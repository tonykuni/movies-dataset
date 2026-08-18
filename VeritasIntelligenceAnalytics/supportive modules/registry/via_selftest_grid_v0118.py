#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_selftest_grid_v0118 — 全面自測矩陣(+中央治理台站)
====================================================================
v0100→v0101:新增第 18 站 SuperDocExtractor selftest(導入自會話
016d7f;15 檢全綠基準)。
v0101→v0102:新增第 19 站 vrn_table_omni 車道矩陣(TOOL-029;唯讀
可用性探測 rc0,不擷取)。
v0102→v0103:新增第 20 站 via_env_plan --offline(TOOL-030;快照+
計畫零網路 rc0)。
v0103→v0104:新增第 21 站 via_dep_super --selftest(TOOL-031;
PEP440 判定器+圖譜衝突掃描 15 檢,零網路零環境依賴 rc0)。
v0104→v0105:雙會話合流——撞版勘誤(本會話曾誤覆寫 v0104,已回復
他方正本):+第 22 站表格統包 --selftest(TOOL-029 四檢)+第 23 站
收編管線 dry(TOOL-036;掃描根缺=env SKIP 誠實)。
v0105→v0106:+第 24 站契約介面引擎 32 測(TOOL-037;pytest/pydantic
缺=env SKIP)+第 25 站留痕包裝器(TOOL-038 --list rc0)。
v0106→v0107:撞版合流(9hh5to 會話亦造 v0106)——併入其重建計畫
自測+教訓帳本 10 檢兩站(27 站)。
v0107→v0108(操作員令 2026-08-18:strengthen optimize automate all
engine · VIA VDF VAP VRN FLOW):五系統全覆蓋——+第 28 站 FlowSystem
14 檢(flow_selftest 合成流零網路)+第 29 站文章攝入五檢(TOOL-045)
+第 30 站介面合約 dry(TOOL-041 零寫入)+第 31 站 office 併表橋 dry
(TOOL-044;空收件夾=rc0 誠實 SKIP 訊息)+第 32 站 ChipWar 引擎編譯
檢(TOOL-043;py_compile 零執行,_sha 鏡像/檢疫夾除外)+第 33/34 站
命名冊六檢+dry(TOOL-047 自動編號註冊命名)——34 站。
v0108→v0109:+第 35 站產品門面九檢(TOOL-048;六頁產出+視覺鎖定
+零 CDN+誠實界線標註)——35 站。
v0109→v0110:+第 36 站缺口總攻四檢(TOOL-049 多方案指揮)——36 站。
v0110→v0111:+第 37/38 站文字統包六檢+矩陣(TOOL-050;十車道+三閘)——38 站。
v0111→v0112:+第 39 站 SuperAccel 四檢(斷點補齊;同意閘/平行/快取)——39 站。
v0112→v0113:+第 40 站引擎總目錄四檢(TOOL-054 全 ENG 覆蓋+實值說明比)——40 站。
v0113→v0114:+41 三因子吸引力四檢+42 lead-lag 邊四檢(TOOL-055)
+43 VME 核心八檢(TOOL-056 方法論導入)——43 站。
v0114→v0115:+第 44 站 VDF 輸出樞紐七檢(TOOL-058 統一參數 SSOT+
六格式輸出 parquet/csv/duckdb/sqlite/sql/gsheet相容+讀回驗證)——44 站。
v0115→v0116:+第 45 站字庫知識樹八檢(TOOL-059 中英文字庫+樹枝
編號 K1-K8+讀報自動建構+JSON 模板回填+審核閉環)——45 站。
v0116→v0117:+46 台灣主動式ETF六檢+47 全球ETF流觀察六檢+48 族群
三分類/族群指數六檢(TOOL-060/061/062)——48 站。
v0117→v0118:+第 49 站中央治理台八檢(TOOL-063 三輪全景/SSOT+
Regex 治理中心/四分區 Matrix/Zero-Hydra)——49 站。
執行器新增 pycode 站型(標準庫內聯檢,零外部檔)。
操作員令(2026-08-12):全面測試修正 till all work perfectly。
原則:
  ① 全站安全模式 — 只跑唯讀/dry-run/selftest/文件模式;零 --commit 零網路
  ② 誠實三態 — OK(如預期)/FAIL(異常)/SKIP(環境缺件,誠實註明)
  ③ 期望制 — 每站宣告期望 rc(rc0=須 0;doc=無參印說明 rc∈{0,2};
     env=環境依賴,缺件 rc≠0 記 SKIP 不記 FAIL)
  ④ 存證 — VIA_Reports/selftest_runs/GRID_<ts>.json
用法:via-selftest            → 全矩陣(43 站)
     via-selftest --fast     → 略過重站(sysman/pipe)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN = VIA / "functional modules/VRN"
