#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0103 — 薄尾(v0102 · v0101 · v0100 一字不動):現況顯示最佳化,並備好給入口整合的介面。

操作員 2026-11-18:「現況顯示功能引擎及展現方式最佳化準備被整合」。

引擎
  ① 彙總列不另計:來源標了 rollup 的列(號冊彙總、橋覆蓋彙總)照樣進矩陣,但不再入選、不再算進真紅 / 黃(細項已逐列各算一項)。
     去向寫「彙總列:細項已逐列,不另計」。曾鎖定為綠的彙總列變了仍照報退步。
  ② 分流修正:紅列的說明裡有明確失敗字樣(仍紅 · [FAIL] · FAILED · Traceback)而沒有缺套件字樣時,歸真紅,不被環境 / 中斷的字眼帶走。
  ③ NEXT 講最大宗那一組是什麼;「號冊有列但檔不在」那一組寫明要全量編號標退役(要操作員批准),不是出新版。
  ④ 上一輪快照與成功鎖的檔名不再跟著來源引擎的版號走(來源出新版不會變成「第一輪」);第一次會把舊檔複製成新名,舊檔不動。
  ⑤ 來源引擎(CGC_MDL282 v0102 起)有增量快取,第二輪起只重掃變過的檔。
  ⑥ 本平台自己寫的收據(STATUS_latest.json · FEEDBACK_latest.json)不再被當成別人的收據掃進矩陣,免得每一輪讀到自己上一輪的燈。
展現(版面仍只取模板鎖冊,沒有新增任何樣式)
  判定條 → 分類卡(八類)→ 系統卡(VCGC · VDF · VRN-2 · VQG · VAP · 其他:各自要處理幾項)→ 群組卡(六組,取代二十幾張區塊卡)→
  給動作主力的更新回饋 → 回饋包(收合)→ 矩陣(預設只看要處理的,可切回全部;多一個群組篩選)→ 機制與對帳(收合)。
  卡片數字照舊只由矩陣算;多兩條對帳:群組卡合計 = 矩陣列數、系統卡合計 = 入選數。
整合(本引擎不改任何入口;以下是給整合的人或 AI 用的)
  · 收據 VIA_Reports/vcgc/STATUS_latest.json:lamp · lamp_scope · at · version · summary · host · 各類計數 · 對帳 · 檔案位置;形狀照收據契約的共通欄。
  · 函式 status(via=None, actor="", budget=300, out=None) → 跑一輪、不印東西、回傳上面那份收據(dict)。
  · 動詞 manifest:印出整合說明(動詞、旗標、輸出、收據欄位、rc、相依版本、接線步驟)。
  · 建議接法:VCGC 入口的 monitor 動詞呼叫 status();MCP 門面登 vcgc/status → STATUS_latest.json;收據契約冊加一筆;功能盤點冊加一筆。
動詞  run · selftest · manifest · spec · version · tools · release(其餘同 v0102)
唯讀倉;只寫 VIA_Reports/vcgc。不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL283_CardMatrixFeedback run --actor claude
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

import contextlib
import datetime as _dt
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0103"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0102.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0102", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0102"] = PRIOR
_spec.loader.exec_module(PRIOR)
P1 = PRIOR.PRIOR            # v0101
P0 = P1.PRIOR               # v0100 本體
CTX = P1.CTX
PRIOR.ENGINE = P1.ENGINE = P0.ENGINE = ENGINE
E, LN, CN, SEV, cut, worst = P0.E, P0.LN, P0.CN, P0.SEV, P0.cut, P0.worst
SOURCE = "CGC_MDL282_LocalMonitor 現況矩陣"          # 不帶版號:快照與鎖的檔名才不會跟著來源換版
SYS_ORDER = ["VCGC", "VDF", "VRN-2", "VQG", "VAP", "其他"]
SYS_ALIAS = {"VRN": "VRN-2", "VRN2": "VRN-2"}
GROUPS = [("系統與工具", ("系統", "工具", "本機工具", "執行環境", "版本線")), ("參數與資料", ("參數", "資料庫", "同義字正則", "環境套件")),
          ("模組與號冊", ("模組引擎", "號冊", "號冊待辦", "橋覆蓋")), ("收據與測試", ("收據", "收據契約", "應有收據", "測試分級")),
          ("治理", ("衝突登記", "成功鎖", "管理面覆蓋"))]
