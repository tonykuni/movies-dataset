#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL149_VeritasCentralGovernanceConsole v0113 — VCGC(批568:⑨ 的第二個洩漏口,以及一道「以後不准再有第三個」的閘)
v0112→v0113(批568 操作員工作站實錄:⑨ 印的是 **BLOCKED_PANORAMA**,不是我本境修的 BLOCKED_UNITEST):
  我在批567 寫下 LL114「引擎有幾個資料來源,自測就要把**每一個**都關進沙盒」,然後**自己只關了一個**。
  `check()` 讀兩個真機器來源:① `rungate()`(批567 已關:VIA_RUNGATE_LATEST + VIA_RUNGATE_DIR)
  ② `REPORTS/panorama/PANORAMA_latest.json`——**寫死路徑、沒有覆寫鍵**,而且它會把 install 直接覆蓋成
  BLOCKED_PANORAMA。本境沒有 panorama 夾,那道閘是啞的,所以我看到的是 UNITEST;操作員機器上有一份
  未完成的全景報告,八個合成案例**全部**被覆蓋成 BLOCKED_PANORAMA。同一個檢、兩台機器、兩種紅法,
  而核可邏輯一行都沒錯。(我連自己查證時都再犯一次:`grep | head -5` 把 v0111/v0112 切掉,
  讓我一度以為新版沒有這道閘——批567 剛立的 L62 打自己的臉。)
  本版兩件:
  ① `PANORAMA_LATEST` 比照 RunGate 慣例加 `VIA_PANORAMA_LATEST` 覆寫鍵(生產預設路徑不變),⑨ 一併關進沙盒。
  ② 新增 ⑳ **來源閘**:用 AST 掃 `check()/rungate()/_rungate_merged()`,列出這條路真正讀的每一個
     `REPORTS / …` 磁碟來源,要求**每一個都配一個 VIA_* 覆寫鍵**,而且自測 ⑨ 區塊**每一個鍵都要指進暫存夾**。
     少一個就報紅並指名是哪一個——「底下還有一層」這件事,從此由機器講,不靠我記得。
  十九檢 → 二十檢。
CGC_MDL149_VeritasCentralGovernanceConsole v0112 — Veritas Central Governance Console(VCGC;批567 ⑨ 不再被機器狀態判成紅燈)
v0111→v0112(批567「自測時測字完成」同族:一個**看機器臉色**的檢,和一個被切掉的訊息一樣不誠實):
  ⑨ 安裝核可是**合成檢**——自測自己在暫存夾寫八份 RunGate 報告,用 VIA_RUNGATE_LATEST 指過去,
  驗「缺/單族/零站/零庫/壞值/未來/過期都 BLOCKED,雙族完整 GREEN 才 INSTALL_OK」。
  但 `_rungate_merged()`(批517 起)會另外掃**真機器**的 `VIA_Reports/rungate/RUNGATE_2*.json` 史,
  而且史**優先於**傳進來的那一份。於是只要機器上有一份 24h 內的真報告,合成的那八份就被蓋掉,
  ⑨ 當場紅。本境量到的正是這個:批566 跑 OneShot 留下 2.2 小時前一份 verdict=YELLOW 的真報告,
  ⑨ 印出「雙族=BLOCKED_UNITEST」——**核可邏輯一行沒變,紅燈是機器狀態換來的**(LL103 同族的判錯紅燈)。
  修法只動自測、**零生產邏輯變更**:⑨ 連 `VIA_RUNGATE_DIR` 一起指向暫存夾(引擎本來就吃這個覆寫鍵),
  讓史掃描也關進沙盒;跑完照原樣還原兩個鍵。合成檢就該只驗自己合成的東西。
CGC_MDL149_VeritasCentralGovernanceConsole v0111 — Veritas Central Governance Console(VCGC;批520 批號改讀政策庫,不再每批改常數)
v0110→v0111(批520):BATCH 不再寫死——讀 VIA_Policy_Laws_SSOT_v0100.json 的 batch(政策庫是批號正本;LL 每批為改一個常數就出新版=假版本);讀不到退 519。
CGC_MDL149_VeritasCentralGovernanceConsole v0110 — Veritas Central Governance Console(VCGC;批519 十二段 U/I 對接與工作流:中央自適應連結)
v0109→v0110(批519 操作員令「中央可以自適應式連結對接 U/I · WORKFLOW 圖可重整不同引擎 · 自動跳出實測真實結果 · VDF 資料庫分類歸納摘要」):
  讀 CGC_MDL153 WorkflowComposer 落的 UI_CONTRACT_latest.json(頁/擁有者/在不在/新鮮/再生令)+ WORKFLOW_latest.json(最新一跑)+ DB_SUMMARY_latest.json(庫分類燈)
  → 十二段 + 頁卡/頁段:頁在=連結(file://)、不在=ABSENT 誠實;工作流最新真跑逐節點;庫分類每類一燈;十九檢 +⑲。
CGC_MDL149_VeritasCentralGovernanceConsole v0109 — Veritas Central Governance Console(VCGC;批518 中央治理主控台 G17 循環判讀入十一段)
v0108→v0109(批518 操作員貼回 via-cgfamily:console RED=G17 3 個循環依賴 + 五 WARN):FAMILY_latest.json 的 console.cycles_reading(CGC_MDL150 v0103 cycles 動詞:
  URN→檔名→區)入十一段一行 + 頁段一行:活樹圈數才是債,退役/收容/存檔內互呼不算(L38);缺=ABSENT 誠實;十八檢 +⑱。
CGC_MDL149_VeritasCentralGovernanceConsole v0108 — Veritas Central Governance Console(VCGC;批517 安裝核可看兩族各自最新一跑)
v0107→v0108(批517 操作員實錄:via-rungate vdf GREEN(早上)+ via-rungate vrn GREEN(晚上),via-vcgc 仍 BLOCKED_UNITEST——
  rungate() 只讀 RUNGATE_latest.json(最後一跑只有 vrn)= 判錯的紅燈):改讀 RUNGATE_*.json 史,每個必驗族取 24h 內最新一筆(VIA_RUNGATE_DIR 可覆寫史夾);
  總燈=各族取用那筆的最壞;十七檢 +⑰。
v0106→v0107(批516 操作員令「除錯成功後才 VTMRA · TA-LIB 確認測試無誤」):+vtmra()(CGC_MDL152 VTMRA_latest.json:七成員態 + 判定;TA-Lib 態在內)
  於四段/頁卡/status;批 516;十六檢 +⑯。
v0105→v0106(批515 操作員令「VETF 改名為 VATETF;直接抓 VDF 擷取的資料庫來用,他是應用端;以 VIA 為中央管理全部 SSOT 化 唯一接觸口」):
  十段/頁標題 VRN / VDF / VATETF(舊名 VETF;契約 names 鍵);批 515;十五檢不變(結構判準)。
v0104→v0105(批514 操作員令「將中央管理系統不足的部分補上」):+十一段 中央治理家族(CGC_MDL150 FAMILY_latest.json:VIA-SYS-MGR-001 主控台 ·
  VIA-GOV-ENG-001 詞彙引擎 · VIA-SYS-MGR-003 下行控制 · VIA-SYS-ENG-003 檔案優先序 · 同名整併;五成員 md5 對冊 + 各自最新快照;誠實 ABSENT)於一頁/頁卡/status;
  RunGate 段帶 host.pythonhome_scrubbed(L32 母殼 PYTHONHOME 撤除存證);十五檢 +⑮。
v0103→v0104(批511 併線):並行線 v0102/v0103(INSTALL_OK 兩族同時在位、registry-sync 元件編號冊唯一寫入口、panorama 契約)+ 本線 批508 環境復原段
  (RECOVER_latest.json;MDL135 recover;律 L24)於二段/頁卡/status;政策庫冊聯集(L26–L29、LL15–LL18 來自並行線 panorama-v0103,orig_id 保留)。
v0101→v0102(批508 結案):① INSTALL_OK 強制 VDF+VRN 兩族同時在位、家族境/必要庫/自測站全綠且 24h 內；
  零站、SKIP、只跑一族都 BLOCKED_UNITEST。② VCGC 成為元件自動編號冊唯一寫入口：registry-sync 預設只列，
  --apply 才把尾版引擎/模組/類別/函數/功能/短令/工具套件/環境以穩定編號寫入 append-only SSOT。
  ③ 註冊稽核分開呈現「中央編號冊覆蓋」與「操作介面掛載」，不再用 ENG/MDL 編號片段模糊命中假裝已登。
v0100→v0101(批507 操作員問「多 AI 寫作要怎麼接手不掉球、格式如何、長久使用」):一頁交接 +〇 接手提示詞(docs/VIA_AI_Handover_Prompt_v*.md 尾版全文嵌入)
  +九 掉球清單(docs/VIA_DroppedBalls_*.md 尾版);格子 PYCODE/自指站標「特殊」不當缺;十二檢。
====================================================================
操作員令:「相關中央控管為 Veritas Central Governance Console,為此系統連接各模組引擎的唯一對接口,
控管 政策庫 · 邏輯庫 · 因子庫 · 資料庫 · VIA 引擎調度 · 多矩陣實測結果;不要丟失參數及指令;
所有引擎/模組/功能/工具/環境都要註冊;lesson-learned;環境統一測式無誤後才可核可安裝;
詳細 handover report 整合成同一頁 + 環境工具管理 + 自動編號註冊表。」(律 L20)
Zero-Hydra:本台**預設只讀**——各庫各冊各引擎的正主不變；唯一例外是明示
`registry-sync --apply` 原子寫中央元件編號冊，與 `page --publish` 發布同頁交接。
  政策庫  VIA_Policy_Laws_SSOT_v*.json(律+lessons)+ ENG082 policy_factors()(攤平入 via_policy_factors)
  邏輯庫  ENG082 LOGIC_latest.json(件/法/後端健康)+ sync_state(全庫同步對帳)
  因子庫  SUP_MDL748 policy_rows()(AllInOne + FDS 兩本冊)
  資料庫  VIA_DB_Table_SSOT(冊)+ DATAHOME_CATALOG_latest.json(家內庫/湖)
  引擎調度 CGC_MDL095 Deck 任務冊 + VIA_InputConsole_Spec 項 + CGC_MDL064 格子站 + Register-VIA-Commands 指令(含用法/參數)
  多矩陣  ENGINE_BUS_latest.json(五矩陣)+ RUNGATE_latest.json(環境統一測式)
  環境工具 TOOLS_PLAN_latest.json(MDL135 tools)
  環境復原 RECOVER_latest.json(MDL135 recover;律 L24 還原前次→順序裝→_M/_H 單獨隔離)
  註冊表  VIA_AutoCode_Registry(自動編號類別 current + 台帳尾)
  註冊稽核 尾版家族×中央元件編號冊；顯式操作介面(規格/Deck/格子/Register/Manager)另列缺口，不模糊命中
  安裝核可 L19:RunGate 24h 內 VDF+VRN 兩族完整 GREEN → INSTALL_OK;否則 BLOCKED_UNITEST
用法:python3 CGC_MDL149_VeritasCentralGovernanceConsole_v0102.py [status|page|onepage|audit|register-plan|registry-sync|check] [--publish|--apply] | --selftest
  page/onepage 預設落 VIA_Reports/vcgc/(不入 git、不弄髒工作樹);--publish 才複製到 ui_support 頁與 docs/VIA_Handover_ONEPAGE.md + 倉根 VIA_HANDOVER_LATEST.md(我 commit 時的手)
律:零 CDN;零彈窗;零網路;預設只讀；只有 page --publish 與 registry-sync --apply 明示寫入；誠實 ABSENT(報告不在=講不在,不編)。
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


import ast
import html
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent
REPORTS = VIA / "VIA_Reports"
OUTDIR = REPORTS / "vcgc"
VERSION = "0113"
def _batch_from_laws() -> int:
    """批520:批號正本=政策庫 batch(「批520」→ 520);讀不到退 519。"""
    try:
        _b = json.loads((HERE / "VIA_Policy_Laws_SSOT_v0100.json").read_text(encoding="utf-8")).get("batch") or ""
        return int(re.sub(r"\D", "", str(_b)) or 519)
    except Exception:
        return 519


BATCH = _batch_from_laws()
UNITEST_MAX_AGE_H = 24.0
INSTALL_REQUIRED_FAMILIES = ("vdf", "vrn")
COMPONENT_REGISTRY = HERE / "VIA_Component_Inventory_SSOT_v0100.json"


def _newest(root: Path, pat: str) -> Path | None:
    c = sorted(root.glob(pat))
    return c[-1] if c else None


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _json(p: Path | None) -> dict | None:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig")) if p and Path(p).is_file() else None
    except Exception:
        return None


def _age_h(ts: str) -> float | None:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return (datetime.now() - datetime.strptime(str(ts)[:19], fmt)).total_seconds() / 3600.0
        except Exception:
            pass
    return None


def _nat(value) -> int:
    """報告計數的 fail-closed 轉換；壞值/負值不得因相等而假綠。"""
    try:
        value = int(value)
        return value if value >= 0 else -1
    except (TypeError, ValueError):
        return -1


# ────────────────────────── 讀各庫各冊(只讀) ──────────────────────────
def laws() -> dict:
    j = _json(_newest(HERE, "VIA_Policy_Laws_SSOT_v*.json"))
    return {"state": "OK" if j else "ABSENT", "laws": (j or {}).get("laws", []), "lessons": (j or {}).get("lessons", []), "src": (j or {}).get("batch", "")}


def ledger() -> dict:
    j = _json(HERE / "VIA_AutoCode_Registry_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    L = j.get("ledger", [])
    return {"state": "OK", "n": len(L), "tail": L[-8:], "categories": {k: v.get("current") for k, v in (j.get("categories") or {}).items()},
            "components": len(j.get("components") or {}), "updated_at": j.get("updated_at")}


def deck_tasks() -> dict:
    p = _newest(HERE, "CGC_MDL095_DeckServer_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}}
    try:
        m = _load("vcgc_deck", p)
        t = m.task_registry()
        return {"state": "OK", "src": p.name, "tasks": {k: {"zh": v.get("zh", ""), "argv": [str(x) for x in v.get("argv", [])], "net": bool(v.get("net"))} for k, v in t.items()}}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "tasks": {}}


def spec_items() -> dict:
    j = _json(HERE / "VIA_InputConsole_Spec_v0100.json")
    if not j:
        return {"state": "ABSENT", "items": []}
    items = []

    def walk(o, fam):
        if isinstance(o, dict):
            if "id" in o and ("engine" in o or "state" in o):
                e = o.get("engine") or {}
                items.append({"family": fam, "id": o["id"], "zh": o.get("zh", ""), "glob": e.get("glob", ""), "dir": e.get("dir", ""), "verb": e.get("verb", []),
                              "params": o.get("params", []), "net": bool(o.get("net")), "state": o.get("state", "")})
            for k, v in o.items():
                walk(v, k if k in ("vdf", "vrn", "vap") else fam)
        elif isinstance(o, list):
            for x in o:
                walk(x, fam)
    walk(j.get("families", {}), "")
    return {"state": "OK", "items": items, "param_kinds": list((j.get("param_kinds") or {}).keys())}


def grid_stations() -> dict:
    p = _newest(HERE, "CGC_MDL064_SelftestGrid_v*.py")
    if not p:
        return {"state": "ABSENT", "stations": []}
    try:
        m = _load("vcgc_grid", p)
        B = m.battery(False)
        st = []
        for b in B:
            pth = str(b["path"]) if b.get("path") else ""
            special = (pth in ("", "PYCODE")) or ("自指" in b["name"])
            st.append({"name": b["name"], "path": pth, "present": ("特殊" if special else (Path(pth).is_file())), "args": b.get("args", [])})
        return {"state": "OK", "src": p.name, "stations": st}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}", "stations": []}


def register_cmds() -> dict:
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if not p:
        return {"state": "ABSENT", "cmds": []}
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    cmds, aliases = [], {}
    for i, ln in enumerate(lines):
        m = re.match(r"^function global:(via-[A-Za-z0-9\-]+)", ln)
        if m:
            name = m.group(1)
            usage = ""
            for j in range(i - 1, max(-1, i - 8), -1):
                if lines[j].startswith("#") and name in lines[j]:
                    usage = lines[j].lstrip("# ").strip()
                    break
            cmds.append({"cmd": name, "usage": usage[:220], "line": i + 1})
        m2 = re.match(r"^Set-Alias -Name (\S+) -Value (via-[A-Za-z0-9\-]+)", ln)
        if m2:
            aliases.setdefault(m2.group(2), []).append(m2.group(1))
    for c in cmds:
        c["aliases"] = aliases.get(c["cmd"], [])
    return {"state": "OK", "src": p.name, "cmds": cmds}


def manager_names() -> dict:
    p = _newest(VIA, "VIA_SYSTEM_MANAGER_v*.py")
    if not p:
        return {"state": "ABSENT", "tasks": {}, "engines": {}}
    s = p.read_text(encoding="utf-8", errors="replace")

    def block(key):
        m = re.search(key + r"\s*=\s*\{(.*?)\n\}", s, flags=re.S)
        return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1))) if m else {}
    return {"state": "OK", "src": p.name, "tasks": block("TASK_FORMAL_NAMES"), "engines": block("ENGINE_FORMAL_NAMES")}


