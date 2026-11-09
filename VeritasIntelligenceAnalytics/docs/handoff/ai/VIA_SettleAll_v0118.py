#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_SettleAll v0118 — 薄尾(v0117 一字不動):一支 PS 開機行 → 一支 Python 整合桌機全部收尾 + 五條新步。

操作員 2026-11-09:「integrate all into one ps code 遵守 ps/py 注入 ast 加速器覆蓋率 100% · 對外擷取資料的引擎 / VDF 注入網路工具 100% ·
VCGC 所有工具網路加速器遇到多個有差異:全景式檢是注入 AST 分類編號修正 標準化 合併 優化簡化 整合去重不遺漏最佳化處理」。

本版在 v0117 的 ⓪…⑰ 之上加(都只讀他系統 · 只寫自己的收據夾 VIA_Reports/settle 與各引擎自己的輸出):
  ⑲ 雙橋覆蓋:CGC_MDL124 BridgeSweeper 尾版 ── PY 加速器橋(四系 + 根層 `--accel --subsystems`)· PS 加速器橋(`--ps --root .`)·
     VDF 擷取引擎網路橋(`--net --root "functional modules/VDF"`);預設 dry-run 只算覆蓋率;`--apply-bridges` 才真注入(操作員桌機自己的改動權;
     注入後的檔在工作樹,本檔不 commit · 不 push,報告列出變了幾支與 git 指令)。燈:覆蓋三項全 100% 🟢 · 有缺(計畫)🟡 · 注入 SKIP(py_compile 不過)🔴。
  ㉑ 治理核心矩陣:docs/handoff/ai/VIA_GovCoreChain 尾版 `run`(dry-run · 不帶 --apply:它的 json / md / UI 是帶版號的已發布冊,就地重生 = 編號稽核 IMMUT 紅;重生要出新版號)→ 總燈 · 家族燈 + 已發布 json 的改動權燈。
     多版本差異的「分類 · 合併 · 去重不遺漏」就在這張矩陣;裁正本是操作員的事,本步不動檔。
  ㉒ 編號稽核:VCGC 主控台 `run CGC_MDL237_NumberingSystem audit` → 遺失 · 改身分 · 重號 都 0 才不紅(冊內不一致照它的黃)。
  ⑱ 五系統憲法矩陣(L125):docs/handoff/ai/VIA_FiveSystemConstitution 尾版 `run --apply` → 五系統各自自測 · 號 · 憲法性 · 進度帳(它自己只增)。
  ⑳ 外部工具:Graphify 隔離環境(%USERPROFILE%\\envs\\via_graphify)· Ponytail(Claude Code 外掛)· OmniRoute(npm 全域)· Node 版本 ── 只偵測不安裝;
     缺的 🟡 並印安裝指令(Graphify 第一次要操作員自己設 VIA_NET_CONSENT;本檔不代設)。
  ⑫ 系統矩陣多五列(⑱ ⑲ ⑳ ㉑ ㉒)· 報告照步驟排。

用法(桌機 PowerShell 7 · 或貼 VIA_SettleAll_v0118.md 裡的開機行 / cmd 版):
  python VIA_SettleAll_v0118.py [v0117 全部參數] [--apply-bridges]
  python VIA_SettleAll_v0118.py --selftest        (本版 + 前版鏈 · 零網路)
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更;本檔零網路,只掛路徑) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import contextlib
import datetime as _dt
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

NAME = "VIA_SettleAll"
VERSION = "v0118"
HERE = Path(__file__).resolve().parent
_MINE = int(re.search(r"_v(\d{4})\.py$", Path(__file__).name).group(1))


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", Path(p).name)
    return int(m.group(1)) if m else -1


_priors = [p for p in HERE.glob("VIA_SettleAll_v*.py") if 0 <= _vnum(p) < _MINE]
if not _priors:
    raise SystemExit("[RED] VIA_SettleAll %s:同夾找不到前版(v0117)· 薄尾不能單獨跑" % VERSION)
