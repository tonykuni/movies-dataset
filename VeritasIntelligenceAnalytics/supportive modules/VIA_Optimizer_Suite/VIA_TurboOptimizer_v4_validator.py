#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Turbo Optimizer v4 -- static validator (R1 panoramic, read-only).
Encodes Tony's PowerShell LL rules + structural balance checks.
Cannot run pwsh in this container, so this is the test/debug harness.
Severity: ERROR (parse-gate blocker) / WARN (advisory).
"""
import re
import sys
import json

PATH = sys.argv[1] if len(sys.argv) > 1 else "VIA_TurboOptimizer_v4.ps1"

with open(PATH, "r", encoding="utf-8") as f:
    raw = f.read()
lines = raw.split("\n")

findings = []  # (severity, rule, line_no, msg)


def add(sev, rule, ln, msg):
    findings.append((sev, rule, ln, msg))


# ---------------------------------------------------------------------------
# Build a mask of which lines are inside the single-quote HTML here-string
# @' ... '@  so we don't lint embedded HTML/JS as if it were PowerShell.
# ---------------------------------------------------------------------------
in_here = False
here_mask = [False] * len(lines)
for i, ln in enumerate(lines):
    stripped = ln.rstrip("\r")
    if not in_here and re.search(r"=\s*@'\s*$", stripped):
        in_here = True
        here_mask[i] = True   # opener line
        continue
    if in_here:
        here_mask[i] = True
        if stripped == "'@":
            in_here = False
if in_here:
    add("ERROR", "HERESTRING", 0, "single-quote here-string @' was never closed by '@")

ps_lines = [(i + 1, ln) for i, ln in enumerate(lines) if not here_mask[i]]


# ---------------------------------------------------------------------------
# 1. param() must be the first executable statement
# ---------------------------------------------------------------------------
first_exec = None
for ln_no, ln in ps_lines:
    s = ln.strip()
    if not s:
        continue
    if s.startswith("#"):
        continue
    if s.startswith("<#"):
        continue
    if s.startswith("#requires") or s.startswith("#Requires"):
        continue
    first_exec = (ln_no, s)
    break
if first_exec and not first_exec[1].lower().startswith("param("):
    # allow block-comment region before; re-scan skipping <# #> blocks
    in_block = False
    fe = None
    for ln_no, ln in ps_lines:
        s = ln.strip()
        if "<#" in s and "#>" not in s:
            in_block = True
            continue
        if in_block:
            if "#>" in s:
                in_block = False
            continue
        if not s or s.startswith("#"):
            continue
        fe = (ln_no, s)
        break
    if fe and not fe[1].lower().startswith("param("):
        add("ERROR", "PARAM-FIRST", fe[0],
            "param() is not the first executable statement: " + fe[1][:60])


# ---------------------------------------------------------------------------
# 2. Brace / paren / bracket balance across PS-only lines
# ---------------------------------------------------------------------------
def balance(symbol_open, symbol_close, name):
    depth = 0
    instr = None  # quote char we're inside of (single line only)
    for ln_no, ln in ps_lines:
        i = 0
        while i < len(ln):
            c = ln[i]
            if instr:
                if c == instr:
                    instr = None
            else:
                if c in ("'", '"'):
                    instr = c
                elif c == "#":
                    break  # rest is comment
                elif c == symbol_open:
                    depth += 1
                elif c == symbol_close:
                    depth -= 1
                    if depth < 0:
                        add("ERROR", name, ln_no,
                            "unbalanced '%s' (extra close)" % symbol_close)
                        depth = 0
            i += 1
    if depth != 0:
        add("ERROR", name, 0, "unbalanced %s: net depth %d at EOF" % (name, depth))


balance("{", "}", "BRACE")
balance("(", ")", "PAREN")


# ---------------------------------------------------------------------------
# 3. LL rules over PS-only lines
# ---------------------------------------------------------------------------
ALIASES = {
    r"\bls\b": "Get-ChildItem", r"\bcat\b": "Get-Content", r"\bgci\b": "Get-ChildItem",
    r"\bgc\b": "Get-Content", r"\bgm\b": "Get-Member", r"\bft\b": "Format-Table",
    r"\bfl\b": "Format-List", r"\bgci\b": "Get-ChildItem", r"\b%\b": "ForEach-Object",
    r"\b\?\b": "Where-Object", r"\bgwmi\b": "Get-WmiObject",
}
# Short-name builtin alias collisions Tony banned
BANNED_FUNCS = [r"\bfunction\s+SL\b", r"\bfunction\s+SP\b", r"\bfunction\s+WL\b",
                r"\bfunction\s+WB\b", r"\bfunction\s+DP\b"]

# Pre-scan: which variables were declared as [ordered]@{} (those must use .Contains())
ordered_vars = set()
for ln_no, ln in ps_lines:
    m = re.search(r"\$(\w+)\s*=\s*\[ordered\]\s*@\{", ln)
    if m:
        ordered_vars.add(m.group(1))

for ln_no, ln in ps_lines:
    code = ln.split("#", 1)[0] if not ln.strip().startswith("#") else ""
    # 3a. banned short function names
    for pat in BANNED_FUNCS:
        if re.search(pat, code):
            add("ERROR", "SHORTFUNC", ln_no, "banned short function name collides with PS7 alias")
    # 3b. -replace used for token injection (heuristic: -replace with __TOKEN__)
    if "-replace" in code and "__" in code:
        add("ERROR", "REPLACE-TOKEN", ln_no, "-replace used near a __TOKEN__ (use .Replace())")
    # 3c. exit in main scope (outside CI gate). Flag any 'exit' not preceded by $CI guard.
    if re.search(r"(^|\s)exit\b", code):
        if "$CI" not in code and "exit ([int]" not in code:
            add("WARN", "EXIT", ln_no, "exit found; ensure it is CI-gated only")
    # 3d. ${var}: wrapping -- detect "$word:" inside double-quoted string (not $script:/$env: drive)
    for m in re.finditer(r'"[^"]*"', code):
        seg = m.group(0)
        for vm in re.finditer(r'\$([A-Za-z_]\w*):', seg):
            name = vm.group(1)
            if name not in ("script", "env", "using", "global", "local", "private"):
                add("WARN", "VARWRAP", ln_no,
                    "$%s: in dq-string should be ${%s}:" % (name, name))
    # 3e. .ContainsKey on an [ordered] var -- must use .Contains(). Plain @{} is fine.
    cm = re.search(r"\$(\w+)\.ContainsKey\(", code)
    if cm and cm.group(1) in ordered_vars:
        add("ERROR", "CONTAINS", ln_no,
            "$%s is [ordered]; use .Contains() not .ContainsKey()" % cm.group(1))
    # 3f. Write-Host ... -f  (ambiguous) without parens
    if re.search(r'-ForegroundColor|Write-Host', code) and re.search(r'"\s+-f\s', code):
        add("WARN", "FOP", ln_no, '"" -f x should be parenthesized ("" -f x)')
    # 3g. Start-Job banned
    if re.search(r"\bStart-Job\b", code):
        add("ERROR", "STARTJOB", ln_no, "Start-Job banned; use ProcessStartInfo")
    # 3h. null-conditional in strings
    if re.search(r'\$\w+\?\.', code):
        add("WARN", "NULLCOND", ln_no, "null-conditional ?. (LL#13) review inside strings")


# ---------------------------------------------------------------------------
# 4. Sort-Object multi-property must use hashtable syntax (heuristic)
# ---------------------------------------------------------------------------
for ln_no, ln in ps_lines:
    m = re.search(r"Sort-Object\s+([^\|#]+)", ln)
    if m:
        arg = m.group(1)
        # multi-property comma form WITHOUT hashtable @{ -> suspicious if -desc present elsewhere
        if "," in arg and "@{" not in arg and "-Property" not in arg:
            add("WARN", "SORTOBJ", ln_no, "Sort-Object multi-prop should use @{e=..;desc=..} hashtable form")


# ---------------------------------------------------------------------------
# 5. UTF-8 No-BOM usage for WriteAllText
# ---------------------------------------------------------------------------
for ln_no, ln in ps_lines:
    if ln.strip().startswith("#"):
        continue
    if "WriteAllText" in ln:
        # look for UTF8Encoding new($false) in same or context; quick same-line check
        ctx = ln
        if "UTF8" not in ctx and "$utf8NoBom" not in ctx and "$enc" not in ctx:
            add("WARN", "UTF8", ln_no, "WriteAllText: confirm UTF-8 No-BOM encoder is passed")

# BOM-y encoding usage (v3 bug) should not appear
for ln_no, ln in ps_lines:
    if "[System.Text.Encoding]::UTF8.GetBytes" in ln:
        add("WARN", "BOM", ln_no, "Encoding::UTF8 emits BOM; prefer UTF8Encoding::new($false)")


# ---------------------------------------------------------------------------
# 6. Token coverage: every __TOKEN__ in here-string must be Replaced
# ---------------------------------------------------------------------------
here_text = "\n".join(lines[i] for i in range(len(lines)) if here_mask[i])
tokens = set(re.findall(r"__[A-Z]+__", here_text))
for tk in tokens:
    # accept chained form where the dot sits on the previous line: "Replace('__X__'"
    if not re.search(r"Replace\(\s*['\"]%s['\"]" % re.escape(tk), raw):
        add("ERROR", "TOKEN", 0, "token %s in HTML never .Replace()d" % tk)


# ---------------------------------------------------------------------------
# 7. Endpoint coverage: every /api/x in JS must have a router arm
# ---------------------------------------------------------------------------
js_endpoints = set(re.findall(r"/api/[a-z]+", here_text))
for ep in js_endpoints:
    if ("'^%s$'" % ep) not in raw and ('"^%s$"' % ep) not in raw:
        add("ERROR", "ENDPOINT", 0, "JS calls %s but no router arm exists" % ep)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
errors = [f for f in findings if f[0] == "ERROR"]
warns = [f for f in findings if f[0] == "WARN"]

print("=" * 72)
print(" VIA Turbo Optimizer v4 -- Static Validator (R1 panoramic)")
print("=" * 72)
print(" File: %s  (%d lines, %d PS lines, %d here-string lines)" %
      (PATH, len(lines), len(ps_lines), sum(here_mask)))
print("-" * 72)
if not findings:
    print(" CLEAN -- no findings.")
else:
    for sev, rule, ln, msg in findings:
        loc = ("L%d" % ln) if ln else "--"
        print(" [%-5s] %-13s %-6s %s" % (sev, rule, loc, msg))
print("-" * 72)
print(" ERRORS: %d   WARNINGS: %d" % (len(errors), len(warns)))
print(" PARSE-GATE: %s" % ("BLOCKED" if errors else "CLEAR"))
print("=" * 72)

sys.exit(1 if errors else 0)
