"""Smoke tests for Mail Tracker V2 pipeline."""

from __future__ import annotations

from mail_tracker_v2 import mail_tracker_v2


def test_sample_risk_email():
    sample = {
        "sender": "rd_lead@example.com",
        "receiver": "pm@example.com",
        "subject": "P2382 risk on validation schedule",
        "body": "We see potential risk and delay on validation phase.",
        "timestamp": "2026-08-25 16:50",
    }
    result = mail_tracker_v2(sample)

    assert "UID" in result and len(result["UID"]) == 16
    assert result["Semantic"]["category"] == "Risk"
    assert result["Semantic"]["risk_level"] >= 7
    assert result["Project"]["project"] == "P2382"
    assert result["Dept"]["dept"] == "RD"
    assert result["Task"]["status"] == "Pending"
    assert result["Task"]["priority"] == "P0"
    assert result["SLA"] == "4h"


def test_unknown_project_action():
    sample = {
        "sender": "ops.user@example.com",
        "receiver": "team@example.com",
        "subject": "Weekly status",
        "body": "All green.",
        "timestamp": "2026-08-25 10:00",
    }
    result = mail_tracker_v2(sample)
    assert result["Semantic"]["category"] in {"Action", "Decision", "Issue", "Delay", "Risk", "Escalation"}
    assert "UID" in result
