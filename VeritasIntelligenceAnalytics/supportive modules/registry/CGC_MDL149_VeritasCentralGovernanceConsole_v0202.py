#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0202 — 薄尾(v0201 一字不動):功能一覽改成 Dashboard(三大功能分欄)· 被取代的交接案不再亮紅

操作員 2026-11-19:「U/I 可以接近兩邊邊界近一點,當 DASHBOARD,一頁可彈性地放入不同類型資料型式」
「VCGC 有中央監管功能 / 節省 TOKEN 及支援功能 / 具對話顯示功能,最佳化視覺展現」「將 VCGC 紅黃問題解決掉」「你決定自動完成」。
本版只在 overview 上補兩件,其餘動詞一律原樣轉交前版 v0201;做法同前兩版:同一行程叫前版,只在讀冊與寫檔的點補,跑完還原。
  ① Dashboard:項目冊多帶 layout(三欄:中央監管 · 省 Token 與支援 · 對話顯示;各欄收哪幾區寫在本檔的 PILLARS),
     由卡片矩陣正主 v0108 照版面冊 VIA_UI_WorkPlatform_DashboardLayout 的規則出頁(貼近兩邊 · 系統訊號一排 · 三欄 · 比例條)。
     模板鎖冊一字不動;本檔不帶任何樣式。
  ② ⑤ 交接測試案:交接冊上「所有工作項都記成被取代(SUPERSEDED)」的案,它的舊收據不再算紅——改亮灰並寫明被誰取代。
     (實錄:24 案已記被取代,一覽上照舊收據亮紅,把真的紅淹掉。)只改顯示;交接冊、收據一個字都不動。
