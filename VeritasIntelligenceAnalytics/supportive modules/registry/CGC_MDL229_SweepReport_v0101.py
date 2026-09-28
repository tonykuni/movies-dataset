#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL229_SweepReport v0101 — 薄尾:報告補上「網路工具版本號」與工具註冊 · 覆蓋 · 舊副本矩陣

操作員 2026-09-28:「上面少了網路工具版本號你查一下」。v0100 的 ② 加速器矩陣只有 Celeritas PS7 那幾列,
網路工具(VeritasAegisNexus 尾版 ← SUP_MDL740 尾版)沒上報告。本尾版不改 v0100 一個字(L04),只在它算完之後補:

  ② 加速器 +3 列:加速器引擎 ← 載入器 · 網路工具 ← 載入器 · 上游包判定(讀 CGC_MDL230 探針 JSON)
  ① 總判 KPI +1 列「⑦ 工具註冊 · 覆蓋」(探針總判;JSON 是不是這次跑出來的照實標)
  ⑪ Ⓐ 工具註冊 · ⑫ Ⓑ 上游包 · ⑬ Ⓒ 覆蓋率 · ⑭ Ⓓ 舊副本(探針自己的四張,原樣接上;本支不另判 L05)
  ⑩ 待辦併入探針的工具待辦,依嚴重度重排

探針 JSON 不在 = KPI 列 ABSENT、其餘照 v0100(缺件 ≠ 壞掉,L16)。
用法同 v0100:python CGC_MDL229_SweepReport_v0101.py render --side <SWEEP_SIDE_latest.json> [--width N] [--plain] [--rows N]
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

import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL229_SweepReport"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl229_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_TAG = "CGC_MDL229_SweepReport v" + Path(__file__).stem.rsplit("_v", 1)[-1]
TOOLPROBE = PRIOR.REPORTS / "toolprobe" / "TOOLPROBE_latest.json"
_BASE_BUILD = PRIOR.build


def __getattr__(name):
    return getattr(PRIOR, name)


def _probe(side: dict) -> dict | None:
    p = Path(side.get("toolprobe_json") or TOOLPROBE)
    return PRIOR._load(p)


STATUS_JSON = "SWEEP_STATUS_latest.json"
_LAST: dict = {}


def _utc_epoch(s: str | None) -> float | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def _freshness(given: dict | None, path: Path, step: dict) -> str:
    """這一步的 JSON 是不是本次寫的。chain 的 generated 帶 Z(UTC)就比它;沒有 UTC 欄位(DB 面板的 ts 是本地時間)就比檔案 mtime。
    回 fresh / stale / absent / unknown。步驟略過 = unknown(不判)。"""
    if step.get("skipped"):
        return "unknown"
    t0 = _utc_epoch(step.get("started_utc"))
    rep = given if given is not None else PRIOR._load(path)
    if not rep:
        return "absent"
    if t0 is None:
        return "unknown"
    gen = str(rep.get("generated") or "")
    if gen.endswith("Z"):
        g = _utc_epoch(gen)
    elif given is None and path.is_file():
        g = path.stat().st_mtime
    else:
        return "unknown"
    return "fresh" if g is not None and g >= t0 - 2 else "stale"


