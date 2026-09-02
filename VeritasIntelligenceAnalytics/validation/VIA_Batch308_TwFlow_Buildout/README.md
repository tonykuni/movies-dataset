# 批308 — 台股流分析建置波(七問令)

操作員令(2026-09-02,七問):①VDF 美國總經/匯率/國債/聯準會/財政收支盤點+細值抓取;
②ETF 各區各類 AUM/CASH INFLOW OUTFLOW 可算;③台股族群清單整理驗證;
④降低台股大盤連動(成交值扣台積電扣當沖=基準動態參數,分大中小型);
⑤外資/內資主導判定;⑥Lead-Lag 四分類(LEADER/PEER/LAGGER/不相關);
⑦月營收整體+族群異常值(低基期不算);VDF 擷取分 TWSE/TPEX。

## 件冊

| 件 | 角色 |
|---|---|
| `batch308_group_verify.py` | 族群冊七檢(三官方名錄實連,快照回落誠實標源) |
| `batch308_group_correct.py` | 族群冊官方機械改正(v0110→v0111;留痕不刪) |
| `batch308_uimatrix_render.py` | U/I Matrix 渲染器(零手寫數字) |
| `Batch308_GroupVerify_Results.json` | 族群驗證機讀結果 |
| `VIA_Batch308_TwFlow_UIMatrix_v0100.html` | 七問答覆矩陣報告(Chromium 截圖驗收) |
| `*_snapshot_20260902.json` ×3 | 官方名錄證跡(上市/上櫃/興櫃) |

## 本波新建/擴充引擎(FlowSystem_v2/engines)

- `FLOW_ENG025_FlowUsMacroOpenData`(新):美國總經四免鑰官方道(NY Fed 利率
  /FiscalData 財政收支+國債細分/財政部殖利率全期限)+五幣 FX → macro_data v2
  長表;補 VDF 冊財政收支零筆缺口。六檢。
- `FLOW_ENG026_FlowTwBaseline`(新):B=(TWSE+TPEx 成交值)−台積電−當沖(買+賣)/2;
  動態參數(滾動 z/百分位)、市值分層(前50/51-150/其餘)、外資參與率主導判定、
  去連動評估。八檢。TWSE 當沖/法人遭雲端 WAF 封鎖=工作站 --ingest 道。
- `FLOW_ENG027_FlowTwMonthlyRevenue`(新):上市+上櫃月營收;低基期律
  s=去年當月/(去年月均)、θ_low=P25 算出;穩健 z 異常榜;族群聚合。八檢。
- `FLOW_ENG020_FlowLeadlag`(擴):classify_nodes 四分類+顯著性閘
  max(0.05, 2.5/√n)+市場透傳。六檢。
- `FLOW_ENG023_FlowTwActiveEtf`(擴):--ingest-openapi 官方單位數×收盤(NAV
  代理)→ 台主動 32 檔 AUM/流 COMPUTABLE。
- `SUP_MDL737 v0104`:fetch gzip 壓縮道(大檔官方節流 60s→13s)。

## 本波真值(2026-09-02)

- 基準 B=1,246,919,758,824(2026-09-01;台積電占 5.4%、當沖占 8.0%[TPEx 側])
- 台主動 ETF AUM 合計 ≈9,671.5 億(32 檔;統一台股增長 2,898.6 億居冠)
- 月營收 11507:1969 家;θ_low=0.914 剔 391 家低基;異常 60;記憶體群 +397.75%
- 美國總經長表:29 序列 2,388 值(FISCAL_US* 首收)
- 族群冊:22 檔市場歸屬官方改正(v0111);4 疑義標旗候操作員定奪

誠實界線:TWSE T86/BFI82U/TWTB4U 雲端 IP 遭 WAF 封鎖候工作站波;全球宇宙
AUM 免費官方端點無=候餵;滾動值樣本 <8 誠實不出。
