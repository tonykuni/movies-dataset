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

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SNAPSHOT_ASOF = "2026-07-18"
SNAPSHOT_METHOD_ID = "ROTATION-M4"
SNAPSHOT_METHOD_VERSION = "0.4.0"
SNAPSHOT_EVIDENCE_TIER = "SOURCE_REPORTED_T2_T3_UNVERIFIED"
DECLARED_REGISTRY_GROUP_COUNT = 29
EXPECTED_TRACKED_GROUP_COUNT = 18
STATE_ORDER = ("IGNITE", "DIFFUSE", "OVERHEAT", "EBB", "DORMANT")
STATE_LABEL = {
    "IGNITE": "啟動",
    "DIFFUSE": "擴散",
    "OVERHEAT": "過熱",
    "EBB": "退潮",
    "DORMANT": "潛伏",
}
EXPECTED_STATE_COUNTS = {"IGNITE": 4, "DIFFUSE": 2, "OVERHEAT": 4, "EBB": 5, "DORMANT": 3}
STATE_BASE_SCORE = {"IGNITE": 0.90, "DIFFUSE": 0.76, "OVERHEAT": 0.52, "EBB": 0.18, "DORMANT": 0.34}
ALLOWED_NEXT_STATES = {
    "DORMANT": {"DORMANT", "IGNITE"},
    "IGNITE": {"IGNITE", "DIFFUSE", "EBB"},
    "DIFFUSE": {"DIFFUSE", "OVERHEAT", "EBB"},
    "OVERHEAT": {"OVERHEAT", "EBB"},
    "EBB": {"EBB", "DORMANT", "IGNITE"},
}

ROTATION_ROWS = [
    ("IGNITE", "石英/頻率元件", "30.10.20", "報價型", 0.35, 0.40, "石英元件供給吃緊"),
    ("IGNITE", "低軌衛星", "50.20.10", "政策型", 0.35, 0.35, "低軌衛星輪動焦點"),
    ("IGNITE", "重電", "10.30.10", "需求型", 0.30, 0.30, "重電 AI 電力題材；輪動焦點"),
    ("IGNITE", "軍工航太", "50.10.10", "政策型", 0.30, 0.30, "軍工航太；跨情境不變量；地緣升溫受惠"),
    ("DIFFUSE", "AI電子材料/CCL", "10.10.60", "報價型", 0.45, 0.50, "AI 電子材料/CCL 漲價與被動同步"),
    ("DIFFUSE", "矽晶圓", "20.30.20", "報價型", 0.40, 0.40, "矽晶圓漲價；新拆出主流；DDR4 新舊倒掛受惠"),
    ("OVERHEAT", "散熱", "10.10.20", "需求型", 0.60, 0.55, "AI 功耗與出貨上升，但漲多過熱"),
    ("OVERHEAT", "PCB", "10.10.30", "需求型", 0.55, 0.50, "PCB 主流但回檔"),
    ("OVERHEAT", "IC設計", "20.10.20", "需求型", 0.55, 0.45, "IC 設計與 ASIC 需求仍在主流"),
    ("OVERHEAT", "光學", "30.20.10", "需求型", 0.50, 0.40, "光學過熱觀察"),
    ("EBB", "被動元件", "30.10.10", "報價型", 0.85, 0.90, "擁擠交易快速反轉；套牢層深"),
    ("EBB", "記憶體", "20.30.10", "報價型", 0.80, 0.75, "報價信仰斷裂風險；HBM4 放緩；晚期套牢"),
    ("EBB", "CPO 共封裝光學", "10.20.10", "題材型", 0.75, 0.60, "CPO/矽光子炒作過度疑慮；退潮深"),
    ("EBB", "AI 伺服器", "10.10.10", "需求型", 0.70, 0.45, "AI 伺服器修正；權值相對落後"),
    ("EBB", "半導體", "20.10.10", "需求型", 0.70, 0.40, "半導體權值利多出盡；相對落後"),
    ("DORMANT", "記憶體封測/模組", "20.30.30", "報價型", 0.60, 0.55, "記憶體封測晚期層；等待原廠拉貨節奏"),
    ("DORMANT", "鋼鐵", "60.20.10", "低基期", 0.15, 0.15, "鋼鐵/傳產反內捲；掛中國依賴旗標"),
    ("DORMANT", "金融", "70.10.10", "防禦型", 0.20, 0.10, "金融潛伏；防禦輪動候選"),
]

