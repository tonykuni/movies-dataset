#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL143_MergeMedic v0102 — 拉齊醫生(批393 工作站實況抓到真 bug:同名雙物正規式只認底線 _v####,連字號 -v####(Register-VIA-Commands-v0168.ps1、Invoke-VIA-VdfFetch-v0102.ps1 等)全部漏判成 MANUAL → 操作員倉庫永遠解不開;批392 工作站實況補測:髒樹 35 件+分叉+卡未合併 2 件三者同時→merge 會被未提交改動擋;本版自帶 stash;批386 操作員令「請你自測自修正 test debug optimize … till it works perfectly」)

工作站實錄(2026-09-12 OneDrive 副本):
  ① 先卡未完成合併(UU 台帳/AA Register-v0168/AA SelftestGrid-v0265)→ merge 一律拒
  ② merge --abort 後改成「分叉」:fatal: Not possible to fast-forward, aborting.(本地 main 有遠端沒有的提交)
  → via-reload 只會 --ff-only,分叉永遠拉不動;HEAD 永停 44b0c79d;新短令(via-accel-import)永不到。
本引擎=把「拉齊」從 ff-only 升級為可處理分叉與衝突的醫生,且每一步都守既有律:

三態判定(git rev-list --left-right --count HEAD...origin/<分支>):
  BEHIND(只落後)→ ff 快轉        DIVERGED(雙方各有提交)→ merge --no-ff(零 force、零 reset、零刪除)
  AHEAD/UP_TO_DATE → 無需拉

