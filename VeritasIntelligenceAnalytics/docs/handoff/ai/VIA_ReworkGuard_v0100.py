#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ReworkGuard v0100 — 重工守門:預設偵測這一週反覆重工的原因,每一項內建解法(操作員 2026-11-24)

  操作員 2026-11-24:「這一周重工因素過多,請找出原因及解決方案,寫成指令的預設偵測問題及解決方案內建」。
  來源(倉裡已有的三份,不另立正本):git 歷史(11-17 ~ 11-24:410 提交 · 還原 6 · 回 Codex 修補 36)
  × 每日教訓帳 VIA_DailyLessons_Ledger_v0100.jsonl(本週 89 條)× 成功鎖定帳。歸成 13 類根因(CAUSES),每類寫明
  偵測器 · 解法 · 一行指令;check 把偵測器全部跑一遍,report 把這一週的數字對回 13 類。
  已有的不另做:版號插到尾版底下 · 改 / 刪已鎖成功 → 直接呼叫 .github/scripts/pr_guard.py 的 check();
  Codex 沒審完 → pr-guards.yml 的 codex_gate(本工具只提醒去設必要檢查);加速器 / 網路橋以語法樹判(同 CGC_MDL158 / VRN v0288)。

  動詞:
    check  [--base origin/main] [--head HEAD] [--fetch-prs] [--json]   推送 / 開 PR / 取號之前跑(預設動詞)
           看 已提交(base...head)+ 工作樹未提交的改動。紅 = rc 1(擋)· 黃 = rc 2 · 綠 = rc 0。
    report [--days 7] [--json]   這一週的重工數字:提交 · 還原 · 回審查修補 · 版號來回最多的家族 · 教訓按 13 類分
    causes                        13 類根因 × 偵測器 × 解法 × 指令(內建知識,不讀網路)
    --selftest                    暫存 git 倉造每一種情境,零網路
  唯讀:只讀 git 物件與工作樹檔案;不改檔、不提交、不出網、不執行被檢查的程式。--fetch-prs 只做 git fetch(開著的 PR 頭)。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import ast
import collections
import datetime as _dt
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_ReworkGuard " + VERSION
VIA = "VeritasIntelligenceAnalytics/"
LESSONS = VIA + "docs/handoff/daily/VIA_DailyLessons_Ledger_v0100.jsonl"
VER = re.compile(r"^(?P<fam>.+)_v(?P<n>\d{4})(?P<ext>\.[A-Za-z0-9]+)$")
NUM_ID = re.compile(r"\bVIA-(?:[A-Z]+-)?(?:MDL|ENG|SSOT|TOOL|FNC|CLS|WKF|REQ|CORE)-?\d{3,5}\b|\b(?:VCGC|VDF|VRN|VQG|VAP)-(?:REQ|WKF)\d{3}\b")
NET_LIBS = {"requests", "urllib3", "httpx", "aiohttp", "curl_cffi", "yfinance", "websocket", "websockets", "ftplib", "akshare",
            "fredapi", "pandas_datareader", "cloudscraper", "playwright", "selenium", "twstock", "FinMind"}
NET_FULL = {"urllib.request", "http.client"}
SECRET_RX = [re.compile(r"\bghp_[A-Za-z0-9]{30,}"), re.compile(r"\bsk-[A-Za-z0-9]{30,}"), re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
             re.compile(r"\bxox[bp]-[A-Za-z0-9-]{20,}")]
SECRET_NAME = re.compile(r"(?i)(api[_-]?key|secret|token|passwd|password)")
LOCAL_PATH = re.compile(r"[A-Za-z]:\\\\?Users\\\\?[A-Za-z0-9_.-]+|/home/(?!user/)[a-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/")
ARTIFACT_DIRS = ("VeritasIntelligenceAnalytics/functional modules/VRN2/", "VeritasIntelligenceAnalytics/functional modules/VDF/_runtime/")
PARSE_ERRORS: list = []                              # 壞檔計數(壞檔本身由 d_bridges 報紅)
ORDER = {"GREEN": 0, "GRAY": 0, "YELLOW": 1, "RED": 2}

