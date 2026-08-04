# -*- coding: utf-8 -*-
"""
VIS_VRN_TickerRegexShim_v0100 - P2 runtime shim (operator-approved 2026-08-04)
SSOT: supportive modules/ssot/VRN_TickerRegexSSOT_v0100.json

One deterministic, minimal, reversible text transformation:
remove the literal year-exclusion token  (?!202[1-9])(?!2030)  everywhere.
This converts every legacy spelling (constants, compiled patterns, and the
modules' own pattern-string self-check assertions) to the v0100 rule in one
consistent step. Canonical files are NEVER written - callers must write the
shimmed text to a run-local copy and execute that.
"""
import sys, os, hashlib

OLD_TOKEN = "(?!202[1-9])(?!2030)"


def shim_text(source: str):
    """Return (shimmed_source, replaced_count)."""
    n = source.count(OLD_TOKEN)
    return source.replace(OLD_TOKEN, ""), n


def shim_file(src_path: str, dst_path: str):
    """Shim src into dst (run-local). Refuses in-place writes. Returns dict."""
    src_path = os.path.abspath(src_path)
    dst_path = os.path.abspath(dst_path)
    if src_path == dst_path:
        raise ValueError("REFUSED_IN_PLACE_WRITE: dst must be a run-local copy, not the canonical source")
    raw = open(src_path, "rb").read()
    text = raw.decode("utf-8", errors="replace")
    shimmed, n = shim_text(text)
    os.makedirs(os.path.dirname(dst_path) or ".", exist_ok=True)
    with open(dst_path, "w", encoding="utf-8", newline="") as f:
        f.write(shimmed)
    return {
        "src": src_path,
        "dst": dst_path,
        "replaced": n,
        "src_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "dst_sha256": hashlib.sha256(shimmed.encode("utf-8")).hexdigest().upper(),
        "residual_old_token": shimmed.count(OLD_TOKEN),
    }


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        s = 'X = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})")\nassert X.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})"'
        out, n = shim_text(s)
        assert n == 2 and OLD_TOKEN not in out
        assert 'r"(?!0)([1-9]\\d{3})"' in out
        print("shim selftest PASS (2 tokens removed, assertion kept consistent)")
        sys.exit(0)
    if len(sys.argv) != 3:
        print("usage: VIS_VRN_TickerRegexShim_v0100.py <src> <run_local_dst>  |  --selftest")
        sys.exit(2)
    import json
    print(json.dumps(shim_file(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=1))