def db_sheet() -> dict:
    j = _json(HERE / "VIA_DB_Table_SSOT_v0100.json")
    if not j:
        return {"state": "ABSENT"}
    t = j.get("tables", [])
    return {"state": "OK", "n": len(t), "all_home": sum(1 for x in t if x.get("db_scope") == "all_home"), "batch": j.get("batch", ""), "dbs": sorted({x.get("db", "") for x in t})}


def datahome() -> dict:
    j = _json(REPORTS / "datahome" / "DATAHOME_CATALOG_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "VIA_Reports/datahome/DATAHOME_CATALOG_latest.json 不在(via-datahome catalog)"}
    return {"state": "OK", "home": j.get("home", ""), "dbs": len(j.get("by_name") or {}), "tables": len(j.get("by_table") or {}), "lakes": len(j.get("lake") or []), "ts": j.get("ts", "")}


def logic() -> dict:
    p = _newest(VIA / "functional modules" / "VRN", "VRN_ENG082_ExtractionLogic_v*.py")
    if not p:
        return {"state": "ABSENT"}
    try:
        m = _load("vcgc_eng082", p)
        d = m.load_latest()
        files = d.get("files") or {}
        by: dict = {}
        for r in files.values():
            by[r.get("verdict")] = by.get(r.get("verdict"), 0) + 1
        out = {"state": "OK", "src": p.name, "files": len(files), "verdicts": by, "backends": {k: v.get("state") for k, v in (d.get("backends") or {}).items()},
               "broken": list(m.broken_backends()), "policy_rows": len(m.policy_factors())}
        try:
            ss = m.sync_state(quiet=True)
            out["sync"] = {"hash": ss.get("hash"), "counts": dict(ss.get("counts") or {}), "dbs": len(ss.get("dbs") or [])}
        except Exception as exc:
            out["sync"] = {"state": f"BROKEN {type(exc).__name__}"}
        try:
            out["handover"] = m.handover_copies(quiet=True)
        except Exception:
            pass
        return out
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}:{str(exc)[:60]}"}


