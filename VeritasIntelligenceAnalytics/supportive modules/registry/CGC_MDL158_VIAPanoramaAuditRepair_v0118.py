#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL158_VIAPanoramaAuditRepair v0118 — 薄尾:全景加 TEMP 快取 · delta 只看差異 · fix 先沙盒再原子換檔(v0117 以前一字不動)

操作員 2026-11-19:「這個動作應該有了 · 強化全景式的功能能力大幅提升 · 資料存 TEMP · 這個動作最強化以後啟動,節省很多 TOKEN」。
同日附件(通用治理方案)逐項對過真倉:骨架卡 / 切片 / ETag / 日誌摘要 / 三態分流 VIA 早就有;缺的是下面三件,本版只補這三件:
  ① TEMP 快取:每支檔的稽核結果依「相對路徑 + 內容雜湊(LF 統一)+ 豁免理由 + 本版號」存在 TEMP(%TEMP%\\VIA_token_cache\\MDL158;
     可用 VIA_TOKEN_CACHE 指別處)。沒改過的檔下一輪直接沿用 → 重掃從分鐘級降到秒級;改過的檔照常重算(結果與不用快取逐筆相同)。
  ② delta [--max N]:全景跑一輪(走快取),只印「跟上一輪比」新增 / 已解的問題與三數(應掃 · 已掃 · 略過);上一輪快照也放 TEMP。
     AI 之後只讀差異,不再讀整張全景。
  ③ fix 加固:落檔一律「同夾暫存 → fsync → os.replace」原子換檔;--apply 前先把原檔備份到 TEMP;改後必過 ast.parse + compile,
     且重新稽核該檔「要修的那幾類沒有變多、沒有新的 SYNTAX」,任何一關不過就從 TEMP 備份還原(紅燈棘輪)。
  另:cache [status|clear] 看 / 清快取。其餘動詞(read · slice · digest · pack · chain · scan · report · fix · tests)照前版。
唯讀原則照舊(scan / delta / read 不寫倉內任何檔;快取與快照只寫 TEMP)。零網路 · 不碰 TA-Lib。
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

import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_V0118 = "v0118"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0117.py")
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


BODY = PRIOR.scan.__globals__                 # 本體模組的全域(scan / fix / main 都從這裡找 audit_source · fix_one · fix)
_ORIG_AUDIT = BODY["audit_source"]
_ORIG_FIX_ONE = BODY["fix_one"]
_ORIG_FIX = BODY["fix"]
STATS = {"hit": 0, "miss": 0}


# ── ① TEMP 快取 ─────────────────────────────────────────────────────────
def cache_root() -> Path:
    base = os.environ.get("VIA_TOKEN_CACHE") or os.path.join(tempfile.gettempdir(), "VIA_token_cache")
    return Path(base) / "MDL158"


def _key(rel: str, src: str) -> str:
    norm = src.replace("\r\n", "\n").encode("utf-8", "replace")          # 跨平台位元組:先統一 LF 再算雜湊
    why = BODY["template_exempt"](rel) or ""
    h = hashlib.sha256()
    for part in (_V0118.encode(), rel.replace("\\", "/").encode("utf-8"), b"\0", why.encode("utf-8"), b"\0", norm):
        h.update(part)
    return h.hexdigest()


def _cpath(k: str) -> Path:
    return cache_root() / "audit" / k[:2] / (k + ".json")


