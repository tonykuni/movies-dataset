# -*- coding: utf-8 -*-
"""via_ssot_evolve_v0100.py — SSOT 自動演化引擎 v0100(凍結件零觸碰 · 提案版遞增 · AI 只整理不發明)。

原理:SSOT 正本(VIA_SSOT_Unified.py 等)受凍結鎖保護,永不就地改。演化 = 從「真實輸入資料」
掃出 SSOT 尚未收錄的候選代號,寫成版本遞增的提案檔(evolution/SSOT_Evolution_Proposals_vNNN.json),
附完整出處舉證(檔案/欄位/出現次數)。提案≠正典 — 經操作員核可後才由後續波納編。

代號鎖定:TW_TICKER_REGEX = (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})(SSOT 鎖定式,本引擎唯讀引用)。

用法:
  py via_ssot_evolve_v0100.py <輸入.csv|.json> [--col 欄名] [--dry]
"""
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
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVO = HERE / "ssot_evolution"
TW_TICKER_REGEX = re.compile(r"^(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})[A-Z]?$")


def known_codes():
    """已知碼域:VRN_MDL010 CodeRegistry(在庫正本)+ 既有提案檔 — 唯讀。"""
    known = set()
    cr = HERE.parent.parent / "functional modules" / "VRN" / "VRN_MDL010_CodeRegistry.py"
    if cr.exists():
        for m in re.finditer(r'"((?!0)[1-9]\d{3}[A-Z]?)"', cr.read_text(encoding="utf-8", errors="ignore")):
            known.add(m.group(1))
    for p in sorted(EVO.glob("SSOT_Evolution_Proposals_v*.json")):
        try:
            for row in json.loads(p.read_text(encoding="utf-8")).get("proposals", []):
                known.add(row["code"])
        except Exception:
            pass
    return known


def harvest(path, col=None):
    """從真實輸入檔萃取候選碼(附出處計數)— 不發明任何值。"""
    hits = {}
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                cells = ([row.get(col, "")] if col else list(row.values()))
                for v in cells:
                    v = str(v).strip()
                    if TW_TICKER_REGEX.match(v):
                        hits[v] = hits.get(v, 0) + 1
    else:
        text = json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False)
        for m in re.finditer(r'"((?!0)[1-9]\d{3}[A-Z]?)"', text):
            if TW_TICKER_REGEX.match(m.group(1)):
                hits[m.group(1)] = hits.get(m.group(1), 0) + 1
    return hits


def next_version():
    vs = [int(m.group(1)) for p in EVO.glob("SSOT_Evolution_Proposals_v*.json")
          if (m := re.search(r"_v(\d+)\.json$", p.name))]
    return (max(vs) + 1) if vs else 100


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    src = Path(argv[1])
    if not src.exists():
        print("[FAIL] 輸入不在位:%s" % src); return 2
    col = argv[argv.index("--col") + 1] if "--col" in argv else None
    dry = "--dry" in argv
    known = known_codes()
    hits = harvest(src, col)
    fresh = {c: n for c, n in hits.items() if c not in known}
    print("=== SSOT 演化引擎 v0100 ===")
    print("  輸入:%s · 命中碼 %d 種 · 已知 %d · 新候選 %d"
          % (src.name, len(hits), len(hits) - len(fresh), len(fresh)))
    if not fresh:
        print("[OK  ] 無新候選 — SSOT 覆蓋完整(誠實零提案,不造件)"); return 0
    if dry:
        for c in sorted(fresh):
            print("  [PLAN] %s ×%d" % (c, fresh[c]))
        return 0
    EVO.mkdir(exist_ok=True)
    v = next_version()
    out = EVO / ("SSOT_Evolution_Proposals_v%03d.json" % v)
    out.write_text(json.dumps({
        "version": v, "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_file": str(src), "source_column": col,
        "policy": ["frozen SSOT untouched", "proposals are NOT canon until operator approval",
                   "no_fake_fill: every code has real provenance below"],
        "proposals": [{"code": c, "occurrences": fresh[c], "provenance": src.name}
                      for c in sorted(fresh)],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[OK  ] 提案檔 %s(%d 候選;凍結正本零觸碰)" % (out.name, len(fresh)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