def factors() -> dict:
    p = _newest(VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL748_FinancialLogicHub_v*.py")
    if not p:
        return {"state": "ABSENT"}
    try:
        m = _load("vcgc_748", p)
        rows = m.policy_rows()
        by: dict = {}
        for r in rows:
            by[r["source"]] = by.get(r["source"], 0) + 1
        m.allinone(); m.fds()
        return {"state": "OK", "src": p.name, "rows": len(rows), "by_source": by, "mounts": dict(m._M.get("why") or {})}
    except Exception as exc:
        return {"state": f"BROKEN {type(exc).__name__}"}


def tools_plan() -> dict:
    j = _json(REPORTS / "env_governance" / "TOOLS_PLAN_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "TOOLS_PLAN_latest.json 不在(via-envtools)"}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "counts": j.get("counts", {}), "risk": j.get("risk_counts", {}), "stages": len(j.get("stages", [])),
            "unrouted": len(j.get("unrouted", [])), "hold": len(j.get("whitelist_hold", [])), "envs": [(e.get("name"), e.get("state")) for e in j.get("envs", [])][:24]}


def recover_plan() -> dict:
    """批508 律 L24:環境復原計畫(MDL135 recover;plan 唯讀;--execute --approve 才跑)。"""
    j = _json(REPORTS / "env_governance" / "RECOVER_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "RECOVER_latest.json 不在(via-envrecover;L24 安裝出問題先還原前次再順序裝)"}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "restore": (j.get("restore") or {}).get("mode"), "stages": len((j.get("install") or {}).get("stages") or []),
            "exclusive": (j.get("isolation") or {}).get("exclusive", []), "borrow_blocked": j.get("borrow_blocked", []),
            "order": [x.split("(")[0] for x in (j.get("order") or [])]}


def cg_family() -> dict:
    """批514:中央治理家族快照(CGC_MDL150 status 落 VIA_Reports/central_governance/FAMILY_latest.json;VIA_CGFAMILY_LATEST 可覆寫路徑)。"""
    p = Path(os.environ.get("VIA_CGFAMILY_LATEST") or (REPORTS / "central_governance" / "FAMILY_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": "FAMILY_latest.json 不在(via-cgfamily 跑一次即有;五成員經 CGC_MDL150 擁有者起跑,預設 dry-run)"}
    ff = j.get("files") or {}
    mem = j.get("members") or {}
    return {"state": j.get("state", "?"), "ts": j.get("ts"), "home": Path(str(j.get("home") or "")).name or "-",
            "files": {k: v.get("state") for k, v in (ff.get("members") or {}).items()},
            "members": {k: {"state": v.get("state"), "snapshot": v.get("snapshot") or v.get("stamp") or v.get("ts") or "", "why": v.get("why") or ""} for k, v in mem.items()},
            "cycles": ((mem.get("console") or {}).get("cycles_reading") or None),      # 批518:G17 循環判讀(CGC_MDL150 v0103 cycles)
            "age_h": _age_h(str(j.get("ts") or ""))}


def cg_cycles_line(cg: dict) -> str:
    """批518:十一段/頁段共用一行——活樹圈才是債;缺=ABSENT 誠實。"""
    cr = (cg or {}).get("cycles")
    if not cr:
        return "主控台 G17 循環判讀:ABSENT(via-cgfamily cycles 跑一次即有;工具 RED 先分活樹/存檔再判)"
    return (f"主控台 G17 循環判讀(批518;L38):{cr.get('n')} 圈 · 活樹 {cr.get('live')} · " + " · ".join(f"{k} {v}" for k, v in (cr.get("by_zone") or {}).items())
            + f" → 活樹 {cr.get('verdict')}(退役/收容/存檔內互呼不是活樹的債;via-cgfamily cycles @ {cr.get('ts') or '-'})")


def ui_workflow() -> dict:
    """批519:U/I 對接契約 + 工作流最新一跑 + 庫分類歸納(CGC_MDL153 落 VIA_Reports/ui|workflow;缺=ABSENT 誠實;VIA_UI_CONTRACT_LATEST/VIA_WORKFLOW_LATEST/VIA_DB_SUMMARY_LATEST 可覆寫)。"""
    _e = os.environ.get("VIA_UI_CONTRACT_LATEST")
    uc = _json(Path(_e)) if _e else (_json(REPORTS / "ui" / "UI_CONTRACT_latest.json") or _json(HERE / "VIA_UI_Contract_v0100.json"))   # 明給路徑不退冊(自測 ABSENT 要真 ABSENT)
    wf = _json(Path(os.environ.get("VIA_WORKFLOW_LATEST") or (REPORTS / "workflow" / "WORKFLOW_latest.json")))
    db = _json(Path(os.environ.get("VIA_DB_SUMMARY_LATEST") or (REPORTS / "workflow" / "DB_SUMMARY_latest.json")))
    pages = (uc or {}).get("pages") or []
    out = {"state": "ABSENT" if not uc else "OK", "ts": (uc or {}).get("ts"), "n": len(pages), "by_family": (uc or {}).get("by_family") or {},
           "absent": [p.get("page") for p in pages if not p.get("exists")], "fresh": sum(1 for p in pages if p.get("fresh")),
           "pages": [{"page": p.get("page"), "family": p.get("family"), "lamp": p.get("lamp"), "owner": p.get("owner") or "", "refresh": p.get("refresh") or "", "path": p.get("path") or "", "exists": bool(p.get("exists"))} for p in pages],
           "workflow": ({"state": "ABSENT", "why": "尚未 via-workflow run"} if not wf else {"state": wf.get("verdict"), "id": wf.get("id"), "ts": wf.get("ts"), "profile": wf.get("profile"), "counts": wf.get("counts"),
                                                                                   "results": [{"id": r.get("id"), "state": r.get("state"), "why": str(r.get("why") or "")[:100]} for r in wf.get("results") or []]}),
           "db": ({"state": "ABSENT", "why": "尚未 via-workflow db-summary"} if not db else {"state": db.get("verdict"), "ts": db.get("ts"), "n_tables": db.get("n_tables"),
                                                                                         "categories": [{"cat": c.get("cat"), "lamp": c.get("lamp"), "n": c.get("n"), "newest": c.get("newest"), "worst_lag": c.get("worst_lag")} for c in db.get("categories") or []]}),
           "composer": "via-workflow page(WORKFLOW_COMPOSER.html;--publish 入倉 ui_support/VIA_UI_WorkflowComposer_v0100.html)"}
    if not uc:
        out["why"] = "UI_CONTRACT_latest.json 不在(via-workflow ui-contract --apply 跑一次即有)"
    return out


def vtmra() -> dict:
    """批516:VTMRA 家族測試閘快照(CGC_MDL152 test 落 VIA_Reports/vtmra/VTMRA_latest.json;VIA_VTMRA_LATEST 可覆寫)。"""
    p = Path(os.environ.get("VIA_VTMRA_LATEST") or (REPORTS / "vtmra" / "VTMRA_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": "VTMRA_latest.json 不在(via-vtmra 跑一次即有;七成員家族境真跑自測)"}
    return {"state": j.get("verdict", "?"), "ts": j.get("ts"), "members": {r.get("id"): r.get("state") for r in (j.get("results") or [])},
            "reasons": j.get("reasons") or [], "age_h": _age_h(str(j.get("ts") or ""))}


def _rungate_merged(latest: dict) -> tuple[dict, dict, list]:
    """批517:每個必驗族取 24h 內最新一跑(RUNGATE_*.json 史;VIA_RUNGATE_DIR 覆寫);回 (families, per-family ts, 取用檔名)。"""
    d = Path(os.environ.get("VIA_RUNGATE_DIR") or (REPORTS / "rungate"))
    fams, ts_of, used = {}, {}, []
    hist = sorted((p for p in d.glob("RUNGATE_2*.json")), key=lambda p: p.name, reverse=True) if d.is_dir() else []
    for fam in INSTALL_REQUIRED_FAMILIES:
        for p in hist:
            j = _json(p) or {}
            f = (j.get("families") or {}).get(fam)
            a = _age_h(j.get("ts", ""))
            if isinstance(f, dict) and a is not None and 0 <= a <= UNITEST_MAX_AGE_H:
                fams[fam], ts_of[fam] = f, j.get("ts", "")
                used.append(f"{fam}:{p.name}")
                break
        if fam not in fams and isinstance((latest.get("families") or {}).get(fam), dict):
            fams[fam], ts_of[fam] = latest["families"][fam], latest.get("ts", "")
            used.append(f"{fam}:latest")
    for fam, f in (latest.get("families") or {}).items():
        fams.setdefault(fam, f); ts_of.setdefault(fam, latest.get("ts", ""))
    return fams, ts_of, used


def rungate() -> dict:
    p = Path(os.environ.get("VIA_RUNGATE_LATEST") or (REPORTS / "rungate" / "RUNGATE_latest.json"))
    j = _json(p)
    if not j:
        return {"state": "ABSENT", "why": f"{p.name} 不在(via-rungate 先跑)", "install": "BLOCKED_UNITEST"}
    families, ts_of, used = _rungate_merged(j)
    _ages = [_age_h(ts_of.get(f, "")) for f in INSTALL_REQUIRED_FAMILIES if f in families]
    age = (max(a for a in _ages if a is not None) if any(a is not None for a in _ages) else _age_h(j.get("ts", "")))
    _order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
    _verdicts = [str((families.get(f) or {}).get("verdict", "?")) for f in INSTALL_REQUIRED_FAMILIES if f in families]
    merged_verdict = (max(_verdicts, key=lambda v: _order.get(v, 3)) if _verdicts else j.get("verdict", "?"))
    j = {**j, "verdict": merged_verdict, "_used": used}
    # L19 必驗族是政策常數，不允許以環境變數縮成單族繞門。
    required = list(INSTALL_REQUIRED_FAMILIES)
    reasons = []
    if j.get("verdict") != "GREEN":
        reasons.append(f"總燈={j.get('verdict', '?')}≠GREEN")
    if age is None or not 0 <= age <= UNITEST_MAX_AGE_H:
        reasons.append("RunGate 時間缺/來自未來/逾 24h")
    coverage = {}
    for fam in required:
        f = families.get(fam)
        if not isinstance(f, dict):
            coverage[fam] = {"ok": False, "why": "家族未測"}
            reasons.append(f"{fam} 家族未測")
            continue
        sm = f.get("summary") or {}
        py_ok = (f.get("python") or {}).get("state") == "OK"
        required_ok = _nat(sm.get("required_ok"))
        required_n = _nat(sm.get("required_n"))
        libs_ok = required_n > 0 and required_ok == required_n
        engines_n = _nat(sm.get("engines_n"))
        engines_ok = _nat(sm.get("engines_ok"))
        tests_ok = engines_n > 0 and engines_ok == engines_n
        fam_ok = f.get("verdict") == "GREEN" and py_ok and libs_ok and tests_ok
        why = []
        if f.get("verdict") != "GREEN": why.append(f"燈={f.get('verdict', '?')}")
        if not py_ok: why.append("家族境非 OK")
        if not libs_ok: why.append(f"必要庫 {sm.get('required_ok', 0)}/{sm.get('required_n', 0)}")
        if not tests_ok: why.append(f"自測站 {engines_ok}/{engines_n}")
        coverage[fam] = {"ok": fam_ok, "why": "、".join(why) or "完整 GREEN",
                         "required_ok": required_ok, "required_n": required_n,
                         "engines_ok": engines_ok, "engines_n": engines_n}
        if not fam_ok:
            reasons.append(f"{fam}:" + coverage[fam]["why"])
    ok = not reasons
    return {"state": j.get("verdict", "?"), "ts": j.get("ts"),
            "age_h": (round(age, 1) if age is not None else None),
            "families": list(families), "required_families": required, "used": j.get("_used", []),
            "coverage": coverage, "reasons": reasons,
            "install": "INSTALL_OK" if ok else "BLOCKED_UNITEST"}


def bus() -> dict:
    j = _json(REPORTS / "engine_bus" / "ENGINE_BUS_latest.json")
    if not j:
        return {"state": "ABSENT", "why": "ENGINE_BUS_latest.json 不在(via-ryg)"}
    res = j.get("results") or []
    by: dict = {}
    for r in res:
        by[r.get("state", "?")] = by.get(r.get("state", "?"), 0) + 1
    reds = [(r.get("id") or r.get("item"), (r.get("why") or "")[:90]) for r in res if r.get("state") in ("RED", "TIMEOUT")]
    return {"state": "OK", "ts": j.get("ts"), "profile": j.get("profile", "run"),
            "apply_families": j.get("apply_families"), "n": len(res), "counts": by or j.get("counts", {}), "reds": reds[:12],
            "html": str(REPORTS / "engine_bus" / "ENGINE_BUS_MATRIX.html")}


def handover_src() -> dict:
    hits = []
    for q in (VIA / "docs").glob("VIA_Handover_*_B*.md"):
        m = re.match(r"VIA_Handover_(\d{8})_B(\d+)\.md$", q.name)
        if m:
            hits.append(((m.group(1), int(m.group(2))), q))
    if not hits:
        return {"state": "ABSENT", "sections": {}}
    p = sorted(hits)[-1][1]
    t = p.read_text(encoding="utf-8", errors="replace")
    secs, cur, buf = {}, None, []
    for ln in t.splitlines():
        if ln.startswith("## "):
            if cur:
                secs[cur] = "\n".join(buf).strip()
            cur, buf = ln[3:].strip(), []
        else:
            buf.append(ln)
    if cur:
        secs[cur] = "\n".join(buf).strip()
    return {"state": "OK", "src": p.name, "sections": secs, "text": t}


def prompt_doc() -> dict:
    p = _newest(VIA / "docs", "VIA_AI_Handover_Prompt_v*.md")
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": (p.read_text(encoding="utf-8", errors="replace") if p else "")}


def dropped_balls() -> dict:
    hits = sorted((VIA / "docs").glob("VIA_DroppedBalls_B*.md"), key=lambda q: int(re.search(r"_B(\d+)", q.name).group(1)))
    p = hits[-1] if hits else None
    t = p.read_text(encoding="utf-8", errors="replace") if p else ""
    rows = [ln for ln in t.splitlines() if ln.startswith("| ") and not ln.startswith("| 代號") and not ln.startswith("|---")]
    return {"state": "OK" if p else "ABSENT", "src": (p.name if p else ""), "text": t, "n": len(rows), "open": sum(1 for r in rows if "~~" not in r)}


# ────────────────────────── 註冊稽核 ──────────────────────────
ENGINE_GLOBS = [("functional modules/VDF/engine", "*_v????.py"), ("functional modules/VRN", "*_v????.py"), ("functional modules/VAP/engine", "*_v????.py"),
                ("supportive modules/registry", "CGC_*_v????.py"), ("supportive modules/70_VRN_Rules", "SUP_*_v????.py"), ("supportive modules/network", "SUP_*_v????.py"),
                ("supportive modules/VIA_Central_Governance", "CGC_*_v????.py"), (".", "VIA_SYSTEM_MANAGER_v????.py")]

COMPONENT_PREFIX = {"system": "SYS", "engine": "ENG", "module": "MDL", "class": "CLS",
                    "function": "FNC", "feature": "FNT", "tool": "TOOL",
                    "package": "PKG", "environment": "ENV"}


def _tail_files() -> dict[str, Path]:
    """受治理範圍的尾版家族。版本變動不重發元件號。"""
    fams: dict[str, Path] = {}
    for d, g in ENGINE_GLOBS:
        for q in (VIA / d).glob(g):
            if "references" in q.parts or "_superseded" in str(q):
                continue
            stem = re.sub(r"_v\d{4}\.py$", "", q.name)
            if stem not in fams or q.name > fams[stem].name:
                fams[stem] = q
    return fams


def live_components() -> dict:
    """建立可重現的活元件清單；不寫檔。

    掃描界線刻意固定：受治理尾版 PY、其 AST 類別/函數、InputConsole 功能項、
    Register 短令、ToolRoster/Baseline 工具套件與環境。references 收容件除非已被
    規格冊掛成正式功能，否則不把整個封存倉當現役元件。
    """
    rows: dict[str, dict] = {}
    parse_errors = []

    def add(category: str, identity: str, source: str, line: int | None = None):
        identity = str(identity).strip()
        if not identity:
            return
        key = f"{category}|{identity}"
        row = {"key": key, "category": category, "identity": identity, "source": source}
        if line:
            row["line"] = int(line)
        rows.setdefault(key, row)

    tails = _tail_files()
    for stem, q in sorted(tails.items()):
        rel = q.relative_to(VIA).as_posix()
        cat = "engine" if re.search(r"_ENG\d+", stem) else ("module" if re.search(r"_MDL\d+", stem) else "system")
        add(cat, stem, rel)
        try:
            tree = ast.parse(q.read_text(encoding="utf-8", errors="replace"), filename=str(q))
        except Exception as exc:
            parse_errors.append({"file": rel, "why": f"{type(exc).__name__}:{str(exc)[:100]}"})
            continue

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                self.stack: list[str] = []

            def visit_ClassDef(self, node):
                qual = ".".join(self.stack + [node.name])
                add("class", f"{stem}:{qual}", rel, node.lineno)
                self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

            def _function(self, node):
                qual = ".".join(self.stack + [node.name])
                add("function", f"{stem}:{qual}", rel, node.lineno)
                self.stack.append(node.name); self.generic_visit(node); self.stack.pop()

            visit_FunctionDef = _function
            visit_AsyncFunctionDef = _function

        Visitor().visit(tree)

    # PowerShell launchers and their declared functions share the same central codes.
    ps_tails = {}
    for q in sorted((VIA / 'launchers').glob('*.ps1')):
        stem = re.sub(r'-v\d+$', '', q.stem)
        ps_tails[stem] = q
    for stem, q in ps_tails.items():
        rel = q.relative_to(VIA).as_posix()
        add('tool', 'launcher:' + stem, rel)
        for no, line in enumerate(q.read_text(encoding='utf-8-sig').splitlines(), 1):
            m = re.match(r'^function\s+(def_[A-Za-z0-9_]+)', line)
            if m:
                add('function', stem + ':' + m.group(1), rel, no)
    pc = _json(HERE / 'VIA_Panorama_Contract_v0100.json') or {}
    if pc:
        add('module', 'VIA_Panorama_Contract', 'supportive modules/registry/VIA_Panorama_Contract_v0100.json')
    for issue in pc.get('problem_types', []):
        add('feature', 'panorama/problem:' + issue['code'], 'VIA_Panorama_Contract')
    for item, params in pc.get('engine_params', {}).items():
        for name in params:
            add('feature', 'panorama/parameter:' + item + ':' + name, 'VIA_Panorama_Contract')
    for it in spec_items().get("items", []):
        add("feature", f"{it.get('family')}/{it.get('id')}", "VIA_InputConsole_Spec")
    for c in register_cmds().get("cmds", []):
        add("tool", c.get("cmd"), "Register-VIA-Commands")

    baseline = _json(HERE / "VIA_EnvGovernance_Baseline_v0100.json") or {}
    envs = {"base"}
    for name, cfg in (baseline.get("env_layout") or {}).items():
        if isinstance(cfg, dict):
            envs.add(str(name)); envs.update(str(x) for x in cfg.get("aliases", []) if x)
    for fam, cfg in (baseline.get("families") or {}).items():
        if not isinstance(cfg, dict):
            continue
        envs.add(str(cfg.get("target_env") or "")); envs.update(str(x) for x in cfg.get("alt_envs", []) if x)
        for pkg in cfg.get("members", []):
            add("package", str(pkg).lower(), f"EnvBaseline:{fam}")
    roster = _json(HERE / "VIA_ToolRoster_SSOT_v0100.json") or {}
    for env, cfg in (roster.get("envs") or {}).items():
        envs.add(str(env)); envs.update(str(x) for x in cfg.get("aliases", []) if x)
        for tool in cfg.get("tools", []):
            if isinstance(tool, dict):
                add("package", str(tool.get("pip") or tool.get("imp") or "").lower(), f"ToolRoster:{env}")
    runtime = _json(REPORTS / "env_governance" / "TOOLS_PLAN_latest.json") or {}
    for e in runtime.get("envs", []):
        if isinstance(e, dict): envs.add(str(e.get("name") or ""))
    for env in sorted(x for x in envs if x):
        add("environment", env, "EnvGovernance")
    counts: dict[str, int] = {}
    for r in rows.values():
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    return {"rows": [rows[k] for k in sorted(rows)], "counts": counts,
            "parse_errors": parse_errors, "tails": len(tails)}


def component_registry() -> dict:
    j = _json(COMPONENT_REGISTRY)
    if not j:
        return {"state": "ABSENT", "path": str(COMPONENT_REGISTRY), "n": 0,
                "active": 0, "retired": 0, "counts": {}, "records": []}
    rec = j.get("records") or []
    active = [r for r in rec if r.get("state", "ACTIVE") == "ACTIVE"]
    counts: dict[str, int] = {}
    for r in active:
        counts[r.get("category", "?")] = counts.get(r.get("category", "?"), 0) + 1
    return {"state": "OK", "path": str(COMPONENT_REGISTRY), "n": len(rec),
            "active": len(active), "retired": len(rec) - len(active), "counts": counts,
            "updated_at": j.get("updated_at"), "records": rec, "counters": j.get("counters", {})}


def registry_sync(apply: bool = False, path: Path = COMPONENT_REGISTRY) -> dict:
    """VCGC 唯一寫入口；穩定號只增不減，消失件標 RETIRED、不刪號。"""
    live = live_components()
    old = _json(path) or {"schema": "VIA.ComponentInventory.v1", "append_only": True,
                          "writer": "VCGC registry-sync --apply", "counters": {}, "records": []}
    counters = {k: int(v) for k, v in (old.get("counters") or {}).items()}
    records = [dict(r) for r in (old.get("records") or [])]
    by_key = {r.get("key"): r for r in records if r.get("key")}
    live_by = {r["key"]: r for r in live["rows"]}
    new_keys = sorted(set(live_by) - set(by_key))
    stale_keys = sorted(k for k, r in by_key.items() if r.get("state", "ACTIVE") == "ACTIVE" and k not in live_by)
    tracked_fields = ("category", "identity", "source", "line")
    changed_keys = sorted(
        key for key in set(live_by) & set(by_key)
        if by_key[key].get("state") != "ACTIVE"
        or any(by_key[key].get(k) != live_by[key].get(k) for k in tracked_fields)
    )
    now = datetime.now().isoformat(timespec="seconds")
    if apply:
        for key in new_keys:
            r = live_by[key]
            prefix = COMPONENT_PREFIX[r["category"]]
            counters[prefix] = counters.get(prefix, 0) + 1
            records.append({**r, "code": f"VIA-{prefix}-{counters[prefix]:04d}",
                            "state": "ACTIVE", "first_seen": now})
        for key in changed_keys:
            cur, src = by_key[key], live_by[key]
            cur.update(src); cur["state"] = "ACTIVE"; cur.pop("retired_at", None)
            cur["changed_at"] = now
        for key in stale_keys:
            by_key[key]["state"] = "RETIRED"; by_key[key]["retired_at"] = now
        dirty = bool(new_keys or stale_keys or changed_keys or not path.exists())
        if dirty:
            out = {**old, "schema": "VIA.ComponentInventory.v1", "append_only": True,
                   "writer": "VCGC registry-sync --apply", "batch": BATCH,
                   "updated_at": now, "counters": counters,
                   "records": sorted(records, key=lambda r: r.get("code", ""))}
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, path)
    return {"state": "APPLIED" if apply else "PLAN", "path": str(path),
            "expected": len(live_by), "counts": live["counts"], "parse_errors": live["parse_errors"],
            "new": len(new_keys), "new_keys": new_keys, "stale": len(stale_keys),
            "stale_keys": stale_keys, "changed": len(changed_keys)}


def audit(deck=None, spec=None, grid=None, reg=None, man=None) -> dict:
    deck = deck if deck is not None else deck_tasks()
    spec = spec if spec is not None else spec_items()
    grid = grid if grid is not None else grid_stations()
    reg = reg if reg is not None else register_cmds()
    man = man if man is not None else manager_names()
    reg_text = ""
    p = _newest(VIA, "Register-VIA-Commands-v*.ps1")
    if p:
        reg_text = p.read_text(encoding="utf-8", errors="replace")
    surface_text = {
        "Deck": json.dumps(deck.get("tasks"), ensure_ascii=False),
        "Spec": json.dumps(spec.get("items"), ensure_ascii=False),
        "Grid": "\n".join(s["path"] + " " + s["name"] for s in grid.get("stations", [])),
        "Register": reg_text,
        "Manager": json.dumps(man, ensure_ascii=False),
    }
    fams = {stem: {"newest": q.name, "dir": q.parent.relative_to(VIA).as_posix()}
            for stem, q in _tail_files().items()}
    inv = component_registry()
    inv_active = {r.get("key") for r in inv.get("records", []) if r.get("state", "ACTIVE") == "ACTIVE"}
    rows = []
    for stem, v in sorted(fams.items()):
        cat = "engine" if re.search(r"_ENG\d+", stem) else ("module" if re.search(r"_MDL\d+", stem) else "system")
        registered = f"{cat}|{stem}" in inv_active
        surfaces = [name for name, text in surface_text.items() if stem in text]
        rows.append({"family": stem, "newest": v["newest"], "dir": v["dir"],
                     "registered": registered, "surfaces": surfaces,
                     "interface_registered": bool(surfaces)})
    unreg = [r for r in rows if not r["registered"]]
    interface_gaps = [r for r in rows if not r["interface_registered"]]
    live = live_components()
    live_keys = {r["key"] for r in live["rows"]}
    missing_all = sorted(live_keys - inv_active)
    return {"families": len(rows), "registered": len(rows) - len(unreg),
            "unregistered": unreg, "rows": rows, "interface_registered": len(rows) - len(interface_gaps),
            "interface_gaps": interface_gaps, "inventory_state": inv.get("state"),
            "inventory_active": inv.get("active", 0), "inventory_expected": len(live_keys),
            "inventory_missing": missing_all, "inventory_counts": inv.get("counts", {}),
            "parse_errors": live.get("parse_errors", [])}


def check() -> dict:
    """L19 安裝核可:VDF+VRN 完整 RunGate GREEN 且 24h 內。"""
    r = rungate()
    result = {"install": r.get("install"), "rungate": r.get("state"), "age_h": r.get("age_h"),
            "required_families": r.get("required_families"), "coverage": r.get("coverage"),
            "reasons": r.get("reasons"), "law": "L19 環境統一測式(VDF+VRN 完整覆蓋)無誤後才可核可安裝"}
    # 批568:比照 RunGate 慣例給覆寫鍵,生產預設路徑不變;合成檢才關得進沙盒(LL114)
    latest_path = Path(os.environ.get("VIA_PANORAMA_LATEST") or (REPORTS / 'panorama' / 'PANORAMA_latest.json'))
    latest = _json(latest_path)
    age = _age_h((latest or {}).get('updated_at', ''))
    if latest_path.exists() and (not latest or latest.get('status') != 'FINISHED' or latest.get('blockers', 1)
                                 or not latest.get('results') or age is None or age < 0 or age > UNITEST_MAX_AGE_H):
        result['install'] = 'BLOCKED_PANORAMA'
        result['reasons'] = list(result.get('reasons') or []) + ['全景實測尚未完成或仍有待修項目']
    return result


# ── 批568 來源閘:⑨ 這條路真正讀的每一個真機器來源,都要配覆寫鍵、都要被自測關進沙盒 ──
SOURCE_GUARD_FUNCS = ("check", "rungate", "_rungate_merged")


def _reports_reads(node) -> list:
    """回傳函式體內所有 `REPORTS / …` 磁碟來源運算式(只留最外層,不留中間節點)。"""
    seen = set()
    for n in ast.walk(node):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div):
            s = ast.unparse(n)
            if s.startswith("REPORTS"):
                seen.add(s)
    return sorted(s for s in seen if not any(o != s and o.startswith(s + " /") for o in seen))


def source_guard() -> dict:
    """⑳ 批568:列 ⑨ 這條路的來源清單,並驗①每個磁碟來源都有 VIA_* 覆寫鍵 ②自測 ⑨ 區塊每個鍵都設過。

    立這道閘的原因寫在檔頭:批567 我只關了 RunGate 一個口,panorama 那口漏著,
    同一個檢在兩台機器上紅成兩種樣子。以後「底下還有一層」由機器講,不靠我記得。
    """
    src = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    guarded, keys, disk = {}, [], []
    for fn in SOURCE_GUARD_FUNCS:
        node = funcs.get(fn)
        if node is None:
            continue
        for n in ast.walk(node):                      # 覆寫慣用式:os.environ.get("VIA_X") or (REPORTS / …)
            if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or) and len(n.values) == 2:
                lhs, rhs = n.values
                if (isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Attribute) and lhs.func.attr == "get"
                        and isinstance(lhs.func.value, ast.Attribute) and lhs.func.value.attr == "environ"
                        and lhs.args and isinstance(lhs.args[0], ast.Constant)):
                    k = str(lhs.args[0].value)
                    keys.append(k)
                    guarded[ast.unparse(rhs).strip("()")] = k
        for s in _reports_reads(node):
            disk.append((fn, s))
    unguarded = sorted({s for _, s in disk if s not in guarded})
    blk = src.split('sv = os.environ.get("VIA_RUNGATE_LATEST")', 1)[-1].split('chk("\u2468', 1)[0]
    unsandboxed = sorted(k for k in set(keys) if f'os.environ["{k}"]' not in blk)
    return {"state": "OK" if not unguarded and not unsandboxed else "FAIL",
            "funcs": list(SOURCE_GUARD_FUNCS), "keys": sorted(set(keys)),
            "disk": sorted({s for _, s in disk}), "guarded": guarded,
            "unguarded": unguarded, "unsandboxed": unsandboxed}