SEC_GROUP = {s: g for g, ss in GROUPS for s in ss}
HARD_FAIL = re.compile(r"仍紅|\[FAIL\]|FAILED|AssertionError|Traceback")
MISSING = re.compile(r"ModuleNotFound|No module named|沒裝|缺套件|缺依賴|環境缺件")
TIMEOUT = re.compile(r"逾時|rc\s*=?\s*124\b|timed out")
OWN_RECEIPTS = ("vcgc/STATUS_latest.json", "vcgc/FEEDBACK_latest.json")
STATE = {"roll": set(), "src": "", "sys": [], "grp": [], "roll_n": 0, "own_n": 0}
_O = {"monitor": PRIOR.monitor, "from_lm": P0.from_localmonitor, "stage1": P0.stage1, "classify": P0.classify, "assemble": P0.assemble, "write_out": P0.write_out}


def sysg(name: str) -> str:
    n = SYS_ALIAS.get(name, name)
    return n if n in SYS_ORDER else "其他"


# ---------------- 引擎 ----------------
class _Proxy:
    """包住來源引擎:照原樣回傳延伸項目,同時記下哪些是彙總列。"""

    def __init__(self, m):
        self._m = m

    def sec_extra(self, via):
        items = self._m.sec_extra(via)
        STATE["roll"] = {"%s|%s|%s" % (str(it.get("section") or "未分區"), str(it.get("system") or "—"), str(it.get("id") or "") or str(it.get("title") or "")) for it in items if it.get("rollup")}
        return items


def monitor(via):
    m = _O["monitor"](via)
    return _Proxy(m) if m is not None and hasattr(m, "sec_extra") else m


def from_localmonitor(via):
    raw, src = _O["from_lm"](via)
    own = [r for r in raw if r.get("section") == "收據" and str(r.get("id") or "").replace("\\", "/").endswith(OWN_RECEIPTS)]
    STATE["src"], STATE["own_n"] = src, len(own)
    return [r for r in raw if r not in own], SOURCE  # 本平台自己的收據不拿來當別人的收據看,否則每一輪都在讀自己上一輪的燈


def stage1(items, prev):
    items = _O["stage1"](items, prev)
    for it in items:
        if it["key"] in STATE["roll"] and "S5" not in it["rules"]:
            it["rules"], it["selected"], it["roll"] = [], False, True
    return items


def classify(it, peer=None):
    c = _O["classify"](it, peer)
    d = it["detail"]
    if c in ("ENV", "INT") and it["lamp"] == "r" and HARD_FAIL.search(d) and not MISSING.search(d) and not (c == "INT" and TIMEOUT.search(d)):
        it["also"] = ""
        return "TRUE"
    return c


def better_next(res) -> str:
    sel = [it for it in res["items"] if it["selected"]]
    n = res["by_cls"]

    def top(cls):
        g = {}
        for it in sel:
            if it["cls"] == cls:
                k = (it["system"], it["section"], it.get("cause") or "")
                g[k] = g.get(k, 0) + 1
        return max(g.items(), key=lambda kv: kv[1]) if g else (("", "", ""), 0)
    if n["REG"]:
        return "先看退步 %d 項(鎖過的綠現在不是綠);再處理真紅 %d 項。" % (n["REG"], n["TRUE"])
    if n["TRUE"]:
        (sysn, sec, cause), m = top("TRUE")
        tail = ":這一組要跑全量編號才會標退役(要操作員批准),不是出新版。" if "檔不在" in cause else ";先處理這一組。"
        return "真紅 %d 項,最大宗 %d 項是 %s/%s「%s」%s" % (n["TRUE"], m, sysn, sec, cut(cause, 40), tail)
    return res["next"]


def assemble(raw, source, prev, budget=300, peer=None):
    STATE.update(roll=set(), sys=[], grp=[], roll_n=0)
    res = _O["assemble"](raw, source, prev, budget, peer)
    items = res["items"]
    for it in items:
        if it.get("roll"):
            it["disp"] = "彙總列:細項已逐列,不另計"
    STATE["roll_n"] = sum(1 for it in items if it.get("roll"))
    if STATE["roll_n"]:  # v0100 的對帳行只拆綠與灰;彙總列是帶黃 / 紅燈的未入選,補上才加得起來
        for i, line in enumerate(res["head"]):
            if line.startswith("[對帳]"):
                res["head"][i] = re.sub(r"未入選 \d+\S綠 \d+ · 灰 \d+", lambda m: m.group(0) + " · 彙總列 %d" % STATE["roll_n"], line, count=1)
    res["next"] = better_next(res)
    sel = [it for it in items if it["selected"]]
    for s in SYS_ORDER:
        mine = [it for it in sel if sysg(it["system"]) == s]
        c = {k: sum(1 for it in mine if it["lamp"] == k) for k in "ryxg"}
        STATE["sys"].append({"kind": "sys", "key": s, "label": s, "n": len(mine), "lamp": worst([it["lamp"] for it in mine]) if any(it["lamp"] in "ry" for it in mine) else ("x" if mine else "g"),
                             "reason": ("紅 %d · 黃 %d · 灰 %d" % (c["r"], c["y"], c["x"])) if mine else "沒有要處理的"})
    for g in [g for g, _ in GROUPS] + ["其他"]:
        mine = [it for it in items if SEC_GROUP.get(it["section"], "其他") == g]
        if not mine and g == "其他":
            continue
        c = {k: sum(1 for it in mine if it["lamp"] == k) for k in "rygx"}
        STATE["grp"].append({"kind": "grp", "key": g, "label": g, "n": len(mine), "lamp": worst([it["lamp"] for it in mine]),
                             "reason": "紅 %d · 黃 %d · 綠 %d · 灰 %d" % (c["r"], c["y"], c["g"], c["x"])})
    res["checks"]["群組卡合計 = 矩陣列數"] = sum(c["n"] for c in STATE["grp"]) == len(items)
    res["checks"]["系統卡合計 = 入選數"] = sum(c["n"] for c in STATE["sys"]) == len(sel)
    if not all(res["checks"].values()):
        res["ok"], res["lamp"] = False, "r"
        res["why"] = "對帳不符:" + "、".join(k for k, v in res["checks"].items() if not v)
        res["head"][1] = "[判定] RED · " + res["why"]
    return res


