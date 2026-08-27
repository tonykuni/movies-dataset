#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vdf_input_matrix_v0100 — VDF 整合輸入介面清單矩陣(TOOL-093,批88)
====================================================================
操作員令:「VDF 整合後的輸入介面清單矩陣並測試——國際股市每日交易
資訊/財報可增減項目+增減個股;台股單獨擷取只有財報(單季/累計/
年度+起始日期+整合輸入);VRN 只有文件路徑+輸入式重點(SUMMARY
MATRIX/BASIC INFO/FINANCIAL DATA);VIA 單雙軸繪圖新增堆圖」。

冊=VDF_Input_Interface_Matrix_v0100.json(活冊;種子承接
VDF_Unified_Params 既有清單)。零刪除語意:remove=軟移除入
removed_*(可 --restore 找回);changelog append-only。

用法:
  via-vdfin --show                              → 全矩陣列印
  via-vdfin --add-item INTL_DAILY turnover      → 增項目
  via-vdfin --remove-item INTL_DAILY volume     → 軟移除項目
  via-vdfin --add-ticker INTL_FIN AAPL          → 增個股
  via-vdfin --remove-ticker INTL_DAILY ^VIX     → 軟移除個股
  via-vdfin --restore INTL_DAILY volume         → 從 removed_* 找回
  via-vdfin --set-tw period 單季 / --set-tw start 2020-01-01
  via-vdfin --set-vrn path <文件路徑>
  via-vdfin --selftest                          → 十三檢(沙盒零網路)
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

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SSOT = HERE / "VDF_Input_Interface_Matrix_v0100.json"


def load(path: Path = None) -> dict:
    return json.loads((path or SSOT).read_text(encoding="utf-8-sig"))


