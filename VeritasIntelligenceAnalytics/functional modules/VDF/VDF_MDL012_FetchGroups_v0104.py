#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL012_FetchGroups v0104 — 薄尾:+ refill 動詞(無資料族群依 FRED → 政府單位 → AkShare 分層補擷取)

操作員 2026-10-05:「FOR THOSE NO DATA USE FRED KEY AND OTHER GOVERNMENT UNIT AND AKSHARE TO FETCH」。
  · 路線在冊 VDF_FetchGroups_SSOT_v0102(尾版)每個族群的 refill 分層:provider(FRED · GOV · AKSHARE · YFINANCE · OTHER)· engines · key。
    只列寫進同一張表的引擎(不同表不混,免得燈假綠)。
  · refill [--groups X,Y] [--as-of D] [--home H] [--apply] [--timeout S] [--json]
      1. 同一 as-of 測全部(或指定)族群:整組 NODATA 或部分來源 NODATA 才補;
      2. 逐層:要鑰的層先查鑰(FRED_API_KEY 環境變數或輸出根 .fred_api_key;只查有沒有,不印)→ 沒鑰 = SKIP 照記;
      3. --apply 才真跑(要本視窗 VIA_NET_CONSENT=YES + VIA_SCRAPE_CONSENT;本檔永不代設;沒開 = GATED rc 4,零子行程);
         每層跑完重測該族群,有資料就停(FILLED · 記哪一層);全部層都試過仍無 = STILL_NODATA 照實報;
      4. 報告 <輸出根上層>/_reports/refill_latest.json(+ 時間戳檔);目錄庫 fg_runs 記一列(mode = refill)。
    沒給 --apply = 只列計畫(零子行程、零寫檔)。
其餘動詞全照 v0103 / v0102 / v0101 / v0100。
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
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import copy
import importlib.util
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


V0100 = PRIOR.V0100
TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
for _m in (PRIOR, PRIOR.PRIOR, PRIOR.V0101, V0100):
    _m.TAG = TAG
KEY_FILE = ".fred_api_key"

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------- 判定 ----------
def needs_refill(summary: dict) -> int:
    """回缺的來源數:整組 NODATA = 全部來源;部分 NODATA = 那幾個;沒缺 = 0。"""
    if not summary:
        return 0
    if summary.get("worst") == "NODATA":
        return int(summary.get("sources") or 1)
    return int((summary.get("states") or {}).get("NODATA", 0))


def key_present(name: str | None, home: Path) -> bool:
    """只查鑰在不在(環境變數或輸出根的鑰檔);永不讀出、永不印。"""
    if not name:
        return True
    if os.environ.get(name):
        return True
    return name == "FRED_API_KEY" and any((p / KEY_FILE).is_file() for p in (home, home / "output_hub" / "mega"))


def route_of(book: dict, gid: str) -> list:
    g = V0100.group_of(book, gid)
    tiers = g.get("refill")
    if tiers:
        return [dict(t) for t in tiers]
    return [{"provider": "SELF", "label": "冊上沒寫 refill → 用族群自己的引擎重跑", "engines": list(g.get("engines") or [])}]


def status_of(book, gids, as_of, home, ledger, sel, matrix) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        rows = V0100.monitor(book, gids, as_of, home, ledger, sel, matrix)
    return V0100.group_summary(rows)


def plan_refill(book: dict, gids: list, summ: dict, home: Path) -> list:
    """每個要補的族群一列:缺幾個來源 · 分層(每層標鑰在不在)。"""
    out = []
    for gid in gids:
        miss = needs_refill(summ.get(gid, {}))
        if not miss:
            continue
        tiers = route_of(book, gid)
        for t in tiers:
            t["key_ok"] = key_present(t.get("key"), home)
        out.append({"group": gid, "zh": V0100.group_of(book, gid).get("zh"), "missing": miss, "tiers": tiers})
    return out


def _tier_rows(book, fb, gid, engines, as_of, sel_path) -> list:
    """把族群的引擎換成這一層的引擎,其餘(起始日 · 成員 · as-of 參數)照族群原本的算法。"""
    bk = copy.deepcopy(book)
    for g in bk["groups"]:
        if g["id"] == gid:
            g["engines"] = list(engines)
    rows = V0100.plan_rows(bk, fb, [gid], as_of, sel_path)
    return [r for r in rows if not r.get("missing")], [r["id"] for r in rows if r.get("missing")]


