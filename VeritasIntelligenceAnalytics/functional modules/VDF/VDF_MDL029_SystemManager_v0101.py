#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated VDF system manager.

Auto-registers the numbered parameters in the latest ParamControl SSOT,
plus ids found in the latest copy of every other VDF SSOT book and the
industry map still stored in code. Writes a monitor page. Does not load
the VRN or VCGC managers, does not set a consent flag, and does not fetch.

  py -3 VDF_MDL029_SystemManager_v0101.py monitor
  py -3 VDF_MDL029_SystemManager_v0101.py catalog
  py -3 VDF_MDL029_SystemManager_v0101.py params VDF-PAR-001
  py -3 VDF_MDL029_SystemManager_v0101.py selftest
"""
from __future__ import annotations

import ast
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VER = "v0101"
FAMILY = re.compile(r"(VDF_(?:ENG|MDL)\d+)")
TAIL = re.compile(r"_v(\d+)")
SSOT_NAME = re.compile(r"(VDF_.+_SSOT)_v(\d+)\.json$")
ELEC = {f"{i:02d}" for i in range(24, 32)}


def _latest(paths):
    best = {}
    for path in paths:
        fam = FAMILY.search(path.name)
        ver = TAIL.search(path.name)
        if not fam or not ver:
            continue
        key, num = fam.group(1), int(ver.group(1))
        if key not in best or num > best[key][0]:
            best[key] = (num, path)
    return best


def _books():
    best = {}
    for path in HERE.glob("VDF_*SSOT_v*.json"):
        match = SSOT_NAME.match(path.name)
        if not match:
            continue
        key, num = match.group(1), int(match.group(2))
        if key not in best or num > best[key][0]:
            best[key] = (num, path)
    return best


def _literal(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError("%s has no %s" % (path.name, name))


def _verbs(path: Path) -> list:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [verb for verb in ("main", "selftest", "catalog", "monitor", "fetch", "start")
            if re.search(r"^def %s\(" % verb, text, re.M)]


def _short(value) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = "" if value is None else str(value)
    text = re.sub(r"(api_key=)[^&\s\"]+", r"\1***", text, flags=re.I)
    return text if len(text) <= 160 else text[:157] + "..."


def _industry():
    hits = sorted((HERE / "engine").glob("VDF_ENG055_*.py"), key=lambda p: int(TAIL.search(p.name).group(1)))
    for path in reversed(hits):
        try:
            return path, _literal(path, "INDUSTRY_MAP")
        except (RuntimeError, SyntaxError, ValueError):
            continue
    raise RuntimeError("INDUSTRY_MAP absent")


def _discover(book, source, found):
    if not isinstance(book, dict):
        return
    for value in book.values():
        if not isinstance(value, list):
            continue
        for row in value:
            if isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"]:
                found.append({
                    "id": row["id"],
                    "name": row.get("name") or row.get("zh") or row.get("item") or "",
                    "class": row.get("class") or "discovered",
                    "mutable": row.get("mutable"),
                    "source": source,
                    "origin": "ssot",
                })


def build() -> dict:
    errors = []
    commands = []
    seen = set()
    paths = list(HERE.glob("VDF_*.py"))
    if (HERE / "engine").is_dir():
        paths.extend((HERE / "engine").glob("VDF_*.py"))
    engines = []
    for fam, (num, path) in sorted(_latest(paths).items()):
        verbs = _verbs(path)
        engines.append({"id": fam, "version": "v%04d" % num, "file": path.name, "commands": verbs})
        for verb in verbs:
            cid = "%s.%s" % (fam, verb)
            if cid in seen:
                errors.append("duplicate command " + cid)
            seen.add(cid)
            commands.append({"id": cid, "engine": fam, "verb": verb, "file": path.name,
                             "writes": verb not in ("selftest", "catalog", "monitor")})

    books = _books()
    control_path = books.get("VDF_ParamControl_SSOT", (None, None))[1]
    if control_path is None:
        raise RuntimeError("ParamControl SSOT absent")
    control = json.loads(control_path.read_text(encoding="utf-8"))
    coded = []
    coded_ids = set()
    for row in control.get("params") or []:
        pid = row.get("id")
        if not pid:
            errors.append("coded parameter without id")
            continue
        if pid in coded_ids:
            errors.append("duplicate coded parameter " + pid)
        coded_ids.add(pid)
        coded.append({
            "id": pid,
            "name": row.get("name") or "",
            "class": row.get("class") or "",
            "mutable": bool(row.get("mutable")),
            "value": _short(row.get("value")),
            "source": control_path.name,
            "path": row.get("path") or "",
            "origin": "param_control",
        })

    discovered = []
    for key, (num, path) in sorted(books.items()):
        if key == "VDF_ParamControl_SSOT":
            continue
        try:
            _discover(json.loads(path.read_text(encoding="utf-8")), path.name, discovered)
        except json.JSONDecodeError:
            errors.append("unreadable " + path.name)
    industry_file, industry = _industry()
    if industry.get("24") != "半導體業":
        errors.append("industry 24 is not semiconductors")
    if "07" in industry or "13" in industry:
        errors.append("retired industry code came back")
    for code in sorted(industry):
        layer = "ELEC" if code in ELEC else "FIN" if code == "17" else "TRAD"
        discovered.append({
            "id": "TW.IND." + code,
            "name": industry[code],
            "class": layer,
            "mutable": False,
            "source": industry_file.name,
            "origin": "code",
        })

    by_id = {}
    for row in discovered:
        by_id.setdefault(row["id"], []).append(row["source"])
    conflicts = [{"id": key, "sources": sources} for key, sources in sorted(by_id.items()) if len(set(sources)) > 1]
    lamp = "RED" if errors else "YELLOW" if conflicts else "GREEN"
    book = {
        "schema": "VDF-SYSTEM-REGISTRY/1.1",
        "manager": "VDF_MDL029_SystemManager_%s" % VER,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engines": len(engines),
        "engine_rows": engines,
        "commands": commands,
        "coded_parameters": coded,
        "discovered": discovered,
        "conflicts": conflicts,
        "books": {key: path.name for key, (num, path) in books.items()},
        "errors": errors,
        "lamp": lamp,
        "state": "ERROR" if errors else "REGISTERED",
    }
    return book


def _page(book: dict) -> str:
    def rows(items, cols):
        head = "".join("<th>%s</th>" % html.escape(c) for c in cols)
        body = []
        for item in items:
            body.append("<tr>" + "".join("<td>%s</td>" % html.escape(_short(item.get(c, ""))) for c in cols) + "</tr>")
        return "<table><tr>%s</tr>%s</table>" % (head, "".join(body))
    coded = book["coded_parameters"]
    frozen = sum(1 for r in coded if not r["mutable"])
    return """<!doctype html><meta charset="utf-8"><title>VDF system monitor</title>
