-- clean_* × gold_* → mart_run_question (한 run_id). ClickHouse와 DuckDB에서 그대로 돈다.
-- 두 DB 공통 문법만 쓴다: CAST, CASE, COALESCE, count, sum, max, JOIN, 서브쿼리.
-- 판정 규칙(retrieval_hit, all_http_200)은 contracts/README.md.
-- LEFT JOIN에서 짝이 없으면 DuckDB는 NULL, ClickHouse는 0을 준다 → COALESCE(…, 0)로 맞춘다.
INSERT INTO mart_run_question
SELECT
    a.run_id AS run_id,
    a.question_id AS question_id,
    a.mode AS mode,
    a.fault AS fault,
    a.model AS model,
    a.answer AS answer,
    q.answer AS gold_answer,
    q.qtype AS qtype,
    COALESCE(l.n_not_200, 0) = 0 AS all_http_200,
    CAST(COALESCE(l.n_calls, 0) AS BIGINT) AS n_llm_calls,
    CAST(COALESCE(t.n_calls, 0) AS BIGINT) AS n_tool_calls,
    CAST(COALESCE(l.input_tokens, 0) AS BIGINT) AS input_tokens,
    CAST(COALESCE(l.output_tokens, 0) AS BIGINT) AS output_tokens,
    CAST(COALESCE(l.retry_count, 0) AS BIGINT) AS retry_count,
    a.duration_ms AS duration_ms,
    COALESCE(h.n_found, 0) = s.n_support AS retrieval_hit,
    a.error_type AS error_type
FROM clean_agent_runs AS a
JOIN gold_questions AS q ON q.question_id = a.question_id
JOIN (
    SELECT question_id, count(DISTINCT title) AS n_support
    FROM gold_paragraphs
    WHERE is_supporting
    GROUP BY question_id
) AS s ON s.question_id = a.question_id
LEFT JOIN (
    SELECT
        trace_id,
        count(*) AS n_calls,
        sum(CASE WHEN http_status = 200 THEN 0 ELSE 1 END) AS n_not_200,
        sum(COALESCE(input_tokens, 0)) AS input_tokens,
        sum(COALESCE(output_tokens, 0)) AS output_tokens,
        sum(retry_count) AS retry_count
    FROM clean_llm_calls
    WHERE run_id = '{run_id}'
    GROUP BY trace_id
) AS l ON l.trace_id = a.trace_id
LEFT JOIN (
    SELECT trace_id, count(*) AS n_calls
    FROM clean_tool_calls
    WHERE run_id = '{run_id}'
    GROUP BY trace_id
) AS t ON t.trace_id = a.trace_id
LEFT JOIN (
    SELECT r.trace_id AS trace_id, count(DISTINCT r.title) AS n_found
    FROM clean_retrievals AS r
    JOIN gold_paragraphs AS p ON p.question_id = r.question_id AND p.title = r.title
    WHERE r.run_id = '{run_id}' AND p.is_supporting
    GROUP BY r.trace_id
) AS h ON h.trace_id = a.trace_id
WHERE a.run_id = '{run_id}'
