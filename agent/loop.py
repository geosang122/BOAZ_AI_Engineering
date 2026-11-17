"""Agent 루프 (프레임워크 없이). 질문 하나를 풀고 Span을 남긴다."""

import json
import re
import sys

from agent.llm import LLMError
from agent.tools import SEARCH_TOOL, search
from contracts.models import ANSWER_MAX, ChatAttrs, ExecuteToolAttrs, Fault, InvokeAgentAttrs, Mode
from telemetry.spans import agent_span, chat_span, set_attrs, tool_span

MAX_STEPS = 6  # 질문 하나당 LLM 호출 상한

ANSWER_RULE = (
    "Reply with only the final answer: a short phrase (a name, date, number), or yes/no. "
    "No explanation, no full sentence."
)
PROMPTS = {
    Mode.TOOLCALL: "Answer the question. Use the search tool to find evidence; each search "
    "returns the 2 best paragraphs. Search again with other words if needed. " + ANSWER_RULE,
    Mode.REACT: "Answer the question by searching. Each turn, write one line 'Thought: ...' then "
    "exactly one action line:\n"
    "Action: Search[query]  (returns the 2 best paragraphs)\n"
    "Action: Finish[answer]  (the final answer: a short phrase or yes/no)\n"
    "Stop after the action line; the Observation will be given to you.",
    Mode.CLOSEDBOOK: "Answer the question from your own knowledge. " + ANSWER_RULE,
}
LAST_STEP = "No searches left. Give your best final answer now."
ACTION_RE = re.compile(r"(Search|Finish)\[(.*?)\]", re.DOTALL)


class NoAnswer(Exception):
    error_type = "no_answer"


def run_question(item: dict, llm, mode: Mode, fault: Fault) -> str | None:
    """HotpotQA 문항 하나 → 최종 답(짧은 문자열). 실패하면 None.

    toolcall:   llm.chat(messages, tools=[SEARCH_TOOL]) → tool_calls가 있으면 search 실행 → 반복
    react:      도구 정의 없이, 답변 텍스트의 Search[...]를 찾아 search 실행
                → 결과를 Observation으로 붙여 반복
    closedbook: search 없이 질문만으로 한 번에 답

    Span: telemetry.spans의 agent_span / chat_span / tool_span (속성은 contracts 모델로만).
    """
    qid = item["id"]
    try:
        with agent_span(qid, llm.model) as root:
            answer = SOLVERS[mode](item, llm, fault)
            set_attrs(
                root, InvokeAgentAttrs(request_model=llm.model, question_id=qid, answer=answer)
            )
        return answer
    except Exception as e:
        # 한 문항 실패로 실행 전체를 멈추지 않는다. 메시지는 본문이 섞일 수 있어 타입만 찍는다.
        print(f"[{qid}] 실패: {type(e).__name__}", file=sys.stderr)
        return None


def _clean(text: str | None) -> str:
    """모델 답 → 짧은 답 (첫 줄, 'Answer:' 접두어 제거, 100자)."""
    lines = (text or "").strip().splitlines()
    first = re.sub(r"^(final answer|answer)\s*:\s*", "", lines[0] if lines else "", flags=re.I)
    answer = first.strip().strip("*").strip()[:ANSWER_MAX]
    if not answer:
        raise NoAnswer
    return answer


def _chat(llm, messages: list[dict], tools: list[dict] | None = None) -> dict:
    """chat Span 하나 = llm.chat 한 번(재시도 포함). 응답의 assistant message를 돌려준다."""
    with chat_span(llm.model) as span:
        try:
            reply, status, retries = llm.chat(messages, tools)
        except LLMError as e:
            set_attrs(
                span,
                ChatAttrs(
                    request_model=llm.model,
                    http_status=e.status,
                    retry_count=e.retries,
                    error_type=e.error_type,
                ),
            )
            raise
        usage = reply.get("usage") or {}
        set_attrs(
            span,
            ChatAttrs(
                request_model=llm.model,
                response_model=reply.get("model"),
                input_tokens=usage.get("prompt_tokens"),
                output_tokens=usage.get("completion_tokens"),
                http_status=status,
                retry_count=retries,
                upstream_provider=reply.get("provider"),
            ),
        )
    return reply["choices"][0]["message"]


def _search(query: str, item: dict, fault: Fault) -> str:
    """execute_tool Span 하나. 결과를 LLM에 보여 줄 텍스트로 (Span에는 제목만)."""
    try:
        with tool_span() as span:
            hits = search(query, item, fault=fault)
            set_attrs(span, ExecuteToolAttrs(retrieved_titles=[t for t, _ in hits]))
    except TimeoutError:
        return "Error: search timed out."
    return "\n\n".join(f"{title}: {text}" for title, text in hits)


def _toolcall(item: dict, llm, fault: Fault) -> str:
    messages = [
        {"role": "system", "content": PROMPTS[Mode.TOOLCALL]},
        {"role": "user", "content": item["question"]},
    ]
    for step in range(MAX_STEPS):
        if step == MAX_STEPS - 1:
            messages.append({"role": "user", "content": LAST_STEP})
        msg = _chat(llm, messages, [SEARCH_TOOL])
        calls = msg.get("tool_calls")
        if not calls:
            return _clean(msg.get("content"))
        messages.append({"role": "assistant", "content": msg.get("content"), "tool_calls": calls})
        for call in calls:
            try:
                query = json.loads(call["function"]["arguments"] or "{}").get("query", "")
            except json.JSONDecodeError:
                query = ""
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": _search(query, item, fault)}
            )
    raise NoAnswer


def _react(item: dict, llm, fault: Fault) -> str:
    messages = [
        {"role": "system", "content": PROMPTS[Mode.REACT]},
        {"role": "user", "content": f"Question: {item['question']}"},
    ]
    for step in range(MAX_STEPS):
        content = _chat(llm, messages).get("content") or ""
        action = ACTION_RE.search(content)
        if not action:
            return _clean(content)  # 형식을 안 지키면 답으로 본다
        if action[1] == "Finish":
            return _clean(action[2])
        # 모델이 Observation까지 지어내도 첫 action까지만 남긴다
        messages.append({"role": "assistant", "content": content[: action.end()]})
        observation = f"Observation: {_search(action[2], item, fault)}"
        if step == MAX_STEPS - 2:
            observation += f"\n\n{LAST_STEP} Use Action: Finish[answer]."
        messages.append({"role": "user", "content": observation})
    raise NoAnswer


def _closedbook(item: dict, llm, fault: Fault) -> str:
    messages = [
        {"role": "system", "content": PROMPTS[Mode.CLOSEDBOOK]},
        {"role": "user", "content": item["question"]},
    ]
    return _clean(_chat(llm, messages).get("content"))


SOLVERS = {Mode.TOOLCALL: _toolcall, Mode.REACT: _react, Mode.CLOSEDBOOK: _closedbook}
