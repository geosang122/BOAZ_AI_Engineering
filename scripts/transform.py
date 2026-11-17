"""raw → clean → mart. 예: uv run python scripts/transform.py 20261118_qwen_toolcall_113006"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from storage.backend import Store
from storage.transform import clean_to_mart, raw_to_clean


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    store = Store()
    raw_to_clean(args.run_id, store)
    clean_to_mart(args.run_id, store)


if __name__ == "__main__":
    main()
