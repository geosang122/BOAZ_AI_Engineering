"""계약 검사: tables.sql ↔ models.py ↔ span_schema.md ↔ fixtures가 서로 맞는지."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import get_args

import duckdb
import pytest
from pydantic import ValidationError

from contracts import models as m

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"
SQL_TYPES = {bool: "BOOLEAN", int: "BIGINT", float: "DOUBLE", datetime: "TIMESTAMP"}


def _column(annotation) -> tuple[str, str]:
    """모델 필드 타입 → (DuckDB 타입, NULL 허용). str·Literal·열거형은 VARCHAR."""
    args = get_args(annotation)
    nullable = type(None) in args
    base = next(a for a in args if a is not type(None)) if nullable else annotation
    return SQL_TYPES.get(base, "VARCHAR"), "YES" if nullable else "NO"


def test_tables_sql_matches_models():
    con = duckdb.connect()
    con.execute((CONTRACTS / "tables.sql").read_text(encoding="utf-8"))
    tables = {r[0] for r in con.execute("SELECT table_name FROM duckdb_tables()").fetchall()}
    assert tables == set(m.TABLES)
    for name, model in m.TABLES.items():
        got = [(c[0], c[1], c[2]) for c in con.execute(f"DESCRIBE {name}").fetchall()]
        want = [(f, *_column(info.annotation)) for f, info in model.model_fields.items()]
        assert got == want, name


def test_span_schema_md_matches_models():
    sections: dict[str, set[str]] = {}
    current = None
    for line in (CONTRACTS / "span_schema.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            if current in m.SPAN_ATTRS:
                sections[current] = set()
        elif current in sections and (hit := re.match(r"\|\s*`([^`]+)`", line)):
            sections[current].add(hit[1])
    want = {k: {f.alias for f in v.model_fields.values()} for k, v in m.SPAN_ATTRS.items()}
    assert sections == want


def test_span_fixture_follows_contract():
    for line in (FIXTURES / "spans.jsonl").read_text(encoding="utf-8").splitlines():
        span = json.loads(line)
        resource = span["resource"]["attributes"]
        m.ResourceAttrs.model_validate({k: v for k, v in resource.items() if "agentscope." in k})
        attrs = span["attributes"]
        m.SPAN_ATTRS[attrs["gen_ai.operation.name"]].model_validate(attrs)


@pytest.mark.parametrize("table", ["mart_run_question", "mart_eval"])
def test_mart_fixtures_follow_contract(table):
    sample = json.loads((FIXTURES / "hotpotqa_sample.json").read_text(encoding="utf-8"))
    ids = {item["id"] for item in sample}
    for line in (FIXTURES / f"{table}.jsonl").read_text(encoding="utf-8").splitlines():
        assert m.TABLES[table].model_validate_json(line).question_id in ids


def test_run_id_rule():
    run_id = m.make_run_id("qwen", m.Mode.TOOLCALL, datetime(2026, 11, 18, 11, 30, 6))
    assert run_id == "20261118_qwen_toolcall_113006"
    with pytest.raises(ValueError):
        m.make_run_id("qwen/qwen3", m.Mode.TOOLCALL)  # 모델 별칭에 / 금지


def test_body_attributes_are_rejected():
    """본문 저장 금지: 계약 밖 속성(예: 프롬프트 메시지)은 모델이 막는다."""
    with pytest.raises(ValidationError):
        m.ChatAttrs.model_validate(
            {"gen_ai.request.model": "x", "gen_ai.input.messages": "[{...prompt...}]"}
        )
    with pytest.raises(ValidationError):
        m.InvokeAgentAttrs(request_model="x", question_id="q", answer="긴 답" * 100)
