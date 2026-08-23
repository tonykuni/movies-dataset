#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_conflict_guard — 衝突機制總哨兵+壞環境黑名單守衛(TOOL-107,批106)
====================================================================
令:「檢查衝突機制 壞環境黑名單 從前一個進度測試 測試新增計畫 計畫無誤直接裝」。
C1 衝突機制總巡檢(八道,全部唯讀):
  ① 中央參數樞紐跨冊衝突(via-params 冊圈)
  ② canonical 未裁殘量(三子系統參數冊:多值且不在 canonical 區=未裁)
  ③ ETF 清冊名碼衝突(CONFLICT_PENDING_VERIFY 具名列示=黃,候實連定奪)
  ④ 雙世代裁決冊:QUEUED 必須歸零;HOLD/BLOCKED 具名列管
  ⑤ 存證冊完整性(存證件在位+現役件在位;缺=紅)
  ⑥ 語法版本閘冊有效性(檔在位+python_min 可解析)
  ⑦ R2 殘留(canonical 裁決含寫死絕對路徑=紅)
  ⑧ 啟動器鐵律殘留(bin/*.cmd 寫死版號=紅;L6 同規)
C2 壞環境黑名單守衛(冊:VIA_BadEnv_Blacklist 最新版):
  ⑨ 現行 VIA 根不得落於黑名單根之下
  ⑩ 活執行區零 0-byte 占位檔(bin/ + registry/ 頂層;HZ-01)
  ⑪ sys.path 不含 accelerator/(HZ-03 標準庫遮蔽)
  ⑫ PATH 不含黑名單根前綴(HZ-02;容器無 Windows PATH=誠實 SKIP)
  ⑬ 黑名單件不得為任何 bin 動詞的執行標的
誠實三態 OK/FAIL/SKIP;報告落 VIA_Reports;rc0=無紅(黃可過,具名列示)。
用法:
  via-conflict            → 全巡檢+報告
  via-conflict --selftest → 十檢(沙盒零網路)
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
REPORTS = VIA / "VIA_Reports" / "conflict_guard_runs"
CMD_HARD_RX = re.compile(r"v\d{3,4}[a-z]?\.(py|ps1)")
ABS_PATH_RX = re.compile(r"OneDrive|Downloads|^[A-Za-z]:\\\\|C:\\\\", re.I)


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def _jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _res(name: str, state: str, note: str = "") -> dict:
    return {"name": name, "state": state, "note": note}


# ── C1 衝突機制八道 ──────────────────────────────────────────────
def c1_central_params(via: Path = VIA) -> dict:
    """① 跨冊衝突:直用 via-params 最新版之 find_conflicts(唯讀)"""
    mod_p = _newest(via / "supportive modules" / "registry", "via_params_central_v*.py")
    if mod_p is None:
        return _res("① 中央參數跨冊衝突", "SKIP", "樞紐缺(誠實)")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_vpc", mod_p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    records = [m.scan_book(b, via) for b in m.BOOKS]
    conflicts = m.find_conflicts(records)
    note = f"{len(conflicts)} 衝突(建議燈)"
    if conflicts:
        note += " · " + " | ".join(c["key"] for c in conflicts[:3])
    return _res("① 中央參數跨冊衝突", "OK" if len(conflicts) == 0 else "WARN", note)


def c1_canonical_residue(via: Path = VIA) -> dict:
    """② 多值未裁殘量(len(vals)>1 且不在 canonical)"""
    residue = 0
    for sub in ("VRN", "VDF", "VAP"):
        p = _newest(via / "functional modules" / sub, f"{sub}_Param_Registry_v*.json")
        if p is None:
            continue
        reg = _jload(p)
        by_name = {}
        for x in reg.get("params", []):
            by_name.setdefault(x["name"], set()).add(x["value"])
        canon = reg.get("canonical", {})
        residue += sum(1 for n, v in by_name.items() if len(v) > 1 and n not in canon)
    return _res("② canonical 未裁殘量", "OK" if residue == 0 else "FAIL", f"{residue} 鍵未裁")


def c1_etf_conflicts(via: Path = VIA) -> dict:
    p = (via / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
         / "config" / "TW_Active_ETF_Registry_v0100.json")
    if not p.exists():
        return _res("③ ETF 名碼衝突", "SKIP", "冊缺(誠實)")
    reg = _jload(p)
    con = [e["ticker"] for e in reg.get("etfs", []) if e.get("status") == "CONFLICT_PENDING_VERIFY"]
    pend = sum(1 for e in reg.get("etfs", []) if e.get("status") == "PENDING_VERIFY")
    return _res("③ ETF 名碼衝突", "WARN" if con else "OK",
                f"衝突 {len(con)}({','.join(con)})候實連定奪 · 待驗 {pend}")


def c1_twoera(via: Path = VIA) -> dict:
    p = _newest(via / "supportive modules" / "registry", "VIA_TwoEra_Verdicts_v*.json")
    if p is None:
        return _res("④ 雙世代裁決冊", "SKIP", "冊缺")
    d = _jload(p)
    st = {}
    for v in d.get("verdicts", []):
        st[v.get("status", "?")] = st.get(v.get("status", "?"), 0) + 1
    queued = st.get("QUEUED", 0)
    hold = st.get("HOLD", 0) + st.get("BLOCKED", 0)
    return _res("④ 雙世代裁決冊", "OK" if queued == 0 else "FAIL",
                f"QUEUED {queued}(須 0)· HOLD/BLOCKED {hold} 列管 · {p.name}")


def c1_evidence(via: Path = VIA) -> dict:
    p = _newest(via / "supportive modules" / "registry", "VIA_Evidence_Originals_v*.json")
    if p is None:
        return _res("⑤ 存證冊完整性", "SKIP", "冊缺")
    bad = []
    for e in _jload(p).get("entries", []):
        f = via / e["file"]
        if not f.exists():
            bad.append(f"存證件缺:{e['file']}")
            continue
        act = e.get("active", "")
        if act and not act.startswith("("):
            if not list(via.rglob(act)) and not (f.parent / act).exists():
                bad.append(f"現役件缺:{act}")
    return _res("⑤ 存證冊完整性", "OK" if not bad else "FAIL", "; ".join(bad) or "全在位")


def c1_syntax_gate(via: Path = VIA) -> dict:
    p = via / "supportive modules" / "registry" / "VIA_Syntax_Gate_Register_v0100.json"
    if not p.exists():
        return _res("⑥ 語法版本閘冊", "SKIP", "冊缺")
    bad = []
    for e in _jload(p).get("entries", []):
        if not (via / e["file"]).exists():
            bad.append(f"閘件缺:{e['file']}")
        try:
            tuple(int(x) for x in e["python_min"].split("."))
        except Exception:
            bad.append(f"python_min 壞:{e.get('python_min')}")
    return _res("⑥ 語法版本閘冊", "OK" if not bad else "FAIL", "; ".join(bad) or "有效")


def c1_r2_residue(via: Path = VIA) -> dict:
    residue = []
    for sub in ("VRN", "VDF", "VAP"):
        p = _newest(via / "functional modules" / sub, f"{sub}_Param_Registry_v*.json")
        if p is None:
            continue
        for name, e in _jload(p).get("canonical", {}).items():
            r = str(e.get("ruling", ""))
            if not r.startswith("<") and ("OneDrive" in r or "C:\\\\" in r or "Downloads" in r):
                residue.append(f"{sub}.{name}")
    return _res("⑦ R2 寫死路徑殘留", "OK" if not residue else "FAIL", "; ".join(residue) or "0 殘留")


def c1_launcher_rule(via: Path = VIA) -> dict:
    bad = []
    for cmd in sorted((via / "bin").glob("*.cmd")):
        for line in cmd.read_text(encoding="utf-8", errors="replace").splitlines():
            low = line.strip().lower()
            if low.startswith("rem") or "dir /b" in low or "%%f" in line:
                continue
            if CMD_HARD_RX.search(low):
                bad.append(f"{cmd.name}")
                break
    return _res("⑧ 啟動器鐵律殘留", "OK" if not bad else "FAIL", "; ".join(bad) or "0 寫死")


# ── C2 壞環境黑名單守衛 ──────────────────────────────────────────
def _blacklist(via: Path = VIA) -> dict | None:
    p = _newest(via / "supportive modules" / "registry", "VIA_BadEnv_Blacklist_v*.json")
    return _jload(p) if p else None


def c2_root_check(via: Path = VIA) -> dict:
    bl = _blacklist(via)
    if bl is None:
        return _res("⑨ 現行根黑名單比對", "SKIP", "黑名單冊缺")
    cur = str(via).replace("/", "\\").lower()
    hits = [r["path"] for r in bl["blacklisted_roots"] if cur.startswith(r["path"].lower())]
    return _res("⑨ 現行根黑名單比對", "OK" if not hits else "FAIL",
                f"現行根 {via} · 黑名單 {len(bl['blacklisted_roots'])} 根 · 命中 {len(hits)}")


def c2_placeholder(via: Path = VIA) -> dict:
    zero = []
    for d, pat in ((via / "bin", "*.cmd"), (via / "bin", "*.py"),
                   (via / "supportive modules" / "registry", "*.py")):
        if not d.exists():
            continue
        for p in d.glob(pat):
            if p.stat().st_size == 0:
                zero.append(p.name)
    return _res("⑩ 活區 0-byte 占位檔", "OK" if not zero else "FAIL",
                "; ".join(zero) or "0 件(HZ-01)")


def c2_syspath(via: Path = VIA) -> dict:
    bad = [p for p in sys.path if "accelerator" in p.replace("\\", "/").split("/")[-1:]]
    bad += [p for p in sys.path
            if p.replace("\\", "/").rstrip("/").endswith("supportive modules/accelerator")]
    return _res("⑪ sys.path 無 accelerator/", "OK" if not bad else "FAIL",
                "; ".join(bad) or "FM-08 防線在位")


def c2_path_env(via: Path = VIA) -> dict:
    bl = _blacklist(via)
    if bl is None:
        return _res("⑫ PATH 黑名單前綴", "SKIP", "黑名單冊缺")
    entries = (os.environ.get("PATH") or "").split(os.pathsep)
    hits = [e for e in entries
            for r in bl["blacklisted_roots"] if e.lower().startswith(r["path"].lower())]
    if not any("\\" in e for e in entries):
        return _res("⑫ PATH 黑名單前綴", "SKIP", "非 Windows PATH(容器誠實;工作站波實測)")
    return _res("⑫ PATH 黑名單前綴", "OK" if not hits else "FAIL", "; ".join(hits[:3]) or "0 命中")


def c2_verb_targets(via: Path = VIA) -> dict:
    bl = _blacklist(via)
    if bl is None:
        return _res("⑬ bin 動詞執行標的", "SKIP", "黑名單冊缺")
    bad_files = {b["file"].replace("\\", "/") for b in bl["blacklisted_files"]}
    hits = []
    for cmd in sorted((via / "bin").glob("*.cmd")):
        t = cmd.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
        for bf in bad_files:
            if bf.split("/")[-1] in t:
                hits.append(f"{cmd.name}→{bf.split('/')[-1]}")
    return _res("⑬ bin 動詞執行標的", "OK" if not hits else "FAIL", "; ".join(hits) or "零黑件引用")


CHECKS = [c1_central_params, c1_canonical_residue, c1_etf_conflicts, c1_twoera,
          c1_evidence, c1_syntax_gate, c1_r2_residue, c1_launcher_rule,
          c2_root_check, c2_placeholder, c2_syspath, c2_path_env, c2_verb_targets]


def run() -> int:
    print("=== 衝突機制總哨兵+壞環境守衛(TOOL-107 批106)· 十三道 ===")
    results = []
    for fn in CHECKS:
        try:
            r = fn()
        except Exception as exc:
            r = _res(fn.__name__, "FAIL", f"{type(exc).__name__}: {str(exc)[:80]}")
        results.append(r)
        print(f"  [{r['state']:>4}] {r['name']} · {r['note'][:96]}")
    n_fail = sum(1 for r in results if r["state"] == "FAIL")
    n_warn = sum(1 for r in results if r["state"] == "WARN")
    n_skip = sum(1 for r in results if r["state"] == "SKIP")
    n_ok = len(results) - n_fail - n_warn - n_skip
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"CONFLICT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"schema": "via.conflict_guard.v1",
                               "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "results": results,
                               "counts": {"ok": n_ok, "warn": n_warn,
                                          "fail": n_fail, "skip": n_skip}},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {n_ok} · WARN {n_warn}(具名列管)· FAIL {n_fail} · SKIP {n_skip} · 存證 {out.name}")
    return 1 if n_fail else 0


# ── 十檢自測(沙盒零網路)────────────────────────────────────────
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        reg = sand / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (sand / "bin").mkdir()
        # 沙盒黑名單冊
        (reg / "VIA_BadEnv_Blacklist_v0100.json").write_text(json.dumps({
            "blacklisted_roots": [{"path": "C:\\\\old\\\\root", "reason": "t"}],
            "forbidden_exec_fragments": [], "env_hazards": [],
            "blacklisted_files": [{"file": "x/bad_evil.py", "reason": "t"}]}), encoding="utf-8")
        # ① 現行根未命中黑名單
        chk("① 根比對(未命中=OK)", c2_root_check(sand)["state"] == "OK")
        # ② 0-byte 占位偵測
        (sand / "bin" / "ok.cmd").write_text("@echo off\n", encoding="utf-8")
        chk("② 零占位=OK", c2_placeholder(sand)["state"] == "OK")
        (sand / "bin" / "ghost.cmd").write_text("", encoding="utf-8")
        chk("③ 占位檔=FAIL", c2_placeholder(sand)["state"] == "FAIL")
        # ④ 黑件引用偵測
        (sand / "bin" / "bad.cmd").write_text("py bad_evil.py\n", encoding="utf-8")
        chk("④ 黑件引用=FAIL", c2_verb_targets(sand)["state"] == "FAIL")
        # ⑤ 啟動器鐵律:寫死=FAIL、dir /b=OK
        (sand / "bin" / "hard.cmd").write_text('py "tool_v0100.py"\n', encoding="utf-8")
        chk("⑤ 寫死版號=FAIL", c1_launcher_rule(sand)["state"] == "FAIL")
        for f in ("bad.cmd", "hard.cmd", "ghost.cmd"):
            (sand / "bin" / f).write_text("rem clean\n", encoding="utf-8")
        chk("⑥ 清乾淨=OK", c1_launcher_rule(sand)["state"] == "OK"
            and c2_verb_targets(sand)["state"] == "OK")
        # ⑦ canonical 未裁殘量沙盒
        vdf = sand / "functional modules" / "VDF"
        vdf.mkdir(parents=True)
        (vdf / "VDF_Param_Registry_v0100.json").write_text(json.dumps({
            "params": [{"name": "A", "value": "1"}, {"name": "A", "value": "2"}],
            "canonical": {}}), encoding="utf-8")
        chk("⑦ 未裁殘量=FAIL", c1_canonical_residue(sand)["state"] == "FAIL")
        (vdf / "VDF_Param_Registry_v0101.json").write_text(json.dumps({
            "params": [{"name": "A", "value": "1"}, {"name": "A", "value": "2"}],
            "canonical": {"A": {"ruling": "2"}}}), encoding="utf-8")
        chk("⑧ 裁畢(glob 新版)=OK", c1_canonical_residue(sand)["state"] == "OK")
        # ⑨ R2 殘留沙盒
        (vdf / "VDF_Param_Registry_v0102.json").write_text(json.dumps({
            "params": [], "canonical": {"P": {"ruling": "'C:\\\\\\\\Users\\\\\\\\x\\\\\\\\OneDrive\\\\\\\\y'"}}}), encoding="utf-8")
        chk("⑨ R2 殘留=FAIL", c1_r2_residue(sand)["state"] == "FAIL")
    # ⑩ 實樹全巡檢煙測(唯讀;不得拋例外)
    try:
        rc = run()
        chk("⑩ 實樹巡檢煙測(rc0=無紅)", rc == 0)
    except Exception as exc:
        chk("⑩ 實樹巡檢煙測", False, str(exc)[:60])
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 衝突哨兵 · 十檢自測(沙盒零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
