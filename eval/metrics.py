"""EM/F1 채점. HotpotQA 공식 채점기(hotpot_evaluate_v1.py)와 같은 정규화를 쓴다."""

import re
import string
from collections import Counter

PUNCT = set(string.punctuation)
SPECIAL = ("yes", "no", "noanswer")


def normalize_answer(text: str) -> str:
    """소문자, 구두점·관사(a, an, the) 제거, 공백 정리."""
    text = "".join(ch for ch in text.lower() if ch not in PUNCT)
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def exact_match(prediction: str, gold: str) -> float:
    """정규화 후 같으면 1.0, 아니면 0.0."""
    return float(normalize_answer(prediction) == normalize_answer(gold))


def f1(prediction: str, gold: str) -> float:
    """정규화 후 단어 단위 F1. yes/no/noanswer는 정확히 같을 때만 점수."""
    pred, ref = normalize_answer(prediction), normalize_answer(gold)
    if (pred in SPECIAL or ref in SPECIAL) and pred != ref:
        return 0.0
    pred_tokens, ref_tokens = pred.split(), ref.split()
    same = sum((Counter(pred_tokens) & Counter(ref_tokens)).values())
    if same == 0:
        return 0.0
    precision, recall = same / len(pred_tokens), same / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)
