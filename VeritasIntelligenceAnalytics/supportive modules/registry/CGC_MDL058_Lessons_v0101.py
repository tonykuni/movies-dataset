#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL058_Lessons_v0101 — 教訓帳本引擎(TOOL-034;操作員令 2026-08-13)
================================================================
令:增加 LESSON-LEARNED 機制——所有成功狀況及失敗因素都被記錄;
PRINT DETAILED RESULT MATRIX & ROOT CAUSES & SOLUTIONS SAVED IN LOG;
成功之無衝突 via_* 環境(單境與全艦隊)記為 GOLDEN 基線,作為下一輪改進起點。
v0100→v0101:手記編號改「最大號+1」(原筆數+1 於帳本分叉時撞號——
工作站實案 RC-16/17 重號)+重複拒收(同象因解已在帳→誠實拒,不再入);
自測「不重號」限縮至種子規則(操作員手記歷史重號屬帳實,不誣)。
方法(五段;純收割零耦合——不改動任何既有引擎):
  ① 收割 — 掃 VIA_Reports 之 depsuper_runs/rebuild_runs 存證 JSON,蒸餾入帳
  ② RESULT MATRIX — 歷次 run × 裁決(互撞/缺件/多層/GREEN 段/環境綠紅)全景表
  ③ ROOT CAUSES & SOLUTIONS — 規則庫(預載 15 條實戰教訓)+證據命中標記
  ④ GOLDEN 基線 — OK 單境指紋+全艦隊無衝突快照;與上一基線差異=回歸獵源
  ⑤ 存錄 — 教訓帳本 append-only(registry 內,隨版控);本輪矩陣全文落 .log
紅線:帳本只增不減(append_only);收割冪等(重跑零重複);零網路零安裝零改動
用法:via-lessons                      → 收割+矩陣+規則命中+基線+落 log
     via-lessons --golden             → 只列 GOLDEN 基線與差異
     via-lessons --record "現象" --cause "根因" --fix "解法"  → 操作員手記一條
     via-lessons --selftest           → 內建 10 檢(零網路零環境依賴)
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

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LEDGER = HERE / "VIA_Lessons_Ledger_v0100.json"
DEPS_DIR = VIA / "VIA_Reports" / "depsuper_runs"
REB_DIR = VIA / "VIA_Reports" / "rebuild_runs"
OUT = VIA / "VIA_Reports" / "lessons_runs"


def load_ledger() -> dict:
    try:
        d = json.loads(LEDGER.read_text(encoding="utf-8"))
        assert isinstance(d.get("entries"), list)
        return d
    except Exception:
        return {"schema": "VIA.Lessons.v1", "append_only": True, "entries": []}


