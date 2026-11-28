#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL140_HandoverConsole v0113 — 薄尾(v0100–v0112 一字不動):舊案不計入現況燈 · 收尾範圍只算 VCGC 與 VDF(VCGC-REQ283)

操作員 2026-11-28:「If they are old case, irrelevant to the current status you can ignore」「Limit the scope of closing up two systems.」
本版只在「分系統之前」多做一步(v0112 的退役清冊判之後),把下面兩種列從燈裡搬出去,一筆不刪、另列兩欄:
  舊案 ignored_old_rows(判法寫死,判不出就照舊紅):
    ① SUPERSEDED_SUCCESSOR_INVALID —— 工作項本身已登記被取代(舊案),接手者失效是接手者那一列的事
    ② EVIDENCE_INVALID —— 工作項的案指名測的版號比同家族現在的尾版舊;或案宣告的相依檔已不在樹上、而在 VIA_RetiredEngines 裡
    ③ CHANGED_CODE_WITHOUT_TEST —— 這支檔不是同家族的尾版(前版;尾版的案才代表現況)
  範圍外 out_of_scope_rows:被測的模組 / 檔只在 VRN · VQG · VAP 的夾(含 70_VRN_Rules,歸屬待裁定)→ 不在這次兩系統收尾範圍
燈與驗收燈照剩下的列重算(同 v0112 的式子)。REQ_CHANGED 不動(只有 checkpoint 能收)。其餘動詞照前版。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] SuperAccel 加速器橋(graceful;執行時載得到才算) =====
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響(自測記一檢)
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0113"
VERBS = ("check", "checkpoint", "test", "daily", "--selftest")     # 動詞照前版;本版沒有新增
RULING = "操作員 2026-11-28:舊案不計入現況燈;收尾範圍只算 VCGC 與 VDF(VCGC-REQ283)"
SKIP_DIRS = ("VIA_RetiredEngines", "references/intake", "/history/")
OUT_DIRS = ("functional modules/VRN/", "supportive modules/70_VRN_Rules/", "functional modules/VQG/", "functional modules/VAP/")
RETIRED = "functional modules/VIA_RetiredEngines"
_NOISE_ARGS = {"run", "core", "vdf", "vrn", "engine", "fetch", "test", "logic", "pslint"}


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


def _chain() -> list:
    out, m = [], PRIOR
    while m is not None and m not in out:
        out.append(m)
        m = vars(m).get("PRIOR")
    return out


def _defined_in(m, name: str) -> bool:
    fn = vars(m).get(name)
    return callable(fn) and getattr(fn, "__globals__", None) is vars(m)


SCOPE_HOME = next(m for m in _chain() if _defined_in(m, "apply_system_scope"))   # v0111:audit 讀自己全域的 _PREV_AUDIT 再分系統
_PREV = vars(SCOPE_HOME)["_PREV_AUDIT"]                                         # 目前掛著的(v0112 的 inner_audit:退役清冊判)


def __getattr__(name: str):
    return getattr(PRIOR, name)


class Tree:
    """一棵 VIA 樹的 .py 索引(略過退役夾 · 收件夾 · history);家族尾版與模組位置都從這裡查。"""

    def __init__(self, via):
        self.via = Path(via)
        self._files = None

    def files(self) -> list:
        if self._files is None:
            self._files = [p.relative_to(self.via).as_posix() for p in self.via.rglob("*.py")
                           if not any(s in "/" + p.relative_to(self.via).as_posix() for s in SKIP_DIRS)]
        return self._files

    def tail(self, fam: str):
        vs = [int(m.group(1)) for f in self.files() for m in [re.match(re.escape(fam) + r"_v(\d{4})$", Path(f).stem)] if m]
        return max(vs) if vs else None

    def locate(self, stem: str) -> list:
        return [f for f in self.files() if Path(f).stem == stem or re.match(re.escape(stem) + r"_v\d{4}$", Path(f).stem)]


def _out(rel: str) -> bool:
    return any(rel.startswith(d) or ("/" + d) in ("/" + rel) for d in OUT_DIRS)


def _target(argv: list):
    """案的 argv 裡被測的那一支(--selftest 之前最後一個像模組 / 檔的字)。"""
    t = None
    for x in argv or []:
        if x == "--selftest":
            break
        if x.startswith("--") or x in _NOISE_ARGS:
            continue
        t = x
    return t


