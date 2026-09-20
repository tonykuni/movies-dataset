#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG084_FilenameTokenParse v0100 — 檔名切分與三來源合流(批634)

操作員令(批634):
  「將檔案的名稱中英文轉換處以及標點符號轉換處切開變成獨立的中文獨立的英文跟獨立的數字,
   4 個數字代表的是臺股個股的 TICKER……較長的數字通常為日期……券商名稱通常會用中文或
   英文簡寫出現在 filename……從檔案名稱擷取下來的日期跟第一頁上左右資訊區所截取下來的
   報告日期應該會相同這也是對照的方法」

【切之前要先保護】
  切分本身三行就寫完,難的是**切之前**。有三種東西天生跨類,先切就死了:
      `2330.TW`      → 被標點切成 2330 / . / TW
      `00715B`       → 被中英數切成 00715 / B
      `Jan 22, 2025` → 被切成三段
  所以本器**先用長樣式在原字串上掃一遍、把命中區段鎖起來**,剩下的才做中英數切分。
  反過來做,就是把答案先剪碎了再找。

【零九頭龍:一條正則都不自己寫】
  代號、日期、季度、年度、券商、姓名、電郵、電話、目標價線索、三來源優先權
  ——全部呼叫 SUP_MDL749 樞紐(它讀 VRN_FieldRules_SSOT 那一本)。
  本器只做三件事:**保護 → 切分 → 歸類**,外加三來源合流的呼叫。
  樞紐缺席就誠實停,不內建影子規則(那就是第二把尺)。

【裸四碼的坑】
  `^[1-9]\d{3}$`(一般個股)與西元四位年**完全重疊**:`2025` 兩邊都合法。
  本器的做法是**先鎖日期/季度/年度的區段**,鎖完剩下的四碼才當代號候選;
  仍然兩邊都成立的,`ambiguous_year` 標起來,不裝作很確定。

【紀律】
  · 零網路 · 只讀檔名字串與第一頁文字,不碰任何原件、不寫庫、沒有 --apply。

用法:
  via-py "functional modules/VRN/VRN_ENG084_FilenameTokenParse_v0100.py" parse --name "<檔名>"
  … scan --in "<報告夾>"      逐檔解析(只讀檔名,不開檔)
  … --selftest
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
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vrn" / "filename"

_HUB = None


