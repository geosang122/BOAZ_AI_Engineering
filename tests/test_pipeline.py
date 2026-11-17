"""한 바퀴: Span → clean → mart → eval. fixtures와 같은 결과가 나오는지 (DuckDB, 서버 없이)."""

import json
import shutil
from pathlib import Path

import pytest

from agent.llm import MockLLM
from agent.loop import run_question
from agent.tools import search
from contracts.models import TABLES, Fault, MartEval, MartRunQuestion, Mode, ResourceAttrs
from eval.classify import score_run
from eval.metrics import exact_match, f1
from storage.backend import Store
from storage.gold import load_gold
from storage.transform import clean_to_mart, raw_to_clean
from telemetry import otel

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
RUN_ID = "20261118_mock_toolcall_090000"
ITEMS = json.loads((FIXTURES / "hotpotqa_sample.json").read_text(encoding="utf-8"))


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSCOPE_BACKEND", "duckdb")
    monkeypatch.setattr(otel, "RUNS_DIR", tmp_path)
    s = Store("duckdb", tmp_path / "t.duckdb")
    load_gold(ITEMS, s)
    return s


def _table(store, model, run_id):
    table = next(name for name, m in TABLES.items() if m is model)
    cols = list(model.model_fields)
    rows = store.query(f"SELECT {', '.join(cols)} FROM {table} WHERE run_id = '{run_id}'")
    return sorted(
        (model(**dict(zip(cols, r, strict=True))) for r in rows), key=lambda r: r.question_id
    )


def _fixture(model, name):
    lines = (FIXTURES / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    return sorted((model.model_validate_json(x) for x in lines), key=lambda r: r.question_id)


def test_fixture_spans_to_mart_and_eval(store):
    shutil.copy(FIXTURES / "spans.jsonl", otel.jsonl_path(RUN_ID))
    for _ in range(2):  # 다시 돌려도 결과가 같다
        raw_to_clean(RUN_ID, store)
        clean_to_mart(RUN_ID, store)
        score_run(RUN_ID, store)
    assert _table(store, MartRunQuestion, RUN_ID) == _fixture(MartRunQuestion, "mart_run_question")
    assert _table(store, MartEval, RUN_ID) == _fixture(MartEval, "mart_eval")


def test_mock_agent_end_to_end(store):
    run_id = "20261118_mock_toolcall_100000"
    provider = otel.setup(ResourceAttrs(run_id=run_id, mode="toolcall", fault="none"))
    answers = [run_question(item, MockLLM(), Mode.TOOLCALL, Fault.NONE) for item in ITEMS]
    provider.shutdown()
    assert answers == ["yes"] * 4
    raw_to_clean(run_id, store)
    clean_to_mart(run_id, store)
    rows = _table(store, MartRunQuestion, run_id)
    assert [(r.n_llm_calls, r.n_tool_calls, r.all_http_200) for r in rows] == [(2, 1, True)] * 4


def test_search_faults():
    item = ITEMS[0]
    supporting = set(item["supporting_facts"]["title"])
    hits = search("Scott Derrickson Ed Wood nationality", item, k=10, fault=Fault.DISTRACTOR_ONLY)
    assert hits and not supporting & {t for t, _ in hits}
    with pytest.raises(TimeoutError):
        search("x", item, fault=Fault.TOOL_TIMEOUT)


def test_metrics_follow_official_rules():
    assert exact_match("The Animorphs.", "animorphs") == 1.0
    assert f1("yes", "no") == 0.0
    assert f1("no, it is not", "no") == 0.0  # yes/no는 정확히 같을 때만
    assert f1("Chief of Protocol of the US", "Chief of Protocol") == pytest.approx(0.75)
