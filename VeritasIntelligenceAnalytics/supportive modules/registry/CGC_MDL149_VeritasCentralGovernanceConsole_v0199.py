#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0199 — 薄尾(v0198 一字不動):overview(VCGC 完整功能一覽:卡片看整體、矩陣看細節)

操作員 2026-11-19:「VCGC 完整功能一覽 HTML U/I」「可先用卡片做整體大致上狀態顯示,再用矩陣細節展現」。
缺口:VCGC 的功能散在好幾本冊與收據(動詞 · 席位 · 功能卡 · 引擎 · 測試案 · 工作流 · 鎖版工具 · 頁面 · 治理冊 · 需求),沒有一頁能一次看完。
冊與收據都在、卡片矩陣的正主也在(CGC_MDL283_CardMatrixFeedback),不另做掃描器、不另做版面(L130):本版只在主控台加一個動詞,其餘原樣轉交前版 v0198。
  overview [--no-open] [--json]
      ① 讀既有的冊與收據整理成項目冊(只讀;不執行任何引擎、不跑任何測試):
           動詞 / 席位 / 功能卡 / 工作流步驟 / PS 入口 ← 串測收據 TEST_latest.json 的 coverage(沒有就讀功能盤點冊),燈 ← 串測狀態冊各站最近一次結果
           引擎與模組 ← registry 夾各家族尾版(ast.parse);燈 = 標準化:語法過 + 加速器橋在 + 元件註冊冊上有號
           交接測試案 ← docs/handoff/evidence/<案>.json(過 = rc 0 且成功字樣對上;收據寫的是主機還是容器照實帶出)
           鎖版工具 ← VIA_ToolVersion_Lock(檔在且雜湊相同)· 頁面 ← 同步台收據 SYNC_latest.json · 治理冊 ← 各冊尾版 · 需求 ← 需求冊裡 VCGC 的列
         沒有收據的一律灰,不補綠。
      ② 交給 CGC_MDL283_CardMatrixFeedback 尾版(v0105 起項目冊可自帶群組與標題)出頁:卡片(依類別 · 依區)+ 可篩選的矩陣;樣式只來自鎖定模板冊。
      ③ 輸出(都在 VIA_Reports/vcgc,不入倉):VCGC_Overview_latest.html · OVERVIEW_latest.json(收據)· overview/(項目冊與引擎的回饋包)。
      rc:0 = 頁做出來 · 1 = 沒做出來。內容的紅黃另記在收據的 content_lamp,不混進 rc。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib · 不寫他系統的夾。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====
import ast
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import warnings
from pathlib import Path

