#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0103 — 薄尾:fill 補缺擷取(只抓不足的部分 · 依相依序 · 清單第一步 · 收尾驗收 + 資料庫報告)

操作員 2026-10-03:「Activate every modules to fetch the data to the database to replenish insufficient parts. Test that they work.」
(選擇:工作站一指令,操作員開雙閘後在 PC 跑;容器內離線實測)。
  fill [ids…] [--group G] [--home 夾] [--mode live|fixture] [--max-age-h 20] [--all] [--apply] [--json]
    不加 --apply = 只列計畫(每支為什麼不足),零子行程、零寫檔。
    不足 = 輸出缺 / 空 / 列數不夠 · 輸出比 --max-age-h 舊 · 這個模式沒跑過 · 上次 rc ≠ 0 · 上次比 --max-age-h 舊;--all = 全部重抓。
    缺套件的引擎照實列 ABSENT(附 pip 指令,不代裝),不起子行程。
    只要有任何一支要抓,第一步兩份清單(MDL009 全台股 · MDL010 主動式 ETF)先抓(其他表的開頭五欄取自它們)。
    執行走 v0102 的 run(子行程從冊上尾版起;依 needs 拓撲排序)→ 驗收輸出 → 單引擎監控前 / 後對照 → DuckDB 視圖 / 鍵欄視圖
    → 報告寫 <輸出根>/../_reports/fill_<UTC>.json。
    live 要雙閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT;鎖版網路工具判):閘關 = rc 4、零子行程、零寫檔。AI 永不代設。
rc:0 全部成功(或沒有不足)· 1 有引擎失敗或輸出不合 · 2 參數錯 / 沒有總控入口 · 3 缺核心套件 · 4 雙閘沒開。不碰 TA-Lib。
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


# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
FILL_MAX_AGE_H_V0103 = 20.0
FIRST_STEP_V0103 = ("009", "010")


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.PRIOR                                    # 入口 · 監控 · 資料庫層
BASE = PRIOR.BASE                                      # v0100 本體:閘 · 驗收 · 拓撲序


def __getattr__(name):
    return getattr(PRIOR, name)


def gaps_v0103(book: dict, home: Path, mode: str, max_age_h: float = FILL_MAX_AGE_H_V0103, force: bool = False,
               ids: list | None = None, group: str | None = None) -> list:
    """每支引擎:不足的理由(空 = 足)· 缺套件 · 是否要抓。只讀。"""
    home = Path(home)
    st = {x["id"]: x for x in V0101.status_v0101(book, home)}
    ver = {}
    for v in BASE.verify(book["engines"], home):
        ver.setdefault(v["id"], []).append(v)
    out = []
    for r in book["engines"]:
        if (ids and r["id"] not in ids) or (group and r["group"] != group):
            continue
        s, outs = st[r["id"]], ver.get(r["id"], [])
        why = ["--all"] if force else []
        bad = [v["path"] for v in outs if not v["ok"]]
        if bad:
            why.append(f"輸出缺 / 空 {len(bad)}")
        if outs and not bad and s["output_age_h"] is not None and s["output_age_h"] > max_age_h:
            why.append(f"輸出 {s['output_age_h']} h > {max_age_h:g} h")
        if s["last_rc"] is None or s["mode"] != mode:
            why.append(f"{mode} 模式沒跑過")
        elif s["last_rc"] != 0:
            why.append(f"上次 rc {s['last_rc']}")
        elif s["last_run_h"] is not None and s["last_run_h"] > max_age_h:
            why.append(f"上次 {s['last_run_h']} h 前")
        out.append({"id": r["id"], "mdl": r["mdl"], "group": r["group"], "lamp": s["lamp"], "reasons": why,
                    "absent": s["missing"], "need": bool(why) and not s["missing"]})
    return out