<style>
body{margin:24px;background:#f4f1ea;color:#1c2430;font:14px/1.45 ui-sans-serif,sans-serif}
h1{font-size:20px;font-weight:600;margin:0 0 8px}
.card{display:flex;gap:16px;margin:12px 0 20px}
.card div{background:#fff;border:1px solid #d5d0c6;padding:10px 14px;min-width:120px}
.lamp{font-weight:650}
table{border-collapse:collapse;width:100%%;background:#fff;margin:0 0 22px}
th,td{border-bottom:1px solid #e4dfd4;text-align:left;padding:6px 8px;vertical-align:top}
th{font-size:12px;letter-spacing:.04em;color:#5c6770}
</style>
<h1>VDF system monitor</h1>
<p>%s · %s · lamp <span class="lamp">%s</span></p>
<div class="card">
<div>engines<br>%d</div><div>commands<br>%d</div>
<div>coded parameters<br>%d</div><div>frozen<br>%d</div>
<div>discovered<br>%d</div><div>conflicts<br>%d</div>
</div>
<h2>Coded SSOT parameters</h2>
%s
<h2>Conflicts</h2>
%s
<h2>Engines</h2>
%s
""" % (
        html.escape(book["manager"]), html.escape(book["at"]), html.escape(book["lamp"]),
        book["engines"], len(book["commands"]), len(coded), frozen, len(book["discovered"]), len(book["conflicts"]),
        rows(coded, ["id", "name", "class", "mutable", "source", "value"]),
        rows(book["conflicts"], ["id", "sources"]) or "<p>none</p>",
        rows([{"id": e["id"], "version": e["version"], "commands": " ".join(e["commands"])} for e in book["engine_rows"]],
             ["id", "version", "commands"]),
    )


def catalog(book=None) -> int:
    book = book or build()
    print("state=%s lamp=%s engines=%d commands=%d coded=%d discovered=%d conflicts=%d" % (
        book["state"], book["lamp"], book["engines"], len(book["commands"]),
        len(book["coded_parameters"]), len(book["discovered"]), len(book["conflicts"])))
    for err in book["errors"]:
        print("ERROR", err)
    return 0 if book["state"] == "REGISTERED" else 1


def monitor(book=None) -> int:
    book = book or build()
    out = HERE / "output_hub" / "mega" / "system_registry"
    out.mkdir(parents=True, exist_ok=True)
    path = out / "VDF_SYSTEM_MONITOR.html"
    path.write_text(_page(book), encoding="utf-8")
    (out / "VDF_SYSTEM_REGISTRY_latest.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    rc = catalog(book)
    print("monitor=%s" % path)
    return rc


def params(key: str, book=None) -> int:
    book = book or build()
    hits = [p for p in book["coded_parameters"] + book["discovered"] if key in p["id"]]
    if not hits:
        print("NONE", key)
        return 1
    for row in hits:
        print(json.dumps(row, ensure_ascii=False))
    return 0


def selftest() -> int:
    book = build()
    if book["state"] != "REGISTERED":
        print("[FAIL]", book["errors"])
        return 1
    ids = [r["id"] for r in book["coded_parameters"]]
    if "VDF-PAR-001" not in ids or len(ids) < 36:
        print("[FAIL] coded parameters", len(ids))
        return 1
    if not any(r["id"] == "TW.IND.24" and r["origin"] == "code" for r in book["discovered"]):
        print("[FAIL] industry code parameter")
        return 1
    rc = monitor(book)
    page = (HERE / "output_hub" / "mega" / "system_registry" / "VDF_SYSTEM_MONITOR.html").read_text(encoding="utf-8")
    if "VDF-PAR-001" not in page or "api_key=" in page.lower() and "***" not in page:
        print("[FAIL] monitor page")
        return 1
    if rc != 0:
        return rc
    print("[OK] REGISTERED coded=%d discovered=%d lamp=%s" % (len(ids), len(book["discovered"]), book["lamp"]))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "monitor"
    if cmd == "selftest":
        return selftest()
    if cmd == "catalog":
        return catalog()
    if cmd == "monitor":
        return monitor()
    if cmd == "params" and len(argv) > 1:
        return params(argv[1])
    print("verbs: monitor | catalog | params <id> | selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
