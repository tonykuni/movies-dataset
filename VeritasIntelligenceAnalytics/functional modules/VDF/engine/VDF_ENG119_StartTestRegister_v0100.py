#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG119_StartTestRegister_v0100 — 啟動、測試、註冊只寫在這一支。

VDF 管理器 v0108 與 VCGC 管理器 v0101 都呼叫本檔，不各寫一份。
對照順序：拒絕清單 → 既有同義字冊 → 本 SSOT。
同義字冊、正規式冊、政策律冊只讀。新詞只放在本 SSOT。撞名就不寫。
啟動只看狀態，不擷取。測試只跑尾版的 --selftest。註冊不執行 registry-sync --apply。
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2]
REG = VIA / "supportive modules" / "registry"
BOOK = REG / "VIA_VDF_StartTestRegister_SSOT_v0100.json"
UNION = REG / "VIA_SSOT_SynonymUnion_v0100.json"
REGEX = REG / "VIA_SSOT_RegexDict_v0100.json"
LAWS = REG / "VIA_Policy_Laws_SSOT_v0100.json"
START = REG / "CGC_MDL209_VdfStart_v0100.py"
SKIP = ("__pycache__", "references/intake", "/_backup", "Retired", "SCOPE_COPY", "_superseded", "_sha", "_from_vap", "_rebuilds", "_bytecode")
TAIL = re.compile(r"_v(\d{4})\.py$")


def _book() -> dict:
    return json.loads(BOOK.read_text(encoding="utf-8"))


def _marked() -> bool:
    return os.environ.get("VIA_FROM_VCGC") == "YES"


def _deny() -> dict:
    return {
        "via": "vcgc",
        "door": "VDF_ENG119_StartTestRegister_v0100",
        "state": "DENY",
        "fetched": False,
        "intake_edited": False,
        "next": "enter through VCGC",
    }


def align() -> dict:
    """Read the three books. Add nothing. A shared synonym is a conflict."""
    book = _book()
    union = UNION.read_text(encoding="utf-8") if UNION.is_file() else ""
    laws = json.loads(LAWS.read_text(encoding="utf-8")) if LAWS.is_file() else {}
    ids = {str(row.get("id")) for row in (laws.get("laws") or [])}
    seen = {}
    conflicts = []
    added = []
    for canon, spec in (book.get("verbs") or {}).items():
        if not re.fullmatch(spec["regex"], spec["argv"]):
            conflicts.append({"canon": canon, "why": "argv misses its own regex"})
        for word in spec.get("synonyms") or []:
            if word in seen:
                conflicts.append({"word": word, "why": "two verbs claim it", "left": seen[word], "right": canon})
            seen[word] = canon
            if f'"{word}"' in union:
                conflicts.append({"word": word, "why": "already in the synonym union"})
            else:
                added.append({"word": word, "canon": canon})
        if any(bad in spec["regex"] for bad in ("talib", "TA-Lib")):
            conflicts.append({"canon": canon, "why": "regex names talib"})
    missing = [pin for pin in book.get("policy_ids") or [] if pin not in ids]
    return {
        "via": "vcgc",
        "door": "VDF_ENG119_StartTestRegister_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "order": book.get("logic_order"),
        "verbs": sorted((book.get("verbs") or {}).keys()),
        "policy_ids": book.get("policy_ids"),
        "policy_missing": missing,
        "regex_book": REGEX.name,
        "regex_book_written": False,
        "synonym_book": UNION.name,
        "synonym_book_written": False,
        "added_here": added,
        "conflicts": conflicts,
        "lock_success": not conflicts and not missing,
        "fetched": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": book.get("do_not"),
        "next": "none" if not conflicts and not missing else "do not register; name the conflict",
    }


