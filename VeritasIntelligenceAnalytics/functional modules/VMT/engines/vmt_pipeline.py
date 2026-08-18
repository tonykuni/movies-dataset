# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Pipeline Orchestrator  v1.0   --  一鍵跑完整條閉環
----------------------------------------------------------------------------
 順序 (刻意如此排):
   1 收信      intake      來源只讀 -> mails.jsonl
   2 判讀      triage      意圖 / 緊急度 / 期限 / 歸案
   3 會議      minutes     逐字稿 -> 會議記錄 (可選, 有給 --transcript 才跑)
   4 編碼      projects    workspace/ 資料夾 -> [PRJ-###] 自動編碼
   5 抽任務    extract     郵件 + 會議待辦 -> 任務台帳 (掛上 [PRJ-###])
   6 收回覆    replies     先套用回覆, 再算 SLA —— 否則剛回覆完的人會被系統催一次
   7 SLA       sla         逾期 / 升級 / 今日催辦排程
   8 產信稿    composer    有限選項追蹤信 (預設只寫檔, 不寄)
   9 總覽      dashboard   純讀推導的戰情頁

 治理: 整條管線預設 dry-run。不加 --commit 時, 每個引擎都只產報告不落帳,
       因此可以放心先跑一次看它「打算做什麼」, 確認後再 --commit。
============================================================================
"""
from __future__ import annotations
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

import sys
import json
import argparse
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vmt_ai_triage  # noqa: E402
import vmt_dashboard  # noqa: E402
import vmt_extract_tasks  # noqa: E402
import vmt_mail_composer  # noqa: E402
import vmt_meeting_minutes  # noqa: E402
import vmt_outlook_intake  # noqa: E402
import vmt_projects  # noqa: E402
import vmt_reply_parser  # noqa: E402
import vmt_sla_engine  # noqa: E402
from vmt_core import EngineResult, Workspace, banner, mode_label  # noqa: E402

ENGINE = "vmt_pipeline"
VERSION = "v1.0"


def run(ws: Workspace, commit: bool = False, no_open: bool = True,
        transcript: str | None = None, meeting_config: dict | None = None,
        source: str = "auto", use_llm: bool = False, me: str = "我",
        as_of: dt.date | None = None, draft: bool = False,
        send: bool = False, sender_name: str = "專案管理系統") -> list[EngineResult]:
    results: list[EngineResult] = []

    results.append(vmt_outlook_intake.run(ws, source, commit=commit, no_open=True))
    results.append(vmt_ai_triage.run(ws, commit=commit, use_llm=use_llm, no_open=True))

    if transcript and meeting_config is not None:
        results.append(vmt_meeting_minutes.run(ws, transcript, meeting_config,
                                               commit=commit, no_open=True))

    # 先跑專案編碼, 抽任務時才能把待辦掛到對應的 [PRJ-###]
    results.append(vmt_projects.run(ws, commit=commit, no_open=True))
    results.append(vmt_extract_tasks.run(ws, me, commit=commit, no_open=True))
    results.append(vmt_reply_parser.run(ws, commit=commit, no_open=True))
    results.append(vmt_sla_engine.run(ws, commit=commit, no_open=True, as_of=as_of))
    results.append(vmt_mail_composer.run(ws, commit=commit, no_open=True,
                                         draft=draft, send=send, as_of=as_of, me=me,
                                         sender_name=sender_name))
    results.append(vmt_dashboard.run(ws, commit=True, no_open=no_open, as_of=as_of))
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="VMT Pipeline — AI Outlook 郵箱 × 工作管理")
    ap.add_argument("--root", default=None)
    ap.add_argument("--commit", action="store_true", help="實際落帳 (預設 dry-run)")
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--source", default="auto", choices=["auto", "outlook", "folder", "sample"])
    ap.add_argument("--transcript", default=None, help="逐字稿, 有給才跑會議記錄")
    ap.add_argument("--meeting-config", default=None)
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--me", default=None)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--draft", action="store_true", help="在 Outlook 建草稿")
    ap.add_argument("--send", action="store_true", help="直接寄出 (不可逆)")
    ap.add_argument("--demo", action="store_true",
                    help="用內建範例 (範例郵件 + 範例逐字稿) 跑完整條管線")
    a = ap.parse_args()

    banner("VMT · AI Outlook 郵箱 × 工作管理系統  %s" % VERSION, mode_label(a.commit))
    if a.send and not a.commit:
        print("[拒絕] --send 必須搭配 --commit")
        return

    ws = Workspace(a.root)
    cfg = ws.load_config()
    samples = Path(__file__).resolve().parent.parent / "samples"

    transcript = a.transcript
    mcfg = None
    if a.meeting_config:
        mcfg = json.loads(Path(a.meeting_config).read_text(encoding="utf-8"))
    if a.demo:
        transcript = transcript or str(samples / "sample_transcript.json")
        mcfg = mcfg or json.loads((samples / "meeting_config.json").read_text(encoding="utf-8"))
    if transcript and mcfg is None:
        mcfg = json.loads((samples / "meeting_config.json").read_text(encoding="utf-8"))

    results = run(ws, a.commit, a.no_open, transcript, mcfg,
                  "sample" if a.demo else a.source, a.llm,
                  a.me or cfg.get("me", "我"),
                  dt.date.fromisoformat(a.as_of) if a.as_of else None,
                  a.draft, a.send, cfg.get("sender_name", "專案管理系統"))

    print("")
    print("=" * 68)
    print("  管線總結  |  %s" % mode_label(a.commit))
    print("=" * 68)
    for r in results:
        print("  %-24s %s" % (r.engine, r.summary()))
    print("")
    print("  報告目錄: %s" % ws.reports)
    print("  戰情總覽: %s" % (ws.reports / "VMT_Dashboard.html"))
    if not a.commit:
        print("")
        print("  ※ 這是 dry-run。以上全部只是計畫，未寫入任何帳本、未產生任何信件。")
        print("    確認無誤後加上 --commit 重跑。")
    print("完成.")


if __name__ == "__main__":
    main()
