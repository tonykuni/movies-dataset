#!/usr/bin/env python3
"""Persistent, data-free single-chart library for the VAP chart editor.

The chart library stores reusable chart *specifications* and small searchable
metadata only.  Source rows, data frames, Plotly traces, and other embedded
datasets are deliberately rejected so saving a visual design never duplicates
or leaks the underlying data.

All public functions return deep copies.  File updates use ``os.replace`` in
the destination directory, keeping the previous valid JSON file intact if a
write is interrupted.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from vap_atomic_io import atomic_write_json, file_transaction_lock
from vap_data_adapter import sanitize_connection_url


CHART_LIBRARY_SCHEMA = "VIA-VAP-CHART-LIBRARY/1.0"
CHART_LIBRARY_VERSION = "2.3.0"
DEFAULT_CHART_LIBRARY_FILENAME = "vap_chart_library.json"

_WINDOWS_RESERVED_BASENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
_FORBIDDEN_EMBEDDED_DATA_KEYS = {
    "records",
    "rows",
    "data_rows",
    "raw_rows",
    "raw_data",
    "dataframe",
    "data_frame",
    "frame",
    "table_data",
    "dataset_content",
    "data_content",
    "plotly_traces",
}
_ALLOWED_CHART_LIST_KEYS = {"y", "secondary_y", "normalized_y", "series"}
_ALLOWED_CHART_MAPPING_KEYS = {
    "colors",
    "data_source",
    "left_axis",
    "right_axis",
}
_SENSITIVE_FIELD_TOKENS = {
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "private_key",
    "passphrase",
    "signature",
    "credential",
    "connect_args",
}
MAX_CHART_SPEC_BYTES = 65_536


def utc_now_text() -> str:
    """Return a compact, timezone-aware timestamp for file metadata."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_chart_library() -> dict[str, Any]:
    """Create a fresh empty chart-library document."""

    now = utc_now_text()
    return {
        "schema": CHART_LIBRARY_SCHEMA,
        "version": CHART_LIBRARY_VERSION,
        "metadata": {
            "created_at": now,
            "updated_at": now,
            "item_count": 0,
        },
        "items": [],
    }