# ─────────────────────────── 13 類根因(內建知識)───────────────────────────
CAUSES = [
    {"code": "R1", "name": "合併搶在審查前 · 已鎖成功被原地改", "lessons": ["LL-20261121-04", "LL-20261121-05", "LL-20261121-24", "LL-20261121-27", "LL-20261122-05"],
     "kw": ["Codex", "審完前", "合併", "已鎖", "原地改"], "detector": "LOCKED(pr_guard ②)· 審查 = pr-guards 的「Codex 審查」",
     "fix": "已鎖的檔一律出新版號(薄尾),不改原檔;GitHub Settings → Branches 把「PR guards」「Codex 審查」設為必要檢查,CI 綠 + Codex 綠才合併。",
     "cmd": "git restore --source origin/main -- <已鎖的檔>   # 改動搬到 <家族>_v<下一號>.py"},
    {"code": "R2", "name": "多線撞號 · 撞版號 · 插到尾版底下", "lessons": ["LL-20261118-15", "LL-20261120-08", "LL-20261120-10", "LL-20261120-17", "LL-20261121-21", "LL-20261122-01"],
     "kw": ["撞", "取號", "分類碼", "插到尾版", "取冊號"], "detector": "TAILS(pr_guard ①)· OPENPR(開著的 PR 也發了同號 / 同檔名)· BOOKLOSS(新冊版少了 base 尾版的代碼)",
     "fix": "取號前 fetch 開著的 PR,號與版號取 本機 ∪ origin/main ∪ 開著的 PR 的最大值之上;撞了就改發新號,已發布的(main)為準。",
     "cmd": "python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_ReworkGuard_v0100.py check --fetch-prs"},
    {"code": "R3", "name": "工作樹不乾淨就同步 / 編號 / 提交", "lessons": ["LL-20261118-04", "LL-20261118-07", "LL-20261118-12", "LL-20261120-05", "LL-20261121-03", "LL-20261121-23"],
     "kw": ["未追蹤", "工作樹", "index.lock", "容器產物", "git status", "git add -A", "共用冊", "擁有者", "覆寫了已追蹤"], "detector": "DIRTY(執行期產物 · index.lock · 已追蹤檔被工具重寫)",
     "fix": "registry-sync / 編號 / 提交前工作樹要全乾淨:執行期產物先移走,背景 git 結束再提交;提交後看 git log -1 與 git status;只 add 自己改的檔。",
     "cmd": "git status --porcelain && git clean -n -- \"VeritasIntelligenceAnalytics/functional modules/VRN2\""},
    {"code": "R4", "name": "薄尾換錯層 · 新版沒生效", "lessons": ["LL-20261118-05", "LL-20261119-05", "LL-20261119-17", "LL-20261120-09", "LL-20261121-01", "LL-20261121-06", "LL-20261122-04"],
     "kw": ["沒生效", "真正做事", "這一層", "接手", "那一層"], "detector": "TAILPATCH(PRIOR.<名> = … 但 <名> 不是直接前版自己定義的)",
     "fix": "先 chain 找真正定義那個名字的版(_owner(name)),換那一版模組的全域;再用命令列實跑一次證明新行為生效(自測過不算)。",
     "cmd": "python3 \"$E\" chain <家族名>   # $E = 鎖冊 token 那支 CGC_MDL158"},
    {"code": "R5", "name": "自測脆:吃本機狀態 · 釘死舊世界 · 前版鏈太深太慢", "lessons": ["LL-20261118-13", "LL-20261119-01", "LL-20261119-08", "LL-20261119-11", "LL-20261119-13", "LL-20261121-15"],
     "kw": ["自測"], "detector": "SELFTEST(自測讀正式夾不用暫存夾)· PINPRIOR(前版檔名寫死)",
     "fix": "自測一律在暫存夾造資料;前版用 glob 取「比自己小的最大版」;前版鏈太深時加行程內記憶(VRN v0289 例:2591 次掃描 → 901)。",
     "cmd": "python3 <新尾版>.py --selftest   # 在乾淨的暫存副本上再跑一次"},
    {"code": "R6", "name": "交給桌機的指令沒先模擬", "lessons": ["LL-20261120-01", "LL-20261121-14", "LL-20261121-25", "LL-20261122-06"],
     "kw": ["桌機", "一行指令", "主機", "相對路徑", "工作目錄", "cwd", "背景", "回收", "心跳"], "detector": "LOCALPATH(新檔含本機路徑)· 指令檢查清單",
     "fix": "交出前照 CLAUDE.md「先模擬桌機」:指令先定位倉根、fetch 並快轉、檔在不在;長跑要有進度與心跳;日誌用 .log.txt(*.log 被忽略)。",
     "cmd": "$Repo=\"$HOME\\OneDrive\\Documents\\movies-dataset\"; git -C $Repo fetch -q origin main; git -C $Repo status -sb"},
    {"code": "R7", "name": "只修被點名的那一條(同類路徑沒一起修)", "lessons": ["LL-20261118-20", "LL-20261121-09", "LL-20261121-17", "LL-20261121-18", "LL-20261121-19", "LL-20261121-20"],
     "kw": ["只修", "那一種", "那一條", "fail-open", "一半", "同一類"], "detector": "SIBLING(同一個 commit 修了 A,同檔裡同名樣式的 B 沒動)— 列成清單人工核",
     "fix": "修之前先列出「同一個毛病還有哪些路徑」寫進 PR 描述;fail-closed:沒列進白名單的型別一律擋,不默默略過。",
     "cmd": "git grep -n \"<被點名的樣式>\" -- VeritasIntelligenceAnalytics"},
    {"code": "R8", "name": "多把尺各說各的 · 字串判斷", "lessons": ["LL-20261119-12", "LL-20261120-03", "LL-20261121-26", "LL-20261121-28"],
     "kw": ["三把尺", "各說各", "字串", "標記", "只有標記", "逐列比"], "detector": "BRIDGES(新檔加速器 / 網路橋以語法樹判)",
     "fix": "判斷一律用語法樹(真的 import / 真的呼叫),不用字串;同一件事只認一把尺(CGC_MDL158 scan · 各系統 bridges)。",
     "cmd": "python3 \"$E\" scan --json   # 或 VRN_SystemManager bridges --json(v0289 起語法樹)"},
    {"code": "R9", "name": "一則一版 · 範圍蔓延", "lessons": ["LL-20261119-03", "LL-20261119-10"],
     "kw": ["一則", "範圍", "接了新需求"], "detector": "CHURN(report:同家族一天 > 3 版)",
     "fix": "連續來的需求先收成一批再出一版;每批只做當則訊息點名的;主機驗收沒過不接新需求。",
     "cmd": "python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_ReworkGuard_v0100.py report"},
    {"code": "R10", "name": "跨系統沒退路(拿掉 VCGC 就倒)", "lessons": ["LL-20261118-08", "LL-20261118-09", "LL-20261119-16"],
     "kw": ["退路", "拿掉 VCGC", "只認"], "detector": "XSYS(VDF / VRN 新檔讀 CGC_* 模組卻沒包 try)",
     "fix": "用到別的系統的模組一律有退路(同判法 · 沒同意照樣關),不准開檔就丟例外;出新版前在拿掉 CGC_*.py 的副本上載一次。",
     "cmd": "python3 <新檔>.py --selftest   # 在拿掉 supportive modules/registry/CGC_*.py 的副本上"},
    {"code": "R11", "name": "憑證明文進倉", "lessons": ["(2026-11-24 安全修復:FRED 金鑰 10 檔)"],
     "kw": ["金鑰", "明文", "憑證"], "detector": "SECRET(改動的檔含金鑰樣式 / *KEY* = 長常數)",
     "fix": "遮罩為 <REDACTED:…>(同 CGC_MDL133 G6 鑰匙守衛);金鑰作廢重發;新鑰只放環境變數或倉外檔。",
     "cmd": "python3 VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_ReworkGuard_v0100.py check"},
    {"code": "R12", "name": "擷取資料不對:回空跳過 · 留洞 · 亂碼 · 欄位 / 日曆對不上 · 默默丟列燈還綠",
     "lessons": ["LL-20261118-17", "LL-20261118-18", "LL-20261119-15", "LL-20261120-15", "LL-20261121-07", "LL-20261121-10", "LL-20261121-11", "LL-20261121-13"],
     "kw": ["回空", "留洞", "亂碼", "字集", "charset", "交易日", "默默", "Yahoo", "官方", "欄位", "停在", "抓不到"],
     "detector": "FETCHTEXT(新擷取檔讀回應 .text 卻沒指定字集)· 擷取後 VDF datamatrix / 輸出對表頭冊(目標缺一不綠)",
     "fix": "回應一律明示 utf-8 / 依來源字集解碼;回空 ≠ 沒交易日(記洞 · 下輪回補);交易日曆取官方;擷取後跑 VDF datamatrix 與輸出驗證,名單缺一不綠。",
     "cmd": "python <VDF_SystemManager 尾版> datamatrix   # 名單逐項點名,缺一不綠"},
    {"code": "R13", "name": "冊與相依沒跟著改(註冊鏈漏步)",
     "lessons": ["LL-20261118-03", "LL-20261118-11", "LL-20261119-02", "LL-20261119-04", "LL-20261119-14", "LL-20261121-16", "LL-20261119-09"],
     "kw": ["工作流冊", "盤點冊", "coverage", "相依", "短指令", "start_args", "沒有回頭", "冊", "中央號", "散在"],
     "detector": "REGISTER(新程式檔沒出現在任何改動的冊裡:需求冊 · 工作流冊 · 盤點冊 · 交接案)",
     "fix": "出新版就走完整條註冊鏈:需求冊 → 工作流冊 → 盤點冊 stations + coverage.case + coverage.workflow → 交接案 → 編號 → 鎖帳;舊步的版號一起往前移。",
     "cmd": "VIA_FROM_VCGC=YES python3 \"$V\" handoff check   # $V = CGC_MDL149 主控台尾版"},
]


