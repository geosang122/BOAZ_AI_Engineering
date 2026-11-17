"""서버 3개(Collector, ClickHouse, Grafana) 켜기. Grafana: http://localhost:3000 (admin/admin)"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if not (ROOT / ".env").exists():
    raise SystemExit(".env가 없다: .env.example을 복사해 .env를 만든다")
subprocess.run(["docker", "compose", "up", "-d", "--wait"], cwd=ROOT, check=True)
