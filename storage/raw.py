"""raw 읽기: run_id의 Span을 두 곳 중 하나에서 같은 모양으로 꺼낸다.

clickhouse: Collector가 만든 otel_traces (ResourceAttributes['agentscope.run_id']로 거름).
            속성 값은 모두 문자열, string[]은 JSON 배열 문자열이다.
duckdb:     telemetry.otel.jsonl_path(run_id) 파일. 모양은 fixtures/spans.jsonl과 같다.
            trace_id·span_id 앞의 '0x'를 떼어 ClickHouse와 맞춘다.
"""

import json
from datetime import datetime, timedelta

from contracts.models import ExecuteToolAttrs, ResourceAttrs
from storage.backend import Store
from telemetry import otel

RUN_ID_KEY = ResourceAttrs.model_fields["run_id"].alias
TITLES_KEY = ExecuteToolAttrs.model_fields["retrieved_titles"].alias
MS = timedelta(milliseconds=1)


def read_raw(run_id: str, store: Store) -> list[dict]:
    """Span 하나 = dict 하나:
    {trace_id, span_id, parent_span_id, name, start_time, duration_ms, attributes, resource}
    """
    return _read_clickhouse(run_id, store) if store.kind == "clickhouse" else _read_jsonl(run_id)


def _hex(value: str | None) -> str | None:
    return value.removeprefix("0x") if value else None


def _read_jsonl(run_id: str) -> list[dict]:
    path = otel.jsonl_path(run_id)
    spans = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        s = json.loads(line)
        start = datetime.fromisoformat(s["start_time"])
        spans.append(
            {
                "trace_id": _hex(s["context"]["trace_id"]),
                "span_id": _hex(s["context"]["span_id"]),
                "parent_span_id": _hex(s["parent_id"]),
                "name": s["name"],
                "start_time": start.replace(tzinfo=None),  # UTC, ClickHouse처럼 tz 없이
                "duration_ms": (datetime.fromisoformat(s["end_time"]) - start) / MS,
                "attributes": s["attributes"],
                "resource": s["resource"]["attributes"],
            }
        )
    return spans


def _read_clickhouse(run_id: str, store: Store) -> list[dict]:
    rows = store.query(
        "SELECT TraceId, SpanId, ParentSpanId, SpanName, Timestamp, Duration, "
        "SpanAttributes, ResourceAttributes FROM otel_traces "
        f"WHERE ResourceAttributes['{RUN_ID_KEY}'] = '{run_id}'"
    )
    spans = []
    for trace_id, span_id, parent, name, start, duration_ns, attrs, resource in rows:
        attrs = dict(attrs)
        if TITLES_KEY in attrs:
            attrs[TITLES_KEY] = json.loads(attrs[TITLES_KEY])
        spans.append(
            {
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent or None,
                "name": name,
                "start_time": start,
                "duration_ms": duration_ns / 1e6,
                "attributes": attrs,
                "resource": dict(resource),
            }
        )
    return spans
