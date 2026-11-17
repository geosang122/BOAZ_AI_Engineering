"""채점: mart_run_question → mart_eval, 그리고 결과 표 출력.

예: uv run python scripts/evaluate.py 20261118_qwen_toolcall_113006
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from eval.classify import print_report, score_run
from storage.backend import Store


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    store = Store()
    score_run(args.run_id, store)
    print_report(args.run_id, store)


if __name__ == "__main__":
    main()
