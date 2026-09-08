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

## 二十、批401:VDF 完工——台股被動 ETF 價格補源(0050 等)

操作員令:「先將 vdf vrn 完工」。工作站 `via-align check` 差集實錄(`ALIGN_latest.json.mismatch`)查出「只籌 8 票」恆定不變:`0050/0051/0052/0053/0055/0056/0057/0061`——全是知名 TWSE 上市被動 ETF。

- **根因**(程式面,非資料面):`VDF_ENG054_TWDailyBackfill` 的 `fetch_listings()` 只從 TWSE `t187ap03_L`/TPEX `mopsfin_t187ap03_O` 兩個「上市/上櫃公司產業分類」端點抓票——ETF 是基金不是公司、天生沒有產業別,從未進過清單,`tw_daily_prices` 因而永遠零 ETF 列。籌碼面(`ENG056` 的 T86/MI_MARGN 逐日申報端點)不靠預建清單、當天有申報就有,ETF 本來就有三大法人/融資融券資料,所以差集恆定卡在這 8 檔。
- **端點驗證**(真連線查實,非猜測硬寫):TWSE openapi 根目錄非目錄頁(734 bytes、零 ETF 字樣)死路;改用 `isin.twse.com.tw` ISIN 分類頁系統性掃過候選 `strMode` 值(1/2/4/5/6/13),以不會假陽性的「元大台灣50」全名鎖定,確認 `strMode=2` 混合上市股票與 ETF(欄位:代號+名稱、ISIN、上市日、市場別、產業別〔ETF 為空〕、CFI 碼〔ETF 為 `CE` 開頭,普通股 `ES` 開頭〕)。同時發現 `VDF_ENG077_ActiveETFUniverse`(主動式 ETF 宇宙,批374)已在用 TWSE openapi **JSON** 端點 `t187ap47_L`(ETF 冊,含被動+主動)——比 ISIN 頁的 Big5 HTML 解析乾淨、且與既有 `t187ap03_L` 同一 `net.http_json()` 車道,改採此端點。
- **修法**(`VDF_ENG054_TWDailyBackfill_v0104.py`,`via-price`/`via-tw-backfill` 新尾版):新增 `fetch_etf_listings()` 抓 `t187ap47_L`,只收四碼數字被動碼(如 `0050`);五碼+A 主動碼(如 `00981A`)留給 `ENG077`(`via-etfuniv`)專責每日持股揭露追蹤,不重複收——Zero-Hydra 分工,兩端點分類互斥(個股產業分類 vs 基金冊),`(code, market)` 鍵結構性不會相撞。`run()` 併入 `tw_listings` 落庫,下游 Yahoo chart 抓價/checkpoint/增量律全程不用改(邏輯與券商代碼無關)。九檢(原八檢+新增 ETF 補源檢:被動收、主動排、FAIL 誠實回空不阻斷雙所清單)。
- **不修**(機制不同,非同類問題):另一差集「只價 44 票」(幾乎全 `.TWO` 上櫃小型股,有價無籌碼)——籌碼面本來就是當天有申報才有、不靠清單,這批比較可能是真實稀疏(小型上櫃股法人/融資融券活動本就少),沒有像 ETF 那樣明確的程式面根因,記為已知邊界暫不追。
- **登錄**:SelftestGrid 站名同步(「台股回補工人六檢」→「九檢」,批136/401);台帳 886。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-price run
via-align check
```

## 二十一、批402:加速/網路雙正典令——VeritasCeleritas 加速器、VeritasAegisNexus 網路核、PS 20 加速器、AST 多輪修正引擎

操作員令:「所有外部資料透過 VDF 取 · 所有 PY 檔導入 `VeritasCeleritas.py` 加速器 · 所有向外擷取資料檔全部導入 `VeritasAegisNexus.py` · PS 指令一律加入 20 個加速器不卡斷、一個指令完成一切 · 啟動 PowerShell 指令語法多輪並行安全修正引擎」;另一會話結論「VDF 加速只認 Celeritas、網路只認 AegisNexus;737/740 留作橋,不直 import;不代設 `VIA_NET_CONSENT`」。本批先查鏈再動筆(Zero-Hydra:不另造第二套實作,只校正既有委派鏈的指向與覆蓋):

- **加速鏈(已通,零改)**:引擎 `[VIA:ACCEL-BRIDGE]` → `VIA_SuperAccel_Module.py`(殼)→ `SUP_MDL737_SuperAccelModule_v0104`(`celeritas()/fetch()` 即 `import VeritasCeleritas`)→ `VeritasCeleritas.py`(88 庫能力冊+執行緒預算)。737 自測 9/9、`--activate` 真載 Celeritas OK。**更正前次誤判**:`VeritasCeleritas.py` 不是死檔,是加速鏈的正典終點(先前只 grep 整合總冊與殼未見其名而誤稱 legacy)。ACCEL 覆蓋:全樹僅註冊夾 5 檔缺(MDL129/130 v0101、MDL133 v0100/v0101、DefTestAudit v0101)→ 補掛後 100%;各件自測不變(8/8、11/11、9/9、9/9;DefTestAudit 無自測,用法 rc2 前後相同)。
- **網路鏈(一處失準,修)**:引擎 `[VIA:NET-BRIDGE]` → `via_net_unified_v*`(殼,glob 尾版)→ `SUP_MDL740_NetUnified`(四車道+雙閘)→ `_aegis()` → **原指 `via_aegis_netcore_v0100.py`(批130 送達件衍生版,4537 行)而非操作員指定正典 `VeritasAegisNexus.py`(5186 行;根層與 `supportive modules/network/` 副本逐位元相同、皆在冊)**。`SUP_MDL740_NetUnified_v0112`:`_resolve_aegis_path()` 改序——① env `VIA_AEGIS_PATH`(指向存在檔才採)② `supportive modules/network/VeritasAegisNexus.py` ③ `supportive modules/VeritasAegisNexus.py` ④ 後備 `via_aegis_netcore_v*`;740 只呼 `fetch_json/fetch_text`,兩核皆備,雙閘/法遵層/四車道零改;二十檢 20/20(新 ⑳:正典優先/env 存在採、不存在忽略/後備在/兩函式在)。殼 glob 尾版自動接 v0112;實測 `VIA_AEGIS_PATH` 已落 `VeritasAegisNexus.py`。
- **NET-BRIDGE 覆蓋(只掛真擷取檔)**:`CGC_MDL124_BridgeSweeper_v0103` +`--net-callers`:去註解/字串字面量後仍直呼 `urlopen/requests/httpx/urllib3/yf.download/yfinance.Ticker/aiohttp` 才算「向外擷取」(本機 `socket.create_connection` 樞紐探測不計;冊內文字提及不計);工具本體(SUP_MDL737/740、via_net_unified、via_aegis_netcore、VIA_NetSupport)與 vendored 件(相對匯入、`pip._vendor`、SPDX 標頭)永不掛(自掛即循環);九檢 9/9。實掛 45 檔:supportive 18(network/ 種子擷取器群、cnn 恐貪、YFinance 引擎、VRN_MDL007 副本…)、VRN 5(MDL001/MDL007 各版、Playwright 雙引擎)、VAP 14(SCOPE_COPY 內 VDF/VRN 擷取件,循批102 全樹前例)、VDF 3(ENG076/079/081,批115 VDF 全導入令補齊);全 py_compile 通、ENG076 8/8、ENG079 13/13、ENG081 12/12 不變。掛法=只增不減:塊內只算路徑、`_via_net()` 惰性載入,原檔直呼一行未改(把直呼改寫為 VIA_NET 車道屬行為變更,須逐檔驗證,另批)。
- **PS 20 加速器**:`VIA_PS_Accel_Module.ps1`(TOOL-101)`$VIA_ACCEL20` 01–20 與操作員名單逐一相同;`[VIA:PS-ACCEL]` 748/761 在冊 ps1(13 未掛=`VIA_Reports/env_governance/` 再生物,不掛);`Write-VIAProgress` 動態進度條(16/17)+`Invoke-VIAGuarded`(18)不卡斷。
- **AST 多輪修正引擎(已在庫,啟動法)**:`via-psrepair`=`Invoke-VIA-PSRepair-v0100.ps1`(批253):R1 唯讀(Accel20 dry-run+PSScriptAnalyzer)→ `-Fix` R2a Accel20 GO_v1 + R2b `CGC_MDL101_PSAstRepair fix`(AST 逐檔、失敗原檔不動)→ R3 PostRepairVerify+再掃+`VIA.ps1` 沙盒解析;沙盒無 pwsh 僅 HEURISTIC_ONLY(846 檔/127 序相依),正式跑在工作站。
- **登錄**:SelftestGrid v0240(站名「統包網路工具二十檢」;+「橋塊掃描注入器九檢」站);README(`via-bridge-sweep`/`via-psrepair` 列);台帳 887。
- **不代設/不動**:`VIA_NET_CONSENT` 不代設(雙閘 fail-closed 照舊);737/740 留橋不直 import;`VRN_MDL009_TrustScore.py` 全倉不存在(其餘 7 件「缺檔」皆在本分支,拉取即得);via-envgov RED 重建仍候 `--approve-remove` 令。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-bridge-sweep --accel --root "supportive modules"
via-bridge-sweep --net --net-callers --root "supportive modules"
via-psrepair
```

