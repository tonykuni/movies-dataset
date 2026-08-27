-- VAP Warehouse V5 Next3 Query Pack
-- VERITAS INTELLIGENCE ANALYTICS

-- 01 Live Data Sources
SELECT * FROM live_data_source_registry ORDER BY source_id;

-- 02 Fetch Plans
SELECT * FROM fetch_plan_registry ORDER BY market, ticker;

-- 03 AI Dashboard Blueprints
SELECT blueprint_id, title, layout, confidence, status
FROM dashboard_blueprint_registry
ORDER BY confidence DESC;

-- 04 Composer Recommendations
SELECT *
FROM dashboard_composer_recommendations
ORDER BY priority DESC, blueprint_id;

-- 05 Timeline Alignment
SELECT market, timezone_policy, calendar_policy, COUNT(*) AS n
FROM timeline_alignment_registry
GROUP BY market, timezone_policy, calendar_policy
ORDER BY n DESC;

-- 06 Cross Asset Relations
SELECT *
FROM cross_asset_relation_registry
ORDER BY relation_id;

-- 07 Coaxis Policies
SELECT *
FROM coaxis_policy_registry
ORDER BY priority DESC;

-- 08 Visual Token Summary
SELECT token_type, COUNT(*) AS n
FROM visual_token_registry
GROUP BY token_type
ORDER BY n DESC;

-- 09 Component Summary
SELECT component_type, COUNT(*) AS n, AVG(confidence) AS avg_confidence
FROM component_registry
GROUP BY component_type
ORDER BY n DESC;
