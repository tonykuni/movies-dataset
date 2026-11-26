#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_GovernanceApply v0100 — 一支 Python 做完「全景診斷 → 參數解耦 → 同功能合併 → 雙橋 AST 注入 → 驗證」(VCGC 工具組裝)

操作員 2026-11-25:「1 全做 用 vcgc 工具完成 · one py code with supports of accelerating module and one ps to activate it」
(承接同日治理 prompt:Token-First · Zero-Rewrite · Modular SSOT;Step 0–5)。

本檔不另造引擎,每條車道都呼叫既有 VCGC 工具:
  net     VDF 網路工具橋缺件(CGC_MDL230 覆蓋矩陣 vdf_net.miss)→ 該家族尾版 +1 的薄尾,橋文取 CGC_MDL158 的 NET_BLOCK / ACCEL_BLOCK、
          求位用 CGC_MDL158 `_insert_after_header`(在 __future__ 之下);前版一字不動。
  accel   PY 加速器缺件(覆蓋矩陣 py_accel.miss)→ CGC_MDL158 `fix_one`(先乾跑,再落檔;AST + compile 過才算);
          收容夾(/intake/ · /references/)與 MDL158 名冊豁免照擋 = 灰(凍結來源不改)。
  param   VDF 現役引擎模組層寫死的輸入 / 輸出參數(名單 = 中央參數冊 PRMT 同名不同值的那些 + 任何本機絕對路徑字串)
          → 該家族尾版 +1 的新版:只把右值改成 `_VDF_PARAM("名", 原值)`(AST 定位,其餘位元組不動),
          值寫進 VDF 參數冊 `VDF_Unified_Params` 新版的 engine_params;預設 = 原值 → 零行為變更;
          本機路徑改成自 VIA 根解析(新檔不含本機路徑)。同名不同值不自動統一,只列在冊上的 harmonize_proposals。
  retire  同功能多份:`_sha` 分身(同夾有正名家族、家族各版公開名稱聯集 ⊇ 分身公開名稱、沒有程式點名)與內容逐位元相同的分身
          → VCGC 中樞的退役閘(先在編號冊 / 元件冊標退役 → worktree 前後 VCGC 指標不變差的證明 → 以搬代刪,RETIRE_MANIFEST 可找回)。
  ps      PS 加速器缺件:只驗(PS 檔由人出新版號,本檔不寫 .ps1)。
動詞:
  plan                    唯讀:五條車道各列 應做 / 可做 / 略過(三數)與理由;寫 VIA_Reports/vcgc_gov/GOV_PLAN_latest.json
  apply [--lanes a,b]     依序 retire → net → accel → param → verify;每檔先在 TEMP 過 ast.parse + compile,落檔後實跑,不過就還原
  verify                  重跑覆蓋矩陣 · 新版自測 · ReworkGuard check · 編號稽核,出雙色矩陣報告
  selftest                暫存夾造資料自測(不吃本機狀態、零網路)
資料不離開本機;零網路;不讀寫同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT);不碰 TA-Lib;不改 .ps1;不改凍結來源。
跨系統:本檔是 VCGC 工具,param / net / retire 會寫 VDF 的檔與冊 —— 依操作員 2026-11-25「全做 用 vcgc 工具完成」;報告逐檔點名。
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

import ast
import collections
import contextlib
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

TAG = "VIA_GovernanceApply v0100"
HERE = Path(__file__).resolve().parent
LANES = ("retire", "net", "accel", "param", "ps")
FROZEN_PARTS = ("/intake/", "/references/", "/VIA_RetiredEngines/", "/vrn2_release_")
DRIVE_RX = re.compile(r"^[A-Za-z]:\\")
SHADOW_RX = re.compile(r"^(?P<base>.+?)_sha[0-9a-f]{6,}$")
VER_RX = re.compile(r"_v(\d{4})$")
PARAM_FALLBACK = ("BASE_DIR", "BATCH_SIZE", "DUCKDB_FILENAME", "END_DATE", "HTTP_TIMEOUT", "HTTP_USER_AGENT", "MARKETS",
                  "MAX_BACKUP_FILES", "OUTPUT_DIR", "OUTPUT_JSON", "PROJECT_NAME", "RETRY_DELAY", "START_DATE",
                  "THREADPOOL_WORKERS", "TWSE_LISTING_URL", "TW_BLOOMBERG_REGEX", "TW_TICKER_REGEX", "TW_YFINANCE_REGEX",
                  "UNIVERSE_SOURCE", "YF_BATCH_SIZE", "YF_HISTORY_PERIOD", "YF_TIMEOUT")
PARAM_SKIP_NAMES = {"VERSION", "__version__"}


def find_via(start: Path | None = None) -> Path:
    env = os.environ.get("VIA_CODE_ROOT", "")
    if env and (Path(env) / "supportive modules").is_dir():
        return Path(env).resolve()
    p = (start or HERE).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    raise SystemExit(f"[{TAG}] 找不到 VIA 根(含 supportive modules 與 functional modules 的夾);請在倉內執行或設 VIA_CODE_ROOT")


def _vnum(p) -> int:
    m = VER_RX.search(Path(p).stem)
    return int(m.group(1)) if m else -1


def tail_of(folder: Path, stem: str) -> Path | None:
    vs = [p for p in folder.glob(stem + "_v*.py") if VER_RX.search(p.stem) and p.stem[: -6] == stem]
    if vs:
        return max(vs, key=_vnum)
    base = folder / (stem + ".py")
    return base if base.exists() else None


def family_of(p: Path) -> str:
    return VER_RX.sub("", p.stem)


def next_version_path(tail: Path) -> Path:
    n = max(_vnum(tail), -1) + 1
    n = max(n, 100)
    return tail.with_name(f"{family_of(tail)}_v{n:04d}.py")


