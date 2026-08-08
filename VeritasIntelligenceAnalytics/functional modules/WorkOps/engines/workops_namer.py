# -*- coding: utf-8 -*-
# WorkOps 命名核對引擎 v0102(ENG-023)— v0102:共用詞彙收斂 import workops_lexicon(SSOT 去重令)— 編號不變,名稱作別名層(提議→核對→顯示)
#
# v0101(操作員 2026/08/09 補不足令):propose 尾端自動做 THR↔CASE 跨帳本連結 —
#   以正規化主旨(剝 Re/Fw/[THR-#] 標籤)比對板側 mails.csv+id_ledger 與深鏈 E01,
#   對映落 out/thr_case_map.json(side-car);THR 編號繼承所連 CASE 之名稱入命名帳本
#   (approved 永不被覆蓋;LINK 動作入 history)。兩套編號自此互鏈,核對表同表涵蓋。
#
# 操作員裁決(2026/08/08):「自動編號的號碼不便 · 系統自動提議名稱給使用者核對 ·
#   可自建名稱歸類」。編號(CASE/THR/WOP)是管控鐵律不可變;本引擎為每個編號
#   自動提議「人話名稱」,使用者核對後全報表顯示「編號·名稱」。
# 資料流:super_engine.db(E01_MAIL)→ propose(最常見主旨+主寄件者啟發式)
#   → out/workops_naming.json(side-car 帳本,只增不減:approved 永不被 propose 覆蓋,
#     每筆留 history)→ out/naming_review.csv(utf8BOM,Excel 可開)供核對
#   → apply 讀回核對欄 → analytics 報表自動顯示名稱。
# 自建歸類:add 動詞把自訂群組(名稱+關鍵字)入帳本,供後續規則增補參考。
# 治理:Outlook/原件零觸碰;帳本 side-car;誠實逐筆回報。
import argparse, csv, io, json, re, sqlite3, sys
from datetime import datetime
from pathlib import Path

from workops_lexicon import PREFIX_RE, TAG_RE, norm_subj, clean_subject

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE    = Path(__file__).resolve().parent          # engines/
OUT     = HERE.parent / "out"
LEDGER  = OUT / "workops_naming.json"
REVIEW  = OUT / "naming_review.csv"
DB_DEF  = OUT / "deep" / "engine_out" / "super_engine.db"

BOARD_MAILS = OUT / "mails.csv"
ID_LEDGER = OUT / "workops_id_ledger.json"
THR_MAP = OUT / "thr_case_map.json"


