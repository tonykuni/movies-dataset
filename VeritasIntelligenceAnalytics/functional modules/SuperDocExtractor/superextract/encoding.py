"""Encoding detection and byte decoding (編碼問題核心).

Detection chain, most reliable first:
  1. BOM sniffing (UTF-8-SIG / UTF-16 / UTF-32)
  2. charset_normalizer (if installed)
  3. chardet (if installed)
  4. Heuristic candidate loop with scoring
     (utf-8 -> cp950/Big5 -> gb18030 -> shift_jis -> cp1252 -> latin-1)

Every decision is recorded so the final report can show *how* the bytes
were interpreted (修復驗證對照 traceability).
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import codecs
from dataclasses import dataclass, field

from .availability import has, load

BOMS = [
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
]

#: Candidate order for the heuristic fallback. cp950 before gb18030 because
#: this tool's primary audience works with Traditional Chinese documents;
#: override with an explicit encoding when that assumption is wrong.
HEURISTIC_CANDIDATES = [
    "utf-8", "cp950", "big5hkscs", "gb18030", "shift_jis", "cp1252", "latin-1",
]


@dataclass
class DetectionResult:
    encoding: str
    confidence: float          # 0.0 - 1.0
    method: str                # bom / charset_normalizer / chardet / heuristic / explicit
    bom_bytes: int = 0
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "encoding": self.encoding,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "bom_bytes": self.bom_bytes,
            "notes": list(self.notes),
        }


def sniff_bom(data: bytes):
    """Return (encoding, bom_length) or (None, 0)."""
    # UTF-32 first: its BOM starts with the UTF-16 BOM bytes.
    for bom, enc in BOMS:
        if data.startswith(bom):
            return enc, len(bom)
    return None, 0


def _decode_score(text: str) -> float:
    """Higher is better. Penalise replacement chars and mojibake markers,
    reward CJK content (this tool's documents are mostly Chinese)."""
    if not text:
        return 0.0
    n = len(text)
    repl = text.count("\ufffd")
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    # Latin-1 supplement chars are legal but, in bulk, usually indicate a
    # wrong single-byte decode of multi-byte CJK data.
    latin_supp = sum(1 for ch in text if "\u0080" <= ch <= "\u00ff" and ch != "\xa0")
    ctrl = sum(1 for ch in text if ord(ch) < 32 and ch not in "\r\n\t")
    return (-40.0 * repl - 2.0 * latin_supp - 10.0 * ctrl + 1.0 * cjk) / n


def detect_encoding(data: bytes) -> DetectionResult:
    """Best-effort encoding detection for a byte payload."""
    if not data:
        return DetectionResult("utf-8", 1.0, "empty")

    enc, bom_len = sniff_bom(data)
    if enc:
        return DetectionResult(enc, 1.0, "bom", bom_bytes=bom_len)

    sample = data[: 512 * 1024]  # cap work on huge files

    # UTF-8 first: it is self-validating (legacy CJK byte streams almost
    # never form valid UTF-8), and mojibake that *is* valid UTF-8 must be
    # decoded as UTF-8 so the downstream repair step can fix it — detectors
    # like charset_normalizer may otherwise "hear" a plausible language in
    # the noise and pick a wrong legacy codec.
    try:
        sample.decode("utf-8")
        return DetectionResult("utf-8", 0.99, "utf8-strict")
    except UnicodeDecodeError:
        pass

    if has("charset_normalizer"):
        cn = load("charset_normalizer")
        best = cn.from_bytes(sample).best()
        if best is not None and best.encoding:
            res = DetectionResult(best.encoding, 1.0 - best.chaos, "charset_normalizer")
            # cn labels Traditional Chinese as big5; prefer the cp950 superset.
            if res.encoding.lower() in ("big5", "big5hkscs"):
                res.notes.append(f"{res.encoding} widened to cp950 superset")
                res.encoding = "cp950"
            return res

    if has("chardet"):
        cd = load("chardet")
        guess = cd.detect(sample)
        if guess and guess.get("encoding"):
            return DetectionResult(guess["encoding"], float(guess.get("confidence") or 0.0), "chardet")

    # Heuristic loop: strict decode, keep the best-scoring candidate.
    best_enc, best_score = None, float("-inf")
    for cand in HEURISTIC_CANDIDATES:
        try:
            text = sample.decode(cand)
        except (UnicodeDecodeError, LookupError):
            continue
        score = _decode_score(text)
        if cand == "utf-8":
            # UTF-8 is self-validating: a strict success is near-certain.
            return DetectionResult("utf-8", 0.99, "heuristic")
        if score > best_score:
            best_enc, best_score = cand, score
    if best_enc is None:  # latin-1 never fails, so we should not get here
        best_enc = "latin-1"
    return DetectionResult(best_enc, 0.5, "heuristic",
                           notes=["ambiguous single/multi-byte data; pass an explicit encoding to override"])


def decode_bytes(data: bytes, encoding: str | None = None):
    """Decode *data* -> (text, DetectionResult).

    With an explicit *encoding* the detection chain is skipped; decode errors
    then fall back to replacement characters instead of crashing, and the
    fallback is recorded in the result notes.
    """
    if encoding:
        enc, bom_len = sniff_bom(data)
        payload = data[bom_len:] if enc else data
        try:
            return payload.decode(encoding), DetectionResult(encoding, 1.0, "explicit", bom_bytes=bom_len)
        except (UnicodeDecodeError, LookupError) as exc:
            res = DetectionResult(encoding, 0.0, "explicit", bom_bytes=bom_len,
                                  notes=[f"explicit encoding failed ({exc}); decoded with errors='replace'"])
            return payload.decode(encoding, errors="replace"), res

    res = detect_encoding(data)
    payload = data[res.bom_bytes:]
    try:
        return payload.decode(res.encoding), res
    except (UnicodeDecodeError, LookupError) as exc:
        res.notes.append(f"detected encoding failed on full payload ({exc}); errors='replace' applied")
        res.confidence = min(res.confidence, 0.3)
        return payload.decode(res.encoding, errors="replace"), res


def read_text_auto(path, encoding: str | None = None):
    """Read a file with encoding auto-detection -> (text, DetectionResult)."""
    with open(path, "rb") as fh:
        return decode_bytes(fh.read(), encoding=encoding)
