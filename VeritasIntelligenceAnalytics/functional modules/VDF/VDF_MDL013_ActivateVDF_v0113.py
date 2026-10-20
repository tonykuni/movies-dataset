#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL013_ActivateVDF v0113 — 薄尾:本輪資料庫流程自動「獨立核對」資料庫清點(db verify),總覽卡顯示核對結果,核對不過不准收尾

操作員令(2026-10-20):「run VDF again to output summary of database(verified 100% correct)」→「好,把檢查器加進 VDF 指令並開 PR 合併」。
疊在 main 的 v0112(跨來源對照結果獨立驗證 · 對照頁 · 收尾判定)之上:v0112 驗的是「跨來源對照結果」,本版驗的是「資料庫清點」本身,兩層互補。
本版(只在本版的一輪裡生效;前版自測照舊):
  ① 資料庫流程:db where → db check → refill → universe xcheck(v0108)之後,多跑 db_verify = 管理員 db verify
     (VDF_SystemManager v0157:不用 db check 的程式,唯讀重推每列每欄比對)。refill 真寫過(--refill-apply 且非 --dry)→ 先重跑一次
     db check(db_check_after_refill)再核對,核對的是補完的庫。核對 FAIL = 紅併進流程;NODATA = 黃。
  ② 清點摘要多 verify(PASS / FAIL · 幾表幾欄 · 差異數;只認核對的就是本輪這份 check —— check_ts 對得上);FAIL → 不准收尾。
  ③ 總覽卡「資料庫清點」多一行「獨立核對:PASS · 65 表 × 5 欄 = 325 欄 · 差異 0」(FAIL 紅字),連 VERIFY_latest.html。本輪 JSON / 頁頭標 v0113。
  ④ 修正(全景定位,不設本輪閘):v0111 db_files 照根序(--db-home > VIA_VDF_DB_HOME > --fetch-home > 本夾 output_hub)把每個根的 .duckdb
     全收,同一個檔名可能收到兩份(資料家一份 + 倉內 output_hub 一份)。對照 / 體檢把兩份都讀,v0112 的獨立驗證器卻按檔名建表 → 後到的
     倉內那份蓋掉本輪的家,回原表逐筆核對錯庫(容器實錄:v0112 自測 Ⓛ V1 不符 15 · V5 不符 2)。本版:同一個檔名只留第一個(本輪的家優先),
     三方看同一份庫。
其餘全照 v0112(→ v0111 → v0110 → v0109 → v0108)。VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

import copy
import html
import importlib.util
import json
import os
import re
import sys
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL013_ActivateVDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0113(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0113(p) < _vnum_v0113(__file__)), key=_vnum_v0113)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():                    # 同 v0102:前版鏈只擋載入那一刻的編譯警告
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)
V0100 = PRIOR.V0100
DBM, FLM = PRIOR.DBM, PRIOR.FLM                    # v0106(清點 / 總覽卡)· v0101(資料庫流程);v0109–v0112 照抄進自己的全域


def __getattr__(name):
    return getattr(PRIOR, name)


LAMP_RANK = ["GREEN", "YELLOW", "GATED", "RED"]
_RUN13 = {"on": False}
_FLOW_DB_V0108 = FLM.flow_db                     # 現在掛著的是 v0108 的(v0109–v0112 沒換)
_DB_INVENTORY_V0108 = DBM.db_inventory
_DB_SECTION_V0108 = DBM.db_section
_DB_FILES_V0111 = PRIOR.db_files                  # v0111 本體(v0112 經它自己的 PRIOR = v0111 模組取用)


def db_files(opt) -> list:
    """同 v0111 根序;同一個檔名只留第一個(本輪的家優先 · 倉內 output_hub 的同名檔不再蓋掉它)。"""
    seen, out = set(), []
    for f in _DB_FILES_V0111(opt):
        k = os.path.normcase(Path(f).name)
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def flow_db(opt, res, gate, log_dir, manager=None, py=None) -> dict:
    """同 v0108 資料庫流程;最後多跑 db verify(refill 真寫過就先重跑一次 db check,核對補完的庫)。"""
    out = _FLOW_DB_V0108(opt, res, gate, log_dir, manager, py)
    if not _RUN13["on"] or out.get("lamp") == "INTERRUPTED" or FLM.STOP.is_set():
        return out
    home = out.get("db_home") or getattr(opt, "db_home", None)
    env = V0100.flow_env(res, "db")
    steps = list(out.get("steps") or [])
    if getattr(opt, "refill_apply", False) and not getattr(opt, "dry", False):
        steps.append(FLM.run_step("db_check_after_refill", ["db", "check"] + (["--home", home] if home else []), env, log_dir, gate, 1800, manager, py))
    steps.append(FLM.run_step("db_verify", ["db", "verify"], env, log_dir, gate, 1800, manager, py))
    worst = max((x.get("lamp") for x in steps), key=lambda x: LAMP_RANK.index(x) if x in LAMP_RANK else 3)
    return dict(out, lamp=worst, steps=steps)


