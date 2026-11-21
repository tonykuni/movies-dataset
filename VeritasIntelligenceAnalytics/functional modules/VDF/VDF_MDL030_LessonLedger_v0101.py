#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local lesson ledger for every VDF caller.

Markdown in kb/lessons is the source. Parquet shards are add-only.
Graphify, OmniRoute and agent-mem are optional peers: this file writes
the files they already know how to read. It does not import them, does
not call their network endpoints, and does not set a consent flag.

  py -3 VDF_MDL030_LessonLedger_v0101.py selftest
  py -3 VDF_MDL030_LessonLedger_v0101.py compile
  py -3 VDF_MDL030_LessonLedger_v0101.py query "WinError 32"
  py -3 VDF_MDL030_LessonLedger_v0101.py export
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LESSONS = HERE / "kb" / "lessons"
LEDGER = HERE / "output_hub" / "mega" / "lesson_ledger"
STAGING = HERE / "output_hub" / "mega" / "lesson_logs"
MODEL = "local-hash-v1"
DIM = 64
FRONT = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.DOTALL)
H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)
ALLOWED = {
    "category": {"runtime_error", "data_quality", "performance", "schema_drift", "infra_io"},
    "severity": {"low", "medium", "high", "critical"},
    "status": {"active", "deprecated", "superseded"},
}
NEED = ("lesson_id", "title", "module", "category", "severity", "status",
        "error_codes", "log_signature", "tags", "updated_at")
SECTIONS = {
    "symptom": ("異常特徵", "symptom"),
    "root_cause": ("根本原因", "root cause", "root_cause"),
    "resolution_steps": ("解決方案", "resolution", "solution"),
    "verification": ("驗證指標", "verification"),
    "prevention": ("預防機制", "prevention"),
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _yaml(text: str) -> dict:
    meta, lists = {}, {}
    current = None
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith("  - ") and current:
            lists.setdefault(current, []).append(raw.split("  - ", 1)[1].strip().strip('"'))
            continue
        if ":" not in raw or raw.startswith(" "):
            continue
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip().strip('"')
        current = key
        if value == "":
            lists[key] = []
        else:
            meta[key] = value
    meta.update(lists)
    return meta


def _sections(body: str) -> dict:
    marks = list(H2.finditer(body))
    found = {key: "" for key in SECTIONS}
    for i, mark in enumerate(marks):
        heading = mark.group(1).strip().lower()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        chunk = body[mark.end():end].strip()
        for key, words in SECTIONS.items():
            if any(word in heading for word in words):
                found[key] = chunk
    return found


def _embed(text: str) -> list:
    vec = [0.0] * DIM
    tokens = re.findall(r"\w+", text.lower()) or ["empty"]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vec[int.from_bytes(digest[:2], "big") % DIM] += 1.0 if digest[2] % 2 == 0 else -1.0
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]


def parse_lesson(path: Path) -> dict:
    match = FRONT.match(path.read_text(encoding="utf-8"))
    if not match:
        raise ValueError("%s has no frontmatter" % path.name)
    meta = _yaml(match.group(1))
    missing = [key for key in NEED if key not in meta]
    if missing:
        raise ValueError("%s missing %s" % (path.name, ", ".join(missing)))
    for key, allowed in ALLOWED.items():
        if str(meta[key]) not in allowed:
            raise ValueError("%s bad %s" % (path.name, key))
    sections = _sections(match.group(2))
    for key in ("symptom", "root_cause", "resolution_steps", "verification"):
        if not sections[key]:
            raise ValueError("%s missing section %s" % (path.name, key))
    codes = meta.get("error_codes") or []
    payload = {
        "lesson_id": str(meta["lesson_id"]),
        "title": str(meta["title"]),
        "module": str(meta["module"]),
        "category": str(meta["category"]),
        "severity": str(meta["severity"]),
        "status": str(meta["status"]),
        "error_codes": codes,
        "log_signature": str(meta["log_signature"]),
        "tags": meta.get("tags") or [],
        "updated_at": str(meta["updated_at"])[:10],
        "source_file": path.name,
        **sections,
    }
    payload["embed_text"] = "\n".join([
        payload["module"], payload["title"], " ".join(codes),
        payload["log_signature"], payload["symptom"], payload["root_cause"],
    ])
    payload["content_hash"] = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return payload


def _connect():
    import duckdb
    return duckdb.connect()


def _latest(ledger: Path) -> dict:
    files = sorted(p.as_posix() for p in ledger.glob("part_*.parquet"))
    if not files:
        return {}
    con = _connect()
    rows = con.execute(
        """
        SELECT lesson_id, version, content_hash
        FROM read_parquet(?)
        QUALIFY row_number() OVER (PARTITION BY lesson_id ORDER BY version DESC) = 1
        """,
        [files],
    ).fetchall()
    con.close()
    return {row[0]: (int(row[1]), row[2]) for row in rows}


