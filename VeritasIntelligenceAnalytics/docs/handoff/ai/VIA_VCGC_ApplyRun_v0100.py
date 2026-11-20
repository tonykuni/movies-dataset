#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0100 — VCGC 的一鍵套用啟動器(Python 版;PS 只負責進環境、呼叫本檔、開頁)

操作員 2026-11-20 15:36「PS 僅負責簡單短啟動」「啟動檔案是用 PY 寫的嗎 · 裡面有加速器嗎」· 16:00「繼續全面性修正」。
原本 Invoke-VIA-ApplyAll v0106 ~ v0109 把同步檢查、各道步驟、判燈、OmniRoute 安裝都寫在 PS 裡(833 行),違反 L117。
本檔把那些邏輯搬進 Python(帶加速器橋),只串各系統既有的動詞,不另做檢查器:

  sync   本機對 GitHub main:fetch → 分支 · 多 / 少幾個提交 · 改過未提交 · 未追蹤;在 main 而且已追蹤的檔乾淨才快轉(--ff-only)
  S 同步台   VCGC synchronizer · VDF synchronizer · VRN synchronizer(VDF / VRN 從自己的入口跑,不帶 VCGC 旗標)
  C 工具與資料庫   VCGC env-tools 稽核 ·(VIA_APPLY_COVERAGE=1)工具覆蓋 · 資料家目錄 · DB 總覽
  E 環境   VCGC 手冊 ENV E01 ~ E11;要裝套件的三步只有你自己開了 VIA_NET_CONSENT=YES 才跑(本檔不設、不改同意閘)
  G 圖 · 路由 · 備份   graphify status / run(隔離環境在、可用記憶體 ≥ 7 GB)· VDF / VRN 自己的 omniroute · 每日備份 check
            · 外部閘道 OmniRoute 3.x(要同意閘才裝;先核登錄庫的完整性雜湊)· 已裝而埠 20128 沒人在聽 → 另開視窗啟動
  R 全景三回修正   ① token · 工具清單 · handoff check · CGC_MDL158 delta / report · ssot · 編號稽核 · SDD · VDF health / engine-matrix · VRN health
               ② CGC_MDL158 fix 乾跑;VIA_APPLY_FIX=1 才 --apply,改到別的系統的檔當場 git 還原並記紅「越界」
               ③ delta · test --quick · handoff check · overview

判燈只看各步的結束碼:0 綠 · 2 黃 · 逾時 / 其他 紅(不會再有「結束碼 2 卻寫完全通過」)。
並行道數 = min(加速器的執行緒預算, 依可用記憶體:<4 GB 1 道 · <8 GB 2 道 · 其餘 3 道);同一道裡的步驟依序跑;每 30 秒印一行心跳。
VCGC 動詞跑完一律把席位冊還原成提交的內容。輸出:VIA_Reports/vcgc/apply/APPLY_latest.json · APPLY_latest.txt(貼回包,末行 NEXT:)
· 頁面由卡片矩陣正主 CGC_MDL283 尾版照模板鎖冊產生(本檔不帶任何顏色)。
沒搬的(照實):舊 PS 的 D 道(讀 VDF 回合頁)與 F 道(一次性複製參考夾)— 舊檔 v0109 仍在,未刪。

用法:python VIA_VCGC_ApplyRun_v0100.py run [--only S,C,E,G,R] [--lanes N] [--no-open] · plan [--only …] · --selftest
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
import base64
import concurrent.futures as cf
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

VERSION = "v0100"
TAG = "VIA_VCGC_ApplyRun " + VERSION
HERE = Path(__file__).resolve().parent
GROUPS = ("S", "C", "E", "G", "R")
ZH = {"S": "三個同步台", "C": "工具與資料庫", "E": "環境(ENV 手冊)", "G": "圖 · 路由 · 備份", "R": "全景三回修正"}
SEAT = "supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json"
PEER_DIRS = re.compile(r"functional modules/(VDF|VRN|VQG|VAP)/|/VQG_|/VAP_")
OMNI_VER = "3.8.54"
OMNI_SRI = "sha512-CwAq+cK1fm2EnWqHCvQObfR+ACAEbEGQvgOGf/Fe0HxWRPvBqLO3+8Kry852g+q65nLBavcUAx/3zgMNkNdhAQ=="
PICK = re.compile(r"^\[(GREEN|YELLOW|RED|GRAY|NODATA|READY|ABSENT|BROKEN|計|交接防遺漏|VCGC 全功能串測|SDD 驗證|工具註冊清單|"
                  r"VCGC 功能一覽|同步|ENV MANAGER|DBM|家|目錄)|遺失 \d|應掃|^\s+\[(RED|FAIL|計|YEL)\]|NEXT:|omniroute|OmniRoute")
