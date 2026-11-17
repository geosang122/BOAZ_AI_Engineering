"""정답·근거 라벨 적재: HotpotQA 문항 → gold_questions, gold_paragraphs."""

from storage.backend import Store


def load_gold(items: list[dict], store: Store) -> None:
    """문항마다 gold_questions 1행 + gold_paragraphs 10행 (근거 제목이면 is_supporting=true).

    supporting_facts.title에는 같은 제목이 여러 번 나온다 (문장마다). 집합으로 본다.
    """
    # TODO(역할3): 다시 넣어도 겹치지 않게
    raise NotImplementedError
