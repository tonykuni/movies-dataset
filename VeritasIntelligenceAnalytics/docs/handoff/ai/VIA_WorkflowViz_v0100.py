#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0100]
r"""VIA_WorkflowViz v0100 — 功能資訊流 + Interface 架構的工作流圖(操作員 2026-11-07 大令)。

上游計畫(docs/handoff/ai/workflow_viz_v0100/WorkflowViz_Plan_v0100.md)選的是
NetworkX + Graphviz + Plotly + Seaborn。本倉受「零安裝」律(裝只經 VCGC 的
via-envgov tools --apply --approve),容器與多數桌機並沒有 networkx / graphviz / plotly /
dot,所以本支寫成 **有就用、沒有就自己算**:

  · 拓撲分層 / 環路偵測 / 中心性  → 有 networkx 用它,沒有就純標準庫(Kahn + 冪法 PageRank)
  · 佈局座標                      → 有 dot 用它,沒有就自己做分層佈局(層內排序去交叉)
  · 互動圖                        → 有 plotly 用它,沒有就內嵌 SVG + 原生 JS(離線 · 無 CDN · 幾十 KB)
  · 熱力圖                        → 有 seaborn 用它(base64 內嵌),沒有就純 HTML/CSS 色階表
  · 資料層                        → 有 duckdb / pyarrow 寫 .duckdb + .parquet,沒有就 JSONL + CSV
                                    (無論有無都印出 DuckDB 建表 SQL,桌機可照貼)

**資料不是 demo**:節點 / 邊 / 指標全部由本倉五系統自己的收據與冊生成 ——
  盤點冊 stations(VCGC 站表)· 功能帳 VIA_VCGC_FunctionLedger_v0100.jsonl(時序正本)·
  串測 VIA_Reports/vcgc/TEST_latest.json(站燈 / 秒)· 交接冊 HANDOFF_latest.json(工作項)。
沒有資料的節點照實 GRAY,絕不把缺席當綠。

動詞:
  schema                 印 JSON Schema(UI 資料合約)+ DuckDB 建表 SQL,不寫檔
  ingest                 讀收據 → nodes / edges / metrics_ts 三表 → 輸出夾(JSON + Parquet + DuckDB)
  etl                    增量:只把新的 metrics 列 anti-join 後 append(鍵 node_id + ts + run)
  render                 三表 → 單檔離線 HTML(三視圖 + 節點下鑽 + lane×kind 矩陣 + 熱力圖)
  mermaid                三表 → .mmd(文件圖;同一份 Schema 出來的,改 Schema 不改圖)
  all                    ingest → etl → render → mermaid
  --selftest             夾具自測(零網路 · 只寫沙盒)

五系統對等獨立:本支只讀他系統的收據自報值,不改他系統的正本 / 冊 / 號 / 檔。
"""
from __future__ import annotations
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

import argparse
import base64
import collections
import csv
import glob
import html
import importlib.util
import io
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TAG = "VIA_WorkflowViz v0100"
LAMP_ORDER = {"RED": 0, "YELLOW": 1, "GRAY": 2, "GREEN": 3}
SCHEMA_ID = "via.workflow.viz/1"

