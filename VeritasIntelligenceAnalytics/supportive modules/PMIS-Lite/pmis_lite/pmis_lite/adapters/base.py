"""Adapter 介面（協定）。

每個來源 adapter 只需做一件事：把自己的來源轉成一串統一的 SSOT Record。
核心引擎只依賴這個介面，不管資料原本長怎樣 —— 這就是「萬用」的根。

未來新增來源（Outlook / Gmail / MS Project）只要實作 read() 回傳 Record 串即可，
核心引擎一行都不用改。
"""
from __future__ import annotations

from typing import Iterable, Protocol

from ..schema import Record


class SourceAdapter(Protocol):
    source_type: str

    def read(self) -> Iterable[Record]:
        """讀取來源，產出統一格式的 Record。"""
        ...
