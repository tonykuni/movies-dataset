"""VDF_ENG077_ActiveETFUniverse tail v0105. 本體與 ScrapeGate 改照尾版律取(不再字串釘死版號)。

v0104→v0105(側線 2026-09-28;DB 面板 AST PINVER 兩筆):v0104 用字串釘 `VDF_ENG077_ActiveETFUniverse_v0101.py` 與 `CGC_MDL224_ScrapeGate_v0100.py`。
本支:本體 = 同族版號小於自己、程式碼裡(不算說明字串)不再點名同族版號檔也不 exec 的最新一支 = 最後一版具體實作
(今天就是 v0101,與 v0104 一字不差;判準同全景 TAILAPI 往回找具體實作那一條);ScrapeGate = registry 夾裡的尾版。
其餘全照 v0104(在自己的 namespace 跑本體、gate_open 換成 ScrapeGate、模組層覆寫生效)。舊版全留作版史(L04)。selftest 不抓網路。
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
    VIA_ACCEL = None
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
import importlib.util as _tail_ilu
import sys as _tail_sys
from pathlib import Path as _TailPath

_TAIL_SELF = _TailPath(__file__).resolve()


def _tail_concrete_body():
    """同族版號小於自己的檔,由新往舊找第一支「程式碼裡不點名同族版號檔、也不 exec」的 = 具體實作本體。"""
    import ast as _ast
    import re as _re
    stem = _TAIL_SELF.name.rsplit("_v", 1)[0]
    sib = _re.compile(_re.escape(stem) + r"_v\d{4}\.py")
    unreadable = []
    for p in sorted((q for q in _TAIL_SELF.parent.glob(stem + "_v*.py") if q.name < _TAIL_SELF.name), reverse=True):
        try:
            tree = _ast.parse(p.read_text(encoding="utf-8-sig", errors="replace"))
        except SyntaxError as e:
            unreadable.append(f"{p.name}:{e.lineno}")   # 讀不動的版本記下來,找不到本體時一起報
            continue
        first = tree.body[0] if tree.body else None
        doc = first.value if isinstance(first, _ast.Expr) and isinstance(getattr(first, "value", None), _ast.Constant) else None
        consts = [n.value for n in _ast.walk(tree) if isinstance(n, _ast.Constant) and isinstance(n.value, str) and n is not doc]
        execs = any(isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id == "exec" for n in _ast.walk(tree))
        if not execs and not any(sib.search(c) for c in consts):
            return p
    raise FileNotFoundError(f"{stem}:版號小於 {_TAIL_SELF.name} 的具體實作本體不在" + (f"(讀不動:{', '.join(unreadable)})" if unreadable else ""))


def _tail_newest(folder, pattern):
    hits = sorted(folder.glob(pattern))
    if not hits:
        raise FileNotFoundError(f"{folder / pattern} 不在")
    return hits[-1]


_TAIL_BODY = _tail_concrete_body()
_TAIL_GATE = _tail_newest(_TAIL_SELF.parents[3] / "supportive modules" / "registry", "CGC_MDL224_ScrapeGate_v*.py")
_TAIL_SURFACE = ('unify', 'run')
_TAIL_NET_PATH = globals().get("VIA_NET_TOOL_PATH")


def _tail_load(path, name):
    spec = _tail_ilu.spec_from_file_location(name, path)
    module = _tail_ilu.module_from_spec(spec)
    _tail_sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_tail_name = __name__
globals()["__name__"] = "vdf_eng077_activeetfuniverse_body_in_tail"   # the body's own main block must not fire
globals()["__file__"] = str(_TAIL_BODY)                 # the body reads paths / its own source from here
try:
    exec(compile(_TAIL_BODY.read_text(encoding="utf-8"), str(_TAIL_BODY), "exec"), globals())
finally:
    globals()["__name__"] = _tail_name
gate_open = _tail_load(_TAIL_GATE, "scrape_gate_for_vdf_eng077_activeetfuniverse_tail").gate_open  # same swap v0102 made
_body_main = main  # noqa: F821


def main() -> int:  # noqa: F811
    return _body_main()


def selftest() -> int:
    text = _TAIL_SELF.read_text(encoding="utf-8")
    bridges = "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and bool(_TAIL_NET_PATH)
    surface = all(callable(globals().get(n)) for n in _TAIL_SURFACE)
    g = gate_open
    gate = (g({}) is False and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False
            and g({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}) is True)
    print(f"  [{'OK' if bridges else 'FAIL'}] 加速橋 + 網路橋在尾版上")
    print(f"  [{'OK' if surface else 'FAIL'}] 尾版帶著具體實作的面:{', '.join(_TAIL_SURFACE)}")
    print(f"  [{'OK' if gate else 'FAIL'}] gate_open = CGC_MDL224 ScrapeGate(同意閘沒開就關)")
    body_ok = _TAIL_BODY.name < _TAIL_SELF.name and "exec(" not in _TAIL_BODY.read_text(encoding="utf-8", errors="ignore")
    import re as _re
    pinned = _re.search(_re.escape(_TAIL_SELF.name.rsplit("_v", 1)[0]) + r"_v\d{4}\.py\"", text.split("def selftest")[0])
    print(f"  [{'OK' if body_ok else 'FAIL'}] 本體照尾版律取到具體實作:{_TAIL_BODY.name} · ScrapeGate {_TAIL_GATE.name}")
    print(f"  [{'OK' if not pinned else 'FAIL'}] 本支沒有字串釘死同族版號(PINVER 0)")
    return 0 if (bridges and surface and gate and body_ok and not pinned) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in _tail_sys.argv else main())
