"""Span 계측 헬퍼. Agent(역할1)는 이 함수들만 쓴다. 속성은 contracts 모델로만 넣는다.

쓰는 모양 (역할1 쪽):
    with agent_span(question_id, model) as root:
        with chat_span(model) as span:
            ...  # LLM 호출
            set_attrs(span, ChatAttrs(request_model=model, http_status=200, ...))
        with tool_span() as span:
            set_attrs(span, ExecuteToolAttrs(retrieved_titles=[...]))
        set_attrs(root, InvokeAgentAttrs(request_model=model, question_id=qid, answer=answer))

예외가 나면 Span에 error.type을 적고 다시 던진다. 이미 적혀 있으면(호출한 쪽이 먼저 적었으면) 두고.
예외 메시지는 본문이 섞일 수 있어 남기지 않는다 (record_exception=False).
"""

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Span

from contracts.models import (
    ChatAttrs,
    ExecuteToolAttrs,
    InvokeAgentAttrs,
    SpanAttrs,
)

ERROR_KEY = InvokeAgentAttrs.model_fields["error_type"].alias


def set_attrs(span: Span, attrs: SpanAttrs) -> None:
    """계약 모델만 받는다. 모델이 계약 밖 속성(본문 등)을 이미 거부했다."""
    span.set_attributes(attrs.otel())


def error_type(exc: BaseException) -> str:
    """예외 → error.type 값. 시간 초과는 timeout, LLMError처럼 error_type을 가진 예외는 그 값."""
    if isinstance(exc, TimeoutError):
        return "timeout"
    return getattr(exc, "error_type", None) or type(exc).__name__


@contextmanager
def _span(name: str, attrs: SpanAttrs, on_error) -> Iterator[Span]:
    tracer = trace.get_tracer("agentscope")
    with tracer.start_as_current_span(name, record_exception=False) as span:
        set_attrs(span, attrs)
        try:
            yield span
        except Exception as e:
            if ERROR_KEY not in (getattr(span, "attributes", None) or {}):
                set_attrs(span, on_error(error_type(e)))
            raise


def agent_span(question_id: str, model: str):
    """루트 Span `invoke_agent agentscope`. 질문 하나 = trace 하나."""
    attrs = InvokeAgentAttrs(request_model=model, question_id=question_id)
    return _span(
        "invoke_agent agentscope",
        attrs,
        lambda err: InvokeAgentAttrs(request_model=model, question_id=question_id, error_type=err),
    )


def chat_span(model: str):
    """`chat {model}` Span. 재시도까지 합쳐 Span 하나."""
    return _span(
        f"chat {model}",
        ChatAttrs(request_model=model),
        lambda err: ChatAttrs(request_model=model, error_type=err),
    )


def tool_span(tool_name: str = "search"):
    """`execute_tool search` Span. 시간 초과면 error.type=timeout."""
    return _span(
        f"execute_tool {tool_name}",
        ExecuteToolAttrs(tool_name=tool_name),
        lambda err: ExecuteToolAttrs(tool_name=tool_name, error_type=err),
    )
