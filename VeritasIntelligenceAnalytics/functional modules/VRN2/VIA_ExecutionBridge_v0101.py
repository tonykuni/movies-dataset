#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared execution bridge: verify the active tool lock, then apply its accelerator."""
from __future__ import annotations

# ===== Parameters =====
LOCK_RELATIVE = "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json"
CACHE = {}
UTF8_BOM = b"\xef\xbb\xbf"

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def load(path, name):
    path = Path(path).resolve()
    cached = sys.modules.get(name)
    if cached is not None and Path(getattr(cached, "__file__", "")).resolve() == path:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def locked_tool(root, book, family, audit=None):
    """Accept exact locked bytes or their CRLF/LF and UTF-8 BOM representations.

    Every accepted representation must reproduce the existing locked SHA256.
    No spaces, comments, statements, trailing newline or lock values are changed.
    """
    entry = book[family]
    relative = Path(entry["path"])
    parts = relative.parts
    if parts and parts[0] == "VeritasIntelligenceAnalytics":
        relative = Path(*parts[1:])
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Tool lock escapes system root")
    expected = str(entry["sha256"]).lower()
    if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
        raise ValueError(f"{family} invalid locked SHA256")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    mode, representation = "EXACT", "raw"
    if digest != expected:
        body = data[len(UTF8_BOM):] if data.startswith(UTF8_BOM) else data
        lf = body.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        candidates = (("LF", lf), ("LF+BOM", UTF8_BOM + lf), ("CRLF", crlf), ("CRLF+BOM", UTF8_BOM + crlf))
        representation = next((name for name, content in candidates if hashlib.sha256(content).hexdigest() == expected), None)
        if representation is None:
            raise ValueError(f"{family} tool content mismatch; not only CRLF/BOM: {path}; expected={expected}; actual={digest}; LF={hashlib.sha256(lf).hexdigest()}; source and lock retained")
        mode = "EOL_BOM_EQUIVALENT"
    if audit is not None:
        audit[family] = {"path": str(path), "mode": mode, "locked_sha256": expected,
                         "actual_sha256": digest, "matched_representation": representation,
                         "actual_bytes": len(data), "locked_bytes": entry.get("bytes")}
    return path, expected


# [VIA:ACCEL-BRIDGE:v0100] Actual initialization, shared by scripts and -c/-m jobs.
# [VIA:NET-BRIDGE:v0100] NetUnified delegates to the hash-checked active network core.
def activate(root=None, network=False):
    root = Path(root or os.environ.get("VIA_TOOLS_ROOT") or os.environ.get("VIA_ROOT") or ".").resolve()
    key = (str(root), network)
    if key in CACHE:
        return CACHE[key]
    book = json.loads((root / LOCK_RELATIVE).read_text(encoding="utf-8-sig"))
    verification = {}
    accelerator_path, accelerator_hash = locked_tool(root, book, "accelerator", verification)
    network_path, network_hash = locked_tool(root, book, "network", verification)
    support = root / "supportive modules"
    if str(support) not in sys.path:
        sys.path.insert(0, str(support))
    bridge = load(support / "VIA_SuperAccel_Module.py", "VIA_CLOSEOUT_ACCEL_BRIDGE")
    accelerator = bridge.celeritas()
    if accelerator is None or Path(accelerator.__file__).resolve() != accelerator_path:
        raise RuntimeError("Active accelerator did not load from its lock")
    applied = accelerator.apply_vrn_vds_max_accel()
    result = {"root": str(root), "accelerator": str(accelerator_path), "accelerator_sha256": accelerator_hash,
              "network_core": str(network_path), "network_sha256": network_hash,
              "applied": {str(k): str(v) for k, v in (applied or {}).items()}, "network_loaded": False,
              "verification": verification}
    if network:
        gateways = sorted((support / "network").glob("via_net_unified_v[0-9][0-9][0-9][0-9].py"))
        if not gateways:
            raise FileNotFoundError("VDF network gateway is missing")
        gateway = load(gateways[-1], "VIA_CLOSEOUT_NET_GATEWAY")
        core = gateway._aegis()
        if core is None or Path(core.__file__).resolve() != network_path:
            raise RuntimeError("NetUnified did not load its active network lock")
        result.update(network_loaded=True, gateway=str(gateways[-1]), canonical=getattr(gateway, "CANONICAL", ""))
    CACHE[key] = result
    return result


def command(arguments, root, package):
    """Preserve interpreter flags and argv while accelerating -c, -m and script jobs."""
    arguments = [str(x) for x in arguments]
    executable, remaining, flags = arguments[0], list(arguments[1:]), []
    while remaining and remaining[0] in ("-I", "-B", "-u", "-E", "-s", "-W", "-X"):
        flag = remaining.pop(0)
        flags.append(flag)
        if flag in ("-W", "-X"):
            flags.append(remaining.pop(0))
    # -I ignores PYTHONUTF8/PYTHONIOENCODING on Windows. Pass UTF-8 as an
    # interpreter option so isolated pip/OCR/probe children keep Unicode logs.
    flags = ["-X", "utf8", *flags]
    if not remaining:
        raise ValueError("Python command has no target")
    head = remaining.pop(0)
    if head in ("-c", "-m"):
        kind, target = ("code" if head == "-c" else "module"), remaining.pop(0)
    else:
        kind, target = "script", head
    return [executable, *flags, str(Path(package) / "VIA_RunWithTools_v0101.py"), "--root", str(root), "--kind", kind, "--target", target, "--", *remaining]
