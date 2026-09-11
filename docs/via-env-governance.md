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

## 三十二、批410:VRN 半邊——自測污染正式產出,收尾閘看到的是假報告

操作員令「你決定 請完成VRN VDF」。VDF 那半邊是批409。VRN 這半邊,我先把鏈**真的跑一遍**再說話。

### 先跑,再判

拿倉內既有的 `synthetic_financial_report.pdf` 走 `via-closeout vrn --run --dir <夾>`,五段鏈
(收件→首頁→入庫→財報頁→四點)**跑得完**——所以 VRN 不是「壞了」。但輸出裡冒出兩份我沒放進去的
報告:`fx_report` 與 `fx_twocol`,而且被判成 FAIL。

### 真因:只有一支引擎的自測會寫進正式產出夾

把 `VIA_Reports` 全樹與各庫做快照,逐一跑四支 VRN 引擎自測再比對差異:

| 引擎 | 自測後新建 | 改動 |
|---|---|---|
| `VRN_ENG072_FirstPageText_v0105` | **6** | 0 |
| `VRN_ENG073_ReportStructuredDB_v0105` | 0 | 0 |
| `VRN_ENG074_FinancialPages_v0102` | 0 | 0 |
| `VRN_ENG080_FourPointDigest_v0100` | 0 | 0 |

ENG072 的 selftest 把**輸入 PDF** 放進暫存夾了,但 `run()` 的**輸出**仍寫
`OUTDIR = VIA_Reports/first_page_text/`,於是每跑一次自測就留下
`fx_report.{txt,json}` / `fx_scan.txt` / `fx_twocol.{txt,json}` 六個 fixture 檔。

後果實測:再跑一次鏈,`ENG073` 把那些 fixture 當**真報告**收進正本庫(`basic +3`、`metrics +2`),
收尾閘於是把誠實的「尚無報告 YELLOW」變成假的「報告 3 · DONE 0 · FAIL 2 · RED」。
工作站只要跑過 `via-rungate --family vrn`、`via-selftest` 或 SelftestGrid 就會中——
這是 VRN 長期吵雜的一部分來源,而且是**假的紅**,比缺料更糟。

### 三處修

- **`VRN_ENG072_FirstPageText_v0106.py`(治本)**:自測期間把 `OUTDIR` 一併重導進暫存夾,跑完還原。
  新檢 ⑮ 只問「**本次**跑有沒有新增」——舊機器上前版留下的殘件不是本次的錯,那是清理道的工;
  拿舊殘件判本次紅,就是判準綁錯前提(批408 的教訓,這次先想到)。十五檢 15/15。
- **`purge-selftest [--apply]`(清舊)**:把已外流的 fixture 自正式產出夾**搬進隔離夾**
  (`_selftest_quarantine/`)——**不刪、可逆、資訊不丟**;並查出正本庫對應列、印出該下的 `DELETE` SQL,
  **庫側絕不代刪**,由操作員自己決定。
  (第一版我對著 `functional modules/VRN/**` glob 找庫,一列都查不到;VRN 的報告表其實住在 VDF 正本庫
  `vdf_tw_market.duckdb`=`ENG073`/`MDL141` 的 `DB_TW`——查核路徑要跟真正寫入者一致。)
- **`CGC_MDL141_ClosingGate_v0102.py`(閘上認得)**:收尾閘認出 fixture 外流件,**不進 rows 與判定**,
  單列 `FIXTURE` 說明並指路清理。這樣即使操作員還沒清庫,判定也已經是誠實的。
  新檢 ⑩ 以對照組實證「有無外流件,報告數與 verdict 皆相同」(乾淨 1 份 RED = 有外流 1 份 RED,外流 2)。十檢 10/10。
  寫這檢時撞到自己一個錯:DuckDB 單寫者,乾淨組讀之前沒先關連線,讀到空 → 判準假紅;先關再讀即正確。

### VRN 的誠實話

鏈本身五段可跑,卡的是**沒有真報告輸入**——`via-closeout vrn` 在乾淨態說「尚無報告(報告夾與庫皆空)
→ 拖 PDF/選夾進主控台即整條鏈」,那句話是對的。倉內的 `synthetic_financial_report.pdf` 不是台股
投資報告(抽不出代號與目標價,`ENG080` 誠實回「`vrn_report_basic` 無有效 ticker 列」),
所以它不能充當四點文摘的示範件。要讓 VRN 走到 GREEN,需要的是真報告,不是再寫程式。

## 三十三、批411:工作站實錄修——`backfill` 回 `tried 0` 不是沒事做,是我讓它做不到

工作站實錄:`verified_dated_lanes: 1`(群益車道確實已驗真)、checkpoint 46 個日格,
`backfill --max-days 10` 卻回 `tried 0 · filled 0 · no_source 0`。

**真因**:`coverage()` 用 `st.setdefault(d, {"state": "MISSING"})` ——**既有日格保留舊態**;
而 `backfill` 只走 `state == "MISSING"` 的日格。批406 那時一條車道都沒有,所有日格早就被寫成
`NO_SOURCE` / `PENDING_TODAY`;於是批409 把車道驗真之後,**那些日格永遠不會再被看一眼**。

`NO_SOURCE` 本來就該是「**當時**沒有源」的紀錄,不是終局判決。是我把它當成終局了。

**重試律**(`VDF_ENG078_v0105`):

| 日格態 | 重試? | 理由 |
|---|---|---|
| `MISSING` | 一律試 | 原本就是待補 |
| `NO_SOURCE` | 該發行商**現在有** VERIFIED DATED 車道才試 | 沒車道時重試是做白工 |
| `PENDING_TODAY` | 那一日**已不是今日**才試 | 當日快照歸 ENG051,過了就該補 |
| `FILLED` | 永不重跑 | 只增不減,已落庫的不動 |

回傳加 `revived` 計數,看得見復活了幾格。另外 `sync` 零動作時逐條印出「不動的原因」——
先前只印「新增 0 · 補鍵 0 · 升態 0」,分不出「早就併好了」與「被狀態擋住」。

**驗**:二十七檢 27/27。新檢 ㉗ 用對照組實證兩個方向:無 DATED 車道時 `NO_SOURCE` 不復活
(revived 1 = 只有過期的 `PENDING_TODAY`),車道驗真後同一批日格復活並真的補起來
(revived 6 · tried 3 · filled 3)。寫這檢時自撞一次:fixture 拿 `wd8[-1]` 當「過期的今日」,
但平日它就等於今日=永遠不復活——判準是對的、fixture 是錯的,改以 `date.today()` 明確切開。

## 三十四、批412:金融機構 SSOT 收容與接線——券商/評等正典化 + 報告分析師姓名擷取

操作員上傳 `VIA_Financial_Institution_SSOT_v0100.{py,json}` 並令
「SSOT補充報告分析師姓名擷取 BROKER / RATING DICTS」。

### 先講缺口(v0105 為止的實況)

- `VRN_ENG073.BROKER_DICT` 只有 **16 條寫死鍵**,而且鍵是**檔名子字串**(`MS`/`Citi`/`凱基`…),
  不是正典鍵;國內 16 家 + 外資 12 家的中英別名、舊鍵遷移(`BOA`→`BOFA`、`MCQ`/`MQ`→`MACQUARIE`)全無。
- `rating_raw` 只存正則抓到的**原字串**,從不正規化——`Outperform` 與 `買進` 在庫裡是兩筆不同的東西。
- **分析師姓名完全沒有抽取**。整條 VRN 鏈(ENG072/073/074/080)沒有任何一處在做這件事。

### 收容與接線

- 收容:`supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.{py,json}`(逐位元原樣)。
  其自測 PASS:國內 16 · 外資 12 · 評等 6 · regex 8 · 網域 16 · 24 斷言。
- `VRN_ENG073_ReportStructuredDB_v0106.py` **綁**它(Zero-Hydra:只調度不改寫,
  本器不自建第二份券商或評等字典):
  - `ssot_broker` 檔名優先→內文後備,舊 16 鍵經 `resolve_broker` 轉正典鍵。
  - `ssot_rating` 英中同義歸一(`Buy`/`Outperform`/`Overweight`/`優於大盤` → `BUY` code2 POSITIVE;
    `NR` → `NOT_RATED` code0 不可行動)。
  - `ssot_analysts` = **全新能力**,以 SSOT 的 `analyze_contact_document` 為引擎
    (Email／電話當錨點 → 鄰近行姓名候選 → local part 相似度比對 → 網域反查機構),落新表 `vrn_report_analyst`。
- **只增不減**:`broker` 與 `rating_raw` 兩欄的語意與值**完全不動**(下游 MDL141/ENG080 仍讀得到原樣),
  新事實一律走新欄新表。順帶必須一起改的:原本 `INSERT ... VALUES (?×18)` 是位置式,
  一旦 `ALTER` 加欄就整批爆掉——**加欄與位置式 INSERT 天生互斥**,改成具名欄位。

### 誠實面

SSOT 給的是四個**語意不同**的欄:`matched_*`(與本錨點比對到的)與 `*_guess`
(自 email local part 還原、或英轉中音譯)。我第一版把它們併成一欄,那是把「驗到的」和「猜的」
混為一談,已改成分欄並記來源(`EMAIL_LOCALPART_GUESS` / `NEARBY_MATCHED` / `TRANSLITERATION_GUESS`)。
另外實測發現 SSOT 會把**同一個中文名同時配給兩位分析師**(鄰近視窗誤配的典型徵狀)——
那是正典的判斷、正典依其 `alias_governance` 為唯讀,我不改它;但我在本器加 `zh_shared` 標記,
讓它不會看起來像確定的事實。

**修掉自己兩個問題**:① 動態載入沒把模組放進 `sys.modules`,pydantic 解不了延後註解,
`analyze_contact_document` 丟「`TextBlock` is not fully defined」——而且**只在動態載入時發生**,
直接 `python SSOT.py` 跑自測不會重現。② 我的 `except` 把它吞成「0 筆」——靜默回空看起來像
「這份報告沒有分析師」,那是假訊息;改為記下因由並在 `[入庫計]` 印出來。

### 回報 SSOT 缺口(canonical 唯讀,我未觸碰;要不要補是操作員的決定)

| 舊鍵/詞 | 意義 | SSOT 現況 |
|---|---|---|
| `JP` | 摩根大通 | 只有 `JPM` / 小摩 / 摩通 / `J.P. Morgan`,沒有裸 `JP` |
| `CLST` | 里昂 | 只有 `CLSA` / 里昂 / `CLSA Securities` |
| `GF` | 廣發 | **SSOT 完全沒有廣發這家券商** |
| `增持` | 買進同義 | `BUY` 的別名有「加碼」沒有「增持」(而「減持」在 `SELL` 裡有) |

這四項**不會遺失資料**——舊欄 `broker`/`rating_raw` 仍存原值,新欄誠實留空。

### 驗

ENG073 v0106 **二十三檢 23/23**(原二十檢全過 + 批412 三檢);SelftestGrid v0249 兩站實跑綠;
ENG078 v0105 二十七檢 27/27;CGC_MDL096 v0109 十檢 10/10。
分析師擷取端到端實測:兩位分析師、英文名自 email local part 還原、電話正規化、
網域反查出「摩根士丹利」與「凱基證券」並帶正典鍵 `MS`/`KGI`、`zh_shared` 正確標出中文名共用。

## 三十五、批413:先去 Grok 倉找解方——找到了,而且四項裁決一字不差

操作員令:「查一下 GROK 在 GITHUB 的文件夾有無解方 昨天有過關 / 去摩通 / CLST·CLSA·里昂都可 /
大陸券商刪除 / 增持加碼」。

### 先查,查到了

`tonykuni/cherry-lagoon-honey-dove` 的 `src/lib/via/vrn-broker-cache.ts` 第一行就寫著:

> `/** Broker dict 29 + extended 28（無陸券）。GS=高盛；MS/大摩；JPM/小摩；刪「摩根」。 */`

而且有一份 `VRN_DROP_KEYS` **明列陸券**:中信證券／中信建投／CITIC／國泰君安／Guotai Junan／
中金／CICC／海通／Haitong／**廣發／GF／GF Securities**,外加「摩根」。
`vrn-rating-cache.ts` 則有 **102 條**評等別名(BUY 31／HOLD 26／SELL 25／NOT_RATED 20),
**「增持」與「加碼」本來就同列 BUY**;JPM 的別名是
`["摩根大通","JPM","JPMorgan Chase","JPMorgan","JP Morgan","JP摩根","小摩"]`——**本來就沒有「摩通」**。

四項裁決與那份冊子完全一致。所以這批不是我在決定什麼,是把你昨天過關的決定接回來。

### 與上傳正典的落差

| 面向 | Grok 冊 | 上傳的正典 SSOT v0100 | 落差 |
|---|---|---|---|
| 券商 | 29 家(+ext 28) | 28 家 | 24 家對得上;**5 家正典沒有**(日盛/合庫/大華/宏遠/德意志) |
| 評等別名 | 102 條 | ~50 條 | **59 條正典查不到**(增持/推薦/超配/續抱/觀望評等/低配/Long/Short…) |
| 陸券處置 | 有 19 條拒絕清單 | 無此概念 | 正典只是「沒收錄」,不是「明確拒絕」 |

### 做法:不改正典,立疊加層

正典 `alias_governance` 自己寫明 `canonical_write_mode = READ_ONLY`、自動更新一律進
`RUN_LOCAL_OVERLAY`。所以我**一個字都沒改正典**,改立
`supportive modules/ssot/VIA_FinancialInstitution_Overlay_v0100.{json,py}`,只做四件事:

1. **拒絕清單(20 條)** —— **先於**正典查詢。`摩通`／`廣發`／`GF`／`中信建投`／`國泰君安`／`中金`／
   `海通`／`摩根` 一律不得解析成任何機構,而且**回報「為什麼被拒」**,不是靜默查無。
   「拒絕」與「查無」是兩種態,不能混。
2. **券商別名補充**:23 條 / 14 家(自 Grok 冊,排除拒絕詞)。
3. **新增機構**:5 家(日盛 JS / 合庫 TCB / 大華 DH / 宏遠 HY / 德意志 DB)。
4. **檔名鍵對映(16 條)**:`JP`→`JPM`、`CLST`→`CLSA`、`GF`→`__DENY__`。
   關鍵設計:**兩三字母 token 只在「檔名命名空間」認得,內文別名絕不收裸 `JP`**——
   在報告內文裡 `JP` 會亂咬。這是兩個不同的命名空間,分開處理才安全。
   (`CLST` 依你的「都可」同時收為內文別名,它夠長不會誤咬。)

評等疊加把那 59 條接到正典的六個鍵上。解析次序一律 **拒絕清單 → 正典 → 疊加層**;
正典先行,疊加層**只補空缺、永不覆寫**正典既有的判斷。

`VRN_ENG073 v0107` 改綁疊加層(分析師擷取引擎仍在正典那一層,轉呼)。

### 驗

疊加層**九檢 9/9**、ENG073 **二十三檢 23/23**、SelftestGrid v0250 兩站實跑綠。
四項裁決端到端實測:

```
JP_2330_…    → JPM  摩根大通    (FILENAME_MAP)
CLST_2317_…  → CLSA 里昂證券    (FILENAME_MAP)
GF_2454_…    → (空) DENY:拒絕清單:GF(操作員裁決)
增持/加碼/超配 → BUY code2 ·  續抱 → HOLD ·  低配/Short → SELL ·  摩通 → (空)
```

舊 `BROKER_DICT` 16 鍵覆蓋率 **13/16 → 15/16**(`GF` 是**刻意拒絕**不是漏掉)。

## 三十六、批414:母倉現況導入 VIA Central Governance Console 面板

操作員令「所有狀況都到導入 GROK VIA CENTRAL GOVERNANCE CONSOLE 面板顯示」。

**先查再做**:那個面板本來就在——`cherry-lagoon-honey-dove` 的 `console-deck.tsx`
標題就是「VIA Central Governance Console · 中央唯一入口」。所以不另開分頁,接進那一頁。

新增 `src/lib/via/mother-status.ts`(照該 app 既有慣例:lib=純資料/邏輯 +
`import type { Light }` + 一支 `node:test`),母倉 PR #30 批407–413 的**唯讀鏡面** 10 列:

| 燈 | 批 | 項目 | 量 |
|---|---|---|---|
| ok | 批409 | 群益 PCF 車道驗真 | 26/26 檢 · 00992A×09-03 → 40 列 |
| **warn** | 批409 | ETF 覆蓋誠實話 | **3 / 23 檔有源** |
| ok | 批411 | 回補重試律 | 工作站 revived 23 · filled 1 |
| ok | 批407 | 三道升級取用 | 22/22 |
| ok | 批408 | 同意閘不覆蓋律 | 六令改為只在未設時補 |
| ok | 批410 | VRN 自測污染修 | 15/15 + 10/10 |
| ok | 批412 | 券商/評等正典化 | 舊鍵覆蓋 15/16 |
| ok | 批412 | 分析師姓名擷取 | 落表 `vrn_report_analyst` |
| ok | 批413 | 操作員裁決疊加層 | 拒絕 20 · 別名 +82 · 機構 +5 |
| **pending** | 批410 | VRN 走到 GREEN 還缺什麼 | **尚無真報告** |

**不跑、不抓、不連線**——數字全部來自母倉實跑與工作站實錄,在面板上只是被顯示。

總燈**不取巧**:有 bad 即 bad,有 warn/pending 即 warn,全 ok 才 ok。
現況是 **warn**(ETF 覆蓋 3/23、VRN 尚無真報告兩件未了結)。
而且面板把**未了結的先列**——不讓好消息壓過待辦。

`console-deck.tsx` 加一段(Pillar 之後、實測矩陣之前),用既有的
`Matrix`/`StatusLight`/`Badge`/`tri`,附「母倉詳情」鍵跳既有 `05 母倉` 分頁。
既有區段與所有既有模組零觸碰。

**驗**:`node --experimental-strip-types --test src/lib/via/*.test.ts` → **227 pass / 0 fail**
(原 224 + 本批 3);`tsc --noEmit` 本批兩檔零錯誤。
已推 `claude/via-mother-deck-b405`(`f2ef6ff`);**未開 PR、未併 main**(未獲該項指令)。
母倉可追溯副本留於 `references/intake/VIA_GrokConsole_CherryLagoon_b404/ui_integration_b414/`。

## 三十七、批415:`--max-days 30` 只 tried 1——不是重試律壞了,是要補的日子根本沒被算進來

工作站實錄:

```
checkpoint 日格 46 · {'NO_SOURCE': 22, 'PENDING_TODAY': 23, 'FILLED': 1}
[回補] tried 1 · filled 0 · no_source 1 · revived 1 · verified_dated_lanes 1
```

46 個日格 ÷ 23 檔 = **每檔只有 2 天**。`--max-days` 給再大也沒用,因為**覆蓋窗本身只有兩天**。

### 真因在 `resolve_listing`

三道解上市日:① registry 冊上市日欄——**未來欄位,現在是空的** ② `yfinance` 首根 K 線——
主動 ETF 幾乎都是新掛牌,**常常查無**(工作站實錄 `00998A.TW → 404 possibly delisted`)
③ 於是全部退到「首個快照=下界」,而首個快照往往**就是前天**。

歷史其實一直都在:實測 `00992A × 2026-02-02` → **52 檔持股**。是我沒把它算進覆蓋窗。

### 修:L1b 發行商自家上市日車道

車道 schema 加 `listing_api`,排在 `yfinance` **之前**(發行商自己的資料比第三方對新掛牌檔可靠):

```json
"listing_api": {"url": ".../CFWeb/api/etf/detail/{fundid}",
                "method": "GET", "pick": "data.listingDate",
                "fallback_pick": "data.establishmentTime"}
```

群益實測 `detail/{fundNo}`:

| fundNo | 代號 | 成立 | **上市** |
|---|---|---|---|
| 399 | 00982A | 2025-05-13 | **2025-05-22** |
| 500 | 00992A | 2025-12-16 | **2025-12-30** |
| 502 | 00997A | 2026-03-30 | **2026-04-14** |

00992A 從 2025-12-30 到今天約 170 個交易日——先前只算到 2 天。

### 誠實界限

- 取到的日期**早於主動 ETF 元年**(`ACTIVE_ETF_ERA`)即**不採信**(那必是解析錯了)。
- 沒有 `listing_api` 的投信**誠實回空**,不猜。
- `listingDate` 缺欄才退 `establishmentTime`(成立日 ≠ 上市日,所以是後備不是首選)。

### 驗

**二十八檢 28/28**。新檢 ㉘ 以注入式假 net 實證四件:L1b 優先於 `yfinance`(假 net 的
`yf_history` 一律回空,重現新掛牌檔實況)、缺欄退 fallback、早於元年不採信、無 `listing_api` 誠實空。
另以**真實抓回的群益 `detail` 回應重放**驗三檔上市日全中——**全程未動任何同意閘**。

## 三十八、批416:批415 推上去了,卻在工作站靜默失效——`sync` 的硬寫鍵白名單

### 工作站回報的事實

`git pull` 拿到 批415 之後:

```
via-etfhist sync --apply
[車道併入] 新增 0 · 補鍵 0 · 升態 0 · 已寫回
  [不動] ISSUER_ARCHIVE:群益投信    已是 VERIFIED(設定齊全,無須併入)

via-etfhist checkpoint
  00400A 上市 2026-09-07(LOWER_BOUND(first_seen)· 快照 0/2(0.0%)
[回補] {'tried': 1, 'filled': 0, 'revived': 1, 'verified_dated_lanes': 1}
```

日格還是 46、上市日還是 `LOWER_BOUND`、`tried` 還是 1。**批415 的程式碼是對的,但它從來沒到過磁碟。**

### 根因

`sync_lanes()` 補鍵時用的是一份**硬寫的鍵白名單**:

```python
keys = [k for k in ("method", "body", "pick", "date_path", "id_api", "fetch", "kind")
        if k in seed and not cur.get(k)]
```

批415 幫車道種子加了 `listing_api`,白名單沒跟著改 → `listing_api` 永遠不會被併進磁碟車道冊
→ `lane_listing_date()` 找不到 `listing_api` → 誠實回空 → `resolve_listing` 照舊退到 L3
「首快照即下界」。整條鏈每一段都按設計行事,合起來就是靜默失效。

而且訊息還幫倒忙:零動作時印的「已是 VERIFIED(**設定齊全**,無須併入)」是**沒有真的比對過**
就下的斷言——缺著 `listing_api` 也照樣說齊全。訊息比缺陷本身更難查。

### 修(`VDF_ENG078_ActiveETFHoldingsHistory_v0107.py`)

白名單這種抽象**每加一個欄位就要記得改一次,漏一次就靜默失效**。換成自種子逐鍵推導,
只排除執行期會被寫回的欄:

```python
SYNC_RUNTIME_KEYS = ("id", "state", "note", "url", "id_map")
keys = sorted(k for k in seed if k not in SYNC_RUNTIME_KEYS and not cur.get(k))
```

- `id` 是鍵;`state`/`note` 由探測與升降態維護;`url` 另有汰換規則(批409);
  `id_map` 是 `probe` 查出的代號↔基金編號對照。其餘欄一律「缺了就補」,以後加欄零維護。
- 零動作訊息改成**逐鍵比對後**才敢講:全在才說「種子鍵全在」,缺了就點名缺哪幾個。

### 驗

**二十九檢 29/29**。新檢 ㉙ 的 fixture 就照工作站當時那份:群益已是 `VERIFIED`、
該有的鍵都有、唯獨缺 `listing_api`;另加一個 `operator_field` 與 `id_map` 驗證補鍵
不得動 `state`/`url`/`note`/`id_map`、不得刪操作員自加的欄,且第二次跑零動作。

**對照組實證**(這檢不是空檢):同一份 fixture 餵給修前的 v0106 → `filled=[]`、
`listing_api` 從不落地;餵給 v0107 → `filled=['ISSUER_ARCHIVE:群益投信:listing_api']`、落地。

### 順帶查實的兩件事(逐家投信仍是逐家的工)

- 群益 `/CFWeb/api/etf/list` 現有 **28 檔**,主動型就是 `00982A`/`00992A`/`00997A` **三檔**
  ——現有 3 條車道**已是群益全部**,不是漏抓。要往上加只能加別家投信。
- 元大:PCF 頁是 `https://www.yuantaetfs.com/tradeInfo/pcf/{code}`(Nuxt SSR),
  API 形狀為 `POST {base}/api/trans`,body `{APIType, CompanyName:"YUANTAFUNDS", PageName,
  DeviceId, FuncId, …}`;但 PCF 的 `FuncId` 在尚未取得的 chunk 內,**且還沒看到日期參數的證據**,
  所以**不寫任何車道**——沒查實就不寫,是 批406c 立下的規矩。