# ────────────────────────── 一頁交接 + 頁 ──────────────────────────
def snapshot() -> dict:
    deck, spec, grid, reg, man = deck_tasks(), spec_items(), grid_stations(), register_cmds(), manager_names()
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "version": VERSION, "batch": BATCH, "laws": laws(), "ledger": ledger(), "deck": deck, "spec": spec,
            "grid": grid, "register": reg, "manager": man, "db_sheet": db_sheet(), "datahome": datahome(), "logic": logic(), "factors": factors(),
            "tools": tools_plan(), "recover": recover_plan(), "cg_family": cg_family(), "vtmra": vtmra(), "ui_workflow": ui_workflow(), "rungate": rungate(), "bus": bus(), "handover": handover_src(), "audit": audit(deck, spec, grid, reg, man),
            "inventory": component_registry(), "prompt": prompt_doc(), "balls": dropped_balls(),
            "panorama": _json(REPORTS / "panorama" / "PANORAMA_latest.json") or {}}


def onepage_md(s: dict) -> str:
    L, lg, dk, sp, gr, rg, mn, db, dh, lo, fa, tp, ru, bu, ho, au, inv = (s[k] for k in ("laws", "ledger", "deck", "spec", "grid", "register", "manager", "db_sheet", "datahome", "logic", "factors", "tools", "rungate", "bus", "handover", "audit", "inventory"))
    o = [f"# VIA 一頁交接 · Veritas Central Governance Console(VCGC v{VERSION} · 批{BATCH})", "",
         f"> 產生 {s['ts']} · 唯一對接口(律 L20):政策庫 · 邏輯庫 · 因子庫 · 資料庫 · 引擎調度 · 多矩陣 · 環境工具 · 註冊表 · 交接。動態段(矩陣/RunGate/工具計畫/資料家)以**你機器上最新一次 `via-vcgc onepage`** 為準;倉內這份是 commit 時的快照。", ""]
    pr, bl = s.get("prompt", {}), s.get("balls", {})
    o += ["## 〇 · 接手提示詞(給下一個 AI;來源 " + str(pr.get("src") or "ABSENT") + ")", "", (pr.get("text") or "(docs/VIA_AI_Handover_Prompt_v*.md 缺)").strip(), ""]
    o += ["## 一 · 政策庫(律 + lessons-learned)", ""]
    for x in L["laws"]:
        o.append(f"- **{x['id']}**({x['batch']};{x['cat']}){x['zh']}")
    o += ["", "**Lessons-learned**", ""] + [f"- {x['id']}({x['batch']}){x['zh']}" for x in L["lessons"]]
    rv = s.get("recover") or {}
    o += ["", "## 二 · 安裝核可(L19)與環境工具", "",
          f"- RunGate:{ru.get('state')} · {ru.get('ts') or '-'} · 齡 {ru.get('age_h')} h · 必驗 {ru.get('required_families')} · 覆蓋 {ru.get('coverage')} → **{ru.get('install')}**" + (f" · 原因 {ru.get('reasons')}" if ru.get("reasons") else ""),
          f"- 工具冊導入計畫:{tp.get('state')} · {tp.get('ts') or '-'} · 件態 {tp.get('counts') if tp.get('counts') is not None else '-'} · 風險 {tp.get('risk') if tp.get('risk') is not None else '-'} · 段 {tp.get('stages') if tp.get('stages') is not None else '-'} · 未路由 {tp.get('unrouted') if tp.get('unrouted') is not None else '-'} · 白名單留置 {tp.get('hold') if tp.get('hold') is not None else '-'}" + (f"({tp.get('why')})" if tp.get("why") else ""),
          f"- 環境復原(L24):{rv.get('state')} · {rv.get('ts') or '-'} · 還原 {rv.get('restore') or '-'} · 段 {rv.get('stages')} · 單獨隔離境 {rv.get('exclusive')} · 借境封鎖 {rv.get('borrow_blocked')} · 次序 {' → '.join(rv.get('order') or []) or '-'}" + (f"({rv.get('why')})" if rv.get("why") else "") + ";安裝出問題=`via-envrecover`(①還原前次 ②順序裝 ③_M/_H 單獨隔離;-Execute -Approve 才跑,① 不受 L19,② 過 L19)",
          "- 裝件=操作員的手:`$env:VIA_NET_CONSENT='YES'; via-envtools -Apply -Approve`(閘不代設;L19 未綠=BLOCKED_UNITEST)", ""]
    o += ["## 三 · 邏輯庫 · 因子庫 · 資料庫", "",
          f"- 邏輯庫 {lo.get('state')}:件 {lo.get('files')} · 判準 {lo.get('verdicts')} · 壞後端 {lo.get('broken')} · 政策因子 {lo.get('policy_rows')} 列 · 全庫同步 {lo.get('sync')} · 交接三處 {lo.get('handover')}",
          f"- 因子庫 {fa.get('state')}:{fa.get('rows')} 列 · {fa.get('by_source')} · 掛載 {fa.get('mounts')}",
          f"- 庫表冊 {db.get('state')}:{db.get('n')} 表({db.get('batch')})· 全庫表 {db.get('all_home')} · 庫 {db.get('dbs')}",
          f"- 資料家 {dh.get('state')}:{dh.get('home') or dh.get('why')} · 庫 {dh.get('dbs') if dh.get('dbs') is not None else '-'} · 表 {dh.get('tables') if dh.get('tables') is not None else '-'} · 湖 {dh.get('lakes') if dh.get('lakes') is not None else '-'}", ""]
    o += ["## 四 · 引擎調度 · 多矩陣實測", "",
          f"- 五矩陣 {bu.get('state')}:{bu.get('ts') or bu.get('why')} · profile {bu.get('profile')} · 真跑 {bu.get('apply_families')} · 項 {bu.get('n')} · 態 {bu.get('counts')}"]
    for rid, why in (bu.get("reds") or []):
        o.append(f"  - RED {rid}:{why}")
    vt = s.get("vtmra") or {}
    o.append(f"- VTMRA 家族測試閘(批516;台股月營收分析七成員):{vt.get('state')} · {vt.get('ts') or vt.get('why') or '-'} · 成員 {vt.get('members') or '-'}" + (f" · {'; '.join(vt.get('reasons') or [])}" if vt.get("reasons") else ""))
    o += [f"- Deck 任務 {len(dk.get('tasks', {}))} · 規格項 {len(sp.get('items', []))} · 格子站 {len(gr.get('stations', []))}(在位 {sum(1 for x in gr.get('stations', []) if x['present'])})· Register 指令 {len(rg.get('cmds', []))} · Manager 正式名稱 任務 {len(mn.get('tasks', {}))} / 引擎 {len(mn.get('engines', {}))}", ""]
    o += ["## 五 · 指令與參數(不丟失;來源 " + str(rg.get("src")) + ")", ""] + [f"- `{c['cmd']}`" + (f"(別名 {'/'.join(c['aliases'])})" if c["aliases"] else "") + (f":{c['usage']}" if c["usage"] else "") for c in rg.get("cmds", [])]
    o += ["", "## 六 · 註冊稽核(所有引擎/模組/功能/工具/環境)", "",
          f"- 中央自動編號冊 {au.get('inventory_state')} · ACTIVE {au.get('inventory_active')}/{au.get('inventory_expected')} · **缺 {len(au.get('inventory_missing', []))}** · 類別 {au.get('inventory_counts')}",
          f"- 尾版引擎/模組家族 {au['families']} · 中央冊已登 {au['registered']} · **未登 {len(au['unregistered'])}** · 操作介面有掛載 {au.get('interface_registered')} · 內部件無操作介面 {len(au.get('interface_gaps', []))}(誠實分列，不拿編號片段假命中)"] + [f"  - 未登 {r['newest']}({r['dir']})" for r in au["unregistered"][:60]]
    o += ["", "## 七 · 自動編號註冊表(台帳)", "", f"- 全域台帳 {lg.get('n')} 筆 · 元件 {lg.get('components')} · 更新 {lg.get('updated_at')}",
          f"- 元件冊 {inv.get('state')} · ACTIVE {inv.get('active')} · RETIRED {inv.get('retired')} · 更新 {inv.get('updated_at')} · {inv.get('counts')}",
          "- 類別 current:" + " · ".join(f"{k} {v}" for k, v in (lg.get("categories") or {}).items() if v), ""]
    for e in (lg.get("tail") or [])[-6:]:
        detail = e.get("kind") or " ".join(
            str(x) for x in (e.get("op"), e.get("category"), e.get("component"), e.get("code")) if x
        )
        o.append(f"- {e.get('ts')} {detail[:90]}")
    o += ["", f"## 八 · 交接本文(來源 {ho.get('src')};逐批紀錄見該檔)", ""]
    # 批508：舊版只挑名稱寫死的「三 還掛／四 紀律／五 一貼」三節；
    # 新固定格式 〇–八 因此整段空白。交接不能靠標題碰巧同名，尾版全文才是
    # 唯一記憶。嵌入時只把標題降一級，維持 ONEPAGE 九個主段不被打散。
    handover_lines = []
    for i, line in enumerate((ho.get("text") or "").splitlines()):
        if i == 0 and line.startswith("# "):
            continue
        if line.startswith("### "):
            line = "#### " + line[4:]
        elif line.startswith("## "):
            line = "### " + line[3:]
        handover_lines.append(line)
    o += handover_lines or ["(逐批交接本文缺)"]
    o_tail = ["", f"## 九 · 掉球清單(來源 {bl.get('src') or 'ABSENT'};列 {bl.get('n')} · 未結 {bl.get('open')};只增不減,結案劃線)", "", (bl.get("text") or "(缺)").strip(), ""]
    o += o_tail
    pa = s.get("panorama") or {}
    if pa:
        o += ["", "## 十 · VRN / VDF / VATETF(舊名 VETF)最新全景實測", "",
              f"{pa.get('start')} → {pa.get('end')} · {pa.get('status')} · 核可 {pa.get('approval')} · 待修 {pa.get('blockers')}", "",
              "| 項目 | 階段 | 狀態 | 問題與處置 |", "|---|---|---|---|"]
        for row in pa.get('results', []):
            vals = [str(row.get(k, '')).replace('|','\\|').replace('\n','<br>') for k in ('id','phase','state','why')]
            o.append('| ' + ' | '.join(vals) + ' |')
    cg = s.get("cg_family") or {}
    o += ["", "## 十一 · 中央治理家族(批514;VIA-SYS-MGR-001 主控台 · VIA-GOV-ENG-001 詞彙引擎 · VIA-SYS-MGR-003 下行控制 · VIA-SYS-ENG-003 檔案優先序 · 同名整併;擁有者 CGC_MDL150;預設 dry-run)", "",
          f"- 家族 {cg.get('state')} · {cg.get('ts') or cg.get('why') or '-'} · 正位 {cg.get('home') or '-'} · 成員件 {cg.get('files') or '-'}"]
    for k, m in (cg.get("members") or {}).items():
        o.append(f"  - {k}:{m.get('state')}" + (f" · {m.get('snapshot')}" if m.get("snapshot") else "") + (f" · {m.get('why')}" if m.get("why") else ""))
    o += ["- " + cg_cycles_line(cg)]
    o += ["- 一貼即用:`via-cgfamily plan`(router → engine --selftest → console → downward → samename;--commit/--probe/--token=你的手)"]
    uw = s.get("ui_workflow") or {}
    o += ["", "## 十二 · U/I 對接與工作流(批519;擁有者 CGC_MDL153 WorkflowComposer;中央只連結不重造;頁在=連、不在=ABSENT)", "",
          f"- U/I 契約 {uw.get('state')} · {uw.get('ts') or uw.get('why') or '-'} · 頁 {uw.get('n')} · 家族 {uw.get('by_family') or '-'} · 新鮮 {uw.get('fresh')} · 不在 {len(uw.get('absent') or [])}"]
    for p in (uw.get("pages") or [])[:60]:
        o.append(f"  - [{p.get('lamp')}] {p.get('family')} · {p.get('page')} · 擁有者 {p.get('owner') or '-'} · 再生 {p.get('refresh') or '-'}")
    w = uw.get("workflow") or {}
    o.append(f"- 工作流最新一跑 {w.get('state')} · {w.get('id') or ''} · {w.get('ts') or w.get('why') or '-'} · {w.get('counts') or ''}")
    for r in w.get("results") or []:
        o.append(f"  - [{r.get('state')}] {r.get('id')} {r.get('why') or ''}")
    d = uw.get("db") or {}
    o.append(f"- VDF 庫分類歸納 {d.get('state')} · {d.get('ts') or d.get('why') or '-'} · 表 {d.get('n_tables') if d.get('n_tables') is not None else '-'} · " + " · ".join(f"{c.get('cat')} {c.get('lamp')}(表 {c.get('n')} 最新 {c.get('newest') or '-'} 滯後 {c.get('worst_lag') if c.get('worst_lag') is not None else '?'})" for c in d.get("categories") or []))
    o.append(f"- 一貼即用:`via-workflow ui-contract --apply` → `via-workflow db-summary` → `via-workflow run <id> --profile test` → `via-workflow page --publish` → `via-open`(零彈窗:頁不自開)")
    return "\n".join(o) + "\n"


