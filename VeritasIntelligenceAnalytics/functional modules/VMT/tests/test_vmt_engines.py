# -*- coding: utf-8 -*-
"""
VMT 引擎測試 — 標準庫 unittest, 無外部相依。

    python3 tests/test_vmt_engines.py            (於 VMT 目錄下執行)

測試重點放在「錯了會出事」的地方:
  - 治理紅線: dry-run 不落帳、帳本只 append、冪等重跑不長資料
  - 語言判讀: 期限換算、決議 vs 提議、指派句、幻覺過濾
  - 主詞標示: 指派 / 第一人稱 / 繼承 / 判不出標 [?]
  - 閉環    : 回覆勾選 -> 事件 -> 狀態; 以及兩個刻意的保守行為
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import tempfile
import unittest
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "engines"))

import vmt_ai_triage          # noqa: E402
import vmt_extract_tasks      # noqa: E402
import vmt_mail_composer      # noqa: E402
import vmt_meeting_minutes as mm  # noqa: E402
import vmt_outlook_intake     # noqa: E402
import vmt_reply_parser       # noqa: E402
import vmt_sla_engine         # noqa: E402
import vmt_task_ssot as ssot  # noqa: E402
import vmt_lang as lang       # noqa: E402
import vmt_pipeline            # noqa: E402
import vmt_projects            # noqa: E402
from vmt_core import (  # noqa: E402
    EventLog, Ledger, Quarantine, Workspace, reset_dry_run,
    atomic_write_text, read_json_resilient,
)

SAMPLES = HERE.parent / "samples"
MEETING_DATE = dt.date(2026, 7, 31)          # 週五


class TempWS(unittest.TestCase):
    def setUp(self):
        reset_dry_run()
        self.tmp = Path(tempfile.mkdtemp(prefix="vmt_test_"))
        self.ws = Workspace(self.tmp).ensure()
        self.cfg = json.loads((SAMPLES / "meeting_config.json").read_text(encoding="utf-8"))

    def tearDown(self):
        reset_dry_run()
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------- 語言層 ----


class TestLang(unittest.TestCase):
    def test_relative_dates(self):
        base = MEETING_DATE                                   # 2026-07-31 週五
        cases = {
            "下週三前提出": dt.date(2026, 8, 5),
            "月底前提供": dt.date(2026, 7, 31),
            "明天給你": dt.date(2026, 8, 1),
            "三天內回覆": dt.date(2026, 8, 3),
            "8月10號補齊": dt.date(2026, 8, 10),
            "下個月5日": dt.date(2026, 8, 5),
        }
        for text, want in cases.items():
            got = lang.resolve_due(text, base)
            self.assertIsNotNone(got, "未解析出期限: %s" % text)
            self.assertEqual(got[0], want, "%s -> %s (預期 %s)" % (text, got[0], want))

    def test_no_false_deadline(self):
        self.assertIsNone(lang.resolve_due("這個案子很重要", MEETING_DATE))

    def test_decision_vs_opinion(self):
        """『應該可以』不是決議 —— 把提議寫成決議是會議記錄最嚴重的錯誤。"""
        self.assertEqual(lang.classify_sentence("那就決定拉長到四週")["tag"], "決")
        self.assertEqual(lang.classify_sentence("我覺得應該可以拉長到四週")["tag"], "議")
        # 弱決策詞只有主席說才算數
        self.assertNotEqual(lang.classify_sentence("那就這樣")["tag"], "決")
        self.assertEqual(lang.classify_sentence("那就這樣", is_chair=True)["tag"], "決")

    def test_assignment_is_action_not_question(self):
        r = lang.classify_sentence("麻煩林佳蓉確認一下排程有沒有衝突")
        self.assertEqual(r["tag"], "辦")
        self.assertTrue(r["cue"].startswith("指派"))

    def test_question(self):
        self.assertEqual(lang.classify_sentence("行銷預算還剩多少？")["tag"], "問")

    def test_fuzzy_correct_never_corrupts_shorter_word(self):
        """『宣傳』不可被『宣傳期』覆寫 —— 校正不能反過來製造錯誤。"""
        out, ch = lang.fuzzy_correct("提出新的宣傳排程", ["宣傳期"])
        self.assertEqual(out, "提出新的宣傳排程")
        self.assertEqual(ch, [])

    def test_fuzzy_correct_fixes_typo(self):
        out, ch = lang.fuzzy_correct("東莞線的稼動律偏低", ["稼動率"])
        self.assertIn("稼動率", out)
        self.assertEqual(ch, [("稼動律", "稼動率")])

    def test_mail_classify(self):
        r = lang.classify_mail("請協助提供產能數字", "麻煩下週三前提供")
        self.assertEqual(r["intent"], "REQUEST")
        self.assertTrue(r["needs_action"])
        r2 = lang.classify_mail("逾期提醒", "此案已逾期，請盡快回覆。緊急。")
        self.assertEqual(r2["intent"], "ESCALATION")
        self.assertEqual(r2["urgency"], 5)
        r3 = lang.classify_mail("FYI - 簡報已上傳", "供參，無需回覆。")
        self.assertFalse(r3["needs_action"])

    def test_zh_numbers(self):
        self.assertEqual(lang.zh2int("三"), 3)
        self.assertEqual(lang.zh2int("十五"), 15)
        self.assertEqual(lang.zh2int("二十"), 20)
        self.assertIsNone(lang.zh2int("很多"))


# ---------------------------------------------------------------- 會議 ------


class TestMinutes(TempWS):
    def _run(self, commit=True):
        return mm.run(self.ws, SAMPLES / "sample_transcript.json", dict(self.cfg),
                      commit=commit, no_open=True)

    def test_pipeline_outputs(self):
        r = self._run()
        rec = r.records[0]
        self.assertEqual(r.counts["decisions"], 1)
        self.assertEqual(r.counts["actions"], 4)
        self.assertEqual(r.counts["dropped"], 1, "ASR 幻覺句應被過濾")

        actions = {a["owner"]: a for a in rec["records"]["actions"]}
        self.assertEqual(actions["李美華"]["due"], "2026-08-05", "「下週三」應換算為絕對日期")
        self.assertEqual(actions["陳志豪"]["due"], "2026-07-31")
        self.assertTrue(all(a["cite"] for a in rec["records"]["actions"]),
                        "每筆待辦都必須帶來源句號")

    def test_assignment_subject(self):
        """『麻煩林佳蓉確認…』的主詞是被指派人, 不是說話的人。"""
        rec = self._run().records[0]
        u = {x["uid"]: x for x in rec["utterances"]}["010"]
        self.assertEqual(u["speaker"], "王小明")
        self.assertEqual(u["subject"], "林佳蓉")
        self.assertEqual(u["subject_src"], "assign")

    def test_no_cross_speaker_inheritance(self):
        """指派給別人之後, 說話者自己的下一句不可繼承成別人。"""
        rec = self._run().records[0]
        u = {x["uid"]: x for x in rec["utterances"]}["017"]
        self.assertEqual(u["subject"], "王小明")

    def test_unknown_subject_is_marked_not_guessed(self):
        rec = self._run().records[0]
        dropped = [u for u in rec["utterances"] if "drop" in u["flags"]]
        self.assertEqual(dropped[0]["subject"], mm.UNKNOWN)

    def test_agenda_coverage_reports_undiscussed(self):
        rec = self._run().records[0]
        self.assertIn("下季新片排程", rec["audit"]["not_discussed"])

    def test_timeline_gap_detected(self):
        rec = self._run().records[0]
        self.assertEqual(len(rec["audit"]["gaps"]), 1)
        self.assertGreater(rec["audit"]["gaps"][0]["seconds"], 90)

    def test_missing_due_becomes_pending_not_dropped(self):
        rec = self._run().records[0]
        incomplete = rec["audit"]["incomplete_actions"]
        self.assertTrue(incomplete, "缺期限的待辦必須被標為待確認")
        self.assertEqual(len(rec["records"]["actions"]), 4, "缺欄位不得導致待辦消失")

    def test_dry_run_writes_nothing(self):
        self._run(commit=False)
        self.assertFalse(self.ws.minutes_ledger.exists(), "dry-run 不得落帳")
        self.assertFalse(list(self.ws.reports.glob("*.md")), "dry-run 不得寫 markdown")


# ---------------------------------------------------------------- 閉環 ------


class TestClosedLoop(TempWS):
    """收信 -> 判讀 -> 抽任務 -> 催辦 -> 回覆 -> 收口, 走完一整圈。"""

    def _seed(self):
        vmt_outlook_intake.run(self.ws, "sample", commit=True, no_open=True)
        vmt_ai_triage.run(self.ws, commit=True, no_open=True)
        mm.run(self.ws, SAMPLES / "sample_transcript.json", dict(self.cfg),
               commit=True, no_open=True)
        vmt_extract_tasks.run(self.ws, "我", commit=True, no_open=True)

    def test_tasks_created_with_provenance(self):
        self._seed()
        tasks = ssot.load_tasks(self.ws)
        self.assertTrue(tasks)
        for t in tasks:
            self.assertIn(t["source"]["type"], ("MAIL", "MINUTES"))
            self.assertTrue(t["source"]["ref"], "任務必須帶出處")

    def test_mail_thread_becomes_one_task(self):
        """原始請求 + 逾期提醒是同一件事, 不可變成兩筆任務。"""
        self._seed()
        mail_tasks = [t for t in ssot.load_tasks(self.ws) if t["source"]["type"] == "MAIL"]
        self.assertEqual(len(mail_tasks), 1)
        self.assertEqual(mail_tasks[0]["urgency"], 5, "會話取最急的緊急度")

    def test_idempotent_rerun(self):
        self._seed()
        before = len(ssot.load_tasks(self.ws))
        self._seed()
        self.assertEqual(len(ssot.load_tasks(self.ws)), before, "重跑不得產生重複任務")

    def test_overdue_is_derived_not_stored(self):
        self._seed()
        far = ssot.derive_states(self.ws, as_of=dt.date(2027, 1, 1))
        self.assertTrue(any(s["status"] == "OVERDUE" for s in far.values()))
        near = ssot.derive_states(self.ws, as_of=dt.date(2026, 7, 1))
        self.assertFalse(any(s["status"] == "OVERDUE" for s in near.values()),
                         "逾期必須隨基準日改變, 不能是寫死的欄位")

    def test_composer_never_mails_self_or_unassigned(self):
        self._seed()
        r = vmt_mail_composer.run(self.ws, commit=True, no_open=True,
                                  as_of=dt.date(2026, 8, 2), me="我")
        for m in r.records:
            self.assertNotEqual(m["to"], "我")
            self.assertNotEqual(m["to"], ssot.UNKNOWN)
        self.assertGreater(r.counts["self"], 0, "自己的待辦應另列而非寄信")

    def test_no_double_chase_same_day(self):
        self._seed()
        as_of = dt.date(2026, 8, 2)
        first = vmt_mail_composer.run(self.ws, commit=True, no_open=True, as_of=as_of, me="我")
        second = vmt_mail_composer.run(self.ws, commit=True, no_open=True, as_of=as_of, me="我")
        self.assertGreater(first.counts["mails"], 0)
        self.assertEqual(second.counts["mails"], 0, "同一天不得重複催辦")

    def _reply(self, task_id: str, option: int, note: str = "", confirm: str = "是"):
        opts = ["[ ] 1. 已完成", "[ ] 2. 需要補資料", "[ ] 3. 需要澄清需求", "[ ] 4. 需要延長時間"]
        opts[option - 1] = opts[option - 1].replace("[ ]", "[x]")
        body = ("【追蹤編號】%s\n%s\n備註：%s\n確認：%s\n"
                % (task_id, "\n".join(opts), note, confirm))
        (self.ws.mail_inbox / ("reply_%s_%d.json" % (task_id, option))).write_text(
            json.dumps({"message_id": "R-%s-%d" % (task_id, option),
                        "subject": "回覆：追蹤 %s" % task_id,
                        "sender": "李美華", "body": body}, ensure_ascii=False),
            encoding="utf-8")
        vmt_outlook_intake.run(self.ws, "folder", commit=True, no_open=True)
        return vmt_reply_parser.run(self.ws, commit=True, no_open=True)

    def _first_task_of(self, owner: str) -> str:
        return next(t["task_id"] for t in ssot.load_tasks(self.ws) if t["owner"] == owner)

    def test_reply_option1_closes_task(self):
        self._seed()
        tid = self._first_task_of("李美華")
        r = self._reply(tid, 1, "資料已附上")
        self.assertEqual(r.counts["applied"], 1)
        self.assertEqual(ssot.derive_states(self.ws)[tid]["status"], "DONE")

    def test_reply_option1_without_confirmation_does_not_close(self):
        """勾了『已完成』但確認欄填否 -> 不收口 (刻意保守)。"""
        self._seed()
        tid = self._first_task_of("李美華")
        self._reply(tid, 1, "還在確認", confirm="否")
        self.assertNotEqual(ssot.derive_states(self.ws)[tid]["status"], "DONE")

    def test_reply_option4_without_eta_is_blocked_not_extended(self):
        self._seed()
        tid = self._first_task_of("李美華")
        self._reply(tid, 4, "供應商還沒回覆")
        st = ssot.derive_states(self.ws)[tid]
        self.assertEqual(st["status"], "BLOCKED", "沒給 ETA 就不得展延")

    def test_reply_option4_with_eta_extends_due(self):
        self._seed()
        tid = self._first_task_of("李美華")
        self._reply(tid, 4, "需要延到 2026-09-15")
        self.assertEqual(ssot.derive_states(self.ws)[tid]["due"], "2026-09-15")

    def test_unmatched_reply_is_quarantined_not_dropped(self):
        self._seed()
        vmt_reply_parser.run(self.ws, commit=True, no_open=True)   # 先消化範例中的回覆
        (self.ws.mail_inbox / "orphan.json").write_text(
            json.dumps({"message_id": "ORPHAN", "subject": "回覆：某件事",
                        "sender": "路人", "body": "[x] 1. 已完成\n確認：是\n"},
                       ensure_ascii=False), encoding="utf-8")
        vmt_outlook_intake.run(self.ws, "folder", commit=True, no_open=True)
        r = vmt_reply_parser.run(self.ws, commit=True, no_open=True)
        self.assertEqual(r.counts["unmatched"], 1)
        self.assertTrue(Quarantine(self.ws, False).open_items())

    def test_escalation_is_idempotent(self):
        self._seed()
        far = dt.date(2026, 9, 1)
        vmt_sla_engine.run(self.ws, commit=True, no_open=True, as_of=far)
        n1 = sum(1 for e in EventLog(self.ws, False).read() if e["event"] == "TASK_ESCALATED")
        vmt_sla_engine.run(self.ws, commit=True, no_open=True, as_of=far)
        n2 = sum(1 for e in EventLog(self.ws, False).read() if e["event"] == "TASK_ESCALATED")
        self.assertEqual(n1, n2, "同一級不得重複升級")

    def test_sla_never_invents_a_deadline(self):
        self._seed()
        p = vmt_sla_engine.plan(self.ws, dt.date(2026, 8, 2))
        self.assertTrue(p["needs_eta"], "無期限任務應列入索取 ETA")
        for t in ssot.load_tasks(self.ws):
            if t["due"] == ssot.UNKNOWN:
                self.assertEqual(ssot.derive_states(self.ws)[t["task_id"]]["due"],
                                 ssot.UNKNOWN, "系統不得自行填上期限")


# ---------------------------------------------------------------- 治理 ------


class TestGovernance(TempWS):
    def test_dry_run_creates_no_ledger(self):
        vmt_outlook_intake.run(self.ws, "sample", commit=False, no_open=True)
        vmt_ai_triage.run(self.ws, commit=False, no_open=True)
        self.assertFalse(self.ws.mails_ledger.exists())
        self.assertFalse(self.ws.events.exists())

    def test_dry_run_computes_whole_plan_but_writes_nothing(self):
        """dry-run 必須算得出整條管線的計畫, 否則「先看它打算做什麼」就沒有意義。"""
        cfg = json.loads((SAMPLES / "meeting_config.json").read_text(encoding="utf-8"))
        results = vmt_pipeline.run(self.ws, commit=False, no_open=True,
                                   transcript=SAMPLES / "sample_transcript.json",
                                   meeting_config=cfg, source="sample",
                                   as_of=dt.date(2026, 8, 2))
        by = {r.engine: r for r in results}
        self.assertGreater(by["vmt_extract_tasks"].counts["created"], 0,
                           "dry-run 應算出將建立哪些任務")
        self.assertGreater(by["vmt_mail_composer"].counts["mails"], 0,
                           "dry-run 應算出將寄出哪些追蹤信")
        self.assertFalse(list(self.ws.data.glob("*.jsonl")), "dry-run 不得寫任何帳本")
        self.assertFalse(list(self.ws.outbox.rglob("*.txt")), "dry-run 不得產生任何信件")

    def test_ledger_is_append_only(self):
        vmt_outlook_intake.run(self.ws, "sample", commit=True, no_open=True)
        first = self.ws.mails_ledger.read_text(encoding="utf-8")
        vmt_outlook_intake.run(self.ws, "sample", commit=True, no_open=True)
        second = self.ws.mails_ledger.read_text(encoding="utf-8")
        self.assertTrue(second.startswith(first), "既有列不得被改寫")
        self.assertEqual(first, second, "同樣輸入不得追加新列 (MD5 去重)")

    def test_quarantine_dedupes(self):
        q = Quarantine(self.ws, True)
        self.assertIsNotNone(q.hold("SRC", "LOW_CONFIDENCE", 0.2, {"a": 1}))
        self.assertIsNone(q.hold("SRC", "LOW_CONFIDENCE", 0.2, {"a": 1}))
        self.assertEqual(len(Ledger(self.ws.quarantine_ledger, False).read()), 1)

    def test_task_state_replays_from_events_only(self):
        """把 tasks.jsonl 的宣告當唯一輸入, 狀態全部由事件重算 —— 沒有可變欄位。"""
        vmt_outlook_intake.run(self.ws, "sample", commit=True, no_open=True)
        vmt_ai_triage.run(self.ws, commit=True, no_open=True)
        vmt_extract_tasks.run(self.ws, "我", commit=True, no_open=True)
        tid = ssot.load_tasks(self.ws)[0]["task_id"]
        self.assertEqual(ssot.derive_states(self.ws)[tid]["status"], "OPEN")
        EventLog(self.ws, True).emit("TASK_DONE", tid, "手動收口")
        self.assertEqual(ssot.derive_states(self.ws)[tid]["status"], "DONE")
        for t in ssot.load_tasks(self.ws):
            self.assertNotIn("status", t, "任務宣告不得帶可變狀態欄位")


# ---------------------------------------------------------------- 崩潰安全 ----


class TestDurability(TempWS):
    def test_atomic_write_roundtrip_and_backup(self):
        p = self.ws.data / "state.json"
        atomic_write_text(p, json.dumps({"v": 1}), backups=3)
        atomic_write_text(p, json.dumps({"v": 2}), backups=3)
        self.assertEqual(json.loads(p.read_text())["v"], 2)
        self.assertTrue(p.with_name("state.json.bak1").exists(), "覆寫前應留下滾動備份")

    def test_atomic_write_leaves_no_tmp(self):
        p = self.ws.data / "x.json"
        atomic_write_text(p, "{}")
        self.assertFalse(p.with_suffix(".json.tmp").exists(), "原子寫入後不得殘留 .tmp")

    def test_resilient_read_recovers_from_corrupt_main(self):
        """主檔損毀時, 自動從備份還原並回寫 —— 無資料庫狀態檔的自我修復。"""
        p = self.ws.data / "state.json"
        atomic_write_text(p, json.dumps({"good": True}), backups=3)
        atomic_write_text(p, json.dumps({"good": True, "v": 2}), backups=3)
        p.write_text("{ this is broken json", encoding="utf-8")   # 模擬斷電殘檔
        data = read_json_resilient(p, default={})
        self.assertTrue(data.get("good"), "應從 .bak 還原出健康資料")
        self.assertEqual(json.loads(p.read_text())["good"], True, "還原後應回寫主檔")


# ---------------------------------------------------------------- 專案編碼 ----


class TestProjects(TempWS):
    def _mkdirs(self, *names):
        for n in names:
            (self.ws.workspace / n).mkdir(parents=True, exist_ok=True)

    def test_dry_run_does_not_rename(self):
        self._mkdirs("日本合資案")
        vmt_projects.run(self.ws, commit=False, no_open=True)
        self.assertTrue((self.ws.workspace / "日本合資案").exists(), "dry-run 不得改資料夾")
        self.assertFalse(self.ws.projects_ledger.exists(), "dry-run 不得寫帳本")

    def test_commit_encodes_and_registers(self):
        self._mkdirs("日本合資案", "[PRJ-005] Q3預算")
        vmt_projects.run(self.ws, commit=True, no_open=True)
        names = sorted(os.path.basename(str(p)) for p in self.ws.workspace.iterdir())
        # 既有 [PRJ-005] 保留, 新資料夾從 006 起編
        self.assertIn("[PRJ-005] Q3預算", names)
        self.assertTrue(any(n.startswith("[PRJ-006]") and "日本合資案" in n for n in names))
        projects = vmt_projects.load_projects(self.ws)
        self.assertIn("[PRJ-006]", projects)

    def test_encoding_is_idempotent(self):
        self._mkdirs("德商合約談判")
        vmt_projects.run(self.ws, commit=True, no_open=True)
        n1 = len(Ledger(self.ws.projects_ledger, False).read())
        vmt_projects.run(self.ws, commit=True, no_open=True)
        n2 = len(Ledger(self.ws.projects_ledger, False).read())
        self.assertEqual(n1, n2, "重跑不得重複建檔或再次編號")

    def test_content_untouched(self):
        self._mkdirs("日本合資案")
        (self.ws.workspace / "日本合資案" / "合約.txt").write_text("v1", encoding="utf-8")
        vmt_projects.run(self.ws, commit=True, no_open=True)
        moved = next(p for p in self.ws.workspace.iterdir() if "日本合資案" in p.name)
        self.assertEqual((moved / "合約.txt").read_text(encoding="utf-8"), "v1",
                         "只改資料夾名, 內容不得被動到")

    def test_resolve_by_code_and_name(self):
        self._mkdirs("德商合約談判")
        vmt_projects.run(self.ws, commit=True, no_open=True)
        code = next(iter(vmt_projects.load_projects(self.ws)))
        self.assertEqual(vmt_projects.resolve_project(f"RE: {code} 進度", self.ws), code)
        self.assertEqual(vmt_projects.resolve_project("關於德商合約談判的狀態", self.ws), code)
        self.assertIsNone(vmt_projects.resolve_project("完全無關的信", self.ws))

    def test_tasks_inherit_project_code(self):
        """會議待辦應自動掛上對應的 [PRJ-###]。"""
        self._mkdirs("2026 年 7 月營運週會")
        vmt_projects.run(self.ws, commit=True, no_open=True)
        mm.run(self.ws, SAMPLES / "sample_transcript.json", dict(self.cfg),
               commit=True, no_open=True)
        vmt_extract_tasks.run(self.ws, "我", commit=True, no_open=True)
        minutes_tasks = [t for t in ssot.load_tasks(self.ws)
                         if t["source"]["type"] == "MINUTES"]
        self.assertTrue(minutes_tasks)
        self.assertTrue(any(t.get("project") for t in minutes_tasks),
                        "至少一筆會議任務應歸戶到專案編碼")


if __name__ == "__main__":
    unittest.main(verbosity=2)
