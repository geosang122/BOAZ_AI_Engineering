# Span 스키마 (계약)

기준: OpenTelemetry GenAI semantic conventions v1.37 (`gen_ai.*`).
표준 이름이 없는 값은 `agentscope.*`, HTTP 값은 OTel HTTP 표준 이름을 쓴다.
`contracts/models.py`의 `SPAN_ATTRS`와 이 표가 같아야 한다 (`tests/test_contracts.py`가 검사).

## 규칙

- 질문 하나 = trace 하나. 루트는 invoke_agent, 그 아래에 chat과 execute_tool.
- chat·execute_tool에는 question_id가 없다. 같은 trace_id로 질문에 묶는다.
- 지연은 Span 시작~끝 시간이다. 따로 속성을 두지 않는다.
- 속성은 계약 모델로만 넣는다: `span.set_attributes(ChatAttrs(...).otel())`. 계약에 없는 속성은 모델이 거부한다.
- 저장 금지: 프롬프트, 메시지, 답변 전문, 검색어, 문단 본문.
  그래서 `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`는 쓰지 않는다.
- ClickHouse의 otel_traces에서는 모든 값이 문자열로, string[]은 JSON 배열 문자열로 저장된다.

## resource

모든 Span에 붙는 Resource 속성. `service.name`은 `agentscope`로 같이 넣는다.

| 속성 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `agentscope.run_id` | string | ✓ | 날짜_모델_모드_시분초 |
| `agentscope.mode` | string | ✓ | toolcall / react / closedbook |
| `agentscope.fault` | string | ✓ | none / distractor_only / tool_timeout |

## invoke_agent

Span 이름: `invoke_agent agentscope`

| 속성 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `gen_ai.operation.name` | string | ✓ | `invoke_agent` |
| `gen_ai.agent.name` | string | ✓ | `agentscope` |
| `gen_ai.request.model` | string | ✓ | 예: `qwen/qwen3-32b` |
| `agentscope.question_id` | string | ✓ | HotpotQA `id` |
| `agentscope.answer` | string |  | 최종 답 (100자 이하) |
| `error.type` | string |  | 실패했을 때만 |

## chat

Span 이름: `chat {gen_ai.request.model}`. 재시도까지 합쳐 Span 하나.

| 속성 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `gen_ai.operation.name` | string | ✓ | `chat` |
| `gen_ai.provider.name` | string | ✓ | `openrouter` |
| `gen_ai.request.model` | string | ✓ | 요청한 모델 |
| `gen_ai.response.model` | string |  | 응답에 적힌 모델 |
| `gen_ai.usage.input_tokens` | int |  | 입력 토큰 |
| `gen_ai.usage.output_tokens` | int |  | 출력 토큰 |
| `http.response.status_code` | int |  | 마지막 시도의 HTTP 상태 |
| `http.request.resend_count` | int | ✓ | 재시도 횟수 (처음 시도는 안 셈) |
| `agentscope.upstream_provider` | string |  | OpenRouter 응답의 `provider` (고정한 값과 같아야 함) |
| `error.type` | string |  | 실패했을 때만. 예: `timeout`, `429` |

## execute_tool

Span 이름: `execute_tool search`

| 속성 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `gen_ai.operation.name` | string | ✓ | `execute_tool` |
| `gen_ai.tool.name` | string | ✓ | `search` |
| `agentscope.retrieved_titles` | string[] | ✓ | 돌려준 문단 제목, 순위 순 (실패하면 빈 배열) |
| `error.type` | string |  | 실패했을 때만. 예: `timeout` |
