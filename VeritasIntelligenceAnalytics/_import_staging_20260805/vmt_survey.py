# -*- coding: utf-8 -*-
"""
============================================================================
 VMT Onboarding Survey v1.0  --  選擇式問卷 -> 系統參數 (零分析門檻使用者)
----------------------------------------------------------------------------
 設計原則 (與原稿的差異, 刻意為之):
   1. 每一題都直接驅動一個系統旋鈕 — 不收「答了也沒用」的資料.
   2. 問「你要系統多幫你」不問「你有多弱」— 偏好題答案誠實, 自評能力題不誠實.
   3. 不建心理側寫 (壓力/分心/風險檔案) — 那是監控素材, 不是系統參數.
   4. 滑鼠專用: chip 選擇, 預設值已選, 可一鍵全部接受預設.
 迴路: SurveyForm.html (chips) -> ==VMT-SURVEY== token -> survey_inbox.txt
       -> 本引擎評分 -> data/user_profiles.json (append-only)
       -> 產 convergence/system 覆寫建議 (自動化強度/提醒頻率/確認預算...).
============================================================================
"""
import os, re, sys, json, html, datetime as dt

VMT_ROOT = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
DATA_DIR = os.path.join(VMT_ROOT, "data")
OUT_DIR  = os.path.join(VMT_ROOT, "reports")
INBOX    = os.path.join(VMT_ROOT, "survey_inbox.txt")
PROFILES = os.path.join(DATA_DIR, "user_profiles.jsonl")

def hsafe(s): return html.escape("" if s is None else str(s))

# ---------------------------------------------------------------------------
# 問卷定義: 每題 -> knob (系統旋鈕) + 每個選項的參數效果. 全選擇題.
# 三選項為主, 預設(default)已標, UI 預選 -> 一鍵接受即可完成.
# ---------------------------------------------------------------------------
SURVEY = [
 {"sec": "A 工作來源", "qs": [
   {"id": "Q1", "q": "你的工作主要從哪裡來？", "knob": "ingest_priority",
    "opts": [("Email 為主", {"ingest": "outlook"}),
             ("主管口頭/會議", {"ingest": "manual"}),
             ("系統/表單", {"ingest": "sheet"})], "default": 0},
   {"id": "Q2", "q": "要不要系統每天自動幫你從 Email 抓出待辦？", "knob": "auto_ingest",
    "opts": [("要, 全自動抓", {"auto_ingest": 2}),
             ("抓了先給我確認", {"auto_ingest": 1}),
             ("我自己填", {"auto_ingest": 0})], "default": 1},
 ]},
 {"sec": "B 整理方式", "qs": [
   {"id": "Q3", "q": "待辦清單想怎麼維護？", "knob": "todo_mode",
    "opts": [("系統全代管(我只看)", {"todo": "auto"}),
             ("系統列, 我勾", {"todo": "assist"}),
             ("我自己管", {"todo": "self"})], "default": 1},
   {"id": "Q4", "q": "要不要系統自動幫 Email 分類到案件？", "knob": "auto_classify",
    "opts": [("要, 分錯我再改", {"auto_classify": 2}),
             ("低信心的先問我", {"auto_classify": 1}),
             ("不用", {"auto_classify": 0})], "default": 1},
 ]},
 {"sec": "C 優先順序", "qs": [
   {"id": "Q5", "q": "每天的做事順序想怎麼決定？", "knob": "priority_mode",
    "opts": [("系統排好我照做", {"priority": "auto"}),
             ("系統建議, 我可調", {"priority": "suggest"}),
             ("我自己排", {"priority": "self"})], "default": 1},
   {"id": "Q6", "q": "快到期的事, 要系統多早提醒？", "knob": "remind_lead",
    "opts": [("前 2 天就提醒", {"remind_lead_days": 2}),
             ("前 1 天", {"remind_lead_days": 1}),
             ("當天就好", {"remind_lead_days": 0})], "default": 1},
 ]},
 {"sec": "D 節奏", "qs": [
   {"id": "Q7", "q": "提醒的頻率你能接受多少？", "knob": "remind_freq",
    "opts": [("一天多次沒關係", {"remind_per_day": 3}),
             ("一天一次就好", {"remind_per_day": 1}),
             ("盡量少吵我", {"remind_per_day": 0})], "default": 1},
   {"id": "Q8", "q": "系統要你確認事情時, 一次最多問幾題？", "knob": "queue_budget",
    "opts": [("10 題內可以", {"max_questions": 10}),
             ("5 題內", {"max_questions": 5}),
             ("3 題內, 越少越好", {"max_questions": 3})], "default": 1},
 ]},
 {"sec": "E 郵件協助", "qs": [
   {"id": "Q9", "q": "追蹤信要系統幫到什麼程度？", "knob": "mail_assist",
    "opts": [("整封寫好我按送出", {"mail_assist": 2}),
             ("寫好草稿我改一下", {"mail_assist": 1}),
             ("給我範本就好", {"mail_assist": 0})], "default": 1},
   {"id": "Q10", "q": "信件內容偏好？", "knob": "mail_style",
    "opts": [("越短越好", {"mail_style": "short"}),
             ("標準", {"mail_style": "std"}),
             ("詳細一點", {"mail_style": "long"})], "default": 1},
 ]},
 {"sec": "F 自動化總強度", "qs": [
   {"id": "Q11", "q": "整體來說, 你希望系統？", "knob": "automation_level",
    "opts": [("盡量全自動, 錯了我再改", {"level": 3, "auto_accept_delta": -0.10}),
             ("自動+關鍵事項問我", {"level": 2, "auto_accept_delta": 0.0}),
             ("每件事都先問我", {"level": 1, "auto_accept_delta": +0.10})], "default": 1},
   {"id": "Q12", "q": "系統判斷錯誤時你偏好？", "knob": "error_pref",
    "opts": [("寧可它多做, 我事後改", {"err": "act"}),
             ("寧可它先問, 慢一點沒關係", {"err": "ask"})], "default": 1},
 ]},
]

