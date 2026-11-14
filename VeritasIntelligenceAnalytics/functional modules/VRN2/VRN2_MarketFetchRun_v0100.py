#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_MarketFetchRun v0100 — step 6e runner: the shared VRN2_MarketFetch (desktop line, functional modules/VRN, read-only) with a fetch Python
that passes the VDF engine's own dependency check.

Desktop 2026-10-29 17:01 (RoundAll v0101, 6e YELLOW): the launcher started MarketFetch v0112 with envs/via_core_312 (all five packages present), but
MarketFetch's fetch_python() always returns envs/via_tw_fetch when that folder exists. That environment has none of the packages, so MarketFetch's probe
said "擷取環境缺套件", and an earlier run of the VDF engine v039 had already tried its own bootstrap there (pip install pandas>=2.2,<3 ... → exit 1).
This runner loads MarketFetch from its own file (not copied, not changed: its __file__, HERE and engine lookup stay the same), replaces only fetch_python()
inside that module with the first candidate that passes the engine's check, and then calls MarketFetch.main(argv) unchanged.
  check     = the engine's def_missing_dependencies(): same modules, same >= / < bounds read from DEPENDENCY_REQUIREMENTS in the engine file,
              Python 3.11 or later, plus MarketFetch's own probe (the "import yfinance, lxml, pandas, pyarrow, duckdb" line read from its source)
  candidates = --python · VIA_FETCH_PY · VDF_ENV_HOME · envs/via_tw_fetch · this Python · the other folders under envs
              (names with retired / backup / bak / old / deprecated / archive are skipped and listed)
  none passes → --fetch prints "[計] 市場擷取 · YELLOW · ..." with what each candidate misses and does not start the engine (its bootstrap would run pip
              again); --fill / --doctor still run, with this Python. Nothing is installed here (installing is VCGC's job).
usage: python VRN2_MarketFetchRun_v0100.py --tool <VRN2_MarketFetch_vNNNN.py> [--python <python>] --pick-python | --fetch ... | --fill ... | --doctor ...
       python VRN2_MarketFetchRun_v0100.py --selftest
[VIA:AST-CLASS] 類別 = VRN-2 私有 runtime 工具(只用標準庫)· 入口 = 本檔 CLI
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import venv

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
MARKET_PROBE = ("yfinance", "lxml", "pandas", "pyarrow", "duckdb")          # MarketFetch v0112 fetch() / doctor() probe
FALLBACK_REQUIREMENTS = (("pandas", "pandas>=2.2,<3"), ("pyarrow", "pyarrow>=17,<27"), ("duckdb", "duckdb>=1.1,<3"),
                         ("yfinance", "yfinance>=0.2.54,<2"), ("lxml", "lxml>=5,<7"), ("tzdata", "tzdata>=2024.1"))   # VDF_TW_AllInOne_v039
FILL_NEEDS = ("pandas", "pyarrow")                                            # MarketFetch --fill reads Parquet in-process (no engine, no bounds)
RETIRED_ENV = re.compile(r"retired|backup|\.bak|_bak|\bbak\b|\.old|_old|-old|deprecated|archive", re.I)
PROBE = r'''
import importlib, importlib.metadata, importlib.util, json, re, sys
reqs, extra = json.loads(sys.argv[1]), json.loads(sys.argv[2])
out = {"py_version": sys.version.split()[0], "py_ok": sys.version_info >= (3, 11), "missing": [], "versions": {}, "import_failed": []}
for module, requirement in reqs:
    available = False
    try:
        available = importlib.util.find_spec(module) is not None
        if available:
            package = requirement.split(">=", 1)[0]
            raw = importlib.metadata.version(package)
            out["versions"][package] = raw
            version = tuple(int(x) for x in re.match(r"\d+(?:\.\d+)*", raw)[0].split("."))
            lower = re.search(r">=([\d.]+)", requirement)
            upper = re.search(r"<([\d.]+)", requirement)
            if lower and version < tuple(int(x) for x in lower[1].split(".")):
                available = False
            if upper and version >= tuple(int(x) for x in upper[1].split(".")):
                available = False
    except Exception:
        available = False
    if not available:
        out["missing"].append(requirement)
for module in extra:
    try:
        importlib.import_module(module)
    except Exception as error:
        out["import_failed"].append("%s(%s)" % (module, type(error).__name__))
print(json.dumps(out))
'''

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def load_tool(tool: Path, alias: str = "vrn2_marketfetch_shared"):
    """MarketFetch from its own file (its HERE / engine lookup stay in functional modules/VRN)."""
    spec = importlib.util.spec_from_file_location(alias, str(tool))
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


def probe_modules_of(tool: Path) -> tuple:
    """The modules MarketFetch's own probe imports ("import yfinance, lxml, ...; print('ok')" in its source) · not found → MARKET_PROBE."""
    try:
        text = Path(tool).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return MARKET_PROBE
    hit = re.search(r"import ([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*;\s*print\('ok'\)", text)
    return tuple(x.strip() for x in hit.group(1).split(",")) if hit else MARKET_PROBE


def requirements(engine) -> tuple:
    """DEPENDENCY_REQUIREMENTS from the engine file (ast, not imported: importing the engine runs its bootstrap) → (requirements, where from)."""
    if engine and Path(engine).is_file():
        try:
            tree = ast.parse(Path(engine).read_text(encoding="utf-8", errors="replace"))
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DEPENDENCY_REQUIREMENTS" for t in node.targets):
                    value = ast.literal_eval(node.value)
                    if isinstance(value, (tuple, list)) and all(isinstance(r, (tuple, list)) and len(r) == 2 and all(isinstance(x, str) for x in r) for r in value):
                        return tuple((r[0], r[1]) for r in value), Path(engine).name
        except (SyntaxError, ValueError):
            pass
    return FALLBACK_REQUIREMENTS, "內建(VDF_TW_AllInOne_v039 的界線 · 引擎檔讀不到)"


def _home() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or str(Path.home()))


