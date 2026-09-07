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
