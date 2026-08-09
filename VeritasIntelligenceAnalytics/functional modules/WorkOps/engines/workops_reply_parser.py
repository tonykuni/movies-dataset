# -*- coding: utf-8 -*-
r"""WorkOps 回覆解析引擎 v0101(ENG-029)— 規劃書 M3:回信 → 三層 fallback 解析 → 狀態事件

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
import argparse, csv, io, json, re, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from workops_lexicon import norm_subj  # noqa: E402(共用詞彙正本)

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


def cmd_parse():
    mails = read_csv(MAILS_P)
    if not mails:
        print("[FAIL] out\\mails.csv 不在位 — 先跑 via-workops(板掃描)")
        return 1
    led = load_json(LEDGER_P, {"map": {}})
    conv2thr = {k[4:]: v for k, v in led.get("map", {}).items() if k.startswith("THR|")}
    bodies, outbound = load_scan_index()
    params = load_params()
    seen = load_seen()
    from datetime import datetime
    now = datetime.now().isoformat(timespec="seconds")
    counts = {"V": 0, "T": 0, "K": 0}
    n_un = n_dup = 0
    events = []
    flags = {}
    sent_stage = {}
    for conv, title, tm in outbound:
        for pfx, stg in STAGE_PREFIX:
            if pfx in (title or ""):
                thr0 = conv2thr.get(conv, "") or conv
                cur = sent_stage.get(thr0)
                if cur is None or STAGE_RANK[stg] > STAGE_RANK[cur["stage"]]:
                    sent_stage[thr0] = {"stage": stg, "date": tm}
                break
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
        b = bodies.get(conv, "")
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
            n_un += 1
            continue
        layer, st, ev = got
        counts[layer] += 1
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
    tmp.write_text(json.dumps({"version": "v0101", "updated": now, "status": status,
                               "flags": flags, "sent_stage": sent_stage},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATUS_P)
    print("[解析] 新事件 %d(投票 %d · token %d · 關鍵詞 %d)· 已記略過 %d · 未解析 %d(誠實不猜)"
          % (len(events), counts["V"], counts["T"], counts["K"], n_dup, n_un))
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