# ─────────────────────────── git 小工具 ───────────────────────────
def git(repo, *a, binary=False, check=True):
    cp = subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    if check and cp.returncode != 0:
        raise RuntimeError("git %s → rc %d · %s" % (" ".join(a[:3]), cp.returncode, cp.stderr.decode("utf-8", "replace")[:200]))
    return cp.stdout if binary else cp.stdout.decode("utf-8", "replace")


def repo_root(start=None) -> Path:
    here = Path(start or os.getcwd())
    try:
        return Path(git(here, "rev-parse", "--show-toplevel").strip())
    except Exception:  # noqa: BLE001
        return here


def load_pr_guard():
    """pr_guard 跟本工具同一個倉的那一份(CI 由 base 複製到同一夾),不載入被檢查的 checkout 裡的版本。"""
    me = Path(__file__).resolve()
    cands = [me.parent / "pr_guard.py"]
    p = me.parent
    while p.parent != p and not (p / ".github").is_dir():
        p = p.parent
    cands.append(p / ".github" / "scripts" / "pr_guard.py")
    for c in cands:
        if c.is_file():
            spec = importlib.util.spec_from_file_location("via_pr_guard_for_rework", c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def changed(repo, base, head) -> dict:
    """已提交(base...head)+ 工作樹未提交(已追蹤改動 · 未追蹤新檔)。路徑相對倉根。"""
    out = {"A": set(), "M": set(), "D": set(), "U": set()}
    for ln in git(repo, "diff", "--name-status", "--no-renames", f"{base}...{head}").splitlines():
        k, _, p = ln.partition("\t")
        if k[:1] in out and p:
            out[k[:1]].add(p)
    for ln in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        code, p = ln[:2], ln[3:].strip().strip('"')
        if code == "??":
            out["U"].add(p)
        elif "D" in code:
            out["D"].add(p)
        elif p not in out["A"]:
            out["M"].add(p)
    return {k: sorted(v) for k, v in out.items()}


def read(repo, p) -> str:
    try:
        return (Path(repo) / p).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


# ─────────────────────────── 偵測器 ───────────────────────────
def _parse(src: str):
    """語法樹;壞檔回 None(壞檔由 d_bridges 報紅,其他偵測器略過該檔)。"""
    try:
        return ast.parse(src)
    except (SyntaxError, ValueError) as exc:
        PARSE_ERRORS.append(type(exc).__name__)
        return None


def _imports(tree) -> set:
    s = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            s |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            s.add(n.module)
            s |= {n.module + "." + a.name for a in n.names}
    return s


def d_bridges(repo, files) -> list:
    out = []
    for p in files:
        if not (p.endswith(".py") and p.startswith(VIA)) or "/intake/" in p or "/references/" in p:
            continue
        src = read(repo, p)
        try:
            imps = _imports(ast.parse(src))
        except SyntaxError as exc:
            out.append(("RED", "R8", f"`{p}` 語法錯(L{exc.lineno})"))
            continue
        if "VIA_SuperAccel_Module" not in imps:
            out.append(("YELLOW", "R8", f"`{p}` 語法樹裡沒有 import VIA_SuperAccel_Module" + ("(只有標記)" if "VIA:ACCEL-BRIDGE" in src else "")))
        net = sorted({i for i in imps if i.split(".")[0] in NET_LIBS} | (imps & NET_FULL))
        if net and "VIA:NET-BRIDGE" not in src and "VIA_NET_TOOL_PATH" not in src:
            out.append(("YELLOW", "R8", f"`{p}` 匯入網路套件 {net[:3]} 卻沒掛網路橋"))
    return out


def d_tailpatch(repo, files) -> list:
    """新尾版 PRIOR.<名> = …,但 <名> 不是直接前版自己頂層定義的 → 換到的是轉交名字,處理動詞的那一層看不到(LL-19-17)。"""
    out = []
    for p in files:
        m = VER.match(Path(p).name)
        if not (m and p.endswith(".py")):
            continue
        src = read(repo, p)
        tree = _parse(src)
        if tree is None:
            continue
        sets = {t.attr for n in ast.walk(tree) if isinstance(n, ast.Assign) for t in n.targets
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "PRIOR"}
        if not sets:
            continue
        here = Path(repo) / p
        n = int(m["n"])
        priors = [q for q in here.parent.glob(m["fam"] + "_v*" + m["ext"]) if VER.match(q.name) and int(VER.match(q.name)["n"]) < n]
        if not priors:
            continue
        prior = max(priors, key=lambda q: int(VER.match(q.name)["n"]))
        ptree = _parse(prior.read_text(encoding="utf-8-sig", errors="replace"))
        if ptree is None:
            continue
        top = {x.name for x in ptree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        top |= {t.id for x in ptree.body if isinstance(x, (ast.Assign, ast.AnnAssign)) for t in (x.targets if isinstance(x, ast.Assign) else [x.target]) if isinstance(t, ast.Name)}
        miss = sorted(s for s in sets if s not in top and not s.isupper())
        if miss:
            out.append(("YELLOW", "R4", f"`{p}` 換了 PRIOR.{', PRIOR.'.join(miss[:4])},但直接前版 {prior.name} 沒有自己定義它們 → 真正處理的那一版可能看不到(用 _owner 找定義的版)"))
    return out


def d_selftest(repo, files) -> list:
    out = []
    for p in files:
        if not p.endswith(".py") or not p.startswith(VIA):
            continue
        src = read(repo, p)
        tree = _parse(src)
        if tree is None:
            continue
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "selftest"):
            body = ast.get_source_segment(src, fn) or ""
            uses_tmp = "tempfile" in body or "TemporaryDirectory" in body or "mkdtemp" in body
            if not uses_tmp and re.search(r"VIA_Reports|\.duckdb|vdf_home|VDF_HOME", body):
                out.append(("YELLOW", "R5", f"`{p}` 自測讀正式資料夾 / 庫卻沒用暫存夾(結果會跟這台機器有沒有資料有關)"))
        if VER.match(Path(p).name):
            fam = VER.match(Path(p).name)["fam"]
            pins = sorted(set(re.findall(r"[\"']%s_v\d{4}\.py[\"']" % re.escape(fam), src)))
            if pins:
                out.append(("YELLOW", "R5", f"`{p}` 寫死前版檔名 {pins[0]}(換版就斷;用 glob 取比自己小的最大版)"))
    return out


def d_secret(repo, files) -> list:
    out = []
    for p in files:
        src = read(repo, p)
        if not src:
            continue
        hit = next((rx.pattern[:12] for rx in SECRET_RX if rx.search(src)), None)
        if not hit and p.endswith(".py"):
            for n in ast.walk(_parse(src) or ast.Module(body=[], type_ignores=[])):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    v = n.value.value
                    names = [t.id if isinstance(t, ast.Name) else getattr(t, "attr", "") for t in n.targets]
                    if any(SECRET_NAME.search(x or "") for x in names) and re.fullmatch(r"[A-Za-z0-9_\-]{24,}", v) and not v.isupper():
                        hit = "*KEY* = 長常數"
                        break
        if hit:
            out.append(("RED", "R11", f"`{p}` 含疑似金鑰({hit};值不印)→ 遮罩 <REDACTED:…> 並作廢重發"))
    return out


def d_localpath(repo, files) -> list:
    out = []
    for p in files:
        if not p.endswith((".py", ".ps1", ".psm1", ".json", ".md")) or "/evidence/" in p:
            continue
        m = LOCAL_PATH.search(read(repo, p))
        if m:
            out.append(("YELLOW", "R6", f"`{p}` 含本機路徑(新檔不含本機路徑;用 $HOME / 倉根相對)"))
    return out


def d_xsys(repo, files) -> list:
    out = []
    for p in files:
        if not p.endswith(".py") or not re.match(VIA + r"functional modules/(VDF|VRN|VQG|VAP)/", p) or "/intake/" in p:
            continue
        src = read(repo, p)
        tree = _parse(src)
        if tree is None:
            continue
        tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
        guarded = set()
        for t in tries:
            for n in ast.walk(t):
                guarded.add(id(n))
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(r"\bCGC_MDL\d{3}", n.value) and id(n) not in guarded:
                if re.search(r"\.py\b|_v\*|glob", n.value) or "spec_from_file_location" in src:
                    out.append(("YELLOW", "R10", f"`{p}` 讀 VCGC 模組 {n.value[:40]!r} 不在 try 裡(拿掉 VCGC 就倒)"))
                    break
    return out


def d_dirty(repo, ch) -> list:
    out = []
    gitdir = Path(git(repo, "rev-parse", "--git-dir").strip())
    gitdir = gitdir if gitdir.is_absolute() else Path(repo) / gitdir
    if (gitdir / "index.lock").exists():
        out.append(("RED", "R3", "`.git/index.lock` 在:另一個 git 行程還在跑(先等它結束,不刪別人的鎖)"))
    art = [p for p in ch["U"] if p.startswith(ARTIFACT_DIRS)]
    if art:
        out.append(("YELLOW", "R3", f"工作樹有 {len(art)} 個執行期產物未追蹤(例 `{art[0]}`)→ registry-sync / 編號前先移走"))
    gen = [p for p in ch["M"] if re.search(r"(_latest\.(json|md|html)|_UI\.html|panorama\.manifest\.json|BACKUP_MANIFEST_latest\.json)$", p)]
    if gen:
        out.append(("YELLOW", "R3", f"{len(gen)} 個已追蹤的收據 / 頁被工具重寫(例 `{gen[0]}`)→ 是這次要交的才 add,否則 git restore"))
    return out


def open_pr_list() -> set | None:
    """開著的 PR 號(CI 由 gh pr list 帶進 VIA_OPEN_PRS="12 34";本機可用 --open-prs)。沒給 = None(改用 10 天內未併的 PR 頭,只亮黃)。"""
    v = os.environ.get("VIA_OPEN_PRS")
    return None if v is None else {x for x in re.split(r"[\s,]+", v) if x.isdigit()}


def d_openpr(repo, base, ch, fetch: bool, open_prs: set | None = None) -> list:
    open_prs = open_pr_list() if open_prs is None else open_prs
    if fetch:
        git(repo, "fetch", "-q", "origin", "+refs/pull/*/head:refs/remotes/pr/*", check=False)
    refs = [r for r in git(repo, "for-each-ref", "--format=%(refname)", "refs/remotes/pr/").split() if r]
    if not refs:
        return [("GRAY", "R2", "沒有開著的 PR 頭可比(加 --fetch-prs 抓;取號 / 出新版號前一定要比)")]
    mine_files = {Path(p).name for p in ch["A"] + ch["U"] if VER.match(Path(p).name)}
    mine_ids = set()
    for ln in git(repo, "diff", "-U0", f"{base}...HEAD").splitlines():
        if ln.startswith("+") and not ln.startswith("+++"):
            mine_ids |= set(NUM_ID.findall(ln))
    head = git(repo, "rev-parse", "HEAD").strip()
    out = []
    cutoff = time.time() - 10 * 86400
    compared, skipped = 0, []
    for r in refs:
        num = r.split("/")[-1]
        if open_prs is not None and num not in open_prs:
            continue
        sha = git(repo, "rev-parse", r).strip()
        if sha == head or any(subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, x], capture_output=True).returncode == 0
                              for x in (base, "HEAD")):
            continue                                                         # 自己(CI 的合併提交含自己的頭)· 已併進 base 的不算
        if open_prs is None and int(git(repo, "log", "-1", "--format=%ct", sha).strip() or 0) < cutoff:
            continue                                                         # 沒有開著的清單時只看 10 天內的頭
        try:
            names = {Path(p).name for p in git(repo, "diff", "--name-only", "--diff-filter=A", f"{base}...{r}").splitlines()}
            plus = git(repo, "diff", "-U0", f"{base}...{r}").splitlines() if mine_ids else []
        except RuntimeError as exc:                                          # 跟 base 沒有共同祖先(極舊的 PR)
            skipped.append(f"#{num}:{str(exc)[:40]}")
            continue
        compared += 1
        lamp, who = ("RED", f"開著的 PR #{num}") if open_prs is not None else ("YELLOW", f"PR #{num}(10 天內 · 未併 · 沒確認是否還開著)")
        both = sorted(mine_files & names)
        if both:
            out.append((lamp, "R2", f"{who} 也新增了同檔名 {both[:3]} → 改發兩邊最大號之上"))
        ids = set()
        for ln in plus:
            if ln.startswith("+") and not ln.startswith("+++"):
                ids |= set(NUM_ID.findall(ln))
        dup = sorted(mine_ids & ids)
        if dup:
            out.append((lamp, "R2", f"{who} 也發了 {dup[:4]} → 重新取號"))
    if not compared and not out:
        out.append(("GRAY", "R2", "沒有可比的 PR 頭(開著的清單空 · 或都已併)"))
    return out