PRIOR_PATH = max(_priors, key=_vnum)
_spec = importlib.util.spec_from_file_location("via_settleall_prior", PRIOR_PATH)
BASE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BASE)
PRIOR = BASE
_PRIOR_VERSION = BASE.VERSION
BASE.VERSION = VERSION                           # 換裝在位:v0117 的所有輸出(報告 · 矩陣 · 帳)從此署名 v0118
BASE.GLYPHS = BASE.GLYPHS.replace("⑫⑩", "⑱⑲㉑㉒⑳⑫⑩") if "⑫⑩" in BASE.GLYPHS else BASE.GLYPHS + "⑱⑲㉑㉒⑳"   # 新步排在 ⑫ 矩陣前
STAGES = tuple(BASE.STAGES[:BASE.STAGES.index("vcgc") + 1]) + ("bridges", "govcore", "numaudit", "fivesys") + \
    tuple(s for s in BASE.STAGES[BASE.STAGES.index("vcgc") + 1:] if s not in ("matrix", "report")) + ("exttools", "matrix", "report")
say, tick, run, LOG = BASE.say, BASE.tick, BASE.run, BASE.LOG
_RX_COVER = re.compile(r"\[橋掃\] (PS-ACCEL|ACCEL|NET)\s+root=(.+?) · 掃 (\d+) · 已掛 (\d+) · 缺 (\d+)(?: · 版史 \d+)? · 排除 (\d+).*?(?:注入 (\d+) · SKIP (\d+)|計畫 (\d+)).*?覆蓋 ([\d.]+)%")
_RX_FIVE = re.compile(r"\[VIA_FiveSystemConstitution_v\d{4}\] 總燈 (\w+) · 實測綠 (\d+)/(\d+) · 憲法性 (\d+)/(\d+) · 空號 (\d+) · 衝突 OPEN (\d+)")
_RX_AUDIT = re.compile(r"\[編號只增稽核\] (\w+) · .*?遺失 (\d+) · 改身分 (\d+) · 重號 (\d+)(?: · 冊內不一致 (\d+))?")


def _tail_glob(folder: Path, pattern: str):
    fs = [p for p in folder.glob(pattern) if _vnum(p) >= 0]
    return max(fs, key=_vnum) if fs else None


def _env():
    e = dict(os.environ)
    e.setdefault("VIA_FROM_VCGC", "YES")
    e.setdefault("PYTHONIOENCODING", "utf-8")
    e.setdefault("PYTHONUTF8", "1")
    return e


# ───────────── ⑲ 雙橋覆蓋 ─────────────
def parse_cover(out: str) -> list:
    rows = []
    for m in _RX_COVER.finditer(out):
        kind, root, scanned, has, miss, ex, inj, skip, plan, cov = m.groups()
        rows.append({"kind": kind, "root": root, "scanned": int(scanned), "has": int(has), "missing": int(miss), "excluded": int(ex),
                     "injected": int(inj or 0), "skipped": int(skip or 0), "planned": int(plan or 0), "coverage": float(cov)})
    return rows


def bridges_lamp(rows: list, applied: bool) -> str:
    if not rows:
        return "RED"
    if any(r["skipped"] for r in rows):
        return "RED"
    if all(r["coverage"] >= 100.0 for r in rows):
        return "GREEN"
    return "YELLOW"


