#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL158_VIAPanoramaAuditRepair v0120 — 薄尾:etag 改成「請求範圍」(同一個檔換參數 = 另一個 etag)· v0119 以前一字不動

操作員 2026-11-21 19:41「收斂完善整理他」;19:36 上傳包 03-漂移 指出、容器同日實測重現:
  read <檔> 拿到 etag=X → read <檔> --depth 3 --if-etag X → 回 [304_NOT_MODIFIED],但 --depth 3 的卡片其實不一樣(AI 會沿用錯的卡)。
根因:v0109 起 etag 只算原檔位元組,沒把請求參數算進去。
本版:read / slice / digest / pack 的 etag = sha256(原檔 etag + 這次的參數)前 16 碼。
  ① 不帶 --if-etag:照前版出卡,卡上的 etag 換成請求範圍的 etag。
  ② 帶 --if-etag:前版照算一次(TEMP 快取命中,很快),對得上請求範圍 etag 才回 304;參數不同或檔變了就出新卡。
其餘動詞(tools · verbs · scan · report · delta · fix · tests · cache · chain …)全部照前版。
舊主控台的字串門要看到的字照留在本檔:"read" "slice" "digest" --if-etag def pack_payload(v0119 ① 的約定)。
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

import contextlib
import functools
import hashlib
import importlib.util
import io
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
SCOPED = ("read", "slice", "digest", "pack")
_ETAG = re.compile(r"etag=([0-9a-f]{8,64})")


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VERBS = dict(PRIOR.VERBS)          # 動詞表照前版:"read" "slice" "digest" "pack" "tools" "verbs" … 之後每一版都要保有 VERBS


def __getattr__(name: str):
    return getattr(PRIOR, name)


@functools.wraps(PRIOR.pack_payload)
def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


def digest_log(text: str) -> dict:
    return PRIOR.digest_log(text)


# ── ② 已修冊複驗的尺(L93 先疑尺不疑樹)──────────────────────────────────────────
# v0115 的 _loaded_chain 只認「程式碼字串裡寫死舊版檔名」的薄尾;用 glob 取「比自己小的最大版號」的薄尾(本家族 v0118 起、
# CGC_MDL156 v0115 都是)被當成沒載入前版 → 已修冊 F536-PINVER / F658-EXEMPT / F658-PINVER 誤報「回歸」(主線 v0119 自測因此 FAIL)。
# 本版補認這種動態載入:檔內真的有載入手段 + 字串常數 "_v*.py" + 比版號(_vnum)→ 載入的是同夾同族比自己小的最大版號。

def _body_module(mod):
    seen = 0
    while mod is not None and seen < 40:
        if "_loaded_chain" in vars(mod) and "_verify_one" in vars(mod):
            return mod
        mod, seen = vars(mod).get("PRIOR"), seen + 1
    return None


_BODY = _body_module(PRIOR)
_DYN = re.compile(r"[\"']_v\*\.py[\"']")


def dynamic_prior(txt: str) -> bool:
    return bool(_DYN.search(txt)) and "_vnum(" in txt and any(x in txt for x in ("spec_from_file_location", "exec_module", "run_path"))


def _loaded_chain(p: Path, limit: int = 12) -> list:
    """同 v0115 的 _loaded_chain,另認 glob 動態取前版的薄尾。"""
    chain, cur = [p], p
    for _ in range(limit):
        m = _BODY._TAIL_RE.match(cur.name)
        if not m:
            break
        try:
            txt = cur.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            break
        ver, stem = int(m.group("ver")), m.group("stem")
        named = _BODY._sibling_loads(txt, stem)
        older = sorted((n for n in named if n < ver and (cur.parent / f"{stem}_v{n:04d}.py").is_file()), reverse=True)
        if not older and dynamic_prior(txt):
            lower = [_vnum(q) for q in cur.parent.glob(stem + "_v*.py") if 0 <= _vnum(q) < ver and q.stem.rsplit("_v", 1)[0] == stem]
            older = sorted(lower, reverse=True)[:1]
        if not older:
            break
        cur = cur.parent / f"{stem}_v{older[0]:04d}.py"
        chain.append(cur)
    return chain


if _BODY is not None:
    _BODY._loaded_chain = _loaded_chain


def split_if_etag(argv: list) -> tuple[list, str]:
    out, want, i = [], "", 0
    while i < len(argv):
        a = argv[i]
        if a == "--if-etag" and i + 1 < len(argv):
            want, i = argv[i + 1], i + 2
            continue
        if a.startswith("--if-etag="):
            want, i = a.split("=", 1)[1], i + 1
            continue
        out.append(a)
        i += 1
    return out, want


