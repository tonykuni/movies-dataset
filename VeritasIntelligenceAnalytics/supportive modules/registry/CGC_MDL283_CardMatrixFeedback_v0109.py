#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0109 — 薄尾(v0108 … v0100 一字不動):看一眼就知道先做什麼 · 整頁資料下載 MD

操作員 2026-11-21:「VCGC 多整合多彈性,全式卡片或矩陣會昏頭」「優化展現方式」「整頁資料可以用 MD 轉換下載」。
資料一列不少,只改擺法(現況頁 monitor status 與功能一覽 overview 都走這裡):
  ① 頁首只留:一句話判定 + 系統一排(每系統一張卡)。
  ② 新增「先做這幾件」:要處理的項目按原因歸組(同一個併組、或同系統同區塊同說明),依 退步 → 真紅 → 待裁 → … 排,
     前 10 個原因直接看,其餘收合;點原因看是哪幾項。項數合計 = 要處理的列數(對不上就不改頁面)。
  ③ 其餘卡片(依類別 · 依群組 · 功能分欄)與給動作主力的更新回饋,收進一個「全部卡片與更新回饋」摺疊區;點卡片照樣篩矩陣。
  ④ 矩陣指定欄寬(舊版沒指定,項目欄被擠成一字一行)。
  ⑤「下載 MD」按鈕:判定 · 先做這幾件 · 依系統 · 要處理的每一列 · 其餘每一列 · 給 AI 的回饋包,一個 .md 檔(靜態頁,不起伺服器)。
寬度規則在版面冊 VIA_UI_WorkPlatform_DashboardLayout 尾版(v0101 起),不帶顏色;本檔沒有任何顏色與尺寸。
頁面結構不如預期(找不到資料、判定條或矩陣)就原樣回並在頁首註明原因。唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
動詞與旗標同 v0108。
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
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0109"
VERSION = "v0109"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0108.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0108", HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0108"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0
for _m in (PRIOR, PRIOR.PRIOR, PRIOR.V6, PRIOR.V5, PRIOR.V5.PRIOR, PRIOR.V3, PRIOR.V3.PRIOR, PRIOR.V3.P1, P0):
    if hasattr(_m, "ENGINE"):
        _m.ENGINE = ENGINE
for _m in (PRIOR, PRIOR.PRIOR, PRIOR.V6, PRIOR.V5):
    if hasattr(_m, "VERSION"):
        _m.VERSION = VERSION
PRIOR.V3.MANIFEST["engine"] = ENGINE
_O = {"render": P0.render}          # 此刻指到 v0108 的包裝
CTX = {"via": None}                 # 自測用;平常自己找 VIA 夾
ZH = {"r": "紅", "y": "黃", "g": "綠", "x": "灰"}
RANK = {"r": 0, "y": 1, "x": 2, "g": 3}
ORDER = [c[1] for c in P0.CLASSES]
TOP = 10                            # 先做這幾件:直接看的原因數
PER = 40                            # 每個原因點開最多列幾項(其餘看矩陣)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
MARK = "/* v0101 · 先做這幾件"       # 版面冊 v0101 起才有的規則
MX_OPEN = '<section class="card" id="mx">'
COLS = ("m-l", "m-s", "m-b", "m-i", "m-v", "", "m-t", "m-c", "m-d")   # 燈 系統 區塊 項目 版本 狀態說明 時間 類別 去向


def E(s) -> str:
    return _html.escape(str(s), quote=True)