def compile_lessons(lessons: Path = LESSONS, ledger: Path = LEDGER) -> Path | None:
    records = []
    seen = set()
    for path in sorted(lessons.glob("*.md")):
        rec = parse_lesson(path)
        if rec["lesson_id"] in seen:
            raise ValueError("duplicate " + rec["lesson_id"])
        seen.add(rec["lesson_id"])
        records.append(rec)
    if not records:
        print("NONE lessons")
        return None
    ledger.mkdir(parents=True, exist_ok=True)
    state = _latest(ledger)
    delta = []
    for rec in records:
        prev = state.get(rec["lesson_id"])
        if prev is None:
            delta.append((rec, 1))
        elif prev[1] != rec["content_hash"]:
            delta.append((rec, prev[0] + 1))
    if not delta:
        print("SKIP unchanged")
        return None
    rows = []
    for rec, version in delta:
        rows.append((
            rec["lesson_id"], version, rec["content_hash"], _now(), rec["source_file"],
            rec["title"], rec["module"], rec["category"], rec["severity"], rec["status"],
            json.dumps(rec["error_codes"], ensure_ascii=False), rec["log_signature"],
            rec["symptom"], rec["root_cause"], rec["resolution_steps"], rec["verification"],
            MODEL, _embed(rec["embed_text"]),
        ))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256("".join(rec["content_hash"] for rec, _ in delta).encode("utf-8")).hexdigest()[:8]
    final = ledger / ("part_%s_%s.parquet" % (stamp, digest))
    tmp = ledger / (".%s.tmp.parquet" % final.name)
    con = _connect()
    con.execute(
        """
        CREATE TABLE shard (
          lesson_id VARCHAR, version INTEGER, content_hash VARCHAR, compiled_at VARCHAR,
          source_file VARCHAR, title VARCHAR, module VARCHAR, category VARCHAR, severity VARCHAR,
          status VARCHAR, error_codes VARCHAR, log_signature VARCHAR, symptom VARCHAR,
          root_cause VARCHAR, resolution_steps VARCHAR, verification VARCHAR,
          embedding_model VARCHAR, embedding FLOAT[]
        )
        """
    )
    con.executemany("INSERT INTO shard VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute("COPY shard TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)" % tmp.as_posix())
    con.close()
    os.replace(tmp, final)
    print("WROTE %d %s" % (len(delta), final))
    return final


def search(query: str, ledger: Path = LEDGER, limit: int = 3) -> list:
    files = sorted(p.as_posix() for p in ledger.glob("part_*.parquet"))
    if not files:
        return []
    con = _connect()
    rows = con.execute(
        """
        WITH latest AS (
          SELECT * FROM read_parquet(?)
          QUALIFY row_number() OVER (PARTITION BY lesson_id ORDER BY version DESC) = 1
        )
        SELECT lesson_id, version, module, title, root_cause, resolution_steps,
               list_cosine_similarity(embedding, ?::FLOAT[]) AS score
        FROM latest
        WHERE status = 'active' AND embedding_model = ?
        ORDER BY score DESC
        LIMIT ?
        """,
        [files, _embed(query), MODEL, limit],
    ).fetchall()
    con.close()
    return rows


def pack_envelope(event: dict) -> dict:
    core = ("ts", "run_id", "module", "level", "event", "error_code", "duration_ms")
    extra = {key: value for key, value in event.items() if key not in core}
    return {
        "ts": event.get("ts") or _now(),
        "run_id": str(event.get("run_id") or "local"),
        "module": str(event.get("module") or "unknown"),
        "level": str(event.get("level") or "info"),
        "event": str(event.get("event") or ""),
        "error_code": str(event.get("error_code") or ""),
        "duration_ms": float(event.get("duration_ms") or 0.0),
        "payload_json": json.dumps(extra, ensure_ascii=False, default=str),
    }


def archive_sealed(staging: Path, lake: Path) -> Path | None:
    sealed = []
    for path in staging.glob("*.jsonl"):
        dest = path.with_suffix(".sealed")
        try:
            os.replace(path, dest)
        except PermissionError:
            continue
        sealed.append(dest)
    if not sealed:
        return None
    lake.mkdir(parents=True, exist_ok=True)
    out = lake / ("logs_%d.parquet" % int(datetime.now(timezone.utc).timestamp()))
    con = _connect()
    con.execute(
        """
        COPY (
          SELECT * FROM read_json_auto(?, format='newline_delimited')
        ) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD)
        """ % out.as_posix(),
        [[p.as_posix() for p in sealed]],
    )
    con.close()
    for path in sealed:
        path.unlink(missing_ok=True)
    return out