- 沙盒限制(誠實記下):Chromium 走中繼 proxy 連任何外部主機一律 `ERR_CONNECTION_RESET`
  (`--disable-http2`/`--disable-quic` 都試過),所以**無法用 XHR 攔截**逐家挖端點;
  curl 可通,但那就要逐家讀 SPA chunk。剩下 13 家需另批逐家做。

## 三十九、批416 F3:六流程全景治理令——先盤點,再說「已在位」還是「要新造」

操作員下了一份完整的 Mega-Prompt(20 加速器 / 三輪全景式分析 / 六獨立同步流程 /
零九頭龍 / RYG HTML UI Matrix)。**照 Zero-Hydra 先查再做**:這份清單裡絕大多數
不是要新造的東西,是這幾十批已經蓋好的件。硬照字面再蓋一套,就正好是它自己
要防的九頭龍。

### 20 加速器 → 現役對應件(全部實查在檔)

| # | 加速器 | 現役件 |
|---|---|---|
| 01 | AST 精準解析 | `VIA_PS_Accel_Module.ps1` #01 + `CGC_MDL101_PSAstRepair_v0100.py` |
| 02 | 多語言語意 | `VIA_PS_Accel_Module.ps1` #02 |
| 03 | 九頭龍風險預測 | `CGC_MDL135_EnvGovernance` 拓撲三輪 |
| 04 | 依賴拓撲排序 | 同上(無環最佳修正序) |
| 05 | 沙盒隔離執行 | `via-rungate`(`CGC_MDL137_RunGate`)家族境逐庫 import |
| 06 | 自動修正建議 | `Invoke-VIA-PSRepair-v0102.ps1` R2b |
| 07 | 三輪全景式分析 | `via-psrepair` R1 / R2 / R3 |
| 08 | SSOT 對齊 | `CGC_MDL096_SyncStatus_v0109` + `VIA_MasterGovernance_SSOT` |
| 09 | 視覺化矩陣生成 | `CGC_MDL064_SelftestGrid`(RYG)+ MDL135 四分區 + MDL139 + MDL140 |
| 10 | 錯誤分類分群 | PSRepair `parallel-fixable` / `sequence-dependent` |
| 11 | 性能與複雜度 | `CGC_MDL133` 引擎簡化稽核 + ENG081 SQL 側計數(批400) |
| 12 | 多子系統同步檢視 | `CGC_MDL140_HandoverConsole` 15 類堆疊矩陣 |
| 13 | 版本差異與回滾 | MDL135 LKGC 快照/晉升/rollback;PSRepair 讓位備份 + UNDO manifest |
| 14 | 覆蓋率與回歸 | `via-selftest`(SelftestGrid 193 站) |
| 15 | 修正順序最佳化 | MDL135 拓撲序 |
| 16 | 動態進度條 | `Write-VIAProgress` / ENG056 `PROGRESS.json` |
| 17 | 動態說明 | 各引擎逐條印因由(批411 起連「不動的原因」都印) |
| 18 | 非阻塞 PowerShell | `Invoke-VIAWatched`(批404 洗版修) |
| 19 | 多引擎整合 | `via-entry` 唯一入口 + `CGC_MDL136_EntryBridge` |
| 20 | 自動部署與初始化 | `via-rebuild` + `via-envgov` |

### 六獨立流程 → 現役短令

1. 代碼層與 AST 重構 → `via-psrepair`
2. SSOT 資料與配置對齊 → `via-ssot` + MDL096
3. 子系統依賴解耦(VRN/VDF/VAP)→ `via-rungate` + `via-envgov`
4. 性能瓶頸與死碼清理 → `via-deadends` + `via-bridge-sweep --net-callers`
5. 沙盒回歸驗證 → `via-selftest`
6. UI Matrix 渲染與非阻塞部署 → `via-famui` / `via-console`

### 本批沙盒實跑(能跑的那一半)

`CGC_MDL064_SelftestGrid_v0252 --fast` 全跑:**OK 158 · FAIL 32 · SKIP 3**(存證
`GRID_20260908_125812.json`)。前次同類全跑是 `OK 135 / FAIL 50 / SKIP 6`。

**32 紅逐條看過,沒有一條是新缺陷**:多數是沙盒沒有工作站的正本庫
(`tw_listings` / `tw_daily_prices` / `features_daily` / `global_daily` 查無此表)
與缺 `pyarrow`,其餘是頁面站在沙盒缺再生前提。這是**誠實三態**該有的樣子——
沙盒沒有的東西就報沒有,不假綠。

### 誠實界限:另一半只能在工作站跑

`via-psrepair` 的入口是 ps1,**沙盒無 pwsh**,所以 R1/R2/R3 三輪、20 個 PS 加速器、
`-Fix` 都必須在工作站跑。`-Fix` 的可逆性已查實:Accel20 走 `.psrepair.bak` 讓位、
MDL101 走 `VIA_Reports/ps_repair/backup_<ts>/` 整檔讓位 + manifest + UNDO,
且 **sequence-dependent 只列不修**——所以它是保守且可回滾的,但仍是會改檔的動作,
由操作員自己在工作站按下。

## 四十、批417:整合台——一頁輸入、一頁結果,VDF → ETF → VRN 跑成一輪

操作員令「用 GROK 的介面將 VRN VDF ETF 跑成功,有整合後的**輸入介面**、**結果介面**」。

### 缺口不是引擎,是動線

Grok app 六個分頁裡三族其實都跑得動,但**輸入散在三處**(VDF 的起始年與金鑰在
`01`、ETF 的挑檔在 `01` 內層、VRN 的檔案拖放在 `02`),**結果也散在各自分頁的四個
tab**。要「跑一輪看結果」得走三個地方——這就是「接近成功」跟「跑成功」的差距。

### 做法(Zero-Hydra:引擎一支都不新造)

- `src/lib/via/run-console.ts` — 純邏輯層 + `node:test` **七檢**:
  - `readiness()` 跑之前先講清楚每族能不能跑、不能跑差什麼(**VRN 沒檔案就是不能跑**)。
  - `resultRows()` 把三族跑完的實際數字收成同一張表。
  - 誠實三態鐵律:沒有輸入=`pending` **絕不當 ok**;跑完零列=`warn`(「跑完了但什麼
    都沒有」跟「成功」是兩件事);`busy` 期間一律 `run`,**不讓上一輪的數字冒充本輪**;
    總燈取最壞 `bad > run > warn > pending > ok`。
- `src/components/run-deck.tsx` — 左輸入 / 右結果一頁:
  - 左:共用(起始年、FRED KEY、網閘勾選——**本頁不替任何人開同意閘**)、主動 ETF 挑檔、
    VRN 拖放+選擇檔案+去重開關、整備矩陣、一鍵「整合跑」(VRN 無檔時按鈕自己改口說會跳過)。
  - 右:三族整合矩陣 + 三族分燈 + 擷取車道 + 主動 ETF 檢核 + VRN 報告,附跳既有分頁的鍵。
- `shell.tsx` 只加 NAV 一列與一個分支;`types.ts` 的 `Deck` 加 `"run"`。既有六分頁零觸碰。

### 真跑驗證(headless Chromium 實際操作,不是靜態檢查)

按下「整合跑」之後:

| 族 | 指標 | 值 | 燈 |
|---|---|---|---|
| VDF | 巨觀序列 | 98 列 | 綠 |
| VDF | 擷取車道 | 4/14 有料 | 綠 |
| ETF | 主動 ETF 檢核列 | 7 列 | 綠 |
| VRN | 報告基本資料 | 71/73 件 | 綠 |
| VRN | 一題四點文摘 | 288 列 | 綠 |
| VRN | 財報頁表格 | 27 列 | 綠 |
| VRN | **卡住的件** | **1 件** | **紅** |

**總燈是紅不是綠,而這是對的**:六項有料、一件卡住,就不准說成功;卡點在 `03 VRN`
分頁逐件列得出來。若把它算成綠,就正好是這整套治理在防的那件事。

驗:`node --test src/lib/via/*.test.ts` → **237 pass / 0 fail**(原 230 + 本批 7);
`tsc --noEmit` 零錯誤;`vite dev` 實跑並截圖存證。已推 `claude/via-mother-deck-b405`
(`76ef17f`);母倉可追溯副本在 `references/intake/VIA_GrokConsole_CherryLagoon_b404/ui_integration_b417/`。

### 順帶取得母倉一直缺的東西:主動 ETF 全名冊 × 發行商

Grok app 的 `src/lib/via/active-etf.ts` 帶有 **29 檔**主動 ETF 的 `ticker → issuer`
對照(`AETF_UNIVERSE` + `AETF_MISSING_CODES = ["00409A","00998A"]`),與工作站
`checkpoint` 看到的 `00400A`–`00406A` 系列相互印證:

國泰 1 · 摩根 2 · 安聯 3 · 統一 3 · 聯博 1 · 富邦 1 · 中信 3 · 凱基 1 · 第一金 2 ·
永豐 1 · 野村 3 · **群益 3** · 台新 2 · 元大 1 · 復華 1 · 兆豐 1。

這正是母倉逐家補車道要的名冊——**群益那 3 檔已通**,剩下 13 家 26 檔有了明確標的與
優先序(檔數多的先做:安聯/統一/中信/野村 各 3 檔)。**但名冊不等於端點**,
端點仍要逐家查實才寫(批406c 的規矩不因為有了名冊而放寬)。

### 順帶查實:操作員上傳的 VETF 封存包已在倉內

`VETF_FINAL_SEAL_20260829_013330.zip` 的 `MANIFEST.json` / `SHA256SUMS.txt` /
`README_FINAL_SEAL.md` 與倉內 `functional modules/VDF/references/intake/VETF_FINAL_SEAL_b242/`
**逐位元相同**——已於 b242 收容,**不重複收**(Zero-Hydra)。

## 四十一、批418:63 份真報告當 INPUT FOR TEST——查出兩個會毀掉整批的問題

