#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0106 — 薄尾(v0105 一字不動):現況顯示的收據進唯讀門面

操作員 2026-11-18:「請你接線」。現況顯示(CGC_MDL283;入口動詞 via-vcgc monitor)每跑一輪寫一份收據,
本版只把它登成唯讀資源,讓 AI 經 MCP 讀燈與下一步,不必讀檔、不必問操作員:
  vcgc/status   VIA_Reports/vcgc/STATUS_latest.json(燈 · 摘要 · 下一步 · 各系統要處理的項數 · 對帳 · 是不是主機實跑 · 各輸出檔位置)
細項仍是 v0104 的三把鍵:vcgc/feedback-delta(先讀這份)· vcgc/feedback · vcgc/feedback-full。
其餘(分頁讀 · 根界 · 燈範圍 · 白名單 · 外部工具收據)全照 v0105。零寫入 · 零網路 · 不 import 他系統 · 不碰 TA-Lib · 不讀寫同意閘。
用法同 v0105:--serve [--root] · --client-config [--root] · --selftest。
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
VERSION = "v0106"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL279_MCPServer_v0105.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0105", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0105"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0

NEW_RECEIPTS = {   # 資源 URI 尾段 → 相對 VIA 根的檔(只讀);現況顯示自己寫的收據
    "vcgc/status": "VIA_Reports/vcgc/STATUS_latest.json",
}
P0.RECEIPTS.update(NEW_RECEIPTS)
P0.VERSION = VERSION
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    saved = {k: P0.RECEIPTS.pop(k) for k in NEW_RECEIPTS}   # 前版自測數的是前版的資源份數 → 先拿掉本版新增,跑完放回
    P0.VERSION = PRIOR.VERSION
    try:
        rc = PRIOR.selftest()
    finally:
        P0.RECEIPTS.update(saved)
        P0.VERSION = VERSION
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_mcp106_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        srv = P0.Server(via, None)
        m = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://vcgc/status"}})["result"]["contents"][0]["text"]
        chk("ⓐ 還沒跑過 monitor:照實說「還沒有」不炸", "還沒有" in m)
        f = via / NEW_RECEIPTS["vcgc/status"]
        f.parent.mkdir(parents=True)
        f.write_text(json.dumps({"schema": "VIA.StatusDisplay.Receipt.v1", "lamp": "RED", "summary": "真紅 3", "next": "先處理真紅"}, ensure_ascii=False), encoding="utf-8")
        lst = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}})["result"]["resources"]
        uris = {r["uri"] for r in lst}
        chk("ⓑ 資源多 1 份 · 前版的全在(回饋包三把鍵 · 外部工具收據)", "via://vcgc/status" in uris and {"via://vcgc/feedback-delta", "via://tools/external", "via://graphify/latest"} <= uris, len(uris))
        r = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "via://vcgc/status"}})["result"]["contents"][0]["text"]
        chk("ⓒ 讀 vcgc/status:小檔整份原樣回(燈與下一步都在)", json.loads(r)["lamp"] == "RED" and json.loads(r)["next"] == "先處理真紅")
        enum = next(t for t in P0.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]
        chk("ⓓ via_receipt 的 key 列舉含 vcgc/status · 分頁參數照前版", "vcgc/status" in enum["key"]["enum"] and "offset" in enum)
        cfg = client_config(via)
        chk("ⓔ client-config 的 command 指到本檔(v0106)", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
        before = sorted(p.name for p in f.parent.iterdir())
        srv.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "via://vcgc/status"}})
        chk("ⓕ 讀收據零寫入(夾內檔不變)", sorted(p.name for p in f.parent.iterdir()) == before)
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0105 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


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
