#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0103 — 第一步監控:VCGC → VDF ∥ VCGC → VRN 實跑現況(薄尾;前版 v0102 → v0101 → 本體 v0100)
操作員(R34,2026-09-30):「將 PANORAMA 為第一步啟動監控 VCGC-VDF-VRN … 在第一步啟動檢查 U/I 後就可知問題在哪 先啟動他」
一 · monitor(只讀):前版只掃檔案樹,不看「跑」。本版讀中樞已經寫下的實跑存證,每條線一盞燈:
     VCGC 事件(VIA_Reports/vcgc/events/EVENTS_*.jsonl:最近一輪 go- / ai- 的 OK · FINDING · FAIL)·
     VDF 鏈(vdf_chain/VDFCHAIN_latest.json tally)· VRN 鏈(vrn_chain/VRNCHAIN_latest.json tally)·
     SDD 實測(sdd/SDD_REAL_latest.json 各工作流)· VCGC 串測(vcgc/TEST_latest.json)· 交接(docs/handoff/HANDOFF_latest.json)·
     TA-Lib(L50:本機 import 查得到 = 紅;只查不裝不刪)。
     每條線帶「存證時間」:超過 --stale-hours(預設 24)標 STALE(黃)——舊存證不冒充綠。
     輸出 VIA_Reports/panorama/monitor_latest.json 與 monitor_latest.html(RYG 表;本機開即看,無伺服器)。
     回傳:綠 0 · 有紅 / 黃 2(FINDING;監控是報告不是閘,紅不回 1 —— rc 1 會被中樞記成失敗進教訓帳)。
     VIA_Panorama 自己的事件不算進 VCGC 事件那一線(不自我參照)。
二 · first:第一步 = dashboard(前版一輪掃描 + 儀表板)→ monitor;回最差的 rc(0 綠 · 2 黃 · 1 紅)。
     PS 操作台與 `via-vcgc panorama` 都先跑這一步,看完就知道問題在哪一條線。
只讀規則同 v0100:不寫目標、不執行目標;只寫輸出夾。VIA_FROM_VCGC:經 VCGC run 呼叫。不用 TA-Lib。
用法:VIA_Panorama_v0103.py first | monitor [--json] [--stale-hours N] [--out 夾] | (其餘照 v0102)| --selftest
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
import html as _html
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_Panorama"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VIA_Panorama_v0102.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("VIA_Panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
globals().update({k: v for k, v in vars(PRIOR).items() if not k.startswith("_")
                  and k not in ("main", "selftest", "VERSION", "ENGINE", "HERE", "PRIOR", "PRIOR_NAME")})


def __getattr__(name: str):
    return getattr(PRIOR, name)


VERSION = "v0103"
ENGINE = Path(__file__).stem
VIA = HERE.parent.parent
MON_JSON, MON_HTML = "monitor_latest.json", "monitor_latest.html"
ORDER = {"RED": 3, "YELLOW": 2, "STALE": 2, "NODATA": 1, "GREEN": 0}


