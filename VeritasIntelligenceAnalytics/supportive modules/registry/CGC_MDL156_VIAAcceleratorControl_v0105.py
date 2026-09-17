#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL156: VIA 25-accelerator control plane.

v0104→v0105(批575 操作員質問「是不是沒按我要求所有 PY 檔案裝這個加速器 所有 VDF 檔案沒有裝這網路工具」)
  量完之後:**他問對了,而且問到的是尺的問題,不是覆蓋率的問題。**
    · 加速器:活樹尾版 807/807 有橋,看起來 100%——但那個 100% 的分母是「活樹尾版扣掉四類免驗」,
      全樹有多少支沒被問到,舊尺一個字都沒講。分母不攤開,100% 就只是一個沒有單位的數字。
    · 網路工具:舊尺問的是「**有沒有人生呼叫**」(負向),批115 的令是「**每一支 VDF 都要掛**」(正向)。
      負向零違規不等於正向全覆蓋——實測正向尺 60/63,缺的三支正好是批569/570/573 我自己新寫的
      ENG088/ENG089/ENG090:它們不 import 網路庫,所以舊尺從來沒問過它們。
  v0105 加五檢:③ 全樹分母攤開(每一支沒問到的都要落在具名豁免類)④ 批115 正向尺
  ⑤ 兩支工具的解析順序可指 ⑥ L50 曝險(解析首位帶不帶 talib 路徑)⑦ 收容正本與掛載本指紋一致。

v0102→v0103(批542 操作員實錄「前一個指令跑太慢」)
  25 個加速器早就在冊、23 檢也早就綠——慢的不是加速器,是**每一道 py 指令都要穿過的那件外套**。
  量出來的:python 側 `-c pass` 約 20ms,外套卻收 279ms;開視窗第一道再多付 1137ms 點燈。
  三個成本都在 VIA_PS_PyProgress_Module.ps1 裡:
    · 快取模式每格 Start-Sleep 25ms × 25 格 = 625ms 純動畫(快取模式根本沒有東西要等)
    · 固定 250ms 輪詢 → 每道指令平均多付 125ms 才發現它早就跑完了
    · Write-Progress 每 250ms 無條件重繪(Windows 主控台重繪整條橫幅,很貴)
  批542 改掉之後:首發 1137→280ms · 後續 279→37ms,六檢行為零變更。
  v0103 加四檢把這三件事**釘住**——不是相信我改過,是讓下一個人改回去時當場亮紅。


This module is deliberately offline and read-only during selftest. It verifies
that the PowerShell roster, Python bootstrap, SuperAccel, Celeritas, Aegis and
central registries agree before any accelerator generation or execution.
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


import argparse
import sys
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
ROSTER_JSON = ROOT / "supportive modules" / "registry" / "VIA_Accelerator_Roster_SSOT_v0100.json"
PS_ROSTER = (sorted((ROOT / "supportive modules" / "registry").glob("VIA_PS_Accelerators_25_Roster_v*.ps1")) or
             [ROOT / "supportive modules" / "registry" / "VIA_PS_Accelerators_25_Roster_v0100.ps1"])[-1]   # 批536 尾版律
PS_MODULE = ROOT / "supportive modules" / "VIA_PS_Accel_Module.ps1"
BOOTSTRAP = ROOT / "supportive modules" / "bootstrap" / "sitecustomize.py"
SUPERACC = ROOT / "supportive modules" / "VIA_SuperAccel_Module.py"
# 批542:所有 py 指令的中央外套(它快一點,全系統就快一點)+ 它的六檢
PYPROG = ROOT / "supportive modules" / "VIA_PS_PyProgress_Module.ps1"
PYPROG_TEST = ROOT / "supportive modules" / "VIA_PS_PyProgress_Selftest_v0100.ps1"
CELERITAS = ROOT / "supportive modules" / "accelerator" / "VeritasCeleritas.py"
AEGIS = ROOT / "supportive modules" / "network" / "VeritasAegisNexus.py"
QUANTGUARD = (sorted((ROOT / "functional modules" / "VDF" / "engine").glob("VDF_ENG086_QuantGuardOneBridge_v*.py")) or
              [ROOT / "functional modules" / "VDF" / "engine" / "VDF_ENG086_QuantGuardOneBridge_v0100.py"])[-1]   # 批536 尾版律(v0101 起 polars 探針式)
