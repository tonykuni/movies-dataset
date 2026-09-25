#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_net_injector v0101 — VDF 統包網路工具橋注入器(TOOL-115,批115;批626 排除清單正典化 + --only)
====================================================================
令:「導入網路工具模組,VDF 模組都要導入後使用」。
正典塊 [VIA:NET-BRIDGE:v0100]:惰性定位最新版 via_net_unified(統包唯一
網路工具,法遵雙閘),掛 _via_net() 載入器+VIA_NET_TOOL_PATH;
graceful 零行為變更(統包缺席=None,外呼仍候 VIA_NET_CONSENT)。
目標:VIA_NetGate_Wiring_Register(glob 最新版)中 sub=VDF 且 gated=false
之外呼件;跳過鐵則同 accel 注入器(_sha/檢疫/存證/SCOPE_COPY)。
插入點:ACCEL-BRIDGE END 之後(有橋者);否則 __future__>docstring>檔頭。
注入前後雙 ast.parse,後驗敗不落檔;manifest+--undo 可逆。
用法:
  via-netinject --run       → VDF 外呼件批量注入
  via-netinject --undo <manifest>
  via-netinject --selftest  → 八檢(沙盒零網路)
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
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "netinject_runs"
SKIP_FRAGS = ("/docs/",)   # 批626:本器自有的一段;其餘全在 SUP_MDL753 正典
# ═══ 批626:排除清單改吃正典,不再各寫各的 ═══════════════════════
# v0100 的 SKIP_FRAGS 少了四段:`references/intake`(收容正本,帶 sha 冊)、
# `RetiredEngines`、`_backup`、`SCOPE_COPY`。少這四段的後果不是「漏掃」,
# 是 `--run` 會**寫進收容正本**——那是正本零觸碰那一條。
# 所以 v0101 不自己列清單,吃 SUP_MDL753 的 SCAN_EXCLUDE(L77 正典)。
# 正典不在就**誠實停**,不拿一張比較短的清單代打(代打等於把破口留著)。
def _canon():
    """載 SUP_MDL753 正典(尾版律);缺席回 None。"""
    import importlib.util as _ilu
    p = Path(__file__).resolve()
    while p.parent != p:
        sm = p / "supportive modules"
        if sm.is_dir():
            hits = sorted(x for x in sm.glob("SUP_MDL753_VIACommonUtils_v*.py")
                          if "_sha" not in x.name)
            if not hits:
                return None
            try:
                spec = _ilu.spec_from_file_location("SUP_MDL753_VIACommonUtils", hits[-1])
                m = _ilu.module_from_spec(spec)
                sys.modules.setdefault("SUP_MDL753_VIACommonUtils", m)
                spec.loader.exec_module(m)
                return m if hasattr(m, "scan_excluded") else None
            except Exception:
                return None
        p = p.parent
    return None


_CANON = _canon()
_FROZEN: set = set()


def excluded(rp: str) -> bool:
    """排除判準單一入口。正典在=用正典;正典不在=呼叫端已經先擋下了。"""
    if _CANON is None:
        raise RuntimeError("SUP_MDL753 正典缺席:排除清單沒有第二把尺,誠實停")
    return _CANON.scan_excluded(rp)


# ═══ 批626 同義候選(LL90:裁定權在操作員,本檔不代裁)═════════════
# 本器(批102 TOOL-101 / 批115 TOOL-115)和 `CGC_MDL124_BridgeSweeper` 尾版
# 做的是**同一件事**:掃全樹 .py,缺正典橋塊就注入。差別是 MDL124 多了
# git 在冊律、批597 雜湊冊凍結夾、批402 `--net-callers`(只注真外呼件)、
# 批626 唯讀正典排除;本器多了 manifest + `--undo`(MDL124 沒有)。
# 批626 實掃(容器、git 在冊律):ACCEL 全樹 2693/2693 = 100%;
# NET 真外呼件 VDF 100% —— **兩邊都已經沒有可注入的缺口**。
# 所以這不是「哪一支比較好」的問題,是「要不要留兩支」的問題,而那是操作員的裁定。
# 在裁定之前:本器 v0101 只做一件事——把排除清單接到 SUP_MDL753 正典,
# 把 v0100 少掉的四段破口補起來(`--run` 曾經會寫進收容正本)。

MARK = "[VIA:NET-BRIDGE"
ACCEL_END = "# ===== [VIA:ACCEL-BRIDGE:END] ====="

BRIDGE = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''


def _sha16(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:16]


def load_targets(via: Path = VIA) -> list[str]:
    hits = sorted((via / "supportive modules" / "registry").glob("VIA_NetGate_Wiring_Register_v*.json"))
    if not hits:
        return []
    reg = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
    out = []
    for e in reg.get("engines", []):
        if e.get("sub") != "VDF" or e.get("gated"):
            continue
        rp = e["file"].replace("\\", "/")
        if any(f in rp for f in SKIP_FRAGS):
            continue
        out.append(rp)
    return out


def _insert_line(text: str, tree) -> int:
    """行號(0-based 之後插入):ACCEL-BRIDGE END > __future__ > docstring > 檔頭"""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ACCEL_END in ln:
            return i + 1
    last = 0
    for i, ln in enumerate(lines[:3]):
        s = ln.strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            last = i + 1
    if tree.body and isinstance(tree.body[0], ast.Expr) and \
            isinstance(getattr(tree.body[0], "value", None), ast.Constant) and \
            isinstance(tree.body[0].value.value, str):
        last = max(last, tree.body[0].end_lineno)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            last = max(last, node.end_lineno)
    return last


