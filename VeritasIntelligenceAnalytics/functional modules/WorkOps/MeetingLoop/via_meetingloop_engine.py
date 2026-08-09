#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

from pathlib import Path

ENGINE_NAME = "VIA MeetingLoop Intelligence Engine"
ENGINE_VERSION = "v005"
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "engine_config.json"
PROFILE_PATH = BASE_DIR / "interaction_profile.json"
FAILURE_PATH = BASE_DIR / "failure_policy.json"
LEXICON_PATH = BASE_DIR / "lexicon.json"
CONTRACT_PATH = BASE_DIR / "data_contract.json"

RUNS_DIR = BASE_DIR / "runs"
SSOT_DIR = BASE_DIR / "ssot"
DATA_DIR = BASE_DIR / "data"
QUARANTINE_DIR = DATA_DIR / "quarantine"
DB_PATH = SSOT_DIR / "via_meetingloop_v005.sqlite3"
DUCKDB_PATH = SSOT_DIR / "via_meetingloop_v005.duckdb"

ACTION_STATUS = {
    "NOT_STARTED", "IN_PROGRESS", "WAITING_RESPONSE", "BLOCKED",
    "OVERDUE", "NEED_DECISION", "COMPLETED_PENDING_EVIDENCE",
    "COMPLETED", "CANCELLED"
}

ACTION_CUES = (
    "請", "需要", "必須", "負責", "提供", "確認", "完成", "回覆", "追蹤",
    "準備", "更新", "交付", "安排", "修正", "提交", "please", "need to",
    "must", "responsible", "provide", "confirm", "complete", "reply",
    "follow up", "prepare", "update", "deliver", "arrange", "submit", "fix"
)
DECISION_CUES = (
    "決定", "決議", "確認採用", "同意", "核准", "定案",
    "decided", "agreed", "approved", "final decision"
)
RISK_CUES = (
    "風險", "延誤", "逾期", "阻塞", "卡住", "缺少", "無法", "失敗",
    "risk", "delay", "overdue", "blocked", "missing", "unable", "failed"
)
NEGATION_TERMS = ("不", "未", "沒有", "尚未", "不能", "無法", "not", "no", "never", "cannot")

# =============================================================================
# def 01_IMPORTS
# =============================================================================

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
import uuid
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Optional

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None

try:
    import dateparser
except Exception:
    dateparser = None

try:
    from opencc import OpenCC
except Exception:
    OpenCC = None

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except Exception:
    pa = None
    pq = None

try:
    import duckdb
except Exception:
    duckdb = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
except Exception:
    TfidfVectorizer = None
    LogisticRegression = None

# =============================================================================
# def 02_MODELS
# =============================================================================

@dataclass
class Segment:
    meeting_id: str
    segment_id: str
    sequence_no: int
    start_time: str
    end_time: str
    raw_speaker: str
    raw_text: str
    normalized_text: str
    corrected_text: str
    approved_text: str
    language: str
    speaker_name: str
    speaker_confirmed: bool
    review_status: str
    source_hash: str
    confidence: float

@dataclass
class Action:
    action_id: str
    meeting_id: str
    project_code: str
    source_segment_ids: list[str]
    action_item: str
    classification: str
    deliverable: str
    acceptance_criteria: str
    primary_owner: str
    backup_owner_1: str
    backup_owner_2: str
    escalation_manager: str
    original_due_date: str
    current_due_date: str
    status: str
    progress_percent: Optional[int]
    blocker: str
    evidence_required: str
    confidence: float
    confirmation_required: bool

# =============================================================================
# def 03_FOUNDATION
# =============================================================================

def def_now() -> dt.datetime:
    return dt.datetime.now().astimezone()

def def_now_iso() -> str:
    return def_now().isoformat(timespec="seconds")

def def_load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))

def def_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8-sig")

def def_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")

def def_read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp950", "big5", "cp932", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    raise RuntimeError(f"Unable to decode: {path}")

def def_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def def_sha256_text(text: str) -> str:
    return def_sha256_bytes(text.encode("utf-8", errors="replace"))

def def_ensure_dirs() -> None:
    for p in (RUNS_DIR, SSOT_DIR, QUARANTINE_DIR):
        p.mkdir(parents=True, exist_ok=True)

def def_make_run_dir(meeting_id: str) -> Path:
    path = RUNS_DIR / f"RUN_{def_now().strftime('%Y%m%d_%H%M%S')}_{meeting_id}"
    path.mkdir(parents=True, exist_ok=False)
    return path