def norm_sha(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def rel(via: Path, p: Path) -> str:
    return p.resolve().relative_to(via.resolve()).as_posix()


def frozen(relpath: str) -> bool:
    r = "/" + relpath.replace("\\", "/")
    return any(x in r for x in FROZEN_PARTS)


_MODS: dict = {}


def load_module(path: Path, name: str):
    key = str(path)
    if key not in _MODS:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        with contextlib.redirect_stdout(sys.stderr):
            spec.loader.exec_module(mod)
        _MODS[key] = mod
    return _MODS[key]


def registry_tail(via: Path, family: str) -> Path | None:
    return tail_of(via / "supportive modules" / "registry", family)


def mdl158(via: Path):
    """CGC_MDL158 鎖冊那一支(= token 卡上的路徑);鎖冊讀不到才退尾版。"""
    lock = via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    p = None
    try:
        lp = json.loads(lock.read_text(encoding="utf-8"))["token"]["path"]
        p = (via.parent / lp) if not Path(lp).is_absolute() else Path(lp)
        if not p.exists():
            p = via / Path(lp).name if (via / Path(lp).name).exists() else None
    except Exception:
        p = None
    p = p if p and p.exists() else registry_tail(via, "CGC_MDL158_VIAPanoramaAuditRepair")
    return load_module(p, "gov_mdl158")


def blocks(via: Path) -> tuple[str, str]:
    m = mdl158(via)
    return m.ACCEL_BLOCK, m.NET_BLOCK


def insert_after_header(via: Path, src: str, block: str) -> str:
    return mdl158(via)._insert_after_header(src, block)


class Heartbeat:
    """長跑心跳:子步驟至少每 25 秒印一行(CLAUDE.md:子行程每 30 秒內至少一行)。"""

    def __init__(self, label: str, every: float = 25.0):
        self.label, self.every, self.t0 = label, every, time.time()
        self._stop = threading.Event()
        self._th = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.wait(self.every):
            print(f"  [心跳] {self.label} · {time.time() - self.t0:.0f}s", flush=True)

    def __enter__(self):
        self._th.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._th.join(timeout=2)


def run(cmd: list, cwd: Path, timeout: int = 900, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)                      # 同意閘只由操作員在安裝 / 擷取閘子行程裡設;本工具不帶
    env.update(env_extra or {})
    try:
        return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or "", (exc.stderr or "") + "\n[逾時]")


def compiles(src: str, name: str) -> str:
    """空字串 = ast.parse 與 compile 都過;否則回原因。"""
    try:
        ast.parse(src)
        compile(src, name, "exec")
    except SyntaxError as exc:
        return f"SyntaxError 行 {exc.lineno}: {exc.msg}"
    except Exception as exc:              # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"
    return ""


def atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + f".gov_{os.getpid()}.sdd_tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    if tmp.stat().st_size == 0:
        tmp.unlink()
        raise RuntimeError(f"暫存檔是空的:{tmp}")
    os.replace(tmp, path)


# ── 覆蓋矩陣(CGC_MDL230)─────────────────────────────────────────────
def coverage(via: Path, fresh: bool = True) -> dict:
    out = via / "VIA_Reports" / "toolprobe" / "COVERAGE_MATRIX_latest.json"
    if fresh:
        t = registry_tail(via, "CGC_MDL230_ToolCoverageProbe")
        with Heartbeat("CGC_MDL230 覆蓋矩陣"):
            r = run([sys.executable, str(t), "matrix", "--no-pwsh"], via, 900, {"VIA_FROM_VCGC": "YES"})
        if r.returncode not in (0, 1, 2) and not out.exists():
            return {"error": f"CGC_MDL230 rc {r.returncode}", "totals": {}}
    try:
        return json.loads(out.read_text(encoding="utf-8"))
    except Exception as exc:              # noqa: BLE001
        return {"error": f"讀不到覆蓋矩陣:{type(exc).__name__}", "totals": {}}


def miss_of(cov: dict, side: str) -> list[str]:
    return list(((cov.get("totals") or {}).get(side) or {}).get("miss") or [])


# ── 車道 net:VDF 網路工具橋 ───────────────────────────────────────────
THIN_TAIL = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""{family} {vtag} — 薄尾(前版 {prior_name} 一字不動):補 VDF 網路工具橋(VDF 全件 100%)

產生:{tool}(操作員 2026-11-25「全做 用 vcgc 工具完成」;覆蓋矩陣 CGC_MDL230 vdf_net 缺件)。
橋文與求位取 CGC_MDL158(NET_BLOCK / ACCEL_BLOCK · `_insert_after_header`);惰性載入 = import 時零網路、零行為變更。
其餘一切照前版(`__getattr__` 轉接;main 轉前版;--selftest = 前版自測 + 雙橋檢)。
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "{family}"
TAG = "{family} {vtag}"