def classify(row: dict, policy: dict, tree: Tree):
    """回 ("OLD" | "OUT", 理由) 或 None(照舊算燈)。判不出一律 None。"""
    rule, d = row.get("rule"), row.get("detail")
    if rule == "SUPERSEDED_SUCCESSOR_INVALID":
        return "OLD", "工作項已登記被取代(舊案);接手者失效由接手者那一列承擔"
    if rule == "CHANGED_CODE_WITHOUT_TEST" and isinstance(d, str):
        if _out(d):
            return "OUT", "檔在 VRN / VQG / VAP 的夾"
        m = re.match(r"(.+)_v(\d{4})$", Path(d).stem)
        t = tree.tail(m.group(1)) if m else None
        if m and t and int(m.group(2)) < t:
            return "OLD", f"前版(家族尾版是 v{t:04d})"
        return None
    if rule == "EVIDENCE_INVALID" and isinstance(d, dict):
        items = {x.get("id"): x for x in policy.get("work_items", [])}
        it = items.get(d.get("id")) or {}
        case = policy.get("test_cases", {}).get(it.get("case") or "")
        if it.get("state") != "VERIFIED" or not case:
            return None
        tgt = _target(case.get("argv"))
        if not tgt:
            return None
        stem = Path(tgt).name.removesuffix(".py")
        m = re.match(r"(.+)_v(\d{4})$", stem)
        locs = tree.locate(m.group(1) if m else stem)
        if locs and all(_out(x) for x in locs):
            return "OUT", "被測模組只在 VRN / VQG / VAP 的夾"
        if m:
            t = tree.tail(m.group(1))
            if t and int(m.group(2)) < t:
                return "OLD", f"案指名測 v{int(m.group(2)):04d},家族尾版是 v{t:04d}"
        for dep in case.get("dependencies") or []:
            if "*" in dep or (tree.via / dep).exists():
                continue
            if list(tree.via.glob(f"{RETIRED}/*/{dep}")):
                return "OLD", f"相依檔已退役:{dep}"
        return None
    return None


