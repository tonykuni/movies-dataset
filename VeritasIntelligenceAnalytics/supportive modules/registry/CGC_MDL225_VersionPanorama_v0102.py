#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL225_VersionPanorama v0102 — 薄尾:鎖 sha 比對認得 Windows 換行(CRLF)

工作站 2026-09-28 15:51 工具探針 Ⓐ:加速器 / 網路兩列「lock sha」RED,容器同一版 GREEN。
根因:倉裡這兩支是 LF、沒標 -text,Windows 的 core.autocrlf 簽出成 CRLF → 位元組變了、sha 對不上,**內容一個字都沒變**。
本尾版只換 lock sha 那兩列的比法:

  · 原位元 sha 相符 → GREEN(同 v0101)
  · 原位元不符、但把 CRLF 換回 LF 後相符 → GREEN,碼欄照實寫「CRLF 工作複本 · 內容相符」
  · 換回 LF 仍不符 → RED(真的被改過)
不改 .gitattributes(改了會讓既有工作複本整支顯示已修改,Z231 的老問題);不改鎖冊;其餘列全照 v0101(L04 · L05)。
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
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL225_VersionPanorama"
PRIOR_PATH = [p for p in sorted(HERE.glob(_STEM + "_v*.py")) if p.name < Path(__file__).name][-1]
_spec = importlib.util.spec_from_file_location("cgc_mdl225_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

ENGINE_TAG = "CGC_MDL225_VersionPanorama_v" + Path(__file__).stem.rsplit("_v", 1)[-1]
_BASE_EXTRA = PRIOR.extra_rows


def __getattr__(name):
    return getattr(PRIOR, name)


def lock_match(path: Path, want: str) -> str:
    """回 exact / eol / mismatch / absent。eol = 只差 CRLF,內容相符。"""
    if not path.is_file():
        return "absent"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() == want:
        return "exact"
    if b"\r\n" in raw and hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == want:
        return "eol"
    return "mismatch"


def extra_rows(book: dict, lock_path: Path | None = None) -> list:
    rows = _BASE_EXTRA(book)
    lock_path = lock_path or PRIOR.LOCK
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
    for r in rows:
        if r["role"] != "lock sha":
            continue
        ent = lock.get(r["family"]) or {}
        p = PRIOR.VIA.parent / ent.get("path", "") if ent.get("path") else None
        m = lock_match(p, ent.get("sha256", "")) if p else "absent"
        if m == "eol":
            r["lamp"] = "GREEN"
            r["code"] = f"{ent.get('version', '-')} · CRLF 工作複本 · 內容相符"
            r["in_inventory"] = True
        elif m in ("mismatch", "absent"):
            r["lamp"] = "RED"
            r["code"] = f"{ent.get('version', '-')} · {'內容和鎖不同(換回 LF 也不符)' if m == 'mismatch' else '檔不在'}"
    return rows


PRIOR.extra_rows = extra_rows        # v0101 的 check() / selftest 用本尾版的比法


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    rc = PRIOR.selftest()
    print(f"=== {ENGINE_TAG} 薄尾加檢(CRLF 工作複本)===")
    with tempfile.TemporaryDirectory() as td:
        lf = b"line one\nline two\n"
        want = hashlib.sha256(lf).hexdigest()
        a, b, c = Path(td) / "a.py", Path(td) / "b.py", Path(td) / "c.py"
        a.write_bytes(lf)
        b.write_bytes(lf.replace(b"\n", b"\r\n"))
        c.write_bytes(b"line one\nline 2\n")
        chk("⑧ 原位元相符 = exact", lock_match(a, want) == "exact")
        chk("⑨ Windows CRLF 簽出(內容同)= eol → GREEN 並照實標", lock_match(b, want) == "eol")
        chk("⑩ 內容真的改了 = mismatch → RED(CRLF 不能拿來蓋掉真改動)", lock_match(c, want) == "mismatch")
        chk("⑪ 檔不在 = absent", lock_match(Path(td) / "none.py", want) == "absent")
    book = json.loads(PRIOR.BOOK.read_text(encoding="utf-8"))
    rows = [r for r in extra_rows(book) if r["role"] == "lock sha"]
    chk("⑫ 真樹兩列 lock sha 都綠", len(rows) == 2 and all(r["lamp"] == "GREEN" for r in rows), " · ".join(r["code"] for r in rows))
    ok = rc == 0 and all(results)
    print(f"  {ENGINE_TAG} 薄尾 {sum(results)}/{len(results)} · v0101 本體 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
