#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_subsys_manager_v0103 — 三子系統管理模組(TOOL-099,批99)
====================================================================
v0101→v0102(批99 操作員四裁+全權授權):+裁決道 --adjudicate——
對參數冊衝突套用核定規則表寫入 canonical 區(append-only 留痕):
  R1 MARKETS=US_INDICES 鍵名體系(現役 SSOT)+成員聯集只增不減
  R2 路徑類(DIR/PATH/ROOT/BASE/OUTPUT)=動態解析嚴禁寫死
  R3 END_DATE/截止日=TODAY 預設+可覆寫固定 YYYY-MM-DD
  R4 純數值=取涵蓋較大值;集合/清單/字典=聯集(只增不減)
  R5 per-engine 常數(DUCKDB_FILENAME/HTML 模板等)=SCOPED 非真衝突
  R6 HTTP_USER_AGENT='Mozilla/5.0 VeritasDataForge/VDF' 統一
  R7 其餘字串=取最完整(最長)值
引擎改讀 canonical=逐引擎版本前進(原件零觸碰)。
====================================================================
v0100→v0101(批98 參數抽離令「參數要從引擎中抽出由子系統管理者
統一管理」):+參數收割道 --params——AST 抽各引擎模組頂層大寫常數
(literal 可求值者)入 {SUB}_Param_Registry_v0100.json(append-only;
name/value/src/lineno);跨引擎同名異值=衝突燈列報。層級:引擎→
子系統參數冊(本管理者)→via-params 中央樞紐(母系統 S3)。引擎
原件零觸碰;引擎改讀冊=逐引擎版本前進候令。
====================================================================
操作員令:批95「三個子系統管理模組建立同步進行」+批97 焦點四柱
(母系統中央+支援性模組+VRN/VDF/VAP,其他凍結待令)。

單一參數化管理引擎管三子系統(VSM 遞迴原則:每個 S1 子系統自身是
可存活系統,管理者對「單元可存活」負責):
  · 憲章對讀   讀 {SUB}_Subsystem_Manifest.json(收容回歸件)之
               role/integration_state/governance,對照現況
  · 盤點      引擎(py)/啟動器(ps1)/知識冊(json)/介面(html)四類件數
  · 健康      AST 通過率(py 全掃,_sha 鏡像除外)→RYG 燈
  · S1-S5 迷你報 S1 引擎群/S2 介面契約件/S3 註冊台帳覆蓋/
               S3* selftest 掛站/S4 knowledge 冊/S5 憲章在位
  · 矩陣輸出   console 矩陣+JSON 存證 VIA_Reports/subsys_runs/
