#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG046_FetchMatrixRegistry v0101 — 薄尾:VDF-390 擷取矩陣「編號 · 勾選」簡化頁(select)

操作員 2026-11-14:「先把 VDF 要擷取的資料矩陣畫編號」「所有項目分大類可都抓可單獨選 · 唯有國際個股及兩檔 3017 3324
這兩張股票取財報資訊 · 其他各類可新增或可不勾選 · 同群可改起始時間 · 簡化」。
v0100(轉錄引擎 + 本體)一字不動;本版只多一個動詞:
  select [--out 夾] [--json]   讀 VDF_FetchOne_Matrix_Registry(390 項 · 17 大類;碼 = 冊上編號 PX-01 …)與擷取族群冊尾版,
                               畫一頁:大類可全選 / 單項勾選 · 每列帶碼 · 狀態 · 推定族群;
                               起始日照族群冊 start_rule 按大類改(TW_MARKET / FIN / MACRO / OTHER);
                               財報範圍照成員帳本:國內選定股財報 TW_FIN(目前 3017 · 3324)· 國際股財報 INTL_FIN;
                               頁上「產生擷取指令」= VDF 自己的 MDL012 指令(start / add / remove / run --groups),不在頁上直接抓。
                               寫 <out>/VDF_FETCH_SELECT_latest.html 與 .json(預設 out = VIA_Reports/vdf)。
誠實界線:碼 → 族群是依碼 / 區段的推定對映(頁上標「推定」);VDF 推導項不另抓(由上游資料算);
  對不到族群的宣告項照列「尚無族群可跑」,勾了也不會抓;TODO 項照列 TODO。中央號(VIA-VDF-…)未發,頁上不冒充。
只讀:不改冊、不寫帳本(增減成員要操作員照頁上指令經 MDL012 --apply);零網路;不碰 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import html as _html
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
_STEM = "VDF_ENG046_FetchMatrixRegistry"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0100(轉接件 → 無版號本體)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


REGISTRY = VDF / "VDF_FetchOne_Matrix_Registry_v0100.json"
LEDGER = VDF / "VDF_FetchGroups_MemberLedger_v0100.jsonl"
OUT_DIR = VIA / "VIA_Reports" / "vdf"
# 碼 → 擷取族群(推定對映;依碼與區段,先中先贏)。VDF 推導項另判,不進族群。
GROUP_RULES = (
    ("TW_PRICE_VOL", r"^(PX-0[12]|MX-A[12])$"),
    ("TW_INDEX", r"^(PX-04C|PX-06F|MX-A3)$"),
    ("TW_CHIP", r"^(FQ-0[1246]|SE-05)$"),
    ("TW_MONTHLY_REV", r"^FN-06[AB]?$"),
    ("TW_ACTIVE_ETF", r"^(EF-01[A-X]?|EF-4[0-3][A-G]?|MX-A12|MX-D1)$"),
    ("TW_FIN", r"^FN-(0[0-57-9]|10)[A-D]?$"),
    ("INTL_FIN", r"^AI-12$"),
    ("INTL_DAILY", r"^(PX-0[3-6][A-P]?|PX-07[AD]|PX-08[AD]|AI-0[0-5]|MX-A[4569]|MX-C[12]|FX-0[12])$"),
    ("CN_NBS", r"^GL-(14|25|33)$"),
    ("CN_MACRO", r"^GL-(04|04[CD]|15)$"),
    ("SHIPPING", r"^CM-0[78]$"),
    ("GLOBAL_MACRO", r"^GL-(0[1-35-9]|1[0-36-9]|2[0-46-9]|3[0-2457])$"),
    ("US_MACRO", r"^(US-[LCG]\d{2}|FD-0\d|FI-0\d|FX-0[3-7]|MX-B[1-4])$"),
    ("SENTIMENT", r"^(SE-(0[1-4]|0[67]|1[01])|MX-B5)$"),
)


