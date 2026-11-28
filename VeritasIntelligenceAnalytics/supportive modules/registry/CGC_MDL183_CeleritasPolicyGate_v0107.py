#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL183_CeleritasPolicyGate v0107 — 薄尾:操作員裁定甲的既有債帳(PS 18 支 · 前版鏈 PY)

實錄(2026-11-28,交接閘 VCGC 紅列 · celeritas 案):
  ① PS「基線外新缺 18」—— 18 支 main 上原本就有、別人寫的 .ps1,在基線資料檔立下之後才進樹。
     L70:不經操作員逐次許可不改既有 .ps1;基線資料檔(批709)也一字不改。
     操作員 2026-11-28 裁定「甲」:列進既有債。本版讀只增的帳 VIA_CeleritasPolicy_AckDebt_v0100.json(files),
     帳上的檔從 new_missing 移到 ps.ack_debt(照列 · 不當綠也不當違律);帳外再冒出的一支照樣紅(棘輪不鬆)。
     ps.debt 不動(v0101 ⑧ 用它對基線冊列數)。
  ② PY「版史仍被冊指名」2 支 —— 尾版以 PRIOR 載入的前版(已發布不原地改,永遠補不了橋章)。
     操作員同日「前版鏈比照裁定甲」:帳 prior_chain_py 上的檔,且尾版帶橋、橋段在載前版那一行之前(AST 看,不執行尾版)
     → py.ack_prior(照列);帳外 / 尾版沒橋 / 橋在載前版之後 → 照紅。
  其餘(名冊豁免 · 版史 · 收容件 · PS 規則)全照 v0106。只收 VCGC 呼叫。零網路。只讀。
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

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL183_CeleritasPolicyGate"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl183_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.V0101
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PY_MARK = V0101.PY_MARK
_SCAN_V0106 = PRIOR.scan
ACK_GLOB = "VIA_CeleritasPolicy_AckDebt_v*.json"
_LOADERS = ("spec_from_file_location", "import_module", "exec_module")


def __getattr__(name):
    return getattr(PRIOR, name)


def ack_path(reg: Path | None = None) -> Path | None:
    """帳的尾版(registry 夾最高版號);不在就 None(照 v0106,不自己列名單)。"""
    hits = sorted((reg or HERE).glob(ACK_GLOB))
    return hits[-1] if hits else None


def ack_book(path: Path | None = None) -> dict:
    p = path or ack_path()
    if p is None or not p.is_file():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return d if isinstance(d, dict) and d.get("baseline_edited") is False else {}


def _norm(rp: str) -> str:
    return str(rp).replace("\\", "/").lstrip("./")


def bridge_before_prior(tail: Path) -> bool:
    """尾版的橋章那一行在第一個載前版呼叫之前(AST 找呼叫行號,不執行);讀不到 / 沒橋 = False。"""
    try:
        src = tail.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError):
        return False
    mark = next((i for i, ln in enumerate(src.splitlines(), 1) if PY_MARK in ln), None)
    if mark is None:
        return False
    calls = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
             and (getattr(n.func, "attr", None) or getattr(n.func, "id", None)) in _LOADERS]
    return not calls or mark < min(calls)


def scan(root: Path | None = None) -> dict:
    """同 v0106;帳上的 PS 新缺 → ps.ack_debt;帳上的前版鏈 PY(尾版先載橋)→ py.ack_prior;其餘照紅。"""
    s = _SCAN_V0106(root)
    base = Path(root) if root else V0101.VIA
    book = ack_book(ack_path(base / "supportive modules" / "registry"))
    ack_ps = {_norm(f) for f in book.get("files") or []}
    ack_py = {_norm(e.get("file", "")): _norm(e.get("tail", "")) for e in book.get("prior_chain_py") or [] if isinstance(e, dict)}
    ps, py = s.get("ps"), s.get("py")
    if isinstance(ps, dict):
        keep, acked = [], []
        for rp in ps.get("new_missing") or []:
            (acked if _norm(rp) in ack_ps else keep).append(rp)
        ps["new_missing"], ps["ack_debt"] = keep, acked
        ps["state"] = "GREEN" if not keep else "RED"
    if isinstance(py, dict):
        blocked, acked = [], []
        for b in py.get("history_blocked") or []:
            f, t = _norm(b.get("file", "")), _norm(b.get("tail", ""))
            if f in ack_py and ack_py[f] == t and bridge_before_prior(base / t):
                acked.append(b)
            else:
                blocked.append(b)
        gone = {_norm(a["file"]) for a in acked}
        py["missing"] = [m for m in py.get("missing") or [] if _norm(m) not in gone]
        py["history_blocked"], py["ack_prior"] = blocked, acked
        py["state"] = "GREEN" if not py["missing"] else "RED"
    s["state"] = "GREEN" if (py or {}).get("state") == "GREEN" and (ps or {}).get("state") == "GREEN" else "RED"
    return s


def _layers() -> list:
    out, m = [], PRIOR
    while m is not None and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None) if hasattr(m, "scan") else None
    if V0101 not in out:
        out.append(V0101)
    return out


def _install_v0107() -> None:
    for m in _layers():                    # v0106 … v0101:report / 各檢讀模組層 scan
        m.scan = scan


_install_v0107()


