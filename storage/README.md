# storage/ — raw → clean → mart

담당: 역할3

- **입력**: raw Span (ClickHouse `otel_traces` 또는 `runs/<run_id>.jsonl`), HotpotQA 문항
- **출력**: `gold_*`, `clean_*`, `mart_run_question` (`contracts/tables.sql`)
- **실행**: `uv run python scripts/transform.py <run_id>`, `uv run python scripts/seed_data.py`
- **mock**: `Store("duckdb")` — 서버 없이 같은 테이블. 샘플 입력은 `fixtures/spans.jsonl`
  (`runs/20261118_mock_toolcall_090000.jsonl`로 복사하면 `read_raw`가 그대로 읽는다)

| 파일 | 내용 |
|---|---|
| `backend.py` | `Store`: 두 DB를 `execute`/`query`/`insert`로 (완성), `load_fixtures` (완성) |
| `raw.py` | `read_raw()`: 두 곳의 Span을 같은 모양 dict로 (TODO) |
| `transform.py` | `raw_to_clean()` 파이썬, `clean_to_mart()` SQL (TODO) |
| `gold.py` | `load_gold()` (TODO) |
| `sql/mart_run_question.sql` | 두 DB 공통 SQL (TODO) |

같은 run_id로 다시 돌려도 결과가 같아야 한다 (먼저 지우고 넣기).
