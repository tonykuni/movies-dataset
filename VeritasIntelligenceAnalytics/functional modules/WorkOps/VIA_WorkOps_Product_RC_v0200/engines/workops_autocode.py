# -*- coding: utf-8 -*-
"""Shared immutable auto-code component.
Format: AAA-YYYYMMDD-NNNNNN. JSON sequence registry + atomic write.
"""
from __future__ import annotations
import json, os, time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
SEQ_P = OUT / "autocode_sequence.json"
LOCK_P = OUT / ".autocode_sequence.lock"

def _load():
    try:
        return json.loads(SEQ_P.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"version":"v0100","sequences":{}}

def _atomic(obj):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = SEQ_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SEQ_P)

class _Lock:
    def __init__(self, timeout=5.0): self.timeout=timeout
    def __enter__(self):
        OUT.mkdir(parents=True, exist_ok=True)
        end=time.time()+self.timeout
        while True:
            try:
                self.fd=os.open(str(LOCK_P), os.O_CREAT|os.O_EXCL|os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode())
                return self
            except FileExistsError:
                if time.time()>end: raise TimeoutError("autocode registry lock timeout")
                time.sleep(0.05)
    def __exit__(self,*_):
        try: os.close(self.fd)
        except Exception: pass
        try: LOCK_P.unlink()
        except Exception: pass

def next_code(prefix: str, event_date=None, width=6) -> str:
    prefix=(prefix or "").strip().upper()
    if len(prefix)!=3 or not prefix.isalpha():
        raise ValueError("prefix must be exactly three letters")
    if event_date is None:
        day=datetime.now().strftime("%Y%m%d")
    elif isinstance(event_date, datetime):
        day=event_date.strftime("%Y%m%d")
    else:
        s=str(event_date).replace("-","")[:8]
        if len(s)!=8 or not s.isdigit():
            raise ValueError("event_date must be YYYY-MM-DD / YYYYMMDD")
        day=s
    key=f"{prefix}|{day}"
    with _Lock():
        doc=_load()
        seqs=doc.setdefault("sequences",{})
        n=int(seqs.get(key,0))+1
        seqs[key]=n
        doc["updated_at"]=datetime.now().isoformat(timespec="seconds")
        _atomic(doc)
    return f"{prefix}-{day}-{n:0{width}d}"
