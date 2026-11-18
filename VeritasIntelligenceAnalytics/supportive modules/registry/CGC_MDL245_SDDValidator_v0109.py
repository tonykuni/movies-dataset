#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL245_SDDValidator v0109 — 薄尾:需求的歸屬寫成「倉內真的存在的檔」也算有歸屬(X-REQ 不再誤判成不存在)

2026-11-18 容器實錄:SDD X-REQ 紅在「歸屬指到不存在」4 條 ——
  VCGC-REQ206 → review/VIA_Workbench_LockSite_v0106_4/SHA256SUMS.txt
  VCGC-REQ207 → functional modules/VQG/VQG_AllInOne_v0108.py
  VCGC-REQ208 → review/VIA_Workbench_Brand_v0100/SHA256SUMS.txt
  VDF-REQ023  → functional modules/VDF/VDF_MacroKeyword_SSOT_v0100.json
四個檔都在倉裡。本體 v0100 的規則只認「工作流 / 步的代碼 · 律號 · 開頭是 VIA_ / CLAUDE.md / docs/ / Master 的字」,
所以寫成 VIA 相對路徑的歸屬被當成不存在。
本版只改這一條的判法:歸屬若是倉內真的存在的檔或夾(VIA 相對路徑;可用 ../ 指到倉根,解析後不得跑出倉根),算有歸屬;檔不在的照舊是紅。
其他規則(代碼格式 · 跳號 · 工作流引用不存在的需求 · 主流程沒掛需求 · X-REQ-OPEN · X-REQ-BACK)全部照前版,一字不動。
不改需求冊、不改任何冊。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem
TAG = "v0109"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_" + TAG, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]
_PRIOR_REQ = BASE.check_requirements          # 目前裝在本體上的那一支(v0104 包過的)
ORPHAN_TAG = "歸屬指到不存在"


def __getattr__(name: str):
    return getattr(PRIOR, name)


def home_is_file(home: str, root: Path | None = None) -> bool:
    """歸屬是倉內真的存在的檔或夾:VIA 相對路徑;可以用 ../ 指到倉根(例:倉根的 VIA_MCP_Engine,同 v0108),但解析後不得跑出倉根。"""
    h = str(home or "").strip().replace("\\", "/")
    if not h or h.startswith("/") or re.match(r"^[A-Za-z]:", h):
        return False
    via = (root or BASE.VIA).resolve()
    target = (via / h).resolve()
    repo = via.parent
    return (target == repo or repo in target.parents) and target.exists()


def orphan_homes(state: dict, root: Path | None = None) -> list:
    """照本體的規則找沒有歸屬的需求,多認一種:倉內真的存在的檔。"""
    reqs = (state.get("req") or {}).get("requirements") or []
    all_codes = set(state["by_code"]) | {st["code"] for _, w in state["wkfs"] for st in w.get("steps") or []}
    laws = {law.get("id") for law in (BASE._json(BASE.HERE / "VIA_Policy_Laws_SSOT_v0100.json", {}) or {}).get("laws") or [] if isinstance(law, dict)}
    out = []
    for r in reqs:
        if not BASE.REQ_RX.match(r.get("code") or ""):
            continue
        for h in r.get("homes") or []:
            ok = (h in all_codes or (BASE.LAW_RX.match(h) and (not laws or h in laws))
                  or h.startswith(("VIA_", "CLAUDE.md", "docs/", "Master")) or home_is_file(h, root))
            if not ok:
                out.append(f"{r['code']}→{h}")
        if not r.get("homes"):
            out.append(f"{r['code']}→(無)")
    return out


def other_faults(state: dict) -> tuple:
    """本體同一列裡另外兩種紅:代碼不合 / 跳號 · 工作流引用不存在的需求。照本體算法,不放寬。"""
    reqs = (state.get("req") or {}).get("requirements") or []
    by_sub, bad = {}, []
    for r in reqs:
        m = BASE.REQ_RX.match(r.get("code") or "")
        if not m:
            bad.append(str(r.get("code")))
            continue
        by_sub.setdefault(m.group(1), []).append(int(m.group(2)))
    for sub, ns in by_sub.items():
        if sorted(ns) != list(range(1, len(ns) + 1)):
            bad.append(f"{sub}-REQ 跳號")
    codes = {r.get("code") for r in reqs}
    back = [f"{w['code']}→{c}" for _, w in state["wkfs"] for c in (w.get("spec") or {}).get("requirements") or [] if c not in codes]
    return bad, back


def check_requirements(state, rows, root: Path | None = None):
    tmp = []
    _PRIOR_REQ(state, tmp)
    for row in tmp:
        if row.get("rule") == "X-REQ" and row.get("lamp") == "RED" and ORPHAN_TAG in str(row.get("msg")):
            orphans = orphan_homes(state, root)
            bad, back = other_faults(state)
            if orphans or bad or back:
                row = dict(row, msg=f"需求代碼不合 {bad[:4]} · 歸屬指到不存在 {orphans[:4]} · 工作流引用不存在的需求 {back[:4]}")
            else:
                reqs = (state.get("req") or {}).get("requirements") or []
                no_req = [w["code"] for _, w in state["wkfs"] if w.get("kind") in ("hub_steps", "procedure") and not (w.get("spec") or {}).get("requirements")]
                files = sum(1 for r in reqs for h in r.get("homes") or [] if home_is_file(h, root) and not h.startswith(("VIA_", "CLAUDE.md", "docs/", "Master")))
                if no_req:
                    row = dict(row, lamp="YELLOW", msg=f"主流程工作流還沒掛需求:{no_req}")
                else:
                    row = dict(row, lamp="GREEN", msg=f"需求 {len(reqs)} 條 · 代碼連續唯一 · 每條有歸屬(工作流步 / 律 / 冊 / 倉內存在的檔 {files} 條)· 主流程工作流都掛需求(雙向)")
        rows.append(row)


