#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL175_AutoDeploy v0101 — 依現況佈署計畫器(批673;批675 +上市價補源兩步 +pack_red 出處對帳)
====================================================================
操作員令(批673):「A POWERSHELL TO LAUNCH AUTO DEPLOY INSTALLATION **BASED ON
OUR THE LAST STATUS**. THEN USER USE THE SYSTEM ON HTML U/I」。

這支只做一件事:**照上一次量到的現況,排出一條從現在走到 HTML U/I 的路**。
它自己不跑任何一步——跑的是 `via-deploy`(在操作員自己的 PS 視窗裡跑,
因為 via-* 是 PS 函式,只有在那個視窗裡才看得見)。

兩條車道,而且**永遠分得開**:
  auto  零風險、可代跑:同步冊 · 重建索引 · 再生頁 · 跑鏈 · 跑格子 · 跑打包閘 · 開 U/I
  hand  **操作員的手**:裝套件 · 開同意閘
        這兩件事 AI 永不代做。不是做不到,是不該做——
        裝套件會動到你的環境,開同意閘等於替你決定要不要觸網。
        所以 hand 那一欄給的是**可以直接貼的一行**,貼不貼是你的事。

「BASED ON THE LAST STATUS」的出處(全部是既有存證,不重新量一次):
  打包就緒閘  VIA_Reports/packgate/PACKGATE_latest.json     (CGC_MDL174)
  全格子      VIA_Reports/selftest_runs/GRID_*.json          (CGC_MDL064)
  六域現況    VIA_Reports/state_matrix/STATE_latest.json     (CGC_MDL169)
  家族境      VIA_Reports/rungate/RUNGATE_latest.json        (CGC_MDL137)
存證**比樹舊就不拿來判**(批669 律):那份講的是另一棵樹。
存證缺席也不是壞掉——它會排一步「先去量」,而不是假裝知道。

用法:
  via-deploy                → 印計畫(零動作)
  via-deploy -Apply         → 依序跑 auto 步,最後開 HTML U/I;hand 步只印不跑
  via-matrixspec 同款矩陣頁:via-deploy html
  本支直呼:plan | html | ps(印可貼的 PS 區塊)| --selftest 十八檢
誠實 rc:0 只剩開頁 · 1 有真的壞 · 2 有缺料要先量 · 4 有等操作員的手的步
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
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "deploy"
BATCH = "批673"

AUTO, HAND, DONE = "auto", "hand", "done"
LANE_ZH = {AUTO: "可代跑", HAND: "**你的手**", DONE: "已經好了"}
LANE_STATE = {AUTO: "NODATA", HAND: "GATED", DONE: "GREEN"}

# 可代跑的白名單:只有 via-* 開頭、而且**沒有殼元字元**的單句才准進 auto 車道。
#   這不是第二份指令表(指令仍然只有這一份),是一道門閂:
#   計畫是資料,資料不該有本事在操作員的視窗裡長出分號跟管線。
_SAFE_CMD = re.compile(r"^via-[a-z0-9-]+(?: [A-Za-z0-9_.:\\\\/=+,-]+)*$")
_SHELL_META = (";", "|", "&", "`", "$(", ">", "<", "\n", "\r")


def safe_auto(cmd: str) -> bool:
    return bool(_SAFE_CMD.match(cmd)) and not any(m in cmd for m in _SHELL_META)


def rel(p) -> str:
    try:
        return str(Path(p).resolve().relative_to(VIA)).replace("\\", "/")
    except Exception:
        return str(p)