def d_register(repo, ch, new) -> list:
    """新程式檔(<家族>_vNNNN.py)沒有出現在任何改動的冊(.json / .jsonl)裡 → 註冊鏈還沒走(R13)。"""
    code = [p for p in new if p.startswith(VIA) and p.endswith((".py", ".ps1")) and VER.match(Path(p).name)]
    if not code:
        return []
    books = [p for p in sorted(set(ch["A"]) | set(ch["M"]) | set(ch["U"])) if p.endswith((".json", ".jsonl")) and p.startswith(VIA)]
    text = "\n".join(read(repo, b) for b in books)
    miss = [p for p in code if Path(p).name not in text and Path(p).stem not in text]
    return [("YELLOW", "R13", f"`{p}` 還沒出現在任何改動的冊裡(需求冊 · 工作流冊 · 盤點冊 · 交接案)") for p in miss[:8]]


def d_fetchtext(repo, files) -> list:
    out = []
    for p in files:
        if not (p.endswith(".py") and p.startswith(VIA)):
            continue
        src = read(repo, p)
        tree = _parse(src)
        if tree is None:
            continue
        if not any(i.split(".")[0] in NET_LIBS for i in _imports(tree)):
            continue
        reads_text = any(isinstance(n, ast.Attribute) and n.attr == "text" and isinstance(n.ctx, ast.Load) for n in ast.walk(tree))
        sets_enc = any(isinstance(n, ast.Attribute) and n.attr == "encoding" and isinstance(n.ctx, ast.Store) for n in ast.walk(tree)) or "decode(" in src
        if reads_text and not sets_enc:
            out.append(("YELLOW", "R12", f"`{p}` 讀回應 .text 卻沒指定字集(沒帶 charset 時會被猜錯 → 亂碼;LL-20261120-15)"))
    return out


