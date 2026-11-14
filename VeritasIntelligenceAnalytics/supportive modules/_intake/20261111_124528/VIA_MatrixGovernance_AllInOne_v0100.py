#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA Matrix Governance v0100 — single-file backend + embedded HTML UI.
Python 3.11+; UI/tests: standard library. Data output: pyarrow (required).
Run: python VIA_MatrixGovernance_AllInOne_v0100.py
CLI: --self-test --output PATH | --run --input rows.json --output PATH
Local reference engine, not a production certification of VCGC/VDF/VRN.
[VIA:ACCEL-BRIDGE] Built-in bounded executor; no unverified external injection.
"""
from __future__ import annotations

# 01 · All configurable parameters and governance definitions
VERSION = "v0100"
APP_NAME = "VIA Matrix Governance"
HOST = "127.0.0.1"
DEFAULT_PORT = 0
MAX_WORKERS = 4
CHUNK_SIZE = 100
MAX_ROWS = 100000
MAX_BODY_BYTES = 12 * 1024 * 1024
NETWORK_TIMEOUT = 3.0
NETWORK_ATTEMPTS = 3
RETRY_SECONDS = 0.02
STRESS_ROWS = 128
MIN_TPS = 5.0
MIN_STAGE_PASS_RATE = 1.0
MIN_REQUIREMENT_STAGES = 2
MAX_AMOUNT = "9999999999999999.99"
MEMORY_HIGH_PERCENT = 85.0
MAX_PREVIEW_ROWS = 50
STAGES = ["Unit", "Integration", "System", "Verification", "Close-Out"]
REQUIREMENTS = ["R1 · 同義字 / REGEX", "R2 · 輸入邊界", "R3 · 網路交握 / 容錯", "R4 · 並行 / 吞吐", "R5 · 輸出 / 歸檔"]
PLANNED_TRACE = [[1,1,1,1,0], [1,1,1,1,0], [0,1,1,0,1], [0,0,1,1,1], [0,0,0,1,1]]
POLICY = {
    "version": "LOCAL-REFERENCE-0100", "ssot_id": None,
    "authority": "Local reference; VCGC approval pending",
    "required": ["ticker_id", "amount"],
    "regex": {"stock": r"[1-9][0-9]{3}", "passive_etf": r"00[0-9]{2,3}",
              "active_etf": r"00[0-9]{3}A", "amount": r"[0-9]+(?:\.[0-9]{1,2})?",
              "node_target": r"NODE_[A-Z0-9_]+"},
    "synonyms": {"code":"ticker_id", "symbol":"ticker_id", "stock_id":"ticker_id",
                 "price":"amount", "val":"amount", "fee":"amount",
                 "endpoint":"node_target", "target":"node_target"},
    "allowed": ["ticker_id", "amount", "node_target", "asset_type"],
    "default_node": "NODE_DEFAULT", "default_asset": "stock",
}
NETWORK_REGISTRY = {"mode":"LOOPBACK_TEST_ONLY", "external_enabled":False,
                    "ssot_id":None, "approved_by_vcgc":False}
PRODUCTION_REQUIREMENTS = [
    ("VCGC_APPROVAL", "VCGC SSOT / 政策 / 網路註冊核准"),
    ("VCGC_REAL", "VCGC 實機整合與規則大規模壓測"),
    ("VDF_REAL", "VDF 實機契約、資料品質與千萬筆壓測"),
    ("VRN_REAL", "VRN 真實報告、OCR / 版面與萬份文件壓測"),
    ("BURN_168H", "168 小時燒機及 CPU / RAM / handle 洩漏驗證"),
    ("DISASTER", "斷電 / 磁碟滿 / 網路中斷災難復原與 RPO"),
    ("ROLLBACK", "正式部署及 Git rollback 驗證"),
    ("IDENTITY", "客戶授權與共享帳號整合"),
    ("SECURITY", "Critical / High 缺陷與安全審查"),
    ("UX_KPI", "真實使用者操作、分類與自適應 KPI"),
]
SAMPLE_ROWS = [
    {"code":"2330", "price":"1050.50", "endpoint":"NODE_TWSE_01"},
    {"symbol":"2454", "val":"1200", "target":"NODE_CORE_1"},
    {"stock_id":"2317", "fee":"200.50"},
    {"ticker_id":"3008", "amount":"2500.00", "node_target":"NODE_CORE_3"},
]

import argparse
import concurrent.futures
import copy
import csv
import hashlib
import html
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import secrets
import socket
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request
import urllib.parse
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


# 02 · Persistence, diagnostics, governance — no external network

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_write(path, data):
    """Durable file flush + same-directory replace; not an RPO=0 guarantee."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def atomic_json(path, value):
    atomic_write(path, json_bytes(value))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def environment_info():
    info = {"python":sys.version.split()[0], "platform":sys.platform,
            "cpu_count":os.cpu_count() or 1, "pyarrow":bool(importlib.util.find_spec("pyarrow")),
            "psutil":bool(importlib.util.find_spec("psutil")), "rss_mb":None,
            "memory_percent":None, "cpu_percent":None, "threads":threading.active_count()}
    if info["psutil"]:
        try:
            import psutil
            info.update(rss_mb=round(psutil.Process().memory_info().rss / 1048576, 2),
                        memory_percent=psutil.virtual_memory().percent,
                        cpu_percent=psutil.cpu_percent(interval=0.05))
        except Exception as error:
            # Restricted /proc or OS permissions must not break cleanup.
            info["telemetry_note"] = type(error).__name__ + ": OS telemetry unavailable"
    return info