GROUP_MAP = {
    "石英/頻率元件": ([], "UNMAPPED_NEW_GROUP_REQUIRES_TAXONOMY_REVIEW"),
    "低軌衛星": (["低軌衛星"], "EXACT"),
    "重電": (["重電"], "EXACT"),
    "軍工航太": (["軍工航太"], "EXACT"),
    "AI電子材料/CCL": (["PCB · 銅箔基板 CCL"], "ALIAS"),
    "矽晶圓": (["半導體上游 · 矽晶圓與材料"], "ALIAS"),
    "散熱": (["散熱"], "EXACT"),
    "PCB": (["PCB · 高階載板 ABF", "PCB · 設備與製程", "PCB · 硬板與軟板", "PCB · 銅箔基板 CCL"], "SPLIT_PARENT"),
    "IC設計": (["IC 設計 · 大型", "IC 設計 · 中小型"], "SPLIT_PARENT"),
    "光學": (["光學"], "EXACT"),
    "被動元件": (["被動元件"], "EXACT"),
    "記憶體": (["記憶體"], "EXACT"),
    "CPO 共封裝光學": (["光通訊 · CPO 共封裝"], "ALIAS"),
    "AI 伺服器": (["AI 伺服器"], "EXACT"),
    "半導體": (["晶圓代工", "封裝測試", "半導體設備", "半導體通路"], "SPLIT_PARENT"),
    "記憶體封測/模組": (["記憶體", "封裝測試"], "CROSS_GROUP_ALIAS"),
    "鋼鐵": (["鋼鐵"], "EXACT"),
    "金融": (["金融"], "EXACT"),
}

FALSIFIER_BY_TYPE = {
    "報價型": "關鍵報價環比走平即視為敘事斷裂，不需等待價格下跌。",
    "需求型": "第 3–5 日量能未延續或訂單/出貨未確認，視為一日避風港。",
    "政策型": "政策、預算或地緣事件未落地，狀態不得升格。",
    "低基期": "市場廣度未擴散，維持潛伏而非啟動。",
    "防禦型": "Risk-Off 資金未流入或相對強度未改善，維持潛伏。",
    "題材型": "成分同步性與實質流量未恢復，不得由退潮直接升格。",
}


def _stable_snapshot_id(group_name: str) -> str:
    digest = hashlib.blake2s(
        f"{SNAPSHOT_ASOF}|{group_name}|{SNAPSHOT_METHOD_VERSION}".encode("utf-8"), digest_size=5
    ).hexdigest().upper()
    return f"ROT-{SNAPSHOT_ASOF.replace('-', '')}-{digest}"


def _relay_score(state: str, trapped: float, leverage: float) -> float:
    base = STATE_BASE_SCORE[state]
    score = base * (1.0 - 0.45 * trapped - 0.35 * leverage)
    return round(float(np.clip(score * 100.0, 0.0, 100.0)), 2)


def def_normalize_candidate_group_names(candidate_groups: Any) -> set[str]:
    """Accept the runtime DataFrame plus lightweight list/dict forms used by tests and contracts."""
    if candidate_groups is None:
        return set()
    if isinstance(candidate_groups, pd.DataFrame):
        if "GroupName" not in candidate_groups.columns:
            raise ValueError("candidate group DataFrame missing GroupName")
        return set(candidate_groups["GroupName"].dropna().astype(str).str.strip())
    if isinstance(candidate_groups, dict):
        nested = candidate_groups.get("groups") or candidate_groups.get("candidate_groups")
        if nested is not None:
            return def_normalize_candidate_group_names(nested)
        return {str(name).strip() for name in candidate_groups if str(name).strip()}
    if isinstance(candidate_groups, (list, tuple, set)):
        names: set[str] = set()
        for item in candidate_groups:
            if isinstance(item, dict):
                value = item.get("GroupName") or item.get("name") or item.get("group")
            else:
                value = item
            if value is not None and str(value).strip():
                names.add(str(value).strip())
        return names
    raise TypeError(f"Unsupported candidate group container: {type(candidate_groups).__name__}")


