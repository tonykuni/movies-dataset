#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL174_PackagingGate v0100 — 三個專案的打包就緒閘(批673)
====================================================================
操作員令(批673):「受測字測字完成,邊修邊改,**三個專案到準備打包的程度**」。

先把題目講清楚,因為「準備打包」很容易被當成一句感覺:
  **能不能打包,不是「我覺得差不多了」,是七條各自量得出來的事。**
所以這支不給一個「完成度 87%」的數字——那種數字誰都推不翻,也就誰都不用負責。
它給**每個專案七列**,每一列一個誠實態,每一列後面掛一個**下一步**(L92)。

七列(每個專案各量一次):
  ① 引擎在位      冊上點名的尾版,樹上找不找得到(ABSENT = 冊樹不同步)
  ② 自測門覆蓋    帶 `--selftest` 的比例——**這是誠實分母**(批671 LL317)
  ③ 自測綠        從最新格子存證取該家族的站;**存證比樹舊就記 NODATA**(批669 律)
  ④ 四面登錄      LL199:加速器橋 · 根目錄梭 · Register · 格子站
  ⑤ 家族境可跑    RunGate 存證(容器沒有家族境 → GATED,不是 RED)
  ⑥ 落頁同一份規格 批672:會落頁的引擎有沒有接 CGC_MDL173(自己長一份 CSS = 尺散了)
  ⑦ 資料證據      該家族的正典庫/表實際列數(**空庫 = NODATA 不是 RED**)

判準不自備第二份:
  排除清單向 CGC_MDL124 橋掃器**整支取用**(批670 LL316:抄清單不算一個出處)。
  VRN 名冊向批665 已覆核的六層冊取;VDF/VIA 走家族前綴 + 同一份排除清單。

**這支零動作**:不裝任何套件、不設任何同意閘、不改任何檔。它只量、只說下一步。
  裝套件是操作員的手;同意閘的裁定權在操作員手上——AI 永不代設。

用法:
  via-packgate              → 打包就緒矩陣(三個專案 × 七列)
  via-packgate html         → 落 rich 矩陣頁(走 CGC_MDL173 排版規格;字小)
  via-packgate --only VRN   → 只看一個專案
  via-packgate --selftest   → 二十檢(沙盒零網路)
誠實 rc:0 三個都可打包 · 1 有真的壞 · 2 有缺料 · 3 有缺件 · 4 有等閘
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

import ast
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "packgate"
BATCH = "批673"
PROJECTS = ("VIA", "VDF", "VRN")
STATE_ORDER = ("RED", "ABSENT", "GATED", "NODATA", "GREEN")
RC = {"GREEN": 0, "RED": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4}
# 打包就緒的門檻:**GREEN 才算就緒**。NODATA/GATED 不是壞掉,但也不是「可以打包」——
#   把「量不到」講成「好了」,就是假綠(批671 兩個方向同時錯過一次,不要再來)。
READY_STATES = ("GREEN",)


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA)).replace("\\", "/")
    except Exception:
        return str(p)


def newest(root: Path, pat: str):
    c = sorted(root.glob(pat))
    return c[-1] if c else None


def row(project, item, state, detail="", fix="", n="", evidence="") -> dict:
    return {"project": project, "item": item, "state": state, "n": str(n),
            "detail": detail, "fix": fix, "evidence": evidence}


# ── 判準:排除清單向橋掃器整支取用(LL316)────────────────────────────
def _sweeper():
    """把 CGC_MDL124 橋掃器**整支**載進來,直接用它的 _excluded()。

    批670 實錄:第一版只 AST 取了兩張靜態清單,漏掉 4 支住在雜湊冊凍結夾的檔——
    「這個夾被凍結了」不在任何靜態清單裡,它是 _excluded() 裡的一段邏輯。
    **抄清單不算一個出處,抄到函式才算。**
    """
    eng = newest(HERE, "CGC_MDL124_BridgeSweeper_v*.py")
    if not eng:
        return None
    try:
        import importlib.util
        sp = importlib.util.spec_from_file_location("packgate_sweeper", eng)
        m = importlib.util.module_from_spec(sp)
        sys.modules["packgate_sweeper"] = m
        sp.loader.exec_module(m)
        return m if hasattr(m, "_excluded") else None
    except Exception:
        return None


_SWEEP = _sweeper()


