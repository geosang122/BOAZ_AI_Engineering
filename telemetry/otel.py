"""OTel 초기화. 설정 하나(AGENTSCOPE_BACKEND)로 Span을 보낼 곳을 바꾼다.

clickhouse (기본): OTLP/HTTP → Collector → ClickHouse otel_traces.
                   주소는 OTEL_EXPORTER_OTLP_ENDPOINT.
duckdb (플랜 B):   runs/{run_id}.jsonl에 Span을 한 줄씩 쓴다. 서버가 필요 없다.
"""

import os
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from contracts.models import ResourceAttrs

RUNS_DIR = Path(__file__).resolve().parents[1] / "runs"


def backend() -> str:
    value = os.environ.get("AGENTSCOPE_BACKEND", "clickhouse")
    if value not in ("clickhouse", "duckdb"):
        raise ValueError(f"AGENTSCOPE_BACKEND는 clickhouse 또는 duckdb: {value!r}")
    return value


def jsonl_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.jsonl"


def setup(resource: ResourceAttrs) -> TracerProvider:
    """전역 TracerProvider를 만든다.

    실행이 끝나면 provider.shutdown()을 꼭 불러 남은 Span을 보낸다.
    """
    attrs = {"service.name": "agentscope", **resource.otel()}
    provider = TracerProvider(resource=Resource.create(attrs))
    if backend() == "duckdb":
        path = jsonl_path(resource.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        out = path.open("a", encoding="utf-8", newline="\n")
        exporter = ConsoleSpanExporter(out=out, formatter=lambda s: s.to_json(indent=None) + "\n")
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider
