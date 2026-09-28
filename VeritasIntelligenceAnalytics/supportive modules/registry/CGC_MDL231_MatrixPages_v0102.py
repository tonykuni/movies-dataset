#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL231_MatrixPages v0102 — 最後再加九頁:無所不編號(母系統 VIA → 子系統 → 類 → 分類 → 號,紅黃綠)

操作員 2026-09-28 R23:編號系統、SSOT · REGEX · 同義字(中英)、政策、金融市場代號(Ticker / YFinance / Bloomberg / Name /
English Name / Exchange / Instrument / Currency / Unit,容許空值)、總經與多來源(各取最新三值並排)、參數 · 邏輯 · 欄位、
函式庫與環境、模組與引擎、整測優化,全部放在 v0101 十二頁之後。資料讀 CGC_MDL237 寫好的編號冊(VIA_Numbering_SSOT +
VIA_NumberBooks),本頁不另量(L05);冊還沒寫就照實說「先經 VCGC 跑 CGC_MDL237 --apply」。
v0101 的 render 照舊產頁,本版只把九頁接到導覽列與內文最後(不改前十二頁一個字)。每頁有篩選框(純本頁 JS,零外連)。
CLS / FNC 八萬多列不上頁(頁會太大),上頁的是每個子系統 × 類的計數與每支模組的定義數;逐列在 JSONL 冊。
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

import html as _html
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "CGC_MDL231_MatrixPages"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_PRIOR = _load(PRIOR, STEM + "_prior_for_" + Path(__file__).stem)
_BASE = _PRIOR._PRIOR                                  # v0100 module: its main() calls the module-level render
ENGINE_TAG = f"{STEM} v{_vnum(Path(__file__)):04d}"
NEW_TABS = ("編號系統", "SSOT·REGEX·同義字", "政策", "金融市場代號", "總經與多源", "參數·邏輯·欄位", "函式庫與環境", "模組與引擎",
            "整測優化")
TABS = tuple(_PRIOR.TABS) + NEW_TABS
LAMP_ZH = {"GREEN": "綠", "AMBER": "黃", "RED": "紅"}
ORDER = {"RED": 0, "AMBER": 1, "GREEN": 2}
_CSS2 = """
.nb{margin:0 0 14px}.nb h3{font-size:12px;margin:8px 0 4px}.nb p{font-size:11px;margin:2px 0 6px;opacity:.85}
.nb table{border-collapse:collapse;font-size:10.5px;width:100%}.nb th,.nb td{border:1px solid var(--line);padding:2px 4px;vertical-align:top;text-align:left}
.nb th{position:sticky;top:0;background:var(--card)}.nb td.c{font-family:ui-monospace,Consolas,monospace;white-space:nowrap}
.nb .l{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:3px}.nb .GREEN{background:#2da44e}
.nb .AMBER{background:#d4a72c}.nb .RED{background:#cf222e}.nb input.flt{font-size:11px;padding:2px 6px;margin:0 0 6px;width:260px;max-width:100%}
.nb .wrap{max-height:70vh;overflow:auto}.nb .x3 td{white-space:nowrap}
"""
_JS2 = """
(function(){[].slice.call(document.querySelectorAll('input.flt')).forEach(function(inp){inp.addEventListener('input',function(){
 var q=inp.value.toLowerCase(),t=document.getElementById(inp.getAttribute('data-t'));if(!t)return;
 [].slice.call(t.tBodies[0].rows).forEach(function(r){r.style.display=(!q||r.textContent.toLowerCase().indexOf(q)>=0)?'':'none';});});});})();
"""


