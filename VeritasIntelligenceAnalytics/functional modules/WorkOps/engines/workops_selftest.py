# -*- coding: utf-8 -*-
r"""Veritas WorkOps 全鏈自測器 v0101(ENG-032)— Integration + System Test 一鍵版

操作員令(2026/08/09):測試功能完整確認無誤後開始串聯 — 本引擎在「隔離沙箱」跑完
整條 Python 引擎鏈(命名→互鏈→歸戶八層→回覆解析→準確度→會議決策→備份/還原),
逐段斷言,
印狀態表 + FinalGate;報告落 out/selftest_report.json。真實 out/ 正本零觸碰。

沙箱法:temp 目錄複製 engines/*.py + 參數詞庫 → 合成 fixtures(六串郵件涵蓋
L1/L2/S3/S4/風險/OOO)→ 逐引擎 subprocess 實跑 → 斷言產物。每段誠實 OK/FAIL,
失敗不中斷其餘段(不卡斷);FinalGate=PASS 才可宣稱鏈路無誤。
動詞:run(預設)。via-workops selftest。
"""
import io, json, csv, shutil, sqlite3, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
REAL_OUT = HERE.parent / "out"

ENGINE_FILES = ["workops_lexicon.py", "workops_namer.py", "workops_wop_identifier.py",
                "workops_reply_parser.py", "workops_accuracy_benchmark.py", "workops_backup.py",
                "workops_decision_log.py"]
DATA_FILES = ["identifier_params.json", "product_code_map.json", "reply_parser_params.json",
              "org_lexicon.json", "bulk_senders.txt", "domain_dict.txt", "holidays_tw.txt",
              "watchtower_params.json"]

RESULTS = []


def stage(name, ok, detail=""):
    RESULTS.append({"stage": name, "gate": "PASS" if ok else "FAIL", "detail": detail})
    print("[%s] %s%s" % ("OK " if ok else "FAIL", name, (" — " + detail) if detail else ""))
    return ok


