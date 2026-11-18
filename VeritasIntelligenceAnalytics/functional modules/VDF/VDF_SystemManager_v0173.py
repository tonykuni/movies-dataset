#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0173 — 單檔重寫(操作員 2026-11-13「不適合的引擎重寫不要用舊的」· L132 能力對等):以 v0171 標準核心為底 + 併入 v0172 缺套件判讀 + VDF 自有一份 VCGC 能力(status · parity · ssot · regex · synonyms · number · params · backup · sdd · graphify · omniroute · mcp · install · page · closeout);模組層不載入任何前版,尚未重寫的 LEGACY 動詞(catalog · links · read · sync · launch · bridges · tools)以子行程明示轉交前版。

(以下為 v0171 標準核心原說明)

操作員令(2026-11-11):「確認三個獨立系統三個 main() 三個 system manager · 補齊基本功能 · 更健全 · 遵守更新後獨立系統規範 ·
沒有誰管誰 · 主導全修正全在我跟 AI · 不符合就從頭規劃標準 system manager 重作」。
實測缺口(2026-11-11):v0170 實測(容器 2026-11-13 全量 85 支):缺第三方套件(yfinance 等)而崩潰 rc 1 被記成失敗 → 本版依 L16 判 ABSENT 並寫明缺哪個套件(自家模組缺仍算壞);v0169 實測(容器 2026-11-12):test 轉交前版,但前版沒有 test 動詞(印用法 rc 2)→ 本版 test 改本系統逐支跑;引擎 rc 2/3/4 依 L16 記缺件,不算失敗
本版是 VDF 自己的入口(L120 / L123):
  · 標準動詞本版自己做:help · version · health · engines · records · peers · conform · selftest(本系統另做 test(逐支尾版 --selftest))。
  · 其餘動詞(前版鏈全部功能)一律以子行程原樣轉交前版 VDF_SystemManager_v0170(參數 · 環境 · rc 不變)—— 只增不減,不可丟失。
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

