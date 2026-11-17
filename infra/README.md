# infra/ — 서버 설정

담당: 역할2. 서버는 루트의 `docker-compose.yml`로 띄운다 (`scripts/up.py`).

| 파일 | 내용 |
|---|---|
| `collector.yaml` | OTLP/HTTP :4318 받기 → ClickHouse `otel_traces` (exporter 기본 테이블) |
| `clickhouse/settings.xml` | 기본 엔진 MergeTree. 그래서 `contracts/tables.sql`에 엔진 절이 없어도 된다 |
| `grafana/datasource.yaml` | Grafana → ClickHouse 연결 (uid `clickhouse`) |

- 포트: Collector 4318, ClickHouse 8123(HTTP)/9000(native), Grafana 3000
- 계정은 `.env`의 `CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD`, Grafana는 admin/admin
- 버전 고정: ClickHouse 26.8.34.13, Collector contrib 0.164.0, Grafana 13.3.0, ClickHouse 플러그인 4.23.2
- ClickHouse 테이블은 처음 뜰 때 한 번 만들어진다. 계약이 바뀌면 `scripts/down.py --volumes` 후 `up.py`
