#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0195 — v0194 薄尾(v0194 一字不改):修掉入倉審查 B1–B4。

操作員 2026-11-10:「出 v0195 修掉 B1–B4」。審查紀錄:docs/handoff/ai/intake_20261110_vcgc_multimatrix/VCGC_MultiMatrix_Intake_20261110.md
  B1 matrix 動詞遮蔽 → 只有 `matrix <v0194 的 14 個 action>`(及 `_parse-worker`)交給 v0194;`matrix` 單獨、`matrix --family …`
     等原生寫法與其他所有動詞,一律交回原生主控台(同夾 ≤ v0192 的最高版)。另給別名 `mmatrix <action>`。
  B2 自行發號 → 需求 / 工作流列的 code 一律留白(L125 ②),只登列、標 number_state=BLANK_PENDING_L125;同名列不重複登。
  B3 自動寫冊 / 發號 → 註冊步驟預設只跑乾跑與稽核(registry-sync 不加 --apply · NumberingSystem 只 audit);
     `--approve-registry-sync` 才加 registry-sync --apply;`--approve-numbering` 才加 NumberingSystem --apply --scope(兩者都是操作員的手)。
  B4 前版只比版號 → 原生 v0192 必須內容相符:去 CR、去結尾換行後的 SHA-256 ∈ KNOWN_V0192(本倉 / main 的 v0192);不符就停。
安裝目標:v0194 + v0195 + 離線頁 → 原生 registry(先出計畫;--apply 前照 v0194 跑原生六檢)。v0194 不在同夾 = 照實報錯。
自測:`matrix selftest` / `matrix resilience-test` = v0194 原套件(以 v0194 原函式跑)+ 本版 B1–B4 自測。
修訂 2026-11-10(安裝前就地修;尚未裝進任何 registry,舊內容在 git 歷史):resilience-test 原本用換過的函式跑,
  v0194 F03(假 v0195 在 registry → 要 NEWER_NATIVE)因此 21/22 → 改成以原函式跑;本版另加「尾版 v0196 → NEWER」自測。零網路;不碰 VRN-1;不代設同意閘。
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
import contextlib
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

ENGINE_FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
VERSION = "v0195"
HERE = Path(__file__).resolve().parent
MATRIX_ACTIONS = ("scan", "doctor", "selftest", "install", "register", "watch", "run-tests", "native-check",
                  "repair-plan", "rollback", "export", "resilience-test", "recover", "auto")
NATIVE_MAX = 192                      # 原生主控台 = 同夾 ≤ v0192 的最高版
SUPPORTED_TAILS = (192, 194, 195)     # 安裝前 registry 尾版可接受:原生 v0192;或已裝過的 v0194 / v0195(冪等 / 升級)
KNOWN_V0192 = {
    # 本倉與 main 的 CGC_MDL149_…_v0192.py(9,734 B · sha256 5d968efa…)正規化(去 CR、去結尾換行)後的 SHA-256
    "482d2010031fb66b8610a1bf2b4bb8a05b41212691721a4d3828300b9a55bb80",
}
APPROVE = {"registry_sync": False, "numbering": False}
_P = None
_NATIVE = None


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


