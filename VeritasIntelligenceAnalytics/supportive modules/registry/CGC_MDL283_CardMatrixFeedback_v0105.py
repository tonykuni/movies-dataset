#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0105 — 薄尾(v0104 · v0103 · v0102 · v0101 · v0100 一字不動):外來的項目冊可以自帶「群組」與「標題」。
為什麼:用 --in 吃外部項目冊時,③「全部列:依群組」的卡片只認現況矩陣自己的區塊名,外來的區塊全掉進「其他」一張卡,
看不出各類的整體狀況;頁首也固定寫「現況」。操作員 2026-11-19:「先用卡片做整體大致上狀態顯示,再用矩陣細節展現」。
本版只加兩件;項目冊沒帶這兩個鍵時,行為與 v0104 完全相同:
  ① 項目冊 {"groups": [["群組名", ["區塊名", …]], …]}:這一輪的群組卡片照它分(沒列到的區塊仍歸「其他」);跑完還原成內建分法。
  ② 項目冊 {"title": "…"}:頁首小標與大標的「現況」換成這個標題(其餘版面、樣式、篩選、對帳都不動)。
另:收據 STATUS_latest.json 的 version 寫本版。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。動詞與旗標同 v0104。
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
import os
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0105"
VERSION = "v0105"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0104.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0104", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0104"] = PRIOR
_spec.loader.exec_module(PRIOR)
V3 = PRIOR.PRIOR            # v0103:群組表 GROUPS / SEC_GROUP 在它的全域
P0 = PRIOR.P0               # v0100 本體(run 用它的全域名呼叫 render / write_out)
PRIOR.ENGINE = V3.ENGINE = V3.PRIOR.ENGINE = V3.P1.ENGINE = P0.ENGINE = ENGINE
V3.MANIFEST["engine"] = ENGINE
_O = {"render": P0.render, "write_out": P0.write_out}     # 此刻指到 v0104 為止的包裝
_BUILTIN = {"GROUPS": V3.GROUPS, "SEC_GROUP": V3.SEC_GROUP}
CTX = {"title": ""}
CAPS_OLD, H1_OLD = "VIA · 對內工作平台 · 現況", "<h1>現況:"


def doc_extras(src: str):
    """讀項目冊自帶的 (groups, title)。格式不對的一律當沒帶(回 None / ''),不猜。"""
    try:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, ""
    if not isinstance(doc, dict):
        return None, ""
    groups = []
    for g in doc.get("groups") or []:
        if isinstance(g, (list, tuple)) and len(g) == 2 and isinstance(g[0], str) and g[0].strip() and isinstance(g[1], (list, tuple)) and all(isinstance(s, str) for s in g[1]):
            groups.append((g[0].strip(), tuple(g[1])))
    title = doc.get("title")
    return (groups or None), (title.strip()[:60] if isinstance(title, str) else "")


def apply_extras(groups, title):
    if groups:
        V3.GROUPS = list(groups)
        V3.SEC_GROUP = {s: g for g, ss in groups for s in ss}
    CTX["title"] = title or ""


def restore():
    V3.GROUPS, V3.SEC_GROUP = _BUILTIN["GROUPS"], _BUILTIN["SEC_GROUP"]
    CTX["title"] = ""


def render(res, cards, pack, css, tpl_note, accel) -> str:
    html = _O["render"](res, cards, pack, css, tpl_note, accel)
    t = CTX["title"]
    if t:
        t = P0.E(t)
        html = html.replace(CAPS_OLD, "VIA · " + t, 1).replace(H1_OLD, "<h1>" + t + ":", 1)
    return html


def write_out(out: Path, res, pack, page, slug):
    final = _O["write_out"](out, res, pack, page, slug)
    p = Path(out) / "STATUS_latest.json"
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return final
    if rec.get("version") != VERSION:
        rec["version"] = VERSION
        tmp = p.with_name(p.name + ".%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(str(tmp), str(p))
    return final


P0.render, P0.write_out = render, write_out


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0104(含前版鏈)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf105_st_"))
    try:
        raw = [{"section": "甲區", "system": "VCGC", "lamp": "y", "id": "a", "title": "a", "detail": "待看"},
               {"section": "乙區", "system": "VCGC", "lamp": "g", "id": "b", "title": "b", "detail": "好"},
               {"section": "丙區", "system": "VCGC", "lamp": "r", "id": "c", "title": "c", "detail": "仍紅"}]
        book = tmp / "book.json"
        book.write_text(json.dumps({"source": "自測冊", "title": "自測一覽", "groups": [["第一組", ["甲區", "乙區"]], ["第二組", ["丙區"]]], "items": raw}, ensure_ascii=False), encoding="utf-8")
        g, t = doc_extras(str(book))
        chk("讀得到項目冊自帶的群組與標題", g == [("第一組", ("甲區", "乙區")), ("第二組", ("丙區",))] and t == "自測一覽", (g, t))
        bad = tmp / "bad.json"
        bad.write_text(json.dumps({"groups": [["x"], "y", ["", ["a"]], ["z", "不是清單"]], "title": 7, "items": raw}, ensure_ascii=False), encoding="utf-8")
        chk("群組或標題格式不對:當沒帶", doc_extras(str(bad)) == (None, ""), doc_extras(str(bad)))
        chk("不是 JSON / 檔不在:當沒帶", doc_extras(str(tmp / "nope.json")) == (None, ""))
        apply_extras(g, t)
        try:
            r = P0.assemble(raw, "自測冊", None)
            grp = {c["key"]: c["n"] for c in V3.STATE["grp"]}
            chk("群組卡片照項目冊分:第一組 2 · 第二組 1 · 沒有掉進「其他」", grp.get("第一組") == 2 and grp.get("第二組") == 1 and not grp.get("其他"), grp)
            page = P0.render(r, P0.cards_of(r), list(r["head"]), "", "自測", "自測")
            chk("頁首與大標換成項目冊的標題", "VIA · 自測一覽" in page and "<h1>自測一覽:" in page and CAPS_OLD not in page and H1_OLD not in page)
            chk("群組卡片寫進頁面", "第一組" in page and "第二組" in page)
        finally:
            restore()
        chk("跑完還原內建分法與標題", V3.GROUPS is _BUILTIN["GROUPS"] and V3.SEC_GROUP is _BUILTIN["SEC_GROUP"] and CTX["title"] == "")
        r0 = P0.assemble(raw, "自測冊", None)
        grp0 = {c["key"]: c["n"] for c in V3.STATE["grp"]}
        page0 = P0.render(r0, P0.cards_of(r0), list(r0["head"]), "", "自測", "自測")
        chk("沒帶群組:外來區塊照舊歸「其他」,頁首照舊(與 v0104 相同)", grp0.get("其他") == 3 and CAPS_OLD in page0 and H1_OLD in page0, grp0)
        out = tmp / "out"
        rc = main(["run", "--in", str(book), "--out", str(out), "--no-open", "--no-clip"])
        html = (out / "WORKPLATFORM_latest.html").read_text(encoding="utf-8") if (out / "WORKPLATFORM_latest.html").exists() else ""
        chk("走 main 的 run --in:頁面寫出,帶標題與群組;rc 照內容(有紅 = 1)", rc == 1 and "<h1>自測一覽:" in html and "第二組" in html, rc)
        chk("main 跑完也還原", V3.GROUPS is _BUILTIN["GROUPS"] and CTX["title"] == "")
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
        apply_extras(*doc_extras(src))
    try:
        return PRIOR.main(args)
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())