def save(d: dict, path: Path = None, op: str = "", note: str = "") -> None:
    d.setdefault("changelog", []).append(
        {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"), "op": op, "note": note})
    (path or SSOT).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _sec(d: dict, name: str) -> dict:
    s = d["sections"].get(name)
    if s is None:
        raise KeyError(f"無此分區:{name}(有效:{'/'.join(d['sections'])})")
    return s


def _move(sec: dict, live_key: str, dead_key: str, val: str, to_dead: bool) -> str:
    """零刪除語意:增=入 live(從 dead 撈回);軟移除=live→dead;restore 反向"""
    live = sec.setdefault(live_key, [])
    dead = sec.setdefault(dead_key, [])
    if to_dead:
        if val not in live:
            return f"SKIP:{val} 不在 {live_key}"
        live.remove(val)
        if val not in dead:
            dead.append(val)
        return f"OK:{val} 軟移除入 {dead_key}(可 --restore 找回)"
    if val in live:
        return f"SKIP:{val} 已在 {live_key}"
    if val in dead:
        dead.remove(val)
    live.append(val)
    return f"OK:{val} 入 {live_key}"


def add_item(d, sec_name, val):   return _move(_sec(d, sec_name), "items", "removed_items", val, False)
def rm_item(d, sec_name, val):    return _move(_sec(d, sec_name), "items", "removed_items", val, True)
def add_ticker(d, sec_name, val): return _move(_sec(d, sec_name), "tickers", "removed_tickers", val, False)
def rm_ticker(d, sec_name, val):  return _move(_sec(d, sec_name), "tickers", "removed_tickers", val, True)


def restore(d, sec_name, val) -> str:
    sec = _sec(d, sec_name)
    for live, dead in (("items", "removed_items"), ("tickers", "removed_tickers"),
                       ("input_focus", "removed_focus"), ("modes", "removed_modes")):
        if val in sec.get(dead, []):
            return _move(sec, live, dead, val, False)
    return f"SKIP:{val} 不在任何 removed_*"


def set_tw(d, key, val) -> str:
    tw = _sec(d, "TW_FIN")
    if key == "period":
        if val not in tw["period_modes"]:
            return f"FAIL:period 僅限 {'/'.join(tw['period_modes'])}"
        tw["period_mode"] = val
        return f"OK:period_mode={val}"
    if key == "start":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", val):
            return "FAIL:start_date 需 YYYY-MM-DD"
        tw["start_date"] = val
        return f"OK:start_date={val}"
    return "FAIL:set-tw 僅 period/start"


def set_vrn(d, key, val) -> str:
    vr = _sec(d, "VRN")
    if key == "path":
        vr["doc_path"] = val
        return f"OK:doc_path={val}"
    return "FAIL:set-vrn 僅 path"


def show(d) -> None:
    print(f"  [冊] {d['schema']} · 分區 {len(d['sections'])} · changelog {len(d.get('changelog', []))}")
    for name, s in d["sections"].items():
        print(f"  ── {name} · {s['desc']}")
        for k in ("items", "tickers", "input_focus", "modes", "period_modes"):
            if k in s and s[k]:
                print(f"     {k}({len(s[k])}):{'、'.join(map(str, s[k]))}")
        for k in ("period_mode", "start_date", "integrated_input", "doc_path", "stacked_new", "mapping", "note"):
            if k in s and s[k] not in ("", None):
                print(f"     {k}={s[k]}")
        for k in ("removed_items", "removed_tickers", "removed_focus", "removed_modes"):
            if s.get(k):
                print(f"     {k}({len(s[k])}):{'、'.join(s[k])}(零刪除保全,--restore 可回)")


def selftest() -> int:
    import copy
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    d0 = load()
    # ① 冊完整:五分區+操作員三重點+堆圖新增
    chk("五分區在冊", set(d0["sections"]) == {"INTL_DAILY", "INTL_FIN", "TW_FIN", "VRN", "PLOT"})
    chk("VRN 三重點", d0["sections"]["VRN"]["input_focus"] == ["SUMMARY_MATRIX", "BASIC_INFO", "FINANCIAL_DATA"])
    chk("堆圖新增", d0["sections"]["PLOT"]["stacked_new"] is True
        and "stacked" in d0["sections"]["PLOT"]["modes"])
    # ② 種子承接既有清單(^GSPC/^HSI 等)
    chk("種子承接 Unified_Params", {"^GSPC", "^HSI", "^N225"} <= set(d0["sections"]["INTL_DAILY"]["tickers"]))
    with tempfile.TemporaryDirectory() as td:
        sp = Path(td) / "m.json"
        d = copy.deepcopy(d0)
        save(d, sp, "SANDBOX", "自測沙盒")
        d = load(sp)
        # ③ 增項目/增個股
        r1 = add_item(d, "INTL_DAILY", "turnover")
        r2 = add_ticker(d, "INTL_FIN", "AAPL")
        chk("增項目/個股", r1.startswith("OK") and r2.startswith("OK")
            and "turnover" in d["sections"]["INTL_DAILY"]["items"]
            and "AAPL" in d["sections"]["INTL_FIN"]["tickers"])
        # ④ 軟移除=零刪除(入 removed_*)
        r3 = rm_ticker(d, "INTL_DAILY", "^VIX")
        chk("軟移除零刪除", r3.startswith("OK")
            and "^VIX" not in d["sections"]["INTL_DAILY"]["tickers"]
            and "^VIX" in d["sections"]["INTL_DAILY"]["removed_tickers"])
        # ⑤ restore 找回
        r4 = restore(d, "INTL_DAILY", "^VIX")
        chk("restore 找回", r4.startswith("OK") and "^VIX" in d["sections"]["INTL_DAILY"]["tickers"])
        # ⑥ 重複增=SKIP 冪等
        chk("冪等 SKIP", add_item(d, "INTL_DAILY", "turnover").startswith("SKIP"))
        # ⑦ 台股 period 白名單閘
        chk("period 白名單", set_tw(d, "period", "單季").startswith("OK")
            and set_tw(d, "period", "亂值").startswith("FAIL"))
        # ⑧ start_date 格式閘
        chk("start_date 閘", set_tw(d, "start", "2020-01-01").startswith("OK")
            and set_tw(d, "start", "2020/1/1").startswith("FAIL"))
        # ⑨ VRN 路徑設定
        chk("VRN 路徑", set_vrn(d, "path", r"C:\reports").startswith("OK")
            and d["sections"]["VRN"]["doc_path"] == r"C:\reports")
        # ⑩ changelog append-only+落檔回讀
        n0 = len(d.get("changelog", []))
        save(d, sp, "EDIT", "自測批次")
        d2 = load(sp)
        chk("changelog+落檔", len(d2["changelog"]) == n0 + 1
            and "turnover" in d2["sections"]["INTL_DAILY"]["items"])
    # ⑪ 正本零觸碰(沙盒編輯不回寫正冊)
    chk("正本零觸碰", "turnover" not in load()["sections"]["INTL_DAILY"]["items"])
    n = 13 - len(fails)
    print(f"  [計] 十三檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VDF 輸入介面矩陣 v0100 · 十三檢(沙盒零網路)===")
        return selftest()
    if "--show" in a or not a:
        print("=== VDF 整合輸入介面清單矩陣(TOOL-093)===")
        show(load())
        return 0
    ops = {"--add-item": add_item, "--remove-item": rm_item,
           "--add-ticker": add_ticker, "--remove-ticker": rm_ticker,
           "--restore": restore}
    for flag, fn in ops.items():
        if flag in a:
            i = a.index(flag)
            try:
                sec_name, val = a[i + 1], a[i + 2]
            except IndexError:
                print(f"[用法] via-vdfin {flag} <分區> <值>")
                return 2
            d = load()
            msg = fn(d, sec_name, val)
            print(f"  [{flag[2:]}] {msg}")
            if msg.startswith("OK"):
                save(d, None, flag[2:].upper(), f"{sec_name}:{val}")
            return 0 if not msg.startswith("FAIL") else 1
    if "--set-tw" in a:
        i = a.index("--set-tw")
        d = load()
        msg = set_tw(d, a[i + 1], a[i + 2])
        print(f"  [set-tw] {msg}")
        if msg.startswith("OK"):
            save(d, None, "SET_TW", f"{a[i+1]}={a[i+2]}")
        return 0 if msg.startswith("OK") else 1
    if "--set-vrn" in a:
        i = a.index("--set-vrn")
        d = load()
        msg = set_vrn(d, a[i + 1], a[i + 2])
        print(f"  [set-vrn] {msg}")
        if msg.startswith("OK"):
            save(d, None, "SET_VRN", f"{a[i+1]}={a[i+2]}")
        return 0 if msg.startswith("OK") else 1
    print(__doc__.split("用法:")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
