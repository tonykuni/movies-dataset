#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0175 — v0174 全文 + collect() 自報改原生(只讀冊 · 不 import 他系統)+ token 省 Token 動詞(經 VCGC 鎖冊 · 子行程 · 唯讀)。

操作員 2026-11-14:「SYSTEM MANAGER 應該據最新狀況及政策重寫並導入多個 VCGC TOKEN-SAVING 工具去完成」。
實錄:v0173 單檔重寫拿掉了 collect() → VCGC 全景「註冊@VDF」一直 NODATA、啟動門 CGC_MDL209 自測 AttributeError。舊 collect() 的上行七處靠 import VCGC
主控台來算(違反標準 P4)。本版照標準 v0101:七處只讀 VCGC 的冊與檔面文字;省 Token 工具(read · slice · digest · chain)只經鎖冊解析、以子行程唯讀執行,
目標限 VDF 自己的樹與自己的收據。沿用 v0173 起的單檔做法(不載入前版);v0174 一字不動。
  collect [--json]                 自報:七處 · 健康 · 規範自查 · 啟動探測(給 VCGC 全景 / 啟動門只讀)
  token read|slice|digest|chain …  省 Token 讀檔(只收 VDF 自己的檔 / 家族 / 收據)

(以下 v0174 說明)VDF_SystemManager v0174 — 全動詞原生(v0173 + 最後 7 個 LEGACY 動詞 catalog · links · read · sync · launch · bridges · tools 改原生 + 鏡像衝突檢視 conflict = 衝突哨兵 · GitHub 對齊 · 子系統邊界;不再轉交前版,--legacy 只供對照)。

(以下 v0173 說明)VDF_SystemManager v0173 — 單檔重寫(操作員 2026-11-13「不適合的引擎重寫不要用舊的」· L132 能力對等):以 v0171 標準核心為底 + 併入 v0172 缺套件判讀 + VDF 自有一份 VCGC 能力(status · parity · ssot · regex · synonyms · number · params · backup · sdd · graphify · omniroute · mcp · install · page · closeout);模組層不載入任何前版,尚未重寫的 LEGACY 動詞(catalog · links · read · sync · launch · bridges · tools)以子行程明示轉交前版。

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
SM_VERSION = "v0175"
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
    if verb in V74_VERBS + V74_EXTRA:
        return sm_cmd_v0174(verb, args, root)
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


def _selftest_v0173() -> int:
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


# ══════════════════════════ v0174:最後 7 個 LEGACY 動詞改原生(catalog · links · read · sync · launch · bridges · tools)══════════════════════════
V74_VERBS = ("catalog", "links", "read", "sync", "launch", "bridges", "tools")
V74_PATH_RX = re.compile(r"[\w ./\-]+?\.(?:py|json|jsonl|ps1)$")   # 只查程式 / 冊引用;資料輸出(parquet · duckdb · csv · html)不是連結
V74_NET_CALL = re.compile(r"urllib\.request\.urlopen|\burlopen\(|\brequests\.(get|post|Session)\(|\bhttpx\.(get|post|Client)\(|\byf\.download\(|\byfinance\.(download|Ticker)\(")


def v74_books(root: Path) -> list:
    d = v73_dir(root)
    fams = {}
    for p in list(d.glob("*.json")) + list((d / "SSOT").glob("*.json")) + list((d / "registry").glob("*.json")):
        m = re.match(r"^(.+)_v(\d{4})\.json$", p.name)
        key = (str(p.parent), m.group(1)) if m else (str(p.parent), p.stem)
        if key not in fams or sm_vnum(p) > sm_vnum(fams[key]):
            fams[key] = p
    return sorted(fams.values(), key=lambda p: p.name)


def v74_resolve(root: Path, s: str) -> bool:
    s = s.strip().replace("\\", "/")
    if not s or s.startswith(("http:", "https:")):
        return True
    for base in (root, v73_dir(root), v73_dir(root) / "engine", v73_dir(root) / "SSOT"):
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
            elif isinstance(x, str) and len(x) < 260 and V74_PATH_RX.fullmatch(x.strip()) and (x.startswith(("functional modules/", "supportive modules/", "docs/")) or Path(x).name.startswith(("VDF_", "VIA_", "CGC_", "SUP_"))):
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
    lamp = "GREEN" if not miss_a and not miss_n else "YELLOW"
    return {"lamp": lamp, "accel": f"{acc}/{n}", "net_callers": f"{net_have}/{net_need}", "missing_accel": miss_a[:20], "missing_net": miss_n[:20]}


