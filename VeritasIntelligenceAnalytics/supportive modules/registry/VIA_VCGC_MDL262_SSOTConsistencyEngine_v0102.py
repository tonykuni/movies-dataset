#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_VCGC_MDL262_SSOTConsistencyEngine v0102 — 薄尾:期間 / 日期統一形式(年 YYYY · 月 YYYY-MM · 季 nQYY · 日 YYYY-MM-DD)

操作員 2026-11-14:「YYYY YYYY-MM 2Q23 YYYY-MM-DD 不管先前多無正形,最後統一以上形式」。
正本是 VIA_SSOT_PeriodFormat_SSOT 尾版(四種形式的式子 · 各種來源寫法 → 統一形式的對照樣本 · 不該硬轉的樣本)。本版:
  period <字串> [<字串> …] [--json]   把來源寫法轉成統一形式;認不出或兩種讀法都成立 → UNRESOLVED(不猜),rc 1
  period --audit                       冊的自我一致:四式兩兩互斥(自動機證明)· 四式沒有方言漂移 · 冊上每個樣本都轉成冊上寫的答案 ·
                                       不該轉的都沒被硬轉 · 統一形式再轉一次不變(冪等)
規則:先 NFKC(全形 → 半形);期別後綴 A / E / F(實績 / 預估 / 預測)拆成另一欄 basis,不留在期間裡;民國年 +1911;
兩位數年只在有標記(Q · FY · 月份英文 · ')時才當 20YY;日期用曆法驗(2 月 30 日不存在);數字日期日 / 月順序分不出來就不轉。
其餘動詞原樣交給前版(v0101 → v0100)。只讀 · 零網路 · 純標準庫 · 不寫任何檔 · 不改任何系統的期間冊(L123)。
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

import datetime
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_MDL262_SSOTConsistencyEngine"
ENGINE = _STEM
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
PERIOD_GLOB = "VIA_SSOT_PeriodFormat_SSOT_v[0-9][0-9][0-9][0-9].json"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_scc_prior_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR
while "PRIOR" in vars(BASE):
    BASE = vars(BASE)["PRIOR"]


def __getattr__(name: str):
    return getattr(PRIOR, name)


MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
MON.update({"JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "SEPT": 9,
            "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12})
_MON = "(" + "|".join(sorted(MON, key=len, reverse=True)) + ")"
ZHQ = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}
LABEL = re.compile(r"^(?:PERIOD|DATE|AS OF|季度|年度|期間|期別|日期|截至|報告日)\s*[::]?\s*")
FORMS = {"year": r"^[0-9]{4}$", "month": r"^[0-9]{4}-(0[1-9]|1[0-2])$", "quarter": r"^[1-4]Q[0-9]{2}$",
         "date": r"^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"}


def _yr(tok: str, marked: bool = True):
    """年:四位照用(1900–2100);民國三位(100–199)+1911;兩位只在有標記時當 20YY。認不出回 None。"""
    n = int(tok)
    if len(tok) == 4:
        return n if 1900 <= n <= 2100 else None
    if len(tok) == 3:
        return n + 1911 if 100 <= n <= 199 else None
    if len(tok) == 2 and marked:
        return 2000 + n
    return None


def _un(raw, why):
    return {"raw": raw, "kind": None, "period": None, "basis": None, "state": "UNRESOLVED", "why": why}


def _ok(raw, kind, period, basis):
    return {"raw": raw, "kind": kind, "period": period, "basis": basis, "state": "OK", "why": ""}


def _date(raw, y, m, d, basis):
    if y is None:
        return _un(raw, "年份認不出來")
    try:
        datetime.date(y, m, d)
    except ValueError:
        return _un(raw, "日期不存在")
    return _ok(raw, "date", "%04d-%02d-%02d" % (y, m, d), basis)


def _month(raw, y, m, basis):
    if y is None:
        return _un(raw, "年份認不出來")
    if not 1 <= m <= 12:
        return _un(raw, "月份不存在")
    return _ok(raw, "month", "%04d-%02d" % (y, m), basis)


def _quarter(raw, y, q, basis):
    if y is None:
        return _un(raw, "年份認不出來")
    if not 2000 <= y <= 2099:
        return _un(raw, "兩位數年表示不了 2000–2099 以外的季")
    return _ok(raw, "quarter", "%dQ%02d" % (q, y % 100), basis)


def normalize_period(raw) -> dict:
    """來源寫法 → {kind, period, basis, state}。認不出或有兩種讀法 → state=UNRESOLVED(不猜)。"""
    if not isinstance(raw, str) or not raw.strip():
        return _un(raw, "空的")
    s = unicodedata.normalize("NFKC", raw).strip().upper()
    s = s.strip("()[]{}<>「」 \t")
    s = LABEL.sub("", s)
    roc = "民國" in s or "民国" in s
    s = s.replace("民國", "").replace("民国", "").strip()
    basis = None
    m = re.fullmatch(r"(.*?[0-9季月日年])\s*([AEF])\.?", s)
    if m:
        s, basis = m.group(1).strip(), m.group(2)
    s = re.sub(r"\s+", " ", s)

    def yr(tok, marked=True):
        if roc and len(tok) <= 3:
            n = int(tok)
            return n + 1911 if 1 <= n <= 199 else None
        return _yr(tok, marked)

    # ---- 日
    m = re.fullmatch(r"(\d{3,4})\s*[-/.年]\s*(\d{1,2})\s*[-/.月]\s*(\d{1,2})\s*日?", s)
    if m:
        return _date(raw, yr(m.group(1)), int(m.group(2)), int(m.group(3)), basis)
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", s)
    if m:
        return _date(raw, _yr(m.group(1)), int(m.group(2)), int(m.group(3)), basis)
    m = re.fullmatch(r"(\d{1,2})[- ]?" + _MON + r"[- ,']*(\d{4}|\d{2})", s)
    if m:
        return _date(raw, _yr(m.group(3)), MON[m.group(2)], int(m.group(1)), basis)
    m = re.fullmatch(_MON + r"\.? (\d{1,2}),? (\d{4})", s)
    if m:
        return _date(raw, _yr(m.group(3)), MON[m.group(1)], int(m.group(2)), basis)
    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), _yr(m.group(3))
        if a > 12 >= b:
            return _date(raw, y, b, a, basis)
        if b > 12 >= a:
            return _date(raw, y, a, b, basis)
        return _un(raw, "日 / 月順序兩種讀法都成立" if a <= 12 and b <= 12 else "日期不存在")
    # ---- 季
    m = re.fullmatch(r"(\d{3,4}) ?[-./_]? ?Q([1-4])", s) or re.fullmatch(r"(\d{3,4}) ?年? ?第? ?([1-4一二三四]) ?季", s)
    if m:
        return _quarter(raw, yr(m.group(1)), ZHQ[m.group(2)], basis)
    m = re.fullmatch(r"(?:FY|CY)? ?Q([1-4]) ?[-./_']? ?(\d{4}|\d{2})", s) or re.fullmatch(r"([1-4])Q ?'?(\d{4}|\d{2})", s)
    if m:
        return _quarter(raw, _yr(m.group(2)), int(m.group(1)), basis)
    m = re.fullmatch(r"(?:FY|CY)? ?(\d{2})Q([1-4])", s)
    if m:
        return _quarter(raw, _yr(m.group(1)), int(m.group(2)), basis)
    if re.fullmatch(r"\d{0,4} ?[-./_]? ?[05-9]Q ?'?\d{2,4}|\d{2,4} ?[-./_]? ?Q[05-9]", s):
        return _un(raw, "沒有這一季")
    # ---- 月
    m = re.fullmatch(r"(\d{3,4}) ?[-/.年] ?(\d{1,2}) ?月?", s)
    if m:
        return _month(raw, yr(m.group(1)), int(m.group(2)), basis)
    m = re.fullmatch(r"(\d{4})(\d{2})", s)
    if m and 1 <= int(m.group(2)) <= 12 and _yr(m.group(1)):
        return _month(raw, _yr(m.group(1)), int(m.group(2)), basis)
    m = re.fullmatch(_MON + r"\.?[- ,']*(\d{4}|\d{2})", s)
    if m:
        return _month(raw, _yr(m.group(2)), MON[m.group(1)], basis)
    m = re.fullmatch(r"(\d{4}) ?" + _MON, s)
    if m:
        return _month(raw, _yr(m.group(1)), MON[m.group(2)], basis)
    m = re.fullmatch(r"(\d{1,2})/(\d{2})", s)
    if m:
        if basis:                           # 表頭式 12/24A:帶 A / E / F 才認成 月/年
            return _month(raw, 2000 + int(m.group(2)), int(m.group(1)), basis)
        return _un(raw, "可能是月/年也可能是日/月")
    # ---- 年
    m = re.fullmatch(r"(?:FY|CY) ?(\d{4}|\d{2})", s)
    if m:
        y = _yr(m.group(1))
        return _ok(raw, "year", "%04d" % y, basis) if y else _un(raw, "年份認不出來")
    m = re.fullmatch(r"(\d{2,4}) ?年?", s)
    if m:
        tok = m.group(1)
        if roc or (len(tok) == 3 and s.endswith("年")):
            y = yr(tok) if roc else _yr(tok)
        elif len(tok) == 4:
            y = _yr(tok)
        else:
            return _un(raw, "只有兩三位數,沒有任何標記" if len(tok) < 4 else "年份認不出來")
        return _ok(raw, "year", "%04d" % y, basis) if y else _un(raw, "年份認不出來")
    if re.search(r"\bH[12]\b|[12]H\d{2}|\d+M\d{2}|YTD|W\d{1,2}\b|半年", s):
        return _un(raw, "半年度 / 累計 / 週還沒有統一形式(待裁)")
    return _un(raw, "不是認得的期間寫法")


def load_period_book(registry: Path):
    hits = sorted(Path(registry).glob(PERIOD_GLOB), key=_vnum)
    if not hits:
        raise ValueError("期間形式冊不存在(%s)" % PERIOD_GLOB)
    return hits[-1], BASE.read_json(hits[-1])


def audit(registry: Path) -> dict:
    """冊的自我一致 + 引擎與冊對不對得上。回 {rows:[(燈, 名, 細節)], lamp}。"""
    path, book = load_period_book(registry)
    rows = []
    forms = {k: v.get("regex") for k, v in (book.get("forms") or {}).items()}
    rows.append(("GREEN" if forms == FORMS else "RED", "四種形式的式子與引擎一致", "" if forms == FORMS else "冊 %s ≠ 引擎 %s" % (forms, FORMS)))
    keys = sorted(forms)
    bad = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            try:
                r = BASE.relate(BASE.build_lang(forms[keys[i]], "full"), BASE.build_lang(forms[keys[j]], "full"))
                if r["rel"] != "DISJOINT":
                    bad.append("%s×%s %s 例 %s" % (keys[i], keys[j], r["rel"], BASE.show(r.get("both"))))
            except BASE.Unsupported as exc:
                bad.append("%s×%s 不可證(%s)" % (keys[i], keys[j], exc))
    rows.append(("GREEN" if not bad else "RED", "四式兩兩互斥(自動機證明):同一個字串不會同時是兩種形式", ";".join(bad)))
    drift = [k for k in keys if any(f["code"] == "RGX_DIALECT_DRIFT" for f in BASE.lint(forms[k]))]
    rows.append(("GREEN" if not drift else "RED", "四式沒有方言漂移(只收 ASCII 數字)", " · ".join(drift)))
    wrong = []
    for kind, spec in (book.get("forms") or {}).items():
        for ex in spec.get("examples") or []:
            hit = [k for k in keys if re.fullmatch(forms[k], ex)]
            n = normalize_period(ex)
            if hit != [kind] or n["period"] != ex or n["kind"] != kind:
                wrong.append("%s → %s / %s" % (ex, hit, n["period"]))
    rows.append(("GREEN" if not wrong else "RED", "統一形式的樣本只合自己那一式,再轉一次不變(冪等)", ";".join(wrong[:4])))
    miss = ["%s → %s(冊寫 %s)" % (a, normalize_period(a)["period"], b) for a, b in book.get("variants") or [] if normalize_period(a)["period"] != b]
    rows.append(("GREEN" if not miss else "RED", "來源寫法 %d 個都轉成冊上寫的答案" % len(book.get("variants") or []), ";".join(miss[:5])))
    forced = ["%s → %s" % (a, normalize_period(a)["period"]) for a, _w in book.get("unresolved") or [] if normalize_period(a)["state"] != "UNRESOLVED"]
    rows.append(("GREEN" if not forced else "RED", "不該硬轉的 %d 個都沒被硬轉" % len(book.get("unresolved") or []), ";".join(forced[:5])))
    bs = ["%s → %s" % (k, (normalize_period(k)["period"], normalize_period(k)["basis"])) for k, v in ((book.get("basis") or {}).get("examples") or {}).items()
          if [normalize_period(k)["period"], normalize_period(k)["basis"]] != list(v)]
    rows.append(("GREEN" if not bs else "RED", "期別後綴 A / E / F 拆成另一欄", ";".join(bs[:4])))
    return {"book": path.name, "rows": rows, "lamp": "GREEN" if all(r[0] == "GREEN" for r in rows) else "RED",
            "divergence": book.get("known_divergence") or [], "undecided": book.get("undecided") or []}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] != ["period"]:
        return PRIOR.main(a)
    rest = a[1:]
    flags = {x for x in rest if x.startswith("--")}
    items = [x for x in rest if not x.startswith("--")]
    if flags - {"--json", "--audit"} or ("--audit" in flags and items) or ("--audit" not in flags and not items):
        print("用法:python %s period <字串> [<字串> …] [--json] | period --audit" % Path(__file__).name)
        return 2
    if "--audit" in flags:
        try:
            res = audit(BASE.VIA / "supportive modules" / "registry")
        except ValueError as exc:
            print("[SSOT 期間形式] RED · %s" % exc)
            return 1
        if "--json" in flags:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            print("[SSOT 期間形式] %s · %s %s · 冊 %s · 檢 %d 項" % (res["lamp"], ENGINE, TAG, res["book"], len(res["rows"])))
            for lamp, name, detail in res["rows"]:
                print("  %-6s %s%s" % (lamp, name, (" · " + detail[:200]) if detail else ""))
            for d in res["divergence"]:
                print("  [現況不同] %s:%s" % (d.get("book"), d.get("now")))
            if res["undecided"]:
                print("  [待裁] " + " · ".join(res["undecided"]))
        return 0 if res["lamp"] == "GREEN" else 1
    out = [normalize_period(x) for x in items]
    if "--json" in flags:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        for r in out:
            if r["state"] == "OK":
                print("  %-22s → %-10s %s%s" % (r["raw"], r["period"], {"year": "年", "month": "月", "quarter": "季", "date": "日"}[r["kind"]],
                                               (" · " + {"A": "實績", "E": "預估", "F": "預測"}[r["basis"]]) if r["basis"] else ""))
            else:
                print("  %-22s → UNRESOLVED · %s" % (r["raw"], r["why"]))
    return 0 if all(r["state"] == "OK" for r in out) else 1


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK " if cond else "NG ", name, (" · " + str(note)[:240]) if note and not cond else ""))

    print("=== %s %s · 薄尾自測(期間 / 日期統一形式)===" % (ENGINE, TAG))
    n = lambda s: normalize_period(s)["period"]                      # noqa: E731
    k = lambda s: normalize_period(s)["kind"]                        # noqa: E731
    chk("① 四種統一形式再轉一次不變(冪等)", [n(x) for x in ("2023", "2023-06", "2Q23", "2023-06-05")] == ["2023", "2023-06", "2Q23", "2023-06-05"]
        and [k(x) for x in ("2023", "2023-06", "2Q23", "2023-06-05")] == ["year", "month", "quarter", "date"])
    q = ["2023Q2", "2023 Q2", "2023.Q2", "Q2 2023", "Q2'23", "2Q2023", "23Q2", "2023年第二季", "2023第2季", "112年第2季", "112Q2", "FY23Q2", "２０２３Ｑ２"]
    chk("② 季的 %d 種寫法都落在 2Q23" % len(q), all(n(x) == "2Q23" for x in q), [(x, n(x)) for x in q if n(x) != "2Q23"])
    d = ["2023/6/5", "2023.06.05", "20230605", "2023年6月5日", "112/06/05", "民國112年6月5日", "5-Jun-23", "Jun 5, 2023", "05 JUNE 2023"]
    chk("③ 日的 %d 種寫法都落在 2023-06-05" % len(d), all(n(x) == "2023-06-05" for x in d), [(x, n(x)) for x in d if n(x) != "2023-06-05"])
    mm = ["2023/6", "2023.06", "2023年6月", "202306", "Jun-23", "June 2023", "2023 Jun", "112/06", "民國112年6月"]
    chk("④ 月的 %d 種寫法都落在 2023-06" % len(mm), all(n(x) == "2023-06" for x in mm), [(x, n(x)) for x in mm if n(x) != "2023-06"])
    yy = ["2023年", "FY2023", "FY23", "CY2023", "民國112年", "112年"]
    chk("⑤ 年的 %d 種寫法都落在 2023" % len(yy), all(n(x) == "2023" for x in yy), [(x, n(x)) for x in yy if n(x) != "2023"])
    amb = ["06/05/2023", "06/23", "23", "112", "abc", "", "H1 2023", "9M23", "2023W23"]
    chk("⑥ 兩種讀法都成立 / 沒有標記 / 還沒定形式的:不猜(UNRESOLVED)", all(normalize_period(x)["state"] == "UNRESOLVED" for x in amb),
        [(x, n(x)) for x in amb if normalize_period(x)["state"] != "UNRESOLVED"])
    bad = ["2023-13", "2023-02-30", "2023/00/10", "5Q23", "2023Q5", "1998Q2", "2101", "20231345"]
    chk("⑦ 不存在的月 / 日 / 季、表示不了的年:不轉", all(normalize_period(x)["state"] == "UNRESOLVED" for x in bad),
        [(x, n(x)) for x in bad if normalize_period(x)["state"] != "UNRESOLVED"])
    chk("⑧ 日 / 月順序只有一種讀法時才轉(13/06 與 06/13 都是 6 月 13 日)", n("13/06/2023") == n("06/13/2023") == "2023-06-13")
    b = [normalize_period(x) for x in ("1Q26E", "FY2025E", "12/24A", "2025F.", "(1Q26E)")]
    chk("⑨ 後綴 A / E / F 拆成 basis,期間照統一形式", [(x["period"], x["basis"]) for x in b] == [("1Q26", "E"), ("2025", "E"), ("2024-12", "A"), ("2025", "F"), ("1Q26", "E")],
        [(x["period"], x["basis"]) for x in b])
    chk("⑩ 閏年照曆法:2024-02-29 在、2023-02-29 不在", n("2024/2/29") == "2024-02-29" and normalize_period("2023/2/29")["state"] == "UNRESOLVED")
    chk("⑪ 原字串原樣帶回,不覆寫", normalize_period(" Q2 2023 ")["raw"] == " Q2 2023 ")
    import random
    rnd = random.Random(20261114)
    good = True
    for _ in range(400):
        y, mo, dd, qq = rnd.randint(2000, 2099), rnd.randint(1, 12), rnd.randint(1, 28), rnd.randint(1, 4)
        good = good and n("%d/%d/%d" % (y, mo, dd)) == "%04d-%02d-%02d" % (y, mo, dd) and n("%dQ%d" % (y, qq)) == "%dQ%02d" % (qq, y % 100) \
            and n("%d年%d月" % (y, mo)) == "%04d-%02d" % (y, mo) and n("%d" % y) == "%04d" % y
    chk("⑫ 隨機 400 組年 / 月 / 日 / 季來回都對", good)
    outs = [normalize_period(x) for x in q + d + mm + yy]
    chk("⑬ 轉出來的每一個都合四式其中一式、且只合一式", all(sum(bool(re.fullmatch(rx, o["period"])) for rx in FORMS.values()) == 1 for o in outs))
    try:
        res = audit(HERE)
        chk("⑭ 真冊 audit 全綠(%d 項;含四式互斥的自動機證明)" % len(res["rows"]), res["lamp"] == "GREEN", [r for r in res["rows"] if r[0] != "GREEN"])
    except ValueError as exc:
        chk("⑭ 真冊讀得到", False, str(exc))
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]
    chk("⑮ 加速器橋在;自測以外沒有任何寫檔動作", "VIA:ACCEL-BRIDGE" in src and not re.search(r"\.write_text\(|\.write_bytes\(|os\.replace", src))
    print("[%s %s 薄尾自測] %d/%d %s" % (ENGINE, TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"))
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
