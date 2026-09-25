#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL183_CeleritasPolicyGate v0100 — Celeritas 產出契約閘(批715 · 執法 L102)

操作員 2026-09-23 令:「測試整合優化這個新加入棄標註版本取代現有,所有 PY 黨都要加入,
AI 若生成 PS 檔都要加入其功能模板,INTO ONE PY ENGINE REGISTER AND
MAKE IT A POLICY AS HIGHER PRIORITY」。

**先量再修**(LL400)。批715 量出來的四件:

| 項 | 實測 | 是哪一種 |
|---|---|---|
| .py 加速橋 | 2583 面 · **18 支從來沒有橋卻一直被報成綠的** | **尺壞了**(不是缺件) |
| .ps1 模板章 | 838 支一支都沒有 | **既有債**(L70:.ps1 是操作員的手) |
| PS 稽核規則 | 新引擎 ANC-30 已經有 `xps_audit` | **有正主,不可以再寫第二把** |
| 批345 不可動律 | 舊正本一個位元組沒動 | 新版**並存**不是覆蓋 |

那 18 支的根因寫在這裡,因為它值得記一輩子:舊導入器判「已橋」的條件是
`"VeritasCeleritas" in text or "VIA_SuperAccel_Module" in text` ——
**文中提到加速器的名字,就算有橋**。而這兩支加速器正本自己都帶著真標記,
所以那道守衛從來沒有保護過任何東西,**只是一台把假綠寫進報表的機器**。

律:唯讀 · 零網路 · 委派不重寫(PS 稽核一律問引擎)· 基線在資料檔不在碼裡 ·
既有債照列不當綠 · 凍結夾具名豁免不混進分母。
用法:python3 CGC_MDL183_CeleritasPolicyGate_v0100.py [--selftest]
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ENGINE_ID = "CGC_MDL183_CeleritasPolicyGate"
VERSION = "v0100"
BATCH = "批715"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BASELINE = HERE / "VIA_CeleritasPolicy_Baseline_v0100.json"
# LL133 自我指涉:本支的原始碼裡就寫著它在數的那個標記(PY_MARK),
# 所以掃描時**把自己整個家族排掉** —— 一把尺不進自己的分母,否則數的是自己。
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]
PY_MARK = "[VIA:ACCEL-BRIDGE"
PS_MARK = "CELERITAS-TEMPLATE-" + "JOIN"          # 拆寫:本支不是模板,不該被當成接好的產出