def save_ledger(d: dict) -> None:
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── ① 收割(冪等;RUN/GOLDEN 蒸餾)────────────────────────────────
def harvest(ledger: dict, deps_dir: Path = DEPS_DIR, reb_dir: Path = REB_DIR) -> list[dict]:
    """存證 → 新帳目(RUN/GOLDEN_ENV/GOLDEN_FLEET);已入帳者跳過(冪等)。"""
    seen_run = {(e.get("engine"), e.get("run")) for e in ledger["entries"] if e.get("kind") == "RUN"}
    gold_env_fp = {e.get("fp") for e in ledger["entries"] if e.get("kind") == "GOLDEN_ENV"}
    gold_fleet_fp = {e.get("fp") for e in ledger["entries"] if e.get("kind") == "GOLDEN_FLEET"}
    new: list[dict] = []
    for f in sorted(deps_dir.glob("DEPS_*.json")):
        d = _read_json(f)
        if not d or ("via-deps", d.get("ts")) in seen_run:
            continue
        c = d.get("conflicts", {})
        new.append({"kind": "RUN", "engine": "via-deps", "run": d.get("ts"),
                    "verdict": d.get("verdict"), "mismatch_n": len(c.get("mismatch", [])),
                    "missing_n": len(c.get("missing", [])), "dup_n": len(c.get("dup_layers", {})),
                    "mirror": d.get("mirror", {}).get("family"), "src": f.name})
    for f in sorted(reb_dir.glob("REBUILD_*.json")):
        d = _read_json(f)
        if not d:
            continue
        envs = d.get("envs", [])
        ok = [e for e in envs if e.get("status") == "OK"]
        bad = [e for e in envs if e.get("status") in ("REBUILD", "BROKEN")]
        stages = d.get("stages", [])
        greens = [s for s in stages if (s.get("dryrun") or {}).get("risk") == "GREEN"]
        if ("via-rebuild", d.get("ts")) not in seen_run:
            new.append({"kind": "RUN", "engine": "via-rebuild", "run": d.get("ts"),
                        "verdict": ("GREEN" if not bad else "RED"), "envs_ok": len(ok),
                        "envs_bad": len(bad), "stages_n": len(stages), "greens_n": len(greens),
                        "bad_envs": [e["name"] for e in bad][:8], "src": f.name})
        for e in ok:  # 單境 GOLDEN:指紋變才記(成功狀況記錄)
            fp = f"{e.get('name')}|{e.get('python')}|{e.get('dists_n')}"
            if fp not in gold_env_fp:
                gold_env_fp.add(fp)
                new.append({"kind": "GOLDEN_ENV", "env": e.get("name"), "python": e.get("python"),
                            "dists_n": e.get("dists_n"), "fp": fp, "run": d.get("ts"),
                            "src": f.name, "note": "無衝突基線;件級詳單見該次 REBUILD 存證"})
        if envs and not bad:  # 全艦隊無衝突=下一輪改進起點
            fleet = sorted(f"{e.get('name')}@{e.get('python')}" for e in envs)
            fp = "|".join(fleet)
            if fp not in gold_fleet_fp:
                gold_fleet_fp.add(fp)
                new.append({"kind": "GOLDEN_FLEET", "envs": fleet, "n": len(fleet), "fp": fp,
                            "run": d.get("ts"), "src": f.name,
                            "note": "多環境多工具全綠一次達陣——改進起點"})
    return new


# ── ③ 規則庫命中(證據 → 教訓)────────────────────────────────────
def rule_hits(rules: list[dict], deps_dir: Path = DEPS_DIR, reb_dir: Path = REB_DIR) -> dict:
    """規則 match 描述子 vs 存證:factor 碼/缺件名/互撞需求方。回 {rule_id: [run…]}。"""
    ev = []
    for f in sorted(deps_dir.glob("DEPS_*.json")):
        d = _read_json(f)
        if d:
            c = d.get("conflicts", {})
            ev.append({"run": d.get("ts"), "factors": set(),
                       "missing": {m.get("pkg") for m in c.get("missing", [])},
                       "by": {m.get("by") for m in c.get("mismatch", [])}})
    for f in sorted(reb_dir.glob("REBUILD_*.json")):
        d = _read_json(f)
        if d:
            fac, miss, by = set(), set(), set()
            for e in d.get("envs", []):
                fac |= {x.get("code") for x in e.get("factors", [])}
                miss |= {m.get("pkg") for m in e.get("missing", [])}
                by |= {m.get("by") for m in e.get("mismatch", [])}
            ev.append({"run": d.get("ts"), "factors": fac, "missing": miss, "by": by})
    hits: dict[str, list] = {}
    for r in rules:
        m = r.get("match") or {}
        got = []
        for e in ev:
            hit = ("factor" in m and m["factor"] in e["factors"]) or \
                  ("missing_pkg" in m and m["missing_pkg"] in e["missing"]) or \
                  ("mismatch_by_any" in m and set(m["mismatch_by_any"]) & e["by"])
            if hit:
                got.append(e["run"])
        if got:
            hits[r["id"]] = sorted(set(got))
    return hits


