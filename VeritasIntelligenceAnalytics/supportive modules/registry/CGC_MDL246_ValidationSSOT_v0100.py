#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL246_ValidationSSOT v0100 — 三系統驗證 SSOT 核對器(驗證邏輯 · 結果驗證 · 交叉核對;X-VAL)

操作員 2026-09-29:「三個系統的validation logic result validation logic cross checking機制寫入ssot」。
冊 = VIA_Validation_SSOT_v*.json(尾版):VCGC · VDF · VRN 各三層——validation_logic(<系統>-VAL)· result_validation
(<系統>-RVL)· cross_check(X- 代碼;三系統共用一本代碼表 cross_checks)。每一條都指名正主。這支只核對「冊上說的」與
「樹上有的」是不是同一件事,不改任何冊:
  V-SHAPE   冊讀得到 · 三系統都在 · 每系統三層都不空 · 每條有 code / name / owner
  V-CODE    代碼格式與層相符(VAL 只在 validation_logic、RVL 只在 result_validation、系統前綴相符)· 不撞號 · 不用退役號
  V-OWNER   每一條的正主在(_v*.py 取尾版;.json / .py 照路徑)
  V-IMPL    交叉代碼的實作記號(symbol)在正主**整條版本鏈**裡找得到(薄尾的函式常在前一版本體)
  V-XREF    雙向:工作流冊 tests.cross 引用的每個代碼都登記在本冊(X-* 是通配)· 各系統 cross_check 只列已登記的 ·
            登記了卻沒人用 = 黃
  V-SDD     SDD 驗證器(CGC_MDL245 版本鏈)實作的每個 X- 代碼都登記在本冊——驗證器多了新檢、本冊沒跟上 = 紅
  V-POLICY  policy 引用對得到:L<條> 在法冊,其餘是政策小冊的 id
  V-REF     refs 指的工作流 / 步代碼在工作流冊
實錄(寫冊當下量到的):三本工作流冊的 tests.cross 引用 X-CONF(4 處)與 X-NET(VDF 2 處),SDD 驗證器從來沒實作這兩個代碼,
也沒有任何一本冊說它們由誰實作——本冊把它們登記到真的正主(X-CONF = VCGC conformance · X-NET = 全景治理類 NET)。
工作流冊照 CGC_MDL245 的 load_books 讀(L05 一把尺;讀不到才退回自己找尾版)。
量不到 ≠ 通過:冊不在 = ABSENT rc3;紅 rc1 · 黃 rc2 · 綠 rc0。只收 VCGC 呼叫(VIA_FROM_VCGC=YES);自測不需要。
零網路 · 不安裝 · 唯讀(check --write 才寫 VIA_Reports/sdd/VAL_CHECK_latest.json,不入 git)。

用法(經 VCGC):
  via-vcgc val                 核對(= via-vcgc run --family core CGC_MDL246_ValidationSSOT check)
  via-vcgc val show [VDF]      三系統三層表
  python CGC_MDL246_ValidationSSOT_v0100.py --selftest
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

import copy
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
OUT = VIA / "VIA_Reports" / "sdd"
BOOK_GLOB = "VIA_Validation_SSOT_v*.json"
SYSTEMS = ("VCGC", "VDF", "VRN")
LAYERS = (("validation_logic", "VAL", "驗證邏輯"), ("result_validation", "RVL", "結果驗證"))
CODE_RX = re.compile(r"^(VCGC|VDF|VRN)-(VAL|RVL)(\d{3})$")
XCODE_RX = re.compile(r"^X-[A-Z]+$")
SDD_XCODE_RX = re.compile(r"\"(X-[A-Z]+)\"")
RULES = ("V-SHAPE", "V-CODE", "V-OWNER", "V-IMPL", "V-XREF", "V-SDD", "V-POLICY", "V-REF")


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def newest(pattern: str, folder: Path = HERE) -> Path | None:
    hits = sorted(folder.glob(pattern), key=_vnum)
    return hits[-1] if hits else None


def _json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8")) if p else None
    except (OSError, ValueError):
        return None


_SDD: dict = {}


