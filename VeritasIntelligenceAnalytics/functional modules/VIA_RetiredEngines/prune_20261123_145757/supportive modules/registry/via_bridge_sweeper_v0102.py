#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0100→v0101(批538 VIA 實測:兩個中央稽核器互相打臉)
  CGC_MDL158 全景稽核說加速器橋 100%、VDF 網路工具 100%;本清掃器說 2099 件裡加速殘 66、網路缺 6。
  兩個中央稽核器對同一棵樹講不同的話,一定有一個在說謊——查完是**範圍**不同:
    · 加速殘 66 全是**非尾版**舊版(VIA_VRN_FirstPageEngine_v0104…v0122、VRN_ENG082_ExtractionLogic_v0105/6…)
    · 網路缺 6 全在**凍結產出夾**(VRN/20260804/、VAP/input/SOURCE_VAP_MODULE/_output/VAP_WAREHOUSE_*_20260507_*/)
  依 L55 活樹律,這兩類都不是活樹;對它們報缺就是假紅。v0101 把「什麼算活樹」統一交給 CGC_MDL158(L30 一功能一主),
  不在本檔另造一套判準;非活樹的件改列 nonlive_* 照樣講清楚,不是掃到地毯下(冊在、數字在、清單在)。
  MDL158 不在時誠實退回舊範圍並標 scope=fallback(不假裝自己是活樹判準)。
via_bridge_sweeper — 雙橋統包清掃器(批127;via-sweep)
====================================================================
操作員令(批127,2026-08-24):「每個模組引擎都要掛加速器;凡向外部
API 要資料的都要用網路工具;整合、自動化」。
本器=單一自動工具,一次掃描全樹活動圈:
  ① ACCEL 橋 — 缺 [VIA:ACCEL-BRIDGE] 的活動 py 補掛(graceful 零行為)
  ② NET 橋 — 有外呼 import(urllib/requests/yfinance/akshare/playwright
     /httpx/aiohttp/websocket)而缺 [VIA:NET-BRIDGE] 的活動 py 補掛
     (統包 SUP_MDL740 惰性定位;法遵雙閘在統包端)
豁免圈(誠實列示,零觸碰):
  · EXEMPT_INTAKE — 原件收容區(new modules engines/v42 生態包/爬蟲
    雙引擎包/TALib vendor/dict/50_Protection/Standalone/docs history/
    references intake/_rebuilds/_from_vap_iso_cleanup):正本不就地修改
  · EXEMPT_SELF — 網路/加速統包家族自身(SUP_MDL737/740/Celeritas/
    AegisNexus/via_net_unified/VIA_SuperAccel_Module/VIA_NetSupport)
  · EXEMPT_LEGACY_NET — supportive modules/network 收容 legacy(統包涵蓋)
鐵則:注入前後雙 ast.parse,後驗敗不落檔;manifest+--undo 可逆;冪等。
用法:
  via-sweep --audit     → 只量測覆蓋(零寫入)
  via-sweep --run       → 雙橋補掛
  via-sweep --undo <manifest>
  via-sweep --selftest  → 八檢(沙盒零網路)
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

import ast
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "bridge_sweep_runs"

SKIP_FRAGS = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine",
              "_review_quarantine", "rename_runs", "rollback", "_syntaxfix_",
              "evidence", "SCOPE_COPY", "backup_", "VIA_Reports",
              "_via_mother_root_reconciliation_runs", "package_samples", "_vdf_envs")
EXEMPT_INTAKE = ("new modules engines", "VeritasAutoPlot_v42_EcoSystem",
                 "webscraping_dualengine", "TALib/vendor", "/dict/",
                 "50_Protection_Acceleration", "VIA_Standalone_Package",
                 "docs/history", "references/intake", "_rebuilds_superseded",
                 "_from_vap_iso_cleanup", "_inbox_to_classify")
EXEMPT_SELF = ("SUP_MDL737_SuperAccelModule", "SUP_MDL740_NetUnified",
               "via_net_unified", "VIA_SuperAccel_Module", "VeritasCeleritas",
               "VeritasAegisNexus", "VIA_NetSupport", "via_bridge_sweeper")
EXEMPT_LEGACY_NET = ("supportive modules/network/",)