def run_py(sandbox, script, *args):
    r = subprocess.run([sys.executable, str(sandbox / "engines" / script)] + list(args),
                       capture_output=True, text=True, cwd=str(sandbox))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def build_fixtures(sb):
    out = sb / "out"
    out.mkdir(parents=True, exist_ok=True)
    led = {"seq_wop": 0, "seq_thr": 6, "map": {("THR|c%d" % i): ("THR-%05d" % i) for i in range(1, 7)}}
    (out / "workops_id_ledger.json").write_text(json.dumps(led), encoding="utf-8")
    rows = [
        {"MailID": "c1", "Subject": "ABC-123 kickoff", "SenderEmail": "wang@acme.com", "ConversationID": "c1", "VotingResponse": ""},
        {"MailID": "c2", "Subject": "Re: ABC-123 kickoff", "SenderEmail": "chen@acme.com", "ConversationID": "c2", "VotingResponse": "已完成"},
        {"MailID": "c3", "Subject": "台新銀行對帳單事宜", "SenderEmail": "svc@bank.com", "ConversationID": "c3", "VotingResponse": ""},
        {"MailID": "c4", "Subject": "進度更新", "SenderEmail": "pm@corp.com", "ConversationID": "c4", "VotingResponse": ""},
        {"MailID": "c5", "Subject": "RE: 合約", "SenderEmail": "legal@vendor.com", "ConversationID": "c5", "VotingResponse": ""},
        {"MailID": "c6", "Subject": "Automatic reply: 追蹤", "SenderEmail": "ooo@corp.com", "ConversationID": "c6", "VotingResponse": ""},
    ]
    for r in rows:
        r.update({"Direction": "INBOUND", "EventDate": "2026/08/09 10:00", "Unread": "False", "Categories": ""})
    with io.open(out / "mails.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    run = out / "deep" / "scanrange" / "RUN_SELFTEST"
    run.mkdir(parents=True, exist_ok=True)
    frows = [
        {"CONVERSATION_ID": "c4", "DIRECTION": "INBOUND", "TITLE": "進度更新", "TIME": "t",
         "FOLDER_NAME": "XY-77 專案信", "BODY_SNIPPET": "如題", "ATTACHMENT_NAMES": "", "FROM": ""},
        {"CONVERSATION_ID": "c5", "DIRECTION": "INBOUND", "TITLE": "RE: 合約", "TIME": "t",
         "FOLDER_NAME": "供應商", "BODY_SNIPPET": "再延遲將視為違約並移交律師處理", "ATTACHMENT_NAMES": "", "FROM": ""},
        {"CONVERSATION_ID": "c6", "DIRECTION": "INBOUND", "TITLE": "Automatic reply: 追蹤", "TIME": "t",
         "FOLDER_NAME": "收件匣", "BODY_SNIPPET": "I am out of office, contact mary@corp.com", "ATTACHMENT_NAMES": "", "FROM": ""},
        {"CONVERSATION_ID": "c5", "DIRECTION": "OUTBOUND", "TITLE": "[急件·再追] 合約 [THR-00005]", "TIME": "t",
         "FOLDER_NAME": "寄件備份", "BODY_SNIPPET": "", "ATTACHMENT_NAMES": "", "FROM": ""},
    ]
    with io.open(run / "01_mail_index.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(frows[0])); w.writeheader(); w.writerows(frows)
    with io.open(sb / "control_sheet.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["案號", "名稱", "承辦人", "狀態"])          # 異質表頭+隱性阻塞詞
        w.writerow(["ABC-123", "艾克米導入", "Tony", "等供應商回覆"])
    db = out / "deep" / "engine_out"
    db.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db / "super_engine.db")
    conn.execute("CREATE TABLE E01_MAIL(case_seq TEXT, subject TEXT, sender TEXT)")
    conn.executemany("INSERT INTO E01_MAIL VALUES(?,?,?)",
                     [("CASE-0001", "台新銀行對帳單事宜", "svc@bank.com"),
                      ("CASE-0002", "ABC-123 kickoff", "wang@acme.com")])
    conn.commit(); conn.close()


def main():
    print("========== Veritas WorkOps 全鏈自測(沙箱;正本零觸碰)==========")
    sb = Path(tempfile.mkdtemp(prefix="VeritasWorkOps_SelfTest_"))
    try:
        eng = sb / "engines"
        eng.mkdir()
        for f in ENGINE_FILES + DATA_FILES:
            src = HERE / f
            if src.exists():
                shutil.copy(src, eng / f)
        build_fixtures(sb)
        out = sb / "out"

        rc, o = run_py(sb, "workops_namer.py", "propose")
        led_ok = (out / "workops_naming.json").exists() and (out / "thr_case_map.json").exists()
        stage("1 命名提議+THR↔CASE 互鏈", rc == 0 and led_ok, "namer propose")

        rc, o = run_py(sb, "workops_wop_identifier.py", "propose")
        reg = json.loads((out / "wop_registry.json").read_text(encoding="utf-8")) if (out / "wop_registry.json").exists() else {}
        w2 = reg.get("thr2wop", {})
        ok = (rc == 0 and "THR-00001" in w2 and "THR-00002" in w2
              and w2.get("THR-00001") == w2.get("THR-00002") and len(reg.get("projects", {})) >= 1)
        stage("2 WOP 八層歸戶(同代號合流)", ok, "AUTO %d 案" % len(reg.get("projects", {})))

        rc, o = run_py(sb, "workops_reply_parser.py", "parse")
        rs = json.loads((out / "reply_status.json").read_text(encoding="utf-8")) if (out / "reply_status.json").exists() else {}
        fl = rs.get("flags", {})
        ok = (rc == 0 and rs.get("status", {}).get("THR-00002", {}).get("layer") == "V"
              and fl.get("THR-00005", {}).get("risk") and fl.get("THR-00006", {}).get("ooo")
              and rs.get("sent_stage", {}).get("THR-00005", {}).get("stage") == "T2")
        stage("3 回覆解析(V 層/⚡風險/⏸OOO/已發段)", ok)

        rc, o = run_py(sb, "workops_accuracy_benchmark.py", "template")
        tpl_ok = rc == 0 and (out / "gold_set_template.csv").exists()
        if tpl_ok:
            shutil.copy(out / "gold_set_template.csv", out / "gold_set.csv")
            rc2, o2 = run_py(sb, "workops_accuracy_benchmark.py", "run")
            rep = json.loads((out / "accuracy_report.json").read_text(encoding="utf-8")) if (out / "accuracy_report.json").exists() else {}
            tpl_ok = rc2 == 0 and rep.get("assignment_accuracy") == 1.0
        stage("4 Gold Set 準確度(全同意=100%)", tpl_ok)

        rc, o = run_py(sb, "workops_decision_log.py", "add", "沙箱決議:契約回簽追蹤", "Tony",
                       "2026-08-15", "THR-00001", "MTG-001")
        rc2, _ = run_py(sb, "workops_decision_log.py", "report")
        rc3, _ = run_py(sb, "workops_decision_log.py", "export")
        dcsv = out / "decision_log.csv"
        dtxt = dcsv.read_text(encoding="utf-8-sig") if dcsv.exists() else ""
        ok = rc == 0 and rc2 == 0 and rc3 == 0 and "DEC-0001" in dtxt and "MTG-001" in dtxt
        stage("5 會議決策追蹤(ENG-027:add→report→export)", ok, "DEC-0001 · 會議碼 MTG-001")

        rc, o = run_py(sb, "workops_backup.py", "backup")
        bks = sorted((out / "backups").glob("*.zip")) if (out / "backups").exists() else []
        bk_ok = rc == 0 and bks
        if bk_ok:
            rc2, _ = run_py(sb, "workops_backup.py", "verify", str(bks[-1]))
            rc3, _ = run_py(sb, "workops_backup.py", "restore", str(bks[-1]))
            bk_ok = rc2 == 0 and rc3 == 0 and (out / "restore_staging").exists()
        stage("6 備份→驗證→還原到暫存", bk_ok)

        n_fail = sum(1 for r in RESULTS if r["gate"] == "FAIL")
        final = "PASS" if n_fail == 0 else "FAIL"
        REAL_OUT.mkdir(parents=True, exist_ok=True)
        (REAL_OUT / "selftest_report.json").write_text(json.dumps(
            {"ts": datetime.now().isoformat(timespec="seconds"), "final_gate": final,
             "stages": RESULTS, "sandbox": str(sb)}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("---------------------------------------------------------------")
        print("[總結] FinalGate = %s(%d/%d 段過)→ out/selftest_report.json" % (final, len(RESULTS) - n_fail, len(RESULTS)))
        return 0 if final == "PASS" else 1
    finally:
        shutil.rmtree(sb, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