## 二十二、批403:六流程並進——PS 修復卡斷修、VRN 三方對照(檔名×首頁×財報頁表格)

操作員兩問:(a)「檢查所有 VRN 檔案有拆解 FILENAME、首頁、財報頁表格、讀取相互對照的引擎模組??」(b) 工作站實錄 `via-psrepair` R1/R2a `rc=1`、R2b「卡斷」,並令「20 個加速器不卡斷、六個獨立步驟、不傷害系統、不產生九頭龍」。六流程各只碰各自的檔,共用登錄由主線最後整合。

- **F1 `Invoke-VIA-PSRepair-v0101.ps1`(卡斷根因修)**:v0100 用 `pwsh -File $accel -ExcludePattern $Excl`。PowerShell 的 `-File` 模式**不支援陣列引數**——`$Excl` 的 9 個樣式被攤平成散落位置引數,第 1 個綁上 `-ExcludePattern`,第 2 個起依宣告序掉進 `-Paths`(位置 1)、`-ThrottleLimit`(位置 3)…於是 `'*\_bytecode_originals\*'` 撞上 `[int]$ThrottleLimit`,報 `Cannot convert value ... to type System.Int32`,R1/R2a 全滅(非設定問題,是真 bug)。改法:子行程改走 `-Command`,於子行程內以「雜湊表字面量+splatting」呼叫(`$p=@{'ExcludePattern'=@('…','…');'ThrottleLimit'=8;…}; & '<腳本>' @p`),陣列真的是陣列、整數真的是整數;仍是獨立行程=收容腳本的 `exit` 不會殺母行程。**收容原件零觸碰**(`references/intake` 不可動律)。並修 R3a:PostRepairVerify 同為 `[string[]]$ExcludePattern` 且 `-PythonExe` 預設是他機硬寫路徑,一併走 `-Command` 道並顯式帶本機解譯器。
- **F1 續:不卡斷(加速器 #16/#17/#18)**:每輪走 `Invoke-VIAGuarded` 看門狗——同視窗直播、逾時 `Kill` 整樹回 `rc=124` 誠實印明(不再無聲吊死);六段輪次進度條(`Write-VIAProgress` Id 12);`-TimeoutSec`(預設 1800)/`-Throttle`/`-ShowCmd` 可調;加速器缺席=graceful 退回直呼。`-Selftest` 八檢純字串驗子行程命令建構(零外呼零寫檔)。`via-psrepair` 走 `Get-VIANewest`,尾版律自動接 v0101,短令零改。
- **F2 VRN 對照盤點(回答 (a))+ `VRN_ENG074_FinancialPages_v0102.py`**:盤點四邊——①檔名拆解=ENG073 `extract_one`(四碼 ticker 逐一對 `tw_listings` 名冊驗證、`BROKER_DICT` 券商、三格式日期含民國)**在位** ②首頁=ENG072 v0105 分區(標題帶/左本文/右資訊/頁尾)+ pdfplumber 法B 雙法逐區對照 AGREE/PARTIAL/DIVERGE **在位** ③財報頁表格=ENG074 **在位** ④檔名↔首頁對照=ENG073 交互驗證(ticker/官方名/升幅 `EXACT_MATCH`·`ROUNDING_ONLY`·`FORMULA_MISMATCH`·`PARSE_SUSPECT`;衝突 `KEEP_BOTH` 不覆寫)**在位**——**唯一缺口=財報頁表格從不與首頁/檔名對照**:v0101 只寫 `vrn_report_financial`,全樹亦只有它自己讀該表,ENG080 四點取的是 ENG073 的 `vrn_report_metrics`。v0102 補第三邊使三角閉合(不另造引擎=Zero-Hydra,對照住在表格擁有者):`crosscheck()` → `vrn_report_crosscheck`:`eps@期間` 首頁 rx 值 vs 表格值 七態(`AGREE` ≤1% / `ROUNDING` ≤5% / `UNIT_SCALE` 比值近 1e±2/3/6=單位差非錯 / `DIVERGE` / `ONLY_FIRSTPAGE` / `ONLY_TABLE` / `MISSING_BOTH`)、表格獨有正典科目列 `ONLY_TABLE`、`ticker_on_fin_page`(檔名 ticker 是否現身財報頁原文)、`report_date_vs_periods`(表格已報年 > 報告日年=`DATE_AHEAD` 誠實可疑)。派生層重算;ENG073 兩表缺=誠實略過不 crash;`run` 內建同輪跑,亦可 `--crosscheck` 單獨重算、`--no-cross` 關閉。十五檢 15/15(端到端:首頁 eps 2024=2.40 對表格 2.40=AGREE、2025 首頁 9.90 對表格 3.10=DIVERGE)。
- **F3 `CGC_MDL141_ClosingGate_v0101.py`**:收尾閘認得第三邊——逐份併列對照欄(AGREE/DIVERGE/ROUNDING/UNIT_SCALE/ONLY_TABLE 計數 + ticker/date 兩態)、總結 `[三方對照]` 行、次步點名 DIVERGE 前五名、未對照=指路 `--crosscheck`。**DIVERGE 屬資訊級誠實旗標(待人工核,非鏈路失敗)故不降 verdict**——九檢 ⑨ 以「同一 fixture 有/無對照表 verdict 相同」對照組實證。
- **F4 `CGC_MDL064_SelftestGrid_v0241`**:站名 財報頁擷取十檢→十五檢、收尾閘八檢→九檢(逐站 2/2 綠)。PS 入口為 ps1、沙盒與 CI 無 pwsh,不設站,改由工作站 `via-psrepair -Selftest` 八檢自驗。
- **F5 docs 本節 + README**(`via-psrepair` 列補卡斷修與看門狗;`via-closeout` 列補三方對照)。**F6 台帳 888 + commit/push/CI/PR**。
- **誠實邊界**:沙盒無 pwsh,F1 只能以「Python 逐字鏡像複刻字串建構器」驗出子行程命令正確(陣列/整數/布林/單引號逸出/零雙引號全過)+ 括號引號平衡檢查,**真跑要在工作站**。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-psrepair -Selftest
via-psrepair
```

## 二十三、批404:PS 修復洗版修 + cherry-lagoon-honey-dove 收容與差異總冊

工作站實跑證實批403 的卡斷根因修生效:`via-psrepair` 三輪全通(R1 `rc=0` 847 檔/976 findings、R3a `rc=0`、R3b `rc=0`、R3c GREEN),18 分鐘零吊死。同一跑暴露三件事:

- **F1 洗版(我造成的,已修)**:`Invoke-VIA-PSRepair-v0102.ps1`。`Write-Progress` 在本場景是淨損——子引擎(Accel20/Verify)自己就印豐富進度,而看門狗每 0.8s 一次 `Write-Progress` 會令主機重繪**所有**在線進度記錄(含本檔輪次列 Id 12),終端每秒冒出數行 `VIA PS 修復三輪 [R1 …]` 把真實輸出淹掉。改法:本檔全面改純文字——不再呼叫 `Invoke-VIAGuarded`(其 0.8s 迴圈=洗版源),改本檔 `Invoke-VIAWatched`(同款 `Start-Process`+逾時 `Kill` 整樹回 124,只每 `-HeartbeatSec` 預設 60 秒印一行心跳);輪次改一行 `[輪次 n/6]`。加速器 #16/#17/#18 的語意(進度可見+逾時不卡斷)全保留,只換呈現方式。九檢(⑨ 零洗版律:不呼 `Write-Progress`/`Invoke-VIAGuarded`、心跳字串與 `HeartbeatSec` 在位;判準以拆字面量寫成,免自測句自撞)。
- **F2 R1 RED(真實待修量,非工具壞)**:847 檔 976 findings,其中 parallel-fixable 65、sequence-dependent 911。65 件可由 `via-psrepair -Fix` 的 R2a 並行安全修處理,911 件序相依需逐檔。**尚未動**——`-Fix` 要操作員下令。
- **F3 R3a RED 的兩個 blocker**:①**5 個不可解析腳本**——我的啟發式括號/引號掃描器在 855 個在冊 ps1 上報 118 個可疑,真 PS AST 只判 5 個,**差距太大表示我這把尺太粗**(PowerShell 的 `$()`、`@{}`、regex 字串、here-string 全會誤判),因此**不猜、不亂修**,真名單要從工作站 `verify_report.json` 取。②`HARNESS_SELFCHECK_FAILED`/`HARNESS_SUSPECT`——收容驗證器的 pytest 連一個 trivial test 都跑不起來,故其「0P/0F/0E」不可信,是**驗證器本身的問題不是程式碼的問題**(誠實記為工具面待查)。
- **F4 cherry-lagoon-honey-dove 收容(操作員令「用他為唯一入口」)**:`add_repo` + 淺 clone(head `ad5b0a17`「Export from Grok」),逐件比對 `attachments/`+`public/via/` 共 63 件 → 同 36 · 異 23 · 缺 4;**只收「異」與「缺」共 26 件**(逐位元相同者不重複收=Zero-Hydra;母倉同名檔一律不覆寫=正本零觸碰,收容件加 `__cherrylagoon` 尾綴並存),落 `supportive modules/references/intake/VIA_GrokConsole_CherryLagoon_b404/` + `VIA_CherryLagoon_Delta_Manifest_v0100.json`(逐件 sha16/狀態/母倉對應路徑/尺寸)。4 件全新:`Invoke-VIA-Spectrum.ps1`、`VRN_PIPELINE_LAUNCHER.ps1`、`VRN_Pipeline_Runner.py`、`Spectrum_preview_dual.html`(4.3MB 產生預覽頁,只記指紋不入倉=倉庫衛生)。
- **正典核對(重要)**:cherry-lagoon 的 `VeritasAegisNexus.py`(5172 行)/`VeritasCeleritas.py`(5694 行)**比母倉正典舊**(5186/5708 行),與 b345/b383 收容件同版。批402 選定的母倉正典因此站得住,無回退風險。
- **TypeScript 面(未動,候裁決)**:`src/lib/via/` 89 模組 + 66 測試共 21,346 行(accel/active-etf/vrn-*/vdf-*/fred/duck-catalog…),是 Grok app 自己的 VIA 層,母倉為 Python/PowerShell 無對應實作。這是架構岔路:①只當參考不整合 ②把 app 接到母倉 DuckDB/引擎(app 前端、母倉後端)③移植成 Python 引擎(=第二套實作,違 Zero-Hydra)。本批不選,列入總冊候操作員裁決。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-psrepair -Selftest
```

## 二十四、批405:母倉成果整合進 Grok app 介面(cherry-lagoon-honey-dove)

操作員令:「透過 GITHUB GROK 上傳介面加計你完成的部分整合到他的介面及版面繼續完成」。

- **推送權限(經過與結果)**:首次 `add_repo(access: push)` 遭安全閘擋下(auto mode classifier),故先做成上傳包交操作員經 Grok 上傳介面放入;操作員隨後明示「你可以進入環境整合」授權,再試即通,已直接推 `tonykuni/cherry-lagoon-honey-dove` 分支 **`claude/via-mother-deck-b405`**(commit `5898fa0`,7 檔 +411/-2)。**未開 PR、未併 main**(未獲該項指令)。上傳包與母倉可追溯副本保留於 `supportive modules/references/intake/VIA_GrokConsole_CherryLagoon_b404/ui_integration_b405/`,兩路等價。
- **接線方式(照該 app 既有慣例,非另起爐灶)**:lib 模組=純資料/邏輯 + `import type { Light } from "./types.ts"` + 每檔一支 `.test.ts`(node:test);元件用既有 `Matrix`/`StatusLight`/`LightLegend`/`Badge` 與既有 Tailwind token。
- **新增 5 檔**:`src/lib/via/tri-xcheck.ts`(VRN 三方對照七態,與 `VRN_ENG074_FinancialPages_v0102` 同律:一致≤1%/四捨五入≤5%/單位差比值近 1e±2·3·6/DIVERGE/單邊/雙缺;`triAffectsVerdict` 明寫 DIVERGE 不降判定)+ 測試;`src/lib/via/psrepair-rounds.ts`(六段輪次契約 + 工作站 2026-09-08 實跑實績 R1 rc=0 847檔976findings、R3a rc=0 但 5 不可解析+HARNESS 不可信、R2a/R2b 誠實 pending 不假綠 + 卡斷根因與洗版修文字)+ 測試;`src/components/mother-deck.tsx`(「母倉」分頁:三方對照五邊矩陣、PS 三輪矩陣、橋覆蓋 521/8/788、本倉收容差異 同36/異23/缺4)。
- **改動 2 檔(各 1–4 行,零刪除)**:`types.ts` 的 `Deck` +`"mother"`;`shell.tsx` 的 import／NAV(`05 母倉`)／`lights`／main 分支。既有 5 個分頁與所有既有模組零觸碰。
- **Zero-Hydra**:`tri-xcheck` 不與既有 `vrn-xval`(報告值 vs API)重疊——那是跨來源,本模組是同一份報告內兩條擷取道;`psrepair-rounds` 沿用既有 `ast-anchor.classifyFix` 做 parallel/sequence 分類,不另造。
- **真跑驗證**(在 clone 上實測,非宣稱):`node --experimental-strip-types --test src/lib/via/*.test.ts` → **224 pass / 0 fail**(原 222 + 本批 2);`tsc --noEmit` → 本批 7 檔**零錯誤**(僅環境級 `@types/node`/`vite/client` 缺,因未 `npm install`,與本批無關)。

## 二十五、批406:主動型台股 ETF 每日持股——回補通路打通(ENG078 v0101)

工作站 `via-etfuniv` 實錄:「23 檔須每日揭露 · 今日已抓 0 · COMPLETE 0 PARTIAL 23 · 回補 tried 0 filled 0 no_source 0」。操作員令回顧:「我只抓主動型台股 ETF 的資料持股」「用 TWSE 去抓」。

- **根因(查車道冊查出,非猜)**:`VIA_ActiveETF_HistoryLanes_v0100.json` 的 17 條車道中,唯一 `VERIFIED` 的 MONEYDJ 是 `LATEST_ONLY`(只給今日),其餘 16 條 `ISSUER_ARCHIVE:*` 全是 `PENDING_SOURCE` 且 `url` 空;`backfill` 的 DATED 分支在 v0100 本來就只是佔位,原碼自註「DATED 車道解析器候接(v0101)」。所以 `tried 0` 不是壞掉,是**根本沒有可呼叫的歷史車道**。
- **不猜端點**:全倉 grep 過所有 TWSE/TPEX/MOPS URL,**沒有任何一條是 ETF 持股/成分**端點;沙盒又連不到 TWSE。依批401 立下的規矩(端點要真連線查實才寫死),本批不硬寫任何持股 URL,改做**發現機制**。
- **`discover [--apply]`**:自 TWSE **OpenAPI 規格檔**(四個候選路徑)真列舉 `paths`,以持股/成分/PCF/基金等中英關鍵字篩出候選,寫回車道冊為 `state: CANDIDATE`(**永不**未驗即標 VERIFIED;只增不減)。四路皆取不到=誠實回 `UNREACHABLE` 並列已試路徑。
- **`parse_holdings`**:JSON(`list[dict]` 欄名對映:代號/名稱/股數/權重,欄名不合慣例時退而找任一四碼值)與 HTML 表雙道 → `(holding_ticker, name, shares, weight)`;判準=**≥5 列**且四碼台股代號與數字皆可辨,不合一律回空(誠實不硬填)。
- **`probe [--ticker] [--date] [--apply]`**:對有 `url` 的非 VERIFIED 車道以真標的真日期取一次、跑上述解析驗證,逐條印 `PASS/FAIL` 與因由(HTTP 態/零列/取用失敗);`--apply` **只把驗證通過者**升為 VERIFIED,不刪車道、不動他條。
- **DATED 回補接上**:`fetch_dated` + `upsert_holdings` → 落 **ENG051 正本表** `holdings_daily`。正本零觸碰:欄名依現表 `DESCRIBE` 逐欄對映、缺欄不寫、**不建表不改結構**(表未建=誠實回 0 並指路先跑 ENG051),鍵 `(portfolio_date, etf_ticker, holding_ticker)` anti-join 冪等。
- **十三檢 13/13**(原八檢 + 本批四檢,全注入式假 net、零外呼):解析雙道、判準誠實(少於門檻/非持股/空皆回空)、發現真列舉與 UNREACHABLE、探測只升通過者、DATED 真回補(同日同列重寫 +0 零倍增、續輪往前推進、全表零重鍵)。自測過程中測出我自己的兩個錯:網路工具契約是 `{state,data}` 我誤寫成 `json/text` 鍵;以及 `max_days=2` 每輪往回推兩天是正確推進、我原本的「重跑應為 0」假設寫錯。
- **登錄**:SelftestGrid v0242 站名;README `via-etfuniv`／`via-etfhist` 列;台帳 891。

```powershell
# 先按 Enter 讓提示字元回來;只貼框內文字
via-reload
via-etfhist discover --apply
via-etfhist probe --ticker 00981A --apply
via-etfhist backfill --max-days 5
```

## 二十六、批406b:工作站首跑修——規格 base 漏 `/v1` 致候選全 404;並記 TWSE 目錄實況

操作員問:「那麼多 404 是不是沒有掛入網路工具?」**不是。** `404 Not Found` 與 `403 Forbidden` 都是伺服器**真的回**給我們的:請求出得去、回得來,證明網路工具有掛且暢通(閘關會回 `DENY`、未掛會回 `NO_NET`、斷線會是連線例外)。`[SuperAccel] 抓取敗(HTTPError)——誠實 None` 也是加速層如實回報,不是壞掉。

- **真根因(我的 bug)**:OpenAPI 規格檔裡的 `paths` 是**相對 base**,不是相對主機根。TWSE 的 base 含 `/v1`(倉內 ENG054/ENG055/ENG077 現役常數皆為 `https://openapi.twse.com.tw/v1/opendata/...`,是既驗證事實)。v0101 首版只接主機名,組出 `https://openapi.twse.com.tw/opendata/t187ap47_L` → 全 404。修:新增 `spec_base()`,序為 OpenAPI3 `servers[0].url`(絕對直用/相對接主機)→ Swagger2 `schemes`+`host`+`basePath` → 退倉內既驗證常數;`discover --apply` 併修既有 CANDIDATE 的錯 url(`VERIFIED` 不動)。十四檢 14/14。
- **discover 本身是成功的**:它真的列舉到 TWSE 目錄並命中 13 條——`/opendata/t187ap47_L`(ETF 冊)、`t187ap46_L_18`、`t187ap02_L`、`t187ap08_L`、`t187ap10_L`、`t187ap11_L`、`t187ap11_P`、`t187ap12_L`、`t187ap13_L`、`/ETFReport/ETFRank`、`/fund/MI_QFIIS_cat`、`/fund/MI_QFIIS_sort_20`。
- **誠實研判(重要)**:這 13 條**看不出有 ETF 每日持股/成分股**。`MI_QFIIS` 是上市公司的**外資持股比例**,不是 ETF 持股;`ETFRank` 是 ETF 排行;`t187ap47_L` 是 ETF 冊(ENG054/ENG077 已在用)。所以修好 `/v1` 之後,預期它們會**取得到(200)但解析不出持股列(FAIL:零可解析持股列)**——那正是判準該給的誠實結果,不是失敗。結論方向:**TWSE openapi 很可能沒有開放主動 ETF 每日持股**,得改走投信 PCF 頁。
- **群益 403 另一類**:伺服器回 403=拒絕,不是找不到。多半要瀏覽器式標頭/referer;倉內有 `VIA_Unified_WebScraping_Playwright_Engine`(雙引擎爬蟲)可走,但那要另掛車道,本批不動。
- **登錄**:SelftestGrid v0243 站名;台帳 892。

## 二十七、批406c:TWSE 定論 + 我的判準太鬆造成 4 條假陽性(收緊與撤銷道)

工作站以修好 base 的 v0101 實跑,拿到**決定性答案**,同時暴露**我的一個真錯**。

- **定論:TWSE openapi 沒有主動 ETF 每日持股。** `discover` 自 `https://openapi.twse.com.tw/v1/swagger.json` 真列舉、base 正確推導為 `.../v1`,命中 12 條,其中文名稱說得很清楚:`t187ap46_L_18` 企業ESG-持股及控制力 · `t187ap47_L` **基金基本資料彙總表**(就是 ENG054/ENG077 在用的 ETF 冊)· `ETFReport/ETFRank` 定期定額交易戶數排行 · `MI_QFIIS_cat`/`MI_QFIIS_sort_20` 外資及陸資持股 · `t187ap02_L` 持股逾 10% 大股東 · `t187ap08_L`/`t187ap10_L` 董監持股不足法定成數 · `t187ap11_L`/`t187ap11_P` 董監事持股餘額明細 · `t187ap12_L`/`t187ap13_L` 內部人持股轉讓。**全是公司內部人/外資/大股東持股,沒有一條是 ETF 成分股。**
- **我的錯(嚴重)**:`probe` 對其中 4 條回 PASS 並升成 VERIFIED——`MI_QFIIS_sort_20`(18 列)、`t187ap08_L`(12 列)、`t187ap11_L`(**27,528 列**)、`t187ap11_P`(6,508 列)。因為我的判準只看「≥5 列 + 四碼代號 + 數字」,董監事持股表全都滿足。若就此跑 `backfill`,會把**董監事持股寫進 ETF 持股正本表**——那比沒資料更糟。
- **收緊三道**:① 列數上下界 `5 ≤ n ≤ 600`(單檔 ETF 單日持股不可能兩萬多列,那是全市場表)② **反指標否決**(董事/監察人/董監/內部人/大股東/外資/陸資/持股比率/轉讓/ESG/定期定額/法定成數/餘額明細/insider/director/supervisor 出現即回空)③ 給了 ETF 代號時,原文須含該代號或含成分股正指標(成分/持股明細/投資組合/基金持股/constituent/holding/portfolio/PCF/申購買回),否則回空。
- **撤銷道(誠實回頭)**:`probe --apply` 現在會**重驗本器自己升過的 VERIFIED**(以 note 內 `probe 驗過` 認定),重驗不過即降回 `CANDIDATE` 並記因由 `曾誤升已撤 · 批406c 收緊判準後重驗不過(…)`;原生 VERIFIED(如 MONEYDJ,非本器所升)不重驗、不動。操作員機上那 4 條會在下次 `probe --apply` 自動撤掉。
- **十八檢 18/18**(+⑮ 反指標、⑯ 列數上限、⑰ 相關性、⑱ 撤銷道)。自測又抓到我兩個 fixture 自撞:DATED 回補的假 payload 沒帶基金代號(收緊後被自己的新判準擋下,改成真實 PCF 樣態帶 `基金代號`);⑰ 的 fixture 名稱寫「成分N」自撞正指標。
- **下一步(方向已定)**:ETF 每日持股要走**投信 PCF 頁**。群益那條回 403(伺服器拒絕,非找不到),需瀏覽器式標頭——倉內有 `VIA_Unified_WebScraping_Playwright_Engine` 可走,但要另掛爬蟲車道,候操作員指示。
- **登錄**:SelftestGrid v0244 站名;台帳 893。

## 二十八、批406d:CI 假紅修——同步狀態台 ④ 檢的「code 前綴白名單」是錯抽象

批406c(`43de99b6`)CI 紅:`CGC_MDL096_SyncStatus` 十檢的 ④「台帳/問題冊唯讀 join」失敗,其餘九檢與 Manager 十檢、DeckServer 25 項全綠。

- **根因**:④ 檢用**前綴白名單**去猜台帳 code——`\b(TOOL|CGC|VDF|VAP|VRN|REG|INTAKE|BENCH|GRID|SHIM|MERGE|REFAIL|CI)-`。但台帳是 append-only、code 可以是任何形狀。批406c 之後尾 8 筆是 `ENG054-`、`SUP_MDL740-`、`PSRepair-`、`GrokUI-`、`ENG078-`×3——**白名單一個都不中**,於是頁面明明正確 join 了台帳,檢查卻報紅。批401–406b 之所以還綠,只是窗內還殘著一筆舊的合規 code;406c 把它擠出去了。
- **這不是第一次**:原本寫死 `"TOOL-"`,批354 就因為「尾筆非 TOOL 即假紅」放寬成 13 個前綴。**放寬白名單只是延後同一個錯**。
- **修法(`CGC_MDL096_SyncStatus_v0109.py`)**:④ 改成驗**真 join**——直接讀 `VIA_AutoCode_Registry_v0100.json` 的尾筆 `code`,斷言它**逐字**出現在頁上。這才是「唯讀 join」的字面意思,且對任何前綴永久成立;台帳不可讀=誠實紅並印明。十檢 10/10(尾筆 `ENG078-v0101-406c(批406c)` 命中)。CI 以 `Tail "CGC_MDL096_SyncStatus_v*.py"` 取尾版,故 v0109 自動生效(尾版律)。
- **順帶更正我先前的誤判**:本會話早先我在沙盒看到同一道 ④ 紅,用 `git stash` 在乾淨的 `128695c1` 上復現後,判定為「沙盒既有、CI 會過、不動」。**復現是對的,歸因是錯的**——那不是環境差異,就是這個脆弱白名單;我自己一路追加台帳,最後把 CI 也拖紅了。
- **登錄**:台帳 894。再生頁 `VIA_UI_SyncStatus_v0100.html` 含 HEAD/dirty/列數等機器態,照往例不入 commit(CI 自己會再生)。

## 二十九、批407:掛網路工具及爬蟲——三道升級取用(http → headers → scrape)

操作員令「掛網路工具及爬蟲」。工作站實證:撤銷道生效(`PASS 0 · 撤銷 4`,車道冊已清乾淨),TWSE 路走完;群益投信那條是 `403 Forbidden`——伺服器拒絕、非找不到。

- **Zero-Hydra:三道全走既有件,本器只調度不改寫**。① `http`=`SUP_MDL740.http_json`/`http_text`(現行)② `headers`=`SUP_MDL740.curl_json` / `http_bytes`——**這兩支本來就收 `headers` 參數**,只是沒人帶瀏覽器式標頭;多數 403(UA 擋)於此即通,不必動用瀏覽器 ③ `scrape`=收容之爬蟲雙引擎包 `PlaywrightBackend`(真瀏覽器),順帶捕 XHR `network_json`——**投信 PCF 頁多為 XHR 載入,故 JSON 優先於 HTML**。
- **自動升級**:`probe`/`fetch_dated` 依車道 `fetch` 欄起跳、首個取到即用,並把**勝出道寫回車道冊**(下次自該道起跳,不必每次重試三道)。群益車道預設起跳道已改 `headers`(403 實證)。
- **法遵不打折**:`scrape` 前必過 `SUP_MDL740.check_url`(雙閘 + 包內 `def_validate_consent` 審查);verdict 非 `ALLOW` 即**不啟動爬蟲**,誠實印因由並提示閘二 `VIA_SCRAPE_CONSENT` 期望 token `I_ACCEPT_RESPONSIBLE_SCRAPING`。**永不代設任何同意閘。** 註:`via-etfhist` 目前設的是 `YES`,`gate_state()` 只看非空故閘二會開,但包內 `def_validate_consent` 可能因 token 不符而出 BLOCK finding → 屆時 `check_url` 會回 DENY 並印明,由操作員決定是否改設正確 token。
- **順修一個會擋死爬蟲道的真 bug**:爬蟲引擎 `import` 同包件(`VIA_Investment_Report_Classifier` 等),載入時**包夾必須在 `sys.path`**,否則 `ModuleNotFoundError`。沙盒自測原本回「引擎載入失敗」,修正後正確回「playwright 未安裝」(誠實區分「載不動」與「沒裝瀏覽器」)。
- **二十二檢 22/22**(+⑲ 三道升級序與瀏覽器標頭真傳入、⑳ 法遵 DENY 不啟動爬蟲、㉑ 走收容雙引擎且缺件誠實、㉒ 勝出道寫回車道冊),全注入式假 net、零外呼。
- **工作站要跑爬蟲道需先裝**:`uv pip install --python <via_vdf_312> playwright` 後 `playwright install chromium`。缺席=誠實回因由,不假裝。
- **登錄**:SelftestGrid v0245 站名;台帳 895。

## 三十、批408:爬蟲道可達性修——短令覆寫式設閘 × 閘二值非期望 token = 批407 掛上的爬蟲道其實是死路

批407 把 `scrape` 道掛上去之後,我回頭實查短令冊要寫給操作員的一貼指令,才發現這條道**根本開不了**。
兩層根因相乘,而且各自單看都不像 bug:

**① 短令是「覆寫式」設閘,不是「預設」。**
`Register-VIA-Commands` 裡六個短令——`via-fred`(批360)、`via-revfill`(批368)、`via-etfuniv`(批374)、
`via-etfhist`(批375)、`via-chip`/`via-price`(批394)——函式體第一句都是:

```powershell
$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES";
```

**每次呼叫都寫死**。所以操作員就算在自己視窗裡把閘二設成正確 token,只要打 `via-etfhist`,
第一句就把它蓋回 `"YES"`。這不是「不代設」的問題(那是另一條律),是**操作員連自己設都設不成**。

**② 閘二的兩個把關者,判準寬嚴不同。**
`SUP_MDL740.gate_state()` 的閘二只驗 `bool(g2)`(非空即算開);但 `check_url()` 會再走包內法遵
`VIA_WebScraping_Compliance_v0101.def_validate_consent`,那支是**逐字比對** SSOT 的
`required_consent_token`(`VIA_WebScraping_Compliance_SSOT.json` = `I_ACCEPT_RESPONSIBLE_SCRAPING`),
`"YES"` 一律回 `CONSENT_MISSING` / `BLOCK`。

於是實際跑出來的樣子是:`gate_state()` 說 `open=True`(看起來兩閘都開了),`check_url()` 卻回
`DENY(fail-closed:法遵 finding 阻擋)`。訊息**看不出差在哪**——這是最傷的部分,操作員只會覺得「掛了但沒用」。

### 修法(兩處,皆只增不減)

- **`Register-VIA-Commands-v0165.ps1`**:新 `Set-VIAGateDefaults`——
  `if (-not $env:VIA_NET_CONSENT) { … }` / `if (-not $env:VIA_SCRAPE_CONSENT) { … }`,
  **只在該閘未設時才補預設值,已設者一律尊重**。六處覆寫改呼它;六令函式名、參數、下游啟動方式零改,
  未設閘的情境下行為與前版**逐字相同**(=既有 `via-fred`/`via-chip`/… 不受影響)。
  另新 `via-gates` 唯讀閘態一覽 + 同名 `.cmd` 梭:只報「是否等於期望 token」,**絕不印原值、絕不代設**,
  並附上要自行開啟時該親打的那一行。
- **`VDF_ENG078_ActiveETFHoldingsHistory_v0103.py`**:新 `gate2_diagnosis()` 三態
  (未設(順帶告知期望值)/已設但非期望值(明說短令預設的 `YES` 過不了)/已是期望 token(阻擋另有其因)),
  接進 `scrape` 道 DENY 的回傳訊息裡。同樣**不外洩原值**。

### 驗

- `ENG078 v0103 --selftest` **二十三檢 23/23**(全注入式假 net、零外呼)。新增檢 ㉓ 以
  「臨時把 `VIA_SCRAPE_CONSENT` 設成 `YES` → 跑 `fetch_escalating` → 斷言訊息含『非期望值』與期望 token、
  且不含原值;跑完還原原環境」實證三態。
- `Register v0165` **十檢 10/10**(沙盒無 pwsh,以 Python 靜態驗)。其中兩檢刻意寫成**相對前版**:
  大括號差與奇數引號行數都取「與 v0164 相同」為準——因為這個檔本來就有字面量內的括號與引號,
  用絕對數當判準只會製造假紅(這是我在寫檢時先撞到、當場改掉的判準錯)。
  另一檢 ⑩ 以集合比對證明「前版函式全數仍在,本批只新增兩支」。

### 律(重申)

**永不代操作員設任何同意閘。** 本批做的是**移除覆寫**、把差別講白,讓操作員自己決定要不要開;
`Set-VIAGateDefaults` 保留六令原有的預設值只是為了不改既有行為,一旦操作員自己設了,它就不再插手。

## 三十一、批409:主動型台股 ETF 每日持股——從「沒有可呼叫的車道」到「一條實測驗真的 DATED 車道」

操作員令「你決定 請完成VRN VDF」。VDF 這邊唯一真正的缺口就是主動 ETF 每日持股:
批406 查出車道冊 16 條投信歷史道全空、批406b 修好 base、批406c 定論 TWSE openapi 沒有這份資料、
批407 掛上三道取用、批408 修好爬蟲道可達性——**但一直還是沒有任何一條真的能取到持股的歷史車道**。

本批把它補上了,而且不是猜的。

### 為什麼這次能查實

先前幾批我一直寫「沙盒連不到,交工作站驗真」。本批重測連線發現:**沙盒本批可連外**——
TWSE 仍被擋(回「FOR SECURITY REASONS」頁),但**投信站可達**。既然可達,端點就該由我查實,
不該再讓操作員拿猜的 URL 去試。

### 查法(逐步,可複現)

1. `https://www.capitalfund.com.tw/etf/product/detail/500/portfolio` 帶瀏覽器 UA → **200**
   (工作站先前 403 是因為走的是不帶標頭的 `http` 道——這正好反證批407 `headers` 道是對的方向),
   標題「00992A 群益台灣科技創新主動式ETF - **申購買回清單**」=PCF 就是這頁。
2. 頁是 Angular SPA,持股走 XHR。`main.*.js` 只給得到 API 路徑清單(`/api/etf/buyback` 等),
   給不到 body 形狀 → 取 `runtime.*.js` 列出 45 個 lazy chunk → 逐塊抓 `getBuyback` 呼叫點 →
   兩塊命中 → 讀出 `this.condition={fundId:"",date:null}`,body 形狀到手。
3. API base 不是站根:直打 `/api/etf/list` 是 **404**,`/CFWeb/api/etf/list` 回 **411 Length Required**
   ——那個 411 正是「端點存在、只是我沒帶 Content-Length」的證據(curl 帶 `--data-raw` 即自動帶上),
   補上就 200。

### 端點(實測)

```
POST https://www.capitalfund.com.tw/CFWeb/api/etf/buyback
body {"fundId": "<投信自家基金編號>", "date": "YYYY-MM-DD"}   # date=null 表示最新一日
→ data.pcf(fundName/date1/nav/…)、data.stocks(持股)、bonds/futures/assets/rps
```

基金編號**不是**股票代號,要先查對照:

```
POST https://www.capitalfund.com.tw/CFWeb/api/etf/list  body null
→ data.funds[].stockNo ↔ fundNo        # 00982A=399、00992A=500、00997A=502
```

實測三態:`date=null` → 39 列;`date=2026-09-01` → 40 列且 `pcf.date1` 隨之變成 2026-09-01;
`date=2026-08-15`(週六)→ `data=null`。**所以這是真的 DATED 車道**,不是只給今日。

### 做了什麼

- **`SUP_MDL740_NetUnified_v0113.py`**:加 `post_json` 車道(雙閘先行 → 法遵 → curl 子程序 →
  `{state,data}` 契約全同)。理由是 Zero-Hydra:這類端點是 POST,若讓呼端自己開 urllib,
  就繞過了雙閘與 `[VIA:NET-BRIDGE]` 稽核——網路出口必須只有一個。二十一檢 21/21。
- **`VDF_ENG078_ActiveETFHoldingsHistory_v0104.py`**:
  - 車道 schema 加 `method` / `body`(含 `{fundid}`/`{date}`/`{ymd}` 模板)/ `pick`(點路徑,
    如 `data.stocks`)/ `date_path` / `id_api`(代號→編號對照表規格)。
  - 新 `fetch_lane` **單一入口**:解編號 → 渲染 url/body → 三道取用 → `pick` → 解析 → 日期硬閘。
    `probe` 與 `backfill` 共用同一條路,判準不會有兩套。
  - **日期硬閘**:點名了哪一日,回來就必須是那一日;不符即拒寫。沒有這道閘,「今日持股被寫成
    過去某一日」會長得跟成功一模一樣——那比沒資料更糟。
  - `parse_holdings` 加 `by_id`:以本檔代號查出的基金編號去**點名**索取的單檔端點,相關性由建構
    方式保證(比字串比對強),故略過批406c 的第③道;**①列數上限與②反指標否決照跑,不放寬**。
    另補 `share` 欄名(群益用單數 `share`,先前只認 `shares` 會漏掉股數)。
  - `probe` 拿別家代號探到「該投信不發此檔」標 **N/A**——不算 PASS,也**不撤銷**。
    (沒有這條,拿 00981A 去探群益車道一次,就會把驗過的好車道誤降。)
  - 新動詞 **`sync [--apply]`**:把程式碼裡的車道種子**加法式**併進磁碟車道冊——新增缺的、
    補空的鍵、只升不降、**未驗過的 url 才汰換且舊值寫進 note**、冪等。
    為什麼要這樣:車道冊是執行期會被 `--apply` 改寫的檔,工作站那份早與倉內分岔;
    把新車道直接寫進倉內 JSON,操作員 `git pull` 就會撞本機修改。設定放程式碼、併入用這支。

### 驗

- ENG078 **二十六檢 26/26**、SUP_MDL740 **二十一檢 21/21**,皆全注入式假 net、零外呼。
- 另做**真實回應重放**端到端驗證(真取用是我自己以 curl 做的端點研究,重放證明解析鏈對真資料成立,
  **全程未動任何同意閘**):00992A × 2026-09-03 → **40 列**
  (3017 奇鋐 1,001,000 股 7.7434%、2059 川湖、2330 台積電 1,116,000 股 6.2205%…);
  把回傳日期改成別日,硬閘立刻擋下並印「日期不符:要 2026-09-03 回 2026-09-08」。
- 車道併入以**倉內真車道冊**實跑:17 條 → 17 條、舊 id 全在、群益升 VERIFIED、第二次跑零動作。

### 誠實的覆蓋話

23 檔須每日揭露的主動 ETF 裡,本批通的是**群益的 3 檔**(00982A / 00992A / 00997A)。
其餘 13 家投信仍是 `PENDING_SOURCE`。查法已經定型(頁→chunk→body 形狀→API base),
可以逐家照做;但那是逐家的工,不是一批做得完,也不該為了湊數而臆造端點。
