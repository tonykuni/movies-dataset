#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_vrn_logic_book_v0112 — 薄尾:L3_驗證 +1 節點 VIA_VRNLogic_AllInOne(R33 SDD 實測實錄)。

  為什麼要這一版:冊上 version v0112 是 vcgc/vrn-logic-add(2026-09-29 03:58)手加 AllInOne 節點後的樣子,
  建冊器還停在 v0111(48 節點)。ENG073 出 v0139 後冊上指標過期 → 守門要 `build` 重建,
  可是用 v0111 重建會把 AllInOne 丟掉(CGC_MDL244 檢查就紅)。所以建冊器本身要帶這個節點,重建才冪等。

  其餘一字未動:六層、層名、歸位、待裁定清單、冪等律都沿用 v0111(前版照讀,不複製)。
  VIA_FROM_VCGC:經 VCGC 中控跑(`via-vrnbook build|check`);不碰正本,不裝套件,不用 TA-Lib。
"""
import importlib.util
import re
import sys
from pathlib import Path

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

HERE = Path(__file__).resolve().parent
_STEM = "via_vrn_logic_book"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "via_vrn_logic_book_v0111.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("vrnbook_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


ALLINONE = {
    "family": "VIA_VRNLogic_AllInOne",
    "tail": "functional modules/VRN/VIA_VRNLogic_AllInOne_v0201.py",
    "head": "VIA VRN logic all-in-one v3.2.0 — filename, first page, financial page, sixteen checks. "
            "Added beside the existing engines.",
    "role": "單檔邏輯增補。不取代六層既有引擎,不執行 install apply,不刪舊尾版。",
    "placed_by": "v0112",
    "evidence": "attachment VIA_VRNLogic_AllInOne_v0201; stdlib; no talib",
    "role_kind": "加工",
    "role_kind_why": "把檔名、首頁、財報頁收成同一份可重跑的結果",
}


def _allinone_node() -> dict:
    """指標跟著樹上尾版走(不是寫死 v0201);樹上沒有就照原記錄(守門會報不在)。"""
    nd = dict(ALLINONE)
    t = PRIOR.tail(PRIOR.VRN, ALLINONE["family"] + "_v*.py")
    if t is not None:
        nd["tail"] = t.relative_to(PRIOR.VIA).as_posix()
    return nd


_ME = Path(__file__).stem
_ME_VER = "v" + _ME.rsplit("_v", 1)[-1]
BOOK = PRIOR.BOOK
_l3 = BOOK["layers"]["L3_驗證"]["nodes"]
if not any(n.get("family") == ALLINONE["family"] for n in _l3):
    _l3.append(_allinone_node())
# R33:ENG113 LogicRollup(R30 進樹)冊上沒有交代,前版檢 ⑧ 一直是紅。上哪一層 = 架構裁定,待操作員(LL90);先掛待裁定。
PENDING_ADD = ["VRN_ENG113_LogicRollup"]
for _f in PENDING_ADD:
    if _f not in PRIOR.OFF_BOOK_PENDING:
        PRIOR.OFF_BOOK_PENDING.append(_f)          # 同一個串列:roster_gap / 檢 ⑧ 都看得到
    if not any(x.get("family") == _f for x in BOOK.get("off_book_pending") or []):
        _p = PRIOR.probe(PRIOR.VRN, _f)
        BOOK.setdefault("off_book_pending", []).append(
            {"family": _f, "state": "PENDING_OPERATOR",
             "head": PRIOR.head1(_p or Path("/nonexistent")),
             "tail": _p.relative_to(PRIOR.VIA).as_posix() if _p else "",
             "why": "樹上活著但未列入六層;是否上架構冊=架構裁定,待操作員"})
BOOK["version"], BOOK["built_by"] = _ME_VER, _ME
_lr = BOOK.get("layer_review_b665")
if isinstance(_lr, dict) and "role_kind_tagged" in _lr:
    _lr["role_kind_tagged"] = sum(1 for lv in BOOK["layers"].values() for n in lv["nodes"] if n.get("role_kind"))
PRIOR._ME, PRIOR._ME_VER = _ME, _ME_VER
do_build, do_check = PRIOR.do_build, PRIOR.do_check


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    nodes = [n for lv in BOOK["layers"].values() for n in lv["nodes"]]
    fams = [n["family"] for n in nodes]
    chk("v0112 冊帶 AllInOne 節點(重建不會丟)", ALLINONE["family"] in fams, f"節點 {len(nodes)}")
    chk("AllInOne 只出現一次(冪等)", fams.count(ALLINONE["family"]) == 1)
    chk("冊的版本與建冊者 = 本支", BOOK["version"] == _ME_VER and BOOK["built_by"] == _ME, f"{_ME_VER} · {_ME}")
    chk("前版守門/建冊的身分跟著改(不報冊版不同步)", PRIOR._ME == _ME)
    chk("節點數 ≥ 49(CGC_MDL244 下限)", len(nodes) >= 49)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("本支帶加速器橋 · VIA_FROM_VCGC 標記", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body)
    chk("不含 TA-Lib 匯入", not re.search(r"^\s*(?:import|from)\s+talib\b", body, re.M))
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== VRN 邏輯架構索引冊 v0112 · 薄尾自測 + 前版十七檢 ===")
        return selftest()
    if a and a[0] == "build":
        return do_build()
    return do_check()


if __name__ == "__main__":
    sys.exit(main())