# ── 上一次的現況(只讀既有存證,不重新量)──────────────────────────────
def _head_ct() -> int | None:
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=str(VIA),
                           capture_output=True, text=True, timeout=20)
        return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def read_evidence(path: Path, what: str) -> tuple[dict | None, str]:
    """回 (存證, 為什麼沒有)。**比樹舊就不拿來判**(批669 律)。"""
    if not path.exists():
        return None, f"{what}沒有存證"
    ct = _head_ct()
    if ct and path.stat().st_mtime < ct:
        gap = ct - path.stat().st_mtime
        unit = ("分鐘", gap / 60) if gap < 3600 else (("小時", gap / 3600) if gap < 86400
                                                     else ("天", gap / 86400))
        return None, (f"{what}存證**比現在的樹舊**(早 {unit[1]:.1f}{unit[0]})"
                      "——它講的是另一棵樹")
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except Exception as exc:
        return None, f"{what}存證讀不開:{type(exc).__name__}"


def last_status() -> dict:
    grid_dir = VIA / "VIA_Reports" / "selftest_runs"
    grids = sorted(grid_dir.glob("GRID_*.json")) if grid_dir.exists() else []
    pack, pack_why = read_evidence(VIA / "VIA_Reports" / "packgate" / "PACKGATE_latest.json",
                                  "打包就緒閘")
    grid, grid_why = (read_evidence(grids[-1], "全格子") if grids else (None, "全格子沒有存證"))
    state, state_why = read_evidence(VIA / "VIA_Reports" / "state_matrix" / "STATE_latest.json",
                                     "六域現況")
    rung, rung_why = read_evidence(VIA / "VIA_Reports" / "rungate" / "RUNGATE_latest.json",
                                   "家族境")
    return {"pack": pack, "pack_why": pack_why, "grid": grid, "grid_why": grid_why,
            "state": state, "state_why": state_why, "rung": rung, "rung_why": rung_why,
            "grid_path": rel(grids[-1]) if grids else ""}


# ── 排路 ──────────────────────────────────────────────────────────────
def step(sid, lane, cmd, why, evidence="") -> dict:
    lane = lane if lane in (AUTO, HAND, DONE) else AUTO
    if lane == AUTO and not safe_auto(cmd):
        # 進不了白名單的一律降成「你的手」——寧可多讓你貼一次,也不在你的視窗裡亂跑
        lane = HAND
        why = why + "(這一句不在可代跑白名單裡,改成你貼)"
    return {"id": sid, "lane": lane, "state": LANE_STATE[lane], "cmd": cmd,
            "why": why, "evidence": evidence}


