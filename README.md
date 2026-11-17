# AgentScope

QA Agent의 실행 기록(OpenTelemetry Span)과 HotpotQA 정답을 이어 붙여,
**"HTTP 200인데 틀린 답"** 과 그 원인(검색 실패 / 추론 실패 / 암기)을 잰다.

```
Agent ──Span──▶ Collector ──▶ ClickHouse(otel_traces) ──▶ clean ──▶ mart ──▶ Grafana
  (agent/)     (infra/)                 (storage/)                  (eval/)  (dashboard/)

플랜 B (서버 없이): Agent ──▶ runs/<run_id>.jsonl ──▶ DuckDB(clean, mart) ──▶ 터미널 표
```

## 처음 한 번

1. [uv](https://docs.astral.sh/uv/) 설치 → `uv sync` (Python 3.11은 uv가 받아 온다)
2. `.env.example`을 복사해 `.env`를 만들고 `LLM_API_KEY`, `LLM_PROVIDER`를 채운다
3. `uv run pre-commit install`
4. `uv run pytest` 통과 확인
5. 서버를 쓸 사람은 Docker Desktop 설치

## 서버 켜고 끄기

```
uv run python scripts/up.py        # Collector :4318, ClickHouse :8123/:9000, Grafana :3000
uv run python scripts/seed_data.py --fixtures   # 샘플 mart → 대시보드에 바로 보임
uv run python scripts/down.py      # 끄기 (--volumes: ClickHouse 데이터까지 지움)
```

Grafana: http://localhost:3000 (admin / admin) → 대시보드 `AgentScope`

## 한 바퀴

```
uv run python scripts/seed_data.py               # HotpotQA 500문항 → 정답 테이블
uv run python scripts/run_agent.py --limit 5     # 끝에 run_id 출력
uv run python scripts/transform.py <run_id>      # raw → clean → mart
uv run python scripts/evaluate.py <run_id>       # 채점 → mart_eval + 표
```

## 플랜 B: 서버 없이

`.env`에서 `AGENTSCOPE_BACKEND=duckdb` 하나만 바꾼다.
Span은 `runs/<run_id>.jsonl`에, 테이블은 `runs/agentscope.duckdb`에 생긴다. 같은 `tables.sql`과 mart SQL이 그대로 돈다.
Grafana는 없고 `evaluate.py`가 표를 출력한다.

## 폴더와 담당

| 폴더 | 담당 | 내용 |
|---|---|---|
| `contracts/` | 리더 승인 | Span·테이블·모델 계약. **수정은 리더 승인** ([규칙](contracts/README.md)) |
| `agent/`, `data/` | 역할1 | Agent 루프, search 도구, 장애 주입, 데이터 로더 |
| `telemetry/`, `infra/`, `docker-compose.yml` | 역할2 | Span 헬퍼, Collector·ClickHouse·Grafana 설정 |
| `storage/` | 역할3 | raw → clean → mart, 정답 적재 |
| `eval/`, `dashboard/` | 역할4 | EM/F1, 실패 유형, Grafana 대시보드·알림 |
| `fixtures/` | 공동 | 모듈 사이에 주고받는 샘플 데이터 |
| `scripts/` | 각 담당 | 실행 진입점 (Makefile 대신, Mac/Windows 공통) |

첫날 할 일: [docs/day1.md](docs/day1.md). 협업 규칙: [CONTRIBUTING.md](CONTRIBUTING.md).
