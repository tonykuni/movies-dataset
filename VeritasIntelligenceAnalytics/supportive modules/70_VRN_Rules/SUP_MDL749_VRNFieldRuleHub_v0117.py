#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""SUP_MDL749_VRNFieldRuleHub v0117 — 薄尾:增補冊同詞多義「讀操作員裁定」(裁定在冊,樞紐只套用,不自己裁 LL90)

量到的:SSOT 全景 同義字@VCGC hub.additive YELLOW「同詞多義 10 條」八輪不動——因為 additive_conflicts() 只攤開增補冊(knowledge/SYNONYM_LIBRARY_v4)
的來源分域多義,而操作員 2026-10-03 的裁定(R-SYN-04:strong buy / conviction / top pick / 強力買進 / 積極買進 → BUY;strong sell / 強力賣出 / 強烈賣出 → SELL;
accumulate / add → ADD)寫在聯集冊 VIA_SSOT_SynonymUnion 尾版的 rulings(scope · key · verdict · ruled_by),樞紐沒看。
本尾版:additive_conflicts() 結果每列對一次聯集冊 rulings —— 有裁定 → 列標 ruled(verdict · ruled_by)不計多義;沒裁定 → 照舊 YELLOW。
冊不改、增補冊不改、候選不裝;rc 對照與動詞一字照前版。
自測:夾具聯集冊裁 2 鍵 → 多義數減 2、列仍在(只標不刪)· 無裁定 → 與前版相同 · 真樹:讀得到尾版聯集冊。
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
import importlib.util, json, re, sys, tempfile, unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL749_VRNFieldRuleHub"
ENGINE = _STEM + "_v0117"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("sup749_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


# 找到真正定義 additive_conflicts 的那一層(薄尾鏈往回走),在它身上換函數 → 前版 main 的 additive 動詞自然走本版
_OWNER = PRIOR
while hasattr(_OWNER, "PRIOR") and "additive_conflicts" not in vars(_OWNER):
    _OWNER = _OWNER.PRIOR
_ORIG = _OWNER.additive_conflicts
VIA = next((p for p in [HERE] + list(HERE.parents) if (p / "supportive modules" / "registry").is_dir()), HERE)


def _nk(s) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(s or "")).casefold()).strip()


def union_rulings(book: Path | None = None) -> tuple[dict, str]:
    """聯集冊尾版 rulings → {(scope, key): {verdict, ruled_by, why}};冊不在回 ({}, '')。"""
    if book is None:
        cands = sorted((VIA / "supportive modules" / "registry").glob("VIA_SSOT_SynonymUnion_v*.json"), key=_vnum)
        if not cands:
            return {}, ""
        book = cands[-1]
    try:
        d = json.loads(book.read_text(encoding="utf-8"))
    except Exception:
        return {}, book.name
    out = {}
    for r in d.get("rulings") or []:
        if isinstance(r, dict) and r.get("verdict") and r.get("scope") and r.get("key"):
            out[(str(r["scope"]), _nk(r["key"]))] = {"verdict": str(r["verdict"]), "ruled_by": str(r.get("ruled_by") or ""), "why": str(r.get("why") or "")}
    return out, book.name


def additive_conflicts(lib=None, rulings_book: Path | None = None) -> dict:
    rep = _ORIG(lib)
    if rep.get("state") == "ABSENT":
        return rep
    rul, bname = union_rulings(rulings_book)
    ruled = 0
    for r in rep.get("rows") or []:
        hit = rul.get((str(r.get("scope")), _nk(r.get("alias"))))
        if hit:
            r["ruled"] = hit; ruled += 1
    open_n = len([r for r in rep.get("rows") or [] if not r.get("ruled")])
    rep["n_total"] = len(rep.get("rows") or []); rep["n_ruled"] = ruled; rep["n"] = open_n
    rep["rulings_book"] = bname
    rep["state"] = "YELLOW" if open_n else "OK"
    rep["why"] = (f"同詞多義 {rep['n_total']} 鍵 · 已裁 {ruled}(裁定在 {bname},樞紐只套用 LL90)· 未裁 {open_n}"
                  + ("(按來源可判;裁定權在操作員)" if open_n else " → 增補冊多義全有裁定"))
    return rep


_OWNER.additive_conflicts = additive_conflicts     # 前版的 additive 動詞 / 全景探針都經這個名字


def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    lib = {"scopes": {"rating": {"strong buy": [{"canonical": "STRONG_BUY", "source": "a"}, {"canonical": "BUY", "source": "b"}],
                                 "accumulate": [{"canonical": "BUY", "source": "a"}, {"canonical": "ADD", "source": "b"}],
                                 "hold": [{"canonical": "HOLD", "source": "a"}]}}}
    base = _ORIG(lib)
    chk("① 前版行為不變:夾具多義 2 鍵 YELLOW", base.get("n") == 2 and base.get("state") == "YELLOW")
    with tempfile.TemporaryDirectory() as td:
        bk = Path(td) / "VIA_SSOT_SynonymUnion_v0999.json"
        bk.write_text(json.dumps({"rulings": [{"scope": "rating", "key": "Strong Buy", "verdict": "BUY", "ruled_by": "test"}]}, ensure_ascii=False), encoding="utf-8")
        rep = additive_conflicts(lib, rulings_book=bk)
        chk("② 裁 1 鍵 → 未裁 1 · 列仍 2(只標不刪)· 鍵正規化(Strong Buy = strong buy)", rep["n"] == 1 and rep["n_total"] == 2 and rep["n_ruled"] == 1 and any(r.get("ruled", {}).get("verdict") == "BUY" for r in rep["rows"]))
        bk.write_text(json.dumps({"rulings": [{"scope": "rating", "key": "strong buy", "verdict": "BUY"}, {"scope": "rating", "key": "accumulate", "verdict": "ADD"}]}, ensure_ascii=False), encoding="utf-8")
        rep2 = additive_conflicts(lib, rulings_book=bk)
        chk("③ 全裁 → state OK · n 0", rep2["state"] == "OK" and rep2["n"] == 0)
        chk("④ 無裁定冊 → 與前版同(n 2 YELLOW)", additive_conflicts(lib, rulings_book=Path(td) / "none.json")["n"] == 2)
    rul, bname = union_rulings()
    chk("⑤ 真樹:讀得到聯集冊尾版(沒有也誠實)", isinstance(rul, dict), f"{bname or '冊不在'} · 裁定 {len(rul)}")
    chk("⑥ 前版 main 走本版(擁有者層已換)", _OWNER.additive_conflicts is additive_conflicts)
    chk("⑦ 加速器橋在 · 不改任何冊", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        rc = selftest()
        return rc
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