def atomic_write_text(path, text: str, encoding: str = "utf-8", errors=None, newline=None) -> int:
    """同夾暫存 → fsync → os.replace(同一個磁區,換檔是原子的;中途斷電不會留下寫一半的檔)。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + p.name + ".", suffix=".via_tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding=encoding, errors=errors, newline=newline) as fh:
            n = fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
        return n
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cached_audit(path, src: str, rel: str) -> list:
    k = _key(rel, src)
    cp = _cpath(k)
    try:
        rows = json.loads(cp.read_text(encoding="utf-8"))
        STATS["hit"] += 1
        return rows
    except (OSError, ValueError):
        pass
    rows = _ORIG_AUDIT(path, src, rel)
    STATS["miss"] += 1
    try:
        atomic_write_text(cp, json.dumps(rows, ensure_ascii=False))
    except OSError:
        pass                                    # 快取寫不進去只是變慢,不影響結果
    return copy.deepcopy(rows)                  # scan 會在每筆上 update(file, system):不讓它改到快取裡的物件


def cache_status() -> dict:
    root = cache_root()
    files = list((root / "audit").rglob("*.json")) if (root / "audit").exists() else []
    size = sum(f.stat().st_size for f in files)
    return {"root": str(root), "entries": len(files), "mb": round(size / 1e6, 2),
            "last": str(root / "panorama_last.json") if (root / "panorama_last.json").exists() else None}


def cache_clear() -> int:
    root = cache_root()
    n = len(list((root / "audit").rglob("*.json"))) if (root / "audit").exists() else 0
    shutil.rmtree(root / "audit", ignore_errors=True)       # 只清本工具自己在 TEMP 的快取夾
    return n


# ── ② delta:只看差異 ─────────────────────────────────────────────────
def _ident(r: dict) -> str:
    return "|".join(str(r.get(k, "")) for k in ("file", "cls", "detail"))     # 不含行號:上面多一行不算新問題


def _keyed(rows: list) -> dict:
    """同檔同類同說明的第 n 筆各自成鍵(依行號排序後編號):同一支檔多冒一筆同樣的問題也看得到。"""
    seen, out = {}, {}
    for r in sorted(rows, key=lambda r: (_ident(r), int(r.get("line") or 0))):
        k = _ident(r)
        seen[k] = seen.get(k, 0) + 1
        out[k + "#" + str(seen[k])] = r
    return out


def delta(prev_rows: list, cur_rows: list) -> dict:
    a, b = _keyed(prev_rows), _keyed(cur_rows)
    new = [b[k] for k in b if k not in a]
    gone = [a[k] for k in a if k not in b]
    return {"new": new, "resolved": gone, "same": len(set(a) & set(b)), "prev": len(a), "cur": len(b)}


def run_delta(max_show: int = 40, echo=print) -> int:
    snap = cache_root() / "panorama_last.json"
    try:
        prev = json.loads(snap.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        prev = None
    STATS.update(hit=0, miss=0)
    d = BODY["scan"](progress=False)
    files = BODY["py_files"]()
    skipped = d.get("skipped") or []
    should = len(files) + len(skipped)
    tn = "應掃 %d · 已掃 %d · 略過 %d" % (should, len(files), len(skipped))
    atomic_write_text(snap, json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "rows": d["rows"], "files": len(files)}, ensure_ascii=False))
    if prev is None:
        echo("[delta] 第一輪(TEMP 還沒有上一輪快照):已存基準 · %s · 問題 %d · 快取 命中 %d / 重算 %d · %.1fs"
             % (tn, d["issues"], STATS["hit"], STATS["miss"], d["secs"]))
        return 0
    x = delta(prev["rows"], d["rows"])
    lamp = "RED" if any(r.get("cls") in ("SYNTAX", "TALIB", "COMPILE") for r in x["new"]) else ("YELLOW" if x["new"] else "GREEN")
    echo("[delta] %s · 比上一輪(%s)· 新增 %d · 已解 %d · 不變 %d · 現有 %d · %s · 快取 命中 %d / 重算 %d · %.1fs"
         % (lamp, prev.get("ts", "?"), len(x["new"]), len(x["resolved"]), x["same"], x["cur"], tn, STATS["hit"], STATS["miss"], d["secs"]))
    for tag, rows in (("新", x["new"]), ("解", x["resolved"])):
        for r in rows[:max_show]:
            echo("  [%s] %-8s %s:%s · %s" % (tag, r.get("cls", ""), r.get("file", ""), r.get("line", ""), str(r.get("detail", ""))[:110]))
        if len(rows) > max_show:
            echo("  [%s] … 另 %d 筆(--max N 看更多)" % (tag, len(rows) - max_show))
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


# ── ③ fix:先備份到 TEMP · 改後必過 parse + compile · 棘輪 · 原子換檔 ─────────────
def _bad_count(rows: list, classes: set) -> int:
    return sum(1 for r in rows if r.get("cls") in classes)


def make_safe_fix_one(orig, via_root=None, audit=None, bak_root=None):
    def safe_fix_one(rel: str, classes: set, apply: bool) -> dict:
        if not apply:
            return orig(rel, classes, apply)
        root = Path(via_root or BODY["VIA"])
        path = root / rel
        try:
            before = path.read_bytes()
        except OSError:
            return orig(rel, classes, apply)
        bak = Path(bak_root or (cache_root() / "bak" / time.strftime("%Y%m%d_%H%M%S"))) / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        bak.write_bytes(before)
        aud = audit or _ORIG_AUDIT
        src0 = before.decode("utf-8", "replace")
        n0 = _bad_count(aud(path, src0, rel), set(classes))
        res = orig(rel, classes, apply)
        try:
            after = path.read_bytes()
        except OSError:
            after = before
        if after == before:
            return res
        src1 = after.decode("utf-8", "replace")
        why = ""
        try:
            compile(src1, str(path), "exec", dont_inherit=True)
        except SyntaxError as exc:
            why = "改後 compile 不過(行 %s)" % exc.lineno
        if not why:
            rows1 = aud(path, src1, rel)
            if any(r.get("cls") == "SYNTAX" for r in rows1):
                why = "改後出現 SYNTAX"
            elif _bad_count(rows1, set(classes)) > n0:
                why = "要修的類別反而變多(%d → %d)" % (n0, _bad_count(rows1, set(classes)))
        if why:
            _restore(path, before)
            res = dict(res, ok=False, applied=[], why=why + " → 已從 TEMP 備份還原", rolled_back=str(bak))
        else:
            res = dict(res, backup=str(bak))
        return res
    return safe_fix_one


def _restore(path: Path, data: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".via_tmp", dir=str(path.parent))
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def safe_fix(*a, **k):
    """fix 期間所有 Path.write_text 走原子換檔;結束還原。"""
    orig_wt = Path.write_text
    Path.write_text = lambda self, data, encoding=None, errors=None, newline=None: atomic_write_text(self, data, encoding or "utf-8", errors, newline)
    try:
        return _ORIG_FIX(*a, **k)
    finally:
        Path.write_text = orig_wt


def install() -> None:
    BODY["audit_source"] = cached_audit
    BODY["fix_one"] = make_safe_fix_one(_ORIG_FIX_ONE)
    BODY["fix"] = safe_fix


def uninstall() -> None:
    BODY["audit_source"], BODY["fix_one"], BODY["fix"] = _ORIG_AUDIT, _ORIG_FIX_ONE, _ORIG_FIX


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    verb = argv[0] if argv else ""
    if verb == "cache":
        if argv[1:2] == ["clear"]:
            print("[cache] 已清 %d 筆(只清 %s 下的稽核快取)" % (cache_clear(), cache_root()))
            return 0
        print("[cache] " + json.dumps(cache_status(), ensure_ascii=False))
        return 0
    install()
    if verb == "delta":
        mx = int(argv[argv.index("--max") + 1]) if "--max" in argv and argv.index("--max") + 1 < len(argv) else 40
        return run_delta(mx)
    rc = PRIOR.main()
    if verb in ("scan", "report", "fix", "all") and (STATS["hit"] or STATS["miss"]):
        print("  [TEMP 快取] 命中 %d · 重算 %d · %s" % (STATS["hit"], STATS["miss"], cache_root()))
    return rc


def selftest() -> int:
    uninstall()
    rc_prior = PRIOR.selftest()                # 前版鏈照原樣自測(本版還沒裝)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note and not cond else ""))
    with tempfile.TemporaryDirectory(prefix="via_mdl158_v0118_") as td:
        os.environ["VIA_TOKEN_CACHE"] = os.path.join(td, "cache")
        root = Path(td) / "tree"
        (root / "pkg").mkdir(parents=True)
        src = "import os\n\ndef f(x):\n    return x + 1\n"
        f = root / "pkg" / "m_v0100.py"
        f.write_text(src, encoding="utf-8")
        STATS.update(hit=0, miss=0)
        a = cached_audit(f, src, "pkg/m_v0100.py")
        b = cached_audit(f, src, "pkg/m_v0100.py")
        chk("① 同內容第二次走快取 · 結果與本體逐筆相同", STATS == {"hit": 1, "miss": 1} and a == b == _ORIG_AUDIT(f, src, "pkg/m_v0100.py"), STATS)
        b[0:0] = [{"cls": "X"}] if isinstance(b, list) else b
        c = cached_audit(f, src, "pkg/m_v0100.py")
        chk("② 呼叫端改動回傳值不會汙染快取(深拷貝)", c == a)
        cached_audit(f, src.replace("\n", "\r\n"), "pkg/m_v0100.py")
        chk("③ CRLF 與 LF 同一份內容算同一個鍵(跨平台不重算)", STATS["miss"] == 1)
        cached_audit(f, src + "x = 1\n", "pkg/m_v0100.py")
        chk("④ 內容改了就重算", STATS["miss"] == 2)
        p1 = [{"file": "a.py", "cls": "ACCEL", "detail": "d", "line": 3}, {"file": "b.py", "cls": "PINVER", "detail": "p", "line": 9}]
        p2 = [{"file": "a.py", "cls": "ACCEL", "detail": "d", "line": 4}, {"file": "c.py", "cls": "SYNTAX", "detail": "s", "line": 1}]
        x = delta(p1, p2)
        chk("⑤ delta:行號挪動不算新問題 · 新 1 · 解 1 · 不變 1", len(x["new"]) == 1 and len(x["resolved"]) == 1 and x["same"] == 1)
        p3 = p2 + [{"file": "a.py", "cls": "ACCEL", "detail": "d", "line": 40}]
        y = delta(p2, p3)
        chk("⑤b 同檔同類同說明多冒一筆也算新增(不被合併吃掉)", len(y["new"]) == 1 and y["same"] == 2 and y["cur"] == 3, y)
        g = root / "pkg" / "g_v0100.py"
        good = "def g():\n    return 1\n"
        g.write_text(good, encoding="utf-8")

        def breaker(rel, classes, apply):
            (root / rel).write_text("def g(:\n", encoding="utf-8")
            return {"file": rel, "applied": ["X"], "ok": True}
        r = make_safe_fix_one(breaker, via_root=root, audit=lambda p, s, rl: [], bak_root=Path(td) / "bak")("pkg/g_v0100.py", {"ACCEL"}, True)
        chk("⑥ fix 改壞(compile 不過)→ 從 TEMP 備份原子還原 · 回報 ok=False", g.read_text(encoding="utf-8") == good and r["ok"] is False
            and "還原" in r["why"] and (Path(td) / "bak" / "pkg" / "g_v0100.py").exists(), r)

        def worse(rel, classes, apply):
            (root / rel).write_text(good + "y = 2\n", encoding="utf-8")
            return {"file": rel, "applied": ["ACCEL"], "ok": True}
        aud = lambda p, s, rl: [{"cls": "ACCEL"}] * (2 if "y = 2" in s else 1)      # noqa: E731
        r = make_safe_fix_one(worse, via_root=root, audit=aud, bak_root=Path(td) / "bak2")("pkg/g_v0100.py", {"ACCEL"}, True)
        chk("⑦ 棘輪:要修的類別變多 → 還原", g.read_text(encoding="utf-8") == good and r["ok"] is False and "變多" in r["why"], r)

        def fine(rel, classes, apply):
            (root / rel).write_text(good + "z = 3\n", encoding="utf-8")
            return {"file": rel, "applied": ["ACCEL"], "ok": True}
        r = make_safe_fix_one(fine, via_root=root, audit=lambda p, s, rl: [], bak_root=Path(td) / "bak3")("pkg/g_v0100.py", {"ACCEL"}, True)
        chk("⑧ 改得好就留下 · 回報備份位置", "z = 3" in g.read_text(encoding="utf-8") and r.get("backup"), r)
        atomic_write_text(g, good)
        chk("⑨ 原子換檔不留暫存檔", g.read_text(encoding="utf-8") == good and not list((root / "pkg").glob("*.via_tmp")))
        install()
        chk("⑩ install 後本體 scan / fix / fix_one 都換上本版(唯讀動詞不受影響)",
            BODY["audit_source"] is cached_audit and BODY["fix"] is safe_fix and BODY["fix_one"] is not _ORIG_FIX_ONE)
        STATS.update(hit=0, miss=0)
        t0 = time.time()
        d1 = BODY["scan"](limit=150, progress=False)
        t1 = time.time()
        d2 = BODY["scan"](limit=150, progress=False)
        t2 = time.time()
        strip = lambda rows: sorted(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)  # noqa: E731
        chk("⑪ 真樹前 150 支:第二輪全走快取 · 結果與第一輪逐筆相同", STATS["hit"] >= 150 and strip(d1["rows"]) == strip(d2["rows"]),
            {"stats": STATS, "t1": round(t1 - t0, 2), "t2": round(t2 - t1, 2)})
        uninstall()
        d0 = BODY["scan"](limit=150, progress=False)
        chk("⑫ 不用快取的本體結果與快取版逐筆相同", strip(d0["rows"]) == strip(d1["rows"]))
        del os.environ["VIA_TOKEN_CACHE"]
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑬ 檔頭:加速器橋 · 網路橋在(__future__ 之後)· 不碰 TA-Lib",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    passed = rc_prior == 0 and all(ok)
    print("[計] %s %s 本版 %d/%d · 前版 %s · %s" % (_STEM, _V0118, sum(ok), len(ok), "PASS" if rc_prior == 0 else "FAIL", "PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
