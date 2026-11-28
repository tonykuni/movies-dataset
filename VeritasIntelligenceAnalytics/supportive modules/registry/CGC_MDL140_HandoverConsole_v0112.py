#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL140_HandoverConsole v0112 — 薄尾(v0100–v0111 一字不動):有退役清冊、而且搬過去的檔雜湊對得上的,不再算 FILE_REMOVED

實錄(2026-11-27 交接閘):FILE_REMOVED 紅 900 列(另有他系統 399 列)。逐列核對:全部是 2026-11-23 / 11-25 `via-prune --prove --apply`
     的退役搬移(以搬代刪);9 本 RETIRE_MANIFEST 記著 原路徑 → 新路徑 → sha256,搬過去的檔都在、雜湊全部相符。
     本體的判法是「上次存檔點有、現在原路徑沒有 = FILE_REMOVED 紅」,不看退役清冊,所以每搬一批就多一批紅,而且永遠清不掉。
本版只補這一條(VCGC-REQ281):
  FILE_REMOVED 的那個原路徑,在任何一本 RETIRE_MANIFEST 的 moved 裡,而且清冊寫的新路徑上有檔、內容雜湊等於清冊記的
  (原樣位元組,或先把 CRLF 換成 LF 再算;兩種有一種對就算) → 這一列不算紅,搬到 report["retired_by_manifest_rows"](一筆不刪),
  summary 多一個數 retired_by_manifest。
  其餘照舊紅:不在任何清冊 · 清冊有但新路徑沒有檔 · 檔在但雜湊不對 · 清冊讀不到。
  判在「分系統」之前做,所以 VCGC 的列與他系統只讀摘要用同一把尺。其餘全部照 v0111 / 前版鏈。不改任何冊、不搬任何檔。零網路。不用 TA-Lib。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0112"
VERBS = ("check", "checkpoint", "test", "daily", "--selftest")     # 動詞照前版;本版沒有新增
RETIRE_GLOB = "functional modules/VIA_RetiredEngines/prune_*/RETIRE_MANIFEST.json"
RULE = "FILE_REMOVED"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE


def _chain() -> list:
    out, m = [], PRIOR
    while m is not None and m not in out:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def _defined_in(m, name: str) -> bool:
    fn = vars(m).get(name)
    return callable(fn) and getattr(fn, "__globals__", None) is vars(m)


SCOPE_HOME = next(m for m in _chain() if _defined_in(m, "apply_system_scope"))     # v0111:它的 audit 讀自己全域的 _PREV_AUDIT,再分系統
_INNER = vars(SCOPE_HOME)["_PREV_AUDIT"]                                           # 分系統之前的那一支(v0110 的)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _read_manifest(p: Path):
    """一本清冊的內容;讀不到或不是 JSON 回 None(那一本管的列就照舊紅)。"""
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_manifests(via) -> dict:
    """讀全部 RETIRE_MANIFEST:{原路徑: [(新路徑, sha256, 批名), …]}。讀不到 / 形狀不對的那一本略過(那一本管的列就照舊紅)。"""
    out: dict = {}
    for p in sorted(Path(via).glob(RETIRE_GLOB)):
        j = _read_manifest(p)
        moved = j.get("moved") if isinstance(j, dict) else None
        for x in moved if isinstance(moved, list) else []:
            if isinstance(x, dict) and all(isinstance(x.get(k), str) and x.get(k) for k in ("from", "to", "sha256")):
                out.setdefault(x["from"], []).append((x["to"], x["sha256"].lower(), str(j.get("batch") or p.parent.name)))
    return out


def _hashes(p: Path) -> tuple:
    raw = p.read_bytes()
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def retired_proof(via, rel: str, manifests: dict):
    """rel 這個原路徑有沒有「清冊 + 新路徑有檔 + 雜湊相符」的證明。有 → (新路徑, 批名);沒有 → None。"""
    root = Path(via).resolve()
    for to, want, batch in manifests.get(rel, []):
        q = (root / to).resolve()
        if root not in q.parents:
            continue                                   # 清冊寫到 VIA 根以外的路徑:不認
        if q.is_file() and want in _hashes(q):
            return to, batch
    return None


def apply_retire_manifests(report: dict, via) -> dict:
    """把有退役證明的 FILE_REMOVED 列搬到 retired_by_manifest_rows;燈與驗收燈照剩下的列重算(同 v0111 的式子)。"""
    rows = report.get("rows") or []
    if not any(r.get("rule") == RULE for r in rows):
        report.setdefault("retired_by_manifest_rows", [])
        report.setdefault("summary", {})["retired_by_manifest"] = 0
        return report
    manifests = load_manifests(via)
    keep, moved = [], []
    for r in rows:
        proof = retired_proof(via, r["detail"], manifests) if r.get("rule") == RULE and isinstance(r.get("detail"), str) else None
        if proof:
            moved.append({"rule": RULE, "detail": r["detail"], "to": proof[0], "batch": proof[1]})
        else:
            keep.append(r)
    lamps = [r.get("lamp") for r in keep]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = keep
    report["retired_by_manifest_rows"] = moved
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if report.get("pending") or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    s = report.setdefault("summary", {})
    s["findings"] = len(keep)
    s["retired_by_manifest"] = len(moved)
    return report


