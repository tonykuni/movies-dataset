#!/usr/bin/env python3
# Apply single-file unified diff (B600 EngineBus v0127→v0128)
import pathlib, re, sys
if len(sys.argv) != 4:
    raise SystemExit("usage: _apply_bus_diff.py SRC.py DIFF.py DST.py")
src_path, diff_path, dst_path = map(pathlib.Path, sys.argv[1:4])
src_lines = src_path.read_text(encoding="utf-8").splitlines(keepends=True)
text = diff_path.read_text(encoding="utf-8")
hunks = list(re.finditer(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n((?:.*\n)*?)(?=^@@ |\Z)",
    text, re.M))
if not hunks:
    raise SystemExit("no hunks in diff")
out, pos = [], 0
for h in hunks:
    old_start = int(h.group(1)) - 1
    body = h.group(5)
    out.extend(src_lines[pos:old_start])
    pos = old_start
    for line in body.splitlines(keepends=True):
        if not line.endswith("\n"):
            line += "\n"
        tag, rest = line[:1], line[1:]
        if tag == " ":
            if pos >= len(src_lines) or src_lines[pos].replace("\r\n", "\n") != rest.replace("\r\n", "\n"):
                raise SystemExit(f"context mismatch at src line {pos+1}")
            out.append(src_lines[pos]); pos += 1
        elif tag == "-":
            pos += 1
        elif tag == "+":
            out.append(rest)
        elif tag == "\\":
            pass
        else:
            raise SystemExit(f"bad diff line: {line[:60]!r}")
out.extend(src_lines[pos:])
dst_path.write_text("".join(out), encoding="utf-8")
print(f"wrote {dst_path} ({dst_path.stat().st_size} bytes)")
