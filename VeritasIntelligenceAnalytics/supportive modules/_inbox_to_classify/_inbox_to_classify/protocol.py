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
from typing import Any, cast, Set, TYPE_CHECKING
from inspect import isclass

if TYPE_CHECKING:
    from pip._vendor.rich.console import RenderableType

_GIBBERISH = """aihwerij235234ljsdnp34ksodfipwoe234234jlskjdf"""


def is_renderable(check_object: Any) -> bool:
    """Check if an object may be rendered by Rich."""
    return (
        isinstance(check_object, str)
        or hasattr(check_object, "__rich__")
        or hasattr(check_object, "__rich_console__")
    )


def rich_cast(renderable: object) -> "RenderableType":
    """Cast an object to a renderable by calling __rich__ if present.

    Args:
        renderable (object): A potentially renderable object

    Returns:
        object: The result of recursively calling __rich__.
    """
    from pip._vendor.rich.console import RenderableType

    rich_visited_set: Set[type] = set()  # Prevent potential infinite loop
    while hasattr(renderable, "__rich__") and not isclass(renderable):
        # Detect object which claim to have all the attributes
        if hasattr(renderable, _GIBBERISH):
            return repr(renderable)
        cast_method = getattr(renderable, "__rich__")
        renderable = cast_method()
        renderable_type = type(renderable)
        if renderable_type in rich_visited_set:
            break
        rich_visited_set.add(renderable_type)

    return cast(RenderableType, renderable)