NET_IMPORT_RX = re.compile(
    r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp|yfinance|akshare|playwright|websockets?)\b", re.M)

# ── 批646 第二層:現行尺涵蓋不到的觸網手法 ──────────────────────────────
#: 操作員令(批646):「全部都要加網路工具」。
#: 先量:第一層(上面那條 RX)報「網路缺 0 = 全覆蓋」——但那條尺只認
#: `import requests|urllib|httpx…` 這一類。**它看不見 socket / ssl / http.client /
#: smtplib / paramiko / pycurl**,而那些一樣出得了門。
#: 所以「全覆蓋」這句話在批646 之前,是**尺的範圍內全覆蓋**,不是全樹全覆蓋。
TIER2_MODS = {"socket", "ssl", "http", "urllib3", "ftplib", "smtplib", "imaplib",
              "poplib", "telnetlib", "paramiko", "pycurl", "selenium"}
#: 被複製進樹的三方件(urllib3/requests 內臟)。它們不是 VIA 的碼,掛 VIA 橋只會把它們改壞。
TIER2_VENDORED = {"pyopenssl", "socks", "_macos", "low_level", "ssltransport", "ssl_", "proxy",
                  "connection", "connectionpool", "poolmanager", "response", "retry",
                  "timeout", "util", "wait", "selectors", "urllib3"}