def stage_bridges(via: Path, ctx: dict, apply: bool = False) -> None:
    tick("⑲")
    sw = _tail_glob(via / "supportive modules" / "registry", "CGC_MDL124_BridgeSweeper_v*.py")
    if sw is None:
        ctx["bridges"] = {"lamp": "RED", "text": "找不到 CGC_MDL124_BridgeSweeper 尾版"}
        say("RED", "⑲ 雙橋覆蓋", ctx["bridges"]["text"])
        return
    flag = ["--apply"] if apply else []
    t0 = time.time()
    outs = []
    for args in (["--accel", "--subsystems"], ["--ps", "--root", "."], ["--net", "--root", "functional modules/VDF"]):
        rc, out = run([sys.executable, str(sw)] + args + flag, cwd=via, timeout=1800, env=_env())
        outs.append((args, rc, out))
    rows = []
    for args, rc, out in outs:
        rows += parse_cover(out)
    tot = re.search(r"\[橋掃\] 四系總表 ([^\n]{0,400})", outs[0][2])
    lamp = bridges_lamp(rows, apply)
    by_kind = {}
    for r in rows:
        k = r["kind"]
        b = by_kind.setdefault(k, {"has": 0, "missing": 0, "injected": 0, "skipped": 0, "planned": 0})
        for f in b:
            b[f] += r[f]
    def pct(b):
        d = b["has"] + b["missing"]
        return round(100.0 * (b["has"] + b["injected"]) / d, 1) if d else 100.0
    text = " · ".join("%s %d/%d (%s%%)%s" % (k, b["has"] + b["injected"], b["has"] + b["missing"], pct(b), (" 注入 %d" % b["injected"]) if apply else ((" 缺 %d" % b["missing"]) if b["missing"] else "")) for k, b in by_kind.items()) or "沒解析到橋掃輸出"
    text += " · %s" % ("真注入(工作樹已改 · 要自己 commit)" if apply else "dry-run 只算")
    skipped = [r for r in rows if r["skipped"]]
    ctx["bridges"] = {"lamp": lamp, "text": text, "rows": rows, "by_kind": by_kind, "subsystems_line": tot.group(1) if tot else None, "apply": apply,
                      "secs": int(time.time() - t0), "sweeper": sw.name, "rc": [rc for _, rc, _ in outs], "out_tail": [o[-1200:] for _, _, o in outs]}
    nxt = ("注入 SKIP = 注入前後 py_compile 不過的檔 → 先修語法再注" if skipped else
           ("缺的照舊:加 --apply-bridges 真注入(或 VCGC run CGC_MDL124_BridgeSweeper --accel --subsystems --apply)→ 自測 → commit" if lamp == "YELLOW" else
            ("git -C <倉> status · 自測變了的尾版 · commit / push 走 PR" if apply and any(r["injected"] for r in rows) else "")))
    say(lamp, "⑲ 雙橋覆蓋", text, nxt)


# ───────────── ㉑ 治理核心矩陣 ─────────────
def parse_govcore(out: str):
    m = re.search(r"\[(VIA_GovCoreChain_v\d{4})\] 總燈 (\w+) · 家族 (\d+) · 載入者列 (\d+)", out)
    if not m:
        return None
    fams = re.findall(r"^\s+\[(\w+)\] (\S+) · ", out, re.M)
    return {"engine_said": m.group(1), "lamp": m.group(2), "families_n": int(m.group(3)), "loader_rows": int(m.group(4)), "families": {f: l for l, f in fams}}


def stage_govcore(via: Path, ctx: dict) -> None:
    """㉑ 唯讀 dry-run(不帶 --apply):GovCoreChain 的 json / md / UI 是帶版號的已發布冊,就地重生會被編號稽核判 IMMUT(本版實測抓到);
    重生要出新版號尾版。這一步只重算、印燈、對照已發布 json 的改動權。"""
    tick("㉑")
    eng = _tail_glob(via / "docs" / "handoff" / "ai", "VIA_GovCoreChain_v*.py")
    if eng is None:
        ctx["govcore"] = {"lamp": "GRAY", "text": "工作樹沒 VIA_GovCoreChain(同步後才有)"}
        say("GRAY", "㉑ 治理核心矩陣", ctx["govcore"]["text"])
        return
    t0 = time.time()
    rc, out = run([sys.executable, str(eng), "run"], cwd=via, timeout=1500, env=_env())      # 不帶 --apply:只算不寫
    g = parse_govcore(out)
    js = via / "docs" / "handoff" / "ai" / ("%s.json" % eng.stem)
    D = {}
    with contextlib.suppress(Exception):
        D = json.loads(js.read_text(encoding="utf-8"))
    rights = (D.get("mutation_rights") or {}).get("lamp", "GRAY")
    if not g:
        ctx["govcore"] = {"lamp": "RED", "text": "沒讀到總燈行(rc %s)" % rc, "rc": rc, "out_tail": out[-800:]}
        say("RED", "㉑ 治理核心矩陣", ctx["govcore"]["text"])
        return
    cnt = {}
    for l in g["families"].values():
        cnt[l] = cnt.get(l, 0) + 1
    text = "%s dry-run · 六家族 🟢%d 🟡%d 🔴%d · 載入者列 %d · 已發布矩陣 %s 改動權 %s(樹上寫治理檔的程式 %s)· 不重生版號冊" % (
        eng.name, cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0), g["loader_rows"], js.name if D else "(讀不到)", rights, (D.get("mutation_rights") or {}).get("tree_writers", "?"))
    ctx["govcore"] = dict(g, text=text, engine=eng.name, rc=rc, rights=rights, published_json=js.name if D else None, secs=int(time.time() - t0))
    say(g["lamp"], "㉑ 治理核心矩陣", text, "紅家族 = 多份內容不同的副本(分岔)→ 操作員裁正本 → 版本化轉接件;矩陣要重生就出 GovCoreChain 新版號(輸出改 _latest 名),不就地改 v0101 冊")


