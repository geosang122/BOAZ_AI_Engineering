# dashboard/ — Grafana 대시보드와 알림

담당: 역할4. Grafana가 뜰 때 이 폴더를 읽는다 (provisioning, `docker-compose.yml`).

- **입력**: ClickHouse의 `mart_run_question`, `mart_eval`
- **확인**: `scripts/up.py` → `scripts/seed_data.py --fixtures` → http://localhost:3000 대시보드 `AgentScope`

| 파일 | 내용 |
|---|---|
| `agentscope.json` | 대시보드. 지금은 '실행별 결과' 표 하나 |
| `alerts.yaml` | 알림 규칙. 지금은 'HTTP 200인데 틀린 답 비율 50% 초과' 하나 |
| `provider.yaml` | 이 폴더의 *.json을 대시보드로 올리는 설정 |

TODO: 실패 유형 막대, 모드별(toolcall/react/closedbook)·장애별 비교, 토큰·지연·재시도 패널, 알림 받을 곳(contact point).
Grafana 화면에서 고친 뒤 JSON으로 내보내 `agentscope.json`에 덮어쓰면 된다.
