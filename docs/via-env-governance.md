# VIA 環境治理統一引擎(批381;CGC_MDL135_EnvGovernance v0100)

> 操作員令:「依照已成功地建構布局向上新增;最壞還原成原本規劃;base 只放該有的工具;其他放在 via_core 及 via_ 開頭的環境」
> +《VIA_EnvManager.py 環境與函式庫防衝突管理規範》(全景式分析先行·uv 極速衝突快篩·衝突立拔與動態隔離·LKGC 授權閉環·一貼即用·HTML UI Matrix)。
> 一鍵:`via-envgov`(唯讀)/ `via-envgov-auto -Online -Approve`(一貼即用);`via-envmgr govern` 同路由(Router v0101)。

## 一、證據與根因(上船件 VIA_Install_Plan_20260820 ×3)

| 體檢時間 | 結果 | 唯一 FAIL |
|---|---|---|
| 06:24 / 23:00 / 23:59 | libs·核心 9/9、DOCX 2/2、OCR(選配)2/2、EnvManager 在庫、Deploy 配置 OK | `pip 衝突掃描:albucore 0.0.24 requires opencv-python-headless, which is not installed.` |

三次同狀=**衝突持續未閉環**。根因:OCR 家族(paddleocr/paddlex/albumentations/albucore/cv2)住在 base;
InstallGate `--doctor` 拔 headless、錨 contrib 後,albucore 的 metadata 需求懸空;既有工具(EnvFix `-RepairBase`
只補缺件、InstallGate 只裝不拉)沒有「把整個家族拉出 base」的動作。本引擎補上這一段,且**正本零觸碰**
(`VIA_EnvManager.py`/MDL050/MDL056/MDL062 全部唯讀復用)。

## 二、base 該有冊(原本規劃 SSOT):`VIA_EnvGovernance_Baseline_v0100.json`

| 層 | 內容 | 依據 |
|---|---|---|
| toolchain | pip/setuptools/wheel/packaging/uv + Top 8 檢測工具(pipdeptree/deptry/pipgrip/johnnydep/pip-tools/pip-check-reqs)… | `requirements-envcheck.txt` |
| engine_core | pandas/numpy/pyarrow/duckdb/pymupdf/requests/jsonschema/plotly/matplotlib/openpyxl/scipy/rich/psutil/docx2python/python-docx… | Provision `REQ_CORE`+`REQ_DOCX`、EnvFix 五依賴、boot_update 核心冊(=已成功布局實證) |
| low_risk_allow | colorama/click/tabulate/humanize/arrow/inquirer/typer… | 5D 矩陣 `L / PY / ANY / R1 / CORE` 白名單候選 |

**base 該有 = manifest ∪ 其已裝相依閉包**;閉包外=拉出候選;`never_in_base_families`(ocr/deep_learning/browser/
table_extraction/ml_boost/gis/web_api/webui/nlp_heavy/process_mining/compilers/stealth_proxy)=RED 立拔;
Linux 發行版 `dist-packages`(OS 管理)不動不列。manifest 內之 MEDIUM 件(duckdb/pyarrow/plotly/openpyxl/pymupdf)
以引擎實證豁免=base 該有(與 EnvManager「base 擋 MEDIUM/HIGH」的新裝閘不衝突:閘管新裝,冊管存量)。

## 三、路由(routing_order)

`explicit → Lessons SKIP(everywhere=拒;base=拒入 base)→ via_core 白名單(EnvManager 政策母版;既有健康境優先)
→ 家族 target_env(如 OCR→paddle_312,備 paddle_311)→ EnvManager purpose hints → 5D 矩陣 lib_index → via_iso_quarantine 候裁`

家族整包=家族根+境內相依閉包;**目標境安裝完整閉包(含 base 留用件副本)鎖 base 現版**(LKGC 精神),
以 `--no-deps` 安裝防解析器回拉拒裝件(headless);cv2 家族一律換錨 `opencv-contrib-python`。
境內殘餘 `albucore→opencv-python-headless`(metadata-only;contrib 錨在)=YELLOW 接受,不裝 headless。

## 四、流程(三輪 × Zero-Hydra)

```
panorama(平行探針硬逾時;動態進度條)→ uv pip check 毫秒快篩(退 pip 退 NOT_RUN 誠實)
→ base 該有冊閉包比對 → 衝突分類(PULL_OUT / REPAIR_BASE / REBUILD / METADATA_SHADOWED)
→ H1 多層遮蔽 / H2 跨境大版分歧 / H3 共用節點(反向相依≥5)/ 高風險混居
→ 段冊:ENSURE_ENV → INSTALL → VERIFY(Parallel-Fixable,R1 並行)
        REMOVE_BASE(Sequence-Dependent,R2 拓撲序;破壞候裁)→ VERIFY base
        LOCK → PRUNE(候裁)→ PROMOTE_LKGC(R3 硬化)
→ uv pip compile 多輪模擬(同意閘;末兩輪一致=GREEN)
→ apply --approve 只跑 GREEN 非破壞段;REMOVE_BASE 須 --approve-remove 且目標境 VERIFY 綠後
→ LKGC 快照;全境零衝突且 base 乾淨才晉升 LKGC_latest
→ 四分區 HTML Matrix(MODULE/ENGINE/FUNCTION-LIB/OTHERS)+ digest ≤25 行
```

雲端實證(沙盒):`apply --approve --approve-remove --only S01..S04` → INSTALL OK(只裝 albucore==0.0.24,未回拉 headless)
→ VERIFY FAIL(誠實)→ **REMOVE_BASE BLOCKED**(base 端一件未動)。

## 五、LKGC 與最壞還原

| 指令 | 作用 |
|---|---|
| `via-envgov lkgc status` | LKGC_latest / 史 / 未晉升候選與原因 |
| `via-envgov rollback` | 有 LKGC:逐境 `uv pip sync lock`(base 端 sync 屬破壞=候裁 `--approve-remove`);無 LKGC:**原本規劃**=Baseline base manifest 補齊+env_layout/家族目標境重建(既有別名境不重建) |
| `via-envgov rollback --baseline --execute --approve` | 直接還原成原本規劃(非破壞段) |

存證:`VIA_Reports/env_governance/{RUN_<ts>.json, LKGC_<ts>.json, LKGC_latest.json, lock/, PLAN_EXEC_<ts>.ps1/.sh, ROLLBACK_<ts>.ps1/.sh, VIA_EnvGovernance_Matrix_latest.html}`
+ `logs/env_governance.log`(JSONL append-only;成敗皆記;`VIA_ENV_GOV_LOG` 可改路徑)。

## 六、指令總表

| 指令 | 內容 |
|---|---|
| `via-envgov` | = `run --offline`(唯讀:全景+計畫+LKGC 快照+矩陣) |
| `via-envgov plan` / `$env:VIA_NET_CONSENT='YES'; via-envgov plan` | 計畫;上網=鏡像健康(清華→阿里→PyPI)+ uv pip compile 多輪模擬 |
| `via-envgov apply --approve [--approve-remove] [--only S02,S03]` | 執行 GREEN 段;base 移除另授權 |
| `via-envgov panorama` / `matrix` / `digest` | 只掃 / 重繪矩陣 / 摘要 |
| `via-envgov-auto [-Online] [-Approve] [-ApproveRemove] [-Background] [-Watch] [-Open]` | 單一 PowerShell 一貼即用(20 加速器→全景→計畫→執行→矩陣;背景 Job 不阻塞) |
| `via-envmgr govern|panorama|plan|apply|lkgc|rollback|matrix|digest` | Router v0101 同路由 |
| `via-rebuild --env X` / `--split X` | 境內衝突/混居委派 MDL050(旁建零破壞) |
| `python CGC_MDL135_EnvGovernance_v0100.py --selftest` | 25 檢(零網路零環境依賴;SelftestGrid 第 187 站) |

