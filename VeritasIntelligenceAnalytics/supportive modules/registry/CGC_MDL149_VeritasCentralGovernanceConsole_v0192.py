#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0192 — 薄尾:新動詞 `mcp`(多 AI 平台 MCP 設定引擎 VIA_MCP_Engine 的 VCGC 入口)。

操作員 2026-11-05 令(原話):「UPGRADE AGAIN AND ADDD VERSION NO. ON THE NAME. OPTIMIZE TEST DEBUG USER-TEST DEBUG TILL IT WORKS.
ADD IT TO VCGC  建一個 PR」(承同日「完整泛用型VIA MCP Engine 使用者介面分類簡單化 只用滑鼠作業即可如 +」
「VIA_MCP_Engine.py backend py + front-end html u/i 高整合高自動化自適應式一個平台皆可新增最多五個」)。
本版只加一件:`via-vcgc mcp <子指令>` → 轉接到倉根 `VIA_MCP_Engine/VIA_MCP_Engine_v*.py` 尾版(glob 取最大版號)的 main();
  mcp(不帶參數)印一張短卡(版本 · 尾版路徑 · 子指令);`mcp serve` 開本機滑鼠操作頁;`mcp doctor` 環境偵測;
  `mcp selftest` 引擎離線自測;其餘子指令(platforms · catalog · add · remove · apply · probe · token …)原樣下放。
  `help` 照前版印完再補 mcp 一段。其餘動詞一字不改,照 v0191 → PRIOR 鏈。
引擎本體在 VIA 樹外(倉根 VIA_MCP_Engine/),是獨立工具:不讀寫 VRN-1 / VRN-2 / VDF / VCGC 的正本 / 冊 / 號 / 檔;
本薄尾零網路(引擎的 GitHub Token 驗證只在操作員按下時才連線,不在本檔)。VIA_FROM_VCGC=YES 才放行,同前版。不碰 TA-Lib;不代設同意閘。
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

import contextlib
import importlib.util
import io
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
_ENGINE_STEM = "VIA_MCP_Engine"
_ENGINE_DIR_NAME = "VIA_MCP_Engine"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)\.(?:py|html)$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0192", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0191
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0188 = PRIOR.V0188


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------------------------------------------------------------- mcp:引擎尾版定位與轉接
def repo_root() -> Path:
    """倉根 = 往上找到含 VeritasIntelligenceAnalytics 的那一層。"""
    p = HERE
    while p.parent != p:
        if (p / "VeritasIntelligenceAnalytics").is_dir():
            return p
        p = p.parent
    return HERE.parents[3] if len(HERE.parents) > 3 else HERE


