# -*- coding: utf-8 -*-
"""CGC_MDL186 — the eight-hub check inside CGC_MDL135. Check only.

Loaded by `via-envgov eight-hub`. It does not install tools, create environments,
or rename them. BASE may keep its name. Every other environment must start with via_.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
TOOLS = (
    ("01", "uv", "uv"),
    ("02", "pip", "pip"),
    ("03", "pipdeptree", "pipdeptree"),
    ("04", "deptry", "deptry"),
    ("05", "johnnydep", "johnnydep"),
    ("06", "pip-tools", "pip-compile"),
    ("07", "pip-check", "pip-check"),
    ("08", "pip-audit", "pip-audit"),
)
MIRRORS = (
    ("Official", "https://pypi.org/simple"),
    ("TUNA", "https://pypi.tuna.tsinghua.edu.cn/simple"),
    ("Aliyun", "https://mirrors.aliyun.com/pypi/simple/"),
)


def _flag(args: list[str], name: str) -> str:
    if name not in args:
        return ""
    i = args.index(name)
    return args[i + 1] if i + 1 < len(args) else ""


def _python(env: Path) -> Path | None:
    for rel in ("python.exe", "Scripts/python.exe", "bin/python", "bin/python3"):
        path = env / rel
        if path.is_file():
            return path
    return None


def discover(root: Path | None, base: str) -> list[dict]:
    found: list[dict] = []
    if base:
        found.append({"name": "base", "python": base, "kind": "BASE"})
    if root and root.is_dir():
        for child in sorted(p for p in root.iterdir() if p.is_dir()):
            py = _python(child)
            if py is not None:
                found.append({"name": child.name, "python": str(py), "kind": "ENV"})
    return found


def naming(name: str, kind: str) -> tuple[str, str]:
    if kind == "BASE" or name.lower() == "base":
        return "BASE", ""
    if name.lower().startswith("via_"):
        return "OK", ""
    return "RENAME", "via_" + name.lower().replace("-", "_")


def _run(argv: list[str], timeout: int = 60) -> tuple[int, str]:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return -9, "TIMEOUT"
    except OSError as exc:
        return -1, type(exc).__name__
    text = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, text[:500]


def check_env(python: str) -> dict:
    path = Path(python)
    if not path.is_file():
        return {"state": "ABSENT", "tool": "", "detail": "解譯器不在"}
    if shutil.which("uv"):
        rc, text = _run(["uv", "pip", "check", "--python", python])
        if rc == 0:
            return {"state": "PASS", "tool": "uv", "detail": "uv pip check"}
        if rc > 0:
            return {"state": "FAIL", "tool": "uv", "detail": text or "uv pip check"}
    rc, text = _run([python, "-m", "pip", "check"])
    if rc == 0:
        return {"state": "PASS", "tool": "pip", "detail": "pip check"}
    if rc > 0:
        return {"state": "FAIL", "tool": "pip", "detail": text or "pip check"}
    return {"state": "NOT_RUN", "tool": "pip", "detail": text or "檢查沒跑成"}


def tool_roster() -> list[dict]:
    rows = []
    for num, name, cmd in TOOLS:
        if name == "pip":
            state = "WITH_ENV"
        else:
            state = "PRESENT" if shutil.which(cmd) else "ABSENT"
        rows.append({"id": num, "name": name, "state": state})
    return rows


def mirror_roster(offline: bool) -> list[dict]:
    consent = (sys.modules.get("os") and __import__("os").environ.get("VIA_NET_CONSENT") == "YES")
    rows = []
    for name, url in MIRRORS:
        if offline or not consent:
            rows.append({"name": name, "url": url, "state": "NOT_RUN"})
        else:
            rows.append({"name": name, "url": url, "state": "NOT_RUN", "why": "本動詞只檢查衝突,不向鏡像編譯"})
    return rows


def report(envs: list[dict], offline: bool) -> dict:
    env_rows = []
    for env in envs:
        mark, suggested = naming(env["name"], env["kind"])
        checked = check_env(env["python"]) if mark != "RENAME" else {"state": "SKIP", "tool": "", "detail": "先改名,不在錯名境裡裝"}
        env_rows.append({**env, "naming": mark, "suggested": suggested, **{f"check_{k}": v for k, v in checked.items()}})
    return {"version": VERSION, "offline": offline, "envs": env_rows, "tools": tool_roster(), "mirrors": mirror_roster(offline)}


def render(pay: dict) -> str:
    lines = ["[eight-hub] 只檢查。不安裝,不重建,不改名。"]
    fails = 0
    for row in pay["envs"]:
        if row["naming"] == "RENAME":
            fails += 1
            lines.append(f"  [RENAME] {row['name']} → {row['suggested']}  用既有 via-envgov rename,這支不執行")
            continue
        state = row["check_state"]
        if state == "FAIL":
            fails += 1
        lines.append(f"  [{state}] {row['name']}  {row['check_tool']}  {row['check_detail'][:120]}")
    absent = [t["name"] for t in pay["tools"] if t["state"] == "ABSENT"]
    lines.append("  八工具 " + " ".join(f"{t['id']}:{t['state']}" for t in pay["tools"]))
    if absent:
        lines.append("  缺工具只記錄,不自動安裝: " + " ".join(absent))
    lines.append("  三鏡像 " + " ".join(f"{m['name']}:{m['state']}" for m in pay["mirrors"]))
    lines.append(f"  [計] 境 {len(pay['envs'])} · 要處理 {fails}")
    return "\n".join(lines)


def run(host, rest: list[str]) -> int:
    del host
    offline = "--online" not in rest
    root = Path(_flag(rest, "--env-root")) if _flag(rest, "--env-root") else None
    pay = report(discover(root, _flag(rest, "--base-python")), offline)
    print(render(pay))
    out = VIA / "VIA_Reports" / "env_governance" / "eight_hub"
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "EIGHT_HUB_latest.json").write_text(json.dumps(pay, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    bad = any(r["naming"] == "RENAME" or r["check_state"] == "FAIL" for r in pay["envs"])
    return 1 if bad else 0


def selftest() -> int:
    fails = []

    def chk(name: str, cond: bool) -> None:
        print(f"  [{'OK' if cond else 'FAIL'}] {name}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        good = root / "via_core"
        (good / "bin").mkdir(parents=True)
        (good / "bin" / "python").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (good / "bin" / "python").chmod(0o755)
        bad = root / "legacy"
        (bad / "bin").mkdir(parents=True)
        (bad / "bin" / "python").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (bad / "bin" / "python").chmod(0o755)
        pay = report(discover(root, ""), True)
        text = render(pay)
        names = {r["name"]: r for r in pay["envs"]}
        chk("via_ 境留下", names["via_core"]["naming"] == "OK")
        chk("沒有 via_ 的境只列改名,不重建", names["legacy"]["naming"] == "RENAME" and names["legacy"]["suggested"] == "via_legacy" and "不執行" in text)
        chk("八工具都有編號,三鏡像離線不連", len(pay["tools"]) == 8 and {m["state"] for m in pay["mirrors"]} == {"NOT_RUN"})
        chk("base 可以保留原名", naming("base", "BASE") == ("BASE", ""))
    print(f"  [計] {4 - len(fails)} OK · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return run(None, sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