def def_build_rotation_snapshot(candidate_groups: Any) -> tuple[pd.DataFrame, dict[str, Any]]:
    candidate_names = def_normalize_candidate_group_names(candidate_groups)
    rows: list[dict[str, Any]] = []
    for state, group_name, twgc, narrative_type, trapped, leverage, evidence in ROTATION_ROWS:
        mapped_names, mapping_status = GROUP_MAP[group_name]
        missing_targets = sorted(set(mapped_names).difference(candidate_names))
        if missing_targets:
            mapping_status = "MAPPING_TARGET_NOT_IN_CANDIDATE_49"
        rows.append(
            {
                "SnapshotId": _stable_snapshot_id(group_name),
                "AsOfDate": SNAPSHOT_ASOF,
                "RegistryDeclaredGroupCount": DECLARED_REGISTRY_GROUP_COUNT,
                "TrackedGroupName": group_name,
                "TWGC": twgc,
                "State": state,
                "StateLabel": STATE_LABEL[state],
                "NarrativeType": narrative_type,
                "TrappedLayer": trapped,
                "LeverageDensity": leverage,
                "RelayScore": _relay_score(state, trapped, leverage),
                "NarrativeEvidence": evidence,
                "Falsifier": FALSIFIER_BY_TYPE[narrative_type],
                "Candidate49Targets": " | ".join(mapped_names),
                "CandidateMappingStatus": mapping_status,
                "MissingMappingTargets": " | ".join(missing_targets),
                "MethodId": SNAPSHOT_METHOD_ID,
                "MethodVersion": SNAPSHOT_METHOD_VERSION,
                "EvidenceTier": SNAPSHOT_EVIDENCE_TIER,
                "M3TruthStatus": "BLOCKED_PENDING_VDF_M3",
                "IndexUseStatus": "PROHIBITED_UNTIL_T1_AND_VALIDATE_PASS",
                "CanonicalMutation": 0,
            }
        )
    snapshot = pd.DataFrame(rows)
    counts = snapshot["State"].value_counts().reindex(STATE_ORDER, fill_value=0).to_dict()
    quality = {
        "SnapshotAsOf": SNAPSHOT_ASOF,
        "RegistryDeclaredGroupCount": DECLARED_REGISTRY_GROUP_COUNT,
        "RegistryMaterializationStatus": "DECLARED_COUNT_ONLY_TW_GROUP_REGISTRY_JSON_NOT_ATTACHED",
        "TrackedGroupCount": int(len(snapshot)),
        "ExpectedTrackedGroupCount": EXPECTED_TRACKED_GROUP_COUNT,
        "StateCounts": {key: int(value) for key, value in counts.items()},
        "StateCountsMatch": counts == EXPECTED_STATE_COUNTS,
        "DuplicateGroupDate": int(snapshot.duplicated(["AsOfDate", "TrackedGroupName"]).sum()),
        "ExactOrAliasMappings": int(snapshot["CandidateMappingStatus"].isin(["EXACT", "ALIAS"]).sum()),
        "SplitOrCrossMappings": int(snapshot["CandidateMappingStatus"].isin(["SPLIT_PARENT", "CROSS_GROUP_ALIAS"]).sum()),
        "UnmappedGroups": snapshot.loc[
            snapshot["CandidateMappingStatus"] == "UNMAPPED_NEW_GROUP_REQUIRES_TAXONOMY_REVIEW",
            "TrackedGroupName",
        ].tolist(),
        "EvidenceTier": SNAPSHOT_EVIDENCE_TIER,
        "CrossValidationClaimStatus": "SOURCE_CLAIM_UNVERIFIED_REGISTRY_AND_SCHEMA_NOT_ATTACHED",
        "M3TruthStatus": "BLOCKED_PENDING_VDF_M3",
        "Candidate49IndexEffect": "NONE_REVIEW_ONLY",
        "CanonicalMutation": 0,
        "SourceBoundaries": [
            "Five-state snapshot is source-reported T2/T3 and cannot generate a measured index.",
            "Hierarchical L1/L2/L3 index and valuation values are DEMO and are not ingested as runtime market facts.",
            "ONE/FIS global simulation contains synthetic or estimated values and remains scenario-only.",
            "VDF control-panel attachment is a contract U/I; no fetcher was executed by this integration.",
        ],
    }
    def_validate_rotation_snapshot(snapshot, quality)
    return snapshot, quality


