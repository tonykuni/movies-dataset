#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL156_VIAAcceleratorControl v0112 — 薄尾:修兩項量測缺陷 + 名冊補 supportive 側收容件

via_precheck(CGC_MDL263)⑭ 量出控制面 RED 36/38,逐條查證都是**尺**的問題,不是 QuantGuard / 加速器壞:
  ① 「QuantGuard bridge declares one-way source guard」:v0110 只讀 ENG086 **尾版那一支檔**的字面;
     VDF_ENG086_QuantGuardOneBridge_v0102 是薄尾(承 v0101),單向宣告(direction / source_read_only)在 v0101 本體。
     本版沿薄尾鏈往前讀(檔內點名的同族前版,遞迴),宣告在鏈上任一版即算(薄尾律:前版的宣告仍生效)。
  ② 「canonical active mounts contain no TA-Lib path」:正則 ['\"]talib['\"] 命中 ENG086 v0102 的
     `policy['mode']['talib']!='forbidden'`——那是**強制禁用**的檢查,不是使用 TA-Lib。本版先剔除
     「['talib'] 與 'forbidden' 比較」這種執法字樣再比對;import talib / _si('talib') 照抓(L50 不放寬)。
  ③ 名冊(_ACCEL_EXEMPT · _TREE_EXEMPT)完整重寫為字面值(CGC_MDL158 只讀最新定義名冊的那一版),
     v0110 原有全部條目一字不動,只增 `supportive modules/intake/`(凍結收容件,同 /references/intake/)。
  加速器座位 accelerator/VeritasCeleritas.py 已依操作員令刪除(新的都有版號);v0111 起 CELERITAS 即版號尾版。
其餘照 v0111。只收 VCGC 呼叫。零網路。不用 TA-Lib。
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
_P11 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _P11
_spec.loader.exec_module(_P11)
_BASE = _P11._PRIOR                      # v0110 全本:runtime_checks / coverage 查的是它的模組全域

# ---- ③ 名冊(字面值;CGC_MDL158 以 ast.literal_eval 讀)----
_ACCEL_EXEMPT = (
    ('VIA_HTML_UI', '批647 正典 U/I TEMPLATE:byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;注入任何橋都會打破那份完整性,故正本零觸碰優先於全樹導入令。它的驗收走 `via-ui --check`(CGC_MDL160 template 車道),不走全樹雙橋'),
    ('supportive modules/VIA_Central_Governance/', '收容件家族:正本零觸碰,只能用 importlib 讀'),
    ('supportive modules/ssot/VIA_Financial_Institution_SSOT', '正典金融機構 SSOT:READ_ONLY'),
    ('supportive modules/ssot/VIA_FinancialInstitution_Overlay', '正典疊加層:裁定權在操作員'),
    ('/tests/', '測試檔不是引擎,不吃加速器橋'),
    ('/_patches/', '一次性補丁夾:跑完即退場,不是活引擎;不改他人併入的檔'),
    ('supportive modules/intake/', '收容件(supportive 側):凍結來源不改(CLAUDE.md;同 /references/intake/ 與 CGC_MDL183 凍結夾)——只收不掛線'),
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
)

_BASE._ACCEL_EXEMPT = tuple(_ACCEL_EXEMPT) + _P11._readonly_exempt()
_BASE._TREE_EXEMPT = tuple(_TREE_EXEMPT)

# ---- ① 薄尾鏈讀單向宣告 · ② TA-Lib 執法字樣不算使用 ----
GUARD_DIR = '"direction": "VDF_DUCKDB_TO_QUANTGUARD"'
GUARD_RO = '"source_read_only": True'
ENFORCE_RX = re.compile(r"\[\s*['\"]talib['\"]\s*\]\s*(?:!=|==)\s*['\"]forbidden['\"]")
FORBIDDEN_RX = re.compile(r"(?im)^\s*(?:from\s+talib\s+import|import\s+talib)|_si\(\s*['\"]talib['\"]\)|['\"]talib['\"]")


def tail_chain(path: Path, limit: int = 12) -> list:
    """薄尾鏈:本檔 → 檔內點名的同族前版(版號較小)→ … ;防循環、最多 limit 層。"""
    out, cur = [], Path(path)
    m = re.match(r"(.+?)_v(\d{4})$", cur.stem)
    fam = m.group(1) if m else cur.stem
    while cur.is_file() and cur not in out and len(out) < limit:
        out.append(cur)
        txt = cur.read_text(encoding="utf-8", errors="replace")
        vs = [int(v) for v in re.findall(re.escape(fam) + r"_v(\d{4})\.py", txt) if int(v) < _vnum(cur)]
        if not vs:
            break
        cur = cur.parent / f"{fam}_v{max(vs):04d}.py"
    return out


def guard_declared(path: Path) -> tuple:
    for p in tail_chain(path):
        t = p.read_text(encoding="utf-8", errors="replace")
        if GUARD_DIR in t and GUARD_RO in t:
            return True, p.name
    return False, ""


def talib_hit(text: str):
    return FORBIDDEN_RX.search(ENFORCE_RX.sub("", text))


_ORIG_RUNTIME = _BASE.runtime_checks


def runtime_checks() -> list:
    out = _ORIG_RUNTIME()
    for i, c in enumerate(out):
        if c["name"] == "QuantGuard bridge declares one-way source guard":
            ok, where = guard_declared(_BASE.QUANTGUARD)
            out[i] = _BASE.check(c["name"], ok, f"ENG086 bridge · 宣告在 {where}(薄尾鏈 {len(tail_chain(_BASE.QUANTGUARD))} 版)" if ok else "ENG086 bridge · 薄尾鏈上找不到單向宣告")
        elif c["name"] == "canonical active mounts contain no TA-Lib path":
            hits = []
            for path in (_BASE.CELERITAS, _BASE.AEGIS, _BASE.QUANTGUARD):
                m = talib_hit(_BASE.read(path))
                if m:
                    hits.append(f"{Path(path).name}:{m.group(0).strip()}")
            out[i] = _BASE.check(c["name"], not hits, "; ".join(hits) or "QuantGuard only(執法字樣 ['talib']!='forbidden' 不算使用)")
    return out


_BASE.runtime_checks = runtime_checks


def __getattr__(name: str):
    return getattr(_P11, name)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note and not cond else ""))

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "X_ENG_v0100.py").write_text('cfg = {"direction": "VDF_DUCKDB_TO_QUANTGUARD", "source_read_only": True}\n', encoding="utf-8")
        (d / "X_ENG_v0101.py").write_text('PRIOR = "X_ENG_v0100.py"\n', encoding="utf-8")
        (d / "Y_ENG_v0101.py").write_text('PRIOR = "Y_ENG_v0100.py"\n', encoding="utf-8")
        chk("① 薄尾鏈:宣告在前版也算", guard_declared(d / "X_ENG_v0101.py") == (True, "X_ENG_v0100.py"))
        chk("① 反例:鏈上都沒有宣告 = 缺", guard_declared(d / "Y_ENG_v0101.py")[0] is False)
    chk("② 執法字樣不算使用", talib_hit("if policy['mode']['talib']!='forbidden': raise") is None)
    chk("② 反例:import talib / _si('talib') / 'talib' 字串照抓",
        bool(talib_hit("import talib\n")) and bool(talib_hit("x=_si('talib')")) and bool(talib_hit("lib = 'talib'")))
    keys = {k for k, _ in _ACCEL_EXEMPT}
    import ast as _ast
    prior_acc = None
    for n in _ast.parse(Path(HERE / (STEM + "_v0110.py")).read_text(encoding="utf-8")).body:
        if isinstance(n, _ast.Assign) and getattr(n.targets[0], "id", "") == "_ACCEL_EXEMPT":
            prior_acc = {k for k, _ in _ast.literal_eval(n.value)}
    chk("③ 名冊只增:v0110 條目全在 + supportive modules/intake/", prior_acc is not None and prior_acc <= keys and "supportive modules/intake/" in keys)
    chk("③ 已裝進 v0110 模組全域(runtime / coverage 走本版)", _BASE.runtime_checks is runtime_checks and "supportive modules/intake/" in {k for k, _ in _BASE._ACCEL_EXEMPT})
    rc = _P11._PRIOR.selftest()
    chk("④ 控制面全檢(v0110 selftest)GREEN", rc == 0)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在 · 不 import TA-Lib", "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[計] CGC_MDL156_VIAAcceleratorControl v0112 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 2


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return _P11.main()


if __name__ == "__main__":
    raise SystemExit(main())
