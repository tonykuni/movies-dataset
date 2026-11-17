#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0104 — 薄尾(v0103 一字不動):唯讀門面多三把鍵,讓接 MCP 的 AI(Claude · ChatGPT · 其他)讀同一份狀態回饋。

操作員 2026-11-17:「每次更新狀態回饋給動作主力 CLAUDE/CHATGPT」。
  vcgc/feedback-delta  → VIA_Reports/vcgc/FEEDBACK_DELTA_latest.txt   這一輪跟上一輪比(修好 / 新增 / 退步 / 仍未解);每次更新先讀這份
  vcgc/feedback        → VIA_Reports/vcgc/FEEDBACK_latest.txt         兩段篩選後的回饋包(≤300 行)
  vcgc/feedback-full   → VIA_Reports/vcgc/FEEDBACK_FULL_latest.jsonl  完整去向冊(大檔照 v0103 的分頁讀)
三份都由 CGC_MDL283_CardMatrixFeedback 產生;本檔只多登鍵,不產生內容。回饋包與更新回饋已遮家目錄路徑;完整去向冊沒遮,只在本機 MCP 讀。
只讀 · 零寫入 · 零網路 · 不 import 他系統 · 不碰 TA-Lib · 不讀寫同意閘。用法同 v0103:--serve [--root] · --client-config [--root] · --selftest。
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import json
import sys
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0104"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL279_MCPServer_v0103.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0103", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0103"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                   # v0100 本體(RECEIPTS 是它的;v0103 的分頁讀照用)
FEEDBACK = {"vcgc/feedback-delta": "VIA_Reports/vcgc/FEEDBACK_DELTA_latest.txt",
            "vcgc/feedback": "VIA_Reports/vcgc/FEEDBACK_latest.txt",
            "vcgc/feedback-full": "VIA_Reports/vcgc/FEEDBACK_FULL_latest.jsonl"}


def install():
    for k, v in FEEDBACK.items():
        P0.RECEIPTS.setdefault(k, v)
    P0.VERSION = VERSION


install()
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    for k in FEEDBACK:                          # 前版鏈的自測數的是「它們那一版的鍵數」,所以先把本版的鍵拿掉再跑、跑完放回
        P0.RECEIPTS.pop(k, None)
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_mcp104_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        f = via / FEEDBACK["vcgc/feedback-delta"]
        f.parent.mkdir(parents=True)
        f.write_text("# 給動作主力 claude 的更新回饋\nNEXT: 自測\n", encoding="utf-8")
        srv = P0.Server(via, None)
        r = srv.read_resource("via://vcgc/feedback-delta")
        chk("vcgc/feedback-delta 讀得到純文字", "給動作主力" in r["contents"][0]["text"])
        m = srv.read_resource("via://vcgc/feedback")
        chk("這台機器還沒有的回饋檔照實說沒有", "還沒有" in m["contents"][0]["text"])
        chk("三把鍵都登了、原有的鍵沒少", all(k in P0.RECEIPTS for k in FEEDBACK) and "vcgc/handoff" in P0.RECEIPTS and "mutual/latest" in P0.RECEIPTS)
        chk("設定檔指到本版", Path(__file__).name in json.dumps(client_config(via), ensure_ascii=False))
    good = rc == 0 and all(ok)
    print("[selftest] %s %s · 前版鏈 rc %d · 本版 %d/%d" % (NAME, VERSION, rc, sum(ok), len(ok)), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = args[args.index("--root") + 1] if "--root" in args else None
        via = Path(root).resolve() if root else P0.VIA_DEFAULT
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    return P0.main(args)


def __getattr__(name):
    return getattr(PRIOR, name)


if __name__ == "__main__":
    sys.exit(main())