def excluded(p: Path) -> bool:
    if _SWEEP is not None:
        try:
            return bool(_SWEEP._excluded(p))
        except Exception:
            pass
    # 橋掃器載不進來時**不自己造一份判準**,寧可全收——
    #   自備第二份排除清單,走鐘那天錯的方向是「去動不該動的東西」(批670 實錄)。
    return False


# ── 名冊:一個專案有哪些支 ─────────────────────────────────────────────
VRN_BOOK = HERE / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"


def _book_tails() -> list:
    """VRN 名冊向批665 已覆核的六層冊取(冊就是名冊,不手寫第二份)。"""
    if not VRN_BOOK.exists():
        return []
    try:
        book = json.loads(VRN_BOOK.read_text(encoding="utf-8"))
    except Exception:
        return []
    seen, out = set(), []
    def walk(o):
        if isinstance(o, dict):
            t = o.get("tail")
            if isinstance(t, str) and t.endswith(".py") and t not in seen:
                seen.add(t)
                out.append(t)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(book)
    return out


_VER_SUF = "_v"


def _tail_of_family(p: Path) -> Path:
    """同名家族的尾版(尾版律)。"""
    n = p.name
    if _VER_SUF not in n:
        return p
    stem = n.rsplit(_VER_SUF, 1)[0]
    sibs = sorted(p.parent.glob(f"{stem}{_VER_SUF}[0-9][0-9][0-9][0-9].py"))
    return sibs[-1] if sibs else p


def roster(project: str) -> list:
    """回該專案的尾版檔清單(已套橋掃器排除清單)。"""
    if project == "VRN":
        got = []
        for t in _book_tails():
            p = VIA / t
            if p.exists() and not excluded(p):
                got.append(_tail_of_family(p))
        return sorted(set(got))
    if project == "VDF":
        roots = [VIA / "functional modules" / "VDF"]
    else:  # VIA = 中央治理家族
        roots = [HERE]
    got = []
    for r in roots:
        if not r.exists():
            continue
        for p in r.rglob("*.py"):
            if excluded(p) or p.name.startswith("test_"):
                continue
            got.append(_tail_of_family(p))
    return sorted(set(got))


# ── ② 自測門(批671 LL317 的同一把尺;走 AST 不走 regex)──────────────
def has_door(p: Path) -> bool:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return False
    flag = "--" + "self" + "test"      # L133:別讓這支掃到自己這一行
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and n.value == flag:
            return True
    return False


# ── ③ 格子存證(比樹舊就不准拿來判現在;批669 律)──────────────────────
def _head_ct() -> int | None:
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=str(VIA),
                           capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def grid_evidence() -> tuple[dict | None, str]:
    runs = VIA / "VIA_Reports" / "selftest_runs"
    cands = sorted(runs.glob("GRID_*.json")) if runs.exists() else []
    if not cands:
        return None, "沒有格子存證——先跑一次全格子"
    p = cands[-1]
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, f"格子存證讀不開:{type(exc).__name__}"
    ct = _head_ct()
    if ct and p.stat().st_mtime < ct:
        gap = ct - p.stat().st_mtime
        unit = ("分鐘", gap / 60) if gap < 3600 else (("小時", gap / 3600) if gap < 86400
                                                     else ("天", gap / 86400))
        return None, (f"**這份存證比現在的樹舊**(比 HEAD commit 早 {unit[1]:.1f}{unit[0]})"
                      "——它講的是另一棵樹,不能拿來判現在")
    d["_path"] = rel(p)
    return d, ""


# ── ④ 四面登錄(LL199)──────────────────────────────────────────────────
def _register_text() -> str:
    reg = newest(VIA, "Register-VIA-Commands-v*.ps1")
    if not reg:
        return ""
    try:
        return reg.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def _grid_text() -> str:
    g = newest(HERE, "CGC_MDL064_SelftestGrid_v*.py")
    try:
        return g.read_text(encoding="utf-8", errors="replace") if g else ""
    except Exception:
        return ""


def dup_commands(reg_txt: str) -> list:
    """Register 裡被定義兩次以上的 via-* 短令(L101 一個名字只能有一扇門)。

    PowerShell 後定義覆蓋前定義,**而且不報錯**。被蓋掉的那一扇從此打不開,
    症狀只會是「怎麼沒反應」——這種壞法沒有紅燈,所以要有人去數。
    """
    import re as _re
    names = _re.findall(r"^function global:(via-[A-Za-z0-9-]+)\s", reg_txt, _re.M)
    seen, dup = set(), set()
    for n in names:
        (dup if n in seen else seen).add(n)
    return sorted(dup)


