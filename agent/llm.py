"""LLM 호출: OpenRouter(OpenAI 호환)와 MockLLM. 응답은 API가 준 dict 그대로 돌려준다."""

import itertools
import os


class OpenRouterClient:
    """provider 하나로 고정(allow_fallbacks=false). 429·타임아웃은 지수 백오프로 재시도."""

    def __init__(self, base_url: str, api_key: str, model: str, provider: str):
        self.base_url, self.api_key, self.model, self.provider = base_url, api_key, model, provider

    @classmethod
    def from_env(cls) -> "OpenRouterClient":
        e = os.environ
        return cls(e["LLM_BASE_URL"], e["LLM_API_KEY"], e["LLM_MODEL"], e["LLM_PROVIDER"])

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[dict, int, int]:
        """(응답 dict, 마지막 HTTP 상태, 재시도 횟수)."""
        # TODO(역할1): httpx로 POST {base_url}/chat/completions
        #   body에 "provider": {"order": [self.provider], "allow_fallbacks": False}
        #   429·타임아웃 → 지수 백오프 재시도, 횟수를 세어 돌려준다 (chat Span의 resend_count)
        raise NotImplementedError


class MockLLM:
    """네트워크 없이 정해 둔 응답을 차례로(끝나면 처음부터) 돌려준다."""

    def __init__(self, replies: list[dict] | None = None):
        self._replies = itertools.cycle(replies or MOCK_REPLIES)
        self.model = "mock/mock-model"

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[dict, int, int]:
        return next(self._replies), 200, 0


def _reply(message: dict, finish: str) -> dict:
    return {
        "model": "mock/mock-model",
        "provider": "mock",
        "choices": [{"message": {"role": "assistant", **message}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 300, "completion_tokens": 25},
    }


# toolcall 모드 기준: search 한 번 → 답. react 모드용 응답은 역할1이 추가.
MOCK_REPLIES = [
    _reply(
        {
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": '{"query": "mock"}'},
                }
            ],
        },
        "tool_calls",
    ),
    _reply({"content": "yes"}, "stop"),
]