def start(run: bool = True) -> dict:
    if not _marked():
        return _deny()
    card = align()
    card["verb"] = "start"
    card["delegates_to"] = START.name
    card["fetched"] = False
    if not run:
        card["ran"] = False
        return card
    spec = importlib.util.spec_from_file_location("vcgc_vdf_start_v0100", START)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    started = module.check()
    card["ran"] = True
    card["started"] = started.get("started")
    card["manager"] = started.get("manager")
    card["open"] = started.get("open")
    card["fetched"] = False
    return card


def _tails() -> dict:
    found = {}
    root = VIA / "functional modules" / "VDF"
    for path in root.rglob("*_v????.py"):
        rel = path.relative_to(VIA).as_posix()
        if any(piece in rel for piece in SKIP):
            continue
        match = TAIL.search(path.name)
        if not match:
            continue
        stem = path.name[: match.start()]
        version = int(match.group(1))
        prior = found.get(stem)
        if prior is None or version > prior[0]:
            found[stem] = (version, path)
    return found


def test(family: str = "") -> dict:
    if not _marked():
        return _deny()
    card = align()
    card["verb"] = "test"
    card["fetched"] = False
    if not card["lock_success"]:
        card["ran"] = False
        return card
    tails = _tails()
    if family:
        hit = tails.get(family)
        if hit is None:
            card["state"] = "ABSENT"
            card["family"] = family
            card["next"] = "name a newest VDF family"
            return card
        chosen = {family: hit}
    else:
        chosen = tails
    rows = []
    env = os.environ.copy()
    env["VIA_FROM_VCGC"] = "YES"
    env["VIA_NET_CONSENT"] = "OFF"
    env.pop("VIA_SCRAPE_CONSENT", None)
    for stem, (version, path) in sorted(chosen.items()):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "--selftest" not in text:
            rows.append({"family": stem, "version": f"{version:04d}", "rc": "NO_DOOR"})
            continue
        try:
            done = subprocess.run(
                [sys.executable, str(path), "--selftest"],
                cwd=str(VIA.parent),
                env=env,
                capture_output=True,
                text=True,
                timeout=12,
            )
            rc = done.returncode
        except subprocess.TimeoutExpired:
            rc = "TIMEOUT"
        rows.append({"family": stem, "version": f"{version:04d}", "rc": rc})
    card["ran"] = True
    card["families"] = len(rows)
    card["rows"] = rows
    card["counts"] = dict(Counter(str(row["rc"]) for row in rows))
    return card


def register() -> dict:
    """The SSOT file is the register. This verb does not write the older books."""
    if not _marked():
        return _deny()
    before = UNION.stat().st_mtime if UNION.is_file() else None
    card = align()
    card["verb"] = "register"
    card["book"] = BOOK.name
    card["registry_apply"] = False
    card["synonym_mtime_same"] = UNION.stat().st_mtime == before if before is not None else False
    if not card["lock_success"]:
        card["registered"] = False
        return card
    card["registered"] = True
    return card


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    book = _book()
    verb = ""
    family = ""
    for token in argv[1:]:
        if token.startswith("--family="):
            family = token.split("=", 1)[1]
        elif token == "--family":
            continue
        elif verb == "" and token in {spec["argv"] for spec in book["verbs"].values()}:
            verb = token
        elif verb == "test" and family == "" and not token.startswith("-"):
            family = token
    if verb == "":
        card = align() if _marked() else _deny()
    elif verb == "start":
        card = start(run=True)
    elif verb == "test":
        card = test(family)
    else:
        card = register()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY":
        return 2
    if card.get("conflicts") or card.get("policy_missing"):
        return 2
    return 0


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = start(run=False).get("state") == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    looked = align()
    registered = register()
    one = test("VDF_ENG109_USMacroList")
    quiet = start(run=False)
    ok = (
        denied
        and looked["lock_success"]
        and not looked["conflicts"]
        and registered["registered"]
        and registered["registry_apply"] is False
        and registered["synonym_book_written"] is False
        and one["rows"][0]["rc"] == 0
        and quiet["fetched"] is False
        and quiet["ran"] is False
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