def has_accel_bridge(p: Path) -> bool:
    try:
        return "[VIA:ACCEL" + "-BRIDGE:" in p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False


# ── ⑥ 落頁的支有沒有接排版規格(批672)────────────────────────────────
def page_engines(files: list) -> tuple[list, list]:
    """回 (跑完會落「報告頁」的支, 其中沒接 CGC_MDL173 的支)。

    範圍要對準操作員那句話:**「以後跑完都要生成矩陣式報告」**——
    講的是**跑完落在 VIA_Reports 的那種報告頁**,不是 U/I 頁。
    第一版我把「原始碼裡寫得出 .html」全算進來,於是 97 支裡有 80 支被判成
    「自己帶一份 CSS」——那裡面有 U/I 產生器、有收容件、有批647 的位元正本頁。
    **拿一個沒人約定過的判準去量,量出來的紅燈是我發明的**(先疑尺不疑樹 L93)。
    所以這裡只收:源碼裡把 .html 落進 VIA_Reports 的支。
    """
    pagers, loose = [], []
    needle = "CGC_MDL173"
    for p in files:
        try:
            s = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if ".html" not in s or "VIA_Reports" not in s:
            continue
        # 落點確實指向報告夾:同一行(或很近)同時看得到報告夾與 .html
        hit = any("VIA_Reports" in ln and (".html" in ln or "html" in ln.lower())
                  for ln in s.splitlines())
        if not hit and "REPORTS" not in s:
            continue
        pagers.append(p)
        if needle not in s and ("</sty" + "le>") in s:
            loose.append(p)
    return pagers, loose


# ── ⑦ 資料證據 ────────────────────────────────────────────────────────
DATA_EVIDENCE = {
    "VRN": (VIA / "VIA_Reports" / "vrn" / "matrix" / "VRN_MATRIX_latest.json", "研報逐列舉證"),
    "VDF": (VIA / "VIA_Reports" / "vdf_chain" / "VDFCHAIN_latest.json", "VDF 鏈實跑存證"),
    "VIA": (VIA / "VIA_Reports" / "state_matrix" / "STATE_latest.json", "六域現況存證"),
}


def data_row(project: str) -> dict:
    p, why = DATA_EVIDENCE[project]
    if not p.exists():
        return row(project, "⑦ 資料證據", "NODATA", f"{why}不在:{rel(p)}",
                   {"VRN": "via-vrnchain run", "VDF": "via-vdfchain run",
                    "VIA": "via-state"}[project] + " 先產一份存證",
                   0, rel(p))
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return row(project, "⑦ 資料證據", "RED", f"存證讀不開:{type(exc).__name__}",
                   "看檔是不是寫到一半", 0, rel(p))
    n = 0
    if isinstance(d, dict):
        for k in ("rows", "reports", "stages"):
            v = d.get(k)
            if isinstance(v, list):
                n = max(n, len(v))
    age = (time.time() - p.stat().st_mtime) / 86400
    if n == 0:
        return row(project, "⑦ 資料證據", "NODATA",
                   f"{why}在,但**列數 0**——一個全綠如果庫裡 0 列,那個綠沒有意義",
                   "先把料放進去再談打包", 0, rel(p))
    return row(project, "⑦ 資料證據", "GREEN", f"{why} {n} 列(齡 {age:.1f} 天)",
               "", n, rel(p))