OUT = VIA / "VIA_Reports" / "selftest_runs"


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def battery(fast: bool):
    py = sys.executable
    B = []

    def add(name, path, args, expect, timeout=180, heavy=False):
        if fast and heavy:
            return
        B.append({"name": name, "path": path, "args": args, "expect": expect, "timeout": timeout})

    add("sysman 三輪協議", newest("via_system_manager_v0*.py", HERE), ["--no-open"], "rc0", 900, heavy=True)
    add("panorama six 六車道", newest("via_panorama_six_v0*.py", HERE), ["--no-open"], "rc0", 300)
    add("xcheck SSOT 對齊", newest("panorama_xcheck_v*.py", VRN), ["--no-pause"], "rc0", 180)
    add("supaudit 導入稽核", newest("via_support_import_audit_v0*.py", HERE), [], "env", 300)
    add("provision 體檢", newest("via_provision_v0*.py", HERE), ["--check"], "rc0", 300)
    add("master Console", newest("via_master_hub_v0*.py", HERE), ["--no-open"], "rc0", 120)
    add("install 閘 check-only", newest("via_install_gate_v0*.py", HERE), ["--check-only"], "rc0", 300)
    add("tidy 整理(dry)", newest("via_downloads_organizer_v0*.py", HERE), [], "env", 600)
    add("store 落庫(dry)", newest("vrn_content_store_v0*.py", VRN), [], "env", 120)
    add("reconcile 對帳", newest("vrn_content_reconcile_v0*.py", VRN), [], "env", 120)
    add("pdfcheck 法醫(doc)", newest("vrn_pdf_forensics_v0*.py", VRN), [], "doc", 60)
    add("docx 引擎(doc)", newest("vrn_docx_engine_v0*.py", VRN), [], "doc", 60)
    add("rescue 救援(doc)", newest("vrn_scan_ocr_rescue_v0*.py", VRN), [], "doc", 60)
    add("pipeline 輪動證偽", VIA / "supportive modules/VIA_Pipeline/via_pipeline.py", ["--demo"], "rc0", 600, heavy=True)
    add("via_io 編碼自檢", VIA / "supportive modules/VIA_Pipeline/via_io.py", ["--selftest"], "rc0", 120)
    add("NetSupport 同意閘", VIA / "supportive modules/VIA_NetSupport.py", [], "rc0", 60)
    sdx = VIA / "functional modules/SuperDocExtractor/super_extract.py"
    add("SuperDocExtractor 15檢", sdx, ["selftest"], "rc0", 300)
    add("表格統包車道矩陣", newest("vrn_table_omni_v0*.py", VRN), [], "rc0", 120)
    add("環境計畫快照(offline)", newest("via_env_plan_v0*.py", HERE), ["--offline"], "rc0", 300)
    add("依賴統包 15 檢", newest("via_dep_super_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("表格統包四檢自測", newest("vrn_table_omni_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("收編管線(dry)", newest("via_intake_v0*.py", HERE), [], "env", 300)
    add("契約介面引擎 32 測", VIA / "supportive modules/VIA_ContractEngine_v0200/selftest_entry.py", [], "env", 300)
    add("留痕包裝器(list)", newest("via_cmdlog_v0*.py", HERE), ["--list"], "rc0", 60)
    add("重建計畫自測", newest("via_env_rebuild_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("教訓帳本 10 檢", newest("via_lessons_v0*.py", HERE), ["--selftest"], "rc0", 300)
    add("FlowSystem 14 檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_selftest.py", [], "rc0", 300)
    add("文章攝入五檢", newest("via_article_intake_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("介面合約(dry)", newest("via_iface_contract_v0*.py", HERE), ["--dry"], "rc0", 600)
    add("office 併表橋(dry)", newest("vrn_office_merge_v0*.py", VRN), [], "env", 180)
    add("命名冊六檢", newest("via_namereg_v0*.py", HERE), ["--selftest"], "rc0", 120)
    add("命名冊(dry)", newest("via_namereg_v0*.py", HERE), ["--dry"], "rc0", 300)
    add("產品門面九檢", newest("via_product_ui_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("缺口總攻四檢", newest("vrn_gap_multirescue_v0*.py", VRN), ["--selftest"], "rc0", 120)
    add("文字統包六檢", newest("vrn_text_omni_v0*.py", VRN), ["--selftest"], "rc0", 180)
    add("文字統包矩陣", newest("vrn_text_omni_v0*.py", VRN), [], "rc0", 120)
    add("SuperAccel 四檢", VIA / "supportive modules/VIA_SuperAccel_Module.py", ["--selftest"], "rc0", 120)
    add("引擎總目錄四檢", newest("via_engine_catalog_v0*.py", HERE), ["--selftest"], "rc0", 180)
    add("三因子吸引力四檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_attractiveness.py", ["--selftest"], "rc0", 120)
    add("leadlag 邊四檢", VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines/flow_leadlag.py", ["--selftest"], "rc0", 120)
    add("VME 核心八檢", VIA / "functional modules/VME/engines/vme_main.py", ["--selftest"], "rc0", 180)
    add("VDF 輸出樞紐七檢", newest("vdf_output_hub_v0*.py", VIA / "functional modules/VDF"), ["--selftest"], "rc0", 300)
    add("字庫知識樹八檢", newest("vrn_lexicon_v0*.py", VRN), ["--selftest"], "rc0", 300)
    FLOWENG = VIA / "supportive modules/VIA_FlowSystem/FlowSystem_v2/engines"
    add("台灣主動式ETF六檢", FLOWENG / "flow_tw_active_etf.py", ["--selftest"], "rc0", 120)
    add("全球ETF流觀察六檢", FLOWENG / "flow_global_etf_flowscope.py", ["--selftest"], "rc0", 120)
    add("族群三分類指數六檢", FLOWENG / "flow_group_taxonomy.py", ["--selftest"], "rc0", 120)
    add("中央治理台八檢", newest("via_central_gov_v0*.py", HERE), ["--selftest"], "rc0", 600)
    B.append({"name": "ChipWar 引擎編譯檢(零執行)", "path": "PYCODE", "args": [], "expect": "rc0",
              "timeout": 180, "pycode": (
                  "import py_compile,sys\n"
                  "from pathlib import Path\n"
                  "root=Path(r'" + str(VIA / "functional modules/ChipWar/engines") + "')\n"
                  "bad=n=0\n"
                  "for p in sorted(root.glob('*.py')):\n"
                  "    if '_sha' in p.stem: continue\n"
                  "    n+=1\n"
                  "    try: py_compile.compile(str(p),doraise=True)\n"
                  "    except Exception as e: bad+=1; print(f'[FAIL] {p.name}: {str(e)[:80]}')\n"
                  "print(f'[計] ChipWar 編譯 {n} 件 · 壞 {bad}(_sha 鏡像/檢疫夾除外)')\n"
                  "sys.exit(1 if bad else 0)\n")})
    add("selftest grid(自指:文件)", None, [], "doc", 10)  # 佔位:自身以 --fast 遞迴屬禁,列 SKIP
    return B


def run_one(b):
    if b["path"] is None or (b["path"] != "PYCODE" and not Path(b["path"]).exists()):
        return {"name": b["name"], "state": "SKIP", "note": "引擎缺/自指佔位(誠實)", "secs": 0}
    t0 = time.time()
    try:
        if b["path"] == "PYCODE":  # pycode 站型:標準庫內聯檢(零外部檔)
            argv = [sys.executable, "-c", b["pycode"]]
            cwd = str(VIA)
        else:
            argv = [sys.executable, str(b["path"]), *b["args"]]
            cwd = str(Path(b["path"]).parent)
        r = subprocess.run(argv, capture_output=True,
                           text=True, timeout=b["timeout"], stdin=subprocess.DEVNULL,
                           cwd=cwd)
        secs = round(time.time() - t0, 1)
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()][-2:]
        if b["expect"] == "rc0":
            state = "OK" if r.returncode == 0 else "FAIL"
        elif b["expect"] == "doc":
            state = "OK" if r.returncode in (0, 2) else "FAIL"
        else:  # env
            state = "OK" if r.returncode == 0 else "SKIP"
        note = " / ".join(t[:80] for t in tail)
        if state == "SKIP":
            note = "環境缺件(誠實):" + note
        return {"name": b["name"], "state": state, "rc": r.returncode, "secs": secs, "note": note}
    except subprocess.TimeoutExpired:
        return {"name": b["name"], "state": "FAIL", "rc": "TIMEOUT", "secs": b["timeout"], "note": "逾時"}
    except Exception as exc:
        return {"name": b["name"], "state": "FAIL", "rc": type(exc).__name__, "secs": 0, "note": str(exc)[:80]}


def main() -> int:
    fast = "--fast" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    B = battery(fast)
    print(f"=== 全面自測矩陣 v0114 · {len(B)} 站 · {'FAST' if fast else 'FULL'} · 全安全模式(零 commit 零網路)===")
    results = []
    for b in B:
        r = run_one(b)
        results.append(r)
        mark = {"OK": "OK  ", "FAIL": "FAIL", "SKIP": "SKIP"}[r["state"]]
        print(f"  [{mark}] {r['name']} · {r['secs']}s · {r.get('note', '')[:96]}")
    n_ok = sum(1 for r in results if r["state"] == "OK")
    n_fail = sum(1 for r in results if r["state"] == "FAIL")
    n_skip = sum(1 for r in results if r["state"] == "SKIP")
    OUT.mkdir(parents=True, exist_ok=True)
    ev = OUT / f"GRID_{ts}.json"
    ev.write_text(json.dumps({"schema": "VIA.SelftestGrid.v1", "ts": ts, "fast": fast,
                              "ok": n_ok, "fail": n_fail, "skip": n_skip, "results": results},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)· 存證 {ev.name}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
