#!/usr/bin/env python3
"""VIA_UploadsWorkbench v0101 — v0100 薄尾:加 3 份交接收據釘選檔的雜湊核對(v0100 一字不改)。

操作員 2026-11-10:「你覺得必要的用 ps 加加速器抓取」。交接文件《VIA VCGC · AI handover · v0106.4》
「Current connection observation」段釘了三個檔的 SHA-256;下載夾裡有同名檔,就逐一對:相同 = GREEN、
不同 = RED(本機那份不是收據看到的那份),沒有 = YELLOW。其餘全部沿用 v0100(prior)。
搭配 Invoke-VIA-UploadsWorkbench-v0100.ps1(VIA 根)從下載夾挑檔 → 暫存 → 經加速器跑本支。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

VERSION = "v0101"
HERE = Path(__file__).resolve().parent
PRIOR_FILE = HERE / "VIA_UploadsWorkbench_v0100.py"

_spec = importlib.util.spec_from_file_location("via_uploads_workbench_v0100", PRIOR_FILE)
prior = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prior)  # type: ignore[union-attr]

PINNED = {  # 來源:上傳的交接文件 v0106.4 · receipt hashes observed in pinned attachments
    "VIA_MatrixGovernance_AllInOne_v0100.py": "bb8d5911a0e15765b9a4e0ad9d01a6104a78a044878db71b509b326f1f80b7b0",
    "VIA_MatrixGovernance_QA_v0100.html": "5d6ff4c59ca2dea122f86839e396d6abca22cfdb9ce8c63c126faf8ba7e7ac8b",
    "VIA_MatrixGovernance_README_v0100.md": "f1d25131e9b11718e1a453f054c272baf27e37c9cb71894a2089b97e6e2b6338",
}

# 只擴充清單,不改 v0100 的判定邏輯
prior.VERSION = VERSION
prior.ENGINE = f"VIA_UploadsWorkbench_{VERSION}"
prior.EXPECTED = list(prior.EXPECTED) + [n for n in PINNED if n not in prior.EXPECTED]
prior._EXP_KEYS = {prior.key(n): n for n in prior.EXPECTED}
assert len(prior._EXP_KEYS) == len(prior.EXPECTED), "EXPECTED 正規化後撞名"

_inventory_prior = prior.inventory
_render_hub_prior = prior.render_hub


def inventory(src: Path) -> dict:
    inv = _inventory_prior(src)
    for i in inv["items"]:
        want = PINNED.get(i["canonical"])
        if not want or not i["copies"]:
            continue
        ok = i["distinct_sha256"] == [want]
        tag = "= 交接收據釘選值" if ok else f"≠ 交接收據釘選值 {want[:12]}…(本機這份不是收據看到的那份)"
        i["note"] = " ｜ ".join(x for x in (i.get("note", ""), tag) if x)
        if not ok:
            i["status"] = "RED"
    return inv


def render_hub(*a, **kw) -> str:
    page = _render_hub_prior(*a, **kw)
    return page.replace("一 · 上傳清單(22 個路徑 → 17 份正本)",
                        f"一 · 上傳清單({len(prior.EXPECTED)} 份正本 · 含 {len(PINNED)} 份交接收據釘選檔)")


prior.inventory = inventory
prior.render_hub = render_hub


def __getattr__(name: str):
    return getattr(prior, name)


def selftest() -> int:
    saved = prior._EXP_KEYS                     # 前版自測數 17 份正本要原樣 → 先換回前版清單,跑完再掛回
    prior._EXP_KEYS = {prior.key(n): n for n in prior.EXPECTED if n not in PINNED}
    try:
        rc = prior.selftest()
    finally:
        prior._EXP_KEYS = saved
    extra = {n: prior.canonical(n) == n for n in PINNED}
    extra["copy"] = prior.canonical("VIA_MatrixGovernance_README_v0100 (1).md") == "VIA_MatrixGovernance_README_v0100.md"
    ok = rc == 0 and all(extra.values()) and len(prior.EXPECTED) == 20
    print({"engine": prior.ENGINE, "selftest_v0101": "PASS" if ok else "FAIL", "checks": extra})
    return 0 if ok else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return prior.main(argv)


if __name__ == "__main__":
    sys.exit(main())