def _path(value: str | Path) -> Path:
    return Path(value).expanduser()


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write JSON beside ``path`` and atomically replace its final name."""

    atomic_write_json(path, value)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"圖庫 JSON 格式錯誤：{path}；{exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("圖庫根節點必須是 JSON object。")
    return value


def _ensure_json_value(value: Any, field_name: str) -> None:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必須可安全儲存為 JSON。") from exc


def _assert_data_free(value: Any, path: str = "chart") -> None:
    """Reject common embedded row/trace payloads while allowing source refs."""

    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            folded = key.casefold()
            child_path = f"{path}.{key}"
            if path == "chart" and isinstance(child, Mapping):
                if folded not in _ALLOWED_CHART_MAPPING_KEYS and child:
                    raise ValueError(f"圖庫 chart 不支援可疑的內嵌 object：{child_path}")
            if path == "chart" and isinstance(child, (list, tuple)):
                if folded not in _ALLOWED_CHART_LIST_KEYS and child:
                    raise ValueError(f"圖庫 chart 不可保存未知內嵌資料內容陣列：{child_path}")
                if any(not isinstance(item, str) for item in child):
                    raise ValueError(f"圖庫欄位清單只能包含欄位名稱：{child_path}")
            if folded in _FORBIDDEN_EMBEDDED_DATA_KEYS:
                is_embedded_collection = isinstance(child, (list, tuple, Mapping)) and bool(child)
                is_embedded_blob = isinstance(child, (bytes, bytearray, memoryview)) and bool(child)
                if is_embedded_collection or is_embedded_blob:
                    raise ValueError(f"圖庫不可保存資料內容：{child_path}")
            # ``data`` and ``dataset`` may be a path/reference string in a VAP
            # chart spec, but a list/object here is an embedded dataset.
            if folded in {"data", "dataset"} and isinstance(child, (list, tuple, Mapping)):
                if child:
                    raise ValueError(f"圖庫不可保存內嵌資料：{child_path}")
            _assert_data_free(child, child_path)
    elif isinstance(value, (list, tuple)):
        if any(isinstance(child, (Mapping, list, tuple)) for child in value):
            raise ValueError(f"圖庫不可保存 records 型態的巢狀陣列：{path}")
        if any(not isinstance(child, str) for child in value):
            raise ValueError(f"圖庫陣列只能保存欄位名稱字串：{path}")
        if len(value) > 256:
            raise ValueError(f"圖庫欄位清單過長：{path}")
        for index, child in enumerate(value):
            _assert_data_free(child, f"{path}[{index}]")


def _redact_chart_secrets(
    value: Any,
    *,
    in_source: bool = False,
) -> Any:
    """Return a deep, source-reference-safe copy for reusable gallery specs."""

    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = str(raw_key)
            with_acronym_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", key)
            with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_acronym_boundaries)
            folded = re.sub(r"[^a-z0-9]+", "_", with_word_boundaries.casefold()).strip("_")
            child_in_source = in_source or folded == "data_source"
            is_sensitive = any(
                folded == token or folded.endswith(f"_{token}")
                for token in _SENSITIVE_FIELD_TOKENS
            )
            if is_sensitive:
                result[key] = "REDACTED"
            elif child_in_source and folded == "query" and str(child).strip():
                result[key] = "REDACTED"
                result["query_present"] = True
            elif isinstance(child, str) and "://" in child:
                result[key] = sanitize_connection_url(child)
            else:
                result[key] = _redact_chart_secrets(child, in_source=child_in_source)
        return result
    if isinstance(value, list):
        return [_redact_chart_secrets(item, in_source=in_source) for item in value]
    if isinstance(value, tuple):
        return [_redact_chart_secrets(item, in_source=in_source) for item in value]
    return deepcopy(value)


def _safe_identifier(value: Any, field_name: str) -> str:
    name = str(value).strip()
    invalid_characters = '<>:"/\\|?*'
    if not name:
        raise ValueError(f"{field_name} 不可為空白。")
    if name in {".", ".."} or name.endswith((".", " ")):
        raise ValueError(f"{field_name} 必須是安全的單一識別碼：{name!r}")
    if any(character in invalid_characters or ord(character) < 32 for character in name):
        raise ValueError(f"{field_name} 不可含路徑或非法字元：{name!r}")
    if name.split(".", 1)[0].upper() in _WINDOWS_RESERVED_BASENAMES:
        raise ValueError(f"{field_name} 不可使用 Windows 保留名稱：{name!r}")
    return name


def _identifier_from_text(value: Any, fallback: str = "chart") -> str:
    text = str(value).strip()
    candidate = re.sub(r"[^\w.-]+", "_", text, flags=re.UNICODE).strip("_.")
    if not candidate:
        candidate = fallback
    if candidate.split(".", 1)[0].upper() in _WINDOWS_RESERVED_BASENAMES:
        candidate = f"{candidate}_chart"
    return _safe_identifier(candidate, "圖庫項目 id")


def _unique_identifier(existing_ids: Iterable[str], preferred: str) -> str:
    existing = {str(value) for value in existing_ids}
    base = _safe_identifier(preferred, "chart id")
    candidate = base
    counter = 2
    while candidate in existing:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def normalize_tags(tags: Iterable[Any] | str | None) -> list[str]:
    """Strip, deduplicate, and preserve the display casing of tags."""

    if tags is None:
        return []
    if isinstance(tags, str):
        values = tags.split(",")
    else:
        try:
            values = list(tags)
        except TypeError as exc:
            raise ValueError("tags 必須是逗號分隔字串或可迭代的標籤。") from exc
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value).strip()
        folded = tag.casefold()
        if tag and folded not in seen:
            result.append(tag)
            seen.add(folded)
    return result


def validate_chart_spec(chart_spec: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and copy a reusable chart spec without changing defaults."""

    if not isinstance(chart_spec, Mapping):
        raise ValueError("chart_spec 必須是 JSON object。")
    chart = _redact_chart_secrets(dict(chart_spec))
    chart["id"] = _safe_identifier(chart.get("id", ""), "圖表 id")
    chart_type = str(chart.get("type", "")).strip()
    if not chart_type:
        raise ValueError("圖表 type 不可為空白。")
    chart["type"] = chart_type
    if "title" in chart and not isinstance(chart["title"], str):
        raise ValueError("圖表 title 必須是字串。")
    if "x" in chart and not isinstance(chart["x"], str):
        raise ValueError("圖表 x 必須是欄位名稱字串。")
    for key in ("y", "secondary_y", "normalized_y"):
        if key not in chart:
            continue
        value = chart[key]
        if isinstance(value, str):
            chart[key] = [part.strip() for part in value.split(",") if part.strip()]
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            chart[key] = [item.strip() for item in value if item.strip()]
        else:
            raise ValueError(f"圖表 {key} 必須是字串陣列。")
    _assert_data_free(chart)
    _ensure_json_value(chart, "chart_spec")
    serialized_size = len(json.dumps(chart, ensure_ascii=False).encode("utf-8"))
    if serialized_size > MAX_CHART_SPEC_BYTES:
        raise ValueError(
            f"chart_spec 超過 {MAX_CHART_SPEC_BYTES // 1024} KiB；圖庫只保存精簡規格，不保存資料內容。"
        )
    return chart