def load_v0194():
    """同夾 v0194(本版的前版)。不在 = 照實報錯,不往下猜。"""
    global _P
    if _P is None:
        p = HERE / f"{ENGINE_FAMILY}_v0194.py"
        if not p.is_file():
            raise RuntimeError("V0194_MISSING_NEXT_TO_V0195; v0195 是 v0194 的薄尾,要放在同一夾")
        spec = importlib.util.spec_from_file_location(ENGINE_FAMILY + "_v0194_for_v0195", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _P = mod
        _patch(mod)
    return _P


def native_console_path(folder: Path | None = None):
    folder = Path(folder) if folder else HERE
    return max((p for p in folder.glob(ENGINE_FAMILY + "_v*.py") if 0 <= _vnum(p) <= NATIVE_MAX), key=_vnum, default=None)


def native_main(args: list) -> int:
    """原生主控台(≤ v0192)。舊動詞(含原生 matrix --family …)一律回到原主人。"""
    global _NATIVE
    if _NATIVE is None:
        p = native_console_path()
        if p is None:
            print("[VCGC] NATIVE_CONSOLE_MISSING; 原生動詞要在原生 registry(與 ≤ v0192 同夾)才可用", file=sys.stderr)
            return 2
        spec = importlib.util.spec_from_file_location(ENGINE_FAMILY + "_native_for_v0195", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _NATIVE = mod
    return _NATIVE.main(args)


def normalized_sha(path: Path) -> str:
    b = Path(path).read_bytes().replace(b"\r\n", b"\n").rstrip(b"\n")
    return hashlib.sha256(b).hexdigest()


def route(args: list) -> str:
    """'v0194' · 'native' · 'alias'。B1 的全部判斷都在這裡。"""
    if args[:1] == ["mmatrix"]:
        return "alias"
    if args[:1] == ["matrix"]:
        rest = args[1:]
        if rest[:1] == ["_parse-worker"] or (rest and rest[0] in MATRIX_ACTIONS):
            return "v0194"
        return "native"
    return "native"


# ---------- B2 + B4:安裝計畫(不發號 · 前版內容核對) ----------
def prepare_install(via, frontend):
    P = load_v0194()
    via = Path(via).resolve()
    folder = via / "supportive modules/registry"
    current = P.tail(folder, ENGINE_FAMILY + "_v*.py")
    me = Path(__file__).resolve()
    src194 = HERE / f"{ENGINE_FAMILY}_v0194.py"
    tgt195 = folder / me.name
    tgt194 = folder / src194.name
    html = via / "supportive modules/VCGC_Matrix" / P.FRONTEND_NAME
    if current and _vnum(current) > int(VERSION[1:]):
        raise RuntimeError("NEWER_NATIVE_CONSOLE_PRESENT; rebase integration before install")
    if current and current.resolve() == tgt195.resolve() and P.file_hash(current) == P.file_hash(me):
        if not html.is_file() or P.file_hash(html) != P.file_hash(frontend):
            raise RuntimeError("INSTALLED_FRONTEND_MISSING_OR_CHANGED")
        inv = P.read_json(P.tail(folder, "VIA_VCGC_FunctionInventory_SSOT_v*.json"), {}) or {}
        if not any(x.get("id") == "C-multimatrix-" + VERSION for x in inv.get("stations", [])):
            raise RuntimeError("INSTALLED_STATION_MISSING")
        return {"idempotent": True, "writes": [], "guards": [], "via": str(via)}
    if current is None or _vnum(current) not in SUPPORTED_TAILS:
        raise RuntimeError("UNSUPPORTED_NATIVE_PRIOR; v0195 接受原生 v0192(或已裝的 v0194 / v0195),不盲升")
    native = native_console_path(folder)
    if native is None or _vnum(native) != NATIVE_MAX:
        raise RuntimeError("NATIVE_V0192_MISSING")
    nsha = normalized_sha(native)
    if nsha not in KNOWN_V0192:                                   # B4
        raise RuntimeError(f"NATIVE_PRIOR_CONTENT_UNKNOWN; v0192 正規化 SHA {nsha[:12]}… 不在已知清單,不升級")
    if not Path(frontend).is_file():
        raise FileNotFoundError(frontend)
    writes, guards = [], [{"path": str(current), "sha256": P.file_hash(current)}]
    if not (tgt194.is_file() and P.file_hash(tgt194) == P.file_hash(src194)):
        writes.append({"path": str(tgt194), "bytes": src194.read_bytes()})
    writes.append({"path": str(html), "bytes": Path(frontend).read_bytes()})
    name = "五系統多矩陣整合與證據治理 " + VERSION
    homes = ["supportive modules/registry/" + tgt195.name, "supportive modules/registry/" + tgt194.name,
             "supportive modules/VCGC_Matrix/" + P.FRONTEND_NAME]
    reqcur, reqpath, req = P.next_registry(folder, "VIA_Requirements_SSOT")
    if not any(r.get("name") == name for r in req.get("requirements", [])):
        req["requirements"].append({"code": "", "number_state": "BLANK_PENDING_L125", "subsystem": "VCGC", "status": "PARTIAL",
                                    "name": name, "homes": homes, "modules": [tgt195.name, tgt194.name], "evidence": [],
                                    "next": "衝突解完後由 VCGC 治理器發號(L125 ③);Windows 原生 AST / 加速 / 網路逐檔證據"})
    invcur, invpath, inv = P.next_registry(folder, "VIA_VCGC_FunctionInventory_SSOT")
    if not any(s.get("id") == "C-multimatrix-" + VERSION for s in inv.get("stations", [])):
        inv["stations"].append({"id": "C-multimatrix-" + VERSION, "name": "VCGC 五系統多矩陣自測 " + VERSION, "argv": ["matrix", "selftest"],
                                "timeout": 240, "deps": homes, "requirement": ""})
    wfcur, wfpath, wf = P.next_registry(folder, "VIA_Workflow_VCGC_SSOT")
    if not any(w.get("alias") == "multi_matrix_governance" for w in wf.get("workflows", [])):
        wf["workflows"].append({"code": "", "number_state": "BLANK_PENDING_L125", "alias": "multi_matrix_governance", "kind": "procedure",
                                "name": "多矩陣掃描、驗證與註冊", "spec": {"goal": "統一 VCGC 證據,各子系統維持獨立", "requirements": []}})
    for before, after, obj in ((reqcur, reqpath, req), (invcur, invpath, inv), (wfcur, wfpath, wf)):
        guards.append({"path": str(before), "sha256": P.file_hash(before)})
        writes.append({"path": str(after), "bytes": P.json_bytes(obj)})
    writes.append({"path": str(tgt195), "bytes": me.read_bytes()})   # 主入口最後發布(沿 v0194 交易語意)
    return {"idempotent": False, "writes": writes, "guards": guards, "via": str(via), "requirement": "", "workflow": "",
            "official_central_id": None, "native_prior": str(native), "native_prior_normalized_sha": nsha,
            "numbering": "BLANK_PENDING_L125(本版不發號)"}


# ---------- B3:註冊步驟(預設不寫冊 · 不發號) ----------
def registration_commands(via, out):
    P = load_v0194()
    transaction = P.read_json(Path(out) / "install_transaction.json", {}) or {}
    if transaction.get("state") != "COMMITTED":
        raise RuntimeError("REGISTRATION_REQUIRES_COMMITTED_INSTALL")
    for entry in transaction.get("created", []):
        if not P.within(entry["path"], [via]) or not Path(entry["path"]).is_file() or P.file_hash(entry["path"]) != entry["sha256"]:
            raise RuntimeError("INSTALLED_FILE_CHANGED; new install review required")
    scoped = [str(Path(x["path"]).relative_to(Path(via))) for x in transaction.get("created", [])]
    seq = [["registry-sync", "--apply"] if APPROVE["registry_sync"] else ["registry-sync"]]
    if APPROVE["numbering"]:
        seq.append(["run", "CGC_MDL237_NumberingSystem", "--apply", "--scope"] + scoped)
    seq += [["run", "CGC_MDL237_NumberingSystem", "audit", "--json"], ["ssot", "panorama"], ["test", "--quick"], ["handoff", "check"]]
    return seq, transaction["id"]


_ORIG = {}


def _patch(mod):
    for name, fn in (("prepare_install", prepare_install), ("registration_commands", registration_commands)):
        _ORIG.setdefault(name, getattr(mod, name))
        setattr(mod, name, fn)


@contextlib.contextmanager
def _unpatched():
    P = load_v0194()
    cur = {k: getattr(P, k) for k in _ORIG}
    try:
        for k, v in _ORIG.items():
            setattr(P, k, v)
        yield P
    finally:
        for k, v in cur.items():
            setattr(P, k, v)


# ---------- 自測 ----------
def _fixture(root: Path, v0192_bytes: bytes):
    reg = root / "VIA" / "supportive modules" / "registry"
    reg.mkdir(parents=True)
    (reg / f"{ENGINE_FAMILY}_v0191.py").write_text("x = 1\n", encoding="utf-8")
    (reg / f"{ENGINE_FAMILY}_v0192.py").write_bytes(v0192_bytes)
    (reg / "VIA_Requirements_SSOT_v0100.json").write_text(json.dumps({"requirements": [{"code": "VCGC-REQ007", "name": "舊"}]}), encoding="utf-8")
    (reg / "VIA_VCGC_FunctionInventory_SSOT_v0100.json").write_text(json.dumps({"stations": [{"id": "A"}]}), encoding="utf-8")
    (reg / "VIA_Workflow_VCGC_SSOT_v0100.json").write_text(json.dumps({"workflows": [{"code": "VCGC-WKF003"}]}), encoding="utf-8")
    fe = root / "front.html"
    fe.write_text("<html></html>", encoding="utf-8")
    return root / "VIA", fe


def selftest_v0195() -> dict:
    ok, rows = [], []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        rows.append({"name": name, "ok": bool(cond), "note": str(note)[:200]})
    # B1 路由
    chk("B1 matrix --family vdf,vrn,vap → 原生", route(["matrix", "--family", "vdf,vrn,vap"]) == "native")
    chk("B1 matrix(單獨)→ 原生", route(["matrix"]) == "native")
    chk("B1 matrix scan / install / selftest / _parse-worker → v0194",
        all(route(["matrix", a]) == "v0194" for a in ("scan", "install", "selftest", "_parse-worker")))
    chk("B1 其他動詞 → 原生 · mmatrix → 別名", route(["token"]) == "native" and route(["mmatrix", "scan"]) == "alias")
    with tempfile.TemporaryDirectory(prefix="v0195_") as td:
        d = Path(td)
        reg = d / "reg"
        reg.mkdir()
        for v in (190, 192, 193, 194):
            (reg / f"{ENGINE_FAMILY}_v{v:04d}.py").write_text("", encoding="utf-8")
        chk("B1 原生主控台 = 同夾 ≤ v0192 最高版", native_console_path(reg).name.endswith("_v0192.py"))
        # B4 正規化 SHA
        a, b = d / "a.py", d / "b.py"
        a.write_bytes(b"line1\nline2\n")
        b.write_bytes(b"line1\r\nline2\r\n\r\n")
        chk("B4 CRLF / 結尾換行不影響正規化 SHA", normalized_sha(a) == normalized_sha(b))
        via_n, fe_n = _fixture(d / "f0", b"x\n")
        (via_n / "supportive modules/registry" / f"{ENGINE_FAMILY}_v0196.py").write_text("", encoding="utf-8")
        try:
            prepare_install(via_n, fe_n)
            chk("F03' registry 尾版比本版新(v0196)→ NEWER_NATIVE 停", False, "沒有停")
        except RuntimeError as exc:
            chk("F03' registry 尾版比本版新(v0196)→ NEWER_NATIVE 停", "NEWER_NATIVE" in str(exc), exc)
        # B2 + B4 安裝計畫
        P = load_v0194()
        via, fe = _fixture(d / "f1", b"unknown v0192\n")
        try:
            prepare_install(via, fe)
            chk("B4 v0192 內容不在已知清單 → 停", False, "沒有停")
        except RuntimeError as exc:
            chk("B4 v0192 內容不在已知清單 → 停", "NATIVE_PRIOR_CONTENT_UNKNOWN" in str(exc), exc)
        via, fe = _fixture(d / "f2", b"known v0192 body\n")
        KNOWN_V0192.add(normalized_sha(via / "supportive modules/registry" / f"{ENGINE_FAMILY}_v0192.py"))
        try:
            plan = prepare_install(via, fe)
            blob = b"".join(w["bytes"] for w in plan["writes"] if w["path"].endswith(".json"))
            new_codes = set(re.findall(rb"VCGC-(?:REQ|WKF)\d+", blob)) - {b"VCGC-REQ007", b"VCGC-WKF003"}
            chk("B2 安裝計畫不發號(沒有新的 VCGC-REQ / WKF 號)· code 留白", not new_codes and b"BLANK_PENDING_L125" in blob, new_codes)
            chk("B2 主入口 v0195 最後寫 · v0194 與離線頁一起進", plan["writes"][-1]["path"].endswith("_v0195.py")
                and any(w["path"].endswith("_v0194.py") for w in plan["writes"]) and any(w["path"].endswith(".html") for w in plan["writes"]))
        except Exception as exc:  # noqa: BLE001
            chk("B2 安裝計畫可產生", False, f"{type(exc).__name__}: {exc}")
        finally:
            KNOWN_V0192.discard(normalized_sha(via / "supportive modules/registry" / f"{ENGINE_FAMILY}_v0192.py"))
        # B3 註冊步驟
        out = d / "out"
        out.mkdir()
        f = via / "x.txt"
        f.write_text("x", encoding="utf-8")
        (out / "install_transaction.json").write_text(json.dumps({"state": "COMMITTED", "id": "T1", "created": [{"path": str(f), "sha256": P.file_hash(f)}]}), encoding="utf-8")
        seq, _ = registration_commands(via, out)
        flat = [" ".join(s) for s in seq]
        chk("B3 預設:registry-sync 乾跑 · NumberingSystem 只 audit · 沒有任何 --apply", not any("--apply" in s for s in flat) and flat[0] == "registry-sync", flat)
        APPROVE.update(registry_sync=True, numbering=True)
        try:
            flat2 = [" ".join(s) for s in registration_commands(via, out)[0]]
        finally:
            APPROVE.update(registry_sync=False, numbering=False)
        chk("B3 兩個核准旗標才各自加回 --apply", flat2[0] == "registry-sync --apply" and any("NumberingSystem --apply --scope" in s for s in flat2), flat2)
    chk("v0194 函式已換成本版(install / register 走本版)", P.prepare_install is prepare_install and P.registration_commands is registration_commands)
    return {"schema": "via.matrix.qa.v0195/1", "version": VERSION, "tests": len(ok), "passed": sum(ok), "status": "PASS" if all(ok) else "FAIL", "rows": rows}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    for flag, key in (("--approve-registry-sync", "registry_sync"), ("--approve-numbering", "numbering")):
        if flag in args:
            APPROVE[key] = True
            args.remove(flag)
    r = route(args)
    if r == "native":
        return native_main(args)
    if r == "alias":
        args = ["matrix"] + args[1:]
    P = load_v0194()
    if args[1:2] in (["selftest"], ["resilience-test"]):
        with _unpatched():
            rc194 = P.main(args)                                     # v0194 原套件(原函式;F03 要看到原本的 prepare_install)
        res = selftest_v0195()
        print(json.dumps({k: res[k] for k in ("schema", "version", "tests", "passed", "status")} | {"v0194_rc": rc194}, ensure_ascii=False))
        for row in res["rows"]:
            if not row["ok"]:
                print("  [FAIL] " + row["name"] + " · " + row["note"], file=sys.stderr)
        return 0 if rc194 == 0 and res["status"] == "PASS" else 1
    return P.main(args)


if __name__ == "__main__":
    sys.exit(main())
