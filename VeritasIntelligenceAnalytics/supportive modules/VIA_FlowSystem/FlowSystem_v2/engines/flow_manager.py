# -*- coding: utf-8 -*-
"""MANAGER-15 flow_manager.py — 系統管理/編排 + synth + CLI(v0100R)。

命令:synth | selftest | autotest | calibrate | factors | run | validate-a | grid |
     worldmap | sim | perf | monitor | status | ui | all | live | harden
all = synth→selftest→calibrate→factors→run→validate-a→grid→worldmap→sim→perf→monitor→status→ui
live = 同 all 但 bridge 吃真實資料(daily_data.json 缺=誠實退 synth 並註明)。
治理:run_ledger.jsonl append-only;三層驗證(A 測量/B 效力/self-test)全綠才 SOLID。
"""
import json
import random
import sys
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
OUT = ROOT / "data" / "output"
STATE = ROOT / "data" / "state"
INP = ROOT / "data" / "input"

from flow_core import compute_fis, load_params, load_universe, snapshot  # noqa: E402
import flow_bridge  # noqa: E402
import flow_calibrate  # noqa: E402
import flow_factors  # noqa: E402
import flow_grid  # noqa: E402
import flow_macro  # noqa: E402
import flow_monitor  # noqa: E402
import flow_perf  # noqa: E402
import flow_pillar_a  # noqa: E402
import flow_selftest  # noqa: E402
import flow_sim  # noqa: E402
import flow_ui  # noqa: E402
import flow_worldmap  # noqa: E402


def _ledger(event, detail=""):
    STATE.mkdir(parents=True, exist_ok=True)
    with open(STATE / "run_ledger.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": dt.datetime.now().isoformat(timespec="seconds"),
                            "event": event, "detail": detail}, ensure_ascii=False) + "\n")


def cmd_synth():
    """依 params.synthetic 產 daily_data.json(alpha 控 flow→return 結構;=0 供反證)。"""
    p = load_params()
    s = p.get("synthetic", {})
    uni = load_universe()
    rng = random.Random(int(s.get("seed", 42)))
    n = int(s.get("n_days", 260))
    alpha = float(s.get("alpha", 0.35))
    noise = float(s.get("noise", 1.0))
    d0 = dt.date(2025, 8, 1)
    dates = []
    d = d0
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(str(d))
        d += dt.timedelta(days=1)
    records = []
    for t, u in uni.items():
        close = rng.uniform(20, 500)
        sh = rng.uniform(5e6, 5e8)
        pend = 0.0
        for i, ds in enumerate(dates):
            dsh = rng.gauss(0, sh * 0.004)
            sh = max(1e5, sh + dsh)
            drift = alpha * (pend / (sh * 0.004)) * 0.006 if sh else 0.0  # 傳導校準:alpha=0.35 可測·alpha=0 必紅
            pend = dsh
            close *= 1 + rng.gauss(drift, 0.011 * noise)
            records.append({"snapshot_date": ds, "ticker": t,
                            "close": round(close, 3), "shares_out": round(sh)})
    INP.mkdir(parents=True, exist_ok=True)
    (INP / "daily_data.json").write_text(
        json.dumps({"source": "synthetic v0100R(alpha=%s)" % alpha, "records": records},
                   ensure_ascii=False), encoding="utf-8")
    print("[synth] %d 檔 × %d 日(alpha=%s)→ data/input/daily_data.json" % (len(uni), n, alpha))
    _ledger("synth", "alpha=%s n=%d" % (alpha, n))
    return 0


def _panel(live=False):
    rec = flow_bridge.load_daily()
    if rec:
        src = ""
        try:
            src = str(json.loads((INP / "daily_data.json").read_text(encoding="utf-8-sig")).get("source", ""))
        except Exception:
            pass
        real = not src.startswith("synthetic")  # 誠實口徑:synth 側車不冒充真實 bridge
        return rec, real
    if live:
        print("[live] daily_data.json 不在位 — 誠實退 synth(bridge 待接)")
    cmd_synth()
    return flow_bridge.load_daily() or [], False


