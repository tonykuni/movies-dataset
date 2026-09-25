#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_iface_autosync_v0101 — 模組對模組介面自湊引擎(TOOL-089,批89)
====================================================================
v0100→v0101:Windows WinError 32 修——`with sqlite3.connect() as
conn` 只包交易不關連線,WAL 檔被咬住致暫存夾清理 PermissionError
(工作站 grid 站實證;Linux unlink 開檔可行故容器未現)。全面改
contextlib.closing 確保連線關閉;行為零變更。
====================================================================
操作員令:「generate an engine to support interface:系統與模組、
模組對模組間的 interface 自湊 mapping connecting syncing test debug
user-test debug activate test debug till all works」+核定文(Top8
Python/JS 本機自動同步庫冊、五階段自適應管道、25 大失效模式與解法、
全格式防彈同步示例)。

五階段自適應管道(操作員核定):
  1 Mapping    自湊欄位對映:直配>別名>模糊比對(difflib≥0.75)
               +自動強制轉型(coercion)+預設值回退+大小閾值閘
  2 Connecting 動態介面對接:模組 Schema 執行期註冊(熱插拔),
               connect(A,B) 自動產出對映表(誠實列 MISSING)
  3 Syncing    全格式同步:記憶體(互斥鎖)→檔案(原子寫入+O_EXCL
               跨平台鎖檔+指數退避)→SQLite(WAL+timeout+版本閘)
  4 Testing    動態測試:依對映表生成斷言;版本閘防循環同步死迴圈
  5 Debugging  結構化錯誤(禁空 except)+半同步誠實標記+ignore-set
               防監聽自觸發

整合去重(不另起爐灶的邊界):
  · 合約「內容」同步=VIA_Central_SSOT_Contract_Sync_Engine 既有站;
    本器=模組對模組「執行期介面」自湊層,互補不重疊。
  · 介面「靜態盤點」=TOOL-037 介面合約冊;本器吃其對映思想到執行期。
  · 操作員貼文示例用 fcntl(僅 Unix)——工作站是 Windows,本器改
    O_EXCL 鎖檔(跨平台)+stdlib 全自足;pydantic/watchdog 在位自動
    增強,缺席 graceful(候態冊見 VIA_IfaceAutoSync_Knowledge_v0100)。

紅線:零網路;零刪除;誠實三態;正本零觸碰。
用法:
  via-ifsync --demo       → 全格式自湊同步演示(沙盒)
  via-ifsync --libs       → Top8 Python/JS 庫冊(候態誠實)
  via-ifsync --failures   → 25 大失效模式與解法矩陣
  via-ifsync --selftest   → 十四檢(沙盒零網路)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import contextlib
import difflib
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNOWLEDGE = HERE / "VIA_IfaceAutoSync_Knowledge_v0100.json"


# ────────────────────────── 1 Mapping:自湊欄位對映 ──────────────────────────
class FieldSpec:
    def __init__(self, name, typ, aliases=(), required=True, default=None, max_len=100_000):
        self.name, self.typ, self.aliases = name, typ, tuple(aliases)
        self.required, self.default, self.max_len = required, default, max_len


