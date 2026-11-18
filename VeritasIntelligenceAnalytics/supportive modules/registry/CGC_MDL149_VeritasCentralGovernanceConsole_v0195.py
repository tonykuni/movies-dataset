#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0195 — 標準 System Manager(依 VIA_SystemManager_Standard_v0100 從頭重作)

操作員令(2026-11-11):「確認三個獨立系統三個 main() 三個 system manager · 補齊基本功能 · 更健全 · 遵守更新後獨立系統規範 ·
沒有誰管誰 · 主導全修正全在我跟 AI · 不符合就從頭規劃標準 system manager 重作」。
實測缺口(2026-11-11):主控台缺 health / version / engines / records(未知動詞退回印 help)
本版是 VCGC 自己的入口(L120 / L123):
  · 標準動詞本版自己做:help · version · health · engines · records · peers · conform · selftest(status / test 轉交前版(保留舊判讀))。
  · 其餘動詞(前版鏈全部功能)一律以子行程原樣轉交前版 CGC_MDL149_VeritasCentralGovernanceConsole_v0194(參數 · 環境 · rc 不變)—— 只增不減,不可丟失。
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
import importlib.util
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SM_CONFIG = {'system': 'VCGC',
 'manager_family': 'CGC_MDL149_VeritasCentralGovernanceConsole',
 'dir': 'supportive modules/registry',
 'own_prefixes': ['CGC_'],
 'reports': ['VIA_Reports/vcgc'],
 'ssot_glob': 'VIA_Numbering_SSOT_v*.json',
 'forward_verbs': ['status', 'test'],
 'native_extra': [],
 'peer_gate_flags': ['VIA_FROM_VDFSM', 'VIA_FROM_VRN'],
 'own_entry_flag': 'VIA_FROM_VCGC',
 'report_env': [],
 'custom_health': [{'name': 'token_lock', 'glob': 'supportive modules/registry/VIA_ToolVersion_Lock_v*.json'},
                   {'name': 'number_books', 'glob': 'supportive modules/registry/VIA_NumberBooks/*.jsonl'},
                   {'name': 'receipts_book',
                    'glob': 'supportive modules/registry/VIA_RegistrationReceipts_v*.jsonl',
                    'required': False}],
 'peers': {'VDF': {'manager_family': 'VDF_SystemManager',
                   'dir': 'functional modules/VDF',
                   'own_prefixes': ['VDF_'],
                   'reports': ['VIA_Reports/vdf_fetch', 'VIA_Reports/vdf']},
           'VRN': {'manager_family': 'VRN_SystemManager',
                   'dir': 'functional modules/VRN',
                   'own_prefixes': ['VRN2_', 'VRN_'],
                   'reports': ['VIA_Reports/vrn2']}}}
SM_VERSION = "v0195"
SM_TAG = SM_CONFIG["manager_family"] + " " + SM_VERSION
SM_HERE = Path(__file__).resolve()
SM_NATIVE = ("help", "version", "health", "engines", "records", "peers", "conform", "selftest") + tuple(SM_CONFIG["native_extra"])
SM_SKIP = {"__pycache__", "_superseded", "_superseded_redundant", "VIA_RetiredEngines", "references", "intake", "retired", "evidence",
        "node_modules", ".git", "VIA_Reports"}
SM_VER_RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")


def sm_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M +00:00")


def sm_via_root(start: Path | None = None) -> Path:
    p = (start or SM_HERE).resolve()
    for q in [p] + list(p.parents):
        if (q / "functional modules").is_dir() and (q / "supportive modules").is_dir():
            return q
    return SM_HERE.parents[2]


def sm_vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def sm_prior_path(root: Path) -> Path | None:
    d = root / SM_CONFIG["dir"]
    mine = sm_vnum(SM_HERE)
    cands = [p for p in d.glob(SM_CONFIG["manager_family"] + "_v*.py") if 0 <= sm_vnum(p) < mine]
    return max(cands, key=sm_vnum) if cands else None


