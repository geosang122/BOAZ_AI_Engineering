# 협업 규칙

## 브랜치와 PR

- 브랜치 이름: `feat/<역할>-<기능>`. 역할은 `agent`, `telemetry`, `storage`, `eval`. 예: `feat/agent-react-mode`
- `main`에 직접 push하지 않는다. PR → 리뷰 1명 승인 → CI 통과 → 병합.
- 담당 폴더 밖을 고쳤으면 PR 설명에 적는다: `담당 밖 수정: <경로> — <이유>`
- 계약(`contracts/`)을 바꾸는 PR은 계약만 담고, **리더 승인**이 있어야 통과한다 (CI 검사 `leader-approved`).

## 커밋 전

```
uv run ruff check --fix .
uv run ruff format .
uv run pytest
```

`uv run pre-commit install`을 해 두면 ruff는 커밋할 때 자동으로 돈다.

## 의존성

- 추가: `uv add <패키지>` (개발용은 `uv add --dev`). `pyproject.toml`과 `uv.lock`을 같이 커밋한다.
- Agent 프레임워크(LangChain 등)는 쓰지 않는다.
- `uv.lock` 충돌이 나면 고치지 말고 main 것을 받은 뒤 다시 만든다:

```
git fetch origin
git merge origin/main
git checkout origin/main -- uv.lock
uv lock
git add uv.lock
git commit
```

## 코드

- 경로는 `pathlib`만 쓴다. 파일은 `encoding="utf-8"`로 연다.
- 셸 스크립트·Makefile 대신 `scripts/*.py`.
- 줄바꿈은 `.gitattributes`가 LF로 맞춘다.

## GitHub 설정 (리더가 한 번)

1. `.github/CODEOWNERS`의 `@LEADER`, `@ROLE1`~`@ROLE4`와
   `.github/workflows/contracts-approval.yml`의 `LEADER_GITHUB_ID`를 실제 아이디로 바꾼다.
2. Settings → Branches → `main` 보호 규칙 추가:
   - Require a pull request before merging → Required approvals: **1**
   - Require status checks to pass: `check (ubuntu-latest)`, `check (windows-latest)`, `leader-approved`
   - "Require review from Code Owners"는 **끈다**. 켜면 폴더 담당자가 자기 PR을 병합할 수 없다 (본인 승인 불가).
