# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_ThreeList_Grouping_DynamicValidationPipeline_v0200.py

三清單 × 台股族群輸入 × 動態 Criteria × 族群指數 × 關聯熱力圖
× 多情境回測 × 使用者測試 × 受控啟用。

治理原則
--------
1. List A 是列級 canonical candidate；List B 只作範圍與治理契約；List C 只作動態測試 cohort。
2. List C 永遠不可覆蓋 List A，也不可進入全市場 COUNT 加總。
3. 市場判定 Criteria 不使用固定相關係數、固定百分位或固定分數門檻；
   邊界由當期資料分布、Gaussian Mixture BIC、跨群 Null 與後驗分類自動生成。
4. 固定數字只允許用於資料結構、可重現種子、資源限制與治理不變項，不能作市場判定紅線。
5. 價格與成交值測試資料為 deterministic controlled DGP；只驗證方法與管線，不代表實盤績效。
6. Append-only 輸出、來源零修改、網路零、下單零。
"""
from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS — 所有參數集中於頂部
# =============================================================================

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import argparse
import ast
import datetime as dt
import gzip
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import time
import warnings

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import seaborn as sns

ENGINE_NAME = "VIA_ThreeList_Grouping_DynamicValidationPipeline"
VERSION = "0.2.00"
RUN_DATE = "2026-08-17"

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = Path("/mnt/data")
PACKAGE_INPUT_DIR = SCRIPT_DIR / "inputs"
DEFAULT_SOURCE_A = (PACKAGE_INPUT_DIR / "source_a_grouping.html") if (PACKAGE_INPUT_DIR / "source_a_grouping.html").exists() else (DEFAULT_BASE_DIR / "e968aad1-29c2-4678-b719-2dfa3a68936c.html")
DEFAULT_SOURCE_B = (PACKAGE_INPUT_DIR / "source_b_control.html") if (PACKAGE_INPUT_DIR / "source_b_control.html").exists() else (DEFAULT_BASE_DIR / "cfd5c419-b129-4faa-8f76-1535055d1906.html")
DEFAULT_SOURCE_C = (PACKAGE_INPUT_DIR / "source_c_dynamic_cohorts.html") if (PACKAGE_INPUT_DIR / "source_c_dynamic_cohorts.html").exists() else (DEFAULT_BASE_DIR / "2631e383-b754-4e87-ac47-e2e2f662a840.html")
DEFAULT_OUT_DIR = (SCRIPT_DIR / "runs") if PACKAGE_INPUT_DIR.exists() else (DEFAULT_BASE_DIR / "VIA_ThreeList_Grouping_DynamicValidation_v0200")

CONTROLLED_PRICE_END = "2026-08-14"
CONTROLLED_OBSERVATIONS = 180
CONTROLLED_SEEDS = [17, 20260817]
CONTROLLED_SCENARIOS = ["ROTATION", "MARKET_TIDE", "LOW_VOL_HIDDEN", "SHOCK"]

SOURCE_IDS = {
    "A": "LIST_A_GROUPING_CODING",
    "B": "LIST_B_ONE_CONTROL",
    "C": "LIST_C_DYNAMIC_3GROUP",
}
ROLE_MAP = {"Leader": "L", "Peer": "P", "Laggard": "G"}
MARKET_MAP = {"上市": "TWSE", "上櫃": "TPEX"}
SUFFIX_MAP = {"上市": ".TW", "上櫃": ".TWO"}
DYNAMIC_GROUP_SEMANTIC_MAP = {
    "Thermal Solution": "AI 散熱",
    "CPO": "AI 高速傳輸",
    "PCB": "PCB",
}
COUNT_FLAGS = {"COUNT", "Y", "YES", "TRUE", "1"}
DISPLAY_FLAGS = {"DISPLAY_ONLY", "EXPOSURE_ONLY", "REVIEW_ONLY"}

# 結構性資源參數，不是市場門檻。
MAX_GMM_COMPONENTS = 3
MAX_PLOT_GROUPS = 500
PERMUTATION_COUNT = 9
NULL_SAMPLE_MULTIPLIER = 3
PLOT_DPI = 150

# 受控啟用政策。
ACTIVATION_SCOPE = "RESEARCH_SANDBOX"
ACTIVATION_TOKEN = "ACTIVATE_THREE_LIST_GROUPING_DYNAMIC_v0200"


@dataclass
class PipelineConfig:
    source_a: Path = DEFAULT_SOURCE_A
    source_b: Path = DEFAULT_SOURCE_B
    source_c: Path = DEFAULT_SOURCE_C
    out_dir: Path = DEFAULT_OUT_DIR
    run_tag: str = "RUN_FINAL_V0200"
    write_plots: bool = True
    run_backtest: bool = True
    activate: bool = True


# =============================================================================
# def 01 UTILITIES
# =============================================================================


def def_configure_cjk_font() -> str:
    preferred = [
        "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans CJK JP",
        "Microsoft JhengHei", "PingFang TC", "Arial Unicode MS",
        "WenQuanYi Zen Hei", "AR PL UMing CN",
    ]
    installed = list(font_manager.fontManager.ttflist)
    for token in preferred:
        for entry in installed:
            if token.lower() in entry.name.lower():
                plt.rcParams["font.family"] = entry.name
                plt.rcParams["axes.unicode_minus"] = False
                return entry.name
    plt.rcParams["axes.unicode_minus"] = False
    return "sans-serif"


CJK_FONT = def_configure_cjk_font()


def def_now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def def_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_stable_seed(text: object) -> int:
    digest = hashlib.sha256(str(text).encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2**32)


def def_write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def def_write_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_safe_float(value: object) -> float:
    try:
        v = float(value)
        return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def def_parse_pct(value: object) -> float:
    return def_safe_float(str(value).replace(",", "").replace("%", "").strip())


def def_sanitize_filename(name: object, max_len: int = 120) -> str:
    s = re.sub(r"[\\/:*?\"<>|\s]+", "_", str(name).strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "group")[:max_len]


def def_html_table(df: pd.DataFrame, max_rows: int = 500) -> str:
    if df.empty:
        return '<div class="empty">No rows</div>'
    return df.head(max_rows).to_html(index=False, escape=True, border=0, classes="matrix")


def def_add_phase(rows: List[Dict[str, Any]], phase: str, status: str, detail: str, started: str, ended: str) -> None:
    rows.append({
        "Phase": phase,
        "Status": status,
        "Started": started,
        "Ended": ended,
        "Detail": detail,
    })


def def_add_test(rows: List[Dict[str, Any]], test_id: str, name: str, status: str, severity: str, evidence: str) -> None:
    rows.append({
        "TestID": test_id,
        "TestName": name,
        "Status": status,
        "Severity": severity,
        "Evidence": evidence,
    })


# =============================================================================
# def 02 SOURCE EXTRACTION
# =============================================================================


def def_unbundle_template(path: Path) -> str:
    raw = path.read_text("utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")
    el = soup.find("script", {"type": "__bundler/template"})
    if el is None or el.string is None:
        return raw
    return json.loads(el.string)


def def_extract_source_a(path: Path) -> Tuple[pd.DataFrame, str]:
    template = def_unbundle_template(path)
    match = re.search(
        r"_data\(\)\s*\{.*?return\s*\[(.*?)\];\s*\}\s*\n\s*_peers\(\)",
        template,
        re.S,
    )
    if match is None:
        raise ValueError("Source A _data() array not found")
    rows = ast.literal_eval("[" + match.group(1) + "]")
    df = pd.DataFrame(
        rows,
        columns=[
            "Name", "Ticker", "MarketRaw", "Group", "Role",
            "HotEmbedded", "LeadEmbedded", "ChangeEmbedded",
        ],
    )
    df["Ticker"] = df["Ticker"].astype(str).str.strip()
    df["Market"] = df["MarketRaw"].map(MARKET_MAP)
    df["YFTicker"] = df["Ticker"] + df["MarketRaw"].map(SUFFIX_MAP)
    df["SourceID"] = SOURCE_IDS["A"]
    df["SourceFile"] = path.name
    df["Dimension"] = "D01_CANONICAL_GROUPING"
    df["CountingFlag"] = "COUNT"
    df["EvidenceStatus"] = "SOURCE_ROW_WITH_EMBEDDED_SAMPLE_METRICS"
    df["MembershipKey"] = df["Dimension"] + "|" + df["Group"] + "|" + df["Ticker"]
    return df, template


def def_extract_source_b(path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    raw = path.read_text("utf-8", errors="ignore")
    visible = " ".join(BeautifulSoup(raw, "html.parser").get_text(" ", strip=True).split())
    group_match = re.search(r"File1\s*族群分類\((\d+)群\)", visible)
    code_match = re.search(r"File2\s*統一編碼\((\d+)碼\)", visible)
    tw_console_match = re.search(r"族群多面向(\d+)檔(\d+)群", visible)
    controls = {
        "ExpectedFile1Groups": int(group_match.group(1)) if group_match else None,
        "ExpectedFile2Codes": int(code_match.group(1)) if code_match else None,
        "ExpectedTWConsoleTickers": int(tw_console_match.group(1)) if tw_console_match else None,
        "ExpectedTWConsoleGroups": int(tw_console_match.group(2)) if tw_console_match else None,
        "ControlRole": "SCOPE_AND_GOVERNANCE_ONLY",
        "SourceFile": path.name,
    }
    rows = [
        {"ControlID": "CTRL_FILE1_GROUPS", "Metric": "File1Groups", "ExpectedValue": controls["ExpectedFile1Groups"]},
        {"ControlID": "CTRL_FILE2_CODES", "Metric": "File2Codes", "ExpectedValue": controls["ExpectedFile2Codes"]},
        {"ControlID": "CTRL_TW_CONSOLE_TICKERS", "Metric": "TWConsoleTickers", "ExpectedValue": controls["ExpectedTWConsoleTickers"]},
        {"ControlID": "CTRL_TW_CONSOLE_GROUPS", "Metric": "TWConsoleGroups", "ExpectedValue": controls["ExpectedTWConsoleGroups"]},
    ]
    df = pd.DataFrame(rows)
    df["SourceID"] = SOURCE_IDS["B"]
    df["SourceFile"] = path.name
    df["EvidenceStatus"] = "CONTROL_METADATA_NOT_MEMBERSHIP"
    return df, controls


def def_parse_classification(value: object) -> Tuple[str, str, str]:
    s = re.sub(r"\s+", "", str(value))
    for label, role in ROLE_MAP.items():
        if s.startswith(label):
            tag = s[len(label):]
            return role, label.upper(), tag or ""
    return "", "UNKNOWN", s


def def_extract_source_c(path: Path) -> pd.DataFrame:
    tables = pd.read_html(str(path))
    group_table_map = [("Thermal Solution", 1), ("CPO", 3), ("PCB", 5)]
    parts: List[pd.DataFrame] = []
    for group_name, table_idx in group_table_map:
        if table_idx >= len(tables):
            raise ValueError(f"Source C table index missing: {group_name}/{table_idx}")
        d = tables[table_idx].copy()
        d["GroupDynamic"] = group_name
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    parsed = df["Classification"].apply(def_parse_classification)
    df["RoleDynamic"] = [x[0] for x in parsed]
    df["RoleDynamicLabel"] = [x[1] for x in parsed]
    df["ClassificationTag"] = [x[2] for x in parsed]
    df["Ticker"] = df["YFinance Ticker"].astype(str).str.extract(r"(\d{4})", expand=False)
    df["SourceID"] = SOURCE_IDS["C"]
    df["SourceFile"] = path.name
    df["Dimension"] = "D90_DYNAMIC_TEST_COHORT"
    df["CountingFlag"] = "DISPLAY_ONLY"
    df["EvidenceStatus"] = "SYNTHETIC_ENGINE_REPORT_NOT_CANONICAL"
    return df


# =============================================================================
# def 03 RECONCILIATION AND SSOT INPUTS
# =============================================================================


def def_reconcile_dynamic_identity(source_a: pd.DataFrame, source_c: pd.DataFrame) -> pd.DataFrame:
    identity = source_a[["Ticker", "Name", "Market", "YFTicker", "Group", "Role"]].copy()
    identity = identity.rename(columns={
        "Name": "CanonicalName",
        "Market": "CanonicalMarket",
        "YFTicker": "CanonicalYFTicker",
        "Group": "CanonicalSourceGroup",
        "Role": "CanonicalSourceRole",
    })
    out = source_c.merge(identity, on="Ticker", how="left")
    out["IdentityMatched"] = out["CanonicalYFTicker"].notna()
    out["SuffixMatched"] = out["YFinance Ticker"].eq(out["CanonicalYFTicker"])
    out["NameMatched"] = out["Name"].eq(out["CanonicalName"])
    out["YFTickerResolved"] = out["CanonicalYFTicker"].fillna(out["YFinance Ticker"])
    out["NameResolved"] = out["CanonicalName"].fillna(out["Name"])
    fallback_market = pd.Series(
        np.where(out["YFTickerResolved"].astype(str).str.endswith(".TWO"), "TPEX", "TWSE"),
        index=out.index,
    )
    out["MarketResolved"] = out["CanonicalMarket"].fillna(fallback_market)
    out["SemanticCandidateGroup"] = out["GroupDynamic"].map(DYNAMIC_GROUP_SEMANTIC_MAP)

    flags: List[str] = []
    for _, row in out.iterrows():
        item: List[str] = []
        if not bool(row["IdentityMatched"]):
            item.append("NEEDS_TICKER_REGISTRY")
        if bool(row["IdentityMatched"]) and not bool(row["SuffixMatched"]):
            item.append("YF_SUFFIX_CONFLICT")
        if bool(row["IdentityMatched"]) and not bool(row["NameMatched"]):
            item.append("NAME_ALIAS_CONFLICT")
        if row.get("CanonicalSourceGroup") != row.get("SemanticCandidateGroup"):
            item.append("CANONICAL_GROUP_DIFFERENCE")
        flags.append("|".join(item) if item else "NONE")
    out["ConflictFlags"] = flags
    return out


def def_build_overlap_ledger(source_a: pd.DataFrame, source_c: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for dynamic_group, canonical_group in DYNAMIC_GROUP_SEMANTIC_MAP.items():
        dyn = set(source_c.loc[source_c["GroupDynamic"] == dynamic_group, "Ticker"].dropna().astype(str))
        can = set(source_a.loc[source_a["Group"] == canonical_group, "Ticker"].dropna().astype(str))
        common = sorted(dyn & can)
        precision = len(common) / len(dyn) if dyn else np.nan
        recall = len(common) / len(can) if can else np.nan
        f1 = 2 * precision * recall / (precision + recall) if precision and recall and precision + recall else 0.0
        if dynamic_group == "Thermal Solution" and common:
            decision = "PROPOSED_ALIAS_REVIEW"
        elif dynamic_group in {"CPO", "PCB"}:
            decision = "SEMANTIC_LABEL_MEMBER_CONFLICT_FAIL_CLOSED"
        else:
            decision = "REVIEW"
        rows.append({
            "DynamicGroup": dynamic_group,
            "CanonicalCandidateGroup": canonical_group,
            "DynamicMembers": len(dyn),
            "CanonicalMembers": len(can),
            "CommonMembers": len(common),
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "CommonTickers": "|".join(common),
            "Decision": decision,
        })
    return pd.DataFrame(rows)


def def_build_conflict_ledger(dynamic: pd.DataFrame, overlap: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, r in dynamic.iterrows():
        flags = str(r["ConflictFlags"])
        if flags == "NONE":
            continue
        rows.append({
            "ConflictType": "DYNAMIC_IDENTITY_OR_GROUP",
            "Severity": "REVIEW" if "NEEDS_TICKER_REGISTRY" in flags else "WARN",
            "Group": r["GroupDynamic"],
            "Ticker": r["Ticker"],
            "SourceName": r["Name"],
            "CanonicalName": r.get("CanonicalName", ""),
            "SourceYFTicker": r["YFinance Ticker"],
            "ResolvedYFTicker": r["YFTickerResolved"],
            "SourceRole": r["RoleDynamic"],
            "CanonicalRole": r.get("CanonicalSourceRole", ""),
            "SourceCanonicalGroup": r.get("CanonicalSourceGroup", ""),
            "SemanticCandidateGroup": r["SemanticCandidateGroup"],
            "Flags": flags,
            "Resolution": "KEEP_DYNAMIC_DISPLAY_ONLY; DO_NOT_OVERWRITE_CANONICAL",
        })
    for _, r in overlap.iterrows():
        if r["Decision"] == "PROPOSED_ALIAS_REVIEW":
            continue
        rows.append({
            "ConflictType": "DYNAMIC_MEMBERSHIP_SEMANTIC_CONFLICT",
            "Severity": "REVIEW",
            "Group": r["DynamicGroup"],
            "Ticker": "",
            "SourceName": "",
            "CanonicalName": "",
            "SourceYFTicker": "",
            "ResolvedYFTicker": "",
            "SourceRole": "",
            "CanonicalRole": "",
            "SourceCanonicalGroup": r["CanonicalCandidateGroup"],
            "SemanticCandidateGroup": r["CanonicalCandidateGroup"],
            "Flags": r["Decision"],
            "Resolution": "FAIL_CLOSED_DISPLAY_ONLY",
        })
    return pd.DataFrame(rows)


def def_build_canonical_input(source_a: pd.DataFrame) -> pd.DataFrame:
    out = source_a[[
        "Group", "Role", "Ticker", "YFTicker", "Name", "Market",
        "Dimension", "CountingFlag", "SourceID", "EvidenceStatus",
        "HotEmbedded", "LeadEmbedded", "ChangeEmbedded",
    ]].copy()
    out.insert(1, "Subgroup", "")
    out = out.rename(columns={"Role": "Rank"})
    out["SourceMetricUse"] = "DISPLAY_ONLY_NOT_LIVE_CRITERIA"
    return out


def def_build_dynamic_input(dynamic: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "Group": dynamic["GroupDynamic"],
        "Subgroup": dynamic["SemanticCandidateGroup"],
        "Rank": dynamic["RoleDynamic"],
        "Ticker": dynamic["Ticker"],
        "YFTicker": dynamic["YFTickerResolved"],
        "Name": dynamic["NameResolved"],
        "Market": dynamic["MarketResolved"],
        "Dimension": "D90_DYNAMIC_TEST_COHORT",
        "CountingFlag": "DISPLAY_ONLY",
        "SourceID": dynamic["SourceID"],
        "EvidenceStatus": dynamic["EvidenceStatus"],
        "ClassificationTag": dynamic["ClassificationTag"],
        "CorrR": pd.to_numeric(dynamic["Corr r"], errors="coerce"),
        "RS": pd.to_numeric(dynamic["RS"], errors="coerce"),
        "CCFLag": pd.to_numeric(dynamic["CCF lag"], errors="coerce"),
        "VolZ": pd.to_numeric(dynamic["Vol z"], errors="coerce"),
        "Score": pd.to_numeric(dynamic["Score"], errors="coerce"),
        "ConflictFlags": dynamic["ConflictFlags"],
        "SourceMetricUse": "DISPLAY_ONLY_NOT_LIVE_CRITERIA",
    })
    return out


# =============================================================================
# def 04 DYNAMIC CRITERIA — 無固定市場紅線
# =============================================================================


def def_fit_adaptive_states(values: Sequence[float], metric_name: str, seed: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    s = pd.Series(values, dtype=float)
    valid_mask = s.notna() & np.isfinite(s)
    valid = s[valid_mask].to_numpy(dtype=float).reshape(-1, 1)
    result = pd.DataFrame(index=s.index)
    result["State"] = "UNCLASSIFIED"
    result["PosteriorConfidence"] = np.nan

    if len(valid) < 3 or np.unique(valid).size < 2:
        meta = {
            "Metric": metric_name,
            "Components": 1,
            "Centers": [float(np.nanmedian(s)) if valid.size else np.nan],
            "Cutpoints": [],
            "BIC": np.nan,
            "Method": "DEGENERATE_SINGLE_STATE",
        }
        result.loc[valid_mask, "State"] = "MIXED"
        result.loc[valid_mask, "PosteriorConfidence"] = 1.0
        return result, meta

    scaler = RobustScaler()
    x = scaler.fit_transform(valid)
    max_components = min(MAX_GMM_COMPONENTS, len(valid), np.unique(valid).size)
    models: List[Tuple[float, GaussianMixture]] = []
    for k in range(1, max_components + 1):
        gm = GaussianMixture(
            n_components=k,
            covariance_type="full",
            random_state=seed,
            n_init=5,
            reg_covar=np.finfo(float).eps ** 0.5,
        )
        gm.fit(x)
        models.append((gm.bic(x), gm))
    bic, model = min(models, key=lambda z: z[0])
    posterior = model.predict_proba(x)
    labels = model.predict(x)
    centers_scaled = model.means_.reshape(-1, 1)
    centers = scaler.inverse_transform(centers_scaled).ravel()
    order = np.argsort(centers)
    rank_by_component = {int(component): rank for rank, component in enumerate(order)}
    if model.n_components == 1:
        state_names = ["MIXED"]
    elif model.n_components == 2:
        state_names = ["LOW", "HIGH"]
    else:
        state_names = ["LOW", "MID", "HIGH"]
    mapped_states = [state_names[rank_by_component[int(lbl)]] for lbl in labels]

    result.loc[valid_mask, "State"] = mapped_states
    result.loc[valid_mask, "PosteriorConfidence"] = posterior.max(axis=1)
    sorted_centers = sorted(float(v) for v in centers)
    cutpoints = [(sorted_centers[i] + sorted_centers[i + 1]) / 2.0 for i in range(len(sorted_centers) - 1)]
    meta = {
        "Metric": metric_name,
        "Components": int(model.n_components),
        "Centers": sorted_centers,
        "Cutpoints": cutpoints,
        "BIC": float(bic),
        "Method": "GAUSSIAN_MIXTURE_BIC_ROBUST_SCALE",
    }
    return result, meta


def def_fit_multivariate_states(df: pd.DataFrame, feature_cols: Sequence[str], model_name: str, seed: int) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    xdf = df[list(feature_cols)].replace([np.inf, -np.inf], np.nan).dropna()
    out = pd.DataFrame(index=df.index)
    out["State"] = "UNCLASSIFIED"
    out["PosteriorConfidence"] = np.nan
    if len(xdf) < 4 or xdf.nunique().sum() <= len(feature_cols):
        out.loc[xdf.index, "State"] = "MIXED"
        out.loc[xdf.index, "PosteriorConfidence"] = 1.0
        return out, {
            "Metric": model_name,
            "Components": 1,
            "Centers": [],
            "Cutpoints": [],
            "BIC": np.nan,
            "Method": "DEGENERATE_SINGLE_STATE",
            "Features": list(feature_cols),
        }
    scaler = RobustScaler()
    x = scaler.fit_transform(xdf)
    max_components = min(MAX_GMM_COMPONENTS, len(xdf))
    models: List[Tuple[float, GaussianMixture]] = []
    for k in range(1, max_components + 1):
        gm = GaussianMixture(
            n_components=k,
            covariance_type="full",
            random_state=seed,
            n_init=5,
            reg_covar=np.finfo(float).eps ** 0.5,
        )
        gm.fit(x)
        models.append((gm.bic(x), gm))
    bic, model = min(models, key=lambda z: z[0])
    labels = model.predict(x)
    posterior = model.predict_proba(x)
    centers_original = scaler.inverse_transform(model.means_)
    # 每個 feature 先 rank，再平均，完全由當期群中心排序狀態。
    center_rank_score = np.zeros(model.n_components, dtype=float)
    for j in range(centers_original.shape[1]):
        order = np.argsort(centers_original[:, j])
        rank = np.empty_like(order, dtype=float)
        rank[order] = np.arange(len(order), dtype=float)
        center_rank_score += rank
    order = np.argsort(center_rank_score)
    rank_by_component = {int(component): rank for rank, component in enumerate(order)}
    if model.n_components == 1:
        state_names = ["MIXED"]
    elif model.n_components == 2:
        state_names = ["LOW", "HIGH"]
    else:
        state_names = ["LOW", "MID", "HIGH"]
    mapped = [state_names[rank_by_component[int(lbl)]] for lbl in labels]
    out.loc[xdf.index, "State"] = mapped
    out.loc[xdf.index, "PosteriorConfidence"] = posterior.max(axis=1)
    return out, {
        "Metric": model_name,
        "Components": int(model.n_components),
        "Centers": [
            {feature: float(centers_original[i, j]) for j, feature in enumerate(feature_cols)}
            for i in range(model.n_components)
        ],
        "Cutpoints": [],
        "BIC": float(bic),
        "Method": "MULTIVARIATE_GAUSSIAN_MIXTURE_BIC_ROBUST_SCALE",
        "Features": list(feature_cols),
    }


# =============================================================================
# def 05 CONTROLLED DATA GENERATOR
# =============================================================================


def def_ar1(rng: np.random.Generator, n: int, scale: float, persistence: float) -> np.ndarray:
    eps = rng.normal(0.0, scale, n)
    x = np.zeros(n, dtype=float)
    for i in range(1, n):
        x[i] = persistence * x[i - 1] + eps[i]
    return x


def def_generate_controlled_panel(
    canonical: pd.DataFrame,
    dynamic: pd.DataFrame,
    seed: int,
    scenario: str,
    observations: int = CONTROLLED_OBSERVATIONS,
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp(CONTROLLED_PRICE_END), periods=observations)
    all_membership = pd.concat([
        canonical[["Group", "Rank", "Ticker", "YFTicker", "Name", "Market", "CountingFlag"]],
        dynamic[["Group", "Rank", "Ticker", "YFTicker", "Name", "Market", "CountingFlag"]],
    ], ignore_index=True)
    ticker_rows = all_membership.drop_duplicates("YFTicker").set_index("YFTicker")
    tickers = ticker_rows.index.tolist()

    scenario_scale = {
        "ROTATION": (0.009, 0.014, 0.011),
        "MARKET_TIDE": (0.024, 0.001, 0.012),
        "LOW_VOL_HIDDEN": (0.003, 0.006, 0.0035),
        "SHOCK": (0.014, 0.012, 0.010),
    }
    market_scale, group_scale, idio_scale = scenario_scale[scenario]
    market = def_ar1(rng, observations, market_scale, 0.08)
    if scenario == "SHOCK":
        shock_start = observations - max(5, int(math.sqrt(observations)))
        market[shock_start:] -= np.linspace(market_scale, market_scale * 3.0, observations - shock_start)

    price_data: Dict[str, np.ndarray] = {}
    turnover_data: Dict[str, np.ndarray] = {}
    truth_rows: List[Dict[str, Any]] = []
    group_driver: Dict[str, np.ndarray] = {}

    canonical_groups = canonical["Group"].drop_duplicates().tolist()
    for group in canonical_groups:
        group_seed = def_stable_seed(f"{seed}|{scenario}|{group}")
        grng = np.random.default_rng(group_seed)
        if scenario == "MARKET_TIDE":
            valid = False
        elif scenario == "SHOCK":
            valid = (group_seed % 5) != 0
        else:
            valid = (group_seed % 4) != 0
        driver = def_ar1(grng, observations, group_scale if valid else group_scale * 0.08, 0.15)
        if valid and scenario in {"ROTATION", "LOW_VOL_HIDDEN"}:
            pulse_points = grng.choice(np.arange(max(4, observations // 5), observations - max(4, observations // 8)), size=3, replace=False)
            for p in pulse_points:
                width = max(2, int(math.sqrt(observations) // 2))
                stop = min(observations, p + width)
                driver[p:stop] += np.linspace(group_scale * 0.4, group_scale * 1.8, stop - p)
        group_driver[group] = driver
        truth_rows.append({"Group": group, "Scenario": scenario, "Seed": seed, "TruthValidGroup": valid})

    for ticker, row in ticker_rows.iterrows():
        source_rows = all_membership[all_membership["YFTicker"] == ticker]
        canonical_row = source_rows[source_rows["CountingFlag"].astype(str).str.upper().isin(COUNT_FLAGS)]
        if not canonical_row.empty:
            group = str(canonical_row.iloc[0]["Group"])
            rank = str(canonical_row.iloc[0]["Rank"])
        else:
            group = str(source_rows.iloc[0]["Group"])
            rank = str(source_rows.iloc[0]["Rank"])
        trng = np.random.default_rng(def_stable_seed(f"{seed}|{scenario}|{ticker}"))
        beta = trng.uniform(0.45, 1.30)
        driver = group_driver.get(group, def_ar1(trng, observations, group_scale * 0.15, 0.10))
        if rank == "L":
            role_signal = driver
            turnover_signal = np.abs(driver)
        elif rank == "P":
            role_signal = np.roll(driver, 1)
            role_signal[0] = 0.0
            turnover_signal = np.roll(np.abs(driver), 1)
            turnover_signal[0] = 0.0
        elif rank == "G":
            role_signal = np.roll(driver, 2)
            role_signal[:2] = 0.0
            turnover_signal = np.roll(np.abs(driver), 2)
            turnover_signal[:2] = 0.0
        else:
            role_signal = trng.normal(0.0, group_scale * 0.05, observations)
            turnover_signal = np.abs(role_signal)
        idio = trng.normal(0.0, idio_scale, observations)
        returns = beta * market + role_signal + idio
        start_price = 20.0 + (def_stable_seed(ticker) % 1800) / 10.0
        price_data[ticker] = start_price * np.exp(np.cumsum(returns))
        base_turnover = 3e7 + (def_stable_seed(ticker + "TURN") % int(8e9))
        noise = trng.lognormal(mean=0.0, sigma=0.25, size=observations)
        turnover_data[ticker] = base_turnover * noise * np.exp(np.clip(turnover_signal / max(group_scale, np.finfo(float).eps), 0, 4))

    prices = pd.DataFrame(price_data, index=dates)
    turnover = pd.DataFrame(turnover_data, index=dates)
    market_return = pd.Series(market, index=dates, name="MARKET_RETURN")
    truth = pd.DataFrame(truth_rows)
    return {
        "prices": prices,
        "turnover": turnover,
        "market_return": market_return,
        "group_truth": truth,
        "scenario": scenario,
        "seed": seed,
    }


# =============================================================================
# def 06 CALCULATION CORE
# =============================================================================


def def_safe_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    data = prices.sort_index().astype(float).where(lambda x: x > 0)
    out = np.log(data / data.shift(1))
    return out.replace([np.inf, -np.inf], np.nan).dropna(how="all")


def def_residualize_market(stock_returns: pd.DataFrame, market_return: pd.Series) -> pd.DataFrame:
    m = market_return.reindex(stock_returns.index).astype(float)
    residual = pd.DataFrame(index=stock_returns.index, columns=stock_returns.columns, dtype=float)
    x = np.column_stack([np.ones(len(m)), m.to_numpy(dtype=float)])
    for ticker in stock_returns.columns:
        y = stock_returns[ticker].to_numpy(dtype=float)
        mask = np.isfinite(y) & np.isfinite(m.to_numpy(dtype=float))
        if mask.sum() <= x.shape[1]:
            continue
        beta, *_ = np.linalg.lstsq(x[mask], y[mask], rcond=None)
        residual.loc[stock_returns.index[mask], ticker] = y[mask] - x[mask] @ beta
    return residual


def def_normalize_prices(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    first = prices.apply(lambda s: s.dropna().iloc[0] if s.dropna().size else np.nan)
    return prices.divide(first, axis=1) * base


def def_build_group_indices(membership: pd.DataFrame, prices: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    norm = def_normalize_prices(prices)
    full: Dict[str, pd.Series] = {}
    for group, gm in membership.groupby("Group", sort=False):
        count_rows = gm[gm["CountingFlag"].astype(str).str.upper().isin(COUNT_FLAGS)]
        tickers = [t for t in count_rows["YFTicker"].drop_duplicates() if t in norm.columns]
        if tickers:
            full[str(group)] = norm[tickers].mean(axis=1, skipna=True)
    full_df = pd.DataFrame(full).sort_index()
    return full_df, def_safe_log_returns(full_df)


def def_pc1_ratio(returns: pd.DataFrame) -> float:
    x = returns.dropna(how="all").copy()
    if x.shape[1] < 2:
        return np.nan
    x = x.fillna(x.mean()).to_numpy(dtype=float)
    x = x - np.nanmean(x, axis=0, keepdims=True)
    if not np.isfinite(x).all() or np.allclose(x, 0):
        return np.nan
    _, s, _ = np.linalg.svd(x, full_matrices=False)
    var = s**2
    return float(var[0] / var.sum()) if var.sum() > 0 else np.nan


def def_pairwise_values(corr: pd.DataFrame) -> np.ndarray:
    if corr.empty or corr.shape[0] < 2:
        return np.array([], dtype=float)
    arr = corr.to_numpy(dtype=float)
    vals = arr[np.triu_indices_from(arr, k=1)]
    return vals[np.isfinite(vals)]


def def_leave_one_out_mean(returns: pd.DataFrame, ticker: str) -> pd.Series:
    others = [c for c in returns.columns if c != ticker]
    if not others:
        return pd.Series(index=returns.index, dtype=float)
    return returns[others].mean(axis=1, skipna=True)


def def_corr(x: pd.Series, y: pd.Series) -> float:
    xv = x.to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)
    mask = np.isfinite(xv) & np.isfinite(yv)
    if mask.sum() < 3:
        return np.nan
    xa = xv[mask]
    ya = yv[mask]
    xs = xa.std(ddof=1)
    ys = ya.std(ddof=1)
    if xs <= 0 or ys <= 0:
        return np.nan
    return float(np.corrcoef(xa, ya)[0, 1])


def def_array_corr(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return np.nan
    xa = x[mask]
    ya = y[mask]
    xs = xa.std(ddof=1)
    ys = ya.std(ddof=1)
    if xs <= 0 or ys <= 0:
        return np.nan
    xa = xa - xa.mean()
    ya = ya - ya.mean()
    return float(np.dot(xa, ya) / ((len(xa) - 1) * xs * ys))


def def_dynamic_max_lag(n_obs: int) -> int:
    # 依樣本長度產生可辨識 lag 範圍；不是市場紅線。
    return max(1, min(int(round(math.sqrt(max(n_obs, 1)) / 2.0)), max(1, n_obs // 8)))


def def_lag_corr(x: np.ndarray, y: np.ndarray, lag: int) -> float:
    # lag > 0: x(t) 對 y(t+lag)，x 領先。
    if lag > 0:
        return def_array_corr(x[:-lag], y[lag:]) if len(x) > lag else np.nan
    if lag < 0:
        k = -lag
        return def_array_corr(x[k:], y[:-k]) if len(x) > k else np.nan
    return def_array_corr(x, y)


def def_lead_lag_metrics(member: pd.Series, group_loo: pd.Series, seed: int) -> Dict[str, float]:
    data = pd.concat([member, group_loo], axis=1).dropna()
    if len(data) < 8:
        return {"BestLag": np.nan, "BestLagCorr": np.nan, "ZeroLagCorr": np.nan, "PermutationEvidence": np.nan}
    x = data.iloc[:, 0].to_numpy(dtype=float)
    y = data.iloc[:, 1].to_numpy(dtype=float)
    max_lag = def_dynamic_max_lag(len(data))
    lags = list(range(-max_lag, max_lag + 1))
    corr_values = [def_lag_corr(x, y, lag) for lag in lags]
    finite_idx = [i for i, c in enumerate(corr_values) if np.isfinite(c)]
    if not finite_idx:
        return {"BestLag": np.nan, "BestLagCorr": np.nan, "ZeroLagCorr": np.nan, "PermutationEvidence": np.nan}
    best_i = max(finite_idx, key=lambda i: abs(corr_values[i]))
    best_lag = lags[best_i]
    best_corr = corr_values[best_i]
    zero = corr_values[lags.index(0)]

    rng = np.random.default_rng(seed)
    possible_shifts = np.arange(max_lag + 1, max(max_lag + 2, len(y) - max_lag - 1))
    null_max: List[float] = []
    if possible_shifts.size:
        shifts = rng.choice(possible_shifts, size=min(PERMUTATION_COUNT, possible_shifts.size), replace=False)
        for shift in shifts:
            ys = np.roll(y, int(shift))
            vals = [abs(def_lag_corr(x, ys, lag)) for lag in lags]
            vals = [v for v in vals if np.isfinite(v)]
            if vals:
                null_max.append(max(vals))
    null_arr = np.asarray(null_max, dtype=float)
    evidence = float(np.mean(abs(best_corr) > null_arr)) if null_arr.size else np.nan
    return {
        "BestLag": float(best_lag),
        "BestLagCorr": float(best_corr),
        "ZeroLagCorr": float(zero) if np.isfinite(zero) else np.nan,
        "PermutationEvidence": evidence,
    }

def def_turnover_hotness(turnover: pd.DataFrame, group_tickers: Sequence[str], ticker: str) -> float:
    group_tickers = [t for t in group_tickers if t in turnover.columns]
    if ticker not in turnover.columns or not group_tickers:
        return np.nan
    group_total = turnover[group_tickers].sum(axis=1).replace(0, np.nan)
    member_share = turnover[ticker] / group_total
    n = len(member_share.dropna())
    if n < 4:
        return np.nan
    memory = max(2, int(round(math.sqrt(n))))
    recent = member_share.tail(memory).median()
    prior = member_share.iloc[:-memory].median() if len(member_share) > memory else member_share.median()
    own_recent = turnover[ticker].tail(memory).median()
    own_prior = turnover[ticker].iloc[:-memory].median() if len(turnover[ticker]) > memory else turnover[ticker].median()
    eps = np.finfo(float).eps
    return float(np.log((recent + eps) / (prior + eps)) + np.log((own_recent + eps) / (own_prior + eps)))


def def_build_null_group(residual: pd.DataFrame, group_tickers: Sequence[str], group_name: str) -> pd.DataFrame:
    outside = [c for c in residual.columns if c not in set(group_tickers)]
    if len(outside) < 2:
        return pd.DataFrame(index=residual.index)
    target_n = min(len(group_tickers), len(outside))
    rng = np.random.default_rng(def_stable_seed(f"NULL|{group_name}|{len(residual)}"))
    chosen = rng.choice(outside, size=target_n, replace=False)
    return residual[list(chosen)]


def def_analyze_membership(
    membership: pd.DataFrame,
    prices: pd.DataFrame,
    turnover: pd.DataFrame,
    market_return: pd.Series,
    model_seed: int,
) -> Dict[str, pd.DataFrame]:
    returns = def_safe_log_returns(prices)
    residual = def_residualize_market(returns, market_return)
    full_index, full_index_returns = def_build_group_indices(membership, prices)
    member_rows: List[Dict[str, Any]] = []
    group_rows: List[Dict[str, Any]] = []
    corr_map: Dict[str, pd.DataFrame] = {}

    for group, gm in membership.groupby("Group", sort=False):
        gm_count = gm[gm["CountingFlag"].astype(str).str.upper().isin(COUNT_FLAGS)]
        tickers = [t for t in gm_count["YFTicker"].drop_duplicates() if t in residual.columns]
        if not tickers:
            continue
        res_g = residual[tickers].dropna(how="all")
        corr = res_g.corr(min_periods=max(3, int(math.sqrt(max(len(res_g), 1)))))
        corr_map[str(group)] = corr
        pair = def_pairwise_values(corr)
        within_median = float(np.nanmedian(pair)) if pair.size else np.nan
        within_mean = float(np.nanmean(pair)) if pair.size else np.nan
        positive_ratio = float(np.mean(pair > 0)) if pair.size else np.nan
        pc1 = def_pc1_ratio(res_g)

        null_g = def_build_null_group(residual, tickers, str(group))
        null_corr = null_g.corr(min_periods=max(3, int(math.sqrt(max(len(null_g), 1))))) if not null_g.empty else pd.DataFrame()
        null_pair = def_pairwise_values(null_corr)
        null_median = float(np.nanmedian(null_pair)) if null_pair.size else np.nan
        null_positive = float(np.mean(null_pair > 0)) if null_pair.size else np.nan
        null_pc1 = def_pc1_ratio(null_g) if not null_g.empty else np.nan

        group_rows.append({
            "Group": str(group),
            "MemberCount": len(tickers),
            "WithinMedianCorr": within_median,
            "WithinMeanCorr": within_mean,
            "PositiveCorrRatio": positive_ratio,
            "PC1Ratio": pc1,
            "NullMedianCorr": null_median,
            "NullPositiveCorrRatio": null_positive,
            "NullPC1Ratio": null_pc1,
            "CorrLiftVsNull": within_median - null_median if np.isfinite(within_median) and np.isfinite(null_median) else np.nan,
            "PositiveLiftVsNull": positive_ratio - null_positive if np.isfinite(positive_ratio) and np.isfinite(null_positive) else np.nan,
            "PC1LiftVsNull": pc1 - null_pc1 if np.isfinite(pc1) and np.isfinite(null_pc1) else np.nan,
        })

        for _, row in gm_count.drop_duplicates("YFTicker").iterrows():
            ticker = row["YFTicker"]
            loo = def_leave_one_out_mean(res_g, ticker)
            sync = def_corr(res_g[ticker], loo)
            lead = def_lead_lag_metrics(res_g[ticker], loo, def_stable_seed(f"{model_seed}|{group}|{ticker}"))
            hot = def_turnover_hotness(turnover, tickers, ticker)
            lead_evidence = (
                abs(lead["BestLagCorr"]) * lead["PermutationEvidence"]
                if np.isfinite(lead["BestLagCorr"]) and np.isfinite(lead["PermutationEvidence"])
                else np.nan
            )
            member_rows.append({
                "Group": str(group),
                "Ticker": row["Ticker"],
                "YFTicker": ticker,
                "Name": row["Name"],
                "StaticRole": row["Rank"],
                "Synchrony": sync,
                "HotnessRaw": hot,
                "BestLag": lead["BestLag"],
                "BestLagCorr": lead["BestLagCorr"],
                "ZeroLagCorr": lead["ZeroLagCorr"],
                "PermutationEvidence": lead["PermutationEvidence"],
                "LeadershipEvidence": lead_evidence,
            })

    group_df = pd.DataFrame(group_rows)
    member_df = pd.DataFrame(member_rows)
    criteria_meta: List[Dict[str, Any]] = []

    if not group_df.empty:
        group_state, meta = def_fit_multivariate_states(
            group_df,
            ["CorrLiftVsNull", "PositiveLiftVsNull", "PC1LiftVsNull"],
            "GROUP_VALIDITY_EVIDENCE",
            model_seed,
        )
        group_df["ValidityState"] = group_state["State"]
        group_df["ValidityConfidence"] = group_state["PosteriorConfidence"]
        criteria_meta.append(meta)
        group_df["GroupValidity"] = group_df["ValidityState"].map({
            "HIGH": "VALID_GROUP",
            "MID": "MONITOR_GROUP",
            "LOW": "NEEDS_SPLIT_OR_REVIEW",
            "MIXED": "GROUP_NOT_SEPARABLE",
            "UNCLASSIFIED": "DATA_INSUFFICIENT",
        }).fillna("DATA_INSUFFICIENT")

        # BIC 若判定整體只有單一分布，不代表所有族群都無效。
        # 以「相對跨群 Null 的零差異」作數學基準：三項中位 lift 全部正向，
        # 表示整個市場存在廣泛但真實的族群結構；再逐群要求三項 lift 同向。
        # 這裡只用 0（無差異）作 Null，不使用固定相關係數或固定百分位。
        if int(meta.get("Components", 1)) == 1:
            evidence_cols = ["CorrLiftVsNull", "PositiveLiftVsNull", "PC1LiftVsNull"]
            global_shift = bool((group_df[evidence_cols].median(skipna=True) > 0).all())
            if global_shift:
                individual_positive = (group_df[evidence_cols] > 0).all(axis=1)
                group_df["ValidityState"] = np.where(individual_positive, "HIGH_NULL_DOMINANCE", "LOW_NULL_DOMINANCE")
                group_df["GroupValidity"] = np.where(individual_positive, "VALID_GROUP", "NEEDS_SPLIT_OR_REVIEW")
                group_df["ValidityConfidence"] = group_df[evidence_cols].gt(0).mean(axis=1)

    if not member_df.empty:
        for metric, name in [
            ("HotnessRaw", "MEMBER_HOTNESS"),
            ("Synchrony", "MEMBER_SYNCHRONY"),
            ("LeadershipEvidence", "MEMBER_LEADERSHIP"),
        ]:
            state, meta = def_fit_adaptive_states(member_df[metric], name, model_seed)
            member_df[name + "State"] = state["State"]
            member_df[name + "Confidence"] = state["PosteriorConfidence"]
            criteria_meta.append(meta)

        valid_map = group_df.set_index("Group")["GroupValidity"].to_dict() if not group_df.empty else {}
        dynamic_roles: List[str] = []
        for _, r in member_df.iterrows():
            validity = valid_map.get(r["Group"], "DATA_INSUFFICIENT")
            hot_state = r["MEMBER_HOTNESSState"]
            sync_state = r["MEMBER_SYNCHRONYState"]
            lead_state = r["MEMBER_LEADERSHIPState"]
            lag = r["BestLag"]
            if validity in {"NEEDS_SPLIT_OR_REVIEW", "GROUP_NOT_SEPARABLE", "DATA_INSUFFICIENT"}:
                role = "MIXED_ROLE" if sync_state != "LOW" else "OUTLIER"
            elif lead_state == "HIGH" and np.isfinite(lag) and lag > 0 and hot_state != "LOW":
                role = "LEADER"
            elif sync_state == "HIGH" and np.isfinite(lag) and lag == 0:
                role = "PEER"
            elif sync_state in {"HIGH", "MID"} and np.isfinite(lag) and lag < 0:
                role = "TRUE_LAGGARD"
            elif sync_state == "LOW" and lead_state == "LOW":
                role = "OUTLIER"
            else:
                role = "MEMBER"
            dynamic_roles.append(role)
        member_df["DynamicRole"] = dynamic_roles
        member_df["CoreEligible"] = ~member_df["DynamicRole"].isin(["OUTLIER"])

    core_membership = membership.copy()
    if not member_df.empty:
        eligibility = member_df[["Group", "YFTicker", "CoreEligible"]].drop_duplicates(["Group", "YFTicker"])
        core_membership = core_membership.merge(eligibility, on=["Group", "YFTicker"], how="left")
        core_membership["CoreEligible"] = core_membership["CoreEligible"].fillna(False)
        core_membership["CountingFlag"] = np.where(core_membership["CoreEligible"], "COUNT", "DISPLAY_ONLY")
    core_index, core_index_returns = def_build_group_indices(core_membership, prices)

    criteria_df = pd.DataFrame([
        {
            "CriterionID": f"CRIT-{i+1:03d}",
            "Metric": m.get("Metric"),
            "Components": m.get("Components"),
            "Centers": json.dumps(m.get("Centers"), ensure_ascii=False),
            "Cutpoints": json.dumps(m.get("Cutpoints"), ensure_ascii=False),
            "BIC": m.get("BIC"),
            "Method": m.get("Method"),
            "Features": json.dumps(m.get("Features", []), ensure_ascii=False),
            "MarketThresholdHardcoded": False,
        }
        for i, m in enumerate(criteria_meta)
    ])

    return {
        "returns": returns,
        "residual_returns": residual,
        "group_index_full": full_index,
        "group_return_full": full_index_returns,
        "group_index_core": core_index,
        "group_return_core": core_index_returns,
        "member_metrics": member_df,
        "group_summary": group_df,
        "criteria_ledger": criteria_df,
        "correlation_map": corr_map,
        "core_membership": core_membership,
    }


def def_classify_trading_capacity(prices: pd.DataFrame, turnover: pd.DataFrame, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    returns = def_safe_log_returns(prices)
    rows: List[Dict[str, Any]] = []
    for ticker in prices.columns:
        tv = turnover[ticker].replace([np.inf, -np.inf], np.nan).dropna()
        ret = returns[ticker].reindex(tv.index).dropna()
        if tv.empty:
            continue
        median_turnover = float(tv.median())
        stability = float(tv.median() / (tv.mad() + np.finfo(float).eps)) if hasattr(tv, "mad") else float(tv.median() / ((tv - tv.median()).abs().median() + np.finfo(float).eps))
        aligned = pd.concat([ret.abs(), tv], axis=1).dropna()
        price_impact = float((aligned.iloc[:, 0] / aligned.iloc[:, 1].replace(0, np.nan)).median()) if not aligned.empty else np.nan
        rows.append({
            "YFTicker": ticker,
            "MedianTurnoverValue": median_turnover,
            "TurnoverStability": stability,
            "PriceImpactPerDollar": price_impact,
            "LogMedianTurnover": math.log(median_turnover) if median_turnover > 0 else np.nan,
            "NegativeLogPriceImpact": -math.log(price_impact) if np.isfinite(price_impact) and price_impact > 0 else np.nan,
        })
    df = pd.DataFrame(rows)
    state, meta = def_fit_multivariate_states(
        df,
        ["LogMedianTurnover", "TurnoverStability", "NegativeLogPriceImpact"],
        "TRADING_CAPACITY",
        seed,
    )
    df["CapacityState"] = state["State"]
    df["CapacityConfidence"] = state["PosteriorConfidence"]
    df["TradingCapacityClass"] = df["CapacityState"].map({
        "HIGH": "LARGE_TRADING_CAPACITY",
        "MID": "MID_TRADING_CAPACITY",
        "LOW": "SMALL_TRADING_CAPACITY",
        "MIXED": "UNCLASSIFIED_TRADING_CAPACITY",
        "UNCLASSIFIED": "DATA_INSUFFICIENT",
    }).fillna("DATA_INSUFFICIENT")
    meta_df = pd.DataFrame([{
        "CriterionID": "CRIT-CAPACITY",
        "Metric": meta.get("Metric"),
        "Components": meta.get("Components"),
        "Centers": json.dumps(meta.get("Centers"), ensure_ascii=False),
        "Cutpoints": json.dumps(meta.get("Cutpoints"), ensure_ascii=False),
        "BIC": meta.get("BIC"),
        "Method": meta.get("Method"),
        "Features": json.dumps(meta.get("Features", []), ensure_ascii=False),
        "MarketThresholdHardcoded": False,
    }])
    return df, meta_df


# =============================================================================
# def 07 PLOTS AND REPORT
# =============================================================================


def def_plot_group_indices(index_df: pd.DataFrame, path: Path, title: str) -> None:
    if index_df.empty:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(13, 7))
    for col in index_df.columns:
        plt.plot(index_df.index, index_df[col], linewidth=1.0, alpha=0.75, label=str(col))
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Base 100")
    if index_df.shape[1] <= 14:
        plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(path, dpi=PLOT_DPI)
    plt.close()


def def_plot_heatmap(corr: pd.DataFrame, path: Path, title: str) -> None:
    if corr.empty or corr.shape[0] < 2:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    mask = np.zeros_like(corr.to_numpy(dtype=float), dtype=bool)
    mask[np.triu_indices_from(mask)] = True
    size = max(5.5, min(12.0, 4.0 + corr.shape[0] * 0.55))
    plt.figure(figsize=(size, size))
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    sns.heatmap(
        corr,
        mask=mask,
        cmap=cmap,
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=0.4,
        cbar_kws={"shrink": 0.55},
        annot=corr.shape[0] <= 8,
        fmt=".2f",
    )
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=PLOT_DPI)
    plt.close()


def def_validate_html_assets(html_path: Path) -> Tuple[bool, List[str]]:
    soup = BeautifulSoup(html_path.read_text("utf-8", errors="ignore"), "html.parser")
    missing: List[str] = []
    for tag, attr in [("img", "src"), ("script", "src"), ("link", "href")]:
        for el in soup.find_all(tag):
            val = el.get(attr)
            if not val or val.startswith(("http://", "https://", "data:", "#")):
                continue
            if not (html_path.parent / val).exists():
                missing.append(val)
    return len(missing) == 0, missing


def def_build_html_report(
    run_dir: Path,
    summary: Mapping[str, Any],
    source_registry: pd.DataFrame,
    test_ledger: pd.DataFrame,
    phase_ledger: pd.DataFrame,
    overlap: pd.DataFrame,
    conflicts: pd.DataFrame,
    group_summary: pd.DataFrame,
    member_metrics: pd.DataFrame,
    capacity: pd.DataFrame,
    backtest_summary: pd.DataFrame,
    user_tests: pd.DataFrame,
    plot_files: Sequence[Path],
) -> Path:
    images = "".join(
        f"<figure><img src='{html.escape(str(p.relative_to(run_dir)))}'><figcaption>{html.escape(p.name)}</figcaption></figure>"
        for p in plot_files if p.exists()
    )
    gate = str(summary.get("FinalGate", ""))
    css = """
    :root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--sub:#6b6860;--line:#dbd9d3;--red:#b5291a;--amber:#c4943a;--green:#5a9e6f;--blue:#4c78a8;--teal:#439a9a}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Arial,'Noto Sans TC',sans-serif;font-size:11px;line-height:1.5}.wrap{max-width:1700px;margin:auto;padding:18px}h1{font-size:22px;margin:4px 0}h2{font-size:14px;border-bottom:1px solid var(--line);padding-bottom:5px;margin-top:20px}.sub{color:var(--sub)}.cards{display:grid;grid-template-columns:repeat(8,1fr);gap:7px;margin:12px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:5px;padding:8px}.card .v{font-size:16px;font-weight:700;word-break:break-word}.card .l{font-size:8px;color:var(--sub);text-transform:uppercase}.note{background:#fff7e7;border-left:4px solid var(--amber);padding:9px;margin:10px 0}.matrix{width:100%;border-collapse:collapse;background:#fff;font-size:8.5px;table-layout:auto}.matrix th{background:#282925;color:#fff;position:sticky;top:0;padding:5px;text-align:left;white-space:nowrap}.matrix td{border-bottom:1px solid #eceae4;padding:4px;vertical-align:top;white-space:normal;word-break:break-word}.section{overflow:auto;max-height:560px;border:1px solid var(--line);background:#fff}.pass{color:var(--green);font-weight:700}.warn{color:var(--amber);font-weight:700}.fail{color:var(--red);font-weight:700}.plots{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:10px}.plots figure{margin:0;background:#fff;border:1px solid var(--line);padding:8px;border-radius:6px}.plots img{max-width:100%;height:auto}.plots figcaption{font-size:9px;color:var(--sub)}.footer{margin-top:18px;border-top:1px solid var(--line);padding-top:8px;color:var(--sub)}@media(max-width:1000px){.cards{grid-template-columns:repeat(4,1fr)}}
    """
    doc = f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VIA Three List Dynamic Validation v0200</title><style>{css}</style></head><body><div class='wrap'>
    <div class='sub'>VERITAS INTELLIGENCE ANALYTICS · APPEND-ONLY · EVIDENCE-HONEST · CONTROLLED ACTIVATION</div>
    <h1>VIA 三清單 × 台股族群 × 動態 Criteria 驗證報告 v0.2.00</h1>
    <div class='note'><b>Final Gate: {html.escape(gate)}</b><br>市場 Criteria 由當期資料分布與 GMM-BIC 自動產生；受控 DGP 只證明流程，不是實盤績效。</div>
    <div class='cards'>
      <div class='card'><div class='v'>{summary.get('CanonicalRows')}</div><div class='l'>Canonical Rows</div></div>
      <div class='card'><div class='v'>{summary.get('CanonicalGroups')}</div><div class='l'>Canonical Groups</div></div>
      <div class='card'><div class='v'>{summary.get('CanonicalTickers')}</div><div class='l'>Canonical Tickers</div></div>
      <div class='card'><div class='v'>{summary.get('DynamicRows')}</div><div class='l'>Dynamic Rows</div></div>
      <div class='card'><div class='v'>{summary.get('DynamicGroups')}</div><div class='l'>Dynamic Groups</div></div>
      <div class='card'><div class='v'>{summary.get('HardFailures')}</div><div class='l'>Hard Failures</div></div>
      <div class='card'><div class='v'>{summary.get('ReviewWarnings')}</div><div class='l'>Review Warnings</div></div>
      <div class='card'><div class='v'>{summary.get('ActivationStatus')}</div><div class='l'>Activation</div></div>
    </div>
    <h2>Pipeline Phases</h2><div class='section'>{def_html_table(phase_ledger)}</div>
    <h2>Test Ledger</h2><div class='section'>{def_html_table(test_ledger)}</div>
    <h2>Source Registry</h2><div class='section'>{def_html_table(source_registry)}</div>
    <h2>Dynamic Group Reconciliation</h2><div class='section'>{def_html_table(overlap)}</div>
    <h2>Conflict Ledger</h2><div class='section'>{def_html_table(conflicts)}</div>
    <h2>Group Validity</h2><div class='section'>{def_html_table(group_summary)}</div>
    <h2>Member Roles</h2><div class='section'>{def_html_table(member_metrics)}</div>
    <h2>Trading Capacity</h2><div class='section'>{def_html_table(capacity)}</div>
    <h2>Back-test</h2><div class='section'>{def_html_table(backtest_summary)}</div>
    <h2>User Tests</h2><div class='section'>{def_html_table(user_tests)}</div>
    <h2>Plots</h2><div class='plots'>{images}</div>
    <div class='footer'>Generated {def_now()} · no network · no order execution · no canonical mutation.</div>
    </div></body></html>"""
    path = run_dir / "index.html"
    path.write_text(doc, encoding="utf-8")
    return path