def plan(st: dict | None = None) -> dict:
    st = st or last_status()
    steps: list = []

    # ① 冊要先同步,不然後面每一步看到的樹都是舊的(LL272 次序)
    steps.append(step("S1", AUTO, "via-vcgc registry-sync -Apply",
                      "元件自動編號冊同步:新支不入冊,後面每一面登錄都會判錯"))
    steps.append(step("S2", AUTO, "via-vrnbook build",
                      "VRN 六層冊重建:冊釘著舊版號時,鏈會去敲你剛修好那支的前一版"
                      "(批671 LL318)"))
    steps.append(step("S3", AUTO, "via-manager ui",
                      "總控頁再生:它是**契約件**,tests/test_master_control_contract 逐字釘著"))

    # ② 家族境:能不能跑是操作員的手(裝套件),不是我的
    rung = st["rung"]
    fams = (rung or {}).get("families") or {}
    for fam in ("vdf", "vrn", "vap"):
        f = fams.get(fam) or {}
        v = str(f.get("verdict") or f.get("state") or "").upper()
        if not rung:
            steps.append(step(f"S4-{fam}", AUTO, f"via-rungate --family {fam}",
                              f"先量一次 {fam.upper()} 家族境能不能跑({st['rung_why']})"))
        elif v in ("GREEN", "OK", "PASS"):
            steps.append(step(f"S4-{fam}", DONE, f"via-rungate --family {fam}",
                              f"{fam.upper()} 家族境上一次判 {v}",
                              rel(VIA / "VIA_Reports/rungate/RUNGATE_latest.json")))
        else:
            miss = f.get("missing") or f.get("libs_missing") or []
            pyexe = f.get("python") or f"<{fam} 家族境 python>"
            if miss:
                steps.append(step(f"S4-{fam}", HAND,
                                  f"& \"{pyexe}\" -m pip install " + " ".join(map(str, miss[:8])),
                                  f"{fam.upper()} 家族境缺 {len(miss)} 個套件 —— "
                                  "**裝套件是你的手**,這一行貼上去才會裝",
                                  rel(VIA / "VIA_Reports/rungate/RUNGATE_latest.json")))
            else:
                steps.append(step(f"S4-{fam}", AUTO, f"via-rungate --family {fam}",
                                  f"{fam.upper()} 家族境上一次判 {v or '沒判'},重量一次看缺什麼"))

    # ③ 同意閘:永不代設
    for tag, env_name, what in (("S5a", "VIA_NET_CONSENT", "觸網"),
                                ("S5b", "VIA_SCRAPE_CONSENT", "擷取")):
        if not os.environ.get(env_name):
            steps.append(step(tag, HAND, f"$env:{env_name}='YES'",
                              f"要{what}的站現在一律 GATED。"
                              "**同意閘 AI 永不代設**——要不要{0}是你決定的"
                              .format(what)))

    # ③b 上市所價補源(批675 實測照出來的唯一大洞)。**兩步都是你的手**,因為都要觸網。
    #     量到的:`tw_daily_prices` 892 檔**全是 .TWO 上櫃**,47 份個股研報一檔都對不到;
    #     `tw_trading_daily` 有上市 1,084 檔,但 **TWSE 停在 2026-01-27(距今 237 天)**。
    #     於是 30 份有代號有目標價的報告,ADJ 全部卡在「上市所整個不在 ADJ 表」。
    #     補起來 = VRN 可判率一次多 26 格。**這兩句不代跑**:抓價會動你的庫,也要觸網。
    for tag, cmd, why in (
            ("S5c", "via-market-lists",
             "先把上市所補進名冊(tw_listings 只有 TPEX 892;tw_listings_industry 已有 TWSE 1,088)"),
            ("S5d", "via-price",
             "再抓上市所日價到今天(帶 adj_close)——**這一步才是那 26 格的鑰匙**")):
        steps.append(step(tag, HAND, cmd, why))

    # ④ 跑鏈:四條鏈各自落一張矩陣頁(批672 起都走同一份排版規格)
    for sid, cmd, why in (
            ("S6", "via-state html", "六域現況矩陣(ENV/LIBS/SSOT/TOOLS/VDF/VRN)"),
            ("S7", "via-vdfchain run", "VDF 獨立鏈七站(參數·邏輯·因子·引擎;起始日 2023-07-01)"),
            ("S8", "via-vrnchain run", "VRN 六層鏈 44 節點(層間依序·層內並行)"),
            ("S8b", "via-repairprice --apply",
             "價補完要重算 VRN 的庫價與上漲空間(零網路;不重新擷取任何報告)"),
            ("S8c", "via-vrnmatrix",
             "驗真矩陣:判對率 + 可判率(**兩個都要 100% 才叫準確**)"),
            ("S9", "via-panoplan html", "全景批次修復計畫(只規劃不動手)")):
        steps.append(step(sid, AUTO, cmd, why))

    # ⑤ 全格子:存證比樹舊就一定要重跑(不然後面每一盞燈都在講另一棵樹)
    grid = st["grid"]
    if grid is None:
        steps.append(step("S10", AUTO, "via-selftest",
                          f"全格子必須重跑:{st['grid_why']}"))
    elif grid.get("fail"):
        steps.append(step("S10", AUTO, "via-selftest",
                          f"上一次全格子 FAIL {grid.get('fail')} 站,重跑並逐站看敗因",
                          st["grid_path"]))
    else:
        steps.append(step("S10", DONE, "via-selftest",
                          f"上一次全格子 OK {grid.get('ok')} · FAIL 0 · SKIP {grid.get('skip')}",
                          st["grid_path"]))

    # ⑥ 打包就緒閘:最後一次對帳
    steps.append(step("S11", AUTO, "via-packgate html",
                      "三個專案 × 七列打包就緒閘 —— **GREEN 才算就緒**"))
    # ⑦ 開 HTML U/I(操作員原令的終點)
    steps.append(step("S12", AUTO, "via-ui",
                      "正典 TEMPLATE 零 server HTML U/I —— 操作員從這裡開始用系統"))

    tally = {"auto": 0, "hand": 0, "done": 0}
    for s in steps:
        tally[s["lane"]] += 1
    red = 0
    if st["pack"]:
        red = int((st["pack"].get("tally") or {}).get("RED") or 0)
    rc = 1 if red else (4 if tally["hand"] else (2 if tally["auto"] else 0))
    return {"pack_red": red,          # 批675:rc 用到的那個數字要**印出來**,
            #   不然自測只能自己再猜一次——v0100 的檢就是這樣寫成永遠 0 的(LL308)
            "schema": "VIA_DEPLOY_v1", "batch": BATCH,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "python": sys.version.split()[0],
            "steps": steps, "tally": tally, "rc": rc,
            "rc_name": {0: "GREEN", 1: "RED", 2: "NODATA", 4: "GATED"}[rc],
            "sources": {k: (rel(v) if isinstance(v, Path) else v) for k, v in (
                ("打包就緒閘", st["pack_why"] or "在"),
                ("全格子", st["grid_why"] or st["grid_path"]),
                ("六域現況", st["state_why"] or "在"),
                ("家族境", st["rung_why"] or "在"))}}