全唯讀;動碼一律版本前進候令。
用法:
  via-subsys --sub VRN|VDF|VAP|ALL   → 管理報(預設 ALL)
  via-subsys --params [VRN|VDF|VAP|ALL] → 參數收割入冊+衝突燈
  via-subsys --adjudicate [VRN|VDF|VAP|ALL] → 批99 規則表裁決入 canonical 區
  via-subsys --selftest              → 十七檢(沙盒零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RUNS = VIA / "VIA_Reports" / "subsys_runs"
SUBS = ("VRN", "VDF", "VAP")
SKIP = ("_sha", "__pycache__", ".venv", "site-packages", "quarantine", "rollback",
        "_vdf_envs", "webscraping_dualengine")
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")


def _files(root: Path, suffix: str):
    for p in root.rglob(f"*{suffix}"):
        if any(f in str(p) for f in SKIP):
            continue
        yield p


def manage(sub: str, via: Path = VIA) -> dict:
    root = via / "functional modules" / sub
    r = {"sub": sub, "root_ok": root.is_dir()}
    if not r["root_ok"]:
        r["light"] = "RED"
        r["note"] = "子系統根目錄不存在"
        return r
    mf_path = root / f"{sub}_Subsystem_Manifest.json"
    manifest = {}
    if mf_path.exists():
        try:
            manifest = json.loads(mf_path.read_text(encoding="utf-8-sig"))
        except ValueError:
            manifest = {"_parse_error": True}
    r["charter"] = {"present": bool(manifest) and "_parse_error" not in manifest,
                    "role": str(manifest.get("role", "—"))[:80],
                    "integration_state": str(manifest.get("integration_state", "—"))[:40],
                    "governance": bool(manifest.get("governance"))}
    py = list(_files(root, ".py"))
    ps1 = list(_files(root, ".ps1"))
    kn = list(_files(root, ".json"))
    ui = list(_files(root, ".html"))
    ok = bad = 0
    bad_list = []
    for p in py:
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
            ok += 1
        except (SyntaxError, ValueError, RecursionError):
            bad += 1
            bad_list.append(p.name)
    rate = round(ok / max(1, ok + bad) * 100, 1)
    r["inventory"] = {"py": len(py), "ps1": len(ps1), "knowledge_json": len(kn), "ui_html": len(ui)}
    r["health"] = {"ast_ok": ok, "ast_bad": bad, "rate": rate, "bad_top": bad_list[:8]}
    r["light"] = "GREEN" if bad == 0 else ("YELLOW" if bad <= 3 else "RED")
    # VSM 迷你報(遞迴:子系統自身的五系統)
    grid = sorted((via / "supportive modules" / "registry").glob("CGC_MDL064_SelftestGrid_v0*.py"))
    gtxt = grid[-1].read_text(encoding="utf-8", errors="ignore") if grid else ""
    r["vsm"] = {
        "S1_engines": len(py),
        "S2_contracts": sum(1 for k in kn if "SSOT" in k.name or "Registry" in k.name
                            or "Manifest" in k.name or "Params" in k.name),
        "S3_ledger_hook": bool((via / "supportive modules" / "registry"
                                / "VIA_AutoCode_Registry_v0100.json").exists()),
        "S3star_grid_hook": (sub in gtxt) or (sub.lower() in gtxt),
        "S4_knowledge": len([k for k in kn if "knowledge" in str(k).lower()
                             or "SSOT" in k.name]) ,
        "S5_charter": r["charter"]["present"],
    }
    return r


def _literal_preview(node):
    try:
        v = ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        return None
    r = repr(v)
    return r if len(r) <= 120 else r[:117] + "..."


def harvest_params(sub: str, via: Path = VIA, write: bool = True) -> dict:
    """批98:引擎頂層大寫常數收割入子系統參數冊(append-only;原件零觸碰)"""
    root = via / "functional modules" / sub
    if not root.is_dir():
        return {"sub": sub, "error": "無根目錄"}
    reg_path = root / f"{sub}_Param_Registry_v0100.json"
    reg = {"schema": "via-subsys-param-registry-v1", "sub": sub,
           "policy": "append-only;引擎原件零觸碰;引擎改讀冊=版本前進候令;上繳 via-params 中央樞紐",
           "params": []}
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8-sig"))
        except ValueError:
            pass
    known = {(x["name"], x["src"]) for x in reg["params"]}
    added = []
    for p in _files(root, ".py"):
        rp = str(p.relative_to(root)).replace("\\", "/")
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, ValueError, RecursionError):
            continue
        for node in tree.body:
            if not isinstance(node, ast.Assign) or not node.targets:
                continue
            name = getattr(node.targets[0], "id", None)
            if not name or not name.isupper() or len(name) < 3 or name.startswith("_"):
                continue
            pv = _literal_preview(node.value)
            if pv is None:
                continue
            if (name, rp) in known:
                continue
            e = {"name": name, "value": pv, "src": rp, "lineno": node.lineno,
                 "harvested": NOW}
            reg["params"].append(e)
            known.add((name, rp))
            added.append(e)
    by_name = {}
    for x in reg["params"]:
        by_name.setdefault(x["name"], set()).add(x["value"])
    conflicts = [{"name": k, "values": sorted(v)[:4], "n_variants": len(v)}
                 for k, v in sorted(by_name.items()) if len(v) > 1]
    if added and write:
        reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"sub": sub, "total": len(reg["params"]), "added": len(added),
            "distinct_names": len(by_name), "conflicts": conflicts,
            "registry": str(reg_path.name)}


def _looks_abspath(v) -> bool:
    """值形態路徑偵測:'C:\\...' 系(repr 內含跳脫)或 POSIX 絕對路徑字串"""
    t = str(v).strip().strip("'\"")
    return bool(re.match(r"^[A-Za-z]:[\\/]", t)) or t.startswith(("/home/", "/Users/", "\\\\"))


