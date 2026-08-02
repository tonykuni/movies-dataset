# -*- coding: utf-8 -*-
"""
============================================================================
 VMT · Core Runtime  v1.0   --  共用基座 (工作區 / 帳本 / 事件 / 治理 / 報告)
----------------------------------------------------------------------------
 定位: 「AI 高智慧自動 Outlook 郵箱及工作管理系統」的共用基座。
       所有引擎一律透過本模組讀寫資料, 治理紅線才有單一執行點。

 治理紅線 (硬性, 由本模組強制):
   - 來源只讀        : Outlook / .eml / 逐字稿 永不刪改, 只複製內容進帳本
   - 帳本 add-only   : 所有 *.jsonl 只 append, 永不 UPDATE / DELETE
   - 狀態由事件推導  : 任務狀態不落地成可變欄位, 一律 replay events.jsonl 得出
   - 預設 dry-run    : 不加 --commit 只產計畫與報告, 不落帳、不建草稿
   - 冪等            : md5 / fingerprint 去重, 同一輸入重跑不產生第二筆
   - 低信心不阻斷    : 判讀信心不足者進 Q01 隔離帳, 主線照跑

 相容: Python 3.11+；標準庫即可執行。
       選配: win32com (Outlook)、opencc (簡繁)、rapidfuzz (模糊校正)、
             本地 LLM (Ollama, 走 HTTP, 無需額外套件)
============================================================================
"""
from __future__ import annotations

import os
import re
import json
import hashlib
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

ENGINE_FAMILY = "VMT"
CORE_VERSION = "v1.0"

# ---------------------------------------------------------------- 工作區 ----


def _default_root() -> str:
    if os.name == "nt":
        return r"C:\VIA\VeritasMailTracker"
    return os.path.join(os.path.expanduser("~"), "VIA", "VeritasMailTracker")


VMT_ROOT = os.environ.get("VMT_ROOT", _default_root())