LOCK = threading.Lock()


# ───────────────────────── 找檔 ─────────────────────────
def find_via(start: Path | None = None) -> Path | None:
    env = os.environ.get("VIA_ROOT")
    if start is None and env and (Path(env) / "supportive modules" / "registry").is_dir():
        return Path(env).resolve()   # 短 PS 從 origin/main 取出本檔到 TEMP 跑時,用這個指回倉
    p = (start or HERE).resolve()
    for q in [p] + list(p.parents):
        if (q / "supportive modules" / "registry").is_dir():
            return q
    return None


def tail(folder: Path, pattern: str) -> Path | None:
    hits = sorted(p for p in folder.glob(pattern) if re.search(r"_v\d{4}\.py$", p.name))
    return hits[-1] if hits else None


def token_tool(via: Path) -> Path | None:
    """鎖冊 token 那一支(不自己取尾版)。"""
    try:
        lk = json.loads((via / "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        rel = str(lk["token"]["path"]).replace("\\", "/")
    except (OSError, ValueError, KeyError, TypeError):
        return None
    for c in (via / rel, via.parent / rel):
        if c.is_file():
            return c
    return None


def free_gb() -> float:
    try:
        import psutil  # noqa: PLC0415
        return round(psutil.virtual_memory().available / 1073741824, 1)
    except Exception:  # noqa: BLE001
        pass
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return round(int(line.split()[1]) / 1048576, 1)
    except OSError:
        pass
    return -1.0


def lanes_for(n_groups: int, want: int | None) -> tuple[int, str]:
    gb = free_gb()
    by_ram = 1 if 0 <= gb < 4 else 2 if 0 <= gb < 8 else 3
    budget = None
    try:
        if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "thread_budget"):
            b = VIA_ACCEL.thread_budget()
            budget = int(b if isinstance(b, (int, float)) else (b.get("threads") or b.get("workers") or 0) if isinstance(b, dict) else 0) or None
    except Exception:  # noqa: BLE001
        budget = None
    n = want or min(by_ram, budget or by_ram)
    n = max(1, min(n, n_groups, 6))
    why = "可用記憶體 %s GB → %d 道" % (gb, by_ram) + ("" if budget is None else " · 加速器預算 %d" % budget) + (" · 你指定 %d" % want if want else "")
    return n, why


# ───────────────────────── 一步 ─────────────────────────
class Step:
    def __init__(self, gid, name, entry, args, sec, own=False, note=""):
        self.gid, self.name, self.entry, self.args, self.sec, self.own, self.note = gid, name, entry, list(args), int(sec), own, note
        self.rc, self.lamp, self.secs, self.hits = None, "灰", 0, []


def run_step(st: Step, via: Path, logdir: Path, beat) -> Step:
    if st.entry is None or not Path(st.entry).is_file():
        st.lamp, st.hits = "紅", ["找不到入口檔:%s" % (st.entry or "—")]
        return st
    env = dict(os.environ, VIA_NO_OPEN="1", VIA_VCGC_PUSH="NO", PYTHONUTF8="1", PYTHONUNBUFFERED="1", PYTHONWARNINGS="ignore", VIA_PANORAMA_AUTO="0")
    if st.own:
        env.pop("VIA_FROM_VCGC", None)
    else:
        env["VIA_FROM_VCGC"] = "YES"
    out = logdir / ("%s_%s.out" % (st.gid, st.name))
    t0 = time.time()
    with out.open("w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.Popen([sys.executable, str(st.entry)] + st.args, cwd=str(via), env=env, stdout=fh, stderr=subprocess.STDOUT)
        last = t0
        while True:
            try:
                p.wait(timeout=2)
                break
            except subprocess.TimeoutExpired:
                now = time.time()
                if now - t0 > st.sec:
                    p.kill()
                    p.wait()
                    st.rc = 124
                    break
                if now - last >= 30:
                    beat("%s · %s 還在跑 %d 秒" % (st.gid, st.name, int(now - t0)))
                    last = now
        if st.rc is None:
            st.rc = p.returncode
    st.secs = int(time.time() - t0)
    text = out.read_text(encoding="utf-8", errors="replace").splitlines()
    absent = st.rc == 3 and any(x.lstrip().startswith("[ABSENT]") for x in text)
    st.lamp = "綠" if st.rc == 0 else "黃" if (st.rc == 2 or absent) else "逾時" if st.rc == 124 else "紅"   # [ABSENT] 是缺件(環境),照規則算黃
    hits = [x.strip() for x in text if PICK.search(x)][:12] or [x.strip() for x in text if x.strip()][-3:]
    st.hits = [re.sub(r"\x1b\[[0-9;]*m", "", h)[:210] for h in hits]
    restore_seat(via)   # 席位冊是 VCGC 的;不管哪一步改到都還原
    return st


def git(via: Path, *a, timeout=120) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", "-C", str(via.parent)] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)


def restore_seat(via: Path) -> None:
    with LOCK:
        rc, o = git(via, "status", "--porcelain", "--", "VeritasIntelligenceAnalytics/" + SEAT)
        if rc == 0 and o.strip():
            git(via, "checkout", "--", "VeritasIntelligenceAnalytics/" + SEAT)


# ───────────────────────── 同步 ─────────────────────────
def sync(via: Path, fetch=True) -> dict:
    if shutil.which("git") is None or not (via.parent / ".git").exists():
        return {"lamp": "灰", "line": "找不到 git 或 .git,沒有量"}
    frc = git(via, "fetch", "-q", "origin", timeout=600)[0] if fetch else None
    br = git(via, "rev-parse", "--abbrev-ref", "HEAD")[1].strip()
    head = git(via, "rev-parse", "--short", "HEAD")[1].strip()
    mrc, main = git(via, "rev-parse", "--short", "origin/main")
    main = main.strip()
    if mrc != 0:
        return {"lamp": "黃", "line": "本機 %s@%s · 找不到 origin/main(沒有遠端或沒 fetch 到),沒法比" % (br, head), "branch": br}
    ahead = git(via, "rev-list", "--count", "origin/main..HEAD")[1].strip()
    behind = git(via, "rev-list", "--count", "HEAD..origin/main")[1].strip()
    dirty = [x for x in git(via, "status", "--porcelain", "--untracked-files=no")[1].splitlines() if x.strip()]
    untr = [x for x in git(via, "ls-files", "--others", "--exclude-standard")[1].splitlines() if x.strip()]
    moved = ""
    if br == "main" and behind not in ("", "0") and not dirty:
        rc, o = git(via, "merge", "--ff-only", "origin/main", timeout=600)
        moved = " · 已快轉到 main" if rc == 0 else " · 快轉失敗:" + o.strip()[:120]
        if rc == 0:
            head, behind = git(via, "rev-parse", "--short", "HEAD")[1].strip(), "0"
    same = br == "main" and ahead == "0" and behind == "0" and not dirty
    line = "本機 %s@%s · GitHub main@%s · 本機多 %s 個提交 · 少 %s 個 · 改過未提交 %d 檔 · 未追蹤 %d 檔%s%s" % (
        br, head, main, ahead, behind, len(dirty), len(untr), moved, "" if frc in (None, 0) else " · fetch 結束碼 %s" % frc)
    if br != "main":
        line += " · 不在 main,不快轉(先把這條分支的工作提交,再切回 main)"
    return {"lamp": "綠" if same else "黃", "line": line, "branch": br, "ahead": ahead, "behind": behind, "dirty": len(dirty), "untracked": len(untr)}


# ───────────────────────── 計畫 ─────────────────────────
def plan(via: Path, only: list[str]) -> tuple[dict, list[str]]:
    reg = via / "supportive modules/registry"
    V = tail(reg, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
    E = token_tool(via)
    VD = tail(via / "functional modules/VDF", "VDF_SystemManager_v*.py")
    VR = tail(via / "functional modules/VRN", "VRN_SystemManager_v*.py")
    B = tail(via / "docs/handoff/ai", "VIA_DailyBackup_v*.py")
    consent = os.environ.get("VIA_NET_CONSENT") == "YES"
    notes, g = [], {}
    if "S" in only:
        g["S"] = [Step("S", "VCGC-sync", V, ["synchronizer", "--no-open"], 2400), Step("S", "VDF-sync", VD, ["synchronizer", "--no-open"], 2400, own=True),
                  Step("S", "VRN-sync", VR, ["synchronizer", "--no-open"], 2400, own=True)]
    if "C" in only:
        c = [Step("C", "VCGC-env-tools", V, ["run", "CGC_MDL273_EnvToolAudit", "audit"], 900)]
        if os.environ.get("VIA_APPLY_COVERAGE") == "1":
            c.append(Step("C", "VCGC-coverage", V, ["run", "CGC_MDL230_ToolCoverageProbe", "probe", "--plain", "--width", "200"], 2400))
        c += [Step("C", "DB-catalog", V, ["run", "CGC_MDL123_DataHome", "catalog", "--tables"], 1500), Step("C", "DB-overview", V, ["run", "CGC_MDL228_VIADBManager", "overview"], 1200)]
        g["C"] = c
    if "E" in only:
        G = "CGC_MDL135_EnvGovernance"
        e = [Step("E", "E01-現況", V, ["run", "CGC_MDL240_EnvManager", "check"], 1500), Step("E", "E04-計畫", V, ["run", G, "plan"], 1800),
             Step("E", "E02-衝突", V, ["run", G, "conflicts"], 900), Step("E", "E03-還原點", V, ["run", G, "lkgc"], 600), Step("E", "E05-工具冊", V, ["run", G, "tools"], 1500)]
        if consent:
            e += [Step("E", "E07-沙盒模擬", V, ["run", G, "run"], 5400), Step("E", "E08-照計畫安裝", V, ["run", G, "apply", "--approve"], 12600),
                  Step("E", "E09-工具冊補裝", V, ["run", G, "tools", "--apply", "--approve"], 7200)]
        else:
            notes.append("[E] 同意閘沒開:E07 ~ E09(會下載安裝)這一輪不跑;要裝先在同一個視窗設 VIA_NET_CONSENT=YES")
        e += [Step("E", "E10-重驗", V, ["run", "CGC_MDL240_EnvManager", "check"], 1500), Step("E", "E11-還原點", V, ["run", G, "lkgc"], 600)]
        g["E"] = e
    if "G" in only:
        s = [Step("G", "Graphify-status", V, ["graphify", "status"], 300)]
        gx = Path(os.environ.get("VIA_GRAPHIFY_PY") or Path.home() / "envs/via_graphify/Scripts/graphify.exe")
        gb = free_gb()
        if os.environ.get("VIA_APPLY_NOGRAPH") == "1":
            notes.append("[G] 你設了 VIA_APPLY_NOGRAPH=1:這一輪不畫圖")
        elif not gx.exists():
            notes.append("[G] Graphify 隔離環境不在(%s)→ 不畫圖;建法見 docs/handoff/ai/via_graphify_v0101" % gx)
        elif 0 <= gb < 7 and os.environ.get("VIA_GRAPHIFY_FORCE") != "1":
            notes.append("[G] Graphify 畫圖跳過 · 可用記憶體 %s GB(VCGC 那張圖在容器量到的峰值約 5.5 GB,留 7 GB 才跑);硬跑設 VIA_GRAPHIFY_FORCE=1" % gb)
        else:
            s.append(Step("G", "Graphify-VCGC", V, ["graphify", "run", "--system", "VCGC"], 3600))
        s += [Step("G", "VDF-omniroute", VD, ["omniroute"], 300, own=True), Step("G", "VRN-omniroute", VR, ["omniroute"], 300, own=True)]
        if os.environ.get("VIA_APPLY_BACKUP") == "1":
            s.append(Step("G", "Backup", B, ["backup"], 900))
        s.append(Step("G", "Backup-check", B, ["check"], 600))
        g["G"] = s
    if "R" in only:
        if E is None:
            notes.append("[R] 鎖冊上的省 Token 工具找不到;R 道的 CGC_MDL158 步會亮紅(本檔不自己取尾版)")
        r = [Step("R", "R1-token", V, ["token"], 300), Step("R", "R1-tools", E, ["tools"], 120), Step("R", "R1-handoff", V, ["handoff", "check"], 900),
             Step("R", "R1-delta", E, ["delta", "--max", "40"], 900), Step("R", "R1-report", E, ["report"], 900), Step("R", "R1-ssot", V, ["ssot", "panorama"], 600),
             Step("R", "R1-numbering", V, ["run", "CGC_MDL237_NumberingSystem", "audit"], 600), Step("R", "R1-sdd", V, ["run", "CGC_MDL245_SDDValidator", "check"], 600),
             Step("R", "R1-VDF-health", VD, ["health"], 900, own=True), Step("R", "R1-VDF-engine-matrix", VD, ["engine-matrix"], 900, own=True),
             Step("R", "R1-VRN-health", VR, ["health"], 900, own=True), Step("R", "R2-fix-dry", E, ["fix"], 900)]
        if os.environ.get("VIA_APPLY_FIX") == "1":
            r.append(Step("R", "R2-fix-apply", E, ["fix", "--apply"], 1800, note="boundary"))
        else:
            notes.append("[R] 修正只乾跑(清單在 R_R2-fix-dry.out);要真的改先設 VIA_APPLY_FIX=1")
        r += [Step("R", "R3-delta", E, ["delta", "--max", "40"], 900), Step("R", "R3-test-quick", V, ["test", "--quick"], 1800),
              Step("R", "R3-handoff", V, ["handoff", "check"], 900), Step("R", "R3-overview", V, ["overview", "--no-open"], 900)]
        notes.append("[R] 灰 · 沒有現成工具:VDF 以外會擷取的模組的網路橋覆蓋 · 錯誤自動分成一次解決 / 依序解決與九頭龍風險(由 AI 讀貼回包判讀)")
        g["R"] = r
    return g, notes


def run_group(steps: list[Step], via: Path, logdir: Path, beat) -> list[Step]:
    for st in steps:
        before = None
        if st.note == "boundary":
            before = set(git(via, "status", "--porcelain", "--untracked-files=all")[1].splitlines())
        beat("%s · %s 開始" % (st.gid, st.name))
        run_step(st, via, logdir, beat)
        if before is not None:
            new = [x for x in git(via, "status", "--porcelain", "--untracked-files=all")[1].splitlines() if x not in before]
            cross = [x for x in new if PEER_DIRS.search(x)]
            for x in cross:
                path = x[3:].strip().strip('"')
                if x.startswith("??"):
                    st.hits.append("越界:fix 在別的系統新增了 %s(沒有刪,留給你看)" % path)
                else:
                    rc = git(via, "checkout", "--", path)[0]
                    st.hits.append("越界:fix 改到別的系統的檔 %s → 已用 git 還原(結束碼 %s)" % (path, rc))
            if cross:
                st.lamp = "紅"
            st.hits.append("fix --apply 之後新改動 %d 檔 · 其中別的系統 %d 檔" % (len(new), len(cross)))
        beat("%s · %s %s · 結束碼 %s · %d 秒" % (st.gid, st.name, st.lamp, st.rc, st.secs))
    return steps


# ───────────────────────── OmniRoute(外部閘道) ─────────────────────────
def omni_port() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 20128), timeout=0.7):
            return True
    except OSError:
        return False


def omniroute(logdir: Path) -> tuple[str, str]:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "VIA" / "tools"
    o3, old = base / "OmniRoute3", base / "OmniRoute"
    cmd3 = o3 / "node_modules" / ".bin" / ("omniroute.cmd" if os.name == "nt" else "omniroute")
    has3, hasold = cmd3.exists(), (old / "package.json").exists()
    if not has3 and not hasold:
        if os.environ.get("VIA_NET_CONSENT") != "YES":
            return "灰", "外部閘道沒有裝;要裝:在同一個視窗設 VIA_NET_CONSENT=YES 再跑一次"
        node, npm = shutil.which("node"), shutil.which("npm")
        if not node or not npm:
            return "黃", "找不到 node / npm(本檔不裝 Node)"
        nv = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
        try:
            maj, mi, pa = (int(x) for x in (nv.split(".") + ["0", "0"])[:3])
        except ValueError:
            return "黃", "node 版本讀不懂:%s" % nv
        if not ((maj == 22 and (mi, pa) >= (22, 2)) or 24 <= maj < 27):
            return "黃", "node %s 不在 OmniRoute 3.x 的支援範圍(22.22.2 以上的 22.x,或 24–26)" % nv
        sri = subprocess.run([npm, "view", "omniroute@" + OMNI_VER, "dist.integrity"], capture_output=True, text=True, timeout=120).stdout.strip()
        if sri != OMNI_SRI:
            return "紅", "登錄庫回報的 %s 完整性雜湊跟本檔釘的不一樣(或問不到),不裝" % OMNI_VER
        o3.mkdir(parents=True, exist_ok=True)
        p = subprocess.run([npm, "install", "--prefix", str(o3), "--no-audit", "--no-fund", "omniroute@" + OMNI_VER], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
        (logdir / "G_OmniRoute-install.out").write_text((p.stdout or "") + (p.stderr or ""), encoding="utf-8")
        has3 = cmd3.exists()
        if not has3:
            return "紅", "npm 安裝結束碼 %s,安裝夾裡沒有 omniroute(看 G_OmniRoute-install.out)" % p.returncode
    if os.environ.get("VIA_APPLY_NOOMNI") == "1":
        return "灰", "你設了 VIA_APPLY_NOOMNI=1:裝了但這一輪不啟動"
    if omni_port():
        return "綠", "已經在跑(埠 20128 有人在聽)· http://localhost:20128"
    if os.name != "nt":
        return "灰", "不是 Windows,不另開視窗啟動"
    data = base / "omniroute-data"
    data.mkdir(parents=True, exist_ok=True)
    if has3:
        line = "$env:PORT='20128'; $env:DATA_DIR='%s'; & '%s'" % (str(data).replace("'", "''"), str(cmd3).replace("'", "''"))
        cwd, which = o3, "3.x(npm 版)"
    else:
        line, cwd, which = "npm run start", old, "舊版(git 版)"
    subprocess.Popen(["pwsh", "-NoExit", "-NoProfile", "-Command", line], cwd=str(cwd), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    for _ in range(30):
        time.sleep(2)
        if omni_port():
            return "綠", "%s 已在另一個視窗啟動並開始聽 · http://localhost:20128 · 關那個視窗就停" % which
    return "黃", "%s 的視窗開了,60 秒內埠 20128 還沒人在聽(看那個視窗)" % which


# ───────────────────────── 輸出 ─────────────────────────
LAMP_KEY = {"綠": "g", "黃": "y", "紅": "r", "逾時": "r", "灰": "x"}


def write_outputs(via: Path, outdir: Path, res: dict, page: bool, open_page: bool) -> Path | None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "APPLY_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# %s · %s · 總燈 %s" % (TAG, res["at"], res["lamp"]), "[一致性] %s · %s" % (res["sync"]["lamp"], res["sync"]["line"]), "[道數] " + res["lanes_why"]]
    lines += res["notes"]
    for s in res["steps"]:
        lines.append("[%s] %s · %s · 結束碼 %s · %d 秒" % (s["group"], s["name"], s["lamp"], s["rc"], s["secs"]))
        if s["lamp"] != "綠":
            lines += ["    " + h for h in s["hits"][:6]]
    if res.get("omniroute"):
        lines.append("[OmniRoute] %s · %s" % tuple(res["omniroute"]))
    lines.append("NEXT: " + res["next"])
    (outdir / "APPLY_latest.txt").write_text("\n".join(lines[:300]) + "\n", encoding="utf-8")
    if not page:
        return None
    cmf = tail(via / "supportive modules/registry", "CGC_MDL283_CardMatrixFeedback_v*.py")
    if cmf is None:
        return None
    items = [{"section": "%s %s" % (s["group"], ZH[s["group"]]), "system": "VCGC", "lamp": LAMP_KEY.get(s["lamp"], "x"), "id": s["name"],
              "title": s["name"], "detail": " · ".join(s["hits"][:3]) or "—", "ver": VERSION, "at": res["at"], "needs": s["lamp"] != "綠"} for s in res["steps"]]
    items.insert(0, {"section": "0 一致性", "system": "VCGC", "lamp": LAMP_KEY[res["sync"]["lamp"]], "id": "sync", "title": "本機對 GitHub main",
                     "detail": res["sync"]["line"], "ver": VERSION, "at": res["at"], "needs": res["sync"]["lamp"] != "綠"})
    secs = sorted({i["section"] for i in items})
    book = {"source": TAG, "title": "VCGC 一鍵套用 · " + res["at"], "groups": [[s, [s]] for s in secs], "items": items}
    src = outdir / "APPLY_items.json"
    src.write_text(json.dumps(book, ensure_ascii=False), encoding="utf-8")
    args = [sys.executable, str(cmf), "run", "--in", str(src), "--out", str(outdir / "page"), "--root", str(via), "--no-clip"] + ([] if open_page else ["--no-open"])
    subprocess.run(args, cwd=str(via), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    pages = sorted((outdir / "page").glob("*.html"), key=lambda p: p.stat().st_mtime)
    return pages[-1] if pages else None


def run(via: Path, only: list[str], want: int | None, open_page: bool, page: bool = True, outdir: Path | None = None, do_sync: bool = True) -> int:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    outdir = outdir or via / "VIA_Reports" / "vcgc" / "apply"
    logdir = outdir / ("run_" + stamp)
    logdir.mkdir(parents=True, exist_ok=True)

    def beat(msg):
        with LOCK:
            print("  %s  %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

    sy = sync(via) if do_sync else {"lamp": "灰", "line": "這一輪沒有量(--no-sync)"}
    beat("[一致性] %s · %s" % (sy["lamp"], sy["line"]))
    g, notes = plan(via, only)
    n, why = lanes_for(len(g), want)
    beat("[道數] " + why + " · 道:" + " ".join("%s %s" % (k, ZH[k]) for k in g))
    done: list[Step] = []
    with cf.ThreadPoolExecutor(max_workers=n) as ex:
        for fut in [ex.submit(run_group, g[k], via, logdir, beat) for k in g]:
            done += fut.result()
    omni = omniroute(logdir) if "G" in only else None
    lamps = [s.lamp for s in done] + ([omni[0]] if omni else [])
    lamp = "紅" if any(x in ("紅", "逾時") for x in lamps) else "黃" if ("黃" in lamps or sy["lamp"] == "黃") else "綠"
    bad = [s for s in done if s.lamp in ("紅", "逾時")]
    nxt = ("先看紅的 %d 步:%s" % (len(bad), " · ".join(s.name for s in bad[:5]))) if bad else ("看黃的步" if lamp == "黃" else "全綠;照實是容器還是主機,看上面")
    if sy.get("branch") not in (None, "main"):
        nxt += ";桌機不在 main,先把那條分支的工作提交再切回 main"
    res = {"tool": TAG, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "lamp": lamp, "only": only, "lanes": n, "lanes_why": why, "sync": sy, "notes": notes,
           "steps": [{"group": s.gid, "name": s.name, "entry": str(s.entry or ""), "args": s.args, "own": s.own, "rc": s.rc, "lamp": s.lamp, "secs": s.secs, "hits": s.hits} for s in done],
           "omniroute": list(omni) if omni else None, "next": nxt, "logdir": str(logdir), "not_ported": ["舊 PS 的 D 道(讀 VDF 回合頁)", "舊 PS 的 F 道(一次性複製參考夾)"]}
    pg = write_outputs(via, outdir, res, page, open_page)
    print("[%s] 總燈 %s · %d 步(綠 %d · 黃 %d · 紅 %d)· 貼回包 %s%s" % (TAG, lamp, len(done), sum(s.lamp == "綠" for s in done), sum(s.lamp == "黃" for s in done),
                                                               len(bad), outdir / "APPLY_latest.txt", (" · 頁 %s" % pg) if pg else ""), flush=True)
    for n_ in notes:
        print(n_)
    print("NEXT: " + nxt)
    return 1 if lamp == "紅" else 2 if lamp == "黃" else 0


# ───────────────────────── 自測(全部在暫存夾) ─────────────────────────
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    print("=== %s 自測(暫存夾 · 假入口 · 不連網 · 不碰真樹)===" % TAG)
    with tempfile.TemporaryDirectory(prefix="via_applyrun_") as td:
        root = Path(td) / "repo"
        via = root / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules/registry"
        reg.mkdir(parents=True)
        (via / "functional modules/VDF").mkdir(parents=True)
        (via / "functional modules/VRN").mkdir(parents=True)
        (via / "docs/handoff/ai").mkdir(parents=True)
        fake = ("import os,sys,time,pathlib\na=sys.argv[1:]\nprint('[計] fake', ' '.join(a), 'FROM=' + os.environ.get('VIA_FROM_VCGC','-'))\n"
                "seat=pathlib.Path('supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json')\n"
                "if seat.exists(): seat.write_text('{\"dirty\":1}')\n"
                "if a and a[0]=='yellow': sys.exit(2)\nif a and a[0]=='absent': print('[ABSENT] no env'); sys.exit(3)\nif a and a[0]=='three': sys.exit(3)\nif a and a[0]=='red': print('[RED] boom'); sys.exit(1)\n"
                "if a and a[0]=='slow': time.sleep(30)\n"
                "if a[:2]==['fix','--apply']:\n  pathlib.Path('functional modules/VDF/VDF_X_v0100.py').write_text('x=2\\n')\n  pathlib.Path('supportive modules/registry/CGC_Y_v0100.py').write_text('y=2\\n')\n")
        V = reg / "CGC_MDL149_VeritasCentralGovernanceConsole_v0999.py"
        V.write_text(fake, encoding="utf-8")
        (via / "functional modules/VDF/VDF_SystemManager_v0999.py").write_text(fake, encoding="utf-8")
        (via / "functional modules/VDF/VDF_X_v0100.py").write_text("x=1\n", encoding="utf-8")
        (reg / "CGC_Y_v0100.py").write_text("y=1\n", encoding="utf-8")
        (reg / "VIA_VCGC_SubsystemSeat_v0100.json").write_text("{}", encoding="utf-8")
        E = reg / "CGC_MDL158_VIAPanoramaAuditRepair_v0999.py"
        E.write_text(fake, encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"token": {"path": "supportive modules/registry/" + E.name}}), encoding="utf-8")
        have_git = shutil.which("git") is not None
        if have_git:
            for a in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"], ["add", "-A"], ["commit", "-q", "-m", "seed"]):
                subprocess.run(["git", "-C", str(root)] + a, capture_output=True)
        os.environ["VIA_ROOT"] = str(via)
        try:
            by_env = find_via()
        finally:
            os.environ.pop("VIA_ROOT", None)
        chk("① 找 VIA 夾(本檔所在或 VIA_ROOT)· 尾版 · 鎖冊上的 token 工具(不自己取尾版)", find_via(reg) == via and by_env == via and tail(reg, "CGC_MDL149_*_v*.py") == V and token_tool(via) == E)
        logdir = Path(td) / "log"
        logdir.mkdir()
        beats = []
        st = [Step("T", "green", V, ["ok"], 20), Step("T", "yellow", V, ["yellow"], 20), Step("T", "red", V, ["red"], 20), Step("T", "slow", V, ["slow"], 3),
              Step("T", "own", via / "functional modules/VDF/VDF_SystemManager_v0999.py", ["ok"], 20, own=True), Step("T", "missing", None, [], 5),
              Step("T", "absent", V, ["absent"], 20), Step("T", "three", V, ["three"], 20)]
        os.environ["VIA_FROM_VCGC"] = "YES"
        try:
            for s in st:
                run_step(s, via, logdir, beats.append)
        finally:
            os.environ.pop("VIA_FROM_VCGC", None)
        chk("② 判燈只看結束碼:0 綠 · 2 黃 · 1 紅 · 逾時 · 入口不在 = 紅 · 3 而且印 [ABSENT] = 黃(缺件)· 3 沒說原因 = 紅", [s.lamp for s in st] == ["綠", "黃", "紅", "逾時", "綠", "紅", "黃", "紅"], [s.lamp for s in st])
        chk("③ VCGC 步帶 VIA_FROM_VCGC=YES;VDF / VRN 從自己的入口跑不帶", any("FROM=YES" in h for h in st[0].hits) and any("FROM=-" in h for h in st[4].hits), (st[0].hits, st[4].hits))
        chk("④ 紅步的判決行有抓到 · 每步一個日誌檔", any("[RED] boom" in h for h in st[2].hits) and (logdir / "T_red.out").exists())
        if have_git:
            seat_clean = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
            chk("⑤ VCGC 動詞改了席位冊 → 跑完還原成提交的內容", seat_clean == "", seat_clean)
            fx = Step("R", "R2-fix-apply", E, ["fix", "--apply"], 20, note="boundary")
            run_group([fx], via, logdir, beats.append)
            vdf_after = (via / "functional modules/VDF/VDF_X_v0100.py").read_text()
            own_after = (reg / "CGC_Y_v0100.py").read_text()
            chk("⑥ fix --apply 改到 VDF 的檔 → 當場還原、燈紅、寫「越界」;VCGC 自己的改動留著", fx.lamp == "紅" and vdf_after == "x=1\n" and own_after == "y=2\n"
                and any("越界" in h for h in fx.hits), fx.hits)
            sy = sync(via, fetch=False)
            chk("⑦ 一致性:沒有 origin 也照實寫一行(不丟例外)", isinstance(sy.get("line"), str) and sy["lamp"] in ("黃", "灰", "綠"), sy.get("line"))
        else:
            chk("⑤ ⑥ ⑦(這台沒有 git:跳過 = 黃,不算綠)", False, "no git")
        os.environ["VIA_NET_CONSENT"] = ""
        g, notes = plan(via, ["E", "R"])
        chk("⑧ 同意閘沒開:E07 ~ E09 不排 · R 只乾跑 fix · 沒工具的兩件照實寫灰", not any(s.name.startswith(("E07", "E08", "E09")) for s in g["E"])
            and not any(s.name == "R2-fix-apply" for s in g["R"]) and any("沒有現成工具" in x for x in notes))
        n, why = lanes_for(5, None)
        chk("⑨ 道數 1 ~ 3(依記憶體與加速器預算)", 1 <= n <= 3, why)
        os.environ.pop("VIA_NET_CONSENT", None)
        out = Path(td) / "out"
        res_rc = run(via, ["S"], 1, open_page=False, page=False, outdir=out, do_sync=False)
        txt = (out / "APPLY_latest.txt").read_text(encoding="utf-8").splitlines()
        js = json.loads((out / "APPLY_latest.json").read_text(encoding="utf-8"))
        chk("⑩ 一輪跑完:收據 + 貼回包(≤ 300 行 · 末行 NEXT:)· 入口不在的步照實紅 · 結束碼照總燈", txt[-1].startswith("NEXT:") and len(txt) <= 300
            and js["lamp"] == "紅" and res_rc == 1 and len(js["steps"]) == 3, (js["lamp"], res_rc))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 加速器橋在 · 不碰 TA-Lib · 本檔沒有色碼 · 不設同意閘", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"#[0-9a-fA-F]{6}\b", src) and not re.search(r"environ\[.VIA_NET_CONSENT.\]\s*=\s*.YES", src))
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if not a or a[0] not in ("run", "plan"):
        print(__doc__.strip().splitlines()[-1])
        return 2
    only, want = list(GROUPS), None
    if "--only" in a:
        i = a.index("--only")
        only = [x.strip().upper() for x in (a[i + 1] if i + 1 < len(a) else "").split(",") if x.strip().upper() in GROUPS]
        if not only:
            print("[%s] --only 要給 S,C,E,G,R 其中幾個" % TAG)
            return 2
    if "--lanes" in a:
        try:
            want = int(a[a.index("--lanes") + 1])
        except (IndexError, ValueError):
            print("[%s] --lanes 要給數字" % TAG)
            return 2
    via = find_via()
    if via is None:
        print("[%s] 找不到 VIA 夾(要有 supportive modules/registry)" % TAG)
        return 1
    if a[0] == "plan":
        g, notes = plan(via, only)
        for k, steps in g.items():
            for s in steps:
                print("%s %-22s %s %s%s" % (k, s.name, Path(s.entry).name if s.entry else "(找不到)", " ".join(s.args), " · 自己的入口" if s.own else ""))
        for n_ in notes:
            print(n_)
        return 0
    return run(via, only, want, open_page="--no-open" not in a)


if __name__ == "__main__":
    raise SystemExit(main())