def sm_has_main(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return False
    return any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)


def sm_forward(args: list, root: Path) -> int:
    """前版其餘功能原樣轉交(子行程 · 參數 / 環境 / cwd / rc 不變)。"""
    pp = sm_prior_path(root)
    if pp is None:
        print(f"[{SM_TAG}] ABSENT · 前版 {SM_CONFIG['manager_family']}_v* 不在 {root / SM_CONFIG['dir']}(動詞 {args[:1]} 無從轉交)")
        return 3
    return subprocess.run([sys.executable, str(pp), *args], env=sm_child_env()).returncode


def sm_child_env() -> dict:
    """子行程環境:只補「本系統自己的」入口旗標(own_entry_flag;不設他系統旗標 · P3)。"""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    own = SM_CONFIG.get("own_entry_flag")
    if own:
        env.setdefault(own, "YES")
    return env


_SM_PRIOR = None


def _sm_prior_module():
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(只載入自己系統的前版;要用才載)。"""
    global _SM_PRIOR
    if _SM_PRIOR is None:
        pp = sm_prior_path(sm_via_root())
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(SM_CONFIG["manager_family"] + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _SM_PRIOR = mod
    return _SM_PRIOR


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_sm_prior_module(), name)


# ---------- 自己的樹(只看自己)----------
def sm_own_files(root: Path) -> list:
    base = root / SM_CONFIG["dir"]
    out = []
    for p in base.rglob("*.py"):
        rel = p.relative_to(base)
        if any(part in SM_SKIP for part in rel.parts[:-1]):
            continue
        if p.name.startswith(tuple(SM_CONFIG["own_prefixes"])) and SM_VER_RX.match(p.name):
            out.append(p)
    return out


def sm_engines(root: Path) -> dict:
    fams = {}
    for p in sm_own_files(root):
        m = SM_VER_RX.match(p.name)
        f = fams.setdefault(m.group("fam"), {"versions": 0, "tail": None, "tail_ver": -1})
        f["versions"] += 1
        v = int(m.group("ver"))
        if v > f["tail_ver"]:
            f.update(tail=str(p.relative_to(root)), tail_ver=v)
    return dict(sorted(fams.items()))


def sm_records(root: Path, n: int = 10) -> list:
    rows = []
    for rel in SM_CONFIG["reports"]:
        d = root / rel
        if d.is_dir():
            for p in d.rglob("*"):
                if p.is_file():
                    st = p.stat()
                    rows.append({"file": str(p.relative_to(root)), "bytes": st.st_size,
                                 "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M")})
    return sorted(rows, key=lambda r: r["mtime"], reverse=True)[:n]


def sm_peers(root: Path) -> list:
    """只讀:對方管理器尾版在否 · 對方自報收據最新時間。不執行、不 import、不寫。"""
    out = []
    for name, pc in SM_CONFIG["peers"].items():
        d = root / pc["dir"]
        tails = sorted(d.glob(pc["manager_family"] + "_v*.py"), key=sm_vnum) if d.is_dir() else []
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


def sm_version_info(root: Path) -> dict:
    pp = sm_prior_path(root)
    return {"system": SM_CONFIG["system"], "manager": SM_HERE.name, "version": SM_VERSION, "sha256": hashlib.sha256(SM_HERE.read_bytes()).hexdigest(),
            "prior": pp.name if pp else None, "prior_has_main": sm_has_main(pp) if pp else False, "main": sm_has_main(SM_HERE),
            "own_dir": SM_CONFIG["dir"], "standard": "VIA_SystemManager_Standard_v0100"}


def sm_static_checks(path: Path) -> dict:
    """P3 / P4 / P7 / P8 的靜態部分(對本檔)。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    imports = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    imports += [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    peer_prefixes = tuple(x for pc in SM_CONFIG["peers"].values() for x in pc["own_prefixes"])
    dyn_n = src.count("spec_from_file_location" + "(")
    flags = [f for f in SM_CONFIG["peer_gate_flags"] if re.search(r"environ(?:\.get)?\(?\[?[\"']" + f, src)]
    return {"P1_main": sm_has_main(path),
            "P3_no_peer_gate": not flags,
            "P3_own_flag_not_peer": SM_CONFIG.get("own_entry_flag") not in SM_CONFIG["peer_gate_flags"],
            "P4_no_peer_import": not any(i.startswith(peer_prefixes) for i in imports) and dyn_n <= 1
                           and ("sm_prior_path(sm_via_root())" in src if dyn_n else True),
            "P7_accel_bridge": "[VIA:ACCEL-BRIDGE" in src,
            "P7_net_bridge": "[VIA:NET-BRIDGE" in src and "def _via_net" in src,
            "P8_no_talib": not re.search(r"^\s*(import|from)\s+talib", src, re.M),
            "P8_no_consent_write": not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src)}