class Contract:
    """stdlib 介面合約:直配>別名>模糊(≥0.75)自湊;coercion 轉型;誠實 errors"""
    FUZZ = 0.75

    def __init__(self, name: str, fields: list[FieldSpec]):
        self.name, self.fields = name, fields

    def _find_key(self, spec: FieldSpec, raw: dict, used: set):
        if spec.name in raw:
            return spec.name, "direct"
        for a in spec.aliases:
            if a in raw:
                return a, "alias"
        best, score = None, 0.0
        for k in raw:
            if k in used:
                continue
            s = difflib.SequenceMatcher(
                None, spec.name.lower().replace("_", ""),
                str(k).lower().replace("_", "")).ratio()
            if s > score:
                best, score = k, s
        if best is not None and score >= self.FUZZ:
            return best, f"fuzzy:{round(score, 2)}"
        return None, "missing"

    def validate(self, raw: dict) -> dict:
        """回 {ok, data, mapping, errors}(禁空 except:錯誤結構化列出)"""
        data, mapping, errors, used = {}, {}, [], set()
        for spec in self.fields:
            key, how = self._find_key(spec, raw, used)
            if key is None:
                if spec.required and spec.default is None:
                    errors.append({"loc": spec.name, "msg": "缺必填欄位(無別名/模糊命中)"})
                else:
                    data[spec.name] = spec.default
                    mapping[spec.name] = "default"
                continue
            used.add(key)
            v = raw[key]
            if isinstance(v, str) and len(v) > spec.max_len:
                errors.append({"loc": spec.name, "msg": f"超長欄位 {len(v)}>{spec.max_len}(失效#20 閘)"})
                continue
            try:
                if spec.typ is float:
                    v = float(str(v).replace(",", ""))
                elif spec.typ is int:
                    v = int(float(str(v).replace(",", "")))
                elif spec.typ is bool:
                    v = str(v).strip().lower() in ("1", "true", "yes", "y", "是")
                elif spec.typ is str:
                    v = str(v)
            except (ValueError, TypeError):
                errors.append({"loc": spec.name, "msg": f"轉型失敗:{str(raw[key])[:40]!r}→{spec.typ.__name__}"})
                continue
            data[spec.name] = v
            mapping[spec.name] = f"{how}←{key}"
        return {"ok": not errors, "data": data, "mapping": mapping, "errors": errors}


# ─────────────────────── 2 Connecting:動態介面對接 ───────────────────────
class ModuleRegistry:
    """執行期 Schema 註冊(熱插拔);connect(A,B)=自動對映表(誠實 MISSING)"""

    def __init__(self):
        self._mods: dict[str, Contract] = {}
        self._lock = threading.Lock()

    def register(self, contract: Contract):
        with self._lock:
            self._mods[contract.name] = contract

    def connect(self, src: str, dst: str) -> list[dict]:
        a, b = self._mods[src], self._mods[dst]
        rows = []
        a_names = {f.name for f in a.fields}
        for spec in b.fields:
            key, how = spec.name if spec.name in a_names else None, "direct"
            if key is None:
                fake = {f.name: None for f in a.fields}
                key, how = b._find_key(spec, fake, set())
            rows.append({"dst": spec.name, "src": key or "—", "how": how,
                         "verdict": "OK" if key else ("DEFAULT" if not spec.required or spec.default is not None else "MISSING")})
        return rows


# ─────────────── 3 Syncing:全格式(記憶體→檔案→SQLite)────────────────
def _lockfile_acquire(lock: Path, retries=3, backoff=0.15):
    """O_EXCL 跨平台鎖檔(失效#1;fcntl 僅 Unix 故不採)+指數退避"""
    for i in range(retries):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return fd
        except FileExistsError:
            time.sleep(backoff * (i + 1))
    return None


def _atomic_write_json(path: Path, obj) -> None:
    """原子寫入(失效#2):tmp 同夾→os.replace,不留殘缺檔"""
    with tempfile.NamedTemporaryFile("w", dir=str(path.parent), suffix=".tmp",
                                     delete=False, encoding="utf-8") as tf:
        json.dump(obj, tf, ensure_ascii=False, indent=1)
        tmp = tf.name
    os.replace(tmp, str(path))