def text(frag: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", frag))).strip()


class _Top(HTMLParser):
    """找出 .wrap 底下第一層的每一塊(起訖字元位置)。"""

    def __init__(self, src):
        super().__init__(convert_charrefs=True)
        self.src, self.depth, self.wrap, self.blocks, self.cur = src, 0, None, [], None
        self.lines = [0]
        for m in re.finditer("\n", src):
            self.lines.append(m.end())

    def _off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.depth += 1
        cls = dict(attrs).get("class") or ""
        if self.wrap is None and tag == "div" and "wrap" in cls.split():
            self.wrap = self.depth
        elif self.wrap is not None and self.depth == self.wrap + 1:
            self.cur = [tag, cls, self._off(), None]

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.wrap is not None and self.depth == self.wrap + 1 and self.cur and self.cur[0] == tag:
            off = self._off()
            self.cur[3] = self.src.index(">", off) + 1
            self.blocks.append(tuple(self.cur))
            self.cur = None
        if self.wrap is not None and self.depth == self.wrap:
            self.wrap = -1          # .wrap 結束後不再收
        self.depth -= 1


def top_blocks(src: str) -> list:
    p = _Top(src)
    p.feed(src)
    p.close()
    return [(t, c, s, e, src[s:e]) for t, c, s, e in p.blocks if e]


def balanced(src: str) -> bool:
    class B(HTMLParser):
        def __init__(self):
            super().__init__()
            self.st, self.bad = [], 0

        def handle_starttag(self, tag, attrs):
            if tag not in VOID:
                self.st.append(tag)

        def handle_endtag(self, tag):
            if tag in VOID:
                return
            if self.st and self.st[-1] == tag:
                self.st.pop()
            else:
                self.bad += 1
    b = B()
    b.feed(src)
    return not b.bad and not b.st


def rows_of(src: str):
    m = re.search(r'<script type="application/json" id="d">(.*?)</script>', src, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def causes(rows: list):
    """要處理的列按原因歸組。回 (要處理的列, 原因清單)。"""
    sel = [r for r in rows if len(r) > 11 and r[11]]
    groups = {}
    for r in sel:
        cls = str(r[7]).split("+")[0]
        disp = str(r[8])
        key = (cls, disp) if disp.startswith("併組:") else (cls, r[1], r[2], re.sub(r"\d+", "#", str(r[5])))
        groups.setdefault(key, []).append(r)
    out = []
    for key, rs in groups.items():
        systems = sorted({str(r[1]) for r in rs})
        secs = sorted({str(r[2]) for r in rs})
        out.append({"cls": key[0], "lamp": min((r[0] for r in rs), key=lambda l: RANK.get(l, 9)), "n": len(rs),
                    "sys": "、".join(systems[:4]) + (" 等 %d 個" % len(systems) if len(systems) > 4 else ""),
                    "sec": "、".join(secs[:2]) + (" 等 %d 區" % len(secs) if len(secs) > 2 else ""),
                    "why": str(rs[0][5]) or "(沒有說明)", "rows": rs})
    out.sort(key=lambda c: (ORDER.index(c["cls"]) if c["cls"] in ORDER else 99, -c["n"], c["sys"], c["sec"]))
    return sel, out


def _cause_rows(cs: list, start: int) -> str:
    h = []
    for i, c in enumerate(cs, start):
        items = []
        for r in c["rows"][:PER]:
            extra = (" — " + E(r[5])) if str(r[5]) and str(r[5]) != c["why"] else ""
            items.append("<li>%s%s%s</li>" % (E(r[3]), (" · " + E(r[4])) if r[4] else "", extra))
        if c["n"] > PER:
            items.append("<li>其餘 %d 項在下面矩陣(類別選「%s」)</li>" % (c["n"] - PER, E(c["cls"])))
        h.append('<tr><td class="l"><span class="lamp %s">%s</span></td><td class="n">%s</td><td class="num n">%d</td><td>%s · %s</td>'
                 '<td><details><summary>%d. %s</summary><ul>%s</ul></details></td></tr>'
                 % (c["lamp"], ZH.get(c["lamp"], "灰"), E(c["cls"]), c["n"], E(c["sys"]), E(c["sec"]), i, E(c["why"]), "".join(items)))
    return "".join(h)


def _table(body: str) -> str:
    return ('<div class="scroll"><table><colgroup><col class="f-l"><col class="f-c"><col class="f-n"><col class="f-s"><col></colgroup>'
            '<thead><tr><th class="l">燈</th><th>類別</th><th>項數</th><th>系統 · 區塊</th><th>原因(點開看是哪幾項)</th></tr></thead><tbody>'
            + body + "</tbody></table></div>")


def focus_html(sel: list, cs: list, fname: str) -> str:
    head = ('<section class="card focus" id="fx"><h2>先做這幾件<span class="note"> · 要處理 %d 項,歸成 %d 個原因;由上往下做</span></h2>'
            '<div class="bar note"><span>同一個原因修一次,底下幾項通常一起好。卡片與明細在下面,平常不用打開。</span>'
            '<button type="button" id="mdl" data-name="%s">下載 MD(整頁資料)</button></div>') % (len(sel), len(cs), E(fname))
    if not cs:
        return head + '<div class="note"><span class="lamp g">綠</span> 這一輪沒有要處理的項目。</div></section>'
    h = head + _table(_cause_rows(cs[:TOP], 1))
    if len(cs) > TOP:
        rest = cs[TOP:]
        h += ('<details class="fold"><summary>其餘 %d 個原因(共 %d 項)</summary>' % (len(rest), sum(c["n"] for c in rest))
              + _table(_cause_rows(rest, TOP + 1)) + "</details>")
    return h + "</section>"


def md_cell(s) -> str:
    return str(s).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def to_md(src: str, rows: list, sel: list, cs: list) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    meta = re.search(r'<header>.*?<div class="note">(.*?)</div>', src, re.S)
    ver = re.search(r'<div class="verdict">(.*?)</div>\s*(?=<h2|<section|<details|<div class="cards)', src, re.S)
    pk = re.search(r'<pre class="pack" id="pk">(.*?)</pre>', src, re.S)
    out = ["# " + (text(m.group(1)) if m else "VIA 現況"), "", "> " + (text(meta.group(1)) if meta else ""), "",
           "**判定** " + (text(ver.group(1)) if ver else "(頁面沒有判定條)"), "",
           "## 先做這幾件(要處理 %d 項 · %d 個原因)" % (len(sel), len(cs)), "",
           "| # | 燈 | 類別 | 項數 | 系統 | 區塊 | 原因 |", "|---|---|---|---|---|---|---|"]
    out += ["| %d | %s | %s | %d | %s | %s | %s |" % (i, ZH.get(c["lamp"], "灰"), md_cell(c["cls"]), c["n"], md_cell(c["sys"]), md_cell(c["sec"]), md_cell(c["why"]))
            for i, c in enumerate(cs, 1)]
    per = {}
    for r in rows:
        k = per.setdefault(str(r[1]), {"all": 0, "sel": 0, "r": 0, "y": 0, "g": 0, "x": 0})
        k["all"] += 1
        k[r[0] if r[0] in "rygx" else "x"] += 1
        k["sel"] += 1 if (len(r) > 11 and r[11]) else 0
    out += ["", "## 依系統", "", "| 系統 | 全部 | 要處理 | 紅 | 黃 | 綠 | 灰 |", "|---|---|---|---|---|---|---|"]
    out += ["| %s | %d | %d | %d | %d | %d | %d |" % (md_cell(s), v["all"], v["sel"], v["r"], v["y"], v["g"], v["x"]) for s, v in sorted(per.items())]
    hdr = ["| 燈 | 系統 | 區塊 | 項目 | 版本 | 狀態說明 | 時間 | 類別 | 去向 |", "|---|---|---|---|---|---|---|---|---|"]

    def line(r):
        return "| %s | %s |" % (ZH.get(r[0], "灰"), " | ".join(md_cell(x) for x in r[1:9]))
    rest = [r for r in rows if not (len(r) > 11 and r[11])]
    out += ["", "## 要處理的每一列(%d)" % len(sel), ""] + hdr + [line(r) for r in sel]
    out += ["", "## 其餘每一列(%d;全部 %d 列)" % (len(rest), len(rows)), ""] + hdr + [line(r) for r in rest]
    if pk:
        out += ["", "## 給 AI 的回饋包", "", "```text", _html.unescape(re.sub(r"<[^>]+>", "", pk.group(1))).strip("\n"), "```"]
    return "\n".join(out) + "\n"


JS = ("<script>(function(){var b=document.getElementById('mdl'),s=document.getElementById('mdj');if(!b||!s)return;"
      "b.onclick=function(){var t=JSON.parse(s.textContent),u=URL.createObjectURL(new Blob([t],{type:'text/markdown;charset=utf-8'})),"
      "a=document.createElement('a');a.href=u;a.download=b.getAttribute('data-name');document.body.appendChild(a);a.click();"
      "setTimeout(function(){URL.revokeObjectURL(u);a.remove()},800)}})();</script>")


def layout_css():
    via = CTX["via"] or P0.find_via()
    css, note = PRIOR.layout_css(via)
    return (css, note) if MARK in css else ("", note if not css else "%s 沒有 v0101 的寬度規則" % note)


def calm(src: str) -> tuple:
    """回 (新頁, 說明)。任何一塊找不到或對帳不符就回 (原頁, 原因)。"""
    rows = rows_of(src)
    if rows is None:
        return src, "找不到矩陣資料"
    blocks = top_blocks(src)
    if not blocks or "verdict" not in " ".join(b[1] for b in blocks):
        return src, "找不到判定條"
    if MX_OPEN not in src:
        return src, "找不到矩陣"
    keep, sysb, fold, tail, names = [], [], [], [], []
    mode = "keep"
    for tag, cls, s, e, seg in blocks:
        t = text(seg)[:40]
        if tag == "h2":
            mode = "sys" if ("系統訊號" in t or "依系統" in t) else "fold"
            if mode == "fold":
                names.append(re.sub(r"^[①②③]\s*", "", t.split("·")[0]).strip()[:14])
        elif t[:1] in "⑤⑥⑦":
            mode = "tail"
        elif t[:1] == "④":
            fold.append(seg)
            names.append("給動作主力的更新回饋")
            continue
        {"keep": keep, "sys": sysb, "fold": fold, "tail": tail}[mode].append(seg)
    if not tail:
        return src, "找不到矩陣那一段"
    sel, cs = causes(rows)
    if sum(c["n"] for c in cs) != len(sel):
        return src, "原因歸組的項數對不上(%d ≠ %d)" % (sum(c["n"] for c in cs), len(sel))
    stamp = re.search(r"(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})", src)
    title = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    kind = "功能一覽" if title and "功能一覽" in text(title.group(1)) else "現況"
    fname = "VIA_%s_%s.md" % (kind, "".join(stamp.groups()[:3]) + "_" + "".join(stamp.groups()[3:]) if stamp else "latest")
    parts = keep + sysb + [focus_html(sel, cs, fname)]
    if fold:
        parts.append('<details class="card fold"><summary><b>全部卡片與更新回饋</b><span class="note"> · %s · 平常不用打開;點卡片一樣會篩下面的矩陣</span></summary>%s</details>'
                     % (E(" · ".join(dict.fromkeys(n for n in names if n))), "".join(fold)))
    parts += tail
    first, last = blocks[0][2], blocks[-1][3]
    new = src[:first] + "\n".join(parts) + src[last:]
    if any(seg not in new for _, _, _, _, seg in blocks):
        return src, "重排後有區塊不見"
    new = new.replace(MX_OPEN, '<section class="card mxw" id="mx">', 1)
    i = new.find("<table>", new.find('id="mx"'))
    if i > 0 and new[i:i + 40].startswith("<table><thead>"):
        new = new[:i] + "<table><colgroup>" + "".join('<col class="%s">' % c if c else "<col>" for c in COLS) + "</colgroup>" + new[i + 7:]
    md = json.dumps(to_md(src, rows, sel, cs), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    new = new.replace("</body>", '<script type="application/json" id="mdj">%s</script>%s</body>' % (md, JS), 1)
    css, note = layout_css()
    if css and MARK not in new and "</style>" in new:
        new = new.replace("</style>", "\n" + css + "</style>", 1)
    if not balanced(new):
        return src, "重排後標籤不成對"
    return new, ("先做這幾件 %d 個原因 · 收起 %d 塊" % (len(cs), len(fold))) + ("" if css or MARK in new else " · 寬度規則沒套:" + note)


def render(res, cards, pack, css, tpl_note, accel) -> str:
    html = _O["render"](res, cards, pack, css, tpl_note, accel)
    new, note = calm(html)
    if new is html:
        return html.replace("</header>", '<div class="note">精簡版面沒有套:%s(照前版版面)</div></header>' % E(note), 1)
    return new


P0.render = render


def restore():
    P0.render = _O["render"]


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    P0.render = _O["render"]
    try:
        chk("v0108 的自測(依 甲 裁定:尾版只驗自己與直接前版)仍全過", PRIOR.selftest() == 0)
    finally:
        P0.render = render
    raw = []
    for i in range(14):
        raw.append({"section": "號冊", "system": "VRN", "lamp": "r", "id": "VRN|m%d" % i, "title": "VRN_MDL%03d_x_v0100" % i, "detail": "號冊有列但檔不在 · 也沒標退役"})
    for i in range(5):
        raw.append({"section": "收據", "system": "VCGC", "lamp": "y", "id": "VCGC|r%d" % i, "title": "receipt%d" % i, "detail": "收據在,但已 %d 小時" % (50 + i)})
    raw += [{"section": "系統", "system": "VDF", "lamp": "g", "id": "VDF|ok", "title": "ok", "detail": "好"},
            {"section": "系統", "system": "VDF", "lamp": "r", "id": "VDF|bad", "title": "壞 | 有直線", "detail": "跑不過 · rc 1 · 失敗"},
            {"section": "參數", "system": "VQG", "lamp": "y", "id": "VQG|p", "title": "p<script>", "detail": "待確認"}]
    r = P0.assemble(raw, "自測", None)
    pack = list(r["head"])
    base = _O["render"](r, P0.cards_of(r), pack, "", "自測", "自測")
    new = P0.render(r, P0.cards_of(r), pack, "", "自測", "自測")
    rows = rows_of(new)
    sel, cs = causes(rows)
    chk("頁面有「先做這幾件」與下載 MD 按鈕", 'id="fx"' in new and 'id="mdl"' in new and "精簡版面沒有套" not in new, new[:200] if "精簡版面沒有套" in new else "")
    chk("原因項數合計 = 要處理的列數;同說明(數字不同)歸成一個原因", sum(c["n"] for c in cs) == len(sel) and any(c["n"] == 5 for c in cs) and any(c["n"] == 14 for c in cs), [(c["cls"], c["n"]) for c in cs])
    chk("原因依類別先後排(真紅在黃前面)", ORDER.index(cs[0]["cls"]) <= ORDER.index(cs[-1]["cls"]), [c["cls"] for c in cs])
    bb = top_blocks(base)
    undo = re.sub(r"<colgroup>(?:<col[^>]*>)+</colgroup><thead><tr><th class=\"l\">燈</th><th>系統</th>", '<thead><tr><th class="l">燈</th><th>系統</th>', new.replace('<section class="card mxw" id="mx">', '<section class="card" id="mx">'))
    lost = [seg[:60] for _, _, _, _, seg in bb if seg not in undo]
    chk("前版每一塊都還在新頁(只搬位置,不丟;扣掉矩陣的欄寬與 class)", bool(bb) and not lost, lost)
    chk("卡片按鈕數不變(點卡片照樣篩矩陣)", base.count('class="kc"') == new.count('class="kc"') > 0, (base.count('class="kc"'), new.count('class="kc"')))
    order = [new.find('class="verdict"'), new.find('id="fx"'), new.find('class="card fold"'), new.find('id="mx"')]
    chk("順序:判定 → 先做這幾件 → 收合區 → 矩陣", all(x > 0 for x in order) and order == sorted(order), order)
    chk("矩陣有 9 欄欄寬,加了 mxw", '<section class="card mxw" id="mx">' in new and new.count('<col class="m-') == 8)
    chk("標籤成對;使用者字串有跳脫(<script> 不會變成標籤)", balanced(new) and "p<script>" not in new and "p&lt;script&gt;" in new)
    md = json.loads(re.search(r'<script type="application/json" id="mdj">(.*?)</script>', new, re.S).group(1))
    data_lines = [x for x in md.splitlines() if x.startswith("| ") and x.split(" | ")[0] in ("| 紅", "| 黃", "| 綠", "| 灰")]
    chk("MD:每一列都在(要處理 + 其餘 = 全部),直線有跳脫", len(data_lines) == len(rows) and "壞 \\| 有直線" in md, (len(data_lines), len(rows)))
    chk("MD:有判定、先做這幾件、依系統、回饋包", all(k in md for k in ("**判定**", "## 先做這幾件", "## 依系統", "## 給 AI 的回饋包")))
    chk("頁面本身沒有加任何色碼", not re.search(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"<style>.*?</style>|<script.*?</script>", "", new, flags=re.S).replace(base.split("</style>")[0], "")))
    real = PRIOR.layout_css(HERE.parents[1])[0]
    chk("真倉的版面冊尾版有 v0101 寬度規則、沒有顏色,而且頁面套上了", MARK in real and not PRIOR.COLOR.search(real) and MARK in new)
    bad = new.replace('<script type="application/json" id="d">', '<script type="application/json" id="dd">', 1)
    chk("負控:找不到矩陣資料 → 原樣回並說原因", calm(bad) == (bad, "找不到矩陣資料"))
    chk("負控:找不到判定條 → 原樣回", calm(base.replace('class="verdict"', 'class="v2"'))[1] == "找不到判定條")
    empty = P0.assemble([{"section": "系統", "system": "VDF", "lamp": "g", "id": "a", "title": "a", "detail": "好"}], "自測", None)
    e2 = P0.render(empty, P0.cards_of(empty), list(empty["head"]), "", "自測", "自測")
    chk("沒有要處理的:照實說沒有,不編原因", "這一輪沒有要處理的項目" in e2 and balanced(e2))
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf109_st_"))
    try:
        CTX["via"] = tmp
        n3 = P0.render(r, P0.cards_of(r), pack, "", "自測", "自測")
        chk("版面冊不在:照樣重排,頁首註明寬度規則沒套", 'id="fx"' in n3 and "寬度規則沒套" not in n3 and MARK not in n3)
    finally:
        CTX["via"] = None
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
    try:
        return PRIOR.main(args)
    finally:
        restore()


if __name__ == "__main__":
    sys.exit(main())
