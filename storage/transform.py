"""raw → clean → mart. 같은 run_id로 다시 돌려도 결과가 같다 (먼저 지우고 넣는다)."""

from pathlib import Path

from storage.backend import Store

SQL_DIR = Path(__file__).resolve().parent / "sql"


def raw_to_clean(run_id: str, store: Store) -> None:
    """파이썬으로 펼친다 (두 DB 공통).

    storage.raw.read_raw → contracts 모델로 검증 → clean_* 4개에 insert.

    question_id는 같은 trace의 invoke_agent Span에서 가져온다.
    """
    # TODO(역할3)
    raise NotImplementedError


def clean_to_mart(run_id: str, store: Store) -> None:
    """sql/mart_run_question.sql을 두 DB에서 그대로 실행한다 (두 DB 공통 SQL만 쓴다)."""
    # TODO(역할3)
    raise NotImplementedError
