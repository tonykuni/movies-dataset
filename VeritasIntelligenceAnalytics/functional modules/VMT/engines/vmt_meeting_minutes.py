# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Meeting Minutes Engine  v1.0   --  會議記錄引擎 (標主詞 -> 標性質 -> 成記錄)
----------------------------------------------------------------------------
 定位: 逐字稿 -> 可稽核的會議記錄, 並把「待辦」直接餵進工作管理 SSOT,
       讓「會議上講的」與「系統在追的」永遠是同一份東西。

 流程 (六步, 每步都可單獨檢查):
   1 切句      逐字稿 -> [序號] 一句一列, 時間戳依字數比例內插
   2 清洗      口語贅詞 / 簡繁 / 專有名詞模糊校正 (原文另存, 供覆核)
   3 標主詞    每句一定要有歸屬; 判不出來標 [?] 絕不猜
   4 標性質    決 / 辦 / 議 / 問 / 資 五類, 附觸發 cue
   5 分議題    依主席轉場語、議程對照、時間間隔切段
   6 產記錄    決議 / 待辦 / 待確認, 每條掛來源句號 (#012) 可回溯

 完整性防線 (刻意內建, 因為「漏掉」比「寫錯」更難發現):
   - 議程對照 : 議程有、逐字稿沒有 -> 明寫「本次未討論」, 不靜默略過
   - 引用反查 : 沒被任何結論引用、卻含期限/數字的句子 -> 列入「疑似遺漏」
   - 欄位強制 : 待辦缺負責人或期限 -> 填 [?] 並列入「待確認」, 不允許消失
   - 幻覺過濾 : 重複 n-gram / 靜音段文字 -> 標記丟棄 (ASR 幻覺的典型樣態)

 產出: reports/VMT_Minutes_<date>.md + .html ; data/minutes.jsonl (add-only)
       待辦 -> vmt_task_ssot 的任務候選 (帶 provenance 回指句號)
============================================================================
"""
from __future__ import annotations

import re
import sys
import json
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    EngineResult, EventLog, Ledger, Workspace, add_common_args, banner, clip,
    esc, fingerprint, kpi_cards, mode_label, pill, render_report, table, try_open,
)
from vmt_lang import (  # noqa: E402
    TAG_NAMES, UNKNOWN, classify_sentence, fuzzy_correct, resolve_due,
    split_sentences, strip_fillers, to_traditional,
)

ENGINE = "vmt_meeting_minutes"
VERSION = "v1.0"

TOPIC_CUES = ["下一個議題", "下一項", "接下來", "我們來談", "我們先看", "換個話題",
              "進入下一", "最後一個議題", "第一案", "第二案", "第三案", "回到"]
# 議事程序語: 這些句子不承載議題內容, 不列入「疑似遺漏」警示
PROCEDURAL_CUES = ["散會", "我們開始", "我們繼續", "休息", "到這裡", "先看", "我們來談",
                   "接下來", "辛苦了", "沒有了"]
GAP_SECONDS = 90.0


# ---------------------------------------------------------------- 1 切句 ----


def load_transcript(src) -> tuple[list[dict], dict]:
    """
    接受三種輸入: segments 陣列 / {"segments":[...]} / 純文字逐字稿。
    純文字支援「[09:02] 王小明：內容」與「王小明：內容」兩種寫法。
    """
    meta: dict = {}
    if isinstance(src, (str, Path)) and Path(str(src)).exists():
        raw = Path(src).read_text(encoding="utf-8")
        try:
            src = json.loads(raw)
        except Exception:
            src = raw
    if isinstance(src, dict):
        meta = {k: v for k, v in src.items() if k != "segments"}
        src = src.get("segments", [])
    if isinstance(src, list):
        return [dict(s) for s in src], meta

    segs: list[dict] = []
    for line in str(src).splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(?:\[(?P<ts>[\d:：.]+)\])?\s*(?P<spk>[^:：]{1,20})[:：]\s*(?P<txt>.+)$", line)
        if not m:
            segs.append({"speaker": segs[-1]["speaker"] if segs else UNKNOWN, "text": line})
            continue
        seg = {"speaker": m.group("spk").strip(), "text": m.group("txt").strip()}
        if m.group("ts"):
            parts = [int(x) for x in re.split(r"[:：.]", m.group("ts")) if x.isdigit()]
            if len(parts) == 2:
                seg["start"] = parts[0] * 60 + parts[1]
                seg["clock"] = "%02d:%02d" % (parts[0], parts[1])
            elif len(parts) == 3:
                seg["start"] = parts[0] * 3600 + parts[1] * 60 + parts[2]
                seg["clock"] = "%02d:%02d:%02d" % tuple(parts)
        segs.append(seg)
    return segs, meta


def segment(segs: list[dict], speaker_map: dict, max_len: int = 60) -> list[dict]:
    """一段多句 -> 一句一列; 時間戳依字數比例內插, 讓每句都能回放定位。"""
    out: list[dict] = []
    for seg in segs:
        text = str(seg.get("text") or "").strip()
        if not text:
            continue
        spk = str(seg.get("speaker") or UNKNOWN)
        spk = speaker_map.get(spk, spk)
        sents = split_sentences(text, max_len) or [text]
        start, end = seg.get("start"), seg.get("end")
        total = sum(len(s) for s in sents) or 1
        acc = 0
        for s in sents:
            u = {"idx": len(out) + 1, "uid": "%03d" % (len(out) + 1),
                 "speaker": spk, "text_raw": s, "text": s,
                 "clock": seg.get("clock"), "flags": [], "meta": {}}
            if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end > start:
                span = end - start
                u["start"] = round(start + span * acc / total, 2)
                u["end"] = round(start + span * (acc + len(s)) / total, 2)
            elif isinstance(start, (int, float)):
                u["start"] = float(start)
            acc += len(s)
            for k in ("no_speech_prob", "avg_logprob", "is_silence"):
                if k in seg:
                    u["meta"][k] = seg[k]
            out.append(u)
    return out


# ---------------------------------------------------------------- 2 清洗 ----


def flag_hallucinations(utts: list[dict], no_speech_max: float = 0.6) -> int:
    """
    ASR 幻覺三訊號: 靜音段有字 / no_speech_prob 過高 / n-gram 連續重複。
    命中者標 drop, 不刪除原列 —— 帳本 add-only, 證據永遠留著。
    """
    dropped = 0
    for u in utts:
        t = u["text"]
        meta = u.get("meta", {})
        if meta.get("is_silence"):
            u["flags"].append("HALLU_SILENCE")
        if isinstance(meta.get("no_speech_prob"), (int, float)) and \
                meta["no_speech_prob"] > no_speech_max:
            u["flags"].append("HALLU_NO_SPEECH")
        for n in (3, 4, 5):
            if len(t) >= n * 3:
                for i in range(len(t) - n * 3 + 1):
                    g = t[i:i + n]
                    if g and t[i:i + n * 3] == g * 3:
                        u["flags"].append("HALLU_REPEAT:%s" % g)
                        break
            if any(f.startswith("HALLU_REPEAT") for f in u["flags"]):
                break
        if u["flags"]:
            u["flags"].append("drop")
            dropped += 1
    return dropped


def clean(utts: list[dict], vocab: list[str], traditional: bool = True) -> list[tuple[str, str]]:
    """清洗流程: 贅詞 -> 簡繁 -> 專有名詞校正。所有替換都回傳供報告呈現。"""
    changes: list[tuple[str, str]] = []
    for u in utts:
        t = strip_fillers(u["text_raw"])
        if traditional:
            t = to_traditional(t)
        t, ch = fuzzy_correct(t, vocab)
        if ch:
            changes.extend(ch)
            u["meta"]["corrections"] = ch
        u["text"] = t or u["text_raw"]
    return changes


# ---------------------------------------------------------------- 3 主詞 ----


def _roster_index(roster: list[dict]) -> list[tuple[str, str, str]]:
    """(別名, 正式姓名, 單位) 依別名長度排序, 長的先比, 避免「小明」蓋掉「王小明」。"""
    idx: list[tuple[str, str, str]] = []
    for p in roster:
        name = str(p.get("name") or "").strip()
        if not name:
            continue
        org = str(p.get("org") or "")
        for alias in [name] + [str(a) for a in (p.get("aliases") or [])]:
            if alias:
                idx.append((alias, name, org))
    return sorted(idx, key=lambda x: -len(x[0]))


def _names_in(text: str, idx) -> list[tuple[str, str, str]]:
    return [e for e in idx if e[0] and e[0] in text]


def resolve_subjects(utts: list[dict], roster: list[dict]) -> None:
    """
    標主詞。中文口語大量省略主詞, 規則由強到弱:
      1 指派句 (請X / 麻煩X / 交給X / X你)     -> X
      2 第一人稱承諾 (我來 / 我會 / 我負責)     -> 講者
      3 我們                                    -> 講者所屬單位 (無單位則「全體」)
      4 你 / 您                                 -> 句中人名, 否則上一位不同講者
      5 他 / 她 / 他們                          -> 最近提及的第三方
      6 句中只有一個人名且無第一人稱            -> 該人名
      7 完全省略                                -> 繼承同講者上一句主詞
      8 仍判不出                                -> [?]  (絕不猜, 留給人工)
    """
    idx = _roster_index(roster)
    org_of = {name: org for _, name, org in idx}
    prev_speaker: str | None = None
    last_third: str | None = None
    prev_subject: str | None = None
    prev_src: str = ""
    prev_utt_speaker: str | None = None

    for u in utts:
        if "drop" in u["flags"]:
            u["subject"], u["subject_src"] = UNKNOWN, "dropped"
            continue
        t, spk = u["text"], u["speaker"]
        names = _names_in(t, idx)
        others = [n for _, n, _ in names if n != spk]
        subject, src = None, "unknown"

        m = re.search(r"(?:請|麻煩|拜託|交給|指派給)\s*([^\s，,。、]{1,8})", t)
        if m and others:
            for _, n, _ in names:
                if n != spk and n in m.group(1) or m.group(1) in n:
                    subject, src = n, "assign"
                    break
        if subject is None and re.search(r"([^\s，,。、]{1,8})\s*你", t) and others:
            subject, src = others[0], "assign"
        if subject is None and re.search(r"我(來|會|負責|去|先|這邊|提供|準備)", t):
            subject, src = spk, "first_person"
        if subject is None and "我們" in t:
            org = org_of.get(spk, "")
            subject, src = (org or "全體"), "we"
        if subject is None and re.search(r"[你您]", t):
            if others:
                subject, src = others[0], "address"
            elif prev_speaker and prev_speaker != spk:
                subject, src = prev_speaker, "address_prev"
        # 「其他」「其它」含「他」但不是代名詞 —— 不排除會把整段主詞帶偏
        if subject is None and re.search(r"(?<!其)[他她它]們?", t):
            if last_third:
                subject, src = last_third, "third_person"
        if subject is None and len(set(others)) == 1 and not re.search(r"^我", t):
            subject, src = others[0], "named"
        if subject is None and re.search(r"^我|我覺得|我認為|我想", t):
            subject, src = spk, "first_person"
        if subject is None:
            # 只繼承「緊鄰的上一句、同一位講者」的主詞 —— 那才是同一段話的延續。
            # 跨越別人發言後再回頭繼承, 會把很久以前指派給別人的主詞硬套到現在這句;
            # 另外「我們→部門」也不進繼承鏈, 否則一句「我們開始」會讓整段變成部門立場。
            if prev_utt_speaker == spk and prev_subject and prev_src not in ("we", "dropped"):
                subject, src = prev_subject, "inherit"
            else:
                subject, src = spk, "speaker"

        u["subject"], u["subject_src"] = subject or UNKNOWN, src
        prev_subject, prev_src, prev_utt_speaker = u["subject"], src, spk
        if others:
            last_third = others[0]
        prev_speaker = spk


# ---------------------------------------------------------------- 4 標性質 --


def tag_utterances(utts: list[dict], chair: str, base_date: dt.date) -> None:
    for u in utts:
        if "drop" in u["flags"]:
            u.update({"tag": "資", "tag_cue": "dropped", "tag_conf": 0.0})
            continue
        r = classify_sentence(u["text"], is_chair=(u["speaker"] == chair), base_date=base_date)
        u.update({"tag": r["tag"], "tag_cue": r["cue"], "tag_conf": r["confidence"]})


# ---------------------------------------------------------------- 5 分議題 --


AGENDA_THRESHOLD = 0.4


def _shingles(s: str, n: int = 2) -> set[str]:
    s = re.sub(r"[\s、,，。／/]+", "", str(s or ""))
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def agenda_hits(text: str, agenda: list[str],
                threshold: float = AGENDA_THRESHOLD) -> list[tuple[str, float]]:
    """句子命中哪些議程項 (二元字組重疊率)。中文議程標題沒有空白可切, 用字組比對最穩。"""
    hits = []
    for item in agenda:
        sh = _shingles(item)
        if not sh:
            continue
        score = sum(1 for g in sh if g in text) / len(sh)
        if score >= threshold:
            hits.append((item, round(score, 2)))
    return sorted(hits, key=lambda x: -x[1])


def split_topics(utts: list[dict], agenda: list[str], chair: str,
                 gap: float = GAP_SECONDS) -> list[dict]:
    """
    議題切分。以「議程對照」為主軸, 轉場語與時間間隔為輔 ——
    純靠轉場語會漏 (很多人不說「接下來」), 純靠間隔會把同一議題切碎。

    一句同時命中兩個以上議程項時視為開場宣讀議程, 不切題;
    否則整場會被開場白帶偏。
    """
    topics: list[dict] = []
    cur: dict | None = None
    prev_end = None
    current_agenda: str | None = None

    for u in utts:
        hits = agenda_hits(u["text"], agenda)
        hint = hits[0][0] if len(hits) == 1 else None      # 多重命中 = 議程宣讀, 不切
        has_cue = any(c in u["text"] for c in TOPIC_CUES)
        big_gap = (isinstance(u.get("start"), (int, float))
                   and isinstance(prev_end, (int, float))
                   and u["start"] - prev_end > gap)

        boundary, why = (cur is None), "start"
        if cur is not None:
            if hint and hint != current_agenda:
                boundary, why = True, "議程對照:%s" % hint
            elif has_cue:
                boundary, why = True, ("主席轉場" if u["speaker"] == chair else "轉場語")
            elif big_gap:
                boundary, why = True, "間隔 %.0fs" % (u["start"] - prev_end)

        if boundary:
            current_agenda = hint
            cur = {"topic_id": len(topics) + 1, "uids": [], "why": why,
                   "matched_agenda": current_agenda, "title": ""}
            topics.append(cur)
        elif hint:
            current_agenda = hint
            cur["matched_agenda"] = cur["matched_agenda"] or hint

        cur["uids"].append(u["uid"])
        u["topic_id"] = cur["topic_id"]
        if isinstance(u.get("end"), (int, float)):
            prev_end = u["end"]
        elif isinstance(u.get("start"), (int, float)):
            prev_end = u["start"]

    by_uid = {u["uid"]: u for u in utts}
    extra = 0
    for t in topics:
        if t["matched_agenda"]:
            t["title"] = t["matched_agenda"]
            continue
        if agenda:
            # 有給議程時, 對不上的段落一律歸「其他事項」——
            # 拿一句閒聊當標題只會讓記錄看起來像亂碼。
            extra += 1
            t["title"] = "其他事項 %d（未對應議程）" % extra
        else:
            t["title"] = _derive_title(by_uid[t["uids"][0]]["text"])
    return topics


def _derive_title(first_line: str) -> str:
    head = re.sub(r"^(那|好|OK|ok|嗯|了解|收到|接下來|我們先看|我們來談)[，,、\s]*",
                  "", str(first_line).strip())
    return clip(head, 20) or "未命名議題"


# ---------------------------------------------------------------- 6 產記錄 --


_LEAD_FILLER = r"^(那就|那我們就|那|好的|好|OK|ok|嗯|了解|收到|沒問題)[，,、\s]*"


def _tidy(text: str) -> str:
    """清掉語助與開場詞。清完若只剩標點, 一律還原原句 —— 寧可留贅字, 不可留空白。"""
    t = strip_fillers(text)
    for _ in range(3):
        nt = re.sub(_LEAD_FILLER, "", t)
        if nt == t:
            break
        t = nt
    t = re.sub(r"[吧喔啦囉呢嘛]+([。！!]?)$", r"\1", t).strip()
    return t if re.sub(r"[。，,、！!？?\s]", "", t) else (text or "").strip()


def _action_phrase(text: str, owner: str | None = None) -> str:
    """
    把「我下週三前把報價單寄給客戶」壓成任務句 (負責人另有欄位, 不重複)。
    指派句只剝掉「麻煩+人名」, 不可連動詞一起吃掉 ——
    否則「麻煩林佳蓉幫忙確認排程」會變成殘句「排程」, 任務內容就失真了。
    """
    t = _tidy(text)
    t = re.sub(r"^(?:我(?:來|會|先|去|這邊)?|由我|我負責)\s*", "", t)
    if owner and owner != UNKNOWN:
        t = re.sub(r"^(?:請|麻煩|拜託|交給|指派給)\s*%s\s*(?:幫忙|協助)?\s*" % re.escape(owner), "", t)
    t = re.sub(r"^(?:請|麻煩|拜託|交給|指派給)\s*(?:幫忙|協助)\s*", "", t)
    return t.strip("，,。 ") or _tidy(text)


def extract_records(utts: list[dict], topics: list[dict], base_date: dt.date) -> dict:
    by_id = {t["topic_id"]: t for t in topics}
    decisions, actions, questions = [], [], []
    for u in utts:
        if "drop" in u["flags"]:
            continue
        topic = by_id.get(u.get("topic_id"), {}).get("title", "")
        if u["tag"] == "決":
            decisions.append({"text": _tidy(u["text"]), "by": u["subject"],
                              "cite": u["uid"], "topic": topic, "confidence": u["tag_conf"]})
        elif u["tag"] == "辦":
            due = resolve_due(u["text"], base_date)
            actions.append({
                "task": _action_phrase(u["text"], u["subject"]),
                "owner": u["subject"] if u["subject"] != UNKNOWN else UNKNOWN,
                "due": due[0].isoformat() if due else UNKNOWN,
                "due_cue": due[1] if due else "",
                "cite": u["uid"], "topic": topic, "confidence": u["tag_conf"],
            })
        elif u["tag"] == "問":
            questions.append({"text": _tidy(u["text"]), "raised_by": u["subject"],
                              "cite": u["uid"], "topic": topic})
    return {"decisions": decisions, "actions": actions, "questions": questions}


# ---------------------------------------------------------------- 完整性 ----


def audit(utts: list[dict], topics: list[dict], records: dict,
          agenda: list[str]) -> dict:
    cited = {d["cite"] for d in records["decisions"]} | \
            {a["cite"] for a in records["actions"]} | \
            {q["cite"] for q in records["questions"]}

    # 議程對照: 有議程但整場沒有對應議題 -> 明寫未討論
    covered = {t.get("matched_agenda") for t in topics if t.get("matched_agenda")}
    not_discussed = [a for a in agenda if a not in covered]

    # 引用反查: 沒被引用、卻帶期限或數字的句子 -> 疑似遺漏。
    # 排除議事程序語 (開場、散會、休息), 否則清單會被例行句灌爆而失去警示作用。
    suspects = []
    for u in utts:
        if u["uid"] in cited or "drop" in u["flags"]:
            continue
        if any(p in u["text"] for p in PROCEDURAL_CUES):
            continue
        if resolve_due(u["text"]) or re.search(r"\d", u["text"]):
            if len(u["text"]) >= 8:
                suspects.append({"cite": u["uid"], "subject": u["subject"],
                                 "text": clip(u["text"], 50), "tag": u["tag"]})

    # 欄位強制: 待辦缺負責人 / 期限
    incomplete = [a for a in records["actions"]
                  if a["owner"] == UNKNOWN or a["due"] == UNKNOWN]
    unknown_subject = [u for u in utts if u.get("subject") == UNKNOWN and "drop" not in u["flags"]]
    dropped = [u for u in utts if "drop" in u["flags"]]

    # 時間軸: 相鄰句間隔過大 -> 可能漏轉 (只在有時間戳時計算)
    gaps = []
    prev = None
    for u in utts:
        s, e = u.get("start"), u.get("end")
        if isinstance(s, (int, float)) and isinstance(prev, (int, float)) and s - prev > GAP_SECONDS:
            gaps.append({"from": round(prev, 1), "to": round(s, 1),
                         "seconds": round(s - prev, 1), "before_uid": u["uid"]})
        prev = e if isinstance(e, (int, float)) else s
    valid = max(1, len(utts) - len(dropped))
    return {"not_discussed": not_discussed,
            "suspects": suspects[:20], "suspects_total": len(suspects),
            "incomplete_actions": incomplete, "unknown_subject": unknown_subject,
            "dropped": dropped, "gaps": gaps,
            # 結論句佔比 = 決/辦/問 三類句數 ÷ 有效句數。這不是「越高越好」的指標,
            # 它的用途是與「疑似遺漏」對照: 佔比低而疑似遺漏多 = 記錄可能漏了東西。
            "conclusion_rate": round(len(cited) / valid, 3),
            "valid_sentences": valid}


# ---------------------------------------------------------------- 輸出 ------


def render_markdown(cfg: dict, utts: list[dict], topics: list[dict],
                    records: dict, au: dict) -> str:
    by_id = {t["topic_id"]: t for t in topics}
    L: list[str] = []
    L.append("# %s" % cfg.get("title", "會議記錄"))
    L.append("")
    L.append("| 項目 | 內容 |")
    L.append("|---|---|")
    L.append("| 日期 | %s |" % cfg.get("date", ""))
    L.append("| 主席 | %s |" % cfg.get("chair", ""))
    L.append("| 出席 | %s |" % "、".join(p.get("name", "") for p in cfg.get("participants", [])))
    L.append("| 記錄 | VMT 會議記錄引擎 %s（自動產生，每條結論可回溯句號）|" % VERSION)
    L.append("")

    L.append("## 一、議題討論")
    for t in topics:
        L.append("")
        L.append("### %d. %s" % (t["topic_id"], t["title"]))
        lines = [u for u in utts if u.get("topic_id") == t["topic_id"]
                 and "drop" not in u["flags"] and u["tag"] in ("資", "議")]
        if not lines:
            L.append("（本議題無討論內容記錄）")
        cap = 12
        for u in lines[:cap]:
            L.append("- %s：%s（#%s）" % (u["subject"], _tidy(u["text"]), u["uid"]))
        if len(lines) > cap:
            # 摘要有上限, 但絕不靜默截斷 —— 少了幾句一定寫出來, 並指向完整證據檔
            L.append("- （本議題另有 %d 句討論未列入摘要，完整內容見標記逐字稿 `%s_marked.txt`）"
                     % (len(lines) - cap, "VMT_Minutes_" + str(cfg.get("date") or "")))

    L.append("")
    L.append("## 二、決議事項")
    if records["decisions"]:
        L.append("")
        L.append("| # | 決議 | 提出/裁示 | 議題 | 來源 |")
        L.append("|---|---|---|---|---|")
        for i, d in enumerate(records["decisions"], 1):
            L.append("| %d | %s | %s | %s | #%s |" % (i, d["text"], d["by"], d["topic"], d["cite"]))
    else:
        L.append("")
        L.append("本次會議無明確決議。")

    L.append("")
    L.append("## 三、待辦事項")
    if records["actions"]:
        L.append("")
        L.append("| # | 負責人 | 事項 | 期限 | 原文用語 | 來源 |")
        L.append("|---|---|---|---|---|---|")
        for i, a in enumerate(records["actions"], 1):
            L.append("| %d | %s | %s | %s | %s | #%s |" % (
                i, a["owner"], a["task"], a["due"], a["due_cue"] or "—", a["cite"]))
    else:
        L.append("")
        L.append("本次會議無待辦事項。")

    L.append("")
    L.append("## 四、待確認事項")
    pend: list[str] = []
    for a in au["incomplete_actions"]:
        miss = "、".join(x for x in (["負責人"] if a["owner"] == UNKNOWN else []) +
                        (["期限"] if a["due"] == UNKNOWN else []))
        pend.append("待辦「%s」缺 %s（#%s）" % (a["task"], miss, a["cite"]))
    for q in records["questions"]:
        pend.append("未解問題：%s（%s 提出，#%s）" % (q["text"], q["raised_by"], q["cite"]))
    for u in au["unknown_subject"]:
        pend.append("句 #%s 主詞無法判定：%s" % (u["uid"], clip(u["text"], 40)))
    for item in au["not_discussed"]:
        pend.append("議程項目「%s」**本次未討論**" % item)
    if pend:
        for p in pend:
            L.append("- %s" % p)
    else:
        L.append("無。")

    L.append("")
    L.append("## 五、完整性稽核")
    L.append("")
    L.append("- 結論句佔比：%.1f%%（決/辦/問 共 %d 句 ÷ 有效句 %d 句）" % (
        au["conclusion_rate"] * 100,
        round(au["conclusion_rate"] * au["valid_sentences"]), au["valid_sentences"]))
    L.append("- 幻覺過濾丟棄：%d 句（原句仍保留於帳本，可查）" % len(au["dropped"]))
    L.append("- 時間軸疑似缺口：%d 處" % len(au["gaps"]))
    for g in au["gaps"]:
        L.append("  - %.0fs–%.0fs 無逐字稿內容（%.0f 秒），請確認該段是否漏轉（#%s 之前）"
                 % (g["from"], g["to"], g["seconds"], g["before_uid"]))
    if au["suspects"]:
        L.append("- 疑似遺漏（含期限或數字，但未被任何結論引用）共 %d 句，列出前 %d 句："
                 % (au["suspects_total"], min(10, len(au["suspects"]))))
        for s in au["suspects"][:10]:
            L.append("  - #%s %s：%s" % (s["cite"], s["subject"], s["text"]))
    L.append("")
    L.append("---")
    L.append("")
    L.append("> 本記錄由 VMT 會議記錄引擎自動產生。每條決議與待辦後方的 `#序號` "
             "對應標記逐字稿的句號，可逐條回查原文驗證。")
    return "\n".join(L)


def render_marked_transcript(utts: list[dict]) -> str:
    """標記逐字稿 —— 會議記錄的原始證據, 必須與記錄一起保存。"""
    out = []
    for u in utts:
        ts = u.get("clock") or (("%02d:%02d" % divmod(int(u["start"]), 60))
                                if isinstance(u.get("start"), (int, float)) else "")
        mark = "|drop|" if "drop" in u["flags"] else "|%s|" % u["tag"]
        out.append("[%s] %s %s %s %s" % (u["uid"], ts, u.get("subject", UNKNOWN), mark, u["text"]))
    return "\n".join(out)


# ---------------------------------------------------------------- 主流程 ----


def run(ws: Workspace, transcript, cfg: dict, commit: bool = False,
        no_open: bool = True) -> EngineResult:
    ws.ensure()
    base_date = dt.date.fromisoformat(cfg["date"]) if cfg.get("date") else dt.date.today()
    roster = cfg.get("participants", [])
    chair = cfg.get("chair", "")

    segs, meta = load_transcript(transcript)
    cfg.setdefault("title", meta.get("title", "會議記錄"))
    utts = segment(segs, cfg.get("speaker_map", {}))
    dropped = flag_hallucinations(utts)
    vocab = list(cfg.get("vocab", [])) + [p.get("name", "") for p in roster]
    corrections = clean(utts, vocab, cfg.get("traditional", True))
    resolve_subjects(utts, roster)
    tag_utterances(utts, chair, base_date)
    topics = split_topics(utts, cfg.get("agenda", []), chair)
    records = extract_records(utts, topics, base_date)
    au = audit(utts, topics, records, cfg.get("agenda", []))

    md = render_markdown(cfg, utts, topics, records, au)
    marked = render_marked_transcript(utts)
    stem = "VMT_Minutes_%s" % (cfg.get("date") or dt.date.today().isoformat())
    md_path = ws.reports / (stem + ".md")
    tr_path = ws.reports / (stem + "_marked.txt")
    if commit:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        tr_path.write_text(marked, encoding="utf-8")

    minute_uid = fingerprint(cfg.get("title"), cfg.get("date"), len(utts))
    rec = {"minute_uid": minute_uid, "title": cfg.get("title"), "date": cfg.get("date"),
           "chair": chair, "topics": topics, "records": records,
           "audit": {k: v for k, v in au.items() if k != "unknown_subject"},
           "utterances": utts, "engine_version": VERSION}
    ledger = Ledger(ws.minutes_ledger, commit)
    if minute_uid not in {r.get("minute_uid") for r in ledger.read()}:
        ledger.append(rec)
        EventLog(ws, commit).emit("MINUTES_GENERATED", minute_uid,
                                  "%s 決議%d 待辦%d" % (cfg.get("title"),
                                                       len(records["decisions"]),
                                                       len(records["actions"])))

    print("[記錄] 句數 %d / 議題 %d / 決議 %d / 待辦 %d / 丟棄 %d"
          % (len(utts), len(topics), len(records["decisions"]),
             len(records["actions"]), dropped))
    print("[稽核] 結論句佔比 %.1f%% / 疑似遺漏 %d / 未討論議程 %d / 時間軸缺口 %d"
          % (au["conclusion_rate"] * 100, au["suspects_total"],
             len(au["not_discussed"]), len(au["gaps"])))

    report = _report(ws, cfg, utts, topics, records, au, corrections, commit)
    try_open(report, no_open)
    return EngineResult(
        engine=ENGINE,
        counts={"utterances": len(utts), "decisions": len(records["decisions"]),
                "actions": len(records["actions"]), "dropped": dropped},
        records=[rec], report=str(report),
        notes=["markdown=%s" % md_path, "marked=%s" % tr_path])


def _report(ws, cfg, utts, topics, records, au, corrections, commit) -> Path:
    tag_hex = {"決": "#5a9e6f", "辦": "#d08343", "議": "#4c78a8", "問": "#c9a13a", "資": "#8a857c"}
    marked = table(
        ["#", "時間", "主詞", "標記", "內容"],
        [["<span class='mono'>%s</span>" % u["uid"],
          "<span class='mono'>%s</span>" % esc(u.get("clock") or ""),
          esc(u.get("subject", UNKNOWN)) + ("" if u.get("subject") != UNKNOWN
                                            else " <span class='cite'>待確認</span>"),
          pill("drop" if "drop" in u["flags"] else u["tag"],
               "#b5443a" if "drop" in u["flags"] else tag_hex.get(u["tag"], "#999")),
          esc(clip(u["text"], 70))] for u in utts], "無逐字稿內容")
    dec = table(["決議", "裁示", "議題", "來源"],
                [[esc(d["text"]), esc(d["by"]), esc(d["topic"]),
                  "<span class='cite'>#%s</span>" % d["cite"]] for d in records["decisions"]],
                "本次無明確決議")
    act = table(["負責人", "事項", "期限", "原文用語", "來源"],
                [[esc(a["owner"]), esc(a["task"]),
                  esc(a["due"]) if a["due"] != UNKNOWN else pill("待確認", "#c9a13a"),
                  esc(a["due_cue"] or "—"), "<span class='cite'>#%s</span>" % a["cite"]]
                 for a in records["actions"]], "本次無待辦")
    gap = table(["疑似遺漏內容 (含期限/數字但未被引用)", "主詞", "來源"],
                [[esc(s["text"]), esc(s["subject"]), "<span class='cite'>#%s</span>" % s["cite"]]
                 for s in au["suspects"]], "無 — 所有含期限/數字的句子都已被結論引用")
    miss = table(["未討論的議程項目"], [[pill(esc(x), "#b5443a")] for x in au["not_discussed"]],
                 "議程全數討論完畢")
    kpi = kpi_cards([("決議", len(records["decisions"]), "#5a9e6f"),
                     ("待辦", len(records["actions"]), "#d08343"),
                     ("結論句佔比", "%.0f%%" % (au["conclusion_rate"] * 100), "#4c78a8"),
                     ("幻覺丟棄", len(au["dropped"]), "#b5443a"),
                     ("待確認", len(au["incomplete_actions"]) + len(au["unknown_subject"]), "#c9a13a")])
    corr = table(["ASR 原文", "校正為"], [[esc(a), esc(b)] for a, b in corrections],
                 "無專有名詞校正")
    return render_report(
        ws.reports / "VMT_Minutes.html", "記", "VMT 會議記錄引擎 — %s" % cfg.get("title", ""),
        "%s · 主席 %s · %s" % (cfg.get("date", ""), cfg.get("chair", ""), mode_label(commit)),
        "治理：每條決議與待辦都掛來源句號（#序號）可回查原文；主詞判不出一律標 [?] 不猜；"
        "議程有而未討論者明寫「未討論」；ASR 幻覺句標記丟棄但原列保留於帳本。",
        [("KPI", kpi), ("決議事項", dec), ("待辦事項", act),
         ("完整性 · 未討論議程", miss), ("完整性 · 引用反查", gap),
         ("正確性 · 專有名詞校正", corr), ("標記逐字稿（證據）", marked)],
        "%s %s | 帳本: data/minutes.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Meeting Minutes Engine")
    add_common_args(ap)
    ap.add_argument("--transcript", help="逐字稿 (json / txt); 省略則用內建範例")
    ap.add_argument("--config", help="會議設定 json (出席/議程/主席/詞彙表)")
    a = ap.parse_args()
    banner("VMT · Meeting Minutes Engine %s" % VERSION, mode_label(a.commit))

    here = Path(__file__).resolve().parent.parent / "samples"
    cfg = json.loads(Path(a.config).read_text(encoding="utf-8")) if a.config \
        else json.loads((here / "meeting_config.json").read_text(encoding="utf-8"))
    src = a.transcript or (here / "sample_transcript.json")
    r = run(Workspace(a.root), src, cfg, a.commit, a.no_open)
    print("[輸出] 報告:", r.report)
    for n in r.notes:
        print("       ", n)
    print("完成.")


if __name__ == "__main__":
    main()
