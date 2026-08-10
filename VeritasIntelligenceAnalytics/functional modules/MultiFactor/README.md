# VIA MultiFactor Resonance SSOT Workbench — 全球多因子共振驗證與金融事件 SSOT 工作台

2026-08-10 歸檔。方法論全文見 `docs/VIA_MF_Handover_20260807.md`(交接報告 SSOT,
E01-E14 引擎分層 · 十表 schema · R0-R6 共振分級 · 模型准入規則 · 峰法推論改善原則)。

## 內容

| 位置 | 內容 |
|---|---|
| `engines/` | 引擎 v0100 + 測試套件 + **SHA256 manifest(歸檔時逐檔驗證通過,四檔原樣零補丁)** + Invoke ps1 啟動器 |
| `runs/RUN_20260807_105152_…/` | 2026-08-07 原始運行證據(summary/報告/factor·simulation 帳本/ALL_TESTS_PASS)— append-only 不可再生,故入版控 |
| `runs/vap_views/` | 帳本 → VAP 圖庫渲染例(增量解釋力 hbar) |
| `docs/` | 交接報告方法論全文 |
| `mf_params.json` | master 動詞參數檔(引擎一階段) |
| `_generated/` | 新 run 落地處(gitignored 可再生) |

## 執行

```powershell
# 引擎(經 workflow master;--ssot 指向 repo 內治理模板,--out-base 落 _generated)
.\VeritasIntelligenceAnalytics\VIA_WorkflowEngine.ps1 master "VeritasIntelligenceAnalytics\functional modules\MultiFactor\mf_params.json"

# 或原生 ps1 啟動器(操作員機)
.\VeritasIntelligenceAnalytics\functional modules\MultiFactor\engines\InvokeVIAMultiFactorTestValidateSimv0100.ps1
```

測試套件硬編碼自 `/mnt/data` 載入引擎(manifest 保真故未補丁);Linux 容器以
symlink 佈署後執行:`mkdir -p /mnt/data && ln -s <engines>/VIA_MultiFactor_…py /mnt/data/`。

## 本容器驗收(2026-08-10)

- SHA256 manifest:引擎 `615403f1…`、測試 `116de8e5…` **逐檔驗證通過**
- 測試套件:**ALL_TESTS_PASS**(與上傳之 2026-08-07 結果檔逐字一致)
- 引擎實跑:`RUN_20260810_161508` 全帳本 + index.html 落地,`high_confidence_engine_execution: true`
- 帳本 × VAP:factor_relation_ledger.csv 直入 VAP 資料層出圖(見 runs/vap_views/)

## 缺席與注意

- `VIA_Console (2).html`(交接報告 §16 提及之 Console 外殼)未在上傳批次 — 到位後歸檔於此
- 治理:引擎輸出一律 `*_NotConfirmed` / `Estimated_Model`(投影不得 Confirmed);
  allow=2 · monitor/regime_specific=7 為 T4 合成面板結果,**不得作為實盤依據**