def sdd():
    """SDD 驗證器尾版(工作流冊讀法的唯一正主)。不在或載入就炸回 None。"""
    if "m" not in _SDD:
        p, m = newest("CGC_MDL245_SDDValidator_v*.py"), None
        if p:
            try:
                spec = importlib.util.spec_from_file_location("sdd_for_" + ENGINE, p)
                m = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = m
                spec.loader.exec_module(m)
            except Exception:
                m = None
        _SDD["m"] = m
    return _SDD["m"]


def resolve(pattern: str, via: Path = VIA) -> Path | None:
    """正主路徑(相對 VIA 根;`_v*` = 尾版)。不在回 None。"""
    if not pattern or "/" not in pattern:
        return None
    if "*" in pattern:
        return newest(Path(pattern).name, via / Path(pattern).parent)
    p = via / pattern
    return p if p.exists() else None


def chain_text(p: Path | None) -> str:
    """正主整條版本鏈(同 stem、版號 ≤ 它的每一支)的原始碼。薄尾的函式常在前一版本體。"""
    if p is None:
        return ""
    m = re.match(r"^(?P<stem>.+)_v(?P<num>\d{4})\.py$", p.name)
    files = [p]
    if m:
        files = [q for q in p.parent.glob(m.group("stem") + "_v[0-9][0-9][0-9][0-9].py")
                 if _vnum(q) <= int(m.group("num"))]
    out = []
    for q in sorted(files, key=_vnum):
        try:
            out.append(q.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(out)


def workflow_books() -> dict:
    """{系統: 工作流冊}——照 CGC_MDL245 load_books(L05);讀不到才退回自己找尾版。"""
    m = sdd()
    if m is not None and hasattr(m, "load_books"):
        try:
            return {s: b for s, (_p, b) in m.load_books()["books"].items()}
        except Exception:
            pass
    return {s: _json(newest(f"VIA_Workflow_{s}_SSOT_v*.json")) or {} for s in ("VCGC", "VDF", "VRN", "VAP")}


def policy_ids(via: Path = VIA) -> set:
    """法冊的 L 條 + 各政策小冊的 id。"""
    reg = via / "supportive modules" / "registry"
    law = _json(newest("VIA_Policy_Laws_SSOT_v*.json", reg)) or {}
    ids = {str(x.get("id")) for x in law.get("laws") or [] if x.get("id")}
    for p in reg.glob("VIA_Policy_*_v*.json"):
        if "Laws_SSOT" in p.name:
            continue
        j = _json(p)
        if isinstance(j, dict) and j.get("id"):
            ids.add(str(j["id"]))
    return ids


def check(book=None, books=None, sdd_text=None, pol_ids=None, via: Path = VIA,
          write: bool = False, out: Path = OUT) -> dict:
    """核對驗證 SSOT。回 {state, rc, rows[], counts, book}。可注入各來源(自測用)。"""
    rows = []

    def row(lamp, rule, msg, ref=""):
        rows.append({"lamp": lamp, "rule": rule, "msg": msg, "ref": ref})

    bp = None
    if book is None:
        bp = newest(BOOK_GLOB, via / "supportive modules" / "registry")
        book = _json(bp)
    if not isinstance(book, dict):
        return {"schema": "VIA.Validation.Check.v1", "engine": ENGINE, "state": "ABSENT", "rc": 3, "rows": [],
                "counts": {}, "book": None, "why": f"驗證 SSOT 冊不在或讀不到({BOOK_GLOB})"}
    books = books if books is not None else workflow_books()
    pol_ids = pol_ids if pol_ids is not None else policy_ids(via)
    systems = book.get("systems") or {}
    xs = {str(x.get("code")): x for x in book.get("cross_checks") or [] if isinstance(x, dict)}
    retired = set(book.get("retired") or [])
    wk_codes = set()
    for b in books.values():
        for w in (b or {}).get("workflows") or []:
            wk_codes.add(w.get("code"))
            wk_codes.update(st.get("code") for st in w.get("steps") or [])
    for s in SYSTEMS:                                               # V-SHAPE
        sec = systems.get(s)
        if not isinstance(sec, dict):
            row("RED", "V-SHAPE", f"{s} 不在冊上", s)
            continue
        for layer, _k, zh in LAYERS:
            if not sec.get(layer):
                row("RED", "V-SHAPE", f"{s} 的{zh}({layer})是空的", s)
        if not sec.get("cross_check"):
            row("RED", "V-SHAPE", f"{s} 的交叉核對(cross_check)是空的", s)
    seen = {}
    for s in SYSTEMS:
        sec = systems.get(s) if isinstance(systems.get(s), dict) else {}
        for layer, kind, _zh in LAYERS:
            for e in sec.get(layer) or []:
                c = str(e.get("code") or "")
                m = CODE_RX.match(c)
                if not m or m.group(1) != s or m.group(2) != kind:
                    row("RED", "V-CODE", f"{s}.{layer} 的代碼 {c!r} 不對(這一層要 {s}-{kind}<三碼>)", c)
                if c in seen:
                    row("RED", "V-CODE", f"撞號 {c}(已在 {seen[c]})", c)
                seen.setdefault(c, f"{s}.{layer}")
                if c in retired:
                    row("RED", "V-CODE", f"用了已退役的號 {c}(號不回收)", c)
                if not e.get("name"):
                    row("RED", "V-SHAPE", f"{c} 沒有 name", c)
                if resolve(str(e.get("owner") or ""), via) is None:
                    row("RED", "V-OWNER", f"{c} 的正主不在:{e.get('owner')}", c)
                if e.get("policy") and str(e["policy"]) not in pol_ids:
                    row("RED", "V-POLICY", f"{c} 引的政策 {e['policy']} 對不到(法冊 L 條或政策小冊 id)", c)
                for r in e.get("refs") or []:
                    if r not in wk_codes:
                        row("RED", "V-REF", f"{c} 引的工作流 / 步 {r} 不在工作流冊", c)
    for code, x in xs.items():                                      # 交叉代碼本身
        if not XCODE_RX.match(code):
            row("RED", "V-CODE", f"交叉代碼 {code!r} 格式不對(X-<大寫>)", code)
        if code in retired:
            row("RED", "V-CODE", f"交叉代碼用了已退役的號 {code}", code)
        p = resolve(str(x.get("owner") or ""), via)
        if p is None:
            row("RED", "V-OWNER", f"{code} 的正主不在:{x.get('owner')}", code)
        else:
            sym = str(x.get("symbol") or "")
            if not sym.strip() or sym not in chain_text(p):
                row("RED", "V-IMPL", f"{code} 的實作記號 {sym!r} 不在 {p.name} 的版本鏈", code)
        if x.get("policy") and str(x["policy"]) not in pol_ids:
            row("RED", "V-POLICY", f"{code} 引的政策 {x['policy']} 對不到", code)
    by_books = {}                                                   # V-XREF(雙向)
    for s, b in books.items():
        for w in (b or {}).get("workflows") or []:
            for c in (w.get("tests") or {}).get("cross") or []:
                by_books.setdefault(c, set()).add(f"{s}:{w.get('code')}")
    for c, where in sorted(by_books.items()):
        if c != "X-*" and c not in xs:
            row("RED", "V-XREF", f"工作流冊引用了本冊沒登記的交叉代碼 {c}({', '.join(sorted(where)[:3])})", c)
    listed = set()
    for s in SYSTEMS:
        for c in (systems.get(s) or {}).get("cross_check") or [] if isinstance(systems.get(s), dict) else []:
            listed.add(c)
            if c != "X-*" and c not in xs:
                row("RED", "V-XREF", f"{s}.cross_check 列了沒登記的 {c}", c)
    for c in xs:
        if c not in listed and c not in by_books:
            row("YELLOW", "V-XREF", f"{c} 登記了,可是三系統都沒列、工作流冊也沒引用", c)
    if sdd_text is None:                                            # V-SDD
        sdd_text = chain_text(newest("CGC_MDL245_SDDValidator_v*.py", via / "supportive modules" / "registry"))
    if not sdd_text:
        row("YELLOW", "V-SDD", "SDD 驗證器不在,量不到它實作了哪些交叉代碼")
    else:
        miss = sorted(set(SDD_XCODE_RX.findall(sdd_text)) - set(xs))
        if miss:
            row("RED", "V-SDD", f"SDD 驗證器實作了本冊沒登記的交叉代碼:{', '.join(miss)}(驗證器多了新檢,本冊沒跟上)")
    bad = {r["rule"] for r in rows if r["lamp"] in ("RED", "YELLOW")}
    for rule in RULES:
        if rule not in bad:
            row("GREEN", rule, "過")
    state = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    counts = {s: {layer: len(((systems.get(s) or {}).get(layer) or [])) for layer, _k, _z in LAYERS}
              | {"cross_check": len((systems.get(s) or {}).get("cross_check") or [])} for s in SYSTEMS
              if isinstance(systems.get(s), dict)}
    rep = {"schema": "VIA.Validation.Check.v1", "engine": ENGINE, "state": state,
           "rc": {"GREEN": 0, "RED": 1, "YELLOW": 2}[state], "rows": rows, "counts": counts,
           "cross_checks": len(xs), "book": bp.name if bp else "(給定)"}
    if write:
        out.mkdir(parents=True, exist_ok=True)
        (out / "VAL_CHECK_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return rep


def show(system: str | None = None, book=None) -> str:
    book = book if book is not None else (_json(newest(BOOK_GLOB)) or {})
    xs = {x.get("code"): x for x in book.get("cross_checks") or []}
    lines = []
    for s in SYSTEMS:
        if system and s != system.upper():
            continue
        sec = (book.get("systems") or {}).get(s) or {}
        lines.append(f"=== [VIA 驗證 SSOT] {s} · {sec.get('zh', '')} ===")
        for layer, _k, zh in LAYERS:
            for e in sec.get(layer) or []:
                own = Path(str(e.get("owner") or "")).name
                pol = f"({e['policy']})" if e.get("policy") else ""
                lines.append(f"  {zh} {e.get('code')} {e.get('name')} ← {own}{pol}")
        for c in sec.get("cross_check") or []:
            x = xs.get(c) or {}
            lines.append(f"  交叉核對 {c} {x.get('zh', '(未登記)')} ← {Path(str(x.get('owner') or '')).name} {x.get('symbol', '')}")
    return "\n".join(lines)


def render(rep: dict) -> str:
    head = f"=== [VIA 驗證 SSOT 核對] {rep['state']} rc={rep['rc']} · 冊 {rep.get('book')} · 交叉代碼 {rep.get('cross_checks', 0)} ==="
    cnt = " · ".join(f"{s} 驗證邏輯 {c['validation_logic']} · 結果驗證 {c['result_validation']} · 交叉 {c['cross_check']}"
                     for s, c in (rep.get("counts") or {}).items())
    body = [f"  [{r['lamp']}] {r['rule']} {r['msg']}" for r in rep.get("rows") or [] if r["lamp"] != "GREEN"]
    ok = [r["rule"] for r in rep.get("rows") or [] if r["lamp"] == "GREEN"]
    return "\n".join([head, "  " + cnt] + body + ([f"  [GREEN] {' · '.join(ok)}"] if ok else []) + ([f"  {rep['why']}"] if rep.get("why") else []))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args and not args[0].startswith("-") else "check"
    if verb == "show":
        print(show(args[1] if len(args) > 1 else None))
        return 0
    rep = check(write="--write" in args)
    print(json.dumps(rep, ensure_ascii=False, indent=1) if "--json" in args else render(rep))
    return rep["rc"]


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    saved = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            denied = main(["check"]) == 2
        chk("① 門:沒經 via-vcgc 直呼 → DENY rc2", denied and "DENY" in buf.getvalue())
    finally:
        if saved is not None:
            os.environ["VIA_FROM_VCGC"] = saved
    bp = newest(BOOK_GLOB)
    real_bytes = bp.read_bytes() if bp else b""
    report = OUT / "VAL_CHECK_latest.json"
    report_before = report.read_bytes() if report.is_file() else None
    book = _json(bp) or {}
    books, pol, sdd_text = workflow_books(), policy_ids(), chain_text(newest("CGC_MDL245_SDDValidator_v*.py"))
    real = check(book=book, books=books, sdd_text=sdd_text, pol_ids=pol)
    reds = [r["msg"] for r in real["rows"] if r["lamp"] != "GREEN"]
    chk("② 真冊:三系統 × 三層都在 · 正主全在 · 實作記號全在 · 工作流冊引用的交叉代碼全登記 · SDD 驗證器的代碼全登記 → GREEN",
        real["state"] == "GREEN", "; ".join(reds)[:200] or " · ".join(f"{s} {c}" for s, c in real["counts"].items())[:200])

    def red(b=None, bk=None, st=None, rule=""):
        r = check(book=b if b is not None else book, books=bk if bk is not None else books,
                  sdd_text=st if st is not None else sdd_text, pol_ids=pol)
        return r["state"] == "RED" and any(x["rule"] == rule and x["lamp"] == "RED" for x in r["rows"])

    b1 = copy.deepcopy(book)
    b1["systems"]["VDF"]["result_validation"][0]["owner"] = "functional modules/VDF/engine/VDF_ENG999_Nope_v*.py"
    chk("③ 負控 正主不在 → 紅 V-OWNER", red(b1, rule="V-OWNER"))
    bk2 = copy.deepcopy(books)
    first = next(s for s in bk2 if (bk2[s] or {}).get("workflows"))
    bk2[first]["workflows"][0].setdefault("tests", {}).setdefault("cross", []).append("X-ZZZ")
    chk("④ 負控 工作流冊引用了本冊沒登記的交叉代碼 → 紅 V-XREF", red(bk=bk2, rule="V-XREF"))
    chk("⑤ 負控 SDD 驗證器多了新檢(本冊沒登記)→ 紅 V-SDD", red(st=sdd_text + '\n_row(rows, "RED", "X-NEWCHK", "x")\n', rule="V-SDD"))
    b6a = copy.deepcopy(book)                    # 四種各自獨立(不讓「撞號」那道順手擋掉別的)
    b6a["systems"]["VRN"]["result_validation"].append(dict(b6a["systems"]["VRN"]["validation_logic"][0], code="VRN-VAL099"))
    b6b = copy.deepcopy(book)
    b6b["systems"]["VDF"]["validation_logic"].append(dict(b6b["systems"]["VDF"]["validation_logic"][0], code="VRN-VAL098"))
    b6c = copy.deepcopy(book)
    b6c["systems"]["VCGC"]["validation_logic"].append(dict(b6c["systems"]["VCGC"]["validation_logic"][0]))
    b6d = copy.deepcopy(book)
    b6d["retired"] = [b6d["systems"]["VCGC"]["validation_logic"][0]["code"]]
    chk("⑥ 負控 代碼層錯(VAL 放進結果驗證)· 系統前綴錯 · 撞號 · 用了退役號 → 四種各自都紅 V-CODE",
        red(b6a, rule="V-CODE") and red(b6b, rule="V-CODE") and red(b6c, rule="V-CODE") and red(b6d, rule="V-CODE"))
    b7 = copy.deepcopy(book)
    b7["cross_checks"][0]["symbol"] = "def nope_zz_not_there"
    chk("⑦ 負控 實作記號不在正主版本鏈 → 紅 V-IMPL", red(b7, rule="V-IMPL"))
    b8 = copy.deepcopy(book)
    b8["systems"]["VRN"]["result_validation"] = []
    chk("⑧ 負控 缺一層(VRN 結果驗證空)→ 紅 V-SHAPE", red(b8, rule="V-SHAPE"))
    b9a = copy.deepcopy(book)
    b9a["systems"]["VCGC"]["validation_logic"][0]["policy"] = "ZZZ-9"
    b9b = copy.deepcopy(book)
    b9b["systems"]["VDF"]["result_validation"][0]["refs"] = ["VDF-WKF999-STP001"]
    chk("⑨ 負控 政策對不到 → 紅 V-POLICY;步代碼不在工作流冊 → 紅 V-REF", red(b9a, rule="V-POLICY") and red(b9b, rule="V-REF"))
    b10 = copy.deepcopy(book)
    b10["cross_checks"].append(dict(b10["cross_checks"][0], code="X-UNUSEDZ"))
    r10 = check(book=b10, books=books, sdd_text=sdd_text, pol_ids=pol)
    chk("⑩ 登記了卻沒人用 → 黃(不是綠,也不是紅)", r10["state"] == "YELLOW" and any(
        x["rule"] == "V-XREF" and x["lamp"] == "YELLOW" for x in r10["rows"]))
    with tempfile.TemporaryDirectory() as td:
        r11 = check(books=books, sdd_text=sdd_text, pol_ids=pol, via=Path(td))
    chk("⑪ 冊不在 → ABSENT rc3(量不到不是通過)", r11["state"] == "ABSENT" and r11["rc"] == 3)
    report_after = report.read_bytes() if report.is_file() else None
    chk("⑫ 零足跡:真冊一個位元不動 · 自測不寫報告", (bp.read_bytes() if bp else b"") == real_bytes and report_after == report_before)
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
