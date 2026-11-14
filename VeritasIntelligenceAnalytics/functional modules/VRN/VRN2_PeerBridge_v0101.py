"""VRN2_PeerBridge v0101 — 薄尾(v0100 一字不改):借用釘指紋算覆蓋 · 桌機 prove 實跑 · 整合冊一能力一主人。

操作員 2026-11-10 令「VRN 臨門一腳 · VRN-1 VRN-2 部分功能強化整合 · 可整合不可丟失不可重複」。
v0100 已把 VRN-1 有、VRN-2 沒有的 9 項能力登進借用冊並釘了 sha256,但矩陣仍算 GAP、
readiness 永遠黃、integrate 只印「尚未實作」—— 這就是差的那一腳。本版只補這塊:

1. gap:GAP 列若借用冊有釘指紋、現檔 sha 相符、ast 剖析過、有 selftest → 轉 BORROWED(附證據)。
   只做靜態(讀檔 + ast.parse),**不執行 VRN-1 的程式**。
2. prove(桌機跑):逐支在子行程、暫存夾、PYTHONDONTWRITEBYTECODE=1 跑 VRN-1 工具自己的 selftest,
   前後比 VRN-1 的 git status(要一字不差),收據寫 VIA_Reports/vrn2/peerbridge/(不入倉)。
3. readiness:GAP(扣掉 BORROWED)= 0 且 REVIEW = 0 才可能綠;BORROWED 沒有「同指紋的 prove 全過收據」
   照實黃(靜態過 ≠ 實跑過)。
4. integrate:寫 VRN2_IntegrationBook(只增,不覆蓋)—— 23 項能力每項恰一個主人
   (MATCH = VRN-2 自己的引擎 · BORROWED = VRN-1 釘指紋借用,不複製檔)。
   有 GAP / REVIEW / 一能力多主人 / 一檔多能力衝突 → 拒絕。
5. 自測:先清 VIA_VRN1_ROOT 並把 HOME 指到沙盒再跑 v0100 自測(v0100 在桌機設了環境變數會誤判 FAIL)。

VRN-1 外倉只讀(L123):本檔不寫 VRN-1 的任何檔,不把 VRN-1 的檔複製進本倉。
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

import argparse
import ast
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
PRIOR = "VRN2_PeerBridge_v0100.py"
INTEGRATION_BOOK_REL = "functional modules/VRN/ssot/VRN2_IntegrationBook_v0100.json"
PROVE_DIR_REL = "VIA_Reports/vrn2/peerbridge"
CONTRACT_GLOB = "supportive modules/registry/VIA_SystemInterface_Contract_SSOT_v*.json"
# 依法不借:VRN-1 自帶、但在 VRN-2 由他系統經契約提供的能力(借進來 = 與契約提供者重複)。
# ast.id:VRN-1 自己給模組編號並寫進原始碼;VRN-2 的編號只由 VCGC 發(L122 / L125),經 IFC-003。
BY_CONTRACT = {
    "ast.id": {"ifc_id": "IFC-003", "provider": "VCGC",
               "why": "VRN-2 的模組編號只由 VCGC 發(L122 / L125 · IFC-003 空號 → VCGC 發號);"
                      "借 VRN-1 自編號引擎會與 VCGC 編號重複,且它會寫進原始碼"},
}
PROVE_TIMEOUT_S = 300


def _load_prior():
    p = Path(__file__).resolve().with_name(PRIOR)
    spec = importlib.util.spec_from_file_location("VRN2_PeerBridge_v0100", p)
    mod = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


B = _load_prior()
# 前版公開名稱全部轉接(TAILAPI:尾版不少於前版)
for _n in dir(B):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(B, _n)

_base_gap_matrix = B.gap_matrix
_base_selftest = B.selftest


def active_contracts(via: Path) -> dict:
    """契約冊尾版裡 ACTIVE 的 IFC 號 → 契約(只讀)。"""
    files = sorted(via.glob(CONTRACT_GLOB))
    if not files:
        return {}
    try:
        j = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {c.get("ifc_id"): c for c in j.get("contracts", [])
            if c.get("ifc_id") and c.get("state") == "ACTIVE"}


# ─────────────────────────────────────────────────────────────────────────────
# 借用冊 → 靜態驗(只讀檔 + ast.parse,不執行)
# ─────────────────────────────────────────────────────────────────────────────
def borrow_book(via: Path) -> dict:
    p = via / B.BORROW_BOOK_REL
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def static_check(path: Path) -> dict:
    """讀檔 + ast.parse:有沒有 selftest / main。不 import、不執行。"""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except (OSError, SyntaxError, ValueError) as e:
        return {"ast_ok": False, "error": f"{type(e).__name__}: {e}"[:160]}
    names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return {"ast_ok": True, "has_selftest": "selftest" in names, "has_main": "main" in names,
            "cli_selftest": "selftest" in src}


def gap_matrix(via: Path) -> dict:
    m = _base_gap_matrix(via)
    book = borrow_book(via)
    pins = {e["tool_id"]: e for e in book.get("entries", []) if e.get("vrn1_sha256")}
    vrn1, _ = B.find_vrn1(via)
    ifc = active_contracts(via)
    for r in m["rows"]:
        if r["state"] != "GAP":
            continue
        bc = BY_CONTRACT.get(r["cap"])
        if bc:
            c = ifc.get(bc["ifc_id"])
            if c and bc["provider"] in (c.get("provider") or []):
                r["state"] = "BY_CONTRACT"
                r["evidence"] = [{"ifc_id": bc["ifc_id"], "provider": bc["provider"],
                                  "contract_version": c.get("version"), "why": bc["why"]}]
            else:
                r["borrow_why_not"] = f"依法由 {bc['provider']} 經 {bc['ifc_id']} 提供,但契約冊沒有 ACTIVE 的 {bc['ifc_id']}"
            continue
        e = pins.get(r["cap"])
        if not e or vrn1 is None:
            continue
        path = vrn1 / B.VRN1_ENGINE_REL / r["vrn1_engine"]
        if not path.is_file():
            r["borrow_why_not"] = "VRN-1 側檔不在"
            continue
        now = B.sha256(path)
        if now != e["vrn1_sha256"]:
            r["borrow_why_not"] = f"指紋變了:冊 {e['vrn1_sha256'][:12]} · 現 {now[:12]}(要重跑 fill 出新版借用冊)"
            continue
        sc = static_check(path)
        if not (sc.get("ast_ok") and sc.get("has_selftest")):
            r["borrow_why_not"] = f"靜態驗不過:{sc}"
            continue
        r["state"] = "BORROWED"
        r["evidence"] = [{"borrow_book": B.BORROW_BOOK_REL, "vrn1_engine": r["vrn1_engine"],
                          "sha256": now, "static": sc}]
    m["counts"] = {s: sum(1 for r in m["rows"] if r["state"] == s)
                   for s in ("MATCH", "BORROWED", "BY_CONTRACT", "REVIEW", "GAP")}
    m["version"] = VERSION
    return m


def print_gap(m: dict) -> None:
    print(f"[能力差異矩陣 {VERSION}] VRN-1 能力 {len(m['rows'])} 項 · 掃過 VRN-2 檔 {m['vrn2_files_scanned']}")
    for r in m["rows"]:
        ev = r["evidence"][0] if r.get("evidence") else {}
        where = ev.get("file") or (f"契約 {ev['ifc_id']} ← {ev['provider']}" if ev.get("ifc_id") else None) or (
            f"借 {ev.get('vrn1_engine')} @{ev.get('sha256', '')[:10]}" if ev else
                                   r.get("borrow_why_not") or "找過:" + "/".join(r["looked_for"]))
        print(f"{r['state']:<9}{r['cap']:<20}{r['vrn1_engine'][:40]:<42}{where}")
    c = m["counts"]
    print(f"\n[判決] MATCH {c['MATCH']} · BORROWED {c['BORROWED']} · BY_CONTRACT {c['BY_CONTRACT']} · "
          f"REVIEW {c['REVIEW']} · GAP {c['GAP']}")
    print("[誠實] BORROWED = 借用冊釘指紋 + 現檔相符 + ast 靜態過;**沒在本機實跑**,實跑看 prove 收據。")


def cmd_gap(args) -> int:
    m = gap_matrix(B.via_root())
    if getattr(args, "json", False):
        print(json.dumps(m, ensure_ascii=False, indent=1))
    else:
        print_gap(m)
    return 0 if m["counts"]["GAP"] == 0 and m["counts"]["REVIEW"] == 0 else 1


# ─────────────────────────────────────────────────────────────────────────────
# prove(桌機跑):VRN-1 工具自己的 selftest,子行程 · 暫存夾 · 不留 bytecode
# ─────────────────────────────────────────────────────────────────────────────
def _git_status(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=60)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _selftest_cmd(path: Path, sc: dict) -> list[str]:
    if sc.get("has_main") and sc.get("cli_selftest"):
        return [sys.executable, str(path), "selftest"]
    code = ("import importlib.util,sys;sys.dont_write_bytecode=True;"
            "s=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(s);"
            "s.loader.exec_module(m);r=m.selftest();"
            "sys.exit(0 if (r is None or r is True or (type(r) is int and r == 0)) else 1)")
    return [sys.executable, "-c", code, str(path)]


def prove(via: Path, vrn1: Path | None = None, timeout: int = PROVE_TIMEOUT_S) -> dict:
    m = gap_matrix(via)
    if vrn1 is None:
        vrn1, why = B.find_vrn1(via)
        if vrn1 is None:
            return {"lamp": "RED", "why": why, "rows": []}
    before = _git_status(vrn1)
    rows = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for r in m["rows"]:
        if r["state"] != "BORROWED":
            continue
        path = vrn1 / B.VRN1_ENGINE_REL / r["vrn1_engine"]
        sc = r["evidence"][0]["static"]
        cmd = _selftest_cmd(path, sc)
        td = tempfile.mkdtemp(prefix="vrn2_prove_")
        try:
            p = subprocess.run(cmd, cwd=td, env=env, capture_output=True, text=True, timeout=timeout)
            rc, tail = p.returncode, [ln for ln in (p.stdout + p.stderr).splitlines() if ln.strip()][-2:]
        except subprocess.TimeoutExpired:
            rc, tail = 124, [f"逾時 {timeout}s"]
        finally:
            shutil.rmtree(td, ignore_errors=True)
        rows.append({"cap": r["cap"], "vrn1_engine": r["vrn1_engine"],
                     "sha256": r["evidence"][0]["sha256"], "rc": rc,
                     "result": "PASS" if rc == 0 else "FAIL", "tail": tail})
    after = _git_status(vrn1)
    untouched = before is not None and before == after
    ok = rows and all(x["result"] == "PASS" for x in rows) and untouched
    return {"schema": "via.vrn2.peerbridge.prove/1", "version": VERSION, "ts": B.utc(),
            "vrn1_root": str(vrn1), "vrn1_untouched": untouched,
            "lamp": "GREEN" if ok else ("YELLOW" if not rows else "RED"), "rows": rows}


def latest_prove(via: Path) -> dict | None:
    d = via / PROVE_DIR_REL
    files = sorted(d.glob("VRN2_Prove_*.json")) if d.is_dir() else []
    for f in reversed(files):
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return None


def cmd_prove(args) -> int:
    via = B.via_root()
    rec = prove(via)
    for x in rec.get("rows", []):
        print(f"  {x['result']:<5}{x['cap']:<20}{x['vrn1_engine'][:40]:<42}rc {x['rc']} · {' | '.join(x['tail'])[:90]}")
    print(f"[prove] {rec['lamp']} · VRN-1 樹未被動到:{rec.get('vrn1_untouched')} · {rec.get('why', '')}")
    if rec.get("rows"):
        out = via / PROVE_DIR_REL / f"VRN2_Prove_{rec['ts'].replace(':', '').replace('-', '')}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"[收據] {out}")
    return 0 if rec["lamp"] == "GREEN" else 1


# ─────────────────────────────────────────────────────────────────────────────
# readiness / integrate
# ─────────────────────────────────────────────────────────────────────────────
def readiness(via: Path) -> dict:
    m = gap_matrix(via)
    mf = B.build_manifest(via)
    vrn1, why = B.find_vrn1(via)
    blockers, notes = [], []
    if m["counts"]["GAP"]:
        blockers.append(f"VRN-2 仍有 {m['counts']['GAP']} 項能力缺口(GAP,沒有釘指紋的借用)")
    if m["counts"]["REVIEW"]:
        blockers.append(f"{m['counts']['REVIEW']} 項待操作員判(REVIEW)—— 不替他判")
    if mf["not_lendable"]:
        blockers.append(f"VRN-2 借不出去的工具 {len(mf['not_lendable'])} 項:{mf['not_lendable']}")
    if vrn1 is None:
        blockers.append("找不到 VRN-1:" + why)
    borrowed = {r["cap"]: r["evidence"][0]["sha256"] for r in m["rows"] if r["state"] == "BORROWED"}
    proven = False
    if borrowed:
        pr = latest_prove(via) or {}
        got = {x["cap"]: x for x in pr.get("rows", [])}
        proven = (pr.get("vrn1_untouched") is True and
                  all(c in got and got[c]["result"] == "PASS" and got[c]["sha256"] == s
                      for c, s in borrowed.items()))
        if not proven:
            notes.append(f"借用 {len(borrowed)} 支只過靜態驗(指紋 + ast);同指紋的 prove 全過收據沒有 → 桌機跑 prove")
    lamp = "RED" if vrn1 is None else ("GREEN" if not blockers and (proven or not borrowed) else "YELLOW")
    return {"schema": B.SCHEMA_ID, "version": VERSION, "ts": B.utc(), "lamp": lamp,
            "blockers": blockers, "notes": notes, "gap_counts": m["counts"],
            "not_lendable": mf["not_lendable"], "vrn1_found": vrn1 is not None,
            "borrowed_proven": proven}


def cmd_readiness(args) -> int:
    r = readiness(B.via_root())
    print(f"[整合就緒燈 {VERSION}] {r['lamp']} · {r['gap_counts']}")
    for b in r["blockers"]:
        print(f"  · 擋:{b}")
    for n in r["notes"]:
        print(f"  · 註:{n}")
    return 0 if r["lamp"] == "GREEN" else 1


def integration_book(via: Path) -> dict:
    """23 項能力 → 每項恰一個主人;同一 VRN-2 檔被當多項能力的唯一證據時列出(要人看,不擋)。"""
    m = gap_matrix(via)
    entries, owners = [], {}
    for r in m["rows"]:
        ev = r["evidence"][0] if r.get("evidence") else {}
        if r["state"] == "MATCH":
            owner = {"system": "VRN-2", "kind": "OWN", "file": ev.get("file")}
        elif r["state"] == "BORROWED":
            owner = {"system": "VRN-1", "kind": "BORROWED_PINNED", "engine": r["vrn1_engine"],
                     "sha256": ev.get("sha256"), "via": f"VRN2_PeerBridge_{VERSION}.py borrow {r['cap']}"}
        elif r["state"] == "BY_CONTRACT":
            owner = {"system": ev.get("provider"), "kind": "BY_CONTRACT", "ifc_id": ev.get("ifc_id"),
                     "why": ev.get("why")}
        else:
            owner = None
        entries.append({"cap": r["cap"], "what": r["what"], "state": r["state"], "owner": owner})
        if owner and owner.get("file"):
            owners.setdefault(owner["file"], []).append(r["cap"])
    caps = [e["cap"] for e in entries]
    problems = []
    dup_caps = sorted({c for c in caps if caps.count(c) > 1})
    if dup_caps:
        problems.append(f"同一能力出現多次:{dup_caps}")
    lost = [e["cap"] for e in entries if e["owner"] is None]
    if lost:
        problems.append(f"沒有主人(會丟失):{lost}")
    shared = {f: cs for f, cs in owners.items() if len(cs) > 1}
    return {"schema": "via.vrn2.integrationbook/1", "version": "v0100", "built_by": f"VRN2_PeerBridge_{VERSION}",
            "ts": B.utc(), "law": "可整合 · 不可丟失 · 不可重複:一能力一主人;借用不複製檔;VRN-1 只讀(L123)",
            "counts": m["counts"], "total": len(entries), "entries": entries,
            "shared_evidence_files": shared, "problems": problems}


def cmd_integrate(args) -> int:
    via = B.via_root()
    book = integration_book(via)
    r = readiness(via)
    print(f"[整合冊] 能力 {book['total']} · {book['counts']} · 問題 {len(book['problems'])}")
    for p in book["problems"]:
        print(f"  [擋] {p}")
    for f, cs in book["shared_evidence_files"].items():
        print(f"  [看] 同一檔當 {len(cs)} 項能力的證據:{f} ← {cs}")
    if book["problems"] or r["blockers"]:
        for b in r["blockers"]:
            print(f"  [擋] {b}")
        print("[拒絕整合] 不可丟失 / 不可重複 沒過,或就緒燈有擋。")
        return 1
    book["readiness"] = {"lamp": r["lamp"], "notes": r["notes"], "borrowed_proven": r["borrowed_proven"]}
    if not getattr(args, "apply", False):
        print(f"[預覽] 就緒燈 {r['lamp']};加 --apply 寫 {INTEGRATION_BOOK_REL}(只增,不覆蓋)")
        return 0
    out = via / INTEGRATION_BOOK_REL
    if out.exists():
        print(f"[不覆蓋] {INTEGRATION_BOOK_REL} 已存在 —— 只增不減,要換版請出新版號檔")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"[寫入] {INTEGRATION_BOOK_REL} · 就緒燈 {r['lamp']}" + (" · " + r["notes"][0] if r["notes"] else ""))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# 自測
# ─────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def ck(name, cond, note=""):
        checks.append((name, bool(cond), note))

    saved = {k: os.environ.get(k) for k in ("VIA_VRN1_ROOT", "HOME", "USERPROFILE")}
    tmp = Path(tempfile.mkdtemp(prefix="vrn2_peerbridge_v0101_"))
    try:
        # ① 環境隔離後跑 v0100 自測(桌機設了 VIA_VRN1_ROOT 不再誤判)
        os.environ.pop("VIA_VRN1_ROOT", None)
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(tmp / "home")
        (tmp / "home").mkdir()
        rc = _base_selftest()
        ck("v0100 自測在隔離環境全過", rc == 0, f"rc {rc}")

        # 夾具:假 VIA + 假 VRN-1(全是本自測自己寫的檔)
        via = tmp / "w" / "via"
        (via / "supportive modules").mkdir(parents=True)
        (via / "functional modules" / "VRN").mkdir(parents=True)
        v1 = tmp / "w" / "via-vdf-vrn"
        eng_dir = v1 / B.VRN1_ENGINE_REL
        eng_dir.mkdir(parents=True)
        good = eng_dir / "VRN_Lock_v0100.py"
        good.write_text('"""fake"""\nimport sys\n\ndef selftest():\n    return 0\n\n'
                        'def main(argv=None):\n    return selftest()\n\n'
                        'if __name__ == "__main__":\n    sys.exit(main(sys.argv[1:]))  # selftest\n',
                        encoding="utf-8")
        bad = eng_dir / "VRN_TruthMatrix_v0100.py"
        bad.write_text('"""fake bad"""\ndef selftest():\n    return 1\n', encoding="utf-8")
        nost = eng_dir / "VRN_RunCache_v0100.py"
        nost.write_text('"""no selftest"""\nX = 1\n', encoding="utf-8")
        os.environ["VIA_VRN1_ROOT"] = str(v1)
        ssot = via / B.BORROW_BOOK_REL
        ssot.parent.mkdir(parents=True, exist_ok=True)
        ssot.write_text(json.dumps({"entries": [
            {"tool_id": "prove.lock", "vrn1_sha256": B.sha256(good)},
            {"tool_id": "truth.matrix", "vrn1_sha256": B.sha256(bad)},
            {"tool_id": "run.cache", "vrn1_sha256": B.sha256(nost)},
            {"tool_id": "temp.store", "vrn1_sha256": "0" * 64},
        ]}), encoding="utf-8")
        (eng_dir / "VRN_TempStore_v0100.py").write_text("def selftest():\n    return 0\n", encoding="utf-8")

        st0 = {r["cap"]: r for r in gap_matrix(via)["rows"]}
        ck("ast.id 契約冊沒有 → 仍 GAP 並說明", st0["ast.id"]["state"] == "GAP"
           and "IFC-003" in st0["ast.id"].get("borrow_why_not", ""))
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True, exist_ok=True)
        (reg / "VIA_SystemInterface_Contract_SSOT_v0101.json").write_text(json.dumps({"contracts": [
            {"ifc_id": "IFC-003", "state": "ACTIVE", "provider": ["VCGC"], "version": "v1.0"}]}), encoding="utf-8")
        m = gap_matrix(via)
        st = {r["cap"]: r for r in m["rows"]}
        ck("ast.id 有 ACTIVE IFC-003(VCGC)→ BY_CONTRACT", st["ast.id"]["state"] == "BY_CONTRACT", st["ast.id"]["state"])
        ck("釘指紋 + 相符 + 有 selftest → BORROWED", st["prove.lock"]["state"] == "BORROWED", st["prove.lock"]["state"])
        ck("沒 selftest → 仍 GAP 且說原因", st["run.cache"]["state"] == "GAP" and "靜態" in st["run.cache"].get("borrow_why_not", ""))
        ck("指紋變了 → 仍 GAP 且說原因", st["temp.store"]["state"] == "GAP" and "指紋變了" in st["temp.store"].get("borrow_why_not", ""))
        ck("沒釘指紋 → 仍 GAP", st["focus.only"]["state"] == "GAP")
        ck("counts 含 BORROWED / BY_CONTRACT 且總數不變", sum(m["counts"].values()) == len(m["rows"])
           and m["counts"]["BORROWED"] == 2 and m["counts"]["BY_CONTRACT"] == 1,
           str(m["counts"]))
        ck("gap 不執行被讀檔(只 ast)", "selftest_ran" not in good.read_text(encoding="utf-8"))

        r = readiness(via)
        ck("有 GAP → readiness 不綠", r["lamp"] != "GREEN" and r["blockers"], r["lamp"])
        ck("BORROWED 沒 prove → 註明只過靜態", any("靜態" in n for n in r["notes"]), str(r["notes"]))

        pr = prove(via, vrn1=v1, timeout=60)
        got = {x["cap"]: x["result"] for x in pr["rows"]}
        ck("prove:好的 PASS · 壞的 FAIL", got.get("prove.lock") == "PASS" and got.get("truth.matrix") == "FAIL", str(got))
        ck("prove:有 FAIL → 燈 RED", pr["lamp"] == "RED", pr["lamp"])
        ck("prove:不在 VRN-1 夾留 __pycache__", not list(v1.rglob("__pycache__")))

        book = integration_book(via)
        ck("整合冊:有 GAP → problems 列沒有主人", any("沒有主人" in p for p in book["problems"]), str(book["problems"])[:80])
        caps = [e["cap"] for e in book["entries"]]
        ck("整合冊:每能力恰一列(不重複)", len(caps) == len(set(caps)) == len(B.VRN1_CAPS))
        ns = argparse.Namespace(apply=True)
        old_root = B.via_root
        B.via_root = lambda start=None: via
        try:
            rc_i = cmd_integrate(ns)
        finally:
            B.via_root = old_root
        ck("整合閘:有缺口就拒絕且不寫冊", rc_i == 1 and not (via / INTEGRATION_BOOK_REL).exists())

        # 補成全覆蓋:把所有能力的 vrn2_any 第一個關鍵字當 VRN-2 自己的檔 → MATCH,冊應可寫
        for cap in B.VRN1_CAPS:
            (via / "functional modules" / "VRN" / f"VRN2_{cap['vrn2_any'][0]}_v0100.py").write_text(
                f'"""{cap["cap"]}"""\n', encoding="utf-8")
        B._INDEX_CACHE.clear()  # 前版整輪只建一次索引;夾具剛加檔要清掉
        B.via_root = lambda start=None: via
        old_mf = B.build_manifest
        B.build_manifest = lambda v: {"not_lendable": []}  # 夾具沒有 VRN-2 借出工具;只測整合閘本身
        try:
            book2 = integration_book(via)
            rc_ok = cmd_integrate(ns)
            rc_again = cmd_integrate(ns)
        finally:
            B.via_root = old_root
            B.build_manifest = old_mf
        ck("全覆蓋 → 無問題", not book2["problems"], str(book2["problems"]))
        ck("整合冊:契約項主人 = VCGC(不借 VRN-1 那支)",
           any(e["cap"] == "ast.id" and (e["owner"] or {}).get("system") in ("VCGC", "VRN-2") for e in book2["entries"]))
        ck("全覆蓋 → 寫出整合冊", rc_ok == 0 and (via / INTEGRATION_BOOK_REL).is_file(), f"rc {rc_ok}")
        ck("整合冊只增:第二次不覆蓋", rc_again == 1)
        ck("尾版保有前版公開名稱(TAILAPI)",
           all(n in globals() for n in dir(B) if not n.startswith("_") and callable(getattr(B, n))))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    ok = sum(1 for _, c, _ in checks if c)
    for name, cond, note in checks:
        if not cond:
            print(f"  [FAIL] {name}" + (f" — {note}" if note else ""))
    print(f"[自測 {VERSION}] {ok}/{len(checks)} " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = B.build_parser()
    ap.prog = f"VRN2_PeerBridge_{VERSION}"
    sub = next(a for a in ap._actions if isinstance(a, argparse._SubParsersAction))
    sub.choices["gap"].set_defaults(fn=cmd_gap)
    sub.choices["readiness"].set_defaults(fn=cmd_readiness)
    p = sub.choices["integrate"]
    p.add_argument("--apply", action="store_true", help="寫整合冊(只增)")
    p.set_defaults(fn=cmd_integrate)
    p = sub.add_parser("prove", help="桌機跑:VRN-1 借用工具各自 selftest(子行程 · 暫存夾 · 不動 VRN-1 樹)")
    p.set_defaults(fn=cmd_prove)
    return ap


def _route_prior() -> None:
    """前版的 `all` / `fill` 在前版模組裡呼叫 gap_matrix / readiness;CLI 跑時改指本版(自測不改,前版自測照原樣)。"""
    B.gap_matrix, B.readiness, B.cmd_gap, B.cmd_readiness = gap_matrix, readiness, cmd_gap, cmd_readiness


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    _route_prior()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