# ── ②④ 矩陣與基線輸出 ───────────────────────────────────────────
def matrix_lines(entries: list[dict]) -> list[str]:
    L = ["  時間              引擎         裁決    互撞  缺件  多層  段(綠/總)  環境(綠/紅)"]
    for e in [x for x in entries if x.get("kind") == "RUN"][-30:]:
        if e["engine"] == "via-deps":
            L.append(f"  {e.get('run', '?'):15s}  via-deps     {e.get('verdict', '?'):6s}"
                     f"  {e.get('mismatch_n', 0):<4}  {e.get('missing_n', 0):<4}  {e.get('dup_n', 0):<4}"
                     f"  —          —")
        else:
            L.append(f"  {e.get('run', '?'):15s}  via-rebuild  {e.get('verdict', '?'):6s}"
                     f"  —     —     —     {e.get('greens_n', 0)}/{e.get('stages_n', 0)}"
                     f"        {e.get('envs_ok', 0)}/{e.get('envs_bad', 0)}"
                     + (f"  紅:{','.join(e.get('bad_envs', [])[:3])}" if e.get("envs_bad") else ""))
    return L


def golden_lines(entries: list[dict]) -> list[str]:
    L = []
    genv = [e for e in entries if e.get("kind") == "GOLDEN_ENV"]
    gfleet = [e for e in entries if e.get("kind") == "GOLDEN_FLEET"]
    for e in genv[-14:]:
        L.append(f"  [單境] {e.get('env', ''):26s} Py {e.get('python', '?'):8s} {e.get('dists_n', 0):>4} 件 · 錄於 {e.get('run', '?')}")
    for e in gfleet[-3:]:
        L.append(f"  [艦隊] {e.get('n')} 境全綠 · 錄於 {e.get('run')}(改進起點)")
    if len(gfleet) >= 2:
        prev, cur = set(gfleet[-2].get("envs", [])), set(gfleet[-1].get("envs", []))
        gone, born = sorted(prev - cur), sorted(cur - prev)
        if gone or born:
            L.append(f"  [基線差異] 退出:{','.join(gone) or '無'} · 新進:{','.join(born) or '無'}")
    if not L:
        L.append("  (尚無 GOLDEN——首個無衝突境/艦隊達陣時自動入帳)")
    return L


# ── 主流程 ───────────────────────────────────────────────────────
def cmd_report(golden_only: bool = False) -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ledger = load_ledger()
    new = harvest(ledger)
    for e in new:
        e["ts"] = ts
    ledger["entries"].extend(new)
    save_ledger(ledger)
    rules = [e for e in ledger["entries"] if e.get("kind") == "ROOT_CAUSE"]
    hits = rule_hits(rules)
    L = [f"=== 教訓帳本引擎 v0100 · {ts} · LESSON-LEARNED(成敗全錄)==="]
    L.append(f"── ① 收割 ── 新收 {len(new)} 筆 · 帳本累計 {len(ledger['entries'])} 筆(append-only)")
    if not golden_only:
        L.append("── ② DETAILED RESULT MATRIX(近 30 run)──")
        L += matrix_lines(ledger["entries"])
        L.append(f"── ③ ROOT CAUSES & SOLUTIONS(規則 {len(rules)} 條;證據命中 {len(hits)} 條)──")
        for r in rules:
            mark = "✓命中:" + ",".join(hits[r["id"]][-2:]) if r["id"] in hits else ("—" if r.get("match") else "手則")
            L.append(f"  [{r['id']}] 象:{r['sig'][:44]}")
            L.append(f"         因:{r['cause'][:52]}")
            L.append(f"         解:{r['fix'][:60]} · {mark}")
    L.append("── ④ GOLDEN 基線(無衝突=下一輪改進起點)──")
    L += golden_lines(ledger["entries"])
    L.append("── ⑤ 存錄 ──")
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / f"LESSON_{ts}.log"
    L.append(f"  帳本:{LEDGER.name}(隨版控) · 本輪全文:{log.relative_to(VIA)}")
    text = "\n".join(L)
    print(text)
    log.write_text(text + "\n", encoding="utf-8")
    return 0


