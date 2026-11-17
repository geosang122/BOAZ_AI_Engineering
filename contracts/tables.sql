-- 계약: contracts/models.py의 TABLES와 같은 구조. 수정 절차는 contracts/README.md.
-- 이 파일 하나를 ClickHouse와 DuckDB에서 그대로 실행한다 (플랜 B).
--   * 엔진 절을 쓰지 않는다. ClickHouse는 infra/clickhouse/settings.xml이 MergeTree를 기본으로 준다.
--   * 타입은 두 DB 공통 이름만: VARCHAR, BIGINT, DOUBLE, BOOLEAN, TIMESTAMP. 배열은 쓰지 않는다.
--   * NULL 여부를 열마다 적는다.
-- raw는 Collector ClickHouse exporter가 만드는 otel_traces를 그대로 쓴다. 여기서 정의하지 않는다.

-- ── 정답 (HotpotQA) ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS gold_questions (
    question_id VARCHAR NOT NULL,
    answer      VARCHAR NOT NULL,
    qtype       VARCHAR NOT NULL,  -- bridge | comparison
    level       VARCHAR NOT NULL   -- easy | medium | hard
);

CREATE TABLE IF NOT EXISTS gold_paragraphs (
    question_id   VARCHAR NOT NULL,
    title         VARCHAR NOT NULL,
    is_supporting BOOLEAN NOT NULL
);

-- ── clean: Span 종류별로 펼친 것 ───────────────────────────

CREATE TABLE IF NOT EXISTS clean_agent_runs (
    run_id      VARCHAR   NOT NULL,
    question_id VARCHAR   NOT NULL,
    trace_id    VARCHAR   NOT NULL,
    mode        VARCHAR   NOT NULL,
    fault       VARCHAR   NOT NULL,
    model       VARCHAR   NOT NULL,
    start_time  TIMESTAMP NOT NULL,
    duration_ms DOUBLE    NOT NULL,
    answer      VARCHAR   NULL,
    error_type  VARCHAR   NULL
);

CREATE TABLE IF NOT EXISTS clean_llm_calls (
    run_id            VARCHAR NOT NULL,
    question_id       VARCHAR NOT NULL,
    trace_id          VARCHAR NOT NULL,
    span_id           VARCHAR NOT NULL,
    request_model     VARCHAR NOT NULL,
    response_model    VARCHAR NULL,
    upstream_provider VARCHAR NULL,
    http_status       BIGINT  NULL,
    retry_count       BIGINT  NOT NULL,
    input_tokens      BIGINT  NULL,
    output_tokens     BIGINT  NULL,
    duration_ms       DOUBLE  NOT NULL,
    error_type        VARCHAR NULL
);

CREATE TABLE IF NOT EXISTS clean_tool_calls (
    run_id      VARCHAR NOT NULL,
    question_id VARCHAR NOT NULL,
    trace_id    VARCHAR NOT NULL,
    span_id     VARCHAR NOT NULL,
    tool_name   VARCHAR NOT NULL,
    duration_ms DOUBLE  NOT NULL,
    error_type  VARCHAR NULL
);

CREATE TABLE IF NOT EXISTS clean_retrievals (
    run_id      VARCHAR NOT NULL,
    question_id VARCHAR NOT NULL,
    trace_id    VARCHAR NOT NULL,
    span_id     VARCHAR NOT NULL,
    hit_rank    BIGINT  NOT NULL,
    title       VARCHAR NOT NULL
);

-- ── mart ───────────────────────────────────────────────────

-- 실행 × 정답 조인 (역할3)
CREATE TABLE IF NOT EXISTS mart_run_question (
    run_id        VARCHAR NOT NULL,
    question_id   VARCHAR NOT NULL,
    mode          VARCHAR NOT NULL,
    fault         VARCHAR NOT NULL,
    model         VARCHAR NOT NULL,
    answer        VARCHAR NULL,
    gold_answer   VARCHAR NOT NULL,
    qtype         VARCHAR NOT NULL,
    all_http_200  BOOLEAN NOT NULL,
    n_llm_calls   BIGINT  NOT NULL,
    n_tool_calls  BIGINT  NOT NULL,
    input_tokens  BIGINT  NOT NULL,
    output_tokens BIGINT  NOT NULL,
    retry_count   BIGINT  NOT NULL,
    duration_ms   DOUBLE  NOT NULL,
    retrieval_hit BOOLEAN NOT NULL,
    error_type    VARCHAR NULL
);

-- 채점 결과 (역할4)
CREATE TABLE IF NOT EXISTS mart_eval (
    run_id       VARCHAR NOT NULL,
    question_id  VARCHAR NOT NULL,
    em           DOUBLE  NOT NULL,
    f1           DOUBLE  NOT NULL,
    failure_type VARCHAR NOT NULL
);
