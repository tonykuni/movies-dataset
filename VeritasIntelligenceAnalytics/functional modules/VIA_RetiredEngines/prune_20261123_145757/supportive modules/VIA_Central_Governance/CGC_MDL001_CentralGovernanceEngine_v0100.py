#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# =============================================================================
#  CGC_MDL001_CentralGovernanceEngine.py                                    (all-in-one)
#  Veritas Intelligence Analytics — 中央治理引擎 · 同義字 / regex SSOT
# -----------------------------------------------------------------------------
#  一顆 Python 檔管全部:
#    1) auto-import live state  自動匯入現況(掃 domain_keywords / ssot.json /
#       events.jsonl / *.csv / *.txt,不吃空白模板)
#    2) 自動擴大同義字            正規化 / 全半形 / 大小寫 / 分隔符 / 縮寫 變體
#    3) 自動更新監測同義字        未知 token 就近歸戶(difflib),分 AUTO/ASK/QUARANTINE
#    4) 自動合成 regex           每個 canonical 依同義字集自動生 regex 並驗證可編譯
#    5) 只增不減治理             同義字只增不刪;退場者轉 DORMANT;evidence V/M/P
#    6) 產出 Visual Lock HTML     深色儀表板 + append-only ledger
#
#  治理原則:只增不減(append-only)、dry-run 預設、--commit 才落地、review-only、
#            evidence honesty(human=V / auto=M封頂 / novel=P)、純 stdlib 可跑。
#  無 Read-Host / 無 input() / 一貼即跑,零外部相依。
#  用法:   python CGC_MDL001_CentralGovernanceEngine.py                 # dry-run 全流程
#           python CGC_MDL001_CentralGovernanceEngine.py --commit        # 落地寫入 SSOT
#           python CGC_MDL001_CentralGovernanceEngine.py --corpus .\logs # 指定語料來源
# =============================================================================

import argparse
import datetime as _dt
import glob
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher

SCHEMA = "VIA-CGE-VOCAB-v1"
ENGINE = "VIA_CentralGovernanceEngine"
VERSION = "v0100"
ID_TYPE = "CGE"

# ---- evidence grades (evidence honesty) -------------------------------------
EV_HUMAN = "V"   # Confirmed — 人工確認
EV_AUTO = "M"    # Media/Model-derived — 自動衍生,封頂於 M
EV_PEND = "P"    # Pending — 新詞待歸類
EV_RANK = {EV_HUMAN: 3, EV_AUTO: 2, EV_PEND: 1}

# ---- lifecycle states (只增不減) --------------------------------------------
ST_ACTIVE = "ACTIVE"
ST_DORMANT = "DORMANT"     # 退場但保留(不刪)
ST_ABSORBED = "ABSORBED"   # 併入其他 canonical

# ---- TW 漲跌色 (Visual Lock) -------------------------------------------------
C_UP = "#c96b5a"    # 紅 = 上升 / 新增
C_DN = "#5a9e6f"    # 綠 = 下降 / 穩定

DEFAULT_PARAMS = {
    "auto_attach": 0.90,   # >= → AUTO(自動歸戶)
    "ask": 0.75,           # >= → ASK(候選待確認)
    # < ask → QUARANTINE / novel(新 canonical 候選)
    "min_token_len": 2,
    "max_token_len": 64,
    "min_freq": 1,
    "word_boundary_ascii": True,
}

# 內建種子字典:讓首跑就有意義(不吃空白模板)。curated=人工 → V。
# 只增不減:seed 只會補進 SSOT,不覆蓋既有。
SEED = {
    "item_number":   {"domain": "superbom", "syn": ["料號", "品號", "part number", "part no", "pn", "mpn", "item no", "料件編號"]},
    "quantity":      {"domain": "superbom", "syn": ["數量", "用量", "qty", "usage", "需求量"]},
    "reference_designator": {"domain": "superbom", "syn": ["位號", "refdes", "ref des", "designator", "location"]},
    "manufacturer":  {"domain": "superbom", "syn": ["製造商", "廠商", "mfr", "maker", "vendor", "供應商", "原廠"]},
    "description":   {"domain": "superbom", "syn": ["描述", "品名", "說明", "desc", "spec", "規格"]},
    "case_id":       {"domain": "vmt", "syn": ["案號", "專案編號", "case", "case no", "專案", "project id"]},
    "activity":      {"domain": "vmt", "syn": ["活動", "事件", "作業", "action", "step", "任務"]},
    "timestamp":     {"domain": "vmt", "syn": ["時間", "時戳", "日期時間", "ts", "datetime", "time"]},
    "follow_up":     {"domain": "vmt", "syn": ["跟催", "追蹤", "催辦", "followup", "chase"]},
    "reminder":      {"domain": "vmt", "syn": ["提醒", "提醒信", "remind"]},
    "warning":       {"domain": "vmt", "syn": ["警告", "延誤警示", "warn", "overdue", "延誤"]},
    "quarantine":    {"domain": "seam", "syn": ["隔離", "檢疫", "quarantine", "q01", "待決"]},
    "eta":           {"domain": "vmt", "syn": ["預計完成", "承諾日", "交期", "deadline", "due", "committed date"]},
}