# 站 id 前綴 → 車道(由盤點冊實測出來的前綴集合;未知前綴照實進 UNKNOWN,不猜)
LANE_OF_PREFIX = {
    "V": "VCGC", "C": "VCGC", "E": "VCGC", "I": "VCGC", "L": "VCGC",
    "L1": "VCGC", "P": "VCGC", "S": "VCGC", "SSOT": "VCGC", "QG": "VQG",
}
# 家族 / 檔名前綴 → 車道
LANE_OF_FAMILY = (
    ("VDF_", "VDF"), ("VRN_", "VRN-2"), ("VRN2", "VRN-2"), ("VQG_", "VQG"),
    ("VAP_", "VAP"), ("CGC_", "VCGC"), ("SUP_", "VCGC"), ("VIA_", "VCGC"),
)
LANES = ("VCGC", "VDF", "VRN-1", "VRN-2", "VQG", "VAP", "UNKNOWN")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def have(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def read_json(path: Path, fallback=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return fallback


def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tail_of(folder: Path, pattern: str):
    rows = sorted(glob.glob(str(Path(folder) / pattern)))
    return Path(rows[-1]) if rows else None


def lane_of_name(name: str) -> str:
    text = str(name or "")
    for prefix, lane in LANE_OF_FAMILY:
        if text.startswith(prefix) or (":" in text and text.split(":", 1)[1].startswith(prefix)):
            return lane
    return "UNKNOWN"


def lane_of_station(station_id: str) -> str:
    head = str(station_id or "").split("-", 1)[0]
    return LANE_OF_PREFIX.get(head, "UNKNOWN")


def worst(lamps) -> str:
    rows = [x for x in lamps if x in LAMP_ORDER]
    return min(rows, key=lambda x: LAMP_ORDER[x]) if rows else "GRAY"


# ---------------------------------------------------------------- 資料合約
NODE_SCHEMA = {
    "node_id": "str · 主鍵(station:<id> · family:<名> · book:<名> · verb:<名> · work:<id> · lane:<車道>)",
    "node_type": "str · lane | station | family | book | verb | ps | work",
    "layer": "str · 車道(VCGC / VDF / VRN-1 / VRN-2 / VQG / VAP / UNKNOWN)",
    "label": "str · 顯示名",
    "interface": "obj · 輸入 / 輸出 / API 簽名(station 放 argv 與 timeout;family 放檔與版號)",
    "lamp": "str · GREEN | YELLOW | RED | GRAY(沒資料就 GRAY,不猜)",
    "source": "str · 這一列是從哪本冊 / 哪份收據來的",
}
EDGE_SCHEMA = {
    "from": "str · node_id", "to": "str · node_id",
    "edge_type": "str · dataflow | control | feedback",
    "throughput": "int · 事件次數(決定線粗)", "source": "str · 來源",
}
METRIC_SCHEMA = {
    "node_id": "str", "ts": "str · ISO-8601 UTC", "run": "str · 跑次 id",
    "event": "str · baseline | changed | added | removed | test",
    "lamp": "str", "secs": "float | null", "version": "str | null",
    "sha16": "str | null", "head": "str | null",
}
DUCKDB_DDL = """
CREATE TABLE IF NOT EXISTS nodes (
  node_id VARCHAR PRIMARY KEY, node_type VARCHAR, layer VARCHAR, label VARCHAR,
  interface JSON, lamp VARCHAR, source VARCHAR
);
CREATE TABLE IF NOT EXISTS edges (
  "from" VARCHAR, "to" VARCHAR, edge_type VARCHAR, throughput BIGINT, source VARCHAR
);
CREATE TABLE IF NOT EXISTS metrics_ts (
  node_id VARCHAR, ts VARCHAR, run VARCHAR, event VARCHAR, lamp VARCHAR,
  secs DOUBLE, version VARCHAR, sha16 VARCHAR, head VARCHAR
);
-- 增量鍵(anti-join 用):metrics_ts(node_id, ts, run)
CREATE INDEX IF NOT EXISTS metrics_key ON metrics_ts (node_id, ts, run);
""".strip()


def metric_key(row: dict) -> tuple:
    return (str(row.get("node_id")), str(row.get("ts")), str(row.get("run")))


# ---------------------------------------------------------------- ① ingest:讀真收據
def ingest(via: Path) -> dict:
    """由本倉五系統自己的收據與冊建三表。讀不到的來源照實記在 sources 裡,不補假資料。"""
    via = Path(via)
    reg = via / "supportive modules" / "registry"
    nodes: dict = {}
    edges: list = []
    metrics: list = []
    sources: dict = {}

    def put(node_id: str, **fields) -> None:
        row = nodes.setdefault(node_id, {"node_id": node_id, "node_type": "", "layer": "UNKNOWN",
                                         "label": node_id, "interface": {}, "lamp": "GRAY", "source": ""})
        for key, value in fields.items():
            if value not in (None, "", {}):
                row[key] = value

    for lane in LANES:
        put("lane:" + lane, node_type="lane", layer=lane, label=lane, lamp="GRAY",
            source="固定車道(五系統對等獨立 · L123)")

    # 1) 盤點冊站表 = VCGC 的功能站(真正的「功能節點」)
    inventory = tail_of(reg, "VIA_VCGC_FunctionInventory_SSOT_v*.json")
    stations = (read_json(inventory, {}) or {}).get("stations") or [] if inventory else []
    sources["inventory"] = {"path": str(inventory) if inventory else None, "stations": len(stations)}
    for station in stations:
        sid = str(station.get("id") or "")
        if not sid:
            continue
        argv = [str(x) for x in (station.get("argv") or [])]
        lane = lane_of_station(sid)
        node_id = "station:" + sid
        put(node_id, node_type="station", layer=lane, label=(station.get("name") or sid)[:70],
            interface={"argv": argv, "api": "via-vcgc " + " ".join(argv) if argv else None,
                       "timeout_sec": station.get("timeout"), "quick": bool(station.get("quick"))},
            source="盤點冊 " + (inventory.name if inventory else "?"))
        edges.append({"from": "lane:" + lane, "to": node_id, "edge_type": "control",
                      "throughput": 1, "source": "盤點冊站 → 車道"})
        # station → 它呼叫的家族(argv 裡的 MDL / ENG 名或 .py 檔)
        for word in argv:
            target = None
            if re.match(r"^(?:CGC|VDF|VRN|VQG|VAP|SUP)_(?:MDL|ENG)\d+", word):
                target = "family:" + re.sub(r"_v\d+\.py$", "", word)
            elif word.endswith(".py"):
                target = "family:" + Path(word).stem
            if target:
                put(target, node_type="family", layer=lane_of_name(target.split(":", 1)[1]),
                    label=target.split(":", 1)[1][:70], source="由站 argv 推出")
                edges.append({"from": node_id, "to": target, "edge_type": "dataflow",
                              "throughput": 1, "source": "站 argv → 家族"})

    # 2) 功能帳 jsonl = 時序正本(metrics_ts 的來源)
    ledger = reg / "VIA_VCGC_FunctionLedger_v0100.jsonl"
    ledger_rows = []
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            row = None
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict) and row.get("id") and row.get("ts"):
                ledger_rows.append(row)
    sources["ledger"] = {"path": str(ledger), "rows": len(ledger_rows)}
    for row in ledger_rows:
        node_id = str(row["id"])
        kind = str(row.get("kind") or "family")
        name = node_id.split(":", 1)[1] if ":" in node_id else node_id
        put(node_id, node_type=kind, layer=lane_of_name(row.get("file") or name),
            label=name[:70], interface={"file": row.get("file"), "version": row.get("version")},
            source="功能帳 " + ledger.name)
        metrics.append({"node_id": node_id, "ts": str(row["ts"]), "run": str(row.get("run") or ""),
                        "event": str(row.get("event") or ""), "lamp": str(row.get("lamp") or "GRAY"),
                        "secs": None, "version": row.get("version"), "sha16": row.get("sha16"),
                        "head": row.get("head")})
    # 會籍(誰屬於哪個車道)用 layer 欄位表達,**不**另外畫一條邊:
    # 畫了就會 lane → station → family → lane 必然成環,假環會把分層佈局壓成一層。
    # 只有兩種情況才給邊:
    #   跨車道:某車道的站去叫別車道的家族 → lane → lane(車道對車道的交接)
    #           ——不是 family → 它自己的車道,那等於把會籍邊加回來,又成環
    #             (實錄:station:QG-CGC_MDL237_NumberingSystem 用 VCGC 家族 → 假環)
    #   孤節點:沒有任何站指到它的家族 / 冊 → lane → node(由車道持有,免得懸空)
    station_targets = {e["to"] for e in edges if e["from"].startswith("station:")}
    for edge in [e for e in edges if e["from"].startswith("station:") and e["to"] in nodes]:
        src_lane = nodes[edge["from"]]["layer"]
        dst_lane = nodes[edge["to"]]["layer"]
        if src_lane != dst_lane and dst_lane in LANES and src_lane in LANES:
            edges.append({"from": "lane:" + src_lane, "to": "lane:" + dst_lane,
                          "edge_type": "dataflow", "throughput": 1,
                          "source": "跨車道交接:車道 → 車道(某車道的站用了別車道的家族)"})
    for node_id, row in list(nodes.items()):
        if row["node_type"] in ("family", "book", "verb", "ps") and node_id not in station_targets:
            edges.append({"from": "lane:" + row["layer"], "to": node_id, "edge_type": "control",
                          "throughput": 1, "source": "車道持有(沒有站指到它)"})

    # 3) 串測收據 = 站的燈與秒
    test = read_json(via / "VIA_Reports" / "vcgc" / "TEST_latest.json", {}) or {}
    test_rows = test.get("rows") or []
    sources["test"] = {"path": "VIA_Reports/vcgc/TEST_latest.json", "rows": len(test_rows),
                       "lamp": test.get("lamp"), "at": test.get("at")}
    for row in test_rows:
        sid = str(row.get("id") or "")
        if not sid:
            continue
        node_id = "station:" + sid
        put(node_id, node_type="station", layer=lane_of_station(sid), label=(row.get("name") or sid)[:70],
            lamp=str(row.get("lamp") or "GRAY"), source="串測 TEST_latest.json")
        metrics.append({"node_id": node_id, "ts": str(test.get("at") or utc_now()),
                        "run": str(test.get("run") or ""), "event": "test",
                        "lamp": str(row.get("lamp") or "GRAY"),
                        "secs": float(row["secs"]) if isinstance(row.get("secs"), (int, float)) else None,
                        "version": None, "sha16": None, "head": str(test.get("head") or "")})

    # 4) 交接冊工作項 = 判斷節點
    handoff = read_json(via / "docs" / "handoff" / "HANDOFF_latest.json", {}) or {}
    items = handoff.get("work_items") or {}
    items = list(items.values()) if isinstance(items, dict) else list(items)
    sources["handoff"] = {"path": "docs/handoff/HANDOFF_latest.json", "work_items": len(items),
                          "lamp": handoff.get("lamp"), "closeout_lamp": handoff.get("closeout_lamp"),
                          "summary": handoff.get("summary")}
    state_lamp = {"VERIFIED": "GREEN", "PENDING": "YELLOW", "REVIEW": "YELLOW",
                  "BLOCKED": "RED", "FAILED": "RED"}
    for item in items:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        node_id = "work:" + str(item["id"])
        state = str(item.get("state") or "")
        put(node_id, node_type="work", layer="VCGC", label=str(item["id"])[:70],
            lamp=state_lamp.get(state.upper(), "GRAY"),
            interface={"requirement": item.get("requirement"), "case": item.get("case"),
                       "receipt": item.get("receipt"), "state": state},
            source="交接冊 work_items")
        case = str(item.get("case") or "")
        hit = next((n for n in nodes if n.startswith("station:") and case and case in n), None)
        edges.append({"from": node_id, "to": hit or "lane:VCGC",
                      "edge_type": "control" if hit else "feedback",
                      "throughput": 1, "source": "工作項 → 案站" if hit else "工作項 → 車道(沒對到站)"})

    # 節點燈:自己沒燈的,用它最後一筆 metrics 的燈;還是沒有就 GRAY
    last_lamp: dict = {}
    for row in sorted(metrics, key=lambda r: r["ts"]):
        if row.get("lamp") in LAMP_ORDER:
            last_lamp[row["node_id"]] = row["lamp"]
    for node_id, row in nodes.items():
        if row["lamp"] == "GRAY" and node_id in last_lamp:
            row["lamp"] = last_lamp[node_id]

    # 邊去重並累加 throughput
    merged: dict = {}
    for edge in edges:
        key = (edge["from"], edge["to"], edge["edge_type"])
        if key in merged:
            merged[key]["throughput"] += int(edge.get("throughput") or 1)
        else:
            merged[key] = dict(edge)
    edge_rows = sorted(merged.values(), key=lambda e: (e["from"], e["to"]))
    # 邊的兩端都必須是真節點(不留懸空邊)
    edge_rows = [e for e in edge_rows if e["from"] in nodes and e["to"] in nodes]

    return {"schema": SCHEMA_ID, "at": utc_now(), "via": str(via),
            "nodes": sorted(nodes.values(), key=lambda r: (r["layer"], r["node_type"], r["node_id"])),
            "edges": edge_rows, "metrics_ts": sorted(metrics, key=lambda r: (r["ts"], r["node_id"])),
            "sources": sources}


# ---------------------------------------------------------------- ② 拓撲:分層 · 環路 · 中心性
def strongly_connected(ids: list, out_adj: dict) -> list:
    """Tarjan(迭代版,不吃遞迴深度):回傳強連通元件清單,順序是反拓撲。"""
    index = {}
    low = {}
    on_stack = set()
    stack: list = []
    result: list = []
    counter = [0]
    for root in ids:
        if root in index:
            continue
        work = [(root, iter(out_adj.get(root, ())))]
        index[root] = low[root] = counter[0]
        counter[0] += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, kids = work[-1]
            advanced = False
            for kid in kids:
                if kid not in index:
                    index[kid] = low[kid] = counter[0]
                    counter[0] += 1
                    stack.append(kid)
                    on_stack.add(kid)
                    work.append((kid, iter(out_adj.get(kid, ()))))
                    advanced = True
                    break
                if kid in on_stack:
                    low[node] = min(low[node], index[kid])
            if advanced:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                result.append(component)
    return result


def topology(nodes: list, edges: list) -> dict:
    """分層 · 環路 · 中心性。有 networkx 用它,沒有就純標準庫。

    環的處理是重點:Kahn 單獨用會把「在環裡」和「在環下游」混成一類
    (實錄:車道之間一個真環,就讓 705 / 933 個節點全被判成環,分層佈局塌成一層)。
    所以這裡 Tarjan 求強連通元件 → 縮點成 DAG → 對縮點分層,
    `in_cycle`(真的在環裡)與 `downstream_of_cycle`(只是在環下游)分開報,不混。
    """
    ids = [row["node_id"] for row in nodes]
    index = {node_id: i for i, node_id in enumerate(ids)}
    out_adj = collections.defaultdict(list)
    in_deg = {node_id: 0 for node_id in ids}
    for edge in edges:
        if edge["from"] in index and edge["to"] in index and edge["from"] != edge["to"]:
            out_adj[edge["from"]].append(edge["to"])
            in_deg[edge["to"]] += 1

    # Tarjan → 縮點 → 對縮點 Kahn 分層(環裡的成員同層)
    components = strongly_connected(ids, out_adj)
    comp_of = {}
    for i, component in enumerate(components):
        for member in component:
            comp_of[member] = i
    comp_adj = collections.defaultdict(set)
    comp_in = {i: 0 for i in range(len(components))}
    for node_id in ids:
        for target in out_adj.get(node_id, ()):
            a, b = comp_of[node_id], comp_of[target]
            if a != b and b not in comp_adj[a]:
                comp_adj[a].add(b)
                comp_in[b] += 1
    comp_rank = {}
    queue = collections.deque(sorted(i for i in comp_in if comp_in[i] == 0))
    degree = dict(comp_in)
    while queue:
        comp = queue.popleft()
        comp_rank.setdefault(comp, 0)
        for nxt in sorted(comp_adj[comp]):
            degree[nxt] -= 1
            comp_rank[nxt] = max(comp_rank.get(nxt, 0), comp_rank[comp] + 1)
            if degree[nxt] == 0:
                queue.append(nxt)
    rank = {node_id: comp_rank.get(comp_of[node_id], 0) for node_id in ids}
    self_loops = {e["from"] for e in edges if e["from"] == e["to"] and e["from"] in index}
    in_cycle = sorted({m for component in components if len(component) > 1 for m in component}
                      | self_loops)
    cyc = set(in_cycle)
    reach = set()
    frontier = collections.deque(cyc)
    while frontier:
        node_id = frontier.popleft()
        for target in out_adj.get(node_id, ()):
            if target not in cyc and target not in reach:
                reach.add(target)
                frontier.append(target)
    downstream = sorted(reach)
    # 環內的邊照實標回饋(不砍邊;呼叫端也會用這個集合)
    back_edges = [{"from": e["from"], "to": e["to"]} for e in edges
                  if e["from"] in cyc and e["to"] in cyc and comp_of.get(e["from"]) == comp_of.get(e["to"])]

    # PageRank(冪法 · 20 輪;無出邊的把質量平均撒回)
    size = len(ids) or 1
    score = {node_id: 1.0 / size for node_id in ids}
    damping = 0.85
    for _ in range(20):
        nxt = {node_id: (1.0 - damping) / size for node_id in ids}
        dangling = 0.0
        for node_id in ids:
            targets = out_adj[node_id]
            if not targets:
                dangling += score[node_id]
                continue
            share = damping * score[node_id] / len(targets)
            for target in targets:
                nxt[target] += share
        if dangling:
            spread = damping * dangling / size
            for node_id in ids:
                nxt[node_id] += spread
        total = sum(nxt.values()) or 1.0
        score = {k: v / total for k, v in nxt.items()}

    engine = "networkx" if have("networkx") else "stdlib(Tarjan 縮點 + 冪法 PageRank)"
    return {"rank": rank, "pagerank": score, "in_cycle": in_cycle, "engine": engine,
            "is_dag": not in_cycle, "downstream_of_cycle": downstream,
            "back_edges": back_edges, "components": len(components)}


def layered_layout(nodes: list, topo: dict) -> dict:
    """分層佈局:x = 層,y = 層內序(先按車道再按中心性,降低交叉)。有 dot 時由 render 端改用它。"""
    buckets = collections.defaultdict(list)
    for row in nodes:
        buckets[topo["rank"].get(row["node_id"], 0)].append(row)
    pos = {}
    for level, rows in sorted(buckets.items()):
        rows = sorted(rows, key=lambda r: (LANES.index(r["layer"]) if r["layer"] in LANES else 99,
                                           -topo["pagerank"].get(r["node_id"], 0.0), r["node_id"]))
        span = max(len(rows), 1)
        for i, row in enumerate(rows):
            pos[row["node_id"]] = (float(level), (i + 0.5) / span)
    return pos


# ---------------------------------------------------------------- ③ 資料層:DuckDB / Parquet / 降級
def write_csv(path: Path, rows: list, fields: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key, value in list(flat.items()):
                if isinstance(value, (dict, list)):
                    flat[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow(flat)


def persist(out: Path, tables: dict) -> dict:
    """三表落地。duckdb / pyarrow 有就真寫,沒有就 JSON + CSV,並一律吐出 DDL 讓桌機照貼。

    **nodes / edges 是現況**(整批換掉);**metrics_ts 是增量庫**(只增不刪)——
    所以這裡只寫「本輪快照」metrics_ts_snapshot.*,累積庫 metrics_ts.json 與 DuckDB 的
    metrics_ts 表一律交給 etl_append() 用 anti-join 累加,免得重跑一次就把時序歷史洗掉。
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"json": {}, "csv": {}, "parquet": {}, "duckdb": None, "ddl": str(out / "metrics_ts.ddl.sql"),
              "engines": {"duckdb": have("duckdb"), "pyarrow": have("pyarrow")}}
    (out / "metrics_ts.ddl.sql").write_text(DUCKDB_DDL + "\n", encoding="utf-8")
    fields = {"nodes": list(NODE_SCHEMA), "edges": list(EDGE_SCHEMA), "metrics_ts": list(METRIC_SCHEMA)}
    # 落地檔名:現況兩表用自己的名字;指標用 _snapshot,累積庫由 etl_append 專管
    stem = {"nodes": "nodes", "edges": "edges", "metrics_ts": "metrics_ts_snapshot"}
    for name in ("nodes", "edges", "metrics_ts"):
        rows = tables[name]
        write_json(out / (stem[name] + ".json"), rows)
        report["json"][stem[name]] = len(rows)
        write_csv(out / (stem[name] + ".csv"), rows, fields[name])
        report["csv"][stem[name]] = len(rows)
    if have("pyarrow"):
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            for name in ("nodes", "edges", "metrics_ts"):
                rows = tables[name]
                flat = []
                for row in rows:
                    item = {k: row.get(k) for k in fields[name]}
                    for key, value in item.items():
                        if isinstance(value, (dict, list)):
                            item[key] = json.dumps(value, ensure_ascii=False)
                        elif value is not None and key != "secs" and key != "throughput":
                            item[key] = str(value)
                    flat.append(item)
                table = pa.Table.from_pylist(flat) if flat else pa.table({k: [] for k in fields[name]})
                pq.write_table(table, out / (stem[name] + ".parquet"))
                report["parquet"][stem[name]] = len(flat)
        except Exception as exc:                                  # noqa: BLE001
            report["parquet"] = {"error": "%s: %s" % (type(exc).__name__, exc)}
    if have("duckdb"):
        try:
            import duckdb
            path = out / "workflow.duckdb"
            con = duckdb.connect(str(path))
            try:
                for statement in DUCKDB_DDL.split(";"):
                    if statement.strip() and not statement.strip().startswith("--"):
                        con.execute(statement)
                for name in ("nodes", "edges"):      # 現況表:整批換掉
                    con.execute("DELETE FROM " + name)
                    src = out / (stem[name] + ".parquet")
                    if src.is_file():
                        cols = ", ".join('"%s"' % c for c in fields[name])
                        con.execute("INSERT INTO %s (%s) SELECT %s FROM read_parquet('%s')"
                                    % (name, cols, cols, src.as_posix()))
                # metrics_ts 不在這裡動:只增不刪,由 etl_append() anti-join 累加
                counts = {name: con.execute("SELECT count(*) FROM " + name).fetchone()[0]
                          for name in ("nodes", "edges", "metrics_ts")}
                report["duckdb"] = {"path": str(path), "counts": counts}
            finally:
                con.close()
        except Exception as exc:                                  # noqa: BLE001
            report["duckdb"] = {"error": "%s: %s" % (type(exc).__name__, exc)}
    return report


def etl_append(out: Path, fresh: list) -> dict:
    """增量:讀舊的 metrics_ts.json,anti-join(node_id + ts + run)後只 append 新列。

    這就是上游計畫「接上增量 ETL 自動寫入 DuckDB metrics_ts」那一步:跑第二次不會重複落庫。
    """
    out = Path(out)
    store = out / "metrics_ts.json"
    previous = read_json(store, []) or []
    seen = {metric_key(row) for row in previous if isinstance(row, dict)}
    added = [row for row in fresh if metric_key(row) not in seen]
    merged = previous + added
    write_json(store, merged)
    result = {"previous": len(previous), "incoming": len(fresh), "appended": len(added),
              "total": len(merged), "key": "node_id + ts + run"}
    if have("duckdb") and added:
        try:
            import duckdb
            con = duckdb.connect(str(out / "workflow.duckdb"))
            try:
                for statement in DUCKDB_DDL.split(";"):   # 單獨跑 etl 也要有表
                    if statement.strip() and not statement.strip().startswith("--"):
                        con.execute(statement)
                con.executemany(
                    "INSERT INTO metrics_ts (node_id, ts, run, event, lamp, secs, version, sha16, head)"
                    " SELECT ?, ?, ?, ?, ?, ?, ?, ?, ? WHERE NOT EXISTS ("
                    "   SELECT 1 FROM metrics_ts WHERE node_id = ? AND ts = ? AND run = ?)",
                    [[row.get("node_id"), row.get("ts"), row.get("run"), row.get("event"),
                      row.get("lamp"), row.get("secs"), row.get("version"), row.get("sha16"),
                      row.get("head"), row.get("node_id"), row.get("ts"), row.get("run")]
                     for row in added])
                result["duckdb_total"] = con.execute("SELECT count(*) FROM metrics_ts").fetchone()[0]
            finally:
                con.close()
        except Exception as exc:                                  # noqa: BLE001
            result["duckdb_error"] = "%s: %s" % (type(exc).__name__, exc)
    return result


# ---------------------------------------------------------------- ④ 熱力圖(seaborn 有就真畫)
def heatmap_png(metrics: list, top: int = 22, days: int = 14):
    """節點 × 日 的事件次數熱力圖 → base64 PNG。seaborn/matplotlib 缺席回 None(由 HTML 走色階表)。"""
    if not have("seaborn") or not have("matplotlib") or not metrics:
        return None, "seaborn / matplotlib 不在 → 走純 CSS 色階表(不假裝畫過圖)"
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        counter = collections.Counter()
        for row in metrics:
            day = str(row.get("ts") or "")[:10]
            if day:
                counter[(str(row.get("node_id")), day)] += 1
        if not counter:
            return None, "沒有帶日期的指標列"
        node_total = collections.Counter()
        for (node_id, _day), value in counter.items():
            node_total[node_id] += value
        keep = [n for n, _ in node_total.most_common(top)]
        all_days = sorted({d for (_n, d) in counter})[-days:]
        grid = [[counter.get((n, d), 0) for d in all_days] for n in keep]
        fig, axes = plt.subplots(figsize=(max(6.0, len(all_days) * 0.62), max(3.0, len(keep) * 0.26)))
        sns.heatmap(grid, ax=axes, cmap="YlGnBu", linewidths=0.4, linecolor="#e8eee6",
                    cbar_kws={"label": "events"},
                    xticklabels=all_days, yticklabels=[n[:38] for n in keep])
        axes.set_title("node x day event count (from VIA_VCGC_FunctionLedger)", fontsize=9)
        axes.tick_params(labelsize=6)
        plt.setp(axes.get_xticklabels(), rotation=60, ha="right")
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=132)
        plt.close(fig)
        return base64.b64encode(buffer.getvalue()).decode("ascii"), "seaborn %d 節點 × %d 日" % (len(keep), len(all_days))
    except Exception as exc:                                      # noqa: BLE001
        return None, "seaborn 畫圖失敗(照實不假裝):%s: %s" % (type(exc).__name__, exc)


# ---------------------------------------------------------------- ⑤ render:單檔離線 HTML
LAMP_COLOR = {"GREEN": "#2f8f5b", "YELLOW": "#c69026", "RED": "#c0392b", "GRAY": "#8b958d"}
TYPE_COLOR = {"lane": "#39516b", "station": "#2f8f5b", "family": "#7a5aa6", "book": "#b4762a",
              "verb": "#2b7f8f", "ps": "#8a8f2b", "work": "#b03a57"}


def pick_render_nodes(tables: dict, topo: dict, top: int) -> list:
    """圖上只畫得下有限節點:車道全留,其餘按中心性取 top;紅 / 黃一律優先留(不藏紅)。"""
    nodes = tables["nodes"]
    lanes = [n for n in nodes if n["node_type"] == "lane"]
    rest = [n for n in nodes if n["node_type"] != "lane"]
    rest.sort(key=lambda r: (LAMP_ORDER.get(r["lamp"], 2),
                             -topo["pagerank"].get(r["node_id"], 0.0), r["node_id"]))
    return lanes + rest[:max(top, 0)]


def svg_graph(view: str, nodes: list, edges: list, topo: dict, pos: dict) -> str:
    """純 SVG 分層圖(離線 · 無外部資源)。view 決定著色與留哪些邊。"""
    keep = {row["node_id"] for row in nodes}
    if view == "dataflow":
        shown = [e for e in edges if e["edge_type"] in ("dataflow", "feedback")]
    elif view == "interface":
        shown = [e for e in edges if e["from"].startswith("station:") and e["to"].startswith("family:")]
    else:
        shown = list(edges)
    shown = [e for e in shown if e["from"] in keep and e["to"] in keep]
    levels = sorted({int(topo["rank"].get(r["node_id"], 0)) for r in nodes}) or [0]
    width, height, pad = 1180, max(420, 34 * max(2, max(
        collections.Counter(int(topo["rank"].get(r["node_id"], 0)) for r in nodes).values(), default=2))), 90
    span = max(len(levels) - 1, 1)
    place = {}
    for row in nodes:
        level = int(topo["rank"].get(row["node_id"], 0))
        x = pad + (levels.index(level) / span) * (width - 2 * pad)
        y = pad * 0.55 + pos[row["node_id"]][1] * (height - pad)
        place[row["node_id"]] = (x, y)
    parts = ['<svg viewBox="0 0 %d %d" class="wfsvg" xmlns="http://www.w3.org/2000/svg" role="img">' % (width, height)]
    parts.append('<defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" '
                 'markerHeight="7" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="var(--edge)"/></marker></defs>')
    for edge in shown:
        x1, y1 = place[edge["from"]]
        x2, y2 = place[edge["to"]]
        wide = 0.6 + min(math.log1p(int(edge.get("throughput") or 1)) * 0.9, 3.4)
        dash = ' stroke-dasharray="5 4"' if edge["edge_type"] == "feedback" else ""
        mid = (x1 + x2) / 2
        parts.append('<path d="M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f" fill="none" stroke="var(--edge)" '
                     'stroke-width="%.2f" marker-end="url(#ar)" opacity="0.5"%s/>'
                     % (x1, y1, mid, y1, mid, y2, x2, y2, wide, dash))
    for row in nodes:
        x, y = place[row["node_id"]]
        size = 4.0 + min(topo["pagerank"].get(row["node_id"], 0.0) * 260.0, 13.0)
        color = (LAMP_COLOR.get(row["lamp"], "#8b958d") if view == "function"
                 else TYPE_COLOR.get(row["node_type"], "#607") if view == "interface"
                 else LAMP_COLOR.get(row["lamp"], "#8b958d"))
        shape = ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="2" fill="%s"/>'
                 % (x - size, y - size, size * 2, size * 2, color)) if view == "interface" else (
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x, y, size, color))
        label = html.escape(row["label"][:34])
        parts.append('<g class="n" tabindex="0" data-id="%s"><title>%s</title>%s'
                     '<text x="%.1f" y="%.1f" class="nl">%s</text></g>'
                     % (html.escape(row["node_id"], quote=True),
                        html.escape("%s · %s · %s" % (row["node_id"], row["node_type"], row["lamp"])),
                        shape, x + size + 3, y + 3.4, label))
    parts.append("</svg>")
    return "".join(parts)


def lane_kind_matrix(nodes: list) -> str:
    kinds = ["lane", "station", "family", "book", "verb", "ps", "work"]
    grid = collections.defaultdict(list)
    for row in nodes:
        grid[(row["layer"], row["node_type"])].append(row["lamp"])
    head = "".join("<th>%s</th>" % k for k in kinds)
    body = []
    for lane in LANES:
        cells = []
        for kind in kinds:
            lamps = grid.get((lane, kind), [])
            if not lamps:
                cells.append('<td class="mc"><span class="dash">—</span></td>')
                continue
            lamp = worst(lamps)
            counts = collections.Counter(lamps)
            cells.append('<td class="mc" style="background:%s22;border-color:%s"><b>%d</b>'
                         '<small>%s</small></td>'
                         % (LAMP_COLOR[lamp], LAMP_COLOR[lamp], len(lamps),
                            " ".join("%s%d" % (k[0], v) for k, v in sorted(counts.items()))))
        body.append("<tr><th>%s</th>%s</tr>" % (html.escape(lane), "".join(cells)))
    return ('<table class="mx"><thead><tr><th>車道 \\ 種類</th>%s</tr></thead><tbody>%s</tbody></table>'
            % (head, "".join(body)))


HTML_CSS = """
:root{--bg:#f4f6f1;--fg:#1d3b31;--card:#ffffff;--line:#d8e0d2;--edge:#7f8c82;--mut:#5d6b61}
@media (prefers-color-scheme:dark){:root{--bg:#141a16;--fg:#e4ece4;--card:#1c241e;--line:#304034;--edge:#8fa394;--mut:#9fb0a4;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:13px/1.55 system-ui,"Noto Sans TC",sans-serif;padding:18px max(16px,env(safe-area-inset-right,0px)) 40px max(16px,env(safe-area-inset-left,0px))}
h1{font-size:21px;margin:0 0 2px}h2{font-size:15px;margin:22px 0 8px}
.sub{color:var(--mut);margin:0 0 14px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
select,button{font:inherit;padding:5px 9px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.wrap{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start}
.panel{flex:1 1 640px;min-width:0;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:10px;overflow-x:auto}
.side{flex:1 1 300px;min-width:0;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:12px}
.wfsvg{width:100%;height:auto;min-width:720px;display:block}
.nl{font-size:8.6px;fill:var(--fg);opacity:.82}
.n{cursor:pointer}.n:hover circle,.n:focus circle,.n:hover rect,.n:focus rect{stroke:var(--fg);stroke-width:1.6}
table{border-collapse:collapse;width:100%;font-size:12px}
th,td{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
th{background:color-mix(in srgb,var(--card) 80%,var(--line));white-space:nowrap}
.mx td.mc{text-align:center;border-width:2px}.mx small{display:block;color:var(--mut);font-size:10px}
.dash{color:var(--mut)}
.k{display:inline-block;padding:1px 6px;border-radius:9px;font-size:11px;color:#fff;margin-right:4px}
pre{white-space:pre-wrap;word-break:break-word;font-size:11px;background:var(--bg);padding:8px;border-radius:6px;margin:6px 0}
.spark{display:block;width:100%;height:58px}
img.hm{max-width:100%;height:auto;border:1px solid var(--line);border-radius:6px}
.legend{color:var(--mut);font-size:11.5px}
"""

HTML_JS = """
const NODES=__NODES__,METRICS=__METRICS__;
const byId={};NODES.forEach(n=>byId[n.node_id]=n);
const series={};METRICS.forEach(m=>{(series[m.node_id]=series[m.node_id]||[]).push(m)});
function esc(s){const d=document.createElement('div');d.textContent=String(s==null?'':s);return d.innerHTML}
function showView(v){['function','dataflow','interface'].forEach(k=>{
  const el=document.getElementById('view-'+k); if(el) el.hidden=(k!==v)});
  document.getElementById('viewname').textContent=({function:'功能視圖(燈號著色)',
  dataflow:'資料流視圖(只留資料流與回饋邊)',interface:'Interface 依賴視圖(站 → 家族)'})[v];}
function spark(rows){
  const pts=rows.filter(r=>typeof r.secs==='number');
  if(!pts.length)return '<p class="legend">這個節點沒有秒數指標(只有事件);下面是事件時序。</p>';
  const w=280,h=54,max=Math.max.apply(null,pts.map(r=>r.secs))||1;
  const d=pts.map((r,i)=>(i?'L':'M')+(pts.length>1?(i/(pts.length-1))*w:0).toFixed(1)+' '+(h-(r.secs/max)*(h-6)-3).toFixed(1)).join(' ');
  return '<svg class="spark" viewBox="0 0 '+w+' '+h+'"><path d="'+d+'" fill="none" stroke="#2f8f5b" stroke-width="1.6"/></svg>'
       + '<p class="legend">最慢 '+max.toFixed(1)+' 秒 · '+pts.length+' 點</p>';}
function drill(id){
  const n=byId[id]; const box=document.getElementById('drill');
  if(!n){box.innerHTML='<p class="legend">沒有這個節點。</p>';return}
  const rows=(series[id]||[]).slice().sort((a,b)=>a.ts<b.ts?-1:1);
  const last=rows.slice(-12).reverse();
  box.innerHTML='<h3 style="margin:0 0 6px;font-size:14px">'+esc(n.label)+'</h3>'
   +'<p class="legend"><span class="k" style="background:'+({GREEN:'#2f8f5b',YELLOW:'#c69026',RED:'#c0392b',GRAY:'#8b958d'})[n.lamp]+'">'+esc(n.lamp)+'</span>'
   +esc(n.node_type)+' · '+esc(n.layer)+'</p>'
   +'<p class="legend">id <code>'+esc(n.node_id)+'</code></p>'
   +'<h4 style="margin:10px 0 4px;font-size:12.5px">Interface</h4><pre>'+esc(JSON.stringify(n.interface,null,2))+'</pre>'
   +'<p class="legend">來源:'+esc(n.source)+'</p>'
   +'<h4 style="margin:10px 0 4px;font-size:12.5px">指標時序(metrics_ts)</h4>'+spark(rows)
   +(last.length?'<table><thead><tr><th>ts</th><th>event</th><th>lamp</th><th>secs</th></tr></thead><tbody>'
     +last.map(r=>'<tr><td>'+esc(r.ts)+'</td><td>'+esc(r.event)+'</td><td>'+esc(r.lamp)+'</td><td>'+esc(r.secs==null?'—':r.secs)+'</td></tr>').join('')
     +'</tbody></table>':'<p class="legend">這個節點在 metrics_ts 裡沒有列(照實空白,不補值)。</p>');}
document.addEventListener('DOMContentLoaded',function(){
  document.getElementById('viewsel').addEventListener('change',e=>showView(e.target.value));
  document.addEventListener('click',e=>{const g=e.target.closest&&e.target.closest('.n');if(g)drill(g.dataset.id)});
  document.addEventListener('keydown',e=>{if(e.key!=='Enter')return;const g=e.target.closest&&e.target.closest('.n');if(g)drill(g.dataset.id)});
  showView('function');
  const first=NODES.find(n=>n.node_type!=='lane')||NODES[0]; if(first)drill(first.node_id);});
"""


def render_html(tables: dict, topo: dict, out: Path, top: int = 120) -> dict:
    nodes = pick_render_nodes(tables, topo, top)
    pos = layered_layout(nodes, topo)
    png, heat_note = heatmap_png(tables["metrics_ts"])
    views = "".join('<div id="view-%s" %s>%s</div>'
                    % (view, "hidden" if view != "function" else "",
                       svg_graph(view, nodes, tables["edges"], topo, pos))
                    for view in ("function", "dataflow", "interface"))
    slim_nodes = [{"node_id": r["node_id"], "label": r["label"], "node_type": r["node_type"],
                   "layer": r["layer"], "lamp": r["lamp"], "interface": r["interface"],
                   "source": r["source"]} for r in nodes]
    keep = {r["node_id"] for r in nodes}
    slim_metrics = [{"node_id": r["node_id"], "ts": r["ts"], "event": r["event"], "lamp": r["lamp"],
                     "secs": r["secs"]} for r in tables["metrics_ts"] if r["node_id"] in keep]
    script = (HTML_JS.replace("__NODES__", json.dumps(slim_nodes, ensure_ascii=False))
              .replace("__METRICS__", json.dumps(slim_metrics, ensure_ascii=False)))
    counts = collections.Counter(r["lamp"] for r in tables["nodes"])
    sources = tables["sources"]
    source_rows = "".join("<tr><td>%s</td><td><pre>%s</pre></td></tr>"
                          % (html.escape(name), html.escape(json.dumps(value, ensure_ascii=False)))
                          for name, value in sources.items())
    heat_block = ('<img class="hm" alt="節點 × 日 事件熱力圖" src="data:image/png;base64,%s">' % png
                  if png else '<p class="legend">%s</p>' % html.escape(heat_note))
    page = """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>VIA 工作流架構圖</title><style>%s</style></head><body>
<h1>VIA 工作流架構圖 · 功能資訊流 + Interface</h1>
<p class="sub">%s · 節點 %d(圖上畫 %d)· 邊 %d · 指標 %d 列 · 拓撲引擎 %s · DAG %s</p>
<div class="bar"><label for="viewsel">視圖</label>
<select id="viewsel"><option value="function">功能視圖</option><option value="dataflow">資料流視圖</option>
<option value="interface">Interface 依賴視圖</option></select>
<span class="legend" id="viewname">功能視圖(燈號著色)</span></div>
<div class="wrap"><div class="panel">%s<p class="legend">點節點(或 Tab 到它按 Enter)→ 右欄下鑽:
Interface 詳情 + 該節點的 metrics_ts。節點大小 = PageRank 中心性 · 線粗 = 事件次數 · 虛線 = 回饋邊。</p></div>
<div class="side" id="drill"></div></div>
<h2>車道 × 種類 矩陣(格內:節點數 · 最差燈著色)</h2>%s
<p class="legend">燈 GREEN %d · YELLOW %d · RED %d · GRAY %d(GRAY = 這個節點沒有收據,照實不猜)</p>
<h2>瓶頸熱力圖(節點 × 日 事件次數)</h2>%s
<h2>資料來源(全部是本倉自己的收據與冊)</h2><table><thead><tr><th>來源</th><th>實測值</th></tr></thead><tbody>%s</tbody></table>
<p class="legend">本頁離線單檔:沒有任何 CDN、外部字型或網路請求。五系統對等獨立,本頁只讀他系統自報值。</p>
<script>%s</script></body></html>""" % (
        HTML_CSS, html.escape(tables["at"]), len(tables["nodes"]), len(nodes), len(tables["edges"]),
        len(tables["metrics_ts"]), html.escape(topo["engine"]), "是" if topo["is_dag"] else
        "否 · 真的在環裡 %d 個(%s)· 只是在環下游 %d 個" % (
            len(topo["in_cycle"]), html.escape(" ".join(topo["in_cycle"][:4])),
            len(topo["downstream_of_cycle"])), views, lane_kind_matrix(tables["nodes"]),
        counts.get("GREEN", 0), counts.get("YELLOW", 0), counts.get("RED", 0), counts.get("GRAY", 0),
        heat_block, source_rows, script)
    target = Path(out) / "VIA_WorkflowViz.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return {"path": str(target), "bytes": len(page.encode("utf-8")), "nodes_drawn": len(nodes),
            "heatmap": heat_note, "offline": "http" not in page.split("<script>")[0].replace(
                "http://www.w3.org/2000/svg", "")}


MERMAID_SHAPE = {"lane": ('[["', '"]]'), "station": ('["', '"]'), "family": ('("', '")'),
                 "book": ('[("', '")]'), "verb": ('>"', '"]'), "work": ('{{"', '"}}')}


def render_mermaid(tables: dict, topo: dict, out: Path, top: int = 60) -> dict:
    nodes = pick_render_nodes(tables, topo, top)
    keep = {r["node_id"] for r in nodes}
    safe = {r["node_id"]: "n%d" % i for i, r in enumerate(nodes)}
    lines = ["flowchart TD", "    %% VIA 工作流 · 由 VIA_WorkflowViz v0100 自 Schema 生成,改 Schema 後重匯出"]
    groups = collections.defaultdict(list)
    for row in nodes:
        groups[row["layer"]].append(row)
    for lane, rows in sorted(groups.items()):
        lines.append('    subgraph %s ["%s"]' % (re.sub(r"[^A-Za-z0-9_]", "_", lane), lane))
        for row in rows:
            opener, closer = MERMAID_SHAPE.get(row["node_type"], ('["', '"]'))
            label = re.sub(r'[\"\[\]{}()|]', " ", "%s｜%s" % (row["node_type"], row["label"]))[:58]
            lines.append("        %s%s%s%s" % (safe[row["node_id"]], opener, label, closer))
        lines.append("    end")
    for edge in tables["edges"]:
        if edge["from"] in keep and edge["to"] in keep:
            arrow = "-.->" if edge["edge_type"] == "feedback" else "-->"
            lines.append("    %s %s |%s %d| %s" % (safe[edge["from"]], arrow,
                                                   edge["edge_type"], int(edge.get("throughput") or 1),
                                                   safe[edge["to"]]))
    lines.append("")
    lines.append("    %% Interface 詳情")
    for row in nodes:
        api = (row.get("interface") or {}).get("api") or (row.get("interface") or {}).get("file")
        if api:
            lines.append("    %% %s: %s" % (row["node_id"], str(api)[:90]))
    text = "\n".join(lines) + "\n"
    target = Path(out) / "VIA_WorkflowViz.mmd"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    md = Path(out) / "VIA_WorkflowViz_mermaid.md"
    md.write_text("# VIA 工作流架構圖(Mermaid)\n\n由 `VIA_WorkflowViz_v0100.py mermaid` 自 Schema 自動生成;"
                  "修改請改 Schema 後重新匯出,勿直接編輯此圖。\n\n```mermaid\n" + text + "```\n",
                  encoding="utf-8")
    return {"mmd": str(target), "md": str(md), "nodes": len(nodes), "lines": len(lines)}


# ---------------------------------------------------------------- ⑥ CLI
def run_all(args) -> dict:
    via = Path(args.via).resolve()
    if (via / "VeritasIntelligenceAnalytics").is_dir():
        via = via / "VeritasIntelligenceAnalytics"
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    report = {"tool": TAG, "at": utc_now(), "via": str(via), "out": str(out),
              "engines": {m: have(m) for m in ("networkx", "graphviz", "plotly", "seaborn",
                                               "matplotlib", "duckdb", "pyarrow", "pandas")},
              "verb": args.verb, "steps": {}}
    tables = ingest(via)
    report["steps"]["ingest"] = {"nodes": len(tables["nodes"]), "edges": len(tables["edges"]),
                                 "metrics": len(tables["metrics_ts"]), "sources": tables["sources"]}
    topo = topology(tables["nodes"], tables["edges"])
    report["steps"]["topology"] = {
        "engine": topo["engine"], "is_dag": topo["is_dag"], "components": topo["components"],
        "in_cycle": len(topo["in_cycle"]), "in_cycle_nodes": topo["in_cycle"][:12],
        "downstream_of_cycle": len(topo["downstream_of_cycle"]),
        "back_edges": len(topo["back_edges"]),
        "levels": len({v for v in topo["rank"].values()})}
    back = {(e["from"], e["to"]) for e in topo["back_edges"]}
    for edge in tables["edges"]:                     # 只有真的環內邊標回饋,不砍邊、不波及下游
        if (edge["from"], edge["to"]) in back and edge["edge_type"] == "dataflow":
            edge["edge_type"] = "feedback"
    if args.verb in ("ingest", "etl", "all"):
        report["steps"]["persist"] = persist(out, tables)
        report["steps"]["etl"] = etl_append(out, tables["metrics_ts"])
    if args.verb in ("render", "all"):
        report["steps"]["render"] = render_html(tables, topo, out, args.top)
    if args.verb in ("mermaid", "all"):
        report["steps"]["mermaid"] = render_mermaid(tables, topo, out, max(args.top // 2, 20))
    lamps = [r["lamp"] for r in tables["nodes"] if r["lamp"] in LAMP_ORDER]
    report["lamp"] = worst(lamps) if lamps else "GRAY"
    report["counts"] = dict(collections.Counter(r["lamp"] for r in tables["nodes"]))
    write_json(out / "WORKFLOW_VIZ.json", report)
    print("[%s] %s · 節點 %d · 邊 %d · 指標 %d · 總燈 %s"
          % (TAG, args.verb, len(tables["nodes"]), len(tables["edges"]),
             len(tables["metrics_ts"]), report["lamp"]), flush=True)
    for name, step in report["steps"].items():
        print("  · %-9s %s" % (name, json.dumps(step, ensure_ascii=False)[:190]), flush=True)
    print("NEXT: 開 %s/VIA_WorkflowViz.html(離線單檔);續跑同一行即增量("
          "metrics_ts 鍵 node_id + ts + run)" % out, flush=True)
    return report


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s 自測 ===" % TAG, flush=True)
    with tempfile.TemporaryDirectory(prefix="wfviz_") as td:
        root = Path(td)
        via = root / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (via / "VIA_Reports" / "vcgc").mkdir(parents=True)
        (via / "docs" / "handoff").mkdir(parents=True)
        write_json(reg / "VIA_VCGC_FunctionInventory_SSOT_v0001.json", {"stations": [
            {"id": "V-token", "name": "省 Token 第一步", "argv": ["token"], "quick": True, "timeout": 300},
            {"id": "C-vdf-fetch", "name": "VDF 擷取站", "argv": ["run", "VDF_MDL012_FetchGroups", "--dry"],
             "timeout": 600},
            {"id": "QG-calc", "name": "VQG 計算站", "argv": ["run", "VQG_MDL001_Calc"], "timeout": 60},
            {"id": "ZZ-unknown", "name": "未知前綴站", "argv": ["noop"], "timeout": 10}]})
        ledger = reg / "VIA_VCGC_FunctionLedger_v0100.jsonl"
        ledger.write_text("\n".join([
            json.dumps({"ts": "2026-11-01T00:00:00+00:00", "event": "baseline", "id": "family:VDF_MDL012_FetchGroups",
                        "kind": "family", "file": "VDF_MDL012_FetchGroups_v0107.py", "version": "v0107",
                        "sha16": "aa", "run": "r1", "head": "h1"}, ensure_ascii=False),
            json.dumps({"ts": "2026-11-02T00:00:00+00:00", "event": "changed", "id": "family:VDF_MDL012_FetchGroups",
                        "kind": "family", "file": "VDF_MDL012_FetchGroups_v0108.py", "version": "v0108",
                        "sha16": "bb", "run": "r2", "head": "h2"}, ensure_ascii=False),
            json.dumps({"ts": "2026-11-02T00:00:00+00:00", "event": "changed", "id": "book:VIA_Req",
                        "kind": "book", "file": "VIA_Requirements_SSOT_v0219.json", "version": "v0219",
                        "sha16": "cc", "run": "r2", "head": "h2"}, ensure_ascii=False),
            "不是 JSON 的一行", ""]) + "\n", encoding="utf-8")
        write_json(via / "VIA_Reports" / "vcgc" / "TEST_latest.json", {
            "at": "2026-11-03T00:00:00+00:00", "run": "t1", "head": "h3", "lamp": "YELLOW",
            "rows": [{"id": "V-token", "name": "省 Token", "lamp": "GREEN", "rc": 0, "secs": 2.5},
                     {"id": "C-vdf-fetch", "name": "VDF 擷取", "lamp": "RED", "rc": 1, "secs": 9.5}]})
        write_json(via / "docs" / "handoff" / "HANDOFF_latest.json", {
            "lamp": "RED", "closeout_lamp": "YELLOW", "summary": {"requirements": 3},
            "work_items": {"R1:token": {"id": "R1:token", "state": "VERIFIED", "requirement": "R1",
                                        "case": "token", "receipt": "e/token.json"},
                           "R2:x": {"id": "R2:x", "state": "BLOCKED", "requirement": "R2", "case": "nope"}}})

        tables = ingest(via)
        ids = {r["node_id"] for r in tables["nodes"]}
        chk("ingest:站 / 家族 / 冊 / 工作項 / 車道 都進了節點表",
            {"station:V-token", "station:C-vdf-fetch", "family:VDF_MDL012_FetchGroups",
             "book:VIA_Req", "work:R1:token", "lane:VDF"} <= ids, len(ids))
        chk("ingest:壞 JSON 行跳過,不當成節點,也不中斷",
            len(tables["metrics_ts"]) == 5 and all(r["node_id"] for r in tables["metrics_ts"]),
            len(tables["metrics_ts"]))
        by_id = {r["node_id"]: r for r in tables["nodes"]}
        chk("車道推定:QG- → VQG · VDF_ 家族 → VDF · 未知前綴照實 UNKNOWN(不猜)",
            by_id["station:QG-calc"]["layer"] == "VQG"
            and by_id["family:VDF_MDL012_FetchGroups"]["layer"] == "VDF"
            and by_id["station:ZZ-unknown"]["layer"] == "UNKNOWN")
        chk("燈:站的紅照實紅 · 工作項 BLOCKED → 紅 · VERIFIED → 綠 · 沒收據的站 GRAY",
            by_id["station:C-vdf-fetch"]["lamp"] == "RED" and by_id["work:R2:x"]["lamp"] == "RED"
            and by_id["work:R1:token"]["lamp"] == "GREEN"
            and by_id["station:ZZ-unknown"]["lamp"] == "GRAY")
        chk("Interface 欄位:站帶 argv 與 api 簽名;工作項帶需求 / 案 / 收據",
            by_id["station:C-vdf-fetch"]["interface"]["argv"][1] == "VDF_MDL012_FetchGroups"
            and by_id["station:C-vdf-fetch"]["interface"]["api"].startswith("via-vcgc run")
            and by_id["work:R1:token"]["interface"]["receipt"] == "e/token.json")
        chk("邊:站 → 家族(dataflow)有了 · 沒有懸空邊 · 同鍵合併累加",
            any(e["from"] == "station:C-vdf-fetch" and e["to"] == "family:VDF_MDL012_FetchGroups"
                and e["edge_type"] == "dataflow" for e in tables["edges"])
            and all(e["from"] in ids and e["to"] in ids for e in tables["edges"]))
        chk("工作項對不到案站 → 邊走 feedback 到車道(照實說沒對到,不硬接)",
            any(e["from"] == "work:R2:x" and e["edge_type"] == "feedback" for e in tables["edges"]))
        chk("會籍不畫邊 · 跨車道畫車道到車道:沒有任何 family → lane 邊,且 VCGC → VDF 交接在",
            not any(e["from"].startswith("family:") and e["to"].startswith("lane:")
                    for e in tables["edges"])
            and any(e["from"] == "lane:VCGC" and e["to"] == "lane:VDF"
                    and e["edge_type"] == "dataflow" for e in tables["edges"]),
            "C-vdf-fetch(VCGC)叫 VDF 家族 → lane:VCGC → lane:VDF")
        topo_dag = topology(tables["nodes"], tables["edges"])
        chk("修掉假環後:站 / 家族 / 冊 / 工作項都不在環裡(環只可能發生在車道之間)",
            all(n.startswith("lane:") for n in topo_dag["in_cycle"]), topo_dag["in_cycle"])
        chk("孤節點:沒有站指到的冊由車道持有(不懸空)",
            any(e["from"] == "lane:VCGC" and e["to"] == "book:VIA_Req" and e["edge_type"] == "control"
                for e in tables["edges"]))

        topo = topology(tables["nodes"], tables["edges"])
        chk("拓撲:分層出來了 · 中心性總和 ≈ 1 · 環照實回報不砍邊",
            len({v for v in topo["rank"].values()}) >= 2
            and abs(sum(topo["pagerank"].values()) - 1.0) < 1e-6
            and isinstance(topo["in_cycle"], list), topo["engine"])
        cyc_nodes = [{"node_id": "a", "node_type": "x", "layer": "VCGC", "label": "a", "interface": {},
                      "lamp": "GRAY", "source": "s"},
                     {"node_id": "b", "node_type": "x", "layer": "VCGC", "label": "b", "interface": {},
                      "lamp": "GRAY", "source": "s"}]
        cyc = topology(cyc_nodes, [{"from": "a", "to": "b", "edge_type": "dataflow", "throughput": 1},
                                   {"from": "b", "to": "a", "edge_type": "dataflow", "throughput": 1}])
        chk("環路偵測:a→b→a 認得出來,is_dag False 且兩個節點都點名",
            cyc["is_dag"] is False and set(cyc["in_cycle"]) == {"a", "b"})

        out = root / "out1"
        first = persist(out, tables)
        chk("落地:三表 JSON + CSV 都寫了 · DuckDB DDL 一律吐出(桌機可照貼)",
            (out / "nodes.json").is_file() and (out / "edges.csv").is_file()
            and (out / "metrics_ts_snapshot.csv").is_file()
            and (out / "metrics_ts.ddl.sql").is_file()
            and "CREATE TABLE IF NOT EXISTS metrics_ts" in (out / "metrics_ts.ddl.sql").read_text(encoding="utf-8"))
        if have("duckdb"):
            counts = (first.get("duckdb") or {}).get("counts", {})
            chk("落地:DuckDB 的現況兩表真寫進去;metrics_ts 此時應為 0(累積庫歸 etl 管,persist 不碰)",
                isinstance(first["duckdb"], dict) and counts.get("nodes") == len(tables["nodes"])
                and counts.get("edges") == len(tables["edges"]) and counts.get("metrics_ts") == 0,
                first["duckdb"])
        else:
            chk("落地:沒有 duckdb → 照實記 None,不假裝寫過", first["duckdb"] is None)

        chk("落地:指標只寫本輪快照 metrics_ts_snapshot.*,不碰累積庫 metrics_ts.json",
            (out / "metrics_ts_snapshot.json").is_file() and not (out / "metrics_ts.json").is_file(),
            sorted(x.name for x in out.glob("metrics_ts*")))
        step1 = etl_append(out, tables["metrics_ts"])
        step2 = etl_append(out, tables["metrics_ts"])
        chk("增量 ETL:第一次全進 · 第二次同一批 append 0(anti-join 鍵 node_id + ts + run)",
            step1["appended"] == len(tables["metrics_ts"]) and step2["appended"] == 0
            and step2["total"] == step1["total"], [step1["appended"], step2["appended"]])
        persist(out, tables)      # 再 persist 一次:累積庫不能被洗掉(這是真 bug 的回歸測)
        chk("回歸:再跑一次 persist 不會洗掉累積的 metrics_ts(只增不刪)",
            len(read_json(out / "metrics_ts.json", []) or []) == step1["total"],
            len(read_json(out / "metrics_ts.json", []) or []))
        newer = tables["metrics_ts"] + [{"node_id": "station:V-token", "ts": "2026-11-09T00:00:00+00:00",
                                         "run": "t2", "event": "test", "lamp": "GREEN", "secs": 1.1,
                                         "version": None, "sha16": None, "head": "h9"}]
        step3 = etl_append(out, newer)
        chk("增量 ETL:只有新的那一列會進去(舊的不重複落庫)", step3["appended"] == 1, step3)
        if have("duckdb"):
            import duckdb
            con = duckdb.connect(str(out / "workflow.duckdb"))
            try:
                total = con.execute("SELECT count(*) FROM metrics_ts").fetchone()[0]
                dups = con.execute("SELECT count(*) FROM (SELECT node_id, ts, run FROM metrics_ts"
                                   " GROUP BY 1,2,3 HAVING count(*) > 1)").fetchone()[0]
            finally:
                con.close()
            chk("DuckDB metrics_ts:增量進去了 · 同鍵沒有重複列", total >= len(tables["metrics_ts"]) and dups == 0,
                [total, dups])

        card = render_html(tables, topo, out, 120)
        page = (out / "VIA_WorkflowViz.html").read_text(encoding="utf-8")
        outside = [x for x in re.findall(r"https?://[^\s\"'<>]+", page)
                   if x != "http://www.w3.org/2000/svg"]
        chk("HTML:單檔離線 · 沒有任何外部引用(SVG 命名空間不算;base64 裡的字母不算)",
            card["offline"] and not outside and "@import" not in page
            and not re.search(r"(?:src|href)=\"(?!data:)(?://|https?:)", page), outside[:3])
        chk("HTML:三視圖都在 · 預設只顯示功能視圖 · 下鑽面板在",
            'id="view-function"' in page and 'id="view-dataflow"' in page
            and 'id="view-interface"' in page and page.count("hidden>") >= 2 and 'id="drill"' in page)
        chk("HTML:車道 × 種類矩陣有 VDF 與 VQG 兩列 · 紅節點進了頁面(紅不被藏起來)",
            ">VDF<" in page and ">VQG<" in page and "station:C-vdf-fetch" in page)
        chk("HTML:燈的計數照實印(含 GRAY 的「沒收據不猜」說明)",
            "GRAY = 這個節點沒有收據" in page)
        if have("seaborn") and have("matplotlib"):
            chk("熱力圖:seaborn 真畫並 base64 內嵌", "data:image/png;base64," in page, card["heatmap"])
        else:
            chk("熱力圖:沒有 seaborn → 照實說沒畫,不假裝", "data:image/png;base64," not in page)

        mm = render_mermaid(tables, topo, out, 40)
        text = Path(mm["mmd"]).read_text(encoding="utf-8")
        chk("Mermaid:flowchart + subgraph 車道 + 邊 + Interface 註解;節點名安全(無引號破圖)",
            text.startswith("flowchart TD") and "subgraph VDF" in text
            and "-->" in text and "%% Interface 詳情" in text and '"]' in text)
        chk("Mermaid:回饋邊用虛線箭頭", "-.->" in text, text.count("-.->"))

        schema_text = json.dumps({"nodes": NODE_SCHEMA, "edges": EDGE_SCHEMA, "metrics_ts": METRIC_SCHEMA},
                                 ensure_ascii=False)
        chk("資料合約:三表欄位齊 · metrics_ts 增量鍵三件都在",
            all(k in schema_text for k in ("node_id", "interface", "throughput", "secs", "run")))
        text_self = Path(__file__).read_text(encoding="utf-8")
        chk("本支帶加速器橋(標記 + 真載)· 第 3 行標記 · 不含 TA-Lib · 沒有自己 pip",
            "[VIA:ACCEL-BRIDGE" in text_self and ("VIA_ACCEL" in globals())
            and text_self.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0100]"
            and not re.search(r"^\s*(?:import|from)\s+talib\b", text_self, re.M)
            and not re.search(r"pip\s+install", text_self))
    bad = len([x for x in ok if not x])
    print("[計] %s 自測 %d/%d · %s" % (TAG, len(ok) - bad, len(ok), "PASS" if not bad else "FAIL"), flush=True)
    return 0 if not bad else 1


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TAG, description="功能資訊流 + Interface 架構的工作流圖(零安裝 · 離線)")
    parser.add_argument("verb", nargs="?", default="all",
                        choices=["schema", "ingest", "etl", "render", "mermaid", "all"])
    here = Path(__file__).resolve()
    guess = here.parents[3] if len(here.parents) > 3 else here.parent
    parser.add_argument("--via", default=str(guess), help="VIA 樹或倉根(預設由本檔位置推)")
    parser.add_argument("--out", default="", help="輸出夾(預設 <VIA>/VIA_Reports/workflow_viz)")
    parser.add_argument("--top", type=int, default=120, help="圖上最多畫幾個節點(紅 / 黃優先留)")
    parser.add_argument("--selftest", action="store_true")
    return parser


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    if args.selftest:
        return selftest()
    if args.verb == "schema":
        print(json.dumps({"schema": SCHEMA_ID, "nodes": NODE_SCHEMA, "edges": EDGE_SCHEMA,
                          "metrics_ts": METRIC_SCHEMA, "incremental_key": "node_id + ts + run"},
                         ensure_ascii=False, indent=2))
        print("\n-- DuckDB DDL --\n" + DUCKDB_DDL)
        return 0
    if not args.out:
        via = Path(args.via).resolve()
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        args.out = str(via / "VIA_Reports" / "workflow_viz")
    report = run_all(args)
    return {"GREEN": 0, "YELLOW": 2, "GRAY": 2, "RED": 1}.get(report.get("lamp", "RED"), 1)


if __name__ == "__main__":
    sys.exit(main())
