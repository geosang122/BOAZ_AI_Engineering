"""계약: tables.sql·span_schema.md와 같은 구조를 파이썬으로 적은 것.

수정 절차는 contracts/README.md.

tests/test_contracts.py가 세 파일이 서로 맞는지 검사한다.
"""

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── 열거형 ────────────────────────────────────────────────


class Mode(StrEnum):
    TOOLCALL = "toolcall"  # 네이티브 tool calling (기본)
    REACT = "react"  # 텍스트 Search[...] 방식
    CLOSEDBOOK = "closedbook"  # 검색 없이 답


class Fault(StrEnum):
    NONE = "none"
    DISTRACTOR_ONLY = "distractor_only"  # search가 방해 문단만 돌려줌
    TOOL_TIMEOUT = "tool_timeout"  # search가 시간 초과로 실패


class FailureType(StrEnum):
    CORRECT_GROUNDED = "correct_grounded"  # 정답 + 근거 문단을 모두 찾음
    CORRECT_MEMORIZED = "correct_memorized"  # 정답인데 근거를 다 못 찾음 (closedbook 정답 포함)
    WRONG_RETRIEVAL = "wrong_retrieval"  # 오답 + 근거를 다 못 찾음
    WRONG_REASONING = "wrong_reasoning"  # 오답인데 근거는 다 찾음
    ERROR = "error"  # 답이 없음 (HTTP 실패, 예외)


# ── run_id: 날짜_모델_모드_시분초 (예: 20261118_qwen_toolcall_113006) ──

RUN_ID_RE = re.compile(r"\d{8}_[a-z0-9-]+_(toolcall|react|closedbook)_\d{6}")
RunId = Annotated[str, Field(pattern=f"^{RUN_ID_RE.pattern}$")]
ANSWER_MAX = 100  # 최종 답 최대 글자 수 (본문 저장 금지)


def make_run_id(model_alias: str, mode: Mode, now: datetime | None = None) -> str:
    """로컬 시각 기준. 모델 별칭은 소문자·숫자·하이픈만."""
    now = now or datetime.now()
    run_id = f"{now:%Y%m%d}_{model_alias}_{mode}_{now:%H%M%S}"
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"run_id 규칙 위반: {run_id!r}")
    return run_id


# ── Span 속성 (span_schema.md) ──────────────────────────────