參數:`--env-root P`(目標境根;預設 EnvManager 環境根候選→`~/envs`)、`--roots P1;P2`、`--base-python EXE`(在 venv 內執行時指定真 base)、
`--workers 20`、`--task-timeout 120`、`--rounds N`、`--install-plan F`、`--quiet`。

## 七、20 加速器 × 六流程對映

A03 九頭龍 · A04 拓撲 · A05 沙盒模擬 · A07 三輪 · A08 SSOT(冊+母版+5D+Lessons)· A09 矩陣 · A10 分類分群 · A11 uv 毫秒快篩/平行探針 ·
A12 多子系統境 · A13 LKGC/rollback · A15 修正序最佳化 · A16 進度條 · A17 digest · A18 背景 Job · A19 多引擎整合 · A20 apply。
P4「uv 依賴解析、衝突立拔與多環境隔離」=本引擎+MDL050;P6「UI Matrix 與非阻塞 PowerShell」=本引擎 matrix+Invoke-VIA-EnvGovernance。

## 八、批382:base 共用冊、功能件家族與命名律

操作員令:「BASE 應該放都用得到的工具;功能性的工具應該都放到 via_ 相關環境;有兩個環境沒有 via_ 在前面,換名稱重建」。
工作站首跑實錄:24 境 19 秒全探,via_* 22 境零衝突,BASE 681 件 136 衝突;`camelot_311`、`paddle_311` 兩境違反命名律。

### base 共用冊(只放大家都用得到的工具)

| 層 | 內容 |
|---|---|
| toolchain | pip/setuptools/wheel/packaging/uv + Top 8 檢測工具 |
| engine_core(共用基座) | numpy/pandas/pyarrow/duckdb/polars/plotly/matplotlib/scipy/requests/httpx/jsonschema/openpyxl/xlsxwriter/rich/psutil/pydantic/loguru/tqdm/dateutil/pytz/pyyaml/orjson/pillow/certifi/urllib3/cffi… |
| 功能件 → via_ 家族境 | docs→`via_vrn_312`(pymupdf/pdfplumber/docx…)、html_parse→`via_html_312`、data_fetch→`via_vdf_312`(yfinance/akshare…)、nlp→`via_nlp`(spaCy/jieba/opencc…)、dev_tools→`via_tools_312`、plot_ui→`via_vap_312`、deep_learning→`via_ml`、ml_boost→`via_ml`;專屬境覆寫 catboost→`via_catboost`、lightgbm→`via_lightgbm`、onnxruntime→`via_onnxruntime` |

家族整包只走**必要相依**(extras 可選件不入包;實錄 extras 曾把 bleach/greenlet 拖進 browser 家族),
一件只歸一家族(單寫者律);多家族共用的相依=「共用支援件」,所有家族目標境驗綠後最後候裁移除。
矩陣的「引擎影響」欄列出倉庫中 import 該家族根件的引擎:功能件拉出 base 後,以 base python 啟動的引擎必須改由目標境 python 啟動,
移除前先看這一欄。

### 命名律(H7)與換名重建

```powershell
via-envgov                                  # digest 出現「命名律 🟡 非 via_ 境 paddle_311 → via_paddle_311」
via-envgov rename                           # 唯讀出令:RENAME_EXEC_<ts>.ps1/.sh + 舊境 lock 快照
via-envgov rename --execute --approve       # uv venv via_paddle_311 --python <舊境實際版本> → uv pip sync 舊境 lock → uv pip check(cv2 錨遮蔽殘餘=接受)
via-envgov rename --execute --approve --approve-remove   # 驗綠後舊境改名 _retire_paddle_311(掃描自然除名;可即回退)
via-envgov rename --from paddle_311 --to via_paddle_313  # 想讓尾碼對齊實際 Python 時自訂新名
```

沙盒實證:paddle_311 → via_paddle_311 建境、同步、驗綠、退役全綠;帶有 albucore 殘缺的境則誠實 FAIL 並保留舊境。
下游同步正名:MDL050 v0109 路由出口一律 `via_` 前綴、OCR 車道 v0101 優先找 `via_paddle_*`、Provision v0102 把功能件改到 via_ 境檢查;
`VIA_EnvManager.py` 正本零觸碰(其 purpose hints 舊鍵視為別名層)。

## 九、批383:單一入口、Grok 主控台接回、VDF/VRN 實際能跑、本機三庫整併(抓過的不必再抓)

操作員令:「將 river-beam-aurora-acorn 裡面的檔案接回做為整合為一入口」+「單一入口與這個(SYSTEM MANAGER MATRIX v0700)整合;vap 補充;vdf vrn 要弄到實際能跑;vdf 要將資料庫存入;之前有的資料庫能把它整理好,抓過的資料不必再抓」。

### 單一入口(`via-entry`;CGC_MDL136 EntryBridge)

- 母倉 `Register-VIA-Commands` 點源=唯一入口。載入即接回收容包 b383 的 `scripts/VIA-CmdMatrix.ps1`:去掉尾段自動執行(`via-enter` 進母根、`via-matrix` WPF 板,違批378 零跳出律),撞名守衛=母倉先發先得(`via-entry`/`via-env` 母倉正本;Grok 同名改 `-grok`),Grok 助手函式升 global。`$env:VIA_GROK_MATRIX="0"` 可不載。
- `via-entry` 燈板 11 層(GitHub/Mother/Data/Env/PATH/EnvGov/VDF-DB/VAP/Matrix/Console/Grok;零網路;落 `VIA_Reports/entry/ENTRY_latest.json/.html`);`via-entry plan` 一貼即用 11 步;`via-entry roster` 短令冊;`--open` 開 `VIA_MasterControl_Matrix_v0700.html`(`via-open 矩陣`,瀏覽器道零跳出);`--console` 帶起 Grok 網頁主控台(`via-webconsole`;npm install 同意閘;8080)。
- `via-env` = `via-envgov`(MDL135 正本);`via-grok matrix` 開 Grok WPF 右側板。

### VDF/VRN 實際能跑(功能件住 via_ 境 → 啟動器指對境 python)

- `Get-VIAEnvPython <family>`/`via-envpy vdf|vrn|vap|core|ocr|table`:`VIA_PY_<FAMILY>` 覆寫 > 境根(`VIA_ENV_ROOT`/`VIA_ENV_ROOTS`/`~\envs`/`C:\Users\tonyk\envs`/conda envs/`$VIA\Environments`)× Baseline 別名(`via_vdf_312`/`via_vrn_312`/`via_vap_312`/`via_paddle_311`/`via_camelot_311`…)> base 退路(誠實黃)。`via-vdfdb`/`via-vapone` 已用此律啟動。
- base 仍缺 manifest 件(工作站實錄 duckdb/pyarrow/plotly 缺)→ `via-envgov apply --approve --only-kind REPAIR_BASE`(只跑 base 補齊段;非破壞;鏡像鏈)。功能件拉出 base 之前,先看矩陣「引擎影響」欄,以 base python 啟動之引擎須改由目標境 python(本批啟動器已備)。

### VDF 資料庫存入與「抓過的不必再抓」(`via-vdfdb`;VDF_ENG079 LocalDbConsolidate)

```powershell
via-vdfdb scan                       # 唯讀:三庫盤點(parquet/csv/duckdb/sqlite)+路由計畫+anti-join 計數(不寫);缺 src 誠實 RED
via-vdfdb run --apply                # COPY_ONLY:anti-join 只補缺鍵(ENG064 鍵 date,ticker;既有列零觸碰;冪等);檔指紋台帳 via_ingest_ledger(已入冊跳過)
via-vdfdb ckpt                       # ENG064 --rebuild-ckpt:段內有列即 done → 歷史回補不再重抓已有年段/檔
via-vdfdb need --start 2023-01-01    # 月粒度覆蓋缺口(只列缺的)→ NEED_latest.json;抓取只抓缺口
via-vdfdb coverage                   # 每表 ticker×年覆蓋 → COVERAGE_latest.json
via-vdfdb run --apply --assume-twse  # 裸碼在 tw_listings 對不到時視為 .TW(預設誠實入 local_px_daily 暫存)
```

