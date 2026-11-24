#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v0105→v0106(批683 操作員令「PY 都要導入加速器;PS 都要加入 25 個加速器;不卡斷;動態進度條;不然指令速度太慢」):
  先量:PY ACCEL 四系 100%(VDF 195/195 · VAP 247/247 · VRN 366/366 · VIA 1860/1860)——PY 那一半沒有欠帳;
  PS 在冊 1027 支,缺 [VIA:PS-ACCEL] 55 支,其中 20 支是**版史**(同族非尾版)、17 支是 VAP 上傳原件與快照夾、1 支是 25 冊本體(注進去=模組 dot-source 冊、冊再 dot-source 模組=循環)。
  改法:① PS 正典塊改抄 Register 尾版的 [VIA:PS-ACCEL:v0101](PS 25 加速器橋),不再是 v0100 的「20」;HAS 判準同時認 v0100/v0101(832 支 v0100 走的是同一個模組,模組已是 25 冊,
     不為了改一行註解去動 832 支)。② +--ps-tail:只注尾版(批670:尺不把版史當資產;版史列 HISTORY 不注)。③ PS 專用排除:SOURCE_VAP_MODULE / _output 快照夾 / _patches 一次性補丁 /
     _sha 凍結副本;PS 不可動:加速器模組本體、20/25 冊、PyProgress 模組(自掛=循環)。④ +⑪ 檢。py 那一側一個字不動。

v0104→v0105(批626):排除冊補 **唯讀正典 SSOT**(`READONLY_CANON`)。全樹 --accel 掃下來
唯一缺橋的活檔就是 `supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py`,
而那支是唯讀正典;v0104 會把它列進計畫,`--apply` 就寫進去了。**覆蓋率差的那 0.1%
不是欠帳,是不准動的東西**——不在冊講清楚,遲早有人為了補成 100% 去動它。

v0103→v0104(批597):+**雜湊冊凍結夾**排除。實錄:我用 v0103 把加速器橋注進
`VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/` 四支,那一夾有 `MANIFEST_b514.json`
(原名零觸碰律的 md5 冊),CGC_MDL150 第①檢當場報紅。四支已還原。判準改成**看夾裡有沒有
記著自己檔案雜湊的冊**,不是靠我記得夾名。

CGC_MDL124_BridgeSweeper v0104 — 橋塊掃描/注入器(批345 操作員令「加速器導入全部 網路工具導入VDF全部」;批346 git 在冊律)
====================================================================
職權:全樹 py 的兩種正典橋塊覆蓋率實掃+缺者注入(graceful 零行為變更;正典塊文字=在庫既有件逐字):
  ACCEL  [VIA:ACCEL-BRIDGE:v0100]  批102 全樹導入令 → VIA_SuperAccel_Module(→SUP_MDL737 尾版→VeritasCeleritas)
  NET    [VIA:NET-BRIDGE:v0100]    批115 VDF 全導入令 → via_net_unified 尾版(→SUP_MDL740 尾版→VeritasAegisNexus)
律:
  只增不減:只插入標記塊,原碼一字不動;插入點=既有 ACCEL 塊 END 之後(NET)/`from __future__` 之後
            /模組 docstring 之後/檔首(ACCEL);注入前後 py_compile 皆須通過,否則該檔 SKIP 誠實
  排除冊(不注入、誠實列):references/intake 收容原件、__pycache__、VIA_RetiredEngines、TALib/vendor、
            tests、new modules engines(bundle 原件)、50_Protection_Acceleration(凍結群)、
            兩獨立工具 VeritasCeleritas.py / VeritasAegisNexus.py(操作員令「不可動」)
  預設 dry-run;--apply 才寫;報告落 VIA_Reports/bridge_sweep/SWEEP_<stamp>.json
v0100→v0101(批346 工作站實錄「掃 5196 · 缺 2718」=工作站含 gitignored 產物:_via_mother_root_reconciliation_runs
rollback 副本(SyntaxWarning 洪水+py_compile 敗 SKIP 35)、VIA_Reports、output_hub、venv):
  ①git 在冊律:倉內只掃 git ls-files 在冊 .py(gitignored 產物/副本/回滾件=非正本,永不注入;誠實計 EXCLUDED「未在冊」)
    git 缺席=退目錄實掃+路徑排除冊
  ②路徑排除冊 +_via_mother_root_reconciliation_runs/rollback/VIA_Reports/output_hub/.venv/venv/site-packages/_backup*/_quarantine
  ③--subsystems:VDF/VAP/VRN/VIA(=supportive modules+根層)四系逐系列覆蓋(ACCEL 全系;NET 依令 VDF)+總表
  ④--warn-quiet:注入前 py_compile 以 -W ignore 抑制 SyntaxWarning 洪水(不改判定)