def page_html(s: dict) -> str:
    def esc(x):
        return html.escape(str(x))

    def table(rows, cols):
        h = "<table><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr>"
        for r in rows:
            h += "<tr>" + "".join(f"<td>{esc(r.get(c, ''))}</td>" for c in cols) + "</tr>"
        return h + "</table>"
    lamp = {"OK": "#16a34a", "GREEN": "#16a34a", "INSTALL_OK": "#16a34a", "ABSENT": "#6b7280", "BLOCKED_UNITEST": "#f59e0b", "RED": "#dc2626", "PLAN": "#2563eb"}
    ru, bu, tp, lo, fa, db, dh, au, rg, lg, L, inv = (s[k] for k in ("rungate", "bus", "tools", "logic", "factors", "db_sheet", "datahome", "audit", "register", "ledger", "laws", "inventory"))

    def chip(t):
        return f'<span class="chip" style="background:{lamp.get(str(t).split(" ")[0], "#6b7280")}">{esc(t)}</span>'
    parts = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>Veritas Central Governance Console v{VERSION}</title>",
             "<style>body{font-family:'Segoe UI',system-ui,sans-serif;margin:0;background:#0f172a;color:#e5e7eb}header{padding:18px 28px;background:#111827;border-bottom:1px solid #334155}h1{margin:0;font-size:20px}h2{font-size:15px;margin:22px 0 8px;color:#93c5fd}section{padding:6px 28px}table{border-collapse:collapse;font-size:12px;width:100%}th,td{border:1px solid #334155;padding:4px 6px;text-align:left;vertical-align:top}th{background:#1f2937}.chip{display:inline-block;padding:2px 8px;border-radius:10px;color:#fff;font-size:12px;margin-right:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}.card{background:#111827;border:1px solid #334155;border-radius:8px;padding:10px 12px;font-size:13px}code{background:#1f2937;padding:1px 4px;border-radius:4px}small{color:#9ca3af}</style></head><body>",
             f"<header><h1>Veritas Central Governance Console <small>v{VERSION} · 批{BATCH} · {esc(s['ts'])} · 唯一對接口(L20)· 零 CDN · 預設只讀</small></h1></header>",
             "<section><div class='grid'>",
             f"<div class='card'><b>安裝核可 L19</b><br>{chip(ru.get('install'))} RunGate {chip(ru.get('state'))} {esc(ru.get('ts') or ru.get('why') or '')} 齡 {esc(ru.get('age_h'))} h<br>必驗 {esc(ru.get('required_families'))} · {esc(ru.get('coverage'))}<br>{esc(ru.get('reasons'))}</div>",
             f"<div class='card'><b>五矩陣</b><br>{chip(bu.get('state'))} {esc(bu.get('ts') or bu.get('why') or '')} · profile {esc(bu.get('profile'))}<br>{esc(bu.get('counts'))}</div>",
             f"<div class='card'><b>環境工具計畫</b><br>{chip(tp.get('state'))} {esc(tp.get('ts') or tp.get('why') or '')}<br>{esc(tp.get('counts') if tp.get('counts') is not None else '-')} · 風險 {esc(tp.get('risk') if tp.get('risk') is not None else '-')}</div>",
             f"<div class='card'><b>環境復原(L24)</b><br>{chip((s.get('recover') or {}).get('state'))} {esc((s.get('recover') or {}).get('ts') or (s.get('recover') or {}).get('why') or '')}<br>還原 {esc((s.get('recover') or {}).get('restore') or '-')} · 段 {esc((s.get('recover') or {}).get('stages'))} · 隔離境 {esc(len((s.get('recover') or {}).get('exclusive') or []))}</div>",
             f"<div class='card'><b>中央治理家族(批514)</b><br>{chip((s.get('cg_family') or {}).get('state'))} {esc((s.get('cg_family') or {}).get('ts') or (s.get('cg_family') or {}).get('why') or '')}<br>正位 {esc((s.get('cg_family') or {}).get('home') or '-')} · 成員 {esc({k: v.get('state') for k, v in ((s.get('cg_family') or {}).get('members') or {}).items()})}</div>",
             f"<div class='card'><b>U/I 對接與工作流(批519)</b><br>{chip((s.get('ui_workflow') or {}).get('state'))} 頁 {esc((s.get('ui_workflow') or {}).get('n'))} · 新鮮 {esc((s.get('ui_workflow') or {}).get('fresh'))} · 不在 {esc(len((s.get('ui_workflow') or {}).get('absent') or []))}<br>工作流 {chip(((s.get('ui_workflow') or {}).get('workflow') or {}).get('state'))} {esc(((s.get('ui_workflow') or {}).get('workflow') or {}).get('id') or '')} · 庫分類 {chip(((s.get('ui_workflow') or {}).get('db') or {}).get('state'))}</div>",
             f"<div class='card'><b>VTMRA 家族測試閘(批516)</b><br>{chip((s.get('vtmra') or {}).get('state'))} {esc((s.get('vtmra') or {}).get('ts') or (s.get('vtmra') or {}).get('why') or '')}<br>成員 {esc((s.get('vtmra') or {}).get('members') or '-')}</div>",
             f"<div class='card'><b>邏輯庫</b><br>{chip(lo.get('state'))} 件 {esc(lo.get('files'))} · {esc(lo.get('verdicts'))}<br>壞後端 {esc(lo.get('broken'))}<br>同步 {esc(lo.get('sync'))}</div>",
             f"<div class='card'><b>因子庫</b><br>{chip(fa.get('state'))} {esc(fa.get('rows'))} 列 · {esc(fa.get('by_source'))}</div>",
             f"<div class='card'><b>資料庫</b><br>庫表冊 {esc(db.get('n'))} 表({esc(db.get('batch'))})· 資料家 {chip(dh.get('state'))} {esc(dh.get('home') or dh.get('why'))} · 庫 {esc(dh.get('dbs') if dh.get('dbs') is not None else '-')} 湖 {esc(dh.get('lakes') if dh.get('lakes') is not None else '-')}</div>",
             f"<div class='card'><b>註冊稽核</b><br>中央冊 {esc(au.get('inventory_active'))}/{esc(au.get('inventory_expected'))} · 缺 {len(au.get('inventory_missing', []))}<br>尾版家族 {au['families']} · 已登 {au['registered']} · 未登 {len(au['unregistered'])} · 介面掛載 {esc(au.get('interface_registered'))}</div>",
             f"<div class='card'><b>掉球清單</b><br>{esc(s.get('balls', {}).get('src') or 'ABSENT')} · 列 {esc(s.get('balls', {}).get('n'))} · 未結 {esc(s.get('balls', {}).get('open'))}<br><small>接手提示詞:{esc(s.get('prompt', {}).get('src') or 'ABSENT')}</small></div>",
             f"<div class='card'><b>自動編號註冊表</b><br>全域台帳 {esc(lg.get('n'))} 筆 · 舊元件 {esc(lg.get('components'))}<br>元件冊 ACTIVE {esc(inv.get('active'))} · RETIRED {esc(inv.get('retired'))}<br>{esc(inv.get('counts'))}</div>",
             "</div></section>",
             "<section><h2>政策庫 · 律</h2>" + table(L["laws"], ["id", "batch", "cat", "zh"]) + "<h2>Lessons-learned</h2>" + table(L["lessons"], ["id", "batch", "zh"]) + "</section>",
             "<section><h2>指令與參數(不丟失)</h2>" + table([{"cmd": c["cmd"], "aliases": "/".join(c["aliases"]), "usage": c["usage"]} for c in rg.get("cmds", [])], ["cmd", "aliases", "usage"]) + "</section>",
             "<section><h2>Deck 任務冊</h2>" + table([{"task": k, "zh": v["zh"], "net": v["net"], "argv": " ".join(Path(a).name if "/" in a or "\\" in a else a for a in v["argv"])} for k, v in s["deck"].get("tasks", {}).items()], ["task", "zh", "net", "argv"]) + "</section>",
             "<section><h2>主控台規格項</h2>" + table(s["spec"].get("items", []), ["family", "id", "zh", "glob", "verb", "params", "net", "state"]) + "</section>",
             "<section><h2>格子站</h2>" + table(s["grid"].get("stations", []), ["name", "present", "path"]) + "</section>",
             "<section><h2>未登中央編號冊的引擎家族(誠實)</h2>" + table(au["unregistered"], ["family", "newest", "dir", "surfaces"]) + "</section>",
             "<section><h2>中央冊完整但未設操作介面的內部家族(不是未註冊)</h2>" + table(au.get("interface_gaps", []), ["family", "newest", "dir"]) + "</section>",
             "<section><h2>紅項(五矩陣)</h2>" + table([{"id": i, "why": w} for i, w in (bu.get("reds") or [])], ["id", "why"]) + "</section>",
             "<section><h2>台帳尾</h2>" + table(lg.get("tail") or [], ["ts", "kind"]) + "</section>",
             "<section><h2>U/I 對接與工作流(批519;擁有者 CGC_MDL153;頁在=連、不在=ABSENT)</h2><table><tr><th>page</th><th>family</th><th>lamp</th><th>owner</th><th>refresh</th></tr>" + "".join(("<tr><td>" + (f"<a href='file:///{esc(str(p.get('path')).replace(chr(92), '/'))}'>{esc(p.get('page'))}</a>" if p.get("exists") else esc(p.get("page"))) + f"</td><td>{esc(p.get('family'))}</td><td>{esc(p.get('lamp'))}</td><td>{esc(p.get('owner'))}</td><td>{esc(p.get('refresh'))}</td></tr>") for p in ((s.get("ui_workflow") or {}).get("pages") or [])) + "</table><p>工作流最新一跑:" + esc(json.dumps(((s.get("ui_workflow") or {}).get("workflow") or {}).get("counts") or ((s.get("ui_workflow") or {}).get("workflow") or {}).get("why") or "ABSENT", ensure_ascii=False)) + " · 庫分類:" + esc(" · ".join(f"{c.get('cat')} {c.get('lamp')}" for c in ((s.get("ui_workflow") or {}).get("db") or {}).get("categories") or []) or "ABSENT") + "</p></section>",
             "<section><h2>中央治理家族(批514;擁有者 CGC_MDL150;預設 dry-run)</h2>" + "<p>" + esc(cg_cycles_line(s.get("cg_family") or {})) + "</p>" + table([{"member": k, "state": v.get("state"), "snapshot": v.get("snapshot"), "why": v.get("why")} for k, v in ((s.get("cg_family") or {}).get("members") or {}).items()], ["member", "state", "snapshot", "why"]) + "</section>",
             "</body></html>"]
    pa = s.get('panorama') or {}
    if pa:
        parts.insert(-1, "<section><h2>VRN / VDF / VATETF(舊名 VETF)最新全景實測</h2><p>" + esc(pa.get('start')) + " → " + esc(pa.get('end')) + " · " + esc(pa.get('status')) + " · 核可 " + esc(pa.get('approval')) + "</p>" + table(pa.get('results', []), ['id','family','phase','state','why']) + "</section>")
    return "".join(parts)


