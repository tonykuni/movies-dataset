-- VAP DuckDB Query Pack v2
-- VERITAS INTELLIGENCE ANALYTICS

-- 01. Taxonomy Inventory
SELECT taxonomy, COUNT(*) AS asset_count
FROM asset_registry_v4
GROUP BY taxonomy
ORDER BY asset_count DESC;

-- 02. Active Warnings Only
SELECT *
FROM warning_assets_v4
WHERE warning_reason IS NOT NULL
  AND TRIM(CAST(warning_reason AS VARCHAR)) <> ''
  AND LOWER(TRIM(CAST(warning_reason AS VARCHAR))) NOT IN ('none', 'null', 'nan');

-- 03. 雙軸模板
SELECT asset_id, file_name, taxonomy, best_template, axes
FROM asset_registry_v4
WHERE axes = 2
ORDER BY file_name;

-- 04. Heatmap / Event Matrix / Stack
SELECT asset_id, file_name, taxonomy, supports_heatmap, supports_event_matrix, supports_stack
FROM asset_registry_v4
WHERE supports_heatmap OR supports_event_matrix OR supports_stack
ORDER BY taxonomy, file_name;

-- 05. Component Registry
SELECT component_type, COUNT(*) AS n, AVG(confidence) AS avg_confidence
FROM component_registry
GROUP BY component_type
ORDER BY n DESC;

-- 06. Visual Token Registry
SELECT token_type, COUNT(*) AS n
FROM visual_token_registry
GROUP BY token_type
ORDER BY n DESC;

-- 07. Schema Intelligence
SELECT schema_role, suggested_template, COUNT(*) AS n
FROM schema_intelligence_registry
GROUP BY schema_role, suggested_template
ORDER BY n DESC;

-- 08. Alignment Policies
SELECT market, timezone_policy, calendar_policy, COUNT(*) AS n
FROM alignment_policy_registry
GROUP BY market, timezone_policy, calendar_policy
ORDER BY n DESC;

-- 09. Auto Dashboard Composition
SELECT *
FROM auto_dashboard_registry
ORDER BY confidence DESC;
