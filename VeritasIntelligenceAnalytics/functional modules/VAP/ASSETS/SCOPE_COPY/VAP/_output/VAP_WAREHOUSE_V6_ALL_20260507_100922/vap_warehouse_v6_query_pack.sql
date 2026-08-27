-- VAP Warehouse V6 Query Pack

SELECT * FROM generated_dashboard_registry ORDER BY blueprint_id;
SELECT * FROM live_fetch_status_v6 ORDER BY market, ticker;
SELECT * FROM live_price_sample_v6 LIMIT 100;
SELECT * FROM normalized_price_series_v6 LIMIT 100;
SELECT * FROM rolling_correlation_plan ORDER BY window, left_ticker, right_ticker;
SELECT * FROM lead_lag_plan ORDER BY leader, follower, lag_days;
SELECT * FROM dashboard_blueprint_registry ORDER BY confidence DESC;
SELECT * FROM cross_asset_relation_registry;
SELECT * FROM coaxis_policy_registry ORDER BY priority DESC;
