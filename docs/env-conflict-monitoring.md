# 監測環境衝突 — Local Free Libs Top 8(uv 加速 + 清華/阿里鏡像 + 官方兜底)

> 一鍵快篩:`bash scripts/envcheck.sh`(Linux/macOS/WSL)或 `.\scripts\envcheck.ps1`(Windows)。
> 秒級出結果;鏡像自動探測,失聯自動切官方 PyPI。

## 一、Top 8 名單(免費、本地執行、以速度排序)

實測環境:uv 0.8.17 / Python 3.11 / 快取命中後之典型值。

| # | 工具 | 用途(衝突監測角度) | 實測速度 | 一鍵指令 |
|---|------|--------------------|----------|----------|
| 1 | **uv** | 已裝套件相容性檢查、整組需求解析預演、依賴樹;本身即安裝加速器 | `uv pip check` **0.4ms**(7 套件) | `uv pip check --python .venv/bin/python` |
| 2 | **pipdeptree** | 依賴樹 + 衝突警告 + 反向查詢(誰依賴它) | **0.7s**(uvx 快取後) | `uvx pipdeptree --python <py> --warn fail` |
| 3 | **pip check** | pip 內建相容性檢查,零安裝 | 百 ms 級 | `python -m pip check` |
| 4 | **deptry** | Rust 核心;掃缺依賴(DEP001)/未用依賴(DEP002)/幽靈依賴(DEP003)/誤置(DEP004) | **0.6s** | `uvx deptry .` |
| 5 | **pipgrip** | PubGrub 解析器;**裝前**衝突預測,不落地安裝 | **2.9s** | `uvx pipgrip --tree "torch" "numpy==1.26.4"` |
| 6 | **johnnydep** | 裝前 metadata 需求樹預檢(要求哪些版本、依賴多深) | **2.0s** | `uvx johnnydep <pkg> --fields name version_latest requires` |
| 7 | **pip-tools** | `pip-compile` 鎖定;衝突於編譯期現形,產出環境「身分證」 | 視需求規模 | `uvx --from pip-tools pip-compile --dry-run requirements.txt` |
| 8 | **pip-check-reqs** | `pip-missing-reqs`/`pip-extra-reqs`:程式碼 import vs 需求清單漂移 | 秒級 | `pip-missing-reqs --requirements-file=requirements.txt .` |

加碼(不佔 Top 8 名額):
- **micromamba dry-run**(C++ SAT Solver):conda 生態的極速衝突預演——見
  `VeritasIntelligenceAnalytics/supportive modules/Invoke-VIA-MicromambaResolver.ps1`
  與橋接碼 `VIA_MambaBridge_v0100.py`(結果直接併入 VIA_EnvManager 衝突報告)。
- **pip-audit / safety**:安全漏洞掃描(CVE 面,非版本衝突面)。

一鍵安裝 Top 8(2/4/5/6/7/8 項):

```bash
uv pip install -r requirements-envcheck.txt          # 自動走 uv.toml 鏡像鏈
pip install -r requirements-envcheck.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 二、鏡像鏈:清華 → 阿里 → 官方 PyPI 兜底

### uv(本 repo 已內建 `uv.toml`)

倉庫根目錄的 [`uv.toml`](../uv.toml) 已定義索引鏈。uv 採 **first-index** 策略:
逐一查詢,前面的鏡像**查無該套件**才往下走;官方 PyPI 標記 `default = true`
永遠排最後 = **官方兜底導入**(同時保有防依賴混淆的保守行為)。

臨時覆寫(不吃設定檔):

```bash
UV_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple https://mirrors.aliyun.com/pypi/simple/" \
UV_DEFAULT_INDEX="https://pypi.org/simple" uv pip install <pkg>

# 海外 CI / 鏡像失聯:整條改走官方
UV_NO_CONFIG=1 UV_DEFAULT_INDEX="https://pypi.org/simple" uv pip install <pkg>
```

> 注意:鏡像**失聯**(連線逾時)與**查無套件**(404)不同——前者會讓 uv 直接報錯。
> `scripts/envcheck.sh` / `envcheck.ps1` 已內建 3 秒探測,失聯自動降級,不需手動切換。
> 鏡像有同步延遲(清華/阿里通常 5 分鐘~數小時);剛發佈的新版本查不到時,
> 用 `UV_NO_CONFIG=1` 走官方,或等鏡像同步。

### pip(全域設定)

```ini
# Linux/macOS: ~/.pip/pip.conf 或 ~/.config/pip/pip.conf
# Windows:     %APPDATA%\pip\pip.ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
extra-index-url = https://mirrors.aliyun.com/pypi/simple/
                  https://pypi.org/simple
