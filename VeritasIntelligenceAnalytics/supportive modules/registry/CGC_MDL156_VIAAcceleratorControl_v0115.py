#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL156_VIAAcceleratorControl v0115 — 薄尾:名冊補 functional modules/VRN/nonstock_v0310/engine/(操作員原件 byte-exact · frozen_sources)

實錄(2026-11-06,操作員令「加速器導入 PS/PY 100%」· 橋掃 --subsystems 乾跑):VRN/accel 161/172,缺 11 支,其中 1 支是
functional modules/VRN/nonstock_v0310/engine/VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py —— 操作員上傳的非個股摘要器**原件**,
依 CLAUDE.md「操作員原件 byte-exact + frozen_sources SHA」凍結(交接冊 frozen_sources 有它的 SHA);注橋 = 改 bytes = 打破凍結。
同夾 reuse/vrn2/ 三支是 AI 寫的轉接器,不豁免(照注)。
本版:名冊(_ACCEL_EXEMPT · _TREE_EXEMPT)照 v0114 字面值整份抄,一字不動,只增 4 條:`functional modules/VRN/nonstock_v0310/engine/`(操作員原件)· `docs/handoff/ai/`(一行 SHA 釘住的發布包)· `functional modules/VQG/` · `supportive modules/agent_os/`(SettleAll PINNED);裝進 v0110 模組全域。
實錄 2:--subsystems --apply 的 ALL 總表那一趟也會注 docs/handoff/ai 的 33 支 VRN2_RoundAll 與 VQG v0105(一行 SHA 釘住的發布件)→ 本輪已還原 bytes,改用名冊豁免。
其餘照 v0114。只收 VCGC 呼叫。零網路。不用 TA-Lib。
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL156_VIAAcceleratorControl"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_v{_vnum(Path(__file__)):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_BASE = PRIOR._BASE                      # v0110 全本:runtime_checks / coverage 查的是它的模組全域

# ---- 名冊(字面值;CGC_MDL158 以 ast.literal_eval 讀;v0112 全部條目 + VRN 側收容件)----
_ACCEL_EXEMPT = (
    ('VIA_HTML_UI', '批647 正典 U/I TEMPLATE:byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;注入任何橋都會打破那份完整性,故正本零觸碰優先於全樹導入令。它的驗收走 `via-ui --check`(CGC_MDL160 template 車道),不走全樹雙橋'),
    ('supportive modules/VIA_Central_Governance/', '收容件家族:正本零觸碰,只能用 importlib 讀'),
    ('supportive modules/ssot/VIA_Financial_Institution_SSOT', '正典金融機構 SSOT:READ_ONLY'),
    ('supportive modules/ssot/VIA_FinancialInstitution_Overlay', '正典疊加層:裁定權在操作員'),
    ('/tests/', '測試檔不是引擎,不吃加速器橋'),
    ('/_patches/', '一次性補丁夾:跑完即退場,不是活引擎;不改他人併入的檔'),
    ('supportive modules/intake/', '收容件(supportive 側):凍結來源不改(CLAUDE.md;同 /references/intake/ 與 CGC_MDL183 凍結夾)——只收不掛線'),
    ('functional modules/VRN/intake/', '收容件(VRN 側):凍結來源不改(CLAUDE.md;同 supportive modules/intake/ 與 /references/intake/)——只收不掛線'),
    ('/envs/', '第三方虛擬環境:pip 產生的 Scripts/*.py 指令檔(例 pdfminer dumppdf.py / pdf2txt.py)與套件;倉內 envs/ 追蹤檔 0 支、.gitignore **/envs/ —— 不是 VIA 原始碼,絕不注入加速器橋'),
    ('functional modules/VRN/nonstock_v0310/engine/', '操作員原件(非個股摘要器 v0310 引擎)byte-exact:交接冊 frozen_sources 守 SHA;同夾 reuse/vrn2 轉接器照注'),
    ('docs/handoff/ai/', '交接一行 SHA-256 釘住的發布包(VRN2_RoundAll 各版 · VIA_SettleAll 各版 · 入倉原件):bytes 由一行守,注橋 = 打破釘;它們自己都帶第 3 行標記'),
    ('functional modules/VQG/', 'VQG 一行 SHA 釘住(SettleAll PINNED + frozen_sources);bytes 由一行守'),
    ('supportive modules/agent_os/', 'VIA Agent OS 一行 SHA 釘住(SettleAll PINNED);bytes 由一行守;v0102 第 3 行已帶標記'),
)