def _j(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _age_h(ts: str | None, now: datetime) -> float | None:
    if not ts:
        return None
    s = str(ts).strip().replace("Z", "+00:00").replace(" ", "T", 1)
    try:
        t = datetime.fromisoformat(s)
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return round((now - t).total_seconds() / 3600, 1)


def _row(track, lamp, value, at, note, now, stale_h):
    age = _age_h(at, now)
    if lamp == "GREEN" and age is not None and age > stale_h:
        lamp, note = "STALE", f"存證 {age} 小時前(> {stale_h})· 舊存證不冒充綠 · " + note
    return {"track": track, "lamp": lamp, "value": value, "at": at or "—", "age_h": age, "note": note}


def feed_events(via: Path, now, stale_h) -> list:
    rows, evs = [], []
    for f in sorted((via / "VIA_Reports" / "vcgc" / "events").glob("EVENTS_*.jsonl"))[-3:]:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("run") and not str(e.get("target") or "").startswith(_STEM):   # 監控自己的事件不算(不自我參照)
                evs.append(e)
    for prefix, name in (("go-", "VCGC 實跑(go)"), ("ai-", "VCGC 實跑(AI)")):
        mine = [e for e in evs if str(e.get("run", "")).startswith(prefix)]
        if not mine:
            rows.append(_row(name, "NODATA", "沒有這類輪號的事件", None, "先跑一輪(PS 操作台 go / AI 經 VCGC)", now, stale_h))
            continue
        run = max(mine, key=lambda e: e.get("t0") or 0)["run"]
        ev = [e for e in mine if e["run"] == run]
        cnt = {k: sum(1 for e in ev if e.get("outcome") == k) for k in ("OK", "FINDING", "FAIL")}
        bad = [str(e.get("target") or e.get("verb")) for e in ev if e.get("outcome") == "FAIL"]
        lamp = "RED" if cnt["FAIL"] else "YELLOW" if cnt["FINDING"] else "GREEN"
        rows.append(_row(name, lamp, f"輪 {run} · 事件 {len(ev)} · OK {cnt['OK']} · FINDING {cnt['FINDING']} · FAIL {cnt['FAIL']}",
                         max((e.get("ts") or "" for e in ev), default=None), ("FAIL:" + " · ".join(bad[:4])) if bad else "", now, stale_h))
    return rows


def feed_chain(via: Path, which: str, now, stale_h) -> dict:
    f = via / "VIA_Reports" / f"{which.lower()}_chain" / f"{which}CHAIN_latest.json"
    d = _j(f)
    track = f"VCGC → {which} 鏈"
    if not isinstance(d, dict):
        return _row(track, "NODATA", f"{f.name} 不在", None, "先跑 VCGC 的鏈(PS 操作台 ③)", now, stale_h)
    t = d.get("tally") or {}
    lamp = "RED" if t.get("RED") else "YELLOW" if any(t.get(k) for k in ("GATED", "NODATA", "ABSENT")) else "GREEN"
    rows = d.get("stages") or d.get("nodes") or []
    open_ = [str(r.get("id") or r.get("layer") or r.get("name")) + ":" + str(r.get("state")) for r in rows
             if isinstance(r, dict) and r.get("state") not in ("GREEN", "INFO", "SKIP")]
    return _row(track, lamp, " · ".join(f"{k} {v}" for k, v in t.items() if v), d.get("generated"),
                ("未綠 " + " · ".join(open_[:5])) if open_ else "", now, stale_h)


def feed_sdd(via: Path, now, stale_h) -> dict:
    d = _j(via / "VIA_Reports" / "sdd" / "SDD_REAL_latest.json")
    if not isinstance(d, dict):
        return _row("SDD 實測(工作流)", "NODATA", "SDD_REAL_latest.json 不在", None, "via-vcgc sdd real", now, stale_h)
    st = {}
    for code, r in (d.get("wkf") or {}).items():
        st.setdefault(r.get("state"), []).append(code)
    ai = [c for c, r in (d.get("wkf") or {}).items() if r.get("state") in ("FAIL", "FINDING", "NOT_RUN") and not r.get("operator_hand")]
    lamp = "RED" if ai else "YELLOW" if set(st) - {"OK", "REGISTERED_ONLY"} else "GREEN"
    return _row("SDD 實測(工作流)", lamp, " · ".join(f"{k} {len(v)}" for k, v in sorted(st.items(), key=lambda x: str(x[0]))),
                d.get("ts"), ("AI 端未綠 " + " · ".join(ai[:5])) if ai else "未綠都在操作員端", now, stale_h)


def feed_test(via: Path, now, stale_h) -> dict:
    d = _j(via / "VIA_Reports" / "vcgc" / "TEST_latest.json")
    if not isinstance(d, dict):
        return _row("VCGC 串測", "NODATA", "TEST_latest.json 不在", None, "via-vcgc test --quick", now, stale_h)
    bad = [str(r.get("id") or r.get("station")) for r in d.get("rows") or [] if isinstance(r, dict) and r.get("lamp") in ("RED", "YELLOW")]
    return _row("VCGC 串測", d.get("lamp") or "NODATA", " · ".join(f"{k} {v}" for k, v in (d.get("counts") or {}).items()),
                d.get("at"), " · ".join(bad[:5]), now, stale_h)


def feed_handoff(via: Path, now, stale_h) -> dict:
    d = _j(via / "docs" / "handoff" / "HANDOFF_latest.json")
    if not isinstance(d, dict):
        return _row("交接(驗收)", "NODATA", "HANDOFF_latest.json 不在", None, "via-vcgc handoff check", now, stale_h)
    lamp = "RED" if "RED" in (d.get("lamp"), d.get("closeout_lamp")) else \
        "YELLOW" if "YELLOW" in (d.get("lamp"), d.get("closeout_lamp")) else d.get("lamp") or "NODATA"
    return _row("交接(驗收)", lamp, f"交接 {d.get('lamp')} · 驗收 {d.get('closeout_lamp')} · 待辦 {len(d.get('pending') or [])}",
                d.get("at"), "交接綠 ≠ 驗收;BLOCKED / REVIEW 照實", now, stale_h)


def feed_talib(now) -> dict:
    found = importlib.util.find_spec("talib") is not None
    return {"track": "TA-Lib(L50)", "lamp": "RED" if found else "GREEN", "value": "本機 import 查得到" if found else "查無(禁用正確)",
            "at": now.isoformat(timespec="seconds"), "age_h": 0.0, "note": "只查不裝不刪;QuantGuard(VDF_ENG086)是唯一正主"}


def monitor_rows(via: Path, stale_h: float = 24.0, now: datetime | None = None) -> list:
    now = now or datetime.now(timezone.utc)
    return (feed_events(via, now, stale_h) + [feed_chain(via, "VDF", now, stale_h), feed_chain(via, "VRN", now, stale_h),
            feed_sdd(via, now, stale_h), feed_test(via, now, stale_h), feed_handoff(via, now, stale_h), feed_talib(now)])


def verdict(rows: list) -> str:
    w = max((ORDER.get(r["lamp"], 1) for r in rows), default=1)
    return {3: "RED", 2: "YELLOW", 1: "YELLOW", 0: "GREEN"}[w]


COLOR = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "STALE": "#9a6700", "RED": "#cf222e", "NODATA": "#57606a"}