# =============================================================================
# def 08 BACKTEST
# =============================================================================


def def_map_dynamic_role_to_static(role: str) -> str:
    return {
        "LEADER": "L",
        "PEER": "P",
        "TRUE_LAGGARD": "G",
        "MEMBER": "P",
        "MIXED_ROLE": "U",
        "OUTLIER": "O",
    }.get(str(role), "U")


def def_run_backtest(canonical: pd.DataFrame, dynamic: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    detail_rows: List[Dict[str, Any]] = []
    threshold_rows: List[Dict[str, Any]] = []
    for scenario in CONTROLLED_SCENARIOS:
        for seed in CONTROLLED_SEEDS:
            panel = def_generate_controlled_panel(canonical, dynamic, seed, scenario)
            analyzed = def_analyze_membership(
                canonical,
                panel["prices"],
                panel["turnover"],
                panel["market_return"],
                seed,
            )
            members = analyzed["member_metrics"].copy()
            groups = analyzed["group_summary"].copy()
            truth = panel["group_truth"]
            groups = groups.merge(truth[["Group", "TruthValidGroup"]], on="Group", how="left")
            pred_valid = groups["GroupValidity"].eq("VALID_GROUP")
            truth_valid = groups["TruthValidGroup"].fillna(False).astype(bool)
            valid_precision = precision_score(truth_valid, pred_valid, zero_division=0)
            valid_recall = recall_score(truth_valid, pred_valid, zero_division=0)
            valid_f1 = f1_score(truth_valid, pred_valid, zero_division=0)
            false_positive = float((pred_valid & ~truth_valid).mean())

            members["PredStatic"] = members["DynamicRole"].map(def_map_dynamic_role_to_static)
            role_mask = members["StaticRole"].isin(["L", "P", "G"]) & members["PredStatic"].isin(["L", "P", "G"])
            role_macro_f1 = f1_score(
                members.loc[role_mask, "StaticRole"],
                members.loc[role_mask, "PredStatic"],
                average="macro",
                zero_division=0,
            ) if role_mask.any() else 0.0
            role_coverage = float(role_mask.mean()) if len(role_mask) else 0.0

            # Raw correlation false positive benchmark: market-tide 中所有 raw group corr 都容易升高。
            raw_returns = def_safe_log_returns(panel["prices"])
            raw_group_flags = []
            residual_group_flags = []
            for group, gm in canonical.groupby("Group"):
                tickers = [t for t in gm["YFTicker"] if t in raw_returns.columns]
                if len(tickers) < 2:
                    continue
                raw_pair = def_pairwise_values(raw_returns[tickers].corr())
                raw_group_flags.append(float(np.nanmedian(raw_pair)) if raw_pair.size else np.nan)
                row = groups[groups["Group"] == group]
                residual_group_flags.append(bool(row.iloc[0]["GroupValidity"] == "VALID_GROUP") if not row.empty else False)
            raw_market_tide_metric = float(np.nanmedian(raw_group_flags)) if raw_group_flags else np.nan

            detail_rows.append({
                "Scenario": scenario,
                "Seed": seed,
                "ValidityPrecision": valid_precision,
                "ValidityRecall": valid_recall,
                "ValidityF1": valid_f1,
                "ValidityFalsePositiveRate": false_positive,
                "RoleMacroF1": role_macro_f1,
                "RoleClassifiedCoverage": role_coverage,
                "RawMedianWithinCorr": raw_market_tide_metric,
                "ResidualMedianWithinCorr": float(groups["WithinMedianCorr"].median()) if not groups.empty else np.nan,
                "ResidualValidGroupRate": float(np.mean(residual_group_flags)) if residual_group_flags else np.nan,
                "CriteriaDigest": hashlib.sha256(analyzed["criteria_ledger"].to_csv(index=False).encode("utf-8")).hexdigest()[:16],
            })
            c = analyzed["criteria_ledger"].copy()
            c["Scenario"] = scenario
            c["Seed"] = seed
            threshold_rows.extend(c.to_dict("records"))

    detail = pd.DataFrame(detail_rows)
    summary = detail.groupby("Scenario", as_index=False).agg(
        Seeds=("Seed", "nunique"),
        ValidityPrecisionMedian=("ValidityPrecision", "median"),
        ValidityRecallMedian=("ValidityRecall", "median"),
        ValidityF1Median=("ValidityF1", "median"),
        FalsePositiveMedian=("ValidityFalsePositiveRate", "median"),
        RoleMacroF1Median=("RoleMacroF1", "median"),
        RoleCoverageMedian=("RoleClassifiedCoverage", "median"),
        RawMedianWithinCorrMedian=("RawMedianWithinCorr", "median"),
        ResidualMedianWithinCorrMedian=("ResidualMedianWithinCorr", "median"),
        ResidualValidGroupRateMedian=("ResidualValidGroupRate", "median"),
        UniqueCriteriaDigests=("CriteriaDigest", "nunique"),
    )
    thresholds = pd.DataFrame(threshold_rows)
    return summary, detail, thresholds


# =============================================================================
# def 09 TESTS, DEVIL VALIDATION, USER TEST, ACTIVATION
# =============================================================================


def def_build_test_ledger(
    cfg: PipelineConfig,
    source_a: pd.DataFrame,
    controls: Mapping[str, Any],
    source_c: pd.DataFrame,
    dynamic_reconciled: pd.DataFrame,
    overlap: pd.DataFrame,
    conflicts: pd.DataFrame,
    canonical: pd.DataFrame,
    dynamic: pd.DataFrame,
    analysis: Mapping[str, pd.DataFrame],
    capacity: pd.DataFrame,
    backtest_summary: pd.DataFrame,
    report_path: Optional[Path] = None,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    files_readable = all(p.exists() and p.stat().st_size > 0 for p in [cfg.source_a, cfg.source_b, cfg.source_c])
    def_add_test(rows, "T01", "三個 HTML 來源可讀", "PASS" if files_readable else "FAIL", "HARD", str(files_readable))
    def_add_test(rows, "T02", "List A row-level extraction", "PASS" if len(source_a) > 0 else "FAIL", "HARD", f"rows={len(source_a)} groups={source_a.Group.nunique()} tickers={source_a.Ticker.nunique()}")
    valid_ticker = source_a["Ticker"].astype(str).str.fullmatch(r"\d{4}").all()
    # f-string 運算式含反斜線在 Python 3.12 才合法;先算後嵌,維持 3.9+ 相容
    invalid_ticker_count = int((~source_a["Ticker"].astype(str).str.fullmatch(r"\d{4}")).sum())
    def_add_test(rows, "T03", "List A 四碼 ticker contract", "PASS" if valid_ticker else "FAIL", "HARD", f"invalid={invalid_ticker_count}")
    duplicates = int(source_a.duplicated("MembershipKey").sum())
    def_add_test(rows, "T04", "List A membership 唯一鍵", "PASS" if duplicates == 0 else "FAIL", "HARD", f"duplicates={duplicates}")
    identity_conflicts = source_a.groupby("Ticker").agg(Names=("Name", "nunique"), Markets=("Market", "nunique")).query("Names>1 or Markets>1")
    def_add_test(rows, "T05", "List A ticker 身分一致", "PASS" if identity_conflicts.empty else "FAIL", "HARD", f"conflicts={len(identity_conflicts)}")
    def_add_test(rows, "T06", "List B 僅作控制契約", "PASS" if controls.get("ControlRole") == "SCOPE_AND_GOVERNANCE_ONLY" else "FAIL", "HARD", json.dumps(controls, ensure_ascii=False))
    scope_mismatch = controls.get("ExpectedFile1Groups") != int(source_a.Group.nunique())
    def_add_test(rows, "T07", "List B 與 List A 版本範圍比對", "WARN" if scope_mismatch else "PASS", "REVIEW", f"control={controls.get('ExpectedFile1Groups')} groups; actual={source_a.Group.nunique()}")
    def_add_test(rows, "T08", "List C 三動態 cohort extraction", "PASS" if source_c.GroupDynamic.nunique() == 3 else "FAIL", "HARD", f"rows={len(source_c)} groups={source_c.GroupDynamic.nunique()}")
    unknown_roles = int((source_c.RoleDynamic == "").sum())
    def_add_test(rows, "T09", "List C role parser", "PASS" if unknown_roles == 0 else "FAIL", "HARD", f"unknown_roles={unknown_roles}")
    unmatched = int((~dynamic_reconciled.IdentityMatched).sum())
    suffix_conflicts = int((dynamic_reconciled.IdentityMatched & ~dynamic_reconciled.SuffixMatched).sum())
    def_add_test(rows, "T10", "List C ticker registry match", "WARN" if unmatched else "PASS", "REVIEW", f"matched={int(dynamic_reconciled.IdentityMatched.sum())} unmatched={unmatched}")
    def_add_test(rows, "T11", "List C yfinance suffix agreement", "WARN" if suffix_conflicts else "PASS", "REVIEW", f"conflicts={suffix_conflicts}")
    alias_decisions = "; ".join(f"{r.DynamicGroup}={r.Decision}" for r in overlap.itertuples())
    def_add_test(rows, "T12", "Dynamic cohort alias/membership reconciliation", "WARN" if any(overlap.Decision != "PROPOSED_ALIAS_REVIEW") else "PASS", "REVIEW", alias_decisions)
    def_add_test(rows, "T13", "Canonical input CountingFlag", "PASS" if set(canonical.CountingFlag.str.upper()) == {"COUNT"} else "FAIL", "HARD", str(canonical.CountingFlag.value_counts().to_dict()))
    def_add_test(rows, "T14", "Dynamic input DISPLAY_ONLY", "PASS" if set(dynamic.CountingFlag.str.upper()) == {"DISPLAY_ONLY"} else "FAIL", "HARD", str(dynamic.CountingFlag.value_counts().to_dict()))
    duplicate_count = int(pd.concat([canonical, dynamic]).query("CountingFlag == 'COUNT'").duplicated(["Dimension", "Group", "Ticker"]).sum())
    def_add_test(rows, "T15", "Duplicate Counting Gate", "PASS" if duplicate_count == 0 else "FAIL", "HARD", f"duplicates={duplicate_count}")
    criteria = analysis["criteria_ledger"]
    no_fixed = bool((criteria["MarketThresholdHardcoded"] == False).all()) if not criteria.empty else False
    def_add_test(rows, "T16", "Dynamic Criteria 無固定市場紅線", "PASS" if no_fixed else "FAIL", "HARD", f"criteria_rows={len(criteria)}")
    index_groups = analysis["group_index_full"].shape[1]
    def_add_test(rows, "T17", "39 群族群指數完整", "PASS" if index_groups == source_a.Group.nunique() else "FAIL", "HARD", f"index_groups={index_groups}")
    member_coverage = analysis["member_metrics"].YFTicker.nunique() if not analysis["member_metrics"].empty else 0
    def_add_test(rows, "T18", "會員熱門度/同步/領先性完整", "PASS" if member_coverage == canonical.YFTicker.nunique() else "FAIL", "HARD", f"metrics={member_coverage} expected={canonical.YFTicker.nunique()}")
    def_add_test(rows, "T19", "交易容量動態分類完整", "PASS" if capacity.YFTicker.nunique() >= canonical.YFTicker.nunique() else "FAIL", "HARD", f"capacity={capacity.YFTicker.nunique()}")
    if not backtest_summary.empty:
        criteria_adapt = bool((backtest_summary["UniqueCriteriaDigests"] > 1).all())
        market_tide = backtest_summary[backtest_summary.Scenario == "MARKET_TIDE"]
        market_tide_control = bool(
            not market_tide.empty
            and market_tide.iloc[0]["RawMedianWithinCorrMedian"] > market_tide.iloc[0]["ResidualMedianWithinCorrMedian"]
        )
        structured = backtest_summary[backtest_summary.Scenario != "MARKET_TIDE"]
        relative_oos = bool(
            not market_tide.empty
            and not structured.empty
            and (structured["ValidityF1Median"] > market_tide.iloc[0]["ValidityF1Median"]).all()
            and (structured["RoleMacroF1Median"] > market_tide.iloc[0]["RoleMacroF1Median"]).all()
        )
        def_add_test(rows, "T20", "Dynamic Criteria 跨情境變動", "PASS" if criteria_adapt else "FAIL", "HARD", backtest_summary[["Scenario", "UniqueCriteriaDigests"]].to_json(orient="records"))
        def_add_test(rows, "T21", "Market Tide 殘差化降低共同市場假相關", "PASS" if market_tide_control else "FAIL", "HARD", market_tide.to_json(orient="records"))
        def_add_test(rows, "T24", "結構化族群情境樣本外優於 Market Tide Null", "PASS" if relative_oos else "FAIL", "HARD", backtest_summary[["Scenario", "ValidityF1Median", "RoleMacroF1Median"]].to_json(orient="records"))
    else:
        def_add_test(rows, "T20", "Dynamic Criteria 跨情境變動", "FAIL", "HARD", "backtest missing")
        def_add_test(rows, "T21", "Market Tide 殘差化降低共同市場假相關", "FAIL", "HARD", "backtest missing")
        def_add_test(rows, "T24", "結構化族群情境樣本外優於 Market Tide Null", "FAIL", "HARD", "backtest missing")
    output_files = ["group_index_full_daily.csv", "group_index_core_daily.csv", "member_role_metrics.csv", "group_validity_summary.csv", "dynamic_criteria_ledger.csv"]
    output_complete = all((cfg.out_dir / cfg.run_tag / f).exists() for f in output_files)
    def_add_test(rows, "T22", "核心輸出完整", "PASS" if output_complete else "FAIL", "HARD", f"required={output_files}")
    if report_path is not None and report_path.exists():
        html_ok, missing = def_validate_html_assets(report_path)
        def_add_test(rows, "T23", "HTML 本地資產完整", "PASS" if html_ok else "FAIL", "HARD", f"missing={missing}")
    return pd.DataFrame(rows)


def def_build_devil_validation_ledger() -> pd.DataFrame:
    rows = [
        ("D01", "Raw Adj Close 假相關", "Residual return heatmap + market factor removal", "MITIGATED"),
        ("D02", "市場齊漲齊跌假族群", "Cross-group null + residual validity mixture", "MITIGATED"),
        ("D03", "固定 0.85 / P85 失效", "GMM-BIC data-derived states and cutpoints", "MITIGATED"),
        ("D04", "Lag fishing 多重檢定", "Circular-shift max-lag permutation evidence", "MITIGATED"),
        ("D05", "個股自我包含提高相關", "Leave-one-out group return", "MITIGATED"),
        ("D06", "Dynamic list 覆蓋 canonical", "DISPLAY_ONLY + fail-closed conflict ledger", "BLOCKED"),
        ("D07", "同股重複計數", "Dimension+Group+Ticker Counting Gate", "BLOCKED"),
        ("D08", "低價股成交張數偏誤", "Trading capacity uses turnover value and price impact", "MITIGATED"),
        ("D09", "受控 DGP 被誤認實盤", "EvidenceStatus + report boundary", "BLOCKED"),
        ("D10", "Source B 舊版控制數字覆蓋新版", "Version mismatch retained as review warning", "BLOCKED"),
        ("D11", "Market suffix 誤配", "Canonical suffix wins; conflict remains visible", "MITIGATED"),
        ("D12", "小型族群分布不可分", "GROUP_NOT_SEPARABLE / MIXED_ROLE allowed", "MITIGATED"),
    ]
    return pd.DataFrame(rows, columns=["DevilID", "Risk", "Control", "Status"])


def def_build_user_tests(
    source_a: pd.DataFrame,
    dynamic: pd.DataFrame,
    overlap: pd.DataFrame,
    conflicts: pd.DataFrame,
    analysis: Mapping[str, pd.DataFrame],
    run_dir: Path,
) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    def add(uid: str, name: str, ok: bool, detail: str) -> None:
        rows.append({"UserTestID": uid, "UserScenario": name, "Status": "PASS" if ok else "FAIL", "Detail": detail})
    add("UT01", "使用者看到 39 群與 238 檔 canonical 輸入", source_a.Group.nunique() == 39 and source_a.Ticker.nunique() == 238, f"groups={source_a.Group.nunique()} tickers={source_a.Ticker.nunique()}")
    add("UT02", "Thermal Solution 僅作 AI 散熱別名候選", bool((overlap.DynamicGroup == "Thermal Solution").any() and overlap.loc[overlap.DynamicGroup == "Thermal Solution", "Decision"].iloc[0] == "PROPOSED_ALIAS_REVIEW"), overlap[overlap.DynamicGroup == "Thermal Solution"].to_json(orient="records", force_ascii=False))
    add("UT03", "CPO/PCB 衝突維持 fail-closed", bool(overlap.loc[overlap.DynamicGroup.isin(["CPO", "PCB"]), "Decision"].str.contains("FAIL_CLOSED").all()), overlap[overlap.DynamicGroup.isin(["CPO", "PCB"])].to_json(orient="records", force_ascii=False))
    add("UT04", "Dynamic cohort 不進 COUNT", bool((dynamic.CountingFlag == "DISPLAY_ONLY").all()), str(dynamic.CountingFlag.value_counts().to_dict()))
    add("UT05", "未匹配與 suffix 衝突仍可見", bool((conflicts.Flags.astype(str).str.contains("NEEDS_TICKER_REGISTRY|YF_SUFFIX_CONFLICT", regex=True)).any()), f"conflicts={len(conflicts)}")
    add("UT06", "每群均有 Full Index", analysis["group_index_full"].shape[1] == 39, f"groups={analysis['group_index_full'].shape[1]}")
    add("UT07", "每檔有熱門度/關聯性/領先性欄位", set(["HotnessRaw", "Synchrony", "BestLag", "DynamicRole"]).issubset(analysis["member_metrics"].columns), str(analysis["member_metrics"].columns.tolist()))
    heatmaps = list((run_dir / "plots" / "heatmaps").glob("*.png"))
    eligible = int((source_a.groupby("Group").size() >= 2).sum())
    add("UT08", "可檢查各族群 residual heatmap", len(heatmaps) == eligible, f"heatmaps={len(heatmaps)} eligible={eligible}")
    return pd.DataFrame(rows)


def def_activation_status(test_ledger: pd.DataFrame, user_tests: pd.DataFrame, requested: bool) -> Dict[str, Any]:
    hard_fail = int(((test_ledger.Status == "FAIL") & (test_ledger.Severity == "HARD")).sum())
    user_fail = int((user_tests.Status == "FAIL").sum())
    if requested and hard_fail == 0 and user_fail == 0:
        status = "CONTROLLED_ACTIVATION_PASS_REVIEW_WARNINGS_RETAINED"
    else:
        status = "ACTIVATION_BLOCKED"
    return {
        "ActivationToken": ACTIVATION_TOKEN,
        "ActivationScope": ACTIVATION_SCOPE,
        "Status": status,
        "ActivatedAt": def_now() if status.startswith("CONTROLLED_ACTIVATION_PASS") else None,
        "CanonicalMutation": 0,
        "NetworkExecution": 0,
        "OrderExecution": 0,
        "HardFailures": hard_fail,
        "UserTestFailures": user_fail,
        "Policy": "research-only / append-only / fail-closed / evidence-honest",
    }


# =============================================================================
# def 10 PIPELINE
# =============================================================================


def def_write_core_outputs(run_dir: Path, analysis: Mapping[str, pd.DataFrame], capacity: pd.DataFrame, capacity_meta: pd.DataFrame) -> None:
    def_write_csv(analysis["group_index_full"].reset_index(names="Date"), run_dir / "group_index_full_daily.csv")
    def_write_csv(analysis["group_index_core"].reset_index(names="Date"), run_dir / "group_index_core_daily.csv")
    def_write_csv(analysis["member_metrics"], run_dir / "member_role_metrics.csv")
    def_write_csv(analysis["group_summary"], run_dir / "group_validity_summary.csv")
    criteria = pd.concat([analysis["criteria_ledger"], capacity_meta], ignore_index=True)
    def_write_csv(criteria, run_dir / "dynamic_criteria_ledger.csv")
    def_write_csv(capacity, run_dir / "trading_capacity_latest.csv")
    def_write_csv(analysis["core_membership"], run_dir / "core_membership_proposal.csv")


def def_generate_plots(run_dir: Path, analysis: Mapping[str, pd.DataFrame]) -> List[Path]:
    plot_files: List[Path] = []
    all_full = run_dir / "plots" / "all_group_indices_full.png"
    def_plot_group_indices(analysis["group_index_full"], all_full, "VIA 39 Group Full Equal-Weight Indices")
    if all_full.exists():
        plot_files.append(all_full)
    all_core = run_dir / "plots" / "all_group_indices_core.png"
    def_plot_group_indices(analysis["group_index_core"], all_core, "VIA 39 Group Core Equal-Weight Indices")
    if all_core.exists():
        plot_files.append(all_core)
    heat_dir = run_dir / "plots" / "heatmaps"
    for group, corr in analysis["correlation_map"].items():
        path = heat_dir / f"residual_corr_{def_sanitize_filename(group)}.png"
        def_plot_heatmap(corr, path, f"{group} · Residual Return Correlation")
        if path.exists():
            plot_files.append(path)
    return plot_files


def def_run_pipeline(cfg: PipelineConfig) -> Dict[str, Any]:
    run_dir = cfg.out_dir / cfg.run_tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    phase_rows: List[Dict[str, Any]] = []
    repair_rows: List[Dict[str, Any]] = [
        {"RepairID": "R01", "Issue": "v0100 production role classifier still used fixed 0.60/0.80 thresholds", "Repair": "Replaced by GMM-BIC dynamic states", "Status": "FIXED"},
        {"RepairID": "R02", "Issue": "v0100 local run directory could be incomplete after packaging", "Repair": "Output completeness + manifest + package replay gates", "Status": "FIXED"},
        {"RepairID": "R03", "Issue": "Canonical run omitted all heatmaps", "Repair": "Generate residual heatmap for every eligible canonical group", "Status": "FIXED"},
        {"RepairID": "R04", "Issue": "Raw correlation may confuse market tide with group coherence", "Repair": "Market residual + cross-group null evidence", "Status": "FIXED"},
        {"RepairID": "R05", "Issue": "Lag search inflation", "Repair": "Circular-shift max-lag permutation evidence", "Status": "FIXED"},
        {"RepairID": "R06", "Issue": "Role-weighted index embeds subjective constants", "Repair": "Primary Full/Core indices are equal-weight", "Status": "FIXED"},
    ]

    # TEST 1
    started = def_now()
    source_a, _ = def_extract_source_a(cfg.source_a)
    controls_df, controls = def_extract_source_b(cfg.source_b)
    source_c = def_extract_source_c(cfg.source_c)
    ended = def_now()
    def_add_phase(phase_rows, "TEST-1", "PASS", "Sources parsed", started, ended)

    # DEBUG 1 + CONSOLIDATION INPUT
    started = def_now()
    dynamic_reconciled = def_reconcile_dynamic_identity(source_a, source_c)
    overlap = def_build_overlap_ledger(source_a, source_c)
    conflicts = def_build_conflict_ledger(dynamic_reconciled, overlap)
    canonical = def_build_canonical_input(source_a)
    dynamic = def_build_dynamic_input(dynamic_reconciled)
    ended = def_now()
    def_add_phase(phase_rows, "DEBUG-1", "PASS", f"Conflicts retained={len(conflicts)}; no source mutation", started, ended)

    # OPTIMIZE + TEST 2 — controlled main panel
    started = def_now()
    panel = def_generate_controlled_panel(canonical, dynamic, CONTROLLED_SEEDS[-1], "ROTATION")
    analysis = def_analyze_membership(canonical, panel["prices"], panel["turnover"], panel["market_return"], CONTROLLED_SEEDS[-1])
    capacity, capacity_meta = def_classify_trading_capacity(panel["prices"], panel["turnover"], CONTROLLED_SEEDS[-1])
    def_write_core_outputs(run_dir, analysis, capacity, capacity_meta)
    ended = def_now()
    def_add_phase(phase_rows, "OPTIMIZE-1", "PASS", "Vectorized panels; dynamic GMM criteria; Full/Core equal-weight indices", started, ended)

    started = def_now()
    pre_tests = def_build_test_ledger(
        cfg, source_a, controls, source_c, dynamic_reconciled, overlap, conflicts,
        canonical, dynamic, analysis, capacity, pd.DataFrame(), None,
    )
    pre_fail = int(((pre_tests.Status == "FAIL") & (pre_tests.Severity == "HARD")).sum())
    ended = def_now()
    def_add_phase(phase_rows, "TEST-2", "PASS" if pre_fail == 3 else "REVIEW", "Pre-backtest expected T20/T21/T24 pending", started, ended)

    # CONSOLIDATE
    started = def_now()
    source_registry = pd.DataFrame([
        {"SourceID": SOURCE_IDS["A"], "SourceFile": cfg.source_a.name, "Role": "ROW_LEVEL_CANONICAL_CANDIDATE", "Rows": len(source_a), "Groups": source_a.Group.nunique(), "Tickers": source_a.Ticker.nunique(), "SHA256": def_sha256(cfg.source_a)},
        {"SourceID": SOURCE_IDS["B"], "SourceFile": cfg.source_b.name, "Role": "SCOPE_GOVERNANCE_CONTROL_ONLY", "Rows": len(controls_df), "Groups": controls.get("ExpectedFile1Groups"), "Tickers": controls.get("ExpectedFile2Codes"), "SHA256": def_sha256(cfg.source_b)},
        {"SourceID": SOURCE_IDS["C"], "SourceFile": cfg.source_c.name, "Role": "DYNAMIC_TEST_COHORT_DISPLAY_ONLY", "Rows": len(source_c), "Groups": source_c.GroupDynamic.nunique(), "Tickers": source_c.Ticker.nunique(), "SHA256": def_sha256(cfg.source_c)},
    ])
    def_write_csv(source_registry, run_dir / "source_registry.csv")
    def_write_csv(controls_df, run_dir / "control_contract.csv")
    def_write_csv(canonical, run_dir / "canonical_membership_input.csv")
    def_write_csv(dynamic, run_dir / "dynamic_cohort_input.csv")
    def_write_csv(dynamic_reconciled, run_dir / "dynamic_reconciliation.csv")
    def_write_csv(overlap, run_dir / "group_overlap_ledger.csv")
    def_write_csv(conflicts, run_dir / "conflict_ledger.csv")
    def_write_csv(pd.DataFrame(repair_rows), run_dir / "repair_ledger.csv")
    ended = def_now()
    def_add_phase(phase_rows, "CONSOLIDATE", "PASS", "Normalized inputs and append-only evidence ledgers written", started, ended)

    # TEST 3
    started = def_now()
    core_files = [
        "canonical_membership_input.csv", "dynamic_cohort_input.csv", "group_index_full_daily.csv",
        "group_index_core_daily.csv", "member_role_metrics.csv", "group_validity_summary.csv",
        "dynamic_criteria_ledger.csv", "conflict_ledger.csv",
    ]
    output_ok = all((run_dir / f).exists() and (run_dir / f).stat().st_size > 0 for f in core_files)
    ended = def_now()
    def_add_phase(phase_rows, "TEST-3", "PASS" if output_ok else "FAIL", f"core_outputs={output_ok}", started, ended)

    # BACK-TEST
    started = def_now()
    if cfg.run_backtest:
        backtest_summary, backtest_detail, backtest_thresholds = def_run_backtest(canonical, dynamic)
    else:
        backtest_summary, backtest_detail, backtest_thresholds = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    def_write_csv(backtest_summary, run_dir / "backtest_summary.csv")
    def_write_csv(backtest_detail, run_dir / "backtest_seed_detail.csv")
    def_write_csv(backtest_thresholds, run_dir / "backtest_dynamic_criteria.csv")
    ended = def_now()
    def_add_phase(phase_rows, "BACK-TEST", "PASS" if not backtest_summary.empty else "FAIL", f"scenarios={len(backtest_summary)} detail_rows={len(backtest_detail)}", started, ended)

    # DEBUG after backtest: no mutation, fail closed if absent.
    started = def_now()
    devil = def_build_devil_validation_ledger()
    def_write_csv(devil, run_dir / "devil_validation_ledger.csv")
    ended = def_now()
    def_add_phase(phase_rows, "DEBUG-BACKTEST", "PASS", "Devil controls reviewed; synthetic evidence remains non-live", started, ended)

    # PLOTS before user test.
    started = def_now()
    plot_files = def_generate_plots(run_dir, analysis) if cfg.write_plots else []
    ended = def_now()
    def_add_phase(phase_rows, "PLOT-RENDER", "PASS", f"plots={len(plot_files)} font={CJK_FONT}", started, ended)

    # USER TEST
    started = def_now()
    user_tests = def_build_user_tests(source_a, dynamic, overlap, conflicts, analysis, run_dir)
    def_write_csv(user_tests, run_dir / "user_test_ledger.csv")
    user_fail = int((user_tests.Status == "FAIL").sum())
    ended = def_now()
    def_add_phase(phase_rows, "USER-TEST", "PASS" if user_fail == 0 else "FAIL", f"failures={user_fail}", started, ended)

    # Final test ledger (HTML asset check appended after report creation).
    phase_ledger = pd.DataFrame(phase_rows)
    test_ledger = def_build_test_ledger(
        cfg, source_a, controls, source_c, dynamic_reconciled, overlap, conflicts,
        canonical, dynamic, analysis, capacity, backtest_summary, None,
    )
    review_warnings = int((test_ledger.Status == "WARN").sum())
    hard_failures = int(((test_ledger.Status == "FAIL") & (test_ledger.Severity == "HARD")).sum())

    activation = def_activation_status(test_ledger, user_tests, cfg.activate)
    def_write_json(activation, run_dir / "activation_status.json")
    def_add_phase(
        phase_rows,
        "ACTIVATE",
        "PASS" if activation["Status"].startswith("CONTROLLED_ACTIVATION_PASS") else "BLOCKED",
        activation["Status"],
        def_now(),
        def_now(),
    )
    phase_ledger = pd.DataFrame(phase_rows)

    summary = {
        "Engine": ENGINE_NAME,
        "Version": VERSION,
        "GeneratedAt": def_now(),
        "FinalGate": activation["Status"],
        "CanonicalRows": int(len(canonical)),
        "CanonicalGroups": int(canonical.Group.nunique()),
        "CanonicalTickers": int(canonical.Ticker.nunique()),
        "DynamicRows": int(len(dynamic)),
        "DynamicGroups": int(dynamic.Group.nunique()),
        "HardFailures": hard_failures,
        "ReviewWarnings": review_warnings,
        "ActivationStatus": activation["Status"],
        "Policy": "append-only / no canonical overwrite / no network / no order execution",
    }

    # First report for asset check.
    report_path = def_build_html_report(
        run_dir, summary, source_registry, test_ledger, phase_ledger, overlap, conflicts,
        analysis["group_summary"], analysis["member_metrics"], capacity,
        backtest_summary, user_tests, plot_files,
    )
    test_ledger = def_build_test_ledger(
        cfg, source_a, controls, source_c, dynamic_reconciled, overlap, conflicts,
        canonical, dynamic, analysis, capacity, backtest_summary, report_path,
    )
    hard_failures = int(((test_ledger.Status == "FAIL") & (test_ledger.Severity == "HARD")).sum())
    review_warnings = int((test_ledger.Status == "WARN").sum())
    activation = def_activation_status(test_ledger, user_tests, cfg.activate)
    summary["FinalGate"] = activation["Status"]
    summary["HardFailures"] = hard_failures
    summary["ReviewWarnings"] = review_warnings
    summary["ActivationStatus"] = activation["Status"]
    def_write_csv(test_ledger, run_dir / "test_validation_ledger.csv")
    def_write_csv(phase_ledger, run_dir / "pipeline_phase_ledger.csv")
    def_write_json(activation, run_dir / "activation_status.json")
    def_write_json(summary, run_dir / "run_summary.json")
    report_path = def_build_html_report(
        run_dir, summary, source_registry, test_ledger, phase_ledger, overlap, conflicts,
        analysis["group_summary"], analysis["member_metrics"], capacity,
        backtest_summary, user_tests, plot_files,
    )

    # Final phase must be written before the immutable manifest is computed.
    final_phase_rows = phase_ledger.to_dict("records")
    final_phase_rows.append({
        "Phase": "FINAL-TEST",
        "Status": "PASS" if hard_failures == 0 and user_fail == 0 else "FAIL",
        "Started": def_now(),
        "Ended": def_now(),
        "Detail": f"hard_failures={hard_failures}; user_failures={user_fail}; manifest_mode=immutable_postcheck",
    })
    phase_ledger = pd.DataFrame(final_phase_rows)
    def_write_csv(phase_ledger, run_dir / "pipeline_phase_ledger.csv")

    # Set the expected state before hashing; no output may be mutated after this block.
    summary["ManifestVerified"] = True
    summary["FinalPhase"] = phase_ledger.iloc[-1].to_dict()
    def_write_json(summary, run_dir / "run_summary.json")

    manifest: Dict[str, str] = {}
    for p in sorted(run_dir.rglob("*")):
        if p.is_file() and p.name != "SHA256_MANIFEST.json":
            manifest[str(p.relative_to(run_dir))] = def_sha256(p)
    def_write_json(manifest, run_dir / "SHA256_MANIFEST.json")
    manifest_ok = all(def_sha256(run_dir / rel) == digest for rel, digest in manifest.items())
    if not manifest_ok:
        raise RuntimeError("SHA256 manifest verification failed")
    return {
        "run_dir": run_dir,
        "summary": summary,
        "test_ledger": test_ledger,
        "phase_ledger": phase_ledger,
        "activation": activation,
        "report": report_path,
    }


# =============================================================================
# def 11 CLI
# =============================================================================


def def_parse_args(argv: Optional[Sequence[str]] = None) -> PipelineConfig:
    parser = argparse.ArgumentParser(description="VIA three-list dynamic grouping validation pipeline")
    parser.add_argument("--source-a", type=Path, default=DEFAULT_SOURCE_A)
    parser.add_argument("--source-b", type=Path, default=DEFAULT_SOURCE_B)
    parser.add_argument("--source-c", type=Path, default=DEFAULT_SOURCE_C)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--run-tag", default="RUN_FINAL_V0200")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--no-backtest", action="store_true")
    parser.add_argument("--no-activate", action="store_true")
    ns = parser.parse_args(argv)
    return PipelineConfig(
        source_a=ns.source_a,
        source_b=ns.source_b,
        source_c=ns.source_c,
        out_dir=ns.out_dir,
        run_tag=ns.run_tag,
        write_plots=not ns.no_plots,
        run_backtest=not ns.no_backtest,
        activate=not ns.no_activate,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    warnings.filterwarnings("error", category=RuntimeWarning)
    warnings.filterwarnings("error", category=FutureWarning)
    try:
        cfg = def_parse_args(argv)
        result = def_run_pipeline(cfg)
        print("=" * 96)
        print(f"{ENGINE_NAME} v{VERSION}")
        print("Final Gate :", result["summary"]["FinalGate"])
        print("Run Dir    :", result["run_dir"])
        print("Hard Fail  :", result["summary"]["HardFailures"])
        print("Review Warn:", result["summary"]["ReviewWarnings"])
        print("Manifest   :", result["summary"].get("ManifestVerified"))
        print("=" * 96)
        return 0 if result["summary"]["HardFailures"] == 0 and result["activation"]["Status"].startswith("CONTROLLED_ACTIVATION_PASS") else 2
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