ID_KEY = re.compile(r'"(?:id|code|case|req_id|wkf_id|station|key)"\s*:\s*"([^"]{2,80})"')


def d_bookloss(repo, base, ch) -> list:
    """新增的冊版(<家族>_vNNNN.json)必須含 base 尾版冊的每一個代碼(成功只增不減 · 待辦不能消失)。
    兩條線各從同一個 main 長冊時,後併的那一支會把先併那支的列蓋掉(#730 REQ254 · 本週 R2)。"""
    out = []
    for p in sorted(set(ch["A"]) | set(ch["U"])):
        m = VER.match(Path(p).name)
        if not (m and m["ext"] == ".json" and p.startswith(VIA)):
            continue
        folder = str(Path(p).parent).replace("\\", "/") + "/"
        names = [x for x in git(repo, "ls-tree", "--name-only", base, folder).splitlines() if VER.match(Path(x).name)]
        same = [x for x in names if VER.match(Path(x).name)["fam"] == m["fam"] and VER.match(Path(x).name)["ext"] == ".json"]
        if not same:
            continue
        tail = max(same, key=lambda x: int(VER.match(Path(x).name)["n"]))
        if int(VER.match(Path(tail).name)["n"]) >= int(m["n"]):
            continue                                                         # 插到尾版底下另由 pr_guard ① 報
        old = set(ID_KEY.findall(git(repo, "show", f"{base}:{tail}")))
        new = set(ID_KEY.findall(read(repo, p)))
        lost = sorted(old - new)
        if lost:
            out.append(("RED", "R2", f"`{p}` 少了 base 尾版 {Path(tail).name} 的 {len(lost)} 個代碼(例 {lost[:4]})→ 先把 base 尾版的列併進來再出版"))
    return out


