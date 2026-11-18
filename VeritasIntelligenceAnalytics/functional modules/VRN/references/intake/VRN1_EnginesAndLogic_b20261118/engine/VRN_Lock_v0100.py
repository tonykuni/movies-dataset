#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG013 · VRN_Lock_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 24；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_Lock v0100 -- what has been proven right is locked, a later change that breaks it is stopped, and what is not right yet
is written out as a fix list.

Operator 2026-10-11:
  「正確鎖功能鎖成功部分及引擎 位成功的持續實測實際修正直到輸出正確可驗證無誤」

Two locks (rules: ssot/VRN_TitleTrim_SSOT_v0100.json "lock"):
  engines  ssot/VRN_EngineLock_SSOT_v0100.json, inside VRN.  An engine (or book) is locked only when every known-answer
           proof that covers it passes; the lock is its AST fingerprint (comments, e.g. the AST ID injection, do not move it;
           a book is fingerprinted as canonical JSON).  `check` turns red when a locked engine's logic changes -- run
           `VRN_Main_v0100.py lock` to prove it again before the new fingerprint is taken.
  outputs  a ledger OUTSIDE the VRN folder (VRN_LOCK_HOME, else %LOCALAPPDATA%\\VRN_Main\\locks, else
           ~/.local/state/VRN_Main/locks): real reports' values never enter the repository.  Keyed by the file's SHA-256 and
           the part (title.ticker, cover.target_price, annual.gross_profit@2025 ...).  A VERIFIED part is locked the first
           time (NEW); the same value later is HELD; a different or missing value is BROKEN (red) until the operator
           unlocks it on purpose.  A new file content (other SHA) is a new file: old locks do not apply.