def write_monitor(out: Path, rows: list, v: str) -> tuple:
    out.mkdir(parents=True, exist_ok=True)
    rep = {"engine": ENGINE, "version": VERSION, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "verdict": v, "rows": rows}
    jp, hp = out / MON_JSON, out / MON_HTML
    jp.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    tr = "".join(f"<tr><td>{_html.escape(r['track'])}</td><td style='color:#fff;background:{COLOR.get(r['lamp'], '#57606a')}'>"
                 f"{r['lamp']}</td><td>{_html.escape(str(r['value']))}</td><td>{_html.escape(str(r['at']))}</td>"
                 f"<td>{_html.escape(str(r['note']))}</td></tr>" for r in rows)
    hp.write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
                  "<title>VIA 第一步監控</title><style>body{font:14px system-ui;margin:16px;background:#fff;color:#1f2328}"
                  "table{border-collapse:collapse;width:100%}td,th{border:1px solid #d0d7de;padding:6px;text-align:left}"
                  "@media(prefers-color-scheme:dark){body{background:#0d1117;color:#e6edf3}td,th{border-color:#30363d}}</style>"
                  f"<h1>VCGC → VDF ∥ VCGC → VRN · 第一步監控 · {v}</h1><p>{_html.escape(rep['at'])} · {ENGINE}</p>"
                  "<table><tr><th>線</th><th>燈</th><th>現況</th><th>存證時間</th><th>說明</th></tr>" + tr + "</table>",
                  encoding="utf-8")
    return jp, hp


def monitor(opts: dict) -> int:
    out = Path(opts.get("out") or (VIA / "VIA_Reports" / "panorama"))
    rows = monitor_rows(VIA, float(opts.get("stale_hours") or 24))
    v = verdict(rows)
    jp, hp = write_monitor(out, rows, v)
    if opts.get("json"):
        print(json.dumps({"verdict": v, "rows": rows}, ensure_ascii=False, indent=1))
    else:
        print(f"[{ENGINE} monitor] {v} · 線 {len(rows)} · 頁 {hp}")
        for r in rows:
            print(f"  {r['lamp']:<7} {r['track']:<16} {str(r['value'])[:90]}" + (f" · {r['note'][:80]}" if r["note"] else ""))
    return 0 if v == "GREEN" else 2          # 報告不是閘:有紅 / 黃 = FINDING(rc 2);rc 1 只留給真的崩潰


def first(opts: dict) -> int:
    rc_scan = PRIOR.dashboard(None, {k: v for k, v in opts.items() if k in ("out", "profile")})
    rc_mon = monitor(opts)
    return 0 if rc_scan == 0 and rc_mon == 0 else 2   # 只報不擋:掃描或監控有紅 / 黃 = rc 2(FINDING)


