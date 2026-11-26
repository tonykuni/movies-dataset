#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_HostBoot v0105 — 薄尾(v0100–v0104 一字不動):新動詞 lakeall(桌機一行:VDF 全族群擷取 → 2018-01-01 起入湖 → 輸出驗證)

操作員 2026-11-26:「整合後再次測試完成啟動VCGC/VDF輸出結果 VDF輸出2018-01-01到最新的數據」。
前版 lake 固定 --skip-fetch(不出網);vdf3 --live 只抓「最新三期」,補不回停在 9 月 / 6 月的表。
本版 lakeall 暫切 origin/<分支>(同 lake / vdfcheck,一定切回;已追蹤檔有改動 = 停不碰),依序跑 VDF 自己的動詞:
  ① VDF_ENG239_ParquetLakeBuild 尾版 --selftest
  ② VDF_ENG239 run --all --jobs <N>:⓪ VDF_MDL012_FetchGroups 全族群擷取(依水位只補缺)→ ① 歷史回補 → ② 入湖 → ③ 管家;
     起日讀 VDF DataPlane 冊(操作員裁定 2018-01-01),到今天
  ③ VDF 管理器尾版 three inventory · distill · reconcile
  ④ VDF 管理器尾版 db check · db verify · monitor --json(輸出驗證)
同意閘:出網要「操作員在自己的視窗」開兩道(VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=YES);本檔只檢查、不代設。
  沒開 = RED rc 1、一步都不跑(不冒充已抓;只要湖用現有資料請用 lake)。
收據(資料邊界:只推結構):DB_CHECK · VERIFY · MONITOR 照 v0104 的投影;湖狀態只推每個 view 的布林
  (有沒有日期欄 · 是否從 2018 年初起 · 是否 7 天內新)與分片數,不推列數與日期;每步主控台只留本機 <夾>_local。