Fix list: every part that is not VERIFIED (and every BROKEN lock), worst first, as CSV + JSON + a short text the operator
can paste back into the conversation.  No network, LIVE off, no consent variable read or set.
"""

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

import argparse
import ast
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import stat
import tempfile
import time
from collections import Counter
from pathlib import Path

LOCK_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
RULE_BOOK = VRN_ROOT / "ssot" / "VRN_TitleTrim_SSOT_v0100.json"
ENGINE_LOCK_BOOK = VRN_ROOT / "ssot" / "VRN_EngineLock_SSOT_v0100.json"
LEDGER_NAME = "VRN_Lock_Ledger_v0100.json"
HISTORY_NAME = "VRN_Lock_History_v0100.jsonl"
FIX_CSV = "VRN_FixList_v0100.csv"
FIX_JSON = "VRN_FixList_v0100.json"
FIX_TXT = "VRN_FixList_Paste_v0100.txt"
STATUS_OF = {"HELD": "PASS", "NEW": "PASS", "OPEN": "WARN", "NOT_IN_RUN": "PASS", "BROKEN": "FAIL"}


# [VRN-ID] VRN-ENG013-FNC001 · LOGIC
def rules():
    return json.loads(RULE_BOOK.read_text(encoding="utf-8"))["lock"]


# =====================================================================
# 1 . FINGERPRINTS
# =====================================================================
# [VRN-ID] VRN-ENG013-FNC021 · LOGIC
def _canon(node):
    """The AST as plain data, the same on every Python version: node names and fields, empty fields left out
    (ast.dump changed between 3.12 and 3.13 -- it now omits them -- so it is not used for the fingerprint)."""
    if isinstance(node, ast.AST):
        out = [type(node).__name__]
        for name, value in ast.iter_fields(node):
            if name in ("type_comment", "type_ignores", "kind") or value is None or (isinstance(value, list) and not value):
                continue
            out.append([name, _canon(value)])
        return out
    if isinstance(node, list):
        return [_canon(x) for x in node]
    return [type(node).__name__, repr(node)]


# [VRN-ID] VRN-ENG013-FNC002 · LOGIC
def ast_sha(path):
    """SHA-256 of the module's AST: comments and blank lines do not count, code and docstrings do; the same on Python 3.11-3.13."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
    data = json.dumps(_canon(tree), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# [VRN-ID] VRN-ENG013-FNC003 · LOGIC
def json_sha(path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# [VRN-ID] VRN-ENG013-FNC004 · LOGIC
def fingerprint(rel, root=VRN_ROOT):
    path = Path(root) / rel
    if not path.is_file():
        return {"kind": "", "sha256": "", "missing": True}
    if path.suffix == ".py":
        return {"kind": "ast", "sha256": ast_sha(path)}
    if path.suffix == ".json":
        return {"kind": "json", "sha256": json_sha(path)}
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return {"kind": "bytes", "sha256": hashlib.sha256(raw).hexdigest()}


# [VRN-ID] VRN-ENG013-FNC005 · LOGIC
def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# =====================================================================
# 2 . ENGINE LOCK (inside VRN, proven by known answers)
# =====================================================================
# [VRN-ID] VRN-ENG013-FNC006 · LOGIC
def targets(root=VRN_ROOT):
    """Every engine and every book a proof names; engine/*.py that no proof covers are listed too (unlocked)."""
    r = rules()
    skip = set(r.get("not_engines") or [])
    out = {f"engine/{p.name}" for p in (Path(root) / "engine").glob("*.py") if f"engine/{p.name}" not in skip}
    out |= {f"engine/mother/{p.name}" for p in (Path(root) / "engine" / "mother").glob("*.py")}
    for files in (r.get("proofs") or {}).values():
        out |= set(files.get("covers") or [])
    return sorted(out)


# [VRN-ID] VRN-ENG013-FNC007 · LOGIC
def run_module_selftest(rel, root=VRN_ROOT):
    """(ok, detail) for an engine's own selftest(); a [SKIP] (a dependency missing) does not prove anything."""
    path = Path(root) / rel
    name = "vrn_lock_proof_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(module)
            got = module.selftest()
    except Exception as error:  # noqa: BLE001
        return False, f"{error.__class__.__name__}: {error}"[:200]
    rc = got[0] if isinstance(got, tuple) else got
    text = buf.getvalue()
    last = [ln for ln in text.splitlines() if ln.strip()][-1:] or [""]
    if "[SKIP]" in text:
        return False, "略過（相依套件不在）：不算證明 · " + last[0][:120]
    if "[FAIL]" in text or int(rc or 0) != 0:
        return False, "自測沒過 · " + last[0][:160]
    return True, last[0][:160]


# [VRN-ID] VRN-ENG013-FNC008 · IO
def write_engine_lock(proof_results, root=VRN_ROOT, book_path=ENGINE_LOCK_BOOK):
    """proof_results: {proof: (ok, detail)} -> the engine lock book (locked = every covering proof passed)."""
    r = rules()
    proofs = r.get("proofs") or {}
    covering = {}
    for name, spec in proofs.items():
        for rel in spec.get("covers") or []:
            covering.setdefault(rel, []).append(name)
    files, unlocked = {}, {}
    for rel in targets(root):
        names = covering.get(rel) or []
        fp = fingerprint(rel, root)
        if fp.get("missing"):
            unlocked[rel] = "檔案不在"
        elif not names:
            unlocked[rel] = "沒有已知答案證明它（不鎖；要鎖先給它一組已知答案）"
        elif not all((proof_results.get(n) or (False, ""))[0] for n in names):
            bad = [n for n in names if not (proof_results.get(n) or (False, ""))[0]]
            unlocked[rel] = "證明沒過：" + "、".join(bad)
        else:
            files[rel] = {"kind": fp["kind"], "sha256": fp["sha256"], "proofs": names}
    book = {"schema": "VRN_EngineLock_SSOT_v0100", "version": LOCK_VERSION,
            "rule": r.get("engine_rule", ""), "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "proofs": {n: {"gate": (proofs.get(n) or {}).get("gate", ""), "ok": bool((proof_results.get(n) or (False, ""))[0]),
                           "detail": (proof_results.get(n) or (False, "沒有跑"))[1]} for n in proofs},
            "files": files, "unlocked": unlocked}
    Path(book_path).write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return book


# [VRN-ID] VRN-ENG013-FNC009 · VALIDATE
def check_engine_lock(root=VRN_ROOT, book_path=ENGINE_LOCK_BOOK):
    """-> [{file, state, detail}]: HELD / CHANGED / MISSING (locked) and UNLOCKED / NEW (not locked)."""
    if not Path(book_path).is_file():
        return [{"file": "", "state": "NO_BOOK", "detail": f"{Path(book_path).name} 不在：先跑 VRN_Main_v0100.py lock"}]
    book = json.loads(Path(book_path).read_text(encoding="utf-8"))
    out = []
    for rel, spec in sorted((book.get("files") or {}).items()):
        fp = fingerprint(rel, root)
        if fp.get("missing"):
            out.append({"file": rel, "state": "MISSING", "detail": "鎖住的檔不見了"})
        elif fp["sha256"] != spec.get("sha256"):
            what = "邏輯變了（AST 指紋不同）" if fp["kind"] == "ast" else "內容變了（JSON 指紋不同）" if fp["kind"] == "json" else "內容變了"
            out.append({"file": rel, "state": "CHANGED", "detail": f"鎖住的{what}：跑 VRN_Main_v0100.py lock 重新驗過已知答案才換鎖"})
        else:
            out.append({"file": rel, "state": "HELD", "detail": "+".join(spec.get("proofs") or [])})
    known = set(book.get("files") or {}) | set(book.get("unlocked") or {})
    for rel, why in sorted((book.get("unlocked") or {}).items()):
        out.append({"file": rel, "state": "UNLOCKED", "detail": why})
    for rel in targets(root):
        if rel not in known:
            out.append({"file": rel, "state": "NEW", "detail": "新檔：還沒證明、還沒鎖"})
    return out