def verify_summary(db: dict) -> dict | None:
    """本輪 check 旁邊的 VERIFY_latest.json;只認核對的就是這份 check(check_ts 對得上)。"""
    j = Path(str(db.get("json") or "")).with_name("VERIFY_latest.json")
    try:
        v = json.loads(j.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not db.get("ts") or v.get("check_ts") != db.get("ts"):
        return None
    return {"lamp": v.get("lamp"), "rows": v.get("rows_compared"), "fields": v.get("fields_compared"),
            "mismatches": len(v.get("mismatches") or []), "page": str(j.with_suffix(".html")), "no_writer": v.get("no_writer"),
            "candidates": sum(1 for cs in (v.get("candidates") or {}).values() if cs)}


def db_inventory(ui_dir: Path | None = None, pre=DBM._UNSET) -> dict:
    db = _DB_INVENTORY_V0108(ui_dir, pre)
    if db.get("lamp") in ("NOT_RUN", "NODATA") or "counts" not in db:
        return db
    v = verify_summary(db)
    if v:
        db["verify"] = v
        if v["lamp"] != "PASS":
            db["closeout"] = False
            db["why"] = ("%s · " % db["why"] if db.get("why") else "") + "獨立核對 %s(差異 %d)→ 清點數字不可信,不能收尾" % (v["lamp"], v["mismatches"])
    return db


def db_section(db: dict | None) -> str:
    s = _DB_SECTION_V0108(db)
    v = (db or {}).get("verify")
    if not s or not v:
        return s
    page = Path(v["page"])
    try:
        href = os.path.relpath(page, V0100.REPORT_DIR)
    except ValueError:
        href = page.as_uri() if page.is_absolute() else str(page)
    ok = v["lamp"] == "PASS"
    line = ('<p>獨立核對:<b style="color:%s">%s</b> · %s 表 × 5 欄 = %s 欄 · 差異 %d · 冊上沒登寫入者 %s 表(程式碼找到候選 %s 表,待確認後登冊)'
            ' · <a href="%s">核對頁(VERIFY_latest.html)</a></p>'
            % ("#1a7f37" if ok else "#cf222e", html.escape(str(v["lamp"])), html.escape(str(v["rows"])), html.escape(str(v["fields"])),
               v["mismatches"], html.escape(str(v.get("no_writer"))), html.escape(str(v.get("candidates"))), html.escape(href)))
    i = s.find('<div class="mut">家')
    return (s[:i] + line + s[i:]) if i >= 0 else s.replace("</section>", line + "</section>", 1)


DBM.db_inventory = db_inventory
DBM.db_section = db_section
FLM.flow_db = flow_db
_DB_FILES_V0111.__globals__["db_files"] = db_files    # 換在 v0111 模組全域:v0111 post_fetch 與 v0112 驗證器(PRIOR.db_files)都走這支
_ACTIVATE_V0112 = PRIOR.activate


def activate(opt, manager: Path | None = None, py: str | None = None, temp: Path | None = None) -> dict:
    """同 v0112 activate;本輪多跑獨立核對,JSON / 頁頭標 v0113,跑完印核對結果。"""
    keep = PRIOR.TAG
    prev = DBM._WRITE_REPORT_V0100

    def _stamp_then_write(c, u=None):
        c["schema"], c["tag"] = "VDF_ActivateVDF_v0113", TAG
        return prev(c, u) if u is not None else prev(c)
    PRIOR.TAG = TAG
    DBM._WRITE_REPORT_V0100 = _stamp_then_write
    _RUN13["on"] = True
    try:
        card = _ACTIVATE_V0112(opt, manager, py, temp)
    finally:
        PRIOR.TAG = keep
        DBM._WRITE_REPORT_V0100 = prev
        _RUN13["on"] = False
    v = (card.get("db") or {}).get("verify")
    if v:
        print("  [獨立核對] %s · %s 表 × 5 欄 = %s 欄 · 差異 %d · 頁 %s" % (v["lamp"], v["rows"], v["fields"], v["mismatches"], v["page"]), flush=True)
    return card


for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def selftest() -> int:
    import shutil
    import tempfile
    import types
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print(f"=== {TAG} · 薄尾自測(資料庫流程獨立核對;沙盒 · 零網路)===")
    calls = []

    def fake_v0108(opt, res, gate, log_dir, manager=None, py=None):
        return {"flow": "db", "lamp": opt.base, "db_home": "/data/home/vdf_database",
                "steps": [{"step": s, "lamp": "GREEN"} for s in ("db_where", "db_check", "db_refill", "db_xcheck")]}

    def fake_step(name, args, env, log_dir, gate=None, timeout=None, manager=None, py=None):
        calls.append((name, list(args)))
        return {"step": name, "args": args, "lamp": {"db_verify": fake_step.verify}.get(name, "GREEN")}
    fake_step.verify = "GREEN"
    global _FLOW_DB_V0108
    keep = (_FLOW_DB_V0108, FLM.run_step, V0100.flow_env)
    _FLOW_DB_V0108, FLM.run_step, V0100.flow_env = fake_v0108, fake_step, lambda res, flow, base_env=None: {"VDF_T_FLOW": flow}
    tmp = Path(tempfile.gettempdir())
    try:
        _RUN13["on"] = True
        r1 = flow_db(types.SimpleNamespace(base="GREEN", dry=False, refill_apply=False), {}, None, tmp)
        r2 = flow_db(types.SimpleNamespace(base="GREEN", dry=False, refill_apply=True), {}, None, tmp)
        r3 = flow_db(types.SimpleNamespace(base="GREEN", dry=True, refill_apply=True), {}, None, tmp)
        fake_step.verify = "RED"
        r4 = flow_db(types.SimpleNamespace(base="GREEN", dry=False, refill_apply=False), {}, None, tmp)
        r5 = flow_db(types.SimpleNamespace(base="INTERRUPTED", dry=False, refill_apply=False), {}, None, tmp)
        _RUN13["on"] = False
        n_before = len(calls)
        r6 = flow_db(types.SimpleNamespace(base="GREEN", dry=False, refill_apply=False), {}, None, tmp)
    finally:
        _RUN13["on"] = False
        _FLOW_DB_V0108, FLM.run_step, V0100.flow_env = keep
    names = lambda r: [s["step"] for s in r["steps"]]       # noqa: E731
    chk("① 本輪資料庫流程最後多 db_verify;refill 真寫過(--refill-apply 且非 --dry)先 db_check_after_refill(帶同一個家)再核對;"
        "核對紅併進流程;中斷 / 不在本版一輪 = 照前版",
        names(r1)[-1] == "db_verify" and r1["lamp"] == "GREEN"
        and names(r2)[-2:] == ["db_check_after_refill", "db_verify"] and ("db_check_after_refill", ["db", "check", "--home", "/data/home/vdf_database"]) in calls
        and "db_check_after_refill" not in names(r3) and r4["lamp"] == "RED" and r5["lamp"] == "INTERRUPTED" and len(r5["steps"]) == 4
        and len(r6["steps"]) == 4 and len(calls) == n_before, (names(r1), names(r2), names(r3), r4["lamp"]))
    td = Path(tempfile.mkdtemp(prefix="vdfact109_"))
    try:
        ui = td / "ui"
        d = DBM.db_report_dir(ui)
        d.mkdir(parents=True, exist_ok=True)
        (d / "DB_CHECK_latest.json").write_text(json.dumps({"lamp": "YELLOW", "ts": "2026-10-20T00:04:17", "tag": "VDF_SystemManager v0156", "rows": [
            {"庫": "a.duckdb", "表": "tw_x", "狀態": "OK", "燈": "GREEN", "列數": 3},
            {"庫": "a.duckdb", "表": "tw_y", "狀態": "過舊", "燈": "YELLOW", "列數": 3}]}, ensure_ascii=False), encoding="utf-8")
        vj = d / "VERIFY_latest.json"
        good = {"lamp": "PASS", "check_ts": "2026-10-20T00:04:17", "rows_compared": 2, "fields_compared": 10, "mismatches": [],
                "no_writer": 1, "candidates": {"tw_x": [{"檔": "VDF_X_v0100.py", "行": 1, "系統": "VDF"}], "tw_z": []}}
        vj.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
        a = db_inventory(ui, pre=None)
        sa = db_section(a)
        vj.write_text(json.dumps(dict(good, lamp="FAIL", mismatches=[{"欄": "列數"}]), ensure_ascii=False), encoding="utf-8")
        b = db_inventory(ui, pre=None)
        sb = db_section(b)
        vj.write_text(json.dumps(dict(good, check_ts="2026-10-19T00:00:00"), ensure_ascii=False), encoding="utf-8")
        c = db_inventory(ui, pre=None)
        chk("② 清點摘要接核對結果(只認 check_ts 對得上的那份):PASS 照可收尾;FAIL → 不准收尾並說明;別輪的核對不算",
            a.get("verify", {}).get("lamp") == "PASS" and a["closeout"] and a["verify"]["candidates"] == 1
            and b["verify"]["lamp"] == "FAIL" and b["closeout"] is False and "獨立核對 FAIL" in b["why"] and "verify" not in c, (a.get("verify"), b.get("why")))
        chk("③ 總覽卡多一行「獨立核對:PASS · 2 表 × 5 欄 = 10 欄 · 差異 0」(連核對頁);FAIL 紅字;沒核對的卡不動",
            "獨立核對:<b style=\"color:#1a7f37\">PASS</b> · 2 表 × 5 欄 = 10 欄 · 差異 0" in sa and "VERIFY_latest.html" in sa
            and "#cf222e\">FAIL</b>" in sb and "差異 1" in sb and "獨立核對" not in db_section(c), sa[-500:])
    finally:
        shutil.rmtree(td, ignore_errors=True)
    td = Path(tempfile.mkdtemp(prefix="vdfact113_"))
    keep_env = os.environ.get("VIA_VDF_DB_HOME")
    try:
        home, other = td / "home", td / "repo_hub"
        for d_, names_ in ((home, ("tw_market.duckdb", "a.duckdb")), (other, ("tw_market.duckdb", "b.duckdb"))):
            (d_ / "sub").mkdir(parents=True)
            for n_ in names_:
                (d_ / "sub" / n_).write_bytes(b"x")
        os.environ["VIA_VDF_DB_HOME"] = str(other)
        o = types.SimpleNamespace(db_home=str(home), fetch_home=None)
        raw, got = _DB_FILES_V0111(o), db_files(o)
        mk = lambda fs: sorted((Path(x).parent.parent.name, Path(x).name) for x in fs)   # noqa: E731
        chk("⑤ db_files 同一個檔名只留第一個(本輪的家優先,另一根的同名檔不蓋掉它;別的檔照收);v0111 模組全域已換上 → v0112 驗證器回原表用同一份庫",
            [n for _, n in mk(raw)].count("tw_market.duckdb") == 2
            and set(mk(got)) >= {("home", "tw_market.duckdb"), ("home", "a.duckdb"), ("repo_hub", "b.duckdb")}
            and ("repo_hub", "tw_market.duckdb") not in mk(got) and len({Path(x).name for x in got}) == len(got)
            and _DB_FILES_V0111.__globals__["db_files"] is db_files, (mk(raw), mk(got)))
    finally:
        if keep_env is None:
            os.environ.pop("VIA_VDF_DB_HOME", None)
        else:
            os.environ["VIA_VDF_DB_HOME"] = keep_env
        shutil.rmtree(td, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("④ 加速器橋 · 網路橋在;不匯入他系統程式;不碰 TA-Lib;同意閘不寫;前版鏈函式換上本版",
        "VIA:ACCEL-BRIDGE" in src and "def _via_net" in src and FLM.flow_db is flow_db and DBM.db_inventory is db_inventory
        and DBM.db_section is db_section
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src))
    print(f"  [計] {TAG} 本版 {p}/{p + f} · {'PASS' if not f else 'FAIL'}")
    if f:
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    # 前版自測驗的是「它自己那版掛著」:跑前版自測時換回 v0108 的三支,跑完換回本版(db_files 修正照留 —— 前版也該用對的庫)
    DBM.db_inventory, DBM.db_section, FLM.flow_db = _DB_INVENTORY_V0108, _DB_SECTION_V0108, _FLOW_DB_V0108
    try:
        rc1 = PRIOR.selftest()
    finally:
        DBM.db_inventory, DBM.db_section, FLM.flow_db = db_inventory, db_section, flow_db
    return rc1 if rc1 in (0, 1, 2, 3) else 1        # 前版紅照實回(同 v0107)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    opt = V0100.parse(argv)
    if opt.verb != "run":
        return V0100.main(argv)
    card = activate(opt)
    return {"GREEN": 0, "YELLOW": 2, "INTERRUPTED": 130}.get(card["lamp"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