def host():
    win = platform.system() == "Windows"
    box = os.path.exists("/.dockerenv") or bool(os.environ.get("CLAUDE_CODE_REMOTE") or os.environ.get("CODESPACES"))
    return {"system": platform.system(), "container": bool(box), "counts_as_host_run": win}


def write_out(out: Path, res, pack, page, slug):
    extra = []
    if STATE["src"]:
        extra.append("[來源] %s" % STATE["src"].replace(" 的五個區塊", "") + (" · 彙總列 %d 列不另計" % STATE["roll_n"] if STATE["roll_n"] else "") + (" · 本平台自己的收據 %d 份不列" % STATE["own_n"] if STATE.get("own_n") else ""))
    final = _O["write_out"](out, res, pack[:2] + extra + pack[2:], page, slug)
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {"schema": "VIA.StatusDisplay.Receipt.v1", "system": "VCGC", "receipt": "status-display", "engine": ENGINE, "version": "v0103",
           "lamp": {"g": "GREEN", "y": "YELLOW", "r": "RED"}[res["lamp"]], "lamp_raw": res["lamp"],
           "lamp_scope": "現況偵測的彙總燈:倉內冊與收據照實彙總。不是任何系統的業務驗收;容器跑的不算主機實測。",
           "at": now, "ts": now, "summary": res["why"], "next": res["next"], "actor": CTX.get("actor") or "", "source": STATE["src"] or res["source"], "host": host(),
           "three": {"should": res["n_raw"], "done": res["n_now"], "skipped": len(res["skipped"])}, "matrix_rows": len(res["items"]),
           "selected": sum(1 for it in res["items"] if it["selected"]), "rollup_rows": STATE["roll_n"], "by_class": {CN[c]: n for c, n in res["by_cls"].items()},
           "systems": {c["key"]: {"lamp": c["lamp"], "n": c["n"]} for c in STATE["sys"]}, "groups": {c["key"]: {"lamp": c["lamp"], "n": c["n"]} for c in STATE["grp"]},
           "gaps": list(PRIOR.STATE.get("gaps") or []), "checks": res["checks"], "ok": res["ok"], "fold_level": res["level"], "pack_lines": len(final),
           "paths": {"page": "WORKPLATFORM_latest.html", "delta": "FEEDBACK_DELTA_latest.txt", "pack": "FEEDBACK_latest.txt", "full": "FEEDBACK_FULL_latest.jsonl"}}
    (out / "STATUS_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return final


# ---------------- 展現 ----------------
JS = r"""(function(){var D=JSON.parse(document.getElementById('d').textContent),LN={g:'綠',y:'黃',r:'紅',x:'灰'},shown=200,sg='';
function $(i){return document.getElementById(i)}function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function opts(id,col){var s={},o='<option value="">全部</option>';D.forEach(function(r){s[col===7?r[col].split('+')[0]:r[col]]=1});Object.keys(s).sort().forEach(function(k){if(k)o+='<option>'+esc(k)+'</option>'});$(id).innerHTML=o}
function pick(){var a=$('fs').value,g=$('fg').value,b=$('fb').value,l=$('fl').value,c=$('fc').value,q=$('fq').value.toLowerCase(),on=$('only').checked;return D.filter(function(r){
return(!on||r[11])&&(!sg||r[10]===sg)&&(!a||r[1]===a)&&(!g||r[9]===g)&&(!b||r[2]===b)&&(!l||r[0]===l)&&(!c||r[7].split('+')[0]===c)&&(!q||r.slice(0,9).join(' ').toLowerCase().indexOf(q)>=0)})}
function draw(){var a=pick(),h='';for(var i=0;i<Math.min(a.length,shown);i++){var r=a[i];h+='<tr><td class="l"><span class="lamp '+r[0]+'">'+LN[r[0]]+'</span></td><td class="k">'+esc(r[1])+'</td><td class="n">'+esc(r[2])+'</td><td>'+esc(r[3])+'</td><td class="mono n">'+esc(r[4])+'</td><td>'+esc(r[5])+'</td><td class="mono n">'+esc(r[6])+'</td><td class="n">'+esc(r[7])+'</td><td>'+esc(r[8])+'</td></tr>'}
$('tb').innerHTML=h||'<tr><td class="l"><span class="lamp x">灰</span></td><td colspan="8">沒有符合的列</td></tr>';
$('cnt').textContent='符合 '+a.length+' 列 · 全部 '+D.length+' 列 · 顯示 '+Math.min(a.length,shown)+(sg?' · 系統卡:'+sg:'')+($('only').checked?' · 只看要處理的':'');$('more').hidden=a.length<=shown}
function reset(){['fs','fg','fb','fl','fc','fq'].forEach(function(i){$(i).value=''});sg='';$('only').checked=true}
function press(b){[].forEach.call(document.querySelectorAll('.kc'),function(k){k.setAttribute('aria-pressed',k===b?'true':'false')})}
opts('fs',1);opts('fg',9);opts('fb',2);opts('fc',7);['fs','fg','fb','fl','fc','only'].forEach(function(i){$(i).onchange=function(){shown=200;draw()}});$('fq').oninput=function(){shown=200;draw()};
$('more').onclick=function(){shown+=400;draw()};$('clr').onclick=function(){reset();press(null);shown=200;draw()};
[].forEach.call(document.querySelectorAll('.kc'),function(k){k.onclick=function(){var on=k.getAttribute('aria-pressed')==='true';reset();if(on){press(null)}else{press(k);var t=k.dataset.kind,v=k.dataset.key;
if(t==='cls'){$('fc').value=v}else if(t==='sys'){sg=v}else{$('fg').value=v;$('only').checked=false}}shown=200;draw();$('mx').scrollIntoView({block:'nearest'})}});
$('cp').onclick=function(){var t=$('pk').textContent;function done(){$('cp').textContent='已複製'}function sel(){var p=$('pk').closest('details');if(p)p.open=true;var r=document.createRange();r.selectNodeContents($('pk'));var s=getSelection();s.removeAllRanges();s.addRange(r)}
if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,sel)}else{sel()}};draw()})();"""


def render(res, cards, pack, css, tpl_note, accel) -> str:
    order = {n: i for i, (_, n, _) in enumerate(P0.CLASSES)}
    data = [[it["lamp"], it["system"], it["section"], it["title"], it["ver"], cut(it["detail"], 260), it["at"],
             CN.get(it["cls"], "未入選") + (("+" + it["also"]) if it.get("also") else ""), it["disp"], SEC_GROUP.get(it["section"], "其他"), sysg(it["system"]), 1 if it["selected"] else 0] for it in res["items"]]
    data.sort(key=lambda r: (order.get(r[7].split("+")[0], 99), SEV[r[0]], r[1], r[2], r[3]))
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    def card(c):
        return ('<button type="button" class="kc" aria-pressed="false" data-kind="%s" data-key="%s"><span class="kl"><span class="lamp %s">%s</span>%s</span>'
                '<span class="kn">%d</span><span class="kr">%s</span></button>') % (c["kind"], E(c["key"]), c["lamp"], LN[c["lamp"]], E(c["label"]), c["n"], E(c["reason"]))
    h = host()
    where = "Windows 主機" if h["counts_as_host_run"] else "%s%s:綠不算主機實測" % (h["system"], "(容器)" if h["container"] else "")
    gaps = PRIOR.STATE.get("gaps") or []
    delta = CTX.get("delta") or []
    rules = "".join('<tr><td class="l">%s</td><td>%s</td></tr>' % (E(k), E(v)) for k, v in P0.RULES)
    chk = "".join('<tr><td class="l"><span class="lamp %s">%s</span></td><td>%s</td></tr>' % ("g" if v else "r", "綠" if v else "紅", E(k)) for k, v in res["checks"].items())
    sel_n = sum(1 for it in res["items"] if it["selected"])
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA 現況 · 卡片與矩陣</title><style>%s</style></head><body><div class=\"wrap\">"
            '<header><div class="caps">VIA · 對內工作平台 · 現況</div><h1>現況:%d 項要處理 · 全部 %d 列</h1>'
            '<div class="note">%s · %s · 來源 %s · 模板 %s · 加速器 %s · %s</div></header>'
            '<div class="verdict"><span class="lamp %s">%s</span><b>%s</b><span>%s</span></div>'
            '<h2>① 要處理的:依類別</h2><div class="cards">%s</div>'
            '<h2>② 要處理的:依系統</h2><div class="cards">%s</div>'
            '<h2>③ 全部列:依群組</h2><div class="cards">%s</div><div class="note">還沒管到的面向:%s</div>'
            '<section class="card"><h2>④ 給動作主力的更新回饋(這一輪跟上一輪比)</h2><pre class="pack">%s</pre></section>'
            '<details class="card"><summary><b>⑤ 給 AI 的回饋包 · %d 行 · 應掃 %d · 已掃 %d · 略過 %d · 摺疊層級 %d(點開)</b></summary>'
            '<div class="bar"><button type="button" id="cp">複製回饋包</button></div><pre class="pack" id="pk">%s</pre></details>'
            '<section class="card" id="mx"><h2>⑥ 矩陣(每一列都有去向)</h2><div class="bar"><label>系統<select id="fs"></select></label><label>群組<select id="fg"></select></label>'
            '<label>區塊<select id="fb"></select></label><label>燈<select id="fl"><option value="">全部</option><option value="r">紅</option><option value="y">黃</option><option value="g">綠</option><option value="x">灰</option></select></label>'
            '<label>類別<select id="fc"></select></label><label>找字<input id="fq" type="search"></label><label>只看要處理的<input id="only" type="checkbox" checked></label>'
            '<button type="button" id="clr">清除篩選</button></div>'
            '<div class="note num" id="cnt"></div><div class="box"><table><thead><tr><th class="l">燈</th><th>系統</th><th>區塊</th><th>項目</th><th>版本</th><th>狀態說明</th><th>時間</th><th>類別</th><th>去向</th></tr></thead>'
            '<tbody id="tb"></tbody></table></div><div class="bar"><button type="button" id="more" hidden>再顯示 400 列</button></div></section>'
            '<details class="card"><summary><b>⑦ 篩選機制與對帳(%s)</b></summary><div class="note">第一段六條任一命中就入選;第二段分流、併組、排序,超過行數只摺不丟;彙總列不另計。</div>'
            '<div class="scroll"><table><thead><tr><th class="l">條</th><th>第一段:入選條件</th></tr></thead><tbody>%s</tbody></table></div>'
            '<div class="scroll"><table><thead><tr><th class="l">燈</th><th>對帳</th></tr></thead><tbody>%s</tbody></table></div></details>'
            '</div><script type="application/json" id="d">%s</script><script>%s</script></body></html>') % (
        css, sel_n, len(res["items"]), E(res["stamp"]), E(where), E((STATE["src"] or res["source"]).replace(" 的五個區塊", "")), E(tpl_note), E(accel), E(ENGINE),
        res["lamp"], LN[res["lamp"]], E(res["why"]), E("NEXT: " + res["next"]),
        "".join(card(c) for c in cards if c["kind"] == "cls"), "".join(card(c) for c in STATE["sys"]), "".join(card(c) for c in STATE["grp"]),
        E("、".join(gaps) if gaps else "沒有(管理面覆蓋全部有來源)" if PRIOR.STATE.get("extra_n") else "這一輪沒有延伸偵測,無從判斷"),
        E("\n".join(delta) if delta else "這一輪沒有更新回饋"), len(pack), res["n_raw"], res["n_now"], len(res["skipped"]), res["level"], E("\n".join(pack)),
        "全部相符" if res["ok"] else "有不符", rules, chk, blob, JS)


