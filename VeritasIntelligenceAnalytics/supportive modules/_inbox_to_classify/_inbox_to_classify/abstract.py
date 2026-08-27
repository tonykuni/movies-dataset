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

import collections
from typing import TYPE_CHECKING, Any, Generic, Iterable, Mapping, NamedTuple

from ..structs import CT, KT, RT, DirectedGraph

if TYPE_CHECKING:
    from ..providers import AbstractProvider
    from ..reporters import BaseReporter
    from .criterion import Criterion

    class Result(NamedTuple, Generic[RT, CT, KT]):
        mapping: Mapping[KT, CT]
        graph: DirectedGraph[KT | None]
        criteria: Mapping[KT, Criterion[RT, CT]]

else:
    Result = collections.namedtuple("Result", ["mapping", "graph", "criteria"])


class AbstractResolver(Generic[RT, CT, KT]):
    """The thing that performs the actual resolution work."""

    base_exception = Exception

    def __init__(
        self,
        provider: AbstractProvider[RT, CT, KT],
        reporter: BaseReporter[RT, CT, KT],
    ) -> None:
        self.provider = provider
        self.reporter = reporter

    def resolve(self, requirements: Iterable[RT], **kwargs: Any) -> Result[RT, CT, KT]:
        """Take a collection of constraints, spit out the resolution result.

        This returns a representation of the final resolution state, with one
        guarenteed attribute ``mapping`` that contains resolved candidates as
        values. The keys are their respective identifiers.

        :param requirements: A collection of constraints.
        :param kwargs: Additional keyword arguments that subclasses may accept.

        :raises: ``self.base_exception`` or its subclass.
        """
        raise NotImplementedError
