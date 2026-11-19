#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL237_NumberingSystem v0123 — 薄尾(v0122 一字不動):替同儕系統的工作流冊「只發號、不改冊」(--peer-workflows)

操作員裁定(2026-11-19 14:45「甲」;同日 14:26:「VCGC 監測衝突,我跟 AI 修改後無衝突發號、更改內容,發號後就是政策」):
  准 VCGC 對 VDF / VRN 的工作流冊只發中央號、不改對方的冊。
實錄(同日清點):VDF 58 個 · VRN 8 個工作流 / 步代碼沒有中央號,SDD 的 X-NUM 因此一直紅。衝突哨兵綠、跨系統衝突 0。
  `--apply --scope <對方的工作流冊>` 會被 VCGC 衝突閘的「子系統邊界」擋下:那道閘看到寫入動作指名對方的冊就擋,
  分不出「拿來讀的來源」與「要寫的目標」。發號其實只寫中央的號冊(VIA_NumberBooks · VIA_Numbering_SSOT),不寫那兩本工作流冊。
本版只加一個動作,其餘參數一律原樣交給 v0122(型別、檢測、上限、發號規則都不動):
  --peer-workflows            零寫入:列出兩本工作流冊(VIA_Workflow_VDF_SSOT · VIA_Workflow_VRN_SSOT 尾版)裡還沒有中央號的代碼
  --apply --peer-workflows    發號:本檔自己找那兩本冊的尾版(動作不指名對方的冊),交給既有的「只登本批」去發;
                              發號前後各量一次那兩本冊的內容雜湊,有任何一本變了 = 越界,回 1 並點名(既有的寫後自核照舊會還原本批)。
邊界照舊:衝突閘動作後仍會量 VDF / VRN 正本有沒有被改;本動作只收這兩個冊族,不收任何檔名參數;對方的冊一個位元組都不寫。
只收 VCGC 呼叫(經 via-vcgc run);零網路;不碰 TA-Lib;不讀寫同意閘。
自測:python CGC_MDL237_NumberingSystem_v0123.py --selftest(VIA_SKIP_PRIOR_SELFTEST=1 只跑本版項)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL237_NumberingSystem"
ENGINE = _STEM + "_v0123"
PEER_BOOKS = ("VIA_Workflow_VDF_SSOT", "VIA_Workflow_VRN_SSOT")       # 只收這兩個冊族(操作員 2026-11-19 裁定的範圍)
NUMBOOKS = {"WKF": "VIA_NumberBooks/VIA_NumberBook_WKF_v0100.jsonl", "STP": "VIA_NumberBooks/VIA_NumberBook_STP_v0100.jsonl"}
FLAG = "--peer-workflows"


def _vnum_v0123(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load_v0123(path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0123(p) < _vnum_v0123(__file__)), key=_vnum_v0123)
PRIOR = _load_v0123(PRIOR_PATH, _STEM + "_prior_for_" + ENGINE)        # v0122
BASE = PRIOR.BASE
INTAKE = PRIOR.INTAKE
BASE.ENGINE = ENGINE


def __getattr__(name):
    return getattr(PRIOR, name)


def peer_books(folder=None) -> list:
    """兩個冊族各自的尾版(找不到的那一族不列)。"""
    folder = Path(folder) if folder else HERE
    out = []
    for stem in PEER_BOOKS:
        hits = [p for p in folder.glob(stem + "_v*.json") if _vnum_v0123(p) >= 0]
        if hits:
            out.append(max(hits, key=_vnum_v0123))
    return out


def sha_of(path) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return ""