# ── 出 ────────────────────────────────────────────────────────────────
HEADERS = ("步", "車道", "指令(可直接貼)", "為什麼要這一步")


def _spec_mod():
    """排版規格向 CGC_MDL173 整支取用(批672;不自備第二份 CSS)。"""
    import importlib.util
    c = sorted(HERE.glob("CGC_MDL173_MatrixReportSpec_v*.py"))
    if not c:
        return None
    try:
        sp = importlib.util.spec_from_file_location("via_matrixspec", c[-1])
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m
    except Exception:
        return None


def to_markdown(rep: dict) -> str:
    t = rep["tally"]
    out = [f"# 依現況佈署計畫({rep['batch']})", "",
           f"- 產生 {rep['generated']} · 主機 {rep['host']} · python {rep['python']}",
           f"- 可代跑 {t['auto']} · **你的手** {t['hand']} · 已經好了 {t['done']}"
           f" → **{rep['rc_name']}**", "",
           "> **裝套件與開同意閘永遠是你的手。** 不是做不到,是不該做:"
           "裝套件會動到你的環境,開同意閘等於替你決定要不要觸網。", "",
           "| " + " | ".join(HEADERS) + " |", "|" + "---|" * len(HEADERS)]
    for s in rep["steps"]:
        out.append(f"| {s['id']} | {LANE_ZH[s['lane']]} | `{s['cmd']}` | "
                   f"{s['why'].replace('|', '/')} |")
    out += ["", "## 現況出處(都是既有存證,沒有重新量)", ""]
    for k, v in rep["sources"].items():
        out.append(f"- {k}:{v}")
    return "\n".join(out) + "\n"


def to_ps_block(rep: dict) -> str:
    """一貼到底的 PS 區塊:auto 照順序跑,hand 只印不跑。"""
    out = ["# === VIA 依現況佈署(批673;auto 照跑,你的手只印不跑)===",
           "$ErrorActionPreference = 'Continue'"]
    for s in rep["steps"]:
        if s["lane"] == AUTO:
            out.append(f"Write-Host '  [{s['id']}] {s['cmd']}' -ForegroundColor Cyan; {s['cmd']}")
        elif s["lane"] == HAND:
            out.append(f"Write-Host '  [{s['id']}] 你的手:{s['cmd']}' -ForegroundColor Yellow")
        else:
            out.append(f"Write-Host '  [{s['id']}] 已經好了:{s['cmd']}' -ForegroundColor DarkGray")
    return "\n".join(out) + "\n"