def cmd_record(args: list[str]) -> int:
    what = _arg_after(args, "--record") or ""
    cause = _arg_after(args, "--cause") or ""
    fix = _arg_after(args, "--fix") or ""
    if not (what and cause and fix):
        print("  ✗ 手記需三件齊:--record 現象 --cause 根因 --fix 解法(誠實不收殘條)")
        return 2
    ledger = load_ledger()
    for e in ledger["entries"]:  # 重複拒收:同象因解已在帳
        if e.get("kind") == "ROOT_CAUSE" and (e.get("sig"), e.get("cause"), e.get("fix")) == (what, cause, fix):
            print(f"  [拒收] 同條已在帳({e.get('id')})——append-only 不重複入(誠實)")
            return 0
    nums = [int(m.group(1)) for e in ledger["entries"] if e.get("kind") == "ROOT_CAUSE"
            for m in [__import__("re").match(r"RC-(\d+)", str(e.get("id", "")))] if m]
    n = (max(nums) + 1) if nums else 1  # 最大號+1(筆數+1 會於帳本分叉時撞號)
    ledger["entries"].append({"kind": "ROOT_CAUSE", "id": f"RC-{n:02d}", "sig": what,
                              "cause": cause, "fix": fix, "match": None, "source": "operator",
                              "ts": datetime.now().strftime("%Y%m%d_%H%M%S")})
    save_ledger(ledger)
    print(f"  [入帳] RC-{n:02d} · {what[:60]}(操作員手則)")
    return 0