# =====================================================================
# 3 . OUTPUT LEDGER (outside VRN)
# =====================================================================
# [VRN-ID] VRN-ENG013-FNC010 · LOGIC
def ledger_home(override=""):
    """(folder, why).  VRN_LOCK_HOME > override > %LOCALAPPDATA%\\VRN_Main\\locks > ~/.local/state/VRN_Main/locks.
    Never inside the VRN folder: the ledger holds values read from real reports."""
    env = os.environ.get("VRN_LOCK_HOME", "")
    if env:
        home, why = Path(env), "VRN_LOCK_HOME"
    elif override:
        home, why = Path(override), "--lock-home"
    elif os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        home, why = Path(os.environ["LOCALAPPDATA"]) / "VRN_Main" / "locks", "%LOCALAPPDATA%"
    else:
        home, why = Path.home() / ".local" / "state" / "VRN_Main" / "locks", "~/.local/state"
    try:
        resolved = home.resolve()
        inside = resolved == VRN_ROOT.resolve() or VRN_ROOT.resolve() in resolved.parents
    except OSError:
        inside = False
    if inside:
        home, why = Path(tempfile.gettempdir()) / "VRN_Main" / "locks", "（要的位置在 VRN 資料夾裡，改放暫存目錄：真報告的值不進倉庫）"
    return home, why


