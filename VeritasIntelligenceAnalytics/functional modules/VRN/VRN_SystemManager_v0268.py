#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0268 — 全動詞原生(v0267 + status · catalog · links · read · sync · launch · bridges · tools 改原生;conflict 的寫死本機路徑改報 YELLOW 附總數;不再轉交前版)。

(以下 v0267 說明)VRN_SystemManager v0267 — 單檔(操作員 2026-11-13「不適合的引擎重寫不要用舊的」· L132):以 v0265 標準核心為底 + 併入 v0266 缺套件判讀 + VRN 自有一份 VCGC 能力(parity · backup · graphify · omniroute · mcp · conflict 鏡像衝突檢視 · page · closeout);模組層不載入任何前版。

(以下為 v0265 標準核心原說明)

操作員令(2026-11-11):「確認三個獨立系統三個 main() 三個 system manager · 補齊基本功能 · 更健全 · 遵守更新後獨立系統規範 ·
沒有誰管誰 · 主導全修正全在我跟 AI · 不符合就從頭規劃標準 system manager 重作」。
實測缺口(2026-11-11):v0264 實測(容器 2026-11-13 全量 74 支):8 支缺 fitz 直接 import 崩潰 rc 1 被記成失敗 → 本版依 L16 判 ABSENT 並寫明缺哪個套件(自家模組缺仍算壞);v0263 實測(容器 2026-11-12):test 把引擎 rc 2(缺件 fitz 等 · L16 ≠ 壞)記成失敗 → 13 支誤紅;本版依 L16 分 PASS / NODATA / ABSENT / GATED / FAIL
本版是 VRN 自己的入口(L120 / L123):
  · 標準動詞本版自己做:help · version · health · engines · records · peers · conform · selftest(本系統另做 test(逐支尾版 --selftest))。
  · 其餘動詞(前版鏈全部功能)一律以子行程原樣轉交前版 VRN_SystemManager_v0264(參數 · 環境 · rc 不變)—— 只增不減,不可丟失。
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

SM_CONFIG = {'system': 'VRN',
 'manager_family': 'VRN_SystemManager',
 'dir': 'functional modules/VRN',
 'own_prefixes': ['VRN2_', 'VRN_'],
 'reports': ['VIA_Reports/vrn2'],
 'ssot_glob': 'ssot/*.json',
 'forward_verbs': ['status'],
 'native_extra': ['test'],
 'peer_gate_flags': ['VIA_FROM_VCGC'],
 'own_entry_flag': None,
 'report_env': [],
 'custom_health': [{'name': 'integration_book', 'glob': 'functional modules/VRN/ssot/VRN2_IntegrationBook_v*.json'},
                   {'name': 'peer_bridge', 'glob': 'functional modules/VRN/VRN2_PeerBridge_v*.py'},
                   {'name': 'integration_gap_zero',
                    'glob': 'functional modules/VRN/ssot/VRN2_IntegrationBook_v*.json',
                    'json_path': 'counts.GAP',
                    'equals': 0},
                   {'name': 'release_launcher',
                    'glob': 'docs/handoff/ai/vrn2_release_v*/ActivateVRN-2_v*.zip',
                    'required': False}],
 'peers': {'VCGC': {'manager_family': 'CGC_MDL149_VeritasCentralGovernanceConsole',
                    'dir': 'supportive modules/registry',
                    'own_prefixes': ['CGC_'],
                    'reports': ['VIA_Reports/vcgc']},
           'VDF': {'manager_family': 'VDF_SystemManager',
                   'dir': 'functional modules/VDF',
                   'own_prefixes': ['VDF_'],
                   'reports': ['VIA_Reports/vdf_fetch', 'VIA_Reports/vdf']}}}
