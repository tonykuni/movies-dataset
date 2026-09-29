#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL245_SDDValidator v0102 — SDD 驗證器:工作流 SSOT 的自測 · 交叉測 · 實測 · 加鎖 · 收尾(薄尾:X-LOCK 依家族比尾版 · 失敗追因多兩種;R34 收尾實測)

  ① X-LOCK 看不到換版(R34 實測):燈鎖冊 wkf 區記的是「正主尾版的路徑 → 檔名」,路徑本身含版號;v0100 的 check_lock 拿這個
  路徑去對這次 check 的尾版表(也以含版號的路徑為鍵)—— 尾版一換,舊路徑在新表裡就查不到,被當成「沒換」跳過,
  於是 Polars 批把 ENG079 v0103→v0104 · ENG081 v0102→v0103 · ENG085 v0105→v0106 換掉之後 X-LOCK 仍是 GREEN,
  「尾版換了要重驗」這條律等於沒在看。現在以**家族**(路徑去掉 _vNNNN)為鍵比:換了 → YELLOW 點名 <工作流>:<鎖的版>→<現在的版>;
  家族已不在任何步上 → 也點名(→(不在步上)),不再默默略過。
  ② 為什麼要多兩種追因:R34 在沒有 PowerShell 的容器收尾 —— ENV MANAGER(CGC_MDL240)照自己的律把「必備執行檔 pwsh 不在 PATH」
  判 RED(rc 1),VCGC-WKF001-STP004 於是 FAIL;單一路徑驗證(CGC_MDL242)的 ① 讀同一份 ENV MANAGER 也跟著 RED →
  VCGC-WKF002-STP002 FAIL。兩者的補法都是「裝件」,依 L07/L08 是操作員的手(AI 不代裝),可是 v0100 的 fail_cause
  只認「DB 面板缺庫」一種因,兩條工作流就被當成 AI 端要修,收尾永遠 OPEN。
  現在 fail_cause 多兩種,照舊只讀正主自己這一輪寫的報告(ts 不早於本輪第一個事件),不是手寫理由:
    envmgr_exe_absent  ENV MANAGER 本輪報告裡**每一列** RED 都是「⑩ 執行檔 · X(必備)」且 PATH 上找不到 → 操作員端;
                       其他任何 RED(工具鎖版 sha 不對 · 加速器 / 網路 / LAYOUT / NLP 載不起來 …)混在裡面 = 追不到,照舊 FAIL。
    pathverify_traced  單一路徑驗證本輪報告的**每一步** RED 都追得到因:「DB 面板」步 → dbpanel_absent,「ENV MANAGER」步 →
                       envmgr_exe_absent;有一步追不到(或報告不是本輪)= 追不到,照舊 FAIL。它是 pathverify_dbpanel 的超集。
  掛法:v0100 的 check() / real() 叫的是 v0100 模組裡 check_lock · fail_cause 這兩個名字 → 本支換掉它們;舊兩種追因
  (dbpanel_absent · pathverify_dbpanel)原樣交回 v0100(前版照讀,不複製)。步驟冊寫哪一種,在 VIA_Workflow_<子系統>_SSOT 的步上 fail_cause。
  其餘一字未動。VIA_FROM_VCGC:只收中控呼叫(前版 main 守門)。不用 TA-Lib。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL245_SDDValidator_v0101.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("sdd_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
_BASE = getattr(PRIOR, "PRIOR", PRIOR)          # v0100:real() / check() / closeout() 的模組全域在這裡
PRIOR.ENGINE = ENGINE
_BASE.ENGINE = ENGINE
_BASE_FAIL_CAUSE = _BASE.fail_cause
KINDS = ("dbpanel_absent", "pathverify_dbpanel", "envmgr_exe_absent", "pathverify_traced")
_EXE_ROW = re.compile(r"^⑩ 執行檔 · (?P<exe>\S+?)[(（]必備[)）]$")      # ENV MANAGER 的必備執行檔列(半形 / 全形括號都認)


def _family(rel) -> str:
    """路徑去掉版號尾碼(…_v0102.py → ….py):同一支正主換版前後是同一個家族。"""
    return re.sub(r"_v\d+(?=\.[^./\\]+$)", "", str(rel))


def lock_moves(wkf: dict, versions: dict) -> list:
    """已鎖工作流記的正主尾版 vs 這次 check 的尾版(依家族比):不同 → <工作流>:<鎖的版>→<現在的版 | (不在步上)>。"""
    cur = {_family(r): (v or {}).get("tail") for r, v in (versions or {}).items()}
    return [f"{code}:{v}→{cur.get(_family(r)) or '(不在步上)'}" for code, rec in (wkf or {}).items()
            for r, v in (rec.get("versions") or {}).items() if cur.get(_family(r)) != v]


def check_lock(state, rows, versions):
    """v0102:X-LOCK 以家族為鍵比對(v0100 以含版號的路徑為鍵,尾版一換就對不到、當成沒換)。"""
    lk = _BASE.newest("VIA_LampLock_v*.json", _BASE.HERE)
    wkf = (_BASE._json(lk, {}) or {}).get("wkf") or {}
    if not wkf:
        _BASE._row(rows, "INFO", "X-LOCK", f"燈鎖冊 {lk.name if lk else '-'} 還沒有 wkf 區(第一次 lock 之後才有)")
        return
    moved = lock_moves(wkf, versions)
    _BASE._row(rows, "YELLOW" if moved else "GREEN", "X-LOCK",
               f"已鎖工作流的尾版換了,要重驗({len(moved)} 處):{moved[:6]}" if moved else
               f"已鎖 {len(wkf)} 條工作流,尾版都沒換(依家族比 · {lk.name})")


_BASE.check_lock = check_lock


def _report(*parts: str) -> dict:
    return _BASE._json(_BASE.VIA.joinpath("VIA_Reports", *parts), {}) or {}


def _fresh(d: dict, since: str) -> bool:
    return bool(since) and str(d.get("ts") or "").replace("T", " ")[:19] >= since[:19]


def envmgr_exe_absent(since: str) -> str:
    """ENV MANAGER 本輪報告:RED 列全是 PATH 上找不到的必備執行檔 → 回成因;否則回空字串(追不到)。"""
    d = _report("env_manager", "ENVMGR_latest.json")
    if not _fresh(d, since):
        return ""
    red = [r for r in d.get("rows") or [] if r.get("state") == "RED"]
    exe = [m.group("exe") for r in red for m in [_EXE_ROW.match(str(r.get("item") or ""))]
           if m and "找不到" in str(r.get("note") or "")]
    if not red or len(exe) != len(red):
        return ""
    return (f"缺必備執行檔 {' · '.join(exe)}:ENV MANAGER 本輪 RED {len(red)} 列全是 PATH 上找不到的必備執行檔"
            "(裝件是操作員的手 · L07/L08;AI 不代裝)")


def pathverify_traced(since: str) -> str:
    """單一路徑驗證本輪報告:每一步 RED 都追得到(DB 面板 → dbpanel_absent · ENV MANAGER → envmgr_exe_absent)。"""
    pv = _report("path_verify", "PATH_VERIFY_latest.json")
    if not _fresh(pv, since):
        return ""
    why = []
    for s in [s for s in pv.get("steps") or [] if s.get("state") == "RED"]:
        name = str(s.get("step") or "")
        c = (_BASE_FAIL_CAUSE("dbpanel_absent", since) if "DB 面板" in name else
             envmgr_exe_absent(since) if "ENV MANAGER" in name else "")
        if not c:
            return ""
        why.append(c)
    return ("單一路徑驗證的紅全追得到因 → " + " | ".join(dict.fromkeys(why))) if why else ""


def fail_cause(kind: str, since: str) -> str:
    """v0102:多 envmgr_exe_absent · pathverify_traced;其餘種類原樣交回 v0100。"""
    if kind == "envmgr_exe_absent":
        return envmgr_exe_absent(since)
    if kind == "pathverify_traced":
        return pathverify_traced(since)
    return _BASE_FAIL_CAUSE(kind, since)


_BASE.fail_cause = fail_cause


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import tempfile
    eng = "functional modules/VDF/engine/VDF_ENG081_UniverseAlign_v0102.py"
    pol = "supportive modules/registry/VIA_Policy_VRNTextScope_v0100.json"
    locked = {"VDF-WKF004": {"versions": {eng: "VDF_ENG081_UniverseAlign_v0102.py"}},
              "VRN-WKF003": {"versions": {pol: "VIA_Policy_VRNTextScope_v0100.json"}}}
    same = {eng: {"tail": "VDF_ENG081_UniverseAlign_v0102.py"}, pol: {"tail": "VIA_Policy_VRNTextScope_v0100.json"}}
    moved = {eng.replace("v0102", "v0103"): {"tail": "VDF_ENG081_UniverseAlign_v0103.py"}, pol: same[pol]}
    chk("① 家族鍵:去掉檔尾版號,不動夾名與沒版號的檔", _family(eng) == "functional modules/VDF/engine/VDF_ENG081_UniverseAlign.py"
        and _family("a_v0100/cli.py") == "a_v0100/cli.py" and _family(pol).endswith("VIA_Policy_VRNTextScope.json"))
    chk("② X-LOCK 依家族比:尾版沒換 → 沒有要重驗的", lock_moves(locked, same) == [])
    mv = lock_moves(locked, moved)
    chk("③ X-LOCK 依家族比:v0102 → v0103 點名", mv == ["VDF-WKF004:VDF_ENG081_UniverseAlign_v0102.py→VDF_ENG081_UniverseAlign_v0103.py"], mv)
    chk("④ X-LOCK:家族已不在任何步上 → 也點名,不默默略過", lock_moves(locked, {pol: same[pol]}) == ["VDF-WKF004:VDF_ENG081_UniverseAlign_v0102.py→(不在步上)"])
    blind = [c for c, rec in locked.items() for r, v in rec["versions"].items() if (moved.get(r) or {}).get("tail") and moved[r]["tail"] != v]
    chk("⑤ 對照:v0100 的比法(含版號路徑當鍵)在同一份資料上看不到換版 —— 本支修的就是這個", blind == [])
    saved_here = _BASE.HERE
    with tempfile.TemporaryDirectory() as td:
        try:
            _BASE.HERE = Path(td)
            rows = []
            check_lock(None, rows, moved)
            chk("⑥ check_lock:燈鎖冊還沒有 wkf 區 → INFO", rows and rows[-1]["lamp"] == "INFO" and rows[-1]["rule"] == "X-LOCK")
            (Path(td) / "VIA_LampLock_v0100.json").write_text(json.dumps({"wkf": locked}), encoding="utf-8")
            (Path(td) / "VIA_LampLock_v0101.json").write_text(json.dumps({"wkf": {"VRN-WKF003": locked["VRN-WKF003"]}}), encoding="utf-8")
            rows = []
            check_lock(None, rows, moved)
            chk("⑦ check_lock:讀燈鎖冊尾版(v0101),沒換 → GREEN", rows[-1]["lamp"] == "GREEN" and "v0101" in rows[-1]["msg"], rows[-1]["msg"][:60])
            (Path(td) / "VIA_LampLock_v0102.json").write_text(json.dumps({"wkf": locked}), encoding="utf-8")
            rows = []
            check_lock(None, rows, moved)
            chk("⑧ check_lock:尾版換了 → YELLOW 點名(1 處)", rows[-1]["lamp"] == "YELLOW" and "(1 處)" in rows[-1]["msg"], rows[-1]["msg"][:80])
        finally:
            _BASE.HERE = saved_here
    chk("⑨ v0100.check() 叫的就是本支的 check_lock(換掉模組全域)", _BASE.check_lock is check_lock)
    since = "2026-09-29 05:00:00"

    def env_rows(*extra):
        return [{"id": "A1", "item": "① 鎖版號 · accelerator", "state": "GREEN", "note": "sha 對"},
                {"id": "B10", "item": "⑩ 執行檔 · git(必備)", "state": "GREEN", "note": "/usr/bin/git"},
                {"id": "B10", "item": "⑩ 執行檔 · tesseract", "state": "AMBER", "note": "PATH 上找不到"}] + list(extra)
    pwsh_red = {"id": "B10", "item": "⑩ 執行檔 · pwsh(必備)", "state": "RED", "note": "PATH 上找不到", "fix": "必備:裝好並放進 PATH"}
    lock_red = {"id": "A1", "item": "① 鎖版號 · network", "state": "RED", "note": "sha 不對"}
    saved = _BASE.VIA
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        def put(rel, obj):
            p = root.joinpath("VIA_Reports", *rel.split("/"))
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")

        def env(rows, ts="2026-09-29 05:10:00"):
            put("env_manager/ENVMGR_latest.json", {"ts": ts, "verdict": "RED", "rows": rows})

        def pv(steps, ts="2026-09-29 05:20:00"):
            put("path_verify/PATH_VERIFY_latest.json", {"ts": ts, "verdict": "RED", "steps": steps})

        def panel(rows, errors, ts="2026-09-29 05:15:00"):
            put("dbmanager/DBM_PANEL_latest.json", {"ts": ts, "reconcile": {"rows": rows}, "errors": errors})
        env_step = {"step": "① ENV MANAGER(輔助工具 · 環境 · LIB)", "state": "RED"}
        db_step = {"step": "⑥ DB 面板", "state": "RED"}
        other = {"step": "② 註冊同步(registry-sync)", "state": "RED"}
        try:
            _BASE.VIA = root
            env(env_rows(pwsh_red))
            c = fail_cause("envmgr_exe_absent", since)
            chk("⑩ envmgr_exe_absent:本輪 RED 只有缺必備執行檔 → 操作員端,點名 pwsh", "pwsh" in c and "操作員的手" in c, c[:60])
            chk("⑪ envmgr_exe_absent:報告不是本輪(ts 早於本輪起點)→ 追不到", fail_cause("envmgr_exe_absent", "2026-09-29 05:30:00") == "")
            chk("⑫ envmgr_exe_absent:沒有本輪起點 → 追不到", fail_cause("envmgr_exe_absent", "") == "")
            env(env_rows(pwsh_red, lock_red))
            chk("⑬ envmgr_exe_absent:混一列工具鎖版 RED → 追不到(AI 端要修)", fail_cause("envmgr_exe_absent", since) == "")
            env(env_rows())
            chk("⑭ envmgr_exe_absent:沒有 RED 列 → 追不到(FAIL 不是這個因)", fail_cause("envmgr_exe_absent", since) == "")
            env(env_rows(dict(pwsh_red, note="/opt/pwsh 在但跑不起來")))
            chk("⑮ envmgr_exe_absent:必備執行檔在 PATH 上卻 RED → 追不到", fail_cause("envmgr_exe_absent", since) == "")
            env(env_rows(dict(pwsh_red, item="⑩ 執行檔 · pandoc")))
            chk("⑯ envmgr_exe_absent:只有必備(必備)才算,選配列 RED 不收", fail_cause("envmgr_exe_absent", since) == "")
            env(env_rows(pwsh_red))
            pv([env_step, {"step": "③ VDF 建庫計畫", "state": "AMBER"}])
            c = fail_cause("pathverify_traced", since)
            chk("⑰ pathverify_traced:唯一的紅是 ENV MANAGER 且追得到 → 操作員端", c.startswith("單一路徑驗證的紅全追得到因") and "pwsh" in c, c[:60])
            panel([{"state": "ABSENT"}], [{"state": "ABSENT"}])
            pv([env_step, db_step])
            c = fail_cause("pathverify_traced", since)
            chk("⑱ pathverify_traced:ENV MANAGER + DB 面板(只缺庫)兩個紅都追得到 → 兩個因都列", "pwsh" in c and "資料家缺庫" in c, c[:80])
            panel([{"state": "ABSENT"}], [{"state": "RED", "source": "清單"}])
            chk("⑲ pathverify_traced:DB 面板有真正 RED(清單)→ 追不到", fail_cause("pathverify_traced", since) == "")
            panel([{"state": "ABSENT"}], [{"state": "ABSENT"}])
            pv([env_step, other])
            chk("⑳ pathverify_traced:有一步紅不是這兩種 → 追不到", fail_cause("pathverify_traced", since) == "")
            pv([env_step], ts="2026-09-29 04:00:00")
            chk("㉑ pathverify_traced:路徑驗證報告不是本輪 → 追不到", fail_cause("pathverify_traced", since) == "")
            pv([{"step": "③ VDF 建庫計畫", "state": "AMBER"}])
            chk("㉒ pathverify_traced:沒有 RED 步 → 追不到(FAIL 不是這個因)", fail_cause("pathverify_traced", since) == "")
            env(env_rows(pwsh_red, lock_red))
            pv([env_step])
            chk("㉓ pathverify_traced:ENV MANAGER 本身追不到 → 路徑驗證也追不到", fail_cause("pathverify_traced", since) == "")
            pv([db_step])
            chk("㉔ 舊種類原樣交回 v0100:pathverify_dbpanel · dbpanel_absent 照舊判", "資料家缺庫" in fail_cause("pathverify_dbpanel", since)
                and "資料家缺庫" in fail_cause("dbpanel_absent", since))
            chk("㉕ 不認得的種類 → 追不到", fail_cause("no_such_kind", since) == "")
        finally:
            _BASE.VIA = saved
    chk("㉖ v0100.real() 叫的就是本支的 fail_cause(換掉模組全域)", _BASE.fail_cause is fail_cause and PRIOR.PRIOR is _BASE)
    chk("㉗ 報告與燈鎖冊記本支引擎名", _BASE.ENGINE == ENGINE and PRIOR.ENGINE == ENGINE)
    used = {}
    for sub in ("VCGC", "VDF", "VRN"):
        book = _BASE._json(_BASE.newest(f"VIA_Workflow_{sub}_SSOT_v*.json"), {}) or {}
        for w in book.get("workflows") or []:
            for s in w.get("steps") or []:
                if s.get("fail_cause"):
                    used[s["code"]] = s["fail_cause"]
    chk("㉘ 三冊尾版的 fail_cause 都是本支認得的種類", used and set(used.values()) <= set(KINDS), used)
    chk("㉙ VCGC 冊尾版:ENV MANAGER 步帶 envmgr_exe_absent · 路徑驗證步帶 pathverify_traced",
        used.get("VCGC-WKF001-STP004") == "envmgr_exe_absent" and used.get("VCGC-WKF002-STP002") == "pathverify_traced")
    body = Path(__file__).read_text(encoding="utf-8")
    chk("㉚ 本支帶加速器橋 · 網路橋 · VIA_FROM_VCGC 標記", "[VIA:ACCEL-BRIDGE" in body and "[VIA:NET-BRIDGE" in body and "VIA_FROM_VCGC" in body)
    chk("㉛ 不含 TA-Lib 匯入", not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M))
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