def link_thr_to_case(led, dbpath):
    """THR↔CASE 跨帳本連結(v0101):正規化主旨比對;THR 繼承 CASE 名稱。
    回傳 (連結數, 新名數);前置缺席誠實回 (0,0)。"""
    p = Path(dbpath)
    if not (BOARD_MAILS.exists() and ID_LEDGER.exists() and p.exists()):
        return 0, 0
    try:
        lm = json.loads(ID_LEDGER.read_text(encoding="utf-8-sig")).get("map", {})
    except Exception:
        return 0, 0
    conv2thr = {k[4:]: v for k, v in lm.items() if k.startswith("THR|")}
    conv2subj = {}
    try:
        with io.open(BOARD_MAILS, "r", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                cid = (row.get("ConversationID") or "").strip()
                if cid and cid not in conv2subj:
                    conv2subj[cid] = row.get("Subject") or ""
    except Exception:
        return 0, 0
    conn = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    subj2case = {}
    for subj, cs in conn.execute("SELECT subject, case_seq FROM E01_MAIL"):
        k = norm_subj(subj)
        if k and cs and k not in subj2case:
            subj2case[k] = cs
    conn.close()
    n_link = n_name = 0
    mapping = {}
    for conv, thr in conv2thr.items():
        case = subj2case.get(norm_subj(conv2subj.get(conv, "")))
        if not case:
            continue
        mapping[thr] = case
        n_link += 1
        ce = led["entries"].get(case) or {}
        label = ce.get("approved") or ce.get("proposed") or ""
        te = led["entries"].get(thr)
        if te is None:
            led["entries"][thr] = {"proposed": label or ("↔" + case), "approved": None,
                                   "link_case": case,
                                   "history": [{"ts": now(), "action": "LINK", "value": case}]}
            if label:
                n_name += 1
        else:
            if te.get("link_case") != case:
                te["link_case"] = case
                te.setdefault("history", []).append({"ts": now(), "action": "LINK", "value": case})
            if label and not te.get("approved") and te.get("proposed") != label:
                te["proposed"] = label
                te["history"].append({"ts": now(), "action": "REPROPOSE-LINK", "value": label})
                n_name += 1
    THR_MAP.write_text(json.dumps({"version": "v0100", "map": mapping}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    return n_link, n_name


def now():
    return datetime.now().isoformat(timespec="seconds")


def load_ledger():
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"version": "v0100", "append_only": True, "entries": {}, "custom_groups": []}


def save_ledger(led):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")


def propose_name(subjects, senders):
    """啟發式:最常見清理後主旨;主旨全空則用主寄件者。"""
    from collections import Counter
    subs = Counter(clean_subject(s) for s in subjects if clean_subject(s))
    if subs:
        return subs.most_common(1)[0][0]
    snd = Counter((x or "").strip() for x in senders if (x or "").strip())
    return (snd.most_common(1)[0][0] if snd else "")[:40]


def cmd_propose(dbpath):
    p = Path(dbpath)
    if not p.exists():
        print("[FAIL] 引擎庫不存在:%s(先跑 via-workops deep)" % p)
        return 1
    conn = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    rows = conn.execute("SELECT case_seq, subject, sender FROM E01_MAIL").fetchall()
    by_case = {}
    for cs, subj, snd in rows:
        by_case.setdefault(cs, ([], []))
        by_case[cs][0].append(subj)
        by_case[cs][1].append(snd)
    led = load_ledger()
    n_new, n_keep = 0, 0
    for cs in sorted(by_case):
        ent = led["entries"].get(cs)
        if ent and ent.get("approved"):
            n_keep += 1
            continue                       # 已核對者永不覆蓋(只增不減)
        name = propose_name(*by_case[cs])
        if not name:
            continue
        if ent is None:
            led["entries"][cs] = {"proposed": name, "approved": None,
                                  "history": [{"ts": now(), "action": "PROPOSE", "value": name}]}
            n_new += 1
        elif ent.get("proposed") != name:
            ent["proposed"] = name
            ent["history"].append({"ts": now(), "action": "REPROPOSE", "value": name})
            n_new += 1
    n_link, n_name = link_thr_to_case(led, dbpath)   # v0101:先互鏈再落表,THR 列同表核對
    save_ledger(led)
    # 核對表(utf8BOM):填「核對名稱」=改名;留空=接受建議;整列刪除=本輪不核對
    OUT.mkdir(parents=True, exist_ok=True)
    with io.open(REVIEW, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["編號", "系統建議名稱", "核對名稱(空=接受建議)", "狀態"])
        for cs in sorted(led["entries"]):
            e = led["entries"][cs]
            w.writerow([cs, e.get("proposed", ""), e.get("approved") or "",
                        "已核對" if e.get("approved") else "待核對"])
    total = len(led["entries"])
    print("[提議] 新/更新 %d · 已核對保留 %d · 帳本共 %d 筆 → %s" % (n_new, n_keep, total, LEDGER))
    if n_link:
        print("[互鏈] THR↔CASE 連結 %d 串 · THR 繼承名稱 %d 筆 → %s" % (n_link, n_name, THR_MAP))
    print("[核對] 開 %s:改名填第三欄、接受留空,再跑 via-workops names apply" % REVIEW)
    return 0


def cmd_apply(csvpath):
    p = Path(csvpath)
    if not p.exists():
        print("[FAIL] 核對表不存在:%s(先跑 names propose)" % p)
        return 1
    led = load_ledger()
    n_ok, n_skip = 0, 0
    with io.open(p, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cs = (row.get("編號") or "").strip()
            ent = led["entries"].get(cs)
            if not cs or ent is None:
                n_skip += 1
                continue
            name = (row.get("核對名稱(空=接受建議)") or "").strip() or (row.get("系統建議名稱") or "").strip()
            if not name or ent.get("approved") == name:
                n_skip += 1
                continue
            ent["approved"] = name
            ent["history"].append({"ts": now(), "action": "APPROVE", "value": name})
            n_ok += 1
    save_ledger(led)
    print("[核對] 已核對 %d 筆 · 略過 %d(空/未變/未知編號)· 下次報表即顯示「編號·名稱」" % (n_ok, n_skip))
    return 0


def cmd_add(name, keyword):
    if not name:
        print("[FAIL] add 需要群組名稱:via-workops names add 名稱 [關鍵字]")
        return 1
    led = load_ledger()
    led["custom_groups"].append({"name": name, "keyword": keyword or "", "ts": now()})
    save_ledger(led)
    print("[自建歸類] 已加入:%s(關鍵字:%s)· 共 %d 組" % (name, keyword or "-", len(led["custom_groups"])))
    return 0


def cmd_list():
    led = load_ledger()
    if not led["entries"] and not led["custom_groups"]:
        print("[空] 帳本無資料 — 先跑 via-workops names propose")
        return 0
    for cs in sorted(led["entries"]):
        e = led["entries"][cs]
        mark = "✔" if e.get("approved") else "…"
        print("%s %s · %s" % (mark, cs, e.get("approved") or (e.get("proposed", "") + "(待核對)")))
    for g in led["custom_groups"]:
        print("▣ 自建:%s(%s)" % (g["name"], g.get("keyword") or "-"))
    return 0


def main():
    ap = argparse.ArgumentParser(description="WorkOps 命名核對:編號不變,名稱提議→核對→顯示")
    ap.add_argument("command", nargs="?", default="list",
                    choices=["propose", "apply", "add", "list"])
    ap.add_argument("arg1", nargs="?", default="")
    ap.add_argument("arg2", nargs="?", default="")
    ap.add_argument("--db", default=str(DB_DEF))
    ap.add_argument("--csv", default=str(REVIEW))
    a = ap.parse_args()
    if a.command == "propose":
        return cmd_propose(a.db)
    if a.command == "apply":
        return cmd_apply(a.csv)
    if a.command == "add":
        return cmd_add(a.arg1, a.arg2)
    return cmd_list()


if __name__ == "__main__":
    sys.exit(main())