def _runner():
    m, mp = V0100._load_mdl008()
    return (getattr(m, "run_v0107", None) or m.BASE.run), mp


RUNNER = None   # 自測可換成假跑者


def execute(book, fb, plan, as_of, home, ledger, sel, matrix, timeout) -> list:
    run, mp = RUNNER or _runner()
    work = home.parent / "_fetch_groups"
    results = []
    for item in plan:
        gid, steps, final = item["group"], [], "STILL_NODATA"
        g = V0100.group_of(book, gid)
        sel_path = None
        if g["membership"] == "EDITABLE_SELECTION":
            work.mkdir(parents=True, exist_ok=True)
            sel_path = work / f"selection_refill_{gid}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
            sel_path.write_text(json.dumps(V0100.effective_selection(book, [gid], ledger, sel), ensure_ascii=False, indent=1), encoding="utf-8")
        for t in item["tiers"]:
            step = {"provider": t["provider"], "label": t.get("label"), "engines": t.get("engines")}
            if not t.get("key_ok", True):
                step.update(state="SKIP", note=f"缺 {t.get('key')}(環境變數或輸出根 {KEY_FILE})")
                steps.append(step)
                continue
            rows, miss = _tier_rows(book, fb, gid, t.get("engines") or [], as_of, str(sel_path) if sel_path else None)
            if not rows:
                step.update(state="SKIP", note=f"擷取冊沒有這些引擎 {miss}")
                steps.append(step)
                continue
            t0 = time.time()
            res = run(rows, "live", home, logs=home.parent / "_logs", timeout=timeout)
            step["rc"] = {x["id"]: x.get("rc") for x in res}
            step["sec"] = round(time.time() - t0, 1)
            after = status_of(book, [gid], as_of, home, ledger, sel, matrix).get(gid, {})
            left = needs_refill(after)
            step.update(state="FILLED" if left == 0 else ("PARTIAL" if left < item["missing"] else "STILL_NODATA"),
                        rows_asof=after.get("rows_asof"), max_date=after.get("max_date"), worst=after.get("worst"))
            steps.append(step)
            if left == 0:
                final = "FILLED"
                break
            if left < item["missing"]:
                final = "PARTIAL"
        results.append({"group": gid, "zh": item["zh"], "missing_before": item["missing"], "result": final, "steps": steps})
    return results


def _write_report(home: Path, body: dict) -> Path:
    rep = home.parent / "_reports"
    rep.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    txt = json.dumps(body, ensure_ascii=False, indent=1, default=str)
    (rep / f"refill_{stamp}.json").write_text(txt, encoding="utf-8")
    (rep / "refill_latest.json").write_text(txt, encoding="utf-8")
    return rep / "refill_latest.json"


def _record_run(home: Path, as_of: str, gids: list, results: list, started) -> None:
    con = V0100._con_catalog(home)
    try:
        rc = {r["group"]: r["result"] for r in results}
        run_id = f"FG_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        con.execute("INSERT INTO fg_runs VALUES (?,?,?,?,?,?,?,?)",
                    [run_id, started, datetime.now(), as_of, "refill", ",".join(gids), ",".join(rc), json.dumps(rc, ensure_ascii=False)])
    finally:
        con.close()