def write_outputs(s: dict, out_dir: Path, publish: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    md, pg = onepage_md(s), page_html(s)
    (out_dir / "VIA_Handover_ONEPAGE.md").write_text(md, encoding="utf-8")
    (out_dir / "VIA_UI_CentralGovernanceConsole_v0100.html").write_text(pg, encoding="utf-8")
    (out_dir / "VCGC_latest.json").write_text(json.dumps({k: v for k, v in s.items() if k != "handover"}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    res = {"out": str(out_dir), "published": []}
    if publish:
        for dst in ((VIA / "docs" / "VIA_Handover_ONEPAGE.md"), (ROOT / "VIA_HANDOVER_LATEST.md")):
            dst.write_text(md, encoding="utf-8"); res["published"].append(str(dst))
        d2 = VIA / "supportive modules" / "ui_support" / "VIA_UI_CentralGovernanceConsole_v0100.html"
        d2.write_text(pg, encoding="utf-8"); res["published"].append(str(d2))
    return res


def status() -> int:
    s = snapshot()
    print(f"[VCGC] v{VERSION} 批{BATCH} · 唯一對接口(L20)· {s['ts']}")
    print(f"  政策庫 {s['laws']['state']}:律 {len(s['laws']['laws'])} · lessons {len(s['laws']['lessons'])} · 政策因子 {s['logic'].get('policy_rows')} 列")
    print(f"  邏輯庫 {s['logic'].get('state')}:件 {s['logic'].get('files')} · {s['logic'].get('verdicts')} · 壞後端 {s['logic'].get('broken')} · 同步 {s['logic'].get('sync')}")
    print(f"  因子庫 {s['factors'].get('state')}:{s['factors'].get('rows')} 列 {s['factors'].get('by_source')}")
    print(f"  資料庫:庫表冊 {s['db_sheet'].get('n')} 表 · 資料家 {s['datahome'].get('state')} {s['datahome'].get('home') or s['datahome'].get('why')}")
    print(f"  引擎調度:Deck {len(s['deck'].get('tasks', {}))} 任務 · 規格 {len(s['spec'].get('items', []))} 項 · 格子 {len(s['grid'].get('stations', []))} 站 · Register {len(s['register'].get('cmds', []))} 指令")
    print(f"  多矩陣 {s['bus'].get('state')}:{s['bus'].get('counts') or s['bus'].get('why')} · profile {s['bus'].get('profile')} · RunGate {s['rungate'].get('state')} → {s['rungate'].get('install')}")
    print(f"  環境工具 {s['tools'].get('state')}:{s['tools'].get('counts') or s['tools'].get('why')}")
    print(f"  環境復原 {s['recover'].get('state')}:{s['recover'].get('restore') or s['recover'].get('why')} · 隔離境 {len(s['recover'].get('exclusive') or [])}(L24)")
    print(f"  VTMRA 家族測試閘 {s['vtmra'].get('state')}:{s['vtmra'].get('members') or s['vtmra'].get('why')}(批516;via-vtmra)")
    print(f"  中央治理家族 {s['cg_family'].get('state')}:{s['cg_family'].get('files') or s['cg_family'].get('why')} · 成員 {({k: v.get('state') for k, v in (s['cg_family'].get('members') or {}).items()}) or '-'}(批514;via-cgfamily)")
    print(f"  註冊稽核:中央冊 {s['audit'].get('inventory_active')}/{s['audit'].get('inventory_expected')} 缺 {len(s['audit'].get('inventory_missing', []))} · 家族 {s['audit']['families']} 已登 {s['audit']['registered']} 未登 {len(s['audit']['unregistered'])} · 操作介面 {s['audit'].get('interface_registered')}" + (":" + ", ".join(r['newest'] for r in s['audit']['unregistered'][:8]) if s['audit']['unregistered'] else ""))
    print(f"  台帳 {s['ledger'].get('n')} 筆 · 交接源 {s['handover'].get('src')} · 頁/一頁:via-vcgc page|onepage(落 VIA_Reports/vcgc;--publish 才入倉)")
    return 0


def _last_h2_demoted(text: str) -> str:
    """交接本文最後一個 ## 標題,依八段嵌入規則降一級(### );沒有標題=空字串(在任何頁裡都真,誠實退化)。"""
    hs = [ln for ln in text.splitlines() if ln.startswith("## ")]
    return ("### " + hs[-1][3:]) if hs else ""


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    L = laws()
    chk("① 政策庫冊掛載(≥20 律、≥8 lessons;含 L19 安裝核可 / L20 唯一對接口)", L["state"] == "OK" and len(L["laws"]) >= 20 and len(L["lessons"]) >= 8 and {x["id"] for x in L["laws"]} >= {"L19", "L20"}, f"({len(L['laws'])} 律 · {len(L['lessons'])} lessons)")
    lg = ledger()
    chk("② 自動編號註冊表(台帳 ≥1000 筆 · 類別 current · 元件)", lg["state"] == "OK" and lg["n"] >= 1000 and "引擎" in lg["categories"] and lg["components"] > 0, f"({lg.get('n')} 筆)")
    dk = deck_tasks()
    chk("③ Deck 任務冊只讀取得(≥60 任務;含 vrn_logic/fin_logic/fin_statements)", dk["state"] == "OK" and len(dk["tasks"]) >= 60 and {"vrn_logic", "fin_logic", "fin_statements"} <= set(dk["tasks"]), f"({dk['state']} · {len(dk['tasks'])})")
    sp = spec_items()
    chk("④ 主控台規格項(≥40 項;fin_statements 接引擎)", sp["state"] == "OK" and len(sp["items"]) >= 40 and any(i["id"] == "fin_statements" and i["glob"] for i in sp["items"]), f"({len(sp['items'])})")
    gr = grid_stations()
    chk("⑤ 格子站只讀取得(≥100 站;在位計數誠實)", gr["state"] == "OK" and len(gr["stations"]) >= 100, f"({gr['state']} · {len(gr['stations'])} 站 · 在位 {sum(1 for x in gr['stations'] if x['present'])})")
    rg = register_cmds()
    chk("⑥ Register 指令與用法解析(≥60 指令;via-vrnlogic/via-finstat 帶用法行;別名 邏輯庫)", rg["state"] == "OK" and len(rg["cmds"]) >= 60
        and any(c["cmd"] == "via-vrnlogic" and c["usage"] and "邏輯庫" in c["aliases"] for c in rg["cmds"]) and any(c["cmd"] == "via-finstat" and c["usage"] for c in rg["cmds"]), f"({len(rg['cmds'])})")
    mn = manager_names()
    chk("⑦ Manager 正式名稱只讀(任務 ≥50 · 引擎 ≥30)", mn["state"] == "OK" and len(mn["tasks"]) >= 50 and len(mn["engines"]) >= 30, f"({len(mn['tasks'])}/{len(mn['engines'])})")
    au = audit(dk, sp, gr, rg, mn)
    chk("⑧ 註冊稽核:家族 ≥80;本批引擎(CGC_MDL149/VDF_ENG082/SUP_MDL748/VRN_ENG082)皆在中央自動編號冊;操作介面覆蓋另列不模糊命中",
        au["families"] >= 80 and all(any(r["family"].startswith(k) and r["registered"] for r in au["rows"]) for k in ("VDF_ENG082_FinStatements", "SUP_MDL748_FinancialLogicHub", "VRN_ENG082_ExtractionLogic")),
        f"(家族 {au['families']} · 中央冊 {au['registered']} · 未登 {len(au['unregistered'])} · 介面 {au.get('interface_registered')})")
    sv = os.environ.get("VIA_RUNGATE_LATEST")
    sr = os.environ.get("VIA_INSTALL_REQUIRED_FAMILIES")
    sd = os.environ.get("VIA_RUNGATE_DIR")
    sp_pan = os.environ.get("VIA_PANORAMA_LATEST")
    with tempfile.TemporaryDirectory() as td:
        # 批567:_rungate_merged() 會掃真機器的 RUNGATE_2*.json 史,而且史優先於傳進來那份。
        # 合成檢只准驗自己合成的東西——史掃描也指進暫存夾,否則機器上有一份 24h 內的真報告就把 ⑨ 判成紅燈。
        os.environ["VIA_RUNGATE_DIR"] = td
        # 批568:panorama 是 check() 的第二個真機器來源,會把 install 直接覆蓋成 BLOCKED_PANORAMA。
        # 指到暫存夾一個不存在的檔=那道閘在合成檢裡是啞的(生產行為零變更)。
        os.environ["VIA_PANORAMA_LATEST"] = str(Path(td) / "no_panorama.json")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "none.json")
        c0 = check()
        good_family = {"verdict": "GREEN", "python": {"state": "OK"},
                       "summary": {"required_ok": 3, "required_n": 3, "engines_ok": 3, "engines_n": 3}}
        Path(td, "one.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "one.json")
        os.environ["VIA_INSTALL_REQUIRED_FAMILIES"] = "vrn"  # 舊繞門形：不得縮減 L19 必驗族
        c1 = check()
        incomplete = {**good_family, "summary": {**good_family["summary"], "engines_ok": 0, "engines_n": 0}}
        Path(td, "zero.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": incomplete, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "zero.json")
        c2 = check()
        Path(td, "both.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": good_family, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "both.json")
        c3 = check()
        no_libs = {**good_family, "summary": {**good_family["summary"], "required_ok": 0, "required_n": 0}}
        Path(td, "nolibs.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": no_libs, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "nolibs.json")
        c_libs = check()
        malformed = {**good_family, "summary": {**good_family["summary"], "required_ok": "broken"}}
        Path(td, "malformed.json").write_text(json.dumps({"verdict": "GREEN", "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "families": {"vdf": malformed, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "malformed.json")
        c_bad = check()
        Path(td, "future.json").write_text(json.dumps({"verdict": "GREEN", "ts": "2099-01-01T00:00:00", "families": {"vdf": good_family, "vrn": good_family}}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "future.json")
        c_future = check()
        Path(td, "old.json").write_text(json.dumps({"verdict": "GREEN", "ts": "2020-01-01T00:00:00"}), encoding="utf-8")
        os.environ["VIA_RUNGATE_LATEST"] = str(Path(td) / "old.json")
        c4 = check()
        if sv is None:
            os.environ.pop("VIA_RUNGATE_LATEST", None)
        else:
            os.environ["VIA_RUNGATE_LATEST"] = sv
        if sr is None:
            os.environ.pop("VIA_INSTALL_REQUIRED_FAMILIES", None)
        else:
            os.environ["VIA_INSTALL_REQUIRED_FAMILIES"] = sr
        if sd is None:
            os.environ.pop("VIA_RUNGATE_DIR", None)
        else:
            os.environ["VIA_RUNGATE_DIR"] = sd
        if sp_pan is None:
            os.environ.pop("VIA_PANORAMA_LATEST", None)
        else:
            os.environ["VIA_PANORAMA_LATEST"] = sp_pan
        chk("⑨ 安裝核可 L19:缺報告/單族繞閘/零測站/零必要庫/壞計數/未來或過期皆 BLOCKED；VDF+VRN 完整 GREEN 且 24h 內才 INSTALL_OK",
            all(c["install"] == "BLOCKED_UNITEST" for c in (c0, c1, c2, c_libs, c_bad, c_future, c4))
            and set(c1["coverage"]) == {"vdf", "vrn"}
            and c3["install"] == "INSTALL_OK" and set(c3["coverage"]) == {"vdf", "vrn"},
            f"(缺={c0['install']} / 單族={c1['install']} / 零站={c2['install']} / 零庫={c_libs['install']} / 壞值={c_bad['install']} / 未來={c_future['install']} / 雙族={c3['install']} / 舊={c4['install']})")
        s = snapshot()
        res = write_outputs(s, Path(td) / "out", publish=False)
        md = (Path(td) / "out" / "VIA_Handover_ONEPAGE.md").read_text(encoding="utf-8")
        pg = (Path(td) / "out" / "VIA_UI_CentralGovernanceConsole_v0100.html").read_text(encoding="utf-8")
        chk("⑩ 一頁交接 + 頁(零 CDN;九主段齊;尾版詳細 handover 全文在八段;預設落暫存夾不入倉;--publish 才入倉)", not res["published"] and all(k in md for k in ("## 一 · 政策庫", "## 二 · 安裝核可", "## 五 · 指令與參數", "## 六 · 註冊稽核", "## 七 · 自動編號註冊表", "## 八 · 交接本文", "## 九 · 掉球清單"))
            and f"來源 {s['handover'].get('src')}" in md and _last_h2_demoted(s["handover"].get("text") or "") in md   # 批511:不釘固定字串,驗「尾版全文真的在八段」(最後一個 ## 標題降級後在頁裡)
            and "<script src" not in pg and "<link rel" not in pg and "Veritas Central Governance Console" in pg, f"({len(md)} 字 · 頁 {len(pg)//1024} KB)")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]     # 不讀自測本身的字串(LL 自我引用)
    chk("⑪ 零網路 · 預設只讀(無 requests/httpx/duckdb/SQL；元件冊只在 registry-sync --apply 明示後原子寫)",
        all(("import " + k) not in code for k in ("requests", "httpx", "duckdb")) and "CREATE " not in code
        and "registry-sync" in code and "if apply:" in code and "os.replace" in code)
    pr, bl = prompt_doc(), dropped_balls()
    gs = grid_stations()
    chk("⑫ 批508:接手提示詞(docs 尾版;含 A 開場/B 收尾/C 格式)與掉球清單(≥12 列)嵌入一頁交接 〇/九 段;格子 PYCODE/自指站標「特殊」不當缺",
        pr["state"] == "OK" and all(k in pr["text"] for k in ("## A", "## B", "## C")) and bl["state"] == "OK" and bl["n"] >= 12
        and "## 〇 · 接手提示詞" in md and "## 九 · 掉球清單" in md and not any(x["present"] is False for x in gs["stations"] if x["path"] in ("", "PYCODE")),
        f"({pr.get('src')} · {bl.get('src')} 列 {bl.get('n')} 未結 {bl.get('open')} · 格子在位 {sum(1 for x in gs['stations'] if x['present'] is True)} 特殊 {sum(1 for x in gs['stations'] if x['present'] == '特殊')})")
    inv = component_registry()
    live = live_components()
    chk("⑬ 元件自動編號冊完整覆蓋尾版引擎/模組/類別/函數/功能/短令/套件/環境；AST 零解析錯；代號穩定且只增不減",
        inv["state"] == "OK" and inv["active"] == len(live["rows"]) and not live["parse_errors"]
        and not au.get("inventory_missing") and {"engine", "module", "function", "feature", "tool", "package", "environment"} <= set(inv["counts"]),
        f"(ACTIVE {inv.get('active')}/{len(live['rows'])} · {inv.get('counts')} · parse_error {len(live['parse_errors'])})")
    with tempfile.TemporaryDirectory() as td:
        rp = Path(td) / "inventory.json"
        p0 = registry_sync(False, rp)
        plan_wrote = rp.exists()
        p1 = registry_sync(True, rp)
        codes1 = {r["key"]: r["code"] for r in (_json(rp) or {}).get("records", [])}
        p2 = registry_sync(True, rp)
        codes2 = {r["key"]: r["code"] for r in (_json(rp) or {}).get("records", [])}
        tampered = _json(rp)
        tampered["records"][0]["source"] = "selftest/tampered"
        rp.write_text(json.dumps(tampered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        before = rp.read_bytes()
        p3 = registry_sync(False, rp)
        chk("⑭ registry-sync 預設 PLAN 零寫且如實列變更；--apply 才建冊；第二次同步 new=0 且既有代號完全不變",
            p0["state"] == "PLAN" and not plan_wrote and p1["new"] == p1["expected"]
            and p2["new"] == 0 and codes1 == codes2 and len(codes1) == p1["expected"]
            and p3["changed"] == 1 and rp.read_bytes() == before)
    with tempfile.TemporaryDirectory() as td15:
        fp = Path(td15) / "FAMILY_latest.json"
        fp.write_text(json.dumps({"state": "PARTIAL", "ts": "2026-09-15T08:00:00", "home": "/x/VIA_CentralGovernanceFamily_b514",
                                  "files": {"members": {"console": {"state": "OK"}, "engine": {"state": "OK"}}},
                                  "members": {"console": {"state": "AMBER", "stamp": "20260915_080000"}, "router": {"state": "ABSENT", "why": "尚未跑"}}}, ensure_ascii=False), encoding="utf-8")
        _sv = os.environ.get("VIA_CGFAMILY_LATEST")
        os.environ["VIA_CGFAMILY_LATEST"] = str(fp)
        try:
            cg_ok = cg_family()
            os.environ["VIA_CGFAMILY_LATEST"] = str(Path(td15) / "none.json")
            cg_absent = cg_family()
        finally:
            if _sv is None:
                os.environ.pop("VIA_CGFAMILY_LATEST", None)
            else:
                os.environ["VIA_CGFAMILY_LATEST"] = _sv
        md15 = onepage_md({**s, "cg_family": cg_ok})
        pg15 = page_html({**s, "cg_family": cg_ok})
    chk("⑮ 批514 中央治理家族段:FAMILY_latest.json 讀成員態/成員件 md5 態;缺=ABSENT 誠實;一頁 十一段 + 頁卡/表列成員",
        cg_ok["state"] == "PARTIAL" and cg_ok["members"]["console"]["state"] == "AMBER" and cg_ok["members"]["console"]["snapshot"] == "20260915_080000"
        and cg_ok["files"] == {"console": "OK", "engine": "OK"} and cg_ok["home"] == "VIA_CentralGovernanceFamily_b514" and cg_absent["state"] == "ABSENT"
        and "## 十一 · 中央治理家族" in md15 and "console:AMBER · 20260915_080000" in md15 and "router:ABSENT" in md15 and "中央治理家族(批514" in pg15 and "20260915_080000" in pg15)
    with tempfile.TemporaryDirectory() as td16:
        fp16 = Path(td16) / "VTMRA_latest.json"
        fp16.write_text(json.dumps({"verdict": "YELLOW", "ts": "2026-09-15T18:00:00", "results": [{"id": "eng063", "state": "OK"}, {"id": "talib", "state": "ABSENT"}], "reasons": ["TA-Lib 未裝"]}, ensure_ascii=False), encoding="utf-8")
        _sv16 = os.environ.get("VIA_VTMRA_LATEST")
        os.environ["VIA_VTMRA_LATEST"] = str(fp16)
        try:
            vt_ok = vtmra()
            os.environ["VIA_VTMRA_LATEST"] = str(Path(td16) / "none.json")
            vt_absent = vtmra()
        finally:
            if _sv16 is None:
                os.environ.pop("VIA_VTMRA_LATEST", None)
            else:
                os.environ["VIA_VTMRA_LATEST"] = _sv16
        md16 = onepage_md({**s, "vtmra": vt_ok})
        pg16 = page_html({**s, "vtmra": vt_ok})
    chk("⑯ 批516 VTMRA 家族測試閘段:VTMRA_latest.json 讀判定/成員態/理由;缺=ABSENT 誠實;四段一行 + 頁卡",
        vt_ok["state"] == "YELLOW" and vt_ok["members"] == {"eng063": "OK", "talib": "ABSENT"} and vt_absent["state"] == "ABSENT"
        and "VTMRA 家族測試閘(批516" in md16 and "'talib': 'ABSENT'" in md16 and "VTMRA 家族測試閘(批516)" in pg16)
    with tempfile.TemporaryDirectory() as td17:
        D17 = Path(td17)
        now17 = datetime.now()
        fam_ok = lambda: {"verdict": "GREEN", "python": {"state": "OK"}, "summary": {"required_ok": 3, "required_n": 3, "engines_ok": 5, "engines_n": 5}}
        (D17 / "RUNGATE_20260915_080000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=6)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vdf": fam_ok()}}), encoding="utf-8")
        (D17 / "RUNGATE_20260915_180000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=1)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vrn": fam_ok()}}), encoding="utf-8")
        (D17 / "RUNGATE_latest.json").write_text((D17 / "RUNGATE_20260915_180000.json").read_text(encoding="utf-8"), encoding="utf-8")
        _sv = {k: os.environ.get(k) for k in ("VIA_RUNGATE_LATEST", "VIA_RUNGATE_DIR")}
        os.environ["VIA_RUNGATE_LATEST"] = str(D17 / "RUNGATE_latest.json"); os.environ["VIA_RUNGATE_DIR"] = str(D17)
        try:
            r17 = rungate()
            (D17 / "RUNGATE_20260915_080000.json").write_text(json.dumps({"ts": (now17 - timedelta(hours=30)).isoformat(timespec="seconds"), "verdict": "GREEN", "families": {"vdf": fam_ok()}}), encoding="utf-8")
            r17b = rungate()
        finally:
            for k, v in _sv.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    chk("⑰ 批517 安裝核可看兩族各自最新一跑(vdf 早跑+vrn 晚跑各自 GREEN=INSTALL_OK;vdf 那跑逾 24h 則 vdf 家族未測=BLOCKED)",
        r17["install"] == "INSTALL_OK" and set(r17["coverage"]) == {"vdf", "vrn"} and any(x.startswith("vdf:RUNGATE_20260915_080000") for x in r17.get("used", []))
        and r17b["install"] == "BLOCKED_UNITEST" and any("vdf" in x for x in r17b["reasons"]), f"({r17.get('used')} / {r17b.get('reasons')})")
    with tempfile.TemporaryDirectory() as td18:
        fp18 = Path(td18) / "FAMILY_latest.json"
        fp18.write_text(json.dumps({"state": "PARTIAL", "ts": "2026-09-15T12:00:00", "home": "/x/VIA_CentralGovernanceFamily_b514", "files": {"members": {}},
                                    "members": {"console": {"state": "RED", "stamp": "20260915_113543", "cycles_reading": {"ts": "2026-09-15T12:00:00", "n": 4, "live": 0, "by_zone": {"退役": 3, "收容": 1}, "verdict": "GREEN"}}}}, ensure_ascii=False), encoding="utf-8")
        _sv18 = os.environ.get("VIA_CGFAMILY_LATEST")
        os.environ["VIA_CGFAMILY_LATEST"] = str(fp18)
        try:
            cg18 = cg_family()
        finally:
            if _sv18 is None:
                os.environ.pop("VIA_CGFAMILY_LATEST", None)
            else:
                os.environ["VIA_CGFAMILY_LATEST"] = _sv18
        md18 = onepage_md({**s, "cg_family": cg18})
        pg18 = page_html({**s, "cg_family": cg18})
        md18b = onepage_md({**s, "cg_family": {**cg18, "cycles": None}})
    chk("⑱ 批518 十一段 G17 循環判讀(L38):FAMILY_latest console.cycles_reading → 圈數/活樹/分區/活樹判定一行入一頁與頁;缺=ABSENT 誠實",
        (cg18.get("cycles") or {}).get("live") == 0 and "4 圈 · 活樹 0 · 退役 3 · 收容 1 → 活樹 GREEN" in md18 and "G17 循環判讀(批518" in pg18 and "循環判讀:ABSENT" in md18b)
    with tempfile.TemporaryDirectory() as td19:
        T19 = Path(td19)
        (T19 / "uc.json").write_text(json.dumps({"ts": "2026-09-15T13:00:00", "n": 2, "by_family": {"vrn": 1, "central": 1}, "pages": [{"page": "VIA_UI_VRNControlTower_v0100.html", "family": "vrn", "lamp": "GREEN", "owner": "VRN_ENG079_ControlTower_v0100.py", "refresh": "via-vrnui", "path": str(T19 / "uc.json"), "exists": True, "fresh": True}, {"page": "GHOST.html", "family": "central", "lamp": "ABSENT", "owner": "", "refresh": "", "path": "/nope", "exists": False, "fresh": False}]}, ensure_ascii=False), encoding="utf-8")
        (T19 / "wf.json").write_text(json.dumps({"id": "vrn_logic_nlp", "verdict": "GREEN", "ts": "2026-09-15T13:01:00", "profile": "test", "counts": {"GREEN": 3}, "results": [{"id": "vrn_logic", "state": "GREEN", "why": ""}]}, ensure_ascii=False), encoding="utf-8")
        (T19 / "db.json").write_text(json.dumps({"verdict": "YELLOW", "ts": "2026-09-15T13:02:00", "n_tables": 51, "categories": [{"cat": "價量", "lamp": "GREEN", "n": 5, "newest": "2026-09-12", "worst_lag": 3}, {"cat": "籌碼", "lamp": "YELLOW", "n": 3, "newest": "2026-09-01", "worst_lag": 14}]}, ensure_ascii=False), encoding="utf-8")
        _sv19 = {k: os.environ.get(k) for k in ("VIA_UI_CONTRACT_LATEST", "VIA_WORKFLOW_LATEST", "VIA_DB_SUMMARY_LATEST")}
        try:
            os.environ["VIA_UI_CONTRACT_LATEST"] = str(T19 / "uc.json"); os.environ["VIA_WORKFLOW_LATEST"] = str(T19 / "wf.json"); os.environ["VIA_DB_SUMMARY_LATEST"] = str(T19 / "db.json")
            uw = ui_workflow()
            os.environ["VIA_UI_CONTRACT_LATEST"] = str(T19 / "none.json"); os.environ["VIA_WORKFLOW_LATEST"] = str(T19 / "none.json"); os.environ["VIA_DB_SUMMARY_LATEST"] = str(T19 / "none.json")
            uw_absent = ui_workflow()
        finally:
            for k, v in _sv19.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        md19 = onepage_md({**s, "ui_workflow": uw})
        pg19 = page_html({**s, "ui_workflow": uw})
        md19b = onepage_md({**s, "ui_workflow": uw_absent})
    chk("⑲ 批519 十二段 U/I 對接與工作流:契約頁(在=連結/不在=ABSENT)· 工作流最新一跑逐節點 · 庫分類每類一燈入一頁與頁;三件缺=ABSENT 誠實",
        uw["state"] == "OK" and uw["n"] == 2 and uw["absent"] == ["GHOST.html"] and uw["workflow"]["state"] == "GREEN" and uw["db"]["state"] == "YELLOW"
        and "## 十二 · U/I 對接與工作流" in md19 and "[GREEN] vrn · VIA_UI_VRNControlTower_v0100.html · 擁有者 VRN_ENG079_ControlTower_v0100.py · 再生 via-vrnui" in md19 and "[ABSENT] central · GHOST.html" in md19
        and "工作流最新一跑 GREEN · vrn_logic_nlp" in md19 and "價量 GREEN(表 5 最新 2026-09-12 滯後 3)" in md19 and "U/I 對接與工作流(批519" in pg19 and "<a href='file:///" in pg19 and "GHOST.html" in pg19
        and uw_absent["state"] == "ABSENT" and uw_absent["workflow"]["state"] == "ABSENT" and uw_absent["db"]["state"] == "ABSENT" and "U/I 契約 ABSENT" in md19b)
    sg = source_guard()
    chk("⑳ 批568 來源閘:⑨ 這條路(check/rungate/_rungate_merged)讀的每個真機器來源都配覆寫鍵,且自測 ⑨ 區塊每個鍵都關進沙盒",
        sg["state"] == "OK" and len(sg["keys"]) >= 3 and "VIA_PANORAMA_LATEST" in sg["keys"],
        f"(來源 {len(sg['disk'])} · 覆寫鍵 {sg['keys']} · 沒配鍵 {sg['unguarded'] or '無'} · 沒關沙盒 {sg['unsandboxed'] or '無'})")
    print(f"  [計] 二十檢 OK {20 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


# ===== VCGC panorama: central orchestration, no second fetch/router implementation =====
PANORAMA_MONTHS = 2
PANORAMA_BATCH_SIZE = 20
PANORAMA_STATION_TIMEOUT = 600
PANORAMA_FETCH_TIMEOUT = 7200
PANORAMA_CONTRACT = HERE / 'VIA_Panorama_Contract_v0100.json'
PANORAMA_OK = {'GREEN', 'COMPLETE', 'APPLIED', 'NOT_NEEDED'}


def def_panorama_atomic(path: Path, data: dict, indent: int = 2) -> None:
    import uuid
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=indent, default=str), encoding='utf-8')
    os.replace(tmp, path)


def def_panorama_dates(months: int = PANORAMA_MONTHS, end: str = '') -> tuple[str, str]:
    import calendar
    from datetime import date, timedelta, timezone
    if not 1 <= months <= 24:
        raise ValueError('months must be 1..24')
    # Default excludes the still-changing current Taiwan calendar day.
    hi = date.fromisoformat(end) if end else datetime.now(timezone(timedelta(hours=8))).date() - timedelta(days=1)
    n = hi.year * 12 + hi.month - 1 - months
    year, month0 = divmod(n, 12)
    lo = date(year, month0 + 1, min(hi.day, calendar.monthrange(year, month0 + 1)[1]))
    return lo.isoformat(), hi.isoformat()


def def_panorama_collect(run_dir: Path) -> list:
    """Collect existing evidence before tests overwrite latest; never re-run merely to read logs."""
    import shutil
    evidence_dir = run_dir / 'previous_evidence'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    found = []
    for filename in ('ENGINE_BUS_latest.json', 'ENGINE_BUS_progress.json'):
        source = REPORTS / 'engine_bus' / filename
        data = _json(source)
        if not data:
            continue
        shutil.copy2(source, evidence_dir / filename)
        for row in data.get('results', []):
            if row.get('family') not in ('vdf', 'vrn'):
                continue
            copy = dict(row)
            log = Path(str(row.get('stdout_log') or ''))
            if row.get('stdout_log') and log.is_file() and log.resolve().is_relative_to((REPORTS / 'engine_bus').resolve()):
                shutil.copy2(log, evidence_dir / log.name)
                copy['evidence_log'] = str((evidence_dir / log.name).resolve())
                text = log.read_text(encoding='utf-8-sig', errors='replace')
                copy['failed_assertions'] = [x for x in text.splitlines() if re.match(r'^\s*\[FAIL\]', x)]
            copy['evidence_source'] = filename
            found.append(copy)
    return found


def def_panorama_resolve_dbs() -> dict:
    """Use declared central data home; ambiguous copies block writes instead of choosing newest."""
    wanted = {'prices': ('VIA_DB_VDF_TW_MARKET', 'vdf_tw_market.duckdb'),
              'etf': ('VIA_DB_ACTIVETWETF', 'ActiveTWETF.duckdb')}
    home_mod = _load('panorama_datahome', _newest(HERE, 'CGC_MDL123_DataHome_v*.py'))
    h, origin = home_mod.resolve_home(VIA)
    hd, hf = home_mod.home_dir(h)
    out = {}
    for key, (env_name, name) in wanted.items():
        explicit = os.environ.get(env_name)
        if explicit:
            candidates = [Path(explicit)]
            source = env_name
        else:
            candidates = ([hf] if hf and hf.name.lower() == name.lower() else
                          [p for p in hd.rglob('*.duckdb') if p.name.lower() == name.lower() and not home_mod._is_sandbox(str(p))] if hd.is_dir() else [])
            source = str(origin)
        candidates = list({p.resolve(): p for p in candidates if p and p.is_file()}.values())
        if len(candidates) == 1:
            out[key] = {'state': 'GREEN', 'path': str(candidates[0].resolve()), 'source': source, 'env': env_name}
        else:
            out[key] = {'state': 'BLOCKED_DB' if not candidates else 'AMBIGUOUS_DB',
                        'path': '', 'source': source, 'candidates': [str(p) for p in candidates],
                        'why': '正庫缺席或多份，須以中央資料家/明示路徑對齊；不建空白替代庫'}
    return out


def def_panorama_sync_laws(run_dir: Path, contract: dict) -> dict:
    import shutil
    path = _newest(HERE, 'VIA_Policy_Laws_SSOT_v*.json')
    data = _json(path)
    if not data:
        return {'state': 'BLOCKED', 'why': '中央政策庫缺/壞；不建立第二份政策正本'}
    changed = 0
    for field, prefix in (('laws', 'L'), ('lessons', 'LL')):
        rows = data.setdefault(field, [])
        existing_keys = {r.get('key') for r in rows}
        nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(prefix + r'(\d+)', str(r.get('id', ''))))]
        counter = max(nums, default=0)
        for item in contract.get(field, []):
            if item['key'] in existing_keys:
                continue
            counter += 1
            rows.append({**item, 'id': f'{prefix}{counter:02}', 'batch': 'panorama-v0103'})
            changed += 1
    if changed:
        shutil.copy2(path, run_dir / 'policy_before.json')
        def_panorama_atomic(path, data, indent=1)
    return {'state': 'APPLIED', 'new': changed, 'path': str(path)}


