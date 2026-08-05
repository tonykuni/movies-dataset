# -*- coding: utf-8 -*-
"""
============================================================================
 VMT Reply Ingest Engine v1.0  --  回覆迴路閉合 + 下拉選單
 (VeritasMailTracker [E6] 引擎: 把「回」的方向補起來)
----------------------------------------------------------------------------
 自動導入現況:  開工先讀 ssot.json 現有 open 案件, 不用白樣板.
 回覆來源 (自動偵測):
   1. 本機 Outlook 回覆 (win32com) -- 讀你自己信箱近 N 天的 RE: 回覆
   2. replies_inbox.txt -- 半自動: 把對方回覆貼進這個檔
   3. 範例 -- 展示
 解析兩種格式:
   (主) 結構化 token:  ==VMT-REPLY== ISS-0002 | 選項:2 | ETA:2026/07/22 | 原因:圖面缺尺寸
   (備) 純文字勾選:    找到 ISS-#### 附近的  [X] 2 ... + ETA: ... + 原因: ...
 寫回 SSOT (只增不減):
   選項1 已完成->DONE  2 補資料->NEED_DATA  3 澄清->NEED_CLARIFY  4 延長->EXTENDED(+新ETA)
   逐筆記 reply{option,eta,reason,at,by}; 事件流記 REPLY_INGEST; 以雜湊去重不重複處理.
 產出:
   ReplyForm.html   -- 互動下拉選單回覆表 (自動帶入現有 open 案件, 產生 token 供貼回)
   ReplyLoop.html   -- 迴路閉合儀表板 (本次收斂/仍等待/ETA 一覽, Visual Lock 風格)
============================================================================
"""
import os, re, sys, json, html, hashlib, datetime as dt

VMT_ROOT   = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
DATA_DIR   = os.path.join(VMT_ROOT, "data")
OUT_DIR    = os.path.join(VMT_ROOT, "reports")
SSOT_PATH  = os.path.join(DATA_DIR, "ssot.json")
EVENT_PATH = os.path.join(DATA_DIR, "events.jsonl")
INBOX_TXT  = os.path.join(VMT_ROOT, "replies_inbox.txt")
DAYS_BACK  = int(os.environ.get("VMT_DAYS_BACK", "14"))

OPTION_STATUS = {
    "1": ("已完成",      "DONE"),
    "2": ("需要補資料",  "NEED_DATA"),
    "3": ("需要澄清需求","NEED_CLARIFY"),
    "4": ("需要延長時間","EXTENDED"),
}

def now_iso():   return dt.datetime.now().isoformat()
def hsafe(s):    return html.escape("" if s is None else str(s))

def append_event(evt, ref, detail):
    line = json.dumps({"ts": now_iso(), "event": evt, "ref": ref, "detail": detail}, ensure_ascii=False)
    with open(EVENT_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ------------------------------------------- 自動導入現況: 讀 SSOT ------------
def load_ssot():
    if not os.path.exists(SSOT_PATH):
        print("[SSOT] 找不到 %s -- 請先跑 VeritasMailTracker_v1.ps1 產生現況" % SSOT_PATH)
        return None
    with open(SSOT_PATH, encoding="utf-8") as f:
        ss = json.load(f)
    ss.setdefault("processed_replies", [])
    print("[SSOT] 已導入現況: %d 案件 / %d issues (open %d)" % (
        len(ss.get("cases", [])), len(ss.get("issues", [])),
        sum(1 for i in ss.get("issues", []) if i.get("status") == "OPEN")))
    return ss

def save_ssot(ss):
    tmp = SSOT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ss, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SSOT_PATH)

# ------------------------------------------- 回覆來源 -----------------------
def norm_case(s):
    if not s: return None
    m = re.search(r"CASE[-\s]?0*(\d{1,3})", str(s), re.IGNORECASE)
    if m: return "CASE-%02d" % int(m.group(1))
    m = re.search(r"\[Case\s*0*(\d{1,3})\]", str(s), re.IGNORECASE)
    return "CASE-%02d" % int(m.group(1)) if m else None

