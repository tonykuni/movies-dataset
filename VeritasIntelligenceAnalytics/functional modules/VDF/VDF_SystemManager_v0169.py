#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0169 — 標準 System Manager(依 VIA_SystemManager_Standard_v0100 從頭重作)

操作員令(2026-11-11):「確認三個獨立系統三個 main() 三個 system manager · 補齊基本功能 · 更健全 · 遵守更新後獨立系統規範 ·
沒有誰管誰 · 主導全修正全在我跟 AI · 不符合就從頭規劃標準 system manager 重作」。
實測缺口(2026-11-11):管理器缺 help / version;engines 借用 VCGC 函式列尾版(只讀借用 · 仍是相依)
本版是 VDF 自己的入口(L120 / L123):
  · 標準動詞本版自己做:help · version · health · engines · records · peers · conform · selftest(status / test 轉交前版(保留舊判讀))。
  · 其餘動詞(前版鏈全部功能)一律以子行程原樣轉交前版 VDF_SystemManager_v0168(參數 · 環境 · rc 不變)—— 只增不減,不可丟失。
    標準動詞後加 --legacy 也轉交前版(看前版原本的版本)。
  · 對等:不 import / 不載入其他系統模組(本檔零動態載入);不要求其他系統的放行旗標;peers 只讀對方檔案(不執行對方程式碼、不寫對方)。
  · 編號依 L122 / L125(本檔不寫號冊)。前版檔一字不動(版號律)。不碰 TA-Lib;不讀寫同意閘;零網路。
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本管理器標準動詞不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CONFIG = {'system': 'VDF',
 'manager_family': 'VDF_SystemManager',
 'dir': 'functional modules/VDF',
 'own_prefixes': ['VDF_'],
 'reports': ['VIA_Reports/vdf_fetch', 'VIA_Reports/vdf'],
 'ssot_glob': 'VDF_FetchSystem_SSOT_v*.json',
 'forward_verbs': ['status', 'test'],
 'native_extra': [],
 'peer_gate_flags': ['VIA_FROM_VCGC'],
 'report_env': ['VIA_NET_CONSENT', 'VIA_SCRAPE_CONSENT'],
 'custom_health': [{'name': 'fetch_system', 'glob': 'functional modules/VDF/VDF_MDL008_FetchSystem_v*.py'},
                   {'name': 'stock_list_generator', 'glob': 'functional modules/VDF/VDF_MDL009_TWStockList_v*.py'},
                   {'name': 'etf_list_generator', 'glob': 'functional modules/VDF/VDF_MDL010_*_v*.py'}],
 'peers': {'VCGC': {'manager_family': 'CGC_MDL149_VeritasCentralGovernanceConsole',
                    'dir': 'supportive modules/registry',
                    'own_prefixes': ['CGC_'],
                    'reports': ['VIA_Reports/vcgc']},
           'VRN': {'manager_family': 'VRN_SystemManager',
                   'dir': 'functional modules/VRN',
                   'own_prefixes': ['VRN2_', 'VRN_'],
                   'reports': ['VIA_Reports/vrn2']}}}
VERSION = "v0169"
TAG = CONFIG["manager_family"] + " " + VERSION
HERE = Path(__file__).resolve()
NATIVE = ("help", "version", "health", "engines", "records", "peers", "conform", "selftest") + tuple(CONFIG["native_extra"])
SKIP = {"__pycache__", "_superseded", "_superseded_redundant", "VIA_RetiredEngines", "references", "intake", "retired", "evidence",
        "node_modules", ".git", "VIA_Reports"}
VER_RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M +00:00")


def via_root(start: Path | None = None) -> Path:
    p = (start or HERE).resolve()
    for q in [p] + list(p.parents):
        if (q / "functional modules").is_dir() and (q / "supportive modules").is_dir():
            return q
    return HERE.parents[2]


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def prior_path(root: Path) -> Path | None:
    d = root / CONFIG["dir"]
    mine = _vnum(HERE)
    cands = [p for p in d.glob(CONFIG["manager_family"] + "_v*.py") if 0 <= _vnum(p) < mine]
    return max(cands, key=_vnum) if cands else None


def has_main(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return False
    return any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)


def forward(args: list, root: Path) -> int:
    """前版其餘功能原樣轉交(子行程 · 參數 / 環境 / cwd / rc 不變)。"""
    pp = prior_path(root)
    if pp is None:
        print(f"[{TAG}] ABSENT · 前版 {CONFIG['manager_family']}_v* 不在 {root / CONFIG['dir']}(動詞 {args[:1]} 無從轉交)")
        return 3
    return subprocess.run([sys.executable, str(pp), *args]).returncode