def _env_python(folder: Path):
    for rel in ("Scripts/python.exe", "bin/python"):
        if (Path(folder) / rel).is_file():
            return Path(folder) / rel
    return None


def candidates(explicit=None) -> tuple:
    """[(python, how)] in order, no duplicates (abspath, not resolve: a venv's python links to the base one) · plus the skipped retired folders."""
    found, skipped, seen = [], [], set()

    def add(path, how):
        if not path or not Path(path).is_file():
            return
        key = os.path.normcase(os.path.abspath(str(path)))
        if key not in seen:
            seen.add(key)
            found.append((str(path), how))
    add(explicit, "--python")
    add(os.environ.get("VIA_FETCH_PY"), "VIA_FETCH_PY")
    if os.environ.get("VDF_ENV_HOME"):
        add(_env_python(Path(os.environ["VDF_ENV_HOME"])), "VDF_ENV_HOME")
    envs = _home() / "envs"
    add(_env_python(envs / "via_tw_fetch"), "envs/via_tw_fetch(VDF 預設)")
    add(sys.executable, "本行程")
    if envs.is_dir():
        for folder in sorted(p for p in envs.iterdir() if p.is_dir() and p.name != "via_tw_fetch"):
            if RETIRED_ENV.search(folder.name):
                skipped.append(folder.name)
                continue
            add(_env_python(folder), "envs/" + folder.name)
    return found, skipped


def probe(python: str, reqs, extra=MARKET_PROBE, env=None) -> dict:
    """Run the engine's check inside `python` (a scratch cwd, so nothing local shadows a package)."""
    with tempfile.TemporaryDirectory(prefix="vrn2-fetchpy-") as scratch:
        try:
            done = subprocess.run([python, "-c", PROBE, json.dumps([list(r) for r in reqs]), json.dumps(list(extra))], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=240, cwd=scratch, env=env)
            got = json.loads((done.stdout.strip().splitlines() or ["{}"])[-1])
        except Exception as error:  # noqa: BLE001
            return {"ok": False, "py_version": "?", "missing": [], "import_failed": [], "note": "起不來:%s" % type(error).__name__}
    got["ok"] = bool(got.get("py_ok")) and not got.get("missing") and not got.get("import_failed")
    if not got.get("py_ok"):
        got["note"] = "Python %s < 3.11(VDF 引擎要 3.11+)" % got.get("py_version")
    return got