ALL_Q = [q for s in SURVEY for q in s["qs"]]

# ---------------------------------------------------------------------------
# 泛用化: 問卷包 (pack) 驅動 — 換行業只換 JSON, 引擎不動.
# 尋找順序: $VMT_SURVEY_PACK 指定 > VMT_ROOT/survey_pack.json > 腳本旁 survey_pack*.json > 內建通用題庫
# pack 結構: {"name","sections":[{"sec","qs":[{"id","q","knob","opts":[[label,{effects}],...],"default":n}]}]}
# opts 的 effects 直接併入 overrides; 以 "domain." 開頭的 key 會收進 overrides["domain"].
# ---------------------------------------------------------------------------
def load_pack():
    global SURVEY, ALL_Q, PACK_NAME
    cands = []
    envp = os.environ.get("VMT_SURVEY_PACK")
    if envp: cands.append(envp)
    cands.append(os.path.join(VMT_ROOT, "survey_pack.json"))
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        for fn in sorted(os.listdir(here)):
            if fn.startswith("survey_pack") and fn.endswith(".json"):
                cands.append(os.path.join(here, fn))
    except Exception:
        pass
    for p in cands:
        if p and os.path.exists(p):
            try:
                pk = json.load(open(p, encoding="utf-8"))
                secs = []
                for s in pk.get("sections", []):
                    qs = []
                    for q in s.get("qs", []):
                        qs.append({"id": q["id"], "q": q["q"], "knob": q.get("knob", ""),
                                   "opts": [(o[0], o[1]) for o in q["opts"]],
                                   "default": int(q.get("default", 1)),
                                   "multi": bool(q.get("multi", False))})
                    secs.append({"sec": s.get("sec", ""), "qs": qs})
                if secs:
                    SURVEY = secs
                    ALL_Q = [q for s in SURVEY for q in s["qs"]]
                    PACK_NAME = pk.get("name", os.path.basename(p))
                    print("[問卷包] 載入: %s (%d 題) <- %s" % (PACK_NAME, len(ALL_Q), os.path.basename(p)))
                    return
            except Exception as e:
                print("[問卷包] %s 解析失敗(%s), 換下一個" % (os.path.basename(p), type(e).__name__))
    PACK_NAME = "通用內建"
    print("[問卷包] 使用內建通用題庫 (%d 題)" % len(ALL_Q))

