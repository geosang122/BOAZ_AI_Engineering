# contracts/ — 모두가 따르는 약속

| 파일 | 내용 |
|---|---|
| `span_schema.md` | Span 종류(invoke_agent, chat, execute_tool)별 속성 이름과 타입 |
| `tables.sql` | 정답·clean·mart 테이블 DDL (ClickHouse와 DuckDB에서 그대로 실행) |
| `models.py` | 위 두 파일과 같은 구조의 pydantic 모델, run_id 규칙, 열거형 |

## 수정 절차

**계약 수정은 리더 승인이 필요하다.** `.github/CODEOWNERS`가 `contracts/`의 승인자를 리더로 정한다.

1. 계약만 바꾸는 PR을 따로 연다. 다른 변경을 섞지 않는다.
2. 세 파일(`span_schema.md`, `tables.sql`, `models.py`)과 `fixtures/`를 함께 고친다. `uv run pytest`가 통과해야 한다.
3. 리더가 승인하면 병합한다. 병합 뒤 팀 채널에 알린다.
4. 테이블이 바뀌면 각자 ClickHouse를 지우고 다시 띄운다: `uv run python scripts/down.py --volumes` 다음 `scripts/up.py`.

계약 밖(다른 폴더)에서 테이블·열·Span 속성 이름을 새로 정의하지 않는다. `contracts.models`에서 가져다 쓴다.

## run_id

`날짜_모델_모드_시분초`, 로컬 시각. 예: `20261118_qwen_toolcall_113006`

- 모델 자리는 `.env`의 `LLM_MODEL_ALIAS`. 소문자·숫자·하이픈만.
- 모드: `toolcall` / `react` / `closedbook`
- 만드는 함수: `contracts.models.make_run_id()`

## 데이터

- 원본: Hugging Face `hotpotqa/hotpot_qa`, 리비전 `1908d6afbbead072334abe2965f91bd2709910ab`,
  파일 `distractor/validation-00000-of-00001.parquet` (HotpotQA distractor dev, 7405문항).
  원래 CMU 주소는 2026-11-17 기준 접속되지 않는다.
- 500문항 뽑기: 파일의 행 순서 그대로 `random.Random(42).sample(rows, 500)`.
- `question_id` = 원본의 `id`.

## 판정 규칙

- `retrieval_hit`: 그 질문 trace의 모든 search 결과 제목을 합쳤을 때, 근거 문단(`is_supporting`) 제목을 모두 포함하면 참.
- `all_http_200`: 그 질문의 chat Span이 모두 마지막 시도에서 200이면 참.
- `failure_type` (정답 여부의 기준은 역할4가 `eval/README.md`에 적는다):

| | 근거 다 찾음 | 근거 못 찾음 |
|---|---|---|
| 정답 | `correct_grounded` | `correct_memorized` |
| 오답 | `wrong_reasoning` | `wrong_retrieval` |
| 답 없음 | `error` | `error` |

closedbook 모드는 검색을 하지 않으므로, 정답이면 모두 `correct_memorized`가 된다.

## 저장 금지

프롬프트, 메시지, 답변 전문, 검색어, 문단 본문은 Span·로그·DB 어디에도 넣지 않는다.
저장하는 것: run_id, question_id, 도구 이름, 검색된 문단 제목, 토큰, 지연, provider, HTTP 상태, 재시도 횟수, 최종 답(100자 이하).