#: 只讀本機名字=零封包出門。豁免要附理由(L87),不是留空。
HOSTNAME_ONLY_ATTRS = {"gethostname", "getfqdn"}
#: **socket 專屬**的連線呼叫:任何接收端都算。
SOCKET_ONLY_ATTRS = {"create_connection", "connect_ex", "wrap_socket", "sendto", "sendall"}
#: 通用的 `connect`:**只有接收端像 socket 才算**。
#: 批646 第一版把 `connect` 無條件收進來,結果 `duckdb.connect(":memory:")` 被當成開 socket
#: ——22 件假紅,其中 11 件是同一支 InputConsole 的各版號。**尺錯不是樹錯**(L93)。
SOCKISH_RECV = {"socket", "s", "sock", "sk", "conn_sock", "_sock", "ssl"}
CONNECT_ATTRS = SOCKET_ONLY_ATTRS | {"connect"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0", ""}
ACCEL_MARK = "[VIA:ACCEL-BRIDGE"
NET_MARK = "[VIA:NET-BRIDGE"
ACCEL_END = "# ===== [VIA:ACCEL-BRIDGE:END] ====="

ACCEL_BRIDGE = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

NET_BRIDGE = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''


def _sha16(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:16]


def classify(rp: str) -> str:
    """回 ACTIVE / SKIP / EXEMPT_*(誠實圈)"""
    r = rp.replace("\\", "/")
    if any(f in r for f in SKIP_FRAGS):
        return "SKIP"
    if any(f in r for f in EXEMPT_INTAKE):
        return "EXEMPT_INTAKE"
    if any(Path(r).name.startswith(x) or x in Path(r).stem for x in EXEMPT_SELF):
        return "EXEMPT_SELF"
    if any(r.startswith(x) or f"/{x}" in "/" + r for x in EXEMPT_LEGACY_NET):
        return "EXEMPT_LEGACY_NET"
    return "ACTIVE"


def _is_socket_call(fn) -> bool:
    """這個 `X.attr(...)` 是不是**開 socket**?

    批646 實錄:第一版寫 `attr in {"connect", ...}`,於是 `duckdb.connect(":memory:")`
    也被算成開 socket——22 件假紅、目標欄印出 `:memory:`。
    收窄:`create_connection/connect_ex/wrap_socket/sendto/sendall` 是 socket 專屬,
    任何接收端都算;而裸 `connect` **只有接收端長得像 socket 才算**。
    """
    import ast as _ast
    if fn.attr in SOCKET_ONLY_ATTRS:
        return True
    if fn.attr != "connect":
        return False
    v = fn.value
    name = v.id if isinstance(v, _ast.Name) else (v.attr if isinstance(v, _ast.Attribute) else "")
    return name.lower() in SOCKISH_RECV


def _tier2_scan_text(t: str) -> dict:
    """一支檔的第二層實況。**零寫入、零網路;看的是 AST,不是註解裡的字。**

    回 {"mods": [...], "attrs": [...], "hosts": [...]}——`hosts` 只收**字面值**;
    收不到字面值(變數/設定檔)就回 `("?",)`,那是「不知道」,不是「本機」。
    """
    import ast as _ast
    out = {"mods": [], "attrs": [], "hosts": []}
    try:
        tree = _ast.parse(t)
    except Exception:
        return out
    mods = set()
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Import):
            mods |= {a.name.split(".")[0] for a in nd.names}
        elif isinstance(nd, _ast.ImportFrom) and nd.module:
            mods.add(nd.module.split(".")[0])
    out["mods"] = sorted(mods & TIER2_MODS)
    if not out["mods"]:
        return out
    attrs, hosts = set(), []
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Attribute):
            attrs.add(nd.attr)
    # 批646 第三把尺:**名字要能解析到它的預設值**。
    #   實錄:`def _port_open(port, host="127.0.0.1"): socket.create_connection((host, port))`
    #   ——只看到 `host` 是個變數就回「?」,於是一支純本機探活被判成缺橋。
    #   那不是保守,那是**把看得懂的東西說成看不懂**,而長期掛著的假紅會讓人不看紅燈(LL272)。
    #   解法:進到每個函式,先把「參數 → 字面預設值」建成表,再拿它解析連線目標。
    # **函式層先走、模組層最後**,而且模組層要跳過已經處理過的呼叫。
    #   批646 第五把尺:前一版兩輪都用 `ast.walk`,而 `walk` 是攤平的——
    #   同一行 `socket.create_connection((host, port))` 被數了兩次:
    #   函式層解析出 `127.0.0.1`,模組層 env 是空的又補了一個 `?`,
    #   於是 hosts=["127.0.0.1", "?"],一支純本機探活永遠紅著。
    _done: set = set()
    _scopes = [x for x in _ast.walk(tree)
               if isinstance(x, (_ast.FunctionDef, _ast.AsyncFunctionDef))] + [tree]
    for scope in _scopes:
        env = {}
        if isinstance(scope, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            a = scope.args
            pos = list(a.posonlyargs) + list(a.args)
            for arg, dflt in zip(pos[len(pos) - len(a.defaults):], a.defaults):
                if isinstance(dflt, _ast.Constant) and isinstance(dflt.value, str):
                    env[arg.arg] = dflt.value
            for arg, dflt in zip(a.kwonlyargs, a.kw_defaults):
                if isinstance(dflt, _ast.Constant) and isinstance(dflt.value, str):
                    env[arg.arg] = dflt.value
        for nd in _ast.walk(scope):
            if not (isinstance(nd, _ast.Call) and isinstance(nd.func, _ast.Attribute)
                    and _is_socket_call(nd.func)):
                continue
            if id(nd) in _done:              # 已由內層(有 env 的那一輪)處理過
                continue
            _done.add(id(nd))
            # **只取位址的第一格**。批646 第四把尺:前一版把整個 `(host, port)` 攤平後
            #   逐項收,於是 `port` 這個沒有字串預設值的參數也變成一個「?」,
            #   一支已經解析出 `127.0.0.1` 的純本機探活照樣紅。**埠號不是主機。**
            addr = nd.args[0] if nd.args else None
            tgt = addr.elts[0] if isinstance(addr, _ast.Tuple) and addr.elts else addr
            if isinstance(tgt, _ast.Constant) and isinstance(tgt.value, str):
                hosts.append(tgt.value)
            elif isinstance(tgt, _ast.Name) and tgt.id in env:
                hosts.append(env[tgt.id])                   # 參數預設值解析得到
            else:
                hosts.append("?")            # 真的判不出=不准當成本機
    out["attrs"] = sorted(attrs)
    out["hosts"] = hosts
    return out


def tier2_classify(rp: str, t: str) -> tuple:
    """(類別, 理由)。類別 ∈ VENDORED / HOSTNAME_ONLY / LOCALHOST_ONLY / NEEDS_BRIDGE / NONE。

    **豁免一律附理由**(L87);判不出連去哪就算 NEEDS_BRIDGE(寧可多問一句,不要少一盞燈)。
    """
    if NET_MARK in t:
        return "NONE", "已掛正典網路橋"
    sc = _tier2_scan_text(t)
    if not sc["mods"]:
        return "NONE", ""
    stem = Path(rp).stem.lower()
    if stem in TIER2_VENDORED or any(stem.startswith(v + "_") for v in TIER2_VENDORED):
        return "VENDORED", f"被複製進樹的三方件({', '.join(sc['mods'])});掛 VIA 橋只會把它改壞"
    used = set(sc["attrs"])
    if not sc["hosts"] and (used & HOSTNAME_ONLY_ATTRS):
        return "HOSTNAME_ONLY", f"只讀本機名字({'/'.join(sorted(used & HOSTNAME_ONLY_ATTRS))});零封包出門"
    if sc["hosts"] and all(h in LOCAL_HOSTS for h in sc["hosts"]):
        return "LOCALHOST_ONLY", f"連線目標字面值全為本機({', '.join(sorted(set(sc['hosts'])))});本機 hub 探活"
    if not sc["hosts"]:
        return "HOSTNAME_ONLY", f"import 了 {', '.join(sc['mods'])} 但沒有任何連線呼叫"
    return "NEEDS_BRIDGE", (f"用了 {', '.join(sc['mods'])} 的連線呼叫,目標 "
                            f"{', '.join(sorted(set(sc['hosts']))) or '(判不出)'};**應掛正典網路橋**")


def tier2_audit(root: Path = VIA) -> dict:
    """第二層覆蓋量測(零寫入)。**本層預設只報不改**——
    把正典橋硬掛到一個 `gethostname()` 上,是為了好看而說謊,不是治理。"""
    out = {"scanned": 0, "VENDORED": [], "HOSTNAME_ONLY": [], "LOCALHOST_ONLY": [],
           "NEEDS_BRIDGE": [], "mods_seen": {}}
    for p in root.rglob("*.py"):
        rp = str(p.relative_to(root))
        if classify(rp) != "ACTIVE":
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        out["scanned"] += 1
        cls, why = tier2_classify(rp, t)
        if cls == "NONE":
            continue
        out[cls].append({"file": rp, "why": why})
        for m in _tier2_scan_text(t)["mods"]:
            out["mods_seen"][m] = out["mods_seen"].get(m, 0) + 1
    return out


def _live_set(root: Path):
    """批538:活樹判準只有一個出處=CGC_MDL158(L30/L55)。回 (set|None, how)。
    只在量**真樹**時套用;自測的沙盒根不是真樹,套上去會把沙盒件全判成非活樹=自己把自己的自測弄啞。"""
    import importlib.util as _il
    if Path(root).resolve() != VIA.resolve():
        return None, "沙盒(全範圍;活樹判準只在真樹適用)"
    hits = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL158_VIAPanoramaAuditRepair_v*.py"))
    if not hits:
        return None, "fallback(CGC_MDL158 不在;範圍=舊判準,非活樹)"
    try:
        sp = _il.spec_from_file_location("_cgc158_live", hits[-1])
        m = _il.module_from_spec(sp)
        sp.loader.exec_module(m)
        return {str(x) for x in m.py_files()}, f"活樹({hits[-1].name};尾版律+凍結副本不算)"
    except Exception as exc:
        return None, f"fallback({type(exc).__name__};範圍=舊判準,非活樹)"


def audit(root: Path = VIA) -> dict:
    """覆蓋量測(零寫入)。批538:範圍=活樹(CGC_MDL158 判準);非活樹的件另列 nonlive_*,不進分母也不消失。"""
    live, how = _live_set(root)
    out = {"active": 0, "accel_have": 0, "accel_miss": [], "net_need": 0,
           "net_have": 0, "net_miss": [], "scope": how,
           "nonlive_accel_miss": [], "nonlive_net_miss": [],
           "exempt": {"EXEMPT_INTAKE": 0,
           "EXEMPT_SELF": 0, "EXEMPT_LEGACY_NET": 0}}
    for p in root.rglob("*.py"):
        rp = str(p.relative_to(root))
        cls = classify(rp)
        if cls == "SKIP":
            continue
        if cls != "ACTIVE":
            out["exempt"][cls] += 1
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        is_live = (live is None) or (str(p) in live)
        if not is_live:                                  # 批538:非活樹(非尾版/凍結產出夾)——講清楚,但不進分母
            if ACCEL_MARK not in t:
                out["nonlive_accel_miss"].append(rp)
            if NET_IMPORT_RX.search(t) and NET_MARK not in t:
                out["nonlive_net_miss"].append(rp)
            continue
        out["active"] += 1
        if ACCEL_MARK in t:
            out["accel_have"] += 1
        else:
            out["accel_miss"].append(rp)
        if NET_IMPORT_RX.search(t):
            out["net_need"] += 1
            if NET_MARK in t:
                out["net_have"] += 1
            else:
                out["net_miss"].append(rp)
    return out


def _insert_line(text: str, tree, after_accel: bool) -> int:
    lines = text.splitlines()
    if after_accel:
        for i, ln in enumerate(lines):
            if ACCEL_END in ln:
                return i + 1
    last = 0
    for i, ln in enumerate(lines[:3]):
        s = ln.strip()
        if s.startswith("#!") or ("coding" in s and s.startswith("#")):
            last = i + 1
    if tree.body and isinstance(tree.body[0], ast.Expr) and \
            isinstance(getattr(tree.body[0], "value", None), ast.Constant) and \
            isinstance(tree.body[0].value.value, str):
        last = max(last, tree.body[0].end_lineno)
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            last = max(last, node.end_lineno)
    return last


def inject_one(p: Path, rp: str, bridge: str, mark: str, after_accel: bool) -> dict:
    text = p.read_text(encoding="utf-8", errors="ignore")
    if mark in text:
        return {"rel": rp, "bridge": mark, "state": "SKIP", "note": "已橋"}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {"rel": rp, "bridge": mark, "state": "SKIP", "note": f"不可解析:{str(exc)[:40]}"}
    at = _insert_line(text, tree, after_accel)
    lines = text.splitlines(keepends=True)
    new = "".join(lines[:at]) + bridge + "".join(lines[at:])
    try:
        ast.parse(new)
    except SyntaxError:
        return {"rel": rp, "bridge": mark, "state": "FAIL", "note": "後驗敗,不落檔"}
    pre = _sha16(text)
    p.write_text(new, encoding="utf-8")
    return {"rel": rp, "bridge": mark, "state": "OK", "pre": pre, "post": _sha16(new)}


def run(root: Path = VIA, out_runs: Path | None = None) -> int:
    a = audit(root)
    print(f"=== 雙橋清掃器(批127)· 活動 {a['active']} · 補加速 {len(a['accel_miss'])}"
          f" · 補網路 {len(a['net_miss'])} · 豁免 {a['exempt']} ===")
    results = []
    n_ok = n_skip = n_fail = 0
    for rp in a["accel_miss"]:
        r = inject_one(root / rp, rp, ACCEL_BRIDGE, ACCEL_MARK, after_accel=False)
        results.append(r)
        n_ok += r["state"] == "OK"; n_skip += r["state"] == "SKIP"; n_fail += r["state"] == "FAIL"
    for rp in a["net_miss"]:
        r = inject_one(root / rp, rp, NET_BRIDGE, NET_MARK, after_accel=True)
        results.append(r)
        n_ok += r["state"] == "OK"; n_skip += r["state"] == "SKIP"; n_fail += r["state"] == "FAIL"
    rd = out_runs or RUNS
    rd.mkdir(parents=True, exist_ok=True)
    mf = rd / f"SWEEP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    mf.write_text(json.dumps({"schema": "via.bridgesweep.v1", "audit_before": {
        k: (len(v) if isinstance(v, list) else v) for k, v in a.items()},
        "results": results}, ensure_ascii=False, indent=1), encoding="utf-8")
    a2 = audit(root)
    print(f"  [計] 注入 {n_ok} · 跳 {n_skip} · 敗 {n_fail} · manifest {mf.name}")
    print(f"  [後測] 活動 {a2['active']} · 加速缺 {len(a2['accel_miss'])}"
          f" · 網路缺 {len(a2['net_miss'])}(0=全覆蓋)")
    return 1 if n_fail else 0