def baseline() -> dict:
    """基線從**資料檔**來。讀不到就回空 —— 不內建一份(批709 那 102 條字面路徑的教訓)。"""
    try:
        return json.loads(BASELINE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _excluded():
    """掃描面的排除清單**問正典**(L77)。導入器不在就誠實回 None,不自己列一張。"""
    try:
        cand = sorted(HERE.glob("via_accel_injector_v*.py"))
        spec = importlib.util.spec_from_file_location("_inj", cand[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["_inj"] = m
        spec.loader.exec_module(m)
        return m.excluded
    except Exception:
        return None


def engine_path() -> Path:
    """唯一正主:尾版 VeritasCeleritas_v*.py。**不含批345 那支無版號正本**(不可動律)。"""
    c = sorted((VIA / "supportive modules").glob("VeritasCeleritas_v*.py"))
    return c[-1] if c else Path("")


def _engine():
    """PS 稽核**委派給引擎**(ANC-30),本支一條規則都不抄(LL404)。"""
    p = engine_path()
    if not p.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("_cel", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["_cel"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def scan(root: Path | None = None) -> dict:
    """全樹掃 .py 與 .ps1,逐支分態。排除清單問正典;問不到就誠實 NODATA(不硬掃)。"""
    root = root or VIA
    ex = _excluded()
    if ex is None:
        return {"state": "NODATA", "why": "排除清單正典問不到(L77);硬掃出來的分母是假的"}
    B = baseline()
    debt = set((B.get("ps1_debt") or {}).get("files") or [])
    exempt = set((B.get("py_exempt") or {}).get("files") or [])
    ro = set((B.get("py_readonly") or {}).get("files") or [])
    selfex = set((B.get("ps1_self") or {}).get("files") or [])
    py = {"n": 0, "bridged": 0, "exempt": 0, "self": 0, "readonly": 0, "missing": []}
    ps = {"n": 0, "joined": 0, "debt": 0, "self": 0, "new_missing": []}
    for p in root.rglob("*.py"):
        rp = str(p.relative_to(root)).replace("\\", "/")
        if ex(rp):
            continue
        if p.stem.rsplit("_v", 1)[0] == _SELF_FAMILY:
            py["self"] += 1                       # LL133:尺不進自己的分母
            continue
        py["n"] += 1
        if PY_MARK in p.read_text(encoding="utf-8", errors="ignore"):
            py["bridged"] += 1
        elif rp in ro:
            py["readonly"] += 1                   # 正典唯讀本:**不算綠也不算紅,算「不准碰」**
        elif rp in exempt:
            py["exempt"] += 1                     # 凍結夾:具名豁免,**不算綠也不算紅**
        else:
            py["missing"].append(rp)
    for p in root.rglob("*.ps1"):
        rp = str(p.relative_to(root)).replace("\\", "/")
        if ex(rp):
            continue
        ps["n"] += 1
        if PS_MARK in p.read_text(encoding="utf-8", errors="ignore"):
            ps["joined"] += 1
        elif rp in selfex:
            ps["self"] += 1
        elif rp in debt:
            ps["debt"] += 1                       # 既有債:照列,**不當綠也不當違律**
        else:
            ps["new_missing"].append(rp)          # 基線以外新冒出來的 —— 這才是紅
    py["state"] = "GREEN" if not py["missing"] else "RED"
    ps["state"] = "GREEN" if not ps["new_missing"] else "RED"
    return {"state": "GREEN" if py["state"] == ps["state"] == "GREEN" else "RED",
            "py": py, "ps": ps}


def report() -> int:
    s = scan()
    if s["state"] == "NODATA":
        print(f"  [NODATA] {s['why']}")
        return 2
    py, ps = s["py"], s["ps"]
    print(f"  [PY ] 掃描面 {py['n']} · 帶橋 {py['bridged']} "
          f"({py['bridged'] * 100 / max(py['n'], 1):.1f}%) · 凍結夾具名豁免 {py['exempt']} · "
          f"自家族排除 {py['self']}(LL133)· 正典唯讀本 {py['readonly']} · 缺 {len(py['missing'])}")
    for m in py["missing"][:10]:
        print(f"   · 缺橋 {m}")
    print(f"  [PS ] 掃描面 {ps['n']} · 帶模板章 {ps['joined']} · 既有債 {ps['debt']}(L70:操作員的手)"
          f" · 自指豁免 {ps['self']} · **基線外新缺 {len(ps['new_missing'])}**")
    for m in ps["new_missing"][:10]:
        print(f"   · 新產出沒接模板 {m}")
    print(f"  [律] L102 rank=2(L50 仍是第一條)· 既有債不是違律,**基線外新增的一支都算紅**")
    return 0 if s["state"] == "GREEN" else 1


def selftest() -> int:
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print(f"=== Celeritas 產出契約閘 {VERSION}({BATCH} · 執法 L102)· 自測(沙盒 · 零網路 · 唯讀)===")
    B = baseline()
    cel = _engine()
    s = scan()

    # ① 排除清單問正典,問不到誠實 NODATA
    chk("① 掃描面的排除清單**問正典**(L77),不自己列一張。"
        "**負控**:正典問不到要誠實 NODATA —— 硬掃出來的分母是假的,比不掃還糟",
        callable(_excluded()) and s["state"] != "NODATA",
        f"(掃描面 py {s.get('py', {}).get('n')} · ps {s.get('ps', {}).get('n')})")

    # ② 提到名字 ≠ 有橋(批715 那 18 支的根因)
    mention = '"""只提到 VeritasCeleritas 與 VIA_SuperAccel' + '_Module,一行橋都沒有。"""\nx = 1\n'
    chk("② **提到加速器的名字 ≠ 有橋**(批715 根因):舊導入器用"
        "『文中出現加速器名字』當『已橋』,**18 支從來沒有橋卻一直被報成綠的**;"
        "而兩支加速器正本自己都帶真標記,那道守衛從來沒保護過任何東西。"
        "**正控**:判準只認標記本身",
        PY_MARK not in mention and PY_MARK in (HERE / "via_accel_injector_v0102.py").read_text(
            encoding="utf-8", errors="ignore"),
        f"(只提到名字→有橋? {PY_MARK in mention})")

    # ③ PS 稽核**委派給引擎**,本支不抄第二把尺
    bare = cel.xps_audit("Write-Host 1\n", name="bare.ps1") if cel else None
    good = cel.xps_join("Write-Host 1\n", name="gen.ps1") if cel else None
    gtext = (good or {}).get("text") or (good or {}).get("body") or ""
    chk("③ **PS 稽核一律問引擎**(ANC-30 的 `xps_audit` / `xps_join`),本支一條規則都不抄(LL404)。"
        "**正控**:`xps_join` 出來的要帶章;**負控**:裸 .ps1 要被判缺",
        cel is not None and bare is not None and not bare.get("joined")
        and bare.get("missing", 0) > 0 and PS_MARK in gtext,
        f"(裸→joined {None if not bare else bare.get('joined')}/缺 "
        f"{None if not bare else bare.get('missing')} · join 出來帶章 {PS_MARK in gtext})")

    # ④ 既有債照列不當綠;基線以外新冒出來的才是紅
    ps = s.get("ps", {})
    chk("④ **既有債棘輪**:樹上 838 支既有 .ps1 沒有模板章 —— 那是**既有債不是違律**"
        "(L70:未經操作員逐次許可不得修改任何 .ps1)。基線在**資料檔**不在碼裡(批709 教訓)。"
        "**負控**:基線以外新冒出來的一支都算紅,不然這道閘等於沒有",
        (ps.get("debt", 0) == len((B.get("ps1_debt") or {}).get("files") or [])
         and ps.get("debt", 0) > 0 and not ps.get("new_missing")),
        f"(既有債 {ps.get('debt')} · 基線外新缺 {len(ps.get('new_missing') or [])})")

    # ⑤ 批345 不可動律:舊正本一個位元組都沒動
    old = VIA / "supportive modules" / "VeritasCeleritas.py"
    want = ((B.get("immutable_b345") or {}).get("sha256") or "")
    got = hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else ""
    chk("⑤ **批345 不可動律**:新版以**尾版身分並存**,舊正本一個位元組都不准動。"
        "要不要把舊正本退役是**操作員的手**,不是我的",
        bool(want) and want == got and engine_path().name != old.name,
        f"(舊正本 hash 相符 {want == got} · 尾版正主 {engine_path().name})")

    # ⑥ LL133:尺不進自己的分母
    chk("⑥ **LL133 自我指涉**:本支原始碼裡就寫著它在數的那個標記,"
        "所以掃描時把**自己整個家族**排掉 —— 一把把自己算進去的尺,量的是自己不是樹。"
        "**負控**:排掉的要**報出來**(排了不說 = 分母偷偷變小)",
        _SELF_FAMILY == Path(__file__).stem.rsplit("_v", 1)[0]
        and s.get("py", {}).get("self", 0) >= 1
        and not any(m.split("/")[-1].startswith(_SELF_FAMILY) for m in s.get("py", {}).get("missing", [])),
        f"(自家族 {_SELF_FAMILY} · 排掉 {s.get('py', {}).get('self')})")

    # ⑦ 正典唯讀本:對的規則用錯檔,也是錯
    ro_f = ((B.get("py_readonly") or {}).get("files") or [])
    ro_ok = all((VIA / f).exists() and PY_MARK not in (VIA / f).read_text(encoding="utf-8", errors="ignore")
                for f in ro_f)
    chk("⑦ **正典唯讀本不准注**(批715 實錄):導入器依 L102① 把加速橋注進了機構 SSOT 正典唯讀本 —— "
        "**對的規則用在不該用的檔上**。唯讀的意思是連治理自己的改動也不准。"
        "已還原並具名豁免:不算綠也不算紅,算**不准碰**。"
        "**負控**:清單要有料且那幾支身上不准有橋(有橋=又被注回去了)",
        bool(ro_f) and ro_ok and s.get("py", {}).get("readonly", 0) == len(ro_f),
        f"(唯讀本 {len(ro_f)} 支 · 身上無橋 {ro_ok} · 掃到 {s.get('py', {}).get('readonly')})")

    # ⑧ 唯讀零網路
    src = (HERE / f"{ENGINE_ID}_{VERSION}.py").read_text(encoding="utf-8", errors="ignore")
    code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
    banned = [w for w in ("url" + "open", "requests." + "get", "write_" + "text(", "socket." + "socket")
              if w in code]
    chk("⑧ 唯讀零網路:本支只讀檔、只比對,不出網、不寫檔",
        not banned, f"(違禁 {banned or '無'})")

    n = len(ran) - len(fails)
    print(f"  [計] {len(ran)} 檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    print(f"=== Celeritas 產出契約閘 {VERSION}({BATCH} · 執法 L102)===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
