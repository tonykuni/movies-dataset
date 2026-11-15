#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0183 — v0182 單檔全文 + 資料平面動詞(操作員 2026-11-15「每個系統 SYSTEM MANAGER 該控管的項目範圍 VDF SYSTEM MANAGER 都要有 · 輸出 PARQUET 增量資料庫可出到各類雲端硬碟 MCP 與 PC · 台股及主動式台股 ETF 清單也要被驗證有效作為輸入 · 不重複擷取 · 整理清簡優化再輸出更新快速」;VDF-REQ030)。
本版只多三個動詞,其餘一字照 v0182:
  scope                     管理範圍總表(輸入清單 → 擷取 → DuckDB 正典庫 → parquet 增量庫 → 匯出 → 整合;每項一燈 + 證據 + 下一步)+ 一頁 U/I
  inputs                    清單輸入閘(台股清單 · 主動式台股 ETF 清單 · 合格判定 VDF-REQ026 獨立重驗)
  parquet status|sync|plan|export   資料家 tw__ / gl__ parquet(ENG065 檔名協定)增量維護 · 不重複擷取計畫 · 增量匯出到 PC 夾 / 雲端同步夾 + MCP 交接清單
三個動詞以子行程轉給 VDF_MDL020_DataPlane 尾版(本檔仍零動態載入他檔;rc 照它)。主分派多一行 if(登在 SM_MAIN_IFS)→ 仍是標準轉交者。

(以下 v0182 說明)VDF_SystemManager v0182 — v0181 單檔全文 + 資料庫狀態矩陣頁(操作員 2026-11-15「Advice, database status with a very well organize matrix report to display if the display effect is good please apply this matrix on the user interface HTml u/i」;VDF-REQ028):`db check` / `db verify` 轉交跑完,本管理器以子行程叫 VDF_MDL019_DBStatusMatrix 尾版 render → VIA_Reports/vdf/DB_STATUS_MATRIX_latest.html(KPI · 建議 · 庫 × 狀態 · 寫入引擎 × 狀態 · 逐表明細 · 他系統表只讀),並把資料庫頁 DB_CHECK_latest.html 換成同一頁(原平表留 DB_CHECK_table_latest.html,明細一列不少);既有連到資料庫頁的地方(ActivateVDF 總覽)點開就是矩陣。rc 照轉交那一版的不改;渲染器不在 / 失敗照實印一行不擋。管理員矩陣頁導覽列多「資料庫狀態矩陣」。主分派多一行 `verb == "db"` 的 if(也登進本版 SM_MAIN_IFS,本檔照樣是標準轉交者);不動態載入他檔(P4)。

(以下 v0181 說明)VDF_SystemManager v0181 — v0180 單檔全文 + 轉交直達(操作員 2026-11-14「Proceed with the remaining part in your recommended methods」;ActivateVDF v0117 實測:每個轉交動詞走 10 層子行程 v0180 → v0179 → … → v0168,一輪 12 次呼叫 = 120 個轉交行程,每個峰值約 69 MB,engine_launch 那一條整段佔約 0.7 GB):前版 v0169 … v0180 的轉交規則 · 前版選法 · 子行程環境 · main 分派逐字相同(本版 AST 比對過),中間各層只是原樣再轉一次 → 本版轉交前先在前版鏈上「唯讀算路」(ast.parse 各版的 SM_NATIVE · 不執行前版):從前一版起,每一版若是標準轉交者且動詞不是它的原生動詞就往下一版,停在第一個會自己處理的那版(實測 = v0168),直接起那一支子行程。參數 / 環境 / cwd / rc 與逐層轉交完全相同(--legacy 照舊只在第一層生效)。任何一版認不出標準形狀 / SM_NATIVE 算不出來 → 停在那版(= 前版行為,不猜)。VIA_VDF_SM_DIRECT=0 可關(回逐層轉交)。新原生動詞 route <動詞 …>:印這個動詞會落在哪一版 · 省掉幾層。前版一字不動;零網路 · 不碰 TA-Lib · 不讀寫同意閘。

(以下 v0180 說明)VDF_SystemManager v0180 — v0179 單檔全文 + 引擎矩陣改用作業系統檔案鎖(PR 641 · Codex P2):v0179 用「O_EXCL 建鎖檔 + 老過 120 秒就刪」,兩個呼叫端同時判定同一個殘留鎖時,後刪的會刪掉先到者剛建的新鎖、兩邊同時進入;本版改 POSIX fcntl.flock / Windows msvcrt.locking,持有者結束(含被砍)作業系統自動放鎖 → 沒有殘留鎖;鎖檔從不刪 → 刪不到別人的鎖;放鎖只經自己的檔案控制碼。

(以下 v0179 說明)VDF_SystemManager v0179 — v0178 單檔全文 + 引擎矩陣同時執行不互撞(PR 640 · Codex P2):舊版每個行程都寫同一個 `<檔>.tmp`,兩個行程同時更新登記冊時後改名的會 FileNotFoundError;本版暫存檔名帶行程號 + 亂數,登記冊「讀 → 算 → 寫」整段用鎖檔排隊(跨行程 / 執行緒);自動登記最多等 2 秒、等不到這一輪不登(不擋主動詞);engine-matrix 最多等 30 秒、還在忙照實回 YELLOW rc 2 不崩;殘留鎖(老過 120 秒)自動清。

(以下 v0178 說明)VDF_SystemManager v0178 — v0177 單檔全文 + 引擎矩陣(操作員 2026-11-14「VDF / VRN / VCGC 每個子系統 SYSTEM MANAGER 都要矩陣化自動註冊所有引擎版本號 時間」):本管理器每次執行(自測除外)靜默登記自己夾裡每個引擎家族 × 每一版(版號 · 檔案時間 UTC · 首次登記 UTC · git 建立時間 · CRLF 無關雜湊 · VCGC 號只讀對照),存 VIA_Reports/vdf/engine_matrix/(JSON · CSV · HTML);新動詞 engine-matrix 印矩陣。同版號內容被改 → 記「變」(版號律)· 尾版待號 → YELLOW。只讀 VCGC 編號冊,不寫冊、不 import 他系統。

(以下 v0177 說明)VDF_SystemManager v0177 — v0176 單檔全文 + sdd 燈不冒充驗收(PR 631 審查 P1):原本只驗冊結構(編號連續 · 步引擎在位 · 副本未漂移)就報 GREEN,並流進 status / closeout;本版 sdd 一律最多 YELLOW,另列 structure 燈;known_open 依步上的手分 OPEN / CLOSED_WITH_OPERATOR_ITEMS;實測證據(evidence_rule)歸 SDD 驗證器,標「未判」(AGENTS.md 第 6 條:未測保留未完成)。

(以下 v0176 說明)VDF_SystemManager v0176 — v0175 單檔全文 + 備份 zip 內檔名一律正斜線(Windows CI 2026-11-14 實測:SHA256SUMS 記反斜線、zip 內存正斜線 → backup check KeyError 崩);check 兼容 v0175 在 Windows 做的舊備份(反斜線名照對),缺件記 RED 不崩。

(以下 v0175 說明)VDF_SystemManager v0175 — v0174 單檔全文 + 矩陣頁視覺鎖定修正(VCGC kit 色票完整對應:淺底深字 · 表格隔列 · 導覽列連到自建工作台與本系統實測輸出)。

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
import contextlib
import importlib.util
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

