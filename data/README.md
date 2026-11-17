# data/ — HotpotQA 로더

담당: 역할1

- **입력**: Hugging Face `hotpotqa/hotpot_qa` distractor validation parquet (리비전 고정, `contracts/README.md`)
- **출력**: 500문항 `list[dict]`. 모양은 `fixtures/hotpotqa_sample.json`
- **실행**: `uv run python scripts/seed_data.py` (정답 적재까지)
- 받은 파일은 `data/cache/`에 둔다 (git 제외)

| 함수 | 내용 |
|---|---|
| `download()` | parquet 받기 (TODO) |
| `load_sample()` | 행 순서 그대로 `random.Random(42).sample(rows, 500)` (TODO) |