def inner_audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    return apply_retire_manifests(_INNER(via, policy, baseline, require_baseline), via)


SCOPE_HOME._PREV_AUDIT = inner_audit            # v0111 的 audit 以它自己的模組全域叫這個名字(分系統之前)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import subprocess
    import tempfile
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] " + ENGINE + " 自測開始(暫存樹 · 不改任何冊 · 零網路)", flush=True)
    global _INNER
    with tempfile.TemporaryDirectory(prefix="mdl140_112_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        ret = via / "functional modules" / "VIA_RetiredEngines"

        def put(rel, data: bytes):
            p = via / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return hashlib.sha256(data).hexdigest()
        lf = b"X = 1\nY = 2\n"
        b1 = "functional modules/VIA_RetiredEngines/prune_A/"
        b2 = "functional modules/VIA_RetiredEngines/prune_B/"
        h_ok = put(b1 + "supportive modules/registry/Old_MDL001_A_v0100.py", lf)
        h_lf = hashlib.sha256(lf).hexdigest()
        put(b1 + "supportive modules/registry/Old_MDL002_B_v0100.py", lf.replace(b"\n", b"\r\n"))        # 主機 CRLF 取出;清冊記的是 LF 的雜湊
        put(b1 + "supportive modules/registry/Old_MDL003_C_v0100.py", b"CHANGED\n")                      # 搬過去之後內容被改
        h_vdf = put(b2 + "functional modules/VDF/VDF_ENG900_Old_v0100.py", b"V = 1\n")
        (ret / "prune_A").mkdir(parents=True, exist_ok=True)
        (ret / "prune_A" / "RETIRE_MANIFEST.json").write_text(json.dumps({"batch": "prune_A", "moved": [
            {"from": "supportive modules/registry/Old_MDL001_A_v0100.py", "to": b1 + "supportive modules/registry/Old_MDL001_A_v0100.py", "sha256": h_ok},
            {"from": "supportive modules/registry/Old_MDL002_B_v0100.py", "to": b1 + "supportive modules/registry/Old_MDL002_B_v0100.py", "sha256": h_lf},
            {"from": "supportive modules/registry/Old_MDL003_C_v0100.py", "to": b1 + "supportive modules/registry/Old_MDL003_C_v0100.py", "sha256": h_lf},
            {"from": "supportive modules/registry/Old_MDL004_D_v0100.py", "to": b1 + "supportive modules/registry/Old_MDL004_D_v0100.py", "sha256": h_lf},
            {"from": "supportive modules/registry/Old_MDL006_F_v0100.py", "to": "../outside/Old_MDL006_F_v0100.py", "sha256": h_lf},
            {"from": "只有兩欄", "to": "x"}, "壞列"]}, ensure_ascii=False), encoding="utf-8")
        (ret / "prune_B").mkdir(parents=True, exist_ok=True)
        (ret / "prune_B" / "RETIRE_MANIFEST.json").write_text(json.dumps({"batch": "prune_B", "moved": [
            {"from": "functional modules/VDF/VDF_ENG900_Old_v0100.py", "to": b2 + "functional modules/VDF/VDF_ENG900_Old_v0100.py", "sha256": h_vdf.upper()}]}), encoding="utf-8")
        (ret / "prune_C").mkdir(parents=True, exist_ok=True)
        (ret / "prune_C" / "RETIRE_MANIFEST.json").write_text("{壞掉", encoding="utf-8")
        (Path(td) / "outside").mkdir()
        (Path(td) / "outside" / "Old_MDL006_F_v0100.py").write_bytes(lf)
        names = ["A", "B", "C", "D", "E", "F"]
        paths = ["supportive modules/registry/Old_MDL00%d_%s_v0100.py" % (i + 1, s) for i, s in enumerate(names)]

        def fake_report():
            rows = [{"lamp": "RED", "rule": RULE, "detail": p} for p in paths]
            rows += [{"lamp": "RED", "rule": RULE, "detail": "functional modules/VDF/VDF_ENG900_Old_v0100.py"},
                     {"lamp": "RED", "rule": RULE, "detail": {"不是": "字串"}},
                     {"lamp": "YELLOW", "rule": "REQ_CHANGED", "detail": "VCGC-REQ001"}]
            return {"rows": rows, "pending": [], "lamp": "RED", "closeout_lamp": "RED", "summary": {"findings": len(rows)}}
        m = load_manifests(via)
        chk("① 讀清冊:好的兩本 6 個原路徑 · 壞掉的那一本與形狀不對的列略過", len(m) == 6 and "只有兩欄" not in m, sorted(m)[:8])
        rep = apply_retire_manifests(fake_report(), via)
        left = [r["detail"] for r in rep["rows"] if r["rule"] == RULE and isinstance(r["detail"], str)]
        gone = [r["detail"] for r in rep["retired_by_manifest_rows"]]
        chk("② 清冊有 + 新路徑有檔 + 雜湊相符 → 不算紅,搬到 retired_by_manifest_rows(帶新路徑與批名)",
            paths[0] in gone and rep["retired_by_manifest_rows"][0]["batch"] == "prune_A" and rep["summary"]["retired_by_manifest"] == 3, gone)
        chk("③ 新路徑上的檔是 CRLF、清冊記 LF 的雜湊 → 照樣認(先換成 LF 再算);清冊雜湊大小寫不拘", paths[1] in gone and "functional modules/VDF/VDF_ENG900_Old_v0100.py" in gone, gone)
        chk("④ 反控:搬過去之後內容被改(雜湊不對)→ 照舊紅", paths[2] in left, left)
        chk("⑤ 反控:清冊有但新路徑沒有檔 → 照舊紅;不在任何清冊 → 照舊紅", paths[3] in left and paths[4] in left, left)
        chk("⑥ 反控:清冊把新路徑寫到 VIA 根以外 → 不認,照舊紅", paths[5] in left, left)
        chk("⑦ 別的規則一列不動 · 細節不是字串的列不動 · 燈照剩下的列重算 · 列數 = 剩下 + 搬開",
            any(r["rule"] == "REQ_CHANGED" for r in rep["rows"]) and any(isinstance(r["detail"], dict) for r in rep["rows"])
            and rep["lamp"] == "RED" and rep["summary"]["findings"] == len(rep["rows"]) and len(rep["rows"]) + len(gone) == 9, (rep["lamp"], len(rep["rows"]), len(gone)))
        only = {"rows": [{"lamp": "RED", "rule": RULE, "detail": paths[0]}], "pending": [], "summary": {}}
        r_only = apply_retire_manifests(only, via)
        r_pend = apply_retire_manifests({"rows": [{"lamp": "RED", "rule": RULE, "detail": paths[0]}], "pending": [{"id": "x"}], "summary": {}}, via)
        r_none = apply_retire_manifests({"rows": [{"lamp": "YELLOW", "rule": "REQ_CHANGED", "detail": "x"}], "pending": [], "lamp": "YELLOW", "closeout_lamp": "YELLOW", "summary": {"findings": 1}}, via)
        chk("⑧ 唯一的一列被搬開 → 燈綠、驗收燈綠;還有待辦 → 驗收燈黃;沒有 FILE_REMOVED 的報告原樣(只多 0 的計數)",
            r_only["lamp"] == "GREEN" and r_only["closeout_lamp"] == "GREEN" and r_pend["lamp"] == "GREEN" and r_pend["closeout_lamp"] == "YELLOW"
            and r_none["lamp"] == "YELLOW" and len(r_none["rows"]) == 1 and r_none["summary"] == {"findings": 1, "retired_by_manifest": 0},
            (r_only["lamp"], r_pend["closeout_lamp"], r_none["summary"]))
        # 走真正的入口:本體讀的 audit → v0111 分系統 → 本版
        keep_inner, keep_scope = _INNER, os.environ.pop("VIA_HANDOFF_SCOPE", None)
        _INNER = lambda via_, policy, baseline, require_baseline: fake_report()        # noqa: E731
        try:
            via_entry = vars(BASE)["audit"](via)
        finally:
            _INNER = keep_inner
            if keep_scope is not None:
                os.environ["VIA_HANDOFF_SCOPE"] = keep_scope
        mine = [r["detail"] for r in via_entry["rows"] if r["rule"] == RULE and isinstance(r["detail"], str)]
        chk("⑨ 從本體讀的 audit 打進去:VCGC 的列只剩真的紅 4 支 · VDF 那一支有證明,不進他系統的紅 · 計數在 summary",
            sorted(mine) == sorted([paths[2], paths[3], paths[4], paths[5]]) and not [r for r in via_entry.get("peer_rows", []) if r["rule"] == RULE]
            and via_entry["summary"].get("retired_by_manifest") == 3 and via_entry["summary"]["findings"] == len(via_entry["rows"]), (mine, via_entry["summary"]))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 本檔沒有寫檔 / 搬檔的呼叫",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP|VTK)", src, re.M)
        and len(re.findall(r"\.write_text\(|\.write_bytes\(|os\.replace\(|shutil\.|\.rename\(|\.unlink\(", src.split("def selftest()")[0])) == 0, VIA_ACCEL is not None)
    lost = [x for x in dir(PRIOR) if not x.startswith("_") and callable(getattr(PRIOR, x)) and not hasattr(sys.modules[__name__], x)]
    chk("⑪ 前版公開名稱都還拿得到(audit · checkpoint · run_case 在內)", not lost and all(callable(getattr(sys.modules[__name__], k)) for k in ("audit", "checkpoint", "run_case")), lost[:6])
    prc = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=900, env=dict(os.environ, VIA_FROM_VCGC="YES")).returncode
    chk("⑫ 前版 " + PRIOR_PATH.name + " 自測照過(子行程,沒載入本版)", prc == 0, "rc " + str(prc))
    print("[計] " + ENGINE + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · " + ("PASS" if n["bad"] == 0 else "FAIL"))
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
