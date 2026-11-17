# Claude Code 규칙 (이 저장소에서 일하는 모든 Claude가 따른다)

## 꼭 지킬 것

1. **계약을 마음대로 고치지 않는다.** `contracts/`(span_schema.md, tables.sql, models.py)는 리더 승인 없이는 바꾸지 않는다.
   바꿔야 할 것 같으면 멈추고 사람에게 이유를 알린다.
2. **계약 밖에서 스키마를 정의하지 않는다.** 테이블·열·Span 속성 이름은 `contracts.models`에서 가져다 쓴다.
   Span 속성은 `span.set_attributes(<계약 모델>.otel())`로만 넣는다.
3. **본문을 저장하지 않는다.** 프롬프트, 메시지, 답변 전문, 검색어, 문단 본문을 Span·로그·DB·파일 어디에도 남기지 않는다.
   저장해도 되는 것은 `contracts/README.md`의 '저장 금지' 절에 있다.
4. **담당 폴더 밖을 고치면 PR 설명에 적는다:** `담당 밖 수정: <경로> — <이유>`. 담당은 `.github/CODEOWNERS`.
5. Agent 프레임워크(LangChain, LlamaIndex 등)를 쓰지 않는다.

## 작업 방식

- Python 3.11 + uv. 의존성은 `uv add`로만 추가한다.
- 경로는 `pathlib`, 파일은 `encoding="utf-8"`. Mac과 Windows에서 모두 돌아야 한다.
- 서버(Collector, ClickHouse, Grafana)는 Docker Compose로만 띄운다. 서버 없이 확인할 때는 `AGENTSCOPE_BACKEND=duckdb`.
- 끝내기 전에 `uv run ruff check . && uv run ruff format --check . && uv run pytest`가 통과해야 한다.
- 다른 모듈을 기다리지 말고 `fixtures/`의 샘플과 mock(`agent.llm.MockLLM`, DuckDB 백엔드)으로 개발한다.