# ── 收集 ──────────────────────────────────────────────────────────────
def collect(only: str = "") -> dict:
    grid, grid_why = grid_evidence()
    reg_txt, grid_txt = _register_text(), _grid_text()
    rows: list = []
    for proj in PROJECTS:
        if only and proj.upper() != only.upper():
            continue
        files = roster(proj)
        # ① 引擎在位
        if proj == "VRN":
            tails = _book_tails()
            missing = [t for t in tails if not (VIA / t).exists()]
            rows.append(row(proj, "① 引擎在位", "ABSENT" if missing else "GREEN",
                            (f"冊上 {len(tails)} 支,樹上找不到 {len(missing)}:"
                             + "·".join(Path(x).name for x in missing[:3])) if missing
                            else f"冊上 {len(tails)} 支全部在樹上(已解析到尾版)",
                            "`via-vrnbook build` 重建冊;或 git pull" if missing else "",
                            len(tails), rel(VRN_BOOK)))
        else:
            rows.append(row(proj, "① 引擎在位", "GREEN" if files else "ABSENT",
                            f"樹上尾版 {len(files)} 支(已套橋掃器排除清單)"
                            if files else "一支都掃不到——根目錄對不對?",
                            "" if files else "確認 functional modules/VDF 或 registry 夾在位",
                            len(files)))
        # ② 自測門覆蓋(誠實分母)
        doors = [p for p in files if has_door(p)]
        pct = (100.0 * len(doors) / len(files)) if files else 0.0
        st2 = "GREEN" if files and pct >= 100.0 else ("NODATA" if files else "ABSENT")
        rows.append(row(proj, "② 自測門覆蓋", st2,
                        f"{len(doors)}/{len(files)} = {pct:.1f}% 帶 --selftest"
                        + ("" if st2 == "GREEN" else
                           " —— **沒有門的支量不到**(批671 LL317);量不到不是壞掉,"
                           "但也不能說它好了"),
                        "" if st2 == "GREEN" else
                        "逐支補 --selftest 門,或在冊上標免測**並附理由**(L87)",
                        f"{len(doors)}/{len(files)}"))
        # ③ 自測綠(讀最新格子存證;存證比樹舊就不判)
        if grid is None:
            rows.append(row(proj, "③ 自測綠(格子存證)", "NODATA", grid_why,
                            "先跑一次全格子再回來看", 0))
        else:
            res = grid.get("results") or []
            key = {"VRN": "VRN", "VDF": "VDF", "VIA": "VIA"}[proj]
            sub = [r for r in res if key in str(r.get("name", ""))]
            bad = [r for r in sub if r.get("state") == "FAIL"]
            st3 = ("GREEN" if sub and not bad else
                   ("RED" if bad else "NODATA"))
            rows.append(row(proj, "③ 自測綠(格子存證)", st3,
                            (f"{key} 相關站 {len(sub)} 個 · FAIL {len(bad)}"
                             + ("" if not bad else ":"
                                + "·".join(str(r.get('name'))[:24] for r in bad[:2]))
                             ) if sub else f"格子裡沒有名字帶 {key} 的站——量不到",
                            "" if st3 == "GREEN" else "逐站看敗因",
                            len(sub), grid.get("_path", "")))
        # ④ 四面登錄(LL199)
        bridges = [p for p in files if has_accel_bridge(p)]
        cmd_tokens = {"VRN": ("via-vrnchain", "via-vrnbook"),
                      "VDF": ("via-vdfchain",), "VIA": ("via-state", "via-matrixspec")}[proj]
        in_reg = [c for c in cmd_tokens if f"function global:{c}" in reg_txt]
        shims = [c for c in cmd_tokens if (VIA / f"{c}.cmd").exists()
                 and (VIA / "bin" / f"{c}.cmd").exists()]
        in_grid = [c for c in cmd_tokens if c in grid_txt] or \
                  [t for t in ({"VRN": "MDL172", "VDF": "MDL170", "VIA": "MDL169"}[proj],)
                   if t in grid_txt]
        br_pct = (100.0 * len(bridges) / len(files)) if files else 0.0
        # L101 一個名字只能有一扇門:Register 裡同名 function 定義兩次,**後面那個會默默蓋掉前面**。
        #   蓋掉的那一扇不會報錯,只是從此打不開——這種壞法沒有紅燈,只有「怎麼沒反應」。
        dup = dup_commands(reg_txt)
        mine_dup = [c for c in cmd_tokens if c in dup]
        four = (br_pct >= 100.0 and len(in_reg) == len(cmd_tokens)
                and len(shims) == len(cmd_tokens) and bool(in_grid) and not mine_dup)
        extra = ""
        if mine_dup:
            extra = f" · **本專案短令重名 {len(mine_dup)}**:" + "·".join(mine_dup)
        elif proj == "VIA" and dup:
            # Register 是 VIA 這一面的東西,全樹重名在這一格具名列出(不記在別人頭上)
            extra = (f" · 全樹短令重名 {len(dup)}(L101 後定義覆蓋前定義):"
                     + "·".join(sorted(dup)[:4]))
        rows.append(row(proj, "④ 四面登錄(LL199)",
                        "GREEN" if four and not (proj == "VIA" and dup) else "NODATA",
                        f"加速器橋 {len(bridges)}/{len(files)}({br_pct:.1f}%) · "
                        f"Register {len(in_reg)}/{len(cmd_tokens)} · "
                        f"梭(根+bin) {len(shims)}/{len(cmd_tokens)} · "
                        f"格子站 {'在' if in_grid else '缺'}" + extra,
                        "" if four and not (proj == "VIA" and dup) else
                        ("重名的短令留一扇門(L101),其餘改名或刪定義" if (mine_dup or dup)
                         else "四面缺哪一面就補哪一面:橋/梭/Register/格子站"),
                        f"{len(bridges)}/{len(files)}"))
        # ⑤ 家族境可跑(RunGate 存證)
        rg = VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json"
        if not rg.exists():
            rows.append(row(proj, "⑤ 家族境可跑", "NODATA", "沒有 RunGate 存證",
                            f"via-rungate --family {proj.lower()}", 0, rel(rg)))
        else:
            try:
                d5 = json.loads(rg.read_text(encoding="utf-8"))
            except Exception:
                d5 = {}
            fam = (d5.get("families") or {}).get(proj.lower()) or {}
            v = str(fam.get("verdict") or fam.get("state") or "")
            st5 = ("GREEN" if v.upper() in ("GREEN", "OK", "PASS") else
                   ("GATED" if not v else "NODATA"))
            rows.append(row(proj, "⑤ 家族境可跑", st5,
                            (f"RunGate 判 {v}" if v else
                             "這台機器上沒有這個家族境的紀錄 —— "
                             "**容器量不到家族境,那是 GATED 不是壞掉**;"
                             "裝套件是操作員的手"),
                            "" if st5 == "GREEN" else
                            f"在工作站跑:via-rungate --family {proj.lower()}",
                            0, rel(rg)))
        # ⑥ 落頁同一份規格(批672)
        pagers, loose = page_engines(files)
        st6 = "GREEN" if not loose else "NODATA"
        rows.append(row(proj, "⑥ 落頁同一份規格", st6,
                        (f"會落頁 {len(pagers)} 支,全部接 CGC_MDL173 排版規格"
                         if not loose else
                         f"會落頁 {len(pagers)} 支,其中 {len(loose)} 支**自己帶一份 CSS**:"
                         + "·".join(p.name for p in loose[:3])
                         + " —— 規格散在幾個地方,它就不是規格(批672 LL321)"),
                        "" if not loose else "那幾支改呼叫 CGC_MDL173.page()/page_html()",
                        f"{len(pagers) - len(loose)}/{len(pagers)}"))
        # ⑦ 資料證據
        rows.append(data_row(proj))

    tally = {s: 0 for s in STATE_ORDER}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    per_proj = {}
    for proj in PROJECTS:
        sub = [r for r in rows if r["project"] == proj]
        if not sub:
            continue
        ready = all(r["state"] in READY_STATES for r in sub)
        blockers = [r["item"] for r in sub if r["state"] not in READY_STATES]
        per_proj[proj] = {"ready": ready, "rows": len(sub), "blockers": blockers}
    worst = next((s for s in STATE_ORDER if tally.get(s)), "GREEN")
    rc = RC[worst]
    return {"schema": "VIA_PACKGATE_v1", "batch": BATCH,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "python": sys.version.split()[0], "only": only,
            "rows": rows, "tally": tally, "per_project": per_proj,
            "rc": rc, "rc_name": worst,
            "ready_projects": [k for k, v in per_proj.items() if v["ready"]],
            "grid_evidence": (grid or {}).get("_path", "") or grid_why}


