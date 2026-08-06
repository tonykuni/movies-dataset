#!/usr/bin/env python3
"""Targeted PS7 static analyzer for VIA scripts.
Checks structural balance (here-strings, braces, parens, brackets) and LL rules.
Cross-platform proxy for `pwsh -Parse` which we cannot install here.
"""
import sys, re

def analyze(path):
    src = open(path, encoding='utf-8').read()
    lines = src.split('\n')
    errors, warns = [], []

    # ---- here-string aware scan -------------------------------------------
    here_open = None          # None | '"' | "'"
    here_start_line = 0
    brace = paren = brack = 0
    code_lines = []           # (lineno, text) only for lines OUTSIDE here-strings
    first_code_line = None

    for i, raw in enumerate(lines, 1):
        if here_open is not None:
            # look for closing marker at column 0
            stripped = raw.lstrip()
            if stripped == here_open + '@' or raw == here_open + '@':
                if raw[:2] != here_open + '@':
                    warns.append(f"L{i}: here-string close '{here_open}@' should be at column 0")
                here_open = None
            continue

        # not in a here-string: detect a here-string opener at END of line
        m = re.search(r"@(['\"])\s*$", raw)
        if m:
            here_open = m.group(1)
            here_start_line = i
            # the opener line itself may contain code before @' — count that part
            pre = raw[:m.start()]
            code_lines.append((i, pre))
            _count(pre, errors, i)
            brace += pre.count('{') - pre.count('}')
            continue

        code_lines.append((i, raw))
        if first_code_line is None and raw.strip() and not raw.strip().startswith('#'):
            first_code_line = (i, raw.strip())

    if here_open is not None:
        errors.append(f"L{here_start_line}: here-string opened with @{here_open} never closed")

    # ---- bracket balance over code-only text ------------------------------
    code = '\n'.join(t for _, t in code_lines)
    # strip line comments (rough: # not inside a quote) and quoted strings
    def strip_for_brackets(s):
        out = []
        in_s = None
        i = 0
        while i < len(s):
            c = s[i]
            if in_s:
                if c == in_s:
                    in_s = None
                i += 1
                continue
            if c in ("'", '"'):
                in_s = c; i += 1; continue
            if c == '#':
                # skip to EOL
                while i < len(s) and s[i] != '\n':
                    i += 1
                continue
            out.append(c); i += 1
        return ''.join(out)
    clean = strip_for_brackets(code)
    b = clean.count('{') - clean.count('}')
    p = clean.count('(') - clean.count(')')
    k = clean.count('[') - clean.count(']')
    if b: errors.append(f"Brace imbalance {{}}: net {b}")
    if p: errors.append(f"Paren imbalance (): net {p}")
    if k: warns.append(f"Bracket imbalance []: net {k} (may be type accelerators / arrays)")

    def strip_comment(s):
        in_s = None
        for i, c in enumerate(s):
            if in_s:
                if c == in_s: in_s = None
                continue
            if c in ("'", '"'): in_s = c; continue
            if c == '#': return s[:i]
        return s

    # ---- LL rule checks (line by line, code only) -------------------------
    for ln, t in code_lines:
        low = strip_comment(t)
        # LL#10/#15: no block comments
        if '<#' in low or '#>' in low:
            errors.append(f"L{ln}: block comment <# #> forbidden (LL#10/#15)")
        # LL#20: Write-Host ... -f  at TOP LEVEL (treated as ForegroundColor).
        # A -f INSIDE parentheses is the safe format operator, so track depth.
        wh = re.search(r'Write-Host\b', low)
        if wh:
            rest = low[wh.end():]
            depth = 0
            j = 0
            while j < len(rest):
                ch = rest[j]
                if ch == '(': depth += 1
                elif ch == ')': depth -= 1
                elif depth == 0 and rest[j:j+3] in (' -f', '\t-f') and (j+3 >= len(rest) or not rest[j+3].isalnum()):
                    errors.append(f"L{ln}: top-level 'Write-Host ... -f' ambiguity (LL#20)")
                    break
                j += 1
        # LL: no Start-Job
        if re.search(r'\bStart-Job\b', low):
            errors.append(f"L{ln}: Start-Job forbidden; use ProcessStartInfo (LL)")
        # LL: no -Args hashtable splat to external exe
        if re.search(r'-Args\s+@\{', low):
            errors.append(f"L{ln}: '-Args @{{...}}' hashtable splat forbidden (LL)")
        # LL#18: ordered dict ContainsKey
        if '.ContainsKey(' in low:
            warns.append(f"L{ln}: '.ContainsKey()' — ordered dict needs .Contains() (LL#18)")
        # LL#17: $word: in a double-quoted string parsed as drive/scope
        for dq in re.findall(r'"(?:[^"`]|`.)*"', low):
            for mm in re.finditer(r'\$([A-Za-z_]\w*):', dq):
                name = mm.group(1).lower()
                if name not in ('env', 'script', 'global', 'local', 'using', 'private'):
                    warns.append(f"L{ln}: '${mm.group(1)}:' inside \"...\" — use ${{{mm.group(1)}}}: (LL#17)")

    # ---- param() must be at top -------------------------------------------
    if first_code_line:
        fl_text = first_code_line[1]
        if not (fl_text.startswith('param') or fl_text.startswith('#requires') or fl_text.startswith('[CmdletBinding')):
            warns.append(f"First code at L{first_code_line[0]}: ensure param() near top")

    return errors, warns

def _count(*_):
    pass

if __name__ == '__main__':
    path = sys.argv[1]
    errs, warns = analyze(path)
    print(f"== PS LINT: {path} ==")
    for e in errs:  print("  ERROR ", e)
    for w in warns: print("  WARN  ", w)
    print(f"-- {len(errs)} error(s), {len(warns)} warning(s) --")
    sys.exit(1 if errs else 0)
