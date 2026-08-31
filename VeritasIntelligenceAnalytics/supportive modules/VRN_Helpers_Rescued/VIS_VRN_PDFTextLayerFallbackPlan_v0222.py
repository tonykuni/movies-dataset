"""VIA v0142 compatibility shim for a missing historical VRN helper.

This is NOT a recovered original implementation.

Governance:
- staging plan only
- no OCR
- no PDF parsing
- no database writes
- no SSOT mutation
- no network
- no import-time filesystem writes

The shim exists solely to satisfy the two statically proven interfaces used by
Invoke-VRN-MQ-NoOCR-Staging-v222.ps1:
- def_build_noocr_candidate
- def_to_dict
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

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

__version__ = "0.14.2"
__module_id__ = "VIS_VRN_PDFTextLayerFallbackPlan_v0222_COMPAT"
__compatibility_mode__ = "STAGING_ONLY_NOOCR_NO_DB_NO_SSOT"
__recovered_original__ = False


@dataclass(frozen=True)
class NoOCRStagingCandidate:
    gate: str
    mode: str
    target_file: str
    target_exists: bool
    target_suffix: str
    target_bytes: int
    broker_helper_loaded: bool
    ocr_allowed: bool
    pdf_parsing_executed: bool
    database_write_allowed: bool
    ssot_mutation_allowed: bool
    network_allowed: bool
    compatibility_shim: bool
    source_module: str
    decision: str


def _first_pathlike(args: Sequence[Any], kwargs: Mapping[str, Any]) -> str:
    preferred_keys = (
        "target_file",
        "target",
        "pdf_path",
        "path",
        "file_path",
        "source",
    )

    for key in preferred_keys:
        value = kwargs.get(key)

        if isinstance(value, (str, Path)) and str(value).strip():
            return str(value)

    for value in args:
        if isinstance(value, Path):
            return str(value)

        if isinstance(value, str) and value.strip():
            candidate = value.strip()

            if (
                candidate.lower().endswith(".pdf")
                or "\\" in candidate
                or "/" in candidate
            ):
                return candidate

    return ""


def _broker_helper_present(args: Sequence[Any], kwargs: Mapping[str, Any]) -> bool:
    preferred_keys = (
        "broker_helper",
        "broker_module",
        "broker_alias_module",
        "broker",
    )

    for key in preferred_keys:
        if kwargs.get(key) is not None:
            return True

    for value in args:
        if hasattr(value, "__name__") or hasattr(value, "__file__"):
            return True

    return False


def def_build_noocr_candidate(*args: Any, **kwargs: Any) -> NoOCRStagingCandidate:
    """Build a metadata-only staging plan.

    The function deliberately does not open or parse the PDF. It accepts
    flexible arguments because the historical helper signature is unavailable.
    """

    target_text = _first_pathlike(args, kwargs)
    target_path = Path(target_text).expanduser() if target_text else None

    target_exists = bool(target_path and target_path.is_file())
    target_suffix = target_path.suffix.lower() if target_path else ""
    target_bytes = target_path.stat().st_size if target_exists else 0

    if not target_text:
        gate = "NOOCR_STAGING_TARGET_NOT_IDENTIFIED"
        decision = "No target path could be identified from the call."
    elif target_suffix != ".pdf":
        gate = "NOOCR_STAGING_TARGET_NOT_PDF"
        decision = "The supplied target does not have a .pdf suffix."
    elif not target_exists:
        gate = "NOOCR_STAGING_TARGET_MISSING"
        decision = "The supplied PDF target does not exist."
    else:
        gate = "NOOCR_STAGING_PLAN_READY"
        decision = (
            "Metadata-only staging plan created. No OCR, PDF parsing, "
            "database write, SSOT mutation or network access was executed."
        )

    return NoOCRStagingCandidate(
        gate=gate,
        mode="NO_OCR_STAGING_ONLY",
        target_file=str(target_path) if target_path else target_text,
        target_exists=target_exists,
        target_suffix=target_suffix,
        target_bytes=target_bytes,
        broker_helper_loaded=_broker_helper_present(args, kwargs),
        ocr_allowed=False,
        pdf_parsing_executed=False,
        database_write_allowed=False,
        ssot_mutation_allowed=False,
        network_allowed=False,
        compatibility_shim=True,
        source_module=__module_id__,
        decision=decision,
    )


def def_to_dict(value: Any) -> Any:
    """Convert common Python objects to JSON-safe structures."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Enum):
        return def_to_dict(value.value)

    if isinstance(value, Path):
        return str(value)

    if is_dataclass(value):
        return {
            field.name: def_to_dict(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, Mapping):
        return {
            str(key): def_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [def_to_dict(item) for item in value]

    if hasattr(value, "model_dump") and callable(value.model_dump):
        return def_to_dict(value.model_dump())

    if hasattr(value, "dict") and callable(value.dict):
        return def_to_dict(value.dict())

    if hasattr(value, "__dict__"):
        return {
            str(key): def_to_dict(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }

    return str(value)


__all__ = [
    "NoOCRStagingCandidate",
    "def_build_noocr_candidate",
    "def_to_dict",
]
