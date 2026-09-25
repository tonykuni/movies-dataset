# -*- coding: utf-8 -*-
r"""WorkOps 回覆解析引擎 v0106(ENG-029)— 規劃書 M3:回信 → 三層 fallback 解析 → 狀態事件

v0106(授權補強 R2:口徑正本化):應答域判定抽為單一事實源 —
  load_scope_context()(conv→THR 映射、已發段留痕、bulk 樣式)+ in_reply_scope()
  (與 v0105 ①分母淨化同式)。cmd_parse 與 ENG-055 ml_lab 共用同一判定,
  replies KPI 與 ml suggest/cluster 分母永遠一致(帳上口徑差 198≠119 就此消除)。

v0105(操作員授權補強令:三方法齊上):
  ①分母淨化 — 未解析只計「應答域」(RE/回覆前綴、已映射 THR、或我方已發追蹤之串;
    bulk/系統寄件者剝除);域外通知另計 n_out 誠實列示,不再污染未解析 KPI。
    域外信仍照常解析 — 有訊號照收事件,只是不佔未解析分母。
  ②body 後備鏈 — scanrange 片段沒配到 conv 時退 corpus.csv(主旨正規化對映,
    取最長 body)— A/Q/E/K 可判母體放大(實測 226/424 封有內文)。
  ③主旨短覆 — body 空時取主旨尾段(剝 RE/FW/回覆/轉寄 前綴後之末段),
    正規化 ≤ack_max_chars 且命中確認詞 → A 層「主旨短覆」。

v0104(實機 FAIL 驅動熱修):cmd_parse 計數器原只開 V/T/K 三格 — A/Q/E 於
  操作員實機首度命中即 KeyError。補滿六層 + counts.get 防炸;彙總行顯示六層。
  教訓:harness 直測 parse_one 未蓋彙總段 → selftest 沙箱信件補 A/E 案例補此洞。

v0101(操作員六機制研究令):三項增能 —
  ① OOO 偵測:收信含 OOO/自動回覆詞 → flags.ooo(⏸窗口休假)+ 內文代理人 email 提示;
    誠實限制:OOO 自動回覆已使該串脫離未回佇列(=實質計時凍結,不誤升級);
    休假結束自動恢復追蹤需 MailOps replied 判定排除 OOO — 候令深改。
  ② 風險語意越級:收信含 risk_terms(違約/律師/breach…)→ flags.risk —
    板端無視工作日數破格直上 T3(⚡);詞庫全 JSON。
  ③ 已發段留痕:掃描索引 OUTBOUND 主旨前綴([再次追蹤]=T1/[急件·再追]=T2/
    [緊急·第三次通知]=T3)→ sent_stage{thr:段,日期} — 板佇列顯示已發到哪段。

操作員 NEXT 令(2026/08/09):Phase 1 閉環最後一段 — 追蹤信寄出(板 [3/5] 三段升級鏈)
→ 對方回信 → 本引擎自動判讀 → 狀態自動更新,人不再逐封讀信。

v0102(UI Phase B 令):未解析樣本(≤40 筆)入 reply_status.json unparsed 欄 — 板 04 確認中心唯讀顯示。

v0103(操作員「大幅提高正確率各類方法」令):V/T/K 之後三新層,全數守誠實閘 —
  A ACK 層   極短回覆(正規化 ≤12 字)命中確認詞(收到/好的/OK/noted…)→「已回覆確認」
             (脫離未回佇列;不冒充完成狀態)
  Q 問句層   回覆以問句收尾/含問號且短 →「對方提問」(球在我方 — 板上紅字提醒)
  E 集成層   三類弱訊號詞庫(完成弱詞/進行弱詞/卡關弱詞)計分投票 — 最高分 ≥2 且
             嚴格領先次高才判(FIS 同號過濾精神:訊號衝突=不判,回未解析)
  詞庫全入 reply_parser_params.json v0102(ack_terms/weak_signals/ensemble_min)。

三層 fallback(規劃書 §01:任一命中即完成狀態識別;都未命中誠實列未解析,絕不猜):
  V 投票層   Outlook VotingResponse 屬性(MailOps Scan v0116 起唯讀匯出)→ 零解析成本
  T token層  信體 ==VMT-CONFIRM== Qn:idx 結構化 token(既有 VMT 機制;Q1=狀態題)
  K 關鍵詞層 回信主旨/內文片段中之狀態詞(reply_parser_params.json 三語同義字)

資料流(全部唯讀既有匯出,零新增 Outlook 觸碰):
  out/mails.csv(INBOUND)× id_ledger(conv→THR)× scanrange BODY_SNIPPET
  → out/reply_events.jsonl(append-only 事實流;冪等=同信不重記)
  → out/reply_status.json(衍生狀態:每 THR 最新判讀;可由事實流重算)
  → 指揮板 ②「最近收到」判讀欄自動顯示

治理:唯讀;誠實(未解析=未解析);只增不減;事實流可重放(F20);參數=JSON。
動詞:parse(預設)/ status
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
import argparse, csv, io, json, re, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from workops_lexicon import norm_subj, load_bulk_patterns, is_bulk  # noqa: E402(共用詞彙正本)

HERE     = Path(__file__).resolve().parent
WORKOPS  = HERE.parent
OUT      = WORKOPS / "out"
PARAMS_P = HERE / "reply_parser_params.json"
MAILS_P  = OUT / "mails.csv"
LEDGER_P = OUT / "workops_id_ledger.json"
EVENTS_P = OUT / "reply_events.jsonl"
STATUS_P = OUT / "reply_status.json"

TOKEN_RE = re.compile(r"==VMT-CONFIRM==\s*Q(\d+)\s*[::]\s*(\d+)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
STAGE_PREFIX = [("[緊急·第三次通知]", "T3"), ("[急件·再追]", "T2"), ("[再次追蹤]", "T1")]
STAGE_RANK = {"T1": 1, "T2": 2, "T3": 3}

DEFAULT_PARAMS = {
    "voting_map": {"進行中": "進行中", "已完成": "已完成", "卡關": "卡關", "需要協助": "需要協助"},
    "q1_options": ["進行中", "已完成", "卡關"],
    "keywords": {
        "已完成": ["已完成", "完成了", "done"],
        "卡關": ["卡關", "卡住", "blocked"],
        "需要協助": ["需要協助", "請協助", "need help"],
        "已口頭說明": ["已口頭說明"],
        "進行中": ["進行中", "處理中", "in progress"],
    },
    "ooo_terms": ["out of office", "automatic reply", "自動回覆", "休假中"],
    "risk_terms": ["違約", "律師", "breach", "penalty"],
    "ack_max_chars": 12,
    "ack_terms": ["收到", "好的", "了解", "瞭解", "沒問題", "谢谢", "謝謝", "ok", "okay", "noted", "thanks", "roger", "got it"],
    "question_max_chars": 60,
    "ensemble_min": 2,
    "weak_signals": {
        "已完成": ["已寄", "已提供", "已回覆", "已更新", "已上傳", "已送出", "如附件", "請查收", "attached", "sent you", "uploaded", "delivered"],
        "進行中": ["正在", "盡快", "安排", "預計", "下週", "下周", "明天", "本週內", "will ", "working on", "eta", "on it"],
        "卡關": ["等待", "尚未", "還沒", "延後", "延誤", "無法", "pending", "waiting", "delay", "cannot", "unable"],
    },
}


def load_json(p, default):
    if Path(p).exists():
        try:
            return json.loads(Path(p).read_text(encoding="utf-8-sig"))
        except Exception:
            return default
    return default


def load_params():
    p = load_json(PARAMS_P, None)
    if not isinstance(p, dict):
        return dict(DEFAULT_PARAMS)
    merged = dict(DEFAULT_PARAMS)
    for k in DEFAULT_PARAMS:
        if k in p:
            merged[k] = p[k]
    return merged


def read_csv(p):
    if not Path(p).exists():
        return []
    try:
        with io.open(p, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def load_scan_index():
    """最新 scanrange RUN:(conv→body, outbound 列[(conv,title,time)])。缺席誠實回空。"""
    root = OUT / "deep" / "scanrange"
    if not root.exists():
        return {}, []
    runs = sorted([d for d in root.iterdir() if d.is_dir() and d.name.startswith("RUN_")])
    if not runs:
        return {}, []
    m, outb = {}, []
    for r in read_csv(runs[-1] / "01_mail_index.csv"):
        cid = (r.get("CONVERSATION_ID") or "").strip()
        bs = (r.get("BODY_SNIPPET") or "").strip()
        if cid and bs and cid not in m:
            m[cid] = bs
        if cid and (r.get("DIRECTION") or "").upper() == "OUTBOUND":
            outb.append((cid, r.get("TITLE") or "", r.get("TIME") or ""))
    return m, outb


REPLY_PFX_RE = re.compile(r"^\s*((re|fw|fwd|回覆|回复|轉寄|转发|答復|答复)\s*[::]\s*)+", re.I)


def norm_subject(s):
    """主旨正規化:剝 RE/FW/回覆 前綴 + 壓空白(body 後備鏈之對映鍵)。"""
    return re.sub(r"\s+", "", REPLY_PFX_RE.sub("", str(s or ""))).lower()


def load_corpus_bodies():
    """v0105 body 後備鏈:corpus.csv 主旨正規化 → 最長 body。缺席誠實回空。"""
    p = OUT / "deep" / "corpus" / "corpus.csv"
    m = {}
    for r in read_csv(p):
        k = norm_subject(r.get("subject"))
        b = (r.get("body") or "").strip()
        if k and b and len(b) > len(m.get(k, "")):
            m[k] = b
    return m


def body_for(bodies, corpus, conv, subject):
    """取信體:scanrange conv 直配 → corpus 主旨後備。"""
    b = bodies.get(conv, "")
    if b:
        return b
    return corpus.get(norm_subject(subject), "")


def detect_flags(row, body, params):
    """v0101:OOO 與風險語意(獨立於狀態判讀;flags 不覆蓋 V/T/K 結果)。"""
    text = ((row.get("Subject") or "") + "\n" + (body or "")).lower()
    ooo = any(t.lower() in text for t in params.get("ooo_terms", []))
    hits = [t for t in params.get("risk_terms", []) if t.lower() in text]
    agent = ""
    if ooo:
        own = (row.get("SenderEmail") or "").lower()
        for em in EMAIL_RE.findall(body or ""):
            if em.lower() != own:
                agent = em
                break
    return ooo, hits, agent


def parse_one(row, body, params):
    """單封回信三層 fallback。回 (layer, status, evidence) 或 None(誠實未解析)。"""
    vr = (row.get("VotingResponse") or "").strip()
    if vr:
        st = params["voting_map"].get(vr) or params["voting_map"].get(vr.strip("!。."))
        if st:
            return "V", st, "投票鈕 " + vr
    text = (row.get("Subject") or "") + "\n" + (body or "")
    m = TOKEN_RE.search(text)
    if m:
        qn, idx = int(m.group(1)), int(m.group(2))
        if qn == 1 and 0 <= idx < len(params["q1_options"]):
            return "T", params["q1_options"][idx], "token Q%d:%d" % (qn, idx)
    low = text.lower()
    for st, words in params["keywords"].items():
        for wd in words:
            if wd.lower() in low:
                return "K", st, "關鍵詞「%s」" % wd
    # ---- v0103 各類方法(誠實閘:寧未解析不亂判)----
    core = re.sub(r"[\s。,,!!??\~~\.…]+", "", (body or ""))
    # A ACK 短覆層:極短且命中確認詞 → 已回覆確認(脫離未回佇列,不冒充完成)
    if 0 < len(core) <= int(params.get("ack_max_chars", 12)):
        for t in params.get("ack_terms", []):
            if t.lower() in core.lower():
                return "A", "已回覆確認", "ACK 短覆「%s」" % core[:12]
    # v0105 ③主旨短覆:body 空時取主旨尾段(剝 RE/FW 前綴後之末段)
    if not (body or "").strip():
        tail = re.split(r"[-—:|/]", REPLY_PFX_RE.sub("", (row.get("Subject") or "")))[-1]
        tcore = re.sub(r"[\s。,,!!??\~~\.…]+", "", tail)
        if 0 < len(tcore) <= int(params.get("ack_max_chars", 12)):
            for t in params.get("ack_terms", []):
                if t.lower() in tcore.lower():
                    return "A", "已回覆確認", "主旨短覆「%s」" % tcore[:12]
    # Q 問句層:含問號且短 → 對方提問(球在我方)
    if ("?" in (body or "") or "?" in (body or "")) and len(core) <= int(params.get("question_max_chars", 60)):
        return "Q", "對方提問", "問句回覆(需我方回答)"
    # E 弱訊號集成層:三類弱詞計分,最高分 ≥ ensemble_min 且嚴格領先次高才判
    ws = params.get("weak_signals", {})
    scores = {}
    ev = {}
    for st, words in ws.items():
        hits = [w for w in words if w.lower() in low]
        if hits:
            scores[st] = len(hits)
            ev[st] = hits
    if scores:
        rank = sorted(scores.items(), key=lambda kv: -kv[1])
        top_st, top_n = rank[0]
        second = rank[1][1] if len(rank) > 1 else 0
        if top_n >= int(params.get("ensemble_min", 2)) and top_n > second:
            return "E", top_st, "弱訊號集成 %d 票「%s」" % (top_n, "、".join(ev[top_st][:3]))
    return None


def load_seen():
    """冪等:既有事件之 (conv, mail_date) 集合;壞列隔離不阻斷(F19)。"""
    seen = set()
    if EVENTS_P.exists():
        for ln in EVENTS_P.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                seen.add((r.get("conv", ""), r.get("mail_date", "")))
            except Exception:
                continue
    return seen


BULK_BUILTIN = ["no-reply", "noreply", "donotreply", "newsletter", "epaper"]


def build_sent_stage(outbound, conv2thr):
    """已發段留痕:OUTBOUND 主旨段前綴 → {thr: {stage, date}}(同串取最高段)。"""
    sent_stage = {}
    for conv, title, tm in outbound:
        for pfx, stg in STAGE_PREFIX:
            if pfx in (title or ""):
                thr0 = conv2thr.get(conv, "") or conv
                cur = sent_stage.get(thr0)
                if cur is None or STAGE_RANK[stg] > STAGE_RANK[cur["stage"]]:
                    sent_stage[thr0] = {"stage": stg, "date": tm}
                break
    return sent_stage


def load_scope_context(outbound=None):
    """v0106 應答域口徑正本 — cmd_parse 與 ENG-055 ml_lab 共用同一判定基礎。
    回傳 (conv2thr, sent_stage, bulk_pats);outbound 可注入避免重掃索引。"""
    led = load_json(LEDGER_P, {"map": {}})
    conv2thr = {k[4:]: v for k, v in led.get("map", {}).items() if k.startswith("THR|")}
    if outbound is None:
        _, outbound = load_scan_index()
    return conv2thr, build_sent_stage(outbound, conv2thr), load_bulk_patterns() + BULK_BUILTIN


def in_reply_scope(row, conv2thr, sent_stage, bulk_pats):
    """應答域判定(v0105 ①分母淨化同式):bulk/系統寄件者=域外;
    RE 前綴、已映射 THR、或我方已發追蹤之串=應答域。"""
    if is_bulk(row.get("SenderEmail"), bulk_pats):
        return False
    conv = (row.get("ConversationID") or "").strip()
    thr0 = conv2thr.get(conv, "") or conv
    return (bool(REPLY_PFX_RE.match(row.get("Subject") or ""))
            or conv in conv2thr or thr0 in sent_stage)


def cmd_parse():
    mails = read_csv(MAILS_P)
    if not mails:
        print("[FAIL] out\\mails.csv 不在位 — 先跑 via-workops(板掃描)")
        return 1
    bodies, outbound = load_scan_index()
    corpus = load_corpus_bodies()
    conv2thr, sent_stage, bulk_pats = load_scope_context(outbound=outbound)
    params = load_params()
    seen = load_seen()
    from datetime import datetime
    now = datetime.now().isoformat(timespec="seconds")
    counts = {"V": 0, "T": 0, "K": 0, "A": 0, "Q": 0, "E": 0}
    n_un = n_dup = n_out = 0
    un_sample = []
    events = []
    flags = {}
    for r in mails:
        if (r.get("Direction") or "").upper() not in ("", "INBOUND"):
            continue
        conv = (r.get("ConversationID") or "").strip()
        if not conv:
            continue
        key = (conv, (r.get("EventDate") or "").strip())
        if key in seen:
            n_dup += 1
            continue
        b = body_for(bodies, corpus, conv, r.get("Subject"))
        ooo, risks, agent = detect_flags(r, b, params)
        thr0 = conv2thr.get(conv, "") or conv
        if ooo or risks:
            fl = flags.setdefault(thr0, {})
            if ooo:
                fl["ooo"] = True
                if agent:
                    fl["agent_hint"] = agent
            if risks:
                fl["risk"] = True
                fl["risk_terms"] = sorted(set(fl.get("risk_terms", []) + risks))
        got = parse_one(r, b, params)
        if got is None:
            # ①分母淨化:未解析只計應答域;v0106 起判定抽為 in_reply_scope,與 ml_lab 共用同式
            if not in_reply_scope(r, conv2thr, sent_stage, bulk_pats):
                n_out += 1
                continue
            n_un += 1
            if len(un_sample) < 40:
                un_sample.append({"thr": conv2thr.get(conv, ""), "subj": (r.get("Subject") or "")[:60],
                                  "from": r.get("SenderEmail", "")})
            continue
        layer, st, ev = got
        counts[layer] = counts.get(layer, 0) + 1
        events.append({"ts": now, "thr": conv2thr.get(conv, ""), "conv": conv,
                       "mail_date": key[1], "layer": layer, "status": st,
                       "evidence": ev, "sender": r.get("SenderEmail", ""),
                       "subject": (r.get("Subject") or "")[:80]})
        seen.add(key)
    if events:
        OUT.mkdir(parents=True, exist_ok=True)
        with io.open(EVENTS_P, "a", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    # 衍生狀態:事實流全量重算(F20:狀態=事件重放,不手改)
    status = {}
    if EVENTS_P.exists():
        for ln in EVENTS_P.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                e = json.loads(ln)
            except Exception:
                continue
            t = e.get("thr") or e.get("conv")
            if not t:
                continue
            cur = status.get(t)
            if cur is None or (e.get("mail_date", "") >= cur.get("mail_date", "")):
                status[t] = {"status": e["status"], "layer": e["layer"],
                             "mail_date": e.get("mail_date", ""), "evidence": e.get("evidence", "")}
    tmp = STATUS_P.with_suffix(".tmp")
    tmp.write_text(json.dumps({"version": "v0106", "updated": now, "status": status,
                               "flags": flags, "sent_stage": sent_stage,
                               "unparsed": {"n": n_un, "sample": un_sample, "out_of_scope": n_out}},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATUS_P)
    print("[解析] 新事件 %d(投票 %d · token %d · 關鍵詞 %d · ACK %d · 問句 %d · 集成 %d)· 已記略過 %d · 未解析 %d(應答域;誠實不猜)· 域外/系統信 %d 不計分母"
          % (len(events), counts["V"], counts["T"], counts["K"],
             counts["A"], counts["Q"], counts["E"], n_dup, n_un, n_out))
    n_ooo = sum(1 for f in flags.values() if f.get("ooo"))
    n_risk = sum(1 for f in flags.values() if f.get("risk"))
    if n_ooo or n_risk or sent_stage:
        print("[旗標] ⏸OOO %d 串 · ⚡風險 %d 串 · 已發段留痕 %d 串" % (n_ooo, n_risk, len(sent_stage)))
    print("[狀態] %d 串有判讀 → %s(板 ② 最近收到自動顯示)" % (len(status), STATUS_P.name))
    return 0


def cmd_status():
    d = load_json(STATUS_P, {})
    st = d.get("status", {})
    if not st:
        print("[空] 尚無判讀 — via-workops replies 先解析")
        return 0
    for t in sorted(st):
        e = st[t]
        print("%s · %s(%s 層 · %s)" % (t, e["status"], e["layer"], e.get("mail_date", "")))
    return 0


def main():
    ap = argparse.ArgumentParser(description="M3 回覆解析:投票→token→關鍵詞三層 fallback(未中誠實不猜)")
    ap.add_argument("command", nargs="?", default="parse", choices=["parse", "status"])
    a = ap.parse_args()
    return cmd_parse() if a.command == "parse" else cmd_status()


if __name__ == "__main__":
    sys.exit(main())
