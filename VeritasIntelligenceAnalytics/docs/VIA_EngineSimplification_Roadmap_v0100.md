# VIA 引擎簡化工程 Roadmap(操作員交付正典;批179 原文照錄)
> 操作員令:未使用引擎盤點整併——網路工具凍結不可動(SUP_MDL740/741/VIA_NetSupport);
> 其餘同功能引擎在不傷原有能力前提下整併優化。
> Guardrails:不 big bang(單策略單市場先行)/保留舊引擎直通回退/分層不混寫/每邊界獨立測試+回放。

## Overall roadmap (5 Phases)
| Phase | Goal | Main tools | Key risks | Mitigations |
|---|---|---|---|---|
| 1 | Data & schema foundation | Pandas, Polars, DuckDB, Pydantic | Schema drift, hidden data issues | Strict contracts, validation, test datasets |
| 2 | Feature layer consolidation | TA-Lib, Featuretools, Scikit-Learn, DuckDB | Feature explosion, leakage | Central Feature Store, access rules, audits |
| 3 | Engine modularization | FastAPI, Pydantic, Hydra | Over-fragmentation, latency | Clear engine boundaries, local calls, profiling |
| 4 | Pipeline & orchestration | Prefect / Dagster / Airflow | Orchestration complexity | Start minimal, one pipeline, then expand |
| 5 | Governance & observability | Git, Prometheus, Grafana | Silent failures, version chaos | Strict versioning, dashboards, alerts |

## Phase 1:Data & schema foundation
- Engine contract:統一 load / transform / evaluate / emit 介面(Single engine interface)
- Schema registry:Pandas/Polars profiling+DuckDB+Pydantic schema definitions
- Risk=Schema drift(新引擎偷加欄位)→ 所有引擎 I/O 必經 Pydantic 驗證+DuckDB schema check

## Phase 2:Feature layer consolidation
- Central Feature Store(TA-Lib 技術特徵/Featuretools 自動衍生/Scikit-Learn transforms/DuckDB 儲存)
- Risk=Feature explosion/leakage → 嚴分原始/衍生/模型特徵;每特徵必有來源、用途、依賴、版本

## Phase 3:Engine modularization
- Flow/Regime/Momentum 等引擎標準化可替換(FastAPI endpoint+Pydantic I/O+Hydra config)
- Risk=Over-fragmentation/latency → 僅邏輯邊界清晰者 API 化;同進程 local call;定期 profiling 砍不必要拆分

## Phase 4:Pipeline & orchestration
- 單一交易管線主幹:Preprocess → Feature → Factor → Decision → Execution(Prefect/Dagster;Airflow 僅排程)
- Risk=DAG 複雜 → 先最小可用管線(單市場單策略);每 stage 限引擎數;可視化 DAG 監依賴

## Phase 5:Governance & observability
- Git tag+config version 綁定;Prometheus/Grafana;延遲/錯誤率/輸出分佈/feature 使用率
- Risk=Silent failures → 關鍵指標閾值告警(signal 分佈異常、factor 全 0/NaN)

## Risk-focused guardrails
- Avoid big bang refactor:一條策略一個市場先導入,再逐步擴展
- Keep fallback path:新管線保留舊引擎直通模式回退
- Strictly separate concerns:資料/特徵/引擎/管線/治理層不混寫
- Test at each boundary:每 engine、每 stage 獨立測試+回放(replay)機制