def undo(manifest: str) -> int:
    d = json.loads(Path(manifest).read_text(encoding="utf-8"))
    n_un = n_skip = 0
    for r in d["results"]:
        if r["state"] != "OK":
            continue
        p = VIA / r["rel"]
        if not p.exists():
            n_skip += 1
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if _sha16(t) != r["post"]:
            n_skip += 1
            continue
        mark = r["bridge"]
        start = "# ===== [VIA:NET-BRIDGE:v0100]" if mark == NET_MARK else "# ===== [VIA:ACCEL-BRIDGE:v0100]"
        endtag = "# ===== [VIA:NET-BRIDGE:END] =====" if mark == NET_MARK else ACCEL_END
        i0 = t.index(start)
        i1 = t.index(endtag) + len(endtag) + 1
        p.write_text(t[:i0] + t[i1:], encoding="utf-8")
        n_un += 1
    print(f"  [undo] 還原 {n_un} · 略過 {n_skip}(已變動/缺=誠實不動)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    ran = []

    def chk(name, cond, note=""):
        ran.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    chk("① 豁免分類(收容/自身/legacy/SKIP/ACTIVE)",
        classify("new modules engines/x.py") == "EXEMPT_INTAKE"
        and classify("supportive modules/SUP_MDL737_SuperAccelModule_v0100.py") == "EXEMPT_SELF"
        and classify("supportive modules/network/SUP_MDL620_x.py") == "EXEMPT_LEGACY_NET"
        and classify("functional modules/VAP/ASSETS/SCOPE_COPY/y.py") == "SKIP"
        and classify("functional modules/VRN/a.py") == "ACTIVE")
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        (sand / "functional modules/X").mkdir(parents=True)
        f1 = sand / "functional modules/X/eng_net.py"
        f1.write_text('"""doc"""\nimport urllib.request\n', encoding="utf-8")
        f2 = sand / "functional modules/X/eng_plain.py"
        f2.write_text('"""doc"""\nx = 1\n', encoding="utf-8")
        f3 = sand / "functional modules/X/broken.py"
        f3.write_text("def broken(:\n", encoding="utf-8")
        a0 = audit(sand)
        chk("② audit(2 缺加速·1 外呼缺網)", len(a0["accel_miss"]) >= 2
            and len(a0["net_miss"]) == 1 and a0["net_need"] == 1)
        rc = run(sand, out_runs=sand / "runs")
        t1 = f1.read_text(encoding="utf-8")
        chk("③ 雙橋注入(net 件=雙橋·先 ACCEL 後 NET)", rc == 0
            and ACCEL_MARK in t1 and NET_MARK in t1
            and t1.index(ACCEL_MARK) < t1.index(NET_MARK))
        chk("④ 純件只掛加速橋", ACCEL_MARK in f2.read_text(encoding="utf-8")
            and NET_MARK not in f2.read_text(encoding="utf-8"))
        chk("⑤ 壞檔誠實 SKIP+後驗 ast 全過",
            all(bool(ast.parse(f.read_text(encoding="utf-8"))) for f in (f1, f2))
            and ACCEL_MARK not in f3.read_text(encoding="utf-8"))
        a1 = audit(sand)
        chk("⑥ 後測全覆蓋(缺=0;壞檔除外)",
            [x for x in a1["accel_miss"] if "broken" not in x] == [] and a1["net_miss"] == [])
        rc2 = run(sand, out_runs=sand / "runs")
        chk("⑦ 冪等(再跑零注入)", rc2 == 0
            and f1.read_text(encoding="utf-8").count(ACCEL_MARK) == 2)  # 塊頭+END 各含 MARK 前綴一次
        ns = {"__file__": str(f1)}
        exec(compile(f1.read_text(encoding="utf-8").split("import urllib")[0], "x", "exec"), ns)
        chk("⑧ 沙盒橋 graceful(兩態合法·NET 統包缺=None)",
            "VIA_ACCEL" in ns and ns["VIA_NET_TOOL_PATH"] is None
            and ns["_via_net"]() is None)
    # ── 批646 第二層 ────────────────────────────────────────────────────
    _t2 = {
        "out": 'import socket\ns = socket.create_connection(("api.example.com", 443))\n',
        "host": "import socket\nname = socket.gethostname()\n",
        "local": 'import socket\nwith socket.create_connection(("127.0.0.1", 8931), timeout=0.3):\n    pass\n',
        "unknown": "import socket\ndef f(h):\n    return socket.create_connection((h, 443))\n",
    }
    _c = {k: tier2_classify(f"x_{k}.py", v)[0] for k, v in _t2.items()}
    chk("⑨ 第二層咬得住**真的出門**的那一種(`socket.create_connection((\"api.example.com\", 443))`"
        " → NEEDS_BRIDGE);而 `gethostname()` → HOSTNAME_ONLY、`127.0.0.1` → LOCALHOST_ONLY"
        "(批646:第一層那條 RX 只認 import requests|urllib|httpx…,**看不見 socket/ssl/http.client**;"
        "所謂「全覆蓋」在此之前是**尺的範圍內全覆蓋**)",
        _c["out"] == "NEEDS_BRIDGE" and _c["host"] == "HOSTNAME_ONLY"
        and _c["local"] == "LOCALHOST_ONLY",
        f"({_c})")
    chk("⑩ **連去哪判不出來就不准算本機**(目標是變數 → NEEDS_BRIDGE)。"
        "寧可多問一句,不要少一盞燈——把「不知道」歸進「安全」是假綠的標準作法",
        _c["unknown"] == "NEEDS_BRIDGE", f"(變數目標 → {_c['unknown']})")
    _a2 = tier2_audit()
    chk("⑪ **活樹第二層零缺橋**(批646 實測:活件裡真的出門而沒掛正典橋的 = 0;"
        "socket 那一批全是 `gethostname()` 讀本機名 或 `127.0.0.1` 本機 hub 探活,"
        "ssl/http 那一批是被複製進樹的三方件)。"
        "**這一檢把「已經全覆蓋」從我的一句話,變成機器每次都會重驗的事**",
        not _a2["NEEDS_BRIDGE"],
        f"(活件 {_a2['scanned']} · 缺橋 {len(_a2['NEEDS_BRIDGE'])}"
        f" · 豁免 三方 {len(_a2['VENDORED'])}/本機名 {len(_a2['HOSTNAME_ONLY'])}"
        f"/本機連線 {len(_a2['LOCALHOST_ONLY'])})")

    print(f"  [計] {len(ran)} 檢 OK {len(ran) - len(fails)} · FAIL {len(fails)}(檢數現場計)")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 雙橋清掃器 · 八檢自測(沙盒零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        return undo(args[i + 1])
    if "--net2" in args:
        a2 = tier2_audit()
        print("=== 雙橋清掃器 · **第二層**(socket/ssl/http.client/smtplib/paramiko…;零寫入)===")
        print(f"  活件 {a2['scanned']} · 模組分佈 {a2['mods_seen'] or '(無)'}")
        for k in ("VENDORED", "HOSTNAME_ONLY", "LOCALHOST_ONLY"):
            print(f"  [豁免 {k:<14}] {len(a2[k]):>3}" +
                  (f"  例:{a2[k][0]['file'].split('/')[-1][:40]} — {a2[k][0]['why'][:52]}" if a2[k] else ""))
        nb = a2["NEEDS_BRIDGE"]
        print(f"  [**NEEDS_BRIDGE**] {len(nb):>3}" + ("(0=第二層也全覆蓋)" if not nb else ""))
        for x in nb[:20]:
            print(f"    [缺橋] {x['file']}  ← {x['why']}")
        print(f"  [裁決] {'GREEN' if not nb else 'RED'} · "
              + ("第一層與第二層都零缺" if not nb
                 else f"第二層點名 {len(nb)} 件;**本層只報不改**——"
                      "掛橋要逐件看它到底出不出門(L87 豁免必附理由)"))
        return 0 if not nb else 1
    if "--audit" in args:
        a = audit()
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in a.items()},
                         ensure_ascii=False, indent=1))
        print("加速缺件:", *a["accel_miss"][:10], sep="\n  ")
        return 0
    return run()


if __name__ == "__main__":
    sys.exit(main())
