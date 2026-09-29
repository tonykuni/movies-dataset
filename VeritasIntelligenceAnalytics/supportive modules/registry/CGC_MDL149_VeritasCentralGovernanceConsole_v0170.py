#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL149_VeritasCentralGovernanceConsole v0170 — 薄尾:元件盤點沿「薄尾鏈」讀(命令冊 dot-source 鏈 · PY 薄尾的前版)

R33 實測實錄(2026-09-29):註冊乾跑報「退役 55」——剛加的 CGC_MDL245 v0101 / via_vrn_logic_book v0112 是薄尾,
  函式留在前版、由 __getattr__ 轉接;盤點只 ast 讀尾版,就把 43 + 12 支還在用的函式當退役。再量全冊:
  命令 181 支有 174 支掛 RETIRED(Register v0244 起是薄尾,只讀尾版那一本)、薄尾 126 支轉接的定義 3,933 個裡 902 個被標退役、
  827 個從沒上冊。這是「薄尾盲點」同一類(全景讀名冊 · 步驟矩陣 · MDL157 命令冊 · ENG073 ⓬ · ENG086 之後第 6 處)。
  ① register_cmds:命令冊沿 dot-source 鏈讀(正主 = CGC_MDL157 v0106+ 的 read();新冊拆掉的函式不算);同名以最新一本為準。
  ② live_components:尾版是薄尾(exec_module 載自己家族的前版)就沿前版往下讀,直到一支實體;前版的類別 / 函式照家族名入冊
     (鍵不變 = 同一個元件;source 記真正定義它的那一版,via 記轉接它的尾版)。尾版自己的定義優先。
  ③ 別名後載的鏈模組(CGC_MDL205 以 vcgc_tails_for_talib_ban 載 v0142)也對齊:同步檢查前 ensure() 一次
     (v0168 同步檢查取 sys.modules 裡第一支 registry_sync;實錄 hub run 後印「退役 1971」就是它拿到沒沿鏈的那支)。
  結果照舊經 v0167 的樹狀態快取(本層另存一份,鍵同)。只增不減:冊的寫入仍只走 registry-sync --apply(要批准)。