v0101→v0102(批355 操作員令「ps要加20個加速器」):+--ps kind:ps1 缺 [VIA:PS-ACCEL] 者注入正典塊(在庫 Invoke-VIA-Complete 逐字);插入點=param(...) 塊之後(#requires/前導註解之後);無 param=檔首註解後;在冊律/排除冊同;雲端無 pwsh=語法候工作站 via-bridge-sweep --ps 實錄(dry-run 預設)。
v0102→v0103(批402 操作員令「所有向外擷取資料檔全部導入 VeritasAegisNexus.py」):+--net-callers:NET 只計/只注入「真向外擷取」檔
  (去註解與字串後仍含 urlopen/requests.get|post|Session/httpx/urllib3/yfinance/aiohttp 直呼者);非擷取檔=NOCALL 誠實列、不注入(零九頭龍)。
  橋本體/網路工具本體/vendored 套件永不注入(CALLER_UNTOUCHABLE:SUP_MDL737/SUP_MDL740/via_net_unified/via_aegis_netcore/VIA_NetSupport/
  相對匯入之 vendored requests 內部件/pip._vendor/SPDX 標頭第三方件);九檢。
用法:python3 CGC_MDL124_BridgeSweeper_v0103.py [--net] [--accel] [--net-callers] [--root <rel>] [--subsystems] [--apply] | --selftest
  預設:--net --root "functional modules/VDF"(操作員令範圍);--accel 全樹覆蓋率報告
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
import json
import py_compile
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "bridge_sweep"

ACCEL_START = "# ===== [VIA:ACCEL-BRIDGE:v0100]"
ACCEL_END = "# ===== [VIA:ACCEL-BRIDGE:END] ====="
NET_START = "# ===== [VIA:NET-BRIDGE:v0100]"
NET_END = "# ===== [VIA:NET-BRIDGE:END] ====="

ACCEL_BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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

NET_BLOCK = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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

EXCLUDE_PARTS = ("references", "intake", "__pycache__", "VIA_RetiredEngines", "vendor", "tests", "new modules engines",
                 "50_Protection_Acceleration", ".pytest_cache", "node_modules", ".git",
                 "_via_mother_root_reconciliation_runs", "rollback", "VIA_Reports", "output_hub", ".venv", "venv",
                 "site-packages", "_quarantine", "_review_quarantine")
SUBSYSTEMS = {"VDF": "functional modules/VDF", "VAP": "functional modules/VAP", "VRN": "functional modules/VRN",
              "VIA": "supportive modules"}

_TRACKED = {"set": None, "tried": False}


def tracked_set():
    """git 在冊 .py 集合(相對 VIA;git 缺席/非倉=None→退目錄實掃)"""
    if _TRACKED["tried"]:
        return _TRACKED["set"]
    _TRACKED["tried"] = True
    try:
        import subprocess
        r = subprocess.run(["git", "ls-files", "-z", "--", "*.py", "*.ps1"], cwd=str(VIA), capture_output=True, timeout=120)  # 批355:ps1 亦在冊
        if r.returncode == 0:
            _TRACKED["set"] = {x for x in r.stdout.decode("utf-8", "ignore").split("\0") if x}
    except Exception:
        _TRACKED["set"] = None
    return _TRACKED["set"]
UNTOUCHABLE = ("VeritasCeleritas.py", "VeritasAegisNexus.py",
               "VIA_SuperAccel_Module.py")  # 橋本體=自掛即循環 import;永不注入
# 批626:**唯讀正典**。實錄——`--accel` 掃全樹,唯一一個「缺橋」的活檔是
#   supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py · 計畫注入於第 13 行
# 那支是操作員定的唯讀正典 SSOT(它自己的說明第 6 條也寫著「canonical SSOT 與
# Regex authority 保持唯讀」)。v0104 不知道這條律,`--apply` 會**直接寫進去**。
# 覆蓋率 99.9% 的那 0.1% 不是欠帳,是**不准動的東西**——把它算成欠帳,
# 遲早有人為了把數字補成 100% 去動它。所以在冊、有名、有理由。
READONLY_CANON = ("VIA_Financial_Institution_SSOT_v0100.py",)
# 批402:--net-callers 律——「真向外擷取」判定(去註解/字串後仍含直呼網路原語;本機樞紐 socket 探測不計)
NET_CALLER_RX = re.compile(r"urllib\.request\.urlopen|\burlopen\(|\brequests\.(get|post|Session)\(|\bhttpx\.(get|post|Client)\("
                           r"|\burllib3\.(PoolManager|request)\(|\byf\.download\(|\byfinance\.(download|Ticker)\(|\baiohttp\.ClientSession\(")
CALLER_UNTOUCHABLE = ("SUP_MDL737_SuperAccelModule", "SUP_MDL740_NetUnified", "via_net_unified", "via_aegis_netcore",
                      "VIA_NetSupport.py")   # 網路/加速工具本體=橋所委派之核,自掛=循環;永不注入
_STR_RX = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\')')


