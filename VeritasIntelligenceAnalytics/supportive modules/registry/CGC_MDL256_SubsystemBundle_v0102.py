#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL256_SubsystemBundle v0102 — 薄尾:包冊上已退役搬走的檔(有退役清冊證明)改列 retired,不算缺

實錄(2026-11-28,交接閘 VCGC 紅列 bundle_tool · bundle_tool_v0101):v0100 自測 ② build 第一包 via_01_vdf「936 檔缺 161」。
這 161 支全部在 functional modules/VIA_RetiredEngines/prune_*/RETIRE_MANIFEST.json 的 moved 裡(操作員核准的以搬代刪),
清冊寫的新路徑上有檔、內容雜湊相符。包冊照只增律保留舊列(不刪列);v0100 不認清冊 → 永遠紅。
本版(v0101 以前一字不動;冊 · build · verify · preflight · list 照前版):
  掛在定義那一層(v0100 的 manifest):冊上缺的檔若有退役證明(清冊 + 新路徑有檔 + sha256 原樣或 CRLF→LF 後相符,
  同 CGC_MDL140 v0112 retired_proof 的判法)→ 移到 man["retired"](照列 · 帶新路徑與批名),不打進包;沒證明的照舊算缺(紅)。
  操作員 2026-11-28「前版鏈比照裁定甲」:本版自測驗本版與直接前版 v0101(v0101 在行程內帶 v0100)。
不連網;不改被打包的檔;不碰 TA-Lib;不代設同意閘。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL256_SubsystemBundle"
ENGINE = Path(__file__).stem
RETIRE_GLOB = "functional modules/VIA_RetiredEngines/prune_*/RETIRE_MANIFEST.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                         # v0100:manifest · build · VIA 住在這一層
_MANIFEST_V0100 = BASE.manifest


def __getattr__(name):
    return getattr(PRIOR, name)


def load_manifests(via: Path | None = None) -> dict:
    """{原路徑: [(新路徑, sha256, 批名), …]};讀不到 / 形狀不對的那一本略過(它管的檔照舊算缺)。"""
    out: dict = {}
    for p in sorted(Path(via or BASE.VIA).glob(RETIRE_GLOB)):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        moved = j.get("moved") if isinstance(j, dict) else None
        for x in moved if isinstance(moved, list) else []:
            if isinstance(x, dict) and all(isinstance(x.get(k), str) and x.get(k) for k in ("from", "to", "sha256")):
                out.setdefault(x["from"], []).append((x["to"], x["sha256"].lower(), str(j.get("batch") or p.parent.name)))
    return out


def _hashes(p: Path) -> tuple:
    raw = p.read_bytes()
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def retired_proof(via: Path, rel: str, manifests: dict):
    root = Path(via).resolve()
    for to, want, batch in manifests.get(rel, []):
        q = (root / to).resolve()
        if root in q.parents and q.is_file() and want in _hashes(q):
            return {"file": rel, "to": to, "batch": batch}
    return None


def manifest(name: str, spec: dict, idx: dict | None = None) -> dict:
    man = _MANIFEST_V0100(name, spec, idx)
    mans = load_manifests(BASE.VIA)
    keep, retired = [], []
    for rel in man.get("missing") or []:
        proof = retired_proof(BASE.VIA, rel, mans)
        (retired.append(proof) if proof else keep.append(rel))
    man["missing"], man["retired"] = keep, retired
    return man


BASE.manifest = manifest                   # v0100 build 讀模組層 manifest


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return PRIOR.main(args)


def selftest() -> int:
    rc0 = PRIOR.selftest()                  # 直接前版 v0101(行程內帶 v0100 · 已用本版 manifest)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(退役清冊證明 → retired)===")
    chk("① 直接前版 v0101 自測照過(build 第一包:缺 0 · 退役照列)", rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        via = Path(td)
        (via / "new").mkdir()
        (via / "new" / "a.py").write_bytes(b"x = 1\r\n")
        (via / "new" / "b.py").write_bytes(b"y = 2\n")
        lf = hashlib.sha256(b"x = 1\n").hexdigest()
        md = via / "functional modules" / "VIA_RetiredEngines" / "prune_t"
        md.mkdir(parents=True)
        (md / "RETIRE_MANIFEST.json").write_text(json.dumps({"batch": "t", "moved": [
            {"from": "old/a.py", "to": "new/a.py", "sha256": lf},
            {"from": "old/b.py", "to": "new/b.py", "sha256": "0" * 64},
            {"from": "old/c.py", "to": "../outside.py", "sha256": lf}]}), encoding="utf-8")
        mans = load_manifests(via)
        a, b, c, d = (retired_proof(via, r, mans) for r in ("old/a.py", "old/b.py", "old/c.py", "old/d.py"))
        chk("② 清冊 + 新路徑有檔 + 雜湊(CRLF→LF 後)相符 → 退役證明;雜湊不合 / 路徑出 VIA 根 / 不在清冊 → 沒證明(照算缺)",
            a == {"file": "old/a.py", "to": "new/a.py", "batch": "t"} and b is None and c is None and d is None)
    book = PRIOR.load_book()
    name = next(iter(book["bundles"]))
    man = manifest(name, book["bundles"][name], {})
    chk("③ 真樹第一包:缺 0;退役照列不消失(帶新路徑)", not man["missing"] and all(r.get("to") for r in man["retired"]),
        f"{name} · 檔 {man['count'] if 'count' in man else len(man.get('files', []))} · 缺 {len(man['missing'])} · 退役 {len(man['retired'])}")
    chk("④ v0100 build 讀到本版 manifest(掛在定義那一層)", BASE.manifest is manifest)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在且執行時載到 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and VIA_ACCEL is not None
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {ENGINE} 本版 {sum(ok)}/{len(ok)} · v0101 {'PASS' if rc0 == 0 else 'FAIL'} · 合計 {'PASS' if rc0 == 0 and all(ok) else 'FAIL'}")
    return 0 if rc0 == 0 and all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
