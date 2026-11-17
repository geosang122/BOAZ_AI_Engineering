"""Agent 실행: 문항마다 run_question → Span. 끝나면 run_id를 출력한다.

예: uv run python scripts/run_agent.py --mock --limit 3
모드·장애는 .env의 AGENT_MODE, AGENT_FAULT. 보낼 곳은 AGENTSCOPE_BACKEND.
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from agent.llm import MockLLM, OpenRouterClient
from agent.loop import run_question
from contracts.models import Fault, Mode, ResourceAttrs, make_run_id
from data.hotpotqa import load_sample
from telemetry.otel import setup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="앞에서 N문항만")
    parser.add_argument("--mock", action="store_true", help="네트워크 없이 MockLLM")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    mode = Mode(os.environ.get("AGENT_MODE", "toolcall"))
    fault = Fault(os.environ.get("AGENT_FAULT", "none"))
    run_id = make_run_id("mock" if args.mock else os.environ["LLM_MODEL_ALIAS"], mode)
    llm = MockLLM() if args.mock else OpenRouterClient.from_env()
    provider = setup(ResourceAttrs(run_id=run_id, mode=mode, fault=fault))
    try:
        for item in load_sample()[: args.limit]:
            run_question(item, llm, mode, fault)
    finally:
        provider.shutdown()
    print(run_id)


if __name__ == "__main__":
    main()
