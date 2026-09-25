"""
    pygments.scanner
    ~~~~~~~~~~~~~~~~

    This library implements a regex based scanner. Some languages
    like Pascal are easy to parse but have some keywords that
    depend on the context. Because of this it's impossible to lex
    that just by using a regular expression lexer like the
    `RegexLexer`.

    Have a look at the `DelphiLexer` to get an idea of how to use
    this scanner.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
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


class EndOfText(RuntimeError):
    """
    Raise if end of text is reached and the user
    tried to call a match function.
    """


class Scanner:
    """
    Simple scanner

    All method patterns are regular expression strings (not
    compiled expressions!)
    """

    def __init__(self, text, flags=0):
        """
        :param text:    The text which should be scanned
        :param flags:   default regular expression flags
        """
        self.data = text
        self.data_length = len(text)
        self.start_pos = 0
        self.pos = 0
        self.flags = flags
        self.last = None
        self.match = None
        self._re_cache = {}

    def eos(self):
        """`True` if the scanner reached the end of text."""
        return self.pos >= self.data_length
    eos = property(eos, eos.__doc__)

    def check(self, pattern):
        """
        Apply `pattern` on the current position and return
        the match object. (Doesn't touch pos). Use this for
        lookahead.
        """
        if self.eos:
            raise EndOfText()
        if pattern not in self._re_cache:
            self._re_cache[pattern] = re.compile(pattern, self.flags)
        return self._re_cache[pattern].match(self.data, self.pos)

    def test(self, pattern):
        """Apply a pattern on the current position and check
        if it patches. Doesn't touch pos.
        """
        return self.check(pattern) is not None

    def scan(self, pattern):
        """
        Scan the text for the given pattern and update pos/match
        and related fields. The return value is a boolean that
        indicates if the pattern matched. The matched value is
        stored on the instance as ``match``, the last value is
        stored as ``last``. ``start_pos`` is the position of the
        pointer before the pattern was matched, ``pos`` is the
        end position.
        """
        if self.eos:
            raise EndOfText()
        if pattern not in self._re_cache:
            self._re_cache[pattern] = re.compile(pattern, self.flags)
        self.last = self.match
        m = self._re_cache[pattern].match(self.data, self.pos)
        if m is None:
            return False
        self.start_pos = m.start()
        self.pos = m.end()
        self.match = m.group()
        return True

    def get_char(self):
        """Scan exactly one char."""
        self.scan('.')

    def __repr__(self):
        return '<%s %d/%d>' % (
            self.__class__.__name__,
            self.pos,
            self.data_length
        )