def node_id(kind: str, value: str) -> str:
    return "%s:%s" % (kind, str(value).strip())


def signature_id(signature: str) -> str:
    return "sig:" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:12]


def _claim(nodes: dict, nid: str, label: str, **fields) -> None:
    prev = nodes.get(nid)
    if prev is not None and prev.get("label") != label:
        raise RuntimeError("node id collision %s" % nid)
    nodes.setdefault(nid, {"id": nid, "label": label, **fields})


def export_peers(ledger: Path = LEDGER, dest: Path | None = None) -> dict:
    """Write the three peer files. Missing products are not an error.

    Node ids are shared by Graphify, OmniRoute and agent-mem.
    EXTRACTED means the target is written in the lesson file.
    A module name is only INFERRED until some source file actually defines it.
    """
    dest = dest or (HERE / "output_hub" / "mega" / "lesson_peers")
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(ledger.glob("part_*.parquet"))
    lessons = []
    if files:
        con = _connect()
        lessons = con.execute(
            """
            SELECT lesson_id, module, title, status, error_codes, log_signature,
                   root_cause, resolution_steps, source_file
            FROM read_parquet(?)
            QUALIFY row_number() OVER (PARTITION BY lesson_id ORDER BY version DESC) = 1
            """,
            [[p.as_posix() for p in files]],
        ).fetchall()
        con.close()
    nodes, edges = {}, {}
    omni, notes, fts_rows = [], [], []
    for row in lessons:
        lesson_id, module, title, status, codes, signature, cause, steps, source = row
        lesson = node_id("lesson", lesson_id)
        module_node = node_id("module", module)
        file_node = node_id("file", "kb/lessons/" + source)
        sig_node = signature_id(signature)
        _claim(nodes, lesson, title, kind="lesson", status=status)
        _claim(nodes, file_node, source, kind="file")
        _claim(nodes, module_node, module, kind="module")
        _claim(nodes, sig_node, signature, kind="signature")
        edges.setdefault((lesson, file_node, "HAS_FILE"),
                         {"source": lesson, "target": file_node, "type": "HAS_FILE", "confidence": "EXTRACTED"})
        edges.setdefault((lesson, sig_node, "HAS_SIGNATURE"),
                         {"source": lesson, "target": sig_node, "type": "HAS_SIGNATURE", "confidence": "EXTRACTED"})
        edges.setdefault((lesson, module_node, "LESSON_FOR"),
                         {"source": lesson, "target": module_node, "type": "LESSON_FOR", "confidence": "INFERRED"})
        error_nodes = []
        for code in json.loads(codes):
            error_node = node_id("error", code)
            error_nodes.append(error_node)
            _claim(nodes, error_node, code, kind="error")
            edges.setdefault((lesson, error_node, "HAS_ERROR"),
                             {"source": lesson, "target": error_node, "type": "HAS_ERROR", "confidence": "EXTRACTED"})
        codes_text = json.loads(codes)
        fts_tokens = [module] + [str(code) for code in codes_text]
        linked = [lesson, file_node, module_node, sig_node] + error_nodes
        omni.append({
            "type": "procedural",
            "key": lesson,
            "content": "%s\n%s\n%s\n%s" % (title, " ".join(fts_tokens), cause, steps),
            "metadata": {
                "node_id": lesson,
                "nodes": linked,
                "lesson_id": lesson_id,
                "source": "vdf_lesson_ledger",
                "fts_tokens": fts_tokens,
                "scope": "api_key_required",
            },
        })
        notes.append((lesson, title, module, steps, source, linked))
        fts_rows.append((lesson_id, " ".join(fts_tokens), "%s\n%s" % (cause, steps)))
    graph_path = dest / "vdf_lessons_overlay.json"
    graph_path.write_text(json.dumps({
        "schema": "VDF-LESSON-OVERLAY/1.1",
        "merge": "id",
        "replaces_graph_json": False,
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    omni_path = dest / "omniroute_memory.jsonl"
    omni_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in omni), encoding="utf-8")
    mem_dir = dest / "agent_mem"
    mem_dir.mkdir(exist_ok=True)
    for lesson, title, module, steps, source, linked in notes:
        body = ["---", "node_id: " + lesson, "module: " + module, "nodes:"]
        body.extend("  - " + item for item in linked)
        body.extend(["files:", "  - kb/lessons/" + source, "---", "", steps, ""])
        (mem_dir / (lesson.split(":", 1)[1] + ".md")).write_text("\n".join(body), encoding="utf-8")
    fts_path = dest / "lessons_fts.sqlite"
    _write_fts(fts_path, fts_rows)
    print("graphify=%s" % graph_path)
    print("omniroute=%s" % omni_path)
    print("agent_mem=%s" % mem_dir)
    print("fts=%s" % fts_path)
    return {"graphify": graph_path, "omniroute": omni_path, "agent_mem": mem_dir, "fts": fts_path}


def _write_fts(path: Path, rows: list) -> None:
    import sqlite3
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute(
        "CREATE VIRTUAL TABLE lesson_fts USING fts5(lesson_id UNINDEXED, tokens, body, tokenize='trigram')"
    )
    con.executemany("INSERT INTO lesson_fts(lesson_id, tokens, body) VALUES (?,?,?)", rows)
    con.commit()
    con.close()


def selftest() -> int:
    import tempfile
    rec = parse_lesson(LESSONS / "LL-20261119-001.md")
    if rec["lesson_id"] != "LL-20261119-001" or "WinError 32" not in rec["error_codes"]:
        print("[FAIL] parse")
        return 1
    try:
        taken = {}
        _claim(taken, "sig:aa", "one", kind="signature")
        _claim(taken, "sig:aa", "two", kind="signature")
        print("[FAIL] signature collision was kept")
        return 1
    except RuntimeError:
        pass
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        first = compile_lessons(LESSONS, root / "ledger")
        second = compile_lessons(LESSONS, root / "ledger")
        if first is None or second is not None:
            print("[FAIL] incremental compile")
            return 1
        hits = search("WinError 32 file lock", root / "ledger")
        if not hits or hits[0][0] != "LL-20261119-001":
            print("[FAIL] search", hits)
            return 1
        stage = root / "stage"
        stage.mkdir()
        (stage / "a.jsonl").write_text(json.dumps(pack_envelope({
            "module": "log_archiver", "level": "error", "event": "archive",
            "error_code": "WinError 32", "ticker": "2330",
        }), ensure_ascii=False) + "\n", encoding="utf-8")
        archived = archive_sealed(stage, root / "lake")
        if archived is None or not archived.is_file():
            print("[FAIL] archive")
            return 1
        peers = export_peers(root / "ledger", root / "peers")
        overlay = json.loads(peers["graphify"].read_text(encoding="utf-8"))
        if overlay.get("schema") != "VDF-LESSON-OVERLAY/1.1" or overlay.get("replaces_graph_json") is not False:
            print("[FAIL] overlay is not marked as an overlay")
            return 1
        ids = [node["id"] for node in overlay["nodes"]]
        if len(ids) != len(set(ids)):
            print("[FAIL] duplicate node id")
            return 1
        lesson = "lesson:LL-20261119-001"
        by_type = {}
        for edge in overlay["edges"]:
            by_type.setdefault(edge["type"], set()).add(edge["confidence"])
        if by_type.get("LESSON_FOR") != {"INFERRED"} or "EXTRACTED" not in by_type.get("HAS_ERROR", ()):
            print("[FAIL] confidence", by_type)
            return 1
        if lesson not in ids or "error:WinError 32" not in ids:
            print("[FAIL] node ids", ids)
            return 1
        line = json.loads(peers["omniroute"].read_text(encoding="utf-8").splitlines()[0])
        if line["key"] != lesson or line["metadata"]["node_id"] != lesson or "api_key_id" in line:
            print("[FAIL] omniroute key")
            return 1
        if "WinError" not in line["content"].split("\n")[1].split():
            print("[FAIL] fts token", line["content"])
            return 1
        note = (peers["agent_mem"] / "LL-20261119-001.md").read_text(encoding="utf-8")
        if "node_id: " + lesson not in note or "error:WinError 32" not in note:
            print("[FAIL] agent-mem node id")
            return 1
        import sqlite3
        hit = sqlite3.connect(peers["fts"]).execute(
            "SELECT lesson_id FROM lesson_fts WHERE lesson_fts MATCH ?", ('"同一個"',)
        ).fetchall()
        if hit != [("LL-20261119-001",)]:
            print("[FAIL] trigram fts", hit)
            return 1
    print("[OK] lesson ledger + graphify overlay + omniroute memory + agent-mem note")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "selftest"
    if cmd == "selftest":
        return selftest()
    if cmd == "compile":
        compile_lessons()
        return 0
    if cmd == "query" and len(argv) > 1:
        rows = search(" ".join(argv[1:]))
        if not rows:
            print("NONE")
            return 1
        for row in rows:
            print("%s v%s score=%.3f %s" % (row[0], row[1], row[6], row[3]))
        return 0
    if cmd == "export":
        compile_lessons()
        export_peers()
        return 0
    print("verbs: selftest | compile | query <text> | export")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
