"""
    pygments.regexopt
    ~~~~~~~~~~~~~~~~~

    An algorithm that generates optimized regexes for matching long lists of
    literal strings.

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
from re import escape
from os.path import commonprefix
from itertools import groupby
from operator import itemgetter

CS_ESCAPE = re.compile(r'[\[\^\\\-\]]')
FIRST_ELEMENT = itemgetter(0)


def make_charset(letters):
    return '[' + CS_ESCAPE.sub(lambda m: '\\' + m.group(), ''.join(letters)) + ']'


def regex_opt_inner(strings, open_paren):
    """Return a regex that matches any string in the sorted list of strings."""
    close_paren = open_paren and ')' or ''
    # print strings, repr(open_paren)
    if not strings:
        # print '-> nothing left'
        return ''
    first = strings[0]
    if len(strings) == 1:
        # print '-> only 1 string'
        return open_paren + escape(first) + close_paren
    if not first:
        # print '-> first string empty'
        return open_paren + regex_opt_inner(strings[1:], '(?:') \
            + '?' + close_paren
    if len(first) == 1:
        # multiple one-char strings? make a charset
        oneletter = []
        rest = []
        for s in strings:
            if len(s) == 1:
                oneletter.append(s)
            else:
                rest.append(s)
        if len(oneletter) > 1:  # do we have more than one oneletter string?
            if rest:
                # print '-> 1-character + rest'
                return open_paren + regex_opt_inner(rest, '') + '|' \
                    + make_charset(oneletter) + close_paren
            # print '-> only 1-character'
            return open_paren + make_charset(oneletter) + close_paren
    prefix = commonprefix(strings)
    if prefix:
        plen = len(prefix)
        # we have a prefix for all strings
        # print '-> prefix:', prefix
        return open_paren + escape(prefix) \
            + regex_opt_inner([s[plen:] for s in strings], '(?:') \
            + close_paren
    # is there a suffix?
    strings_rev = [s[::-1] for s in strings]
    suffix = commonprefix(strings_rev)
    if suffix:
        slen = len(suffix)
        # print '-> suffix:', suffix[::-1]
        return open_paren \
            + regex_opt_inner(sorted(s[:-slen] for s in strings), '(?:') \
            + escape(suffix[::-1]) + close_paren
    # recurse on common 1-string prefixes
    # print '-> last resort'
    return open_paren + \
        '|'.join(regex_opt_inner(list(group[1]), '')
                 for group in groupby(strings, lambda s: s[0] == first[0])) \
        + close_paren


def regex_opt(strings, prefix='', suffix=''):
    """Return a compiled regex that matches any string in the given list.

    The strings to match must be literal strings, not regexes.  They will be
    regex-escaped.

    *prefix* and *suffix* are pre- and appended to the final regex.
    """
    strings = sorted(strings)
    return prefix + regex_opt_inner(strings, '(') + suffix
