#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0101 — 薄尾(v0100 一字不動):MCP「對接一切」= 多露 SettleAll 四張矩陣與各系統 / 工具的收據(只讀)· 多一個唯讀動詞 mcp doctor。

操作員 2026-11-06:「MCP 功能完善化對接一切」。v0100 露 15 個只讀動詞 + 11 份收據;本版把這兩天新出的東西也接上(全部只讀 · 零寫入 · 零網路):
  資源 +16:⑫ 系統矩陣 · ⑭ 模組矩陣 · VCGC 站表矩陣 · ⑬ VDF 引擎矩陣(json / md)· SETTLE 報告 md · VCGC 測試狀態冊 · VCGC 功能帳 · Agent OS status / skills ·
          VRN-2 RoundAll 收據 · VCGC 兩天新增功能整理 · 架構基線 B1–B5 對照 · VAP v0300 函式清冊。
  工具 +1:vcgc_mcp_doctor(主控台 v0192 的 `mcp doctor` · 只讀偵測各 AI 平台設定)。
  其餘(協定 · stdio · 白名單 · 拒寫 · client-config)全部沿用 v0100;--client-config 的 command 指到本檔。
用法同 v0100:--serve [--root] · --client-config [--root] · --selftest(先跑 v0100 的 12 項再跑本版 4 項)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None   # 本模組零網路(stdio);橋只為治理規則留名,不載入
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import json

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = "CGC_MDL279_MCPServer"
VERSION = "v0101"
_PRIOR_FILE = HERE / "CGC_MDL279_MCPServer_v0100.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0100", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)

NEW_RECEIPTS = {   # 資源 URI 尾段 → 相對 VIA 根的檔(只讀);全是各系統 / 工具自己寫的收據與矩陣
    "settle/system-matrix": "VIA_Reports/settle/VIA_SystemMatrix_latest.json",
    "settle/system-matrix-md": "VIA_Reports/settle/VIA_SystemMatrix_latest.md",
    "settle/module-matrix": "VIA_Reports/settle/VIA_ModuleMatrix_latest.json",
    "settle/module-matrix-md": "VIA_Reports/settle/VIA_ModuleMatrix_latest.md",
    "settle/station-matrix": "VIA_Reports/settle/VCGC_StationMatrix_latest.json",
    "settle/station-matrix-md": "VIA_Reports/settle/VCGC_StationMatrix_latest.md",
    "settle/vdf-engines": "VIA_Reports/settle/VDF_Engines_Matrix_latest.json",
    "settle/latest-md": "VIA_Reports/settle/SETTLE_latest.md",
    "vcgc/test-state": "VIA_Reports/vcgc/TEST_STATE_v0101.json",
    "vcgc/function-ledger": "supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl",
    "agent-os/status": "VIA_Reports/agent_os/VIA_AgentOS_v0102_status.json",
    "agent-os/skills": "VIA_Reports/agent_os/VIA_AgentOS_v0102_skills.json",
    "vrn2/roundall": "VIA_Reports/vrn2/VRN2_RoundAll_latest.json",
    "matrix/new-functions": "docs/handoff/ai/VCGC_NewFunctions_20261104_06.md",
    "matrix/blueprint-b1b5": "docs/handoff/ai/VIA_Blueprint_B1B5_Mapping_20261106.md",
    "vap/function-inventory": "functional modules/VAP/intake/allinone_v0300/VAP_Function_Inventory_v0300.json",
}
PRIOR.RECEIPTS.update(NEW_RECEIPTS)
PRIOR.READ_VERBS["vcgc_mcp_doctor"] = (["mcp", "doctor"], "MCP 設定引擎環境偵測(主控台 v0192 動詞 mcp doctor · 只讀 · 不寫任何平台設定)")
PRIOR.VERSION = VERSION                      # serve / selftest 的署名跟著尾版
RECEIPTS, READ_VERBS, PROTOCOL = PRIOR.RECEIPTS, PRIOR.READ_VERBS, PRIOR.PROTOCOL


def client_config(via: Path) -> dict:
    """同 v0100,但 command 指到本檔(尾版)。"""
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    with tempfile.TemporaryDirectory(prefix="via_mcp101_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "VIA_Reports" / "settle").mkdir(parents=True)
        (via / "VIA_Reports" / "settle" / "VCGC_StationMatrix_latest.json").write_text('{"counts": {"GREEN": 3}}', encoding="utf-8")
        srv = PRIOR.Server(via, None)
        names = {t["name"] for t in PRIOR.tool_specs()}
        res = {r["name"] for r in PRIOR.resource_specs(via)}
        chk("ⓐ 工具多 vcgc_mcp_doctor(argv mcp doctor)· via_receipt 的 key 列舉含 16 份新收據", "vcgc_mcp_doctor" in names and READ_VERBS["vcgc_mcp_doctor"][0] == ["mcp", "doctor"]
            and set(NEW_RECEIPTS) <= set(next(t for t in PRIOR.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]["key"]["enum"]))
        chk("ⓑ 資源列 %d 份 = v0100 11 + 本版 16 · 新 key 全在" % len(res), len(res) == 27 and set(NEW_RECEIPTS) <= res, sorted(res - set(NEW_RECEIPTS))[:3])
        rr = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://settle/station-matrix"}})["result"]["contents"][0]
        miss = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "via://vap/function-inventory"}})["result"]["contents"][0]
        chk("ⓒ 讀新資源:站表矩陣 JSON 讀到 · 沒有的(VAP 清冊)照實說還沒有不炸", '"GREEN": 3' in rr["text"] and "還沒有" in miss["text"])
        cfg = client_config(via)
        chk("ⓓ client-config 的 command 指到本檔(v0101)而不是 v0100", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0100 12 項 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = None
        if "--root" in args:
            root = args[args.index("--root") + 1]
        via = Path(root).resolve() if root else PRIOR.VIA_DEFAULT
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    return PRIOR.main(args)


def __getattr__(name):
    return getattr(PRIOR, name)


if __name__ == "__main__":
    sys.exit(main())