def numbering() -> dict | None:
    p = max((q for q in HERE.glob("CGC_MDL237_NumberingSystem_v*.py") if _vnum(q) >= 0), key=_vnum, default=None)
    if p is None:
        return None
    mod = _load(p, "numbering_for_" + Path(__file__).stem)
    ssot = mod._json(mod._newest(HERE, "VIA_Numbering_SSOT_v*.json"))
    if not ssot:
        return {"absent": True, "engine": p.stem}
    st = mod.load_state()
    by_kind = {}
    for (kind, _), r in st["rows"].items():
        by_kind.setdefault(kind, []).append(r)
    for rows in by_kind.values():
        rows.sort(key=lambda r: r["code"])
    return {"ssot": ssot, "rows": by_kind, "engine": p.stem}


def _e(v) -> str:
    return _html.escape("" if v is None else str(v))


def _lamp(l) -> str:
    return f"<span class='l {_e(l)}'></span>{LAMP_ZH.get(l, _e(l))}"


def table(tid: str, title: str, heads: list, rows: list, note: str = "", cls: str = "") -> str:
    body = "".join("<tr>" + "".join(f"<td{' class=c' if i == 0 else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return (f"<div class='nb'><h3>{_e(title)}</h3>{('<p>' + note + '</p>') if note else ''}"
            f"<input class='flt' data-t='{tid}' placeholder='篩選(號碼 · 名稱 · 分類 · 燈…)'>"
            f"<div class='wrap'><table id='{tid}' class='{cls}'><thead><tr>{''.join('<th>' + _e(h) + '</th>' for h in heads)}</tr></thead>"
            f"<tbody>{body}</tbody></table></div></div>")


def _count(rows) -> str:
    c = {k: sum(1 for r in rows if r.get("lamp") == k) for k in LAMP_ZH}
    return f"綠 {c['GREEN']} · 黃 {c['AMBER']} · 紅 {c['RED']}"


def _base_rows(rows, extra=()):
    rows = sorted(rows, key=lambda r: (ORDER.get(r.get("lamp"), 3), r["code"]))
    return [[_e(r["code"]), _lamp(r.get("lamp")), _e(r.get("name")), _e(r.get("cat")), _e(r.get("cat_code")), _e(r.get("version")),
             _e(r.get("source")), _e(r.get("api")), _e(r.get("updated_at"))] + [f(r) for f in extra] + [_e(r.get("note"))] for r in rows]


BASE_HEADS = ["號碼", "燈", "名稱", "分類", "分類碼", "版本", "資料來源", "API 來源", "更新日期"]


def page_system(nb: dict) -> str:
    s, rows = nb["ssot"], nb["rows"]
    subs = s.get("subsystems") or []
    kinds = [k["kind"] for k in s.get("kinds") or []]
    head = (f"<div class='nb'><h3>號碼格式</h3><p>{_e(s.get('format'))}</p><p>{_e(s.get('rule'))}</p>"
            f"<p>母系統 {_e((s.get('mother') or {}).get('code'))} · {_e((s.get('mother') or {}).get('zh'))} · 建冊 {_e(s.get('built_at'))} · "
            f"引擎 {_e(s.get('engine'))}</p></div>")
    matrix = []
    for sb in subs:
        cnt = [sum(1 for r in rows.get(k, []) if r.get("sub") == sb["abbr"]) for k in kinds]
        matrix.append([_e(sb["no"]), _e(sb["abbr"]), _e(sb["zh"])] + [str(c) if c else "" for c in cnt] + [str(sum(cnt))])
    kind_rows = [[_e(k["no"]), _e(k["kind"]), _e(k["zh"]), str(len(rows.get(k["kind"], []))), _count(rows.get(k["kind"], [])),
                  str(len((s.get("categories") or {}).get(k["kind"]) or {}))] for k in s.get("kinds") or []]
    cats = []
    for k, cmap in (s.get("categories") or {}).items():
        if k in ("CLS", "FNC"):
            continue
        per = {}
        for r in rows.get(k, []):
            per[r.get("cat")] = per.get(r.get("cat"), 0) + 1
        cats += [[_e(code), _e(k), _e(name), str(per.get(name, 0))] for name, code in cmap.items()]
    red = [r for k in kinds for r in rows.get(k, []) if r.get("lamp") == "RED"]
    return (head + table("nb_mx", "子系統 × 類(列數)", ["子系統號", "子系統", "說明"] + kinds + ["合計"], matrix, cls="x3")
            + table("nb_kind", "類 · 燈 · 分類數", ["類號", "類", "中文", "列數", "燈", "分類數"], kind_rows)
            + table("nb_red", f"紅燈全列 · {len(red)}", BASE_HEADS + ["說明"], _base_rows(red))
            + table("nb_cat", "分類碼(CLS / FNC 的分類 = 所屬模組,見「模組與引擎」)", ["分類碼", "類", "分類", "列數"], cats))


def _bi(r):
    return _e(r.get("name_zh"))


def _en(r):
    return _e(r.get("name_en"))


def page_ssot(nb):
    out = []
    for k, zh in (("SSOT", "SSOT 冊"), ("RGX", "正規式 REGEX"), ("SYN", "同義字")):
        rows = nb["rows"].get(k, [])
        miss = sum(1 for r in rows if r.get("lang"))
        out.append(table("nb_" + k, f"{zh} · {len(rows)} · {_count(rows)} · 中英缺 {miss}",
                         BASE_HEADS + ["中文名", "English"] + (["同義詞"] if k == "SYN" else []) + ["說明"],
                         _base_rows(rows, (_bi, _en) + ((lambda r: _e(" ≡ ".join(r.get("words") or [])),) if k == "SYN" else ())),
                         "三類整列寫進 VIA_Numbering_SSOT(編入 SSOT)。中英缺一 = 黃;同一詞在同一範圍指向兩個長鍵 = 紅(待裁定 key_alias)。"))
    return "".join(out)


def page_policy(nb):
    rows = nb["rows"].get("PLCY", [])
    return table("nb_plcy", f"政策 · {len(rows)} · {_count(rows)}", BASE_HEADS + ["說明"], _base_rows(rows),
                 "法條 · 教訓 · 每一本政策 / 法冊 / 合規 / 憲章 / 提示詞 / 閘門冊 · 冊內每一條規則 · 遺漏偵測(被引用卻不在法冊 = 紅,"
                 "補法條要操作員批准)。")


FM_HEADS = ["號碼", "燈", "Ticker", "YFinance Ticker", "Bloomberg Ticker", "Name", "English Name", "Exchange", "Instrument",
            "Currency", "Unit", "分類", "資料來源", "API 來源", "更新日期", "說明"]


def page_fm(nb):
    rows = sorted(nb["rows"].get("FM", []), key=lambda r: r["code"])
    body = []
    for r in rows:
        c = r.get("cols") or {}
        body.append([_e(r["code"]), _lamp(r.get("lamp"))] + [_e(c.get(k)) if c.get(k) not in (None, "") else "<i>—</i>"
                                                            for k in ("ticker", "yfinance", "bloomberg", "name", "name_en",
                                                                      "exchange", "instrument", "currency", "unit")]
                    + [_e(r.get("cat")), _e(r.get("source")), _e(r.get("api")), _e(r.get("updated_at")), _e(r.get("note"))])
    notes = " · ".join((nb["ssot"].get("notes") or {}).get("ins") or [])
    return table("nb_fm", f"金融市場代號 FM-<地區>-<類別>-四碼 · {len(rows)} · {_count(rows)}", FM_HEADS, body,
                 "空值容許存在(— = 本來源沒有)。台股全部與主動式 ETF 全部由 VDF_ENG087 尾版的庫表給;本機沒有庫時照實只列已提交的名冊。"
                 + (" 清單狀態:" + _e(notes) if notes else ""))


def page_macro(nb):
    xs = nb["rows"].get("XSRC", [])
    cards = []
    for r in xs:
        lanes = r.get("lanes") or []
        head = "".join(f"<th>{_e(l.get('source'))}<br><small>{_e(l.get('api'))}</small></th>" for l in lanes)
        depth = max((len(l.get("latest3") or []) for l in lanes), default=0)
        body = ""
        for i in range(depth):
            cells = []
            for l in lanes:
                lst = l.get("latest3") or []
                v = lst[len(lst) - 1 - i] if i < len(lst) else None          # newest first; a short lane shows — below
                cells.append(f"<td>{_e(v[0])} · <b>{_e(v[1])}</b></td>" if v else "<td>—</td>")
            body += f"<tr><td class=c>最新{'一二三'[i]}</td>{''.join(cells)}</tr>"
        pairs = " · ".join(f"{_e(p.get('pair'))} {_e(p.get('state'))}{(' @' + _e(p.get('date'))) if p.get('date') else ''}"
                           for p in r.get("pairs") or [])
        cards.append(f"<div class='nb'><h3>{_e(r['code'])} · {_lamp(r.get('lamp'))} · {_e(r.get('name'))} · {_e(r.get('note'))}</h3>"
                     f"<p>{pairs or '只有一個來源或沒有資料'}</p><div class='wrap'><table><thead><tr><th></th>{head}</tr></thead>"
                     f"<tbody>{body}</tbody></table></div></div>")
    mrc = nb["rows"].get("MRC", [])
    return ("<div class='nb'><p>同一數據多來源:各取最新三值並排;取最近的共同日期比,容差內 = 一致(綠)、容差外 = 不一致(紅)、"
            "沒有共同日期或只有一個來源 = 黃。一致的那組代號互為同義字(見同義字頁)。</p></div>" + "".join(cards)
            + table("nb_mrc", f"總體經濟 MRC-<地區>-四碼 · {len(mrc)} · {_count(mrc)}", BASE_HEADS + ["頻率", "單位", "FRED id", "說明"],
                    _base_rows(mrc, (lambda r: _e(r.get("freq")), lambda r: _e(r.get("unit")), lambda r: _e(r.get("fred_id"))))))


def page_params(nb):
    out = []
    for k, zh in (("PRMT", "參數"), ("LGC", "邏輯"), ("FD", "財務數據欄位"), ("BI", "基本資料欄位"), ("IDX", "指數與資料表"),
                  ("TOOL", "工具")):
        rows = nb["rows"].get(k, [])
        out.append(table("nb_" + k, f"{zh} {k} · {len(rows)} · {_count(rows)}", BASE_HEADS + ["說明"], _base_rows(rows)))
    return "".join(out)


def page_lib(nb):
    out = []
    for k, zh in (("LIB", "函式庫(尾數四碼)"), ("ENV", "環境變數 · 布建步驟 · 套件清單 · 工具鎖")):
        rows = nb["rows"].get(k, [])
        out.append(table("nb_" + k, f"{zh} · {len(rows)} · {_count(rows)}", BASE_HEADS + ["使用檔數", "說明"],
                         _base_rows(rows, (lambda r: _e(r.get("users")),))))
    return "".join(out)


def page_modules(nb):
    rows = nb["rows"].get("MDL", []) + nb["rows"].get("ENG", [])
    defs = {}
    for k in ("CLS", "FNC"):
        for r in nb["rows"].get(k, []):
            m = re.match(r"^(VIA-[A-Z0-9]+-(?:MDL|ENG)\d+)", r["code"])
            if m:
                defs.setdefault(m.group(1), {"CLS": 0, "FNC": 0})[k] += 1
    return table("nb_mdl", f"模組 · 引擎 · {len(rows)} · {_count(rows)} · 類別 {len(nb['rows'].get('CLS', []))} · "
                           f"函式 {len(nb['rows'].get('FNC', []))}",
                 BASE_HEADS + ["類別數", "函式數", "說明"],
                 _base_rows(rows, (lambda r: str(defs.get(r["code"], {}).get("CLS", 0)),
                                   lambda r: str(defs.get(r["code"], {}).get("FNC", 0)))),
                 "類別號 = 模組號-CLS###,函式號 = 模組號(-CLS###)-FNC###;逐列在 VIA_NumberBooks/VIA_NumberBook_{CLS,FNC}_<子系統>_v*.jsonl。")


def page_opt(nb):
    rows = nb["rows"].get("OPT", [])
    return table("nb_opt", f"整測優化紀錄(回合 · 掉球 · 批次)· {len(rows)} · {_count(rows)}", BASE_HEADS + ["說明"], _base_rows(rows))


PAGES = {"編號系統": page_system, "SSOT·REGEX·同義字": page_ssot, "政策": page_policy, "金融市場代號": page_fm,
         "總經與多源": page_macro, "參數·邏輯·欄位": page_params, "函式庫與環境": page_lib, "模組與引擎": page_modules,
         "整測優化": page_opt}


def extra_tabs(nb: dict | None) -> list:
    """[(tab name, count, html)] for the nine tabs, in NEW_TABS order."""
    if nb is None or nb.get("absent"):
        why = ("CGC_MDL237 尾版不在" if nb is None else "編號冊還沒寫:經 VCGC 跑 " + nb["engine"] + " --apply")
        return [(t, 0, f"<div class='nb'><p>{_e(why)}</p></div>") for t in NEW_TABS]
    counts = {"編號系統": sum(len(v) for v in nb["rows"].values()),
              "SSOT·REGEX·同義字": sum(len(nb["rows"].get(k, [])) for k in ("SSOT", "RGX", "SYN")),
              "政策": len(nb["rows"].get("PLCY", [])), "金融市場代號": len(nb["rows"].get("FM", [])),
              "總經與多源": len(nb["rows"].get("MRC", [])) + len(nb["rows"].get("XSRC", [])),
              "參數·邏輯·欄位": sum(len(nb["rows"].get(k, [])) for k in ("PRMT", "LGC", "FD", "BI", "IDX", "TOOL")),
              "函式庫與環境": len(nb["rows"].get("LIB", [])) + len(nb["rows"].get("ENV", [])),
              "模組與引擎": len(nb["rows"].get("MDL", [])) + len(nb["rows"].get("ENG", [])), "整測優化": len(nb["rows"].get("OPT", []))}
    return [(t, counts[t], PAGES[t](nb)) for t in NEW_TABS]


def inject(doc: str, tabs: list) -> str:
    nav = "".join(f"<button role='tab' aria-selected='false'>{_e(t)}<span class='n'>{n}</span></button>" for t, n, _ in tabs)
    panels = "".join(f"<section role='tabpanel' aria-label='{_e(t)}'>{frag}</section>" for t, _, frag in tabs)
    doc = doc.replace("</nav>", nav + "</nav>", 1).replace("</main>", panels + "</main>", 1)
    doc = doc.replace("</style>", _CSS2 + "</style>", 1)
    # the base script binds the tab buttons it finds, so the new buttons exist before it runs; the filter script goes last
    doc = doc.replace("</body>", f"<script>{_JS2}</script></body>", 1)
    return doc.replace(f"{_PRIOR.ENGINE_TAG} ·", f"{ENGINE_TAG} ·", 1)


_V0101_RENDER = _PRIOR.render


def render(width: int = 150, out: Path = None, side_path: Path = None, runall_path: Path = None, rep: dict | None = None,
           nb: dict | None = None) -> dict:
    res = _V0101_RENDER(width=width, out=out, side_path=side_path, runall_path=runall_path, rep=rep)
    tabs = extra_tabs(nb if nb is not None else numbering())
    path = Path(res["path"])
    path.write_text(inject(path.read_text(encoding="utf-8"), tabs), encoding="utf-8")
    res["tabs"].update({t: n for t, n, _ in tabs})
    res["engine_tag"] = ENGINE_TAG
    res["numbering"] = sum(n for t, n, _ in tabs if t == "編號系統")
    return res


_BASE.render = render                                   # v0100 main() → this render (v0101's own name stays its own)


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def main(argv=None) -> int:
    return _PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    rc = _PRIOR.selftest()                              # v0101 points v0100 back at its render when done; take ours back
    _BASE.render = render
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    fm = {"code": "VIA-VDF-FM-US-EQT-0001", "lamp": "GREEN", "cat": "股票", "source": "f", "api": "yfinance", "updated_at": "t",
          "cols": {"ticker": "NVDA", "yfinance": "NVDA", "bloomberg": None, "name": "輝達", "name_en": "NVIDIA", "exchange": "NASDAQ",
                   "instrument": "Equity", "currency": "USD", "unit": "USD/股"}}
    xs = {"code": "VIA-VDF-XSRC001", "lamp": "GREEN", "name": "美國10年期公債殖利率", "note": "AGREE",
          "lanes": [{"source": "FRED DGS10", "api": "FRED", "latest3": [["d1", 4.4], ["d2", 4.45], ["d3", 4.48]]},
                    {"source": "yfinance ^TNX", "api": "yf", "latest3": [["d2", 4.46], ["d3", 4.49]]}],
          "pairs": [{"pair": "FRED DGS10 × yfinance ^TNX", "state": "AGREE", "date": "d3"}]}
    syn = {"code": "VIA-VCGC-SYN001", "lamp": "AMBER", "name": "X", "words": ["X"], "name_zh": "", "name_en": "X", "lang": "缺中文"}
    nb = {"ssot": {"format": "f", "rule": "r", "mother": {"code": "VIA"}, "subsystems": [{"no": "VIA-02", "abbr": "VDF", "zh": "z"}],
                   "kinds": [{"no": "K13", "kind": "FM", "zh": "金融市場商品"}], "categories": {"FM": {"股票": "FM-C001"}}},
          "rows": {"FM": [fm], "XSRC": [xs], "SYN": [syn], "MRC": [], "PLCY": []}, "engine": "e"}
    with tempfile.TemporaryDirectory() as td:
        rep = {"sections": [("① 總覽", ["燈"], [["GREEN"]], 0)], "verdict": "GREEN", "ts": "t", "head": "h"}
        res = render(out=Path(td), rep=rep, nb=nb)
        page = Path(res["path"]).read_text(encoding="utf-8")
        res2 = render(out=Path(td), rep=rep, nb={"absent": True, "engine": "CGC_MDL237_NumberingSystem_v0100"})
        page2 = Path(res2["path"]).read_text(encoding="utf-8")
    chk("⑰ 二十一頁:v0101 十二頁照舊 + 九頁在最後", list(res["tabs"])[-9:] == list(NEW_TABS) and len(res["tabs"]) == 21 and
        page.count("role='tabpanel'") == 21)
    chk("⑱ 金融市場九欄齊、空值照列(—)", all(h in page for h in FM_HEADS[2:11]) and "VIA-VDF-FM-US-EQT-0001" in page and "<i>—</i>" in page)
    row3 = re.search(r"最新三</td>(.*?)</tr>", page)
    chk("⑲ 多來源各取最新三值並排(短的來源下面是 —,不重複)+ 對照結論", "最新一" in page and "AGREE" in page and
        "FRED DGS10 × yfinance ^TNX" in page and row3 and "d1" in row3.group(1) and "<td>—</td>" in row3.group(1))
    chk("⑳ SSOT·REGEX·同義字 有中文名 / English 欄,缺一照實列", "中文名" in page and "English" in page and "中英缺 1" in page)
    chk("㉑ 冊沒寫就照實說(不假綠)", "--apply" in page2 and page2.count("role='tabpanel'") == 21)
    chk("㉒ 零外連 · 篩選框在", not re.search(r"(src|href)=['\"]https?://", page) and "input.flt" in page)
    ok = rc == 0 and all(results)
    print(f"  {ENGINE_TAG} selftest +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
