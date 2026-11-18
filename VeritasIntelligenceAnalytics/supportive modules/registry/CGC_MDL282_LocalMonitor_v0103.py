#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL282_LocalMonitor v0103 — 薄尾(v0102 · v0101 · v0100 一字不動):收據契約的「選配」與「自己的收據」照規矩處理。

操作員 2026-11-18:「請你接線」。接線後收據契約冊多一筆 VCGC 的 status-display(現況顯示自己的收據,選配)。v0101 讀契約時有兩個缺口,本版補上:
  ① 選配收據不計入系統燈(契約冊與 VIA_MutualMonitor 的規矩:系統燈 = 非選配收據的最差燈)。
     v0101 把每一筆都拿去算「測試分級」的系統級格子;本版選配的那幾筆只列在「收據契約」區塊,不進測試分級。
  ② 自己的收據不讀自己的燈:現況顯示的收據寫的是「上一輪整體是紅是綠」。把它當成一項輸入,只要有一輪是紅,下一輪就會因為這一筆再紅,永遠出不來。
     本版對 VIA_Reports/vcgc/STATUS_latest.json 只看在不在、必填欄齊不齊、過不過時效,不讀它的燈。
  其餘偵測、快取、彙總列標記與 v0102 相同。唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
動詞  run · extra · selftest · version(同 v0102)
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

import datetime as _dt
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL282_LocalMonitor_v0103"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL282_LocalMonitor_v0102.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL282_LocalMonitor_v0102", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL282_LocalMonitor_v0102"] = PRIOR
_spec.loader.exec_module(PRIOR)
P1 = PRIOR.PRIOR            # v0101:sec_extra 用它的全域名呼叫 sec_contract / sec_testgrid
P0 = P1.PRIOR               # v0100
PRIOR.ENGINE = P1.ENGINE = P0.ENGINE = ENGINE
OWN = ("VIA_Reports/vcgc/STATUS_latest.json",)
_O = {"contract": P1.sec_contract, "testgrid": P1.sec_testgrid}


def _specs(via: Path) -> dict:
    """契約冊尾版 → {"系統鍵|收據 id": 規格}。讀不到回空表(v0101 自己會報冊不在)。"""
    p = P1.tail_json(Path(via) / "supportive modules" / "registry", "VIA_SystemReceipt_Contract_SSOT")
    d = P0.load_json(p) if p else None
    out = {}
    for sysn, s in ((d or {}).get("systems") or {}).items():
        for r in s.get("receipts") or []:
            out["%s|%s" % (sysn, r.get("id"))] = r
    return out


def sec_contract(via: Path):
    rows = _O["contract"](via)
    specs = _specs(via)
    for row in rows:
        spec = specs.get(str(row.get("id")))
        if not spec:
            continue
        if spec.get("optional"):
            row["optional"] = True
            row["detail"] = row.get("detail", "") + " · 選配:不計入系統燈"
        if str(spec.get("path") or "").replace("\\", "/").endswith(OWN) and row.get("lamp") != "x":
            notes = [n for n in row.get("detail", "").split(" · ") if n and not n.startswith("自報 ")]
            bad = any(k in n for n in notes for k in ("缺必填欄", "沒有時間", "超過時效"))
            row["lamp"] = "y" if bad else "g"
            row["detail"] = "本平台自己的收據:只看在不在、必填欄與時效,不讀自己上一輪的燈" + ((" · " + " · ".join(notes)) if notes else "")
    return rows


def sec_testgrid(via: Path, contract_items, expected=None):
    return _O["testgrid"](via, [it for it in contract_items if not it.get("optional")], expected)