def source_outlook():
    try:
        import win32com.client
    except Exception:
        return None
    try:
        ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = ns.GetDefaultFolder(6)
        items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        cutoff = dt.datetime.now() - dt.timedelta(days=DAYS_BACK)
        try:
            items = items.Restrict("[ReceivedTime] >= '%s'" % cutoff.strftime("%m/%d/%Y %H:%M %p"))
        except Exception:
            pass
        msgs = []
        for m in items:
            try:
                if getattr(m, "Class", None) != 43:
                    continue
                subj = m.Subject or ""
                body = m.Body or ""
                if ("ISS-" not in body) and ("==VMT-REPLY==" not in body) and (not norm_case(subj)):
                    continue
                sender = ""
                try: sender = m.SenderName or ""
                except Exception: pass
                mid = ""
                try: mid = m.EntryID or ""
                except Exception: pass
                msgs.append({"subject": subj, "body": body, "by": sender, "id": mid})
            except Exception:
                continue
        if not msgs: return None
        print("[來源] 本機 Outlook: %d 封含回覆線索的信 (近 %d 天)" % (len(msgs), DAYS_BACK))
        return msgs
    except Exception as e:
        print("[來源] Outlook 略過:", e)
        return None

def source_inbox_file():
    if not os.path.exists(INBOX_TXT): return None
    txt = open(INBOX_TXT, encoding="utf-8").read()
    if not txt.strip(): return None
    print("[來源] replies_inbox.txt: %d 字元" % len(txt))
    return [{"subject": "", "body": txt, "by": "PASTED", "id": ""}]

def source_sample():
    print("[來源] 無真實回覆 -> 產生範例 (展示 token + 勾選兩種解析)")
    body = (
        "==VMT-REPLY== ISS-0002 | 選項:2 | ETA:2026/07/22 | 原因:圖面缺尺寸標註 | 備註:這兩天大會前人力吃緊，盡量趕 | 確認:是\n"
        "----\n"
        "回覆 ISS-0003:\n"
        "[X] 4. 需要延長時間\n"
        "ETA: 2026/07/23\n"
        "原因: 需等東莞確認版本\n"
        "備註: 供應商週一才回\n"
    )
    return [{"subject": "RE: 今日跟進", "body": body, "by": "India-Team", "id": "SAMPLE-1"}]

# ------------------------------------------- 解析 --------------------------
TOKEN_RE = re.compile(
    r"==VMT-REPLY==\s*(ISS-\d+)\s*\|\s*選項[:：]\s*([1-4])"
    r"(?:\s*\|\s*ETA[:：]\s*([^|\n]+))?"
    r"(?:\s*\|\s*原因[:：]\s*([^|\n]+))?"
    r"(?:\s*\|\s*備註[:：]\s*([^|\n]+))?"
    r"(?:\s*\|\s*確認[:：]\s*([^|\n]+))?",
    re.IGNORECASE)

def parse_replies(msgs, open_ids):
    """回傳 list[dict(issueId,option,eta,reason,by,src_hash)]"""
    out = []
    for m in msgs:
        body = m.get("body", "") or ""
        by   = m.get("by", "") or ""
        found_ids = set()
        # (主) 結構化 token
        for mt in TOKEN_RE.finditer(body):
            iss = mt.group(1).upper()
            conf = (mt.group(6) or "").strip()
            out.append({"issueId": iss, "option": mt.group(2),
                        "eta": (mt.group(3) or "").strip(),
                        "reason": (mt.group(4) or "").strip(),
                        "note": (mt.group(5) or "").strip(),
                        "confirmed": conf in ("是", "yes", "Y", "y", "1", "true", "True"),
                        "by": by, "src": m.get("id", ""), "fmt": "token"})
            found_ids.add(iss)
        # (備) 純文字勾選: 每個 ISS-#### 區段找勾選
        for im in re.finditer(r"(ISS-\d+)", body, re.IGNORECASE):
            iss = im.group(1).upper()
            if iss in found_ids:
                continue
            seg = body[im.start(): im.start() + 400]
            om = re.search(r"[\[\(【]?\s*[xX✓✔■●]\s*[\]\)】]?\s*([1-4])[\.\s、]", seg)
            if not om:
                om = re.search(r"選項[:：]?\s*([1-4])", seg)
            if not om:
                continue
            eta = ""
            em = re.search(r"ETA[:：]?\s*([0-9]{4}[/\-][0-9]{1,2}[/\-][0-9]{1,2}(?:\s+[0-9:]+)?)", seg, re.IGNORECASE)
            if not em:
                em = re.search(r"預計完成[^:：]*[:：]\s*([0-9][^\n]+)", seg)
            if em: eta = em.group(1).strip()
            rm = re.search(r"(?:延遲)?原因[:：]\s*([^\n]+)", seg)
            reason = rm.group(1).strip() if rm else ""
            nm = re.search(r"備註[:：]\s*([^\n]+)", seg)
            note = nm.group(1).strip() if nm else ""
            cm = re.search(r"確認[:：]\s*([^\n]+)", seg)
            confirmed = bool(cm) and cm.group(1).strip() in ("是", "yes", "Y", "y", "1")
            out.append({"issueId": iss, "option": om.group(1), "eta": eta,
                        "reason": reason, "note": note, "confirmed": confirmed,
                        "by": by, "src": m.get("id", ""), "fmt": "checkbox"})
            found_ids.add(iss)
    # 只處理仍屬於系統的 issue
    out = [r for r in out if r["issueId"] in open_ids]
    for r in out:
        raw = "%s|%s|%s|%s|%s|%s" % (r["issueId"], r["option"], r["eta"], r["reason"], r.get("note", ""), r["src"])
        r["hash"] = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return out

