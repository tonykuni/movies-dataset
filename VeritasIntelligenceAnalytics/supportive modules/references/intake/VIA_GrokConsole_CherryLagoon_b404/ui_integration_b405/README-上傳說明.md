# 母倉成果整合包(批405)— 上傳到 cherry-lagoon-honey-dove

把本包 `src/` 底下的檔案,依相同路徑放進 repo(Grok 上傳介面直接放即可)。

## 新增 5 檔
| 路徑 | 作用 |
|---|---|
| `src/lib/via/tri-xcheck.ts` | VRN 三方對照(檔名 × 首頁 × 財報頁表格)七態判準,與母倉 `VRN_ENG074_FinancialPages_v0102` 同律 |
| `src/lib/via/tri-xcheck.test.ts` | 上者之 node:test |
| `src/lib/via/psrepair-rounds.ts` | PS 修復三輪(R1/R2a/R2b/R3a/R3b/R3c)契約 + 工作站 2026-09-08 實跑實績 + 卡斷根因與洗版修 |
| `src/lib/via/psrepair-rounds.test.ts` | 上者之 node:test |
| `src/components/mother-deck.tsx` | 「母倉」分頁:三方對照五邊、PS 三輪矩陣、橋覆蓋、本倉收容差異 |

## 改動 2 檔(各只動 1–4 行,零刪除)
| 路徑 | 改動 |
|---|---|
| `src/lib/via/types.ts` | `Deck` 型別 +`"mother"`(1 行) |
| `src/components/shell.tsx` | import `MotherDeck`/`psrOverall`、NAV +`{ id: "mother", label: "母倉", kicker: "05" }`、`lights` +`mother`、main +`{deck === "mother" ? <MotherDeck /> : null}` |

## 驗證(在本包來源的 clone 上真跑過)
- `node --experimental-strip-types --test src/lib/via/*.test.ts` → **224 pass / 0 fail**(原 222 + 本包 2)
- `tsc --noEmit` → 本包 5 個新檔與 2 個改檔 **零錯誤**(僅環境級 `@types/node`/`vite/client` 缺,因未 `npm install`)

## 慣例遵循
- lib 模組=純資料/邏輯,`import type { Light } from "./types.ts"`,每檔配一支 `.test.ts`(node:test + assert/strict)
- 元件用既有 `Matrix` / `StatusLight` / `LightLegend` / `Badge` 與既有 Tailwind token(`bg-surface`/`text-subtle`/`shadow-[var(--shadow-border)]`)
- Zero-Hydra:`tri-xcheck` 不與既有 `vrn-xval`(報告值 vs API)重疊,比的是同一份報告內兩條擷取道;`psrepair-rounds` 沿用既有 `ast-anchor.classifyFix` 做並行/序相依分類,不另造
- 只增不減:既有 5 個分頁與所有既有模組零觸碰
