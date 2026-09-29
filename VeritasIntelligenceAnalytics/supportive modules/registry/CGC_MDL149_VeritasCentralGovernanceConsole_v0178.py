#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0178 — 薄尾:SSOT 全景入口 · 系統管理器薄尾沿鏈讀(上行七處假缺)· AI 必用功能卡

操作員令(側線 2026-09-29 i):「VCGC TO VDF TO VRN 全部檢測 · SSOT / 正則 / 同義字 / 自動編號 / 命名 / 註冊功能強化 ·
SSOT 全景式檢視 · 自動自適應式上下單向檢測到底」「盤點中央控管功能架構還那些缺漏 · 補強」
「AI 進入讀取後開始使用 · 充分讓 AI 知道功能及使用及必用功能寫入」。
  ① manager_names():系統管理器 v0149 / v0150 是薄尾(v0150 exec v0148 本體),ENGINE_FORMAL_NAMES 字面只在 v0148;
     前版只用正則讀「最新那一本」的文字 → VDF / VRN 管理器的上行七處 manager 格恆為假缺(6/7)。本版沿檔內點名的
     同族舊版一路讀到本體(由舊到新合併;尾版字面 .pop("鍵") 照除),鏈上每支定義它的前版模組一併換成本版。
  ② ssot panorama [--full] [--json] [--no-write]:經既有 run 路徑(同一道閘與事件紀錄)派給 CGC_MDL247_SSOTPanorama。
  ③ functions [--json]:照 VIA_AI_FunctionCard_SSOT 冊印 AI 必用功能卡(順序 · 指令 · 何時用 · 做什麼 · 禁止);
     token(非 --json)印完原卡後,尾端加三行必用摘要與指路 —— AI 第一步就看得到;--json 保持純 JSON 一字不動。
其餘照 v0177(handoff · go 前交接閘 · 原 PowerShell 編排不變)。
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

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0178", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
CARD_GLOB = "VIA_AI_FunctionCard_SSOT_v*.json"
MANAGER_GLOB = "VIA_SYSTEM_MANAGER_v*.py"
_V0142_MANAGER_NAMES = PRIOR.manager_names


def __getattr__(name):
    return getattr(PRIOR, name)


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


# ---------------------------------------------------------------- ① manager names through the thin-tail chain
def manager_chain(p: Path, seen: set | None = None) -> list:
    """The newest system manager plus every same-family older file it names (exec / load), newest first."""
    seen = set() if seen is None else seen
    if p in seen or not p.is_file():
        return []
    seen.add(p)
    text = p.read_text(encoding="utf-8", errors="replace")
    out = [(p, text)]
    for name in re.findall(r"VIA_SYSTEM_MANAGER_v\d+\.py", text):
        q = p.parent / name
        if q != p and _vnum(q) < _vnum(p):
            out += manager_chain(q, seen)
    return out


def _block(text: str, key: str) -> dict:
    m = re.search(key + r"\s*=\s*\{(.*?)\n\}", text, flags=re.S)
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1))) if m else {}


def manager_names(folder: Path | None = None) -> dict:
    folder = VIA if folder is None else folder
    hits = [p for p in folder.glob(MANAGER_GLOB) if _vnum(p) >= 0]
    if not hits:
        return {"state": "ABSENT", "tasks": {}, "engines": {}}
    newest = max(hits, key=_vnum)
    chain = manager_chain(newest)
    tasks, engines = {}, {}
    for _, text in reversed(chain):                            # oldest first; a newer file only adds or pops
        tasks.update(_block(text, "TASK_FORMAL_NAMES"))
        engines.update(_block(text, "ENGINE_FORMAL_NAMES"))
        for key in re.findall(r'TASK_FORMAL_NAMES\.pop\(\s*"([^"]+)"', text):
            tasks.pop(key, None)
        for key in re.findall(r'ENGINE_FORMAL_NAMES\.pop\(\s*"([^"]+)"', text):
            engines.pop(key, None)
    return {"state": "OK", "src": newest.name, "chain": [p.name for p, _ in chain], "tasks": tasks, "engines": engines}


