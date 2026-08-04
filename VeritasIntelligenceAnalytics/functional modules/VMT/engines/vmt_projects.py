# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Project Auto-Encoder  v1.0   --  資料夾即專案 · [PRJ-###] 自動編碼
----------------------------------------------------------------------------
 定位: 讓「本機資料夾」成為專案的單一真相 (folder-centric SSOT)。
       你在 workspace/ 底下隨手建一個「日本合資案」資料夾, 系統掃到後自動
       重新命名為「[PRJ-001] 日本合資案」, 並在 projects.jsonl 建檔。
       從此這個高辨識度的 [PRJ-001] 成為郵件歸戶與任務歸屬的精準金鑰,
       取代模糊的中文名稱比對。

 為何要編碼: 兩個專案名稱很像 (合資案A / 合資案B) 時, 靠名稱比對會誤判;
       [PRJ-001] 這種 ID 級別對接則零歧義, 且對方回信只要保留歷史主旨,
       編碼幾乎一定還在。

 治理 (與 VMT 一致):
   - 預設 dry-run: 不改任何資料夾名稱、不寫帳本, 只列出「打算怎麼編碼」
   - --commit    : 才實際 rename 資料夾 + 在 projects.jsonl 建檔
   - add-only    : projects.jsonl 只 append; 已編碼資料夾、已建檔編碼一律略過 (冪等)
   - 不刪除      : 只 rename, 從不刪除或搬移你的檔案內容
   - 資料夾內容完全不碰, 只動最外層資料夾名稱
