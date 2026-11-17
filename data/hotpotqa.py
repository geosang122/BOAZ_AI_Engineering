"""HotpotQA distractor dev 내려받기와 500문항 뽑기. 규칙은 contracts/README.md의 '데이터'."""

import random
from pathlib import Path

import duckdb
import httpx

REVISION = "1908d6afbbead072334abe2965f91bd2709910ab"
URL = (
    "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/"
    f"{REVISION}/distractor/validation-00000-of-00001.parquet"
)
CACHE = Path(__file__).resolve().parent / "cache"
SAMPLE_SIZE, SEED = 500, 42


def download() -> Path:
    """CACHE/validation.parquet가 없으면 받는다 (약 27MB). 경로를 돌려준다."""
    path = CACHE / "validation.parquet"
    if path.exists():
        return path
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")  # 받다 끊겨도 반쪽 파일이 캐시로 남지 않게
    with httpx.stream("GET", URL, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    tmp.replace(path)
    return path


def load_sample() -> list[dict]:
    """파일 행 순서 그대로 random.Random(42).sample(rows, 500).

    한 문항 모양은 fixtures/hotpotqa_sample.json과 같다:
    id, question, answer, type, level, supporting_facts{title, sent_id}, context{title, sentences}
    """
    con = duckdb.connect()
    # 행 순서가 seed 결과를 정하므로 file_row_number로 순서를 못 박는다
    rel = con.execute(
        "SELECT * EXCLUDE (file_row_number) FROM read_parquet(?, file_row_number = true) "
        "ORDER BY file_row_number",
        [str(download())],
    )
    cols = [d[0] for d in rel.description]
    rows = [dict(zip(cols, r, strict=True)) for r in rel.fetchall()]
    return random.Random(SEED).sample(rows, SAMPLE_SIZE)