timeout = 15
```

或指令式:`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`

## 三、加速器(要快)

| 加速器 | 作用 | 用法 |
|--------|------|------|
| **uv 本體** | Rust 解析器 + 平行下載 + 全域快取,較 pip 常見 10–100× | 以 `uv pip …` 取代 `pip …` |
| **uvx 工具快取** | 檢測工具免安裝、首跑後毫秒級喚起,不污染目標環境 | `uvx pipdeptree …` |
| **全域快取重用** | 多環境共用 wheel 快取,重建環境近乎零下載 | `uv cache dir` / `uv cache prune` |
| **硬連結安裝** | 同機多 venv 共用檔案,省磁碟省時間 | `UV_LINK_MODE=hardlink`(預設值,跨磁碟時改 `copy`) |
| **平行下載數** | 大包(torch 等)提速 | `UV_CONCURRENT_DOWNLOADS=8`(預設已高;弱網可調低) |
| **鏡像 CDN** | 清華/阿里在中港台大幅降低延遲與斷流 | 見上節 |
| **micromamba SAT** | C++ 解算器做 conda 生態 dry-run,比 pip 模擬快數十倍 | `Invoke-VIA-MicromambaResolver.ps1 -TargetEnv via_core` |
| **ccache** | 需編譯 C-ext 的環境重建省 ~80% 編譯時間 | 系統層安裝後自動生效 |

## 四、envcheck 指令總表

| 指令 | 內容 | 典型耗時 |
|------|------|----------|
| `envcheck.sh`(=`fast`) | uv pip check + pipdeptree 衝突警告 | **~1s** |
| `envcheck.sh full` | fast + deptry + pip-check-reqs + 整組需求解析預演 | ~10s |
| `envcheck.sh tree` | 完整依賴樹 | ~1s |
| `envcheck.sh why <pkg>` | 反查誰依賴 `<pkg>`(排查「A 升級 B 就壞」) | ~1s |
| `envcheck.sh resolve <spec…>` | 裝前衝突預測(pipgrip,不動環境) | 3s+ |
| `envcheck.sh info <pkg>` | 裝前需求預檢(johnnydep) | 2s+ |
| `envcheck.sh lock [檔]` | pip-compile 解析預演 | 視規模 |
| `envcheck.sh setup` | `uv venv .venv` + 依 requirements.txt 安裝 | 視規模 |
| `envcheck.sh doctor` | 三鏡像連通性(含延遲)+ uv/python/快取體檢 | ~1s |

環境變數:`ENVCHECK_PY`(目標直譯器)、`ENVCHECK_INDEX=auto|tsinghua|aliyun|official`、
`ENVCHECK_NO_MUTATE=1`(full 模式禁止在目標環境裝檢測工具)。
Windows 同名參數:`.\scripts\envcheck.ps1 <mode> [target…]`。

檢多個 via_ 環境:

```bash
for py in ~/envs/via_*/bin/python; do ENVCHECK_PY="$py" bash scripts/envcheck.sh; done
```

```powershell
Get-ChildItem C:\Users\tonyk\envs\via_* | ForEach-Object {
  $env:ENVCHECK_PY = "$($_.FullName)\Scripts\python.exe"; .\scripts\envcheck.ps1 fast
}
```

## 五、與 VIA 體系整合(監測迴路)

```
VIA_EnvManager.py scan ──────────────┐  (uv pip check / pip check / import probe)
Invoke-VIA-MicromambaResolver.ps1 ───┤  (SAT dry-run → %TEMP%\via_mamba_conflict_<env>.json)
scripts/envcheck.{sh,ps1} ───────────┤  (Top 8 快篩,人工/排程皆可)
                                     ▼
        python VIA_MambaBridge_v0100.py merge
                                     ▼
        _via_envmanager_output/VIA_EnvManager_ConflictReport.json(只增不減、去重)
        _via_envmanager_output/VIA_EnvManager_History.jsonl(存證)
```

- 橋接碼**不修改** `VIA_EnvManager.py` 核心與 `def_scan_all_envs()`;純外掛合併,
  衝突格式對齊 `def_EnvConflictRecord`(env_name / severity / category / detail / related_packages)。
- 環境分配藍圖(5D 分類 × 25 個 via_ 環境)見
  [`docs/via-env-matrix-5d.md`](via-env-matrix-5d.md) 與機器可讀之
  `VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Env_Matrix_5D_v0100.json`。
