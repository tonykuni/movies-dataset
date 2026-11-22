#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0117 — 薄尾:VCGC 管理器統管開發支援工具箱(toolbox · guard · fuse)

操作員 2026-11-22 09:09:「one ps to handle all. ensure VCGC System Manager control all of these functions interrelated without missing.
整理好工具用中文白話文詳細說明工具用途」。
本版讓 VCGC 自己的管理器一個入口管全部開發支援工具,而且逐一核「有沒有漏」:
  toolbox [check]        十個工具逐一核七件事:尾版在 · 有編號 · 有登錄(元件冊)· 有交接測試案 · 有盤點站 · 管理器有路由 ·
                         (工具類)引擎版本冊有一列 → 每個工具一盞燈;寫 VIA_Reports/vcgc/toolbox/TOOLBOX_latest.json|txt|html
  toolbox help [工具]    印白話說明書(docs/handoff/VCGC_ToolManual_v*.md 尾版)的那一節
  toolbox install [--apply]   算出全景守衛 15 工具 + 模組整合 15 套件還缺哪些;--apply 才經 VCGC 安裝閘(CGC_MDL056 尾版)裝
                         (本檔不設同意閘;要連網裝,由操作員端啟動器只在那一個行程設)
  toolbox run [--since <git 參照>]   一次跑:check → 全景守衛 scan --changed-since → 模組整合 doctor + selftest → 合併貼回包(≤300 行,NEXT: 結尾)
  guard <參數…>          轉交全景守衛尾版(VIA_PanoramaGuard),例:guard tools · guard scan --root <倉> --changed-since origin/main
  fuse <參數…>           轉交模組整合尾版(VIA_ModuFuse),自動帶鎖定的加速器路徑(VIA_CELERITAS_PATH)
其餘動詞全部照 v0116(omniroute · engine-matrix · 獨立 MAIN …)。唯讀核對;只寫自己的報告夾;不改 VDF / VRN 的檔。
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

import html
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "CGC_SystemManager"
TAG = "CGC_SystemManager v0117"
REG = "supportive modules/registry"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if "cgc_prior_for_v0117" in sys.modules:
    PRIOR = sys.modules["cgc_prior_for_v0117"]