def _vnum(p) -> int:
    m = re.search(r"_v(\\d{{4}})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_{vtag}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:200]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 3 項 + 前版 %s 自測 · 零網路)" % (TAG, PRIOR_PATH.name), flush=True)
    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 0
    chk("T1 前版自測照過(rc 0)", rc == 0, rc)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("T2 雙橋在 __future__ 之下(ACCEL + NET 標記)", text.index("[VIA:ACCEL-BRIDGE:v0100]") > text.index("from __future__")
        and "[VIA:NET-BRIDGE:v0100]" in text)
    chk("T3 網路工具惰性載入:找得到統包網路工具(import 時零網路)", VIA_NET_TOOL_PATH is not None and callable(_via_net), VIA_NET_TOOL_PATH)
    print("[計] %s 自測 %d/%d %s" % (TAG, sum(ok), len(ok), "PASS" if all(ok) else "FAIL"), flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args) if callable(getattr(PRIOR, "main", None)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_thin_tail(via: Path, tail: Path, new: Path) -> str:
    accel, net = blocks(via)
    src = THIN_TAIL.format(family=family_of(tail), vtag=f"v{_vnum(new):04d}", prior_name=tail.name, tool=TAG)
    src = insert_after_header(via, src, net.rstrip("\n"))
    return insert_after_header(via, src, accel.rstrip("\n"))


def plan_net(via: Path, cov: dict) -> dict:
    items, skipped = [], []
    for r in miss_of(cov, "vdf_net"):
        p = via / r
        fam = family_of(p)
        tail = tail_of(p.parent, fam)
        if frozen(r):
            skipped.append([r, "凍結 / 收容來源不改(灰)"])
        elif tail is None or tail.resolve() != p.resolve():
            skipped.append([r, f"不是家族尾版(尾版 {tail.name if tail else '—'});尾版已有橋就不補舊版"])
        elif _vnum(p) < 0:
            skipped.append([r, "未帶版號的本體:先由該系統出第一個版號再補(不猜)"])
        else:
            items.append({"file": r, "new": rel(via, next_version_path(p))})
    return {"lane": "net", "should": len(items) + len(skipped), "can": len(items), "skipped": skipped, "items": items}


def apply_net(via: Path, plan: dict) -> list[dict]:
    out = []
    for it in plan["items"]:
        tail, new = via / it["file"], via / it["new"]
        res = {"file": it["file"], "new": it["new"]}
        if new.exists():
            out.append({**res, "state": "SKIP", "why": "新版號已存在"})
            continue
        src = build_thin_tail(via, tail, new)
        why = compiles(src, new.name)
        if why:
            out.append({**res, "state": "FAIL", "why": "TEMP 檢不過:" + why})
            continue
        atomic_write_text(new, src)
        r = run([sys.executable, str(new), "--selftest"], new.parent, 600)
        if r.returncode != 0:
            new.unlink()
            out.append({**res, "state": "FAIL", "why": f"自測 rc {r.returncode} → 已還原", "log": (r.stdout + r.stderr)[-600:]})
        else:
            out.append({**res, "state": "OK", "why": next((ln for ln in r.stdout.splitlines()[::-1] if "自測" in ln), "")[:120]})
    return out


# ── 車道 accel:CGC_MDL158 fix_one ────────────────────────────────────
def plan_accel(via: Path, cov: dict) -> dict:
    m = mdl158(via)
    items, skipped = [], []
    for r in miss_of(cov, "py_accel"):
        ex = m.template_exempt(r) if hasattr(m, "template_exempt") else ""
        if frozen(r):
            skipped.append([r, "收容夾 / 凍結來源不改(灰,豁免)"])
        elif ex:
            skipped.append([r, "CGC_MDL158 名冊豁免:" + ex[:60]])
        else:
            items.append({"file": r})
    return {"lane": "accel", "should": len(items) + len(skipped), "can": len(items), "skipped": skipped, "items": items}


def apply_accel(via: Path, plan: dict) -> list[dict]:
    m = mdl158(via)
    out = []
    for it in plan["items"]:
        p = via / it["file"]
        orig = p.read_bytes()
        dry = m.fix_one(it["file"], {"ACCEL"}, False)
        if "ACCEL" not in dry.get("applied", []):
            out.append({**it, "state": "SKIP", "why": dry.get("why") or str(dry.get("skipped"))[:100]})
            continue
        res = m.fix_one(it["file"], {"ACCEL"}, True)
        why = compiles(p.read_text(encoding="utf-8"), p.name)
        if why or not res.get("ok"):
            p.write_bytes(orig)
            out.append({**it, "state": "FAIL", "why": "落檔後檢不過 → 已還原:" + (why or res.get("why", ""))})
        else:
            out.append({**it, "state": "OK", "why": f"CGC_MDL158 fix_one ACCEL · +{res.get('bytes_delta', 0)} B"})
    return out


# ── 車道 param:參數解耦 ───────────────────────────────────────────────
PARAM_BLOCK = '''# ===== [VIA:GOV-PARAM:v0100] 參數解耦橋(值在 VDF_Unified_Params 尾版 engine_params;缺冊 / 缺鍵 = 原值,零行為變更) =====
_VDF_GOV_FAMILY = "{family}"
_VDF_GOV_BOOK = None


def _VDF_VIA_ROOT_REL(rel):
    """本機路徑改自 VIA 根解析:環境變數 VIA_ROOT(資料根)先,再往上找含 supportive modules 的程式根。"""
    import os as _gp_os
    from pathlib import Path as _gp_P
    roots = [_gp_P(_gp_os.environ["VIA_ROOT"])] if _gp_os.environ.get("VIA_ROOT") else []
    _gp_p = _gp_P(__file__).resolve()
    while _gp_p.parent != _gp_p:
        if (_gp_p / "supportive modules").is_dir():
            roots.append(_gp_p)
            break
        _gp_p = _gp_p.parent
    for _gp_r in roots:
        if (_gp_r / rel).exists():
            return str(_gp_r / rel)
    return str((roots[-1] if roots else _gp_P(__file__).resolve().parent) / rel)


def _VDF_PARAM(name, default):
    """讀 VDF 參數冊尾版 engine_params[家族][名];讀不到 = 原值(誠實:不補 0、不編值)。"""
    global _VDF_GOV_BOOK
    try:
        if _VDF_GOV_BOOK is None:
            import json as _gp_json
            from pathlib import Path as _gp_P
            _gp_here = _gp_P(__file__).resolve().parent
            _gp_hits = sorted({{q for d in (_gp_here, _gp_here.parent) for q in d.glob("VDF_Unified_Params_v*.json")}}, key=lambda q: q.name)
            _VDF_GOV_BOOK = ((_gp_json.loads(_gp_hits[-1].read_text(encoding="utf-8")).get("engine_params") or {{}})
                             .get(_VDF_GOV_FAMILY) or {{}}) if _gp_hits else {{}}
        ent = _VDF_GOV_BOOK.get(name)
        if not isinstance(ent, dict):
            return default
        if "via_root_rel" in ent:
            return _VDF_VIA_ROOT_REL(ent["via_root_rel"])
        if "regex" in ent:
            import re as _gp_re
            return _gp_re.compile(ent["regex"])
        if "value" not in ent:
            return default
        v = ent["value"]
        return type(default)(v) if isinstance(default, (tuple, frozenset, set)) and isinstance(v, list) else v
    except Exception:
        return default
# ===== [VIA:GOV-PARAM:END] ====='''


def prmt_names(via: Path) -> set[str]:
    """中央參數冊 PRMT:同名出現在多支模組且值不同的名(= SDD X-PARAM 的「值不同」)。冊讀不到退內建清單。"""
    books = sorted((via / "supportive modules" / "registry" / "VIA_NumberBooks").glob("VIA_NumberBook_PRMT_v*.jsonl"), key=_vnum)
    if not books:
        return set(PARAM_FALLBACK)
    by = collections.defaultdict(set)
    cnt = collections.Counter()
    for ln in books[-1].read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("gone_since"):
            continue
        by[r.get("name")].add(str(r.get("note")))
        cnt[r.get("name")] += 1
    names = {k for k, v in by.items() if cnt[k] > 1 and len(v) > 1 and k}
    return (names or set(PARAM_FALLBACK)) - PARAM_SKIP_NAMES


def _literal(node: ast.AST):
    """回 (種類, 值):value / regex / drive;取不到回 None。"""
    try:
        v = ast.literal_eval(node)
    except Exception:
        v = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "compile" \
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "re" and len(node.args) == 1 and not node.keywords \
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            return ("regex", node.args[0].value)
        return None
    if isinstance(v, str) and DRIVE_RX.match(v):
        return ("drive", v)
    norm = list(v) if isinstance(v, (tuple, set, frozenset)) else v
    try:
        if json.loads(json.dumps(norm)) != norm:
            return None
    except (TypeError, ValueError):
        return None
    return ("value", norm)


def drive_rel(v: str) -> str:
    parts = re.split(r"[\\/]+", v)
    low = [x.lower() for x in parts]
    if "veritasintelligenceanalytics" in low:
        i = len(low) - 1 - low[::-1].index("veritasintelligenceanalytics")
        return "/".join(parts[i + 1:])
    return "/".join(parts[3:]) if len(parts) > 3 else parts[-1]


def _byte_offsets(src: str) -> list[int]:
    offs, acc = [0], 0
    for line in src.encode("utf-8").splitlines(keepends=True):
        acc += len(line)
        offs.append(acc)
    return offs


def rewrite_params(src: str, names: set[str]) -> tuple[str, dict, list]:
    """只換模組層賦值的右值;回 (新原文, engine_params 條目, 略過清單)。AST col 是 UTF-8 位元組 → 以位元組切。"""
    tree = ast.parse(src)
    offs = _byte_offsets(src)
    data = src.encode("utf-8")
    edits, entries, skipped = [], {}, []
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        nm = node.targets[0].id
        lit = _literal(node.value)
        is_drive = bool(lit and lit[0] == "drive")
        if nm not in names and not is_drive:
            continue
        if nm in PARAM_SKIP_NAMES:
            continue
        if lit is None:
            skipped.append([nm, node.lineno, "右值不是字面值(運算式;保留原樣,不猜)"])
            continue
        a = offs[node.value.lineno - 1] + node.value.col_offset
        b = offs[node.value.end_lineno - 1] + node.value.end_col_offset
        orig = data[a:b].decode("utf-8")
        kind, val = lit
        if kind == "drive":
            rl = drive_rel(val)
            default = f"_VDF_VIA_ROOT_REL({json.dumps(rl, ensure_ascii=False)})"
            entries[nm] = {"via_root_rel": rl, "was": "本機絕對路徑(已改為自 VIA 根解析;原文不入冊)", "line": node.lineno}
        elif kind == "regex":
            default = orig
            entries[nm] = {"regex": val, "line": node.lineno}
        else:
            default = orig
            entries[nm] = {"value": val, "line": node.lineno}
        edits.append((a, b, f"_VDF_PARAM({json.dumps(nm)}, {default})".encode("utf-8")))
    for a, b, rep in sorted(edits, reverse=True):
        data = data[:a] + rep + data[b:]
    return data.decode("utf-8"), entries, skipped


def _vdf_tails(via: Path) -> list[Path]:
    root = via / "functional modules" / "VDF"
    fams: dict = {}
    for p in sorted(list(root.glob("*.py")) + list((root / "engine").glob("*.py"))):
        if SHADOW_RX.match(p.stem) or p.name.startswith("VRN_") or frozen(rel(via, p)):
            continue
        fams.setdefault((p.parent, family_of(p)), []).append(p)
    out = []
    for (d, fam), _ps in fams.items():
        t = tail_of(d, fam)
        if t is not None:
            out.append(t)
    return out


def plan_param(via: Path) -> dict:
    names = prmt_names(via)
    items, skipped = [], []
    locs = collections.defaultdict(set)
    for t in _vdf_tails(via):
        locs[family_of(t)].add(t.parent)
    for t in _vdf_tails(via):
        src = t.read_text(encoding="utf-8", errors="replace")
        if "[VIA:GOV-PARAM:v0100]" in src:
            continue
        try:
            new_src, ent, sk = rewrite_params(src, names)
        except SyntaxError as exc:
            skipped.append([rel(via, t), f"原檔語法錯(行 {exc.lineno}),不動"])
            continue
        if not ent:
            continue
        fam = family_of(t)
        other = [d for d in locs[fam] if d != t.parent]
        if other and _vnum(t) < 0 and any(tail_of(d, fam) and _vnum(tail_of(d, fam)) >= 0 for d in other):
            skipped.append([rel(via, t), f"同名家族在 {rel(via, other[0])} 有版號本體;這份是未帶版號的另一位置副本(不另開同名版號,避免撞號)"])
            continue
        items.append({"file": rel(via, t), "family": fam, "new": rel(via, next_version_path(t)), "params": sorted(ent),
                      "drive": sorted(k for k, v in ent.items() if "via_root_rel" in v), "kept_expr": sk})
    return {"lane": "param", "should": len(items) + len(skipped), "can": len(items), "skipped": skipped, "items": items,
            "names": sorted(names)}


def build_param_version(via: Path, tail: Path, new: Path, names: set[str]) -> tuple[str, dict]:
    src = tail.read_text(encoding="utf-8")
    new_src, ent, _sk = rewrite_params(src, names)
    head = (f"# [VIA:GOV-PARAM:v0100] {family_of(tail)} v{_vnum(new):04d} = {tail.name} 全文 + 參數解耦"
            f"(產生:{TAG};操作員 2026-11-25「全做」):模組層 {len(ent)} 個參數改讀 VDF 參數冊 engine_params,預設 = 原值;"
            f"本機路徑改自 VIA 根解析。其餘位元組與前版相同。\n")
    lines = new_src.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#!") or lines[i].startswith("# -*-") or lines[i].startswith("# coding")):
        i += 1
    new_src = "".join(lines[:i]) + head + "".join(lines[i:])
    new_src = insert_after_header(via, new_src, PARAM_BLOCK.format(family=family_of(tail)))
    accel, net = blocks(via)
    if "[VIA:NET-BRIDGE" not in new_src:
        new_src = insert_after_header(via, new_src, net.rstrip("\n"))
    if "[VIA:ACCEL-BRIDGE" not in new_src and "VIA_SuperAccel_Module" not in new_src:
        new_src = insert_after_header(via, new_src, accel.rstrip("\n"))
    return new_src, ent


def params_book(via: Path) -> Path:
    root = via / "functional modules" / "VDF"
    return max(root.glob("VDF_Unified_Params_v*.json"), key=lambda q: _vnum(q.with_suffix(".py")))


def harmonize_proposals(via: Path, names: set[str]) -> dict:
    books = sorted((via / "supportive modules" / "registry" / "VIA_NumberBooks").glob("VIA_NumberBook_PRMT_v*.jsonl"), key=_vnum)
    out = collections.defaultdict(collections.Counter)
    if books:
        for ln in books[-1].read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln)
                if r.get("name") in names and not r.get("gone_since"):
                    v = str(r.get("note"))
                    out[r["name"]]["<本機路徑>" if DRIVE_RX.match(v.strip("'r\"")) or "\\\\Users\\\\" in v else v[:80]] += 1
    return {k: {"values_seen": dict(c), "state": "proposed(未套用:同名不同值不自動統一,操作員裁定後由 VDF 出新版)"}
            for k, c in sorted(out.items())}


