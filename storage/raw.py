"""raw 읽기: run_id의 Span을 두 곳 중 하나에서 같은 모양으로 꺼낸다.

clickhouse: Collector가 만든 otel_traces (ResourceAttributes['agentscope.run_id']로 거름).
            속성 값은 모두 문자열, string[]은 JSON 배열 문자열이다.
duckdb:     telemetry.otel.jsonl_path(run_id) 파일. 모양은 fixtures/spans.jsonl과 같다.
            trace_id·span_id 앞의 '0x'를 떼어 ClickHouse와 맞춘다.
"""

from storage.backend import Store


def read_raw(run_id: str, store: Store) -> list[dict]:
    """Span 하나 = dict 하나:
    {trace_id, span_id, parent_span_id, name, start_time, duration_ms, attributes, resource}
    """
    # TODO(역할3)
    raise NotImplementedError