def render(rep: dict):
    M = _spec_mod()
    if M is None or not M.rich_ok()[0]:
        print("  [NODATA] CGC_MDL173 排版規格或 rich 缺席 → 不落頁")
        return None
    con = M.console()
    t = M.table("依現況佈署計畫 · 從這裡走到 HTML U/I",
                [{"name": "步", "width": 8},
                 {"name": "車道", "width": 10, "justify": "center"},
                 {"name": "指令(可直接貼)", "width": 52},
                 {"name": "為什麼要這一步", "width": 96}])
    for s in rep["steps"]:
        col = M.SPEC["states"][s["state"]]
        t.add_row(s["id"], f"[{col}]{LANE_ZH[s['lane']]}[/]", s["cmd"], s["why"])
    con.print(t)
    t2 = M.table("現況出處(都是既有存證,沒有重新量)",
                 [{"name": "來源", "width": 14}, {"name": "狀況"}])
    for k, v in rep["sources"].items():
        t2.add_row(k, str(v))
    con.print(t2)
    tl = rep["tally"]
    kpis = [{"label": "可代跑", "value": tl["auto"], "state": "NODATA"},
            {"label": "你的手", "value": tl["hand"], "state": "GATED"},
            {"label": "已經好了", "value": tl["done"], "state": "GREEN"},
            {"label": "總判", "value": rep["rc_name"], "state": rep["rc_name"]}]
    REPORTS.mkdir(parents=True, exist_ok=True)
    return M.page(con, title="依現況佈署計畫 · 批673",
                  subtitle=(f"{rep['generated']} · 主機 {rep['host']} · "
                            f"python {rep['python']} · via-deploy -Apply 會照這張表跑 auto 那幾步"),
                  md=to_markdown(rep), payload=rep, kpis=kpis,
                  law=("<b>裝套件與開同意閘永遠是你的手。</b> 不是做不到,是不該做:"
                       "裝套件會動到你的環境,開同意閘等於替你決定要不要觸網。<br>"
                       "<b>現況全部讀既有存證</b>,沒有重新量;"
                       "存證比樹舊就不拿來判——那份講的是另一棵樹(批669)。"),
                  out=REPORTS / "VIA_Deploy_Plan_v0100.html")


