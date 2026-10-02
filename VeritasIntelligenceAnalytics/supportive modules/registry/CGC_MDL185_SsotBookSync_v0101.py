#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL185_SsotBookSync v0101 — 薄尾:E4 台股代號 regex 冊改成「範疇感知」(只比同範疇的冊 + 逐冊對範疇預期)

操作員 2026-10-02:「你決定自動完成」(三項待裁之三:VRN 四冊代號 regex 收斂)。
裁定:**保留各冊範疇,不合併成一本**。v0100 的 E4 把四本冊放在一起比,0050 / 00878 / 00981A 永遠分歧(DISAGREE 黃),
但那是三個不同的操作員裁定(四碼 LOCKED 圈 · 全商品含 ETF · 內文只抽個股),不是錯。
本版:
  · 範疇正本 VIA_TickerRegex_Scope_SSOT_v*.json(尾版):宣告每本冊屬哪個範疇、每個範疇對每個探針該收 / 該拒。
    本支只讀它;冊的式仍在各冊,本支不改任何冊。
  · E4 判法(fullmatch,與 v0100 同一把尺):
      每本冊對自己範疇的預期逐探針比 → 偏離 = SCOPE_DRIFT(黃,列出冊 · 探針 · 預期 / 實際)
      讀得到但範疇冊沒宣告的冊 → UNSCOPED(黃,新冊先登範疇)
      同範疇冊之間判法不同 → 一定也偏離預期,歸 SCOPE_DRIFT(不另開一態)
      全部符合 → AGREE(綠);範疇冊讀不到 → 退回 v0100 原判(不假綠)
  · E1–E3 照 v0100(委派前版,不重寫)。
用法:經 VCGC(VIA_FROM_VCGC=YES;ssot 門 ⑥ 讀本支 check())· python CGC_MDL185_SsotBookSync_v0101.py check [--json] | --selftest
律:唯讀 · 零網路 · 不設同意閘 · stdlib。
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

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL185_SsotBookSync"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})\.(py|json)$", Path(p).name)
    return int(m.group(1)) if m else -1


_ME = _vnum(__file__)
_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _ME), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"_mdl185_prior_{_vnum(_PRIOR_PATH):04d}", _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_ID = _STEM
VERSION = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
NEW_YELLOW = {"SCOPE_DRIFT", "UNSCOPED"}
PRIOR.YELLOW_STATES.update(NEW_YELLOW)          # 前版 lamp / check 讀同一個集合:新態落黃燈,不另寫一份 lamp
_E4_V0100 = PRIOR.e4_ticker


def __getattr__(name):
    return getattr(PRIOR, name)


def scope_book(folder: Path = None):
    hits = sorted((folder or PRIOR.REG).glob("VIA_TickerRegex_Scope_SSOT_v[0-9][0-9][0-9][0-9].json"), key=_vnum)
    return (PRIOR._json(hits[-1]), hits[-1].name) if hits else (None, None)


def _book_id(name: str) -> str:
    """ticker_books() 的冊名 → 範疇冊的鍵(TickerRegexSSOT 帶版號 → 去版號)。"""
    return re.sub(r"_v\d{4}$", "", name)


def compare_scoped(books: list, scope: dict) -> dict:
    probes = tuple(scope.get("probes") or PRIOR.TICKER_PROBES)
    decl, scopes = scope.get("books") or {}, scope.get("scopes") or {}
    rows, unscoped, by_scope = [], [], {}
    for name, key, rx in books:
        d = decl.get(_book_id(name))
        if not d or d.get("scope") not in scopes:
            unscoped.append(name)
            continue
        by_scope.setdefault(d["scope"], []).append(name)
        expect = scopes[d["scope"]].get("expect") or {}
        try:
            cre = re.compile(rx)
        except re.error as exc:
            rows.append({"book": name, "scope": d["scope"], "probe": "__error__", "expect": None, "got": str(exc)})
            continue
        for p in probes:
            if p in expect and bool(cre.fullmatch(p)) != bool(expect[p]):
                rows.append({"book": name, "scope": d["scope"], "probe": p, "expect": bool(expect[p]), "got": bool(cre.fullmatch(p))})
    return {"rows": rows, "unscoped": unscoped, "by_scope": by_scope, "probes": probes}


def e4_ticker() -> dict:
    scope, sname = scope_book()
    if not scope:
        return _E4_V0100()                            # 範疇冊讀不到 = 照 v0100 原判(不假綠)
    books = PRIOR.ticker_books()
    if not books:
        return PRIOR.edge("ticker", "E4 台股代號 regex 冊一致(範疇感知)", "ABSENT", "讀得到的冊 0 本")
    cmp = compare_scoped(books, scope)
    groups = " · ".join(f"{s}:{'、'.join(n)}" for s, n in sorted(cmp["by_scope"].items()))
    if cmp["rows"]:
        ex = " ; ".join(f"{r['book']}[{r['scope']}] {r['probe']} 該{'收' if r['expect'] else '拒'}實{'收' if r['got'] else '拒'}"
                        for r in cmp["rows"][:6])
        return PRIOR.edge("ticker", "E4 台股代號 regex 冊一致(範疇感知)", "SCOPE_DRIFT",
                          f"{len(cmp['rows'])} 處偏離自己範疇的預期 · {ex} · 範疇冊 {sname}",
                          "冊的式偏離範疇 = 改那本冊的新版(式的正本在冊);範疇本身要變 = 出範疇冊新版(操作員裁)", cmp["rows"])
    if cmp["unscoped"]:
        return PRIOR.edge("ticker", "E4 台股代號 regex 冊一致(範疇感知)", "UNSCOPED",
                          f"未宣告範疇的冊 {cmp['unscoped']} · 範疇冊 {sname}", "在範疇冊新版登記這本冊屬哪個範疇",
                          [{"book": n, "state": "UNSCOPED"} for n in cmp["unscoped"]])
    return PRIOR.edge("ticker", "E4 台股代號 regex 冊一致(範疇感知)", "AGREE",
                      f"{len(books)} 本冊各合自己範疇對 {len(cmp['probes'])} 個探針的預期 · 同範疇判法相同 · {groups} · 範疇冊 {sname}")


