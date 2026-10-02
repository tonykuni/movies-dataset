#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL170_VDFChainRunner v0104 — 薄尾:0c 獨立性沿薄尾鏈看依賴(繼承來的依賴不再看不見)

v0103 → v0104(R39 實測 2026-10-01:SDD 自測 MDL170 ⑳ FAIL「已審 ['VDF_ENG063…'] · 未審 []」):
  2026-09-30 VDF_ENG094 出了 v0101 薄尾,讀 VRN_ENG090 的那行留在 v0100 本體(薄尾執行時載入它)。
  v0103 的 classify 只讀尾版那一支的原始碼 → 薄尾沒有那行字 → 這條仍然存在的依賴從掃描裡消失。
  ⑳ 抓到的是掃描器的盲點,不是測試過時;判準(未審 0、已審 ≥ 2)不放寬。
本尾版只換 classify 的取文:尾版是薄尾(用 spec_from_file_location 載同家族前版)就沿鏈往回把前版本體一起讀,
直到遇到不是薄尾的本體為止;不是薄尾的照 v0103 只讀自己。豁免冊比對、0c 判燈、其餘各站全照 v0103(L04 · L05)。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL170_VDFChainRunner"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl170_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def __getattr__(name):
    return getattr(PRIOR, name)


def _is_thin_tail(txt: str, base: str) -> bool:
    """A thin tail loads an earlier version of its own family (glob on its stem + spec_from_file_location)."""
    return "spec_from_file_location" in txt and (base + "_v") in txt


def chain_text(p: Path, base: str) -> str:
    """Tail text plus, while the file is a thin tail, the text of the next lower version of the same family."""
    out, cur = [], p
    seen = set()
    while cur is not None and cur.name not in seen:
        seen.add(cur.name)
        txt = cur.read_text(encoding="utf-8", errors="ignore").replace("\\", "/")
        out.append(txt)
        if not _is_thin_tail(txt, base):
            break
        older = sorted(q for q in cur.parent.glob(base + "_v[0-9][0-9][0-9][0-9].py") if q.name < cur.name)
        cur = older[-1] if older else None
    return "\n".join(out)


def classify(eng_dir: Path, waivers: list) -> dict:
    """逐家族把指向兄弟家族的命中分成:收容件 · 已審單向讀取 · 未審依賴(取文沿薄尾鏈)。"""
    fams = PRIOR._tails(eng_dir)
    filed, reviewed, open_dep = [], [], []
    for base, p in fams.items():
        try:
            txt = chain_text(p, base)
        except OSError as e:
            open_dep.append(f"{base}→(讀不動:{type(e).__name__};量不到不算獨立)")
            continue
        mine = [w for w in waivers if w.get("family") == base]
        for sib in PRIOR.PRIOR._SIBLING:
            for m in re.finditer(re.escape(sib) + r"[^\"\'\n]*", txt):
                seg = m.group(0)
                if "/references/intake/" in seg:
                    filed.append(f"{base}→{seg[:64]}")
                    continue
                ok = next((w for w in mine if w.get("target") == sib and w.get("direction") == "read-only"
                           and w.get("module_glob", "").split("_v")[0] in txt
                           and all(c in txt for c in w.get("calls") or [])), None)
                (reviewed if ok else open_dep).append(f"{base}→{seg[:64]}")
    return {"families": len(fams), "filed": sorted(set(filed)), "reviewed": sorted(set(reviewed)), "open": sorted(set(open_dep))}


PRIOR.classify = classify          # v0103 的 standalone_check(0c)與自測都改用沿鏈取文


def selftest() -> int:
    rc = PRIOR.selftest()          # v0103 的 ⑳(真樹 已審 ≥ 2 · 未審 0)現在用沿鏈取文重跑
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' (' + note + ')') if note else ''}")

    print(f"=== {ENGINE_TAG} 薄尾加檢(沿薄尾鏈看依賴)===")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "VDF_ENG950_Chain_v0100.py").write_text("p = VIA / 'functional modules/VRN'\nx.read_it()\n", encoding="utf-8")
        (d / "VDF_ENG950_Chain_v0101.py").write_text(
            "import importlib.util\nP = sorted(HERE.glob('VDF_ENG950_Chain_v*.py'))[-2]\n"
            "s = importlib.util.spec_from_file_location('p', P)\n", encoding="utf-8")
        (d / "VDF_ENG951_Body_v0100.py").write_text("q = 1\n", encoding="utf-8")
        (d / "VDF_ENG951_Body_v0101.py").write_text("r = 2\n", encoding="utf-8")
        a = classify(d, [])
        chk("㉓ 薄尾繼承的依賴看得到:v0101 薄尾自己沒寫、v0100 本體有 → 仍列為依賴",
            a["open"] == ["VDF_ENG950_Chain→functional modules/VRN"], str(a["open"]))
        b = classify(d, [{"family": "VDF_ENG950_Chain", "target": "functional modules/VRN", "module_glob": "VDF_ENG950_Chain_v*.py",
                          "calls": ["read_it"], "direction": "read-only", "why": "test"}])
        chk("㉔ 豁免比對也沿鏈:登記的呼叫名在本體 → 算已審", b["reviewed"] == ["VDF_ENG950_Chain→functional modules/VRN"]
            and not b["open"], str(b))
        chk("㉕ 不是薄尾的本體只讀自己(舊版的字不算進新版)", "ENG951" not in " ".join(a["open"] + a["reviewed"]))
    real = classify(PRIOR.VDF_ENG, PRIOR._waivers())
    chk("㉖ 真樹:ENG063 · ENG094 兩處都看得到且都已審 · 未審 0", not real["open"] and len(real["reviewed"]) >= 2,
        f"已審 {real['reviewed']} · 未審 {real['open']}")
    ok = rc == 0 and all(results)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(results)}/{len(results)} · v0103 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


PRIOR.selftest_v0104 = selftest


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
