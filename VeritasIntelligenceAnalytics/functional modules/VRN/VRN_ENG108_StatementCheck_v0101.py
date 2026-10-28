#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read one statement table and check it. Basic EPS and diluted EPS stay apart.

An unlabeled EPS is not assigned to either. No outside history, no invented base.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
import re

_KEYS = (
    ("diluted_eps", ("稀釋每股盈餘", "稀釋eps", "diluted eps", "diluted earnings per share")),
    ("basic_eps", ("基本每股盈餘", "基本eps", "basic eps", "basic earnings per share")),
    ("gross", ("營業毛利", "毛利", "gross profit")),
    ("cost", ("營業成本", "cost of revenue", "cost of sales")),
    ("revenue", ("營業收入", "收益合計", "net revenue", "total revenue", "revenue")),
    ("net", ("本期淨利", "稅後淨利", "net income", "net profit")),
    ("margin", ("毛利率", "gross margin")),
    ("eps", ("每股盈餘", "eps")),
)
_PAGE = ("基本每股盈餘", "稀釋每股盈餘", "合併綜合損益", "basic eps", "diluted eps", "gross profit", "income statement")
_NUM = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?%?")


def _kind(label: str) -> str | None:
    low = label.lower().replace(" ", "")
    raw = label.lower()
    for kind, names in _KEYS:
        for name in names:
            if name.replace(" ", "") in low or name in raw:
                if kind == "eps" and ("basic" in raw or "diluted" in raw or "基本" in label or "稀釋" in label):
                    continue
                if kind == "revenue" and "cost" in raw:
                    continue
                return kind
    return None


def _num(cell: str) -> float | None:
    text = str(cell or "").strip().replace(",", "").replace("，", "")
    if not text or text in {"-", "—", "–", "n.a.", "na"}:
        return None
    match = _NUM.search(text)
    if match is None:
        return None
    token = match.group(0).replace("%", "")
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        value = float(token)
    except ValueError:
        return None
    return -value if negative else value


def _last_number(line: str) -> float | None:
    found = [_num(token) for token in _NUM.findall(line)]
    found = [item for item in found if item is not None]
    return found[-1] if found else None


def from_text(text: str) -> dict:
    got: dict[str, float] = {}
    for line in (text or "").splitlines():
        kind = _kind(line)
        if kind is None or kind in got:
            continue
        value = _last_number(line)
        if value is not None:
            got[kind] = value
    revenue, cost, gross = got.get("revenue"), got.get("cost"), got.get("gross")
    if None not in (revenue, cost, gross):
        add = "OK" if abs((revenue - cost) - gross) <= 0.02 * max(abs(revenue), 1.0) else "FAIL"
    else:
        add = "SKIP"
    margin = got.get("margin")
    if None not in (revenue, gross) and revenue and margin is not None:
        ratio = gross / revenue
        reported = margin / 100.0 if abs(margin) > 1.5 else margin
        div = "OK" if abs(ratio - reported) <= 0.02 else "FAIL"
    else:
        div = "SKIP"
    unlabeled = got.get("eps")
    return {
        "basic_eps": got.get("basic_eps"),
        "diluted_eps": got.get("diluted_eps"),
        "unlabeled_eps": unlabeled if "basic_eps" not in got and "diluted_eps" not in got else None,
        "add": add,
        "div": div,
        "hist": "NO_BASE",
    }


def inspect(path) -> dict:
    try:
        import fitz
    except Exception:
        return {"state": "ABSENT", "hist": "NO_BASE"}
    try:
        with fitz.open(str(path)) as doc:
            for index, page in enumerate(doc):
                if index == 0 or index > 12:
                    continue
                text = page.get_text("text") or ""
                low = text.lower()
                if not any(key in low or key in text for key in _PAGE):
                    continue
                card = from_text(text)
                card.update({"state": "SEEN", "page": index + 1})
                return card
    except Exception as exc:
        return {"state": f"FAIL {type(exc).__name__}", "hist": "NO_BASE"}
    return {"state": "NODATA", "add": "SKIP", "div": "SKIP", "hist": "NO_BASE",
            "basic_eps": None, "diluted_eps": None, "unlabeled_eps": None}


def selftest() -> int:
    good = from_text("\n".join([
        "Revenue 80 100",
        "Cost of revenue 30 40",
        "Gross profit 50 60",
        "Gross margin 62.5% 60%",
        "Basic EPS 8 10",
        "Diluted EPS 7 9",
    ]))
    bare = from_text("EPS 5.2")
    bad = from_text("Revenue 100\nCost of sales 40\nGross profit 50")
    ok = (
        good["add"] == "OK" and good["div"] == "OK"
        and good["basic_eps"] == 10 and good["diluted_eps"] == 9
        and good["unlabeled_eps"] is None
        and bare["unlabeled_eps"] == 5.2 and bare["basic_eps"] is None
        and bad["add"] == "FAIL"
    )
    print("  [OK]" if ok else f"  [FAIL] {good} {bare} {bad}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