VERSION = "v0199"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
REP = "VIA_Reports/vcgc/"
CMF_STEM, CMF_MIN = "CGC_MDL283_CardMatrixFeedback", 105      # 卡片 + 矩陣的正主;v0105 起項目冊可自帶群組與標題
OV_DIR, OV_BOOK, OV_PAGE, OV_RECEIPT = REP + "overview", "VCGC_OVERVIEW_items.json", "VCGC_Overview_latest.html", "OVERVIEW_latest.json"
OV_TITLE = "VCGC 功能一覽"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _tail(d: Path, stem: str):
    hits = [p for p in d.glob(stem + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def child_env() -> dict:
    """子行程環境:不提交不推送 · 不自己開頁(由本動詞最後開一次)· 輸出一律 UTF-8。"""
    return dict(_env(), VIA_VCGC_PUSH="NO", VIA_NO_OPEN="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")


def _call(path, args: list) -> int:
    if path is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(path), *args], env=_env()).returncode


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0198(子行程 · rc 不變)。"""
    return _call(_prior_path(), args)


_PRIOR = None


def _prior_module():
    global _PRIOR
    if _PRIOR is None:
        pp = _prior_path()
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(要用才載)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior_module(), name)


# ===== [VIA:VCGC-OVERVIEW-CORE:v0100] VCGC 功能一覽:把既有的冊與收據整理成項目冊(只讀;不另寫掃描器、不執行任何引擎) =====
OV_SECTIONS = ["① 入口與動詞", "② 席位", "③ AI 功能卡", "④ 引擎與模組(標準化)", "⑤ 交接測試案", "⑥ 工作流步驟", "⑦ 鎖版工具", "⑧ 頁面", "⑨ 治理冊", "⑩ 需求", "⑪ PS 入口"]
OV_LAMP = {"GREEN": "g", "YELLOW": "y", "RED": "r", "g": "g", "y": "y", "r": "r"}


def ov_json(path):
    if path is None:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def ov_tail(folder, pattern):
    hits = sorted(Path(folder).glob(pattern))
    return hits[-1] if hits else None


def ov_host(env):
    """收據上的環境 → 主機 / 容器 / 不明(只認收據自己寫的平台,不猜)。"""
    s = json.dumps(env, ensure_ascii=False).lower() if env else ""
    if "windows" in s or "win32" in s:
        return "主機"
    if "linux" in s:
        return "容器"
    return "不明"


def ov_station_row(state, sid):
    """狀態冊裡這一站的最近一次結果 → (燈, 時間, 說明)。沒有收據 = 灰。"""
    r = (state or {}).get(sid) if sid else None
    if not isinstance(r, dict):
        return "x", "", "這一站還沒有測試收據(跑 test 整輪才有)"
    return OV_LAMP.get(str(r.get("lamp")), "x"), str(r.get("at") or ""), "站 %s · rc %s · %s" % (sid, r.get("rc"), str(r.get("last") or "")[:110])


def ov_families(reg):
    """registry 夾裡每個家族的尾版:語法 · 加速器橋 · 版本數(只 ast.parse,不執行)。"""
    fam = {}
    for p in Path(reg).glob("*_v[0-9][0-9][0-9][0-9].py"):
        m = re.match(r"^(.+?)_v(\d{4})\.py$", p.name)
        if not m:
            continue
        d = fam.setdefault(m.group(1), {"n": 0, "ver": -1, "path": None})
        d["n"] += 1
        if int(m.group(2)) > d["ver"]:
            d["ver"], d["path"] = int(m.group(2)), p
    out = []
    for name in sorted(fam):
        d = fam[name]
        try:
            text = d["path"].read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        ok, doc = True, ""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tree = ast.parse(text)
            doc = (ast.get_docstring(tree) or "").strip().splitlines()[0] if ast.get_docstring(tree) else ""
        except SyntaxError:
            ok = False
        out.append({"family": name, "ver": "v%04d" % d["ver"], "versions": d["n"], "file": d["path"].name, "syntax": ok, "bridge": "[VIA:ACCEL-BRIDGE" in text,
                    "doc": re.sub(r"^%s\s*v\d{4}\s*[—\-·:]*\s*" % re.escape(name), "", doc)[:150]})
    return out


def ov_collect(via):
    """回 {"source", "items", "notes"}。items 欄位照 CGC_MDL283 的項目冊:section · system · lamp · id · title · detail · ver · at · needs。"""
    via = Path(via).resolve()
    reg, rep = via / "supportive modules" / "registry", via / "VIA_Reports" / "vcgc"
    items, notes = [], []

    def add(section, lamp, iid, title, detail="", ver="", at="", needs=False):
        items.append({"section": section, "system": "VCGC", "lamp": lamp, "id": str(iid), "title": str(title)[:120], "detail": str(detail)[:260], "ver": str(ver), "at": str(at), "needs": bool(needs)})

    test, state = ov_json(rep / "TEST_latest.json") or {}, ov_json(rep / "TEST_STATE_v0101.json") or {}
    if not test:
        notes.append("沒有串測收據 TEST_latest.json(先跑 test);動詞 / 席位 / 功能卡 / 工作流 / 測試案的清單改讀盤點冊")
    inv_p = ov_tail(reg, "VIA_VCGC_FunctionInventory_SSOT_v*.json")
    inv = ov_json(inv_p) or {}
    stations = {s.get("id"): s for s in inv.get("stations") or [] if isinstance(s, dict)}
    console = ov_tail(reg, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    cver = console.stem.rsplit("_", 1)[-1] if console else ""
    cov = test.get("coverage") or []
    if not cov:      # 沒有串測收據時,從盤點冊的 coverage 攤開(只有名稱與對應站)
        for kind, d in (inv.get("coverage") or {}).items():
            if isinstance(d, dict):
                for k, v in d.items():
                    cov.append({"kind": kind, "id": k, "state": "EXEMPT" if isinstance(v, dict) and v.get("exempt") else "COVERED", "by": (v or {}).get("station", "") if isinstance(v, dict) else "", "why": (v or {}).get("exempt", "") if isinstance(v, dict) else "", "where": ""})
    # ⑤ 的燈來自交接證據夾的最新收據
    ev_root = via / "docs" / "handoff" / "evidence"
    sec_of = {"verb": OV_SECTIONS[0], "seat": OV_SECTIONS[1], "card": OV_SECTIONS[2], "case": OV_SECTIONS[4], "workflow": OV_SECTIONS[5], "ps": OV_SECTIONS[10]}
    for r in cov:
        kind, rid = r.get("kind"), str(r.get("id"))
        sec = sec_of.get(kind)
        if not sec:
            continue
        name = (stations.get(r.get("by")) or {}).get("name") or ""
        if r.get("state") == "EXEMPT":
            add(sec, "x", rid, rid, "具名豁免:" + str(r.get("why") or ""), cver if kind == "verb" else "")
            continue
        if kind == "case":
            rc = ov_json(ev_root / (rid + ".json"))
            if not rc:
                add(sec, "x", rid, rid, "沒有測試收據 · " + str(r.get("where") or "")[:150])
            else:
                good = rc.get("rc") == 0 and bool(rc.get("target_marker_seen"))
                add(sec, "g" if good else "r", rid, "%s · %s" % (rid, str(rc.get("scope") or "")[:90]), "%s · rc %s · 成功字樣 %s · %s收據" % (
                    "過" if good else "不過", rc.get("rc"), "對上" if rc.get("target_marker_seen") else "對不上", ov_host(rc.get("environment"))), "", rc.get("completed_at") or "")
            continue
        lamp, at, why = ov_station_row(state, r.get("by"))
        title = {"verb": "via-vcgc " + rid}.get(kind, rid)
        add(sec, lamp, rid, title if not name else "%s · %s" % (title, name), why + ((" · " + str(r.get("where"))[:90]) if kind != "verb" and r.get("where") else ""), cver if kind in ("verb", "seat") else "", at)
    # ④ 引擎與模組:標準化燈 = 語法過 + 加速器橋在 + 有號
    codes = {}
    comp = ov_json(reg / "VIA_Component_Inventory_SSOT_v0100.json") or {}
    for rec in comp.get("records") or []:
        if rec.get("category") in ("module", "engine", "tool") and rec.get("state") == "ACTIVE":
            codes[str(rec.get("source") or "").rsplit("/", 1)[-1]] = (rec.get("code") or "", rec.get("first_seen") or rec.get("ts") or "")
    exempt = set((inv.get("bridge_exempt") or {}).keys()) if isinstance(inv.get("bridge_exempt"), dict) else set(inv.get("bridge_exempt") or [])
    for f in ov_families(reg):
        code, seen = codes.get(f["file"], ("", ""))
        upd = state.get("upd:" + f["file"][:-3]) if isinstance(state, dict) else None
        miss = [w for w, bad in (("語法不過", not f["syntax"]), ("沒有加速器橋", not f["bridge"] and f["file"] not in exempt and f["family"] not in exempt), ("還沒編號", not code)) if bad]
        lamp = "r" if (not f["syntax"] or "沒有加速器橋" in miss) else ("y" if miss else "g")
        test_note = (" · 自測 %s(%s)" % (upd.get("lamp"), str(upd.get("at") or "")[:16])) if isinstance(upd, dict) else ""
        add(OV_SECTIONS[3], lamp, f["family"], "%s · %s" % (f["family"], f["doc"] or "(沒有說明)"), "%s · 號 %s · 共 %d 版%s" % ("標準化齊" if not miss else " · ".join(miss), code or "—", f["versions"], test_note), f["ver"], seen)
    # ⑦ 鎖版工具
    lock = ov_json(reg / "VIA_ToolVersion_Lock_v0100.json") or {}
    for k, v in lock.items():
        if not isinstance(v, dict) or not v.get("path"):
            continue
        p = via.parent / v["path"]
        if not p.exists():
            p = via / v["path"]
        if not p.exists():
            add(OV_SECTIONS[6], "r", k, "%s · %s" % (k, Path(v["path"]).name), "鎖冊上的檔不在")
            continue
        raw = p.read_bytes()
        got = [hashlib.sha256(b).hexdigest() for b in (raw, raw.replace(b"\r\n", b"\n"))]
        want = str(v.get("sha256") or v.get("sha") or "")
        ok = bool(want) and any(g.startswith(want) or want.startswith(g[:len(want)]) for g in got)
        add(OV_SECTIONS[6], "g" if ok else ("y" if not want else "r"), k, "%s · %s" % (k, p.name), "雜湊與鎖冊相同" if ok else ("鎖冊沒有記雜湊" if not want else "雜湊與鎖冊不同"), re.search(r"v\d{4}", p.name).group(0) if re.search(r"v\d{4}", p.name) else "", str(v.get("activated_at") or v.get("ts") or ""))
    # ⑧ 頁面:讀同步台自己的收據
    sync = ov_json(rep / "SYNC_latest.json") or {}
    pages = [r for r in (sync.get("pages") or []) + (sync.get("links") or []) if isinstance(r, dict)]
    if not pages:
        notes.append("沒有同步台收據 SYNC_latest.json(先跑 synchronizer);頁面一段是灰")
    for r in pages:
        add(OV_SECTIONS[7], OV_LAMP.get(str(r.get("lamp")), "x"), r.get("id") or r.get("name"), "%s%s" % (r.get("name") or "", (" · " + str(r.get("page"))) if r.get("page") else ""),
            str(r.get("note") or ""), str(r.get("version") or ""), str(r.get("page_time") or r.get("time") or ""))
    # ⑨ 治理冊
    for label, pat in (("政策冊", "VIA_Policy_Laws_SSOT_v*.json"), ("需求冊", "VIA_Requirements_SSOT_v*.json"), ("工作流冊 VCGC", "VIA_Workflow_VCGC_SSOT_v*.json"), ("功能盤點冊", "VIA_VCGC_FunctionInventory_SSOT_v*.json"),
                       ("AI 功能卡冊", "VIA_AI_FunctionCard_SSOT_v*.json"), ("交接政策冊", "VIA_Handoff_Continuity_SSOT_v*.json"), ("編號冊", "VIA_Numbering_SSOT_v*.json"), ("元件註冊冊", "VIA_Component_Inventory_SSOT_v*.json"),
                       ("工具鎖冊", "VIA_ToolVersion_Lock_v*.json"), ("收據契約冊", "VIA_SystemReceipt_Contract_SSOT_v*.json"), ("版面鎖", "VIA_UI_WorkPlatform_TemplateLock_v*.json"), ("版面 token 冊", "VIA_UI_Template_SSOT_v*.json")):
        p = ov_tail(reg, pat)
        if not p:
            add(OV_SECTIONS[8], "x", label, label, "找不到這本冊")
            continue
        d = ov_json(p)
        add(OV_SECTIONS[8], "g" if d is not None else "r", p.stem.rsplit("_v", 1)[0], "%s · %s" % (label, p.name), "讀得到 · %d KB" % (p.stat().st_size // 1024) if d is not None else "JSON 讀不進來",
            "v" + p.stem.rsplit("_v", 1)[-1], str((d or {}).get("ts") or (d or {}).get("updated_at") or "") if isinstance(d, dict) else "")
    # ⑩ 需求(只列 VCGC 自己的;燈照需求冊自己的狀態)
    reqp = ov_tail(reg, "VIA_Requirements_SSOT_v*.json")
    reqs = (ov_json(reqp) or {}).get("requirements") or []
    lamp_of = {"COVERED": "g", "PARTIAL": "y", "MISSING": "r"}     # RECORDED(入冊、由 AI 程序遵守、沒有引擎把關)照實給灰
    for r in reqs:
        if isinstance(r, dict) and r.get("subsystem") == "VCGC":
            stt = str(r.get("status") or "")
            add(OV_SECTIONS[9], lamp_of.get(stt.upper(), "x"), r.get("code"), "%s · %s" % (r.get("code"), str(r.get("topic") or "")[:60]), "狀態 %s · %s" % (stt or "沒寫", str(r.get("requirement") or "")[:170]), "", "", stt.upper() == "MISSING")
    return {"source": "VCGC 功能一覽", "items": items, "notes": notes, "console": console.name if console else "", "inventory": inv_p.name if inv_p else ""}
# ===== [VIA:VCGC-OVERVIEW-CORE:END] =====


def ov_write(path: Path, text: str) -> None:
    """本版唯一的寫檔點(只寫自己的 VIA_Reports/vcgc;先寫暫存再換名)。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".%d.tmp" % os.getpid())
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(str(tmp), str(path))


