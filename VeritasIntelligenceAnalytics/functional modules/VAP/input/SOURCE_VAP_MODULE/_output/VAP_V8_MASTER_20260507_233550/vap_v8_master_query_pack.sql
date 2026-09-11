-- VAP V8 Master Query Pack
SELECT * FROM vap_v8_maturity_matrix ORDER BY score DESC;
SELECT * FROM generated_data_bound_dashboard_registry_v8 ORDER BY blueprint_id;
SELECT * FROM visual_token_normalized_registry_v8 ORDER BY governance_role, normalized_token_type;
SELECT * FROM quant_normalized_returns_v8 LIMIT 200;
SELECT * FROM quant_rolling_correlation_v8 ORDER BY window, left_ticker, right_ticker;
SELECT * FROM quant_lead_lag_score_v8 WHERE lag_corr IS NOT NULL ORDER BY ABS(lag_corr) DESC LIMIT 100;
SELECT * FROM live_fetch_status_v8 ORDER BY market, ticker;
SELECT * FROM vap_v8_completion_table_status ORDER BY table;