def v74_tools(root: Path) -> dict:
    sup = root / "supportive modules"
    out = {}
    for key, pat, base in (("super_accel", "SUP_MDL737_SuperAccelModule_v*.py", sup), ("net_unified", "SUP_MDL740_NetUnified_v*.py", sup / "network")):
        p = v73_tail(base, pat)
        out[key] = {"path": str(p.relative_to(root)) if p else None,
                    "sha12": hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p else None, "bytes": p.stat().st_size if p else 0}
    for key in V73_OWN:
        b = v73_own_book(root, key)
        out["own_" + key] = {"book": b.get("book"), "drift": b.get("drift"), "lamp": b.get("lamp")}
    miss = [k for k, v in out.items() if not (v.get("path") or v.get("book"))]
    return {"lamp": "GREEN" if not miss else "YELLOW", "tools": out, "missing": miss}


def v74_launch(root: Path, run_args: list | None = None) -> dict:
    d = v73_dir(root)
    act = v73_tail(d, "VDF_MDL013_ActivateVDF_v*.py")
    gates = {k: os.environ.get(k, "") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    plan = v73_out(root, "install") / "VDF_InstallPlan_latest.json"
    missing_libs = json.loads(plan.read_text(encoding="utf-8")).get("missing_here", []) if plan.is_file() else []
    dbs = [p for base in (d / "output_hub", root / "VIA_Reports" / "vdf_fetch") if base.is_dir() for p in base.rglob("*.duckdb")]
    if run_args is not None and act:
        rc = subprocess.run([sys.executable, str(act), *run_args], env=sm_child_env(), cwd=str(d)).returncode
        return {"lamp": "GREEN" if rc == 0 else ("YELLOW" if rc in (2, 3, 4) else "RED"), "ran": act.name, "rc": rc}
    if not act:
        state, lamp = "RED(啟動器不在)", "RED"
    elif missing_libs:
        state, lamp = "ABSENT(缺套件 · 經 VCGC InstallGate)", "ABSENT"
    elif not all(v.upper() == "YES" for v in gates.values()):
        state, lamp = "GATED(同意閘未開 = 你的手)", "YELLOW"
    elif not dbs:
        state, lamp = "NODATA(庫還沒建)", "YELLOW"
    else:
        state, lamp = "READY", "GREEN"
    return {"lamp": lamp, "state": state, "launcher": act.name if act else None, "gates": {k: (v or "UNSET") for k, v in gates.items()},
            "missing_libs": missing_libs, "duckdb": len(dbs), "l16_rc": {"READY": 0, "RED": 1}.get(state.split("(")[0], 4 if state.startswith("GATED") else (3 if state.startswith("ABSENT") else 2))}


def v74_sync(root: Path, apply: bool) -> dict:
    own = {k: v73_own_book(root, k) for k in V73_OWN}
    num = v73_number(root)
    r = {"lamp": v73_worst([*(v["lamp"] for v in own.values()), num["lamp"]]), "own_drift": [k for k, v in own.items() if v.get("drift")],
         "unnumbered": num["unnumbered"], "changed": num["changed_since_last"], "applied": False}
    if apply:
        tool = v73_tail(v73_dir(root), "VDF_SSOTSync_v*.py")
        if tool:
            rc = subprocess.run([sys.executable, str(tool), "sync"], env=sm_child_env(), cwd=str(v73_dir(root))).returncode
            r.update({"applied": True, "tool": tool.name, "rc": rc})
            if rc not in (0, 2):
                r["lamp"] = "RED"
    return r


def v74_read(root: Path, args: list) -> dict:
    dom = args[0] if args else ""
    key = args[1] if len(args) > 1 and not args[1].startswith("--") else None
    d = v73_dir(root)
    pick = {"param": "VDF_Param_Registry_v*.json", "ssot": SM_CONFIG["ssot_glob"], "datahome": "VDF_DataHome_SSOT_v*.json",
            "universe": "VDF_InputUniverse_SSOT_v*.json", "unified": "VDF_Unified_Params_v*.json", "logic": "VDF_*Logic*_v*.json",
            "factor": "VDF_*Factor*_v*.json", "policy": None, "regex": "SSOT/VDF_Regex_SSOT_v*.json", "synonyms": "SSOT/VDF_Synonym_SSOT_v*.json",
            "workflow": "SSOT/VDF_Workflow_SSOT_v*.json"}
    live = {"engine": lambda: {k: v["tail"] for k, v in sm_engines(root).items()}, "bridge": lambda: v74_bridges(root), "tool": lambda: v74_tools(root),
            "records": lambda: sm_records(root), "launch": lambda: v74_launch(root), "params": lambda: v73_params(root),
            "upstream": lambda: {"vcgc_console": (v73_tail(root / "supportive modules" / "registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py") or Path("—")).name,
                                 "relation": "對等 · 只讀(L123)"},
            "handover": lambda: {k: v for k, v in json.loads((root / "docs" / "handoff" / "HANDOFF_latest.json").read_text(encoding="utf-8")).items()
                                 if k in ("summary", "updated_at", "pending")} if (root / "docs" / "handoff" / "HANDOFF_latest.json").is_file() else {}}
    if dom in live:
        val = live[dom]()
        return {"lamp": "GREEN", "domain": dom, "value": val.get(key) if key and isinstance(val, dict) else val}
    if dom == "policy":
        p = v73_tail(root / "supportive modules" / "registry", "VIA_Policy_Laws_SSOT_v*.json")
        laws = [x for x in json.loads(p.read_text(encoding="utf-8")).get("laws", []) if not key or x.get("id") == key or "VDF" in json.dumps(x, ensure_ascii=False)] if p else []
        return {"lamp": "GREEN" if p else "ABSENT", "domain": dom, "book": p.name if p else None, "value": [{"id": x.get("id"), "key": x.get("key")} for x in laws][:80]}
    if dom in pick:
        base, pat = (d / "SSOT", pick[dom][5:]) if pick[dom].startswith("SSOT/") else (d, pick[dom])
        p = v73_tail(base, pat)
        if not p:
            return {"lamp": "ABSENT", "domain": dom, "why": f"沒有 {pick[dom]}"}
        data = json.loads(p.read_text(encoding="utf-8"))
        val = data.get(key) if key and isinstance(data, dict) else (list(data.keys()) if isinstance(data, dict) else f"{type(data).__name__} {len(data)}")
        return {"lamp": "GREEN", "domain": dom, "book": p.name, "value": val}
    return {"lamp": "YELLOW", "domain": dom or "—", "why": "用法:read <" + "|".join(sorted(set(pick) | set(live))) + "> [key]"}


def v74_catalog(root: Path) -> dict:
    rows = {"ssot": v73_tail(v73_dir(root), SM_CONFIG["ssot_glob"]) is not None, "books": len(v74_books(root)),
            "engines": len(sm_engines(root)), "own_copies": [k for k in V73_OWN if v73_tail(v73_dir(root) / "SSOT", V73_OWN[k])],
            "records": len(sm_records(root)), "launcher": (v73_tail(v73_dir(root), "VDF_MDL013_ActivateVDF_v*.py") or Path("—")).name,
            "verbs_native": len(SM_NATIVE), "verbs_legacy_left": [v for v in V73_LEGACY if v not in SM_NATIVE]}
    return {"lamp": "GREEN" if rows["ssot"] and not rows["verbs_legacy_left"] else "YELLOW", **rows}



V74_EXTRA = ("conflict",)
V74_OTHER_SYS = re.compile(r"(?:import|from)\s+(VRN|VQG|VAP|CGC)_\w+|spec_from_file_location\([^)]*['\"](?:VRN|VQG|VAP|CGC)_\w+|functional modules/(?:VRN|VQG|VAP)\b|['\"]VRN_SystemManager|['\"]VQG_AllInOne|['\"]VAP_SystemManager")
V74_ABS_PATH = re.compile(r"[A-Za-z]:\\\\Users\\\\|C:/Users/|/home/[a-z]+/|/Users/[A-Za-z]")


def v74_conflict(root: Path) -> dict:
    """鏡像衝突檢視(VDF 自有一份 · 同 VCGC 衝突閘三道):① 衝突哨兵 ② GitHub 對齊 ③ 子系統邊界;只讀。"""
    d = v73_dir(root)
    # ① 衝突哨兵:同名不同內容 · 0-byte 佔位 · 寫死絕對路徑(R2 同規)
    seen, dup, zero, abspath = {}, [], [], []
    skip = ("references", "intake", "_superseded", "output_hub", "__pycache__", "retired")
    for q in d.rglob("*.py"):
        if any(x in q.parts for x in skip):
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
    sentinel = {"lamp": "RED" if abspath else ("YELLOW" if (zero or dup) else "GREEN"), "same_name_diff": dup[:10], "zero_byte": zero[:10], "abs_path": abspath[:10]}
    # ② GitHub 對齊:分支對上游 ahead/behind(本機已知 ref,不連網)· VDF 夾未提交
    def git(*a):
        r = subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)
        return r.returncode, r.stdout.strip()
    rc, ab = git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    ahead, behind = (ab.split() + ["?", "?"])[:2] if rc == 0 else ("?", "?")
    _, dirty = git("status", "--porcelain", "--", SM_CONFIG["dir"])
    dirty_n = len([x for x in dirty.splitlines() if x.strip()])
    gh_lamp = "GREEN" if rc == 0 and behind == "0" and dirty_n == 0 else ("YELLOW" if rc == 0 else "YELLOW")
    github = {"lamp": gh_lamp, "ahead": ahead, "behind": behind, "vdf_uncommitted": dirty_n, "upstream": rc == 0}
    # ③ 子系統邊界:VDF 尾版不得載入他系統程式(加速器 / 網路橋 = 共用支援工具,不算)
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