SM_VERSION = "v0268"
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
    if verb in V267_VERBS:
        return sm_cmd_v0267(verb, args, root)
    if verb in V268_VERBS:
        return sm_cmd_v0268(verb, args, root)
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
        ck("單檔(L132 ④):不再經 __getattr__ 轉接前版公開名稱", tail_api == "NO_FORWARD", tail_api)
        ck("P5 實測:跑完標準動詞,對等系統的樹一字未動", before == peer_sig())
    sc = sm_static_checks(SM_HERE)
    ck("本檔靜態:P1 main · P3 無他系統放行旗標 · P4 無跨系統載入 · P7 橋 · P8", all(sc.values()), [k for k, v in sc.items() if not v])
    print(f"[計] {SM_TAG} 自測 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1



# ══════════════════════════ v0267:VRN 單檔 · L132 能力對等(VRN 自有一份;不載入任何前版)══════════════════════════
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


def v73_stamp() -> str:
    """檔名用時間戳(Windows 安全:無空格 · 無冒號)。"""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def v73_dir(root: Path) -> Path:
    return root / SM_CONFIG["dir"]


def v73_out(root: Path, *sub) -> Path:
    p = root / "VIA_Reports" / "vrn2" / "manager"
    for s in sub:
        p = p / s
    p.mkdir(parents=True, exist_ok=True)
    return p


def v73_tail(folder: Path, pattern: str):
    hits = sorted(folder.glob(pattern), key=sm_vnum)
    return hits[-1] if hits else None


def v73_backup(root: Path, check_only: bool = False) -> dict:
    out = v73_out(root, "backup")
    if check_only:
        zips = sorted(out.glob("VRN_Backup_*.zip"))
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
    files = [p for p in (d / "ssot").glob("*.json")] + [p for p in d.glob("*.json")] + [SM_HERE]
    files += [root / f["tail"] for f in sm_engines(root).values() if (root / f["tail"]).is_file()]
    files = sorted(set(files))
    zp = out / f"VRN_Backup_{v73_stamp()}.zip"
    lines = []
    with _zipfile.ZipFile(zp, "w", _zipfile.ZIP_DEFLATED) as z:
        for p in files:
            rel = str(p.relative_to(root)) if p.is_relative_to(root) else "_manager/" + p.name
            b = p.read_bytes()
            z.writestr(rel, b)
            lines.append(f"{hashlib.sha256(b).hexdigest()}  {rel}")
        z.writestr("SHA256SUMS", "\n".join(lines) + "\n")
        z.writestr("MANIFEST.json", json.dumps({"system": "VRN", "at": sm_utc(), "manager": SM_TAG, "files": len(files)}, ensure_ascii=False))
    return {"lamp": "GREEN", "zip": str(zp.relative_to(root)), "files": len(files), "bytes": zp.stat().st_size}


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
    g = {"system": "VRN", "at": sm_utc(), "nodes": sorted(names), "edges": edges}
    (out / "VRN_GRAPH_latest.json").write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    deg = {}
    for a, b in edges:
        deg[b] = deg.get(b, 0) + 1
    top = sorted(deg.items(), key=lambda x: -x[1])[:10]
    return {"lamp": "GREEN" if names else "YELLOW", "nodes": len(names), "edges": len(edges), "most_used": top,
            "file": str((out / "VRN_GRAPH_latest.json").relative_to(root))}


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
            res = {"protocolVersion": "2024-11-05", "serverInfo": {"name": "vrn-system-manager", "version": SM_VERSION},
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
    return {"mcpServers": {"vrn": {"command": "python", "args": ["-B", str(SM_HERE), "mcp", "--serve"], "env": {"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES"}}}}


def v73_omniroute(root: Path) -> dict:
    """OmniRoute(跨 AI 路由)VRN 自有一份:同一個 VRN MCP 伺服器給各家 AI 用戶端的設定片段;只寫報告夾。"""
    cfg = v73_mcp_config(root)
    routes = {c: cfg for c in ("claude", "chatgpt", "gemini", "copilot", "manus")}
    out = v73_out(root, "omniroute")
    p = out / "VRN_OmniRoute_latest.json"
    p.write_text(json.dumps({"system": "VRN", "at": sm_utc(), "tools": V73_MCP_TOOLS, "routes": routes}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "GREEN", "clients": sorted(routes), "tools": len(V73_MCP_TOOLS), "file": str(p.relative_to(root))}


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
            f"<title>VRN 系統管理器矩陣</title><style>{css}</style></head><body>"
            f"<h1>VRN 系統管理器 {SM_VERSION} · 能力與狀態矩陣</h1><p style='color:{t['muted']}'>{sm_utc()} · 視覺色票 {_h.escape(t['_source'])} · 只讀產生</p>"
            f"<h2>功能燈</h2><div class='wrap'><table><tr><th>功能</th><th>燈</th><th>摘要</th></tr>{rows}</table></div>"
            f"<h2>L132 能力對等(VRN 自有一份)</h2><div class='wrap'><table><tr><th>能力</th><th>狀態</th></tr>{cap_rows}</table></div>"
            f"<h2>家族尾版({len(eng)})</h2><div class='wrap'><table><tr><th>家族</th><th>尾版</th><th>版本數</th></tr>{eng_rows}</table></div></body></html>")
    p = v73_out(root) / "VRN_MANAGER_MATRIX_latest.html"
    p.write_text(page, encoding="utf-8")
    return p


def v73_worst(lamps) -> str:
    order = ["RED", "ABSENT", "YELLOW", "GREEN"]
    ls = [x for x in lamps if x in order]
    return min(ls, key=order.index) if ls else "YELLOW"


def v74_conflict(root: Path) -> dict:
    """鏡像衝突檢視(VRN 自有一份 · 同 VCGC 衝突閘三道):① 衝突哨兵 ② GitHub 對齊 ③ 子系統邊界;只讀。"""
    d = v73_dir(root)
    # ① 衝突哨兵:同名不同內容 · 0-byte 佔位 · 寫死絕對路徑(R2 同規)
    seen, dup, zero, abspath = {}, [], [], []
    skip = ("references", "intake", "_superseded", "output_hub", "__pycache__", "retired")
    for q in d.rglob("*.py"):
        if any(x in q.parts for x in skip) or any(re.fullmatch(r"\d{8}", x) for x in q.parts):   # 日期夾 = 凍結快照
            continue
        if q.stat().st_size == 0:
            zero.append(str(q.relative_to(root)))
            continue
        h = hashlib.sha256(q.read_bytes()).hexdigest()
        if q.name in seen and seen[q.name][1] != h:
            dup.append(f"{q.name}:{seen[q.name][0]} ≠ {q.relative_to(root)}")
        seen.setdefault(q.name, (str(q.relative_to(root)), h))
    for f in sm_engines(root).values():
        if (root / f["tail"]).resolve() == SM_HERE:
            continue
        try:
            body = re.sub(r"(?s)\"\"\".*?\"\"\"|#[^\n]*", "", (root / f["tail"]).read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        if V74_ABS_PATH.search(body):
            abspath.append(Path(f["tail"]).name)
    sentinel = {"lamp": "YELLOW" if (abspath or zero or dup) else "GREEN", "same_name_diff": dup[:10], "zero_byte": zero[:10], "abs_path": abspath[:10], "abs_path_n": len(abspath),
                "abs_path_note": "寫死本機路徑全倉皆有(操作員決定統一換法前照實列 YELLOW)"}
    # ② GitHub 對齊:分支對上游 ahead/behind(本機已知 ref,不連網)· VRN 夾未提交
    def git(*a):
        r = subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    rc, ab = git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    ahead, behind = (ab.split() + ["?", "?"])[:2] if rc == 0 else ("?", "?")
    _, dirty = git("status", "--porcelain", "--", SM_CONFIG["dir"])
    dirty_n = len([x for x in dirty.splitlines() if x.strip()])
    gh_lamp = "GREEN" if rc == 0 and behind == "0" and dirty_n == 0 else ("YELLOW" if rc == 0 else "YELLOW")
    github = {"lamp": gh_lamp, "ahead": ahead, "behind": behind, "vrn_uncommitted": dirty_n, "upstream": rc == 0}
    # ③ 子系統邊界:VRN 尾版不得載入他系統程式(加速器 / 網路橋 = 共用支援工具,不算)
    cross = []
    for f in sm_engines(root).values():
        if (root / f["tail"]).resolve() == SM_HERE:      # 管理器只讀監控對等系統(L123)= 合法,不算越界
            continue
        try:
            src = (root / f["tail"]).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        body = re.sub(r"(?s)\"\"\".*?\"\"\"|#[^\n]*", "", src)
        if V74_OTHER_SYS.search(body):
            cross.append(Path(f["tail"]).name)
    boundary = {"lamp": "RED" if cross else "GREEN", "cross_system": cross[:20]}
    parts = {"sentinel": sentinel, "github": github, "boundary": boundary}
    return {"lamp": v73_worst(v["lamp"] for v in parts.values()), **{k: v["lamp"] for k, v in parts.items()}, "detail": parts}



V74_OTHER_SYS = re.compile(r"(?:import|from)\s+(VDF|VQG|VAP|CGC)_\w+|spec_from_file_location\([^)]*['\"](?:VDF|VQG|VAP|CGC)_\w+|functional modules/(?:VDF|VQG|VAP)/\w+\.py|['\"]VDF_SystemManager|['\"]VQG_AllInOne|['\"]VAP_SystemManager")
V74_ABS_PATH = re.compile(r"[A-Za-z]:\\\\Users\\\\|C:/Users/|/home/[a-z]+/|/Users/[A-Za-z]")
V267_VERBS = ("parity", "backup", "graphify", "omniroute", "mcp", "conflict", "page", "closeout", "install")
V73_MCP_TOOLS = {"vrn_health": "VRN 健康燈(只讀)", "vrn_engines": "VRN 家族尾版清單(只讀)", "vrn_parity": "VRN 能力對等(L132)", "vrn_conflict": "VRN 鏡像衝突檢視(只讀)"}


def v73_mcp_call(root: Path, name: str) -> dict:
    return {"vrn_health": lambda: sm_health(root), "vrn_engines": lambda: {k: v["tail"] for k, v in sm_engines(root).items()},
            "vrn_parity": lambda: v73_parity(root), "vrn_conflict": lambda: v74_conflict(root)}[name]()


def v73_parity(root: Path) -> dict:
    d = v73_dir(root)
    names = [p.name for p in d.rglob("*") if p.is_file() and not any(x in p.parts for x in ("intake", "references", "_superseded", "__pycache__"))]
    has = lambda rx: any(re.search(rx, n) for n in names)
    caps = {"省 Token / 全景(health · engines · conform)": True, "SSOT 冊": any((root / SM_CONFIG["dir"]).glob(SM_CONFIG["ssot_glob"])),
            "正則 Regex": has(r"Regex"), "同義字 Synonym": has(r"Synonym|Lexicon"), "編號請求 / 更新偵測": has(r"SSOTSync|Number"),
            "輸入輸出參數 / 時間總管": has(r"Param|AsOf|Calendar"), "註冊同步(版本 + 時間)": has(r"Regist|Inventory"),
            "交接 / 收尾(closeout 動詞)": True, "備份": True, "自測格 / 串測": True, "SDD / 工作流冊": has(r"SDD|Workflow"),
            "政策冊遵循(L123 / L125 / L131 / L132)": True, "Graphify": True, "OmniRoute": True, "MCP": True, "矩陣 HTML U/I(視覺鎖定)": True,
            "安裝閘(install 動詞 · 只出計畫)": True, "加速器 / 網路橋": "VIA:ACCEL-BRIDGE" in SM_HERE.read_text(encoding="utf-8"),
            "鏡像衝突檢視(哨兵 · GitHub 對齊 · 子系統邊界)": True}
    gaps = [k for k, v in caps.items() if not v]
    return {"lamp": "GREEN" if not gaps else "YELLOW", "have": len(caps) - len(gaps), "total": len(caps), "gaps": gaps, "caps": caps}


def v73_install(root: Path) -> dict:
    """安裝閘(只出計畫):掃 VRN 尾版的第三方 import,這台沒裝的列出;一律經 VCGC InstallGate 安裝,本管理器不裝。"""
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
    plan = v73_out(root, "install") / "VRN_InstallPlan_latest.json"
    plan.write_text(json.dumps({"system": "VRN", "at": sm_utc(), "third_party": sorted(need), "missing_here": missing,
                                "how": "經 VCGC InstallGate(CGC_MDL240 / EnvGovernance)安裝;VRN 不 pip"}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"lamp": "YELLOW" if missing else "GREEN", "third_party": len(need), "missing_here": missing, "plan": str(plan.relative_to(root))}


def sm_cmd_v0267(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "mcp":
        if "--serve" in args:
            return v73_mcp_serve(root)
        print(json.dumps(v73_mcp_config(root), ensure_ascii=False, indent=1))
        return 0
    if verb == "backup":
        r = v73_backup(root, check_only="check" in args)
    elif verb in ("page", "closeout"):
        data = {"health": sm_health(root), "parity": v73_parity(root), "conflict": v74_conflict(root)}
        if verb == "closeout":
            data.update({"graphify": v73_graph(root), "omniroute": v73_omniroute(root), "install": v73_install(root), "backup": v73_backup(root)})
            data["backup_check"] = v73_backup(root, check_only=True)
        p = v73_page(root, data)
        r = {"lamp": v73_worst(v.get("lamp") for v in data.values()), "page": str(p.relative_to(root)), "parts": {k: v.get("lamp") for k, v in data.items()}}
        if verb == "closeout":
            rc = v73_out(root) / f"VRN_CLOSEOUT_{v73_stamp()}.json"
            rc.write_text(json.dumps({"manager": SM_TAG, **r}, ensure_ascii=False, indent=1), encoding="utf-8")
            r["receipt"] = str(rc.relative_to(root))
    else:
        r = {"parity": v73_parity, "graphify": v73_graph, "omniroute": v73_omniroute, "conflict": v74_conflict, "install": v73_install}[verb](root)
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
    else:
        brief = " · ".join(f"{k} {v}" for k, v in r.items() if k not in ("lamp", "caps", "detail") and (not isinstance(v, (dict, list)) or k in ("gaps", "parts")))
        print(f"[{SM_TAG}] {verb} {r.get('lamp')} · {brief[:500]}")
    return SM_RC.get(r.get("lamp"), 2)


def _selftest_v0267() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)
    print(f"=== {SM_TAG} 自測(單檔 · 不載入任何前版 · L132 能力對等)===", flush=True)
    src = SM_HERE.read_text(encoding="utf-8")
    ck("① 單檔:無 __getattr__ 轉接 · 無模組層前版載入", ("\n" + "def __getattr__") not in src and ("PRIOR = " + "importlib") not in src)
    e = "  [FAIL] pymupdf 道(ModuleNotFoundError)\n主標題:PyMuPDF 不在\n"
    ck("② 併入 v0266 缺套件判讀:PyMuPDF 沒裝 → 判缺件;有裝 → 照實 FAIL", (sm_missing_lib(e).startswith("fitz")) != lib_installed("fitz"))
    ck("③ 自家模組缺 = 真壞", sm_missing_lib("[FAIL] x\nNo module named 'VRN_ENG999_X'\n") == "")
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"]
        (d / "ssot").mkdir(parents=True)
        eng = d / "VRN_ENG001_Demo_v0100.py"
        eng.write_text("import json\n")
        global sm_engines
        real = sm_engines
        sm_engines = lambda r: {"VRN_ENG001_Demo": {"tail": str(eng.relative_to(tr)), "tail_ver": 100, "versions": 1}}
        try:
            b = v73_backup(tr)
            c = v73_backup(tr, check_only=True)
            ck("④ 備份 zip + SHA256SUMS → check GREEN · 檔名 Windows 安全", c["lamp"] == "GREEN" and not any(x in Path(b["zip"]).name for x in (" ", ":")), c)
            ck("⑤ graphify:節點 1", v73_graph(tr)["nodes"] == 1)
            import io as _io
            outp = _io.StringIO()
            v73_mcp_serve(tr, _io.StringIO('{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"vrn_engines"}}\n'), outp)
            resp = [json.loads(x) for x in outp.getvalue().splitlines()]
            ck("⑥ MCP stdio:tools/list 4 個 vrn_ 工具 · tools/call 回家族", len(resp[0]["result"]["tools"]) == 4 and "VRN_ENG001_Demo" in resp[1]["result"]["content"][0]["text"])
            ck("⑦ OmniRoute:5 家 AI 用戶端同一 VRN MCP", v73_omniroute(tr)["clients"] == ["chatgpt", "claude", "copilot", "gemini", "manus"])
            eng.write_text("import VDF_ENG001_X\n")
            ck("⑧ 鏡像衝突:VRN 程式載入 VDF 模組 → 子系統邊界 RED", v74_conflict(tr)["boundary"] == "RED")
        finally:
            sm_engines = real
    root = sm_via_root()
    par = v73_parity(root)
    ck("⑨ 真倉 L132 能力對等:VRN 缺口 0", not par["gaps"], par["gaps"])
    ck("⑩ 加速器 / 網路橋在 · 不代設同意閘 · 零 TA-Lib · 不 pip", "VIA:ACCEL-BRIDGE" in src and "environ[\"VIA_NET" + "_CONSENT\"] =" not in src
       and "import " + "talib" not in src and ("pip " + "install") not in src)
    import contextlib as _cl, io as _io2
    buf = _io2.StringIO()
    with _cl.redirect_stdout(buf):
        rc = _selftest_core()
    ck("⑪ 標準核心(v0265 從頭重作那一份)自測照過", rc == 0, buf.getvalue()[-400:])
    n = sum(ok)
    print(f"[計] {SM_TAG} 單檔 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


SM_NATIVE = SM_NATIVE + tuple(v for v in V267_VERBS if v not in SM_NATIVE)


# ══════════════════════════ v0268:VRN 剩下動詞全改原生(status · catalog · links · read · sync · launch · bridges · tools)══════════════════════════
V74_PATH_RX = re.compile(r"[\w ./\-]+?\.(?:py|json|jsonl|ps1)$")
V74_NET_CALL = re.compile(r"urllib\.request\.urlopen|\burlopen\(|\brequests\.(get|post|Session)\(|\bhttpx\.(get|post|Client)\(|\byf\.download\(|\byfinance\.(download|Ticker)\(")


def v74_books(root: Path) -> list:
    d = v73_dir(root)
    fams = {}
    for p in list(d.glob("*.json")) + list((d / "ssot").glob("*.json")) + list((d / "registry").glob("*.json")):
        m = re.match(r"^(.+)_v(\d{4})\.json$", p.name)
        key = (str(p.parent), m.group(1)) if m else (str(p.parent), p.stem)
        if key not in fams or sm_vnum(p) > sm_vnum(fams[key]):
            fams[key] = p
    return sorted(fams.values(), key=lambda p: p.name)


def v74_resolve(root: Path, s: str) -> bool:
    s = s.strip().replace("\\", "/")
    if not s or s.startswith(("http:", "https:")):
        return True
    for base in (root, v73_dir(root), v73_dir(root) / "engine", v73_dir(root) / "ssot"):
        if (base / s).exists():
            return True
    name = Path(s).name
    m = re.match(r"^(.+)_v\d{4}(\.\w+)$", name)
    pat = (m.group(1) + "_v*" + m.group(2)) if m else name
    return any(v73_dir(root).rglob(pat)) or any((root / "supportive modules").glob(pat))


def v74_links(root: Path) -> dict:
    cnt, missing = {"GREEN": 0, "MISSING": 0}, []
    for p in v74_books(root):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        stack = [data]
        while stack:
            x = stack.pop()
            if isinstance(x, dict):
                stack.extend(x.values())
            elif isinstance(x, list):
                stack.extend(x)
            elif isinstance(x, str) and len(x) < 260 and V74_PATH_RX.fullmatch(x.strip()) and (x.startswith(("functional modules/", "supportive modules/", "docs/")) or Path(x).name.startswith(("VRN_", "VRN2_", "VIA_", "CGC_", "SUP_"))):
                if "*" in x or "<" in x:
                    continue
                if v74_resolve(root, x):
                    cnt["GREEN"] += 1
                else:
                    cnt["MISSING"] += 1
                    missing.append(f"{p.name} → {x}")
    lamp = "GREEN" if not cnt["MISSING"] else "YELLOW"
    return {"lamp": lamp, "links": sum(cnt.values()), "counts": cnt, "missing": sorted(set(missing))[:30], "books": len(v74_books(root))}


def v74_bridges(root: Path) -> dict:
    acc, net_need, net_have, miss_a, miss_n = 0, 0, 0, [], []
    eng = sm_engines(root)
    for fam, f in eng.items():
        p = root / f["tail"]
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "VIA:ACCEL-BRIDGE" in src:
            acc += 1
        else:
            miss_a.append(p.name)
        body = re.sub(r"(?s)\"\"\".*?\"\"\"|'''.*?'''|#[^\n]*", "", src)
        if V74_NET_CALL.search(body):
            net_need += 1
            if "VIA:NET-BRIDGE" in src:
                net_have += 1
            else:
                miss_n.append(p.name)
    n = len(eng)
    exempt = set()
    bl = v73_tail(root / "supportive modules" / "registry", "VIA_CeleritasPolicy_Baseline_v*.json")   # 只讀資料(不載入 VCGC 程式)
    try:
        exempt = {Path(x).name for x in json.loads(bl.read_text(encoding="utf-8")).get("py_readonly", {}).get("files", [])} if bl else set()
    except (ValueError, OSError):
        exempt = set()
    ex = sorted(x for x in miss_a + miss_n if x in exempt)
    miss_a = [x for x in miss_a if x not in exempt]
    miss_n = [x for x in miss_n if x not in exempt]
    lamp = "GREEN" if not miss_a and not miss_n else "YELLOW"
    return {"lamp": lamp, "accel": f"{acc}/{n}", "net_callers": f"{net_have}/{net_need}", "missing_accel": miss_a[:20], "missing_net": miss_n[:20],
            "exempt_readonly": sorted(set(ex))}



V268_VERBS = ("status", "catalog", "links", "read", "sync", "launch", "bridges", "tools")


def v268_tools(root: Path) -> dict:
    sup = root / "supportive modules"
    out = {}
    for key, pat, base in (("super_accel", "SUP_MDL737_SuperAccelModule_v*.py", sup), ("net_unified", "SUP_MDL740_NetUnified_v*.py", sup / "network")):
        p = v73_tail(base, pat)
        out[key] = {"path": str(p.relative_to(root)) if p else None, "sha12": hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p else None}
    d = v73_dir(root)
    skip = ("intake", "references", "_superseded", "__pycache__", "_quarantine_pip_vendor")
    own = [p for p in d.rglob("*") if p.is_file() and p.suffix in (".json", ".py") and not any(x in p.parts for x in skip)]
    for key, rx in (("regex_books", r"Regex"), ("synonym_books", r"Synonym|Lexicon"), ("ssot_books", r"SSOT|ssot")):
        out[key] = len([p for p in own if re.search(rx, p.name) or (key == "ssot_books" and "ssot" in p.parts)])
    miss = [k for k, v in out.items() if (isinstance(v, dict) and not v.get("path")) or v == 0]
    return {"lamp": "GREEN" if not miss else "YELLOW", "tools": out, "missing": miss}


def v268_launcher(root: Path):
    rel = sorted((root / "docs" / "handoff" / "ai").glob("vrn2_release_v*/ActivateVRN-2_v*.zip"), key=lambda p: (sm_vnum(p.parent), p.name))
    run = sorted((root / "docs" / "handoff" / "ai").glob("vrn2_release_v*/VRN2_RoundAll_v*.py"), key=sm_vnum)
    return (rel[-1] if rel else None), (run[-1] if run else None)


def v268_launch(root: Path, run_args: list | None = None) -> dict:
    zp, ra = v268_launcher(root)
    plan = v73_out(root, "install") / "VRN_InstallPlan_latest.json"
    missing = json.loads(plan.read_text(encoding="utf-8")).get("missing_here", []) if plan.is_file() else []
    if run_args is not None and ra:
        rc = subprocess.run([sys.executable, str(ra), *run_args], env=sm_child_env(), cwd=str(ra.parent)).returncode
        return {"lamp": "GREEN" if rc == 0 else ("YELLOW" if rc in (2, 3, 4) else "RED"), "ran": ra.name, "rc": rc}
    if not zp and not ra:
        state, lamp, rc = "RED(啟動器 / RoundAll 都不在)", "RED", 1
    elif missing:
        state, lamp, rc = "ABSENT(缺套件 · 經 VCGC InstallGate)", "ABSENT", 3
    else:
        state, lamp, rc = "READY", "GREEN", 0
    return {"lamp": lamp, "state": state, "release_zip": zp.name if zp else None, "roundall": ra.name if ra else None,
            "missing_libs": missing, "l16_rc": rc}


def v268_read(root: Path, args: list) -> dict:
    dom = args[0] if args else ""
    key = args[1] if len(args) > 1 and not args[1].startswith("--") else None
    live = {"engine": lambda: {k: v["tail"] for k, v in sm_engines(root).items()}, "bridge": lambda: v74_bridges(root),
            "tool": lambda: v268_tools(root), "records": lambda: sm_records(root), "launch": lambda: v268_launch(root),
            "parity": lambda: v73_parity(root), "conflict": lambda: v74_conflict(root),
            "upstream": lambda: {"vcgc_console": (v73_tail(root / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py") or Path("—")).name,
                                 "relation": "對等 · 只讀(L123)"}}
    if dom in live:
        val = live[dom]()
        return {"lamp": "GREEN", "domain": dom, "value": val.get(key) if key and isinstance(val, dict) else val}
    if dom == "ssot":
        books = sorted(p.name for p in (v73_dir(root) / "ssot").glob("*.json"))
        if key:
            p = v73_dir(root) / "ssot" / key
            return {"lamp": "GREEN" if p.is_file() else "ABSENT", "domain": dom, "book": key,
                    "value": list(json.loads(p.read_text(encoding="utf-8")).keys()) if p.is_file() else None}
        return {"lamp": "GREEN" if books else "ABSENT", "domain": dom, "value": books}
    if dom == "policy":
        p = v73_tail(root / "supportive modules" / "registry", "VIA_Policy_Laws_SSOT_v*.json")
        laws = [x for x in json.loads(p.read_text(encoding="utf-8")).get("laws", []) if not key or x.get("id") == key or "VRN" in json.dumps(x, ensure_ascii=False)] if p else []
        return {"lamp": "GREEN" if p else "ABSENT", "domain": dom, "book": p.name if p else None, "value": [{"id": x.get("id"), "key": x.get("key")} for x in laws][:80]}
    return {"lamp": "YELLOW", "domain": dom or "—", "why": "用法:read <" + "|".join(sorted(set(live) | {"ssot", "policy"})) + "> [key]"}


def v268_sync(root: Path, apply: bool) -> dict:
    """VRN 自己的同步計畫:能力對等 + 衝突 + 安裝計畫(只讀);VRN 沒有自家 SSOT 同步引擎 → --apply 照實不寫(L125 編號由 VCGC 核發)。"""
    par, cf, ins = v73_parity(root), v74_conflict(root), v73_install(root)
    return {"lamp": v73_worst([par["lamp"], cf["lamp"], ins["lamp"]]), "parity_gaps": par["gaps"], "conflict": cf["lamp"],
            "missing_libs": ins.get("missing_here", []), "applied": False,
            "why": "--apply:VRN 尚無自家 SSOT 同步引擎 → 不寫任何冊(照實)" if apply else ""}


def v268_catalog(root: Path) -> dict:
    zp, ra = v268_launcher(root)
    rows = {"ssot_books": len(list((v73_dir(root) / "ssot").glob("*.json"))), "books": len(v74_books(root)), "engines": len(sm_engines(root)),
            "records": len(sm_records(root)), "release_zip": zp.name if zp else None, "roundall": ra.name if ra else None,
            "verbs_native": len(SM_NATIVE), "verbs_forwarded_left": [v for v in ("status", "catalog", "links", "read", "sync", "launch", "bridges", "tools") if v not in SM_NATIVE]}
    return {"lamp": "GREEN" if rows["ssot_books"] and not rows["verbs_forwarded_left"] else "YELLOW", **rows}


def sm_cmd_v0268(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "status":
        s = {"health": sm_health(root), "parity": v73_parity(root), "conflict": v74_conflict(root), "launch": v268_launch(root)}
        r = {"lamp": v73_worst(v["lamp"] for v in s.values()), **{k: v["lamp"] for k, v in s.items()}}
    elif verb == "catalog":
        r = v268_catalog(root)
    elif verb == "links":
        r = v74_links(root)
    elif verb == "read":
        r = v268_read(root, [a for a in args if a not in ("--json", "--full")])
    elif verb == "sync":
        r = v268_sync(root, "--apply" in args)
    elif verb == "launch":
        r = v268_launch(root, [a for a in args if a not in ("--run", "--json", "--no-probe")] if "--run" in args else None)
    elif verb == "bridges":
        r = v74_bridges(root)
    else:
        r = v268_tools(root)
    if as_json or verb == "read":
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str)[:20000])
    else:
        brief = " · ".join(f"{k} {v}" for k, v in r.items() if k != "lamp" and (not isinstance(v, (dict, list)) or k in ("counts", "missing", "missing_libs", "verbs_forwarded_left", "parity_gaps")))
        print(f"[{SM_TAG}] {verb} {r.get('lamp')} · {brief[:600]}")
    if verb == "launch" and "--run" not in args:
        return r["l16_rc"]
    return SM_RC.get(r.get("lamp"), 2)


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)
    print(f"=== {SM_TAG} 自測(全動詞原生 · 不轉交前版)===", flush=True)
    import contextlib as _cl, io as _io
    buf = _io.StringIO()
    with _cl.redirect_stdout(buf):
        rc67 = _selftest_v0267()
    ck("① v0267 單檔 + L132 能力自測照過", rc67 == 0, buf.getvalue()[-300:])
    ck("② 剩下動詞全改原生:status · catalog · links · read · sync · launch · bridges · tools 都在 SM_NATIVE", all(v in SM_NATIVE for v in V268_VERBS))
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"]
        (d / "ssot").mkdir(parents=True)
        (d / "VRN_ENG001_A_v0100.py").write_text("x=1\n")
        (d / "ssot" / "VRN2_Demo_SSOT_v0100.json").write_text(json.dumps({"e": "functional modules/VRN/VRN_ENG001_A_v0100.py", "g": "VRN_ENG999_Gone_v0100.py"}))
        lk = v74_links(tr)
        ck("③ links:存在 1 · 不在 1(點名)", lk["counts"] == {"GREEN": 1, "MISSING": 1}, lk)
        la = v268_launch(tr)
        ck("④ launch 探測:發布包 / RoundAll 都不在 → RED rc 1", la["l16_rc"] == 1, la)
        ck("⑤ read ssot → 列冊", v268_read(tr, ["ssot"])["value"] == ["VRN2_Demo_SSOT_v0100.json"])
        ck("⑥ read 未知 → 用法 YELLOW", v268_read(tr, ["nope"])["lamp"] == "YELLOW")
    root = sm_via_root()
    ca = v268_catalog(root)
    ck("⑦ 真倉 catalog:轉交前版的動詞剩 0", ca["verbs_forwarded_left"] == [], ca["verbs_forwarded_left"])
    ck("⑧ 真倉 bridges:VRN 尾版加速器橋 100%", not v74_bridges(root)["missing_accel"], v74_bridges(root)["missing_accel"][:3])
    ck("⑨ 真倉 tools:加速器 / 網路工具正典解析得到", v268_tools(root)["tools"]["super_accel"]["path"] is not None)
    n = sum(ok)
    print(f"[計] {SM_TAG} 全原生 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


SM_NATIVE = SM_NATIVE + tuple(v for v in V268_VERBS if v not in SM_NATIVE)


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