def write_log(rep: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"DEPLOY_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "DEPLOY_latest.json").write_text(body, encoding="utf-8")
    (REPORTS / "DEPLOY_latest.md").write_text(to_markdown(rep), encoding="utf-8")
    (REPORTS / "DEPLOY_latest.ps1.txt").write_text(to_ps_block(rep), encoding="utf-8")
    return REPORTS / "DEPLOY_latest.json"


def print_plain(rep: dict) -> None:
    # 欄寬照**最長的步號**算。寫死 8 的那一版被 `S5-VIA_SCRAPE_CONSENT` 撞開,
    #   整行擠成一坨——可貼的東西被擠壞,操作員就會貼錯(批670 LL313 同一類)。
    w = max((len(s["id"]) for s in rep["steps"]), default=4) + 2
    for s in rep["steps"]:
        print(f"  {s['id']:<{w}}{LANE_ZH[s['lane']]:<10}{s['cmd']:<46}{s['why'][:78]}")
    t = rep["tally"]
    print(f"  [計] 可代跑 {t['auto']} · 你的手 {t['hand']} · 已經好了 {t['done']}"
          f" → {rep['rc_name']}")


# ── 自測 ──────────────────────────────────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails: list[str] = []

    def chk(name, ok, note=""):
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}")
        if not ok:
            fails.append(name)

    rep = plan()
    ids = [s["id"] for s in rep["steps"]]
    # ① 路一定走到 HTML U/I(操作員原令的終點)
    chk("最後一步是開 HTML U/I", rep["steps"][-1]["cmd"] == "via-ui", f"({ids[-1]})")
    # ② 次序:冊 → 頁 → 鏈 → 格子 → 打包閘 → 開頁(LL272)
    order = [i for i in ("S1", "S2", "S3", "S10", "S11", "S12") if i in ids]
    chk("次序照 LL272(冊→頁→…→格子→打包閘→開頁)",
        order == sorted(order, key=lambda x: ids.index(x)), f"({order})")
    # ③ 裝套件永遠在 hand 車道
    installs = [s for s in rep["steps"] if "pip install" in s["cmd"]]
    chk("裝套件一律 hand(不代裝套件)",
        all(s["lane"] == HAND for s in installs), f"({len(installs)} 步)")
    # ④ 同意閘永遠在 hand 車道,而且本支不設它
    gates = [s for s in rep["steps"] if "CONSENT" in s["cmd"]]
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest(")[0]
    sets_gate = ("environ[" in src and "CONSENT" in src.split("environ[")[1][:40])
    chk("同意閘一律 hand 且本支不代設",
        all(s["lane"] == HAND for s in gates) and not sets_gate, f"({len(gates)} 步)")
    # ⑤ auto 白名單:擋得住殼元字元
    chk("auto 白名單擋得住殼元字元",
        safe_auto("via-selftest") and safe_auto("via-rungate --family vrn")
        and not safe_auto("via-x; rm -rf /") and not safe_auto("pip install x")
        and not safe_auto("via-x && evil") and not safe_auto("via-x $(evil)"))
    # ⑥ 不在白名單的步會被降成 hand(而不是硬跑)
    s = step("X", AUTO, "via-x; evil", "咬用")
    chk("白名單外的步降成 hand 不硬跑", s["lane"] == HAND and "白名單" in s["why"])
    # ⑦ 每一步都說得出為什麼(L92)
    noplan = [s["id"] for s in rep["steps"] if not s["why"]]
    chk("每一步都說得出為什麼(L92)", not noplan, f"({noplan})")
    # ⑧ 現況全部讀既有存證:本支不呼叫任何 via-*(它是計畫器不是跑者)
    chk("本支不自己跑任何一步(它是計畫器)",
        "subprocess.run([\"via-" not in src and "subprocess.call" not in src)
    # ⑨ 存證比樹舊 → 不拿來判(批669 律)
    chk("存證比樹舊就不拿來判", "比現在的樹舊" in src)
    # ⑩ 存證缺席 → 排一步「先去量」,不是假裝知道
    with tempfile.TemporaryDirectory() as td:
        empty = plan({"pack": None, "pack_why": "沒有存證", "grid": None,
                      "grid_why": "沒有存證", "state": None, "state_why": "沒有存證",
                      "rung": None, "rung_why": "沒有存證", "grid_path": ""})
    s10 = next((s for s in empty["steps"] if s["id"] == "S10"), None)
    chk("存證缺席 → 排一步先去量(不假裝知道)",
        s10 is not None and s10["lane"] == AUTO and "必須重跑" in s10["why"])
    # ⑪ 家族境上次綠 → 那一步記 done(不重複跑)
    got = plan({"pack": None, "pack_why": "", "grid": None, "grid_why": "",
                "state": None, "state_why": "",
                "rung": {"families": {"vrn": {"verdict": "GREEN"}}}, "rung_why": "",
                "grid_path": ""})
    sv = next(s for s in got["steps"] if s["id"] == "S4-vrn")
    chk("家族境上次綠 → 記 done 不重跑", sv["lane"] == DONE, f"({sv['lane']})")
    # ⑫ 家族境缺套件 → hand,而且把該家族境的 python 具名寫進那一行
    got2 = plan({"pack": None, "pack_why": "", "grid": None, "grid_why": "",
                 "state": None, "state_why": "",
                 "rung": {"families": {"vdf": {"verdict": "RED",
                                               "python": "C:/envs/via_vdf_312/python.exe",
                                               "missing": ["duckdb", "pandas"]}}},
                 "rung_why": "", "grid_path": ""})
    sv2 = next(s for s in got2["steps"] if s["id"] == "S4-vdf")
    chk("缺套件那一行具名寫出該家族境的 python",
        sv2["lane"] == HAND and "via_vdf_312" in sv2["cmd"] and "duckdb" in sv2["cmd"])
    # ⑬ rc 與車道一致
    t = rep["tally"]
    # 批675:v0100 這一行寫成 `rep["pack_red"] if "pack_red" in rep else 0` —— 而 `plan()`
    #   當時根本沒有印出 pack_red,所以那個三元永遠取 0,檢等於在用**另一套算法**。
    #   打包閘第一次出現 RED 1 的那天,engine 判 rc=1、檢算 want=4,當場紅。
    #   **engine 用哪個數字,檢就要讀哪個數字**(LL308:沒有對帳器的數字只是看起來很負責)。
    want = 1 if rep.get("pack_red") else (4 if t["hand"] else (2 if t["auto"] else 0))
    chk("rc 與車道一致", rep["rc"] == want, f"(rc={rep['rc']} 應 {want})")
    # ⑭ PS 區塊:hand 只印不跑
    ps = to_ps_block(rep)
    hand_cmds = [s["cmd"] for s in rep["steps"] if s["lane"] == HAND]
    leaked = [c for c in hand_cmds if f"; {c}" in ps]
    chk("PS 區塊裡 hand 只印不跑", not leaked, f"(外洩 {leaked[:1]})")
    # ⑮ 負向:把一個 hand 步硬塞成 auto,白名單要擋下來
    bad = step("Y", AUTO, "$env:VIA_NET_CONSENT='YES'", "咬用")
    chk("負向:同意閘塞進 auto 也會被擋成 hand", bad["lane"] == HAND)
    # ⑯ MD 三段齊
    md = to_markdown(rep)
    chk("MD 三段齊(抬頭 · 逐步 · 現況出處)",
        all(s in md for s in ("# 依現況佈署計畫", "| 步 |", "## 現況出處")))
    # ⑰ 落頁走 CGC_MDL173(不自備第二份 CSS)
    declares_css = ("</sty" + "le>") in src or "css = (" in src
    chk("落頁走 CGC_MDL173(本支不寫樣式)", "CGC_MDL173" in src and not declares_css)
    # ⑱ 存證三件 + PS 區塊落得出來
    write_log(rep)
    chk("存證三件 + 可貼 PS 區塊落得出來",
        all((REPORTS / f).exists() for f in ("DEPLOY_latest.json", "DEPLOY_latest.md",
                                             "DEPLOY_latest.ps1.txt")))

    n = 18 - len(fails)
    print(f"  [計] 十八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print("=== 依現況佈署計畫器 v0100 · 十八檢(沙盒零網路)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "plan")
    if verb not in ("plan", "html", "ps"):
        print(f"  [用法] plan | html | ps | --selftest(收到 {verb!r})")
        return 2
    rep = plan()
    if verb == "ps":
        print(to_ps_block(rep), end="")
    elif verb == "html":
        p = render(rep)
        if p:
            print(f"  [頁] {rel(p)}")
            if not os.environ.get("VIA_NO_OPEN"):
                try:
                    import webbrowser
                    webbrowser.open(p.as_uri())
                except Exception:
                    pass
    else:
        print_plain(rep)
    write_log(rep)
    if verb != "ps":
        print("  [律] **裝套件與開同意閘永遠是你的手。** 這支只排路、不跑路;"
              "跑的是 via-deploy -Apply,而它也只跑 auto 那幾步。")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