def sm_cmd_v0174(verb: str, args: list, root: Path) -> int:
    as_json = "--json" in args
    if verb == "catalog":
        r = v74_catalog(root)
    elif verb == "links":
        r = v74_links(root)
    elif verb == "read":
        r = v74_read(root, [a for a in args if a not in ("--json", "--full")])
    elif verb == "sync":
        r = v74_sync(root, "--apply" in args)
    elif verb == "launch":
        r = v74_launch(root, [a for a in args if a not in ("--run", "--json", "--no-probe")] if "--run" in args else None)
    elif verb == "bridges":
        r = v74_bridges(root)
    elif verb == "conflict":
        r = v74_conflict(root)
    else:
        r = v74_tools(root)
    if as_json or verb == "read":
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str)[:20000])
    else:
        brief = " · ".join(f"{k} {v}" for k, v in r.items() if k != "lamp" and not isinstance(v, (dict, list)) or k in ("counts", "missing", "gates", "missing_libs", "own_copies", "verbs_legacy_left", "own_drift"))
        print(f"[{SM_TAG}] {verb} {r.get('lamp')} · {brief[:600]}")
    if verb == "launch" and "--run" not in args:
        return r["l16_rc"]
    return SM_RC.get(r.get("lamp"), 2)


def _selftest_v0174() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}", flush=True)
    print(f"=== {SM_TAG} 自測(全動詞原生 · 不轉交前版)===", flush=True)
    import contextlib as _cl, io as _io
    buf = _io.StringIO()
    with _cl.redirect_stdout(buf):
        rc73 = _selftest_v0173()
    ck("① v0173 單檔 + L132 能力自測照過", rc73 == 0, buf.getvalue()[-300:])
    ck("② 7 個舊動詞全改原生:catalog · links · read · sync · launch · bridges · tools 都在 SM_NATIVE", all(v in SM_NATIVE for v in V74_VERBS))
    root = sm_via_root()
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"]
        (d / "SSOT").mkdir(parents=True)
        (d / "VDF_ENG001_A_v0100.py").write_text("x=1\n")
        (d / "VDF_Demo_SSOT_v0100.json").write_text(json.dumps({"engine": "functional modules/VDF/VDF_ENG001_A_v0100.py", "gone": "VDF_ENG999_Gone_v0100.py",
                                                                 "url": "https://x/y.json"}))
        lk = v74_links(tr)
        ck("③ links:存在 1 · 不在 1(點名)· 網址不算", lk["counts"] == {"GREEN": 1, "MISSING": 1} and "VDF_ENG999_Gone_v0100.py" in lk["missing"][0], lk)
        global sm_engines
        real = sm_engines
        sm_engines = lambda r: {"VDF_ENG001_A": {"tail": "functional modules/VDF/VDF_ENG001_A_v0100.py", "tail_ver": 100, "versions": 1}}
        try:
            (d / "VDF_ENG001_A_v0100.py").write_text("import requests\nr = requests.get('http://x')\n")
            br = v74_bridges(tr)
            ck("④ bridges:缺加速器橋 + 真擷取缺網路橋 → 點名", br["missing_accel"] == ["VDF_ENG001_A_v0100.py"] and br["missing_net"] == ["VDF_ENG001_A_v0100.py"], br)
            la = v74_launch(tr)
            ck("⑤ launch 探測:啟動器不在 → RED rc 1", la["lamp"] == "RED" and la["l16_rc"] == 1, la)
            (d / "VDF_MDL013_ActivateVDF_v0100.py").write_text("import sys\nsys.exit(0)\n")
            la2 = v74_launch(tr)
            ck("⑥ launch 探測:啟動器在 · 閘未開 → GATED rc 4(不代設同意閘)", la2["l16_rc"] in (2, 3, 4) and "UNSET" in la2["gates"].values() if not os.environ.get("VIA_NET_CONSENT") else True, la2)
            rd = v74_read(tr, ["engine"])
            ck("⑦ read engine → 家族表", rd["value"] == {"VDF_ENG001_A": "functional modules/VDF/VDF_ENG001_A_v0100.py"})
            ck("⑧ read 未知領域 → 用法提示 YELLOW", v74_read(tr, ["nope"])["lamp"] == "YELLOW")
            sy = v74_sync(tr, apply=False)
            ck("⑨ sync 預設只出計畫(不跑 SSOTSync · 不寫冊)", sy["applied"] is False)
        finally:
            sm_engines = real
    ck("⑬ conflict 三道(哨兵 · GitHub 對齊 · 子系統邊界)都有燈", set(v74_conflict(root)) >= {"sentinel", "github", "boundary", "lamp"})
    ca = v74_catalog(root)
    ck("⑩ 真倉 catalog:LEGACY 動詞剩 0", ca["verbs_legacy_left"] == [], ca)
    t = v74_tools(root)
    ck("⑪ 真倉 tools:加速器 / 網路工具正典 + 三份自有冊都解析得到", t["lamp"] == "GREEN", t["missing"])
    b = v74_bridges(root)
    ck("⑫ 真倉 bridges:VDF 尾版加速器 / 網路橋覆蓋 100%", b["lamp"] == "GREEN", (b["missing_accel"][:3], b["missing_net"][:3]))
    n = sum(ok)
    print(f"[計] {SM_TAG} 全原生 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


SM_NATIVE = SM_NATIVE + tuple(v for v in V74_VERBS + V74_EXTRA if v not in SM_NATIVE)


def _main_v0174(argv=None) -> int:
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



# ══════════════════════════ v0175:collect() 自報改原生(只讀冊 · 不 import 他系統)+ token 省 Token 動詞(經鎖冊 · 子行程 · 唯讀)══════════════════════════
# 操作員 2026-11-14:「SYSTEM MANAGER 應該據最新狀況及政策重寫並導入多個 VCGC TOKEN-SAVING 工具去完成」。
# 實錄:11/11 依標準重寫時拿掉了 collect()(VCGC 全景 / 啟動門讀的自報介面),VCGC 那一格一直是 NODATA;舊 collect() 的上行七處靠 import VCGC
# 主控台來算,違反標準 P4。本段:七處改成只讀 VCGC 的冊與檔面文字來判(不 import、不執行);省 Token 工具只經鎖冊解析、以子行程唯讀執行,
# 目標限本系統自己的樹與自己的收據;鎖冊或工具不在 → ABSENT,管理器其他功能不受影響。
V75_SEVEN = ("spec", "grid", "register", "deck", "manager", "inventory", "handover")
V75_KEYS = {"VDF": {"spec_id": "vdf_system", "deck": "vdf_system", "cmd": "via-vdfsys"},
            "VRN": {"spec_id": "vrn_system", "deck": "vrn_system", "cmd": "via-vrnsys"}}
V75_TOKEN_SUBS = ("read", "slice", "digest", "chain")
V75_VERBS = ("collect", "token")


def _v75_cfg() -> dict:
    return SM_CONFIG


def _v75_vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _v75_newest(folder: Path, pattern: str):
    hits = [p for p in folder.glob(pattern) if p.is_file()] if folder.is_dir() else []
    return max(hits, key=lambda p: (_v75_vnum(p), p.name)) if hits else None


def _v75_text(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace") if p else ""
    except OSError as exc:
        return "\0READ_ERROR " + type(exc).__name__


def v75_upstream(root: Path) -> dict:
    """上行七處自審:全部只讀 VCGC 的冊與檔面文字(不 import、不執行;標準 P4)。找不到的那一處照實記 False,不假綠。"""
    cfg = _v75_cfg()
    fam, key = cfg["manager_family"], V75_KEYS[cfg["system"]]
    reg = root / "supportive modules" / "registry"
    src = {"spec": _v75_newest(reg, "VIA_InputConsole_Spec_v*.json"), "grid": _v75_newest(reg, "CGC_MDL064_SelftestGrid_v*.py"),
           "register": _v75_newest(root, "Register-VIA-Commands-v*.ps1"), "deck": _v75_newest(reg, "CGC_MDL095_DeckServer_v*.py"),
           "inventory": _v75_newest(reg, "VIA_Component_Inventory_SSOT_v*.json")}
    mgrs = sorted(root.glob("VIA_SYSTEM_MANAGER_v*.py"), key=_v75_vnum)
    out = {"via": SM_TAG, "mode": "file_read", "how": "只讀 VCGC 的冊與檔面文字(不 import、不執行 · 標準 P4)",
           "sources": {k: (v.name if v else None) for k, v in src.items()}}
    out["spec"] = bool(re.search(r'"id"\s*:\s*"%s"' % re.escape(key["spec_id"]), _v75_text(src["spec"])))
    out["grid"] = fam in _v75_text(src["grid"])
    books = sorted(root.glob("Register-VIA-Commands-v*.ps1"), key=_v75_vnum)      # 命令冊是 dot-source 鏈:整條讀
    out["register"] = any(re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(key["cmd"]), _v75_text(b)) for b in books)
    dk = _v75_text(src["deck"])
    out["deck"] = ('"%s"' % key["deck"]) in dk or ("'%s'" % key["deck"]) in dk
    out["manager"] = any(('"%s"' % fam) in _v75_text(p) for p in mgrs)
    out["via_manager"] = mgrs[-1].name if mgrs else "ABSENT"
    inv = False
    try:
        j = json.loads(_v75_text(src["inventory"]) or "{}")
        rec = next((r for r in j.get("records") or [] if r.get("identity") == fam and r.get("state", "ACTIVE") == "ACTIVE"), None)
        inv = (rec or {}).get("code") or False
    except ValueError as exc:
        out["inventory_error"] = type(exc).__name__
    out["inventory"] = inv
    docs = sorted((root / "docs").glob("*.md"))[-40:]
    out["handover"] = any(fam in _v75_text(q) for q in docs)
    out["seven"] = {k: out.get(k, False) for k in V75_SEVEN}
    out["done"] = sum(1 for k in V75_SEVEN if out.get(k))
    return out


def _v75_lamp(x) -> str:
    return x.get("lamp", "NODATA") if isinstance(x, dict) else "NODATA"


def collect() -> dict:
    """給對等系統只讀監控的自報(VCGC 全景 · 啟動門讀這個):七處 · 健康 · 規範自查 · 啟動探測。不寫檔、不出網、不 import 他系統。"""
    root = sm_via_root()
    up = v75_upstream(root)
    lamps = {"upstream": "GREEN" if up["done"] == len(V75_SEVEN) else "YELLOW"}
    for name, fn in (("health", sm_health), ("conform", sm_conform)):
        try:
            lamps[name] = _v75_lamp(fn(root))
        except Exception as exc:  # noqa: BLE001 — 自報不讓單一檢查拖垮;照實記
            lamps[name] = "NODATA"
            up.setdefault("errors", {})[name] = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    out = {"schema": "VIA.%s.SystemManager.collect.v2" % _v75_cfg()["system"], "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "me": Path(__file__).name, "version": "v0175", "system": _v75_cfg()["system"], "served_by": {"tail": SM_TAG},
           "upstream": up, "lamps": lamps}
    try:
        la = v74_launch(root)
        st = str(la.get("state") or "")
        out["launch"] = {"state": la.get("lamp"), "detail": st, "launcher": la.get("launcher"), "gates": la.get("gates"), "duckdb": la.get("duckdb"),
                         "launchers": {"cmds_missing": []}, "why": st,
                         "next": "同意閘是操作員的手(本管理器不代設)" if st.startswith("GATED") else ("缺套件經 VCGC InstallGate" if st.startswith("ABSENT") else "")}
    except Exception as exc:  # noqa: BLE001
        out["launch"] = {"state": "NODATA", "why": "%s: %s" % (type(exc).__name__, str(exc)[:120]), "launchers": {"cmds_missing": []}}
    worst = list(lamps.values()) + ([out["launch"]["state"]] if isinstance(out.get("launch"), dict) else [])
    out["rc"] = 1 if "RED" in worst else (0 if all(x == "GREEN" for x in worst) else 2)
    out["rc_name"] = {0: "GREEN", 1: "RED", 2: "YELLOW/NODATA"}[out["rc"]]
    return out


def _v75_scope(root: Path) -> list:
    cfg = _v75_cfg()
    return [root / cfg["dir"]] + [root / r for r in cfg.get("reports") or []] + [root / "docs" / "handoff" / "evidence"]


def _v75_resolve(root: Path, target: str):
    """目標路徑:絕對 → 照用;相對 → 先以目前目錄、再以 VIA 根找。回 (絕對路徑, 是否在本系統範圍內)。"""
    cands = [Path(target)] if Path(target).is_absolute() else [Path.cwd() / target, root / target]
    t = next((c for c in cands if c.exists()), cands[-1])
    try:
        t = t.resolve()
    except (OSError, ValueError):
        return t, False
    return t, any(t == s.resolve() or s.resolve() in t.parents for s in _v75_scope(root))


def v75_token(root: Path, args: list, capture: bool = False) -> dict:
    """省 Token:read(骨架卡)· slice(一個定義)· digest(日誌判決行)· chain(薄尾版本鏈)。
    工具路徑只從 VCGC 鎖冊 VIA_ToolVersion_Lock 的 token.path 解析(不釘檔名、不 import);以子行程唯讀執行;目標限本系統的樹與自己的收據。"""
    sub = args[0] if args else ""
    if sub not in V75_TOKEN_SUBS:
        return {"lamp": "YELLOW", "why": "用法:token <%s> <目標…>(read / slice / digest 收本系統的檔;chain 收本系統的家族名)" % "|".join(V75_TOKEN_SUBS)}
    rest = [a for a in args[1:]]
    pos = [a for a in rest if not a.startswith("-")]
    if not pos:
        return {"lamp": "YELLOW", "why": "少了目標"}
    if sub == "chain":
        prefixes = tuple(_v75_cfg().get("own_prefixes") or ())
        if not pos[0].startswith(prefixes):
            return {"lamp": "DENY", "why": "chain 只收本系統的家族(%s…)" % "/".join(prefixes), "target": pos[0]}
    else:
        absp, inside = _v75_resolve(root, pos[0])
        if not inside:
            return {"lamp": "DENY", "why": "目標不在本系統的樹或自己的收據內(對等系統只讀不代看)", "target": pos[0]}
        rest = [str(absp) if a == pos[0] else a for a in rest]
    lock = _v75_newest(root / "supportive modules" / "registry", "VIA_ToolVersion_Lock_v*.json")
    try:
        rel = ((json.loads(_v75_text(lock)) if lock else {}).get("token") or {}).get("path")
    except ValueError:
        rel = None
    tool = None
    if rel:                                 # 鎖冊的路徑以倉根為準(前綴 VIA 根夾名);兩種寫法都認
        for base in (root.parent, root):
            if (base / rel).is_file():
                tool = base / rel
                break
    if tool is None:
        return {"lamp": "ABSENT", "why": "鎖冊或省 Token 工具不在(本管理器其他功能照常)", "lock": lock.name if lock else None, "tool": rel}
    cp = subprocess.run([sys.executable, str(tool), sub, *rest], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    text = cp.stdout or ""
    ledger = next((l.strip() for l in text.splitlines() if l.startswith("[token 帳]")), "")
    if not capture:
        sys.stdout.write(text)
        if cp.stderr.strip():
            sys.stderr.write(cp.stderr[-2000:])
    return {"lamp": "GREEN" if cp.returncode == 0 else "RED", "rc": cp.returncode, "tool": tool.name, "lock": lock.name, "ledger": ledger,
            "out": text if capture else None}


def _v75_cmd(verb: str, args: list) -> int:
    root = sm_via_root()
    if verb == "collect":
        r = collect()
        if "--json" in args:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        else:
            up = r["upstream"]
            print("[%s] collect · rc %s %s · 七處 %d/7 %s · 燈 %s%s" % (SM_TAG, r["rc"], r["rc_name"], up["done"],
                  " ".join(k for k, v in up["seven"].items() if not v) and ("缺 " + " ".join(k for k, v in up["seven"].items() if not v)) or "",
                  r["lamps"], (" · 啟動 " + r["launch"]["state"]) if isinstance(r.get("launch"), dict) else ""), flush=True)
        return r["rc"]
    r = v75_token(root, args)
    if r["lamp"] != "GREEN":
        print("[%s] token %s · %s" % (SM_TAG, r["lamp"], r.get("why") or ("rc %s" % r.get("rc"))), flush=True)
    return {"GREEN": 0, "RED": 1, "DENY": 2, "YELLOW": 2, "ABSENT": 3}.get(r["lamp"], 2)


def _v75_selftest_new() -> list:
    """本版新增的自測(回 [(名稱, 過否, 附註)])。零網路 · 只在 tempfile 寫。"""
    res = []
    root = sm_via_root()
    before = {n for n in sys.modules if n.startswith(("CGC_", "vcgc", "via_vcgc"))}
    r = collect()
    loaded = {n for n in sys.modules if n.startswith(("CGC_", "vcgc", "via_vcgc"))} - before
    res.append(("① collect():上行七鍵齊 · rc / 燈都有 · 呼叫後沒有載入任何 VCGC 模組(P4)",
                set(r["upstream"]["seven"]) == set(V75_SEVEN) and "rc" in r and "lamps" in r and not loaded, (r["upstream"]["done"], sorted(loaded))))
    la = r.get("launch") or {}
    res.append(("② collect():啟動門要的欄位齊(launch.state · launchers.cmds_missing);啟動器在就不是 RED",
                isinstance(la, dict) and "state" in la and "cmds_missing" in (la.get("launchers") or {}) and la.get("state") != "RED", la.get("state")))
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        reg = tr / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        cfg = _v75_cfg()
        (reg / "VIA_InputConsole_Spec_v0100.json").write_text(json.dumps({"x": [{"id": V75_KEYS[cfg["system"]]["spec_id"], "state": "ON"}]}), encoding="utf-8")
        (reg / "VIA_Component_Inventory_SSOT_v0100.json").write_text(json.dumps({"records": [{"identity": cfg["manager_family"], "code": "VIA-SYS-TEST", "state": "ACTIVE"}]}), encoding="utf-8")
        up = v75_upstream(tr)
        res.append(("③ 夾具:只有規格冊與元件冊 → 七處只 spec / inventory 真,其餘照實 False(不假綠)",
                    up["seven"]["spec"] is True and up["seven"]["inventory"] == "VIA-SYS-TEST" and up["done"] == 2, up["seven"]))
        t0 = v75_token(tr, ["read", cfg["dir"] + "/x.py"], capture=True)
        res.append(("④ token:鎖冊不在 → ABSENT(不崩 · 其他功能照常)", t0["lamp"] == "ABSENT", t0))
    other = "functional modules/VRN/VRN_SystemManager_v0266.py" if _v75_cfg()["system"] == "VDF" else "functional modules/VDF/VDF_SystemManager_v0174.py"
    t1 = v75_token(root, ["read", other], capture=True)
    t2 = v75_token(root, ["chain", "CGC_MDL149_VeritasCentralGovernanceConsole"], capture=True)
    res.append(("⑤ token:目標是對等系統的檔 / 家族 → DENY(只讀自己的樹)", t1["lamp"] == "DENY" and t2["lamp"] == "DENY", (t1["lamp"], t2["lamp"])))
    t3 = v75_token(root, ["read", _v75_cfg()["dir"] + "/" + Path(__file__).name], capture=True)
    res.append(("⑥ token read 本檔:經鎖冊解析的工具出骨架卡 + [token 帳](鎖冊不在則照實 ABSENT)",
                (t3["lamp"] == "GREEN" and "[token 帳]" in (t3.get("out") or "")) or t3["lamp"] == "ABSENT", (t3["lamp"], t3.get("tool"), t3.get("ledger", "")[:60])))
    src = Path(__file__).read_text(encoding="utf-8")
    block = src[src.index("# ══════════════════════════ " + "v0175" + ":"):]
    bad = re.findall(r"^\s*(?:import|from)\s+(CGC_\w+|VIA_VCGC_\w+|VRN\w*|VDF\w*)\b", block, re.M)
    gate_write = re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", block)
    ta = re.search(r"^\s*(?:import|from)\s+" + "ta" + "lib", block, re.M)
    res.append(("⑦ 本段原始碼:不 import 他系統 · 不寫同意閘 · 不碰 TA-Lib", not bad and not gate_write and not ta, (bad, bool(gate_write), bool(ta))))
    res.append(("⑧ 動詞齊:collect · token 都在原生動詞表", all(v in SM_NATIVE for v in V75_VERBS), ""))
    return res


SM_NATIVE = SM_NATIVE + tuple(v for v in V75_VERBS if v not in SM_NATIVE)


def selftest() -> int:
    print(f"=== {SM_TAG} 自測(v0174 核心 + 本版 collect / token)===", flush=True)
    core = _selftest_v0174() == 0
    res = [("⓪ v0174 核心自測照過(全動詞原生 13 項)", core, "")] + _v75_selftest_new()
    for name, ok, note in res[1:]:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note and not ok else ''}", flush=True)
    n = sum(1 for _, ok, _ in res if ok)
    print(f"[計] {SM_TAG} 自測 {n}/{len(res)} {'PASS' if n == len(res) else 'FAIL'}", flush=True)
    return 0 if n == len(res) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] and args[0] in V75_VERBS:
        return _v75_cmd(args[0], args[1:])
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return _main_v0174(args)


if __name__ == "__main__":
    sys.exit(main())