def _chain_modules() -> list:
    """Every loaded VCGC module (any version, however its prior attribute is named) — same sweep as v0174."""
    me = sys.modules.get(__name__)
    return [m for m in list(sys.modules.values())
            if m is not None and m is not me and _STEM in str(getattr(m, "__file__", "") or "")]


def install() -> int:
    """Every loaded VCGC chain module that defines manager_names now calls this version (status / page / managers alike)."""
    n = 0
    for m in _chain_modules():
        if "manager_names" in vars(m) and vars(m)["manager_names"] is not manager_names:
            m.manager_names = manager_names
            n += 1
    return n


_PATCHED = install()


# ---------------------------------------------------------------- ③ AI function card
def function_card(path: Path | None = None) -> dict | None:
    if path is None:
        hits = [p for p in HERE.glob(CARD_GLOB) if _vnum(p) >= 0]
        path = max(hits, key=_vnum) if hits else None
    if path is None or not Path(path).is_file():
        return None
    card = json.loads(Path(path).read_text(encoding="utf-8"))
    card["_src"] = Path(path).name
    return card


def render_card(card: dict) -> str:
    lines = [f"[AI 必用功能卡] {card['_src']} · 進場照順序用;指令從倉根照貼(V = VCGC 尾版;E = token 鎖版工具)"]
    for s in card.get("must_use") or []:
        lines.append(f"  {s['step']:>2}. {s['id']:<14} {s['cmd']}")
        lines.append(f"      何時:{s['when']} · 做什麼:{s['what']}")
    tools = card.get("token_tools") or {}
    if tools:
        lines.append("  [省 Token 工具] " + " · ".join(f"{k}:{v}" for k, v in tools.items()))
    for d in card.get("doors") or []:
        lines.append(f"  [門] {d['verb']:<34} {d['what']}")
    for n in card.get("never") or []:
        lines.append(f"  [禁] {n}")
    return "\n".join(lines)


def card_summary(card: dict) -> list:
    steps = card.get("must_use") or []
    return [f"[必用功能] {' → '.join(s['id'] for s in steps)}(共 {len(steps)} 步;全卡:via-vcgc functions)",
            "[必用功能] 改薄尾家族前先 chain · 動 SSOT / 編號 / 註冊前後各跑一次 ssot panorama · 編號寫入後 audit 必須 遺失 0 · 改身分 0 · 重號 0",
            "[必用功能] 禁:TA-Lib · 改 .ps1(L70)· 裝套件 · 代設同意閘 · 格子 --help;黃不是綠"]


# ---------------------------------------------------------------- main
def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:2] == ["ssot", "panorama"]:
        return PRIOR.main(["run", "CGC_MDL247_SSOTPanorama", *args[2:]])
    if args[:1] == ["functions"] and os.environ.get("VIA_FROM_VCGC") == "YES":
        card = function_card()
        if card is None:
            print(json.dumps({"via": "vcgc", "verb": "functions", "state": "ABSENT", "why": f"{CARD_GLOB} 不在"}, ensure_ascii=False))
            return 3
        print(json.dumps(card, ensure_ascii=False, indent=1) if "--json" in args else render_card(card))
        return 0
    rc = PRIOR.main(args)
    if args[:1] == ["token"] and "--json" not in args and os.environ.get("VIA_FROM_VCGC") == "YES":
        card = function_card()
        if card is not None:
            print("\n".join(card_summary(card)))
    return rc


def help_catalog():
    card = PRIOR.help_catalog()
    card.update(entry=Path(__file__).name, previous=PRIOR_PATH.name, ssot_panorama="ssot panorama [--full] [--json] [--no-write]",
                functions="functions [--json](AI 必用功能卡,正本 VIA_AI_FunctionCard_SSOT)")
    return card