def _read_policy(via, policy):
    if isinstance(policy, dict):
        return policy
    try:
        return json.loads((Path(via) / POLICY.relative_to(VIA)).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def apply_old_and_scope(report: dict, via, policy=None) -> dict:
    """舊案 / 範圍外的列搬到兩欄(一筆不刪);燈與驗收燈照剩下的列重算(同 v0112 的式子)。"""
    pol = _read_policy(via, policy)
    tree = Tree(via)
    keep, old, out = [], [], []
    for r in report.get("rows") or []:
        c = classify(r, pol, tree)
        if c is None:
            keep.append(r)
        else:
            (old if c[0] == "OLD" else out).append(dict(r, why_moved=c[1]))
    lamps = [r.get("lamp") for r in keep]
    lamp = "RED" if "RED" in lamps else "YELLOW" if lamps else "GREEN"
    report["rows"] = keep
    report["ignored_old_rows"] = old
    report["out_of_scope_rows"] = out
    report["lamp"] = lamp
    report["closeout_lamp"] = ("RED" if lamp == "RED" else "YELLOW"
                               if report.get("pending") or lamp == "YELLOW" or report.get("z281_handover") else "GREEN")
    s = report.setdefault("summary", {})
    s["findings"] = len(keep)
    s["ignored_old"] = len(old)
    s["out_of_scope"] = len(out)
    s["scope_ruling"] = RULING
    return report


def inner_audit(via=VIA, policy=None, baseline=None, require_baseline=True):
    return apply_old_and_scope(_PREV(via, policy, baseline, require_baseline), via, policy)


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

    print(f"[計] {ENGINE} 自測開始(暫存樹 · 不改任何冊 · 零網路)", flush=True)
    chk("① 加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 掛在分系統之前(v0111 的 _PREV_AUDIT 是本版的 inner_audit,內層接 v0112)",
        vars(SCOPE_HOME)["_PREV_AUDIT"] is inner_audit and getattr(_PREV, "__globals__", None) is vars(PRIOR) and _PREV.__name__ == "inner_audit")
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        for rel in ("supportive modules/registry/CGC_MDLX_Foo_v0101.py", "supportive modules/registry/CGC_MDLX_Foo_v0103.py",
                    "supportive modules/registry/CGC_MDLY_Bar_v0100.py", "functional modules/VRN/VRN_ENGX_Baz_v0100.py",
                    "supportive modules/70_VRN_Rules/SUP_MDLX_Rule_v0102.py",
                    f"{RETIRED}/prune_x/supportive modules/registry/CGC_MDLZ_Gone_v0100.py", "supportive modules/registry/CGC_MDLZ_Gone_v0101.py"):
            p = via / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x = 1\n", encoding="utf-8")
        reg.mkdir(parents=True, exist_ok=True)
        tc = {"pin_old": {"argv": ["--family", "core", "supportive modules/registry/CGC_MDLX_Foo_v0101.py", "--selftest"], "dependencies": []},
              "fam_tail": {"argv": ["CGC_MDLX_Foo", "--selftest"], "dependencies": []},
              "pin_tail": {"argv": ["--family", "core", "supportive modules/registry/CGC_MDLX_Foo_v0103.py", "--selftest"], "dependencies": []},
              "vrn": {"argv": ["VRN_ENGX_Baz", "--selftest"], "dependencies": []},
              "dep_gone": {"argv": ["CGC_MDLZ_Gone", "--selftest"], "dependencies": ["supportive modules/registry/CGC_MDLZ_Gone_v0100.py"]},
              "dep_missing": {"argv": ["CGC_MDLY_Bar", "--selftest"], "dependencies": ["supportive modules/registry/CGC_MDLY_Never_v0100.py"]}}
        wis = [{"id": "R:" + k, "case": k, "state": "VERIFIED"} for k in tc] + [{"id": "R:pending", "case": "pin_old", "state": "REVIEW"}]
        pol = {"test_cases": tc, "work_items": wis}
        tree = Tree(via)

        def ev(i):
            return {"lamp": "RED", "rule": "EVIDENCE_INVALID", "detail": {"id": "R:" + i, "why": ["x"]}}

        cases = {"③ 指名舊版(v0101 < 尾版 v0103)→ 舊案": (ev("pin_old"), "OLD"),
                 "④ 測家族尾版 → 照算(現況)": (ev("fam_tail"), None),
                 "⑤ 指名的就是尾版 → 照算(現況)": (ev("pin_tail"), None),
                 "⑥ 被測模組只在 VRN 夾 → 範圍外": (ev("vrn"), "OUT"),
                 "⑦ 相依檔不在樹上、在退役夾 → 舊案": (ev("dep_gone"), "OLD"),
                 "⑧ 反控:相依檔不在樹上、退役夾也沒有 → 照算(不准當舊案)": (ev("dep_missing"), None),
                 "⑨ 反控:工作項不是 VERIFIED → 照算": (ev("pending"), None),
                 "⑩ 反控:工作項找不到 → 照算": (ev("nope"), None),
                 "⑪ 沒測試的前版檔 → 舊案": ({"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "supportive modules/registry/CGC_MDLX_Foo_v0101.py"}, "OLD"),
                 "⑫ 反控:沒測試的尾版檔 → 照算": ({"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "supportive modules/registry/CGC_MDLX_Foo_v0103.py"}, None),
                 "⑬ 沒測試、在 70_VRN_Rules → 範圍外": ({"lamp": "RED", "rule": "CHANGED_CODE_WITHOUT_TEST", "detail": "supportive modules/70_VRN_Rules/SUP_MDLX_Rule_v0102.py"}, "OUT"),
                 "⑭ 接手者失效(工作項已被取代)→ 舊案": ({"lamp": "RED", "rule": "SUPERSEDED_SUCCESSOR_INVALID", "detail": {"id": "R:x"}}, "OLD"),
                 "⑮ 反控:REQ_CHANGED 不動": ({"lamp": "YELLOW", "rule": "REQ_CHANGED", "detail": "VCGC-REQ001"}, None)}
        for name, (row, want) in cases.items():
            got = classify(row, pol, tree)
            chk(name, (got[0] if got else None) == want, got)
        rows = [c[0] for c in cases.values()]
        rep = apply_old_and_scope({"rows": [dict(r) for r in rows], "pending": []}, via, pol)
        kept, old, out = len(rep["rows"]), len(rep["ignored_old_rows"]), len(rep["out_of_scope_rows"])
        chk("⑯ 一筆不刪:照算 + 舊案 + 範圍外 = 原列數", kept + old + out == len(rows), (kept, old, out, len(rows)))
        chk("⑰ 燈照剩下的列重算:還有現況紅 → RED;每筆搬走的列帶理由",
            rep["lamp"] == "RED" and all(r.get("why_moved") for r in rep["ignored_old_rows"] + rep["out_of_scope_rows"]))
        only_old = apply_old_and_scope({"rows": [ev("pin_old"), cases["⑮ 反控:REQ_CHANGED 不動"][0]], "pending": []}, via, pol)
        chk("⑱ 紅全是舊案 → 燈剩黃(REQ_CHANGED)· 驗收燈黃,不冒充綠", only_old["lamp"] == "YELLOW" and only_old["closeout_lamp"] == "YELLOW")
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    pr = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    chk("⑲ 直接前版自測(乾淨子行程)照過", pr.returncode == 0, (pr.stdout.strip().splitlines() or ["?"])[-1])
    verdict = "PASS" if n["bad"] == 0 else "FAIL"
    print(f"[計] {ENGINE} 本版 {n['ok']}/{n['ok'] + n['bad']} · {verdict}", flush=True)
    return 0 if n["bad"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
