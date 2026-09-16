# VIA 引擎總目錄 v0100(逐引擎詳細功能)

引擎 804 支 · 20260915_205620 · 原則:零發明:說明=AST 實抽 docstring;函式/CLI/邊=合約冊實值

| SYS | 支數 | 自測具備 |
|---|---|---|
| CHW · 籌碼戰 | 6 | 0 |
| FLOW · 資金流 | 24 | 6 |
| GRP · 族群指數 | 41 | 4 |
| PLG · 插件 | 17 | 0 |
| VAP · 視覺分析 | 202 | 13 |
| VDF · 數據鍛造 | 146 | 41 |
| VIA · 泛功能 | 59 | 2 |
| VRN · 報告情報 | 309 | 32 |

## CHW · 籌碼戰(6 支)

### CHW_ENG001_ChipWarConsole
- **族**:`functional modules/ChipWar/engines/VIA_ChipWar_Console`(版本 1;現役 `VIA_ChipWar_Console_v010.py`)
- **功能**:VIA_ChipWar_Console_v010.py
- **函式**(5):`run_engine(name, meta)` · `phase_test()` · `phase_consolidate(results)` · `phase_user_test()` · `main()`
- **自測**:主程式可跑

### CHW_ENG002_FinMindIngest
- **族**:`functional modules/ChipWar/engines/VIA_FinMind_Ingest`(版本 1;現役 `VIA_FinMind_Ingest_v010.py`)
- **功能**:VIA_FinMind_Ingest_v010.py
- **函式**(12):`init_db(con)` · `t_plus_1(d)` · `raw_hash(obj)` · `fetch_live(ds, stock_id, start, end)` · `fetch_mock(ds, stock_id, start, end)` · `fetch(ds, stock_id, start, end)` · `validate(name, df)` · `normalize(name, raw)` · `ingest(con, name, start, end)` · `derive_gov_net(con)`
- **自測**:主程式可跑

### CHW_ENG004_GovFundEngine
- **族**:`functional modules/ChipWar/engines/VIA_GovFundEngine`(版本 1;現役 `VIA_GovFundEngine_v040.py`)
- **功能**:VIA_GovFundEngine_v040.py — 自主進化版
- **函式**(12):`gen_world(world, n, seed)` · `z(s, w, mp)` · `build(df, dd_q)` · `score(out, use)` · `detect(out, zc, use)` · `fuzzy(t, k)` · `recall_fpr(sig, truth)` · `loeo(df, use)` · `ablate(df, use, zc)` · `auto_select()`
- **自測**:主程式可跑

### CHW_ENG005_RotationEngine
- **族**:`functional modules/ChipWar/engines/CHW_ENG005_RotationEngine`(版本 1;現役 `CHW_ENG005_RotationEngine_v010.py`)
- **功能**:VIA_RotationEngine_v010.py
- **函式**(11):`z(s, w, lag)` · `roc(s, lag)` · `gen_world(seed)` · `build_panel(dates, mkt, flows, prices)` · `quadrant(fm, pm)` · `alerts_for(panel)` · `daily_ic(sig, fwd)` · `ic_t(ics)` · `backtest(seed)` · `run_tests()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### CHW_ENG007_SectorWhaleEngine
- **族**:`functional modules/ChipWar/engines/VIA_SectorWhaleEngine`(版本 1;現役 `VIA_SectorWhaleEngine_v020.py`)
- **功能**:VIA_SectorWhaleEngine_v020.py — 準確率改良 + 完整回測(準確率/波動性)
- **函式**(9):`gen_world(seed, n)` · `zscore(s, kind, w, mp, lag)` · `sector_flows(df)` · `anchor_asof(wkdf, sec, dates)` · `detect(flow_z, anchor, cfg)` · `fuzzy(t, k)` · `metrics(sig, truth_dir)` · `backtest(cfg)` · `main()`
- **自測**:主程式可跑

### CHW_ENG009_SectorRotationCapitalFlowEngine
- **族**:`functional modules/ChipWar/engines/sector_rotation_capital_flow_engine`(版本 1;現役 `sector_rotation_capital_flow_engine.py`)
- **功能**:無說明(候補)
- **類**:SectorRotationEngine
- **函式**(1):`generate_noisy_market_data(days)`
- **自測**:主程式可跑


## FLOW · 資金流(24 支)

### FLOW_ENG001_FlowAutotest
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG001_FlowAutotest`(版本 1;現役 `FLOW_ENG001_FlowAutotest.py`)
- **功能**:VDF-FLOW-AUTOTEST flow_autotest.py — 硬化+引擎建構驗證(v0100R)。
- **函式**(1):`run()`
- **自測**:主程式可跑

### FLOW_ENG002_FlowBridge
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_bridge`(版本 1;現役 `flow_bridge.py`)
- **功能**:VDF-FLOW-BRIDGE flow_bridge.py — 真實資料入口(v0101R)。
- **函式**(5):`load_daily()` · `load_perf_prices()` · `load_flow_precise()` · `load_reference_flows()` · `source_status()`
- **自測**:匯入型

### FLOW_ENG003_FlowCalibrate
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_calibrate`(版本 1;現役 `flow_calibrate.py`)
- **功能**:CALIBRATE-13 flow_calibrate.py — optimize→test→debug→backtest→calibrate 迴圈(v0100R)。
- **函式**(1):`calibrate(panel, params, write)`
- **自測**:匯入型

### FLOW_ENG004_FlowCore
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_core`(版本 1;現役 `flow_core.py`)
- **功能**:VDF-FLOW-CORE-11 flow_core.py — FIS 強度 + 雙估計器信任 + 聚合(v0100R 重建版)。
- **函式**(9):`load_json(p, default)` · `load_params()` · `load_universe()` · `compute_fis(panel, params, universe)` · `role_gate(rows, universe)` · `bucket_fis(rows, key_fn, params, universe)` · `gram(rows, params, universe)` · `roro(rows, params, universe)` · `snapshot(rows, params, universe)`
- **自測**:匯入型

### FLOW_ENG005_FlowFactors
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_factors`(版本 1;現役 `flow_factors.py`)
- **功能**:VDF-FLOW-FACTORS flow_factors.py — 因子庫(v0100R)。
- **函式**(1):`build_factors(rows, rets_fwd, min_t, include_noise_probe, seed)`
- **自測**:匯入型

### FLOW_ENG006_FlowGrid
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_grid`(版本 1;現役 `flow_grid.py`)
- **功能**:VDF-FLOW-GRID-22 flow_grid.py — Region×Sector 網格 + Fidelity 評分卡(v0100R)。
- **函式**(1):`build_grid(rows, write)`
- **自測**:匯入型

### FLOW_ENG007_FlowHub
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_hub`(版本 1;現役 `flow_hub.py`)
- **功能**:VDF-FLOW-HUB flow_hub.py — 單一視窗整合 Hub + 理論總覽(v0101R;操作員「介面整合」令)。
- **函式**(5):`svg_main_flow()` · `svg_quadrant()` · `svg_solid()` · `svg_engine_layers()` · `build_hub(write)`
- **自測**:匯入型

### FLOW_ENG008_FlowMacro
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_macro`(版本 1;現役 `flow_macro.py`)
- **功能**:VDF-FLOW-MACRO flow_macro.py — 宏觀對照層 v2(自適應權重;操作員 2026/08/12 令)。
- **函式**(1):`load_macro_cfg()`
- **自測**:匯入型

### FLOW_ENG009_FlowManager
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG009_FlowManager`(版本 1;現役 `FLOW_ENG009_FlowManager.py`)
- **功能**:MANAGER-15 flow_manager.py — 系統管理/編排 + synth + CLI(v0100R)。
- **函式**(4):`cmd_synth(rho_override)` · `cmd_run(live)` · `cmd_status()` · `main()`
- **自測**:主程式可跑

### FLOW_ENG010_FlowMonitor
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_monitor`(版本 1;現役 `flow_monitor.py`)
- **功能**:VDF-FLOW-MONITOR flow_monitor.py — 族群整合監控 + 採用項目專頁(v0100R)。
- **函式**(1):`build_monitor(rows, write)`
- **自測**:匯入型

### FLOW_ENG011_FlowPerf
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_perf`(版本 1;現役 `flow_perf.py`)
- **功能**:VDF-FLOW-PERF flow_perf.py — 正規化走勢圖 + 主題分類(v0100R)。
- **函式**(1):`build_perf(write)`
- **自測**:匯入型

### FLOW_ENG012_FlowPillarA
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_pillar_a`(版本 1;現役 `flow_pillar_a.py`)
- **功能**:PILLARA-19 flow_pillar_a.py — Pillar A 測量校準(v0100R)。
- **函式**(1):`validate_a(fis_rows, write)`
- **自測**:匯入型

### FLOW_ENG013_FlowRoles
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_roles`(版本 1;現役 `flow_roles.py`)
- **功能**:VDF-FLOW-ROLES flow_roles.py — monitor_role 閘門 + 分類存取(v0100R)。
- **函式**(5):`spot_only(rows, universe)` · `by_tier(universe)` · `by_region(universe)` · `by_class(universe)` · `fidelity_classes(universe)`
- **自測**:匯入型

### FLOW_ENG014_FlowSelftest
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_selftest`(版本 1;現役 `flow_selftest.py`)
- **功能**:SELFTEST-20 flow_selftest.py — 14 項邊界測試(v0100R;README v0103 涵蓋清單)。
- **函式**(1):`run()`
- **自測**:主程式可跑

### FLOW_ENG015_FlowSim
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_sim`(版本 1;現役 `flow_sim.py`)
- **功能**:VDF-FLOW-SIM flow_sim.py — 全球資金流動情境模擬引擎(v0100R)。
- **函式**(4):`load_sim()` · `ground_loadings(rows, universe)` · `build_frames(sim, loadings, src)` · `build_map_sim(rows, write)`
- **自測**:匯入型

### FLOW_ENG016_FlowUi
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_ui`(版本 1;現役 `flow_ui.py`)
- **功能**:UI-14 flow_ui.py — 由 JSON 產 Visual Lock index.html(v0100R)。
- **函式**(8):`esc(s)` · `css_base()` · `nav_strip(current)` · `macro_card(mo)` · `vr_card(mo)` · `why_card(mo)` · `gaps_card(mo)` · `build_index(rows, calib, status, grid, factors)`
- **自測**:匯入型

### FLOW_ENG017_FlowValidate
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_validate`(版本 1;現役 `flow_validate.py`)
- **功能**:VALIDATE-12 flow_validate.py — IC/decay/quantile/long-short/null + gate 評估(v0100R)。
- **函式**(8):`rank_ic(sig, fwd)` · `daily_ic(rows, rets)` · `hac_t(ics, lags)` · `quantile_check(rows, rets, q)` · `long_short(rows, rets, cost_bps, q)` · `null_test(rows, rets, k, seed)` · `lead_ratio(rows, rets_fwd, rets_same)` · `evaluate(rows, rets_fwd, rets_same, params)`
- **自測**:匯入型

### FLOW_ENG018_FlowWorldmap
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_worldmap`(版本 1;現役 `flow_worldmap.py`)
- **功能**:VDF-FLOW-WORLDMAP-23 flow_worldmap.py — 世界地圖/風險階梯 資金流動畫(v0100R)。
- **函式**(2):`build_worldmap(rows, write)` · `build_tierflow(rows, write)`
- **自測**:匯入型

### FLOW_ENG019_FlowAttractiveness
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG019_FlowAttractiveness`(版本 1;現役 `FLOW_ENG019_FlowAttractiveness.py`)
- **功能**:flow_attractiveness — 資金流三因子吸引力引擎(TOOL-055;內容功能導入 2026-08-18)
- **函式**(2):`compute(inputs, ic_weights)` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest

### FLOW_ENG020_FlowLeadlag
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG020_FlowLeadlag`(版本 1;現役 `FLOW_ENG020_FlowLeadlag.py`)
- **功能**:flow_leadlag — 因果力場 lead-lag 邊 harness(TOOL-055;內容功能導入 2026-08-18)
- **函式**(4):`edge_leadlag(a, b, k)` · `regime_split(a, b, regimes, k)` · `field_edges(series, edges, k)` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest

### FLOW_ENG021_FlowGlobalEtfFlowscope
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG021_FlowGlobalEtfFlowscope`(版本 1;現役 `FLOW_ENG021_FlowGlobalEtfFlowscope.py`)
- **功能**:flow_global_etf_flowscope — 全球 ETF 跨資產資金流觀察引擎(TOOL-061)
- **函式**(5):`cmd_universe()` · `measure(rows)` · `cmd_measure(path)` · `selftest()` · `main()`
- **CLI**:`--help` `--measure` `--selftest` `--universe`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### FLOW_ENG022_FlowGroupTaxonomy
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG022_FlowGroupTaxonomy`(版本 1;現役 `FLOW_ENG022_FlowGroupTaxonomy.py`)
- **功能**:flow_group_taxonomy — 台股族群三分類+族群指數繪製方法論引擎(TOOL-062)
- **函式**(8):`c1_groups()` · `c3_quadrant(ret_z, vol_z)` · `cmd_taxonomy()` · `build_index(rows, weighting)` · `to_chartspec(idx, weighting)` · `cmd_index(path, emit_spec)` · `selftest()` · `main()`
- **CLI**:`--chartspec` `--help` `--index` `--selftest` `--taxonomy`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### FLOW_ENG023_FlowTwActiveEtf
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG023_FlowTwActiveEtf`(版本 1;現役 `FLOW_ENG023_FlowTwActiveEtf.py`)
- **功能**:flow_tw_active_etf — 台灣主動式 ETF 清單+資金流引擎(TOOL-060)
- **函式**(9):`load_registry()` · `save_registry(reg)` · `cmd_registry()` · `cmd_refresh()` · `cmd_ingest(path)` · `compute_flows(rows)` · `cmd_flows()` · `selftest()` · `main()`
- **CLI**:`--flows` `--help` `--ingest` `--refresh` `--registry` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### FLOW_ENG024_FLOWENG024FlowRegistryOps
- **族**:`supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/FLOW_ENG024_FlowRegistryOps`(版本 1;現役 `FLOW_ENG024_FlowRegistryOps.py`)
- **功能**:FLOW_ENG024_FlowRegistryOps — 註冊台維運引擎(TOOL-075;批51 ①②③)
- **函式**(5):`cmd_refresh_equity()` · `cmd_holdings(csv_path, etf)` · `cmd_coverage(tw_reg, universe)` · `selftest()` · `main()`
- **CLI**:`--coverage` `--etf` `--holdings` `--refresh` `--refresh-equity` `--refresh-etf` `--registry` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module


## GRP · 族群指數(41 支)

### GRP_ENG001_ActiveStockETF
- **族**:`functional modules/GroupIndex/engine/VIA_ActiveStockETF`(版本 1;現役 `VIA_ActiveStockETF.py`)
- **功能**:VIA_ActiveStockETF.py
- **類**:Log, FetchError, Http, Val, Sources, Registry
- **函式**(11):`decode_text(raw)` · `roc_to_iso(s)` · `to_float(v)` · `to_int(v)` · `norm_text(s)` · `today_tw()` · `month_starts(months, end)` · `parse_isin_table(html_text)` · `parse_nav_rows(rows)` · `parse_stock_day_rows(rows)`
- **CLI**:`---` `--base-isin` `--base-openapi` `--base-tpex` `--base-twse` `--cache` `--months` `--no-cache` `--offline` `--open` `--out` `--overrides`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG003_ChipWarConsole
- **族**:`functional modules/GroupIndex/engine/VIA_ChipWar_Console`(版本 1;現役 `VIA_ChipWar_Console_v010.py`)
- **功能**:VIA_ChipWar_Console_v010.py
- **函式**(5):`run_engine(name, meta)` · `phase_test()` · `phase_consolidate(results)` · `phase_user_test()` · `main()`
- **自測**:主程式可跑

### GRP_ENG006_FinMindIngest
- **族**:`functional modules/GroupIndex/engine/VIA_FinMind_Ingest`(版本 1;現役 `VIA_FinMind_Ingest_v010.py`)
- **功能**:VIA_FinMind_Ingest_v010.py
- **函式**(12):`init_db(con)` · `t_plus_1(d)` · `raw_hash(obj)` · `fetch_live(ds, stock_id, start, end)` · `fetch_mock(ds, stock_id, start, end)` · `fetch(ds, stock_id, start, end)` · `validate(name, df)` · `normalize(name, raw)` · `ingest(con, name, start, end)` · `derive_gov_net(con)`
- **自測**:主程式可跑

### GRP_ENG007_GlobalETFFlow
- **族**:`functional modules/GroupIndex/engine/VIA_GlobalETFFlow`(版本 1;現役 `VIA_GlobalETFFlow.py`)
- **功能**:VIA_GlobalETFFlow.py
- **類**:Log, FetchError, Http, Val, Sources, _RobustWindow, UniverseRegistry, SharesRegistry
- **函式**(10):`decode_text(raw)` · `to_float(v)` · `median(xs)` · `mad(xs, med)` · `robust_z(x, sample)` · `clamp(x, lo, hi)` · `today_utc()` · `parse_stooq_csv(text)` · `parse_yahoo_chart(doc)` · `parse_quote_summary(doc)`
- **CLI**:`--all` `--base-stooq` `--base-yahoo` `--cache` `--group` `--keep` `--mocktest` `--no-cache` `--offline` `--open` `--out` `--probe`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG008_GovFundEngine
- **族**:`functional modules/GroupIndex/engine/VIA_GovFundEngine`(版本 1;現役 `VIA_GovFundEngine_v040.py`)
- **功能**:VIA_GovFundEngine_v040.py — 自主進化版
- **函式**(12):`gen_world(world, n, seed)` · `z(s, w, mp)` · `build(df, dd_q)` · `score(out, use)` · `detect(out, zc, use)` · `fuzzy(t, k)` · `recall_fpr(sig, truth)` · `loeo(df, use)` · `ablate(df, use, zc)` · `auto_select()`
- **自測**:主程式可跑

### GRP_ENG009_GroupIndexEnvPreflight
- **族**:`functional modules/GroupIndex/engine/VIA_GroupIndex_EnvPreflight`(版本 1;現役 `VIA_GroupIndex_EnvPreflight_v0100.py`)
- **功能**:VERITAS INTELLIGENCE ANALYTICS
- **函式**(7):`def_detect_env()` · `def_check_tools()` · `def_discover_via_envs()` · `def_audit_base_cleanliness()` · `def_whitelist_gap()` · `def_run_preflight(enforce)` · `main(argv)`
- **CLI**:`--enforce`
- **自測**:主程式可跑

### GRP_ENG015_SectorWhaleEngine
- **族**:`functional modules/GroupIndex/engine/VIA_SectorWhaleEngine`(版本 1;現役 `VIA_SectorWhaleEngine_v020.py`)
- **功能**:VIA_SectorWhaleEngine_v020.py — 準確率改良 + 完整回測(準確率/波動性)
- **函式**(9):`gen_world(seed, n)` · `zscore(s, kind, w, mp, lag)` · `sector_flows(df)` · `anchor_asof(wkdf, sec, dates)` · `detect(flow_z, anchor, cfg)` · `fuzzy(t, k)` · `metrics(sig, truth_dir)` · `backtest(cfg)` · `main()`
- **自測**:主程式可跑

### GRP_ENG017_Init
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/__init__`(版本 1;現役 `__init__.py`)
- **功能**:台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).
- **自測**:匯入型

### GRP_ENG018_Analyze
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/analyze`(版本 1;現役 `analyze.py`)
- **功能**:analyze.py -- 三層動能分析引擎.
- **函式**(5):`compute_company_metrics(g, cfg)` · `classify_pattern(m, cfg)` · `momentum_score(m, cfg)` · `tier(m, cfg)` · `analyze(data, cfg)`
- **自測**:匯入型

### GRP_ENG019_Classify
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/classify`(版本 1;現役 `classify.py`)
- **功能**:classify.py -- 產業分類 + 原物料/週期股全市場分流.
- **函式**(1):`tag_cyclical(df, cyclical_industries)`
- **自測**:匯入型

### GRP_ENG020_Cli
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/cli`(版本 1;現役 `cli.py`)
- **功能**:cli.py -- 命令列進入點.
- **函式**(9):`load_cfg(path)` · `cmd_fetch(cfg)` · `cmd_analyze(cfg, data)` · `cmd_report(cfg, result, data)` · `cmd_run(cfg)` · `cmd_demo(cfg)` · `cmd_groups(cfg)` · `cmd_selftest(cfg)` · `main(argv)`
- **CLI**:`--config`
- **自測**:主程式可跑

### GRP_ENG021_Fetch
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/fetch`(版本 1;現役 `fetch.py`)
- **功能**:fetch.py -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收.
- **函式**(3):`month_iter(months_back, ref)` · `fetch_page(session, hosts, market, year, month)` · `fetch_all(cfg, ref)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG022_Groups
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/groups`(版本 1;現役 `groups.py`)
- **功能**:groups.py -- 熱門族群分類層 (VIA 族群分類 v1.1 疊加).
- **函式**(6):`load_groups(path)` · `attach_groups(analysis, groups)` · `group_momentum(analysis, groups, cfg)` · `cyclical_sector_groups(analysis)` · `order_sector_table(gt)` · `group_members_detail(analysis, groups, grp)`
- **自測**:匯入型

### GRP_ENG023_Report
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/report`(版本 1;現役 `report.py`)
- **功能**:report.py -- 單頁 HTML 儀表板 (視覺鎖定: VIA 族群分類 v1.1 風格).
- **自測**:匯入型

### GRP_ENG024_Store
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/store`(版本 1;現役 `store.py`)
- **功能**:store.py -- 月營收累計增量資料庫 (parquet SSOT + duckdb 查詢層).
- **函式**(2):`upsert(df, cfg)` · `load(cfg, months_back)`
- **自測**:匯入型

### GRP_ENG025_Synth
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/synth`(版本 1;現役 `synth.py`)
- **功能**:synth.py -- 產生合成月營收資料, 供離線測試與 demo.
- **函式**(1):`make_synthetic(cfg, ref)`
- **自測**:匯入型

### GRP_ENG026_Tests
- **族**:`functional modules/GroupIndex/engine/taiwan_revenue_engine/twrevenue/tests`(版本 1;現役 `tests.py`)
- **功能**:tests.py -- 內建自我測試 (python -m twrevenue.cli selftest).
- **函式**(9):`t_regex()` · `t_parser()` · `t_sectors()` · `t_groups_ssot()` · `t_store()` · `t_duckdb()` · `t_url()` · `t_formula()` · `run_all()`
- **自測**:匯入型

### GRP_ENG040_GroupingRotationRunner
- **族**:`functional modules/GroupIndex/engine/GRP_ENG040_GroupingRotationRunner`(版本 3;現役 `GRP_ENG040_GroupingRotationRunner_v0102.py`)
- **功能**:GRP_ENG040_GroupingRotationRunner v0101 — 雙 profile 輪動統一轉接(批153;via-rotation)
- **函式**(6):`export_prices_tw(dst, tickers)` · `export_prices_global(dst, tickers)` · `build_factors_tw(dst)` · `build_factors_global(dst)` · `sidecar_global(out_dir, memb_csv)` · `run(profile, start, ev, end)`
- **CLI**:`--demo` `--end` `--end-date` `--eval` `--factors` `--membership` `--no-write` `--normalized-date` `--output-root` `--prices` `--selftest` `--start`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG041_RotationMethodLab
- **族**:`functional modules/GroupIndex/engine/GRP_ENG041_RotationMethodLab`(版本 2;現役 `GRP_ENG041_RotationMethodLab_v0101.py`)
- **功能**:GRP_ENG041_RotationMethodLab v0101 — 輪動方法論實測室(批155;via-methodlab)
- **函式**(9):`load_prices()` · `load_market()` · `s1_structure()` · `s2_flow_share(px)` · `s3_group_evidence(px, mkt)` · `s4_ta_backtest(px, mkt)` · `s6_global_risk()` · `s7_fx_triangle()` · `s8_flow_decomp(mkt)`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG042_TWGroupingIndexRotationUnifiedEngine
- **族**:`functional modules/GroupIndex/VIA_TW_Grouping_LatestCommand_v0202/VIA_TW_GroupingIndexRotationUnifiedEngine`(版本 1;現役 `VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py`)
- **功能**:無說明(候補)
- **類**:EngineConfig, EngineResult
- **函式**(12):`def_configure_logging(verbose)` · `def_now_utc()` · `def_json_safe(value)` · `def_sha256(path)` · `def_stable_seed()` · `def_column_key(value)` · `def_find_column(columns, candidates)` · `def_ticker_base(value)` · `def_normalize_ticker(value, market)` · `def_normalize_role(value)`
- **CLI**:`--demo` `--demo-observations` `--end-date` `--factors` `--membership` `--no-write` `--normalized-date` `--output-root` `--prices` `--start-date` `--strict` `--verbose`
- **自測**:主程式可跑

### GRP_ENG043_TestVIATWGroupingIndexRotationUnifiedEngine
- **族**:`functional modules/GroupIndex/VIA_TW_Grouping_LatestCommand_v0202/test_VIA_TW_GroupingIndexRotationUnifiedEngine`(版本 1;現役 `test_VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py`)
- **功能**:無說明(候補)
- **函式**(12):`engine()` · `membership(engine)` · `small_method_run(engine, membership)` · `test_membership_scope_and_primary_key(membership)` · `test_ticker_market_suffix(engine)` · `test_raw_close_is_fail_closed(engine, membership)` · `test_volume_and_flow_are_not_forward_filled(engine, membership)` · `test_point_in_time_roles_take_effect_next_session(small_method_run)` · `test_membership_validity_is_separate_from_role_separability(small_method_run)` · `test_temporal_devil_validation_fields_exist(small_method_run)`
- **自測**:匯入型

### GRP_ENG044_TWGroupPriceVolumeVolatilityEngine
- **族**:`functional modules/GroupIndex/engine/VIA_TW_Group_PriceVolume_Volatility_Engine`(版本 1;現役 `VIA_TW_Group_PriceVolume_Volatility_Engine_v0100.py`)
- **功能**:無說明(候補)
- **類**:EngineConfig, EngineResult
- **函式**(11):`def_configure_logging(verbose)` · `def_json_safe(value)` · `def_sha256(path)` · `def_column_key(value)` · `def_find_column(columns, candidates)` · `def_ticker_base(value)` · `def_normalize_ticker(value, market)` · `def_validate_config(config)` · `def_load_group_ssot(path)` · `def_ssot_summary(ssot)`
- **CLI**:`--end-date` `--group-ssot` `--no-write` `--normalized-date` `--output-root` `--price-path` `--self-test` `--start-date` `--strict` `--ticker-list` `--use-yfinance-fallback` `--verbose`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG046_Init
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA Taiwan group-flow simulation system.
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG047_BuildControlledFixture
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/build_controlled_fixture`(版本 1;現役 `build_controlled_fixture.py`)
- **功能**:無說明(候補)
- **函式**(5):`def_parse_args()` · `def_build_membership(reference_dir)` · `def_build_market_tables(membership)` · `def_write_fixture(output_dir)` · `def_main()`
- **CLI**:`--output-dir`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG048_BuildReleaseManifest
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/build_release_manifest`(版本 1;現役 `build_release_manifest.py`)
- **功能**:無說明(候補)
- **函式**(2):`def_sha256(path)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG049_DashboardBuilder
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/dashboard_builder`(版本 1;現役 `dashboard_builder.py`)
- **功能**:無說明(候補)
- **函式**(2):`def_encode_dashboard_payload(payload)` · `def_build_dashboard_html(payload)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG050_AttentionShareEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_attention_share_engine`(版本 1;現役 `via_attention_share_engine.py`)
- **功能**:無說明(候補)
- **函式**(2):`def_compute_attention_share(stock_turnover, market_turnover, tsmc_ticker)` · `def_compute_group_attention_score(attention_rows, membership, smoothing_days)`
- **自測**:匯入型

### GRP_ENG051_ClassificationIntake
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_classification_intake`(版本 1;現役 `via_classification_intake.py`)
- **功能**:無說明(候補)
- **函式**(5):`def_clean_html_text(value)` · `def_literal_dict_from_python(path)` · `def_build_market_lookup(reference_dir)` · `def_extract_candidate_membership(source_html, reference_dir)` · `def_write_candidate_membership(project_root, output_path)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG052_DynamicClassificationEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_dynamic_classification_engine`(版本 1;現役 `via_dynamic_classification_engine.py`)
- **功能**:無說明(候補)
- **函式**(6):`def_derive_dynamic_parameters(price)` · `def_prepare_main_force(main_force)` · `def_safe_corr(left, right, minimum)` · `def_last_robust_z(values, minimum)` · `def_group_validation(membership, price, parameters)` · `def_compute_dynamic_classification(membership, price, institutional, main_force, roles)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG053_FlowrotCandidateIntake
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_flowrot_candidate_intake`(版本 1;現役 `via_flowrot_candidate_intake.py`)
- **功能**:無說明(候補)
- **函式**(3):`def_extract_flowrot_candidate(source_path)` · `def_validate_flowrot_candidate(groups, members, quality)` · `def_write_flowrot_candidate(source_path, input_dir, evidence_dir)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG054_GroupFundFlowMonitorEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_group_fund_flow_monitor_engine`(版本 1;現役 `via_group_fund_flow_monitor_engine.py`)
- **功能**:無說明(候補)
- **類**:SystemConfig
- **函式**(12):`def_utc_now()` · `def_load_config(config_path)` · `def_resolve_path(project_root, configured_path)` · `def_read_table(path)` · `def_require_columns(frame, required, table_name)` · `def_to_bool(series, default)` · `def_normalize_ticker(value)` · `def_check(ledger, check_id, check, status, severity)` · `def_prepare_membership(membership, config, ledger)` · `def_prepare_price(price, config, ledger)`
- **CLI**:`--config`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG055_RotationBacktestEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_rotation_backtest_engine`(版本 1;現役 `via_rotation_backtest_engine.py`)
- **功能**:無說明(候補)
- **函式**(4):`def_max_drawdown(wealth)` · `def_rank_ic(group)` · `def_metrics(daily, observations_per_year, annual_risk_free_rate)` · `def_run_rotation_backtest(group_index, group_flow, parameters, ledger, transaction_cost_bps)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG056_RotationSnapshotEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_rotation_snapshot_engine`(版本 1;現役 `via_rotation_snapshot_engine.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_normalize_candidate_group_names(candidate_groups)` · `def_build_rotation_snapshot(candidate_groups)` · `def_validate_rotation_snapshot(snapshot, quality)` · `def_validate_rotation_source_contract(source_path, snapshot)` · `def_validate_transition_history(history)` · `def_append_rotation_snapshot(snapshot, base_path)` · `def_extract_vdf_contract_summary(source_path)` · `def_write_rotation_quality(quality, path)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG057_StatisticalValidationEngine
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_statistical_validation_engine`(版本 1;現役 `via_statistical_validation_engine.py`)
- **功能**:無說明(候補)
- **函式**(4):`def_pca_absorption_rate(returns, iterations)` · `def_ccf_lag_spectrum(leader, follower, max_lag)` · `def_permutation_max_ccf_test(leader, follower, max_lag, permutations, seed)` · `def_validate_leader_follower(group_returns, leader_column, follower_column, absorption_min, p_value_max)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG058_VersionChain
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/engine/via_version_chain`(版本 1;現役 `via_version_chain.py`)
- **功能**:無說明(候補)
- **函式**(3):`def_weakest_evidence()` · `def_build_candidate_version_chain(candidate_validation, asof_date, source_ref, parameters_digest)` · `def_validate_candidate_groups(groups, attention_min, leadership_min)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG059_8bd5bc089d824fb198d01763f5210a27
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/references/intake/8bd5bc08-9d82-4fb1-98d0-1763f5210a27`(版本 1;現役 `8bd5bc08-9d82-4fb1-98d0-1763f5210a27.py`)
- **功能**:無說明(候補)
- **類**:UltraAccuracyEngineV2
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG060_9df6891bD3094af6Bc58A21b2907308e
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/references/intake/9df6891b-d309-4af6-bc58-a21b2907308e`(版本 1;現役 `9df6891b-d309-4af6-bc58-a21b2907308e.py`)
- **功能**:無說明(候補)
- **類**:SectorRotationEngine
- **函式**(1):`generate_noisy_market_data(days)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG061_RunSystem
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/run_system`(版本 1;現役 `run_system.py`)
- **功能**:無說明(候補)
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG062_RunTests
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:run_tests — 族群流模擬系統 v0400 測試套統一入口(收容整合層,原件零觸碰)
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG063_Init
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/tests/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### GRP_ENG064_TestViaGroupFlowSystem
- **族**:`functional modules/GroupIndex/flow_simulation_v0400/tests/test_via_group_flow_system`(版本 1;現役 `test_via_group_flow_system.py`)
- **功能**:無說明(候補)
- **類**:TestVIAGroupFlowSystem
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module


## PLG · 插件(17 支)

### PLG_ENG001_SuperExtract
- **族**:`functional modules/SuperDocExtractor/PLG_ENG001_SuperExtract`(版本 1;現役 `PLG_ENG001_SuperExtract.py`)
- **功能**:Entry point:  python super_extract.py <command> ...
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module, superextract

### PLG_ENG002_Init
- **族**:`functional modules/SuperDocExtractor/superextract/__init__`(版本 1;現役 `__init__.py`)
- **功能**:superextract — Word/Excel/CSV text & table extractor with encoding
- **自測**:匯入型

### PLG_ENG003_Main
- **族**:`functional modules/SuperDocExtractor/superextract/__main__`(版本 1;現役 `__main__.py`)
- **功能**:Allow `python -m superextract ...`.
- **自測**:主程式可跑

### PLG_ENG004_Availability
- **族**:`functional modules/SuperDocExtractor/superextract/availability`(版本 1;現役 `availability.py`)
- **功能**:Optional-dependency registry.
- **函式**(4):`has(name)` · `load(name)` · `doctor()` · `doctor_text()`
- **自測**:匯入型

### PLG_ENG005_Cli
- **族**:`functional modules/SuperDocExtractor/superextract/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface.
- **函式**(8):`cmd_doctor(_args)` · `cmd_extract(args)` · `cmd_validate(args)` · `cmd_compare(args)` · `cmd_crosscheck(args)` · `cmd_selftest(args)` · `build_parser()` · `main(argv)`
- **CLI**:`--delimiter` `--drop-layout-tables` `--encoding` `--engine` `--html` `--json` `--keep` `--key` `--no-datacompy` `--no-repair` `--outdir` `--output-encoding`
- **自測**:主程式可跑

### PLG_ENG006_Compare
- **族**:`functional modules/SuperDocExtractor/superextract/compare`(版本 1;現役 `compare.py`)
- **功能**:Comparison (對照): text diff, table pairing, cell-level diff.
- **類**:TextDiff, CellChange, TableDiff
- **函式**(7):`compare_texts(old, new, label_old, label_new, normalize)` · `html_side_by_side(old, new, label_old, label_new)` · `pair_tables(old_tables, new_tables, threshold)` · `cells_equal(a, b)` · `detect_key_column(g1, g2)` · `compare_grids(g_old, g_new, key, auto_key, with_datacompy)` · `crosscheck_docx(path)`
- **CLI**:`---`
- **自測**:匯入型

### PLG_ENG007_CsvExtract
- **族**:`functional modules/SuperDocExtractor/superextract/csv_extract`(版本 1;現役 `csv_extract.py`)
- **功能**:CSV extraction with encoding detection, dialect sniffing and ragged-row
- **類**:CsvResult
- **函式**(2):`sniff_dialect(sample)` · `extract_csv(path, encoding, delimiter, row_policy)`
- **自測**:匯入型

### PLG_ENG008_Encoding
- **族**:`functional modules/SuperDocExtractor/superextract/encoding`(版本 1;現役 `encoding.py`)
- **功能**:Encoding detection and byte decoding (編碼問題核心).
- **類**:DetectionResult
- **函式**(4):`sniff_bom(data)` · `detect_encoding(data)` · `decode_bytes(data, encoding)` · `read_text_auto(path, encoding)`
- **自測**:匯入型

### PLG_ENG009_ExcelExtract
- **族**:`functional modules/SuperDocExtractor/superextract/excel_extract`(版本 1;現役 `excel_extract.py`)
- **功能**:Excel (.xlsx / .xls) extraction into Grids.
- **類**:ExcelWorkbook
- **函式**(5):`col_to_index(ref)` · `split_ref(ref)` · `serial_to_datetime(serial, date1904)` · `extract_xlsx_rawxml(path, password, values)` · `extract_xlsx_openpyxl(path, password, values)`
- **自測**:匯入型

### PLG_ENG010_Pipeline
- **族**:`functional modules/SuperDocExtractor/superextract/pipeline`(版本 1;現役 `pipeline.py`)
- **功能**:High-level pipeline: extract -> repair -> validate -> report, for any of
- **類**:ExtractionResult
- **函式**(3):`detect_format(path)` · `extract_any(path, engine, encoding, password, values)` · `compare_files(old_path, new_path, key, with_datacompy, max_diff_lines)`
- **自測**:匯入型

### PLG_ENG011_Report
- **族**:`functional modules/SuperDocExtractor/superextract/report`(版本 1;現役 `report.py`)
- **功能**:Report rendering: one markdown/JSON view over extraction + repair +
- **函式**(5):`write_json(payload, path)` · `render_extraction_md(report)` · `render_comparison_md(report)` · `render_crosscheck_md(report)` · `dump_debug_json(payload)`
- **自測**:匯入型

### PLG_ENG012_Samples
- **族**:`functional modules/SuperDocExtractor/superextract/samples`(版本 1;現役 `samples.py`)
- **功能**:Sample-file factory for the selftest.
- **函式**(4):`write_docx(path, body_xml, with_header)` · `write_xlsx(path)` · `write_csvs(outdir)` · `build_all(outdir)`
- **自測**:匯入型

### PLG_ENG013_Selftest
- **族**:`functional modules/SuperDocExtractor/superextract/selftest`(版本 1;現役 `selftest.py`)
- **功能**:End-to-end selftest: generate pathological samples, run the full
- **函式**(12):`check_docx_text_and_track_changes(paths)` · `check_docx_invisible_char_repair(paths)` · `check_docx_merges(paths)` · `check_docx_nested_and_layout(paths)` · `check_docx_crosscheck(paths)` · `check_xlsx_both_engines(paths)` · `check_xlsx_validation(paths)` · `check_csv_big5(paths)` · `check_csv_bom(paths)` · `check_csv_mojibake(paths)`
- **自測**:匯入型

### PLG_ENG014_Tableops
- **族**:`functional modules/SuperDocExtractor/superextract/tableops`(版本 1;現役 `tableops.py`)
- **功能**:Grid: the common table structure every extractor produces.
- **類**:Grid
- **函式**(2):`dedupe_headers(names)` · `coerce_number(value)`
- **CLI**:`---`
- **自測**:匯入型

### PLG_ENG015_Textclean
- **族**:`functional modules/SuperDocExtractor/superextract/textclean`(版本 1;現役 `textclean.py`)
- **功能**:Text repair (修復): mojibake, invisible characters, normalization.
- **類**:CleanResult
- **函式**(5):`mojibake_score(text)` · `fix_mojibake(text)` · `clean_text(text, fix_encoding, normalize, strip_zero_width, strip_control)` · `normalize_for_compare(value)` · `find_invisible_chars(text)`
- **自測**:匯入型

### PLG_ENG016_Validate
- **族**:`functional modules/SuperDocExtractor/superextract/validate`(版本 1;現役 `validate.py`)
- **功能**:Validation (驗證): structural and content checks on extracted data.
- **類**:Issue
- **函式**(3):`validate_text(text, location)` · `validate_grid(grid, header_row)` · `summarize_issues(issues)`
- **自測**:匯入型

### PLG_ENG017_WordExtract
- **族**:`functional modules/SuperDocExtractor/superextract/word_extract`(版本 1;現役 `word_extract.py`)
- **功能**:Word (.docx) text + table extraction.
- **類**:ExtractionError, WordDocument
- **函式**(6):`sniff_container(path_or_bytes)` · `open_office_zip(path, password)` · `extract_docx_rawxml(path, password, include_headers_footers)` · `extract_docx_python_docx(path)` · `extract_docx_docx2python(path)` · `extract_docx(path, engine, password, include_headers_footers)`
- **CLI**:`----media/.*?----`
- **自測**:匯入型


## VAP · 視覺分析(202 支)

### VAP_ENG002_AutoplotEngine
- **族**:`functional modules/VAP/engine/VAP_ENG002_AutoplotEngine`(版本 1;現役 `VAP_ENG002_AutoplotEngine_v001.py`)
- **功能**:VIA · VeritasAutoPlot (VAP) engine v001 · 雙軸互比繪圖引擎.
- **函式**(8):`log(message)` · `discover_db_files(base, extra)` · `write_demo_db(base)` · `load_tables(path)` · `parse_x(value)` · `parse_number(value)` · `numeric_columns(rows)` · `x_column(rows, preferred)`
- **CLI**:`--auto` `--base` `--db` `--demo` `--left` `--left-form` `--list` `--max-charts` `--out` `--right` `--right-form` `--table`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG003_AutoplotSeabornPlotly
- **族**:`functional modules/VAP/engine/VAP_ENG003_AutoplotSeabornPlotly`(版本 1;現役 `VAP_ENG003_AutoplotSeabornPlotly_v0100.py`)
- **功能**:VIA · VeritasAutoPlot seaborn+plotly 引擎 v0100 — VAP-CH-01…28 全譜雙後端實作.
- **類**:VAPError, VAPUnsupported, Spec, SeabornBackend, PlotlyBackend
- **函式**(10):`find_ssot_dir(override)` · `nice_step(raw, multiples)` · `ticks_for(lo, hi, spec, n_intervals, headroom)` · `decimals_of(step)` · `fmt_tick(value, step, thousands)` · `dual_ticks(l_lo, l_hi, r_lo, r_hi, spec)` · `thin_labels(labels, max_labels)` · `demo_data(chart_id)` · `hex_to_rgba(hex_color, alpha)` · `hex_to_mpl_rgba(hex_color, alpha)`
- **CLI**:`--backend` `--chart` `--data` `--file` `--group` `--limit` `--map` `--out` `--plotlyjs` `--scale` `--ssot` `--table`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG008_TestConsole
- **族**:`functional modules/VAP/engine/VAP_ENG008_TestConsole`(版本 1;現役 `VAP_ENG008_TestConsole_v0100.py`)
- **功能**:VAP_ENG008_TestConsole — VAP 全測×簡潔響應式主控台(批162;via-vapui)
- **函式**(7):`run_tests()` · `harvest_specs()` · `build_ui(results, specs)` · `run()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG009_DashboardUI
- **族**:`functional modules/VAP/engine/VAP_ENG009_DashboardUI`(版本 8;現役 `VAP_ENG009_DashboardUI_v0107.py`)
- **功能**:VAP_ENG009_DashboardUI — VIA 儀表板原始版(批167;操作員 Layout element 定案)
- **函式**(5):`load_dash_tokens()` · `harvest_data()` · `harvest_rotation(top_n, days)` · `harvest_global(days)` · `preflight(db, ssot, rot_root, import_fn, connect_fn)`
- **CLI**:`--approve-install` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG010_BaseHomeIoBuilder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder`(版本 1;現役 `vap_base_home_io_builder.py`)
- **功能**:無說明(候補)
- **類**:def_DataAsset, def_TemplateAsset
- **函式**(12):`def_now()` · `def_read_text(path_value)` · `def_slug(value)` · `def_write_json(path_value, payload)` · `def_kind(path_value)` · `def_extract_csv(path_value)` · `def_extract_json(path_value)` · `def_extract_html(path_value)` · `def_extract_parquet(path_value)` · `def_extract_text(path_value)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG011_CheckLibs
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_DUCKDB_PARQUET_20260506_221932/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG012_DuckdbParquetBuilder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_DUCKDB_PARQUET_20260506_221932/vap_duckdb_parquet_builder`(版本 1;現役 `vap_duckdb_parquet_builder.py`)
- **功能**:無說明(候補)
- **類**:Asset
- **函式**(12):`now()` · `safe_text(p)` · `slug(v)` · `write_json(p, payload)` · `kind(p)` · `norm_headers(headers)` · `extract_csv(p)` · `extract_json(p)` · `extract_html(p)` · `extract_parquet(p)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG013_CheckLibs
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PANORAMA_MATURITY_OPT_20260507_110152/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG014_PanoramaMaturityOptimizer
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PANORAMA_MATURITY_OPT_20260507_110152/vap_panorama_maturity_optimizer`(版本 1;現役 `vap_panorama_maturity_optimizer.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_read_json(path_value, default)` · `def_safe_table(con, table_name)` · `def_table_exists(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_latest_run(pattern)` · `def_scan_versions()` · `def_scan_duckdb()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG016_PanoramaMaturityOptimizer
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PANORAMA_MATURITY_OPT_20260507_230210/vap_panorama_maturity_optimizer`(版本 1;現役 `vap_panorama_maturity_optimizer.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_read_json(path_value, default)` · `def_safe_table(con, table_name)` · `def_table_exists(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_latest_run(pattern)` · `def_scan_versions()` · `def_scan_duckdb()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG017_CheckLibs
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PROJECT_COMPLETION_20260506_224841/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG018_ProjectCompletionProbe
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PROJECT_COMPLETION_20260506_224841/vap_project_completion_probe`(版本 1;現役 `vap_project_completion_probe.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_now()` · `def_read_json(path_value, default)` · `def_table_count(con, table_name)` · `def_table_exists(con, table_name)` · `def_write_query_pack()` · `def_write_launchers()` · `def_write_handover(manifest, tables)` · `main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG020_ProjectCompletionProbeV2
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_PROJECT_COMPLETION_V2_20260506_225531/vap_project_completion_probe_v2`(版本 1;現役 `vap_project_completion_probe_v2.py`)
- **功能**:無說明(候補)
- **函式**(9):`def_now()` · `def_read_json(path_value, default)` · `def_table_count(con, table_name)` · `def_table_exists(con, table_name)` · `def_active_warning_count(con)` · `def_write_query_pack()` · `def_write_launchers()` · `def_write_handover(manifest, tables)` · `main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG021_CheckLibs
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_V8_MASTER_20260507_233550/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG022_V8MasterOrchestrator
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_V8_MASTER_20260507_233550/vap_v8_master_orchestrator`(版本 1;現役 `vap_v8_master_orchestrator.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_write_json(p, payload)` · `def_safe_table(con, table)` · `def_table_exists(con, table)` · `def_table_count(con, table)` · `def_write_table(con, table, df)` · `def_live_fetch_status()` · `def_fetch_prices()` · `def_prepare_returns(price_df)` · `def_calc_rolling_corr(norm_df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG024_WarehouseV4Builder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_WAREHOUSE_V4_20260506_222535/vap_warehouse_v4_builder`(版本 1;現役 `vap_warehouse_v4_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_safe_text(path_value)` · `def_write_json(path_value, payload)` · `def_slug(value)` · `def_read_duckdb_table(table_name)` · `def_scan_files()` · `def_json_kind(path_value)` · `def_normalize_asset_registry(asset_df)` · `def_detect_components_for_html(path_value, asset_id)` · `def_build_component_registry(asset_df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG026_WarehouseV5Next3Builder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_230931/vap_warehouse_v5_next3_builder`(版本 1;現役 `vap_warehouse_v5_next3_builder.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_bool_series(df, col)` · `def_build_live_data_source_registry()` · `def_build_fetch_plan_registry(source_df)` · `def_try_fetch_yfinance(fetch_df)` · `def_build_dashboard_blueprints(asset_df, component_df, schema_df, token_df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG028_WarehouseV5Next3Builder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_231125/vap_warehouse_v5_next3_builder`(版本 1;現役 `vap_warehouse_v5_next3_builder.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_bool_series(df, col)` · `def_build_live_data_source_registry()` · `def_build_fetch_plan_registry(source_df)` · `def_try_fetch_yfinance(fetch_df)` · `def_build_dashboard_blueprints(asset_df, component_df, schema_df, token_df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG030_WarehouseV6AllBuilder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_WAREHOUSE_V6_ALL_20260507_100922/vap_warehouse_v6_all_builder`(版本 1;現役 `vap_warehouse_v6_all_builder.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_write_table(con, table_name, df)` · `def_build_live_fetch_status()` · `def_fetch_yfinance_prices()` · `def_generate_dashboard_html(blueprint_df)` · `def_build_normalized_series(price_df)` · `def_build_rolling_correlation_plan(fetch_status_df)` · `def_build_lead_lag_plan(fetch_status_df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG032_WarehouseV7QuantBuilder
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/_output/VAP_WAREHOUSE_V7_QUANT_20260507_104041/vap_warehouse_v7_quant_builder`(版本 1;現役 `vap_warehouse_v7_quant_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_write_table(con, table_name, df)` · `def_prepare_price_data(price_df)` · `def_calculate_rolling_correlation(norm_df)` · `def_calculate_lead_lag(norm_df)` · `def_build_factor_plan(fetch_status_df)` · `def_build_regime_plan()` · `def_write_query_pack()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG033_Server
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/api/vap_server`(版本 1;現役 `vap_server.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **函式**(10):`health_check()` · `list_data_sources()` · `load_data(source, rows)` · `get_demo_data(ticker, days)` · `compute_indicators(source, indicators)` · `list_templates()` · `get_template(name)` · `save_template(name, config)` · `delete_template(name)` · `run_server(host, port)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG034_ChartDashboard
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/charts/vap_chart_dashboard`(版本 1;現役 `vap_chart_dashboard.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPDashboard
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG035_ChartHeatmap
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/charts/vap_chart_heatmap`(版本 1;現役 `vap_chart_heatmap.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPHeatmapChart
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG036_ChartStack
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/charts/vap_chart_stack`(版本 1;現役 `vap_chart_stack.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPStackChart
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG037_ChartTechnical
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/charts/vap_chart_technical`(版本 1;現役 `vap_chart_technical.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTechnicalChart
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG038_ChartTwoaxis
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/charts/vap_chart_twoaxis`(版本 1;現役 `vap_chart_twoaxis.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTwoAxisChart
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG039_Annotations
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_annotations`(版本 1;現役 `vap_annotations.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:EventLine, HighLowMarker, CrisisZone, VAPAnnotationEngine
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG040_Config
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_config`(版本 1;現役 `vap_config.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPPaths, IndicatorCategory, ExportConfig, ChartDefaults
- **函式**(2):`get_price_column(df, prefer_adj)` · `resolve_ohlcv_columns(df)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG041_DataAdapter
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_data_adapter`(版本 1;現役 `vap_data_adapter.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPDataAdapter
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG042_Export
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_export`(版本 1;現役 `vap_export.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPExportEngine
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG043_Indicators
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_indicators`(版本 1;現役 `vap_indicators.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPIndicatorEngine
- **自測**:匯入型

### VAP_ENG044_Templates
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/core/vap_templates`(版本 1;現役 `vap_templates.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTemplateManager
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG045_Main
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/main`(版本 1;現役 `main.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **函式**(5):`cmd_health()` · `cmd_demo()` · `cmd_compute(args)` · `cmd_serve(args)` · `main()`
- **CLI**:`--chart` `--days` `--demo` `--health` `--indicators` `--output` `--port` `--serve` `--source` `--template` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG046_Layout
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VAP/vap_layout`(版本 1;現役 `vap_layout.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:AnnotationBox, VAPLayoutEngine
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG047_MDL014VrnFinalControlCenterV061575MODULEV061575
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL014_vrn_final_control_center_v061575__MODULE__v061575`(版本 1;現役 `VRN_MDL014_vrn_final_control_center_v061575__MODULE__v061575.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_asset(label, path, role, required)` · `def_html_table(title, rows, limit)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG048_MDL015VrnFinalProductionLockRegistryV061573SUPPORTRULEV061573
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL015_vrn_final_production_lock_registry_v061573__SUPPORT_RULE__v061573`(版本 1;現役 `VRN_MDL015_vrn_final_production_lock_registry_v061573__SUPPORT_RULE__v061573.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_asset(label, path, required, role)` · `def_html_table(title, rows)` · `def_write_html(path, counts, sections)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG049_MDL016VrnFinalIntegrationGovernanceSealV0615703GOVERNANCEV0615703
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL016_vrn_final_integration_governance_seal_v0615703__GOVERNANCE__v0615703`(版本 1;現役 `VRN_MDL016_vrn_final_integration_governance_seal_v0615703__GOVERNANCE__v0615703.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_file_asset(label, path, required, role)` · `def_html_table(title, rows)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG050_MDL018VRNMDLSummaryPipelineBridgeAIOV01CORE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL018_VRN_MDL_SummaryPipelineBridge_AIO_v01__CORE_`(版本 1;現役 `VRN_MDL018_VRN_MDL_SummaryPipelineBridge_AIO_v01__CORE__v01.py`)
- **功能**:def VRN_MDL_SummaryPipelineBridge_AIO_v01
- **函式**(12):`def_bridge_find_vrn_root_v01()` · `def_bridge_router_path_v01()` · `def_bridge_active_config_v01()` · `def_bridge_read_json_v01(path)` · `def_bridge_write_json_v01(path, obj)` · `def_bridge_write_csv_v01(path, rows)` · `def_bridge_read_csv_v01(path)` · `def_bridge_html_v01(x)` · `def_bridge_import_router_v01()` · `def_bridge_load_records_v01(input_json, input_csv)`
- **CLI**:`--active-config` `--db-ready-csv` `--input-csv` `--input-json` `--output-csv` `--output-html` `--output-json` `--selftest`
- **自測**:✅ --selftest

### VAP_ENG051_MDL035VrnRealCommitArgfixBackupPostcheckV0615711MODULEV0615711
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL035_vrn_real_commit_argfix_backup_postcheck_v0615711__MODULE__v0615711`(版本 1;現役 `VRN_MDL035_vrn_real_commit_argfix_backup_postcheck_v0615711__MODULE__v0615711.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_get(row, aliases)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG052_MDL036VrnRealCommitBackupPostcheckRollbackV061571MODULEV061571
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL036_vrn_real_commit_backup_postcheck_rollback_v061571__MODULE__v061571`(版本 1;現役 `VRN_MDL036_vrn_real_commit_backup_postcheck_rollback_v061571__MODULE__v061571.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_strip_sql_comments(text)`
- **自測**:主程式可跑

### VAP_ENG054_MDL047VrnPackageCompatSmokeV061576MODULEV061576
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL047_vrn_package_compat_smoke_v061576__MODULE__v061576`(版本 1;現役 `VRN_MDL047_vrn_package_compat_smoke_v061576__MODULE__v061576.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_light(sev)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_find_latest_dir(root, prefixes)` · `def_ast_compile_check(path)` · `def_file_size(path)` · `def_copy_asset(src, package_dir, category)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG055_MDL048VrnFinalHandoverCommitBlockerSealV0615702GOVERNANCEV0615702
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL048_vrn_final_handover_commit_blocker_seal_v0615702__GOVERNANCE__v0615702`(版本 1;現役 `VRN_MDL048_vrn_final_handover_commit_blocker_seal_v0615702__GOVERNANCE__v0615702.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_file_asset(label, path, required)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG056_MDL049V0569CanonicalEnglishSystemSealFixGOVERNANCE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL049_v0569_canonical_english_system_seal_fix__GOVERNANCE_`(版本 1;現役 `VRN_MDL049_v0569_canonical_english_system_seal_fix__GOVERNANCE__v0569.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_h(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_read_json(path)` · `def_remove_summary_cols(rows)` · `def_to_float(x)` · `def_fmt_by_unit(x, unit)` · `def_safe_str(x)` · `def_official_category(cat, data, canon)`
- **CLI**:`--out-basic-csv` `--out-basic-parquet` `--out-duckdb` `--out-fin-csv` `--out-fin-parquet` `--out-html` `--out-json` `--out-official-csv` `--out-quarantine-csv` `--out-review-csv` `--out-round-csv` `--out-support-csv`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG057_MDL083VRNV141D6CSourceHygieneNoHangBRIDGEV141D6C
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL083_VRN_v141D6C_Source_Hygiene_NoHang__BRIDGE__v141D6C`(版本 1;現役 `VRN_MDL083_VRN_v141D6C_Source_Hygiene_NoHang__BRIDGE__v141D6C.py`)
- **功能**:無說明(候補)
- **函式**(12):`now()` · `lamp(s)` · `esc(x)` · `norm(x)` · `blank(x)` · `num(x)` · `fmt(col, val)` · `write_csv(path, rows)` · `write_json(path, obj)` · `add(rows, cat, item, value, expected)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG058_MDL084VRNV141AReadOnlyConsumerLoaderMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL084_VRN_v141A_ReadOnly_Consumer_Loader__MODULE_`(版本 1;現役 `VRN_MDL084_VRN_v141A_ReadOnly_Consumer_Loader__MODULE__v141A.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_sha256(path)` · `def_sql_ident(x)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_add_matrix(rows, page, gate, value, expected)` · `def_find_asset(datasets, asset_id)` · `def_table_exists(con, table_name)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG059_MDL085VRNV139PPostBridgeRescoreMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL085_VRN_v139P_PostBridge_Rescore__MODULE_`(版本 1;現役 `VRN_MDL085_VRN_v139P_PostBridge_Rescore__MODULE__v139P.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_read_text(path)` · `def_sha1(path)` · `def_add_matrix(rows, page, gate, value, status)` · `def_write_csv(path, rows)` · `def_find_latest_n2_strict_csv()` · `def_read_csv(path)` · `def_import_core(label, path)` · `def_strip_ps_comments(text)`
- **自測**:主程式可跑

### VAP_ENG060_MDL086VRNV139MRedFalsePositiveCrusherMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL086_VRN_v139M_RedFalsePositiveCrusher__MODULE_`(版本 1;現役 `VRN_MDL086_VRN_v139M_RedFalsePositiveCrusher__MODULE__v139M.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_read_text(path)` · `def_sha1(path)` · `def_add_matrix(rows, page, gate, value, status)` · `def_write_csv(path, rows)` · `def_import_file(label, path)` · `def_is_archive_or_generated(p)` · `def_is_production_candidate(p)` · `def_scan_files_fast()`
- **自測**:主程式可跑

### VAP_ENG061_MDL087VRNV139KDualCoreCoverageAnalyzerMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL087_VRN_v139K_DualCore_Coverage_Analyzer__MODULE_`(版本 1;現役 `VRN_MDL087_VRN_v139K_DualCore_Coverage_Analyzer__MODULE__v139K.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_read_text(path)` · `def_add_matrix(rows, page, gate, value, status)` · `def_write_csv(path, rows)` · `def_import_file(label, path)` · `def_scan_files()` · `def_analyze_python(path, text)` · `def_analyze_powershell(path, text)` · `def_build_patch_plan(module_rows)`
- **自測**:主程式可跑

### VAP_ENG062_MDL088VrnYfinanceHeaderCanonicalRefreshV06147DATASOURCEV06147
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL088_vrn_yfinance_header_canonical_refresh_v06147__DATA_SOURCE__v06147`(版本 1;現役 `VRN_MDL088_vrn_yfinance_header_canonical_refresh_v06147__DATA_SOURCE__v06147.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_is_blank(x)` · `def_fmt_num(x, digits)` · `def_fmt_int(x)` · `def_fmt_pct(x)` · `def_parse_date(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG063_MDL092VrnPostCommitProductionSealV0615721GOVERNANCEV0615721
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL092_vrn_post_commit_production_seal_v0615721__GOVERNANCE__v0615721`(版本 1;現役 `VRN_MDL092_vrn_post_commit_production_seal_v0615721__GOVERNANCE__v0615721.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_html_table(title, rows, limit)` · `def_write_html(path, counts, sections)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG064_MDL093VrnTriflowCloseoutSealFinalOpsConsoleV0615701GOVERNANCEV0615701
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL093_vrn_triflow_closeout_seal_final_ops_console_v0615701__GOVERNANCE__v0615701`(版本 1;現役 `VRN_MDL093_vrn_triflow_closeout_seal_final_ops_console_v0615701__GOVERNANCE__v0615701.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_file_asset(label, path, required)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG065_MDL094VrnCommitCandidatePackApprovalGateV061570MODULEV061570
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL094_vrn_commit_candidate_pack_approval_gate_v061570__MODULE__v061570`(版本 1;現役 `VRN_MDL094_vrn_commit_candidate_pack_approval_gate_v061570__MODULE__v061570.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_sha256_text(text)` · `def_read_csv(path)` · `def_read_json(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG066_MDL095WorkerARowLevelJoinScanV06154COREV06154
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL095_worker_A_row_level_join_scan_v06154__CORE__v06154`(版本 1;現役 `VRN_MDL095_worker_A_row_level_join_scan_v06154__CORE__v06154.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_table_html(title, rows)` · `def_write_html(path, title, subtitle, counts, sections)` · `def_file_match(row, filename, ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG067_MDL096WorkerCBasicinfoMarketdataScanV06154BASICINFOV06154
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL096_worker_C_basicinfo_marketdata_scan_v06154__BASICINFO__v06154`(版本 1;現役 `VRN_MDL096_worker_C_basicinfo_marketdata_scan_v06154__BASICINFO__v06154.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_table_html(title, rows)` · `def_write_html(path, title, subtitle, counts, sections)` · `def_file_match(row, filename, ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG068_MDL097VrnFinancialdataFinalEvidenceSelectorV06149FINANCIALDATAV06149
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL097_vrn_financialdata_final_evidence_selector_v06149__FINANCIALDATA__v06149`(版本 1;現役 `VRN_MDL097_vrn_financialdata_final_evidence_selector_v06149__FINANCIALDATA__v06149.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_is_blank(x)` · `def_to_float(x)` · `def_fmt_num(x, digits)` · `def_fmt_pct(numer, denom)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)`
- **自測**:主程式可跑

### VAP_ENG069_MDL098VrnFinancialSsotCompleteTrustIntegrationV0608FINANCIALDATA
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL098_vrn_financial_ssot_complete_trust_integration_v0608__FINANCIALDATA_`(版本 1;現役 `VRN_MDL098_vrn_financial_ssot_complete_trust_integration_v0608__FINANCIALDATA__v0608.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_read_csv(path)` · `def_write_csv(path, df)` · `def_write_json(path, obj)` · `def_safe_parquet(path, df)` · `def_safe_duckdb(path, tables)` · `def_status_lights(sev)` · `def_clean_text(x)` · `def_key_text(x)` · `def_clean_num(x)` · `def_format_num(x, decimals, suffix)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG070_MDL099VrnValuationMethodPrecisionRebindV0593MODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL099_vrn_valuation_method_precision_rebind_v0593__MODULE_`(版本 1;現役 `VRN_MDL099_vrn_valuation_method_precision_rebind_v0593__MODULE__v0593.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean_text(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_safe_json_loads(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG071_MDL135VRNV140B3CSVCaseSafeAuditorGOVERNANCEV140B3
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL135_VRN_v140B3_CSV_CaseSafe_Auditor__GOVERNANCE__v140B3`(版本 1;現役 `VRN_MDL135_VRN_v140B3_CSV_CaseSafe_Auditor__GOVERNANCE__v140B3.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_norm_header(x)` · `def_source_prefix(col)` · `def_type_guess(sample)` · `def_open_csv(path)` · `def_count_csv_rows(path)` · `def_schema_and_audit(path, sample_limit)` · `def_write_csv(path, rows)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG072_MDL206VRNMDLYFinanceInfoReferencePrefixV02DATASOURCE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL206_VRN_MDL_YFinanceInfoReferencePrefix_v02__DATA_SOURCE_`(版本 1;現役 `VRN_MDL206_VRN_MDL_YFinanceInfoReferencePrefix_v02__DATA_SOURCE__v02.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_yfinance_info_reference_field_map_v02()` · `def_yfinance_info_protected_basicinfo_fields_v02()` · `def_yfinance_info_to_reference_record_v02(info, yf_ticker)` · `def_yfinance_info_merge_reference_only_v02(basicinfo, yfinance_info, yf_ticker)` · `def_validate_yfinance_reference_prefix_v02(row)` · `def_fetch_yfinance_info_reference_v02(yf_ticker)` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG073_MDL208VRNV139LTop10AcceleratorAnalyzerMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL208_VRN_v139L_Top10_Accelerator_Analyzer__MODULE_`(版本 1;現役 `VRN_MDL208_VRN_v139L_Top10_Accelerator_Analyzer__MODULE__v139L.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_read_text(path)` · `def_sha1(path)` · `def_add_matrix(rows, page, gate, value, status)` · `def_write_csv(path, rows)` · `def_import_file(label, path)` · `def_is_target_file(p)` · `def_scan_files_fast()` · `def_analyze_python(path, text)`
- **自測**:主程式可跑

### VAP_ENG074_MDL209VRNV139LTop10AcceleratorAnalyzerMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL209_VRN_v139L_Top10_Accelerator_Analyzer__MODULE_`(版本 1;現役 `VRN_MDL209_VRN_v139L_Top10_Accelerator_Analyzer__MODULE__v139L.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_read_text(path)` · `def_sha1(path)` · `def_add_matrix(rows, page, gate, value, status)` · `def_write_csv(path, rows)` · `def_import_file(label, path)` · `def_is_target_file(p)` · `def_scan_files_fast()` · `def_analyze_python(path, text)`
- **自測**:主程式可跑

### VAP_ENG075_MDL210VRNV070AllInOneMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL210_VRN_v070_AllInOne__MODULE_`(版本 1;現役 `VRN_MDL210_VRN_v070_AllInOne__MODULE__v070.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_lamp(s)` · `def_progress(stage, idx, total, msg)` · `def_esc(x)` · `def_sha256(p)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_load_ssot()` · `def_ssot_match(text, ssot)` · `def_extract_tables_pdf(pdf_path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG076_MDL211VRNV141D6BNoHangAcceleratorBRIDGEV141D6B
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL211_VRN_v141D6B_NoHang_Accelerator__BRIDGE__v141D6B`(版本 1;現役 `VRN_MDL211_VRN_v141D6B_NoHang_Accelerator__BRIDGE__v141D6B.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_status_lamp(s)` · `def_esc(x)` · `def_norm(x)` · `def_blank(x)` · `def_num(x)` · `def_fmt(col, val)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_add(rows, cat, item, value, expected)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG077_MDL212VRNV141D5BTestDebugActivatorMODULEV141D5B
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL212_VRN_v141D5B_Test_Debug_Activator__MODULE__v141D5B`(版本 1;現役 `VRN_MDL212_VRN_v141D5B_Test_Debug_Activator__MODULE__v141D5B.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_status_lamp(status)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_add_matrix(rows, category, item, value, expected)` · `def_import_file(path, name)` · `def_check_core_tools()` · `def_default_20_libs()` · `def_load_20_libs()`
- **CLI**:`--upgrade`
- **自測**:主程式可跑

### VAP_ENG078_MDL213VRNV141D5AegisCeleritasRuntimeBridgeMODULEV141D5
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL213_VRN_v141D5_Aegis_Celeritas_Runtime_Bridge__MODULE__v141D5`(版本 1;現役 `VRN_MDL213_VRN_v141D5_Aegis_Celeritas_Runtime_Bridge__MODULE__v141D5.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_status_lamp(status)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_add_matrix(rows, category, item, value, expected)` · `def_import_file(path, name)` · `def_check_core_tools()` · `def_default_20_libs()` · `def_load_20_libs()`
- **CLI**:`--upgrade`
- **自測**:主程式可跑

### VAP_ENG079_MDL214VRNV141D4FunctionalModuleContractMODULEV141D4
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL214_VRN_v141D4_Functional_Module_Contract__MODULE__v141D4`(版本 1;現役 `VRN_MDL214_VRN_v141D4_Functional_Module_Contract__MODULE__v141D4.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_html_escape(x)` · `def_status_lamp(status)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_add_matrix(rows, category, item, value, expected)` · `def_ast_scan(path)` · `def_import_module(path, name)` · `def_check_module_set(module_set, module_type)` · `def_scan_input_files()`
- **自測**:主程式可跑

### VAP_ENG080_MDL215VrnFinancialdataTriflowStagingV06153FINANCIALDATAV06153
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL215_vrn_financialdata_triflow_staging_v06153__FINANCIALDATA__v06153`(版本 1;現役 `VRN_MDL215_vrn_financialdata_triflow_staging_v06153__FINANCIALDATA__v06153.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_light(sev)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_find_latest_json(run_root, pattern)` · `def_flatten_json_rows(obj, source_name)` · `def_first(row, names)` · `def_pct(n, d)` · `def_input_manifest(input_dir)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG081_MDL216FinalUnifiedGateV06154COREV06154
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL216_final_unified_gate_v06154__CORE__v06154`(版本 1;現役 `VRN_MDL216_final_unified_gate_v06154__CORE__v06154.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_table_html(title, rows)` · `def_write_html(path, title, subtitle, counts, sections)` · `def_file_match(row, filename, ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG082_MDL217WorkerBTargetedRestoreScanV06154COREV06154
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL217_worker_B_targeted_restore_scan_v06154__CORE__v06154`(版本 1;現役 `VRN_MDL217_worker_B_targeted_restore_scan_v06154__CORE__v06154.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_table_html(title, rows)` · `def_write_html(path, title, subtitle, counts, sections)` · `def_file_match(row, filename, ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG083_MDL218VrnFinancialDataConfirmVerifyV06125FINANCIALDATAV06125
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL218_vrn_financial_data_confirm_verify_v06125__FINANCIALDATA__v06125`(版本 1;現役 `VRN_MDL218_vrn_financial_data_confirm_verify_v06125__FINANCIALDATA__v06125.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_status_lights(sev)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_read_csv_any(path)` · `def_import_module(path)` · `def_compile_import(path)` · `def_backup(path, tag)` · `def_replace_function(text, func_name, new_func)` · `def_patch_bridge_date_noise(bridge_path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG084_MDL219VrnAnalystTargetReportdateSsotPatchV06123REPORTV06123
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL219_vrn_analyst_target_reportdate_ssot_patch_v06123__REPORT__v06123`(版本 1;現役 `VRN_MDL219_vrn_analyst_target_reportdate_ssot_patch_v06123__REPORT__v06123.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_status_lights(sev)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_compile_import(path)` · `def_table_html(title, rows)` · `def_write_html(path, result, sections)` · `def_backup(path, tag)` · `def_append_ssot_block(ssot_path)` · `def_replace_function(text, func_name, new_func_code)` · `def_patch_bridge(bridge_path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG086_MDL221VRNGeometryReconRunnerMODULEV00
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL221_VRN_GeometryRecon_Runner__MODULE__v0_0`(版本 1;現役 `VRN_MDL221_VRN_GeometryRecon_Runner__MODULE__v0_0.py`)
- **功能**:無說明(候補)
- **函式**(5):`imp(path, name)` · `read_csv(p)` · `write_csv(p, rows)` · `is_target(src)` · `main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG087_MDL227VrnBusinessValidationReportV061574REPORTV061574
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL227_vrn_business_validation_report_v061574__REPORT__v061574`(版本 1;現役 `VRN_MDL227_vrn_business_validation_report_v061574__REPORT__v061574.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_to_float(x)` · `def_to_int(x)` · `def_html_table(title, rows, limit)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG088_MDL228VrnBusinessValidationReportV061574REPORTV061574
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL228_vrn_business_validation_report_v061574__REPORT__v061574`(版本 1;現役 `VRN_MDL228_vrn_business_validation_report_v061574__REPORT__v061574.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefixes)` · `def_sha256_file(path)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_to_float(x)` · `def_to_int(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG090_MDL230VrnFinalStagingEvidenceSealV0615694GOVERNANCEV0615694
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL230_vrn_final_staging_evidence_seal_v0615694__GOVERNANCE__v0615694`(版本 1;現役 `VRN_MDL230_vrn_final_staging_evidence_seal_v0615694__GOVERNANCE__v0615694.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_float(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_read_json(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_get(row, aliases)`
- **自測**:主程式可跑

### VAP_ENG092_MDL232VrnOfficialCellValidationMaterializationGateV06156810615691GOVERNANCEV0615681
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL232_vrn_official_cell_validation_materialization_gate_v0615681_0615691__GOVERNANCE__v0615681`(版本 1;現役 `VRN_MDL232_vrn_official_cell_validation_materialization_gate_v0615681_0615691__GOVERNANCE__v0615681.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_flat(x)` · `def_norm(x)` · `def_int(x, default)` · `def_float(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG093_MDL233VrnFinalValidationRouterMaterializationGateV061569GOVERNANCEV061569
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL233_vrn_final_validation_router_materialization_gate_v061569__GOVERNANCE__v061569`(版本 1;現役 `VRN_MDL233_vrn_final_validation_router_materialization_gate_v061569__GOVERNANCE__v061569.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_float(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_read_json(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_get(row, aliases)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG094_MDL234VrnFlowaOfficialParserFlowcHealthV061567DATASOURCEV061567
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL234_vrn_flowa_official_parser_flowc_health_v061567__DATA_SOURCE__v061567`(版本 1;現役 `VRN_MDL234_vrn_flowa_official_parser_flowc_health_v061567__DATA_SOURCE__v061567.py`)
- **功能**:無說明(候補)
- **類**:DefSimpleTableParser
- **函式**(12):`def_clean(x)` · `def_flat(x)` · `def_norm(x)` · `def_int(x, default)` · `def_float(x, default)` · `def_light(sev)` · `def_sha256(path)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_read_json(path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG095_MDL235VrnOfficialFetchDryrunParserReadyV06156551DATASOURCEV06156551
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL235_vrn_official_fetch_dryrun_parser_ready_v06156551__DATA_SOURCE__v06156551`(版本 1;現役 `VRN_MDL235_vrn_official_fetch_dryrun_parser_ready_v06156551__DATA_SOURCE__v06156551.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_clean(x)` · `def_flat(x)` · `def_norm(x)` · `def_int(x, default)` · `def_float(x, default)` · `def_light(sev)` · `def_sha256_bytes(data)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG096_MDL236VrnOfficialForecastValidationPreflightSealV06156541GOVERNANCEV06156541
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL236_vrn_official_forecast_validation_preflight_seal_v06156541__GOVERNANCE__v06156541`(版本 1;現役 `VRN_MDL236_vrn_official_forecast_validation_preflight_seal_v06156541__GOVERNANCE__v06156541.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_norm(x)` · `def_float(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_get(row, aliases)` · `def_table(title, rows, limit)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG097_MDL237VrnParserRepairRouterValidationGateV0615653GOVERNANCEV0615653
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL237_vrn_parser_repair_router_validation_gate_v0615653__GOVERNANCE__v0615653`(版本 1;現役 `VRN_MDL237_vrn_parser_repair_router_validation_gate_v0615653__GOVERNANCE__v0615653.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_flat(x)` · `def_norm(x)` · `def_int(x, default)` · `def_float(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG098_MDL238VrnAccountPeriodValueParserPreflightV0615651MODULEV0615651
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL238_vrn_account_period_value_parser_preflight_v0615651__MODULE__v0615651`(版本 1;現役 `VRN_MDL238_vrn_account_period_value_parser_preflight_v0615651__MODULE__v0615651.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean(x)` · `def_flat(x)` · `def_norm(x)` · `def_float(x, default)` · `def_int(x, default)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG099_MDL239VrnNewReportFormatSystemDefaultInstallerV06155REPORTV06155
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL239_vrn_new_report_format_system_default_installer_v06155__REPORT__v06155`(版本 1;現役 `VRN_MDL239_vrn_new_report_format_system_default_installer_v06155__REPORT__v06155.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_now()` · `def_sha256(path)` · `def_backup_if_exists(path, tag)` · `def_write_text(path, text)` · `def_write_json(path, obj)` · `def_light(sev)` · `def_gate_module_code()` · `def_registry_obj()` · `def_playbook_text()` · `def_write_html_report(path, rows, registry)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG100_MDL240VrnDualflowFinalReportRepairV0615492REPORTV0615492
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL240_vrn_dualflow_final_report_repair_v0615492__REPORT__v0615492`(版本 1;現役 `VRN_MDL240_vrn_dualflow_final_report_repair_v0615492__REPORT__v0615492.py`)
- **功能**:無說明(候補)
- **函式**(10):`def_clean(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_table(title, rows)` · `def_write_html(path, result, sections)` · `def_flow_b_pass(flow_b, source)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG101_MDL241FlowATableReconstructionPlannerV061549SUPPORTRULEV061549
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL241_flow_a_table_reconstruction_planner_v061549__SUPPORT_RULE__v061549`(版本 1;現役 `VRN_MDL241_flow_a_table_reconstruction_planner_v061549__SUPPORT_RULE__v061549.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_flat_text(x)` · `def_norm_key(x)` · `def_light(sev)` · `def_find_latest_dir(root, prefix)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_get(row, aliases)` · `def_int(x, default)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG102_MDL242VrnFinancialdataRowLevelJoinRepairV06153FINANCIALDATAV06153
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL242_vrn_financialdata_row_level_join_repair_v06153__FINANCIALDATA__v06153`(版本 1;現役 `VRN_MDL242_vrn_financialdata_row_level_join_repair_v06153__FINANCIALDATA__v06153.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_to_float(x)` · `def_fmt_num(x)` · `def_fmt_pct(num, den)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG103_MDL243VrnEvidenceSourceDecontaminationRouterV06152MODULEV06152
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL243_vrn_evidence_source_decontamination_router_v06152__MODULE__v06152`(版本 1;現役 `VRN_MDL243_vrn_evidence_source_decontamination_router_v06152__MODULE__v06152.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_is_target_status(status)` · `def_is_optional_status(status)` · `def_is_summary_pollution(path)`
- **自測**:主程式可跑

### VAP_ENG104_MDL244VrnFinancialdataRepairRouterV06151FINANCIALDATAV06151
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL244_vrn_financialdata_repair_router_v06151__FINANCIALDATA__v06151`(版本 1;現役 `VRN_MDL244_vrn_financialdata_repair_router_v06151__FINANCIALDATA__v06151.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(root, patterns)` · `def_is_target_status(status)` · `def_is_optional_status(status)` · `def_file_tokens(filename)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG105_MDL245VrnBrokerAbbrevSsotFinalPatchV06135SUPPORTRULEV06135
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL245_vrn_broker_abbrev_ssot_final_patch_v06135__SUPPORT_RULE__v06135`(版本 1;現役 `VRN_MDL245_vrn_broker_abbrev_ssot_final_patch_v06135__SUPPORT_RULE__v06135.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, patterns)` · `def_first(row, keys)` · `def_final_broker_alias_rows()` · `def_final_broker_map()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG107_MDL247VrnBrokerEnglishAbbrevSsotNormalizeV06134SUPPORTRULEV06134
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL247_vrn_broker_english_abbrev_ssot_normalize_v06134__SUPPORT_RULE__v06134`(版本 1;現役 `VRN_MDL247_vrn_broker_english_abbrev_ssot_normalize_v06134__SUPPORT_RULE__v06134.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, patterns)` · `def_first(row, keys)` · `def_fallback_broker_map()` · `def_extract_possible_broker_map_from_ast(ssot_path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG108_MDL248VrnCompanyReportMatrixCalibrationV06131REPORTV06131
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL248_vrn_company_report_matrix_calibration_v06131__REPORT__v06131`(版本 1;現役 `VRN_MDL248_vrn_company_report_matrix_calibration_v06131__REPORT__v06131.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_text(x)` · `def_num(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_first(row, keys)` · `def_parse_rate_cell(cell)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG109_MDL249VrnCompanyReportOnlyGateV06130REPORTV06130
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL249_vrn_company_report_only_gate_v06130__REPORT__v06130`(版本 1;現役 `VRN_MDL249_vrn_company_report_only_gate_v06130__REPORT__v06130.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_text(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_first(row, keys)` · `def_is_tw_ticker(ticker)` · `def_company_report_classify(row)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG110_MDL250VrnOneRowFileValidationMatrixV06129GOVERNANCEV06129
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL250_vrn_one_row_file_validation_matrix_v06129__GOVERNANCE__v06129`(版本 1;現役 `VRN_MDL250_vrn_one_row_file_validation_matrix_v06129__GOVERNANCE__v06129.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_text(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_first(row, keys)` · `def_num(x)` · `def_int_fmt(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG111_MDL251VrnInputFileCoverageReconcileV06128MODULEV06128
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL251_vrn_input_file_coverage_reconcile_v06128__MODULE__v06128`(版本 1;現役 `VRN_MDL251_vrn_input_file_coverage_reconcile_v06128__MODULE__v06128.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_text(x)` · `def_lights(sev)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_first(row, keys)` · `def_tokenize_filename(name)` · `def_yfinance_candidates(ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG112_MDL252VrnFinancialFinalSealV06127FINANCIALDATAV06127
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL252_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127`(版本 1;現役 `VRN_MDL252_vrn_financial_final_seal_v06127__FINANCIALDATA__v06127.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_lights(sev)` · `def_first(row, keys)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_find_latest(run_root, pattern)` · `def_apply_final_alias(row)` · `def_is_db_ready(row)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG114_MDL254VrnFinancialRescueSsotAliasV06126FINANCIALDATAV06126
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL254_vrn_financial_rescue_ssot_alias_v06126__FINANCIALDATA__v06126`(版本 1;現役 `VRN_MDL254_vrn_financial_rescue_ssot_alias_v06126__FINANCIALDATA__v06126.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_key(x)` · `def_status_lights(sev)` · `def_float_or_none(x)` · `def_numeric_tokens(x)` · `def_get(row, keys)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_read_csv_any(path)` · `def_import_module(path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG115_MDL255VrnMasterBridgeFunctionalSmokeTestV06122GOVERNANCEV06122
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL255_vrn_master_bridge_functional_smoke_test_v06122__GOVERNANCE__v06122`(版本 1;現役 `VRN_MDL255_vrn_master_bridge_functional_smoke_test_v06122__GOVERNANCE__v06122.py`)
- **功能**:無說明(候補)
- **函式**(7):`def_status_lights(sev)` · `def_write_json(path, obj)` · `def_write_csv(path, rows)` · `def_import_bridge(path)` · `def_table_html(title, rows)` · `def_write_html(path, result, sections)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG116_MDL256RestoreVisVrnMasterRegistryBridgeV0611ManifestGOVERNANCE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL256_restore_vis_vrn_master_registry_bridge_v0611_manifest__GOVERNANCE_`(版本 1;現役 `VRN_MDL256_restore_vis_vrn_master_registry_bridge_v0611_manifest__GOVERNANCE__v0611.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_status_lights(sev)` · `def_sha256(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_load_module_paths(path)` · `def_scan_module(path)` · `def_build_manifest(scan_rows)` · `def_replace_source_manifest(text, manifest)` · `def_test_import(path)` · `def_normalize_header(c)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG117_MDL257VrnNameShortFinancialValidationV0606FINANCIALDATA
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL257_vrn_name_short_financial_validation_v0606__FINANCIALDATA_`(版本 1;現役 `VRN_MDL257_vrn_name_short_financial_validation_v0606__FINANCIALDATA__v0606.py`)
- **功能**:無說明(候補)
- **函式**(11):`def_read_csv(path)` · `def_write_csv(path, df)` · `def_write_json(path, obj)` · `def_safe_parquet(path, df)` · `def_safe_duckdb(path, tables)` · `def_status_lights(sev)` · `def_band(score)` · `def_clean_num(x)` · `def_format_num(x, decimals, suffix)` · `def_first(row, cols)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG118_MDL258VrnFinancialSsotInputRebindV0604FINANCIALDATA
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL258_vrn_financial_ssot_input_rebind_v0604__FINANCIALDATA_`(版本 1;現役 `VRN_MDL258_vrn_financial_ssot_input_rebind_v0604__FINANCIALDATA__v0604.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_read_csv(path)` · `def_write_csv(path, df)` · `def_write_json(path, obj)` · `def_load_module(path)` · `def_first(row, cols)` · `def_status_lights(sev)` · `def_format_num(val, unit)` · `def_numeric_tokens(raw)` · `def_parse_value(raw)` · `def_table_html(title, df, max_rows)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG119_MDL259VrnReportDateWindowTableRestoreV0597REPORT
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL259_vrn_report_date_window_table_restore_v0597__REPORT_`(版本 1;現役 `VRN_MDL259_vrn_report_date_window_table_restore_v0597__REPORT__v0597.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_norm_filename(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG120_MDL260VrnValuationDictionarySourcebankRepairV0595MODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL260_vrn_valuation_dictionary_sourcebank_repair_v0595__MODULE_`(版本 1;現役 `VRN_MDL260_vrn_valuation_dictionary_sourcebank_repair_v0595__MODULE__v0595.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean_text(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_safe_json_loads(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG121_MDL261VrnFirstpageSourcebankValuationRepairV0594MODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL261_vrn_firstpage_sourcebank_valuation_repair_v0594__MODULE_`(版本 1;現役 `VRN_MDL261_vrn_firstpage_sourcebank_valuation_repair_v0594__MODULE__v0594.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean_text(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_safe_json_loads(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG122_MDL262VrnValuationMethodSsotRebindV0592SUPPORTRULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL262_vrn_valuation_method_ssot_rebind_v0592__SUPPORT_RULE_`(版本 1;現役 `VRN_MDL262_vrn_valuation_method_ssot_rebind_v0592__SUPPORT_RULE__v0592.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_config()` · `def_now()` · `def_h(x)` · `def_nonblank(x)` · `def_clean_text(x)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_write_json(path, obj)` · `def_first(row, keys)` · `def_safe_json_loads(x)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG123_MDL263VrnUnifiedOperationDbUiV0582MODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL263_vrn_unified_operation_db_ui_v0582__MODULE_`(版本 1;現役 `VRN_MDL263_vrn_unified_operation_db_ui_v0582__MODULE__v0582.py`)
- **功能**:無說明(候補)
- **類**:Handler
- **函式**(12):`def_now()` · `def_log(level, msg)` · `def_json(obj)` · `def_h(x)` · `def_hash_file(path)` · `def_ensure_base(base)` · `def_read_csv(path)` · `def_count_csv(path)` · `def_write_json(path, obj)` · `def_normalize_filename(name)`
- **CLI**:`--base` `--bridge-json` `--canonical-dir` `--port` `--preview-duckdb` `--run-dir` `--stable-dir` `--vrn-root`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG124_MDL264VrnUnifiedOperationDbUiV0582MODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL264_vrn_unified_operation_db_ui_v0582__MODULE_`(版本 1;現役 `VRN_MDL264_vrn_unified_operation_db_ui_v0582__MODULE__v0582.py`)
- **功能**:無說明(候補)
- **類**:Handler
- **函式**(12):`def_now()` · `def_log(level, msg)` · `def_json(obj)` · `def_h(x)` · `def_hash_file(path)` · `def_ensure_base(base)` · `def_read_csv(path)` · `def_count_csv(path)` · `def_write_json(path, obj)` · `def_normalize_filename(name)`
- **CLI**:`--base` `--bridge-json` `--canonical-dir` `--port` `--preview-duckdb` `--run-dir` `--stable-dir` `--vrn-root`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG125_MDL265V0572CanonicalDuckdbViewRepairMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL265_v0572_canonical_duckdb_view_repair__MODULE_`(版本 1;現役 `VRN_MDL265_v0572_canonical_duckdb_view_repair__MODULE__v0572.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_h(x)` · `def_read_json(path)` · `def_write_json(path, obj)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_count_csv(path)` · `def_safe_df(rows, schema)` · `def_supportive_check(support_dir)` · `def_rebuild_duckdb(duckdb_path, basic_csv, financial_csv, data_trust_csv, accepted_csv)`
- **CLI**:`--accepted` `--active-report-html` `--basic` `--canonical-dir` `--data-trust` `--duckdb` `--external-optional` `--final-seal-dir` `--financial` `--manifest-main` `--manifest-v0571` `--manifest-v0572`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG126_MDL266V05692DataTrustGranularCalibrationMODULEV05692
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL266_v05692_data_trust_granular_calibration__MODULE__v05692`(版本 1;現役 `VRN_MDL266_v05692_data_trust_granular_calibration__MODULE__v05692.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_h(x)` · `def_safe_str(x)` · `def_read_csv(path)` · `def_write_csv(path, rows, empty_schema)` · `def_read_json(path)` · `def_remove_summary_cols(rows)` · `def_to_float(x)` · `def_band_value(row, col)` · `def_score_value(row, keys)`
- **CLI**:`--out-accepted-csv` `--out-basic-csv` `--out-basic-parquet` `--out-data-trust-csv` `--out-duckdb` `--out-fin-csv` `--out-fin-parquet` `--out-html` `--out-json` `--out-official-csv` `--out-quarantine-csv` `--out-round-csv`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG127_MDL267V05691DuckdbEmptySafeDataTrustCalibrationMODULEV05691
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL267_v05691_duckdb_empty_safe_data_trust_calibration__MODULE__v05691`(版本 1;現役 `VRN_MDL267_v05691_duckdb_empty_safe_data_trust_calibration__MODULE__v05691.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_h(x)` · `def_safe_str(x)` · `def_read_csv(path)` · `def_write_csv(path, rows, empty_schema)` · `def_read_json(path)` · `def_remove_summary_cols(rows)` · `def_to_float(x)` · `def_score(row, keys)` · `def_safe_rows_for_storage(rows, empty_schema)`
- **CLI**:`--out-basic-csv` `--out-basic-parquet` `--out-data-trust-csv` `--out-duckdb` `--out-fin-csv` `--out-fin-parquet` `--out-html` `--out-json` `--out-official-csv` `--out-quarantine-csv` `--out-round-csv` `--out-support-csv`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG128_MDL269VRNQualityRulesQuarantineDryRunMODULEV00
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL269_VRN_QualityRules_QuarantineDryRun__MODULE__v0_0`(版本 1;現役 `VRN_MDL269_VRN_QualityRules_QuarantineDryRun__MODULE__v0_0.py`)
- **功能**:無說明(候補)
- **函式**(6):`def_load_module(path)` · `def_read_csv(path)` · `def_write_csv(path, rows)` · `def_norm_row_keys(row)` · `def_light(risk)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG129_MDL287FlowBUiTextSpecPackV061549SUPPORTRULEV061549
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL287_flow_b_ui_text_spec_pack_v061549__SUPPORT_RULE__v061549`(版本 1;現役 `VRN_MDL287_flow_b_ui_text_spec_pack_v061549__SUPPORT_RULE__v061549.py`)
- **功能**:無說明(候補)
- **函式**(4):`def_write_json(path, obj)` · `def_write_markdown(path, spec)` · `def_write_html(path, spec)` · `def_main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG130_MDL289VrnCanonicalCleanBuilderV03SUPPORTRULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL289_vrn_canonical_clean_builder_v03__SUPPORT_RULE_`(版本 1;現役 `VRN_MDL289_vrn_canonical_clean_builder_v03__SUPPORT_RULE__v03.py`)
- **功能**:無說明(候補)
- **函式**(9):`is_summary_column(name)` · `read_csv(path)` · `write_csv(path, rows, columns)` · `get_first(row, names)` · `normalize_basic_row(row)` · `clean_rows_drop_summary(rows)` · `guess_fin_category(row)` · `normalize_financial_rows(rows)` · `main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG131_MDL290VrnSummarizerV062CliLiftPatcherMODULE
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL290_vrn_summarizer_v062_cli_lift_patcher__MODULE_`(版本 1;現役 `VRN_MDL290_vrn_summarizer_v062_cli_lift_patcher__MODULE__v062.py`)
- **功能**:無說明(候補)
- **函式**(1):`main()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG132_MDL293VrnD8bReprocessMODULEV00
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/dict/VRN/_registry/verified_numbered_modules/VRN_MDL293_vrn_d8b_reprocess__MODULE__v0_0`(版本 1;現役 `VRN_MDL293_vrn_d8b_reprocess__MODULE__v0_0.py`)
- **功能**:無說明(候補)
- **函式**(6):`find_csv(rundir)` · `resolve(headers)` · `read_rows(path)` · `write_csv(path, rows)` · `esc(x)` · `badge(chg)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG133_RuntimeImportFirewall
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/10_Core_Runtime/VIA_RuntimeImportFirewall`(版本 1;現役 `VIA_RuntimeImportFirewall.py`)
- **功能**:無說明(候補)
- **類**:VIA_RuntimeImportFirewall
- **函式**(9):`def_now()` · `def_norm(path)` · `def_sha256(path)` · `def_ast_fingerprint(path)` · `def_load_json(path)` · `def_write_json(path, payload)` · `def_verify_runtime(seal_path, modules_to_verify, provenance_path, strict)` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:匯入型

### VAP_ENG134_RuntimeBridgeAllInOne
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/10_Core_Runtime/VIA_Runtime_Bridge_All_in_One`(版本 1;現役 `VIA_Runtime_Bridge_All_in_One.py`)
- **功能**:無說明(候補)
- **類**:def_VIARuntimeContext
- **函式**(12):`def_ensure_supportive_root_on_sys_path()` · `def_safe_import(module_name)` · `def_load_core_modules()` · `def_bootstrap_celeritas(ctx)` · `def_bootstrap_env_manager(ctx)` · `def_bootstrap_registry(ctx)` · `def_bootstrap_ssot(ctx)` · `def_bootstrap_aegis(ctx)` · `def_bootstrap_runtime()` · `def_registry_resolve(ctx, task_name)`
- **自測**:主程式可跑

### VAP_ENG135_SupportiveRuntimeHardGateBridge
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/10_Core_Runtime/VIA_Supportive_Runtime_HardGate_Bridge`(版本 1;現役 `VIA_Supportive_Runtime_HardGate_Bridge.py`)
- **功能**:無說明(候補)
- **類**:def_ModuleGate, def_RuntimeState
- **函式**(11):`def_role_map()` · `def_now()` · `def_read_text(path_value)` · `def_write_json(path_value, payload)` · `def_count_ast(path_value)` · `def_add_supportive_to_path()` · `def_scan_module(module_name)` · `def_safe_bootstrap()` · `def_write_html(path_value, state)` · `def_main()`
- **自測**:主程式可跑

### VAP_ENG136_RegistryCoreV1
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/20_Registry_SSOT/VIA_RegistryCore_v1`(版本 1;現役 `VIA_RegistryCore_v1.py`)
- **功能**:無說明(候補)
- **類**:def_ModuleIdentity, def_ModuleRecord, def_RegistryState
- **函式**(12):`def_now_utc_iso()` · `def_ensure_output_dirs()` · `def_read_text_safe(path_value)` · `def_read_json_safe(path_value, default_value)` · `def_write_json(path_value, payload)` · `def_append_jsonl(path_value, payload)` · `def_get_file_hash_sha256(path_value)` · `def_normalize_module_name(path_value)` · `def_slugify(value)` · `def_build_short_hash(value, length_value)`
- **自測**:主程式可跑

### VAP_ENG137_SSOTUnified
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/20_Registry_SSOT/VIA_SSOT_Unified`(版本 1;現役 `VIA_SSOT_Unified.py`)
- **功能**:無說明(候補)
- **類**:_VIAStateBox, SSOT, VIAFinancialSubjectMatch
- **函式**(3):`filter_noise(rows, list_name)` · `asset_dump(source, asset_id, slot_name, lang, version)` · `asset_load(json_str)`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VeritasAegisNexus, VeritasCeleritas

### VAP_ENG138_HardGateSealEngine
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/30_HardGate_Governance/VIA_HardGate_SealEngine`(版本 1;現役 `VIA_HardGate_SealEngine.py`)
- **功能**:無說明(候補)
- **函式**(6):`load_json(path)` · `save_json(path, data)` · `check_required_outputs(required_list)` · `run_seal_engine(phase_report_path, seal_path, output_path)` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG139_PanoramaASTRuntimeInjector
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/30_HardGate_Governance/VIA_Panorama_AST_RuntimeInjector`(版本 1;現役 `VIA_Panorama_AST_RuntimeInjector.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_read_text(path_value)` · `def_write_json(path_value, payload)` · `def_write_html(path_value, rows)` · `def_analyze_python_file(file_path)` · `def_scan_project(base_root)` · `def_main()` · `via_runtime_heartbeat()` · `via_runtime_smoke()` · `via_runtime_heartbeat()`
- **CLI**:`--base-root` `--compat-shim` `--dry-run` `--execute` `--output-dir`
- **自測**:主程式可跑

### VAP_ENG140_EnvManager
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/40_Environment_Health/VIA_EnvManager`(版本 1;現役 `VIA_EnvManager.py`)
- **功能**:無說明(候補)
- **類**:def_EnvAliasRecord, def_LibProbeResult, def_EnvHealthRecord, def_EnvConflictRecord, def_InstallRequest, def_InstallDecision, def_EnvManagerState
- **函式**(12):`def_now_utc_iso()` · `def_ensure_output_dir()` · `def_read_text_safe(path_value)` · `def_read_json_safe(path_value, default_value)` · `def_write_json(path_value, payload)` · `def_append_jsonl(path_value, payload)` · `def_pick_first_existing_path(path_candidates)` · `def_get_hostname()` · `def_is_base_env_name(env_name)` · `def_is_managed_env_name(env_name)`
- **CLI**:`--format` `--python`
- **自測**:主程式可跑

### VAP_ENG141_VISInstallHealthRegistry
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/40_Environment_Health/VIS_InstallHealthRegistry`(版本 1;現役 `VIS_InstallHealthRegistry.py`)
- **功能**:def VIS_InstallHealthRegistry
- **類**:VISHealthRecord
- **函式**(8):`def_now()` · `def_python_info()` · `def_make_record(name, status, path, message, detail)` · `def_write_health_registry(output_path, records, metadata)` · `def_load_health_registry(path)` · `def_smoke()` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG142_VISVRNBrokerAliasCompatibility
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_BrokerAlias_Compatibility`(版本 1;現役 `VIS_VRN_BrokerAlias_Compatibility_v0222.py`)
- **功能**:VIS_VRN_BrokerAlias_Compatibility_v0222
- **類**:BrokerAliasResult
- **函式**(5):`def_normalize_broker_name(text)` · `def_get_broker_alias_table()` · `def_smoke_test()` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG143_VISVRNBrokerAliasExtension
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_BrokerAlias_Extension`(版本 1;現役 `VIS_VRN_BrokerAlias_Extension_v0224.py`)
- **功能**:VIS_VRN_BrokerAlias_Extension_v0224
- **類**:BrokerAliasMatch
- **函式**(5):`def_match_broker_alias(text)` · `def_get_broker_alias_extension()` · `def_smoke_test()` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG144_VISVRNBrokerAnalystAdaptersV06146
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_BrokerAnalystAdapters_v06146`(版本 1;現役 `VIS_VRN_BrokerAnalystAdapters_v06146.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_clean_text(x)` · `def_norm_text(x)` · `def_is_huanan_context(row, first_page_text)` · `def_is_huanan_memo_or_visit(row, first_page_text)` · `def_is_contact_label(x)` · `def_is_bad_analyst_name(x)` · `def_extract_huanan_email(text)` · `def_extract_huanan_email_all(text)` · `def_huanan_name_candidate_from_line(line)` · `def_extract_huanan_analyst_v06146(row, first_page_text, lines)`
- **自測**:匯入型

### VAP_ENG145_VISVRNFinancialRescueRulesV06126
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_FinancialRescueRules_v06126`(版本 1;現役 `VIS_VRN_FinancialRescueRules_v06126.py`)
- **功能**:無說明(候補)
- **函式**(7):`def_clean_text(x)` · `def_norm_key(x)` · `def_get_rescue_rules_v06126()` · `def_build_rescue_index_v06126()` · `def_match_financial_rescue_v06126(data_raw)` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:匯入型

### VAP_ENG146_VISVRNFinancialSSOT
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_FinancialSSOT`(版本 2;現役 `VIS_VRN_FinancialSSOT_v0608.py`)
- **功能**:無說明(候補)
- **函式**(4):`def_get_vrn_financial_account_ssot()` · `def_get_vrn_financial_account_alias_index()` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:匯入型

### VAP_ENG147_VISVRNHistoricalValidationPolicy
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_HistoricalValidationPolicy`(版本 1;現役 `VIS_VRN_HistoricalValidationPolicy_v0100.py`)
- **功能**:VIS_VRN_HistoricalValidationPolicy_v0100.py
- **類**:def_ValidationSource
- **函式**(12):`def_is_report_source(source_type)` · `def_is_historical_source(source_type)` · `def_get_policy()` · `def_should_use_report_as_basicinfo_value(field_name)` · `def_can_use_source_for_historical_validation(source_type)` · `def_can_use_source_for_financial_truth(source_type)` · `def_classify_validation_source(source)` · `def_validate_historical_interval_source(source_type, period_start, period_end)` · `def_validate_add_sub_source(source_type)` · `def_validate_division_source(source_type)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG148_VISVRNInputRoutePolicy
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_InputRoutePolicy`(版本 1;現役 `VIS_VRN_InputRoutePolicy_v0224.py`)
- **功能**:VIS_VRN_InputRoutePolicy_v0224
- **類**:RoutePolicyResult
- **函式**(6):`def_is_macro_theme_report(filename, ticker_signal)` · `def_is_mq_noocr(filename, text_layer)` · `def_classify_input_route(filename, text_layer, ticker_signal, current_route)` · `def_smoke_test()` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:主程式可跑

### VAP_ENG149_VISVRNNewReportCompatibilityGate
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_NewReportCompatibilityGate`(版本 1;現役 `VIS_VRN_NewReportCompatibilityGate_v01.py`)
- **功能**:VIS_VRN_NewReportCompatibilityGate_v01.py
- **類**:CompatibilityDecision
- **函式**(12):`def_clean_text(x)` · `def_norm(x)` · `def_safe_int(x, default)` · `def_load_adapter_registry(path)` · `def_detect_broker_from_filename(filename, registry)` · `def_score_report_identity(payload)` · `def_score_basicinfo(payload)` · `def_score_table_locator(payload)` · `def_score_financial_validation(payload)` · `def_decide_new_report(payload, registry)`
- **自測**:主程式可跑

### VAP_ENG150_VISVRNQ1AliasRoutePatch
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_Q1_AliasRoutePatch`(版本 1;現役 `VIS_VRN_Q1_AliasRoutePatch_v0100.py`)
- **功能**:VIS_VRN_Q1_AliasRoutePatch_v0100.py
- **函式**(4):`def_get_eligible_single_stock_alias_rows_v0100()` · `def_get_route_only_input_policy_rows_v0100()` · `def_lookup_source_policy_v0100(file_name)` · `def_self_check_v0100()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG151_VISVRNTWOfficialYFinanceV06051
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_TWOfficialYFinance_v06051`(版本 1;現役 `VIS_VRN_TWOfficialYFinance_v06051.py`)
- **功能**:無說明(候補)
- **函式**(4):`def_is_tw_ticker(ticker)` · `def_yfinance_from_market(ticker, market)` · `def_vrn_v139o_optional_import_module(module_name, module_path)` · `def_vrn_v139o_supportive_bridge_health()`
- **自測**:匯入型

### VAP_ENG152_VISVRNTableGeometryReconstructor
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_TableGeometryReconstructor`(版本 1;現役 `VIS_VRN_TableGeometryReconstructor_v0101.py`)
- **功能**:VIS_VRN_TableGeometryReconstructor_v0101
- **函式**(12):`def_normalize_space_v0101(x)` · `def_is_route_only_source_v0101(source_file, ticker)` · `def_is_period_or_header_fragment_v0101(account_raw, value_raw)` · `def_find_value_tokens_v0101(x)` · `def_clean_number_v0101(x)` · `def_value_type_v0101(x)` · `def_account_hits_v0101(text)` · `def_split_accounts_v0101(account_raw)` · `def_values_from_account_and_value_v0101(account_raw, value_raw)` · `def_canonical_account_v0101(account)`
- **CLI**:`---`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG153_VISVRNTableHeaderPeriodOriginalRestore
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/supportive modules/70_VRN_Rules/VIS_VRN_TableHeaderPeriodOriginalRestore`(版本 1;現役 `VIS_VRN_TableHeaderPeriodOriginalRestore_v0100.py`)
- **功能**:VIS_VRN_TableHeaderPeriodOriginalRestore_v0100
- **函式**(12):`def_clean_space_v0100(x)` · `def_num_tokens_v0100(x)` · `def_is_noise_line_v0100(x)` · `def_has_account_signal_v0100(x)` · `def_period_tokens_v0100(x)` · `def_forward_fill_cells_v0100(cells)` · `def_split_line_to_cells_v0100(line)` · `def_pick_header_lines_v0100(lines, row_index, up_lines)` · `def_restore_from_text_line_v0100(source_file, line_no, raw_line, context_lines, up_lines)` · `def_restore_from_pdfplumber_table_row_v0100(source_file, page, table_index, row_index, raw_cells)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG164_PsLint
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/toolkits/VIA_TurboOptimizer/ps_lint`(版本 1;現役 `ps_lint.py`)
- **功能**:Targeted PS7 static analyzer for VIA scripts.
- **函式**(1):`analyze(path)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG165_Init
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VeritasAutoPlot™ Engine Package
- **自測**:匯入型

### VAP_ENG166_Autoplot
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/autoplot`(版本 1;現役 `autoplot.py`)
- **功能**:VeritasAutoPlot™ Main Pipeline v4.1
- **類**:VeritasAutoPlot
- **CLI**:`--am` `--bl` `--co` `--gn` `--tl` `--vi`
- **自測**:匯入型

### VAP_ENG167_BubbleValuation
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/bubble_valuation`(版本 1;現役 `bubble_valuation.py`)
- **功能**:VeritasAutoPlot™ Bubble Detection & Valuation Engine
- **類**:BubbleEngine, ValuationEngine
- **自測**:匯入型

### VAP_ENG168_ChartEngine
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/chart_engine`(版本 1;現役 `chart_engine.py`)
- **功能**:VeritasAutoPlot™ Chart Engine
- **函式**(11):`chart_price_ma(df, title, show_bb, show_ma)` · `chart_candlestick(df, title)` · `chart_macd(df, title)` · `chart_rsi(df, title)` · `chart_kd(df, title)` · `chart_dual_axis(df, left_col, right_col, title)` · `chart_bubble_radar(df, threshold, title)` · `chart_valuation(df, title)` · `chart_distribution(df, title)` · `chart_drawdown(df, title)`
- **自測**:匯入型

### VAP_ENG169_ChartFlow
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/chart_flow`(版本 1;現役 `chart_flow.py`)
- **功能**:VeritasAutoPlot™ ETF Flow Chart Engine
- **函式**(5):`chart_dvol_ratio(df, title, threshold)` · `chart_flow_summary(df, title)` · `chart_etf_matrix(df, value_col, title)` · `chart_rs_flow(rs_df, target_name, base_name, title)` · `chart_price_flow_overlay(df, title)`
- **自測**:匯入型

### VAP_ENG170_DataLoader
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/data_loader`(版本 1;現役 `data_loader.py`)
- **功能**:VeritasAutoPlot™ Data Loader Engine
- **類**:VeritasDataLoader, VeritasDataProfiler
- **自測**:匯入型

### VAP_ENG171_DesignSystem
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/design_system`(版本 1;現役 `design_system.py`)
- **功能**:VeritasAutoPlot™ Design System Constants
- **自測**:匯入型

### VAP_ENG172_EventMatrix
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/event_matrix`(版本 1;現役 `event_matrix.py`)
- **功能**:VeritasAutoPlot™ Event Matrix Engine
- **函式**(1):`detect_sector(filename)`
- **自測**:匯入型

### VAP_ENG173_HtmlRenderer
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/html_renderer`(版本 1;現役 `html_renderer.py`)
- **功能**:VeritasAutoPlot™ HTML Dashboard Renderer
- **類**:VeritasHTMLRenderer
- **CLI**:`--bl`
- **自測**:匯入型

### VAP_ENG174_TaEngine
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/ta_engine`(版本 1;現役 `ta_engine.py`)
- **功能**:VeritasAutoPlot™ Technical Analysis Engine
- **類**:VeritasTAEngine, VeritasQuantEngine
- **自測**:匯入型

### VAP_ENG175_Bridge
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/vdf_bridge`(版本 1;現役 `vdf_bridge.py`)
- **功能**:VeritasAutoPlot™ VDF Bridge Module
- **類**:VDFBridge, VDFFlowEngine, VDFPanoramicVisualizer
- **CLI**:`--am` `--bl` `--co` `--gn` `--tl` `--vi`
- **自測**:匯入型

### VAP_ENG176_Connector
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/vdf_connector`(版本 1;現役 `vdf_connector.py`)
- **功能**:VeritasAutoPlot™ VDF Connector Module
- **類**:VDFNamingParser, VDFOutputScanner, GSheetConnector, MultiDBLoader, MacroBridge, VDFConnector
- **自測**:匯入型

### VAP_ENG177_Integration
- **族**:`functional modules/VAP/VeritasAutoPlot_v42_EcoSystem/engine/via_integration`(版本 1;現役 `via_integration.py`)
- **功能**:VeritasAutoPlot™ VIA Ecosystem Integration Module
- **類**:VIAAssetBridge, SSOTBridge, VPNConnector, VeritasAutoPlotVIA
- **CLI**:`--am` `--bl` `--co` `--gn` `--tl` `--vi`
- **自測**:匯入型

### VAP_ENG182_ENG005TemplateRunner
- **族**:`functional modules/VAP/engine/VAP_ENG005_TemplateRunner`(版本 1;現役 `VAP_ENG005_TemplateRunner_v0100.py`)
- **功能**:VAP_ENG005_TemplateRunner — 圖表模板跑器(批123;via-vaptpl)
- **函式**(11):`load_registry(reg_path)` · `latest_engine(pattern)` · `apply_sets(tpl, sets)` · `resolve_data_path(tpl)` · `load_frame(tpl)` · `render_eng001(tpl, out_dir)` · `render_corrheat(tpl, out_dir)` · `render_ta_overlay(tpl, out_dir)` · `render_map(tpl, out_dir)` · `render(names, sets, save_as, reg_path, out_root)`
- **CLI**:`--bands` `--base` `--db` `--left` `--left-form` `--list` `--out` `--panels` `--render` `--right` `--right-form` `--save-as`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG183_ENG006AcceptanceAudit
- **族**:`functional modules/VAP/engine/VAP_ENG006_AcceptanceAudit`(版本 1;現役 `VAP_ENG006_AcceptanceAudit_v0100.py`)
- **功能**:VAP_ENG006_AcceptanceAudit — VAP 驗收清單稽核引擎(批124;via-vapaccept)
- **函式**(11):`chk_mgr01()` · `chk_mgr02()` · `chk_vis01()` · `chk_vis02()` · `scan_iso01()` · `chk_iso01()` · `chk_iso02()` · `chk_db01()` · `chk_ui01()` · `fix_iso()`
- **CLI**:`--fix-iso` `--selftest` `--sync-db`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG184_ENG007RawWideRefresh
- **族**:`functional modules/VAP/engine/VAP_ENG007_RawWideRefresh`(版本 2;現役 `VAP_ENG007_RawWideRefresh_v0101.py`)
- **功能**:VAP_ENG007_RawWideRefresh — 宏觀寬表刷新器(批145;via-rawwide)
- **函式**(6):`fred_key_present()` · `load_db_series()` · `refresh()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG185_SpecGuard
- **族**:`functional modules/VAP/vap_spec_guard`(版本 1;現役 `vap_spec_guard_v0100.py`)
- **功能**:vap_spec_guard_v0100 — VAP 圖規鎖守衛(TOOL-083)
- **函式**(6):`newest(pattern)` · `load_pair()` · `audit(specs, snaps)` · `rich_matrix(title, rows)` · `run()` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG186_ENG010ChartLibrarySSOT
- **族**:`functional modules/VAP/engine/VAP_ENG010_ChartLibrarySSOT`(版本 1;現役 `VAP_ENG010_ChartLibrarySSOT_v0100.py`)
- **功能**:VAP_ENG010_ChartLibrarySSOT — 圖庫 SSOT 橋(批247;操作員令「收容完善整合」)
- **函式**(4):`validate_rules(doc)` · `run(intake, out)` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG187_ENG011TemplateRegistry
- **族**:`functional modules/VAP/engine/VAP_ENG011_TemplateRegistry`(版本 2;現役 `VAP_ENG011_TemplateRegistry_v0101.py`)
- **功能**:VAP_ENG011_TemplateRegistry — TPN 模板編號冊引擎(批250 立;批251 斷點清零)
- **函式**(5):`register(intake)` · `compose(tpns)` · `render(reg)` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG188_ENG012GovernedImageStore
- **族**:`functional modules/VAP/engine/VAP_ENG012_GovernedImageStore`(版本 1;現役 `VAP_ENG012_GovernedImageStore_v0100.py`)
- **功能**:VAP_ENG012_GovernedImageStore — 治理存圖道(批251;補 TPN 冊唯一斷點)
- **函式**(4):`save(src, tpn)` · `list_store()` · `selftest()` · `main()`
- **CLI**:`--file` `--selftest` `--tpn`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG189_ENG013MarketAnalytics
- **族**:`functional modules/VAP/engine/VAP_ENG013_MarketAnalytics`(版本 5;現役 `VAP_ENG013_MarketAnalytics_v0104.py`)
- **功能**:VAP_ENG013_MarketAnalytics v0103 — VAP 市場分析(9hh5to 手機代測令;批330 資料律)
- **函式**(5):`revenue_analysis(top)` · `group_analysis(top)` · `etf_list(limit)` · `etf_holdings(ids, top)` · `parse_twse_month(d)`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG190_ENG014StdDashboardTemplate
- **族**:`functional modules/VAP/engine/VAP_ENG014_StdDashboardTemplate`(版本 2;現役 `VAP_ENG014_StdDashboardTemplate_v0101.py`)
- **功能**:VAP_ENG014_StdDashboardTemplate — 標準化模板階層(批279;操作員令)
- **函式**(5):`gather()` · `render(d, po)` · `run()` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG191_ENG015SeabornStackBridge
- **族**:`functional modules/VAP/engine/VAP_ENG015_SeabornStackBridge`(版本 4;現役 `VAP_ENG015_SeabornStackBridge_v0103.py`)
- **功能**:VAP_ENG015_SeabornStackBridge v0103 — Seaborn 垂直圖組產生器 v2.3.1 橋接(批327;批329 K線疊加;批330 資料律)
- **函式**(5):`pkg_root()` · `export_stock(code)` · `export_heatmap()` · `build_stock(code, do_print)` · `build_kline(code, do_print, last_n_png)`
- **CLI**:`--axis-mode` `--cmap` `--config` `--data` `--force` `--heatmap-columns` `--heatmap-index` `--heatmap-value` `--height-ratio` `--id` `--pkgtest` `--preset`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG192_ENG016AutoplotOne
- **族**:`functional modules/VAP/engine/VAP_ENG016_AutoplotOne`(版本 1;現役 `VAP_ENG016_AutoplotOne_v0100.py`)
- **功能**:VAP_ENG016_AutoplotOne_v0100 — VAP ONE · 單檔整合引擎(Veritas AutoPlot · one file)
- **類**:file_transaction_lock
- **函式**(12):`utc_now_text()` · `run_stamp()` · `sha12(data)` · `nice_step_candidates(rough_step, family)` · `compute_locked_ticks(minimum, maximum, tick_count, include_zero, family)` · `mantissa_of(step)` · `axis_checks(ticks, data_min, data_max, family)` · `decimal_places_for_step(step, minimum)` · `format_tick_fixed(value, decimals)` · `magnitude_formatter(value)`
- **CLI**:`--axis` `--bridge-scan` `--check-spec` `--data` `--demo` `--family` `--formats` `--group` `--include-zero` `--json` `--lanes` `--list-charts`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VAP_ENG193_BaseHomeIoBuilder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_BASE_HOME_IO_20260506_210324/vap_base_home_io_builder`(版本 1;現役 `vap_base_home_io_builder.py`)
- **功能**:無說明(候補)
- **類**:def_DataAsset, def_TemplateAsset
- **函式**(12):`def_now()` · `def_read_text(path_value)` · `def_slug(value)` · `def_write_json(path_value, payload)` · `def_kind(path_value)` · `def_extract_csv(path_value)` · `def_extract_json(path_value)` · `def_extract_html(path_value)` · `def_extract_parquet(path_value)` · `def_extract_text(path_value)`
- **自測**:主程式可跑

### VAP_ENG194_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_DUCKDB_PARQUET_20260506_221932/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG195_DuckdbParquetBuilder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_DUCKDB_PARQUET_20260506_221932/vap_duckdb_parquet_builder`(版本 1;現役 `vap_duckdb_parquet_builder.py`)
- **功能**:無說明(候補)
- **類**:Asset
- **函式**(12):`now()` · `safe_text(p)` · `slug(v)` · `write_json(p, payload)` · `kind(p)` · `norm_headers(headers)` · `extract_csv(p)` · `extract_json(p)` · `extract_html(p)` · `extract_parquet(p)`
- **自測**:主程式可跑

### VAP_ENG196_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PANORAMA_MATURITY_OPT_20260507_110152/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG197_PanoramaMaturityOptimizer
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PANORAMA_MATURITY_OPT_20260507_110152/vap_panorama_maturity_optimizer`(版本 1;現役 `vap_panorama_maturity_optimizer.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_read_json(path_value, default)` · `def_safe_table(con, table_name)` · `def_table_exists(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_latest_run(pattern)` · `def_scan_versions()` · `def_scan_duckdb()`
- **自測**:主程式可跑

### VAP_ENG198_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PANORAMA_MATURITY_OPT_20260507_230210/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG199_PanoramaMaturityOptimizer
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PANORAMA_MATURITY_OPT_20260507_230210/vap_panorama_maturity_optimizer`(版本 1;現役 `vap_panorama_maturity_optimizer.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_read_json(path_value, default)` · `def_safe_table(con, table_name)` · `def_table_exists(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_latest_run(pattern)` · `def_scan_versions()` · `def_scan_duckdb()`
- **自測**:主程式可跑

### VAP_ENG200_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PROJECT_COMPLETION_20260506_224841/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG201_ProjectCompletionProbe
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PROJECT_COMPLETION_20260506_224841/vap_project_completion_probe`(版本 1;現役 `vap_project_completion_probe.py`)
- **功能**:無說明(候補)
- **函式**(8):`def_now()` · `def_read_json(path_value, default)` · `def_table_count(con, table_name)` · `def_table_exists(con, table_name)` · `def_write_query_pack()` · `def_write_launchers()` · `def_write_handover(manifest, tables)` · `main()`
- **自測**:主程式可跑

### VAP_ENG202_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PROJECT_COMPLETION_V2_20260506_225531/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG203_ProjectCompletionProbeV2
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_PROJECT_COMPLETION_V2_20260506_225531/vap_project_completion_probe_v2`(版本 1;現役 `vap_project_completion_probe_v2.py`)
- **功能**:無說明(候補)
- **函式**(9):`def_now()` · `def_read_json(path_value, default)` · `def_table_count(con, table_name)` · `def_table_exists(con, table_name)` · `def_active_warning_count(con)` · `def_write_query_pack()` · `def_write_launchers()` · `def_write_handover(manifest, tables)` · `main()`
- **自測**:主程式可跑

### VAP_ENG204_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_V8_MASTER_20260507_233550/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG205_V8MasterOrchestrator
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_V8_MASTER_20260507_233550/vap_v8_master_orchestrator`(版本 1;現役 `vap_v8_master_orchestrator.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(p, payload)` · `def_safe_table(con, table)` · `def_table_exists(con, table)` · `def_table_count(con, table)` · `def_write_table(con, table, df)` · `def_live_fetch_status()` · `def_fetch_prices()` · `def_prepare_returns(price_df)` · `def_calc_rolling_corr(norm_df)`
- **自測**:主程式可跑

### VAP_ENG206_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V4_20260506_222535/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG207_WarehouseV4Builder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V4_20260506_222535/vap_warehouse_v4_builder`(版本 1;現役 `vap_warehouse_v4_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_safe_text(path_value)` · `def_write_json(path_value, payload)` · `def_slug(value)` · `def_read_duckdb_table(table_name)` · `def_scan_files()` · `def_json_kind(path_value)` · `def_normalize_asset_registry(asset_df)` · `def_detect_components_for_html(path_value, asset_id)` · `def_build_component_registry(asset_df)`
- **自測**:主程式可跑

### VAP_ENG208_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_230931/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG209_WarehouseV5Next3Builder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_230931/vap_warehouse_v5_next3_builder`(版本 1;現役 `vap_warehouse_v5_next3_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_bool_series(df, col)` · `def_build_live_data_source_registry()` · `def_build_fetch_plan_registry(source_df)` · `def_try_fetch_yfinance(fetch_df)` · `def_build_dashboard_blueprints(asset_df, component_df, schema_df, token_df)`
- **自測**:主程式可跑

### VAP_ENG210_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_231125/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG211_WarehouseV5Next3Builder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V5_NEXT3_20260506_231125/vap_warehouse_v5_next3_builder`(版本 1;現役 `vap_warehouse_v5_next3_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_table_count(con, table_name)` · `def_write_table(con, table_name, df)` · `def_bool_series(df, col)` · `def_build_live_data_source_registry()` · `def_build_fetch_plan_registry(source_df)` · `def_try_fetch_yfinance(fetch_df)` · `def_build_dashboard_blueprints(asset_df, component_df, schema_df, token_df)`
- **自測**:主程式可跑

### VAP_ENG212_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V6_ALL_20260507_100922/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG213_WarehouseV6AllBuilder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V6_ALL_20260507_100922/vap_warehouse_v6_all_builder`(版本 1;現役 `vap_warehouse_v6_all_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_write_table(con, table_name, df)` · `def_build_live_fetch_status()` · `def_fetch_yfinance_prices()` · `def_generate_dashboard_html(blueprint_df)` · `def_build_normalized_series(price_df)` · `def_build_rolling_correlation_plan(fetch_status_df)` · `def_build_lead_lag_plan(fetch_status_df)`
- **自測**:主程式可跑

### VAP_ENG214_CheckLibs
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V7_QUANT_20260507_104041/check_libs`(版本 1;現役 `check_libs.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VAP_ENG215_WarehouseV7QuantBuilder
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_V7_QUANT_20260507_104041/vap_warehouse_v7_quant_builder`(版本 1;現役 `vap_warehouse_v7_quant_builder.py`)
- **功能**:無說明(候補)
- **函式**(12):`def_now()` · `def_write_json(path_value, payload)` · `def_safe_table(con, table_name)` · `def_write_table(con, table_name, df)` · `def_prepare_price_data(price_df)` · `def_calculate_rolling_correlation(norm_df)` · `def_calculate_lead_lag(norm_df)` · `def_build_factor_plan(fetch_status_df)` · `def_build_regime_plan()` · `def_write_query_pack()`
- **自測**:主程式可跑

### VAP_ENG216_Server
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/api/vap_server`(版本 1;現役 `vap_server.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **函式**(10):`health_check()` · `list_data_sources()` · `load_data(source, rows)` · `get_demo_data(ticker, days)` · `compute_indicators(source, indicators)` · `list_templates()` · `get_template(name)` · `save_template(name, config)` · `delete_template(name)` · `run_server(host, port)`
- **自測**:主程式可跑

### VAP_ENG217_ChartDashboard
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/charts/vap_chart_dashboard`(版本 1;現役 `vap_chart_dashboard.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPDashboard
- **自測**:匯入型

### VAP_ENG218_ChartHeatmap
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/charts/vap_chart_heatmap`(版本 1;現役 `vap_chart_heatmap.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPHeatmapChart
- **自測**:匯入型

### VAP_ENG219_ChartStack
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/charts/vap_chart_stack`(版本 1;現役 `vap_chart_stack.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPStackChart
- **自測**:匯入型

### VAP_ENG220_ChartTechnical
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/charts/vap_chart_technical`(版本 1;現役 `vap_chart_technical.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTechnicalChart
- **自測**:匯入型

### VAP_ENG221_ChartTwoaxis
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/charts/vap_chart_twoaxis`(版本 1;現役 `vap_chart_twoaxis.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTwoAxisChart
- **自測**:匯入型

### VAP_ENG222_Annotations
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_annotations`(版本 1;現役 `vap_annotations.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:EventLine, HighLowMarker, CrisisZone, VAPAnnotationEngine
- **自測**:匯入型

### VAP_ENG223_Config
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_config`(版本 1;現役 `vap_config.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPPaths, IndicatorCategory, ExportConfig, ChartDefaults
- **函式**(2):`get_price_column(df, prefer_adj)` · `resolve_ohlcv_columns(df)`
- **自測**:主程式可跑

### VAP_ENG224_DataAdapter
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_data_adapter`(版本 1;現役 `vap_data_adapter.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPDataAdapter
- **自測**:主程式可跑

### VAP_ENG225_Export
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_export`(版本 1;現役 `vap_export.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPExportEngine
- **自測**:匯入型

### VAP_ENG226_Indicators
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_indicators`(版本 1;現役 `vap_indicators.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPIndicatorEngine
- **自測**:匯入型

### VAP_ENG227_Templates
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/core/vap_templates`(版本 1;現役 `vap_templates.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:VAPTemplateManager
- **自測**:匯入型

### VAP_ENG228_Main
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/main`(版本 1;現役 `main.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **函式**(7):`via_support(name)` · `via_support_status(load_all)` · `cmd_health()` · `cmd_demo()` · `cmd_compute(args)` · `cmd_serve(args)` · `main()`
- **CLI**:`--chart` `--days` `--demo` `--health` `--indicators` `--output` `--port` `--serve` `--source` `--template` `--ticker`
- **自測**:主程式可跑

### VAP_ENG229_Layout
- **族**:`functional modules/VAP/input/SOURCE_VAP_MODULE/vap_layout`(版本 1;現役 `vap_layout.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════╗
- **類**:AnnotationBox, VAPLayoutEngine
- **函式**(2):`via_support(name)` · `via_support_status(load_all)`
- **自測**:匯入型

### VAP_ENG230_DataRuntime
- **族**:`functional modules/VAP/references/intake/VAP_v025_Complete_Package/runtime/vap_data_runtime`(版本 1;現役 `vap_data_runtime_v025.py`)
- **功能**:VeritasAutoPlot v025 local read-only data runtime and file bridge.
- **類**:RefreshResult, CatalogRuntime, JsonLineFormatter
- **函式**(12):`def_now_iso()` · `def_package_root()` · `def_canonical_json(value)` · `def_sha256_bytes(value)` · `def_sha256_text(value)` · `def_atomic_write_text(path, text)` · `def_atomic_write_json(path, value)` · `def_load_json(path, fallback)` · `def_safe_identifier(value, fallback)` · `def_json_safe(value)`
- **CLI**:`--config` `--host` `--no-browser` `--once-refresh` `--port` `--run-self-test` `--sync-connect`
- **自測**:主程式可跑

### VAP_ENG231_VdfManifestTool
- **族**:`functional modules/VAP/references/intake/VAP_v025_Complete_Package/runtime/vap_vdf_manifest_tool`(版本 1;現役 `vap_vdf_manifest_tool_v025.py`)
- **功能**:VDF handoff manifest fingerprint and validation helper for VAP v025.
- **函式**(6):`def_canonical_json(value)` · `def_connection_fingerprint(connection)` · `def_validate_connection(connection)` · `def_atomic_write(path, payload)` · `def_parse_args()` · `def_main()`
- **CLI**:`--manifest` `--seal-source`
- **自測**:主程式可跑

### VAP_ENG232_RunAllTests
- **族**:`functional modules/VAP/references/intake/VAP_v025_Complete_Package/tests/run_all_tests`(版本 1;現役 `run_all_tests_v025.py`)
- **功能**:無說明(候補)
- **函式**(6):`def_find_browser()` · `def_write_package_manifest()` · `def_run_python_suite()` · `def_run_node_suite()` · `def_browser_capability()` · `def_main()`
- **自測**:主程式可跑

### VAP_ENG233_TestVapPackageStatic
- **族**:`functional modules/VAP/references/intake/VAP_v025_Complete_Package/tests/test_vap_package_static`(版本 1;現役 `test_vap_package_static_v025.py`)
- **功能**:無說明(候補)
- **類**:IdCollector, PackageStaticTests
- **CLI**:`--run-self-test` `--sync-connect`
- **自測**:主程式可跑

### VAP_ENG234_TestVapRuntime
- **族**:`functional modules/VAP/references/intake/VAP_v025_Complete_Package/tests/test_vap_runtime`(版本 1;現役 `test_vap_runtime_v025.py`)
- **功能**:無說明(候補)
- **類**:RuntimeFixture
- **自測**:主程式可跑


## VDF · 數據鍛造(146 支)

### VDF_ENG004_MDL002YFinanceFetchingEngine
- **族**:`functional modules/VDF/VDF_MDL002_YFinanceFetchingEngine`(版本 1;現役 `VDF_MDL002_YFinanceFetchingEngine.py`)
- **功能**:================================================================================
- **類**:FileManager, DataValidator, ETFFundFlowCalculator, FinancialDataFetcher, YFinanceUniverseTool
- **函式**(9):`validate_ticker(ticker, market_group)` · `detect_tw_ticker_format(s)` · `check_and_install_dependencies()` · `print_rich_summary_matrix(tool, df_main, df_flow, df_composite)` · `main()` · `tool_run(tool)` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--etf-only` `--menu` `--no-flows` `--no-pause` `--non-etf-only`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SuperAccel_Module

### VDF_ENG005_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(2):`print_rich_summary_matrix(eng)` · `main()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG009_MDL007SSOTResolver
- **族**:`functional modules/VDF/VDF_MDL007_SSOTResolver`(版本 1;現役 `VDF_MDL007_SSOTResolver.py`)
- **功能**:================================================================================
- **類**:TickerResolver, TWSESource, TPEXSource, MOPSSource, YFinanceSource, FactSetSource, SSOTResolverEngine
- **函式**(1):`main()`
- **CLI**:`--all` `--batch` `--name` `--no-consensus` `--no-pause` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG010_MDL101OutputManager
- **族**:`functional modules/VDF/VDF_MDL101_OutputManager`(版本 1;現役 `VDF_MDL101_OutputManager.py`)
- **功能**:================================================================================
- **類**:OutputManager
- **CLI**:`--gsheet` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG013_MDL104RegistryLoader
- **族**:`functional modules/VDF/VDF_MDL104_RegistryLoader`(版本 1;現役 `VDF_MDL104_RegistryLoader.py`)
- **功能**:================================================================================
- **類**:RegistryLoader
- **函式**(1):`main()`
- **CLI**:`--dry-run` `--filter` `--no-pause` `--registry` `--schema` `--themes`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG014_MDL105CrossValidator
- **族**:`functional modules/VDF/VDF_MDL105_CrossValidator`(版本 1;現役 `VDF_MDL105_CrossValidator.py`)
- **功能**:================================================================================
- **類**:CrossValidator
- **函式**(1):`main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG019_MDL501FetchContractManager
- **族**:`functional modules/VDF/VDF_ENG019_MDL501FetchContractManager`(版本 1;現役 `VDF_ENG019_MDL501FetchContractManager.py`)
- **功能**:VDF 取數契約管理器 v0100(MDL501)— 擷取項目 增/減/查/比 一支到底
- **函式**(10):`load()` · `save(c, action)` · `index(c)` · `cmd_check()` · `cmd_list(dom, status)` · `cmd_diff(other)` · `cmd_add(dom, code, item, source, fetcher)` · `cmd_remove(code, note)` · `cmd_setstatus(code, status)` · `main(argv)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG025_MDL001TWUniverseVerify
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL001_TWUniverseVerify`(版本 1;現役 `VDF_MDL001_TWUniverseVerify_v0100R.py`)
- **功能**:================================================================================
- **類**:TWUniverseFetcher, TWUniverseVerifyEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG026_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine_v0100R.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, SentimentMacroEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG027_MDL005TWStockFilter
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL005_TWStockFilter`(版本 1;現役 `VDF_MDL005_TWStockFilter_v0100R.py`)
- **功能**:================================================================================
- **類**:StockFilterEngine
- **CLI**:`--no-pause` `--tickers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG028_MDL006FinancialModel
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL006_FinancialModel`(版本 1;現役 `VDF_MDL006_FinancialModel_v0100R.py`)
- **功能**:================================================================================
- **類**:FinancialModelEngine
- **CLI**:`--no-pause` `--tickers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG029_MDL101OutputManager
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL101_OutputManager`(版本 1;現役 `VDF_MDL101_OutputManager_v0100R.py`)
- **功能**:================================================================================
- **類**:OutputManager
- **CLI**:`--no-%s`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG030_MDL103MasterRegistry
- **族**:`functional modules/VDF/_rebuilds_superseded/VDF_MDL103_MasterRegistry`(版本 1;現役 `VDF_MDL103_MasterRegistry_v0100R.py`)
- **功能**:================================================================================
- **類**:MasterRegistryEngine
- **CLI**:`--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG032_MDL002YFinanceFetchingEngine
- **族**:`functional modules/VDF/engine/VDF_MDL002_YFinanceFetchingEngine`(版本 1;現役 `VDF_MDL002_YFinanceFetchingEngine.py`)
- **功能**:================================================================================
- **類**:FileManager, DataValidator, ETFFundFlowCalculator, FinancialDataFetcher, YFinanceUniverseTool
- **函式**(9):`validate_ticker(ticker, market_group)` · `detect_tw_ticker_format(s)` · `check_and_install_dependencies()` · `print_rich_summary_matrix(tool, df_main, df_flow, df_composite)` · `main()` · `tool_run(tool)` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--etf-only` `--menu` `--no-flows` `--no-pause` `--non-etf-only`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SuperAccel_Module

### VDF_ENG033_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/engine/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(3):`print_rich_summary_matrix(eng)` · `main()` · `interactive_menu()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG036_MDL007SSOTResolver
- **族**:`functional modules/VDF/engine/VDF_MDL007_SSOTResolver`(版本 1;現役 `VDF_MDL007_SSOTResolver.py`)
- **功能**:================================================================================
- **類**:TickerResolver, TWSESource, TPEXSource, MOPSSource, YFinanceSource, FactSetSource, SSOTResolverEngine
- **函式**(1):`main()`
- **CLI**:`--all` `--batch` `--name` `--no-consensus` `--no-pause` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG041_SectorRotationCapitalFlowEngine
- **族**:`functional modules/VDF/engine/candidates/sector_rotation_capital_flow_engine`(版本 1;現役 `sector_rotation_capital_flow_engine.py`)
- **功能**:無說明(候補)
- **類**:SectorRotationEngine
- **函式**(1):`generate_noisy_market_data(days)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher
- **族**:`functional modules/VDF/VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher`(版本 1;現役 `VDF_ENG044_MDLXXXYFinanceGlobalDataFetcher.py`)
- **功能**:🚀 簡化金融數據工具 v4.0 - 完全可用版本
- **類**:FileManager, DataValidator, FinancialDataFetcher, TaiwanFinancialTool
- **函式**(5):`check_and_install_dependencies()` · `main()` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--menu`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG045_OutputHub
- **族**:`functional modules/VDF/VDF_ENG045_OutputHub`(版本 1;現役 `VDF_ENG045_OutputHub_v0100.py`)
- **功能**:vdf_output_hub_v0100 — VDF 統一參數+全格式輸出樞紐(TOOL-058;操作員令 2026-08-18)
- **函式**(5):`load_params()` · `write_all(rows, table, formats, outdir)` · `summary(matrix)` · `selftest()` · `main()`
- **CLI**:`--formats` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG057_TradingValueBackfill
- **族**:`functional modules/VDF/engine/VDF_ENG057_TradingValueBackfill`(版本 2;現役 `VDF_ENG057_TradingValueBackfill_v0101.py`)
- **功能**:VDF_ENG057_TradingValueBackfill v0101 — 逐股成交值歷史回補(批154;via-tval)
- **函式**(7):`gate_open(env)` · `curl_json(url)` · `parse_twse_mi(js, iso)` · `parse_tpex(js, iso)` · `trading_days()` · `upsert(rows)` · `run(max_days)`
- **CLI**:`--days` `--max-time` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG058_IndustryUnifiedMap
- **族**:`functional modules/VDF/engine/VDF_ENG058_IndustryUnifiedMap`(版本 1;現役 `VDF_ENG058_IndustryUnifiedMap_v0100.py`)
- **功能**:VDF_ENG058_IndustryUnifiedMap — 雙所產業混合分類編號冊(批155;via-industry)
- **函式**(5):`rollup(code)` · `build()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG059_EstimateBands
- **族**:`functional modules/VDF/engine/VDF_ENG059_EstimateBands`(版本 1;現役 `VDF_ENG059_EstimateBands_v0100.py`)
- **功能**:VDF_ENG059_EstimateBands — 分析師預估×PE/PB band(批155;via-bands)
- **函式**(7):`gate_open(env)` · `parse_estimates(sym, d)` · `band_stats(prices, denom)` · `upsert(rows)` · `run(top_n)` · `chart(code)` · `pd_dates(px)`
- **CLI**:`--chart` `--selftest` `--status` `--top`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG060_AdjPriceLayer
- **族**:`functional modules/VDF/engine/VDF_ENG060_AdjPriceLayer`(版本 4;現役 `VDF_ENG060_AdjPriceLayer_v0103.py`)
- **功能**:VDF_ENG060_AdjPriceLayer v0103 — 調整後價格層(批178;操作員令;批346 旗標表缺 graceful;批349 原始層同式重算;批368 ① 相對門檻)
- **函式**(4):`build()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG061_FeatureStore
- **族**:`functional modules/VDF/engine/VDF_ENG061_FeatureStore`(版本 2;現役 `VDF_ENG061_FeatureStore_v0101.py`)
- **功能**:VDF_ENG061_FeatureStore v0101 — 因子庫(批188;Roadmap Phase 2;批368 ②⑥ 相對門檻)
- **函式**(4):`build()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG062_GroupFeatureLayer
- **族**:`functional modules/VDF/engine/VDF_ENG062_GroupFeatureLayer`(版本 2;現役 `VDF_ENG062_GroupFeatureLayer_v0101.py`)
- **功能**:VDF_ENG062_GroupFeatureLayer v0101(批349 快照缺=誠實 FAIL 不拋例外)— 族群聚合因子層(批193;Phase 2 續深)
- **函式**(4):`build()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG063_MonthlyRevenue
- **族**:`functional modules/VDF/engine/VDF_ENG063_MonthlyRevenue`(版本 6;現役 `VDF_ENG063_MonthlyRevenue_v0105.py`)
- **功能**:VDF_ENG063_MonthlyRevenue v0105 — 月營收分析模組(批194;操作員令)
- **函式**(2):`run_mops(net, con, ts)` · `run(codes)`
- **CLI**:`--analyze` `--groups` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG064_HistoryBackfill
- **族**:`functional modules/VDF/engine/VDF_ENG064_HistoryBackfill`(版本 12;現役 `VDF_ENG064_HistoryBackfill_v0111.py`)
- **功能**:VDF_ENG064_HistoryBackfill v0111 — 歷史回補引擎(批203 立;批212 收束;批226 自訂日期;批322 讓庫律;批353 批內平行=真用加速器)
- **類**:DbBusy
- **函式**(1):`run_range(start, end, limit)`
- **CLI**:`--batch-size` `--db` `--end` `--gap-mode` `--limit` `--max-batches` `--rebuild-ckpt` `--report` `--selftest` `--start` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG065_MDL001TWEquityEngine
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL001_TWEquityEngine`(版本 1;現役 `VDF_MDL001_TWEquityEngine.py`)
- **功能**:================================================================================
- **類**:IntelligentDependencyChecker, IntelligentModuleImporter, IndexFileManager, EquityFileManager, RealIndexFetcher, RealEquityFetcher, SmartAutoDeployController, EnhancedStockProcessor
- **函式**(10):`to_twse_yyyymmdd(dt)` · `to_twse_month(dt)` · `to_roc_slash(dt)` · `to_roc_dash(dt)` · `to_western_iso(dt)` · `get_date_range(s, e)` · `is_known_tw_holiday(dt)` · `safe_num(value)` · `print_raw_response(api_name, args, resp)` · `print_rich_summary_matrix(processor, deployment_success, processing_success)`
- **CLI**:`--equity-only` `--format=json` `--index-only` `--no-pause` `--only-reset` `--quiet` `--reset-all` `--reset-holidays` `--upgrade`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module, VeritasAegisNexus, VeritasCeleritas

### VDF_ENG066_MDL001TWUniverseVerify
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL001_TWUniverseVerify`(版本 1;現役 `VDF_MDL001_TWUniverseVerify.py`)
- **功能**:================================================================================
- **類**:TWUniverseFetcher, TWUniverseVerifier, OutputManager
- **函式**(4):`apply_ssot_regex(code)` · `run_verify(dryrun)` · `print_summary_matrix(report, twse_pass, tpex_pass, combined_rej, mgr)` · `main()`
- **CLI**:`--dryrun` `--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG067_MDL002YFinanceFetchingEngine
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL002_YFinanceFetchingEngine`(版本 1;現役 `VDF_MDL002_YFinanceFetchingEngine.py`)
- **功能**:================================================================================
- **類**:FileManager, DataValidator, ETFFundFlowCalculator, FinancialDataFetcher, YFinanceUniverseTool
- **函式**(9):`validate_ticker(ticker, market_group)` · `detect_tw_ticker_format(s)` · `check_and_install_dependencies()` · `print_rich_summary_matrix(tool, df_main, df_flow, df_composite)` · `main()` · `tool_run(tool)` · `interactive_menu()` · `view_existing_data()` · `cleanup_backups()`
- **CLI**:`--etf-only` `--menu` `--no-flows` `--no-pause` `--non-etf-only`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SuperAccel_Module

### VDF_ENG068_MDL003SentimentMacroEngine
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(3):`print_rich_summary_matrix(eng)` · `main()` · `interactive_menu()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG069_MDL004TWFullMarketEngine
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL004_TWFullMarketEngine`(版本 1;現役 `VDF_MDL004_TWFullMarketEngine.py`)
- **功能**:================================================================================
- **類**:TWSEFullMarketFetcher, TPEXFullMarketFetcher, YFHistoryBulkFetcher, YFConsensusFetcher, FactSetConsensusFetcher, SMAVolMcapCalculator, TWFullMarketEngine
- **函式**(1):`main()`
- **CLI**:`--max` `--no-consensus` `--no-history` `--no-pause` `--universe-source`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG070_MDL005TWStockFilter
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL005_TWStockFilter`(版本 1;現役 `VDF_MDL005_TWStockFilter.py`)
- **功能**:================================================================================
- **類**:YFinanceConsensusFetcher, FactSetConsensusFetcher, UpsideCalculator, UniverseLoader, OutputManager, StockFilterEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--gsheet` `--max` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet` `--no-pause` `--tickers` `--universe`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG071_MDL006FinancialModel
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL006_FinancialModel`(版本 1;現役 `VDF_MDL006_FinancialModel.py`)
- **功能**:================================================================================
- **類**:YFinanceFinancialFetcher, RatioAnalyzer, ValuationAnalyzer, BandChartBuilder, OutputManager, FinancialModelEngine
- **函式**(2):`print_rich_summary(eng)` · `main()`
- **CLI**:`--json` `--max` `--no-charts` `--no-csv` `--no-duckdb` `--no-parquet` `--no-pause` `--period` `--tickers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG072_MDL007SSOTResolver
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL007_SSOTResolver`(版本 1;現役 `VDF_MDL007_SSOTResolver.py`)
- **功能**:================================================================================
- **類**:TickerResolver, TWSESource, TPEXSource, MOPSSource, YFinanceSource, FactSetSource, SSOTResolverEngine
- **函式**(1):`main()`
- **CLI**:`--all` `--batch` `--name` `--no-consensus` `--no-pause` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG073_MDL101OutputManager
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL101_OutputManager`(版本 1;現役 `VDF_MDL101_OutputManager.py`)
- **功能**:================================================================================
- **類**:OutputManager
- **CLI**:`--gsheet` `--no-csv` `--no-duckdb` `--no-json` `--no-parquet`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG074_MDL102FormatUpgrader
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL102_FormatUpgrader`(版本 1;現役 `VDF_MDL102_FormatUpgrader.py`)
- **功能**:================================================================================
- **類**:FormatUpgrader
- **函式**(1):`main()`
- **CLI**:`--dryrun` `--modules` `--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG075_MDL103MasterRegistry
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL103_MasterRegistry`(版本 1;現役 `VDF_MDL103_MasterRegistry.py`)
- **功能**:================================================================================
- **類**:MasterRegistryEngine
- **函式**(1):`main()`
- **CLI**:`--check` `--filter` `--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG076_MDL104RegistryLoader
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL104_RegistryLoader`(版本 1;現役 `VDF_MDL104_RegistryLoader.py`)
- **功能**:================================================================================
- **類**:RegistryLoader
- **函式**(1):`main()`
- **CLI**:`--dry-run` `--filter` `--no-pause` `--registry` `--schema` `--themes`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG077_MDL105CrossValidator
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL105_CrossValidator`(版本 1;現役 `VDF_MDL105_CrossValidator.py`)
- **功能**:================================================================================
- **類**:CrossValidator
- **函式**(1):`main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG078_MDL201GenerateFullRegistry
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL201_GenerateFullRegistry`(版本 1;現役 `VDF_MDL201_GenerateFullRegistry.py`)
- **功能**:================================================================================
- **函式**(9):`extract_fred_registry()` · `extract_akshare_registry()` · `extract_yf_universe()` · `build_fred_item(via_code, meta)` · `build_akshare_item(code, meta)` · `build_yf_item(ticker, name, group, rule)` · `build_sentiment_items()` · `build_tw_universe_dynamic()` · `main()`
- **CLI**:`--no-pause` `--validate`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG079_MDL301SystemTest
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL301_SystemTest`(版本 1;現役 `VDF_MDL301_SystemTest.py`)
- **功能**:================================================================================
- **函式**(6):`check_dependencies()` · `test_output_manager()` · `test_upgrader()` · `check_module_files()` · `print_grand_summary(deps, om_test, upg_test, files)` · `main()`
- **CLI**:`--modules` `--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG080_MDL302FinalActivation
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL302_FinalActivation`(版本 1;現役 `VDF_MDL302_FinalActivation.py`)
- **功能**:================================================================================
- **函式**(9):`phase1_dependencies()` · `phase2_imports()` · `phase3_mock_data()` · `phase4_pipeline(mock_data, imports)` · `phase5_integrity(sandbox)` · `phase6_integration(sandbox)` · `phase7_edge_cases(imports)` · `print_grand_summary(deps, imports, mock_data, sandbox)` · `main()`
- **CLI**:`--modules` `--no-pause` `--quick` `--tickers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG081_MDL303RegistryActivation
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VDF/VDF_MDL303_RegistryActivation`(版本 1;現役 `VDF_MDL303_RegistryActivation.py`)
- **功能**:================================================================================
- **函式**(6):`phase1_generator()` · `phase2_validation()` · `phase3_loader()` · `phase4_crossvalidator(loader)` · `print_grand_summary(registry)` · `main()`
- **CLI**:`--validate`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG083_MDL003SentimentMacroEngine
- **族**:`functional modules/VDF/_from_vap_iso_cleanup/VDF_MDL003_SentimentMacroEngine`(版本 1;現役 `VDF_MDL003_SentimentMacroEngine.py`)
- **功能**:================================================================================
- **類**:AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher, OutputManager, SentimentMacroEngine
- **函式**(3):`print_rich_summary_matrix(eng)` · `main()` · `interactive_menu()`
- **CLI**:`--aaii` `--akshare` `--cnn` `--fred` `--gsheet` `--menu` `--no-aaii` `--no-akshare` `--no-cnn` `--no-csv` `--no-duckdb` `--no-fred`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG084_PriceFetch
- **族**:`functional modules/VDF/_vdf_engine_integration/vdf_price_fetch`(版本 1;現役 `vdf_price_fetch.py`)
- **功能**:VDF price layer (ADJ-first then regular). See VDF_Engine_Config.json.
- **函式**(4):`normalize_columns(df)` · `select_price_series(df)` · `fetch_prices(ticker, start, end, sources)` · `to_parquet(df, path)`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG085_EngineAaiiSentiment
- **族**:`functional modules/VDF/_vdf_engines/sentiment_strength/VDF_Engine_aaii_sentiment`(版本 1;現役 `VDF_Engine_aaii_sentiment.py`)
- **功能**:def VDF_Engine_aaii_sentiment
- **函式**(5):`def_find_column(columns, keywords)` · `def_clean_aaii_dataframe(raw)` · `def_fetch_aaii_from_local_csv(local_csv)` · `def_fetch_aaii_from_html(url, timeout)` · `def_fetch_aaii_sentiment(task)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG086_EngineCnnFearGreedProxy
- **族**:`functional modules/VDF/_vdf_engines/sentiment_strength/VDF_Engine_cnn_fear_greed_proxy`(版本 1;現役 `VDF_Engine_cnn_fear_greed_proxy.py`)
- **功能**:def VDF_Engine_cnn_fear_greed_proxy
- **函式**(4):`def_fetch_yfinance_close(symbol, period, interval)` · `def_fetch_price_matrix(symbols, period, interval)` · `def_pct_change(series, periods)` · `def_build_cnn_fear_greed_proxy(task)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG087_EngineSentimentStrength
- **族**:`functional modules/VDF/_vdf_engines/sentiment_strength/VDF_Engine_sentiment_strength`(版本 1;現役 `VDF_Engine_sentiment_strength.py`)
- **功能**:def VDF_Engine_sentiment_strength
- **函式**(8):`def_clip_score(value, low, high)` · `def_classify_strength(score)` · `def_calc_zscore(series, window, min_periods)` · `def_zscore_to_strength(zscore, center, scale)` · `def_rolling_percentile_score(series, window, min_periods, inverse)` · `def_normalize_percent_column(series)` · `def_calc_aaii_strength(df, z_window, min_periods)` · `def_blend_scores(score_items)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG090_ManifestFetchAdapter
- **族**:`functional modules/VDF/_vdf_system/macro_manifest_fetch_runs/RUN_20260617_001157_VDF_NEXUS_PANORAMA_3ROUND/VDF_ManifestFetchAdapter`(版本 1;現役 `VDF_ManifestFetchAdapter.py`)
- **功能**:VDF Manifest Fetch Adapter
- **函式**(11):`def_json_dump(path, obj)` · `def_sha256(path)` · `def_import_pandas()` · `def_import_requests()` · `def_module_available(name)` · `def_package_check(outdir)` · `def_audit_python_modules(vdf_base, required_json, outdir)` · `def_load_manifest(path)` · `def_flatten_manifest(manifest)` · `def_effective_start(manifest, row, policy)`
- **CLI**:`--fred-api-key-env` `--manifest` `--mode` `--network` `--no-network` `--outdir` `--required-json` `--start-policy` `--vdf-base`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG091_ENG046FetchMatrixRegistry
- **族**:`functional modules/VDF/engine/VDF_ENG046_FetchMatrixRegistry`(版本 1;現役 `VDF_ENG046_FetchMatrixRegistry.py`)
- **功能**:VDF_ENG046_FetchMatrixRegistry — VDF-390 擷取總冊機器轉錄引擎(批104)
- **函式**(8):`parse_matrix(md_path)` · `extract_active_etfs(items)` · `build_registry(md_path)` · `sync_etf_registry(roster, write)` · `check_schema()` · `run(sync)` · `selftest()` · `main()`
- **CLI**:`--selftest` `--sync-etf`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG092_ENG047USMacroDetailFetcher
- **族**:`functional modules/VDF/engine/VDF_ENG047_USMacroDetailFetcher`(版本 2;現役 `VDF_ENG047_USMacroDetailFetcher_v0101.py`)
- **功能**:VDF_ENG047_USMacroDetailFetcher — 美國經濟細目擷取引擎(批109;via-usmacro)
- **函式**(9):`load_roster(root)` · `roster_items(roster)` · `gate_status()` · `fetch_series(fred_id, start, api_key, http)` · `write_outputs(fred_id, key, rows, out_dir)` · `cmd_list()` · `cmd_fetch(start, http, env)` · `selftest()` · `main()`
- **CLI**:`--fetch` `--selftest` `--start`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG094_ENG049FiveDayFetch
- **族**:`functional modules/VDF/engine/VDF_ENG049_FiveDayFetch`(版本 1;現役 `VDF_ENG049_FiveDayFetch.py`)
- **功能**:VDF_ENG049_FiveDayFetch — 五日相關數據擷取引擎(批112;via-fetch5d)
- **函式**(7):`build_universe(root)` · `preflight(http_probe)` · `fetch_5d(tickers, fetch_fn)` · `write_run(result, meta)` · `run(plan_only, http_probe, fetch_fn, env)` · `selftest()` · `main()`
- **CLI**:`--plan` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG095_ENG050OrderFetch
- **族**:`functional modules/VDF/engine/VDF_ENG050_OrderFetch`(版本 2;現役 `VDF_ENG050_OrderFetch_v0101.py`)
- **功能**:VDF_ENG050_OrderFetch v0101 — 擷取單接單引擎(批114+批119 十域;via-order)
- **函式**(10):`load_orders(root)` · `get_order(oid, book)` · `trading_days_back(n, today)` · `preflight(lane, http)` · `fetch_twse_lane(targets, days, http)` · `fetch_yf_lane(targets, fetch_fn)` · `fetch_json_lane(targets, http)` · `fetch_yf_consensus(targets, tk_fn)` · `fetch_financials_lane(lane, http, tk_fn)` · `write_order_run(oid, payload)`
- **CLI**:`--order` `--plan` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG096_ENG051ActiveTWETFHoldings
- **族**:`functional modules/VDF/engine/VDF_ENG051_ActiveTWETF_Holdings`(版本 3;現役 `VDF_ENG051_ActiveTWETF_Holdings_v0102.py`)
- **功能**:[ 理 ] Veritas Intelligence Analytics
- **函式**(11):`def_now_taipei()` · `def_today_taipei()` · `def_dependency_status()` · `def_require_dependencies(live_fetch)` · `def_setup_logging(verbose)` · `def_build_session()` · `def_http_get_text(session, url)` · `def_guess_issuer_from_name(etf_name)` · `def_is_missing(value)` · `def_normalize_etf_ticker(value)`
- **CLI**:`--check-dependencies` `--duckdb-path` `--no-refresh-universe` `--output-dir` `--parquet-root` `--self-test` `--tickers` `--universe-csv` `--verbose` `--version`
- **自測**:主程式可跑

### VDF_ENG097_ENG052MegaFetch
- **族**:`functional modules/VDF/engine/VDF_ENG052_MegaFetch`(版本 3;現役 `VDF_ENG052_MegaFetch_v0102.py`)
- **功能**:VDF_ENG052_MegaFetch — 總擷取引擎 · 單 003 執行器(批128;via-mega)
- **函式**(10):`load_order(root)` · `derive_chip_fields(row)` · `holdings_views(rows)` · `write_parquet(rows, lane, out_root)` · `upsert_duckdb(db, table, rows, keys)` · `lane_global_yf(order, net, yf_fn, out_root)` · `lane_tw_listings(order, net, http)` · `preflight(net)` · `plan(order)` · `run(lanes_sel, env)`
- **CLI**:`--lane` `--plan` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG098_ENG053ParamEngineMap
- **族**:`functional modules/VDF/engine/VDF_ENG053_ParamEngineMap`(版本 3;現役 `VDF_ENG053_ParamEngineMap_v0102.py`)
- **功能**:VDF_ENG053_ParamEngineMap — VDF 輸入參數×引擎整合映射器(批134;via-vdf-map)
- **函式**(8):`active_engines()` · `harvest_file(path)` · `load_books()` · `derive_string_consumers(engines, tokens)` · `build_map()` · `run()` · `selftest()` · `main()`
- **CLI**:`--mode` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG099_ENG054TWDailyBackfill
- **族**:`functional modules/VDF/engine/VDF_ENG054_TWDailyBackfill`(版本 5;現役 `VDF_ENG054_TWDailyBackfill_v0104.py`)
- **功能**:VDF_ENG054_TWDailyBackfill — 台股全市場日線回補工人(批136;via-tw-backfill)
- **類**:DbBusy
- **函式**(11):`gate_open(env)` · `write_parquet(rows, stem)` · `connect_retry(path, read_only)` · `upsert_duckdb(table, rows, keys)` · `fetch_listings(net)` · `fetch_etf_listings(net)` · `load_ckpt()` · `save_ckpt(ck)` · `target_date(now)` · `last_dates()`
- **CLI**:`--full` `--limit` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG100_ENG055OmniFetch
- **族**:`functional modules/VDF/engine/VDF_ENG055_OmniFetch`(版本 12;現役 `VDF_ENG055_OmniFetch_v0111.py`)
- **功能**:VDF_ENG055_OmniFetch — 單 004 總擷取執行器(批137;via-omni)
- **函式**(7):`gate_open(env)` · `write_parquet(rows, stem)` · `upsert(db, table, rows, keys)` · `lane_listings(net)` · `lane_trading(net)` · `lane_valuation(net)` · `lane_etf_book(net)`
- **CLI**:`--date` `--export` `--from-file` `--lane` `--market` `--max-time` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG101_ENG056ChipBackfill
- **族**:`functional modules/VDF/engine/VDF_ENG056_ChipBackfill`(版本 3;現役 `VDF_ENG056_ChipBackfill_v0102.py`)
- **功能**:VDF_ENG056_ChipBackfill — 台股籌碼欄歷史回補(批140;via-chip)
- **類**:Progress
- **函式**(9):`gate_open(env)` · `curl_json(url)` · `trading_days()` · `parse_t86(d, date)` · `parse_margin_twse(d, date)` · `parse_inst_tpex(d, date)` · `parse_margin_tpex(d, date)` · `upsert(table, rows, keys)` · `write_parquet(rows, stem)`
- **CLI**:`--days` `--derive` `--max-time` `--selftest` `--status` `--workers`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG103_InputMatrix
- **族**:`functional modules/VDF/vdf_input_matrix`(版本 1;現役 `vdf_input_matrix_v0100.py`)
- **功能**:vdf_input_matrix_v0100 — VDF 整合輸入介面清單矩陣(TOOL-093,批88)
- **函式**(9):`load(path)` · `save(d, path, op, note)` · `add_item(d, sec_name, val)` · `rm_item(d, sec_name, val)` · `add_ticker(d, sec_name, val)` · `rm_ticker(d, sec_name, val)` · `restore(d, sec_name, val)` · `set_tw(d, key, val)` · `set_vrn(d, key, val)`
- **CLI**:`--add-item` `--add-ticker` `--remove-item` `--remove-ticker` `--restore` `--selftest` `--set-tw` `--set-vrn` `--show`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG105_ENG065DbImport
- **族**:`functional modules/VDF/engine/VDF_ENG065_DbImport`(版本 1;現役 `VDF_ENG065_DbImport_v0100.py`)
- **功能**:VDF_ENG065_DbImport — 資料庫 parquet 合併匯入引擎(批216;操作員令)
- **函式**(3):`run_import(folder, dbs)` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG106_ENG066GlobalUniverse
- **族**:`functional modules/VDF/engine/VDF_ENG066_GlobalUniverse`(版本 3;現役 `VDF_ENG066_GlobalUniverse_v0102.py`)
- **功能**:VDF_ENG066_GlobalUniverse v0102 — 全球宇宙擷取引擎(批226 立;批228 P3 契約對齊)
- **函式**(6):`load_roster()` · `pick_symbols(cats)` · `run(cats, start, end)` · `list_cats()` · `selftest()` · `main()`
- **CLI**:`--cats` `--end` `--list` `--selftest` `--start`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG107_ENG067ConsensusEnrichment
- **族**:`functional modules/VDF/engine/VDF_ENG067_ConsensusEnrichment`(版本 1;現役 `VDF_ENG067_ConsensusEnrichment_v0100.py`)
- **功能**:VDF_ENG067_ConsensusEnrichment — ETF 持股×共識增益橋(批243;操作員令)
- **函式**(4):`probe()` · `run()` · `selftest()` · `main()`
- **CLI**:`--asof` `--factset` `--holdings` `--output-dir` `--prices` `--selftest` `--write-mode`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG108_ENG068ETFConsensusAnalysis
- **族**:`functional modules/VDF/engine/VDF_ENG068_ETFConsensusAnalysis`(版本 5;現役 `VDF_ENG068_ETFConsensusAnalysis_v0104.py`)
- **功能**:VDF_ENG068_ETFConsensusAnalysis — 主動式 ETF×共識分析(批264;操作員令)
- **函式**(4):`analyze()` · `render(d)` · `probe()` · `run()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG109_ENG069RevenueConsensusAnalysis
- **族**:`functional modules/VDF/engine/VDF_ENG069_RevenueConsensusAnalysis`(版本 9;現役 `VDF_ENG069_RevenueConsensusAnalysis_v0108.py`)
- **功能**:VDF_ENG069_RevenueConsensusAnalysis v0108 — 台股月營收×共識分析(批517:主庫資料家優先 + 空表誠實缺料)(批519:資料在位時的自測分「程式檢」與「資料側」)(批520:(code,ym)
- **函式**(6):`resolve_db()` · `analyze()` · `render(d)` · `probe()` · `run()` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG110_ENG070GroupClassificationIndex
- **族**:`functional modules/VDF/engine/VDF_ENG070_GroupClassificationIndex`(版本 12;現役 `VDF_ENG070_GroupClassificationIndex_v0111.py`)
- **功能**:(v0110→v0111 批335「完成一切未完工作自動化」:+輪動快照成員冊輸出 export_rotation_snapshot=
- **函式**(6):`load_panel()` · `classify(px)` · `build_indices(df, gcol, min_members)` · `load_stories()` · `add_residual(px)` · `bh_q(pvals)`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG111_ENG071GroupBacktest
- **族**:`functional modules/VDF/engine/VDF_ENG071_GroupBacktest`(版本 2;現役 `VDF_ENG071_GroupBacktest_v0101.py`)
- **功能**:VDF_ENG071_GroupBacktest — 族群分類回測引擎(批315;操作員令
- **函式**(9):`risk_free()` · `ann_days(dates)` · `metrics(ret, rf, ann, bench)` · `walk_forward(ret, bench, rf, ann)` · `random_group_test(panel, size, ret_actual, rf, ann)` · `block_permutation(ret, bench, rng)` · `run(do_print)` · `render(ev, results)` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG112_ENG072StoryRotationBridge
- **族**:`functional modules/VDF/engine/VDF_ENG072_StoryRotationBridge`(版本 1;現役 `VDF_ENG072_StoryRotationBridge_v0100.py`)
- **功能**:VDF_ENG072_StoryRotationBridge v0100 — 故事族群輪動引擎 v0.5 橋接(批325)
- **函式**(6):`pkg_root()` · `load_stories()` · `export(do_print)` · `preflight(do_print)` · `run(do_print)` · `pkgtest(do_print)`
- **CLI**:`--config` `--pkgtest` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG113_ENG073DataArchitecture
- **族**:`functional modules/VDF/engine/VDF_ENG073_DataArchitecture`(版本 1;現役 `VDF_ENG073_DataArchitecture_v0100.py`)
- **功能**:VDF_ENG073_DataArchitecture — VDF 資料架構對映/盤點/最佳化計畫(批360;via-vdfarch)
- **函式**(9):`ssot_dir()` · `load_ssot()` · `inventory()` · `classify(cat, inv, ssot_cat)` · `optimize_plan(inv)` · `apply_plan(plan, do_print)` · `bridge_coverage()` · `fetch_lamps()` · `data_home()`
- **CLI**:`--go` `--open` `--optimize` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG114_ENG074FredMacroSSOT
- **族**:`functional modules/VDF/engine/VDF_ENG074_FredMacroSSOT`(版本 3;現役 `VDF_ENG074_FredMacroSSOT_v0102.py`)
- **功能**:VDF_ENG074_FredMacroSSOT v0102 — FRED 宏觀 SSOT 擷取引擎(批360/361;批362 動詞修;批363 FAIL 序列 PARK 律+status 紅冊)
- **函式**(8):`gate_open(env)` · `ssot_path()` · `load_series()` · `fred_key(interactive)` · `write_key(key)` · `progress_bar(done, total, width, spent)` · `fetch_window(net, key, sid, end, start)` · `plan_windows(freq, newest, since, cursor)`
- **CLI**:`--fred-key` `--limit` `--max-windows` `--only` `--retry-parked` `--rpm` `--selftest` `--since` `--workers`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG115_ENG075MonthlyRevenueBackfill
- **族**:`functional modules/VDF/engine/VDF_ENG075_MonthlyRevenueBackfill`(版本 3;現役 `VDF_ENG075_MonthlyRevenueBackfill_v0102.py`)
- **功能**:VDF_ENG075_MonthlyRevenueBackfill — 月營收全市場史深回補(批368;via-revfill)
- **類**:_T21Parser
- **函式**(7):`gate_open(env)` · `month_seq(since, newest)` · `url_for(mk, k, ym, host)` · `is_stub(raw)` · `fetch_hosts(net, mk, k, ym)` · `decode_page(raw)` · `parse_t21(text, ym)`
- **CLI**:`--max-months` `--pause` `--selftest` `--since` `--workers`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG116_ENG076ETFRevenueMomentum
- **族**:`functional modules/VDF/engine/VDF_ENG076_ETFRevenueMomentum`(版本 1;現役 `VDF_ENG076_ETFRevenueMomentum_v0100.py`)
- **功能**:VDF_ENG076_ETFRevenueMomentum — 主動 ETF 持股 × 月營收動能(批373;via-etfrev)
- **函式**(8):`latest_revenue_month(con)` · `compute()` · `persist(res)` · `render(res)` · `run()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG117_ENG077ActiveETFUniverse
- **族**:`functional modules/VDF/engine/VDF_ENG077_ActiveETFUniverse`(版本 1;現役 `VDF_ENG077_ActiveETFUniverse_v0100.py`)
- **功能**:VDF_ENG077_ActiveETFUniverse — 主動式 ETF 宇宙日更器(批374;via-etfuniv)
- **函式**(11):`is_active_code(code)` · `is_domestic(fund_type, name)` · `gate_open(env)` · `from_twse(net)` · `from_etf_book()` · `from_existing()` · `unify(primary, fallback, existing)` · `persist(rows, ts)` · `write_ssot_csv(rows)` · `run(args)`
- **CLI**:`--offline` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG118_ENG078ActiveETFHoldingsHistory
- **族**:`functional modules/VDF/engine/VDF_ENG078_ActiveETFHoldingsHistory`(版本 9;現役 `VDF_ENG078_ActiveETFHoldingsHistory_v0108.py`)
- **功能**:VDF_ENG078_ActiveETFHoldingsHistory — 主動 ETF 每日持股史深覆蓋器(批375;via-etfhist)
- **函式**(8):`gate_open(env)` · `load_lanes()` · `universe()` · `snapshot_dates()` · `trading_days(start, end)` · `lane_listing_date(u, net, lanes)` · `resolve_listing(u, snaps, net, ck)` · `coverage(net, ck, start, end, save)`
- **CLI**:`--apply` `--date` `--end` `--gap-mode` `--max-days` `--offline` `--report` `--selftest` `--start` `--ticker`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG119_ENG079LocalDbConsolidate
- **族**:`functional modules/VDF/engine/VDF_ENG079_LocalDbConsolidate`(版本 1;現役 `VDF_ENG079_LocalDbConsolidate_v0100.py`)
- **功能**:VDF_ENG079_LocalDbConsolidate v0100 — 本機三庫整併入正典 DuckDB 引擎(批383)
- **函式**(3):`log_event(kind, msg)` · `fingerprint(p)` · `detect(cols)`
- **CLI**:`--apply` `--assume-twse` `--db` `--db-global` `--end` `--force` `--json` `--only` `--rebuild-ckpt` `--selftest` `--src` `--start`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG120_ENG081UniverseAlign
- **族**:`functional modules/VDF/engine/VDF_ENG081_UniverseAlign`(版本 1;現役 `VDF_ENG081_UniverseAlign_v0100.py`)
- **功能**:VDF_ENG081_UniverseAlign v0100 — 台股每日交易資訊×籌碼 數量對齊與股票清單更新引擎(批390)
- **函式**(1):`log_event(kind, msg)`
- **CLI**:`--allow-latest` `--apply` `--asof` `--days` `--db` `--json` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG121_ENG082FinStatements
- **族**:`functional modules/VDF/engine/VDF_ENG082_FinStatements`(版本 1;現役 `VDF_ENG082_FinStatements_v0100.py`)
- **功能**:VDF_ENG082_FinStatements v0100 — 三大報表擷取引擎(批505;填主控台冊 vdf/fin_statements「缺席」空位)
- **函式**(9):`fetcher()` · `net()` · `gate_open()` · `aegis_session()` · `columns()` · `norm_ticker(t)` · `listings(con, limit)` · `write_rows(con, rows, cols)` · `mops_probe(code)`
- **CLI**:`--db` `--dry` `--limit` `--only` `--selftest` `--years`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG122_ENG085VatetfBridge
- **族**:`functional modules/VDF/engine/VDF_ENG085_VatetfBridge`(版本 5;現役 `VDF_ENG085_VatetfBridge_v0104.py`)
- **功能**:VDF_ENG085_VatetfBridge v0104 — VATETF 應用端正主橋(批522 工作站實錄:via-vetf 印 OK 40 筆但 adapter 其實 FileExistsError APPEND_ONLY_CONF
- **函式**(7):`family_python()` · `child_env()` · `resolve_sources(holdings, prices)` · `contract_check(cols, kind)` · `status(do_print, holdings, prices)` · `run(args, do_print, runner)` · `judge_adapter(r, after)`
- **CLI**:`--asof` `--days` `--factset` `--holdings` `--json` `--no-consensus` `--output-dir` `--prices` `--selftest` `--write-mode` `--yfinance`
- **自測**:✅ --selftest

### VDF_ENG123_ENG086QuantGuardOneBridge
- **族**:`functional modules/VDF/engine/VDF_ENG086_QuantGuardOneBridge`(版本 1;現役 `VDF_ENG086_QuantGuardOneBridge_v0100.py`)
- **功能**:VDF_ENG086 QuantGuard bridge.
- **函式**(4):`selftest()` · `status()` · `run_input(path, output)` · `main()`
- **CLI**:`--in` `--out`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VDF_ENG124_ENG087MarketListGovernance
- **族**:`functional modules/VDF/engine/VDF_ENG087_MarketListGovernance`(版本 1;現役 `VDF_ENG087_MarketListGovernance_v0100.py`)
- **功能**:VDF_ENG087 — Central market-list governance bridge.
- **函式**(1):`dedupe_market_turnover(rows)`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest

### VDF_ENG125_Init
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/__init__`(版本 1;現役 `__init__.py`)
- **功能**:台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).
- **自測**:匯入型

### VDF_ENG126_Analyze
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/analyze`(版本 1;現役 `analyze.py`)
- **功能**:analyze.py -- 三層動能分析引擎.
- **函式**(5):`compute_company_metrics(g, cfg)` · `classify_pattern(m, cfg)` · `momentum_score(m, cfg)` · `tier(m, cfg)` · `analyze(data, cfg)`
- **自測**:匯入型

### VDF_ENG127_Breakout
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/breakout`(版本 1;現役 `breakout.py`)
- **功能**:breakout.py -- 真突破偵測 (Genuine Breakout Detection).
- **函式**(4):`compute_breakout_metrics(g, cfg)` · `breakout_score(m, cfg)` · `detect(data, cfg)` · `summary(bo)`
- **自測**:匯入型

### VDF_ENG128_Classify
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/classify`(版本 1;現役 `classify.py`)
- **功能**:classify.py -- 產業分類 + 原物料/週期股全市場分流.
- **函式**(1):`tag_cyclical(df, cyclical_industries)`
- **自測**:匯入型

### VDF_ENG129_Cli
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/cli`(版本 1;現役 `cli.py`)
- **功能**:cli.py -- 命令列進入點.
- **函式**(9):`load_cfg(path)` · `cmd_fetch(cfg)` · `cmd_analyze(cfg, data)` · `cmd_report(cfg, result, data, bo)` · `cmd_run(cfg)` · `cmd_demo(cfg)` · `cmd_breakout(cfg)` · `cmd_groups(cfg)` · `cmd_selftest(cfg)`
- **CLI**:`--config`
- **自測**:主程式可跑

### VDF_ENG130_Csvio
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/csvio`(版本 1;現役 `csvio.py`)
- **功能**:csvio.py -- CSV 讀寫的單一入口 (編碼治理).
- **函式**(4):`write_encoding(cfg)` · `write(df, path, cfg)` · `read(path)` · `has_bom(path)`
- **自測**:匯入型

### VDF_ENG131_Fetch
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/fetch`(版本 1;現役 `fetch.py`)
- **功能**:fetch.py -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收.
- **函式**(3):`month_iter(months_back, ref)` · `fetch_page(session, hosts, market, year, month)` · `fetch_all(cfg, ref)`
- **自測**:匯入型

### VDF_ENG132_Groups
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/groups`(版本 1;現役 `groups.py`)
- **功能**:groups.py -- 熱門族群分類層 (VIA 族群分類 v1.1 疊加, 兩階層).
- **函式**(9):`load_groups(path, include_flagged)` · `verify_against_data(groups, data)` · `industry_coherence(groups, analysis, min_share)` · `dedupe_members(gdf)` · `group_momentum(analysis, groups, cfg, level)` · `cyclical_sector_groups(analysis)` · `order_sector_table(gt)` · `subgroups_of(group_table, groups, parent)` · `group_members_detail(analysis, groups, grp, level)`
- **自測**:匯入型

### VDF_ENG133_Intl
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/intl`(版本 1;現役 `intl.py`)
- **功能**:intl.py -- 國際產業分類對照 (GICS / yfinance / ICB).
- **函式**(7):`gics_of(industry_canon, stock_id)` · `yf_ticker(stock_id, market, industry)` · `attach(df)` · `crosswalk()` · `rollup(analysis, level, cfg)` · `unmapped(analysis)` · `audit()`
- **自測**:匯入型

### VDF_ENG134_Report
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/report`(版本 1;現役 `report.py`)
- **功能**:report.py -- 單頁 HTML 儀表板 (視覺鎖定: VIA 族群分類 v1.1 風格).
- **自測**:匯入型

### VDF_ENG135_Store
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/store`(版本 1;現役 `store.py`)
- **功能**:store.py -- 月營收累計增量資料庫 (parquet SSOT + duckdb 查詢層).
- **函式**(2):`upsert(df, cfg)` · `load(cfg, months_back)`
- **自測**:匯入型

### VDF_ENG136_Synth
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/synth`(版本 1;現役 `synth.py`)
- **功能**:synth.py -- 產生合成月營收資料, 供離線測試與 demo.
- **函式**(1):`make_synthetic(cfg, ref)`
- **自測**:匯入型

### VDF_ENG137_Taxonomy
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/taxonomy`(版本 1;現役 `taxonomy.py`)
- **功能**:taxonomy.py -- 台灣產業分類階層 SSOT (TWSE / TPEX 整合治理).
- **函式**(5):`normalize(name)` · `levels(name)` · `attach(df, col)` · `rollup(analysis, level, cfg, parent)` · `audit()`
- **自測**:匯入型

### VDF_ENG138_Tests
- **族**:`functional modules/VDF/references/intake/TWREV_v2.7_FULL_b477/twrevenue/tests`(版本 1;現役 `tests.py`)
- **功能**:tests.py -- 內建自我測試 (python -m twrevenue.cli selftest).
- **函式**(11):`t_regex()` · `t_parser()` · `t_sectors()` · `t_groups_ssot()` · `t_groups_two_level()` · `t_groups_parent_dedupe()` · `t_store()` · `t_duckdb()` · `t_url()` · `t_formula()`
- **自測**:匯入型

### VDF_ENG139_TestVdfTwMonthlyRevenueCrossGroupPhase
- **族**:`functional modules/VDF/references/intake/VDF_TW_MonthlyRevenue_CrossGroupPhase_v030_b481/test_vdf_tw_monthly_revenue_cross_group_phase`(版本 1;現役 `test_vdf_tw_monthly_revenue_cross_group_phase_v030.py`)
- **功能**:無說明(候補)
- **類**:TestVDFMonthlyRevenueCrossGroupPhaseV030
- **函式**(1):`def_sha256(path)`
- **自測**:主程式可跑

### VDF_ENG140_TwMonthlyRevenueCrossGroupPhaseEngine
- **族**:`functional modules/VDF/references/intake/VDF_TW_MonthlyRevenue_CrossGroupPhase_v030_b481/vdf_tw_monthly_revenue_cross_group_phase_engine`(版本 1;現役 `vdf_tw_monthly_revenue_cross_group_phase_engine_v030.py`)
- **功能**:無說明(候補)
- **類**:EngineConfig
- **函式**(12):`def_make_run_id()` · `def_utc_now_iso()` · `def_setup_logging(level)` · `def_json_default(value)` · `def_sha256_file(path, chunk_size)` · `def_safe_sql_identifier(value)` · `def_normalize_label(value)` · `def_first_existing_path(candidates)` · `def_month_delta(later, earlier)` · `def_streak_boolean(values)`
- **CLI**:`---` `--backup-before-write` `--company-master` `--end-period` `--fetch-latest` `--group-map` `--incremental` `--input` `--log-level` `--output-dir` `--require-duckdb` `--require-parquet`
- **自測**:主程式可跑

### VDF_ENG141_VETFConsensusEnrichmentAdapter
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/01_ENGINES/Consensus_Enrichment_Adapter/VETF_ConsensusEnrichment_Adapter`(版本 1;現役 `VETF_ConsensusEnrichment_Adapter_v001.py`)
- **功能**:VETF Consensus Enrichment Adapter v001
- **函式**(12):`utc_now_iso()` · `normalize_field_name(value)` · `clean_text(value)` · `to_float(value)` · `to_int(value)` · `round_number(value)` · `parse_date(value)` · `format_date(value)` · `canonicalize_record(record, aliases)` · `normalize_ticker(value, exchange)`
- **CLI**:`--acceptance-file` `--asof` `--authorization-file` `--factset` `--holdings` `--output-dir` `--prices` `--write-mode` `--yfinance`
- **自測**:主程式可跑

### VDF_ENG142_TestVetfConsensusEnrichment
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/01_ENGINES/Consensus_Enrichment_Adapter/test_vetf_consensus_enrichment`(版本 1;現役 `test_vetf_consensus_enrichment_v001.py`)
- **功能**:無說明(候補)
- **類**:ConsensusEnrichmentTests
- **自測**:主程式可跑

### VDF_ENG143_CNYESFactSetYFinanceConsensusFusionEngine
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/01_ENGINES/Legacy_Consensus_Engines/VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine`(版本 1;現役 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py`)
- **功能**:VIA · CNYES/FactSet × YFinance Consensus Fusion Engine · v2.0.0
- **函式**(12):`def_import_libraries()` · `def_runtime_dependency_report(live_mode)` · `def_assert_runtime_dependencies(live_mode)` · `def_now_utc()` · `def_now_utc_iso()` · `def_format_date(value)` · `def_epoch_to_date(value)` · `def_safe_float(value)` · `def_safe_int(value)` · `def_round(value, digits)`
- **CLI**:`--allow-missing-duckdb` `--codes` `--fixture` `--force-refresh` `--no-resume` `--output-dir` `--preflight-only` `--skip-unit-tests`
- **自測**:主程式可跑

### VDF_ENG144_FactSetYFinanceConsensusMatrixEngine
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/01_ENGINES/Legacy_Consensus_Engines/VIA_FactSet_YFinance_Consensus_Matrix_Engine`(版本 1;現役 `VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0111.py`)
- **功能**:VIA · FactSet × YFinance Consensus Matrix Engine · v1.4.0
- **函式**(12):`def_import_libraries()` · `def_now_utc()` · `def_now_utc_iso()` · `def_format_date(value)` · `def_epoch_to_date(value)` · `def_safe_float(value)` · `def_safe_int(value)` · `def_round(value, digits)` · `def_ratio(numerator, denominator)` · `def_sha256_bytes(data)`
- **CLI**:`--codes` `--fixture` `--output-dir` `--skip-unit-tests`
- **自測**:主程式可跑

### VDF_ENG145_TestVetfConsensusEnrichment
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/04_TESTS/test_vetf_consensus_enrichment`(版本 1;現役 `test_vetf_consensus_enrichment_v001.py`)
- **功能**:無說明(候補)
- **類**:ConsensusEnrichmentTests
- **自測**:主程式可跑

### VDF_ENG146_BuildFinalSeal
- **族**:`functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/tools/build_final_seal`(版本 1;現役 `build_final_seal.py`)
- **功能**:無說明(候補)
- **函式**(9):`sha256_file(path)` · `iter_payload_files()` · `build_manifest(files)` · `write_manifest(manifest)` · `write_checksums(files)` · `build_zip()` · `validate_zip(expected_file_count)` · `write_zip_checksum(zip_report)` · `main()`
- **自測**:主程式可跑

### VDF_ENG147_AkshareFetcher
- **族**:`functional modules/VDF/references/intake/VIA_AKShare_VAKE_b367/VDF_AkshareFetcher`(版本 1;現役 `VDF_AkshareFetcher.py`)
- **功能**:VDF_AkshareFetcher.py  —  VIA / VDF (VeritasDataForge) AKShare Super Fetcher  (VAKE v0200, single-file build)
- **類**:_LockedCon, Store, _Batch, Handler
- **函式**(7):`ensure_dirs()` · `stamp()` · `now_iso()` · `log(msg, level, run_id)` · `write_json(path, obj)` · `read_json(path, default)` · `parse_tables(lines)`
- **CLI**:`--fns` `--min-parts` `--mode` `--no-open` `--offline` `--open` `--port` `--refresh` `--refresh-docs` `--selection` `--start` `--workers`
- **自測**:主程式可跑

### VDF_ENG148_ActiveTWETFDailyHoldingsEngineV0101DuckDB
- **族**:`functional modules/VDF/references/intake/VIA_ActiveTWETF_DailyHoldings_Engine_v0101_DuckDB`(版本 1;現役 `VIA_ActiveTWETF_DailyHoldings_Engine_v0101_DuckDB.py`)
- **功能**:[ 理 ] Veritas Intelligence Analytics
- **函式**(12):`def_now_taipei()` · `def_today_taipei()` · `def_dependency_status()` · `def_require_dependencies(live_fetch)` · `def_setup_logging(verbose)` · `def_build_session()` · `def_http_get_text(session, url)` · `def_guess_issuer_from_name(etf_name)` · `def_is_missing(value)` · `def_normalize_etf_ticker(value)`
- **CLI**:`--check-dependencies` `--duckdb-path` `--no-refresh-universe` `--output-dir` `--parquet-root` `--self-test` `--tickers` `--universe-csv` `--verbose` `--version`
- **自測**:主程式可跑

### VDF_ENG149_FinMindTWFlowEngine
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/VIA_FinMind_TW_Flow_Engine`(版本 1;現役 `VIA_FinMind_TW_Flow_Engine.py`)
- **功能**:VIA 官方免費來源優先、FinMind 補足的台股籌碼擷取引擎。
- **函式**(12):`utc_now_iso()` · `parse_iso_date(value)` · `format_iso_date(value)` · `resolve_end_date(value)` · `clamp_start_date(dataset, requested_start)` · `normalize_ticker(raw_value)` · `read_tickers(ticker_file, ticker_limit)` · `configure_enabled_datasets(selection)` · `prompt_api_token()` · `resolve_supportive_path(configured_path, fallback_name)`
- **CLI**:`--aegis-path` `--branch-mode` `--celeritas-path` `--datasets` `--end-date` `--latest-only` `--output-root` `--plan-only` `--range-batch-mode` `--source-mode` `--start-date` `--ticker-file`
- **自測**:主程式可跑 · **整合邊**:VIA_TW_Official_Data_Adapter

### VDF_ENG150_TWBranchCapitalCircleEngine
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/VIA_TW_Branch_Capital_Circle_Engine`(版本 1;現役 `VIA_TW_Branch_Capital_Circle_Engine.py`)
- **功能**:VIA 台股分點資金管理圈與大戶行為日資料判定引擎。
- **類**:UnionFind
- **函式**(12):`utc_now_iso()` · `require_duckdb()` · `quote_identifier(identifier)` · `normalize_ticker(value)` · `safe_float(value, default)` · `safe_int(value, default)` · `sign(value, tolerance)` · `clamp(value, low, high)` · `safe_ratio(numerator, denominator, default)` · `mean(values, default)`
- **CLI**:`--duckdb` `--end-date` `--group-map` `--output-root`
- **自測**:主程式可跑

### VDF_ENG151_TWOfficialDataAdapter
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/VIA_TW_Official_Data_Adapter`(版本 1;現役 `VIA_TW_Official_Data_Adapter.py`)
- **功能**:TWSE、TPEX、TDCC 免費官方資料介面。
- **類**:OfficialSourceError
- **函式**(12):`def_utc_now_iso()` · `def_clean_text(value)` · `def_normalize_key(value)` · `def_index_row(row)` · `def_get_any(row, aliases, default)` · `def_number_text(value)` · `def_to_int(value, default)` · `def_to_float(value, default)` · `def_normalize_stock_id(value)` · `def_normalize_date(value)`
- **CLI**:`---`
- **自測**:匯入型

### VDF_ENG152_VeritasAegisNexus
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/VeritasAegisNexus`(版本 1;現役 `VeritasAegisNexus.py`)
- **功能**:無說明(候補)
- **類**:_VIAStateBox, _AegisLazyModule, LibraryInfo, LibraryRegistry, UserAgentRotator, HeadersBuilder, ProxyInfo, ProxyManager, ExponentialBackoff, CircuitBreakerOpen, CircuitBreaker, HttpConfig
- **函式**(5):`vc_log()` · `vc_accelerate()` · `va_guard()` · `va_validate()` · `VIA_EXTERNAL_GATEWAY_BLOCKED(tag, default)`
- **CLI**:`--disable-gpu` `--no-sandbox`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SafeFix_PathRegistry, VIA_SuperAccel_Module, VeritasAegisNexus

### VDF_ENG153_VeritasCeleritas
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/VeritasCeleritas`(版本 1;現役 `VeritasCeleritas.py`)
- **功能**:無說明(候補)
- **類**:_VIAStateBox, _LazyModule, _LazyAttr, GCTuner, MemoryPool, _LazyBackends, LRUCache, TTLCache, AutotuneCache, CacheManager, CompressionEngine, HashEngine
- **函式**(5):`vc_log()` · `vc_accelerate()` · `va_guard()` · `va_validate()` · `VIA_EXTERNAL_GATEWAY_BLOCKED(tag, default)`
- **自測**:主程式可跑

### VDF_ENG154_TestCapitalCircle
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/tests/test_capital_circle`(版本 1;現役 `test_capital_circle.py`)
- **功能**:無說明(候補)
- **類**:CapitalCirclePureFunctionTests
- **自測**:主程式可跑

### VDF_ENG155_TestEngine
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:EngineTests
- **CLI**:`--aegis-path` `--celeritas-path`
- **自測**:主程式可跑

### VDF_ENG156_TestOfficialAdapter
- **族**:`functional modules/VDF/references/intake/VIA_Hybrid_TW_Flow_Engine_v1.5.0_b245/FinMind_TW_Flow_Engine/tests/test_official_adapter`(版本 1;現役 `test_official_adapter.py`)
- **功能**:無說明(候補)
- **類**:OfficialAdapterTests
- **自測**:主程式可跑

### VDF_ENG157_TwUsCrossMarketRisk
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/examples/tw_us_cross_market_risk`(版本 1;現役 `tw_us_cross_market_risk.py`)
- **功能**:Complete Taiwan/US cross-market alignment and risk-metric example.
- **函式**(5):`load_confirmed_market_prices(path, market_code, ticker)` · `align_taiwan_signal_to_us_close(taiwan, us)` · `calculate_target_risk_and_features(target_ohlcv, aligned_market)` · `build_target_ohlcv(taiwan_source, target_ticker)` · `main()`
- **CLI**:`--output-dir` `--tw-parquet` `--tw-ticker` `--us-parquet` `--us-ticker`
- **自測**:主程式可跑

### VDF_ENG158_VeritasAegisNexus
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/mounts/VeritasAegisNexus`(版本 1;現役 `VeritasAegisNexus.py`)
- **功能**:無說明(候補)
- **類**:_VIAStateBox, _AegisLazyModule, LibraryInfo, LibraryRegistry, UserAgentRotator, HeadersBuilder, ProxyInfo, ProxyManager, ExponentialBackoff, CircuitBreakerOpen, CircuitBreaker, HttpConfig
- **函式**(5):`vc_log()` · `vc_accelerate()` · `va_guard()` · `va_validate()` · `VIA_EXTERNAL_GATEWAY_BLOCKED(tag, default)`
- **CLI**:`--disable-gpu` `--no-sandbox`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SafeFix_PathRegistry, VIA_SuperAccel_Module, VeritasAegisNexus

### VDF_ENG159_VeritasCeleritas
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/mounts/VeritasCeleritas`(版本 1;現役 `VeritasCeleritas.py`)
- **功能**:無說明(候補)
- **類**:_VIAStateBox, _LazyModule, _LazyAttr, GCTuner, MemoryPool, _LazyBackends, LRUCache, TTLCache, AutotuneCache, CacheManager, CompressionEngine, HashEngine
- **函式**(5):`vc_log()` · `vc_accelerate()` · `va_guard()` · `va_validate()` · `VIA_EXTERNAL_GATEWAY_BLOCKED(tag, default)`
- **自測**:主程式可跑

### VDF_ENG160_Init
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VDF_ENG161_Core
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/core`(版本 1;現役 `core.py`)
- **功能**:Local-first quantitative and technical-analysis engine built on Polars.
- **類**:ParameterSpec, EngineConfig
- **函式**(6):`encode_parameters(config, include_unregistered)` · `render_parameter_text(config, include_pros_cons)` · `benchmark_catalog_table()` · `encode_category_label(category_code, language)` · `validate_input_schema(df, require_ohlcv, require_turnover)` · `load_data(source, query, connection, fetcher, fetcher_kwargs)`
- **自測**:匯入型

### VDF_ENG162_Governance
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/governance`(版本 1;現役 `governance.py`)
- **功能**:Central SSOT governance for the adjusted-price and ex-day-trade engine.
- **類**:MarketPolicy, ParameterPolicy
- **函式**(8):`ssot_manifest()` · `validate_governance_frame(df, require_price, require_non_day_trade_volume)` · `prepare_non_day_trade_activity(df, volume_col, day_trade_volume_col, turnover_col, day_trade_turnover_col)` · `normalize_market_timestamp(df, timestamp_col, market_col)` · `align_confirmed_closes(prices, left_market, right_market, left_date_col, right_date_col)` · `policy_table()` · `factor_table()` · `logic_table()`
- **自測**:匯入型

### VDF_ENG163_Replay
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/replay`(版本 1;現役 `replay.py`)
- **功能**:Integrated point-in-time store, deterministic replay, and anti-lookahead guards.
- **類**:ReplayConfig, ReplaySession, ReplayManifest, ReplayResult, PointInTimeStore, PointInTimeReader, _DatabasePointInTimeStore, DuckDBPointInTimeStore, PostgresPointInTimeStore, DeterministicReplay
- **函式**(4):`stable_frame_hash(frame)` · `assert_no_future_rows(frame, cutoff_utc, timestamp_col)` · `assert_future_append_invariant(before, after, cutoff_utc, key_columns)` · `build_replay_sessions(calendar, market_code, start, end, execution_lag_sessions)`
- **自測**:匯入型

### VDF_ENG164_Risk
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/risk`(版本 1;現役 `risk.py`)
- **功能**:Rolling risk metrics with explicit annualisation and tail-loss policies.
- **類**:RiskConfig
- **函式**(3):`encode_risk_parameters(config)` · `calculate_risk_metrics(df, config, return_col, ticker_col, date_col)` · `summarize_risk_metrics(df, config, return_col, ticker_col)`
- **自測**:匯入型

### VDF_ENG165_Statistics
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/quant_engine/statistics`(版本 1;現役 `statistics.py`)
- **功能**:Rolling statistical structure metrics.
- **函式**(2):`rolling_statistical_features(df, windows, return_col, value_col, volume_col)` · `rolling_r2(df, x_col, y_col, window, min_samples)`
- **自測**:匯入型

### VDF_ENG166_CalcStress
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/scripts/_calc_stress`(版本 1;現役 `_calc_stress.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VDF_ENG167_ExportSsot
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/scripts/export_ssot`(版本 1;現役 `export_ssot.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VDF_ENG168_RunBacktestWithDuckdb
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/scripts/run_backtest_with_duckdb`(版本 1;現役 `run_backtest_with_duckdb.py`)
- **功能**:Run a point-in-time DuckDB backtest with a versioned factor composite.
- **函式**(6):`parse_factor_weights(value)` · `load_revisions(store, revision_parquet)` · `build_strategy_returns(decisions, ticker, long_threshold, short_threshold)` · `run_duckdb_backtest(db_path, revision_parquet, calendar_parquet, target_ticker, factor_weights)` · `load_revisions_into_store(store, revision_parquet)` · `main()`
- **CLI**:`--calendar-parquet` `--db-path` `--end-date` `--factor-weights` `--long-threshold` `--output-dir` `--revision-parquet` `--short-threshold` `--skip-load` `--start-date` `--target-ticker`
- **自測**:主程式可跑

### VDF_ENG169_TestCore
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/tests/test_core`(版本 1;現役 `test_core.py`)
- **功能**:無說明(候補)
- **函式**(12):`prices(n)` · `test_config_windows_are_strict()` · `test_technical_indicators_are_polars_only_and_have_expected_columns()` · `test_analysis_rejects_raw_volume_and_uses_only_ex_day_trade_volume()` · `test_feature_matrix_is_cross_quadrant_and_labels_are_explicit()` · `test_feature_matrix_can_join_benchmark_features()` · `test_risk_and_statistical_modules_are_independently_usable()` · `test_cross_market_asof_uses_last_confirmed_close_not_same_calendar_date()` · `test_market_timestamp_normalization_uses_iana_timezones()` · `test_central_ssot_exposes_policy_logic_and_factor_libraries()`
- **自測**:匯入型

### VDF_ENG170_TestDuckdbBacktest
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/tests/test_duckdb_backtest`(版本 1;現役 `test_duckdb_backtest.py`)
- **功能**:無說明(候補)
- **函式**(2):`test_duckdb_cli_runs_pit_factor_composite_backtest(tmp_path)` · `test_duckdb_cli_entrypoint_writes_summary(tmp_path)`
- **CLI**:`--calendar-parquet` `--db-path` `--factor-weights` `--output-dir` `--revision-parquet` `--target-ticker`
- **自測**:匯入型

### VDF_ENG171_TestExample
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/tests/test_example`(版本 1;現役 `test_example.py`)
- **功能**:無說明(候補)
- **函式**(1):`test_complete_tw_us_example_pipeline(tmp_path)`
- **自測**:匯入型

### VDF_ENG172_TestQuantguardRegression
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/tests/test_quantguard_regression`(版本 1;現役 `test_quantguard_regression.py`)
- **功能**:無說明(候補)
- **函式**(6):`fixture()` · `test_via_quantguard_sharpe_and_max_drawdown_golden_values()` · `test_via_quantguard_technical_indicator_golden_values()` · `test_via_quantguard_factor_outputs_golden_values()` · `test_via_quantguard_factor_composite_fails_closed_on_missing_factor()` · `test_via_quantguard_stress_scenarios(scenario)`
- **自測**:匯入型

### VDF_ENG173_TestReplay
- **族**:`functional modules/VDF/references/intake/VIA_QuantGuard_v20260916/tests/test_replay`(版本 1;現役 `test_replay.py`)
- **功能**:無說明(候補)
- **函式**(12):`ts(day, hour)` · `revision_frame(days)` · `test_confirmed_only_hides_t_plus_2_revision_until_available()` · `test_late_us_close_is_not_visible_to_same_day_taiwan_cutoff()` · `test_initial_release_can_show_provisional_but_confirmed_only_cannot()` · `test_future_append_invariance_and_future_row_guard()` · `test_stable_hash_is_independent_of_row_order()` · `test_replay_sessions_use_next_open_for_execution()` · `test_deterministic_replay_emits_manifest_and_only_current_session(tmp_path)` · `test_store_rejects_duplicate_revision_versions()`
- **自測**:匯入型

### VDF_ENG174_Api
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_api`(版本 1;現役 `vdf_api.py`)
- **功能**:VDF API server.
- **類**:RunState, _BufferLogHandler, VDFRequestHandler
- **函式**(2):`start_run(req, sys_mod)` · `main(host, port)`
- **CLI**:`--host` `--port`
- **自測**:主程式可跑

### VDF_ENG175_Bridge
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_bridge`(版本 1;現役 `vdf_bridge.py`)
- **功能**:Bridge layer for VDF <-> Supportive Modules.
- **類**:BridgeContext, _StdlibHttp
- **函式**(8):`get_bridge()` · `http_get_json(url, params, timeout)` · `accelerated_concat(frames, prefer)` · `accelerated_drop_duplicates(frame, subset)` · `thread_budget(mode)` · `registry_record(module_name, version, role, extra)` · `ssot_extract(rule, text)` · `env_health_check()`
- **自測**:匯入型 · **整合邊**:VIA_EnvManager, VIA_Panorama_AST_RuntimeInjector, VIA_RegistryCore_v1, VIA_Runtime_Bridge_All_in_One, VIA_SSOT_Unified, VeritasAegisNexus

### VDF_ENG176_Core
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_core`(版本 1;現役 `vdf_core.py`)
- **功能**:VDF Core (v2).
- **類**:CategorySpec, FetchMatrix, ParquetStore, FetcherRegistry, VDFRunner
- **函式**(7):`register_all_fetchers()` · `mirror_to_duckdb(output_dir, db_filename, table_prefix)` · `duckdb_query(output_dir, sql, db_filename)` · `generate_matrix_views(matrix_path)` · `parse_date_arg(s, default_today)` · `build_arg_parser()` · `main(argv)`
- **CLI**:`--category` `--end` `--fred-key` `--full-refresh` `--limit` `--matrix` `--mode` `--output-dir` `--output-format` `--prod-paths` `--skip-chips` `--start`
- **自測**:主程式可跑

### VDF_ENG177_FetchersConsensus
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_consensus`(版本 1;現役 `vdf_fetchers_consensus.py`)
- **功能**:vdf_fetchers_consensus.py — TW Stock YFinance + FactSet Consensus
- **函式**(6):`tw_to_yfinance_candidates(tw)` · `fetch_yfinance_one(tw_ticker, yf_ticker)` · `parse_target_block(text)` · `parse_rating_block(text)` · `parse_eps_block(text)` · `fetch_cnyes_consensus(tw_ticker)`
- **自測**:主程式可跑

### VDF_ENG178_FetchersDerived
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_derived`(版本 1;現役 `vdf_fetchers_derived.py`)
- **功能**:vdf_fetchers_derived.py — Derived macro models
- **函式**(7):`compute_fed_policy_stance(data)` · `compute_liquidity_impulse(data)` · `compute_usd_policy_diff(data)` · `compute_usd_yield_diff_2y(data)` · `compute_usd_risk_factor(data)` · `compute_usd_composite(policy_diff, yield_diff_2y, liquidity_impulse, risk_factor)` · `compute_yield_curve_inversion(data)`
- **自測**:主程式可跑

### VDF_ENG179_FetchersEtfHoldings
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_etf_holdings`(版本 1;現役 `vdf_fetchers_etf_holdings.py`)
- **功能**:vdf_fetchers_etf_holdings.py — Taiwan Active ETF daily holdings (v4 production)
- **函式**(9):`http_get(url, headers)` · `http_get_json(url, headers)` · `empty_holding_row(etf_ticker, date_str)` · `parse_holdings_table(html, etf_ticker, source_tag)` · `fetch_uni_holdings(etf_ticker)` · `fetch_nom_holdings(etf_ticker)` · `fetch_cap_holdings(etf_ticker)` · `fetch_ctbc_holdings(etf_ticker)` · `fetch_agi_holdings(etf_ticker)`
- **自測**:主程式可跑

### VDF_ENG180_FetchersFed
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_fed`(版本 1;現役 `vdf_fetchers_fed.py`)
- **功能**:vdf_fetchers_fed.py — Federal Reserve FOMC scraper
- **函式**(6):`fetch_fomc_press_feed()` · `filter_fomc_decisions(items)` · `get_recent_sep_dates()` · `fetch_sep_table(date_str)` · `score_policy_tone(text)` · `fetch_fed_full_snapshot()`
- **自測**:主程式可跑

### VDF_ENG181_FetchersFinancials
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_financials`(版本 1;現役 `vdf_fetchers_financials.py`)
- **功能**:Public entry:
- **函式**(1):`fetch_stock_financials(spec, ctx)`
- **自測**:匯入型

### VDF_ENG182_FetchersFiscal
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_fiscal`(版本 1;現役 `vdf_fetchers_fiscal.py`)
- **功能**:vdf_fetchers_fiscal.py — Treasury FiscalData API fetcher
- **函式**(9):`fetch_paged(endpoint, fields, filter_str, sort, page_size)` · `fetch_dts_deposits_withdrawals(start, days)` · `fetch_dts_operating_cash_balance(start, days)` · `fetch_dts_public_debt(start, days)` · `fetch_mts_table_1(start_year)` · `fetch_mts_table_4(start_year)` · `fetch_mts_table_5(start_year)` · `fetch_fiscal_all(start_date, days)` · `standardize_dts_for_ssot(raw_records)`
- **自測**:主程式可跑

### VDF_ENG183_FetchersMacro
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_macro`(版本 1;現役 `vdf_fetchers_macro.py`)
- **功能**:Public entry points:
- **函式**(3):`fetch_macro_fred(spec, ctx)` · `fetch_sentiment(spec, ctx)` · `fetch_shipping(spec, ctx)`
- **自測**:匯入型

### VDF_ENG184_FetchersMarket
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_market`(版本 1;現役 `vdf_fetchers_market.py`)
- **功能**:Public entry points exposed by this module:
- **類**:_Http
- **函式**(1):`fetch_yfinance_prices(spec, ctx)`
- **自測**:匯入型

### VDF_ENG185_FetchersSentiment
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_sentiment`(版本 1;現役 `vdf_fetchers_sentiment.py`)
- **功能**:vdf_fetchers_sentiment.py — Market sentiment indices
- **函式**(7):`fetch_aaii(url)` · `parse_aaii_xls(data, max_rows)` · `standardize_aaii_for_ssot(records)` · `fetch_cnn_fear_greed(start_date)` · `parse_cnn_fear_greed(raw)` · `standardize_cnn_for_ssot(records)` · `fetch_sentiment_all()`
- **自測**:主程式可跑

### VDF_ENG186_FetchersTdcc
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_fetchers_tdcc`(版本 1;現役 `vdf_fetchers_tdcc.py`)
- **功能**:vdf_fetchers_tdcc.py — 台灣集中保管結算所 (TDCC) data fetcher
- **函式**(5):`fetch_distribution_raw(ticker)` · `standardize_distribution_for_ssot(rows)` · `fetch_etf_beneficiary_count(etf_ticker)` · `compute_retail_concentration(distribution_rows)` · `compute_beneficiary_delta(yesterday, today)`
- **自測**:主程式可跑

### VDF_ENG187_SupportiveBridge
- **族**:`functional modules/VDF/references/intake/VIA_VDF_SSOT_b360/vdf_supportive_bridge`(版本 1;現役 `vdf_supportive_bridge.py`)
- **功能**:vdf_supportive_bridge.py — Integration shim for VeritasAegisNexus + VeritasCeleritas
- **函式**(10):`http_get(url, headers, timeout)` · `http_get_json(url, headers, timeout)` · `http_get_bytes(url, headers, timeout)` · `parallel_map(fn, items, max_workers)` · `cache_get(key)` · `cache_set(key, value, ttl_sec)` · `system_under_pressure()` · `wait_for_resources(timeout_sec)` · `env_health()` · `detect_python()`
- **自測**:主程式可跑 · **整合邊**:VIA_EnvManager, VeritasAegisNexus, VeritasCeleritas

### VDF_ENG188_FetchersFinancials
- **族**:`functional modules/VDF/references/intake/vdf_fetchers_financials_b504/vdf_fetchers_financials`(版本 1;現役 `vdf_fetchers_financials.py`)
- **功能**:Public entry:
- **函式**(1):`fetch_stock_financials(spec, ctx)`
- **自測**:匯入型

### VDF_ENG189_InjectAccelNetBridges
- **族**:`functional modules/VDF/tools/VDF_InjectAccelNetBridges`(版本 1;現役 `VDF_InjectAccelNetBridges_v0104.py`)
- **功能**:VDF_InjectAccelNetBridges_v0104 — 只增不減錨點注入器
- **函式**(4):`plan_file(path)` · `apply_file(path, backup_dir)` · `collect(vdf_root)` · `main(argv)`
- **CLI**:`--backup-dir` `--mode` `--report` `--vdf-root`
- **自測**:主程式可跑


## VIA · 泛功能(59 支)

### VIA_ENG004_VmtAiTriage
- **族**:`functional modules/VMT/engines/vmt_ai_triage`(版本 1;現役 `vmt_ai_triage.py`)
- **功能**:============================================================================
- **函式**(4):`triage_one(mail, llm, base_date)` · `run(ws, commit, use_llm, no_open, base_date)` · `load_triage(ws)` · `main()`
- **CLI**:`--llm`
- **自測**:主程式可跑

### VIA_ENG005_VmtCore
- **族**:`functional modules/VMT/engines/vmt_core`(版本 1;現役 `vmt_core.py`)
- **功能**:============================================================================
- **類**:Workspace, Ledger, EventLog, Quarantine, LocalLLM, EngineResult
- **函式**(10):`now_iso()` · `today()` · `md5_bytes(b)` · `fingerprint()` · `norm_case(s)` · `clip(s, n)` · `banner(title, subtitle)` · `mode_label(commit)` · `read_jsonl(path)` · `append_jsonl(path, rec, durable)`
- **CLI**:`--commit` `--no-open` `--root`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG006_VmtDashboard
- **族**:`functional modules/VMT/engines/vmt_dashboard`(版本 1;現役 `vmt_dashboard.py`)
- **功能**:============================================================================
- **函式**(2):`run(ws, commit, no_open, as_of)` · `main()`
- **CLI**:`--as-of`
- **自測**:主程式可跑

### VIA_ENG007_VmtExtractTasks
- **族**:`functional modules/VMT/engines/vmt_extract_tasks`(版本 1;現役 `vmt_extract_tasks.py`)
- **功能**:============================================================================
- **函式**(5):`from_mails(ws, me)` · `from_minutes(ws, include_questions)` · `find_duplicates(candidates, existing)` · `run(ws, me, commit, no_open, include_questions)` · `main()`
- **CLI**:`--include-questions` `--me`
- **自測**:主程式可跑

### VIA_ENG008_VmtLang
- **族**:`functional modules/VMT/engines/vmt_lang`(版本 1;現役 `vmt_lang.py`)
- **功能**:============================================================================
- **函式**(7):`split_sentences(text, max_len)` · `zh2int(s)` · `resolve_due(text, base)` · `classify_mail(subject, body, has_checkbox_reply)` · `classify_sentence(text, is_chair, base_date)` · `strip_fillers(text)` · `to_traditional(text, config)`
- **自測**:匯入型

### VIA_ENG009_VmtMailComposer
- **族**:`functional modules/VMT/engines/vmt_mail_composer`(版本 1;現役 `vmt_mail_composer.py`)
- **功能**:============================================================================
- **函式**(3):`compose(reminder, sender_name, as_of, roster)` · `run(ws, commit, no_open, draft, send)` · `main()`
- **CLI**:`--as-of` `--draft` `--me` `--send` `--sender`
- **自測**:主程式可跑

### VIA_ENG010_VmtMeetingMinutes
- **族**:`functional modules/VMT/engines/vmt_meeting_minutes`(版本 1;現役 `vmt_meeting_minutes.py`)
- **功能**:============================================================================
- **函式**(8):`load_transcript(src)` · `segment(segs, speaker_map, max_len)` · `flag_hallucinations(utts, no_speech_max)` · `clean(utts, vocab, traditional)` · `resolve_subjects(utts, roster)` · `tag_utterances(utts, chair, base_date)` · `agenda_hits(text, agenda, threshold)` · `split_topics(utts, agenda, chair, gap)`
- **CLI**:`---` `--config` `--transcript`
- **自測**:主程式可跑

### VIA_ENG011_VmtOutlookIntake
- **族**:`functional modules/VMT/engines/vmt_outlook_intake`(版本 1;現役 `vmt_outlook_intake.py`)
- **功能**:============================================================================
- **函式**(8):`thread_key(subject, case)` · `normalize_mail(raw, source)` · `source_outlook(days_back)` · `source_folder(inbox)` · `source_sample()` · `run(ws, source, days_back, commit, no_open)` · `load_mails(ws)` · `main()`
- **CLI**:`--days-back` `--source`
- **自測**:主程式可跑

### VIA_ENG012_VmtPipeline
- **族**:`functional modules/VMT/engines/vmt_pipeline`(版本 1;現役 `vmt_pipeline.py`)
- **功能**:============================================================================
- **函式**(2):`run(ws, commit, no_open, transcript, meeting_config)` · `main()`
- **CLI**:`--as-of` `--commit` `--demo` `--draft` `--llm` `--me` `--meeting-config` `--no-open` `--root` `--send` `--source` `--transcript`
- **自測**:主程式可跑

### VIA_ENG013_VmtProjects
- **族**:`functional modules/VMT/engines/vmt_projects`(版本 1;現役 `vmt_projects.py`)
- **功能**:============================================================================
- **函式**(7):`parse_code(text)` · `strip_code(name)` · `load_projects(ws)` · `resolve_project(text, ws)` · `scan(ws)` · `run(ws, commit, no_open)` · `main()`
- **自測**:主程式可跑

### VIA_ENG014_VmtReplyParser
- **族**:`functional modules/VMT/engines/vmt_reply_parser`(版本 1;現役 `vmt_reply_parser.py`)
- **功能**:============================================================================
- **函式**(3):`parse_reply(mail, base_date)` · `run(ws, commit, no_open, base_date)` · `main()`
- **自測**:主程式可跑

### VIA_ENG015_VmtSlaEngine
- **族**:`functional modules/VMT/engines/vmt_sla_engine`(版本 1;現役 `vmt_sla_engine.py`)
- **功能**:============================================================================
- **函式**(4):`sla_table(ws)` · `plan(ws, as_of)` · `run(ws, commit, no_open, as_of)` · `main()`
- **CLI**:`--as-of`
- **自測**:主程式可跑

### VIA_ENG016_VmtTaskSsot
- **族**:`functional modules/VMT/engines/vmt_task_ssot`(版本 1;現役 `vmt_task_ssot.py`)
- **功能**:============================================================================
- **函式**(8):`task_fingerprint(source_type, ref, cite, title)` · `build_task(title, owner, due, urgency, source_type)` · `create_tasks(ws, candidates, commit)` · `load_tasks(ws)` · `derive_states(ws, events, as_of)` · `open_tasks(ws, as_of)` · `run(ws, commit, no_open, as_of)` · `main()`
- **自測**:主程式可跑

### VIA_ENG030_Init
- **族**:`functional modules/WorkOps/VTR/engine/tests/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VIA_ENG031_TestEngine
- **族**:`functional modules/WorkOps/VTR/engine/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:vtr_py 確定性層測試。
- **類**:TestDocument, TestConfig, TestGate, TestLangDetect, TestNormalize, TestProtect, _BadStage, TestInvariants, TestAdversarial, TestReplay, TestEndToEnd
- **函式**(3):`ctx()` · `doc_of(doc_id)` · `run(doc)`
- **自測**:主程式可跑

### VIA_ENG032_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/__init__`(版本 1;現役 `__init__.py`)
- **功能**:vtr_py — DG-IN Meeting Transcript Restoration Engine（Python 版）。
- **自測**:匯入型

### VIA_ENG033_Cli
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/cli`(版本 1;現役 `cli.py`)
- **功能**:vtr CLI（確定性層）。
- **函式**(4):`cmd_restore(args)` · `cmd_replay(args)` · `cmd_inspect(args)` · `main(argv)`
- **CLI**:`--config` `--doc-id` `--meta` `--out` `--review` `--strict` `--to-rev`
- **自測**:主程式可跑

### VIA_ENG034_Context
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/context`(版本 1;現役 `context.py`)
- **功能**:執行期設定與 Context。
- **類**:Config, Metrics, Context
- **函式**(1):`default_config()`
- **自測**:匯入型

### VIA_ENG035_Document
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/document`(版本 1;現役 `document.py`)
- **功能**:VTR Document 資料契約的 Python 實作。
- **類**:ContractError, Run, Protection, Patch, Revision, Segment, Document
- **函式**(2):`apply_patches(segment, patches)` · `group_by_segment(patches)`
- **自測**:匯入型

### VIA_ENG036_Gate
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/gate`(版本 1;現役 `gate.py`)
- **功能**:信心度閘門（00_ARCHITECTURE.md §3）。
- **類**:ConfidenceGate
- **自測**:匯入型

### VIA_ENG037_Pipeline
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/pipeline`(版本 1;現役 `pipeline.py`)
- **功能**:Pipeline 執行器：Stage 串接、不變式檢查、patch 套用、版本記錄。
- **類**:StageResult, Stage, InvariantViolation, Pipeline
- **函式**(4):`check_invariants(before, result, stage_name)` · `commit(doc, result, stage_name, ctx, problems)` · `preprocessing_pipeline()` · `rejected_and_review(doc)`
- **自測**:匯入型

### VIA_ENG038_Protect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/protect`(版本 1;現役 `protect.py`)
- **功能**:P0 保護遮罩（00_ARCHITECTURE.md §2.3）。
- **類**:Candidate, SentinelViolation
- **函式**(5):`find_candidates(text, enabled_kinds)` · `next_sentinel_index(segment)` · `mask(segment, candidates, make_patch_id)` · `unmask(segment, make_patch_id)` · `check_sentinels(segments)`
- **自測**:匯入型

### VIA_ENG039_Rules
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/rules`(版本 1;現役 `rules.py`)
- **功能**:rule_id 註冊表。
- **類**:Rule, UnknownRuleError
- **函式**(2):`require(rule_id, stage)` · `cross_engine_rule_ids()`
- **自測**:匯入型

### VIA_ENG040_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VTR Stage 實作。每個 Stage 都是純函式：(Document, Context) -> StageResult。
- **自測**:匯入型

### VIA_ENG041_S1LangDetect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s1_lang_detect`(版本 1;現役 `s1_lang_detect.py`)
- **功能**:步驟 1：語言偵測（LANG_DETECT）。
- **類**:LangDetectStage
- **函式**(5):`classify(ch)` · `raw_runs(text)` · `merge_short_runs(runs, min_cjk, min_latin)` · `assign_roles(runs, text, dominant)` · `detect_segment(seg, min_cjk, min_latin, mixed_threshold)`
- **自測**:匯入型

### VIA_ENG042_S2Normalize
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s2_normalize`(版本 1;現役 `s2_normalize.py`)
- **功能**:步驟 2：正規化（NORMALIZE）。
- **類**:Claim, NormalizeStage
- **函式**(1):`resolve_claims(claims)`
- **自測**:匯入型

### VIA_ENG043_S3Protect
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/stages/s3_protect`(版本 1;現役 `s3_protect.py`)
- **功能**:P0：保護遮罩 Stage（PROTECT）。
- **類**:ProtectStage, UnprotectStage
- **自測**:匯入型

### VIA_ENG044_Init
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/__init__`(版本 1;現役 `__init__.py`)
- **功能**:Diff & Versioning Pipeline。
- **自測**:匯入型

### VIA_ENG045_Patchlog
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/patchlog`(版本 1;現役 `patchlog.py`)
- **功能**:append-only patch log（JSONL）。
- **函式**(3):`write_patchlog(doc, path)` · `read_patchlog(path)` · `patches_of_rev(rows, rev)`
- **自測**:匯入型

### VIA_ENG046_Replay
- **族**:`functional modules/WorkOps/VTR/engine/vtr_py/versioning/replay`(版本 1;現役 `replay.py`)
- **功能**:重播與回滾。
- **類**:ReplayMismatch
- **函式**(1):`replay_to(doc, target_rev)`
- **自測**:匯入型

### VIA_ENG065_WorkopsControlCommon
- **族**:`functional modules/WorkOps/engines/workops_control_common`(版本 1;現役 `workops_control_common.py`)
- **功能**:無說明(候補)
- **函式**(12):`now()` · `today()` · `jload(p, d)` · `csvrows(p)` · `atomic_json(p, obj)` · `append_hist(item, ev, detail)` · `wop_registry()` · `thr2wop()` · `project_label(wop)` · `decision_rows()`
- **自測**:匯入型

### VIA_ENG072_WorkopsLexicon
- **族**:`functional modules/WorkOps/engines/workops_lexicon`(版本 1;現役 `workops_lexicon.py`)
- **功能**:WorkOps 共用詞彙模組 v0101 — SSOT/REGEX/同義字/LIST 彙整去重(操作員 2026/08/09 令)。
- **函式**(7):`norm_subj(s)` · `clean_subject(s)` · `subj_code(s)` · `load_bulk_patterns(path)` · `is_bulk(sender, pats)` · `load_org_lexicon(path)` · `extract_url_domains(text)`
- **自測**:匯入型

### VIA_ENG079_WorkopsReplyParser
- **族**:`functional modules/WorkOps/engines/workops_reply_parser`(版本 1;現役 `workops_reply_parser.py`)
- **功能**:WorkOps 回覆解析引擎 v0106(ENG-029)— 規劃書 M3:回信 → 三層 fallback 解析 → 狀態事件
- **函式**(12):`load_json(p, default)` · `load_params()` · `read_csv(p)` · `load_scan_index()` · `norm_subject(s)` · `load_corpus_bodies()` · `body_for(bodies, corpus, conv, subject)` · `detect_flags(row, body, params)` · `parse_one(row, body, params)` · `load_seen()`
- **自測**:主程式可跑

### VIA_ENG089_Init
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA Accelerated Integration v0139A governed engines.
- **自測**:匯入型

### VIA_ENG090_DomainEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_domain_engine`(版本 1;現役 `via_domain_engine_v0139a.py`)
- **功能**:無說明(候補)
- **類**:ContractError, HydraRiskError, WriteResult, PipelineResult
- **函式**(12):`def_utc_now_text()` · `def_slug(value)` · `def_sha256_bytes(data)` · `def_sha256_file(path)` · `def_atomic_write_text(path, content, encoding)` · `def_atomic_write_json(path, payload)` · `def_normalize_columns(frame, aliases)` · `def_require_columns(frame, required, dataset_name)` · `def_normalize_ticker(value)` · `def_read_table(path, declared_format)`
- **CLI**:`--classification` `--flows` `--mode` `--output-dir` `--prices` `--require-parquet` `--revenue`
- **自測**:主程式可跑

### VIA_ENG091_FlowSimulationEngine
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/engine/via_flow_simulation_engine`(版本 1;現役 `via_flow_simulation_engine_v0139a.py`)
- **功能**:無說明(候補)
- **函式**(1):`def_run(flows, prices, classification, short_window, long_window)`
- **自測**:匯入型

### VIA_ENG096_Init
- **族**:`functional modules/VIA_Accelerated_Integration_v0139A_DELIVERY/VIA_Accelerated_Integration_v0139A/tests/__init__`(版本 1;現役 `__init__.py`)
- **功能**:Unit and integration tests for VIA Accelerated Integration v0139A.
- **自測**:匯入型

### VIA_ENG148_VmeMain
- **族**:`functional modules/VME/engines/vme_main`(版本 1;現役 `vme_main.py`)
- **功能**:vme_main — VME 方法論引擎核心 v0.1(TOOL-056;方法論導入令 2026-08-18)
- **類**:Policy, Lake
- **函式**(6):`load_system_config(path)` · `resolve_mode_policy(mode, approval)` · `authorize_operation(mode, runtime_append_approved)` · `build_run_context(cfg)` · `selftest()` · `main()`
- **CLI**:`--approve-runtime-append` `--mode` `--selftest`
- **自測**:✅ --selftest

### VIA_ENG149_BuildAll
- **族**:`functional modules/WorkOps/VeritasPulse/build_all`(版本 1;現役 `build_all.py`)
- **功能**:VeritasPulse — build everything (interactive app + project deck).
- **函式**(1):`main()`
- **CLI**:`--db` `--out` `--pid`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG150_BuildDeck
- **族**:`functional modules/WorkOps/VeritasPulse/VIA_ENG150_BuildDeck`(版本 1;現役 `VIA_ENG150_BuildDeck.py`)
- **功能**:VeritasPulse — one-shot project deck builder.
- **函式**(1):`main()`
- **CLI**:`--db` `--out` `--pid`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG152_Selftest
- **族**:`functional modules/WorkOps/VeritasPulse/selftest`(版本 1;現役 `selftest.py`)
- **功能**:VeritasPulse — consolidated self-test (test/debug/consolidate/activate).
- **函式**(11):`check(name, fn)` · `t_compile()` · `t_store()` · `t_archive()` · `t_minutes()` · `t_env_arrange()` · `t_deck()` · `t_app()` · `t_meeting_docs()` · `t_config_pwa()`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG153_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG154_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/app/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG155_BuildApp
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/app/build_app`(版本 1;現役 `build_app.py`)
- **功能**:VPL-APP · single-file application generator.
- **函式**(1):`build(db_path, out_dir, out_name, project_id)`
- **CLI**:`--db` `--out`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG156_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/charts/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG157_Optimize
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/charts/optimize`(版本 1;現役 `optimize.py`)
- **功能**:VPL-I02/I03 chart engine with an 'auto-optimize' pass.
- **函式**(5):`optimize(ax, grid)` · `gantt(tasks, out_dir)` · `budget(rows, out_dir)` · `risk_heatmap(risks, out_dir)` · `stakeholders(rows, out_dir)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG158_Config
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/config`(版本 1;現役 `config.py`)
- **功能**:VPL-CFG · central configuration surface.
- **函式**(2):`load(out_dir)` · `write_default(out_dir)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG159_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/core/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG160_Archive
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/core/archive`(版本 1;現役 `archive.py`)
- **功能**:VPL-C05 · Storage policy + archive (Parquet / JSON / DuckDB).
- **函式**(3):`archive(db_path, out_dir)` · `generate_minutes(db_path, out_dir, meeting_id)` · `export_csv(db_path, out_dir)`
- **CLI**:`--db` `--out`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG161_EnvArrange
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/core/env_arrange`(版本 1;現役 `env_arrange.py`)
- **功能**:VPL-C00 · Environment Arrangement (with Veritas supportive tools).
- **函式**(2):`arrange(supportive_root, preferred_env, out_dir, execute)` · `deploy(supportive_root, preferred_env, out_dir, dry_run)`
- **CLI**:`--deploy` `--env` `--execute` `--live` `--out` `--root`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG162_Store
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/core/store`(版本 1;現役 `store.py`)
- **功能**:VPL-C01 Registry + VPL-C03 LocalStore.
- **函式**(3):`connect(db_path)` · `init_db(db_path, seed)` · `load_project(db_path, project_id)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG163_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/meeting/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG164_ExcelTemplate
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/meeting/excel_template`(版本 1;現役 `excel_template.py`)
- **功能**:VPL-XLS · transcript-review Excel template (reduce manual classification).
- **函式**(1):`build(db_path, out_dir, meeting_id)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG165_MinutesDoc
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/meeting/minutes_doc`(版本 1;現役 `minutes_doc.py`)
- **功能**:VPL-MIN · professional, visual-locked Meeting Minutes (HTML + PDF).
- **函式**(1):`build(db_path, out_dir, mode, meeting_id)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG166_Init
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/ppt/__init__`(版本 1;現役 `__init__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG167_Generate
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/ppt/generate`(版本 1;現役 `generate.py`)
- **功能**:VPL-OUT · Project PPT generator (python-pptx).
- **函式**(5):`title_slide(prs, p)` · `snapshot_slide(prs, p)` · `chart_slide(prs, title, sub, img, img_w)` · `closing_slide(prs, p)` · `build(project, out_dir, out_name)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG168_Registry
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/registry`(版本 1;現役 `registry.py`)
- **功能**:VeritasPulse module registry.
- **函式**(1):`enabled_modules()`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG169_Theme
- **族**:`functional modules/WorkOps/VeritasPulse/vpl/theme`(版本 1;現役 `theme.py`)
- **功能**:VeritasPulse (VPL) — VIA Visual Lock v1 theme tokens.
- **函式**(1):`mpl(c)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VIA_ENG170_WorkPulseUnified
- **族**:`functional modules/WorkOps/VIA_ENG170_WorkPulseUnified`(版本 4;現役 `VIA_ENG170_WorkPulseUnified_v0103.py`)
- **功能**:(v0102→v0103 批349:⑤ sha 比對 CRLF 正規化後備=Windows autocrlf 簽出不假壞)(v0101→v0102 批337:⑤ wave4+wave5 manifest 自洽—快取件(.pytest_cac
- **函式**(5):`domains()` · `dedup_audit()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module


## VRN · 報告情報(309 支)

### VRN_ENG002_InvestmentRegexPatternVALIDATED
- **族**:`functional modules/VRN/InvestmentRegexPattern_VALIDATED`(版本 1;現役 `InvestmentRegexPattern_VALIDATED.py`)
- **功能**:╔═══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:_FbTimer, _FbHardwareTuner, _FbGCTuner, StatementType, CategoryType, ValidationLevel, PatternDef, ExtractedValue, ValidationResult, InvestmentPatternMatcher, FinancialDataValidator, FinancialStatementAnalyzer
- **函式**(3):`get_version()` · `get_status()` · `run_test()`
- **自測**:主程式可跑

### VRN_ENG003_HardGateBootPrecheck
- **族**:`functional modules/VRN/VIA_HardGate_BootPrecheck`(版本 1;現役 `VIA_HardGate_BootPrecheck.py`)
- **功能**:VIA_HardGate_BootPrecheck.py — 7-Tool BOOT_PRECHECK 統一載入樣板
- **函式**(3):`hardgate_load_inline(ssot_dir, policy, py_inject, quiet)` · `hardgate_caps_summary(caps)` · `hardgate_get(caps, key)`
- **CLI**:`--quiet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG013_MDL001Converter
- **族**:`functional modules/VRN/VRN_MDL001_Converter`(版本 3;現役 `VRN_MDL001_Converter_v0121.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, MDL001BatchBuffer, MDL001DuckWriter, MDL001SelfVerifier, VRN_MDL001_Converter
- **函式**(3):`file_sha256(path)` · `detect_input_type(path)` · `list_input_files(input_dir)`
- **CLI**:`--convert-to` `--headless` `--outdir` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG015_MDL002LayoutExtractor
- **族**:`functional modules/VRN/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DocCache, MDL002DBWriter, MDL002BatchBuffer, MDL002DuckWriter, MDL002SelfVerifier, VRN_MDL002_LayoutExtractor
- **函式**(5):`list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)` · `extract_zones_first_page(pdf_path, page, cfg)` · `detect_table_regions(pdf_path, page_no, page_text, page_cls, cfg)` · `split_quadrants(pdf_path, page_no, cfg, doc_cache)`
- **自測**:主程式可跑

### VRN_ENG016_MDL003TableRestorer
- **族**:`functional modules/VRN/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003BatchBuffer, MDL003DuckWriter, MDL003DBWriter, MDL003SelfVerifier, VRN_MDL003_TableRestorer
- **函式**(4):`load_mdl002_output(mdl002_temp)` · `repair_text_blocks_batch(blocks, reflow)` · `canonicalize_label(label)` · `classify_fin_type(canonical)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG017_MDL004OCRFetchingPDFTable
- **族**:`functional modules/VRN/VRN_ENG017_MDL004OCRFetchingPDFTable`(版本 1;現役 `VRN_ENG017_MDL004OCRFetchingPDFTable.py`)
- **功能**:無說明(候補)
- **類**:MDL004DocCache, RawTableResult, FixedTable, MDL004DBWriter, MDL004BatchBuffer, MDL004DuckWriter, MDL004SelfVerifier, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG018_MDL005OCRFetchingPDFText
- **族**:`functional modules/VRN/VRN_ENG018_MDL005OCRFetchingPDFText`(版本 1;現役 `VRN_ENG018_MDL005OCRFetchingPDFText.py`)
- **功能**:無說明(候補)
- **類**:MDL005DocCache, RawTextBlock, FixedTextBlock, MDL005DBWriter, MDL005BatchBuffer, MDL005DuckWriter, MDL005SelfVerifier, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG019_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VRN/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, MDL006BatchBuffer, MDL006DuckWriter, MDL006SelfVerifier, VRN_MDL006_Consolidator
- **函式**(2):`load_mdl003_output(mdl003_temp)` · `load_mdl004_output(mdl004_temp)`
- **自測**:匯入型

### VRN_ENG020_MDL007APIDataFetcher
- **族**:`functional modules/VRN/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, MDL007BatchBuffer, MDL007DuckWriter, MDL007SelfVerifier, VRN_MDL007_APIDataFetcher
- **函式**(3):`load_plugins(ssot_dir)` · `normalize_to_million(value, source_unit)` · `normalize_precision(value_million, decimal)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG021_MDL008CrossValidator
- **族**:`functional modules/VRN/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, MDL008BatchBuffer, MDL008DuckWriter, MDL008SelfVerifier, VRN_MDL008_CrossValidator
- **函式**(7):`is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)` · `to_million(value, unit)` · `precision_normalize(v, decimal)` · `std_val(value, unit)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG022_MDL010CodeRegistry
- **族**:`functional modules/VRN/VRN_MDL010_CodeRegistry`(版本 1;現役 `VRN_MDL010_CodeRegistry.py`)
- **功能**:無說明(候補)
- **類**:VRN_MDL010_CodeRegistry
- **CLI**:`--out` `--query`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VeritasAegisNexus, VeritasCeleritas

### VRN_ENG023_MDL011DailyFetcher
- **族**:`functional modules/VRN/VRN_ENG023_MDL011DailyFetcher`(版本 1;現役 `VRN_ENG023_MDL011DailyFetcher.py`)
- **功能**:無說明(候補)
- **類**:VRN_MDL011_DailyFetcher
- **CLI**:`--codes` `--date` `--out`
- **自測**:主程式可跑 · **整合邊**:VIA_SSOT_Unified, VIA_SuperAccel_Module, VeritasAegisNexus, VeritasCeleritas

### VRN_ENG029_EditableLegacy
- **族**:`functional modules/VRN/_quarantine_pip_vendor/editable_legacy`(版本 1;現役 `editable_legacy.py`)
- **功能**:Legacy editable installation process, i.e. `setup.py develop`.
- **函式**(1):`install_editable(global_options, prefix, home, use_user_site, name)`
- **自測**:匯入型

### VRN_ENG030_InstallationReport
- **族**:`functional modules/VRN/_quarantine_pip_vendor/installation_report`(版本 1;現役 `installation_report.py`)
- **功能**:無說明(候補)
- **類**:InstallationReport
- **自測**:匯入型

### VRN_ENG031_MetadataEditable
- **族**:`functional modules/VRN/_quarantine_pip_vendor/metadata_editable`(版本 1;現役 `metadata_editable.py`)
- **功能**:Metadata generation logic for source distributions.
- **函式**(1):`generate_editable_metadata(build_env, backend, details)`
- **自測**:匯入型

### VRN_ENG032_Reporter
- **族**:`functional modules/VRN/_quarantine_pip_vendor/reporter`(版本 1;現役 `reporter.py`)
- **功能**:無說明(候補)
- **類**:PipReporter, PipDebuggingReporter
- **自測**:匯入型

### VRN_ENG033_Reporters
- **族**:`functional modules/VRN/_quarantine_pip_vendor/reporters`(版本 1;現役 `reporters.py`)
- **功能**:無說明(候補)
- **類**:BaseReporter
- **自測**:匯入型

### VRN_ENG034_Table
- **族**:`functional modules/VRN/_quarantine_pip_vendor/table`(版本 1;現役 `table.py`)
- **功能**:無說明(候補)
- **類**:Column, Row, _Cell, Table
- **自測**:主程式可跑

### VRN_ENG035_WheelEditable
- **族**:`functional modules/VRN/_quarantine_pip_vendor/wheel_editable`(版本 1;現役 `wheel_editable.py`)
- **功能**:無說明(候補)
- **函式**(1):`build_wheel_editable(name, backend, metadata_directory, tempd)`
- **自測**:匯入型

### VRN_ENG037_MDL001Converter
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL001_Converter`(版本 1;現役 `VRN_MDL001_Converter.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, VRN_MDL001_Converter
- **函式**(4):`file_sha256(path)` · `detect_input_type(path)` · `list_input_files(input_dir)` · `parse_filename_meta(filename)`
- **CLI**:`--convert-to` `--headless` `--outdir`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG038_MDL002LayoutExtractor
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DBWriter, VRN_MDL002_LayoutExtractor
- **函式**(5):`list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)` · `extract_zones_first_page(pdf_path, page, cfg)` · `detect_table_regions(pdf_path, page_no, page_text, page_cls, cfg)` · `split_quadrants(pdf_path, page_no, cfg)`
- **自測**:主程式可跑

### VRN_ENG039_MDL003TableRestorer
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003DBWriter, VRN_MDL003_TableRestorer
- **函式**(7):`load_mdl002_output(mdl002_temp)` · `canonicalize_label(label)` · `classify_fin_type(canonical)` · `clean_ocr_number(val)` · `is_axis_noise(text)` · `restore_one_table(tbl_dict, repair, cfg)` · `apply_calc_rules(rt)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG040_MDL004OCRFetchingPDFTableV1
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL004_OCR_FetchingPDFTable_v1`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTableResult, FixedTable, MDL004DBWriter, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG041_MDL005OCRFetchingPDFTextV1
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL005_OCRFetchingPDFText_v1`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTextBlock, FixedTextBlock, MDL005DBWriter, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG042_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, VRN_MDL006_Consolidator
- **函式**(2):`load_mdl003_output(mdl003_temp)` · `load_mdl004_output(mdl004_temp)`
- **自測**:匯入型

### VRN_ENG043_MDL007APIDataFetcher
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, VRN_MDL007_APIDataFetcher
- **函式**(3):`load_plugins(ssot_dir)` · `normalize_to_million(value, source_unit)` · `normalize_precision(value_million, decimal)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG044_MDL008CrossValidator
- **族**:`functional modules/VRN/_superseded/20260804/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, VRN_MDL008_CrossValidator
- **函式**(7):`is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)` · `to_million(value, unit)` · `precision_normalize(v, decimal)` · `std_val(value, unit)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG045_PanoramaXcheck
- **族**:`functional modules/VRN/panorama_xcheck`(版本 3;現役 `panorama_xcheck_v112.py`)
- **功能**:panorama_xcheck_v110.py — 全景交叉核對(v111R 重建;README 載明「full 8-module dataflow」
- **函式**(1):`run()`
- **CLI**:`--no-pause`
- **自測**:主程式可跑

### VRN_ENG051_D8bFilenameParser
- **族**:`functional modules/VRN/vrn_d8b_filename_parser`(版本 1;現役 `vrn_d8b_filename_parser.py`)
- **功能**:無說明(候補)
- **函式**(3):`parse_filename(fn)` · `classify_eps(text)` · `validate_eps_pair(basic, diluted, tol)`
- **自測**:匯入型

### VRN_ENG056_PdfForensics
- **族**:`functional modules/VRN/VRN_ENG056_PdfForensics`(版本 1;現役 `VRN_ENG056_PdfForensics_v0100.py`)
- **功能**:vrn_pdf_forensics_v0100 — PDF 法醫探針(唯讀;零輸出檔死因判定)
- **函式**(2):`forensics(p)` · `main()`
- **CLI**:`--file`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG059_GapMultirescue
- **族**:`functional modules/VRN/VRN_ENG059_GapMultirescue`(版本 1;現役 `VRN_ENG059_GapMultirescue_v0100.py`)
- **功能**:vrn_gap_multirescue_v0100 — 表格缺口多方案總攻指揮(TOOL-049;操作員令 2026-08-18)
- **函式**(9):`newest(pattern, root)` · `find_gaps()` · `locate(name)` · `run_stream(argv, timeout)` · `probe_extract_result(name)` · `assault_pdf(name, path, log)` · `assault_docx(name, path, commit, log)` · `selftest()` · `main()`
- **CLI**:`--commit` `--engines` `--extract` `--only` `--selftest` `--timeout`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module, superextract

### VRN_ENG060_TextOmni
- **族**:`functional modules/VRN/VRN_ENG060_TextOmni`(版本 1;現役 `VRN_ENG060_TextOmni_v0100.py`)
- **功能**:vrn_text_omni_v0100 — 文字統包引擎(TOOL-050;操作員令 2026-08-18)
- **函式**(5):`lanes()` · `guard_zipbomb(p)` · `guard_encrypted(p)` · `mojibake_score(text)` · `extract_one(p)`
- **CLI**:`--extract` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module, superextract

### VRN_ENG061_PanoramaXcheckV110Shaa9stub110R
- **族**:`functional modules/VRN/panorama_xcheck_v110_shaa9stub110R`(版本 1;現役 `panorama_xcheck_v110_shaa9stub110R.py`)
- **功能**:panorama_xcheck_v110.py — 全景交叉核對(v110R 重建;README 載明「full 8-module dataflow」
- **函式**(1):`run()`
- **CLI**:`--no-pause`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG062_SummarizerV1
- **族**:`functional modules/VRN/VRN_ENG062_SummarizerV1`(版本 3;現役 `VRN_ENG062_SummarizerV1_v0102.py`)
- **功能**:無說明(候補)
- **類**:ReportSummary, AdjCloseFetcher, KeywordExtractor, ExtractiveSummarizer, CategorySentenceExtractor, ValuationMethodDetector, ReportCodeGenerator, VRN_Summarizer
- **函式**(4):`get_version()` · `get_libs_status()` · `summarize_report(ticker, first_page_text, remaining_text)` · `main()`
- **CLI**:`---` `--status` `--test` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG066_NLPSupportHub
- **族**:`functional modules/VRN/VRN_ENG066_NLPSupportHub`(版本 1;現役 `VRN_ENG066_NLPSupportHub_v0100.py`)
- **功能**:VRN_ENG066_NLPSupportHub — NLP 工具統一整合×Summarizer 支援樞紐(批157;via-nlphub)
- **函式**(8):`normalize(text)` · `analyze(text)` · `segment(text)` · `enrich_for_summary(text, top_sentences)` · `verify_summary(summary_text, source_text)` · `support_summarizer(text, bullets)` · `selftest()` · `main()`
- **CLI**:`--demo` `--json` `--selftest` `--text`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG067_MindMapSSOT
- **族**:`functional modules/VRN/VRN_ENG067_MindMapSSOT`(版本 4;現役 `VRN_ENG067_MindMapSSOT_v0103.py`)
- **功能**:VRN_ENG067_MindMapSSOT — 三語關鍵字 SSOT×分類×漸進知識體 Mind map(批158;via-mindmap)
- **函式**(6):`classify(kw, ent_label)` · `extract_keywords(text)` · `ingest(text, source)` · `build_map()` · `status()` · `selftest()`
- **CLI**:`--file` `--map` `--selftest` `--status` `--text`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG068_DailyBrief
- **族**:`functional modules/VRN/VRN_ENG068_DailyBrief`(版本 5;現役 `VRN_ENG068_DailyBrief_v0104.py`)
- **功能**:(v0101→v0102 批337:市場寬度句改取最新「完整」交易日=標的數≥0.8×近 60 日中位(批326 尾端
- **函式**(7):`harvest_via()` · `harvest_vdf()` · `harvest_vap()` · `harvest_vrn()` · `build()` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG069_ConsensusDB
- **族**:`functional modules/VRN/VRN_ENG069_ConsensusDB`(版本 5;現役 `VRN_ENG069_ConsensusDB_v0104.py`)
- **功能**:VRN_ENG069_ConsensusDB — 驗證共識資料庫(批176;操作員定位令)
- **函式**(4):`build()` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG070_YahooConsensus
- **族**:`functional modules/VRN/VRN_ENG070_YahooConsensus`(版本 3;現役 `VRN_ENG070_YahooConsensus_v0102.py`)
- **功能**:VRN_ENG070_YahooConsensus — Yahoo 共識資料引擎(批194;操作員令)
- **函式**(6):`parse_symbol(payload)` · `upsert(con, date, code, row)` · `run(codes)` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG071_CnyesFusion
- **族**:`functional modules/VRN/VRN_ENG071_CnyesFusion`(版本 1;現役 `VRN_ENG071_CnyesFusion_v0100.py`)
- **功能**:VRN_ENG071_CnyesFusion — 鉅亨 FactSet 共識融合引擎(批199;操作員令)
- **函式**(7):`parse_target(d)` · `parse_eps(rows)` · `upsert(con, date, code, tp, eps)` · `run(codes)` · `status()` · `selftest()` · `main()`
- **CLI**:`--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG072_MDL001Converter
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL001_Converter`(版本 1;現役 `VRN_MDL001_Converter.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, VRN_MDL001_Converter
- **函式**(5):`file_sha256(path)` · `detect_input_type(path)` · `list_input_files(input_dir)` · `parse_filename_meta(filename)` · `convert_pdf_to_hq_pdf(src_path, dst_path, dpi, jpeg_quality, max_pages)`
- **CLI**:`--convert-to` `--headless` `--outdir`
- **自測**:主程式可跑

### VRN_ENG073_MDL002LayoutExtractor
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DBWriter, VRN_MDL002_LayoutExtractor
- **函式**(5):`list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)` · `extract_zones_first_page(pdf_path, page, cfg)` · `detect_table_regions(pdf_path, page_no, page_text, page_cls, cfg)` · `split_quadrants(pdf_path, page_no, cfg)`
- **自測**:主程式可跑

### VRN_ENG074_MDL003TableRestorer
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003DBWriter, VRN_MDL003_TableRestorer
- **函式**(7):`load_mdl002_output(mdl002_temp)` · `canonicalize_label(label)` · `classify_fin_type(canonical)` · `clean_ocr_number(val)` · `is_axis_noise(text)` · `restore_one_table(tbl_dict, repair, cfg)` · `apply_calc_rules(rt)`
- **CLI**:`---`
- **自測**:主程式可跑

### VRN_ENG075_MDL004OCRFetchingPDFTableV1
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL004_OCR_FetchingPDFTable_v1`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTableResult, FixedTable, MDL004DBWriter, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG076_MDL005OCRFetchingPDFTextV1
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL005_OCRFetchingPDFText_v1`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTextBlock, FixedTextBlock, MDL005DBWriter, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑

### VRN_ENG077_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, VRN_MDL006_Consolidator
- **函式**(2):`load_mdl003_output(mdl003_temp)` · `load_mdl004_output(mdl004_temp)`
- **自測**:匯入型

### VRN_ENG078_MDL007APIDataFetcher
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, VRN_MDL007_APIDataFetcher
- **函式**(3):`load_plugins(ssot_dir)` · `normalize_to_million(value, source_unit)` · `normalize_precision(value_million, decimal)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG079_MDL008CrossValidator
- **族**:`functional modules/VAP/ASSETS/SCOPE_COPY/VeritasIntelligenceAnalytics/functional modules/VRN/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, VRN_MDL008_CrossValidator
- **函式**(7):`is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)` · `to_million(value, unit)` · `precision_normalize(v, decimal)` · `std_val(value, unit)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑

### VRN_ENG080_FinancialDocumentSummarizerEngine1
- **族**:`functional modules/VRN/VIA_Financial_Document_Summarizer_Engine_1`(版本 1;現役 `VIA_Financial_Document_Summarizer_Engine_1.py`)
- **功能**:VIA Financial Document Intelligence & Four-Bullet Summarizer Engine.
- **類**:DocumentBlock, SecurityIdentity, InvestmentMetrics, EngineResult, SummarizerBackend, SummaryContext, DeterministicExtractiveSummarizer, LlamaCppSummarizer
- **函式**(12):`def_has_module(name)` · `def_build_tool_registry()` · `def_sha256(path)` · `def_normalize_text(text)` · `def_repair_mojibake(text)` · `def_split_sentences(text)` · `def_dedupe_sentences(sentences)` · `def_classify_text(text, size, base, max_size, bold)` · `def_make_plain_blocks(text, source)` · `def_parse_pdf(path)`
- **CLI**:`--backend` `--context-size` `--model-path` `--output-dir` `--security-master` `--self-test` `--threads` `--ticker`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG081_SummarizerEngine2
- **族**:`functional modules/VRN/VIA_SummarizerEngine_2`(版本 1;現役 `VIA_SummarizerEngine_2.py`)
- **功能**:VIA Summarizer Engine
- **類**:EngineConfig, ResourceSnapshot, SentenceRecord, KeywordRecord, SummaryBullet, SummaryResult, SSOTStore, VIASummarizerEngine
- **函式**(11):`def_configure_thread_environment(cpu_threads)` · `def_now_iso()` · `def_sha256_text(text)` · `def_sha256_file(path, block_size)` · `def_json_dumps(value, indent)` · `def_atomic_write_text(path, text, encoding)` · `def_optional_module(module_name)` · `def_spacy_pipeline(model_name)` · `def_capability_report()` · `def_normalize_number_token(token)`
- **CLI**:`--approve` `--auto-promote` `--available-only` `--batch-size` `--blacklist` `--context` `--cpu-threads` `--db` `--embedding-model-path` `--fasttext-model-path` `--formats` `--glob`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG082_CompleteFeatureAuditUltra
- **族**:`functional modules/VRN/VRN_Complete_FeatureAudit_Ultra`(版本 1;現役 `VRN_Complete_FeatureAudit_Ultra.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:StockTickerPatterns, DatePatterns, TargetPricePatterns, ValidationResult, FinancialValidationEngine, DocumentElementType, DocumentElementPatterns, ExternalDataFetcher
- **函式**(1):`run_complete_audit()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG083_ENG064KnowledgeStack
- **族**:`functional modules/VRN/VRN_ENG064_KnowledgeStack`(版本 2;現役 `VRN_ENG064_KnowledgeStack_v0101.py`)
- **功能**:VRN_ENG064_KnowledgeStack — 本地知識抽取堆疊轉接 v0101(批152;via-know)
- **函式**(4):`load_stack()` · `analyze(text)` · `selftest()` · `main()`
- **CLI**:`--demo` `--json` `--selftest` `--text`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG084_ENG065MailIntel
- **族**:`functional modules/VRN/VRN_ENG065_MailIntel`(版本 1;現役 `VRN_ENG065_MailIntel_v0100.py`)
- **功能**:VRN_ENG065_MailIntel — NLP×郵件追蹤×報告摘要整合管線(批143;via-mail)
- **函式**(6):`enrich(email, tracker_fn, nlp_mod)` · `summarize(cards, nlp_mod)` · `to_markdown(summary, cards)` · `run(inbox, write_md)` · `selftest()` · `main()`
- **CLI**:`--demo` `--inbox` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG085_FinancialSynonymsSSOT
- **族**:`functional modules/VRN/VRN_Financial_Synonyms_SSOT`(版本 1;現役 `VRN_Financial_Synonyms_SSOT.py`)
- **功能**:VRN_Financial_Synonyms_SSOT.py
- **函式**(6):`normalize_metric(raw)` · `normalize_field_cn(raw)` · `normalize_sector(raw)` · `normalize_currency(raw)` · `parse_unit(raw)` · `normalize_report_type(raw)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG086_MDL004OCRFetchingPDFTableV1
- **族**:`functional modules/VRN/VRN_MDL004_OCR_FetchingPDFTable_v1`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTableResult, FixedTable, MDL004DBWriter, VRN_MDL004_OCRFetcher
- **函式**(3):`list_pdfs(pdf_temp)` · `is_scan_pdf(pdf_path)` · `get_header_context(page, table_bbox)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG087_MDL005OCRFetchingPDFTextV1
- **族**:`functional modules/VRN/VRN_MDL005_OCRFetchingPDFText_v1`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTextBlock, FixedTextBlock, MDL005DBWriter, VRN_MDL005_TextFetcher
- **函式**(2):`normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG090_OperatorRegexTWTicker
- **族**:`functional modules/VRN/VRN_OperatorRegex_TWTicker`(版本 1;現役 `VRN_OperatorRegex_TWTicker_v0100.py`)
- **功能**:無說明(候補)
- **函式**(1):`parse_taiwan_ticker(input_ticker)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG092_TW01TickerBridge
- **族**:`functional modules/VRN/VRN_TW01_TickerBridge`(版本 3;現役 `VRN_TW01_TickerBridge_v0102.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:TickerFormat, DetectedTicker
- **函式**(6):`detect_tickers(text)` · `trigger_data_fetch(codes)` · `read_output_data()` · `process_document_text(text, auto_fetch)` · `self_test()` · `selftest()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG093_TW02ReportParser
- **族**:`functional modules/VRN/VRN_TW02_ReportParser`(版本 2;現役 `VRN_TW02_ReportParser_v0101.py`)
- **功能**:╔══════════════════════════════════════════════════════════════════════════════════════════════════════╗
- **類**:ReportDatePatterns, AnalystPatterns, FilenameParser, PageParser, CrossValidator, TW02_ReportParser
- **函式**(3):`is_valid_ticker(code)` · `fetch_financial_data(tickers)` · `self_test()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG097_FinancialClassificationRules
- **族**:`functional modules/VRN/financial_classification_rules`(版本 1;現役 `financial_classification_rules.py`)
- **功能**:VeritasSynonymEngine™ - 財務分類規則完整版
- **類**:TickerRegex, DateTimeRegex
- **函式**(7):`get_feature_category(feature_name)` · `get_all_features()` · `get_feature_regex(feature_name)` · `find_broker(text)` · `find_rating(text)` · `convert_ticker(ticker, target_format)` · `print_summary()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG098_FinancialDataStandardization
- **族**:`functional modules/VRN/financial_data_standardization`(版本 1;現役 `financial_data_standardization.py`)
- **功能**:無說明(候補)
- **類**:FinancialDataTester, RegexPatterns, FinancialFieldMapping, FinancialFieldsMapper, KeywordRules, ValidationEngine, FinancialDataStandardizer
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG104_CNYESFactSetYFinanceConsensusFusionEngine
- **族**:`functional modules/VRN/references/intake/VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine`(版本 1;現役 `VIA_CNYES_FactSet_YFinance_Consensus_Fusion_Engine_v0120.py`)
- **功能**:VIA · CNYES/FactSet × YFinance Consensus Fusion Engine · v2.0.0
- **函式**(12):`def_import_libraries()` · `def_runtime_dependency_report(live_mode)` · `def_assert_runtime_dependencies(live_mode)` · `def_now_utc()` · `def_now_utc_iso()` · `def_format_date(value)` · `def_epoch_to_date(value)` · `def_safe_float(value)` · `def_safe_int(value)` · `def_round(value, digits)`
- **CLI**:`--allow-missing-duckdb` `--codes` `--fixture` `--force-refresh` `--no-resume` `--output-dir` `--preflight-only` `--skip-unit-tests`
- **自測**:主程式可跑

### VRN_ENG105_Reporter
- **族**:`functional modules/VRN/reporter`(版本 1;現役 `reporter.py`)
- **功能**:無說明(候補)
- **類**:PipReporter, PipDebuggingReporter
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG106_Reporters
- **族**:`functional modules/VRN/reporters`(版本 1;現役 `reporters.py`)
- **功能**:無說明(候補)
- **類**:BaseReporter
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG107_Table
- **族**:`functional modules/VRN/table`(版本 1;現役 `table.py`)
- **功能**:無說明(候補)
- **類**:Column, Row, _Cell, Table
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG109_FinExtract
- **族**:`functional modules/VRN/vrn_fin_extract`(版本 2;現役 `vrn_fin_extract_v0101.py`)
- **功能**:vrn_fin_extract_v0101 — 財報頁年度分析擷取器(TOOL-082)
- **函式**(10):`load_ssot()` · `parse_number(tok)` · `find_years(line, ssot)` · `extract_annual(text, ssot)` · `to_fin_dict(result, year)` · `rich_matrix(title, columns, rows, state_col)` · `render_ui(result, src_name, run_dir, ssot)` · `run_file(path, fin_out, year, no_open, out_root)` · `selftest()` · `main()`
- **CLI**:`--file` `--fin-out` `--no-open` `--selftest` `--year`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG110_Finaudit
- **族**:`functional modules/VRN/vrn_finaudit`(版本 6;現役 `vrn_finaudit_v0105.py`)
- **功能**:vrn_finaudit_v0105 — 財務驗算稽核器(TOOL-078)
- **函式**(7):`load_feature_audit()` · `load_vdf_rows(explicit)` · `audit_row(r, fa, vdf_map)` · `audit_financials(fin, fa)` · `rich_matrix(title, columns, rows, state_col)` · `render_ui(result, run_dir)` · `newest_matrix()`
- **CLI**:`--fin` `--matrix` `--no-open` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG111_Finlex
- **族**:`functional modules/VRN/vrn_finlex`(版本 5;現役 `vrn_finlex_v0104.py`)
- **功能**:vrn_finlex_v0104 — 財務字庫收割引擎(TOOL-072)
- **函式**(8):`camel2snake(k)` · `fold_degenerates(metrics)` · `newest(pattern)` · `harvest()` · `rich_matrix(title, columns, rows, state_col)` · `build(out_dir)` · `ask(term)` · `ask_many(terms)`
- **CLI**:`--all` `--ask` `--build` `--no-open` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG112_MethodKernel
- **族**:`functional modules/VRN/vrn_method_kernel`(版本 3;現役 `vrn_method_kernel_v0102.py`)
- **功能**:vrn_method_kernel_v0102 — VRN 方法核(TOOL-071)
- **類**:FieldRecord
- **函式**(12):`load_method()` · `mixed_tolerance(a, b, abs_tol, rel_tol)` · `judge(a, b, abs_tol, rel_tol)` · `pct_point_diff(reported_pct, recalc_pct)` · `upside_pct(target, current)` · `growth(cur, base)` · `derive_quarter(stmt_type, cumulative, prev_cumulative)` · `gross_profit_check(revenue, cost, reported_gp, abs_tol, rel_tol)` · `balance_identity(assets, liabilities, equity, abs_tol, rel_tol)` · `cashflow_identity(end_cash, begin_cash, op_cf, inv_cf, fin_cf)`
- **CLI**:`--audit` `--selftest` `--show`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG113_ReportDigest
- **族**:`functional modules/VRN/vrn_report_digest`(版本 16;現役 `vrn_report_digest_v0115.py`)
- **功能**:vrn_report_digest_v0115 — 個股報告摘要批跑器(TOOL-070;批516 自測零網路律落實)
- **函式**(9):`load_params()` · `load_summarizer()` · `load_equity_registry()` · `resolve_equity(ticker, text, reg, prm)` · `load_classifier40()` · `classify_non_stock(stem, ticker, reg, prm, cls40)` · `shorten_official_name(off_name, stem, prm)` · `tp_flag(upside, prm)` · `load_tw02()`
- **CLI**:`--collect` `--dir` `--from` `--limit` `--no-open` `--selftest` `--to` `--undo` `--vdf`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG114_InvestmentReportClassifier
- **族**:`functional modules/VRN/webscraping_dualengine_v20260819/VIA_Investment_Report_Classifier`(版本 1;現役 `VIA_Investment_Report_Classifier.py`)
- **功能**:無說明(候補)
- **類**:ReportClassification
- **函式**(5):`def_load_report_type_ssot(path)` · `def_normalize_report_text(value)` · `def_classify_investment_report(title, content, ssot)` · `def_split_morning_brief(title, content, parent_url, ssot)` · `def_self_test()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG115_UnifiedWebScrapingPlaywrightEngine
- **族**:`functional modules/VRN/webscraping_dualengine_v20260819/VIA_Unified_WebScraping_Playwright_Engine`(版本 1;現役 `VIA_Unified_WebScraping_Playwright_Engine.py`)
- **功能**:VIA Unified Web Scraping Engine — Playwright-first, local, governed.
- **類**:CrawlConfig, FetchResponse, ExtractedPage, CrawlState, FetchBackend, RobotsGuard, PoliteRateLimiter, UrllibBackend, HttpxBackend, PlaywrightBackend, StandardHTMLExtractor, OutputStore
- **函式**(11):`def_has_module(module)` · `def_capability_registry()` · `def_now_iso()` · `def_normalize_url(url, base_url)` · `def_registered_domain(host)` · `def_same_scope(candidate, seeds, allow_subdomains)` · `def_url_allowed(url, config)` · `def_choose_backend(name)` · `def_parse_json_ld(parts)` · `def_find_jsonld_value(items, keys)`
- **CLI**:`--allow-external` `--authorization-basis` `--backend` `--browser` `--click` `--config` `--consent-token` `--delay` `--exclude` `--headed` `--ignore-robots` `--include`
- **自測**:主程式可跑 · **整合邊**:VIA_Investment_Report_Classifier, VIA_SuperAccel_Module, VIA_WebScraping_Compliance

### VRN_ENG116_WebScrapingCompliance
- **族**:`functional modules/VRN/webscraping_dualengine_v20260819/VIA_WebScraping_Compliance`(版本 2;現役 `VIA_WebScraping_Compliance_v0101.py`)
- **功能**:無說明(候補)
- **類**:ComplianceFinding
- **函式**(8):`def_load_compliance_ssot(path)` · `def_validate_consent(token, purpose, authorization_basis, ssot)` · `def_luhn_valid(value)` · `def_tw_id_valid(value)` · `def_redact_pii(text, mode, ssot)` · `def_scan_terms_text(text, ssot)` · `def_compliance_payload(text, pii_mode)` · `def_self_test()`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG117_WebScrapingComplianceSyntaxfix
- **族**:`functional modules/VRN/webscraping_dualengine_v20260819/VIA_WebScraping_Compliance_syntaxfix`(版本 1;現役 `VIA_WebScraping_Compliance_syntaxfix_v0100.py`)
- **功能**:無說明(候補)
- **類**:ComplianceFinding
- **函式**(8):`def_load_compliance_ssot(path)` · `def_validate_consent(token, purpose, authorization_basis, ssot)` · `def_luhn_valid(value)` · `def_tw_id_valid(value)` · `def_redact_pii(text, mode, ssot)` · `def_scan_terms_text(text, ssot)` · `def_compliance_payload(text, pii_mode)` · `def_self_test()`
- **自測**:主程式可跑

### VRN_ENG118_WebScrapingDualEngineGovernanceController
- **族**:`functional modules/VRN/webscraping_dualengine_v20260819/VIA_WebScraping_DualEngine_Governance_Controller`(版本 1;現役 `VIA_WebScraping_DualEngine_Governance_Controller.py`)
- **功能**:One Python governance controller for VIA Python + JavaScript scraping engines.
- **類**:Capability, EngineHealth, RunResult
- **函式**(12):`def_now()` · `def_hash_file(path)` · `def_atomic_json(path, value)` · `def_python_module_available(name)` · `def_node_module_available(name)` · `def_emit(percent, status, message)` · `def_check_python_engine(dynamic_required)` · `def_check_javascript_engine()` · `def_panorama(mode)` · `def_choose_lanes(mode, panorama)`
- **CLI**:`--authorization-basis` `--backend` `--browser` `--check` `--click` `--consent-token` `--delay` `--headed` `--max-depth` `--max-pages` `--mode` `--output-dir`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module, VIA_WebScraping_Compliance

### VRN_ENG120_ENG036FinalizeCoreV2
- **族**:`functional modules/VRN/20260804/VRN_ENG036_FinalizeCoreV2`(版本 1;現役 `VRN_ENG036_FinalizeCoreV2.py`)
- **功能**:VRN Finalize AIO - embedded Python core
- **函式**(3):`via_support(name)` · `via_support_status(load_all)` · `cmd_anchor_preview(canonical_master, out_json)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG121_MDL001Converter
- **族**:`functional modules/VRN/20260804/VRN_MDL001_Converter`(版本 1;現役 `VRN_MDL001_Converter.py`)
- **功能**:無說明(候補)
- **類**:MDL001DBWriter, VRN_MDL001_Converter
- **函式**(4):`via_support(name)` · `via_support_status(load_all)` · `file_sha256(path)` · `detect_input_type(path)`
- **CLI**:`--convert-to` `--headless` `--outdir`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG122_MDL002LayoutExtractor
- **族**:`functional modules/VRN/20260804/VRN_MDL002_LayoutExtractor`(版本 1;現役 `VRN_MDL002_LayoutExtractor.py`)
- **功能**:無說明(候補)
- **類**:TableRecord, TextBlock, MDL002DBWriter, VRN_MDL002_LayoutExtractor
- **函式**(4):`via_support(name)` · `via_support_status(load_all)` · `list_pdfs_in_temp(pdf_temp)` · `classify_page(page_text, page_no)`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG123_MDL003TableRestorer
- **族**:`functional modules/VRN/20260804/VRN_MDL003_TableRestorer`(版本 1;現役 `VRN_MDL003_TableRestorer.py`)
- **功能**:無說明(候補)
- **類**:TextRepairEngine, RestoredTable, MDL003DBWriter, VRN_MDL003_TableRestorer
- **函式**(6):`via_support(name)` · `via_support_status(load_all)` · `load_mdl002_output(mdl002_temp)` · `canonicalize_label(label)` · `classify_fin_type(canonical)` · `clean_ocr_number(val)`
- **CLI**:`---`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG124_MDL004OCRFetchingPDFTableV1
- **族**:`functional modules/VRN/20260804/VRN_MDL004_OCR_FetchingPDFTable_v1`(版本 1;現役 `VRN_MDL004_OCR_FetchingPDFTable_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTableResult, FixedTable, MDL004DBWriter, VRN_MDL004_OCRFetcher
- **函式**(2):`via_support(name)` · `via_support_status(load_all)`
- **CLI**:`---` `--dpi` `--engine-primary` `--engine-secondary` `--mdl004-temp` `--no-db` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG125_MDL005OCRFetchingPDFTextV1
- **族**:`functional modules/VRN/20260804/VRN_MDL005_OCRFetchingPDFText_v1`(版本 1;現役 `VRN_MDL005_OCRFetchingPDFText_v1.py`)
- **功能**:無說明(候補)
- **類**:RawTextBlock, FixedTextBlock, MDL005DBWriter, VRN_MDL005_TextFetcher
- **函式**(4):`via_support(name)` · `via_support_status(load_all)` · `normalize_rating(raw)` · `load_plugins(ssot_dir)`
- **CLI**:`--engine-primary` `--engine-secondary` `--mdl005-temp` `--no-aegis` `--no-celeritas` `--no-db` `--no-ssot` `--pdf-temp` `--ssot-dir` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG126_MDL006ConsolidatorAndPhaseValidator
- **族**:`functional modules/VRN/20260804/VRN_MDL006_ConsolidatorAndPhaseValidator`(版本 1;現役 `VRN_MDL006_ConsolidatorAndPhaseValidator.py`)
- **功能**:無說明(候補)
- **類**:CompareResult, VRN_MDL006_Consolidator
- **函式**(2):`via_support(name)` · `via_support_status(load_all)`
- **自測**:匯入型 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG127_MDL007APIDataFetcher
- **族**:`functional modules/VRN/20260804/VRN_MDL007_APIDataFetcher`(版本 1;現役 `VRN_MDL007_APIDataFetcher.py`)
- **功能**:無說明(候補)
- **類**:MDL007DBWriter, VRN_MDL007_APIDataFetcher
- **函式**(3):`via_support(name)` · `via_support_status(load_all)` · `load_plugins(ssot_dir)`
- **CLI**:`--mdl007-temp` `--ssot-dir` `--tickers` `--workers`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG128_MDL008CrossValidator
- **族**:`functional modules/VRN/20260804/VRN_MDL008_CrossValidator`(版本 1;現役 `VRN_MDL008_CrossValidator.py`)
- **功能**:無說明(候補)
- **類**:VerifyResult, ForecastCheck, MDL008DBWriter, VRN_MDL008_CrossValidator
- **函式**(6):`via_support(name)` · `via_support_status(load_all)` · `is_historical(period)` · `is_forecast(period)` · `to_year(period)` · `load_plugins(ssot_dir)`
- **CLI**:`--api-parquet` `--output-dir` `--report-parquet` `--ssot-dir`
- **自測**:主程式可跑 · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG129_VRNFirstPageEngine
- **族**:`functional modules/VRN/VIA_VRN_FirstPageEngine`(版本 23;現役 `VIA_VRN_FirstPageEngine_v0124.py`)
- **功能**:VIA_VRN_FirstPageEngine  v0113
- **類**:TickerFilename, Layout, TableGeometry, NLPRepair, XValBridge, NameReconciler, FinancialValidation, PriceAdjustment, BrokerRatingDict, FieldValidation, CrossValidation, FirstPageEngine
- **函式**(4):`load_ssot_blocks(ssot_path)` · `mount_nlp_hub(explicit_dir)` · `parse_period(tok)` · `to_million_2dp(value, unit, unit_mult)`
- **CLI**:`--body` `--dir` `--file` `--fixtures` `--help` `--json` `--no-onepage-open` `--onepage` `--open` `--report` `--selftest` `--ssot`
- **自測**:✅ --selftest

### VRN_ENG130_ENG072FirstPageText
- **族**:`functional modules/VRN/VRN_ENG072_FirstPageText`(版本 30;現役 `VRN_ENG072_FirstPageText_v0129.py`)
- **功能**:v0128→v0129(批522 工作站實錄 via-ryg vrn:firstpage RED 三檢 ㉙/㉜/㊷):
- **函式**(5):`intake_kinds()` · `kind_of(p)` · `intake_in_dir(d)` · `intake_files(targets)` · `logic_mod()`
- **CLI**:`--adapters` `--apply` `--dir` `--disabled` `--force` `--in` `--json` `--list-langs` `--no-incoming` `--ocr-budget` `--open` `--pdf`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG131_ENG073ReportStructuredDB
- **族**:`functional modules/VRN/VRN_ENG073_ReportStructuredDB`(版本 27;現役 `VRN_ENG073_ReportStructuredDB_v0126.py`)
- **功能**:v0125→v0126(批521 工作站實錄 via-ryg vrn RED ㉞:Windows 上 Path('/tmp/_d_') 印成 \tmp\_d_,字串比對永遠不等=判錯的紅燈;改 as_posix 比對;程式行為零改)
- **函式**(6):`nlp_hub()` · `nlp_stats()` · `tokenize_filename(stem)` · `date_from_token(tok)` · `parse_date(name)` · `parse_broker(name)`
- **CLI**:`--apply` `--db` `--dir` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG132_ENG074FinancialPages
- **族**:`functional modules/VRN/VRN_ENG074_FinancialPages`(版本 10;現役 `VRN_ENG074_FinancialPages_v0109.py`)
- **功能**:v0108→v0109(批521 工作站實錄 via-ryg vrn RED ⑯:Windows 上 Path('/tmp/_b_.duckdb') 印成反斜線,字串比對永遠不等=判錯的紅燈;改 as_posix 比對;程式行為零改)
- **函式**(6):`parse_header(line)` · `parse_data_row(line, header, syn, hub)` · `is_financial_page(text)` · `extract_docx_fin(p)` · `extract_pdf_fin(p)` · `compare_values(a, b)`
- **CLI**:`--crosscheck` `--db` `--dir` `--no-cross` `--selftest` `--status`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG133_ENG075DocToMarkdown
- **族**:`functional modules/VRN/VRN_ENG075_DocToMarkdown`(版本 2;現役 `VRN_ENG075_DocToMarkdown_v0101.py`)
- **功能**:VRN_ENG075_DocToMarkdown — 文件→Markdown→JSON 引擎(批249 立;批258 JSON 道)
- **函式**(5):`convert(p)` · `md_to_json(md)` · `run(src)` · `selftest()` · `main()`
- **CLI**:`--dir` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG134_ENG076RegressionGate
- **族**:`functional modules/VRN/VRN_ENG076_RegressionGate`(版本 2;現役 `VRN_ENG076_RegressionGate_v0101.py`)
- **功能**:VRN_ENG076_RegressionGate v0101 — 抽取鏈迴歸閘(批251;操作員「完成所有工作
- **函式**(6):`extract_tp_p(m, right, main, stem)` · `day_numbers_in(report_date)` · `base_suspect(base, report_date, price_cands, ticker)` · `run(evid)` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG135_ENG077OmniFormatBridge
- **族**:`functional modules/VRN/VRN_ENG077_OmniFormatBridge`(版本 1;現役 `VRN_ENG077_OmniFormatBridge_v0100.py`)
- **功能**:VRN_ENG077_OmniFormatBridge — VOFIE 全格式引擎橋(批256;操作員令)
- **函式**(4):`probe()` · `run(inputs)` · `selftest()` · `main()`
- **CLI**:`--output` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG136_ENG078NLPOneBridge
- **族**:`functional modules/VRN/VRN_ENG078_NLPOneBridge`(版本 2;現役 `VRN_ENG078_NLPOneBridge_v0101.py`)
- **功能**:VRN_ENG078_NLPOneBridge — NLP OneEngine 收容橋(批283;操作員令)
- **函式**(5):`probe()` · `register_merge()` · `run()` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG137_ENG079ControlTowerDashboard
- **族**:`functional modules/VRN/VRN_ENG079_ControlTowerDashboard`(版本 1;現役 `VRN_ENG079_ControlTowerDashboard_v0100.py`)
- **功能**:VRN_ENG079_ControlTowerDashboard — VRN 控制塔儀表板(批306)
- **函式**(5):`gather()` · `render(d)` · `run(do_print)` · `selftest()` · `main()`
- **CLI**:`--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG138_ENG080FourPointDigest
- **族**:`functional modules/VRN/VRN_ENG080_FourPointDigest`(版本 6;現役 `VRN_ENG080_FourPointDigest_v0105.py`)
- **功能**:VRN_ENG080_FourPointDigest v0100 — 研報「一題四點」文摘+潛在上漲空間(目標價除權息調整)引擎(批386)
- **函式**(10):`grab(text, rx)` · `extract_target_price(text)` · `extract_val_method(text)` · `extract_basis(text)` · `extract_reason(text)` · `extract_risk(text)` · `extract_eps_years(text)` · `first_page(text)` · `remainder_two(text)` · `fmt_pct(v)`
- **CLI**:`--db` `--json` `--limit` `--selftest` `--ticker` `--zones`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG139_ENG081ParquetMainDB
- **族**:`functional modules/VRN/VRN_ENG081_ParquetMainDB`(版本 1;現役 `VRN_ENG081_ParquetMainDB_v0100.py`)
- **功能**:VRN_ENG081_ParquetMainDB v0100 — VRN 交付主資料庫(Parquet 唯一真值)
- **函式**(5):`resolve_db(db)` · `build(db, outdir, derive, do_print)` · `status(outdir, do_print)` · `selftest()` · `main()`
- **CLI**:`--derive` `--out` `--selftest`
- **自測**:✅ --selftest · **整合邊**:VIA_SuperAccel_Module

### VRN_ENG140_ENG082ExtractionLogic
- **族**:`functional modules/VRN/VRN_ENG082_ExtractionLogic`(版本 11;現役 `VRN_ENG082_ExtractionLogic_v0110.py`)
- **功能**:VRN_ENG082_ExtractionLogic v0110 — VRN 擷取**中央邏輯庫**(批515 +fix_contents:TAB3「FIXED CONTENTS」修正識別)
- **函式**(10):`logic_dir()` · `ssot()` · `ladder()` · `budget_s()` · `backend_ttl_h()` · `hq_budget_s()` · `hq_dpi_band()` · `nonocr_failed(lg)` · `sha1_of(path)` · `load_latest()`
- **CLI**:`--db` `--dry-run` `--selftest`
- **自測**:✅ --selftest

### VRN_ENG141_ENG086FirstPageLogicBridge
- **族**:`functional modules/VRN/VRN_ENG086_FirstPageLogicBridge`(版本 1;現役 `VRN_ENG086_FirstPageLogicBridge_v0100.py`)
- **功能**:VRN_ENG086_FirstPageLogicBridge v0100 — 第一頁邏輯補缺正主橋(批522 操作員上傳 VIA_VRN_FirstPageEngine v0101 ALL-IN-ONE;「附件看能否修第一頁邏輯缺失部分」
- **函式**(10):`intake_home()` · `intake_engine_file(home)` · `intake_md5_ok(home)` · `load_intake()` · `resolve_vdf_db()` · `roster()` · `broker_tables(E)` · `safe_broker(text, E)` · `safe_rating(text, E)` · `safe_target_price(text, E, exclude_code, exclude_codes)`
- **CLI**:`--in` `--limit` `--out` `--selftest`
- **自測**:✅ --selftest

### VRN_ENG142_AdapterSdk
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/adapter_sdk`(版本 1;現役 `adapter_sdk.py`)
- **功能**:Shared contracts and utilities for every GenericLayoutEngine backend.
- **類**:AdapterConfig, AdapterProbe, AdapterElement, QualityMetrics, AdapterResult, AdapterContext, BaseAdapter, ExternalCommandAdapter
- **函式**(12):`utc_timestamp()` · `normalize_text(value)` · `text_signature(value)` · `readable_character_ratio(value)` · `replacement_character_ratio(value)` · `duplicate_line_ratio(value)` · `compute_quality(result)` · `evaluate_acceptance(result, config)` · `module_exists(module_name)` · `binary_path(binary_name)`
- **自測**:匯入型

### VRN_ENG143_AllBackendEngines
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/all_backend_engines`(版本 1;現役 `all_backend_engines.py`)
- **功能**:Concrete adapters for the full local PDF/image extraction matrix.
- **類**:PdfPlumberEngine, PyPdfEngine, PopplerEngine, PdfParseNodeEngine, PyMuPdfEngine, PdfMinerEngine, PdfBoxEngine, PdfJsEngine, MuPdfCliEngine, PyMuPdf4LlmEngine, CamelotEngine, TabulaEngine
- **函式**(12):`result_shell(adapter, probe)` · `bbox_from_any(value)` · `render_pdf_pages(context)` · `image_dimensions(path)` · `resolved_tesseract_languages(context)` · `command_from_template(template, input_path, output_dir)` · `markdown_to_elements(markdown)` · `find_first_text_file(directory, suffixes)` · `package_major_version(distribution_name)` · `paddle_result_payload(value)`
- **CLI**:`--deskew` `--input-type=module` `--language` `--list-langs` `--optimize` `--output_dir` `--skip-text` `--text`
- **自測**:匯入型

### VRN_ENG144_GenericLayoutEngine
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/generic_layout_engine`(版本 1;現役 `generic_layout_engine.py`)
- **功能**:GenericLayoutEngine
- **類**:EngineConfig, BBox, FontProfile, Relation, LayoutElement, PageLayout, BackendStatus, DocumentLayout
- **函式**(12):`utc_timestamp()` · `sha256_file(path)` · `hash8(value)` · `normalize_text(value)` · `text_signature(value)` · `weighted_median(values)` · `union_bbox(boxes)` · `zone_for_bbox(box, width, height)` · `font_weight_from_name(font_name, flags)` · `safe_relative_path(path, base)`
- **CLI**:`--config` `--dpi` `--languages` `--no-annotations` `--no-tables` `--ocr` `--output`
- **自測**:主程式可跑

### VRN_ENG145_MultiEngineOrchestrator
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/multi_engine_orchestrator`(版本 1;現役 `multi_engine_orchestrator.py`)
- **功能**:Resource-aware router, backend orchestrator, and consensus fusion engine.
- **類**:OrchestratorConfig, CanonicalElement, OrchestratorRun
- **函式**(12):`load_config_payload(path)` · `apply_adapter_config(config, payload)` · `load_engine_stack_config(payload)` · `load_orchestrator_config(path)` · `required_capabilities_met(result, required)` · `build_route(config)` · `should_jump_to_ocr(result, config)` · `document_profile_from_results(results, min_text_characters)` · `file_sha256(path)` · `adapter_cache_key(adapter, context, input_digest, probe)`
- **CLI**:`--adapter` `--config` `--mode` `--no-cache` `--no-core-layout` `--output`
- **自測**:主程式可跑

### VRN_ENG146_TestGenericLayoutEngine
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/tests/test_generic_layout_engine`(版本 1;現役 `test_generic_layout_engine.py`)
- **功能**:無說明(候補)
- **類**:GenericLayoutEngineTests
- **函式**(1):`build_synthetic_pdf(path)`
- **自測**:主程式可跑

### VRN_ENG147_TestMultiEngineOrchestrator
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/tests/test_multi_engine_orchestrator`(版本 1;現役 `test_multi_engine_orchestrator.py`)
- **功能**:無說明(候補)
- **類**:MultiEngineOrchestratorTests
- **自測**:主程式可跑

### VRN_ENG148_AdapterSdk
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/adapter_sdk`(版本 1;現役 `adapter_sdk.py`)
- **功能**:Shared contracts and utilities for every GenericLayoutEngine backend.
- **類**:AdapterConfig, AdapterProbe, AdapterElement, QualityMetrics, AdapterResult, AdapterContext, BaseAdapter, ExternalCommandAdapter
- **函式**(12):`utc_timestamp()` · `normalize_text(value)` · `text_signature(value)` · `readable_character_ratio(value)` · `replacement_character_ratio(value)` · `duplicate_line_ratio(value)` · `compute_quality(result)` · `evaluate_acceptance(result, config)` · `module_exists(module_name)` · `binary_path(binary_name)`
- **自測**:匯入型

### VRN_ENG149_AllBackendEngines
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/all_backend_engines`(版本 1;現役 `all_backend_engines.py`)
- **功能**:Concrete adapters for the full local PDF/image extraction matrix.
- **類**:PdfPlumberEngine, PyPdfEngine, PopplerEngine, PdfParseNodeEngine, PyMuPdfEngine, PdfMinerEngine, PdfBoxEngine, PdfJsEngine, MuPdfCliEngine, PyMuPdf4LlmEngine, CamelotEngine, TabulaEngine
- **函式**(8):`result_shell(adapter, probe)` · `bbox_from_any(value)` · `render_pdf_pages(context)` · `command_from_template(template, input_path, output_dir)` · `markdown_to_elements(markdown)` · `find_first_text_file(directory, suffixes)` · `build_all_adapters()` · `adapter_registry()`
- **CLI**:`--deskew` `--input-type=module` `--language` `--optimize` `--output_dir` `--skip-text` `--text`
- **自測**:匯入型

### VRN_ENG150_GenericLayoutEngine
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/generic_layout_engine`(版本 1;現役 `generic_layout_engine.py`)
- **功能**:GenericLayoutEngine
- **類**:EngineConfig, BBox, FontProfile, Relation, LayoutElement, PageLayout, BackendStatus, DocumentLayout
- **函式**(12):`utc_timestamp()` · `sha256_file(path)` · `hash8(value)` · `normalize_text(value)` · `text_signature(value)` · `weighted_median(values)` · `union_bbox(boxes)` · `zone_for_bbox(box, width, height)` · `font_weight_from_name(font_name, flags)` · `safe_relative_path(path, base)`
- **CLI**:`--config` `--dpi` `--languages` `--no-annotations` `--no-tables` `--ocr` `--output`
- **自測**:主程式可跑

### VRN_ENG151_MultiEngineOrchestrator
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/multi_engine_orchestrator`(版本 1;現役 `multi_engine_orchestrator.py`)
- **功能**:Resource-aware router, backend orchestrator, and consensus fusion engine.
- **類**:OrchestratorConfig, CanonicalElement, OrchestratorRun
- **函式**(12):`load_orchestrator_config(path)` · `required_capabilities_met(result, required)` · `build_route(config)` · `should_jump_to_ocr(result, config)` · `document_profile_from_results(results)` · `execute_route(input_path, work_dir, config)` · `bbox_iou(first, second)` · `elements_match(first, second)` · `choose_consensus_type(items)` · `fuse_results(results, min_confidence)`
- **CLI**:`--adapter` `--config` `--mode` `--no-core-layout` `--output`
- **自測**:主程式可跑

### VRN_ENG152_TestGenericLayoutEngine
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/tests/test_generic_layout_engine`(版本 1;現役 `test_generic_layout_engine.py`)
- **功能**:無說明(候補)
- **類**:GenericLayoutEngineTests
- **函式**(1):`build_synthetic_pdf(path)`
- **自測**:主程式可跑

### VRN_ENG153_TestMultiEngineOrchestrator
- **族**:`functional modules/VRN/references/intake/GenericLayoutEngine_v2.0.0_b242/tests/test_multi_engine_orchestrator`(版本 1;現役 `test_multi_engine_orchestrator.py`)
- **功能**:無說明(候補)
- **類**:MultiEngineOrchestratorTests
- **自測**:主程式可跑

### VRN_ENG154_MarkdownEngine
- **族**:`functional modules/VRN/references/intake/MarkdownEditingEngine_v1.2.0/engine/markdown_engine`(版本 1;現役 `markdown_engine.py`)
- **功能**:MarkdownEditingEngine: safe polyglot Markdown repair orchestrator.
- **類**:CommandResult, FileResult
- **函式**(12):`def_now_run_id()` · `def_load_json(path)` · `def_load_config(path)` · `def_sha256_bytes(data)` · `def_sha256_file(path)` · `def_resolve_executable(name)` · `def_python_package_version(name)` · `def_node_package_path(name)` · `def_node_package_version(name)` · `def_tool_registry()`
- **CLI**:`---
` `--auto-fix` `--book-output` `--check` `--config` `--disable-rules` `--dry-run` `--enable-extensions` `--fix` `--formatter` `--frail` `--from=gfm`
- **自測**:主程式可跑

### VRN_ENG155_SemanticReconstruction
- **族**:`functional modules/VRN/references/intake/MarkdownEditingEngine_v1.2.0/engine/semantic_reconstruction`(版本 1;現役 `semantic_reconstruction.py`)
- **功能**:Evidence-preserving Markdown segmentation and table reconstruction analysis.
- **函式**(12):`def_sha256_text(text)` · `def_normalize_semantic_text(text)` · `def_finding(code, severity, message, start_line, end_line)` · `def_count_unescaped_pipes(line)` · `def_split_pipe_row(line)` · `def_is_delimiter_cells(cells)` · `def_is_delimiter_like_cells(cells)` · `def_find_frontmatter_range(lines)` · `def_find_fence_ranges(lines)` · `def_index_ranges(ranges)`
- **CLI**:`---`
- **自測**:匯入型

### VRN_ENG156_TestEngine
- **族**:`functional modules/VRN/references/intake/MarkdownEditingEngine_v1.2.0/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:MarkdownEditingEngineTests
- **自測**:主程式可跑

### VRN_ENG157_BuildRelease
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/scripts/build_release`(版本 1;現役 `build_release.py`)
- **功能**:Build and verify a deterministic release ZIP and SHA-256 manifest.
- **函式**(7):`sha256_file(path)` · `should_include(path)` · `source_files()` · `write_manifest(files)` · `build_archive(files)` · `verify_archive(files)` · `main()`
- **自測**:主程式可跑

### VRN_ENG158_RunTests
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/scripts/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:Run the dependency-free unit suite without requiring pytest.
- **函式**(1):`main()`
- **自測**:主程式可跑

### VRN_ENG159_Init
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA NLP Application System public API.
- **自測**:匯入型

### VRN_ENG160_Main
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/__main__`(版本 1;現役 `__main__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG161_Adapters
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/adapters`(版本 1;現役 `adapters.py`)
- **功能**:Optional Tier 2-4 adapters, loaded only when invoked.
- **類**:OptionalNLPAdapters
- **函式**(1):`safe_extract_json(raw)`
- **自測**:匯入型

### VRN_ENG162_Api
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/api`(版本 1;現役 `api.py`)
- **功能**:FastAPI application factory. The API extra is optional.
- **類**:TokenBucketLimiter
- **函式**(1):`create_app(config_path, overrides)`
- **自測**:匯入型

### VRN_ENG163_Audit
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/audit`(版本 1;現役 `audit.py`)
- **功能**:Append-only JSONL audit log protected by a SHA-256 hash chain.
- **類**:AuditLogger
- **函式**(1):`redact_text(text)`
- **自測**:匯入型

### VRN_ENG164_BilingualOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/bilingual_ops`(版本 1;現役 `bilingual_ops.py`)
- **功能**:Conservative Chinese/English structural projection without invented translation.
- **函式**(4):`detect_language(text)` · `build_glossary(source_text)` · `bilingual_label(text, glossary)` · `decorate_mind_map(mind_map, source_text)`
- **自測**:匯入型

### VRN_ENG165_BundleOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/bundle_ops`(版本 1;現役 `bundle_ops.py`)
- **功能**:Deterministic multi-document intake and reconstruction package export.
- **函式**(2):`read_document_bundle(inputs, recursive, max_files, max_total_bytes, max_file_bytes)` · `export_reconstruction_package(output_directory, bundle, process_result)`
- **自測**:匯入型

### VRN_ENG166_Cache
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/cache`(版本 1;現役 `cache.py`)
- **功能**:Bounded SQLite cache and resumable job checkpoint store.
- **類**:SQLiteCache
- **自測**:匯入型

### VRN_ENG167_Cli
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface for local operation and testing.
- **函式**(2):`build_parser()` · `main(argv)`
- **CLI**:`--accepted` `--allow-network` `--backend` `--config` `--corrected-label` `--file` `--host` `--input` `--markitdown` `--max-chunk-chars` `--max-file-bytes` `--max-files`
- **自測**:主程式可跑

### VRN_ENG168_CodeReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/code_reconstruction`(版本 1;現役 `code_reconstruction.py`)
- **功能**:Static, non-executing reconstruction of code pasted across discussions.
- **類**:CodeDiscussionReconstructor
- **自測**:匯入型

### VRN_ENG169_CodeRestoration
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/code_restoration`(版本 1;現役 `code_restoration.py`)
- **功能**:Reviewable module templates reconstructed from static code evidence.
- **類**:CodeRestorer
- **自測**:匯入型

### VRN_ENG170_Config
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/config`(版本 1;現役 `config.py`)
- **功能**:Configuration loading, validation and path resolution.
- **函式**(2):`validate_config(config)` · `load_config(path, overrides)`
- **自測**:匯入型

### VRN_ENG171_ContentRoles
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/content_roles`(版本 1;現役 `content_roles.py`)
- **功能**:Conservative body/non-body classification and complete-input summarization.
- **類**:ContentRoleAnalyzer
- **自測**:匯入型

### VRN_ENG172_ContextReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/context_reconstruction`(版本 1;現役 `context_reconstruction.py`)
- **功能**:Source-grounded reconstruction for disordered articles and conversations.
- **類**:ContextReconstructor
- **自測**:匯入型

### VRN_ENG173_CpuAugmentation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/cpu_augmentation`(版本 1;現役 `cpu_augmentation.py`)
- **功能**:Optional CPU-first NLP augmentation with deterministic safe fallbacks.
- **類**:CPUNLPAugmentor
- **函式**(2):`decode_bytes_with_cpu_detector(raw, min_confidence, use_available_provider)` · `provider_groups()`
- **自測**:匯入型

### VRN_ENG174_Discourse
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/discourse`(版本 1;現役 `discourse.py`)
- **功能**:CPU-first discourse reconstruction for fragmented conversations and articles.
- **類**:CPUHierarchicalTopicOrganizer
- **函式**(3):`infer_content_roles(text, kind)` · `build_refinement_ledger(processor, segments)` · `build_dialogue_flow(topics, segments)`
- **自測**:匯入型

### VRN_ENG175_DiscussionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/discussion_ops`(版本 1;現役 `discussion_ops.py`)
- **功能**:Evidence-first knowledge object reconstruction for noisy discussion records.
- **類**:DiscussionKnowledgeReconstructor
- **自測**:匯入型

### VRN_ENG176_Engine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/engine`(版本 1;現役 `engine.py`)
- **功能**:VIA NLP Application System orchestration facade.
- **類**:VIAEngine
- **自測**:匯入型

### VRN_ENG177_Evaluation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/evaluation`(版本 1;現役 `evaluation.py`)
- **功能**:Gold-set quality metrics and candidate-only topic threshold calibration.
- **類**:TopicThresholdCalibrator
- **函式**(5):`precision_recall_f1(predicted, expected)` · `bcubed_scores(predicted, expected)` · `topic_labels(topics)` · `return_pairs(dialogue_flow)` · `evaluate_topic_output(topics, dialogue_flow, gold_topic_labels, gold_return_pairs)`
- **自測**:匯入型

### VRN_ENG178_FunctionClassifier
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/function_classifier`(版本 1;現役 `function_classifier.py`)
- **功能**:Evidence-first functional classification for statically extracted symbols.
- **類**:FunctionClassifier
- **自測**:匯入型

### VRN_ENG179_Ingest
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/ingest`(版本 1;現役 `ingest.py`)
- **功能**:Local, bounded extraction for common article and document formats.
- **類**:_HTMLTextExtractor
- **函式**(1):`read_local_document(path, max_bytes, use_markitdown)`
- **自測**:匯入型

### VRN_ENG180_InstructionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/instruction_ops`(版本 1;現役 `instruction_ops.py`)
- **功能**:Evidence-first reconstruction of fragmented instructions and shell commands.
- **類**:InstructionReconstructor
- **自測**:匯入型

### VRN_ENG181_Jobs
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/jobs`(版本 1;現役 `jobs.py`)
- **功能**:Crash-resistant file queue for long-running batch work.
- **類**:JobQueue
- **函式**(1):`atomic_write_json(path, value)`
- **自測**:匯入型

### VRN_ENG182_Knowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/knowledge`(版本 1;現役 `knowledge.py`)
- **功能**:Lossless dialogue segmentation, knowledge reconstruction and code governance.
- **類**:RawSegment, LosslessSegmenter, CodeExtractor, KnowledgeBuilder
- **函式**(1):`SPACE_CLEAN(value)`
- **自測**:匯入型

### VRN_ENG183_KnowledgeBodyOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/knowledge_body_ops`(版本 1;現役 `knowledge_body_ops.py`)
- **功能**:Layered bilingual knowledge-body projection over immutable evidence registers.
- **函式**(1):`build_bilingual_knowledge_body(source_text, topics, knowledge_registry, instruction_registry, code_reconstruction)`
- **自測**:匯入型

### VRN_ENG184_LayoutAnalysis
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/layout_analysis`(版本 1;現役 `layout_analysis.py`)
- **功能**:Lossless Markdown-oriented layout analysis and NLP repair projection.
- **類**:MarkdownLayoutAnalyzer
- **CLI**:`---`
- **自測**:匯入型

### VRN_ENG185_Learning
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/learning`(版本 1;現役 `learning.py`)
- **功能**:Governed feedback loop and out-of-core text classifier evolution.
- **類**:FeedbackStore, GovernedClassifier
- **自測**:匯入型

### VRN_ENG186_MindmapEnrichment
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/mindmap_enrichment`(版本 1;現役 `mindmap_enrichment.py`)
- **功能**:Typed Mind Map enrichment for context, templates, layout and functions.
- **函式**(1):`enrich_mind_map_v15(mind_map, context_reconstruction, function_classification, template_reconstruction, layout_analysis)`
- **自測**:匯入型

### VRN_ENG187_MindmapEvolution
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/mindmap_evolution`(版本 1;現役 `mindmap_evolution.py`)
- **功能**:Append-only Mind Map snapshot comparison and reviewable correction proposals.
- **函式**(2):`load_previous_reconstruction(path)` · `build_mind_map_evolution(current_mind_map, previous, conflict_register)`
- **自測**:匯入型

### VRN_ENG188_ModelPool
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/model_pool`(版本 1;現役 `model_pool.py`)
- **功能**:Lazy model pool with TTL, LRU eviction and memory estimates.
- **類**:ModelEntry, LazyModelPool
- **自測**:匯入型

### VRN_ENG189_ModuleComposition
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/module_composition`(版本 1;現役 `module_composition.py`)
- **功能**:Source-grounded CLASS/FUNCTION/PARAMETER/LIB module composition registry.
- **類**:ModuleCompositionRegistry
- **自測**:匯入型

### VRN_ENG190_ProviderRegistry
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/provider_registry`(版本 1;現役 `provider_registry.py`)
- **功能**:Read-only registry for optional local development providers.
- **類**:LocalProviderRegistry
- **自測**:匯入型

### VRN_ENG191_Resources
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/resources`(版本 1;現役 `resources.py`)
- **功能**:Cross-platform resource monitoring and admission control.
- **類**:ResourcePressureError, ResourceMonitor, ResourceWatchdog
- **自測**:匯入型

### VRN_ENG192_Routing
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/routing`(版本 1;現役 `routing.py`)
- **功能**:Task-to-tier routing with deterministic pressure fallback.
- **類**:TaskRouter
- **自測**:匯入型

### VRN_ENG193_Schemas
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/schemas`(版本 1;現役 `schemas.py`)
- **功能**:Dependency-free request and response contracts.
- **類**:ProcessRequest, RouteDecision, ResourceSnapshot, ProcessResult, FeedbackRecord, BatchItem
- **自測**:匯入型

### VRN_ENG194_Summarization
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/summarization`(版本 1;現役 `summarization.py`)
- **功能**:Bounded, evidence-linked and complete-input extractive summarization.
- **類**:CompleteEvidenceSummarizer
- **自測**:匯入型

### VRN_ENG195_SystemManager
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/system_manager`(版本 1;現役 `system_manager.py`)
- **功能**:Explicit macro-module registry and fail-closed system manager.
- **類**:SystemModuleRegistration, VIASystemManager
- **函式**(2):`build_default_system_manager(processor, knowledge_builder)` · `macro_module_catalog()`
- **自測**:匯入型

### VRN_ENG196_TableOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/table_ops`(版本 1;現役 `table_ops.py`)
- **功能**:Deterministic, provenance-first table recognition for noisy extracted text.
- **類**:StructuredTable, TextTableExtractor
- **自測**:匯入型

### VRN_ENG197_TemplateReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/template_reconstruction`(版本 1;現役 `template_reconstruction.py`)
- **功能**:Standard template reconstruction around immutable source references.
- **類**:StandardTemplateReconstructor
- **自測**:匯入型

### VRN_ENG198_TextOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/text_ops`(版本 1;現役 `text_ops.py`)
- **功能**:Deterministic bilingual text repair and analysis for arbitrary articles.
- **類**:TextProcessor
- **函式**(1):`chunk_text(text, max_chars, overlap)`
- **自測**:匯入型

### VRN_ENG199_Translation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/src/via_nlp_engine/translation`(版本 1;現役 `translation.py`)
- **功能**:Chunked translation with local memory and explicit, supported backends.
- **類**:TranslationMemory, TranslationService
- **自測**:匯入型

### VRN_ENG200_TestBundle
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test_bundle`(版本 1;現役 `test_bundle.py`)
- **功能**:無說明(候補)
- **類**:BundleReconstructionTests
- **自測**:主程式可跑

### VRN_ENG201_TestEngine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:TextProcessorTests, EngineTests, PersistenceTests
- **自測**:主程式可跑

### VRN_ENG202_TestKnowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test_knowledge`(版本 1;現役 `test_knowledge.py`)
- **功能**:無說明(候補)
- **類**:KnowledgeTests, TranslationTests
- **自測**:主程式可跑

### VRN_ENG203_TestMl
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test_ml`(版本 1;現役 `test_ml.py`)
- **功能**:無說明(候補)
- **類**:GovernedMLTests
- **自測**:主程式可跑

### VRN_ENG204_TestQuality
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test_quality`(版本 1;現役 `test_quality.py`)
- **功能**:無說明(候補)
- **類**:QualityMetricTests
- **自測**:主程式可跑

### VRN_ENG205_Test
- **族**:`functional modules/VRN/references/intake/VIA_NLP_Application_System_v1.8.0/tests/test`(版本 6;現役 `test_v18.py`)
- **功能**:無說明(候補)
- **類**:V18EvidenceSummarizerTests, V18ContentAuditTests
- **自測**:主程式可跑

### VRN_ENG206_BuildRelease
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/scripts/build_release`(版本 1;現役 `build_release.py`)
- **功能**:Build and verify a deterministic release ZIP and SHA-256 manifest.
- **函式**(7):`sha256_file(path)` · `should_include(path)` · `source_files()` · `write_manifest(files)` · `build_archive(files)` · `verify_archive(files)` · `main()`
- **自測**:主程式可跑

### VRN_ENG207_RunTests
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/scripts/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:Run the dependency-free unit suite without requiring pytest.
- **函式**(1):`main()`
- **自測**:主程式可跑

### VRN_ENG208_Init
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA NLP One Engine public API.
- **自測**:匯入型

### VRN_ENG209_Main
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/__main__`(版本 1;現役 `__main__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG210_Adapters
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/adapters`(版本 1;現役 `adapters.py`)
- **功能**:Optional Tier 2-4 adapters, loaded only when invoked.
- **類**:OptionalNLPAdapters
- **函式**(1):`safe_extract_json(raw)`
- **自測**:匯入型

### VRN_ENG211_Api
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/api`(版本 1;現役 `api.py`)
- **功能**:FastAPI application factory. The API extra is optional.
- **類**:TokenBucketLimiter
- **函式**(1):`create_app(config_path, overrides)`
- **自測**:匯入型

### VRN_ENG212_Audit
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/audit`(版本 1;現役 `audit.py`)
- **功能**:Append-only JSONL audit log protected by a SHA-256 hash chain.
- **類**:AuditLogger
- **函式**(1):`redact_text(text)`
- **自測**:匯入型

### VRN_ENG213_Cache
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/cache`(版本 1;現役 `cache.py`)
- **功能**:Bounded SQLite cache and resumable job checkpoint store.
- **類**:SQLiteCache
- **自測**:匯入型

### VRN_ENG214_Cli
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface for local operation and testing.
- **函式**(2):`build_parser()` · `main(argv)`
- **CLI**:`--accepted` `--allow-network` `--backend` `--config` `--corrected-label` `--file` `--host` `--max-chunk-chars` `--port` `--predicted-label` `--promote` `--quality`
- **自測**:主程式可跑

### VRN_ENG215_Config
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/config`(版本 1;現役 `config.py`)
- **功能**:Configuration loading, validation and path resolution.
- **函式**(2):`validate_config(config)` · `load_config(path, overrides)`
- **自測**:匯入型

### VRN_ENG216_Discourse
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/discourse`(版本 1;現役 `discourse.py`)
- **功能**:CPU-first discourse reconstruction for fragmented conversations and articles.
- **類**:CPUHierarchicalTopicOrganizer
- **函式**(3):`infer_content_roles(text, kind)` · `build_refinement_ledger(processor, segments)` · `build_dialogue_flow(topics, segments)`
- **自測**:匯入型

### VRN_ENG217_Engine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/engine`(版本 1;現役 `engine.py`)
- **功能**:VIA NLP One Engine orchestration facade.
- **類**:VIAEngine
- **自測**:匯入型

### VRN_ENG218_Ingest
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/ingest`(版本 1;現役 `ingest.py`)
- **功能**:Local, bounded extraction for common article and document formats.
- **類**:_HTMLTextExtractor
- **函式**(1):`read_local_document(path, max_bytes)`
- **自測**:匯入型

### VRN_ENG219_Jobs
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/jobs`(版本 1;現役 `jobs.py`)
- **功能**:Crash-resistant file queue for long-running batch work.
- **類**:JobQueue
- **函式**(1):`atomic_write_json(path, value)`
- **自測**:匯入型

### VRN_ENG220_Knowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/knowledge`(版本 1;現役 `knowledge.py`)
- **功能**:Lossless dialogue segmentation, knowledge reconstruction and code governance.
- **類**:RawSegment, LosslessSegmenter, CodeExtractor, KnowledgeBuilder
- **函式**(1):`SPACE_CLEAN(value)`
- **自測**:匯入型

### VRN_ENG221_Learning
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/learning`(版本 1;現役 `learning.py`)
- **功能**:Governed feedback loop and out-of-core text classifier evolution.
- **類**:FeedbackStore, GovernedClassifier
- **自測**:匯入型

### VRN_ENG222_ModelPool
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/model_pool`(版本 1;現役 `model_pool.py`)
- **功能**:Lazy model pool with TTL, LRU eviction and memory estimates.
- **類**:ModelEntry, LazyModelPool
- **自測**:匯入型

### VRN_ENG223_Resources
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/resources`(版本 1;現役 `resources.py`)
- **功能**:Cross-platform resource monitoring and admission control.
- **類**:ResourcePressureError, ResourceMonitor, ResourceWatchdog
- **自測**:匯入型

### VRN_ENG224_Routing
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/routing`(版本 1;現役 `routing.py`)
- **功能**:Task-to-tier routing with deterministic pressure fallback.
- **類**:TaskRouter
- **自測**:匯入型

### VRN_ENG225_Schemas
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/schemas`(版本 1;現役 `schemas.py`)
- **功能**:Dependency-free request and response contracts.
- **類**:ProcessRequest, RouteDecision, ResourceSnapshot, ProcessResult, FeedbackRecord, BatchItem
- **自測**:匯入型

### VRN_ENG226_TextOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/text_ops`(版本 1;現役 `text_ops.py`)
- **功能**:Deterministic bilingual text repair and analysis for arbitrary articles.
- **類**:TextProcessor
- **函式**(1):`chunk_text(text, max_chars, overlap)`
- **自測**:匯入型

### VRN_ENG227_Translation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/translation`(版本 1;現役 `translation.py`)
- **功能**:Chunked translation with local memory and explicit, supported backends.
- **類**:TranslationMemory, TranslationService
- **自測**:匯入型

### VRN_ENG228_TestEngine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:TextProcessorTests, EngineTests, PersistenceTests
- **自測**:主程式可跑

### VRN_ENG229_TestKnowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/tests/test_knowledge`(版本 1;現役 `test_knowledge.py`)
- **功能**:無說明(候補)
- **類**:KnowledgeTests, TranslationTests
- **自測**:主程式可跑

### VRN_ENG230_TestMl
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.1.0/tests/test_ml`(版本 1;現役 `test_ml.py`)
- **功能**:無說明(候補)
- **類**:GovernedMLTests
- **自測**:主程式可跑

### VRN_ENG231_BuildRelease
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/scripts/build_release`(版本 1;現役 `build_release.py`)
- **功能**:Build and verify a deterministic release ZIP and SHA-256 manifest.
- **函式**(7):`sha256_file(path)` · `should_include(path)` · `source_files()` · `write_manifest(files)` · `build_archive(files)` · `verify_archive(files)` · `main()`
- **自測**:主程式可跑

### VRN_ENG232_RunTests
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/scripts/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:Run the dependency-free unit suite without requiring pytest.
- **函式**(1):`main()`
- **自測**:主程式可跑

### VRN_ENG233_Init
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA NLP One Engine public API.
- **自測**:匯入型

### VRN_ENG234_Main
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/__main__`(版本 1;現役 `__main__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG235_Adapters
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/adapters`(版本 1;現役 `adapters.py`)
- **功能**:Optional Tier 2-4 adapters, loaded only when invoked.
- **類**:OptionalNLPAdapters
- **函式**(1):`safe_extract_json(raw)`
- **自測**:匯入型

### VRN_ENG236_Api
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/api`(版本 1;現役 `api.py`)
- **功能**:FastAPI application factory. The API extra is optional.
- **類**:TokenBucketLimiter
- **函式**(1):`create_app(config_path, overrides)`
- **自測**:匯入型

### VRN_ENG237_Audit
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/audit`(版本 1;現役 `audit.py`)
- **功能**:Append-only JSONL audit log protected by a SHA-256 hash chain.
- **類**:AuditLogger
- **函式**(1):`redact_text(text)`
- **自測**:匯入型

### VRN_ENG238_BilingualOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/bilingual_ops`(版本 1;現役 `bilingual_ops.py`)
- **功能**:Conservative Chinese/English structural projection without invented translation.
- **函式**(4):`detect_language(text)` · `build_glossary(source_text)` · `bilingual_label(text, glossary)` · `decorate_mind_map(mind_map, source_text)`
- **自測**:匯入型

### VRN_ENG239_BundleOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/bundle_ops`(版本 1;現役 `bundle_ops.py`)
- **功能**:Deterministic multi-document intake and reconstruction package export.
- **函式**(2):`read_document_bundle(inputs, recursive, max_files, max_total_bytes, max_file_bytes)` · `export_reconstruction_package(output_directory, bundle, process_result)`
- **自測**:匯入型

### VRN_ENG240_Cache
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/cache`(版本 1;現役 `cache.py`)
- **功能**:Bounded SQLite cache and resumable job checkpoint store.
- **類**:SQLiteCache
- **自測**:匯入型

### VRN_ENG241_Cli
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface for local operation and testing.
- **函式**(2):`build_parser()` · `main(argv)`
- **CLI**:`--accepted` `--allow-network` `--backend` `--config` `--corrected-label` `--file` `--host` `--input` `--markitdown` `--max-chunk-chars` `--max-file-bytes` `--max-files`
- **自測**:主程式可跑

### VRN_ENG242_CodeReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/code_reconstruction`(版本 1;現役 `code_reconstruction.py`)
- **功能**:Static, non-executing reconstruction of code pasted across discussions.
- **類**:CodeDiscussionReconstructor
- **自測**:匯入型

### VRN_ENG243_CodeRestoration
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/code_restoration`(版本 1;現役 `code_restoration.py`)
- **功能**:Reviewable module templates reconstructed from static code evidence.
- **類**:CodeRestorer
- **自測**:匯入型

### VRN_ENG244_Config
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/config`(版本 1;現役 `config.py`)
- **功能**:Configuration loading, validation and path resolution.
- **函式**(2):`validate_config(config)` · `load_config(path, overrides)`
- **自測**:匯入型

### VRN_ENG245_ContextReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/context_reconstruction`(版本 1;現役 `context_reconstruction.py`)
- **功能**:Source-grounded reconstruction for disordered articles and conversations.
- **類**:ContextReconstructor
- **自測**:匯入型

### VRN_ENG246_Discourse
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/discourse`(版本 1;現役 `discourse.py`)
- **功能**:CPU-first discourse reconstruction for fragmented conversations and articles.
- **類**:CPUHierarchicalTopicOrganizer
- **函式**(3):`infer_content_roles(text, kind)` · `build_refinement_ledger(processor, segments)` · `build_dialogue_flow(topics, segments)`
- **自測**:匯入型

### VRN_ENG247_DiscussionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/discussion_ops`(版本 1;現役 `discussion_ops.py`)
- **功能**:Evidence-first knowledge object reconstruction for noisy discussion records.
- **類**:DiscussionKnowledgeReconstructor
- **自測**:匯入型

### VRN_ENG248_Engine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/engine`(版本 1;現役 `engine.py`)
- **功能**:VIA NLP One Engine orchestration facade.
- **類**:VIAEngine
- **自測**:匯入型

### VRN_ENG249_Evaluation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/evaluation`(版本 1;現役 `evaluation.py`)
- **功能**:Gold-set quality metrics and candidate-only topic threshold calibration.
- **類**:TopicThresholdCalibrator
- **函式**(5):`precision_recall_f1(predicted, expected)` · `bcubed_scores(predicted, expected)` · `topic_labels(topics)` · `return_pairs(dialogue_flow)` · `evaluate_topic_output(topics, dialogue_flow, gold_topic_labels, gold_return_pairs)`
- **自測**:匯入型

### VRN_ENG250_FunctionClassifier
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/function_classifier`(版本 1;現役 `function_classifier.py`)
- **功能**:Evidence-first functional classification for statically extracted symbols.
- **類**:FunctionClassifier
- **自測**:匯入型

### VRN_ENG251_Ingest
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/ingest`(版本 1;現役 `ingest.py`)
- **功能**:Local, bounded extraction for common article and document formats.
- **類**:_HTMLTextExtractor
- **函式**(1):`read_local_document(path, max_bytes, use_markitdown)`
- **自測**:匯入型

### VRN_ENG252_InstructionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/instruction_ops`(版本 1;現役 `instruction_ops.py`)
- **功能**:Evidence-first reconstruction of fragmented instructions and shell commands.
- **類**:InstructionReconstructor
- **自測**:匯入型

### VRN_ENG253_Jobs
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/jobs`(版本 1;現役 `jobs.py`)
- **功能**:Crash-resistant file queue for long-running batch work.
- **類**:JobQueue
- **函式**(1):`atomic_write_json(path, value)`
- **自測**:匯入型

### VRN_ENG254_Knowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/knowledge`(版本 1;現役 `knowledge.py`)
- **功能**:Lossless dialogue segmentation, knowledge reconstruction and code governance.
- **類**:RawSegment, LosslessSegmenter, CodeExtractor, KnowledgeBuilder
- **函式**(1):`SPACE_CLEAN(value)`
- **自測**:匯入型

### VRN_ENG255_KnowledgeBodyOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/knowledge_body_ops`(版本 1;現役 `knowledge_body_ops.py`)
- **功能**:Layered bilingual knowledge-body projection over immutable evidence registers.
- **函式**(1):`build_bilingual_knowledge_body(source_text, topics, knowledge_registry, instruction_registry, code_reconstruction)`
- **自測**:匯入型

### VRN_ENG256_LayoutAnalysis
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/layout_analysis`(版本 1;現役 `layout_analysis.py`)
- **功能**:Lossless Markdown-oriented layout analysis and NLP repair projection.
- **類**:MarkdownLayoutAnalyzer
- **CLI**:`---`
- **自測**:匯入型

### VRN_ENG257_Learning
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/learning`(版本 1;現役 `learning.py`)
- **功能**:Governed feedback loop and out-of-core text classifier evolution.
- **類**:FeedbackStore, GovernedClassifier
- **自測**:匯入型

### VRN_ENG258_MindmapEnrichment
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/mindmap_enrichment`(版本 1;現役 `mindmap_enrichment.py`)
- **功能**:Typed Mind Map enrichment for context, templates, layout and functions.
- **函式**(1):`enrich_mind_map_v15(mind_map, context_reconstruction, function_classification, template_reconstruction, layout_analysis)`
- **自測**:匯入型

### VRN_ENG259_MindmapEvolution
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/mindmap_evolution`(版本 1;現役 `mindmap_evolution.py`)
- **功能**:Append-only Mind Map snapshot comparison and reviewable correction proposals.
- **函式**(2):`load_previous_reconstruction(path)` · `build_mind_map_evolution(current_mind_map, previous, conflict_register)`
- **自測**:匯入型

### VRN_ENG260_ModelPool
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/model_pool`(版本 1;現役 `model_pool.py`)
- **功能**:Lazy model pool with TTL, LRU eviction and memory estimates.
- **類**:ModelEntry, LazyModelPool
- **自測**:匯入型

### VRN_ENG261_ProviderRegistry
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/provider_registry`(版本 1;現役 `provider_registry.py`)
- **功能**:Read-only registry for optional local development providers.
- **類**:LocalProviderRegistry
- **自測**:匯入型

### VRN_ENG262_Resources
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/resources`(版本 1;現役 `resources.py`)
- **功能**:Cross-platform resource monitoring and admission control.
- **類**:ResourcePressureError, ResourceMonitor, ResourceWatchdog
- **自測**:匯入型

### VRN_ENG263_Routing
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/routing`(版本 1;現役 `routing.py`)
- **功能**:Task-to-tier routing with deterministic pressure fallback.
- **類**:TaskRouter
- **自測**:匯入型

### VRN_ENG264_Schemas
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/schemas`(版本 1;現役 `schemas.py`)
- **功能**:Dependency-free request and response contracts.
- **類**:ProcessRequest, RouteDecision, ResourceSnapshot, ProcessResult, FeedbackRecord, BatchItem
- **自測**:匯入型

### VRN_ENG265_TableOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/table_ops`(版本 1;現役 `table_ops.py`)
- **功能**:Deterministic, provenance-first table recognition for noisy extracted text.
- **類**:StructuredTable, TextTableExtractor
- **自測**:匯入型

### VRN_ENG266_TemplateReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/template_reconstruction`(版本 1;現役 `template_reconstruction.py`)
- **功能**:Standard template reconstruction around immutable source references.
- **類**:StandardTemplateReconstructor
- **自測**:匯入型

### VRN_ENG267_TextOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/text_ops`(版本 1;現役 `text_ops.py`)
- **功能**:Deterministic bilingual text repair and analysis for arbitrary articles.
- **類**:TextProcessor
- **函式**(1):`chunk_text(text, max_chars, overlap)`
- **自測**:匯入型

### VRN_ENG268_Translation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/src/via_nlp_engine/translation`(版本 1;現役 `translation.py`)
- **功能**:Chunked translation with local memory and explicit, supported backends.
- **類**:TranslationMemory, TranslationService
- **自測**:匯入型

### VRN_ENG269_TestBundle
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test_bundle`(版本 1;現役 `test_bundle.py`)
- **功能**:無說明(候補)
- **類**:BundleReconstructionTests
- **自測**:主程式可跑

### VRN_ENG270_TestEngine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:TextProcessorTests, EngineTests, PersistenceTests
- **自測**:主程式可跑

### VRN_ENG271_TestKnowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test_knowledge`(版本 1;現役 `test_knowledge.py`)
- **功能**:無說明(候補)
- **類**:KnowledgeTests, TranslationTests
- **自測**:主程式可跑

### VRN_ENG272_TestMl
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test_ml`(版本 1;現役 `test_ml.py`)
- **功能**:無說明(候補)
- **類**:GovernedMLTests
- **自測**:主程式可跑

### VRN_ENG273_TestQuality
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test_quality`(版本 1;現役 `test_quality.py`)
- **功能**:無說明(候補)
- **類**:QualityMetricTests
- **自測**:主程式可跑

### VRN_ENG274_Test
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.5.0/tests/test`(版本 2;現役 `test_v15.py`)
- **功能**:無說明(候補)
- **類**:V15ReconstructionTests
- **自測**:主程式可跑

### VRN_ENG275_BuildRelease
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/scripts/build_release`(版本 1;現役 `build_release.py`)
- **功能**:Build and verify a deterministic release ZIP and SHA-256 manifest.
- **函式**(7):`sha256_file(path)` · `should_include(path)` · `source_files()` · `write_manifest(files)` · `build_archive(files)` · `verify_archive(files)` · `main()`
- **自測**:主程式可跑

### VRN_ENG276_RunTests
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/scripts/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:Run the dependency-free unit suite without requiring pytest.
- **函式**(1):`main()`
- **自測**:主程式可跑

### VRN_ENG277_Init
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA NLP One Engine public API.
- **自測**:匯入型

### VRN_ENG278_Main
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/__main__`(版本 1;現役 `__main__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG279_Adapters
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/adapters`(版本 1;現役 `adapters.py`)
- **功能**:Optional Tier 2-4 adapters, loaded only when invoked.
- **類**:OptionalNLPAdapters
- **函式**(1):`safe_extract_json(raw)`
- **自測**:匯入型

### VRN_ENG280_Api
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/api`(版本 1;現役 `api.py`)
- **功能**:FastAPI application factory. The API extra is optional.
- **類**:TokenBucketLimiter
- **函式**(1):`create_app(config_path, overrides)`
- **自測**:匯入型

### VRN_ENG281_Audit
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/audit`(版本 1;現役 `audit.py`)
- **功能**:Append-only JSONL audit log protected by a SHA-256 hash chain.
- **類**:AuditLogger
- **函式**(1):`redact_text(text)`
- **自測**:匯入型

### VRN_ENG282_BilingualOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/bilingual_ops`(版本 1;現役 `bilingual_ops.py`)
- **功能**:Conservative Chinese/English structural projection without invented translation.
- **函式**(4):`detect_language(text)` · `build_glossary(source_text)` · `bilingual_label(text, glossary)` · `decorate_mind_map(mind_map, source_text)`
- **自測**:匯入型

### VRN_ENG283_BundleOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/bundle_ops`(版本 1;現役 `bundle_ops.py`)
- **功能**:Deterministic multi-document intake and reconstruction package export.
- **函式**(2):`read_document_bundle(inputs, recursive, max_files, max_total_bytes, max_file_bytes)` · `export_reconstruction_package(output_directory, bundle, process_result)`
- **自測**:匯入型

### VRN_ENG284_Cache
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/cache`(版本 1;現役 `cache.py`)
- **功能**:Bounded SQLite cache and resumable job checkpoint store.
- **類**:SQLiteCache
- **自測**:匯入型

### VRN_ENG285_Cli
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface for local operation and testing.
- **函式**(2):`build_parser()` · `main(argv)`
- **CLI**:`--accepted` `--allow-network` `--backend` `--config` `--corrected-label` `--file` `--host` `--input` `--markitdown` `--max-chunk-chars` `--max-file-bytes` `--max-files`
- **自測**:主程式可跑

### VRN_ENG286_CodeReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/code_reconstruction`(版本 1;現役 `code_reconstruction.py`)
- **功能**:Static, non-executing reconstruction of code pasted across discussions.
- **類**:CodeDiscussionReconstructor
- **自測**:匯入型

### VRN_ENG287_CodeRestoration
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/code_restoration`(版本 1;現役 `code_restoration.py`)
- **功能**:Reviewable module templates reconstructed from static code evidence.
- **類**:CodeRestorer
- **自測**:匯入型

### VRN_ENG288_Config
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/config`(版本 1;現役 `config.py`)
- **功能**:Configuration loading, validation and path resolution.
- **函式**(2):`validate_config(config)` · `load_config(path, overrides)`
- **自測**:匯入型

### VRN_ENG289_ContextReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/context_reconstruction`(版本 1;現役 `context_reconstruction.py`)
- **功能**:Source-grounded reconstruction for disordered articles and conversations.
- **類**:ContextReconstructor
- **自測**:匯入型

### VRN_ENG290_CpuAugmentation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/cpu_augmentation`(版本 1;現役 `cpu_augmentation.py`)
- **功能**:Optional CPU-first NLP augmentation with deterministic safe fallbacks.
- **類**:CPUNLPAugmentor
- **函式**(2):`decode_bytes_with_cpu_detector(raw, min_confidence, use_available_provider)` · `provider_groups()`
- **自測**:匯入型

### VRN_ENG291_Discourse
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/discourse`(版本 1;現役 `discourse.py`)
- **功能**:CPU-first discourse reconstruction for fragmented conversations and articles.
- **類**:CPUHierarchicalTopicOrganizer
- **函式**(3):`infer_content_roles(text, kind)` · `build_refinement_ledger(processor, segments)` · `build_dialogue_flow(topics, segments)`
- **自測**:匯入型

### VRN_ENG292_DiscussionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/discussion_ops`(版本 1;現役 `discussion_ops.py`)
- **功能**:Evidence-first knowledge object reconstruction for noisy discussion records.
- **類**:DiscussionKnowledgeReconstructor
- **自測**:匯入型

### VRN_ENG293_Engine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/engine`(版本 1;現役 `engine.py`)
- **功能**:VIA NLP One Engine orchestration facade.
- **類**:VIAEngine
- **自測**:匯入型

### VRN_ENG294_Evaluation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/evaluation`(版本 1;現役 `evaluation.py`)
- **功能**:Gold-set quality metrics and candidate-only topic threshold calibration.
- **類**:TopicThresholdCalibrator
- **函式**(5):`precision_recall_f1(predicted, expected)` · `bcubed_scores(predicted, expected)` · `topic_labels(topics)` · `return_pairs(dialogue_flow)` · `evaluate_topic_output(topics, dialogue_flow, gold_topic_labels, gold_return_pairs)`
- **自測**:匯入型

### VRN_ENG295_FunctionClassifier
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/function_classifier`(版本 1;現役 `function_classifier.py`)
- **功能**:Evidence-first functional classification for statically extracted symbols.
- **類**:FunctionClassifier
- **自測**:匯入型

### VRN_ENG296_Ingest
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/ingest`(版本 1;現役 `ingest.py`)
- **功能**:Local, bounded extraction for common article and document formats.
- **類**:_HTMLTextExtractor
- **函式**(1):`read_local_document(path, max_bytes, use_markitdown)`
- **自測**:匯入型

### VRN_ENG297_InstructionOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/instruction_ops`(版本 1;現役 `instruction_ops.py`)
- **功能**:Evidence-first reconstruction of fragmented instructions and shell commands.
- **類**:InstructionReconstructor
- **自測**:匯入型

### VRN_ENG298_Jobs
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/jobs`(版本 1;現役 `jobs.py`)
- **功能**:Crash-resistant file queue for long-running batch work.
- **類**:JobQueue
- **函式**(1):`atomic_write_json(path, value)`
- **自測**:匯入型

### VRN_ENG299_Knowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/knowledge`(版本 1;現役 `knowledge.py`)
- **功能**:Lossless dialogue segmentation, knowledge reconstruction and code governance.
- **類**:RawSegment, LosslessSegmenter, CodeExtractor, KnowledgeBuilder
- **函式**(1):`SPACE_CLEAN(value)`
- **自測**:匯入型

### VRN_ENG300_KnowledgeBodyOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/knowledge_body_ops`(版本 1;現役 `knowledge_body_ops.py`)
- **功能**:Layered bilingual knowledge-body projection over immutable evidence registers.
- **函式**(1):`build_bilingual_knowledge_body(source_text, topics, knowledge_registry, instruction_registry, code_reconstruction)`
- **自測**:匯入型

### VRN_ENG301_LayoutAnalysis
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/layout_analysis`(版本 1;現役 `layout_analysis.py`)
- **功能**:Lossless Markdown-oriented layout analysis and NLP repair projection.
- **類**:MarkdownLayoutAnalyzer
- **CLI**:`---`
- **自測**:匯入型

### VRN_ENG302_Learning
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/learning`(版本 1;現役 `learning.py`)
- **功能**:Governed feedback loop and out-of-core text classifier evolution.
- **類**:FeedbackStore, GovernedClassifier
- **自測**:匯入型

### VRN_ENG303_MindmapEnrichment
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/mindmap_enrichment`(版本 1;現役 `mindmap_enrichment.py`)
- **功能**:Typed Mind Map enrichment for context, templates, layout and functions.
- **函式**(1):`enrich_mind_map_v15(mind_map, context_reconstruction, function_classification, template_reconstruction, layout_analysis)`
- **自測**:匯入型

### VRN_ENG304_MindmapEvolution
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/mindmap_evolution`(版本 1;現役 `mindmap_evolution.py`)
- **功能**:Append-only Mind Map snapshot comparison and reviewable correction proposals.
- **函式**(2):`load_previous_reconstruction(path)` · `build_mind_map_evolution(current_mind_map, previous, conflict_register)`
- **自測**:匯入型

### VRN_ENG305_ModelPool
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/model_pool`(版本 1;現役 `model_pool.py`)
- **功能**:Lazy model pool with TTL, LRU eviction and memory estimates.
- **類**:ModelEntry, LazyModelPool
- **自測**:匯入型

### VRN_ENG306_ProviderRegistry
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/provider_registry`(版本 1;現役 `provider_registry.py`)
- **功能**:Read-only registry for optional local development providers.
- **類**:LocalProviderRegistry
- **自測**:匯入型

### VRN_ENG307_Resources
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/resources`(版本 1;現役 `resources.py`)
- **功能**:Cross-platform resource monitoring and admission control.
- **類**:ResourcePressureError, ResourceMonitor, ResourceWatchdog
- **自測**:匯入型

### VRN_ENG308_Routing
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/routing`(版本 1;現役 `routing.py`)
- **功能**:Task-to-tier routing with deterministic pressure fallback.
- **類**:TaskRouter
- **自測**:匯入型

### VRN_ENG309_Schemas
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/schemas`(版本 1;現役 `schemas.py`)
- **功能**:Dependency-free request and response contracts.
- **類**:ProcessRequest, RouteDecision, ResourceSnapshot, ProcessResult, FeedbackRecord, BatchItem
- **自測**:匯入型

### VRN_ENG310_TableOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/table_ops`(版本 1;現役 `table_ops.py`)
- **功能**:Deterministic, provenance-first table recognition for noisy extracted text.
- **類**:StructuredTable, TextTableExtractor
- **自測**:匯入型

### VRN_ENG311_TemplateReconstruction
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/template_reconstruction`(版本 1;現役 `template_reconstruction.py`)
- **功能**:Standard template reconstruction around immutable source references.
- **類**:StandardTemplateReconstructor
- **自測**:匯入型

### VRN_ENG312_TextOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/text_ops`(版本 1;現役 `text_ops.py`)
- **功能**:Deterministic bilingual text repair and analysis for arbitrary articles.
- **類**:TextProcessor
- **函式**(1):`chunk_text(text, max_chars, overlap)`
- **自測**:匯入型

### VRN_ENG313_Translation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/src/via_nlp_engine/translation`(版本 1;現役 `translation.py`)
- **功能**:Chunked translation with local memory and explicit, supported backends.
- **類**:TranslationMemory, TranslationService
- **自測**:匯入型

### VRN_ENG314_TestBundle
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test_bundle`(版本 1;現役 `test_bundle.py`)
- **功能**:無說明(候補)
- **類**:BundleReconstructionTests
- **自測**:主程式可跑

### VRN_ENG315_TestEngine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:TextProcessorTests, EngineTests, PersistenceTests
- **自測**:主程式可跑

### VRN_ENG316_TestKnowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test_knowledge`(版本 1;現役 `test_knowledge.py`)
- **功能**:無說明(候補)
- **類**:KnowledgeTests, TranslationTests
- **自測**:主程式可跑

### VRN_ENG317_TestMl
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test_ml`(版本 1;現役 `test_ml.py`)
- **功能**:無說明(候補)
- **類**:GovernedMLTests
- **自測**:主程式可跑

### VRN_ENG318_TestQuality
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test_quality`(版本 1;現役 `test_quality.py`)
- **功能**:無說明(候補)
- **類**:QualityMetricTests
- **自測**:主程式可跑

### VRN_ENG319_Test
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_b283/VIA_NLP_OneEngine_v1.6.1/tests/test`(版本 4;現役 `test_v161.py`)
- **功能**:無說明(候補)
- **類**:StubProcessor, V161LayoutSegmentationTests, V161CodeFragmentTests, V161TopicNoiseTests
- **自測**:主程式可跑

### VRN_ENG320_BuildRelease
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/scripts/build_release`(版本 1;現役 `build_release.py`)
- **功能**:Build and verify a deterministic release ZIP and SHA-256 manifest.
- **函式**(7):`sha256_file(path)` · `should_include(path)` · `source_files()` · `write_manifest(files)` · `build_archive(files)` · `verify_archive(files)` · `main()`
- **自測**:主程式可跑

### VRN_ENG321_RunTests
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/scripts/run_tests`(版本 1;現役 `run_tests.py`)
- **功能**:Run the dependency-free unit suite without requiring pytest.
- **函式**(1):`main()`
- **自測**:主程式可跑

### VRN_ENG322_Init
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/__init__`(版本 1;現役 `__init__.py`)
- **功能**:VIA NLP One Engine public API.
- **自測**:匯入型

### VRN_ENG323_Main
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/__main__`(版本 1;現役 `__main__.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG324_Adapters
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/adapters`(版本 1;現役 `adapters.py`)
- **功能**:Optional Tier 2-4 adapters, loaded only when invoked.
- **類**:OptionalNLPAdapters
- **函式**(1):`safe_extract_json(raw)`
- **自測**:匯入型

### VRN_ENG325_Api
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/api`(版本 1;現役 `api.py`)
- **功能**:FastAPI application factory. The API extra is optional.
- **類**:TokenBucketLimiter
- **函式**(1):`create_app(config_path, overrides)`
- **自測**:匯入型

### VRN_ENG326_Audit
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/audit`(版本 1;現役 `audit.py`)
- **功能**:Append-only JSONL audit log protected by a SHA-256 hash chain.
- **類**:AuditLogger
- **函式**(1):`redact_text(text)`
- **自測**:匯入型

### VRN_ENG327_Cache
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/cache`(版本 1;現役 `cache.py`)
- **功能**:Bounded SQLite cache and resumable job checkpoint store.
- **類**:SQLiteCache
- **自測**:匯入型

### VRN_ENG328_Cli
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/cli`(版本 1;現役 `cli.py`)
- **功能**:Command-line interface for local operation and testing.
- **函式**(2):`build_parser()` · `main(argv)`
- **CLI**:`--accepted` `--allow-network` `--backend` `--config` `--corrected-label` `--file` `--host` `--max-chunk-chars` `--port` `--predicted-label` `--promote` `--quality`
- **自測**:主程式可跑

### VRN_ENG329_Config
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/config`(版本 1;現役 `config.py`)
- **功能**:Configuration loading, validation and path resolution.
- **函式**(2):`validate_config(config)` · `load_config(path, overrides)`
- **自測**:匯入型

### VRN_ENG330_Discourse
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/discourse`(版本 1;現役 `discourse.py`)
- **功能**:CPU-first discourse reconstruction for fragmented conversations and articles.
- **類**:CPUHierarchicalTopicOrganizer
- **函式**(3):`infer_content_roles(text, kind)` · `build_refinement_ledger(processor, segments)` · `build_dialogue_flow(topics, segments)`
- **自測**:匯入型

### VRN_ENG331_Engine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/engine`(版本 1;現役 `engine.py`)
- **功能**:VIA NLP One Engine orchestration facade.
- **類**:VIAEngine
- **自測**:匯入型

### VRN_ENG332_Ingest
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/ingest`(版本 1;現役 `ingest.py`)
- **功能**:Local, bounded extraction for common article and document formats.
- **類**:_HTMLTextExtractor
- **函式**(1):`read_local_document(path, max_bytes)`
- **自測**:匯入型

### VRN_ENG333_Jobs
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/jobs`(版本 1;現役 `jobs.py`)
- **功能**:Crash-resistant file queue for long-running batch work.
- **類**:JobQueue
- **函式**(1):`atomic_write_json(path, value)`
- **自測**:匯入型

### VRN_ENG334_Knowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/knowledge`(版本 1;現役 `knowledge.py`)
- **功能**:Lossless dialogue segmentation, knowledge reconstruction and code governance.
- **類**:RawSegment, LosslessSegmenter, CodeExtractor, KnowledgeBuilder
- **函式**(1):`SPACE_CLEAN(value)`
- **自測**:匯入型

### VRN_ENG335_Learning
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/learning`(版本 1;現役 `learning.py`)
- **功能**:Governed feedback loop and out-of-core text classifier evolution.
- **類**:FeedbackStore, GovernedClassifier
- **自測**:匯入型

### VRN_ENG336_ModelPool
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/model_pool`(版本 1;現役 `model_pool.py`)
- **功能**:Lazy model pool with TTL, LRU eviction and memory estimates.
- **類**:ModelEntry, LazyModelPool
- **自測**:匯入型

### VRN_ENG337_Resources
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/resources`(版本 1;現役 `resources.py`)
- **功能**:Cross-platform resource monitoring and admission control.
- **類**:ResourcePressureError, ResourceMonitor, ResourceWatchdog
- **自測**:匯入型

### VRN_ENG338_Routing
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/routing`(版本 1;現役 `routing.py`)
- **功能**:Task-to-tier routing with deterministic pressure fallback.
- **類**:TaskRouter
- **自測**:匯入型

### VRN_ENG339_Schemas
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/schemas`(版本 1;現役 `schemas.py`)
- **功能**:Dependency-free request and response contracts.
- **類**:ProcessRequest, RouteDecision, ResourceSnapshot, ProcessResult, FeedbackRecord, BatchItem
- **自測**:匯入型

### VRN_ENG340_TextOps
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/text_ops`(版本 1;現役 `text_ops.py`)
- **功能**:Deterministic bilingual text repair and analysis for arbitrary articles.
- **類**:TextProcessor
- **函式**(1):`chunk_text(text, max_chars, overlap)`
- **自測**:匯入型

### VRN_ENG341_Translation
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/src/via_nlp_engine/translation`(版本 1;現役 `translation.py`)
- **功能**:Chunked translation with local memory and explicit, supported backends.
- **類**:TranslationMemory, TranslationService
- **自測**:匯入型

### VRN_ENG342_TestEngine
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/tests/test_engine`(版本 1;現役 `test_engine.py`)
- **功能**:無說明(候補)
- **類**:TextProcessorTests, EngineTests, PersistenceTests
- **自測**:主程式可跑

### VRN_ENG343_TestKnowledge
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/tests/test_knowledge`(版本 1;現役 `test_knowledge.py`)
- **功能**:無說明(候補)
- **類**:KnowledgeTests, TranslationTests
- **自測**:主程式可跑

### VRN_ENG344_TestMl
- **族**:`functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1.1.0/tests/test_ml`(版本 1;現役 `test_ml.py`)
- **功能**:無說明(候補)
- **類**:GovernedMLTests
- **自測**:主程式可跑

### VRN_ENG345_PDFPlumberPlusEngine
- **族**:`functional modules/VRN/references/intake/VIA_PDFPlumberPlusEngine_v1.0.0/VIA_PDFPlumberPlusEngine`(版本 1;現役 `VIA_PDFPlumberPlusEngine.py`)
- **功能**:無說明(候補)
- **類**:_Triage, _DigitalExtractor, _ScannedExtractor, _Emitter, PDFPlumberPlusEngine
- **CLI**:`---` `--json-only` `--no-html` `--no-ocr` `--no-structure` `--out` `--scan-dir` `--selftest` `--threads`
- **自測**:✅ --selftest

### VRN_ENG346_VRNLogicAllInOne
- **族**:`functional modules/VRN/references/intake/VIA_VRNLogic_AllInOne_v0201_b504/VIA_VRNLogic_AllInOne`(版本 1;現役 `VIA_VRNLogic_AllInOne_v0201.py`)
- **功能**:VIA / VRN report logic engine — all-in-one edition.
- **函式**(12):`clamp_confidence(value)` · `normalize_text(value)` · `is_missing(value)` · `stable_json(value, pretty)` · `stable_digest(value)` · `sha256_file(path)` · `source_priority(source)` · `atomic_write_text(path, text, encoding)` · `atomic_write_csv(path, rows, columns)` · `tokenize_filename(filename)`
- **CLI**:`--acceptance-test` `--compare-contract` `--formats` `--input` `--inspect-contract` `--install` `--output-dir` `--pretty` `--project-relative` `--repo-root` `--report-root` `--selftest`
- **自測**:✅ --selftest

### VRN_ENG347_VRNFirstPageEngine2
- **族**:`functional modules/VRN/references/intake/VIA_VRN_FirstPageEngine_v0101_b522/VIA_VRN_FirstPageEngine_2`(版本 1;現役 `VIA_VRN_FirstPageEngine_2.py`)
- **功能**:VIA_VRN_FirstPageEngine  v0101
- **類**:TickerFilename, Layout, TableGeometry, NLPRepair, FinancialValidation, PriceAdjustment, BrokerRatingDict, FieldValidation, CrossValidation, FirstPageEngine
- **函式**(1):`load_ssot_blocks(ssot_path)`
- **自測**:主程式可跑

### VRN_ENG348_VRNUnifiedReportEngine
- **族**:`functional modules/VRN/references/intake/VIA_VRN_UnifiedReportEngine_v0100_b492/VIA_VRN_UnifiedReportEngine`(版本 1;現役 `VIA_VRN_UnifiedReportEngine_v0100.py`)
- **功能**:VIA_VRN_UnifiedReportEngine v0100
- **類**:EngineConfig, ListingRecord, PageEvidence, FinancialObservation, ReportResult, OfficialListingResolver, FilenameEngineAdapter, DocumentPageExtractor, UnifiedReportEngine
- **函式**(12):`def_now_iso()` · `def_nfkc(value)` · `def_compact_text(value)` · `def_normalize_compare(value)` · `def_json(value, max_chars)` · `def_stable_id(prefix)` · `def_file_sha256(path, chunk_size)` · `def_version_key(path)` · `def_find_latest_module(explicit, module_dir, pattern)` · `def_load_module(path, logical_name)`
- **CLI**:`--allow-web-official` `--csv` `--dry-run` `--duckdb` `--financial-page-score` `--firstpage-engine` `--firstpage-text` `--html` `--in` `--json` `--json-stdout` `--max-pages`
- **自測**:主程式可跑

### VRN_ENG349_OmniFormatIntelligenceEngine
- **族**:`functional modules/VRN/references/intake/Veritas_OmniFormat_Intelligence_Engine_v0140_FINAL_b245/Veritas_OmniFormat_Intelligence_Engine_v0140/Veritas_OmniFormat_Intelligence_Engine`(版本 1;現役 `Veritas_OmniFormat_Intelligence_Engine.py`)
- **功能**:Veritas OmniFormat Intelligence Engine (VOFIE) v1.4.0.
- **類**:VOFIEError, SourceRecord, CodeUnit, TopicBlock, QuarantineItem, UniversalContentIR, EngineOptions, RecoveryContext, RecoveryActionResult, SemanticHTMLParser, VeritasOmniFormatEngine
- **函式**(12):`utc_now()` · `blake2s_bytes(data)` · `blake2s_text(text)` · `stable_id(prefix)` · `natural_key(value)` · `canonical_text(text)` · `ensure_new_output_dir(path)` · `atomic_write_text(path, content)` · `atomic_write_bytes(path, content)` · `file_snapshot(path)`
- **CLI**:`---` `--approval-token` `--check` `--execute-safe` `--file` `--formats` `--functions` `--language` `--max-topic-chars` `--no-quarantine` `--no-vsis` `--operations`
- **自測**:主程式可跑

### VRN_ENG350_HydraRiskMarker
- **族**:`functional modules/VRN/references/intake/Veritas_OmniFormat_Intelligence_Engine_v0140_FINAL_b245/Veritas_OmniFormat_Intelligence_Engine_v0140/tests/fixtures/hydra_risk_marker`(版本 1;現役 `hydra_risk_marker.py`)
- **功能**:無說明(候補)
- **自測**:匯入型

### VRN_ENG351_TestVofie
- **族**:`functional modules/VRN/references/intake/Veritas_OmniFormat_Intelligence_Engine_v0140_FINAL_b245/Veritas_OmniFormat_Intelligence_Engine_v0140/tests/test_vofie`(版本 1;現役 `test_vofie.py`)
- **功能**:無說明(候補)
- **類**:VOFIEContractTests, VOFIEPipelineTests
- **CLI**:`--check` `--self-test`
- **自測**:主程式可跑

### VRN_ENG352_GeminicodeDocHierarchyB236
- **族**:`functional modules/VRN/references/intake/geminicode_doc_hierarchy_b236`(版本 1;現役 `geminicode_doc_hierarchy_b236.py`)
- **功能**:無說明(候補)
- **函式**(1):`build_document_hierarchy(pdf_path)`
- **自測**:匯入型

### VRN_ENG353_GeminicodeRepairPdfTextB236
- **族**:`functional modules/VRN/references/intake/geminicode_repair_pdf_text_b236`(版本 1;現役 `geminicode_repair_pdf_text_b236.py`)
- **功能**:無說明(候補)
- **函式**(1):`repair_pdf_text(pdf_path, title_size_threshold)`
- **自測**:匯入型