def _compare_script() -> str:
    return r'''
import importlib.util, json, sys, re
def load(p, n):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
names = json.loads(sys.argv[3]); out = {}
try:
    a = load(sys.argv[1], "gov_cmp_old"); b = load(sys.argv[2], "gov_cmp_new")
except Exception as exc:
    print(json.dumps({"import": type(exc).__name__ + ": " + str(exc)[:160]})); raise SystemExit(0)
for n in names:
    x, y = getattr(a, n, None), getattr(b, n, None)
    if isinstance(x, re.Pattern): x = x.pattern
    if isinstance(y, re.Pattern): y = y.pattern
    out[n] = (x == y)
print(json.dumps({"import": "", "same": out}))
'''


def apply_param(via: Path, plan: dict) -> tuple[list[dict], dict]:
    names = set(plan["names"])
    out, all_ent = [], {}
    staged = []
    for it in plan["items"]:
        tail, new = via / it["file"], via / it["new"]
        if new.exists():
            out.append({**it, "state": "SKIP", "why": "新版號已存在"})
            continue
        src, ent = build_param_version(via, tail, new, names)
        why = compiles(src, new.name)
        if why:
            out.append({**it, "state": "FAIL", "why": "TEMP 檢不過:" + why})
            continue
        staged.append((it, tail, new, src, ent))
        all_ent[it["family"]] = {k: v for k, v in ent.items()}
    book_rel = ""
    if staged:
        old = params_book(via)
        book = json.loads(old.read_text(encoding="utf-8"))
        ep = dict(book.get("engine_params") or {})
        ep.update(all_ent)
        nb = old.with_name(re.sub(r"_v\d{4}\.json$", f"_v{_vnum(old.with_suffix('.py')) + 1:04d}.json", old.name))
        book.update({"schema": book.get("schema", "VDF.UnifiedParams"),
                     "engine_params_note": ("各引擎模組層參數的正本(VIA_GovernanceApply v0100 解耦;引擎新版以 _VDF_PARAM(名, 原值) 讀這裡,"
                                            "缺冊 / 缺鍵 = 原值)。via_root_rel = 自 VIA 根解析的相對路徑;regex = 正規式字串。"),
                     "engine_params": ep,
                     "harmonize_proposals": harmonize_proposals(via, names)})
        atomic_write_text(nb, json.dumps(book, ensure_ascii=False, indent=1) + "\n")
        book_rel = rel(via, nb)
    for it, tail, new, src, ent in staged:
        atomic_write_text(new, src)
        cmp_names = [k for k, v in ent.items() if "via_root_rel" not in v]
        r = run([sys.executable, "-c", _compare_script(), str(tail), str(new), json.dumps(cmp_names)], new.parent, 180)
        try:
            res = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
        except ValueError:
            res = {"import": f"rc {r.returncode}"}
        if res.get("import"):
            r2 = run([sys.executable, "-c", f"import importlib.util as u,sys;s=u.spec_from_file_location('o',{str(tail)!r});"
                                         f"m=u.module_from_spec(s);s.loader.exec_module(m)"], new.parent, 180)
            if r2.returncode == 0:
                new.unlink()
                out.append({**it, "state": "FAIL", "why": "前版載得起來、新版載不起來 → 已還原:" + res["import"]})
            else:
                out.append({**it, "state": "OK-容器", "why": "新舊版在容器都載不起來(缺依賴,同因)→ 只驗到 ast + compile:" + res["import"][:80]})
            continue
        diff = [k for k, same in (res.get("same") or {}).items() if not same]
        if diff:
            new.unlink()
            out.append({**it, "state": "FAIL", "why": f"參數值跟前版不同 {diff} → 已還原"})
        else:
            out.append({**it, "state": "OK", "why": f"參數 {len(ent)} 個改讀冊 · 值與前版相同 {len(cmp_names)}/{len(cmp_names)}"
                                                 + (f" · 本機路徑改自 VIA 根解析 {it['drive']}" if it["drive"] else "")})
    if book_rel and not any(o["state"].startswith("OK") for o in out):
        (via / book_rel).unlink()
        book_rel = ""
    return out, {"book": book_rel, "families": sorted(all_ent)}