# ───────────── ㉒ 編號稽核 ─────────────
def parse_audit(out: str):
    m = _RX_AUDIT.search(out)
    if not m:
        return None
    lamp, lost, ident, dup, incons = m.groups()
    return {"lamp": lamp, "lost": int(lost), "identity_changed": int(ident), "dup": int(dup), "inconsistent": int(incons or 0)}


def stage_numaudit(via: Path, ctx: dict) -> None:
    tick("㉒")
    con = BASE._tail(via, "CGC_MDL149_Console")
    if con is None:
        ctx["numaudit"] = {"lamp": "RED", "text": "找不到 VCGC 主控台"}
        say("RED", "㉒ 編號稽核", ctx["numaudit"]["text"])
        return
    t0 = time.time()
    rc, out = run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], cwd=via, timeout=900, env=_env())
    a = parse_audit(out)
    if not a:
        ctx["numaudit"] = {"lamp": "RED", "text": "沒讀到 [編號只增稽核] 行(rc %s)" % rc, "rc": rc, "out_tail": out[-800:]}
        say("RED", "㉒ 編號稽核", ctx["numaudit"]["text"])
        return
    lamp = "RED" if (a["lost"] or a["identity_changed"] or a["dup"]) else ("YELLOW" if a["inconsistent"] else "GREEN")
    text = "遺失 %d · 改身分 %d · 重號 %d · 冊內不一致 %d(稽核自報 %s)" % (a["lost"], a["identity_changed"], a["dup"], a["inconsistent"], a["lamp"])
    ctx["numaudit"] = dict(a, text=text, rc=rc, secs=int(time.time() - t0), lamp_final=lamp)
    ctx["numaudit"]["lamp"] = lamp
    say(lamp, "㉒ 編號稽核", text, "發號只經 VCGC run CGC_MDL237_NumberingSystem --apply --scope <已提交的檔>(L125 ③:衝突解了才發)" if lamp != "RED" else "遺失 / 改身分 / 重號 > 0 = 號冊被動過 → 先找是哪一輪、還原號冊")


# ───────────── ⑱ 五系統憲法矩陣 ─────────────
def parse_fivesys(out: str):
    m = _RX_FIVE.search(out)
    if not m:
        return None
    lamp, g, n, c, n2, blank, conf = m.groups()
    rows = re.findall(r"^\s+\[(\w+)\s*\] (\S+)\s+號 (\S+)\s+憲法性 (\S+)\s+實測 (\w+)\s+rc (\S+)", out, re.M)
    return {"lamp": lamp, "run_green": int(g), "systems": int(n), "constitutional": int(c), "blank": int(blank), "conflicts_open": int(conf),
            "rows": [{"lamp": a, "sys": b, "number": c2, "constitution": d, "run": e, "rc": f} for a, b, c2, d, e, f in rows]}


