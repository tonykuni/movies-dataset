#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_AutoNumberSSOT.py  —  URN VIA-SYS-ENG-007  v0100

自動編號管理 SSOT 模組
=====================

平台上每一個被治理的東西（PowerShell 控制腳本、system manager、engine、
library、JSON 設定檔、參數鍵）都要有一個**永不改變**的號碼。這支模組就是
那個號碼的唯一來源。

兩種號碼，同時發放：

    code    VIA-{TYPE}-{YYYYMMDD}-{######}   流水號，帶首次登記日期
    hcode   VIA-{TYPE}-{HEX6}                blake2s 穩定碼，可離線重算驗證

hcode 的雜湊輸入原文一併寫進 SSOT（LL#30），否則號碼無法被第三方驗證。

治理原則（只增不減）
    - 號碼一旦發出，永不回收、永不重指派
    - 識別鍵（identity）用**家族鍵**不用完整路徑，檔案搬家不會換號
    - 這一輪沒掃到的舊項目 -> state=DORMANT，不刪除
    - 之後又出現 -> state=ACTIVE，沿用原號碼
    - 所有事件寫 append-only ledger（jsonl）

單獨執行可做自我測試：
    python VIA_AutoNumberSSOT.py --selftest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

URN_SELF = "VIA-SYS-ENG-007"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

# 允許的型別代碼。只增不減：要新增型別就往下加，不要改既有的。
TYPE_CODES = {
    "SYS": "系統（整棵樹）",
    "MGR": "system manager（最上層控制者）",
    "GOV": "控管用 PowerShell（governor）",
    "ORC": "orchestrator（承上啟下）",
    "ENG": "engine（被呼叫的執行體）",
    "LIB": "library（無進入點）",
    "MDL": "module（模組檔）",
    "CFG": "JSON 設定檔",
    "PRM": "參數鍵路徑",
    "EDG": "呼叫關係邊",
    "FNC": "函式（function / cmdlet）",
    "CLS": "類別（class）",
    "IMP": "外部依賴套件",
    "PAT": "待套用的修補（accel / net / remark）",
}

STATE_ACTIVE = "ACTIVE"
STATE_DORMANT = "DORMANT"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _datestamp() -> str:
    return datetime.now().strftime("%Y%m%d")


def stable_hash(type_code: str, identity: str) -> tuple:
    """回傳 (hash_input, hex6)。輸入原文一併回傳，供 SSOT 保存以利驗證。"""
    raw = "%s|%s" % (type_code, identity)
    hex6 = hashlib.blake2s(raw.encode("utf-8"), digest_size=3).hexdigest().upper()
    return raw, hex6


def _atomic_write(path: Path, text: str) -> None:
    """先寫暫存檔再 replace。避免半途中斷把 SSOT 截斷成空檔。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


class AutoNumberSSOT:
    """自動編號註冊處。所有寫入都是加法。"""

    def __init__(self, out_dir: Path, ssot_name: str = "autonumber_ssot.json"):
        self.out_dir = Path(out_dir)
        self.ssot_path = self.out_dir / ssot_name
        self.ledger_path = self.out_dir / "autonumber_ledger.jsonl"
        self.records: Dict[str, Dict[str, Any]] = {}
        self.counters: Dict[str, int] = {}
        self._events: List[Dict[str, Any]] = []
        self._seen_this_run: set = set()
        self.loaded_from_disk = False
        self._load()

    # -- 載入 ------------------------------------------------------------
    def _load(self) -> None:
        if not self.ssot_path.exists():
            return
        try:
            data = json.loads(self.ssot_path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            # 壞掉的 SSOT 不覆蓋、不刪除，改名封存後重新開始
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.ssot_path.replace(self.ssot_path.with_name(
                self.ssot_path.stem + "_corrupt_" + stamp + ".json"))
            return
        for rec in data.get("records", []):
            key = rec.get("key")
            if key:
                self.records[key] = rec
        self.counters = {k: int(v) for k, v in data.get("counters", {}).items()}
        self.loaded_from_disk = True

    # -- 發號 ------------------------------------------------------------
    def assign(self, type_code: str, identity: str,
               attrs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """給 identity 一個號碼。已經有號的沿用原號，只更新 last_seen 與 attrs。"""
        if type_code not in TYPE_CODES:
            raise ValueError("未登記的型別代碼: %s" % type_code)
        key = "%s|%s" % (type_code, identity)
        self._seen_this_run.add(key)
        attrs = attrs or {}

        existing = self.records.get(key)
        if existing is not None:
            existing["last_seen"] = _now()
            if existing.get("state") == STATE_DORMANT:
                existing["state"] = STATE_ACTIVE
                existing["reactivated_at"] = _now()
                self._log("REACTIVATE", existing)
            merged = dict(existing.get("attrs", {}))
            changed = False
            for name, value in attrs.items():
                if merged.get(name) != value:
                    merged[name] = value
                    changed = True
            if changed:
                existing["attrs"] = merged
                self._log("ATTR_UPDATE", existing)
            return existing

        seq = self.counters.get(type_code, 0) + 1
        self.counters[type_code] = seq
        hash_input, hex6 = stable_hash(type_code, identity)
        record = {
            "key": key,
            "type": type_code,
            "type_label": TYPE_CODES[type_code],
            "identity": identity,
            "code": "VIA-%s-%s-%06d" % (type_code, _datestamp(), seq),
            "hcode": "VIA-%s-%s" % (type_code, hex6),
            "hash_algo": "blake2s/3",
            "hash_input": hash_input,      # LL#30：不存輸入，號碼就無法驗證
            "seq": seq,
            "state": STATE_ACTIVE,
            "first_seen": _now(),
            "last_seen": _now(),
            "spec": SPEC_VERSION,
            "attrs": dict(attrs),
        }
        self.records[key] = record
        self._log("ASSIGN", record)
        return record

    def sweep_absent(self) -> int:
        """這輪沒看到的既有項目轉 DORMANT。不刪除任何一筆。"""
        turned = 0
        for key, rec in self.records.items():
            if key in self._seen_this_run:
                continue
            if rec.get("state") == STATE_ACTIVE:
                rec["state"] = STATE_DORMANT
                rec["dormant_at"] = _now()
                self._log("DORMANT", rec)
                turned += 1
        return turned

    # -- 稽核 ------------------------------------------------------------
    def verify(self) -> List[Dict[str, str]]:
        """回傳閘門結果。每一項都是可以失敗的斷言，不是裝飾。"""
        gates: List[Dict[str, str]] = []

        codes = [r["code"] for r in self.records.values()]
        dup_code = len(codes) - len(set(codes))
        gates.append({
            "code": "AN01", "title": "流水號唯一",
            "status": "PASS" if dup_code == 0 else "FAIL",
            "detail": "%d 筆，重複 %d" % (len(codes), dup_code)})

        hcodes = [r["hcode"] for r in self.records.values()]
        dup_h = len(hcodes) - len(set(hcodes))
        gates.append({
            "code": "AN02", "title": "穩定碼無碰撞",
            "status": "PASS" if dup_h == 0 else "FAIL",
            "detail": "%d 筆，碰撞 %d（碰撞代表 3-byte 摘要不夠用）" % (len(hcodes), dup_h)})

        bad = 0
        for rec in self.records.values():
            _, expect = stable_hash(rec["type"], rec["identity"])
            if rec["hcode"] != "VIA-%s-%s" % (rec["type"], expect):
                bad += 1
            if not rec.get("hash_input"):
                bad += 1
        gates.append({
            "code": "AN03", "title": "穩定碼可重算（LL#30）",
            "status": "PASS" if bad == 0 else "FAIL",
            "detail": "不符或缺輸入原文 %d 筆" % bad})

        for type_code, top in self.counters.items():
            seqs = [r["seq"] for r in self.records.values() if r["type"] == type_code]
            if seqs and max(seqs) > top:
                gates.append({
                    "code": "AN04", "title": "計數器不落後",
                    "status": "FAIL",
                    "detail": "%s 計數器 %d < 已用最大 %d" % (type_code, top, max(seqs))})
                break
        else:
            gates.append({
                "code": "AN04", "title": "計數器不落後",
                "status": "PASS", "detail": "%d 種型別" % len(self.counters)})

        return gates

    # -- 落地 ------------------------------------------------------------
    def _log(self, event: str, record: Dict[str, Any]) -> None:
        self._events.append({
            "ts": _now(), "event": event, "by": URN_SELF,
            "key": record["key"], "code": record["code"], "hcode": record["hcode"],
            "state": record.get("state"),
        })

    def save(self) -> None:
        payload = {
            "urn": URN_SELF,
            "version": VERSION,
            "spec": SPEC_VERSION,
            "generated_at": _now(),
            "governance": "append-only / 只增不減：號碼不回收、項目不刪除、消失者轉 DORMANT",
            "type_codes": TYPE_CODES,
            "counters": self.counters,
            "total": len(self.records),
            "active": sum(1 for r in self.records.values() if r["state"] == STATE_ACTIVE),
            "dormant": sum(1 for r in self.records.values() if r["state"] == STATE_DORMANT),
            "records": sorted(self.records.values(), key=lambda r: (r["type"], r["seq"])),
        }
        _atomic_write(self.ssot_path, json.dumps(payload, ensure_ascii=False, indent=2))
        if self._events:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8", newline="\n") as handle:
                for ev in self._events:
                    handle.write(json.dumps(ev, ensure_ascii=False) + "\n")
            self._events = []

    # -- 查詢 ------------------------------------------------------------
    def code_of(self, type_code: str, identity: str) -> str:
        rec = self.records.get("%s|%s" % (type_code, identity))
        return rec["code"] if rec else ""

    def by_type(self, type_code: str) -> List[Dict[str, Any]]:
        return [r for r in self.records.values() if r["type"] == type_code]


# ---------------------------------------------------------------------------

def _selftest() -> int:
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="an_ssot_"))
    failures: List[str] = []
    try:
        reg = AutoNumberSSOT(tmp)
        a = reg.assign("ENG", "VDF/VDF_Hub.py", {"lang": "py"})
        b = reg.assign("ENG", "VRN/VRN_Report.py", {"lang": "py"})
        reg.assign("MGR", "Start-VIA-SystemManager.ps1", {"lang": "ps1"})
        reg.save()

        if a["code"].endswith("000001") is False:
            failures.append("首號不是 000001: %s" % a["code"])
        if b["seq"] != 2:
            failures.append("序號沒遞增")

        # 第二輪：同樣的 identity 必須拿到同樣的號碼（冪等）
        reg2 = AutoNumberSSOT(tmp)
        a2 = reg2.assign("ENG", "VDF/VDF_Hub.py", {"lang": "py"})
        if a2["code"] != a["code"]:
            failures.append("重跑換號了: %s -> %s" % (a["code"], a2["code"]))
        if a2["first_seen"] != a["first_seen"]:
            failures.append("first_seen 被覆寫")

        # VRN 這輪沒出現 -> 應轉 DORMANT，且不得消失
        reg2.sweep_absent()
        reg2.save()
        raw = json.loads((tmp / "autonumber_ssot.json").read_text(encoding="utf-8"))
        keys = {r["key"] for r in raw["records"]}
        if "ENG|VRN/VRN_Report.py" not in keys:
            failures.append("DORMANT 項目被刪掉了（違反只增不減）")
        dormant = [r for r in raw["records"] if r["state"] == STATE_DORMANT]
        if len(dormant) != 2:
            failures.append("DORMANT 數不對: %d" % len(dormant))

        # 復活後號碼必須沿用
        reg3 = AutoNumberSSOT(tmp)
        c = reg3.assign("ENG", "VRN/VRN_Report.py", {})
        if c["code"] != b["code"]:
            failures.append("復活後換號了")
        if c["state"] != STATE_ACTIVE:
            failures.append("復活後狀態不對")
        reg3.save()

        for gate in reg3.verify():
            if gate["status"] != "PASS":
                failures.append("閘門 %s %s" % (gate["code"], gate["detail"]))

        lines = (tmp / "autonumber_ledger.jsonl").read_text(encoding="utf-8").strip().split("\n")
        if len(lines) < 6:
            failures.append("ledger 事件數過少: %d" % len(lines))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        for msg in failures:
            print("FAIL  " + msg)
        return 1
    print("PASS  VIA_AutoNumberSSOT %s 自我測試全過（冪等／DORMANT 保留／復活沿用／閘門）" % VERSION)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="VIA_AutoNumberSSOT.py",
        description="%s 自動編號管理 SSOT 模組" % URN_SELF)
    parser.add_argument("--selftest", action="store_true", help="跑自我測試")
    parser.add_argument("--out", default="", help="SSOT 目錄")
    parser.add_argument("--list", action="store_true", help="列出現有號碼")
    args = parser.parse_args(argv)

    if args.selftest or not args.out:
        return _selftest()

    reg = AutoNumberSSOT(Path(args.out))
    if args.list:
        for rec in sorted(reg.records.values(), key=lambda r: (r["type"], r["seq"])):
            print("%-24s %-22s %-8s %s" % (
                rec["code"], rec["hcode"], rec["state"], rec["identity"]))
        print("\n共 %d 筆" % len(reg.records))
    for gate in reg.verify():
        print("%-5s %-22s %-5s %s" % (
            gate["code"], gate["title"], gate["status"], gate["detail"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