BASE.check_requirements = check_requirements    # 本體 check() 以模組全域叫 check_requirements()


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    n = {"ok": 0, "bad": 0}

    def chk(name, cond, note=""):
        n["ok" if cond else "bad"] += 1
        print("  " + ("[OK] " if cond else "[FAIL] ") + name + ((" · " + str(note)) if note else ""))

    print("=== " + ENGINE + " 自測(X-REQ:倉內存在的檔算歸屬;不在的照舊紅)===")
    with tempfile.TemporaryDirectory(prefix="sdd_v0109_") as td:
        root = Path(td)
        (root / "review" / "pack").mkdir(parents=True)
        (root / "review" / "pack" / "SHA256SUMS.txt").write_text("x\n", encoding="utf-8")

        def state(homes_by_code, wkf_reqs=None):
            return {"req": {"requirements": [{"code": c, "homes": h, "status": "COVERED"} for c, h in homes_by_code.items()]},
                    "by_code": {"VCGC-WKF001": {}}, "wkfs": [(None, {"code": "VCGC-WKF001", "kind": "other", "steps": [{"code": "VCGC-WKF001-STP001"}],
                                                                     "spec": {"requirements": wkf_reqs or []}})]}

        def run(st):
            rows = []
            saved = BASE.check_requirements
            try:
                check_requirements(st, rows, root)
            finally:
                BASE.check_requirements = saved
            return {r["rule"]: r for r in rows if r["rule"] == "X-REQ"}["X-REQ"]

        chk("① 歸屬是倉內存在的檔 → 不再紅", run(state({"VCGC-REQ001": ["review/pack/SHA256SUMS.txt"]}))["lamp"] == "GREEN")
        r2 = run(state({"VCGC-REQ001": ["review/pack/NOPE.txt"]}))
        chk("② 檔不在 → 照舊紅,並點名", r2["lamp"] == "RED" and "VCGC-REQ001→review/pack/NOPE.txt" in r2["msg"], r2["msg"][:80])
        r3 = run(state({"VCGC-REQ001": ["../outside.txt"], "VCGC-REQ002": ["/etc/hosts"]}))
        chk("③ 不存在的 ../ 路徑 / 絕對路徑不算歸屬", r3["lamp"] == "RED" and "outside" in r3["msg"])
        (root.parent / (root.name + "_sib.txt")).write_text("x", encoding="utf-8")
        deep = root / "via"
        deep.mkdir()
        ok_up = home_is_file("../" + root.name + "_sib.txt", deep) is False and home_is_file("../review/pack/SHA256SUMS.txt", deep) is True
        (root.parent / (root.name + "_sib.txt")).unlink()
        chk("③b ../ 只能到倉根(VIA 的上一層)之內;再往外即使檔存在也不算", ok_up)
        r4 = run(state({"VCGC-REQ001": ["review/pack/SHA256SUMS.txt"], "VCGC-REQ002": []}))
        chk("④ 沒寫歸屬的需求照舊紅", r4["lamp"] == "RED" and "VCGC-REQ002→(無)" in r4["msg"], r4["msg"][:80])
        r5 = run(state({"VCGC-REQ001": ["review/pack/SHA256SUMS.txt"], "VCGC-REQ003": ["VCGC-WKF001"]}))
        chk("⑤ 跳號照舊紅(不因為歸屬過了就放行)", r5["lamp"] == "RED" and "跳號" in r5["msg"], r5["msg"][:60])
        r6 = run(state({"VCGC-REQ001": ["review/pack/SHA256SUMS.txt"]}, wkf_reqs=["VCGC-REQ009"]))
        chk("⑥ 工作流引用不存在的需求照舊紅", r6["lamp"] == "RED" and "VCGC-WKF001→VCGC-REQ009" in r6["msg"])
        r7 = run(state({"VCGC-REQ001": ["VCGC-WKF001-STP001"], "VCGC-REQ002": ["docs/x.md"]}))
        chk("⑦ 原本就綠的照舊綠(前版訊息原樣)", r7["lamp"] == "GREEN" and "倉內存在的檔" not in r7["msg"])
        chk("⑧ home_is_file:空字串 / Windows 絕對路徑都不算", not home_is_file("", root) and not home_is_file("C:/x/y.txt", root) and home_is_file("review/pack", root))
    chk("⑨ 裝進本體:本體 check() 呼叫的就是本版", BASE.check_requirements is check_requirements)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋真的匯入 · 不含本機路徑 · 不寫任何冊", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and ("C:" + "\\Users") not in src and ".write_text(" not in src.split("def selftest")[0])
    live = BASE.check(write=False)
    xr = [r for r in live["rows"] if r["rule"] == "X-REQ"]
    chk("⑪ 真冊:X-REQ 不再因為「檔存在的歸屬」而紅", bool(xr) and not (xr[0]["lamp"] == "RED" and any(home_is_file(m.split("→", 1)[1].rstrip("']")) for m in re.findall(r"'([^']+→[^']+)'", xr[0]["msg"]))), xr[0]["lamp"] + " · " + xr[0]["msg"][:90] if xr else "沒有 X-REQ 列")
    print("[計] " + ENGINE + " 本版 " + str(n["ok"]) + "/" + str(n["ok"] + n["bad"]) + " · " + ("PASS" if n["bad"] == 0 else "FAIL"))
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
