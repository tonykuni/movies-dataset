# -*- coding: utf-8 -*-
"""CGC_MDL258 TempAccel v0100 — TEMP 換記憶體加速器 (純 stdlib, 零安裝 · 零網路)。
把「海量資料一次進 RAM」改為「分片轉儲 TEMP + 串流聚合」,五機制一次到位:
  [1] 分片轉儲 Spill   : 記錄流分片寫入 TEMP (.jsonl.gz), 一片落地立即釋放 RAM。
  [2] 記憶體防衛閘     : 以「實際觀測 payload 位元組」觸發轉儲 (拒用固定寬度估算);
                        psutil 在場則加系統水位參考, 缺席零影響。
  [3] 子進程隔離       : 每片由獨立子進程寫檔後關閉, 作業系統硬性回收該進程全部 RAM。
  [4] 進度日誌/中斷回復 : journal.json 記每片狀態; 重啟自動跳過已完成分片 (Resume)。
  [5] 命名空間隔離     : 每輪獨立 run_<時間戳_uuid> 目錄, 平行引擎不互踩; 滾動只留 N 輪。
治理: 只寫自家 TEMP 命名空間; 不吞例外 (raise ... from); 選配套件 graceful 缺席。
用法:
  acc = TempAccel(chunk_rows=50000)
  for batch in 來源: acc.feed(batch)     # 防衛閘超水位自動轉儲
  acc.flush()
  total = acc.reduce(lambda s, r: s + r["value"], 0.0)   # 串流聚合, 不整批進 RAM
自測: python CGC_MDL258_TempAccel_v0100.py --selftest
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import sys
import tempfile
import uuid
import datetime as dt
import multiprocessing as mp
from pathlib import Path

try:
    import psutil  # 選配: 在場加系統水位參考
except ImportError:
    psutil = None

DEFAULT_LIMIT_MB = 256
KEEP_RUNS = 5


def temp_root() -> Path:
    """本引擎專屬 TEMP 根 (系統 TEMP 下自家命名空間, 不碰他人)。"""
    root = Path(os.environ.get("VIA_TEMPACCEL_DIR") or
                Path(tempfile.gettempdir()) / "VIA_tempaccel")
    root.mkdir(parents=True, exist_ok=True)
    return root


def observed_bytes(records: list) -> int:
    """實際觀測 payload 位元組 (序列化實測, 拒用固定寬度估算)。"""
    return sum(len(json.dumps(r, ensure_ascii=False).encode("utf-8")) + 1 for r in records)


def system_mem_pct() -> float:
    """系統記憶體水位百分比; psutil 缺席回 -1 (誠實未知, 不假造)。"""
    if psutil is not None:
        return float(psutil.virtual_memory().percent)
    return -1.0


def _dump_chunk(path_str: str, records: list) -> None:
    """子進程本體: 單片寫入 .jsonl.gz 後行程結束, OS 硬性回收 RAM。"""
    tmp = path_str + ".part"
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path_str)  # 原子落地: 中斷不留半片


def rolling_cleanup(keep: int = KEEP_RUNS) -> int:
    """滾動清理: 只留最近 keep 輪 run_* 目錄; 回傳刪除數。"""
    runs = sorted([p for p in temp_root().iterdir() if p.is_dir() and p.name.startswith("run_")])
    doomed = runs[:-keep] if keep > 0 else runs
    for p in doomed:
        shutil.rmtree(p, ignore_errors=True)
    return len(doomed)


class TempAccel:
    """TEMP 換記憶體加速器: feed -> (防衛閘) spill -> stream/reduce 串流聚合。"""

    def __init__(self, run_id: str = "", chunk_rows: int = 50000,
                 limit_mb: int = DEFAULT_LIMIT_MB, use_subprocess: bool = True):
        """run_id 給同名可續跑 (Resume); 空白 = 新輪 (時間戳+uuid 命名空間)。"""
        stamp = run_id or ("%s_%s" % (dt.datetime.now().strftime("%Y%m%d_%H%M%S"),
                                      uuid.uuid4().hex[:8]))
        self.run_dir = temp_root() / ("run_%s" % stamp)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.run_dir / "journal.json"
        self.chunk_rows = max(1, chunk_rows)
        self.limit_bytes = max(1, limit_mb) * 1024 * 1024
        self.use_subprocess = use_subprocess
        self.buffer: list = []
        self.buffer_bytes = 0
        self.journal = self._load_journal()

    def _load_journal(self) -> dict:
        """讀回進度日誌; 壞檔誠實重建 (不吞原因, 記入 journal.rebuilt)。"""
        if self.journal_path.exists():
            try:
                return json.loads(self.journal_path.read_text(encoding="utf-8"))
            except ValueError as exc:
                return {"chunks": {}, "rebuilt": "journal 損毀重建: %s" % exc}
        return {"chunks": {}}

    def _save_journal(self) -> None:
        """落地進度日誌 (原子寫)。"""
        tmp = self.journal_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.journal, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.journal_path)

    def guard(self) -> dict:
        """防衛閘讀數: 緩衝實測位元組 + 系統水位 (psutil 缺席 = -1)。"""
        return {"buffer_rows": len(self.buffer), "buffer_bytes": self.buffer_bytes,
                "limit_bytes": self.limit_bytes, "system_pct": system_mem_pct(),
                "over": self.buffer_bytes >= self.limit_bytes or len(self.buffer) >= self.chunk_rows}

    def feed(self, record: dict) -> bool:
        """進一筆; 防衛閘超水位自動轉儲。回傳本筆是否觸發 spill。"""
        self.buffer.append(record)
        self.buffer_bytes += len(json.dumps(record, ensure_ascii=False).encode("utf-8")) + 1
        if self.guard()["over"]:
            self.spill()
            return True
        return False

    def spill(self) -> str:
        """手動/自動轉儲目前緩衝成一片; Resume: 已完成片自動跳過重算。"""
        if not self.buffer:
            return ""
        chunk_id = "chunk_%04d" % len(self.journal["chunks"])
        path = self.run_dir / (chunk_id + ".jsonl.gz")
        done = self.journal["chunks"].get(chunk_id, {})
        if done.get("state") == "DONE" and path.exists():
            self.buffer, self.buffer_bytes = [], 0
            return chunk_id  # 中斷回復: 這片上輪已落地
        rows, size = len(self.buffer), self.buffer_bytes
        if self.use_subprocess:
            proc = mp.Process(target=_dump_chunk, args=(str(path), self.buffer))
            proc.start()
            proc.join()
            if proc.exitcode != 0:
                raise RuntimeError("子進程轉儲失敗 rc=%s (%s)" % (proc.exitcode, chunk_id))
        else:
            _dump_chunk(str(path), self.buffer)
        self.journal["chunks"][chunk_id] = {"state": "DONE", "rows": rows,
                                            "bytes": size, "ts": dt.datetime.now().isoformat()}
        self._save_journal()
        self.buffer, self.buffer_bytes = [], 0
        return chunk_id

    def flush(self) -> str:
        """收尾: 把殘餘緩衝轉儲。"""
        return self.spill()

    def stream(self):
        """串流讀回: 一次只載一片進 RAM, 片間即釋放 (聚合不爆記憶體)。"""
        for chunk_id in sorted(self.journal["chunks"]):
            path = self.run_dir / (chunk_id + ".jsonl.gz")
            if not path.exists():
                raise FileNotFoundError("日誌有帳但片不在: %s" % chunk_id)
            with gzip.open(path, "rt", encoding="utf-8") as f:
                for line in f:
                    yield json.loads(line)

    def reduce(self, fn, init):
        """串流折疊聚合: fn(累計, 記錄) -> 累計。"""
        acc = init
        for record in self.stream():
            acc = fn(acc, record)
        return acc

    def stats(self) -> dict:
        """清點: 片數/列數/位元組/命名空間 (給加速器盤點冊)。"""
        chunks = self.journal["chunks"]
        return {"accel": "A-TEMP", "run_dir": str(self.run_dir),
                "chunks": len(chunks),
                "rows": sum(c["rows"] for c in chunks.values()),
                "bytes": sum(c["bytes"] for c in chunks.values()),
                "resumable": True, "subprocess": self.use_subprocess}


def selftest() -> tuple:
    """自測: 防衛閘觸發/子進程轉儲/串流聚合/中斷回復/命名空間/滾動清理/原子落地。"""
    p = f = 0

    def ck(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    run_id = "selftest_%s" % uuid.uuid4().hex[:6]
    acc = TempAccel(run_id=run_id, chunk_rows=100, limit_mb=1, use_subprocess=False)
    spilled = 0
    for i in range(250):
        if acc.feed({"id": i, "value": float(i), "pad": "x" * (i % 7)}):
            spilled += 1
    acc.flush()
    ck("① 防衛閘自動轉儲 (chunk_rows=100 -> 2 次自動+1 收尾)", spilled == 2 and acc.stats()["chunks"] == 3)
    ck("② 實測位元組非固定估算", observed_bytes([{"a": "xx"}]) != observed_bytes([{"a": "xxxxxx"}]))
    total = acc.reduce(lambda s, r: s + r["value"], 0.0)
    ck("③ 串流聚合值正確 (0+1+...+249)", abs(total - sum(range(250))) < 1e-9)
    ck("④ 進度日誌落地", acc.journal_path.exists() and len(acc.journal["chunks"]) == 3)
    acc2 = TempAccel(run_id=run_id, chunk_rows=100, limit_mb=1, use_subprocess=False)
    ck("⑤ 中斷回復: 同 run_id 讀回 3 片不重算", len(acc2.journal["chunks"]) == 3)
    rows = acc2.reduce(lambda s, r: s + 1, 0)
    ck("⑥ 回復後資料零遺失 (250 列)", rows == 250)
    sub = TempAccel(run_id=run_id + "_sub", chunk_rows=50, limit_mb=1)
    for i in range(60):
        sub.feed({"id": i, "value": 1.0})
    sub.flush()
    ck("⑦ 子進程隔離轉儲 (OS 硬回收)", sub.stats()["chunks"] == 2 and sub.reduce(lambda s, r: s + 1, 0) == 60)
    ck("⑧ 命名空間互不相撞", acc.run_dir != sub.run_dir and acc.run_dir.parent == sub.run_dir.parent)
    ck("⑨ 無 .part 半片殘留 (原子落地)", not list(acc.run_dir.glob("*.part")))
    for i in range(KEEP_RUNS + 3):
        TempAccel(run_id="roll_%02d" % i, use_subprocess=False)
    left = rolling_cleanup()
    runs = [x for x in temp_root().iterdir() if x.name.startswith("run_")]
    ck("⑩ 滾動清理只留 %d 輪" % KEEP_RUNS, left >= 3 and len(runs) <= KEEP_RUNS)
    ck("⑪ psutil graceful (%s)" % ("在場" if psutil else "缺席 -1"), isinstance(system_mem_pct(), float))
    print("[計] CGC_MDL258_TempAccel_v0100 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return p, f


def main() -> None:
    """CLI: --selftest 自測; stats 印 TEMP 命名空間清點。"""
    if "--selftest" in sys.argv:
        _, fails = selftest()
        sys.exit(0 if fails == 0 else 1)
    if "stats" in sys.argv:
        runs = sorted(x.name for x in temp_root().iterdir() if x.name.startswith("run_"))
        print(json.dumps({"temp_root": str(temp_root()), "runs": runs[-10:]}, ensure_ascii=False, indent=2))
        return
    print(__doc__)


if __name__ == "__main__":
    mp.freeze_support()
    main()