PACK_NAME = "通用內建"

# ---------------------------------------------------------------------------
def build_form(out_path):
    cards = ""
    for sec in SURVEY:
        cards += "<h2>%s</h2>" % hsafe(sec["sec"])
        for q in sec["qs"]:
            multi = q.get("multi", False)
            defv = q["default"]
            defset = set(defv if isinstance(defv, list) else [defv])
            chips = ""
            for j, (label, _fx) in enumerate(q["opts"]):
                sel = "sel" if j in defset else ""
                chips += ("<span class='chip %s' data-v='%d' onclick='pick(this)'>%s</span>"
                          % (sel, j, hsafe(label)))
            hint = "<span class='multi-hint'>可複選</span>" if multi else ""
            valstr = ",".join(str(x) for x in sorted(defset))
            cards += ("<div class='card' data-q='%s' data-val='%s'%s>"
                      "<div class='qt'>%s %s<span class='qid'>%s</span></div>"
                      "<div class='chips'>%s</div></div>"
                      % (hsafe(q["id"]), valstr, (" data-multi='1'" if multi else ""),
                         hsafe(q["q"]), hint, hsafe(q["id"]), chips))
    nows = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    tmpl = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>VMT 上手問卷</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--blue:#4c78a8;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px;max-width:860px;margin:0 auto}
