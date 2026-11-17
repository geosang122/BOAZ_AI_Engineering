# telemetry/ — Span 계측

담당: 역할2

- **입력**: Agent가 넘기는 계약 모델 (`contracts.models`의 `*Attrs`)
- **출력**: OTLP/HTTP → Collector, 또는 `runs/<run_id>.jsonl` (플랜 B)
- **설정**: `.env`의 `AGENTSCOPE_BACKEND` (clickhouse | duckdb), `OTEL_EXPORTER_OTLP_ENDPOINT`
- **확인**: `uv run pytest tests/test_plan_b.py`

| 파일 | 내용 |
|---|---|
| `otel.py` | `setup()`: exporter 전환 (완성). 끝나면 `provider.shutdown()` |
| `spans.py` | `agent_span`, `chat_span`, `tool_span` (TODO), `set_attrs` (완성) |