def declared_codes(book) -> list:
    """一本工作流冊宣告的 (類, 代碼):每條工作流一個 WKF、每一步一個 STP。讀不懂就回空。"""
    try:
        doc = json.loads(Path(book).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for w in doc.get("workflows") or [] if isinstance(doc, dict) else []:
        if isinstance(w, dict) and w.get("code"):
            out.append(("WKF", str(w["code"])))
            out += [("STP", str(s["code"])) for s in w.get("steps") or [] if isinstance(s, dict) and s.get("code")]
    return out


def numbered(folder=None) -> dict:
    """中央號冊裡已經有號的宣告代碼 {類: {代碼}}。"""
    folder = Path(folder) if folder else HERE
    out = {}
    for kind, rel in NUMBOOKS.items():
        got = set()
        try:
            for line in (folder / rel).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        got.add(str(json.loads(line).get("declared") or ""))
                    except ValueError:
                        continue
        except OSError:
            pass
        out[kind] = got
    return out


def missing(folder=None) -> dict:
    """{冊檔名: [還沒有中央號的代碼]}。"""
    have = numbered(folder)
    return {b.name: [c for k, c in declared_codes(b) if c not in have.get(k, set())] for b in peer_books(folder)}


def guarded_apply(books, run, out=sys.stdout) -> int:
    """發號前後各量一次對方的冊;run(檔清單) 是既有的「只登本批」。對方的冊有變 = 越界(回 1)。"""
    if not books:
        print("[%s] %s:找不到 %s 的尾版,一列不寫" % (ENGINE, FLAG, " / ".join(PEER_BOOKS)), file=out)
        return 2
    before = {str(b): sha_of(b) for b in books}
    rc = run(books)
    crossed = [Path(b).name for b in before if sha_of(b) != before[b]]
    if crossed:
        print("[編號 · 同儕工作流] RED · 越界:發號動到了對方的冊 %s(本動作只准寫中央號冊;請把這幾本還原)" % "、".join(crossed), file=out)
        return 1
    print("[編號 · 同儕工作流] 對方的冊 %d 本內容雜湊前後相同(一個位元組都沒寫)· 發號 rc %s" % (len(books), rc), file=out)
    return rc


def _rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA)).replace("\\", "/")
    except ValueError:
        return str(p)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if FLAG in args:
        rest = [a for a in args if a not in (FLAG, "--apply", "--json")]
        if rest:
            print("[拒跑] %s:%s 不收其他參數(%s);冊由本檔自己找尾版 · 零寫入" % (ENGINE, FLAG, " ".join(rest)))
            return 2
        miss = missing()
        n = sum(len(v) for v in miss.values())
        if "--apply" not in args:
            if "--json" in args:
                print(json.dumps({"via": "vcgc", "verb": FLAG, "apply": False, "books": miss, "missing": n}, ensure_ascii=False))
            else:
                print("[編號 · 同儕工作流] PLAN · 零寫入 · 還沒有中央號 %d 個" % n)
                for b, codes in miss.items():
                    print("  %s:%d 個%s" % (b, len(codes), (" · " + "、".join(codes[:6]) + (" …" if len(codes) > 6 else "")) if codes else ""))
                print("  發號:via-vcgc run %s --apply %s(只寫中央號冊;對方的冊不動)" % (_STEM, FLAG))
            return 0
        print("[編號 · 同儕工作流] 操作員 2026-11-19 裁定:VCGC 對 VDF / VRN 的工作流冊只發號、不改冊 · 待發 %d 個" % n)
        if not n:
            print("[編號 · 同儕工作流] 沒有要發的號,一列不寫")
            return 0
        return guarded_apply(peer_books(), lambda books: PRIOR.main(["--apply", "--scope"] + [_rel(b) for b in books]))
    return PRIOR.main(args)