============================================================================
"""
from __future__ import annotations

import os
import re
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vmt_core import (  # noqa: E402
    EngineResult, EventLog, Ledger, Workspace, add_common_args, banner, clip,
    esc, kpi_cards, mode_label, next_serial, now_iso, pill, render_report,
    table, try_open,
)

ENGINE = "vmt_projects"
VERSION = "v1.0"

CODE_RE = re.compile(r"\[PRJ-(\d{3,})\]")
CODED_PREFIX_RE = re.compile(r"^\[PRJ-\d{3,}\]\s*")


def parse_code(text: str) -> str | None:
    """從任意字串 (資料夾名 / 郵件主旨 / 內文) 取出第一個 [PRJ-###]。"""
    m = CODE_RE.search(str(text or ""))
    return "[PRJ-%s]" % m.group(1) if m else None


def strip_code(name: str) -> str:
    return CODED_PREFIX_RE.sub("", str(name or "")).strip()


def load_projects(ws: Workspace) -> dict[str, dict]:
    """code -> 最新一筆專案宣告 (add-only, 取最後一次)。"""
    latest: dict[str, dict] = {}
    for r in Ledger(ws.projects_ledger, False).read():
        if r.get("code"):
            latest[r["code"]] = r
    return latest


def resolve_project(text: str, ws: Workspace) -> str | None:
    """
    把一段文字歸到某個專案 code。優先用 [PRJ-###] 精準比對;
    找不到編碼時, 才退回用專案名稱做子字串比對 (話題漂移偵測會用到)。
    """
    projects = load_projects(ws)
    code = parse_code(text)
    if code and code in projects:
        return code
    blob = str(text or "")
    for code, p in projects.items():
        name = p.get("name") or ""
        if name and len(name) >= 2 and name in blob:
            return code
    return None


# ---------------------------------------------------------------- 編碼 ------


def scan(ws: Workspace) -> dict:
    """
    掃描 workspace/ , 分類出: 已編碼、待編碼 (將分配的號碼)、以及帳本裡有但資料夾已不在的。
    純讀, 不改任何東西 —— dry-run 與 commit 共用同一份計畫。
    """
    root = ws.workspace
    root.mkdir(parents=True, exist_ok=True)
    registered = load_projects(ws)

    coded, to_encode = [], []
    used_codes = set(registered.keys())
    for name in sorted(os.listdir(root)):
        if not (root / name).is_dir():
            continue
        code = parse_code(name)
        if code:
            coded.append({"code": code, "name": strip_code(name), "folder": name})
            used_codes.add(code)

    # 依既有資料夾 + 帳本推導下一號, 兩邊都納入避免撞號
    seed_ids = [c for c in used_codes]
    for name in sorted(os.listdir(root)):
        if (root / name).is_dir() and not parse_code(name):
            new_code = next_serial("PRJ", [s.strip("[]") for s in seed_ids], width=3)
            new_code = "[%s]" % new_code
            seed_ids.append(new_code)
            to_encode.append({"old": name, "code": new_code,
                              "new": "%s %s" % (new_code, name.strip())})

    orphan = [c for c in registered
              if not any(x["code"] == c for x in coded)]
    return {"coded": coded, "to_encode": to_encode, "orphan_codes": orphan,
            "registered": registered}


def run(ws: Workspace, commit: bool = False, no_open: bool = True) -> EngineResult:
    ws.ensure()
    plan = scan(ws)
    ledger = Ledger(ws.projects_ledger, commit)
    events = EventLog(ws, commit)
    known = set(plan["registered"].keys())

    encoded = []
    for item in plan["to_encode"]:
        old_path = ws.workspace / item["old"]
        new_path = ws.workspace / item["new"]
        renamed = False
        if commit:
            try:
                if not new_path.exists():
                    os.rename(old_path, new_path)   # 只改名, 內容完全不動
                    renamed = True
            except OSError as e:
                item["error"] = str(e)[:80]
        if item["code"] not in known:
            ledger.append({"code": item["code"], "name": item["old"].strip(),
                           "folder": item["new"], "status_light": "Green",
                           "created": now_iso()})
            events.emit("PROJECT_ENCODED", item["code"],
                        "%s -> %s" % (item["old"], item["new"]))
            known.add(item["code"])
        item["renamed"] = renamed
        encoded.append(item)

    # 已有資料夾但帳本沒登記過的 (例如手動改好名的) -> 補登, add-only
    for c in plan["coded"]:
        if c["code"] not in known:
            ledger.append({"code": c["code"], "name": c["name"], "folder": c["folder"],
                           "status_light": "Green", "created": now_iso()})
            events.emit("PROJECT_REGISTERED", c["code"], "補登既有資料夾 %s" % c["folder"])
            known.add(c["code"])

    print("[專案] 既有編碼 %d / 本次新編 %d / 帳本孤兒(資料夾已不在) %d"
          % (len(plan["coded"]), len(encoded), len(plan["orphan_codes"])))
    report = _report(ws, plan, encoded, commit)
    try_open(report, no_open)
    return EngineResult(engine=ENGINE,
                        counts={"existing": len(plan["coded"]), "encoded": len(encoded),
                                "orphan": len(plan["orphan_codes"])},
                        records=encoded, report=str(report))


def _report(ws, plan, encoded, commit) -> Path:
    enc = table(["原資料夾", "分配編碼", "編碼後名稱", "已改名"],
                [[esc(i["old"]), pill(i["code"], "#4c78a8"), esc(i["new"]),
                  "✔" if i.get("renamed") else ("—" if commit else "(dry-run)")]
                 for i in encoded],
                "workspace/ 內沒有未編碼的資料夾")
    exist = table(["編碼", "專案名稱", "資料夾"],
                  [["<span class='mono'>%s</span>" % esc(c["code"]), esc(c["name"]),
                    esc(c["folder"])] for c in plan["coded"]],
                  "尚無已編碼專案")
    orphan = table(["帳本中有、資料夾已不在的編碼"],
                   [[pill(esc(c), "#c9a13a")] for c in plan["orphan_codes"]],
                   "無 — 帳本與資料夾一致")
    kpi = kpi_cards([("既有編碼專案", len(plan["coded"]), "#4c78a8"),
                     ("本次新編碼", len(encoded), "#5a9e6f"),
                     ("孤兒編碼", len(plan["orphan_codes"]), "#c9a13a")])
    return render_report(
        ws.reports / "VMT_Projects.html", "碼", "VMT 專案自動編碼 — 資料夾即 SSOT",
        "workspace/ 掃描 · [PRJ-###] · %s" % mode_label(commit),
        "治理：只重新命名最外層資料夾（內容完全不動、從不刪除）；projects.jsonl 只 append；"
        "已編碼資料夾與已建檔編碼一律冪等略過。dry-run 只列計畫，不改任何資料夾、不寫帳本。"
        "編碼後，[PRJ-###] 成為郵件歸戶與任務歸屬的精準金鑰，取代模糊的名稱比對。",
        [("KPI", kpi), ("本次自動編碼", enc), ("既有專案清單", exist),
         ("孤兒編碼（資料夾可能被搬走或改名）", orphan)],
        "%s %s | workspace/ + data/projects.jsonl" % (ENGINE, VERSION), commit)


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Project Auto-Encoder")
    add_common_args(ap)
    a = ap.parse_args()
    banner("VMT · Project Auto-Encoder %s" % VERSION, mode_label(a.commit))
    r = run(Workspace(a.root), a.commit, a.no_open)
    print("[輸出] 報告:", r.report)
    print("完成.")


if __name__ == "__main__":
    main()