def run_check(repo, base="origin/main", head="HEAD", fetch=False, open_prs=None) -> dict:
    repo = Path(repo)
    ch = changed(repo, base, head)
    touched = sorted(set(ch["A"]) | set(ch["M"]) | set(ch["U"]))
    found = []
    pg = load_pr_guard()
    if pg is not None:
        r = pg.check(str(repo), base, head)
        found += [("RED", "R2" if x.startswith("①") else "R1", x) for x in r["red"]]
        found += [("YELLOW", "R2", x) for x in r["yellow"]]
        locks = pg.locked(str(repo), base)
        for p in ch["M"]:                                                    # 工作樹未提交也比(pr_guard 只看已提交)
            row = locks.get(p[len(VIA):]) if p.startswith(VIA) else None
            if row and row.get("sha256_lf") and (repo / p).is_file() and pg.lf_sha((repo / p).read_bytes()) != row["sha256_lf"]:
                msg = f"② `{p}` 已鎖成功,工作樹改了位元(未提交)→ 出新版號"
                if not any(p in x[2] for x in found):
                    found.append(("RED", "R1", msg))
    else:
        found.append(("GRAY", "R1", "找不到 .github/scripts/pr_guard.py(版號尾版 · 成功鎖兩項沒查)"))
    found += d_dirty(repo, ch)
    found += d_openpr(repo, base, ch, fetch, open_prs)
    new = sorted(set(ch["A"]) | set(ch["U"]))                               # 新檔才查寫法類(舊檔原有的毛病不算這次的重工)
    found += d_tailpatch(repo, [p for p in new if p.endswith(".py")])
    found += d_selftest(repo, new)
    found += d_bridges(repo, new)
    found += d_localpath(repo, new)
    found += d_xsys(repo, new)
    found += d_bookloss(repo, base, ch)
    found += d_fetchtext(repo, new)
    found += d_register(repo, ch, new)
    found += d_secret(repo, touched)                                         # 金鑰:新檔與改過的檔都查
    lamp = max((f[0] for f in found if f[0] != "GRAY"), key=lambda x: ORDER[x], default="GREEN")
    return {"tool": TAG, "base": base, "head": head, "lamp": lamp, "scanned": len(touched),
            "changes": {k: len(v) for k, v in ch.items()}, "findings": [{"lamp": a, "cause": b, "what": c} for a, b, c in found]}


def render_check(r: dict) -> str:
    by = {c["code"]: c for c in CAUSES}
    lines = [f"[{r['tool']}] check {r['lamp']} · 掃 {r['scanned']} 檔(新增 {r['changes']['A']} · 改 {r['changes']['M']} · 刪 {r['changes']['D']} · 未追蹤 {r['changes']['U']})· base {r['base']}"]
    seen = set()
    for f in sorted(r["findings"], key=lambda x: -ORDER[x["lamp"]]):
        c = by[f["cause"]]
        lines.append(f"  [{f['lamp']:<6}] {f['cause']} {c['name']} · {f['what']}")
        if f["cause"] not in seen and f["lamp"] in ("RED", "YELLOW"):
            seen.add(f["cause"])
            lines.append(f"           解法:{c['fix']}")
            lines.append(f"           指令:{c['cmd']}  · 教訓 {', '.join(c['lessons'][:3])}")
    if not r["findings"]:
        lines.append("  沒有偵測到 13 類重工原因(版號 · 鎖 · 撞號 · 工作樹 · 換錯層 · 自測 · 橋 · 金鑰 · 本機路徑 · 跨系統退路;寫法類只查新檔)")
    return "\n".join(lines)


# ─────────────────────────── report ───────────────────────────
def classify(row: dict) -> str:
    text = " ".join(str(row.get(k) or "") for k in ("problem", "cause", "fix"))
    for c in CAUSES:
        if row.get("id") in c["lessons"]:
            return c["code"]
    for c in CAUSES:
        if any(k in text for k in c["kw"]):
            return c["code"]
    return "其他"


def run_report(repo, days=7) -> dict:
    repo = Path(repo)
    since = (_dt.date.today() - _dt.timedelta(days=days)).isoformat()
    ref = "origin/main" if git(repo, "rev-parse", "--verify", "-q", "origin/main", check=False).strip() else "HEAD"
    subj = git(repo, "log", ref, f"--since={since}", "--no-merges", "--pretty=%s").splitlines()
    merges = len(git(repo, "log", ref, f"--since={since}", "--merges", "--pretty=%h").split())
    added = git(repo, "log", ref, f"--since={since}", "--diff-filter=A", "--name-only", "--pretty=@%ad", "--date=short").splitlines()
    fam_day = collections.Counter()
    fam_all = collections.Counter()
    day = ""
    for ln in added:
        if ln.startswith("@"):
            day = ln[1:]
            continue
        m = VER.match(Path(ln).name)
        if m and m["ext"] == ".py":
            fam_all[m["fam"]] += 1
            fam_day[(m["fam"], day)] += 1
    rows, bad_rows = [], []
    lp = repo / LESSONS
    if lp.is_file():
        for ln in lp.read_text(encoding="utf-8").splitlines():
            try:
                x = json.loads(ln)
            except ValueError:
                bad_rows.append(ln[:40])
                continue
            if str(x.get("date") or "")[:10] >= since:
                rows.append(x)
    cats = collections.Counter(classify(x) for x in rows)
    churn = sorted(((f, d, n) for (f, d), n in fam_day.items() if n > 3), key=lambda t: -t[2])
    return {"tool": TAG, "since": since, "ref": ref, "commits": len(subj), "merges": merges,
            "reverts": sum(1 for s in subj if s.lower().startswith("revert")),
            "review_fixes": sum(1 for s in subj if re.search(r"Codex|\bP[12]\b|review", s)),
            "new_versions": sum(fam_all.values()), "top_families": fam_all.most_common(6),
            "churn_days": churn[:8], "lessons": len(rows), "lesson_rows_unreadable": len(bad_rows), "by_cause": cats.most_common()}