_TREE_EXEMPT = (
    ('VIA_HTML_UI', '批647 正典 U/I TEMPLATE:byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;注入任何橋都會打破那份完整性,故正本零觸碰優先於全樹導入令。它的驗收走 `via-ui --check`(CGC_MDL160 template 車道),不走全樹雙橋'),
    ('__pycache__', '位元快取,不是原始碼'),
    ('/references/intake/', '收容件:正本零觸碰,只收不掛線'),
    ('RetiredEngines', '已退役:只增不減的墓園,不接回活動調度'),
    ('_backup', '備份副本'),
    ('VIA_Reports', '產物夾,不是原始碼'),
    ('new modules engines', '未納管暫存區:進了 supportive/functional 才算活件'),
    ('.venv', '第三方虛境'),
    ('site-packages', '第三方套件'),
    ('_vdf_envs', '家族虛境'),
    ('quarantine', '隔離區'),
    ('SCOPE_COPY', '凍結範圍副本'),
    ('VIA_Standalone_Package', '打包產物'),
    ('50_Protection_Acceleration', '批180 凍結群:兩支獨立工具不可動'),
    ('_syntaxfix_', '語法修復暫存'),
    ('rename_runs', '改名紀錄'),
    ('rollback', '回滾紀錄'),
    ('_review_quarantine', '覆核隔離'),
    ('package_samples', '樣本'),
    ('_rebuilds_superseded', '已被取代的重建'),
    ('_from_vap_iso_cleanup', 'VAP 隔離清理殘件'),
    ('_inbox_to_classify', '未分類收件匣'),
    ('_sha', '指紋副本'),
    ('evidence', '存證夾'),
    ('docs/history', '歷史文件'),
    ('VeritasAutoPlot_v42_EcoSystem', '外部生態系收容'),
    ('webscraping_dualengine', '外部收容'),
    ('TALib/vendor', 'L50 禁用件:只保留 append-only 稽核'),
    ('/dict/', '字典資料'),
    ('_via_mother_root_reconciliation_runs', '母根對帳紀錄'),
    ('VIA_Central_Governance/', '收容件家族:正本零觸碰,只能用 importlib 讀'),
    ('/tests/', '測試檔不是引擎,不吃加速器橋'),
    ('/_patches/', '一次性補丁夾:跑完即退場,不是活引擎;不改他人併入的檔'),
    ('supportive modules/intake/', '收容件(supportive 側):凍結來源不改,只收不掛線(同 /references/intake/)'),
    ('functional modules/VRN/intake/', '收容件(VRN 側):凍結來源不改,只收不掛線(同 supportive modules/intake/)'),
    ('/envs/', '第三方虛擬環境(Windows venv 的 Scripts/ · Lib/;.gitignore **/envs/,倉內追蹤 0 支)'),
    ('functional modules/VRN/nonstock_v0310/engine/', '操作員原件(非個股摘要器 v0310 引擎)byte-exact:交接冊 frozen_sources 守 SHA;同夾 reuse/vrn2 轉接器照注'),
    ('docs/handoff/ai/', '交接一行 SHA-256 釘住的發布包(VRN2_RoundAll 各版 · VIA_SettleAll 各版 · 入倉原件):bytes 由一行守,注橋 = 打破釘;它們自己都帶第 3 行標記'),
    ('functional modules/VQG/', 'VQG 一行 SHA 釘住(SettleAll PINNED + frozen_sources);bytes 由一行守'),
    ('supportive modules/agent_os/', 'VIA Agent OS 一行 SHA 釘住(SettleAll PINNED);bytes 由一行守;v0102 第 3 行已帶標記'),
)

NEW_KEY = "functional modules/VRN/nonstock_v0310/engine/"
_BASE._ACCEL_EXEMPT = tuple(_ACCEL_EXEMPT) + PRIOR._P11._readonly_exempt()
_BASE._TREE_EXEMPT = tuple(_TREE_EXEMPT)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _literal(path: Path, name: str):
    import ast as _ast
    for n in _ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(n, _ast.Assign) and getattr(n.targets[0], "id", "") == name:
            return {k for k, _ in _ast.literal_eval(n.value)}
    return None


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    me = Path(__file__)
    for var in ("_ACCEL_EXEMPT", "_TREE_EXEMPT"):
        prior_keys, keys = _literal(_PRIOR_PATH, var), _literal(me, var)
        chk(f"① {var} 只增:v0114 條目全在 + {NEW_KEY}", prior_keys is not None and keys is not None and prior_keys <= keys and NEW_KEY in keys and len(keys) == len(prior_keys) + 4)
    chk("② 已裝進 v0110 模組全域(runtime / coverage 走本版名冊)",
        NEW_KEY in {k for k, _ in _BASE._ACCEL_EXEMPT} and NEW_KEY in {k for k, _ in _BASE._TREE_EXEMPT})
    ex = lambda rel: any(k in "/" + rel for k, _ in _BASE._ACCEL_EXEMPT)
    chk("②b 操作員原件 nonstock_v0310/engine · 一行 SHA 釘住的 docs/handoff/ai / VQG / agent_os 判豁免;同夾 reuse/vrn2 轉接器與活引擎不受影響;v0114 的 envs/ 照舊",
        ex("functional modules/VRN/nonstock_v0310/engine/VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py") and ex("envs/via_pdf_tools/Scripts/dumppdf.py")
        and ex("docs/handoff/ai/vrn2_release_v0179/VRN2_RoundAll_v0135.py") and ex("functional modules/VQG/VQG_AllInOne_v0105.py") and ex("supportive modules/agent_os/VIA_AgentOS_v0102.py")
        and not ex("functional modules/VRN/nonstock_v0310/reuse/vrn2/VRN_M07_Summarizer.py") and not ex("functional modules/VDF/VDF_SystemManager_v0168.py") and not ex("supportive modules/registry/CGC_MDL156_VIAAcceleratorControl_v0115.py"))
    rc = PRIOR.selftest()
    chk("③ 前版 v0114 自測(連 v0113 · v0112 · v0110 控制面全檢)GREEN", rc == 0)
    src = me.read_text(encoding="utf-8")
    chk("④ 加速器橋在 · 不 import TA-Lib · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and "HERE.glob(STEM" in src)
    print(f"[計] CGC_MDL156_VIAAcceleratorControl v0115 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 2


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
