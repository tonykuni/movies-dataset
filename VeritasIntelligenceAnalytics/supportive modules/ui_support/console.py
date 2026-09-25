"""
    pygments.console
    ~~~~~~~~~~~~~~~~

    Format colored console output.

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

esc = "\x1b["

codes = {}
codes[""] = ""
codes["reset"] = esc + "39;49;00m"

codes["bold"] = esc + "01m"
codes["faint"] = esc + "02m"
codes["standout"] = esc + "03m"
codes["underline"] = esc + "04m"
codes["blink"] = esc + "05m"
codes["overline"] = esc + "06m"

dark_colors = ["black", "red", "green", "yellow", "blue",
               "magenta", "cyan", "gray"]
light_colors = ["brightblack", "brightred", "brightgreen", "brightyellow", "brightblue",
                "brightmagenta", "brightcyan", "white"]

x = 30
for dark, light in zip(dark_colors, light_colors):
    codes[dark] = esc + "%im" % x
    codes[light] = esc + "%im" % (60 + x)
    x += 1

del dark, light, x

codes["white"] = codes["bold"]


def reset_color():
    return codes["reset"]


def colorize(color_key, text):
    return codes[color_key] + text + codes["reset"]


def ansiformat(attr, text):
    """
    Format ``text`` with a color and/or some attributes::

        color       normal color
        *color*     bold color
        _color_     underlined color
        +color+     blinking color
    """
    result = []
    if attr[:1] == attr[-1:] == '+':
        result.append(codes['blink'])
        attr = attr[1:-1]
    if attr[:1] == attr[-1:] == '*':
        result.append(codes['bold'])
        attr = attr[1:-1]
    if attr[:1] == attr[-1:] == '_':
        result.append(codes['underline'])
        attr = attr[1:-1]
    result.append(codes[attr])
    result.append(text)
    result.append(codes['reset'])
    return ''.join(result)