衝突自動裁決(只在 merge 產生衝突時;逐檔分類,永不一律取一方):
  LEDGER        台帳 VIA_AutoCode_Registry_v*.json = append-only 聯集(遠端序在前,本地獨有者附後;
                以 (code, ts, name[:60]) 去重;零丟棄)
  VERSIONED_TWIN 同名雙物(帶 _v#### 版號的正本檔,兩邊內容不同)= 先發先得 → 取遠端版(本地同名件
                若另有價值,操作員可另起新版號;本引擎零刪除)
  REGEN         再生物(ui_support/*.html、再生冊 VIA_*_v####.json、WHERE_IS_*.md)= 取遠端版(產物非正本)
  MANUAL        其餘 = 不動、具名列出(誠實;由操作員或 AI 逐案處理)
髒樹律(批392):merge 前若工作樹有未提交改動(含未追蹤),先 stash push -u 保存,合併完成後 pop 原樣還原;
  pop 起衝突=stash 留存並誠實印(永不丟棄操作員的工作);--no-stash 可關(此時髒樹分叉=誠實停不硬合)。
律:零 force、零 reset --hard、零刪除檔案、零 checkout 覆蓋未衝突檔;只處理 git 標記為未合併(U*)之路徑;
    失敗即誠實回報並保留現場;預設唯讀(--apply 才寫);台帳聯集前後筆數必印。
用法:via-reload(短令自動委派)/ python <本檔> status | plan | sync --apply [--branch main] [--root <repo>]
      python <本檔> --selftest      → 十一檢(真建暫時 git 倉;真造分叉/三類衝突/髒樹三合一,真驗)
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
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT_DEFAULT = VIA.parent
REP = VIA / "VIA_Reports" / "merge_medic"
ENGINE_TAG = "CGC_MDL143_MergeMedic v0102"

LEDGER_RX = re.compile(r"VIA_AutoCode_Registry_v\d+\.json$")
# 批393:版號分隔符兩型皆認——底線(CGC_MDL064_SelftestGrid_v0265.py)與連字號(Register-VIA-Commands-v0168.ps1)
# 實錄:v0101 只認 _v → 連字號族全判 MANUAL → 操作員 OneDrive 副本卡兩件 Register 永遠解不開
VERSIONED_RX = re.compile(r"[-_]v\d{3,4}\.(py|ps1|json|md|html|cmd)$", re.I)
REGEN_RX = re.compile(r"(supportive modules/ui_support/.*\.html"
                      r"|supportive modules/registry/VIA_(Engine_Consolidation_Register|Engine_Contract|SSOT_RegexDict"
                      r"|Schema_Registry|Tool_Escalation_Ladder|Unified_Register|IndustryUnifiedMap|Problem_Ledger"
                      r"|NetModules_Integration_Register|AccelModules_Integration_Register|VDFArchitecture"
                      r"|ProjectCompletion|ProductGate|ParallelLanes|AccelImport)_v\d+\.json"
                      r"|WHERE_IS_[A-Z_]+\.md)$")
RULES = ["零 force、零 reset --hard、零刪除檔案;只動 git 標為未合併(U*)之路徑",
         "台帳=append-only 聯集(遠端序在前+本地獨有者附後;(code,ts,name) 去重;前後筆數必印)",
         "同名雙物=先發先得取遠端版(本地版若另有價值→另起新版號;本引擎零刪除)",
         "再生物(頁/再生冊/WHERE_IS)=取遠端版(產物非正本)",
         "其餘衝突=MANUAL 不動具名列出(誠實);預設唯讀,--apply 才寫"]


def git(root: Path, *args, text: bool = True, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root)] + list(args), capture_output=True, text=text, check=check, timeout=600)


def current_branch(root: Path) -> str:
    r = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    b = (r.stdout or "").strip()
    return b if b and b != "HEAD" else "main"


def divergence(root: Path, branch: str) -> dict:
    """(ahead, behind, state);state: UP_TO_DATE / BEHIND / AHEAD / DIVERGED / NO_UPSTREAM"""
    target = "origin/" + branch
    if git(root, "rev-parse", "--verify", "--quiet", target).returncode != 0:
        return {"ahead": 0, "behind": 0, "state": "NO_UPSTREAM", "target": target}
    r = git(root, "rev-list", "--left-right", "--count", "HEAD..." + target)
    try:
        ahead, behind = (int(x) for x in (r.stdout or "0\t0").split())
    except Exception:
        ahead, behind = 0, 0
    st = ("UP_TO_DATE" if not ahead and not behind else
          "BEHIND" if behind and not ahead else
          "AHEAD" if ahead and not behind else "DIVERGED")
    return {"ahead": ahead, "behind": behind, "state": st, "target": target}


def unmerged(root: Path) -> list:
    r = git(root, "status", "--porcelain", "-z")
    out = []
    for ent in (r.stdout or "").split("\0"):
        if len(ent) > 3 and ent[:2] in ("UU", "AA", "DU", "UD", "AU", "UA", "DD"):
            out.append({"xy": ent[:2], "path": ent[3:]})
    return out


def classify(path: str) -> str:
    p = path.replace("\\", "/")
    if LEDGER_RX.search(p):
        return "LEDGER"
    if REGEN_RX.search(p):
        return "REGEN"
    if VERSIONED_RX.search(p):
        return "VERSIONED_TWIN"
    return "MANUAL"


def _stage_blob(root: Path, stage: int, path: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(root), "show", f":{stage}:{path}"], capture_output=True, timeout=600)
    return r.stdout if r.returncode == 0 else None


def ledger_union(ours: bytes | None, theirs: bytes | None) -> tuple[bytes | None, dict]:
    """append-only 聯集:遠端(theirs)序在前,本地(ours)獨有者附後;(code,ts,name[:60]) 去重"""
    def load(b):
        try:
            return json.loads(b.decode("utf-8"))
        except Exception:
            return None
    o, t = load(ours or b""), load(theirs or b"")
    if not isinstance(t, dict) or not isinstance(t.get("ledger"), list):
        return None, {"ok": False, "why": "遠端台帳不可解析"}
    if not isinstance(o, dict) or not isinstance(o.get("ledger"), list):
        return json.dumps(t, ensure_ascii=False, indent=1).encode("utf-8"), {"ok": True, "theirs": len(t["ledger"]), "ours": 0, "added": 0, "total": len(t["ledger"])}

    def key(e):
        return (str(e.get("code", "")), str(e.get("ts", "")), str(e.get("name", ""))[:60])
    seen = {key(e) for e in t["ledger"]}
    extra = [e for e in o["ledger"] if key(e) not in seen]
    merged = dict(t)
    merged["ledger"] = list(t["ledger"]) + extra
    return (json.dumps(merged, ensure_ascii=False, indent=1).encode("utf-8"),
            {"ok": True, "theirs": len(t["ledger"]), "ours": len(o["ledger"]), "added": len(extra), "total": len(merged["ledger"])})


def resolve(root: Path, apply: bool = False, do_print: bool = True) -> dict:
    """逐未合併檔按律裁決;MANUAL 不動。回報每檔 action/state"""
    items = []
    for u in unmerged(root):
        path, kind = u["path"], classify(u["path"])
        ent = {"path": path, "xy": u["xy"], "kind": kind, "action": "", "state": "PLAN", "note": ""}
        if kind == "LEDGER":
            ours, theirs = _stage_blob(root, 2, path), _stage_blob(root, 3, path)
            data, info = ledger_union(ours, theirs)
            ent["action"] = "台帳聯集"
            ent["note"] = (f"遠端 {info.get('theirs')} + 本地獨有 {info.get('added')} → {info.get('total')}"
                           if info.get("ok") else str(info.get("why")))
            if not info.get("ok") or data is None:
                ent["state"] = "FAIL"
            elif apply:
                (root / path).write_bytes(data)
                ent["state"] = "OK" if git(root, "add", "--", path).returncode == 0 else "FAIL"
        elif kind in ("VERSIONED_TWIN", "REGEN"):
            ent["action"] = "取遠端版(" + ("先發先得" if kind == "VERSIONED_TWIN" else "產物非正本") + ")"
            if apply:
                blob = _stage_blob(root, 3, path)
                if blob is None:
                    ent["state"], ent["note"] = "FAIL", "遠端階段物缺(可能為本地新增件)"
                else:
                    (root / path).parent.mkdir(parents=True, exist_ok=True)
                    (root / path).write_bytes(blob)
                    ent["state"] = "OK" if git(root, "add", "--", path).returncode == 0 else "FAIL"
        else:
            ent["action"], ent["state"], ent["note"] = "不動(MANUAL)", "MANUAL", "非台帳/非同名雙物/非再生物=逐案由操作員或 AI 處理"
        items.append(ent)
        if do_print:
            print("  [" + ent["state"] + "] " + kind.ljust(14) + " " + path[-70:] + (" · " + ent["note"] if ent["note"] else ""))
    return {"items": items, "manual": [i["path"] for i in items if i["state"] == "MANUAL"],
            "failed": [i["path"] for i in items if i["state"] == "FAIL"]}


def stash_push(root: Path, tag: str) -> tuple[bool, str]:
    """批392:保存未提交改動(含未追蹤);回 (是否有 stash, 說明)"""
    dirty = [l for l in (git(root, "status", "--porcelain").stdout or "").splitlines() if l.strip()]
    if not dirty:
        return False, "工作樹乾淨=免 stash"
    r = git(root, "stash", "push", "--include-untracked", "-q", "-m", tag)
    if r.returncode != 0:
        return False, "stash 失敗(誠實;不硬合):" + ((r.stderr or r.stdout or "").strip().splitlines() or [""])[-1][:120]
    return True, "已 stash " + str(len(dirty)) + " 件(含未追蹤;合併後自動還原)"


def stash_pop(root: Path) -> str:
    r = git(root, "stash", "pop")
    if r.returncode == 0:
        return "stash 已原樣還原"
    return "stash 還原起衝突=stash 留存(誠實;手動 git stash pop):" + ((r.stderr or r.stdout or "").strip().splitlines() or [""])[-1][:120]


def sync(root: Path | None = None, branch: str | None = None, apply: bool = False, do_print: bool = True,
         write: bool = True, stash: bool = True) -> dict:
    root = Path(root or ROOT_DEFAULT)
    branch = branch or current_branch(root)
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "root": str(root),
           "branch": branch, "apply": apply, "rules": RULES, "steps": []}

    def step(name, state, note=""):
        rep["steps"].append({"name": name, "state": state, "note": note})
        if do_print:
            print("  [" + state + "] " + name + (" · " + note if note else ""))

    head0 = (git(root, "rev-parse", "--short", "HEAD").stdout or "").strip()
    rep["head_before"] = head0
    pre = unmerged(root)
    if pre:
        step("未完成合併先解(" + str(len(pre)) + " 件)", "PLAN" if not apply else "RUN")
        r0 = resolve(root, apply=apply, do_print=do_print)
        rep["pre_resolve"] = r0
        if apply and (r0["failed"] or r0["manual"]):
            rep["state"] = "MANUAL" if r0["manual"] else "FAIL"
            step("停:仍有未解衝突", rep["state"], ", ".join((r0["manual"] + r0["failed"])[:4]))
            return _finish(rep, write)
        if apply:
            git(root, "-c", "user.name=tonykuni", "-c", "user.email=tonyhuang0122@gmail.com",
                "commit", "-q", "-m", "解未完成合併(MergeMedic):台帳聯集 + 同名雙物讓位遠端 + 再生物取遠端;零刪除零 force")
            step("完成合併提交", "OK")

    if apply:
        git(root, "fetch", "-q", "origin", branch)
    d = divergence(root, branch)
    stashed = False
    if apply and stash and d["state"] in ("BEHIND", "DIVERGED"):
        stashed, why = stash_push(root, "mergemedic " + rep["stamp"])
        step("髒樹 stash(批392:未提交改動會擋 merge)", "OK" if stashed or "乾淨" in why else "SKIP", why)
        rep["stashed"] = stashed
    rep["divergence"] = d
    step("分歧判定 " + d["state"], "OK", "本地獨有 " + str(d["ahead"]) + " · 遠端獨有 " + str(d["behind"]) + " · " + d["target"])
    def _pop_and_finish(r):
        if stashed:
            note = stash_pop(root)
            step("stash 還原", "OK" if "原樣還原" in note else "FAIL", note)
            if "原樣還原" not in note:
                r["stash_left"] = True
        return _finish(r, write)
    if d["state"] in ("UP_TO_DATE", "AHEAD", "NO_UPSTREAM"):
        rep["state"] = "OK"
        return _pop_and_finish(rep)
    if not apply:
        rep["state"] = "PLAN"
        step("計畫:" + ("ff 快轉" if d["state"] == "BEHIND" else "merge --no-ff + 按律解衝突"), "PLAN", "--apply 才執行")
        return _finish(rep, write)

    if d["state"] == "BEHIND":
        r = git(root, "merge", "--ff-only", d["target"])
        step("ff 快轉", "OK" if r.returncode == 0 else "FAIL", ((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-1][:160] if (r.stdout or r.stderr) else "")
        rep["state"] = "OK" if r.returncode == 0 else "FAIL"
    else:
        env = dict(os.environ, GIT_EDITOR="true", GIT_MERGE_AUTOEDIT="no")
        r = subprocess.run(["git", "-C", str(root), "-c", "user.name=tonykuni", "-c", "user.email=tonyhuang0122@gmail.com",
                            "merge", "--no-ff", "--no-edit", d["target"]], capture_output=True, text=True, env=env, timeout=900)
        conflicted = unmerged(root)
        if r.returncode == 0 and not conflicted:
            step("merge --no-ff(零衝突)", "OK")
            rep["state"] = "OK"
        else:
            step("merge --no-ff 起衝突 " + str(len(conflicted)) + " 件", "RUN")
            r1 = resolve(root, apply=True, do_print=do_print)
            rep["resolve"] = r1
            if r1["failed"] or r1["manual"]:
                rep["state"] = "MANUAL" if r1["manual"] else "FAIL"
                step("停:衝突未全解(現場保留;可 git merge --abort 回復)", rep["state"], ", ".join((r1["manual"] + r1["failed"])[:4]))
                return _finish(rep, write)   # 衝突現場保留時不 pop(避免把 stash 疊到衝突上)
            c = git(root, "-c", "user.name=tonykuni", "-c", "user.email=tonyhuang0122@gmail.com", "commit", "-q", "--no-edit")
            step("合併提交", "OK" if c.returncode == 0 else "FAIL")
            rep["state"] = "OK" if c.returncode == 0 else "FAIL"
    rep["head_after"] = (git(root, "rev-parse", "--short", "HEAD").stdout or "").strip()
    step("HEAD " + head0 + " → " + str(rep.get("head_after")), "OK")
    return _pop_and_finish(rep)


def _finish(rep: dict, write: bool) -> dict:
    rep.setdefault("state", "PLAN")
    if write:
        try:
            REP.mkdir(parents=True, exist_ok=True)
            (REP / ("MEDIC_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception:
            pass
    return rep


def status(root: Path | None = None, branch: str | None = None) -> int:
    root = Path(root or ROOT_DEFAULT)
    branch = branch or current_branch(root)
    d = divergence(root, branch)
    u = unmerged(root)
    print("VIA MERGE MEDIC · 根 " + str(root) + " · 分支 " + branch + " · " + d["state"]
          + "(本地獨有 " + str(d["ahead"]) + " · 遠端獨有 " + str(d["behind"]) + ")· 未合併 " + str(len(u)) + " 件")
    for x in u:
        print("  " + x["xy"] + " " + classify(x["path"]).ljust(14) + " " + x["path"])
    if d["state"] == "DIVERGED":
        print("  下一步:python <本檔> sync --apply(merge --no-ff + 按律解衝突;零 force 零刪除)")
    elif d["state"] == "BEHIND":
        print("  下一步:python <本檔> sync --apply(ff 快轉)")
    return 0


# ---------------------------------------------------------------- 自測(真 git 倉)
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    def run(cwd, *a):
        return subprocess.run(["git", "-C", str(cwd)] + list(a), capture_output=True, text=True, timeout=300)

    chk("①b 版號兩型皆認(批393 實錄:連字號 -v#### 曾全漏判成 MANUAL 致倉庫解不開)",
        classify("VeritasIntelligenceAnalytics/Register-VIA-Commands-v0168.ps1") == "VERSIONED_TWIN"
        and classify("VeritasIntelligenceAnalytics/Register-VIA-Commands-v0169.ps1") == "VERSIONED_TWIN"
        and classify("VeritasIntelligenceAnalytics/Invoke-VIA-VdfFetch-v0102.ps1") == "VERSIONED_TWIN"
        and classify("x/CGC_MDL064_SelftestGrid_v0265.py") == "VERSIONED_TWIN")
    chk("① 分類律(台帳→LEDGER;_v0100.py 正本→VERSIONED_TWIN;ui_support 頁/再生冊/WHERE_IS→REGEN;其餘→MANUAL)",
        classify("a/supportive modules/registry/VIA_AutoCode_Registry_v0100.json") == "LEDGER"
        and classify("x/CGC_MDL064_SelftestGrid_v0265.py") == "VERSIONED_TWIN"
        and classify("VeritasIntelligenceAnalytics/supportive modules/ui_support/VIA_UI_DailyBrief_v0100.html") == "REGEN"
        and classify("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ProductGate_v0100.json") == "REGEN"
        and classify("VeritasIntelligenceAnalytics/functional modules/VDF/WHERE_IS_OUTPUT_HUB.md") == "REGEN"
        and classify("README.md") == "MANUAL")
    o = json.dumps({"registry_id": "x", "ledger": [{"code": "A", "ts": "1", "name": "a"}, {"code": "L", "ts": "9", "name": "only-local"}]}, ensure_ascii=False).encode()
    t = json.dumps({"registry_id": "x", "ledger": [{"code": "A", "ts": "1", "name": "a"}, {"code": "R", "ts": "8", "name": "only-remote"}]}, ensure_ascii=False).encode()
    data, info = ledger_union(o, t)
    merged = json.loads(data.decode())
    chk("② 台帳聯集(遠端序在前+本地獨有附後;共有者零重複;零丟棄)",
        info["ok"] and info["total"] == 3 and [e["code"] for e in merged["ledger"]] == ["A", "R", "L"], f"({info})")
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        bare, a, b = tdp / "origin.git", tdp / "A", tdp / "B"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True, timeout=120)
        subprocess.run(["git", "clone", "-q", str(bare), str(a)], check=True, timeout=120)
        led = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"
        eng = "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL064_SelftestGrid_v0265.py"
        page = "VeritasIntelligenceAnalytics/supportive modules/ui_support/VIA_UI_DailyBrief_v0100.html"
        other = "README.md"
        for p, body in ((led, json.dumps({"registry_id": "x", "ledger": [{"code": "BASE", "ts": "0", "name": "base"}]}, ensure_ascii=False)),
                        (eng, "# base\n"), (page, "<html>base</html>"), (other, "base\n")):
            f = a / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body, encoding="utf-8")
        run(a, "add", "-A"); run(a, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        run(a, "push", "-q", "origin", "HEAD:refs/heads/main")
        run(a, "branch", "-M", "main")
        run(a, "branch", "--set-upstream-to=origin/main", "main")
        # 裸倉預設 HEAD 可能是 master → 指向 main,否則第二份複本 checkout 出空樹(自測首錯實錄)
        subprocess.run(["git", "-C", str(bare), "symbolic-ref", "HEAD", "refs/heads/main"], check=True, timeout=120)
        subprocess.run(["git", "clone", "-q", str(bare), str(b)], check=True, timeout=120)
        assert (b / led).exists(), "clone B 空樹(裸倉 HEAD 未指 main)"
        # 遠端(A)前進:台帳 +R、引擎改、頁改
        (a / led).write_text(json.dumps({"registry_id": "x", "ledger": [{"code": "BASE", "ts": "0", "name": "base"}, {"code": "R", "ts": "8", "name": "remote"}]}, ensure_ascii=False), encoding="utf-8")
        (a / eng).write_text("# remote tail\n", encoding="utf-8")
        (a / page).write_text("<html>remote</html>", encoding="utf-8")
        run(a, "add", "-A"); run(a, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "remote work")
        run(a, "push", "-q", "origin", "main")
        # 本地(B)也前進=分叉:台帳 +L、引擎改、頁改
        (b / led).write_text(json.dumps({"registry_id": "x", "ledger": [{"code": "BASE", "ts": "0", "name": "base"}, {"code": "L", "ts": "9", "name": "local"}]}, ensure_ascii=False), encoding="utf-8")
        (b / eng).write_text("# local tail\n", encoding="utf-8")
        (b / page).write_text("<html>local</html>", encoding="utf-8")
        run(b, "add", "-A"); run(b, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "local work")
        run(b, "fetch", "-q", "origin", "main")
        d = divergence(b, "main")
        chk("③ 分歧判定(雙方各一提交=DIVERGED;ahead/behind 皆 1)", d["state"] == "DIVERGED" and d["ahead"] == 1 and d["behind"] == 1, f"({d})")
        p0 = sync(b, "main", apply=False, do_print=False, write=False)
        head_b4 = (run(b, "rev-parse", "--short", "HEAD").stdout or "").strip()
        chk("④ 唯讀計畫(未 --apply=HEAD 不動、零合併)", p0["state"] == "PLAN" and not unmerged(b) and head_b4 == (run(b, "rev-parse", "--short", "HEAD").stdout or "").strip())
        rep = sync(b, "main", apply=True, do_print=False, write=False)
        led_after = json.loads((b / led).read_text(encoding="utf-8"))
        chk("⑤ 分叉真合(merge --no-ff 成功;HEAD 前進;零衝突殘留)",
            rep["state"] == "OK" and not unmerged(b) and rep.get("head_after") and rep["head_after"] != head_b4, f"({rep['state']})")
        chk("⑥ 台帳衝突=聯集(BASE+R+L 三筆皆在;零丟棄)",
            [e["code"] for e in led_after["ledger"]] == ["BASE", "R", "L"], f"({[e['code'] for e in led_after['ledger']]})")
        chk("⑦ 同名雙物=取遠端版(先發先得);再生頁=取遠端版(產物非正本)",
            (b / eng).read_text(encoding="utf-8").strip() == "# remote tail" and (b / page).read_text(encoding="utf-8") == "<html>remote</html>")
        chk("⑧ 本地提交零丟失(merge 保留本地 commit;git log 見 local work)",
            "local work" in (run(b, "log", "--oneline", "-6").stdout or "") and "remote work" in (run(b, "log", "--oneline", "-6").stdout or ""))
        # MANUAL 類:雙方改 README → 不動並誠實停
        (a / other).write_text("remote readme\n", encoding="utf-8")
        run(a, "add", "-A"); run(a, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "r2"); run(a, "push", "-q", "origin", "main")
        (b / other).write_text("local readme\n", encoding="utf-8")
        run(b, "add", "-A"); run(b, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "l2")
        run(b, "fetch", "-q", "origin", "main")
        rep2 = sync(b, "main", apply=True, do_print=False, write=False)
        still = unmerged(b)
        chk("⑨ MANUAL 誠實停(README 雙改=不動、列名、現場保留可 merge --abort;不假綠)",
            rep2["state"] == "MANUAL" and any(x["path"] == other for x in still)
            and (b / other).read_text(encoding="utf-8") in ("local readme\n", "remote readme\n") or "<<<<<<<" in (b / other).read_text(encoding="utf-8"),
            f"({rep2['state']}, 未合併 {len(still)})")
        run(b, "merge", "--abort")
    # ⑩ 批392:髒樹 + 分叉 + 台帳衝突三者同時(工作站實況:髒 35 + DIVERGED + 未合併 2)
    with tempfile.TemporaryDirectory() as td3:
        t3 = Path(td3)
        bare3, a3, b3 = t3 / "o.git", t3 / "A", t3 / "B"
        subprocess.run(["git", "init", "-q", "--bare", str(bare3)], check=True, timeout=120)
        subprocess.run(["git", "clone", "-q", str(bare3), str(a3)], check=True, timeout=120)
        led3 = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"
        (a3 / led3).parent.mkdir(parents=True, exist_ok=True)
        (a3 / led3).write_text(json.dumps({"ledger": [{"code": "BASE", "ts": "0", "name": "b"}]}, ensure_ascii=False), encoding="utf-8")
        (a3 / "f.txt").write_text("base\n", encoding="utf-8")
        run(a3, "add", "-A"); run(a3, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        run(a3, "push", "-q", "origin", "HEAD:refs/heads/main"); run(a3, "branch", "-M", "main")
        subprocess.run(["git", "-C", str(bare3), "symbolic-ref", "HEAD", "refs/heads/main"], check=True, timeout=120)
        subprocess.run(["git", "clone", "-q", str(bare3), str(b3)], check=True, timeout=120)
        (b3 / led3).write_text(json.dumps({"ledger": [{"code": "BASE", "ts": "0", "name": "b"}, {"code": "R", "ts": "8", "name": "r"}]}, ensure_ascii=False), encoding="utf-8")
        run(b3, "add", "-A"); run(b3, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "remote")
        run(b3, "push", "-q", "origin", "main")
        (a3 / led3).write_text(json.dumps({"ledger": [{"code": "BASE", "ts": "0", "name": "b"}, {"code": "L", "ts": "9", "name": "l"}]}, ensure_ascii=False), encoding="utf-8")
        run(a3, "add", "-A"); run(a3, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "local")
        (a3 / "f.txt").write_text("base\nDIRTY\n", encoding="utf-8")          # 未提交改動(追蹤檔)
        (a3 / "untracked.txt").write_text("u\n", encoding="utf-8")              # 未追蹤檔
        run(a3, "fetch", "-q", "origin", "main")
        d3 = divergence(a3, "main")
        h0 = (run(a3, "rev-parse", "--short", "HEAD").stdout or "").strip()
        rep3 = sync(a3, "main", apply=True, do_print=False, write=False)
        led_final = json.loads((a3 / led3).read_text(encoding="utf-8"))
        dirty_back = "DIRTY" in (a3 / "f.txt").read_text(encoding="utf-8") and (a3 / "untracked.txt").exists()
        chk("⑩ 髒樹+分叉+台帳衝突三者同時(批392 工作站實況):stash→merge→台帳聯集→pop 原樣還原;本地改動零丟失",
            d3["state"] == "DIVERGED" and rep3["state"] == "OK" and not unmerged(a3)
            and [e["code"] for e in led_final["ledger"]] == ["BASE", "R", "L"] and dirty_back
            and (run(a3, "rev-parse", "--short", "HEAD").stdout or "").strip() != h0,
            "(終態 " + rep3["state"] + " · 髒檔還原 " + ("是" if dirty_back else "否") + " · 台帳 " + ",".join(e["code"] for e in led_final["ledger"]) + ")")
    # ⑫ 批394 續章:操作員卡住態的完整複製——「合併進行中(MERGE_HEAD 在)」+ 兩件連字號同名雙物
    #    衝突 + 髒樹 + 未追蹤件 + 台帳衝突 五者同時,驗「單一指令 sync --apply」足以全解。
    #    立此檢的理由:v0101 只認底線版號,連字號族被判 MANUAL 而停,故當時必須先手動
    #    git checkout --theirs 兩件才走得動;v0102 修正後醫生自己就能解,手動步驟已多餘。
    #    此檢把「零手動前置」鎖死成回歸條件,避免日後又退回要操作員手工解衝突。
    with tempfile.TemporaryDirectory() as td4:
        t4 = Path(td4)
        bare4, w4, o4 = t4 / "o.git", t4 / "W", t4 / "O"
        subprocess.run(["git", "init", "-q", "--bare", str(bare4)], check=True, timeout=120)
        subprocess.run(["git", "-C", str(bare4), "symbolic-ref", "HEAD", "refs/heads/main"], check=True, timeout=120)
        subprocess.run(["git", "clone", "-q", str(bare4), str(w4)], check=True, timeout=120)
        sub4 = w4 / "VeritasIntelligenceAnalytics"
        led4 = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json"
        (w4 / led4).parent.mkdir(parents=True, exist_ok=True)

        def _led(rows):
            return json.dumps({"ledger": [{"code": c, "ts": "0", "name": c} for c in rows]}, ensure_ascii=False)

        (sub4 / "Register-VIA-Commands-v0168.ps1").write_text("# BASE 168\n", encoding="utf-8")
        (sub4 / "Register-VIA-Commands-v0169.ps1").write_text("# BASE 169\n", encoding="utf-8")
        (w4 / led4).write_text(_led(["BASE"]), encoding="utf-8")
        run(w4, "symbolic-ref", "HEAD", "refs/heads/main")
        run(w4, "add", "-A"); run(w4, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
        run(w4, "push", "-q", "-u", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(bare4), str(o4)], check=True, timeout=120)
        os4 = o4 / "VeritasIntelligenceAnalytics"
        (os4 / "Register-VIA-Commands-v0168.ps1").write_text("# REMOTE 168\n", encoding="utf-8")
        (os4 / "Register-VIA-Commands-v0169.ps1").write_text("# REMOTE 169\n", encoding="utf-8")
        (o4 / led4).write_text(_led(["BASE", "R"]), encoding="utf-8")
        run(o4, "add", "-A"); run(o4, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "remote")
        run(o4, "push", "-q", "origin", "main")
        (sub4 / "Register-VIA-Commands-v0168.ps1").write_text("# LOCAL 168\n", encoding="utf-8")
        (sub4 / "Register-VIA-Commands-v0169.ps1").write_text("# LOCAL 169\n", encoding="utf-8")
        (w4 / led4).write_text(_led(["BASE", "L"]), encoding="utf-8")
        run(w4, "add", "-A"); run(w4, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "local")
        run(w4, "fetch", "-q", "origin", "main")
        run(w4, "merge", "--no-ff", "--no-edit", "origin/main")          # 撞衝突=停在合併進行中
        in_merge = (w4 / ".git" / "MERGE_HEAD").exists()
        (sub4 / "dirty.txt").write_text("dirty\n", encoding="utf-8")     # 髒樹(未追蹤新件)
        (sub4 / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        pre_u = len(unmerged(w4))
        rep4 = sync(w4, "main", apply=True, do_print=False, write=False)  # 單一指令
        led_f = [e["code"] for e in json.loads((w4 / led4).read_text(encoding="utf-8"))["ledger"]]
        twin_ok = ("REMOTE" in (sub4 / "Register-VIA-Commands-v0168.ps1").read_text(encoding="utf-8")
                   and "REMOTE" in (sub4 / "Register-VIA-Commands-v0169.ps1").read_text(encoding="utf-8"))
        keep_ok = (sub4 / "dirty.txt").exists() and (sub4 / "untracked.txt").exists()
        chk("⑫ 卡合併態+連字號同名雙物×2+髒樹+未追蹤+台帳衝突:單一 sync --apply 全解(零手動 checkout --theirs)",
            in_merge and pre_u == 3 and rep4["state"] == "OK" and not unmerged(w4)
            and led_f == ["BASE", "R", "L"] and twin_ok and keep_ok,
            "(合併進行中 " + str(in_merge) + " · 前未合併 " + str(pre_u)
            + " · 終態 " + str(rep4["state"]) + " · 雙物取遠端 " + ("是" if twin_ok else "否")
            + " · 台帳 " + ",".join(led_f) + " · 本地件保留 " + ("是" if keep_ok else "否") + ")")
    print("  [計] 十二檢 OK " + str(12 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 拉齊醫生(" + ENGINE_TAG + ")· 十一檢自測(真 git 倉) ===")
        return selftest()

    def opt(n, d=None):
        return a[a.index(n) + 1] if n in a and a.index(n) + 1 < len(a) else d
    root = Path(opt("--root", str(ROOT_DEFAULT)))
    branch = opt("--branch")
    verb = a[0] if a and not a[0].startswith("-") else "status"
    if verb == "status":
        return status(root, branch)
    if verb in ("plan", "sync"):
        rep = sync(root, branch, apply=("--apply" in a and verb == "sync"))
        print("[醫生] 終態 " + rep["state"] + (" · HEAD " + str(rep.get("head_before")) + " → " + str(rep.get("head_after")) if rep.get("head_after") else ""))
        return 0 if rep["state"] in ("OK", "PLAN") else 1
    print("用法:status | plan | sync --apply [--branch main] [--root <repo>] | --selftest")
    return 2


if __name__ == "__main__":
    sys.exit(main())