def _adjudicate_one(name: str, values: list) -> tuple:
    """批99 規則表:回 (ruling, rationale)"""
    up = name.upper()
    if up == "MARKETS":
        return ("<UNION:US_INDICES 鍵名體系+成員聯集>",
                "R1 操作員裁:US_INDICES/TAIWAN_INDICES 體系(現役 SSOT);成員聯集只增不減(含 ^NDX/^RUT)")
    if any(k in up for k in ("DIR", "PATH", "ROOT", "BASE", "OUTPUT", "FOLDER")):
        return ("<DYNAMIC:自引擎位置向上解析 VIA 根>", "R2 操作員裁:全部改新路徑=動態解析,嚴禁寫死絕對路徑")
    # R2 值形態閘(v0103):名不含 PATH 但值是絕對路徑(OUT_*/UNIVERSE_SOURCE 型漏網教訓)
    if values and all(_looks_abspath(v) for v in values):
        return ("<DYNAMIC:自引擎位置向上解析 VIA 根;舊絕對路徑入 variants 存證>",
                "R2 操作員裁:全部改新路徑=動態解析,嚴禁寫死絕對路徑(值形態偵測)")
    if "END_DATE" in up or up in ("DEADLINE", "CUTOFF_DATE"):
        return ("<TODAY;可覆寫 YYYY-MM-DD>", "R3 操作員裁:截止日預設最新,單筆可改固定日期")
    if up in ("DUCKDB_FILENAME", "HTML", "TEMPLATE", "DB_FILENAME") or up.endswith("_FILENAME"):
        return ("SCOPED(per-engine)", "R5 各引擎自有檔名/模板=同名不同用途,非真衝突")
    if up == "HTTP_USER_AGENT":
        return ("'Mozilla/5.0 VeritasDataForge/VDF'", "R6 全權統一:去 MDL 尾綴")
    nums = []
    for v in values:
        try:
            nums.append(float(v))
        except (ValueError, TypeError):
            nums = None
            break
    if nums:
        pick = max(values, key=lambda x: float(x))
        return (pick, "R4 純數值取涵蓋較大值(全權統一)")
    if all(str(v).lstrip().startswith(("{", "[", "(")) or str(v).startswith(("set(", "frozenset(")) for v in values):
        return ("<UNION:聯集>", "R4 集合/清單/字典=聯集(只增不減,全權統一)")
    pick = max(values, key=lambda x: len(str(x)))
    return (str(pick)[:120], "R7 字串取最完整值(全權統一)")


def adjudicate_params(sub: str, via: Path = VIA) -> dict:
    root = via / "functional modules" / sub
    reg_path = root / f"{sub}_Param_Registry_v0100.json"
    if not reg_path.exists():
        return {"sub": sub, "error": "參數冊不存在(先跑 --params)"}
    reg = json.loads(reg_path.read_text(encoding="utf-8-sig"))
    by_name = {}
    for x in reg["params"]:
        by_name.setdefault(x["name"], set()).add(x["value"])
    canon = reg.setdefault("canonical", {})
    ruled_now = 0
    for name, vals in sorted(by_name.items()):
        if len(vals) < 2 or name in canon:
            continue
        ruling, why = _adjudicate_one(name, sorted(vals))
        canon[name] = {"ruling": ruling, "rationale": why,
                       "variants": sorted(vals)[:6], "batch": "批99",
                       "authority": "操作員四裁+全權授權(2026-08-21)",
                       "apply": "引擎改讀 canonical=逐引擎版本前進(原件零觸碰)"}
        ruled_now += 1
    if ruled_now:
        reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"sub": sub, "ruled_now": ruled_now, "canonical_total": len(canon)}


def adjudicate_report(subs, via: Path = VIA) -> dict:
    out = {"schema": "VIA.SubsysAdjudicate.v1", "ts": NOW, "subs": []}
    for s in subs:
        r = adjudicate_params(s, via)
        out["subs"].append(r)
        if "error" in r:
            print(f"  [{s}] FAIL · {r['error']}")
        else:
            print(f"  [{s}] 本輪裁決 {r['ruled_now']} · canonical 累計 {r['canonical_total']}")
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / f"SUBSYS_ADJ_{NOW}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  [裁] 規則表=批99 四裁+全權授權;引擎改讀 canonical 逐引擎版本前進候排program")
    return out


def params_report(subs, via: Path = VIA) -> dict:
    out = {"schema": "VIA.SubsysParams.v1", "ts": NOW, "subs": []}
    for s in subs:
        r = harvest_params(s, via)
        out["subs"].append(r)
        if "error" in r:
            print(f"  [{s}] FAIL · {r['error']}")
            continue
        print(f"  [{s}] 冊 {r['registry']} · 參數 {r['total']}(本輪 +{r['added']})· "
              f"名 {r['distinct_names']} · 衝突 {len(r['conflicts'])}")
        for c in r["conflicts"][:8]:
            print(f"        [衝突] {c['name']} × {c['n_variants']} 值:{c['values']}")
    RUNS.mkdir(parents=True, exist_ok=True)
    ev = RUNS / f"SUBSYS_PARAMS_{NOW}.json"
    ev.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [存證] {ev.name} · 衝突裁決與引擎改讀冊=候操作員令(版本前進)")
    return out