def render_report(r: dict) -> str:
    by = {c["code"]: c for c in CAUSES}
    out = [f"[{r['tool']}] report · {r['since']} 起 · {r['ref']}",
           f"  提交 {r['commits']}(合併 {r['merges']})· 還原 {r['reverts']} · 回審查修補 {r['review_fixes']} · 新版號程式檔 {r['new_versions']} · 教訓 {r['lessons']} 條",
           "  版號最多的家族:" + " · ".join(f"{f} +{n}" for f, n in r["top_families"])]
    if r["churn_days"]:
        out.append("  一天 > 3 版(R9 一則一版):" + " · ".join(f"{f} {d} +{n}" for f, d, n in r["churn_days"]))
    out.append("  重工原因(教訓帳按 %d 類分;多到少):" % len(CAUSES))
    for code, n in r["by_cause"]:
        c = by.get(code)
        out.append(f"    {code:<4} {n:>3} 條 · {c['name'] if c else '未歸類'}")
        if c:
            out.append(f"         偵測:{c['detector']}")
            out.append(f"         解法:{c['fix']}")
    return "\n".join(out)


def render_causes() -> str:
    out = [f"[{TAG}] {len(CAUSES)} 類重工原因 · 偵測器 · 解法 · 指令(內建)"]
    for c in CAUSES:
        out += [f"  {c['code']:<4}{c['name']}", f"       偵測:{c['detector']}", f"       解法:{c['fix']}",
                f"       指令:{c['cmd']}", f"       教訓:{', '.join(c['lessons'])}"]
    return "\n".join(out)


