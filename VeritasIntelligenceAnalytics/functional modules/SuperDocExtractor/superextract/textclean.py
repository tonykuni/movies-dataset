"""Text repair (修復): mojibake, invisible characters, normalization.

Every applied fix is returned as an audit entry so reports can show exactly
what was changed — nothing is silently rewritten.
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

import re
import unicodedata
from dataclasses import dataclass, field

from .availability import has, load

#: Zero-width and BOM-ish characters that break string comparison ("幽靈差異").
ZERO_WIDTH = "\u200b\u200c\u200d\u2060\ufeff\u00ad"
_ZW_RE = re.compile("[%s]" % ZERO_WIDTH)
#: C0/C1 control chars except \t \n \r.
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_MULTI_BLANK_RE = re.compile(r"\n\s*\n+")
_SPACE_RUN_RE = re.compile(r"[ \t\f\v]+")

#: Byte-sequences-seen-as-latin1 markers that flag likely mojibake.
_MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\u00e2\u20ac", "\u00e5", "\u00e4\u00b8", "\u00e7", "\u00e6", "\u00ef\u00bb\u00bf", "\u00ef\u00bc", "\ufffd")


@dataclass
class CleanResult:
    text: str
    fixes: list = field(default_factory=list)   # human-readable audit entries

    def as_dict(self) -> dict:
        return {"chars": len(self.text), "fixes": list(self.fixes)}


def mojibake_score(text: str) -> int:
    """Rough count of mojibake evidence in *text* (0 = looks clean)."""
    score = sum(text.count(m) for m in _MOJIBAKE_MARKERS)
    # Long runs of Latin-1 supplement characters are another strong signal.
    score += len(re.findall("[\u0080-\u00ff]{3,}", text))
    return score


def fix_mojibake(text: str):
    """Try to repair double-encoded text -> (fixed_text, method | None).

    Uses ftfy when installed; otherwise attempts the classic reverse
    transcode (latin-1/cp1252 -> utf-8) and keeps the result only when it
    strictly *reduces* the mojibake score — never makes text worse.
    """
    before = mojibake_score(text)
    if before == 0:
        return text, None

    if has("ftfy"):
        ftfy = load("ftfy")
        fixed = ftfy.fix_text(text)
        if fixed != text and mojibake_score(fixed) < before:
            return fixed, "ftfy.fix_text"

    best, best_score, method = text, before, None
    for enc in ("cp1252", "latin-1"):
        try:
            cand = text.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        score = mojibake_score(cand)
        if score < best_score and "�" not in cand:
            best, best_score, method = cand, score, f"recode {enc}->utf-8"
    return best, method


def clean_text(text: str,
               *,
               fix_encoding: bool = True,
               normalize: str | None = "NFKC",
               strip_zero_width: bool = True,
               strip_control: bool = True,
               unify_newlines: bool = True,
               collapse_spaces: bool = False,
               collapse_blank_lines: bool = True) -> CleanResult:
    """Standard repair pipeline for extracted text.

    normalize:
        "NFKC" also folds full-width forms (１２３ -> 123, ： -> :) — the
        usual choice before comparison; "NFC" keeps widths; None disables.
    collapse_spaces:
        off by default because indentation can be meaningful; turn on when
        preparing text purely for diffing.
    """
    fixes: list[str] = []

    if unify_newlines and ("\r" in text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        fixes.append("unified CRLF/CR newlines to LF")

    if fix_encoding:
        text, method = fix_mojibake(text)
        if method:
            fixes.append(f"repaired mojibake via {method}")

    if strip_zero_width:
        n = len(_ZW_RE.findall(text))
        if n:
            text = _ZW_RE.sub("", text)
            fixes.append(f"removed {n} zero-width/BOM character(s)")

    if strip_control:
        n = len(_CTRL_RE.findall(text))
        if n:
            text = _CTRL_RE.sub("", text)
            fixes.append(f"removed {n} control character(s)")

    if "\xa0" in text:
        n = text.count("\xa0")
        text = text.replace("\xa0", " ")
        fixes.append(f"replaced {n} non-breaking space(s) with plain spaces")

    if normalize:
        normed = unicodedata.normalize(normalize, text)
        if normed != text:
            fixes.append(f"applied unicodedata.normalize({normalize!r}) "
                         "(unifies full/half width forms)" if normalize == "NFKC"
                         else f"applied unicodedata.normalize({normalize!r})")
            text = normed

    if collapse_spaces:
        collapsed = "\n".join(_SPACE_RUN_RE.sub(" ", ln).strip() for ln in text.split("\n"))
        if collapsed != text:
            fixes.append("collapsed runs of spaces/tabs")
            text = collapsed

    if collapse_blank_lines:
        collapsed = _MULTI_BLANK_RE.sub("\n\n", text)
        if collapsed != text:
            fixes.append("collapsed repeated blank lines")
            text = collapsed

    return CleanResult(text.strip("\n"), fixes)


def normalize_for_compare(value) -> str:
    """Aggressive normalization used only for *equality checks*, never for
    output: NFKC + zero-width strip + whitespace collapse + trim."""
    text = "" if value is None else str(value)
    text = _ZW_RE.sub("", text)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\xa0", " ")
    return _SPACE_RUN_RE.sub(" ", text).strip()


def find_invisible_chars(text: str) -> dict:
    """Diagnostic: {char_repr: count} of invisible/suspicious characters."""
    counts: dict[str, int] = {}
    for ch in text:
        if ch in ZERO_WIDTH or ch == "\xa0" or (_CTRL_RE.match(ch) and ch not in "\r\n\t"):
            key = "U+%04X %s" % (ord(ch), unicodedata.name(ch, "?"))
            counts[key] = counts.get(key, 0) + 1
    return counts
