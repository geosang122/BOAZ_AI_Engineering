# eval/ — 채점과 실패 유형

담당: 역할4

- **입력**: `mart_run_question` (샘플: `fixtures/mart_run_question.jsonl`)
- **출력**: `mart_eval` (샘플: `fixtures/mart_eval.jsonl`), 터미널 표 (플랜 B)
- **실행**: `uv run python scripts/evaluate.py <run_id>`
- **mock**: `uv run python scripts/seed_data.py --fixtures`로 샘플 mart를 넣고 개발

| 파일 | 내용 |
|---|---|
| `metrics.py` | HotpotQA 공식 정규화, EM, F1 (TODO) |
| `classify.py` | `classify()`, `score_run()`, `print_report()` (TODO) |

정답 기준: TODO — EM=1로 할지 F1 문턱으로 할지 정해서 여기에 적는다.
실패 유형 판정표는 `contracts/README.md`.
