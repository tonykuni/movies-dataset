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
from types import TracebackType
from typing import IO, Iterable, Iterator, List, Optional, Type


class NullFile(IO[str]):
    def close(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    def read(self, __n: int = 1) -> str:
        return ""

    def readable(self) -> bool:
        return False

    def readline(self, __limit: int = 1) -> str:
        return ""

    def readlines(self, __hint: int = 1) -> List[str]:
        return []

    def seek(self, __offset: int, __whence: int = 1) -> int:
        return 0

    def seekable(self) -> bool:
        return False

    def tell(self) -> int:
        return 0

    def truncate(self, __size: Optional[int] = 1) -> int:
        return 0

    def writable(self) -> bool:
        return False

    def writelines(self, __lines: Iterable[str]) -> None:
        pass

    def __next__(self) -> str:
        return ""

    def __iter__(self) -> Iterator[str]:
        return iter([""])

    def __enter__(self) -> IO[str]:
        return self

    def __exit__(
        self,
        __t: Optional[Type[BaseException]],
        __value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> None:
        pass

    def write(self, text: str) -> int:
        return 0

    def flush(self) -> None:
        pass

    def fileno(self) -> int:
        return -1


NULL_FILE = NullFile()