def _latest(glob: str):
    hits = sorted(VDF.glob(glob), key=_vnum_v0101)
    return hits[-1] if hits else None


def is_derived(it: dict) -> bool:
    return it.get("fetcher") == "vdf_fetchers_derived" or str(it.get("source", "")).startswith(("VDF 推導", "VDF 品質閘門"))


def group_of(it: dict) -> str:
    if is_derived(it):
        return ""
    for g, rx in GROUP_RULES:
        if re.match(rx, it.get("id", "")):
            return g
    return ""


def members(book: dict, ledger: Path = LEDGER) -> dict:
    """可增減族群的有效名單(預設 + add − remove,後寫者勝;同 MDL012 規則,只讀)。"""
    rows = []
    if ledger.is_file():
        for ln in ledger.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(ln))
            except ValueError:
                rows.append({"kind": "bad"})
    out = {}
    for g in book.get("groups") or []:
        if g.get("membership") != "EDITABLE_DEFAULT":
            continue
        cur = [str(x) for x in g.get("default_members") or []]
        for r in rows:
            if r.get("kind") == "member" and r.get("group") == g["id"]:
                v = str(r.get("value"))
                if r.get("op") == "add" and v not in cur:
                    cur.append(v)
                elif r.get("op") == "remove" and v in cur:
                    cur.remove(v)
        out[g["id"]] = cur
    return out


def build(reg_path: Path = REGISTRY, ledger: Path = LEDGER) -> dict:
    reg = json.loads(Path(reg_path).read_text(encoding="utf-8"))
    gb_path = _latest("VDF_FetchGroups_SSOT_v*.json")
    book = json.loads(gb_path.read_text(encoding="utf-8")) if gb_path else {"groups": [], "categories": []}
    g_zh = {g["id"]: g.get("zh", g["id"]) for g in book.get("groups") or []}
    g_cat = {gid: c["id"] for c in book.get("categories") or [] for gid in c.get("groups") or []}
    items = []
    for it in reg.get("items") or []:
        g = group_of(it)
        items.append({"id": it.get("id", ""), "section": it.get("section", ""), "name": it.get("name", ""), "source": it.get("source", ""),
                      "freq": it.get("freq", ""), "fields": it.get("fields", ""), "status": it.get("status", ""), "derived": is_derived(it),
                      "group": g, "group_zh": g_zh.get(g, ""), "category": g_cat.get(g, "")})
    sections = []
    for it in items:
        if not sections or sections[-1]["name"] != it["section"]:
            sections.append({"name": it["section"], "ids": []})
        sections[-1]["ids"].append(it["id"])
    mdl012 = _latest("VDF_MDL012_FetchGroups_v*.py")
    return {"tag": TAG, "registry": Path(reg_path).name, "groups_book": gb_path.name if gb_path else "", "mdl012": mdl012.name if mdl012 else "",
            "categories": [{"id": c["id"], "zh": c.get("zh", ""), "default_start": c.get("default_start", ""), "groups": c.get("groups") or []}
                           for c in book.get("categories") or []],
            "editable": [g["id"] for g in book.get("groups") or [] if str(g.get("membership", "")).startswith("EDITABLE")],
            "members": members(book, ledger), "sections": sections, "items": items,
            "counts": {"items": len(items), "sections": len(sections), "mapped": sum(1 for i in items if i["group"]),
                       "derived": sum(1 for i in items if i["derived"]), "unmapped": sum(1 for i in items if not i["group"] and not i["derived"])}}


def _tokens() -> dict:
    p = _latest("VDF_UI_VisualSpec_SSOT_v*.json")
    try:
        return (json.loads(p.read_text(encoding="utf-8")).get("tokens") or {}) if p else {}
    except (OSError, ValueError):
        return {}