路由律:px `date+ticker+close` → `tw_daily_prices`(裸碼經 `tw_listings` 表/`mega/tw_listings_*.csv` 對映 yahoo 風格;非台股碼 → `global_daily`);chip → `tw_chips_daily`(欄位聯集只增);rest → `tw_rest_daily`(鍵 `date,ticker,kind`;`kind` 缺以檔名補);無鍵 → `local_<part>__<stem>`(EXCEPT 集合 anti-join)。正典庫=ENG064/ENG065 同路徑 `output_hub/mega`(MDL123 接點→本機資料家)。

### VAP 補充(`via-vapone`;VAP_ENG016 AutoplotOne)

原件零改動直入 `functional modules/VAP/engine/`;`--selftest` 72 檢(沙盒 70/72、工作站 base 71/72;缺 plotly/duckdb/pyarrow 車道=Baseline 冊 REPAIR_BASE 補;`via-vapone` 以 `via_vap_312` 啟動=全車道)。

### 一貼即用(工作站 pwsh)

```powershell
via-reload; via-entry
via-envgov; via-envgov apply --approve --only-kind REPAIR_BASE
via-vdfdb scan; via-vdfdb run --apply; via-vdfdb ckpt; via-vdfdb need --start 2023-01-01
via-vapone; via-open 矩陣
via-webconsole --install; via-webconsole --background     # 選配:Grok 網頁主控台(Node 22;觸網同意)
```

## 十、批384:中央控管整合(session_01R2d69oa1AGvnPVwjSUdSv5)與「vdf vrn 能跑」閘

操作員令:「以此為中央控管將 session_01R2d69oa1AGvnPVwjSUdSv5 整合完畢 vdf vrn 能跑」。

### 整合對象與結論