# ── 車道 retire:同功能分身 → VCGC 中樞退役閘 ─────────────────────────
def public_names(p: Path) -> set[str]:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
            out.add(n.name)
        if isinstance(n, ast.ClassDef):
            out |= {f"{n.name}.{m.name}" for m in n.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_")}
    return out


def code_refs(via: Path, stems: list[str]) -> dict:
    """程式(.py / .ps1)點名:位元組掃(凍結 / 收容 / 封存 / 分身自己不算)。"""
    hits = {s: [] for s in stems}
    keys = [(s, s.encode()) for s in stems]
    for p in list(via.rglob("*.py")) + list(via.rglob("*.ps1")):
        r = rel(via, p)
        if frozen(r) or "/VIA_Reports/" in "/" + r or SHADOW_RX.match(p.stem):
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        for s, b in keys:
            if b in data:
                hits[s].append(r)
    return hits


def plan_retire(via: Path, systems: tuple = ("VDF",)) -> dict:
    """systems = 這次授權搬的系統夾(預設 VDF:操作員 2026-11-25 點名 VDF 分身 + 放在 VDF 夾的 MDL253);其他系統的候選只列不動。"""
    items, skipped, cands = [], [], []
    for sysdir in ("VDF", "VRN"):
        root = via / "functional modules" / sysdir
        shadows = [p for p in sorted(root.glob("*.py")) if SHADOW_RX.match(p.stem)]
        by_sha = collections.defaultdict(list)
        for p in shadows:
            by_sha[norm_sha(p.read_bytes())].append(p)
        for p in shadows:
            base = SHADOW_RX.match(p.stem).group("base")
            same = sorted(by_sha[norm_sha(p.read_bytes())], key=lambda q: q.name)
            if len(same) > 1 and same[0] != p:
                cands.append((p, f"內容與 {same[0].name} 逐位元相同(LF 正規化 sha256)", base))
                continue
            fam = [q for q in root.glob(base + "*.py") if not SHADOW_RX.match(q.stem) and family_of(q) == base]
            if not fam:
                skipped.append([rel(via, p), "唯一實作(同夾沒有正名家族)→ 留(只增不減)"])
                continue
            union = set().union(*(public_names(q) for q in fam))
            miss = public_names(p) - union
            if miss:
                skipped.append([rel(via, p), f"家族缺它的公開名稱 {sorted(miss)[:3]} → 留(合併要先出家族新版)"])
                continue
            cands.append((p, f"家族 {base} {len(fam)} 版公開名稱聯集涵蓋它({len(public_names(p))} 個)", base))
    refs = code_refs(via, [p.stem for p, _w, _b in cands])
    for p, why, base in cands:
        if p.parent.name not in systems:
            skipped.append([rel(via, p), f"候選({why[:40]})· {p.parent.name} 系統自己的分身 → 範圍外,交該系統管理器(不動)"])
        elif refs.get(p.stem):
            skipped.append([rel(via, p), f"程式點名 {refs[p.stem][:2]} → 先遷引用(不搬)"])
        else:
            items.append({"path": rel(via, p), "dir": rel(via, p.parent), "family": base, "v": "shadow", "why": why})
    return {"lane": "retire", "should": len(items) + len(skipped), "can": len(items), "skipped": skipped, "items": items}


def hub(via: Path):
    t = max(via.glob("VCGC_CommandHub_v*.py"), key=_vnum)
    return load_module(t, "gov_hub")


def apply_retire(via: Path, plan: dict) -> list[dict]:
    if not plan["items"]:
        return []
    h = hub(via)
    paths = [it["path"] for it in plan["items"]]
    st = run(["git", "status", "--porcelain", "--", *paths], via, 60)
    if st.stdout.strip():
        return [{**it, "state": "FAIL", "why": "工作樹上這些檔有未提交變更(證明用 HEAD 的 worktree)→ 先提交"} for it in plan["items"]]
    logs = []

    def log(msg):
        logs.append(msg)
        print("  " + str(msg), flush=True)

    with Heartbeat("退役證明(worktree 前後 VCGC 指標)"):
        pv = h.prune_prove(via, plan["items"], log=log)
    proven = {x["path"] for x in pv.get("proven", [])}
    out = []
    if proven:
        with Heartbeat("退役搬移(主樹前後 VCGC 指標)"):
            ap = h.prune_apply(via, pv["proven"])
        for it in plan["items"]:
            if it["path"] in proven and ap.get("moved"):
                out.append({**it, "state": "OK", "why": f"標退役 → 證過 → 搬到 {ap['dest']}(RETIRE_MANIFEST 可找回)"})
            elif it["path"] in proven:
                out.append({**it, "state": "FAIL", "why": f"主樹搬後指標變差 → 整批還原 {ap.get('worse')}"})
            else:
                out.append({**it, "state": "FAIL", "why": "證明沒過(牽連 / 指標變差)→ 不搬"})
    else:
        out = [{**it, "state": "FAIL", "why": f"證明沒過:失敗 {pv.get('failed', [])[:2]} · 變差 {pv.get('worse')}"} for it in plan["items"]]
    return out


# ── 車道 ps:只驗 ───────────────────────────────────────────────────────
def plan_ps(via: Path, cov: dict) -> dict:
    items, skipped = [], []
    for r in miss_of(cov, "ps_accel"):
        p = via / r
        m = re.match(r"(.+)_v(\d{4})\.ps1$", p.name)
        newer = []
        if m:
            newer = [q for q in p.parent.glob(m.group(1) + "_v*.ps1")
                     if int(re.search(r"_v(\d{4})\.ps1$", q.name).group(1)) > int(m.group(2)) and b"PS-ACCEL" in q.read_bytes()]
        if newer:
            skipped.append([r, f"已有新版 {sorted(q.name for q in newer)[-1]} 帶 PS-ACCEL(下次覆蓋矩陣取尾版即綠)"])
        else:
            items.append({"file": r, "why": "PS 檔由人出新版號帶 PS-ACCEL 橋(本工具不寫 .ps1)"})
    return {"lane": "ps", "should": len(items) + len(skipped), "can": 0, "skipped": skipped, "items": items}


# ── 總控 ───────────────────────────────────────────────────────────────
def build_plan(via: Path, lanes: tuple, fresh_cov: bool = True) -> dict:
    t0 = time.time()
    cov = coverage(via, fresh_cov) if {"net", "accel", "ps"} & set(lanes) else {"totals": {}}
    plan = {"tool": TAG, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "via": via.name,
            "coverage_before": {k: {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                                for k, v in (cov.get("totals") or {}).items()},
            "lanes": {}}
    fn = {"retire": lambda: plan_retire(via), "net": lambda: plan_net(via, cov), "accel": lambda: plan_accel(via, cov),
          "param": lambda: plan_param(via), "ps": lambda: plan_ps(via, cov)}
    for ln in LANES:
        if ln in lanes:
            plan["lanes"][ln] = fn[ln]()
    plan["secs"] = round(time.time() - t0, 1)
    return plan


def lamp_of(lane: dict, results: list | None) -> str:
    if results is None:
        return "YELLOW" if lane["can"] or lane["items"] else ("GRAY" if lane["skipped"] else "GREEN")
    if any(r["state"] == "FAIL" for r in results):
        return "RED"
    if any(r["state"] != "OK" for r in results) or lane["skipped"] and lane["lane"] != "retire":
        return "YELLOW"
    return "GREEN"


def report(via: Path, plan: dict, results: dict | None, extra: dict | None = None) -> dict:
    rows = []
    for ln, lane in plan["lanes"].items():
        res = (results or {}).get(ln)
        done = sum(1 for r in res if r["state"].startswith("OK")) if res is not None else 0
        rows.append({"lane": ln, "lamp": lamp_of(lane, res), "should": lane["should"], "can": lane["can"], "done": done,
                     "skipped": len(lane["skipped"])})
    rep = {**plan, "results": results or {}, "rows": rows, **(extra or {})}
    out = via / "VIA_Reports" / "vcgc_gov"
    out.mkdir(parents=True, exist_ok=True)
    name = "GOV_APPLY_latest" if results is not None else "GOV_PLAN_latest"
    atomic_write_text(out / f"{name}.json", json.dumps(rep, ensure_ascii=False, indent=1) + "\n")
    icon = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "GRAY": "⚪"}
    lines = [f"[{TAG}] {'套用' if results is not None else '計畫(唯讀)'} · {plan['at']} · {plan['secs']}s"]
    lines.append(f"  {'燈':2} {'車道':7} {'應做':>4} {'可做':>4} {'已做':>4} {'略過':>4}")
    for r in rows:
        lines.append(f"  {icon[r['lamp']]} {r['lane']:7} {r['should']:>4} {r['can']:>4} {r['done']:>4} {r['skipped']:>4}")
    for ln, lane in plan["lanes"].items():
        for it in (results or {}).get(ln) or []:
            if it["state"] != "OK":
                tag = "[🔴 RED - CRITICAL ERROR]" if it["state"] == "FAIL" else "[🟡 YELLOW - AI FEEDBACK]"
                lines.append(f"  {tag} {ln} · {it.get('file') or it.get('path')} · {it['why'][:140]}")
        for f, why in lane["skipped"][:12]:
            lines.append(f"  [略過] {ln} · {f} · {why[:120]}")
        if len(lane["skipped"]) > 12:
            lines.append(f"  [略過] {ln} · 另 {len(lane['skipped']) - 12} 項(全文見 JSON)")
    for k, v in (extra or {}).items():
        lines.append(f"  [{k}] {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)[:300]}")
    atomic_write_text(out / f"{name}.txt", "\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    print(f"[報告] {rel(via, out / (name + '.json'))}", flush=True)
    return rep


def verify(via: Path, new_files: list[str]) -> dict:
    ex = {}
    st = []
    for f in new_files:
        p = via / f
        if p.suffix == ".py" and p.exists():
            r = run([sys.executable, str(p), "--selftest"], p.parent, 600)
            st.append(f"{p.name} rc {r.returncode}")
    ex["新版自測"] = " · ".join(st) or "—"
    cov = coverage(via, True)
    ex["覆蓋矩陣"] = {k: f"{v.get('have', '?')}/{v.get('n', v.get('total', '?'))} miss {len(v.get('miss') or [])}"
                    for k, v in (cov.get("totals") or {}).items()}
    rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
    if rg:
        with Heartbeat("ReworkGuard check"):
            r = run([sys.executable, str(rg[-1]), "check"], via, 900)
        ex["ReworkGuard"] = next((ln for ln in r.stdout.splitlines()[::-1] if ln.strip()), f"rc {r.returncode}")[:200]
    con = registry_tail(via, "CGC_MDL149_VeritasCentralGovernanceConsole")
    if con:
        with Heartbeat("CGC_MDL237 編號稽核"):
            r = run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], via, 900, {"VIA_FROM_VCGC": "YES"})
        ex["編號稽核"] = " | ".join(ln.strip() for ln in r.stdout.splitlines() if re.search(r"遺失|改身分|重號|XCODE|DUPREG", ln))[:300] or f"rc {r.returncode}"
    return ex


