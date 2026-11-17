"""search 도구와 장애 주입. 문단은 프롬프트에 넣지 않고 이 도구로만 보여준다."""

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


def search(query: str, item: dict, k: int = 2, fault: Fault = Fault.NONE) -> list[tuple[str, str]]:
    """그 질문의 문단 10개(item["context"]) 안에서만 찾아 (제목, 본문) k개를 돌려준다.

    fault=distractor_only: 근거 문단(item["supporting_facts"]의 제목)을 빼고 방해 문단만.
    fault=tool_timeout: TimeoutError를 던진다 (Span에 error.type=timeout).
    """
    # TODO(역할1): 순위 매기는 방법(예: 단어 겹침, BM25) 정하기
    raise NotImplementedError