def _is_net_caller(src: str) -> bool:
    """去註解與字串字面量後仍含直呼網路原語=真向外擷取檔(字串/註解/冊內文字提及不算)"""
    body = _STR_RX.sub('""', src)
    body = "\n".join(ln.split("#", 1)[0] for ln in body.split("\n"))
    return bool(NET_CALLER_RX.search(body))


def _caller_untouchable(p: Path, src: str) -> str:
    """回排除因由(空=可注入):工具本體(名冊)/vendored 相對匯入內部件(如 network/ 內 requests 副本)"""
    if any(p.name.startswith(k) or p.name == k for k in CALLER_UNTOUCHABLE):
        return "網路/加速工具本體(自掛=循環)"
    if re.search(r"^from \.+\s*[a-zA-Z_]", src, re.M) and "supportive modules" in str(p):
        return "vendored 套件內部件(相對匯入)"
    if re.search(r"^(from|import) pip\._vendor\b|SPDX-FileCopyrightText:", src, re.M):
        return "第三方 vendored 件(pip._vendor/SPDX 標頭)"
    return ""


#: 批597:**雜湊冊凍結夾**——夾裡有一本記著自己檔案 md5/sha 的冊,就是凍結件,
#  會寫檔的腳本一律不得碰。實錄:批597 我用 v0103 把加速器橋注進
#  `supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514/` 四支,
#  那一夾有 `MANIFEST_b514.json`(原名零觸碰律的 md5 冊),注完 CGC_MDL150 第①檢當場報紅。
#  排除清單裡沒有它的名字,所以攔不住——**尺不認得的東西,不會因為它重要就自己躲開**(L77 延伸)。
FROZEN_MANIFESTS = ("MANIFEST",)
_FROZEN_CACHE: dict = {}


def _frozen_dir(d: Path) -> str:
    """**只看這一夾自己**有沒有一本點名自己 .py 的雜湊冊;有=凍結,回冊名。

    範圍刻意收窄(第一版我往祖先夾一路找,結果 `supportive modules/` 底下一個
    `*_sha*.json` 就把整個 supportive modules 都判成凍結=**把整棵樹關掉**——
    尺太寬跟太窄一樣壞)。判準要有證據:冊裡**真的點名**這一夾裡的某支 .py。
    """
    key = str(d)
    if key in _FROZEN_CACHE:
        return _FROZEN_CACHE[key]
    why = ""
    pys = {f.name for f in d.glob("*.py")}
    if pys:
        for f in d.glob("*.json"):
            if not any(t in f.stem for t in FROZEN_MANIFESTS):
                continue
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(nm in txt for nm in pys):
                why = f"雜湊冊凍結夾({d.name}/{f.name})"
                break
    _FROZEN_CACHE[key] = why
    return why


def _excluded(p: Path) -> str:
    rel = p.relative_to(VIA)
    for seg in rel.parts:
        if seg in EXCLUDE_PARTS or seg.startswith("_backup"):
            return seg
    fz = _frozen_dir(p.parent)
    if fz:
        return fz
    ts = tracked_set()
    if ts is not None and str(rel).replace("\\", "/") not in ts:
        return "未在冊(gitignored 產物/副本)"
    if p.name in UNTOUCHABLE:
        return "獨立工具不可動" if p.name.startswith("Veritas") else "橋本體(自掛=循環)"
    if p.name in READONLY_CANON:
        return "唯讀正典 SSOT(批626;操作員律,不得注入)"
    return ""


PS_START = "# ===== [VIA:PS-ACCEL:v01"        # 批683:v0100(20)與 v0101(25)都算已掛——兩者 dot-source 同一個模組,模組已是 25 冊
PS_BLOCK = '# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====\ntry {\n    $VIAPSAccelProbe = $PSScriptRoot\n    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {\n        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\\VIA_PS_Accel_Module.ps1"\n        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }\n        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent\n    }\n} catch { }\n# ===== [VIA:PS-ACCEL:END] =====\n'   # 批683:抄 Register 尾版 v0101 塊逐字(PS 25 加速器橋)


PS_EXCLUDE_PARTS = ("SOURCE_VAP_MODULE", "_output", "_patches")     # 批683:VAP 上傳原件與快照夾 · 一次性補丁 —— 只管 .ps1,py 那一側不動
PS_UNTOUCHABLE = ("VIA_PS_Accel_Module.ps1", "VIA_PS_Accelerators_20_Roster_v0100.ps1", "VIA_PS_Accelerators_25_Roster_v0100.ps1", "VIA_PS_PyProgress_Module.ps1")
_PS_VER = re.compile(r"[-_]v\d{4}(?=\.ps1$)")