def def_panorama_sync_params(run_dir: Path, contract: dict) -> dict:
    import shutil
    path = _newest(HERE, 'VIA_InputConsole_Spec_v*.json')
    data = _json(path)
    if not data:
        return {'state': 'BLOCKED', 'why': 'InputConsole 正典缺席或損壞'}
    added = 0
    found = set()
    for family in data.get('families', {}).values():
        for group in family.get('groups', []):
            for item in group.get('items', []):
                if item['id'] not in contract.get('engine_params', {}):
                    continue
                found.add(item['id'])
                params = item.setdefault('params', [])
                for name in contract['engine_params'][item['id']]:
                    if name not in params:
                        params.append(name); added += 1
    missing = set(contract.get('engine_params', {})) - found
    if missing:
        return {'state': 'BLOCKED', 'why': '冊缺item: ' + ','.join(sorted(missing))}
    if added:
        shutil.copy2(path, run_dir / 'input_spec_before.json')
        def_panorama_atomic(path, data, indent=1)
    return {'state': 'APPLIED', 'new_params': added, 'path': str(path)}


def def_panorama_problem(row: dict, contract: dict) -> list:
    text = '\n'.join([str(row.get('why', '')), str(row.get('stdout_tail', '')),
                       *[str(x) for x in row.get('failed_assertions', [])]])
    matches = []
    for issue in contract.get('problem_types', []):
        if issue.get('pattern') and re.search(issue['pattern'], text, re.I):
            matches.append(issue['code'])
    return matches or (['TEST_ASSERTION'] if row.get('state') not in PANORAMA_OK else [])


def def_panorama_render(data: dict) -> str:
    def esc(v):
        return html.escape(str(v))
    def table(rows, cols):
        cells = ['<div class="scroll"><table><thead><tr>' + ''.join('<th>'+esc(label)+'</th>' for key,label in cols) + '</tr></thead><tbody>']
        for r in rows:
            color = 'good' if r.get('state') in PANORAMA_OK else 'bad' if r.get('state') in ('RED','ERROR') else 'pending'
            cells.append('<tr class="'+color+'">'+''.join('<td>'+esc(r.get(key,''))+'</td>' for key,label in cols)+'</tr>')
        return ''.join(cells)+'</tbody></table></div>'
    rows = data.get('results', [])
    tests = [r for r in rows if r.get('phase') == 'test']
    jobs = [r for r in rows if r.get('phase') != 'test']
    rules = data.get('contract', {}).get('problem_types', [])
    known = data.get('contract', {}).get('known_findings', [])
    prior = [{'id': r.get('id'), 'state':r.get('state'), 'why':'\n'.join(r.get('failed_assertions') or [r.get('why','')]),
              'stdout_log':r.get('evidence_log',r.get('stdout_log',''))} for r in data.get('previous_evidence',[]) if r.get('state') not in PANORAMA_OK and r.get('state') != 'PLAN']
    cols = [('id','項目'),('family','家族'),('phase','階段'),('state','狀態'),('seconds','秒'),('why','問題／處置'),('stdout_log','完整紀錄')]
    refresh = '<meta http-equiv="refresh" content="8">' if data.get('status') == 'RUNNING' else ''
    return '''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'''+refresh+'''<title>VIA 全景實測矩陣</title><style>
body{font:13px/1.6 "Segoe UI","Microsoft JhengHei",sans-serif;background:#f4f6f8;color:#172b3a;margin:0}header,main{max-width:1560px;margin:auto;padding:20px}header{border-bottom:3px solid #217b88}h1{font-size:23px;margin:0}h2{font-size:16px;margin-top:26px}p{margin:6px 0}.cards{display:flex;gap:10px;flex-wrap:wrap}.card{background:white;border:1px solid #dae3e9;padding:12px 18px;border-radius:7px}.card b{display:block;font-size:19px}.scroll{overflow:auto;background:white;border:1px solid #dce3e8;border-radius:6px}table{width:100%;border-collapse:collapse}th{background:#e9eff4;text-align:left;position:sticky;top:0}td,th{padding:8px 10px;border-bottom:1px solid #e3e9ed;vertical-align:top}td{white-space:pre-wrap;overflow-wrap:anywhere;max-width:650px}.bad td:first-child{border-left:4px solid #c35159}.pending td:first-child{border-left:4px solid #c69b35}.good td:first-child{border-left:4px solid #238771}input{padding:9px;border:1px solid #abbecb;border-radius:5px;width:300px;max-width:90%}summary{cursor:pointer;font-weight:600;padding:10px;background:#edf2f5}.muted{color:#5f7380}code{white-space:pre-wrap}</style>
<header><h1>VIA · VRN / VDF / VATETF(舊名 VETF)全景實測</h1><p>唯一治理入口：Veritas Central Governance Console</p><p>'''+esc(data.get('start',''))+' → '+esc(data.get('end',''))+' · 最近 '+esc(data.get('months',''))+' 個曆月 · '+esc(data.get('status',''))+'''</p><div class="cards"><div class="card">安裝核可<b>'''+esc(data.get('approval','BLOCKED'))+'''</b></div><div class="card">本輪已記錄<b>'''+str(len(rows))+'''</b></div><div class="card">待處理項目<b>'''+str(data.get('blockers',0))+'''</b></div></div></header><main>
<p class="muted">測試通過、擷取成功與資料完整分開判定。平日候選不是官方交易日曆；ETF 有快照日不代表每筆持股已完整驗證。既有欄位缺值、未扣當沖輸入、未驗證來源均保留待修。</p><input id="q" placeholder="搜尋站名、狀態、問題或解法" oninput="document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase()))">
<h2>本輪引擎測試</h2>'''+table(tests,cols)+'''<h2>查庫、缺口補抓、報告與環境驗收</h2>'''+table(jobs,cols)+'''<h2>已識別問題與本輪處置</h2>'''+table(known,[('code','代碼'),('state','狀態'),('finding','證據／影響'),('solution','本輪解法／下一輪')])+'''<details><summary>前次完整失敗證據</summary>'''+table(prior,[('id','站'),('state','狀態'),('why','失敗斷言'),('stdout_log','已保存紀錄')])+'''</details><details><summary>問題類型與解法手冊（類型不代表本機全部發生）</summary>'''+table(rules,[('code','類型'),('name','問題'),('solution','解法'),('auto','自動處理範圍')])+'''</details><details><summary>日期、環境與執行參數</summary><pre>'''+esc(json.dumps({k:data.get(k) for k in ('start','end','months','dbs','environments','parameters')},ensure_ascii=False,indent=2))+'''</pre></details></main></html>'''