def select_v0103(book: dict, gaps: list) -> list:
    """要抓的列(冊序);有任何一支要抓 → 第一步兩份清單一定先抓。"""
    need = {g["id"] for g in gaps if g["need"]}
    if need:
        need |= {e for e in FIRST_STEP_V0103 if any(r["id"] == e and not V0101.missing_v0101(r) for r in book["engines"])}
    return [r for r in book["engines"] if r["id"] in need]


def fill_v0103(book: dict, home: Path, mode: str = "live", max_age_h: float = FILL_MAX_AGE_H_V0103, force: bool = False,
               ids: list | None = None, group: str | None = None, apply: bool = False, timeout: int | None = None) -> dict:
    home = Path(home)
    before = gaps_v0103(book, home, mode, max_age_h, force, ids, group)
    rows = select_v0103(book, before)
    rep = {"engine": TAG, "mode": mode, "home": str(home), "max_age_h": max_age_h, "apply": apply,
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "before": before,
           "selected": [r["id"] for r in rows], "absent": [g for g in before if g["absent"]], "runs": [], "verify": [], "after": [], "db": None}
    if not apply or not rows:
        rep["rc"] = 0
        return rep
    if mode == "live" and not BASE.gate_open():
        rep["rc"], rep["gated"] = 4, True
        return rep
    home.mkdir(parents=True, exist_ok=True)
    rep["runs"] = PRIOR.run_v0102(rows, mode, home, logs=home.parent / "_logs", timeout=timeout or BASE.CHILD_TIMEOUT_S)   # 子行程從 v0102 起(冊 v0102)
    rep["verify"] = BASE.verify(rows, home)
    rep["after"] = gaps_v0103(book, home, mode, max_age_h, False, ids, group)
    try:
        rep["db"] = V0101.db_v0101(home)
    except ImportError:
        rep["db"] = {"error": "ABSENT:duckdb"}
    except Exception as e:  # 資料庫層照實回報,不吞
        rep["db"] = {"error": f"{type(e).__name__}: {str(e)[:120]}"}
    rep["rc"] = 0 if all(x["rc"] == 0 for x in rep["runs"]) and all(v["ok"] for v in rep["verify"]) else 1
    rd = home.parent / "_reports"
    rd.mkdir(parents=True, exist_ok=True)
    rep["report"] = str(rd / f"fill_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    Path(rep["report"]).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return rep


def _print_fill_v0103(rep: dict) -> None:
    head = "計畫(不執行;加 --apply 才抓)" if not rep["apply"] else "執行"
    print(f"[VDF 擷取系統 · 補缺 {head}] 模式 {rep['mode']} · 輸出根 {rep['home']} · 新鮮門檻 {rep['max_age_h']:g} h")
    for g in rep["before"]:
        tag = "ABSENT" if g["absent"] else ("抓" if g["id"] in rep["selected"] else "足")
        why = ("缺 " + ",".join(g["absent"])) if g["absent"] else (" · ".join(g["reasons"]) or "新鮮")
        print(f"  [{tag:6}] {g['id']:7} {g['mdl'][:30]:30} {g['group']:10} {why}")
    if rep["absent"]:
        pk = sorted({p for g in rep["absent"] for p in g["absent"]})
        print(f"  [缺套件] {len(rep['absent'])} 支不起子行程 —— 自己裝(AI 不代裝):py -3 -m pip install {' '.join(pk)}")
    if rep.get("gated"):
        print("[GATED] 雙閘沒開 —— 零子行程、零出網、零寫檔(不是壞掉)。本視窗開閘(操作員的手):"
              "$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'")
        return
    if not rep["apply"]:
        print(f"  要抓 {len(rep['selected'])} 支:{' '.join(rep['selected']) or '—(全部新鮮)'}")
        return
    if not rep["selected"]:
        print("  全部新鮮 —— 沒有要抓的(零子行程)")
        return
    for x in rep["runs"]:
        lab = {0: "OK", 2: "NODATA", 3: "ABSENT", 4: "GATED"}.get(x["rc"], "rc" + str(x["rc"]))
        print(f"  [{lab:6}] {x['mdl'][:34]:34} {x['sec']:7.1f}s · {(x.get('tail') or [''])[-1][:90]}")
    ok_v = sum(v["ok"] for v in rep["verify"])
    print(f"  [驗收] 輸出 {ok_v}/{len(rep['verify'])} 檔合格")
    still = [g["id"] for g in rep["after"] if g["need"]]
    print(f"  [補後] 仍不足 {len(still)} 支" + (f":{' '.join(still)}" if still else ""))
    d = rep["db"] or {}
    print(f"  [資料庫] 視圖 {d.get('views')} · 鍵欄視圖 {len(d.get('keyed_views') or [])} · 主清單 {d.get('master_list')}"
          + (f" · {d['error']}" if d.get("error") else ""))
    print(f"  [報告] {rep.get('report')}")
    print(f"[計] 補缺 {'PASS' if rep['rc'] == 0 else 'FAIL'} · 抓 {len(rep['runs'])} 支 · rc 0 {sum(x['rc'] == 0 for x in rep['runs'])}")


def _arg_v0103(rest: list, flag: str):
    return rest[rest.index(flag) + 1] if flag in rest and rest.index(flag) + 1 < len(rest) else None


def fill_main_v0103(rest: list) -> int:
    book = V0101.load_book_v0101()
    known = {r["id"] for r in book["engines"]}
    vals = {_arg_v0103(rest, f) for f in ("--home", "--mode", "--max-age-h", "--group")}
    ids = [a for a in rest if not a.startswith("--") and a not in vals]
    bad = [i for i in ids if i not in known]
    mode = _arg_v0103(rest, "--mode") or "live"
    grp = _arg_v0103(rest, "--group")
    try:
        age = float(_arg_v0103(rest, "--max-age-h") or FILL_MAX_AGE_H_V0103)
    except ValueError:
        age = -1.0
    unknown = [a for a in rest if a.startswith("--") and a not in ("--home", "--mode", "--max-age-h", "--group", "--all", "--apply", "--json")]
    if bad or unknown or mode not in BASE.MODES or age < 0 or (grp and grp not in V0101.GROUPS_V0101):
        print(f"[拒跑] {TAG}:fill 參數不對(冊上沒有 {bad} · 不認得 {unknown} · --mode 只收 {'/'.join(BASE.MODES)} · "
              f"--group 只收 {'/'.join(V0101.GROUPS_V0101)} · --max-age-h 要 ≥ 0)")
        return 2
    if "--apply" in rest:
        core = [m for m in V0101.CORE_PACKAGES_V0101 if importlib.util.find_spec(m) is None]
        if core:
            print(f"[ABSENT] {TAG}:本直譯器缺核心套件 {', '.join(core)} —— 不代裝;自己裝:py -3 -m pip install {' '.join(core)}")
            return 3
    rep = fill_v0103(book, BASE.home_dir(_arg_v0103(rest, "--home")), mode, age, "--all" in rest, ids, grp, "--apply" in rest)
    if "--json" in rest:
        print(json.dumps({"vdf_fetch_fill": rep}, ensure_ascii=False, default=str))
    else:
        _print_fill_v0103(rep)
    return rep["rc"]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] == ["fill"]:
        if not V0101.entry_ok_v0101():
            print(f"[VDF_MDL008] 拒絕。VDF 擷取系統由 VDF System Manager 總控:"
                  f"python \"functional modules/VDF/VDF_SystemManager_v0128.py\" fetch {' '.join(args)}(VCGC 也可呼叫)")
            return 2
        with V0101._approved_call_v0101():
            return fill_main_v0103(args[1:])
    if args[:1] == ["_child"]:
        return PRIOR.main(args)
    rc = PRIOR.main(args)
    if args[:1] in ([], ["list"]) and "--json" not in args and rc in (0, 1):
        print("  補缺:fetch fill(計畫)→ fetch fill --apply(live 要雙閘)· 只抓不足的部分")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc0 = PRIOR.selftest()
    print(f"=== {TAG} · 薄尾自測(fill 補缺:只抓不足 · 清單第一步 · 雙閘 · fixture 離線網)===")
    chk("① v0102 自測過(冊 v0102 · MDL009 v0101 · 子行程)", rc0 == 0, f"rc {rc0}")
    book = V0101.load_book_v0101()
    ids = ["009", "010", "001u", "004", "007"]
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "dict"
        plan = fill_v0103(book, home, "live")
        absent = {g["id"] for g in plan["before"] if g["absent"]}
        chk("② 空輸出根的計畫:能跑的全部要抓(理由:沒跑過 / 輸出缺)· 缺套件的照列 ABSENT 不抓 · 零寫檔",
            set(plan["selected"]) == {r["id"] for r in book["engines"]} - absent and plan["rc"] == 0 and not home.exists(),
            f"要抓 {len(plan['selected'])} · ABSENT {sorted(absent)}")
        saved = {k: os.environ.pop(k, None) for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
        keep_gate = BASE.gate_open
        try:
            BASE.gate_open = lambda: False
            g = fill_v0103(book, home, "live", ids=ids, apply=True)
        finally:
            BASE.gate_open = keep_gate
            for k, v in saved.items():
                if v is not None:
                    os.environ[k] = v
        chk("③ live 雙閘沒開 → rc 4 · 零子行程 · 零寫檔(不是壞掉)", g["rc"] == 4 and not g["runs"] and not Path(tmp, "_logs").exists() and not home.exists())
        r1 = fill_v0103(book, home, "fixture", ids=ids, apply=True, timeout=900)
        chk("④ fixture 補缺:5 支全抓 · rc 0 · 輸出全合格 · 資料庫有主清單 · 報告寫出",
            r1["rc"] == 0 and r1["selected"] == ids and len(r1["runs"]) == 5 and all(v["ok"] for v in r1["verify"])
            and (r1["db"] or {}).get("master_list") and Path(r1["report"]).is_file(), [(x["id"], x["rc"]) for x in r1["runs"]])
        r2 = fill_v0103(book, home, "fixture", ids=ids, apply=True)
        chk("⑤ 再補一次:全部新鮮 → 零子行程(省下載)", r2["rc"] == 0 and not r2["selected"] and not r2["runs"])
        old = time.time() - 48 * 3600
        for o in next(r for r in book["engines"] if r["id"] == "004")["outputs"]:
            os.utime(home / o["path"], (old, old))
        r3 = fill_v0103(book, home, "fixture", ids=ids, apply=True, timeout=900)
        chk("⑥ 只有 MDL004 的輸出變舊 → 只抓 004 + 第一步兩份清單 · 其他不動", r3["rc"] == 0 and r3["selected"] == ["009", "010", "004"],
            r3["selected"])
        rl = fill_v0103(book, home, "live", ids=ids)
        chk("⑦ fixture 跑過不算 live:live 計畫仍要抓(理由「live 模式沒跑過」)",
            rl["selected"] == ids and all("live 模式沒跑過" in g["reasons"] for g in rl["before"]))
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VDFSM", "VIA_FROM_VCGC")}
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc_x = main(["fill"])
            os.environ["VIA_FROM_VDFSM"] = "YES"
            rc_bad = main(["fill", "--mode", "nope"])
            rc_plan = main(["fill", "009", "--home", str(Path(tempfile.gettempdir()) / "via_fill_plan_probe")])
            leaked = "VIA_FROM_VCGC" in os.environ
    finally:
        os.environ.pop("VIA_FROM_VDFSM", None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    chk("⑧ 沒有總控入口 → rc 2;參數錯 → rc 2;計畫 rc 0;核准只在呼叫內", rc_x == 2 and rc_bad == 2 and rc_plan == 0 and not leaked
        and "VDF System Manager" in buf.getvalue(), (rc_x, rc_bad, rc_plan))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · v0102 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
