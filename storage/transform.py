"""raw → clean → mart. 같은 run_id로 다시 돌려도 결과가 같다 (먼저 지우고 넣는다)."""

from pathlib import Path

from contracts.models import (
    RUN_ID_RE,
    SPAN_ATTRS,
    ChatAttrs,
    CleanAgentRun,
    CleanLlmCall,
    CleanRetrieval,
    CleanToolCall,
    ExecuteToolAttrs,
    InvokeAgentAttrs,
    ResourceAttrs,
)
from storage.backend import Store
from storage.raw import read_raw

SQL_DIR = Path(__file__).resolve().parent / "sql"
OP_KEY = InvokeAgentAttrs.model_fields["operation_name"].alias
CLEAN_TABLES = {
    CleanAgentRun: "clean_agent_runs",
    CleanLlmCall: "clean_llm_calls",
    CleanToolCall: "clean_tool_calls",
    CleanRetrieval: "clean_retrievals",
}


def check_run_id(run_id: str) -> str:
    """SQL에 그대로 넣으므로 규칙에 맞는 run_id만 받는다."""
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"run_id 규칙 위반: {run_id!r}")
    return run_id


def raw_to_clean(run_id: str, store: Store) -> None:
    """파이썬으로 펼친다 (두 DB 공통).

    storage.raw.read_raw → contracts 모델로 검증 → clean_* 4개에 insert.

    question_id는 같은 trace의 invoke_agent Span에서 가져온다.
    """
    check_run_id(run_id)
    spans = [
        (s, SPAN_ATTRS[s["attributes"][OP_KEY]].model_validate(s["attributes"]))
        for s in read_raw(run_id, store)
    ]
    question_of = {
        s["trace_id"]: a.question_id for s, a in spans if isinstance(a, InvokeAgentAttrs)
    }
    rows: dict[type, list] = {model: [] for model in CLEAN_TABLES}
    for s, a in spans:
        qid = question_of.get(s["trace_id"])
        if qid is None:  # 루트가 없는 trace (실행이 중간에 죽음)는 질문에 묶을 수 없다
            continue
        base = {"run_id": run_id, "question_id": qid, "trace_id": s["trace_id"]}
        if isinstance(a, InvokeAgentAttrs):
            res = ResourceAttrs.model_validate(
                {k: v for k, v in s["resource"].items() if k.startswith("agentscope.")}
            )
            rows[CleanAgentRun].append(
                CleanAgentRun(
                    **base,
                    mode=res.mode,
                    fault=res.fault,
                    model=a.request_model,
                    start_time=s["start_time"],
                    duration_ms=s["duration_ms"],
                    answer=a.answer,
                    error_type=a.error_type,
                )
            )
            continue
        base["span_id"] = s["span_id"]
        if isinstance(a, ChatAttrs):
            rows[CleanLlmCall].append(
                CleanLlmCall(
                    **base,
                    request_model=a.request_model,
                    response_model=a.response_model,
                    upstream_provider=a.upstream_provider,
                    http_status=a.http_status,
                    retry_count=a.retry_count,
                    input_tokens=a.input_tokens,
                    output_tokens=a.output_tokens,
                    duration_ms=s["duration_ms"],
                    error_type=a.error_type,
                )
            )
        elif isinstance(a, ExecuteToolAttrs):
            rows[CleanToolCall].append(
                CleanToolCall(
                    **base,
                    tool_name=a.tool_name,
                    duration_ms=s["duration_ms"],
                    error_type=a.error_type,
                )
            )
            rows[CleanRetrieval] += [
                CleanRetrieval(**base, hit_rank=rank, title=title)
                for rank, title in enumerate(a.retrieved_titles, start=1)
            ]
    for model, table in CLEAN_TABLES.items():
        store.execute(f"DELETE FROM {table} WHERE run_id = '{run_id}'")
        store.insert(table, rows[model])


def clean_to_mart(run_id: str, store: Store) -> None:
    """sql/mart_run_question.sql을 두 DB에서 그대로 실행한다 (두 DB 공통 SQL만 쓴다)."""
    check_run_id(run_id)
    sql = (SQL_DIR / "mart_run_question.sql").read_text(encoding="utf-8")
    store.execute(f"DELETE FROM mart_run_question WHERE run_id = '{run_id}'")
    store.execute(sql.format(run_id=run_id))
