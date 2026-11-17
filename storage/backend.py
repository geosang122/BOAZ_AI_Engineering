"""저장소 연결. AGENTSCOPE_BACKEND(telemetry와 같은 설정)로 ClickHouse/DuckDB를 고른다.

두 DB를 같은 세 함수(execute, query, insert)로 다룬다 → 같은 SQL을 그대로 돌린다 (플랜 B).
ClickHouse 테이블은 서버가 처음 뜰 때 contracts/tables.sql로 만들어진다 (docker-compose.yml).
"""

import os
from pathlib import Path

from pydantic import BaseModel

from contracts.models import TABLES
from telemetry.otel import backend

ROOT = Path(__file__).resolve().parents[1]
TABLES_SQL = ROOT / "contracts" / "tables.sql"
DUCKDB_PATH = ROOT / "runs" / "agentscope.duckdb"
FIXTURES = ROOT / "fixtures"


class Store:
    def __init__(self, kind: str | None = None, duckdb_path: Path = DUCKDB_PATH):
        self.kind = kind or backend()
        if self.kind == "clickhouse":
            import clickhouse_connect

            self._ch = clickhouse_connect.get_client(
                host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
                port=int(os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")),
                username=os.environ.get("CLICKHOUSE_USER", "default"),
                password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
            )
        else:
            import duckdb

            duckdb_path.parent.mkdir(parents=True, exist_ok=True)
            self._duck = duckdb.connect(str(duckdb_path))
            self._duck.execute(TABLES_SQL.read_text(encoding="utf-8"))

    def execute(self, sql: str) -> None:
        if self.kind == "clickhouse":
            self._ch.command(sql)
        else:
            self._duck.execute(sql)

    def query(self, sql: str) -> list[tuple]:
        if self.kind == "clickhouse":
            return self._ch.query(sql).result_rows
        return self._duck.execute(sql).fetchall()

    def insert(self, table: str, rows: list[BaseModel]) -> None:
        """계약 테이블에 계약 모델 행만 넣는다."""
        model = TABLES[table]
        if not all(type(r) is model for r in rows):
            raise TypeError(f"{table}에는 {model.__name__} 행만 넣는다")
        if not rows:
            return
        columns = list(model.model_fields)
        data = [list(r.model_dump().values()) for r in rows]
        if self.kind == "clickhouse":
            self._ch.insert(table, data, column_names=columns)
        else:
            marks = ", ".join("?" * len(columns))
            self._duck.executemany(
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})", data
            )


def load_fixtures(store: Store) -> list[str]:
    """fixtures/의 mart 샘플을 넣는다 (대시보드·채점을 첫날부터 만들 수 있게).

    다시 넣어도 겹치지 않는다.
    """
    loaded = []
    for table in ("mart_run_question", "mart_eval"):
        model = TABLES[table]
        text = (FIXTURES / f"{table}.jsonl").read_text(encoding="utf-8")
        rows = [model.model_validate_json(line) for line in text.splitlines() if line]
        for run_id in sorted({r.run_id for r in rows}):
            store.execute(f"DELETE FROM {table} WHERE run_id = '{run_id}'")
        store.insert(table, rows)
        loaded.append(f"{table}: {len(rows)}행")
    return loaded
