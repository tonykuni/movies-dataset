# -*- coding: utf-8 -*-
r"""Veritas WorkOps × MeetingLoop 對帳橋 v0100(ENG-048)— 操作員「合為對帳」令

MeetingLoop 每輪 run 的「決議/行動」自動併入 WorkOps 對帳迴圈:
  決議(04_decisions.json)→ ENG-027 decision_log add(DEC-#### 本冊發號;
    冪等 — 橋帳本記 meeting+內容雜湊,同件永不重入;來源標 MTG id)
  行動(06_actions.csv)→ out/meeting_actions.json(未完行動 → 每日 TO-DO 會議行動批)
會議中人已確認之決議=人工確認等級,直接入帳;行動只彙整不代辦。全程 append-only。
動詞:pull(預設)/ status。via-workops mtg。
"""
import csv, hashlib, io, json, subprocess, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
RUNS = WORKOPS / "MeetingLoop" / "runs"
LEDGER_P = OUT / "meetingloop_bridge_ledger.json"
ACTIONS_P = OUT / "meeting_actions.json"
OPEN_STATUS = {"NOT_STARTED", "IN_PROGRESS", "WAITING_RESPONSE", "BLOCKED", "OVERDUE", "NEED_DECISION"}


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def key_of(mtg, text):
    return mtg + "|" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def cmd_pull():
    if not RUNS.exists():
        print("[空] 尚無 MeetingLoop run — via-meetingloop -Mode Process 之後再 pull")
        return 0
    led = jload(LEDGER_P, {"absorbed": {}})
    n_dec_new = n_dec_dup = 0
    all_actions = []
    runs = sorted(d for d in RUNS.iterdir() if d.is_dir() and d.name.startswith("RUN_"))
    for run in runs:
        man = jload(run / "11_run_manifest.json", {})
        mtg = man.get("meeting_id") or run.name
        for dec in jload(run / "04_decisions.json", []):
            text = (dec.get("text") or dec.get("decision") or str(dec))[:120]
            k = key_of(mtg, text)
            if k in led["absorbed"]:
                n_dec_dup += 1
                continue
            r = subprocess.run([sys.executable, str(HERE / "workops_decision_log.py"),
                                "add", text, dec.get("owner", "") or "會議指派", "", "", mtg],
                               capture_output=True, text=True)
            if r.returncode == 0:
                led["absorbed"][k] = {"ts": datetime.now().isoformat(timespec="seconds"),
                                      "mtg": mtg, "text": text}
                n_dec_new += 1
                print("[入帳] %s ← 「%s」" % (mtg, text[:50]))
            else:
                print("[FAIL] decision_log add:%s" % (r.stdout + r.stderr)[:120])
        cur = jload(run / "actions_current.json", None)
        rows = []
        if isinstance(cur, list):
            rows = cur
        else:
            try:
                with io.open(run / "06_actions.csv", "r", encoding="utf-8-sig", errors="replace", newline="") as f:
                    rows = list(csv.DictReader(f))
            except Exception:
                rows = []
        for a in rows:
            st = (a.get("status") or "").strip()
            if st in OPEN_STATUS or not st:
                all_actions.append({"mtg": mtg, "action_id": a.get("action_id", ""),
                                    "item": (a.get("action_item") or "")[:80],
                                    "owner": a.get("owner", ""), "due": a.get("due_date", ""),
                                    "status": st or "NOT_STARTED"})
    OUT.mkdir(parents=True, exist_ok=True)
    LEDGER_P.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    if n_dec_new:
        subprocess.run([sys.executable, str(HERE / "workops_decision_log.py"), "export"],
                       capture_output=True)   # 刷新 CSV — todo「未結決議」即時同步
    ACTIONS_P.write_text(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                     "open_actions": all_actions}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[對帳橋] run %d 輪 · 決議新入 %d(冪等略過 %d)· 未完行動 %d 件 → meeting_actions.json(TO-DO 會議行動批)"
          % (len(runs), n_dec_new, n_dec_dup, len(all_actions)))
    print("[治理] 決議=會議中人已確認 → 直接入 DEC 帳(來源標 MTG);行動只彙整不代辦;絕不代寄")
    return 0


def cmd_status():
    led = jload(LEDGER_P, {"absorbed": {}})
    ac = jload(ACTIONS_P, {})
    print("[橋帳] 已吸收決議 %d 筆 · 未完行動 %d 件(%s)"
          % (len(led["absorbed"]), len(ac.get("open_actions", [])), ac.get("ts", "尚未 pull")))
    return 0


def main(argv):
    if len(argv) > 1 and argv[1] == "status":
        return cmd_status()
    return cmd_pull()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
