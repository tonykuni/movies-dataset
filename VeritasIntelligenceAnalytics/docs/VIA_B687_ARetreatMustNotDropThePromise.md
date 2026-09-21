# 批687 · 早退分支不准把承諾一起退掉 —— ENG090 ㉔ 四態全帶「不代設」(Z80)· 開機自補逐件退路(Z81)· Z79 工作站實錄結案

操作員令:「依你建議進行 · 關」。三件:關 PR #57、接 Z80/Z81、把你的工作站實錄寫進 Z79 結案。
批號 687:680–686 都已被用掉(680 前一會期 Z57;681–686 awesome-bardeen 線;682B 本線),LL334 掃過全部遠端分支。
本線起點 main 08f76a0d(PR #60:批683/684/685 併入;Grid 尾版 v0435、VCGC 尾版仍是本線的 v0119)。

## 一 · Z80 · VDF_ENG090 v0105

| 量到 | 修 | 驗 |
|---|---|---|
| `roster()` 初始 `out.note` 寫「同意閘是操作員的手」,**沒有「不代設」三個字**;那三個字只在走完全程的 OK/NODATA 尾段才被接上。四條早退分支(名冊缺 / duckdb 缺 / 正典庫不在 / `tw_daily_prices` 缺)一走,㉔ 的 `"不代設" in note+why` 就假 | 初始 `out.note` 就帶「本閘不代設」,四態全帶;引擎行為零變更 | ㉔ OK;+㉕ 合成 ABSENT:把模組層 `MEGA_DB` 指到暫存夾裡不存在的檔 → state ABSENT · why 非空 · note 帶「不代設」· by_market 是 dict;**24 檢 OK 24** |

批682B 容器第一輪這一站紅、補料後綠——那不是修好,是不再走那條路。承諾(不代設)要跟著每一條路走出去,不是只跟著成功的那條。

## 二 · Z81 · `via_boot_update.sh` ⓪ 環境自補(無版號檔,就地改;L04)

| 量到 | 修 | 驗 |
|---|---|---|
| 新容器第一次開機:`pip install -r VIA_Env_Requirements_v0100.txt` 因 jieba 在 Debian setuptools 68 / wheel 0.42 建輪失敗(`install_layout`),pip 把**整份**放棄 → 29 條 `No module named duckdb/pandas`,OmniFetch 15 車道全假敗,收尾 GREY | 整份 rc≠0 → 逐件裝;一件失敗再試 `--use-pep517`;還是失敗只列名,不放棄其餘。覆寫鍵 `VIA_ENV_REQ` 只給合成檢,真機器不設 | `bash -n` 過;把 PYENV 段抽出來以 `VIA_ENV_REQ=`(bogus + jieba)真跑:`整份補裝 rc=1 → 逐件補裝 2 件 · 失敗 1:no-such-pkg-zz9-b687`,jieba 過 |

明天容器首開的 `BOOT_*.log` ⓪ 段會是這一批的第一次真機驗證。

## 三 · Z79 結案實錄(操作員工作站,main b45c9380,v0119)

```
registry-sync  PLAN · 活元件 5991 · 新 0 · 變更 0 · 退役 0
--selftest     二十五檢 OK 25 · FAIL 0
⑬             ACTIVE 5991/5991 · runtime 另列 1        ← 工作站有 TOOLS_PLAN,那個虛境被看見、被列出、不進等式
㉕             rows 有檔 5991 / 無檔 5991 · plan 新 0
```

同一支 v0119 在容器印「runtime 另列 0」,兩邊等式都成立。批681/682/682B 三次互翻到此為止。

## 四 · 三線現況(本批起點)

| 線 | 狀態 |
|---|---|
| main 08f76a0d | PR #60 併入 awesome-bardeen 批683/684/685;掉球到 Z86;台帳 1285 |
| awesome-bardeen | 批686 在分支上(六層鏈跑器 rc≠0 先印 [FAIL]) |
| busy-bell(PR #53) | 對 main 領先 14 · 落後 6;它的 CGC_MDL149 **v0119 撞號**(內容不同;awesome-bardeen 已登 Z86)→ 要改 v0120 疊在 main 的 v0119 上;操作員轉告 |
| PR #57 | **已關**(內容 ⊂ #58 + 批684;上面 Codex 兩條是 ENG088,歸 PR #53 / Z73) |

## 五 · 收

| 檔 | 是什麼 |
|---|---|
| `functional modules/VDF/engine/VDF_ENG090_DataCoverageGate_v0105.py` | 四態全帶「不代設」;+㉕;24 檢 |
| `supportive modules/registry/via_boot_update.sh` | ⓪ 逐件退路 + `--use-pep517` + `VIA_ENV_REQ` |
| `supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json` | registry-sync(v0119):ENG090 記錄改指 v0105 |
| `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | 台帳 +1(1286) |
| `docs/VIA_DroppedBalls_B507.md` | ~~Z80~~ · ~~Z81~~ 已結;Z79 補工作站實錄 |
| `docs/VIA_B687_ARetreatMustNotDropThePromise.md` | 本文 |

推之前全格子 v0435:OK 278 · FAIL 5 · SKIP 4 · TIMEOUT 0(GRID_20260921_104543,350s);紅 5 全是容器(pwsh 不在 · TWSE openapi 三車道無產業表/ETF 冊 · sidecar 庫 0 份);VDF 資料涵蓋閘站(newest → v0105)OK