def pick(reqs, explicit=None, extra=MARKET_PROBE, env=None) -> tuple:
    """First candidate that passes → (python or None, report rows, skipped folders)."""
    found, skipped = candidates(explicit)
    report = []
    for python, how in found:
        got = probe(python, reqs, extra, env)
        report.append({"python": python, "how": how, "ok": got["ok"], "py_version": got.get("py_version"), "missing": got.get("missing", []),
                       "import_failed": got.get("import_failed", []), "versions": got.get("versions", {}), "note": got.get("note", "")})
        if got["ok"]:
            return python, report, skipped
    return None, report, skipped


def fill_python(report):
    """--fill needs only pandas + pyarrow in the Python that runs it: the first probed candidate that imports both (bounds do not matter there)."""
    for row in report:
        if row["py_version"] != "?" and not any(x.split("(")[0] in FILL_NEEDS for x in row["import_failed"]):
            return row["python"]
    return None


def explain(report, skipped) -> str:
    parts = []
    for row in report:
        versions = row.get("versions") or {}
        missing = ["%s(有 %s)" % (r, versions[r.split(">=", 1)[0]]) if r.split(">=", 1)[0] in versions else r for r in row["missing"]]   # 裝了但不在界線內 → 寫出裝的版本
        what = row["note"] or " ".join(missing + ["匯入失敗 " + x for x in row["import_failed"]])
        where = "" if row["how"].startswith("envs/") else " " + (Path(row["python"]).parent.parent.name or row["python"])   # --python / VIA_FETCH_PY / 本行程 → 寫出是哪個環境
        parts.append("%s%s(%s):%s" % (row["how"], where, row["py_version"], what or "?"))
    if skipped:
        parts.append("略過退役 / 備份 %s" % " ".join(skipped))
    return " | ".join(parts)


def _opt(argv, key):
    return argv[argv.index(key) + 1] if key in argv and argv.index(key) + 1 < len(argv) else None


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    tool, explicit = _opt(argv, "--tool"), _opt(argv, "--python")
    rest = [a for i, a in enumerate(argv) if a not in ("--tool", "--python") and (i == 0 or argv[i - 1] not in ("--tool", "--python"))]
    if not tool or not Path(tool).is_file():
        print("[計] 市場擷取 · GRAY · 沒有 MarketFetch(--tool %s)" % tool, flush=True)
        return 2
    module = load_tool(Path(tool))
    engine = module.engine_path() if hasattr(module, "engine_path") else None
    reqs, source = requirements(engine)
    python, report, skipped = pick(reqs, explicit, probe_modules_of(Path(tool)))
    bounds = " ".join(r[1] for r in reqs)
    if "--pick-python" in rest:
        print(json.dumps({"schema": "VRN2_MARKET_PYTHON/1", "version": VERSION, "python": python, "requirements": [list(r) for r in reqs], "requirements_from": source,
                          "fill_python": python or fill_python(report), "candidates": report, "skipped": skipped, "why": "" if python else explain(report, skipped)}, ensure_ascii=False), flush=True)
        return 0 if python else 2
    if python:
        how = next(r["how"] for r in report if r["python"] == python)
        print("[計] ⑥e 擷取 Python · %s(%s · Python %s)· 合 %s 的版本界線 %s" % (python, how, report[-1]["py_version"], source, bounds), flush=True)
        module.fetch_python = lambda: python
    else:
        if "--fetch" in rest:
            print("[計] 市場擷取 · YELLOW · 沒有合 VDF 引擎版本界線的擷取 Python(%s)· 不啟動引擎(它會自己 pip 安裝 · 桌機上次就失敗)"
                  "→ 交 VCGC:建好 envs\\via_tw_fetch 或設 VIA_FETCH_PY · 界線 %s(%s)" % (explain(report, skipped)[:700], bounds, source), flush=True)
            return 0
        fallback = fill_python(report) or sys.executable
        module.fetch_python = lambda: fallback
        print("[計] ⑥e 擷取 Python · 沒有合界線的 · %s 用本行程 %s(%s)" % (next((a for a in rest if a in ("--fill", "--doctor", "--selftest")), "本步"), sys.executable, explain(report, skipped)[:400]), flush=True)
    return int(module.main(rest) or 0)