def build(side: dict, vdf: dict | None = None, vrn: dict | None = None, db: dict | None = None,
          limit: int | None = None, probe: dict | None = None) -> dict:
    rep = _BASE_BUILD(side, vdf=vdf, vrn=vrn, db=db, limit=limit)
    rep["engine"] = ENGINE_TAG
    tp = _probe(side) if probe is None else probe
    step = PRIOR._step(side, "toolprobe")
    cell = PRIOR._cell
    res = (tp or {}).get("resolved") or {}
    up = (tp or {}).get("upstream") or {}
    # ② 加速器:補引擎 / 網路工具版本號(操作員要的那一列)
    for i, (t, cols, rows, st) in enumerate(rep["sections"]):
        if t.startswith("②"):
            extra = [["加速器引擎(py)", f"{res.get('accelerator', '—')} ← {res.get('accelerator_loader', '—')}"],
                     ["網路工具(py)", f"{res.get('network', '—')} ← {res.get('network_loader', '—')}"],
                     ["上游包", f"{up.get('source', '—')} {up.get('package', '')} · {up.get('verdict', '探針 JSON 不在(via-sweep 工具步)')}"]]
            rep["sections"][i] = ("② 加速器與網路工具(版本號 · PS7 · 模板助手)", cols, rows + [[cell(x) for x in r] for r in extra], st)
    # ① KPI:工具註冊 · 覆蓋
    if step.get("skipped"):
        state, point = "SKIP", "本次略過"
    elif not tp:
        state, point = "ABSENT", "TOOLPROBE_latest.json 不在(CGC_MDL230 probe 沒跑)"
    else:
        t0, gen = step.get("started_utc"), tp.get("ts_utc")
        fresh = "未比對" if not (t0 and gen) else ("本次" if str(gen)[:19] >= str(t0)[:19] else "舊的(本次沒寫)")
        state = tp.get("verdict") or "NODATA"
        if fresh.startswith("舊的"):
            state = "STALE"               # 舊結論不冒充本次(照 Codex #334 P1 的教訓)
        point = " · ".join(f"{k[0]} {k[1]}" for k in tp.get("kpi") or []) + f" · JSON {fresh}"
    kpi_row = ["⑦ 工具註冊 · 覆蓋", state, "—" if step.get("rc") is None else str(step.get("rc")),
               "—" if step.get("sec") is None else f"{step.get('sec')}s", point]
    rep["kpi"].append(kpi_row)
    # ⑩ 待辦併入工具待辦
    if tp:
        for r in tp.get("todo") or []:
            rep["todo"].append([r[0], "工具 · " + str(r[1]), r[2], r[3], r[4]])
        rep["todo"].sort(key=lambda r: (PRIOR.SEV.get(str(r[0]), 5), r[1]))
        n = limit
        todo = rep["todo"] if not n or len(rep["todo"]) <= n else rep["todo"][:n] + [[f"… 另 {len(rep['todo']) - n} 列(全表在 JSON / log)", "", "", "", ""]]
        for i, (t, cols, rows, st) in enumerate(rep["sections"]):
            if t.startswith("⑩"):
                rep["sections"][i] = (f"⑩ 待辦({len(rep['todo'])} 列;依嚴重度)", cols, [[cell(x) for x in r] for r in todo], st)
        marks = ["⑪", "⑫", "⑬", "⑭"]
        for m, sec in zip(marks, (tp.get("sections") or [])[:4]):
            t, cols, rows, st = sec
            rep["sections"].append((m + " " + t, cols, rows, st))
    # Codex #338 P1:舊的結論不決定本次總判。本步沒寫 JSON(崩潰 / 逾時 / 中斷)= STALE;本步輸出有 Traceback = RED
    incomplete = []
    checks = (("② VDF 鏈", "vdf_chain", vdf, PRIOR.VDF_CHAIN), ("③ VRN 鏈", "vrn_chain", vrn, PRIOR.VRN_CHAIN),
              ("⑥ DB 面板", "db_panel", db, PRIOR.DB_PANEL))
    for name, sid, given, path in checks:
        stp = PRIOR._step(side, sid)
        row = next((r for r in rep["kpi"] if r[0] == name), None)
        if row is None or not stp or stp.get("skipped"):
            continue
        if stp.get("missing"):
            incomplete.append(f"{name}:尾版不在")
            continue
        crashed = any("Traceback (most recent call last)" in str(x) for x in stp.get("lines") or [])
        f = _freshness(given, path, stp)
        if crashed:
            row[1], row[4] = "RED", "本步崩潰(輸出有 Traceback)· " + str(row[4])
            incomplete.append(f"{name}:崩潰")
        if f in ("stale", "absent") and not crashed:
            row[1] = "STALE" if f == "stale" else "ABSENT"
            row[4] = ("JSON 不是本次寫的(舊結論不算)· " if f == "stale" else "本次沒有結論 JSON · ") + str(row[4])
            incomplete.append(f"{name}:{'結論是舊的' if f == 'stale' else '沒有結論'}")
            rep["todo"].insert(0, [row[1], "實測", name, "本次這一步沒有寫出結論(崩潰 / 逾時 / 中斷)", "看 log 該步全文;單跑該步"])
    for sid, name in (("bridge", "④ 橋掃"), ("panorama", "⑤ 全景"), ("toolprobe", "⑦ 工具")):
        stp = PRIOR._step(side, sid)
        if stp and not stp.get("skipped") and (stp.get("missing") or any("Traceback (most recent call last)" in str(x) for x in stp.get("lines") or [])):
            incomplete.append(f"{name}:{'尾版不在' if stp.get('missing') else '崩潰'}")
    for i, (t, cols, rows, st) in enumerate(rep["sections"]):
        if t.startswith("①"):
            rep["sections"][i] = (t, cols, [[cell(x) for x in r] for r in rep["kpi"]], st)
    rep["incomplete"] = incomplete
    rep["verdict"] = PRIOR._worst([r[1] for r in rep["kpi"] if r[1] not in ("INFO", "SKIP", "HOLD")])
    _LAST.clear()
    _LAST.update({"verdict": rep["verdict"], "incomplete": incomplete, "ts": rep["ts"]})
    return rep