def report(subs, via: Path = VIA, save: bool = True) -> dict:
    out = {"schema": "VIA.SubsysManager.v1", "ts": NOW, "subs": []}
    for s in subs:
        m = manage(s, via)
        out["subs"].append(m)
        if not m["root_ok"]:
            print(f"  [{s}] RED · {m['note']}")
            continue
        c, h, v = m["charter"], m["health"], m["vsm"]
        print(f"  [{s}] {m['light']} · 憲章={'在位' if c['present'] else '缺'}"
              f"({c['integration_state']}) · 引擎 py {m['inventory']['py']}"
              f"/ps1 {m['inventory']['ps1']}/冊 {m['inventory']['knowledge_json']}"
              f"/UI {m['inventory']['ui_html']} · AST {h['rate']}%(壞 {h['ast_bad']})")
        print(f"        VSM:S1 引擎 {v['S1_engines']} · S2 契約 {v['S2_contracts']}"
              f" · S3 台帳 {'✓' if v['S3_ledger_hook'] else '✗'}"
              f" · S3* grid {'✓' if v['S3star_grid_hook'] else '✗'}"
              f" · S4 知識 {v['S4_knowledge']} · S5 憲章 {'✓' if v['S5_charter'] else '✗'}")
        if h["ast_bad"]:
            print(f"        壞件候修:{h['bad_top']}")
    lights = [m.get("light", "RED") for m in out["subs"]]
    out["overall"] = "RED" if "RED" in lights else ("YELLOW" if "YELLOW" in lights else "GREEN")
    if save:
        RUNS.mkdir(parents=True, exist_ok=True)
        ev = RUNS / f"SUBSYS_{NOW}.json"
        ev.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  [計] 三子系統總燈 {out['overall']} · 存證 {ev.name}")
    return out


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (via / "supportive modules" / "registry" / "VIA_AutoCode_Registry_v0100.json").write_text("{}", encoding="utf-8")
        (via / "supportive modules" / "registry" / "CGC_MDL064_SelftestGrid_v0999.py").write_text(
            "# VRN VDF stations", encoding="utf-8")
        for s, good in (("VRN", True), ("VDF", False)):
            d = via / "functional modules" / s
            d.mkdir(parents=True)
            (d / f"{s}_Subsystem_Manifest.json").write_text(json.dumps(
                {"subsystem": s, "role": "測試子系統", "integration_state": "ACTIVE",
                 "governance": {"g": 1}}), encoding="utf-8")
            (d / "engine_a.py").write_text("def a():\n pass\n", encoding="utf-8")
            (d / "K_SSOT.json").write_text("{}", encoding="utf-8")
            if not good:
                (d / "broken.py").write_text("def broken(:\n", encoding="utf-8")
        # ① 憲章對讀
        m = manage("VRN", via)
        chk("憲章對讀", m["charter"]["present"] and m["charter"]["integration_state"] == "ACTIVE"
            and m["charter"]["governance"])
        # ② 盤點四類
        chk("盤點四類", m["inventory"]["py"] == 1 and m["inventory"]["knowledge_json"] == 2)
        # ③ 健康綠燈
        chk("健康綠燈", m["light"] == "GREEN" and m["health"]["rate"] == 100.0)
        # ④ 壞件黃燈+候修清單
        m2 = manage("VDF", via)
        chk("壞件黃燈", m2["light"] == "YELLOW" and m2["health"]["bad_top"] == ["broken.py"])
        # ⑤ VSM 六欄
        chk("VSM 迷你報", m["vsm"]["S1_engines"] == 1 and m["vsm"]["S2_contracts"] == 2
            and m["vsm"]["S3_ledger_hook"] and m["vsm"]["S5_charter"])
        # ⑥ S3* grid 掛站偵測
        chk("grid 掛站偵測", m["vsm"]["S3star_grid_hook"] and m2["vsm"]["S3star_grid_hook"])
        # ⑦ 缺根=RED 誠實
        m3 = manage("VAP", via)
        chk("缺根 RED", m3["light"] == "RED" and not m3["root_ok"])
        # ⑧ 總報+總燈(RED 傳播)
        global RUNS
        _r = RUNS
        RUNS = via / "runs"
        try:
            out = report(["VRN", "VDF", "VAP"], via)
        finally:
            RUNS = _r
        chk("總燈傳播", out["overall"] == "RED")
        # ⑨ 存證落檔
        chk("存證落檔", len(list((via / "runs").glob("SUBSYS_*.json"))) == 1)
        # ⑩ 憲章缺=誠實(拔掉 manifest)
        (via / "functional modules" / "VRN" / "VRN_Subsystem_Manifest.json").unlink()
        m4 = manage("VRN", via)
        chk("憲章缺誠實", not m4["charter"]["present"] and not m4["vsm"]["S5_charter"])
        # ⑪-⑭ 參數收割道(批98)
        d = via / "functional modules" / "VRN"
        (d / "engine_a.py").write_text(
            "TIMEOUT_S = 30\nRETRY_MAX = 3\n_PRIV = 1\nDYN = open\ndef a():\n pass\n",
            encoding="utf-8")
        (d / "engine_b.py").write_text("TIMEOUT_S = 60\n", encoding="utf-8")
        r = harvest_params("VRN", via)
        chk("參數收割入冊", r["added"] == 3 and r["total"] == 3
            and (d / "VRN_Param_Registry_v0100.json").exists())
        chk("私名/動態值不收", all(x["name"] not in ("_PRIV", "DYN")
            for x in json.loads((d / "VRN_Param_Registry_v0100.json")
                                .read_text(encoding="utf-8"))["params"]))
        chk("同名異值衝突燈", len(r["conflicts"]) == 1
            and r["conflicts"][0]["name"] == "TIMEOUT_S"
            and r["conflicts"][0]["n_variants"] == 2)
        r2 = harvest_params("VRN", via)
        chk("收割冪等 append-only", r2["added"] == 0 and r2["total"] == 3)
        # ⑮-⑰ 裁決道(批99 規則表)
        (d / "engine_c.py").write_text(
            "BASE_DIR = 'C:/old/path'\nDB_SUFFIXES = ['.db']\n", encoding="utf-8")
        (d / "engine_d.py").write_text(
            "BASE_DIR = 'D:/other'\nDB_SUFFIXES = ['.db', '.duckdb']\n", encoding="utf-8")
        harvest_params("VRN", via)
        ra = adjudicate_params("VRN", via)
        reg = json.loads((d / "VRN_Param_Registry_v0100.json").read_text(encoding="utf-8"))
        c = reg["canonical"]
        chk("裁決:路徑動態化+數值取大", c["BASE_DIR"]["ruling"].startswith("<DYNAMIC")
            and c["TIMEOUT_S"]["ruling"] == "60")
        chk("裁決:聯集規則", c["DB_SUFFIXES"]["ruling"].startswith("<UNION"))
        rb = adjudicate_params("VRN", via)
        chk("裁決冪等", rb["ruled_now"] == 0 and rb["canonical_total"] == ra["canonical_total"])
    n = 17 - len(fails)
    print(f"  [計] 十七檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 三子系統管理模組 v0102 · 十七檢(沙盒零網路)===")
        return selftest()
    subs = list(SUBS)
    if "--params" in a:
        i = a.index("--params")
        v = a[i + 1].upper() if i + 1 < len(a) and not a[i + 1].startswith("-") else "ALL"
        subs2 = list(SUBS) if v == "ALL" else ([v] if v in SUBS else None)
        if subs2 is None:
            print(f"[用法] --params VRN|VDF|VAP|ALL(收到 {v})")
            return 2
        print("=== 子系統參數收割(TOOL-099 批98)· 引擎→子系統冊→中央樞紐 ===")
        params_report(subs2)
        return 0
    if "--adjudicate" in a:
        i = a.index("--adjudicate")
        v = a[i + 1].upper() if i + 1 < len(a) and not a[i + 1].startswith("-") else "ALL"
        subs3 = list(SUBS) if v == "ALL" else ([v] if v in SUBS else None)
        if subs3 is None:
            print(f"[用法] --adjudicate VRN|VDF|VAP|ALL(收到 {v})")
            return 2
        print("=== 參數衝突裁決(TOOL-099 批99 規則表)===")
        adjudicate_report(subs3)
        return 0
    if "--sub" in a:
        i = a.index("--sub")
        v = a[i + 1].upper() if i + 1 < len(a) else "ALL"
        if v != "ALL":
            if v not in SUBS:
                print(f"[用法] --sub VRN|VDF|VAP|ALL(收到 {v})")
                return 2
            subs = [v]
    print("=== 三子系統管理模組(TOOL-099)· VSM 遞迴管理報 ===")
    report(subs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
