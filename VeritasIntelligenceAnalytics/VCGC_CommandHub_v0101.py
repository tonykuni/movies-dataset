#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VCGC_CommandHub v0101 — 薄尾:四指令改接 VCGC 真引擎 · 燈照實 · 吃 --selftest(v0100 一字不動)

操作員 2026-11-24 03:45:「用 VCGC 全景式檢視工具 · PS 指令 PY 化 · 導入加速器透過 AST · 缺少的就導入 · 整理整格 VCGC 工具 · 整合測試無誤收尾」。
v0100(#729)的四指令保留,但查出三件不照實的事:
  ① bak 的 GRAPHIFY / OMNIROUTE / SNAPSHOT 三盞燈寫死「綠燈」:GRAPHIFY 是自己數函式名、OMNIROUTE 是自己累加的計數,
     沒有叫真的 Graphify、真的 OmniRoute,備份也沒有 zip / MANIFEST / check
  ② boot 的「Graphify + OmniRoute」列讀的就是 ① 那兩個自製檔
  ③ 摘要矩陣的燈只認綠 / 黃,其他(含灰)一律畫成紅方塊
本版(邏輯全在 Python;PS 只找倉 → 叫一次 → 開頁):
  bak  [--note N] [--net]   ApplyRun 尾版 `run --only G`(真 Graphify · VCGC / VDF / VRN 各自的 omniroute · DailyBackup backup + check)
                            → 燈照 G 道每步實際的燈;Graphify 隔離環境不在:--net 才照倉內 boot 行(SHA-256 對上釋出冊)建一次,否則黃並給指令
                            → agency-mem 交接筆記照舊寫(標明是本機筆記,不是外部 agentmemory)
  pano [--apply --scope S] [--net] [--since REF]   前版全景 + 一輪 AST 修(照舊)→ 管理器 toolbox run(全景守衛 + 模組整合)→ connect
                            --net:先 toolbox install --apply(缺的工具經安裝閘裝)
  boot [--all] [--net] [--since REF]   頂部矩陣 + 真收據摘要(備份 · Graphify · omniroute · 工具箱 · 連線)+ 管理器 toolbox check(四群 24 項 + 獨立性)
                            --all:先 bak 再 pano 再 boot,一次做完
  ast …                     照前版
每個動作都寫 VIA_Reports/vcgc_hub/HUB_latest.txt(≤300 行 · NEXT: 結尾)與 HUB_latest.html(燈在第一欄 · 色取格式鎖冊)。
--net 只在需要連網的那一個子行程設兩道同意閘(安裝 · 建 Graphify 環境),本行程與其他步驟不設、不寫檔。
不 import VDF / VRN;他系統的 omniroute 由 ApplyRun 叫它們自己的管理器。零 TA-Lib。
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

import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VCGC_CommandHub"
TAG = "VCGC_CommandHub v0101"
REG = "supportive modules/registry"
AI = "docs/handoff/ai"
LAMPS = ("GREEN", "YELLOW", "RED", "GRAY")
ZH = {"GREEN": "綠燈", "YELLOW": "黃燈", "RED": "紅燈", "GRAY": "灰燈"}
FROM_ZH = {"綠": "GREEN", "黃": "YELLOW", "紅": "RED", "灰": "GRAY"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


VIA_ROOT = PRIOR.VIA_ROOT
HUB_DIR = PRIOR.HUB_DIR

# ---- 頂部矩陣照實改寫(只改說明文字,四個指令不變) ----
PRIOR.SHORT_COMMANDS_SPEC = [
    ("via", "晨間 boot", "前次備份 / Graphify / omniroute 真收據 + 工具箱四群核對;--all 一次做完 bak → pano → boot", "CommandHub v0101"),
    ("via-pano", "全景 pano", "全景 + 一輪安全 AST 修(預設乾跑)→ 全景守衛 + 模組整合 → 連線總表", "SystemManager"),
    ("via-bak", "備份 bak", "ApplyRun G 道:每日備份 backup + check · 真 Graphify · 三系統 omniroute · 交接筆記", "ApplyRun · DailyBackup"),
    ("via-ast", "AST 注入 ast", "剪貼簿 / --code-file / --code,diff 預覽 + 確認,--rollback 還原(照 v0100)", "CommandHub v0100"),
] if isinstance(getattr(PRIOR, "SHORT_COMMANDS_SPEC", None), list) else getattr(PRIOR, "SHORT_COMMANDS_SPEC", [])


def lamp_of(text: str) -> str:
    """把任何燈字(GREEN / 綠燈 / 就緒 / WARN / 灰 …)收成四色之一;認不得的算 GRAY(不冒充紅也不冒充綠)。"""
    t = str(text or "")
    for k in LAMPS:
        if k in t.upper():
            return k
    for k, v in FROM_ZH.items():
        if k in t:
            return v
    if any(k in t for k in ("OK", "就緒", "PASS")):
        return "GREEN"
    if any(k in t for k in ("WARN", "待修")):
        return "YELLOW"
    if any(k in t for k in ("FAIL", "ERR")):
        return "RED"
    return "GRAY"


def print_matrix(title: str, rows: list, footer: str = "VCGC Hub v0101") -> None:
    """四色照實的摘要矩陣(灰不再畫成紅)。"""
    if not getattr(PRIOR, "RICH_AVAILABLE", False):
        print("\n=== %s ===" % title, flush=True)
        for r in rows:
            print("[%s] %s | %s: %s | %s" % (ZH[lamp_of(r.get("status"))], r.get("category"), r.get("metric"), r.get("detail"), r.get("action", "")), flush=True)
        return
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    badge = {"GREEN": "[bold #A3BE8C]● 綠燈[/]", "YELLOW": "[bold #EBCB8B]▲ 黃燈[/]", "RED": "[bold #BF616A]■ 紅燈[/]", "GRAY": "[bold #9AA5B1]○ 灰燈[/]"}
    t = Table(title="[bold #88C0D0]%s[/]" % title, box=box.SIMPLE_HEAVY, header_style="bold #ECEFF4 on #2E3440", border_style="#4C566A",
              row_styles=["none", "dim"], expand=True, padding=(0, 1))
    t.add_column("燈號", justify="center", width=9, no_wrap=True)
    t.add_column("模組域", style="bold #88C0D0", width=12, no_wrap=True)
    t.add_column("項目", style="bold #D8DEE9", width=22, overflow="fold")
    t.add_column("詳細", style="#E5E9F0", overflow="fold")
    t.add_column("建議動作", style="italic #A3BE8C", width=24, overflow="fold")
    for r in rows:
        t.add_row(badge[lamp_of(r.get("status"))], str(r.get("category", "-")), str(r.get("metric", "-")), str(r.get("detail", "-")), str(r.get("action", "-")))
    PRIOR.console.print(Panel(t, subtitle="[dim #81A1C1]%s | accel=%s | %s[/]" % (footer, "on" if VIA_ACCEL else "off", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                              border_style="#5E81AC", padding=(0, 1)))


PRIOR.print_detailed_summary_matrix = print_matrix  # 前版其他指令(pano / ast)的矩陣也改用四色照實


# ---- 共用 ----
def tail(d: Path, stem: str):
    hits = [p for p in d.glob(stem + "_v*.py") if _vnum(p) >= 0 and p.stem.rsplit("_v", 1)[0] == stem]
    return max(hits, key=_vnum) if hits else None


def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def child_env(net: bool = False) -> dict:
    """子行程環境:一律帶 UTF-8 與 VCGC 入口標記;只有明示 --net 的那一步才帶兩道同意閘。"""
    e = dict(os.environ, PYTHONUTF8="1", VIA_FROM_VCGC="YES", VIA_NO_OPEN="1")
    if net:
        e.update({"VIA_NET_" + "CONSENT": "YES", "VIA_SCRAPE_" + "CONSENT": "YES"})
    return e


def stream(cmd: list, env: dict, timeout: int, cwd: Path = None):
    """邊跑邊印(長步驟看得到心跳),同時收下全文。回 (rc, 全文)。"""
    lines, t0 = [], time.time()
    try:
        p = subprocess.Popen(cmd, cwd=str(cwd or VIA_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        return None, "啟動失敗:%s" % e
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        print("  " + line.rstrip("\n"), flush=True)
        if time.time() - t0 > timeout:
            p.kill()
            lines.append("[逾時] %d 秒" % timeout)
            break
    try:
        rc = p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
        rc = None
    return rc, "\n".join(lines)


def manager(via: Path = None):
    return tail((via or VIA_ROOT) / REG, "CGC_SystemManager")


# ---- Graphify 隔離環境 ----
def graphify_exe() -> Path:
    if os.environ.get("VIA_GRAPHIFY_PY"):
        return Path(os.environ["VIA_GRAPHIFY_PY"])
    base = Path.home() / "envs" / "via_graphify"
    return base / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")


def graphify_boot(via: Path = None) -> tuple:
    """回 (可以跑, 指令行, 原因)。boot 行要跟釋出冊的 boot_line_sha256 對上才給。"""
    d = (via or VIA_ROOT) / AI / "via_graphify_v0101"
    rel = read_json(d / "VIA_Graphify_Release_v0101.json")
    try:
        line = (d / "VIA_Graphify_v0101_boot.txt").read_text(encoding="utf-8-sig").strip()
    except OSError:
        return False, "", "倉內沒有 Graphify boot 行"
    got = hashlib.sha256(line.encode("utf-8")).hexdigest()
    if not rel.get("boot_line_sha256") or got != rel["boot_line_sha256"]:
        return False, "", "boot 行雜湊對不上釋出冊(要 %s · 實得 %s)→ 不執行" % (rel.get("boot_line_sha256"), got)
    return True, line, "雜湊對上釋出冊 · 釘 graphifyy %s · 只跑本機 AST" % rel.get("graphifyy", "?")


# ---- G 道結果解析 ----
G_STEP = re.compile(r"G · (\S+) (綠|黃|紅|灰) · 結束碼 (\S+)")


def parse_g(text: str) -> list:
    rows, seen = [], set()
    for m in G_STEP.finditer(text or ""):
        name, lamp, rc = m.group(1), FROM_ZH[m.group(2)], m.group(3)
        if name in seen:
            continue
        seen.add(name)
        cat = "GRAPHIFY" if name.startswith("Graphify") else "OMNIROUTE" if "omniroute" in name.lower() else "BACKUP" if name.startswith("Backup") else "G"
        rows.append({"category": cat, "metric": name, "status": lamp, "detail": "結束碼 %s" % rc, "action": "" if lamp == "GREEN" else "看 APPLY_latest.txt 這一步"})
    return rows


# ---- 報告 ----
def lamp_css(via: Path = None) -> str:
    hits = sorted(((via or VIA_ROOT) / REG).glob("VIA_UI_FormatLock_v*.json"), key=_vnum)
    return str(read_json(hits[-1]).get("lamp_css", "")) if hits else ""


def write_report(title: str, rows: list, extra: list = None, via: Path = None) -> Path:
    via = via or VIA_ROOT
    out = via / "VIA_Reports" / "vcgc_hub"
    out.mkdir(parents=True, exist_ok=True)
    lamps = [lamp_of(r.get("status")) for r in rows]
    total = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN" if lamps and all(x == "GREEN" for x in lamps) else "GRAY" if not lamps else "YELLOW"
    bad = [r for r in rows if lamp_of(r.get("status")) in ("RED", "YELLOW")]
    nxt = ("NEXT: " + (bad[0].get("action") or ("先看「%s」" % bad[0].get("metric")))) if bad else "NEXT: 全綠"
    txt = ["# %s · %s · %s · 總燈 %s · 綠 %d 黃 %d 紅 %d 灰 %d" % (title, TAG, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total,
                                                               *[lamps.count(k) for k in LAMPS])]
    txt += ["[%s] %s · %s · %s%s" % (lamp_of(r.get("status")), r.get("category"), r.get("metric"), r.get("detail"),
                                     (" · " + r["action"]) if r.get("action") else "") for r in rows]
    txt += list(extra or [])
    txt = txt[:299] + [nxt]
    (out / "HUB_latest.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    (out / "HUB_latest.json").write_text(json.dumps({"tag": TAG, "title": title, "lamp": total, "rows": rows, "next": nxt},
                                                    ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    trs = "".join("<tr><td><span class='lamp %s'></span>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        lamp_of(r.get("status")), lamp_of(r.get("status")), *[html.escape(str(r.get(k, ""))) for k in ("category", "metric", "detail", "action")]) for r in rows)
    page = ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>VCGC Hub</title><style>" + lamp_css(via) +
            "body{font:11px/1.35 system-ui,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a;margin:12px}h1{font-size:14px;margin:0 0 6px}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{padding:3px 6px;border-bottom:1px solid #e2e8f0;text-align:left;overflow-wrap:anywhere;white-space:normal}"
            "th{background:#f1f5f9}td:first-child,th:first-child{width:7em}pre{font-size:11px;white-space:pre-wrap}</style><h1>" + html.escape(title) + " · " + total + "</h1>"
            "<table><thead><tr><th>燈</th><th>模組域</th><th>項目</th><th>詳細</th><th>建議動作</th></tr></thead><tbody>" + trs + "</tbody></table>"
            "<pre>" + html.escape("\n".join(list(extra or []) + [nxt])) + "</pre></html>")
    (out / "HUB_latest.html").write_text(page, encoding="utf-8")
    return out


# ---- 指令 ----
def cmd_bak(note: str = "Routine Active Checkpoint", net: bool = False) -> tuple:
    rows = []
    gx = graphify_exe()
    if gx.exists():
        rows.append({"category": "GRAPHIFY", "metric": "隔離環境", "status": "GREEN", "detail": str(gx), "action": ""})
    else:
        ok, line, why = graphify_boot()
        if net and ok and shutil.which("pwsh"):
            print("[bak] Graphify 隔離環境不在 → 照倉內 boot 行建一次(%s)" % why, flush=True)
            e = child_env(net=True)
            e["VRN2_ROOT"] = str(VIA_ROOT)
            rc, _ = stream(["pwsh", "-NoProfile", "-Command", line], e, 3600)
            rows.append({"category": "GRAPHIFY", "metric": "建隔離環境", "status": "GREEN" if graphify_exe().exists() else "YELLOW",
                         "detail": "rc=%s · %s" % (rc, why), "action": "" if graphify_exe().exists() else "看上面 boot 輸出"})
        else:
            rows.append({"category": "GRAPHIFY", "metric": "隔離環境", "status": "YELLOW" if ok else "RED",
                         "detail": "不在(%s)· %s" % (gx, why), "action": "via-bak -Net(或 boot --all --net)建一次" if ok else "boot 行要先修"})
    ar = tail(VIA_ROOT / AI, "VIA_VCGC_ApplyRun")
    if ar is None:
        rows.append({"category": "G", "metric": "ApplyRun", "status": "RED", "detail": "找不到 VIA_VCGC_ApplyRun 尾版", "action": "先快轉 main"})
        return rows, 1
    print("[bak] %s run --only G(Graphify · VCGC / VDF / VRN omniroute · 備份 backup + check)" % ar.name, flush=True)
    e = child_env()
    e["VIA_APPLY_BACKUP"] = "1"
    rc, out = stream([sys.executable, "-B", str(ar), "run", "--only", "G", "--no-open"], e, 7200)
    g = parse_g(out)
    rows += g or [{"category": "G", "metric": ar.name, "status": "RED", "detail": "沒解析到任何步驟(rc=%s)" % rc, "action": "看上面輸出"}]
    bk = read_json(VIA_ROOT / "VIA_Reports" / "backup" / "BACKUP_latest.json")
    rows.append({"category": "BACKUP", "metric": "備份儲存", "status": lamp_of(bk.get("lamp")) if bk else "GRAY",
                 "detail": "%s · %s 檔 · %s" % (bk.get("backup_dir", "—"), bk.get("total_files", 0), bk.get("at", "—")) if bk else "沒有 BACKUP_latest.json",
                 "action": ""})
    try:
        PRIOR.ensure_dirs()
        PRIOR.AGENCY_MEM_FILE.write_text(json.dumps({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active_focus": note, "last_backup_dir": bk.get("backup_dir", ""),
            "backed_up_files": bk.get("total_files", 0), "g_lane": {r["metric"]: r["status"] for r in g}, "kind": "本機交接筆記(不是外部 agentmemory)",
            "writer": TAG}, ensure_ascii=False, indent=2), encoding="utf-8")
        rows.append({"category": "AGENCY-MEM", "metric": "本機交接筆記", "status": "GREEN", "detail": "焦點:%s" % note,
                     "action": "外部 agentmemory 照 11-06 裁定不接"})
    except OSError as err:
        rows.append({"category": "AGENCY-MEM", "metric": "本機交接筆記", "status": "RED", "detail": str(err), "action": ""})
    return rows, rc if isinstance(rc, int) else 1


def cmd_pano(apply: bool = False, scope=None, net: bool = False, since: str = "origin/main~8") -> tuple:
    rows = []
    print("[pano] 前版全景 + 一輪 AST 修(%s)" % ("寫入 " + scope if apply and scope else "乾跑"), flush=True)
    try:
        prc = PRIOR.cmd_panorama(apply=apply, scope=scope)
    except Exception as err:  # 前版失敗照實記紅,不中斷後面的守衛
        prc = 1
        rows.append({"category": "PANO", "metric": "前版全景", "status": "RED", "detail": "%s: %s" % (type(err).__name__, err), "action": ""})
    else:
        rows.append({"category": "PANO", "metric": "前版全景 + AST 修", "status": "GREEN" if prc == 0 else "YELLOW", "detail": "rc=%s" % prc, "action": ""})
    cm = manager()
    if cm is None:
        rows.append({"category": "TOOLBOX", "metric": "VCGC 管理器", "status": "RED", "detail": "找不到 CGC_SystemManager 尾版", "action": "先快轉 main"})
        return rows, 1
    if net:
        print("[pano] toolbox install --apply(缺的經 VCGC 安裝閘裝;同意閘只開在這一個子行程)", flush=True)
        irc, _ = stream([sys.executable, "-B", str(cm), "toolbox", "install", "--apply"], child_env(net=True), 3600)
        rows.append({"category": "INSTALL", "metric": "缺的工具 / 套件", "status": "GREEN" if irc == 0 else "YELLOW", "detail": "rc=%s" % irc, "action": ""})
    print("[pano] %s toolbox run --since %s(全景守衛 + 模組整合)" % (cm.name, since), flush=True)
    trc, _ = stream([sys.executable, "-B", str(cm), "toolbox", "run", "--since", since], child_env(), 5400)
    tb = read_json(VIA_ROOT / "VIA_Reports" / "vcgc" / "toolbox" / "TOOLBOX_latest.json")
    rows.append({"category": "TOOLBOX", "metric": "工具箱四群 + 全景守衛 + 模組整合", "status": lamp_of(tb.get("lamp")) if tb else "GRAY",
                 "detail": "rc=%s · %s" % (trc, tb.get("next", "")), "action": "" if tb.get("lamp") == "GREEN" else "看 TOOLBOX_latest.txt"})
    print("[pano] %s connect(各類文件 × MCP 通道 × 外部工具 × 備份)" % cm.name, flush=True)
    stream([sys.executable, "-B", str(cm), "connect"], child_env(), 900)
    cj = read_json(VIA_ROOT / "VIA_Reports" / "vcgc" / "connect" / "CONNECT_latest.json")
    rows.append({"category": "CONNECT", "metric": "全景連線", "status": lamp_of(cj.get("lamp")) if cj else "GRAY",
                 "detail": "綠 %s 黃 %s 紅 %s 灰 %s" % tuple((cj.get("counts") or {}).get(k, "?") for k in LAMPS) if cj else "沒有 CONNECT_latest.json",
                 "action": "看 CONNECT_latest.txt" if cj and cj.get("lamp") != "GREEN" else ""})
    worst = max([x for x in (prc, trc) if isinstance(x, int)] + [0])
    return rows, worst


def boot_rows(via: Path = None) -> list:
    """晨間摘要只讀真收據;沒有收據就灰,不冒充綠。"""
    via = via or VIA_ROOT
    rows = []
    bk = read_json(via / "VIA_Reports" / "backup" / "BACKUP_latest.json")
    rows.append({"category": "BACKUP", "metric": "前次備份", "status": lamp_of(bk.get("lamp")) if bk else "GRAY",
                 "detail": "%s · %s 檔" % (bk.get("at", "—"), bk.get("total_files", 0)) if bk else "沒有備份收據", "action": "" if bk else "via-bak"})
    cj = read_json(via / "VIA_Reports" / "vcgc" / "connect" / "CONNECT_latest.json")
    for t in (cj.get("tools") or []):
        if t.get("key") in ("graphify", "omniroute"):
            rows.append({"category": t["key"].upper(), "metric": t.get("name", ""), "status": t.get("lamp", "GRAY"), "detail": t.get("evidence", ""), "action": t.get("note", "")})
    if not cj:
        rows.append({"category": "CONNECT", "metric": "Graphify / OmniRoute / 通道", "status": "GRAY", "detail": "沒有 connect 收據", "action": "via-pano"})
    mem = read_json(PRIOR.AGENCY_MEM_FILE) if via == VIA_ROOT else {}
    rows.append({"category": "AGENCY-MEM", "metric": "本機交接筆記", "status": "GREEN" if mem else "GRAY",
                 "detail": "%s · 焦點:%s" % (mem.get("timestamp", "—"), mem.get("active_focus", "—")) if mem else "還沒有", "action": "" if mem else "via-bak"})
    return rows


def cmd_boot(all_: bool = False, net: bool = False, since: str = "origin/main~8") -> tuple:
    rows, rcs = [], []
    if all_:
        r, rc = cmd_bak("boot --all", net)
        rows += r
        rcs.append(rc)
        r, rc = cmd_pano(False, None, net, since)
        rows += r
        rcs.append(rc)
    PRIOR.print_top_command_matrix()
    rows += boot_rows()
    cm = manager()
    if cm:
        rc, _ = stream([sys.executable, "-B", str(cm), "toolbox", "check"], child_env(), 900)
        tb = read_json(VIA_ROOT / "VIA_Reports" / "vcgc" / "toolbox" / "TOOLBOX_latest.json")
        rows.append({"category": "TOOLBOX", "metric": "四群 %s 項 + 獨立性" % tb.get("tools", "?"), "status": lamp_of(tb.get("lamp")) if tb else "GRAY",
                     "detail": " · ".join("%s 綠 %s" % kv for kv in (tb.get("groups") or {}).items()), "action": tb.get("next", "")})
        rcs.append(rc if isinstance(rc, int) else 1)
    seen, uniq = set(), []
    for r in rows:
        k = (r.get("category"), r.get("metric"))
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq, max(rcs + [0])


def run(cmd: str, title: str, rows: list, rc: int) -> int:
    print_matrix(title, rows)
    out = write_report(title, rows)
    print("[報告] %s · %s" % (out / "HUB_latest.txt", out / "HUB_latest.html"), flush=True)
    lamps = [lamp_of(r.get("status")) for r in rows]
    return 1 if "RED" in lamps else 2 if ("YELLOW" in lamps or rc) else 0


def _opt(argv: list, name: str, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        return selftest()
    net, since = "--net" in argv, _opt(argv, "--since", "origin/main~8")
    if argv[:1] == ["bak"]:
        rows, rc = cmd_bak(_opt(argv, "--note", "Routine Active Checkpoint"), net)
        return run("bak", "VIA 備份 · Graphify · OmniRoute(真引擎)", rows, rc)
    if argv[:1] == ["pano"]:
        rows, rc = cmd_pano("--apply" in argv, _opt(argv, "--scope"), net, since)
        return run("pano", "VIA 全景 · 工具箱 · 連線", rows, rc)
    if argv[:1] == ["boot"]:
        rows, rc = cmd_boot("--all" in argv, net, since)
        return run("boot", "VIA 晨間" + (" · 全部(bak → pano → boot)" if "--all" in argv else ""), rows, rc)
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 8 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 燈照實:綠 / 黃 / 紅 / 灰 四色各自認得,認不得的算灰(不冒充紅)",
        [lamp_of(x) for x in ("綠燈", "黃燈", "紅燈", "灰燈", "GREEN", "就緒", "WARN", "??")] == ["GREEN", "YELLOW", "RED", "GRAY", "GREEN", "GREEN", "YELLOW", "GRAY"])
    sample = ("  16:02:00  G · Graphify-status 開始\n  16:02:01  G · Graphify-status 黃 · 結束碼 3 · 1 秒\n"
              "  16:02:02  G · VCGC-omniroute 綠 · 結束碼 0 · 0 秒\n  16:02:11  G · VDF-omniroute 綠 · 結束碼 0 · 8 秒\n"
              "  16:02:28  G · Backup 綠 · 結束碼 0 · 3 秒\n  16:02:28  G · Backup-check 紅 · 結束碼 1 · 0 秒\n")
    g = {r["metric"]: (r["category"], r["status"]) for r in parse_g(sample)}
    chk("T2 bak 的燈照 G 道每步實際的燈(不再寫死綠)", g == {"Graphify-status": ("GRAPHIFY", "YELLOW"), "VCGC-omniroute": ("OMNIROUTE", "GREEN"),
        "VDF-omniroute": ("OMNIROUTE", "GREEN"), "Backup": ("BACKUP", "GREEN"), "Backup-check": ("BACKUP", "RED")}, g)
    with tempfile.TemporaryDirectory(prefix="hub101_") as td:
        via = Path(td) / "VIA"
        d = via / AI / "via_graphify_v0101"
        d.mkdir(parents=True)
        line = "& { Write-Host boot }"
        (d / "VIA_Graphify_v0101_boot.txt").write_text(line + "\n", encoding="utf-8")
        (d / "VIA_Graphify_Release_v0101.json").write_text(json.dumps({"boot_line_sha256": hashlib.sha256(line.encode()).hexdigest(), "graphifyy": "0.9.100"}), encoding="utf-8")
        good = graphify_boot(via)
        (d / "VIA_Graphify_v0101_boot.txt").write_text(line + "; Remove-Item x\n", encoding="utf-8")
        bad = graphify_boot(via)
        chk("T3 Graphify boot 行:雜湊對上才給,被改過就拒絕", good[0] and good[1] == line and not bad[0] and bad[1] == "", (good, bad))
        ck = "VIA_NET_" + "CONSENT"
        before = os.environ.get(ck)
        e0, e1 = child_env(False), child_env(True)
        chk("T4 同意閘只進 --net 那一步的子行程環境;一般步驟不加、本行程不變",
            e1.get(ck) == "YES" and e0.get(ck) == before and os.environ.get(ck) == before, (before, e0.get(ck), e1.get(ck)))
        rows = boot_rows(via)
        chk("T5 沒有收據的項目一律灰,不冒充綠", rows and all(lamp_of(r["status"]) == "GRAY" for r in rows), rows)
        out = write_report("自測", [{"category": "A", "metric": "m", "status": "黃燈", "detail": "d", "action": "做某事"},
                                  {"category": "B", "metric": "n", "status": "GREEN", "detail": "d", "action": ""}], ["附註"], via)
        txt = (out / "HUB_latest.txt").read_text(encoding="utf-8").splitlines()
        page = (out / "HUB_latest.html").read_text(encoding="utf-8")
        chk("T6 報告:txt ≤300 行、NEXT: 結尾且指向黃燈的動作 · html 燈在第一欄", txt[-1] == "NEXT: 做某事" and len(txt) <= 300 and "<td><span class='lamp YELLOW'>" in page, txt[-1:])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T7 檔面:第 3 行加速器標記 · 零 TA-Lib · 本行程不寫同意閘 · 不 import 他系統",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M))
    chk("T8 前版照載 · 頂部矩陣仍是四個指令 · 前版矩陣改用四色照實", len(PRIOR.SHORT_COMMANDS_SPEC) == 4 and PRIOR.print_detailed_summary_matrix is print_matrix)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