def resource_plan():
    env = environment_info()
    workers = max(1, min(MAX_WORKERS, env["cpu_count"]))
    chunk = CHUNK_SIZE
    if env["memory_percent"] is not None and env["memory_percent"] >= MEMORY_HIGH_PERCENT:
        workers, chunk = 1, max(1, CHUNK_SIZE // 4)
    return {"workers":workers, "chunk":chunk, "environment":env}


def normalize_and_validate(raw):
    """Strict boundary: reject missing/unknown/ambiguous aliases; Decimal money."""
    require(isinstance(raw, dict), "輸入必須為 JSON object")
    cleaned = {}
    for key, value in raw.items():
        require(isinstance(key, str), "欄位名稱必須為文字")
        name = key.strip().lower()
        name = POLICY["synonyms"].get(name, name)
        require(name in POLICY["allowed"], "未知欄位: " + key)
        require(name not in cleaned, "CFG-ALIAS: 多欄位映射至 " + name)
        require(isinstance(value, str), "欄位值必須使用字串: " + name)
        require(len(value) <= 128, "欄位過長: " + name)
        cleaned[name] = value.strip()
    require(all(k in cleaned for k in POLICY["required"]), "缺少 ticker_id 或 amount")
    cleaned.setdefault("asset_type", POLICY["default_asset"])
    cleaned.setdefault("node_target", POLICY["default_node"])
    require(cleaned["asset_type"] in ("stock", "passive_etf", "active_etf"), "不支援的 asset_type")
    for field, rule in (("ticker_id", cleaned["asset_type"]), ("amount", "amount"), ("node_target", "node_target")):
        require(re.fullmatch(POLICY["regex"][rule], cleaned[field]) is not None, "REGEX 不符: " + field)
    number = Decimal(cleaned["amount"])
    require(number <= Decimal(MAX_AMOUNT), "金額超過政策上限")
    cleaned["amount"] = format(number.quantize(Decimal("0.01")), "f")
    return cleaned


def prepare_rows(rows):
    require(isinstance(rows, list) and 0 < len(rows) <= MAX_ROWS, "輸入必須是非空陣列，最多 %d 筆" % MAX_ROWS)
    result, rejected, seen = [], [], set()
    duplicates = 0
    for index, raw in enumerate(rows):
        try:
            value = normalize_and_validate(raw)
            key = digest(value)
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            result.append(value)
        except ValueError as error:
            rejected.append({"row":index + 1, "error":str(error), "incident_id":"CFG-%06d" % (len(rejected) + 1),
                             "source":"input", "scope":"input boundary", "severity":"HIGH", "suggestion":"修正欄位後重新執行；不自動修改治理政策"})
    return result, rejected, duplicates


def parse_json(data):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "JSON 重複鍵: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("非有限數字: " + value)
    return json.loads(data, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


# 03 · Real local HTTP contract fixture, tracked network resources, bounded executor

def start_fixture():
    state = {"counts":{}, "lock":threading.Lock()}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                require(0 < length <= MAX_BODY_BYTES, "size")
                self.connection.settimeout(NETWORK_TIMEOUT)
                body = parse_json(self.rfile.read(length))
                with state["lock"]:
                    count = state["counts"].get(self.path, 0) + 1
                    state["counts"][self.path] = count
                code = 200
                if self.path == "/deny":
                    code = 403
                elif self.path.startswith("/transient") and count == 1:
                    code = 503
                elif self.path == "/unavailable":
                    code = 503
                payload = {"payload":body, "net_status":code}
                if self.path == "/corrupt":
                    payload["payload"] = {"ticker_id":"9999"}
                data = json_bytes(payload)
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (ValueError, OSError):
                self.close_connection = True
    server = ThreadingHTTPServer((HOST, 0), Handler)
    server.daemon_threads = False
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval":0.05}, name="VIA-Fixture", daemon=True)
    thread.start()
    return {"server":server, "thread":thread, "url":"http://%s:%d" % server.server_address, "state":state}


def new_network(fixture):
    return {"url":fixture["url"], "lock":threading.Lock(), "active":0, "peak":0,
            "attempts":0, "completed":0, "retries":0}


def dispatch_packet(net, payload, path="/echo"):
    # Private fixture URL only: this function cannot take arbitrary external URLs.
    for attempt in range(NETWORK_ATTEMPTS):
        with net["lock"]:
            net["active"] += 1
            net["peak"] = max(net["peak"], net["active"])
            net["attempts"] += 1
        try:
            request = urllib.request.Request(net["url"] + path, data=json_bytes(payload), headers={"Content-Type":"application/json"})
            # Ignore environment proxies even for loopback; no credentials sent.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=NETWORK_TIMEOUT) as response:
                data = response.read(MAX_BODY_BYTES + 1)
                require(len(data) <= MAX_BODY_BYTES, "回應過大")
                output = parse_json(data)
            require(output.get("net_status") == 200 and output.get("payload") == payload, "網路契約內容不符")
            with net["lock"]:
                net["completed"] += 1
            return output
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
            if code in (401,403):
                raise PermissionError("網路拒絕；禁止降級繞過") from error
            if code not in (429,500,502,503,504) or attempt + 1 == NETWORK_ATTEMPTS:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == NETWORK_ATTEMPTS:
                raise
        finally:
            with net["lock"]:
                net["active"] -= 1
        with net["lock"]:
            net["retries"] += 1
        time.sleep(RETRY_SECONDS * (2 ** attempt))
    raise RuntimeError("重試用盡")


def execute_transaction(raw, net):
    value = normalize_and_validate(raw)
    dispatch_packet(net, value)
    return {"status":"PASS", "std_ticker":value["ticker_id"], "asset_type":value["asset_type"],
            "verified_amount":value["amount"], "routed_node":value["node_target"]}


def verify_output(output, expected):
    wanted = {"status":"PASS", "std_ticker":expected["ticker_id"], "asset_type":expected["asset_type"],
              "verified_amount":expected["amount"], "routed_node":expected["node_target"]}
    require(output == wanted, "輸出與獨立預期值不符")
    return True


def stop_fixture(fixture):
    fixture["server"].shutdown()
    fixture["server"].server_close()
    fixture["thread"].join(timeout=NETWORK_TIMEOUT)
    require(not fixture["thread"].is_alive(), "Fixture 執行緒未關閉")


# 04 · Parquet first; atomic chunk commit; hash-checked deterministic resume

def parquet_schema():
    import pyarrow as pa
    return pa.schema([("status",pa.string()), ("std_ticker",pa.string()), ("asset_type",pa.string()),
                      ("verified_amount",pa.decimal128(18,2)), ("routed_node",pa.string())])


def write_parquet(path, rows):
    import pyarrow as pa
    import pyarrow.parquet as pq
    values = [dict(row, verified_amount=Decimal(row["verified_amount"])) for row in rows]
    table = pa.Table.from_pylist(values, schema=parquet_schema())
    target = Path(path)
    temp = target.with_suffix(".parquet.tmp")
    try:
        pq.write_table(table, temp, compression="zstd")
        with temp.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink()


def read_parquet(path):
    import pyarrow.parquet as pq
    table = pq.read_table(path)
    require(table.schema == parquet_schema(), "Parquet schema 不符")
    return [dict(row, verified_amount=format(row["verified_amount"], ".2f")) for row in table.to_pylist()]


def checkpoint_load(folder, fingerprint):
    path = folder / "checkpoint.json"
    if not path.exists():
        return {"fingerprint":fingerprint, "chunks":[], "rows":0}
    saved = parse_json(path.read_bytes())
    require(saved["fingerprint"] == fingerprint, "續跑來源或政策 / 程式版本已改變")
    total = 0
    for index, item in enumerate(saved["chunks"]):
        require(item["name"] == "part-%06d.parquet" % index, "檢查點檔名不符")
        part = folder / item["name"]
        require(part.is_file() and file_digest(part) == item["sha256"], "檢查點雜湊不符；保留檔案等待修復")
        total += item["rows"]
    require(total == saved["rows"], "檢查點筆數不符")
    return saved


def export_data(folder, rows, executor, net, cancel, progress, fingerprint):
    require(bool(importlib.util.find_spec("pyarrow")), "缺少 pyarrow；請執行 python -m pip install pyarrow")
    checkpoint = checkpoint_load(folder, fingerprint)
    require(checkpoint["rows"] <= len(rows), "檢查點超出輸入長度")
    # Verify checkpoint data against current input, not only stored hashes.
    offset = 0
    for part in checkpoint["chunks"]:
        old = read_parquet(folder / part["name"])
        require(len(old) == part["rows"], "檢查點檔案筆數不符")
        for output in old:
            verify_output(output, rows[offset])
            offset += 1
    resumed = checkpoint["rows"]
    while checkpoint["rows"] < len(rows):
        if cancel.is_set():
            raise InterruptedError("使用者停止；已完成批次保留可續跑")
        plan = resource_plan()
        start = checkpoint["rows"]
        batch = rows[start:start + plan["chunk"]]
        # Queue bounded to one chunk; high memory uses sequential execution.
        if plan["workers"] == 1:
            outputs = [execute_transaction(row, net) for row in batch]
        else:
            outputs = list(executor.map(lambda row: execute_transaction(row, net), batch))
        for output, expected in zip(outputs, batch):
            verify_output(output, expected)
        name = "part-%06d.parquet" % len(checkpoint["chunks"])
        write_parquet(folder / name, outputs)
        part = {"name":name, "rows":len(outputs), "sha256":file_digest(folder / name)}
        checkpoint["chunks"].append(part)
        checkpoint["rows"] += len(outputs)
        atomic_json(folder / "checkpoint.json", checkpoint)
        progress(checkpoint["rows"], len(rows))
    # A final Parquet file is streamed from committed chunks (no giant concat).
    import pyarrow as pa
    import pyarrow.parquet as pq
    temp = folder / "output.parquet.tmp"
    try:
        with pq.ParquetWriter(temp, parquet_schema(), compression="zstd") as writer:
            for part in checkpoint["chunks"]:
                for batch in pq.ParquetFile(folder / part["name"]).iter_batches(batch_size=CHUNK_SIZE):
                    writer.write_table(pa.Table.from_batches([batch], schema=parquet_schema()))
        with temp.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temp, folder / "output.parquet")
    finally:
        if temp.exists():
            temp.unlink()
    csv_temp = folder / "output.csv.tmp"
    try:
        with csv_temp.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=parquet_schema().names)
            writer.writeheader()
            for part in checkpoint["chunks"]:
                writer.writerows(read_parquet(folder / part["name"]))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(csv_temp, folder / "output.csv")
    finally:
        if csv_temp.exists():
            csv_temp.unlink()
    return {"rows":checkpoint["rows"], "resumed_rows":resumed, "chunks":len(checkpoint["chunks"]),
            "parquet_sha256":file_digest(folder / "output.parquet")}


