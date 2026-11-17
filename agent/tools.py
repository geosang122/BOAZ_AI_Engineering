"""search 도구와 장애 주입. 문단은 프롬프트에 넣지 않고 이 도구로만 보여준다."""

import re

from contracts.models import Fault

# 네이티브 tool calling용 도구 정의 (OpenAI 형식)
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the paragraphs for this question. Returns titles and text.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}

STOPWORDS = set(
    "a an the of in on at to for and or is was were are be by with what which who".split()
)


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower())) - STOPWORDS


def search(query: str, item: dict, k: int = 2, fault: Fault = Fault.NONE) -> list[tuple[str, str]]:
    """그 질문의 문단 10개(item["context"]) 안에서만 찾아 (제목, 본문) k개를 돌려준다.

    순위: 검색어와 겹치는 단어 수 (제목 겹침은 2배). 같으면 원래 순서.
    fault=distractor_only: 근거 문단(item["supporting_facts"]의 제목)을 빼고 방해 문단만.
    fault=tool_timeout: TimeoutError를 던진다 (Span에 error.type=timeout).
    """
    if fault == Fault.TOOL_TIMEOUT:
        raise TimeoutError("search timed out")
    q = _words(query)
    supporting = set(item["supporting_facts"]["title"])
    docs = [
        (title, "".join(sentences))
        for title, sentences in zip(
            item["context"]["title"], item["context"]["sentences"], strict=True
        )
        if not (fault == Fault.DISTRACTOR_ONLY and title in supporting)
    ]
    scored = sorted(
        docs,
        key=lambda d: -(2 * len(q & _words(d[0])) + len(q & _words(d[1]))),
    )  # sorted는 안정 정렬이라 같은 점수면 원래 순서
    return scored[:k]
