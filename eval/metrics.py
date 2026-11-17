"""EM/F1 채점. HotpotQA 공식 채점기(hotpot_evaluate_v1.py)와 같은 정규화를 쓴다."""


def normalize_answer(text: str) -> str:
    """소문자, 구두점·관사(a, an, the) 제거, 공백 정리."""
    # TODO(역할4)
    raise NotImplementedError


def exact_match(prediction: str, gold: str) -> float:
    """정규화 후 같으면 1.0, 아니면 0.0."""
    # TODO(역할4)
    raise NotImplementedError


def f1(prediction: str, gold: str) -> float:
    """정규화 후 단어 단위 F1. yes/no/noanswer는 정확히 같을 때만 점수."""
    # TODO(역할4)
    raise NotImplementedError