def _rows(panel):
    p = load_params()
    cal = json.loads((OUT / "calibration.json").read_text(encoding="utf-8-sig")) \
        if (OUT / "calibration.json").exists() else {}
    cp = cal.get("calibrated_params")
    if cp:
        p = json.loads(json.dumps(p))
        p["fis"].update(cp)
    return compute_fis(panel, p)


def cmd_run(live=False):
    panel, real = _panel(live)
    rows = _rows(panel)
    sn = snapshot(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "snapshot.json").write_text(json.dumps(
        {"version": "v0100R", "real_data": real, "generated": dt.datetime.now().isoformat(timespec="seconds"),
         **{k: v for k, v in sn.items() if k != "per_ticker"},
         "per_ticker": sn["per_ticker"][:70]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[run] snapshot:%d 檔 · RORO %s · %s · regime %s" %
          (len(sn["per_ticker"]), sn.get("roro"), sn.get("regime"), sn.get("regime_market")))
    _ledger("run", "roro=%s" % sn.get("roro"))
    return rows


def cmd_status():
    cal = json.loads((OUT / "calibration.json").read_text(encoding="utf-8-sig")) \
        if (OUT / "calibration.json").exists() else {}
    pa = json.loads((OUT / "pillar_a.json").read_text(encoding="utf-8-sig")) \
        if (OUT / "pillar_a.json").exists() else {}
    st_ok = (OUT / "selftest_ok.flag").exists()
    layers = {"pillar_a": "OK" if pa.get("status") == "CALIBRATED" else
              ("SKIP" if pa.get("status") == "UNCALIBRATED" else "FAIL"),
              "pillar_b": "OK" if cal.get("status") == "PROVED_VALID" else "FAIL",
              "selftest": "OK" if st_ok else "FAIL"}
    # UNCALIBRATED = 誠實降級:NOT_SOLID + indicative only(README v0103)
    solid = "SOLID" if all(v == "OK" for v in layers.values()) else "NOT_SOLID"
    note = ""
    if layers["pillar_a"] == "SKIP":
        note = "Pillar A UNCALIBRATED(真值未接)→ NOT_SOLID · signal indicative only"
    status = {"version": "v0100R", "solid": solid, "layers": layers, "note": note,
              "ts": dt.datetime.now().isoformat(timespec="seconds")}
    (OUT / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[status] SYSTEM %s · A=%s B=%s self=%s %s" %
          (solid, layers["pillar_a"], layers["pillar_b"], layers["selftest"], note))
    return status


def main():
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if cmd == "synth":
        return cmd_synth()
    if cmd == "selftest":
        rc = flow_selftest.run()
        if rc == 0:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "selftest_ok.flag").write_text("ok", encoding="utf-8")
        return rc
    if cmd in ("autotest", "harden"):
        return __import__("flow_autotest").run()
    if cmd == "calibrate":
        panel, _ = _panel()
        r = flow_calibrate.calibrate(panel)
        print("[calibrate] %s — %s" % (r["status"], r["reason"]))
        _ledger("calibrate", r["status"])
        return 0 if r["status"] == "PROVED_VALID" else 1
    if cmd == "factors":
        panel, _ = _panel()
        rows = _rows(panel)
        fwd, _s = flow_calibrate._rets_from_panel(panel)
        fx = flow_factors.build_factors(rows, fwd, include_noise_probe=True)
        print("[factors] kept %d · rejected %d" % (len(fx["kept"]), len(fx["rejected"])))
        return 0
    if cmd == "run":
        cmd_run()
        return 0
    if cmd == "validate-a":
        panel, _ = _panel()
        r = flow_pillar_a.validate_a(_rows(panel))
        print("[validate-a] %s — %s" % (r["status"], r["reason"]))
        return 0
    if cmd == "macro":
        panel, _ = _panel()
        mo = flow_macro.build_overlay(_rows(panel))
        print("[macro] %s · %s · %d 區判讀 → macro_overlay.json" %
              (mo["dxy"]["regime"], "真實側車" if mo["real_data"] else "合成 demo", len(mo["rows"])))
        return 0
    if cmd == "grid":
        panel, _ = _panel()
        flow_grid.build_grid(_rows(panel))
        print("[grid] grid.json OK")
        return 0
    if cmd == "worldmap":
        panel, _ = _panel()
        rows = _rows(panel)
        flow_worldmap.build_worldmap(rows)
        flow_worldmap.build_tierflow(rows)
        flow_sim.build_map_sim(rows)
        print("[worldmap] world_flow.html + tier_flow.html + global_map_sim.html")
        return 0
    if cmd == "sim":
        panel, _ = _panel()
        flow_sim.build_map_sim(_rows(panel))
        print("[sim] global_map_sim.html")
        return 0
    if cmd == "perf":
        flow_perf.build_perf()
        print("[perf] perf_trend.html")
        return 0
    if cmd == "monitor":
        panel, _ = _panel()
        flow_monitor.build_monitor(_rows(panel))
        print("[monitor] flow_monitor.html")
        return 0
    if cmd == "status":
        cmd_status()
        return 0
    if cmd == "ui":
        panel, _ = _panel()
        rows = _rows(panel)
        cal = json.loads((OUT / "calibration.json").read_text(encoding="utf-8-sig")) \
            if (OUT / "calibration.json").exists() else {}
        grid = json.loads((OUT / "grid.json").read_text(encoding="utf-8-sig")) \
            if (OUT / "grid.json").exists() else None
        fx = json.loads((OUT / "factors.json").read_text(encoding="utf-8-sig")) \
            if (OUT / "factors.json").exists() else None
        st = json.loads((OUT / "status.json").read_text(encoding="utf-8-sig")) \
            if (OUT / "status.json").exists() else None
        mo = json.loads((OUT / "macro_overlay.json").read_text(encoding="utf-8-sig")) \
            if (OUT / "macro_overlay.json").exists() else None
        flow_ui.build_index(rows, cal, st, grid, fx, mo)
        print("[ui] index.html")
        return 0
    if cmd in ("all", "live"):
        live = cmd == "live"
        panel, real = _panel(live)
        print("[all] 資料:%s" % ("真實 bridge" if real else "synthetic"))
        rc_st = flow_selftest.run()
        if rc_st == 0:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / "selftest_ok.flag").write_text("ok", encoding="utf-8")
        elif (OUT / "selftest_ok.flag").exists():
            (OUT / "selftest_ok.flag").unlink()
        r = flow_calibrate.calibrate(panel)
        print("[calibrate] %s — %s" % (r["status"], r["reason"]))
        rows = cmd_run(live)
        fwd, _s = flow_calibrate._rets_from_panel(panel)
        flow_factors.build_factors(rows, fwd, include_noise_probe=True)
        pa = flow_pillar_a.validate_a(rows)
        print("[validate-a] %s" % pa["status"])
        flow_grid.build_grid(rows)
        mo = flow_macro.build_overlay(rows)
        print("[macro] %s · %d 區判讀" % (mo["dxy"]["regime"], len(mo["rows"])))
        flow_worldmap.build_worldmap(rows)
        flow_worldmap.build_tierflow(rows)
        flow_sim.build_map_sim(rows)
        flow_perf.build_perf()
        flow_monitor.build_monitor(rows)
        st = cmd_status()
        cal = json.loads((OUT / "calibration.json").read_text(encoding="utf-8-sig"))
        grid = json.loads((OUT / "grid.json").read_text(encoding="utf-8-sig"))
        fx = json.loads((OUT / "factors.json").read_text(encoding="utf-8-sig"))
        flow_ui.build_index(rows, cal, st, grid, fx, mo)
        print("[ui] index.html + world_flow + tier_flow + global_map_sim + perf_trend + flow_monitor")
        _ledger("all", st["solid"])
        return 0
    print("未知命令:%s(可用:synth|selftest|autotest|calibrate|factors|run|validate-a|grid|macro|worldmap|sim|perf|monitor|status|ui|all|live|harden)" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
