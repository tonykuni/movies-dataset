# [VIA:ACCEL-BRIDGE] 隔離測試用輸出契約
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    input_file, output = Path(sys.argv[1]), Path(sys.argv[2])
    data = json.loads(input_file.read_text(encoding="utf-8"))
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {"schema": data["schema"], "rows": 1, "version": data["version"],
              "repaired": data.get("ready") is True}
    output.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
