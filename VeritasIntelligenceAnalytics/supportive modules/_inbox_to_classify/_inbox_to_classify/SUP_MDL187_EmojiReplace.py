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
from typing import Callable, Match, Optional
import re

from ._emoji_codes import EMOJI


_ReStringMatch = Match[str]  # regex match object
_ReSubCallable = Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EmojiSubMethod = Callable[[_ReSubCallable, str], str]  # Sub method of a compiled re


def _emoji_replace(
    text: str,
    default_variant: Optional[str] = None,
    _emoji_sub: _EmojiSubMethod = re.compile(r"(:(\S*?)(?:(?:\-)(emoji|text))?:)").sub,
) -> str:
    """Replace emoji code in text."""
    get_emoji = EMOJI.__getitem__
    variants = {"text": "\uFE0E", "emoji": "\uFE0F"}
    get_variant = variants.get
    default_variant_code = variants.get(default_variant, "") if default_variant else ""

    def do_replace(match: Match[str]) -> str:
        emoji_code, emoji_name, variant = match.groups()
        try:
            return get_emoji(emoji_name.lower()) + get_variant(
                variant, default_variant_code
            )
        except KeyError:
            return emoji_code

    return _emoji_sub(do_replace, text)