class SpanAttrs(BaseModel):
    # 계약에 없는 속성은 거부한다: 프롬프트·답변 전문 같은 본문이 실수로 들어가지 않게.
    model_config = ConfigDict(
        extra="forbid", validate_by_name=True, validate_by_alias=True, frozen=True
    )

    def otel(self) -> dict:
        """span.set_attributes()에 그대로 넣을 dict (gen_ai.* 이름, None 제외)."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class ResourceAttrs(SpanAttrs):
    """모든 Span에 붙는 Resource 속성. 실행 하나 = 프로세스 하나."""

    run_id: RunId = Field(alias="agentscope.run_id")
    mode: Mode = Field(alias="agentscope.mode")
    fault: Fault = Field(alias="agentscope.fault")


class InvokeAgentAttrs(SpanAttrs):
    """invoke_agent Span: 질문 하나의 루트."""

    operation_name: Literal["invoke_agent"] = Field("invoke_agent", alias="gen_ai.operation.name")
    agent_name: Literal["agentscope"] = Field("agentscope", alias="gen_ai.agent.name")
    request_model: str = Field(alias="gen_ai.request.model")
    question_id: str = Field(alias="agentscope.question_id")
    answer: str | None = Field(None, alias="agentscope.answer", max_length=ANSWER_MAX)
    error_type: str | None = Field(None, alias="error.type")


class ChatAttrs(SpanAttrs):
    """chat Span: LLM 호출 한 번 (재시도 포함)."""

    operation_name: Literal["chat"] = Field("chat", alias="gen_ai.operation.name")
    provider_name: Literal["openrouter"] = Field("openrouter", alias="gen_ai.provider.name")
    request_model: str = Field(alias="gen_ai.request.model")
    response_model: str | None = Field(None, alias="gen_ai.response.model")
    input_tokens: int | None = Field(None, alias="gen_ai.usage.input_tokens")
    output_tokens: int | None = Field(None, alias="gen_ai.usage.output_tokens")
    http_status: int | None = Field(None, alias="http.response.status_code")
    retry_count: int = Field(0, alias="http.request.resend_count")
    upstream_provider: str | None = Field(None, alias="agentscope.upstream_provider")
    error_type: str | None = Field(None, alias="error.type")


class ExecuteToolAttrs(SpanAttrs):
    """execute_tool Span: search 호출 한 번. 검색어와 문단 본문은 저장하지 않는다."""

    operation_name: Literal["execute_tool"] = Field("execute_tool", alias="gen_ai.operation.name")
    tool_name: Literal["search"] = Field("search", alias="gen_ai.tool.name")
    retrieved_titles: list[str] = Field(default_factory=list, alias="agentscope.retrieved_titles")
    error_type: str | None = Field(None, alias="error.type")


SPAN_ATTRS: dict[str, type[SpanAttrs]] = {
    "resource": ResourceAttrs,
    "invoke_agent": InvokeAgentAttrs,
    "chat": ChatAttrs,
    "execute_tool": ExecuteToolAttrs,
}

# ── 테이블 행 (tables.sql) ──────────────────────────────────


class _Row(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GoldQuestion(_Row):
    question_id: str
    answer: str
    qtype: Literal["bridge", "comparison"]
    level: Literal["easy", "medium", "hard"]


class GoldParagraph(_Row):
    """질문마다 문단 10개 (근거 2개 + 방해 8개)."""

    question_id: str
    title: str
    is_supporting: bool


class CleanAgentRun(_Row):
    """invoke_agent Span 하나 = 행 하나."""

    run_id: RunId
    question_id: str
    trace_id: str
    mode: Mode
    fault: Fault
    model: str
    start_time: datetime
    duration_ms: float
    answer: str | None = Field(max_length=ANSWER_MAX)
    error_type: str | None


class CleanLlmCall(_Row):
    """chat Span 하나 = 행 하나."""

    run_id: RunId
    question_id: str
    trace_id: str
    span_id: str
    request_model: str
    response_model: str | None
    upstream_provider: str | None
    http_status: int | None
    retry_count: int
    input_tokens: int | None
    output_tokens: int | None
    duration_ms: float
    error_type: str | None


class CleanToolCall(_Row):
    """execute_tool Span 하나 = 행 하나."""

    run_id: RunId
    question_id: str
    trace_id: str
    span_id: str
    tool_name: str
    duration_ms: float
    error_type: str | None


class CleanRetrieval(_Row):
    """검색 결과 제목 하나 = 행 하나 (배열을 쓰지 않으려고 펼침). hit_rank는 1부터."""

    run_id: RunId
    question_id: str
    trace_id: str
    span_id: str
    hit_rank: int
    title: str


class MartRunQuestion(_Row):
    """실행 × 정답 조인. 역할3이 만든다."""

    run_id: RunId
    question_id: str
    mode: Mode
    fault: Fault
    model: str
    answer: str | None
    gold_answer: str
    qtype: Literal["bridge", "comparison"]
    all_http_200: bool  # 이 질문의 LLM 호출이 모두 최종 200
    n_llm_calls: int
    n_tool_calls: int
    input_tokens: int
    output_tokens: int
    retry_count: int
    duration_ms: float
    retrieval_hit: bool  # 근거 문단 제목을 검색으로 모두 찾음
    error_type: str | None


class MartEval(_Row):
    """채점 결과. 역할4가 만든다. em은 0 또는 1."""

    run_id: RunId
    question_id: str
    em: float
    f1: float
    failure_type: FailureType


TABLES: dict[str, type[_Row]] = {
    "gold_questions": GoldQuestion,
    "gold_paragraphs": GoldParagraph,
    "clean_agent_runs": CleanAgentRun,
    "clean_llm_calls": CleanLlmCall,
    "clean_tool_calls": CleanToolCall,
    "clean_retrievals": CleanRetrieval,
    "mart_run_question": MartRunQuestion,
    "mart_eval": MartEval,
}