# ---------------------------------------------------------------- selftest
def selftest():
    import contextlib
    import io
    import tempfile
    from unittest.mock import Mock, patch
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    real = manager_names()
    old = _V0142_MANAGER_NAMES()
    chk("① 實樹:系統管理器薄尾沿鏈讀,VDF / VRN 管理器都在名冊(前版只讀最新一本 → 讀不到 = 上行七處假缺)",
        "VDF_SystemManager" in real["engines"] and "VRN_SystemManager" in real["engines"]
        and not ("VDF_SystemManager" in (old.get("engines") or {})),
        f"鏈 {real.get('chain')} · 本版 {len(real['engines'])} 名 · 前版 {len(old.get('engines') or {})} 名")
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "VIA_SYSTEM_MANAGER_v0100.py").write_text('ENGINE_FORMAL_NAMES = {\n    "A": "甲",\n    "B": "乙",\n}\n'
                                                       'TASK_FORMAL_NAMES = {\n    "t": "任務",\n}\n', encoding="utf-8")
        (d / "VIA_SYSTEM_MANAGER_v0101.py").write_text('BODY = "VIA_SYSTEM_MANAGER_v0100.py"\nexec(open(BODY).read())\n'
                                                       'ENGINE_FORMAL_NAMES.pop("B", None)\n', encoding="utf-8")
        (d / "VIA_SYSTEM_MANAGER_v0102.py").write_text('# unrelated tail that names nothing\n', encoding="utf-8")
        mid = manager_names(d)
        (d / "VIA_SYSTEM_MANAGER_v0102.py").unlink()
        got = manager_names(d)
    chk("② 合成鏈:尾版 exec 本體 → 讀到本體名冊;尾版字面 pop 照除;不點名任何舊版的尾版 = 誠實讀不到",
        got["engines"] == {"A": "甲"} and got["tasks"] == {"t": "任務"} and got["chain"] == ["VIA_SYSTEM_MANAGER_v0101.py", "VIA_SYSTEM_MANAGER_v0100.py"]
        and mid["engines"] == {}, {"got": got["engines"], "mid": mid["engines"]})
    owners = [m for m in _chain_modules() if "manager_names" in vars(m)]
    chk("③ 鏈上定義 manager_names 的前版模組都換成本版(status / page / 管理器上行同一把尺;至少換到 1 支,不空轉)",
        _PATCHED >= 1 and owners and all(vars(m)["manager_names"] is manager_names for m in owners), f"換 {_PATCHED} 支 · 鏈上定義者 {len(owners)} 支")
    dispatch = Mock(return_value=5)
    with patch.object(PRIOR, "main", dispatch):
        rc = main(["ssot", "panorama", "--full"])
        route = dispatch.call_args.args[0]
    chk("④ ssot panorama 經既有 run 路徑派給 CGC_MDL247(同一道閘與事件紀錄)", rc == 5 and route == ["run", "CGC_MDL247_SSOTPanorama", "--full"], route)
    card = {"_src": "t.json", "must_use": [{"step": 1, "id": "token", "cmd": "via-vcgc token", "when": "進場", "what": "卡"}],
            "token_tools": {"read": "骨架卡"}, "doors": [{"verb": "go", "what": "整輪"}], "never": ["TA-Lib"]}
    text = render_card(card)
    chk("⑤ 功能卡:照冊印順序 · 指令 · 何時 · 做什麼 · 工具 · 門 · 禁止", all(s in text for s in ("1. token", "何時:進場", "[省 Token 工具] read:骨架卡",
                                                                               "[門] go", "[禁] TA-Lib")))
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    with patch.dict(os.environ, env), patch.object(PRIOR, "main", Mock(side_effect=lambda a: print("原卡") or 0)), \
            patch.object(sys.modules[__name__], "function_card", return_value=card):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_tok = main(["token"])
        jbuf = io.StringIO()
        with contextlib.redirect_stdout(jbuf):
            main(["token", "--json"])
    chk("⑥ token 卡尾端加必用摘要(原卡照印在前);token --json 保持原樣", rc_tok == 0 and buf.getvalue().startswith("原卡")
        and "[必用功能] token" in buf.getvalue() and "[必用功能]" not in jbuf.getvalue())
    with patch.dict(os.environ, env), patch.object(sys.modules[__name__], "function_card", return_value=None):
        fbuf = io.StringIO()
        with contextlib.redirect_stdout(fbuf):
            rc_abs = main(["functions"])
    chk("⑦ 功能卡冊不在 = ABSENT rc 3(不編)", rc_abs == 3 and "ABSENT" in fbuf.getvalue())
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔頭 · 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[VCGC v0178] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
