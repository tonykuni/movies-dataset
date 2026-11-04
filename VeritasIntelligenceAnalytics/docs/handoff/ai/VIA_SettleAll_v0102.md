# VIA_SettleAll v0102 · 一支程式處理 2026-11-04 桌機四條的結果(integrate into one code to handle above)

操作員 2026-11-04 桌機貼回:Graphify 綠 3 黃 1 · VRN-2 `--confirm H-fd2ea35f` 已記(收尾頁 DATA_GAP · 資料源缺口 · VRN-2 側結案)· VQG 紅 · Agent OS selftest rc 2。
→ `docs/handoff/ai/VIA_SettleAll_v0102.py`(新檔 · v0101 一字不動 · 自測 23 / 23 · 容器實跑 scan / vrn / graphify / vqg / agentos / report 六段 rc 照實)。

## 三個紅黃的根因與本版怎麼處理

| 條 | 桌機看到 | 根因(AST / 冊 / 實錄定位)| v0102 |
|---|---|---|---|
| VQG | `[RED] ② VDF 庫就緒 · NO_DAILY_PRICES · …\via_01_vdf · 日線檔 0` | VQG 一行只取兩個 VQG 檔,**沒更新桌機工作樹**;工作樹的 VDF 冊只有 `VDF_DataHome_SSOT_v0100`(家 = `via_01_vdf`,VDF 自己 2026-10-22 實測底下 .duckdb 0 個),分支上的 **v0101** 才把真正的家 `via_database\vdf_database` 排第一 → VQG 照舊冊找錯家 | ③ 同步先把分支併進工作樹(乾淨才併);⑧ 家候選 = `$env:VQG_VDF_ROOT` → 工作樹 + 分支尾版兩邊所有 `VDF_DataHome_SSOT_v*.json` 的 homes(新版冊優先)→ 倉內 `VDF\output_hub` 接點;每個存在的家跑 VQG 自己的 `doctor`,取第一個有日線 parquet 的再 `closeout`。都沒有 → RED 列出每個家的判決 + 指明 VDF 線要跑日線回填(ENG054 寫 `<db_home>\output_hub\mega\tw_daily_prices_<時間>.parquet`)|
| Agent OS | `selftest rc 2 · skills / status / vcgc-status rc 0` | 引擎自測 `test_scan_project_enforces_total_source_bytes_and_nofollow` 用 `symlink_to` 建捷徑;Windows 沒開「開發人員模式」或不是系統管理員 → `OSError [WinError 1314]`(容器 48 / 48 綠)。引擎一字不改(SHA-256 釘住)| ⑨ 讀自測 JSON 的 `details` 逐項分類:只有「Windows 建 symlink 權限」→ **YELLOW**(環境 · 引擎本體照設計拒 symlink · 功能不受影響);其他失敗 → RED;不是 RED 才產生儀表板(一行原本 RED 就停)|
| Graphify | `[YELLOW] ④ VCGC · 可用記憶體 4.6 GB < 需要約 6 GB · 跳過` | v0101 一行用固定表估(VRN 3 · VRN_Shared 4 · VDF 4 · VCGC 6 GB),不是實測 | ⑦ **真跑 + 記憶體看門狗**:每秒量可用記憶體與子行程 RSS,可用 < 下限(預設 0.75 GB · `--graphify-floor-gb`)就殺整棵子行程(桌機不當掉)· 峰值 RSS / 最低可用寫進收據 → 下次有實測數字。已綠的三張走 graphify 自己的增量快取 |
| VRN-2 | 確認已記 · DATA_GAP 結案 | — | ⑤ `--vrn` 預設 `status`:只讀 VRN-2 自己的收尾收據判燈(PASS 綠 · VRN-2 有待修紅 · 其他黃),不重跑 40 分鐘那輪;要重跑 `--vrn repair` |

取檔:VQG v0104 / v0105 與 Agent OS v0102 先看工作樹(SHA-256 對才用),不對或不在 → 從 `origin/claude/optimistic-goodall-yhalc5` `git show` 取到 `Downloads\VIA_Settle_v0102\` 再核 SHA-256(與各一行同一套雜湊);VQG 的 Python 照一行的順序找有 duckdb + polars 的(VQG 不 pip)。

## 段(順序)· 各系統只經自己的入口 · 只寫 VIA_Reports\settle · agent_os · graphify 與 Downloads

| 段 | 做什麼 | 寫什麼 |
|---|---|---|
| ① 環境 · ② AST 全景 | Python / duckdb / pyarrow / polars / pwsh / 可用記憶體;10 個家族全部版本 ast.parse + compile(只在記憶體)| — |
| ③ 同步 | 比 GitHub 少幾個 → 合併(不 rebase · 不強推 · 有沒提交的改動就不合併 · 失敗自動 abort)| git 合併提交 |
| ④ VDF ui | VDF 尾版 `ui` · 紅 → traceback AST 定位 | VDF 自己的頁 |
| ⑤ VRN | status(預設 · 只讀收據)/ repair / check / skip | — |
| ⑥ VCGC | `handoff check` + `test --quick` | VCGC 自己的紀錄冊 |
| ⑦ Graphify | 4 張圖 · 看門狗 · `$env:VIA_GRAPHIFY_ONLY` 可點名 | `VIA_Reports\graphify\VIA_Graphify_latest.json`(同 v0101 格式 + watchdog / peak / min_free)|
| ⑧ VQG | 家候選 → doctor → closeout | VQG 自己的 `VIA_Reports\vqg\VQG_Closeout_latest.json` |
| ⑨ Agent OS | selftest / skills test / status / vcgc-status → 分類 → 儀表板 | `VIA_Reports\agent_os\VIA_AgentOS_v0102_*.json` · `Downloads\VIA_AgentOS_Dashboard_v0102_<時間>.html` |
| ⑩ 報告 | 總表 + VDF AST 定位 + VQG 家候選表 | `VIA_Reports\settle\SETTLE_latest.json / .md` + `Downloads\VIA_Settle_<時間>.zip`(含 graphify / vqg / agent_os / vrn2 / vdf 收據)|

VCGC 全景卡:治理 7 類錯 0;報 3 處 PINVER(釘死版號路徑 = 故意的 · SHA-256 釘住的三個檔)· 2 處 SWALLOW(1 處承自 v0101)。

## 桌機要做的(PowerShell 7 · 一行 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0102";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0102.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0102.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'AD2036AD24B165BD6D9BA12E23BE78D679B8B5A04BDBB7AD500498095ABE7373'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

跑完看最後一行 `NEXT:`;不是 GREEN → 把 `Downloads\VIA_Settle_<時間>.zip` 上傳給 AI。預期:
- ⑧ VQG:③ 同步成功後 → 家 = `via_database\vdf_database`(冊 v0101 第一)→ YELLOW(曆是推的)或 RED(VDF 那邊還沒有日線 parquet → 報告的「VDF 家候選」表會寫每個家的 doctor 判決)。
- ⑨ Agent OS:YELLOW(只有 symlink 權限那項)+ 儀表板會開;要它全綠 = Windows 設定 → 開發人員模式(或以系統管理員跑一次)。
- ⑦ Graphify:VCGC 那張會真跑;可用記憶體被吃到 < 0.75 GB 會自己殺掉並記峰值,不會把桌機弄當。
