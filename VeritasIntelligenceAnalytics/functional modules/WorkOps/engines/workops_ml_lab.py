# -*- coding: utf-8 -*-
r"""WorkOps ML 實驗室 v0100(ENG-055)— 操作員 apply ML/DL top10 local free libs 令

定位:V/T/K/A/Q/E 六層誠實解析「之後、之外」的機器學習建議層 —
ML 永不直寫狀態;所有產出=人工圈選候選。解析器本體零改動。

動詞:
  probe    二十庫在位探測(ML 十選 + DL 十選;docs/ML_DL_2026_Top10_Local_Free.md 對照)
  setup    安裝核心依賴 scikit-learn(py -m pip install --user)
  train    詞庫泛化模型:人工核准詞庫(keywords/weak_signals/ack_terms)+ 已判讀
           事實流(reply_events)+ Gold Set(在位時)→ char n-gram TF-IDF +
           邏輯迴歸;交叉驗證誠實報分;樣本不足=誠實 FAIL
  suggest  對未解析回信出 ML 候選狀態(機率 ≥ 門檻才列)→ out/ml_suggestions.csv
  cluster  未解析樣本聚類提詞 → out/lexicon_review.csv(人工填「建議狀態」欄)
  adopt    讀回 lexicon_review.csv 已填列 → 核准詞寫回 reply_parser_params.json
           (閉環;AI 只整理不發明 — 只收人工填過的列)

治理:模型/建議/聚類全落 out/(可再生側車);行為參數全 config/ml_params.json;
依賴缺席=誠實 FAIL + 一行安裝指令;sentence-transformers 在位時自動升級語意嵌入。
"""
import argparse
import csv
import io
import json
import pickle
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
MLDIR = OUT / "ml"
CFG_P = WORKOPS / "config" / "ml_params.json"
MODEL_P = MLDIR / "reply_model.pkl"
SUGG_P = OUT / "ml_suggestions.csv"
LEXREV_P = OUT / "lexicon_review.csv"
PROBE_P = OUT / "ml_probe.json"

ML10 = ["sklearn", "xgboost", "lightgbm", "catboost", "statsmodels",
        "pandas", "numpy", "imblearn", "river", "mlxtend"]
DL10 = ["torch", "tensorflow", "jax", "transformers", "sentence_transformers",
        "onnxruntime", "llama_cpp", "ollama", "spacy", "openvino"]

DEFAULTS = {"suggest_threshold": 0.75, "min_per_class": 3, "min_classes": 2,
            "cluster_k_max": 8, "cluster_min_docs": 6, "char_ngram": [1, 3],
            "use_embeddings": True}


def now():
    return datetime.now().isoformat(timespec="seconds")


def cfg():
    d = dict(DEFAULTS)
    try:
        j = json.loads(CFG_P.read_text(encoding="utf-8-sig"))
        for k in DEFAULTS:
            if k in j:
                d[k] = j[k]
    except Exception:
        pass
    return d


def need_sklearn():
    try:
        import sklearn  # noqa: F401
        return True
    except Exception:
        print("[FAIL] scikit-learn 未安裝 — 貼一行安裝(或 via-workops ml setup):")
        print("py -m pip install --user scikit-learn")
        return False


def cmd_probe():
    rows = []
    for group, names in (("ML", ML10), ("DL", DL10)):
        for n in names:
            ver = ""
            try:
                m = __import__(n)
                ver = str(getattr(m, "__version__", "?"))
                ok = True
            except Exception:
                ok = False
            rows.append({"group": group, "lib": n, "present": ok, "version": ver})
            print(" [%s] %-2s %-22s %s" % ("在位" if ok else "缺席", group, n, ver))
    n_ok = sum(1 for r in rows if r["present"])
    OUT.mkdir(parents=True, exist_ok=True)
    PROBE_P.write_text(json.dumps({"version": "v0100", "engine_id": "ENG-055", "ts": now(),
                                   "present": n_ok, "total": len(rows), "libs": rows},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print("========== 探測:%d/%d 在位(對照 docs/ML_DL_2026_Top10_Local_Free.md)==========" % (n_ok, len(rows)))
    print("[報告] %s" % PROBE_P)
    return 0


def cmd_setup():
    print("[安裝] scikit-learn(核心;--user 免系統權限)...")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "scikit-learn"])
    if r.returncode == 0 and need_sklearn():
        print("[OK ] scikit-learn 就緒 — 下一步:via-workops ml train")
        return 0
    print("[FAIL] 安裝未成 — 檢查網路後重試")
    return 1