def render(m: dict) -> str:
    t = {"bg": "#f8f7f2", "text": "#26312f", "panel": "#f1f3ec", "card": "#fffefb", "card_border": "#dedfd5", "th_bg": "#eeeee7",
         "row_border": "#e1e4dc", "font": "Inter,'Segoe UI','Noto Sans CJK TC','Microsoft JhengHei',sans-serif"}
    t.update({k: v for k, v in _tokens().items() if k in t})
    e = _html.escape
    by_id = {i["id"]: i for i in m["items"]}
    secs = []
    for s in m["sections"]:
        rows = []
        for cid in s["ids"]:
            it = by_id[cid]
            st = it["status"]
            lamp = "g" if st == "DONE" else ("y" if st == "PROXY" else "r")
            grp = ("推導 · 不另抓" if it["derived"] else (f"{e(it['group_zh'])} <span class='mut'>{e(it['group'])}</span>" if it["group"] else "<span class='warn'>尚無族群可跑</span>"))
            scope = ""
            if it["group"] == "TW_FIN":
                scope = " <span class='tag'>只抓 " + e(" · ".join(m["members"].get("TW_FIN", []))) + "</span>"
            elif it["group"] == "INTL_FIN":
                scope = " <span class='tag'>國際股 " + e(" · ".join(m["members"].get("INTL_FIN", []))) + "</span>"
            rows.append(f"<tr data-id='{e(cid)}' data-g='{e(it['group'])}' data-d='{1 if it['derived'] else 0}' data-st='{e(st)}'>"
                        f"<td><input type='checkbox' class='it' value='{e(cid)}'></td><td class='code'>{e(cid)}</td>"
                        f"<td title='{e(it['fields'])}'>{e(it['name'])}{scope}</td><td>{e(it['source'])}</td><td>{e(it['freq'])}</td>"
                        f"<td><span class='dot {lamp}'></span>{e(st)}</td><td>{grp}</td></tr>")
        secs.append(f"<details open class='sec'><summary><input type='checkbox' class='all-sec'> <b>{e(s['name'])}</b> "
                    f"<span class='mut cnt'>0/{len(s['ids'])}</span></summary><table><thead><tr><th></th><th>碼</th><th>資料項</th><th>來源</th>"
                    f"<th>頻率</th><th>狀態</th><th>族群(推定)</th></tr></thead><tbody>{''.join(rows)}</tbody></table></details>")
    cats = "".join(f"<label class='cat'>{e(c['zh'])}<input type='date' class='start' data-cat='{e(c['id'])}' data-def='{e(c['default_start'])}' value='{e(c['default_start'])}'></label>"
                   for c in m["categories"])
    edit = "".join(f"<option value='{e(g)}'>{e(g)}</option>" for g in m["editable"])
    c = m["counts"]
    css = (f":root{{--bg:{t['bg']};--fg:{t['text']};--panel:{t['panel']};--card:{t['card']};--line:{t['card_border']};--th:{t['th_bg']};--row:{t['row_border']}}}"
           "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:11px/1.5 " + t["font"] + "}"
           "main{max-width:1280px;margin:0 auto;padding:12px 16px}h1{font-size:17px;margin:2px 0}.mut{color:#6b746f}.warn{color:#b45309}"
           ".bar.top{position:sticky;top:0;z-index:2}.bar{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:8px 0;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center}"
           "button{font:inherit;padding:3px 9px;border:1px solid var(--line);border-radius:5px;background:var(--card);cursor:pointer}"
           ".cat{display:inline-flex;gap:4px;align-items:center}.cat input{font:inherit}"
           "details.sec{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:6px 0;padding:4px 8px}summary{cursor:pointer;padding:3px 0}"
           "table{width:100%;border-collapse:collapse;table-layout:auto}th,td{border-bottom:1px solid var(--row);padding:3px 6px;text-align:left;vertical-align:top;word-wrap:break-word;overflow-wrap:anywhere}"
           "th{background:var(--th);font-size:10.5px}.code{font-family:ui-monospace,Consolas,monospace;white-space:nowrap}"
           ".dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}.g{background:#16a34a}.y{background:#f59e0b}.r{background:#dc2626}"
           ".tag{font-size:10px;border:1px solid var(--line);border-radius:3px;padding:0 4px;margin-left:4px}"
           "textarea{width:100%;min-height:120px;font:11px ui-monospace,Consolas,monospace}#out{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px;margin:8px 0}")
    js = ("var M=" + json.dumps({"mdl012": m["mdl012"], "items": {i["id"]: {"g": i["group"], "c": i["category"], "d": i["derived"], "s": i["status"]} for i in m["items"]}},
                                ensure_ascii=False) + ";"
          "function $(q,r){return (r||document).querySelectorAll(q)}"
          "function cnt(){$('details.sec').forEach(function(d){var a=$('input.it',d),k=0;a.forEach(function(x){if(x.checked)k++});"
          "d.querySelector('.cnt').textContent=k+'/'+a.length;var m=d.querySelector('.all-sec');m.checked=k===a.length;m.indeterminate=k>0&&k<a.length});"
          "var n=0;$('input.it').forEach(function(x){if(x.checked)n++});document.getElementById('sel').textContent=n}"
          "function setAll(f){$('input.it').forEach(function(x){x.checked=f(x.closest('tr'))});cnt()}"
          "$('.all-sec').forEach(function(m){m.addEventListener('click',function(ev){ev.stopPropagation();var d=m.closest('details');"
          "$('input.it',d).forEach(function(x){x.checked=m.checked});cnt()})});"
          "$('input.it').forEach(function(x){x.addEventListener('change',cnt)});"
          "document.getElementById('b-all').onclick=function(){setAll(function(){return true})};"
          "document.getElementById('b-none').onclick=function(){setAll(function(){return false})};"
          "document.getElementById('b-done').onclick=function(){setAll(function(r){return r.dataset.st==='DONE'})};"
          "document.getElementById('b-run').onclick=function(){setAll(function(r){return !!r.dataset.g})};"
          "var edits=[];document.getElementById('b-edit').onclick=function(){var g=document.getElementById('eg').value,op=document.getElementById('eo').value,"
          "v=document.getElementById('ev').value.trim();if(!v)return;edits.push([op,g,v.split(/[\\s,]+/).join(' ')]);document.getElementById('ev').value='';gen()};"
          "function gen(){var sel=[],groups={},todo=[],un=[],der=[];$('input.it').forEach(function(x){if(!x.checked)return;var i=M.items[x.value];sel.push(x.value);"
          "if(i.d)der.push(x.value);else if(!i.g)un.push(x.value);else{groups[i.g]=1;if(i.s==='TODO')todo.push(x.value)}});"
          "var py='python3 \"functional modules/VDF/'+M.mdl012+'\"',L=[],starts={};"
          "$('input.start').forEach(function(s){starts[s.dataset.cat]=s.value;if(s.value&&s.value!==s.dataset.def)L.push(py+' start --category '+s.dataset.cat+' --set '+s.value+' --apply')});"
          "edits.forEach(function(e){L.push(py+' '+e[0]+' '+e[1]+' '+e[2]+' --apply')});"
          "var gs=Object.keys(groups);if(gs.length)L.push(py+' run --groups '+gs.join(','));"
          "var o={tag:'" + e(TAG) + "',selected:sel,groups:gs,starts:starts,member_edits:edits,derived_not_fetched:der,no_group_yet:un,todo:todo};"
          "document.getElementById('cmd').value=L.join('\\n')+'\\n';document.getElementById('js').value=JSON.stringify(o,null,1);"
          "document.getElementById('note').textContent='族群 '+gs.length+' · 推導不另抓 '+der.length+' · 尚無族群可跑 '+un.length+' · 其中 TODO '+todo.length}"
          "document.getElementById('b-gen').onclick=gen;"
          "document.getElementById('b-dl').onclick=function(){gen();var b=new Blob([document.getElementById('js').value],{type:'application/json'}),a=document.createElement('a');"
          "a.href=URL.createObjectURL(b);a.download='VDF_FETCH_SELECTION.json';a.click()};cnt();")
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>VDF 擷取矩陣 · 編號勾選</title><style>{css}</style></head><body><main>"
            f"<h1>VDF 擷取矩陣 · 編號 · 勾選</h1><div class='mut'>{e(m['tag'])} · 冊 {e(m['registry'])} · 族群冊 {e(m['groups_book'])} · "
            f"{c['items']} 項 · {c['sections']} 大類 · 有族群可跑 {c['mapped']} · 推導 {c['derived']} · 尚無族群 {c['unmapped']} · 碼 = 冊上編號(中央號未發)</div>"
            "<div class='bar top'><button id='b-all'>全選</button><button id='b-none'>全不選</button><button id='b-done'>只選已實作</button>"
            "<button id='b-run'>只選有族群可跑</button><span>已選 <b id='sel'>0</b></span><span class='mut'>起始日(按大類改):</span>" + cats + "</div>"
            "<div class='bar'><span>財報範圍:國內 <b>" + e(" · ".join(m["members"].get("TW_FIN", []))) + "</b> · 國際 <b>" + e(" · ".join(m["members"].get("INTL_FIN", [])))
            + "</b></span><span class='mut'>增減成員:</span><select id='eo'><option>add</option><option>remove</option></select><select id='eg'>" + edit
            + "</select><input id='ev' placeholder='代號,空白或逗號分隔'><button id='b-edit'>加入指令</button></div>"
            + "".join(secs)
            + "<div id='out'><button id='b-gen'>產生擷取指令</button> <button id='b-dl'>下載選擇 JSON</button> <span id='note' class='mut'></span>"
            "<p class='mut'>指令走 VDF 自己的 MDL012:先改起始日 / 成員(--apply 才寫帳本),再 run 選到的族群。頁上不直接抓資料。</p>"
            "<textarea id='cmd' readonly></textarea><textarea id='js' readonly></textarea></div>"
            f"</main><script>{js}</script></body></html>")