- 該會話「VIA系統後續工作」的分支 `claude/via-system-followup-tz7k9t` 尾端 c14d428 = `origin/main` = 本分支基底;`git log HEAD..該分支` 為 0,其全部工作已在本分支(PR #30 `claude/via-envmanager-governance-7cls8h`)。本分支即中央控管;該會話遺留的待辦「`via-reload; via-autorun`」改由 `via-entry` 一貼次序承接。
- 其他未併分支(`claude/taiwan-etf-vrn-validation-9b39qw` 等)屬不同世系,本批不併;需要時另令。

### 「能跑」的誠實定義(`via-rungate`;CGC_MDL137 RunGate)

功能件住 via_ 境(Baseline 冊),所以「能跑」不是 base 有沒有裝,而是**以家族境 python 真跑引擎自測**:

```powershell
via-rungate                 # 每族 8 站(vdf/vrn/vap);家族境 python 逐庫 import + SelftestGrid 家族站真跑
via-rungate --fast          # 每族 3 站(總控台 rungate 任務同此)
via-rungate --all           # 全站
via-rungate --family vdf    # 只看一族
via-rungate status          # 看上次 RUNGATE_latest.json
```

判定:族內任一引擎 FAIL/TIMEOUT=RED;家族境未見(base 退路)或必要庫缺=YELLOW;全綠=GREEN。必要庫:vdf `duckdb/pandas/numpy/pyarrow`、vrn `fitz/duckdb`、vap `pandas/matplotlib/duckdb/plotly`。缺件時報告直接印修法(`via-envgov apply --approve` 建境/補庫、或 `--only-kind REPAIR_BASE`)。

### 家族路由落到所有啟動面(一處路由,全鏈同律)

- **DeckServer v0129**:任務冊 `argv[0]` 改由 `_py(family)` 解析(MDL136;`VIA_PY_<FAMILY>` 覆寫 > 境根×Baseline 別名 > base 退路)。ParallelLanes、CompletionAutomator、MasterControl 都讀這本任務冊,因此 `via-mobile --lanes`/`via-autorun`/總控頁按鈕一併改走家族境。雲端/CI 無境=退路 `sys.executable`=原行為零差異。
- **Register v0151**:所有 VDF/VRN/VAP 引擎短令改為 `& (Get-VIAEnvPython <fam>) (Get-VIANewest …)`;新增 `via-py <fam> <script>` 通用啟動器。
- **VIA.ps1** 開機鏈仍 `Start-Process python`(base;正本零觸碰),RunGate 鏈路燈誠實列黃。

### 一貼即用

```powershell
via-reload; via-entry
via-rungate                                   # RED:看尾行修引擎;YELLOW:境缺 → via-envgov apply --approve;必要庫缺 → 報告印的 pip 令
via-envgov apply --approve --only-kind REPAIR_BASE
via-vdfdb scan; via-vdfdb run --apply; via-vdfdb ckpt
via-vapone; via-open 矩陣
```

## 十一、批385:工作站實錄修——via-reload 分支感知、旗標白名單、衝突明細

工作站實錄(2026-09-07 22:13):b381 worktree 在 `claude/via-envmanager-governance-7cls8h` 分支,舊 `via-reload` 固定拉 `origin/main`,快轉失敗、HEAD 停在 8be0780,所以 `via-entry`/`via-vdfdb`/`via-vapone`/`via-rungate` 全部 not recognized;同時舊版 MDL135 不認識 `--only-kind`,卻在 `--approve` 下靜默跑完所有 GREEN 非破壞段(多境 INSTALL + REPAIR_BASE;無破壞段;3 境 VERIFY FAIL)。

- **`via-reload` 分支感知**(Register v0152):當前分支是 `main` 才拉 `origin/main`;否則拉 `origin/<當前分支>`,並印「分支/目標/HEAD 前後」。stash 律不變。
- **旗標白名單**(MDL135):未知 `--旗標` 一律誠實停(rc 2)並列已知旗標,版本落差不再靜默照跑。
- **`via-envgov conflicts [--env X] [--limit N]`**:自 `RUN_latest.json` 印各境衝突明細(requirer/要求/裝的是/kind)與逐條修法(pip 令、`via-rebuild --env`);BASE 預設只印計數。
- 命名律豁免受保護境(`env_layout.protected_envs`,如 `vmt_pm`)與冊 `naming_law.exempt`。

脫困一貼(第一行用絕對路徑,之後 `via-reload` 自動拉對分支):

```powershell
git -C "C:\Users\tonyk\Downloads\movies-dataset-b381" pull --ff-only origin claude/via-envmanager-governance-7cls8h
via-reload; via-entry
via-envgov conflicts --env via_vrn_312; via-rungate --family vrn
via-rungate; via-vdfdb scan; via-vdfdb run --apply; via-vdfdb ckpt; via-vapone; via-open 矩陣
```

## 十二、批386:VRN 一題四點契約接回母倉(潛在上漲空間與目標價除權息調整)

操作員令(自 Grok 主控台對話帶回):「1. 潛在上漲空間(用最新 adj close 去算),目標價 xxx 元,評價方式 xxx,基於 xxx;2. n~n+3 diluted eps,yoy xxx,主要原因 xxx;3. 4. 將第一頁其餘本文部分整合成兩點不受限」,並補一律:「如果報告時間在除權息前,目標價也必須除權息調整」。

- 引擎 `VRN_ENG080_FourPointDigest`(`via-vrn4`,以 `via_vrn_312` python 啟動):輸入 ENG073 的 `vrn_report_basic`/`vrn_report_metrics`、ENG072 首頁 sidecar(header/right/body)與 `tw_daily_prices`;輸出 `vrn_four_point_digest`(派生層,同 report_file 重寫)與 `VIA_Reports/vrn/four_point/DIGEST_latest.json/.html`。
- **除權息調整律**:報告日 < 除權息日 ≤ 最新日 → `TP_adj = TP × F`,`F = (adj_close/close)@報告日 ÷ (adj_close/close)@最新日`(後向復權因子鏈;因子變動日即除權息/拆股事件,逐日列示)。母倉沒有配息事件表,因子由價表推定並誠實標 `PRICE_FACTOR_CHAIN`;最新日因子 ≠ 1 代表 adj 基準不是最新(價表混抓時點),報告會加註,建議 `via-hist` 重抓或 ENG060 重建。
- **潛在上漲空間** `upside_now = (TP_adj − 最新 adj close) / 最新 adj close`;批240 的「報告時上漲」(目標價 ÷ 報告前日 close)另欄保留,兩者口徑不同、不互相取代。目標價缺、該檔不在價表、或價表無 adj_close 時一律「上漲空間未算」,不拿共識或 close 頂替。
- 五槽 quote-or-abstain:標題/K1/K2/K3/K4 皆須從正文或冊抽出才算接地;K5 風險可空即通過;多值目標價只列示不平均;文摘裡出現來源沒有的數字 → QC 紅(衍生數 TP_adj/上漲%/YoY 除外)。
- 另依操作員裁示,Baseline 冊新增 `not_accelerators`:PyPy/RPython 翻譯鏈不是加速槽,`via_iso_pypy` 不得當 GA/PS 加速器,cp311/cp312 與 pp311 ABI 不混載。

```powershell
via-reload; via-vrn4                 # 全冊;需先 ENG072 首頁抽取 + ENG073 入庫
via-vrn4 --ticker 2330; via-vrn4 show 2330
```

## 十三、批387:工作站實錄修——旗標值誤判動詞、CRLF 去尾段、via_vrn_312 補庫

工作站實錄三件:`via-rungate --family vrn` 印出用法(旗標值 `vrn` 被當成動詞);`via-vrn4` 在 `via_vrn_312` 下 `ModuleNotFoundError: duckdb`;`via-reload` 載入 Grok 矩陣時印出 Grok 的 ENTER/ENV 燈並把 cwd 跳到主 clone(Windows `autocrlf` 工作副本是 CRLF,`$` 只認 `\n` 前,`\r` 殘留讓 `via-enter | Out-Null` 那行沒被去掉、載入即執行)。

- 動詞白名單:MDL137/MDL136/ENG079/ENG080 只把已知動詞當動詞,旗標值不再誤判。
- 去尾段 regex 容 `\r`(Register v0154 與 MDL136 同律;MDL136 自測加 CRLF 樣本)。
- `via-rungate --family vrn --approve-install`:必要庫缺而家族境在時,`uv pip install --python <家族境> <缺件>`(無 uv 退 pip;`VIA_PIP_INDEX_URL` 可指鏡像;import 名→pip 名 fitz→pymupdf);未授權只印 PLAN;base 退路一律不裝功能件;裝後重探。Baseline 冊新增 `family_env_core` 記三個家族境的核心基座。
- ENG080 缺 duckdb 時誠實 FAIL 並印修法,不再 traceback。

```powershell
git -C "C:\Users\tonyk\Downloads\movies-dataset-b381" pull --ff-only origin claude/via-envmanager-governance-7cls8h
via-reload
via-rungate --family vrn --approve-install
via-rungate --family vrn; via-vrn4; via-vrn4 show 2330
```

## 十四、批388:VDF/VRN 的 U/I 能跑(`via-famui`)

操作員令「若能跑 vdf vrn 的 u/i」。「U/I 能跑」的誠實定義:以家族境 python 真跑母倉現役的頁面產生器,產物頁在位且本次新鮮、零 CDN,再由 `via-open`(瀏覽器道,零跳出)開啟。

- 冊(尾版 glob):vdf = ENG073 資料架構矩陣、MDL120 系統總台(六主體;base 先跑,缺庫才退家族境);vrn = ENG079 控制塔、ENG068 每日觀察摘要、ENG080 一題四點(資料閘:報告表缺=YELLOW);vap = ENG009/ENG014 儀表板;靜態頁 VDF Fetch ONE、MDL501 控制器、VRN VisualLock 側欄、VAP ONE。
- 判定:產生器 rc≠0 且無頁=RED;資料側/頁未更新/靜態缺=YELLOW;全新鮮=GREEN。樞紐 127.0.0.1:8765 在聽=LIVE(系統總台可從樞紐重取),否則 SNAPSHOT(頁內嵌快照,誠實)。
- 索引 `VIA_Reports/ui/FAMILY_UI_latest.html` 以 file:// 真連結列所有頁;`via-open 家族` 一鍵開索引,`via-open VDF` / `via-open VRN` / `via-open 四點` 直開單頁。總控台任務冊 +`ui_vdf`/`ui_vrn`,MasterControl 頁按鈕同律。

```powershell
via-reload; via-famui vdf,vrn --open      # 再生 VDF/VRN 頁 + 開索引
via-open VDF; via-open VRN; via-open 四點  # 直開單頁
via                                        # 樞紐 8765 帶起後再 via-famui 即 LIVE
```

## 十五、批389:工作站實錄——ENG065 協定檔回歸正典表、資料家接點、VRN plotly

操作員貼回 `via-famui` 產出的 VDF 資料架構頁與 VRN 控制塔頁。三件實錄:

- **part3_rest 的 ENG065 協定檔落錯表**:`tw__tw_listings`、`gl__us_macro`、`tw__tw_monthly_revenue`、`gl__sentiment_daily`、`gl__cross_macro`、`tw__tw_rates_cbc`、`tw__etf_book`、`tw__tw_daytrade_market`、`gl__factset_earnings`、`tw__tw_listings_industry` 被 ENG079 路由到 `local_rest__<stem>`(無 date+ticker 鍵的保底道)。批389 起 ENG079 認 ENG065 檔名協定:`tw__<table>` → `vdf_tw_market` 同名正典表、`gl__<table>` → `vdf_global_market` 同名正典表(跨庫經臨時 parquet 搬運,零 pyarrow 依賴);零改名零轉型(同 ENG065 律)、共同欄交集不 ALTER 正典表;`date`+`ticker` 皆在=鍵 anti-join(ENG064 律),否則 EXCEPT 集合 anti-join。台帳鍵改為「指紋|單元|目標表」:同檔改路由自動重做,不需 `--force`;舊的 `local_rest__*` 表只增不減留存(可自行 DROP,引擎不動)。
- **資料家接點 UNLINKED**:b381 worktree 的 `functional modules/VDF/output_hub` 是真目錄,正典庫困在 worktree 內,與 `C:\Users\tonyk\Github\movies-dataset\data` 資料家各一份。ENG079 加接點燈(MDL123 正本判定):正典庫在倉內 output_hub 且接點非 LINKED → YELLOW 並指路 `via-datahome link`(倉內庫併入家後接點;MDL123 合併律只增)→ 重跑 `via-vdfdb run --apply`(冪等只補缺鍵)。`via-entry` Data 燈同律,`via-entry plan` +`via-datahome link` 步(14 步)。
- **VRN 控制塔「誠實降級:plotly 未安裝」**:`via_vrn_312` 無 plotly。RunGate vrn 必要庫 +plotly、Baseline `family_env_core.via_vrn_312` +plotly;`via-rungate --family vrn --approve-install` 以 uv 補進家族境(不動 base)。

```powershell
via-reload                                   # 拉齊本分支 + 重載短令冊
via-datahome status; via-datahome link       # 接點:倉內 output_hub → 資料家 junction(庫併入家)
via-vdfdb run --apply; via-vdfdb ckpt        # tw__/gl__ 協定檔自動回歸正典表(冪等);checkpoint 重建
via-rungate --family vrn --approve-install   # via_vrn_312 補 plotly
via-famui vdf,vrn --open                     # 再生兩族頁面:資料架構頁應見 tw_listings/us_macro 等正典表;控制塔不再降級
```

自測:ENG079 十三檢 13/13(協定回歸/跨庫/鍵律/台帳鍵/接點燈)、MDL137 十檢、MDL136 八檢、MDL135 31 檢;SelftestGrid v0232 第 189 站改十三檢(193 站不變)。

## 十六、批390:輸入主控台——左面板輸入、右面板矩陣(`via-console`)與日交易×籌碼對齊(`via-align`)

操作員令:「左面板有輸入介面,右面板是顯示介面;VDF 可新增查詢標的(總體經濟指標分 PMI/通膨/就業…;台灣股票分 TWSE/TPEX 可新增代碼);輸入項目類別拆細;起始日期個別可改;財報分當季/累計/年度、年起迄;DEFAULT 都是最新;目前資料庫狀況;台股每日交易資訊及籌碼要對齊數量,作為更新股票清單並核對一致;輸出 parquet 增量、DuckDB 管理;所有輸入介面在左側面板,右側矩陣有篩選、大到小;儘量 Windows U/I 下拉/勾選/全選/全不選;VRN 輸入可有資料夾、Windows I/O 拖曳、啟動、人機互動動畫、高自動化;VRN 要看整體跑況 BASIC INFO / SUMMARY / FINANCIAL DATA(VERIFIED/FAIL);其他含輸入介面儘量簡單但維持個別改動;VAP 也一樣」。

- **冊** `VIA_InputConsole_Spec_v0100.json`:三族 37 項,每項綁母倉現役引擎與真旗標(尾版 glob):台股 ENG054 增量/ENG064 歷史(起迄)/ENG056 籌碼(天數)/ENG057/ENG081 對齊與清單/ENG063 月營收(代碼)/ENG079 need;總體經濟 ENG074 FRED(類別勾選自 `macro_ssot` 展開 `--only`,`--since`)/ENG047 細目/ENG055 車道;財報:三大報表 **PLANNED**(母倉無現役 MOPS 擷取引擎;期別/年起迄先入冊 `VDF_Input_Interface_Matrix`,引擎上船即接)、ENG075 月營收回補;ETF/全球/庫狀況(ENG073/ENG079);VRN ENG072→073→074→080→MDL138 鏈(`--dir` 報告夾);VAP ENG015/009/014/016。預設 `start=latest`=不帶旗標=引擎增量律;`user` 段=操作員個別改動(只增不減;台股代碼/期別/VRN 路徑鏡寫活冊)。
- **引擎** `CGC_MDL139_InputConsole_v0100.py`:`status`(庫狀況=ENG073 架構冊快照+DuckDB 現值;對齊=ENG081;台股清單=焦點冊∪操作員;宏觀 13 類;VRN 跑況判準:BASIC INFO=代碼+日期+價;SUMMARY=摘要非空;FINANCIAL DATA=VERIFIED(價表核對態 EXACT/ROUNDING/DB_DERIVED 且有指標)|FAIL(公式不符/無指標)|PENDING;項目可跑態 READY/PLANNED/ENGINE_MISSING/NEED_DIR)、`set k=v`、`argv`/`run --item`(參數白名單)、`build` 頁(零 CDN)。八檢。
- **頁** `VIA_UI_InputConsole_v0100.html`:左 rail 三族表單(下拉/勾選/全選/全不選/逐項起始日「最新」勾/拖曳區/`webkitdirectory` Windows 選夾),右 main 八矩陣(篩選、點欄排序預設大到小、勾選),進度動畫輪詢樞紐 `/status`。樞紐同源 `http://127.0.0.1:8765/console` = LIVE 可啟動;`file://` 頁 = SNAPSHOT 只看並印等價短令。
- **橋** DeckServer v0132:`GET /console`、`/console_status`;`POST /console_run{item,params}`(冊白名單+參數逐項驗證→單一啟動道)、`/console_set{ops}`;任務冊 50→52(`console_ui`/`align`);`/status` 併列 `console:<item>`;安全模型零變(同源 CSRF POST;零 CORS)。23/23。
- **對齊** `VDF_ENG081_UniverseAlign_v0100.py`(`via-align`):`check` 逐日核對價表票數 vs 籌碼票數(inst∪margin 經 `tw_listings.yf_ticker` 對映)→ ALIGNED/PARTIAL/MISALIGNED + 最新日差集;籌碼落後價表=誠實指路 `via-chip run`;`update --apply` → `tw_universe`(anti-join 只增)+ `mega/tw_universe_<ts>.parquet` 只含新增列。八檢。boot 鏈 +⑰ check +⑱ 建頁。

```powershell
via-reload; via-console                     # 建頁(零 CDN)
via                                         # 帶起樞紐 8765
start http://127.0.0.1:8765/console         # LIVE:左輸入→▶ 啟動;或 via-open 主控台(SNAPSHOT 只看)
via-align check; via-align update --apply   # 日交易×籌碼對齊 → 更新 tw_universe
via-console set tw-add=6488:TPEX macro-cats=Business,Prices,Labor fin-period=累計 fin-from=2022
```

### 批391 工作站實錄補:LIVE 開頁走 `via-open`、對齊引擎讓庫律

- `start http://127.0.0.1:8765/console` 會被零跳出律(PS 側 `Start-Process` 閘)抑制。正道:`via-console --open`(先探樞紐 8765,在線即以瀏覽器 exe 開 LIVE 網址;離線開快照頁並印修法),或 `via-open LIVE`。`via-open` 自 v0157 起認 `http(s)://`(只走瀏覽器 exe,閘外)。
- `via-align check` 真跑:籌碼最新日落後價表 13 日 → MISALIGNED 並指路 `via-chip run`(日更鏈 ③ 籌碼增量);`update --apply` 撞日更鏈/回補的單寫者鎖曾 traceback → 讓庫律:短等重試 6×3s,逾額誠實 `[FAIL] 庫忙` rc3 印修法(等背景鏈跑完再 `update --apply`;`check` 唯讀)。

```powershell
via-reload; via-console --open              # 樞紐在線=開 LIVE(可按啟動);離線=快照頁
via-align check                             # 唯讀;籌碼落後=先跑籌碼增量(日更鏈 ③ 或 via-py vdf ENG056 run)
via-align update --apply                    # 日更鏈/回補跑完後再寫 tw_universe(讓庫律誠實等/停)
```

## 十七、批392:參數最小化——啟動跑一切、統一起始 2023-01-01、VRN 三 TAB 核對(VDF 為主)、接棒狀態台(`via-handover`)

操作員令:「參數最小化;VRN 只是透過 Windows I/O 或拖曳式檔案及資料夾,啟動就跑了;台股除了財報可選股票外其他都是抓全部;國際資訊現有哪些、增減那些,勾選功能可放右面板;啟動跑一切;輸入及運作結果矩陣;TAB2 BASIC INFO WITH VERIFIED STATUS;TAB3 SUMMARY MATRIX;TAB4 FINANCIAL DATA VERIFYING,如果報告歷史值跟報告值不同,VDF 抓來的資料歷史值為主;起始時間統一 2023-01-01 起到最新;單一種資料庫儲存可個別整類改起始日,齊 YYYY-MM-DD,格子中「-」不動,未輸入前顯示淺色 YYYY-MM-DD,輸入數字自行填上;VAP 規格細節跟圖片顯示;VDF VRN VAP 都跑成功了嗎;VIA Central Console 一定是超詳細的系統狀態如 handover reports,表格最佳化、分門別類堆疊矩陣一頁展示,可轉換成 MD 供下一日接棒」。

- **冊 v2** `VIA_InputConsole_Spec_v0100.json`:`defaults.start=2023-01-01`(統一起始;`latest`=不帶旗標=引擎增量律);`user.group_starts` 整類起始(呼叫參數 > 單項 > 整類 > 預設);台股群除財報(`fin_statements`)/月營收(`tw_revenue_codes`)外零代碼參數=抓全部;`intl` 群(原 global)讀寫 `VDF_Input_Interface_Matrix` 的 INTL_DAILY/INTL_FIN 兩節;VRN `minimal=true`(拖曳即跑;`chain_default` 五段);VAP `specs_csv`(40 規格)+`image_dirs`。
- **引擎 v2** `CGC_MDL139_InputConsole_v0100.py`:`effective_start`;`apply_set` +`group-start=<群>:<日|latest>`、`intl-add/intl-remove/intl-item-add/intl-item-remove`(零刪除:軟移除入 `removed_*`,可 `--restore`);`fin_final` 核對律:報告值 vs VDF 歷史值 → 一致(VDF 為主)|不同→VDF 歷史值為主(單位差 ×千/×百萬 標)|無 VDF 對照=報告值(誠實)|報告缺=VDF;`vrn_tabs`:TAB2 BASIC INFO(核對態 VERIFIED|FAIL)/TAB3 SUMMARY 矩陣/TAB4 FINANCIAL(價、上漲、營收 vs `tw_monthly_revenue`);`vap_specs`/`vap_images`;`family_success` 三族最近一次真跑落檔。十檢。
- **頁 v2**:左 rail `▶ 啟動全部 VDF`(冊內全部可跑項依序入樞紐)、整類起始遮罩 `dmask`(`YYYY-MM-DD` 淺色提示、只收數字、「-」固定)+「最新」勾、VRN 拖曳/`webkitdirectory` 選夾上傳 → 樞紐 `/intake`(dest `vrn_incoming`)→ 自動啟動整條鏈;右 main 12 矩陣:輸入×運作結果、國際資訊勾選、TAB2/3/4、庫狀況、對齊、清單、宏觀、VAP 規格與圖(LIVE 走樞紐 `/vap_img?p=` 白名單道;SNAPSHOT 走 `file://`)、「跑成功?」、執行狀態。
- **接棒狀態台** `CGC_MDL140_HandoverConsole_v0100.py`(`via-handover`):只讀現役 `*_latest.json`(ENTRY/ENV_GOV/RUNGATE/FAMILY_UI/CONSOLE/ALIGN/UNIVERSE/COVERAGE/LOCALDB/VRN/VAP/boot log)+ git 現況 + 缺口冊 `VIA_Handover_Gap_Register` → 15 類分門別類堆疊矩陣一頁 `VIA_UI_Handover_v0100.html`(零 CDN;頁內「複製 Markdown」)+ `VIA_Reports/handover/HANDOVER_latest.md`/`.json`;缺料誠實 UNKNOWN;八檢。DeckServer v0133 `GET /handover`(注入權杖)、`GET /vap_img`(夾內守衛+副檔名白名單;越夾=404)、任務冊 52→53(`handover`)。
- **登錄**:Register v0158 `via-handover`(探樞紐 → `via-open 接棒LIVE` 或快照頁)+ `via-open` 別名 接棒/接棒LIVE;Manager v0120 正式名稱 53;MDL136 plan 16 步;MDL138 HUB_PAGES;SelftestGrid v0235 第 196 站;Console GOV-25;SSOT 動詞;boot ⑲;台帳 877。
- **「VDF VRN VAP 都跑成功了嗎」誠實答**:「跑成功?」分頁與接棒頁只認最近一次真跑落檔——VRN 能跑閘 GREEN、VDF 價表已整併但籌碼落後價表(對齊 MISALIGNED 直到日更鏈 ③ 補齊)、VRN 尚無報告(丟 PDF 即跑)、VAP 頁存在但未逐圖驗證、財報三大報表 PLANNED;不假綠。

```powershell
via-reload; via-console --open              # v2 頁:樞紐在線=LIVE(▶ 啟動全部 VDF;VRN 拖曳即跑)
via-handover --open                         # 接棒狀態台:15 類堆疊矩陣一頁;頁內複製 Markdown / via-handover md
via-console set group-start=tw_equity:2024-01-01 intl-add=INTL_DAILY:^FTSE   # 整類起始/國際資訊增減(可選)
via-align check; via-align update --apply   # 背景日更鏈/回補跑完後(讓庫律誠實等/停)
```

### 批393 工作站實錄補:清單基準日律、持鎖者解析、`via-bg`

- 實錄 A:`via-align update --apply` 以最新價日 2026-09-07 建清單,但該日價表只有 399 票、籌碼 0(日更未齊+籌碼落後)→ `tw_universe` 首快照 399 列=殘缺(只增不減,留存;`status` 現標 PARTIAL 快照)。修:基準日律——`update` 預設取最新「雙側齊日」(價表票數 ≥ 窗內最大 60%、籌碼有票、判定 ALIGNED/PARTIAL;實錄即 2026-08-25 價 1978 籌碼 1935),最新價日殘缺=誠實 YELLOW 改基準並印修法;`--asof YYYY-MM-DD` 指定;`--allow-latest` 強制最新價日;`check` 逐日標「價未齊」;`status` 標殘缺快照並報現役 `current_asof`。
- 實錄 B:`[FAIL] 庫忙` 指路 `via-status`,但 `via-status` 開的是同步狀態頁不是進程表。修:ENG081 自 IOException 解析持鎖者 PID → 命令列 → 引擎名+動詞,印一次 `[庫忙] 持鎖者 PID 7396:VDF_ENG064_HistoryBackfill_v0102.py run`;`[FAIL]` 句改指路 `via-bg`(Register v0159:`Get-CimInstance Win32_Process` 唯讀一覽 VIA 背景引擎 PID/已跑分鐘/引擎+動詞;絕不 `Stop-Process`)。十一檢。
- 實錄 C:`via-handover` 不認=批392 一貼首行 `via-reload; via-console --open` 被前一段尾註 `# …` 吞成註解(上一段貼入時末行無換行,兩段接成一行)。修法:貼之前先按一次 Enter 讓提示字元回來;本文件一貼自此改「註解獨立行、指令純行」。

```powershell
# 先按 Enter 讓提示字元回來,再整段貼(批393 後一貼皆此式)
via-reload
via-bg
via-align check
via-align update --apply
via-handover --open
```

### 批394 工作站實錄補:`via-chip`/`via-price` 登錄、接棒台點名 RED 燈與缺件

- 實錄 A(批393 一貼全綠):`via-bg` 無背景進程;`via-align check` 標 09-03/09-04/09-07 價未齊;`update --apply` 基準日自動改 2026-08-25、`tw_universe` +1979 列;`via-handover --open` 建頁成功(樞紐離線=快照頁)。
- 實錄 B:ENG081/ENG056 docstring 指路的 `via-chip` 在短令冊從未登錄=死路(Zero-Hydra 違律)。籌碼止 08-25 的根因:ENG056 交易日曆=價表實際日期,日更鏈 ③ 跑時價表尚無 08-26 之後交易日(ENG064 回補在後才補齊),故那些日子從未入待抓;現在 `via-chip run` 即補 10 日 × 4 車道(約 1 分鐘)。修:Register v0160 `via-chip`(ENG056 run/--derive/--status)、`via-price`(ENG054 增量 run/--status;別名 `via-tw-backfill`)+ 三梭;`via-align check` 的修法句改指 `via-price run`。
- 實錄 C:接棒台印「未跑/缺 1 · 判定 RED」看不出是哪一類。修:MDL140 摘要 +`red`(RED 燈名)+`missing_names`(缺件來源),build/status 行點名。

```powershell
# 先按 Enter 讓提示字元回來,再整段貼(籌碼補 10 日約 1 分鐘;價未齊日由 via-price 補)
via-reload
via-chip run
via-chip --derive
via-price run
via-align check
via-align update --apply
via-handover
```

### 批395 工作站實錄補:籌碼回補「卡斷」修——自庫重建 checkpoint、20 加速器平行、動態進度條、Ctrl+C 安全

- 實錄:`via-chip run` 印「交易日 649 · 待抓 1800 日×車道(節流 1.2s)」後 96 秒零輸出(v0101 每 80 件才印一行)→ 操作員 Ctrl+C → `KeyboardInterrupt` 裸 traceback,緩衝列與 checkpoint 全失。待抓 1800 的根因:本 worktree 的 `chip_checkpoint.json` 不知道 ENG079 整併/他機回補進庫的日子,只憑 checkpoint 就要重抓 450 日 × 4 車道(約 36 分鐘)。`via-price run` 已把 09-03/09-04 補齊到 1978 票(09-07 仍 400,Yahoo 尚未齊;`failed 1424` 保留重試權)。
- 修(ENG056 v0102):① checkpoint 自庫重建——啟動時自 `tw_chip_inst`/`tw_chip_margin` 既有 (date, market) 標記該日該車道已完成並回寫 checkpoint(1800 → 只剩真缺的日×車道);② SuperAccel `accel_map` 平行(加速器 #12/#19,同 ENG054 律)`--workers N` 預設 4,每工保留 1.2s 節流,小塊提交(Ctrl+C 最多等一塊),一塊傳輸敗過半=自癒減工;③ 動態進度條+數字(加速器 #16 `Write-VIAProgress` 同款):`[####----] 37.5% 675/1800 · OK · 空 · 敗 · 至日 · 速率 · ETA`,非 TTY 每 40 件換行,`VIA_Reports/vdf/chips/PROGRESS.json` 供主控台/接棒台;④ Ctrl+C → 先落緩衝列(parquet+upsert)再存 checkpoint,印 `[中斷] … 重跑續補` rc130 零 traceback。九檢。SelftestGrid v0237 第 100 站。
- 接棒台點名:`RED 燈 entry,env,vrn · 未跑 localdb:覆蓋`——各自來源:`via-entry`(入口燈板)、`via-envgov`(環境治理)、`via-vrn4`(一題四點;尚無報告=RED 誠實)、`via-vdfdb coverage`(覆蓋缺口);皆是「來源自己的判定」,接棒台只彙整。

```powershell
# 先按 Enter 讓提示字元回來,再整段貼(籌碼只補真缺;進度條每 0.5 秒重繪;Ctrl+C 安全)
via-reload
via-chip run
via-chip --derive
via-align check
via-align update --apply
via-handover
```

### 批396 工作站實錄補:`via-rebuild` 登錄、環境治理 RED 的安全路徑、coverage 哨兵

- 實錄(批395 一貼全綠):`via-chip run` 自庫重建 +1760、待抓 40、四工 1.95 件/秒、落庫 33,584 列;08-25 至 09-04 全轉 PARTIAL;清單基準日前進至 2026-09-04(+1978 列);`via-vdfdb coverage` 16 表;接棒台缺件歸零,RED 燈剩 entry/env/vrn。
- `via-envgov` 裁決 RED(BASE 317 件 136 衝突;via_iso_scrape_H/via_paddle_311/via_vrn_312 候 REBUILD;base manifest 缺 28;封鎖家族件 14),digest「下一指令」指路 `via-rebuild --env <境>`,但短令冊從未登錄(與批394 `via-chip` 同類死路)。修:Register v0161 `via-rebuild`(MDL050 多環境隔離重建;旁建零破壞;無參數=`--offline` 唯讀計畫;`--split` 為 MDL135 提案、MDL050 尾版尚無 → 改以 `--env --offline` 唯讀並印明)+ `via-rebuild.cmd`;`via-entry` 次序文字 15 步→16 步含 console/handover。
- 安全路徑(皆非破壞;破壞段 `--approve-remove` 一律由操作員另下令):`via-envgov apply --approve --only-kind REPAIR_BASE`(base 補 manifest 缺 28)→ `via-rebuild --env via_vrn_312`(旁建驗綠;原境不動)→ 再看 digest。entry RED 隨 env RED 連動;vrn RED=尚無報告。
- ENG079 `coverage`:哨兵列 `_NOOP_`(1900-01-01)不計入票數/年分佈(實錄 tw_daily_prices 顯示 1981 票含 1900:1票=哨兵)。十三檢不變。

```powershell
# 先按 Enter 讓提示字元回來,再整段貼(皆唯讀或非破壞;不含 --approve-remove)
via-reload
via-rebuild --env via_vrn_312
via-envgov apply --approve --only-kind REPAIR_BASE
via-envgov
via-handover
```

### 批397 工作站實錄補:雙副本律(`via-pin`)

- 實錄:在 `PS C:\Users\tonyk>` 新視窗 `via-reload; via-famui vdf,vrn --open` → 載到 `Register-VIA-Commands-v0148.ps1 · HEAD c14d428c → c14d428c`,`via-famui` 不認。根因:`$PROFILE` 點源的是 Github 母副本(分支 `main`,c14d428c = PR #30 基底),`via-reload` 分支感知只拉 `origin/main`;PR #30 未併,母副本永遠拉不到批381–396。b381 副本(`Downloads\movies-dataset-b381`,分支 `claude/…`,e7989bc8,v0161)只在該資料夾啟動的視窗生效。另:貼入的文字含終端輸出(`remote: …`、`Fast-forward` 等),PowerShell 逐行當指令跑=一串 ParserError,無害但吵;只貼程式碼框內文字。
- 修:Register v0162 `via-pin`——把 profile 的 VIA 點源行換成本窗副本(`--show` 只看;只改 profile 一行;兩副本檔案零觸碰);`via-reload` 印雙副本提示(profile 預設副本 ≠ 本窗副本時指路 `via-pin`)。PR #30 合併後母副本自然拉齊,`via-pin` 回指母副本即可(操作員令「合併」未下,不自行合併)。

```powershell
# 在任何新視窗(先按 Enter 讓提示字元回來;只貼本框內文字)
. (Get-ChildItem "C:\Users\tonyk\Downloads\movies-dataset-b381\VeritasIntelligenceAnalytics\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName
via-reload
via-pin
via-famui vdf,vrn --open
```

## 十八、批398:收尾閘——VRN 驗證收尾(VAL)與 VAP 產出收尾(`via-closeout`)

操作員令:「將 VRN VAL 收個尾吧」。收尾=「跑成功了嗎」的最後一道誠實閘:不另算、不另抓,只彙整母倉現役引擎的落檔與判準,逐份/逐圖給 DONE|FAIL|PENDING、總判 GREEN|YELLOW|RED|GREY、下一步短令,落 JSON+Markdown 供接棒台讀。

- **引擎** `CGC_MDL141_ClosingGate_v0100.py`(`via-closeout [vrn|vap|all] [--run] [--dir 夾] [--json]`;別名 `via-vrnval`/`via-vapval`;以 `via_vrn_312` python 啟動):
  - **VRN**:報告夾(`functional modules/VRN/input_reports` ∪ `input/incoming`)每一份 → 五段鏈 收件→首頁(ENG072 sidecar `VIA_Reports/first_page_text/<stem>.json`)→入庫(ENG073 `vrn_report_basic`)→財報頁(ENG074 `vrn_report_financial` / ENG073 metrics)→四點(ENG080 `vrn_four_point_digest`);核對態沿用 MDL139 正本 in-process(`basic_verified`/`classify_report`/`fin_final`/`vrn_tabs`:TAB2 BASIC INFO VERIFIED|FAIL|PENDING、TAB4 報告值 vs VDF 歷史值 一致|不同→VDF 為主|無對照);逐份 DONE(五段全通且 VERIFIED)|FAIL|PENDING;總判:無報告=YELLOW(候操作員丟 PDF)· 有 FAIL=RED · 有未跑完=YELLOW(最低停段)· 全 DONE=GREEN · 庫缺/duckdb 缺=GREY;次步直指該補的鏈段(`via-console run --item vrn_firstpage` …)。
  - **VAP**:規格冊 `VIA_VAP_All_Chart_Specs`(40 條)計數 + 產出夾(`vap_one`/`vap_stack`)逐圖驗:SVG 有 `<svg>` 與繪圖元素且無外部連結、PNG 簽章與 IHDR 尺寸、HTML 有圖且零 CDN、PDF 簽章;VAP ONE 台帳末筆;逐圖 OK|FAIL;總判:夾缺=GREY · 無圖=YELLOW · 有壞圖=RED · 全好=GREEN。
  - `--run`:先經 MDL139 `run --item` 跑鏈(vrn=冊 `chain_default` 五段,`--dir` 只給有 dir 參數的段;vap=`vap_one_render`;任一段 rc≠0 即停)再收尾。落 `VIA_Reports/closeout/CLOSEOUT_latest.json/.md`(+`VRN_`/`VAP_`)。八檢(臨時庫/臨時夾/假圖;零網路)。
- **登錄**:Register v0163 三短令+三梭;MDL140 接棒台 vrn/vap 類 +「驗證收尾」「產出收尾」矩陣 +`closeout` 燈;MDL136 plan +`via-closeout`(17 步);SelftestGrid v0238 第 197 站;boot ⑳(只讀);Console GOV-26;SSOT 動詞;台帳 883。
- **誠實現況**(工作站):VRN 報告夾空、庫無 `vrn_report_basic` → 收尾 YELLOW「尚無報告」,丟 PDF 進主控台或 `via-closeout vrn --run --dir <夾>` 即整條鏈;VAP 產出夾有無圖由 `via-closeout vap` 逐圖判,不假綠。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-closeout                                   # 兩族只讀收尾:VRN 無報告=YELLOW 屬誠實;VAP 逐圖 OK|FAIL
via-closeout vrn --run --dir "C:\Users\tonyk\Downloads\reports"   # 有報告夾時:先跑五段鏈再收尾(路徑換成您的夾)
via-handover                                   # 接棒台 vrn/vap 類含收尾矩陣;closeout 燈
```

### 批399 自審修(code review 十一項 → 九修)

- MDL141:次步冊 off-by-one(stage 是「已完成段」,次步應指下一段);報告夾律 `_report_dirs`(`--dir` > `user.vrn_dir` > 冊 `dir_default`;相對路徑=母倉相對;incoming 一律併入)與 MDL139 `dir` 參數同律。
- ENG056 v0102:五處開庫改走讓庫律 `_connect`(撞單寫者鎖=短等重試;永鎖=誠實 `[FAIL] 庫忙` rc3 指路 `via-bg`,不再裸 traceback)。
- MDL139:宏觀面板 since 與 `resolve_argv` 同律(`set macro-since=` 經 `group_starts` 生效);`vap_images` 以實路徑去重;`fin_final(0,0)`=一致;頁面 `chainRun` 加 `.catch`(樞紐斷線=停於該段印明)。
- MDL140:收件夾只算 `.pdf/.docx`(`.gitkeep` 不再誤列為報告);頁面占位純量先換再拼 Markdown/快照;`_rows_from` 死碼修。
- 不修並註:ENG081 `--asof` 遠日窗寬效能(少用;可接受)。
- 工作站實錄(批397/398 一貼):profile 原指第三份副本 `C:\Users\tonyk\movies-dataset`(`claude/via-system-followup-tz7k9t` c14d428c),`via-pin` 已換 b381;`via-famui` YELLOW(vrn 四點 DATA=報告表缺;vap 儀表板 rc1 舊頁在位);`via-closeout` VRN YELLOW 尚無報告、VAP GREY 產出夾皆缺;`--dir "C:\Users\tonyk\Downloads\reports"` 為示例路徑不存在=NEED_DIR 誠實停。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-closeout vap --run          # VAP ONE 渲染後逐圖驗(via_vap_312)
via-closeout vrn --run --dir "<您放研究報告 PDF 的資料夾>"   # 有報告才跑
via-handover
```

## 十九、批400:八流程並進——一次修完可修的、其餘下一次、不傷系統、零九頭龍

操作員令:「可同時修完的問題一次修完;不能的下一次;不傷害系統;不發生九頭龍問題;多流程 8 個平行流程向前推進」。做法:八個子流程各只碰各自的引擎檔,共用登錄檔(短令冊/台帳/SSOT/docs/README)由主線最後整合;全面自測在隔離 worktree 跑,只報紅不改碼。

| 流程 | 修了什麼 | 自測 |
|---|---|---|
| F1 收尾閘 MDL141 | `vap --run` 無 config → 先 `--demo` 產示範圖再逐圖驗(印明);`vrn --run` 報告夾空=一行指路、不跑鏈、零 NEED_DIR | 八檢 8/8 |
| F2 接棒台 MDL140 | 收件夾三態:有件 GREEN、在位但空 GREEN「空」、夾缺 GREY(不再誤報未跑) | 八檢 8/8 |
| F3 對齊 ENG081 | 逐日計數 SQL 端化(`FULL OUTER JOIN` 計數;籌碼對映仍走 `chip_ticker`);`--asof` 遠日 16.6 s/240 MB → 0.38 s/0.5 MB;輸出逐位元相同 | 十二檢 12/12 |
| F4 單一入口 MDL136 | `deadends` 短令死路掃描器(`via-deadends`):真倉 158 令/2,554 處未登錄;`via-chip`/`via-rebuild` 已不在 | 九檢 9/9 |
| F5 儀表板 ENG009 v0107 | 缺料前檢:缺件/缺表逐項指補料短令,rc2 誠實停、舊頁在位;鎖住走讓庫律 rc3;MDL138 roster `data_gate` | 十六檢 rc0 |
| F6 樞紐/總控 | Deck v0134 +`closeout` 任務(54);Manager v0121 正式名稱「收尾閘再生」;總控頁再生;契約測試 19/19 | 25/25、10/10、19/19 |
| F7 主控台 MDL139 | 「收尾」分頁(第 13 頁):三族判定、VRN 逐份、VAP 逐圖;LIVE/快照同路 | 十檢 10/10 |
| F8 全面自測 v0238 | FAST 191 站:OK 135 / FAIL 50 / SKIP 6;49 紅=沙盒缺庫缺料(pandas/fitz/pyarrow/duckdb 檔);**1 真發現**:雙橋稽核「網路缺 2」(MDL135 `mirror_health`、MDL134 `online` 直用 `urlopen`)→ 補掛 NET-BRIDGE(MDL134 併補 ACCEL-BRIDGE)後 網路缺 0、加速覆蓋 99.6%、自動總跑器 S1 GREEN | — |

- **不修(下一次/需操作員令)**:`via-envgov` RED 的環境重建(`--approve-remove` 段);09-07 Yahoo 價未齊(資料面);VRN 需真實報告 PDF;158 個舊令的登錄工程;`update()` 的 `executemany` 效能(F3 註)。
- 登錄:Register v0164(`via-entry` 白名單 +`deadends`;`via-deadends` 別名+梭);SelftestGrid v0239 站名;SSOT 動詞;Console 註;台帳 885;README(`via-deadends` 列與「本表以實掃為準」註)。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-closeout vap --run          # 無 config 自動走 --demo:產示範圖 → 逐圖驗 → VAP 收尾應轉 GREEN
via-deadends                    # 短令死路實掃(唯讀;落 DEADENDS_latest.json)
via-handover                    # 接棒台:收件夾「空」GREEN;closeout 燈
```
