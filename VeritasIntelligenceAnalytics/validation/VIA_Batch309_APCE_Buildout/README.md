# 批309 — APCE 自適應完美分類引擎落地(參數家族 × 三加權指數 × 2D 價量 × 指標庫 MATRIX)

操作員令(2026-09-02,設計稿全文):Type-F/D/H 參數分家「一個家」;Attention Share
第一道輸入;三加權族群指數(T-1 無前視/權重上限/鏈結);Price RS;半動態不失敏;
2D 價量同動;K 線重心實質淨流;籌碼風格;信用當沖;Z 跨群修正;角色雙重條件+遲滯;
PC1 吸收率探索/指數分級;C-15/C-16 生命週期;三策略訊號;指標庫一類一類 MATRIX。
稿為 Polars——本波以標準庫自算(倉庫零硬依賴律),每模組附合成自檢。

## 件冊

| 件 | 角色 |
|---|---|
| `GroupIndex/flow_simulation_v0400/ssot/VIA_FLOWROT_Method_Thresholds_v0400.json` | 門檻冊 v0400:C-01~C-14 分家+新增 C-01b/C-02b/C-09b/C-15~C-22;鎖觸 L1–L5;v0300 不動 |
| `FlowSystem_v2/engines/FLOW_ENG028_FlowParamFamily.py` | 參數家族解析器:F 固定→D 滾動→H 條件鎖;加速視窗;校準族譜。八檢 |
| `FlowSystem_v2/engines/FLOW_ENG029_FlowApce.py` | APCE 引擎本體(39 項指標 registry)。十檢 |
| `FlowSystem_v2/engines/FLOW_ENG030_FlowTwPanel.py` | 149 成員真實面板道(Yahoo 歷史+官方當日快照+官方股數)。六檢 |
| `batch309_uimatrix_render.py` → `VIA_Batch309_APCE_UIMatrix_v0100.html` | 指標庫 MATRIX+參數家族+族群指數/健康+角色榜/訊號+面板覆蓋 |

## 用法

```
python3 FLOW_ENG028_FlowParamFamily.py --family            # 參數家族冊
python3 FLOW_ENG029_FlowApce.py --selftest                 # 十檢
VIA_NET_CONSENT=YES python3 FLOW_ENG030_FlowTwPanel.py --build   # 面板(同意閘)
python3 FLOW_ENG030_FlowTwPanel.py --run                   # 實跑 → data/output/apce_latest.json
python3 batch309_uimatrix_render.py                        # 矩陣頁
```

## 稿→實作之修正(自檢證得,誠實記)

- 聚焦權重上限:稿對「原始 AS」clip 0.18 實為 no-op(AS 為全市場占比,量級 10⁻³)——
  改為對「族群內正規化權重」迭代封頂(指數業界法);n×0.18<1 之小族群數學不可行⇒等權退場(記錄)。
- 遲滯:單閾 EWM3>0.5 於「長期 1 後單日 0」恰等於 0.5(邊界失格);改雙閾值真遲滯
  ≥0.7 入/≤0.3 出/中間維持——帶寬須含 1/0 交替穩態 [.333,.667] 方不擺盪(C-19)。
- 分層 rolling_quantile.over("date")/群中位 rolling_median.over([sector,date]) 皆為
  Polars 語意退化——改為每日橫截面分位/中位(稿之本意)。
- 指數用 PCA 門檻與探索門檻分開(C-01b=0.55 憲法);LEADER=族群前 20%∧複合分≥C-05
  ∧價同動過閘∧rs_mom>0(相對+絕對雙重)。

## 本波真值(2026-09-03;145 檔 × 165 日)

見矩陣頁丙/丁節。誠實界線:成交值歷史=量×收盤 PROXY(官方值到日覆蓋);TWSE 個股當沖/
法人/融資遭雲端 WAF 封鎖候工作站 --ingest(籌碼/信用模組本波 SKIP);多數族群 3–4 檔
受 C-16 有效成員 ≥5 律判 REMOVE——族群冊擴員為前提。