# ------------------------------------------- 寫回 SSOT (只增不減) ------------
def apply_replies(ss, replies):
    idx = {i["issueId"]: i for i in ss["issues"]}
    processed = set(ss.get("processed_replies", []))
    changed = []
    for r in replies:
        if r["hash"] in processed:
            continue
        iss = idx.get(r["issueId"])
        if not iss:
            continue
        label, status = OPTION_STATUS.get(r["option"], ("未知", "OPEN"))
        prev = iss.get("status")
        iss["status"] = status
        if status == "DONE":
            iss["closed"] = now_iso()
        if r["eta"]:
            iss["due"] = r["eta"]                       # 延長/更新 ETA
        iss["reply"] = {"option": r["option"], "optionLabel": label,
                        "eta": r["eta"], "reason": r["reason"], "note": r.get("note", ""),
                        "confirmed": bool(r.get("confirmed")),
                        "at": now_iso(), "by": r["by"], "fmt": r["fmt"]}
        processed.add(r["hash"])
        append_event("REPLY_INGEST", r["issueId"],
                     "opt%s(%s) %s->%s ETA=%s confirmed=%s by=%s" % (
                         r["option"], label, prev, status, r["eta"], bool(r.get("confirmed")), r["by"]))
        changed.append({"issueId": r["issueId"], "caseId": iss.get("caseId"),
                        "title": iss.get("title"), "prev": prev, "status": status,
                        "label": label, "eta": r["eta"], "reason": r["reason"],
                        "note": r.get("note", ""), "confirmed": bool(r.get("confirmed")), "by": r["by"]})
    ss["processed_replies"] = sorted(processed)
    return changed