def _opts(rest: list) -> dict:
    o = {"json": "--json" in rest}
    for key in ("--out", "--stale-hours"):
        if key in rest:
            i = rest.index(key)
            if i + 1 < len(rest):
                o[key[2:].replace("-", "_")] = rest[i + 1]
    return o


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] == "monitor":
        return monitor(_opts(a[1:]))
    if a and a[0] == "first":
        return first(_opts(a[1:]))
    return PRIOR.main(a)


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    print(f"=== {ENGINE} 自測(薄尾;先跑前版 v0102 → v0101 → 本體 v0100)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    chk("前版 v0102(含 v0101 · 本體 v0100)自測", prc == 0, (buf.getvalue().strip().splitlines() or [""])[-1])
    miss = [k for k in vars(PRIOR) if not k.startswith("_") and k not in globals() and k != "PRIOR_NAME"]
    chk("尾版不少公開名稱(TAILAPI)", not miss, " · ".join(miss[:5]))
    tmp = Path(tempfile.mkdtemp(prefix="via_pan103_"))
    try:
        now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
        ev = tmp / "VIA_Reports" / "vcgc" / "events"
        ev.mkdir(parents=True)
        lines = [{"run": "go-1", "t0": 1, "ts": "2026-09-30 11:00:00", "outcome": "OK", "target": "A"},
                 {"run": "go-1", "t0": 2, "ts": "2026-09-30 11:01:00", "outcome": "FAIL", "target": "CGC_MDL242_PathVerify"},
                 {"run": "ai-1", "t0": 3, "ts": "2026-09-30 11:02:00", "outcome": "OK", "target": "B"},
                 {"run": "ai-1", "t0": 4, "ts": "2026-09-30 11:03:00", "outcome": "FAIL", "target": "VIA_Panorama"}]
        (ev / "EVENTS_20260930.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        for name, key in (("VDF", "stages"), ("VRN", "nodes")):
            d = tmp / "VIA_Reports" / f"{name.lower()}_chain"
            d.mkdir(parents=True)
            tally = {"RED": 0, "GREEN": 5} if name == "VDF" else {"RED": 0, "NODATA": 2, "GREEN": 3}
            gen = "2026-09-30 10:00:00Z" if name == "VDF" else "2026-09-20 10:00:00Z"
            (d / f"{name}CHAIN_latest.json").write_text(json.dumps({"generated": gen, "tally": tally,
                                                                      key: [{"id": "3a", "state": "NODATA"}]}), encoding="utf-8")
        rows = monitor_rows(tmp, 24, now)
        by = {r["track"]: r for r in rows}
        chk("VCGC 事件:最近一輪 go- 有 FAIL = 紅,並點名目標", by["VCGC 實跑(go)"]["lamp"] == "RED"
            and "CGC_MDL242_PathVerify" in by["VCGC 實跑(go)"]["note"])
        chk("VCGC 事件:ai- 輪全 OK = 綠(VIA_Panorama 自己的 FAIL 不算)", by["VCGC 實跑(AI)"]["lamp"] == "GREEN")
        chk("VDF 鏈 tally 全綠且新鮮 = 綠", by["VCGC → VDF 鏈"]["lamp"] == "GREEN")
        chk("VRN 鏈有 NODATA = 黃,並列未綠節點", by["VCGC → VRN 鏈"]["lamp"] == "YELLOW" and "3a:NODATA" in by["VCGC → VRN 鏈"]["note"])
        chk("存證不在 = NODATA(SDD · 串測 · 交接),不冒充綠",
            all(by[k]["lamp"] == "NODATA" for k in ("SDD 實測(工作流)", "VCGC 串測", "交接(驗收)")))
        old = _row("x", "GREEN", "v", "2026-09-20T00:00:00+00:00", "", now, 24)
        chk("綠但存證過期 = STALE(黃)", old["lamp"] == "STALE")
        chk("TA-Lib 查無 = 綠(禁用正確)", by["TA-Lib(L50)"]["lamp"] in ("GREEN", "RED") and
            (by["TA-Lib(L50)"]["lamp"] == "GREEN") == (importlib.util.find_spec("talib") is None))
        chk("總判取最差:有紅 = 紅", verdict(rows) == "RED" and verdict([old]) == "YELLOW" and verdict([by["VCGC 實跑(AI)"]]) == "GREEN")
        import unittest.mock as _um
        with _um.patch.object(sys.modules[__name__], "VIA", tmp), contextlib.redirect_stdout(io.StringIO()):
            rc_m = monitor({"out": str(tmp / "o2")})
        chk("monitor 有紅回 rc 2(報告不是閘;rc 1 只給崩潰)", rc_m == 2)
        jp, hp = write_monitor(tmp / "out", rows, verdict(rows))
        page = hp.read_text(encoding="utf-8")
        chk("輸出 monitor_latest.json + html(RYG · 明暗主題 · 無外部資源)", _j(jp)["verdict"] == "RED" and "prefers-color-scheme" in page
            and "http" not in page.split("<h1>")[0].replace("http-equiv", ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