def stage_fivesys(via: Path, ctx: dict) -> None:
    tick("⑱")
    eng = _tail_glob(via / "docs" / "handoff" / "ai", "VIA_FiveSystemConstitution_v*.py")
    if eng is None:
        ctx["fivesys"] = {"lamp": "GRAY", "text": "工作樹沒 VIA_FiveSystemConstitution(同步後才有;PR #619)"}
        say("GRAY", "⑱ 五系統憲法矩陣", ctx["fivesys"]["text"])
        return
    t0 = time.time()
    rc, out = run([sys.executable, str(eng), "run", "--apply"], cwd=via, timeout=1800, env=_env())
    f = parse_fivesys(out)
    if not f:
        ctx["fivesys"] = {"lamp": "RED", "text": "沒讀到總燈行(rc %s)" % rc, "rc": rc, "out_tail": out[-800:]}
        say("RED", "⑱ 五系統憲法矩陣", ctx["fivesys"]["text"])
        return
    text = "實測綠 %d/%d · 憲法性 %d/%d · 空號 %d · 衝突冊 OPEN %d · %s" % (f["run_green"], f["systems"], f["constitutional"], f["systems"], f["blank"], f["conflicts_open"],
                                                                   " ".join("%s%s" % (BASE.LAMP_ICON.get(r["lamp"], "⚪"), r["sys"]) for r in f["rows"]))
    ctx["fivesys"] = dict(f, text=text, engine=eng.name, rc=rc, secs=int(time.time() - t0), ui=str(via / "docs" / "handoff" / "ai" / "VIA_FiveSystemConstitution_UI.html"))
    say(f["lamp"], "⑱ 五系統憲法矩陣", text, "憲法性紅 = 衝突冊 OPEN 點到該系統 / 空號;L125 ③:操作員 + AI 裁衝突 → VCGC 偵測無誤才發號;實測紅 = 該系統自己的 --selftest 不過")


# ───────────── ⑳ 外部工具 ─────────────
def detect_exttools(home: Path, which=shutil.which) -> dict:
    gx = home / "envs" / "via_graphify" / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")
    pony = False
    for cand in (home / ".claude" / "plugins", home / ".claude" / "marketplaces"):
        if cand.exists():
            pony = pony or any("ponytail" in p.name.lower() for p in cand.rglob("*ponytail*"))
    with contextlib.suppress(Exception):
        s = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
        pony = pony or "ponytail" in json.dumps(s).lower()
    omni = which("omniroute") or which("omniroute.cmd")
    node = which("node")
    return {"graphify": {"present": gx.exists(), "path": str(gx), "install": "貼 docs/handoff/ai/via_graphify_v0101/VIA_Graphify_v0101.md 的開機行(第一次先 $env:VIA_NET_CONSENT='YES',操作員自己設)"},
            "ponytail": {"present": bool(pony), "install": "Claude Code 裡:/plugin marketplace add DietrichGebert/ponytail → /plugin install ponytail@ponytail"},
            "omniroute": {"present": bool(omni), "path": omni, "install": "npm install -g omniroute → omniroute(需 Node 22 / 24 LTS · 只綁 127.0.0.1:20128)"},
            "node": {"present": bool(node), "path": node}}


def stage_exttools(via: Path, ctx: dict) -> None:
    tick("⑳")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    d = detect_exttools(home)
    present = [k for k in ("graphify", "ponytail", "omniroute") if d[k]["present"]]
    absent = [k for k in ("graphify", "ponytail", "omniroute") if not d[k]["present"]]
    lamp = "GREEN" if not absent else "YELLOW"
    text = "在:%s · 缺:%s · node %s" % (", ".join(present) or "—", ", ".join(absent) or "—", "在" if d["node"]["present"] else "不在")
    ctx["exttools"] = dict(d, lamp=lamp, text=text, present=present, absent=absent)
    say(lamp, "⑳ 外部工具", text, " / ".join("%s:%s" % (k, d[k]["install"]) for k in absent) if absent else "")


# ───────────── ⑫ 矩陣多五列 ─────────────
_MATRIX_ROWS_0117 = BASE.matrix_rows


def matrix_rows(via: Path, ctx: dict) -> list:
    rows = _MATRIX_ROWS_0117(via, ctx)
    for key, name, parent, ver in (("fivesys", "五系統憲法矩陣 ⑱", None, lambda c: c.get("engine") or "—"),
                                   ("bridges", "雙橋覆蓋 ⑲", "VCGC", lambda c: c.get("sweeper") or "—"),
                                   ("govcore", "治理核心矩陣 ㉑", "VCGC", lambda c: c.get("engine") or "—"),
                                   ("numaudit", "編號稽核 ㉒", "VCGC", lambda c: "CGC_MDL237 audit"),
                                   ("exttools", "外部工具 ⑳", None, lambda c: "Graphify · Ponytail · OmniRoute")):
        c = ctx.get(key) or {}
        if c.get("lamp"):
            rows.append({"system": name, "parent": parent, "lamp": c["lamp"], "version": ver(c), "status": c.get("text", ""), "secs": c.get("secs"), "vcgc_no": "—"})
    return rows


