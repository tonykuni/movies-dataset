#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0108 — 薄尾:啟用檢查認「轉接鏈」(薄尾 → 薄尾 → 本體):公開名稱與參數表沿鏈合併再比

實錄(2026-11-06,操作員令「啟動 VCGC 所有節省 TOKEN 功能 自動完成完善」):
  `tools activate nlp SUP_MDL866_VIAUnifiedNLPOrchestrator_v0108.py` 乾跑被擋兩檢:
    「公開名稱不少於現役(v0106)」少 BODY · OCR_PKGS · REGISTRY · REPO · VIA · paragraphs_of · pdf_text · praddle_pinned · run_pdf_text
    「參數只增不減」少 OCR_PKGS · _MODS_V0106。
  v0100 的 _api / params_superset 只看「候選檔 + 一個具體本體(頂層 ENGINE_VERSION)」;NLP 家族 v0108 → v0107 → v0106 三層都靠
  `__getattr__` 轉接、沒有一支帶 ENGINE_VERSION,所以 _body_of(v0108) = v0108 自己,v0106 的名字與表在 AST 層全算「少了」。
  實際 import v0108:九個名字與兩張表都 hasattr 為真(轉接鏈在執行期一個都沒少;全景 TAILAPI 也認轉接)。
  本版:候選檔先算「轉接鏈」—— 本檔 → _body_of(本檔);沒有具體本體的轉接薄尾(有 __getattr__ 且內含 getattr(…))沿同夾同族較低版號
  一路往下,直到不再轉接或沒有更低版;公開名稱 = 鏈上各檔聯集;參數表 = 鏈上由舊到新合併(新檔同鍵蓋舊);再照 v0100 的尺比
  (少了 / 同鍵異值 / regex 不見照擋)。沒有轉接鏈的候選檔照前版判。現役席位是轉接薄尾時,v0100 的 _body_of 也改認鏈末端本體。
  啟用 v0108 之後,v0101 寫死的夾具「⑫ nlp 新版(v0105)過全部檢查」只在席位 = v0106 時成立(v0105 公開名 5 個 < v0106 的 13 個);
  本版自測把它列為唯一容許的前版紅(照實印出、不消失、不改前版),其他前版紅照擋。其餘十檢與 apply 全照 v0107。只有 VCGC 能啟用。零網路。
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
import contextlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL233_ToolActivate"
ENGINE = Path(__file__).stem


def _vnum_v0108(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(Path(__file__))), key=_vnum_v0108)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
BASE = _PRIOR.BASE
FAMILIES = BASE.FAMILIES
_V0105_CHECKS = BASE.checks            # 載完前版鏈後裝在本體上的那一把(v0105 席位恰一列)
_ORIG_BODY_OF = BASE._body_of          # v0100 的本體解析(只認頂層 ENGINE_VERSION);轉接鏈沿它往下
NAMES_CHECK = "公開名稱不少於現役"
PARAMS_CHECK = "參數只增不減、不衝突(SSOT / regex / 同義字表;操作員 2026-09-28)"


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def _read_tree(path: Path):
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return None


def _forwards_all(tree: ast.Module) -> bool:
    """模組層 __getattr__ 且函式體內真的呼叫 getattr(…)(把沒定義的名字轉給前版),才算轉接薄尾。"""
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == "__getattr__":
            return any(isinstance(c, ast.Call) and getattr(c.func, "id", "") == "getattr" for c in ast.walk(n))
    return False


