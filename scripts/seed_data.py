"""데이터 넣기.

기본:       HotpotQA 500문항 → gold_questions, gold_paragraphs
--fixtures: fixtures/의 mart 샘플 → mart_run_question, mart_eval (대시보드·채점 개발용)
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from data.hotpotqa import download, load_sample
from storage.backend import Store, load_fixtures
from storage.gold import load_gold


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", action="store_true", help="mart 샘플만 넣는다")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    store = Store()
    if args.fixtures:
        print(*load_fixtures(store), sep="\n")
        return
    download()
    load_gold(load_sample(), store)


if __name__ == "__main__":
    main()
