#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0105 — 薄尾(v0104 一字不動):外部工具收據進唯讀門面

2026-11-17 夜:本內容原以 v0104 送在 PR #655,與 PR #654 的 v0104(回饋包三把鍵 · VIA-VCGC-MDL1647)撞版號(同名不同內容);
改以 v0105 疊在 #654 那份 v0104 之上,內容不變,#655 關閉。

操作員 2026-11-17:「用 VCGC 所有省 TOKEN 工具台之工具把目前的黃紅灰色項目全數解決並強化升級 · 外部工具導入啟用並與內部工具完整搭配」。
外部工具(Graphify 本機 AST · Prettier · Ponytail · OmniRoute)由桌機一鍵 Invoke-VIA-VCGC-ExternalTools 先查衝突、再裝、再自測,
收據寫在 VIA_Reports/vcgc/tools/;本版只把那幾份收據登成唯讀資源,讓 AI 經 MCP 讀,不必讀檔、不必問操作員:
  tools/external        VIA_ExternalTools_latest.json(每支工具:預檢燈 · 安裝燈 · 自測燈 · 版本 · 位置 · 與哪支內部工具搭配)
  tools/external-md     VIA_ExternalTools_latest.md(同上,給人看)
  tools/preflight       VIA_ExternalTools_Preflight_latest.json(環境衝突檢查:Python · Node · 連接埠 · 磁碟 · 記憶體 · 既有安裝)
  tools/prettier-check  VIA_PrettierCheck_latest.json(Prettier 只檢不寫:哪些檔排版不一致;鎖定 U/I 檔不在檢查範圍)
其餘(分頁讀 · 根界 · 燈範圍 · 白名單 · 回饋包三把鍵)全照 v0104。零寫入 · 零網路 · 不 import 他系統 · 不碰 TA-Lib · 不讀寫同意閘。
用法同 v0104:--serve [--root] · --client-config [--root] · --selftest。
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
VERSION = "v0105"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL279_MCPServer_v0104.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0104", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0104"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0

NEW_RECEIPTS = {   # 資源 URI 尾段 → 相對 VIA 根的檔(只讀);全是桌機一鍵自己寫的收據
    "tools/external": "VIA_Reports/vcgc/tools/VIA_ExternalTools_latest.json",
    "tools/external-md": "VIA_Reports/vcgc/tools/VIA_ExternalTools_latest.md",
    "tools/preflight": "VIA_Reports/vcgc/tools/VIA_ExternalTools_Preflight_latest.json",
    "tools/prettier-check": "VIA_Reports/vcgc/tools/VIA_PrettierCheck_latest.json",
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
        P0.RECEIPTS.update(saved); P0.VERSION = VERSION
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)) if note else ""), flush=True)
    with tempfile.TemporaryDirectory(prefix="via_mcp104_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        f = via / NEW_RECEIPTS["tools/external"]; f.parent.mkdir(parents=True)
        f.write_text(json.dumps({"lamp": "YELLOW", "tools": [{"tool": "graphify", "lamp": "GREEN"}]}, ensure_ascii=False), encoding="utf-8")
        srv = P0.Server(via, None)
        lst = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}})["result"]["resources"]
        uris = {r["uri"] for r in lst}
        chk("ⓐ 資源多 4 份外部工具收據 · 前版的全在(含 v0104 回饋包)", {"via://" + k for k in NEW_RECEIPTS} <= uris and "via://graphify/latest" in uris and "via://vcgc/feedback-delta" in uris, len(uris))
        r = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "via://tools/external"}})["result"]["contents"][0]["text"]
        chk("ⓑ 讀 tools/external:小檔整份原樣回", json.loads(r)["tools"][0]["tool"] == "graphify")
        m = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": "via://tools/preflight"}})["result"]["contents"][0]["text"]
        chk("ⓒ 還沒有的收據照實說「還沒有」不炸", "還沒有" in m)
        enum = next(t for t in P0.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]
        chk("ⓓ via_receipt 的 key 列舉含新 4 份 · 分頁參數(offset · limit · sha)照 v0103", set(NEW_RECEIPTS) <= set(enum["key"]["enum"]) and "offset" in enum)
        cfg = client_config(via)
        chk("ⓔ client-config 的 command 指到本檔(v0105)", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0104 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
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