def select_main(args: list) -> int:
    out = Path(args[args.index("--out") + 1]) if "--out" in args and args.index("--out") + 1 < len(args) else OUT_DIR
    m = build()
    out.mkdir(parents=True, exist_ok=True)
    hp, jp = out / "VDF_FETCH_SELECT_latest.html", out / "VDF_FETCH_SELECT_latest.json"
    hp.write_text(render(m), encoding="utf-8")
    jp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    c = m["counts"]
    by = {}
    for i in m["items"]:
        k = i["group"] or ("推導" if i["derived"] else "尚無族群")
        by[k] = by.get(k, 0) + 1
    if "--json" in args:
        print(json.dumps({"counts": c, "by_group": by, "members": m["members"], "html": str(hp)}, ensure_ascii=False, indent=1))
    else:
        print(f"[擷取矩陣 · 編號勾選] {c['items']} 項 · {c['sections']} 大類 · 有族群可跑 {c['mapped']} · 推導 {c['derived']} · 尚無族群 {c['unmapped']}"
              f" · 財報 國內 {' · '.join(m['members'].get('TW_FIN', []))} / 國際 {' · '.join(m['members'].get('INTL_FIN', []))} · 頁 {hp}")
        print("  " + " · ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda t: -t[1])))
    return 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if a[:1] == ["select"]:
        return select_main(a[1:])
    body = PRIOR._load()
    sys.argv = [str(PRIOR_PATH)] + a
    return body.main() if hasattr(body, "main") else 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(擷取矩陣編號勾選頁)===", flush=True)
    g = lambda i, **kw: group_of(dict({"id": i, "fetcher": "vdf_fetchers_market", "source": "X"}, **kw))   # noqa: E731
    chk("① 推定對映:PX-01 台股量價 · PX-04C 台股指數 · FN-01 財報 → TW_FIN · FN-06 月營收 · EF-01A 主動 ETF · AI-12 國際財報 · "
        "US-L05 美國總經 · GL-14 NBS · CM-07 航運 · PX-04H 國際日線;推導項不進族群",
        g("PX-01") == "TW_PRICE_VOL" and g("PX-04C") == "TW_INDEX" and g("FN-01") == "TW_FIN" and g("FN-05D") == "TW_FIN"
        and g("FN-06") == "TW_MONTHLY_REV" and g("EF-01A") == "TW_ACTIVE_ETF" and g("AI-12") == "INTL_FIN" and g("US-L05") == "US_MACRO"
        and g("GL-14") == "CN_NBS" and g("CM-07") == "SHIPPING" and g("PX-04H") == "INTL_DAILY" and g("GL-01") == "GLOBAL_MACRO"
        and group_of({"id": "FN-04", "fetcher": "vdf_fetchers_derived", "source": "VDF 推導"}) == "")
    with tempfile.TemporaryDirectory(prefix="eng046_v0101_") as td:
        led = Path(td) / "ledger.jsonl"
        led.write_text("\n".join([json.dumps({"kind": "member", "group": "TW_FIN", "op": "add", "value": "3017"}),
                                  json.dumps({"kind": "member", "group": "TW_FIN", "op": "remove", "value": "2330"})]) + "\n", encoding="utf-8")
        m = build(REGISTRY, led)
        chk("② 財報範圍照成員帳本:TW_FIN = 預設 2330 · 3324 + add 3017 − remove 2330 → 3324 · 3017;INTL_FIN 照預設",
            set(m["members"].get("TW_FIN", [])) == {"3017", "3324"} and m["members"].get("INTL_FIN"), m["members"])
        c = m["counts"]
        chk("③ 390 項 · 17 大類全進頁;有族群 + 推導 + 尚無族群 = 390;四大類起始日照族群冊預設",
            c["items"] == 390 and c["sections"] == 17 and c["mapped"] + c["derived"] + c["unmapped"] == 390 and c["mapped"] > 150
            and {x["id"] for x in m["categories"]} >= {"TW_MARKET", "FIN", "MACRO", "OTHER"} and all(x["default_start"] for x in m["categories"]), c)
        page = render(m)
        chk("④ 頁:每項一個勾選框且帶碼 · 大類全選框 17 · 起始日四個 · 增減成員 · 產生 MDL012 指令 / 下載 JSON · 11px · 自動換行",
            page.count("class='it'") == 390 and page.count("class='all-sec'") == 17 and page.count("class='start'") == 4
            and "id='b-gen'" in page and "id='b-dl'" in page and m["mdl012"] in page and "font:11px" in page and "word-wrap:break-word" in page
            and "PX-01" in page and "FN-10" in page and "只抓 3324 · 3017" in page)
        out = Path(td) / "out"
        rc = select_main(["--out", str(out)])
        chk("⑤ select 寫 html + json 到指定夾(rc 0)", rc == 0 and (out / "VDF_FETCH_SELECT_latest.html").is_file()
            and json.loads((out / "VDF_FETCH_SELECT_latest.json").read_text(encoding="utf-8"))["counts"]["items"] == 390)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑥ 加速器橋 · 網路工具橋在;只讀(不寫冊 / 帳本,寫檔只在輸出夾兩處);零網路;不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and body.count(".write_text(") == 2 and "LEDGER.write" not in body
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and "requests" not in body and "urlopen" not in body)
    chk("⑦ 前版轉接仍可用(v0100 → 無版號本體的名字照轉)", hasattr(PRIOR, "_load") and callable(getattr(PRIOR._load(), "main", None)))
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
