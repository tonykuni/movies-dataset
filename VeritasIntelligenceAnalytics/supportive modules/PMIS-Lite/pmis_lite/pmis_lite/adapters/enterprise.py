"""企業系統來源 adapter：讀 CSV/HTML → 套 preset 對照 → Record。"""
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
import csv, os


class EnterpriseAdapter:
    def __init__(self, path: str, preset: str, overrides=None, audit=None):
        self.path = path
        self.preset = preset
        self.overrides = overrides
        self.audit = audit
        self.source_type = preset

    def read(self):
        from ..presets import apply_preset
        from .. import html_ui
        a = self.audit.audit(self.preset) if self.audit else None
        if not os.path.exists(self.path):
            return
        if self.path.lower().endswith((".html", ".htm")):
            rows = html_ui.tables_as_dicts(open(self.path, encoding="utf-8").read())
        else:
            rows = list(csv.DictReader(open(self.path, encoding="utf-8-sig")))
        if a:
            a.seen += len(rows)
        for rec in apply_preset(rows, self.preset, self.overrides):
            if a:
                a.extracted += 1
            yield rec