def _validate_item(item: Mapping[str, Any], position: int) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ValueError(f"第 {position} 個圖庫項目必須是 JSON object。")
    result = deepcopy(dict(item))
    result["id"] = _safe_identifier(result.get("id", ""), f"第 {position} 個圖庫項目 id")
    result["name"] = str(result.get("name", "")).strip()
    if not result["name"]:
        raise ValueError(f"第 {position} 個圖庫項目 name 不可為空白。")
    result["description"] = str(result.get("description", "")).strip()
    result["tags"] = normalize_tags(result.get("tags"))
    result["chart"] = validate_chart_spec(result.get("chart", {}))
    result["chart_type"] = str(result.get("chart_type") or result["chart"]["type"]).strip()
    if result["chart_type"] != result["chart"]["type"]:
        raise ValueError(f"第 {position} 個圖庫項目的 chart_type 與 chart.type 不一致。")
    metadata = result.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError(f"第 {position} 個圖庫項目 metadata 必須是 JSON object。")
    result["metadata"] = _redact_chart_secrets(dict(metadata))
    _assert_data_free(result["metadata"], f"items[{position - 1}].metadata")
    _ensure_json_value(result["metadata"], "item metadata")
    if len(json.dumps(result["metadata"], ensure_ascii=False).encode("utf-8")) > MAX_CHART_SPEC_BYTES:
        raise ValueError("圖庫 item metadata 過大；不可用 metadata 保存資料內容。")
    return result