.seal{display:inline-flex;width:44px;height:44px;background:#4c78a8;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 20px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:22px 0 10px;text-transform:uppercase}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:12px 14px;margin-bottom:10px}
.qt{font-size:14px}.qid{font-family:"DM Mono",monospace;font-size:11px;color:#aaa;margin-left:6px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.chip{cursor:pointer;user-select:none;font-size:13px;padding:6px 14px;border:1px solid var(--hair);border-radius:16px;background:#fff}
.chip:hover{border-color:var(--blue)}
.chip.sel{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:600}
.multi-hint{font-size:11px;color:#439a9a;border:1px solid #bfe0da;border-radius:10px;padding:1px 8px;margin-left:6px}
.prog{position:sticky;top:0;background:var(--bg);padding:8px 0 6px;z-index:5}
.progbar{height:6px;background:#e6e4de;border-radius:3px;overflow:hidden}
.progfill{height:6px;background:linear-gradient(90deg,#4c78a8,#439a9a);width:100%;transition:.2s}
.progtxt{font-family:"DM Mono",monospace;font-size:11px;color:#777;margin-top:4px}
.btnbig{background:#5a9e6f;color:#fff;border:none;border-radius:4px;padding:12px 22px;font-size:15px;font-weight:700;cursor:pointer;margin-right:8px}
.btn{background:var(--blue);color:#fff;border:none;border-radius:3px;padding:9px 16px;font-size:13px;cursor:pointer}
pre{background:#1e1d1a;color:#e8e6e0;font-family:"DM Mono",monospace;font-size:12px;padding:14px;border-radius:3px;white-space:pre-wrap;margin-top:10px}
.note{background:#f0f6f4;border-left:5px solid #439a9a;padding:10px 14px;font-size:12px;color:#2f5d52;border-radius:3px;margin:10px 0}
input{font-family:inherit;font-size:13px;padding:6px 10px;border:1px solid var(--hair);border-radius:3px}
footer{margin-top:26px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">問</div><div><h1>VMT 上手問卷 — 選一選, 系統照你的方式幫你</h1>
<div class="sub">{{NOW}} · 12 題全選擇 · 每題已預選常見答案, 全部同意就一鍵完成</div></div></header>
<div class="strip"></div>
<div class="prog"><div class="progbar"><div class="progfill" id="pf"></div></div><div class="progtxt" id="pt"></div></div>
<div class="note">這不是考試, 沒有對錯。你選「要系統幫多少」, 系統就調成那樣; 之後隨時可以重填改設定。答案只用來調整你自己的系統參數。標「可複選」的題目點多個都算。</div>
<div class="card"><div class="qt">你的名字/代號 (讓設定跟著你)</div>
<input id="uname" placeholder="例: Tony" style="margin-top:8px;width:220px"></div>
{{CARDS}}
<div style="margin-top:14px">
<button class="btnbig" onclick="gen()">✓ 完成 (用目前選擇)</button>
<button class="btn" style="background:#439a9a" onclick="cp()">複製結果</button></div>
<pre id="out">（按「完成」產生設定 token → 複製 → 貼進 survey_inbox.txt → 重跑系統即套用）</pre>
<footer>vmt_survey v1.0 | 每題直接對應一個系統參數 | 只調你自己的設定, 不建任何評比檔案</footer>
<script>
function upd(){var cs=document.querySelectorAll('.card[data-q]');var done=0;
 cs.forEach(function(c){if((c.getAttribute('data-val')||'').length>0)done++;});
 var pct=Math.round(100*done/Math.max(1,cs.length));
 document.getElementById('pf').style.width=pct+'%';
 document.getElementById('pt').innerText='已完成 '+done+'/'+cs.length+' 題 ('+pct+'%) — 全部已有預設值, 同意即可直接按「完成」';}
function pick(el){var card=el.closest('.card');
 if(card.getAttribute('data-multi')==='1'){
   el.classList.toggle('sel');
   var vs=[];card.querySelectorAll('.chip.sel').forEach(function(c){vs.push(c.getAttribute('data-v'));});
   card.setAttribute('data-val',vs.join(','));
 } else {
   card.querySelectorAll('.chip').forEach(function(c){c.classList.remove('sel');});
   el.classList.add('sel');card.setAttribute('data-val',el.getAttribute('data-v'));
 }
 upd();}
function gen(){var u=(document.getElementById('uname').value||'user').trim();var parts=[];
 document.querySelectorAll('.card[data-q]').forEach(function(c){var v=c.getAttribute('data-val');if(v&&v.length)parts.push(c.getAttribute('data-q')+':'+v);});
 document.getElementById('out').innerText='==VMT-SURVEY== '+u+' | '+parts.join(' | ');}
function cp(){navigator.clipboard.writeText(document.getElementById('out').innerText).then(function(){alert('已複製，貼進 survey_inbox.txt 後重跑');});}
upd();
</script></body></html>"""
    open(out_path, "w", encoding="utf-8").write(
        tmpl.replace("{{NOW}}", nows).replace("{{CARDS}}", cards))

# ---------------------------------------------------------------------------
def ingest():
    """survey_inbox.txt 的 ==VMT-SURVEY== token -> 使用者答案 dict"""
    if not os.path.exists(INBOX): return {}
    txt = open(INBOX, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"==VMT-SURVEY==\s*([^\|\n]+)\|(.+)", txt):
        user = m.group(1).strip()
        ans = {}
        for qm in re.finditer(r"(Q\d+)\s*:\s*([\d,]+)", m.group(2)):
            vals = [int(x) for x in qm.group(2).split(",") if x.strip().isdigit()]
            if vals: ans[qm.group(1)] = vals
        if ans: out[user] = ans
    return out

def score(ans):
    """答案 -> 參數效果合併 + 簡單維度分數 (assist_need 0-100)"""
    fx = {}
    assist_pts = 0; assist_max = 0
    for q in ALL_Q:
        raw = ans.get(q["id"], q["default"])
        js = raw if isinstance(raw, list) else [raw]
        js = [max(0, min(len(q["opts"]) - 1, int(j))) for j in js]
        if not q.get("multi"):
            js = js[:1]
        labels_sel = []
        for j in js:
            label, eff = q["opts"][j]
            labels_sel.append(label)
            for k, v in eff.items():
                if k.startswith("domain.") and isinstance(v, list) and isinstance(fx.get(k), list):
                    for x in v:
                        if x not in fx[k]: fx[k].append(x)
                else:
                    fx[k] = list(v) if isinstance(v, list) else v
        if not q.get("multi"):
            j = js[0]
            # 選項序位: 0=最自動(要系統幫最多) -> 序位越前 assist 越高
            assist_pts += (len(q["opts"]) - 1 - j)
            assist_max += (len(q["opts"]) - 1)
        fx["_ans_" + q["id"]] = " / ".join(labels_sel)
    assist_need = round(100 * assist_pts / max(1, assist_max))  # 高=要系統多幫
    self_serve = 100 - assist_need                              # 高=偏好自己來
    level = fx.get("level", 2)
    return fx, {"assist_need": assist_need, "self_serve": self_serve, "automation_level": level}

def apply_overrides(fx, dims):
    """把問卷結果轉成其他引擎讀得懂的覆寫檔 (建議值, 不強改參數檔)"""
    domain = {}
    for k, v in list(fx.items()):
        if k.startswith("domain."):
            key = k.split(".", 1)[1]
            if isinstance(v, list):
                domain.setdefault(key, [])
                for x in v:
                    if x not in domain[key]: domain[key].append(x)
            else:
                domain[key] = v
    ov = {
        "generated": dt.datetime.now().isoformat(),
        "pack": PACK_NAME,
        "automation_level": dims["automation_level"],
        "convergence": {
            "auto_accept_delta": fx.get("auto_accept_delta", 0.0),
            "max_questions_per_round": fx.get("max_questions", 5)
        },
        "mailer": {"assist": fx.get("mail_assist", 1), "style": fx.get("mail_style", "std"),
                   "send_window": fx.get("send_window", "evening")},
        "reminders": {"lead_days": fx.get("remind_lead_days", 1), "per_day": fx.get("remind_per_day", 1)},
        "ingest": {"source": fx.get("ingest", "outlook"), "auto": fx.get("auto_ingest", 1),
                   "auto_classify": fx.get("auto_classify", 1)},
        "priority_mode": fx.get("priority", "suggest"),
        "todo_mode": fx.get("todo", "assist"),
        "error_preference": fx.get("err", "ask"),
        "domain": domain,
    }
    return ov

def main():
    print("=" * 60); print("  VMT Onboarding Survey v1.1  |  泛用問卷包 -> 系統參數"); print("=" * 60)
    load_pack()
    os.makedirs(DATA_DIR, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)
    form = os.path.join(OUT_DIR, "SurveyForm.html")
    build_form(form)
    print("[表單] %s (12 題全 chip, 預設已選, 可一鍵完成)" % form)
    answers = ingest()
    if not answers:
        print("[答案] survey_inbox.txt 尚無 ==VMT-SURVEY== token — 填完貼入後重跑即套用")
    for user, ans in answers.items():
        fx, dims = score(ans)
        ov = apply_overrides(fx, dims)
        rec = {"ts": dt.datetime.now().isoformat(), "user": user, "answers": ans,
               "dims": dims, "overrides": ov}
        with open(PROFILES, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        ov_path = os.path.join(DATA_DIR, "overrides_%s.json" % re.sub(r"[^0-9A-Za-z_\-]", "_", user))
        json.dump(ov, open(ov_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("[評分] %s: 協助需求 %d/100, 自動化等級 L%d -> %s" %
              (user, dims["assist_need"], dims["automation_level"], os.path.basename(ov_path)))
        print("        確認預算=%d 題/輪, auto_accept 調整 %+0.2f, 提醒 %d 次/天(提前 %d 天), 郵件協助 L%d" %
              (ov["convergence"]["max_questions_per_round"], ov["convergence"]["auto_accept_delta"],
               ov["reminders"]["per_day"], ov["reminders"]["lead_days"], ov["mailer"]["assist"]))
    try:
        if os.name == "nt" and "--no-open" not in sys.argv: os.startfile(form)  # noqa
    except Exception: pass
    print("完成.")

if __name__ == "__main__":
    main()
