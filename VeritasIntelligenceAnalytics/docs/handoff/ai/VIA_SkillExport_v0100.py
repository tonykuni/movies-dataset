#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
r"""VIA_SkillExport v0100 — 技能引擎:三層漸進載入 · 10 技能登錄表 · /export-skill(操作員 2026-11-08 令)。

操作員貼上「Claude Cowork 超級版 v2.0」與「Manus 超級版 v2.0」兩份規格,NEXT 指定:
「兩邊各丟同一指令 `/export-skill /ast-diag` 作首測,比對產出的 SKILL.md 與 scripts
是否都過 Celeritas 三檢,過則把 10 技能全部匯出並一次登錄 VSKE。」

本支就是那個 `/export-skill`,以及它要過的那三檢。

三層漸進載入(LAW-7;本支真的分層,不是說說):
  Tier1  索引   `registry` 只印 slash / description / 分類 / 觸發 / ↔加速器 —— 常駐用這層
  Tier2  SOP    `sop <slash>` 才載入該技能四段(Objective · Pre-flight · SOP · Output&Rollback)
  Tier3  資源   scripts/ references/ assets/ —— 只有 `export` 產檔時才生成/掛載
  `registry --depth` 可量測三層各自的字元數,證明分層真的省(不是宣稱省)。

動詞:
  registry [--json]        Tier1 索引:10 列表(Slash | Skill | Category | Trigger | ↔Accel | Status)
  sop <slash>              Tier2:只載入一個技能的四段 SOP
  export <slash> [--out D] 產出官方結構 SKILL.md + scripts/ + references/ + assets/
  export-all [--out D]     10 技能全匯出
  check <技能夾…>          三檢:① 語法剖析 ② 借用函式自帶預設 ③ 路徑全引號(+ PY 骨架規則)
  vske [--apply]           VSKE 登錄冊(只增;--apply 才寫檔)
  tokens                   以本倉真檔實測骨架卡 vs 整檔的位元組差(省 Token 不靠宣稱)
  all                      registry → export-all → check → vske → tokens
  --selftest               夾具自測(零網路 · 只寫沙盒)

誠實規矩(照 L65 / LAW-7 與本倉收尾律):
  * **不產 .ps1**。CLAUDE.md 禁改 .ps1(L70),且鬆散 .ps1 從不提交 —— 所以匯出的 scripts/
    一律是 Python。PS 的八段式 / 引號 / 借用函式規則保留成**唯讀驗證器**(`check --ps <檔>`),
    給操作員 Windows 側自己寫的 PS 用,本支不代寫、不代改。
  * 容器沒有 `pwsh`,所以 PowerShell `Parser.ParseFile` 這一檢在這裡**做不到**,一律回
    `UNAVAILABLE`(灰),**不算通過也不算失敗**;只有真有 pwsh 時才會真剖析。
    .ps1 在無 pwsh 下只做文字剖析,並在收據上寫明「文字剖析,不是 Parser.ParseFile」。
  * Python 那一檢是**真的 AST 驗**:ast.parse + 走訪,不是字串比對。
  * 10 技能一律標「↔ Celeritas 加速器」對應,**禁止重寫輪子**:技能是組合既有加速器的 SOP,
    不是另一份實作。對應不上的技能照實標 `UNMAPPED`,不假裝有。
  * 五系統對等獨立:本支只讀各系統自報值,不改他系統正本 / 冊 / 號 / 檔。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_ID = "via.skill.export/1"
VSKE_NAME = "VIA_VSKE_SkillRegistry_v0100.json"
KIT_LAW = "L70"  # 禁改 .ps1


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def via_root(start: Path | None = None) -> Path:
    p = (start or Path(__file__)).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[2]


# ═══════════════════════════════════════════════════════════════════════════
# Tier1 · 10 技能登錄表(常駐索引:只有這層的欄位會被 registry 讀)
# 每筆的 sop 欄是 Tier2,只有 sop()/export() 會碰它。
# ═══════════════════════════════════════════════════════════════════════════
SKILLS: list[dict] = [
    {
        "slash": "/ast-diag",
        "name": "ast-driven-diagnosis",
        "category": "A 開發自動化",
        "trigger": "結構分析 / 修 bug / 跨 PS·PY 注入",
        "accel": ["01", "03", "06", "13"],
        "desc": "AST 摘要 + 錨點外科注入 + 自動回滾,防 hydra 回歸",
        "sop": {
            "objective": (
                "用 AST(不是字串取代)定位要改的那一個定義,外科式注入,並保留可回滾的前後指紋。"
                "目標是修一處不弄壞九處 —— 九頭龍回歸的來源幾乎都是字串取代改到同名的別處。"
            ),
            "preflight": [
                "先 `read` 骨架卡拿定義樹,不整檔讀(L65 ①)。",
                "改薄尾家族前先 `chain <家族名>`,確認誰是本體、誰蓋了誰。",
                "`ast.parse` 必須先乾淨;不乾淨先修語法,不要在壞樹上注入。",
                "記下目標檔的 sha256 作為回滾指紋。",
            ],
            "steps": [
                "`read <檔>` → 取定義樹(行號 / 簽章 / 首行說明)。",
                "`slice <檔> <名|Class.method>` → 只取要改的那一個定義。",
                "在 AST 上找錨點:用 `ast.walk` 比對 `FunctionDef.name` / `ClassDef.name` + `lineno`,"
                "**不用 regex 找定義**(同名會中錯的那一個)。",
                "注入:只改錨點那一段的行區間,其餘位元組不動。",
                "注入後立刻重跑 `ast.parse` + `compile`(ast 過但 compile 不過是真的會發生:"
                "例如橋注在 `from __future__` 之前)。",
                "跑該檔的自測 / 該站 `test --full --only <站>`。",
            ],
            "output_rollback": [
                "輸出:改動的定義名 + 行區間 + 前後 sha256 + 測試判決。",
                "回滾:前 sha256 對不上就還原原檔;**只增不減**,正本已發布就改出新版號檔而非原地改。",
                "失敗 3 輪未過 → RED 交回 + 一行診斷,不要第 4 輪。",
            ],
        },
    },
    {
        "slash": "/token-state",
        "name": "token-optimized-state",
        "category": "A 開發自動化",
        "trigger": "多 Agent 交接 / 大 repo / 資料 schema",
        "accel": ["02", "12"],
        "desc": "SHA-256 檔案狀態雜湊 + Parquet/DuckDB 零拷貝 metadata,不讀原文",
        "sop": {
            "objective": "用指紋代替原文傳遞狀態:後手只比 hash 就知道哪些變了,不用把檔案再讀一遍。",
            "preflight": [
                "先確認要納管的檔案集合(清冊),讀不到的目錄保留 UNKNOWN,不當成 0。",
                "Parquet / DuckDB 在不在:不在就退回純 JSON 指紋,並標明退回。",
            ],
            "steps": [
                "對每個檔算 sha256,連同 size / mtime 寫成 `{path: {sha, size, mtime}}`。",
                "資料集只讀 metadata(欄名 / 列數 / 型別),**不讀列**。",
                "交接時只送指紋表與變更清單(新增 / 改變 / 消失)。",
                "後手用同一支重算,比對差集。",
            ],
            "output_rollback": [
                "輸出:指紋表 + 三個差集的數量與清單。",
                "回滾:指紋表只增不覆蓋 —— 新一輪寫新檔,舊指紋留著當基準。",
                "誠實:讀不到的路徑列 UNKNOWN,不寫 0,也不從上一輪沿用。",
            ],
        },
    },
    {
        "slash": "/self-heal",
        "name": "self-healing-automation",
        "category": "A 開發自動化",
        "trigger": "寫腳本 / CLI / 批次 / 部署",
        "accel": ["05", "16", "17", "18", "20"],
        "desc": "單檔 PS7/PY:進度列、即時日誌、pre-flight AST、原子回滾",
        "sop": {
            "objective": "交付一支能自己跑完、跑壞能自己退回原狀、跑的時候看得見進度的單檔。",
            "preflight": [
                "參數置頂、功能分段;禁 `input()`(無人值守會卡死)。",
                "有 `__main__`;無 `__main__` 的腳本禁 `--help`(會把整個流程跑起來)。",
                "寫入前先算目標的 sha256,作為原子回滾的依據。",
            ],
            "steps": [
                "pre-flight:先 `ast.parse` 自己要產出的程式碼,過不了就不落檔。",
                "每階段印一行判決(不是進度條噴屏),時間與 rc 都印。",
                "寫檔走 `tmp → fsync → replace` 的原子換檔,不原地截斷。",
                "任何階段 rc != 0 → 停在那裡並印原因,**不要繼續往下假裝成功**。",
            ],
            "output_rollback": [
                "輸出:階段 × 燈 × rc × 耗時的收據 JSON。",
                "回滾:把 tmp 丟掉即可,原檔從未被動過。",
                "誠實:rc 2(部分成功)是 YELLOW,不是 GREEN。",
            ],
        },
    },
    {
        "slash": "/local-env",
        "name": "local-first-virtualization",
        "category": "A 開發自動化",
        "trigger": "環境 / 依賴 / 本機套件",
        "accel": ["21", "22", "23", "24", "25"],
        "desc": "隔離 venv(遵 VIA_EnvManager / VEGN 規則)、零外部依賴優先 · detect-only",
        "sop": {
            "objective": "要的套件就位,且**不碰 VIA 既有環境**。缺的交給 VCGC 安裝閘,不自己 pip。",
            "preflight": [
                "VIA 環境內一律 **detect-only**:只回報缺什麼,不安裝(本倉政策)。",
                "安裝只經 VCGC `via-envgov tools --apply --approve`,不走 pip。",
                "上傳 / 下載來的東西放自己的空目錄,用 `python -I` 跑(隔離 user site)。",
            ],
            "steps": [
                "列出要用的套件與**實際找到的版本**(找不到就 ABSENT,不是舊版)。",
                "判斷「有就用、沒有就自己算」:能純標準庫完成的就不要求裝套件。",
                "需要隔離時建自己的 venv,路徑寫進收據,不改 VIA 環境變數。",
                "退出時還原動過的環境變數。",
            ],
            "output_rollback": [
                "輸出:套件 × 需要 / 實際 / 判決 的矩陣 + 缺件清單。",
                "回滾:venv 整夾刪掉即可;VIA 環境從未被動。",
                "誠實:`python -I` 看不到 user site(duckdb 常裝在那),所以 -I 下的缺件要標明是隔離造成的。",
            ],
        },
    },
    {
        "slash": "/doc-extract",
        "name": "hybrid-layout-extraction",
        "category": "B 資料 · 量化",
        "trigger": "PDF / 財報 / 複雜表格",
        "accel": ["19"],
        "desc": "多引擎 OCR + 版面框 + 表格重建 → Parquet/DuckDB",
        "sop": {
            "objective": "把 PDF 的值取出來且**能指回原文位置**:頁碼 + 區域 + 原字串,不只給數字。",
            "preflight": [
                "先確認可用的讀取器(layout / pdfplumber / OCR)各自版本;缺的標 ABSENT。",
                "同一值要有第二讀法可交叉;只有一條讀法的值標 UNVERIFIED。",
            ],
            "steps": [
                "版面框先切:表格區 / 正文區分開,不要讓正文混進表格。",
                "表格重建:表頭(可能雙行)→ 欄對映 → 值;轉置表要走第三讀法。",
                "每個值帶 `source`(檔 / 頁 / 區域 / 原字串)。",
                "落 Parquet / DuckDB,鍵要能冪等(重跑不重複)。",
            ],
            "output_rollback": [
                "輸出:值 + 來源 + 讀法 + 驗證狀態;FAIL / REVIEW 分開列。",
                "回滾:重複鍵進 quarantine,不覆蓋已驗證值。",
                "誠實:讀不到就是讀不到 —— **不補零、不推測、不以鄰值填**。",
            ],
        },
    },
    {
        "slash": "/data-pipe",
        "name": "high-throughput-data-pipeline",
        "category": "B 資料 · 量化",
        "trigger": "大表 / 時序 / ETL",
        "accel": ["19"],
        "desc": "Polars Lazy + DuckDB 零拷貝;禁逐列迴圈(numba 缺席時照實標)",
        "sop": {
            "objective": "大表用集合運算做完,不要逐列迴圈;增量只算新的那一段。",
            "preflight": [
                "確認 polars / duckdb / pyarrow 在不在;缺的退回 pandas 或純標準庫並標明。",
                "**numba 本容器缺席** → 不宣稱 JIT 加速,照實標 ABSENT。",
                "增量的鍵要先定好(本倉慣例:`(id, ts, run)` 這類複合鍵)。",
            ],
            "steps": [
                "讀用 Lazy / scan,不要先 collect 整張。",
                "增量用反連接(`WHERE NOT EXISTS`)只插新列,**append-only**。",
                "寫完要把整個合併後的庫對帳回去(只送 added 會讓 JSON 與 DuckDB 永久分歧 —— 這是實際踩過的坑)。",
                "禁 `for row in df.iterrows()` 這類逐列迴圈。",
            ],
            "output_rollback": [
                "輸出:列數(前 / 後 / 新增)+ 耗時 + 來源別計數。",
                "回滾:append-only 的庫不刪;錯的那一輪用 run 鍵隔離。",
                "誠實:庫寫不進去時**總燈不能綠**(假綠是踩過的坑)。",
            ],
        },
    },
    {
        "slash": "/quant-roll",
        "name": "dynamic-rolling-analytics",
        "category": "B 資料 · 量化",
        "trigger": "指標 / 模型 / 估值 / 門檻",
        "accel": ["11"],
        "desc": "動態 rolling CRITERIA;台債 10y 為 rf;乾淨資金流動比排除當沖與 2330 非當沖扭曲;禁硬編碼靜態值",
        "sop": {
            "objective": "門檻隨資料滾動算出來,不是寫死的常數;每個指標的視窗與缺值政策都要寫明。",
            "preflight": [
                "rf = **台債 10y**(不是美債,不是 0)。",
                "成交量值依既定政策**扣除當沖**;**2330 單獨處理**(非當沖扭曲)。",
                "價格一律用 **ADJ**;歷史值 / 預估值 / 來源日期 / 調整依據分開存。",
            ],
            "steps": [
                "指標身分與參數分層:5/10/20/60/120/240 天是**同一指標的參數**,不是六個指標。",
                "門檻用 rolling 分位 / z-score 當期算,**禁硬編碼**。",
                "缺值政策寫明(前推 / 跳過 / 標 GRAY),不以 0 代替。",
                "結果要有獨立驗算(第二條路算同一個值)。",
            ],
            "output_rollback": [
                "輸出:指標 × 公式版本 × 視窗 × 缺值政策 × 驗算判決。",
                "回滾:公式改版出新版號,舊版結果留著可比。",
                "誠實:Unit 過不能讓 Result 直接變綠。",
            ],
        },
    },
    {
        "slash": "/entity-norm",
        "name": "entity-ticker-normalization",
        "category": "B 資料 · 量化",
        "trigger": "代碼清洗 / 跨平台對映",
        "accel": ["08"],
        "desc": "台股 4 位數首位非零、跨平台共根;Bloomberg 格式 XXXX TT,不接 Equity",
        "sop": {
            "objective": "同一家公司在各平台的代碼對得起來,且不把上市上櫃搞混。",
            "preflight": [
                "台股本體代碼 = **4 位數、首位非零**。",
                "Bloomberg 寫 `XXXX TT`,**後面不接 Equity**。",
                "yfinance 上市 `.TW`、上櫃 `.TWO` —— 判錯會整批抓不到。",
            ],
            "steps": [
                "先取共根(4 位數字),再按平台加後綴。",
                "上市 / 上櫃由官方名單判定,不猜。",
                "名稱一併帶(Ticker 與 Name 緊接),避免只有號碼無從核對。",
                "對不上的進例外表,逐筆留原字串。",
            ],
            "output_rollback": [
                "輸出:共根 × 各平台代碼 × 判定來源;例外表另列。",
                "回滾:對映表只增,改判出新版。",
                "誠實:判不出上市上櫃就標 UNKNOWN,不預設 .TW。",
            ],
        },
    },
    {
        "slash": "/canvas-zen",
        "name": "minimalist-canvas-design",
        "category": "C 視覺 · 治理",
        "trigger": "圖表 / U/I / 報告",
        "accel": ["09"],
        "desc": "留白、丹青水墨、Seaborn muted、幾何符號、三列標頭;燈四色與 typekit 以視覺鎖定為準,不得覆蓋",
        "sop": {
            "objective": "所有 VIA 頁看起來是同一個系統出的。美學讓位給鎖定:鎖定的色與字不准覆蓋。",
            "preflight": [
                "色彩一律 `var(--vl-*)`,**由 Atlas 鎖定正本抽出**,不手抄 hex。",
                "燈四色 紅(慢閃)/黃/綠/灰 以 `VIA_UI_FormatLock` 為準;黃格必亮黃燈。",
                "三列標頭:VERITAS INTELLIGENCE ANALYTICS / 子系統 / 中文標語。",
            ],
            "steps": [
                "掛上共用 kit(同一份位元組),不要每頁自己寫一套色。",
                "矩陣:淺色小字、緊湊自適應、**燈是第一欄**。",
                "手機側邊槽 `max(16px, env(safe-area-inset-*))`;頁面不橫向捲動。",
                "靜態單檔、零外連、無伺服器。",
            ],
            "output_rollback": [
                "輸出:頁 + 鎖定閘五判定的收據(含連到的樣式表真的打開驗過)。",
                "回滾:鎖定正本位元組改了就重抽 kit,頁跟著重產。",
                "誠實:缺資料畫骨架不畫線,**絕不畫假 K 線、不編價格**。",
            ],
        },
    },
    {
        "slash": "/ssot-gov",
        "name": "ssot-filename-governance",
        "category": "C 視覺 · 治理",
        "trigger": "重構 / 參數登錄 / 跨子系統同步(庫 牘 觀 輔 理)",
        "accel": ["08", "26", "27", "28", "29", "30"],
        "desc": "功能性檔名為 SSOT,路由與 schema 同步只認檔名",
        "sop": {
            "objective": "檔名就是身分。新需求兩邊都要登(需求冊 + 對應工作流冊),少一邊就是治理破口。",
            "preflight": [
                "動 SSOT / 正則 / 同義字 / 編號 / 命名 / 註冊**前後各跑一次** `ssot panorama`。",
                "新需求必須同時登中央需求冊與相應 `VIA_Workflow_*_SSOT`(AGENTS.md 第 3 條)。",
                "新指令 / 新工作流步沒登盤點冊 = 黃(不是綠)。",
            ],
            "steps": [
                "出新版號檔,舊版不動(只增不減)。",
                "需求冊登 id / why / homes / workflow;工作流冊登 goal / 驗收 / steps / tests。",
                "盤點冊把每個新步對映到站。",
                "編號寫入後 `run CGC_MDL237_NumberingSystem audit` 必須 遺失 0 · 改身分 0 · 重號 0。",
            ],
            "output_rollback": [
                "輸出:冊版本 + 新增條目 + audit 三個 0。",
                "回滾:冊只增版,舊版留著;撞號保留原號另給候選識別碼,**不自動改正式編號**。",
                "誠實:`handoff` 綠只代表交接資料完整;驗收看 `closeout_lamp`。",
            ],
        },
    },
]

SLASH_INDEX = {s["slash"]: s for s in SKILLS}
NAME_INDEX = {s["name"]: s for s in SKILLS}

# Celeritas 加速器編號 → 名稱(只用來證明「對得上」,不重寫加速器本身)
ACCEL_MAP = {
    "01": "AST / 結構",
    "02": "狀態指紋",
    "03": "注入 / 錨點",
    "05": "腳本骨架",
    "06": "回滾",
    "08": "SSOT / 命名",
    "09": "視覺 / 模板",
    "11": "量化 / rolling",
    "12": "零拷貝 metadata",
    "13": "AST 覆蓋",
    "16": "進度列",
    "17": "即時日誌",
    "18": "原子寫檔",
    "19": "資料管線",
    "20": "pre-flight",
    "21": "環境偵測",
    "22": "venv",
    "23": "依賴盤點",
    "24": "版本鎖",
    "25": "安裝閘",
    "26": "庫",
    "27": "牘",
    "28": "觀",
    "29": "輔",
    "30": "理",
}


def resolve(slash: str) -> dict | None:
    key = slash if slash.startswith("/") else "/" + slash
    if key in SLASH_INDEX:
        return SLASH_INDEX[key]
    return NAME_INDEX.get(slash.lstrip("/"))


# ═══════════════════════════════════════════════════════════════════════════
# Tier1 · registry
# ═══════════════════════════════════════════════════════════════════════════
def tier_sizes() -> dict:
    """量測三層各自的字元數 —— 分層省 Token 要能算,不能只宣稱。"""
    t1 = 0
    t2 = 0
    for s in SKILLS:
        t1 += len(" | ".join([s["slash"], s["name"], s["category"], s["trigger"], s["desc"]]))
        t2 += len(json.dumps(s["sop"], ensure_ascii=False))
    return {"tier1_chars": t1, "tier2_chars": t2,
            "tier2_over_tier1": round(t2 / t1, 2) if t1 else None}


def registry_rows() -> list[dict]:
    rows = []
    for s in SKILLS:
        mapped = [a for a in s["accel"] if a in ACCEL_MAP]
        rows.append({
            "slash": s["slash"],
            "skill": s["name"],
            "category": s["category"],
            "trigger": s["trigger"],
            "accel": "/".join(s["accel"]) if mapped == s["accel"] else
                     ("/".join(s["accel"]) + " (UNMAPPED)"),
            "status": "READY" if mapped == s["accel"] else "UNMAPPED",
        })
    return rows


def cmd_registry(args) -> int:
    rows = registry_rows()
    sizes = tier_sizes()
    if args.json:
        print(json.dumps({"schema": SCHEMA_ID, "ts": utc(), "rows": rows, "tiers": sizes},
                         ensure_ascii=False, indent=2))
        return 0
    w = [max(len(r[k]) for r in rows + [{k: k.upper() for k in rows[0]}]) for k in
         ("slash", "skill", "category", "trigger", "accel", "status")]
    keys = ("slash", "skill", "category", "trigger", "accel", "status")
    head = "  ".join(h.upper().ljust(w[i]) for i, h in enumerate(keys))
    print("[Tier1 索引 · 10 技能登錄表] " + utc())
    print(head)
    print("  ".join("-" * w[i] for i in range(len(keys))))
    for r in rows:
        print("  ".join(str(r[k]).ljust(w[i]) for i, k in enumerate(keys)))
    print()
    print(f"[分層量測] Tier1 索引 {sizes['tier1_chars']} 字元 · "
          f"Tier2 全部 SOP {sizes['tier2_chars']} 字元 · "
          f"倍數 {sizes['tier2_over_tier1']}×(常駐只付 Tier1)")
    if args.depth:
        for s in SKILLS:
            print(f"  {s['slash']:<13} Tier2 {len(json.dumps(s['sop'], ensure_ascii=False)):>5} 字元")
    unmapped = [r["slash"] for r in rows if r["status"] != "READY"]
    print(f"[判決] READY {len(rows) - len(unmapped)}/{len(rows)}" +
          (f" · UNMAPPED {unmapped}" if unmapped else " · 全部對上 Celeritas 加速器"))
    return 0


def cmd_sop(args) -> int:
    s = resolve(args.slash)
    if not s:
        print(f"[RED] 不認識的技能:{args.slash};Tier1 有:{', '.join(SLASH_INDEX)}")
        return 1
    print(f"[Tier2 · 只載入這一個] {s['slash']}  {s['name']}")
    print(f"  分類 {s['category']} · 觸發 {s['trigger']} · ↔加速器 {'/'.join(s['accel'])}")
    print(f"\n① Objective\n  {s['sop']['objective']}")
    for title, key in (("② Pre-flight", "preflight"), ("③ SOP", "steps"),
                       ("④ Output & Rollback", "output_rollback")):
        print(f"\n{title}")
        for i, line in enumerate(s["sop"][key], 1):
            print(f"  {i}. {line}")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# Tier3 · export(官方結構 SKILL.md + scripts/ + references/ + assets/)
# ═══════════════════════════════════════════════════════════════════════════
def skill_md(s: dict) -> str:
    """SKILL.md = YAML frontmatter(name/description)+ 四段。"""
    accel = "/".join(s["accel"])
    desc = s["desc"].replace('"', "'")
    out = [
        "---",
        f"name: {s['name']}",
        f"description: {desc} 觸發:{s['trigger']}。",
        "---",
        "",
        f"# {s['slash']}  ·  {s['name']}",
        "",
        f"| 分類 | 觸發 | ↔ Celeritas 加速器 |",
        f"|---|---|---|",
        f"| {s['category']} | {s['trigger']} | {accel} |",
        "",
        "> 這個技能**組合既有加速器**,不重寫輪子。對應不上加速器的步驟會在 `check` 標 UNMAPPED。",
        "",
        "## ① Objective",
        "",
        s["sop"]["objective"],
        "",
        "## ② Pre-flight",
        "",
    ]
    for line in s["sop"]["preflight"]:
        out.append(f"- {line}")
    out += ["", "## ③ SOP", ""]
    for i, line in enumerate(s["sop"]["steps"], 1):
        out.append(f"{i}. {line}")
    out += ["", "## ④ Output & Rollback", ""]
    for line in s["sop"]["output_rollback"]:
        out.append(f"- {line}")
    out += [
        "",
        "## Tier3 資源",
        "",
        "| 路徑 | 什麼時候掛 |",
        "|---|---|",
        "| `scripts/` | 真要產檔 / 處理檔案時才掛 |",
        "| `references/` | 要查規則細節時才讀 |",
        "| `assets/` | 要出頁 / 出圖時才用 |",
        "",
        f"`scripts/` 一律是 Python:本倉 {KIT_LAW} 禁改 .ps1,鬆散 .ps1 也從不提交,",
        "所以 PowerShell 的規則在這裡是**唯讀驗證器**(`check --ps <檔>`),不代寫 PS。",
        "",
    ]
    return "\n".join(out) + "\n"


SCRIPT_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{slash} · {name} —— Tier3 腳本骨架(VIA 強制 PY 檔案規則)。

參數置頂、功能分段、禁 input()、有 __main__。
加速器以 graceful 方式載入:缺席時零行為變更,不假裝有加速。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

# ===== 參數置頂 =====
SKILL_SLASH = "{slash}"
SKILL_NAME = "{name}"
ACCEL_IDS = {accel!r}

# ===== 加速器橋(graceful) =====
try:
    import VeritasCeleritas_v1141 as vc
except Exception:  # 缺席零影響,照實記
    vc = None


def _shield(fn):
    """vc.shield 在時用它;不在時原樣回傳 —— 不假裝被護欄包過。"""
    if vc is not None and hasattr(vc, "shield"):
        return vc.shield(fn)
    return fn


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def register() -> str:
    """CeleritasKernel.register —— 有核心就登錄,沒有就回 ABSENT。"""
    if vc is not None and hasattr(vc, "CeleritasKernel"):
        try:
            vc.CeleritasKernel.register(SKILL_NAME)
            return "REGISTERED"
        except Exception as exc:
            return "REGISTER_FAILED: " + str(exc)[:80]
    return "ABSENT"


def run(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog=SKILL_NAME, description="{desc}")
    ap.add_argument("--json", action="store_true", help="收據以 JSON 印出")
    args = ap.parse_args(argv)
    receipt = {{
        "skill": SKILL_NAME,
        "slash": SKILL_SLASH,
        "accel": ACCEL_IDS,
        "accel_bridge": "PRESENT" if vc is not None else "ABSENT",
        "kernel": register(),
        "ts": utc(),
        "lamp": "GRAY",
        "why": "骨架:實作步驟見 SKILL.md ③ SOP;未實作前照實 GRAY,不報綠。",
    }}
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    else:
        for k, v in receipt.items():
            print(f"{{k:<13}} {{v}}")
    return receipt


@_shield
def main(argv: list[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def reference_md(s: dict) -> str:
    lines = [
        f"# {s['slash']} · 規則參考(Tier3)",
        "",
        "## ↔ Celeritas 加速器對應",
        "",
        "| 編號 | 加速器 |",
        "|---|---|",
    ]
    for a in s["accel"]:
        lines.append(f"| {a} | {ACCEL_MAP.get(a, 'UNMAPPED')} |")
    lines += [
        "",
        "## 這個技能不做什麼",
        "",
        "- 不重寫加速器已有的能力(禁止重做輪子)。",
        "- 不產 .ps1(本倉 " + KIT_LAW + ")。",
        "- 不把沒跑過的步驟寫成通過。",
        "",
        "## 收尾誠實律",
        "",
        "- 未知 / 缺席 → YELLOW 或 GRAY,**永不綠**。",
        "- 成功標記必須來自測試本身,不能由呼叫端代寫。",
        "- rc 2(部分成功)是 YELLOW。",
        "",
    ]
    return "\n".join(lines) + "\n"


def export_one(s: dict, out_root: Path) -> dict:
    d = out_root / s["name"]
    (d / "scripts").mkdir(parents=True, exist_ok=True)
    (d / "references").mkdir(parents=True, exist_ok=True)
    (d / "assets").mkdir(parents=True, exist_ok=True)

    md = skill_md(s)
    (d / "SKILL.md").write_text(md, encoding="utf-8")

    script = SCRIPT_TEMPLATE.format(
        slash=s["slash"], name=s["name"], accel=s["accel"],
        desc=s["desc"].replace('"', "'"),
    )
    script_path = d / "scripts" / (s["name"].replace("-", "_") + "_v0100.py")
    script_path.write_text(script, encoding="utf-8")

    (d / "references" / "rules_v0100.md").write_text(reference_md(s), encoding="utf-8")
    # assets/ 保持空的要有理由,不塞假檔
    (d / "assets" / "README.md").write_text(
        f"# {s['slash']} assets\n\n"
        "這個技能目前沒有需要隨身帶的靜態資產。出頁 / 出圖時才會在這裡放,\n"
        "而且色與字一律取自視覺鎖定 kit,不在這裡另存一份色票(會漂移)。\n",
        encoding="utf-8")

    return {
        "slash": s["slash"],
        "name": s["name"],
        "dir": str(d),
        "skill_md_sha256": sha256_text(md),
        "script": str(script_path),
        "script_sha256": sha256_text(script),
        "files": sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()),
    }


def cmd_export(args) -> int:
    s = resolve(args.slash)
    if not s:
        print(f"[RED] 不認識的技能:{args.slash}")
        return 1
    out = Path(args.out).resolve()
    info = export_one(s, out)
    print(f"[Tier3 匯出] {info['slash']} → {info['dir']}")
    for f in info["files"]:
        print(f"  {f}")
    print(f"  SKILL.md sha256 {info['skill_md_sha256'][:16]}…")
    print(f"  script   sha256 {info['script_sha256'][:16]}…")
    rep = check_skill_dir(Path(info["dir"]))
    print_check(rep)
    return 0 if rep["lamp"] == "GREEN" else 1


def cmd_export_all(args) -> int:
    out = Path(args.out).resolve()
    infos = [export_one(s, out) for s in SKILLS]
    reps = [check_skill_dir(Path(i["dir"])) for i in infos]
    bad = [r for r in reps if r["lamp"] != "GREEN"]
    print(f"[Tier3 全匯出] {len(infos)} 個技能 → {out}")
    for i, r in zip(infos, reps):
        print(f"  {r['lamp']:<6} {i['slash']:<13} {len(i['files'])} 檔 · "
              f"三檢 {r['passed']}/{r['applicable']} · N/A {r['na']} · 灰 {r['unavailable']}")
    print(f"[判決] GREEN {len(reps) - len(bad)}/{len(reps)}")
    return 0 if not bad else 1


# ═══════════════════════════════════════════════════════════════════════════
# 三檢(Celeritas)+ PY 骨架規則 —— Python 這邊是真的 AST 驗
# ═══════════════════════════════════════════════════════════════════════════
BORROWED_HINT = re.compile(r"\bvc\.|\bVIA_ACCEL\.|\bVeritasCeleritas")


def py_checks(path: Path) -> list[dict]:
    """對一支 Python 腳本跑 VIA 強制 PY 規則 —— ast 真走訪,不是字串比對。"""
    out: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    # ① 語法剖析(對應 PS 的 Parser.ParseFile)
    try:
        tree = ast.parse(text, filename=str(path))
        out.append({"check": "① 語法剖析 ast.parse", "state": "PASS", "note": "樹乾淨"})
    except SyntaxError as exc:
        out.append({"check": "① 語法剖析 ast.parse", "state": "FAIL",
                    "note": f"{exc.msg} @ line {exc.lineno}"})
        return out
    # ast 過但 compile 不過是真的會發生(橋注在 __future__ 之前)
    try:
        compile(text, str(path), "exec")
        out.append({"check": "①b compile", "state": "PASS", "note": "可編譯"})
    except Exception as exc:  # noqa: BLE001
        out.append({"check": "①b compile", "state": "FAIL", "note": str(exc)[:90]})

    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

    # 裝飾器豁免:名字出現在某個 decorator_list 裡、且只收一個位置參數的函式,
    # 那個參數就是「被裝飾的函式」,**本來就該是位置參數**,不該要求預設值。
    # 這個豁免是結構判定(真的被當裝飾器用 + 恰好一個位置參數),不是看名字放水。
    decorator_names: set[str] = set()
    for node in ast.walk(tree):
        for dec in getattr(node, "decorator_list", []) or []:
            if isinstance(dec, ast.Name):
                decorator_names.add(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorator_names.add(dec.attr)
            elif isinstance(dec, ast.Call):
                f = dec.func
                if isinstance(f, ast.Name):
                    decorator_names.add(f.id)
                elif isinstance(f, ast.Attribute):
                    decorator_names.add(f.attr)

    # ② 借用函式自帶預設:凡呼叫加速器的函式,其參數必須有預設值(加速器缺席也能叫)
    offenders = []
    exempt = []
    for name, node in funcs.items():
        src_seg = ast.get_source_segment(text, node) or ""
        if not BORROWED_HINT.search(src_seg):
            continue
        a = node.args
        positional = a.posonlyargs + a.args
        n_defaults = len(a.defaults)
        required = [p.arg for p in positional[: len(positional) - n_defaults]
                    if p.arg not in ("self", "cls")]
        if not required:
            continue
        if name in decorator_names and len(positional) == 1 and not a.vararg and not a.kwonlyargs:
            exempt.append(name)
            continue
        offenders.append(f"{name}({', '.join(required)})")
    note_ok = "借用加速器的函式參數都有預設"
    if exempt:
        note_ok += f"(裝飾器豁免:{', '.join(sorted(exempt))} —— 被裝飾的函式本來就是位置參數)"
    out.append({
        "check": "② 借用函式自帶預設",
        "state": "PASS" if not offenders else "FAIL",
        "note": note_ok if not offenders else "缺預設:" + "; ".join(offenders),
    })

    # ③ 路徑全引號:Python 裡等價的是「不要用裸字串拼路徑」→ 檢 os.system / shell=True
    risky = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            dotted = ""
            if isinstance(fn, ast.Attribute):
                dotted = fn.attr
            elif isinstance(fn, ast.Name):
                dotted = fn.id
            if dotted == "system":
                risky.append("os.system")
            for kw in node.keywords or []:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    risky.append("shell=True")
    out.append({
        "check": "③ 路徑全引號 / 不走 shell",
        "state": "PASS" if not risky else "FAIL",
        "note": "沒有 os.system / shell=True" if not risky else "有:" + ", ".join(sorted(set(risky))),
    })

    # PY 骨架規則
    has_main_guard = any(
        isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
        for n in tree.body
    )
    out.append({"check": "④ 有 __main__", "state": "PASS" if has_main_guard else "FAIL",
                "note": "" if has_main_guard else "無 __main__ 守衛"})

    input_calls = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id == "input"]
    out.append({"check": "⑤ 禁 input()", "state": "PASS" if not input_calls else "FAIL",
                "note": "" if not input_calls else f"有 {len(input_calls)} 處 input()"})

    main_node = funcs.get("main")
    decorated = bool(main_node and main_node.decorator_list)
    out.append({"check": "⑥ main 有護欄裝飾", "state": "PASS" if decorated else "FAIL",
                "note": "" if decorated else "main 沒有 shield 類裝飾"})

    has_register = "CeleritasKernel" in text and "register" in text
    out.append({"check": "⑦ CeleritasKernel.register", "state": "PASS" if has_register else "FAIL",
                "note": "" if has_register else "沒有核心登錄呼叫"})

    # 加速器缺席時必須 graceful,不能直接炸
    guarded = bool(re.search(r"try:\s*\n\s*import VeritasCeleritas", text))
    out.append({"check": "⑧ 加速器缺席 graceful", "state": "PASS" if guarded else "FAIL",
                "note": "" if guarded else "import 沒有 try 包覆,缺席會炸"})
    return out


def ps_checks(path: Path) -> list[dict]:
    """PowerShell 唯讀驗證器。沒有 pwsh 就誠實回 UNAVAILABLE,不當通過。"""
    out: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    pwsh = shutil.which("pwsh") or shutil.which("powershell")
    if pwsh:
        script = (
            "$ErrorActionPreference='Stop';"
            "$t=$null;$e=$null;"
            f"[void][System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$t,[ref]$e);"
            "if($e.Count -gt 0){$e | ForEach-Object { $_.Message } ; exit 1} else { exit 0 }"
        )
        try:
            r = subprocess.run([pwsh, "-NoLogo", "-NoProfile", "-Command", script],
                               capture_output=True, text=True, timeout=120)
            out.append({"check": "① Parser.ParseFile", "state": "PASS" if r.returncode == 0 else "FAIL",
                        "note": "樹乾淨" if r.returncode == 0 else (r.stdout or r.stderr)[:120]})
        except Exception as exc:  # noqa: BLE001
            out.append({"check": "① Parser.ParseFile", "state": "UNAVAILABLE",
                        "note": f"pwsh 跑不起來:{str(exc)[:80]}"})
    else:
        out.append({"check": "① Parser.ParseFile", "state": "UNAVAILABLE",
                    "note": "本容器沒有 pwsh —— 這一檢做不到,下面只做文字剖析,不是 ParseFile"})

    # ② 借用函式自帶預設(文字剖析:param 區塊裡的必填參數)
    bad_params = re.findall(r"\[Parameter\(\s*Mandatory\s*=\s*\$true", text, re.I)
    out.append({"check": "② 借用函式自帶預設(文字剖析)",
                "state": "PASS" if not bad_params else "FAIL",
                "note": "沒有 Mandatory 必填" if not bad_params
                        else f"有 {len(bad_params)} 個 Mandatory=$true,無人值守會卡住"})

    # ③ 路徑全引號(文字剖析:帶磁碟機代號或 $env: 的裸路徑)
    naked = []
    for m in re.finditer(r"(?<![\"'])(?:[A-Za-z]:\\|\$env:[A-Za-z_]+\\)[^\s\"';|)]+", text):
        naked.append(m.group(0)[:48])
    out.append({"check": "③ 路徑全引號(文字剖析)",
                "state": "PASS" if not naked else "FAIL",
                "note": "路徑都有引號" if not naked else "裸路徑:" + "; ".join(naked[:3])})

    # 禁用動作
    banned = {
        "Invoke-Expression": r"\bInvoke-Expression\b|\biex\b",
        "WebClient": r"\bNew-Object\s+System\.Net\.WebClient\b",
        "HKLM": r"\bHKLM:",
        "Stop-Process": r"\bStop-Process\b",
    }
    hits = [k for k, pat in banned.items() if re.search(pat, text, re.I)]
    out.append({"check": "④ 禁用動作", "state": "PASS" if not hits else "FAIL",
                "note": "沒有禁用動作" if not hits else "有:" + ", ".join(hits)})
    return out


def check_skill_dir(d: Path) -> dict:
    """對一個匯出的技能夾跑完整檢查。"""
    findings: list[dict] = []
    md = d / "SKILL.md"
    if not md.is_file():
        findings.append({"check": "SKILL.md 存在", "state": "FAIL", "note": "沒有 SKILL.md"})
    else:
        text = md.read_text(encoding="utf-8", errors="replace")
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        findings.append({"check": "SKILL.md YAML frontmatter",
                         "state": "PASS" if fm else "FAIL",
                         "note": "" if fm else "開頭沒有 --- 包住的 YAML"})
        if fm:
            body = fm.group(1)
            for key in ("name", "description"):
                ok = re.search(rf"^{key}:\s*\S", body, re.M)
                findings.append({"check": f"frontmatter {key}",
                                 "state": "PASS" if ok else "FAIL",
                                 "note": "" if ok else f"缺 {key}"})
        for i, title in enumerate(("① Objective", "② Pre-flight", "③ SOP",
                                   "④ Output & Rollback"), 1):
            ok = f"## {title}" in text
            findings.append({"check": f"四段 {title}", "state": "PASS" if ok else "FAIL",
                             "note": "" if ok else "缺這一段"})

    for sub in ("scripts", "references", "assets"):
        ok = (d / sub).is_dir()
        findings.append({"check": f"官方結構 {sub}/", "state": "PASS" if ok else "FAIL",
                         "note": "" if ok else "缺這個夾"})

    pys = sorted((d / "scripts").glob("*.py")) if (d / "scripts").is_dir() else []
    pss = sorted((d / "scripts").glob("*.ps1")) if (d / "scripts").is_dir() else []
    for p in pys:
        for f in py_checks(p):
            findings.append({**f, "check": f"[PY {p.name}] " + f["check"]})
    if pss:
        findings.append({"check": "不產 .ps1(" + KIT_LAW + ")", "state": "FAIL",
                         "note": f"有 {len(pss)} 支 .ps1;本倉禁改 .ps1,鬆散 .ps1 也不提交"})
        for p in pss:
            for f in ps_checks(p):
                findings.append({**f, "check": f"[PS {p.name}] " + f["check"]})
    else:
        findings.append({"check": "PS 三檢", "state": "N/A",
                         "note": f"沒有 .ps1(本倉 {KIT_LAW} 禁改 .ps1),所以 PS 那三檢不適用;"
                                 "PS 規則保留成 `check --ps <檔>` 的唯讀驗證器"})

    passed = sum(1 for f in findings if f["state"] == "PASS")
    failed = [f for f in findings if f["state"] == "FAIL"]
    na = sum(1 for f in findings if f["state"] == "N/A")
    unavail = sum(1 for f in findings if f["state"] == "UNAVAILABLE")
    applicable = passed + len(failed)
    lamp = "RED" if failed else ("YELLOW" if unavail else "GREEN")
    return {
        "schema": SCHEMA_ID, "ts": utc(), "dir": str(d), "skill": d.name,
        "findings": findings, "passed": passed, "failed": len(failed),
        "applicable": applicable, "na": na, "unavailable": unavail, "lamp": lamp,
        "why": [f"{f['check']}: {f['note']}" for f in failed],
    }


def print_check(rep: dict) -> None:
    print(f"\n[三檢 · {rep['skill']}] {rep['lamp']} · "
          f"通過 {rep['passed']}/{rep['applicable']} · N/A {rep['na']} · 灰 {rep['unavailable']}")
    for f in rep["findings"]:
        mark = {"PASS": "  ✓", "FAIL": "  ✗", "N/A": "  –", "UNAVAILABLE": "  ?"}[f["state"]]
        note = f" — {f['note']}" if f["note"] else ""
        print(f"{mark} {f['check']}{note}")


def cmd_check(args) -> int:
    if args.ps:
        p = Path(args.ps)
        if not p.is_file():
            print(f"[RED] 找不到 {p}")
            return 1
        print(f"[PS 唯讀驗證器] {p}")
        rep = ps_checks(p)
        for f in rep:
            mark = {"PASS": "  ✓", "FAIL": "  ✗", "UNAVAILABLE": "  ?"}[f["state"]]
            print(f"{mark} {f['check']} — {f['note']}")
        print("[提醒] 本支不改 .ps1(" + KIT_LAW + ");以上只是回報,不代修。")
        return 0 if not any(f["state"] == "FAIL" for f in rep) else 1

    worst = 0
    for d in args.dirs:
        rep = check_skill_dir(Path(d))
        print_check(rep)
        if rep["lamp"] == "RED":
            worst = 1
    return worst


# ═══════════════════════════════════════════════════════════════════════════
# VSKE 登錄冊(只增)
# ═══════════════════════════════════════════════════════════════════════════
def vske_payload(reps: list[dict] | None = None) -> dict:
    return {
        "schema": "via.vske.registry/1",
        "version": "v0100",
        "ts": utc(),
        "law": "只增不減:換版出新版號檔,舊條目不刪、不改身分",
        "tiers": tier_sizes(),
        "note": ("技能一律組合既有 Celeritas 加速器,不重寫輪子;"
                 f"scripts/ 只有 Python(本倉 {KIT_LAW} 禁改 .ps1)。"),
        "skills": [
            {
                "slash": s["slash"], "name": s["name"], "category": s["category"],
                "trigger": s["trigger"], "accel": s["accel"],
                "accel_names": [ACCEL_MAP.get(a, "UNMAPPED") for a in s["accel"]],
                "description": s["desc"],
                "sop_sha256": sha256_text(json.dumps(s["sop"], ensure_ascii=False, sort_keys=True)),
                "skill_md_sha256": sha256_text(skill_md(s)),
            }
            for s in SKILLS
        ],
        "checks": [{"skill": r["skill"], "lamp": r["lamp"],
                    "passed": r["passed"], "applicable": r["applicable"]}
                   for r in (reps or [])],
    }


def cmd_vske(args) -> int:
    payload = vske_payload()
    if args.apply:
        out = Path(args.out).resolve() / VSKE_NAME
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            print(f"[不覆蓋] {out} 已存在 —— 只增不減,要換版請出新版號檔")
            return 1
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[VSKE 登錄] 寫入 {out} · {len(payload['skills'])} 筆")
        return 0
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# tokens —— 省 Token 用本倉真檔實測,不宣稱
# ═══════════════════════════════════════════════════════════════════════════
def cmd_tokens(args) -> int:
    root = via_root()
    lock = root / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    if not lock.is_file():
        print(f"[YELLOW] 找不到鎖冊 {lock} —— 無法取全景工具,這一項照實灰,不估。")
        return 1
    try:
        tool = json.loads(lock.read_text(encoding="utf-8"))["token"]["path"]
    except Exception as exc:  # noqa: BLE001
        print(f"[YELLOW] 鎖冊讀不出 token.path:{exc}")
        return 1
    # 鎖冊裡的路徑是**相對倉根**寫的,不是相對 VIA 根 —— 兩個都試,找不到才黃。
    cands = []
    if Path(tool).is_absolute():
        cands.append(Path(tool))
    else:
        cands += [root.parent / tool, root / tool, Path(tool)]
    tool_path = next((c for c in cands if c.is_file()), None)
    if tool_path is None:
        print("[YELLOW] 鎖版工具不在,試過:" + " · ".join(str(c) for c in cands))
        return 1

    samples = sorted((root / "docs" / "handoff" / "ai").glob("VIA_*_v01*.py"))[-6:]
    if not samples:
        print("[YELLOW] 沒有取樣檔")
        return 1
    rows = []
    for p in samples:
        full = len(p.read_text(encoding="utf-8", errors="replace"))
        try:
            r = subprocess.run([sys.executable, str(tool_path), "read", str(p)],
                               capture_output=True, text=True, timeout=180,
                               cwd=str(root), env={**__import__("os").environ,
                                                   "VIA_FROM_VCGC": "YES"})
            card = len(r.stdout)
            ok = r.returncode == 0 and card > 0
        except Exception as exc:  # noqa: BLE001
            card, ok = 0, False
            print(f"  [!] {p.name} 卡片取不到:{str(exc)[:70]}")
        rows.append({"file": p.name, "full_chars": full, "card_chars": card,
                     "saved_pct": round(100 * (1 - card / full), 1) if (ok and full) else None})

    good = [r for r in rows if r["saved_pct"] is not None]
    print(f"[省 Token 實測] 工具 {tool_path.name} · 取樣 {len(rows)} 檔")
    print(f"{'檔':<34}{'整檔':>10}{'骨架卡':>10}{'省':>8}")
    for r in rows:
        s = f"{r['saved_pct']}%" if r["saved_pct"] is not None else "—"
        print(f"{r['file'][:33]:<34}{r['full_chars']:>10}{r['card_chars']:>10}{s:>8}")
    if good:
        tot_full = sum(r["full_chars"] for r in good)
        tot_card = sum(r["card_chars"] for r in good)
        print(f"\n[合計] 整檔 {tot_full} 字元 → 骨架卡 {tot_card} 字元 · "
              f"省 {round(100 * (1 - tot_card / tot_full), 1)}%(真測,非估)")
    else:
        print("\n[YELLOW] 一張卡都沒取到 —— 不給數字,照實灰")
    return 0 if good else 1


def cmd_all(args) -> int:
    rc = 0
    print("══ ① Tier1 索引 ══")
    rc |= cmd_registry(argparse.Namespace(json=False, depth=False))
    print("\n══ ② Tier3 全匯出 + 三檢 ══")
    rc |= cmd_export_all(argparse.Namespace(out=args.out))
    print("\n══ ③ VSKE 登錄冊 ══")
    out = Path(args.out).resolve()
    reps = [check_skill_dir(out / s["name"]) for s in SKILLS]
    payload = vske_payload(reps)
    vp = out / VSKE_NAME
    if not vp.exists():
        vp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[VSKE 登錄] {vp} · {len(payload['skills'])} 筆 · "
              f"GREEN {sum(1 for r in reps if r['lamp'] == 'GREEN')}/{len(reps)}")
    else:
        print(f"[不覆蓋] {vp} 已存在(只增不減)")
    print("\n══ ④ 省 Token 實測 ══")
    # 量不到就是量不到:這一段的燈**必須進總燈**,不能讓前三段的綠蓋過去(假綠是踩過的坑)。
    tok_rc = cmd_tokens(argparse.Namespace())
    tokens_lamp = "GREEN" if tok_rc == 0 else "YELLOW"
    lamps = {r["lamp"] for r in reps} | {tokens_lamp}
    agg = "RED" if "RED" in lamps else ("YELLOW" if "YELLOW" in lamps else "GREEN")
    print(f"\n[總燈] {agg}" +
          ("" if tokens_lamp == "GREEN" else "(④ 省 Token 實測量不到 → 總燈不給綠)"))
    return rc if agg != "RED" else 1


# ═══════════════════════════════════════════════════════════════════════════
# 自測(零網路 · 只寫沙盒)
# ═══════════════════════════════════════════════════════════════════════════
def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def ck(name: str, cond: bool, note: str = "") -> None:
        checks.append((name, bool(cond), note))

    tmp = Path(tempfile.mkdtemp(prefix="via_skillexport_"))
    try:
        # ── Tier1 ──
        rows = registry_rows()
        ck("Tier1 恰好 10 列", len(rows) == 10, f"實際 {len(rows)}")
        ck("Tier1 全部 READY(加速器都對上)",
           all(r["status"] == "READY" for r in rows),
           str([r["slash"] for r in rows if r["status"] != "READY"]))
        ck("slash 不重複", len({r["slash"] for r in rows}) == 10)
        ck("分類三組齊全",
           {s["category"][0] for s in SKILLS} == {"A", "B", "C"})

        sizes = tier_sizes()
        ck("分層真的有差(Tier2 比 Tier1 大)",
           sizes["tier2_chars"] > sizes["tier1_chars"] * 2,
           f"T1 {sizes['tier1_chars']} / T2 {sizes['tier2_chars']}")

        # ── Tier2 ──
        s = resolve("/ast-diag")
        ck("resolve 吃 slash", s is not None and s["name"] == "ast-driven-diagnosis")
        ck("resolve 吃無斜線", resolve("ast-diag") is s)
        ck("resolve 吃全名", resolve("ast-driven-diagnosis") is s)
        ck("resolve 不認的回 None", resolve("/nope") is None)
        for sk in SKILLS:
            assert set(sk["sop"]) == {"objective", "preflight", "steps", "output_rollback"}
        ck("10 個技能四段都齊", True)

        # ── Tier3 首測:/export-skill /ast-diag ──
        info = export_one(s, tmp)
        ck("匯出產生 SKILL.md", (Path(info["dir"]) / "SKILL.md").is_file())
        ck("匯出產生三個夾",
           all((Path(info["dir"]) / d).is_dir() for d in ("scripts", "references", "assets")))
        ck("匯出的 scripts 只有 .py",
           not list((Path(info["dir"]) / "scripts").glob("*.ps1")))

        rep = check_skill_dir(Path(info["dir"]))
        ck("/ast-diag 首測三檢 GREEN", rep["lamp"] == "GREEN", f"{rep['lamp']} {rep['why']}")
        ck("首測沒有 FAIL", rep["failed"] == 0, str(rep["why"]))
        ck("PS 三檢標 N/A 而不是通過",
           any(f["check"] == "PS 三檢" and f["state"] == "N/A" for f in rep["findings"]))
        names = [f["check"] for f in rep["findings"]]
        for want in ("① 語法剖析", "② 借用函式自帶預設", "③ 路徑全引號"):
            ck(f"三檢有「{want}」", any(want in n for n in names), str(names[:4]))
        for want in ("④ 有 __main__", "⑤ 禁 input()", "⑥ main 有護欄裝飾",
                     "⑦ CeleritasKernel.register", "⑧ 加速器缺席 graceful"):
            ck(f"PY 骨架規則有「{want}」", any(want in n for n in names))

        # 產出的腳本真的可以獨立跑(加速器缺席時 graceful)
        script = Path(info["script"])
        r = subprocess.run([sys.executable, "-I", str(script), "--json"],
                           capture_output=True, text=True, timeout=120)
        ck("產出的腳本 -I 跑得起來", r.returncode == 0, (r.stderr or "")[:120])
        try:
            receipt = json.loads(r.stdout)
        except Exception:
            receipt = {}
        ck("腳本收據標加速器缺席", receipt.get("accel_bridge") == "ABSENT", str(receipt)[:90])
        ck("腳本收據骨架期是 GRAY 不是 GREEN", receipt.get("lamp") == "GRAY", str(receipt.get("lamp")))
        ck("腳本收據 kernel 標 ABSENT 不假裝登錄", receipt.get("kernel") == "ABSENT",
           str(receipt.get("kernel")))

        # ── 三檢真的會抓錯(不是橡皮章)──
        bad = tmp / "bad-skill"
        (bad / "scripts").mkdir(parents=True)
        (bad / "references").mkdir()
        (bad / "assets").mkdir()
        (bad / "SKILL.md").write_text("# 沒有 frontmatter 也沒有四段\n", encoding="utf-8")
        (bad / "scripts" / "broken.py").write_text("def f(:\n  pass\n", encoding="utf-8")
        rbad = check_skill_dir(bad)
        ck("壞技能夾判 RED", rbad["lamp"] == "RED", rbad["lamp"])
        ck("抓到缺 frontmatter",
           any("frontmatter" in f["check"] and f["state"] == "FAIL" for f in rbad["findings"]))
        ck("抓到語法錯",
           any("語法剖析" in f["check"] and f["state"] == "FAIL" for f in rbad["findings"]))
        ck("抓到缺四段",
           any("四段" in f["check"] and f["state"] == "FAIL" for f in rbad["findings"]))

        # ② 借用函式自帶預設:真的要抓到缺預設的借用函式
        v = tmp / "vcheck"
        (v / "scripts").mkdir(parents=True)
        (v / "references").mkdir()
        (v / "assets").mkdir()
        (v / "SKILL.md").write_text(skill_md(s), encoding="utf-8")
        (v / "scripts" / "nodefault.py").write_text(
            "import VeritasCeleritas_v1141 as vc\n"
            "def borrow(a, b):\n"
            "    return vc.shield(a)\n"
            "if __name__ == '__main__':\n    pass\n", encoding="utf-8")
        rv = check_skill_dir(v)
        ck("抓到借用函式缺預設",
           any("借用函式自帶預設" in f["check"] and f["state"] == "FAIL" for f in rv["findings"]),
           str([f for f in rv["findings"] if "借用" in f["check"]])[:140])

        # 裝飾器豁免必須是窄的:單一位置參數但**沒被當裝飾器用**,照樣要 FAIL
        (v / "scripts" / "nodefault.py").unlink()
        (v / "scripts" / "shelly.py").write_text(
            "import VeritasCeleritas_v1141 as vc\n"
            "def looks_like_decorator(fn):\n"      # 一個位置參數,但沒人拿它當裝飾器
            "    return vc.shield(fn)\n"
            "if __name__ == '__main__':\n    pass\n", encoding="utf-8")
        rnarrow = check_skill_dir(v)
        ck("裝飾器豁免是窄的(沒被當裝飾器用就不豁免)",
           any("借用函式自帶預設" in f["check"] and f["state"] == "FAIL"
               for f in rnarrow["findings"]),
           str([f for f in rnarrow["findings"] if "借用" in f["check"]])[:150])

        # 真的被當裝飾器用,就該豁免
        (v / "scripts" / "shelly.py").write_text(
            "import VeritasCeleritas_v1141 as vc\n"
            "def guard(fn):\n"
            "    return vc.shield(fn) if hasattr(vc, 'shield') else fn\n"
            "@guard\n"
            "def main(argv=None):\n    return 0\n"
            "if __name__ == '__main__':\n    pass\n", encoding="utf-8")
        rdec = check_skill_dir(v)
        ck("真裝飾器得到豁免",
           any("借用函式自帶預設" in f["check"] and f["state"] == "PASS"
               for f in rdec["findings"]),
           str([f for f in rdec["findings"] if "借用" in f["check"]])[:150])
        ck("豁免有寫明理由",
           any("裝飾器豁免" in (f["note"] or "") for f in rdec["findings"]))

        # ③ shell=True / os.system 要抓到
        (v / "scripts" / "shelly.py").write_text(
            "import os, subprocess\n"
            "import VeritasCeleritas_v1141 as vc\n"
            "def go(x=1):\n"
            "    os.system('ls')\n"
            "    subprocess.run('ls', shell=True)\n"
            "    return vc\n"
            "if __name__ == '__main__':\n    pass\n", encoding="utf-8")
        rv2 = check_skill_dir(v)
        shell_f = [f for f in rv2["findings"]
                   if "路徑全引號" in f["check"] and f["state"] == "FAIL"]
        ck("抓到 os.system / shell=True", bool(shell_f), str(shell_f)[:140])

        # input() 要抓到
        (v / "scripts" / "asks.py").write_text(
            "import VeritasCeleritas_v1141 as vc\n"
            "def go(x=1):\n    return input('?') or vc\n"
            "if __name__ == '__main__':\n    pass\n", encoding="utf-8")
        rv3 = check_skill_dir(v)
        ck("抓到 input()",
           any("禁 input()" in f["check"] and f["state"] == "FAIL" for f in rv3["findings"]))

        # .ps1 出現就要判 FAIL(本倉禁改 .ps1)
        p = tmp / "psskill"
        (p / "scripts").mkdir(parents=True)
        (p / "references").mkdir()
        (p / "assets").mkdir()
        (p / "SKILL.md").write_text(skill_md(s), encoding="utf-8")
        (p / "scripts" / "x.ps1").write_text(
            "#Requires -Version 7.0\nSet-Location C:\\Users\\x\\Downloads\n", encoding="utf-8")
        rp = check_skill_dir(p)
        ck(".ps1 出現判 RED", rp["lamp"] == "RED", rp["lamp"])
        ck("有不產 .ps1 的那條 FAIL",
           any("不產 .ps1" in f["check"] and f["state"] == "FAIL" for f in rp["findings"]))
        ck("PS ParseFile 無 pwsh 時標 UNAVAILABLE 不是 PASS",
           any("Parser.ParseFile" in f["check"] and
               f["state"] in ("UNAVAILABLE", "PASS", "FAIL") for f in rp["findings"]))
        if not (shutil.which("pwsh") or shutil.which("powershell")):
            ck("本容器沒 pwsh → ParseFile 一律 UNAVAILABLE",
               any("Parser.ParseFile" in f["check"] and f["state"] == "UNAVAILABLE"
                   for f in rp["findings"]))
            ck("UNAVAILABLE 不計入通過數",
               rp["unavailable"] >= 1 and
               not any("Parser.ParseFile" in f["check"] and f["state"] == "PASS"
                       for f in rp["findings"]))
        ck("PS 裸路徑抓到",
           any("路徑全引號(文字剖析)" in f["check"] and f["state"] == "FAIL"
               for f in rp["findings"]))

        # ── 10 技能全匯出 ──
        out_all = tmp / "all"
        infos = [export_one(sk, out_all) for sk in SKILLS]
        ck("全匯出 10 夾", len(infos) == 10)
        reps = [check_skill_dir(Path(i["dir"])) for i in infos]
        ck("10 個技能三檢全 GREEN",
           all(r["lamp"] == "GREEN" for r in reps),
           str([(r["skill"], r["lamp"], r["why"]) for r in reps if r["lamp"] != "GREEN"])[:200])

        # 10 支產出的腳本都要能跑
        bad_runs = []
        for i in infos:
            rr = subprocess.run([sys.executable, "-I", i["script"], "--json"],
                                capture_output=True, text=True, timeout=120)
            if rr.returncode != 0:
                bad_runs.append((Path(i["script"]).name, (rr.stderr or "")[:60]))
        ck("10 支腳本都跑得起來", not bad_runs, str(bad_runs)[:160])

        # ── VSKE 只增不減 ──
        payload = vske_payload(reps)
        ck("VSKE 10 筆", len(payload["skills"]) == 10)
        ck("VSKE 每筆有 sop 指紋",
           all(len(x["sop_sha256"]) == 64 for x in payload["skills"]))
        vp = out_all / VSKE_NAME
        vp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_v = cmd_vske(argparse.Namespace(apply=True, out=str(out_all)))
        ck("VSKE 已存在時拒絕覆寫", rc_v == 1 and "不覆蓋" in buf.getvalue(), buf.getvalue()[:90])

        # 同一輸入要出同一位元組(可重現)
        again = sha256_text(skill_md(s))
        ck("SKILL.md 可重現(同輸入同指紋)", again == info["skill_md_sha256"])

        # ── 迴歸:④ 省 Token 量不到時,總燈不能被前三段的綠蓋成 GREEN ──
        # (這是本支開發中真的踩到的假綠:三段 GREEN + ④ YELLOW 卻印 [總燈] GREEN)
        import io
        import contextlib as _ctx
        fake_root = tmp / "norepo"
        (fake_root / "supportive modules").mkdir(parents=True)
        (fake_root / "functional modules").mkdir()
        buf2 = io.StringIO()
        _orig_via_root = globals()["via_root"]
        globals()["via_root"] = lambda start=None: fake_root
        try:
            with _ctx.redirect_stdout(buf2):
                cmd_all(argparse.Namespace(out=str(tmp / "aggtest")))
        finally:
            globals()["via_root"] = _orig_via_root
        agg_out = buf2.getvalue()
        ck("④ 量不到時總燈不是 GREEN",
           "[總燈] GREEN" not in agg_out, agg_out[-200:])
        ck("④ 量不到時總燈標 YELLOW 並寫原因",
           "[總燈] YELLOW" in agg_out and "總燈不給綠" in agg_out, agg_out[-200:])

        # ── 誠實律:描述裡不准出現沒跑過就說綠 ──
        md_text = (Path(info["dir"]) / "SKILL.md").read_text(encoding="utf-8")
        ck("SKILL.md 寫明不產 .ps1 的理由", KIT_LAW in md_text)
        ck("SKILL.md 標明組合而非重寫", "不重寫輪子" in md_text)
        ck("參考檔寫明未知不綠",
           "永不綠" in (Path(info["dir"]) / "references" / "rules_v0100.md")
           .read_text(encoding="utf-8"))

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = sum(1 for _, c, _ in checks if c)
    for name, cond, note in checks:
        if not cond:
            print(f"  [FAIL] {name}" + (f" — {note}" if note else ""))
    print(f"[自測] {ok}/{len(checks)} " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="VIA_SkillExport_v0100",
        description="技能引擎:三層漸進載入 · 10 技能登錄表 · /export-skill + Celeritas 三檢")
    ap.add_argument("--selftest", action="store_true", help="夾具自測(零網路 · 只寫沙盒)")
    sub = ap.add_subparsers(dest="verb")

    p = sub.add_parser("registry", help="Tier1 索引:10 技能登錄表")
    p.add_argument("--json", action="store_true")
    p.add_argument("--depth", action="store_true", help="逐技能印 Tier2 字元數")
    p.set_defaults(fn=cmd_registry)

    p = sub.add_parser("sop", help="Tier2:只載入一個技能的四段 SOP")
    p.add_argument("slash")
    p.set_defaults(fn=cmd_sop)

    p = sub.add_parser("export", help="Tier3:產出官方結構")
    p.add_argument("slash")
    p.add_argument("--out", default="VIA_Reports/skills")
    p.set_defaults(fn=cmd_export)

    p = sub.add_parser("export-all", help="Tier3:10 技能全匯出")
    p.add_argument("--out", default="VIA_Reports/skills")
    p.set_defaults(fn=cmd_export_all)

    p = sub.add_parser("check", help="三檢 + PY 骨架規則")
    p.add_argument("dirs", nargs="*")
    p.add_argument("--ps", help="唯讀驗證一支 .ps1(不代修)")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("vske", help="VSKE 登錄冊(只增)")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--out", default="VIA_Reports/skills")
    p.set_defaults(fn=cmd_vske)

    p = sub.add_parser("tokens", help="省 Token 實測(本倉真檔)")
    p.set_defaults(fn=cmd_tokens)

    p = sub.add_parser("all", help="registry → export-all → check → vske → tokens")
    p.add_argument("--out", default="VIA_Reports/skills")
    p.set_defaults(fn=cmd_all)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
