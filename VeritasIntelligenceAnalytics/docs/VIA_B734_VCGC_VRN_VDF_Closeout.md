# 批734 — VCGC 對 VRN / VDF 的進度盤點與收尾

> 操作員令:「VCGC 開始對 VRN VDF 在進行的進度掌握而協助進行收尾」
> 基底:main 89e1ff90(批733)。本境 = 雲端容器(無工作站樣本夾、無 rich/pdfplumber/pydantic、同意閘未開)。

## 一、VCGC 一眼看(`via-vcgc status` → 兩個子系統管理器 → 兩條鏈跑器)

| | 盤點前 | 本批做了什麼 | 盤點後 |
|---|---|---|---|
| **VRN 管理器** | RED(邏輯格紅 · 連結紅 2) | 邏輯索引冊重建(紅因是我自己切 ENG086 v0117 讓冊指到舊版) | **GREEN**(205 綠 · NODATA 1 · ABSENT 1) |
| **VRN 鏈** | 30 綠 · **紅 3** · 無資料 12 | ENG072 v0138、ENG068 v0107:缺件/缺存證改誠實 SKIP | 31 綠 · **紅 1**(資料缺口,見 Z207) |
| **VDF 管理器** | STALE/NODATA(STALE 2 · NODATA 1) | 卡書重建(8→7);鏈跑補存證 | STALE 2(兩件都要你裁,見 Z208/Z209) |
| **VDF 鏈** | 無存證(NODATA) | 真跑七站 | **綠 9 · 紅 0** · 等同意閘 1 |

## 二、本批修掉的

1. **VRN_ENG072 v0138**:自測 ⑪ 在沒有 pdfplumber 的境判 FAIL(抽法在碰檔前就回 None)。缺件=SKIP 並講明,有件的境照原判準。自測 55 綠 · 0 紅 · 1 SKIP。
2. **VRN_ENG068 v0107**:自測 ① 在沒有格子存證的新境拿 ok=0 比 ≥110 判 FAIL;同一檢對金字塔缺存證早就判 SKIP——同一函式兩把尺。改成同律。自測 6 綠 · 0 紅 · 3 SKIP。
3. **VRN 邏輯索引冊**:版號一動就過期,按守門指示 `build` 重建(產物,不手改)→ 51/51 在位且尾版。
4. **VDF 卡書**:`via-peis scan --family vdf` + `book` 重建(45→46 張,省 98.6%)。
5. **掉球 G 結案**:VRN_MDL 數量同一把尺重量(數字表見掉球冊)。

## 三、還開著、要你的手(我不代做)

| 代號 | 事 | 下一步 |
|---|---|---|
| Z207 | VRN 最後一紅:`tw_trading_daily` 缺 **2026-09-23**(前後兩天都有),AdjOracle 對不到最新日 | 開同意閘補這一天;另請裁「增量閘要不要驗日期連續」——它這次是綠的,沒看出中間缺一天 |
| Z208 | VDF 卡書範圍與管理器不同(只掃 `engine/`、收了 candidates/) | 二選一,本線建議擴 PEIS vdf 範圍 |
| Z209 | `VeritasCeleritas.py` 三份不一致(正典合規、兩份舊的帶 talib 路徑) | 舊兩份退役與否(批345 不可動,AI 不同步) |
| — | VDF 網路站 GATED | `$env:VIA_NET_CONSENT='YES'` 後 `via-vdfchain run --resume` |
| — | VRN 引擎面 NODATA/ABSENT | 樣本夾 `C:\測試樣本報告` 只在工作站;在工作站跑 `via-vrnchain run` |

掉球冊開放總數:VRN/VDF 相關 AI 可做 8 件 → 結 1(G);其餘多數需網路、樣本或裁定。

## 四、本批自己的錯

- 盤點時才發現批708(本 PR 原內容)動到兩支加速器工具本體,違反批345 不可動律 → 6 檔還原(詳 VIA_B734_FixShadowedDefinitions.md)。
- 鏈跑器會順手改寫 `VIA_Engine_Consolidation_Register_v0100.json`(已追蹤)——每跑一次都還原,不隨本批提交。