def selftest() -> int:
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(薄尾 · 同儕工作流只發號不改冊;夾具 · 零網路 · 不碰真號冊)===" % ENGINE, flush=True)
    chk("① 前版是 v0122 · 引擎名是本版", _vnum_v0123(PRIOR_PATH) == 122 and BASE.ENGINE == ENGINE, PRIOR_PATH.name)
    tmp = Path(tempfile.mkdtemp(prefix="via_num123_"))
    try:
        (tmp / "VIA_NumberBooks").mkdir()
        wf = lambda code, steps: {"code": code, "steps": [{"code": "%s-STP%03d" % (code, i + 1)} for i in range(steps)]}
        (tmp / "VIA_Workflow_VDF_SSOT_v0002.json").write_text(json.dumps({"workflows": [wf("VDF-WKF001", 2)]}), encoding="utf-8")
        (tmp / "VIA_Workflow_VDF_SSOT_v0010.json").write_text(json.dumps({"workflows": [wf("VDF-WKF001", 2), wf("VDF-WKF002", 1)]}), encoding="utf-8")
        (tmp / "VIA_Workflow_VRN_SSOT_v0003.json").write_text(json.dumps({"workflows": [wf("VRN-WKF001", 1)]}), encoding="utf-8")
        (tmp / "VIA_Workflow_VCGC_SSOT_v0099.json").write_text(json.dumps({"workflows": [wf("VCGC-WKF001", 1)]}), encoding="utf-8")
        (tmp / NUMBOOKS["WKF"]).write_text("\n".join(json.dumps({"declared": c}) for c in ("VDF-WKF001", "VRN-WKF001")) + "\n{壞行\n", encoding="utf-8")
        (tmp / NUMBOOKS["STP"]).write_text("\n".join(json.dumps({"declared": c}) for c in ("VDF-WKF001-STP001", "VDF-WKF001-STP002")) + "\n", encoding="utf-8")
        books = peer_books(tmp)
        chk("② 只找 VDF / VRN 兩個冊族的尾版(版號照數字比;VCGC 自己的冊不在內)", [b.name for b in books] == ["VIA_Workflow_VDF_SSOT_v0010.json", "VIA_Workflow_VRN_SSOT_v0003.json"], [b.name for b in books])
        miss = missing(tmp)
        chk("③ 還沒有號的代碼:照中央號冊的 declared 欄比;已有號的不列;號冊裡的壞行略過",
            miss == {"VIA_Workflow_VDF_SSOT_v0010.json": ["VDF-WKF002", "VDF-WKF002-STP001"], "VIA_Workflow_VRN_SSOT_v0003.json": ["VRN-WKF001-STP001"]}, miss)
        seen, buf = [], io.StringIO()
        rc_ok = guarded_apply(books, lambda bs: seen.append([b.name for b in bs]) or 0, out=buf)
        chk("④ 對方的冊沒被動:照既有發號的 rc 回(0),並印「雜湊前後相同」", rc_ok == 0 and seen == [[b.name for b in books]] and "前後相同" in buf.getvalue(), buf.getvalue())
        chk("⑤ 既有發號回非 0(例:自核不過)照原樣回,不改成 0", guarded_apply(books, lambda bs: 2, out=io.StringIO()) == 2)
        buf2 = io.StringIO()

        def bad(bs):
            Path(bs[0]).write_text(Path(bs[0]).read_text(encoding="utf-8") + " ", encoding="utf-8")
            return 0
        rc_bad = guarded_apply(books, bad, out=buf2)
        chk("⑥ 負控:發號過程動到對方的冊 → 越界 rc 1 並點名那一本(就算發號自己回 0)", rc_bad == 1 and "越界" in buf2.getvalue() and books[0].name in buf2.getvalue(), buf2.getvalue())
        buf3 = io.StringIO()
        chk("⑦ 找不到冊:rc 2 · 不呼叫發號", guarded_apply([], lambda bs: seen.append("不該到這") or 0, out=buf3) == 2 and "不該到這" not in seen)
        empty = Path(tempfile.mkdtemp(prefix="via_num123_e_"))
        chk("⑧ 空夾 / 冊讀不懂:不炸,回空", peer_books(empty) == [] and missing(empty) == {} and declared_codes(empty / "nope.json") == [] and numbered(empty) == {"WKF": set(), "STP": set()})
        shutil.rmtree(str(empty), ignore_errors=True)
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    calls, real = [], PRIOR.main
    PRIOR.main = lambda a: calls.append(list(a)) or 0
    try:
        keep_out, sys.stdout = sys.stdout, io.StringIO()
        try:
            r1 = main([FLAG, "x.json"])
            r2 = main(["--apply", FLAG, "--scope"])
            r3 = main([FLAG])
            r4 = main(["audit"])
        finally:
            sys.stdout = keep_out
    finally:
        PRIOR.main = real
    chk("⑨ 本動作不收檔名或其他參數(rc 2 · 不呼叫發號);不帶 --apply = 零寫入計畫(不呼叫發號);其餘參數原樣交給前版",
        r1 == 2 and r2 == 2 and r3 == 0 and r4 == 0 and calls == [["audit"]], (r1, r2, r3, r4, calls))
    real_books = peer_books()
    chk("⑩ 真樹:兩本同儕工作流冊找得到 · 計畫讀得出數字(零寫入)", len(real_books) == 2 and all(isinstance(v, list) for v in missing().values()), [b.name for b in real_books])
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("⑪ 本檔自己不寫檔 · 不連網 · 不用 TA-Lib · 不寫同意閘 · 不 import 他系統", ".write_text(" not in live and "open(" not in live
        and not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|VDF_|VRN_)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        BASE.ENGINE = PRIOR.ENGINE                        # v0122 自測會核對引擎名是它自己
        try:
            rc_prior = PRIOR.selftest()
        finally:
            BASE.ENGINE = ENGINE
        chk("⑫ 前版 v0122 自測(含它的前版鏈)rc 0 · 跑完引擎名還原成本版", rc_prior == 0 and BASE.ENGINE == ENGINE, "rc %s" % rc_prior)
    n = sum(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