def _label_corpus():
    """標註源三路合併:詞庫種子(人工核准 JSON)+ 事實流已判讀 + Gold Set 狀態欄。"""
    from workops_reply_parser import load_params
    docs, labels, srcs = [], [], {"lexicon": 0, "events": 0, "gold": 0}
    p = load_params()
    seed = {}
    for st, words in (p.get("keywords") or {}).items():
        seed.setdefault(st, []).extend(words)
    for st, words in (p.get("weak_signals") or {}).items():
        seed.setdefault(st, []).extend(words)
    seed.setdefault("已回覆確認", []).extend(p.get("ack_terms") or [])
    for st, words in seed.items():
        for w in words:
            w = str(w).strip()
            if w:
                docs.append(w)
                labels.append(st)
                srcs["lexicon"] += 1
    ev_p = OUT / "reply_events.jsonl"
    if ev_p.exists():
        for ln in ev_p.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(ln)
            except Exception:
                continue
            subj = (e.get("subject") or "").strip()
            st = (e.get("status") or "").strip()
            if subj and st:
                docs.append(subj)
                labels.append(st)
                srcs["events"] += 1
    gs_p = OUT / "gold_set.csv"
    if gs_p.exists():
        try:
            with io.open(gs_p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
                for r in csv.DictReader(f):
                    subj = (r.get("Subject") or r.get("主旨") or "").strip()
                    st = (r.get("正確狀態") or r.get("status") or "").strip()
                    if subj and st:
                        docs.append(subj)
                        labels.append(st)
                        srcs["gold"] += 1
        except Exception:
            pass
    return docs, labels, srcs


def cmd_train():
    if not need_sklearn():
        return 1
    from collections import Counter
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline
    c = cfg()
    docs, labels, srcs = _label_corpus()
    cnt = Counter(labels)
    print("[標註] 詞庫種子 %d · 事實流 %d · Gold Set %d → 共 %d 樣本 %d 類"
          % (srcs["lexicon"], srcs["events"], srcs["gold"], len(docs), len(cnt)))
    for st, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print("   %-8s %d" % (st, n))
    weak = [st for st, n in cnt.items() if n < int(c["min_per_class"])]
    if len(cnt) < int(c["min_classes"]) or weak:
        print("[FAIL] 樣本不足(每類至少 %d;不足類:%s)— 誠實不硬 train"
              % (c["min_per_class"], "、".join(weak) or "類數不足"))
        return 1
    ng = tuple(int(x) for x in c["char_ngram"])
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=ng, min_df=1)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    k = min(3, min(cnt.values()))
    cv_line = "樣本過少未交叉驗證"
    if k >= 2:
        try:
            scores = cross_val_score(pipe, docs, labels, cv=k)
            cv_line = "%d-fold 交叉驗證 accuracy %.3f ± %.3f" % (k, scores.mean(), scores.std())
        except Exception as e:
            cv_line = "交叉驗證未成(%s)" % e
    pipe.fit(docs, labels)
    MLDIR.mkdir(parents=True, exist_ok=True)
    with io.open(MODEL_P, "wb") as f:
        pickle.dump({"pipe": pipe, "classes": sorted(cnt), "ts": now(),
                     "n": len(docs), "sources": srcs}, f)
    (MLDIR / "reply_model_meta.json").write_text(json.dumps(
        {"version": "v0100", "engine_id": "ENG-055", "ts": now(), "n_docs": len(docs),
         "classes": {k2: v for k2, v in cnt.items()}, "sources": srcs, "cv": cv_line,
         "governance": "詞庫泛化模型 — 建議層專用,永不直寫狀態"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("[訓練] %s" % cv_line)
    print("[模型] %s(誠實註記:訓練分數≠實測準確率;Gold Set 實測仍為唯一準確率權威)" % MODEL_P)
    return 0


def _unparsed_docs():
    """與解析器同源取未解析件:mails.csv × scanrange body;parse_one=None 者。"""
    from workops_reply_parser import (load_params, load_scan_index, parse_one, read_csv,
                                      load_corpus_bodies, body_for)
    mails = read_csv(OUT / "mails.csv")
    bodies, _ = load_scan_index()
    corpus = load_corpus_bodies()
    params = load_params()
    items = []
    for r in mails:
        if (r.get("Direction") or "").upper() not in ("", "INBOUND"):
            continue
        conv = (r.get("ConversationID") or "").strip()
        if not conv:
            continue
        b = body_for(bodies, corpus, conv, r.get("Subject"))
        if parse_one(r, b, params) is None:
            items.append({"conv": conv, "subj": (r.get("Subject") or "").strip(),
                          "from": (r.get("SenderEmail") or "").strip(),
                          "text": ((r.get("Subject") or "") + "\n" + b).strip()})
    return items


def cmd_suggest():
    if not need_sklearn():
        return 1
    if not MODEL_P.exists():
        print("[FAIL] 模型不在位 — 先跑 via-workops ml train")
        return 1
    c = cfg()
    with io.open(MODEL_P, "rb") as f:
        M = pickle.load(f)
    pipe = M["pipe"]
    items = _unparsed_docs()
    if not items:
        print("[空] 無未解析件(或 out\\mails.csv 不在位)— 先跑 via-workops all")
        return 0
    proba = pipe.predict_proba([x["text"] for x in items])
    classes = list(pipe.classes_)
    th = float(c["suggest_threshold"])
    rows = []
    for x, pr in zip(items, proba):
        best = max(range(len(classes)), key=lambda i: pr[i])
        if pr[best] >= th:
            rows.append({"ThrConv": x["conv"], "Subject": x["subj"][:70], "Sender": x["from"],
                         "ML候選狀態": classes[best], "機率": "%.2f" % pr[best], "採納(Y/留空)": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    with io.open(SUGG_P, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ThrConv", "Subject", "Sender", "ML候選狀態", "機率", "採納(Y/留空)"])
        w.writeheader()
        w.writerows(rows)
    print("[建議] 未解析 %d 件 → ML 候選 %d 件(機率 ≥ %.2f 才列;絕不直寫狀態)"
          % (len(items), len(rows), th))
    if items and not rows:
        mx = max(max(pr) for pr in proba)
        print("[誠實] 全數未達門檻(本輪最高機率 %.2f)— 模型會隨事實流/Gold Set 標註長大;門檻在 config\\ml_params.json" % mx)
    print("[報告] %s(Excel 圈選參考;正式狀態仍由回信訊號/人工認定)" % SUGG_P)
    return 0


def cmd_cluster():
    if not need_sklearn():
        return 1
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
    c = cfg()
    items = _unparsed_docs()
    if len(items) < int(c["cluster_min_docs"]):
        print("[空] 未解析僅 %d 件(< %d)— 樣本不足不硬聚類" % (len(items), c["cluster_min_docs"]))
        return 0
    ng = tuple(int(x) for x in c["char_ngram"])
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(max(2, ng[0]), max(3, ng[1])), min_df=2)
    X = vec.fit_transform([x["text"] for x in items])
    k = max(2, min(int(c["cluster_k_max"]), X.shape[0] // 3))
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    feats = vec.get_feature_names_out()
    rows = []
    for ci in range(k):
        members = [items[i] for i in range(len(items)) if km.labels_[i] == ci]
        center = km.cluster_centers_[ci]
        top = [feats[i].strip() for i in center.argsort()[::-1][:8] if feats[i].strip()]
        rows.append({"群": ci, "件數": len(members),
                     "代表片語": " | ".join(top[:6]),
                     "樣本主旨": " / ".join(m["subj"][:24] for m in members[:3]),
                     "建議狀態(人填;空=不採)": "", "採納詞(分號隔;空=用代表片語)": ""})
    with io.open(LEXREV_P, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("[聚類] 未解析 %d 件 → %d 群 → %s" % (len(items), k, LEXREV_P))
    print("[下一步] Excel 填「建議狀態」欄(已完成/進行中/卡關/需要協助/對方提問)→ via-workops ml adopt")
    return 0


def cmd_adopt():
    if not LEXREV_P.exists():
        print("[FAIL] %s 不在位 — 先跑 via-workops ml cluster" % LEXREV_P.name)
        return 1
    from workops_reply_parser import PARAMS_P
    valid = {"已完成", "進行中", "卡關", "需要協助", "已口頭說明", "對方提問", "已回覆確認"}
    try:
        params = json.loads(Path(PARAMS_P).read_text(encoding="utf-8-sig"))
    except Exception:
        print("[FAIL] reply_parser_params.json 讀取失敗")
        return 1
    adopted = []
    with io.open(LEXREV_P, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
        for r in csv.DictReader(f):
            st = (r.get("建議狀態(人填;空=不採)") or "").strip()
            if not st:
                continue
            if st not in valid:
                print("[忽略] 群 %s:未知狀態「%s」(可用:%s)" % (r.get("群"), st, "、".join(sorted(valid))))
                continue
            manual = (r.get("採納詞(分號隔;空=用代表片語)") or "").strip()
            terms = [t.strip() for t in manual.split(";") if t.strip()] if manual else \
                    [t.strip() for t in (r.get("代表片語") or "").split("|") if len(t.strip()) >= 2][:3]
            for t in terms:
                if st in ("對方提問", "已回覆確認"):
                    key, bucket = "ack_terms", params.setdefault("ack_terms", [])
                    if st == "對方提問":
                        continue  # 問句層靠問號,不收詞 — 誠實略過
                else:
                    kw = params.setdefault("keywords", {})
                    bucket = kw.setdefault(st, [])
                if t not in bucket:
                    bucket.append(t)
                    adopted.append((st, t))
    if not adopted:
        print("[空] 無已填核准列 — lexicon_review.csv 填「建議狀態」後重跑")
        return 0
    bak = Path(str(PARAMS_P) + ".bak")
    bak.write_text(Path(PARAMS_P).read_text(encoding="utf-8-sig"), encoding="utf-8")
    Path(PARAMS_P).write_text(json.dumps(params, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[採納] %d 詞寫回 reply_parser_params.json(備份 .bak;人工核准=唯一寫回路徑):" % len(adopted))
    for st, t in adopted:
        print("   %s ← 「%s」" % (st, t))
    print("[下一步] via-workops replies 重解析 → via-workops accuracy harness 迴歸驗證")
    return 0


def main():
    ap = argparse.ArgumentParser(description="ENG-055 ML 實驗室(建議層;永不直寫狀態)")
    ap.add_argument("command", nargs="?", default="probe",
                    choices=["probe", "setup", "train", "suggest", "cluster", "adopt"])
    a = ap.parse_args()
    return {"probe": cmd_probe, "setup": cmd_setup, "train": cmd_train,
            "suggest": cmd_suggest, "cluster": cmd_cluster, "adopt": cmd_adopt}[a.command]()


if __name__ == "__main__":
    sys.exit(main())
