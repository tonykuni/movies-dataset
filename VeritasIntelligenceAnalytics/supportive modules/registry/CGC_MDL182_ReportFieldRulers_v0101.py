#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL182_ReportFieldRulers v0101 — 薄尾:讀規則冊尾版(只增不減的職稱 / 電話)+ 樣本挖掘 mine(前版 v0100 本體照讀)

v0100→v0101(R36d 操作員 2026-10-01):「分析師中英文姓名通常放在職稱電話電郵上方 列一些可能的中英文職稱也可去樣本找
  電話regex可更新只增不減不衝突 電郵通常@前方為分析師英文名 後方為broker」。
  四條規則冊上(VIA_VRN_ReportFieldRules_SSOT 批713/714)本來都在:姓名在上方 = contacts_of 的錨點回溯窗(Email 往前 80 字元);
  @ 前英文名 = at_left 三式互證;@ 後網域 = domain_verdict(先過拒絕閘)。本版只做三件:
  ① 前版把冊路徑寫死在 v0100 → 改讀冊尾版(v0101 起:職稱 中 19→43 · 英 15→31;電話 +TW_MOBILE · +INTL 兩式)。
  ② 新兩式照冊 ⑧ 放在冊 contact_block.corrected_v0101,phone.use 只寫出處路徑(`from`)—— 前版 _pat 原樣取得到,不改。
  ③ mine --samples <夾>:逐份首頁、逐個 Email 開窗(上 3 行 · 下 2 行),列 冊外職稱樣行 · 所有電話式都不收的號碼 · 冊外網域
     (附檔名券商字首當旁證)· @ 左側種類 · 姓名在職稱 / 電話 / 電郵上方的比率 → VIA_Reports/vrn/field_rules/MINE_latest.json。
     **只列提案,不自動入冊**(裁定後出冊新版,只增不減)。
  「不衝突」的證據:v0100 自測全部探針在 v0101 冊下重跑仍全過;known_false_positive 三條探針的 HIT 逐條相同。
VIA_FROM_VCGC:mine 只收 VCGC 呼叫(via-vcgc run --family core CGC_MDL182_ReportFieldRulers mine …);--selftest 例外。零網路;不用 TA-Lib;正本唯讀。
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
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL182_ReportFieldRulers"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL182_ReportFieldRulers_v0100.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("rulers_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ENGINE = Path(__file__).stem
VERSION = "v0101"
RULES_V0100 = PRIOR.RULES
RULES = max(HERE.glob("VIA_VRN_ReportFieldRules_SSOT_v*.json"), key=_vnum, default=PRIOR.RULES)
PRIOR.RULES = RULES                                  # 前版 rules() 的預設路徑 → 冊尾版
OUT = HERE.parent.parent / "VIA_Reports" / "vrn" / "field_rules"
rules = PRIOR.rules
phones_of = PRIOR.phones_of
contacts_of = PRIOR.contacts_of
titles_in = PRIOR.titles_in
domain_verdict = PRIOR.domain_verdict

TITLE_CUE = re.compile(r"分析師|研究|經理|協理|襄理|處長|副總|主管|顧問|經濟學家|策略|Analyst|Research|Director|President|Economist|Strategist"
                       r"|Associate|Head|Chief|Officer|Manager|Specialist|Principal", re.I)
NUM_RUN = re.compile(r"[+(]?\d[\d\s\-().]{6,}\d")


def _broker_hint(stem: str) -> str:
    m = re.match(r"^\s*(?:【([^】]+)】|([A-Za-z]{2,8})\s*[-_ ]|([一-鿿]{2,6}(?:投顧|證券|投信|期貨))|(CTBC))", stem)
    if m:
        return next(g for g in m.groups() if g)
    m = re.search(r"(CTBC|KGI|凱基|華南|統一|群益|國泰|元大|富邦|永豐|兆豐)", stem)
    return m.group(1) if m else ""