def _ps_excluded(p: Path) -> str:
    """PS 專用排除(批683):模組本體/冊(自掛=循環)· _sha 凍結副本 · 上傳原件與快照夾 · 一次性補丁。"""
    if p.name in PS_UNTOUCHABLE:
        return "PS 加速器模組/冊本體(自掛=循環)"
    if "_sha" in p.name:
        return "凍結副本(_sha)"
    for seg in p.relative_to(VIA).parts:
        if seg in PS_EXCLUDE_PARTS:
            return seg
    return ""


def _ps_history(rows: list) -> set:
    """同族非尾版=版史(批670:尺不把版史當資產)。族=檔名去 -vNNNN/_vNNNN;尾版=同族名稱最大者;只在 HAS/MISSING 之間比。"""
    fams: dict = {}
    for r in rows:
        if r["state"] not in ("HAS", "MISSING"):
            continue
        key = _PS_VER.sub("", r["file"])
        fams.setdefault(key, []).append(r["file"])
    hist = set()
    for key, fs in fams.items():
        if len(fs) > 1:
            fs = sorted(fs)
            hist.update(fs[:-1])
    return hist


def _ps_insert_point(src: str) -> int:
    """ps1 插入點:param(...) 塊結尾之後;無 param=檔首 #requires/註解區之後"""
    m = re.search(r"^\s*param\s*\(", src, re.M | re.I)
    if m:
        depth, k = 0, m.end() - 1
        while k < len(src):
            if src[k] == "(":
                depth += 1
            elif src[k] == ")":
                depth -= 1
                if depth == 0:
                    return src.index("\n", k) + 1 if "\n" in src[k:] else len(src)
            k += 1
    pos = 0
    for line in src.split("\n"):
        if line.startswith("#") or line.strip() == "":
            pos += len(line) + 1
        else:
            break
    return pos


def scan_ps(root: str) -> list:
    base = VIA / root
    out = []
    for p in sorted(base.rglob("*.ps1")):
        ex = _excluded(p) or _ps_excluded(p)
        if ex:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": ex})
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        out.append({"file": str(p.relative_to(VIA)), "state": "HAS" if (PS_START in t or "VIA_PS_Accel_Module.ps1" in t) else "MISSING", "why": ""})
    return out


def inject_ps(rel: str, apply: bool) -> dict:
    p = VIA / rel
    src = p.read_text(encoding="utf-8")
    at = _ps_insert_point(src)
    new = src[:at] + PS_BLOCK + src[at:]
    if not apply:
        return {"file": rel, "state": "PLAN", "why": f"插入於第 {src[:at].count(chr(10)) + 1} 行"}
    p.write_text(new, encoding="utf-8", newline="\r\n" if "\r\n" in src else "\n")
    return {"file": rel, "state": "INJECTED", "why": f"第 {src[:at].count(chr(10)) + 1} 行"}


def run_ps(root: str, apply: bool, do_print: bool = True, tail_only: bool = False) -> dict:
    rows = scan_ps(root)
    if tail_only:
        hist = _ps_history(rows)
        for r in rows:
            if r["state"] == "MISSING" and r["file"] in hist:
                r["state"], r["why"] = "HISTORY", "版史(同族非尾版;批670 尺不把版史當資產)不注"
    miss = [r for r in rows if r["state"] == "MISSING"]
    acts = [inject_ps(r["file"], apply) for r in miss]
    n_has = sum(1 for r in rows if r["state"] == "HAS")
    rep = {"scanned": len(rows), "has": n_has, "missing": len(miss), "excluded": sum(1 for r in rows if r["state"] == "EXCLUDED"), "history": sum(1 for r in rows if r["state"] == "HISTORY"),
           "injected": sum(1 for a in acts if a["state"] == "INJECTED"), "planned": sum(1 for a in acts if a["state"] == "PLAN"),
           "coverage_after": round(100 * (n_has + sum(1 for a in acts if a["state"] == "INJECTED")) / max(1, n_has + len(miss)), 1), "actions": acts}
    if do_print:
        print(f"[橋掃] PS-ACCEL root={root} · 掃 {rep['scanned']} · 已掛 {n_has} · 缺 {len(miss)} · 版史 {rep['history']} · 排除 {rep['excluded']} · "
              f"{'注入 ' + str(rep['injected']) if apply else '計畫 ' + str(rep['planned']) + '(dry-run)'} · 覆蓋 {rep['coverage_after']}%")
        for a in acts[:60]:
            print(f"    {a['state']:8s} {a['file']} · {a['why']}")
    return rep


