"""실패 유형 분류와 mart_eval 기록, 플랜 B용 터미널 표."""

from contracts.models import FailureType, MartEval, MartRunQuestion
from eval.metrics import exact_match, f1
from storage.backend import Store
from storage.transform import check_run_id

WRONG = (FailureType.WRONG_RETRIEVAL, FailureType.WRONG_REASONING)


def classify(row: MartRunQuestion, correct: bool) -> FailureType:
    """contracts/README.md의 판정표대로. 답이 없으면(row.answer is None) error."""
    if row.answer is None:
        return FailureType.ERROR
    if correct:
        return FailureType.CORRECT_GROUNDED if row.retrieval_hit else FailureType.CORRECT_MEMORIZED
    return FailureType.WRONG_REASONING if row.retrieval_hit else FailureType.WRONG_RETRIEVAL


def score_run(run_id: str, store: Store) -> None:
    """mart_run_question → EM/F1/분류 → mart_eval. 같은 run_id는 먼저 지운다."""
    check_run_id(run_id)
    cols = list(MartRunQuestion.model_fields)
    result = store.query(
        f"SELECT {', '.join(cols)} FROM mart_run_question WHERE run_id = '{run_id}'"
    )
    rows = [MartRunQuestion(**dict(zip(cols, r, strict=True))) for r in result]
    scored = []
    for row in rows:
        em = exact_match(row.answer, row.gold_answer) if row.answer is not None else 0.0
        f = f1(row.answer, row.gold_answer) if row.answer is not None else 0.0
        scored.append(
            MartEval(
                run_id=run_id,
                question_id=row.question_id,
                em=em,
                f1=f,
                failure_type=classify(row, correct=em == 1.0),  # 정답 기준: eval/README.md
            )
        )
    store.execute(f"DELETE FROM mart_eval WHERE run_id = '{run_id}'")
    store.insert("mart_eval", scored)


def print_report(run_id: str, store: Store) -> None:
    """정답률, 'HTTP 200인데 틀린 답' 수, 실패 유형별 수를 표로 출력 (Grafana가 없는 플랜 B용)."""
    check_run_id(run_id)
    rows = store.query(
        "SELECT e.em, e.f1, e.failure_type, m.all_http_200 "
        "FROM mart_eval AS e JOIN mart_run_question AS m "
        "ON m.run_id = e.run_id AND m.question_id = e.question_id "
        f"WHERE e.run_id = '{run_id}'"
    )
    n = len(rows)
    if not n:
        print(f"{run_id}: 채점된 문항이 없다")
        return
    correct = sum(1 for em, *_ in rows if em == 1.0)
    wrong_200 = sum(1 for _, _, ft, ok in rows if ok and ft in WRONG)
    print(f"run_id               {run_id}")
    print(f"문항                 {n}")
    print(f"정답 (EM)            {correct} ({correct / n:.1%})")
    print(f"평균 F1              {sum(r[1] for r in rows) / n:.3f}")
    print(f"HTTP 200인데 틀린 답 {wrong_200} ({wrong_200 / n:.1%})")
    print()
    print(f"{'failure_type':<20} {'n':>4} {'비율':>7}")
    for ft in FailureType:
        k = sum(1 for r in rows if r[2] == ft)
        print(f"{ft.value:<20} {k:>4} {k / n:>7.1%}")
