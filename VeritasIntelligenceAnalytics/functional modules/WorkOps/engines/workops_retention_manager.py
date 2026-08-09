# -*- coding: utf-8 -*-
r"""Veritas WorkOps 保留政策引擎 v0100 — GapFill 自建路 B(裁定序 G;PLAN 先行·apply 特別門)

刪除=最高風險動作,三重門全過才動一個檔:
  ①預設只產 PLAN(零刪除);②apply 需顯式 --confirm;③apply 前最新備份必須存在且
  verify PASS(ENG-031),否則拒絕。刪除範圍白名單鎖死:僅 out/ 下「可再生產物」
  (backups 舊 zip/scanrange 舊 RUN/audit_bundle 舊 zip/restore_staging/_gapfill_staging)
  — 側車帳本(registry/naming/events/lessons…)永不在範圍(只增不減)。
  每刪一檔 append out/retention_log.jsonl(誰/何時/多大/哪條規則)。
動詞:plan(預設)/ apply --confirm / log
參數:engines/retention_params.json(保留份數/天數;行為改變只改此檔)。
via-workops retention。
"""
import json, subprocess, sys, time
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
PLAN_P = OUT / "retention_plan.json"
LOG_P = OUT / "retention_log.jsonl"
PARAMS_P = HERE / "retention_params.json"
DEFAULTS = {"backups_keep": 10, "scanrange_runs_keep": 5, "audit_bundles_keep": 10,
            "staging_age_days": 30, "restore_staging_age_days": 14}


def params():
    try:
        p = json.loads(PARAMS_P.read_text(encoding="utf-8-sig"))
        d = dict(DEFAULTS)
        d.update({k: v for k, v in p.items() if k in DEFAULTS})
        return d
    except Exception:
        return dict(DEFAULTS)


def aged_dirs(root, days):
    if not root.exists():
        return []
    cut = time.time() - days * 86400
    return [d for d in root.iterdir() if d.is_dir() and d.stat().st_mtime < cut]


def build_plan():
    cfg = params()
    items = []

    def keep_newest(root, pattern, keep, rule):
        if not root.exists():
            return
        c = sorted(root.glob(pattern))
        for p in c[:-keep] if keep else c:
            items.append({"path": str(p), "size": p.stat().st_size if p.is_file() else sum(f.stat().st_size for f in p.rglob("*") if f.is_file()), "rule": rule})
    keep_newest(OUT / "backups", "*.zip", cfg["backups_keep"], "backups 留新 %d" % cfg["backups_keep"])
    keep_newest(OUT / "deep" / "scanrange", "RUN_*", cfg["scanrange_runs_keep"], "scanrange 留新 %d" % cfg["scanrange_runs_keep"])
    keep_newest(OUT / "audit_bundle", "*.zip", cfg["audit_bundles_keep"], "稽核包留新 %d" % cfg["audit_bundles_keep"])
    for d in aged_dirs(OUT / "restore_staging", cfg["restore_staging_age_days"]):
        items.append({"path": str(d), "size": sum(f.stat().st_size for f in d.rglob("*") if f.is_file()), "rule": "還原暫存 >%d 天" % cfg["restore_staging_age_days"]})
    for d in aged_dirs(OUT / "_gapfill_staging", cfg["staging_age_days"]):
        items.append({"path": str(d), "size": sum(f.stat().st_size for f in d.rglob("*") if f.is_file()), "rule": "staging >%d 天" % cfg["staging_age_days"]})
    return items


def cmd_plan():
    items = build_plan()
    tot = sum(i["size"] for i in items)
    PLAN_P.parent.mkdir(parents=True, exist_ok=True)
    PLAN_P.write_text(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                  "items": items, "total_bytes": tot}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[保留計畫] 可清 %d 項 · 共 %.1f MB(零刪除 — 只是計畫)→ %s" % (len(items), tot / 1048576.0, PLAN_P.name))
    for i in items[:10]:
        print("  %.1f MB  %s(%s)" % (i["size"] / 1048576.0, Path(i["path"]).name, i["rule"]))
    if not items:
        print("  (無可清項 — 全部在保留份數/天數內)")
    print("[門] 執行清理:retention apply --confirm(需最新備份 verify PASS;側車帳本永不在範圍)")
    return 0


def cmd_apply(confirm):
    if not confirm:
        print("[拒絕] apply 需顯式 --confirm(特別門①)")
        return 1
    bks = sorted((OUT / "backups").glob("*.zip")) if (OUT / "backups").exists() else []
    if not bks:
        print("[拒絕] 無任何備份 — 先 via-workops backup(特別門②)")
        return 1
    r = subprocess.run([sys.executable, str(HERE / "workops_backup.py"), "verify", str(bks[-1])],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("[拒絕] 最新備份 verify 未過 — 不在可回復狀態,拒刪(特別門③)")
        return 1
    print("[門] 三重門過(confirm+備份在位+verify PASS)— 依最新計畫執行")
    plan = json.loads(PLAN_P.read_text(encoding="utf-8-sig")) if PLAN_P.exists() else {"items": []}
    allow = [str(OUT / "backups"), str(OUT / "deep" / "scanrange"), str(OUT / "audit_bundle"),
             str(OUT / "restore_staging"), str(OUT / "_gapfill_staging")]
    import shutil
    n = 0
    with LOG_P.open("a", encoding="utf-8") as lg:
        for it in plan["items"]:
            p = Path(it["path"])
            if not any(str(p).startswith(a) for a in allow):
                print("  [跳] 白名單外拒刪:%s" % p)
                continue
            if not p.exists():
                continue
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()
            n += 1
            lg.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                 "deleted": str(p), "size": it["size"], "rule": it["rule"]},
                                ensure_ascii=False) + "\n")
    print("[清理] 刪 %d 項(逐筆入 retention_log.jsonl;側車帳本零觸碰)" % n)
    return 0


def cmd_log():
    if LOG_P.exists():
        for ln in LOG_P.read_text(encoding="utf-8").splitlines()[-20:]:
            print("  " + ln)
    else:
        print("  (尚無清理紀錄)")
    return 0


def main(argv):
    a = argv[1:]
    if a and a[0] == "apply":
        return cmd_apply("--confirm" in a)
    if a and a[0] == "log":
        return cmd_log()
    if not a or a[0] == "plan":
        return cmd_plan()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