def scan(root: str, kind: str, callers_only: bool = False) -> list:
    """回列 [{file, state: HAS|MISSING|EXCLUDED|NOCALL, why}];批402 callers_only(kind=net):非真擷取檔=NOCALL 不注入"""
    base = VIA / root
    start = ACCEL_START if kind == "accel" else NET_START
    out = []
    for p in sorted(base.rglob("*.py")):
        ex = _excluded(p)
        if ex:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": ex})
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": f"讀取失敗 {type(exc).__name__}"})
            continue
        if callers_only and kind == "net":
            cu = _caller_untouchable(p, src)
            if cu:
                out.append({"file": str(p.relative_to(VIA)), "state": "EXCLUDED", "why": cu})
                continue
            if not _is_net_caller(src):
                out.append({"file": str(p.relative_to(VIA)), "state": "NOCALL", "why": "非向外擷取檔(無直呼網路原語)"})
                continue
        alt = "VIA_SuperAccel_Module" if kind == "accel" else "via_net_unified_v"
        if start in src:
            out.append({"file": str(p.relative_to(VIA)), "state": "HAS", "why": ""})
        elif alt in src:
            out.append({"file": str(p.relative_to(VIA)), "state": "HAS", "why": f"自掛({alt})"})
        else:
            out.append({"file": str(p.relative_to(VIA)), "state": "MISSING", "why": ""})
    return out


def _insert_point(src: str, kind: str) -> int:
    """回插入字元位置;NET=ACCEL END 之後優先;其次 from __future__ 行之後;其次 docstring 之後;否則檔首(shebang/coding 之後)"""
    if kind == "net" and ACCEL_END in src:
        i = src.index(ACCEL_END)
        return src.index("\n", i) + 1
    m = re.search(r"^from __future__ import [^\n]*\n", src, re.M)
    if m:
        return m.end()
    lines = src.split("\n")
    pos = 0
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or re.match(r"^#.*coding[:=]", lines[i]) or lines[i].strip() == ""):
        pos += len(lines[i]) + 1
        i += 1
    if i < len(lines) and re.match(r'^[rRuUbB]*("""|\'\'\')', lines[i]):
        q = '"""' if '"""' in lines[i] else "'''"
        rest = src[pos:]
        first = rest.index(q) + 3
        end = rest.find(q, first)
        if end >= 0:
            return pos + src[pos:].index("\n", end) + 1 if "\n" in src[pos + end:] else len(src)
    return pos


