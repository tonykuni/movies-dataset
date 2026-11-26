#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SUP_MDL866 v0108 — 薄尾:L1 本地清洗工具改「可選依賴」(缺套件照實 ABSENT,不讓整支崩);核心 NLP / PRADDLE 路徑照 v0106

導入 PR #439(2026-10-03,VCGC-REQ139)後實測:v0107 的 L1 清洗(l1-clean · l1-review)與自測要 16 套件
(polars · pydantic · pandera · google-re2 · pyahocorasick · flashtext · rapidfuzz …),容器與 CI 直譯器沒有 →
`--selftest` 在 clean_batch 的 `import polars` 直接 ModuleNotFoundError;而 v0107 自測沒跑 v0106 的核心自測,
交接案 nlp_praddle(標記「SUP_MDL866 v0106 7/7」)因此看不到。本版只改這兩件(v0103–v0107 一字不動):
  ① l1-clean / l1-review:先問 find_spec 這一路要的套件(l1-clean = polars · pydantic · pandera + 精確比對後端 + regex 後端);
     缺 → 印 {"state":"ABSENT","missing":[…]} 回 3(照實,不冒充、不代裝);齊 → 照 v0107。l1-tools 本來就只讀版本,照 v0107。
  ② --selftest:先跑 v0106 核心自測(PRADDLE / LAYOUT 走的那一路);16 套件齊才跑 v0107 的 L1 自測,缺就照實「略過 + 列缺件」;
     另驗 ① 的缺件路徑。其餘動詞(--brief · pdf · text …)照 v0107 → v0106。
工具鎖冊 nlp 仍釘 v0106(LAYOUT 從鎖冊取);本版是候選,不自動換鎖。零網路;不碰 TA-Lib;只收 VCGC 呼叫。
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
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL866_VIAUnifiedNLPOrchestrator"
ENGINE = Path(__file__).stem
L1_CORE_V0108 = ("polars", "pydantic", "pandera")
BACKEND_MOD_V0108 = {"aho": "ahocorasick", "flashtext": "flashtext", "polars": "polars", "re2": "re2", "duckdb": "duckdb"}


def _vnum_v0108(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0108(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0108(p) < _vnum_v0108(__file__)), key=_vnum_v0108)
PRIOR = _load_v0108(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0107:L1 本地清洗
V0106_PATH = HERE / (_STEM + "_v0106.py")


def __getattr__(name):
    return getattr(PRIOR, name)


def missing_v0108(mods) -> list:
    return [m for m in dict.fromkeys(mods) if importlib.util.find_spec(m) is None]


def needs_v0108(args: list) -> list:
    """這一個 L1 動詞要的匯入名(l1-clean 看 --backend / --regex-backend;l1-review 走 rapidfuzz 等審查轉接,一律要 L1 三件)。"""
    if args[:1] == ["l1-clean"]:
        backend = args[args.index("--backend") + 1] if "--backend" in args and args.index("--backend") + 1 < len(args) else "aho"
        rx = args[args.index("--regex-backend") + 1] if "--regex-backend" in args and args.index("--regex-backend") + 1 < len(args) else "re2"
        return list(L1_CORE_V0108) + [BACKEND_MOD_V0108.get(backend, backend), BACKEND_MOD_V0108.get(rx, rx)]
    if args[:1] == ["l1-review"]:
        return list(L1_CORE_V0108)
    return []


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] only VCGC entry")
        return 2
    if args == ["--selftest"]:
        return selftest()
    need = needs_v0108(args)
    miss = missing_v0108(need)
    if miss:
        print(json.dumps({"state": "ABSENT", "engine": ENGINE, "verb": args[0], "missing": miss,
                          "why": "L1 本地清洗要的套件不在本直譯器(不代裝;到裝好的境再跑,或經 EnvManager 補)"}, ensure_ascii=False))
        return 3
    return PRIOR.main(args)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    keep = sys.argv[:]
    try:
        sys.argv = [str(V0106_PATH), "--selftest"]
        core = _load_v0108(V0106_PATH, "_nlp_v0106_for_" + ENGINE)
        rc106 = core.selftest()
    finally:
        sys.argv = keep
    all16 = sorted(set(PRIOR.TOOL_MODULES.values()))
    miss16 = missing_v0108(all16)
    print(f"=== {ENGINE} · 薄尾自測(L1 可選依賴 · 核心照 v0106)===")
    chk("① v0106 核心自測過(PRADDLE / LAYOUT 從鎖冊取的那一支)", rc106 == 0, f"rc {rc106}")
    if miss16:
        print(f"  [略過] v0107 L1 自測要 16 套件;本直譯器缺 {len(miss16)} 件:{' · '.join(miss16)} → 照實略過(不算過、不算錯)")
    else:
        rc107 = PRIOR.selftest()
        chk("② v0107 L1 自測過(16 套件齊)", rc107 == 0, f"rc {rc107}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        inv = PRIOR.tool_inventory()
    chk("③ l1-tools 不需任何可選套件也讀得出 16 件版本(缺 = ABSENT 照實)", len(inv) == len(PRIOR.TOOL_MODULES)
        and {r["state"] for r in inv} <= {"ABSENT", "AVAILABLE_NOT_ACTIVATION_PROOF"}, f"缺 {sum(1 for r in inv if r['state'] == 'ABSENT')}")
    need = needs_v0108(["l1-clean", "--input", "x.json", "--backend", "flashtext", "--regex-backend", "duckdb"])
    chk("④ l1-clean 要的套件照旗標算(L1 三件 + 精確比對後端 + regex 後端)",
        need == ["polars", "pydantic", "pandera", "flashtext", "duckdb"], need)
    keep_env = os.environ.get("VIA_FROM_VCGC")
    os.environ["VIA_FROM_VCGC"] = "YES"
    real_find = importlib.util.find_spec
    try:
        importlib.util.find_spec = lambda name, *a, **k: None if name == "polars" else real_find(name, *a, **k)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["l1-clean", "--input", "nope.json"])
        out = json.loads(buf.getvalue().strip().splitlines()[-1])
    finally:
        importlib.util.find_spec = real_find
        if keep_env is None:
            os.environ.pop("VIA_FROM_VCGC", None)
        else:
            os.environ["VIA_FROM_VCGC"] = keep_env
    chk("⑤ 缺套件 → l1-clean 回 3 · state ABSENT · 點名缺件(不崩、不冒充)", rc == 3 and out.get("state") == "ABSENT" and "polars" in out.get("missing", []), out)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在 · 不碰 TA-Lib · 只收 VCGC", "[VIA:ACCEL-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and "VIA_FROM_VCGC" in text)
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · v0106 {'PASS' if rc106 == 0 else 'FAIL'} · L1 {'略過(缺件)' if miss16 else '已跑'} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