def ov_tally(items) -> dict:
    out = {s: {"r": 0, "y": 0, "g": 0, "x": 0} for s in OV_SECTIONS}
    for it in items:
        out.setdefault(it["section"], {"r": 0, "y": 0, "g": 0, "x": 0})[it["lamp"] if it["lamp"] in "rygx" else "x"] += 1
    return out


def overview(args: list, via=None, rep=None) -> int:
    """功能一覽:整理項目冊 → 交給卡片矩陣正主出頁 → 收據。rc 只看頁有沒有做出來(0 / 1);內容燈另記。"""
    via = Path(via) if via else VIA
    rep = Path(rep) if rep else via / REP
    out, zh, t0 = rep / "overview", {"r": "紅", "y": "黃", "g": "綠", "x": "灰"}, time.time()
    print("[1/4] 讀冊與收據 15%", flush=True)
    doc = ov_collect(via)
    tally = ov_tally(doc["items"])
    book = out / OV_BOOK
    ov_write(book, json.dumps({"source": OV_TITLE, "title": OV_TITLE, "groups": [[s, [s]] for s in OV_SECTIONS], "items": doc["items"]}, ensure_ascii=False))
    print("[2/4] 卡片與矩陣 45%", flush=True)
    cmf = _tail(via / "supportive modules" / "registry", CMF_STEM)
    page, why, content = rep / OV_PAGE, "", "x"
    if cmf is None or _vnum(cmf) < CMF_MIN:
        why = "卡片矩陣引擎 %s 要 v%04d 以上(現在 %s)" % (CMF_STEM, CMF_MIN, cmf.name if cmf else "不在")
    else:
        try:
            cp = subprocess.run([sys.executable, str(cmf), "run", "--in", str(book), "--out", str(out), "--root", str(via), "--no-open", "--no-clip"], env=child_env(),
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
            made = out / "WORKPLATFORM_latest.html"
            if cp.returncode in (0, 1, 2) and made.is_file() and made.stat().st_mtime >= t0 - 2:
                content = {0: "g", 2: "y", 1: "r"}[cp.returncode]
                print("[3/4] 落頁 80%", flush=True)
                ov_write(page, made.read_text(encoding="utf-8"))
            else:
                why = "卡片矩陣引擎沒有寫出頁面(rc %s):%s" % (cp.returncode, ((cp.stdout or "") + (cp.stderr or "")).strip().splitlines()[-1:] or ["沒有輸出"])
        except subprocess.TimeoutExpired:
            why = "卡片矩陣引擎逾時(1200 秒)"
    ok = not why
    host = "Windows 主機實跑" if platform.system() == "Windows" else "%s(容器):這一輪不算主機實測" % platform.system()
    rec = {"schema": "VIA.VCGC.Overview.v1", "system": "VCGC", "receipt": "overview", "engine": FAMILY + "_" + VERSION, "version": VERSION,
           "lamp": "g" if ok else "r", "content_lamp": content, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "secs": round(time.time() - t0, 1),
           "summary": ("%d 列 · %d 區" % (len(doc["items"]), sum(1 for s in OV_SECTIONS if sum(tally[s].values())))) if ok else why, "rows": len(doc["items"]), "sections": tally,
           "notes": doc["notes"], "page": str(page) if ok else "", "book": str(book), "renderer": cmf.name if cmf else "", "console": doc.get("console"), "inventory": doc.get("inventory"), "host": host}
    ov_write(rep / OV_RECEIPT, json.dumps(rec, ensure_ascii=False, indent=1))
    print("[4/4] 完成 100%", flush=True)
    if "--json" in args:
        print(json.dumps(rec, ensure_ascii=False))
    else:
        print("[%s] 頁 %s · 內容 %s · %s · %s 秒 · %s" % (OV_TITLE, "綠" if ok else "紅", zh[content], rec["summary"], rec["secs"], host), flush=True)
        for s in OV_SECTIONS:
            c = tally[s]
            n = sum(c.values())
            lamp = "x" if not n else ("r" if c["r"] else "y" if c["y"] else "g" if c["g"] else "x")
            print("  [%s] %s %d · 紅 %d · 黃 %d · 綠 %d · 灰 %d" % (zh[lamp], s, n, c["r"], c["y"], c["g"], c["x"]), flush=True)
        for n in doc["notes"]:
            print("  [注] " + n, flush=True)
        if ok:
            print("[U/I] %s" % page, flush=True)
        print("NEXT: " + ("灰的多半是還沒有測試收據:跑 via-vcgc test(整輪)之後再跑一次本動詞" if ok else why), flush=True)
    if ok and "--no-open" not in args and not os.environ.get("VIA_NO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(page.resolve().as_uri())
        except Exception as e:
            print("[U/I] 開不起來(%s),請手動開上面那個檔" % type(e).__name__, flush=True)
    return 0 if ok else 1


def help_extra() -> None:
    print("  ── v0199 overview(VCGC 自己的全部功能;卡片看整體、矩陣看細節)──")
    print("  overview [--no-open] [--json]   讀既有的冊與收據 → 項目冊 → %s 出頁 → %s%s(rc 0 = 頁做出來;內容燈另記)" % (CMF_STEM, REP, OV_PAGE))


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(薄尾 · overview 一個動詞 + 原樣轉交;夾具 · 零網路 · 真樹只讀)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0198 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    chk("② 其餘動詞原樣轉交(version → 前版鏈 rc 0)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    doc = ov_collect(VIA)
    keys = {"section", "system", "lamp", "id", "title", "detail", "ver", "at", "needs"}
    secs = {it["section"] for it in doc["items"]}
    chk("③ 真樹:項目冊欄位齊 · 燈只有 r/y/g/x · 全是 VCGC · 區塊都在名單內", bool(doc["items"]) and all(set(it) == keys and it["lamp"] in "rygx" and it["system"] == "VCGC" for it in doc["items"]) and secs <= set(OV_SECTIONS), sorted(secs - set(OV_SECTIONS)))
    chk("④ 真樹:動詞 · 引擎 · 鎖版工具 · 治理冊 四區都有列", all(any(it["section"] == OV_SECTIONS[i] for it in doc["items"]) for i in (0, 3, 6, 8)), sorted(secs))
    ids = [(it["section"], it["id"]) for it in doc["items"]]
    chk("⑤ 同一區裡項目不重複", len(ids) == len(set(ids)), len(ids) - len(set(ids)))
    with tempfile.TemporaryDirectory(prefix="via_console199_") as td:
        fake = Path(td) / "VIA"
        (fake / "supportive modules" / "registry").mkdir(parents=True)
        d2 = ov_collect(fake)
        chk("⑥ 空樹:不炸;沒有的冊照實寫進說明或給灰,不編列", isinstance(d2["items"], list) and len(d2["notes"]) >= 2 and all(it["lamp"] == "x" for it in d2["items"]), (len(d2["items"]), d2["notes"]))
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep, sys.stdout = sys.stdout, nul
            try:
                rc_fake = overview(["--no-open"], via=fake)
            finally:
                sys.stdout = keep
        r2 = json.loads((fake / REP / OV_RECEIPT).read_text(encoding="utf-8"))
        chk("⑦ 空樹:卡片矩陣引擎不在 → rc 1 · 收據紅並寫原因 · 沒有假頁", rc_fake == 1 and r2["lamp"] == "r" and CMF_STEM in r2["summary"] and not (fake / REP / OV_PAGE).exists(), (rc_fake, r2.get("summary")))
        rep = Path(td) / "rep"
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep, sys.stdout = sys.stdout, nul
            try:
                rc_real = overview(["--no-open"], rep=rep)
            finally:
                sys.stdout = keep
        html = (rep / OV_PAGE).read_text(encoding="utf-8") if (rep / OV_PAGE).is_file() else ""
        r3 = json.loads((rep / OV_RECEIPT).read_text(encoding="utf-8")) if (rep / OV_RECEIPT).is_file() else {}
        chk("⑧ 真樹出頁(寫到暫存夾):rc 0 · 頁帶標題與每一區的群組卡片 · 樣式來自鎖定模板", rc_real == 0 and ("<h1>%s:" % OV_TITLE) in html and all(s in html for s in secs) and ".lamp" in html, (rc_real, len(html)))
        chk("⑨ 收據:頁燈與內容燈分開 · 列數 = 項目冊列數 · 各區燈數加起來對得上", r3.get("lamp") == "g" and r3.get("content_lamp") in ("g", "y", "r") and r3.get("rows") == len(doc["items"])
            and sum(sum(v.values()) for v in (r3.get("sections") or {}).values()) == len(doc["items"]), {k: r3.get(k) for k in ("lamp", "content_lamp", "rows")})
        chk("⑩ 沒留下暫存檔", not list(rep.rglob("*.tmp")))
    env = child_env()
    chk("⑪ 子行程環境:VIA_VCGC_PUSH=NO · VIA_NO_OPEN=1 · 只補自己的旗標", env.get("VIA_VCGC_PUSH") == "NO" and env.get("VIA_NO_OPEN") == "1" and env.get(OWN_FLAG)
        and not any(k in env and k not in os.environ for k in ("VIA_FROM_VDFSM", "VIA_FROM_VRN")))
    seen = []
    real = globals()["forward"]
    globals()["forward"] = lambda x: seen.append(list(x)) or 0
    try:
        m1, m2 = main(["synchronizer", "--last"]), main(["sync-check"])
    finally:
        globals()["forward"] = real
    chk("⑫ 只有 overview 留在本版;synchronizer · sync-check 等原樣轉交前版", seen == [["synchronizer", "--last"], ["sync-check"]] and m1 == 0 and m2 == 0, seen)
    names = [n for n in dir(_prior_module()) if not n.startswith("_") and callable(getattr(_prior_module(), n, None))]
    chk("⑬ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("⑭ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 寫檔只經 ov_write · 本檔沒有色碼",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|VDF_|VRN_)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src)
        and live.count(".write_text(") == 1 and not re.search(r"#[0-9a-fA-F]{6}\b", live))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:1] == ["overview"]:
        return overview(args[1:])
    if not args or args[0] == "help":
        rc = forward(args or ["help"])
        help_extra()
        return rc
    return forward(args)


if __name__ == "__main__":
    sys.exit(main())