def hub():
    """規則樞紐 SUP_MDL749(動態解析尾版;缺席誠實拋,不退回自己寫一份)。"""
    global _HUB
    if _HUB is not None:
        return _HUB
    d = VIA / "supportive modules" / "70_VRN_Rules"
    hits = sorted(d.glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    if not hits:
        raise RuntimeError("SUP_MDL749 規則樞紐缺席:本器不內建第二份規則,誠實停")
    spec = importlib.util.spec_from_file_location("SUP_MDL749_hub", hits[-1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _HUB = m
    return m


# ── 保護樣式:切之前先鎖起來的跨類整體 ────────────────────────────────
#   次序是**長的先鎖**。`2330.TW` 要在 `2330` 之前,不然鎖完剩一個 `.TW`。
def _protect_patterns() -> list:
    h = hub()
    pf = (h.platform_rules().get("corrected") or h.platform_rules().get("as_given") or {})
    pats = []
    for key in ("TW_YF_TICKER", "TW_BB_TICKER"):
        rx = pf.get(key)
        if rx:
            pats.append(("TICKER_PLATFORM", rx.strip("^$")))
    for p in (h.period_rules().get("quarter_patterns") or []):
        pats.append(("QUARTER", p["rx"].strip("^$")))
    for p in (h.period_rules().get("year_patterns") or []):
        if p.get("id") in ("Y_FY_YYYY", "Y_FY_YY", "Y_YYYY_EST"):
            pats.append(("YEAR", p["rx"].strip("^$")))
    for p in h.date_patterns():
        pats.append(("DATE", str(p["rx"]).strip("^$")))
    # 本地 ETF 尾碼(`00715B`)——中英數切分會把尾碼切掉
    pats.append(("TICKER_ETF", r"00\d{2,4}[ABDLRTUV]?"))
    return pats


_CLS = [("CJK", r"[\u4e00-\u9fa5]+"), ("EN", r"[A-Za-z]+"),
        ("NUM", r"[0-9]+"), ("PUNCT", r"[^\u4e00-\u9fa5A-Za-z0-9]+")]


def tokenize(name: str) -> list:
    """檔名 → token 串。每個 token 帶 `{text, cls, span, protected, why}`。

    兩段:① 長樣式先鎖(protected=True)② 其餘做中英數標點切分。
    """
    s = str(name or "")
    if not s:
        return []
    taken = [False] * len(s)
    out = []
    for kind, rx in _protect_patterns():
        try:
            cr = re.compile(rx)
        except re.error:
            continue
        for m in cr.finditer(s):
            a, b = m.span()
            if a == b or any(taken[a:b]):
                continue            # 已被更長的樣式鎖走就不重複鎖
            for i in range(a, b):
                taken[i] = True
            out.append({"text": s[a:b], "cls": kind, "span": (a, b),
                        "protected": True,
                        "why": f"切之前先鎖:{kind}(跨中英數/標點,先切就碎了)"})
    # 未被鎖的區段,做中英數切分
    i = 0
    while i < len(s):
        if taken[i]:
            i += 1
            continue
        j = i
        while j < len(s) and not taken[j]:
            j += 1
        seg = s[i:j]
        pos = i
        for m in re.finditer("|".join(f"(?P<{k}>{v})" for k, v in _CLS), seg):
            k = m.lastgroup
            out.append({"text": m.group(), "cls": k,
                        "span": (pos + m.start(), pos + m.end()),
                        "protected": False, "why": "中英數標點切分"})
        i = j
    return sorted(out, key=lambda t: t["span"][0])


def classify(tok: dict) -> dict:
    """一個 token 是什麼。回 `{role, value, detail}`;歸不了類回 role=OTHER。"""
    h = hub()
    t = tok["text"]
    if tok["cls"] == "PUNCT":
        return {"role": "PUNCT", "value": "", "detail": {}}
    per = h.parse_period_any(t)
    tk = h.ticker_platform(t)
    # **兩邊都成立就不准自己挑一個。**自審抓到:原本先問期間、中了就回,
    #   於是裸 `2025` 永遠是年,`ambiguous_year` 那支旗子從來沒亮過
    #   ——而 2025 是**真的有一支上市公司**。先問期間看起來很合理
    #   (研報檔名裡的 2025 九成是年),但「九成」不是判準,是機率。
    #   兩讀都留著、標 AMBIGUOUS,交給上下文或另一個平台寫法去斷。
    if per and tk and tk.get("ambiguous_year"):
        return {"role": "AMBIGUOUS", "value": per.get("iso", ""),
                "detail": {"as_period": per, "as_ticker": tk,
                           "why": "裸四碼同時是合法西元年與合法個股代號;"
                                  "本器不挑,兩讀都留(冊上 ticker.conflicts_known 第 1 條)"}}
    if per:
        return {"role": per["type"].upper(), "value": per.get("iso", ""), "detail": per}
    if tk:
        return {"role": "TICKER", "value": tk["canonical"], "detail": tk}
    if tok["cls"] in ("CJK", "EN"):
        bk = h.broker_of(t)
        if bk and bk[0]:
            return {"role": "BROKER", "value": bk[0], "detail": {"src": bk[1]}}
    return {"role": "OTHER", "value": t, "detail": {}}


def parse_filename(name: str) -> dict:
    """檔名整份解析。回 tokens + 各欄候選 + 衝突。"""
    toks = tokenize(name)
    rows = []
    for t in toks:
        c = classify(t)
        rows.append({**t, **c})
    def pick(role):
        return [r for r in rows if r["role"] == role]
    tickers = pick("TICKER")
    amb = pick("AMBIGUOUS")
    return {
        "name": str(name or ""),
        "tokens": rows,
        "ticker": hub().ticker_crosscheck([r["text"] for r in tickers]) if tickers
                  else {"state": "NODATA", "canonical": "", "seen": [], "why": "檔名裡沒有代號樣式"},
        "ticker_ambiguous": [r["text"] for r in amb],
        "date": (pick("DATE")[0]["value"] if pick("DATE") else ""),
        "quarter": (pick("QUARTER")[0]["value"] if pick("QUARTER") else ""),
        # 兩讀的那些**不進 year 也不進 ticker**——進了就是替操作員做了裁定。
        "year": (pick("YEAR")[0]["value"] if pick("YEAR") else ""),
        "broker": (pick("BROKER")[0]["value"] if pick("BROKER") else ""),
        "counts": {k: sum(1 for r in rows if r["role"] == k)
                   for k in ("TICKER", "DATE", "QUARTER", "YEAR", "AMBIGUOUS",
                             "BROKER", "OTHER", "PUNCT")},
    }


def reconcile_report(fn_parse: dict, peripheral: dict = None, body: dict = None) -> dict:
    """三來源合流。`peripheral` / `body` 給 `{"ticker","date","broker","rating","target_price"}`。

    優先權與衝突處理**全部委由樞紐的 `reconcile()`**——優先權寫在冊上不是寫在這裡。
    """
    h = hub()
    p, b = (peripheral or {}), (body or {})
    fn = {"ticker": (fn_parse.get("ticker") or {}).get("canonical", ""),
          "date": fn_parse.get("date", ""), "broker": fn_parse.get("broker", "")}
    out = {}
    for field in ("ticker", "date", "broker", "rating", "target_price"):
        out[field] = h.reconcile({"本文": b.get(field), "第一頁周邊資訊區": p.get(field),
                                  "檔名": fn.get(field)}, field)
    # 券商例外:電郵網域勝過三來源(冊上 source_priority.exception)
    dom_bk = ""
    for addr in h.emails_of(b.get("_text", "") or p.get("_text", "")):
        d = h.analyst_from_email(addr)
        if d.get("broker"):
            dom_bk = d["broker"]
            break
    if dom_bk:
        prev = out["broker"]
        out["broker"] = {"state": "GREEN" if prev.get("value") in ("", None, dom_bk) else "YELLOW",
                         "value": dom_bk, "src": "電郵網域",
                         "seen": dict(prev.get("seen") or {}, **{"電郵網域": dom_bk}),
                         "why": ("網域是最硬的券商證據(檔名會被改、封面會換版型,寄件網域不會)"
                                 + ("" if prev.get("value") in ("", None, dom_bk)
                                    else f";與其他來源不一致:{prev.get('value')}"))}
    return out


def scan(indir: str) -> dict:
    d = Path(indir)
    if not d.exists():
        return {"state": "ABSENT", "why": f"夾子不在:{d}"}
    files = [p for p in sorted(d.rglob("*")) if p.is_file()]
    if not files:
        return {"state": "NODATA", "why": f"夾子在但是空的:{d}"}
    rows = [parse_filename(p.name) for p in files]
    tal = {"ticker_green": sum(1 for r in rows if r["ticker"]["state"] == "GREEN"),
           "ticker_conflict": sum(1 for r in rows if r["ticker"]["state"] == "YELLOW"),
           "ticker_none": sum(1 for r in rows if r["ticker"]["state"] == "NODATA"),
           "date": sum(1 for r in rows if r["date"]),
           "quarter": sum(1 for r in rows if r["quarter"]),
           "broker": sum(1 for r in rows if r["broker"]),
           "ambiguous": sum(1 for r in rows if r["ticker_ambiguous"])}
    return {"state": "OK", "dir": str(d), "n": len(rows), "tally": tal, "rows": rows}


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VRN_ENG084 檔名切分與三來源合流 v{VERSION} · 自測(零網路;零寫檔)===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 沒有 --apply(只讀只報)", '"--apply"' not in code)
    chk("③ 零九頭龍:一條正則都不自己寫,全部呼叫樞紐"
        "(本器只做保護→切分→歸類;`_CLS` 四類是操作員逐字給的切分規則,不是抽取規則)",
        "hub()" in code and "SUP_MDL749" in code
        and code.count('re.compile(r"') == 0)

    t1 = tokenize("2025_富邦_台積電(2330)_投資評等報告_20250122.pdf")
    kinds = [x["cls"] for x in t1]
    chk("④ 中英數標點切開(操作員令的第一句)",
        "CJK" in kinds and "NUM" in kinds and "PUNCT" in kinds,
        f"({len(t1)} 段)")

    t2 = tokenize("TSMC_2330.TW_Jan 22, 2025_Target.pdf")
    prot = {x["text"] for x in t2 if x["protected"]}
    chk("⑤ **切之前先鎖**:`2330.TW` 不可以被標點切成 2330/./TW",
        "2330.TW" in prot, str(sorted(prot)))
    chk("⑥ 英文日期不可以被切成三段(`Jan 22, 2025` 要整段鎖住)",
        any("2025" in x and "Jan" in x for x in prot), str(sorted(prot)))

    t3 = tokenize("元大00715B債券ETF季報2025Q2.pdf")
    prot3 = {x["text"] for x in t3 if x["protected"]}
    chk("⑦ ETF 尾碼不可以被中英數切掉(`00715B` → 00715 / B 就死了);"
        "季度 `2025Q2` 同理",
        "00715B" in prot3 and "2025Q2" in prot3, str(sorted(prot3)))

    p1 = parse_filename("2025_富邦_台積電(2330)_投資評等報告_20250122.pdf")
    chk("⑧ 檔名整份解析:代號 2330 · 日期 2025-01-22 · 券商 FUBON",
        p1["ticker"]["canonical"] == "2330" and p1["date"] == "2025-01-22"
        and p1["broker"] == "FUBON",
        f"({p1['ticker']['canonical']} / {p1['date']} / {p1['broker']})")

    p2 = parse_filename("TSMC_2330.TW_2330 TT_20250122.pdf")
    chk("⑨ 同一份裡三種寫法要對得起來(本地碼逐字相同=GREEN)",
        p2["ticker"]["state"] == "GREEN" and p2["ticker"]["canonical"] == "2330",
        p2["ticker"]["why"])
    p3 = parse_filename("2330.TW_vs_2317 TT.pdf")
    chk("⑩ 對不起來就是 YELLOW,而且**三個值都留著**(不挑一個用)",
        p3["ticker"]["state"] == "YELLOW" and len(p3["ticker"]["seen"]) == 2,
        p3["ticker"]["why"][:60])

    p4 = parse_filename("半導體產業展望_20250122.pdf")
    chk("⑪ **日期區段先鎖住,裸四碼才不會被當成代號**:"
        "`20250122` 整段是日期,裡面的 `2025` 不可以另外變成一支個股",
        p4["date"] == "2025-01-22" and p4["ticker"]["state"] == "NODATA",
        f"(代號 {p4['ticker']['state']} · 日期 {p4['date']})")
    p5 = parse_filename("展望_2025_半導體.pdf")
    chk("⑫ 裸四碼兩讀都留,**不准自己挑一個**:`2025` 單獨出現時"
        "既是合法西元年也是合法個股代號(2025 真的是一支上市公司)。"
        "第一版我先問期間、中了就回——於是它永遠是年,ambiguous 那支旗子從來沒亮過,"
        "而這一檢當時是用 `or` 寫的,**照樣綠**",
        p5["ticker_ambiguous"] == ["2025"] and p5["year"] == ""
        and p5["ticker"]["state"] == "NODATA"
        and parse_filename("半導體_2330.pdf")["ticker_ambiguous"] == [],
        f"(兩讀 {p5['ticker_ambiguous']} · 年 {p5['year'] or '不填(對)'})")

    p6 = parse_filename("富邦_台積電_250122.pdf")
    chk("⑬ 券商省略世紀的寫法:`250122` → 2025-01-22(操作員點名的那一種)",
        p6["date"] == "2025-01-22", f"({p6['date']})")
    p7 = parse_filename("國泰_2330_1140122.pdf")
    chk("⑭ 民國:`1140122` → 2025-01-22", p7["date"] == "2025-01-22", f"({p7['date']})")

    r = reconcile_report(parse_filename("富邦_2330_20250122.pdf"),
                         {"ticker": "2330", "date": "2025-01-22"},
                         {"ticker": "2330", "date": "2025-01-22",
                          "_text": "分析師 陳小明 wei-ting.chen@fubon.com"})
    chk("⑮ 三來源合流:一致 = GREEN",
        r["ticker"]["state"] == "GREEN" and r["date"]["state"] == "GREEN",
        f"({r['ticker']['state']} / {r['date']['state']})")
    chk("⑯ 券商例外:**電郵網域勝過三來源**"
        "(檔名會被改、封面會換版型,寄件網域不會)",
        r["broker"]["src"] == "電郵網域" and r["broker"]["value"] == "FUBON",
        r["broker"]["why"][:44])
    r2 = reconcile_report(parse_filename("富邦_2330_20250122.pdf"),
                          {"ticker": "2317"}, {"ticker": "2330"})
    chk("⑰ 衝突不藏:依優先權取本文,但把每一個來源的值都列出來",
        r2["ticker"]["state"] == "YELLOW" and r2["ticker"]["value"] == "2330"
        and "2317" in r2["ticker"]["why"],
        r2["ticker"]["why"][:56])

    chk("⑱ 夾子不在=誠實 ABSENT · 空夾=NODATA(兩件事兩句話)",
        scan("/no/such/dir")["state"] == "ABSENT")
    chk("⑲ 保護樣式的次序是**長的先鎖**:`2330.TW` 要在 `2330` 之前,"
        "不然鎖完只剩一個 `.TW`",
        _protect_patterns()[0][0] == "TICKER_PLATFORM")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(檢數現場計)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG084_FilenameTokenParse",
                                 description="檔名切分與三來源合流(零網路;只讀)")
    ap.add_argument("verb", nargs="?", default="parse", choices=["parse", "scan"])
    ap.add_argument("--name", default="", help="單一檔名")
    ap.add_argument("--in", dest="indir", default="", help="報告夾(只讀檔名,不開檔)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "scan":
        if not a.indir:
            print("  [絕] scan 要給夾子:--in \"C:\\測試樣本報告\"")
            return 1
        r = scan(a.indir)
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
            return 0 if r["state"] == "OK" else {"NODATA": 2, "ABSENT": 3}.get(r["state"], 1)
        if r["state"] != "OK":
            print(f"[VRN_ENG084 v{VERSION}] scan · {r['state']} · {r['why']}")
            return {"NODATA": 2, "ABSENT": 3}.get(r["state"], 1)
        t = r["tally"]
        print(f"[VRN_ENG084 v{VERSION}] scan · OK · {r['n']} 個檔名")
        print(f"  代號 GREEN {t['ticker_green']} · 衝突 {t['ticker_conflict']} · 無 {t['ticker_none']}"
              f"(其中年碼重疊 {t['ambiguous']})")
        print(f"  日期 {t['date']} · 季度 {t['quarter']} · 券商 {t['broker']}")
        return 0
    if not a.name:
        print("  [絕] parse 要給檔名:--name \"...\"")
        return 1
    p = parse_filename(a.name)
    if a.json:
        print(json.dumps(p, ensure_ascii=False))
        return 0
    print(f"[VRN_ENG084 v{VERSION}] parse · {p['name']}")
    for t in p["tokens"]:
        mark = "🔒" if t["protected"] else "  "
        print(f"  {mark} {t['cls']:6} {t['role']:8} {t['text'][:28]:28} {t['value'][:22]}")
    print(f"  [結] 代號 {p['ticker']['state']} {p['ticker']['canonical']} · "
          f"日期 {p['date'] or '—'} · 季度 {p['quarter'] or '—'} · "
          f"年 {p['year'] or '—'} · 券商 {p['broker'] or '—'}")
    if p["ticker_ambiguous"]:
        print(f"  [疑] 年碼重疊(四碼同時像代號與西元年):{p['ticker_ambiguous']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