用法:python VIA_HostBoot_v0105.py --repo <倉> lakeall [--branch B] [--jobs 3] [--push]
其餘動詞(fnc · bak · vdf · vdfp · vdf3 · fin5y · hydra · lake · vdfcheck)全部照前版。不用 TA-Lib · 不設同意閘 · 本檔零外呼。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    import os as _sa_os
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.insert(0, _sa_Path(_sa_os.environ["VIA_REPO"]).resolve() / "VeritasIntelligenceAnalytics")
    for _sa_p in _sa_roots:
        _sa_hit = None
        while True:
            for _sa_c in (_sa_p, _sa_p / "VeritasIntelligenceAnalytics"):
                if (_sa_c / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit or _sa_p.parent == _sa_p:
                break
            _sa_p = _sa_p.parent
        if _sa_hit:
            _sa_sys.path.insert(0, str(_sa_hit / "supportive modules"))
            break
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0105"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                   # v0101:on_branch · newest · push_receipts · say · VIA_REL
VERBS = tuple(PRIOR.VERBS) + ("lakeall",)
VIA_NET_TOOL_PATH = getattr(PRIOR, "VIA_NET_TOOL_PATH", None)
CONSENT = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")
START_BY = "2018-01-10"                             # 「從 2018 年初起」的判準(DataPlane 起日 2018-01-01,頭幾天可能是假日)
FRESH_DAYS = 7


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    BASE.say(msg)


def lakeall_steps(via: Path, live: bool, extra: list) -> list:
    eng = via / "functional modules" / "VDF" / "engine"
    lb = BASE.newest(eng, "VDF_ENG239_ParquetLakeBuild_v*.py")
    vm = BASE.newest(via / "functional modules" / "VDF", "VDF_SystemManager_v*.py")
    jobs = extra[extra.index("--jobs") + 1] if "--jobs" in extra and extra.index("--jobs") + 1 < len(extra) else "3"
    return ([[str(lb), "--selftest"], [str(lb), "run", "--all", "--jobs", str(jobs)]]
            + [[str(vm), "three", v] for v in ("inventory", "distill", "reconcile")]
            + [[str(vm), "db", "check"], [str(vm), "db", "verify"], [str(vm), "monitor", "--lanes", "3", "--timeout", "400", "--json"]])


def project_lake(d: dict) -> dict:
    """湖狀態只留結構:view 名 · 有沒有日期欄 · 是否從 2018 年初起 · 是否 7 天內新 · 分片數(不留列數與日期)。"""
    views = []
    for t in d.get("tables") or []:
        if not isinstance(t, dict):
            continue
        lo, lag = t.get("min_date"), t.get("lag_days")
        views.append({"view": t.get("view"), "has_date": bool(t.get("date_col")),
                      "covers_2018": bool(lo) and str(lo) <= START_BY,
                      "fresh_7d": isinstance(lag, int) and lag <= FRESH_DAYS, "parts": t.get("parts")})
    dated = [v for v in views if v["has_date"]]
    return {"engine": d.get("engine"), "at": d.get("at"), "views_n": len(views), "dated_n": len(dated),
            "covers_2018_n": sum(v["covers_2018"] for v in dated), "fresh_7d_n": sum(v["fresh_7d"] for v in dated), "views": views}


def coverage_rc(pj: dict) -> tuple:
    """要求範圍(2018-01-01 起 · 到最新):有日期的 view 任一不是從 2018 年初起或不是 7 天內新 → 至少黃,逐項點名(不只看收據在不在)。"""
    dated = [v for v in pj.get("views") or [] if v.get("has_date")]
    short = [v["view"] for v in dated if not v.get("covers_2018")]
    stale = [v["view"] for v in dated if not v.get("fresh_7d")]
    if not dated:
        return 2, short, stale                        # 一張帶日期的表都沒有 = 沒交出要的資料
    return (2 if (short or stale) else 0), short, stale


def run_lakeall(rest: list, repo: Path, out: Path, env: dict) -> int:
    missing = [k for k in CONSENT if env.get(k) != "YES"]
    if missing:
        say(f"[RED] lakeall 要出網擷取:兩道同意閘由你在自己的視窗開(本工具不代設);還沒開:{' · '.join(missing)}。"
            "只要用庫內現有資料建湖請改用 lake。")
        return 1
    if "--live" in rest:
        rest = [x for x in rest if x != "--live"]
    t0 = time.time()
    env = dict(env)
    env[PRIOR.ENTRY_FLAG[0]] = PRIOR.ENTRY_FLAG[1]  # VDF db 動詞收的入口標記(只放子行程環境)
    rc = BASE.on_branch(rest, repo, out, env, "lakeall", lakeall_steps, ("vdf_three",))
    kept = PRIOR.keep_local(out, "lakeall")
    if kept:
        say(f"主控台 {len(kept)} 檔只留本機 → {out.name}_local(不推送)")
    via = repo / BASE.VIA_REL
    got = PRIOR.collect_receipts(via, out, t0)
    st = via / "VIA_Reports" / "vdf_lake" / "LAKE_STATUS_latest.json"
    if st.is_file() and st.stat().st_mtime >= t0 - 2:
        try:
            pj = project_lake(json.loads(st.read_text(encoding="utf-8")))
            (out / "lakeall_LAKE_STATUS_projection.json").write_text(json.dumps(pj, ensure_ascii=False, indent=1), encoding="utf-8")
            got.append("lakeall_LAKE_STATUS_projection.json")
            say(f"湖 · view {pj['views_n']} · 有日期 {pj['dated_n']} · 從 2018 年初起 {pj['covers_2018_n']} · 7 天內新 {pj['fresh_7d_n']}")
            crc, short, stale = coverage_rc(pj)
            for name, lst in (("沒從 2018 年初起", short), ("不是 7 天內新", stale)):
                if lst:
                    say(f"  [黃] {name} {len(lst)} 張:" + " · ".join(lst[:12]) + (" …" if len(lst) > 12 else ""))
            rc = PRIOR.worse(rc, crc)               # 範圍沒達成 = 至少黃(PR #762 Codex P1);已經紅就留紅
        except ValueError:
            say("[黃] LAKE_STATUS_latest.json 讀不懂")
    else:
        say("[黃] 這次沒有新的 LAKE_STATUS_latest.json(入湖那步沒跑成或沒寫)")
    lp = PRIOR.lamps(out)
    for k, v in lp.items():
        say(f"  {k.replace('vdfcheck_', '')} · 燈 {v.get('lamp')}" + (f" · {v.get('counts')}" if v.get("counts") else ""))
    rc = PRIOR.worse(rc, *(PRIOR.lamp_rc(v.get("lamp")) for v in lp.values()))
    if len([g for g in got if g.startswith("vdfcheck_")]) < len(PRIOR.RECEIPTS) or "lakeall_LAKE_STATUS_projection.json" not in got:
        rc = PRIOR.worse(rc, 2)                     # 缺件至少黃;已經紅就留紅
    say("收據 → " + (" · ".join(got) if got else "(無)"))
    return rc


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "lakeall" not in argv:
        return PRIOR.main(argv)
    i = argv.index("lakeall")
    head, rest = argv[:i], argv[i + 1:]
    push = "--push" in head + rest
    head = [x for x in head if x != "--push"]
    rest = [x for x in rest if x != "--push"]
    if "--repo" not in head:
        say("[RED] 要 --repo <倉>")
        return 1
    repo = Path(head[head.index("--repo") + 1]).expanduser().resolve()
    if not (repo / BASE.VIA_REL).is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在(黃)'}")
    from datetime import datetime
    env = dict(os.environ, VIA_REPO=str(repo))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"via_hostboot_lakeall_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rc = run_lakeall(rest, repo, out, env)
    (out / "lakeall_RUN.json").write_text(json.dumps({"tool": TAG, "verb": "lakeall", "rc": rc, "secs": round(time.time() - _T0, 1),
                                                      "args": rest, "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None},
                                                     ensure_ascii=False, indent=1), encoding="utf-8")
    say(f"lakeall · rc {rc} · 收據 → {out}")
    if push:
        say(BASE.push_receipts(repo, out, stamp))
    say(f"完成 · rc {rc} · 總計 {time.time() - _T0:.0f}s")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 動詞表 = 前版 + lakeall", VERBS[:-1] == tuple(PRIOR.VERBS) and VERBS[-1] == "lakeall" and "vdfcheck" in VERBS)
    via = HERE.parents[3]
    st = lakeall_steps(via, False, ["--jobs", "4"])
    chk("③ 步驟:ENG239 尾版 --selftest → run --all --jobs 4(不帶 --start:起日讀 DataPlane 冊)→ three inventory/distill/reconcile → db check/verify → monitor",
        Path(st[0][0]).name.startswith("VDF_ENG239_ParquetLakeBuild_v") and st[1][1:] == ["run", "--all", "--jobs", "4"]
        and [s[1:] for s in st[2:5]] == [["three", "inventory"], ["three", "distill"], ["three", "reconcile"]]
        and [s[1:3] for s in st[5:7]] == [["db", "check"], ["db", "verify"]] and st[7][1] == "monitor", st)
    chk("③b 沒給 --jobs = 3 道", lakeall_steps(via, False, [])[1][-1] == "3")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / BASE.VIA_REL).mkdir(parents=True)
        calls = {}
        keep = BASE.on_branch

        def fake(rest, repo, out, env, tag, fn, rd):
            calls.update(tag=tag, rd=rd, env=env)
            return 0
        before = {k: os.environ.get(k) for k in CONSENT}
        try:
            BASE.on_branch = fake
            rc_no = run_lakeall([], tdp, tdp, {"X": "1"})
            no_call = "tag" not in calls
            rc_yes = run_lakeall([], tdp, tdp, {"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"})
        finally:
            BASE.on_branch = keep
        chk("④ 同意閘沒開 = RED rc 1、一步都不跑(on_branch 沒被叫)", rc_no == 1 and no_call, (rc_no, calls))
        chk("⑤ 閘開了(操作員視窗)→ on_branch tag lakeall · 收 vdf_three · 子行程帶入口標記 · 本檔沒改 os.environ 的閘",
            calls.get("tag") == "lakeall" and calls.get("rd") == ("vdf_three",) and calls["env"].get(PRIOR.ENTRY_FLAG[0]) == PRIOR.ENTRY_FLAG[1]
            and {k: os.environ.get(k) for k in CONSENT} == before, {k: v for k, v in calls.items() if k != "env"})
        chk("⑥ 收據缺件(湖狀態 / 驗證收據都沒有)→ 黃 rc 2,不冒充綠", rc_yes == 2, rc_yes)
    pj = project_lake({"engine": "e", "tables": [
        {"view": "v_a__t", "rows": 2341815, "date_col": "date", "min_date": "2018-01-02", "max_date": "2026-11-25", "lag_days": 1, "parts": 3},
        {"view": "v_b__t", "rows": 360, "date_col": "date", "min_date": "2018-01-02", "max_date": "2019-06-28", "lag_days": 2708, "parts": 1},
        {"view": "v_c__s", "rows": 9, "date_col": None, "min_date": None, "max_date": None, "lag_days": None, "parts": 1}]})
    txt = json.dumps(pj, ensure_ascii=False)
    chk("⑦ 湖投影:只留布林與分片數(不含列數 2341815 / 日期 2026-11-25)· 從 2018 起 2 · 7 天內新 1 · 有日期 2",
        "2341815" not in txt and "2026-11-25" not in txt and pj["covers_2018_n"] == 2 and pj["fresh_7d_n"] == 1 and pj["dated_n"] == 2, txt[:300])
    full = project_lake({"tables": [{"view": "v_x__t", "date_col": "date", "min_date": "2018-01-02", "lag_days": 1, "parts": 1}]})
    late = project_lake({"tables": [{"view": "v_x__t", "date_col": "date", "min_date": "2022-01-03", "lag_days": 500, "parts": 1}]})
    rc_full, rc_late = coverage_rc(full)[0], coverage_rc(late)
    chk("⑦b 覆蓋算進總燈:2018 起且 7 天內新 = 0 · 2022 起又落後 500 天 = 黃 2 並點名(Codex P1)· 一張日期表都沒有 = 黃",
        rc_full == 0 and rc_late[0] == 2 and rc_late[1] == ["v_x__t"] and rc_late[2] == ["v_x__t"]
        and coverage_rc({"views": []})[0] == 2, (rc_full, rc_late))
    rc_p = PRIOR.selftest()
    chk("⑧ 前版 v0104 自測照過(rc 0)", rc_p == 0, rc_p)
    src = HERE.read_text(encoding="utf-8")
    chk("⑨ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘(不寫 os.environ)· 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