# 05 · Independent labeled test oracle and evidence-driven lifecycle

def oracle_cases():
    good = {"ticker_id":"2330", "amount":"1050.50", "node_target":"NODE_DEFAULT", "asset_type":"stock"}
    return [
        ("stock", {"symbol":"2330", "price":"1050.5"}, good),
        ("trim endpoint", {" code ":"2330", "amount":"1050.50", " endpoint ":"NODE_DEFAULT"}, good),
        ("passive ETF", {"ticker_id":"0050", "amount":"1", "asset_type":"passive_etf"}, {"ticker_id":"0050", "amount":"1.00", "node_target":"NODE_DEFAULT", "asset_type":"passive_etf"}),
        ("active ETF", {"ticker_id":"00981A", "amount":"1.01", "asset_type":"active_etf"}, {"ticker_id":"00981A", "amount":"1.01", "node_target":"NODE_DEFAULT", "asset_type":"active_etf"}),
        ("zero", {"ticker_id":"2330", "amount":"0"}, dict(good, amount="0.00")),
        ("maximum", {"ticker_id":"2330", "amount":MAX_AMOUNT}, dict(good, amount=MAX_AMOUNT)),
        ("missing", {"code":"2330"}, None),
        ("ETF as stock", {"code":"0050", "price":"10"}, None),
        ("Unicode ticker", {"code":"２３３０", "price":"10"}, None),
        ("negative", {"code":"2330", "price":"-1"}, None),
        ("three decimals", {"code":"2330", "price":"1.234"}, None),
        ("NaN", {"code":"2330", "price":"NaN"}, None),
        ("infinity", {"code":"2330", "price":"Infinity"}, None),
        ("boolean", {"code":"2330", "price":True}, None),
        ("float", {"code":"2330", "price":1.25}, None),
        ("unknown", {"code":"2330", "price":"10", "extra":"x"}, None),
        ("alias collision", {"code":"2330", "ticker_id":"2454", "price":"10"}, None),
        ("same alias collision", {"code":"2330", "ticker_id":"2330", "price":"10"}, None),
        ("node", {"code":"2330", "price":"10", "target":"http://evil"}, None),
        ("newline injection", {"code":"2330\nx", "price":"10"}, None),
        ("overflow", {"code":"2330", "price":"10000000000000000"}, None),
        ("null", {"code":"2330", "price":None}, None),
        ("not object", [], None),
    ]


def expect_rejection(fn, exception=ValueError):
    try:
        fn()
    except exception:
        return True
    raise ValueError("應被拒絕但未攔截")


def new_report(run_id):
    return {"app":APP_NAME, "version":VERSION, "run_id":run_id, "started_at":utc_now(),
            "status":"RUNNING", "phase":"Environment", "progress":0,
            "policy_sha256":digest(POLICY), "policy":POLICY, "network_registry":NETWORK_REGISTRY,
            "cases":[], "state_matrix":[], "trace_matrix":[[0]*5 for _ in range(5)],
            "planned_trace":PLANNED_TRACE, "confusion":{"TP":0,"TN":0,"FP":0,"FN":0,"definition":"positive = invalid input; predicted positive = rejected"},
            "resources":{}, "exports":{}, "rejected":[], "preview":[], "events":[],
            "gate":{"local_reference_pass":False, "go_live":False, "reason":"尚未完成"},
            "production_gates":[{"id":key,"requirement":label,"status":"NOT_EXECUTED"} for key,label in PRODUCTION_REQUIREMENTS]}


def refresh_matrices(report):
    matrix, trace = [], [[0]*5 for _ in range(5)]
    for stage in range(5):
        cases = [c for c in report["cases"] if c["stage"] == stage]
        passed = sum(c["status"] == "PASS" for c in cases)
        for req in range(5):
            relevant = [c for c in cases if req in c["requirements"]]
            trace[req][stage] = int(bool(relevant) and all(c["status"] == "PASS" for c in relevant))
        planned = sum(row[stage] for row in PLANNED_TRACE)
        covered = sum(trace[req][stage] for req in range(5) if PLANNED_TRACE[req][stage])
        matrix.append({"stage":STAGES[stage], "total":len(cases), "passed":passed,
                       "pass_rate":passed/len(cases) if cases else None,
                       "requirement_coverage":covered/planned if planned else None,
                       "elapsed_ms":round(sum(c["elapsed_ms"] for c in cases),2),
                       "status":("FAIL" if passed<len(cases) else "PASS") if cases else "PENDING"})
    report["state_matrix"], report["trace_matrix"] = matrix, trace


def render_audit_html(report):
    escaped = html.escape(json.dumps(report, ensure_ascii=False, indent=2))
    rows = "".join("<tr><td>%s</td><td>%s/%s</td><td>%s</td></tr>" % (m["stage"],m["passed"],m["total"],m["status"]) for m in report["state_matrix"])
    return ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><title>VIA Audit</title><style>body{font:14px system-ui;background:#101727;color:#e2e8f0;padding:30px}td,th{padding:10px;border-bottom:1px solid #334155}pre{white-space:pre-wrap}h1{color:#64dfb2}</style>"
            + "<h1>理 · VIA Matrix Governance</h1><p>本機參考測試：%s；正式放行：BLOCKED</p>" % report["gate"]["local_reference_pass"]
            + "<table><tr><th>階段</th><th>通過 / 總數</th><th>狀態</th></tr>" + rows + "</table><details><summary>完整證據、需求矩陣與門檻</summary><pre>" + escaped + "</pre></details></html>").encode("utf-8")


