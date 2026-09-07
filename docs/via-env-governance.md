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