# [VRN-ID] VRN-ENG013-FNC011 · LOGIC
def canonical(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return f"{float(value):.10g}"
    s = str(value).strip()
    if len(s) >= 10 and s.isdigit():
        return s                                           # round 4: a phone (886223269899) is text, never a float
    try:
        return f"{float(s.replace(',', '')):.10g}" if s and s.replace(",", "").replace(".", "", 1).lstrip("-").isdigit() else s
    except ValueError:
        return s


LOSSY_RX = re.compile(r"^-?\d(?:\.\d+)?e[+-]\d+$")


# [VRN-ID] VRN-ENG013-FNC023 · LOGIC
def lossy_same(old, new):
    """Round 5 (2026-10-12): a ledger written before round 4 holds '8.862232698e+11' for the phone 886223269812 -- the old
    canonical read the digits as a float and dropped the tail.  The new value is run through that old rule: equal = the same
    value, and the ledger then keeps the exact new form (healed)."""
    if not LOSSY_RX.match(str(old or "")):
        return False
    try:
        return f"{float(str(new).replace(',', '')):.10g}" == str(old)
    except (TypeError, ValueError):
        return False


# [VRN-ID] VRN-ENG013-FNC022 · LOGIC
def same_value(part, old, new):
    """Real run 2026-10-12 (round 4): the ledger had read the phone '0223269899' as a number ('223269899') and called the
    same phone written '886223269899' BROKEN.  A phone is the same phone when its last 8 digits agree (country code, the
    area code's 0 and an extension aside); every other part compares its canonical value; a lossy old canonical is
    compared through the old rule (lossy_same)."""
    if str(part).endswith(".tel"):
        da, db = re.sub(r"\D", "", str(old or "")), re.sub(r"\D", "", str(new or ""))
        if da and da[-8:] == db[-8:]:
            return True
    if str(part).endswith(".company"):
        ka, kb = company_key(old), company_key(new)
        if ka and kb and (ka == kb or (min(len(ka), len(kb)) >= (2 if re.search(r"[一-鿿]", ka) else 4) and (kb.startswith(ka) or ka.startswith(kb)))):
            return True                                   # 2026-10-13: 慧洋 = 慧洋-KY, 頎邦 = 頎邦科技股份有限公司 (the same company)
    return old == new or lossy_same(old, new)


COMPANY_FORM_RX = re.compile(r"(?:股份有限公司|有限公司|股份公司|公司|corporation|corp|incorporated|inc|limited|ltd|holdings|holding|company|co)$")


# [VRN-ID] VRN-ENG013-FNC024 · LOGIC
def company_key(name):
    """A company name as the ledger compares it: letters / digits / CJK only, -KY and company-form words dropped."""
    k = re.sub(r"[^0-9a-z一-鿿]", "", str(name or "").casefold())
    if k.endswith("ky") and (len(k) > 4 or re.search(r"[一-鿿]ky$", k)):
        k = k[:-2]
    for _ in range(3):
        k2 = COMPANY_FORM_RX.sub("", k)
        if k2 == k or len(k2) < 2:
            break
        k = k2
    return k


# [VRN-ID] VRN-ENG013-CLS001 · CLASS
class Ledger:
    """The output locks of one place (real samples: the operator's ledger; synthetic runs: a folder of the run)."""

    # [VRN-ID] VRN-ENG013-FNC012 · INIT
    def __init__(self, home):
        self.home = Path(home)
        self.path = self.home / LEDGER_NAME
        self.history = self.home / HISTORY_NAME
        if self.path.is_file():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {"schema": "VRN_Lock_Ledger_v0100", "version": LOCK_VERSION, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "parts": {}, "engines": {}}

    # [VRN-ID] VRN-ENG013-FNC013 · LOGIC
    def save(self):
        self.home.mkdir(parents=True, exist_ok=True)
        self.data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        # 2026-10-19：tmp 檔名本來是 `with_suffix(".tmp")` —— 固定、而且兩個行程共用。
        # A 寫完要換檔的瞬間 B 已經把它截短重寫，A 於是把 B 寫到一半的內容 rename 成正式帳本。
        # 實測兩個寫入者對 400 次讀：共用 tmp 讀壞 70 次、換檔時 tmp 不見 156 次。
        # 第一版改成帶 pid+thread，但 Codex PR #72 P1 指出「可預測」本身就是問題：
        # 帳本家目錄若是別人也寫得進去的地方，攻擊者可以先在那個名字上放 symlink，
        # write_text 會跟著它走（在 VRN_Main 那一側實測過：受害者檔被整個覆蓋）。
        # 改用 mkstemp：O_CREAT|O_EXCL、名字隨機 —— 不可預測，而且存在就失敗。
        # 唯一性由 O_EXCL 保證，不再靠自己組名字。帳本是擋退步的那一份，它壞掉等於守門先倒。
        keep_mode = None
        try:
            keep_mode = stat.S_IMODE(self.path.stat().st_mode)
        except OSError:
            pass
        fd, tmp_name = tempfile.mkstemp(dir=str(self.home), prefix=self.path.name + ".", suffix=".tmp")
        tmp = Path(tmp_name)
        try:
            handle = os.fdopen(fd, "w", encoding="utf-8")
        except BaseException:
            os.close(fd)
            tmp.unlink(missing_ok=True)
            raise
        try:
            with handle:
                handle.write(json.dumps(self.data, ensure_ascii=False, indent=1))
            if keep_mode is not None:
                os.chmod(tmp, keep_mode)
            os.replace(tmp, self.path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    # [VRN-ID] VRN-ENG013-FNC014 · LOGIC
    def log(self, event):
        self.home.mkdir(parents=True, exist_ok=True)
        with open(self.history, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(event, at=time.strftime("%Y-%m-%dT%H:%M:%S")), ensure_ascii=False, default=str) + "\n")

    # [VRN-ID] VRN-ENG013-FNC015 · LOGIC
    def apply(self, items, engines=None, write=True):
        """items: [{file, file_sha256, part, value, state, why}] -> {rows, counts, engines, verdict, ledger}."""
        parts = self.data.setdefault("parts", {})
        rows = []
        seen_files = {it["file_sha256"][:16] for it in items if it.get("file_sha256")}
        seen_keys = set()
        for it in items:
            sha = (it.get("file_sha256") or "")[:16]
            if not sha:
                continue
            key = f"{sha}|{it['part']}"
            seen_keys.add(key)
            value = canonical(it.get("value"))
            old = parts.get(key)
            if it.get("dynamic"):
                # 2026-10-16 操作員「全部使用最新的 adj close 或報告前一日的 adj close 為基準動態更新」：
                # 這個值本來就會隨庫更新而變，變動不是退步。照記最新的值與基準日（看得到變化），但永不紅。
                # 不這樣做的話，同一份報告隔天再跑必 BROKEN（實測 534 檔，12 個 BROKEN 全是 cover.current_price）。
                was = (old or {}).get("value")
                parts[key] = {"file": it["file"], "file_sha256": it["file_sha256"], "part": it["part"], "value": value,
                              "why": it.get("why", ""), "source": it.get("source", ""), "dynamic": True,
                              "date": it.get("date", ""), "locked_at": (old or {}).get("locked_at") or time.strftime("%Y-%m-%dT%H:%M:%S"),
                              "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                moved = was is not None and not same_value(it["part"], was, value)
                if moved:
                    self.log({"event": "dynamic", "key": key, "from": was, "to": value, "date": it.get("date", "")})
                rows.append({"file": it["file"], "file_sha16": sha, "part": it["part"], "value": value, "state": it.get("state", ""),
                             "lock": "DYNAMIC", "locked_value": value,
                             "detail": (f"動態部位（基準 {it.get('date', '')}）：{was!r} → {value!r}" if moved
                                        else f"動態部位（基準 {it.get('date', '')}）：與上次同值")})
                continue
            if old is not None:
                if same_value(it["part"], old.get("value"), value):
                    lock, detail = "HELD", f"鎖於 {old.get('locked_at', '')}"
                    if it.get("source") == "db" and old.get("source") != "db":
                        old["source"] = "db"                     # the same value, now from the database
                    if lossy_same(old.get("value"), value) and not LOSSY_RX.match(str(value)):
                        self.log({"event": "healed", "key": key, "from": old.get("value"), "to": value, "why": "舊帳本把數字串當浮點存（失真）；同值，改記完整寫法"})
                        old["value"], old["healed_at"] = value, time.strftime("%Y-%m-%dT%H:%M:%S")
                        detail += " · 帳本值修正成完整寫法"
                elif it.get("source") == "db" and old.get("source") != "db":
                    # 2026-10-13 operator「公司名稱價格一率至DATABASE去取」: the value now comes from the database -- a change of
                    # source, not a regression; the old lock is replaced (VERIFIED) or released, and logged
                    self.log({"event": "source_db", "key": key, "from": old.get("value"), "to": value, "state": it.get("state")})
                    if it.get("state") == "VERIFIED":
                        lock = "NEW"
                        parts[key] = {"file": it["file"], "file_sha256": it["file_sha256"], "part": it["part"], "value": value,
                                      "why": it.get("why", ""), "source": "db", "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                    else:
                        lock = "OPEN"
                        parts.pop(key, None)
                    detail = f"改取資料庫的值（原鎖 {old.get('value')!r} → {value!r}）"
                    old = parts.get(key)
                else:
                    lock, detail = "BROKEN", f"鎖住的值 {old.get('value')!r} → 這次 {value!r}（{it.get('state')}）"
            elif it.get("state") == "VERIFIED":
                lock, detail = "NEW", it.get("why", "")
                parts[key] = {"file": it["file"], "file_sha256": it["file_sha256"], "part": it["part"], "value": value,
                              "why": it.get("why", ""), "locked_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                if it.get("source"):
                    parts[key]["source"] = it["source"]
            else:
                lock, detail = "OPEN", it.get("why", "")
            rows.append({"file": it["file"], "file_sha16": sha, "part": it["part"], "value": value, "state": it.get("state", ""),
                         "lock": lock, "locked_value": (old or parts.get(key) or {}).get("value", ""), "detail": detail})
        for key, old in parts.items():
            sha, part = key.split("|", 1)
            if sha in seen_files and key not in seen_keys:
                rows.append({"file": old.get("file", ""), "file_sha16": sha, "part": part, "value": "", "state": "",
                             "lock": "BROKEN", "locked_value": old.get("value", ""), "detail": "鎖住的部位這次沒有輸出"})
        not_in_run = sum(1 for key in parts if key.split("|", 1)[0] not in seen_files)
        broken = [r for r in rows if r["lock"] == "BROKEN"]
        eng_rows = []
        old_eng = self.data.setdefault("engines", {})
        for rel, fp in sorted((engines or {}).items()):
            prev = old_eng.get(rel)
            if prev is None:
                eng_rows.append({"file": rel, "state": "NEW"})
            elif prev.get("sha256") != fp.get("sha256"):
                eng_rows.append({"file": rel, "state": "CHANGED_BROKE" if broken else "CHANGED_HELD"})
            else:
                eng_rows.append({"file": rel, "state": "HELD"})
        if not broken:
            for rel, fp in (engines or {}).items():
                old_eng[rel] = {"sha256": fp.get("sha256"), "kind": fp.get("kind"), "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        counts = Counter(r["lock"] for r in rows)
        counts["NOT_IN_RUN"] = not_in_run
        verdict = "RED" if broken else ("AMBER" if counts.get("OPEN") or any(e["state"].startswith("CHANGED") for e in eng_rows) else "GREEN")
        if write:
            self.save()
            self.log({"event": "run", "counts": dict(counts), "verdict": verdict, "broken": broken[:50],
                      "engines_changed": [e["file"] for e in eng_rows if e["state"].startswith("CHANGED")]})
        return {"rows": rows, "counts": dict(counts), "engines": eng_rows, "verdict": verdict, "ledger": str(self.path),
                "locked_total": len(parts)}

    # [VRN-ID] VRN-ENG013-FNC016 · LOGIC
    def unlock(self, file_or_sha, part=""):
        """Remove the locks of one file (name or SHA-256 prefix), or one part of it.  Logged."""
        parts = self.data.get("parts", {})
        hit = [k for k, v in parts.items()
               if (k.startswith(file_or_sha[:16]) or v.get("file") == file_or_sha or Path(v.get("file", "")).name == file_or_sha)
               and (not part or k.split("|", 1)[1] == part)]
        for k in hit:
            parts.pop(k, None)
        if hit:
            self.save()
            self.log({"event": "unlock", "target": file_or_sha, "part": part, "removed": hit})
        return hit

    # [VRN-ID] VRN-ENG013-FNC017 · LOGIC
    def status(self):
        parts = self.data.get("parts", {})
        return {"ledger": str(self.path), "parts": len(parts), "files": len({k.split("|", 1)[0] for k in parts}),
                "by_part": dict(Counter(k.split("|", 1)[1].split("@")[0] for k in parts).most_common(20)),
                "engines": len(self.data.get("engines", {})), "updated": self.data.get("updated", "")}


# =====================================================================
# 4 . FIX LIST
# =====================================================================
# [VRN-ID] VRN-ENG013-FNC018 · IO
def write_fix_list(out_dir, fixes, header):
    """fixes: rows of VRN_TitleTrim.fix_rows (+ lock) -> CSV, JSON and a short text to paste back.  -> {csv, json, txt}."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cols = ["seq", "priority", "file", "part", "state", "lock", "value", "why", "sources", "evidence"]
    rows = [dict(f, seq=i) for i, f in enumerate(fixes, 1)]
    with open(out / FIX_CSV, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    (out / FIX_JSON).write_text(json.dumps({"header": header, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = [f"VRN 待修清單 {LOCK_VERSION} · {header.get('generated', '')} · 樣本 {header.get('files', 0)} 檔（個股 {header.get('stock', 0)}）",
             "鎖：" + " · ".join(f"{k} {v}" for k, v in (header.get("lock_counts") or {}).items())
             + f" · 帳本 {header.get('ledger', '')}",
             "部位：" + " · ".join(f"{k} {v}" for k, v in (header.get("states") or {}).items())]
    groups = ((0, "已鎖部位退步（BROKEN：擋下）", 80), (1, "讀法不一致／該有沒讀到／TRIM 掉字（先修）", 80),
              (2, "要人判：多候選、列標對不到科目、驗算不過", 60))
    for pri, title, cap in groups:
        sel = [r for r in rows if r["priority"] == pri]
        if not sel:
            continue
        lines.append(f"== 優先 {pri}：{title} · {len(sel)} 項 ==")
        if pri == 2:
            unm = Counter(r["part"].split(":", 1)[1].rsplit("@", 1)[0] for r in sel if r["state"] == "UNMAPPED")
            if unm:
                lines.append("  對不到科目的列標（次數）：" + "、".join(f"{k}×{v}" for k, v in unm.most_common(30)))
            sel = [r for r in sel if r["state"] != "UNMAPPED"]
        for r in sel[:cap]:
            lines.append(f"  {r['file']} | {r['part']} | {r['state']}{('/' + r['lock']) if r['lock'] else ''} | {str(r['value'])[:40]} | "
                         f"{str(r['why'])[:90]} | {str(r['sources'])[:140]}" + (f" | {str(r['evidence'])[:120]}" if r.get("evidence") else ""))
        if len(sel) > cap:
            lines.append(f"  …另 {len(sel) - cap} 項在 {FIX_CSV}")
    single = Counter(r["part"].split("@")[0] for r in rows if r["priority"] == 3)
    if single:
        lines.append(f"== 優先 3：只有一條讀法（SINGLE，鎖不住）· {sum(single.values())} 項，按部位 ==")
        lines.append("  " + "、".join(f"{k}×{v}" for k, v in single.most_common(40)))
    (out / FIX_TXT).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": str(out / FIX_CSV), "json": str(out / FIX_JSON), "txt": str(out / FIX_TXT), "rows": len(rows)}


# =====================================================================
# 5 . SELFTEST / CLI
# =====================================================================
# [VRN-ID] VRN-ENG013-FNC019 · ENTRY
def selftest(verbose=True):
    checks = []
    with tempfile.TemporaryDirectory(prefix="vrn_lock_") as td:
        led = Ledger(Path(td) / "locks")
        item = {"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.target_price", "value": 1200.0, "state": "VERIFIED", "why": "x"}
        open_item = dict(item, part="cover.analyst", value="元大", state="SINGLE")
        r1 = led.apply([item, open_item], {"engine/x.py": {"sha256": "1", "kind": "ast"}})
        checks.append(("VERIFIED 第一次 = NEW，SINGLE = OPEN", r1["counts"].get("NEW") == 1 and r1["counts"].get("OPEN") == 1))
        r2 = Ledger(Path(td) / "locks").apply([dict(item, value="1,200")], {"engine/x.py": {"sha256": "1", "kind": "ast"}})
        checks.append(("同值（1,200 = 1200.0）= HELD", r2["counts"].get("HELD") == 1 and r2["verdict"] != "RED"))
        r3 = Ledger(Path(td) / "locks").apply([dict(item, value=104.0, state="CONFLICT")], {"engine/x.py": {"sha256": "2", "kind": "ast"}})
        checks.append(("值變了 = BROKEN，紅燈，點名改過的引擎", r3["counts"].get("BROKEN") == 1 and r3["verdict"] == "RED"
                       and r3["engines"][0]["state"] == "CHANGED_BROKE"))
        r4 = Ledger(Path(td) / "locks").apply([dict(item, part="cover.date", value="2026-09-01")], {})
        checks.append(("鎖住的部位沒輸出 = BROKEN", any(r["lock"] == "BROKEN" and r["part"] == "cover.target_price" for r in r4["rows"])))
        r5 = Ledger(Path(td) / "locks").apply([dict(item, file_sha256="cd" * 32, value=99.0)], {}, write=False)
        checks.append(("新檔內容（別的 SHA）舊鎖不套", r5["counts"].get("NEW") == 1 and not r5["counts"].get("BROKEN")))
        led = Ledger(Path(td) / "locks")
        removed = led.unlock("a.pdf", "cover.target_price")
        checks.append(("操作員解鎖一個部位（有紀錄）", len(removed) == 1 and (Path(td) / "locks" / HISTORY_NAME).is_file()))
        home, _why = ledger_home(str(VRN_ROOT / "ssot"))
        checks.append(("帳本絕不放進 VRN 資料夾", VRN_ROOT.resolve() not in home.resolve().parents or "VRN_LOCK_HOME" in os.environ))
        src = Path(td) / "m.py"
        src.write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
        a = ast_sha(src)
        src.write_text("# [VRN-ID] VRN-XXX-FNC001 · LOGIC\ndef f(x):\n\n    return x + 1  # comment\n", encoding="utf-8")
        b = ast_sha(src)
        src.write_text("def f(x):\n    return x + 2\n", encoding="utf-8")
        c = ast_sha(src)
        checks.append(("AST 指紋：只加註解不變、改邏輯就變", a == b and a != c))
        fixes = [{"priority": 1, "file": "a.pdf", "part": "title.rating_action", "state": "CONFLICT", "lock": "", "value": "MAINTAIN",
                  "why": "標題=MAINTAIN vs 首頁引擎=UPGRADE", "sources": "{}"},
                 {"priority": 3, "file": "a.pdf", "part": "annual.basic_eps@2025", "state": "SINGLE", "lock": "", "value": "10.4", "why": "",
                  "sources": "{}"}]
        got = write_fix_list(Path(td) / "fix", fixes, {"generated": "t", "files": 1, "stock": 1})
        txt = Path(got["txt"]).read_text(encoding="utf-8")
        checks.append(("待修清單 CSV／JSON／貼回文字", got["rows"] == 2 and "title.rating_action" in txt and "annual.basic_eps×1" in txt))
        healed = Ledger(Path(td) / "locks_lossy")
        healed.data.setdefault("parts", {})[f"{'ab' * 8}|cover.tel"] = {"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.tel",
                                                                        "value": "8.862232698e+11", "locked_at": "t"}
        r6 = healed.apply([{"file": "a.pdf", "file_sha256": "ab" * 32, "part": "cover.tel", "value": "886223269812", "state": "VERIFIED"}], {})
        moved = Ledger(Path(td) / "locks_db")
        base = {"file": "a.pdf", "file_sha256": "cd" * 32, "state": "VERIFIED"}
        moved.apply([dict(base, part="title.company", value="Wiwynn"), dict(base, part="cover.current_price", value=3300.0)], {})
        r7 = Ledger(Path(td) / "locks_db").apply([dict(base, part="title.company", value="緯穎", source="db"),
                                                  dict(base, part="cover.current_price", value=3300.0, source="db")], {})
        r8 = Ledger(Path(td) / "locks_db").apply([dict(base, part="title.company", value="廣達", source="db"),
                                                  dict(base, part="cover.current_price", value=3300.0, source="db")], {})
        checks.append(("改取資料庫的值是換來源、不是退步：重新上鎖並記帳；同值照樣 HELD；之後換值照樣擋",
                       sorted(r["lock"] for r in r7["rows"]) == ["HELD", "NEW"] and r8["counts"].get("BROKEN") == 1
                       and same_value("title.company", "慧洋", "慧洋-KY") and same_value("title.company", "頎邦", "頎邦科技股份有限公司")))
        checks.append(("舊帳本的失真浮點值（8.862232698e+11）：同一支電話 = HELD，帳本值改成完整號碼",
                       r6["counts"].get("HELD") == 1 and healed.data["parts"][f"{'ab' * 8}|cover.tel"]["value"] == "886223269812"
                       and not lossy_same("8.862232698e+11", "886223269999")))
        dyn = Ledger(Path(td) / "locks_dyn")
        d0 = {"file": "凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf", "file_sha256": "ef" * 32, "part": "cover.current_price",
              "state": "VERIFIED", "source": "db", "dynamic": True}
        d1 = dyn.apply([dict(d0, value=96.9, date="2026-09-15")], {})
        d2 = Ledger(Path(td) / "locks_dyn").apply([dict(d0, value=95.5, date="2026-09-16")], {})
        d3 = Ledger(Path(td) / "locks_dyn").apply([dict(d0, value=95.5, date="2026-09-16")], {})
        checks.append(("動態部位（現價以 adj close 為基準、庫更新就變）：記最新值與基準日，永不判退步",
                       d1["rows"][0]["lock"] == "DYNAMIC" and d2["rows"][0]["lock"] == "DYNAMIC"
                       and not d2["counts"].get("BROKEN") and d2["verdict"] != "RED"
                       and "95.5" in d2["rows"][0]["detail"] and "2026-09-16" in d3["rows"][0]["detail"]
                       and dyn.data["parts"][f"{'ef' * 8}|cover.current_price"]["dynamic"] is True))
        checks.append(("電話只比後 8 碼（0223269899 = 886223269899；分機接進去才算變）",
                       same_value("cover.tel", "223269899", "886223269899") and not same_value("cover.tel", "886223269899", "8862232698997960")
                       and canonical("886223269899") == "886223269899" and not same_value("cover.target_price", "100", "101")))
    bad = [c for c in checks if not c[1]]
    if verbose:
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        print(f"[LOCK] {LOCK_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return 1 if bad else 0


# [VRN-ID] VRN-ENG013-FNC020 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN Lock: engine fingerprints, the output ledger, the fix list")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("selftest")
    st = sub.add_parser("status")
    st.add_argument("--lock-home", default="")
    un = sub.add_parser("unlock")
    un.add_argument("target", help="檔名或檔案 SHA-256（前 16 碼即可）")
    un.add_argument("--part", default="")
    un.add_argument("--lock-home", default="")
    sub.add_parser("engines")
    args = parser.parse_args(argv)
    if args.command == "status":
        home, why = ledger_home(args.lock_home)
        print(json.dumps(dict(Ledger(home).status(), home_from=why), ensure_ascii=False, indent=1))
        return 0
    if args.command == "unlock":
        home, _why = ledger_home(args.lock_home)
        removed = Ledger(home).unlock(args.target, args.part)
        print(f"解鎖 {len(removed)} 個部位" + (": " + ", ".join(removed[:20]) if removed else ""))
        return 0 if removed else 1
    if args.command == "engines":
        for r in check_engine_lock():
            print(f"  [{r['state']:8}] {r['file']} · {r['detail']}")
        return 0
    return selftest()


if __name__ == "__main__":
    sys.exit(main())
