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
from abc import ABC


class RichRenderable(ABC):
    """An abstract base class for Rich renderables.

    Note that there is no need to extend this class, the intended use is to check if an
    object supports the Rich renderable protocol. For example::

        if isinstance(my_object, RichRenderable):
            console.print(my_object)

    """

    @classmethod
    def __subclasshook__(cls, other: type) -> bool:
        """Check if this class supports the rich render protocol."""
        return hasattr(other, "__rich_console__") or hasattr(other, "__rich__")


if __name__ == "__main__":  # pragma: no cover
    from pip._vendor.rich.text import Text

    t = Text()
    print(isinstance(Text, RichRenderable))
    print(isinstance(t, RichRenderable))

    class Foo:
        pass

    f = Foo()
    print(isinstance(f, RichRenderable))
    print(isinstance("", RichRenderable))
