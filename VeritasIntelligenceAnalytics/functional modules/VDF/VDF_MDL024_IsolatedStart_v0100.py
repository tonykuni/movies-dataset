#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF isolated start. One file. Does not import the manager chain, VRN, VCGC, or Celeritas.

  py -3 VDF_MDL024_IsolatedStart_v0100.py start
  py -3 VDF_MDL024_IsolatedStart_v0100.py selftest

start prints one card: tail count, AST numbers, accelerator, network, lamp, milliseconds.
Numbers come from the filename tokens ENG/MDL/FNC/ENV. A tail counts only after ast.parse.
"""
from __future__ import annotations

import ast
import re
import sys
import time
from pathlib import Path

TAG = "VDF-ISO"
VER = "v0100"
RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")
NUM = re.compile(r"(ENG|MDL|FNC|ENV)(\d{2,4})")
ACCEL = "VIA_SuperAccel_Module"
NET_TOP = {"requests", "urllib3", "httpx", "aiohttp", "curl_cffi", "yfinance", "websocket", "websockets", "ftplib", "akshare", "fredapi", "pandas_datareader", "cloudscraper", "selenium", "playwright"}
NET_FULL = ("urllib.request", "http.client")


def load_accel():
    """Not called by start. Import stays in the syntax tree without loading Celeritas."""
    import VIA_SuperAccel_Module as via_accel
    return via_accel


def load_net():
    """Not called by start. Same rule as the fetch engines: resolve, then the caller uses it."""
    root = vdf_dir().parents[1]
    hits = sorted((root / "supportive modules" / "network").glob("via_net_unified_v*.py"))
    if not hits:
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location("VIA_NET_UNIFIED", hits[-1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def vdf_dir(start: Path | None = None) -> Path:
    here = (start or Path(__file__)).resolve()
    if here.is_file():
        here = here.parent
    if here.name == "VDF":
        return here
    for parent in [here, *here.parents]:
        cand = parent / "functional modules" / "VDF"
        if cand.is_dir():
            return cand
    return here


def number_of(name: str) -> str:
    match = NUM.search(name)
    if match:
        return "VDF-" + match.group(1) + match.group(2)
    if "SystemManager" in name:
        return "VDF-SystemManager"
    return "VDF-" + name.split("_v")[0][:42]


def tails(folder: Path) -> list[Path]:
    best: dict[str, tuple[int, Path]] = {}
    if not folder.is_dir():
        return []
    for path in folder.rglob("VDF_*.py"):
        match = RX.match(path.name)
        if not match:
            continue
        ver = int(match.group("ver"))
        cur = best.get(match.group("fam"))
        if cur is None or ver > cur[0]:
            best[match.group("fam")] = (ver, path)
    return [item[1] for item in sorted(best.values(), key=lambda item: item[1].name)]


def _net_name(name: str, libs: set[str]) -> None:
    head = (name or "").split(".")[0]
    if head in NET_TOP:
        libs.add(head)
    for full in NET_FULL:
        if name == full or name.startswith(full + "."):
            libs.add(full)


def scan(path: Path) -> dict:
    row = {"file": path.name, "id": number_of(path.name), "syntax": True, "accel": False, "net": "offline", "libs": []}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError, ValueError):
        row["syntax"] = False
        row["net"] = "syntax"
        return row
    libs: set[str] = set()
    assigned = False
    called = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                row["accel"] = row["accel"] or alias.name == ACCEL
                _net_name(alias.name, libs)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            row["accel"] = row["accel"] or mod == ACCEL
            _net_name(mod, libs)
        elif isinstance(node, ast.Assign):
            assigned = assigned or any(isinstance(t, ast.Name) and t.id == "VIA_NET_TOOL_PATH" for t in node.targets)
        elif isinstance(node, ast.Call):
            consts = [a.value for a in list(node.args) + [k.value for k in node.keywords] if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            called = called or any("via_net_unified" in c.lower() for c in consts)
    if assigned and called:
        row["net"] = "bridge"
    elif libs:
        row["net"] = "gap"
        row["libs"] = sorted(libs)
    return row


def card(folder: Path) -> dict:
    rows = [scan(path) for path in tails(folder)]
    ids: dict[str, list[str]] = {}
    for row in rows:
        ids.setdefault(row["id"], []).append(row["file"])
    dups = {key: names for key, names in ids.items() if len(names) > 1}
    accel = sum(1 for row in rows if row["accel"])
    return {
        "tails": len(rows),
        "accel": accel,
        "bridge": sum(1 for row in rows if row["net"] == "bridge"),
        "offline": sum(1 for row in rows if row["net"] == "offline"),
        "gap": [row for row in rows if row["net"] == "gap" or not row["syntax"] or not row["accel"]],
        "dups": dups,
    }


def lamp(info: dict) -> str:
    if any(not row["syntax"] for row in info["gap"]):
        return "RED"
    if info["gap"] or info["dups"]:
        return "YELLOW"
    return "GREEN"


def render(info: dict, ms: int) -> str:
    lines = [
        "%s %s" % (TAG, VER),
        "tails=%d accel=%d/%d" % (info["tails"], info["accel"], info["tails"]),
        "net=%d bridge / %d offline / %d gap" % (info["bridge"], info["offline"], sum(1 for row in info["gap"] if row["net"] == "gap")),
        "lamp=%s ms=%d" % (lamp(info), ms),
    ]
    for key, names in sorted(info["dups"].items()):
        lines.append("dup %s %s" % (key, " ".join(names)))
    for row in info["gap"]:
        why = "syntax" if not row["syntax"] else ("no-accel" if not row["accel"] else row["net"])
        extra = (":" + ",".join(row["libs"])) if row["libs"] else ""
        lines.append("gap %s %s %s%s" % (row["id"], row["file"], why, extra))
    return "\n".join(lines)


def start(folder: Path | None = None) -> int:
    begun = time.perf_counter()
    info = card(folder or vdf_dir())
    text = render(info, int((time.perf_counter() - begun) * 1000))
    print(text, flush=True)
    return 0 if lamp(info) != "RED" else 1


def selftest() -> int:
    import tempfile
    folder = Path(tempfile.mkdtemp(prefix="vdf-iso-"))
    good = folder / "VDF_ENG001_Good_v0100.py"
    old = folder / "VDF_ENG001_Good_v0099.py"
    gap = folder / "VDF_ENG002_Gap_v0100.py"
    twin = folder / "VDF_ENG001_Other_v0100.py"
    good.write_text("import VIA_SuperAccel_Module\n", encoding="utf-8")
    old.write_text("import VIA_SuperAccel_Module\n", encoding="utf-8")
    gap.write_text("import VIA_SuperAccel_Module\nimport urllib.request\n", encoding="utf-8")
    twin.write_text("import VIA_SuperAccel_Module\n", encoding="utf-8")
    begun = time.perf_counter()
    info = card(folder)
    text = render(info, int((time.perf_counter() - begun) * 1000))
    fails = []
    if info["tails"] != 3:
        fails.append("tails %s" % info["tails"])
    if info["accel"] != 3 or info["bridge"] != 0 or info["offline"] != 2:
        fails.append("counts %s" % (info["accel"], info["bridge"], info["offline"]))
    if [row["file"] for row in info["gap"]] != ["VDF_ENG002_Gap_v0100.py"]:
        fails.append("gap %s" % info["gap"])
    if set(info["dups"]) != {"VDF-ENG001"}:
        fails.append("dup %s" % info["dups"])
    if "lamp=YELLOW" not in text or "VDF-ISO v0100" not in text:
        fails.append("text")
    if fails:
        print("[FAIL] " + "; ".join(fails))
        print(text)
        return 1
    print("[OK] tails=3 old-version-skipped gap=1 dup=ENG001")
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "start"
    if cmd == "selftest":
        return selftest()
    if cmd != "start":
        print("verbs: start selftest", flush=True)
        return 2
    return start()


if __name__ == "__main__":
    raise SystemExit(main())