PRIOR.e4_ticker = e4_ticker                     # 前版 check() 讀模組全域 e4_ticker:換成本版,E1–E3 不動


def check() -> dict:
    res = PRIOR.check()
    res["version"] = VERSION
    return res


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "check")
    if verb != "check":
        print("  [用法] check [--json] | --selftest")
        return 2
    res = check()
    if "--json" in a:
        print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
    else:
        PRIOR.render(res)
    return res["rc"]


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_ID} {VERSION} · 薄尾自測(E4 範疇感知;夾具 + 真樹唯讀)===")
    P = ("2330", "0050", "00981A")
    sc = {"probes": list(P),
          "scopes": {"S4": {"expect": {"2330": True, "0050": True, "00981A": False}},
                     "ALL": {"expect": {"2330": True, "0050": True, "00981A": True}},
                     "TXT": {"expect": {"2330": True, "0050": False, "00981A": False}}},
          "books": {"A": {"scope": "S4"}, "B": {"scope": "ALL"}, "C": {"scope": "TXT"}, "D": {"scope": "TXT"}}}
    good = [("A", "k", r"^\d{4}$"), ("B", "k", r"^(?:\d{4}|00\d{3}[A-Z])$"), ("C_v0100", "k", r"(?<!\d)([1-9]\d{3})(?!\d)"),
            ("D", "k", r"\b[1-9]\d{3}\b")]
    r = compare_scoped(good, sc)
    chk("① 四本冊跨範疇判法不同,但各合自己範疇 → 無偏離(v0100 會判 DISAGREE)", not r["rows"] and not r["unscoped"], r["rows"][:2])
    chk("② 帶版號的冊名去版號後對到範疇鍵(C_v0100 → C)", r["by_scope"].get("TXT") == ["C_v0100", "D"], r["by_scope"])
    r = compare_scoped([("C", "k", r"^\d{4}$")], sc)
    chk("③ 內文抽個股的冊收了 0050 → 偏離(列冊 · 探針 · 預期 / 實際)",
        r["rows"] == [{"book": "C", "scope": "TXT", "probe": "0050", "expect": False, "got": True}], r["rows"])
    r = compare_scoped([("E", "k", r"^\d{4}$")], sc)
    chk("④ 範疇冊沒宣告的冊 → UNSCOPED", r["unscoped"] == ["E"] and not r["rows"])
    r = compare_scoped([("A", "k", "(")], sc)
    chk("⑤ 壞式記成偏離列(不當成全拒)", r["rows"] and r["rows"][0]["probe"] == "__error__")
    chk("⑥ 新態落黃燈(前版 lamp 同一集合)", PRIOR.lamp("SCOPE_DRIFT") == "YELLOW" and PRIOR.lamp("UNSCOPED") == "YELLOW"
        and PRIOR.lamp("AGREE") == "GREEN")
    scope, sname = scope_book()
    chk("⑦ 真樹:範疇冊讀得到 · 三個範疇 · 四本冊都宣告", bool(scope) and len(scope.get("scopes", {})) == 3
        and len(scope.get("books", {})) == 4, sname)
    live = check()
    e4 = next((e for e in live["edges"] if e["id"] == "ticker"), {})
    chk("⑧ 真樹:E4 = AGREE(四本冊各合範疇)· 燈綠 · 版本 = 本版", e4.get("state") == "AGREE" and e4.get("lamp") == "GREEN"
        and live["version"] == VERSION, (e4.get("state"), e4.get("detail", "")[:160]))
    chk("⑨ 前版 check 走本版 E4(門 ⑥ 讀哪支都一樣)", PRIOR.e4_ticker is e4_ticker)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋在 · 不代設同意閘 · 零網路 · 經 VCGC(VIA_FROM_VCGC)", "VIA:ACCEL-BRIDGE" in src and "VIA_FROM_VCGC" in src
        and not re.findall(r"environ\[\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT", src)
        and not re.search(r"^\s*(import|from) (urllib|requests|socket)", src, re.M))
    mine = all(ok)
    print(f"  [計] {ENGINE_ID} {VERSION} 薄尾 {sum(ok)}/{len(ok)} · {'PASS' if mine else 'FAIL'}")
    prior = PRIOR.selftest()
    print(f"  [計] {ENGINE_ID} {VERSION} 合計 {'PASS' if mine and prior == 0 else 'FAIL'}")
    return 0 if mine and prior == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
