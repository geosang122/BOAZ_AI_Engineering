# 1일차 체크리스트

목표: 저녁까지 각자 **자기 모듈이 fixtures/mock만으로 한 번 돈다**. 다른 사람을 기다리지 않는다.

## 모두 (오전)

- [ ] 저장소 받기 → `uv sync` → `.env.example`을 `.env`로 복사
- [ ] `uv run pre-commit install`
- [ ] `uv run pytest` 통과 (9개)
- [ ] `contracts/README.md`, `contracts/span_schema.md` 읽기 — 궁금한 점은 오전 안에 리더에게
- [ ] 자기 브랜치 만들기: `feat/<역할>-<기능>`
- [ ] Claude Code를 쓰면 `CLAUDE.md`를 먼저 읽게 한다

## 리더

- [ ] GitHub 저장소 만들고 push, 팀원 초대
- [ ] `.github/CODEOWNERS`와 `.github/workflows/contracts-approval.yml`의 아이디 채우기
- [ ] `main` 보호 규칙 설정 (`CONTRIBUTING.md` 맨 아래)
- [ ] OpenRouter 키·provider를 팀에 나눠 주기 (`.env`는 git에 올리지 않는다)

## 역할1 — agent/, data/

- [ ] `data.hotpotqa.download()`, `load_sample()` 구현
- [ ] 500문항 중 앞 3개 id를 팀 채널에 올리기 → 모두 같은지 확인 (seed 42가 맞게 됐는지)
- [ ] `search()`를 단어 겹침 같은 쉬운 방법으로 먼저 구현
- [ ] `run_question()` toolcall 모드를 `MockLLM`으로 1문항 돌리기
      (`AGENTSCOPE_BACKEND=duckdb uv run python scripts/run_agent.py --mock --limit 1`)
- [ ] `OpenRouterClient.chat()`으로 실제 1회 호출, 응답의 `provider`가 고정한 값인지 확인
- 완료 기준: `runs/<run_id>.jsonl`이 생기고, 그 파일로 `fixtures/spans.jsonl`을 잠시 바꿔도 `pytest`가 통과

## 역할2 — telemetry/, infra/, docker-compose.yml

- [ ] Docker Desktop 설치 → `uv run python scripts/up.py` → http://localhost:3000 열기
- [ ] `uv run python scripts/seed_data.py --fixtures` → 대시보드 표에 4문항이 보이는지
- [ ] `telemetry/spans.py`의 `agent_span`, `chat_span`, `tool_span` 구현 + 테스트 하나
- [ ] 역할1과 헬퍼 쓰는 모양 맞추기 (`spans.py` 맨 위 예시)
- [ ] Mac 한 명, Windows 한 명이 `up.py`를 실제로 돌려 보기
- 완료 기준: 서버를 켠 상태에서 Span을 보내면 ClickHouse `otel_traces`에 행이 생김

## 역할3 — storage/

- [ ] `fixtures/spans.jsonl`을 `runs/20261118_mock_toolcall_090000.jsonl`로 복사
- [ ] `read_raw()` DuckDB 쪽 먼저 → `raw_to_clean()` → `clean_*` 4개 채우기
- [ ] `load_gold()`를 `fixtures/hotpotqa_sample.json`으로 돌리기
- [ ] `sql/mart_run_question.sql` 초안
- 완료 기준: 샘플 입력으로 만든 `mart_run_question` 4행이 `fixtures/mart_run_question.jsonl`과 같음
  (`duration_ms`처럼 계산이 다른 값은 차이를 메모)

## 역할4 — eval/, dashboard/

- [ ] `eval/metrics.py`: 공식 채점기와 같은 EM/F1 + 테스트 (yes/no, 관사, 구두점)
- [ ] 정답 기준(EM=1 또는 F1 문턱)을 정해 `eval/README.md`에 적기
- [ ] `classify()`, `score_run()`: `fixtures/mart_run_question.jsonl`을 넣으면 `fixtures/mart_eval.jsonl`과 같은 결과
- [ ] 역할2가 서버를 띄우면 `seed_data.py --fixtures` 데이터로 패널 하나 더 (실패 유형 막대)
- 완료 기준: 샘플 4문항의 실패 유형 4종이 맞게 나옴

## 저녁 (모두, 15분)

- [ ] 각자 완료 기준 통과했는지 공유
- [ ] 계약을 바꿔야 할 것 같은 점 모으기 → 리더가 내일 아침 한 PR로 정리