def engine_tail(root: Path | None = None) -> Path | None:
    d = (root or repo_root()) / _ENGINE_DIR_NAME
    hits = [p for p in d.glob(_ENGINE_STEM + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def load_engine(tail: Path | None = None):
    tail = tail or engine_tail()
    if tail is None:
        return None
    name = f"via_mcp_engine_for_vcgc_{_vnum(tail)}"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, tail)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


MCP_USAGE = (
    "  mcp                           MCP 設定引擎短卡(版本 · 尾版 · 子指令;零寫入)\n"
    "  mcp serve [--port N]          開本機滑鼠操作頁:點平台 → 按 + 加 MCP(每平台最多 5)→ 套用 / 測試啟動 / Token 唯讀驗證\n"
    "  mcp doctor | platforms | catalog | list            環境偵測 / 平台 / 目錄 / 目前指派(只讀)\n"
    "  mcp add <平台> <MCP> [k=v] · mcp remove · mcp apply <平台> [--dry-run] · mcp probe <平台> [名]\n"
    "  mcp token check | readonly-test --repo o/r [--temp]  GitHub Token 範圍 / 讀成功寫被拒(寫入意外成功自動清理)\n"
    "  mcp selftest                  引擎離線自測(假 HOME · 假 GitHub;不連網、不碰真設定)\n"
)


def mcp_card(tail: Path | None, mod) -> str:
    ver = getattr(mod, "VERSION", "?") if mod else "ABSENT"
    html = (tail.with_suffix(".html") if tail else None)
    lines = [f"[mcp] VIA_MCP_Engine {ver} · 尾版 {tail if tail else 'ABSENT(倉根 VIA_MCP_Engine/ 沒有 VIA_MCP_Engine_v*.py)'}"
             f" · 前端 {'在' if html and html.exists() else '缺'} · 每平台上限 {getattr(mod, 'MAX_SERVERS_PER_PLATFORM', 5) if mod else 5}",
             "[mcp] 引擎在 VIA 樹外,獨立運作;只讀他系統(不碰 VRN-1 / VRN-2 / VDF / VCGC 正本)。子指令:", MCP_USAGE.rstrip()]
    return "\n".join(lines)


def run_mcp(args: list[str]) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[mcp] 只收 VCGC 入口:VIA_FROM_VCGC=YES via-vcgc mcp …", file=sys.stderr)
        return 2
    tail = engine_tail()
    mod = load_engine(tail) if tail else None
    if not args:
        print(mcp_card(tail, mod))
        return 0 if mod else 1
    if mod is None:
        print(mcp_card(tail, mod), file=sys.stderr)
        return 1
    rc = mod.main(list(args))
    return int(rc or 0)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "mcp":
        return run_mcp(args[1:])
    rc = PRIOR.main(argv)
    if args[:1] == ["help"]:
        print("  [v0192 新增] " + MCP_USAGE.strip().splitlines()[0].strip())
        print(MCP_USAGE.rstrip("\n").split("\n", 1)[1])
    return rc


def selftest() -> int:
    keep_file = PRIOR.__dict__.get("__file__")
    PRIOR.__dict__["__file__"] = str(Path(__file__).resolve())      # 前版鏈「尾版 = 自己」的檢查指向目前生效入口(本檔)
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.__dict__["__file__"] = keep_file
    print("=== VCGC v0192 · 薄尾自測(mcp 動詞 → VIA_MCP_Engine 尾版)===")
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    chk("① 前版鏈自測過(v0191 → v0190 → …)", prior_rc == 0, f"rc {prior_rc}")
    tail = engine_tail()
    chk("② 倉根 VIA_MCP_Engine/ 找到引擎尾版(帶版號)且同名 .html 在",
        tail is not None and tail.with_suffix(".html").is_file() and _vnum(tail) >= 101, getattr(tail, "name", tail))
    mod = load_engine(tail) if tail else None
    chk("③ 引擎可載入:VERSION 與檔名版號一致 · 上限 5 · main 可呼叫",
        mod is not None and getattr(mod, "VERSION", "") == f"v{_vnum(tail):04d}" and getattr(mod, "MAX_SERVERS_PER_PLATFORM", 0) == 5
        and callable(getattr(mod, "main", None)), getattr(mod, "VERSION", None))
    keep_env = os.environ.get("VIA_FROM_VCGC")
    os.environ.pop("VIA_FROM_VCGC", None)
    buf_err = io.StringIO()
    with contextlib.redirect_stderr(buf_err):
        rc_blocked = run_mcp([])
    chk("④ 沒有 VIA_FROM_VCGC=YES → rc 2 不放行", rc_blocked == 2 and "VIA_FROM_VCGC" in buf_err.getvalue())
    os.environ["VIA_FROM_VCGC"] = "YES"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_card = main(["mcp"])
    card = buf.getvalue()
    chk("⑤ `mcp` 短卡 rc 0 · 帶版本 · 帶子指令 · 零寫入", rc_card == 0 and "VIA_MCP_Engine v" in card and "mcp serve" in card)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc_ver = main(["mcp", "version"])
    chk("⑥ 子指令原樣下放:`mcp version` 由引擎回答", rc_ver == 0 and "VIA_MCP_Engine v" in buf.getvalue(), buf.getvalue().strip()[:40])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        rc_self = main(["mcp", "selftest"]) if mod is not None else 1
    verdict = [ln for ln in buf.getvalue().splitlines() if ln.startswith("[計] VIA_MCP_Engine")]
    chk("⑦ `mcp selftest` 引擎離線自測 PASS(假 HOME · 假 GitHub)", rc_self == 0 and verdict and verdict[-1].endswith("PASS"),
        verdict[-1] if verdict else "(沒有判決行)")
    if keep_env is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = keep_env
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 只有單獨 --selftest 跑中央自測:run X --selftest 照路由給 X",
        bool(re.search(r'^\s+sys\.exit\(selftest\(\) if sys\.argv\[1:\] == \["--selftest"\] else main\(\)\)', src, re.M)))
    chk("⑨ 加速器橋在 · 只收 VCGC(VIA_FROM_VCGC)· 本檔零網路 · 不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "VIA_FROM_VCGC" in src
        and not re.search(r"^\s*(import|from)\s+(urllib|requests|http\.client|socket|talib)\b", src, re.M))
    print(f"  [計] VCGC v0192 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(selftest() if sys.argv[1:] == ["--selftest"] else main())    # 只有單獨 --selftest 跑中央自測;run X --selftest 照路由給 X(v0176 起的規矩)