PRIOR.build = build            # v0100 的 render / main 用本尾版的 build(v0100 單獨跑時不受影響)


_BASE_RENDER = PRIOR.render


def render(side: dict, *a, **kw) -> dict:
    """同 v0100 render,另寫 SWEEP_STATUS_latest.json(總判 + 沒跑完的步)給 PowerShell 定結束碼(Codex #338 P2)。"""
    r = _BASE_RENDER(side, *a, **kw)
    out = Path(kw.get("out") or PRIOR.OUT)
    st = {"verdict": _LAST.get("verdict"), "incomplete": _LAST.get("incomplete") or [], "ts": _LAST.get("ts")}
    (out / STATUS_JSON).write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    r["incomplete"] = st["incomplete"]
    r["paths"]["status"] = str(out / STATUS_JSON)
    return r


PRIOR.render = render          # v0100 的 main 也走本尾版 render(寫狀態檔)
plain = PRIOR.plain
paste = PRIOR.paste


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    side = {"head": "abc1234 test", "flow": {"ok": True, "line": "[流程] 政策過 · 子系統已對齊 · 才執行"},
            "accel": {"加速器": "套對 v1141 · 已套"},
            "steps": [{"id": "vcgc", "rc": 0, "sec": 1.0, "lines": ["[流程] 政策過 · 子系統已對齊 · 才執行"]},
                      {"id": "toolprobe", "rc": 0, "sec": 2.0, "started_utc": "2026-09-28 00:00:00"}]}
    probe = {"ts": "2026-09-28 01:00:00", "ts_utc": "2026-09-28 01:00:00", "verdict": "AMBER",
             "resolved": {"accelerator": "VeritasCeleritas_v1141.py", "accelerator_loader": "SUP_MDL737_SuperAccelModule_v0108.py",
                          "network": "VeritasAegisNexus_v0116.py", "network_loader": "SUP_MDL740_NetUnified_v0117.py"},
             "upstream": {"source": "zip VeritasCeleritas-v1.14.0_4.zip", "package": "v1.14.0", "verdict": "不採用:上游引擎含 TA-Lib(L50 第一條)"},
             "kpi": [["Ⓐ 工具註冊", "GREEN", ""], ["Ⓒ 覆蓋率", "AMBER", ""]],
             "todo": [["AMBER", "覆蓋", "PS 模板章 · 既有債", "843 支", "L70"]],
             "sections": [["Ⓐ 工具註冊", ["燈", "檔"], [["GREEN", "VeritasAegisNexus_v0116.py"]], 0],
                          ["Ⓑ 上游包", ["燈", "檔"], [["INFO", "engine/VeritasCeleritas.py"]], 0],
                          ["Ⓒ 覆蓋率", ["燈", "面"], [["GREEN", "PY"]], 0],
                          ["Ⓓ 舊副本", ["燈", "檔"], [["HOLD", "supportive modules/VeritasAegisNexus.py"]], 0],
                          ["Ⓔ 工具待辦", ["燈"], [["AMBER"]], 0]]}
    empty = {"summary": []}
    rep = build(side, vdf={}, vrn={}, db=empty, probe=probe)
    acc = next(s for s in rep["sections"] if s[0].startswith("②"))
    chk("① ② 矩陣有網路工具版本號(VeritasAegisNexus_v0116 ← SUP_MDL740 v0117)",
        any("VeritasAegisNexus_v0116.py ← SUP_MDL740_NetUnified_v0117.py" in r[1] for r in acc[2]))
    chk("② 總判 KPI 多一列「⑦ 工具註冊 · 覆蓋」且帶探針總判", any(r[0] == "⑦ 工具註冊 · 覆蓋" and r[1] == "AMBER" for r in rep["kpi"]))
    titles = [s[0] for s in rep["sections"]]
    chk("③ 探針四張矩陣接成 ⑪–⑭(Ⓔ 不重複,已併進 ⑩)", [t[:1] for t in titles[-4:]] == ["⑪", "⑫", "⑬", "⑭"] and not any("Ⓔ" in t for t in titles),
        " · ".join(t[:6] for t in titles))
    chk("④ 工具待辦併進 ⑩", any(str(r[1]).startswith("工具") for r in rep["todo"]))
    rep2 = build(side, vdf={}, vrn={}, db=empty, probe={})
    chk("⑤ 探針 JSON 不在 = KPI ABSENT,不當壞掉也不假綠", any(r[0] == "⑦ 工具註冊 · 覆蓋" and r[1] == "ABSENT" for r in rep2["kpi"]))
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "TOOLPROBE_latest.json"
        pj.write_text(json.dumps(probe, ensure_ascii=False), encoding="utf-8")
        side2 = dict(side, toolprobe_json=str(pj))
        r = render(side2, out=Path(td), use_plain=True, echo=False, vdf={}, vrn={}, db=empty)
        txt = (Path(td) / PRIOR.REPORT_TXT).read_text(encoding="utf-8")
        chk("⑥ render 走本尾版 build:純文字報告有 ⑭ 與網路工具列", "⑭" in txt and "VeritasAegisNexus_v0116" in txt, r["engine"])
    stale = build(dict(side, steps=side["steps"][:1] + [dict(side["steps"][1], started_utc="2026-09-29 00:00:00")]),
                  vdf={}, vrn={}, db=empty, probe=dict(probe, ts_utc="2026-09-28 01:00:00"))
    chk("⑦ 探針 JSON 比這次開跑還舊 = STALE,不冒充本次", any(r[0] == "⑦ 工具註冊 · 覆蓋" and r[1] == "STALE" for r in stale["kpi"]))
    chk("⑧ 薄尾只接:v0100 本體 build 原樣保留、render 走本尾版", PRIOR_PATH.name.endswith("_v0100.py") and _BASE_BUILD is not build and PRIOR.build is build)
    # Codex #338 P1/P2
    side3 = dict(side, steps=side["steps"] + [
        {"id": "vdf_chain", "rc": 1, "sec": 1.0, "started_utc": "2026-09-28 05:00:00", "lines": ["Traceback (most recent call last):", "boom"]},
        {"id": "vrn_chain", "rc": 1, "sec": 1.0, "started_utc": "2026-09-28 05:00:00", "lines": []},
        {"id": "db_panel", "rc": 0, "sec": 1.0, "started_utc": "2026-09-28 05:00:00", "lines": []}])
    green = {"rc_name": "GREEN", "generated": "2026-09-27 01:00:00Z", "rows": []}
    fresh_green = {"rc_name": "GREEN", "generated": "2026-09-28 05:00:30Z", "rows": []}
    with tempfile.TemporaryDirectory() as td:
        dbp = Path(td) / "DBM_PANEL_latest.json"
        dbp.write_text(json.dumps({"verdict": "GREEN", "ts": "2026-09-28 13:00:00", "summary": []}), encoding="utf-8")
        import os as _os
        _os.utime(dbp, (_utc_epoch("2026-09-27 00:00:00"), _utc_epoch("2026-09-27 00:00:00")))
        keep = PRIOR.DB_PANEL
        PRIOR.DB_PANEL = dbp
        try:
            r3 = build(side3, vdf=green, vrn=green, db=None, probe=probe)
        finally:
            PRIOR.DB_PANEL = keep
    k3 = {r[0]: r[1] for r in r3["kpi"]}
    chk("⑨ 舊的 GREEN 結論不冒充本次:VRN JSON 早於本步開跑 = STALE;DB 面板本地 ts 看似新、檔案 mtime 舊 = STALE",
        k3.get("③ VRN 鏈") == "STALE" and k3.get("⑥ DB 面板") == "STALE", str(k3))
    chk("⑩ 本步輸出有 Traceback = RED,總判跟著 RED", k3.get("② VDF 鏈") == "RED" and r3["verdict"] == "RED", r3["verdict"])
    chk("⑪ incomplete 列出沒跑完的步(PowerShell 據此給結束碼 2)", len(r3["incomplete"]) >= 3, " · ".join(r3["incomplete"]))
    side4 = dict(side, steps=side["steps"] + [{"id": "vrn_chain", "rc": 1, "sec": 1.0, "started_utc": "2026-09-28 05:00:00", "lines": []}])
    r4 = build(side4, vdf={}, vrn=fresh_green, db={"summary": []}, probe=probe)
    chk("⑫ 本次寫的 JSON 照用(不誤判 STALE)", {r[0]: r[1] for r in r4["kpi"]}.get("③ VRN 鏈") == "GREEN" and not any("VRN" in x for x in r4["incomplete"]))
    with tempfile.TemporaryDirectory() as td:
        pj = Path(td) / "TOOLPROBE_latest.json"
        pj.write_text(json.dumps(probe, ensure_ascii=False), encoding="utf-8")
        render(dict(side3, toolprobe_json=str(pj)), out=Path(td), use_plain=True, echo=False, vdf=green, vrn=green, db={"summary": []})
        stj = json.loads((Path(td) / STATUS_JSON).read_text(encoding="utf-8"))
        chk("⑬ render 寫 SWEEP_STATUS_latest.json(總判 + incomplete)", stj.get("verdict") == "RED" and stj.get("incomplete"), str(stj))
    ok = all(results)
    print(f"  {ENGINE_TAG} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a or (a and a[0] == "selftest"):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
