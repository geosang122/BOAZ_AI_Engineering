"""플랜 B: 설정 하나(AGENTSCOPE_BACKEND=duckdb)로 Span은 JSONL에, 테이블은 DuckDB에."""

import json

from contracts.models import ChatAttrs, ResourceAttrs
from storage.backend import Store, load_fixtures
from telemetry import otel


def test_jsonl_exporter(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTSCOPE_BACKEND", "duckdb")
    monkeypatch.setattr(otel, "RUNS_DIR", tmp_path)
    resource = ResourceAttrs(run_id="20261118_mock_toolcall_090000", mode="toolcall", fault="none")
    provider = otel.setup(resource)
    with provider.get_tracer("test").start_as_current_span("chat mock") as span:
        span.set_attributes(ChatAttrs(request_model="mock").otel())
    provider.shutdown()
    line = json.loads(otel.jsonl_path(resource.run_id).read_text(encoding="utf-8"))
    assert line["resource"]["attributes"]["agentscope.run_id"] == resource.run_id
    assert line["attributes"]["gen_ai.operation.name"] == "chat"


def test_duckdb_store_loads_fixtures_twice(tmp_path):
    store = Store("duckdb", tmp_path / "t.duckdb")
    load_fixtures(store)
    load_fixtures(store)  # 다시 넣어도 겹치지 않음
    assert store.query("SELECT count(*) FROM mart_eval") == [(4,)]
