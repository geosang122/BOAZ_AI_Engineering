"""실패 유형 분류와 mart_eval 기록, 플랜 B용 터미널 표."""

from contracts.models import FailureType, MartRunQuestion
from storage.backend import Store


def classify(row: MartRunQuestion, correct: bool) -> FailureType:
    """contracts/README.md의 판정표대로. 답이 없으면(row.answer is None) error."""
    # TODO(역할4)
    raise NotImplementedError


def score_run(run_id: str, store: Store) -> None:
    """mart_run_question → EM/F1/분류 → mart_eval. 같은 run_id는 먼저 지운다."""
    # TODO(역할4)
    raise NotImplementedError


def print_report(run_id: str, store: Store) -> None:
    """정답률, 'HTTP 200인데 틀린 답' 수, 실패 유형별 수를 표로 출력 (Grafana가 없는 플랜 B용)."""
    # TODO(역할4)
    raise NotImplementedError
