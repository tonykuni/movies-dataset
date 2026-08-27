from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from collections import defaultdict
from logging import getLogger
from typing import Any

from pip._vendor.resolvelib.reporters import BaseReporter

from .base import Candidate, Requirement

logger = getLogger(__name__)


class PipReporter(BaseReporter[Requirement, Candidate, str]):
    def __init__(self) -> None:
        self.reject_count_by_package: defaultdict[str, int] = defaultdict(int)

        self._messages_at_reject_count = {
            1: (
                "pip is looking at multiple versions of {package_name} to "
                "determine which version is compatible with other "
                "requirements. This could take a while."
            ),
            8: (
                "pip is still looking at multiple versions of {package_name} to "
                "determine which version is compatible with other "
                "requirements. This could take a while."
            ),
            13: (
                "This is taking longer than usual. You might need to provide "
                "the dependency resolver with stricter constraints to reduce "
                "runtime. See https://pip.pypa.io/warnings/backtracking for "
                "guidance. If you want to abort this run, press Ctrl + C."
            ),
        }

    def rejecting_candidate(self, criterion: Any, candidate: Candidate) -> None:
        self.reject_count_by_package[candidate.name] += 1

        count = self.reject_count_by_package[candidate.name]
        if count not in self._messages_at_reject_count:
            return

        message = self._messages_at_reject_count[count]
        logger.info("INFO: %s", message.format(package_name=candidate.name))

        msg = "Will try a different candidate, due to conflict:"
        for req_info in criterion.information:
            req, parent = req_info.requirement, req_info.parent
            # Inspired by Factory.get_installation_error
            msg += "\n    "
            if parent:
                msg += f"{parent.name} {parent.version} depends on "
            else:
                msg += "The user requested "
            msg += req.format_for_error()
        logger.debug(msg)


class PipDebuggingReporter(BaseReporter[Requirement, Candidate, str]):
    """A reporter that does an info log for every event it sees."""

    def starting(self) -> None:
        logger.info("Reporter.starting()")

    def starting_round(self, index: int) -> None:
        logger.info("Reporter.starting_round(%r)", index)

    def ending_round(self, index: int, state: Any) -> None:
        logger.info("Reporter.ending_round(%r, state)", index)
        logger.debug("Reporter.ending_round(%r, %r)", index, state)

    def ending(self, state: Any) -> None:
        logger.info("Reporter.ending(%r)", state)

    def adding_requirement(
        self, requirement: Requirement, parent: Candidate | None
    ) -> None:
        logger.info("Reporter.adding_requirement(%r, %r)", requirement, parent)

    def rejecting_candidate(self, criterion: Any, candidate: Candidate) -> None:
        logger.info("Reporter.rejecting_candidate(%r, %r)", criterion, candidate)

    def pinning(self, candidate: Candidate) -> None:
        logger.info("Reporter.pinning(%r)", candidate)
