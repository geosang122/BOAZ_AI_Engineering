# agent/ — Agent 루프와 search 도구

담당: 역할1

- **입력**: HotpotQA 문항 (`data.hotpotqa.load_sample()`, 모양은 `fixtures/hotpotqa_sample.json`), `.env`의 `LLM_*`, `AGENT_MODE`, `AGENT_FAULT`
- **출력**: Span (`contracts/span_schema.md`). 보낼 곳은 telemetry가 정한다 (Collector 또는 `runs/<run_id>.jsonl`)
- **실행**: `uv run python scripts/run_agent.py --mock --limit 3`
- **mock**: `agent.llm.MockLLM` — 네트워크 없이 정해 둔 응답 (toolcall용 2개)

| 파일 | 내용 |
|---|---|
| `llm.py` | `OpenRouterClient` (TODO: provider 고정, 백오프, 재시도 횟수), `MockLLM` |
| `tools.py` | `SEARCH_TOOL` 정의, `search()` + 장애 2종 (TODO) |
| `loop.py` | `run_question()`: toolcall / react / closedbook (TODO) |

문단 10개를 프롬프트에 넣지 않는다. search로만 보여준다.
