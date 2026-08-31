# -*- coding: utf-8 -*-
r"""Veritas WorkOps 里程碑引擎 v0100 — GapFill 自建路 B(裁定序 C;append-only)

WOP 案件掛里程碑:MLS-#### 編號一經生成永不變;不可刪、只可補狀態(history 全留)。
動詞:create WOP-#### 名稱 YYYY-MM-DD [--owner 人]
      complete MLS-#### [--evidence 佐證]
      list [WOP-####] / status
側車:out/milestones.json(seq+items+history,append-only)。via-workops milestones。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json, sys
from datetime import datetime, date
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
P = OUT / "milestones.json"


def now():
    return datetime.now().isoformat(timespec="seconds")


def load():
    try:
        return json.loads(P.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"seq": 0, "items": {}}


def save(d):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = P.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(P)


def cmd_create(wop, name, due, owner=""):
    d = load()
    d["seq"] += 1
    mid = "MLS-%04d" % d["seq"]
    d["items"][mid] = {"wop": wop, "name": name, "due": due, "owner": owner,
                       "status": "OPEN", "created": now(), "evidence": "",
                       "history": [{"ts": now(), "ev": "CREATE"}]}
    save(d)
    print("[里程碑] %s:%s(%s · due %s · %s)— 編號永不變" % (mid, name, wop, due, owner or "未指派"))
    return 0


def cmd_complete(mid, evidence=""):
    d = load()
    it = d["items"].get(mid)
    if not it:
        print("[FAIL] 查無 %s" % mid)
        return 1
    if it["status"] == "COMPLETED":
        print("[略] %s 已完成(冪等)" % mid)
        return 0
    it["status"] = "COMPLETED"
    it["completed"] = now()
    if evidence:
        it["evidence"] = evidence
    it["history"].append({"ts": now(), "ev": "COMPLETE", "evidence": evidence})
    save(d)
    print("[完成] %s %s%s" % (mid, it["name"], (" · 佐證 " + evidence) if evidence else "(無佐證 — 誠實留白)"))
    return 0


def cmd_list(wop=""):
    d = load()
    today = date.today().isoformat()
    n = 0
    for mid, it in sorted(d["items"].items()):
        if wop and it["wop"] != wop:
            continue
        n += 1
        late = "⚠逾期" if (it["status"] == "OPEN" and it.get("due", "9999") < today) else ""
        print("  %-8s %-9s %-8s %s · due %s · %s %s" % (mid, it["wop"], it["status"], it["name"][:30], it.get("due", "—"), it.get("owner", ""), late))
    print("[共] %d 筆(帳本 %d)" % (n, len(d["items"])))
    return 0


def cmd_status():
    d = load()
    today = date.today().isoformat()
    n_open = sum(1 for it in d["items"].values() if it["status"] == "OPEN")
    n_late = sum(1 for it in d["items"].values() if it["status"] == "OPEN" and it.get("due", "9999") < today)
    print("[里程碑] 共 %d · 未完 %d · 逾期 %d(逾期即入下游衝擊 — timeline build 檢視)" % (len(d["items"]), n_open, n_late))
    return 0


def main(argv):
    a = argv[1:]

    def opt(flag):
        return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else ""
    try:
        if a and a[0] == "create":
            return cmd_create(a[1], a[2], a[3], opt("--owner"))
        if a and a[0] == "complete":
            return cmd_complete(a[1], opt("--evidence"))
        if a and a[0] == "list":
            return cmd_list(a[1] if len(a) > 1 and not a[1].startswith("--") else "")
        if not a or a[0] == "status":
            return cmd_status()
    except IndexError:
        pass
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