class AllFormatSync:
    """記憶體(互斥鎖)+JSON 檔(原子+鎖檔)+SQLite(WAL+timeout+版本閘)。
    版本閘=防循環同步死迴圈(失效#21);ignore-set=防監聽自觸發。"""

    def __init__(self, workdir: Path, key_field: str = "record_id",
                 version_field: str = "version"):
        self.dir = Path(workdir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.db = self.dir / "iface_sync.db"
        self.kf, self.vf = key_field, version_field
        self.memory: dict[str, dict] = {}
        self._mlock = threading.Lock()
        self.ignore_files: set[str] = set()
        with contextlib.closing(sqlite3.connect(self.db)) as conn, conn:
            conn.execute("PRAGMA journal_mode=WAL;")   # 失效#6
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("CREATE TABLE IF NOT EXISTS state ("
                         "key TEXT PRIMARY KEY, version INT, payload TEXT, "
                         "sync_status TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

    def sync(self, contract: Contract, raw: dict, source: str = "IPC") -> dict:
        r = contract.validate(raw)
        if not r["ok"]:
            return {"state": "REJECT", "errors": r["errors"], "mapping": r["mapping"]}
        d = r["data"]
        key, ver = str(d[self.kf]), int(d.get(self.vf, 0))
        with self._mlock:                              # 失效#11 競態
            cur = self.memory.get(key)
            if cur is not None and int(cur.get(self.vf, -1)) >= ver:
                return {"state": "SKIP", "note": f"版本閘:既有 v{cur.get(self.vf)} ≥ v{ver}(防死迴圈)"}
            self.memory[key] = d                       # 記憶體=單一真相先行
        status = {"memory": "OK"}
        fp = self.dir / f"{key}.json"
        if source != "FILE_WATCH":                     # 監聽來源不回寫=防迴圈
            self.ignore_files.add(str(fp))
            fd = _lockfile_acquire(fp.with_suffix(".lock"))
            if fd is None:
                status["file"] = "FAIL:locked(退避 3 次仍佔用,誠實)"
            else:
                try:
                    _atomic_write_json(fp, d)
                    status["file"] = "OK"
                finally:
                    os.close(fd)
                    fp.with_suffix(".lock").unlink(missing_ok=True)
        else:
            status["file"] = "SKIP:來源即檔案"
        try:
            with contextlib.closing(sqlite3.connect(self.db, timeout=5.0)) as conn, conn:   # 失效#6/#25
                row = conn.execute("SELECT version FROM state WHERE key=?", (key,)).fetchone()
                if row is None or row[0] < ver:
                    conn.execute("INSERT OR REPLACE INTO state (key,version,payload,sync_status) "
                                 "VALUES (?,?,?,?)",
                                 (key, ver, json.dumps(d, ensure_ascii=False), "SYNCED"))
                    status["db"] = "OK"
                else:
                    status["db"] = f"SKIP:DB 已 v{row[0]}"
        except sqlite3.OperationalError as exc:
            status["db"] = f"FAIL:{str(exc)[:50]}"
        full = all(v.startswith(("OK", "SKIP")) for v in status.values())
        return {"state": "SYNCED" if full else "HALF-SYNC",
                "status": status, "mapping": r["mapping"], "key": key, "version": ver}

    def watch_once(self, mtimes: dict) -> list[Path]:
        """4 Testing 觸發器:stdlib mtime 輪詢(失效#5 後備);ignore-set 放行自寫"""
        changed = []
        for p in sorted(self.dir.glob("*.json")):
            m = p.stat().st_mtime
            if str(p) in self.ignore_files:
                self.ignore_files.discard(str(p))
                mtimes[str(p)] = m
                continue
            if mtimes.get(str(p)) != m:
                mtimes[str(p)] = m
                changed.append(p)
        return changed


# ──────────── 4+5 Testing/Debugging:activate till all works ────────────
def activate(engine: AllFormatSync, contract: Contract, payloads: list[dict],
             max_rounds: int = 3) -> dict:
    """test→debug→…→activate 循環:逐輪重試 HALF-SYNC/REJECT,全綠即收斂"""
    pending = list(payloads)
    log = []
    for rnd in range(1, max_rounds + 1):
        nxt = []
        for pl in pending:
            r = engine.sync(contract, pl)
            if r["state"] in ("SYNCED", "SKIP"):
                log.append({"round": rnd, "state": r["state"]})
            else:
                log.append({"round": rnd, "state": r["state"],
                            "debug": r.get("errors") or r.get("status")})
                nxt.append(pl)
        if not nxt:
            return {"activated": True, "rounds": rnd, "log": log}
        pending = nxt
    return {"activated": False, "rounds": max_rounds, "log": log, "pending": len(pending)}


# ────────────────────────────── 報表道 ──────────────────────────────
def _load_knowledge() -> dict:
    return json.loads(KNOWLEDGE.read_text(encoding="utf-8-sig"))


def cmd_libs() -> int:
    k = _load_knowledge()
    print("=== Top8 Python 本機自動同步庫(候態誠實)===")
    for e in k["top8_python"]:
        print(f"  {e['lib']:<12} {e['role']} · {e['承接']}")
    print("=== Top8 JavaScript(候態冊;零 CDN 紅線,僅前端選型參照)===")
    for e in k["top8_javascript"]:
        print(f"  {e['lib']:<12} {e['role']}")
    return 0


def cmd_failures() -> int:
    k = _load_knowledge()
    print("=== 25 大失效模式與解法(操作員核定;引擎承接標註)===")
    for f in k["failures_top25"]:
        print(f"  #{f['no']:>2} {f['name']} · {f['symptom']} → {f['solution']} "
              f"[py:{f['lib_py']} | js:{f['lib_js']}]")
    return 0


def cmd_demo() -> int:
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        c = Contract("demo", [
            FieldSpec("record_id", str, aliases=("id",)),
            FieldSpec("version", int),
            FieldSpec("metric_value", float),
            FieldSpec("status_code", int, required=False, default=0)])
        eng = AllFormatSync(Path(td))
        print("  [demo] 自湊+轉型:", eng.sync(c, {"id": "N1", "version": 1, "metricValue": "23.45"}))
        print("  [demo] 版本閘防迴圈:", eng.sync(c, {"id": "N1", "version": 1, "metric_value": 9.9}))
        print("  [demo] 壞資料誠實拒:", eng.sync(c, {"id": "N2", "version": 1, "metric_value": "壞值"}))
    return 0


# ────────────────────────────── 十四檢 ──────────────────────────────
def selftest() -> int:
    import tempfile as _tf
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    c = Contract("t", [
        FieldSpec("record_id", str, aliases=("id",)),
        FieldSpec("version", int),
        FieldSpec("metric_value", float),
        FieldSpec("note", str, required=False, default="—", max_len=50)])
    # ① 轉型 coercion(失效#16)
    r = c.validate({"id": "A", "version": "2", "metric_value": "1,234.5"})
    chk("轉型 coercion", r["ok"] and r["data"]["version"] == 2
        and r["data"]["metric_value"] == 1234.5)
    # ② 別名對映 id→record_id
    chk("別名對映", r["mapping"]["record_id"].startswith("alias"))
    # ③ 模糊自湊 metricValue→metric_value(失效#18)
    r3 = c.validate({"id": "A", "version": 1, "metricValue": 2.0})
    chk("模糊自湊", r3["ok"] and r3["mapping"]["metric_value"].startswith("fuzzy"))
    # ④ 缺必填=結構化錯誤(失效#17/#23 禁空 except)
    r4 = c.validate({"id": "A", "metric_value": 1.0})
    chk("缺必填誠實拒", not r4["ok"] and r4["errors"][0]["loc"] == "version")
    # ⑤ 預設值回退
    chk("預設值回退", r["data"]["note"] == "—" and r["mapping"]["note"] == "default")
    # ⑥ 超長欄位閘(失效#20)
    r6 = c.validate({"id": "A", "version": 1, "metric_value": 1.0, "note": "x" * 51})
    chk("超長欄位閘", not r6["ok"] and "超長" in r6["errors"][0]["msg"])
    with _tf.TemporaryDirectory() as td:
        eng = AllFormatSync(Path(td))
        ok1 = eng.sync(c, {"id": "K1", "version": 1, "metric_value": 5.0})
        # ⑦ 全格式三道同步(記憶體+檔案+DB)
        chk("全格式同步", ok1["state"] == "SYNCED"
            and (Path(td) / "K1.json").exists()
            and json.loads((Path(td) / "K1.json").read_text(encoding="utf-8"))["metric_value"] == 5.0)
        # ⑧ 原子寫入(檔案為完整合法 JSON)+WAL 模式在位
        with contextlib.closing(sqlite3.connect(eng.db)) as conn:
            wal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        chk("WAL 模式", wal.lower() == "wal")
        # ⑨ 版本閘防死迴圈(失效#21:同版/舊版拒觸)
        r9 = eng.sync(c, {"id": "K1", "version": 1, "metric_value": 7.7})
        chk("版本閘防迴圈", r9["state"] == "SKIP"
            and eng.memory["K1"]["metric_value"] == 5.0)
        # ⑩ 新版本覆蓋+DB 版本閘一致
        r10 = eng.sync(c, {"id": "K1", "version": 2, "metric_value": 8.8})
        with contextlib.closing(sqlite3.connect(eng.db)) as conn:
            dbv = conn.execute("SELECT version FROM state WHERE key='K1'").fetchone()[0]
        chk("新版本覆蓋", r10["state"] == "SYNCED" and dbv == 2)
        # ⑪ O_EXCL 鎖檔互斥(失效#1)
        lk = Path(td) / "K9.lock"
        fd = _lockfile_acquire(lk)
        fd2 = _lockfile_acquire(lk, retries=2, backoff=0.01)
        chk("鎖檔互斥", fd is not None and fd2 is None)
        os.close(fd)
        lk.unlink()
        # ⑫ 監聽 ignore-set 防自觸發+外部變更可測(失效#5 輪詢後備)
        mt: dict = {}
        eng.watch_once(mt)                     # 建基線(自寫件放行)
        ext = Path(td) / "K2.json"
        ext.write_text(json.dumps({"record_id": "K2", "version": 1,
                                   "metric_value": 3.3}), encoding="utf-8")
        changed = eng.watch_once(mt)
        chk("輪詢監聽+防自觸發", [p.name for p in changed] == ["K2.json"]
            and not eng.watch_once(mt))
        # ⑬ activate till all works(test→debug 循環收斂)
        act = activate(eng, c, [
            {"id": "M1", "version": 1, "metric_value": 1.0},
            {"id": "M2", "version": 1, "metric_value": 2.0}])
        chk("activate 收斂", act["activated"] and act["rounds"] == 1)
    # ⑭ 知識冊完整(Top8×2+25 失效+管道五階)
    k = _load_knowledge()
    chk("知識冊完整", len(k["top8_python"]) == 8 and len(k["top8_javascript"]) == 8
        and len(k["failures_top25"]) == 25 and len(k["pipeline"]) == 5)
    # 動態對接表(Connecting)附測於 ⑭ 後誠實列印
    reg = ModuleRegistry()
    reg.register(c)
    reg.register(Contract("dst", [FieldSpec("record_id", str), FieldSpec("versionNo", int, required=False, default=0)]))
    tbl = reg.connect("t", "dst")
    print(f"  [印] connect(t→dst) 對映表:{tbl}")
    n = 14 - len(fails)
    print(f"  [計] 十四檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 介面自湊引擎 v0101 · 十四檢(沙盒零網路)===")
        return selftest()
    if "--libs" in a:
        return cmd_libs()
    if "--failures" in a:
        return cmd_failures()
    if "--demo" in a:
        print("=== 介面自湊引擎 v0101 · 演示(沙盒)===")
        return cmd_demo()
    print(__doc__.split("用法:")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
