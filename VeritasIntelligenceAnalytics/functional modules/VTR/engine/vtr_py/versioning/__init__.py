"""Diff & Versioning Pipeline。"""

from .patchlog import read_patchlog, write_patchlog
from .replay import replay_to

__all__ = ["read_patchlog", "write_patchlog", "replay_to"]
