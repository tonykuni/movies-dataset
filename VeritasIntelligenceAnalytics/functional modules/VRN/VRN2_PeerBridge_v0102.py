#!/usr/bin/env python3
r"""VRN2_PeerBridge v0102 — 薄尾(v0100 · v0101 一字不改):整合冊出新版號 · 把 prove 實跑證據寫進冊裡

操作員 2026-11-14 令「VRN-2 不足處用 VRN-1 補強」「把差異加進 VRN-2」「VRN 只出現在 HTML U/I」。
2026-11-14 容器實跑(VRN-1 = tonykuni/via-vdf-vrn 淺 clone,只讀):
  gap:能力 23 項 · MATCH 14 · BORROWED 8 · BY_CONTRACT 1 · REVIEW 0 · GAP 0(借用冊 8 支指紋與 VRN-1 現檔全相符)
  prove:8 支 VRN-1 借用工具各自 selftest 全 PASS · VRN-1 樹未被動到 → 就緒燈 GREEN
  integrate --apply:v0101 只認 VRN2_IntegrationBook_v0100.json 一個檔名 —— 2026-11-10 寫的那份就緒燈 YELLOW
  (當時沒有 prove 收據),今天整合過了卻寫不進去(「已存在 → 不覆蓋」),而 prove 收據只在 VIA_Reports(不入倉)。
本版只補這塊(其餘全部照 v0101):
  ① integrate --apply:冊夾裡取最新版號的整合冊比「實質內容」(能力 · 狀態 · 主人 · 就緒燈 · 借用證據的指紋與結果;
     不比時間戳);不同 → 寫下一個版號(新檔 x 模式建立,舊冊一個位元組都不動,冊頭記 supersedes);相同 → 不出新版。
  ② 冊裡多一段 prove:最新 prove 收據的摘要(收據時間 · VRN-1 commit · VRN-1 樹未被動到 · 每支借用工具的指紋 / rc / 結果 /
     最後一行)—— 只收「借用冊上那幾支、且指紋相同」的列;指紋對不上照實標 pin_mismatch,不算證據。
借用照舊:不複製 VRN-1 的檔進本倉,VRN-2 經 borrow(能力 id)唯讀載入(載入前比指紋,對不上就擋)。VRN-1 只讀(L123)。
零網路 · 不碰 TA-Lib · 不讀寫同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

_STEM = "VRN2_PeerBridge"
import contextlib
import importlib.util
import os
import pathlib
import re
import sys
import tempfile
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def _vnum_tail(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_tail(p) < _vnum_tail(__file__)), key=_vnum_tail)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    warnings.simplefilter("ignore", DeprecationWarning)
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _own_src_ok() -> bool:
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    return ("[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "_CONSENT" not in body
            and not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|ta" + r"lib\b)", src, re.M))


class _Checks:
    def __init__(self):
        self.ok = []

    def __call__(self, name, cond, note=""):
        self.ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if (note and not cond) else ""), flush=True)

    def done(self) -> int:
        good = all(self.ok)
        print("[計] %s 薄尾 %d/%d · %s" % (TAG, sum(self.ok), len(self.ok), "PASS" if good else "FAIL"), flush=True)
        return 0 if good else 1


import argparse
import json
import subprocess

VERSION = "v0102"
BOOK_DIR_REL = "functional modules/VRN/ssot"
BOOK_PREFIX = "VRN2_IntegrationBook_v"


def _book_ver(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.json$", Path(p).name)
    return int(m.group(1)) if m else -1


def latest_book(book_dir: Path):
    hits = [p for p in Path(book_dir).glob(BOOK_PREFIX + "*.json") if _book_ver(p) >= 0]
    return max(hits, key=_book_ver) if hits else None


def _substance(book: dict) -> dict:
    ents = []
    for e in book.get("entries") or []:
        own = dict(e.get("owner") or {})
        own.pop("via", None)                         # 「經哪一版 CLI 借」是說明,不是實質
        ents.append({"cap": e.get("cap"), "state": e.get("state"), "owner": own})
    rd = book.get("readiness") or {}
    pv = book.get("prove") or {}
    rows = sorted((r.get("cap"), r.get("sha256"), r.get("result"), bool(r.get("pin_mismatch"))) for r in pv.get("rows") or [])
    return {"counts": book.get("counts"), "entries": ents, "lamp": rd.get("lamp"), "proven": rd.get("borrowed_proven"),
            "prove_rows": rows, "vrn1_untouched": pv.get("vrn1_untouched")}


def _git_head(root) -> str | None:
    if not root:
        return None
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def prove_summary(receipt: dict | None, borrowed: dict, vrn1_commit: str | None = None) -> dict | None:
    """最新 prove 收據 → 冊用摘要;只收借用冊上那幾支。指紋對不上 → pin_mismatch(不算證據)。"""
    if not receipt:
        return None
    rows = []
    for x in receipt.get("rows") or []:
        cap = x.get("cap")
        if cap not in borrowed:
            continue
        tail = x.get("tail") or []
        rows.append({"cap": cap, "vrn1_engine": x.get("vrn1_engine"), "sha256": x.get("sha256"), "rc": x.get("rc"),
                     "result": x.get("result"), "last": str(tail[-1])[:160] if tail else "",
                     "pin_mismatch": x.get("sha256") != borrowed[cap]})
    return {"receipt_ts": receipt.get("ts"), "receipt_version": receipt.get("version"), "vrn1_commit": vrn1_commit,
            "vrn1_untouched": receipt.get("vrn1_untouched"), "lamp": receipt.get("lamp"), "rows": rows,
            "missing": sorted(set(borrowed) - {r["cap"] for r in rows})}


def plan_write(book_dir: Path, book: dict) -> dict:
    prev = latest_book(book_dir)
    if prev is None:
        return {"write": True, "path": Path(book_dir) / (BOOK_PREFIX + "0100.json"), "prev": None, "why": "冊夾裡還沒有整合冊"}
    try:
        old = json.loads(prev.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        old = {"_unreadable": str(exc)}
    if _substance(old) == _substance(book):
        return {"write": False, "path": None, "prev": prev, "why": "與 %s 實質相同(能力 · 主人 · 就緒燈 · 借用證據)" % prev.name}
    nxt = Path(book_dir) / ("%s%04d.json" % (BOOK_PREFIX, _book_ver(prev) + 1))
    return {"write": True, "path": nxt, "prev": prev, "why": "與 %s 實質不同 → 出下一版" % prev.name}


def write_book(plan: dict, book: dict) -> Path:
    out = Path(plan["path"])
    book = dict(book, version="v%s" % out.stem.rsplit("_v", 1)[-1], built_by="VRN2_PeerBridge_%s" % VERSION,
                supersedes=plan["prev"].name if plan.get("prev") else None)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "x", encoding="utf-8") as fh:       # x:檔已在就丟 FileExistsError —— 只增,絕不覆蓋
        fh.write(json.dumps(book, ensure_ascii=False, indent=1) + "\n")
    return out


def cmd_integrate(args) -> int:
    via = PRIOR.B.via_root()
    book = PRIOR.integration_book(via)
    r = PRIOR.readiness(via)
    print(f"[整合冊 {VERSION}] 能力 {book['total']} · {book['counts']} · 問題 {len(book['problems'])}")
    for p in book["problems"]:
        print(f"  [擋] {p}")
    if book["problems"] or r["blockers"]:
        for b in r["blockers"]:
            print(f"  [擋] {b}")
        print("[拒絕整合] 不可丟失 / 不可重複 沒過,或就緒燈有擋。")
        return 1
    book["readiness"] = {"lamp": r["lamp"], "notes": r["notes"], "borrowed_proven": r["borrowed_proven"]}
    borrowed = {e["cap"]: (e.get("owner") or {}).get("sha256") for e in book["entries"] if e["state"] == "BORROWED"}
    vrn1, _why = PRIOR.B.find_vrn1(via)
    book["prove"] = prove_summary(PRIOR.latest_prove(via), borrowed, _git_head(vrn1))
    pl = plan_write(via / BOOK_DIR_REL, book)
    pv = book["prove"] or {}
    print(f"  [證據] prove 收據 {pv.get('receipt_ts') or '沒有'} · VRN-1 commit {str(pv.get('vrn1_commit') or '—')[:12]}"
          f" · 樹未動 {pv.get('vrn1_untouched')} · 借用 {len(borrowed)} 支 · 收進冊 {len(pv.get('rows') or [])} 列")
    if not getattr(args, "apply", False):
        print(f"[預覽] 就緒燈 {r['lamp']} · {pl['why']}" + (f" · 加 --apply 寫 {pl['path'].name}(新檔,只增)" if pl["write"] else ""))
        return 0
    if not pl["write"]:
        print(f"[不變] {pl['why']} —— 不出新版")
        return 0
    out = write_book(pl, book)
    print(f"[寫入] {out.relative_to(via) if str(out).startswith(str(via)) else out} · 就緒燈 {r['lamp']} · supersedes {pl['prev'].name if pl['prev'] else '—'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = PRIOR.build_parser()
    ap.prog = f"VRN2_PeerBridge_{VERSION}"
    sub = next(a for a in ap._actions if isinstance(a, argparse._SubParsersAction))
    sub.choices["integrate"].set_defaults(fn=cmd_integrate)
    return ap


def selftest() -> int:
    chk = _Checks()
    print("=== %s · 薄尾自測(整合冊出新版號 · prove 證據入冊;零網路 · 只寫沙盒)===" % TAG, flush=True)
    pins = {"a.cap": "a" * 64, "b.cap": "b" * 64}
    receipt = {"ts": "2026-11-14T20:20:24Z", "version": "v0101", "vrn1_untouched": True, "lamp": "GREEN",
               "rows": [{"cap": "a.cap", "vrn1_engine": "A.py", "sha256": "a" * 64, "rc": 0, "result": "PASS", "tail": ["x", "[A] 3/3"]},
                        {"cap": "b.cap", "vrn1_engine": "B.py", "sha256": "c" * 64, "rc": 0, "result": "PASS", "tail": []},
                        {"cap": "z.cap", "vrn1_engine": "Z.py", "sha256": "z" * 64, "rc": 0, "result": "PASS", "tail": []}]}
    ps = prove_summary(receipt, pins, "f" * 40)
    chk("① prove 摘要只收借用冊上的能力(z 不收)· 指紋對不上標 pin_mismatch · 留 VRN-1 commit 與「樹未動」",
        [r["cap"] for r in ps["rows"]] == ["a.cap", "b.cap"] and ps["rows"][1]["pin_mismatch"] and not ps["rows"][0]["pin_mismatch"]
        and ps["vrn1_commit"] == "f" * 40 and ps["vrn1_untouched"] is True and ps["rows"][0]["last"] == "[A] 3/3" and ps["missing"] == [])
    base = {"counts": {"MATCH": 1, "BORROWED": 1}, "total": 2, "problems": [],
            "entries": [{"cap": "m", "state": "MATCH", "owner": {"system": "VRN-2", "file": "x.py"}},
                        {"cap": "a.cap", "state": "BORROWED", "owner": {"system": "VRN-1", "sha256": "a" * 64, "via": "VRN2_PeerBridge_v0101.py borrow a.cap"}}],
            "readiness": {"lamp": "YELLOW", "borrowed_proven": False}}
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        p0 = plan_write(d, base)
        f0 = write_book(p0, base)
        chk("② 冊夾空 → 寫第一版 v0100", f0.name == BOOK_PREFIX + "0100.json" and json.loads(f0.read_text(encoding="utf-8"))["supersedes"] is None)
        b0 = f0.read_bytes()
        same = json.loads(json.dumps(base))
        same["entries"][1]["owner"]["via"] = "VRN2_PeerBridge_v0102.py borrow a.cap"
        p1 = plan_write(d, same)
        chk("③ 實質相同(只差時間戳 / 經哪版 CLI)→ 不出新版", p1["write"] is False and "實質相同" in p1["why"])
        newer = dict(json.loads(json.dumps(base)), readiness={"lamp": "GREEN", "borrowed_proven": True}, prove=ps)
        p2 = plan_write(d, newer)
        f2 = write_book(p2, newer)
        j2 = json.loads(f2.read_text(encoding="utf-8"))
        chk("④ 就緒燈 YELLOW → GREEN + prove 證據 → 出 v0101(supersedes v0100)· 舊冊一個位元組都沒動",
            f2.name == BOOK_PREFIX + "0101.json" and j2["supersedes"] == BOOK_PREFIX + "0100.json" and j2["version"] == "v0101"
            and j2["prove"]["rows"][0]["cap"] == "a.cap" and f0.read_bytes() == b0)
        try:
            write_book({"path": f2, "prev": f0}, newer)
            refused = False
        except FileExistsError:
            refused = True
        chk("⑤ 目標檔已在 → 拒寫(x 模式,絕不覆蓋)", refused and json.loads(f2.read_text(encoding="utf-8")) == j2)
        chk("⑥ 再跑一次同內容 → 不變(最新版是 v0101)", plan_write(d, newer)["write"] is False)
    ap = build_parser()
    a = ap.parse_args(["integrate", "--apply"])
    chk("⑦ CLI:integrate 換成本版 · 其餘動詞照 v0101(gap / prove / readiness)",
        a.fn is cmd_integrate and ap.parse_args(["gap"]).fn is PRIOR.cmd_gap and ap.parse_args(["prove"]).fn is PRIOR.cmd_prove)
    rc = PRIOR.selftest()
    chk("⑧ 前版 v0101 自測 rc 0(含 v0100)", rc == 0, rc)
    body = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑨ 兩座橋在 · 不匯入他系統 · 不碰 TA-Lib · 同意閘不讀不寫 · 不複製 VRN-1 的檔(本體無 shutil / copy)",
        _own_src_ok() and "shutil" not in body and "copyfile(" not in body and "copy2(" not in body)
    return chk.done()


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    PRIOR._route_prior()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 0
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
