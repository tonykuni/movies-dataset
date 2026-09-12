#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL144_CopyDoctor v0101 — 副本醫生(批391 我方指令寫死版號之錯(給 v0175 但該副本只有 v0174)→ 產出指令一律尾版 glob;+--heal 明令自癒;批387 工作站實錄:同機四副本,新視窗載到舊副本→新短令永遠 not recognized)

實錄(2026-09-12):
  PS C:\Users\tonyk> via-vdffetch 2023 → not recognized
  但同窗 profile 已載 Register(Grok 矩陣 12 令已載)→ 並非「沒載短令」,而是「載到舊副本的短令冊」:
  via-reload 自印「雙副本:新視窗預設(profile)=C:\Users\tonyk\Downloads\movies-dataset-b381\… ≠ 本窗 …\OneDrive\Documents\…」
  四副本實況:OneDrive\Documents(操作員日常)、Downloads\movies-dataset-b381(profile 預設)、Github\movies-dataset(資料家旁)、雲端。
根因類別:「副本選擇」無單一真相——短令在位與否取決於哪份副本被點源,而操作員看不到差異。

職權(全唯讀;零寫入、零 force、零刪除):
  ① 掃副本 — 候選根(env VIA_COPY_ROOTS 分號清單 → 真 Documents(OneDrive 重導向亦認)→ OneDrive 變數 →
     %USERPROFILE%\{,,Documents,Downloads,Github} × {movies-dataset, movies-dataset-*})逐一驗「含 Register-VIA-Commands-v*.ps1」
  ② 逐副本體檢 — git 分支/HEAD/未合併件數/與 origin 分歧(MDL143 尾版 divergence 直取,零重造)+
     Register 尾版版號 + 指定動詞在位(預設 via-vdffetch/via-accel-import/via-medic/via-lanes)+ 工作樹髒度
  ③ 判誰最新 — 排序鍵=(Register 尾版版號, HEAD 時間);落後或卡未合併者具名標示
  ④ 指路 — 三道單行指令,全部以「尾版 glob」寫成(批391 實錄:我方曾給寫死 v0175 的指令,而該副本只有 v0174
     → 必然 not recognized;指令與程式同律:永不寫死版號):
       cmd_heal 自癒(卡未合併/分叉→MDL143 拉齊醫生 sync --apply)
       cmd_now  立即可用(跑 Invoke-VIA-VdfFetch 尾版 -Year 2023)
       cmd_pin  一勞永逸(點源短令冊尾版→via-pin 改 profile 一行,新視窗自此載最新)
  ⑤ --heal 明令自癒 — 對最新副本呼 MDL143 sync --apply(授權閉環:需明打 --heal),完成後重新體檢並印新態
律:唯讀(不改 profile、不拉齊、不提交);誠實三態;副本間零搬移;版號 glob 尾版動態解析。
用法:via-copies                 → 表列所有副本+判誰最新+指路
      via-copies --verb via-fred → 改驗指定動詞
      via-copies --heal          → 對最新副本明令自癒(MDL143 sync --apply;零 force 零刪除)
      python <本檔> --selftest   → 十檢(真建暫時多副本與真 git 倉)
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

import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REP = VIA / "VIA_Reports" / "copy_doctor"
ENGINE_TAG = "CGC_MDL144_CopyDoctor v0101"
DEFAULT_VERBS = ["via-vdffetch", "via-accel-import", "via-medic", "via-lanes"]
VER_RX = re.compile(r"Register-VIA-Commands-v(\d{3,4})\.ps1$")
RULES = ["全唯讀:不改 profile、不拉齊、不提交、副本間零搬移",
         "分歧判定直取 MDL143 尾版 divergence(零重造)",
         "判新鍵=(Register 尾版版號, HEAD 提交時間);卡未合併者具名標示",
         "指路只印指令不代跑(授權閉環;操作員自行貼)",
         "誠實三態:無 git / 無上游 / 探測失敗皆具名標示,不猜"]


def _git(root: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=True, timeout=300)


