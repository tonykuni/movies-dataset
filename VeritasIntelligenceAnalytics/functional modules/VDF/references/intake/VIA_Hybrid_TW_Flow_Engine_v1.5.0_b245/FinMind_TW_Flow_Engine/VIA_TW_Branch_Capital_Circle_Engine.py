#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA 台股分點資金管理圈與大戶行為日資料判定引擎。

重要限制：公開分點資料是交易通路彙總，不是最終受益人資料。本引擎只能輸出
「疑似相同資金管理圈／相近交易策略來源」及統計信心，不能確認自然人、法人
或違法行為身分。WH-036～WH-038 僅為資料異常待覆核標籤。
"""

from __future__ import annotations


# =============================================================================
# 0. 所有可調參數（集中於程式碼頂部）
# =============================================================================

ENGINE_NAME = "VIA TW Branch Capital Circle Engine"
ENGINE_VERSION = "1.0.0"

DEFAULT_DUCKDB_PATH = "FinMind_TW_Flow_Output/FinMind_TW_Flow.duckdb"
DEFAULT_GROUP_MAP_PATH = ""
DEFAULT_OUTPUT_ROOT = "FinMind_TW_Flow_Output/capital_circle"
DEFAULT_END_DATE = "latest"

LOOKBACK_TRADING_DAYS = 120
BEHAVIOR_ROLLING_DAYS = 20
TOP_BRANCHES_PER_STOCK_DAY = 12
MIN_BRANCH_ACTIVE_DAYS = 5
MIN_PAIR_OVERLAP = 6
MUTUAL_TOP_K = 3
MAX_CIRCLE_MEMBERS = 12

CIRCLE_EDGE_THRESHOLD = 0.68
CIRCLE_HIGH_CONFIDENCE = 0.80
MIN_DIRECTION_MATCH = 0.70
INSTITUTION_CORRELATION_THRESHOLD = 0.55
INSTITUTION_DIRECTION_HIT_THRESHOLD = 0.65
MIN_INSTITUTION_OBSERVATIONS = 10

SIDEWAYS_RETURN_ABS = 0.03
PULLBACK_RETURN = -0.02
TREND_RETURN = 0.06
BREAKOUT_BUFFER = 0.002
HIGH_VOLUME_RATIO = 1.50
LOW_VOLUME_RATIO = 0.80
HIGH_DAYTRADE_RATIO = 0.35
HIGH_FLOW_CONCENTRATION = 0.35
MIN_SIGNAL_SCORE = 60.0

CSV_ENCODING = "utf-8-sig"
EXPORT_WITHOUT_EXTENSION = True
DATE_OUTPUT_FORMAT = "%Y/%m/%d"

GROUP_TABLE_CANDIDATES = (
    "tw_stock_group_map",
    "stock_group_map",
    "tw_stock_group_classification",
)

GROUP_COLUMN_ALIASES = {
    "stock_id": ("stock_id", "ticker", "symbol", "code", "stock_code"),
    "group_id": ("group_id", "group_code", "industry_id", "category_id"),
    "group_name": (
        "group_name", "industry", "industry_name", "category", "sub_industry",
    ),
}

EDGE_WEIGHTS = {
    "direction_match": 0.30,
    "signed_correlation": 0.20,
    "activity_overlap": 0.18,
    "group_profile": 0.14,
    "stock_profile": 0.08,
    "cost_similarity": 0.06,
    "volume_similarity": 0.04,
}

BEHAVIOR_CATALOG = (
    ("WH-001", "低檔集中建倉", "ACCUMULATION", "supported"),
    ("WH-002", "橫盤隱蔽吸籌", "ACCUMULATION", "supported"),
    ("WH-003", "下跌承接", "ACCUMULATION", "supported"),
    ("WH-004", "回檔加碼", "ACCUMULATION", "supported"),
    ("WH-005", "多分點拆單建倉", "ACCUMULATION", "supported"),
    ("WH-006", "定量規律建倉", "ACCUMULATION", "supported_daily_approximation"),
    ("WH-007", "鉅額交易承接", "ACCUMULATION", "conditional_block_data"),
    ("WH-008", "法人賣出、大戶承接", "ACCUMULATION", "conditional_institution_data"),
    ("WH-009", "小量試單", "TESTING", "supported_candidate"),
    ("WH-010", "突破試盤", "TESTING", "supported_candidate"),
    ("WH-011", "壓價測試", "TESTING", "supported_candidate"),
    ("WH-012", "縮量洗盤", "TESTING", "supported"),
    ("WH-013", "爆量震盪洗盤", "TESTING", "supported_candidate"),
    ("WH-014", "融資清洗", "TESTING", "conditional_margin_data"),
    ("WH-015", "突破加碼", "MARKUP", "supported"),
    ("WH-016", "階梯式推升", "MARKUP", "supported"),
    ("WH-017", "鎖籌推升", "MARKUP", "supported_candidate"),
    ("WH-018", "尾盤集中買進", "MARKUP", "not_identifiable_from_daily"),
    ("WH-019", "族群聯動布局", "MARKUP", "supported_group_daily"),
    ("WH-020", "消息前提前布局", "ACCUMULATION", "requires_event_calendar"),
    ("WH-021", "分點間移轉", "ROTATION", "supported_cross_circle_candidate"),
    ("WH-022", "大戶間換手", "ROTATION", "supported_cross_circle_candidate"),
    ("WH-023", "強勢換手", "ROTATION", "supported_cross_circle_candidate"),
    ("WH-024", "族群輪動", "ROTATION", "supported_group_daily"),
    ("WH-025", "部位再平衡", "ROTATION", "supported_calendar_candidate"),
    ("WH-026", "上漲分批減碼", "DISTRIBUTION", "supported"),
    ("WH-027", "反彈出貨", "DISTRIBUTION", "supported"),
    ("WH-028", "高檔爆量出貨", "DISTRIBUTION", "supported"),
    ("WH-029", "多分點分散出貨", "DISTRIBUTION", "supported"),
    ("WH-030", "法人接手出貨", "DISTRIBUTION", "conditional_institution_data"),
    ("WH-031", "現貨多單加期貨避險", "HEDGE_SHORT", "requires_futures_positions"),
    ("WH-032", "借券策略性偏空", "HEDGE_SHORT", "conditional_lending_data"),
    ("WH-033", "多空配對交易", "HEDGE_SHORT", "supported_group_daily"),
    ("WH-034", "短空回補", "HEDGE_SHORT", "conditional_margin_data"),
    ("WH-035", "事件前降低曝險", "HEDGE_SHORT", "requires_event_calendar"),
    ("WH-036", "買賣大量但淨額極小異常", "ANOMALY_REVIEW", "supported_review_only"),
    ("WH-037", "集中買進與價格急升異常", "ANOMALY_REVIEW", "supported_review_only"),
    ("WH-038", "集中賣出與價格急跌異常", "ANOMALY_REVIEW", "supported_review_only"),
    ("WH-039", "隔日反向短週期資金", "TESTING", "supported_daily_approximation"),
    ("WH-040", "突破時原資金轉賣風險", "DISTRIBUTION", "supported"),
)


# =============================================================================
# 1. 匯入與通用工具
# =============================================================================

import argparse
import hashlib
import itertools
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

try:
    import duckdb
except ModuleNotFoundError:  # 允許純函式單元測試先執行。
    duckdb = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def require_duckdb() -> None:
    if duckdb is None:
        raise RuntimeError("缺少 duckdb；請先執行 pip install -r requirements.txt")


def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"不安全識別字：{identifier}")
    return f'"{identifier}"'


def normalize_ticker(value: Any) -> str:
    ticker = str(value or "").strip().upper()
    ticker = re.sub(r"\.(TW|TWO)$", "", ticker)
    if not re.fullmatch(r"[0-9A-Z]{4,10}", ticker):
        raise ValueError(f"無法辨識股票代碼：{value}")
    return ticker


def safe_float(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "--"):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def safe_int(value: Any, default: int = 0) -> int:
    return int(round(safe_float(value, float(default))))


def sign(value: float, tolerance: float = 1e-12) -> int:
    if value > tolerance:
        return 1
    if value < -tolerance:
        return -1
    return 0


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if abs(denominator) > 1e-12 else default


def mean(values: Iterable[float], default: float = 0.0) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else default


def coefficient_of_variation(values: Iterable[float]) -> float:
    materialized = [abs(value) for value in values if abs(value) > 1e-12]
    if len(materialized) < 2:
        return math.inf
    average = mean(materialized)
    return statistics.pstdev(materialized) / average if average else math.inf


def pearson_from_sums(stats: dict[str, float]) -> float:
    count = stats.get("count", 0.0)
    if count < 2:
        return 0.0
    numerator = count * stats["sum_xy"] - stats["sum_x"] * stats["sum_y"]
    left = count * stats["sum_x2"] - stats["sum_x"] ** 2
    right = count * stats["sum_y2"] - stats["sum_y"] ** 2
    denominator = math.sqrt(max(left, 0.0) * max(right, 0.0))
    return numerator / denominator if denominator > 1e-12 else 0.0


def pearson_pairs(pairs: Iterable[tuple[float, float]]) -> float:
    stats = {
        "count": 0.0, "sum_x": 0.0, "sum_y": 0.0,
        "sum_x2": 0.0, "sum_y2": 0.0, "sum_xy": 0.0,
    }
    for x_value, y_value in pairs:
        stats["count"] += 1.0
        stats["sum_x"] += x_value
        stats["sum_y"] += y_value
        stats["sum_x2"] += x_value * x_value
        stats["sum_y2"] += y_value * y_value
        stats["sum_xy"] += x_value * y_value
    return pearson_from_sums(stats)


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left).intersection(right)
    numerator = sum(left[key] * right[key] for key in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm <= 1e-12 or right_norm <= 1e-12:
        return 0.0
    return clamp((numerator / (left_norm * right_norm) + 1.0) / 2.0)


def weighted_jaccard(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left).union(right)
    numerator = sum(min(abs(left.get(key, 0.0)), abs(right.get(key, 0.0))) for key in keys)
    denominator = sum(max(abs(left.get(key, 0.0)), abs(right.get(key, 0.0))) for key in keys)
    return safe_ratio(numerator, denominator)


def stable_circle_id(branch_ids: Iterable[str]) -> str:
    identity = "|".join(sorted(set(branch_ids)))
    return "CC-" + hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10].upper()


# =============================================================================
# 2. 分點觀測、關聯圖與資金圈聚類（純函式，可離線測試）
# =============================================================================

def normalize_observation(source: dict[str, Any]) -> dict[str, Any]:
    buy_volume = safe_float(source.get("buy_volume", source.get("buy", 0.0)))
    sell_volume = safe_float(source.get("sell_volume", source.get("sell", 0.0)))
    buy_price = safe_float(source.get("buy_price", source.get("price", 0.0)))
    sell_price = safe_float(source.get("sell_price", source.get("price", 0.0)))
    net_volume = safe_float(source.get("net_volume", buy_volume - sell_volume))
    net_amount = safe_float(
        source.get("net_amount", buy_volume * buy_price - sell_volume * sell_price)
    )
    gross_amount = safe_float(
        source.get("gross_amount", buy_volume * buy_price + sell_volume * sell_price)
    )
    effective_price = buy_price if net_volume >= 0 else sell_price
    raw_groups = source.get("groups")
    if isinstance(raw_groups, str):
        raw_groups = (raw_groups,)
    groups = tuple(sorted(set(raw_groups or (source.get("group_id") or "UNGROUPED",))))
    return {
        "date": str(source["date"]),
        "stock_id": normalize_ticker(source["stock_id"]),
        "branch_id": str(source.get("branch_id") or source.get("securities_trader_id") or "").strip(),
        "branch_name": str(source.get("branch_name") or source.get("securities_trader") or "").strip(),
        "buy_volume": buy_volume,
        "sell_volume": sell_volume,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "net_volume": net_volume,
        "net_amount": net_amount,
        "gross_amount": gross_amount,
        "effective_price": effective_price,
        "direction": sign(net_amount if abs(net_amount) > 1e-12 else net_volume),
        "groups": groups,
        "stock_total_abs_net": safe_float(source.get("stock_total_abs_net", 0.0)),
    }


def build_branch_profiles(
    observations: Iterable[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]]]:
    profiles: dict[str, dict[str, Any]] = {}
    by_stock_day: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in observations:
        observation = normalize_observation(raw)
        branch_id = observation["branch_id"]
        if not branch_id or observation["direction"] == 0:
            continue
        by_stock_day[(observation["date"], observation["stock_id"])].append(observation)
        profile = profiles.setdefault(branch_id, {
            "branch_id": branch_id,
            "branch_name": observation["branch_name"],
            "active_keys": set(),
            "active_dates": set(),
            "stock_profile": defaultdict(float),
            "group_profile": defaultdict(float),
            "net_amount": 0.0,
        })
        profile["active_keys"].add((observation["date"], observation["stock_id"]))
        profile["active_dates"].add(observation["date"])
        profile["stock_profile"][observation["stock_id"]] += abs(observation["net_amount"])
        group_weight = abs(observation["net_amount"]) / max(len(observation["groups"]), 1)
        for group_id in observation["groups"]:
            profile["group_profile"][group_id] += group_weight * observation["direction"]
        profile["net_amount"] += observation["net_amount"]
    return profiles, by_stock_day


def build_pair_statistics(
    profiles: dict[str, dict[str, Any]],
    by_stock_day: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[tuple[str, str], dict[str, float]]:
    pair_stats: dict[tuple[str, str], dict[str, float]] = {}
    for stock_day_observations in by_stock_day.values():
        ordered = sorted(
            stock_day_observations,
            key=lambda row: abs(row["net_amount"]),
            reverse=True,
        )[:TOP_BRANCHES_PER_STOCK_DAY]
        for left, right in itertools.combinations(ordered, 2):
            pair = tuple(sorted((left["branch_id"], right["branch_id"])))
            stats = pair_stats.setdefault(pair, {
                "count": 0.0, "same_direction": 0.0, "opposite_direction": 0.0,
                "sum_x": 0.0, "sum_y": 0.0, "sum_x2": 0.0,
                "sum_y2": 0.0, "sum_xy": 0.0,
                "cost_sum": 0.0, "cost_count": 0.0,
                "volume_sum": 0.0, "volume_count": 0.0,
            })
            x_value = math.copysign(math.log1p(abs(left["net_amount"])), left["direction"])
            y_value = math.copysign(math.log1p(abs(right["net_amount"])), right["direction"])
            stats["count"] += 1.0
            stats["sum_x"] += x_value
            stats["sum_y"] += y_value
            stats["sum_x2"] += x_value * x_value
            stats["sum_y2"] += y_value * y_value
            stats["sum_xy"] += x_value * y_value
            if left["direction"] == right["direction"]:
                stats["same_direction"] += 1.0
                price_base = max(abs(left["effective_price"]), abs(right["effective_price"]), 1e-9)
                relative_gap = abs(left["effective_price"] - right["effective_price"]) / price_base
                stats["cost_sum"] += math.exp(-relative_gap / 0.01)
                stats["cost_count"] += 1.0
                left_amount = max(abs(left["net_amount"]), 1.0)
                right_amount = max(abs(right["net_amount"]), 1.0)
                stats["volume_sum"] += math.exp(-abs(math.log(left_amount / right_amount)))
                stats["volume_count"] += 1.0
            else:
                stats["opposite_direction"] += 1.0
    return pair_stats


def score_branch_edges(
    profiles: dict[str, dict[str, Any]],
    pair_stats: dict[tuple[str, str], dict[str, float]],
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for (left_id, right_id), stats in pair_stats.items():
        overlap = int(stats["count"])
        left_profile = profiles[left_id]
        right_profile = profiles[right_id]
        if overlap < MIN_PAIR_OVERLAP:
            continue
        if min(len(left_profile["active_dates"]), len(right_profile["active_dates"])) < MIN_BRANCH_ACTIVE_DAYS:
            continue
        direction_match = safe_ratio(stats["same_direction"], stats["count"])
        signed_correlation = clamp(pearson_from_sums(stats), 0.0, 1.0)
        activity_overlap = safe_ratio(
            overlap,
            min(len(left_profile["active_keys"]), len(right_profile["active_keys"])),
        )
        group_profile = cosine_similarity(
            dict(left_profile["group_profile"]), dict(right_profile["group_profile"])
        )
        stock_profile = weighted_jaccard(
            dict(left_profile["stock_profile"]), dict(right_profile["stock_profile"])
        )
        cost_similarity = safe_ratio(stats["cost_sum"], stats["cost_count"])
        volume_similarity = safe_ratio(stats["volume_sum"], stats["volume_count"])
        components = {
            "direction_match": direction_match,
            "signed_correlation": signed_correlation,
            "activity_overlap": clamp(activity_overlap),
            "group_profile": group_profile,
            "stock_profile": stock_profile,
            "cost_similarity": cost_similarity,
            "volume_similarity": volume_similarity,
        }
        score = sum(EDGE_WEIGHTS[name] * components[name] for name in EDGE_WEIGHTS)
        edges.append({
            "branch_a": left_id,
            "branch_b": right_id,
            "overlap_observations": overlap,
            "score": score,
            **components,
        })
    return sorted(edges, key=lambda row: (-row["score"], row["branch_a"], row["branch_b"]))


class UnionFind:
    def __init__(self, nodes: Iterable[str]):
        self.parent = {node: node for node in nodes}
        self.size = {node: 1 for node in nodes}

    def find(self, node: str) -> str:
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, left: str, right: str) -> bool:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return False
        if self.size[left_root] + self.size[right_root] > MAX_CIRCLE_MEMBERS:
            return False
        if self.size[left_root] < self.size[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        self.size[left_root] += self.size[right_root]
        return True


def cluster_mutual_top_edges(
    profiles: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    qualifying = [
        edge for edge in edges
        if edge["score"] >= CIRCLE_EDGE_THRESHOLD
        and edge["direction_match"] >= MIN_DIRECTION_MATCH
    ]
    neighbor_edges: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for edge in qualifying:
        neighbor_edges[edge["branch_a"]].append((edge["score"], edge["branch_b"]))
        neighbor_edges[edge["branch_b"]].append((edge["score"], edge["branch_a"]))
    top_neighbors = {
        branch_id: {
            neighbor for _score, neighbor in sorted(values, reverse=True)[:MUTUAL_TOP_K]
        }
        for branch_id, values in neighbor_edges.items()
    }
    mutual_edges = [
        edge for edge in qualifying
        if edge["branch_b"] in top_neighbors.get(edge["branch_a"], set())
        and edge["branch_a"] in top_neighbors.get(edge["branch_b"], set())
    ]
    union_find = UnionFind(profiles)
    for edge in mutual_edges:
        union_find.union(edge["branch_a"], edge["branch_b"])
    grouped: dict[str, list[str]] = defaultdict(list)
    for branch_id in profiles:
        grouped[union_find.find(branch_id)].append(branch_id)
    circles = {
        stable_circle_id(members): sorted(members)
        for members in grouped.values() if len(members) >= 2
    }
    branch_to_circle = {
        branch_id: circle_id
        for circle_id, members in circles.items() for branch_id in members
    }
    retained_edges: list[dict[str, Any]] = []
    for edge in edges:
        left_circle = branch_to_circle.get(edge["branch_a"])
        right_circle = branch_to_circle.get(edge["branch_b"])
        if left_circle and left_circle == right_circle:
            retained_edges.append({**edge, "circle_id": left_circle})
    return retained_edges, circles


def build_capital_circles(
    observations: Iterable[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, list[str]]]:
    profiles, by_stock_day = build_branch_profiles(observations)
    pair_stats = build_pair_statistics(profiles, by_stock_day)
    edges = score_branch_edges(profiles, pair_stats)
    retained_edges, circles = cluster_mutual_top_edges(profiles, edges)
    return profiles, retained_edges, circles


# =============================================================================
# 3. 法人對齊、行情衍生值與大戶行為狀態機
# =============================================================================

def institutional_alignment(
    circle_flow: dict[tuple[str, str], float],
    institutional_flow: dict[tuple[str, str], dict[str, float]],
) -> dict[str, Any]:
    categories = (
        "investment_trust", "dealer_self", "dealer_hedging", "foreign_investor"
    )
    results: list[dict[str, Any]] = []
    for category in categories:
        pairs: list[tuple[float, float]] = []
        direction_hits = 0
        for key, circle_value in circle_flow.items():
            institutional_value = institutional_flow.get(key, {}).get(category)
            if institutional_value is None or abs(institutional_value) <= 1e-12:
                continue
            transformed_circle = math.copysign(math.log1p(abs(circle_value)), circle_value)
            transformed_institution = math.copysign(
                math.log1p(abs(institutional_value)), institutional_value
            )
            pairs.append((transformed_circle, transformed_institution))
            direction_hits += int(sign(circle_value) == sign(institutional_value))
        results.append({
            "category": category,
            "observations": len(pairs),
            "correlation": pearson_pairs(pairs),
            "direction_hit": safe_ratio(direction_hits, len(pairs)),
        })
    best = max(results, key=lambda row: (row["correlation"], row["direction_hit"]), default={})
    qualified = (
        best
        and best["observations"] >= MIN_INSTITUTION_OBSERVATIONS
        and best["correlation"] >= INSTITUTION_CORRELATION_THRESHOLD
        and best["direction_hit"] >= INSTITUTION_DIRECTION_HIT_THRESHOLD
    )
    labels = {
        "investment_trust": "疑似投信執行通路",
        "dealer_self": "疑似自營商方向型通路",
        "dealer_hedging": "疑似自營避險型通路",
        "foreign_investor": "疑似外資執行通路",
    }
    return {
        "style": labels.get(best.get("category"), "疑似大戶／其他國內法人或混合資金")
        if qualified else "疑似大戶／其他國內法人或混合資金",
        "qualified": bool(qualified),
        "best_category": best.get("category", "unknown"),
        "correlation": safe_float(best.get("correlation")),
        "direction_hit": safe_float(best.get("direction_hit")),
        "observations": safe_int(best.get("observations")),
        "all_categories": results,
    }


def signal_score(*conditions: tuple[bool, float]) -> float:
    available = sum(weight for _condition, weight in conditions)
    passed = sum(weight for condition, weight in conditions if condition)
    return 100.0 * safe_ratio(passed, available)


def append_signal(
    signals: list[dict[str, Any]],
    code: str,
    score: float,
    evidence: dict[str, Any],
) -> None:
    if score < MIN_SIGNAL_SCORE:
        return
    catalog = {item[0]: item for item in BEHAVIOR_CATALOG}
    _code, name, state, _availability = catalog[code]
    signals.append({
        "behavior_code": code,
        "behavior_name": name,
        "state": state,
        "signal_score": round(score, 2),
        "evidence": evidence,
    })


def classify_daily_behavior(context: dict[str, Any]) -> list[dict[str, Any]]:
    """以日資料輸出候選行為；允許同日多標籤，最終由分數排序。"""
    signals: list[dict[str, Any]] = []
    net_1 = safe_float(context.get("net_1"))
    net_5 = safe_float(context.get("net_5"))
    net_20 = safe_float(context.get("net_20"))
    gross_1 = safe_float(context.get("gross_1"))
    ret_1 = safe_float(context.get("ret_1"))
    ret_5 = safe_float(context.get("ret_5"))
    ret_20 = safe_float(context.get("ret_20"))
    price_position = safe_float(context.get("price_position"), 0.5)
    volume_ratio = safe_float(context.get("volume_ratio"), 1.0)
    concentration = safe_float(context.get("flow_concentration"))
    buy_days_5 = safe_int(context.get("buy_days_5"))
    sell_days_5 = safe_int(context.get("sell_days_5"))
    active_members = safe_int(context.get("active_members"), 1)
    circle_members = safe_int(context.get("circle_members"), active_members)
    margin_delta = context.get("margin_delta")
    short_delta = context.get("short_delta")
    daytrade_ratio = context.get("daytrade_ratio")
    institution_net = context.get("institution_net")
    block_volume = context.get("block_volume")
    lending_volume = context.get("lending_volume")
    previous_net = safe_float(context.get("previous_net"))
    previous_high_20 = safe_float(context.get("previous_high_20"))
    close = safe_float(context.get("close"))
    amount_cv_5 = safe_float(context.get("amount_cv_5"), math.inf)
    evidence = {
        "net_1": net_1, "net_5": net_5, "net_20": net_20,
        "ret_1": ret_1, "ret_5": ret_5, "ret_20": ret_20,
        "price_position": price_position, "volume_ratio": volume_ratio,
        "flow_concentration": concentration,
        "daytrade_ratio": daytrade_ratio,
    }
    persistent_buy = net_5 > 0 and buy_days_5 >= 3
    persistent_sell = net_5 < 0 and sell_days_5 >= 3
    breakout = previous_high_20 > 0 and close >= previous_high_20 * (1.0 + BREAKOUT_BUFFER)
    low_daytrade_noise = daytrade_ratio is None or safe_float(daytrade_ratio) <= HIGH_DAYTRADE_RATIO

    append_signal(signals, "WH-001", signal_score(
        (persistent_buy, 3), (price_position <= 0.35, 2),
        (ret_20 <= SIDEWAYS_RETURN_ABS, 1), (low_daytrade_noise, 1),
    ), evidence)
    append_signal(signals, "WH-002", signal_score(
        (persistent_buy, 3), (abs(ret_5) <= SIDEWAYS_RETURN_ABS, 2),
        (volume_ratio <= 1.20, 1), (low_daytrade_noise, 1),
    ), evidence)
    append_signal(signals, "WH-003", signal_score(
        (net_1 > 0, 2), (ret_5 <= PULLBACK_RETURN, 2),
        (margin_delta is None or safe_float(margin_delta) <= 0, 1),
        (low_daytrade_noise, 1),
    ), evidence)
    append_signal(signals, "WH-004", signal_score(
        (ret_20 >= TREND_RETURN, 2), (ret_5 < 0, 1), (net_5 > 0, 2),
    ), evidence)
    append_signal(signals, "WH-005", signal_score(
        (circle_members >= 2, 2), (active_members >= 2, 2),
        (net_5 > 0, 1), (low_daytrade_noise, 1),
    ), evidence)
    append_signal(signals, "WH-006", signal_score(
        (buy_days_5 >= 4, 2), (amount_cv_5 <= 0.35, 2),
        (net_5 > 0, 1), (low_daytrade_noise, 1),
    ), evidence)
    if block_volume is not None:
        append_signal(signals, "WH-007", signal_score(
            (safe_float(block_volume) > 0, 2), (net_1 > 0, 2), (ret_1 >= -0.02, 1),
        ), evidence)
    if institution_net is not None:
        append_signal(signals, "WH-008", signal_score(
            (safe_float(institution_net) < 0, 2), (net_1 > 0, 2), (net_5 > 0, 1),
        ), evidence)
    append_signal(signals, "WH-009", signal_score(
        (net_1 > 0, 2), (abs(previous_net) <= abs(net_1) * 0.20, 1),
        (volume_ratio <= 1.10, 1), (abs(ret_1) <= 0.02, 1),
    ), evidence)
    append_signal(signals, "WH-010", signal_score(
        (breakout, 2), (net_1 > 0, 2), (volume_ratio >= 1.10, 1),
    ), evidence)
    append_signal(signals, "WH-011", signal_score(
        (net_1 < 0, 2), (net_20 > 0, 2), (abs(ret_1) <= 0.02, 1),
    ), evidence)
    append_signal(signals, "WH-012", signal_score(
        (ret_5 < 0, 1), (volume_ratio <= LOW_VOLUME_RATIO, 2), (net_20 > 0, 2),
    ), evidence)
    append_signal(signals, "WH-013", signal_score(
        (ret_5 <= 0, 1), (volume_ratio >= HIGH_VOLUME_RATIO, 2),
        (net_20 > 0, 1), (price_position >= 0.35, 1),
    ), evidence)
    if margin_delta is not None:
        append_signal(signals, "WH-014", signal_score(
            (safe_float(margin_delta) < 0, 2), (net_5 > 0, 2), (ret_5 <= 0.02, 1),
        ), evidence)
    append_signal(signals, "WH-015", signal_score(
        (breakout, 2), (net_5 > 0, 2), (buy_days_5 >= 3, 1),
    ), evidence)
    append_signal(signals, "WH-016", signal_score(
        (ret_20 >= TREND_RETURN, 2), (ret_5 > 0, 1), (net_20 > 0, 2),
    ), evidence)
    append_signal(signals, "WH-017", signal_score(
        (ret_20 >= TREND_RETURN, 2), (volume_ratio <= 1.0, 1),
        (concentration >= HIGH_FLOW_CONCENTRATION, 2),
    ), evidence)
    append_signal(signals, "WH-026", signal_score(
        (ret_5 >= 0.03, 2), (net_5 < 0, 2), (sell_days_5 >= 3, 1),
    ), evidence)
    append_signal(signals, "WH-027", signal_score(
        (ret_20 <= -TREND_RETURN, 2), (ret_5 > 0, 1), (net_5 < 0, 2),
    ), evidence)
    append_signal(signals, "WH-028", signal_score(
        (price_position >= 0.80, 2), (volume_ratio >= HIGH_VOLUME_RATIO, 2),
        (persistent_sell, 2),
    ), evidence)
    append_signal(signals, "WH-029", signal_score(
        (circle_members >= 2, 2), (active_members >= 2, 1), (persistent_sell, 2),
    ), evidence)
    if institution_net is not None:
        append_signal(signals, "WH-030", signal_score(
            (safe_float(institution_net) > 0, 2), (net_1 < 0, 2), (net_5 < 0, 1),
        ), evidence)
    if lending_volume is not None:
        append_signal(signals, "WH-032", signal_score(
            (safe_float(lending_volume) > 0, 2), (net_5 < 0, 2), (ret_5 <= 0, 1),
        ), evidence)
    if short_delta is not None:
        append_signal(signals, "WH-034", signal_score(
            (safe_float(short_delta) < 0, 2), (ret_5 > 0, 2), (net_1 > 0, 1),
        ), evidence)
    append_signal(signals, "WH-036", signal_score(
        (gross_1 > 0, 1), (safe_ratio(abs(net_1), gross_1, 1.0) <= 0.10, 3),
        (volume_ratio >= 1.20, 1),
    ), evidence)
    append_signal(signals, "WH-037", signal_score(
        (concentration >= HIGH_FLOW_CONCENTRATION, 2), (ret_1 >= 0.04, 2),
        (volume_ratio >= HIGH_VOLUME_RATIO, 1), (net_1 > 0, 1),
    ), evidence)
    append_signal(signals, "WH-038", signal_score(
        (concentration >= HIGH_FLOW_CONCENTRATION, 2), (ret_1 <= -0.04, 2),
        (volume_ratio >= HIGH_VOLUME_RATIO, 1), (net_1 < 0, 1),
    ), evidence)
    append_signal(signals, "WH-039", signal_score(
        (previous_net > 0, 2), (net_1 < 0, 2),
        (abs(net_1) >= abs(previous_net) * 0.50, 1),
        (daytrade_ratio is None or safe_float(daytrade_ratio) >= HIGH_DAYTRADE_RATIO, 1),
    ), evidence)
    append_signal(signals, "WH-040", signal_score(
        (breakout, 2), (net_1 < 0, 2), (net_5 < 0, 1),
    ), evidence)
    return sorted(signals, key=lambda row: (-row["signal_score"], row["behavior_code"]))


# =============================================================================
# 4. DuckDB 資料讀取與標準化
# =============================================================================

def table_exists(connection: Any, table_name: str) -> bool:
    row = connection.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE lower(table_name) = lower(?)",
        [table_name],
    ).fetchone()
    return bool(row and row[0])


def table_columns(connection: Any, table_name: str) -> list[str]:
    rows = connection.execute(f"DESCRIBE {quote_identifier(table_name)}").fetchall()
    return [str(row[0]) for row in rows]


def table_row_count(connection: Any, table_name: str) -> int:
    if not table_exists(connection, table_name):
        return 0
    return safe_int(connection.execute(
        f"SELECT COUNT(*) FROM {quote_identifier(table_name)}"
    ).fetchone()[0])


def resolve_branch_source_table(connection: Any) -> str:
    for table_name in (
        "tw_stock_trading_daily_report_secid_agg",
        "tw_stock_trading_daily_report",
    ):
        if table_row_count(connection, table_name) > 0:
            return table_name
    raise RuntimeError("找不到有資料的分點日資料表。")


def resolve_column(columns: Iterable[str], aliases: Iterable[str]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    for alias in aliases:
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return None


def detect_file_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        return "parquet"
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return "json"
    if suffix in {".csv", ".txt", ".tsv"}:
        return "csv"
    with path.open("rb") as source:
        return "parquet" if source.read(4) == b"PAR1" else "csv"


def load_group_map(connection: Any, group_map_path: str) -> dict[str, tuple[str, ...]]:
    source_table: str | None = None
    if group_map_path:
        source_path = Path(group_map_path).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"族群對照檔不存在：{source_path}")
        escaped = str(source_path).replace("'", "''")
        file_format = detect_file_format(source_path)
        if file_format == "parquet":
            reader = f"read_parquet('{escaped}')"
        elif file_format == "json":
            reader = f"read_json_auto('{escaped}')"
        else:
            reader = f"read_csv_auto('{escaped}', header=true, all_varchar=true)"
        connection.execute(f"CREATE OR REPLACE TEMP TABLE _cc_group_raw AS SELECT * FROM {reader}")
        source_table = "_cc_group_raw"
    else:
        source_table = next(
            (candidate for candidate in GROUP_TABLE_CANDIDATES if table_exists(connection, candidate)),
            None,
        )
    if source_table is None:
        raise RuntimeError(
            "找不到股票族群對照；請提供 --group-map，至少包含 stock_id 與 group_name。"
        )
    columns = table_columns(connection, source_table)
    stock_column = resolve_column(columns, GROUP_COLUMN_ALIASES["stock_id"])
    group_id_column = resolve_column(columns, GROUP_COLUMN_ALIASES["group_id"])
    group_name_column = resolve_column(columns, GROUP_COLUMN_ALIASES["group_name"])
    if not stock_column or (not group_id_column and not group_name_column):
        raise RuntimeError(
            f"族群對照欄位不足：columns={columns}；需要 stock_id 與 group_id/group_name。"
        )
    group_expression = quote_identifier(group_id_column or group_name_column)
    group_name_expression = quote_identifier(group_name_column or group_id_column)
    rows = connection.execute(
        f"SELECT {quote_identifier(stock_column)}, {group_expression}, {group_name_expression} "
        f"FROM {quote_identifier(source_table)}"
    ).fetchall()
    mapping: dict[str, set[str]] = defaultdict(set)
    normalized_rows: list[tuple[str, str, str]] = []
    for raw_stock, raw_group_id, raw_group_name in rows:
        try:
            stock_id = normalize_ticker(raw_stock)
        except ValueError:
            continue
        group_id = str(raw_group_id or raw_group_name or "UNGROUPED").strip()
        group_name = str(raw_group_name or raw_group_id or group_id).strip()
        mapping[stock_id].add(group_id)
        normalized_rows.append((stock_id, group_id, group_name))
    if not normalized_rows:
        raise RuntimeError("族群對照沒有可用的股票資料。")
    connection.execute("DROP TABLE IF EXISTS _cc_group_map")
    connection.execute(
        "CREATE TEMP TABLE _cc_group_map (stock_id VARCHAR, group_id VARCHAR, group_name VARCHAR)"
    )
    connection.executemany("INSERT INTO _cc_group_map VALUES (?, ?, ?)", normalized_rows)
    return {stock_id: tuple(sorted(groups)) for stock_id, groups in mapping.items()}


def resolve_analysis_dates(connection: Any, end_date: str) -> list[str]:
    source_table = resolve_branch_source_table(connection)
    maximum = connection.execute(
        f"SELECT MAX(date) FROM {quote_identifier(source_table)}"
    ).fetchone()[0]
    if maximum is None:
        raise RuntimeError("分點日資料表目前沒有資料。")
    resolved_end = str(maximum) if end_date.lower() == "latest" else end_date
    rows = connection.execute(
        f"""SELECT DISTINCT date FROM {quote_identifier(source_table)}
            WHERE date <= ? ORDER BY date DESC LIMIT ?""",
        [resolved_end, LOOKBACK_TRADING_DAYS],
    ).fetchall()
    return sorted(str(row[0]) for row in rows)


def load_branch_observations(
    connection: Any,
    group_map: dict[str, tuple[str, ...]],
    analysis_dates: list[str],
    branch_ids: set[str] | None = None,
    top_n: int | None = TOP_BRANCHES_PER_STOCK_DAY,
) -> list[dict[str, Any]]:
    if not analysis_dates:
        return []
    start_date, end_date = analysis_dates[0], analysis_dates[-1]
    source_table = resolve_branch_source_table(connection)
    if source_table == "tw_stock_trading_daily_report_secid_agg":
        base_sql = """
            SELECT date, stock_id, securities_trader_id AS branch_id,
                   securities_trader AS branch_name,
                   COALESCE(buy_volume, 0) AS buy_volume,
                   COALESCE(sell_volume, 0) AS sell_volume,
                   COALESCE(buy_price, 0) AS buy_price,
                   COALESCE(sell_price, 0) AS sell_price
            FROM tw_stock_trading_daily_report_secid_agg
        """
    else:
        base_sql = """
            SELECT date, stock_id, securities_trader_id AS branch_id,
                   MAX(securities_trader) AS branch_name,
                   SUM(COALESCE(buy, 0)) AS buy_volume,
                   SUM(COALESCE(sell, 0)) AS sell_volume,
                   SUM(COALESCE(buy, 0) * COALESCE(price, 0)) /
                       NULLIF(SUM(COALESCE(buy, 0)), 0) AS buy_price,
                   SUM(COALESCE(sell, 0) * COALESCE(price, 0)) /
                       NULLIF(SUM(COALESCE(sell, 0)), 0) AS sell_price
            FROM tw_stock_trading_daily_report
            GROUP BY date, stock_id, securities_trader_id
        """
    selected_join = ""
    if branch_ids:
        connection.execute("DROP TABLE IF EXISTS _cc_selected_branch")
        connection.execute("CREATE TEMP TABLE _cc_selected_branch (branch_id VARCHAR PRIMARY KEY)")
        connection.executemany(
            "INSERT INTO _cc_selected_branch VALUES (?)",
            [(branch_id,) for branch_id in sorted(branch_ids)],
        )
        selected_join = "INNER JOIN _cc_selected_branch s ON b.branch_id = s.branch_id"
    common_sql = f"""
        WITH branch_base AS ({base_sql}),
        enriched_all AS (
            SELECT b.*,
                   (buy_volume - sell_volume) AS net_volume,
                   (buy_volume * buy_price - sell_volume * sell_price) AS net_amount,
                   (buy_volume * buy_price + sell_volume * sell_price) AS gross_amount,
                   SUM(ABS(buy_volume - sell_volume)) OVER (
                       PARTITION BY b.date, b.stock_id
                   ) AS stock_total_abs_net
            FROM branch_base b
            INNER JOIN (SELECT DISTINCT stock_id FROM _cc_group_map) g USING (stock_id)
            WHERE b.date BETWEEN ? AND ?
        ),
        enriched AS (
            SELECT b.* FROM enriched_all b
            {selected_join}
        )
    """
    if top_n is None:
        query_sql = common_sql + """
        SELECT date, stock_id, branch_id, branch_name, buy_volume, sell_volume,
               buy_price, sell_price, net_volume, net_amount, gross_amount,
               stock_total_abs_net
        FROM enriched WHERE ABS(net_volume) > 0
        ORDER BY date, stock_id, ABS(net_amount) DESC, branch_id
        """
        parameters: list[Any] = [start_date, end_date]
    else:
        query_sql = common_sql + """,
        ranked AS (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY date, stock_id ORDER BY ABS(net_amount) DESC, branch_id
            ) AS importance_rank
            FROM enriched
            WHERE ABS(net_volume) > 0
        )
        SELECT date, stock_id, branch_id, branch_name, buy_volume, sell_volume,
               buy_price, sell_price, net_volume, net_amount, gross_amount,
               stock_total_abs_net
        FROM ranked WHERE importance_rank <= ?
        ORDER BY date, stock_id, importance_rank
        """
        parameters = [start_date, end_date, top_n]
    rows = connection.execute(query_sql, parameters).fetchall()
    columns = (
        "date", "stock_id", "branch_id", "branch_name", "buy_volume", "sell_volume",
        "buy_price", "sell_price", "net_volume", "net_amount", "gross_amount",
        "stock_total_abs_net",
    )
    observations: list[dict[str, Any]] = []
    for row in rows:
        item = dict(zip(columns, row))
        item["groups"] = group_map.get(str(item["stock_id"]), ("UNGROUPED",))
        observations.append(item)
    return observations


def load_institutional_flow(
    connection: Any,
    start_date: str,
    end_date: str,
) -> dict[tuple[str, str], dict[str, float]]:
    table_name = "tw_stock_institutional_investors_wide"
    if not table_exists(connection, table_name):
        return {}
    rows = connection.execute(f"""
        SELECT date, stock_id,
               COALESCE(Investment_Trust_buy, 0) - COALESCE(Investment_Trust_sell, 0),
               COALESCE(Dealer_self_buy, 0) - COALESCE(Dealer_self_sell, 0),
               COALESCE(Dealer_Hedging_buy, 0) - COALESCE(Dealer_Hedging_sell, 0),
               COALESCE(Foreign_Investor_buy, 0) - COALESCE(Foreign_Investor_sell, 0)
        FROM {quote_identifier(table_name)}
        WHERE date BETWEEN ? AND ?
    """, [start_date, end_date]).fetchall()
    return {
        (str(row[0]), str(row[1])): {
            "investment_trust": safe_float(row[2]),
            "dealer_self": safe_float(row[3]),
            "dealer_hedging": safe_float(row[4]),
            "foreign_investor": safe_float(row[5]),
        }
        for row in rows
    }


def load_market_context(
    connection: Any,
    start_date: str,
    end_date: str,
) -> dict[tuple[str, str], dict[str, Any]]:
    context: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
    if table_exists(connection, "tw_stock_price_daily"):
        rows = connection.execute("""
            SELECT date, stock_id, Trading_Volume, Trading_money,
                   open, max, min, close
            FROM tw_stock_price_daily WHERE date BETWEEN ? AND ?
            ORDER BY stock_id, date
        """, [start_date, end_date]).fetchall()
        by_stock: dict[str, list[tuple[Any, ...]]] = defaultdict(list)
        for row in rows:
            by_stock[str(row[1])].append(row)
        for stock_rows in by_stock.values():
            for index, row in enumerate(stock_rows):
                date_value, stock_id = str(row[0]), str(row[1])
                close = safe_float(row[7])
                prior_close = safe_float(stock_rows[index - 1][7]) if index >= 1 else 0.0
                close_5 = safe_float(stock_rows[index - 5][7]) if index >= 5 else 0.0
                close_20 = safe_float(stock_rows[index - 20][7]) if index >= 20 else 0.0
                trailing = stock_rows[max(0, index - 19):index + 1]
                prior_trailing = stock_rows[max(0, index - 20):index]
                highs = [safe_float(item[5]) for item in trailing if safe_float(item[5]) > 0]
                lows = [safe_float(item[6]) for item in trailing if safe_float(item[6]) > 0]
                volumes = [safe_float(item[2]) for item in trailing]
                previous_highs = [
                    safe_float(item[5]) for item in prior_trailing if safe_float(item[5]) > 0
                ]
                low_20 = min(lows) if lows else close
                high_20 = max(highs) if highs else close
                context[(date_value, stock_id)].update({
                    "trading_volume": safe_float(row[2]),
                    "trading_money": safe_float(row[3]),
                    "open": safe_float(row[4]), "high": safe_float(row[5]),
                    "low": safe_float(row[6]), "close": close,
                    "ret_1": safe_ratio(close, prior_close, 1.0) - 1.0 if prior_close else 0.0,
                    "ret_5": safe_ratio(close, close_5, 1.0) - 1.0 if close_5 else 0.0,
                    "ret_20": safe_ratio(close, close_20, 1.0) - 1.0 if close_20 else 0.0,
                    "price_position": safe_ratio(close - low_20, high_20 - low_20, 0.5),
                    "volume_ratio": safe_ratio(safe_float(row[2]), mean(volumes), 1.0),
                    "previous_high_20": max(previous_highs) if previous_highs else 0.0,
                })
    if table_exists(connection, "tw_stock_margin_short_daily"):
        rows = connection.execute("""
            SELECT date, stock_id,
                   MarginPurchaseTodayBalance - MarginPurchaseYesterdayBalance,
                   ShortSaleTodayBalance - ShortSaleYesterdayBalance
            FROM tw_stock_margin_short_daily WHERE date BETWEEN ? AND ?
        """, [start_date, end_date]).fetchall()
        for row in rows:
            context[(str(row[0]), str(row[1]))].update({
                "margin_delta": safe_float(row[2]), "short_delta": safe_float(row[3]),
            })
    if table_exists(connection, "tw_stock_day_trading_daily"):
        rows = connection.execute("""
            SELECT date, stock_id, Volume FROM tw_stock_day_trading_daily
            WHERE date BETWEEN ? AND ?
        """, [start_date, end_date]).fetchall()
        for row in rows:
            key = (str(row[0]), str(row[1]))
            trading_volume = safe_float(context[key].get("trading_volume"))
            context[key]["daytrade_ratio"] = safe_ratio(safe_float(row[2]), trading_volume)
    if table_exists(connection, "tw_stock_block_trade"):
        rows = connection.execute("""
            SELECT date, stock_id, SUM(volume) FROM tw_stock_block_trade
            WHERE date BETWEEN ? AND ? GROUP BY date, stock_id
        """, [start_date, end_date]).fetchall()
        for row in rows:
            context[(str(row[0]), str(row[1]))]["block_volume"] = safe_float(row[2])
    if table_exists(connection, "tw_stock_securities_lending_daily"):
        rows = connection.execute("""
            SELECT date, stock_id, SUM(volume) FROM tw_stock_securities_lending_daily
            WHERE date BETWEEN ? AND ? GROUP BY date, stock_id
        """, [start_date, end_date]).fetchall()
        for row in rows:
            context[(str(row[0]), str(row[1]))]["lending_volume"] = safe_float(row[2])
    return context


# =============================================================================
# 5. 摘要、行為日表、SSOT 寫入與輸出
# =============================================================================

def aggregate_circle_flows(
    observations: Iterable[dict[str, Any]],
    circles: dict[str, list[str]],
) -> dict[str, dict[tuple[str, str], dict[str, Any]]]:
    branch_to_circle = {
        branch_id: circle_id for circle_id, members in circles.items() for branch_id in members
    }
    result: dict[str, dict[tuple[str, str], dict[str, Any]]] = defaultdict(dict)
    for raw in observations:
        observation = normalize_observation(raw)
        circle_id = branch_to_circle.get(observation["branch_id"])
        if not circle_id:
            continue
        key = (observation["date"], observation["stock_id"])
        target = result[circle_id].setdefault(key, {
            "buy_volume": 0.0, "sell_volume": 0.0,
            "net_volume": 0.0, "net_amount": 0.0, "gross_amount": 0.0,
            "branches": set(), "groups": observation["groups"],
            "stock_total_abs_net": observation["stock_total_abs_net"],
        })
        target["net_volume"] += observation["net_volume"]
        target["buy_volume"] += observation["buy_volume"]
        target["sell_volume"] += observation["sell_volume"]
        target["net_amount"] += observation["net_amount"]
        target["gross_amount"] += observation["gross_amount"]
        target["branches"].add(observation["branch_id"])
    return result


def build_behavior_rows(
    snapshot_date: str,
    analysis_dates: list[str],
    circle_flows: dict[str, dict[tuple[str, str], dict[str, Any]]],
    circles: dict[str, list[str]],
    market_context: dict[tuple[str, str], dict[str, Any]],
    institutional_flow: dict[tuple[str, str], dict[str, float]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for circle_id, flows in circle_flows.items():
        by_stock: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for (date_value, stock_id), flow in flows.items():
            by_stock[stock_id].append((date_value, flow))
        for stock_id, active_stock_rows in by_stock.items():
            active_stock_rows.sort()
            flow_by_date = dict(active_stock_rows)
            first_date = active_stock_rows[0][0]
            default_groups = active_stock_rows[0][1]["groups"]
            stock_rows: list[tuple[str, dict[str, Any]]] = []
            for date_value in analysis_dates:
                if date_value < first_date:
                    continue
                if (date_value, stock_id) not in market_context and date_value not in flow_by_date:
                    continue
                stock_rows.append((date_value, flow_by_date.get(date_value, {
                    "buy_volume": 0.0, "sell_volume": 0.0,
                    "net_volume": 0.0, "net_amount": 0.0, "gross_amount": 0.0,
                    "branches": set(), "groups": default_groups, "stock_total_abs_net": 0.0,
                })))
            for index, (date_value, flow) in enumerate(stock_rows):
                recent_5 = stock_rows[max(0, index - 4):index + 1]
                recent_20 = stock_rows[max(0, index - 19):index + 1]
                amounts_5 = [item[1]["net_amount"] for item in recent_5]
                context = dict(market_context.get((date_value, stock_id), {}))
                institution = institutional_flow.get((date_value, stock_id), {})
                context.update({
                    "net_1": flow["net_volume"],
                    "net_5": sum(item[1]["net_volume"] for item in recent_5),
                    "net_20": sum(item[1]["net_volume"] for item in recent_20),
                    "gross_1": flow["buy_volume"] + flow["sell_volume"],
                    "buy_days_5": sum(item[1]["net_volume"] > 0 for item in recent_5),
                    "sell_days_5": sum(item[1]["net_volume"] < 0 for item in recent_5),
                    "active_members": len(flow["branches"]),
                    "circle_members": len(circles[circle_id]),
                    "flow_concentration": safe_ratio(
                        abs(flow["net_volume"]), flow["stock_total_abs_net"]
                    ),
                    "previous_net": stock_rows[index - 1][1]["net_volume"] if index else 0.0,
                    "amount_cv_5": coefficient_of_variation(amounts_5),
                    # 方向判定排除自營避險，避免將權證／ETF 避險誤認為法人看法。
                    "institution_net": (
                        institution.get("investment_trust", 0.0)
                        + institution.get("dealer_self", 0.0)
                        + institution.get("foreign_investor", 0.0)
                    ) if institution else None,
                })
                # 零流量日只參與 5/20 日窗口，不輸出空洞的行為訊號。
                if abs(flow["net_volume"]) <= 1e-12 and flow["gross_amount"] <= 1e-12:
                    continue
                signals = classify_daily_behavior(context)
                for rank, signal in enumerate(signals, start=1):
                    rows.append({
                        "snapshot_date": snapshot_date,
                        "date": date_value,
                        "circle_id": circle_id,
                        "stock_id": stock_id,
                        "group_id": ",".join(flow["groups"]),
                        "rank": rank,
                        **signal,
                        "evidence_json": json.dumps(signal["evidence"], ensure_ascii=False),
                    })
    return rows


def build_group_behavior_rows(
    snapshot_date: str,
    circle_flows: dict[str, dict[tuple[str, str], dict[str, Any]]],
    market_context: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    catalog = {item[0]: item for item in BEHAVIOR_CATALOG}
    rows: list[dict[str, Any]] = []
    for circle_id, flows in circle_flows.items():
        grouped: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
        for (date_value, stock_id), flow in flows.items():
            for group_id in flow["groups"]:
                grouped[(date_value, group_id)].append((stock_id, flow))
        for (date_value, group_id), items in grouped.items():
            if len(items) < 2:
                continue
            buys = [(stock_id, flow) for stock_id, flow in items if flow["net_volume"] > 0]
            sells = [(stock_id, flow) for stock_id, flow in items if flow["net_volume"] < 0]
            buy_breadth = safe_ratio(len(buys), len(items))
            sell_breadth = safe_ratio(len(sells), len(items))
            net_amount = sum(flow["net_amount"] for _stock_id, flow in items)
            candidates: list[tuple[str, float, dict[str, Any]]] = []
            if len(items) >= 3 and buy_breadth >= 0.70 and net_amount > 0:
                candidates.append(("WH-019", 70 + 30 * buy_breadth, {
                    "stock_count": len(items), "buy_breadth": buy_breadth,
                }))
            if buys and sells:
                bought_returns = [
                    safe_float(market_context.get((date_value, stock_id), {}).get("ret_20"))
                    for stock_id, _flow in buys
                ]
                sold_returns = [
                    safe_float(market_context.get((date_value, stock_id), {}).get("ret_20"))
                    for stock_id, _flow in sells
                ]
                if mean(bought_returns) + 0.02 < mean(sold_returns):
                    candidates.append(("WH-024", 75.0, {
                        "buy_count": len(buys), "sell_count": len(sells),
                        "bought_ret20": mean(bought_returns),
                        "sold_ret20": mean(sold_returns),
                    }))
                buy_amount = sum(abs(flow["net_amount"]) for _stock_id, flow in buys)
                sell_amount = sum(abs(flow["net_amount"]) for _stock_id, flow in sells)
                balance = min(buy_amount, sell_amount) / max(buy_amount, sell_amount, 1.0)
                if balance >= 0.55:
                    candidates.append(("WH-033", 60 + 40 * balance, {
                        "buy_count": len(buys), "sell_count": len(sells), "balance": balance,
                    }))
            is_month_end = date_value[8:10] >= "24"
            is_quarter_month = date_value[5:7] in {"03", "06", "09", "12"}
            if len(items) >= 5 and buys and sells and is_month_end and is_quarter_month:
                candidates.append(("WH-025", 80.0, {
                    "stock_count": len(items), "calendar_window": "quarter_end_candidate",
                }))
            for rank, (code, score, evidence) in enumerate(
                sorted(candidates, key=lambda item: (-item[1], item[0])), start=1
            ):
                _code, name, state, _availability = catalog[code]
                rows.append({
                    "snapshot_date": snapshot_date, "date": date_value,
                    "circle_id": circle_id, "stock_id": "*GROUP*", "group_id": group_id,
                    "rank": rank, "behavior_code": code, "behavior_name": name,
                    "state": state, "signal_score": round(min(score, 100.0), 2),
                    "evidence_json": json.dumps(evidence, ensure_ascii=False),
                })
    return rows


def build_cross_circle_behavior_rows(
    snapshot_date: str,
    circle_flows: dict[str, dict[tuple[str, str], dict[str, Any]]],
    market_context: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """辨識資金圈間的等量反向流；僅是換手候選，不代表帳戶關係。"""
    catalog = {item[0]: item for item in BEHAVIOR_CATALOG}
    by_stock_day: dict[tuple[str, str], list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    histories: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    for circle_id, flows in circle_flows.items():
        for (date_value, stock_id), flow in flows.items():
            if abs(flow["net_volume"]) <= 1e-12:
                continue
            by_stock_day[(date_value, stock_id)].append((circle_id, flow))
            histories[(circle_id, stock_id)].append((date_value, flow["net_volume"]))
    for values in histories.values():
        values.sort()

    rows: list[dict[str, Any]] = []
    for (date_value, stock_id), items in by_stock_day.items():
        buyers = [(circle_id, flow) for circle_id, flow in items if flow["net_volume"] > 0]
        sellers = [(circle_id, flow) for circle_id, flow in items if flow["net_volume"] < 0]
        market = market_context.get((date_value, stock_id), {})
        ret_1 = safe_float(market.get("ret_1"))
        volume_ratio = safe_float(market.get("volume_ratio"), 1.0)
        for (buyer_id, buyer_flow), (seller_id, seller_flow) in itertools.product(buyers, sellers):
            buyer_amount = abs(buyer_flow["net_volume"])
            seller_amount = abs(seller_flow["net_volume"])
            balance = min(buyer_amount, seller_amount) / max(buyer_amount, seller_amount, 1.0)
            if balance < 0.50:
                continue
            evidence = {
                "buyer_circle": buyer_id, "seller_circle": seller_id,
                "buyer_volume": buyer_amount, "seller_volume": seller_amount,
                "volume_balance": balance, "ret_1": ret_1,
                "volume_ratio": volume_ratio,
            }
            candidates: list[tuple[str, float]] = []
            if balance >= 0.75 and abs(ret_1) <= 0.02:
                candidates.append(("WH-021", 70.0 + 30.0 * balance))
            if volume_ratio >= HIGH_VOLUME_RATIO and abs(ret_1) <= 0.03:
                candidates.append(("WH-022", 75.0 + 15.0 * balance))
            buyer_history = [
                value for history_date, value in histories[(buyer_id, stock_id)]
                if history_date < date_value
            ][-BEHAVIOR_ROLLING_DAYS:]
            seller_history = [
                value for history_date, value in histories[(seller_id, stock_id)]
                if history_date < date_value
            ][-BEHAVIOR_ROLLING_DAYS:]
            buyer_was_quiet = abs(sum(buyer_history)) <= buyer_amount * 0.50
            seller_was_accumulating = sum(seller_history) > seller_amount * 0.50
            if buyer_was_quiet and seller_was_accumulating and ret_1 >= -0.01:
                candidates.append(("WH-023", 80.0))
            for rank, (code, score) in enumerate(
                sorted(candidates, key=lambda item: (-item[1], item[0])), start=1
            ):
                _code, name, state, _availability = catalog[code]
                rows.append({
                    "snapshot_date": snapshot_date, "date": date_value,
                    "circle_id": f"{seller_id}>{buyer_id}", "stock_id": stock_id,
                    "group_id": ",".join(buyer_flow["groups"]), "rank": rank,
                    "behavior_code": code, "behavior_name": name, "state": state,
                    "signal_score": round(min(score, 100.0), 2),
                    "evidence_json": json.dumps(evidence, ensure_ascii=False),
                })
    return rows


def create_analysis_tables(connection: Any) -> None:
    connection.execute("""
        CREATE TABLE IF NOT EXISTS capital_circle_edge (
            snapshot_date VARCHAR, circle_id VARCHAR, branch_a VARCHAR, branch_b VARCHAR,
            score DOUBLE, overlap_observations BIGINT, direction_match DOUBLE,
            signed_correlation DOUBLE, activity_overlap DOUBLE, group_profile DOUBLE,
            stock_profile DOUBLE, cost_similarity DOUBLE, volume_similarity DOUBLE,
            created_at VARCHAR
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS capital_circle_member (
            snapshot_date VARCHAR, circle_id VARCHAR, branch_id VARCHAR, branch_name VARCHAR,
            member_score DOUBLE, active_days BIGINT, stock_count BIGINT,
            dominant_group VARCHAR, created_at VARCHAR
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS capital_circle_summary (
            snapshot_date VARCHAR, circle_id VARCHAR, member_count BIGINT,
            mean_edge_score DOUBLE, confidence VARCHAR, dominant_group VARCHAR,
            suspected_style VARCHAR, institution_category VARCHAR,
            institution_correlation DOUBLE, institution_direction_hit DOUBLE,
            institution_observations BIGINT, created_at VARCHAR
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS capital_circle_behavior_daily (
            snapshot_date VARCHAR, date VARCHAR, circle_id VARCHAR, stock_id VARCHAR,
            group_id VARCHAR, rank BIGINT, behavior_code VARCHAR, behavior_name VARCHAR,
            state VARCHAR, signal_score DOUBLE, evidence_json VARCHAR, created_at VARCHAR
        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS capital_circle_behavior_catalog (
            behavior_code VARCHAR PRIMARY KEY, behavior_name VARCHAR,
            state VARCHAR, daily_data_status VARCHAR, updated_at VARCHAR
        )
    """)


def replace_snapshot_rows(
    connection: Any,
    snapshot_date: str,
    profiles: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    circles: dict[str, list[str]],
    circle_flows: dict[str, dict[tuple[str, str], dict[str, Any]]],
    institutional_flow: dict[tuple[str, str], dict[str, float]],
    behavior_rows: list[dict[str, Any]],
) -> dict[str, int]:
    create_analysis_tables(connection)
    timestamp = utc_now_iso()
    for table in (
        "capital_circle_edge", "capital_circle_member", "capital_circle_summary",
        "capital_circle_behavior_daily",
    ):
        connection.execute(f"DELETE FROM {quote_identifier(table)} WHERE snapshot_date = ?", [snapshot_date])
    connection.executemany("""
        INSERT OR REPLACE INTO capital_circle_behavior_catalog VALUES (?, ?, ?, ?, ?)
    """, [(code, name, state, status, timestamp) for code, name, state, status in BEHAVIOR_CATALOG])

    edge_rows = [(
        snapshot_date, edge["circle_id"], edge["branch_a"], edge["branch_b"],
        edge["score"], edge["overlap_observations"], edge["direction_match"],
        edge["signed_correlation"], edge["activity_overlap"], edge["group_profile"],
        edge["stock_profile"], edge["cost_similarity"], edge["volume_similarity"], timestamp,
    ) for edge in edges]
    if edge_rows:
        connection.executemany("INSERT INTO capital_circle_edge VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", edge_rows)

    member_rows: list[tuple[Any, ...]] = []
    summary_rows: list[tuple[Any, ...]] = []
    for circle_id, members in circles.items():
        circle_edges = [edge for edge in edges if edge["circle_id"] == circle_id]
        mean_edge_score = mean(edge["score"] for edge in circle_edges)
        group_totals: dict[str, float] = defaultdict(float)
        circle_flow_simple: dict[tuple[str, str], float] = {}
        for key, flow in circle_flows.get(circle_id, {}).items():
            circle_flow_simple[key] = flow["net_volume"]
            for group_id in flow["groups"]:
                group_totals[group_id] += abs(flow["net_amount"]) / max(len(flow["groups"]), 1)
        alignment = institutional_alignment(circle_flow_simple, institutional_flow)
        dominant_group = max(group_totals, key=group_totals.get, default="UNKNOWN")
        confidence = "high" if mean_edge_score >= CIRCLE_HIGH_CONFIDENCE else "medium"
        summary_rows.append((
            snapshot_date, circle_id, len(members), mean_edge_score, confidence,
            dominant_group, alignment["style"], alignment["best_category"],
            alignment["correlation"], alignment["direction_hit"],
            alignment["observations"], timestamp,
        ))
        for branch_id in members:
            branch_edges = [
                edge["score"] for edge in circle_edges
                if branch_id in {edge["branch_a"], edge["branch_b"]}
            ]
            profile = profiles[branch_id]
            dominant_branch_group = max(
                profile["group_profile"], key=lambda key: abs(profile["group_profile"][key]),
                default="UNKNOWN",
            )
            member_rows.append((
                snapshot_date, circle_id, branch_id, profile["branch_name"],
                mean(branch_edges), len(profile["active_dates"]),
                len(profile["stock_profile"]), dominant_branch_group, timestamp,
            ))
    if member_rows:
        connection.executemany("INSERT INTO capital_circle_member VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", member_rows)
    if summary_rows:
        connection.executemany("INSERT INTO capital_circle_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", summary_rows)
    insert_behavior_rows = [(
        row["snapshot_date"], row["date"], row["circle_id"], row["stock_id"],
        row["group_id"], row["rank"], row["behavior_code"], row["behavior_name"],
        row["state"], row["signal_score"], row["evidence_json"], timestamp,
    ) for row in behavior_rows]
    if insert_behavior_rows:
        connection.executemany("INSERT INTO capital_circle_behavior_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", insert_behavior_rows)
    connection.execute("CHECKPOINT")
    return {
        "circles": len(circles), "edges": len(edge_rows), "members": len(member_rows),
        "behavior_signals": len(insert_behavior_rows),
    }


def export_analysis_tables(connection: Any, output_root: Path) -> dict[str, dict[str, Any]]:
    output_root.mkdir(parents=True, exist_ok=True)
    parquet_root = output_root / "parquet"
    csv_root = output_root / "csv"
    parquet_root.mkdir(parents=True, exist_ok=True)
    csv_root.mkdir(parents=True, exist_ok=True)
    tables = (
        "capital_circle_summary", "capital_circle_member", "capital_circle_edge",
        "capital_circle_behavior_daily", "capital_circle_behavior_catalog",
    )
    results: dict[str, dict[str, Any]] = {}
    for table in tables:
        filename = table if EXPORT_WITHOUT_EXTENSION else f"{table}.parquet"
        parquet_path = parquet_root / filename
        csv_path = csv_root / (table if EXPORT_WITHOUT_EXTENSION else f"{table}.csv")
        csv_temp = csv_path.with_name(csv_path.name + ".tmp")
        escaped_parquet = str(parquet_path).replace("'", "''")
        escaped_csv = str(csv_temp).replace("'", "''")
        expressions: list[str] = []
        for column in table_columns(connection, table):
            if column == "created_at":
                continue
            if column in {"date", "snapshot_date"}:
                expressions.append(
                    f"strftime(CAST({quote_identifier(column)} AS DATE), '{DATE_OUTPUT_FORMAT}') "
                    f"AS {quote_identifier(column)}"
                )
            else:
                expressions.append(quote_identifier(column))
        select_sql = f"SELECT {', '.join(expressions)} FROM {quote_identifier(table)}"
        connection.execute(
            f"COPY ({select_sql}) TO '{escaped_parquet}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        connection.execute(
            f"COPY ({select_sql}) TO '{escaped_csv}' (FORMAT CSV, HEADER TRUE)"
        )
        with csv_temp.open("rb") as source, csv_path.open("wb") as target:
            target.write(b"\xef\xbb\xbf")
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        csv_temp.unlink(missing_ok=True)
        row_count = safe_int(connection.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(table)}"
        ).fetchone()[0])
        results[table] = {
            "rows": row_count, "parquet": str(parquet_path), "csv": str(csv_path),
        }
    return results


def write_audit_report(output_root: Path, report: dict[str, Any]) -> Path:
    audit_root = output_root / "audit"
    audit_root.mkdir(parents=True, exist_ok=True)
    path = audit_root / f"CapitalCircle_{report['run_id']}.json"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    return path


# =============================================================================
# 6. CLI 與主流程
# =============================================================================

def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    parser.add_argument("--duckdb", default=DEFAULT_DUCKDB_PATH)
    parser.add_argument("--group-map", default=DEFAULT_GROUP_MAP_PATH)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE, help="YYYY-MM-DD 或 latest")
    return parser


def run_analysis(arguments: argparse.Namespace) -> int:
    require_duckdb()
    database_path = Path(arguments.duckdb).expanduser().resolve()
    if not database_path.exists():
        raise FileNotFoundError(f"DuckDB 不存在：{database_path}")
    output_root = Path(arguments.output_root).expanduser().resolve()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    connection = duckdb.connect(str(database_path))
    try:
        group_map = load_group_map(connection, arguments.group_map)
        analysis_dates = resolve_analysis_dates(connection, arguments.end_date)
        snapshot_date = analysis_dates[-1]
        observations = load_branch_observations(connection, group_map, analysis_dates)
        profiles, edges, circles = build_capital_circles(observations)
        circle_branch_ids = {
            branch_id for members in circles.values() for branch_id in members
        }
        member_observations = load_branch_observations(
            connection, group_map, analysis_dates,
            branch_ids=circle_branch_ids, top_n=None,
        ) if circle_branch_ids else []
        institutional_flow = load_institutional_flow(
            connection, analysis_dates[0], analysis_dates[-1]
        )
        market_context = load_market_context(
            connection, analysis_dates[0], analysis_dates[-1]
        )
        circle_flows = aggregate_circle_flows(member_observations, circles)
        behavior_rows = build_behavior_rows(
            snapshot_date, analysis_dates, circle_flows, circles,
            market_context, institutional_flow,
        )
        behavior_rows.extend(
            build_group_behavior_rows(snapshot_date, circle_flows, market_context)
        )
        behavior_rows.extend(
            build_cross_circle_behavior_rows(snapshot_date, circle_flows, market_context)
        )
        counts = replace_snapshot_rows(
            connection, snapshot_date, profiles, edges, circles, circle_flows,
            institutional_flow, behavior_rows,
        )
        exports = export_analysis_tables(connection, output_root)
        report = {
            "engine": ENGINE_NAME, "engine_version": ENGINE_VERSION, "run_id": run_id,
            "created_at": utc_now_iso(), "snapshot_date": snapshot_date,
            "analysis_start": analysis_dates[0], "analysis_end": analysis_dates[-1],
            "trading_days": len(analysis_dates), "group_stock_count": len(group_map),
            "inference_observation_count": len(observations),
            "member_observation_count": len(member_observations), "counts": counts,
            "exports": exports,
            "interpretation_limit": (
                "分點為交易通路彙總；資金圈、法人型態與行為皆為統計候選，不是身分或違法認定。"
            ),
        }
        audit_path = write_audit_report(output_root, report)
    finally:
        connection.close()
    print(f"{ENGINE_NAME} {ENGINE_VERSION}")
    print(f"快照日期：{snapshot_date}；疑似資金圈：{counts['circles']}")
    print(f"成員：{counts['members']}；行為訊號：{counts['behavior_signals']}")
    print(f"稽核報告：{audit_path}")
    return 0


def main() -> int:
    parser = build_argument_parser()
    try:
        return run_analysis(parser.parse_args())
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