def def_safe_copy(source: Path, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / source.name
    if target.exists():
        target = folder / f"{source.stem}_{def_sha256_bytes(source.read_bytes())[:10]}{source.suffix}"
    shutil.copy2(source, target)
    return target

def def_contains(text: str, cues: Iterable[str]) -> bool:
    lowered = text.casefold()
    return any(c.casefold() in lowered for c in cues)

# =============================================================================
# def 04_DOCTOR
# =============================================================================

def def_doctor() -> dict[str, Any]:
    dependencies = {
        "rapidfuzz": fuzz is not None,
        "dateparser": dateparser is not None,
        "opencc": OpenCC is not None,
        "pyarrow": pa is not None and pq is not None,
        "duckdb": duckdb is not None,
        "sklearn": TfidfVectorizer is not None
    }
    capabilities = {
        "core_processing": True,
        "sqlite_ssot": True,
        "parquet": dependencies["pyarrow"],
        "duckdb_views": dependencies["duckdb"] and dependencies["pyarrow"],
        "natural_date": dependencies["dateparser"],
        "traditional_chinese": dependencies["opencc"],
        "fuzzy_lexicon": dependencies["rapidfuzz"],
        "ml_classifier": dependencies["sklearn"]
    }
    gate = "GREEN" if all((capabilities["parquet"], capabilities["duckdb_views"])) else "DEGRADED"
    return {
        "engine": f"{ENGINE_NAME} {ENGINE_VERSION}",
        "python": sys.version,
        "dependencies": dependencies,
        "capabilities": capabilities,
        "gate": gate,
        "fallback": "SQLite + JSONL" if gate == "DEGRADED" else "Parquet + DuckDB + SQLite"
    }

# =============================================================================
# def 05_DATABASE
# =============================================================================

def def_db_connect() -> sqlite3.Connection:
    def_ensure_dirs()
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con

def def_db_init() -> None:
    with def_db_connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            meeting_id TEXT PRIMARY KEY,
            project_code TEXT NOT NULL,
            meeting_title TEXT,
            meeting_date TEXT,
            next_meeting_date TEXT,
            source_file TEXT,
            source_sha256 TEXT NOT NULL,
            run_dir TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS transcript_events (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            meeting_id TEXT NOT NULL,
            segment_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS action_events (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            meeting_id TEXT NOT NULL,
            action_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reminder_events (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            meeting_id TEXT NOT NULL,
            action_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL,
            scheduled_for TEXT NOT NULL,
            draft_path TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS failure_events (
            row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            meeting_id TEXT,
            failure_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            gate_name TEXT NOT NULL,
            observed_value TEXT,
            expected_value TEXT,
            fallback_used TEXT,
            human_review_required INTEGER NOT NULL,
            resolution_status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)

def def_append_event(table: str, meeting_id: str, object_field: str, object_id: str,
                     event_type: str, payload: dict[str, Any]) -> None:
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if table not in {"transcript_events", "action_events"}:
        raise ValueError("Unsupported event table")
    with def_db_connect() as con:
        con.execute(
            f"""INSERT INTO {table}
            (event_id, meeting_id, {object_field}, event_type, payload_json, payload_sha256, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), meeting_id, object_id, event_type,
                payload_json, def_sha256_text(payload_json), def_now_iso()
            )
        )

def def_log_failure(meeting_id: str, failure_id: str, severity: str, gate_name: str,
                    observed: Any, expected: Any, fallback: str,
                    human_review: bool, status: str) -> None:
    with def_db_connect() as con:
        con.execute(
            """INSERT INTO failure_events
            (event_id, meeting_id, failure_id, severity, gate_name, observed_value,
             expected_value, fallback_used, human_review_required,
             resolution_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()), meeting_id, failure_id, severity, gate_name,
                json.dumps(observed, ensure_ascii=False),
                json.dumps(expected, ensure_ascii=False),
                fallback, int(human_review), status, def_now_iso()
            )
        )

# =============================================================================
# def 06_PARSE_AND_RESTORE
# =============================================================================

def def_parse_timestamp(line: str) -> tuple[str, str] | None:
    match = re.match(
        r"\s*((?:\d{2}:)?\d{2}:\d{2}[.,]\d{3})\s*-->\s*((?:\d{2}:)?\d{2}:\d{2}[.,]\d{3})",
        line
    )
    return (match.group(1).replace(",", "."), match.group(2).replace(",", ".")) if match else None

def def_sentence_split(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return [x.strip() for x in re.split(r"(?<=[。！？!?；;])\s*|(?<=[。！？!?；;])", clean) if x.strip()]

def def_parse_source(path: Path, meeting_id: str) -> list[Segment]:
    text = def_read_text(path)
    suffix = path.suffix.lower()
    rows: list[tuple[str, str, str, str]] = []

    if suffix == ".vtt":
        lines = text.replace("\r\n", "\n").split("\n")
        i = 0
        while i < len(lines):
            stamp = def_parse_timestamp(lines[i])
            if not stamp:
                i += 1
                continue
            start, end = stamp
            i += 1
            buffer = []
            while i < len(lines) and lines[i].strip():
                if not lines[i].strip().isdigit():
                    buffer.append(lines[i].strip())
                i += 1
            raw = " ".join(buffer).strip()
            speaker = ""
            m = re.match(r"<v\s+([^>]+)>(.*)</v>", raw)
            if m:
                speaker, raw = m.group(1).strip(), m.group(2).strip()
            if raw:
                rows.append((start, end, speaker, raw))
            i += 1
    elif suffix in {".txt", ".md"}:
        for line in [x.strip() for x in text.replace("\r\n", "\n").split("\n") if x.strip()]:
            start = ""
            speaker = ""
            body = line
            m = re.match(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*([^:：]{0,50})[:：]\s*(.+)$", line)
            if m:
                start, speaker, body = m.group(1), m.group(2).strip(), m.group(3).strip()
            else:
                m = re.match(r"^([^:：]{1,50})[:：]\s*(.+)$", line)
                if m:
                    speaker, body = m.group(1).strip(), m.group(2).strip()
            for sentence in def_sentence_split(body):
                rows.append((start, "", speaker, sentence))
    elif suffix == ".json":
        data = json.loads(text)
        for item in data.get("segments", data if isinstance(data, list) else []):
            rows.append((
                str(item.get("start_time", "")), str(item.get("end_time", "")),
                str(item.get("speaker", "")), str(item.get("text", "")).strip()
            ))
    else:
        raise ValueError(f"Unsupported source format: {suffix}")

    result = []
    for idx, (start, end, speaker, raw) in enumerate(rows, start=1):
        if not raw:
            continue
        result.append(Segment(
            meeting_id=meeting_id,
            segment_id=f"{meeting_id}-SEG-{idx:05d}",
            sequence_no=idx,
            start_time=start,
            end_time=end,
            raw_speaker=speaker,
            raw_text=raw,
            normalized_text="",
            corrected_text="",
            approved_text="",
            language="",
            speaker_name=speaker,
            speaker_confirmed=False,
            review_status="PENDING",
            source_hash=def_sha256_text(raw),
            confidence=0.70
        ))
    return result

def def_detect_language(text: str) -> str:
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh-en" if re.search(r"[A-Za-z]", text) else "zh"
    return "en" if re.search(r"[A-Za-z]", text) else "unknown"

def def_normalize(text: str, config: dict[str, Any]) -> str:
    value = unicodedata.normalize("NFKC", text).replace("\u200b", "").replace("\ufeff", "")
    value = re.sub(r"[ \t]+", " ", value).strip()
    if OpenCC is not None:
        try:
            value = OpenCC("s2twp").convert(value)
        except Exception:
            pass
    return value

def def_apply_lexicon(text: str, lexicon: dict[str, Any], threshold: int) -> tuple[str, list[dict[str, Any]]]:
    corrected = text
    changes = []
    for entity_type, entries in lexicon.items():
        for entry in entries:
            canonical = str(entry.get("canonical_term", "")).strip()
            aliases = [str(x).strip() for x in entry.get("aliases", []) if str(x).strip()]
            for alias in sorted(set(aliases), key=len, reverse=True):
                pattern = re.compile(re.escape(alias), re.IGNORECASE)
                if pattern.search(corrected):
                    before = corrected
                    corrected = pattern.sub(canonical, corrected)
                    if before != corrected:
                        changes.append({"type": entity_type, "from": alias, "to": canonical, "method": "EXACT"})
            if fuzz is not None and len(canonical) >= 5:
                for token in re.findall(r"[\w.-]+", corrected):
                    score = fuzz.ratio(token.casefold(), canonical.casefold())
                    if score >= threshold and token.casefold() != canonical.casefold():
                        before = corrected
                        corrected = re.sub(rf"\b{re.escape(token)}\b", canonical, corrected)
                        if before != corrected:
                            changes.append({"type": entity_type, "from": token, "to": canonical, "method": f"FUZZY_{score}"})
    return corrected, changes

def def_high_risk_diff(raw: str, corrected: str) -> list[str]:
    risks = []
    raw_numbers = re.findall(r"\d+(?:[./:-]\d+)*", raw)
    corrected_numbers = re.findall(r"\d+(?:[./:-]\d+)*", corrected)
    if raw_numbers != corrected_numbers:
        risks.append("NUMBER_CHANGE")
    for term in NEGATION_TERMS:
        if (term.casefold() in raw.casefold()) != (term.casefold() in corrected.casefold()):
            risks.append("NEGATION_CHANGE")
            break
    return sorted(set(risks))

def def_restore_segments(segments: list[Segment], config: dict[str, Any],
                         lexicon: dict[str, Any]) -> tuple[list[Segment], list[dict[str, Any]]]:
    ledger = []
    threshold = int(config.get("fuzzy_lexicon_threshold", 94))
    for segment in segments:
        segment.normalized_text = def_normalize(segment.raw_text, config)
        segment.corrected_text, changes = def_apply_lexicon(segment.normalized_text, lexicon, threshold)
        if not re.search(r"[。！？.!?]$", segment.corrected_text):
            segment.corrected_text += "。" if def_detect_language(segment.corrected_text) in {"zh", "zh-en", "ja"} else "."
        segment.approved_text = segment.corrected_text
        segment.language = def_detect_language(segment.corrected_text)
        risks = def_high_risk_diff(segment.raw_text, segment.corrected_text)
        segment.confidence = 0.98 if not risks and not changes else (0.88 if not risks else 0.55)
        if risks:
            segment.review_status = "NEEDS_REVIEW"
        ledger.append({
            "segment_id": segment.segment_id,
            "changes": changes,
            "high_risk_diff": risks,
            "confidence": segment.confidence
        })
    return segments, ledger

# =============================================================================
# def 07_SUMMARY_AND_CLASSIFICATION
# =============================================================================

def def_tokenize(text: str) -> list[str]:
    stop = {"的","了","是","在","和","與","及","也","要","請","我們","the","a","an","to","of","and","or","is","are","we","you","it"}
    tokens = re.findall(r"[\u4e00-\u9fff]|[A-Za-z][A-Za-z0-9_.-]*", text.casefold())
    return [t for t in tokens if t not in stop]

def def_summary(segments: list[Segment], config: dict[str, Any]) -> list[dict[str, Any]]:
    token_lists = [def_tokenize(s.approved_text) for s in segments]
    df = Counter()
    for tokens in token_lists:
        df.update(set(tokens))
    scored = []
    n = max(1, len(segments))
    for index, (segment, tokens) in enumerate(zip(segments, token_lists)):
        if not tokens:
            continue
        tf = Counter(tokens)
        score = sum(count * (math.log((1+n)/(1+df[token])) + 1) for token, count in tf.items()) / len(tokens)
        if def_contains(segment.approved_text, DECISION_CUES):
            score *= 1.50
        if def_contains(segment.approved_text, RISK_CUES):
            score *= 1.45
        if def_contains(segment.approved_text, ACTION_CUES):
            score *= 1.35
        if re.search(r"\d", segment.approved_text):
            score *= 1.15
        scored.append((score, index, segment))
    count = min(
        int(config.get("summary_max_sentences", 12)),
        max(int(config.get("summary_min_sentences", 3)),
            math.ceil(len(segments) * float(config.get("summary_ratio", 0.25))))
    )
    selected = sorted(sorted(scored, reverse=True)[:count], key=lambda x: x[1])
    return [{
        "text": s.approved_text,
        "source_segment_id": s.segment_id,
        "speaker": s.speaker_name,
        "start_time": s.start_time,
        "score": round(score, 4)
    } for score, _, s in selected]

def def_classify_sentence(text: str) -> tuple[str, float]:
    scores = {
        "DECISION": 0.95 if def_contains(text, DECISION_CUES) else 0.0,
        "RISK": 0.88 if def_contains(text, RISK_CUES) else 0.0,
        "ACTION": 0.82 if def_contains(text, ACTION_CUES) else 0.0
    }
    label = max(scores, key=scores.get)
    if scores[label] == 0:
        return "DISCUSSION", 0.65
    return label, scores[label]

def def_extract_owner(text: str, attendees: list[dict[str, Any]]) -> str:
    for attendee in attendees:
        name = str(attendee.get("name", "")).strip()
        aliases = [name] + [str(x) for x in attendee.get("aliases", [])]
        if any(a and a.casefold() in text.casefold() for a in aliases):
            if re.search(rf"(請|ask(?:ed)?|request(?:ed)?)\s*{re.escape(name)}", text, re.IGNORECASE):
                return name
    for attendee in attendees:
        name = str(attendee.get("name", "")).strip()
        if name and name.casefold() in text.casefold():
            return name
    return "OWNER_PENDING"

def def_extract_due(text: str, meeting_date: str) -> str:
    matches = re.findall(r"(20\d{2}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2})?)", text)
    if matches:
        return matches[0].replace("-", "/")
    if dateparser is not None:
        settings: dict[str, Any] = {"PREFER_DATES_FROM": "future"}
        try:
            settings["RELATIVE_BASE"] = dt.datetime.fromisoformat(meeting_date.replace("/", "-"))
        except Exception:
            pass
        parsed = dateparser.parse(text, languages=["zh", "en", "ja"], settings=settings)
        if parsed:
            return parsed.strftime("%Y/%m/%d %H:%M:%S")
    return "DUE_DATE_PENDING"

def def_actions(segments: list[Segment], config: dict[str, Any], meeting_id: str) -> list[Action]:
    project = str(config.get("project_code", "BUX")).upper()[:3]
    date_token = re.sub(r"\D", "", str(config.get("meeting_date", "")))[:8] or def_now().strftime("%Y%m%d")
    result = []
    for segment in segments:
        label, confidence = def_classify_sentence(segment.approved_text)
        if label != "ACTION":
            continue
        owner = def_extract_owner(segment.approved_text, config.get("attendees", []))
        due = def_extract_due(segment.approved_text, str(config.get("meeting_date", "")))
        qualified = owner != "OWNER_PENDING" and due != "DUE_DATE_PENDING"
        result.append(Action(
            action_id=f"{project}-ACT-{date_token}-{len(result)+1:03d}",
            meeting_id=meeting_id,
            project_code=project,
            source_segment_ids=[segment.segment_id],
            action_item=segment.approved_text,
            classification="ACTION" if qualified else "ACTION_CANDIDATE",
            deliverable="DELIVERABLE_PENDING",
            acceptance_criteria="ACCEPTANCE_CRITERIA_PENDING",
            primary_owner=owner,
            backup_owner_1="BACKUP_OWNER_1_PENDING",
            backup_owner_2="BACKUP_OWNER_2_PENDING",
            escalation_manager="ESCALATION_MANAGER_PENDING",
            original_due_date=due,
            current_due_date=due,
            status="NOT_STARTED",
            progress_percent=None,
            blocker="",
            evidence_required="EVIDENCE_REQUIRED_PENDING",
            confidence=confidence,
            confirmation_required=True
        ))
    return result

def def_decisions(segments: list[Segment]) -> list[dict[str, Any]]:
    return [{
        "decision_id": f"{s.meeting_id}-DEC-{i+1:03d}",
        "decision": s.approved_text,
        "decision_maker": s.speaker_name or "DECISION_MAKER_PENDING",
        "source_segment_ids": [s.segment_id],
        "confirmation_required": True
    } for i, s in enumerate([x for x in segments if def_classify_sentence(x.approved_text)[0] == "DECISION"])]

def def_risks(segments: list[Segment]) -> list[dict[str, Any]]:
    return [{
        "risk_id": f"{s.meeting_id}-RSK-{i+1:03d}",
        "risk": s.approved_text,
        "source_segment_ids": [s.segment_id],
        "confirmation_required": True
    } for i, s in enumerate([x for x in segments if def_classify_sentence(x.approved_text)[0] == "RISK"])]

# =============================================================================
# def 08_DATA_LAYER
# =============================================================================

def def_validate_rows(table: str, rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    contract = def_load_json(CONTRACT_PATH, {})
    required = contract.get("tables", {}).get(table, {}).get("required", [])
    errors = []
    for idx, row in enumerate(rows):
        missing = [col for col in required if col not in row]
        if missing:
            errors.append(f"row {idx}: missing {missing}")
    return not errors, errors

def def_write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

def def_write_dataset(layer: str, table: str, meeting_id: str,
                      rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid, errors = def_validate_rows(table, rows)
    if not valid:
        target = QUARANTINE_DIR / f"{meeting_id}_{table}_{def_now().strftime('%Y%m%d_%H%M%S')}.json"
        def_write_json(target, {"table": table, "errors": errors, "rows": rows})
        return {"status": "QUARANTINED", "path": str(target), "errors": errors}

    folder = DATA_DIR / layer / table / f"meeting_id={meeting_id}"
    folder.mkdir(parents=True, exist_ok=True)
    jsonl_path = folder / "part-00000.jsonl"
    def_write_jsonl(jsonl_path, rows)

    if pa is not None and pq is not None:
        parquet_path = folder / "part-00000.parquet"
        try:
            table_obj = pa.Table.from_pylist(rows)
            pq.write_table(table_obj, parquet_path, compression="zstd")
            return {"status": "PARQUET", "path": str(parquet_path), "fallback": str(jsonl_path)}
        except Exception as exc:
            return {"status": "JSONL_FALLBACK", "path": str(jsonl_path), "error": str(exc)}
    return {"status": "JSONL_FALLBACK", "path": str(jsonl_path), "reason": "pyarrow unavailable"}

def def_build_duckdb_views() -> dict[str, Any]:
    if duckdb is None or pa is None or pq is None:
        return {"status": "SKIPPED", "reason": "duckdb or pyarrow unavailable"}
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        patterns = {
            "vw_transcript_segments": str(DATA_DIR / "silver" / "transcript_segments" / "**" / "*.parquet"),
            "vw_actions": str(DATA_DIR / "gold" / "actions" / "**" / "*.parquet")
        }
        for view, pattern in patterns.items():
            con.execute(f"CREATE OR REPLACE VIEW {view} AS SELECT * FROM read_parquet('{pattern}', hive_partitioning=true, union_by_name=true)")
        return {"status": "READY", "path": str(DUCKDB_PATH), "views": list(patterns)}
    finally:
        con.close()

# =============================================================================
# def 09_WORKBENCH
# =============================================================================

def def_build_workbench(run_dir: Path, config: dict[str, Any],
                        segments: list[Segment], actions: list[Action],
                        summary: list[dict[str, Any]]) -> Path:
    data = {
        "meeting": {
            "meeting_id": segments[0].meeting_id if segments else "",
            "meeting_title": config.get("meeting_title", ""),
            "next_meeting_date": config.get("next_meeting_date", "")
        },
        "attendees": config.get("attendees", []),
        "segments": [{
            "segment_id": s.segment_id,
            "start_time": s.start_time,
            "raw_text": s.raw_text,
            "suggested_text": s.corrected_text,
            "speaker_candidates": [{"name": s.raw_speaker or "無法確認", "confidence": s.confidence}],
            "risk_level": "HIGH" if s.review_status == "NEEDS_REVIEW" else "LOW",
            "review_status": s.review_status,
            "confidence": s.confidence
        } for s in segments],
        "actions": [asdict(a) for a in actions],
        "summary": summary,
        "kpi": {
            "need_verification": sum(1 for s in segments if s.review_status != "CONFIRMED") + len(actions),
            "unanswered": sum(1 for a in actions if a.status == "WAITING_RESPONSE"),
            "overdue": sum(1 for a in actions if a.status == "OVERDUE"),
            "days_to_next_meeting": 0
        }
    }
    template = (BASE_DIR / "templates" / "mouse_first_workbench.html").read_text(encoding="utf-8")
    output = template.replace("__EMBEDDED_DATA__", json.dumps(data, ensure_ascii=False))
    path = run_dir / "12_mouse_first_workbench.html"
    def_write_text(path, output)
    return path

# =============================================================================
# def 10_REMINDERS_AND_OUTPUTS
# =============================================================================

def def_reminder_drafts(run_dir: Path, config: dict[str, Any], actions: list[Action],
                        meeting_id: str) -> list[dict[str, Any]]:
    value = str(config.get("next_meeting_date", ""))
    next_meeting = None
    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            next_meeting = dt.datetime.strptime(value, fmt).astimezone()
            break
        except Exception:
            pass
    if next_meeting is None:
        return []
    manifest = []
    with def_db_connect() as con:
        for reminder_type, days in (("N-3", int(config.get("n3_days_before", 3))),
                                    ("N-1", int(config.get("n1_days_before", 1)))):
            scheduled = next_meeting - dt.timedelta(days=days)
            for action in actions:
                subject = f"[{reminder_type}] {action.action_id} 進度更新與權責確認"
                body = f"""Subject: {subject}

您好，

請以滑鼠回填以下追蹤事項：

Action ID：{action.action_id}
事項：{action.action_item}
責任人：{action.primary_owner}
原期限：{action.original_due_date}
狀態：{action.status}

需確認：責任、狀態、進度、期限、阻塞、協助與證據。
此版本僅建立草稿，不會寄出。
"""
                path = run_dir / "reminder_drafts" / f"{reminder_type}_{action.action_id}.txt"
                def_write_text(path, body)
                item = {
                    "event_id": str(uuid.uuid4()), "meeting_id": meeting_id,
                    "action_id": action.action_id, "reminder_type": reminder_type,
                    "scheduled_for": scheduled.isoformat(timespec="seconds"),
                    "draft_path": str(path), "created_at": def_now_iso()
                }
                manifest.append(item)
                con.execute(
                    """INSERT INTO reminder_events
                    (event_id, meeting_id, action_id, reminder_type, scheduled_for, draft_path, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    tuple(item.values())
                )
    return manifest

def def_write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)

# =============================================================================
# def 11_PROCESS
# =============================================================================

def def_meeting_id(config: dict[str, Any]) -> str:
    project = str(config.get("project_code", "BUX")).upper()[:3]
    date_token = re.sub(r"\D", "", str(config.get("meeting_date", "")))[:8] or def_now().strftime("%Y%m%d")
    return f"MTG-{project}-{date_token}-001"

def def_process(source: Path) -> Path:
    def_ensure_dirs()
    def_db_init()
    config = def_load_json(CONFIG_PATH, {})
    lexicon = def_load_json(LEXICON_PATH, {})
    meeting_id = def_meeting_id(config)
    run_dir = def_make_run_dir(meeting_id)

    copied = def_safe_copy(source, run_dir / "00_raw_evidence")
    source_hash = def_sha256_bytes(copied.read_bytes())
    if not copied.exists() or not source_hash:
        raise RuntimeError("Evidence Gate failed")

    segments = def_parse_source(copied, meeting_id)
    if not segments:
        def_log_failure(meeting_id, "F03", "CRITICAL", "TRANSCRIPT", 0, ">0", "STOP", True, "OPEN")
        raise RuntimeError("No transcript segments parsed")

    segments, correction_ledger = def_restore_segments(segments, config, lexicon)
    summary = def_summary(segments, config)
    actions = def_actions(segments, config, meeting_id)
    decisions = def_decisions(segments)
    risks = def_risks(segments)

    with def_db_connect() as con:
        con.execute(
            """INSERT OR IGNORE INTO meetings
            (meeting_id, project_code, meeting_title, meeting_date, next_meeting_date,
             source_file, source_sha256, run_dir, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                meeting_id, config.get("project_code", "BUX"),
                config.get("meeting_title", ""), config.get("meeting_date", ""),
                config.get("next_meeting_date", ""), str(copied), source_hash,
                str(run_dir), def_now_iso()
            )
        )

    for segment in segments:
        def_append_event("transcript_events", meeting_id, "segment_id",
                         segment.segment_id, "SEGMENT_CREATED", asdict(segment))
    for action in actions:
        def_append_event("action_events", meeting_id, "action_id",
                         action.action_id, "ACTION_CANDIDATE_CREATED", asdict(action))

    segment_rows = [asdict(s) for s in segments]
    action_rows = [asdict(a) for a in actions]
    data_results = {
        "silver_transcript": def_write_dataset("silver", "transcript_segments", meeting_id, segment_rows),
        "gold_actions": def_write_dataset("gold", "actions", meeting_id, action_rows)
    }
    duck_result = def_build_duckdb_views()

    def_write_csv(run_dir / "01_transcript_segments.csv", segment_rows)
    def_write_json(run_dir / "02_correction_ledger.json", correction_ledger)
    def_write_json(run_dir / "03_extractive_summary.json", summary)
    def_write_json(run_dir / "04_decisions.json", decisions)
    def_write_json(run_dir / "05_risks.json", risks)
    def_write_csv(run_dir / "06_actions.csv", action_rows)
    def_write_json(run_dir / "07_data_layer.json", data_results)
    def_write_json(run_dir / "08_duckdb_status.json", duck_result)
    reminder_manifest = def_reminder_drafts(run_dir, config, actions, meeting_id)
    def_write_json(run_dir / "09_reminder_manifest.json", reminder_manifest)

    ai_payload = {
        "policy": {"suggestion_only": True, "do_not_invent": True, "evidence_required": True},
        "meeting": config, "segments": segment_rows, "summary": summary,
        "actions": action_rows, "decisions": decisions, "risks": risks
    }
    def_write_json(run_dir / "10_ai_payload.json", ai_payload)
    workbench = def_build_workbench(run_dir, config, segments, actions, summary)

    manifest = {
        "engine": ENGINE_NAME, "version": ENGINE_VERSION, "meeting_id": meeting_id,
        "source_sha256": source_hash, "segment_count": len(segments),
        "action_count": len(actions), "decision_count": len(decisions),
        "risk_count": len(risks), "summary_count": len(summary),
        "doctor": def_doctor(), "data_layer": data_results,
        "duckdb": duck_result, "workbench": str(workbench),
        "run_dir": str(run_dir), "generated_at": def_now_iso(),
        "gate": "REVIEW_REQUIRED"
    }
    def_write_json(run_dir / "11_run_manifest.json", manifest)

    print("=" * 96)
    print(f"def Engine      : {ENGINE_NAME} {ENGINE_VERSION}")
    print(f"def Gate        : {manifest['gate']}")
    print(f"def Meeting ID  : {meeting_id}")
    print(f"def Segments    : {len(segments)}")
    print(f"def Actions     : {len(actions)}")
    print(f"def Decisions   : {len(decisions)}")
    print(f"def Risks       : {len(risks)}")
    print(f"def Data Mode   : {def_doctor()['fallback']}")
    print(f"def RunDir      : {run_dir}")
    print(f"def Workbench   : {workbench}")
    print("=" * 96)
    return run_dir

# =============================================================================
# def 12_IMPORT_REVIEW_AND_CONSOLIDATE
# =============================================================================

def def_import_review(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    meeting_id = str(payload.get("meeting", {}).get("meeting_id", "UNKNOWN"))
    state = payload.get("review_state", {})
    counts = {"segments": 0, "actions": 0}
    for object_id, item in state.get("segments", {}).items():
        def_append_event("transcript_events", meeting_id, "segment_id",
                         object_id, "SEGMENT_REVIEWED", item)
        counts["segments"] += 1
    for object_id, item in state.get("actions", {}).items():
        def_append_event("action_events", meeting_id, "action_id",
                         object_id, "ACTION_REVIEWED", item)
        counts["actions"] += 1
    return {"meeting_id": meeting_id, "imported": counts, "db": str(DB_PATH)}

def def_latest_events(table: str, object_col: str, meeting_id: str) -> list[dict[str, Any]]:
    with def_db_connect() as con:
        rows = con.execute(
            f"""SELECT {object_col}, payload_json, event_type, created_at
            FROM {table}
            WHERE meeting_id=?
            ORDER BY row_id""", (meeting_id,)
        ).fetchall()
    latest = {}
    for row in rows:
        latest[row[object_col]] = {
            "object_id": row[object_col],
            "payload": json.loads(row["payload_json"]),
            "event_type": row["event_type"],
            "created_at": row["created_at"]
        }
    return list(latest.values())

def def_consolidate(meeting_id: str) -> Path:
    run_dir = RUNS_DIR / f"CONSOLIDATED_{def_now().strftime('%Y%m%d_%H%M%S')}_{meeting_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    segments = def_latest_events("transcript_events", "segment_id", meeting_id)
    actions = def_latest_events("action_events", "action_id", meeting_id)
    def_write_json(run_dir / "segments_current.json", segments)
    def_write_json(run_dir / "actions_current.json", actions)
    def_write_json(run_dir / "consolidation_manifest.json", {
        "meeting_id": meeting_id, "segment_count": len(segments),
        "action_count": len(actions), "generated_at": def_now_iso(),
        "source": str(DB_PATH)
    })
    return run_dir

# =============================================================================
# def 13_SELF_TEST
# =============================================================================

def def_self_test() -> dict[str, Any]:
    sample = BASE_DIR / "sample_meeting.txt"
    assertions = []
    run_dir = def_process(sample)
    manifest = def_load_json(run_dir / "11_run_manifest.json", {})
    tests = {
        "run_created": run_dir.exists(),
        "source_hash": bool(manifest.get("source_sha256")),
        "segments_positive": manifest.get("segment_count", 0) > 0,
        "summary_positive": manifest.get("summary_count", 0) > 0,
        "decision_detected": manifest.get("decision_count", 0) >= 1,
        "workbench_exists": Path(manifest.get("workbench", "")).exists(),
        "sqlite_exists": DB_PATH.exists(),
        "data_layer_manifest": (run_dir / "07_data_layer.json").exists(),
        "reminder_manifest": (run_dir / "09_reminder_manifest.json").exists()
    }
    passed = all(tests.values())
    report = {
        "gate": "PASS" if passed else "FAIL",
        "tests": tests,
        "run_dir": str(run_dir),
        "doctor": def_doctor()
    }
    def_write_json(BASE_DIR / "SELF_TEST_REPORT.json", report)
    return report

# =============================================================================
# def 14_CLI
# =============================================================================

def def_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"{ENGINE_NAME} {ENGINE_VERSION}")
    sub = p.add_subparsers(dest="command", required=True)
    process = sub.add_parser("process")
    process.add_argument("--source", required=True, type=Path)
    sub.add_parser("doctor")
    sub.add_parser("self-test")
    review = sub.add_parser("import-review")
    review.add_argument("--review", required=True, type=Path)
    consolidate = sub.add_parser("consolidate")
    consolidate.add_argument("--meeting-id", required=True)
    return p

def def_main() -> int:
    try:
        args = def_parser().parse_args()
        if args.command == "doctor":
            print(json.dumps(def_doctor(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "self-test":
            report = def_self_test()
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["gate"] == "PASS" else 2
        if args.command == "process":
            source = args.source.expanduser().resolve()
            if not source.exists():
                raise FileNotFoundError(source)
            def_process(source)
            return 0
        if args.command == "import-review":
            result = def_import_review(args.review.expanduser().resolve())
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if args.command == "consolidate":
            path = def_consolidate(args.meeting_id)
            print(f"def Consolidated: {path}")
            return 0
        return 1
    except KeyboardInterrupt:
        print("def Cancelled. No source was modified.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"def FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(def_main())