# ---------- 自己的樹(只看自己)----------
def own_files(root: Path) -> list:
    base = root / CONFIG["dir"]
    out = []
    for p in base.rglob("*.py"):
        rel = p.relative_to(base)
        if any(part in SKIP for part in rel.parts[:-1]):
            continue
        if p.name.startswith(tuple(CONFIG["own_prefixes"])) and VER_RX.match(p.name):
            out.append(p)
    return out


def engines(root: Path) -> dict:
    fams = {}
    for p in own_files(root):
        m = VER_RX.match(p.name)
        f = fams.setdefault(m.group("fam"), {"versions": 0, "tail": None, "tail_ver": -1})
        f["versions"] += 1
        v = int(m.group("ver"))
        if v > f["tail_ver"]:
            f.update(tail=str(p.relative_to(root)), tail_ver=v)
    return dict(sorted(fams.items()))


def records(root: Path, n: int = 10) -> list:
    rows = []
    for rel in CONFIG["reports"]:
        d = root / rel
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file():
                    st = p.stat()
                    rows.append({"file": str(p.relative_to(root)), "bytes": st.st_size,
                                 "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M")})
    return sorted(rows, key=lambda r: r["mtime"], reverse=True)[:n]


def peers(root: Path) -> list:
    """只讀:對方管理器尾版在否 · 對方自報收據最新時間。不執行、不 import、不寫。"""
    out = []
    for name, pc in CONFIG["peers"].items():
        d = root / pc["dir"]
        tails = sorted(d.glob(pc["manager_family"] + "_v*.py"), key=_vnum) if d.is_dir() else []
        newest = None
        for rel in pc["reports"]:
            rd = root / rel
            if rd.is_dir():
                for p in rd.rglob("*"):
                    if p.is_file():
                        t = p.stat().st_mtime
                        newest = t if newest is None or t > newest else newest
        out.append({"system": name, "manager_tail": tails[-1].name if tails else None,
                     "self_report_latest": datetime.fromtimestamp(newest, timezone.utc).strftime("%Y-%m-%d %H:%M") if newest else None,
                     "lamp": "GREEN" if tails else "ABSENT"})
    return out


def version_info(root: Path) -> dict:
    pp = prior_path(root)
    return {"system": CONFIG["system"], "manager": HERE.name, "version": VERSION, "sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
            "prior": pp.name if pp else None, "prior_has_main": has_main(pp) if pp else False, "main": has_main(HERE),
            "own_dir": CONFIG["dir"], "standard": "VIA_SystemManager_Standard_v0100"}