def scoped(src_etag: str, request: list) -> str:
    sig = "\x1f".join([src_etag] + [str(x) for x in request])
    return hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]


def run_prior(argv: list) -> tuple[int, str]:
    buf, keep = io.StringIO(), sys.argv
    sys.argv = [keep[0]] + list(argv)
    try:
        with contextlib.redirect_stdout(buf):
            try:
                rc = PRIOR.main()
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    finally:
        sys.argv = keep
    return int(rc or 0), buf.getvalue()


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    if not argv or argv[0] not in SCOPED:
        return PRIOR.main()
    request, want = split_if_etag(argv)
    rc, text = run_prior(request)
    m = _ETAG.search(text)
    if not m:                                   # 前版沒給 etag(錯誤 / 空結果):原樣交回,不冒充 304
        sys.stdout.write(text)
        return rc
    tag = scoped(m.group(1), request)
    if want and want == tag and rc == 0:
        print("[304_NOT_MODIFIED] etag=%s 原檔與參數都沒變,沿用上一張(請求範圍 etag · v0120)" % tag)
        return 0
    sys.stdout.write(_ETAG.sub(lambda mm: "etag=" + scoped(mm.group(1), request), text))
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s v0120 自測開始(本版 8 項 · 再前版 %s)" % (_STEM, _PRIOR_PATH.name), flush=True)
    chk("E1 --if-etag 兩種寫法都拆得出來 · 其他參數順序不動", split_if_etag(["read", "a.py", "--if-etag", "x1", "--depth", "3"]) == (["read", "a.py", "--depth", "3"], "x1")
        and split_if_etag(["slice", "a.py", "f", "--if-etag=y2"]) == (["slice", "a.py", "f"], "y2"))
    with tempfile.TemporaryDirectory(prefix="mdl158_v0120_") as td:
        f = Path(td) / "demo.json"
        f.write_text('{"a": {"b": {"c": [1, 2, {"d": 3}]}}, "e": 1}\n', encoding="utf-8")

        def call(args):
            keep = sys.argv
            sys.argv = [keep[0]] + args
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = main()
            finally:
                sys.argv = keep
            return rc, buf.getvalue()
        rc1, t1 = call(["read", str(f)])
        e1 = (_ETAG.search(t1) or [None, ""])[1]
        rc2, t2 = call(["read", str(f), "--if-etag", e1])
        rc3, t3 = call(["read", str(f), "--depth", "3", "--if-etag", e1])
        e3 = (_ETAG.search(t3) or [None, ""])[1]
        chk("E2 同檔同參數帶回 etag → 304", rc1 == 0 and e1 and "[304_NOT_MODIFIED]" in t2, (e1, t2[:120]))
        chk("E3 同檔換參數(--depth 3)帶舊 etag → 不回 304,出新卡、新 etag(本版修的就是這條)",
            "[304_NOT_MODIFIED]" not in t3 and e3 and e3 != e1, t3[:160])
        f.write_text('{"a": 2}\n', encoding="utf-8")
        rc4, t4 = call(["read", str(f), "--if-etag", e1])
        chk("E4 檔變了帶舊 etag → 出新卡", "[304_NOT_MODIFIED]" not in t4 and _ETAG.search(t4), t4[:160])
    if _BODY is not None:
        ch = [q.name for q in _BODY._loaded_chain(Path(__file__).resolve())]
        f658 = _BODY._verify_one({"kind": "tail_contains", "dir": "supportive modules/registry", "glob": _STEM + "_v*.py",
                                  "markers": ["_load_exempt_roster", "glob_stmt_lines"]}, {}, {})
        chk("E5b 尺:glob 動態載前版的薄尾也算進鏈(本檔 → v0119 → v0118 → …)· F658 憑據在鏈上找得到 = GREEN",
            len(ch) >= 3 and ch[1].endswith("_v0119.py") and f658[0] == "GREEN", (ch[:4], f658))
    else:
        chk("E5b 尺:找不到放 _verify_one 的本體模組", False)
    g = PRIOR.legacy_gate_sees(Path(__file__))
    chk("E5 舊主控台字串門看得到 read / slice / digest / --if-etag / def pack_payload", all(g.values()), g)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("E6 檔面:第 3 行加速器標記 · 零 TA-Lib · 不寫同意閘 · VERBS 在本檔",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and "VERBS = " in src)
    rc_prior = PRIOR.selftest()
    chk("E7 前版 %s 自測照過" % _PRIOR_PATH.name, rc_prior == 0, rc_prior)
    n = sum(ok)
    print("[計] %s v0120 自測 %d/%d · %s" % (_STEM, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
