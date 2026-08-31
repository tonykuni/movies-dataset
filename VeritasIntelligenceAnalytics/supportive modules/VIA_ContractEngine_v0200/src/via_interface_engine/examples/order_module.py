"""Side-effect-controlled reference implementation of a governed module."""

from __future__ import annotations
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

import hashlib
from typing import Any, Literal

from pydantic import Field

from ..contracts import (
    ModuleContext,
    ModuleManifest,
    VIAInputModel,
    VIAModuleABC,
    VIAOutputModel,
)


# def 01 EXAMPLE PARAMETERS
DEFAULT_CURRENCY = "TWD"
SUPPORTED_CURRENCIES = ("TWD", "USD", "JPY")
TRANSACTION_PREFIX = "TXN"


# def 02 EXAMPLE INPUT AND OUTPUT CONTRACTS
class ProcessOrderInput(VIAInputModel):
    order_id: str = Field(
        ...,
        min_length=3,
        max_length=40,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="訂單的全域唯一編號",
    )
    amount: float = Field(
        ...,
        gt=0,
        le=100_000_000,
        description="訂單金額，必須大於 0",
    )
    currency: Literal["TWD", "USD", "JPY"] = Field(
        default=DEFAULT_CURRENCY,
        description="幣別",
        json_schema_extra={"ui_widget": "select"},
    )


class ProcessOrderOutput(VIAOutputModel):
    status: str = Field(pattern=r"^(SUCCESS|REJECTED)$")
    transaction_id: str
    normalized_amount: float
    currency: str


# def 03 EXAMPLE INJECTABLE COMPONENTS
class DBConnection:
    """Minimal context-managed resource used to prove automatic cleanup."""

    def __init__(self) -> None:
        self.closed = False
        self.statements: list[tuple[str, tuple[Any, ...]]] = []

    def __enter__(self) -> "DBConnection":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def execute(self, statement: str, parameters: tuple[Any, ...]) -> None:
        if self.closed:
            raise RuntimeError("DBConnection 已關閉")
        self.statements.append((statement, parameters))

    def close(self) -> None:
        self.closed = True


class CoreLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str) -> None:
        self.messages.append(message)


# def 04 EXAMPLE GOVERNED MODULE
class OrderProcessorModule(VIAModuleABC):
    __manifest__ = ModuleManifest(
        name="OrderProcessor",
        version="2.0.0",
        author="VIA",
        subsystem="VIA_DEMO",
        language="PY",
        capability="ORDER",
        description="Typed order-processing reference module",
        dependencies=(),
        permissions=("db:write:orders",),
        tags=("contract", "di", "demo"),
    )

    def __init__(self) -> None:
        self._context: ModuleContext | None = None
        self._is_ready = False

    def setup(self, context: ModuleContext) -> None:
        self._context = context
        self._is_ready = True

    def health_check(self) -> bool:
        return self._is_ready and self._context is not None

    def execute(
        self,
        input_data: ProcessOrderInput,
        db: DBConnection,
        logger: CoreLogger,
    ) -> ProcessOrderOutput:
        if not self._is_ready:
            raise RuntimeError("模組尚未 setup")
        if input_data.currency not in SUPPORTED_CURRENCIES:
            return ProcessOrderOutput(
                status="REJECTED",
                transaction_id="",
                normalized_amount=input_data.amount,
                currency=input_data.currency,
            )

        logger.info(f"開始處理訂單 {input_data.order_id}")
        transaction_id = self._make_transaction_id(input_data)
        db.execute(
            "INSERT INTO orders(order_id, amount, currency, transaction_id) VALUES (?, ?, ?, ?)",
            (
                input_data.order_id,
                input_data.amount,
                input_data.currency,
                transaction_id,
            ),
        )
        return ProcessOrderOutput(
            status="SUCCESS",
            transaction_id=transaction_id,
            normalized_amount=input_data.amount,
            currency=input_data.currency,
        )

    def teardown(self) -> None:
        self._is_ready = False
        self._context = None

    @staticmethod
    def _make_transaction_id(input_data: ProcessOrderInput) -> str:
        canonical = f"{input_data.order_id}|{input_data.amount:.6f}|{input_data.currency}"
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12].upper()
        return f"{TRANSACTION_PREFIX}-{digest}"
