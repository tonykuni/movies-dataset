-- VAP Panorama Maturity Optimization Query Pack

SELECT * FROM panorama_maturity_matrix ORDER BY score DESC;
SELECT * FROM panorama_optimization_backlog ORDER BY priority;
SELECT * FROM panorama_duckdb_table_audit ORDER BY maturity_role, table;
SELECT * FROM panorama_version_audit ORDER BY version;
SELECT * FROM panorama_parquet_audit ORDER BY file_name;

-- Where quant is still plan-only
SELECT * FROM panorama_maturity_matrix
WHERE gaps LIKE '%plan-only%' OR gaps LIKE '%live price%';

-- Core quant tables
SELECT * FROM quant_normalized_returns_v7 LIMIT 50;
SELECT * FROM quant_rolling_correlation_v7 LIMIT 50;
SELECT * FROM quant_lead_lag_score_v7 LIMIT 50;