else:
    _spec = importlib.util.spec_from_file_location("cgc_prior_for_v0117", PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules["cgc_prior_for_v0117"] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


# 工具箱目錄:key · 白話名 · 族名 · 資料夾 · 自測參數 · 管理器路由 · 引擎版本冊的族(工具類才有)· 鎖冊鍵
TOOLBOX = [
    {"key": "token", "name": "省 Token 工具(骨架卡 · 片段 · 日誌摘要)", "stem": "CGC_MDL158_VIAPanoramaAuditRepair", "dir": REG,
     "route": "via-vcgc token / 本檔 read · slice · digest", "family": "token", "lock": "token"},
    {"key": "guard", "name": "全景守衛(全景掃描 + 安全修復一輪 · 15 個在地工具)", "stem": "VIA_PanoramaGuard", "dir": REG,
     "route": "toolbox run · guard …", "family": "panorama-guard"},
    {"key": "fuse", "name": "模組整合去重(拳腳 · 單檔 FNC-LIB)", "stem": "VIA_ModuFuse", "dir": REG, "route": "fuse …", "family": "modufuse"},
    {"key": "install", "name": "安裝閘(裝套件只走這裡)", "stem": "CGC_MDL056_InstallGate", "dir": REG, "route": "toolbox install --apply"},
    {"key": "handoff", "name": "交接閘(交接資料完整不完整)", "stem": "CGC_MDL140_HandoverConsole", "dir": REG, "route": "via-vcgc handoff check"},
    {"key": "numbering", "name": "編號系統(發號 · 稽核)", "stem": "CGC_MDL237_NumberingSystem", "dir": REG, "route": "via-vcgc run CGC_MDL237_NumberingSystem audit"},
    {"key": "sdd", "name": "SDD 驗證(需求 · 工作流 · 編號對得起來)", "stem": "CGC_MDL245_SDDValidator", "dir": REG, "route": "via-vcgc sdd check"},
    {"key": "applyrun", "name": "一鍵套用啟動器(各道一起跑)", "stem": "VIA_VCGC_ApplyRun", "dir": "docs/handoff/ai", "route": "Invoke-VIA-ApplyAll"},
    {"key": "manager", "name": "VCGC 管理器本身(omniroute · toolbox)", "stem": "CGC_SystemManager", "dir": REG, "route": "本檔"},
    {"key": "accel", "name": "加速器 VeritasCeleritas(鎖定版)", "stem": None, "dir": "supportive modules", "route": "自動(各工具自己載)", "lock": "accelerator"},
]
FUSE_LIBS = ["joblib", "psutil", "asttokens", "parso", "jsonschema", "packaging", "more-itertools", "msgpack", "zstandard",
             "PyYAML", "XlsxWriter", "Pygments", "pydantic", "mcp", "anyio"]
FUSE_MODS = {"more-itertools": "more_itertools", "PyYAML": "yaml", "XlsxWriter": "xlsxwriter", "Pygments": "pygments"}


def tail(via: Path, d: str, stem: str):
    hits = [p for p in (via / d).glob(stem + "_v*.py") if _vnum(p) >= 0 and p.stem.rsplit("_v", 1)[0] == stem]
    return max(hits, key=_vnum) if hits else None


def lock_path(via: Path, key: str):
    try:
        lk = json.loads((via / REG / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        rel = (lk.get(key) or {}).get("path", "")
    except (OSError, ValueError):
        return None
    p = via.parent / rel
    return p if rel and p.is_file() else None


def _latest(via: Path, pattern: str):
    hits = sorted((via / REG).glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _number_sources(via: Path) -> set:
    out = set()
    for f in (via / REG / "VIA_NumberBooks").glob("*.jsonl"):
        try:
            for line in f.open(encoding="utf-8"):
                m = re.search(r'"source":\s*"([^"]+)"', line)
                if m:
                    out.add(m.group(1).replace("\\\\", "/"))
        except OSError:
            continue
    return out


def check(via: Path = VIA_ROOT) -> dict:
    """逐工具核七件事;只讀。"""
    nums = _number_sources(via)
    try:
        comp = (via / REG / "VIA_Component_Inventory_SSOT_v0100.json").read_text(encoding="utf-8")
    except OSError:
        comp = ""
    try:
        hb = json.loads((via / REG / "VIA_Handoff_Continuity_SSOT_v0100.json").read_text(encoding="utf-8"))
        cases = json.dumps(hb.get("test_cases", {}), ensure_ascii=False)
    except (OSError, ValueError):
        cases = ""
    inv_p = _latest(via, "VIA_VCGC_FunctionInventory_SSOT_v*.json")
    inv = inv_p.read_text(encoding="utf-8") if inv_p else ""
    try:
        eng = json.loads((via / REG / "VIA_EngineVersion_Register_v0100.json").read_text(encoding="utf-8")).get("rows", [])
    except (OSError, ValueError):
        eng = []
    rows = []
    for t in TOOLBOX:
        if t["stem"] is None:
            p = lock_path(via, t["lock"])
            items = {"尾版在": bool(p), "鎖冊": bool(p)}
            rows.append({"key": t["key"], "name": t["name"], "tail": p.name if p else None, "items": items, "route": t["route"],
                         "lamp": "GREEN" if p else "RED", "missing": [k for k, v in items.items() if not v]})
            continue
        p = tail(via, t["dir"], t["stem"])
        rel = p.relative_to(via).as_posix() if p else ""
        items = {"尾版在": bool(p),
                 "有編號": bool(p) and rel in nums,
                 "有登錄": bool(p) and p.name in comp,
                 "有交接測試案": bool(p) and (p.name in cases or t["stem"] in cases),
                 "有盤點站": bool(p) and t["stem"] in inv,
                 "管理器有路由": True}
        if t.get("family"):
            items["引擎版本冊"] = any(r.get("family") == t["family"] and r.get("file") == (p.name if p else None) for r in eng)
        if t.get("lock"):
            lp = lock_path(via, t["lock"])
            items["鎖冊指到尾版"] = bool(p and lp and lp.resolve() == p.resolve())
        miss = [k for k, v in items.items() if not v]
        lamp = "RED" if not p else ("GREEN" if not miss else "YELLOW")
        rows.append({"key": t["key"], "name": t["name"], "tail": p.name if p else None, "items": items, "route": t["route"],
                     "lamp": lamp, "missing": miss})
    lamps = [r["lamp"] for r in rows]
    return {"tag": TAG, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tools": len(rows), "rows": rows,
            "lamp": "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN",
            "inventory": inv_p.name if inv_p else None}


def _lamp_css(via: Path) -> str:
    p = _latest(via, "VIA_UI_FormatLock_v*.json")
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("lamp_css", "") if p else ""
    except (OSError, ValueError):
        return ""


def write_report(via: Path, res: dict, extra_lines=None) -> Path:
    out = via / "VIA_Reports" / "vcgc" / "toolbox"
    out.mkdir(parents=True, exist_ok=True)
    (out / "TOOLBOX_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# VCGC 工具箱 · %s · %s · 總燈 %s" % (TAG, res["at"], res["lamp"])]
    for r in res["rows"]:
        lines.append("[%s] %s · %s · 尾版 %s%s" % (r["lamp"], r["key"], r["name"], r["tail"] or "—",
                                               (" · 缺:" + "、".join(r["missing"])) if r["missing"] else ""))
    lines += list(extra_lines or [])
    nxt = res.get("next") or ("NEXT: 全部齊了" if res["lamp"] == "GREEN" else "NEXT: 補缺的那幾件(見各列「缺」)")
    lines = lines[:299] + [nxt]
    (out / "TOOLBOX_latest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    trs = "".join("<tr><td><span class='lamp %s'></span>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        r["lamp"], r["lamp"], html.escape(r["key"]), html.escape(r["name"]), html.escape(r["tail"] or "—"),
        html.escape(" · ".join(("✔" if v else "✘") + k for k, v in r["items"].items())), html.escape(r["route"])) for r in res["rows"])
    page = ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>VCGC 工具箱</title><style>"
            + _lamp_css(via) + "body{font:11px/1.35 system-ui,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a;margin:12px}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{padding:3px 6px;border-bottom:1px solid #e2e8f0;text-align:left;"
            "overflow-wrap:anywhere;white-space:normal}th{background:#f1f5f9}td:first-child,th:first-child{width:8em}h1{font-size:14px;margin:0 0 6px}"
            "pre{font-size:11px;white-space:pre-wrap}</style><h1>VCGC 開發支援工具箱 · " + html.escape(res["lamp"]) + "</h1>"
            "<table><thead><tr><th>燈</th><th>代號</th><th>工具</th><th>尾版</th><th>七件事</th><th>怎麼叫</th></tr></thead><tbody>" + trs +
            "</tbody></table>" + ("<pre>" + html.escape("\n".join(extra_lines)) + "</pre>" if extra_lines else "") + "</html>")
    (out / "TOOLBOX_latest.html").write_text(page, encoding="utf-8")
    return out


def manual(via: Path = VIA_ROOT):
    hits = sorted((via / "docs" / "handoff").glob("VCGC_ToolManual_v*.md"), key=_vnum)
    return hits[-1] if hits else None


def help_text(key: str = "", via: Path = VIA_ROOT) -> str:
    m = manual(via)
    if not m:
        return "找不到白話說明書(docs/handoff/VCGC_ToolManual_v*.md)"
    text = m.read_text(encoding="utf-8")
    if not key:
        return text
    parts = re.split(r"(?m)^## ", text)
    for p in parts:
        if re.match(r"[^\n]*`%s`" % re.escape(key), p):
            return "## " + p.strip()
    return "說明書沒有「%s」這一節;可用:%s" % (key, ", ".join(t["key"] for t in TOOLBOX))


def missing_packages(via: Path = VIA_ROOT) -> dict:
    """全景守衛 15 工具 + 模組整合 15 套件,還缺哪些(只看,不裝)。"""
    out = {"guard": [], "fuse": []}
    g = tail(via, REG, "VIA_PanoramaGuard")
    if g:
        try:
            p = subprocess.run([sys.executable, "-B", str(g), "tools"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=120, env=dict(os.environ, PYTHONUTF8="1"))
            m = re.search(r"InstallGate\s+(.+)$", p.stdout or "", re.M)
            out["guard"] = m.group(1).split() if m else []
        except (OSError, subprocess.SubprocessError):
            out["guard"] = ["?"]
    for dist in FUSE_LIBS:
        mod = FUSE_MODS.get(dist, dist)
        try:
            found = importlib.util.find_spec(mod) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            out["fuse"].append(dist)
    return out


def install(apply: bool, via: Path = VIA_ROOT) -> int:
    miss = missing_packages(via)
    pkgs = [p for p in dict.fromkeys(miss["guard"] + miss["fuse"]) if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", p)]
    print("[%s] toolbox install · 全景守衛缺 %s · 模組整合缺 %s" % (TAG, " ".join(miss["guard"]) or "無", " ".join(miss["fuse"]) or "無"), flush=True)
    if not pkgs:
        print("  都裝了", flush=True)
        return 0
    gate = tail(via, REG, "CGC_MDL056_InstallGate")
    if not apply or gate is None:
        print("  要裝:經 VCGC 安裝閘 → %s %s(加 --apply 才裝;連網要操作員端開同意閘)" % (gate.name if gate else "CGC_MDL056_InstallGate(找不到)", " ".join(pkgs)), flush=True)
        return 2
    p = subprocess.run([sys.executable, "-B", str(gate), *pkgs], env=dict(os.environ, VIA_FROM_VCGC="YES", PYTHONUTF8="1"))
    return p.returncode


def _run_tool(path: Path, args: list, timeout: int, env=None):
    e = dict(os.environ, PYTHONUTF8="1", VIA_FROM_VCGC="YES")
    if env:
        e.update(env)
    try:
        p = subprocess.run([sys.executable, "-B", str(path), *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, env=e, cwd=str(VIA_ROOT.parent))
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", ""


def fuse(args: list, via: Path = VIA_ROOT, capture: bool = False):
    f = tail(via, REG, "VIA_ModuFuse")
    if f is None:
        print("[fuse] 找不到 VIA_ModuFuse 尾版", flush=True)
        return (2, "", "") if capture else 2
    acc = lock_path(via, "accelerator")
    env = {"VIA_CELERITAS_PATH": str(acc)} if acc else {}
    if capture:
        return _run_tool(f, args, 1800, env)
    return subprocess.run([sys.executable, "-B", str(f), *args], env=dict(os.environ, PYTHONUTF8="1", **env)).returncode


def guard(args: list, via: Path = VIA_ROOT) -> int:
    g = tail(via, REG, "VIA_PanoramaGuard")
    if g is None:
        print("[guard] 找不到 VIA_PanoramaGuard 尾版", flush=True)
        return 2
    return subprocess.run([sys.executable, "-B", str(g), *args], env=dict(os.environ, PYTHONUTF8="1")).returncode


def run_all(since: str, via: Path = VIA_ROOT) -> int:
    """check → 全景守衛 scan(只掃改過的檔)→ 模組整合 doctor + selftest → 合併貼回包。"""
    res = check(via)
    lines, rcs = [], []
    g = tail(via, REG, "VIA_PanoramaGuard")
    print("[%s] toolbox run · 工具箱 %s · 全景守衛掃 %s 之後改過的檔 …" % (TAG, res["lamp"], since), flush=True)
    if g:
        rc, so, se = _run_tool(g, ["scan", "--root", str(via.parent), "--changed-since", since], 3600)
        for line in (se or "").splitlines():
            if line.startswith("[工具]"):
                print("  " + line, flush=True)
        try:
            card = json.loads(so[so.index("{"):]) if so and "{" in so else {}
        except ValueError:
            card = {}
        rcs.append(rc if isinstance(rc, int) else 2)
        lines.append("[guard] %s · %s · 引擎 %s · etag %s" % (card.get("decision_all", "?"), card.get("scope", "?"), card.get("after"), card.get("etag")))
        lines.append("[guard 工具] " + " · ".join("%s %s" % kv for kv in (card.get("tools") or {}).items()))
        for b in (card.get("blocked") or [])[:10]:
            lines.append("[guard 擋] %s · %s" % (b[0], b[1]))
        if card.get("pastepack") and Path(card["pastepack"]).is_file():
            pack = Path(card["pastepack"]).read_text(encoding="utf-8").splitlines()
            lines += ["[guard 紅] " + x[4:] for x in pack if x.startswith("[紅]")][:120]
            lines.append("[guard 貼回包] " + card["pastepack"])
        if card.get("next"):
            lines.append("[guard " + card["next"] + "]")
    rc, so, se = fuse(["doctor"], via, capture=True)
    try:
        d = json.loads(so)
        lines.append("[fuse doctor] 套件 %s/15 · 加速器 %s" % (d.get("available"), "有" if d.get("accelerator") else "沒有"))
    except ValueError:
        lines.append("[fuse doctor] 讀不懂輸出(rc=%s)" % rc)
    rc, so, se = fuse(["selftest"], via, capture=True)
    try:
        d = json.loads(so)
        lines.append("[fuse selftest] %s · %s 項" % (d.get("status"), d.get("count")))
        rcs.append(0 if d.get("status") == "PASS" else 1)
    except ValueError:
        lines.append("[fuse selftest] 失敗(rc=%s)· %s" % (rc, (se or "").strip().splitlines()[-1:] or ""))
        rcs.append(1)
    bad = [r["key"] for r in res["rows"] if r["lamp"] != "GREEN"]
    res["next"] = ("NEXT: 工具箱缺件先補:" + "、".join(bad)) if bad else ("NEXT: 先看全景守衛的紅" if any(x == 1 for x in rcs) else "NEXT: 全綠")
    out = write_report(via, res, lines)
    print((out / "TOOLBOX_latest.txt").read_text(encoding="utf-8"), flush=True)
    print("[報告] %s · %s" % (out / "TOOLBOX_latest.txt", out / "TOOLBOX_latest.html"), flush=True)
    worst = max([0 if res["lamp"] == "GREEN" else 2 if res["lamp"] == "YELLOW" else 1] + [x for x in rcs if isinstance(x, int)])
    return worst


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["toolbox"]:
        sub = argv[1] if len(argv) > 1 else "check"
        if sub == "check":
            res = check()
            out = write_report(VIA_ROOT, res)
            print((out / "TOOLBOX_latest.txt").read_text(encoding="utf-8"), flush=True)
            return 0 if res["lamp"] == "GREEN" else 2 if res["lamp"] == "YELLOW" else 1
        if sub == "help":
            print(help_text(argv[2] if len(argv) > 2 else ""), flush=True)
            return 0
        if sub == "install":
            return install("--apply" in argv)
        if sub == "run":
            since = argv[argv.index("--since") + 1] if "--since" in argv and argv.index("--since") + 1 < len(argv) else "origin/main~8"
            return run_all(since)
        print("toolbox [check | help [工具] | install [--apply] | run [--since 參照]]", flush=True)
        return 2
    if argv[:1] == ["guard"]:
        return guard(argv[1:])
    if argv[:1] == ["fuse"]:
        return fuse(argv[1:])
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 8 項 · 再前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    with tempfile.TemporaryDirectory(prefix="csm117_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        reg = via / REG
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        (via / "docs/handoff/ai").mkdir(parents=True)
        for stem in ("CGC_MDL158_VIAPanoramaAuditRepair", "VIA_PanoramaGuard", "VIA_ModuFuse", "CGC_MDL056_InstallGate", "CGC_MDL140_HandoverConsole",
                     "CGC_MDL237_NumberingSystem", "CGC_MDL245_SDDValidator", "CGC_SystemManager"):
            (reg / (stem + "_v0101.py")).write_text("x = 1\n", encoding="utf-8")
        (via / "docs/handoff/ai/VIA_VCGC_ApplyRun_v0101.py").write_text("x = 1\n", encoding="utf-8")
        (via / "supportive modules/VeritasCeleritas_v1141.py").write_text("x = 1\n", encoding="utf-8")
        names = [p for p in reg.glob("*_v0101.py")] + [via / "docs/handoff/ai/VIA_VCGC_ApplyRun_v0101.py"]
        (reg / "VIA_NumberBooks/VIA_NumberBook_MDL_VCGC_v0100.jsonl").write_text(
            "".join(json.dumps({"source": p.relative_to(via).as_posix()}) + "\n" for p in names), encoding="utf-8")
        (reg / "VIA_Component_Inventory_SSOT_v0100.json").write_text(json.dumps([p.name for p in names]), encoding="utf-8")
        (reg / "VIA_Handoff_Continuity_SSOT_v0100.json").write_text(json.dumps({"test_cases": {p.stem: {"argv": [p.name]} for p in names}}), encoding="utf-8")
        (reg / "VIA_VCGC_FunctionInventory_SSOT_v0100.json").write_text(json.dumps({"stations": [p.stem for p in names]}), encoding="utf-8")
        (reg / "VIA_EngineVersion_Register_v0100.json").write_text(json.dumps({"rows": [
            {"family": "token", "file": "CGC_MDL158_VIAPanoramaAuditRepair_v0101.py"},
            {"family": "panorama-guard", "file": "VIA_PanoramaGuard_v0101.py"},
            {"family": "modufuse", "file": "VIA_ModuFuse_v0101.py"}]}), encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({
            "token": {"path": "VeritasIntelligenceAnalytics/" + REG + "/CGC_MDL158_VIAPanoramaAuditRepair_v0101.py"},
            "accelerator": {"path": "VeritasIntelligenceAnalytics/supportive modules/VeritasCeleritas_v1141.py"}}), encoding="utf-8")
        r = check(via)
        chk("T1 十個工具全登好 → 每盞綠、總燈綠", r["lamp"] == "GREEN" and r["tools"] == len(TOOLBOX) and all(x["lamp"] == "GREEN" for x in r["rows"]),
            [(x["key"], x["missing"]) for x in r["rows"] if x["missing"]])
        (reg / "VIA_ModuFuse_v0102.py").write_text("x = 2\n", encoding="utf-8")
        r = check(via)
        fz = [x for x in r["rows"] if x["key"] == "fuse"][0]
        chk("T2 新尾版沒編號 / 沒登錄 / 沒案 / 沒進引擎版本冊 → 黃,並列出缺哪幾件", fz["lamp"] == "YELLOW" and fz["tail"] == "VIA_ModuFuse_v0102.py"
            and {"有編號", "有登錄", "引擎版本冊"} <= set(fz["missing"]), fz)
        (reg / "CGC_MDL158_VIAPanoramaAuditRepair_v0102.py").write_text("x = 2\n", encoding="utf-8")
        tk = [x for x in check(via)["rows"] if x["key"] == "token"][0]
        chk("T3 尾版換了但鎖冊沒跟上 → 黃(鎖冊指到尾版 ✘)", "鎖冊指到尾版" in tk["missing"], tk)
        (reg / "VIA_PanoramaGuard_v0101.py").unlink()
        gd = [x for x in check(via)["rows"] if x["key"] == "guard"][0]
        chk("T4 工具檔不見了 → 紅", gd["lamp"] == "RED" and gd["tail"] is None, gd)
        out = write_report(via, check(via), ["[guard] 測試行"])
        txt = (out / "TOOLBOX_latest.txt").read_text(encoding="utf-8").splitlines()
        chk("T5 報告:txt 以 NEXT: 結尾 · html 燈在第一欄 · json 可讀", txt[-1].startswith("NEXT:") and "<td><span class='lamp" in (out / "TOOLBOX_latest.html").read_text(encoding="utf-8")
            and json.loads((out / "TOOLBOX_latest.json").read_text(encoding="utf-8"))["tools"] == len(TOOLBOX))
        (via / "docs/handoff/VCGC_ToolManual_v0100.md").write_text("# 手冊\n\n## 全景守衛 `guard`\n用途:掃。\n\n## 模組整合 `fuse`\n用途:併。\n", encoding="utf-8")
        chk("T6 說明書:整本 / 單節 / 不認得的工具給可用清單", "用途:併" in help_text("fuse", via) and "用途:掃" not in help_text("fuse", via)
            and "可用" in help_text("zzz", via) and help_text("", via).startswith("# 手冊"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T7 檔面:第 3 行加速器標記 · 零 TA-Lib · 不設同意閘 · 不 import VDF / VRN",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and not re.search(r"^\s*(import|from)\s+(VDF|VRN)", src, re.M))
    prior_rc = PRIOR.selftest()
    chk("T8 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
