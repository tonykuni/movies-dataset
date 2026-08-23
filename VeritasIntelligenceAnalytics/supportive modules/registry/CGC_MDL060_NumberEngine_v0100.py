# -*- coding: utf-8 -*-
"""via_number_engine_v0100.py — VIA 自動編號引擎(編號永不變 · 只增不減 · append-only)。

功能:掃描登錄簿 components + ledger + pkg_pointers,對每個編號族(ENG/PKG/TOOL/FNT)
計算「下一可用號」;--issue 正式核發:寫入 components(類別|名稱→代號)並在 ledger
追加核發存證。已核發之號永不回收、永不改指。

用法:
  py via_number_engine_v0100.py                 → 各族下一號預覽(不寫)
  py via_number_engine_v0100.py --peek ENG      → 單族預覽
  py via_number_engine_v0100.py --issue ENG 引擎 名稱說明   → 核發並落帳
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
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = HERE / "VIA_AutoCode_Registry_v0100.json"
FAMILIES = ("ENG", "PKG", "TOOL", "FNT")


def load():
    return json.loads(REG.read_text(encoding="utf-8"))


def used_numbers(d):
    """全域掃描:components 值 + ledger code 欄 + pkg_pointers 檔名 — 一號都不漏。"""
    text = json.dumps(d, ensure_ascii=False)
    used = {f: set() for f in FAMILIES}
    for fam, num in re.findall(r"\b(ENG|PKG|TOOL|FNT)-(\d{3})\b", text):
        used[fam].add(int(num))
    for p in (HERE / "pkg_pointers").glob("PKG_*_Pointer.json"):
        m = re.match(r"PKG_(\d{3})_", p.name)
        if m:
            used["PKG"].add(int(m.group(1)))
    return used


def next_free(used, fam):
    return (max(used[fam]) + 1) if used[fam] else 1


def main(argv):
    d = load()
    used = used_numbers(d)
    if len(argv) >= 4 and argv[1] == "--issue":
        fam = argv[2].upper()
        if fam not in FAMILIES:
            print("[FAIL] 編號族僅限 %s" % "/".join(FAMILIES)); return 2
        cat = argv[3]
        name = " ".join(argv[4:]) or "(未命名)"
        n = next_free(used, fam)
        code = "%s-%03d" % (fam, n)
        key = "%s|%s" % (cat, name)
        if key in d["components"]:
            print("[FAIL] 同名件已有代號 %s — 編號永不變,不重發" % d["components"][key]); return 2
        d["components"][key] = code
        d["ledger"].append({
            "ts": datetime.now().isoformat(timespec="seconds"),
            "op": "ISSUE", "category": "編號", "component": key, "code": code,
            "note": "自動編號引擎核發:%s 族第 %d 號(掃描既用 %d 個;append-only 永不回收)。"
                    % (fam, n, len(used[fam]))})
        REG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("[OK  ] 核發 %s → %s(台帳第 %d 筆)" % (code, key, len(d["ledger"])))
        return 0
    fams = [argv[2].upper()] if (len(argv) >= 3 and argv[1] == "--peek") else FAMILIES
    print("=== VIA 自動編號引擎 v0100(預覽,不寫)===")
    for f in fams:
        print("  %s:既用 %3d 個 · 下一號 %s-%03d" % (f, len(used[f]), f, next_free(used, f)))
    print("核發:py via_number_engine_v0100.py --issue <族> <類別> <名稱>")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
