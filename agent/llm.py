"""LLM 호출: OpenRouter(OpenAI 호환)와 MockLLM. 응답은 API가 준 dict 그대로 돌려준다."""

import itertools
import os
import time

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 4  # 대기 4, 8, 16, 32초
TIMEOUT = 120


class LLMError(Exception):
    """마지막 시도까지 실패. error_type은 chat Span의 error.type (예: "429", "timeout")."""

    def __init__(self, error_type: str, status: int | None, retries: int):
        super().__init__(error_type)
        self.error_type, self.status, self.retries = error_type, status, retries


class OpenRouterClient:
    """provider 하나로 고정(allow_fallbacks=false). 429·5xx·타임아웃은 지수 백오프로 재시도.

    실패하면 LLMError. 정상 반환이면 HTTP 200이다.
    """

    def __init__(self, base_url: str, api_key: str, model: str, provider: str):
        self.base_url, self.api_key, self.model, self.provider = base_url, api_key, model, provider

    @classmethod
    def from_env(cls) -> "OpenRouterClient":
        e = os.environ
        return cls(e["LLM_BASE_URL"], e["LLM_API_KEY"], e["LLM_MODEL"], e["LLM_PROVIDER"])

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[dict, int, int]:
        """(응답 dict, 마지막 HTTP 상태, 재시도 횟수)."""
        body = {
            "model": self.model,
            "messages": messages,
            "provider": {"order": [self.provider], "allow_fallbacks": False},
        }
        if tools:
            body["tools"] = tools
        headers = {"Authorization": f"Bearer {self.api_key}"}
        for attempt in range(MAX_RETRIES + 1):
            if attempt:
                time.sleep(2 ** (attempt + 1))
            try:
                r = httpx.post(
                    f"{self.base_url}/chat/completions", json=body, headers=headers, timeout=TIMEOUT
                )
            except httpx.TimeoutException:
                error, status = "timeout", None
                continue
            if r.status_code == 200:
                reply = r.json()
                # OpenRouter는 upstream 오류를 200 + error 본문으로 줄 때가 있다
                if not reply.get("choices"):
                    raise LLMError("bad_response", 200, attempt)
                return reply, 200, attempt
            error, status = str(r.status_code), r.status_code
            if r.status_code not in RETRY_STATUS:
                break
        raise LLMError(error, status, attempt)


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
