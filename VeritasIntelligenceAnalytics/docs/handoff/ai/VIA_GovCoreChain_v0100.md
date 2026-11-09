# 治理核心相依鏈驗證矩陣(RC-1 W2 · 唯讀)

`VIA_GovCoreChain_v0100` · 2026-11-09T10:03:55Z · 總燈 **RED** · 靜態解析(逐列 confidence)

## 三種目錄慣例(多頭的根因)

- **flat**:supportive modules/X.py —— 加速器橋把這個根插進 sys.path,裸 import 落這裡
- **numbered**:supportive modules/10_…50_/X.py —— 10_Core_Runtime Runtime Bridge 的 v018 canonical adapter 指名這裡
- **topic**:supportive modules/environment|registry|audit_tools|runtime_bridge|ssot|network/X.py —— VRN 插件載入器以 ssot_dir + 上層搜尋(桌機設定值)
- **lock**:VeritasAegisNexus:SUP_MDL737 SuperAccel v0110 把裸 import 接到鎖冊尾版 network/VeritasAegisNexus_v1652

## VIA_EnvManager · YELLOW

副本 3(無版號 3 · 版本鏈 0) · 內容組 1 · 載入者落點:supportive modules/40_Environment_Health/VIA_EnvManager.py ×1 · supportive modules/VIA_EnvManager.py ×13 · supportive modules/environment/VIA_EnvManager.py ×5 · 只給名字 CORE 5 · SUP 100 · VAP 2 · VCGC 133 · VRN 44 · 桌機絕對路徑 59(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `supportive modules/40_Environment_Health/VIA_EnvManager.py` | numbered | 4425bbd1 | 1672 | supportive modules, environment | PATH_LITERAL 1 | 位元相同 · 有 1 個載入者落到這裡:遷呼叫者後再退 |
| `supportive modules/VIA_EnvManager.py` | flat | 4425bbd1 | 1672 | 40_Environment_Health, environment | PATH_LITERAL 13 | 位元相同 · 有 13 個載入者落到這裡:遷呼叫者後再退 |
| `supportive modules/environment/VIA_EnvManager.py` | topic | 4425bbd1 | 1672 | 40_Environment_Health, supportive modules | PATH_LITERAL 5 | 位元相同 · 有 5 個載入者落到這裡:遷呼叫者後再退 |

## VIA_RegistryCore_v1 · YELLOW

副本 3(無版號 3 · 版本鏈 0) · 內容組 1 · 載入者落點:supportive modules/VIA_RegistryCore_v1.py ×1 · 只給名字 SUP 43 · VCGC 18 · VDF 4 · VRN 33 · 桌機絕對路徑 10(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `supportive modules/20_Registry_SSOT/VIA_RegistryCore_v1.py` | numbered | fb8073a8 | 1200 | supportive modules, registry | 0 | 位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改) |
| `supportive modules/VIA_RegistryCore_v1.py` | flat | fb8073a8 | 1200 | 20_Registry_SSOT, registry | PATH_LITERAL 1 | 位元相同 · 有 1 個載入者落到這裡:遷呼叫者後再退 |
| `supportive modules/registry/VIA_RegistryCore_v1.py` | topic | fb8073a8 | 1200 | 20_Registry_SSOT, supportive modules | 0 | 位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改) |

## VIA_Panorama_AST_RuntimeInjector · YELLOW

副本 3(無版號 3 · 版本鏈 0) · 內容組 1 · 載入者落點:靜態推不到任何一份(全是只給名字 / 桌機路徑) · 只給名字 SUP 30 · VCGC 6 · VRN 33 · 桌機絕對路徑 8(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `supportive modules/30_HardGate_Governance/VIA_Panorama_AST_RuntimeInjector.py` | numbered | b48f8650 | 337 | supportive modules, audit_tools | 0 | 位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改) |
| `supportive modules/VIA_Panorama_AST_RuntimeInjector.py` | flat | b48f8650 | 337 | 30_HardGate_Governance, audit_tools | 0 | 位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改) |
| `supportive modules/audit_tools/VIA_Panorama_AST_RuntimeInjector.py` | topic | b48f8650 | 337 | 30_HardGate_Governance, supportive modules | 0 | 位元相同 · 無獨佔載入者:可退(版本化轉接件,不就地改) |

