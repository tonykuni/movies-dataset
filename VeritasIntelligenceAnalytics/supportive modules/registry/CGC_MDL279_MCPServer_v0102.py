#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL279_MCPServer v0102 — 薄尾(v0101 一字不動):MCP 多露 2026-11-09 晚六項令 + 今日收尾的收據(全部只讀 · 零寫入 · 零網路)。

操作員 2026-11-09:「強化完善 VCGC MCP SDD 節省 TOKEN 工具最強化」。本版只加資源,不加動詞、不改協定:
  mutual/latest · mutual/latest-md          五系統互監矩陣(VIA_MutualMonitor)
  backup/manifest · backup/check            每日備份入倉 MANIFEST · 隔天檢查結果(VIA_DailyBackup)
  vdf/macro-hierarchy · vdf/macro-crosscheck VDF 總經階層 · AKShare × 官方交叉比對
  vrn2/lanes                                VRN-2 個股 / 非個股車道檢查
  vqg/catalog-options · vqg/export-vap      VQG 全庫選項 · export-vap(含 quant 節)
  workbench/ui-usertest · workbench/responsive 工作台逐鍵使用者測試 · 響應式實測
  graphify/latest                           Graphify 容器收據
  contract/system-receipt                   五系統自報收據契約冊
用法同 v0101:--serve [--root] · --client-config [--root] · --selftest(先 v0101(含 v0100)再本版 3 項)。
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
VERSION = "v0102"
HERE = Path(__file__).resolve().parent
_PRIOR_FILE = HERE / "CGC_MDL279_MCPServer_v0101.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL279_MCPServer_v0101", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL279_MCPServer_v0101"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.PRIOR                              # v0100 本體(Server · tool_specs · resource_specs)

NEW_RECEIPTS_0102 = {
    "mutual/latest": "VIA_Reports/mutual/MUTUAL_latest.json",
    "mutual/latest-md": "VIA_Reports/mutual/MUTUAL_latest.md",
    "backup/manifest": "docs/handoff/backup/BACKUP_MANIFEST_latest.json",
    "backup/check": "VIA_Reports/backup/CHECK_latest.json",
    "vdf/macro-hierarchy": "VIA_Reports/vdf/macro/VDF_MacroHierarchy_latest.json",
    "vdf/macro-crosscheck": "VIA_Reports/vdf/macro/VDF_MacroCrossCheck_latest.json",
    "vrn2/lanes": "VIA_Reports/vrn2/VRN2_LaneCheck_latest.json",
    "vqg/catalog-options": "VIA_Reports/vqg/vqg_catalog_options.json",
    "vqg/export-vap": "VIA_Reports/vqg/VQG_ExportVAP_latest.json",
    "workbench/ui-usertest": "VIA_Reports/workbench/UI_UserTest_latest.json",
    "workbench/responsive": "VIA_Reports/workbench/UI_Responsive_latest.json",
    "graphify/latest": "VIA_Reports/graphify/VIA_Graphify_latest.json",
    "contract/system-receipt": "supportive modules/registry/VIA_SystemReceipt_Contract_SSOT_v0100.json",
}
_PRIOR_KEYS = set(P0.RECEIPTS)
P0.RECEIPTS.update(NEW_RECEIPTS_0102)
P0.VERSION = VERSION
RECEIPTS, READ_VERBS, PROTOCOL = P0.RECEIPTS, P0.READ_VERBS, P0.PROTOCOL


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    import tempfile
    added = [k for k in NEW_RECEIPTS_0102 if k not in _PRIOR_KEYS]
    for k in added:                                   # 前版自測數資源數要原樣 → 先拿掉本版的 key,跑完再掛回
        P0.RECEIPTS.pop(k, None)
    try:
        rc = PRIOR.selftest()
    finally:
        P0.RECEIPTS.update(NEW_RECEIPTS_0102)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    with tempfile.TemporaryDirectory(prefix="via_mcp102_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        (via / "VIA_Reports" / "mutual").mkdir(parents=True)
        (via / "VIA_Reports" / "mutual" / "MUTUAL_latest.json").write_text('{"lamp": "RED", "systems": {"VAP": {"lamp": "GRAY"}}}', encoding="utf-8")
        srv = P0.Server(via, None)
        res = {r["name"] for r in P0.resource_specs(via)}
        chk("ⓐ 資源列 %d 份 = 前版 %d + 本版新 %d · 新 key 全在 · via_receipt enum 含新 key" % (len(res), len(_PRIOR_KEYS), len(added)), len(res) == len(_PRIOR_KEYS) + len(added) and set(NEW_RECEIPTS_0102) <= res
            and set(NEW_RECEIPTS_0102) <= set(next(t for t in P0.tool_specs() if t["name"] == "via_receipt")["inputSchema"]["properties"]["key"]["enum"]))
        rr = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/read", "params": {"uri": "via://mutual/latest"}})["result"]["contents"][0]
        miss = srv.handle({"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": "via://backup/check"}})["result"]["contents"][0]
        chk("ⓑ 讀新資源:互監矩陣讀到(VAP GRAY)· 沒有的(backup/check)照實說還沒有不炸", '"GRAY"' in rr["text"] and "還沒有" in miss["text"])
        cfg = client_config(via)
        chk("ⓒ client-config 的 command 指到本檔(v0102)", Path(__file__).name in json.dumps(cfg) and _PRIOR_FILE.name not in json.dumps(cfg))
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · 本版 %d 項 · 不過 %d(v0101 鏈 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", NAME, VERSION, len(ok), bad, rc), flush=True)
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
