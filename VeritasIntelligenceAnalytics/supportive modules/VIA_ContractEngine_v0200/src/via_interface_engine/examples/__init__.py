"""Governed example modules for VIA Contract Interface Engine."""

from .order_module import (
    CoreLogger,
    DBConnection,
    OrderProcessorModule,
    ProcessOrderInput,
    ProcessOrderOutput,
)

__all__ = [
    "CoreLogger",
    "DBConnection",
    "OrderProcessorModule",
    "ProcessOrderInput",
    "ProcessOrderOutput",
]