## VIA_Runtime_Bridge_All_in_One · YELLOW

副本 3(無版號 3 · 版本鏈 0) · 內容組 2 · 10_Core_Runtime 是 supportive modules 的超集(+79 行) · 10_Core_Runtime 是 runtime_bridge 的超集(+79 行) · 載入者落點:supportive modules/runtime_bridge/VIA_Runtime_Bridge_All_in_One.py ×1 · 只給名字 SUP 44 · VCGC 9 · VRN 33 · 桌機絕對路徑 10(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `supportive modules/10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py` | numbered | 2b0366a6 | 757 | — | 0 | 正本候選(是另一份的 append-only 超集) |
| `supportive modules/VIA_Runtime_Bridge_All_in_One.py` | flat | 44714e14 | 679 | runtime_bridge | 0 | 被超集涵蓋 · 無獨佔載入者:可退(出版本化轉接件後進 _superseded) |
| `supportive modules/runtime_bridge/VIA_Runtime_Bridge_All_in_One.py` | topic | 44714e14 | 679 | supportive modules | PATH_LITERAL 1 | 被超集涵蓋:可退(先遷獨佔載入者,再出版本化轉接件,原檔不就地改) |

- SUPERSET:`supportive modules/10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py` ⊇ `supportive modules/VIA_Runtime_Bridge_All_in_One.py`(+79 行)
- SUPERSET:`supportive modules/10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py` ⊇ `supportive modules/runtime_bridge/VIA_Runtime_Bridge_All_in_One.py`(+79 行)

## VIA_SSOT_Unified · YELLOW

副本 3(無版號 3 · 版本鏈 0) · 內容組 2 · ssot 是 20_Registry_SSOT 的超集(+95 行) · ssot 是 supportive modules 的超集(+95 行) · 載入者落點:supportive modules/VIA_SSOT_Unified.py ×25 · supportive modules/ssot/VIA_SSOT_Unified.py ×3 · 只給名字 SUP 70 · VCGC 24 · VDF 7 · VRN 44 · 桌機絕對路徑 10(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `supportive modules/20_Registry_SSOT/VIA_SSOT_Unified.py` | numbered | b3c9cfa6 | 8250 | supportive modules | 0 | 被超集涵蓋 · 無獨佔載入者:可退(出版本化轉接件後進 _superseded) |
| `supportive modules/VIA_SSOT_Unified.py` | flat | b3c9cfa6 | 8250 | 20_Registry_SSOT | PATH_LITERAL 15, IMPORT 10 | 被超集涵蓋:可退(先遷獨佔載入者,再出版本化轉接件,原檔不就地改) |
| `supportive modules/ssot/VIA_SSOT_Unified.py` | topic | 6ddda978 | 8345 | — | PATH_LITERAL 2, IMPORT 1 | 正本候選(是另一份的 append-only 超集) |

- SUPERSET:`supportive modules/ssot/VIA_SSOT_Unified.py` ⊇ `supportive modules/20_Registry_SSOT/VIA_SSOT_Unified.py`(+95 行)
- SUPERSET:`supportive modules/ssot/VIA_SSOT_Unified.py` ⊇ `supportive modules/VIA_SSOT_Unified.py`(+95 行)

## VeritasAegisNexus · RED

副本 8(無版號 4 · 版本鏈 4) · 內容組 5 · 分岔 VeritasAegisNexus.py ↔ supportive modules/50_Protection_Acceleration/VeritasAegisNexus.py(各自獨有 3297 / 45 行) · 分岔 VeritasAegisNexus.py ↔ supportive modules/VeritasAegisNexus.py(各自獨有 3297 / 45 行) · 分岔 VeritasAegisNexus.py ↔ supportive modules/network/VeritasAegisNexus.py(各自獨有 3297 / 45 行) · 載入者落點:supportive modules/VeritasAegisNexus.py ×29 · supportive modules/network/VeritasAegisNexus_v1652.py ×39 · 只給名字 CORE 2 · SUP 102 · VAP 2 · VCGC 168 · VDF 34 · VRN 107 · 桌機絕對路徑 300(倉內無效)

| 副本 | 慣例 | sha8 | 行 | 位元相同於 | 載入者(靜態落點) | 建議 |
|---|---|---|---|---|---|---|
| `VeritasAegisNexus.py` | root | b983c642 | 8438 | network | 0 | 分岔:要 diff 裁(操作員) |
| `supportive modules/50_Protection_Acceleration/VeritasAegisNexus.py` | numbered | f5f81f04 | 5186 | supportive modules, network | 0 | 分岔:要 diff 裁(操作員) |
| `supportive modules/VeritasAegisNexus.py` | flat | f5f81f04 | 5186 | 50_Protection_Acceleration, network | PATH_LITERAL 29 | 分岔:要 diff 裁(操作員) |
| `supportive modules/network/VeritasAegisNexus.py` | topic | f5f81f04 | 5186 | 50_Protection_Acceleration, supportive modules | 0 | 分岔:要 diff 裁(操作員) |
| `supportive modules/network/VeritasAegisNexus_v0116.py` | topic | adb254cc | 139 | — | 0 | 版本鏈前版:保留(相依鏈律) |
| `supportive modules/network/VeritasAegisNexus_v0117.py` | topic | ad494845 | 191 | — | 0 | 版本鏈前版:保留(相依鏈律) |
| `supportive modules/network/VeritasAegisNexus_v1651.py` | topic | b983c642 | 8438 | VeritasAegisNexus.py | 0 | 版本鏈前版:保留(相依鏈律) |
| `supportive modules/network/VeritasAegisNexus_v1652.py` | topic · tail | c2f40107 | 310 | — | IMPORT 39 | 正本候選(鎖冊尾版;鏈上前版都保留) |

- DIVERGED:`VeritasAegisNexus.py` ↔ `supportive modules/50_Protection_Acceleration/VeritasAegisNexus.py`(獨有 3297 / 45 行)
- DIVERGED:`VeritasAegisNexus.py` ↔ `supportive modules/VeritasAegisNexus.py`(獨有 3297 / 45 行)
- DIVERGED:`VeritasAegisNexus.py` ↔ `supportive modules/network/VeritasAegisNexus.py`(獨有 3297 / 45 行)

## 各獨立系統 × 治理核心(只讀借用;互不干涉律 L123)

| 家族 | CORE | SUP | VAP | VCGC | VDF | VRN |
|---|---|---|---|---|---|---|
| VIA_EnvManager | 6 | 106 | 2 | 145 | 0 | 44 |
| VIA_RegistryCore_v1 | 0 | 43 | 0 | 19 | 4 | 33 |
| VIA_Panorama_AST_RuntimeInjector | 0 | 30 | 0 | 6 | 0 | 33 |
| VIA_Runtime_Bridge_All_in_One | 0 | 44 | 0 | 10 | 0 | 33 |
| VIA_SSOT_Unified | 0 | 75 | 0 | 30 | 10 | 58 |
| VeritasAegisNexus | 2 | 110 | 2 | 250 | 53 | 186 |

## 改動權 · GREEN

治理核心(六件)只有操作員與 AI 經 PR 能改;VCGC / VDF / VRN-2 / VQG / VAP 五系統對它只讀借用(互不干涉律 L123),任何自動寫入都是紅線

TREE(真寫樹上)0 · FIXTURE(暫存夾具)46

| 寫入者 | 車道 | 家族 | 呼叫 | 行 | 範圍 | 函式 | 有 --apply 閘 |
|---|---|---|---|---|---|---|---|
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | .write_text() | 654 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | .write_text() | 655 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | .write_text() | 656 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | .write_text() | 657 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | .write_text() | 658 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | .write_text() | 659 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | .write_text() | 660 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | .write_text() | 661 | FIXTURE(暫存夾) | selftest | ✔ |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | .write_text() | 662 | FIXTURE(暫存夾) | selftest | ✔ |
| `functional modules/VRN/VRN2_MarketFetch_v0105.py` | VRN | VeritasAegisNexus | .write_text() | 469 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0105.py` | VRN | VeritasAegisNexus | .replace() | 472 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0106.py` | VRN | VeritasAegisNexus | .write_text() | 482 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0106.py` | VRN | VeritasAegisNexus | .write_bytes() | 487 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0106.py` | VRN | VeritasAegisNexus | .write_bytes() | 491 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0106.py` | VRN | VeritasAegisNexus | .write_bytes() | 495 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0106.py` | VRN | VeritasAegisNexus | .replace() | 485 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .write_text() | 517 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .write_bytes() | 522 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .write_bytes() | 526 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .write_bytes() | 530 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .replace() | 520 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0107.py` | VRN | VeritasAegisNexus | .replace() | 532 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .write_text() | 521 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .write_bytes() | 526 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .write_bytes() | 530 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .write_bytes() | 534 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .replace() | 535 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .replace() | 524 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0110.py` | VRN | VeritasAegisNexus | .replace() | 536 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .write_text() | 570 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .write_bytes() | 575 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .write_bytes() | 579 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .write_bytes() | 583 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .replace() | 584 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .replace() | 573 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0111.py` | VRN | VeritasAegisNexus | .replace() | 585 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .write_text() | 572 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .write_bytes() | 577 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .write_bytes() | 581 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .write_bytes() | 585 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .replace() | 586 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .replace() | 575 | FIXTURE(暫存夾) | selftest | ✘ |
| `functional modules/VRN/VRN2_MarketFetch_v0112.py` | VRN | VeritasAegisNexus | .replace() | 587 | FIXTURE(暫存夾) | selftest | ✘ |
| `supportive modules/VIA_IF_Engine/SUP_MDL144_IfEngine.py` | SUP | VIA_SSOT_Unified | .write_text() | 729 | FIXTURE(暫存夾) | def_selftest | ✘ |
| `supportive modules/registry/CGC_MDL248_FullCheck_v0100.py` | VCGC | VeritasAegisNexus | .write_text() | 444 | FIXTURE(暫存夾) | selftest | ✔ |
| `supportive modules/registry/CGC_MDL248_FullCheck_v0101.py` | VCGC | VeritasAegisNexus | .write_text() | 225 | FIXTURE(暫存夾) | selftest | ✘ |

只算 TREE(寫在樹上的):有 --apply 字樣算黃(有閘,仍要操作員按);沒閘算紅;0 筆 = 綠。FIXTURE(所在函式用 tempfile 造暫存夾的自測夾具)另列不計燈。靜態偵測只看路徑位置的字串(open 第一引數 · write_text/unlink/rename/replace 的接收者 · shutil.copy/move 的引數),目標必須是模組檔本身(X.py / X_v####.py),輸出冊 / 報告名不算。

## 載入者明細(前 60 列)

| 載入者 | 車道 | 家族 | 方式 | 慣例 | 行 | 推定落點 | 信心 |
|---|---|---|---|---|---|---|---|
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_SSOT_Unified | NAME_ONLY | name-only | 137 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 137 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_SSOT_Unified | NAME_ONLY | name-only | 6487 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 6488 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_EnvManager | NAME_ONLY | name-only | 6490 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Panorama_AST_RuntimeInjector | NAME_ONLY | name-only | 6491 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_RegistryCore_v1 | NAME_ONLY | name-only | 6492 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 6493 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_SSOT_Unified | PATH_DESKTOP | desktop | 6487 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VeritasAegisNexus | PATH_DESKTOP | desktop | 6488 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_EnvManager | PATH_DESKTOP | desktop | 6490 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Panorama_AST_RuntimeInjector | PATH_DESKTOP | desktop | 6491 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_RegistryCore_v1 | PATH_DESKTOP | desktop | 6492 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Runtime_Bridge_All_in_One | PATH_DESKTOP | desktop | 6493 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_SSOT_Unified | NAME_ONLY | name-only | 6473 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 6474 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_EnvManager | NAME_ONLY | name-only | 6476 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Panorama_AST_RuntimeInjector | NAME_ONLY | name-only | 6477 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_RegistryCore_v1 | NAME_ONLY | name-only | 6478 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VeritasCeleritas_v1141.py` | SUP | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 6479 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VIA_MambaBridge_v0101.py` | SUP | VIA_EnvManager | NAME_ONLY | name-only | 1 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/VIA_MambaBridge_v0100.py` | SUP | VIA_EnvManager | NAME_ONLY | name-only | 1 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/SUP_MDL737_SuperAccelModule_v0110.py` | SUP | VeritasAegisNexus | PATH_LITERAL | flat | 3 | supportive modules/VeritasAegisNexus.py | HIGH |
| `supportive modules/SUP_MDL737_SuperAccelModule_v0110.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 28 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/SUP_MDL737_SuperAccelModule_v0110.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 108 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `supportive modules/SUP_MDL737_SuperAccelModule_v0110.py` | SUP | VeritasAegisNexus | NAME_ONLY | name-only | 119 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `VIA_Reports/handover/evidence_b532_unified_nlp/VDF_ENG086_QuantGuardOneBridge_v0100.py` | CORE | VeritasAegisNexus | NAME_ONLY | name-only | 56 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `VIA_Reports/skills/local-first-virtualization/scripts/local_first_virtualization_v0100.py` | CORE | VIA_EnvManager | NAME_ONLY | name-only | 50 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | flat | 3 | supportive modules/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 72 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_RegistryCore_v1 | NAME_ONLY | name-only | 72 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Panorama_AST_RuntimeInjector | NAME_ONLY | name-only | 72 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 73 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | NAME_ONLY | name-only | 73 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | NAME_ONLY | name-only | 73 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | NAME_ONLY | name-only | 290 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | NAME_ONLY | name-only | 469 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_DESKTOP | desktop | 664 | (桌機絕對路徑:倉內無此檔;只在桌機有意義) | N/A |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 669 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | NAME_ONLY | name-only | 687 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 691 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | topic | 699 | supportive modules/environment/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 712 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | PATH_LITERAL | topic | 291 | supportive modules/network/VeritasAegisNexus.py | supportive modules/network/VeritasAegisN | MEDIUM |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 654 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | numbered | 655 | supportive modules/40_Environment_Health/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | topic | 656 | supportive modules/environment/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | NAME_ONLY | name-only | 657 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_SSOT_Unified | PATH_LITERAL | topic | 658 | supportive modules/ssot/VIA_SSOT_Unified.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 659 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | PATH_LITERAL | topic | 660 | supportive modules/runtime_bridge/VIA_Runtime_Bridge_All_in_One.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | PATH_LITERAL | topic | 661 | supportive modules/network/VeritasAegisNexus.py | supportive modules/network/VeritasAegisN | MEDIUM |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | PATH_LITERAL | topic | 662 | supportive modules/network/VeritasAegisNexus.py | supportive modules/network/VeritasAegisN | MEDIUM |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | flat | 674 | supportive modules/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | PATH_LITERAL | topic | 676 | supportive modules/environment/VIA_EnvManager.py | HIGH |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_RegistryCore_v1 | NAME_ONLY | name-only | 680 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_Runtime_Bridge_All_in_One | NAME_ONLY | name-only | 682 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VeritasAegisNexus | NAME_ONLY | name-only | 683 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 673 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |
| `docs/handoff/ai/VIA_GovCoreChain_v0100.py` | VCGC | VIA_EnvManager | NAME_ONLY | name-only | 729 | (只給名字;落點由呼叫者的搜尋夾決定 —— VRN 插件載入器用 ssot_dir 與其上層,桌機設定值) | LOW |

## 不在範圍
- 凍結(RetiredEngines · quarantine · intake)· 鏡像(SCOPE_COPY · Standalone · new modules engines)· _sha 分身(CONFLICT-00005)
- 執行期 sys.path 的真實順序(本支只做靜態推定,逐列標 confidence)
- 任何修改:殼 · 版本化轉接件 · _superseded 都是操作員裁完才做