# =============================================================================
#  Normalization / tokenization
# =============================================================================
def norm(s):
    """正規化鍵:NFKC(統一全半形)→ casefold → 收斂分隔符與空白。"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.casefold().strip()
    s = re.sub(r"[\s_\-/\\.·、,，:：;；()（）\[\]【】]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def variants(term):
    """自動擴大:由一個詞衍生確定式變體(不含模糊猜測)。"""
    out = set()
    raw = str(term).strip()
    if not raw:
        return out
    base = unicodedata.normalize("NFKC", raw)
    cores = {base, base.casefold(), base.upper(), base.lower(), base.title()}
    # 分隔符互換
    seps = re.split(r"[\s_\-/]+", base)
    if len(seps) > 1:
        joined = "".join(seps)
        for j in ("_", "-", " ", ""):
            cores.add(j.join(seps))
        cores.add(joined)
        # 縮寫(取每段首字,僅 ASCII 詞)
        if all(re.match(r"^[A-Za-z0-9]+$", p) for p in seps if p):
            acr = "".join(p[0] for p in seps if p)
            if 3 <= len(acr) <= 6:   # 2 字縮寫過度泛用(如 in/is)→ 不生成
                cores.add(acr)
    for c in cores:
        c = c.strip()
        if c:
            out.add(c)
    return out


def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def token_set_overlap(a, b):
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def match_score(token_norm, cand_norm):
    """未知 token 對 canonical/synonym 的就近分數。"""
    if token_norm == cand_norm:
        return 1.0
    r = ratio(token_norm, cand_norm)
    o = token_set_overlap(token_norm, cand_norm)
    contain = 0.0
    if token_norm and cand_norm and (token_norm in cand_norm or cand_norm in token_norm):
        contain = 0.85
    return max(r, o, contain)


# =============================================================================
#  ID / code (blake2s;hash input = term,LL#30 可驗證)
# =============================================================================
def code_for(term, first_seen):
    h = hashlib.blake2s(("CGE|" + str(term)).encode("utf-8"), digest_size=3).hexdigest().upper()
    day = first_seen.replace("-", "")[:8] if first_seen else "00000000"
    return "VIA-%s-%s-%s" % (ID_TYPE, day, h)


def now_iso():
    return _dt.datetime.now().replace(microsecond=0).isoformat()


def today():
    return _dt.date.today().isoformat()


# =============================================================================
#  Vocab SSOT I/O
# =============================================================================
def blank_vocab():
    return {
        "meta": {
            "schema": SCHEMA,
            "engine": ENGINE,
            "version": VERSION,
            "id_format": "VIA-%s-YYYYMMDD-HEX6" % ID_TYPE,
            "principle": "only-increase (只增不減)",
            "created": now_iso(),
            "runs": 0,
        },
        "canonicals": {},   # cid -> {term, domain, status, code, synonyms[], regex, regex_source, first_seen}
        "quarantine": [],   # {token, freq, nearest, score, decided_run}
    }


def load_json(path, default):
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
        except Exception as e:
            print("  ! 讀取失敗 %s: %s" % (path, e))
    return default


def save_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_ledger(path, event):
    line = json.dumps(event, ensure_ascii=False)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


# =============================================================================
#  Corpus harvesting — auto-import live state
# =============================================================================
LIVE_HINTS = [
    "domain_keywords.json", "ssot.json", "events.jsonl", "confirmations.jsonl",
    "convergence_state.json", "master_state.json",
]


def discover_sources(roots, exclude=None):
    """探索語料來源;exclude 為引擎自身產出的絕對路徑(避免回饋汙染)。"""
    exclude = exclude or set()

    def excluded(p):
        ap = os.path.abspath(p)
        if ap in exclude:
            return True
        base = os.path.basename(p)
        return bool(re.match(r"^(governance_(vocab|ledger)|via_cge_)", base) or
                    base.startswith("VIA_CentralGovernance"))

    found = []
    seen = set()
    for root in roots:
        if os.path.isfile(root):
            if root not in seen and not excluded(root):
                found.append(root); seen.add(root)
            continue
        if not os.path.isdir(root):
            continue
        for hint in LIVE_HINTS:
            for p in glob.glob(os.path.join(root, "**", hint), recursive=True):
                if p not in seen and not excluded(p):
                    found.append(p); seen.add(p)
        for ext in ("*.csv", "*.tsv", "*.txt", "*.jsonl"):
            for p in glob.glob(os.path.join(root, "**", ext), recursive=True):
                if p not in seen and not excluded(p):
                    found.append(p); seen.add(p)
    return found


def _walk_strings(obj, out):
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.append(k)
            _walk_strings(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_strings(v, out)


def harvest(path):
    """回傳該來源的候選 token 清單(原文,尚未正規化)。"""
    toks = []
    low = path.lower()
    try:
        if low.endswith(".json"):
            data = load_json(path, None)
            strs = []
            _walk_strings(data, strs)
            for s in strs:
                toks.extend(re.split(r"[\|,;\t]+", s))
        elif low.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8-sig") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        obj = json.loads(ln)
                        strs = []
                        _walk_strings(obj, strs)
                        toks.extend(strs)
                    except Exception:
                        toks.append(ln)
        elif low.endswith((".csv", ".tsv")):
            sep = "\t" if low.endswith(".tsv") else ","
            with open(path, "r", encoding="utf-8-sig") as f:
                head = f.readline()
                toks.extend(head.split(sep))            # 表頭最重要
                for i, ln in enumerate(f):
                    if i > 500:
                        break
                    toks.extend(ln.split(sep))
        else:  # txt / 其他
            with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
                for i, ln in enumerate(f):
                    if i > 2000:
                        break
                    toks.extend(re.split(r"[\|,;\t]+", ln))
    except Exception as e:
        print("  ! harvest 失敗 %s: %s" % (path, e))
    # 清洗
    clean = []
    for t in toks:
        t = str(t).strip().strip("\"'")
        if t:
            clean.append(t)
    return clean


# =============================================================================
#  Pipeline
# =============================================================================
def build_lookup(vocab):
    """norm(text) -> cid  (canonical 詞與所有 synonym)"""
    lut = {}
    for cid, c in vocab["canonicals"].items():
        if c.get("status") == ST_ABSORBED:
            continue
        lut[norm(c["term"])] = cid
        for syn in c.get("synonyms", []):
            lut[norm(syn["text"])] = cid
    return lut


def ensure_canonical(vocab, term, domain, ledger_events, run):
    key = norm(term)
    for cid, c in vocab["canonicals"].items():
        if norm(c["term"]) == key:
            return cid
    fs = today()
    cid = code_for(term, fs)
    vocab["canonicals"][cid] = {
        "term": term,
        "domain": domain or "unassigned",
        "status": ST_ACTIVE,
        "code": cid,
        "first_seen": fs,
        "synonyms": [],
        "regex": [],
        "regex_source": "",
    }
    ledger_events.append({"ts": now_iso(), "run": run, "op": "CANONICAL_ADD",
                          "cid": cid, "term": term, "domain": domain})
    return cid


def add_synonym(vocab, cid, text, evidence, source, run, ledger_events):
    """append-only:只增不減。回傳 True 若為新增。"""
    c = vocab["canonicals"][cid]
    nkey = norm(text)
    if not nkey or nkey == norm(c["term"]):
        return False
    for syn in c["synonyms"]:
        if norm(syn["text"]) == nkey:
            # 只升不降 evidence
            if EV_RANK.get(evidence, 0) > EV_RANK.get(syn["evidence"], 0):
                syn["evidence"] = evidence
                syn["source"] = source
                ledger_events.append({"ts": now_iso(), "run": run, "op": "SYN_UPGRADE",
                                      "cid": cid, "text": text, "evidence": evidence})
            return False
    c["synonyms"].append({"text": text, "evidence": evidence, "source": source,
                          "first_seen": today(), "run": run})
    ledger_events.append({"ts": now_iso(), "run": run, "op": "SYN_ADD",
                          "cid": cid, "text": text, "evidence": evidence, "source": source})
    return True


def synth_regex(vocab, cid, params):
    """依同義字集自動合成 regex(escape + alternation,長者優先),驗證可編譯。"""
    c = vocab["canonicals"][cid]
    terms = [c["term"]] + [s["text"] for s in c["synonyms"]
                           if s["evidence"] != EV_PEND]
    # 去重(以正規化),保留原文
    seen, uniq = set(), []
    for t in sorted(terms, key=lambda x: -len(x)):
        k = norm(t)
        if k and k not in seen:
            seen.add(k)
            uniq.append(t)
    if not uniq:
        c["regex"] = []
        return
    alts = []
    for t in uniq:
        esc = re.escape(t.strip())
        # 允許 _ - 空白 互換
        esc = re.sub(r"\\[ _\\-]", r"[\\s_\\-]?", esc)
        alts.append(esc)
    body = "|".join(alts)
    ascii_only = all(re.match(r"^[\x00-\x7f]+$", t) for t in uniq)
    if params["word_boundary_ascii"] and ascii_only:
        pat = r"(?i)\b(?:%s)\b" % body
    else:
        pat = r"(?i)(?:%s)" % body
    try:
        re.compile(pat)
        c["regex"] = [pat]
        c["regex_source"] = "auto:alternation(%d)" % len(uniq)
    except re.error as e:
        c["regex"] = []
        c["regex_source"] = "ERROR:%s" % e


def run_pipeline(args):
    root = os.path.abspath(args.workdir)
    vocab_path = args.vocab or os.path.join(root, "governance_vocab.json")
    params_path = args.params or os.path.join(root, "via_cge_params.json")
    ledger_path = args.ledger or os.path.join(root, "governance_ledger.jsonl")
    html_path = args.out_html or os.path.join(root, "VIA_CentralGovernance.html")

    params = dict(DEFAULT_PARAMS)
    params.update(load_json(params_path, {}))
    vocab = load_json(vocab_path, blank_vocab())
    vocab.setdefault("canonicals", {})
    vocab.setdefault("quarantine", [])
    run_id = "R%04d" % (vocab["meta"].get("runs", 0) + 1)
    ledger_events = []

    print("=" * 68)
    print(" %s %s  ·  中央治理引擎(同義字/regex SSOT)" % (ENGINE, VERSION))
    print(" mode = %s   run = %s" % ("COMMIT 落地" if args.commit else "DRY-RUN 預覽(不寫)", run_id))
    print("=" * 68)

    # ---- 0) seed (append-only,只補不覆蓋) ----------------------------------
    seed_added = 0
    if not args.no_seed:
        for term, meta in SEED.items():
            cid = ensure_canonical(vocab, term, meta["domain"], ledger_events, run_id)
            for s in meta["syn"]:
                if add_synonym(vocab, cid, s, EV_HUMAN, "seed", run_id, ledger_events):
                    seed_added += 1
    print(" [0] seed 匯入:canonical=%d,新同義字=%d" % (len(vocab["canonicals"]), seed_added))

    # ---- 1) INGEST live state ----------------------------------------------
    roots = args.corpus or [root]
    own = {os.path.abspath(p) for p in (vocab_path, params_path, ledger_path, html_path)}
    sources = discover_sources(roots, exclude=own)
    freq = {}
    raw_by_norm = {}
    for src in sources:
        for tok in harvest(src):
            tok = tok.strip()
            if not (params["min_token_len"] <= len(tok) <= params["max_token_len"]):
                continue
            if tok.isdigit():          # 純數字不是詞彙
                continue
            nk = norm(tok)
            if not nk:
                continue
            freq[nk] = freq.get(nk, 0) + 1
            raw_by_norm.setdefault(nk, tok.strip())
    print(" [1] 匯入現況:來源 %d 個,唯一 token %d 個" % (len(sources), len(freq)))
    for s in sources[:8]:
        print("       · %s" % os.path.relpath(s, root))

    # ---- 2) EXPAND 自動擴大同義字(確定式變體) -----------------------------
    exp_added = 0
    for cid in list(vocab["canonicals"].keys()):
        c = vocab["canonicals"][cid]
        seeds_terms = [c["term"]] + [s["text"] for s in c["synonyms"]]
        gen = set()
        for t in seeds_terms:
            gen |= variants(t)
        for v in gen:
            if add_synonym(vocab, cid, v, EV_AUTO, "auto:variant", run_id, ledger_events):
                exp_added += 1
    print(" [2] 自動擴大:新增變體同義字 %d 個(evidence=M)" % exp_added)

    # ---- 3) MONITOR 未知 token 就近歸戶 ------------------------------------
    lut = build_lookup(vocab)
    auto_n = ask_n = q_n = known_n = 0
    ask_queue = []
    quarantine_new = []
    for nk, f in freq.items():
        if f < params["min_freq"]:
            continue
        if nk in lut:
            known_n += 1
            continue
        # 找最近 canonical
        best_cid, best_score = None, 0.0
        for cid, c in vocab["canonicals"].items():
            if c.get("status") == ST_ABSORBED:
                continue
            cands = [norm(c["term"])] + [norm(s["text"]) for s in c["synonyms"]]
            for cand in cands:
                sc = match_score(nk, cand)
                if sc > best_score:
                    best_score, best_cid = sc, cid
        raw = raw_by_norm.get(nk, nk)
        if best_score >= params["auto_attach"] and best_cid:
            add_synonym(vocab, best_cid, raw, EV_AUTO, "auto:monitor(%.2f)" % best_score,
                        run_id, ledger_events)
            auto_n += 1
        elif best_score >= params["ask"] and best_cid:
            ask_n += 1
            ask_queue.append({"token": raw, "freq": f, "nearest": best_cid,
                              "nearest_term": vocab["canonicals"][best_cid]["term"],
                              "score": round(best_score, 3)})
        else:
            q_n += 1
            item = {"token": raw, "freq": f,
                    "nearest": best_cid, "score": round(best_score, 3),
                    "decided_run": run_id, "status": "NOVEL"}
            quarantine_new.append(item)
    # 隔離區 append-only
    existing_q = {norm(x["token"]) for x in vocab["quarantine"]}
    for it in quarantine_new:
        if norm(it["token"]) not in existing_q:
            vocab["quarantine"].append(it)
    print(" [3] 監測歸戶:AUTO=%d  ASK=%d  QUARANTINE=%d  (既知 %d)"
          % (auto_n, ask_n, q_n, known_n))

    # ---- 4) REGEX 合成 ------------------------------------------------------
    rx_ok = 0
    for cid in vocab["canonicals"]:
        synth_regex(vocab, cid, params)
        if vocab["canonicals"][cid]["regex"]:
            rx_ok += 1
    print(" [4] regex 合成:%d/%d canonical 具可編譯 regex"
          % (rx_ok, len(vocab["canonicals"])))

    # ---- 5) 統計 ------------------------------------------------------------
    total_syn = sum(len(c["synonyms"]) for c in vocab["canonicals"].values())
    dormant = sum(1 for c in vocab["canonicals"].values() if c["status"] == ST_DORMANT)
    stats = {
        "run": run_id, "mode": "COMMIT" if args.commit else "DRY-RUN",
        "canonicals": len(vocab["canonicals"]),
        "synonyms": total_syn,
        "new_this_run": seed_added + exp_added + auto_n,
        "ask": ask_n, "quarantine": q_n, "dormant": dormant,
        "regex_cov": rx_ok, "sources": len(sources), "tokens": len(freq),
        "ts": now_iso(),
    }

    # ---- 6) COMMIT / DRY-RUN ------------------------------------------------
    vocab["meta"]["runs"] = vocab["meta"].get("runs", 0) + 1
    vocab["meta"]["last_run"] = now_iso()
    if args.commit:
        save_json(params_path, params)
        save_json(vocab_path, vocab)
        for ev in ledger_events:
            append_ledger(ledger_path, ev)
        append_ledger(ledger_path, {"ts": now_iso(), "run": run_id, "op": "RUN_COMMIT", "stats": stats})
        print(" [6] COMMIT:已寫入 %s(+ ledger %d 事件)"
              % (os.path.basename(vocab_path), len(ledger_events) + 1))
    else:
        print(" [6] DRY-RUN:未寫入 SSOT(加 --commit 落地);本次會新增 %d 事件"
              % len(ledger_events))

    write_html(html_path, vocab, stats, ask_queue, params)
    print(" [7] 儀表板:%s" % os.path.basename(html_path))
    print("=" * 68)
    print(" 完成。canonical=%d  同義字=%d  regex覆蓋=%d  ASK=%d  隔離=%d"
          % (stats["canonicals"], stats["synonyms"], stats["regex_cov"],
             stats["ask"], stats["quarantine"]))
    return stats


# =============================================================================
#  Visual Lock HTML dashboard
# =============================================================================
def _chip(text, ev):
    color = {EV_HUMAN: C_UP, EV_AUTO: "#7c8aa5", EV_PEND: "#b0883a"}.get(ev, "#7c8aa5")
    return ('<span class="chip" style="border-color:%s;color:%s">%s'
            '<i>%s</i></span>' % (color, color, html.escape(text), ev))


def write_html(path, vocab, stats, ask_queue, params):
    def card(label, val, color):
        return ('<div class="card"><div class="v" style="color:%s">%s</div>'
                '<div class="l">%s</div></div>' % (color, val, label))

    cards = "".join([
        card("Canonical 詞條", stats["canonicals"], "#e6edf6"),
        card("同義字總數", stats["synonyms"], "#e6edf6"),
        card("本次新增", stats["new_this_run"], C_UP),
        card("待確認 ASK", stats["ask"], "#d9b25a"),
        card("隔離 QUARANTINE", stats["quarantine"], C_UP),
        card("DORMANT 休眠", stats["dormant"], "#7c8aa5"),
        card("regex 覆蓋", "%d/%d" % (stats["regex_cov"], stats["canonicals"]), C_DN),
        card("匯入來源", stats["sources"], "#7c8aa5"),
    ])

    # canonical 表
    rows = []
    for cid, c in sorted(vocab["canonicals"].items(),
                         key=lambda kv: (kv[1]["domain"], kv[1]["term"])):
        chips = "".join(_chip(s["text"], s["evidence"]) for s in c["synonyms"][:40])
        more = "" if len(c["synonyms"]) <= 40 else '<span class="more">+%d…</span>' % (len(c["synonyms"]) - 40)
        rx = html.escape(c["regex"][0]) if c.get("regex") else '<span class="muted">—</span>'
        st_color = {ST_ACTIVE: C_DN, ST_DORMANT: "#7c8aa5", ST_ABSORBED: "#555"}.get(c["status"], "#999")
        rows.append(
            '<tr><td><b>%s</b><div class="code">%s</div></td>'
            '<td><span class="dom">%s</span></td>'
            '<td><span style="color:%s">%s</span></td>'
            '<td class="syn">%s%s</td>'
            '<td class="rx">%s</td></tr>'
            % (html.escape(c["term"]), c["code"], html.escape(c["domain"]),
               st_color, c["status"], chips, more, rx))
    table = "".join(rows)

    # ASK 佇列(預選最佳猜測,一鍵風格)
    aq = sorted(ask_queue, key=lambda x: -x["score"])[:60]
    ask_rows = "".join(
        '<tr><td>%s</td><td class="num">%d</td>'
        '<td>→ <b>%s</b></td><td class="num">%.2f</td></tr>'
        % (html.escape(a["token"]), a["freq"], html.escape(a["nearest_term"]), a["score"])
        for a in aq) or '<tr><td colspan="4" class="muted">本次無待確認候選</td></tr>'

    doc = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA 中央治理 · 同義字/regex SSOT</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b0f17;color:#e6edf6;font:14px/1.5 -apple-system,"Segoe UI","PingFang TC","Microsoft JhengHei",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
.hdr{border:1px solid #1c2740;border-radius:14px;padding:18px 22px;margin-bottom:20px;
 background:linear-gradient(135deg,#0f1626,#0b0f17)}
.hdr h1{margin:0;font-size:18px;letter-spacing:.5px}
.hdr .sub{color:#8fa0bd;font-size:12px;margin-top:6px}
.hdr .tag{display:inline-block;margin-top:10px;padding:3px 10px;border:1px solid #294;border-radius:20px;
 color:#5a9e6f;font-size:11px}
.hdr .mode{margin-left:8px;padding:3px 10px;border-radius:20px;font-size:11px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:12px;margin-bottom:22px}
.card{background:#0f1626;border:1px solid #1c2740;border-radius:12px;padding:14px}
.card .v{font-size:24px;font-weight:700}
.card .l{color:#8fa0bd;font-size:12px;margin-top:2px}
h2{font-size:14px;color:#b7c6e0;border-left:3px solid %(up)s;padding-left:9px;margin:26px 0 12px}
table{width:100%%;border-collapse:collapse;background:#0f1626;border:1px solid #1c2740;border-radius:12px;overflow:hidden}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #16203a;vertical-align:top;font-size:13px}
th{background:#111a2e;color:#8fa0bd;font-weight:600;position:sticky;top:0}
tr:last-child td{border-bottom:none}
.code{color:#5c6f8f;font-size:10px;font-family:ui-monospace,Consolas,monospace;margin-top:3px}
.dom{background:#16203a;color:#9db4dc;padding:2px 8px;border-radius:6px;font-size:11px}
.syn .chip{display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;border:1px solid #444;
 border-radius:14px;font-size:11px;white-space:nowrap}
.syn .chip i{opacity:.6;font-style:normal;margin-left:4px;font-size:9px}
.more{color:#7c8aa5;font-size:11px}
.rx{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#89c0b8;max-width:300px;word-break:break-all}
.num{text-align:right;font-variant-numeric:tabular-nums}
.muted{color:#5c6f8f}
.foot{color:#5c6f8f;font-size:11px;margin-top:24px;text-align:center}
.legend{color:#8fa0bd;font-size:11px;margin:6px 0 0}
.legend b{color:%(up)s}
</style></head><body><div class="wrap">
<div class="hdr">
 <h1>VIA 中央治理引擎 · 同義字 / regex SSOT</h1>
 <div class="sub">Central Governance Engine — 自動擴大 · 自動監測 · 只增不減(append-only)· dry-run 預設 · evidence honesty</div>
 <span class="tag">%(schema)s</span>
 <span class="mode" style="background:%(modebg)s;color:#fff">%(mode)s · %(run)s</span>
 <div class="legend">evidence:&nbsp; <b>V</b>=人工確認&nbsp; <span style="color:#7c8aa5">M</span>=自動衍生(封頂)&nbsp; <span style="color:#b0883a">P</span>=待決</div>
</div>
<div class="grid">%(cards)s</div>
<h2>Canonical 詞條 · 同義字 · 自動 regex</h2>
<table><thead><tr><th>Canonical</th><th>Domain</th><th>狀態</th><th>同義字(chips)</th><th>auto regex</th></tr></thead>
<tbody>%(table)s</tbody></table>
<h2>ASK 待確認佇列(已預選最佳歸戶,確認即升 V)</h2>
<table><thead><tr><th>新 token</th><th>頻次</th><th>建議歸戶</th><th>相似度</th></tr></thead>
<tbody>%(ask)s</tbody></table>
<div class="foot">%(engine)s %(version)s · %(ts)s · 只增不減:同義字永不刪除,退場者轉 DORMANT · regex 均已通過 re.compile 驗證</div>
</div></body></html>""" % {
        "up": C_UP,
        "schema": SCHEMA,
        "mode": stats["mode"],
        "modebg": C_UP if stats["mode"] == "COMMIT" else "#3a4a66",
        "run": stats["run"],
        "cards": cards, "table": table, "ask": ask_rows,
        "engine": ENGINE, "version": VERSION, "ts": stats["ts"],
    }
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)


# =============================================================================
#  CLI
# =============================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog=ENGINE,
        description="VIA 中央治理引擎:自動擴大/監測同義字 + regex SSOT(只增不減,一貼即跑)")
    ap.add_argument("--workdir", default=".", help="工作根目錄(預設當前)")
    ap.add_argument("--corpus", nargs="*", default=None,
                    help="語料來源(檔或資料夾;預設自動掃 workdir)")
    ap.add_argument("--vocab", default=None, help="governance_vocab.json 路徑")
    ap.add_argument("--params", default=None, help="via_cge_params.json 路徑")
    ap.add_argument("--ledger", default=None, help="governance_ledger.jsonl 路徑")
    ap.add_argument("--out-html", default=None, help="HTML 儀表板輸出路徑")
    ap.add_argument("--commit", action="store_true", help="落地寫入 SSOT(預設 dry-run)")
    ap.add_argument("--no-seed", action="store_true", help="不匯入內建種子字典")
    args = ap.parse_args(argv)
    try:
        run_pipeline(args)
        return 0
    except Exception as e:
        print("FATAL: %s" % e)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