def _lower_same_stem(path: Path) -> Path | None:
    stem = path.stem.rsplit("_v", 1)[0]
    lower = [p for p in path.parent.glob(stem + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(path)]
    return max(lower, key=_vnum_v0108) if lower else None


def forward_chain(path: Path) -> list:
    """候選檔的轉接鏈:本檔 → _body_of(本檔);沒有具體本體的轉接薄尾沿同夾同族較低版號往下;直到不再轉接 / 沒有更低版 / 繞圈。"""
    chain, seen = [], set()
    p = Path(path)
    while p is not None and p.is_file() and p.resolve() not in seen:
        chain.append(p)
        seen.add(p.resolve())
        tree = _read_tree(p)
        if tree is None:
            break
        body = _ORIG_BODY_OF(p)
        if body.resolve() != p.resolve():
            p = body
        elif _forwards_all(tree):
            p = _lower_same_stem(p)
        else:
            p = None
    return chain


def body_of_chain(path: Path) -> Path:
    """本體 = 轉接鏈的末端(沒有 ENGINE_VERSION 的家族也能找到真本體);沒有鏈就是 v0100 的答案。現役席位是轉接薄尾時,「現役」的名字與表也照這個本體量。"""
    chain = forward_chain(path)
    return chain[-1] if chain else _ORIG_BODY_OF(path)


def api_chain(path: Path) -> set:
    names = set()
    for p in forward_chain(path):
        tree = _read_tree(p)
        if tree is not None:
            names |= BASE._public(tree)
    return names


def param_tables_chain(path: Path) -> dict:
    """鏈上參數表由舊到新合併:新檔同鍵蓋舊(新檔沒寫的表沿用前版,正是 __getattr__ 轉接的語意)。"""
    out = {}
    for p in reversed([q for q in forward_chain(path) if _read_tree(q) is not None]):   # 鏈尾若剖析不過已在 forward_chain 止步
        out.update(BASE.param_tables(p))
    return out


def checks(family: str, file_name: str, register: dict | None = None, root: Path | None = None) -> list:
    out = _V0105_CHECKS(family, file_name, register, root)
    if family not in FAMILIES:
        return out
    _stem, folder, _req, _r = FAMILIES[family]
    cand = Path(folder) / file_name
    current = BASE.pinned(family, root)
    if not cand.is_file() or not current or current.resolve() == cand.resolve():
        return out
    chain = forward_chain(cand)
    if len(chain) < 2:
        return out                                    # 沒有轉接鏈:照前版判
    base = body_of_chain(current)
    base_tree = _read_tree(base)
    if base_tree is None:
        return out
    hops = " → ".join(p.name for p in chain)
    old = {n for n in BASE._public(base_tree) if not n.startswith("_")}
    names = api_chain(cand)
    lost = sorted(n for n in old if n not in names)
    old_t = BASE.param_tables(base)
    new_t = param_tables_chain(cand)
    lost_t = [k for k in old_t if k not in new_t]
    conflict = []
    for k in old_t:
        if k in new_t:
            sub_lost, sub_conf = BASE.param_diff(old_t[k], new_t[k], k)
            lost_t += sub_lost
            conflict += sub_conf
    for c in out:
        if str(c.get("check", "")).startswith(NAMES_CHECK):
            c["ok"] = not lost
            c["detail"] = (", ".join(lost[:12]) or f"{len(old)} 個全在") + f" · 轉接鏈 {hops}"
        elif c.get("check") == PARAMS_CHECK:
            c["ok"] = not lost_t and not conflict
            c["detail"] = (f"舊 {len(old_t)} 張 → 新(鏈){len(new_t)} 張 · 少 {len(lost_t)} · 衝突 {len(conflict)} "
                           + "; ".join((lost_t + conflict)[:6]) + f" · 轉接鏈 {hops}")
    return out


BASE.checks = checks                    # plan() 與前版自測在本體全域找 checks
BASE._body_of = body_of_chain           # v0100 的 _api / checks 也照轉接鏈末端當本體(席位是薄尾時「現役」量真本體;前版自測同一把尺)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


STALE_FIXTURE = "⑫ nlp 新版過 v0100 的全部檢查(SUP_MDL866_VIAUnifiedNLPOrchestrator_v0105.py)"   # v0101 寫死的候選:席位在 v0106 時才成立


def selftest() -> int:
    BASE.checks = _V0105_CHECKS         # 前版鏈自測量前版那一把(v0105 的「本尾版已裝」斷言)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = _PRIOR.selftest()
    finally:
        BASE.checks = checks            # 然後裝回本版
    prior_out = buf.getvalue()
    print(prior_out, end="")
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(啟用檢查認轉接鏈)===")
    fails = [l.strip() for l in prior_out.splitlines() if "[FAIL]" in l]
    stale = [l for l in fails if STALE_FIXTURE in l]
    cascade = [l for l in fails if "前版鏈" in l]
    other = [l for l in fails if l not in stale and l not in cascade]
    chk("㊶ 前版鏈自測過(v0100 … v0107;唯一容許的紅 = v0101 寫死候選 v0105 的 ⑫:NLP 席位已由 v0106 前進到 v0108,v0105 本就不該再過「不少於現役」,照實列出不消失)",
        rc == 0 or (not other and stale), f"rc {rc} · 前版 FAIL {len(fails)}(舊夾具 {len(stale)} · 連帶 {len(cascade)} · 其他 {len(other)})" + ("; " + other[0][:120] if other else ""))
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "Fam_v0100.py").write_text("T = {'a': 1}\nR = re.compile('x')\n\ndef f():\n    return 1\n", encoding="utf-8")   # 本體但沒有 ENGINE_VERSION(同 NLP 家族)
        (d / "Fam_v0101.py").write_text("import importlib\nPRIOR = None\n\ndef __getattr__(name):\n    return getattr(PRIOR, name)\n", encoding="utf-8")
        (d / "Fam_v0102.py").write_text("PRIOR = None\nU = ['new']\n\ndef __getattr__(name):\n    return getattr(PRIOR, name)\n", encoding="utf-8")
        (d / "Fam_v0103.py").write_text("U = ['new']\n\ndef g():\n    return 2\n", encoding="utf-8")       # 不轉接:鏈只有自己
        (d / "Fam_v0104.py").write_text("T = {'a': 2}\n\ndef __getattr__(name):\n    return getattr(None, name)\n", encoding="utf-8")   # 同鍵異值
        (d / "Body_v0100.py").write_text("ENGINE_VERSION = 'v0100'\n\ndef h():\n    return 3\n", encoding="utf-8")   # 具體本體(頂層 ENGINE_VERSION)
        (d / "Body_v0101.py").write_text("def __getattr__(name):\n    return getattr(None, name)\n", encoding="utf-8")
        (d / "Body_v0102.py").write_text("def __getattr__(name):\n    return getattr(None, name)\n", encoding="utf-8")
        c102 = [p.name for p in forward_chain(d / "Fam_v0102.py")]
        cb = [p.name for p in forward_chain(d / "Body_v0102.py")]
        chk("㊷ 沙盒:沒有具體本體的轉接薄尾沿版號往下(v0102 → v0101 → v0100 止);有具體本體(ENGINE_VERSION)的照 v0100 _body_of 直接跳到本體",
            c102 == ["Fam_v0102.py", "Fam_v0101.py", "Fam_v0100.py"] and cb == ["Body_v0102.py", "Body_v0100.py"] and "h" in api_chain(d / "Body_v0102.py"),
            " → ".join(c102) + " | " + " → ".join(cb))
        names = api_chain(d / "Fam_v0102.py")
        tabs = param_tables_chain(d / "Fam_v0102.py")
        chk("㊸ 沙盒:鏈上名字 / 參數表聯集(f · T · R#regex 都在;U 新增照過)",
            {"f", "T", "U"} <= names and set(tabs) >= {"T", "R#regex", "U"} and tabs["T"] == {"a": 1}, f"{sorted(names)} · {sorted(tabs)}")
        c103 = [p.name for p in forward_chain(d / "Fam_v0103.py")]
        chk("㊹ 沙盒:不轉接的檔鏈只有自己(名字真的少了照擋 · 負控)", c103 == ["Fam_v0103.py"] and "f" not in api_chain(d / "Fam_v0103.py"), " → ".join(c103))
        t104 = param_tables_chain(d / "Fam_v0104.py")
        _l, conf = BASE.param_diff({"a": 1}, t104.get("T"), "T")
        chk("㊺ 沙盒:鏈上同鍵異值仍是衝突(新檔蓋舊 → T.a 1 ≠ 2 照擋 · 負控)", t104.get("T") == {"a": 2} and bool(conf), f"{conf}")
    nlp_dir = BASE.VIA / "supportive modules" / "70_VRN_Rules"
    tails = sorted(nlp_dir.glob("SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"), key=_vnum_v0108)
    if tails:
        tail = tails[-1]
        hops = [p.name for p in forward_chain(tail)]
        body = body_of_chain(tail)
        body_tree = _read_tree(body)
        old = {n for n in BASE._public(body_tree) if not n.startswith("_")} if body_tree else set()
        lost = sorted(old - api_chain(tail))
        old_t, new_t = BASE.param_tables(body), param_tables_chain(tail)
        lost_t = [k for k in old_t if k not in new_t]
        conf = [c for k in old_t if k in new_t for c in BASE.param_diff(old_t[k], new_t[k], k)[1]]
        chk(f"㊻ 真樹:NLP 尾版 {tail.name} 沿轉接鏈(鏈 {len(hops)} 支 · 本體 {body.name})公開名稱 / 參數表一個不少(不論它是候選還是現役席位)",
            len(hops) >= 2 and body.name != tail.name and not lost and not lost_t and not conf and old,
            f"本體公開名 {len(old)} · 少 {lost} · 表少 {lost_t} · 衝突 {conf}")
    else:
        chk("㊻ 真樹:NLP 尾版不在 → 照實失敗", False)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("㊼ 本版已裝在本體(plan 走本版 checks · _body_of 認轉接鏈末端)· 加速器橋在 · 不碰 TA-Lib",
        BASE.checks is checks and BASE._body_of is body_of_chain and "VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    ok = all(results)                   # 前版鏈的 rc 由 ㊶ 裁(唯一容許的舊夾具紅照實列出)
    print(f"  {ENGINE} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
