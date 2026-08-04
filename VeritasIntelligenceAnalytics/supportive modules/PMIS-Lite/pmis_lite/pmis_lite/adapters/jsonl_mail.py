"""讀 mail_fetched.jsonl → Record（讓自動擷取的郵件直接進 SSOT pipeline）。"""
from __future__ import annotations
import json, os


class JsonlMailAdapter:
    def __init__(self, path: str, audit=None):
        self.path = path
        self.audit = audit
        self.source_type = "mail_jsonl"

    def read(self):
        from ..schema import Record
        a = self.audit.audit("mail_jsonl") if self.audit else None
        if not os.path.exists(self.path):
            return
        for line in open(self.path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            if a:
                a.seen += 1
            try:
                d = json.loads(line)
            except Exception as e:
                if a:
                    a.failures.append((line[:30], f"json:{e.__class__.__name__}"))
                continue
            r = Record(
                title=d.get("title", ""), body=d.get("body", ""), actor=d.get("actor", ""),
                counterparts=d.get("counterparts", ""), event_time=d.get("event_time", ""),
                source_type=d.get("source_type", "mail"), source_ref=d.get("source_ref", ""),
                raw_keys=d.get("raw_keys", ""), thread_id=d.get("thread_id", ""))
            if a:
                a.extracted += 1
            yield r