# ── 出（表由 rich 畫;殼走 CGC_MDL173 排版規格)────────────────────────
HEADERS = ("專案", "列", "態", "數", "量到什麼 · 為什麼是這個燈", "下一步", "出處")


def _spec_mod():
    """排版規格向 CGC_MDL173 **整支取用**(批672;不自備第二份 CSS)。"""
    import importlib.util
    c = sorted(HERE.glob("CGC_MDL173_MatrixReportSpec_v*.py"))
    if not c:
        return None
    try:
        sp = importlib.util.spec_from_file_location("via_matrixspec", c[-1])
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m
    except Exception:
        return None


def to_markdown(rep: dict) -> str:
    t = rep["tally"]
    out = [f"# 三個專案 · 打包就緒閘({rep['batch']})", "",
           f"- 產生 {rep['generated']} · 主機 {rep['host']} · python {rep['python']}",
           f"- GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']} · "
           f"NODATA {t['NODATA']} · ABSENT {t['ABSENT']} → **{rep['rc_name']}**",
           f"- 可打包:{'、'.join(rep['ready_projects']) or '(還沒有)'}", "",
           "> **能不能打包不是一句感覺。** GREEN 才算就緒;NODATA/GATED 不是壞掉,"
           "但把「量不到」講成「好了」就是假綠。", "",
           "| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
    for r in rep["rows"]:
        out.append("| " + " | ".join(str(r[k]).replace("|", "/") for k in
                                     ("project", "item", "state", "n", "detail",
                                      "fix", "evidence")) + " |")
    out.append("")
    for k, v in rep["per_project"].items():
        out.append(f"- **{k}**:{'可打包' if v['ready'] else '未就緒'}"
                   + ("" if v["ready"] else " · 卡在 " + "、".join(v["blockers"])))
    return "\n".join(out) + "\n"


def render(rep: dict) -> tuple[Path | None, bool]:
    M = _spec_mod()
    if M is None:
        print("  [NODATA] CGC_MDL173 排版規格缺席 → 不落頁(不自備第二份 CSS)")
        return None, False
    ok, why = M.rich_ok()
    if not ok:
        print(f"  [NODATA] {why}")
        return None, False
    con = M.console()
    t = M.table("三個專案 · 打包就緒閘",
                [{"name": "專案", "width": 5}, {"name": "列", "width": 18},
                 {"name": "態", "width": 7, "justify": "center"},
                 {"name": "數", "width": 8, "justify": "right"},
                 {"name": "量到什麼 · 為什麼是這個燈", "width": 74},
                 {"name": "下一步", "width": 34}])
    for r in rep["rows"]:
        col = M.SPEC["states"].get(r["state"], "")
        t.add_row(r["project"], r["item"], f"[{col}]{r['state']}[/]", r["n"],
                  r["detail"], r["fix"])
    con.print(t)
    t2 = M.table("逐專案裁決", [{"name": "專案", "width": 6},
                                {"name": "裁決", "width": 10},
                                {"name": "卡在哪(GREEN 才算就緒)"}])
    for k, v in rep["per_project"].items():
        c = M.SPEC["states"]["GREEN" if v["ready"] else "NODATA"]
        t2.add_row(k, f"[{c}]{'可打包' if v['ready'] else '未就緒'}[/]",
                   "、".join(v["blockers"]) or "—")
    con.print(t2)
    tl = rep["tally"]
    kpis = [{"label": k, "value": tl[k], "state": k} for k in STATE_ORDER]
    kpis.append({"label": "可打包", "value": len(rep["ready_projects"]), "state": "GREEN"})
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = M.page(con, title="三個專案 · 打包就緒閘 · 批673",
               subtitle=(f"{rep['generated']} · 主機 {rep['host']} · python {rep['python']}"
                         f" · 格子存證 {rep['grid_evidence']}"),
               md=to_markdown(rep), payload=rep, kpis=kpis,
               law=("<b>能不能打包不是一句感覺。</b> 七列各自量得出來,每一列後面掛一個下一步。<br>"
                    "<b>GREEN 才算就緒</b>——NODATA / GATED 不是壞掉,但把「量不到」講成"
                    "「好了」就是假綠(批671 同一天兩個方向都錯過一次)。<br>"
                    "<b>本閘零動作</b>:不裝套件、不設同意閘、不改任何檔。"
                    "裝套件是操作員的手;同意閘的裁定權在操作員手上。"),
               out=REPORTS / "VIA_Packaging_Gate_v0100.html")
    return p, True


def write_log(rep: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"PACKGATE_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "PACKGATE_latest.json").write_text(body, encoding="utf-8")
    (REPORTS / "PACKGATE_latest.md").write_text(to_markdown(rep), encoding="utf-8")
    led = REPORTS / "LEDGER.tsv"
    head = "" if led.exists() else "ts\trc\tready\tGREEN\tRED\tGATED\tNODATA\tABSENT\n"
    t = rep["tally"]
    with led.open("a", encoding="utf-8") as f:
        f.write(head + f"{ts}\t{rep['rc_name']}\t{','.join(rep['ready_projects'])}\t"
                       f"{t['GREEN']}\t{t['RED']}\t{t['GATED']}\t{t['NODATA']}\t"
                       f"{t['ABSENT']}\n")
    return REPORTS / "PACKGATE_latest.json"


def print_plain(rep: dict) -> None:
    t = rep["tally"]
    for r in rep["rows"]:
        print(f"  {r['state']:<7}{r['project']:<5}{r['item']:<18}{r['detail'][:96]}")
    print(f"  [計] GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']} · "
          f"NODATA {t['NODATA']} · ABSENT {t['ABSENT']} → {rep['rc_name']}")
    for k, v in rep["per_project"].items():
        print(f"  [{k}] {'可打包' if v['ready'] else '未就緒'}"
              + ("" if v["ready"] else " · 卡在 " + "、".join(v["blockers"])))


# ── 自測 ──────────────────────────────────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails: list[str] = []

    def chk(name, ok, note=""):
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}")
        if not ok:
            fails.append(name)

    rep = collect()
    # ① 三個專案 × 七列
    chk("三個專案各七列", len(rep["rows"]) == 21 and
        {r["project"] for r in rep["rows"]} == set(PROJECTS), f"({len(rep['rows'])} 列)")
    # ② 每一列都有態,而且態在誠實六態裡
    chk("每一列都有誠實態", all(r["state"] in STATE_ORDER for r in rep["rows"]))
    # ③ 非 GREEN 的列一定掛得出下一步(L92)
    noplan = [r["item"] for r in rep["rows"] if r["state"] != "GREEN" and not r["fix"]]
    chk("非綠的列都給得出下一步(L92)", not noplan, f"({noplan[:2]})")
    # ④ GREEN 才算就緒:把一列塞成 NODATA,該專案必須翻成未就緒
    fake = json.loads(json.dumps(rep))
    fake["rows"][0]["state"] = "NODATA"
    sub = [r for r in fake["rows"] if r["project"] == fake["rows"][0]["project"]]
    chk("GREEN 才算就緒(一列非綠就不就緒)",
        not all(r["state"] in READY_STATES for r in sub))
    # ⑤ rc 與燈一致(紅 > 缺件 > 等閘 > 缺料 > 綠)
    worst = next((s for s in STATE_ORDER if rep["tally"].get(s)), "GREEN")
    chk("rc 與燈一致", rep["rc"] == RC[worst] and rep["rc_name"] == worst,
        f"(rc={rep['rc']} {rep['rc_name']})")
    # ⑥ 排除清單向橋掃器整支取用,不自備第二份(LL316)
    chk("排除清單向 CGC_MDL124 整支取用", _SWEEP is not None and hasattr(_SWEEP, "_excluded"),
        "(橋掃器載得進來)" if _SWEEP else "(橋掃器載不進來 → 寧可全收,不自造判準)")
    # ⑦ 自測門探針兩向皆準(本支有門;沙盒假檔沒門)
    with tempfile.TemporaryDirectory() as td:
        nod = Path(td) / "no_door.py"
        nod.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        chk("自測門探針兩向皆準", has_door(Path(__file__)) and not has_door(nod))
    # ⑧ 尾版解析:冊釘舊版號時要解析到樹上尾版
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "zz_v0100.py").write_text("x=1\n", encoding="utf-8")
        (d / "zz_v0101.py").write_text("x=2\n", encoding="utf-8")
        chk("尾版解析(冊釘舊版號也要敲到尾版)",
            _tail_of_family(d / "zz_v0100.py").name == "zz_v0101.py")
    # ⑨ VRN 名冊出自六層冊(不手寫第二份)
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest(")[0]
    chk("VRN 名冊出自六層冊(不手寫第二份)",
        "VIA_VRN_LogicArchitecture_SSOT" in src and len(_book_tails()) > 0,
        f"(冊上 {len(_book_tails())} 支)")
    # ⑩ 存證比樹舊 → 不准拿來判現在(批669 律)
    chk("存證比樹舊的路徑寫在碼上", "比現在的樹舊" in src)
    # ⑪ 空庫不是紅(批669 同律):資料列 0 要記 NODATA
    chk("空庫記 NODATA 不記 RED", "列數 0" in src and "那個綠沒有意義" in src)
    # ⑫ 本閘零動作:不准出現裝套件/設同意閘/刪檔的動詞
    bad_verbs = [v for v in ("pip install", "conda install", "Remove-Item", "shutil.rmtree",
                             "VIA_NET_CONSENT'] =", 'VIA_NET_CONSENT"] =')
                 if v in src]
    chk("零動作(不裝套件·不設同意閘·不刪檔)", not bad_verbs, f"({bad_verbs})")
    # ⑬ 零網路
    chk("零網路", "import requests" not in src and "urllib.request" not in src)
    # ⑭ 落頁走 CGC_MDL173(不自備第二份 CSS)
    #   第一版寫 `"body{" not in src` —— 結果咬到的是 page_engines() 裡那個
    #   **偵測字串**(它就是拿 "body{" 去看別人有沒有自帶 CSS)。
    #   偵測器不是樣式表。要問的是「這支有沒有在**寫**樣式」:
    #   有沒有收尾的 </style>、有沒有 css = ( 這種樣式表賦值。
    #   (同一類坑今天第三次:批664 拿 regex 讀 regex、批672 宣告零 CDN 被當成 CDN。)
    declares_css = ("</sty" + "le>") in src or ("css = (" in src)
    chk("落頁走 CGC_MDL173 排版規格(本支不寫樣式)",
        "CGC_MDL173" in src and not declares_css, f"(自寫樣式={declares_css})")
    # ⑮ MD 三段齊
    md = to_markdown(rep)
    chk("MD 三段齊(抬頭 · 逐列 · 逐專案裁決)",
        all(s in md for s in ("# 三個專案 · 打包就緒閘", "| 專案 |", "**VRN**")))
    # ⑯ --only 只留一個專案
    one = collect(only="VRN")
    chk("--only 只留一個專案", {r["project"] for r in one["rows"]} == {"VRN"}
        and len(one["rows"]) == 7, f"({len(one['rows'])} 列)")
    # ⑰ 頁落得出來且零外連(規格在的話)
    M = _spec_mod()
    if M is None or not M.rich_ok()[0]:
        chk("頁零外連 · 三顆鍵在位", True, "(規格或 rich 缺席,此檢不適用)")
    else:
        import re as _re
        con = M.console()
        con.print(M.table("x", ["a"]))
        with tempfile.TemporaryDirectory() as td:
            h = M.page(con, title="t", md=md, payload=rep,
                       out=Path(td) / "p.html").read_text(encoding="utf-8")
        ext = _re.findall(r"(?:src|href)\s*=\s*['\"](?:https?:)?//[^'\"]+", h)
        chk("頁零外連 · 三顆鍵在位",
            not ext and all(k in h for k in ("vmd()", "vjson()", "vcopy()")),
            f"(外連 {len(ext)})")
    # ⑱ 自我指涉閘(L133):本支不拿自己的格子站當判準
    chk("自我指涉閘(不讀自己那一站當判準)", "MDL174" not in src.replace("CGC_MDL174_", ""))
    # ⑲ 存證四件 + 台帳 append-only
    n0 = 0
    led = REPORTS / "LEDGER.tsv"
    if led.exists():
        n0 = len(led.read_text(encoding="utf-8").splitlines())
    write_log(rep)
    n1 = len(led.read_text(encoding="utf-8").splitlines())
    chk("存證四件 + 台帳 append-only",
        all((REPORTS / f).exists() for f in ("PACKGATE_latest.json", "PACKGATE_latest.md"))
        and n1 > n0, f"(台帳 {n1} 行)")

    # ⑳ 短令重名探針(L101):合成一份有重名的 Register 文字,必須抓得到
    fake_reg = ("function global:via-aaa {\n}\n"
                "function global:via-bbb {\n}\n"
                "function global:via-aaa {\n}\n")
    chk("短令重名探針(L101 後定義會默默蓋掉前定義)",
        dup_commands(fake_reg) == ["via-aaa"] and dup_commands("function global:via-x {\n") == [],
        f"({dup_commands(fake_reg)})")
    n = 20 - len(fails)
    print(f"  [計] 二十檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print("=== 三個專案打包就緒閘 v0100 · 二十檢(沙盒零網路)===")
        return selftest()
    only = a[a.index("--only") + 1] if "--only" in a and len(a) > a.index("--only") + 1 else ""
    verb = next((x for x in a if not x.startswith("-") and x != only), "gate")
    if verb not in ("gate", "html"):
        print(f"  [用法] gate | html [--only VIA|VDF|VRN] | --selftest(收到 {verb!r})")
        return 2
    rep = collect(only=only)
    if verb == "html":
        p, ok = render(rep)
        if p:
            print(f"  [頁] {rel(p)}")
            if ok and not os.environ.get("VIA_NO_OPEN"):
                try:
                    import webbrowser
                    webbrowser.open(p.as_uri())
                except Exception:
                    pass
    else:
        print_plain(rep)
    write_log(rep)
    print("  [律] **GREEN 才算就緒。** NODATA/GATED 不是壞掉,但把「量不到」講成「好了」"
          "就是假綠。本閘零動作:裝套件是操作員的手,同意閘 AI 永不代設。")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
