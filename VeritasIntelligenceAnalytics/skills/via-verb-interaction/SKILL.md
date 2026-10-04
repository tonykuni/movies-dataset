---
name: via-verb-interaction
description: VIA 的「AI 動詞交互反饋」技能:AI 不讀整檔、只讀動詞回傳;每輪一來一回(黃紅字貼回包 ≤300 行 + NEXT 一行);紅分三類(被打斷 / 環境 / 真紅);真紅只出薄尾(新版號、前版不動、含根因重現檢);教訓帳與裁定帳先讀再修。正主 CGC_MDL256_AiVerbBridge。
version: v0100
engine: CGC_MDL256_AiVerbBridge_v0100
---

# via-verb-interaction(VSKE 技能 · 可分拆)

## 何時啟用
操作員貼回任何 VIA 執行輸出(貼回包 / 矩陣 / 全景 / log)或要求「修紅」「下一步」時。

## 七條規矩(T1–T7)
1. **不讀整檔**:只讀 `paste` 產出的黃紅字區與 `classify` 結果;要看碼用 `via-vcgc token slice --lines a-b`(錨點 ±30 行),不 `read` 整檔。
2. **固定形狀**:每個動詞回 `{state, lamp, why, anchor, next}`;AI 只依 `NEXT:` 行動,一輪一來一回。
3. **貼回包有預算**:≤300 行;`[監控] / [矩陣] / [自動跳出] / SyntaxWarning / 進度列` 一律濾掉;超過改貼 `paste.md` 路徑。
4. **沿用律**:輸出寫「沿用」或指紋沒變 → 不要求重跑;同輪只看 diff。
5. **教訓帳先讀**:`lesson get <key>` 第 3 次起 escalate=True → 必先讀再出修法;修法不得與帳上失敗過的相同。
6. **裁定帳先讀**:裁過的(R-SYN-*/R-EPS-01/命名改號)在冊,不再問。
7. **真紅只出薄尾**:`thin-tail <stem> <prior> <new> <owner_fn> --why --check` 產骨架 → AI 只填三格(修正體 · 根因重現檢 · 抽一檢)→ `--selftest` 綠 → `EngineLanes -Only` → 登冊鎖。

## 紅三類(classify)
| 類 | 判準 | 動作 |
|---|---|---|
| INTERRUPTED | rc -1073741510 / 124 / TIMEOUT / 錨點在 threading·codecs·glob·<frozen> | 重跑(更大預算),不修碼 |
| ENV | 閘未開 / NO_CONSENT / 收容件缺 / ABSENT / No module / unrecognized --selftest / GATED | EnvGovernance `tools --approve` 或開閘;加 `--selftest` 的是薄尾但屬介面補齊 |
| TRUE | 燈 RED 且錨點在自家檔 | 薄尾(規矩 7) |

## 一輪契約
```
操作員 → 一貼(骨架 PS,黃紅字收尾)
AI     ← paste 包(≤300 行)+ NEXT
AI     → 薄尾 N 支 + 一貼(不出整檔、不出長文)
操作員 → 跑;貼回
```
token 上限(建議):輸入 ≤ 6k · 輸出 ≤ 8k;超過 = 動詞囉嗦,修動詞不修 AI。

## 動詞(都在 CGC_MDL256;VIA_FROM_VCGC=YES)
- `paste <log|-> [--max 300] [--next "…"]`
- `classify <ENGINE_READINESS.csv | 貼回包>`
- `lesson add <key> <note>` · `lesson get <key>` · `lesson list`
- `thin-tail <stem> <prior4> <new4> <owner_fn> --family <core|vdf|vrn|sup> --why "…" --check "…"`
- `round write <n> --paste <pack.md> [--classify <json>]`

## 技能自測(VSKE 要求:多 AI 試用式)
給技能這段假貼回包,合格答案必須:(1) 濾掉 3 行噪音;(2) ENG393 歸真紅、ENG112 歸被打斷(錨在 threading.py)、ENG117 歸 ENV(--selftest 缺);(3) 只對 ENG393 產薄尾骨架,owner_fn 用前版鏈上存在的名字;(4) 回覆 ≤ 40 行且最後一行是 NEXT:。
```
  [監控] 已在背景起全景監控 pid 5516
  <unknown>:670: SyntaxWarning: invalid escape sequence '\d'
[計] VRN_ENG399_RealTestHarness_v0100 自測 8/8 · PASS
[真紅] vrn VRN_ENG393_DocClassVerify_v0101 · Traceback · 錨 supportive modules\SUP_MDL737_SuperAccelModule_v0109.py:54
[真紅] vrn VRN_ENG112_FinancialRead_v0100 · sys.exit(selftest()) · 錨 C:\Python313\Lib\threading.py:1094
[真紅] vdf VDF_ENG117_ForwardVintage_v0101 · unrecognized arguments: --selftest · 錨
```
機器驗:`python CGC_MDL256_AiVerbBridge_v0100.py --selftest`(11 檢)。

## 不做
不讀整檔、不改舊版、不刪行為、不裁定(裁定權在操作員)、不在貼回包外推斷錨點。