P1.sec_contract, P1.sec_testgrid = sec_contract, sec_testgrid


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0102(含 v0101 · v0100)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_lm103_st_"))
    try:
        via = tmp / "via"
        reg, rep = via / "supportive modules" / "registry", via / "VIA_Reports" / "vcgc"
        reg.mkdir(parents=True)
        rep.mkdir(parents=True)
        now = _dt.datetime.now(_dt.timezone.utc)
        (reg / "VIA_SystemReceipt_Contract_SSOT_v0101.json").write_text(json.dumps({"stale_hours": 48, "lamp_maps": {}, "systems": {"VCGC": {"receipts": [
            {"id": "test", "path": "VIA_Reports/vcgc/TEST_latest.json", "lamp_key": "lamp", "at_keys": ["at"], "required": ["lamp", "at"], "zh": "串測"},
            {"id": "status-display", "path": "VIA_Reports/vcgc/STATUS_latest.json", "lamp_key": "lamp", "at_keys": ["at", "ts"], "required": ["lamp", "at", "version", "summary"], "zh": "現況顯示", "optional": True},
            {"id": "systems", "path": "VIA_Reports/vcgc/SYSTEMS_latest.json", "lamp_key": "lamp", "at_keys": ["at"], "required": [], "zh": "systems", "optional": True}]}}}, ensure_ascii=False), encoding="utf-8")
        (rep / "TEST_latest.json").write_text(json.dumps({"lamp": "GREEN", "at": now.isoformat()}), encoding="utf-8")
        (rep / "STATUS_latest.json").write_text(json.dumps({"lamp": "RED", "at": now.isoformat(), "version": "v0103", "summary": "真紅 3"}), encoding="utf-8")
        (rep / "SYSTEMS_latest.json").write_text(json.dumps({"lamp": "RED", "at": now.isoformat()}), encoding="utf-8")
        k = {x["id"]: x for x in sec_contract(via)}
        chk("自己的收據是紅也不讀它的燈:在、欄齊、沒過期 → 綠", k["VCGC|status-display"]["lamp"] == "g" and "不讀自己上一輪的燈" in k["VCGC|status-display"]["detail"], k["VCGC|status-display"])
        chk("別的選配收據照讀它的燈,並標選配", k["VCGC|systems"]["lamp"] == "r" and k["VCGC|systems"].get("optional") and "選配" in k["VCGC|systems"]["detail"])
        chk("必要收據不標選配", not k["VCGC|test"].get("optional") and k["VCGC|test"]["lamp"] == "g")
        g = {x["id"]: x for x in sec_testgrid(via, list(k.values()))}
        chk("測試分級的系統級格子只算必要收據(紅的選配不拖累)", g["VCGC|系統"]["lamp"] == "g" and "綠 1 · 黃 0 · 紅 0" in g["VCGC|系統"]["detail"], g["VCGC|系統"])
        (rep / "STATUS_latest.json").write_text(json.dumps({"lamp": "GREEN", "at": (now - _dt.timedelta(hours=100)).isoformat(), "version": "v0103"}), encoding="utf-8")
        k2 = {x["id"]: x for x in sec_contract(via)}
        chk("自己的收據過期或缺必填欄 → 黃並點名", k2["VCGC|status-display"]["lamp"] == "y" and "缺必填欄 summary" in k2["VCGC|status-display"]["detail"] and "超過時效" in k2["VCGC|status-display"]["detail"], k2["VCGC|status-display"]["detail"])
        (rep / "STATUS_latest.json").unlink()
        k3 = {x["id"]: x for x in sec_contract(via)}
        chk("自己的收據不在 → 灰(沒有收據),照舊", k3["VCGC|status-display"]["lamp"] == "x" and "沒有收據" in k3["VCGC|status-display"]["detail"])
        items = PRIOR.sec_extra(via)
        chk("整輪延伸偵測照跑,選配收據不進測試分級", any(x["id"] == "VCGC|systems" for x in items) and next(x for x in items if x["id"] == "VCGC|系統")["lamp"] == "g")
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    verb = a[0] if a and not a[0].startswith("-") else "run"
    if verb == "selftest" or "--selftest" in a:
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