def cmd_apply(via: Path, lanes: tuple) -> int:
    print(f"[{TAG}] 套用 · 車道 {','.join(lanes)} · 先算計畫(唯讀)", flush=True)
    plan = build_plan(via, lanes)
    results, new_files, extra = {}, [], {}
    order = [ln for ln in ("retire", "net", "accel", "param") if ln in lanes]
    for ln in order:
        lane = plan["lanes"][ln]
        print(f"[{ln}] 應做 {lane['should']} · 可做 {lane['can']} · 略過 {len(lane['skipped'])}", flush=True)
        if not lane["items"]:
            results[ln] = []
            continue
        if ln == "retire":
            results[ln] = apply_retire(via, lane)
        elif ln == "net":
            results[ln] = apply_net(via, lane)
            new_files += [r["new"] for r in results[ln] if r["state"] == "OK"]
        elif ln == "accel":
            results[ln] = apply_accel(via, lane)
        elif ln == "param":
            results[ln], meta = apply_param(via, lane)
            new_files += [r["new"] for r in results[ln] if r["state"].startswith("OK")]
            if meta["book"]:
                extra["參數冊新版"] = meta["book"]
    if "ps" in lanes:
        results["ps"] = [{**it, "state": "TODO"} for it in plan["lanes"]["ps"]["items"]]
    extra.update(verify(via, new_files))
    extra["跨系統寫入"] = sorted({(r.get("new") or r.get("file") or r.get("path") or "").split("/")[1]
                              for v in results.values() for r in v if r["state"].startswith("OK") and "/" in (r.get("new") or r.get("file") or r.get("path") or "")})
    rep = report(via, plan, results, extra)
    bad = any(r["lamp"] == "RED" for r in rep["rows"])
    print("NEXT: " + ("看 [🔴] 行修好再跑 apply" if bad else "git add 新檔與冊 → ReworkGuard check --fetch-prs → 提交推送;編號等開著的 PR 併入後再發"), flush=True)
    return 1 if bad else 0


