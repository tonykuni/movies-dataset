from __future__ import annotations

import json
from pathlib import Path

from quant_engine.governance import ssot_manifest

root = Path(__file__).resolve().parents[1]
out = root / "ssot" / "quant_engine_ssot.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(
    json.dumps(ssot_manifest(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(out)