操作員把工作站上 63 份**真研究報告**的路徑交出來當測試輸入
(`…\VeritasIntelligenceAnalytics - 複製\functional modules\VRN\input\incoming\`)。
**先把 63 個檔名逐一餵給現役擷取器**再說要不要動手——查出兩件事,兩件都會在真跑時
把整批毀掉。

### 一、年份被當成股票代號(假資料入正本庫)

`第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂.pdf` 被抽出代號 **2026**。
那是**年份**。而且擋不住——`extract_one` 本來就會「逐驗官方名冊」,但
**2026 恰好是真實上市代號(聚亨)**,名冊逐驗照樣放行。三份研討會簡報全中。

把產業展望簡報歸到聚亨名下,比沒有代號更糟:**假資料比缺資料難查**。

修(`VRN_ENG073_ReportStructuredDB_v0108.py` 的 `_is_year_like`),三道由結構到語意:

1. 候選落在本檔名的日期字串裡 → 那是日期的一部分(結構事實,永遠對)
2. 候選後面緊接 `年`/`年度`/`H1`/`Q3`… → 語言事實,永遠對
3. 值在 1990–2099、檔名帶 展望/趨勢/前瞻/年度 這類詞、且候選旁沒有代號記號
   (括號/`TT`/代號)→ 這是**判斷**不是事實,所以條件收得很緊

第 ③ 道擋錯的代價是「誠實無代號」,擋不住的代價是「假代號入正本庫」——不對稱,
所以寧可擋。被擋下的候選寫進 `conflicts` 的 `YEAR_NOT_TICKER=…`,留痕可查。

### 二、19 份非個股報告會變成一整面假紅

63 份裡有 **19 份本來就不是個股報告**:

| 型別 | 份數 | 例 |
|---|---|---|
| 個股 | 41 | `凱基投顧_3665 貿聯-KY_李承泰_20260519` |
| 產業 | 9 | `MS-Thermal Solutions` / `MS-ABF` / `Daiwa-PCB` / `凱基投顧_鋼鐵產業` |
| 大盤晨報 | 6 | `20251205兆豐晨會報告(一)` / `投資早報251209` / `台新台股盤勢分析` |
| 海外 | 4 | `凱基日股分析` / `凱基美股分析` / `UBS-Asia Hardware Insights` |
| 研討會 | 3 | `第一場 2026年投資大趨勢 - 華南投顧` |

它們沒有代號、沒有目標價、沒有 EPS——**這是對的**,不是缺陷。但
`CGC_MDL139.classify_report` 在「零 metrics 且零 financial」時直接判
`financial=FAIL`,於是這 19 份會被算成 **FAIL**:操作員一跑就看到一整面**假紅**,
而假紅跟假綠一樣糟。

修(`VRN_ENG073 v0108` + `CGC_MDL141_ClosingGate_v0103.py`):

- ENG073 新增 `classify_kind()` → `report_kind` / `kind_reason` 兩個新欄(ALTER 加欄,
  舊欄零觸碰)。**有代號一律先算個股**(代號是最硬的證據);沒代號才按關鍵詞分,
  全不中=「其他」誠實留白,**不硬塞個股**。
- MDL141 讀 `report_kind`:非個股型只要**首頁抽出來了、也進了庫**,對它適用的鏈就
  走完了 → `DONE_NS`(非個股完成),自成一格統計、不混進「全通且 VERIFIED」充數。
  **收得很緊**:真的核對不符(`DB_NO_MATCH`、上漲空間落在 FAIL 態)照舊是 FAIL,
  不因為型別就放過。舊庫沒有這一欄=**行為逐字不變**(只增不減)。

### 驗

- ENG073 **二十六檢 26/26**;新檢 ㉔㉕㉖ 的 fixture **全部取自操作員這 63 份真檔名**,
  並把 `2026:聚亨` 放進名冊以重現「名冊逐驗擋不住」的真實情況。
- MDL141 **十一檢 11/11**;新檢 ⑪ 是**對照組**:同一份 fixture,沒有型別欄時兩份都
  `FAIL`(證明假紅真的存在),加上型別欄後 產業→`DONE_NS`、個股→仍 `FAIL`(不受影響)。
- 63 個真檔名的**全量重跑對照**:v0107 三份研討會被誤判代號 2026 → v0108 **0 份**;
  型別分佈 個股 41 / 產業 9 / 大盤晨報 6 / 海外 4 / 研討會 3 = 63,每一份非個股都
  印得出判準理由。
- SelftestGrid **v0253** 兩站實跑綠。

### 券商正典化在真檔名上的實測(批412/413 的疊加層真的有用)

`JP-2330` → `JPM 摩根大通`、`CLST-6669` → `CLSA 里昂證券`、
`GF-Thoughts on TPU…` → **`DENY:拒絕清單:GF(操作員裁決)`**、
兆豐→`MEGA`、華南→`HUANAN`、凱基→`KGI`、國泰→`CATHAY`、台新→`TAISHIN`、
統一→`PRESIDENT`、`CTBC`、`MQ`→`MACQUARIE`、`UBS`、`Citi`→`CITI`、`Daiwa`→`DAIWA`。
63 份裡只有 5 份抽不出券商鍵,其中 `GF` 是**刻意拒絕**不是漏掉。

## 四十二、批419:那一跑成功了——但 37 份文摘裡只有 7 份的「上漲空間」是它字面的意思

操作員把工作站 2026-09-08 21:55 的真跑輸出貼回來,並令「用 GROK 的 U/I 顯示狀況,
逐步形成微系統 U/I」。

**先講成功的部分**:65 份真報告全走完五段鏈,ENG080 產出 **37 份四點文摘**,
`via-famui` 三頁再生 **GREEN 3/3**。VRN 從「尚無真報告」變成「有真報告、也真的跑出東西」。

**再講輸出裡兩件會讓人讀錯的事**——用他自己的數字證明,不是猜的。

### 一、目標價只有股價的 1/50 到 1/200(抽錯的數被印成預測)

| 檔 | 目標價 | 基準價 | 比值 | 印出來的「上漲空間」 |
|---|---|---|---|---|
| `MS-2308 20251128` | 37.8 | 1850.0 | **0.020** | −98.0% |
| `MS-8210 20251007` | 17.81 | 937.0 | **0.019** | −98.1% |
| `JP-3653 20251003` | 25.84 | 5655.0 | **0.005** | −99.5% |

沒有分析師會發 −98% 的目標價。那三個數是抽錯的(EPS、倍數、或外幣價)。
**印成「潛在上漲空間 −98.0%」比不印更糟**:讀的人會以為那是預測。

### 二、37 份全部拿 2026-09-07 的價去比,但 18 份的報告逾 180 天

最舊的 `Daiwa-1319` 是 **2023-10-11**——距基準日 **1062 天**。
拿三年後的價算三年前報告的「潛在上漲空間」,算出來的不是上漲空間,**是事後看圖**。
`JP-2330`(2025-07-18,416 天)印出 −48.9%,那不是分析師看空,是台積電漲了。

### 修(`VRN_ENG080_FourPointDigest_v0101.py`)

- **`tp_sanity()`** 合理帶 `[0.2, 5.0]`(=上漲 −80%～+400%)。帶外 → `TP_SUSPECT`,
  K1 **不列為潛在上漲空間**,改印兩個數字與比值並註明待人工核。
  **只 flag 不丟棄**——我們不知道哪個數字才對,丟棄等於替操作員決定;
  標可疑,他才知道要去翻哪三份 PDF。泓德 +192%(比值 2.92)仍在帶內=**不亂殺**。
- **`basis_state()`** 逾 `STALE_DAYS=180` → `STALE_BASIS`,K1 改把**報告時上漲**
  (批240 既有的 `upside_at_report`)放頭,今日比值降為「僅供參考,不作潛在上漲空間」。
- 兩態落庫(`tp_state`/`tp_ratio`/`basis_state`/`basis_days`,ALTER 加欄),
  逐份印 `⚑TP 疑誤` / `⚑非當期`,總結加 `tp_suspect`/`stale_basis`/`upside_trusted`。
- **順帶踩到批412 同一個坑**:加四個欄後位置式 `INSERT VALUES (?×36)` 立刻爆
  「40 欄 36 值」。改具名欄位。**記法:加欄就改具名。**

### 判讀結果(37 份)

| 判讀 | 份數 | 意思 |
|---|---|---|
| 可信 | **7** | 當期(≤180 天)且比值在合理帶內——「潛在上漲空間」是它字面的意思 |
| 非當期 | 18 | 今日比值僅供參考 |
| TP 疑誤 | 3 | 待人工核 PDF |
| 未算 | 9 | 報告沒抽到目標價 |

### GROK 側:微系統 U/I 的第一塊

新增 `src/lib/via/vrn-run.ts`(唯讀鏡面 + 同律判讀)+ 六檢、
`src/components/vrn-run-deck.tsx`(NAV「04 VRN 實跑」):三張摘要卡
(鏈跑完了/頁面再生/四點文摘判讀)+ 逐份判讀表,**排序刻意把要處理的放最上面**
(TP 疑誤 → 非當期 → 未算 → 可信)。總燈紅——有 TP 疑誤就是紅,不取巧。

驗:ENG080 v0101 **十四檢 14/14**(新檢 ⑬⑭ 的 fixture 比值與天數全部取自這 37 份真文摘);
SelftestGrid **v0254** 該站實跑綠;Grok `node --test` **250 pass / 0 fail**、`tsc` 零錯誤、
`vite dev` 實跑截圖。

## 四十三、批419b/c:閘門被自己的診斷訊息判死,以及一個看不出因由的 0

操作員拉齊後重跑,兩件事同時出現。

### 一、批419 的閘生效了,但我讓它把自己判死

```
[RED] MS-2308 … ⚑TP 疑誤(比值 0.020) · 新數字 ['0.020', '0.2']
[RED] MS-8210 … ⚑TP 疑誤(比值 0.019) · 新數字 ['0.019', '0.2', '5.0']
[RED] JP-3653 … ⚑TP 疑誤(比值 0.005) · 新數字 ['0.005', '0.2', '5.0']
[via-vrn4] RED · QC 紅 3 → vrn_fourpoint rc=1
```

閘門判對了(那三份的目標價確實可疑),但 K1 印出的 **比值 0.020** 與 **合理帶界 0.2 / 5.0**
是**閘門自己的診斷值**——是「關於擷取的後設說明」,不是「報告裡的宣稱」。
`novel numbers` 拿它們去查有沒有出處,等於要求**判準本身也要出現在報告正文裡**,無理。
結果三份 QC 紅、`rc=1`,**整段鏈被自己的診斷訊息判死**。

修(`VRN_ENG080 v0102`):把比值、合理帶界、天數、`STALE_DAYS` 一併列入 `derived`
(既有的「衍生數不計」機制,不另造)。新檢 ⑮ 帶對照組:
**不**把診斷值放進 `derived` 就會被判成新數字(證明這檢不是空檢),
而真的發明的數字(`7777`)照樣抓得到——閘門不是萬用赦免。

### 二、`券商正典鍵 0/59` —— 0 沒有告訴我們任何事

```
[SSOT 正規化] 券商正典鍵 0/59 · 評等正典鍵 0/59 · 分析師 +0(庫 0)· 金融機構 SSOT 在位
```

批412/413 端到端測過會通,現在全空。但**這一行給得出數字給不出因由**:0 可能是
SSOT 沒載、可能是券商 token 抽不到、也可能是抽到了而正典查無——三件事差很多。
**靜默的 0 跟假訊息一樣難查。**

修(`VRN_ENG073 v0109`),三件:

1. **`NULL` 不等於 `''`**。`WHERE broker_ssot_key <> ''` 在 SQL 裡對 NULL 回 **NULL 不是 TRUE**,
   加欄前寫入的舊列一律不被計入。改 `COALESCE(...,'')` 並**把 NULL 列數分開報**——
   「認不出」和「舊列沒這欄」不該長得一樣。
2. **報告型別直方圖**:`[報告型別] 個股 41 · 產業 9 · …`。分不出型別,收尾閘就會把
   產業/晨報/研討會當成失敗(批418 修的正是這個),所以要看得到它到底有沒有分。
3. **零命中逐項取樣**:命中 0 時直接取三份實跑同一支函式,印出
   `token=… → key=… src=…` 與模組路徑、`resolve_broker_filename` 是否可呼叫。
   **不猜**——下一跑就會直接說出是哪一段斷掉。

順帶修掉 `SyntaxWarning: invalid escape sequence '\m'`(docstring 內的 Windows 路徑,改 raw string)。

### 驗

ENG080 v0102 **十五檢 15/15**、ENG073 v0109 **二十七檢 27/27**(新檢 ㉗ 以
`MS`/`''`/`NULL` 三列實證直算會少算一列而 `COALESCE` 不會);SelftestGrid **v0255** 兩站實跑綠。

### 這一跑真正的好消息

`via-closeout vrn` 從 **65 份 / PENDING 6** 變成 **59 份 / PENDING 0**——收件與首頁兩段
**全清空**(`段:{'收件': 0, '首頁': 0, …}`),鏈跑得完了。DONE 25 維持,
三方對照從 61/65 升到 **59/59 全覆蓋**,DIVERGE 從 6 降到 4。

## 四十四、批419d:診斷程式碼把主流程弄掛,以及守衛太寬又走回假紅

操作員再跑一次,兩件事同時出現——**一件是好消息,一件是我的錯**。

### 好消息:批418 的分類確實在跑

```
[報告型別] 個股 37 · 產業 9 · 大盤晨報 6 · 海外 4 · 研討會 3
```

批419c 加的直方圖第一次讓我們看見:59 份裡 **22 份是非個股**,分類完全生效。
先前只能猜「有沒有分到」,現在是事實。**這就是加診斷的價值。**

### 我的錯一:診斷程式碼把主流程弄掛

```
File …VRN_ENG073_ReportStructuredDB_v0109.py, line 716, in run
    _con2 = duckdb.connect(str(db), read_only=True)
_duckdb.IOException: Cannot open database "…\VeritasIntelligenceAnalytics\None"
[via-console run] vrn_structdb rc=1
```

`run(zdir=None, db=None)` 的 `db` 是**函式參數**,解析後的路徑是區域變數 `dbp`。
我在關庫後另開一條唯讀連線,而且傳錯變數 → `str(None)` → `"…\None"` → 整支 rc=1。

**診斷程式碼把主流程弄掛,比沒有診斷更糟。**

修(`v0110`):取樣改在**關庫前**用同一條連線抓好,**完全不再開第二條連線**——
少一個地方可以傳錯路徑。新檢 ㉘ 以 stub SSOT 逼出零命中分支**真的走一遍**
(v0109 的自測從沒進過這條分支,所以沒抓到)。

### 我的錯二:守衛太寬,22 份非個股又被擋回 FAIL

批418 讓非個股判 `DONE_NS`,但我加了一道「真失敗才不放過」的守衛:

```python
_fail_states = getattr(mod, "FAIL_STATES", ())     # ← 含 MISSING_SOURCE
_real_bad = price_state == "DB_NO_MATCH" or upside_state in _fail_states
```

`MDL139.FAIL_STATES = ("FORMULA_MISMATCH", "FORMULA_MISMATCH_DB", "PARSE_SUSPECT", "MISSING_SOURCE")`
——而 **`MISSING_SOURCE` 正是產業/晨報/研討會的正常態**(沒代號 → 沒目標價 → 沒價)。
守衛於是把 22 份非個股**全部擋回 FAIL**,等於又走回假紅。

修(`MDL141 v0104`):非個股真正該留 FAIL 的只有
`FORMULA_MISMATCH` / `FORMULA_MISMATCH_DB` / `PARSE_SUSPECT`
——**數字抽出來了、而且對不起來**。`MISSING_SOURCE` 與 `DB_NO_MATCH` 是預期。

**這條為什麼檢沒抓到**:v0103 的 fixture `upside_state` 用**空字串**,
而真實資料是 `MISSING_SOURCE`。**fixture 不帶真實狀態,測的就不是真的那條路。**
v0104 的 fixture 改帶 `MISSING_SOURCE`,並多加一份「非個股但 `FORMULA_MISMATCH`」
證明守衛沒被拆掉——那一份照樣 FAIL。

### 驗

ENG073 v0110 **二十八檢 28/28**、MDL141 v0104 **十一檢 11/11**、
SelftestGrid **v0256** 兩站實跑綠。

### 這一跑的其他進展

`vrn_fourpoint` **rc=0**(批419b 的 derived 修生效,QC 紅 3 → **0**),
三份 TP 疑誤照樣掛旗標但不再判死;`via-closeout` 維持 59 份 / PENDING 0 /
三方對照 59/59 全覆蓋。

## 四十五、批419e:捕捉到卻不顯示,等於沒捕捉

### 先講成果:非個股修真的生效了

```
[via-closeout vrn] RED · 12/59 份核對 FAIL;另 22 份非個股已完成
  報告 59(DONE 25 · FAIL 12 · PENDING 0)
  DONE_NS 20251205兆豐晨會報告(一) / 20251208_台新台股盤勢分析 / Daiwa-PCB /
          GF-Thoughts on TPU / GS-AI PCB CCL …
```

**FAIL 從 34 掉到 12**,22 份產業/晨報/海外/研討會轉成「非個股已完成」。
`vrn_structdb` 也回 **rc=0**。批418→419d 那條線收斂了。

### 再講 `券商正典鍵 0/59`——診斷把答案交出來了

批419c 加的取樣印出:

```
· 20250819兆豐個股報告-泓德能源(6873)  token=兆豐 → key=(空) src=(空)
· 疊加層/正典模組:…\VIA_FinancialInstitution_Overlay_v0100.py
· resolve_broker_filename 可呼叫=True
```

**沙盒跑同一條鏈是通的**(實跑對照:`兆豐→MEGA`、`MS→MS`、`JP→JPM`,
`ssot_broker` 經 `fin_ssot()` 一樣通)。所以不是邏輯錯,是**執行期查詢在炸**。

看程式碼就找到形狀:

- 疊加層的 `overlay()` 是 `json.loads(OVERLAY_JSON.read_text(...))`,**沒有 try**
  ——資料檔讀不到就**丟例外**,不是回空。
- `ssot_broker` 的 `except Exception` 把因由存進 `_FIN["why"]` 然後回空字典。
- 而總結那一行 **只在模組是 None 時才印 `_FIN["why"]`**。

於是:模組載得起來(所以印「SSOT 在位」)、每次查詢都拋例外、**因由躺在
`_FIN["why"]` 裡沒人看**,對外只剩一個沒有理由的 `0/59`。

**捕捉到卻不顯示,等於沒捕捉。** 這跟批412「`except` 把 pydantic 錯誤吞成
『0 筆』」是同一個錯誤家族——那次我修的是單一支函式,這次要修的是**顯示規則**。

### 修(`VRN_ENG073 v0111`)

1. **因由一律印**:模組在位但 `_FIN["why"]` 非空時,總結行補
   「**查詢期例外**:…」。
2. 零命中診斷加印**疊加層自己的 `stats()`**(`filename_keys` 幾條、`canon` 在不在)
   與**資料檔路徑及是否存在**——JSON 沒載/壞掉會直接在這裡現形。

新檢 ㉙ 用「**模組在位但每次查詢都炸**」的 stub 重現工作站的故障形狀,
斷言 `rc=0`、因由印得出來、而且是**原始**因由(不是重述)、`stats()` 炸掉也照實說。

### 驗

ENG073 v0111 **二十九檢 29/29**、SelftestGrid **v0257** 該站實跑綠。

### 還沒解的

`0/59` 的**根因**還沒定案——下一跑的 `stats()` 與資料檔存在與否會直接指出來:
若 `filename_keys=0` 或資料檔不存在,就是 `VIA_FinancialInstitution_Overlay_v0100.json`
沒被拉到/讀不到;若 `stats()` 正常而查詢仍炸,那是別的東西。**不猜。**

## 四十六、批419f:診斷把根因交出來了——正典缺席時,疊加層自有的鍵一起陪葬

### 診斷奏效:一字不差的根因

批419e 加的兩行,下一跑就把答案交出來:

```
[SSOT 正規化] 券商正典鍵 0/59 · … · 金融機構 SSOT 在位
              · **查詢期例外**:正典載入失敗 ModuleNotFoundError:No module named 'pydantic'
[SSOT 診斷] … stats()={'deny_keys': 20, 'broker_alias_add': 23, 'broker_add': 5,
                        'rating_alias_add': 59, 'filename_keys': 16,
                        'canon': "缺席:正典載入失敗 … No module named 'pydantic'"}
            疊加層資料檔:…\VIA_FinancialInstitution_Overlay_v0100.json · 存在=True
```

**疊加層資料全在**(16 條檔名鍵、20 條拒絕、23+59 條別名),**正典載不起來**
——`via_vrn_312` 沒有 `pydantic`。從「0 沒有告訴我們任何事」到「一行說完」,
中間隔的就是批419c/e 那兩次加診斷。

### 根因:把已知的資料丟掉

```python
def resolve_broker_filename(token):
    tgt = filename_key_map.get(token)      # 兆豐 → "MEGA"  ← 查到了
    if tgt:
        r = resolve_broker(tgt)            # 拿 MEGA 去問正典要中英名
        return r                           # 正典缺席 → r["key"] 是空的 → 整個丟掉
```

`resolve_broker("MEGA")` 的次序是 拒絕 → 正典 → 疊加層別名 → 疊加層新增機構。
`MEGA` 是**正典**的機構,所以正典一缺席就全落空——即使
`filename_key_map` **已經知道** `兆豐 → MEGA`。

**中英名確實只有正典有,但「鍵」是操作員裁決寫在疊加層 JSON 裡的資料。**
正典缺席不影響那個鍵成立。把它一起丟掉,是把已知的資料丟掉。

### 修(`VIA_FinancialInstitution_Overlay_v0101.py`)

- 新 `overlay_keys()`:疊加層自己知道的鍵集合(`filename_key_map` 的目標 ∪
  `broker_alias_add` 的鍵 ∪ `broker_add` 的 `ssot_key`)。
- `resolve_broker()`:**正典缺席時**,若 `value` 命中 `overlay_keys()`,鍵照回、
  中英名**誠實留空**、`src="OVERLAY_KEY(正典缺席;僅鍵無中英名)"`——**不冒充 CANON**。
- `resolve_broker_filename()`:對映查得到目標鍵卻因正典缺席回空 → 直接回那個鍵,
  `src="FILENAME_MAP(正典缺席;僅鍵無中英名)"`。
- **界線沒有放寬**:查無仍是查無(`不存在的券商XYZ` → 空,不硬造);
  拒絕仍壓過一切(`GF` → DENY);正典在位時一切照舊走 CANON。
- 資料檔改**尾版 glob**,不再把 `v0100.json` 的名字寫死在 v0101 裡。

### 驗

疊加層 **十檢 10/10**(新檢 ⑩ 把 `_CACHE["ssot"]` 強制設成缺席以重現 vrn 境無 pydantic);
**端到端實證**:同一條 `ENG073.ssot_broker` 鏈在正典缺席下跑 9 個真檔名 → **命中 8**
(`兆豐→MEGA`、`MS→MS`、`JP→JPM`、`CLST→CLSA`、`凱基→KGI`、`華南→HUANAN`、
`CTBC→CTBC`、`UBS→UBS`;`GF` 正確 DENY)。SelftestGrid **v0258** 該站實跑綠。

### 誠實界限:這不是 pydantic 的替代品

券商**鍵**回來了,但這三件仍然要正典,也就仍然要 `pydantic`:

- 券商中英名(`broker_name_zh` / `broker_name_en`)
- 評等正典鍵的 `code` / `direction`
- **分析師姓名擷取**(`analyze_contact_document` 整支都在正典那一層)

補法一行:`uv pip install --python C:\Users\tonyk\envs\via_vrn_312 pydantic`

## 四十七、批419g:券商鍵 0→54 之後,評等仍 0——抽取器的詞表比正規化器窄

### 批419f 的修生效了

```
[SSOT 正規化] 券商正典鍵 54/59 · 評等正典鍵 0/59 · … · 查詢期例外:… No module named 'pydantic'
```

`0/59 → 54/59`。剩下 5 個是檔名本來就沒有券商 token 的
(`3014TT-20231005`、`投資早報251209`、`6933_AMAX-KY`、研討會三場),**那是對的**。

### 但評等還是 0——而且是另一種病

`ssot_rating` 的次序是:`rating_raw`(`RATING_RX` 抓到的)→ 內文用 `RATING_RX` 逐詞試。
兩道**都以 `RATING_RX` 為詞表**,而它只認:

```
Buy|Sell|Hold|Neutral|Overweight|Underweight|Outperform|Underperform
買進|賣出|中立|增持|減持|優於大盤|強力買進
```

批413 把 **59 條別名**加進疊加層(加碼/續抱/低配/未評等/超配/區間操作…),
但**掃描器看不到它們**。實測:`加碼`/`續抱`/`低配`/`未評等` 四個 `RATING_RX` 一個都不中。

**字典加了 59 條,掃描器只認 15 個詞——加了等於白加。**

### 修(`VRN_ENG073 v0112`)

第三道:改用**疊加層自己的別名**當掃描詞表(Zero-Hydra,**不寫第二份詞表**),
且**只掃標題帶/右區與檔名**——評等就寫在那裡,掃全文只會把內文敘述裡的
「中立」當成評等。只收 ≥2 字的詞(單字「買」「空」在內文太容易亂咬)。

計數同時加「**原始評等字串 N 筆**」:0/59 有兩種可能——抽取階段就沒抓到字串,
或抓到了但正規化查不到。只印後者的分母,就跟先前那個沒有因由的 0 一樣難查。

### 順帶補上兩條疊加層資料(操作員裁決掉了一半)

- **`加碼`**:操作員裁決是「**增持 = 加碼** = BUY」,但疊加層只帶了「增持」,
  「加碼」一直靠**正典**。批413 的檢是在正典在位時過的,所以沒發現——
  **正典缺席時,操作員親自裁決的一半就掉了**。已補進疊加層自帶。
- **`未評等` / `NR`**:出自操作員真檔名 `瑞基(4171,NR_未評等)-CTBC251208`;
  疊加層原本只有「未評級」。

兩條都是**補完既有裁決**,不是新裁決;正典仍然一個字都沒動。

### 驗

ENG073 v0112 **三十檢 30/30**(新檢 ㉚ 實證舊詞表漏掉四個、詞表 67 條、
`加碼→BUY`、`未評等→NOT_RATED`、無評等→空不硬塞、`Buy` 原路照舊優先);
疊加層 **十檢 10/10**;SelftestGrid **v0259** 兩站實跑綠。

**判準對著事實寫**:第一版我斷言「這五個 `RATING_RX` 都不中」,實測發現
「增持」本來就在裡面 → 改成四個。批419d 的教訓再一次:**斷言要對著真實狀態寫。**

## 四十八、批420:操作員規格——檔名拆解律 + 評等全名冊

### 診斷先分辨出是哪一段(批419g 的成果)

```
[SSOT 正規化] 券商正典鍵 54/59 · 評等正典鍵 4/59(原始評等字串 34 筆)
```

**34 筆有原始評等字串,只有 4 筆解得出鍵**——所以不是抽取問題,是**正規化查不到**。
而且是券商那個病的翻版:`Buy`/`買進`/`中立` 這些**基本詞只在正典裡**,疊加層只帶
別名(增持/加碼/續抱…),正典缺席就全落空。已把基本詞補進疊加層自帶
(BUY 19→32、HOLD 14→24、SELL 14→24、NOT_RATED 16→22);正典在位時次序仍是
**正典先行**,這些永遠不會蓋過正典。

### 操作員規格,逐條實作

> 「FILENAME 拆解方式就是中英文標點符號轉換處切開來,TRIM 過便成為獨立連續的
> 英文/中文/數字的單位。四碼數字是台股的 TICKER,較長的數字為日期。
> TICKER 去 TWSE/TPEX 找名稱。名字-KY 也是公司名稱。**3014TT 是 3014 TT**。」

新增 `tokenize_filename()` —— 一支具名、可測的拆解器:

1. **標點切**:ASCII 與全形一併收(`-_()【】,、。;:` 等)。
2. **字集轉換處再切**:數字 / 英文 / 中日韓各自成段。
   **這一條就是 `3014TT` 的解**——它沒有標點,只有數字↔英文的轉換;
   舊的三支 regex(`TICK_RX` 掃裸四碼、`parse_date` 三種寫法、`parse_broker`
   拿字典做子字串掃)各管一段,**誰也切不開**。
3. **四碼數字 = 台股 TICKER**(年份守衛照舊在後面把關,批418)。
4. **較長的數字 = 日期**:8 碼 `20251202`、7 碼民國 `1141202`、6 碼 `251209`。
5. **市場後綴** `TT`/`TW`/`TWO`/`TPE` 單獨記,不當代號也不當日期。
6. **名字-KY 也是公司名稱**:中文段(或英文段)後面緊跟 `-KY` 就合體收進名候選,
   `貿聯` 與 `貿聯-KY` **兩個都留**,交給 TWSE/TPEX 名冊決定。
   代號抽不到時改以名候選反查名冊,並在 `conflicts` 記 `TICKER_FROM_NAME=…` 留痕。

`parse_date` / ticker 候選 / 名冊反查**全部改吃拆解器的結果**,不再各切各的。

> 「RATING_LIST=() 所有評等中英文名稱,第一頁符合即可。」

新增 `RATING_LIST`(中英文共約 100 條)併入掃描詞表(與疊加層別名聯集,共 **109 條**)。
它是**掃描詞表不是判定表**——判定仍走正典/疊加層 `resolve_rating`,
認不出就是認不出(Zero-Hydra:本器不自建第二份「詞→鍵」對照)。

### 驗:對著操作員的 63 份真檔名跑

| | 結果 |
|---|---|
| 有日期 | **60/63**(3 份本來就沒有:`6933_AMAX-KY_個股介紹報告` 與兩場研討會) |
| 有四碼代號候選 | **44/63** |
| 日期候選有但解不出 | **0** |
| `3014TT-20231005` | 代號 `3014` · 日期 `2023-10-05` · 市場 `TT` |
| `凱基投顧_3665 貿聯-KY_…` | 代號 `3665` · 名候選含 `貿聯-KY` |
| `華南投顧-2637-慧洋-KY-1141202` | 代號 `2637` · 民國日期 `2025-12-02` · 名候選含 `慧洋-KY` |
| `瑞基(4171,NR_未評等)-CTBC251208` | 代號 `4171` · 評等 `NOT_RATED` |
| `晶心科(6533,N,中立)-CTBC251208` | 代號 `6533` · 評等 `HOLD` |

ENG073 v0113 **三十二檢 32/32**、疊加層 **十檢 10/10**、SelftestGrid **v0260** 兩站實跑綠。

### 操作員已補 pydantic

`uv pip install --python …\via_vrn_312 pydantic` → `pydantic==2.13.5` 已裝。
下一跑正典會在位:券商中英名、評等 `code`/`direction`、**分析師姓名擷取**三件會一起回來,
`src` 也會從 `OVERLAY_KEY(正典缺席…)` 變回 `CANON`。

## 四十九、批421:兩收容系統升格為 VRN 支援模組——順手抓到寫死的尾版律破口

操作員令:「REGISTER AND IMPLEMENT THESE TWO SYSTEMS AS SUPPORTIVE MODULES TO
SUPPORT VRN」,附 `GenericLayoutEngine_AllEngines_v2.1.0` 與
`VIA_NLP_Application_System_v1.8.0` 兩包。

### 收容前先查驗:一包是新的,一包不是

| 上傳包 | 逐檔比對結果 | 處置 |
|---|---|---|
| GLE AllEngines v2.1.0(18 檔) | 對在庫 `..._v2.1.0_b245` **16 檔位元相同** | **不新增收容夾** |
| ↳ `Install-GenericLayoutEngine-All.ps1` | 唯一差異:`${ExitCode}:` → `$ExitCode:` | 不採(見下) |
| ↳ `dist/*.whl` | 原始碼的建置產物,原始碼已在庫 | 不收(不留二進位重複件) |
| NLP Application System v1.8.0(68 檔) | 對在庫 v1.5.0 **多 5 支、13 檔改版** | **收容**,原件一位元未改 |

那個 installer 差異值得記一筆:PowerShell 裡 `"$ExitCode:"` 的冒號會被當成範圍/限定
符解析,`"${ExitCode}:"` 才是安全寫法。**在庫那份是對的,上傳那份是回歸** —— 所以不採。
「新上傳的就比較新」不是通則,逐檔比對才是。

### 真正的缺陷在鏈上,不在收容夾

```
VRN_ENG072_FirstPageText_v0106.py:123   pkg = _INTAKE / "VIA_NLP_OneEngine_v1.1.0"
VRN_ENG073_ReportStructuredDB_v0113.py:134   pkg = HERE/".../VIA_NLP_OneEngine_v1.1.0"
```

**寫死。** 庫裡早有 v1.5.0,現在又有 v1.8.0,兩支引擎永遠掛不上。
`ENG077`/`ENG078` 兩座舊橋雖然都做了尾版 glob,但**鏈上四支引擎沒有一支走橋**。

差多少?v1.1.0 有 18 支模組,v1.8.0 有 39 支。多出來的這六支,正是研報解讀要用的:

`table_ops`(表格結構化)· `layout_analysis`(版面分塊)· `content_roles` ·
`context_reconstruction` · `summarization` · `function_classifier`

### 新增兩支支援模組(`supportive modules/70_VRN_Rules/`)

**`SUP_MDL743_GenericLayoutHub_v0100`** — GLE 全後端統轄橋。九檢 9/9。
在此之前,收容件只有 ENG072 私下掛載,而且只用 `generic_layout_engine` 一支;
`all_backend_engines`(32 支 adapter 優先序)與 `multi_engine_orchestrator`(路由/共識/快取)
**全樹無人呼叫**——收容了但沒被採用。本橋把四支正主收成單一掛載點,
`zone_annotate` 與 ENG072 的 `gle_annotate` 逐鍵同契約,實作只留一份。

寫這支時被自己的檢咬了兩次,兩次都是真的:

- 我先斷言路由表有六個模式 `auto/consensus/tables/paddle/ocr/all`。實際 `MODE_ADAPTERS`
  **只有四個具名鍵**,`auto` 與 `all` 根本不在表內,是靠 `build_route` 的 else 落到
  `build_all_adapters()`。改成如實回報四具名 + 落空分支,並另開 `route_fallthrough()`
  把去向講明白。**斷言要對著真實狀態寫,不是對著我以為的樣子寫。**
- 「本橋零安裝動作」那一檢用字串比對掃自己的原始碼,結果掃到**斷言自己寫的那些字串**
  = 自指偽陽。改用 AST 檢查匯入面(`subprocess`/`os`/`pip` 一個都沒有)。

**`SUP_MDL744_NLPApplicationHub_v0100`** — NLP 應用系統統轄橋。十一檢 11/11。
跨 `VIA_NLP_OneEngine_v*` 與 `VIA_NLP_Application_System_v*` **兩個家族名**做語意尾版解析
(只認一個 glob 就會漏掉尾版)。另有兩件本橋獨有的防制:

- **`__main__` 排除**:它 `import` 即跑 argparse,會用 `SystemExit` 中斷宿主。
  第一次全模組探測就是被它炸掉的。
- **雙掛防制**:同一個行程只能有一個 `via_nlp_engine`。舊引擎若先把 v1.1.0 掛進
  `sys.modules`,本橋**不偷換**,回 `MOUNTED_STALE` 並指出先佔者是誰。

### 接鏈:兩支引擎改走橋,退路一寸不少

`ENG072 v0107`(十六檢 16/16)· `ENG073 v0114`(三十三檢 33/33)

三段誠實退路:**橋 → v1.1.0 直掛(原行為逐字不動)→ stdlib NFKC**。
ENG073 的 `run` 尾段新增一行 `[NLP 掛載]`,把走了哪條、為何沒走橋當場印出來
——批419e 的教訓:捕捉到卻不顯示,等於沒捕捉。

新檢怎麼證「真的走到尾版」?**全形轉半形不能當證據**,`ＡＢＣ１２３ → ABC123`
stdlib 也做得到,測不出差別。改用判別輸入:

| 輸入 | stdlib NFKC | TextProcessor |
|---|---|---|
| `台積電  的的的營收`(連續空白) | `台積電  的的的營收`(不併) | `台積電 的的的營收`(併) |

外加缺席對照組:把 `HUB_DIR` 指到空夾,兩支橋都得**退回直掛而不是炸掉**。

### 一項自審更正

上一則回覆我對操作員說「ENG074 現在只用 pdfplumber+fitz 雙法」——**這是錯的**。
ENG074 其實只有 `fitz` 文字 + 行級 regex **一法**;docstring 第 24 行寫的是 ENG072 的法B。

而本批**沒有動 ENG074**。原因是實測結果不支持我原本的假設:
`fitz.get_text("text", sort=True)` 會把分欄版面的標籤與數字**併回同一行**,
舊法在那種情形是 work 的,我造的合成樣本沒有重現真實故障。
剩下的 12 筆真 FAIL 全是 GS 英文報告,不拿到真檔無從斷因 ——
**不憑猜測去動一條已經跑綠的鏈。**

### 登錄

`Register v0166`(`via-gle`/`via-nlp` + 別名 `版面橋`/`語意橋` + 兩梭;
梭機制與正典 `via-closeout.cmd` 逐行相同)· `SelftestGrid v0261`(+兩站)· 台帳 914。

## 五十、批423:卡斷根治——輸出被吞、逾時沒接線,兩條都不在被懷疑的那一端

操作員令:「卡斷 加入20個加速器 不卡斷 動態進度條」。
實錄:`via-go` 印出「── ① TEST(自測矩陣)──」之後**畫面完全不動**。

### 先排除被懷疑的那一端

直覺會說「自測矩陣 200 站太慢」。但看格子的程式碼,它**逐站都有 `flush=True`**,
而且早就有 SuperAccel 平行(8 工人)。格子不是啞巴。

真正的兩條根因都在 `Invoke-VIA-AllGreen-v0100.ps1`:

```powershell
# 根因① — 第 45 行
$out = & $PY @Argv 2>&1 | Out-String      # ← 緩衝到子行程結束才吐

# 根因② — 第 12 行
param( [int]$StageTimeoutSec = 1200 )     # ← grep 全檔:只有這一行,從未被使用
```

**①** `Out-String` 把 200 站的輸出全部吞進管線,跑完才一次吐出。
格子每站都在喊,操作員一個字都看不到 —— 批419e「捕捉到卻不顯示,等於沒捕捉」的 PowerShell 版。

**②** 檔頭契約寫著「非阻塞(無 Read-Host/無限等待)· 誠實 OK/FAIL/NOT_RUN 不卡斷」,
`$StageTimeoutSec` 也宣告好了 —— **但整支檔案沒有一行用到它**。
契約寫了,實作沒接。跟批422 的假綠(`MDL141` 不讀 `tp_state`)是同一個家族:
**宣告了、沒接線。**

### 修法

**`Invoke-VIA-AllGreen-v0101.ps1`** — `①~⑭` 流程、判準、Gate 文字一字未改,只換「怎麼跑一站」:

| | |
|---|---|
| `def_Drain` | 以 `FileShare::ReadWrite` 開重導向檔,每 0.4s 排出新行即時轉播 |
| 逾時 | `$StageTimeoutSec` 真正接線,逾時 `Kill()` |
| 第四態 | `TIMEOUT` —— **不冒充 FAIL 也不冒充 OK** |
| 進度 | `Write-Progress` 進度列 + 每站耗時 |
| 加速器 | `def_AccelLamp` 開跑先點 20 加速器名(缺席誠實說缺) |

真 pwsh 7.4.6 實跑驗證:

```
=== ① 逾時真的會 Kill(上限 3s,子行程要跑 30s)===
  [RUN    ] 慢站 · 逾時上限 3s · 子行程輸出即時轉播 ↓
      |   慢站心跳 1/30 … 4/30
  [TIMEOUT] 慢站 · 3.3s          ← 不是 30s
=== ② 輸出即時轉播 ===
      | 逐步輸出 1 … 5           ← 逐行出現,不再等到最後
```

**`CGC_MDL064_SelftestGrid_v0262.py`** — 格子端補三件:

- 動態進度條:TTY 走 `\r` 就地重畫;**非 TTY 每 10 站一行**(被導向檔案時,
  200 行進度條會把站名洗光)
- `SELFTEST_PROGRESS.json` 心跳每站落檔 —— 外部可以證明行程還活著,
  不必去猜「沒輸出」是卡死還是在跑
- Ctrl+C 安全落檔:**中斷不是崩潰**。已跑完的站是真證據,寫出來;
  沒跑到的標 `NOT_RUN`(不冒充 `SKIP`);`rc=130` 不冒充成功也不冒充失敗

加速器點名實測:`Celeritas OK · lib 9/88 · 能力 7/31 · 執行緒預算 3 · maxsafe · 缺 79 支(列名不假在)`。

### 自審:我差點自己製造一個新的假訊息

心跳檔本來命名 `GRID_PROGRESS.json`。**我自己的測試第一次就踩到** ——
`sorted(glob("GRID_*.json"))[-1]` 取到的是心跳不是證據(字母序 `GRID_P` > `GRID_2`)。

追下去發現會被害的不只我的測試:

| 消費者 | 取法 | 後果 |
|---|---|---|
| `VRN_ENG068_DailyBrief`(三版) | `sorted(glob("GRID_*.json"))` | 取到心跳 |
| `CGC_MDL131_ProjectCompletion` | **按 mtime** | 心跳永遠最後寫 → **必中** |
| `CGC_MDL095_DeckServer` | `[-1]` | 取到心跳 |
| `Invoke-VIA-FinishLine` | `-Filter 'GRID_*.json'` | 取到心跳 |

改名 `SELFTEST_PROGRESS.json`。
**教訓:新增產出檔之前,先查誰在 glob 同一個樣式。**

### 死路修:修好了但送不到,等於沒修

倉庫裡**沒有任何東西呼叫 AllGreen**。`via-go` 是操作員自己放在 PATH 上的檔,
指向寫死的 `v0100` —— 批358 已記「PATH 上已有操作員之 via-go;同名=九頭龍→讓位」,
所以短令冊永遠不能佔 `via-go` 這個名。

**只推 v0101 的話,操作員的 `via-go` 照樣跑 v0100、照樣卡。**

→ `Register v0167` 新登錄 `via-allgreen`(尾版律 glob `Invoke-VIA-AllGreen-v*.ps1`;
別名 `統包`)+ `via-allgreen.cmd` 梭(機制與正典 `via-closeout.cmd` 逐行相同)。
新版一落地就自動生效,不必再改任何寫死路徑。

回歸:橋743 **9/9** · 橋744 **11/11** · ENG072 v0107 **16/16** · ENG073 v0114 **33/33**。
四支 `.ps1` 全數通過 `Parser::ParseFile`(含批421 的 `v0166` —— 那批我沒驗過語法,補驗了)。

## 五十一、批424:TEST→DEBUG→…→TEST 五輪實跑——修的是自測本身在污染正本

操作員令:「TEST DEBUG OPTIMIZE TEST DEBUG CONSOLIDATE TEST DEBUG **TILL THEY WORKS**」。
不是給指令,是在沙盒裡把 201 站自測矩陣**跑到修完**。

| 輪 | 結果 | 這一輪做了什麼 |
|---|---|---|
| R1 | OK 162 · FAIL 36 · 151s | 基準。批423 的進度條與心跳全程生效,不再有畫面空白 |
| R2 | — | 補件(pyarrow/bs4/yfinance/fastparquet/lxml) |
| R3 | — | 補件(openpyxl/matplotlib/opencc) |
| R4 | OK 173 · FAIL 25 | 補 pytest、jieba |
| R5 | **OK 177 · FAIL 22** | 自指站落後一輪的驗證 |

**15 站轉綠。**

### 真缺陷:自測每跑一次就往正本冊塞一筆

```python
# SUP_MDL742_ToolLadder_v0100.py selftest ⑥⑦
e2 = escalate("OCR_PDF_TEXT", 3, "selftest 演練證據:L1 pdfplumber 對掃描件回空文字")
#    ↑ escalate() 寫的是正本 VIA_Tool_Escalation_Ladder_v0100.json
```

本 session 十餘跑,`escalation_log` **66 筆 → 78 筆**,全是「selftest 演練證據」。
工作站每天跑一次 `via-selftest` 就多一筆,**真實升階紀錄會被演練資料淹沒**。
這違反正本零觸碰。

修法(`v0101`)刻意不走捷徑:

- 自測期間把 `LADDER_P` 改指 tempdir 內的正本副本
- **`escalate()` 一行未改、不加測試旗標、不弱化斷言** —— 走的仍是同一條真實寫入路徑
- 新增檢⑩:`sha256` 前後比對證明正本零位元變動,**且副本確實多一筆**
  (證明寫入真的發生了,這一檢不是空轉)

驗證:連跑三次自測,正本仍 66 筆、`git diff` 無變更;十檢 **10/10**。

### 結構性事實:自指站永遠慢一拍(不是回歸)

格子裡有四個站讀**格子自己的存證**:

| 站 | 讀什麼 |
|---|---|
| MDL088 五系統測試分頁 · MDL104 測試結果總表 · MDL110 三軌測試矩陣 | 最新 `GRID_*.json` |
| MDL093 治理台 UI Matrix | 綠燈率 ≥95% |

它們在格子**內**跑時,本輪存證還沒落檔,讀到的是**上一輪**的證據。
所以修好之後的第一輪它們仍紅,第二輪才轉綠。

實測對照:**R4 三站紅,但單獨跑全綠;R5 三站全綠。**
`MDL093` 例外 —— 它斷言的是綠燈率,那是**後果不是原因**,別家紅它就跟著紅。

這條已寫進 `Grid v0263` 檔頭,免得下次有人把它誤判成回歸。

### 兩個 pip 教訓

1. **批次安裝會互相拖累。** `jieba` 建 wheel 失敗,把同一批的 `openpyxl`/`matplotlib`/
   `opencc` 全拖下水 —— 三支都沒裝成,而輸出看起來像成功。**分開裝才看得出誰真的失敗。**
2. **jieba 是純 Python。** pip 建不起來時,把套件目錄直接搬進 `site-packages` 就能用
   (分詞實測 `['台積電','第三季','毛利率','創高']` 正確)。

補件的連鎖效果:`opencc` 一裝就修掉 `ENG066 ②`(9/9)與 `ENG064 ②③b`;
`pytest` 修掉 `ENG064 ⑧`;`jieba` 補上後 `ENG064` 9/9、`SUP_MDL742 ④` 轉綠。

### 剩下 22 站沒有被改成綠

| 類 | 站數 | 為什麼不動 |
|---|---|---|
| 要操作員的 DuckDB | ~19 | `global_daily`/`tw_daily_prices`/`tw_listings`/`tw_prices_adj`/`features_daily`/ETF 共識庫。**沙盒沒有庫就是沒有**,檢誠實地紅 |
| 後果非原因 | 1 | `MDL093` 綠燈率 |
| 沙盒環境 | ~2 | matplotlib 缺 CJK 字型(`findfont`) |

其中 `MDL105 ⑨` 值得單記:它斷言 `VIA_UI_ETFConsensusAnalysis_v0100.html` 存在,
查出該頁**自批303 起就在 `.gitignore:311`**(產出物不入庫),
產生器 `VDF_ENG068` 在無庫時誠實停(`[ETF共識] 在庫來源缺=誠實停`)→ 同屬資料依賴。

**弱化斷言就是造假。** `SUP_MDL742 ④` 斷言 jieba 這個最輕階必須在位 ——
我的解法是把 jieba 裝起來,不是把斷言拿掉。

### 清理

五輪跑下來沙盒重生了 **25 個產出檔**(19 個 `ui_support` HTML + 6 個 `registry` JSON,
其中 `VIA_Schema_Registry` 少了 **343 行** = 沙盒無庫的塌陷),全數 `git checkout` 還原。
**不把沙盒狀態寫進正本** —— 批416、批421 之後同一教訓的第三次。

## 五十二、批425:自己造報告把 VRN 跑到 GREEN——四例「參數在、線沒接」

操作員令:「Test by yourself debug optimize test debug **till VRN works** and then **verify if VDF works**」。

沙盒沒有操作員的報告,也沒有他的庫。所以自己造:五份**符合命名慣例的真 PDF**
(中文券商個股 / GS 英文個股 / 民國日期檔名 / 晨會報告 / 產業報告)+ 一個
`tw_daily_prices(date, ticker, close, adj_close)` 的 DuckDB,然後跑**真 `run`**,不是跑自測。

### VRN 最終:GREEN

```
[via-closeout vrn] GREEN · 報告 5(DONE 3 · FAIL 0 · PENDING 0)· 三方對照 5/5
  DONE    志強-KY(6768)   段 4/4  BASIC VERIFIED  FIN VERIFIED  四點✓
  DONE    GS-2330        段 4/4  BASIC VERIFIED  FIN VERIFIED  四點✓
  DONE    慧洋-KY(2637)   段 4/4  BASIC VERIFIED  FIN VERIFIED  四點✓
  DONE_NS 晨會報告 · 產業報告
```

| 報告 | 目標價 | adj close | 算出上漲 | 對照 |
|---|---|---|---|---|
| 志強-KY(6768) | 145 | 118.0 | **22.9%** | 報告自稱 23.0% → `ROUNDING_ONLY` |
| GS-2330 | 1275 | 1130.0 | **12.8%** | — |
| 慧洋-KY(2637) | 78 | 68.9 | **13.2%** | — |

### 一路上修的四件,全是同一個病

**參數在、線沒接。**

| # | 位置 | 病灶 | 實跑證據 |
|---|---|---|---|
| ① | `ENG073 v0114` | `main()` 是光禿禿的 `return run()`;`run(zdir, db)` 簽名擺著,CLI 從不解析 `--dir`/`--db`,**傳了不生效也不吭聲** | `--db` 被吞 → 讀到殘留舊庫,`庫 8 · DB_NO_MATCH` |
| ② | `ENG074 v0102` | run 分支寫死 `run(d, None, ...)` —— db 那格是 `None`;而 `--db` 在 `--crosscheck` 分支**有**解析,所以更難察覺 | 印「對照 5 件 → 28 列」,收尾讀 X 卻是「已對照 **0/5**」 |
| ③ | `MDL141 v0104` | `main()` 不解析 `--db`/`--zones`,但 `vrn_closeout(..., db=DB_TW)` 參數一直在、`closeout(**kw)` 一直會轉發 | ENG080 報 GREEN、上漲已算 3/3,收尾卻三份都印「**四點-**」 |
| ④ | `AllGreen v0100`(批423 已修) | `$StageTimeoutSec` 宣告了整檔沒用過 | 任一站卡住就永遠等 |

**四天內同一模式第四次。** 已寫進 `Grid v0264` 檔頭。
三支的新檢都用**攔真實呼叫**證明旗標有傳到,不掃原始碼字串
——那只證明字在,不證明會生效。

### 自審:兩次差點把自己的錯報成引擎的錯

1. 第一版 fixture 抽回來是 `NT,275`,我一度認定是「千分位逗號解析 bug」。
   實查是 **bash heredoc 沒加引號,`$1` 被當成位置參數吃掉了** —— 引擎無辜。
2. `ENG080` 起初報 `adj — · 上漲未算`。查出是我的價表沒有 `adj_close` 欄,
   而引擎**誠實拒絕拿 `close` 頂替**(「Adjusted 與原始不混用」)—— 正確行為,不是 bug。
   補欄後 3/3 全算出。

**先證明是被測物的錯,再動被測物。**

### VDF 驗證

`via-rungate --family vdf`:**引擎 8/8 OK · 必要庫 4/4** · 選配 2/4。
判 `YELLOW` 的唯一原因是沙盒無 `via_vdf_312` 家族境、退 base python
(誠實標註「能跑≠本位」)—— 不是程式碼問題。

自測過不等於產得出資料,所以再跑兩支唯讀動詞驗真:

```
VDF_ENG081 check → 2025-12-04 價 2 · 12-03 價 4 · 12-02 價 4 · 12-01 價 4
                   RED 籌碼表缺 (tw_chip_inst, tw_chip_margin)
VDF_ENG079 scan  → RED 本機三庫根缺 C:\新增資料夾(Windows 路徑,沙盒本來就沒有)
```

`ENG081` **真的讀到了我的價表**,每日檔數與插入列數完全吻合,然後誠實紅在缺料上。

**離線驗不到的部分照實說**:價格 / 籌碼 / 月營收的**擷取道**要同意閘 + 網路。
我不代設同意閘,所以那一段未驗。

### 回歸

`ENG072 v0107` 16/16 · `ENG073 v0115` **34/34** · `ENG074 v0103` **16/16** ·
`ENG080 v0102` 15/15 · `MDL141 v0105` **12/12**。

## 五十三、批426:首頁全能引擎 v0101 → v0102——先驗貨,六項缺陷全部實測坐實

操作員上傳 `VIA_VRN_FirstPageEngine v0101`,令「根據上面資訊更新給我一個升級版」;
續傳 `VRN_MDL008_CrossValidator` / `VRN_TW02_ReportParser` / `ENG024` / `ENG025`,
令「整合如果關聯 驗證法」;再補規格三條。

### 先驗貨:六項缺陷都是跑出來的,不是讀碼猜的

| # | 缺陷 | 實測 |
|---|---|---|
| ① | `NLPRepair` 掛鉤呼叫 `self.ext.repaired()` | `TextProcessor` **沒有這個方法**(只有 `repair()`,且回 dict)→ 每次 `AttributeError` 被 `except` 吃掉 → **靜默退啟發式,外接引擎等於沒接** |
| ② | `multiply(None,10,5)` / `add_sub(None,[1,2])` | **當場 `TypeError`** —— 而 `None` 正是抽取器找不到數字時的常態回傳 |
| ③ | 民國七碼 `1141202` | → `None`(操作員真檔名正在用) |
| ④ | `慧洋-KY` | 被切成 `慧洋` + `KY` |
| ⑤ | `Price Target 650` / `PT 78` | → `None`(只認 `NT$` 與 `目標價`) |
| ⑥ | `restore_period_header` | 只認 `12/24A` 與 `2023` 兩型 |

①是最隱蔽的一個:掛鉤存在、看起來有接、實際永遠走後備,而且**失敗被吞掉不外顯**。

### 整合判定:關聯的才綁,不關聯的不硬塞

`MDL008` 是**正典驗證層**(`to_million/std_val` 單位、`tolerance` 依量級的絕對容差、
`compare_one/classify_mismatch/fallback_resolve`),而 v0101 的 `_band()` 是它的
**粗糙複製品**,而且模型不同:

| | 容差模型 |
|---|---|
| `MDL008` | 依金額量級給**絕對**容差(百萬元;≥1000 大 / ≥100 中 / 其餘小) |
| `v0101 _band` | 一律**相對**誤差 1% / 5% / 10% |

零九頭龍:不寫第三份 → 新增 `XValBridge` **綁正典**,正典缺席才退本地 band,
**並在回傳裡註明 `tol_src`**。`TW02.CrossValidator.validate` 是三源交叉核對正典,同橋綁上。

`ENG024`(格式轉接器安裝)與 `ENG025`(日期窗表格還原)與本引擎的驗證法無關 ——
**不整合**;兩支目前也不在庫,要收容請另下令。

### 操作員規格三條

1. **`to_million_2dp()`** —— 任何單位 → 百萬、固定兩位小數;單位冊優先用 `MDL008` 的
   `UNIT_MULT`(不寫第二份)。不可轉 = `None`,**不當 0**。
2. **補不足能力** —— 即下方第 3 條與 A–M 十三項。
3. **`parse_period()`** 一次收齊:

```
FY-23  FY23  F23  E23  23F  2023  2023F        → year   (+basis A實際/E預估/F預測)
20230102  230102  1141202(民國)  114年         → date / year (roc 旗標)
12/25E                                          → month  2025-12 estimate
1Q25  25Q1  Q1 2025                             → quarter 2025-Q1
```

**期間與基準分開回報** —— 把預估當實際比對就是製造假訊息。

### 驗證

`--selftest` **十二檢 12/12**。放進庫後三橋全接上:

```
NLP 路徑=HUB(VIA_NLP_Application_System_v1.8.0) · 正典 MDL008=在 / TW02=在
```

再拿批425 造的五份真 PDF 實跑:

```
[PASS] 20251204兆豐個股報告-志強-KY(6768)   型別=個股     代號=6768 券商=MEGA    TP=145
[PASS] 20251205兆豐晨會報告-…                型別=大盤晨報  代號=-    券商=MEGA    TP=-
[PASS] GS-2330 20251205                     型別=個股     代號=2330 券商=GOLDMAN TP=1275
[PASS] GS-AI PCB CCL 20251204               型別=未分類    代號=-    券商=GOLDMAN TP=-
[PASS] 華南投顧-2637-慧洋-KY-1141202          型別=個股     代號=2637 券商=HUANAN  TP=78
```

晨會報告判「大盤晨報」不被當失敗;`GS-AI PCB CCL` 判「未分類」——
英文產業名沒有中文關鍵詞,**誠實未分類優於誤判個股**。

### 自審:同一個坑我又踩了兩次

- 檢②⑪ 我用「原始碼裡有沒有這串字」來判,掃到的是**斷言自己寫的那串字**
  —— 批423 `SUP_MDL743` 踩過一模一樣的坑。改用 **AST 看真實呼叫節點**。
- 檢② 我把去連字號的期望值寫成 `"a b c"`,實際應為 `"ab c"`
  (接回被換行斷開的字才是對的)。**是我斷言錯,不是碼錯** → 改斷言。

### 補正批425 的一個漏

當時我把 `ENG074` 的站名猜成「財報頁**表格**十五檢」,冊上實際是「財報頁**擷取**十五檢」
—— 字串不符,`replace` **靜默沒生效**,檢數已加到十六卻還印十五。本批補正。

**教訓:改站名先 grep 真字串,不要憑印象寫。**

## 五十四、批427:報告型別次序修(AI-PCB / AI-CCL)+ 代號↔證券名稱四階梯對帳

操作員令①「AI-PCB AI-CCL 解決後將引擎一個 PY 檔提供給我」;令②(同回合追加)
「台新 BROKER 2317 TICKER 鴻海 股票名稱 可透過 TICKER 去 TWSE TPEX 去找名稱證券名稱抓回來對照
也可以 VDF 系統建立的股票清單每日更新去對帳」。

**檔**:`functional modules/VRN/VIA_VRN_FirstPageEngine_v0103.py`(十四檢 14/14)

### N. 一個症狀,兩個病

`GS-AI PCB CCL 20251204.pdf` 在 v0102 判「未分類」。看起來像「詞冊不夠」一個病,實際是兩個:

| | 病 | 只修這個會怎樣 |
|---|---|---|
| N1 | 主題詞冊缺:`_SECTOR_KW` 只有 產業/類股/族群/策略/展望/sector/industry,PCB/CCL/ABF/CoWoS/HBM/TPU/GPU/供應鏈/半導體 全不認得 | AI-PCB 修好了 |
| N2 | 次序錯:`classify_kind` **先掃型別詞、後才看代號** | 「台新AI伺服器-2317鴻海」會因為含「伺服器」被判成**產業報告** |

只補 N1 = 把一個未分類換成一個誤判,而且是更糟的那種(個股判成產業,下游就不會去要目標價了)。
兩個一起修才算修。重排後的六階,**次序即判準,不可交換**:

1. 強非個股標記(晨報/晨會/盤勢/研討會/論壇)——縱使檔名帶四碼代號也不是個股報告,晨會本來就列一串代號
2. 有四碼代號 = 個股 —— 主題詞不得越過代號
3. 無代號 → 海外 / 法說
4. 無代號 → 主題詞冊(中文用 `in`;英文走**詞界 regex**,否則 `review` 會被 `ev` 命中、`preview` 會被 `ic` 命中)
5. 無代號 → 有界啟發:≥2 個全大寫科技縮寫,扣掉券商/市場/評等停用詞(GS/MS/TT/TW/KY/FY/EPS/BUY…)
6. 未分類(誠實留白)

順手治好第二個誤判:「法說」由強標記**降為弱標記**——`2330法說會報告`**是**個股報告,v0102 判它研討會。

### O. 代號 → 證券名稱四階梯

`TickerFilename.name_hint()` 取檔名裡與代號**相鄰**的公司名:先 `X-KY` 整體,再代號之後,再代號之前;
濾掉券商與「報告/個股/研究/投顧/評等…」通用詞。不濾就會拿「伺服器」去對帳,對出一堆自己造的假紅。
於是 `台新AI伺服器-2317鴻海` → 台新=券商、2317=代號、鴻海=名稱,正是操作員說的那三格。

`NameReconciler` 四階梯,離線優先:

| 階 | 來源 | 落點 |
|---|---|---|
| ① | SSOT `_RAW_SYNONYMS` | 零 I/O |
| ② | **VDF 正典庫**(ENG081 每日更新) | `tw_universe` → `tw_listings` → `tw_listings_industry`,唯讀,**絕不建庫** |
| ③ | `VRN_MDL010_CodeRegistry` 預設冊 | 離線後備 |
| ④ | TWSE / TPEX OpenAPI | **預設關**;要走網路必須操作員自己開妥雙閘 + 自己打 `--web-names` |

比對三層:完全相等 → 包含(慧洋 ⊂ 慧洋-KY)→ **中文縮寫有序子序列**(台積電 ⊂ 台灣積體電路、中鋼 ⊂ 中國鋼鐵)。
第三層設界:短名 ≥2 且全中文、長名 ≥4、**首字必須相同**——首字這一刀擋掉「台泥 vs 台灣化學纖維」這種只共用一個字的偽同名。

誠實三態進總判:`name_match` 閘 MATCH=PASS、MISMATCH=FAIL、**查不到=N/A**。
來源不可得 ≠ 沒問題——這正是批422 假綠的根,不能在這裡重犯。

### 同意閘鐵律

線上階梯預設關。本引擎**全域不存在任何寫環境變數的節點**,檢⑭ 以 AST 掃 `environ[...]` 下標賦值與 `putenv`
證明,**永不代設 `VIA_NET_CONSENT`**;真要出網也是走正典 `SUP_MDL740.http_json`,不自建抓取(零九頭龍)。

> **誠實聲明**:階梯 ④ 的線上實跑在本沙箱**未驗證**——沙箱零同意閘,依治理律不代設。
> ①②③ 皆已實跑。④ 第一次真跑會在工作站、由操作員自己開閘之後。

### 自審實錄:三則都是我的錯,不是碼的錯

1. **`DESCRIBE` 的欄名是 `c[0]` 不是 `c[1]`。** 我初版寫 `c[1]` 收到的是**型別**,於是 `"name"` 永遠不在集合裡
   → 整條庫階梯靜靜空轉,三檔 -KY 全判 UNKNOWN。錯一個索引,一整層樓不亮,而且不報錯。
2. **MDL010 的佔位名。** `resolve()` 對**任何**四碼都 `regex_autofill` 出 `name="TW:2637"` 並回 `ok=True`。
   那是代號的回音不是證券名稱;收下它,慧洋-KY 就會被判 MISMATCH ——**自己造一盞假紅,比查不到還糟**。
   依 `source=="regex_autofill"` 與「名稱是代號回音」雙重擋掉。
3. **我的斷言錯了。** 我在 docstring 寫「包含判抓得到 台積電 ⊂ 台灣積體電路」,實跑打臉(台積電不是連續子字串)。
   補第三層縮寫子序列規則並設界,不是把斷言刪掉了事。

### 落庫實測

沙箱正典庫 `vdf_tw_market.duckdb` 裡**沒有** `tw_universe`、也沒有 `tw_listings`,真正帶 `code`+`name` 的是
`tw_listings_industry`(1978 檔)。只寫 ENG081 的 `UNIVERSE` 表名等於整條階梯空轉——所以三張表都排進去,
有哪張用哪張,誰都沒有就誠實 SKIP。順手把該表的 `industry_name` 帶回來:

```
鴻海=其他電子業 · 慧洋-KY=航運業 · 志強-KY=運動休閒 · 台積電=半導體業
```

這是操作員自己每日更新的官方產業別,比任何關鍵詞啟發都準。

### 五份真報告實跑(全 PASS)

```
[PASS] 20251204兆豐個股報告-志強-KY(6768).pdf   型別=個股    代號=6768 券商=MEGA    TP=145.0  名稱=志強-KY→志強-KY[MATCH/VDF_DB:tw_listings_industry]
[PASS] 20251205兆豐晨會報告-當日新聞與重要訊息評論   型別=大盤晨報 代號=-    券商=MEGA    TP=-      名稱=-→?[NO_TICKER]
[PASS] GS-2330 20251205.pdf                  型別=個股    代號=2330 券商=GOLDMAN TP=1275.0 名稱=-→台積電[NO_HINT/VDF_DB:tw_listings_industry]
[PASS] GS-AI PCB CCL 20251204.pdf            型別=產業    代號=-    券商=GOLDMAN TP=-      名稱=-→?[NO_TICKER]      ← 本批要修的,未分類→產業
[PASS] 華南投顧-2637-慧洋-KY-1141202.pdf        型別=個股    代號=2637 券商=HUANAN  TP=78.0   名稱=慧洋-KY→慧洋-KY[MATCH/VDF_DB:tw_listings_industry]
```

`GS-2330` 檔名沒帶公司名 → `NO_HINT`。這不是錯,只是無從對,所以是 N/A 不是綠。

登錄:Grid v0266(站名「首頁全能引擎十二檢」→「十四檢」)、docs 五十四、台帳 920。

## 五十五、批427b:`--dir` 三病合一 —— 而且第一個病是我給錯路徑

操作員貼回工作站實錄：自測十四檢 14/14 過，但

```
> python "functional modules\VRN\VIA_VRN_FirstPageEngine_v0103.py" --dir "VIA_Reports\incoming"
[絕] 無可處理檔(VIA_Reports\incoming)
```

**檔**：`functional modules/VRN/VIA_VRN_FirstPageEngine_v0104.py`（十六檢 16/16）

### P1 路徑是我憑印象給錯的

正典收件夾**不是** `VIA_Reports/incoming`，是：

```
functional modules/VRN/input_reports      ← 冊 dir_default
functional modules/VRN/input/incoming     ← 冊 incoming(一律併入)
```

冊在 `supportive modules/registry/VIA_InputConsole_Spec_v0100.json` 的 `families.vrn.input`，
MDL139 / MDL141 全走這條。我上一則的一貼即跑沒查冊。

**這是本會期第三次同型錯誤：**

| 批 | 我憑印象寫的 | 冊上真正的 |
|---|---|---|
| 425 | 站名「財報頁**表格**十五檢」 | 「財報頁**擷取**十五檢」（replace 靜默沒生效） |
| 426 | 去連字號期望值 `'a b c'` | `'ab c'`（接回換行斷字才對） |
| 427b | `VIA_Reports\incoming` | `functional modules/VRN/input/incoming` |

三次都是「我以為我記得」。**記得不算證據，grep 才算。**

### P2 三種原因壓成一句話

夾不存在 / 夾是空的 / 夾有檔但副檔名不對 —— 這三件事對操作員的下一步**完全不同**
（換路徑 / 放檔進去 / 看副檔名），v0103 一律回「`[絕] 無可處理檔`」。
操作員看到的是「沒檔案」，真相卻是「夾根本不存在」，下一步全走錯。

> **把不同的失敗壓成同一個訊息，等於把診斷資訊丟掉。**
> 這正是我這幾批一直在修的病（批422 假綠、批425 靜默退後備）出現在我自己的碼裡。

v0104 分三態講，並列出夾內實際有哪些副檔名各幾個：

```
[絕] 找不到可處理的報告檔。以下是**每個夾各自**的真實狀況
     (報告夾律 --dir > user.vrn_dir > 冊 dir_default,incoming 一律併入;來源=冊 VIA_InputConsole_Spec_v0100.json):
   · 夾不存在     …\VIA_Reports\incoming
   · 夾是空的     …\functional modules\VRN\input_reports
   · 夾有檔但沒有報告檔 …\input\incoming   [夾內其他檔:.txt×3、.xlsx×1]
   認的副檔名=.pdf/.docx(大小寫不拘)
   下一步:把報告放進下面這個**正典收件夾**,或用 --dir 指到你真正放報告的夾
     …\functional modules\VRN\input\incoming
```

### P3 副檔名

`glob("*.pdf")` 漏大寫 `.PDF`；而冊上 `extensions` 明明寫 `[".pdf", ".docx"]`，v0103 連 `.docx` 看都不看。
v0104 走 `suffix.lower()`，兩種都收。

### Q. 補 P 的時候當場撞出來的假紅

修完 P 拿混合夾實跑，`台新AI伺服器-2317鴻海.docx` 檔名層**全對**
（台新=券商、2317=代號、鴻海=名稱、對帳 MATCH），卻被判 **FAIL** —— 因為 `target_price` 抽不到。

但 `.docx` 本來就沒有 PDF 文字層。**讀不到 ≠ 抽錯。**

> 這是假紅，和批422 的假綠是**同一枚硬幣的兩面**：
> 證據不可得的時候，燈要給 N/A，不是給顏色。

`run()` 產出 `text_state`；無文字層時文字類的閘
（`target_price` / `tp_sanity` / `zone_presence` / `filename_vs_page` / `historical`）
一律降成 `N/A_NO_TEXT`，而**檔名類的閘照常判** —— 代號、券商、名稱對帳正是 `.docx` 仍然有用的部分，
名稱對不上照樣要紅（檢⑯ 有這組對照）。

順帶修了檢⑩ 的斷言：`--file` 缺值原本斷言 `rc==0`。但旗標打壞卻回成功，
對串鏈的呼叫端就是一句謊（`via-closeout --run` 靠 `rc≠0` 才會誠實停）→ 改斷言 `rc==2` 且訊息說得出原因。

### 實跑（混合夾六件全 PASS）

```
[PASS] 20251204兆豐個股報告-志強-KY(6768).pdf   個股    6768 MEGA    TP=145.0  志強-KY→志強-KY[MATCH/VDF_DB]
[PASS] 20251205兆豐晨會報告-當日新聞與重要訊息評論   大盤晨報  -    MEGA    TP=-      -→?[NO_TICKER]
[PASS] GS-2330 20251205.PDF                  個股    2330 GOLDMAN TP=1275.0 -→台積電[NO_HINT/VDF_DB]    ← 大寫副檔名
[PASS] GS-AI PCB CCL 20251204.pdf            產業    -    GOLDMAN TP=-      -→?[NO_TICKER]
[PASS] 台新AI伺服器-2317鴻海.docx               個股    2317 TAISHIN TP=- 文字層=無 鴻海→鴻海[MATCH/VDF_DB]  ← .docx 走檔名層
[PASS] 華南投顧-2637-慧洋-KY-1141202.pdf        個股    2637 HUANAN  TP=78.0   慧洋-KY→慧洋-KY[MATCH/VDF_DB]
```

登錄：Grid v0267（站名「首頁全能引擎十四檢」→「十六檢」）、docs 五十五、台帳 921。

## 五十六、批428:64 份真報告實測 → 檔名層六修 + 純文字車道 + 四分頁矩陣

操作員把 64 份真報告放進正典收件夾並貼出全部檔名，令
「先拿裡面的報告實測，跳出四頁式，字小一點比較專業，矩陣報告：
1. detailed summary matrix and error matrix　2. basic info　3. financial data」。

**檔**：`functional modules/VRN/VIA_VRN_FirstPageEngine_v0105.py`（十九檢 19/19）
**產出**：`VIA_Reports/vrn/VRN_REPORT_MATRIX.html`（71 KB · 零 CDN · 離線雙擊即開）

### 先不寫碼，先全跑一遍：54 對 10 錯

| | 症狀 | 筆數 |
|---|---|---|
| T1 | `2026` 被當成四碼代號（第一/二/三場全判個股） | 3 |
| T2 | 晨報家族漏字（早報／晨間／解盤） | 3 |
| T3 | 主題詞漏（automation／thermal／hardware） | 4 |
| **T4** | **假紅 ×2**：名稱提示取到分析師、取到評等 | 2 |
| T5 | 券商冊漏（國泰／CLST／GF／JP） | 4 |
| T6 | 底線吃掉 `-KY` | 1 |

### T1:不能用「排除 2000–2030」修

年份與代號在字形上**無法分辨**。排除那個區間會誤殺一整排真代號：

```
2002 中鋼 · 2015 豐興 · 2023 燁輝 · 2027 大成鋼 · 2030 彰源 …
```

整個鋼鐵類股都住在那裡。正解是**拿冊對帳** —— 四碼在 `tw_listings_industry`（1979 檔）上才算代號；
不在冊且落在 1990–2100 就是年份。這正是操作員原令「用 VDF 每日更新的股票清單去對帳」。
庫不可得 → 沿用舊行為但標明「未經庫對帳」，不假裝驗過。

### T4:兩筆假紅，比未分類嚴重得多

```
凱基投顧_2891 中信金_施志鴻_20260519.pdf  → 名稱提示=施志鴻(分析師) → MISMATCH
晶心科(6533,N,中立)-CTBC251208.pdf       → 名稱提示=中立(評等)     → MISMATCH
```

第一筆的根因是「中信金」含券商別名「中信」，被 `broker_of_token` 當成券商濾掉，
名稱提示就落到後面的分析師。修法：**去掉機構後綴（證券／投顧／投信／期貨／證期／研究部）後
「等於」別名才算券商**，單純「含有」不算 —— 中信金 ≠ 中信，它是股票名 2891。

六修後 **64/64 全對**：個股 42 · 大盤晨報 6 · 產業 10 · 海外 3 · 研討會 3；零 MISMATCH、零未分類。

### R. 純文字車道

操作員的 incoming 原本是空的，但庫裡有這 64 份的**全文**（批245 收容語料）。
v0104 只吃 PDF 字元幾何，一份都用不上。`text_state` 由二態擴為三態：

| 態 | 意思 | 能判什麼 |
|---|---|---|
| `OK` | 有字元幾何（PDF） | 版面／分區／字級階層全可判 |
| `TEXT_ONLY` | 只有純文字 | TP／評等／券商／電話／分句照抽，版面幾何類不判 |
| `NO_TEXT` | 兩者皆無 | 文字類的閘一律 N/A |

**三態不可併成二態** —— `TEXT_ONLY` 抽得到的東西遠多於 `NO_TEXT`，併了就是把 64 份真語料的證據丟掉。

### U. 語料一接上就撞到的假綠

```
20251205兆豐晨會報告(二)-公司訪談摘要.pdf  → TP=4441.0  target_price=PASS
```

晨會報告根本不該有目標價。根因：非個股降級只降 FAIL/WARN，**PASS 原封不動**。
→ 一律降 `N/A_NON_STOCK`，並新增 `nonstock_tp_leak=WARN` 把「撈到不該有的東西」講出來。
全庫 5 筆，v0104 全部靜靜給綠。

### V. 全文實跑再挖出三個

**V1 券商被內文的股票名蓋掉。** 台灣金控幾乎全是券商母公司 ——
中信2891 · 元大2885 · 富邦2881 · 統一1216 · 永豐2890 · 第一金2892 · 兆豐2886 · 台新2887 · 華南2880 · 凱基2883。
在整篇文字上掃中文券商別名，命中的多半是內文提到的**股票**：`GS-1590` 判成 KGI、`華南投顧-2762` 判成 TAISHIN，
再拿去跟檔名券商比 → 一整排假紅。改成頁面文字走 strict：中文別名**必須後接機構詞**。

**V1b 更狠的一個。** Daiwa 的全名就叫 **Daiwa Capital Markets**，而 `capital` 是群益的英文別名兼英文常用字
（capital expenditure／working capital）→ `Daiwa-1319` 判成 CAPITAL。
**別名愈短愈常見，愈不能單獨採信** —— 詞界也救不了，只能整個不收或要求它帶機構詞。

**V3 TP 缺席要分兩種。**

| 情況 | 燈 | 意思 |
|---|---|---|
| 文中**有**觸發詞卻抽不到數字 | FAIL | 真的抽取失敗 |
| 文中**一個觸發詞都沒有** | WARN | 這份報告本來就沒有目標價 |

實測 `GS-3706` / `MQ-1560` / 三份華南 Memo，全文 grep 不到 target price／PT／目標價 任何一個。
把「沒有」講成「失敗」，錯誤矩陣就會被不是錯的東西灌滿，**真的錯反而被淹掉**。

### S. 四分頁矩陣

| 頁 | 內容 | 來源 |
|---|---|---|
| ① DETAILED SUMMARY MATRIX | 逐報告 × 全欄位 × 全閘；檔名層與頁面層**分欄** | 引擎本次實跑 |
| ② ERROR MATRIX | 只放紅黃 + 庫側 crosscheck 非 OK 列 | 引擎 + 庫 |
| ③ BASIC INFO | `vrn_report_basic` | 庫 |
| ④ FINANCIAL DATA | `vrn_report_financial` + `vrn_report_metrics` | 庫 |

代號與券商**分成「檔名」「頁面」兩欄** —— 兩者不一致正是 `filename_vs_page` 這盞燈在講的事，
擠成一欄就看不出是哪一邊抓錯。

分頁用 `<input type=radio>` + CSS 同層選擇器，**零 JS 框架、零 CDN**，離線雙擊即開。
字級沿用 ENG072 房規（10.5px）再收一級（表格 9px）—— 操作員要的「小一點比較專業」是這個尺度，不是另立一套視覺。

庫不可得 → **印出為何，不印一張空表讓人以為「跑過了沒資料」**。
①② 的引擎側是本次實跑，②下半與③④ 是庫側（先前 ENG073/ENG074 入庫成果），來源不同、時點不同，分開標明不混一鍋。

### 自審:FAIL 從 14 降到 0,是不是靠放寬斷言換來的?

**不是。** 逐條核：

- V1／V1b 移除的是**真的誤判**（頁面券商本來就抓錯）
- V2 檔名自己寫著 `NR_未評等`
- V3 是**紅轉黃，不是消失**

25 個異常格**全都還在錯誤矩陣裡**，總判 43 PASS / 21 WARN，而且多出 5 盞 `nonstock_tp_leak`
是 v0104 原本給綠的新發現。沒有任何一格被藏起來。

### 自審三則:又是我的斷言錯

1. **檢⑪ 因 `--report` 落檔而紅。** 產四分頁是正當產出 —— 但「允許落檔」不等於「不用管」，
   改成**指名唯一落檔者**（只有 `run_cli` 可寫，寫的是已 gitignore 的 `VIA_Reports`），多一個函式會寫就要紅。
2. **檢⑯ 的 fixture 沒寫 `tp_trigger_seen`**，V3 上線後測到的是 V3 分支而不是 ⑯ 本身 —— 斷言要指名它在測什麼。
3. **檢⑱ 我斷言寬鬆模式回 CTBC**，實際回 YUANTA（元大在中信之前）—— 綁死某一家等於在測字典順序，不是測行為。

登錄：Grid v0268（站名「首頁全能引擎十六檢」→「十九檢」，逾時 180→240）、docs 五十六、台帳 922。

## 五十七、批429:工作站真 PDF 實跑 —— 四病一根

操作員拿 64 份**真 PDF**（不是文字語料）跑 v0105，貼回全表。錯得有系統。

**檔**：`functional modules/VRN/VIA_VRN_FirstPageEngine_v0106.py`（二十一檢 21/21）
**新件**：`functional modules/VRN/VRN_TWRoster_Offline_v0100.json`（1978 檔離線代號冊）

### W1　TP 抽到的是代號本身

```
泓德能源(6873) → TP=6873    神達(3706) → TP=3706    望隼(4771) → TP=4771
```

根因：`extract_target_price` 取**第一個**命中就回，不排序不過濾。
改成候選評分 —— 五道剔除 + 四級排序：

| 剔除 | 例 | 64 份命中 |
|---|---|---|
| 等於本檔代號 = 代號回音 | `目標價 6873` | 1 |
| 括號內緊接中文公司名 | `某某(4441)` | 1 |
| 八碼日期形狀 | `20251204` | 1 |
| 四碼年份且無貨幣無小數 | `2026` | 4 |
| 數字後接量級後綴 | `NT$48.5**bn**` | **42** |
| 前綴「前次」 | `前次…目標價125 元` | 8 |

排序：**來源（觸發詞 > 裸 NT$）→ 貨幣符號 → 小數 → 出現位置**。

> **自審：初版把裸 `NT$` 的底分排在觸發詞之上，比不修還爛。**
> 志強-KY 145→125、GS-2317 844→2.4、儒鴻 367→1.0。
> 「目標價」旁邊的數字是強證據；`NT$` 在報告裡到處都是，是弱證據。
> **來源權重必須壓過貨幣加分，不能讓加分翻轉來源。** 做了前後對照才抓到。

另兩條規則也是對照跑出來的：`GS-2317` 的 2.4 是 `NT$2.4trillion`、`MS-Thermal` 的 48.5 是 `NT$48.5bn`
—— 外資報告的裸 NT$ 車道撈到的多半是**營收**。而志強-KY 的 125 是「**前次** 投資建議 2025.08.06: 目標價125 元」，
現在是 145 —— 而且 14 字的前綴窗看不到「前次」（距離約 20 字），窗要開到 28。

### W2　TP 量級離譜卻沒人擋

```
奇鋐 TP=1780 · 中信金 TP=1.0 · 健策 TP=2.0 · MS-Thermal TP=14503 / 17382
```

TP 合理性閘（0.2–5.0）要**現價**才能判，而現價來自庫 —— 庫不在，閘就睡著了。
→ 加一道**不需要現價**的台股幣別合理帶 1–5000 元。這是合理性不是精準驗證，所以給黃燈並標明，不是紅也不是靜音。

### W3　非個股報告從內文亂撈代號

```
晨會報告 代號=1163 / 4441 · MS-Thermal 代號=3017 · UBS-Asia 代號=8722 · 投資早報 代號=2325
```

**產業報告提到 3017 奇鋐，不會使它變成一份 3017 的報告。**
→ 非個股型別一律把內文四碼移到「內文提及」，`ticker` 留空。

### W4　一個缺件同時廢掉三個能力 ← 這是根

```
庫不在:...\functional modules\VDF\output_hub\mega\vdf_tw_market.duckdb
```

操作員的 OneDrive 副本沒有那個 DuckDB。庫一不在：

| 廢掉的能力 | 後果 |
|---|---|
| 代號冊空 | `is_valid_bare` 無冊可對 → 內文四碼全收（W3 更嚴重） |
| 名稱對帳 | 64 份全 UNKNOWN，只有 4 份靠 MDL010 僥倖命中 |
| TP 合理性閘 | 拿不到現價 → 睡著（W2 無人擋） |

→ 新增離線代號冊 `VRN_TWRoster_Offline_v0100.json`（1978 檔，由庫快照，帶 `asof` 與來源）。
**這不是第二份實作，是同一份事實的副本**；階梯 `庫 → 離線冊 → MDL010`，庫在時仍以庫為準。
實測庫不在時：roster 退離線冊 1978 檔、`6873 → 泓德能源 MATCH/OFFLINE`。

### X　版面（操作員令「自小一點 · 矩陣格式自動最佳化 · 堆疊矩陣 · 擷取結果驗證」）

- **字級再收一級**：基底 10.5→9.5px、表格 9→8.5px、頁首 13→12px
- **欄寬自動最佳化**：掃該欄**實際內容**長度定寬（中日韓字寬算兩倍），短欄 `nowrap`、數字右對齊。
  v0105 讓瀏覽器平均分欄，「代號」「燈」這種四字欄被撐得跟「為何」一樣寬，長文欄反而被擠到換行。
- **⑤ 堆疊矩陣**：同一份報告的證據堆在一起。橫表看不出「檔名說 A、頁面說 B」，堆疊才看得出來；每張卡帶燈號比例條。
- **⑥ 擷取結果驗證**：每個 TP 候選的 值／來源／貨幣／小數／分數／採用與否／為何，全部攤開。
  這一頁回答的是**「你憑什麼說目標價是這個數字」**。

### 驗證

二十一檢 21/21。64 份語料實跑產出 236 KB 六分頁，**外部連結 0 個、腳本 0 個**，64 張堆疊卡、171 列擷取驗證。

### 自審

檢⑳ 的 fixture 一開始造不出代號回音 —— 庫裡那份 `.txt` 寫的是「同步下修目標價至208 元」（正確），
是操作員**真 PDF 的版面**把代號排到「目標價」旁邊才出事。我看不到他的 PDF，
只能照症狀把那個**形狀**造出來測，並在碼裡標明「依工作站症狀重建，造的是形狀不是結論」。

另：f-string 運算式不得含反斜線（Py3.11）又踩一次。

登錄：Grid v0269（站名「十九檢」→「二十一檢」，逾時 240→300）、docs 五十七、台帳 923。

## 五十八、批430:百分比不是價格 + 開頁旗標 + 另庫勘查

**檔**：`functional modules/VRN/VIA_VRN_FirstPageEngine_v0107.py`（二十二檢 22/22）

### Y1　TP 抽到的是百分比／倍數

v0106 工作站實跑：`志強-KY TP=23.0` —— 而報告寫的是「潛在上漲空間 **23%**」。
泓德能源 22.7、神達 41.9 同型（上漲空間／報酬率）。

根因：`_TP` 的 `[^\d\-]{0,20}` 會**跨過**「潛在上漲空間」這種詞，去撈後面的數字。

三道新剔除：

| 剔除 | 例 |
|---|---|
| 數字後接 `%` / `％` / `ppts` | `潛在上漲空間 23%` |
| 數字後接 `x` / `倍` / `PER` | `13x 2026(F)PER`（本益比倍數） |
| 觸發詞與數字之間夾著「上漲空間／報酬率／殖利率／漲幅」 | `目標價 潛在上漲空間 23%` |

修後：**泓德能源 208 · 神達 128 · 志強-KY 145** —— 與報告原文一致。

### Y2　沒有自動跳出報告

治理律是**零彈窗**（批340：引擎不得自作主張開視窗），所以 v0106 產完只印路徑。
→ 加 `--open`：操作員明打就是他要開，那不是自作主張。
若殼裡 `VIA_NO_OPEN=1`（短指令梭一律設）照樣不開 —— 那是他自己的閘，不代解；
但要把「為何沒開、怎麼改」講清楚，**不是靜靜不動作讓人以為壞了**。

### Y3　另庫勘查（操作員令：看 `tonykuni/VIA-VDF-VRN`，需要就複製來用）

掛進來跑 `npm run test:vrn` → **36/36 全綠**。但操作員說「他也還沒成功」。

```js
// src/lib/via/nlp-extract.ts:109
grab("K1", /(?:目標價|潛在上漲|評價方式)[:：]\s*(.+)/);
```

**把「目標價」和「潛在上漲」當成同一個欄位** —— 正是本批 Y1 修掉的那個病。
而且要求觸發詞後**緊接冒號**，真報告多半寫「目標價145」沒有冒號，直接抽不到。

所以那 36/36 是跑在**有冒號的 fixture** 上，不是跑在操作員的 64 份真報告上 ——
**又一次「測試全綠但系統沒在動」。**

> **結論：沒有可複製進來的東西，本引擎的抽取層比它前面。** 誠實回報，不硬抄也不客套。

### 自審

檢㉒ 第一版斷言又錯：我拿「目標價145…潛在上漲空間23%」去驗百分比剔除，
但那句裡的「23%」前面**根本沒有觸發詞**，壓根不會成為候選，自然沒有剔除理由。
三道剔除要各自用**會產生該候選**的句子（`PT 23%` / `目標價 13x 2026` / `目標價 潛在上漲空間 23%`）去驗
—— 斷言要指名它在測什麼。

登錄：Grid v0270（站名「二十一檢」→「二十二檢」）、docs 五十八、台帳 924。

## 五十九、批431:兩邊都修 —— 母庫文內自洽 + 另庫候選評分移植

操作員令「繼續幫兩邊都修正完」，續令「因為過了除權息所有股價資料都用 adj 價格」。

### 母庫:先講兩條走不通的路,以及為什麼不做

殘留問題是 TP 量級可疑（奇鋐 1780 · 中信金 1.0 · MS-3661 4388 · 貿聯 2600），要判準需要現價。

| 路 | 試了什麼 | 結果 |
|---|---|---|
| ① 離線收盤快照 | 從庫導出 **865 檔成功** | 但 3017/2891/3661/3665/2330/6768 **一檔都不在裡面** —— 庫裡那張 `tw_trading_daily` 是 4 天 889 檔的局部測試資料 |
| ② 文內現價 | 掃 64 份語料 | 只有 1 份疑似帶現價，而那個「股價10」其實是「評價位於股價10-11x」的本益比 |

> 出一個**對所有相關個股都查不到**的檔案是**假能力**：看起來有用，閘照樣睡著。
> 已產出、已驗證、**已刪除**。

### 能做的第三條:文內自洽

報告若同時寫了目標價與上漲空間，兩者互相隱含一個價：`隱含價 = TP ÷ (1 + 上漲空間%)`。

```
志強-KY:145 ÷ 1.23 = 117.89   而報告原文收盤價 118.00 —— 對得上
```

> **但我寫規格時預測它會抓到 `GS-2383`（6000 ÷ 1.32 = 4545），實跑打臉。**
> 4545 落在合理帶內判 PASS，而且 4545 在台股並非不可能（大立光曾站上 6000）。
> 這個檢查證明的是**文內一致，不是外部正確** —— 目標價與上漲空間若是**一起**被抽錯，它們仍然自洽。
> 它能抓的是**粗錯**：`TP=1.0` 配上漲空間 20% ⇒ 隱含 0.83，低於合理帶。
> **預測錯了就改寫規格，不改斷言去遷就預測。**

覆蓋率誠實講：64 份裡只有 7 份同時有這兩個數。

### adj / raw 分野(操作員新令)

隱含價是**報告日的原始價（raw）**，不是復權價、不是今天的價。
VDF 側一律 adj，兩者差一個除權息因子，**不可直接相比**；要比必須先經 ENG080 除權息調整（批386/425）。
已在碼與回傳鍵（`implied_price_basis = RAW_AT_REPORT_DATE`）標死。

### 另庫 `tonykuni/VIA-VDF-VRN`

查出 `first-page.ts` 的 `FPE_VER = "v0103"` —— **那整支就是本引擎 v0103 的 TypeScript 移植**，
所以帶著一模一樣的病（取第一個命中就回、把 `NT$` 當觸發詞）。
`digest-four.ts` 只是轉呼叫它，**一個修點就夠**。

- 把候選評分六道剔除 + 四級排序移植成 TS
- 另修 `nlp-extract.ts:109`：把「目標價」與「潛在上漲」拆開、冒號改可選
- 新增 `first-page-tp.test.ts` 8 例，每例都由真報告實測帶出來
  —— 含「來源權重壓過貨幣加分」那條，那是母庫初版踩過的坑

實測：新測 8/8、他們原有 `test:vrn` 36/36、`talib`+`digest-four` 8/8，**零回歸**。
（`tsc --noEmit` 的錯是 `node_modules` 沒裝造成的缺 `@types/node`，與改動無關。）

分支：`claude/vrn-tp-candidate-scoring`（已推，未開 PR —— 開不開由操作員決定）。

登錄：Grid v0271（站名「二十二檢」→「二十三檢」，逾時 300→320）、docs 五十九、台帳 925。

## 六十、批432:雙方檔案互取除錯法

操作員令「雙方檔案中找除錯的方法」。兩邊各有對方缺的東西。

| | 有什麼 | 缺什麼 |
|---|---|---|
| `via-vdf-vrn` | `fin-audit.ts`：「**一列必須是原子事實。P 級不得掛綠**」—— 證據分級 | 逐候選 trace、真報告語料 |
| 母庫 | 逐候選 trace、64 份真報告 | 證據分級 —— TP 只有「有值/沒值」 |

### 他們 → 我:證據等級 V/M/P

我這邊 TP **沒人問它證據多強**，於是 `中信金 TP=1.0`、`Daiwa-3653 TP=2.0` 這種孤證照樣掛 PASS。

| 級 | 條件 | 燈 |
|---|---|---|
| V 已驗 | 觸發詞命中 **且** 帶貨幣記號 | PASS |
| M 提及 | 觸發詞命中但無貨幣記號 | WARN |
| P 推定 | 只有裸 `NT$` 孤證 | WARN，且 `target_price` 一併降級 —— **不得掛綠** |

> **自審：初版只罰衝突不賞佐證。**
> 志強-KY 的 145 被**三個候選同時命中**、又通過文內自洽，卻只給 M ——
> **只罰不賞的分級會把對的東西一起壓低，那也是一種不誠實。**
> 補上：同值多次命中升一級、文內自洽通過再升一級、不同值打架降一級。

64 份語料分佈：**V 14 / M 16 / P 2**。

### 我 → 他們:逐候選稽核

`--trace <關鍵字>` 把候選表印到主控台。

> **我看不到操作員的 PDF，就修不了我看不見的東西。**
> 給他一個能把現場拍給我看的工具，比我在這邊猜十次有用。

反向也送過去：他們那邊補 `tpGrade()` 與 `tpAudit()`，`fpeQc()` 加 `FP_TP_ECHO`（代號回音）與 `FP_TP_GRADE`（P 級孤證）兩盞燈。

### AA1 每跑必噴的警告

```
SyntaxWarning: invalid escape sequence '\d'
```

模組 docstring 裡引用了正則 `[^\d\-]{0,20}`，而 docstring 不是 raw string。改 raw 即解。
不是大病，但**每跑必噴的警告會訓練人忽略警告**，那才是大病。

（改的時候我在說明裡寫了三引號，把 docstring 自己終止，當場把檔案寫壞一次。）

### AA4 神達新回歸 —— 誠實記錄,不硬改

工作站 v0108 實跑：神達 TP 從 128 變成 **119715**，而 **`tp_self_consistency` FAIL 抓到了**
（119715 ÷ 1.419 = 84,365 荒謬）—— 批431 那道文內自洽閘在真 PDF 上第一次證明自己有用。

但我看不到他的 PDF 文字層，無從得知 119715 從哪來。**在拿到 trace 之前不猜、不硬改。**
閘已經把它擋在綠燈外，這是誠實的中間狀態。

### 自審二:斷言裡的 `or True`

檢㉔ 初版尾巴寫成 `... or True`，**整條變空洞** ——
我抓了一整個會期的空洞斷言，結果自己在同一分鐘內寫了一個。

拿掉之後它**真的紅了**，才發現第二個錯：`目標價 145 元 · 目標價 999 元` 帶著「元」，
起點是 **V** 不是 M，打架降一級到 **M**。降級規則沒錯，是我算錯起點（本會期第四次斷言錯）。

登錄：Grid v0272（站名「二十三檢」→「二十四檢」，逾時 320→340）、docs 六十、台帳 926。

## 六十一、批433:trace 把答案送回來了

操作員跑批432 的 `--trace 神達`，候選表直接把答案送回來 —— 這就是那個旗標存在的理由。

```
     41.9  觸發詞 Y Y  225.0  剔(上漲空間)
  119,715  觸發詞 Y -  220.0  留 ← 被採用
     3706  觸發詞 - -  200.0  剔(代號回音)
       78  觸發詞 - -  200.0  留 ← 真正的目標價
```

`78 ÷ 1.419 = 54.97` —— 神達當時就在 55 上下，完全合理。

### AB1 排序權重又錯一層

**119,715 贏在哪？它多了一個貨幣記號（+20 分）就贏了 78。**

根因：我把「帶貨幣記號」排在「落在合理股價帶」之上。但**六位數帶千分位的數字不是股價**
—— 那是營收／市值，而且這個訊號比有沒有一個「元」字強得多。

> 批429 我修過一次排序權重（**來源 > 貨幣**），這是同一課的第二層：**合理性 > 貨幣記號**。

合理帶進評分：帶內 `+40`、帶外 `−60`。

| 候選 | 舊分 | 新分 |
|---|---|---|
| 119,715 | 220 | 220 − 60 = **160** |
| 78 | 200 | 200 + 40 = **240** ← 勝 |

### AB2 台股目標價的下界不是 1 元

`中信金 TP=1.0`（實際約 45）、`Daiwa-3653 TP=2.0`（健策數百）—— 兩者都落在舊帶 `[1, 5000]` 之內，**連黃燈都沒有**。

券商報告給出低於 5 元的目標價極罕見（那個價位是全額交割股，而那種股票不會有目標價報告）。
→ 下界 `1 → 5`。**這是提醒不是判死**：低於 5 元的目標價確實存在，所以給黃燈要人看一眼。

### 誠實邊界

- **AB1 是真修好了** —— 有 trace 為證，78 是可驗證的正解。
- **AB2 只是把可疑的標出來** —— 我仍然沒有現價，判不了 1780／4388／2600 誰對誰錯。

### 回歸驗證

64 份語料上 **TP 零筆變動** —— 那個病只在操作員真 PDF 的文字層出現，代表這是針對性修正、沒有誤傷。
分級分佈維持 **V 14 / M 16 / P 2**。

### 兩邊同步

另庫 `first-page.ts` 同步同一修正，`FPE_VER v0108→v0110`，新增兩例測試。
`first-page-tp.test.ts` 12/12、`test:vrn` 36/36、`talib` 3/3。

> 更正：前次台帳寫「talib 8/8」是把 `talib` + `digest-four` 合計算成一支，分開跑是 3 + 5。

登錄：Grid v0273（站名「二十四檢」→「二十五檢」，逾時 340→360）、docs 六十一、台帳 927。

## 六十二、批434:黃燈太多,其中一半是我自己造的

操作員問「可以在妳那一端自測字修正到全部成功嗎」。

誠實盤點：64 份裡 **49 個非綠燈格，約半數是我自己過度標記** —— 那些我修；剩下的是真的，不硬壓成綠。

### AC1 我把他們的律套過頭了

`fin-audit.ts` 寫的是「一列必須是原子事實。**P 級**不得掛綠」—— **只講 P**。

我批432 移植時讓 **M 級也掛黃**（18 格裡 16 格是 M），於是：

```
MS-2308  TP=1288   乾淨抽取 → 被拉黃
JP-2330  TP=1275   乾淨抽取 → 被拉黃
```

只因為數字旁邊沒有「元」字。而**英文報告本來就不會寫「元」** —— 用貨幣記號當必要條件是中文報告偏見。

→ M 級 `tp_evidence` 回 PASS（等級仍原樣寫進 `tp_grade` 與矩陣，**資訊不消失**）；只有 P 級才 WARN。
**照他們寫的那句話辦，不加碼。**

### AC2 非個股沒有資訊區

`zone_presence` 檢查的是「目標價／評等／券商」三件套有沒有出現在本文分句裡。
晨報／海外／研討會**本來就沒有這三件套** —— 拿它來判等於問一份晨報「你的目標價段落呢」。

→ 非個股一律 `N/A_NON_STOCK`，與 `target_price` 同律。**個股照判，不一起放水**（檢㉖ 有這組對照）。

### AC3 更正我自己說錯的話

我上一則說「奇鋐 TP=1780 可疑」。操作員跑 `--trace 奇鋐`：

```
   1,780  觸發詞 Y -  260.0  留
1,780.00  觸發詞 - Y  245.0  留      ← 同一個數字寫了兩次
    2026  觸發詞 - -  240.0  剔(年份)
```

報告裡**只有 1,780 這一個數字**，寫了兩次、帶貨幣記號、等級 V，而奇鋐 2025 年本來就在千元以上。

> **1780 是對的，是我的懷疑沒有根據。**
> trace 不只用來抓錯，也用來洗刷冤枉 —— 這次它洗掉的是我自己造的懷疑。

### 成效與誠實邊界

**PASS 25 → 47 · 非綠格 49 → 25。**

剩下 25 格逐一核過，**全是真的**：

| 成因 | 格 | 是不是真的 |
|---|---|---|
| `target_price` 文中無目標價觸發詞 | 15 | 真 —— 那些報告確實沒有目標價 |
| `zone_presence` 個股但資訊區要素不在本文 | 4 | 真 |
| `tp_twd_band` 中信金 1.0、Daiwa-3653 2.0 | 2 | 真 |
| `tp_evidence` P 級孤證 | 2 | 真 |
| `nonstock_tp_leak` 非個股卻抽到目標價 | 2 | 真 |

> **這 25 格不壓成綠。** 操作員問的是「修到全部成功」，
> 而正確的答案是「**把我自己造的黃燈修掉，真的黃燈留著**」。

### 兩邊同步

另庫加 `tpEvidenceLight()`（只有 P 拉燈），`FPE_VER v0110→v0111`；13/13 + 36/36 零回歸。

登錄：Grid v0274（站名「二十五檢」→「二十六檢」，逾時 360→380）、docs 六十二、台帳 928。

## 六十三、批435:多工具核對的本文 —— 但那東西早就造好了

操作員令：「另外一邊有最新的 NLP 引擎／LAYOUT 引擎，將第一頁真正的內容相關本文及表格
（不含底部小字體頁尾），多工具核對，至少兩種解取工具還原文字及表格後是一致的，先看驗證後的本文」。

### 先查再造:`VRN_ENG072 v0107` 已經有了

| | 方法 |
|---|---|
| 法A | `fitz` 分區 —— 標題帶／左本文／右資訊區／**頁尾帶（底 8% 當雜訊）** |
| 法B | `pdfplumber` words 同判準分區 + `extract_tables` 表格還原 |
| 法C | `GenericLayoutEngine v2.1.0` —— 九宮分區 + 字重階層 + 本文字級推定 |
| 句級 | NLP `OneEngine TextProcessor`（帶 `ssot_lexicon`）修復後再 `split_sentences` |

`compare_zones` 逐區 difflib：**≥0.90 AGREE ／ ≥0.60 PARTIAL ／ 低 DIVERGE**。
產物就在 `VIA_Reports/first_page_text/<檔名>.json`。

### 那我這支引擎在幹嘛 —— 它自己又判了一次版面

本引擎從 v0101 起用自己的 `_pdf_chars` + `Layout` 判版面，**完全沒去讀 sidecar**。
同一份 PDF 被判兩次版面，而且**下游用的是沒有經過雙法核對的那一份**。

> 這是我造出來的重複，也是操作員這次問題的真正答案：
> **不是「要做多工具核對」，是「已經做了，但我沒接」。**

→ 新增 `SidecarBridge`：有 sidecar 就用驗證後的本文，沒有就退回自判並在 `text_source` 寫明走哪條。

| `text_consensus` | 燈 |
|---|---|
| AGREE | PASS |
| PARTIAL | WARN |
| **DIVERGE** | **FAIL** |
| 無 sidecar | `N/A_NO_SIDECAR` |

**DIVERGE 判紅不判黃**：兩個獨立工具對同一頁讀出不同的字，那不是「有點疑慮」，
是**下游拿到的字可能根本不是報告寫的**。

`verified()` 在 DIVERGE 時仍把本文給出來供人看，但 state 已標明不可信 ——
**不挑一份給下游當真**，回哪一份都是在猜。

### 先看驗證後的本文

```
python … --dir --body 2330

── GS-2330 20251205.pdf
   核對=AGREE 相似度=1.0 工具=fitz+pdfplumber+GLE+NLP句級
   來源=ENG072 sidecar(AGREE;fitz+pdfplumber+GLE+NLP句級)
   ┌─ 本文(不含頁尾小字) ──────────────────────────────
   │ Goldman Sachs Equity Research TSMC (2330 TT) Buy
   │ 12-month target price: NT$1,275 Last close: NT$1,130.0
   └──────────────────────────────────────────────────
```

登錄：Grid v0275（站名「二十六檢」→「二十七檢」，逾時 380→400）、docs 六十三、台帳 929。

## 六十四、批436:文件結構層——一標題 一句話 一資料分類

操作員把整份規格一次講完:「接斷句直到句號(標題沒有句號字體較大或粗)去空格 TRIM
過後……一標題 一句話 一資料分類 REPORT DATE / FILENAME / BROKER / CATEGORY(表圖文) /
TYPE……有時候表頭的第一個位置沒有填任何資料也把它暫時填一個資料如 item 才容易把他還原」。

這不是一條需求,是一份文件模型。`DocStructure`(v0113)逐條實作。

### 零九頭龍:字級字重不自己再偵測一次

批435 才剛因為「自己又判一次版面」被抓到重複。所以這一層**不碰字級偵測**——
`ENG072` 的 `gle_annotate` 每塊都已經給了 size / bold / zone 與 `body_font`,
本層只吃它算比例。sidecar 不在才退回純文字弱啟發,而且要在輸出裡標明:

```
階層來源=gle.elements(5 塊,本文字級 12.0)
階層來源=純文字弱啟發(無 gle;字級不可得)
```

### 最大最粗有兩種,用「有沒有代號」分開

操作員的規格裡,「股票名稱及代號」與「文章主題」**同為最大最粗**——
字體本身分不開它們。分開的訊號是這一行有沒有四碼代號/公司名:

| 條件 | 階層 |
|---|---|
| ≥1.60 倍本文字級 且粗 且**有代號** | `TICKER_NAME` |
| ≥1.60 倍本文字級 且粗 且**無代號** | `SUBJECT`(文章主題,一句話) |
| ≥1.60 / ≥1.35 / ≥1.15 | `H1` / `H2` / `H3` |
| <0.85 | `FOOTER`(頁尾不相關小字) |
| 附錄/免責/Analyst Certification 之後 | `APPENDIX` |

邊界(1.60 / 1.35 / 1.15 / 0.85)寫成類常數,不散在判斷式裡。

### 標題沒有句號,所以標題不參與接句

`join_body()` 把本文一路接到句號為止(`。．.!！?？;；`),TRIM 後再接。
標題自成一列,遇到標題先把**沒收尾的句子吐出來**再放標題:

```
輸入 H2 合併損益表 / BODY 本季營收 / BODY 成長 12%。 / BODY 毛利率下滑 / H3 風險 / BODY 匯率波動。
輸出 H2 合併損益表 · BODY 本季營收 成長 12%。 · BODY 毛利率下滑 · H3 風險 · BODY 匯率波動。
```

寫檢 ㉘ 的斷言時我把「毛利率下滑」排在「風險」之後——**本會期第五次斷言寫錯**。
碼的次序是對的:緩衝在標題**之前**沖出。已在碼裡留註記。

### 表被誤判成文字時的還原

操作員指認了兩個訊號,一個坑:

- 訊號一:一行連續出現 **≥3 個期間樣式**(`2024 2025F 2026F` / `1Q25 2Q25`)→ 那是表頭,也可能是第一欄
- 訊號二:一行有 **≥2 個可對齊的數字**(兩個以上空白隔開)→ 資料列
- 坑:**表頭第一格空著**(首欄標題整格沒填)→ 少一格整列就對不齊

```
還原前   "          2024    2025F   2026F"
還原後   表頭 | item | 2024 | 2025F | 2026F
              | 營業收入 | 41,430 | 52,180 | 61,900
why=表頭第一格空著(首格就是期間)→ 補 item 才對得齊欄位
```

判斷「首格空著」用的是 `_PERIOD.fullmatch(hdr[0])`——**第一格本身就是期間**,
就代表首欄標題那一格是空的。補 `item` 之後 header 與 rows 再補齊到同寬。

### 財報表分類綁 SSOT,缺的補同義字

操作員令「損益表 資產負債表 現金流量表 比率分析 評價分析……相關的統一制參考 SSOT
若有新的把它補足同義字」。`vrn_finlex_v0104.py` 的 `STMT_ZH` 有
BALANCE_SHEET / INCOME_STATEMENT / CASH_FLOW / EQUITY_CHANGE / RATIO / PER_SHARE / NOTES,
**沒有評價分析**。所以綁既有的冊,只補缺的那一個,並把補了什麼印出來:

```
財報表冊=綁 vrn_finlex_v0104.py;補同義字 ['VALUATION'](冊上原本沒有)
```

不在 finlex 裡改冊——正本零觸碰;補的那一條掛在引擎側,冊上哪天自己有了就自動讓位
(`base` 已有的鍵不覆蓋)。

### 一標題 一句話 一資料分類

`rows()` 把每一列做成一筆原子事實,欄位就是操作員點名的那幾個:

| 欄 | 來源 |
|---|---|
| `REPORT_DATE` | 報告日 |
| `FILENAME` | 檔名 |
| `BROKER` | 券商 |
| `CATEGORY` | **表 / 圖 / 文**——表圖題之後的列繼承該題的分類 |
| `TYPE` | 字體階層(`TICKER_NAME`…`APPENDIX`) |
| `TEXT` | TRIM 後的那一句 |
| `CAPTION_NO` / `CAPTION_DESC` | 表號/圖號:說明 |
| `SOURCE` | 資料來源(表/圖的來源資訊) |
| `STMT` / `STMT_ZH` / `STMT_HIT` | 財報表冊命中的鍵、中文、命中的同義字 |

### 實跑

```
python … --dir <報告夾> --struct 志強

階層來源=gle.elements(5 塊,本文字級 12.0)
財報表冊=綁 vrn_finlex_v0104.py;補同義字 ['VALUATION'](冊上原本沒有)
H3   文   -   兆豐證券投顧  個股研究報告
H3   文   -   志強-KY(6768 TT)  買進
BODY 文   -   目標價:145 元    現價:118.0 元

«表 3：合併損益表» 題=表3 財報表=損益表 · «評價分析» 財報表=評價分析 · «資產負債表摘要» 財報表=資產負債表
```

`--struct` 要 sidecar 才有字級階層。工作站要先跑一次
`python "functional modules\VRN\VRN_ENG072_FirstPageText_v0107.py" run`
產生 `VIA_Reports/first_page_text/*.json`,`--body` 與 `--struct` 才吃得到。

登錄:引擎 v0112→v0113(二十七檢→二十八檢)、Grid v0276(站名「首頁全能引擎二十八檢(批436)」,逾時 400→420)、docs 六十四、台帳 930。

## 六十五、批437:三包裡沒有新引擎——文內自洽升格為仲裁

操作員丟了三包上來(`VIA_NLP_v1.6.1`、`VIA_Discussion_Reconstruction_Package`、
`VIA_NLP_Application_System_v1.8.0`),外加工作站的 `--struct` 實錄,說「三個引擎協助」。

先查再造。查出來的結論跟預期相反。

### 三包裡沒有一支庫內沒有的引擎碼

| 包 | 實況 |
|---|---|
| `VIA_NLP_Application_System_v1.8.0` | 與庫內 `references/intake/` 那份**逐檔相同**(只差 `__pycache__`) |
| `VIA_NLP_v1.6.1` | OneEngine 37 模組,是 v1.8.0 那 41 模組的**舊版子集** |
| `VIA_Discussion_Reconstruction_Package` | 76 MB,全是 JSON 資料,不是引擎 |

缺的從來不是碼,是**呼叫**。這是批435 那一課的第三次。

而且——庫裡本來就躺著那 64 份報告的**第二份取字**:

```
functional modules/VRN/references/intake/AttachmentFixedOutput_v1.0.0_b245/
  AttachmentFixedOutput_v1.0.0/01_repair/documents/*.txt     ← 64 份,全文
```

`VRNTextRepairEngine 1.0.0` 產的,`four_engine_manifest.json` 記著 run_id、sha256、64 records。
我整個批432 到批436 都在跟操作員要「`--trace` 貼回來」,而東西在庫裡。
批432 我自己寫過一句「我看不見操作員的 PDF 就修不了看不見的東西」——那句話當時就不成立。

### A1 文內自洽:從「驗證」升格為「仲裁」

批431 造了文內自洽,但只拿來**選完之後驗證**——選錯了它只會說「這個數字算不通」。
真正能決勝的用法是**排序時仲裁**:

> 報告自陳上漲空間時,目標價 ÷ (1 + 空間) 必須等於同頁的現價。

批429 學到「來源 > 貨幣記號」,批433 學到「合理帶 > 貨幣記號」,這是同一課的第三層:
**自洽 > 觸發詞**。加分 150,壓得過「觸發詞 200 對裸 NT$ 100」的來源落差。

實據兩則,都來自庫內第二取字:

```
CLST-6669   報告寫「12M price target NT$4,200.00 ±% potential +27%」
            4,200 ÷ 1.27 = 3,307 ≈ 同頁 3,300  ✓
            而 3,300 是現價、3,425 是 52 週高、3,600 是「from NT$3,600 to NT$4,200」的 A

中信金2891  報告寫「12 個月目標價 (NT$) 63.00 / 前次 59.00 / 調升 6.7% / 上漲空間 13.7%」
            63 ÷ 1.137 = 55.41 ≈ 自陳收盤價 55.40  ✓
            63 ÷ 59 = 1.0678 ⇒ 調升 6.7%           ✓  兩條算式同時吻合
```

庫內 64 份有 12 份發動仲裁,每一份的隱含價都對上報告自陳的收盤價,誤差 <0.3%。

上漲空間有三種寫法,舊式只認一種:

| 寫法 | 出處 | 舊式 |
|---|---|---|
| `潛在上漲空間23%` | 兆豐 | ✓ |
| `上漲空間 (%) 13.7` | 凱基/中信——**% 在數字之前** | ✗ 一個都抓不到 |
| `potential +27%` | 外資 | ✗ |

`potential` 是普通英文字(growth potential…),所以那一式**強制要有正負號**:
「potential to grow 20%」沒有號,不算。

收盤價的抓法也踩過一次:找到標籤後取其後 48 字,**先把日期樣式挖掉**再抓第一個數字。
不挖就會把「收盤價 **May 19** (NT$) 55.40」的 19 當收盤價 —— 自審時實測到的,
差點讓仲裁拿錯支點。

### A2 四條剔除律,全部有實據

| 律 | 實據 |
|---|---|
| `from A to B` 的 A | 「raise our TP **from** NT$3,600 **to** NT$4,200」——與中文「前次」同族,英文報告改用 from…to 寫 |
| `hi/lo` 或斜線接數字 | 「12M hi/lo NT$3,425.00/1,570.00」是 52 週高低 |
| 觸發詞後緊接 `n.a.` | 「Target price: n.a.」=本報告沒有目標價,不得再往後撈 |
| 數字後接月份縮寫 | 「(2 Oct)」「(21 May)」是日期 |

### A2c 第三種 TP 缺席——而且揪出兩份假綠

Daiwa-3653 與 Daiwa-6278 白紙黑字寫 `Target price: n.a.`,
v0113 跨過去抓「Share price (**21** May)」的 21 當目標價,還掛 PASS。**兩份都是假綠。**

擋下來之後判 FAIL 就換成假紅了(批434 的教訓),所以立第三種缺席:

| 情況 | 狀態 | 立於 |
|---|---|---|
| 文中一個觸發詞都沒有 | `WARN` | 批428-V3 |
| 未評等 NR / Not Rated | `N/A_NOT_RATED` | 批428-V2 |
| **報告明寫 `Target price: n.a.`** | `N/A_TP_DECLARED_NA` | 批437-A2c |
| 有觸發詞卻抽不到數字 | `FAIL` | 真的抽取失敗 |

順帶一個**不修**的決定:GS-2383 TP=6,000 超出台股合理帶,但文內自洽算得通
(6000÷1.32=4,545=同頁自陳的現價)。**燈照黃,不轉綠**——自洽排除的是「抽錯欄」,
排除不了「這份報告以外幣計價」。自己把黃壓成綠就是批422 那個假綠。
仲裁結果寫進註記讓人一眼看得到,要不要放行是操作員的事。

### A3 SUP_MDL744 的 `roles()` 一直回空

橋自己的註解寫著「服務面(**VRN 引擎直接消費的四道**)」:
`text_processor` / `segments` / `tables` / `layout` / `roles`。
而首頁全能引擎從 v0101 起**只消費了 `text_processor()` 一道**。

接上去才發現 `roles()` 根本壞的:

```python
# v0100
return cr.ContentRoleAnalyzer().build(text, lay)   # TypeError:少了 processor
except Exception:
    return {}                                       # ← 吞掉,下游只看到「沒有角色」
```

`ContentRoleAnalyzer.__init__(self, processor)` 要一個處理器。
批419e 記過的病,原封不動又來一次:**捕捉到卻不顯示,等於沒捕捉**。

```
同一份 志強-KY:  v0100 → records=0   v0101 → records=35
```

v0101 三修:餵 `text_processor()` 進去、失敗一律把因由留在 `roles_why()`、
舊收容件若真的不吃參數就退無參建構**並講出來**。

### A4 / A5 裸民國年吃掉目標價

```
_PERIOD 舊式含 1[0-2]\d,沒有邊界
「投資評等目標價 前次投資建議2025. 08. 06: 目標價125 元 報告日期:2025. 1」
命中 ['2025', '125', '2025'] → 湊到 3 個 → 判成表頭 → 印出一張沒有資料列的假表
```

民國年與價格**形狀相同**,分不開就不該猜。只認有上下文的兩種:「民國 114」與七碼日期 `1141202`。

而那張假表還自己打自己的臉——v0113 印「表格還原:無表格訊號」的**同時**印出表頭,
因為 `why` 只在 `hdr and rows` 都有時才寫,`header` 卻照回不誤。
一列表頭沒有任何資料列,那就不是表。

### ENG072 v0108:一個夾的預設值,關掉了一整層防護

操作員跑的那一行:

```
[首頁擷取] …\functional modules\VRN\input_reports 無報告件(誠實;缺件搜集器先跑)
```

話是誠實的,結論是錯的——**報告就在旁邊那個夾**(`input/incoming`,64 份)。
v0107 把 `input_reports` 寫死成唯一預設,而正典冊上明明兩個夾都列著。

後果不只是少一行輸出:sidecar 一份都沒生 → 首頁全能引擎的 `text_consensus`
全部 `N/A_NO_SIDECAR` → **批435 造的多工具核對整層睡著**。
而「兩個工具對同一頁讀出不同的目標價」正是中信金 1.0 的病(工作站真 PDF 抽到 1.0,
庫內第二取字抽到 63.0),那一層當時是關的。

v0108 把報告夾綁回輸入規格正典(`dir_default ∪ incoming`,與首頁全能引擎、MDL141、
MDL139 同一本冊),三態診斷分開講。

### 自審

- 檢數原本手寫 `n = 28`,加了兩檢忘了改,印出「三十檢 OK **28**」自打嘴巴 → 改成真的數
- 斷言本會期第六、七次寫錯:免責聲明之後應為 `APPENDIX` 我寫成 `FOOTER`;
  `role_why` 在下一次呼叫就被重設,我卻事後才讀。兩次都是**碼對、我寫反**

### 實跑

```
三十檢 30/30
庫內 64 份:PASS 48 · WARN 16 · FAIL 0      (v0113 為 47/17/0)
逐檔差異只有兩份——Daiwa-3653 / Daiwa-6278 的假綠被擋下
```

登錄:引擎 v0114、橋 SUP_MDL744 v0101、ENG072 v0108、Grid v0277
(站名「首頁全能引擎三十檢(批437)」,逾時 420→440)、docs 六十五、台帳 931。

## 六十六、批438:右資訊區回歸——把夾律修對,反而讓結果變差

先報好消息:**中信金在真 PDF 上也被扶正了。**

```
── 凱基投顧_2891 中信金_施志鴻_20260519.pdf
   採用 TP=63.0 等級=V(文內自洽 ÷(1+13.7%)=55.41≈自陳收盤價 55.4,升一級)
        63.00  觸發詞  Y Y  415.0  留 ⟨自洽⟩
        59.00  觸發詞  Y Y  265.0  剔 前綴「前次」
```

批437 的仲裁在工作站成立。**壞消息是同一次跑,MS/JP 整批掉了目標價**,那是我造的。

### B1 右資訊區——我親眼看過,卻沒接起來

批437 的 ENG072 v0108 把夾律修對了,工作站第一次真的生出 sidecar。結果:

| 檔 | v0113(無 sidecar) | v0114(有 sidecar) |
|---|---|---|
| MS-2308 | TP=1288 PASS | **TP=- FAIL** |
| MS-3661 | 4388 | **-** |
| MS-3665 / MS-6669 / MS-1590 / JP-3653 | 有值 | **全掉** |

**把夾律修對,反而讓結果變差。**

根因不在批437 的新剔除律,在**批435 的橋只接了 sidecar 的 `body`**。ENG072 的 sidecar 逐區分四塊:

```
header / right / body / footer
```

而外資報告(MS / GS / JP / CLSA)的「投資評等 · 目標價 · 現價」住在**右資訊區**。
sidecar 一生出來,引擎就改吃 `body`,右欄整塊被丟掉 —— 目標價當然抽不到。

操作員批436 的原話是「本文及表格(不含底部小字體**頁尾**)」。
不含的是**頁尾**,不是右欄。我把「不含頁尾」做成了「只要 body」。

更該記的一筆:批437 查 `logical_layout.json` 時我**親眼看過**這一段 ——

```json
{"location": "RIGHT_INFO", "text": "個股報告\n投資評等\n目標價\n逢低買進\n$145\n前次…"}
```

看過,沒接。

v0115:抽欄位吃 `header+right+body+footer` 四區全文;顯示本文(`--body` / `--struct`)仍只給 `body`。
**兩者用途不同,不可合一。**

### B2 「華南無文字是因為沒有 extractors?」——是,而且分兩種病

ENG072 只有**PDF 分區成功**時才寫 `.json`,`.docx` 與掃描檔一律只寫 `.txt`,
而橋只讀 `.json`。於是 4 份華南 Memo 與 MQ-1560 全顯示「文字層=無」。

ENG072 其實早就替它們留了話,寫在 `.txt` 首列:

```
# 華南投顧-3038-全台-Memo.docx · DOCX_LIB_MISSING(pip install python-docx) · …
# MQ-1560 20260520.pdf · NEEDS_OCR · …
```

**話在檔裡,人看不到,等於沒說**(批419e 那一課)。

撿回 `.txt` 之後:

| 檔 | 之前 | 之後 |
|---|---|---|
| 4 份華南 `.docx` | 文字層=無 | 裝了 `python-docx` 就抽得到目標價(檢 ㉜ 示範 92 元) |
| MQ-1560 掃描檔 | 文字層=無 | 仍 NO_TEXT,但講得出「需 OCR」 |

### B3 批422 假綠修(你說「好」)

`ENG080` 四點文摘自己有一道 TP 合理性閘 —— `tp_state = TP_SUSPECT` 表示目標價與現價比值荒謬。
而 `MDL141` 的 `DONE_NS` 守衛**只讀 `vrn_report_basic.upside_state`,從來沒讀過它**。

「四點說目標價有問題」抓到了、寫進庫了,收尾閘看不到。

`TP_SUSPECT` 的定義正是 `_REAL_BAD_STATES` 講的「數字抽出來了而且對不起來」,
只是住在另一張表。同一個判準兩個來源,不能只讀一個。

```
四點 OK        → DONE_NS
四點 TP_SUSPECT → FAIL      (舊碼會給 DONE_NS = 假綠)
```

### B4 MarkdownEditingEngine v1.2.0 —— 這一包真的有庫裡沒有的東西

先查再造第四次。前三包都是「碼庫裡有了,缺的是呼叫」,這一包不同:

`engine/semantic_reconstruction.py` 969 行、**純 stdlib**(csv/hashlib/json/re/pathlib),
不需要它包裡的 Node/Rust/Go 就跑得起來。

| 它有的 | 批436 我寫的 |
|---|---|
| `def_classify_blocks` 先分類 frontmatter/code/table/heading/list/quote/HTML/paragraph 再切句 | 直接逐行判 |
| `def_period_is_boundary` 判「這個點是不是真的句尾」 | `buf[-1] in "。.!?"` |
| `def_analyze_tables` 表頭/分隔列/逐列欄數/matrix SHA-256 | 期間數 + 對齊數字 |

所以「報告日期:**2025.12.**」在我這裡會被切成兩句 —— 那是日期不是句號。

**而且我接錯了一次。** 第一版只把 `buf` 傳進去,句點剛好在字串尾,
它的 `next_character` 是空的於是一律回 `True` —— 接了等於沒接:

```
第一版  「兆豐證券投顧 報告日期:2025.12.」 / 「04 研究員…」   ← 還是斷開
修正後  「…報告日期:2025.12. 04 研究員:黃煜倫 目標價 145 元。」  ← 接對了
```

正確用法要把**下一行的第一個字**接上去再問。這正是它門規
`split-first-merge-never` 的意思:**邊界要可證明才切**。

收容件原地不動(`MANIFEST.sha256` 隨包保留),另立 `SUP_MDL745_MarkdownStructureHub_v0100`
統轄橋;橋掛不上退回批436 粗判並在 `md_why` 標明退了。

### 自審

`MDL141` 的檢數也是手寫(「十三檢 OK **12**」),與上一批引擎同病,一併改成真的數。

### 實跑

```
首頁全能引擎 三十三檢 33/33 · MDL141 十三檢 13/13 · MDL745 六檢 6/6
MDL744 十一檢 11/11 · ENG072 十六檢 16/16
庫內 64 份:PASS 48 · WARN 16 · FAIL 0(與 v0114 同,無迴歸)
```

登錄:引擎 v0115、MDL141 v0106、SUP_MDL745 v0100、MarkdownEditingEngine v1.2.0 收容、
Grid v0278(站名「首頁全能引擎三十三檢(批438)」逾時 440→480,新增「Markdown 結構橋六檢」)、
docs 六十六、台帳 932。

## 六十七、批439:CLST 與 CLSA 是同一家——而且是我自己造的兩個正典

批438 兩修在工作站都證實生效:

| | v0114 | v0115 |
|---|---|---|
| MS-2308 / 3661 / 3665 / 6669 / 1590 · JP-3653 | 目標價全掉 | **1288 / 4388 / 1900 / 3500 / 1130 / 2470 全回來** |
| 4 份華南 `.docx` | 文字層=無 | **文字層=純文字** |
| MQ-1560 | 文字層=無 | 文字層=無**(需 OCR 才有字)** |
| FAIL | 2 | 1 |

### C1 剩下那唯一的 FAIL,根因是我

`CLST-6669` 的 `filename_vs_page` 還是紅的。查下去:

```python
# 批428-T5 我加的
"CLSA": ["里昂", "clsa"],                      # ← 冊上本來就有
"CLST": ["clst", "clsa taiwan"],               # ← 我又新增了一個
```

**同一家券商,兩個正典鍵。** 檔名 `CLST-6669` 正規化成 `CLST`,頁面文字認出 `CLSA`,
`filename_vs_page` 逐欄比對永遠對不上。

零九頭龍講的就是這件事:**該加別名的時候,不要新增正典。**

而它拖到現在才爆,是因為批438 把右資訊區接回來,頁面才**第一次**認得出券商 ——
修對一件事,把另一件錯照出來。

庫內 64 份逐檔對照 v0115 → v0116:**只有一行變**(券商 `CLST`→`CLSA`),零迴歸。

### C2 讀序不同,不是內容分歧

20 份報告掛 `text_consensus: WARN`。ENG072 的 `compare_zones` 是這樣算的:

```python
r = difflib.SequenceMatcher(None, ta, tb).ratio()   # 比字元**序列**
```

而兩欄式 PDF 的 fitz 與 pdfplumber **讀序本來就不同** —— 字一樣、順序不同,比率就掉進 0.60–0.90。

```
fitz        台達電 2308 我們看好…  投資評等 增持 目標價 NT$1,288.00
pdfplumber  投資評等 增持 目標價 NT$1,288.00  台達電 2308 我們看好…
序列比率 0.688 → 舊判定 PARTIAL(黃燈)
```

對**抽欄位**而言順序根本不重要。目標價是 1,288 就是 1,288,它排在第幾個字不影響任何一道閘。
把「順序不同」講成「可能讀錯字」,錯誤矩陣會被不是錯的東西灌滿(批434 那一課)。

加兩道分流,都在橋這一側算,**ENG072 零觸碰**:

| 訊號 | 用途 |
|---|---|
| 字元**多重集**(與順序無關) | 掉字/多字/錯字跑不掉,**只有排序**跑得掉 |
| **數字多重集** | 閘吃的全是數字,這一道才是把關的 |

### C2 自審 —— 檢 ㉟ 逼出來的洞,比原本的問題更嚴重

初版我把數字檢查放在 `AGREE` 之後。於是:

```
2,000 字的頁面,pdfplumber 把目標價讀成 1,238 而不是 1,288
序列比率 = 0.999  →  判 AGREE  →  一路綠燈
```

**而那正是批435 造這一層要抓的事。** 閘吃的全是數字,數字打架比字像不像重要得多,
所以 `NUM_CONFLICT` 排在序列比率**之前**,判紅:

```
純讀序不同      → ORDER_ONLY (綠)   多重集 1.0
目標價讀錯一位  → NUM_CONFLICT (紅) 序列比率 0.999 仍看似一致
                  差 ['1288.00'] ↔ ['1238.00']     ← 講得出是哪個數字
長文錯一中文字  → AGREE (綠)        不是數字問題,不無中生有
```

「不一樣」還要分兩種,否則會造假紅:

- **子集 = 涵蓋差** —— pdfplumber 把表格另外抽,body 少幾個數字是正常的
- **兩邊各有對方沒有的 = 真衝突** —— 同一個位置讀出不同的數,一定有一邊錯

### 自審

`--report` 不帶值時印「後面沒有值=**忽略**」,然後**照樣產出了報告**。
訊息與行為對不上,比沒有訊息更糟。`--report` 不帶值本來就合法 —— 改成「走預設路徑」。

### 實跑

```
三十五檢 35/35
庫內 64 份:PASS 48 · WARN 16 · FAIL 0
v0115→v0116 逐檔差異:1 行(CLST→CLSA)
```

登錄:引擎 v0116、Grid v0279(站名「首頁全能引擎三十五檢(批439)」逾時 480→500)、
docs 六十七、台帳 933。

## 六十八、批440:我把閘改嚴,多出 15 個紅

上一批我的收尾話是「這一跑應該是 FAIL 0」。工作站實跑:**FAIL 從 1 變成 16**。

批439 我加的 `NUM_CONFLICT` —— 兩個取字工具各有對方沒有的數字就判紅 ——
在合成測資上乾淨漂亮,真 PDF 上把 15 份沒問題的報告點成紅。

### 根因:欄界會把數字黏成一個新數

```
fitz        「毛利率18.12,170」  → 讀出 18.12 與 170
pdfplumber  「毛利率18.1 2,170」 → 讀出 18.1  與 2170
```

兩邊互有對方沒有的數,而**沒有任何一邊讀錯** —— 那是斷字位置不同。
原始數字袋量大、雜訊多,不能當核對訊號。

### 修:比兩側各自抽出的目標價

批435 造這一層時我寫的是「兩個獨立工具對同一頁讀出不同的**字**」。
但下游真正消費的不是字,是**抽出來的那個數**。

```
純讀序不同      → ORDER_ONLY (綠)
欄界黏字        → 不點燈(數字袋差異留在診斷裡看得到)
目標價打架      → TP_CONFLICT (紅)  1288.0 ↔ 1238.0
                  序列比率 0.999 看似一致也要判紅
```

`TP_CONFLICT` 收得很緊:**兩側都抽到且不同**才算。
一側抽到一側沒有 = 涵蓋差(pdfplumber 常把表格另外抽),不點燈。

### 該記的教訓

我上一批才剛在 **docs 六十六** 寫下批434 那一課 ——
「把不是錯的東西講成錯,錯誤矩陣會被不是錯的東西灌滿」——
然後下一批就自己再犯一次,而且是**拿合成測資就把一道閘改嚴並上線**。

> 合成測資只能證明碼會動,證不了它不亂點燈。
> **改嚴一道閘之前要有真檔證據。**

這一條與批429 的「改排序一定要跑前後差」同族,但更嚴格:
前後差要跑在**真檔**上,不是我自己寫的字串上。

### 實跑

```
三十五檢 35/35
庫內 64 份:與 v0116 逐檔零差異
```

登錄:引擎 v0117、Grid v0280、docs 六十八、台帳 934。

## 六十九、批441:一頁式矩陣報告 —— 後面加一個,不是換掉那個

批440 生效:工作站 **FAIL 16 → 1**,我自己造的 15 個假紅清掉了。

剩下那一個是 **MS-2308 的 `text_consensus: TP_CONFLICT`** ——
fitz 與 pdfplumber 對同一頁抽出**不同的目標價**。那是真訊號,正是批435 造這一層要抓的事。

但它**沒說是哪兩個數**。捕捉到卻不顯示等於沒捕捉(批419e),所以逐列改印:

```
· **兩工具目標價打架** fitz=1288.0 pdfplumber=1238.0(引擎採用 1288.0;兩者必有一錯)
```

### 一頁式:五段直排,六分頁保留不動

操作員令是「**後面加一個**」,不是「換掉那個」。只增不減。

| 段 | 內容 |
|---|---|
| ① DETAILED SUMMARY MATRIX | 逐報告 × 全欄位 × 每一道閘 |
| ② ERROR MATRIX | 只放非綠;N/A 不進來(證據不可得不是錯) |
| ③ BASIC INFO | 庫 `vrn_report_basic` |
| ④ **FIXED CONTENT** | 一標題 一句話一行,類型分類在前,自動換行 |
| ⑤ FINANCIAL DATA | 紅黃綠燈 |

零九頭龍:欄寬最佳化(批429-X2)、燈號晶片、跳脫全部沿用既有 `_table` / `_chip` / `_esc`,
不另寫一套 HTML 堆疊。字級 8.5px(六分頁 9px),零 CDN。

### ④ FIXED CONTENT —— 直接吃批436 的列化結果,不重算

```
報告檔 | 型別 | 券商 | 報告日 | CATEGORY | TYPE | 財報表 | 內容
…6873 | 個股 | MEGA | 2025-08-19 | 文      | BODY | 評價分析 | • 展望 2026 年,在台灣…
…2308 | 個股 | MS   | 2025-11-28 | 表3     | BODY | 損益表   | 營業收入 41,430 52,180
```

`CATEGORY`(表/圖/文,表圖題之後的列繼承該題與表號)與 `TYPE`(字體階層)
全部排在句子**前面**;內容欄 `white-space:pre-wrap`,長句自動換行不截斷。
庫內 64 份實跑產出 **482 列**。

### ⑤ FINANCIAL DATA 的紅黃綠 —— 綠只給報告自己寫的數

| 燈 | 狀態 | 理由 |
|---|---|---|
| 綠 | `REPORT_STATED` / `DB_MATCH` | 報告自己寫的 |
| 黃 | `ESTIMATE` / `DERIVED` / `ROUNDING` / `UNIT_SCALE` | **推估或推導不是事實** |
| 紅 | `DIVERGE` / `MISMATCH` / `PARSE_SUSPECT` / `FORMULA_MISMATCH` | 對不上 |
| 灰 | 冊上沒有的狀態 | **不猜色**——猜色就是假綠 |

庫不在就印為何並指路(先跑 `vrn_structdb` 再跑 `vrn_finpages`),不留白。

### 自動跳出來 vs 零彈窗

治理律零彈窗(批340)講的是引擎不得**自作主張**開視窗。
操作員明令要開,那不是自作主張 —— 所以一頁式產出後自動開。

`VIA_NO_OPEN=1` 照樣不開(那是他自己設的閘,我不代解),並印出本窗怎麼開;
`--no-onepage-open` 可以單次關掉。

### 實跑

```
三十六檢 36/36
庫內 64 份:PASS 48 · WARN 16 · FAIL 0
一頁式 336 KB · 482 定稿列 · 外部資源 0
```

登錄:引擎 v0118、Grid v0281(站名「首頁全能引擎三十六檢(批441)」逾時 500→520)、
docs 六十九、台帳 935。

## 七十、批442:邏輯一致化 —— 兩個引擎讀不同的名冊表

操作員令:「自測試自修正 VRN 至 BASIC INFO / FINANCIAL INFO / FIXED CONTENT 正確,
多方法核對,兩邊工具都要一致化,邏輯一致化,測試無誤後同步上傳兩個 GitHub」。

### 先量再改 —— 要談「正確」就得先有資料

庫裡沒有 PDF,只有 64 份修復文字。用它們 + `02_layout/logical_layout.json` 的
MAIN/RIGHT_INFO 分區造出 64 份 sidecar,**誠實標記為單一取字來源** ——
不寫 `plumber`、不寫 `compare`,讓 `SidecarBridge` 判 `SINGLE_TOOL`(黃)。
偽裝成雙工具一致就是假能力。

跑完 ENG073 入庫,再與首頁引擎逐檔比對:

```
可比對 64 份 · 型別不一致 38 · 代號不一致 37
報告型別:其他 38 · 產業 9 · 大盤晨報 7 · 個股 5 · 海外 4 · 研討會 3
```

**個股只有 5 份**,而首頁引擎判出 43 份。

### 根因不是啟發式要微調,是兩本名冊

| 引擎 | 名冊 | 6873 在不在 |
|---|---|---|
| 首頁引擎 | `NameReconciler` 階梯 → `tw_listings_industry`(1978 檔) | **在** |
| ENG073 | 寫死 `tw_listings`(891 檔) | **不在** |

代號查不到 → `classify_kind` 沒有代號可用 → 型別掉成「其他」 → BASIC INFO 整片是空的。

這是零九頭龍在檔名層的實例:**兩套實作、兩本名冊、兩種答案。**

### 修:開一道公開契約,不抄第二份

引擎 v0119 開 `filename_facts(filename)`,一次交出代號/券商/報告日/名稱提示/型別/型別理由。
ENG073 v0116 綁它,並改用首頁的四階梯查官方名
(原本只查 891 那本,所以代號對了、名字還是空的,不算正確)。

契約用**公開方法**不用私有 `_filename_fields` —— 跨模組碰別人的底線,下次改名就斷。

```
綁後:可比對 64 份 · 型別不一致 0 · 代號不一致 0 · 券商不一致 0 · 報告日不一致 0
報告型別:個股 43 · 產業 10 · 大盤晨報 7 · 研討會 3 · 海外 3
有代號 43 列 · 其中有官方名 43 列(100%)
```

### 正本庫被我的自測夾具污染

實跑發現 BASIC INFO 69 列裡混著 `fx_report` / `fx_twocol` / `synthetic_financial_report`
—— **自測夾具寫進了正本庫**。測試污染正本,那一段就不算正確。

ENG073 v0116 補 `purge-selftest`,紀律與 ENG072 同律:
**預設只列不刪,`--apply` 才真的動**,刪的只有夾具列,不碰任何一列真報告。

```
[fixture 清理] vrn_report_basic 3 列 · vrn_report_metrics 2 列 · vrn_report_crosscheck 2 列
清完:66 列全真
```

### FINANCIAL INFO 的誠實邊界

財報資料要**真 PDF** 才抽得到(ENG074 讀的是財報頁表格)。我這邊只有修復文字,
所以庫內仍是先前 8 份報告的 27 列。紅黃綠實測 **18 綠(REPORT_STATED)/ 9 黃(ESTIMATE)**,
分色規則正確 —— 但要 64 份全有財報資料,**必須在操作員機器上跑 `vrn_finpages`**。

順帶修掉 ENG074 v0104 的夾律:它把 `input_reports` 寫死,
與 ENG072 v0107 犯過的**一模一樣**(批438 已修)。同一個錯不該在第二支引擎再犯。

### 兩邊一致化 —— 而且抓到一個本來就不一樣的地方

移植到 `tonykuni/via-vdf-vrn`(`85c410d`):文內自洽仲裁、上漲空間三式、
收盤價先挖日期、四條剔除律、`tpGrade` 自洽升級。

移植過程中抓到**兩庫本來就不一樣**的一處:

```
母庫  目標價 [^\d\-]{0,20} 數字        ← 括號/貨幣記號/換行都跨得過
另庫  目標價 \s*[:：]?\s*  數字        ← 只允許冒號與空白
```

所以凱基/中信的「12 個月目標價 **(NT$)↵**63.00」母庫抽得到、另庫一個都抽不到。
**同一份報告兩庫給不同答案,那就是邏輯不一致。** 改成同寬,並配上 `n.a.` 守衛
(窗放寬之後不加守衛就會跨過「Target price: n.a.」去撈「Share price (21 May)」的 21)。

### 自審

ENG073 的檢數也是手寫(「三十五檢 OK **34**」)—— 首頁引擎、MDL141 之後的**第三支**。
一併改成真的數。

### 實跑

```
首頁 三十六檢 36/36 · ENG073 三十五檢 35/35 · ENG074 十六檢 16/16
兩引擎逐檔比對 64/64 四項全一致
另庫 first-page-tp 13→18 測全過 · 該庫 82 個測試檔全數 fail 0
```

登錄:引擎 v0119、ENG073 v0116、ENG074 v0104、Grid v0282、docs 七十、台帳 936、
另庫 `85c410d`。

## 七十一、批443:資料已經在庫裡,是我找不到那個庫

工作站同一次跑,兩個引擎講了兩句互相矛盾的話:

```
ENG073  [庫解析] 主路徑缺→改用替根庫(家目錄那份 clone)…  → basic +59
ENG074                                                    → 財報值 +7,024
首頁引擎 庫:庫不在(OneDrive 那份)
```

**資料已經在庫裡了。是首頁引擎找不到那個庫。**
一頁式的 BASIC INFO 與 FINANCIAL DATA 因此還是「庫不可得」—— 不是沒資料。

ENG073 的 `_resolve_db` 有雙 clone 替根探測,首頁引擎的 `_locate_db` 只認主路徑。
批442 統一了檔名層,這是同一件事沒做完。v0120 補上 `_alt_root()`。

### 真檔逼出的兩個抽取洞

**JP-3653 抽到的是現價,不是目標價。**

```
Price Target (Dec-26):NT$3,650.00     ← 真正的目標價
Price (02 Oct 25):NT$2,470.00         ← 現價

v0119 trace:
  2,470.00  NT$  165.0  留     ← 位置先,勝出
  3,650.00  NT$  165.0  留
  採用 TP=2470.0 等級=P
```

觸發詞到數字的窗是 `[^\d\-]{0,20}`,而括號裡的目標年月**含數字** ——
窗遇數字就停,於是**觸發詞車道一個都沒命中**。窗改成可跨過一組括號:

```
  3,650.00  觸發詞  265.0  留   ← 採用 TP=3650.0 等級=M
```

MS 的「Price target (Dec-26)」、凱基的「12 個月目標價 (NT$)」是同一形狀。

第二個:現價標籤冊補「`Price (`」與「`Close`」—— 外資第一頁就是這樣寫的。

### 自審:綁契約不等於把對方的守衛一起拆掉

ENG073 v0117 把目標價與現價也綁上契約(它自己抽的
中信金 **59**=前次目標價、MS-2308 **38**、JP-3653 **26**、MS-8210 **18** 全錯),
結果自測 35 檢掉了三檢 ⑬ / ⑮ / ⑱。

查下去不是契約錯,是**批239 立的配對合理性律(TP/P 比值 0.30–3.2,否則寧缺勿假)
被我繞過去了** —— 於是「目標價 367 元 / 收盤價 19」的 19 被寫進庫。

> 那是本檔的正主知識。**綁契約把對方的守衛一起拆掉,那叫換一個錯,不叫一致化。**

改成:契約給值,本檔的配對律仍然當家。再補一條
「目標價 == 現價 = 同一個數讀兩次」剔除律
(JP 型的「PT Dec-25」那一行只剩日期沒有數字,裸 NT$ 車道就把現價當成了目標價)。

同時在首頁引擎加「前綴月份 = 目標日期不是價格」。與括號式的差別就在**括號**:
括號裡的是註記可以跨過去;月份緊貼數字,那個數字就是日期的一部分。

### OCR —— PaddleOCR 系列有,而且早就在庫裡

先查再造第四次。`GenericLayoutEngine v2.1.0` 的 `all_backend_engines.py` 有八個 OCR 後端,
`SUP_MDL743` 橋也早就掛著:

```
ocr 路由 7 支:tesseract · paddleocr · paddle_ppstructure · paddle_pdf_pipeline
              · easyocr · ocrmypdf · transkribus_core
paddle 模式另掛:paddle_layout · paddle_detection        ← PaddleOCR 系列共五支
```

只是 `NEEDS_OCR` 的檔從來沒去走它。ENG072 v0109 接上 `mode="ocr"` 的 orchestrator。

**一支都沒裝時絕不假抽** —— 改印路由、逐支在位狀態與三種裝法:

```
[OCR 未就緒] 路由 7 支全未裝:tesseract, paddleocr, paddle_ppstructure, …
   掃描影像 PDF 會誠實停在 NEEDS_OCR(不假抽)。要開通擇一:
   pip install paddleocr paddlepaddle   # CJK 最佳,操作員指名的那一系
```

標記也由「`NEEDS_OCR`」改成「`NEEDS_OCR[為何]`」——「候 OCR」三個字讓人不知道下一步。

### 實跑

```
首頁 三十六檢 36/36 · ENG073 三十五檢 35/35 · ENG072 十六檢 16/16
庫內 64 份 FAIL 0
BASIC INFO 66 列全真 · FIXED CONTENT 497 列 · FINANCIAL 27 列(18 綠 / 9 黃)
TP 前後差:只有 JP-3653 一份(2,470 → 3,650)
```

登錄:引擎 v0120、ENG073 v0117、ENG072 v0109、Grid v0283、docs 七十一、台帳 937。

## 七十二、批444:先查再造第五次 —— 而且這一次我先講錯,再改回來

操作員上傳 `VIA_PDFPlumberPlusEngine.py`(1196 行)並令「接上去」。

### 先把話講回來

我上一輪對操作員說過:「這包真正庫裡沒有的,是它**真的會去建構** PaddleOCR /
PP-Structure。」**那句是錯的。**

查了 `GenericLayoutEngine_AllEngines_v2.1.0_b245/GenericLayoutEngine/all_backend_engines.py`
第 1334–1348 行才知道,GLE 的 `PaddleOcrEngine.extract()` 一樣真的
`from paddleocr import PaddleOCR` 並建構,而且**連 3.x 新 API 都接**——
`PPStructureV3` / `LayoutDetection` / `engine.predict()`;這一包只接得動 2.x
(`PPStructure`、`use_gpu`、`show_log` 都是 2.x 才有的鍵)。論 OCR 建構,
**庫裡那支比較新**。

所以這條車道的定位不是取代,是**補位**:誰在位誰上。

### 逐項對照後,真正非重疊的三件

| | 這一包 | 庫裡本來有的 |
|---|---|---|
| OCR 建構 | paddleocr **2.x**,`_build()` 逐鍵剝除不支援 kwargs | GLE:**2.x + 3.x**,七支後端路由 |
| 渲染 | 記憶體內 fitz→NumPy,不落暫存圖 | GLE:fitz→PNG 落地 |
| 抽表 | **四策略**(lines / lines+text / text+lines / text)+重疊率去重+表頭回溯+填充率平方化評分 | GLE 的 pdfplumber 轉接器:**只跑 lines/lines 一種** |
| 逐頁分流 | **字元密度閘** | 沒有。ENG072 也沒有 |

四策略是真的有差。同一批真檔跑下來,勝出的策略各不相同:

```
synthetic_financial_report.pdf   S1_lines        3 列×4 欄
EarningsInsight_062626.pdf       S4_text        20 列×10 欄   ← lines/lines 一張都找不到
VisualLock_v0109_SLIDES.pdf      S4_text        19 列×12 欄
TALib_參考_A_14頁.pdf            S3_text_lines  15 列×10 欄
```

### 真正的收穫是密度閘,而且一個新套件都不必裝

ENG072 到 v0109 為止的判準是:

```python
txt = doc[0].get_text("text", sort=True).strip()
if txt:
    return txt, "FITZ_LAYOUT"
```

抽得到**一個字**就算有文字層。一頁只有浮水印文字層(「機密」「DRAFT」十來個字)
的掃描頁會被這一問放行,首頁引擎再從那十來個字裡找目標價——**那是假綠**。
而且是最難查的那種假綠,因為它**有值**。

密度閘把「字數 ÷ 頁面點面積」一起看,浮水印那種頁 3e-05 遠低於 2e-04 就擋下來。

### 但密度單獨用會誤殺 —— 批440 那一課第二次現身

全庫 20 件 PDF 掃過一輪,跳出一件:

```
supportive modules/specs/Veritas Intelligence Analytics Brief.pdf
  949 × 7448 點(14.1 倍 A4 面積)· 首頁 862 字的 8–11pt 正文
  密度 1.22e-04 < 門檻 2e-04  → 光看密度會判它「掃描頁」
```

那是**假紅**。一份長捲頁(web 式一頁 brief)的真文字層,被面積稀釋掉了。

批440 的那一課——「改嚴一道閘之前要有真檔證據,合成測資只能證明碼會動,
證不了它不亂點燈」——在這裡第二次現身,而且這次是我自己在收容件裡撿到的
現成參數,更容易照單全收。

修法:**密度只當訊號,不當判決**。誠實三態:

| 態 | 判準 | 處置 |
|---|---|---|
| `DIGITAL` | 密度過門檻 | 照抽 |
| `THIN` | 密度不足**但字數 >= 300** | **照抽**,只把「稀薄」標出來 |
| `SCANNED` | 字數 < 300 且密度不足(或幾乎無字) | 走 OCR 車道 |
| `UNKNOWN` | 探不動(檔不在/頁數不足/橋缺席) | 走 v0109 原路,零回歸 |

界線 300 是量出來的:全庫最低的真文字首頁是 442 字
(`synthetic_financial_report.pdf`),浮水印/戳章那種頁在 100 字以下,
300 兩邊都留得住餘裕。

### 閘要擋在對的地方

第一次接的位置是 `extract_pdf_page1()` 裡——**錯的**。PDF 的正路是分區道
`extract_page1_zones()`,浮水印那十幾個字照樣會讓 `zones["header"]` 非空,
分區道就把它當首頁文字收下了。**閘擋在後面等於沒擋。**

改成分流先跑,判 `SCANNED` 就整條分區道都不走,直接交給 OCR 車道;
OCR 也跑不動就停在 `NEEDS_OCR[…·密度閘:…]`,把密度因由寫進標記——
不靜靜把浮水印那十幾個字當首頁文字送下去。

### OCR 兩車道

```
道一 GLE(SUP_MDL743)  七支後端,含 paddleocr 3.x 新 API   ← 先走
道二 PPP(SUP_MDL746)  只接 2.x,但記憶體內渲染不落暫存圖   ← 道一整條不在位才換
```

順序的理由是**涵蓋面**,不是偏好。兩條都不在位就誠實停在 `NEEDS_OCR`,
兩條的因由都印出來:

```
[OCR 未就緒] 道一 GLE 路由 7 支全未裝(tesseract, paddleocr, …) · 道二 PPP 缺 paddleocr
```

### 自審三條

**① 候OCR 那格一直報 0。** 批443 起 `NEEDS_OCR` 帶了因由後綴,而 v0109 的
`key = tag if tag in stats` 對不上鍵,整批被算進 `OTHER`。改取「[」前的基名。

**② ENG072 的檢數也是手寫**(`16 - len(fails)`)。這是第四支同病
(前三支在批438/批442/批443),一併改成 `done.append(name)` 真的數。

**③ fixture 太瘦。** `fx_report.pdf` 首頁只有 38 個字,密度閘**正確地**把它
判成掃描頁——38 字的一頁和只有浮水印的掃描頁本來就分不出來。
修法不是把閘放寬(那等於白做),是把 fixture 加厚成**像一頁真報告**(2194 字)。
fixture 太瘦就代表不了它要代表的東西。

### 紀律

* **收容件原地不動**——不是宣告,是證據:全部服務道跑過一輪後
  收容件 SHA-256 不變(`d1a4d8f037ce…`),且原始碼裡凡提到 `INTAKE` 的行
  一行都沒有寫檔動詞。
* 它 `_PARAMS["VIA_ROOT"]` 硬寫 `C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics`
  ——**操作員實機不是這條**(是 `…\OneDrive\Documents\movies-dataset\…`)。
  橋一律用 `CFG["out_dir"]` 蓋過去,落到 `VIA_Reports/pdfplumber_plus/`(已入 .gitignore)。
* 零網路、零彈窗(它只寫 report.html 不自己開窗;stderr 進度條在**記憶體內**關掉,
  檔案一位元不動)。

### 落地

| 件 | 版 | 檢 |
|---|---|---|
| `SUP_MDL746_PDFPlumberPlusHub` | v0100 | 九檢 9/9 |
| `VRN_ENG072_FirstPageText` | v0110 | 十八檢 18/18 |
| `CGC_MDL064_SelftestGrid` | v0284 | +「PDFPlumber-Plus 統轄橋九檢」站 |
| `Register-VIA-Commands` | v0168 | +`via-ppp`(別名 抽表橋) |

短令:

```powershell
via-ppp                          # 狀態頁:掛載態/落地根/逐件在位/OCR 車道可跑否
via-ppp --triage "C:\...\x.pdf"  # 這一頁到底有沒有文字層(DIGITAL/THIN/SCANNED)
via-ppp --run    "C:\...\x.pdf"  # 整份跑並落地 JSON/CSV/MD/HTML + G00–G12 閘報
via-ppp --selftest
```

## 七十三、批445:那一個 FAIL 底下有十二份

工作站跑完批443 只剩一個 FAIL:MS-2308 的 `text_consensus`,
`fitz=1288.0 pdfplumber=38.0`。看起來是「兩個工具讀不一樣」的小事。

**先量再改**——把庫內 66 份真 sidecar 的目標價 / 現價 / 自陳上漲空間逐份量過:

| 檔 | 現價(v0120) | 真值 | 假在哪 |
|---|---|---|---|
| MS-1590 / 2308 / 3661 / 3665 / 6669 / 8210 | `2025` | 885 / 932 / 3190 / 1535 / 3510 / 621 | `close (Nov 28, **2025**)` — 日期挖掉月日,沒挖走年 |
| JP-3653 / JP-2330 / Citi-3231 | `25` | 2470 / 1130 / 114 | `Price (02 Oct **25**)` — 兩碼年 |
| MS-ABF | `2026` → `5` | 無 | `the close on … **05:30** AM GMT` — 那是發佈時刻 |
| 統一投顧投資早報 | `5` | 無 | `收盤價 漲跌 漲跌幅 **5 日**漲跌幅` — 那是期間 |
| 兆豐晨會 / 凱基鋼鐵 | `120` / `2025` | 無 | 大盤與產業報告,本來就沒有單一現價 |

### 為什麼十二份都沒有亮燈

`tp=1288 / px=2025` 的比值是 **0.64**——**落在批239 的合理帶 0.30–3.2 之內**。
批443 才剛把 ENG073 綁上契約,它會把 2025 當成現價寫進庫。

有值、比值合理、閘全綠。**這種假綠比抽不到還難查**,因為抽不到至少會留一格空白。

### 38 那一側

MS 的右資訊區寫:

```
Up/downside to price target (%)
38
Price target
NT$1,288.00
```

觸發詞 `price target` **長在上漲空間欄的標籤裡**。舊的百分比剔除律看的是
數字**後面**有沒有 `%`——這裡 `%` 在數字**之前**,而且包在單位括號裡,擋不住。
於是 38 掛觸發詞級 240 分,成為合法候選;fitz 那側因為 `NT$1,288.00` 拿到
265 分才險勝,pdfplumber 那側欄序一換就輸掉。

### 四修一放寬

1. `_DATEISH` 補年份段——**做成可選的**。中信金寫
   「維持收盤價 May 19 **(NT$)** 55.40」,月份後面接的是幣別不是年份,
   吞過頭會把 55.40 一起帶走。
2. `doc_close` 改 **帶幣的數優先於裸數**。批429「來源>貨幣」同一族:
   MS 的真值是 `NT$932.00`、JP 的是 `NT$2,470.00`,而假值 `2025`、`25` 都是裸的。
3. **弱標(`股價|收盤`)只認帶幣的數**。拿不出幣證就不給值——寧缺勿假。
4. 新剔除律:**觸發詞長在 `up/downside to …` 標籤裡 = 那是上漲空間欄**。
5. `_UPSIDE_UNIT` 放寬到容得下 `to price target`。

### 放寬之後,MS 全家第一次自洽

| 檔 | 目標價 | 現價 | 自陳% | 隱含價 | 差 |
|---|---|---|---|---|---|
| MS-1590 | 1130 | 885 | 28 | 882.8 | 0.25% |
| MS-2308 | 1288 | 932 | 38 | 933.3 | **0.14%** |
| MS-3661 | 4388 | 3190 | 38 | 3179.7 | 0.32% |
| MS-3665 | 1900 | 1535 | 24 | 1532.3 | 0.18% |
| MS-6669 | 3500 | 3510 | 0 | 3500.0 | 0.28% |
| MS-8210 | 730 | 621 | 18 | 618.6 | 0.38% |

1288 於是不是猜的,是**同一頁三個數字互相算得出來的**。

而剔除律與仲裁是**兩件事**:仲裁是**分數**壓過去,只在報告自陳上漲空間時
發得動;剔除律是**直接剔掉**。沒自陳上漲空間的 MS 報告只有剔除律擋得住,
所以兩道都要。

**實測 66 份:比值荒謬 5 → 0,目標價改變 0 份**(只修現價,不動目標價)。

### 自審 —— 兩條都犯在我自己的新檢上,而且都是批419e 那一課

**①「上版 0」是假的。** 我寫的 ㊳ 要拿上一版當對照組,結果印出
「比值荒謬 上版 0 → 本版 0」。讀起來像「上一版本來就乾淨,這批沒修到什麼」——
**真相是對照組根本沒跑**:本檔模組層沒有 `import sys`(只有加速橋的 `_sa_sys`),
`sys.modules[...]` 拋 `NameError`,被我自己的 `except Exception` 吞掉。

**② 同一檢因為什麼都沒做而通過。** 修好 ① 之後它還是印 0。
第二個原因是 `_json` 未定義,`except Exception: continue` 把 66 份**一份一份**
吞掉,迴圈裡**一份都沒進去**;而判準 `_n45 == 0 and _tp45 == 0`
在什麼都沒做的時候**恆為真**。

> 一個因為什麼都沒做而通過的檢,比紅燈還糟。紅燈至少會叫。

兩條都改成「對照組載不進來 / 真的跑過的份數不足 → 判紅」,
並把 `真的跑過 66/66 份` 印進因由裡。同一批之內,同一課犯了兩次。

### 落地

| 件 | 版 | 檢 |
|---|---|---|
| `VIA_VRN_FirstPageEngine` | v0121 | 三十八檢 38/38 |
| `CGC_MDL064_SelftestGrid` | v0285 | 站名 三十六檢 → 三十八檢 |

`ENG073` / `ENG074` / `MDL141` 零改動——它們自批442/443 起就綁契約走尾版律,
引擎一換版自動跟上。

## 七十四、批446:同一份冊,四個消費者三個做對一個做錯

`via-vrnval --run` 第一段就停:

```
[via-console run] NEED_DIR:報告夾缺:…\functional modules\VRN\input_reports
[via-closeout --run] vrn_firstpage rc=2 → 停(誠實;修後重跑)
```

而**同一次跑**的收尾閘:

```
[via-closeout vrn] 報告 64(DONE 0 · FAIL 0 · PENDING 64)
                   段:{'收件': 5, '首頁': 59}
  PENDING MS-2308 20251128.pdf   段 1/4(首頁)  夾✓ 頁✓ 庫- 四點-
```

**64 份報告全在 `input/incoming`。收尾閘看得見,啟動器看不見。**

### 報告夾律,四個消費者

| 消費者 | `dir_default ∪ incoming`? | 立於 |
|---|---|---|
| `VRN_ENG072` v0108 | ✅ | 批438 |
| `VRN_ENG074` v0104 | ✅ | 批442 |
| `CGC_MDL141` v0105 | ✅ | 批400 |
| `CGC_MDL139` `kind == "dir"` | ❌ 只認 `dir_default` | — |

更難看的是 MDL141 那一份的 docstring:

```python
def _report_dirs(spec, given):
    """報告夾律(批399 自審;同 MDL139 dir 參數):…;incoming 一律併入"""
```

「**同 MDL139 dir 參數**」——那句是假的。本檔併 `incoming`,MDL139 不併。
**「同某某」寫在註解裡,不會讓它真的相同。**

而且這件事**批421 的台帳第 915 筆就記過了**,逐字:

> via-console run --item vrn_firstpage 回 NEED_DIR:預設夾 input_reports
> 不存在,實檔在 input/incoming

記了沒修,拖了 25 批。

### 第二條同型:主庫替根

同一次跑:

```
ENG073/ENG074 → 主路徑缺→改用替根庫(家目錄那份 clone)· 寫進 59 列 basic / 7,024 列財報值
收尾閘        → 庫缺 …\mega\vdf_tw_market.duckdb(先 via-vdfdb run --apply / 日更鏈)· GREY
```

替根探測 `ENG073._resolve_db`(批244)、`ENG074`、首頁引擎 `_alt_root`(批443)都有,
MDL141 寫死 `DB_TW`,不在就判 GREY。**庫就在那裡,是收尾閘沒去找。**
批443 那一課(「資料已經在庫裡,是我找不到那個庫」)第二次現身,這次在收尾閘。

### 治法:不是貼第四份第五份

兩條律收在**冊的擁有者** `CGC_MDL139` v0101:

| 函式 | 律 |
|---|---|
| `vrn_report_dirs(spec, given)` | `--dir > user.vrn_dir > 冊 dir_default`,**incoming 一律併入** |
| `vrn_dir_with_reports(spec, given)` | 取**有報告件的**那個夾,回 `(夾, 逐夾狀況)`;全無 → `None` |
| `mega_db(explicit, via, home)` | 主路徑 → 替根,回 `(路徑, 因由)` |

`CGC_MDL141` v0107 的 `_report_dirs` / `_mega_db` 改成**轉呼叫**;
舊版 MDL139 掛上來時退本地實作**並印因由**(零回歸)。

`vrn_dir_with_reports` 取的是「**有件的**」而不是「存在的」那個夾——
`input_reports` 可能存在但是空的,而檔全在 `incoming`;
**指到空夾等於什麼都沒跑還報成功。**

### 實測(重現工作站佈局:報告只在 incoming、input_reports 不存在)

```
MDL139 v0100 → ok=False  state=NEED_DIR
MDL139 v0101 → ok=True   state=READY   --dir → incoming
```

### 自審三條

**① 檢數又是手寫。** MDL139 的 `10 - len(fails)` ——第五支同病,改成真的數。

**② 新檢 ⑫ 的判準恆為真。** 第一版寫

```python
(_db is None) == (not _why.startswith("主路徑缺→替根庫") and _db is None)
```

`_db` 不是 None 時左邊 False、右邊也 False → **恆真**。而這正是它能活到今天的原因:
**沙盒的主路徑剛好有庫,工作站沒有**——「跑得到就算過」的檢在沙盒永遠綠,
替根那一支**從來沒被驗過**。改成把「皆缺 / 只有替根 / 主路徑也有」三條分支的
佈局都造出來各走一遍,並讓 `mega_db` 收 `via`/`home` 注入參數使它測得起來。

**③ 新檢 ⑭ 自己 match 自己。** 第一版拿「原始碼裡還有沒有『同 MDL139 dir 參數』
這串字」當證據——而**檢自己的敘述文字就含著那串字**,恆為假
(與 `SUP_MDL746` 檢 ② 同一個陷阱)。改成真的把一個沒有那兩支函式的假 MDL139
換上去,走退路一遍。

### 落地

| 件 | 版 | 檢 |
|---|---|---|
| `CGC_MDL139_InputConsole` | v0101 | 十二檢 12/12 |
| `CGC_MDL141_ClosingGate` | v0107 | 十四檢 14/14 |
| `CGC_MDL064_SelftestGrid` | v0286 | 兩站改名 |