def validate_chart_library(library: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a library document and return a normalized deep copy."""

    if not isinstance(library, Mapping):
        raise ValueError("圖庫根節點必須是 JSON object。")
    result = deepcopy(dict(library))
    if result.get("schema") != CHART_LIBRARY_SCHEMA:
        raise ValueError(
            f"不支援的圖庫 schema：{result.get('schema')!r}；預期 {CHART_LIBRARY_SCHEMA}。"
        )
    if result.get("version") != CHART_LIBRARY_VERSION:
        raise ValueError(
            f"不支援的圖庫 version：{result.get('version')!r}；預期 {CHART_LIBRARY_VERSION}。"
        )
    items = result.get("items")
    if not isinstance(items, list):
        raise ValueError("圖庫 items 必須是 JSON array。")
    normalized_items = [_validate_item(item, index) for index, item in enumerate(items, start=1)]
    item_ids = [item["id"] for item in normalized_items]
    if len(set(item_ids)) != len(item_ids):
        raise ValueError("圖庫項目 id 不可重複。")
    metadata = result.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("圖庫 metadata 必須是 JSON object。")
    result["metadata"] = _redact_chart_secrets(dict(metadata))
    _assert_data_free(result["metadata"], "metadata")
    if len(json.dumps(result["metadata"], ensure_ascii=False).encode("utf-8")) > MAX_CHART_SPEC_BYTES:
        raise ValueError("圖庫 metadata 過大；不可用 metadata 保存資料內容。")
    result["metadata"]["item_count"] = len(normalized_items)
    result["items"] = normalized_items
    _ensure_json_value(result, "chart library")
    return result


def load_chart_library(
    path: str | Path,
    *,
    create: bool = True,
) -> dict[str, Any]:
    """Load a chart library, optionally creating an empty one when absent."""

    library_path = _path(path)
    with file_transaction_lock(library_path):
        if not library_path.exists():
            if not create:
                raise FileNotFoundError(f"找不到圖庫：{library_path}")
            library = default_chart_library()
            _atomic_write_json(library_path, library)
            return deepcopy(library)
        return validate_chart_library(_read_json(library_path))


def save_chart_library(path: str | Path, library: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and atomically save a complete chart-library document."""

    library_path = _path(path)
    with file_transaction_lock(library_path):
        normalized = validate_chart_library(library)
        metadata = normalized.setdefault("metadata", {})
        metadata.setdefault("created_at", utc_now_text())
        metadata["updated_at"] = utc_now_text()
        metadata["item_count"] = len(normalized["items"])
        _atomic_write_json(library_path, normalized)
        return deepcopy(normalized)


def get_chart_item(library: Mapping[str, Any] | str | Path, item_id: str) -> dict[str, Any]:
    """Return one library item or raise ``KeyError``."""

    document = (
        load_chart_library(library, create=False)
        if isinstance(library, (str, Path))
        else validate_chart_library(library)
    )
    requested = str(item_id)
    for item in document["items"]:
        if item["id"] == requested:
            return deepcopy(item)
    raise KeyError(f"找不到圖庫項目 id：{requested}")


def upsert_chart(
    library_path: str | Path,
    chart_spec: Mapping[str, Any],
    *,
    name: str | None = None,
    tags: Iterable[Any] | str | None = None,
    description: str | None = None,
    item_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a library item, or overwrite the explicitly selected item.

    Omitting ``item_id`` always creates a new item with a collision-free id.
    Supplying an existing ``item_id`` overwrites that item's design while
    preserving its original ``created_at`` timestamp.
    """

    with file_transaction_lock(library_path):
        chart = validate_chart_spec(chart_spec)
        library = load_chart_library(library_path, create=True)
        items = library["items"]
        target_index = None
        if item_id is not None:
            requested_id = _safe_identifier(item_id, "圖庫項目 id")
            target_index = next(
                (index for index, item in enumerate(items) if item["id"] == requested_id),
                None,
            )
            final_item_id = requested_id
        else:
            preferred = _identifier_from_text(name or chart.get("id") or chart.get("title") or "chart")
            final_item_id = _unique_identifier((item["id"] for item in items), preferred)

        previous = items[target_index] if target_index is not None else None
        if name is not None:
            display_name = str(name).strip()
        elif previous is not None:
            display_name = previous["name"]
        else:
            display_name = str(chart.get("title") or chart["id"]).strip()
        if not display_name:
            raise ValueError("圖庫項目 name 不可為空白。")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ValueError("metadata 必須是 JSON object。")
        item_metadata = deepcopy(dict((previous or {}).get("metadata", {})))
        item_metadata.update(deepcopy(dict(metadata or {})))
        item_metadata = _redact_chart_secrets(item_metadata)
        _assert_data_free(item_metadata, "metadata")
        _ensure_json_value(item_metadata, "metadata")
        now = utc_now_text()
        item_metadata["created_at"] = (
            str((previous or {}).get("metadata", {}).get("created_at") or now)
        )
        item_metadata["updated_at"] = now
        item_metadata["source_chart_id"] = chart["id"]
        final_tags = (
            normalize_tags(tags)
            if tags is not None
            else deepcopy((previous or {}).get("tags", []))
        )
        final_description = (
            str(description).strip()
            if description is not None
            else str((previous or {}).get("description", "")).strip()
        )
        item = _validate_item(
            {
                "id": final_item_id,
                "name": display_name,
                "description": final_description,
                "tags": final_tags,
                "chart_type": chart["type"],
                "chart": chart,
                "metadata": item_metadata,
            },
            (target_index + 1) if target_index is not None else (len(items) + 1),
        )
        if target_index is None:
            items.append(item)
        else:
            items[target_index] = item
        save_chart_library(library_path, library)
        return deepcopy(item)


def delete_chart(library_path: str | Path, item_id: str) -> bool:
    """Delete a library item; return ``False`` when it did not exist."""

    with file_transaction_lock(library_path):
        library = load_chart_library(library_path, create=True)
        requested = str(item_id)
        remaining = [item for item in library["items"] if item["id"] != requested]
        if len(remaining) == len(library["items"]):
            return False
        library["items"] = remaining
        save_chart_library(library_path, library)
        return True


def search_charts(
    library: Mapping[str, Any] | str | Path,
    *,
    query: str = "",
    tags: Iterable[Any] | str | None = None,
    chart_type: str | None = None,
) -> list[dict[str, Any]]:
    """Search by free text, required tags, and an exact chart type.

    Free text is matched case-insensitively against name, description, tags,
    chart type, original chart id, and chart title.  When several tags are
    supplied, every requested tag must be present.
    """

    document = (
        load_chart_library(library, create=False)
        if isinstance(library, (str, Path))
        else validate_chart_library(library)
    )
    needle = query.strip().casefold()
    requested_tags = {tag.casefold() for tag in normalize_tags(tags)}
    requested_type = str(chart_type or "").strip().casefold()
    matches: list[dict[str, Any]] = []
    for item in document["items"]:
        item_tags = {tag.casefold() for tag in item["tags"]}
        if requested_tags and not requested_tags.issubset(item_tags):
            continue
        if requested_type and item["chart_type"].casefold() != requested_type:
            continue
        chart = item["chart"]
        searchable_fields: list[str] = []
        for field_name in (
            "x",
            "y",
            "secondary_y",
            "normalized_y",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "unit",
            "secondary_unit",
        ):
            field_value = chart.get(field_name)
            if isinstance(field_value, list):
                searchable_fields.extend(str(value) for value in field_value)
            elif field_value not in (None, ""):
                searchable_fields.append(str(field_value))
        haystack = "\n".join(
            [
                item["name"],
                item["description"],
                *item["tags"],
                item["chart_type"],
                str(chart.get("id", "")),
                str(chart.get("title", "")),
                *searchable_fields,
            ]
        ).casefold()
        if needle and needle not in haystack:
            continue
        matches.append(deepcopy(item))
    return matches


def instantiate_chart(
    item: Mapping[str, Any],
    *,
    existing_ids: Iterable[str] = (),
    preferred_id: str | None = None,
) -> dict[str, Any]:
    """Clone one library item into a collision-free chart specification."""

    normalized_item = _validate_item(item, 1)
    chart = deepcopy(normalized_item["chart"])
    preferred = str(preferred_id or chart.get("id") or normalized_item["id"]).strip()
    preferred = _safe_identifier(preferred, "圖表 id")
    chart["id"] = _unique_identifier(existing_ids, preferred)
    chart["gallery_item_id"] = normalized_item["id"]
    chart["gallery_item_name"] = normalized_item["name"]
    return chart


def append_library_chart(
    config_path: str | Path,
    library_path: str | Path,
    item_id: str,
    *,
    preferred_id: str | None = None,
) -> dict[str, Any]:
    """Instantiate a library item and append it to a VAP stack config."""

    item = get_chart_item(library_path, item_id)
    stack_path = _path(config_path)
    with file_transaction_lock(stack_path):
        config = _read_json(stack_path)
        charts = config.setdefault("charts", [])
        if not isinstance(charts, list):
            raise ValueError("設定檔 charts 必須是 JSON array。")
        if any(not isinstance(chart, Mapping) for chart in charts):
            raise ValueError("設定檔中的每個 chart 都必須是 JSON object。")
        chart = instantiate_chart(
            item,
            existing_ids=(str(existing.get("id", "")) for existing in charts),
            preferred_id=preferred_id,
        )
        charts.append(chart)
        metadata = config.setdefault("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("設定檔 metadata 必須是 JSON object。")
        metadata["updated_at"] = utc_now_text()
        _ensure_json_value(config, "stack config")
        _atomic_write_json(stack_path, config)
        return deepcopy(chart)


__all__ = [
    "CHART_LIBRARY_SCHEMA",
    "CHART_LIBRARY_VERSION",
    "DEFAULT_CHART_LIBRARY_FILENAME",
    "append_library_chart",
    "default_chart_library",
    "delete_chart",
    "get_chart_item",
    "instantiate_chart",
    "load_chart_library",
    "normalize_tags",
    "save_chart_library",
    "search_charts",
    "upsert_chart",
    "validate_chart_library",
    "validate_chart_spec",
]
