# 批607 — 省 TOKEN:畫面可以壓,紅燈不可以(L86 · LL164)

操作員令「優化指令省 TOKEN」+ 工作站 ALL-IN-ONE 首次全跑實錄。

---

## 〇、先報這一跑的成績(15 步)

```
GREEN 9 · NODATA 4 · RED 1 · TIMEOUT 1 · 加速器 25/25 · 同步 FASTFORWARD
```

**真正該高興的兩格**:

- `04_EnvRunGate` **GREEN** —— `[vdf] GREEN · 完整 GREEN` / `[vrn] GREEN · 完整 GREEN`。
  批603 修的 `VDF_ENG090` 漏 `import os` 生效了。
- `07_EnvResume` **GREEN** —— 逐境 LKGC **42 境 READY**,而「全境成功紀錄」誠實印
  **(從未有過)**。批602 說的「你要的那份從來沒被存下來過」,現在有了。

## 一、TOKEN 大戶是我自己排的

| # | 哪裡燒 | 有多少 | 修法 |
|---|---|---|---|
| ① | `11_PanoramaScan` 帶 `--json` | **101 列 JSON 全吐畫面** | 拿掉 `--json` → **6 行摘要**。同一份 JSON 本來就落在 `VIA_Reports\panorama_audit`,資訊密度一樣 |
| ② | `13_SelftestGrid` 250 站逐站 | ~300 行 | 畫面濾鏡壓到 60 行內(紅的照印) |
| ③ | 每步開頭的 `SyntaxWarning: invalid escape sequence '\e'` | 每步 2 行 × 6 步 | 那是**我批601 留下的**,修掉(見三) |

**已經落檔的東西,不必再刷一次畫面。壓縮不是砍資訊,是砍重複。**

## 二、畫面濾鏡的規矩(L86)

```
log 永遠是全的(一個字都不少)· 畫面才壓
純噪音       進度條 / @@PROGRESS / SyntaxWarning 與其回音 → 直接丟,但**報出丟了幾行**
一般行       印到上限(-MaxLines,預設 60)
說得出原因的 [FAIL] / [計] / [停] / Traceback / 判定 / 裁決 → **不受上限,過了照印**
```

**實測(合成 248 行,FAIL 故意埋在第 201 行)**:

```
來源 248 行 · 畫面 63 行 · 壓 181 · 噪音 5 · 紅字補印 2
console 裡 [FAIL] 衝突哨兵   → 1 行  ✓ 埋在上限之外照樣印得出來
console 裡 [計] OK 248 …     → 1 行  ✓
console 裡 噪音               → 0 行  ✓
log 行數                      → 248   ✓ 一個字都沒少
```

## 三、兩件**只有你那台量得到**的(LL164)

### `\e` —— 我這邊一次都看不到

批601 我在 `tools_ps` 寫了 `"$env:USERPROFILE\envs"`,`\e` 不是合法跳脫。

| | 本容器 | 你的工作站 |
|---|---|---|
| Python | **3.11.15** | **3.12.12** |
| invalid escape | DeprecationWarning(預設不顯示) | **SyntaxWarning(每步都印)** |

我甚至跑過 `python3 -W error::SyntaxWarning` 驗證,回「無警告」——
**尺在我的直譯器上就是量不到**。`v0111` 修掉;對照組:`v0110` 仍 1 筆、`v0111` 為 0。

### 全格逾時 3600s —— 拿我的錶量你的路

```
本容器 292s   ←→   你的工作站 2314s(平行)+ 第二段序跑複判
```

**差 8 倍**,結果整跑在 3600s 被殺,**前面 240 站的結果跟著沒了**。

- 逾時拉到 **7200s**(`-GridTimeoutSec` 可調)
- 逾時**不再只說「逾時」**:讀 `SELFTEST_PROGRESS.json` 心跳,講出
  「跑到第幾站 · OK 幾 FAIL 幾 · 最後在哪一站」

## 四、還沒解決的(誠實列著)

- `06_EnvPlan` RED —— BASE 判 RED(封鎖家族件 29 · manifest 缺 10),**那是真的環境狀態**,不是步驟壞掉
- `03/05/12/15` NODATA —— 引擎自述缺料,不是壞掉
- 全格第一段 **OK 196 · FAIL 52**,第二段序跑複判把 12 站轉綠(鎖撞=假紅);
  剩下的紅要逐站看,**這一批沒動它們**
- 你最後那行 `...ps1"pwsh -NoProfile...` 是**貼了兩次**黏在一起,不是指令壞掉

## 五、我讀不到你給的那個 session

`claude.ai/code/session_01FQ…` 我這邊開不了。`tonykuni/via-vdf-vrn`
(`claude/charming-brown-2qaooh`,已併 PR #28/30/31/32)掛上來看過了 ——
那是**另一棵樹**(vite/node + `VIA_CentralGovernance.py`),跟 `movies-dataset` 不同專案。
要我在那邊做什麼,你說。