@contextmanager
def exclusive_workspace(root):
    """OS lock survives crashes without a stale PID file; no concurrent writers."""
    Path(root).mkdir(parents=True, exist_ok=True)
    handle = (Path(root) / "workspace.lock").open("a+b")
    acquired = False
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
        yield
    finally:
        if acquired:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def run_pipeline(raw_rows, root, cancel=None, on_update=None, resume=False):
    with exclusive_workspace(root):
        return run_pipeline_locked(raw_rows, root, cancel, on_update, resume)


def run_pipeline_locked(raw_rows, root, cancel=None, on_update=None, resume=False):
    cancel = cancel or threading.Event()
    on_update = on_update or (lambda report: None)
    source_hash = file_digest(__file__)
    fingerprint = digest({"rows":raw_rows,"policy":POLICY,"version":VERSION,"source_sha256":source_hash})
    run_id = fingerprint[:20]
    folder = Path(root) / run_id
    if resume:
        for previous in sorted(Path(root).glob(run_id + "*/report.json"), key=lambda p:p.stat().st_mtime, reverse=True):
            saved = parse_json(previous.read_bytes())
            if saved.get("input_fingerprint") == fingerprint:
                folder, run_id = previous.parent, previous.parent.name
                break
    folder.mkdir(parents=True, exist_ok=True)
    # Never erase existing evidence. New run generation, or explicit resume only.
    if not resume and (folder / "report.json").exists():
        run_id += "-" + secrets.token_hex(3)
        folder = Path(root) / run_id
        folder.mkdir()
    report = new_report(run_id)
    report["input_fingerprint"] = fingerprint
    if resume and (folder / "report.json").exists():
        history_name = "report-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(3) + ".json"
        atomic_write(folder / "history" / history_name, (folder / "report.json").read_bytes())
    report["source_sha256"] = source_hash
    report["output_directory"] = str(folder.resolve())
    fixture = net = executor = None
    worker_prefix = "VIA-" + secrets.token_hex(4)
    def publish():
        refresh_matrices(report)
        atomic_json(folder / "report.json", report)
        on_update(copy.deepcopy(report))
    def event(message):
        item = {"time":utc_now(),"message":message}
        report["events"].append(item)
        with (folder / "audit.jsonl").open("ab") as handle:
            handle.write(json_bytes(item) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    def check(stage, name, reqs, fn):
        started = time.perf_counter()
        status, detail = "PASS", ""
        try:
            fn()
        except Exception as error:
            status, detail = "FAIL", type(error).__name__ + ": " + str(error)
        report["cases"].append({"stage":stage,"name":name,"requirements":reqs,"status":status,
                                "detail":detail,"elapsed_ms":round((time.perf_counter()-started)*1000,3)})
        event(STAGES[stage] + " / " + name + " / " + status + (" / " + detail if detail else ""))
        publish()
        return status == "PASS"
    def phase(number):
        if cancel.is_set():
            raise InterruptedError("使用者停止")
        report["phase"] = STAGES[number]
        report["progress"] = number * 20
        event("開始 " + STAGES[number])
        publish()
    def progress(done,total):
        report["progress"] = 60 + int(15 * done / max(1,total))
        report["processed_rows"] = done
        publish()
    failure = None
    try:
        report["resource_plan"] = resource_plan()
        event("環境檢查完成；使用本機 HTTP fixture；外網關閉")
        phase(0)
        # Unit stage has no fixture, executor, or network initialization.
        for name, raw, expected in oracle_cases():
            def unit(raw=raw, expected=expected):
                if expected is None:
                    expect_rejection(lambda: normalize_and_validate(raw))
                else:
                    require(normalize_and_validate(raw) == expected, "正規化與預期不符")
            check(0,name,[0,1],unit)
        check(0,"JSON duplicate keys",[1],lambda: expect_rejection(lambda: parse_json('{"code":"2330","code":"2454"}')))
        check(0,"No infrastructure initialized",[0,1],lambda: require(fixture is None and executor is None, "Unit 階段不得建立網路 / pool"))
        phase(1)
        fixture = start_fixture()
        net = new_network(fixture)
        exemplar = {"ticker_id":"2454","amount":"1200.00","node_target":"NODE_TWSE_01","asset_type":"stock"}
        check(1,"HTTP contract + aliases",[0,1,2],lambda: verify_output(execute_transaction({"stock_id":"2454","val":"1200","endpoint":"NODE_TWSE_01"},net),exemplar))
        check(1,"503 then retry",[2],lambda: dispatch_packet(net,exemplar,"/transient"))
        def denied():
            before = net["attempts"]
            expect_rejection(lambda: dispatch_packet(net,exemplar,"/deny"),PermissionError)
            require(net["attempts"] - before == 1,"DENY 不得重試")
        check(1,"DENY no bypass",[2],denied)
        def exhaustion():
            before = net["attempts"]
            expect_rejection(lambda: dispatch_packet(net,exemplar,"/unavailable"),urllib.error.HTTPError)
            require(net["attempts"] - before == NETWORK_ATTEMPTS,"重試次數不符")
            require(net["active"] == 0,"失敗後連線未回收")
        check(1,"Bounded retries + exception cleanup",[2],exhaustion)
        check(1,"Corrupt payload rejected",[2],lambda: expect_rejection(lambda: dispatch_packet(net,exemplar,"/corrupt")))
        phase(2)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=report["resource_plan"]["workers"],thread_name_prefix=worker_prefix)
        def system_stress():
            started = time.perf_counter()
            outputs = list(executor.map(lambda _:execute_transaction({"symbol":"2330","price":"1050.50"},net), range(STRESS_ROWS)))
            elapsed = time.perf_counter() - started
            for value in outputs:
                verify_output(value,{"ticker_id":"2330","amount":"1050.50","node_target":"NODE_DEFAULT","asset_type":"stock"})
            report["stress"] = {"rows":STRESS_ROWS,"seconds":round(elapsed,4),"tps":round(STRESS_ROWS/elapsed,2),"minimum_tps":MIN_TPS,"scope":"local HTTP fixture"}
            require(report["stress"]["tps"] >= MIN_TPS,"TPS 未達設定門檻")
        check(2,"Concurrent E2E + TPS",[0,1,2,3],system_stress)
        def boundary_before_network():
            before = net["attempts"]
            expect_rejection(lambda:execute_transaction({"code":"0050","price":"10"},net))
            require(net["attempts"] == before,"無效資料觸發網路")
        check(2,"Boundary blocks before dispatch",[0,1,2],boundary_before_network)
        def future_error():
            f = executor.submit(lambda:execute_transaction({"symbol":"bad","price":"1"},net))
            expect_rejection(lambda:f.result(timeout=NETWORK_TIMEOUT))
        check(2,"Worker exception visible",[3],future_error)
        phase(3)
        for name,raw,expected in oracle_cases():
            def classify(raw=raw,expected=expected):
                try:
                    result = normalize_and_validate(raw)
                    predicted_invalid = False
                except ValueError:
                    result, predicted_invalid = None, True
                actual_invalid = expected is None
                label = ("TP" if predicted_invalid else "FN") if actual_invalid else ("FP" if predicted_invalid else "TN")
                report["confusion"][label] += 1
                require(predicted_invalid == actual_invalid,"分類錯誤: " + label)
                if expected is not None:
                    require(result == expected,"有效資料正規化內容錯誤")
            check(3,"Oracle / " + name,[0,1],classify)
        rows,rejected,duplicates = prepare_rows(raw_rows)
        report.update(input_rows=len(raw_rows),valid_unique_rows=len(rows),duplicates=duplicates,rejected=rejected)
        report["preview"] = [{"status":"VALIDATED",**r} for r in rows[:MAX_PREVIEW_ROWS]]
        check(3,"Input has no unresolved conflicts",[0,1],lambda: require(not rejected and bool(rows),"拒絕 %d 筆；有效 %d 筆" % (len(rejected),len(rows))))
        check(3,"Exact output oracle",[3,4],lambda: verify_output(execute_transaction(exemplar,net),exemplar))
        def tamper_test():
            bad = {"status":"PASS","std_ticker":"2454","asset_type":"stock","verified_amount":"1201.00","routed_node":"NODE_TWSE_01"}
            expect_rejection(lambda:verify_output(bad,exemplar))
        check(3,"Amount tampering detected",[4],tamper_test)
        def export():
            report["exports"] = export_data(folder,rows,executor,net,cancel,progress,fingerprint)
            report["preview"] = read_parquet(folder / "part-000000.parquet")[:MAX_PREVIEW_ROWS] if rows else []
            # Use a fresh read of all saved output rows with independent input order.
            import pyarrow.parquet as pq
            index = 0
            for batch in pq.ParquetFile(folder / "output.parquet").iter_batches(batch_size=CHUNK_SIZE):
                for item in batch.to_pylist():
                    item["verified_amount"] = format(item["verified_amount"],".2f")
                    verify_output(item,rows[index])
                    index += 1
            require(index == len(rows),"輸出筆數不符")
        check(3,"Parquet export + full roundtrip",[3,4],export)
        def recovery_test():
            require(bool(importlib.util.find_spec("pyarrow")),"缺少 pyarrow")
            with tempfile.TemporaryDirectory(prefix="via-recovery-") as directory:
                path = Path(directory)
                data = [exemplar,dict(exemplar,amount="1201.00")]
                first = execute_transaction(exemplar,net)
                write_parquet(path / "part-000000.parquet",[first])
                atomic_json(path / "checkpoint.json",{"fingerprint":"test","rows":1,"chunks":[{"name":"part-000000.parquet","rows":1,"sha256":file_digest(path / "part-000000.parquet")}]})
                result = export_data(path,data,executor,net,threading.Event(),lambda a,b:None,"test")
                require(result["resumed_rows"] == 1 and result["rows"] == 2,"續跑未從既有檢查點開始")
                require(len(read_parquet(path / "output.parquet")) == 2,"續跑重複 / 遺失")
                (path / "part-000000.parquet").write_bytes(b"corrupt")
                expect_rejection(lambda:checkpoint_load(path,"test"))
        check(3,"Checkpoint resume + corruption detection",[3,4],recovery_test)
    except InterruptedError as error:
        failure = "CANCELLED"
        event(str(error))
    except Exception as error:
        failure = "ERROR"
        event(type(error).__name__ + ": " + str(error))
        atomic_write(folder / "error.txt",traceback.format_exc().encode("utf-8"))
    finally:
        report["phase"] = "Close-Out"
        report["progress"] = 90
        # Always close real resources; never force counters to zero.
        def close_resources():
            try:
                if executor is not None:
                    executor.shutdown(wait=True,cancel_futures=True)
            finally:
                if fixture is not None:
                    stop_fixture(fixture)
            active = net["active"] if net is not None else 0
            owned = [t.name for t in threading.enumerate() if t.name.startswith(worker_prefix)]
            report["resources"] = {"active_connections":active,"owned_worker_threads":len(owned),
                                    "fixture_alive":bool(fixture and fixture["thread"].is_alive()),
                                    "http_peak":net["peak"] if net else 0,
                                    "network_attempts":net["attempts"] if net else 0,
                                    "environment_after":environment_info(),
                                    "scope":"only this run's executor and fixture; UI server remains running"}
            require(active == 0 and not owned and not report["resources"]["fixture_alive"],"資源仍有殘留")
        check(4,"Graceful shutdown / no owned resources",[2,3,4],close_resources)
        def archival():
            require(bool(report["exports"]),"無已驗證輸出")
            require((folder / "audit.jsonl").is_file(),"稽核軌跡未保存")
            require(file_digest(folder / "output.parquet") == report["exports"]["parquet_sha256"],"歸檔雜湊不符")
            atomic_json(folder / "manifest.json",{"run_id":run_id,"source_sha256":source_hash,"policy_sha256":digest(POLICY),"files":{name:file_digest(folder/name) for name in ("output.parquet","output.csv","checkpoint.json")}})
        check(4,"Artifact manifest / SHA256",[4],archival)
        refresh_matrices(report)
        coverage = all(sum(row) >= MIN_REQUIREMENT_STAGES for row in report["trace_matrix"])
        stages_ok = all(m["pass_rate"] is not None and m["pass_rate"] >= MIN_STAGE_PASS_RATE and m["requirement_coverage"] == 1 for m in report["state_matrix"])
        cm = report["confusion"]
        confusion_ok = cm["FN"] == cm["FP"] == 0 and cm["TP"] > 0 and cm["TN"] > 0
        local_pass = stages_ok and coverage and confusion_ok and not failure and not cancel.is_set()
        report["status"] = failure or ("CANCELLED" if cancel.is_set() else ("PASS" if local_pass else "FAIL"))
        report["gate"] = {"local_reference_pass":bool(local_pass),"go_live":False,
                          "reason":"本機參考測試已完成；正式系統與附件門檻尚待實機證據" if local_pass else "本機測試未達門檻；詳見失敗證據",
                          "min_requirement_stages":min(map(sum,report["trace_matrix"])),
                          "code_coverage":None,"code_coverage_note":"未測量程式碼行 / 分支 / AST 覆蓋率；矩陣僅為需求覆蓋"}
        report["finished_at"] = utc_now()
        report["phase"],report["progress"] = "Finished",100
        event("結案: " + report["status"] + "；Go-Live BLOCKED")
        publish()
        atomic_write(folder / "audit.html",render_audit_html(report))
    return report


