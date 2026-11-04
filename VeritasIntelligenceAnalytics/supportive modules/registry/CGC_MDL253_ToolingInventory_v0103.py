#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL253_ToolingInventory v0103 — 薄尾:薄尾鏈走法認得「尾版律」(本體在執行期才決定 · 自己 exec 本體)

操作員 2026-11-04 令「開始 VDF / VCGC CLOSE OUT」;重跑交接案 engine_params:v0101 自測 ⑦b FAIL ——
  VDF_ENG055_OmniFetch 備料卡的鏈只有 ['v0123'](0 個參數 · 0 個旗標),預期鏈尾是本體 v0118 並收到 --lane 等旗標。
根因:ENG055 v0122 / v0123(2026-10-14 起)照 VDF 的尾版律在執行期取本體 ——
  「本體 = 版號小於自己、程式碼裡不 exec 也不點名同族版號檔的最新一支」,自己 exec(compile(本體)) 跑;
  鎖版全景的 _link 只認字面(exec 本體 vNNNN / 釘名 / glob),看到沒字面就當「本體」停下 → 備料卡讀不到真正的參數。
本版只改這一件(v0100 … v0102 一字不動):
  · v0101 的 chain_files_v0101 包一層:走到的那一支若自己 exec、又照同族 _v*.py 找本體(= 尾版律的寫法)→ 照同一條尾版律
    取本體接著走;其他照舊。改在 v0101 模組上(v0101 / v0102 的備料卡都經它)。
  · 其他(備料卡 ⑧–⑩ · engine tools · 動詞)照 v0102。只讀:不執行被讀的檔 · 不寫他系統的檔 · 不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

import ast
import importlib.util
import re
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0102 → v0101 → v0100
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner_v0103(name: str):
    m, seen = PRIOR, []
    while isinstance(m, types.ModuleType) and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = getattr(m, "PRIOR", None)
    return None


def _tree_v0103(p: Path):
    try:
        return ast.parse(Path(p).read_text(encoding="utf-8-sig", errors="replace"))
    except SyntaxError:
        return None


def _consts_v0103(tree) -> list:
    first = tree.body[0] if tree.body else None
    doc = first.value if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) else None
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not doc]


def _execs_v0103(tree) -> bool:
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "exec" for n in ast.walk(tree))


def is_tail_law_v0103(p: Path) -> bool:
    """這一支自己 exec、又照同族 _v*.py 找本體 = 尾版律的寫法(本體在執行期才決定)。"""
    t = _tree_v0103(p)
    return t is not None and _execs_v0103(t) and any("_v*.py" in c for c in _consts_v0103(t))


def tail_law_body_v0103(p: Path):
    """同 VDF 尾版律:同族版號小於自己的檔,由新往舊找第一支「不 exec、也不點名同族版號檔」的 = 本體;沒有 → None。"""
    p = Path(p)
    stem = p.stem.rsplit("_v", 1)[0]
    sib = re.compile(re.escape(stem) + r"_v\d{4}\.py")
    lower = sorted((q for q in p.parent.glob(stem + "_v*.py") if re.fullmatch(re.escape(stem) + r"_v\d{4}", q.stem) and _vnum_v0103(q) < _vnum_v0103(p)),
                   key=_vnum_v0103, reverse=True)
    for q in lower:
        t = _tree_v0103(q)
        if t is None:
            continue
        if not _execs_v0103(t) and not any(sib.search(c) for c in _consts_v0103(t)):
            return q
    return None


_OWN = _owner_v0103("chain_files_v0101")
_ORIG_CHAIN = _OWN.chain_files_v0101 if _OWN is not None else None


def chain_files_v0103(path: Path) -> list:
    """v0101 的走法 + 尾版律:鏈尾那一支若是尾版律寫法 → 取本體接著走(防環 · 最多 30 支)。"""
    out = list(_ORIG_CHAIN(path)) if _ORIG_CHAIN else [Path(path)]
    for _ in range(30):
        last = out[-1]
        if not is_tail_law_v0103(last):
            break
        body = tail_law_body_v0103(last)
        if body is None or body in out:
            break
        more = [q for q in (_ORIG_CHAIN(body) if _ORIG_CHAIN else [body]) if q not in out]
        if not more:
            break
        out += more
    return out


if _OWN is not None:
    _OWN.chain_files_v0101 = chain_files_v0103


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(薄尾鏈認得尾版律)===", flush=True)
    with tempfile.TemporaryDirectory(prefix="cgc253_v0103_") as td:
        d = Path(td)
        (d / "Fam_v0100.py").write_text("def a():\n    return 1\n", encoding="utf-8")
        (d / "Fam_v0101.py").write_text("P = 'Fam_v0100.py'\n", encoding="utf-8")
        (d / "Fam_v0102.py").write_text("import glob\nB = sorted(glob.glob('Fam' + '_v*.py'))\nexec(compile(open(B[0]).read(), B[0], 'exec'))\n", encoding="utf-8")
        (d / "Body_v0100.py").write_text("code = 'x = 1'\nexec(code)\n", encoding="utf-8")
        chk("① 尾版律寫法(自己 exec + 照同族 _v*.py 找)認得;真本體裡有 exec 但不找同族 → 不算",
            is_tail_law_v0103(d / "Fam_v0102.py") and not is_tail_law_v0103(d / "Fam_v0100.py") and not is_tail_law_v0103(d / "Body_v0100.py"))
        chk("② 尾版律取本體:跳過點名同族版號的 v0101 → 本體 v0100", tail_law_body_v0103(d / "Fam_v0102.py") == d / "Fam_v0100.py")
    eng = HERE.parent.parent / "functional modules" / "VDF" / "engine"
    tails = sorted(eng.glob("VDF_ENG055_OmniFetch_v*.py"), key=_vnum_v0103)
    ch = [q.stem.rsplit("_", 1)[-1] for q in chain_files_v0103(tails[-1])] if tails else []
    chk("③ 實樹 ENG055:鏈從尾版走到本體 v0118(不再停在尾版)", ch and ch[0] == tails[-1].stem.rsplit("_", 1)[-1] and ch[-1] == "v0118", ch)
    chk("④ 換裝在 v0101 模組上(v0101 / v0102 備料卡都經它)", _OWN is not None and _OWN.chain_files_v0101 is chain_files_v0103)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    tail = [ln for ln in buf.getvalue().splitlines() if "⑦b" in ln or "[計]" in ln]
    for ln in tail[-4:]:
        print("  ── 前版 " + ln.strip()[:200], flush=True)
    chk("⑤ 前版 v0102 自測(含 v0101 ⑦b 實樹 ENG055 備料卡)rc 0", rc == 0, "rc %s" % rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路工具橋在;只讀(不寫檔 · 不執行被讀的檔);不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and ".write_text(" not in src.split("def selftest", 1)[0])
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc ' + str(rc)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
