"""Stable, collision-resistant email identity (UID v2)."""

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
import re
from typing import Any, Dict


def _norm(value: Any) -> str:
    """Normalize a field for hashing: strip, lower, collapse whitespace."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def generate_uid_v2(email: Dict[str, Any], length: int = 16) -> str:
    """
    Generate a deterministic short UID from core email fields.

    Includes project/dept when available so the same logical thread
    under different mappings still produces a stable identity.
    """
    parts = [
        _norm(email.get("sender")),
        _norm(email.get("receiver")),
        _norm(email.get("subject")),
        _norm(email.get("timestamp")),
        _norm(email.get("project")),
        _norm(email.get("dept")),
        _norm(email.get("message_id")),  # optional RFC822 Message-ID
    ]
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest[: max(8, min(length, 64))]
