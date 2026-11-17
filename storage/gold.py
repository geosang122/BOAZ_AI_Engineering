"""정답·근거 라벨 적재: HotpotQA 문항 → gold_questions, gold_paragraphs."""

from contracts.models import GoldParagraph, GoldQuestion
from storage.backend import Store


def load_gold(items: list[dict], store: Store) -> None:
    """문항마다 gold_questions 1행 + gold_paragraphs 10행 (근거 제목이면 is_supporting=true).

    supporting_facts.title에는 같은 제목이 여러 번 나온다 (문장마다). 집합으로 본다.
    """
    questions, paragraphs = [], []
    for item in items:
        qid = item["id"]
        supporting = set(item["supporting_facts"]["title"])
        questions.append(
            GoldQuestion(
                question_id=qid, answer=item["answer"], qtype=item["type"], level=item["level"]
            )
        )
        paragraphs += [
            GoldParagraph(question_id=qid, title=title, is_supporting=title in supporting)
            for title in item["context"]["title"]
        ]
    if not questions:
        return
    # SQL에 그대로 넣으므로 확인한다 (HotpotQA id는 16진수)
    if not all(q.question_id.isalnum() for q in questions):
        raise ValueError("question_id는 영숫자만")
    ids = ", ".join(f"'{q.question_id}'" for q in questions)
    for table, rows in (("gold_questions", questions), ("gold_paragraphs", paragraphs)):
        store.execute(f"DELETE FROM {table} WHERE question_id IN ({ids})")
        store.insert(table, rows)
