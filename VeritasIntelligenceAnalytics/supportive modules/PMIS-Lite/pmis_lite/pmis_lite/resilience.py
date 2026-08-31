"""備援鏈（內建多元備援，降低失敗率）。

設計原則：每個關鍵能力都不押注單一作法，而是排一串「策略」依序嘗試，
第一個成功的就用，全失敗才回報——並記錄走到第幾條、為什麼前面的失敗。

這把「失敗率」從「單一函式庫掛掉就整個失敗」降成「全部備援都掛才失敗」。
例：讀 MS Project = [另存XML] → [COM 自動化] → [mpxj] ；讀郵件 = [Outlook COM] → [libpff讀OST/PST] → [IMAP]。
"""
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

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Strategy:
    name: str
    fn: Callable[[], Any]
    available: Callable[[], bool] | None = None   # 可選的前置可用性檢查


@dataclass
class ChainResult:
    ok: bool
    value: Any = None
    used: str = ""
    attempts: list = field(default_factory=list)   # [(name, status, detail)]

    def report(self) -> str:
        lines = [f"備援鏈結果：{'成功' if self.ok else '全部失敗'}"
                 + (f"（採用：{self.used}）" if self.ok else "")]
        for name, status, detail in self.attempts:
            lines.append(f"  - {name}: {status}{('　' + detail) if detail else ''}")
        return "\n".join(lines)


def run_chain(strategies: list[Strategy], validate: Callable[[Any], bool] | None = None) -> ChainResult:
    """依序嘗試策略；第一個產出有效結果者勝出。"""
    res = ChainResult(ok=False)
    for s in strategies:
        if s.available is not None:
            try:
                if not s.available():
                    res.attempts.append((s.name, "skip", "前置不可用"))
                    continue
            except Exception as e:
                res.attempts.append((s.name, "skip", f"檢查失敗:{e.__class__.__name__}"))
                continue
        try:
            value = s.fn()
            if value is None or (validate and not validate(value)):
                res.attempts.append((s.name, "empty", "無有效結果"))
                continue
            res.ok, res.value, res.used = True, value, s.name
            res.attempts.append((s.name, "ok", ""))
            return res
        except Exception as e:
            res.attempts.append((s.name, "fail", f"{e.__class__.__name__}:{e}"))
            continue
    return res