PRIOR.monitor = monitor
# 更新回饋的「仍未解 / 新增 / 修好」也不把彙總列另算一項(彙總列的細項已各自在列)
P1.delta_lines = (lambda _d: lambda res, prev, actor: _d(dict(res, items=[it for it in res["items"] if not it.get("roll")]), prev, actor))(P1.delta_lines)
P0.from_localmonitor, P0.stage1, P0.classify, P0.assemble, P0.write_out, P0.render = from_localmonitor, stage1, classify, assemble, write_out, render


# ---------------- 整合介面 ----------------
def migrate(out: Path):
    """快照與成功鎖換成不帶來源版號的檔名;只複製,不動舊檔。"""
    done = []
    new_snap = out / ("FEEDBACK_SNAPSHOT_%s.json" % (re.sub(r"[^\w.-]+", "_", SOURCE)[:60]))
    if not new_snap.exists():
        old = sorted(out.glob("FEEDBACK_SNAPSHOT_CGC_MDL282_LocalMonitor_v*.json"), key=lambda p: p.stat().st_mtime)
        if old:
            shutil.copy2(str(old[-1]), str(new_snap))
            done.append("快照沿用 " + old[-1].name)
    new_lock = out / ("FEEDBACK_SUCCESSLOCK_%s.json" % P1.stable_slug(SOURCE))
    old_lock = out / ("FEEDBACK_SUCCESSLOCK_%s.json" % P1.stable_slug("CGC_MDL282_LocalMonitor_v0100 的五個區塊"))
    if not new_lock.exists() and old_lock.exists():
        shutil.copy2(str(old_lock), str(new_lock))
        done.append("成功鎖沿用 " + old_lock.name)
    return done


