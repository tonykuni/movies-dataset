# -*- coding: utf-8 -*-
r"""
engine_analytics.py  v1.3
=========================
v1.3(2026-08-08 操作員實跑報告驅動之中英文優化):
  1) 聚類/監督/相似度改用「詞級」向量(原 char_wb 2-4 字元 n-gram 把已斷詞文本
     再切碎 → 建議關鍵字出現「銀行 , 銀」「ea, eat, ats」碎片)。
  2) 領域詞典改以引擎目錄定位(原相對 cwd,deep 鏈 cwd 在 out\deep 永遠載不到
     → 「永豐銀行」被切成「豐銀行」);內建詞擴充銀行/品牌/財經術語,
     engines\domain_dict.txt 一行一詞可自行增補(只增不減)。
  3) 停用詞擴充中英信件樣板(fw/nt/星期X/透過/您好/親愛…);純拉丁 token 需 ≥3 字。
  4) 回覆延遲表增「型態」欄:no-reply/電子報/通知類系統寄件者誠實標注,
     OUTLIER 升級判定只對人類對口;engines\bulk_senders.txt 可自行增補樣式。
  5) 聚類樣本主旨過濾空值(原顯示「| |」)。
超級引擎進階分析層:自然語言處理 × 資料挖掘 × 流程探勘
讀取 email_super_engine.py 產出的 super_engine.db(唯讀),輸出 analytics_report.html。
不修改引擎本體與資料庫(只增不減)。

三大模組(缺套件自動跳過並提示):
  [NLP]  jieba 中英混合斷詞 + TF-IDF 各案關鍵詞
         scikit-learn KMeans 對「待歸類」信件聚類 → 建議新分類關鍵字(人工核准後增補規則)
  [DM]   回覆延遲離群偵測(IQR)/ 各案週信量趨勢 / 未結行動 Pareto(80/20 對口集中度)
         標籤共現分析(CASE × PMAREA 風險集中矩陣)
  [PM]   DFG 流程發現(pm4py,無則內建 fallback)/ 轉移平均等待時間 /
         催辦迴圈偵測 / 一致性檢查:實際軌跡 vs 標準流程 Request→Commitment→Delivery

用法:
  python engine_analytics.py --db ./engine_out/super_engine.db --outdir ./engine_out
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def progress(pct: int, label: str):
    print(f"@@PROGRESS|{pct}|{label}", file=sys.stderr, flush=True)


# ---- 可選套件偵測(優雅降級) ----
TOOLS = {}
try:
    import jieba
    jieba.setLogLevel(60)
    TOOLS["jieba"] = True
except ImportError:
    TOOLS["jieba"] = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    TOOLS["sklearn"] = True
except ImportError:
    TOOLS["sklearn"] = False
try:
    import pandas as pd
    TOOLS["pandas"] = True
except ImportError:
    TOOLS["pandas"] = False
try:
    import pm4py
    TOOLS["pm4py"] = True
except ImportError:
    TOOLS["pm4py"] = False

STANDARD_FLOW = ["Request", "Commitment", "Delivery"]   # BU 標準交付流程(可改)
STOPWORDS = set("""the a an and or of to in for on with is are was were be been this that
please could would kindly regards thanks best dear hi hello from sent subject
your you our their via new now get all any per not fwd fwd: re: mail email
的 了 在 是 我 你 他 我們 你們 這 那 請 就 都 及 與 或 也 但 而 並 於
fw re 轉寄 回覆 您好 謝謝 親愛 敬啟 透過 系統 星期 星期一 星期二 星期三 星期四
星期五 星期六 星期日 上午 下午 晚上 早上 凌晨 今天 明天 昨天 本週 上週 下週
如下 如附 附件 內容 相關 進行 使用 提供 可以 沒有 這個 那個 什麼 任何 已經
以上 以下 目前 之後 之前 其中 一個 一起 立刻 立即 一下 這些 那些 就是 怎麼
還沒 不用 只要 即將 把握 提醒您 快來 看吧 感謝 歡迎""".split())


def load_domain_dict(path="domain_dict.txt"):
    """jieba 自訂領域詞典:一行一詞(可附詞頻),放料號/廠名/術語。
    先找給定路徑,再找引擎目錄(deep 鏈 cwd 不在 engines,相對路徑會落空)。"""
    if not TOOLS["jieba"]:
        return False
    # 內建領域詞(v1.3 擴充:銀行/品牌/財經 — 修「豐銀行」類切錯)
    for w in ["信賴性", "量產放行", "轉廠", "斷點", "催辦", "green light", "DVT", "reliability",
              "永豐銀行", "台新銀行", "星展銀行", "第一銀行", "土地銀行", "富邦產險",
              "中華航空", "人力銀行", "簽帳金融卡", "信用卡", "電子發票", "電子明細",
              "網路銀行", "行動銀行", "會員點數", "定期定額", "手續費", "父親節",
              "標普", "費半", "道瓊", "那斯達克", "美股", "台股", "升息", "降息",
              "非農", "財報", "回檔", "鉅亨", "誠品線上", "屈臣氏", "全聯"]:
        jieba.add_word(w)
    loaded = False
    for p in (Path(path), Path(__file__).resolve().parent / "domain_dict.txt"):
        if p.exists():
            jieba.load_userdict(str(p))
            loaded = True
            break
    return loaded


def textrank_keywords(text: str, top_n=8):
    """jieba TextRank:圖排序關鍵詞,對長文與口語信件比 TF-IDF 穩。"""
    if not TOOLS["jieba"]:
        return []
    try:
        import jieba.analyse
        return jieba.analyse.textrank(text, topK=top_n,
                                      allowPOS=("n", "nz", "vn", "eng", "nr", "ns"))
    except Exception:
        return []


def tokenize(text: str):
    text = re.sub(r"[\w.+-]+@[\w.-]+", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    # 中文詞被 HTML 折行切斷(「永\n豐銀行」→ 殘片「豐銀行」)— 接合 CJK 間空白
    text = re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", text)
    if TOOLS["jieba"]:
        toks = jieba.lcut(text)
    else:
        toks = re.findall(r"[a-zA-Z]{2,}|[\u4e00-\u9fff]{2,}", text)
    out = []
    for t in toks:
        t = t.strip().lower()
        if len(t) < 2 or t in STOPWORDS or t.isdigit():
            continue
        if re.fullmatch(r"[\W_]+", t):
            continue
        if any(ch.isdigit() for ch in t):        # 25.1 / w32 / m27 類混數 token 無語義
            continue
        if re.fullmatch(r"[a-z]{1,2}", t):        # 純拉丁需 ≥3 字(fw/nt/ea 類碎片)
            continue
        out.append(t)
    return out


# ============================================================
# [NLP] 模組
# ============================================================
def nlp_case_keywords(conn, top_n=8):
    """各案 TF-IDF 關鍵詞(以案為文件)。"""
    if not TOOLS["sklearn"]:
        return None
    rows = conn.execute(
        "SELECT case_seq, subject || ' ' || body_clean FROM E01_MAIL").fetchall()
    docs = defaultdict(list)
    for cs, text in rows:
        docs[cs].append(text or "")
    cases = sorted(docs)
    corpus = [" ".join(tokenize(" ".join(docs[c]))) for c in cases]
    if len(corpus) < 2 or all(not c for c in corpus):
        return []
    vec = TfidfVectorizer(max_features=3000)
    try:
        X = vec.fit_transform(corpus)
    except ValueError:
        return []
    terms = vec.get_feature_names_out()
    out = []
    for i, cs in enumerate(cases):
        arr = X[i].toarray()[0]
        idx = arr.argsort()[::-1][:top_n]
        kws = [terms[j] for j in idx if arr[j] > 0]
        out.append((cs, kws))
    return out


def nlp_cluster_unclassified(conn, max_k=5):
    """對 CASE 維度未命中(待歸類)之信件聚類,產出建議關鍵字供人工增補規則。"""
    if not TOOLS["sklearn"]:
        return None
    rows = conn.execute(
        "SELECT m.mail_id, m.subject, m.body_clean FROM E01_MAIL m"
        " WHERE m.mail_id NOT IN (SELECT mail_id FROM E03_LABEL WHERE dimension='CASE')"
    ).fetchall()
    if len(rows) < 3:
        return []
    texts = [" ".join(tokenize((s or "") + " " + (b or "")[:2000])) for _, s, b in rows]
    # v1.3:詞級向量(文本已斷詞;char n-gram 會再切碎中英詞 → 「銀行 , 銀」碎片)
    vec = TfidfVectorizer(max_features=2000, analyzer=str.split)
    try:
        X = vec.fit_transform(texts)
    except ValueError:
        return []
    from sklearn.metrics import silhouette_score
    best_k, best_score, best_km = 2, -1.0, None
    for k in range(2, min(max_k, len(rows) - 1) + 1):
        km_try = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X)
        if len(set(km_try.labels_)) < 2:
            continue
        try:
            sc = silhouette_score(X, km_try.labels_)
        except ValueError:
            continue
        if sc > best_score:
            best_k, best_score, best_km = k, sc, km_try
    km = best_km if best_km is not None else KMeans(n_clusters=2, n_init=10, random_state=42).fit(X)
    k = best_k
    terms = vec.get_feature_names_out()
    clusters = []
    for ci in range(k):
        members = [rows[i][1] for i in range(len(rows)) if km.labels_[i] == ci]
        center = km.cluster_centers_[ci]
        top = []
        for j in center.argsort()[::-1]:          # 去重去空,湊滿 6 個乾淨詞
            t = terms[j].strip()
            if t and t not in top:
                top.append(t)
            if len(top) >= 6:
                break
        samples = [s.strip() for s in members if s and s.strip()][:3] or ["(無主旨)"]
        clusters.append({"cluster": ci, "size": len(members),
                         "suggest_keywords": top, "sample_subjects": samples})
    return clusters


def nlp_supervised_suggest(conn, min_train=8, confidence=0.5):
    """監督式二階分類:以規則已標 CASE 的信為訓練集(LinearSVC),
    對「待歸類」信件給高信心案件建議。僅建議、不寫庫,人工核准後入 rules_addendum。"""
    if not TOOLS["sklearn"]:
        return None
    labeled = conn.execute(
        "SELECT m.subject || ' ' || m.body_clean, l.label FROM E01_MAIL m"
        " JOIN E03_LABEL l ON l.mail_id=m.mail_id AND l.dimension='CASE'").fetchall()
    unlabeled = conn.execute(
        "SELECT m.mail_id, m.subject, m.subject || ' ' || m.body_clean FROM E01_MAIL m"
        " WHERE m.mail_id NOT IN (SELECT mail_id FROM E03_LABEL WHERE dimension='CASE')").fetchall()
    if len(labeled) < min_train or len(set(l for _, l in labeled)) < 2 or not unlabeled:
        return []
    from sklearn.svm import LinearSVC
    from sklearn.pipeline import make_pipeline
    texts = [" ".join(tokenize(t)) for t, _ in labeled]
    ys = [l for _, l in labeled]
    clf = make_pipeline(
        TfidfVectorizer(max_features=4000, analyzer=str.split),
        LinearSVC())
    try:
        clf.fit(texts, ys)
    except ValueError:
        return []
    out = []
    ux = [" ".join(tokenize(t)) for _, _, t in unlabeled]
    scores = clf.decision_function(ux)
    preds = clf.predict(ux)
    import numpy as np
    for i, (mid, subj, _) in enumerate(unlabeled):
        row = scores[i] if getattr(scores[i], "__len__", None) else [scores[i]]
        margin = float(np.max(row))
        if margin >= confidence:
            out.append((mid, subj[:60], preds[i], round(margin, 2)))
    return out


def nlp_similar_threads(conn, threshold=0.45):
    """相似 thread 偵測:主旨不同但內容高度相似(cosine),提示可能是同一件事拆線。"""
    if not TOOLS["sklearn"]:
        return None
    rows = conn.execute(
        "SELECT t.case_seq, t.norm_subject,"
        " (SELECT group_concat(substr(body_clean,1,800),' ') FROM E01_MAIL m"
        "  WHERE m.thread_key=t.thread_key) FROM E02_THREAD t").fetchall()
    if len(rows) < 3:
        return []
    texts = [" ".join(tokenize(r[2] or "")) for r in rows]
    vec = TfidfVectorizer(max_features=3000, analyzer=str.split)
    try:
        X = vec.fit_transform(texts)
    except ValueError:
        return []
    from sklearn.metrics.pairwise import cosine_similarity
    S = cosine_similarity(X)
    out = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if S[i, j] >= threshold:
                out.append((rows[i][0], rows[j][0], round(float(S[i, j]), 2),
                            rows[i][1][:40], rows[j][1][:40]))
    return sorted(out, key=lambda x: -x[2])


# ============================================================
# [DM] 模組
# ============================================================
BULK_SENDER_PATTERNS = [
    r"no-?reply", r"donot", r"do-not-reply", r"newsletter", r"notification",
    r"電子報", r"特刊", r"愛讀報", r"會員報", r"晨訊", r"通知", r"明細", r"官網",
    r"平台", r"中心", r"magazine", r"defender", r"support", r"service", r"電子明細",
    r"銀行", r"產險", r"保險", r"航空", r"金融卡", r"信用卡", r"人力",
]


def _load_bulk_patterns():
    """系統寄件者樣式:內建 + engines/bulk_senders.txt(一行一個 regex,只增不減)。"""
    pats = list(BULK_SENDER_PATTERNS)
    p = Path(__file__).resolve().parent / "bulk_senders.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pats.append(line)
    return re.compile("|".join(pats), re.IGNORECASE)


def dm_latency_outliers(conn):
    """對口回覆延遲 IQR 離群:延遲顯著高於群體者,列為升級優先對象。
    v1.3:電子報/no-reply 類系統寄件者誠實標注「系統/電子報」,不參與升級判定
    (對永不回信的系統算回覆延遲無意義);人類對口排前。"""
    rows = conn.execute(
        "SELECT sk_email, avg_latency_hr FROM V_LATEST_ASSESSMENT"
        " WHERE avg_latency_hr IS NOT NULL").fetchall()
    bulk_re = _load_bulk_patterns()
    tagged = [(e, l, bool(bulk_re.search(e or ""))) for e, l in rows]
    humans = [(e, l) for e, l, b in tagged if not b]
    if len(humans) < 4:
        out = [(e, l, "人", "樣本不足,僅列值") for e, l in humans]
    else:
        vals = sorted(l for _, l in humans)
        q1, q3 = vals[len(vals) // 4], vals[3 * len(vals) // 4]
        fence = q3 + 1.5 * (q3 - q1)
        out = [(e, l, "人", "OUTLIER-升級優先" if l > fence else "") for e, l in humans]
    out += [(e, l, "系統/電子報", "不列升級") for e, l, b in tagged if b]
    return out


def dm_weekly_volume(conn):
    """各案每週信量(趨勢資料;信量驟增常代表案件出事)。"""
    rows = conn.execute(
        "SELECT case_seq, mail_date FROM E01_MAIL WHERE mail_date IS NOT NULL").fetchall()
    weekly = Counter()
    for cs, d in rows:
        dt = datetime.fromisoformat(d)
        weekly[(cs, dt.strftime("%G-W%V"))] += 1
    return sorted(weekly.items())


def dm_pareto_blocked(conn):
    """未結行動依對口 Pareto:找出 20% 對口佔 80% 卡點。"""
    rows = conn.execute(
        "SELECT counterpart, COUNT(*) FROM V_OPEN_ACTIONS GROUP BY counterpart"
        " ORDER BY COUNT(*) DESC").fetchall()
    total = sum(n for _, n in rows) or 1
    out, cum = [], 0
    for cp, n in rows:
        cum += n
        out.append((cp, n, round(100 * cum / total, 1)))
    return out


def dm_label_cooccurrence(conn):
    """CASE × PMAREA 共現矩陣:哪個案子的風險/時程議題最集中。"""
    rows = conn.execute(
        "SELECT a.label, b.label FROM E03_LABEL a JOIN E03_LABEL b"
        " ON a.mail_id=b.mail_id AND a.dimension='CASE' AND b.dimension='PMAREA'"
    ).fetchall()
    m = Counter(rows)
    return sorted(m.items(), key=lambda kv: -kv[1])


# ============================================================
# [PM] 模組
# ============================================================
def pm_build_traces(conn):
    rows = conn.execute(
        "SELECT case_seq, activity, ts, resource FROM E05_INTERACTION"
        " WHERE ts IS NOT NULL ORDER BY case_seq, ts").fetchall()
    traces = defaultdict(list)
    for cs, act, ts, res in rows:
        traces[cs].append((act, datetime.fromisoformat(ts), res))
    return traces


def pm_dfg_with_time(traces):
    """DFG + 每個轉移的平均等待小時(瓶頸=等待最久的邊)。"""
    edge_n, edge_t = Counter(), defaultdict(list)
    for evs in traces.values():
        for (a1, t1, _), (a2, t2, _) in zip(evs, evs[1:]):
            edge_n[(a1, a2)] += 1
            edge_t[(a1, a2)].append((t2 - t1).total_seconds() / 3600)
    out = []
    for (a, b), n in edge_n.most_common():
        ts = edge_t[(a, b)]
        out.append((a, b, n, round(sum(ts) / len(ts), 1)))
    return out


def pm_reminder_loops(traces):
    """催辦迴圈:每案 Reminder 次數與 Request→無 Delivery 的懸案。"""
    out = []
    for cs, evs in traces.items():
        acts = [a for a, _, _ in evs]
        rem = acts.count("Reminder")
        has_req = "Request" in acts or "Reminder" in acts
        has_del = "Delivery" in acts
        if rem >= 2 or (has_req and not has_del):
            out.append((cs, rem, "無交付" if (has_req and not has_del) else "多次催辦"))
    return sorted(out, key=lambda x: -x[1])


def pm_conformance(traces):
    """一致性檢查:實際軌跡 vs 標準流程 Request→Commitment→Delivery。
    偏差分類:CONFORM / MISSING_COMMITMENT(跳過承諾直接催)/ NO_DELIVERY / EXTRA_LOOP。"""
    results = []
    for cs, evs in traces.items():
        acts = [a for a, _, _ in evs]
        core = [a for a in acts if a in STANDARD_FLOW]
        dedup = list(dict.fromkeys(core))
        if dedup == STANDARD_FLOW:
            verdict = "CONFORM"
        elif "Delivery" not in acts and ("Request" in acts or "Reminder" in acts):
            verdict = "NO_DELIVERY"
        elif "Commitment" not in acts and "Delivery" in acts:
            verdict = "MISSING_COMMITMENT"
        elif acts.count("Reminder") >= 2:
            verdict = "EXTRA_LOOP"
        else:
            verdict = "PARTIAL"
        results.append((cs, "→".join(acts), verdict))
    return results


def pm_variants(traces):
    """軌跡變體統計:相同活動序列的案件歸為一個變體,主流程 vs 例外一目了然。"""
    v = Counter()
    for evs in traces.values():
        v["→".join(a for a, _, _ in evs)] += 1
    return v.most_common()


def pm_case_durations(traces):
    """案件工期(首事件到末事件,小時)與分位數。"""
    durs = []
    for cs, evs in traces.items():
        if len(evs) >= 2:
            durs.append((cs, round((evs[-1][1] - evs[0][1]).total_seconds() / 3600, 1)))
    durs.sort(key=lambda x: -x[1])
    if not durs:
        return [], {}
    vals = sorted(d for _, d in durs)
    pct = {"P50": vals[len(vals) // 2], "P90": vals[min(len(vals) - 1, int(len(vals) * 0.9))],
           "MAX": vals[-1]}
    return durs, pct


def pm_sla_breach(conn, traces):
    """SLA 違約:E07 有正規化承諾日(due_date_iso)但該案在期限前無 Delivery 事件。"""
    rows = conn.execute(
        "SELECT a.case_code, m.case_seq, a.due_date_iso, a.description"
        " FROM E07_ACTION a JOIN E01_MAIL m ON m.mail_id=a.mail_id"
        " WHERE a.due_date_iso IS NOT NULL").fetchall()
    today = datetime.now().date()
    out = []
    for case_code, case_seq, due_iso, desc in rows:
        due = datetime.fromisoformat(due_iso).date()
        delivered = any(a == "Delivery" and t.date() <= due
                        for a, t, _ in traces.get(case_seq, []))
        if not delivered and due < today:
            out.append((case_code, due_iso, (today - due).days, desc[:60]))
    return sorted(out, key=lambda x: -x[2])


def _attach_portable_graphviz():
    """dot 不在 PATH 時,臨時接上 engines/.graphviz 可攜版(dotsetup 產物;只改本程序環境)。"""
    if shutil.which("dot"):
        return
    root = Path(__file__).resolve().parent / ".graphviz"
    for name in ("dot.exe", "dot"):
        hits = sorted(root.glob("*/bin/" + name)) + sorted(root.glob("bin/" + name))
        if hits:
            os.environ["PATH"] = str(hits[0].parent) + os.pathsep + os.environ.get("PATH", "")
            return


def pm_pmislite_dfg_svg(traces, outdir: Path):
    """pm4py/graphviz 缺席時之後備:PMIS-Lite process_mining(純 stdlib)離線 SVG
    流程圖(工作流優化引擎跨系統應用;瓶頸紅粗線/返工環/偷跑紅虛線)。"""
    try:
        import importlib.util
        from types import SimpleNamespace
        pm_path = (Path(__file__).resolve().parents[3] / "supportive modules"
                   / "PMIS-Lite" / "pmis_lite" / "pmis_lite" / "process_mining.py")
        if not pm_path.exists():
            return None
        spec = importlib.util.spec_from_file_location("via_pmis_process_mining", str(pm_path))
        pm = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = pm
        spec.loader.exec_module(pm)
        records = []
        for case, evs in traces.items():
            for act, ts, _subj in evs:
                t = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts or "")
                records.append(SimpleNamespace(thread_id=case, topic=act, event_time=t, actor=""))
        if not records:
            return None
        expected = ["Request", "Commitment", "Delivery"]
        result = pm.mine(records, expected_sequence=expected)
        svg = pm.render_svg(result, expected, title="流程探勘 · DFG 實況路徑圖(離線 SVG 後備)")
        (outdir / "process_dfg.svg").write_text(svg, encoding="utf-8")
        return "process_dfg.svg"
    except Exception as e:
        print(f"[INFO] 離線 SVG 流程圖後備未成:{e}", file=sys.stderr)
        return None


def pm_pm4py_discover(conn, outdir: Path):
    """pm4py 正式流程發現:輸出 DFG 圖(需 graphviz;失敗僅記事不中斷)。"""
    if not (TOOLS["pm4py"] and TOOLS["pandas"]):
        return None
    _attach_portable_graphviz()
    try:
        df = pd.read_sql_query(
            "SELECT case_seq AS \"case:concept:name\", activity AS \"concept:name\","
            " ts AS \"time:timestamp\" FROM E05_INTERACTION WHERE ts IS NOT NULL", conn)
        if df.empty:
            return None
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"])
        log = pm4py.format_dataframe(df, case_id="case:concept:name",
                                     activity_key="concept:name",
                                     timestamp_key="time:timestamp")
        dfg, start, end = pm4py.discover_dfg(log)
        try:
            pm4py.save_vis_dfg(dfg, start, end, str(outdir / "process_dfg.png"))
            return "process_dfg.png"
        except Exception as e:
            print(f"[INFO] DFG 圖輸出略過(需 graphviz):{e}", file=sys.stderr)
            return "dfg-computed-no-image"
    except Exception as e:
        print(f"[WARN] pm4py 分析失敗:{e}", file=sys.stderr)
        return None


# ============================================================
# HTML 報告
# ============================================================
NEXT_STEP_MAP = {
    "NO_DELIVERY": "書面催辦(CC 主管);2 個工作天無果,附影響評估上報",
    "EXTRA_LOOP": "停止再催,直接升級:附催辦次數與延誤天數",
    "MISSING_COMMITMENT": "要求對方補書面承諾日期,入矩陣列管",
    "CONFORM": "維持追蹤,期限前 2 天主動提醒",
    "PARTIAL": "確認缺口環節(承諾或交付),補齊後結案",
}


def export_next_steps(conn, traces, outdir: Path):
    """依一致性判定產出「下一步」建議 CSV,欄位可直接貼 WorkMatrix。"""
    import csv as _csv
    rows = []
    subj = dict(conn.execute("SELECT case_seq, norm_subject FROM E02_THREAD").fetchall())
    for cs, trace, verdict in pm_conformance(traces):
        rows.append((cs, subj.get(cs, "")[:50], verdict,
                     NEXT_STEP_MAP.get(verdict, "維持追蹤")))
    out = outdir / "workmatrix_next_steps.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["案件", "主旨", "流程判定", "建議下一步(可貼 WorkMatrix)"])
        w.writerows(rows)
    return len(rows)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table(headers, rows):
    h = "<tr>" + "".join(f"<th>{esc(x)}</th>" for x in headers) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table>{h}{b}</table>"


def write_report(outdir: Path, sections):
    sb = ['<!DOCTYPE html><html><head><meta charset="utf-8"><title>進階分析報告</title>',
          '<style>body{font-family:"Microsoft JhengHei",sans-serif;background:#f5f4f0;'
          'color:#26313a;margin:32px;max-width:1100px}h1{font-size:20px}'
          'h2{font-size:16px;margin-top:30px;border-left:4px solid #0e7c86;padding-left:10px}'
          'table{border-collapse:collapse;background:#fff;margin-top:8px;width:100%}'
          'td,th{border:1px solid #dbd9d3;padding:6px 10px;font-size:13px;text-align:left}'
          'th{background:#2b3a42;color:#fff}p.note{color:#6b7a85;font-size:12px}</style></head><body>',
          f'<h1>超級引擎進階分析報告 · {datetime.now():%Y-%m-%d %H:%M}</h1>',
          '<p class="note">工具狀態:' + " / ".join(
              f"{k}:{'可用' if v else '未安裝'}" for k, v in TOOLS.items()) + '</p>']
    for title, note, content in sections:
        sb.append(f"<h2>{esc(title)}</h2>")
        if note:
            sb.append(f'<p class="note">{esc(note)}</p>')
        sb.append(content)
    sb.append('<p class="note">所有統計為 M 級證據(信件樣本推算);正式上報請註明資料範圍。'
              '聚類建議關鍵字須人工核准後才增補至分類規則(只增不減)。</p></body></html>')
    (outdir / "analytics_report.html").write_text("".join(sb), encoding="utf-8")


# ============================================================
# main
# ============================================================
def main():
    ap = argparse.ArgumentParser(description="超級引擎進階分析層")
    ap.add_argument("--db", default="./engine_out/super_engine.db")
    ap.add_argument("--outdir", default="./engine_out")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    sections = []
    ssot_dict = Path(args.db).parent / "domain_dict.txt"
    if load_domain_dict(str(ssot_dict)):
        print("[INFO] 已載入領域詞典(db 側或 engines\\domain_dict.txt)")

    # 命名帳本(workops_namer 產):報表以「編號·名稱」顯示,編號本身不變
    names = {}
    for cand in ([Path(args.db).resolve().parents[2] / "workops_naming.json"]
                 if len(Path(args.db).resolve().parents) > 2 else []) + \
                [Path(__file__).resolve().parent.parent / "out" / "workops_naming.json"]:
        if cand.exists():
            try:
                names = json.loads(cand.read_text(encoding="utf-8")).get("entries", {})
                print("[INFO] 已載入命名帳本:%d 筆(via-workops names 管理)" % len(names))
            except Exception as e:
                print("[WARN] 命名帳本讀取失敗:%s" % e, file=sys.stderr)
            break

    def L(cs):
        e = names.get(cs)
        if not e:
            return cs
        if e.get("approved"):
            return "%s·%s" % (cs, e["approved"])
        return "%s·%s(待核對)" % (cs, e.get("proposed", "")) if e.get("proposed") else cs

    def LR(rows):
        return [(L(r[0]),) + tuple(r[1:]) for r in rows]
    progress(10, "分析層啟動:NLP 模組")

    # --- NLP ---
    kw = nlp_case_keywords(conn)
    if kw is None:
        sections.append(("NLP · 各案關鍵詞", "需 pip install scikit-learn jieba", "<p>模組未啟用</p>"))
    else:
        sections.append(("NLP · 各案 TF-IDF 關鍵詞",
                         "每案信件合併為一份文件,關鍵詞代表該案討論核心;關鍵詞突變=案件重心轉移。",
                         table(["案件", "關鍵詞"], [(L(c), ", ".join(k)) for c, k in kw]) if kw else "<p>樣本不足</p>"))
    cl = nlp_cluster_unclassified(conn)
    if cl:
        sections.append(("NLP · 待歸類信件聚類(建議新規則)",
                         "KMeans 聚類未命中 CASE 的信件;建議關鍵字經人工核准後增補 CASE_RULES。",
                         table(["群", "封數", "建議關鍵字", "樣本主旨"],
                               [(c["cluster"], c["size"], ", ".join(c["suggest_keywords"]),
                                 " | ".join(c["sample_subjects"])) for c in cl])))
    elif cl is not None:
        sections.append(("NLP · 待歸類信件聚類", "", "<p>待歸類信件少於 3 封,無需聚類。</p>"))

    sug = nlp_supervised_suggest(conn)
    if sug:
        sections.append(("NLP · 監督式分類建議(高信心)",
                         "以規則已標信件訓練 LinearSVC;僅供建議,人工核准後寫入 rules_addendum.json。",
                         table(["mail_id", "主旨", "建議案件", "信心分數"], sug)))
    elif sug is not None:
        sections.append(("NLP · 監督式分類建議", "訓練樣本不足(<8 封已標信或類別<2),累積後自動啟用。", "<p>暫不啟用</p>"))
    sim = nlp_similar_threads(conn)
    if sim:
        sections.append(("NLP · 相似 thread 偵測(疑似同案拆線)",
                         "主旨不同但內容 cosine 相似度高,建議人工確認是否併案追蹤。",
                         table(["Thread A", "Thread B", "相似度", "主旨A", "主旨B"], sim)))

    progress(45, "資料挖掘模組")
    # --- DM ---
    sections.append(("資料挖掘 · 回覆延遲離群偵測(IQR)",
                     "延遲顯著高於群體者列為升級優先對象(僅人類對口;系統/電子報誠實標注不列升級);樣本少於 4 人僅列值。",
                     table(["對口", "平均延遲(hr)", "型態", "判定"], dm_latency_outliers(conn)) or "<p>無資料</p>"))
    wv = dm_weekly_volume(conn)
    sections.append(("資料挖掘 · 各案週信量",
                     "單案單週信量驟增通常代表出事;可與卡住狀態交叉驗證。",
                     table(["案件", "週", "封數"], [(L(c), w, n) for (c, w), n in wv])))
    sections.append(("資料挖掘 · 未結行動 Pareto(對口集中度)",
                     "累積 % 快速到 80 = 卡點集中於少數對口,升級火力應對準這幾位。",
                     table(["對口", "未結行動", "累積%"], dm_pareto_blocked(conn))))
    co = dm_label_cooccurrence(conn)
    sections.append(("資料挖掘 · CASE × 管理領域 共現",
                     "哪個案子的風險/時程議題最集中,即為每日優先案。",
                     table(["案件", "管理領域", "共現次數"], [(L(a), b, n) for (a, b), n in co])))

    progress(70, "流程探勘模組")
    # --- PM ---
    traces = pm_build_traces(conn)
    sections.append(("流程探勘 · DFG 轉移與平均等待",
                     "等待小時最長的邊就是流程瓶頸;Request→Reminder 高頻=對方拖延的量化證據。",
                     table(["From", "To", "次數", "平均等待(hr)"], pm_dfg_with_time(traces))))
    loops = pm_reminder_loops(traces)
    sections.append(("流程探勘 · 催辦迴圈與無交付懸案",
                     "Reminder≥2 或有要求無交付的案件;直接對應 48h 升級規則的觸發清單。",
                     table(["案件", "催辦次數", "型態"], LR(loops)) if loops else "<p>無懸案。</p>"))
    sections.append(("流程探勘 · 一致性檢查(vs 標準流程 Request→Commitment→Delivery)",
                     "NO_DELIVERY / EXTRA_LOOP 即為流程偏差,可作為上報 BU 的偏差清單。",
                     table(["案件", "實際軌跡", "判定"], LR(pm_conformance(traces)))))
    sections.append(("流程探勘 · 軌跡變體",
                     "同一活動序列歸為一個變體;最大宗變體=實際主流程,長尾=例外處理。",
                     table(["活動序列", "案件數"], pm_variants(traces))))
    durs, pct = pm_case_durations(traces)
    if durs:
        sections.append(("流程探勘 · 案件工期(首末事件間隔)",
                         f"分位數:P50={pct['P50']}hr / P90={pct['P90']}hr / MAX={pct['MAX']}hr;超過 P90 的案優先檢視。",
                         table(["案件", "工期(hr)"], LR(durs))))
    breach = pm_sla_breach(conn, traces)
    sections.append(("流程探勘 · SLA 違約(承諾日已過且無交付)",
                     "承諾日取自信件正規化期限;逾期天數即上報 BU 的量化依據。",
                     table(["案件", "承諾日", "逾期天數", "事項"], LR(breach)) if breach else "<p>無違約。</p>"))
    dfg_img = pm_pm4py_discover(conn, outdir)
    if dfg_img == "process_dfg.png":
        sections.append(("流程探勘 · pm4py DFG 流程圖", "",
                         '<img src="process_dfg.png" style="max-width:100%">'))
    else:
        svg_img = pm_pmislite_dfg_svg(traces, outdir)
        if svg_img:
            sections.append(("流程探勘 · DFG 實況路徑圖(離線 SVG 後備)",
                             "pm4py/graphviz 缺席之機器亦有圖:PMIS-Lite 純 stdlib 探勘器(瓶頸紅粗線/返工環)。",
                             '<img src="process_dfg.svg" style="max-width:100%">'))

    n_ns = export_next_steps(conn, traces, outdir)
    progress(88, f"下一步建議 {n_ns} 筆 → workmatrix_next_steps.csv")
    progress(92, "產出分析報告")
    write_report(outdir, sections)
    conn.close()
    progress(100, "分析層完成")
    print(f"完成:{outdir / 'analytics_report.html'}")
    missing = [k for k, v in TOOLS.items() if not v]
    if missing:
        print("未安裝(可選):pip install " + " ".join(missing))


if __name__ == "__main__":
    main()