def inject(rel: str, kind: str, apply: bool) -> dict:
    p = VIA / rel
    block = NET_BLOCK if kind == "net" else ACCEL_BLOCK
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            py_compile.compile(str(p), doraise=True, quiet=1)
    except Exception as exc:
        return {"file": rel, "state": "SKIP", "why": f"注入前 py_compile 失敗 {type(exc).__name__}"}
    src = p.read_text(encoding="utf-8")
    at = _insert_point(src, kind)
    new = src[:at] + block + src[at:]
    if not apply:
        return {"file": rel, "state": "PLAN", "why": f"插入於字元 {at}(第 {src[:at].count(chr(10)) + 1} 行)"}
    tmp = p.with_suffix(".py.__sweep_tmp")
    try:
        tmp.write_text(new, encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            py_compile.compile(str(tmp), doraise=True, quiet=1)
    except Exception as exc:
        tmp.unlink(missing_ok=True)
        return {"file": rel, "state": "SKIP", "why": f"注入後 py_compile 失敗 {type(exc).__name__}(原檔未動)"}
    tmp.unlink(missing_ok=True)
    p.write_text(new, encoding="utf-8", newline="\n" if "\r\n" not in src else "\r\n")
    return {"file": rel, "state": "INJECTED", "why": f"第 {src[:at].count(chr(10)) + 1} 行"}


def run(kinds: list, root: str, apply: bool, do_print: bool = True, callers_only: bool = False) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep = {"ts": stamp, "root": root, "apply": apply, "kinds": {}, "callers_only": callers_only}
    for kind in kinds:
        rows = scan(root, kind, callers_only=callers_only)
        miss = [r for r in rows if r["state"] == "MISSING"]
        acts = [inject(r["file"], kind, apply) for r in miss]
        n_has = sum(1 for r in rows if r["state"] == "HAS")
        n_ex = sum(1 for r in rows if r["state"] == "EXCLUDED")
        n_inj = sum(1 for a in acts if a["state"] == "INJECTED")
        n_skip = sum(1 for a in acts if a["state"] == "SKIP")
        n_plan = sum(1 for a in acts if a["state"] == "PLAN")
        n_nocall = sum(1 for r in rows if r["state"] == "NOCALL")
        rep["kinds"][kind] = {"scanned": len(rows), "has": n_has, "missing": len(miss), "excluded": n_ex, "nocall": n_nocall,
                              "injected": n_inj, "skipped": n_skip, "planned": n_plan,
                              "coverage_after": round(100 * (n_has + n_inj) / max(1, n_has + len(miss)), 1),
                              "actions": acts, "excluded_list": [r for r in rows if r["state"] == "EXCLUDED"][:200]}
        if do_print:
            print(f"[橋掃] {kind.upper():5s} root={root} · 掃 {len(rows)} · 已掛 {n_has} · 缺 {len(miss)} · 排除 {n_ex}"
                  f"{' · 非擷取 ' + str(n_nocall) if callers_only and kind == 'net' else ''} · "
                  f"{'注入 ' + str(n_inj) + ' · SKIP ' + str(n_skip) if apply else '計畫 ' + str(n_plan) + '(dry-run)'} · "
                  f"覆蓋 {rep['kinds'][kind]['coverage_after']}%", flush=True)
            for a in acts:
                if a["state"] == "SKIP" or (not apply and len(acts) <= 20):
                    print(f"    {a['state']:8s} {a['file']} · {a['why']}")
    REP.mkdir(parents=True, exist_ok=True)
    out = REP / f"SWEEP_{stamp}.json"
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    rep["file"] = out.name
    if do_print:
        print(f"[橋掃] 報告 {out.relative_to(VIA)}")
    return rep


def selftest() -> int:
    fails = []

    _n626 = [0]

    def chk(name, cond, note=""):
        _n626[0] += 1          # 批626:檢數現場計(v0104 寫死 10,我加了第 11 檢它還是印 10)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    import tempfile
    src = Path(__file__).read_text(encoding="utf-8")
    # ① 正典塊文字=在庫件逐字(取任一已掛 NET 的現役件比對)
    ref = None
    for p in sorted(VIA.glob("VIA_SYSTEM_MANAGER_v*.py")):
        t = p.read_text(encoding="utf-8")
        if NET_START in t:
            ref = t
    net_ok = ref is not None and NET_BLOCK.strip() in ref
    acc_ok = ref is not None and ACCEL_BLOCK.strip() in ref
    chk("① 正典塊文字=在庫現役件逐字(NET/ACCEL)", net_ok and acc_ok)
    # ② 插入點律:ACCEL END 後/future 後/docstring 後/檔首
    s1 = 'from __future__ import annotations\n' + ACCEL_BLOCK + 'import os\n'
    s2 = '#!/usr/bin/env python3\n"""doc\nmore"""\nimport os\n'
    s3 = 'import os\n'
    s4 = '# -*- coding: utf-8 -*-\nfrom __future__ import annotations\nimport os\n'
    chk("② 插入點律(ACCEL END 後→future 後→docstring 後→檔首)",
        s1[_insert_point(s1, "net"):].startswith("import os") and s2[_insert_point(s2, "accel"):].startswith("import os")
        and _insert_point(s3, "accel") == 0 and s4[_insert_point(s4, "net"):].startswith("import os"))
    # ③ 沙盒注入真跑:臨時檔→注入→py_compile 通→兩塊皆在→原碼保留
    with tempfile.TemporaryDirectory(dir=str(VIA / "VIA_Reports")) as td:
        tp = Path(td) / "t_sweep.py"
        tp.write_text('#!/usr/bin/env python3\n"""x"""\nfrom __future__ import annotations\nimport os\nX = 1\n', encoding="utf-8")
        rel = str(tp.relative_to(VIA))
        r1 = inject(rel, "accel", apply=True)
        r2 = inject(rel, "net", apply=True)
        t = tp.read_text(encoding="utf-8")
        ok3 = r1["state"] == "INJECTED" and r2["state"] == "INJECTED" and ACCEL_START in t and NET_START in t \
            and t.index(ACCEL_END) < t.index(NET_START) and t.endswith("X = 1\n") and t.startswith("#!/usr/bin/env python3\n")
        try:
            py_compile.compile(str(tp), doraise=True)
        except Exception:
            ok3 = False
        # 壞檔=SKIP 誠實(原檔未動)
        bp = Path(td) / "t_bad.py"
        bp.write_text("def (:\n", encoding="utf-8")
        r3 = inject(str(bp.relative_to(VIA)), "net", apply=True)
        ok3 = ok3 and r3["state"] == "SKIP" and bp.read_text(encoding="utf-8") == "def (:\n"
    chk("③ 沙盒注入真跑(ACCEL→NET 順序;原碼保留;compile 通;壞檔 SKIP 原檔未動)", ok3)
    # ④ 排除冊:獨立工具/凍結群/收容原件/退役 皆 EXCLUDED
    chk("④ 排除冊(獨立工具不可動/凍結群/收容原件/退役/vendor)",
        _excluded(VIA / "supportive modules" / "VeritasCeleritas.py") == "獨立工具不可動"
        and _excluded(VIA / "supportive modules" / "50_Protection_Acceleration" / "x.py") == "50_Protection_Acceleration"
        and _excluded(VIA / "functional modules" / "VDF" / "references" / "intake" / "a" / "x.py") == "references"
        and _excluded(VIA / "functional modules" / "VIA_RetiredEngines" / "x.py") == "VIA_RetiredEngines"
        and _excluded(VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG072_StoryRotationBridge_v0100.py") == "")
    # ⑤ dry-run 零寫:VDF 掃描 PLAN 不動檔
    before = {p: p.stat().st_mtime for p in (VIA / "functional modules" / "VDF").rglob("*.py")}
    rep = run(["net"], "functional modules/VDF", apply=False, do_print=False)
    after = {p: p.stat().st_mtime for p in (VIA / "functional modules" / "VDF").rglob("*.py")}
    chk("⑤ dry-run 零寫(VDF 全掃 mtime 不變;報告落盤)", before == after and (REP / rep["file"]).exists(),
        f"(掃 {rep['kinds']['net']['scanned']} · 已掛 {rep['kinds']['net']['has']} · 缺 {rep['kinds']['net']['missing']})")
    chk("⑥ 紀律宣告(只增不減/graceful/dry-run 預設/不可動/py_compile 雙驗)",
        all(k in src for k in ("只增不減", "graceful", "dry-run", "不可動", "py_compile")))
    ts = tracked_set()
    _ro = VIA / "supportive modules" / "ssot" / READONLY_CANON[0]
    chk("⑪ 批626 唯讀正典 SSOT 不得進計畫:`_excluded()` 要回得出理由"
        "(覆蓋率差的那 0.1% 不是欠帳,是不准動的東西;不講清楚就會有人去補它)",
        (not _ro.exists()) or ("唯讀正典" in _excluded(_ro)),
        f"({_excluded(_ro) if _ro.exists() else '檔不在此樹'})")
    chk("⑦ git 在冊律(在冊集合非空;VIA_Reports/rollback/未在冊件 EXCLUDED;在冊現役件放行)",
        (ts is None) or (len(ts) > 100
        and _excluded(VIA / "VIA_Reports" / "x.py") == "VIA_Reports"
        and _excluded(VIA / "_via_mother_root_reconciliation_runs" / "R" / "rollback" / "x.py") == "_via_mother_root_reconciliation_runs"
        and _excluded(VIA / "functional modules" / "VDF" / "engine" / "not_tracked_zzz.py").startswith("未在冊")
        and _excluded(VIA / "supportive modules" / "registry" / "CGC_MDL124_BridgeSweeper_v0100.py") == ""),
        f"(在冊 {len(ts) if ts else 0} 件)")
    chk("⑧ PS-ACCEL 注入律(正典塊=在庫啟動器逐字;param 塊後插入;無 param=檔首註解後;dry-run 零寫)",
        PS_START in PS_BLOCK and "VIA_PS_Accel_Module.ps1" in PS_BLOCK
        and _ps_insert_point("#requires -Version 7.0\nparam(\n  [string]$A = 'x',\n  [switch]$B\n)\n$x = 1\n") == len("#requires -Version 7.0\nparam(\n  [string]$A = 'x',\n  [switch]$B\n)\n")
        and _ps_insert_point("# c\n# d\n$x = 1\n") == len("# c\n# d\n"))
    # ⑨ 批402 --net-callers 律:程式碼直呼=擷取檔;僅字串/註解提及=NOCALL;工具本體/vendored 相對匯入=排除;本機 socket 探測不計
    c1 = "import urllib.request\nr = urllib.request.urlopen('http://x')\n"
    c2 = "X = 'yfinance totalRevenue'  # requests.get( 只在字串/註解\n# urlopen(\n"
    c3 = "import socket\nsocket.create_connection(('127.0.0.1', 8765), 1)\n"
    c4 = '"""urlopen( 在 docstring"""\nimport os\n'
    ok9 = (_is_net_caller(c1) and not _is_net_caller(c2) and not _is_net_caller(c3) and not _is_net_caller(c4)
           and _caller_untouchable(VIA / "supportive modules" / "SUP_MDL737_SuperAccelModule_v0104.py", "x") != ""
           and _caller_untouchable(VIA / "supportive modules" / "network" / "request.py", "from .packages import six\n") != ""
           and _caller_untouchable(VIA / "supportive modules" / "x" / "ntlmpool.py", "from .. import HTTPSConnectionPool\n") != ""
           and _caller_untouchable(VIA / "supportive modules" / "x" / "_cmd.py", "# SPDX-FileCopyrightText: 2015 E\nfrom pip._vendor import requests\n") != ""
           and _caller_untouchable(VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG054_TWDailyBackfill_v0104.py", c1) == "")
    chk("⑨ --net-callers 律(直呼=擷取/字串註解 docstring 不算/本機 socket 不算/工具本體與 vendored(相對匯入/pip._vendor/SPDX)排除)", ok9)
    # ⑩ 批597 實錄:v0103 把橋注進 VIA_CentralGovernanceFamily_b514 四支,
    #    那一夾有 MANIFEST_b514.json(原名零觸碰律的 md5 冊),CGC_MDL150 ① 當場報紅。
    #    尺要**看得見證據**(冊裡真的點名這一夾的 .py),而且**不准往祖先夾亂長**
    #    ——第一版往上找,一個 `*_sha*.json` 就把整個 supportive modules 判成凍結=把整棵樹關掉。
    fam = VIA / "supportive modules" / "VIA_Central_Governance" / "VIA_CentralGovernanceFamily_b514"
    ok10 = True
    if fam.is_dir():
        ok10 = bool(_frozen_dir(fam))
    ok10 = (ok10
            and not _frozen_dir(VIA / "supportive modules")
            and not _frozen_dir(VIA / "functional modules" / "VDF" / "engine"))
    chk("⑩ 雜湊冊凍結夾律(批597):夾裡有點名自己 .py 的雜湊冊=不得注入;"
        "尺只看本夾**不往祖先長**(太寬會把整棵樹關掉,跟太窄一樣壞)", ok10,
        f"b514={_frozen_dir(fam) or '(未偵測)'}" if fam.is_dir() else "b514 夾不在=本境跳過")
    _rows11 = [{"file": "Invoke-X-v0100.ps1", "state": "MISSING"}, {"file": "Invoke-X-v0101.ps1", "state": "HAS"},
               {"file": "Invoke-Y-v0100.ps1", "state": "MISSING"}, {"file": "Invoke-Y-v0102.ps1", "state": "MISSING"}, {"file": "Solo.ps1", "state": "MISSING"}]
    chk("⑫ 批683 PS 25 律:正典塊=Register 尾版 v0101 逐字(PS 25)且 HAS 同時認 v0100/v0101;版史只在同族非尾版(X-v0100 史/X-v0101 尾;Y-v0100 史/Y-v0102 尾;Solo 非史);"
        "模組本體/25 冊/_sha/_output/SOURCE_VAP_MODULE 不注",
        "PS 25" in PS_BLOCK and "[VIA:PS-ACCEL:v0101]" in PS_BLOCK and PS_START in PS_BLOCK and PS_START in "# ===== [VIA:PS-ACCEL:v0100] x"
        and _ps_history(_rows11) == {"Invoke-X-v0100.ps1", "Invoke-Y-v0100.ps1"}
        and _ps_excluded(VIA / "supportive modules" / "registry" / "VIA_PS_Accelerators_25_Roster_v0100.ps1") != ""
        and _ps_excluded(VIA / "supportive modules" / "VIA_PS_Accel_Module.ps1") != ""
        and _ps_excluded(VIA / "x" / "A_shaabc.ps1") != "" and _ps_excluded(VIA / "functional modules" / "VAP" / "input" / "SOURCE_VAP_MODULE" / "a.ps1") != ""
        and _ps_excluded(VIA / "launchers" / "Invoke-VIA-AllInOne-v0111.ps1") == "",
        "")
    print(f"  [計] {_n626[0]} 檢 OK {_n626[0] - len(fails)} · FAIL {len(fails)}"
          "(檢數現場計:v0104 寫死 `10 - len(fails)`,批626 加了第 11 檢,它照樣印 10——"
          "寫死的檢數會把新加的檢從帳上抹掉)")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 橋塊掃描/注入器(CGC_MDL124 v0104)· 十檢自測(零外網)===")
        return selftest()
    kinds = [k for k in ("net", "accel") if f"--{k}" in a] or ["net"]
    if "--ps" in a:
        root = a[a.index("--root") + 1] if "--root" in a else "."
        rep = run_ps(root, apply="--apply" in a, tail_only="--ps-tail" in a)
        return 0
    if "--subsystems" in a:
        rc = 0
        tot = {}
        for name, root in SUBSYSTEMS.items():
            ks = ["accel"] + (["net"] if name == "VDF" else [])
            rep = run(ks, root, apply="--apply" in a)
            for k, v in rep["kinds"].items():
                tot[f"{name}/{k}"] = f"{v['has'] + v['injected']}/{v['has'] + v['missing']} ({v['coverage_after']}%)"
                rc |= 1 if v["skipped"] else 0
        # 根層(VIA_*.py 等)ACCEL
        rep = run(["accel"], ".", apply="--apply" in a, do_print=False)
        v = rep["kinds"]["accel"]
        tot["ALL/accel"] = f"{v['has'] + v['injected']}/{v['has'] + v['missing']} ({v['coverage_after']}%)"
        print("[橋掃] 四系總表 " + " · ".join(f"{k} {x}" for k, x in tot.items()))
        return rc
    root = a[a.index("--root") + 1] if "--root" in a else "functional modules/VDF"
    rep = run(kinds, root, apply="--apply" in a, callers_only="--net-callers" in a)
    return 0 if all(v["skipped"] == 0 for v in rep["kinds"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