POLICY_SSOT = ROOT / "supportive modules" / "registry" / "VIA_QuantGuard_TA_Lib_Policy_v0100.json"
REPORT_DIR = ROOT / "VIA_Reports" / "accelerator"
LATEST_JSON = REPORT_DIR / "VIA_ACCELERATOR_CONTROL_latest.json"
LATEST_HTML = REPORT_DIR / "VIA_ACCELERATOR_CONTROL_latest.html"

REGISTRIES = [
    ROOT / "supportive modules" / "registry" / "VIA_InputConsole_Spec_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Workflow_SSOT_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Interface_Contract_Registry_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Naming_Registry_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_Component_Inventory_SSOT_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_ToolRoster_SSOT_v0100.json",
    ROOT / "supportive modules" / "registry" / "VIA_QuantGuard_TA_Lib_Policy_v0100.json",
]


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "state": "PASS" if ok else "FAIL", "ok": bool(ok), "detail": detail}


def roster_checks(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = payload.get("accelerators") or []
    ids = [str(x.get("id")) for x in items]
    expected = [f"{i:02d}" for i in range(1, 26)]
    out = [check("SSOT roster JSON exists", ROSTER_JSON.is_file(), str(ROSTER_JSON))]
    out.append(check("SSOT roster count=25", len(items) == 25, f"count={len(items)}"))
    out.append(check("SSOT ids unique and contiguous", ids == expected, f"ids={ids}"))
    out.append(check("network accelerator is explicit", any(x.get("id") == "23" and x.get("network") is True for x in items), "id=23"))
    return out


def runtime_checks() -> list[dict[str, Any]]:
    ps_roster_text = read(PS_ROSTER)
    ps_module_text = read(PS_MODULE)
    boot_text = read(BOOTSTRAP)
    reg_text = "\n".join(read(p) for p in REGISTRIES)
    out = [
        check("PowerShell 25 roster exists", PS_ROSTER.is_file(), str(PS_ROSTER)),
        check("PowerShell roster declares 25 entries", len(re.findall(r"^\s*'\d{2}'\s*=", ps_roster_text, re.M)) == 25, "regex count"),
        check("PowerShell runtime exports VIA_ACCEL25", "VIA_ACCEL25" in ps_module_text and "Get-VIAAccelRoster" in ps_module_text, "VIA_PS_Accel_Module.ps1"),
        check("Python sitecustomize bootstrap exists", BOOTSTRAP.is_file(), str(BOOTSTRAP)),
        check("Python bootstrap exposes accelerator state", "VIA_ACCEL_BOOT" in boot_text, "sitecustomize.py"),
        check("Python bootstrap exports 25-roster identity", "VIA_ACCELERATOR_ROSTER" in boot_text and ":25" in boot_text, "all Python families"),
        check("Python bootstrap exports central control identity", "VIA_ACCELERATOR_CONTROL" in boot_text and "CGC_MDL156" in boot_text, "central control"),
        check("Python bootstrap mounts via_net for VDF", 'sys.modules["via_net"]' in boot_text and 'fam == "vdf"' in boot_text, "network family gate"),
        check("Python bootstrap mounts Celeritas/Aegis", "VeritasCeleritas" in boot_text and "VeritasAegisNexus" in boot_text, "lazy tool mounts"),
        check("SuperAccel canonical module exists", SUPERACC.is_file(), str(SUPERACC)),
        # ── 批542:中央 py 外套的四道「別改回去」閘 ──────────────────────────
        check("central py launcher exists (all py commands go through it)",
              PYPROG.is_file(), str(PYPROG)),
        check("b542 lamp row has no per-lamp sleep in cache mode (was 25x25ms=625ms of pure animation)",
              "Start-Sleep -Milliseconds 25 }" not in read(PYPROG), "Show-VIAAccel20"),
        check("b542 adaptive poll (10ms ramp to 250ms), not a flat 250ms wait",
              "$poll = 10" in read(PYPROG) and "Start-Sleep -Milliseconds $poll" in read(PYPROG), "Invoke-VIAPython"),
        check("b542 progress bar is throttled and skipped for sub-400ms runs",
              "-ge 400" in read(PYPROG) and "$st -ne $lastKey" in read(PYPROG), "Write-Progress cost"),
        check("b542 central launcher has its own six checks (speed change must not eat a line or an rc)",
              PYPROG_TEST.is_file() and "stdout" in read(PYPROG_TEST), str(PYPROG_TEST)),
        check("Celeritas canonical mount exists", CELERITAS.is_file(), str(CELERITAS)),
        check("Aegis canonical mount exists", AEGIS.is_file(), str(AEGIS)),
        check("network is OFF by default in roster", '"network_default": "OFF"' in read(ROSTER_JSON), "fail-closed"),
        check("central registries mention accelerator control", "via_accelerator_control" in reg_text or "CGC_MDL156" in reg_text, "central registry references"),
        check("QuantGuard-only active policy is registered", POLICY_SSOT.is_file() and '"status": "ACTIVE"' in read(POLICY_SSOT) and '"legacy_indicator_library": "FORBIDDEN_NOT_USED"' in read(POLICY_SSOT), "policy SSOT"),
        check("QuantGuard data flow is VDF/DuckDB -> QuantGuard", '"direction": "VDF_DUCKDB_TO_QUANTGUARD"' in read(POLICY_SSOT) and '"source_mutation": "FORBIDDEN"' in read(POLICY_SSOT), "one-way policy SSOT"),
        check("QuantGuard bridge declares one-way source guard", '"direction": "VDF_DUCKDB_TO_QUANTGUARD"' in read(QUANTGUARD) and '"source_read_only": True' in read(QUANTGUARD), "ENG086 bridge"),
    ]
    # TA-Lib is permanently prohibited. Scan only canonical active mounts;
    # retired/reference material is intentionally not treated as an active path.
    forbidden = re.compile(r"(?im)^\s*(?:from\s+talib\s+import|import\s+talib)|_si\(\s*['\"]talib['\"]\)|['\"]talib['\"]")
    active_hits = []
    for path in (CELERITAS, AEGIS, QUANTGUARD):
        match = forbidden.search(read(path))
        if match:
            active_hits.append(f"{path.name}:{match.group(0).strip()}")
    out.append(check("canonical active mounts contain no TA-Lib path", not active_hits, "; ".join(active_hits) or "QuantGuard only"))
    # Count active Python files that receive the bootstrap transitively.
    py_files = []
    for base in (ROOT / "functional modules", ROOT / "supportive modules"):
        if base.exists():
            py_files.extend(p for p in base.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts)
    out.append(check("Python active tree is non-empty", bool(py_files), f"python_files={len(py_files)}"))
    return out


# ===== 批567 操作員令「所有 PY 指令加入加速器 · 所有 VDF 加入網路工具」=====
# **先量再說**。量出來的結果跟「還沒做」相反,所以這一批做的不是去加,是把**已經成立的事實
# 釘成一道會自己講話的閘**——不然下一支新引擎漏掉,沒有人會發現。
#
#   加速器橋:活樹 .py 2,698 支,帶橋 2,614,缺 84。而那 84 支拆開來是
#             尾版現役 7 · 舊版(非尾版)59 · 產物/新模組夾 18。
#             再看那 7 支尾版——**沒有一支是我可以動的**:
#               4 支 收容件 VIA_CentralGovernanceFamily_b514/*(正本零觸碰)
#               2 支 supportive modules/ssot/*(正典金融機構 SSOT,READ_ONLY)
#               1 支 tests/test_master_control_contract_v0102.py(測試檔,不是引擎)
#             所以「所有 PY 加入加速器」**已經到位**,剩下的全是**依律不得改**的。
#   VDF 網路:VDF 尾版 90 支,不觸網 62、走正典網路件 28、**生網路呼叫 0**。
#             「所有 VDF 加入網路工具」**也已經到位**。
#
# 這兩條現在各配一檢,且**免驗名單寫在碼裡並附理由**——名單要能被讀、被質疑、被改,
# 而不是一個我口頭說「那幾支不算」的數字(L57 誠實分母)。
import re as _re567

#: 免驗名單:每一條都附**為什麼不得改**,不是「懶得處理」
_ACCEL_EXEMPT = (
    ("supportive modules/VIA_Central_Governance/", "收容件家族:正本零觸碰,只能用 importlib 讀"),
    ("supportive modules/ssot/VIA_Financial_Institution_SSOT", "正典金融機構 SSOT:READ_ONLY"),
    ("supportive modules/ssot/VIA_FinancialInstitution_Overlay", "正典疊加層:裁定權在操作員"),
    ("/tests/", "測試檔不是引擎,不吃加速器橋"),
)


#: 批575 全樹分母:每一類「沒問」都要附理由(L57 誠實分母 → L68 尺不得比律窄)
#: 這份名冊的用途不是把數字做漂亮,是讓「沒問到的那些」可以被讀、被質疑、被改。
_TREE_EXEMPT = (
    ("__pycache__", "位元快取,不是原始碼"),
    ("/references/intake/", "收容件:正本零觸碰,只收不掛線"),
    ("RetiredEngines", "已退役:只增不減的墓園,不接回活動調度"),
    ("_backup", "備份副本"),
    ("VIA_Reports", "產物夾,不是原始碼"),
    ("new modules engines", "未納管暫存區:進了 supportive/functional 才算活件"),
    (".venv", "第三方虛境"),
    ("site-packages", "第三方套件"),
    ("_vdf_envs", "家族虛境"),
    ("quarantine", "隔離區"),
    ("SCOPE_COPY", "凍結範圍副本"),
    ("VIA_Standalone_Package", "打包產物"),
    ("50_Protection_Acceleration", "批180 凍結群:兩支獨立工具不可動"),
    ("_syntaxfix_", "語法修復暫存"),
    ("rename_runs", "改名紀錄"),
    ("rollback", "回滾紀錄"),
    ("_review_quarantine", "覆核隔離"),
    ("package_samples", "樣本"),
    ("_rebuilds_superseded", "已被取代的重建"),
    ("_from_vap_iso_cleanup", "VAP 隔離清理殘件"),
    ("_inbox_to_classify", "未分類收件匣"),
    ("_sha", "指紋副本"),
    ("evidence", "存證夾"),
    ("docs/history", "歷史文件"),
    ("VeritasAutoPlot_v42_EcoSystem", "外部生態系收容"),
    ("webscraping_dualengine", "外部收容"),
    ("TALib/vendor", "L50 禁用件:只保留 append-only 稽核"),
    ("/dict/", "字典資料"),
    ("_via_mother_root_reconciliation_runs", "母根對帳紀錄"),
    ("VIA_Central_Governance/", "收容件家族:正本零觸碰,只能用 importlib 讀"),
    ("/tests/", "測試檔不是引擎,不吃加速器橋"),
)

#: 批575:兩支獨立工具的正典掛載點(批345 操作員令「這兩個獨立工具不可動」)
INTAKE_B575 = ROOT / "supportive modules" / "references" / "intake" / "VIA_TwoTools_b575"
MOUNT_PAIRS = (
    ("VeritasCeleritas.py", ROOT / "supportive modules" / "VeritasCeleritas.py"),
    ("VeritasAegisNexus.py", ROOT / "supportive modules" / "network" / "VeritasAegisNexus.py"),
)
SUPER_CANON_GLOB = "SUP_MDL737_SuperAccelModule_v*.py"


def _lf_sha(p: Path) -> str | None:
    """行尾正規化後的指紋(批546:CRLF 與 LF 是同一份內容,不該判成兩份)。"""
    try:
        return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    except Exception:
        return None


def _tree_census(tails: set[str]) -> dict[str, Any]:
    """批575:把全樹分母攤開。尺問了幾支、沒問幾支、沒問的落在哪一類、有沒有『不明原因沒問』。"""
    total = asked = nontail = 0
    byex: dict[str, int] = {}
    unknown: list[str] = []
    for q in ROOT.rglob("*.py"):
        total += 1
        sp = str(q).replace("\\", "/")
        hit = next((f for f, _w in _TREE_EXEMPT if f in sp), None)
        if hit:
            byex[hit] = byex.get(hit, 0) + 1
            continue
        if str(q) in tails:
            asked += 1
        elif _re567.search(r"_v\d{4}\.py$", q.name):
            nontail += 1                      # 尾版律:同家族只問最後一支
        else:
            unknown.append(sp)
    return {"total": total, "asked": asked, "exempt": byex, "nontail": nontail, "unknown": unknown}


def _cel_resolve_order() -> list[str]:
    """讀 SUP_MDL737 尾版裡的 CEL_CANDIDATES(純文字解析,零匯入零副作用)。"""
    hits = sorted((ROOT / "supportive modules").glob(SUPER_CANON_GLOB))
    if not hits:
        return []
    m = _re567.search(r"CEL_CANDIDATES\s*=\s*\(([^)]*)\)", read(hits[-1]))
    return _re567.findall(r'"([^"]+)"', m.group(1)) if m else []


def _live_tail_py(root: Path):
    """活樹**尾版**的 .py(去版號分家族,各取最後一支);排除快取/收容/退役/備份/產物。"""
    fam: dict[str, list[Path]] = {}
    for q in root.rglob("*.py"):
        sp = str(q)
        if any(x in sp for x in ("__pycache__", "references/intake", "RetiredEngines",
                                 "_backup", "VIA_Reports", "new modules engines")):
            continue
        key = str(q.parent) + "/" + _re567.sub(r"_v\d{4}\.py$", "", q.name)
        fam.setdefault(key, []).append(q)
    return [sorted(v, key=lambda x: x.name)[-1] for v in fam.values()]


def coverage_checks() -> list[dict[str, Any]]:
    """批567 兩檢:加速器橋全樹覆蓋 · VDF 零生網路呼叫。"""
    out: list[dict[str, Any]] = []
    tails = _live_tail_py(ROOT)
    missing = []
    for q in tails:
        try:
            t = q.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "[VIA:ACCEL-BRIDGE" in t:
            continue
        rel = str(q.relative_to(ROOT)).replace("\\", "/")
        if any(k in "/" + rel for k, _ in _ACCEL_EXEMPT):
            continue
        missing.append(rel)
    out.append(check(
        "every live tail .py carries the accelerator bridge (exemptions are named and justified)",
        not missing,
        (f"tails={len(tails)} missing={len(missing)}: " + "; ".join(missing[:4])) if missing
        else f"tails={len(tails)} · 全覆蓋 · 免驗 {len(_ACCEL_EXEMPT)} 類(收容件/READ_ONLY SSOT/測試檔)"))

    RAW = _re567.compile(r"\b(requests\.(get|post|put|Session)|urllib\.request\.(urlopen|Request)"
                         r"|urlopen\(|httpx\.|aiohttp\.|yfinance\.|yf\.download)")
    CANON = ("SUP_MDL740", "NetUnified", "AegisNexus", "net_unified", "http_bytes", "post_json")
    vdf = [q for q in tails if "functional modules/VDF" in str(q).replace("\\", "/")]
    raw_only, via_canon, no_net = [], 0, 0
    for q in vdf:
        t = q.read_text(encoding="utf-8", errors="replace")
        if not RAW.search(t):
            no_net += 1
            continue
        if any(c in t for c in CANON):
            via_canon += 1
        else:
            raw_only.append(q.name)
    out.append(check(
        "no VDF tail engine reaches the network outside the canonical net tool",
        not raw_only,
        (f"vdf={len(vdf)} raw_only={len(raw_only)}: " + "; ".join(raw_only[:4])) if raw_only
        else f"vdf={len(vdf)} · 不觸網 {no_net} · 走正典網路件 {via_canon} · 生呼叫 0"))

    # ── ③ 批575:分母攤得開嗎(L68 尺不得比律窄)──────────────────────────────
    cen = _tree_census({str(q) for q in tails})
    out.append(check(
        "全樹分母攤得開:每一支沒被問到的 .py 都落在具名豁免類或尾版律(L68)",
        not cen["unknown"],
        f"全樹 {cen['total']} 支 = 尾版 {len(tails)}(第①檢分母,全問)+ 非尾版舊版 "
        f"{cen['total'] - len(tails)}(尾版律:同家族只問最後一支)· "
        f"具名豁免 {sum(cen['exempt'].values())} 支/{len(cen['exempt'])} 類(其中 "
        f"{len(tails) - cen['asked']} 支同時是尾版,尺仍然問了它們——寧可問多)· "
        + (f"**不明原因沒問 {len(cen['unknown'])}**:" + "; ".join(cen["unknown"][:4])
           if cen["unknown"] else "**不明原因沒問 0**")))

    # ── ④ 批115「VDF 全導入令」的正向尺(舊尺是負向的,兩者不等價)──────────
    vdf_live = [q for q in vdf
                if not any(f in str(q).replace("\\", "/") for f, _w in _TREE_EXEMPT)]
    vdf_no_net = [str(q.relative_to(ROOT)).replace("\\", "/") for q in vdf_live
                  if "[VIA:NET-BRIDGE" not in q.read_text(encoding="utf-8", errors="replace")]
    out.append(check(
        "批115 VDF 全導入令(正向尺):每一支 VDF 活件尾版都掛了統包網路工具橋",
        not vdf_no_net,
        (f"VDF 活件 {len(vdf_live)}(尾版 {len(vdf)} 扣具名豁免 {len(vdf)-len(vdf_live)})· "
         f"掛橋 {len(vdf_live)-len(vdf_no_net)} · **缺 {len(vdf_no_net)}**:" + "; ".join(vdf_no_net[:6]))
        if vdf_no_net else
        f"VDF 活件 {len(vdf_live)}(尾版 {len(vdf)} 扣具名豁免 {len(vdf)-len(vdf_live)})· 全掛 · "
        f"正向尺與負向尺(第②檢)兩邊都乾淨"))

    # ── ⑤ 兩支工具的解析順序講得出來 ────────────────────────────────────────
    order = _cel_resolve_order()
    first = next((c for c in order if (ROOT / "supportive modules" / c).is_file()), None)
    out.append(check(
        "加速器本體的解析順序可指(SUP_MDL737 CEL_CANDIDATES)且首位存在",
        bool(order) and first is not None,
        f"順序 {order} · 執行期實際載入 supportive modules/{first}" if first
        else f"順序 {order or 'ABSENT'} · **首位解析不到任何檔**"))

    # ── ⑥ L50 曝險:解析首位帶不帶 talib 路徑(活違規=紅;惰性曝險=點名待裁定)──
    talib_live = False
    try:
        import importlib.util as _ilu575
        talib_live = _ilu575.find_spec("talib") is not None
    except Exception:
        talib_live = False
    first_txt = read(ROOT / "supportive modules" / first) if first else ""
    first_has_talib = bool(_re567.search(r'_si\(\s*["\']talib["\']\s*\)|^\s*import\s+talib\b',
                                        first_txt, _re567.M))
    clean = [c for c in order
             if (ROOT / "supportive modules" / c).is_file()
             and not _re567.search(r'_si\(\s*["\']talib["\']\s*\)|^\s*import\s+talib\b',
                                   read(ROOT / "supportive modules" / c), _re567.M)]
    if not first_has_talib:
        d = f"解析首位 {first} 無 talib 路徑 · L50 合規"
    elif talib_live:
        d = (f"**L50 活違規**:解析首位 {first} 帶 talib 惰性路徑,且本境 find_spec('talib') 找得到"
             f" → 執行期會真的載入。L50 合規本 {clean or '無'}")
    else:
        d = (f"**PENDING_OPERATOR**:解析首位 {first} 帶 talib 惰性路徑,本境 talib 未安裝故未活化;"
             f"L50 合規本 {clean or '無'} 排在後面=執行期永遠解析不到。"
             f"一行修法=SUP_MDL737 的 CEL_CANDIDATES 把合規本提到第一(不動兩支工具本體);"
             f"**裁定權在操作員**(批345 不可動律)")
    out.append(check(
        "L50 QuantGuard-only:加速器解析首位不得帶可活化的 talib 路徑",
        (not first_has_talib) or (not talib_live), d))

    # ── ⑦ 操作員手上的正本 vs 庫內掛載本(行尾正規化)────────────────────────
    drift = []
    for name, mount in MOUNT_PAIRS:
        src = INTAKE_B575 / name
        a, b = _lf_sha(src), _lf_sha(mount)
        if a is None:
            drift.append(f"{name}:收容正本 ABSENT")
        elif b is None:
            drift.append(f"{name}:掛載本 ABSENT")
        elif a != b:
            drift.append(f"{name}:正本 {a[:12]} ≠ 掛載本 {b[:12]}")
    out.append(check(
        "操作員收容正本(批575)與庫內掛載本指紋一致(CRLF/LF 正規化後比)",
        not drift,
        "; ".join(drift) if drift
        else f"兩件皆同一份 · {INTAKE_B575.name} · 掛載點 " +
             " / ".join(str(m.relative_to(ROOT)).replace("\\", "/") for _n, m in MOUNT_PAIRS)))
    return out


def run(write: bool = True) -> dict[str, Any]:
    try:
        roster = load_json(ROSTER_JSON)
        load_error = None
    except Exception as exc:  # pragma: no cover - emitted in status
        roster = {}
        load_error = f"{type(exc).__name__}: {exc}"
    checks = roster_checks(roster) if not load_error else [check("SSOT roster JSON parse", False, load_error)]
    checks.extend(runtime_checks())
    checks.extend(coverage_checks())          # 批567:兩條覆蓋率閘
    passed = sum(1 for x in checks if x["ok"])
    failed = len(checks) - passed
    verdict = "GREEN" if failed == 0 else "RED"
    payload = {
        "schema": "VIA.CGC156.AcceleratorControl.v1",
        "engine": "CGC_MDL156_VIAAcceleratorControl_v0100",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "control_state": "READY_FOR_25" if verdict == "GREEN" else "DO_NOT_GENERATE_25",
        "checks": checks,
        "counts": {"total": len(checks), "pass": passed, "fail": failed, "accelerators": len(roster.get("accelerators", []))},
        "mounts": {name: {"path": str(path), "exists": path.is_file(), "sha256": sha256(path)} for name, path in {"superaccel": SUPERACC, "celeritas": CELERITAS, "aegis": AEGIS}.items()},
        "generation_policy": "Only generate/execute accelerator modules after this report is GREEN and registry-sync is idempotent.",
    }
    if write:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        LATEST_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        LATEST_HTML.write_text(render_html(payload), encoding="utf-8")
    return payload


def render_html(payload: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(str(x['name']))}</td><td class='{x['state']}'>{x['state']}</td><td>{html.escape(str(x.get('detail','')))}</td></tr>"
        for x in payload["checks"]
    )
    c = payload["counts"]
    return f"""<!doctype html>
<html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA 25 Accelerator Control</title>
<style>body{{font:14px system-ui,sans-serif;margin:32px;color:#172033}}h1{{margin-bottom:4px}}.pill{{padding:5px 12px;border-radius:999px;font-weight:700}}.GREEN,.PASS{{background:#d9f2e9;color:#08745b}}.RED,.FAIL{{background:#ffe1df;color:#a52b25}}table{{border-collapse:collapse;width:100%;margin-top:22px}}th,td{{border-bottom:1px solid #dfe5ee;padding:9px;text-align:left;vertical-align:top}}th{{background:#f4f7fb}}code{{white-space:pre-wrap}}</style></head>
<body><h1>VIA 25 加速器中央線控驗收</h1><p><span class='pill {payload['verdict']}'>{payload['verdict']}</span> <b>{payload['control_state']}</b> · {payload['timestamp']}</p>
<p>PASS {c['pass']} / {c['total']} · accelerators={c['accelerators']}</p><table><thead><tr><th>檢查</th><th>狀態</th><th>細節</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""


def selftest() -> int:
    payload = run(write=True)
    c = payload["counts"]
    print(f"[CGC_MDL156] {payload['verdict']} · {c['pass']}/{c['total']} · accelerators={c['accelerators']}")
    print(f"JSON: {LATEST_JSON}")
    print(f"HTML: {LATEST_HTML}")
    return 0 if payload["verdict"] == "GREEN" else 2



# ===== 批534:VIA 全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck/總控頁);本引擎原只認位置動詞。=====
# 等價轉換,只增不減:旗標 → 位置動詞(L39 U/I 對接契約律;一個功能一種呼叫法)。
_FLAG_VERBS_B534 = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes"}


def _normalise_argv_b534(argv):
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS_B534 and verb is None:
            verb = _FLAG_VERBS_B534[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out

def main() -> int:
    parser = argparse.ArgumentParser(description="VIA 25 accelerator control plane")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    sub.add_parser("status")
    sub.add_parser("manifest")
    sub.add_parser("routes")
    args = parser.parse_args(_normalise_argv_b534(sys.argv[1:]))   # 批534:旗標=位置動詞(L39)
    if args.cmd == "selftest":
        return selftest()
    payload = run(write=True)
    if args.cmd == "routes":
        print(json.dumps({"powershell": str(PS_ROSTER), "python_bootstrap": str(BOOTSTRAP), "network": "VDF only and operator consent", "generation": payload["control_state"]}, ensure_ascii=False, indent=2))
    elif args.cmd == "manifest":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"verdict": payload["verdict"], "control_state": payload["control_state"], "counts": payload["counts"], "json": str(LATEST_JSON), "html": str(LATEST_HTML)}, ensure_ascii=False, indent=2))
    return 0 if payload["verdict"] == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
