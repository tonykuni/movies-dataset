"""企業系統來源 adapter：讀 CSV/HTML → 套 preset 對照 → Record。"""
from __future__ import annotations
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
