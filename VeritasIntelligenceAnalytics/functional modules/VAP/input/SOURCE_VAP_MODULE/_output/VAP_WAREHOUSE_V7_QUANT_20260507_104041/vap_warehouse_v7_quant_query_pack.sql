-- VAP Warehouse V7 Quant Intelligence Query Pack

SELECT * FROM quant_normalized_returns_v7 LIMIT 200;
SELECT * FROM quant_rolling_correlation_v7 ORDER BY window, left_ticker, right_ticker;
SELECT * FROM quant_lead_lag_score_v7 WHERE lag_corr IS NOT NULL ORDER BY ABS(lag_corr) DESC LIMIT 100;
SELECT * FROM quant_factor_plan_v7;
SELECT * FROM quant_regime_plan_v7;
SELECT * FROM rolling_correlation_plan LIMIT 200;
SELECT * FROM lead_lag_plan LIMIT 200;