# ===== selftest =====
def _venv(folder: Path, fake_version=None) -> Path:
    """A scratch venv (stdlib venv, no pip, nothing downloaded) · optionally with a fake distribution 'vrn2fakepkg' of that version in its site-packages."""
    venv.EnvBuilder(with_pip=False, symlinks=(os.name != "nt")).create(str(folder))
    python = _env_python(folder)
    if fake_version:
        site = subprocess.run([str(python), "-c", "import sysconfig;print(sysconfig.get_paths()['purelib'])"], capture_output=True, text=True, timeout=120).stdout.strip()
        site = Path(site)
        site.mkdir(parents=True, exist_ok=True)
        (site / "vrn2fakepkg.py").write_text("VALUE = 1\n", encoding="utf-8")
        info = site / ("vrn2fakepkg-%s.dist-info" % fake_version)
        info.mkdir()
        (info / "METADATA").write_text("Metadata-Version: 2.1\nName: vrn2fakepkg\nVersion: %s\n" % fake_version, encoding="utf-8")
    return python


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    saved = {k: os.environ.get(k) for k in ("VIA_FETCH_PY", "VDF_ENV_HOME", "USERPROFILE", "HOME")}
    try:
        with tempfile.TemporaryDirectory(prefix="vrn2-marketrun-") as temporary:
            root = Path(temporary)
            engine = root / "VRN" / "_vdf_fetch" / "VDF_TW_AllInOne_v099.py"
            engine.parent.mkdir(parents=True)
            engine.write_text('import sys\nDEPENDENCY_REQUIREMENTS = (\n    ("vrn2fakepkg", "vrn2fakepkg>=1.2,<2"),\n)\nraise SystemExit("never imported")\n', encoding="utf-8")
            reqs, source = requirements(engine)
            fallback, how = requirements(root / "none.py")
            (root / "empty.py").write_text("DEPENDENCY_REQUIREMENTS = ()\n", encoding="utf-8")
            fallback = fallback if requirements(root / "empty.py")[0] == () else None
            chk("① 界線從引擎檔讀(ast · 不匯入引擎)· 讀不到 → 內建 v039 界線 6 項 · 探測模組從 MarketFetch 原文取(找不到 → 內建 5 個)", reqs == (("vrn2fakepkg", "vrn2fakepkg>=1.2,<2"),)
                and source == engine.name and fallback == FALLBACK_REQUIREMENTS and "內建" in how and probe_modules_of(root / "none.py") == MARKET_PROBE)
            home = root / "home"
            envs = home / "envs"
            for key in ("VIA_FETCH_PY", "VDF_ENV_HOME"):
                os.environ.pop(key, None)
            os.environ["USERPROFILE"] = os.environ["HOME"] = str(home)
            broken = _venv(envs / "via_tw_fetch")                     # VDF's own env, nothing installed (the desktop)
            good = _venv(envs / "via_core_312", "1.5")                 # has the package in bounds
            _venv(envs / "via_core.retired-20260914_111946", "1.5")    # retired → never used
            low = _venv(envs / "via_lowver", "1.1")                     # below the lower bound
            found, skipped = candidates()
            hows = [h for _, h in found]
            chk("② 候選順序:via_tw_fetch → 本行程 → 其餘 envs(退役夾略過並列出)", hows[:2] == ["envs/via_tw_fetch(VDF 預設)", "本行程"] and "envs/via_core_312" in hows
                and not any("retired" in h for h in hows) and skipped == ["via_core.retired-20260914_111946"])
            python, report, _ = pick(reqs, extra=("vrn2fakepkg",))
            first = report[0]
            chk("③ 桌機情形:via_tw_fetch 缺套件 → 不選 · 選到 via_core_312(合界線 · 匯入得到)", python == str(good) and first["how"].startswith("envs/via_tw_fetch") and not first["ok"]
                and first["missing"] == ["vrn2fakepkg>=1.2,<2"] and report[-1]["versions"].get("vrn2fakepkg") == "1.5")
            python2, report2, _ = pick((("vrn2fakepkg", "vrn2fakepkg>=1.2,<1.5"),), extra=("vrn2fakepkg",))
            chk("④ 上界照引擎算(1.5 不 < 1.5 → 不合)· 下界(1.1 < 1.2 → 不合)· 都不合 → 沒有 · 說明逐個列(裝了但不在界線內寫出版本)", python2 is None and all(not r["ok"] for r in report2)
                and "vrn2fakepkg>=1.2,<1.5(有 1.5)" in explain(report2, ["x.retired"]) and "略過退役" in explain(report2, ["x.retired"]))
            os.environ["VIA_FETCH_PY"] = str(low)
            python3, report3, _ = pick(reqs, extra=("vrn2fakepkg",))
            chk("⑤ VIA_FETCH_PY 指的 Python 不合界線 → 不硬用 · 往下找到合的", report3[0]["how"] == "VIA_FETCH_PY" and not report3[0]["ok"] and python3 == str(good))
            os.environ.pop("VIA_FETCH_PY", None)
            tool = root / "VRN" / "VRN2_MarketFetch_v0199.py"
            tool.write_text("import sys\nfrom pathlib import Path\nHERE = Path(__file__).resolve().parent\n"
                            "def engine_path():\n    return HERE / '_vdf_fetch' / 'VDF_TW_AllInOne_v099.py'\n"
                            "def fetch_python():\n    return 'WRONG-via_tw_fetch'\n"
                            "PROBE = \"import vrn2fakepkg; print('ok')\"\n"
                            "def main(argv):\n    print('[計] 市場%s · GREEN · py=%s · argv=%s' % ('擷取' if '--fetch' in argv else '填值', fetch_python(), ' '.join(argv)))\n    return 0\n", encoding="utf-8")
            me = str(Path(__file__).resolve())
            run = subprocess.run([str(good), "-X", "utf8", me, "--tool", str(tool), "--fetch", "--out", str(root / "m")], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            chk("⑥ --fetch:MarketFetch 的 fetch_python 換成合界線的 Python · 其餘參數原樣交給它的 main", "py=%s" % good in run.stdout and "argv=--fetch --out" in run.stdout and run.returncode == 0)
            engine.write_text('DEPENDENCY_REQUIREMENTS = (("vrn2fakepkg", "vrn2fakepkg>=9"),)\n', encoding="utf-8")
            run = subprocess.run([str(good), "-X", "utf8", me, "--tool", str(tool), "--fetch", "--out", str(root / "m")], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            run2 = subprocess.run([str(good), "-X", "utf8", me, "--tool", str(tool), "--fill", "--out", str(root / "m")], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            chk("⑦ 沒有合界線的:--fetch 印「市場擷取 · YELLOW」且不啟動引擎(不 pip)· --fill 照跑(本行程)",
                "[計] 市場擷取 · YELLOW · 沒有合 VDF 引擎版本界線" in run.stdout and "py=" not in run.stdout and "[計] 市場填值 · GREEN · py=" in run2.stdout and "沒有合界線的 · --fill 用本行程" in run2.stdout)
            run = subprocess.run([str(good), "-X", "utf8", me, "--tool", str(tool), "--python", str(good), "--pick-python"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            got = json.loads(run.stdout.strip().splitlines()[-1])
            chk("⑧ --pick-python 印 JSON(界線 · 來源 · 每個候選缺什麼)· 沒有合的 → python null · rc 2 · 填值用 fill_python(能匯入 pandas / pyarrow 的第一個)",
                got["python"] is None and run.returncode == 2 and got["requirements_from"] == engine.name and got["candidates"][0]["how"] == "--python" and "vrn2fakepkg>=9" in got["why"]
                and got["fill_python"] == str(good) and fill_python([{"python": "a", "py_version": "3.12", "import_failed": ["pandas(ModuleNotFoundError)"]}, {"python": "b", "py_version": "3.12", "import_failed": ["yfinance(X)"]}]) == "b")
        shared = sorted((HERE.parent / "VRN").glob("VRN2_MarketFetch_v[0-9][0-9][0-9][0-9].py"))
        if shared:
            module = load_tool(shared[-1], "vrn2_marketfetch_selftest")
            reqs, source = requirements(module.engine_path())
            chk("⑨ 共用夾的 %s 載得進來(不改不抄)· 有 fetch_python / main / engine_path · 界線 %d 項(%s)· 探測 %s" % (shared[-1].name, len(reqs), source, " ".join(probe_modules_of(shared[-1]))),
                callable(getattr(module, "fetch_python", None)) and callable(getattr(module, "main", None)) and len(reqs) >= 5 and set(probe_modules_of(shared[-1])) >= {"yfinance", "pandas"})
        else:
            print("[SKIP] ⑨ 共用夾 functional modules/VRN 沒有 VRN2_MarketFetch(不在 VIA 樹裡跑)", flush=True)
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    print("[%s] VRN2_MarketFetchRun %s --selftest · 9 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, len(bad)), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
