#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0107 — 薄尾(v0106 … v0100 一字不動):系統卡片可以寫上「這個系統的一句話」。
為什麼:操作員 2026-11-19:「顯示系統狀況每個系統一個資訊,透過 SYSTEM MANAGER 彙總,全部再由 VCGC 看全部」。
② 的系統卡片原本只算「這個系統有幾列要處理」;別的系統的管理器自己彙總的那一句(燈 · 時間 · 版本)沒有地方放。
本版只加一件;項目冊沒帶這個鍵時,行為與 v0106 完全相同:
  項目冊 {"sys_info": {"VDF": {"lamp": "y", "note": "…"}, …}}:那個系統的卡片改用這盞燈,說明寫這一句(後面仍接「要處理幾項」);
  沒列到的系統照舊;卡片上的數字(要處理幾項)與對帳不動。燈與字都是送項目冊的一方照對方自報填的,本引擎不讀任何系統。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。動詞與旗標同 v0106。
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
import json
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0107"
VERSION = "v0107"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0106.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0106", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0106"] = PRIOR
_spec.loader.exec_module(PRIOR)
V5 = PRIOR.PRIOR            # v0105:收據的 version 由它的 write_out 寫
V3 = PRIOR.V3               # v0103:系統卡片在它的 STATE["sys"]
P0 = PRIOR.P0               # v0100 本體(run 用它的全域名呼叫 assemble)
PRIOR.ENGINE = V5.ENGINE = V5.PRIOR.ENGINE = V3.ENGINE = V3.PRIOR.ENGINE = V3.P1.ENGINE = P0.ENGINE = ENGINE
PRIOR.VERSION = V5.VERSION = VERSION
V3.MANIFEST["engine"] = ENGINE
_O = {"assemble": P0.assemble}   # 此刻指到 v0103 的包裝
CTX = {"sys_info": None}


def doc_sys_info(src: str):
    """讀項目冊自帶的 sys_info。格式不對的項一律略過;一項都沒有就回 None。"""
    try:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    info = doc.get("sys_info") if isinstance(doc, dict) else None
    if not isinstance(info, dict):
        return None
    out = {}
    for k, v in info.items():
        if isinstance(k, str) and k.strip() and isinstance(v, dict) and v.get("lamp") in ("r", "y", "g", "x") and isinstance(v.get("note"), str) and v["note"].strip():
            out[k.strip()] = {"lamp": v["lamp"], "note": v["note"].strip()[:140]}
    return out or None


def apply_sys_info(info):
    CTX["sys_info"] = info


def restore():
    CTX["sys_info"] = None


def assemble(raw, source, prev, budget=300, peer=None):
    res = _O["assemble"](raw, source, prev, budget, peer)
    info = CTX["sys_info"]
    if info:
        for c in V3.STATE["sys"]:
            i = info.get(c["key"])
            if i:
                c["lamp"] = i["lamp"]
                c["reason"] = i["note"] + ((" · 要處理:" + c["reason"]) if c["n"] else "")
    return res