MANIFEST = {
    "name": "VIA 現況顯示(卡片 · 矩陣 · AI 回饋)", "engine": ENGINE, "system": "VCGC", "read_only": True,
    "chain": ["CGC_MDL283_CardMatrixFeedback_v0100.py", "CGC_MDL283_CardMatrixFeedback_v0101.py", "CGC_MDL283_CardMatrixFeedback_v0102.py", "CGC_MDL283_CardMatrixFeedback_v0103.py"],
    "depends": {"偵測": "CGC_MDL282_LocalMonitor 尾版(v0102 起有快取與彙總列標記;只有 v0100 也能跑,少延伸區塊)",
                "模板": "VIA_UI_WorkPlatform_TemplateLock 尾版 + 它釘住的 VIA_UI_Template_SSOT", "分流字樣": "CGC_MDL259_AiVerbBridge(可缺)",
                "成功鎖定帳": "docs/handoff/daily/VIA_SuccessLock_Ledger_v0100.jsonl(只讀)"},
    "verbs": {"run": "跑一輪並寫出全部輸出", "selftest": "自測(含前版鏈)", "manifest": "印這份整合說明", "tools": "本機免費工具狀態", "release <子字串>": "放掉項目層的成功鎖", "spec": "機制說明", "version": "版本"},
    "flags": {"--actor <名>": "動作主力(也可用環境變數 VIA_ACTOR)", "--in <json>": "改吃外部項目冊(其他系統自報)", "--out <夾>": "輸出夾,預設 VIA_Reports/vcgc",
              "--budget <行>": "回饋包行數上限,預設 300", "--no-open": "不開頁", "--no-clip": "不放剪貼簿"},
    "rc": {"0": "綠", "2": "黃", "1": "紅(對帳不符也是 1)", "3": "找不到 VIA 夾"},
    "outputs": {"STATUS_latest.json": "收據(給入口 · 互監 · MCP 讀)", "WORKPLATFORM_latest.html": "卡片 + 矩陣頁", "FEEDBACK_DELTA_latest.txt": "給動作主力的更新回饋",
                "FEEDBACK_latest.txt": "回饋包(≤300 行)", "FEEDBACK_FULL_latest.jsonl": "完整去向冊(留在本機)"},
    "receipt_fields": ["schema", "system", "receipt", "engine", "version", "lamp", "lamp_raw", "lamp_scope", "at", "ts", "summary", "next", "actor", "source", "host", "three",
                       "matrix_rows", "selected", "rollup_rows", "by_class", "systems", "groups", "gaps", "checks", "ok", "fold_level", "pack_lines", "paths"],
    "python_api": "status(via=None, actor='', budget=300, out=None) -> dict(跑一輪、不印東西、回傳收據)",
    "integrate": ["VCGC 入口加 monitor 動詞:載本家族尾版,呼叫 status(),印 lamp / summary / next 三行並回 rc(綠 0 · 黃 2 · 紅 1)",
                  "MCP 唯讀門面登一把鍵 vcgc/status → VIA_Reports/vcgc/STATUS_latest.json",
                  "收據契約冊 VCGC 節加一筆:id status-display · lamp_key lamp · at_keys [at, ts] · required [lamp, at, version, summary]",
                  "功能盤點冊登本家族;需求冊 / 工作流冊補登",
                  "其他系統要進同一頁:各自的管理器把項目寫成項目冊(items:section · system · lamp · id · title · detail · ver · at · needs · rollup),用 --in"],
    "not_done": ["沒有改任何入口、門面、契約冊、盤點冊(留給整合)", "只在容器實跑,沒有 Windows 主機收據", "剪貼簿那段沒在 Windows 上跑過"]}