def sm_health(root: Path) -> dict:
    checks = {"own_dir": (root / SM_CONFIG["dir"]).is_dir()}
    pp = sm_prior_path(root)
    checks["prior_present"] = pp is not None
    checks["prior_has_main"] = bool(pp) and sm_has_main(pp)
    checks["ssot_present"] = any((root / SM_CONFIG["dir"]).glob(SM_CONFIG["ssot_glob"]))
    checks.update(sm_static_checks(SM_HERE))
    soft = {"ssot_present"}
    for c in SM_CONFIG["custom_health"]:                         # 各系統客製健檢(宣告式:只讀自己樹上的檔)
        hits = sorted(root.glob(c["glob"]), key=sm_vnum)
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
    info = {e: ("SET" if os.environ.get(e) else "NOT_SET") for e in SM_CONFIG.get("report_env", [])}   # 只報,不設
    red = [k for k, v in checks.items() if not v and k not in soft]
    yellow = [k for k, v in checks.items() if not v and k in soft]
    lamp = "RED" if red else ("YELLOW" if yellow else "GREEN")
    return {"lamp": lamp, "checks": checks, "red": red, "yellow": yellow, "env": info}


def sm_spec_path(root: Path) -> Path | None:
    hits = sorted((root / "docs" / "handoff" / "ai").glob("VIA_SystemManager_Standard_v*.json"), key=sm_vnum)
    return hits[-1] if hits else None


def sm_conform(root: Path) -> dict:
    sp = sm_spec_path(root)
    if sp is None:
        return {"lamp": "YELLOW", "why": "規範檔不在(系統照常運作,不依賴它)", "missing_verbs": [], "props": {}}
    spec = json.loads(sp.read_text(encoding="utf-8"))
    forwardable = set(SM_CONFIG["forward_verbs"])
    missing = [v for v in spec.get("verbs", {}) if v not in SM_NATIVE and v not in forwardable]
    props = sm_static_checks(SM_HERE)
    bad = [k for k, v in props.items() if not v]
    return {"lamp": "GREEN" if not missing and not bad else "RED", "spec": sp.name, "missing_verbs": missing, "props": props, "bad": bad}


def sm_test_native(root: Path, only: str = "", max_n: int = 25, timeout: int = 120) -> dict:
    fams = sm_engines(root)
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
                               encoding="utf-8", errors="replace", timeout=timeout, env=sm_child_env())
            rows.append({"family": fam, "rc": r.returncode, "result": "PASS" if r.returncode == 0 else "FAIL"})
        except subprocess.TimeoutExpired:
            rows.append({"family": fam, "rc": 124, "result": "TIMEOUT"})
    untested = len(picked) - len(rows)
    fail = [r for r in rows if r["result"] != "PASS"]
    lamp = "RED" if fail else ("YELLOW" if untested or not rows else "GREEN")
    return {"lamp": lamp, "tested": len(rows), "untested": untested, "fail": fail, "rows": rows}


SM_RC = {"GREEN": 0, "RED": 1, "YELLOW": 2, "ABSENT": 3}