def def_panorama_save(run_dir: Path, data: dict) -> None:
    import csv
    import uuid
    data['blockers'] = sum(r.get('state') not in PANORAMA_OK for r in data.get('results', []))
    data['updated_at'] = datetime.now().isoformat(timespec='seconds')
    def_panorama_atomic(run_dir / 'PANORAMA.json', data)
    if data.get('owns_lock'):
        def_panorama_atomic(REPORTS / 'panorama' / 'PANORAMA_latest.json', data)
    path = run_dir / 'PANORAMA.html'
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(def_panorama_render(data), encoding='utf-8')
    os.replace(tmp,path)
    cols = ['id','family','phase','state','seconds','why','stdout_log']
    with (run_dir / 'summary_matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=cols,extrasaction='ignore')
        writer.writeheader(); writer.writerows(data.get('results',[]))


def def_panorama_main(args: list) -> int:
    import contextlib
    import io
    def arg(flag, default=''):
        return args[args.index(flag)+1] if flag in args else default
    months = int(arg('--months', str(PANORAMA_MONTHS)))
    start, end = def_panorama_dates(months, arg('--end'))
    station_timeout = int(arg('--timeout', str(PANORAMA_STATION_TIMEOUT)))
    fetch_timeout = int(arg('--fetch-timeout', str(PANORAMA_FETCH_TIMEOUT)))
    batch_size = int(arg('--batch-size', str(PANORAMA_BATCH_SIZE)))
    if min(station_timeout,fetch_timeout,batch_size) < 1:
        raise ValueError('timeout and batch-size must be positive')
    apply = '--apply' in args
    fetch = '--fetch' in args
    run_dir = Path(arg('--out', str(REPORTS/'panorama'/datetime.now().strftime('%Y%m%d_%H%M%S'))))
    run_dir.mkdir(parents=True,exist_ok=True)
    contract = _json(PANORAMA_CONTRACT)
    if not contract:
        raise RuntimeError('中央 panorama 契約缺席；停止，不猜動詞')
    data = {'schema':'VIA.Panorama.v1', 'status':'RUNNING','approval':'BLOCKED', 'start':start,'end':end,
            'months':months,'contract':contract,'results':[], 'owns_lock':False, 'run_dir':str(run_dir.resolve()),
            'parameters':{'apply':apply,'fetch':fetch,'batch_size':batch_size,'timeout':station_timeout,'fetch_timeout':fetch_timeout}}
    data['previous_evidence'] = def_panorama_collect(run_dir)
    bus = _load('panorama_bus', _newest(HERE,'CGC_MDL148_EngineBus_v*.py'))
    catalog_rows = [r for r in bus.catalog() if r['family'] in ('vdf','vrn')]
    data['environments'] = {f:bus.python_for(f) for f in ('vdf','vrn')}
    def record(row, phase):
        row = {**row, 'phase':phase}
        row['problem_types'] = def_panorama_problem(row,contract)
        data['results'].append(row)
        def_panorama_save(run_dir,data)
        print(f"[PANORAMA] {row.get('id')} · {row.get('state')} · {row.get('why','')}",flush=True)
        return row
    def call(item, params=None, phase='test', timeout=station_timeout):
        try:
            r = bus.call(item,params=params,timeout=timeout,apply=apply,catalog_rows=catalog_rows,
                         profile='test' if phase=='test' else 'run')
        except Exception as exc:
            r = {'id':item,'state':'ERROR','why':f'{type(exc).__name__}: {exc}'}
        if params and params.get('report'):
            detail = _json(Path(params['report']))
            if detail:
                if 'missing_keys' in detail:
                    summary = f"候選缺鍵 {detail['missing_keys']} · 品質缺列 {len(detail.get('quality_gaps', []))} · 抓回 {detail.get('fetched',0)} · 新插 {detail.get('inserted',0)} · {detail.get('state')}"
                else:
                    coverage = detail.get('coverage', detail)
                    summary = f"ETF {len(coverage.get('etfs', []))} 檔 · 缺快照 {sum(x.get('missing_days',0) for x in coverage.get('etfs', []))} 日格 · 快照日期覆蓋尚非成分完整性驗證"
                r['why'] = summary + ' · ' + str(r.get('why',''))
                r['detail_report'] = params['report']
        return record(r,phase)
    def delegated(name, function, phase):
        log=run_dir/(name+'.log')
        try:
            # Console progress remains visible; detailed module reports keep their own evidence.
            result=function()
            if not isinstance(result,dict):
                result={'result':result}
            log.write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
            state=result.get('verdict',result.get('state','UNKNOWN'))
            return record({'id':name,'state':state,'why':str(result.get('why','')),'stdout_log':str(log)},phase)
        except Exception as exc:
            import traceback
            log.write_text(traceback.format_exc(),encoding='utf-8')
            return record({'id':name,'state':'ERROR','why':str(exc),'stdout_log':str(log)},phase)
    lock=None
    try:
        if apply:
            lock_path=REPORTS/'panorama'/'panorama_runner.lock'
            lock_path.parent.mkdir(parents=True,exist_ok=True)
            lock=lock_path.open('a+b')
            lock.seek(0)
            if os.name=='nt':
                import msvcrt
                if not lock.read(1):
                    lock.write(b'0');lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            data['owns_lock']=True
        data['dbs']=def_panorama_resolve_dbs()
        for key,row in data['dbs'].items():
            record({'id':'db_'+key,**row},'database')
            if row['state']=='GREEN':
                os.environ[row['env']]=row['path']
        if apply:
            for fam,env in data['environments'].items():
                parents=Path(env['python']).parents
                formal=any(p.name.lower().startswith('via_') for p in list(parents)[:3])
                if not formal or not Path(env['python']).is_file():
                    record({'id':'env_'+fam,'state':'BLOCKED_ENV','why':'非正式 via_ 家族境：'+str(env)},'environment')
            if any(r['state']=='BLOCKED_ENV' for r in data['results']):
                return 2
            delegated('policy_append',lambda:def_panorama_sync_laws(run_dir,contract),'governance')
            delegated('input_params',lambda:def_panorama_sync_params(run_dir,contract),'governance')
            delegated('registry_sync',lambda:registry_sync(apply=True),'governance')
            catalog_rows = [r for r in bus.catalog() if r['family'] in ('vdf','vrn')]
        # Run all independent test stations; a failed VRN station never hides VDF/VETF results.
        tested={}
        for row in catalog_rows:
            tested[row['id']]=call(row['id'])
        if apply:
            tests=list(tested.values())
            counts={st:sum(r.get('state')==st for r in tests) for st in {r.get('state') for r in tests}}
            def_panorama_atomic(REPORTS/'engine_bus'/'ENGINE_BUS_latest.json',{'schema':'VIA.EngineBus.v2','profile':'test','ts':datetime.now().isoformat(timespec='seconds'),'results':tests,'catalog':catalog_rows,'counts':counts,'family':'vdf,vrn','apply':True,'apply_families':['vdf','vrn'],'ids':[],'live_n':len(tests),'census':bus._census_block()})
        if not apply:
            record({'id':'workstation_execution','state':'NOT_EXECUTED','why':'唯讀預覽；未啟動家族引擎或網路'},'execution')
            return 2
        # Always inspect the DB before deciding whether to fetch, even on later rounds.
        for item,key in (('tw_history','prices'),('etf_holdings_daily','etf')):
            if data['dbs'][key]['state']!='GREEN':
                record({'id':item+'_gap','state':'BLOCKED_DEPENDENCY','why':'正庫尚未唯一定位'},'gap')
                continue
            params={'gap-mode':'plan','start':start,'end':end,'report':str(run_dir/(item+'_gap_before.json'))}
            if key=='prices':
                params['db']=data['dbs'][key]['path']
            plan=call(item,params,'gap')
            if fetch and tested.get(item,{}).get('state')=='GREEN' and plan.get('state')=='GREEN':
                params.update({'gap-mode':'fetch','report':str(run_dir/(item+'_gap_after.json'))})
                if key=='prices':
                    params['batch-size']=str(batch_size)
                else:
                    params['max-days']='0'
                call(item,params,'fetch',fetch_timeout)
            elif fetch:
                record({'id':item+'_fetch','state':'BLOCKED_DEPENDENCY','why':'對應自測或查庫未通過，保留待下一輪'},'fetch')
        # No speculative fetch of unbounded lanes: declare uncovered scope explicitly.
        for item in contract.get('deferred_fetch',[]):
            record({'id':item['id'],'family':'vdf','state':'DEFERRED','why':item['why']},'next_round')
        vrn=[r for key,r in tested.items() if r.get('family')=='vrn']
        if vrn and all(r.get('state')=='GREEN' for r in vrn) and data['dbs']['prices']['state']=='GREEN':
            closing=_load('panorama_closeout',_newest(HERE,'CGC_MDL141_ClosingGate_v*.py'))
            delegated('vrn_real_reports',lambda:closing.closeout('vrn',run=True,
                      report_dir=arg('--input-dir',str(VIA/'functional modules/VRN/input/incoming')),
                      db=Path(data['dbs']['prices']['path'])),'real_reports')
        else:
            record({'id':'vrn_real_reports','family':'vrn','state':'BLOCKED_DEPENDENCY',
                    'why':'VRN 自測或正庫未通過；完整失敗斷言已保存，未假報原始報告通過'},'real_reports')
        gate=_load('panorama_rungate',_newest(HERE,'CGC_MDL137_RunGate_v*.py'))
        delegated('environment_gate',lambda:gate.run(['vdf','vrn'],mode='fast'),'environment')
        try:
            def_panorama_save(run_dir,data)
            write_outputs(snapshot(),OUTDIR,publish=True)
        except Exception as exc:
            record({'id':'handover','state':'ERROR','why':str(exc)},'governance')
    except Exception as exc:
        import traceback
        (run_dir/'fatal.log').write_text(traceback.format_exc(),encoding='utf-8')
        record({'id':'panorama','state':'ERROR','why':str(exc),'stdout_log':str(run_dir/'fatal.log')},'execution')
    finally:
        data['status']='FINISHED'
        data['approval']='BLOCKED'
        def_panorama_save(run_dir,data)
        # Existing L19 check remains authoritative and is never overwritten to green.
        data['gate']=check()
        if not data['blockers'] and data['gate'].get('install')=='INSTALL_OK':
            data['approval']='INSTALL_OK'
        def_panorama_save(run_dir,data)
        if apply and data.get('owns_lock'):
            try:
                write_outputs(snapshot(),OUTDIR,publish=True)
            except Exception as exc:
                (run_dir/'handover_error.txt').write_text(str(exc),encoding='utf-8')
        if lock is not None:
            lock.close()
        print('[PANORAMA_REPORT] '+str((run_dir/'PANORAMA.html').resolve()),flush=True)
    return 0 if data['approval']=='INSTALL_OK' else 2


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print(f"=== Veritas Central Governance Console(CGC_MDL149 v{VERSION})· 二十檢自測(零網路;預設只讀)===")
        return selftest()
    verb = a[0] if a else "status"
    if verb == "status":
        return status()
    if verb in ("page", "onepage"):
        s = snapshot()
        res = write_outputs(s, OUTDIR, publish="--publish" in a)
        print(f"[VCGC] 一頁交接 + 頁 → {res['out']}" + (f" · 已發佈 {res['published']}" if res["published"] else " (未入倉;--publish 才入倉)"))
        return 0
    if verb == "panorama":
        return def_panorama_main(a[1:])
    if verb == "audit":
        au = audit()
        print(f"[VCGC 註冊稽核] 中央冊 ACTIVE {au['inventory_active']}/{au['inventory_expected']} · 全類缺 {len(au['inventory_missing'])} · 家族 {au['families']} 已登 {au['registered']} 未登 {len(au['unregistered'])} · 操作介面掛載 {au['interface_registered']}")
        for r in au["unregistered"]:
            print(f"  未登 {r['newest']}({r['dir']})")
        if au["interface_gaps"]:
            print(f"  [介面分列] {len(au['interface_gaps'])} 個內部家族已在中央冊、未設操作介面(非未註冊；via-vcgc register-plan 看清單)")
        return 0
    if verb == "register-plan":
        # 中央編號冊由 registry-sync 管；此處只列尚無操作介面的內部家族，不混為「未註冊」。
        au = audit()
        OUTDIR.mkdir(parents=True, exist_ok=True)
        lines = [f"# VCGC 操作介面掛載建議 {datetime.now():%Y-%m-%d %H:%M} · 中央冊已覆蓋；無操作介面家族 {len(au['interface_gaps'])}(只列不寫)", ""]
        for r in au["interface_gaps"]:
            q = VIA / r["dir"] / r["newest"]
            has_st = False
            try:
                has_st = "--selftest" in q.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
            lines.append(f"- {r['newest']}({r['dir']})· 自測旗 {'有' if has_st else '無'} → " + (f"格子站:add(\"{r['family']} 自測\", newest(\"{r['family']}_v*.py\", VIA / \"{r['dir']}\"), [\"--selftest\"], \"rc0\", 300)" if has_st else "先補 --selftest 再登站;Deck/Register 依其動詞另議"))
        (OUTDIR / "REGISTER_PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines[:30]) + (f"\n… 共 {len(lines) - 2} 條 → {OUTDIR / 'REGISTER_PLAN.md'}" if len(lines) > 30 else ""))
        return 0
    if verb == "registry-sync":
        r = registry_sync(apply="--apply" in a)
        print(f"[VCGC 元件自動編號冊] {r['state']} · 活元件 {r['expected']} · 新 {r['new']} · 變更 {r['changed']} · 退役 {r['stale']} · AST錯 {len(r['parse_errors'])} · {r['counts']}")
        if r["state"] == "PLAN":
            print("  預設零寫；確認後才用 via-vcgc registry-sync --apply")
        if r["parse_errors"]:
            for e in r["parse_errors"][:10]: print(f"  [AST錯] {e['file']}:{e['why']}")
        return 0 if not r["parse_errors"] else 2
    if verb == "check":
        c = check()
        print(f"[VCGC 安裝核可] {c['install']} · RunGate {c['rungate']} · 齡 {c['age_h']} h · 必驗 {c['required_families']} · {c['law']}")
        for fam, v in (c.get("coverage") or {}).items(): print(f"  [{fam}] {'GREEN' if v.get('ok') else 'BLOCK'} · {v.get('why')}")
        for why in c.get("reasons") or []: print(f"  [阻擋] {why}")
        return 0 if c["install"] == "INSTALL_OK" else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