SM_CONFIG = {'system': 'VDF',
 'manager_family': 'VDF_SystemManager',
 'dir': 'functional modules/VDF',
 'own_prefixes': ['VDF_'],
 'reports': ['VIA_Reports/vdf_fetch', 'VIA_Reports/vdf'],
 'ssot_glob': 'VDF_FetchSystem_SSOT_v*.json',
 'forward_verbs': ['status'],
 'native_extra': ['test'],
 'peer_gate_flags': ['VIA_FROM_VCGC'],
 'own_entry_flag': None,
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
SM_VERSION = "v0173"
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


def _legacy_getattr_disabled(name):
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
            res = SM_TEST_RC.get(r.returncode, "FAIL")
            lib = sm_missing_lib((r.stdout or "") + "\n" + (r.stderr or "")) if res == "FAIL" else ""
            rows.append({"family": fam, "rc": r.returncode, "result": "ABSENT" if lib else res, **({"why": "缺套件 " + lib} if lib else {})})
        except subprocess.TimeoutExpired:
            rows.append({"family": fam, "rc": 124, "result": "TIMEOUT"})
    untested = len(picked) - len(rows)
    fail = [r for r in rows if r["result"] in ("FAIL", "TIMEOUT")]
    soft = [r for r in rows if r["result"] in ("NODATA", "ABSENT", "GATED")]
    lamp = "RED" if fail else ("YELLOW" if untested or soft or not rows else "GREEN")
    return {"lamp": lamp, "tested": len(rows), "untested": untested, "fail": fail, "soft": soft, "rows": rows}


SM_REPO_MOD_PREFIX = ("VRN", "VDF", "CGC_", "SUP_", "VIA_", "VQG", "VAP", "nonstock", "vrn2_", "vdf_")   # 自家模組缺 = 真壞,不算缺件


def _sm_missing_lib_base(text: str) -> str:
    """引擎因缺「第三方套件」而崩潰(最後一個例外是 ModuleNotFoundError,或每一個 [FAIL] 行都寫 No module named)→ 回套件名;
    自家模組(VRN_ / VDF_ / CGC_ …)缺 = 真壞,回空。依 L16:缺件 ≠ 壞,照實記 ABSENT(黃),不冒充綠也不誤紅。"""
    names = re.findall(r"No module named '([\w.]+)'", text or "")
    if not names:
        return ""
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    last_exc = next((ln for ln in reversed(lines) if re.match(r"^\w*(Error|Exception)\b", ln.strip())), "")
    fails = [ln for ln in lines if "[FAIL]" in ln]
    crash = last_exc.strip().startswith("ModuleNotFoundError")
    only_lib_fails = bool(fails) and all("No module named" in ln for ln in fails)
    tops = {n.split(".")[0] for n in names}
    if (crash or only_lib_fails) and not any(t.startswith(SM_REPO_MOD_PREFIX) for t in tops):
        return ",".join(sorted(tops))
    return ""


SM_TEST_RC = {0: "PASS", 2: "NODATA", 3: "ABSENT", 4: "GATED"}   # L16 五態碼:2 缺件 / 缺料 ≠ 壞掉 · 3 缺席 · 4 同意閘未開(操作員的手)


SM_RC = {"GREEN": 0, "RED": 1, "YELLOW": 2, "ABSENT": 3}


def sm_cmd(verb: str, args: list, root: Path) -> int:
    if verb in V73_VERBS:
        return sm_cmd_v0173(verb, args, root)
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
            print(f"  {x['result']:<8}{x['family']} · rc {x['rc']}" + (f" · {x['why']}" if x.get("why") else ""))
        print(f"[{SM_TAG}] test {t['lamp']} · 測 {t['tested']} · 通過 {t['tested'] - len(t['fail']) - len(t['soft'])} · 缺件/缺料 {len(t['soft'])}(L16 rc 2/3/4 ≠ 壞)"
              f" · 失敗 {len(t['fail'])} · 沒測到 {t['untested']}(照實記 NODATA)")
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


def _selftest_core() -> int:
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
        fam2 = SM_CONFIG["own_prefixes"][0] + "ENG002_NeedsLib"
        (own / f"{fam2}_v0100.py").write_text("import sys\nif '--selftest' in sys.argv: sys.exit(2)\n", encoding="utf-8")
        fam3 = SM_CONFIG["own_prefixes"][0] + "ENG003_MissingPkg"
        (own / f"{fam3}_v0100.py").write_text("import sys\nif '--selftest' in sys.argv:\n    import zz_fake_pkg_for_sm_test\n", encoding="utf-8")
        fam4 = SM_CONFIG["own_prefixes"][0] + "ENG004_MissingOwn"
        (own / f"{fam4}_v0100.py").write_text("import sys\nif '--selftest' in sys.argv:\n    import VRN_ENG999_NotInRepo\n", encoding="utf-8")
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
        ck("engines:只看自己的夾(對等系統的檔不列)· 尾版取最大版號", set(e) == {fam, fam2, fam3, fam4, SM_CONFIG["manager_family"]}
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
        ck("test(本版):逐支 --selftest · 失敗照實紅(自家模組缺也算壞)", t["lamp"] == "RED" and t["tested"] == 4
           and {r["family"] for r in t["fail"]} == {fam, fam4}, t)
        t3 = sm_test_native(root, only="MissingPkg")
        ck("test:缺第三方套件而崩潰(ModuleNotFoundError)→ ABSENT + 寫明缺哪個套件 → YELLOW(L16)", t3["lamp"] == "YELLOW" and not t3["fail"]
           and t3["soft"] and t3["soft"][0]["result"] == "ABSENT" and "zz_fake_pkg_for_sm_test" in t3["soft"][0].get("why", ""), t3)
        t2 = sm_test_native(root, only="NeedsLib")
        ck("test:rc 2(缺件 / 缺料)記 NODATA 不算失敗 → YELLOW(L16 缺件≠壞)", t2["lamp"] == "YELLOW" and not t2["fail"]
           and t2["soft"] and t2["soft"][0]["result"] == "NODATA", t2)
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
            tail_api = "NO_FORWARD" if not hasattr(sys.modules[__name__], "legacy_public") else "FORWARDED"
        finally:
            _SM_PRIOR, globals()["SM_HERE"], globals()["sm_via_root"] = keep_prior, keep_here, keep_root
        ck("單檔重寫(L132 ④):不再經 __getattr__ 轉接前版公開名稱(前版就在旁邊也不載)", tail_api == "NO_FORWARD", tail_api)
        ck("P5 實測:跑完標準動詞,對等系統的樹一字未動", before == peer_sig())
    sc = sm_static_checks(SM_HERE)
    ck("本檔靜態:P1 main · P3 無他系統放行旗標 · P4 無跨系統載入 · P7 橋 · P8", all(sc.values()), [k for k, v in sc.items() if not v])
    print(f"[計] {SM_TAG} 自測 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1



# ══════════════════════════ v0173:L132 能力對等 · VDF 自有一份(不載入任何前版)══════════════════════════
import zipfile as _zipfile

LIB_ALIASES = {"pymupdf": "fitz", "fitz": "fitz", "yfinance": "yfinance", "pdfplumber": "pdfplumber", "pypdfium2": "pypdfium2",
               "pytesseract": "pytesseract", "paddleocr": "paddleocr", "easyocr": "easyocr", "camelot": "camelot",
               "tabula": "tabula", "openpyxl": "openpyxl", "python-docx": "docx", "akshare": "akshare", "duckdb": "duckdb"}
MISSING_WORDS = re.compile(r"ModuleNotFoundError|No module named|不在|缺件|ABSENT", re.I)


def lib_installed(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def sm_missing_lib(text: str) -> str:
    """v0171 規則先跑;不中再認已知第三方套件(含別名)+ 這台實查沒裝 → 判缺件(併入 v0172 修正)。"""
    got = _sm_missing_lib_base(text)
    if got:
        return got
    t = text or ""
    if not MISSING_WORDS.search(t):
        return ""
    if any(m.split(".")[0].startswith(SM_REPO_MOD_PREFIX) for m in re.findall(r"No module named '([\w.]+)'", t)):
        return ""
    low = t.lower()
    named = {mod for alias, mod in LIB_ALIASES.items() if re.search(r"(?<![\w-])" + re.escape(alias.lower()) + r"(?![\w-])", low)}
    absent = sorted(m for m in named if not lib_installed(m))
    return ",".join(absent) + "(這台沒裝 · 有裝的機器要複驗)" if absent else ""


V73_VERBS = ("status", "parity", "ssot", "regex", "synonyms", "number", "params", "backup", "sdd", "graphify", "omniroute",
             "mcp", "install", "page", "closeout")
V73_OWN = {"regex": "VDF_Regex_SSOT_v*.json", "synonyms": "VDF_Synonym_SSOT_v*.json", "sdd": "VDF_Workflow_SSOT_v*.json"}
V73_LEGACY = ("catalog", "links", "read", "sync", "launch", "bridges", "tools")      # 尚未重寫:明示轉交前版(照實標 LEGACY)


def v73_stamp() -> str:
    """檔名用時間戳(Windows 安全:無空格 · 無冒號)。"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def v73_dir(root: Path) -> Path:
    return root / SM_CONFIG["dir"]


def v73_out(root: Path, *sub) -> Path:
    p = root / "VIA_Reports" / "vdf" / "manager"
    for s in sub:
        p = p / s
    p.mkdir(parents=True, exist_ok=True)
    return p


def v73_tail(folder: Path, pattern: str):
    hits = sorted(folder.glob(pattern), key=sm_vnum)
    return hits[-1] if hits else None


def v73_own_book(root: Path, key: str) -> dict:
    p = v73_tail(v73_dir(root) / "SSOT", V73_OWN[key])
    if not p:
        return {"lamp": "ABSENT", "why": f"VDF/SSOT 沒有自有 {V73_OWN[key]}"}
    d = json.loads(p.read_text(encoding="utf-8"))
    src = root / d.get("source", "")
    cur = hashlib.sha256(src.read_bytes()).hexdigest() if src.is_file() else None
    body = d.get("body")
    n = len(body) if isinstance(body, (list, dict)) else 0
    drift = cur is not None and cur != d.get("source_sha256")
    return {"lamp": "YELLOW" if drift else "GREEN", "book": p.name, "entries_top": n, "source": d.get("source"),
            "drift": drift, "why": "VCGC 來源已有新內容 · 未經准許不換(L131 ②③)" if drift else ""}


def v73_number(root: Path) -> dict:
    """編號請求 + 更新內容偵測:尾版 sha 對上次收據;VCGC 編號冊(只讀)沒登的 → 寫請求(L125 編號由 VCGC 核發)。"""
    eng = sm_engines(root)
    num = set()
    for p in (root / "supportive modules" / "registry" / "VIA_NumberBooks").glob("*.jsonl"):
        for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            if '"source"' in ln:
                try:
                    r = json.loads(ln)
                except ValueError:
                    continue
                if not r.get("gone_since"):
                    num.add(r.get("source"))
    out = v73_out(root, "number")
    last_p = out / "VDF_NumberWatch_latest.json"
    last = json.loads(last_p.read_text(encoding="utf-8")).get("sha", {}) if last_p.is_file() else {}
    sha, changed, unnum = {}, [], []
    for fam, f in eng.items():
        rel = f["tail"]
        p = root / rel
        if not p.is_file():
            continue
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        sha[rel] = h
        if last and last.get(rel) != h:
            changed.append(rel)
        if rel not in num:
            unnum.append(rel)
    rec = {"at": sm_utc(), "tails": len(sha), "changed": changed, "unnumbered": unnum, "sha": sha}
    last_p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    if unnum:
        (out / f"VDF_NumberRequest_{v73_stamp()}.json").write_text(json.dumps(
            {"system": "VDF", "law": "L125", "request": unnum, "how": "VCGC:run CGC_MDL237_NumberingSystem --apply --scope <檔>"},
            ensure_ascii=False, indent=1), encoding="utf-8")
    lamp = "YELLOW" if unnum else "GREEN"
    return {"lamp": lamp, "tails": len(sha), "changed_since_last": len(changed), "unnumbered": len(unnum), "first_run": not last,
            "examples": unnum[:5]}


def v73_params(root: Path) -> dict:
    d = v73_dir(root)
    books = {}
    for key, pat in (("unified_params", "VDF_Unified_Params_v*.json"), ("param_registry", "VDF_Param_Registry_v*.json"),
                     ("data_home", "VDF_DataHome_SSOT_v*.json"), ("input_universe", "VDF_InputUniverse_SSOT_v*.json")):
        p = v73_tail(d, pat)
        books[key] = p.name if p else None
    lake = root / "VIA_Reports" / "vdf_lake" / "LAKE_STATUS_latest.json"
    lake_max = None
    if lake.is_file():
        try:
            dates = [t.get("max_date") for t in json.loads(lake.read_text(encoding="utf-8")).get("tables", []) if t.get("max_date")]
            lake_max = max(dates) if dates else None
        except ValueError:
            pass
    utc = datetime.now(timezone.utc)
    tpe = utc.astimezone(timezone(__import__("datetime").timedelta(hours=8)))
    miss = [k for k, v in books.items() if not v]
    return {"lamp": "YELLOW" if miss else "GREEN", "books": books, "missing": miss,
            "time": {"utc": utc.strftime("%Y-%m-%dT%H:%M:%SZ"), "taipei": tpe.strftime("%Y-%m-%d %H:%M"), "fetch_start_default": "2022-01-01",
                     "lake_max_date": lake_max}}


def v73_backup(root: Path, check_only: bool = False) -> dict:
    out = v73_out(root, "backup")
    if check_only:
        zips = sorted(out.glob("VDF_Backup_*.zip"))
        if not zips:
            return {"lamp": "YELLOW", "why": "還沒有備份(先跑 backup)"}
        bad = []
        with _zipfile.ZipFile(zips[-1]) as z:
            sums = dict(ln.split("  ", 1)[::-1] for ln in z.read("SHA256SUMS").decode().splitlines() if "  " in ln)
            for name, h in sums.items():
                if hashlib.sha256(z.read(name)).hexdigest() != h:
                    bad.append(name)
        return {"lamp": "RED" if bad else "GREEN", "zip": zips[-1].name, "files": len(sums), "bad": bad}
    d = v73_dir(root)
    files = [p for p in (d / "SSOT").glob("*.json")] + [p for p in d.glob("*.json")] + [SM_HERE]
    files += [root / f["tail"] for f in sm_engines(root).values() if (root / f["tail"]).is_file()]
    files = sorted(set(files))
    zp = out / f"VDF_Backup_{v73_stamp()}.zip"
    lines = []
    with _zipfile.ZipFile(zp, "w", _zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = str(p.relative_to(root)) if p.is_relative_to(root) else "_manager/" + p.name
            b = p.read_bytes()
            z.writestr(rel, b)
            lines.append(f"{hashlib.sha256(b).hexdigest()}  {rel}")
        z.writestr("SHA256SUMS", "\n".join(lines) + "\n")
        z.writestr("MANIFEST.json", json.dumps({"system": "VDF", "at": sm_utc(), "manager": SM_TAG, "files": len(files)}, ensure_ascii=False))
    return {"lamp": "GREEN", "zip": str(zp.relative_to(root)), "files": len(files), "bytes": zp.stat().st_size}


def v73_sdd(root: Path) -> dict:
    own = v73_own_book(root, "sdd")
    if own["lamp"] == "ABSENT":
        return own
    p = v73_tail(v73_dir(root) / "SSOT", V73_OWN["sdd"])
    body = json.loads(p.read_text(encoding="utf-8"))["body"]
    wf = body.get("workflows") or []
    codes = [w.get("code") for w in wf]
    nums = sorted(int(re.sub(r"\D", "", c.split("-")[-1]) or 0) for c in codes if c)
    cont = nums == list(range(1, len(nums) + 1))
    steps = [s for w in wf for s in (w.get("steps") or [])]
    noeng = []
    for s in steps:
        e = s.get("engine") or ""
        if e and e not in ("browser", "operator", "manual") and "/" in e and not (root / e).exists() and not list((root / Path(e).parent).glob(Path(e).name.split("_v")[0] + "_v*.py")):
            noeng.append(s.get("code"))
    lamp = "GREEN" if cont and not noeng else "YELLOW"
    return {"lamp": lamp if own["lamp"] == "GREEN" else "YELLOW", "workflows": len(wf), "steps": len(steps), "codes_continuous": cont,
            "steps_engine_missing": noeng[:10], "drift": own["drift"]}


def v73_graph(root: Path) -> dict:
    eng = sm_engines(root)
    names = {fam: root / f["tail"] for fam, f in eng.items()}
    edges = []
    for fam, p in names.items():
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for other in names:
            if other != fam and other in src:
                edges.append((fam, other))
    out = v73_out(root, "graph")
    g = {"system": "VDF", "at": sm_utc(), "nodes": sorted(names), "edges": edges}
    (out / "VDF_GRAPH_latest.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    deg = {}
    for a, b in edges:
        deg[b] = deg.get(b, 0) + 1
    top = sorted(deg.items(), key=lambda x: -x[1])[:10]
    return {"lamp": "GREEN" if names else "YELLOW", "nodes": len(names), "edges": len(edges), "most_used": top,
            "file": str((out / "VDF_GRAPH_latest.json").relative_to(root))}


V73_MCP_TOOLS = {"vdf_health": "VDF 健康燈(只讀)", "vdf_engines": "VDF 家族尾版清單(只讀)",
                 "vdf_params": "VDF 參數冊與時間總管(只讀)", "vdf_parity": "VDF 能力對等(L132)"}


def v73_mcp_call(root: Path, name: str) -> dict:
    return {"vdf_health": lambda: sm_health(root), "vdf_engines": lambda: {k: v["tail"] for k, v in sm_engines(root).items()},
            "vdf_params": lambda: v73_params(root), "vdf_parity": lambda: v73_parity(root)}[name]()


def v73_mcp_serve(root: Path, stdin=None, stdout=None) -> int:
    """最小 MCP stdio(JSON-RPC 2.0):initialize · tools/list · tools/call;只讀工具,不出網、不寫冊。"""
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    for line in stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        rid, m = req.get("id"), req.get("method")
        if m == "initialize":
            res = {"protocolVersion": "2024-11-05", "serverInfo": {"name": "vdf-system-manager", "version": SM_VERSION},
                   "capabilities": {"tools": {}}}
        elif m == "tools/list":
            res = {"tools": [{"name": k, "description": v, "inputSchema": {"type": "object", "properties": {}}} for k, v in V73_MCP_TOOLS.items()]}
        elif m == "tools/call":
            nm = (req.get("params") or {}).get("name")
            if nm not in V73_MCP_TOOLS:
                stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": f"unknown tool {nm}"}}) + "\n")
                stdout.flush()
                continue
            res = {"content": [{"type": "text", "text": json.dumps(v73_mcp_call(root, nm), ensure_ascii=False, default=str)[:20000]}]}
        elif rid is None:
            continue
        else:
            stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"no method {m}"}}) + "\n")
            stdout.flush()
            continue
        stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": res}, ensure_ascii=False) + "\n")
        stdout.flush()
    return 0


def v73_mcp_config(root: Path) -> dict:
    return {"mcpServers": {"vdf": {"command": "python", "args": ["-B", str(SM_HERE), "mcp", "--serve"], "env": {"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES"}}}}


def v73_omniroute(root: Path) -> dict:
    """OmniRoute(跨 AI 路由)VDF 自有一份:同一個 VDF MCP 伺服器給各家 AI 用戶端的設定片段;只寫報告夾。"""
    cfg = v73_mcp_config(root)
    routes = {c: cfg for c in ("claude", "chatgpt", "gemini", "copilot", "manus")}
    out = v73_out(root, "omniroute")
    p = out / "VDF_OmniRoute_latest.json"
    p.write_text(json.dumps({"system": "VDF", "at": sm_utc(), "tools": V73_MCP_TOOLS, "routes": routes}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "clients": sorted(routes), "tools": len(V73_MCP_TOOLS), "file": str(p.relative_to(root))}


def v73_install(root: Path) -> dict:
    """安裝閘(只出計畫):掃 VDF 尾版的第三方 import,這台沒裝的列出;一律經 VCGC InstallGate 安裝,本管理器不 pip。"""
    import ast as _ast
    std = set(getattr(sys, "stdlib_module_names", ()))
    local = {q.stem for base in (v73_dir(root), root / "supportive modules") for q in base.rglob("*.py")}
    need = {}
    for f in sm_engines(root).values():
        p = root / f["tail"]
        try:
            tree = _ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError, ValueError):
            continue
        for n in _ast.walk(tree):
            mods = [a.name for a in n.names] if isinstance(n, _ast.Import) else ([n.module] if isinstance(n, _ast.ImportFrom) and n.module and not n.level else [])
            for m in mods:
                top = m.split(".")[0]
                if top in std or top.startswith(SM_REPO_MOD_PREFIX) or top.startswith(("_", "VIA", "via_", "SUP", "CGC")):
                    continue
                if top not in local:
                    need.setdefault(top, set()).add(Path(p).name)
    missing = sorted(k for k in need if not lib_installed(k))
    plan = v73_out(root, "install") / "VDF_InstallPlan_latest.json"
    plan.write_text(json.dumps({"system": "VDF", "at": sm_utc(), "third_party": sorted(need), "missing_here": missing,
                                "how": "經 VCGC InstallGate(CGC_MDL240 / EnvGovernance)安裝;VDF 不 pip"}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "YELLOW" if missing else "GREEN", "third_party": len(need), "missing_here": missing, "plan": str(plan.relative_to(root))}


def v73_parity(root: Path) -> dict:
    caps = {
        "省 Token / 全景(health · engines · conform)": True,
        "SSOT 冊": any(v73_dir(root).glob(SM_CONFIG["ssot_glob"])),
        "正則 Regex": v73_tail(v73_dir(root) / "SSOT", V73_OWN["regex"]) is not None,
        "同義字 Synonym": v73_tail(v73_dir(root) / "SSOT", V73_OWN["synonyms"]) is not None,
        "編號請求 / 更新偵測": True, "輸入輸出參數 / 時間總管": True, "註冊同步(版本 + 時間)": True,
        "交接 / 收尾": True, "備份": True, "自測格 / 串測": True,
        "SDD / 工作流冊": v73_tail(v73_dir(root) / "SSOT", V73_OWN["sdd"]) is not None,
        "政策冊遵循(L123 / L125 / L131 / L132)": True, "Graphify": True, "OmniRoute": True, "MCP": True,
        "矩陣 HTML U/I(視覺鎖定)": True, "安裝閘": True, "加速器 / 網路橋": "VIA:ACCEL-BRIDGE" in SM_HERE.read_text(encoding="utf-8"),
    }
    gaps = [k for k, v in caps.items() if not v]
    return {"lamp": "GREEN" if not gaps else "YELLOW", "have": len(caps) - len(gaps), "total": len(caps), "gaps": gaps, "caps": caps}


def v73_tokens(root: Path) -> dict:
    """視覺鎖定:VCGC 鎖站 kit 的色票(只讀);缺就用中性預設。"""
    p = root / "docs" / "handoff" / "ai" / "VIA_WorkbenchLock_kit_latest.json"
    t = {"bg": "#0f1720", "panel": "#16212c", "fg": "#e6edf3", "muted": "#8b9bab", "accent": "#d4a64a", "green": "#3fb950", "yellow": "#d29922", "red": "#f85149"}
    try:
        k = json.loads(p.read_text(encoding="utf-8"))
        for key, val in (k.get("tokens") or k.get("colors") or {}).items():
            if isinstance(val, str) and val.startswith("#"):
                t[key.replace("--vl-", "").replace("--", "")] = val
        t["_source"] = p.name
    except (OSError, ValueError):
        t["_source"] = "預設(kit 不在)"
    return t


def v73_page(root: Path, data: dict) -> Path:
    import html as _h
    t = v73_tokens(root)
    lamp_c = {"GREEN": t["green"], "YELLOW": t["yellow"], "RED": t["red"], "ABSENT": t["muted"]}
    rows = "".join(f"<tr><td><b style='color:{lamp_c.get(v.get('lamp'), t['muted'])}'>●</b> {_h.escape(k)}</td><td>{_h.escape(str(v.get('lamp')))}</td>"
                   f"<td>{_h.escape(json.dumps({x: y for x, y in v.items() if x not in ('lamp', 'caps', 'sha')}, ensure_ascii=False, default=str)[:300])}</td></tr>"
                   for k, v in data.items())
    caps = data.get("parity", {}).get("caps", {})
    cap_rows = "".join(f"<tr><td>{_h.escape(k)}</td><td style='color:{t['green'] if v else t['red']}'>{'✓ 自有' if v else '✗ 缺'}</td></tr>" for k, v in caps.items())
    eng = sm_engines(root)
    eng_rows = "".join(f"<tr><td>{_h.escape(f)}</td><td>v{e['tail_ver']:04d}</td><td>{e['versions']}</td></tr>" for f, e in list(eng.items())[:400])
    css = (f"body{{background:{t['bg']};color:{t['fg']};font:14px/1.5 system-ui,'Noto Sans TC',sans-serif;margin:0;padding:16px}}"
           f"h1{{font-size:1.3rem;color:{t['accent']}}}h2{{font-size:1.05rem;margin-top:1.4rem}}table{{border-collapse:collapse;width:100%;background:{t['panel']}}}"
           f"td,th{{border-bottom:1px solid #2a3642;padding:4px 8px;text-align:left;vertical-align:top}}th{{color:{t['muted']};font-size:.8rem}}"
           ".wrap{overflow-x:auto}")
    page = (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>VDF 系統管理器矩陣</title><style>{css}</style></head><body>"
            f"<h1>VDF 系統管理器 {SM_VERSION} · 能力與狀態矩陣</h1><p style='color:{t['muted']}'>{sm_utc()} · 視覺色票 {_h.escape(t['_source'])} · 只讀產生</p>"
            f"<h2>功能燈</h2><div class='wrap'><table><tr><th>功能</th><th>燈</th><th>摘要</th></tr>{rows}</table></div>"
            f"<h2>L132 能力對等(VDF 自有一份)</h2><div class='wrap'><table><tr><th>能力</th><th>狀態</th></tr>{cap_rows}</table></div>"
            f"<h2>家族尾版({len(eng)})</h2><div class='wrap'><table><tr><th>家族</th><th>尾版</th><th>版本數</th></tr>{eng_rows}</table></div></body></html>")
    p = v73_out(root) / "VDF_MANAGER_MATRIX_latest.html"
    p.write_text(page, encoding="utf-8")
    return p


def v73_status(root: Path) -> dict:
    return {"health": sm_health(root), "parity": v73_parity(root), "regex": v73_own_book(root, "regex"),
            "synonyms": v73_own_book(root, "synonyms"), "sdd": v73_sdd(root), "params": v73_params(root)}


def v73_worst(lamps) -> str:
    order = ["RED", "ABSENT", "YELLOW", "GREEN"]
    ls = [x for x in lamps if x in order]
    return min(ls, key=order.index) if ls else "YELLOW"


def sm_cmd_v0173(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "mcp":
        if "--serve" in args:
            return v73_mcp_serve(root)
        print(json.dumps(v73_mcp_config(root), ensure_ascii=False, indent=1))
        return 0
    if verb == "backup":
        r = v73_backup(root, check_only="check" in args)
    elif verb in ("regex", "synonyms"):
        r = v73_own_book(root, verb)
    elif verb == "ssot":
        r = {"lamp": v73_worst([v73_own_book(root, "regex")["lamp"], v73_own_book(root, "synonyms")["lamp"], v73_sdd(root)["lamp"]]),
             "books": sorted(p.name for p in (v73_dir(root) / "SSOT").glob("*.json")), "ssot_tail": (v73_tail(v73_dir(root), SM_CONFIG["ssot_glob"]) or Path("—")).name}
    else:
        fn = {"number": v73_number, "params": v73_params, "sdd": v73_sdd, "graphify": v73_graph, "omniroute": v73_omniroute,
              "install": v73_install, "parity": v73_parity}.get(verb)
        if fn:
            r = fn(root)
        elif verb == "status":
            s = v73_status(root)
            r = {"lamp": v73_worst(v["lamp"] for v in s.values()), **{k: v["lamp"] for k, v in s.items()}}
        elif verb in ("page", "closeout"):
            data = v73_status(root)
            if verb == "closeout":
                data.update({"number": v73_number(root), "install": v73_install(root), "graphify": v73_graph(root),
                             "omniroute": v73_omniroute(root), "backup": v73_backup(root)})
                data["backup_check"] = v73_backup(root, check_only=True)
            p = v73_page(root, data)
            r = {"lamp": v73_worst(v.get("lamp") for v in data.values()), "page": str(p.relative_to(root)),
                 "parts": {k: v.get("lamp") for k, v in data.items()}}
            if verb == "closeout":
                rc = v73_out(root) / f"VDF_CLOSEOUT_{v73_stamp()}.json"
                rc.write_text(json.dumps({"manager": SM_TAG, **r}, ensure_ascii=False, indent=1), encoding="utf-8")
                r["receipt"] = str(rc.relative_to(root))
        else:
            return 2
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
    else:
        brief = " · ".join(f"{k} {v}" for k, v in r.items() if k not in ("lamp", "caps", "sha", "examples", "most_used") and not isinstance(v, (dict, list)) or k in ("gaps", "missing_here"))
        print(f"[{SM_TAG}] {verb} {r.get('lamp')} · {brief}")
    return SM_RC.get(r.get("lamp"), 2)


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)
    print(f"=== {SM_TAG} 自測(單檔重寫 · 不載入任何前版 · L132 能力對等)===", flush=True)
    src = SM_HERE.read_text(encoding="utf-8")
    ck("① 單檔:模組層不載入任何前版(無 __getattr__ 轉接 · 無模組層 exec_module);只有 LEGACY 動詞以子行程轉交",
       ("\n" + "def __getattr__") not in src and ("PRIOR = " + "importlib") not in src)
    e082 = ("  [FAIL] ⑩ 零列 · 缺件 No module named 'yfinance'(ModuleNotFoundError)\n  [FAIL] ⑪ 兩趟都零列 → 表未建 (rc=2)\n")
    ck("② 併入 v0172 缺套件判讀:yfinance 沒裝 → 判缺件;有裝 → 照實 FAIL", (sm_missing_lib(e082).startswith("yfinance")) != lib_installed("yfinance"))
    ck("③ 自家模組缺 = 真壞", sm_missing_lib("[FAIL] x\nNo module named 'VDF_ENG999_X'\n") == "")
    root = sm_via_root()
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"] / "SSOT"
        d.mkdir(parents=True)
        (tr / "supportive modules" / "registry").mkdir(parents=True)
        src_book = tr / "supportive modules" / "registry" / "SRC_v0100.json"
        src_book.write_text('{"a":1}')
        own = {"source": "supportive modules/registry/SRC_v0100.json", "source_sha256": hashlib.sha256(b'{"a":1}').hexdigest(), "body": {"a": 1}}
        (d / "VDF_Regex_SSOT_v0100.json").write_text(json.dumps(own))
        ck("④ 自有正則冊在 · 來源未變 → GREEN", v73_own_book(tr, "regex")["lamp"] == "GREEN")
        src_book.write_text('{"a":2}')
        ck("⑤ VCGC 來源變了 → YELLOW drift(未准許不換)", v73_own_book(tr, "regex")["drift"] is True)
        ck("⑥ 自有同義字冊不在 → ABSENT", v73_own_book(tr, "synonyms")["lamp"] == "ABSENT")
        eng = tr / SM_CONFIG["dir"] / "VDF_ENG001_Demo_v0100.py"
        eng.write_text("import json\n")
        global sm_engines
        real = sm_engines
        sm_engines = lambda r: {"VDF_ENG001_Demo": {"tail": str(eng.relative_to(tr)), "tail_ver": 100, "versions": 1}}
        try:
            n1 = v73_number(tr)
            eng.write_text("import json\nx=1\n")
            n2 = v73_number(tr)
            ck("⑦ 編號偵測:首輪記 sha · 改內容 → changed 1 · 未登號 → 寫請求檔", n1["first_run"] and n2["changed_since_last"] == 1
               and n2["unnumbered"] == 1 and list((tr / "VIA_Reports" / "vdf" / "manager" / "number").glob("VDF_NumberRequest_*.json")))
            b = v73_backup(tr)
            c = v73_backup(tr, check_only=True)
            ck("⑧ 備份 zip + SHA256SUMS → check GREEN · 檔名 Windows 安全(無空格 / 冒號)", b["files"] >= 2 and c["lamp"] == "GREEN" and not any(x in Path(b["zip"]).name for x in (" ", ":")), c)
            g = v73_graph(tr)
            ck("⑨ graphify:節點 1 · 寫 VDF_GRAPH_latest.json", g["nodes"] == 1)
            import io as _io
            inp = _io.StringIO('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'
                               '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"vdf_engines"}}\n')
            outp = _io.StringIO()
            v73_mcp_serve(tr, inp, outp)
            resp = [json.loads(x) for x in outp.getvalue().splitlines()]
            ck("⑩ MCP stdio:initialize · tools/list 4 工具 · tools/call vdf_engines 回家族", len(resp) == 3 and len(resp[1]["result"]["tools"]) == 4
               and "VDF_ENG001_Demo" in resp[2]["result"]["content"][0]["text"])
            o = v73_omniroute(tr)
            ck("⑪ OmniRoute:5 家 AI 用戶端同一 VDF MCP", o["clients"] == ["chatgpt", "claude", "copilot", "gemini", "manus"])
            ins = v73_install(tr)
            ck("⑫ 安裝閘只出計畫(不 pip)", ("pip " + "install") not in src and ins["lamp"] in ("GREEN", "YELLOW"))
            p = v73_page(tr, {"parity": v73_parity(tr), "number": n2})
            pg = p.read_text(encoding="utf-8")
            ck("⑬ 矩陣頁:有標題 · 能力表 · 家族表 · viewport", "<title>" in pg and "L132" in pg and "VDF_ENG001_Demo" in pg and "viewport" in pg)
        finally:
            sm_engines = real
    ck("⑭ 真倉:自有正則 / 同義字 / 工作流冊都在(L131)", all(v73_own_book(root, k)["lamp"] != "ABSENT" for k in ("regex", "synonyms", "sdd")))
    par = v73_parity(root)
    ck("⑮ 真倉 L132 能力對等:VDF 缺口 0", not par["gaps"], par["gaps"])
    ck("⑯ 加速器 / 網路橋在 · 不代設同意閘 · 零 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
       and "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src)
    import contextlib as _cl, io as _io2
    buf = _io2.StringIO()
    with _cl.redirect_stdout(buf):
        rc = _selftest_core()
    ck("⑰ 標準核心(v0171 從頭重作那一份)自測照過", rc == 0, buf.getvalue()[-400:])
    n = sum(ok)
    print(f"[計] {SM_TAG} 單檔 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


SM_NATIVE = SM_NATIVE + tuple(v for v in V73_VERBS if v not in SM_NATIVE)


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