# 06 · Embedded frontend (no CDN, fonts, build step, or external service)
HTML = r'''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA · Matrix Governance</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--border:#28324b;--muted:#94a4c4;--text:#edf2ff;--green:#56dfb1;--amber:#f9c86a;--red:#ff8997;--purple:#a49bff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:13px/1.5 system-ui,"Microsoft JhengHei",sans-serif}button,input,textarea,select{font:inherit}button,a.link{border:1px solid var(--border);border-radius:7px;background:#1c2841;color:var(--text);padding:9px 13px;cursor:pointer;text-decoration:none;display:inline-block}button:hover,a.link:hover{border-color:var(--purple)}button:disabled{opacity:.4;cursor:wait}.primary{background:var(--green);color:#082e25;font-weight:700;border:0}header{padding:20px 30px;display:flex;align-items:center;gap:14px;border-bottom:1px solid var(--border)}.logo{background:var(--green);color:#0b332a;font-size:32px;width:58px;height:58px;display:grid;place-items:center;border-radius:13px}h1{font-size:20px;letter-spacing:.5px;margin:0}h2{font-size:15px;margin:0 0 14px}p{margin:4px 0}.muted{color:var(--muted)}.badge{padding:3px 9px;border:1px solid var(--border);border-radius:12px;font-size:11px;display:inline-block}.right{margin-left:auto;text-align:right}.shell{max-width:1540px;margin:auto;padding:24px 30px}.toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:16px}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px}.card,.panel{min-width:0;background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px}.value{font-size:28px;font-weight:650;letter-spacing:-1px}.label{color:var(--muted);font-size:12px}.grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:16px}.wide{grid-column:1/-1}.scroll{overflow:auto;max-height:440px}table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:12px}td,th{padding:10px 8px;text-align:left;border-bottom:1px solid var(--border)}th{color:var(--muted);font-weight:500}tr:last-child td{border:0}.PASS{color:var(--green)}.FAIL,.ERROR,.CANCELLED{color:var(--red)}.PENDING,.NOT_EXECUTED{color:var(--amber)}.RUNNING{color:var(--purple)}progress{width:100%;height:5px;accent-color:var(--green);margin:4px 0 16px}.drop{border:1px dashed #536385;border-radius:8px;padding:18px;margin-bottom:12px;background:#101829;text-align:center}.drop.over{border-color:var(--green)}textarea{width:100%;height:190px;background:#0a1120;color:#d6e2ff;border:1px solid var(--border);border-radius:7px;padding:12px;font:12px/1.6 ui-monospace,monospace;resize:vertical}details{margin-top:10px}summary{cursor:pointer;color:var(--muted)}.logs{max-height:200px;overflow:auto;font:11px/1.7 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere}.notice{border-left:3px solid var(--amber);padding:10px 14px;background:#222131;margin-bottom:16px}.error{color:var(--red);white-space:pre-wrap;overflow-wrap:anywhere;min-height:22px}.status-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--green);margin-right:6px}.small{font-size:11px}.matrix td:not(:first-child),.matrix th:not(:first-child){text-align:center}.on{color:var(--green);background:#17382f;border-radius:4px;padding:2px 7px}.off{color:#6c7c99}.downloads{display:flex;gap:8px;flex-wrap:wrap}.tabs{display:flex;gap:6px;flex-wrap:wrap}.tabs button.active{color:var(--green);border-color:var(--green)}.hidden{display:none!important}@media(max-width:900px){.grid{grid-template-columns:minmax(0,1fr)}.cards{grid-template-columns:repeat(2,1fr)}.shell{padding:16px}.right{display:none}header{padding:16px}header>div{min-width:0}.logo{flex-shrink:0}h1{font-size:17px}}@media(max-width:480px){.cards{grid-template-columns:1fr 1fr}.value{font-size:22px}}
</style></head><body>
<header><div class="logo">理</div><div><h1>VIA · Matrix Governance</h1><p class="muted">Veritas Intelligence Analytics · 五階段驗證與治理工作台</p><p class="small">SSOT / Policy / Regex / Synonym · v0100 · 獨立本機參考引擎</p></div><div class="right"><span class="badge"><i class="status-dot"></i>LOCAL ONLY</span><p class="muted small">治理集中 · 執行分離 · 證據驅動</p></div></header>
<main class="shell"><div class="notice">本機測試通過僅代表此參考引擎的已執行案例通過。VCGC / VDF / VRN 實機、168 小時燒機與災難復原未驗證前，正式放行維持 BLOCKED。</div>
<div class="toolbar"><button class="primary" id="start">▶ 一鍵執行五階段</button><button id="resume">↻ 續跑相同輸入</button><button id="stop" disabled>停止並保留檢查點</button><button id="sample">載入範例</button><span class="muted" id="phase">就緒</span><span class="right badge" id="env">檢查環境中</span></div>
<div class="error" id="error" role="alert"></div><progress id="progress" value="0" max="100"></progress>
<div class="cards"><div class="card"><div class="label">本機參考測試</div><div class="value" id="status">READY</div><div class="small muted" id="runid">尚無執行紀錄</div></div><div class="card"><div class="label">實測案例通過率</div><div class="value" id="rate">—</div><div class="small muted" id="counts">由逐項證據計算</div></div><div class="card"><div class="label">本機 HTTP 吞吐量</div><div class="value" id="tps">—</div><div class="small muted">TPS · 非外部資料源效能</div></div><div class="card"><div class="label">正式放行</div><div class="value PENDING">BLOCKED</div><div class="small muted">待實機證據與 VCGC 核准</div></div></div>
<div class="grid"><section class="panel"><h2>01 / 生命周期主矩陣</h2><div class="scroll"><table><thead><tr><th>階段</th><th>需求覆蓋</th><th>通過率</th><th>案例</th><th>耗時 ms</th><th>狀態</th></tr></thead><tbody id="lifecycle"></tbody></table></div><p class="small muted">覆蓋＝已通過的需求／該階段規劃需求；不是程式碼或 AST 覆蓋率。</p></section>
<section class="panel"><h2>02 / 需求追溯矩陣</h2><div class="scroll"><table class="matrix"><thead><tr><th>需求</th><th>T1</th><th>T2</th><th>T3</th><th>T4</th><th>T5</th><th>合計</th></tr></thead><tbody id="trace"></tbody></table></div><p class="small muted">1＝該需求在該階段的所有關聯案例通過；每列至少 2 階段。</p></section>
<section class="panel"><h2>輸入 / 最少操作</h2><div class="drop" id="drop">拖入 JSON，或 <button id="choose">選擇檔案</button><input type="file" accept=".json,application/json" id="file" hidden><p class="muted small">交易資料陣列 · 數值使用字串 · 最多 100,000 筆 / 12 MB</p></div><textarea id="input" aria-label="JSON 輸入"></textarea><p class="muted small">amount 採 Decimal；ETF 需指定 asset_type。原始業務參數不會自行改寫中央政策。</p><details><summary>政策 / 網路註冊資訊（唯讀）</summary><pre class="logs" id="policy"></pre></details></section>
<section class="panel"><h2>驗證 / 資源證據</h2><div class="cards" style="grid-template-columns:repeat(4,1fr)"><div><div class="label">TP</div><div class="value PASS" id="TP">—</div></div><div><div class="label">TN</div><div class="value PASS" id="TN">—</div></div><div><div class="label">FP</div><div class="value" id="FP">—</div></div><div><div class="label">FN</div><div class="value" id="FN">—</div></div></div><p class="small muted">正類＝非法輸入；預測正類＝攔截。僅對內建標記案例計算。</p><div id="resources" class="logs muted">尚未量測</div><h2 style="margin-top:16px">產出與下載</h2><div class="downloads" id="downloads"></div><p class="small muted" id="exportinfo">Parquet 主格式 · CSV UTF-8 BOM · JSON 稽核 · HTML 結案報告</p></section>
<section class="panel wide"><div class="toolbar"><h2 style="margin:0">證據中心</h2><div class="tabs"><button class="active" data-tab="cases">測試案例</button><button data-tab="outputs">資料預覽</button><button data-tab="conflicts">衝突</button><button data-tab="production">正式門檻</button></div></div><div class="scroll" id="evidence"></div></section>
<section class="panel wide"><h2>執行軌跡</h2><div class="logs" id="logs">等待執行。</div></section></div></main>
<script>
'use strict';
const TOKEN=__TOKEN__, SAMPLE=__SAMPLE__, REQS=__REQS__, PHASES=__STAGES__;
const $=id=>document.getElementById(id);let current=null,tab='cases';
function cell(value){const td=document.createElement('td');td.textContent=value??'—';return td}
function tableInto(el,heads,rows){el.replaceChildren();const t=document.createElement('table');const h=document.createElement('thead'),tr=document.createElement('tr');for(const text of heads){const th=document.createElement('th');th.textContent=text;tr.append(th)}h.append(tr);t.append(h);const b=document.createElement('tbody');for(const row of rows){const r=document.createElement('tr');row.forEach(v=>r.append(cell(v)));b.append(r)}t.append(b);el.append(t)}
function pct(v){return v==null?'—':(v*100).toFixed(1)+'%'}
async function api(path,options={}){const res=await fetch(path,{...options,headers:{'X-VIA-Token':TOKEN,'Content-Type':'application/json'}});const data=await res.json();if(!res.ok)throw Error(data.error||res.statusText);return data}
function showEvidence(){if(!current)return;const r=current;if(tab==='cases')tableInto($('evidence'),['階段','案例','狀態','ms','證據 / 錯誤'],r.cases.map(c=>[PHASES[c.stage],c.name,c.status,c.elapsed_ms,c.detail]));if(tab==='outputs')tableInto($('evidence'),['股票','類型','金額','節點','狀態'],r.preview.map(v=>[v.std_ticker||v.ticker_id,v.asset_type,v.verified_amount||v.amount,v.routed_node||v.node_target,v.status]));if(tab==='conflicts')tableInto($('evidence'),['Incident','列','原因','來源','優先級','建議'],r.rejected.map(c=>[c.incident_id,c.row,c.error,c.source,c.severity,c.suggestion]));if(tab==='production')tableInto($('evidence'),['ID','正式驗證需求','狀態'],r.production_gates.map(g=>[g.id,g.requirement,g.status]))}
function render(r,running){current=r;$('start').disabled=running;$('resume').disabled=running;$('stop').disabled=!running;if(!r)return;$('status').textContent=r.status;$('status').className='value '+r.status;$('runid').textContent=r.run_id;$('phase').textContent=r.phase;$('progress').value=r.progress;const passed=r.cases.filter(c=>c.status==='PASS').length;$('rate').textContent=r.cases.length?pct(passed/r.cases.length):'—';$('counts').textContent=passed+' / '+r.cases.length+' 案例';$('tps').textContent=r.stress?.tps??'—';$('lifecycle').replaceChildren();for(const m of r.state_matrix){const tr=document.createElement('tr');[m.stage,pct(m.requirement_coverage),pct(m.pass_rate),m.passed+'/'+m.total,m.elapsed_ms,m.status].forEach(v=>tr.append(cell(v)));tr.lastChild.className=m.status;$('lifecycle').append(tr)}$('trace').replaceChildren();r.trace_matrix.forEach((row,i)=>{const tr=document.createElement('tr');tr.append(cell(REQS[i]));row.forEach(v=>{const td=cell(v);td.className=v?'PASS':'muted';tr.append(td)});tr.append(cell(row.reduce((a,b)=>a+b,0)));$('trace').append(tr)});for(const key of ['TP','TN','FP','FN'])$(key).textContent=r.confusion[key];$('policy').textContent=JSON.stringify({policy:r.policy,network:r.network_registry},null,2);$('resources').textContent=JSON.stringify(r.resources,null,2);$('logs').textContent=r.events.slice(-80).map(x=>x.time+' '+x.message).join('\n');$('exportinfo').textContent=`有效 ${r.valid_unique_rows??0} · 重複 ${r.duplicates??0} · 衝突 ${r.rejected.length} · 已輸出 ${r.exports.rows??0} · 復用 ${r.exports.resumed_rows??0} 筆`;$('downloads').replaceChildren();if(!running&&r.output_directory){for(const [name,label] of [['output.parquet','Parquet'],['output.csv','CSV'],['report.json','JSON'],['audit.html','HTML'],['manifest.json','SHA256']]){if((name.startsWith('output')||name==='manifest.json')&&!r.exports.rows)continue;const btn=document.createElement('button');btn.textContent=label;btn.onclick=()=>download(name);$('downloads').append(btn)}}showEvidence()}
async function download(name){try{const res=await fetch('/api/download?name='+encodeURIComponent(name),{headers:{'X-VIA-Token':TOKEN}});if(!res.ok)throw Error('檔案尚未生成');const url=URL.createObjectURL(await res.blob());const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){$('error').textContent=e.message}}
async function start(resume){$('error').textContent='';try{JSON.parse($('input').value);await api('/api/run',{method:'POST',body:JSON.stringify({rows_json:$('input').value,resume})});await poll()}catch(e){$('error').textContent=e.message}}
async function poll(){try{const data=await api('/api/status');render(data.report,data.running)}catch(e){$('error').textContent='連線異常：'+e.message}}
$('start').onclick=()=>start(false);$('resume').onclick=()=>start(true);$('stop').onclick=async()=>{try{await api('/api/stop',{method:'POST',body:'{}'})}catch(e){$('error').textContent=e.message}};$('sample').onclick=()=>{$('input').value=JSON.stringify(SAMPLE,null,2)};$('sample').click();
async function readFile(file){if(!file)return;try{if(file.size>12*1024*1024)throw Error('檔案超過 12 MB');const text=await file.text();JSON.parse(text);$('input').value=text;$('error').textContent=''}catch(e){$('error').textContent=e.message}}
$('choose').onclick=()=>$('file').click();$('file').onchange=e=>readFile(e.target.files[0]);$('drop').ondragover=e=>{e.preventDefault();$('drop').classList.add('over')};$('drop').ondragleave=()=>$('drop').classList.remove('over');$('drop').ondrop=e=>{e.preventDefault();$('drop').classList.remove('over');readFile(e.dataTransfer.files[0])};document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));showEvidence()});
api('/api/environment').then(e=>{$('env').textContent='Python '+e.python+' · CPU '+e.cpu_count+' · Parquet '+(e.pyarrow?'READY':'MISSING');if(!e.pyarrow)$('error').textContent='缺少 Parquet 套件：請執行 python -m pip install pyarrow 後重新啟動。'}).catch(e=>$('error').textContent=e.message);
poll();setInterval(poll,1000);
</script></body></html>'''


