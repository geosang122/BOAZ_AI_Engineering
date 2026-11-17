"""Agent 루프 (프레임워크 없이). 질문 하나를 풀고 Span을 남긴다."""

from contracts.models import Fault, Mode


def run_question(item: dict, llm, mode: Mode, fault: Fault) -> str | None:
    """HotpotQA 문항 하나 → 최종 답(짧은 문자열). 실패하면 None.

    toolcall:   llm.chat(messages, tools=[SEARCH_TOOL]) → tool_calls가 있으면 search 실행 → 반복
    react:      도구 정의 없이, 답변 텍스트의 Search[...]를 찾아 search 실행
                → 결과를 Observation으로 붙여 반복
    closedbook: search 없이 질문만으로 한 번에 답

    Span: telemetry.spans의 agent_span / chat_span / tool_span (속성은 contracts 모델로만).
    """
    # TODO(역할1): 세 모드, 최대 단계 수, 답 길이 100자 자르기
    raise NotImplementedError
