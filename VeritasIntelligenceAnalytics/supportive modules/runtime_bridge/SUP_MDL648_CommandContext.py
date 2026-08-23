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
from collections.abc import Generator
from contextlib import AbstractContextManager, ExitStack, contextmanager
from typing import TypeVar

_T = TypeVar("_T", covariant=True)


class CommandContextMixIn:
    def __init__(self) -> None:
        super().__init__()
        self._in_main_context = False
        self._main_context = ExitStack()

    @contextmanager
    def main_context(self) -> Generator[None, None, None]:
        assert not self._in_main_context

        self._in_main_context = True
        try:
            with self._main_context:
                yield
        finally:
            self._in_main_context = False

    def enter_context(self, context_provider: AbstractContextManager[_T]) -> _T:
        assert self._in_main_context

        return self._main_context.enter_context(context_provider)