BASE.matrix_rows = matrix_rows                   # 換裝在位:v0117 的 stage_matrix 從此拿到多五列的表


# ───────────── main ─────────────
def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="%s_%s" % (NAME, VERSION), description="v0117 全部 + ⑲ 雙橋覆蓋 · ㉑ 治理核心矩陣 · ㉒ 編號稽核 · ⑱ 五系統憲法矩陣 · ⑳ 外部工具")
    ap.add_argument("--root")
    ap.add_argument("--only", default=",".join(STAGES))
    ap.add_argument("--no-sync", action="store_true")
    ap.add_argument("--vrn", choices=("status", "repair", "check", "skip"), default="status")
    ap.add_argument("--graphify-floor-gb", type=float, default=0.75)
    ap.add_argument("--serial", action="store_true")
    ap.add_argument("--graphify", choices=("changed", "all", "skip"), default="changed")
    ap.add_argument("--force-old-tree", action="store_true")
    ap.add_argument("--vdf-budget", type=int, default=1200)
    ap.add_argument("--apply-bridges", action="store_true", help="⑲ 真注入(預設 dry-run 只算覆蓋率)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    via = BASE.find_root(a.root)
    if via is None:
        say("RED", "⓪ VIA 根", "找不到(查過 --root · VIA_ROOT · 本檔所在 · OneDrive\\Documents\\movies-dataset)", "加 --root <倉根>")
        return 1
    tick("⓪")
    say("GREEN", "⓪ VIA 根", "%s · %s %s(前版 %s)" % (via, NAME, VERSION, _PRIOR_VERSION))
    only = [s.strip() for s in a.only.split(",") if s.strip()]
    ctx = {"tool": NAME + " " + VERSION, "root": str(via), "branch": BASE.BRANCH, "run_id": _dt.datetime.now().strftime("%Y%m%d_%H%M%S"), "prior": _PRIOR_VERSION}
    if "scan" in only:
        BASE.stage_scan(via, ctx)
    if "sync" in only:
        BASE.stage_sync(via, ctx, not a.no_sync)
    light = [("④ VDF ui", lambda: BASE.stage_vdf(via, ctx, a.force_old_tree)), ("⑤ VRN", lambda: BASE.stage_vrn(via, ctx, a.vrn)),
             ("⑧ VQG", lambda: BASE.stage_vqg(via, ctx)), ("⑨ Agent OS", lambda: BASE.stage_agentos(via, ctx)), ("⑮ VAP", lambda: BASE.stage_vap(via, ctx))]
    light = [(n, f) for (n, f), key in zip(light, BASE.PARALLEL) if key in only]
    if light and not a.serial:
        print("[計] ④⑤⑧⑨⑮ 併行(%s)· 各寫各的收據夾 · 輸出行會交錯 · 報告照步驟排" % " · ".join(n for n, _ in light), flush=True)
        BASE.run_parallel(light)
    else:
        for _, f in light:
            f()
    if "link" in only:
        BASE.stage_link(via, ctx)
    if "vcgc" in only:
        BASE.stage_vcgc(via, ctx, a.force_old_tree)
    if "bridges" in only:
        stage_bridges(via, ctx, apply=a.apply_bridges)
    if "govcore" in only:
        stage_govcore(via, ctx)
    if "numaudit" in only:
        stage_numaudit(via, ctx)
    if "fivesys" in only:
        stage_fivesys(via, ctx)
    if "graphify" in only:
        BASE.stage_graphify(via, ctx, a.graphify_floor_gb, mode=a.graphify)
    if "policy" in only:
        BASE.stage_policy(via, ctx)
    if "vdfeng" in only:
        BASE.stage_vdfeng(via, ctx, budget_s=a.vdf_budget, force_old=a.force_old_tree)
    if "modmatrix" in only:
        BASE.stage_modmatrix(via, ctx)
    if "conflicts" in only:
        BASE.stage_conflicts(via, ctx)
    if "exttools" in only:
        stage_exttools(via, ctx)
    if "matrix" in only:
        BASE.stage_matrix(via, ctx)
    if "report" in only:
        BASE.stage_report(via, ctx)
    return 1 if any(x["lamp"] == "RED" for x in LOG) else 2 if any(x["lamp"] == "YELLOW" for x in LOG) else 0


# ───────────── 自測(本版 + 前版鏈 · 零網路 · 只在 tempfile 寫) ─────────────
def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, why=""):
        (ok if cond else bad).append(name)
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, "" if cond else " · " + str(why)[:200]), flush=True)
    chk("① 前版鏈:PRIOR = %s · 換裝在位 BASE.VERSION = %s · GLYPHS 含 ⑱⑲⑳㉑㉒ 且在 ⑫ 之前" % (PRIOR_PATH.name, BASE.VERSION),
        _PRIOR_VERSION == "v0117" and BASE.VERSION == VERSION and all(g in BASE.GLYPHS for g in "⑱⑲⑳㉑㉒") and BASE.GLYPHS.index("⑲") < BASE.GLYPHS.index("⑫") and BASE.GLYPHS.endswith("⑩"), BASE.GLYPHS)
    chk("② STAGES:v0117 全部 + bridges / govcore / numaudit / fivesys / exttools · matrix · report 殿後",
        set(BASE.STAGES) <= set(STAGES) and STAGES[-2:] == ("matrix", "report") and STAGES.index("bridges") == STAGES.index("vcgc") + 1 and "exttools" in STAGES, str(STAGES))
    sample = ("[橋掃] ACCEL root=functional modules/VDF · 掃 120 · 已掛 118 · 缺 2 · 排除 3 · 計畫 2(dry-run) · 覆蓋 98.3%\n"
              "[橋掃] NET   root=functional modules/VDF · 掃 40 · 已掛 40 · 缺 0 · 排除 1 · 計畫 0(dry-run) · 覆蓋 100.0%\n"
              "[橋掃] PS-ACCEL root=. · 掃 30 · 已掛 30 · 缺 0 · 版史 2 · 排除 4 · 計畫 0(dry-run) · 覆蓋 100.0%\n"
              "[橋掃] ACCEL root=. · 掃 10 · 已掛 8 · 缺 2 · 排除 0 · 注入 1 · SKIP 1 · 覆蓋 90.0%\n")
    rows = parse_cover(sample)
    chk("③ 橋掃解析:4 列 · dry 計畫 / apply 注入 SKIP · PS 版史欄也吃 · 覆蓋數字對", len(rows) == 4 and rows[0]["planned"] == 2 and rows[2]["kind"] == "PS-ACCEL" and rows[3]["injected"] == 1 and rows[3]["skipped"] == 1 and rows[1]["coverage"] == 100.0, json.dumps(rows, ensure_ascii=False)[:300])
    chk("④ 雙橋燈:有 SKIP → RED · 全 100 → GREEN · 有缺 → YELLOW · 空 → RED",
        bridges_lamp(rows, False) == "RED" and bridges_lamp(rows[1:3], False) == "GREEN" and bridges_lamp(rows[:3], False) == "YELLOW" and bridges_lamp([], False) == "RED")
    f = parse_fivesys("[VIA_FiveSystemConstitution_v0100] 總燈 RED · 實測綠 5/5 · 憲法性 0/5 · 空號 0 · 衝突 OPEN 6 · 進度帳 +5\n"
                      "  [RED   ] VCGC  號 VIA-VCGC-MDL1625       憲法性 CONFLICT_OPEN              實測 GREEN rc 0     37.1s · 衝突 1 · 進度 2/2 連 2\n"
                      "  [GRAY  ] VRN-1 號 空號                     憲法性 EXTERNAL_READONLY          實測 GRAY  rc None     0s · 衝突 0 · 進度 0/0 連 0\n")
    chk("⑤ 憲法矩陣解析:總燈 RED · 5/5 · 0/5 · 兩列系統", f and f["lamp"] == "RED" and f["run_green"] == 5 and f["constitutional"] == 0 and len(f["rows"]) == 2 and f["rows"][1]["sys"] == "VRN-1", str(f)[:200])
    gc = parse_govcore("[VIA_GovCoreChain_v0100] 總燈 RED · 家族 6 · 載入者列 1827\n  [YELLOW] VIA_EnvManager · 3 份\n  [RED] VeritasAegisNexus · 8 份\n")
    chk("⑤b 治理核心解析:總燈 RED · 家族 6 · 1827 列 · 兩家族燈", gc and gc["lamp"] == "RED" and gc["families_n"] == 6 and gc["families"].get("VeritasAegisNexus") == "RED", str(gc))
    au = parse_audit("[編號只增稽核] YELLOW · 基準 f7f681e6663f · 列 121828 → 122350(+522) · 遺失 0 · 改身分 0 · 重號 0 · 冊內不一致 1\n")
    chk("⑥ 稽核解析:YELLOW · 0 / 0 / 0 · 不一致 1", au and au["lamp"] == "YELLOW" and au["lost"] == 0 and au["dup"] == 0 and au["inconsistent"] == 1, str(au))
    with tempfile.TemporaryDirectory() as td:
        h = Path(td)
        d0 = detect_exttools(h, which=lambda n: None)
        (h / "envs" / "via_graphify" / ("Scripts" if os.name == "nt" else "bin")).mkdir(parents=True)
        (h / "envs" / "via_graphify" / ("Scripts/graphify.exe" if os.name == "nt" else "bin/graphify")).write_text("", encoding="utf-8")
        (h / ".claude" / "plugins" / "marketplaces" / "ponytail").mkdir(parents=True)
        d1 = detect_exttools(h, which=lambda n: "/usr/bin/" + n if n in ("omniroute", "node") else None)
        chk("⑦ 外部工具偵測:空家三缺 · 假家 graphify / ponytail / omniroute / node 全在 · 只偵測不安裝",
            not any(d0[k]["present"] for k in ("graphify", "ponytail", "omniroute")) and all(d1[k]["present"] for k in ("graphify", "ponytail", "omniroute", "node")), json.dumps(d1, ensure_ascii=False)[:200])
    fake_ctx = {"fivesys": {"lamp": "RED", "text": "x", "engine": "E.py", "secs": 1}, "bridges": {"lamp": "GREEN", "text": "y", "sweeper": "S.py"}, "exttools": {"lamp": "YELLOW", "text": "z"}}
    global _MATRIX_ROWS_0117
    _saved = _MATRIX_ROWS_0117
    _MATRIX_ROWS_0117 = lambda via, ctx: []        # 假根上只驗本版追加段(v0117 的列在實樹才有)
    try:
        extra = [r for r in matrix_rows(Path(tempfile.gettempdir()), dict(fake_ctx, families={})) if r["system"][-1] in "⑱⑲⑳㉑㉒"]
    finally:
        _MATRIX_ROWS_0117 = _saved
    chk("⑧ ⑫ 矩陣追加:ctx 有的三步各一列 · 欄位齊(system / parent / lamp / version / status)", len(extra) == 3 and all({"system", "parent", "lamp", "version", "status"} <= set(r) for r in extra) and BASE.matrix_rows is matrix_rows, str(extra)[:200])
    body = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑨ 紀律:兩橋在且在 from __future__ 後 · 不 pip · 不設 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT · 不 push · 不改 v0117",
        "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:NET-BRIDGE:v0100]" in body and body.index("from __future__") < body.index("[VIA:ACCEL-BRIDGE:v0100]")
        and "pip install" not in body and "VIA_NET_" + "CONSENT'] =" not in body and "VIA_SCRAPE_" + "CONSENT" not in body and "git push" not in body and "\"push\"" not in body)
    print("[%s %s] 本版 %d/%d · FAIL %d · %s" % (NAME, VERSION, len(ok), len(ok) + len(bad), len(bad), "PASS" if not bad else "FAIL: " + " / ".join(bad)), flush=True)
    print("[%s %s] 前版鏈 %s 自測 →" % (NAME, VERSION, _PRIOR_VERSION), flush=True)
    rc_prior = BASE.selftest()
    print("[%s %s] 合計 %s" % (NAME, VERSION, "PASS" if (not bad and rc_prior == 0) else "FAIL(本版 %d · 前版 rc %s)" % (len(bad), rc_prior)), flush=True)
    return 0 if (not bad and rc_prior == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
