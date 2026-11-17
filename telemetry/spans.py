"""Span 계측 헬퍼. Agent(역할1)는 이 함수들만 쓴다. 속성은 contracts 모델로만 넣는다.

쓰는 모양 (역할1 쪽):
    with agent_span(question_id, model) as root:
        with chat_span(model) as span:
            ...  # LLM 호출
            set_attrs(span, ChatAttrs(request_model=model, http_status=200, ...))
        with tool_span() as span:
            set_attrs(span, ExecuteToolAttrs(retrieved_titles=[...]))
        set_attrs(root, InvokeAgentAttrs(request_model=model, question_id=qid, answer=answer))
"""

from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry.trace import Span

from contracts.models import SpanAttrs


def set_attrs(span: Span, attrs: SpanAttrs) -> None:
    """계약 모델만 받는다. 모델이 계약 밖 속성(본문 등)을 이미 거부했다."""
    span.set_attributes(attrs.otel())


@contextmanager
def agent_span(question_id: str, model: str) -> Iterator[Span]:
    """루트 Span `invoke_agent agentscope`. 질문 하나 = trace 하나."""
    # TODO(역할2): tracer.start_as_current_span, 예외 시 error.type 기록하고 다시 던지기
    raise NotImplementedError
    yield


@contextmanager
def chat_span(model: str) -> Iterator[Span]:
    """`chat {model}` Span. 재시도까지 합쳐 Span 하나."""
    # TODO(역할2)
    raise NotImplementedError
    yield


@contextmanager
def tool_span(tool_name: str = "search") -> Iterator[Span]:
    """`execute_tool search` Span."""
    # TODO(역할2): 시간 초과면 error.type=timeout
    raise NotImplementedError
    yield