# ------------------------------------------- HTML: 共用樣式 -----------------
VCSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--blue:#4c78a8;--teal:#439a9a;--red:#c96b5a;--grn:#5a9e6f;--amber:#c9a13a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;color:#fff;align-items:center;justify-content:center;font-size:22px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666;letter-spacing:1px}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px;margin-bottom:12px}
.crow{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.cid{font-family:"DM Mono",monospace;font-size:12px;color:#666;min-width:150px}
select,input{font-family:inherit;font-size:13px;padding:6px 8px;border:1px solid var(--hair);border-radius:3px;background:#fff}
.btn{background:var(--blue);color:#fff;border:none;border-radius:3px;padding:8px 16px;font-size:13px;cursor:pointer}
.btn:hover{background:#3a6491}
pre{background:#1e1d1a;color:#e8e6e0;font-family:"DM Mono",monospace;font-size:12px;padding:14px;border-radius:3px;white-space:pre-wrap;margin-top:10px}
.empty{color:#999;text-align:center;padding:16px}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
"""

STATUS_COLOR = {"DONE": "#5a9e6f", "NEED_DATA": "#c96b5a", "NEED_CLARIFY": "#c9a13a",
                "EXTENDED": "#4c78a8", "OPEN": "#999"}

# ------------------------------------------- HTML: 互動下拉回覆表 ------------
def build_reply_form(ss):
    open_issues = [i for i in ss["issues"] if i.get("status") in ("OPEN", "NEED_DATA", "NEED_CLARIFY", "EXTENDED")]
    rows = ""
    js_issues = []
    for i in open_issues:
        iid = i["issueId"]; cid = i.get("caseId", ""); title = i.get("title", "")
        js_issues.append(iid)
        rows += """
<div class="card" data-iss="{iid}">
  <div class="crow"><span class="cid">{iid} · {cid}</span><b>{title}</b></div>
  <div class="crow" style="margin-top:8px">
    <select class="opt">
      <option value="">— 選擇回覆 —</option>
      <option value="1">1. 已完成（附資料）</option>
      <option value="2">2. 需要補資料</option>
      <option value="3">3. 需要澄清需求</option>
      <option value="4">4. 需要延長時間</option>
    </select>
    <input class="eta" type="date" title="ETA 預計完成">
    <input class="reason" type="text" placeholder="原因（簡短，選填）" style="flex:1;min-width:160px">
  </div>
  <textarea class="note" rows="2" placeholder="備註／說明（選填，會一併記錄並顯示在專案組儀表板供檢視）" style="width:100%;margin-top:8px;font-family:inherit;font-size:13px;padding:8px;border:1px solid var(--hair);border-radius:3px"></textarea>
  <label style="display:block;margin-top:8px;font-size:13px"><input type="checkbox" class="confirm"> 我確認以上選擇無誤（需勾選，此項才會納入回覆）</label>
</div>""".format(iid=hsafe(iid), cid=hsafe(cid), title=hsafe(title))
    if not rows:
        rows = "<div class='empty'>目前無待回覆的 open 案件</div>"
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>VMT 回覆表</title><style>%s</style></head>
<body><header><div class="seal" style="background:#4c78a8">覆</div><div>
<h1>VMT 互動回覆表 — 下拉選單（自動帶入現有 open 案件）</h1>
<div class="sub">填完按「產生回覆內容」→ 複製 → 貼進 Email 回信 | %s</div></div></header>
<div class="strip"></div>
<h2>待回覆案件</h2>
%s
<div style="margin-top:14px"><button class="btn" onclick="gen()">產生回覆內容</button>
<button class="btn" style="background:#439a9a" onclick="cp()">複製</button></div>
<pre id="out">（填好上方下拉選單後按「產生回覆內容」）</pre>
<footer>回覆內容含 ==VMT-REPLY== 結構標記，貼回 Email 後由 vmt_reply_ingest 自動寫回 SSOT 閉環</footer>
<script>
function gen(){
  var cards=document.querySelectorAll('.card[data-iss]'); var lines=[]; var pending=0;
  cards.forEach(function(c){
    var iss=c.getAttribute('data-iss');
    var opt=c.querySelector('.opt').value; if(!opt) return;
    var confirmed=c.querySelector('.confirm').checked;
    if(!confirmed){ pending++; return; }   // 防呆: 未勾選確認的項目不納入
    var eta=c.querySelector('.eta').value||'';
    var reason=c.querySelector('.reason').value||'';
    var note=(c.querySelector('.note').value||'').replace(/[\\r\\n]+/g,' ');
    var s='==VMT-REPLY== '+iss+' | 選項:'+opt;
    if(eta) s+=' | ETA:'+eta;
    if(reason) s+=' | 原因:'+reason;
    if(note) s+=' | 備註:'+note;
    s+=' | 確認:是';
    lines.push(s);
  });
  var out=lines.length? lines.join('\\n') : '（尚未有已確認的回覆）';
  if(pending>0) out+='\\n\\n（有 '+pending+' 項已選但尚未勾選「我確認」，未納入回覆）';
  document.getElementById('out').innerText = out;
}
function cp(){ var t=document.getElementById('out').innerText;
  navigator.clipboard.writeText(t).then(function(){ alert('已複製，貼進 Email 回信即可'); }); }
</script></body></html>""" % (VCSS, now, rows)

# ------------------------------------------- HTML: 迴路閉合儀表板 ------------
def build_loop_dashboard(ss, changed):
    issues = ss["issues"]
    n_open = sum(1 for i in issues if i.get("status") == "OPEN")
    n_done = sum(1 for i in issues if i.get("status") == "DONE")
    n_wait = sum(1 for i in issues if i.get("status") in ("NEED_DATA", "NEED_CLARIFY", "EXTENDED"))
    ch_rows = ""
    for c in changed:
        col = STATUS_COLOR.get(c["status"], "#999")
        conf = ("<span class='pill' style='background:#5a9e6f'>已確認</span>"
                if c.get("confirmed") else "<span class='pill' style='background:#c9a13a'>未確認</span>")
        note = hsafe(c.get("note", "")) or "<span style='color:#bbb'>—</span>"
        ch_rows += ("<tr><td>%s</td><td>%s</td><td>%s &rarr; <span class='pill' style='background:%s'>%s</span></td>"
                    "<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            hsafe(c["issueId"]), hsafe(c["caseId"]), hsafe(c["prev"]), col, hsafe(c["label"]),
            hsafe(c["eta"]), hsafe(c["reason"]), note, conf, hsafe(c["by"])))
    if not ch_rows:
        ch_rows = "<tr><td colspan='8' class='empty'>本次無新回覆被收斂（可能已去重或無回覆）</td></tr>"
    wait_rows = ""
    for i in issues:
        if i.get("status") in ("OPEN", "NEED_DATA", "NEED_CLARIFY", "EXTENDED"):
            col = STATUS_COLOR.get(i.get("status"), "#999")
            rp = i.get("reply", {})
            wait_rows += ("<tr><td>%s</td><td>%s</td><td>%s</td><td><span class='pill' style='background:%s'>%s</span></td>"
                          "<td>%s</td></tr>" % (
                hsafe(i["issueId"]), hsafe(i.get("caseId")), hsafe(i.get("title")),
                col, hsafe(i.get("status")), hsafe(i.get("due") or rp.get("eta", ""))))
    if not wait_rows:
        wait_rows = "<tr><td colspan='5' class='empty'>全部收斂，無等待中案件</td></tr>"
    kpi = [("本次收斂", len(changed), "#5a9e6f"), ("仍 OPEN", n_open, "#999"),
           ("等待補件/澄清/延長", n_wait, "#c9a13a"), ("已完成累計", n_done, "#5a9e6f")]
    kpis = "".join("<div class='card' style='min-width:150px;display:inline-block;margin-right:10px'>"
                   "<div style='font-size:24px;font-weight:700;color:%s'>%s</div>"
                   "<div style='font-size:12px;color:#777'>%s</div></div>" % (c, v, n) for n, v, c in kpi)
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>VMT 迴路閉合</title><style>%s</style></head>
<body><header><div class="seal" style="background:#439a9a">環</div><div>
<h1>VMT 迴路閉合儀表板 — 回覆自動寫回 SSOT</h1>
<div class="sub">只增不減 · 去重 · 事件流留痕 | %s</div></div></header>
<div class="strip"></div>
<h2>KPI</h2><div>%s</div>
<h2>本次收斂 — 剛寫回 SSOT 的回覆（狀態由下拉選項決定；備註僅記錄供檢視）</h2>
<table><tr><th>ISS</th><th>案件</th><th>狀態轉移</th><th>ETA</th><th>原因</th><th>備註</th><th>確認</th><th>回覆者</th></tr>%s</table>
<h2>仍等待中 — 需持續跟進</h2>
<table><tr><th>ISS</th><th>案件</th><th>問題</th><th>狀態</th><th>ETA</th></tr>%s</table>
<footer>vmt_reply_ingest v1.0 | 回覆來源: Outlook / replies_inbox.txt | 事件流: events.jsonl</footer>
</body></html>""" % (VCSS, now, kpis, ch_rows, wait_rows)

# ------------------------------------------- 主流程 -------------------------
def main():
    print("=" * 60)
    print("  VMT Reply Ingest Engine v1.0  |  回覆迴路閉合 + 下拉選單")
    print("=" * 60)
    ss = load_ssot()
    if ss is None:
        return
    open_ids = {i["issueId"] for i in ss["issues"]}   # 系統認得的所有 ISS
    msgs = source_outlook() or source_inbox_file() or source_sample()
    replies = parse_replies(msgs, open_ids)
    print("[解析] 擷取 %d 筆可對應回覆" % len(replies))
    changed = apply_replies(ss, replies)
    if changed:
        save_ssot(ss)
    print("[寫回] 本次收斂 %d 筆 (其餘為去重或無對應)" % len(changed))
    for c in changed:
        print("        %s %s: %s -> %s (ETA %s)" % (c["issueId"], c["caseId"], c["prev"], c["status"], c["eta"]))

    os.makedirs(OUT_DIR, exist_ok=True)
    form = build_reply_form(ss)
    dash = build_loop_dashboard(ss, changed)
    form_path = os.path.join(OUT_DIR, "ReplyForm.html")
    dash_path = os.path.join(OUT_DIR, "ReplyLoop.html")
    open(form_path, "w", encoding="utf-8").write(form)
    open(dash_path, "w", encoding="utf-8").write(dash)
    print("[輸出] 互動回覆表:", form_path)
    print("[輸出] 迴路儀表板:", dash_path)
    try:
        if os.name == "nt" and "--no-open" not in sys.argv:
            os.startfile(dash_path)  # noqa
    except Exception:
        pass
    print("完成.")

if __name__ == "__main__":
    main()