def sm_cmd(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "help":
        print(f"{SM_TAG} · {SM_CONFIG['system']} 自己的入口(對等 · 不管別人 · 不被別人管)")
        print("  標準動詞(本版):" + " · ".join(SM_NATIVE))
        print(f"  其餘動詞:原樣轉交前版 {sm_prior_path(root).name if sm_prior_path(root) else '(不在)'};標準動詞加 --legacy 也轉交前版")
        print("  rc:0 綠 · 1 紅 · 2 黃 / 過期 / 沒量 · 3 缺件 · 4 等同意閘")
        return 0
    if verb == "version":
        v = sm_version_info(root)
        print(json.dumps(v, ensure_ascii=False, indent=1) if as_json else
              f"[{SM_TAG}] {v['system']} · {v['manager']} · sha {v['sha256'][:12]} · main {v['main']} · 前版 {v['prior']}(main {v['prior_has_main']})")
        return 0
    if verb == "health":
        h = sm_health(root)
        print(json.dumps(h, ensure_ascii=False, indent=1) if as_json else
              f"[{SM_TAG}] health {h['lamp']} · " + " · ".join(f"{k} {'✓' if v else '✗'}" for k, v in h["checks"].items())
              + ("" if not h["env"] else " · 環境(只報不設) " + " · ".join(f"{k} {v}" for k, v in h["env"].items())))
        return SM_RC[h["lamp"]]
    if verb == "engines":
        e = sm_engines(root)
        if as_json:
            print(json.dumps(e, ensure_ascii=False, indent=1))
        else:
            for fam, f in list(e.items())[:200]:
                print(f"  {fam:<50} v{f['tail_ver']:04d} · {f['versions']} 版")
            print(f"[{SM_TAG}] 尾版家族 {len(e)}(只看自己的夾 {SM_CONFIG['dir']})")
        return 0 if e else 2
    if verb == "records":
        r = sm_records(root)
        for x in r:
            print(f"  {x['mtime']}  {x['bytes']:>10,}  {x['file']}")
        print(f"[{SM_TAG}] 自己的收據 / 日誌最新 {len(r)} 筆" + ("" if r else "(NODATA:還沒有收據)"))
        return 0 if r else 2
    if verb == "peers":
        ps = sm_peers(root)
        for x in ps:
            print(f"  {x['system']:<6} {x['lamp']:<6} 管理器尾版 {x['manager_tail']} · 自報收據最新 {x['self_report_latest'] or '無'}")
        print(f"[{SM_TAG}] 對等系統只讀監控 {len(ps)} 個(不執行 · 不改對方)")
        return 0
    if verb == "conform":
        c = sm_conform(root)
        print(json.dumps(c, ensure_ascii=False, indent=1) if as_json else
              f"[{SM_TAG}] conform {c['lamp']} · 規範 {c.get('spec', '—')} · 缺動詞 {c['missing_verbs']} · 不合 {c.get('bad', [])}" + (f" · {c['why']}" if c.get("why") else ""))
        return SM_RC[c["lamp"]]
    if verb == "test":
        only = args[args.index("--only") + 1] if "--only" in args else ""
        mx = int(args[args.index("--max") + 1]) if "--max" in args else 25
        t = sm_test_native(root, only, mx)
        for x in t["rows"]:
            print(f"  {x['result']:<8}{x['family']} · rc {x['rc']}")
        print(f"[{SM_TAG}] test {t['lamp']} · 測 {t['tested']} · 沒測到 {t['untested']}(照實記 NODATA)· 失敗 {len(t['fail'])}")
        return SM_RC[t["lamp"]]
    if verb == "status":
        h = sm_health(root)
        print(f"[{SM_TAG}] status {h['lamp']}(本版無前版 status 可轉交,用 health)")
        return SM_RC[h["lamp"]]
    return 2


def sm_nest(path: str, val):
    out = val
    for k in reversed(path.split(".")):
        out = {k: out}
    return out


def sm_fixture_json(c: dict) -> str:
    return json.dumps(sm_nest(c["json_path"], c["equals"])) if "json_path" in c else "{}"


def selftest() -> int:
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"
        (root / "supportive modules").mkdir(parents=True)
        own = root / SM_CONFIG["dir"]
        own.mkdir(parents=True, exist_ok=True)
        prior = own / (SM_CONFIG["manager_family"] + "_v0001.py")
        prior.write_text("import sys\ndef legacy_public():\n    return 'LEGACY_OK'\ndef main(a):\n    print('PRIOR', a)\n    return 7 if a[:1]==['boom'] else 0\nif __name__=='__main__':\n"
                         "    sys.exit(main(sys.argv[1:]))\n", encoding="utf-8")
        fam = SM_CONFIG["own_prefixes"][0] + "ENG001_Demo"
        (own / f"{fam}_v0100.py").write_text("import sys\nif '--selftest' in sys.argv: sys.exit(0)\n", encoding="utf-8")
        (own / f"{fam}_v0101.py").write_text("import sys\nif '--selftest' in sys.argv: sys.exit(1)\n", encoding="utf-8")
        for name, pc in SM_CONFIG["peers"].items():
            pd = root / pc["dir"]
            pd.mkdir(parents=True, exist_ok=True)
            (pd / (pc["manager_family"] + "_v0005.py")).write_text("def main():\n    return 0\n", encoding="utf-8")
            for rel in pc["reports"][:1]:
                (root / rel).mkdir(parents=True, exist_ok=True)
                (root / rel / "receipt.json").write_text("{}", encoding="utf-8")
        rd = root / SM_CONFIG["reports"][0]
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "mine.json").write_text("{}", encoding="utf-8")
        (root / "docs" / "handoff" / "ai").mkdir(parents=True)
        spec = json.loads((sm_via_root() / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").read_text(encoding="utf-8")) \
            if (sm_via_root() / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").is_file() else {"verbs": {v: "" for v in SM_NATIVE}}
        (root / "docs/handoff/ai/VIA_SystemManager_Standard_v0100.json").write_text(json.dumps(spec), encoding="utf-8")
        peer_sig = lambda: sorted((str(p), p.read_bytes()) for pc in SM_CONFIG["peers"].values() for p in (root / pc["dir"]).rglob("*") if p.is_file())
        before = peer_sig()
        e = sm_engines(root)
        ck("engines:只看自己的夾(對等系統的檔不列)· 尾版取最大版號", set(e) == {fam, SM_CONFIG["manager_family"]}
           and e[fam]["tail_ver"] == 101 and e[fam]["versions"] == 2, sorted(e))
        ck("version:前版找得到且有 main", sm_version_info(root)["prior"] == prior.name and sm_version_info(root)["prior_has_main"])
        ck("records:只列自己的收據", [r["file"] for r in sm_records(root)] == [str((rd / "mine.json").relative_to(root))])
        ps = sm_peers(root)
        ck("peers:對方管理器尾版 · 自報收據時間(只讀)", all(x["lamp"] == "GREEN" and x["self_report_latest"] for x in ps) and len(ps) == len(SM_CONFIG["peers"]), ps)
        for c in SM_CONFIG["custom_health"]:
            if c.get("required", True):
                f = root / c["glob"].replace("**/", "").replace("*", "0100")
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(sm_fixture_json(c), encoding="utf-8")
        h = sm_health(root)
        ck("health:缺 SSOT → YELLOW(不是紅)· 客製必要項在 → 其餘綠", h["lamp"] == "YELLOW" and not h["red"], (h["red"], h["yellow"]))
        miss = [c for c in SM_CONFIG["custom_health"] if c.get("required", True)]
        if miss:
            f = root / miss[0]["glob"].replace("**/", "").replace("*", "0100")
            f.unlink()
            ck(f"health:客製必要項缺({miss[0]['name']})→ RED", miss[0]["name"] in sm_health(root)["red"])
            f.write_text(sm_fixture_json(miss[0]), encoding="utf-8")
        jc = [c for c in SM_CONFIG["custom_health"] if "json_path" in c]
        if jc:
            f = root / jc[0]["glob"].replace("*", "0100")
            f.write_text(json.dumps(sm_nest(jc[0]["json_path"], "WRONG")), encoding="utf-8")
            ck(f"health:內容檢({jc[0]['name']})值不符 → RED", jc[0]["name"] in sm_health(root)["red"])
            f.write_text(sm_fixture_json(jc[0]), encoding="utf-8")
        (own / SM_CONFIG["ssot_glob"].replace("*", "0100")).write_text("{}", encoding="utf-8")
        hy = sm_health(root)
        opt = [c for c in SM_CONFIG["custom_health"] if not c.get("required", True)]
        ck("health:非必要客製項缺 → 只黃不紅", (hy["lamp"] == "YELLOW" and set(hy["yellow"]) == {c["name"] for c in opt}) if opt else hy["lamp"] == "GREEN",
           hy["yellow"])
        for c in opt:
            f = root / c["glob"].replace("**/", "").replace("*", "0100")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("{}", encoding="utf-8")
        ck("health:SSOT 與客製項都在 → GREEN", sm_health(root)["lamp"] == "GREEN", sm_health(root)["yellow"])
        c = sm_conform(root)
        ck("conform:規範動詞全覆蓋 · P1–P8 靜態全過", c["lamp"] == "GREEN", (c.get("missing_verbs"), c.get("bad")))
        t = sm_test_native(root)
        ck("test(本版):逐支 --selftest · 失敗照實紅", t["lamp"] == "RED" and t["tested"] == 1 and t["fail"][0]["family"] == fam, t)
        keep_here = sys.modules[__name__].__dict__["SM_HERE"]
        try:
            globals()["SM_HERE"] = own / (SM_CONFIG["manager_family"] + "_v0002.py")
            r1 = subprocess.run([sys.executable, str(prior), "hello", "x"], capture_output=True, text=True)
            rc_fwd = sm_forward(["boom"], root)
        finally:
            globals()["SM_HERE"] = keep_here
        ck("轉交前版:參數原樣 · rc 原樣(7)", "PRIOR ['hello', 'x']" in r1.stdout and rc_fwd == 7, rc_fwd)
        cenv, own_flag = sm_child_env(), SM_CONFIG.get("own_entry_flag")
        ck("子行程只補本系統入口旗標(不補他系統旗標)", (not own_flag or cenv.get(own_flag) == "YES")
           and not [f for f in SM_CONFIG["peer_gate_flags"] if f in cenv and f not in os.environ], own_flag)
        global _SM_PRIOR
        keep_prior, keep_root = _SM_PRIOR, globals()["sm_via_root"]
        try:
            _SM_PRIOR = None
            globals()["SM_HERE"] = own / (SM_CONFIG["manager_family"] + "_v0002.py")
            globals()["sm_via_root"] = lambda start=None: root
            tail_api = sys.modules[__name__].legacy_public()
        finally:
            _SM_PRIOR, globals()["SM_HERE"], globals()["sm_via_root"] = keep_prior, keep_here, keep_root
        ck("尾版律 TAILAPI:前版公開名稱經本檔取得(只載自己系統的前版)", tail_api == "LEGACY_OK", tail_api)
        ck("P5 實測:跑完標準動詞,對等系統的樹一字未動", before == peer_sig())
    sc = sm_static_checks(SM_HERE)
    ck("本檔靜態:P1 main · P3 無他系統放行旗標 · P4 無跨系統載入 · P7 橋 · P8", all(sc.values()), [k for k, v in sc.items() if not v])
    print(f"[計] {SM_TAG} 自測 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = sm_via_root()
    if not args:
        return sm_cmd("help", [], root)
    verb = args[0]
    if verb in ("--selftest", "selftest"):
        return selftest()
    if verb in SM_NATIVE and "--legacy" not in args:
        return sm_cmd(verb, args[1:], root)
    return sm_forward([a for a in args if a != "--legacy"], root)


if __name__ == "__main__":
    sys.exit(main())
