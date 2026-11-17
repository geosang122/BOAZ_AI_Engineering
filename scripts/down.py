"""서버 끄기. --volumes를 붙이면 ClickHouse 데이터까지 지운다 (계약 테이블이 바뀌었을 때)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

subprocess.run(["docker", "compose", "down", *sys.argv[1:]], cwd=ROOT, check=True)
