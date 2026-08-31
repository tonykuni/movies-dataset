"""Normalize raw email payloads into a canonical internal schema."""

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

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    # comma / semicolon separated
    return [p.strip() for p in re.split(r"[,;]", str(value)) if p.strip()]


def _parse_timestamp(raw: Any) -> Optional[str]:
    if raw is None or raw == "":
        return None
    if isinstance(raw, datetime):
        return raw.isoformat()
    text = str(raw).strip()
    # Keep original string if we cannot parse; downstream may still use it
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y/%m/%d %H:%M",
    ):
        try:
            return datetime.strptime(text, fmt).isoformat()
        except ValueError:
            continue
    return text


def parse_email(raw_email: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonical email record.

    Accepts flexible keys (From/To/Subject/Body/Date aliases)
    and returns a stable schema used by the rest of the pipeline.
    """
    if not isinstance(raw_email, dict):
        raise TypeError("raw_email must be a dict")

    sender = (
        raw_email.get("sender")
        or raw_email.get("from")
        or raw_email.get("From")
        or ""
    )
    receiver = (
        raw_email.get("receiver")
        or raw_email.get("to")
        or raw_email.get("To")
        or ""
    )
    cc = raw_email.get("cc") or raw_email.get("Cc") or []
    subject = (
        raw_email.get("subject")
        or raw_email.get("Subject")
        or ""
    )
    body = (
        raw_email.get("body")
        or raw_email.get("Body")
        or raw_email.get("text")
        or ""
    )
    timestamp = _parse_timestamp(
        raw_email.get("timestamp")
        or raw_email.get("date")
        or raw_email.get("Date")
    )
    message_id = (
        raw_email.get("message_id")
        or raw_email.get("Message-ID")
        or raw_email.get("messageId")
        or ""
    )

    return {
        "sender": str(sender).strip(),
        "receiver": str(receiver).strip(),
        "cc": _as_list(cc),
        "subject": str(subject).strip(),
        "body": str(body).strip(),
        "timestamp": timestamp or "",
        "message_id": str(message_id).strip(),
    }
