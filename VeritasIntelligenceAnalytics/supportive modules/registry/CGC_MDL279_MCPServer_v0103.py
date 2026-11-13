#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL279_MCPServer v0103 — 薄尾(v0102 一字不動):MCP 露出「上傳檔整合」收據(只讀 · 零寫入 · 零網路)。

操作員 2026-11-10:「activate vcgc mcp to files」。本版只加資源,不加動詞、不改協定:
  uploads/latest     上傳檔整合收據(VIA_UploadsWorkbench 尾版寫出;Invoke-VIA-UploadsWorkbench-v0100.ps1 複製到此)
                     內容:每份正本的複本 · SHA-256 · 側檔 / 交接收據釘選核對 · 審查包包內 SHA256SUMS · 各系統頁列數與燈
收據檔在 VIA_Reports/(.gitignore 內,只留本機,不進公開倉)。還沒跑過 = 照實說「還沒有」,不炸。
用法同 v0102:--serve [--root] · --client-config [--root] · --selftest(先 v0102 鏈再本版 3 項)。
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
VERSION = "v0103"
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "CGC_MDL279_MCPServer_v0102.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0102", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0102"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0                                  # v0100 本體(Server · tool_specs · resource_specs · RECEIPTS)

NEW_RECEIPTS_0103 = {
    "uploads/latest": "VIA_Reports/uploads/UPLOADS_latest.json",
}
_PRIOR_KEYS = set(P0.RECEIPTS)
P0.RECEIPTS.update(NEW_RECEIPTS_0103)
P0.VERSION = VERSION
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False)
    for old in (str(_PRIOR_FILE), _PRIOR_FILE.name, str(PRIOR._PRIOR_FILE), PRIOR._PRIOR_FILE.name):
        text = text.replace(old, str(Path(__file__).resolve()) if "/" in old or "\\" in old else Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    added = [k for k in NEW_RECEIPTS_0103 if k not in _PRIOR_KEYS]
    for k in added:                                   # 前版自測數資源數要原樣 → 先拿掉本版的 key,跑完再掛回
        P0.RECEIPTS.pop(k, None)
    try:
        rc = PRIOR.selftest()
    finally:
        P0.RECEIPTS.update(NEW_RECEIPTS_0103)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    with tempfile.TemporaryDirectory(prefix="via_mcp103_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        srv = P0.Server(via, None)
        res = {r["name"] for r in P0.resource_specs(via)}
        enum = set(next(t for t in P0.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]["key"]["enum"])
        chk("ⓐ 資源列 %d 份 = 前版 %d + 本版新 %d · via_receipt enum 含 uploads/latest" % (len(res), len(_PRIOR_KEYS), len(added)),
            len(res) == len(_PRIOR_KEYS) + len(added) and set(NEW_RECEIPTS_0103) <= res and set(NEW_RECEIPTS_0103) <= enum)
        miss = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://uploads/latest"}})["result"]["contents"][0]
        (via / "VIA_Reports" / "uploads").mkdir(parents=True)
        (via / "VIA_Reports" / "uploads" / "UPLOADS_latest.json").write_text('{"engine": "VIA_UploadsWorkbench_v0101", "lamp": "YELLOW", "uploaded": 5}', encoding="utf-8")
        got = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "via://uploads/latest"}})["result"]["contents"][0]
        chk("ⓑ 還沒跑 = 照實說還沒有不炸 · 跑過 = 讀到收據(engine · lamp)", "還沒有" in miss["text"] and "VIA_UploadsWorkbench_v0101" in got["text"])
        cfg = json.dumps(client_config(via))
        chk("ⓒ client-config 的 command 指到本檔(v0103)", Path(__file__).name in cfg and _PRIOR_FILE.name not in cfg)
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0102 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = None
        if "--root" in args:
            root = args[args.index("--root") + 1]
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
