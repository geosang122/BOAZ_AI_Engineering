# fixtures/ — 모듈 사이에 주고받는 샘플

다른 사람 작업이 끝나기 전에도 각자 개발할 수 있게, 각 단계의 입력·출력 샘플을 둔다.
모두 같은 실행(`20261118_mock_toolcall_090000`, 4문항)에서 나왔고 `tests/test_contracts.py`가 계약대로인지 검사한다.

| 파일 | 만드는 쪽 → 쓰는 쪽 | 내용 |
|---|---|---|
| `hotpotqa_sample.json` | 데이터 → 역할1·3 | HotpotQA distractor dev 앞 4문항 (원본 모양 그대로) |
| `spans.jsonl` | 역할1 → 역할3 | 플랜 B JSONL 모양의 Span 18개 |
| `mart_run_question.jsonl` | 역할3 → 역할4 | 실행 × 정답 조인 결과 |
| `mart_eval.jsonl` | 역할4 → 대시보드 | 채점 결과. 실패 유형 4종이 하나씩 |

시나리오: 1번 정답+근거 찾음, 2번 정답인데 근거 못 찾음(암기, 재시도 1회), 3번 근거 못 찾고 오답, 4번 근거 찾고 오답.

계약이 바뀌면 이 파일들도 같은 PR에서 고친다.
HotpotQA는 CC BY-SA 4.0 라이선스다.
