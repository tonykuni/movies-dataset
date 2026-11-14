#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_SSOTSync v0102 — v0101 薄尾(v0101 / v0100 一字不改):提案冊 v0101 + v0101 的自測隔離跑。

操作員 2026-11-01(重申):SSOT / 正則 / 同義字 / 邏輯 / 政策由 VRN-2 / VDF 因應問題累積新增 → 沒有編號(空白)→ VCGC 偵測到新項目做衝突測試 →
有問題發警示 → 使用者 + AI 改完、VCGC 測過無誤 → 公布編號 → VRN-2 / VDF 自動補入編號(三系統互不影響 · 同一套帳與編號 · 由 VCGC 公布)。
本版不改流程(request / apply / sync 照 v0101:提案冊最新版號的條目附進核號請求 · ssot_id 空白 · VCGC 核發後 apply 補填登記冊):
  ① 提案冊 VRN2_SSOT_Proposals_v0101.json = v0100 的 9 條原樣 + v0164 這輪新增 8 條(VRN2-PROP-0010 ~ 0017 · ssot_id 全空)。
  ② v0101 的自測寫死「提案冊 9 條」→ 本夾有 v0101 提案冊時會被它撿到(最高版號)→ 本版自測把 v0101 的自測放進只有 v0100 提案冊的暫存夾跑(不改 v0101)。
動詞同 v0101:request | apply | sync [--vrn <VRN-2 程式夾>] · --selftest
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TAG = "v0102"
DISPLAY_NAME = "VRN2_SSOTSync"
PRIOR_NAME = "VRN2_SSOTSync_v0101.py"
HERE = Path(__file__).resolve().parent
BOOK = "VRN2_SSOT_Proposals_v0101.json"
NEW_KEYS = ("POLICY_NO_MOPS_DOMESTIC_TWSE_TPEX", "TP_ADJ_SYNC", "MOPS_HISTORY_ROW_MARKERS", "TW_DATASET_IDENTITY_PREFIX", "CONSENSUS_TARGET_PRICE_MEDIAN",
            "CONSENSUS_GATE_QUALITY", "VDF_FETCH_ZERO_FAILURE", "TW_MARKET_CONSENSUS_MERGE")


def _prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_ssotsync_prior_v0101", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
request = PRIOR.request
sync = PRIOR.sync


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print(("[PASS] " if cond else "[FAIL] ") + label, flush=True)
        if not cond:
            bad.append(label)
    with tempfile.TemporaryDirectory(prefix="vrn2-ssot102-") as td:
        iso = Path(td) / "iso"
        iso.mkdir()
        for n in (PRIOR_NAME, "VRN2_SSOTSync_v0100.py", "VRN2_SSOT_Proposals_v0100.json"):
            shutil.copy2(str(HERE / n), str(iso / n))
        r = subprocess.run([sys.executable, "-X", "utf8", str(iso / PRIOR_NAME), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        tail = [l for l in (r.stdout or "").splitlines() if "--selftest" in l][-1:]
        chk("① v0101 自測(隔離在只有 v0100 提案冊的夾)照過:%s" % (tail[0][:90] if tail else (r.stderr or "")[-120:]), r.returncode == 0)
        old = json.loads((HERE / "VRN2_SSOT_Proposals_v0100.json").read_text(encoding="utf-8"))
        new = json.loads((HERE / BOOK).read_text(encoding="utf-8"))
        added = new["entries"][len(old["entries"]):]
        chk("② 提案冊 v0101:v0100 的 9 條原樣在前 · 新增 8 條(VRN2-PROP-0010 ~ 0017)· ssot_id 全空 · 種類都是核號請求會送的(SSOT / REGEX / SYN / CFG / PARAM / DICT / LIST)",
            new["entries"][:len(old["entries"])] == old["entries"] and [e["key"] for e in added] == list(NEW_KEYS) and all(e["ssot_id"] == "" for e in new["entries"])
            and [e["proposed_no"] for e in added] == ["VRN2-PROP-%04d" % i for i in range(10, 18)] and all(e["kind"] in PRIOR.PRIOR.REQUEST_KINDS for e in new["entries"]))
        rx = {e["key"]: e["value"] for e in added if e["kind"] == "REGEX"}["VDF_FETCH_ZERO_FAILURE"]
        chk("③ 正則 VDF_FETCH_ZERO_FAILURE:「失敗 0 ·」「失敗 0」對 · 「失敗 01」「失敗 2」不對", bool(re.search(rx, "跑 10 次 · 失敗 0 · 09-18")) and bool(re.search(rx, "失敗 0"))
            and not re.search(rx, "失敗 01") and not re.search(rx, "失敗 2"))
        vrn = Path(td) / "VIA" / "functional modules" / "VRN2"
        (vrn / "SSOT").mkdir(parents=True)
        shutil.copy2(str(HERE / BOOK), str(vrn / "SSOT" / BOOK))
        got = sync(vrn)
        q = json.loads((vrn / "contract" / PRIOR.PRIOR.REQUEST_NAME).read_text(encoding="utf-8"))
        chk("④ 核號請求(暫存 VRN-2 夾 · 沒有登記冊):提案冊 v0101 的 17 條全進 ssot_items(ssot_id 空白 · 待 VCGC 核號)· pending 17 · 來源冊名 v0101",
            q["counts"]["proposals"] == 17 and len(q["pending"]) == 17 and q["proposals_book"] == BOOK and all(i["ssot_id"] == "" for i in q["ssot_items"]) and got["lamp"] in ("GREEN", "YELLOW", "GRAY"))   # 沒有登記冊 = v0100 的灰(請求冊照寫)
    print("[%s] %s %s --selftest · 4 項 · 不過 %d" % ("PASS" if not bad else "FAIL", DISPLAY_NAME, TAG, len(bad)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
