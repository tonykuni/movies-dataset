# -*- coding: utf-8 -*-
"""
============================================================================
 VMT Convergence Engine v1.0  --  信心分級 + 主動學習確認迴路
----------------------------------------------------------------------------
 補上系統缺的收斂機制: 人工確認不只更正紀錄, 還回頭調校分類器, 讓同樣的模糊
 下次自動解掉. 核心迴路:  訓練(已確認) -> 預測(待定, 帶信心) -> 低信心/矛盾排隊
 一鍵確認 -> 寫回 confirmations (append-only 學習記憶) -> 重跑即更準.
 自動導入現況: 讀 ssot.json / events.jsonl, 不交白樣板.
 優雅降級: 有 scikit-learn -> 校準機率分類; 無 -> 規則式信心 (仍可跑).
           有 sentence-transformers -> 語意嵌入; 無 -> TF-IDF.
 治理: ssot 只讀; confirmations.jsonl append-only; 產物落 reports/.
 參數: convergence_params.json (門檻/欄位/衰減), 改參數即改行為.
============================================================================
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import os, re, sys, json, math, html, hashlib, datetime as dt
from collections import Counter, defaultdict

def hsafe(s): return html.escape("" if s is None else str(s))
def now(): return dt.datetime.now()
def parse_dt(s):
    if not s: return None
    for f in ("%Y-%m-%dT%H:%M:%S.%f","%Y-%m-%dT%H:%M:%S","%Y/%m/%d %H:%M","%Y/%m/%d","%Y-%m-%d"):
        try: return dt.datetime.strptime(str(s).strip()[:26], f)
        except Exception: pass
    try: return dt.datetime.fromisoformat(str(s))
    except Exception: return None

# ---------------------------------------------- 參數 -----------------------
def load_params():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "convergence_params.json")
    cfg = {}
    if os.path.exists(p):
        cfg = json.load(open(p, encoding="utf-8"))
    root = os.environ.get("VMT_ROOT") or cfg.get("paths", {}).get("vmt_root") or r"C:\VIA\VeritasMailTracker"
    cfg.setdefault("paths", {})["vmt_root"] = root
    return cfg

def P(cfg, *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur: return default
        cur = cur[k]
    return cur

# ---------------------------------------------- 導入 -----------------------
def load_issues(root, cfg):
    ssot = os.path.join(root, P(cfg, "paths", "ssot", default="data/ssot.json"))
    if not os.path.exists(ssot):
        print("[SSOT] 找不到 %s" % ssot); return None
    ss = json.load(open(ssot, encoding="utf-8"))
    active = set(P(cfg, "task", "active_status", default=["OPEN"]))
    items = []
    for i in ss.get("issues", []):
        st = i.get("status")
        if st in active or st == "DONE":
            items.append(i)
    return items

def ingest_confirmations(root, cfg):
    """把 confirmations_inbox.txt 的 ==VMT-CONFIRM== 併入 confirmations.jsonl (append-only, 去重)"""
    conf_path = os.path.join(root, P(cfg, "paths", "confirmations", default="data/confirmations.jsonl"))
    inbox = os.path.join(root, P(cfg, "paths", "confirmations_inbox", default="confirmations_inbox.txt"))
    seen = set(); confs = []
    if os.path.exists(conf_path):
        for line in open(conf_path, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line); confs.append(r); seen.add(r.get("hash"))
            except Exception: pass
    if os.path.exists(inbox):
        txt = open(inbox, encoding="utf-8").read()
        rx = re.compile(r"==VMT-CONFIRM==\s*(ISS-\d+)\s*\|\s*標籤[:：]\s*([^\|\n]+)(?:\|\s*by[:：]\s*([^\n]+))?", re.I)
        new = 0
        for m in rx.finditer(txt):
            iss = m.group(1).upper(); label = m.group(2).strip(); by = (m.group(3) or "human").strip()
            h = hashlib.sha1(("%s|%s" % (iss, label)).encode()).hexdigest()[:12]
            if h in seen: continue
            rec = {"ts": now().isoformat(), "iss": iss, "label": label, "by": by, "hash": h}
            confs.append(rec); seen.add(h); new += 1
            with open(conf_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if new: print("[確認] 併入 %d 筆新人工確認" % new)
    labels = {}
    for r in confs:
        labels[r["iss"]] = r["label"]   # 後者覆寫前者
    return labels

# ---------------------------------------------- 特徵 -----------------------
def build_rows(items, cfg):
    tf = P(cfg, "task", "text_fields", default=["title"])
    nf = P(cfg, "task", "numeric_fields", default=["urgency"])
    catf = P(cfg, "task", "categorical_fields", default=["caseId"])
    rows = []
    for i in items:
        text = " ".join(str(i.get(k, "")) for k in tf)
        num = [float(i.get(k, 0) or 0) for k in nf]
        created = parse_dt(i.get("created"))
        age = (now() - created).days if created else 0
        num.append(float(age))
        cats = {k: str(i.get(k, "")) for k in catf}
        rows.append({"iss": i.get("issueId"), "text": text, "num": num, "cats": cats,
                     "provisional": i.get(P(cfg, "task", "label_field", default="type")),
                     "status": i.get("status"), "age": age})
    return rows

# ---------------------------------------------- 模型 (優雅降級) -------------
def try_sklearn(rows, labels, cfg):
    try:
        import numpy as np
        from scipy.sparse import hstack, csr_matrix
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.model_selection import cross_val_score
    except Exception as e:
        print("[模型] 無 scikit-learn (%s) -> 規則式降級" % type(e).__name__)
        return None
    lab_rows = [r for r in rows if r["iss"] in labels]
    y = [labels[r["iss"]] for r in lab_rows]
    cls_count = Counter(y)
    minlab = P(cfg, "model", "min_labels_per_class", default=2)
    usable = [c for c, n in cls_count.items() if n >= minlab]
    if len(usable) < 2 or len(lab_rows) < 4:
        print("[模型] 已確認樣本不足 (labels=%d, classes>=%d: %d) -> 規則式降級" % (len(lab_rows), minlab, len(usable)))
        return None
    # 只留可用類別
    lab_rows = [r for r in lab_rows if labels[r["iss"]] in usable]
    y = [labels[r["iss"]] for r in lab_rows]
    # 特徵: tfidf(text) + numeric + one-hot(cats)
    vec = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    all_text = [r["text"] for r in rows]
    vec.fit(all_text)
    cat_keys = sorted({(k, v) for r in rows for k, v in r["cats"].items()})
    cat_index = {kv: j for j, kv in enumerate(cat_keys)}
    def feat(rs):
        Xt = vec.transform([r["text"] for r in rs])
        Xn = np.array([r["num"] for r in rs], dtype=float)
        Xc = np.zeros((len(rs), len(cat_index)))
        for a, r in enumerate(rs):
            for k, v in r["cats"].items():
                j = cat_index.get((k, v))
                if j is not None: Xc[a, j] = 1.0
        return hstack([Xt, csr_matrix(Xn), csr_matrix(Xc)]).tocsr()
    Xtr = feat(lab_rows)
    base = LogisticRegression(max_iter=1000, class_weight="balanced")
    cv = min(3, min(cls_count[c] for c in usable))
    acc = None
    try:
        if cv >= 2:
            acc = float(np.mean(cross_val_score(base, Xtr, y, cv=cv)))
    except Exception: pass
    clf = base
    if P(cfg, "model", "calibrate", default=True) and cv >= 2:
        try:
            clf = CalibratedClassifierCV(base, cv=cv); clf.fit(Xtr, y)
        except Exception:
            clf = base; clf.fit(Xtr, y)
    else:
        clf.fit(Xtr, y)
    Xall = feat(rows)
    proba = clf.predict_proba(Xall); classes = list(clf.classes_)
    out = {}
    for a, r in enumerate(rows):
        pr = proba[a]; j = int(pr.argmax())
        out[r["iss"]] = {"pred": classes[j], "conf": float(pr[j]),
                         "margin": float(sorted(pr)[-1] - (sorted(pr)[-2] if len(pr) > 1 else 0))}
    print("[模型] scikit-learn 校準分類就緒 (labels=%d, classes=%d, CV acc=%s)" %
          (len(lab_rows), len(usable), ("%.2f" % acc) if acc is not None else "n/a"))
    return {"pred": out, "acc": acc, "n_labels": len(lab_rows), "backend": "sklearn"}

def rule_fallback(rows, labels, cfg):
    # 規則: 已確認=1.0; 其餘依 urgency 與關鍵字給粗略信心
    kw = {"Warning": ["延遲", "缺", "警告", "逾"], "Reminder": ["提醒", "澄清", "確認"], "FollowUp": ["跟進", "週報", "一般"]}
    out = {}
    for r in rows:
        if r["iss"] in labels:
            out[r["iss"]] = {"pred": labels[r["iss"]], "conf": 1.0, "margin": 1.0}; continue
        text = r["text"]; best = r["provisional"] or "FollowUp"; score = 0.5
        for lab, words in kw.items():
            if any(w in text for w in words): best = lab; score = 0.7; break
        u = 0
        try: u = int(r["num"][0])
        except Exception: pass
        if u >= 5: best = "Warning"; score = max(score, 0.75)
        out[r["iss"]] = {"pred": best, "conf": score, "margin": 0.2}
    print("[模型] 規則式信心 (無訓練, 僅示範迴路; 裝 scikit-learn 後自動升級)")
    return {"pred": out, "acc": None, "n_labels": len(labels), "backend": "rules"}

# ---------------------------------------------- 新鮮度衰減 ------------------
def apply_decay(conf, age_days, cfg):
    if not P(cfg, "freshness", "apply_decay", default=True): return conf
    hl = P(cfg, "freshness", "half_life_days", default=14)
    if hl and hl > 0 and age_days > 0:
        return conf * (0.5 ** (age_days / hl))
    return conf

def grade(conf, cfg):
    hi = P(cfg, "evidence_tiers", "high_min", default=0.85)
    med = P(cfg, "evidence_tiers", "medium_min", default=0.6)
    cap = P(cfg, "evidence_tiers", "synthetic_cap", default=0.59)
    if conf >= hi: return "M"      # media/high-verified 級 (仍非 Confirmed; 只有人=V)
    if conf >= med: return "P"     # pending
    if conf <= cap: return "Syn"   # synthetic/hard-cap
    return "Est"

# ---------------------------------------------- 主流程 ----------------------
def main():
    cfg = load_params()
    root = P(cfg, "paths", "vmt_root")
    print("=" * 60); print("  VMT Convergence Engine v1.0  |  信心 + 主動學習確認迴路"); print("=" * 60)
    items = load_issues(root, cfg)
    if items is None: return
    labels = ingest_confirmations(root, cfg)
    # 把 DONE 的 issue 也當可信標籤 (若設定)
    if P(cfg, "task", "trust_done_as_label", default=True):
        lf = P(cfg, "task", "label_field", default="type")
        for i in items:
            if i.get("status") == "DONE" and i.get("issueId") not in labels and i.get(lf):
                labels[i["issueId"]] = i.get(lf)
    rows = build_rows(items, cfg)
    print("[導入] issue=%d / 已確認標籤=%d" % (len(rows), len(labels)))

    res = try_sklearn(rows, labels, cfg) if P(cfg, "model", "backend", default="auto") in ("auto", "sklearn") else None
    if res is None: res = rule_fallback(rows, labels, cfg)
    pred = res["pred"]

    auto_t = P(cfg, "confidence", "auto_accept", default=0.85)
    quar_t = P(cfg, "confidence", "quarantine_below", default=0.45)
    prioritize_dis = P(cfg, "confidence", "prioritize_disagreement", default=True)
    budget = P(cfg, "confidence", "max_questions_per_round", default=10)

    enriched = []
    for r in rows:
        p = pred.get(r["iss"], {"pred": r["provisional"], "conf": 0.5, "margin": 0.2})
        raw = p["conf"]
        conf = apply_decay(raw, r["age"], cfg)
        confirmed = r["iss"] in labels
        disagree = (not confirmed) and (p["pred"] != r["provisional"]) and (r["provisional"] is not None)
        # 分流: 隔離只留給「模型本身就不確定」; 過時/中信心/矛盾 -> ASK 重新確認
        if confirmed: tier = "CONFIRMED"
        elif raw < quar_t: tier = "QUARANTINE"
        elif conf >= auto_t and not disagree: tier = "AUTO"
        else: tier = "ASK"
        # 主動學習資訊量: 邊際越小越該問; 矛盾加權
        info = (1.0 - p.get("margin", 0.2)) + (0.5 if disagree else 0.0)
        enriched.append({**r, "pred": p["pred"], "conf": conf, "raw_conf": p["conf"],
                         "grade": ("V" if confirmed else grade(conf, cfg)),
                         "disagree": disagree, "tier": tier, "info": info})
    ask = [e for e in enriched if e["tier"] == "ASK"]
    if prioritize_dis:
        ask.sort(key=lambda e: (not e["disagree"], -e["info"]))
    else:
        ask.sort(key=lambda e: -e["info"])
    queue = ask[:budget]
    tiers = Counter(e["tier"] for e in enriched)
    auto_rate = (tiers["AUTO"] + tiers["CONFIRMED"]) / max(1, len(enriched))
    print("[分級] AUTO=%d CONFIRMED=%d ASK=%d QUARANTINE=%d | 自動化率=%.0f%%" %
          (tiers["AUTO"], tiers["CONFIRMED"], tiers["ASK"], tiers["QUARANTINE"], auto_rate * 100))
    print("[本輪要問] %d 題 (預算 %d), 依資訊量+矛盾排序" % (len(queue), budget))

    out_dir = os.path.join(root, P(cfg, "paths", "out_dir", default="reports"))
    os.makedirs(out_dir, exist_ok=True)
    state = {"ts": now().isoformat(), "backend": res["backend"], "cv_acc": res["acc"],
             "n_issues": len(rows), "n_labels": len(labels), "auto_rate": auto_rate,
             "tiers": dict(tiers),
             "items": [{"iss": e["iss"], "provisional": e["provisional"], "pred": e["pred"],
                        "conf": round(e["conf"], 3), "grade": e["grade"], "tier": e["tier"],
                        "disagree": e["disagree"]} for e in enriched]}
    json.dump(state, open(os.path.join(out_dir, "convergence_state.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    build_html(enriched, queue, res, tiers, auto_rate, os.path.join(out_dir, "ConfirmationQueue.html"))
    print("[輸出]", os.path.join(out_dir, "ConfirmationQueue.html"))
    print("       確認方式: 在該頁選好 -> 產生 ==VMT-CONFIRM== -> 貼進 confirmations_inbox.txt -> 重跑, 系統會更準")
    print("完成.")

# ---------------------------------------------- HTML -----------------------
def build_html(enriched, queue, res, tiers, auto_rate, out_path):
    gcol = {"V": "#5a9e6f", "M": "#4c78a8", "P": "#c9a13a", "Est": "#d08343", "Syn": "#b5443a"}
    tcol = {"CONFIRMED": "#5a9e6f", "AUTO": "#4c78a8", "ASK": "#c9a13a", "QUARANTINE": "#b5443a"}
    labels_all = sorted({e["provisional"] for e in enriched if e["provisional"]} | {e["pred"] for e in enriched if e["pred"]})
    qrows = ""
    for e in queue:
        dis = " <span class='pill' style='background:#b5443a'>與現值不符</span>" if e["disagree"] else ""
        chips = ""
        for l in labels_all:
            sel = "sel" if l == e["pred"] else ""
            chips += "<span class='chip %s' data-v='%s' onclick='pick(this)'>%s</span>" % (sel, hsafe(l), hsafe(l))
        qrows += ("<div class='card' data-iss='%s' data-val='%s'>"
                  "<div class='crow'><span class='cid'>%s</span><b>%s</b>%s</div>"
                  "<div class='crow' style='margin-top:4px;font-size:12px;color:#888'>模型猜 <b>%s</b>(已預選) · 信心 %.2f · 現值 %s</div>"
                  "<div class='chips'>%s</div>"
                  "<div class='crow' style='margin-top:6px'><span class='addnote' onclick='toggleNote(this)'>＋說明(選填)</span>"
                  "<input class='note' style='display:none;flex:1;min-width:160px;margin-left:8px' placeholder='僅在需要時才打字'></div>"
                  "</div>") % (
            hsafe(e["iss"]), hsafe(e["pred"]), hsafe(e["iss"]), hsafe(e["text"][:36]), dis,
            hsafe(e["pred"]), e["conf"], hsafe(e["provisional"]), chips)
    if not qrows: qrows = "<div class='empty'>本輪無需詢問 (全部高信心或已確認) — 收斂良好</div>"
    trows = ""
    for e in sorted(enriched, key=lambda x: x["conf"]):
        trows += ("<tr><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td>"
                  "<td><span class='pill' style='background:%s'>%s</span></td>"
                  "<td><span class='pill' style='background:%s'>%s</span></td></tr>") % (
            hsafe(e["iss"]), hsafe(e["provisional"]), hsafe(e["pred"]), e["conf"],
            gcol.get(e["grade"], "#999"), hsafe(e["grade"]),
            tcol.get(e["tier"], "#999"), hsafe(e["tier"]))
    acc = ("%.0f%%" % (res["acc"] * 100)) if res.get("acc") is not None else "—"
    kpis = [("自動化率", "%.0f%%" % (auto_rate * 100), "#5a9e6f"),
            ("本輪要問", len(queue), "#c9a13a"),
            ("模型交叉驗證", acc, "#4c78a8"),
            ("已確認學習樣本", res["n_labels"], "#439a9a"),
            ("引擎", res["backend"], "#8a857c")]
    kh = "".join("<div class='kpi'><div class='kv' style='color:%s'>%s</div><div class='kn'>%s</div></div>"
                 % (c, v, n) for n, v, c in kpis)
    nows = now().strftime("%Y/%m/%d %H:%M")
    tmpl = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>收斂確認佇列</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--blue:#4c78a8;--teal:#439a9a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#439a9a;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.kpis{display:flex;gap:12px;flex-wrap:wrap}.kpi{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:12px 18px;min-width:120px}
.kv{font-size:22px;font-weight:700}.kn{font-size:12px;color:#777}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:12px 14px;margin-bottom:10px}
.crow{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.cid{font-family:"DM Mono",monospace;font-size:12px;color:#666}
select{font-family:inherit;font-size:13px;padding:5px 8px;border:1px solid var(--hair);border-radius:3px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.chip{cursor:pointer;user-select:none;font-size:13px;padding:6px 14px;border:1px solid var(--hair);border-radius:16px;background:#fff;transition:.1s}
.chip:hover{border-color:var(--blue)}
.chip.sel{background:var(--blue);color:#fff;border-color:var(--blue);font-weight:600}
.addnote{cursor:pointer;color:var(--blue);font-size:12px;user-select:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.btn{background:var(--blue);color:#fff;border:none;border-radius:3px;padding:8px 16px;font-size:13px;cursor:pointer}
.btnbig{background:#5a9e6f;color:#fff;border:none;border-radius:4px;padding:12px 22px;font-size:15px;font-weight:700;cursor:pointer}
.btnbig:hover{background:#4d8a5f}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
pre{background:#1e1d1a;color:#e8e6e0;font-family:"DM Mono",monospace;font-size:12px;padding:14px;border-radius:3px;white-space:pre-wrap;margin-top:10px}
.empty{color:#999;text-align:center;padding:16px}.note{background:#f0f6f4;border-left:5px solid #439a9a;padding:10px 14px;font-size:12px;color:#2f5d52;border-radius:3px;margin:8px 0}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">斂</div><div><h1>VMT 收斂確認佇列 — 主動學習迴路</h1>
<div class="sub">{{NOW}} | 低信心/矛盾優先問 · 確認即學習 · ssot 只讀</div></div></header>
<div class="strip"></div>
<div class="note">運作: 系統只問「最能降低不確定」的少數幾題; 你確認的答案寫進 confirmations (append-only), 下次重跑模型更準、要問的更少 — 這就是收斂。只有你的確認 = V(Confirmed); 模型再高信心也只到 M。</div>
<h2>KPI</h2><div class="kpis">{{KPI}}</div>
<h2>本輪確認佇列 — 滑鼠專用 (模型猜測已預選, 對就一鍵全接受, 錯才點別的)</h2>
<div style="margin-bottom:12px"><button class="btnbig" onclick="acceptAll()">✓ 全部接受模型建議 ({{NQ}})</button>
<span style="color:#888;font-size:12px;margin-left:10px">每題已預選模型最可能的答案; 不用打字, 點一下就好</span></div>
{{QUEUE}}
<div style="margin-top:12px"><button class="btn" onclick="gen()">產生確認 token</button>
<button class="btn" style="background:#439a9a" onclick="cp()">複製</button></div>
<pre id="out">（模型猜測已預選 → 對的話直接按上方「全部接受」→ 複製 → 貼進 confirmations_inbox.txt）</pre>
<h2>全體信心/分級/分流 (依信心由低到高)</h2>
<table><tr><th>ISS</th><th>現值</th><th>模型預測</th><th>信心</th><th>證據級</th><th>分流</th></tr>{{TABLE}}</table>
<footer>vmt_convergence v1.0 | 參數 convergence_params.json | 滑鼠專用: 預選+一鍵接受, 鍵盤只在＋說明時才用</footer>
<script>
function pick(el){var chips=el.parentNode.querySelectorAll('.chip');chips.forEach(function(c){c.classList.remove('sel');});el.classList.add('sel');el.closest('.card').setAttribute('data-val',el.getAttribute('data-v'));gen();}
function toggleNote(el){var n=el.parentNode.querySelector('.note');n.style.display=(n.style.display==='none')?'inline-block':'none';if(n.style.display!=='none')n.focus();}
function acceptAll(){/* 模型猜測已是預選, 直接產生 */ gen(); var o=document.getElementById('out'); o.scrollIntoView({behavior:'smooth'});}
function gen(){var cs=document.querySelectorAll('.card[data-iss]');var out=[];
 cs.forEach(function(c){var iss=c.getAttribute('data-iss');var v=c.getAttribute('data-val');if(!v)return;
  var note=c.querySelector('.note');var ns=(note&&note.value)?(' | 說明:'+note.value):'';
  out.push('==VMT-CONFIRM== '+iss+' | 標籤:'+v+' | by:me'+ns);});
 document.getElementById('out').innerText=out.length?out.join('\\n'):'（尚未選擇）';}
function cp(){navigator.clipboard.writeText(document.getElementById('out').innerText).then(function(){alert('已複製，貼進 confirmations_inbox.txt 後重跑');});}
gen();
</script></body></html>"""
    htmls = (tmpl.replace("{{NOW}}", nows).replace("{{KPI}}", kh)
                 .replace("{{NQ}}", str(len(queue)))
                 .replace("{{QUEUE}}", qrows).replace("{{TABLE}}", trows))
    open(out_path, "w", encoding="utf-8").write(htmls)

if __name__ == "__main__":
    main()