SM_CONFIG = {'system': 'VDF',
 'manager_family': 'VDF_SystemManager',
 'dir': 'functional modules/VDF',
 'own_prefixes': ['VDF_'],
 'reports': ['VIA_Reports/vdf_fetch', 'VIA_Reports/vdf'],
 'ssot_glob': 'VDF_FetchSystem_SSOT_v*.json',
 'forward_verbs': ['status'],
 'native_extra': ['test', 'engine-matrix', 'route'],
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
SM_VERSION = "v0183"
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


# ══════════════════════════ v0181:轉交直達(唯讀算路 · 不執行前版)══════════════════════════
SM_FWD_V0180 = """def sm_forward(args: list, root: Path) -> int:
    '''前版其餘功能原樣轉交(子行程 · 參數 / 環境 / cwd / rc 不變)。'''
    pp = sm_prior_path(root)
    if pp is None:
        print(f"[{SM_TAG}] ABSENT · 前版 {SM_CONFIG['manager_family']}_v* 不在 {root / SM_CONFIG['dir']}(動詞 {args[:1]} 無從轉交)")
        return 3
    return subprocess.run([sys.executable, str(pp), *args], env=sm_child_env()).returncode
"""          # 前版鏈(v0169 … v0180)逐字相同的轉交函式;本版自己的另算(兩種都是「標準轉交者」)
SM_MAIN_IFS = ('if not args:', 'if verb in ("--selftest", "selftest"):', 'if verb != "engine-matrix":',
               'if verb in SM_NATIVE and "--legacy" not in args:',
               'if verb == "db" and args[1:2] in (["check"], ["verify"]):',   # v0182:db 清點 / 核對後出資料庫狀態矩陣頁
               'if verb in DP_VERBS and "--legacy" not in args:')             # v0183:資料平面三動詞轉 VDF_MDL020


class _SmUnknown:
    def __repr__(self):
        return "UNKNOWN"


SM_UNK = _SmUnknown()


def _sm_ev(node, env):
    """模組層常數式的唯讀求值(只認 常數 · tuple / list / dict · 名字 · 下標 · 相加 · tuple()/list() · 單層產生式 if x not in Y)。其餘 → UNKNOWN。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, (ast.Tuple, ast.List)):
        vals = [_sm_ev(e, env) for e in node.elts]
        if any(v is SM_UNK for v in vals):
            return SM_UNK
        return tuple(vals) if isinstance(node, ast.Tuple) else list(vals)
    if isinstance(node, ast.Dict):
        out = {}
        for k, v in zip(node.keys, node.values):
            kk = _sm_ev(k, env) if k is not None else SM_UNK
            if isinstance(kk, (str, int)):
                out[kk] = _sm_ev(v, env)
        return out
    if isinstance(node, ast.Name):
        return env.get(node.id, SM_UNK)
    if isinstance(node, ast.Subscript):
        base, key = _sm_ev(node.value, env), _sm_ev(node.slice, env)
        if base is SM_UNK or key is SM_UNK or not isinstance(base, (dict, tuple, list)):
            return SM_UNK
        try:
            return base[key]
        except (KeyError, IndexError, TypeError):
            return SM_UNK
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _sm_ev(node.left, env), _sm_ev(node.right, env)
        if a is SM_UNK or b is SM_UNK or type(a) is not type(b) or not isinstance(a, (tuple, list, str)):
            return SM_UNK
        return a + b
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("tuple", "list")
            and len(node.args) == 1 and not node.keywords):
        arg = node.args[0]
        vals = _sm_gen(arg, env) if isinstance(arg, ast.GeneratorExp) else _sm_ev(arg, env)
        if vals is SM_UNK or not isinstance(vals, (tuple, list)):
            return SM_UNK
        return tuple(vals) if node.func.id == "tuple" else list(vals)
    return SM_UNK


def _sm_gen(g, env):
    if len(g.generators) != 1:
        return SM_UNK
    c = g.generators[0]
    if c.is_async or not isinstance(c.target, ast.Name) or not isinstance(g.elt, ast.Name) or g.elt.id != c.target.id:
        return SM_UNK
    it = _sm_ev(c.iter, env)
    if it is SM_UNK or not isinstance(it, (tuple, list)):
        return SM_UNK
    out = []
    for x in it:
        keep = True
        for cond in c.ifs:
            if not (isinstance(cond, ast.Compare) and isinstance(cond.left, ast.Name) and cond.left.id == c.target.id
                    and len(cond.ops) == 1 and isinstance(cond.ops[0], (ast.In, ast.NotIn))):
                return SM_UNK
            coll = _sm_ev(cond.comparators[0], env)
            if coll is SM_UNK or not isinstance(coll, (tuple, list, dict, str)):
                return SM_UNK
            hit = x in coll
            keep = keep and (not hit if isinstance(cond.ops[0], ast.NotIn) else hit)
        if keep:
            out.append(x)
    return out


def sm_static_card(path: Path) -> dict:
    """一支管理器檔的唯讀名片:是不是標準轉交者 · 原生動詞(ast 求值;不執行那支)。"""
    card = {"path": str(path), "version": sm_vnum(path), "standard": False, "natives": None, "why": ""}
    try:
        src = Path(path).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError) as exc:
        card["why"] = "讀不了 / 剖析不了:%s" % type(exc).__name__
        return card
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    mine = {n.name: n for n in ast.parse(SM_HERE.read_text(encoding="utf-8")).body if isinstance(n, ast.FunctionDef)}
    ref_fwd = {ast.unparse(ast.parse(SM_FWD_V0180).body[0]), ast.unparse(mine["sm_forward"])}
    if not all(k in fns for k in ("main", "sm_forward", "sm_prior_path", "sm_child_env", "sm_vnum")):
        card["why"] = "不是標準管理器(缺 main / sm_forward / sm_prior_path / sm_child_env / sm_vnum)"
        return card
    same = all(ast.unparse(fns[k]) == ast.unparse(mine[k]) for k in ("sm_prior_path", "sm_child_env", "sm_vnum"))
    if not same or ast.unparse(fns["sm_forward"]) not in ref_fwd:
        card["why"] = "前版選法 / 子行程環境 / 轉交函式跟標準不同"
        return card
    ifs = [ast.unparse(n.test) for n in ast.walk(fns["main"]) if isinstance(n, ast.If)]
    allowed = {ast.unparse(ast.parse(s[3:-1], mode="eval").body) for s in SM_MAIN_IFS}
    need = ast.unparse(ast.parse('verb in SM_NATIVE and "--legacy" not in args', mode="eval").body)
    if not set(ifs) <= allowed or need not in ifs:
        card["why"] = "main 分派跟標準不同:%s" % sorted(set(ifs) - allowed)[:3]
        return card
    for n in ast.walk(tree):
        if isinstance(n, ast.Global) and {"SM_NATIVE", "SM_CONFIG"} & set(n.names):
            card["why"] = "函式裡改 SM_NATIVE / SM_CONFIG(靜態算不準)"
            return card
    env = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            env[n.targets[0].id] = _sm_ev(n.value, env)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            env[n.target.id] = _sm_ev(n.value, env)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            cur, add = env.get(n.target.id, SM_UNK), _sm_ev(n.value, env)
            env[n.target.id] = cur + add if (isinstance(n.op, ast.Add) and cur is not SM_UNK and add is not SM_UNK
                                             and type(cur) is type(add) and isinstance(cur, (tuple, list))) else SM_UNK
        elif not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.If, ast.Try, ast.Expr)):
            if any(isinstance(x, ast.Name) and x.id in ("SM_NATIVE", "SM_CONFIG") for x in ast.walk(n)):
                card["why"] = "模組層有看不懂的 SM_NATIVE / SM_CONFIG 敘述"
                return card
        elif isinstance(n, (ast.Expr, ast.If, ast.Try)):
            if any(isinstance(x, ast.Name) and x.id in ("SM_NATIVE", "SM_CONFIG") for x in ast.walk(n)) and not (
                    isinstance(n, ast.If) and "__name__" in ast.unparse(n.test)):
                card["why"] = "模組層在 if / try / 呼叫裡碰 SM_NATIVE / SM_CONFIG(靜態算不準)"
                return card
    nat = env.get("SM_NATIVE", SM_UNK)
    if not (isinstance(nat, (tuple, list)) and all(isinstance(x, str) for x in nat)):
        card["why"] = "SM_NATIVE 算不出來"
        return card
    card.update(standard=True, natives=tuple(nat), why="標準轉交者")
    return card


def sm_route(args: list, root: Path) -> dict:
    """唯讀算路:轉交(已去掉 --legacy 的)參數會落在哪一版。回 {target, hops[], skipped, why}。"""
    d = root / SM_CONFIG["dir"]
    verb = args[0] if args else ""
    cur, hops = sm_prior_path(root), []
    if cur is None:
        return {"target": None, "hops": [], "skipped": 0, "why": "前版不在"}
    while True:
        card = sm_static_card(cur)
        hops.append({"file": cur.name, "standard": card["standard"], "why": card["why"]})
        if not card["standard"] or not verb or verb in ("--selftest", "selftest") or verb in card["natives"]:
            why = "%s 自己處理" % cur.name if card["standard"] else "%s(%s)" % (cur.name, card["why"])
            break
        nxt = [p for p in d.glob(SM_CONFIG["manager_family"] + "_v*.py") if 0 <= sm_vnum(p) < sm_vnum(cur)]
        if not nxt:
            why = "%s 之下沒有前版(照逐層轉交它也會 ABSENT)" % cur.name
            break
        cur = max(nxt, key=sm_vnum)
    return {"target": cur, "hops": hops, "skipped": len(hops) - 1, "why": why}


def sm_forward(args: list, root: Path) -> int:
    """前版其餘功能轉交(子行程 · 參數 / 環境 / cwd / rc 不變);v0181:直達會自己處理的那一版(VIA_VDF_SM_DIRECT=0 回逐層)。"""
    pp = sm_prior_path(root)
    if pp is None:
        print(f"[{SM_TAG}] ABSENT · 前版 {SM_CONFIG['manager_family']}_v* 不在 {root / SM_CONFIG['dir']}(動詞 {args[:1]} 無從轉交)")
        return 3
    target = pp
    if os.environ.get("VIA_VDF_SM_DIRECT", "1") != "0":
        try:
            target = sm_route(args, root)["target"] or pp
        except Exception as exc:  # noqa: BLE001 — 算路壞了就照逐層轉交(行為等同前版),原因記在狀態
            EM_STATE["route_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:160])
            target = pp
    return subprocess.run([sys.executable, str(target), *args], env=sm_child_env()).returncode


def sm_route_cmd(args: list, root: Path) -> int:
    fwd = [a for a in args if a not in ("--legacy", "--json")]
    r = sm_route(fwd, root)
    if "--json" in args:
        print(json.dumps({"verb": fwd, "target": r["target"].name if r["target"] else None, "skipped": r["skipped"],
                          "hops": r["hops"], "why": r["why"]}, ensure_ascii=False, indent=1))
        return 0 if r["target"] else 3
    print(f"[{SM_TAG}] route {' '.join(fwd) or '(空)'} → {r['target'].name if r['target'] else '—'} · 省掉 {r['skipped']} 層轉交 · {r['why']}")
    for h in r["hops"]:
        print(f"  {h['file']:<32} {'標準轉交者' if h['standard'] else '停 · ' + h['why']}")
    return 0 if r["target"] else 3


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


EM_CFG = {"system": "VDF", "manager": SM_TAG, "dir": SM_CONFIG["dir"], "prefixes": tuple(SM_CONFIG["own_prefixes"]),
          "out": "VIA_Reports/vdf/engine_matrix"}


def em_files(root) -> list:
    """引擎矩陣與 engines 動詞看同一批檔(自己的夾 · 自己的前綴 · 有版號 · 跳過 SM_SKIP)。"""
    return sorted(sm_own_files(Path(root)))

# ────────────────── 引擎矩陣:本系統每個引擎家族 × 每一版 × 時間(自動登記 · 只看自己的夾)──────────────────
# 每次本管理器執行(自測除外)都靜默更新一次登記冊(檔沒變就不重寫;雜湊用大小 + 修改時間快取);`engine-matrix` 動詞印矩陣並出 CSV / HTML。
# 時間四種:file_time(檔案修改時間 UTC)· first_seen(本系統第一次登記到這一版的 UTC 時間)·
#           git_added(這一版檔案第一次進 git 的時間,= 版本建立時間;`engine-matrix` 才查,沒 git / 淺 clone 照實留空)·
#           vcgc_at(VCGC 編號冊給號的時間;只讀,冊不在就「待號」,不代寫冊)。
# 雜湊是 CRLF → LF 後的 SHA-256 前 12 碼(Windows / Linux 同值)。同版號內容變了 = 違反版號律 → 記「變」+ changed_at,燈 YELLOW。
EM_VER_RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")
EM_BOOK_GLOBS = ("VIA_NumberBook_MDL_v*.jsonl", "VIA_NumberBook_ENG_v*.jsonl")
EM_STATE = {"auto": None, "auto_error": None}
EM_COLS = ("system", "family", "version", "tail", "vcgc_code", "vcgc_at", "git_added", "file_time", "first_seen", "changed_at", "gone_at",
           "sha12", "bytes", "state", "path")


def em_utc(ts=None) -> str:
    d = datetime.now(timezone.utc) if ts is None else datetime.fromtimestamp(ts, timezone.utc)
    return d.strftime("%Y-%m-%d %H:%M:%S +00:00")


def em_iso_to_utc(s: str) -> str:
    try:
        return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +00:00")
    except ValueError:
        return ""


def em_read(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def em_json(s):
    try:
        return json.loads(s) if s else None
    except ValueError:
        return None


def em_sha12(p) -> str:
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def em_numbers(root) -> dict:
    """VCGC 編號冊(MDL + ENG)只讀:檔名(不含 .py)→ 號 · 給號時間。冊不在 → 空(全部「待號」)。"""
    d = Path(root) / "supportive modules" / "registry" / "VIA_NumberBooks"
    out = {}
    for g in EM_BOOK_GLOBS:
        for bp in sorted(d.glob(g)):
            for ln in em_read(bp).splitlines():
                r = em_json(ln)
                if isinstance(r, dict) and r.get("name"):
                    out[r["name"]] = {"code": r.get("code"), "at": r.get("numbered_at") or r.get("updated_at")}
    return out


def em_parse_git(text: str) -> dict:
    """`git log --diff-filter=A --name-only --format=@@%cI` → 檔名 → 第一次加入 git 的 UTC 時間(log 由新到舊,留最舊那次)。"""
    out, cur = {}, ""
    for ln in text.splitlines():
        if ln.startswith("@@"):
            cur = em_iso_to_utc(ln[2:])
        elif ln.strip() and cur:
            out[Path(ln.strip()).name] = cur
    return out


def em_git_added(root) -> dict:
    base = Path(root) / EM_CFG["dir"]
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=off", "log", "--diff-filter=A", "--name-only", "--format=@@%cI", "--", str(base)],
                           cwd=str(root), capture_output=True, timeout=180, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"_error": "%s:%s" % (type(exc).__name__, str(exc)[:120])}
    if r.returncode != 0:
        return {"_error": "git rc %s" % r.returncode}
    return em_parse_git(r.stdout.decode("utf-8", errors="replace"))


def em_out_dir(root, out_dir=None) -> Path:
    return Path(out_dir) if out_dir else Path(root) / EM_CFG["out"]


def em_register_unlocked(root, out_dir=None, use_git=False, now=None) -> dict:
    """掃自己的夾 → 登記冊(JSON)+ CSV + HTML;回摘要。前一份冊的 first_seen / git_added / changed_at 照留(只增不改)。"""
    root = Path(root)
    od = em_out_dir(root, out_dir)
    reg_p = od / ("%s_EngineMatrix_latest.json" % EM_CFG.get("stem", EM_CFG["system"]))
    prev = em_json(em_read(reg_p)) or {}
    rows_prev = prev.get("rows") or {}
    now = now or em_utc()
    nums = em_numbers(root)
    git = em_git_added(root) if use_git else {}
    files = em_files(root)
    tails = {}
    for p in files:
        m = EM_VER_RX.match(p.name)
        tails[m.group("fam")] = max(tails.get(m.group("fam"), -1), int(m.group("ver")))
    rows, new, changed = {}, [], []
    for p in files:
        m = EM_VER_RX.match(p.name)
        fam, ver, key = m.group("fam"), int(m.group("ver")), p.stem
        st = p.stat()
        old = rows_prev.get(key) or {}
        cached = old.get("bytes") == st.st_size and old.get("mtime_ns") == st.st_mtime_ns and old.get("sha12")
        sha = old["sha12"] if cached else em_sha12(p)
        num = nums.get(key) or {}
        row = {"system": EM_CFG["system"], "family": fam, "version": "v%04d" % ver, "tail": ver == tails[fam],
               "path": p.relative_to(root).as_posix(), "bytes": st.st_size, "mtime_ns": st.st_mtime_ns, "file_time": em_utc(st.st_mtime),
               "sha12": sha, "first_seen": old.get("first_seen") or now, "changed_at": old.get("changed_at"), "gone_at": None,
               "vcgc_code": num.get("code"), "vcgc_at": num.get("at"), "git_added": git.get(p.name) or old.get("git_added"), "state": "在"}
        if old.get("sha_prev"):
            row["sha_prev"] = old["sha_prev"]
        if not old:
            row["state"] = "新" if rows_prev else "在"
            new.append(key)
        elif old.get("sha12") and old["sha12"] != sha:
            row.update(state="變", changed_at=now, sha_prev=old["sha12"])
            changed.append(key)
        elif old.get("state") == "變":
            row["state"] = "變"                                   # 同版號改過內容 = 照實一直標著,不因下一輪沒再變就洗掉
        rows[key] = row
    gone = []
    for key, old in rows_prev.items():
        if key not in rows:
            r = dict(old, tail=False, state="消失", gone_at=old.get("gone_at") or now)
            if not old.get("gone_at"):
                gone.append(key)
            rows[key] = r
    live = [r for r in rows.values() if r["state"] != "消失"]
    tail_rows = [r for r in live if r["tail"]]
    unnum = sorted(r["family"] + "_" + r["version"] for r in tail_rows if not r.get("vcgc_code"))
    bad = sorted(k for k, r in rows.items() if r["state"] == "變")
    summary = {"system": EM_CFG["system"], "manager": EM_CFG["manager"], "updated_at": now, "families": len(tail_rows), "versions": len(live),
               "baseline": not rows_prev, "new": len(new) if rows_prev else 0, "changed_now": len(changed), "changed_total": len(bad),
               "gone_now": len(gone), "gone_total": sum(1 for r in rows.values() if r["state"] == "消失"),
               "tails_numbered": len(tail_rows) - len(unnum), "tails_unnumbered": unnum[:50], "versions_numbered": sum(1 for r in live if r.get("vcgc_code")),
               "git_dated": sum(1 for r in live if r.get("git_added")), "git_error": git.get("_error") if use_git else None,
               "new_list": new[:50] if rows_prev else [], "changed_list": bad[:50], "gone_list": gone[:50]}
    summary["lamp"] = "YELLOW" if (unnum or bad) else ("GREEN" if live else "GRAY")
    body = {"schema": "VIA.EngineMatrix.v1", "system": EM_CFG["system"], "own_dir": EM_CFG["dir"], "summary": summary,
            "rows": dict(sorted(rows.items()))}
    outs = [reg_p, od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"])), od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"]))]
    same = prev.get("rows") == body["rows"] and all(x.is_file() for x in outs)    # 逐版內容沒變且三個檔都在 → 不重寫
    summary["written"] = not same
    if not same:
        od.mkdir(parents=True, exist_ok=True)
        em_write(reg_p, json.dumps(body, ensure_ascii=False, indent=1))
        em_write(od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"])), em_csv(body), bom=True)
        em_write(od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"])), em_html(body))
    summary["files"] = {"json": str(reg_p), "csv": str(od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"]))),
                        "html": str(od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"])))}
    return summary


def em_sorted_rows(body: dict) -> list:
    return sorted(body["rows"].values(), key=lambda r: (r["family"], -int(r["version"][1:])))


def em_csv(body: dict) -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(EM_COLS)
    for r in em_sorted_rows(body):
        w.writerow([r.get(c) if r.get(c) is not None else "" for c in EM_COLS])
    return buf.getvalue()


def em_html(body: dict) -> str:
    import html as _h
    s = body["summary"]
    esc = lambda v: _h.escape("" if v is None else str(v))  # noqa: E731
    lamp_c = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "GRAY": "#57606a"}.get(s["lamp"], "#cf222e")
    trs = []
    for r in em_sorted_rows(body):
        cls = " ".join(x for x in ("tail" if r.get("tail") else "", {"新": "new", "變": "chg", "消失": "gone"}.get(r.get("state"), "")) if x)
        trs.append("<tr class='%s'>%s</tr>" % (cls, "".join("<td>%s</td>" % esc(r.get(c) if c != "tail" else ("尾版" if r.get("tail") else ""))
                                                       for c in EM_COLS if c not in ("system", "path"))))
    head = "".join("<th>%s</th>" % esc(c) for c in EM_COLS if c not in ("system", "path"))
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>%s 引擎矩陣</title><style>"
            ":root{--bg:#fff;--fg:#1f2328;--mut:#57606a;--line:#d0d7de;--alt:#f6f8fa}"
            "@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8d96a0;--line:#30363d;--alt:#161b22}}"
            "body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,'Microsoft JhengHei',sans-serif}"
            "h1{font-size:18px;margin:0 0 6px}.meta{color:var(--mut);margin-bottom:10px}.lamp{font-weight:700;color:%s}"
            ".bar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:8px 0}input{padding:6px 8px;border:1px solid var(--line);"
            "border-radius:6px;background:var(--bg);color:var(--fg);min-width:220px}.wrap{overflow:auto;border:1px solid var(--line);border-radius:6px}"
            "table{border-collapse:collapse;width:100%%;font-size:12.5px}th,td{padding:4px 8px;border-bottom:1px solid var(--line);white-space:nowrap;text-align:left}"
            "th{position:sticky;top:0;background:var(--alt)}tr:nth-child(even) td{background:var(--alt)}tr.tail td:nth-child(2){font-weight:700}"
            "tr.new td:last-child{color:#1a7f37;font-weight:700}tr.chg td:last-child{color:#cf222e;font-weight:700}tr.gone td{opacity:.55}"
            "</style></head><body><h1>%s 引擎矩陣 · %s</h1>"
            "<div class='meta'><span class='lamp'>%s</span> · 家族 %d · 版本 %d · 尾版已給號 %d / %d · git 建立時間 %d 版 · 本輪 新 %d · 同版號內容變 %d · 消失 %d · 更新 %s</div>"
            "<div class='bar'><input id='q' placeholder='篩選(家族 / 版號 / 號)' oninput='f()'><label><input type='checkbox' id='t' onchange='f()'> 只看尾版</label></div>"
            "<div class='wrap'><table><thead><tr>%s</tr></thead><tbody id='b'>%s</tbody></table></div>"
            "<script>function f(){var q=document.getElementById('q').value.toLowerCase(),t=document.getElementById('t').checked;"
            "document.querySelectorAll('#b tr').forEach(function(r){r.style.display=((!t||r.classList.contains('tail'))&&r.textContent.toLowerCase().indexOf(q)>=0)?'':'none'})}</script>"
            "</body></html>") % (esc(s["system"]), lamp_c, esc(s["system"]), esc(s["manager"]), esc(s["lamp"]), s["families"], s["versions"],
                                 s["tails_numbered"], s["families"], s["git_dated"], s["new"], s["changed_total"], s["gone_now"], esc(s["updated_at"]), head, "".join(trs))



# ────────────────── 引擎矩陣:同時執行不互撞(PR 640 · Codex P2)──────────────────
# 舊版每個行程都寫同一個 `<檔>.tmp`,兩個行程同時更新登記冊時,後改名的那個會 FileNotFoundError。
# 本版:暫存檔名帶行程號 + 亂數(各寫各的)· 登記冊的「讀 → 算 → 寫」整段用鎖檔排隊(O_EXCL 建檔,跨行程 / 跨執行緒都有效)。
# 自動登記最多等 EM_AUTO_WAIT 秒,等不到就這一輪不登(別的行程正在登同一份),不擋主動詞;
# engine-matrix 動詞最多等 EM_LOCK_WAIT 秒,還在忙就照實回 YELLOW(rc 2)不崩。(v0180 起鎖改作業系統檔案鎖,見下方;EM_LOCK_STALE 不再使用)
EM_LOCK_WAIT, EM_AUTO_WAIT, EM_LOCK_STALE = 30.0, 2.0, 120.0


def em_lock_path(root, out_dir=None) -> Path:
    return em_out_dir(root, out_dir) / ("%s_EngineMatrix.lock" % EM_CFG.get("stem", EM_CFG["system"]))


def em_unlink(p) -> bool:
    try:
        Path(p).unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        EM_STATE["unlink_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:120])
        return False




def em_write(p: Path, text: str, bom: bool = False) -> None:
    """原子寫入:暫存檔名每個行程 / 每次都不同,寫完 os.replace;失敗時暫存檔照清。"""
    p = Path(p)
    tmp = p.with_name("%s.%d.%s.tmp" % (p.name, os.getpid(), uuid.uuid4().hex[:8]))
    try:
        tmp.write_text(text, encoding="utf-8-sig" if bom else "utf-8", newline="\n")
        os.replace(tmp, p)
    finally:
        em_unlink(tmp)






def em_age(p):
    """前版名稱(TAILAPI 轉接):檔案多久沒改(秒);不在 → None。v0180 起排隊不再看鎖檔年紀。"""
    try:
        return time.time() - Path(p).stat().st_mtime
    except OSError:
        return None


def em_safe_selftest(chk, register, cmd, auto, state: dict, setwait) -> None:
    """前版名稱(TAILAPI 轉接):改跑作業系統檔案鎖自測。"""
    return em_oslock_selftest(chk, register, cmd, auto, state, setwait)


def em_default_wait() -> float:
    return EM_LOCK_WAIT


# ────────────────── 引擎矩陣:作業系統檔案鎖(PR 641 · Codex P2)──────────────────
# 前版用「O_EXCL 建鎖檔 + 老過 120 秒就刪」排隊:兩個呼叫端同時判定同一個殘留鎖時,後刪的那個會刪掉先到者剛建的新鎖,
# 兩邊同時進入登記冊的讀 → 算 → 寫(更新會互相蓋掉);finally 也可能刪到已經不是自己的鎖。
# 本版改用作業系統的檔案鎖:POSIX fcntl.flock(LOCK_EX | LOCK_NB)· Windows msvcrt.locking(LK_NBLCK)。
#   · 持有者結束(含被砍)時作業系統自動放鎖 → 不會再有殘留鎖,也就不需要「過期就刪」。
#   · 鎖檔本身留著、從不刪 → 不可能刪到別人的鎖;放鎖只能經自己的檔案控制碼 → 只放自己的。
#   · 同一行程不同執行緒各自開檔,鎖彼此照樣互斥(flock 以開啟的檔案描述為單位;Windows 以控制碼為單位)。
EM_CHILD_LOCK_CODE = r'''
import os, sys, time
fh = open(sys.argv[1], "a+b")
if os.name == "nt":
    import msvcrt
    fh.seek(0)
    msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
else:
    import fcntl
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
print("READY", flush=True)
time.sleep(120)
'''


def em_try_lock(fh) -> bool:
    """非阻塞拿鎖:拿到 True;別人持有 False。"""
    if os.name == "nt":
        import msvcrt
        fh.seek(0)
        try:
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False


def em_unlock(fh) -> None:
    if os.name == "nt":
        import msvcrt
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@contextlib.contextmanager
def em_locked(lock: Path, wait=None, stale=None):
    """作業系統檔案鎖排隊:拿到才往下;等超過 wait 秒 → TimeoutError。鎖檔從不刪(stale 參數只為相容前版呼叫,不再使用)。"""
    wait = em_default_wait() if wait is None else wait
    lock = Path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock, "a+b")
    try:
        t0 = time.time()
        while not em_try_lock(fh):
            if time.time() - t0 > wait:
                raise TimeoutError("另一個行程正在更新引擎登記冊(%s),等了 %.0f 秒" % (lock.name, wait))
            time.sleep(0.05)
        try:
            yield lock
        finally:
            em_unlock(fh)
    finally:
        fh.close()


def em_oslock_selftest(chk, register, cmd, auto, state: dict, setwait) -> None:
    """作業系統檔案鎖自測(暫存夾)。register / cmd / auto = 本版的登記 · 動詞 · 自動;setwait(lock, auto) 改等待秒數並回舊值。"""
    import io
    import subprocess as _sp
    import threading
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        own.mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        (own / (pre + "ENG931_Theta_v0100.py")).write_text("t = 1\n", encoding="utf-8")
        od0 = em_out_dir(root)
        od0.mkdir(parents=True, exist_ok=True)
        (od0 / "probe.json.tmp").write_text("舊版固定暫存名(別的行程的)", encoding="utf-8")
        em_write(od0 / "probe.json", '{"ok": 1}')
        left = [x.name for x in od0.iterdir() if x.name.startswith("probe.json.") and x.name != "probe.json.tmp"]
        chk("L0 暫存檔名每個行程 / 每次都不同(照前版):寫完只剩正檔 · 不碰別人的 probe.json.tmp · 自己的暫存不殘留",
            em_read(od0 / "probe.json") == '{"ok": 1}' and (od0 / "probe.json.tmp").is_file() and left == [], left)
        (od0 / "probe.json.tmp").unlink()
        (od0 / "probe.json").unlink()
        lockp = em_lock_path(root)
        lockp.parent.mkdir(parents=True, exist_ok=True)
        lockp.write_bytes(b"")
        ino0 = lockp.stat().st_ino
        inside, peak, errs = [0], [0], []
        guard = threading.Lock()

        def crowd():
            try:
                for _ in range(15):
                    with em_locked(lockp, wait=20):
                        with guard:
                            inside[0] += 1
                            peak[0] = max(peak[0], inside[0])
                        time.sleep(0.002)
                        with guard:
                            inside[0] -= 1
            except Exception as exc:  # noqa: BLE001 — 自測要收集每條執行緒的例外再判
                errs.append("%s:%s" % (type(exc).__name__, exc))
        th = [threading.Thread(target=crowd) for _ in range(6)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        chk("L1 互斥:6 條執行緒 × 15 次搶同一把鎖,任何時刻最多 1 條在裡面 · 零例外 · 鎖檔從沒被刪過(同一個檔)",
            peak[0] == 1 and not errs and lockp.is_file() and (not ino0 or lockp.stat().st_ino == ino0), (peak[0], errs[:2]))
        lockp.write_bytes(b"crashed-run residue")
        t0 = time.time()
        with em_locked(lockp, wait=0.5):
            got = time.time() - t0
        chk("L2 殘留的鎖檔(沒人持有)不擋路:立刻拿到(%.2f 秒)· 不需要「過期就刪」" % got, got < 0.4)
        child = _sp.Popen([sys.executable, "-c", EM_CHILD_LOCK_CODE, str(lockp)], stdout=_sp.PIPE, stdin=_sp.DEVNULL, text=True)
        try:
            ready = (child.stdout.readline() or "").strip()
            blocked = False
            try:
                with em_locked(lockp, wait=0.4):
                    blocked = False
            except TimeoutError:
                blocked = True
            child.kill()
            child.wait(timeout=30)
            t0 = time.time()
            try:
                with em_locked(lockp, wait=10):
                    freed = time.time() - t0
            except TimeoutError:
                freed = 99.0
        finally:
            if child.poll() is None:
                child.kill()
            if child.stdout:
                child.stdout.close()
        chk("L3 跨行程:別的行程持鎖時這邊等不到(TimeoutError)· 那個行程被砍掉後作業系統自動放鎖,這邊 %.2f 秒內拿到(不會有殘留鎖)" % freed,
            ready == "READY" and blocked and freed < 5, (ready, blocked, freed))
        fh = open(lockp, "a+b")
        held = em_try_lock(fh)
        old = setwait(0.3, 0.2)
        buf, buf2 = io.StringIO(), io.StringIO()
        keep = dict(state)
        try:
            with contextlib.redirect_stdout(buf):
                rc = cmd(["--no-git"], root)
            with contextlib.redirect_stdout(buf2):
                auto(root)
            auto_err = state.get("auto_error") or ""
        finally:
            setwait(*old)
            state.clear()
            state.update(keep)
            if held:
                em_unlock(fh)
            fh.close()
        chk("L4 鎖一直被別人持有:engine-matrix 照實回 YELLOW rc 2 + 說「另一個行程正在更新」(不崩)· 自動登記一個字不印、只記下來、不擋",
            held and rc == 2 and "另一個行程正在更新" in buf.getvalue() and buf2.getvalue() == "" and "TimeoutError" in auto_err,
            (held, rc, buf.getvalue()[-160:], buf2.getvalue()[:80], auto_err))
        errs2 = []

        def worker(i):
            try:
                (own / ("%sENG94%d_Iota_v0100.py" % (pre, i))).write_text("i = %d\n" % i, encoding="utf-8")
                register(root, wait=30)
            except Exception as exc:  # noqa: BLE001 — 自測要收集每條執行緒的例外再判
                errs2.append("%s:%s" % (type(exc).__name__, exc))
        th = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in th:
            t.start()
        for t in th:
            t.join()
        od = em_out_dir(root)
        final = em_json(em_read(od / ("%s_EngineMatrix_latest.json" % EM_CFG.get("stem", EM_CFG["system"])))) or {}
        names = set((final.get("rows") or {}).keys())
        junk = [x.name for x in od.iterdir() if x.name.endswith(".tmp")]
        chk("L5 8 條同時登記(各加一版再登):零例外 · 登記冊 9 版全在(沒有誰的更新被蓋掉)· 不留暫存檔 · 鎖檔還是同一個",
            not errs2 and all("%sENG94%d_Iota_v0100" % (pre, i) in names for i in range(8)) and len(names) == 9 and not junk
            and (not ino0 or lockp.stat().st_ino == ino0), (errs2[:3], len(names), junk))



def em_register(root, out_dir=None, use_git=False, now=None, wait=None) -> dict:
    """登記冊的「讀 → 算 → 寫」整段排隊(同時執行不互撞 · 不丟別人的更新)。"""
    with em_locked(em_lock_path(root, out_dir), wait=wait):
        return em_register_unlocked(root, out_dir=out_dir, use_git=use_git, now=now)


def em_setwait(lock_wait, auto_wait) -> tuple:
    """自測用:暫時改等待秒數,回舊值。"""
    global EM_LOCK_WAIT, EM_AUTO_WAIT
    old = (EM_LOCK_WAIT, EM_AUTO_WAIT)
    EM_LOCK_WAIT, EM_AUTO_WAIT = lock_wait, auto_wait
    return old


def em_auto(root) -> dict | None:
    """每次本管理器執行時的靜默登記(不印任何東西 · 不擋主動詞);失敗只記在 EM_STATE。"""
    try:
        EM_STATE["auto"] = em_register(root, wait=EM_AUTO_WAIT)   # 別的行程正在登 → 最多等 2 秒,等不到這一輪不登
    except Exception as exc:  # noqa: BLE001 — 自動登記壞了不擋主流程,照實記下,engine-matrix 動詞會顯示
        EM_STATE["auto_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:160])
    return EM_STATE["auto"]


def em_cmd(args: list, root) -> int:
    """`engine-matrix [--json] [--no-git] [--open]`:登記並印矩陣(每家族一列:尾版 · 版數 · 號 · 時間);燈照 L16(0 綠 · 2 黃)。"""
    try:
        s = em_register(root, use_git="--no-git" not in args)
    except TimeoutError as exc:
        print("[%s] 引擎矩陣 YELLOW · %s · 等一下再跑一次" % (EM_CFG["manager"], exc))
        return 2
    if "--json" in args:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        body = em_json(em_read(s["files"]["json"])) or {"rows": {}}
        print("  %-48s %-6s %4s  %-18s %-25s %-25s %s" % ("家族", "尾版", "版數", "VCGC 號", "版本建立(git)", "首次登記", "狀態"))
        fams = {}
        for r in body["rows"].values():
            if r.get("state") != "消失":
                fams.setdefault(r["family"], []).append(r)
        for fam in sorted(fams):
            rs = fams[fam]
            t = next(x for x in rs if x.get("tail"))
            flag = "變" if any(x.get("state") == "變" for x in rs) else ("新" if t.get("state") == "新" else "")
            print("  %-48s %-6s %4d  %-18s %-25s %-25s %s" % (fam[:48], t["version"], len(rs), t.get("vcgc_code") or "待號",
                                                             t.get("git_added") or "—", t.get("first_seen") or "—", flag))
        print("[%s] 引擎矩陣 %s · 家族 %d · 版本 %d · 尾版已給號 %d / %d · git 建立時間 %d 版%s · 本輪 新 %d · 同版號內容變 %d · 消失 %d"
              % (EM_CFG["manager"], s["lamp"], s["families"], s["versions"], s["tails_numbered"], s["families"], s["git_dated"],
                 ("(git:%s)" % s["git_error"]) if s.get("git_error") else "", s["new"], s["changed_total"], s["gone_now"]))
        if s["tails_unnumbered"]:
            print("  [待號] 尾版還沒有 VCGC 號:" + " · ".join(s["tails_unnumbered"][:8]) + (" …" if len(s["tails_unnumbered"]) > 8 else ""))
        if s["changed_list"]:
            print("  [變] 同版號內容被改過(版號律:要出新版號):" + " · ".join(s["changed_list"][:8]))
        print("  [檔] %s · %s · %s" % (s["files"]["json"], s["files"]["csv"], s["files"]["html"]))
    if "--open" in args:
        import webbrowser
        webbrowser.open(Path(s["files"]["html"]).as_uri())
    return 0 if s["lamp"] == "GREEN" else 2


def em_selftest(chk) -> None:
    """引擎矩陣自測(暫存夾,不碰真倉的登記冊)。chk(name, cond, note)。"""
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        (own / "intake").mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        a0, a1, b0 = own / (pre + "ENG901_Alpha_v0100.py"), own / (pre + "ENG901_Alpha_v0101.py"), own / (pre + "ENG902_Beta_v0100.py")
        a0.write_text("x = 1\n", encoding="utf-8")
        a1.write_bytes(b"x = 2\r\n")
        b0.write_text("y = 1\n", encoding="utf-8")
        (own / "intake" / (pre + "ENG903_Skip_v0100.py")).write_text("z\n", encoding="utf-8")
        (own / "notmine_v0100.py").write_text("n\n", encoding="utf-8")
        nb = root / "supportive modules" / "registry" / "VIA_NumberBooks"
        nb.mkdir(parents=True)
        (nb / "VIA_NumberBook_ENG_v0100.jsonl").write_text(json.dumps({"code": "VIA-X-ENG001", "name": pre + "ENG901_Alpha_v0101",
                                                                      "numbered_at": "2026-11-14 10:00:00 +0000"}) + "\n", encoding="utf-8")
        s1 = em_register(root, now="2026-11-14 00:00:00 +00:00")
        body1 = em_json(em_read(s1["files"]["json"]))
        r_a1 = body1["rows"][pre + "ENG901_Alpha_v0101"]
        chk("E1 首次登記:只收自己的夾 · 自己前綴 · 有版號(intake / 別人的檔不收)· 家族 2 · 版本 3 · 尾版 Alpha v0101 有號 · Beta 待號 → YELLOW · "
            "CSV / HTML 都寫出 · 雜湊 CRLF 與 LF 同值",
            s1["baseline"] and s1["families"] == 2 and s1["versions"] == 3 and r_a1["tail"] and r_a1["vcgc_code"] == "VIA-X-ENG001"
            and s1["tails_unnumbered"] == [pre + "ENG902_Beta_v0100"] and s1["lamp"] == "YELLOW"
            and Path(s1["files"]["csv"]).is_file() and "ENG901_Alpha" in em_read(s1["files"]["html"])
            and r_a1["sha12"] == hashlib.sha256(b"x = 2\n").hexdigest()[:12] and r_a1["first_seen"] == "2026-11-14 00:00:00 +00:00", s1)
        s1b = em_register(root, now="2026-11-14 00:30:00 +00:00")
        b0.write_text("y = 2  # 同版號改內容\n", encoding="utf-8")
        a2 = own / (pre + "ENG901_Alpha_v0102.py")
        a2.write_text("x = 3\n", encoding="utf-8")
        a0.unlink()
        s2 = em_register(root, now="2026-11-15 00:00:00 +00:00")
        body2 = em_json(em_read(s2["files"]["json"]))
        rows2 = body2["rows"]
        chk("E2 第二輪:沒變就不重寫 · 新版 Alpha v0102 記「新」並成尾版(待號)· 同版號改內容 Beta v0100 記「變」+ changed_at · 刪掉的 v0100 記「消失」+ gone_at · "
            "首次登記時間照留",
            s1b["written"] is False and s2["new"] == 1 and rows2[pre + "ENG901_Alpha_v0102"]["state"] == "新" and rows2[pre + "ENG901_Alpha_v0102"]["tail"]
            and rows2[pre + "ENG902_Beta_v0100"]["state"] == "變" and rows2[pre + "ENG902_Beta_v0100"]["changed_at"] == "2026-11-15 00:00:00 +00:00"
            and rows2[pre + "ENG901_Alpha_v0100"]["state"] == "消失" and rows2[pre + "ENG901_Alpha_v0100"]["gone_at"] == "2026-11-15 00:00:00 +00:00"
            and rows2[pre + "ENG902_Beta_v0100"]["first_seen"] == "2026-11-14 00:00:00 +00:00" and s2["changed_list"] == [pre + "ENG902_Beta_v0100"], s2)
        s3 = em_register(root, now="2026-11-16 00:00:00 +00:00")
        rows3 = em_json(em_read(s3["files"]["json"]))["rows"]
        chk("E3 第三輪:「變」照實一直標著(不因下一輪沒再改就洗掉)· 消失的不重複算",
            rows3[pre + "ENG902_Beta_v0100"]["state"] == "變" and s3["gone_now"] == 0 and s3["gone_total"] == 1, s3)
        g = em_parse_git("@@2026-11-14T23:05:00+08:00\nVeritasIntelligenceAnalytics/x/%sENG901_Alpha_v0102.py\n\n"
                         "@@2026-11-01T01:00:00+00:00\nVeritasIntelligenceAnalytics/x/%sENG901_Alpha_v0102.py\nVeritasIntelligenceAnalytics/x/%sENG902_Beta_v0100.py\n"
                         % (pre, pre, pre))
        chk("E4 git 建立時間:+08:00 換成 UTC · 同一檔多次加入取最早那次", g.get(pre + "ENG902_Beta_v0100.py") == "2026-11-01 01:00:00 +00:00"
            and g.get(pre + "ENG901_Alpha_v0102.py") == "2026-11-01 01:00:00 +00:00" and em_iso_to_utc("2026-11-14T23:05:00+08:00") == "2026-11-14 15:05:00 +00:00", g)
        buf = io.StringIO()
        keep = dict(EM_STATE)
        with contextlib.redirect_stdout(buf):
            em_auto(root)
        auto_ok = buf.getvalue() == "" and EM_STATE.get("auto_error") is None and isinstance(EM_STATE.get("auto"), dict)
        EM_STATE.update(keep)
        chk("E5 自動登記:一個字都不印(不弄亂 --json 等輸出)· 不擋主流程", auto_ok, buf.getvalue()[:200])


def sm_cmd(verb: str, args: list, root: Path) -> int:
    if verb in V73_VERBS:
        return sm_cmd_v0173(verb, args, root)
    if verb in V74_VERBS + V74_EXTRA:
        return sm_cmd_v0174(verb, args, root)
    if verb == "engine-matrix":
        return em_cmd(args, root)
    if verb == "route":
        return sm_route_cmd(args, root)
    as_json = "--json" in args
    if verb == "help":
        print(f"{SM_TAG} · {SM_CONFIG['system']} 自己的入口(對等 · 不管別人 · 不被別人管)")
        print("  標準動詞(本版):" + " · ".join(SM_NATIVE))
        print("  資料平面(v0183 · 轉 VDF_MDL020):scope · inputs · parquet status | sync | plan | export --to <夾|onedrive|gdrive|dropbox>")
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
            names = set(z.namelist())
            for name, h in sums.items():
                key = name if name in names else name.replace("\\", "/")   # v0175 在 Windows 記反斜線;zip 內一律正斜線
                if key not in names or hashlib.sha256(z.read(key)).hexdigest() != h:
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
            rel = p.relative_to(root).as_posix() if p.is_relative_to(root) else "_manager/" + p.name
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
    structure = "GREEN" if cont and not noeng and own["lamp"] == "GREEN" else "YELLOW"
    known = [{"step": s.get("code"), "hand": (s.get("known_open") or {}).get("hand"), "why": (s.get("known_open") or {}).get("why")}
             for s in steps if isinstance(s, dict) and s.get("known_open")]
    ai_open = [k["step"] for k in known if k["hand"] != "operator"]
    acceptance = "OPEN" if ai_open else ("CLOSED_WITH_OPERATOR_ITEMS" if known else "UNVERIFIED")
    # 本管理器只驗冊結構(編號連續 · 步引擎在位 · 副本未漂移);實測證據(evidence_rule:step / self / chain / git)由 SDD 驗證器判,
    # 這裡不判 → 不自報驗收綠(AGENTS.md 第 6 條:未測保留未完成)。結構燈另列 structure。
    return {"lamp": "YELLOW", "structure": structure, "acceptance": acceptance, "known_open": known[:10], "known_open_ai": ai_open[:10],
            "evidence": "未判(SDD 驗證器的手)", "workflows": len(wf), "steps": len(steps), "codes_continuous": cont,
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
    """視覺鎖定:VCGC 鎖站 kit 的色票(只讀資料);kit 名稱 → 本頁用途完整對應;缺就用同色系預設。"""
    p = root / "docs" / "handoff" / "ai" / "VIA_WorkbenchLock_kit_latest.json"
    t = {"bg": "#f2f1ec", "panel": "#ffffff", "fg": "#33403f", "muted": "#6b6860", "accent": "#1b1a17", "line": "#dbd9d3", "row": "#ebe9e3",
         "green": "#3d7a52", "yellow": "#6f5c31", "red": "#9e2b25", "g_bg": "#e6efec", "y_bg": "#f2ecdd", "r_bg": "#f3e7e6"}
    kit_map = {"--bg": "bg", "--white": "panel", "--ink": "fg", "--muted": "muted", "--title": "accent", "--line": "line", "--row": "row",
               "--green": "green", "--y-ink": "yellow", "--r-ink": "red", "--g-bg": "g_bg", "--y-bg": "y_bg", "--r-bg": "r_bg"}
    try:
        k = json.loads(p.read_text(encoding="utf-8"))
        for key, val in (k.get("tokens") or {}).items():
            if key in kit_map and isinstance(val, str) and val.startswith("#"):
                t[kit_map[key]] = val
        t["_source"] = f"{p.name}(契約 {k.get('ui_contract_version', '—')} · {k.get('token_count', '—')} 色票)"
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
    links = [('自建工作台(五系統)', 'VIA_Reports/workbench/VIA_Workbench_Hub_latest.html'), ('VDF 工作台頁', 'VIA_Reports/workbench/VIA_Workbench_VDF_latest.html'), ('VDF 擷取矩陣', 'VIA_Reports/vdf/FETCH_MATRIX_latest.html'), ('資料庫狀態矩陣', 'VIA_Reports/vdf/DB_STATUS_MATRIX_latest.html'), ('VDF 管理範圍', 'VIA_Reports/vdf/VDF_SCOPE_latest.html'), ('Parquet 湖狀態', 'VIA_Reports/vdf_lake/LAKE_STATUS_latest.json'), ('引用圖', 'VIA_Reports/vdf/manager/graph/VDF_GRAPH_latest.json'), ('安裝計畫', 'VIA_Reports/vdf/manager/install/VDF_InstallPlan_latest.json'), ('OmniRoute / MCP 設定', 'VIA_Reports/vdf/manager/omniroute/VDF_OmniRoute_latest.json')]
    here = v73_out(root)
    links = [(lb, (max((str(q.relative_to(root)) for q in root.glob(rel)), default=rel) if "*" in rel else rel)) for lb, rel in links]   # 萬用字元 = 取最新一份
    nav = "<nav>" + "".join(
        (f"<a href='{_h.escape(os.path.relpath(root / rel, here).replace(os.sep, '/'))}'>{_h.escape(label)}</a>" if (root / rel).is_file()
         else f"<a class='off' title='檔還沒產生'>{_h.escape(label)}(未產生)</a>") for label, rel in links) + "</nav>"
    css = (f"body{{background:{t['bg']};color:{t['fg']};font:14px/1.5 system-ui,'Noto Sans TC',sans-serif;margin:0;padding:16px}}"
           f"h1{{font-size:1.3rem;color:{t['accent']}}}nav a{{display:inline-block;margin:0 .6rem .4rem 0;padding:.25rem .6rem;border:1px solid {t['line']};border-radius:6px;color:{t['fg']};background:{t['panel']};text-decoration:none}}nav a.off{{color:{t['muted']};border-style:dashed}}tr:nth-child(even) td{{background:{t['row']}}}h2{{font-size:1.05rem;margin-top:1.4rem}}table{{border-collapse:collapse;width:100%;background:{t['panel']}}}"
           f"td,th{{border-bottom:1px solid {t['line']};padding:4px 8px;text-align:left;vertical-align:top}}th{{color:{t['muted']};font-size:.8rem}}"
           ".wrap{overflow-x:auto}")
    page = (f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>VDF 系統管理器矩陣</title><style>{css}</style></head><body>"
            f"<h1>VDF 系統管理器 {SM_VERSION} · 能力與狀態矩陣</h1><p style='color:{t['muted']}'>{sm_utc()} · 視覺色票 {_h.escape(t['_source'])} · 只讀產生</p>{nav}"
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


def selftest() -> int:
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
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"]
        (d / "SSOT").mkdir(parents=True)
        (d / "SSOT" / "VDF_Regex_SSOT_v0100.json").write_text('{"a":1}')
        (d / "VDF_Demo_SSOT_v0100.json").write_text('{"b":2}')
        real = sm_engines
        sm_engines = lambda r: {}
        try:
            bk = v73_backup(tr)
            out = v73_out(tr, "backup")
            zp = out / Path(bk["zip"]).name
            with _zipfile.ZipFile(zp) as z:
                nm = z.namelist()
                sums = z.read("SHA256SUMS").decode()
            ok_names = not any("\\" in x for x in nm + sums.split()) and "functional modules/VDF/SSOT/VDF_Regex_SSOT_v0100.json" in nm
            legacy = out / "VDF_Backup_99999999T999999Z.zip"   # 排序在最後 = check 會挑這份
            with _zipfile.ZipFile(zp) as zi, _zipfile.ZipFile(legacy, "w") as zo:
                for x in zi.namelist():
                    zo.writestr(x, zi.read(x) if x != "SHA256SUMS" else sums.replace("/", "\\").encode())
            c1 = v73_backup(tr, check_only=True)
            lines = sums.splitlines() + ["0" * 64 + "  functional modules/VDF/VDF_Gone_v0100.json"]
            with _zipfile.ZipFile(zp) as zi, _zipfile.ZipFile(legacy, "w") as zo:
                for x in zi.namelist():
                    zo.writestr(x, zi.read(x) if x != "SHA256SUMS" else ("\n".join(lines) + "\n").encode())
            c2 = v73_backup(tr, check_only=True)
        finally:
            sm_engines = real
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        d = tr / SM_CONFIG["dir"] / "SSOT"
        d.mkdir(parents=True)
        (tr / "supportive modules" / "registry").mkdir(parents=True)
        (tr / "supportive modules" / "registry" / "SRC_v0100.json").write_text("{}")
        def wfbook(steps):
            return json.dumps({"source": "supportive modules/registry/SRC_v0100.json", "source_sha256": hashlib.sha256(b"{}").hexdigest(),
                               "body": {"workflows": [{"code": "VDF-WKF001", "steps": steps}]}})
        (d / "VDF_Workflow_SSOT_v0100.json").write_text(wfbook([{"code": "VDF-WKF001-STP001", "engine": "operator"}]))
        s1 = v73_sdd(tr)
        (d / "VDF_Workflow_SSOT_v0100.json").write_text(wfbook([{"code": "VDF-WKF001-STP001", "engine": "operator",
                                                              "known_open": {"hand": "ai", "why": "主機 DB 未實測"}}]))
        s2 = v73_sdd(tr)
        (d / "VDF_Workflow_SSOT_v0100.json").write_text(wfbook([{"code": "VDF-WKF001-STP001", "engine": "operator",
                                                              "known_open": {"hand": "operator", "why": "裝件"}}]))
        s3 = v73_sdd(tr)
    ck("⑮ sdd 只驗結構不冒充驗收:結構全過也 YELLOW(UNVERIFIED)· known_open ai 手 → OPEN · operator 手 → CLOSED_WITH_OPERATOR_ITEMS",
       s1["structure"] == "GREEN" and s1["lamp"] == "YELLOW" and s1["acceptance"] == "UNVERIFIED"
       and s2["acceptance"] == "OPEN" and s2["known_open_ai"] == ["VDF-WKF001-STP001"]
       and s3["acceptance"] == "CLOSED_WITH_OPERATOR_ITEMS" and s3["lamp"] == "YELLOW", (s1, s2, s3))
    ck("⑭ v0176 備份 zip 內檔名與 SHA256SUMS 一律正斜線(含 SSOT 子夾)· 舊備份反斜線名 check 照樣 GREEN · 缺件 RED 不崩",
       ok_names and "as_posix()" in SM_HERE.read_text(encoding="utf-8") and c1["lamp"] == "GREEN" and c2["lamp"] == "RED"
       and c2["bad"] == ["functional modules/VDF/VDF_Gone_v0100.json"], (nm, c1, c2))
    em_selftest(ck)
    em_oslock_selftest(ck, em_register, em_cmd, em_auto, EM_STATE, em_setwait)
    fams_em = {EM_VER_RX.match(p.name).group("fam") for p in em_files(root)}
    ck("⑯ 真倉:引擎矩陣與 engines 動詞同一批家族(%d)· engine-matrix 是原生動詞 · 主程式每次自動登記(自測除外)" % len(fams_em),
       fams_em == set(sm_engines(root)) and "engine-matrix" in SM_NATIVE and "em_auto(root)" in SM_HERE.read_text(encoding="utf-8"))
    route_selftest(ck, root)
    dbmx_selftest(ck, root)
    dp_selftest(ck, root)
    n = sum(ok)
    print(f"[計] {SM_TAG} 全原生 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


SM_NATIVE = SM_NATIVE + tuple(v for v in V74_VERBS + V74_EXTRA if v not in SM_NATIVE)


def route_selftest(ck, root: Path) -> None:
    """v0181 轉交直達自測:靜態原生動詞 = 各版執行期的 SM_NATIVE · 真倉路線 · 真跑同輸出 · 少掉的子行程 · 認不出就停。"""
    global SM_HERE
    me = sm_static_card(SM_HERE)
    ck("R1 本檔靜態算出的原生動詞 = 執行期 SM_NATIVE(%d 個)· 本檔是標準轉交者" % len(SM_NATIVE),
       me["standard"] and me["natives"] == tuple(SM_NATIVE), (me["why"], me["natives"]))
    d = root / SM_CONFIG["dir"]
    olds = sorted((p for p in d.glob(SM_CONFIG["manager_family"] + "_v*.py") if 169 <= sm_vnum(p) < sm_vnum(SM_HERE)), key=sm_vnum)
    probe = "import json,runpy,sys;g=runpy.run_path(sys.argv[1],run_name='vdf_sm_prior_probe');print(json.dumps(list(g['SM_NATIVE'])))"   # 只載 VDF 自己的前版 · 子行程 · 只在自測
    bad = []
    for p in olds:
        card = sm_static_card(p)
        r = subprocess.run([sys.executable, "-c", probe, str(p)], capture_output=True, text=True, timeout=120,
                           env=dict(sm_child_env(), VIA_FROM_VCGC="YES"), cwd=tempfile.gettempdir())
        try:
            rt = tuple(json.loads(r.stdout.strip().splitlines()[-1]))
        except (ValueError, IndexError):
            rt = None
        if not card["standard"] or card["natives"] != rt:
            bad.append((p.name, card["why"], card["natives"] == rt))
    ck("R2 前版 v0169 … v%04d 共 %d 支:每支都認得出是標準轉交者 · 靜態原生動詞 = 子行程載入後的 SM_NATIVE" % (sm_vnum(SM_HERE) - 1, len(olds)),
       olds and not bad, bad[:3])
    routes = {v: sm_route(v.split(), root) for v in ("engine list", "engine launch", "db check", "refill --home x", "universe xcheck", "fetch run", "ui")}
    tg = {v: (r["target"].name if r["target"] else None, r["skipped"]) for v, r in routes.items()}
    term = {t for t, _ in tg.values()}
    ck("R3 真倉路線:ActivateVDF 會叫的 7 個轉交動詞全落在同一支(%s)· 每次省 %s 層" % (sorted(term), sorted({s for _, s in tg.values()})),
       len(term) == 1 and None not in term and all(s >= 1 for _, s in tg.values()), tg)
    nat = sm_route(["engines"], root)
    leg = sm_route(["status"], root)
    ck("R4 第一個前版就會自己處理的動詞(--legacy engines · status)→ 停在前一版(省 0 層;等同前版逐層)",
       nat["target"] is not None and nat["skipped"] == 0 and leg["skipped"] == 0, (nat["why"], leg["why"]))
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        dd = tr / SM_CONFIG["dir"]
        dd.mkdir(parents=True)
        fam = SM_CONFIG["manager_family"]
        (dd / (fam + "_v0001.py")).write_text("def main():\n    return 0\n", encoding="utf-8")
        (dd / (fam + "_v0003.py")).write_text(SM_HERE.read_text(encoding="utf-8"), encoding="utf-8")
        (dd / (fam + "_v0002.py")).write_text(SM_HERE.read_text(encoding="utf-8") + "\nSM_NATIVE.append(\"engine\")\n", encoding="utf-8")
        keep = SM_HERE
        try:
            SM_HERE = dd / (fam + "_v0004.py")
            SM_HERE.write_text(keep.read_text(encoding="utf-8"), encoding="utf-8")
            r = sm_route(["engine", "list"], tr)
        finally:
            SM_HERE = keep
    ck("R5 前版認不出(模組層在呼叫裡改 SM_NATIVE · 靜態算不準)→ 停在那支照它自己轉(不猜、不跳過)",
       r["target"] is not None and r["target"].name.endswith("_v0002.py") and r["skipped"] == 1 and "靜態算不準" in r["hops"][-1]["why"] and r["hops"][0]["standard"], r)
    import time as _t

    def run(extra_env=None):                                     # 自己跑自己(本檔)· 同一個行程境
        env = dict(os.environ, VIA_FROM_VCGC="YES", **(extra_env or {}))
        t0 = _t.time()
        p = subprocess.run([sys.executable, str(Path(__file__).resolve()), "engine", "list", "--json"], capture_output=True, text=True, timeout=600, env=env)
        return p.returncode, p.stdout, round(_t.time() - t0, 1)
    run()                                                        # 暖身一次:每版起跑會靜默登記引擎矩陣,第一次跑可能改到登記狀態
    rc_old, out_old, t_old = run({"VIA_VDF_SM_DIRECT": "0"})
    rc_new, out_new, t_new = run()
    ck("R6 真跑 engine list --json:直達與逐層(VIA_VDF_SM_DIRECT=0)rc 相同 · 輸出逐字相同 · 直達 %.1f 秒 / 逐層 %.1f 秒" % (t_new, t_old),
       rc_new == rc_old == 0 and out_new == out_old and out_new.strip().startswith("{"), (rc_new, rc_old, out_new[:120], out_old[:120]))

# ══════════════════════════ v0182:資料庫狀態矩陣頁(VDF-REQ028)══════════════════════════
DBMX_GLOB = "VDF_MDL019_DBStatusMatrix_v*.py"


def sm_db_matrix(root: Path, quiet: bool = False) -> dict:
    """db check / db verify 跑完 → 子行程叫 VDF_MDL019 尾版 render → 資料庫頁 DB_CHECK_latest.html 換成矩陣頁(原平表另存 DB_CHECK_table_latest.html)。
    只讀 VDF 自己的清點報告;不改 rc;渲染器不在 / 失敗照實回(不擋)。"""
    d = root / SM_CONFIG["dir"]
    hits = [p for p in d.glob(DBMX_GLOB) if sm_vnum(p) >= 0]
    out = root / "VIA_Reports" / "vdf"
    page, flat, keep = out / "DB_STATUS_MATRIX_latest.html", out / "DB_CHECK_latest.html", out / "DB_CHECK_table_latest.html"
    if not hits:
        r = {"lamp": "ABSENT", "why": "渲染器 %s 不在 %s" % (DBMX_GLOB, d)}
    else:
        tail = max(hits, key=sm_vnum)
        try:
            cp = subprocess.run([sys.executable, str(tail), "render"], env=sm_child_env(), capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=180)
        except subprocess.TimeoutExpired:
            cp = None
        if cp is None or cp.returncode != 0 or not page.is_file():
            r = {"lamp": "RED", "why": "渲染失敗:%s" % (("逾時 180 秒" if cp is None else (cp.stdout + cp.stderr).strip()[-200:]) or "沒產出")}
        else:
            if flat.is_file() and 'content="DB_STATUS_MATRIX"' not in flat.read_text(encoding="utf-8", errors="replace")[:600]:
                keep.write_bytes(flat.read_bytes())          # 原平表另存(這一輪 db check 寫的那份)
            flat.write_bytes(page.read_bytes())
            r = {"lamp": "GREEN", "page": str(page), "db_page": str(flat), "table": str(keep), "renderer": tail.name}
    if not quiet:
        if r["lamp"] == "GREEN":
            print(f"[{SM_TAG}] [矩陣] 資料庫狀態矩陣 → {os.path.relpath(page, root)}(資料庫頁 DB_CHECK_latest.html 同一頁;原平表 DB_CHECK_table_latest.html)")
        else:
            print(f"[{SM_TAG}] [矩陣] 資料庫狀態矩陣 {r['lamp']} · {r['why']}(資料庫頁照原樣)")
    return r


def dbmx_selftest(ck, root: Path) -> None:
    """v0182 自測:分派仍是標準轉交者 · 沙盒真渲染(資料庫頁換成矩陣 · 原平表另存)· 渲染器不在照實 ABSENT · 導覽列有連結。"""
    me = sm_static_card(SM_HERE)
    ck("D1 主分派多一行 db check / verify 的 if(登在本版 SM_MAIN_IFS)· 本檔照樣是標準轉交者 · rc 照轉交那一版",
       me["standard"] and 'if verb == "db" and args[1:2] in (["check"], ["verify"]):' in SM_MAIN_IFS
       and "rc = sm_forward(" in SM_HERE.read_text(encoding="utf-8") and "return rc" in SM_HERE.read_text(encoding="utf-8"), me.get("why"))
    hits = sorted((root / SM_CONFIG["dir"]).glob(DBMX_GLOB), key=sm_vnum)
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        vd = tr / SM_CONFIG["dir"]
        vd.mkdir(parents=True)
        (tr / "VIA_Reports" / "vdf").mkdir(parents=True)
        r0 = sm_db_matrix(tr, quiet=True)
        ok_render = False
        note = r0
        if hits:
            (vd / hits[-1].name).write_bytes(hits[-1].read_bytes())
            fx = {"verb": "db check", "tag": "VDF_SystemManager v0156", "ts": "2026-11-15T09:00:00", "book": "VIA_DB_Table_SSOT_v0102.json",
                  "lamp": "RED", "home_pick": {"picked": str(tr)},
                  "rows": [{"庫": "a.duckdb", "表": "p", "狀態": "OK", "燈": "GREEN", "列數": 9, "最少": 1, "上次列數": None, "最新日": "2026-11-14",
                            "落後天": 1, "寫入者": "VDF_ENG001", "檔": ""},
                           {"庫": "a.duckdb", "表": "q", "狀態": "缺表", "燈": "RED", "列數": None, "最少": 1, "上次列數": None, "最新日": None,
                            "落後天": None, "寫入者": "VDF_ENG002", "檔": ""}]}
            (tr / "VIA_Reports" / "vdf" / "DB_CHECK_latest.json").write_text(json.dumps(fx, ensure_ascii=False), encoding="utf-8")
            (tr / "VIA_Reports" / "vdf" / "DB_CHECK_latest.html").write_text("<html>原平表 a.duckdb q 缺表</html>", encoding="utf-8")
            r1 = sm_db_matrix(tr, quiet=True)
            db_page = (tr / "VIA_Reports" / "vdf" / "DB_CHECK_latest.html").read_text(encoding="utf-8")
            table = (tr / "VIA_Reports" / "vdf" / "DB_CHECK_table_latest.html").read_text(encoding="utf-8") if (tr / "VIA_Reports" / "vdf" / "DB_CHECK_table_latest.html").is_file() else ""
            r2 = sm_db_matrix(tr, quiet=True)          # 再跑一次:原平表不被矩陣頁蓋掉
            table2 = (tr / "VIA_Reports" / "vdf" / "DB_CHECK_table_latest.html").read_text(encoding="utf-8")
            ok_render = (r1["lamp"] == "GREEN" and "矩陣一 · 庫 × 狀態" in db_page and "原平表" in table and r2["lamp"] == "GREEN" and table2 == table)
            note = (r1, table[:60])
    ck("D2 沙盒真渲染(%s):資料庫頁換成狀態矩陣 · 原平表另存 DB_CHECK_table_latest.html · 再跑一次原平表不被蓋;渲染器不在 → ABSENT 照實不擋"
       % (hits[-1].name if hits else "渲染器不在倉"), r0["lamp"] == "ABSENT" and (ok_render or not hits), note)
    ck("D3 管理員矩陣頁導覽列有「資料庫狀態矩陣」· 不動態載入他檔(子行程叫渲染器)",
       "('資料庫狀態矩陣', 'VIA_Reports/vdf/DB_STATUS_MATRIX_latest.html')" in SM_HERE.read_text(encoding="utf-8")
       and sm_static_checks(SM_HERE)["P4_no_peer_import"])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = sm_via_root()
    if not args:
        return sm_cmd("help", [], root)
    verb = args[0]
    if verb in ("--selftest", "selftest"):
        return selftest()
    if verb != "engine-matrix":
        em_auto(root)                                            # 每次執行靜默登記引擎版本與時間(不印 · 不擋)
    if verb in SM_NATIVE and "--legacy" not in args:
        return sm_cmd(verb, args[1:], root)
    if verb in DP_VERBS and "--legacy" not in args:
        return sm_dataplane(args, root)                          # v0183:管理範圍 · 清單輸入閘 · parquet 增量庫(rc 照 MDL020)
    rc = sm_forward([a for a in args if a != "--legacy"], root)
    if verb == "db" and args[1:2] in (["check"], ["verify"]):
        sm_db_matrix(root)                                       # v0182:資料庫頁 = 狀態矩陣(rc 照轉交那一版)
    return rc


DP_VERBS = ("scope", "inputs", "parquet")
DP_GLOB = "VDF_MDL020_DataPlane_v*.py"


def sm_dataplane(args: list, root: Path, capture: bool = False):
    """v0183:scope · inputs · parquet … → 子行程叫 VDF_MDL020_DataPlane 尾版(帶本系統入口旗標);rc 照它。不在 = ABSENT rc 3。
    sync / export 在大資料家上可能跑很久,不設逾時(操作員可 Ctrl+C)。capture=True 回 (rc, 輸出) 給自測用。"""
    d = root / SM_CONFIG["dir"]
    hits = [p for p in d.glob(DP_GLOB) if sm_vnum(p) >= 0]
    if not hits:
        msg = f"[{SM_TAG}] [資料平面] ABSENT · {DP_GLOB} 不在 {d}"
        if capture:
            return 3, msg
        print(msg)
        return 3
    tail = max(hits, key=sm_vnum)
    cmd = [sys.executable, str(tail), *[a for a in args if a != "--legacy"]]
    if capture:
        cp = subprocess.run(cmd, env=sm_child_env(), capture_output=True, text=True, encoding="utf-8", errors="replace")
        return cp.returncode, cp.stdout + cp.stderr
    return subprocess.run(cmd, env=sm_child_env()).returncode


def dp_selftest(ck, root: Path) -> None:
    """v0183 自測:主分派仍是標準轉交者 · 沙盒真跑(parquet sync 建 tw__ 檔 · 重跑不動檔 · status 列得出)· 模組不在 ABSENT · 導覽列有連結。"""
    me = sm_static_card(SM_HERE)
    text = SM_HERE.read_text(encoding="utf-8")
    ck("P1 主分派多一行資料平面 if(登在本版 SM_MAIN_IFS)· 本檔照樣是標準轉交者 · 三動詞不在原生表(不搶前版)",
       me["standard"] and 'if verb in DP_VERBS and "--legacy" not in args:' in SM_MAIN_IFS and not set(DP_VERBS) & set(SM_NATIVE), me.get("why"))
    hits = sorted((root / SM_CONFIG["dir"]).glob(DP_GLOB), key=sm_vnum)
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        (tr / SM_CONFIG["dir"]).mkdir(parents=True)
        r0 = sm_dataplane(["parquet", "status", "--home", td], tr, capture=True)
        ok_run, note = False, r0
        if hits:
            try:
                import duckdb
            except ImportError:
                duckdb = None
            if duckdb is not None:
                h = tr / "home"
                (h / "output_hub" / "mega").mkdir(parents=True)
                c = duckdb.connect(str(h / "output_hub" / "mega" / "vdf_tw_market.duckdb"))
                c.execute("CREATE TABLE tw_daily_prices AS SELECT '2026-11-1' || i AS date, '2330' AS ticker, 1.0 * i AS close FROM range(3) t(i)")
                c.close()
                pq = h / "tw__tw_daily_prices.parquet"
                r1 = sm_dataplane(["parquet", "sync", "--home", str(h)], root, capture=True)
                m1 = pq.stat().st_mtime_ns if pq.is_file() else None
                r2 = sm_dataplane(["parquet", "sync", "--home", str(h)], root, capture=True)
                m2 = pq.stat().st_mtime_ns if pq.is_file() else None
                r3 = sm_dataplane(["parquet", "status", "--home", str(h)], root, capture=True)
                ok_run = (r1[0] == 0 and m1 is not None and r2[0] == 0 and m1 == m2 and "沒新鍵不動 1 檔" in r2[1]
                          and r3[0] in (0, 2) and "tw__tw_daily_prices.parquet" in r3[1])
                note = (r1[1][-200:], r2[1][-160:], r3[1][-160:])
            else:
                ok_run, note = True, "duckdb 不在 → 只驗轉交"
    ck("P2 沙盒真跑(%s):parquet sync 建 tw__ 檔 · 重跑沒新鍵不動檔 · status 列得出 · 模組不在 → ABSENT rc 3"
       % (hits[-1].name if hits else "資料平面模組不在倉"), r0[0] == 3 and "ABSENT" in r0[1] and (ok_run or not hits), note)
    ck("P3 管理員頁導覽列有「VDF 管理範圍」· help 列出三動詞 · 不動態載入他檔(子行程叫資料平面)",
       "('VDF 管理範圍', 'VIA_Reports/vdf/VDF_SCOPE_latest.html')" in text and "資料平面(v0183" in text and sm_static_checks(SM_HERE)["P4_no_peer_import"])


if __name__ == "__main__":
    sys.exit(main())