# ─────────────────────────── selftest ───────────────────────────
def selftest() -> int:
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 自測(暫存 git 倉造情境 · 零網路)===", flush=True)
    td = Path(tempfile.mkdtemp(prefix="via_rework_"))
    try:
        r = td / "repo"
        r.mkdir()

        def sh(*a):
            return git(r, *a)
        sh("init", "-q", "-b", "main")
        sh("config", "user.email", "t@example.invalid")
        sh("config", "user.name", "t")
        sh("config", "commit.gpgsign", "false")
        fam = r / VIA / "functional modules" / "VRN"
        fam.mkdir(parents=True)
        acc = "# [VIA:ACCEL-BRIDGE:v0100]\nimport VIA_SuperAccel_Module as VIA_ACCEL\n"
        (fam / "VRN_X_v0100.py").write_text(acc + "def run():\n    return 1\ndef main():\n    return run()\n", encoding="utf-8")
        bookd = r / VIA / "supportive modules" / "registry"
        bookd.mkdir(parents=True)
        (bookd / "VIA_Req_SSOT_v0001.json").write_text(json.dumps({"requirements": [{"id": "R-001"}, {"id": "R-002"}]}), encoding="utf-8")
        locked = fam / "VRN_Lock_v0100.py"
        locked.write_text(acc + "X = 1\n", encoding="utf-8")
        (r / ".github" / "scripts").mkdir(parents=True)
        pg_src = Path(__file__).resolve()
        while pg_src.parent != pg_src and not (pg_src / ".github").is_dir():
            pg_src = pg_src.parent
        shutil.copy(pg_src / ".github" / "scripts" / "pr_guard.py", r / ".github" / "scripts" / "pr_guard.py")
        import hashlib
        led = r / VIA / "docs/handoff/daily"
        led.mkdir(parents=True)
        sha = hashlib.sha256(locked.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        (led / "VIA_SuccessLock_Ledger_v0100.jsonl").write_text(json.dumps({"path": "functional modules/VRN/VRN_Lock_v0100.py", "sha256_lf": sha, "locked_at": "t"}) + "\n", encoding="utf-8")
        (led / "VIA_DailyLessons_Ledger_v0100.jsonl").write_text(
            json.dumps({"id": "LL-20261121-05", "date": _dt.date.today().isoformat(), "problem": "合併搶在 Codex 前", "cause": "", "fix": ""}, ensure_ascii=False) + "\n"
            + json.dumps({"id": "LL-X", "date": _dt.date.today().isoformat(), "problem": "自測吃本機", "cause": "", "fix": ""}, ensure_ascii=False) + "\n", encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        sh("update-ref", "refs/remotes/origin/main", "HEAD")
        clean = run_check(r, "origin/main", "HEAD")
        chk("① 乾淨分支 → 綠(只會有「沒比開著的 PR」灰)", clean["lamp"] == "GREEN" and all(f["lamp"] == "GRAY" for f in clean["findings"]), clean["findings"])
        # 開著的 PR 也發了同號 / 同檔名
        sh("checkout", "-qb", "pr9")
        (fam / "VRN_X_v0101.py").write_text(acc + "# VIA-VRN-MDL900\n", encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "pr9")
        sh("update-ref", "refs/remotes/pr/9", "HEAD")
        sh("checkout", "-q", "main")
        sh("checkout", "-qb", "work")
        (fam / "VRN_X_v0101.py").write_text(
            acc + "import importlib, glob\nPRIOR = None\n# VIA-VRN-MDL900\nPRIOR_NAME = 'VRN_X_v0100.py'\n"
            "def install():\n    PRIOR.helper = 1\n"
            "def selftest():\n    return open('VIA_Reports/x.json').read()\n", encoding="utf-8")
        (fam / "VRN_Net_v0100.py").write_text("import requests\nhtml = requests.get('u').text\nFRED_API_KEY = 'abcdef0123456789abcdef0123456789'\nP = r'" + "C:" + "\\Users\\someone\\x'\n"
                                              "SPEC = 'supportive modules/registry/CGC_MDL224_ScrapeGate_v*.py'\n", encoding="utf-8")
        locked.write_text(acc + "X = 2\n", encoding="utf-8")
        (bookd / "VIA_Req_SSOT_v0003.json").write_text(json.dumps({"requirements": [{"id": "R-001"}, {"id": "R-003"}]}), encoding="utf-8")
        (r / VIA / "functional modules" / "VRN2").mkdir(parents=True)
        (r / VIA / "functional modules" / "VRN2" / "out.json").write_text("{}", encoding="utf-8")
        sh("add", f"{VIA}functional modules/VRN/VRN_X_v0101.py")
        sh("commit", "-qm", "work")
        res = run_check(r, "origin/main", "HEAD", open_prs={"9"})
        txt = json.dumps(res, ensure_ascii=False)
        codes = {(f["lamp"], f["cause"]) for f in res["findings"]}
        res_unk = run_check(r, "origin/main", "HEAD")
        chk("②b 沒有開著的清單 → 同一個撞號只亮黃(沒確認是否還開著)", any(f["cause"] == "R2" and f["lamp"] == "YELLOW" and "#9" in f["what"] for f in res_unk["findings"]), res_unk["findings"])
        chk("② 開著的 PR 同檔名 + 同號 → 紅 R2", ("RED", "R2") in codes and "VIA-VRN-MDL900" in txt and "VRN_X_v0101.py" in txt, res["findings"])
        chk("③ 已鎖成功的檔在工作樹被改(未提交)→ 紅 R1", any(f["cause"] == "R1" and f["lamp"] == "RED" and "VRN_Lock_v0100.py" in f["what"] for f in res["findings"]))
        chk("④ 金鑰常數 → 紅 R11(值不印)", ("RED", "R11") in codes and "abcdef0123456789" not in txt)
        chk("⑤ PRIOR.helper 不是直接前版定義的 → 黃 R4", any(f["cause"] == "R4" and "PRIOR.helper" in f["what"] for f in res["findings"]), res["findings"])
        chk("⑥ 自測讀 VIA_Reports 不用暫存夾 · 前版檔名寫死 → 黃 R5 兩項", sum(1 for f in res["findings"] if f["cause"] == "R5") == 2)
        chk("⑦ 沒加速器匯入 · 匯入 requests 沒網路橋 → 黃 R8 兩項(語法樹)", sum(1 for f in res["findings"] if f["cause"] == "R8" and "VRN_Net_v0100" in f["what"]) == 2)
        chk("⑧ 本機路徑 → 黃 R6 · 讀 CGC_MDL 沒 try → 黃 R10 · 執行期產物 → 黃 R3",
            ("YELLOW", "R6") in codes and ("YELLOW", "R10") in codes and ("YELLOW", "R3") in codes, sorted(codes))
        chk("⑧b 讀 .text 沒指定字集 → 黃 R12 · 新程式檔沒進任何冊 → 黃 R13", ("YELLOW", "R12") in codes and ("YELLOW", "R13") in codes, sorted(codes))
        chk("⑧c 新冊版 v0003 少了 base 尾版 v0001 的 R-002 → 紅 R2(BOOKLOSS)", any(f["cause"] == "R2" and f["lamp"] == "RED" and "R-002" in f["what"] for f in res["findings"]), res["findings"])
        chk("⑨ 總燈紅 · 解法與指令都印得出來", res["lamp"] == "RED" and "解法:" in render_check(res) and "指令:" in render_check(res))
        (r / ".git" / "index.lock").write_text("", encoding="utf-8")
        try:
            chk("⑩ index.lock 在 → 紅 R3(不刪別人的鎖)", any(f["cause"] == "R3" and "index.lock" in f["what"] for f in run_check(r)["findings"]))
        finally:
            (r / ".git" / "index.lock").unlink()
        rep = run_report(r, 7)
        chk("⑪ report:數字從 git 與教訓帳來 · 教訓按 13 類分(R1 由 ID 對上)", rep["commits"] >= 1 and dict(rep["by_cause"]).get("R1") == 1
            and dict(rep["by_cause"]).get("R5") == 1, rep)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    chk("⑫ 13 類都有 偵測器 · 解法 · 指令 · 教訓", len(CAUSES) == 13 and all(c["detector"] and c["fix"] and c["cmd"] and c["lessons"] for c in CAUSES))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑬ 加速器橋 · 不出網 · 不碰 TA-Lib · 不設他系統入口旗標", "import VIA_SuperAccel_Module" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M)
        and not re.search(r"environ(?:\[[\"']VIA_FROM_\w+[\"']\]\s*=|\.setdefault\([\"']VIA_FROM_)", body))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if a[:1] == ["causes"]:
        print(render_causes())
        return 0
    ap = argparse.ArgumentParser(prog="VIA_ReworkGuard")
    ap.add_argument("verb", nargs="?", default="check", choices=("check", "report"))
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--fetch-prs", action="store_true")
    ap.add_argument("--open-prs", default=None, help="開著的 PR 號(逗號分隔);CI 用環境變數 VIA_OPEN_PRS")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--summary", default=os.environ.get("GITHUB_STEP_SUMMARY"))
    o = ap.parse_args(a)
    repo = Path(o.repo) if o.repo else repo_root()
    if o.verb == "report":
        r = run_report(repo, o.days)
        print(json.dumps(r, ensure_ascii=False, indent=1) if o.json else render_report(r))
        return 0
    r = run_check(repo, o.base, o.head, o.fetch_prs, None if o.open_prs is None else {x for x in re.split(r"[\s,]+", o.open_prs) if x.isdigit()})
    text = json.dumps(r, ensure_ascii=False, indent=1) if o.json else render_check(r)
    print(text)
    if o.summary and not o.json:
        with open(o.summary, "a", encoding="utf-8") as fh:
            fh.write("```\n" + text + "\n```\n")
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[r["lamp"]]


if __name__ == "__main__":
    sys.exit(main())