零網路([VIA:NET-BRIDGE] 留名);不碰 TA-Lib;不讀寫同意閘;本版自己不寫檔。不是 Windows 主機跑的不算主機實測。
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
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0202"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
CMF_MIN = 108                                        # 卡片矩陣正主 v0108 起項目冊可要 Dashboard 版面
HANDOFF_BOOK = "VIA_Handoff_Continuity_SSOT"
SEC_CASE = "⑤ 交接測試案"
PILLARS = [
    {"name": "中央監管", "note": "各系統的訊號 · 交接 · 需求 · 冊 · 契約",
     "sections": ["① 入口與動詞", "② 席位", "⑤ 交接測試案", "⑥ 工作流步驟", "⑨ 治理冊", "⑩ 需求", "⑫ 同儕系統自報(只讀)", "⑬ 參數冊", "⑭ 介面契約", "⑮ VCGC 自己的收據"]},
    {"name": "省 Token 與支援", "note": "AI 與操作員用的工具 · 引擎 · 加速器", "sections": ["③ AI 功能卡", "④ 引擎與模組(標準化)", "⑦ 鎖版工具", "⑪ PS 入口"]},
    {"name": "對話顯示", "note": "給人與 AI 讀的頁面與回饋", "sections": ["⑧ 頁面"], "feedback": True}]


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0201(子行程 · rc 不變)。"""
    pp = _prior_path()
    if pp is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(pp), *args], env=_env()).returncode


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


def superseded_cases(via) -> dict:
    """交接冊上「所有工作項都是 SUPERSEDED」的案 → {案名: 被誰取代}。冊讀不到回空。"""
    hits = [p for p in (Path(via) / "supportive modules" / "registry").glob(HANDOFF_BOOK + "_v*.json") if _vnum(p) >= 0]
    if not hits:
        return {}
    try:
        doc = json.loads(max(hits, key=_vnum).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    by = {}
    for w in doc.get("work_items") or [] if isinstance(doc, dict) else []:
        if isinstance(w, dict) and w.get("case"):
            by.setdefault(str(w["case"]), []).append(w)
    out = {}
    for case, ws in by.items():
        if all(w.get("state") == "SUPERSEDED" for w in ws):
            succ = sorted({str(w.get("superseded_by") or "").split(":", 1)[-1] for w in ws if w.get("superseded_by")})
            out[case] = "、".join(succ) or "沒寫接手的案"
    return out


def mark_superseded(items: list, sup: dict) -> int:
    """⑤ 裡被取代的案改亮灰、寫明接手的案;回改了幾列。只動這一輪的顯示列。"""
    n = 0
    for it in items:
        if it.get("section") == SEC_CASE and it.get("id") in sup:
            it["detail"] = "已被取代(接手:%s)· 舊收據:%s" % (sup[it["id"]], it.get("detail") or "")
            it["lamp"], it["needs"] = "x", ""
            n += 1
    return n


def overview(args: list, via=None, rep=None) -> int:
    """功能一覽:在 v0201 之上加 Dashboard 版面與被取代案的顯示。"""
    P = _prior_module()                    # v0201
    P200 = P._prior_module()               # v0200
    Q = P200._prior_module()               # v0199
    via_p = Path(via) if via else VIA
    keep = {"collect": Q.ov_collect, "write": Q.ov_write, "pver": P.VERSION, "pmin": P.CMF_MIN}
    seen = {"sup": 0}

    def collect(v):
        doc = keep["collect"](v)
        seen["sup"] = mark_superseded(doc["items"], superseded_cases(v))
        return doc

    def write(path, text):
        path = Path(path)
        if path.name in (Q.OV_BOOK, Q.OV_RECEIPT):
            try:
                d = json.loads(text)
            except ValueError:
                d = None
            if isinstance(d, dict) and path.name == Q.OV_BOOK:
                d["layout"] = {"mode": "dashboard", "pillars": [dict(p) for p in PILLARS]}
                text = json.dumps(d, ensure_ascii=False)
            elif isinstance(d, dict):
                d.update(layout="dashboard", pillars=[p["name"] for p in PILLARS], superseded_shown_gray=seen["sup"])
                text = json.dumps(d, ensure_ascii=False, indent=1)
        return keep["write"](path, text)

    Q.ov_collect, Q.ov_write, P.VERSION, P.CMF_MIN = collect, write, VERSION, CMF_MIN
    try:
        return P.overview(args, via=via_p, rep=rep)
    finally:
        Q.ov_collect, Q.ov_write, P.VERSION, P.CMF_MIN = keep["collect"], keep["write"], keep["pver"], keep["pmin"]


def help_extra() -> None:
    print("  ── v0202 overview:Dashboard(%s)· 被取代的交接案亮灰 ──" % " · ".join(p["name"] for p in PILLARS))


def selftest() -> int:
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(薄尾 · overview Dashboard + 被取代案;夾具 · 零網路 · 真樹只讀)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0201 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    chk("② 其餘動詞原樣轉交(version → 前版鏈 rc 0)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    P = _prior_module()
    P200 = P._prior_module()
    Q = P200._prior_module()
    tmp = Path(tempfile.mkdtemp(prefix="via_console202_"))
    try:
        reg = tmp / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        hb = {"work_items": [{"id": "R1:a", "case": "a", "state": "SUPERSEDED", "superseded_by": "R9:a2"}, {"id": "R2:a", "case": "a", "state": "SUPERSEDED", "superseded_by": "R9:a2"},
                             {"id": "R1:b", "case": "b", "state": "SUPERSEDED", "superseded_by": "R9:b2"}, {"id": "R2:b", "case": "b", "state": "VERIFIED"},
                             {"id": "R1:c", "case": "c", "state": "VERIFIED"}, {"id": "R1:d", "case": "d", "state": "SUPERSEDED"}, {"id": "R1:x", "state": "PENDING"}]}
        (reg / (HANDOFF_BOOK + "_v0100.json")).write_text(json.dumps(hb), encoding="utf-8")
        sup = superseded_cases(tmp)
        chk("③ 被取代的案:所有工作項都是 SUPERSEDED 才算(還有一項在用的不算);寫出接手的案;沒寫接手的照實說",
            sup == {"a": "a2", "d": "沒寫接手的案"}, sup)
        items = [{"section": SEC_CASE, "id": "a", "lamp": "r", "detail": "不過 · rc 1", "needs": "x"}, {"section": SEC_CASE, "id": "b", "lamp": "r", "detail": "不過"},
                 {"section": SEC_CASE, "id": "c", "lamp": "g", "detail": "過"}, {"section": "① 入口與動詞", "id": "a", "lamp": "r", "detail": "同名但不同區"}]
        n = mark_superseded(items, sup)
        chk("④ 只改 ⑤ 裡被取代的那幾列:亮灰、寫明接手的案、舊收據的話留著;其他列(含別區同名的)不動",
            n == 1 and items[0]["lamp"] == "x" and "接手:a2" in items[0]["detail"] and "不過 · rc 1" in items[0]["detail"] and items[0]["needs"] == ""
            and [i["lamp"] for i in items[1:]] == ["r", "g", "r"] and items[3]["detail"] == "同名但不同區", items)
        empty = Path(tempfile.mkdtemp(prefix="via_console202_e_"))
        chk("⑤ 交接冊不在 / 讀不懂:回空,不炸;一列不改", superseded_cases(empty) == {} and mark_superseded([dict(items[1])], {}) == 0)
        shutil.rmtree(str(empty), ignore_errors=True)
        secs_all = [s for p in PILLARS for s in p["sections"]]
        known = list(Q.OV_SECTIONS) + [P200.PEER_SECTION, P.SEC_PARAM, P.SEC_IFC, P.SEC_OWN]
        chk("⑥ 三欄設定:十五區每一區正好在一欄裡(不多不少不重複);只有一欄收回饋", sorted(secs_all) == sorted(known) and len(set(secs_all)) == len(secs_all) and sum(1 for p in PILLARS if p.get("feedback")) == 1,
            sorted(set(known) ^ set(secs_all)))
        snap = (Q.ov_collect, Q.ov_write, P.VERSION, P.CMF_MIN)
        rep = tmp / "rep"
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep_out, sys.stdout = sys.stdout, nul
            try:
                rc = overview(["--no-open"], via=VIA, rep=rep)
            finally:
                sys.stdout = keep_out
        book = P200.pv_json(rep / "overview" / Q.OV_BOOK) or {}
        rec = P200.pv_json(rep / Q.OV_RECEIPT) or {}
        page = (rep / Q.OV_PAGE).read_text(encoding="utf-8") if (rep / Q.OV_PAGE).is_file() else ""
        real_sup = superseded_cases(VIA)
        cases = {it["id"]: it for it in book.get("items") or [] if it.get("section") == SEC_CASE}
        chk("⑦ 真樹(只讀)出頁到暫存夾:rc 0 · 項目冊帶 layout 三欄 · 前幾版加的鍵都還在(系統順序 · 展開區 · 每個系統一句話)",
            rc == 0 and (book.get("layout") or {}).get("mode") == "dashboard" and [p["name"] for p in book["layout"]["pillars"]] == [p["name"] for p in PILLARS]
            and book.get("systems") == P200.SYS_CARDS and "sys_info" in book and "expand" in book, (rc, list(book)))
        chk("⑧ 真樹:交接冊上被取代的 %d 案在一覽上全是灰並寫明接手;沒被取代的案燈不動" % len(real_sup),
            all(cases[c]["lamp"] == "x" and "已被取代" in cases[c]["detail"] for c in real_sup if c in cases) and rec.get("superseded_shown_gray") == sum(1 for c in real_sup if c in cases)
            and any(v["lamp"] == "g" for v in cases.values()), rec.get("superseded_shown_gray"))
        chk("⑨ 頁面是 Dashboard:貼近兩邊 · 系統訊號 · 三欄的欄名都在 · 矩陣還在", '<div class="wrap dash">' in page and "系統訊號" in page and all((" " + p["name"] + "<") in page for p in PILLARS) and 'id="mx"' in page)
        chk("⑩ 收據:版本是本版 · 記了版面與三欄 · 前幾版的欄位(own_content_lamp · peers · system_info)還在 · 頁燈綠",
            rec.get("version") == VERSION and rec.get("engine") == FAMILY + "_" + VERSION and rec.get("lamp") == "g" and rec.get("layout") == "dashboard"
            and rec.get("pillars") == [p["name"] for p in PILLARS] and all(k in rec for k in ("own_content_lamp", "peers", "system_info")), {k: rec.get(k) for k in ("version", "lamp", "layout", "pillars")})
        chk("⑪ 跑完還原前版模組(讀冊點 · 寫檔點 · 版本);沒留下暫存檔", (Q.ov_collect, Q.ov_write, P.VERSION, P.CMF_MIN) == snap and not list(rep.rglob("*.tmp")))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    seen = []
    real = globals()["forward"]
    globals()["forward"] = lambda x: seen.append(list(x)) or 0
    try:
        m1 = main(["status"])
        m2 = main(["synchronizer", "check"])
    finally:
        globals()["forward"] = real
    chk("⑫ 只有 overview 留在本版;其餘動詞原樣轉交前版", seen == [["status"], ["synchronizer", "check"]] and m1 == 0 and m2 == 0, seen)
    names = [n for n in dir(P) if not n.startswith("_") and callable(getattr(P, n, None))]
    chk("⑬ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("⑭ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 本版自己不寫檔 · 本檔沒有色碼與樣式",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|VDF_|VRN_|VQG_|VAP_)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src)
        and ".write_text(" not in live and "open(" not in live and not re.search(r"#[0-9a-fA-F]{6}\b", live) and "style=" not in live)
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