class Workspace:
    """VMT 工作區。所有路徑集中於此, 測試時只要換 root 即可完全隔離。"""

    def __init__(self, root: str | os.PathLike | None = None):
        self.root = Path(root or VMT_ROOT)

    # --- 目錄 ---
    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def reports(self) -> Path:
        return self.root / "reports"

    @property
    def outbox(self) -> Path:
        return self.root / "mails"

    @property
    def mail_inbox(self) -> Path:
        return self.root / "mail_inbox"

    @property
    def transcripts(self) -> Path:
        return self.root / "transcripts"

    # --- 帳本 (全部 add-only) ---
    @property
    def mails_ledger(self) -> Path:
        return self.data / "mails.jsonl"

    @property
    def events(self) -> Path:
        return self.data / "events.jsonl"

    @property
    def tasks_ledger(self) -> Path:
        return self.data / "tasks.jsonl"

    @property
    def triage_ledger(self) -> Path:
        return self.data / "triage.jsonl"

    @property
    def quarantine_ledger(self) -> Path:
        return self.data / "quarantine.jsonl"

    @property
    def minutes_ledger(self) -> Path:
        return self.data / "minutes.jsonl"

    @property
    def config_path(self) -> Path:
        return self.data / "vmt_config.json"

    def ensure(self) -> "Workspace":
        for d in (self.data, self.reports, self.outbox, self.mail_inbox, self.transcripts):
            d.mkdir(parents=True, exist_ok=True)
        return self

    def load_config(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        return {}


# ---------------------------------------------------------------- 小工具 ----


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def today() -> dt.date:
    return dt.date.today()


def md5_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def fingerprint(*parts: Any) -> str:
    """冪等指紋: 同樣語意的輸入 -> 同樣的 12 碼, 用來擋重複建案。"""
    raw = "\u0001".join("" if p is None else str(p).strip() for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def norm_case(s: Any) -> Optional[str]:
    """沿用 VMT v1 案號規則: 主旨含 [CASE-07] / Case 7 -> CASE-07。"""
    if not s:
        return None
    m = (re.search(r"CASE[-\s_]?0*(\d{1,3})", str(s), re.IGNORECASE)
         or re.search(r"\[\s*Case\s*0*(\d{1,3})\s*\]", str(s), re.IGNORECASE))
    return ("CASE-%02d" % int(m.group(1))) if m else None


def clip(s: Any, n: int = 120) -> str:
    t = "" if s is None else str(s).replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def banner(title: str, subtitle: str = "") -> None:
    line = "=" * 68
    print(line)
    print("  " + title)
    if subtitle:
        print("  " + subtitle)
    print(line)


def mode_label(commit: bool) -> str:
    return "COMMIT (實際落帳)" if commit else "DRY-RUN (只產計畫, 加 --commit 才落帳)"


# ---------------------------------------------------------------- 帳本 ------


def read_jsonl(path: Path) -> list[dict]:
    """讀 add-only 帳本。壞行跳過而不中斷 — 帳本永遠可讀是硬需求。"""
    out: list[dict] = []
    p = Path(path)
    if not p.exists():
        return out
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def append_jsonl(path: Path, rec: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# dry-run 的行程內暫存區 (key = 帳本絕對路徑)。
# 沒有這一層的話, dry-run 只有第一個引擎看得到東西, 後面全是 0 ——
# 而「先跑一次看它打算做什麼」正是 dry-run 存在的理由, 必須整條管線都算得出來。
_DRY_PENDING: dict[str, list[dict]] = {}


def reset_dry_run() -> None:
    """清空 dry-run 暫存 (長駐行程或連續試算時使用)。"""
    _DRY_PENDING.clear()


class Ledger:
    """
    add-only 帳本。
    commit=True  : 直接 append 到磁碟
    commit=False : 只寫進行程內暫存區, 磁碟完全不動, 但同一次執行的下游引擎讀得到,
                   因此 dry-run 能算出整條管線的完整計畫。
    """

    def __init__(self, path: Path, commit: bool = False):
        self.path = Path(path)
        self.commit = commit
        self.pending: list[dict] = []

    @property
    def _key(self) -> str:
        return str(self.path.resolve())

    def read(self) -> list[dict]:
        return read_jsonl(self.path) + _DRY_PENDING.get(self._key, [])

    def append(self, rec: dict) -> dict:
        rec = dict(rec)
        rec.setdefault("ts", now_iso())
        if self.commit:
            append_jsonl(self.path, rec)
        else:
            rec["_dry_run"] = True
            _DRY_PENDING.setdefault(self._key, []).append(rec)
        self.pending.append(rec)
        return rec


class EventLog:
    """
    事件帳 — 系統唯一的真相來源。
    任務/信件狀態一律由此 replay 推導, 因此永遠不需要 UPDATE 任何一列。
    """

    def __init__(self, ws: Workspace, commit: bool = False):
        self.ws = ws
        self.ledger = Ledger(ws.events, commit)

    def emit(self, event: str, ref: str, detail: str = "", **payload: Any) -> dict:
        rec = {"ts": now_iso(), "event": event, "ref": ref, "detail": detail}
        if payload:
            rec["payload"] = payload
        return self.ledger.append(rec)

    def read(self) -> list[dict]:
        return self.ledger.read()

    def all(self) -> list[dict]:
        """已落帳 + 本次待落帳, 依時間排序 (read() 已含 dry-run 暫存)。"""
        return sorted(self.read(), key=lambda r: r.get("ts", ""))

    @property
    def pending(self) -> list[dict]:
        return self.ledger.pending


class Quarantine:
    """Q01 隔離帳: 判讀信心不足者送這裡, 主線不阻斷 (沿用 SuperBOM 的 Q01 精神)。"""

    def __init__(self, ws: Workspace, commit: bool = False):
        self.ledger = Ledger(ws.quarantine_ledger, commit)
        self._held: set[str] | None = None

    def hold(self, source: str, reason_code: str, confidence: float,
             raw: Any, ref: str = "") -> Optional[dict]:
        """
        送 Q01 隔離。同一個 q_uid 只留一列 —— 隔離帳每跑一次就長一列的話,
        「待人工處理」的數字會虛胖, 真正該看的東西反而被淹掉。
        回傳 None 表示先前已隔離過 (本次不算新增)。
        """
        q_uid = fingerprint(source, reason_code, json.dumps(raw, ensure_ascii=False, default=str))
        if self._held is None:
            self._held = {r.get("q_uid") for r in self.ledger.read()}
        if q_uid in self._held:
            return None
        self._held.add(q_uid)
        return self.ledger.append({
            "q_uid": q_uid, "source": source, "reason_code": reason_code,
            "confidence": round(float(confidence), 3), "ref": ref,
            "raw": raw, "resolved": False,
        })

    def open_items(self) -> list[dict]:
        rows = self.ledger.read()
        resolved = {r["q_uid"] for r in rows if r.get("event") == "RESOLVED"}
        return [r for r in rows if r.get("q_uid") not in resolved and not r.get("resolved")]

    @property
    def pending(self) -> list[dict]:
        return self.ledger.pending


def next_serial(prefix: str, existing: Iterable[str], width: int = 4) -> str:
    """
    由帳本既有 ID 推導下一號, 不使用可變 counter 檔 —
    counter 檔一旦與帳本不同步就會發號重複, 這是 add-only 系統的常見破口。
    """
    hi = 0
    pat = re.compile(r"^%s-(\d+)$" % re.escape(prefix))
    for e in existing:
        m = pat.match(str(e or ""))
        if m:
            hi = max(hi, int(m.group(1)))
    return "%s-%0*d" % (prefix, width, hi + 1)


# ---------------------------------------------------------------- 本地 LLM --


class LocalLLM:
    """
    選配的本地 LLM (預設 Ollama)。無法連線時所有引擎自動退回規則判讀,
    因此本系統在完全離線、無模型的機器上仍可完整跑完 — 這是刻意的設計。
    """

    def __init__(self, endpoint: str | None = None, model: str | None = None, timeout: int = 60):
        self.endpoint = (endpoint or os.environ.get("VMT_LLM_ENDPOINT")
                         or "http://localhost:11434/api/generate")
        self.model = model or os.environ.get("VMT_LLM_MODEL") or "qwen3"
        self.timeout = timeout
        self._checked: Optional[bool] = None

    def available(self) -> bool:
        if self._checked is None:
            self._checked = self.ask("ping", timeout=3) is not None
        return self._checked

    def ask(self, prompt: str, timeout: int | None = None, json_mode: bool = False) -> Optional[str]:
        import urllib.request

        body = json.dumps({
            "model": self.model, "prompt": prompt, "stream": False,
            **({"format": "json"} if json_mode else {}),
        }).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8")).get("response")
        except Exception:
            return None

    def ask_json(self, prompt: str) -> Optional[dict]:
        raw = self.ask(prompt, json_mode=True)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            m = re.search(r"\{.*\}", raw, re.S)
            try:
                return json.loads(m.group(0)) if m else None
            except Exception:
                return None


# ---------------------------------------------------------------- 報告 ------
# Visual Lock: 沿用 VMT / SuperBOM 既有報告樣式, 讓整個 VIA 系列外觀一致。

URG_HEX = {5: "#b5443a", 4: "#d08343", 3: "#c9a13a", 2: "#7ba86a", 1: "#4d8f63"}
URG_EMOJI = {5: "\U0001F534", 4: "\U0001F7E0", 3: "\U0001F7E1", 2: "\U0001F7E2", 1: "\U0001F7E9"}
STATUS_HEX = {
    "OPEN": "#4c78a8", "ACK": "#439a9a", "IN_PROGRESS": "#c9a13a",
    "BLOCKED": "#b5443a", "OVERDUE": "#b5443a", "DONE": "#5a9e6f",
    "CANCELLED": "#8a857c", "PENDING": "#8a857c",
}

_REPORT_CSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--teal:#439a9a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#439a9a;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}
.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 20px;min-width:150px}
.cv{font-size:24px;font-weight:700}.cn{font-size:12px;color:#777;margin-top:2px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden;margin-top:6px}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair);vertical-align:top}
tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px;white-space:nowrap}
.empty{color:#999;text-align:center}
.mono{font-family:"DM Mono",monospace;font-size:12px;color:#666}
.gov{background:#f0f6f4;border:1px solid #cfe3dc;border-left:5px solid #439a9a;border-radius:3px;padding:10px 14px;font-size:12px;color:#2f5d52;margin-bottom:14px}
.dry{background:#fdf6ec;border:1px solid #f0dcc0;border-left:5px solid #d08343;border-radius:3px;padding:10px 14px;font-size:12px;color:#7a5326;margin-bottom:14px}
.cite{font-family:"DM Mono",monospace;font-size:11px;color:#8a857c}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
"""


def esc(s: Any) -> str:
    return ("" if s is None else str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pill(text: Any, color: str) -> str:
    return "<span class='pill' style='background:%s'>%s</span>" % (color, esc(text))


def kpi_cards(items: list[tuple[str, Any, str]]) -> str:
    return "<div class='cards'>%s</div>" % "".join(
        "<div class='card'><div class='cv' style='color:%s'>%s</div><div class='cn'>%s</div></div>"
        % (c, esc(v), esc(n)) for n, v, c in items)


def table(headers: list[str], rows: list[list[str]], empty: str = "無資料") -> str:
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    if not rows:
        body = "<tr><td colspan='%d' class='empty'>%s</td></tr>" % (len(headers), esc(empty))
    else:
        body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return "<table><tr>%s</tr>%s</table>" % (head, body)


def render_report(out_path: Path, seal: str, title: str, subtitle: str,
                  gov: str, sections: list[tuple[str, str]],
                  footer: str, commit: bool = True) -> Path:
    """產出 Visual Lock 報告。dry-run 會在頁首顯著標示, 避免誤讀成已生效。"""
    dry = "" if commit else (
        "<div class='dry'>DRY-RUN：本報告只是<strong>計畫</strong>，尚未落帳、未建立任何草稿。"
        "確認內容無誤後加上 <code>--commit</code> 重跑才會實際寫入。</div>")
    body = "".join("<h2>%s</h2>%s" % (esc(t), html) for t, html in sections)
    page = (
        "<!DOCTYPE html><html lang=\"zh-Hant\"><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>%s</title><style>%s</style></head><body>"
        "<header><div class=\"seal\">%s</div><div><h1>%s</h1><div class=\"sub\">%s</div></div></header>"
        "<div class=\"strip\"></div>%s<div class='gov'>%s</div>%s<footer>%s</footer></body></html>"
    ) % (esc(title), _REPORT_CSS, esc(seal), esc(title),
         esc("%s | %s" % (dt.datetime.now().strftime("%Y/%m/%d %H:%M"), subtitle)),
         dry, gov, body, esc(footer))
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page, encoding="utf-8")
    return p


def try_open(path: Path, no_open: bool = False) -> None:
    if no_open or os.name != "nt":
        return
    try:
        os.startfile(str(path))  # noqa: F821  (Windows only)
    except Exception:
        pass


# ---------------------------------------------------------------- 通用 CLI --


def add_common_args(ap) -> None:
    ap.add_argument("--root", default=None, help="VMT 工作區 (預設 $VMT_ROOT)")
    ap.add_argument("--commit", action="store_true", help="實際落帳 (預設 dry-run 只產計畫)")
    ap.add_argument("--no-open", action="store_true", help="不自動開啟報告")


@dataclass
class EngineResult:
    """所有引擎的統一回傳格式, 讓 vmt_pipeline 可以無腦串接。"""
    engine: str
    ok: bool = True
    counts: dict = field(default_factory=dict)
    records: list = field(default_factory=list)
    report: Optional[str] = None
    notes: list = field(default_factory=list)

    def summary(self) -> str:
        return "%s: %s" % (self.engine, ", ".join("%s=%s" % kv for kv in self.counts.items()) or "—")