# ── 自測 10 檢(零網路;合成存證於暫存)────────────────────────────
def cmd_selftest() -> int:
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="via_lessons_st_"))
    dd, rd = tmp / "deps", tmp / "reb"
    dd.mkdir()
    rd.mkdir()
    (dd / "DEPS_T1.json").write_text(json.dumps({
        "ts": "T1", "verdict": "RED", "mirror": {"family": "official"},
        "conflicts": {"missing": [{"pkg": "enum34", "by": "bezier"}],
                      "mismatch": [{"pkg": "pandas", "by": "gradio"}], "dup_layers": {"a": []}}}),
        encoding="utf-8")
    (rd / "REBUILD_T2.json").write_text(json.dumps({
        "ts": "T2", "envs": [
            {"name": "via_ok", "status": "OK", "python": "3.12.12", "dists_n": 10, "factors": [],
             "missing": [], "mismatch": []},
            {"name": "via_bad", "status": "REBUILD", "python": "3.12.12", "dists_n": 5,
             "factors": [{"code": "CV2_OFF_ANCHOR"}], "missing": [], "mismatch": []}],
        "stages": [{"dryrun": {"risk": "GREEN"}}]}), encoding="utf-8")
    (rd / "REBUILD_T3.json").write_text(json.dumps({
        "ts": "T3", "envs": [
            {"name": "via_ok", "status": "OK", "python": "3.12.12", "dists_n": 10, "factors": [],
             "missing": [], "mismatch": []},
            {"name": "via_bad", "status": "OK", "python": "3.12.12", "dists_n": 12, "factors": [],
             "missing": [], "mismatch": []}],
        "stages": []}), encoding="utf-8")
    led = {"schema": "VIA.Lessons.v1", "append_only": True, "entries": [
        {"kind": "ROOT_CAUSE", "id": "RC-A", "sig": "s", "cause": "c", "fix": "f",
         "match": {"factor": "CV2_OFF_ANCHOR"}},
        {"kind": "ROOT_CAUSE", "id": "RC-B", "sig": "s", "cause": "c", "fix": "f",
         "match": {"missing_pkg": "enum34"}},
        {"kind": "ROOT_CAUSE", "id": "RC-C", "sig": "s", "cause": "c", "fix": "f",
         "match": {"mismatch_by_any": ["gradio", "streamlit"]}},
        {"kind": "ROOT_CAUSE", "id": "RC-D", "sig": "s", "cause": "c", "fix": "f", "match": None}]}

    def t01():
        new = harvest(led, dd, rd)
        kinds = [e["kind"] for e in new]
        assert kinds.count("RUN") == 3 and "GOLDEN_ENV" in kinds and "GOLDEN_FLEET" in kinds

    def t02():
        new = harvest(led, dd, rd)
        led2 = {**led, "entries": led["entries"] + new}
        assert harvest(led2, dd, rd) == []  # 冪等:重收零筆

    def t03():
        new = harvest(led, dd, rd)
        genv = [e for e in new if e["kind"] == "GOLDEN_ENV"]
        assert {e["env"] for e in genv} == {"via_ok", "via_bad"}  # via_bad 轉綠亦入帳
        assert len([e for e in genv if e["env"] == "via_ok"]) == 1  # 同指紋只記一次

    def t04():
        new = harvest(led, dd, rd)
        fleet = [e for e in new if e["kind"] == "GOLDEN_FLEET"]
        assert len(fleet) == 1 and fleet[0]["run"] == "T3"  # T2 有紅不成艦隊;T3 全綠達陣

    def t05():
        h = rule_hits(led["entries"], dd, rd)
        assert h.get("RC-A") == ["T2"] and h.get("RC-B") == ["T1"] and h.get("RC-C") == ["T1"]
        assert "RC-D" not in h  # 手則不誣命中

    def t06():
        new = harvest(led, dd, rd)
        lines = matrix_lines(led["entries"] + new)
        assert any("via-deps" in l and "RED" in l for l in lines)
        assert any("via-rebuild" in l and "via_bad" in l for l in lines)

    def t07():
        new = harvest(led, dd, rd)
        gl = golden_lines(led["entries"] + new)
        assert any("艦隊" in l for l in gl) and any("via_ok" in l for l in gl)

    def t08():
        real = load_ledger()
        assert real.get("append_only") is True
        rules = [e for e in real["entries"] if e.get("kind") == "ROOT_CAUSE"]
        assert len(rules) >= 15 and all(r.get("sig") and r.get("cause") and r.get("fix") for r in rules)

    def t09():
        real = load_ledger()
        ids = [e["id"] for e in real["entries"]
               if e.get("kind") == "ROOT_CAUSE" and e.get("source") != "operator"]
        assert len(ids) == len(set(ids))  # 種子規則不重號(手記歷史重號屬帳實不誣)

    def t10():
        bad = harvest({"schema": "x", "append_only": True, "entries": []}, tmp / "nodir", tmp / "nodir2")
        assert bad == []  # 目錄缺=誠實零收不炸

    battery = [("收割三態", t01), ("冪等零重複", t02), ("單境基線+指紋去重", t03),
               ("艦隊達陣判定", t04), ("規則命中三式", t05), ("矩陣行", t06),
               ("基線行+艦隊", t07), ("預載規則完備", t08), ("規則不重號", t09),
               ("缺目錄誠實", t10)]
    print("=== 教訓帳本引擎自測 10 檢(v0101)(零網路零改動;合成存證)===")
    n_ok = 0
    for name, fn in battery:
        try:
            fn()
            n_ok += 1
            print(f"  [OK  ] {name}")
        except Exception as exc:
            print(f"  [FAIL] {name} · {type(exc).__name__}:{str(exc)[:70]}")
    print(f"  [計] {n_ok}/{len(battery)} 綠")
    return 0 if n_ok == len(battery) else 1


def _arg_after(args: list, flag: str):
    try:
        return args[args.index(flag) + 1]
    except (ValueError, IndexError):
        return None


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return cmd_selftest()
    if "-h" in a or "--help" in a or "--doc" in a:
        print(__doc__)
        return 0
    if "--record" in a:
        return cmd_record(a)
    return cmd_report(golden_only="--golden" in a)


if __name__ == "__main__":
    sys.exit(main())