def status(via=None, actor="", budget=300, out=None) -> dict:
    """給入口整合用:跑一輪、不印東西、回傳收據。找不到 VIA 夾時回 {'lamp': 'GRAY', ...}。"""
    via = P0.find_via(str(via) if via else "")
    if via is None:
        return {"schema": "VIA.StatusDisplay.Receipt.v1", "lamp": "GRAY", "summary": "找不到 VIA 夾", "ok": False}
    args = ["run", "--no-open", "--no-clip", "--budget", str(budget)] + (["--actor", actor] if actor else []) + (["--out", str(out)] if out else [])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(args + ["--root", str(via)])
    p = (Path(out) if out else via / "VIA_Reports" / "vcgc") / "STATUS_latest.json"
    rec = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {"lamp": "GRAY", "summary": "這一輪沒有寫出收據", "ok": False}
    rec["rc"] = rc
    return rec


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    saved = dict(CTX)
    chk("v0102(含 v0101 · v0100)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf103_st_"))
    keep = _O["monitor"]
    try:
        class Stub:
            @staticmethod
            def sec_extra(via):
                return [{"section": "號冊", "system": "VDF", "lamp": "r", "id": "TST|VDF", "title": "TST 號冊 · VDF", "detail": "彙總 · 紅 2", "rollup": True},
                        {"section": "號冊", "system": "CORE", "lamp": "y", "id": "PLCY|CORE", "title": "PLCY 號冊 · CORE", "detail": "彙總 · 黃 9(沒逐列)"},
                        {"section": "號冊待辦", "system": "VDF", "lamp": "r", "id": "T1", "title": "測一", "detail": "平行敗→序跑 仍紅: [FAIL] 環境治理探針"},
                        {"section": "號冊待辦", "system": "VDF", "lamp": "r", "id": "T2", "title": "測二", "detail": "ModuleNotFoundError: No module named polars · FAILED"},
                        {"section": "號冊待辦", "system": "VRN", "lamp": "r", "id": "T3", "title": "測三", "detail": "逾時 900 秒 · [FAIL]"},
                        {"section": "模組引擎", "system": "VRN", "lamp": "r", "id": "M1", "title": "M1", "detail": "已註冊 · 號冊有列但檔不在,也沒標退役"},
                        {"section": "模組引擎", "system": "VRN", "lamp": "r", "id": "M2", "title": "M2", "detail": "已註冊 · 號冊有列但檔不在,也沒標退役"},
                        {"section": "管理面覆蓋", "system": "VCGC", "lamp": "x", "id": "資料內容品質", "title": "資料內容品質", "detail": "還沒管到"}]
        _O["monitor"] = lambda via: Stub
        base = [{"section": "系統", "system": "VAP", "lamp": "g", "id": "VAP", "title": "VAP 入口", "detail": "實跑 rc 0"}]
        CTX.update(via=tmp, out=tmp, extras=True, famkey=True, lock=None, src="", actor="claude", clip=False)
        r = assemble(base, SOURCE, None, 300)
        k = {it["key"]: it for it in r["items"]}
        chk("彙總列進矩陣但不入選,去向寫明不另計", not k["號冊|VDF|TST|VDF"]["selected"] and "不另計" in k["號冊|VDF|TST|VDF"]["disp"] and STATE["roll_n"] == 1, k["號冊|VDF|TST|VDF"]["disp"])
        acct = next(x for x in r["head"] if x.startswith("[對帳]"))
        nums = [int(x) for x in re.findall(r"\d+", acct.split("未入選")[1].split("矩陣")[0])]
        chk("對帳行的未入選拆得開(綠 + 灰 + 彙總列 = 未入選)", "彙總列 1" in acct and len(nums) == 4 and nums[0] == sum(nums[1:]), acct)
        chk("沒標彙總的黃列(細項沒逐列)照算", k["號冊|CORE|PLCY|CORE"]["selected"] and k["號冊|CORE|PLCY|CORE"]["cls"] == "YEL")
        chk("明確失敗字樣歸真紅,不被環境字眼帶走", k["號冊待辦|VDF|T1"]["cls"] == "TRUE", k["號冊待辦|VDF|T1"]["cls"])
        chk("真的缺套件仍歸環境、真的逾時仍歸中斷", (k["號冊待辦|VDF|T2"]["cls"], k["號冊待辦|VRN|T3"]["cls"]) == ("ENV", "INT"), (k["號冊待辦|VDF|T2"]["cls"], k["號冊待辦|VRN|T3"]["cls"]))
        chk("NEXT 點名最大宗並說要全量編號不是出新版", "最大宗 2 項是 VRN/模組引擎" in r["next"] and "全量編號" in r["next"], r["next"])
        chk("對帳含兩條新的且全部相符", r["ok"] and r["checks"].get("群組卡合計 = 矩陣列數") and r["checks"].get("系統卡合計 = 入選數"), r["checks"])
        s = {c["key"]: c for c in STATE["sys"]}
        chk("系統卡:VRN 併到 VRN-2、沒事的系統亮綠寫 0", s["VRN-2"]["n"] == 3 and s["VRN-2"]["lamp"] == "r" and s["VAP"]["n"] == 0 and s["VAP"]["lamp"] == "g", s)
        g = {c["key"]: c for c in STATE["grp"]}
        chk("群組卡:每個區塊恰屬一組,合計等於矩陣列數", sum(c["n"] for c in g.values()) == len(r["items"]) and g["模組與號冊"]["n"] == 7, {x: g[x]["n"] for x in g})
        STATE["src"] = "CGC_MDL282_LocalMonitor_v0102 的五個區塊"
        pk = write_out(tmp, r, list(r["head"]), lambda p: render(r, P0.cards_of(r), p, "", "自測", "自測"), "st")
        dl = (tmp / "FEEDBACK_DELTA_latest.txt").read_text(encoding="utf-8")
        chk("更新回饋不把彙總列另算", "號冊 · TST" not in dl and "[仍待處理]" in dl, dl[:200])
        rec = json.loads((tmp / "STATUS_latest.json").read_text(encoding="utf-8"))
        chk("收據欄位齊、燈與對帳照實、說明燈的範圍", all(f in rec for f in MANIFEST["receipt_fields"]) and rec["lamp"] == "RED" and rec["ok"] and "不是任何系統的業務驗收" in rec["lamp_scope"],
            [f for f in MANIFEST["receipt_fields"] if f not in rec])
        chk("收據記主機;不是 Windows 就不算主機實測", rec["host"]["counts_as_host_run"] == (platform.system() == "Windows") and rec["gaps"] == ["資料內容品質"])
        page = (tmp / "WORKPLATFORM_latest.html").read_text(encoding="utf-8")
        chk("頁面:三排卡片(類別 · 系統 · 群組)、回饋包收合、預設只看要處理的", page.count('data-kind="cls"') == 8 and page.count('data-kind="sys"') == 6 and page.count('data-kind="grp"') >= 3
            and "<details" in page and 'id="only" type="checkbox" checked' in page and page.count("</script>") == 2)
        chk("頁面點名還沒管到的面向", "還沒管到的面向:資料內容品質" in page)
        chk("回饋包有來源(帶實際版號)與彙總列說明", "[來源] CGC_MDL282_LocalMonitor_v0102 · 彙總列 1 列不另計" in pk, [x for x in pk if x.startswith("[來源]")])
        fake = lambda via: ([{"section": "收據", "system": "VCGC", "lamp": "r", "id": "VIA_Reports/vcgc/STATUS_latest.json", "title": "x", "detail": "lamp = RED"},
                              {"section": "收據", "system": "VDF", "lamp": "g", "id": "VIA_Reports/vdf/H_latest.json", "title": "y", "detail": "lamp = GREEN"}], "CGC_MDL282_LocalMonitor_v0102 的五個區塊")
        keep_lm, _O["from_lm"] = _O["from_lm"], fake
        raw2, src2 = from_localmonitor(tmp)
        _O["from_lm"] = keep_lm
        chk("自己的收據不列、別人的照列、來源名不帶版號", len(raw2) == 1 and raw2[0]["system"] == "VDF" and STATE["own_n"] == 1 and src2 == SOURCE and "v0" not in src2, (len(raw2), src2))
        # 換名沿用
        o2 = tmp / "mig"
        o2.mkdir()
        (o2 / "FEEDBACK_SNAPSHOT_CGC_MDL282_LocalMonitor_v0101_的五個區塊.json").write_text('{"a":"g"}', encoding="utf-8")
        (o2 / ("FEEDBACK_SUCCESSLOCK_%s.json" % P1.stable_slug("CGC_MDL282_LocalMonitor_v0100 的五個區塊"))).write_text('{"a":{"since":"x"}}', encoding="utf-8")
        d1 = migrate(o2)
        chk("快照與成功鎖沿用舊檔(複製,舊檔不動),第二次不重做", len(d1) == 2 and len(list(o2.glob("*.json"))) == 4 and migrate(o2) == [], d1)
        chk("新舊鎖檔名不同但都不帶版號", "v0" not in P1.stable_slug(SOURCE))
        chk("整合說明可序列化且欄位齊", json.loads(json.dumps(MANIFEST, ensure_ascii=False))["rc"]["1"].startswith("紅") and len(MANIFEST["integrate"]) == 5)
        chk("本檔原始碼沒有色碼", not re.search(r"#[0-9a-fA-F]{6}\b", Path(__file__).read_text(encoding="utf-8")))
    finally:
        _O["monitor"] = keep
        shutil.rmtree(str(tmp), ignore_errors=True)
        CTX.clear()
        CTX.update(saved)
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
    if verb == "manifest":
        print(json.dumps(MANIFEST, ensure_ascii=False, indent=2))
        return 0
    if verb == "spec":
        print(__doc__)
    if verb == "run" and "--in" not in args:
        root = args[args.index("--root") + 1] if "--root" in args and args.index("--root") + 1 < len(args) else ""
        via = P0.find_via(root)
        if via is not None:
            out = Path(args[args.index("--out") + 1]) if "--out" in args and args.index("--out") + 1 < len(args) else via / "VIA_Reports" / "vcgc"
            if out.is_dir():
                for line in migrate(out):
                    print("[沿用] " + line, flush=True)
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
