#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_conflict_guard — 衝突機制總哨兵+壞環境黑名單守衛(TOOL-107,批106)
====================================================================
令:「檢查衝突機制 壞環境黑名單 從前一個進度測試 測試新增計畫 計畫無誤直接裝」。
C1 衝突機制總巡檢(八道,全部唯讀):
  ① 中央參數樞紐跨冊衝突(via-params 冊圈)
  ② canonical 未裁殘量(三子系統參數冊:多值且不在 canonical 區=未裁)
  ③ ETF 清冊名碼衝突(CONFLICT_PENDING_VERIFY 具名列示=黃,候實連定奪)
  ④ 雙世代裁決冊:QUEUED 必須歸零;HOLD/BLOCKED 具名列管
  ⑤ 存證冊完整性(存證件在位+現役件在位;缺=紅)
  ⑥ 語法版本閘冊有效性(檔在位+python_min 可解析)
  ⑦ R2 殘留(canonical 裁決含寫死絕對路徑=紅)
  ⑧ 啟動器鐵律殘留(bin/*.cmd 寫死版號=紅;L6 同規)
C2 壞環境黑名單守衛(冊:VIA_BadEnv_Blacklist 最新版):
  ⑨ 現行 VIA 根不得落於黑名單根之下
  ⑩ 活執行區零 0-byte 占位檔(bin/ + registry/ 頂層;HZ-01)
  ⑪ sys.path 不含 accelerator/(HZ-03 標準庫遮蔽)
  ⑫ PATH 不含黑名單根前綴(HZ-02;容器無 Windows PATH=誠實 SKIP)
  ⑬ 黑名單件不得為任何 bin 動詞的執行標的
誠實三態 OK/FAIL/SKIP;報告落 VIA_Reports;rc0=無紅(黃可過,具名列示)。
用法:
  via-conflict            → 全巡檢+報告
  via-conflict --selftest → 十四檢(沙盒零網路)

v0100→v0101(批618 操作員令「衝突哨兵 PATH」):
 (1) **冊寫了 action,工具沒做到**。黑名單冊 env_hazards 的 HZ-02 白紙黑字寫著
     action=「紅燈+PATH 換錨指令」——v0100 只做了紅燈那半邊,換錨指令從第一版起
     就沒有出現過。捕捉到卻不出手等於沒捕捉(批441 同一道教訓的第二次現身)。
     ⑫ 現在逐條印出命中、印出**黑名單冊自己寫的 reason**(L87 豁免/分類必附理由),
     並吐一段**操作員自己貼**的 PowerShell 換錨句。我不代設任何環境變數(不代設律)。
 (2) **剝離不是萬用解,盲剝會打斷 VRN**。量過:pdf2image 靠 PATH 找 pdftoppm,
     VRN_ENG058_TableOmni v0105 與 SUP_MDL747_OcrLaneRunner v0102 都點名 poppler;
     工作站那一條命中(…\OneDrive\Desktop\VRN\poppler\…\Library\bin)是**工具寄生在黑根**。
     照 v0100 的口徑判紅、再照直覺一把剝掉,VRN 的 PDF 取表道當場斷線——
     那就是「判錯的紅燈和假綠一樣傷」。⑫ 因此分兩類:純殘留→剝離句;
     帶工具嫌疑→**搬家句**(搬出黑根再換錨),而且明講容器 stat 不到工作站的碟,
     這是**嫌疑**不是斷言(沒讀過那個目錄就不准說裡面有什麼)。
 (3) **具名豁免走冊,不走我的手**。黑名單冊 v0102 新增 path_exemptions(出廠是空的),
     每一條必須帶 reason;缺 reason 一律判紅。豁免是裁定,裁定權在操作員。
 (4) **自測 ⑩ 過去在替整棵樹打分,不是在替工具打分**。v0100 的 ⑩ 寫
     `chk("⑩ 實樹巡檢煙測(rc0=無紅)", rc == 0)`——只要哨兵**正確地**抓到一件真衝突,
     run() 回 1,自測就紅,格上那一盞「衝突哨兵十檢」跟著紅。工具在盡責反而被判失職,
     而且紅燈上寫的是錯的名字。v0101 的 ⑩ 只煙測**工具本身**(不拋例外、十三道齊發、
     報告確實落地),樹乾不乾淨改由格上新開的「衝突哨兵實樹巡檢」那一盞誠實照。
     兩件事兩盞燈——一盞燈照兩件事,紅起來沒人知道在說哪一件。
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

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "conflict_guard_runs"
CMD_HARD_RX = re.compile(r"v\d{3,4}[a-z]?\.(py|ps1)")
ABS_PATH_RX = re.compile(r"OneDrive|Downloads|^[A-Za-z]:\\\\|C:\\\\", re.I)


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590/591;正典 SUP_MDL751_VIATailPick)=====
# 本群原本的行為:_newest(dirp, pat)
# 批590 量過:CGC 族 32 份 `newest` 是 **13 個行為群**,不是同一件事(最大兩群參數順序相反、
# 兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序)。所以正典把差異變成**明示選項**,
# 並逐群重放證零損失(15 種具名變體 × 6 組語料,90 組全同)。
# 這裡是**綁定**不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯(整條鏈指到舊引擎,沒人會發現)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
_newest = _TP_MOD.bind(order="rp")
# ===== [VIA:TAILPICK-BRIDGE:END] =====


def _jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _res(name: str, state: str, note: str = "", fix: list[str] | None = None) -> dict:
    r = {"name": name, "state": state, "note": note}
    if fix:
        r["fix"] = fix          # 一貼即用的修法句;由操作員親手貼(不代設律)
    return r


# ── C1 衝突機制八道 ──────────────────────────────────────────────
def c1_central_params(via: Path = VIA) -> dict:
    """① 跨冊衝突:直用 via-params 最新版之 find_conflicts(唯讀)"""
    mod_p = _newest(via / "supportive modules" / "registry", "via_params_central_v*.py")
    if mod_p is None:
        return _res("① 中央參數跨冊衝突", "SKIP", "樞紐缺(誠實)")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_vpc", mod_p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    records = [m.scan_book(b, via) for b in m.BOOKS]
    conflicts = m.find_conflicts(records)
    note = f"{len(conflicts)} 衝突(建議燈)"
    if conflicts:
        note += " · " + " | ".join(c["key"] for c in conflicts[:3])
    return _res("① 中央參數跨冊衝突", "OK" if len(conflicts) == 0 else "WARN", note)


def c1_canonical_residue(via: Path = VIA) -> dict:
    """② 多值未裁殘量(len(vals)>1 且不在 canonical)"""
    residue = 0
    for sub in ("VRN", "VDF", "VAP"):
        p = _newest(via / "functional modules" / sub, f"{sub}_Param_Registry_v*.json")
        if p is None:
            continue
        reg = _jload(p)
        by_name = {}
        for x in reg.get("params", []):
            by_name.setdefault(x["name"], set()).add(x["value"])
        canon = reg.get("canonical", {})
        residue += sum(1 for n, v in by_name.items() if len(v) > 1 and n not in canon)
    return _res("② canonical 未裁殘量", "OK" if residue == 0 else "FAIL", f"{residue} 鍵未裁")


def c1_etf_conflicts(via: Path = VIA) -> dict:
    p = (via / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
         / "config" / "TW_Active_ETF_Registry_v0100.json")
    if not p.exists():
        return _res("③ ETF 名碼衝突", "SKIP", "冊缺(誠實)")
    reg = _jload(p)
    con = [e["ticker"] for e in reg.get("etfs", []) if e.get("status") == "CONFLICT_PENDING_VERIFY"]
    pend = sum(1 for e in reg.get("etfs", []) if e.get("status") == "PENDING_VERIFY")
    return _res("③ ETF 名碼衝突", "WARN" if con else "OK",
                f"衝突 {len(con)}({','.join(con)})候實連定奪 · 待驗 {pend}")


def c1_twoera(via: Path = VIA) -> dict:
    p = _newest(via / "supportive modules" / "registry", "VIA_TwoEra_Verdicts_v*.json")
    if p is None:
        return _res("④ 雙世代裁決冊", "SKIP", "冊缺")
    d = _jload(p)
    st = {}
    for v in d.get("verdicts", []):
        st[v.get("status", "?")] = st.get(v.get("status", "?"), 0) + 1
    queued = st.get("QUEUED", 0)
    hold = st.get("HOLD", 0) + st.get("BLOCKED", 0)
    return _res("④ 雙世代裁決冊", "OK" if queued == 0 else "FAIL",
                f"QUEUED {queued}(須 0)· HOLD/BLOCKED {hold} 列管 · {p.name}")


def c1_evidence(via: Path = VIA) -> dict:
    p = _newest(via / "supportive modules" / "registry", "VIA_Evidence_Originals_v*.json")
    if p is None:
        return _res("⑤ 存證冊完整性", "SKIP", "冊缺")
    bad = []
    for e in _jload(p).get("entries", []):
        f = via / e["file"]
        if not f.exists():
            bad.append(f"存證件缺:{e['file']}")
            continue
        act = e.get("active", "")
        if act and not act.startswith("("):
            if not list(via.rglob(act)) and not (f.parent / act).exists():
                bad.append(f"現役件缺:{act}")
    return _res("⑤ 存證冊完整性", "OK" if not bad else "FAIL", "; ".join(bad) or "全在位")


def c1_syntax_gate(via: Path = VIA) -> dict:
    p = via / "supportive modules" / "registry" / "VIA_Syntax_Gate_Register_v0100.json"
    if not p.exists():
        return _res("⑥ 語法版本閘冊", "SKIP", "冊缺")
    bad = []
    for e in _jload(p).get("entries", []):
        if not (via / e["file"]).exists():
            bad.append(f"閘件缺:{e['file']}")
        try:
            tuple(int(x) for x in e["python_min"].split("."))
        except Exception:
            bad.append(f"python_min 壞:{e.get('python_min')}")
    return _res("⑥ 語法版本閘冊", "OK" if not bad else "FAIL", "; ".join(bad) or "有效")


def c1_r2_residue(via: Path = VIA) -> dict:
    residue = []
    for sub in ("VRN", "VDF", "VAP"):
        p = _newest(via / "functional modules" / sub, f"{sub}_Param_Registry_v*.json")
        if p is None:
            continue
        for name, e in _jload(p).get("canonical", {}).items():
            r = str(e.get("ruling", ""))
            if not r.startswith("<") and ("OneDrive" in r or "C:\\\\" in r or "Downloads" in r):
                residue.append(f"{sub}.{name}")
    return _res("⑦ R2 寫死路徑殘留", "OK" if not residue else "FAIL", "; ".join(residue) or "0 殘留")


def c1_launcher_rule(via: Path = VIA) -> dict:
    bad = []
    for cmd in sorted((via / "bin").glob("*.cmd")):
        for line in cmd.read_text(encoding="utf-8", errors="replace").splitlines():
            low = line.strip().lower()
            if low.startswith("rem") or "dir /b" in low or "%%f" in line:
                continue
            if CMD_HARD_RX.search(low):
                bad.append(f"{cmd.name}")
                break
    return _res("⑧ 啟動器鐵律殘留", "OK" if not bad else "FAIL", "; ".join(bad) or "0 寫死")


# ── C2 壞環境黑名單守衛 ──────────────────────────────────────────
def _blacklist(via: Path = VIA) -> dict | None:
    p = _newest(via / "supportive modules" / "registry", "VIA_BadEnv_Blacklist_v*.json")
    return _jload(p) if p else None


def c2_root_check(via: Path = VIA) -> dict:
    bl = _blacklist(via)
    if bl is None:
        return _res("⑨ 現行根黑名單比對", "SKIP", "黑名單冊缺")
    cur = str(via).replace("/", "\\").lower()
    hits = [r["path"] for r in bl["blacklisted_roots"] if cur.startswith(r["path"].lower())]
    note = f"現行根 {via} · 黑名單 {len(bl['blacklisted_roots'])} 根 · 命中 {len(hits)}"
    if not hits:
        return _res("⑨ 現行根黑名單比對", "OK", note)
    # 命中只有兩種可能,兩種都不是「哨兵自己改冊」:要嘛搬根,要嘛冊過期(批349 已立先例
    # ——現行正主根被誤列,走 reinstated_roots 留痕除名,零刪除)。裁定權在操作員。
    return _res("⑨ 現行根黑名單比對", "FAIL", note,
                ["# 命中的是**現在正在跑的根**,兩條路(裁定權在操作員,哨兵不自己改冊):",
                 f"#  (甲) 這確實是舊根 → 換到現行正主根再跑;冊:{hits[0]}",
                 "#  (乙) 冊過期了(此根已扶正)→ 依批349 先例移入 reinstated_roots 並補 why,"
                 "零刪除留痕",
                 "# 驗:via-conflict   ← ⑨ 要轉 OK"])


def c2_placeholder(via: Path = VIA) -> dict:
    zero = []
    for d, pat in ((via / "bin", "*.cmd"), (via / "bin", "*.py"),
                   (via / "supportive modules" / "registry", "*.py")):
        if not d.exists():
            continue
        for p in d.glob(pat):
            if p.stat().st_size == 0:
                zero.append(p.name)
    return _res("⑩ 活區 0-byte 占位檔", "OK" if not zero else "FAIL",
                "; ".join(zero) or "0 件(HZ-01)")


def c2_syspath(via: Path = VIA) -> dict:
    bad = [p for p in sys.path if "accelerator" in p.replace("\\", "/").split("/")[-1:]]
    bad += [p for p in sys.path
            if p.replace("\\", "/").rstrip("/").endswith("supportive modules/accelerator")]
    return _res("⑪ sys.path 無 accelerator/", "OK" if not bad else "FAIL",
                "; ".join(bad) or "FM-08 防線在位")


def _ps_strip_line(prefix: str) -> str:
    """剝離句:只動**本視窗**的 PATH。要永久生效是操作員自己的手(不代設律)。"""
    return ("$env:PATH = (($env:PATH -split ';') | "
            f"Where-Object {{ $_ -and $_ -notlike '{prefix}*' }}) -join ';'")


def _ps_relocate_lines(entry: str, tool: str, exe: str, home: str) -> list[str]:
    """搬家句:先把工具搬出黑根,再換錨,最後才剝離舊錨——次序反了會有一瞬間找不到工具。
    驗收句認的是**可執行檔**(exe_anchors),不是工具的俗名:`Get-Command poppler` 永遠找不到
    東西,poppler 這個名字沒有對應的 exe。"""
    dest = f"{home}\\{tool}"
    return [f"New-Item -ItemType Directory -Force -Path '{dest}' | Out-Null",
            f"Copy-Item -Recurse -Force '{entry}\\*' '{dest}\\'",
            f"$env:PATH = '{dest}' + ';' + $env:PATH",
            f"{_ps_strip_line(entry)}",
            f"# 驗:Get-Command {exe} | Select-Object -Expand Source   ← 要指到 {dest}"]


# 舊 VIA 克隆的指紋。命中這個的一律**剝離**,絕不搬家——
# 把舊克隆的 bin 複製到新家再掛上 PATH,等於親手讓封存根復活(零 Hydra)。
_CLONE_RX = re.compile(r"veritasintelligenceanalytics|movies-dataset", re.I)


def _tool_suspicion(entry: str, bl: dict) -> dict | None:
    """這一條命中像不像「工具寄生在黑根」。回 None = 沒有工具跡象(可直接剝離)。
    容器 stat 不到工作站的碟,所以這是**嫌疑**不是斷言——只憑路徑字面判,
    而且把判準寫出來給操作員自己覆核(假設目錄裡有什麼等於沒讀過那個目錄)。"""
    low = entry.lower().replace("/", "\\")
    if _CLONE_RX.search(low):
        return None                      # 舊 VIA 克隆:這正是黑名單要殺的東西,剝離
    for a in bl.get("path_tool_anchors", []):
        if any(d.lower() in low for d in a.get("dir_anchors", [])):
            return dict(a, _known=True)
    if low.rstrip("\\").endswith("\\bin") or low.rstrip("\\").endswith("\\scripts"):
        # 不明就是不明:不生成任何動作句。生成一條把不明目錄掛回 PATH 的指令,
        # 比不生成危險得多(MDL167 批613 同律:不明→不動,由操作員裁定)。
        return {"tool": "", "exe_anchors": [], "dir_anchors": [], "needed_by": [],
                "found_how": "路徑以 \\bin 或 \\Scripts 收尾", "_known": False}
    return None


def c2_path_env(via: Path = VIA, path_value: str | None = None) -> dict:
    """⑫ PATH 不得帶黑名單根前綴(HZ-02)。
    冊上 HZ-02 的 action 是「紅燈+PATH 換錨指令」——這裡把後半邊補上。"""
    bl = _blacklist(via)
    if bl is None:
        return _res("⑫ PATH 黑名單前綴", "SKIP", "黑名單冊缺")

    # (0) 具名豁免必須附理由,缺理由一律紅(L87:沒理由的豁免等於假綠)
    exempt, bad_ex = [], []
    for x in bl.get("path_exemptions", []):
        if not str(x.get("reason") or "").strip():
            bad_ex.append(str(x.get("prefix") or "(無前綴)"))
        else:
            exempt.append(x)
    if bad_ex:
        return _res("⑫ PATH 黑名單前綴", "FAIL",
                    f"豁免缺理由 {len(bad_ex)} 條:{'; '.join(bad_ex[:3])}(L87 豁免必附理由)",
                    ["# 修:到 VIA_BadEnv_Blacklist 最新版,替下列 path_exemptions 補 reason 後再跑",
                     *[f"#   {b}" for b in bad_ex[:5]]])

    raw = os.environ.get("PATH") if path_value is None else path_value
    entries = [e for e in (raw or "").split(";" if path_value is not None else os.pathsep) if e]
    if not any("\\" in e for e in entries):
        return _res("⑫ PATH 黑名單前綴", "SKIP", "非 Windows PATH(容器誠實;工作站波實測)")

    hits, skipped, n_unknown = [], [], 0
    for e in entries:
        for r in bl["blacklisted_roots"]:
            if e.lower().startswith(r["path"].lower()):
                ex = next((x for x in exempt if e.lower().startswith(x["prefix"].lower())), None)
                (skipped if ex else hits).append((e, r["reason"], ex))
                break
    if not hits:
        note = f"0 命中(PATH {len(entries)} 條"
        note += f";具名豁免放行 {len(skipped)} 條)" if skipped else ")"
        return _res("⑫ PATH 黑名單前綴", "OK", note)

    homes = [h["path"] for h in bl.get("relocation_home_candidates", [])] or ["C:\\VIA_Tools"]
    fix = ["# ── HZ-02 換錨句(只動本視窗;要永久生效請自己走「系統內容→環境變數」)──",
           "# 本段由哨兵印出、由操作員親手貼:哨兵不代設任何環境變數。"]
    n_move = 0
    for e, reason, _ in hits:
        a = _tool_suspicion(e, bl)
        fix.append(f"#  命中 {e}")
        fix.append(f"#    └ 黑名單冊理由:{reason}")
        if a and a["_known"]:
            n_move += 1
            need = "、".join(a.get("needed_by", [])) or "(冊上未點名)"
            exe = (a.get("exe_anchors") or [a["tool"]])[0]
            fix.append(f"#    └ 帶工具嫌疑:{a['tool']}(判準:{a.get('found_how', '')});"
                       f"VIA 點名處:{need}")
            fix.append("#    └ 盲剝會斷鏈 → 走搬家,不走剝離")
            fix += [f"    {ln}" for ln in _ps_relocate_lines(e, a["tool"], exe, homes[0])]
        elif a:
            n_unknown += 1
            fix.append(f"#    └ 疑似工具目錄但**冊上認不出是什麼**({a.get('found_how', '')});"
                       "容器讀不到工作站的碟,所以這裡不生成任何動作句——")
            fix.append("#      不明就掛回 PATH 比不動危險。先看一眼,再由你裁定剝離或搬家:")
            fix.append(f"    Get-ChildItem '{e}' -File -Name | Select-Object -First 20")
            fix.append("#    └ 看完若是 VIA 用得到的工具 → 把它補進黑名單冊的 path_tool_anchors "
                       "(附 needed_by 證據)再跑一次;若不是 → 貼下面這行剝離:")
            fix.append(f"    # {_ps_strip_line(e)}")
        else:
            why = ("舊 VIA 克隆的 bin——黑名單要殺的正是它,搬家等於讓封存根復活"
                   if _CLONE_RX.search(e) else "未見工具跡象")
            fix.append(f"#    └ {why} → 剝離")
            fix.append(f"    {_ps_strip_line(e)}")
    tail = f"# 驗:via-conflict   ← ⑫ 要從 FAIL 轉 OK({len(hits)} 條命中歸零"
    fix.append(tail + (f";其中 {n_unknown} 條要你先裁定)" if n_unknown else ")"))
    n_strip = len(hits) - n_move - n_unknown
    note = (f"{len(hits)} 條命中(搬家 {n_move} · 剝離 {n_strip} · 待裁定 {n_unknown})"
            f"{f';具名豁免放行 {len(skipped)}' if skipped else ''} · 修法句見下方修法區")
    return _res("⑫ PATH 黑名單前綴", "FAIL", note, fix)


def c2_verb_targets(via: Path = VIA) -> dict:
    bl = _blacklist(via)
    if bl is None:
        return _res("⑬ bin 動詞執行標的", "SKIP", "黑名單冊缺")
    bad_files = {b["file"].replace("\\", "/") for b in bl["blacklisted_files"]}
    hits = []
    for cmd in sorted((via / "bin").glob("*.cmd")):
        t = cmd.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
        for bf in bad_files:
            if bf.split("/")[-1] in t:
                hits.append(f"{cmd.name}→{bf.split('/')[-1]}")
    return _res("⑬ bin 動詞執行標的", "OK" if not hits else "FAIL", "; ".join(hits) or "零黑件引用")


CHECKS = [c1_central_params, c1_canonical_residue, c1_etf_conflicts, c1_twoera,
          c1_evidence, c1_syntax_gate, c1_r2_residue, c1_launcher_rule,
          c2_root_check, c2_placeholder, c2_syspath, c2_path_env, c2_verb_targets]


def run() -> int:
    print("=== 衝突機制總哨兵+壞環境守衛(TOOL-107 批106)· 十三道 ===")
    results = []
    for fn in CHECKS:
        try:
            r = fn()
        except Exception as exc:
            r = _res(fn.__name__, "FAIL", f"{type(exc).__name__}: {str(exc)[:80]}")
        results.append(r)
        print(f"  [{r['state']:>4}] {r['name']} · {r['note'][:96]}")
    n_fail = sum(1 for r in results if r["state"] == "FAIL")
    n_warn = sum(1 for r in results if r["state"] == "WARN")
    n_skip = sum(1 for r in results if r["state"] == "SKIP")
    n_ok = len(results) - n_fail - n_warn - n_skip
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"CONFLICT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"schema": "via.conflict_guard.v1",
                               "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                               "results": results,
                               "counts": {"ok": n_ok, "warn": n_warn,
                                          "fail": n_fail, "skip": n_skip}},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] OK {n_ok} · WARN {n_warn}(具名列管)· FAIL {n_fail} · SKIP {n_skip} · 存證 {out.name}")
    fixes = [(r["name"], r["fix"]) for r in results if r.get("fix")]
    if fixes:
        print("\n  ── 修法區(一貼即用;由操作員親手貼,哨兵不代設)──")
        for nm, lines in fixes:
            print(f"  [{nm}]")
            for ln in lines:
                print(f"  {ln}")
    return 1 if n_fail else 0


# ── 十檢自測(沙盒零網路)────────────────────────────────────────
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        reg = sand / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (sand / "bin").mkdir()
        # 沙盒黑名單冊
        (reg / "VIA_BadEnv_Blacklist_v0100.json").write_text(json.dumps({
            "blacklisted_roots": [{"path": "C:\\\\old\\\\root", "reason": "t"}],
            "forbidden_exec_fragments": [], "env_hazards": [],
            "blacklisted_files": [{"file": "x/bad_evil.py", "reason": "t"}]}), encoding="utf-8")
        # ① 現行根未命中黑名單
        chk("① 根比對(未命中=OK)", c2_root_check(sand)["state"] == "OK")
        # ② 0-byte 占位偵測
        (sand / "bin" / "ok.cmd").write_text("@echo off\n", encoding="utf-8")
        chk("② 零占位=OK", c2_placeholder(sand)["state"] == "OK")
        (sand / "bin" / "ghost.cmd").write_text("", encoding="utf-8")
        chk("③ 占位檔=FAIL", c2_placeholder(sand)["state"] == "FAIL")
        # ④ 黑件引用偵測
        (sand / "bin" / "bad.cmd").write_text("py bad_evil.py\n", encoding="utf-8")
        chk("④ 黑件引用=FAIL", c2_verb_targets(sand)["state"] == "FAIL")
        # ⑤ 啟動器鐵律:寫死=FAIL、dir /b=OK
        (sand / "bin" / "hard.cmd").write_text('py "tool_v0100.py"\n', encoding="utf-8")
        chk("⑤ 寫死版號=FAIL", c1_launcher_rule(sand)["state"] == "FAIL")
        for f in ("bad.cmd", "hard.cmd", "ghost.cmd"):
            (sand / "bin" / f).write_text("rem clean\n", encoding="utf-8")
        chk("⑥ 清乾淨=OK", c1_launcher_rule(sand)["state"] == "OK"
            and c2_verb_targets(sand)["state"] == "OK")
        # ⑦ canonical 未裁殘量沙盒
        vdf = sand / "functional modules" / "VDF"
        vdf.mkdir(parents=True)
        (vdf / "VDF_Param_Registry_v0100.json").write_text(json.dumps({
            "params": [{"name": "A", "value": "1"}, {"name": "A", "value": "2"}],
            "canonical": {}}), encoding="utf-8")
        chk("⑦ 未裁殘量=FAIL", c1_canonical_residue(sand)["state"] == "FAIL")
        (vdf / "VDF_Param_Registry_v0101.json").write_text(json.dumps({
            "params": [{"name": "A", "value": "1"}, {"name": "A", "value": "2"}],
            "canonical": {"A": {"ruling": "2"}}}), encoding="utf-8")
        chk("⑧ 裁畢(glob 新版)=OK", c1_canonical_residue(sand)["state"] == "OK")
        # ⑨ R2 殘留沙盒
        (vdf / "VDF_Param_Registry_v0102.json").write_text(json.dumps({
            "params": [], "canonical": {"P": {"ruling": "'C:\\\\\\\\Users\\\\\\\\x\\\\\\\\OneDrive\\\\\\\\y'"}}}), encoding="utf-8")
        chk("⑨ R2 殘留=FAIL", c1_r2_residue(sand)["state"] == "FAIL")
        # ⑪ 具名豁免缺理由 = 紅(L87:沒理由的豁免等於假綠)
        (reg / "VIA_BadEnv_Blacklist_v0101.json").write_text(json.dumps({
            "blacklisted_roots": [{"path": "C:\\\\old\\\\root", "reason": "t"}],
            "forbidden_exec_fragments": [], "env_hazards": [], "blacklisted_files": [],
            "path_exemptions": [{"prefix": "C:\\\\old\\\\root\\\\keep"}]}), encoding="utf-8")
        r11 = c2_path_env(sand, path_value="C:\\\\ok\\\\bin")
        chk("⑪ 豁免缺理由=FAIL", r11["state"] == "FAIL" and "L87" in r11["note"], r11["note"][:40])
        # ⑫ 純殘留命中 → 剝離句(-notlike)
        (reg / "VIA_BadEnv_Blacklist_v0102.json").write_text(json.dumps({
            "blacklisted_roots": [{"path": "C:\\\\old\\\\root", "reason": "舊根封存"}],
            "forbidden_exec_fragments": [], "env_hazards": [], "blacklisted_files": [],
            "path_exemptions": [],
            "path_tool_anchors": [{"tool": "poppler", "dir_anchors": ["poppler"],
                                   "exe_anchors": ["pdftoppm"], "needed_by": ["VRN"],
                                   "found_how": "測"}],
            "relocation_home_candidates": [{"path": "C:\\\\VIA_Tools", "why": "測"}]}),
            encoding="utf-8")
        r12 = c2_path_env(sand, path_value="C:\\\\old\\\\root\\\\junk;C:\\\\ok")
        f12 = "\n".join(r12.get("fix", []))
        chk("⑫ 純殘留=剝離句", r12["state"] == "FAIL" and "-notlike" in f12
            and "Copy-Item" not in f12, r12["note"][:40])
        # ⑬ 帶工具嫌疑 → 搬家句,而且**不准**出現盲剝(盲剝會打斷 VRN 的 poppler)
        r13 = c2_path_env(sand, path_value="C:\\\\old\\\\root\\\\poppler\\\\Library\\\\bin")
        f13 = "\n".join(r13.get("fix", []))
        chk("⑬ 帶工具=搬家句", r13["state"] == "FAIL" and "Copy-Item" in f13
            and "VIA_Tools\\poppler" in f13 and "搬家" in f13
            and "Get-Command pdftoppm" in f13, r13["note"][:40])
        # ⑭ 舊 VIA 克隆的 bin 絕不准生成搬家句——搬家等於親手讓封存根復活(零 Hydra)。
        # 這一檢是批618 自己踩出來的:\bin 收尾的啟發式把舊克隆判成「帶工具」,
        # 生成的句子會把死根的 bin 複製到新家再掛上 PATH。走過 Windows 那一半才看得到。
        r14 = c2_path_env(sand, path_value="C:\\\\old\\\\root\\\\movies-dataset\\\\VeritasIntelligenceAnalytics\\\\bin")
        f14 = "\n".join(r14.get("fix", []))
        chk("⑭ 舊克隆=剝離不搬家", r14["state"] == "FAIL" and "Copy-Item" not in f14
            and "-notlike" in f14 and "復活" in f14, r14["note"][:40])
    # ⑩ 實樹煙測:照的是**工具本身**,不是樹乾不乾淨。
    # v0100 這裡寫 rc==0,等於哨兵只要正確抓到一件真衝突就自判失職——
    # 工具盡責反被判紅,而且紅燈上寫的是錯的名字。樹乾不乾淨改由格上
    # 「衝突哨兵實樹巡檢」那一盞照(批618)。
    try:
        before = len(list(REPORTS.glob("CONFLICT_*.json"))) if REPORTS.exists() else 0
        rc = run()
        after = len(list(REPORTS.glob("CONFLICT_*.json")))
        chk("⑩ 實樹煙測(不拋例外+十三道齊發+報告落地)",
            rc in (0, 1) and after == before + 1 and len(CHECKS) == 13,
            f"rc={rc} 報告+{after - before} 道數={len(CHECKS)}")
    except Exception as exc:
        chk("⑩ 實樹煙測", False, str(exc)[:60])
    n = 14 - len(fails)
    print(f"  [計] 十四檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 衝突哨兵 · 十四檢自測(沙盒零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
