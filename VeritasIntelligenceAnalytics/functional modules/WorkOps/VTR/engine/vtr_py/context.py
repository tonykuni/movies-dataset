"""執行期設定與 Context。

Context 是 Stage 唯一能取得外部狀態的管道（設定、詞庫、量測、時鐘）。
Stage 不得讀取全域變數或直接呼叫 datetime.now() —— 時鐘注入是為了讓
replay 與測試可重現。
"""

from __future__ import annotations

import copy
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from .gate import ConfidenceGate

ENGINE_ID = "vtr-py/1.0.0"

DEFAULT_CONFIG: dict[str, Any] = {
    "engine": ENGINE_ID,
    "gate": {
        "auto_threshold": 0.85,
        "review_threshold": 0.60,
        "llm_only_ceiling": 0.80,
    },
    "normalize": {
        "opencc": "s2twp",
        "filler_policy": "mark",          # mark | remove | keep
        "filler_confidence": 0.70,        # 落在 review 頻帶
    },
    "lang_detect": {
        "min_run_cjk": 2,
        "min_run_latin": 3,
        "mixed_threshold": 0.7,
    },
    "protect": {
        "enabled_kinds": [
            "url", "email", "timestamp",
            "part_number", "code_ident", "number_unit",
        ],
    },
    "pipeline": {
        # True = 不變式違反直接拋錯（CI 用）；False = 回退該 Stage 並記錄（生產用）
        "strict": False,
    },
}


def default_config() -> dict[str, Any]:
    """預設設定的**深拷貝**。

    刻意不回傳 DEFAULT_CONFIG 本身、也不用 dict() 淺拷貝：巢狀 dict 會被共用，
    任何一處寫入都會污染全域預設值。這個 bug 在測試裡表現為「前一個測試把
    strict 打開，後面所有測試跟著變 strict」—— 極難從症狀反推原因。
    """
    return copy.deepcopy(DEFAULT_CONFIG)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


@dataclass(frozen=True)
class Config:
    data: dict[str, Any] = field(default_factory=default_config)

    def get(self, path: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    @property
    def gate(self) -> ConfidenceGate:
        g = self.data.get("gate", {})
        return ConfidenceGate(
            auto_threshold=g.get("auto_threshold", 0.85),
            review_threshold=g.get("review_threshold", 0.60),
            llm_only_ceiling=g.get("llm_only_ceiling", 0.80),
        )

    @staticmethod
    def load(path: Optional[Path] = None) -> "Config":
        """讀取設定檔。

        JSON 一律支援；YAML 僅在環境有 PyYAML 時支援。確定性層必須零相依，
        因此預設設定檔是 `config/vtr.json`。
        """
        if path is None:
            return Config()
        text = Path(path).read_text(encoding="utf-8")
        if str(path).endswith((".yaml", ".yml")):
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover - 環境相依
                raise RuntimeError(
                    f"讀取 {path} 需要 PyYAML；改用 JSON 設定檔或安裝 pyyaml"
                ) from exc
            override = yaml.safe_load(text) or {}
        else:
            override = json.loads(text)
        return Config(_deep_merge(default_config(), override))


class Metrics:
    """Stage 量測收集器。每個 Stage 拿到一個乾淨的實例。"""

    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()
        self._values: dict[str, Any] = {}

    def bump(self, key: str, by: int = 1) -> None:
        self._counter[key] += by

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def as_dict(self) -> dict[str, Any]:
        return {**dict(self._counter), **self._values}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z")


@dataclass
class Context:
    config: Config = field(default_factory=Config)
    engine: str = ENGINE_ID
    #: 注入時鐘，讓 replay 與測試可重現。
    clock: Callable[[], str] = _utc_now
    #: 由 pipeline 在每個 Stage 前重設。
    metrics: Metrics = field(default_factory=Metrics)
    #: 目前 revision 編號，供決定性 patch_id 使用。
    rev: int = 0
    #: 目前 Stage 名稱，供 Stage 內部產生 patch_id 與檢查。
    stage: str = ""
    #: SSOT Lexicon 快照（步驟 7 接上後填入；步驟 1–2 不需要）。
    lexicon: Any = None

    @property
    def gate(self) -> ConfidenceGate:
        return self.config.gate

    def new_patch_id(self, index: int) -> str:
        """決定性 patch_id：rev + 序號。

        刻意不用 uuid / 時間戳 —— replay 必須能重建完全相同的 patch log，
        隨機 id 會讓「同一份輸入是否產生同一份輸出」變成無法驗證的問題。
        """
        return f"p{self.rev:03d}-{index:04d}"