P0.assemble = assemble


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0106(含前版鏈)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf107_st_"))
    try:
        raw = [{"section": "甲區", "system": "VCGC", "lamp": "y", "id": "a", "title": "a", "detail": "待看"},
               {"section": "同儕", "system": "VDF", "lamp": "y", "id": "b", "title": "b", "detail": "自報 YELLOW"},
               {"section": "同儕", "system": "VQG", "lamp": "g", "id": "c", "title": "c", "detail": "入口檔在"}]
        base = {"source": "自測冊", "title": "自測一覽", "groups": [["甲", ["甲區"]], ["同儕", ["同儕"]]], "systems": ["VCGC", "VDF", "VQG"], "items": raw}
        book = tmp / "book.json"
        book.write_text(json.dumps(dict(base, sys_info={"VDF": {"lamp": "g", "note": "管理器自報 綠 · 11-18 17:19"}, "VQG": {"lamp": "x", "note": "管理器還沒有彙總收據"},
                                                         "壞一": {"lamp": "紫", "note": "x"}, "壞二": "不是物件"}), ensure_ascii=False), encoding="utf-8")
        info = doc_sys_info(str(book))
        chk("讀得到項目冊自帶的 sys_info;格式不對的項略過", info == {"VDF": {"lamp": "g", "note": "管理器自報 綠 · 11-18 17:19"}, "VQG": {"lamp": "x", "note": "管理器還沒有彙總收據"}}, info)
        chk("不是 JSON / 檔不在 / 沒帶:回 None", doc_sys_info(str(tmp / "nope.json")) is None and doc_sys_info(str(Path(__file__))) is None)
        PRIOR.apply_extras(["VCGC", "VDF", "VQG"], None)
        apply_sys_info(info)
        try:
            r = P0.assemble(raw, "自測冊", None)
            by = {c["key"]: c for c in V3.STATE["sys"]}
            chk("有列的系統:卡片用管理器那盞燈,說明寫那一句再接「要處理幾項」;數字不動", by["VDF"]["lamp"] == "g" and by["VDF"]["n"] == 1 and by["VDF"]["reason"].startswith("管理器自報 綠 · 11-18 17:19 · 要處理:"), by["VDF"])
            chk("沒有要處理的系統:只寫那一句;沒列到的系統(VCGC)照舊", by["VQG"]["lamp"] == "x" and by["VQG"]["reason"] == "管理器還沒有彙總收據" and by["VCGC"]["lamp"] == "y" and "管理器" not in by["VCGC"]["reason"], (by["VQG"], by["VCGC"]))
            chk("對帳不受影響", r["checks"].get("系統卡合計 = 入選數") is True and r["checks"].get("群組卡合計 = 矩陣列數") is True, r["checks"])
            page = P0.render(r, P0.cards_of(r), list(r["head"]), "", "自測", "自測")
            chk("那一句寫進頁面的系統卡片", "管理器自報 綠 · 11-18 17:19" in page and "管理器還沒有彙總收據" in page)
        finally:
            restore()
            PRIOR.restore()
        r0 = P0.assemble(raw, "自測冊", None)
        chk("跑完還原;沒帶 sys_info:卡片與 v0106 相同", CTX["sys_info"] is None and all("管理器" not in c["reason"] for c in V3.STATE["sys"]))
        out = tmp / "out"
        rc = main(["run", "--in", str(book), "--out", str(out), "--no-open", "--no-clip"])
        html = (out / "WORKPLATFORM_latest.html").read_text(encoding="utf-8") if (out / "WORKPLATFORM_latest.html").exists() else ""
        chk("走 main 的 run --in:頁面寫出,帶標題、系統順序與那一句;rc 照內容(只有黃 = 2)", rc == 2 and "<h1>自測一覽:" in html and "管理器自報 綠 · 11-18 17:19" in html and 'data-key="VQG"' in html, rc)
        chk("main 跑完也還原", CTX["sys_info"] is None and V3.SYS_ORDER is PRIOR._BUILTIN["SYS_ORDER"])
        rec = json.loads((out / "STATUS_latest.json").read_text(encoding="utf-8")) if (out / "STATUS_latest.json").exists() else {}
        chk("收據的 version 與 engine 都是本版", rec.get("version") == VERSION and rec.get("engine") == ENGINE, (rec.get("version"), rec.get("engine")))
        chk("沒留下暫存檔", not list(out.glob("*.tmp")))
    finally:
        restore()
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    verb = args[0] if args and not args[0].startswith("-") else ("selftest" if "--selftest" in args else "run")
    if verb == "selftest":
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    src = args[args.index("--in") + 1] if "--in" in args and args.index("--in") + 1 < len(args) else ""
    if verb == "run" and src:
        apply_sys_info(doc_sys_info(src))
    try:
        return PRIOR.main(args)
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())