def report() -> int:
    rc = PRIOR.report()
    s = scan()
    for f in (s.get("ps") or {}).get("ack_debt") or []:
        print(f"   · 既有債(裁定甲 · 帳){f}")
    for a in (s.get("py") or {}).get("ack_prior") or []:
        print(f"   · 前版鏈(裁定甲 · 帳){a['file']} → 尾版 {a['tail']} 先載橋")
    return rc


def selftest() -> int:
    rc = PRIOR.selftest()            # v0101 八檢 + v0102 … v0106 加檢照跑(實樹以本版規則量)
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {_STEM} {VERSION} 薄尾加檢(裁定甲:PS 既有債帳 · 前版鏈 PY)===")
    ap = ack_path()
    book = ack_book(ap)
    chk("㉚ 帳在 · baseline_edited=false · PS 18 支 · 前版鏈 PY 2 支(名單在冊不在碼)",
        bool(book) and len(book.get("files") or []) == 18 and len(book.get("prior_chain_py") or []) == 2, f"{ap.name if ap else '-'}")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        reg = root / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        good = "#!/usr/bin/env python3\n# [VIA:ACCEL-BRIDGE:v0111]\nimport importlib.util\nP = importlib.util.spec_from_file_location('p', 'x')\n"
        late = "#!/usr/bin/env python3\nimport importlib.util\nP = importlib.util.spec_from_file_location('p', 'x')\n# [VIA:ACCEL-BRIDGE:v0111]\n"
        (root / "Good_v0102.py").write_text(good, encoding="utf-8")
        (root / "Late_v0102.py").write_text(late, encoding="utf-8")
        chk("㉛ 橋在載前版之前 → True;橋在之後 / 沒橋 → False(AST 行號,不執行)",
            bridge_before_prior(root / "Good_v0102.py") and not bridge_before_prior(root / "Late_v0102.py")
            and not bridge_before_prior(root / "Nope_v0102.py"))
        (reg / "VIA_CeleritasPolicy_AckDebt_v0100.json").write_text(json.dumps({
            "baseline_edited": False, "files": ["a/Old.ps1"],
            "prior_chain_py": [{"file": "Good_v0101.py", "tail": "Good_v0102.py"}, {"file": "Late_v0101.py", "tail": "Late_v0102.py"}]}), encoding="utf-8")
        fake = {"state": "RED",
                "ps": {"n": 3, "debt": 0, "new_missing": ["a/Old.ps1", "b/New.ps1"], "state": "RED"},
                "py": {"missing": ["Good_v0101.py", "Late_v0101.py", "Free_v0100.py"], "state": "RED",
                       "history_blocked": [{"file": "Good_v0101.py", "tail": "Good_v0102.py", "callers": ["X.json:.a"]},
                                           {"file": "Late_v0101.py", "tail": "Late_v0102.py", "callers": ["X.json:.b"]}]}}
        global _SCAN_V0106
        keep_scan, _SCAN_V0106 = _SCAN_V0106, (lambda r=None: json.loads(json.dumps(fake)))
        try:
            s = scan(root)
            (reg / "VIA_CeleritasPolicy_AckDebt_v0100.json").write_text(json.dumps({"baseline_edited": True, "files": ["a/Old.ps1"]}), encoding="utf-8")
            s2 = scan(root)
        finally:
            _SCAN_V0106 = keep_scan
        ps, py = s["ps"], s["py"]
        chk("㉜ 帳上 PS → ack_debt · 帳外 PS 照紅(棘輪)· ps.debt 不動",
            ps["ack_debt"] == ["a/Old.ps1"] and ps["new_missing"] == ["b/New.ps1"] and ps["state"] == "RED" and ps["debt"] == 0)
        chk("㉝ 帳上前版鏈 + 尾版先載橋 → ack_prior;尾版橋在後 → 照紅;帳外 PY 照紅",
            [a["file"] for a in py["ack_prior"]] == ["Good_v0101.py"] and sorted(py["missing"]) == ["Free_v0100.py", "Late_v0101.py"]
            and [b["file"] for b in py["history_blocked"]] == ["Late_v0101.py"] and s["state"] == "RED", f"{py}")
        chk("㉞ 帳寫 baseline_edited≠false → 不認帳,全部照紅(負控)",
            not s2["ps"]["ack_debt"] and len(s2["ps"]["new_missing"]) == 2 and not s2["py"]["ack_prior"] and len(s2["py"]["missing"]) == 3)
    real = scan()
    rps, rpy = real.get("ps") or {}, real.get("py") or {}
    chk("㉟ 實樹:PS 新缺 0 · PY 缺 0 · 帳上的照列不消失",
        real.get("state") == "GREEN" and len(rps.get("ack_debt") or []) == 18 and len(rpy.get("ack_prior") or []) == 2,
        f"PS 新缺 {rps.get('new_missing')} · 帳 {len(rps.get('ack_debt') or [])} · PY 缺 {rpy.get('missing')} · 前版鏈 {len(rpy.get('ack_prior') or [])}")
    chk("㊱ 各層 scan 同一把尺(v0101 … v0106 都讀本版)", all(m.scan is scan for m in _layers()) and len(_layers()) >= 6,
        f"{len(_layers())} 層")
    ok = rc == 0 and all(results)
    print(f"  [計] {_STEM} {VERSION} 本版 {sum(results)}/{len(results)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}(薄尾 · 裁定甲既有債帳 · 前版鏈 · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
