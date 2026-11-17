"""HotpotQA distractor dev 내려받기와 500문항 뽑기. 규칙은 contracts/README.md의 '데이터'."""

from pathlib import Path

REVISION = "1908d6afbbead072334abe2965f91bd2709910ab"
URL = (
    "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/"
    f"{REVISION}/distractor/validation-00000-of-00001.parquet"
)
CACHE = Path(__file__).resolve().parent / "cache"
SAMPLE_SIZE, SEED = 500, 42


def download() -> Path:
    """CACHE/validation.parquet가 없으면 받는다 (약 27MB). 경로를 돌려준다."""
    # TODO(역할1): httpx로 받기 (follow_redirects=True)
    raise NotImplementedError


def load_sample() -> list[dict]:
    """파일 행 순서 그대로 random.Random(42).sample(rows, 500).

    한 문항 모양은 fixtures/hotpotqa_sample.json과 같다:
    id, question, answer, type, level, supporting_facts{title, sent_id}, context{title, sentences}
    """
    # TODO(역할1): duckdb로 parquet 읽기 (이미 의존성에 있음)
    raise NotImplementedError