# ── 自測(暫存夾造資料;不吃本機狀態;零網路)─────────────────────────
FIX_MDL158 = r'''
ACCEL_BLOCK = """# ===== [VIA:ACCEL-BRIDGE:v0100] fx =====
try:
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
"""
NET_BLOCK = """# ===== [VIA:NET-BRIDGE:v0100] fx =====
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
    return None
# ===== [VIA:NET-BRIDGE:END] =====
"""
import ast
def template_exempt(rel):
    return "fx 名冊" if "TEMPLATE" in rel else ""
def _insert_after_header(src, block):
    tree = ast.parse(src); line = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            line = max(line, node.end_lineno or 0); continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            line = max(line, node.end_lineno or 0); continue
        break
    lines = src.splitlines(keepends=True)
    if line == 0:
        i = 0
        while i < len(lines) and lines[i].startswith("#"):
            i += 1
        line = i
    return "".join(lines[:line]) + "\n" + block + "\n" + "".join(lines[line:])
def fix_one(rel, classes, apply):
    from pathlib import Path
    p = Path(VIA) / rel; src = p.read_text(encoding="utf-8")
    res = {"file": rel, "applied": [], "skipped": [], "ok": True, "why": ""}
    if "ACCEL" in classes and "[VIA:ACCEL-BRIDGE" not in src:
        src = _insert_after_header(src, ACCEL_BLOCK); res["applied"].append("ACCEL")
    if apply and res["applied"]:
        p.write_text(src, encoding="utf-8")
    res["bytes_delta"] = 1
    return res
'''


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(8 項 · 暫存夾造資料 · 零網路)", flush=True)
    with tempfile.TemporaryDirectory(prefix="gov_st_") as td:
        via = Path(td) / "VIA"
        (via / "supportive modules" / "registry" / "VIA_NumberBooks").mkdir(parents=True)
        (via / "supportive modules" / "network").mkdir(parents=True)
        (via / "supportive modules" / "network" / "via_net_unified_v0101.py").write_text("X = 1\n", encoding="utf-8")
        vdf = via / "functional modules" / "VDF"
        (vdf / "engine").mkdir(parents=True)
        (via / "functional modules" / "VAP" / "intake" / "x").mkdir(parents=True)
        m158 = via / "supportive modules" / "registry" / "CGC_MDL158_VIAPanoramaAuditRepair_v0100.py"
        m158.write_text(f"VIA = {str(via)!r}\n" + FIX_MDL158, encoding="utf-8")
        _MODS.clear()
        rows = [{"name": "YF_TIMEOUT", "note": "15"}, {"name": "YF_TIMEOUT", "note": "20"}, {"name": "TW_TICKER_REGEX", "note": "a"},
                {"name": "TW_TICKER_REGEX", "note": "b"}, {"name": "SAME", "note": "1"}, {"name": "SAME", "note": "1"}]
        (via / "supportive modules" / "registry" / "VIA_NumberBooks" / "VIA_NumberBook_PRMT_v0100.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        chk("① 參數名單 = PRMT 同名不同值(同值不算)", prmt_names(via) == {"YF_TIMEOUT", "TW_TICKER_REGEX"}, prmt_names(via))

        eng = vdf / "VDF_MDL900_FxEngine_v0100.py"
        eng.write_text('#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""fx 引擎:中文說明。"""\nfrom __future__ import annotations\nimport re\n'
                       'BASE_DIR = r"' + "Z:" + "\\fx\\home\\VeritasIntelligenceAnalytics\\module\\VDF\\dict" + '"\n'
                       'YF_TIMEOUT = 15  # 中文註解\nTW_TICKER_REGEX = re.compile(r"^[1-9]\\d{3}$")\nOTHER = 7\n'
                       'DERIVED = BASE_DIR + "/x"\nYF_TUPLE = (1, 2)\n\n\ndef selftest():\n    return 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(selftest())\n',
                       encoding="utf-8")
        (vdf / "VDF_Unified_Params_v0102.json").write_text(json.dumps({"schema": "fx", "time": {"start_date": "2018-01-01"}}), encoding="utf-8")
        pl = plan_param(via)
        it = (pl["items"] or [{}])[0]
        chk("② 參數車道:抓到 BASE_DIR(本機路徑)· YF_TIMEOUT · TW_TICKER_REGEX;不動 OTHER", it.get("params") == ["BASE_DIR", "TW_TICKER_REGEX", "YF_TIMEOUT"]
            and it.get("drive") == ["BASE_DIR"] and it.get("new", "").endswith("VDF_MDL900_FxEngine_v0101.py"), it)
        res, meta = apply_param(via, pl)
        newp = vdf / "VDF_MDL900_FxEngine_v0101.py"
        txt = newp.read_text(encoding="utf-8") if newp.exists() else ""
        book = json.loads((vdf / "VDF_Unified_Params_v0103.json").read_text(encoding="utf-8")) if (vdf / "VDF_Unified_Params_v0103.json").exists() else {}
        chk("③ 新版落檔:值與前版相同、ast+compile 過、新檔不含本機路徑、冊 v0103 有 engine_params 且不含本機路徑",
            res and res[0]["state"] == "OK" and "Z:\\" not in txt and not compiles(txt, "x")
            and book.get("engine_params", {}).get("VDF_MDL900_FxEngine", {}).get("YF_TIMEOUT", {}).get("value") == 15
            and "fx\\\\home" not in json.dumps(book) and txt.index("[VIA:GOV-PARAM:v0100] 參數解耦橋") > txt.index("from __future__"), (res, meta))
        book["engine_params"]["VDF_MDL900_FxEngine"]["YF_TIMEOUT"]["value"] = 99
        (vdf / "VDF_Unified_Params_v0103.json").write_text(json.dumps(book), encoding="utf-8")
        r = run([sys.executable, "-c", "import importlib.util as u;s=u.spec_from_file_location('n',%r);m=u.module_from_spec(s);s.loader.exec_module(m);"
                 "print(m.YF_TIMEOUT, m.TW_TICKER_REGEX.pattern, m.BASE_DIR.replace(chr(92),'/').endswith('module/VDF/dict'))" % str(newp)], vdf, 60)
        chk("④ 引擎改讀冊:冊改 99 → 引擎讀到 99;正規式照冊編譯;本機路徑自 VIA 根解析", r.stdout.split() == ["99", "^[1-9]\\d{3}$", "True"],
            (r.stdout, r.stderr[-200:]))

        dp = vdf / "VDF_MDL901_FxPlane_v0100.py"
        dp.write_text('"""fx plane."""\nfrom __future__ import annotations\n\n\ndef selftest():\n    return 0\n\n\ndef main(argv=None):\n    return 0\n', encoding="utf-8")
        cov = {"totals": {"vdf_net": {"miss": [rel(via, dp), "functional modules/VAP/intake/x/a.py"]},
                          "py_accel": {"miss": ["functional modules/VAP/intake/x/a.py", "functional modules/VRN/t.py", "TEMPLATE/z.py"]},
                          "ps_accel": {"miss": []}}}
        pn = plan_net(via, cov)
        rn = apply_net(via, pn)
        tv = vdf / "VDF_MDL901_FxPlane_v0101.py"
        tt = tv.read_text(encoding="utf-8") if tv.exists() else ""
        tree = ast.parse(tt) if tt else ast.parse("")
        real_net = any(isinstance(n, ast.FunctionDef) and n.name == "_via_net" for n in tree.body) and \
            any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "VIA_NET_TOOL_PATH" for t in n.targets) for n in tree.body)
        chk("⑤ 網路橋車道:收容件略過;尾版出 v0101 薄尾、雙橋在 __future__ 下、AST 真橋、自測 rc 0",
            len(pn["items"]) == 1 and len(pn["skipped"]) == 1 and rn and rn[0]["state"] == "OK" and real_net
            and tt.index("[VIA:NET-BRIDGE:v0100]") > tt.index("from __future__"), (pn, rn))

        (via / "functional modules" / "VRN").mkdir(parents=True, exist_ok=True)
        (via / "functional modules" / "VRN" / "t.py").write_text('"""t."""\nX = 1\n', encoding="utf-8")
        pa = plan_accel(via, cov)
        ra = apply_accel(via, pa)
        chk("⑥ 加速器車道:收容夾與名冊豁免略過;其餘經 CGC_MDL158 fix_one 落檔且 compile 過",
            [i["file"] for i in pa["items"]] == ["functional modules/VRN/t.py"] and len(pa["skipped"]) == 2 and ra and ra[0]["state"] == "OK"
            and "[VIA:ACCEL-BRIDGE" in (via / "functional modules" / "VRN" / "t.py").read_text(encoding="utf-8"), (pa, ra))

        (vdf / "VDF_MDL902_Fam_v0100.py").write_text("def a():\n    pass\n\n\ndef b():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL902_Fam_sha1234567.py").write_text("def a():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL903_Solo_sha89abcdef.py").write_text("def c():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL904_Fam_v0100.py").write_text("def a():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL904_Fam_shaabcdef12.py").write_text("def zz():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL905_Dup_sha11111111.py").write_text("def d():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL906_Dup_sha22222222.py").write_text("def d():\r\n    pass\r\n", encoding="utf-8")
        (vdf / "VDF_MDL907_Ref_v0100.py").write_text("def a():\n    pass\n", encoding="utf-8")
        (vdf / "VDF_MDL907_Ref_sha33333333.py").write_text("def a():\n    pass\n", encoding="utf-8")
        (vdf / "user.py").write_text("import VDF_MDL907_Ref_sha33333333\n", encoding="utf-8")
        pr = plan_retire(via)
        got = sorted(Path(i["path"]).name for i in pr["items"])
        sk = {Path(f).name: w for f, w in pr["skipped"]}
        chk("⑦ 合併車道:家族涵蓋 / 逐位元相同(含 CRLF)→ 候選;唯一實作 · 家族缺名 · 程式點名 → 留",
            got == ["VDF_MDL902_Fam_sha1234567.py", "VDF_MDL906_Dup_sha22222222.py"] and "唯一實作" in sk.get("VDF_MDL903_Solo_sha89abcdef.py", "")
            and "家族缺" in sk.get("VDF_MDL904_Fam_shaabcdef12.py", "") and "程式點名" in sk.get("VDF_MDL907_Ref_sha33333333.py", ""), (got, sk))
        buf = []
        hb = Heartbeat("fx", every=0.05)
        with contextlib.redirect_stdout(_Tee(buf)), hb:
            time.sleep(0.2)
        chk("⑧ 心跳:長跑每格印一行", any("[心跳] fx" in x for x in buf), buf[:2])
        _MODS.clear()
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


class _Tee:
    def __init__(self, buf):
        self.buf = buf

    def write(self, s):
        self.buf.append(s)

    def flush(self):
        pass


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("selftest", "--selftest"):
        return selftest()
    via = find_via()
    lanes = LANES
    if "--lanes" in args and args.index("--lanes") + 1 < len(args):
        lanes = tuple(x for x in args[args.index("--lanes") + 1].split(",") if x in LANES) or LANES
    if args[0] == "plan":
        report(via, build_plan(via, lanes), None)
        return 0
    if args[0] == "apply":
        return cmd_apply(via, lanes)
    if args[0] == "verify":
        plan = build_plan(via, lanes, fresh_cov=False)
        report(via, plan, None, verify(via, []))
        return 0
    print(f"[{TAG}] 不認得的動詞 {args[0]!r};可用:plan · apply [--lanes retire,net,accel,param,ps] · verify · selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