def static_checks(path: Path) -> dict:
    """P3 / P4 / P7 / P8 的靜態部分(對本檔)。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    imports = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    imports += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    peer_prefixes = tuple(x for pc in CONFIG["peers"].values() for x in pc["own_prefixes"])
    dyn = "spec_from_file_location" + "("
    flags = [f for f in CONFIG["peer_gate_flags"] if re.search(r"environ(?:\.get)?\(?\[?[\"']" + f, src)]
    return {"P1_main": has_main(path),
            "P3_no_peer_gate": not flags,
            "P4_no_peer_import": not any(i.startswith(peer_prefixes) for i in imports) and dyn not in src.replace("dyn = ", ""),
            "P7_accel_bridge": "[VIA:ACCEL-BRIDGE" in src,
            "P7_net_bridge": "[VIA:NET-BRIDGE" in src and "def _via_net" in src,
            "P8_no_talib": not re.search(r"^\s*(import|from)\s+talib", src, re.M),
            "P8_no_consent_write": not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src)}


def health(root: Path) -> dict:
    checks = {"own_dir": (root / CONFIG["dir"]).is_dir()}
    pp = prior_path(root)
    checks["prior_present"] = pp is not None
    checks["prior_has_main"] = bool(pp) and has_main(pp)
    checks["ssot_present"] = any((root / CONFIG["dir"]).glob(CONFIG["ssot_glob"]))
    checks.update(static_checks(HERE))
    soft = {"ssot_present"}
    for c in CONFIG["custom_health"]:                         # 各系統客製健檢(宣告式:只讀自己樹上的檔)
        hits = sorted(root.glob(c["glob"]), key=_vnum)
        ok = bool(hits)
        if ok and "json_path" in c:                           # 內容檢:最新一版 JSON 的某欄 == 期望值
            try:
                cur = json.loads(hits[-1].read_text(encoding="utf-8"))
                for k in c["json_path"].split("."):
                    cur = cur[k]
                ok = cur == c["equals"]
            except (OSError, ValueError, KeyError, TypeError):
                ok = False
        checks[c["name"]] = ok
        if not c.get("required", True):
            soft.add(c["name"])
    info = {e: ("SET" if os.environ.get(e) else "NOT_SET") for e in CONFIG.get("report_env", [])}   # 只報,不設
    red = [k for k, v in checks.items() if not v and k not in soft]
    yellow = [k for k, v in checks.items() if not v and k in soft]
    lamp = "RED" if red else ("YELLOW" if yellow else "GREEN")
    return {"lamp": lamp, "checks": checks, "red": red, "yellow": yellow, "env": info}


def spec_path(root: Path) -> Path | None:
    hits = sorted((root / "docs" / "handoff" / "ai").glob("VIA_SystemManager_Standard_v*.json"), key=_vnum)
    return hits[-1] if hits else None


def conform(root: Path) -> dict:
    sp = spec_path(root)
    if sp is None:
        return {"lamp": "YELLOW", "why": "規範檔不在(系統照常運作,不依賴它)", "missing_verbs": [], "props": {}}
    spec = json.loads(sp.read_text(encoding="utf-8"))
    forwardable = set(CONFIG["forward_verbs"])
    missing = [v for v in spec.get("verbs", {}) if v not in NATIVE and v not in forwardable]
    props = static_checks(HERE)
    bad = [k for k, v in props.items() if not v]
    return {"lamp": "GREEN" if not missing and not bad else "RED", "spec": sp.name, "missing_verbs": missing, "props": props, "bad": bad}


def test_native(root: Path, only: str = "", max_n: int = 25, timeout: int = 120) -> dict:
    fams = engines(root)
    rows, untested = [], 0
    picked = []
    for fam, f in fams.items():
        p = root / f["tail"]
        if only and only not in fam:
            continue
        if "--selftest" not in p.read_text(encoding="utf-8", errors="replace"):
            continue
        picked.append((fam, p))
    for fam, p in picked[:max_n]:
        try:
            r = subprocess.run([sys.executable, str(p), "--selftest"], cwd=tempfile.gettempdir(), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=timeout, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            rows.append({"family": fam, "rc": r.returncode, "result": "PASS" if r.returncode == 0 else "FAIL"})
        except subprocess.TimeoutExpired:
            rows.append({"family": fam, "rc": 124, "result": "TIMEOUT"})
    untested = len(picked) - len(rows)
    fail = [r for r in rows if r["result"] != "PASS"]
    lamp = "RED" if fail else ("YELLOW" if untested or not rows else "GREEN")
    return {"lamp": lamp, "tested": len(rows), "untested": untested, "fail": fail, "rows": rows}


RC = {"GREEN": 0, "RED": 1, "YELLOW": 2, "ABSENT": 3}


def cmd(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "help":
        print(f"{TAG} · {CONFIG['system']} 自己的入口(對等 · 不管別人 · 不被別人管)")
        print("  標準動詞(本版):" + " · ".join(NATIVE))
        print(f"  其餘動詞:原樣轉交前版 {prior_path(root).name if prior_path(root) else '(不在)'};標準動詞加 --legacy 也轉交前版")
        print("  rc:0 綠 · 1 紅 · 2 黃 / 過期 / 沒量 · 3 缺件 · 4 等同意閘")
        return 0
    if verb == "version":
        v = version_info(root)
        print(json.dumps(v, ensure_ascii=False, indent=1) if as_json else
              f"[{TAG}] {v['system']} · {v['manager']} · sha {v['sha256'][:12]} · main {v['main']} · 前版 {v['prior']}(main {v['prior_has_main']})")
        return 0
    if verb == "health":
        h = health(root)
        print(json.dumps(h, ensure_ascii=False, indent=1) if as_json else
              f"[{TAG}] health {h['lamp']} · " + " · ".join(f"{k} {'✓' if v else '✗'}" for k, v in h["checks"].items())
              + ("" if not h["env"] else " · 環境(只報不設) " + " · ".join(f"{k} {v}" for k, v in h["env"].items())))
        return RC[h["lamp"]]
    if verb == "engines":
        e = engines(root)
        if as_json:
            print(json.dumps(e, ensure_ascii=False, indent=1))
        else:
            for fam, f in list(e.items())[:200]:
                print(f"  {fam:<50} v{f['tail_ver']:04d} · {f['versions']} 版")
            print(f"[{TAG}] 尾版家族 {len(e)}(只看自己的夾 {CONFIG['dir']})")
        return 0 if e else 2
    if verb == "records":
        r = records(root)
        for x in r:
            print(f"  {x['mtime']}  {x['bytes']:>10,}  {x['file']}")
        print(f"[{TAG}] 自己的收據 / 日誌最新 {len(r)} 筆" + ("" if r else "(NODATA:還沒有收據)"))
        return 0 if r else 2
    if verb == "peers":
        ps = peers(root)
        for x in ps:
            print(f"  {x['system']:<6} {x['lamp']:<6} 管理器尾版 {x['manager_tail']} · 自報收據最新 {x['self_report_latest'] or '無'}")
        print(f"[{TAG}] 對等系統只讀監控 {len(ps)} 個(不執行 · 不改對方)")
        return 0
    if verb == "conform":
        c = conform(root)
        print(json.dumps(c, ensure_ascii=False, indent=1) if as_json else
              f"[{TAG}] conform {c['lamp']} · 規範 {c.get('spec', '—')} · 缺動詞 {c['missing_verbs']} · 不合 {c.get('bad', [])}" + (f" · {c['why']}" if c.get("why") else ""))
        return RC[c["lamp"]]
    if verb == "test":
        only = args[args.index("--only") + 1] if "--only" in args else ""
        mx = int(args[args.index("--max") + 1]) if "--max" in args else 25
        t = test_native(root, only, mx)
        for x in t["rows"]:
            print(f"  {x['result']:<8}{x['family']} · rc {x['rc']}")
        print(f"[{TAG}] test {t['lamp']} · 測 {t['tested']} · 沒測到 {t['untested']}(照實記 NODATA)· 失敗 {len(t['fail'])}")
        return RC[t["lamp"]]
    if verb == "status":
        h = health(root)
        print(f"[{TAG}] status {h['lamp']}(本版無前版 status 可轉交,用 health)")
        return RC[h["lamp"]]
    return 2


def _nest(path: str, val):
    out = val
    for k in reversed(path.split(".")):
        out = {k: out}
    return out


def _fixture_json(c: dict) -> str:
    return json.dumps(_nest(c["json_path"], c["equals"])) if "json_path" in c else "{}"


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        (root / "supportive modules").mkdir(parents=True)
        own = root / CONFIG["dir"]
        own.mkdir(parents=True, exist_ok=True)
        prior = own / (CONFIG["manager_family"] + "_v0001.py")
        prior.write_text("import sys\ndef main(a):\n    print('PRIOR', a)\n    return 7 if a[:1]==['boom'] else 0\nif __name__=='__main__':\n"
                         "    sys.exit(main(sys.argv[1:]))\n", encoding="utf-8")
        fam = CONFIG["own_prefixes"][0] + "ENG001_Demo"
        (own / f"{fam}_v0100.py").write_text("import sys\nif '--selftest' in sys.argv: sys.exit(0)\n", encoding="utf-8")
        (own / f"{fam}_v0101.py").write_text("import sys\nif '--selftest' in sys.argv: sys.exit(1)\n", encoding="utf-8")
        for name, pc in CONFIG["peers"].items():
            pd = root / pc["dir"]
            pd.mkdir(parents=True, exist_ok=True)
            (pd / (pc["manager_family"] + "_v0005.py")).write_text("def main():\n    return 0\n", encoding="utf-8")
            for rel in pc["reports"][:1]:
                (root / rel).mkdir(parents=True, exist_ok=True)
                (root / rel / "receipt.json").write_text("{}", encoding="utf-8")
        rd = root / CONFIG["reports"][0]
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "mine.json").write_text("{}", encoding="utf-8")
        (root / "docs" / "handoff" / "ai").mkdir(parents=True)
        spec = json.loads((via_root() / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").read_text(encoding="utf-8")) \
            if (via_root() / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").is_file() else {"verbs": {v: "" for v in NATIVE}}
        (root / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").write_text(json.dumps(spec), encoding="utf-8")
        peer_sig = lambda: sorted((str(p), p.read_bytes()) for pc in CONFIG["peers"].values() for p in (root / pc["dir"]).rglob("*") if p.is_file())
        before = peer_sig()
        e = engines(root)
        ck("engines:只看自己的夾(對等系統的檔不列)· 尾版取最大版號", set(e) == {fam, CONFIG["manager_family"]}
           and e[fam]["tail_ver"] == 101 and e[fam]["versions"] == 2, sorted(e))
        ck("version:前版找得到且有 main", version_info(root)["prior"] == prior.name and version_info(root)["prior_has_main"])
        ck("records:只列自己的收據", [r["file"] for r in records(root)] == [str((rd / "mine.json").relative_to(root))])
        ps = peers(root)
        ck("peers:對方管理器尾版 · 自報收據時間(只讀)", all(x["lamp"] == "GREEN" and x["self_report_latest"] for x in ps) and len(ps) == len(CONFIG["peers"]), ps)
        for c in CONFIG["custom_health"]:
            if c.get("required", True):
                f = root / c["glob"].replace("**/", "").replace("*", "0100")
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(_fixture_json(c), encoding="utf-8")
        h = health(root)
        ck("health:缺 SSOT → YELLOW(不是紅)· 客製必要項在 → 其餘綠", h["lamp"] == "YELLOW" and not h["red"], (h["red"], h["yellow"]))
        miss = [c for c in CONFIG["custom_health"] if c.get("required", True)]
        if miss:
            f = root / miss[0]["glob"].replace("**/", "").replace("*", "0100")
            f.unlink()
            ck(f"health:客製必要項缺({miss[0]['name']})→ RED", miss[0]["name"] in health(root)["red"])
            f.write_text(_fixture_json(miss[0]), encoding="utf-8")
        jc = [c for c in CONFIG["custom_health"] if "json_path" in c]
        if jc:
            f = root / jc[0]["glob"].replace("*", "0100")
            f.write_text(json.dumps(_nest(jc[0]["json_path"], "WRONG")), encoding="utf-8")
            ck(f"health:內容檢({jc[0]['name']})值不符 → RED", jc[0]["name"] in health(root)["red"])
            f.write_text(_fixture_json(jc[0]), encoding="utf-8")
        sf = own / CONFIG["ssot_glob"].replace("*", "0100")
        sf.parent.mkdir(parents=True, exist_ok=True)
        sf.write_text("{}", encoding="utf-8")
        hy = health(root)
        opt = [c for c in CONFIG["custom_health"] if not c.get("required", True)]
        ck("health:非必要客製項缺 → 只黃不紅", (hy["lamp"] == "YELLOW" and set(hy["yellow"]) == {c["name"] for c in opt}) if opt else hy["lamp"] == "GREEN",
           hy["yellow"])
        for c in opt:
            f = root / c["glob"].replace("**/", "").replace("*", "0100")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("{}", encoding="utf-8")
        ck("health:SSOT 與客製項都在 → GREEN", health(root)["lamp"] == "GREEN", health(root)["yellow"])
        c = conform(root)
        ck("conform:規範動詞全覆蓋 · P1–P8 靜態全過", c["lamp"] == "GREEN", (c.get("missing_verbs"), c.get("bad")))
        t = test_native(root)
        ck("test(本版):逐支 --selftest · 失敗照實紅", t["lamp"] == "RED" and t["tested"] == 1 and t["fail"][0]["family"] == fam, t)
        keep_here = sys.modules[__name__].__dict__["HERE"]
        try:
            globals()["HERE"] = own / (CONFIG["manager_family"] + "_v0002.py")
            r1 = subprocess.run([sys.executable, str(prior), "hello", "x"], capture_output=True, text=True)
            rc_fwd = forward(["boom"], root)
        finally:
            globals()["HERE"] = keep_here
        ck("轉交前版:參數原樣 · rc 原樣(7)", "PRIOR ['hello', 'x']" in r1.stdout and rc_fwd == 7, rc_fwd)
        ck("P5 實測:跑完標準動詞,對等系統的樹一字未動", before == peer_sig())
    sc = static_checks(HERE)
    ck("本檔靜態:P1 main · P3 無他系統放行旗標 · P4 無跨系統載入 · P7 橋 · P8", all(sc.values()), [k for k, v in sc.items() if not v])
    print(f"[計] {TAG} 自測 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = via_root()
    if not args:
        return cmd("help", [], root)
    verb = args[0]
    if verb in ("--selftest", "selftest"):
        return selftest()
    if verb in NATIVE and "--legacy" not in args:
        return cmd(verb, args[1:], root)
    return forward([a for a in args if a != "--legacy"], root)


if __name__ == "__main__":
    sys.exit(main())