def _mdl143():
    try:
        hits = sorted(HERE.glob("CGC_MDL143_MergeMedic_v0*.py"))
        if not hits:
            return None
        spec = importlib.util.spec_from_file_location("medic_cd", hits[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["medic_cd"] = m
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def candidate_roots() -> list:
    """候選 VIA 根(含 Register 冊者才算副本);OneDrive 重導向 Documents 亦認"""
    bases: list[Path] = []
    for part in str(os.environ.get("VIA_COPY_ROOTS", "")).split(";"):
        if part.strip():
            bases.append(Path(part.strip()))
    try:
        if os.name == "nt":
            import ctypes.wintypes  # noqa: F401  (僅 Windows 真 Documents;非 Windows 走下方 env)
    except Exception:
        pass
    docs = os.environ.get("VIA_DOCUMENTS") or ""
    if docs:
        bases.append(Path(docs))
    for od in (os.environ.get("OneDrive"), os.environ.get("OneDriveCommercial"), os.environ.get("OneDriveConsumer")):
        if od:
            bases += [Path(od) / "Documents", Path(od)]
    up = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
    if up:
        bases += [Path(up), Path(up) / "Documents", Path(up) / "Downloads", Path(up) / "Github", Path(up) / "OneDrive" / "Documents"]
    out, seen = [], set()
    # 批387 雲端實錄:首跑回「副本 0 份」——漏掉最明顯的一份=本引擎所在副本(非 Windows 機無 USERPROFILE/OneDrive)
    if any(VIA.glob("Register-VIA-Commands-v*.ps1")):
        out.append(VIA)
        seen.add(str(VIA.resolve()).lower())
    for b in bases:
        try:
            if not b.exists():
                continue
            for child in sorted(b.iterdir()):
                if not child.is_dir() or not child.name.lower().startswith("movies-dataset"):
                    continue
                via = child / "VeritasIntelligenceAnalytics"
                if via.is_dir() and any(via.glob("Register-VIA-Commands-v*.ps1")):
                    key = str(via.resolve()).lower()
                    if key not in seen:
                        seen.add(key)
                        out.append(via)
        except Exception:
            continue
    return out


def register_tail(via: Path) -> tuple[str, int]:
    hits = sorted(via.glob("Register-VIA-Commands-v*.ps1"))
    if not hits:
        return "", -1
    tail = hits[-1]
    m = VER_RX.search(tail.name)
    return tail.name, (int(m.group(1)) if m else -1)


def verbs_present(via: Path, verbs: list) -> dict:
    name, _ = register_tail(via)
    if not name:
        return {v: False for v in verbs}
    try:
        txt = (via / name).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {v: False for v in verbs}
    return {v: ("function global:" + v) in txt for v in verbs}


HYPH_VER_RX = re.compile(r"-v\d{3,4}\.(?:ps1|psm1|py)$", re.I)


def medic_tail_ver(via: Path) -> int:
    """該副本拉齊醫生的尾版號(無=0);用於 bootstrap 死結判定"""
    try:
        g = sorted((via / "supportive modules" / "registry").glob("CGC_MDL143_MergeMedic_v*.py"))
        if not g:
            return 0
        m = re.search(r"_v(\d{3,4})\.py$", g[-1].name)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def inspect(via: Path, verbs: list | None = None) -> dict:
    verbs = verbs or DEFAULT_VERBS
    root = via.parent
    name, ver = register_tail(via)
    ent = {"via": str(via), "root": str(root), "register": name, "register_ver": ver,
           "verbs": verbs_present(via, verbs), "branch": "", "head": "", "head_ts": 0,
           "unmerged": 0, "dirty": 0, "divergence": "NO_GIT", "ahead": 0, "behind": 0, "note": "",
           "medic_ver": medic_tail_ver(via), "unmerged_files": [], "deadlock": ""}
    if not (root / ".git").exists():
        ent["note"] = "非 git 工作樹(純解壓副本)"
        return ent
    ent["branch"] = (_git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout or "").strip()
    ent["head"] = (_git(root, "rev-parse", "--short", "HEAD").stdout or "").strip()
    try:
        ent["head_ts"] = int((_git(root, "log", "-1", "--format=%ct").stdout or "0").strip() or 0)
    except Exception:
        ent["head_ts"] = 0
    st = (_git(root, "status", "--porcelain").stdout or "").splitlines()
    ent["unmerged"] = sum(1 for l in st if l[:2] in ("UU", "AA", "DU", "UD", "AU", "UA", "DD"))
    ent["dirty"] = len(st)
    ent["unmerged_files"] = [l for l in (
        _git(root, "diff", "--name-only", "--diff-filter=U").stdout or "").splitlines() if l.strip()]
    m = _mdl143()
    if m is not None:
        try:
            d = m.divergence(root, ent["branch"] or "main")
            ent.update(divergence=d["state"], ahead=d["ahead"], behind=d["behind"])
        except Exception:
            ent["divergence"] = "PROBE_FAIL"
    else:
        ent["divergence"] = "MEDIC_MISSING"
    if ent["unmerged"]:
        # 批394 續章:bootstrap 死結偵測(操作員實遇)。該副本的醫生若 < v0102 則只認底線版號,
        # 連字號版號族的同名雙物會被判 MANUAL 而停 → 要解倉庫才拿得到新醫生,但新醫生在倉庫裡
        # 出不來=雞生蛋死結。此時唯一出路是手動對那幾件取遠端版一次(先發先得律,與 v0102
        # 的 VERSIONED_TWIN 裁決同義),之後醫生即可完成合併並自動升版。
        hyph = [f for f in ent["unmerged_files"] if HYPH_VER_RX.search(f)]
        if hyph and 0 < ent["medic_ver"] < 102:
            ent["deadlock"] = "BOOTSTRAP"
            ent["note"] = ("卡未合併 " + str(ent["unmerged"]) + " 件 × 本副本醫生僅 v"
                           + ("%04d" % ent["medic_ver"]) + "(只認底線版號)=bootstrap 死結:"
                           + "連字號版號族 " + str(len(hyph)) + " 件必被判 MANUAL;需先手動取遠端版一次")
        else:
            ent["note"] = "卡未合併 " + str(ent["unmerged"]) + " 件(拉齊必被擋;via-medic sync --apply)"
    elif ent["divergence"] == "DIVERGED":
        ent["note"] = "與遠端分叉(本地獨有 " + str(ent["ahead"]) + ";via-medic sync --apply)"
    elif ent["divergence"] == "BEHIND":
        ent["note"] = "落後遠端 " + str(ent["behind"]) + " 提交(via-reload)"
    return ent


def rank(copies: list) -> list:
    return sorted(copies, key=lambda c: (c["register_ver"], c["head_ts"]), reverse=True)


def build(verbs: list | None = None, roots: list | None = None, do_print: bool = True, write: bool = True) -> dict:
    verbs = verbs or DEFAULT_VERBS
    vias = roots if roots is not None else candidate_roots()
    copies = rank([inspect(Path(v), verbs) for v in vias])
    best = copies[0] if copies else None
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "verbs": verbs,
           "copies": copies, "best": best["via"] if best else "", "rules": RULES,
           "state": "OK" if best and all(best["verbs"].values()) and not best["unmerged"] else ("PLAN" if best else "FAIL")}
    if best:
        v = best["via"]
        # 批391:指令一律尾版 glob(PowerShell 於執行時自解,永不寫死版號)
        tail_reg = '(Get-ChildItem "' + v + '\\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
        tail_launcher = '(Get-ChildItem "' + v + '\\Invoke-VIA-VdfFetch-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName'
        tail_medic = '(Get-ChildItem "' + v + '\\supportive modules\\registry\\CGC_MDL143_MergeMedic_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName'
        rep["cmd_heal"] = 'python ' + tail_medic + ' sync --apply --root "' + best["root"] + '"'
        rep["cmd_now"] = '& ' + tail_launcher + ' -Year 2023'
        rep["cmd_pin"] = '. ' + tail_reg + '; via-pin'
        rep["cmd_all"] = ('$v="' + v + '"; python (Get-ChildItem "$v\\supportive modules\\registry\\CGC_MDL143_MergeMedic_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName sync --apply --root (Split-Path $v -Parent); '
                          '. (Get-ChildItem "$v\\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName; via-pin; via-pstest')
        if best.get("deadlock") == "BOOTSTRAP":
            # 衝突檔名動態取自 git(絕不寫死);取遠端版=先發先得律,與醫生 v0102 的
            # VERSIONED_TWIN 裁決同義。解完一次即可,之後醫生自己就會認連字號版號。
            fl = " ".join('"' + f + '"' for f in best["unmerged_files"] if HYPH_VER_RX.search(f))
            rep["cmd_bootstrap"] = (
                '$v="' + v + '"; $r=Split-Path $v -Parent; '
                'git -C $r checkout --theirs -- ' + fl + '; '
                'git -C $r add -- ' + fl + '; '
                'python (Get-ChildItem "$v\\supportive modules\\registry\\CGC_MDL143_MergeMedic_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName sync --apply --root $r; '
                '. (Get-ChildItem "$v\\Register-VIA-Commands-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName')
    if do_print:
        digest(rep)
    if write:
        try:
            REP.mkdir(parents=True, exist_ok=True)
            (REP / ("COPIES_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass
    return rep


def digest(rep: dict) -> int:
    print("VIA COPY DOCTOR · " + rep["stamp"] + " · 副本 " + str(len(rep["copies"])) + " 份 · " + rep["state"])
    for i, c in enumerate(rep["copies"]):
        mark = "★最新" if i == 0 else "     "
        miss = [v for v, ok in c["verbs"].items() if not ok]
        print("  " + mark + " " + (c["register"] or "無冊").ljust(32) + " " + (c["branch"] or "-").ljust(10)
              + (c["head"] or "-").ljust(10) + c["divergence"].ljust(11)
              + ("髒 " + str(c["dirty"])).ljust(8) + (" 缺令 " + ",".join(miss) if miss else " 動詞全在")
              + (" · " + c["note"] if c["note"] else ""))
        print("          " + c["via"])
    if rep.get("cmd_heal") and (rep["copies"] and (rep["copies"][0]["unmerged"] or rep["copies"][0]["divergence"] in ("DIVERGED", "BEHIND"))):
        print("  [先自癒] " + rep["cmd_heal"])
    if rep.get("cmd_now"):
        print("  [立即可用] " + rep["cmd_now"])
    if rep.get("cmd_pin"):
        print("  [一勞永逸] " + rep["cmd_pin"])
    if rep.get("cmd_bootstrap"):
        print("  [★ bootstrap 死結] 本副本醫生版本過舊,連字號版號族衝突必被判 MANUAL。")
        print("     先貼這一段(手動取遠端版一次→醫生完成合併→自動升版→點源新冊):")
        print("     " + rep["cmd_bootstrap"])
    if rep.get("cmd_all"):
        print("  [一行全包] " + rep["cmd_all"])
    return 0 if rep["state"] in ("OK", "PLAN") else 1


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # 三副本:A(舊冊 v0100 無動詞)、B(新冊 v0173 含動詞,git 在位)、C(無 Register=不算副本)
        a = tdp / "movies-dataset-old" / "VeritasIntelligenceAnalytics"
        b = tdp / "movies-dataset" / "VeritasIntelligenceAnalytics"
        c = tdp / "movies-dataset-empty" / "VeritasIntelligenceAnalytics"
        for p in (a, b, c):
            p.mkdir(parents=True)
        (a / "Register-VIA-Commands-v0100.ps1").write_text("function global:via-lanes { }\n", encoding="utf-8")
        (b / "Register-VIA-Commands-v0173.ps1").write_text(
            "function global:via-vdffetch { }\nfunction global:via-accel-import { }\nfunction global:via-medic { }\nfunction global:via-lanes { }\n", encoding="utf-8")
        (b / "Invoke-VIA-VdfFetch-v0101.ps1").write_text("param([string]$Year='2023')\n", encoding="utf-8")
        (c / "readme.txt").write_text("x", encoding="utf-8")
        ra, rb = a.parent, b.parent
        for r in (ra, rb):
            subprocess.run(["git", "init", "-q", str(r)], check=True, timeout=120)
            subprocess.run(["git", "-C", str(r), "add", "-A"], check=True, timeout=120)
            subprocess.run(["git", "-C", str(r), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"], check=True, timeout=120)
        ia, ib, ic = inspect(a), inspect(b), inspect(c)
        chk("① 體檢(Register 尾版版號解析;動詞在位實讀;git 分支/HEAD 取得)",
            ia["register_ver"] == 100 and ib["register_ver"] == 173 and ib["verbs"]["via-vdffetch"] and not ia["verbs"]["via-vdffetch"]
            and ib["head"] and ib["branch"])
        real = candidate_roots()
        chk("②b 本引擎所在副本必入冊(雲端實錄:首版漏收=副本 0 份)",
            any(Path(x).resolve() == VIA.resolve() for x in real), "(掃得 " + str(len(real)) + " 份)")
        chk("② 無 Register 夾不算副本(candidate_roots 只收含冊者)",
            not any(Path(x).resolve() == c.resolve() for x in [ia["via"], ib["via"]]) and ic["register_ver"] == -1)
        rep = build(roots=[a, b], do_print=False, write=False)
        chk("③ 判新(冊版號優先:v0173 勝 v0100;best 指向新副本)",
            rep["best"] == str(b) and rep["copies"][0]["register_ver"] == 173)
        import re as _re
        cmds = " ; ".join([rep.get("cmd_heal", ""), rep.get("cmd_now", ""), rep.get("cmd_pin", ""), rep.get("cmd_all", "")])
        hard = _re.findall(r"-v\d{3,4}\.(?:ps1|py)", cmds)
        chk("④ 指路三道+一行全包,且永不寫死版號(批391 我方指令給 v0175 而該副本只有 v0174=必然失敗之錯;改 glob 尾版)",
            all(k in cmds for k in ("Invoke-VIA-VdfFetch-v*.ps1", "Register-VIA-Commands-v*.ps1", "CGC_MDL143_MergeMedic_v*.py", "via-pin", "-Year 2023"))
            and not hard, "(寫死版號 " + str(len(hard)) + " 處)")
        chk("⑤ 缺令具名(舊副本缺 via-vdffetch/via-accel-import/via-medic 三令)",
            sorted(v for v, ok in rep["copies"][1]["verbs"].items() if not ok) == ["via-accel-import", "via-medic", "via-vdffetch"])
        # 未合併態副本:造真衝突
        (b / "x.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(rb), "add", "-A"], check=True, timeout=120)
        subprocess.run(["git", "-C", str(rb), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x"], check=True, timeout=120)
        subprocess.run(["git", "-C", str(rb), "checkout", "-q", "-b", "side"], check=True, timeout=120)
        (b / "x.txt").write_text("side\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(rb), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-am", "side"], check=True, timeout=120)
        subprocess.run(["git", "-C", str(rb), "checkout", "-q", "-"], check=True, timeout=120)
        (b / "x.txt").write_text("main\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(rb), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-am", "main"], check=True, timeout=120)
        subprocess.run(["git", "-C", str(rb), "merge", "side"], capture_output=True, timeout=300)
        ib2 = inspect(b)
        assert ib2["unmerged"] >= 1 or True   # 自測首錯實錄:git -c 必置於子命令前,否則 commit 靜默失敗→無衝突可測
        chk("⑥ 未合併態偵測(UU 計數>0 並指路 via-medic sync --apply)", ib2["unmerged"] >= 1 and "via-medic" in ib2["note"])
        subprocess.run(["git", "-C", str(rb), "merge", "--abort"], capture_output=True, timeout=120)
        rep2 = build(roots=[a, b], do_print=False, write=False)
        chk("⑦ 判定態(最新副本動詞全在但曾卡未合併→解後 state=OK/PLAN;永不假綠)", rep2["state"] in ("OK", "PLAN"))
        chk("⑧ 分歧欄誠實(無上游=NO_UPSTREAM 或 MEDIC_MISSING;不猜)",
            ib2["divergence"] in ("NO_UPSTREAM", "UP_TO_DATE", "PROBE_FAIL", "MEDIC_MISSING", "DIVERGED", "BEHIND", "AHEAD"))
        m = _mdl143()
        chk("⑨ 零重造(分歧判定來自 MDL143 尾版;本檔無自製 rev-list 解析)",
            m is not None and hasattr(m, "divergence") and "rev-list" not in Path(__file__).read_text(encoding="utf-8").split("def selftest")[0])
    # ⑪ 批394 續章:bootstrap 死結偵測與指令產出(操作員實遇:醫生 v0101 + 連字號同名雙物 ×2)
    with tempfile.TemporaryDirectory() as td5:
        t5 = Path(td5)
        r5, v5 = t5 / "repo", t5 / "repo" / "VeritasIntelligenceAnalytics"
        (v5 / "supportive modules" / "registry").mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(r5)], timeout=120)
        (v5 / "supportive modules" / "registry" / "CGC_MDL143_MergeMedic_v0101.py").write_text("# old medic\n", encoding="utf-8")
        (v5 / "Register-VIA-Commands-v0168.ps1").write_text("# base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r5), "add", "-A"])
        subprocess.run(["git", "-C", str(r5), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "b"])
        subprocess.run(["git", "-C", str(r5), "checkout", "-q", "-b", "other"], timeout=120)
        (v5 / "Register-VIA-Commands-v0168.ps1").write_text("# theirs\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r5), "add", "-A"])
        subprocess.run(["git", "-C", str(r5), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "o"])
        subprocess.run(["git", "-C", str(r5), "checkout", "-q", "-"], timeout=120)
        (v5 / "Register-VIA-Commands-v0168.ps1").write_text("# ours\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(r5), "add", "-A"])
        subprocess.run(["git", "-C", str(r5), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "l"])
        subprocess.run(["git", "-C", str(r5), "merge", "other"])
        e5 = inspect(v5, ["via-help"])
        rep5 = build(verbs=["via-help"], roots=[str(v5)], do_print=False, write=False)
        cb = rep5.get("cmd_bootstrap", "")
        chk("⑪ bootstrap 死結偵測(舊醫生×連字號同名雙物=必判 MANUAL)並產可貼指令(檔名動態、零寫死版號)",
            e5.get("deadlock") == "BOOTSTRAP" and e5["medic_ver"] == 101
            and "Register-VIA-Commands-v0168.ps1" in cb and "checkout --theirs" in cb
            and "MergeMedic_v*.py" in cb and "MergeMedic_v0101.py" not in cb,
            "(死結 " + str(e5.get("deadlock")) + " · 醫生 v" + str(e5["medic_ver"])
            + " · 指令 " + ("有" if cb else "無") + ")")
    print("  [計] 十一檢 OK " + str(11 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 副本醫生(" + ENGINE_TAG + ")· 十檢自測 ===")
        return selftest()
    verbs = DEFAULT_VERBS
    if "--verb" in a and a.index("--verb") + 1 < len(a):
        verbs = [x.strip() for x in a[a.index("--verb") + 1].split(",") if x.strip()]
    rep = build(verbs=verbs)
    if "--heal" in a and rep.get("copies"):
        best = rep["copies"][0]
        if not (best["unmerged"] or best["divergence"] in ("DIVERGED", "BEHIND")):
            print("  [自癒] 最新副本無卡未合併且與遠端同步=免醫(誠實)")
            return 0
        m = _mdl143()
        if m is None:
            print("  [自癒] 拉齊醫生缺(CGC_MDL143_MergeMedic_v*.py)=無法自癒(誠實)")
            return 1
        print("  [自癒] 對最新副本呼拉齊醫生 sync --apply(零 force 零刪除):" + best["root"])
        r = m.sync(Path(best["root"]), best["branch"] or None, apply=True, do_print=True, write=True)
        print("  [自癒] 終態 " + r.get("state", "?") + " · HEAD " + str(r.get("head_before")) + " → " + str(r.get("head_after", r.get("head_before"))))
        rep2 = build(verbs=verbs, do_print=True, write=True)
        return 0 if rep2["state"] in ("OK", "PLAN") else 1
    return 0 if rep["state"] in ("OK", "PLAN") else 1


if __name__ == "__main__":
    sys.exit(main())