def cmd_refill(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="refill", description="無資料族群分層補擷取(FRED → 政府單位 → AkShare)")
    ap.add_argument("--groups"); ap.add_argument("--as-of", dest="as_of"); ap.add_argument("--home")
    ap.add_argument("--apply", action="store_true"); ap.add_argument("--timeout", type=int, default=1800); ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = V0100._ctx(a)
    gids = V0100._gids(book, a.groups)
    as_of = V0100.resolve_asof(a.as_of or V0100.current_asof_setting(book, ledger))
    summ = status_of(book, gids, as_of, home, ledger, sel, matrix)
    plan = plan_refill(book, gids, summ, home)
    print(f"[refill] {TAG} · as-of {as_of} · 輸出根 {home} · 測 {len(gids)} 族群 · 要補 {len(plan)}")
    for p in plan:
        print(f"  {p['group']:<14} {p['zh']} · 缺 {p['missing']} 個來源")
        for i, t in enumerate(p["tiers"], 1):
            k = "" if not t.get("key") else (f" · 鑰 {t['key']} " + ("在" if t["key_ok"] else "缺 → 這層會 SKIP"))
            print(f"     {i}. {t['provider']:<8} {t.get('label', '')} · 引擎 {','.join(t.get('engines') or [])}{k}")
    if not plan:
        print("[refill] 沒有無資料的族群 —— 不用補")
        return 0
    if not a.apply:
        print("[refill] 只列計畫(零子行程、零寫檔)。要真跑:本視窗開雙閘後加 --apply")
        return 0
    if not V0100.gates_open():
        print("[GATED] 雙閘沒開 —— 零子行程、零出網、零寫檔。本視窗開閘(操作員的手,本檔永不代設):VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES")
        return 4
    started = datetime.now()
    results = execute(book, fb, plan, as_of, home, ledger, sel, matrix, a.timeout)
    body = {"tool": TAG, "as_of": as_of, "home": str(home), "started": started, "finished": datetime.now(), "results": results}
    path = _write_report(home, body)
    _record_run(home, as_of, [p["group"] for p in plan], results, started)
    n = {k: sum(1 for r in results if r["result"] == k) for k in ("FILLED", "PARTIAL", "STILL_NODATA")}
    for r in results:
        last = r["steps"][-1] if r["steps"] else {}
        print(f"  {r['group']:<14} {r['result']:<12} " + " → ".join(f"{s['provider']}:{s['state']}" for s in r["steps"])
              + (f" · 最晚 {last.get('max_date')}" if last.get("max_date") else ""))
    print(f"[refill] 補到 {n['FILLED']} · 部分 {n['PARTIAL']} · 仍無 {n['STILL_NODATA']} · 報告 {path}")
    if a.json:
        print(json.dumps(body, ensure_ascii=False, default=str))
    return 0 if n["STILL_NODATA"] == 0 else 1


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    keep_glob = V0100.BOOK_GLOB
    V0100.BOOK_GLOB = "VDF_FetchGroups_SSOT_v0101.json"          # 前版斷言寫的是冊 v0101 → 釘住再跑
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            prior_rc = PRIOR.selftest()
    finally:
        V0100.BOOK_GLOB = keep_glob
        for _m in (PRIOR, PRIOR.PRIOR, PRIOR.V0101, V0100):
            _m.TAG = TAG
    chk("① v0103 自測照過(連 v0102 / v0101 / v0100 鏈;釘冊 v0101)", prior_rc == 0, buf.getvalue()[-300:])
    book = V0100.load_book()
    chk("② 冊尾版 v0102:14 族群都有 refill 分層;US_MACRO 三層都是 FRED 要 FRED_API_KEY;AkShare 族群走 011d;台股走政府",
        Path(book["_path"]).name == "VDF_FetchGroups_SSOT_v0102.json" and all(g.get("refill") for g in book["groups"])
        and all(t["provider"] == "FRED" and t.get("key") == "FRED_API_KEY" for t in V0100.group_of(book, "US_MACRO")["refill"])
        and V0100.group_of(book, "CN_NBS")["refill"][0]["engines"] == ["011d"]
        and V0100.group_of(book, "TW_INDEX")["refill"][0]["provider"] == "GOV", Path(book.get("_path", "")).name)
    chk("③ 判定:整組 NODATA = 全部來源;部分 NODATA = 那幾個;綠 / 黃 = 0",
        needs_refill({"worst": "NODATA", "sources": 2}) == 2 and needs_refill({"worst": "YELLOW", "states": {"YELLOW": 1, "NODATA": 1}}) == 1
        and needs_refill({"worst": "GREEN", "states": {"GREEN": 2}}) == 0 and needs_refill({}) == 0)
    tmp = Path(tempfile.mkdtemp(prefix="mdl012v4_"))
    keep_env = {k: os.environ.get(k) for k in ("FRED_API_KEY", "VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    global RUNNER
    try:
        home = tmp / "mega"
        home.mkdir()
        os.environ.pop("FRED_API_KEY", None)
        chk("④ 鑰只查在不在:沒環境變數也沒鑰檔 = 缺;輸出根有 .fred_api_key = 在(不讀內容)",
            not key_present("FRED_API_KEY", home) and key_present(None, home)
            and ((home / KEY_FILE).write_text("x", encoding="utf-8") or key_present("FRED_API_KEY", home)))
        (home / KEY_FILE).unlink()
        fb = V0100._json(V0100.tail(V0100.FETCH_GLOB))
        ledger, (sel, matrix, _, _) = PRIOR._ledger(), V0100.load_inputs(book)
        summ = {"US_MACRO": {"worst": "NODATA", "sources": 1}, "TW_INDEX": {"worst": "GREEN", "states": {"GREEN": 1}}}
        plan = plan_refill(book, ["US_MACRO", "TW_INDEX"], summ, home)
        chk("⑤ 計畫只含要補的族群;FRED 層沒鑰標 key_ok False", [p["group"] for p in plan] == ["US_MACRO"]
            and all(t["key_ok"] is False for t in plan[0]["tiers"]), plan)
        calls = []

        def fake_run(rows, mode, home_, logs=None, timeout=None):
            calls.append([r["id"] for r in rows])
            if "e113" in calls[-1]:     # 第二層才補到:寫進族群自己的表
                d = V0100._duck().connect(str(home_ / "vdf_global_market.duckdb"))
                d.execute("CREATE TABLE IF NOT EXISTS us_macro(date DATE, series VARCHAR, value DOUBLE)")
                d.execute("INSERT INTO us_macro VALUES (current_date - 1, 'DGS10', 4.1)")
                d.close()
            return [{"id": r["id"], "rc": 0} for r in rows]

        RUNNER = (fake_run, Path("fake"))
        os.environ["FRED_API_KEY"] = "selftest-not-a-key"
        plan = plan_refill(book, ["US_MACRO"], {"US_MACRO": {"worst": "NODATA", "sources": 1}}, home)
        out = execute(book, fb, plan, V0100.resolve_asof("latest"), home, ledger, sel, matrix, 60)
        st = [s["state"] for s in out[0]["steps"]]
        chk("⑥ 分層照序跑、每層重測、補到就停:e074 仍無 → e113 補到 = FILLED;第三層不跑", out[0]["result"] == "FILLED"
            and st == ["STILL_NODATA", "FILLED"] and [c[0] for c in calls if c] == ["e074", "e113"], (out, calls))
        os.environ.pop("FRED_API_KEY", None)
        calls.clear()
        plan = plan_refill(book, ["US_MACRO"], {"US_MACRO": {"worst": "NODATA", "sources": 1}}, home)
        out = execute(book, fb, plan, V0100.resolve_asof("latest"), home, ledger, sel, matrix, 60)
        chk("⑦ 沒鑰:FRED 三層全 SKIP、零子行程、結果 STILL_NODATA(不假裝補到)",
            out[0]["result"] == "STILL_NODATA" and not calls and all(s["state"] == "SKIP" for s in out[0]["steps"]), out)
        os.environ.pop("VIA_NET_CONSENT", None)
        os.environ.pop("VIA_SCRAPE_CONSENT", None)
        RUNNER = (lambda *a, **k: calls.append("RAN") or [], Path("fake"))
        b2 = io.StringIO()
        with contextlib.redirect_stdout(b2):
            rc = cmd_refill(["--home", str(tmp / "empty" / "mega"), "--groups", "US_MACRO", "--apply"])
        chk("⑧ --apply 沒開雙閘 = GATED rc 4、零子行程、零寫報告", rc == 4 and not calls and "GATED" in b2.getvalue()
            and not (tmp / "empty" / "_reports").exists(), b2.getvalue()[-200:])
        b3 = io.StringIO()
        with contextlib.redirect_stdout(b3):
            rc = cmd_refill(["--home", str(tmp / "empty" / "mega"), "--groups", "US_MACRO,CN_NBS"])
        chk("⑨ 沒 --apply = 只列計畫(兩族群 · FRED 層標鑰缺)rc 0、零寫檔", rc == 0 and "只列計畫" in b3.getvalue()
            and "US_MACRO" in b3.getvalue() and "CN_NBS" in b3.getvalue() and "FRED_API_KEY 缺" in b3.getvalue()
            and not (tmp / "empty" / "_reports").exists(), b3.getvalue()[-300:])
    finally:
        RUNNER = None
        for k, v in keep_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0103 鏈 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "refill":
        return cmd_refill(argv[1:])
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