def mine_text(text: str, stem: str = "", R: dict | None = None) -> dict:
    """一份首頁文字 → 提案(冊外職稱 / 不收的號碼 / 冊外網域)+ 姓名位置。"""
    R = R if R is not None else rules()
    lines = text.splitlines()
    B = (R.get("contact_block") or {}).get("as_given") or {}
    email_rx = re.compile(B.get("email") or r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
    phone_hits = phones_of(text, R)
    known_ph = [p["hit"] for p in phone_hits]
    out = {"emails": 0, "titles_unknown": [], "phones_unknown": [], "domains_unknown": [], "at_left": Counter(), "name_above": [0, 0]}
    cs = contacts_of(text, R)
    for c in cs:
        out["emails"] += 1
        out["at_left"][c["at_left_kind"]] += 1
        if c["broker_state"] == "UNKNOWN":
            out["domains_unknown"].append({"domain": c["email"].split("@")[-1].lower(), "hint_from_filename": _broker_hint(stem)})
        li = next((i for i, ln in enumerate(lines) if c["email"] in ln), None)
        if li is None:
            continue
        names = [n for n in (c["name_cn"] + c["name_en"]) if n]
        name_li = next((i for i in range(max(0, li - 4), li + 1) if any(n in lines[i] for n in names)), None)
        anchors = [i for i in range(max(0, li - 4), min(len(lines), li + 3))
                   if titles_in(lines[i], R) or any(p in lines[i] for p in known_ph) or c["email"] in lines[i]]
        if name_li is not None and anchors:
            out["name_above"][1] += 1
            out["name_above"][0] += int(name_li <= min(anchors))
        for i in range(max(0, li - 3), min(len(lines), li + 3)):
            ln = lines[i].strip()
            if not ln or c["email"] in ln:
                continue
            if TITLE_CUE.search(ln) and not titles_in(ln, R) and len(ln) <= 60:
                out["titles_unknown"].append(ln)
            for m in NUM_RUN.finditer(ln):
                s = m.group(0).strip()
                nd = sum(ch.isdigit() for ch in s)
                covered = any((s in k or k in s) and sum(ch.isdigit() for ch in k) >= nd - 1 for k in known_ph)
                if nd >= 8 and not covered \
                        and not re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", s):
                    out["phones_unknown"].append(s)
    out["titles_unknown"] = list(dict.fromkeys(out["titles_unknown"]))
    out["phones_unknown"] = list(dict.fromkeys(out["phones_unknown"]))
    return out


def mine(samples: list, R: dict | None = None) -> dict:
    R = R if R is not None else rules()
    files = []
    for d in samples:
        p = Path(d)
        files += sorted(p.rglob("*.pdf")) if p.is_dir() else ([p] if p.suffix.lower() == ".pdf" and p.exists() else [])
    agg = {"files": 0, "emails": 0, "titles_unknown": Counter(), "phones_unknown": Counter(), "domains_unknown": {},
           "at_left": Counter(), "name_above": [0, 0], "errors": []}
    try:
        import fitz
    except Exception as exc:
        agg["errors"].append(f"PyMuPDF 不在:{type(exc).__name__}")
        return agg
    for f in files:
        try:
            with fitz.open(str(f)) as doc:
                text = doc[0].get_text("text") if doc.page_count else ""
        except Exception as exc:
            agg["errors"].append(f"{f.name}:{type(exc).__name__}")
            continue
        r = mine_text(text, f.stem, R)
        agg["files"] += 1
        agg["emails"] += r["emails"]
        agg["titles_unknown"].update(r["titles_unknown"])
        agg["phones_unknown"].update(r["phones_unknown"])
        agg["at_left"].update(r["at_left"])
        agg["name_above"][0] += r["name_above"][0]
        agg["name_above"][1] += r["name_above"][1]
        for d in r["domains_unknown"]:
            e = agg["domains_unknown"].setdefault(d["domain"], {"n": 0, "hints": Counter()})
            e["n"] += 1
            if d["hint_from_filename"]:
                e["hints"][d["hint_from_filename"]] += 1
    return agg


def _payload(agg: dict, src: str) -> dict:
    return {"engine": ENGINE, "rules": RULES.name, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "source": src,
            "files": agg["files"], "emails": agg["emails"], "at_left": dict(agg["at_left"]),
            "name_above": {"above": agg["name_above"][0], "measured": agg["name_above"][1]},
            "proposals": {"titles": agg["titles_unknown"].most_common(60), "phones": agg["phones_unknown"].most_common(60),
                          "domains": {k: {"n": v["n"], "hints": dict(v["hints"])} for k, v in
                                      sorted(agg["domains_unknown"].items(), key=lambda kv: -kv[1]["n"])}},
            "rule": "只列提案,不自動入冊;裁定後出 VIA_VRN_ReportFieldRules_SSOT 新版(只增不減)", "errors": agg["errors"][:20]}


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    if a[:1] == ["mine"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
            return 2
        samples = [a[i + 1] for i, x in enumerate(a) if x == "--samples" and i + 1 < len(a)]
        if not samples:
            print("[欄位尺 · mine] 要 --samples <夾>")
            return 2
        agg = mine(samples)
        pl = _payload(agg, " · ".join(samples))
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "MINE_latest.json").write_text(json.dumps(pl, ensure_ascii=False, indent=1), encoding="utf-8")
        na = pl["name_above"]
        print(f"[欄位尺 · mine] {pl['files']} 份 · Email {pl['emails']} · @左 {pl['at_left']} · 姓名在上方 {na['above']}/{na['measured']} · "
              f"冊外職稱 {len(pl['proposals']['titles'])} · 不收的號碼 {len(pl['proposals']['phones'])} · 冊外網域 {len(pl['proposals']['domains'])}")
        for t, n in pl["proposals"]["titles"][:15]:
            print(f"  職稱? {n:>3} × {t}")
        for t, n in pl["proposals"]["phones"][:10]:
            print(f"  電話? {n:>3} × {t}")
        for dmn, v in list(pl["proposals"]["domains"].items())[:15]:
            print(f"  網域? {v['n']:>3} × {dmn}  檔名券商 {v['hints']}")
        print(f"  [寫出] {OUT / 'MINE_latest.json'}(提案;裁定後才入冊)")
        return 0 if not agg["errors"] else 3
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    R0 = PRIOR.rules(RULES_V0100)
    R1 = rules()
    chk("讀冊尾版(v0101 起)· 前版 rules() 預設也指向尾版", RULES.name >= "VIA_VRN_ReportFieldRules_SSOT_v0101.json" and PRIOR.RULES == RULES, RULES.name)
    t0, t1 = R0["analyst_titles"], R1["analyst_titles"]
    chk("職稱只增不減:中 / 英都是 v0100 的超集,且長的排前面", set(t0["zh"]) <= set(t1["zh"]) and set(t0["en"]) <= set(t1["en"])
        and len(t1["zh"]) > len(t0["zh"]) and [len(w) for w in t1["zh"]] == sorted((len(w) for w in t1["zh"]), reverse=True),
        (len(t0["zh"]), len(t1["zh"]), len(t0["en"]), len(t1["en"])))
    ids0 = [s["id"] for s in R0["phone"]["use"]]
    ids1 = [s["id"] for s in R1["phone"]["use"]]
    chk("電話式只增不減:v0100 三式原樣在前,新兩式排最後 · 只寫出處路徑(冊 ⑧)", ids1[:len(ids0)] == ids0 and ids1[len(ids0):] == ["TW_MOBILE", "INTL"]
        and R1["phone"]["use"][:len(ids0)] == R0["phone"]["use"] and all("from" in u and "rx" not in u for u in R1["phone"]["use"]), ids1)
    dm0 = R0["broker_domains_addendum"]["map"]
    dm1 = R1["broker_domains_addendum"]["map"]
    chk("網域冊與拒絕閘不減", all(dm1.get(k) == v for k, v in dm0.items())
        and R1["broker_domains_addendum"]["deny_domains"]["map"] == R0["broker_domains_addendum"]["deny_domains"]["map"])

    def hits(text, R):
        return [(p["id"], p["hit"]) for p in phones_of(text, R) if p["state"] == "HIT"]
    probes = [x["probe"] for x in R0["phone"].get("known_false_positive") or []] + [
        "Tel: (02) 2181-8888 ext. 123", "電話:+886-2-8758-1234", "Tel +852 2123 4567", "(03) 578-1234", "報告日 20251202"]
    diff = [p for p in probes if hits(p, R0) != hits(p, R1)]
    chk("不衝突:v0100 已知探針(含 known_false_positive 三條)在 v0101 冊下 HIT 逐條相同", not diff, [(p, hits(p, R0), hits(p, R1)) for p in diff])
    chk("新式:Tel: 0912-345-678 → TW_MOBILE · +886-912-345-678 → TW_MOBILE(台北式咬不到 4-3-3)",
        hits("Tel: 0912-345-678", R1) == [("TW_MOBILE", "0912-345-678")] and hits("Mobile +886-912-345-678", R1) == [("TW_MOBILE", "+886-912-345-678")],
        (hits("Tel: 0912-345-678", R1), hits("Mobile +886-912-345-678", R1)))
    chk("新式:+65 6123 4567 / +81 3 1234 5678 → INTL;+852 / +886 照舊歸香港 / 台北(國際式不搶)",
        hits("Tel +65 6123 4567", R1) == [("INTL", "+65 6123 4567")] and hits("+81 3 1234 5678", R1) == [("INTL", "+81 3 1234 5678")]
        and [i for i, _ in hits("Tel +852 2123 4567", R1)] == ["HK"] and [i for i, _ in hits("電話:+886-2-8758-1234", R1)] == ["TPE"],
        (hits("Tel +65 6123 4567", R1), hits("Tel +852 2123 4567", R1)))
    chk("守衛照舊:裸號 0912345678(無電話字樣、無 +/(/-)= WEAK 不當命中",
        [p["state"] for p in phones_of("0912345678", R1) if p["id"] == "TW_MOBILE"] == ["WEAK"])
    chk("新職稱:資深協理 · Chief Economist · Senior Research Analyst 認得出", "資深協理" in titles_in("資深協理 王大明", R1)
        and "Chief Economist" in titles_in("Chief Economist", R1) and "Senior Research Analyst" in titles_in("Senior Research Analyst", R1))
    blk = ("Jeff Pu\nSenior Research Analyst\nTel: +65 6123 4567\njeff.pu@gs.com\n"
           "林大衛\n資深協理\n電話:(02) 2181-8888 #123\ndavid.lin@abcsec.com.tw\n"
           "Mary Chen\nDesk Head\n(886)2-2181-8888\nmary.chen@kgi.com\n")
    cs = contacts_of(blk, R1)
    chk("@ 前英文名互證 · @ 後券商:jeff.pu@gs.com → GREEN · GOLDMAN SACHS · 電話 INTL 收進窗",
        cs[0]["state"] == "GREEN" and cs[0]["broker"] == "GOLDMAN SACHS" and cs[0]["phone"] == ["+65 6123 4567"], cs[0])
    r = mine_text(blk, "GS-2330 20251203", R1)
    chk("mine:冊外職稱 Desk Head · 不收的號碼 (886)2-2181-8888 · 冊外網域 abcsec.com.tw 都列成提案",
        r["titles_unknown"] == ["Desk Head"] and "(886)2-2181-8888" in r["phones_unknown"]
        and [d["domain"] for d in r["domains_unknown"]] == ["abcsec.com.tw"], r)
    chk("mine:姓名在職稱 / 電話 / 電郵上方(3 人皆是)", r["name_above"] == [3, 3], r["name_above"])
    chk("mine:檔名券商字首當旁證(GS- → GS · 【國泰證期研究部】→ 國泰證期研究部 · 凱基投顧_ → 凱基投顧)",
        _broker_hint("GS-2330 20251203") == "GS" and _broker_hint("【國泰證期研究部】神達(3706 TT)") == "國泰證期研究部"
        and _broker_hint("凱基投顧_2637 慧洋-KY") == "凱基投顧", (_broker_hint("凱基投顧_2637 慧洋-KY"),))
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 閘 · 不匯入 TA-Lib · 不碰網路", "[VIA:ACCEL-BRIDGE" in body and 'os.environ.get("VIA_FROM_VCGC") != "YES"' in body
        and not re.search(r"^\s*(import|from)\s+(" + "ta" + r"lib|requests|urllib)\b", body, re.M))
    print("--- 前版 v0100 全套自測(在 v0101 冊下重跑 = 不衝突的證據)---")
    prc = PRIOR.selftest()
    chk("前版自測在 v0101 冊下仍全過", prc == 0)
    print(f"[CGC_MDL182 v0101 職稱 · 電話只增不減 · mine] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