# 07 · Local authenticated HTTP API, asynchronous jobs, controlled downloads

def serve_ui(root, port=DEFAULT_PORT, open_browser=True):
    token = secrets.token_urlsafe(32)
    lock = threading.RLock()
    state = {"running":False,"report":None,"cancel":threading.Event(),"worker":None}
    root = Path(root).resolve()
    root.mkdir(parents=True,exist_ok=True)
    # Reload most recent completed evidence; interrupted jobs need explicit resume.
    reports = sorted(root.glob("*/report.json"),key=lambda p:p.stat().st_mtime,reverse=True)
    if reports:
        try:
            state["report"] = parse_json(reports[0].read_bytes())
            if state["report"]["status"] == "RUNNING":
                state["report"]["status"] = "INTERRUPTED"
                state["report"]["phase"] = "前次工作中斷；提供相同輸入後可續跑"
        except (ValueError,OSError):
            pass
    if state["report"] is None:
        state["report"] = new_report("尚無執行紀錄")
        state["report"].update(status="READY", phase="就緒")
        refresh_matrices(state["report"])
    page = HTML.replace("__TOKEN__",json.dumps(token)).replace("__SAMPLE__",json.dumps(SAMPLE_ROWS)).replace("__REQS__",json.dumps(REQUIREMENTS)).replace("__STAGES__",json.dumps(STAGES))
    def update(report):
        with lock:
            state["report"] = report
    def work(rows, resume):
        try:
            run_pipeline(rows,root,state["cancel"],update,resume)
        except Exception as error:
            with lock:
                report = state["report"] or new_report("startup-error")
                report["status"] = "ERROR"
                report["events"].append({"time":utc_now(),"message":str(error)})
                state["report"] = report
        finally:
            with lock:
                state["running"] = False
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):
            pass
        def reply(self,code,data,content_type="application/json; charset=utf-8",filename=None):
            if isinstance(data,(dict,list)):
                data = json_bytes(data)
            self.send_response(code)
            self.send_header("Content-Type",content_type)
            self.send_header("Content-Length",str(len(data)))
            self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff")
            self.send_header("X-Frame-Options","DENY")
            self.send_header("Content-Security-Policy","default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
            if filename:
                self.send_header("Content-Disposition",'attachment; filename="'+filename+'"')
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):
                pass
        def authorized(self,api=True):
            expected = "%s:%d" % self.server.server_address
            if self.headers.get("Host") != expected:
                self.reply(403,{"error":"Host rejected"})
                return False
            if api and not secrets.compare_digest(self.headers.get("X-VIA-Token",""),token):
                self.reply(403,{"error":"Token required"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin != "http://" + expected:
                self.reply(403,{"error":"Origin rejected"})
                return False
            return True
        def do_GET(self):
            path = urllib.parse.urlsplit(self.path)
            if not self.authorized(path.path != "/"):
                return
            if path.path == "/":
                self.reply(200,page.encode("utf-8"),"text/html; charset=utf-8")
            elif path.path == "/api/environment":
                self.reply(200,environment_info())
            elif path.path == "/api/status":
                with lock:
                    data = {"report":copy.deepcopy(state["report"]),"running":state["running"]}
                self.reply(200,data)
            elif path.path == "/api/download":
                name = urllib.parse.parse_qs(path.query).get("name",[""])[0]
                if name not in {"output.parquet","output.csv","report.json","audit.html","manifest.json"}:
                    self.reply(400,{"error":"無效檔名"}); return
                with lock:
                    report = state["report"]
                    running = state["running"]
                if not report or running or not report.get("output_directory"):
                    self.reply(409,{"error":"等待工作完成"}); return
                folder = Path(report["output_directory"]).resolve()
                if not folder.is_relative_to(root):
                    self.reply(403,{"error":"路徑不在輸出目錄"}); return
                file = folder / name
                if not file.is_file():
                    self.reply(404,{"error":"檔案尚未生成"}); return
                self.reply(200,file.read_bytes(),"application/octet-stream",name)
            else:
                self.reply(404,{"error":"Not found"})
        def do_POST(self):
            if not self.authorized():
                return
            try:
                self.connection.settimeout(NETWORK_TIMEOUT)
                length = int(self.headers.get("Content-Length","0"))
                require(0 < length <= MAX_BODY_BYTES,"請求過大或為空")
                body = parse_json(self.rfile.read(length))
                require(isinstance(body,dict),"需要 JSON object")
                if self.path == "/api/run":
                    rows = parse_json(body["rows_json"]) if "rows_json" in body else body.get("rows")
                    require(isinstance(rows,list) and 0 < len(rows) <= MAX_ROWS,"需要非空 JSON 陣列")
                    require(isinstance(body.get("resume",False),bool),"resume 必須為 boolean")
                    with lock:
                        if state["running"]:
                            self.reply(409,{"error":"已有工作執行中"}); return
                        state["running"] = True
                        state["cancel"] = threading.Event()
                        state["report"] = new_report("starting")
                        state["worker"] = threading.Thread(target=work,args=(rows,body.get("resume",False)),name="VIA-Job",daemon=False)
                        state["worker"].start()
                    self.reply(202,{"accepted":True})
                elif self.path == "/api/stop":
                    with lock:
                        state["cancel"].set()
                    self.reply(200,{"stopping":True})
                else:
                    self.reply(404,{"error":"Not found"})
            except (ValueError,KeyError,TypeError,TimeoutError) as error:
                self.reply(400,{"error":str(error)})
    server = ThreadingHTTPServer((HOST,port),Handler)
    server.daemon_threads = True
    url = "http://%s:%d" % server.server_address
    print("\n理 | VIA Matrix Governance " + VERSION,flush=True)
    print(url,flush=True)
    print("輸出目錄: " + str(root),flush=True)
    print("Ctrl+C 結束；工作將在目前有界批次結束後關閉。",flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        state["cancel"].set()
        if state["worker"] is not None:
            state["worker"].join()
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path(os.environ.get("LOCALAPPDATA",str(Path.home()))) / "VIA" / "MatrixGovernance" / VERSION)
    parser.add_argument("--port",type=int,default=DEFAULT_PORT)
    parser.add_argument("--no-browser",action="store_true")
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--run",action="store_true")
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--input",type=Path)
    parser.add_argument("--doctor",action="store_true")
    args = parser.parse_args(argv)
    if args.doctor:
        print(json.dumps({"environment":environment_info(),"plan":resource_plan(),"network":NETWORK_REGISTRY,"policy_sha256":digest(POLICY)},ensure_ascii=False,indent=2))
        return 0
    if args.self_test or args.run:
        if args.input and args.input.stat().st_size > MAX_BODY_BYTES:
            parser.error("輸入檔超過大小上限")
        rows = parse_json(args.input.read_bytes()) if args.input else SAMPLE_ROWS
        report = run_pipeline(rows,args.output,resume=args.resume)
        print(json.dumps({"status":report["status"],"cases":len(report["cases"]),"pass":sum(c["status"]=="PASS" for c in report["cases"]),"confusion":report["confusion"],"gate":report["gate"],"output":report["output_directory"]},ensure_ascii=False,indent=2))
        return 0 if report["gate"]["local_reference_pass"] else 1
    serve_ui(args.output,args.port,not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