其餘照 v0169(thin tail;__getattr__ 轉接)。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。不用 TA-Lib。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                 default=HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0169.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("vcgc_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


_UEC: dict = {}
BOOK_HDR = re.compile(r"^# ==== (Register-VIA-Commands-v\d{4}\.ps1) ====$")


def uec():
    """The command-book chain reader's owner: the newest CGC_MDL157 that has command_book_chain (None when absent)."""
    if "m" not in _UEC:
        _UEC["m"] = None
        for p in sorted(HERE.glob("CGC_MDL157_VIAUniqueEntryControl_v*.py"), key=_vnum, reverse=True):
            try:
                m = PRIOR._load(p, "uec_for_v0170")
            except Exception:
                continue
            if hasattr(m, "command_book_chain"):
                _UEC["m"] = m
                break
    return _UEC["m"]


def register_cmds() -> dict:
    """v0170: the command book read as its whole dot-source chain (newest first; a name defined twice keeps the newest)."""
    books = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"), key=lambda p: int(re.search(r"-v(\d+)$", p.stem).group(1)) if re.search(r"-v(\d+)$", p.stem) else -1)
    if not books:
        return {"state": "ABSENT", "cmds": []}
    p, m = books[-1], uec()
    text = m.read(p) if m else p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    cmds, aliases, seen, book = [], {}, set(), p.name
    for i, ln in enumerate(lines):
        h = BOOK_HDR.match(ln)
        if h:
            book = h.group(1)
            continue
        mm = re.match(r"^function global:(via-[A-Za-z0-9\-]+)", ln)
        if mm and mm.group(1) not in seen:
            name = mm.group(1)
            seen.add(name)
            usage = ""
            for j in range(i - 1, max(-1, i - 8), -1):
                if lines[j].startswith("#") and name in lines[j]:
                    usage = lines[j].lstrip("# ").strip()
                    break
            cmds.append({"cmd": name, "usage": usage[:220], "line": i + 1, "book": book})
        m2 = re.match(r"^Set-Alias -Name (\S+) -Value (via-[A-Za-z0-9\-]+)", ln)
        if m2 and m2.group(1) not in aliases.get(m2.group(2), []):
            aliases.setdefault(m2.group(2), []).append(m2.group(1))
    for c in cmds:
        c["aliases"] = aliases.get(c["cmd"], [])
    return {"state": "OK", "src": p.name, "chain": len(m.command_book_chain(p)) if m else 1, "cmds": cmds}


def is_thin(stem: str, text: str) -> bool:
    """A tail that loads its own family's prior version (exec_module on `<stem>_v…`)."""
    return "exec_module" in text and bool(
        re.search(re.escape(stem) + r"""(?:_v\d{3,4}\.py|_v\*|["']\s*\+)""", text)
        or re.search(r"""_STEM\s*=\s*["']""" + re.escape(stem) + """["']""", text))


def forwarded_defs(tails: list, limit: int = 80) -> dict:
    """{key: row} for the classes / functions a thin tail forwards from its prior chain (read only; ast.parse, never executed)."""
    out: dict = {}
    for stem, q in tails:
        cur, hops = q, 0
        while hops < limit:
            try:
                txt = cur.read_text(encoding="utf-8", errors="replace")
            except OSError:
                break
            if not is_thin(stem, txt):
                break
            older = [p for p in cur.parent.glob(stem + "_v*.py") if 0 <= _vnum(p) < _vnum(cur)]
            if not older:
                break
            nxt, hops = max(older, key=_vnum), hops + 1
            rel, via = nxt.relative_to(VIA).as_posix(), q.relative_to(VIA).as_posix()
            try:
                tree = ast.parse(nxt.read_text(encoding="utf-8", errors="replace"), filename=str(nxt))
            except (SyntaxError, ValueError):
                cur = nxt
                continue

            class V(ast.NodeVisitor):
                def __init__(self):
                    self.stack: list = []

                def _add(self, node, cat):
                    ident = f"{stem}:{'.'.join(self.stack + [node.name])}"
                    out.setdefault(f"{cat}|{ident}", {"key": f"{cat}|{ident}", "category": cat, "identity": ident,
                                                      "source": rel, "line": node.lineno, "via": via})
                    self.stack.append(node.name)
                    self.generic_visit(node)
                    self.stack.pop()

                def visit_ClassDef(self, node):
                    self._add(node, "class")

                def visit_FunctionDef(self, node):
                    self._add(node, "function")

                visit_AsyncFunctionDef = visit_FunctionDef

            V().visit(tree)
            cur = nxt
    return out


def extend(inv: dict) -> dict:
    rows = {r["key"]: r for r in inv.get("rows") or []}
    for c in register_cmds().get("cmds", []):
        rows.setdefault(f"tool|{c['cmd']}", {"key": f"tool|{c['cmd']}", "category": "tool", "identity": c["cmd"], "source": "Register-VIA-Commands"})
    tails = [(r["identity"], VIA / r["source"]) for r in rows.values()
             if r.get("category") in ("engine", "module", "system") and str(r.get("source", "")).endswith(".py")]
    fwd = forwarded_defs(tails)
    added = 0
    for k, r in fwd.items():
        if k not in rows:
            rows[k] = r
            added += 1
    counts: dict = {}
    for r in rows.values():
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    out = dict(inv)
    out.update({"rows": [rows[k] for k in sorted(rows)], "counts": counts, "forwarded": added, "chain_reader": "v0170"})
    return out


def _install() -> int:
    """Swap the effective live_components / register_cmds in every loaded chain module that holds them."""
    mods = [m for m in list(sys.modules.values()) if getattr(m, "__file__", "") and _STEM in str(getattr(m, "__file__", ""))
            and m is not sys.modules.get(__name__)]
    eff = next((m.__dict__["live_components"] for m in mods if callable(m.__dict__.get("live_components")) and "audit" in m.__dict__), None)
    old_rc = next((m.__dict__["register_cmds"] for m in mods if callable(m.__dict__.get("register_cmds"))), None)
    n = 0
    for m in mods:
        if old_rc is not None and m.__dict__.get("register_cmds") is old_rc:
            m.__dict__["register_cmds"] = register_cmds
    if eff is None or getattr(eff, "_v0170", False):
        return 0
    base = getattr(eff, "__wrapped__", eff)
    ext = PRIOR.cached(lambda: extend(base()), name="live_components_v0170")
    ext._v0170 = True
    ext.__wrapped__ = lambda: extend(base())
    _EXT["f"] = ext
    for m in mods:
        if m.__dict__.get("live_components") is eff:
            m.__dict__["live_components"] = ext
            n += 1
    return n


_EXT: dict = {}


def ensure() -> int:
    """Chain modules loaded later under another name (e.g. CGC_MDL205 loads v0142 as `vcgc_tails_for_talib_ban`) get the same
    chain-aware inventory; the v0168 sync check takes the first registry_sync it finds in sys.modules, whichever that is."""
    ext, n = _EXT.get("f"), 0
    if ext is None:
        return 0
    for m in list(sys.modules.values()):
        d = getattr(m, "__dict__", {})
        if _STEM in str(getattr(m, "__file__", "")) and callable(d.get("registry_sync")) and d.get("live_components") is not ext:
            d["live_components"] = ext
            if callable(d.get("register_cmds")):
                d["register_cmds"] = register_cmds
            n += 1
    return n


_V0169_SYNC = PRIOR.sync_check


def sync_check(key: str | None = None) -> dict:
    ensure()
    return _V0169_SYNC(key)


_PATCHED = _install()
for _m in [PRIOR] + [getattr(PRIOR, "PRIOR", None)]:
    if _m is not None and _m.__dict__.get("sync_check") is _V0169_SYNC:
        _m.__dict__["sync_check"] = sync_check


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    rc = register_cmds()
    names = {c["cmd"] for c in rc["cmds"]}
    chk("命令冊沿 dot-source 鏈讀(正主 CGC_MDL157 read)", uec() is not None and rc.get("chain", 1) >= 2 and len(names) >= 150,
        f"鏈 {rc.get('chain')} 本 · 命令 {len(names)}")
    chk("新冊拆掉的命令不算(via-talib / via-taone 由 v0262 拆除)", not ({"via-talib", "via-taone"} & names))
    chk("同名只留最新一本", len(names) == len(rc["cmds"]))
    body = "import importlib.util\nPRIOR_PATH = max(HERE.glob(_STEM + '_v*.py'))\n_spec.loader.exec_module(PRIOR)\n"
    chk("薄尾判定:載自己家族前版 = 薄尾;載別家 = 不是", is_thin("X_MDL001_A", body + "_STEM = \"X_MDL001_A\"\n")
        and not is_thin("X_MDL001_A", "spec.loader.exec_module(m)  # Y_MDL002_B_v0100.py\n"))
    me = Path(__file__)
    fwd = forwarded_defs([(_STEM, me)], limit=3)
    chk("本支前版的定義照家族名入冊(source = 定義它的那一版)", f"function|{_STEM}:sdd_module" in fwd
        and fwd[f"function|{_STEM}:sdd_module"]["source"].endswith("_v0169.py"), f"轉接 {len(fwd)}")
    live = sys.modules[__name__].__dict__.get("_PATCHED")
    chk("盤點已換成沿鏈版(每支持有 live_components 的鏈模組都換)", bool(live), f"換 {live}")
    import importlib.util as _ilu
    sp = _ilu.spec_from_file_location("vcgc_selftest_late_load", HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0142.py")
    late = _ilu.module_from_spec(sp)
    sys.modules[sp.name] = late
    sp.loader.exec_module(late)
    ensure()
    chk("後載的鏈模組(別名載入 v0142,如 CGC_MDL205)同步檢查前也換成沿鏈盤點", late.live_components is _EXT.get("f")
        and PRIOR.PRIOR.sync_check is sync_check)
    sys.modules.pop(sp.name, None)
    b = Path(__file__).read_text(encoding="utf-8")
    chk("抬頭 raw · 帶加速器橋 · 網路橋 · VIA_FROM_VCGC 標記", b.split("\n", 3)[2].startswith('r"""') and "[VIA:ACCEL-BRIDGE" in b
        and "[VIA:NET-BRIDGE" in b and "VIA_FROM_VCGC" in b)
    chk("不含 TA-Lib 匯入", not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", b, re.M))
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(selftest() if a == ["--selftest"] else main())
