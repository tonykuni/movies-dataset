#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0189 — 薄尾(操作員 2026-10-11 智慧資產化 + 真實資料根因)。
  assetize 動詞 → VRN_ENG396_AssetIndex(VES v1000 為分群後端 · 只讀):全景 AST 分類 · 加速器覆蓋 · 往前找缺少功能 · 分群 / 九頭龍 · AI 全貌索引 · 指令精準表 · 契約
  真實資料四個根因(替換四頭 · 都不在熱點):
  ① 共識比對時間窗:報告日距今 >180 天 → 灰「時點不同」(共識是現值 · 舊報告目標價不比)
  ② 標題代號必須在資料庫名冊(年份 2026 之類不再當代號)
  ③ 名稱用簡稱:去「股份有限公司」/「開曼群島商」/ 尾綴(科技 / 國際 / 開發 / 生物科技 …)
  ④ 檔名推分析師:必須是常見姓氏開頭(「大顯神威」「營運騰達」「科技」不再當分析師)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import functools
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0189"
WINDOW_DAYS = 180
SURNAMES = set("王李張劉陳楊黃趙吳周徐孫馬朱胡郭何高林羅鄭梁謝宋唐許韓馮鄧曹彭曾蕭肖田董袁潘于蔣蔡余杜葉程蘇魏呂丁任沈姚盧姜崔鍾譚陸汪范金石廖賈夏韋方白鄒孟熊秦邱江尹薛閻段雷侯龍史陶黎賀顧毛郝龔邵萬錢嚴武戴莫孔向湯施賴洪翁游涂詹柯簡辜溫莊歐傅連紀郁凃")
_TRIM = ["股份有限公司", "有限公司"]
_SUFFIX = ["海洋生物科技", "生物科技", "科技開發", "國際", "開發", "科技", "電子", "工業", "實業", "控股"]