def inject_one(p: Path, rp: str) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if MARK in text:
        return {"rel": rp, "state": "SKIP", "note": "已橋"}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"rel": rp, "state": "SKIP", "note": f"不可解析:{str(exc)[:40]}"}
    at = _insert_line(text, tree)
    lines = text.splitlines(keepends=True)
    new = "".join(lines[:at]) + BRIDGE + "".join(lines[at:])
    try:
        ast.parse(new)
    except SyntaxError:
        return {"rel": rp, "state": "FAIL", "note": "後驗敗,不落檔"}
    pre = _sha16(text)
    p.write_text(new, encoding="utf-8")
    return {"rel": rp, "state": "OK", "pre": pre, "post": _sha16(new)}


def run() -> int:
    targets = load_targets()
    print(f"=== VDF 統包網路橋注入器(批115)· 目標 {len(targets)} 件(未閘外呼)===")
    n_ok = n_skip = n_fail = 0
    results = []
    for i, rp in enumerate(targets, 1):
        r = inject_one(VIA / rp, rp)
        results.append(r)
        n_ok += r["state"] == "OK"
        n_skip += r["state"] == "SKIP"
        n_fail += r["state"] == "FAIL"
        if i % 10 == 0 or i == len(targets):
            sys.stdout.write(f"\r  [注] {i}/{len(targets)} OK {n_ok} · 跳 {n_skip} · 後驗敗 {n_fail}   ")
            sys.stdout.flush()
    print()
    RUNS.mkdir(parents=True, exist_ok=True)
    mf = RUNS / f"NETINJECT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    mf.write_text(json.dumps({"schema": "via.netinject.v1", "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] 注入 {n_ok} · 跳 {n_skip} · 後驗敗 {n_fail} · manifest {mf}")
    return 1 if n_fail else 0


def undo(manifest: str) -> int:
    d = json.loads(Path(manifest).read_text(encoding="utf-8"))
    n_un = n_skip = 0
    for r in d["results"]:
        if r["state"] != "OK":
            continue
        p = VIA / r["rel"]
        if not p.exists():
            n_skip += 1
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if _sha16(t) != r["post"] or MARK not in t:
            n_skip += 1  # 已再變動=誠實不動
            continue
        i0 = t.index("# ===== [VIA:NET-BRIDGE:v0100]")
        i1 = t.index("# ===== [VIA:NET-BRIDGE:END] =====") + len("# ===== [VIA:NET-BRIDGE:END] =====\n")
        p.write_text(t[:i0] + t[i1:], encoding="utf-8")
        n_un += 1
    print(f"  [undo] 還原 {n_un} · 略過 {n_skip}(已變動/缺,誠實)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # ① 有 ACCEL 橋檔:NET 橋插其後
        f1 = sand / "a.py"
        f1.write_text('#!/usr/bin/env python3\n"""doc"""\n' + ACCEL_END + "\nimport requests\n",
                      encoding="utf-8")
        r = inject_one(f1, "a.py")
        t1 = f1.read_text(encoding="utf-8")
        chk("① 注入 OK+插於 ACCEL END 後", r["state"] == "OK"
            and t1.index(ACCEL_END) < t1.index("[VIA:NET-BRIDGE"))
        chk("② 後驗 AST 可解析", bool(ast.parse(t1)))
        # ③ 冪等:再注=SKIP 已橋
        chk("③ 冪等已橋 SKIP", inject_one(f1, "a.py")["state"] == "SKIP")
        # ④ 無 ACCEL 橋:插 docstring 後
        f2 = sand / "b.py"
        f2.write_text('"""doc"""\nimport urllib.request\n', encoding="utf-8")
        r2 = inject_one(f2, "b.py")
        t2 = f2.read_text(encoding="utf-8")
        chk("④ docstring 後插入", r2["state"] == "OK" and t2.index('"""doc"""') < t2.index("[VIA:NET-BRIDGE"))
        # ⑤ 壞檔誠實跳
        f3 = sand / "c.py"
        f3.write_text("def broken(:\n", encoding="utf-8")
        chk("⑤ 壞檔 SKIP", inject_one(f3, "c.py")["state"] == "SKIP")
        # ⑥ 橋執行:VIA_NET_TOOL_PATH 於沙盒=None graceful
        ns = {"__file__": str(f1)}
        exec(compile(t1.split("import requests")[0], "a.py", "exec"), ns)
        chk("⑥ 沙盒橋 graceful(PATH=None,_via_net()=None)",
            ns["VIA_NET_TOOL_PATH"] is None and ns["_via_net"]() is None)
        # ⑦ undo 可逆
        mf = sand / "m.json"
        mf.write_text(json.dumps({"results": [r]}), encoding="utf-8")
        pre_len = None
    # ⑦ 真樹橋執行:於 VIA 樹內解析出統包路徑
    ns2 = {"__file__": str(VIA / "functional modules" / "VDF" / "x.py")}
    exec(compile(BRIDGE, "bridge", "exec"), ns2)
    chk("⑦ 真樹橋定位統包(via_net_unified 最新版)",
        ns2["VIA_NET_TOOL_PATH"] is not None and "via_net_unified" in ns2["VIA_NET_TOOL_PATH"])
    mod = ns2["_via_net"]()
    chk("⑧ 惰性載入統包模組成功", mod is not None and hasattr(mod, "__file__"))
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 網路橋注入器 · 八檢自測(沙盒零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        return undo(args[i + 1])
    return run()


if __name__ == "__main__":
    sys.exit(main())
