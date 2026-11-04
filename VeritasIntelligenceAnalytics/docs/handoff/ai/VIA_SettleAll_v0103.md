# VIA_SettleAll v0103 · 桌機 v0102 貼回(2026-11-04 20:34)的處理

## v0102 在桌機的結果(貼回包 VIA_Settle_20261104_203458.zip · 只記結論與筆數)

| 段 | 燈 | 事實 |
|---|---|---|
| ① 環境 | 綠 | Python 3.13.7 · duckdb 1.5.2 · pyarrow 24 · polars 1.40.1 · pwsh 有 · 可用 3.8 GB |
| ② AST | 綠(但舊)| 328 檔錯 0;工作樹尾版 VDF_SystemManager **v0162**(分支 v0168)· VRN_SystemManager v0254(分支 v0261)· VQG / Agent OS / RoundAll 不在樹上 |
| ③ 同步 | 黃 | 桌機在 **main** · 落後分支 213 提交 · 多 2 個沒推 · 已追蹤改動 38 · 未追蹤 404 → v0102 不合併 |
| ④ VDF ui | 紅 | v0162 `AttributeError … no attribute 'DB_MOD'`(v0160 L177 讀 PRIOR.DB_MOD;`DB_MOD` 在分支的 v0155+ 才有 · 桌機那幾版是舊內容)→ **③ 沒同步的後果** |
| ⑤ VRN | 黃 | 收尾收據 DATA_GAP · 資料源 3 · VRN-2 0(結案)|
| ⑥ VCGC | 紅 | 交接閘 rc 1 · 串測沒總行 —— v0102 沒把輸出存下來,看不出原因(舊樹上跑的)|
| ⑦ Graphify | 黃 | VRN 7300 / VRN_Shared 43631 / VDF 15426 節點綠(125 / 366 / 162 秒 · 記憶體少所以慢);**VCGC 吃到可用 0.74 GB 被看門狗殺**(起始 3.97 → 最低 0.74 = 吃掉 ≥ 3.2 GB · 914 秒)|
| ⑧ VQG | **黃(第一次算出來)** | 家 = `via_database\vdf_database`(分支冊 v0101 · 日線 parquet 351 檔 · DERIVE_READY)· closeout rc 0 · 探針 0050.TW sma / rsi / macd · 曆是推的 |
| ⑨ Agent OS | 黃 | 48 項 · 錯 1 = symlink 權限(WinError 1314 · 環境)· skills / status / vcgc-status rc 0 · 儀表板已出 |

## v0103 改什麼(v0102 一字不動)

| 段 | 改法 |
|---|---|
| ③ 同步 | 已追蹤改動分兩類:**收據類**(`VIA_Reports/**` · `docs/handoff/evidence/**` · `HANDOFF_latest.json` · Lessons / FunctionLedger 兩本只增冊 · `.via/`)= 各系統自己跑出來的 → 自動 `git stash push -- <那些檔>` → 合併 → `stash pop`(衝突取桌機版 · stash 清空);**其他**(程式 / 冊)才停,並把檔名印出來與寫進報告 `sync_dirty.others` |
| ② AST | 多比對分支尾版(`git ls-tree origin/<BRANCH>`)→ 「工作樹落後分支」逐家族列出;④ / ⑥ 紅時直接指回 ③ |
| ⑥ VCGC | 輸出尾段 + 第一行 `[RED]` 寫進報告 |
| ⑦ Graphify | 記「階段(extract / cluster)」與「吃掉(估)= 起始可用 − 最低可用」(graphify.exe 是殼 · 自己的 RSS 量不到 worker);下一步寫明:可用 ≥ 6 GB 再跑 `$env:VIA_GRAPHIFY_ONLY='VCGC'` |

自測 25 / 25(含假遠端:收據類衝突 stash → 合併 → 放回 · 非收據改動列檔名拒合併)· 容器實跑 scan / sync / vrn / vcgc / graphify / vqg / agentos / report(⑥ 這次有總行與紅類計數)· VCGC 全景卡治理錯 0(報 3 處 PINVER = 釘 SHA 的三個檔 · 1 處 SWALLOW 承自 v0101)。

## 桌機要做的(PowerShell 7 · 一行 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0103";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0103.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0103.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F673698309AB6FDE77A6DA5A6EEFDA7A2EBF3CA0B4C62F690BDECB36BE0871B2'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

預期:③ 若 38 個改動全是收據類 → 自動放回並合併(桌機的 2 個提交保留)→ ④ VDF ui 跑到 v0168 · ⑥ VCGC 在新樹上;若有非收據改動 → 黃燈列出檔名,你決定提交或還原後再貼一次。⑦ VCGC 那張圖要可用記憶體 ≥ 6 GB(關掉瀏覽器 / Office / OneDrive 同步後 `$env:VIA_GRAPHIFY_ONLY='VCGC'` 單跑)。⑧ VQG 黃是設計(要 GREEN 得 VDF 線出 market / session_index / available_on 三欄)。⑨ Agent OS 黃 = Windows 開發人員模式才會全綠。