def def_validate_rotation_snapshot(snapshot: pd.DataFrame, quality: dict[str, Any]) -> None:
    if len(snapshot) != EXPECTED_TRACKED_GROUP_COUNT:
        raise ValueError(f"Rotation tracked count mismatch: {len(snapshot)}")
    if not quality["StateCountsMatch"]:
        raise ValueError(f"Rotation state count mismatch: {quality['StateCounts']}")
    if quality["DuplicateGroupDate"]:
        raise ValueError("Rotation snapshot contains duplicate AsOfDate + TrackedGroupName")
    if set(snapshot["State"]) != set(STATE_ORDER):
        raise ValueError(f"Rotation states mismatch: {sorted(set(snapshot['State']))}")
    if not snapshot["CanonicalMutation"].eq(0).all():
        raise ValueError("Rotation snapshot attempted canonical mutation")


def def_validate_rotation_source_contract(source_path: Path, snapshot: pd.DataFrame) -> dict[str, Any]:
    """Prove that runtime rows exactly match the persisted user-message source contract."""
    contract = json.loads(source_path.read_text(encoding="utf-8"))
    if contract.get("as_of") != SNAPSHOT_ASOF:
        raise ValueError(f"Rotation source as_of mismatch: {contract.get('as_of')}")
    if int(contract.get("registry_declared_group_count", -1)) != DECLARED_REGISTRY_GROUP_COUNT:
        raise ValueError("Rotation source declared registry count mismatch")
    if int(contract.get("tracked_group_count", -1)) != EXPECTED_TRACKED_GROUP_COUNT:
        raise ValueError("Rotation source tracked count mismatch")
    if contract.get("expected_state_counts") != EXPECTED_STATE_COUNTS:
        raise ValueError("Rotation source state count contract mismatch")
    source_rows = pd.DataFrame(contract.get("rows", []))
    required = {
        "state",
        "group",
        "twgc",
        "narrative_type",
        "trapped_layer",
        "leverage_density",
        "evidence",
    }
    if not required.issubset(source_rows.columns):
        raise ValueError(f"Rotation source rows missing fields: {sorted(required.difference(source_rows.columns))}")
    if len(source_rows) != EXPECTED_TRACKED_GROUP_COUNT or source_rows["group"].duplicated().any():
        raise ValueError("Rotation source rows are incomplete or duplicated")
    runtime = snapshot.rename(
        columns={
            "State": "state",
            "TrackedGroupName": "group",
            "TWGC": "twgc",
            "NarrativeType": "narrative_type",
            "TrappedLayer": "trapped_layer",
            "LeverageDensity": "leverage_density",
            "NarrativeEvidence": "evidence",
        }
    )
    joined = source_rows.merge(runtime[list(required)], on="group", how="outer", suffixes=("_source", "_runtime"), indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Rotation source/runtime group set mismatch")
    text_columns = ["state", "twgc", "narrative_type", "evidence"]
    mismatches: list[str] = []
    for column in text_columns:
        unequal = joined[f"{column}_source"].astype(str) != joined[f"{column}_runtime"].astype(str)
        mismatches.extend(joined.loc[unequal, "group"].astype(str).map(lambda name: f"{name}:{column}").tolist())
    for column in ["trapped_layer", "leverage_density"]:
        unequal = ~np.isclose(
            pd.to_numeric(joined[f"{column}_source"], errors="coerce"),
            pd.to_numeric(joined[f"{column}_runtime"], errors="coerce"),
            equal_nan=True,
        )
        mismatches.extend(joined.loc[unequal, "group"].astype(str).map(lambda name: f"{name}:{column}").tolist())
    if mismatches:
        raise ValueError("Rotation source/runtime row mismatch: " + " | ".join(sorted(mismatches)))
    return {
        "SourceContractId": contract.get("snapshot_id"),
        "SourceContractVersion": contract.get("version"),
        "SourceProvenance": contract.get("source"),
        "SourceStatus": contract.get("source_status"),
        "SourceRowsValidated": int(len(source_rows)),
        "SourceRuntimeMatch": True,
        "CanonicalMutation": int(contract.get("canonical_mutation", 0)),
    }


def def_validate_transition_history(history: pd.DataFrame) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    ordered = history.sort_values(["TrackedGroupName", "AsOfDate"])
    for group_name, rows in ordered.groupby("TrackedGroupName", sort=False):
        states = rows["State"].tolist()
        dates = rows["AsOfDate"].tolist()
        for index in range(1, len(states)):
            if states[index] not in ALLOWED_NEXT_STATES.get(states[index - 1], set()):
                findings.append(
                    {
                        "TrackedGroupName": group_name,
                        "FromDate": dates[index - 1],
                        "ToDate": dates[index],
                        "FromState": states[index - 1],
                        "ToState": states[index],
                        "Status": "BLOCKED_ILLEGAL_STATE_TRANSITION",
                    }
                )
    return findings


def def_append_rotation_snapshot(snapshot: pd.DataFrame, base_path: Path) -> dict[str, Any]:
    """Append new group-date events; reject conflicting rewrites of an existing event."""
    csv_path = base_path.with_suffix(".csv")
    base_path.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(csv_path, encoding="utf-8-sig") if csv_path.exists() else pd.DataFrame()
    if existing.empty:
        merged = snapshot.copy()
        appended = len(snapshot)
    else:
        keys = ["AsOfDate", "TrackedGroupName"]
        overlap = existing.merge(snapshot, on=keys, how="inner", suffixes=("_old", "_new"))
        comparison_columns = ["State", "TWGC", "NarrativeType", "TrappedLayer", "LeverageDensity"]
        for column in comparison_columns:
            if not overlap.empty and not overlap[f"{column}_old"].astype(str).equals(overlap[f"{column}_new"].astype(str)):
                raise ValueError(f"Append-only conflict for rotation column: {column}")
        existing_keys = set(map(tuple, existing[keys].astype(str).to_numpy()))
        addition = snapshot.loc[
            ~snapshot[keys].astype(str).apply(tuple, axis=1).isin(existing_keys)
        ]
        merged = pd.concat([existing, addition], ignore_index=True)
        appended = len(addition)
    merged = merged.sort_values(["AsOfDate", "State", "TrackedGroupName"]).reset_index(drop=True)
    merged.to_csv(csv_path, index=False, encoding="utf-8-sig")
    try:
        merged.to_parquet(base_path.with_suffix(".parquet"), index=False)
        parquet_status = "PASS"
    except Exception as exc:
        parquet_status = f"REVIEW_OPTIONAL_DEPENDENCY:{type(exc).__name__}"
    return {"rows": int(len(merged)), "appended": int(appended), "parquet_status": parquet_status}


def def_extract_vdf_contract_summary(source_path: Path) -> dict[str, Any]:
    html = source_path.read_text(encoding="utf-8")
    title_match = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    twse_match = re.search(r"const\s+TW_TWSE\s*=\s*(\d+)", html)
    tpex_match = re.search(r"const\s+TW_TPEX\s*=\s*(\d+)", html)
    if not title_match or not twse_match or not tpex_match:
        raise ValueError("VDF contract attachment missing title or TW market count constants")
    twse = int(twse_match.group(1))
    tpex = int(tpex_match.group(1))
    return {
        "SourceFile": source_path.name,
        "Title": title_match.group(1).strip(),
        "DeclaredTWSE": twse,
        "DeclaredTPEX": tpex,
        "DeclaredTaiwanTotal": twse + tpex,
        "ContractStatus": "SOURCE_REPORTED_UI_CONTRACT_NOT_EXECUTED",
        "ExternalFontDependencyDetected": bool(re.search(r"https://fonts\.googleapis\.com", html)),
        "EmbedPolicy": "SUMMARY_ONLY_OFFLINE_DASHBOARD_NO_EXTERNAL_DEPENDENCY",
        "FetcherExecution": 0,
        "NetworkExecution": 0,
        "CanonicalMutation": 0,
    }


def def_write_rotation_quality(quality: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")