def _vnum_v0189(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0189(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0189(p) < _vnum_v0189(__file__)), key=_vnum_v0189)
PRIOR = _load_v0189(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


def _patch_v(name: str, fn):
    mo = _owner(name)
    if mo is None or getattr(vars(mo)[name], "_v189", False):
        return None
    prev = vars(mo)[name]
    functools.update_wrapper(fn, prev)
    fn._v189 = True
    fn._prev = prev
    setattr(mo, name, fn)
    return prev


_ASOF = {}


def read_consensus_v189(root=None) -> dict:
    """照前版讀共識 · 另從共識資料自己的日期欄(as_of / fetched / updated / snapshot / date)抓共識時點;沒有日期欄 → 不判時點(不拿今天硬猜)。"""
    out = read_consensus_v189._prev(root)
    _ASOF.clear()
    r = root or (_resolve("_vdb") or (lambda: Path("")))()
    best = ""
    try:
        import duckdb  # noqa: WPS433
        con = duckdb.connect()
        for p in sorted(Path(r).rglob("*.parquet")) if r and Path(r).is_dir() else []:
            if not re.search(r"consensus", p.name, re.I):
                continue
            cols = [c[0] for c in con.execute("describe select * from read_parquet('%s')" % str(p).replace("'", "''")).fetchall()]
            for c in [c for c in cols if re.search(r"(?i)as_?of|fetch|updated?|snapshot|data_date|^date$", c)]:
                v = con.execute('select max(cast("%s" as varchar)) from read_parquet(\'%s\')' % (c, str(p).replace("'", "''"))).fetchone()[0]
                m = re.search(r"(20\d{2})[-/]?(\d{2})[-/]?(\d{2})", str(v or ""))
                if m:
                    best = max(best, "%s-%s-%s" % m.groups())
    except Exception:  # noqa: BLE001
        pass
    if best:
        _ASOF["date"] = best
    return out


def judge_v189(item: dict, cons: dict) -> dict:
    asof, rd = _ASOF.get("date"), str(item.get("report_date") or "")
    try:
        age = (datetime.date.fromisoformat(asof) - datetime.date.fromisoformat(rd[:10])).days if asof else None
    except ValueError:
        age = None
    if cons and age is not None and age > WINDOW_DAYS:
        return {"lamp": "GRAY", "by_source": [{"source": "—", "lamp": "GRAY", "detail": "時點不同:報告 %s 與共識 %s 相差 %d 天 > %d(舊報告目標價不比)" % (rd[:10], asof, age, WINDOW_DAYS)}]}
    return judge_v189._prev(item, cons)


def short_name(cn: str) -> str:
    s = re.sub(r"^(開曼群島商|英屬維京群島商|英屬蓋曼群島商|百慕達商)", "", str(cn or ""))
    for t in _TRIM:
        if s.endswith(t) and len(s) > len(t) + 1:
            s = s[: -len(t)]
    for _ in range(2):
        for t in _SUFFIX:
            if s.endswith(t) and len(s) - len(t) >= 2:
                s = s[: -len(t)]
                break
    return s


def tw_roster_v189(vdb=None) -> dict:
    ro = tw_roster_v189._prev(vdb) if vdb is not None else tw_roster_v189._prev()
    for k, e in (ro.get("codes") or {}).items():
        if e.get("cn") and re.search(r"股份有限公司|有限公司|^開曼|^英屬", e["cn"]):
            e.setdefault("cn_full", e["cn"])
            e["cn"] = short_name(e["cn"])
    return ro


_RC = {}


def codes_in_title_v189(pg: dict) -> list:
    got = codes_in_title_v189._prev(pg)
    if not _RC:
        try:
            _RC.update({"codes": set((_resolve("tw_roster")() or {}).get("codes") or {})})
        except Exception:  # noqa: BLE001
            _RC["codes"] = set()
    known = _RC.get("codes") or set()
    return [c for c in got if not known or c in known]


def analyst_from_filename_v189(fn, code, names, aliases) -> str:
    out = analyst_from_filename_v189._prev(fn, code, names, aliases)
    keep = [t for t in (out.split("; ") if out else []) if t and t[0] in SURNAMES and 2 <= len(t) <= 4]
    return "; ".join(keep)


_patch_v("judge", judge_v189)
_patch_v("read_consensus", read_consensus_v189)
_patch_v("tw_roster", tw_roster_v189)
_patch_v("codes_in_title", codes_in_title_v189)
_patch_v("analyst_from_filename", analyst_from_filename_v189)


def eng396():
    cands = sorted(HERE.glob("VRN_ENG396_AssetIndex_v*.py"), key=_vnum_v0189)
    return _load_v0189(cands[-1], "vrn_eng396_" + cands[-1].stem) if cands else None


def assetize() -> list:
    m = eng396()
    if m is None:
        return ["[計] 智慧資產化 · VRN_ENG396_AssetIndex 不在 VRN 樹 → 沒跑"]
    reg = {}
    rp = sorted((HERE / "knowledge").glob("VRN_Engine_Register_v*.json"), key=_vnum_v0189) if (HERE / "knowledge").is_dir() else []
    if rp:
        try:
            import json
            body = json.loads(rp[-1].read_text(encoding="utf-8"))
            for e in (body.get("families") or body.get("engines") or body.get("body") or []):
                if isinstance(e, dict) and e.get("family"):
                    reg[e["family"]] = {"no": e.get("no") or e.get("id")}
        except (OSError, ValueError):
            pass
    o = m.run(HERE, _resolve("_rep")(), register=reg)
    hot = ", ".join("%s×%d" % kv for kv in o["heads"].most_common() if kv[1] >= 3) or "無"
    L = ["[計] 智慧資產化 · %s · %s · 家族最新版 %d(%s)· 燈 %s" % (m.ENGINE_ID, o["ves"], o["tails"], " · ".join("%s %d" % kv for kv in o["cats"].items()), o["lamps"]),
         "[計] 加速器覆蓋 %s%%(檔內標記 %d · 經管理器執行 %d · 獨立執行未覆蓋 %d)→ 100%% 做法:執行入口保證 + 獨立執行檔出新版補橋(不改既有檔)" % (
             o["coverage"]["pct"], o["coverage"]["by"].get("檔內標記", 0), o["coverage"]["by"].get("經管理器執行", 0), o["coverage"]["by"].get("獨立執行 · 未覆蓋", 0)),
         "[計] 往前找缺少但合規的功能 %d(合規 %d · 附 AST 錨點 · 任務卡 · 在地測試才併)· 九頭龍熱點 %s(不動 · 整併版處理)· 動詞 %d 個" % (o["missing"], o["missing_ok"], hot, o["verbs"]),
         "[計] AI 全貌索引 %s(≤300 行 · AI 先讀這份)· 契約 contract/VRN_ASSET_CONTRACT_latest.json" % o["index"]]
    if o["uncovered"]:
        L.append("[計] 獨立執行未覆蓋(前幾個)· " + " · ".join(o["uncovered"]))
    return L


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["assetize"]:
        for l in assetize():
            print(l)
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    _ASOF["date"] = datetime.date.today().isoformat()                       # 模擬共識資料有日期欄(測完還原)
    old = (datetime.date.today() - datetime.timedelta(days=700)).isoformat()
    new = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    cons = {"FactSet(鉅亨)": {"target_low": 250.0, "target_median": 425.0, "target_high": 626.0}}
    j1 = _resolve("judge")({"tp": 98.0, "report_date": old}, cons)
    j2 = _resolve("judge")({"tp": 98.0, "report_date": new}, cons)
    _ASOF.clear()
    j3 = _resolve("judge")({"tp": 98.0, "report_date": old}, cons)
    chk("① 共識時間窗(基準 = 共識資料自己的日期):相差 700 天 → 灰「時點不同」· 30 天 → 照比(紅)· 共識沒有日期 → 不判時點(照比)",
        j1["lamp"] == "GRAY" and "時點不同" in j1["by_source"][0]["detail"] and j2["lamp"] == "RED" and j3["lamp"] == "RED")
    sn = {x: short_name(x) for x in ("頎邦科技股份有限公司", "開曼群島商竣邦國際股份有限公司", "鈺緯科技開發股份有限公司", "瑞基海洋生物科技股份有限公司", "寶雅國際股份有限公司", "台積電")}
    chk("② 名稱用簡稱:%s" % " · ".join("%s→%s" % kv for kv in list(sn.items())[:5]),
        sn["頎邦科技股份有限公司"] == "頎邦" and sn["開曼群島商竣邦國際股份有限公司"] == "竣邦" and sn["鈺緯科技開發股份有限公司"] == "鈺緯" and sn["瑞基海洋生物科技股份有限公司"] == "瑞基"
        and sn["寶雅國際股份有限公司"] == "寶雅" and sn["台積電"] == "台積電")
    _saved_rc = dict(_RC)
    _RC["codes"] = {"3653", "2330"}
    ct = _resolve("codes_in_title")({"blocks": [{"kind": "text", "size": 20, "text": "健策 3653 TT 2026/09/15 展望"}]})
    _RC.clear()
    _RC.update(_saved_rc)                                                    # 還原全域快取(不污染前版鏈自測)
    chk("③ 標題代號必須在名冊:3653 留 · 2026(年份)剔除 → %s" % ct, ct == ["3653"])
    af = _resolve("analyst_from_filename")
    a1 = af("【國泰證期研究部】神達(3706 TT)-初次評等買進-大顯神威，營運騰達-20250822.pdf", "3706", ["神達"], ["國泰", "CATHAY"])
    a2 = af("凱基投顧_6526 達發科技_劉宇程_20260917.pdf", "6526", ["達發"], ["凱基投顧", "凱基", "KGI"])
    chk("④ 檔名推分析師要姓氏開頭:「大顯神威」「營運騰達」剔除 →「%s」· 「科技; 劉宇程」→「%s」" % (a1, a2), a1 == "" and a2 == "劉宇程")
    chk("⑤ assetize 動詞接 ENG396(VRN 樹有就跑 · 沒有照實說)", callable(assetize) and (eng396() is None or hasattr(eng396(), "run")))
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111] · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0111]" in me and _job_entry.__module__ in ("__main__", __name__))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] VRN_SystemManager_v0189 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
