#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ThreeDayLock v0100 — 三日進度:實測成功鎖住 · 未完成照實分類 · 出 HTML U/I
(操作員 2026-11-08 令「讀取進三日進度 · 實際測成成功部分記錄鎖住 · 未完成者持續做到完成 · 自動完成並跳出 HTML U/I」)

只讀:不改他系統正本 / 冊 / 號 / 檔;只寫自己的鎖冊與自己的 HTML。

鎖的門檻不放寬 —— 四個條件全要:
  schema == VIA.Handoff.TestReceipt.v1 · rc == 0 · target_marker_seen == True · 有 completed_at 與 log_sha256
鎖住的是 (case, log_sha256) 這一對。下一輪同案 log_sha256 變了 = REGRESSED;案不見了 = GONE。
不靠記憶、不靠對話,只靠收據。

未鎖住的案「為什麼沒完成」一律由**日誌裡真的出現過的字**判定(案名會騙人,所以不看案名);
認不出來就寫 UNKNOWN 留白,不硬歸類、不寫成成功。

動詞:
  scan      三日視窗盤點,只印不寫
  lock      把綠的寫進鎖冊(add-only:實質沒變就不出新版號;不覆蓋已發布版號)
  verify    拿鎖冊比現況:LOCKED_OK / REGRESSED / GONE / NEW_GREEN
  ui        產 HTML U/I(Atlas --vl-* 視覺鎖定)
  all       scan → lock → verify → ui(--apply 才真的寫鎖冊)
  --selftest 自測
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "VIA.ThreeDayLock.v1"
HERE = Path(__file__).resolve().parent              # docs/handoff/ai
HANDOFF = HERE.parent                               # docs/handoff
VIA = HANDOFF.parent.parent                         # VeritasIntelligenceAnalytics
EVIDENCE = HANDOFF / "evidence"
LOCK_DIR = HERE
LOCK_STEM = "VIA_ThreeDayLock_v"
UI_NAME = "VIA_ThreeDayLock_UI.html"

RECEIPT_SCHEMA = "VIA.Handoff.TestReceipt.v1"
WINDOW_DAYS = 3

# 車道判定(路徑 → 系統);五系統對等獨立,只分類不代修
LANES = (
    ("functional modules/VRN/", "VRN-2"),
    ("functional modules/VDF/", "VDF"),
    ("functional modules/VQG/", "VQG"),
    ("functional modules/VAP/", "VAP"),
    ("supportive modules/registry/", "VCGC"),
    ("supportive modules/", "VCGC"),
    ("docs/", "docs"),
)

BLOCK_KINDS = {
    "ENV_PKG": "容器缺套件(只能經 VCGC via-envgov tools --apply --approve,不 pip)",
    "NO_PWSH": "容器沒有 pwsh(PS 側交叉讀法做不到,非程式錯)",
    "NET_GATE": "要觸網同意閘(VIA_NET_CONSENT + VIA_SCRAPE_CONSENT,不代設)",
    "DESKTOP": "要桌機(Remote Control 未供出資料夾)",
    "FROZEN": "凍結來源(已鎖成功來源維持原樣,不改)",
    "OPERATOR": "要操作員裁定",
    "NO_LOG": "沒有日誌可讀 —— 不歸類,照實記",
    "UNKNOWN": "日誌裡沒有可認的訊號 —— 不猜,留白待查",
}

# 日誌真訊號 → 阻塞類別。順序有意義:先認最具體的。
LOG_SIGNALS = (
    (re.compile(r"No module named ['\"]([A-Za-z0-9_.]+)['\"]"), "ENV_PKG"),
    (re.compile(r"ModuleNotFoundError"), "ENV_PKG"),
    # 有些工具不丟 ModuleNotFoundError,而是自己印「缺核心套件 X —— 不代裝」
    (re.compile(r"缺(核心)?套件\s*([A-Za-z0-9_.\-]+)"), "ENV_PKG"),
    (re.compile(r"\[ABSENT\].*(缺|不代裝)"), "ENV_PKG"),
    (re.compile(r"pwsh\s*不在|PS 讀法 pwsh|pwsh.*not found"), "NO_PWSH"),
    (re.compile(r"VIA_NET_CONSENT|VIA_SCRAPE_CONSENT|同意閘(未開|關)|DENY"), "NET_GATE"),
    (re.compile(r"Remote Control|C:\\Users|桌機(未|沒)"), "DESKTOP"),
    (re.compile(r"frozen|凍結"), "FROZEN"),
    (re.compile(r"待操作員|候裁|操作員裁"), "OPERATOR"),
)


# ─────────────────────────────────────────────── 小工具
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def lane_of(path: str) -> str:
    p = path.replace("VeritasIntelligenceAnalytics/", "", 1)
    for pref, lane in LANES:
        if p.startswith(pref):
            return lane
    return "其他"


def git(*args: str) -> str:
    """只讀 git;失敗回空字串(誠實,不炸)"""
    try:
        r = subprocess.run(["git", *args], cwd=str(VIA.parent),
                           capture_output=True, text=True, timeout=120)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def window_since() -> str:
    """三日視窗起點 = git 最新提交日 − (WINDOW_DAYS-1) 天。
    刻意不用機器當下時間,否則同一份收據隔天重跑就對不上。"""
    head = git("log", "-1", "--date=short", "--pretty=%ad").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", head or ""):
        return ""
    from datetime import date, timedelta
    y, m, d = (int(x) for x in head.split("-"))
    return (date(y, m, d) - timedelta(days=WINDOW_DAYS - 1)).isoformat()


# ─────────────────────────────────────────────── 收據
def read_receipts() -> tuple[list[dict], list[dict]]:
    """回 (綠, 非綠)。綠的門檻一字不放寬。"""
    green: list[dict] = []
    other: list[dict] = []
    if not EVIDENCE.is_dir():
        return green, other
    for f in sorted(EVIDENCE.glob("*.json")):
        case = f.stem
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            other.append({"case": case, "why": f"收據讀不懂:{str(e)[:50]}",
                          "rc": None, "marker": None, "schema": None})
            continue
        rc, mk = d.get("rc"), d.get("target_marker_seen")
        sch, log_sha = d.get("schema"), d.get("log_sha256") or ""
        done = (d.get("completed_at") or "")[:19]
        row = {"case": case, "rc": rc, "marker": bool(mk), "schema": sch,
               "completed_at": done, "log_sha256": log_sha,
               "command": " ".join(d.get("command") or [])[:200]}
        if sch == RECEIPT_SCHEMA and rc == 0 and mk and done and log_sha:
            green.append(row)
        else:
            miss = []
            if sch != RECEIPT_SCHEMA:
                miss.append(f"schema={sch}")
            if rc != 0:
                miss.append(f"rc={rc}")
            if not mk:
                miss.append("標記沒印")
            if not done:
                miss.append("無 completed_at")
            if not log_sha:
                miss.append("無 log_sha256")
            row["why"] = " · ".join(miss)
            other.append(row)
    return green, other


def log_tail(case: str, nbytes: int = 20000) -> str:
    """讀該案日誌尾段(唯讀)。沒有日誌回空字串 —— 誠實,不猜。"""
    f = EVIDENCE / f"{case}.txt"
    if not f.is_file():
        return ""
    try:
        return f.read_bytes()[-nbytes:].decode("utf-8", "replace")
    except Exception:
        return ""


def classify_block(case: str, why: str) -> tuple[str, str]:
    """回 (類別, 逐字證據)。只看日誌真訊號,不看案名。"""
    tail = log_tail(case)
    text = tail + "\n" + (why or "")
    for rx, kind in LOG_SIGNALS:
        m = rx.search(text)
        if m:
            line = ""
            for ln in text.splitlines():
                if rx.search(ln):
                    line = ln.strip()[:160]
                    break
            return kind, line or m.group(0)[:160]
    if not tail:
        return "NO_LOG", "沒有日誌檔可讀(照實記,不歸類)"
    return "UNKNOWN", (why or "")[:160]


# ─────────────────────────────────────────────── 三日提交
def window_commits(since: str) -> dict:
    if not since:
        return {"since": "", "by_day": {}, "total": 0, "by_lane": {}, "files": 0}
    by_day: dict[str, int] = {}
    for line in git("log", f"--since={since} 00:00", "--date=short",
                    "--pretty=%ad").splitlines():
        line = line.strip()
        if line:
            by_day[line] = by_day.get(line, 0) + 1
    by_lane: dict[str, int] = {}
    nfiles = 0
    for line in git("log", f"--since={since} 00:00", "--name-only",
                    "--pretty=format:").splitlines():
        line = line.strip()
        if not line:
            continue
        nfiles += 1
        lane = lane_of(line)
        by_lane[lane] = by_lane.get(lane, 0) + 1
    return {"since": since, "by_day": dict(sorted(by_day.items())),
            "total": sum(by_day.values()),
            "by_lane": dict(sorted(by_lane.items(), key=lambda kv: -kv[1])),
            "files": nfiles}


# ─────────────────────────────────────────────── 鎖冊
def lock_versions() -> list[Path]:
    return sorted(LOCK_DIR.glob(LOCK_STEM + "*.json"))


def lock_tail() -> Path | None:
    v = lock_versions()
    return v[-1] if v else None


def next_lock_path() -> Path:
    v = lock_versions()
    if not v:
        return LOCK_DIR / (LOCK_STEM + "0100.json")
    m = re.search(r"_v(\d{4})\.json$", v[-1].name)
    n = int(m.group(1)) + 1 if m else 100
    return LOCK_DIR / f"{LOCK_STEM}{n:04d}.json"


def substance(book: dict) -> str:
    """實質 = 鎖了哪些 (case, log_sha256);時間戳與敘述不算,免得每跑一次就出新版號"""
    rows = sorted((r["case"], r["log_sha256"]) for r in book.get("locked", []))
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def build_lock(green: list[dict], other: list[dict], commits: dict) -> dict:
    return {
        "schema": SCHEMA,
        "measured_at": now_utc(),
        "measured_by": ("容器實跑 VIA_ThreeDayLock_v0100 · HEAD "
                        + (git("rev-parse", "--short", "HEAD").strip() or "?")),
        "window": {"since": commits.get("since", ""), "days": WINDOW_DAYS},
        "rule": ("鎖住的是 (case, log_sha256)。門檻:schema=VIA.Handoff.TestReceipt.v1 且 rc==0 且 "
                 "target_marker_seen==True 且有 completed_at 與 log_sha256。下一輪同案 log_sha256 變了 "
                 "= REGRESSED;案不見了 = GONE。只增不減:撤鎖要寫 revoked_at。"),
        "locked": [{"case": r["case"], "log_sha256": r["log_sha256"],
                    "completed_at": r["completed_at"], "revoked_at": None}
                   for r in sorted(green, key=lambda x: x["case"])],
        "not_locked": [
            {"case": r["case"], "why": r.get("why", ""),
             "block": classify_block(r["case"], r.get("why", ""))[0],
             "block_evidence": classify_block(r["case"], r.get("why", ""))[1]}
            for r in sorted(other, key=lambda x: x["case"])],
        "commits": commits,
    }


def cmd_lock(apply_: bool) -> tuple[int, dict, str]:
    green, other = read_receipts()
    book = build_lock(green, other, window_commits(window_since()))
    tail = lock_tail()
    if tail:
        try:
            prev = json.loads(tail.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        if substance(prev) == substance(book):
            return 0, book, f"不動({tail.name} 實質沒變:鎖 {len(book['locked'])} 案)"
        if not apply_:
            return 0, book, f"乾跑:實質變了 → 要 --apply 才寫 {next_lock_path().name}"
        nxt = next_lock_path()
        if nxt.exists():
            return 1, book, f"拒寫:{nxt.name} 已存在(版本律:不覆蓋已發布)"
        book["prior"] = tail.name
        nxt.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0, book, f"已寫 {nxt.name}(鎖 {len(book['locked'])} 案)"
    if not apply_:
        return 0, book, f"乾跑:還沒有鎖冊 → 要 --apply 才寫 {next_lock_path().name}"
    nxt = next_lock_path()
    nxt.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0, book, f"已寫 {nxt.name}(首版 · 鎖 {len(book['locked'])} 案)"


def cmd_verify() -> tuple[int, dict]:
    """拿鎖冊比現況。

    四種結果,**REGRESSED 的定義很窄**:只有「本來綠、現在不綠」才算回歸。
      LOCKED_OK  還是綠,而且 log_sha256 一模一樣
      REFRESHED  還是綠,但 log_sha256 變了 —— 重跑過而已(日誌帶時戳,每跑必變)。
                 **不是回歸**,不給紅;鎖冊下次寫就會自動收下新指紋。
      REGRESSED  收據還在,但已經不綠了(rc != 0 或標記沒印)→ 真回歸,紅。
      GONE       收據整個不見了 → 紅。
    """
    tail = lock_tail()
    green, other = read_receipts()
    now = {r["case"]: r["log_sha256"] for r in green}
    not_green = {r["case"]: r.get("why", "") for r in other}
    out: dict = {"locked_ok": [], "refreshed": [], "regressed": [], "gone": [],
                 "new_green": [], "book": None}
    if not tail:
        out["new_green"] = sorted(now)
        return 0, out
    out["book"] = tail.name
    try:
        prev = json.loads(tail.read_text(encoding="utf-8"))
    except Exception as e:
        out["error"] = f"鎖冊讀不懂:{str(e)[:60]}"
        return 1, out
    locked = {r["case"]: r["log_sha256"] for r in prev.get("locked", [])
              if not r.get("revoked_at")}
    for case, sha in sorted(locked.items()):
        if case in now:
            if now[case] == sha:
                out["locked_ok"].append(case)
            else:
                out["refreshed"].append({"case": case, "locked": sha[:12],
                                         "now": now[case][:12]})
        elif case in not_green:
            out["regressed"].append({"case": case, "locked": sha[:12],
                                     "why": not_green[case][:120]})
        else:
            out["gone"].append(case)
    out["new_green"] = sorted(set(now) - set(locked))
    return (1 if (out["regressed"] or out["gone"]) else 0), out


# ─────────────────────────────────────────────── HTML U/I(Atlas --vl-* 視覺鎖定)
VL = """:root{color-scheme:light;
--vl-bg:#f2f1ec;--vl-row:#ebe9e3;--vl-white:#fff;--vl-ink:#33403f;--vl-title:#1b1a17;--vl-muted:#6b6860;
--vl-border:#dbd9d3;--vl-border-soft:#dcdad3;--vl-success:#3d7a52;--vl-success-bg:#e6efec;--vl-success-ink:#2c4f4a;
--vl-warning-bg:#f2ecdd;--vl-warning-ink:#6f5c31;--vl-danger-bg:#f3e7e6;--vl-danger-ink:#9e2b25;
--vl-font-cjk:"Microsoft JhengHei","Segoe UI",sans-serif;--vl-font-display:"Cormorant Garamond",Georgia,serif;
--vl-font-mono:Consolas,ui-monospace,monospace;--vl-size-base:clamp(9.5px,1.05vw,11px);--vl-size-label:9px;
--vl-size-numeric:9.5px;--vl-size-primary:11px;--vl-size-status:8px;--vl-size-title:19px}"""


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_ui(book: dict, ver: dict) -> str:
    def lamp(kind: str, text: str) -> str:
        return f'<span class="lamp {kind}">{esc(text)}</span>'

    nlock = len(book["locked"])
    nnot = len(book["not_locked"])
    c = book["commits"]
    red = bool(ver["regressed"] or ver["gone"])
    agg = "RED" if red else ("GREEN" if nlock else "GRAY")
    agg_l = {"RED": "r", "GREEN": "g", "GRAY": "n"}[agg]

    rows_lane = "".join(f'<tr><td>{esc(k)}</td><td class="num">{v}</td></tr>'
                        for k, v in c["by_lane"].items())
    rows_day = "".join(f'<tr><td class="c">{esc(k)}</td><td class="num">{v}</td></tr>'
                       for k, v in c["by_day"].items())

    by_block: dict[str, list[dict]] = {}
    for r in book["not_locked"]:
        by_block.setdefault(r["block"], []).append(r)
    rows_block = ""
    for k in sorted(by_block, key=lambda x: -len(by_block[x])):
        items = by_block[k]
        names = " · ".join(sorted(x["case"] for x in items))
        ev = next((x["block_evidence"] for x in items if x.get("block_evidence")), "")
        rows_block += (f'<tr><td class="c">{esc(k)}</td><td class="num">{len(items)}</td>'
                       f'<td>{esc(BLOCK_KINDS.get(k, k))}</td>'
                       f'<td class="mono small">{esc(names)}</td>'
                       f'<td class="mono small">{esc(ev)}</td></tr>')

    if red:
        reg = "".join(f'<tr><td class="c">{esc(r["case"])}</td>'
                      f'<td class="c">{esc(r["locked"])}…</td>'
                      f'<td>{esc(r.get("why", ""))}</td></tr>' for r in ver["regressed"])
        gone = "".join(f'<tr><td class="c">{esc(g)}</td><td colspan="2">GONE:鎖住的案不見了</td></tr>'
                       for g in ver["gone"])
        reg_block = ('<h2>④ 回歸 REGRESSED / 消失 GONE</h2><div class="tw"><table><thead><tr>'
                     '<th>案</th><th>鎖住時 log_sha</th><th>現在怎麼了</th></tr></thead><tbody>'
                     + reg + gone + '</tbody></table></div>')
    else:
        reg_block = ('<h2>④ 回歸</h2><p>' + lamp("g", "無回歸")
                     + f' 鎖冊 {esc(ver.get("book") or "(首次)")} 比對:'
                       f'LOCKED_OK <b>{len(ver["locked_ok"])}</b> · '
                       f'REFRESHED <b>{len(ver["refreshed"])}</b>(重跑過仍綠,不算回歸)· '
                       f'REGRESSED <b>0</b> · GONE <b>0</b> · '
                       f'新綠 <b>{len(ver["new_green"])}</b></p>')

    locked_names = " · ".join(r["case"] for r in book["locked"])

    return f"""<title>三日進度鎖</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
{VL}
*{{box-sizing:border-box}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);font-size:var(--vl-size-base);line-height:1.55;margin:0}}
.wrap{{max-width:1180px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:18px 44px}}
h1,h2{{margin:0;color:var(--vl-title);text-wrap:balance}}
h2{{font-size:13px;margin-block:26px 8px;padding-bottom:5px;border-bottom:1px solid var(--vl-border)}}
.mono{{font-family:var(--vl-font-mono)}} .small{{font-size:var(--vl-size-status)}}
header{{background:var(--vl-white);border:1px solid var(--vl-border);padding:14px 16px}}
header .nm{{font-family:var(--vl-font-display);font-size:var(--vl-size-title);color:var(--vl-title);font-weight:600}}
header .sep{{color:var(--vl-border)}}
header .sub{{margin-top:8px;font-size:var(--vl-size-numeric);color:var(--vl-muted);font-family:var(--vl-font-mono);word-break:break-all}}
.lamp{{display:inline-block;font-size:var(--vl-size-status);letter-spacing:.1em;padding:2px 7px;border:1px solid;white-space:nowrap}}
.g{{background:var(--vl-success-bg);color:var(--vl-success-ink);border-color:var(--vl-success)}}
.y{{background:var(--vl-warning-bg);color:var(--vl-warning-ink);border-color:#c9b183}}
.r{{background:var(--vl-danger-bg);color:var(--vl-danger-ink);border-color:#c08a86}}
.n{{background:var(--vl-row);color:var(--vl-muted);border-color:var(--vl-border)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:12px}}
.card{{background:var(--vl-white);border:1px solid var(--vl-border);padding:12px 14px;min-width:0}}
.card .l{{font-size:var(--vl-size-label);letter-spacing:.09em;text-transform:uppercase;color:var(--vl-muted)}}
.card .v{{font-family:var(--vl-font-display);font-size:27px;color:var(--vl-title);line-height:1.1;margin-top:5px}}
.tw{{overflow-x:auto;border:1px solid var(--vl-border);background:var(--vl-white)}}
table{{border-collapse:collapse;width:100%;font-size:var(--vl-size-numeric)}}
th,td{{border-bottom:1px solid var(--vl-border-soft);padding:5px 8px;text-align:left;vertical-align:top}}
thead th{{background:var(--vl-row);color:var(--vl-title);font-size:var(--vl-size-label);letter-spacing:.07em;text-transform:uppercase;white-space:nowrap}}
tbody tr:nth-child(even){{background:#faf9f6}}
td.c{{font-family:var(--vl-font-mono);white-space:nowrap}}
td.num,th.num{{text-align:right;font-family:var(--vl-font-mono)}}
.note{{margin-top:7px;font-size:var(--vl-size-numeric);color:var(--vl-muted)}}
p{{margin:6px 0 0}}
footer{{margin-top:30px;padding-top:10px;border-top:1px solid var(--vl-border);font-size:var(--vl-size-numeric);color:var(--vl-muted)}}
</style>
<div class="wrap">
<header>
  <div><span class="nm">VIA-THREEDAYLOCK</span> <span class="sep">·</span>
  <span class="mono">{esc(book['measured_at'])}</span> <span class="sep">·</span>
  {lamp('g','READ-ONLY')} <span class="sep">·</span> {lamp(agg_l, '總燈 ' + agg)}</div>
  <div class="sub">視窗 {esc(c['since'])} → HEAD · {WINDOW_DAYS} 日 · {esc(book['measured_by'])}</div>
</header>

<h2>① 三日進度</h2>
<div class="cards">
  <div class="card"><div class="l">提交</div><div class="v">{c['total']}</div></div>
  <div class="card"><div class="l">改檔次</div><div class="v">{c['files']}</div></div>
  <div class="card"><div class="l">鎖住的實測成功</div><div class="v">{nlock}</div></div>
  <div class="card"><div class="l">還沒鎖住</div><div class="v">{nnot}</div></div>
</div>
<div class="cards" style="margin-top:12px">
  <div><div class="tw"><table><thead><tr><th>日</th><th class="num">提交</th></tr></thead><tbody>{rows_day}</tbody></table></div></div>
  <div><div class="tw"><table><thead><tr><th>系統 / 區</th><th class="num">檔次</th></tr></thead><tbody>{rows_lane}</tbody></table></div></div>
</div>
<div class="note">檔次是「提交 × 檔」的累計,同一檔改兩次算兩次。某系統 0 檔就照實是 0 —— 不補、不美化。</div>

<h2>② 鎖住的是什麼(門檻不放寬)</h2>
<p>{esc(book['rule'])}</p>
<p class="note">鎖住 <b>{nlock}</b> 案。案名:<span class="mono small">{esc(locked_names)}</span></p>

<h2>③ 還沒鎖住的 {nnot} 案 —— 照實分類,不寫成成功</h2>
<div class="tw"><table><thead><tr><th>阻塞</th><th class="num">案</th><th>意思</th><th>案名</th><th>日誌證據(逐字)</th></tr></thead>
<tbody>{rows_block}</tbody></table></div>
<div class="note">分類<b>只看日誌裡真的出現過的字</b>(案名會騙人,所以不看案名);認不出來寫 UNKNOWN 留白,不硬歸類。最後一欄是那一類的第一條逐字證據。黃不是綠。</div>

{reg_block}

<footer>
五系統對等獨立(L120 / L123):本頁只讀各系統自報的收據與 git 紀錄,不改他系統正本 / 冊 / 號 / 檔。<br>
鎖冊 add-only:實質(case × log_sha256)沒變就不出新版號;撤鎖要寫 <span class="mono">revoked_at</span>。<br>
視覺鎖定:VIA Atlas <span class="mono">--vl-*</span> 唯一正本,色值與字級照抄,未新增色。非投資建議。
</footer>
</div>
"""


# ─────────────────────────────────────────────── 動詞
def print_scan(book: dict, ver: dict) -> None:
    c = book["commits"]
    print(f"[三日] 視窗 {c['since']} → HEAD · 提交 {c['total']} · 改檔次 {c['files']}")
    for k, v in c["by_day"].items():
        print(f"   {k}  {v}")
    print("[分佈] " + " · ".join(f"{k} {v}" for k, v in c["by_lane"].items()))
    print(f"[鎖] 實測成功 {len(book['locked'])} 案(rc 0 + 標記見到 + 有 log_sha256)")
    by: dict[str, int] = {}
    for r in book["not_locked"]:
        by[r["block"]] = by.get(r["block"], 0) + 1
    print(f"[未鎖] {len(book['not_locked'])} 案:"
          + " · ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda kv: -kv[1])))
    for r in book["not_locked"]:
        if r["block"] in ("ENV_PKG", "NO_PWSH", "UNKNOWN", "NO_LOG"):
            print(f"   [{r['block']}] {r['case']} · {r['block_evidence'][:90]}")
    print(f"[比對] LOCKED_OK {len(ver['locked_ok'])} · REFRESHED {len(ver['refreshed'])}"
          f"(重跑過仍綠,不算回歸)· REGRESSED {len(ver['regressed'])}"
          f" · GONE {len(ver['gone'])} · 新綠 {len(ver['new_green'])}")


def cmd_ui(book: dict, ver: dict, out: Path | None = None) -> Path:
    p = out or (LOCK_DIR / UI_NAME)
    p.write_text(render_ui(book, ver), encoding="utf-8")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_ThreeDayLock_v0100", add_help=True)
    ap.add_argument("verb", nargs="?", default="all",
                    choices=["scan", "lock", "verify", "ui", "all"])
    ap.add_argument("--apply", action="store_true", help="lock 才真的寫鎖冊")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    rc_lock, book, msg = cmd_lock(a.apply if a.verb in ("lock", "all") else False)
    rc_ver, ver = cmd_verify()

    if a.verb == "scan":
        print_scan(book, ver)
        return 0
    if a.verb == "lock":
        print_scan(book, ver)
        print(f"[鎖冊] {msg}")
        return rc_lock
    if a.verb == "verify":
        print(f"[比對] 鎖冊 {ver.get('book') or '(還沒有)'}")
        print(f"   LOCKED_OK {len(ver['locked_ok'])} · REFRESHED {len(ver['refreshed'])}"
              f"(重跑過仍綠)· REGRESSED {len(ver['regressed'])}"
              f" · GONE {len(ver['gone'])} · 新綠 {len(ver['new_green'])}")
        for r in ver["refreshed"]:
            print(f"   [綠] REFRESHED {r['case']} 鎖 {r['locked']}… → 現 {r['now']}…"
                  f"(重跑過,還是綠)")
        for r in ver["regressed"]:
            print(f"   [RED] REGRESSED {r['case']} 鎖 {r['locked']}… → 已不綠:{r['why']}")
        for g in ver["gone"]:
            print(f"   [RED] GONE {g}")
        return rc_ver
    if a.verb == "ui":
        print(f"[U/I] {cmd_ui(book, ver, Path(a.out) if a.out else None)}")
        return 0

    print_scan(book, ver)
    print(f"[鎖冊] {msg}")
    print(f"[U/I] {cmd_ui(book, ver, Path(a.out) if a.out else None)}")
    agg = "RED" if (ver["regressed"] or ver["gone"] or rc_lock != 0) else "GREEN"
    print(f"[總燈] {agg}(回歸 {len(ver['regressed'])} · 消失 {len(ver['gone'])}"
          f" · 鎖冊 rc {rc_lock})")
    return 0 if agg == "GREEN" else 1


# ─────────────────────────────────────────────── 自測
def selftest() -> int:
    import tempfile
    global EVIDENCE, LOCK_DIR
    ok = fail = 0

    def chk(name, cond, note=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  [OK] {name} {note}")
        else:
            fail += 1
            print(f"  [FAIL] {name} {note}")

    chk("① schema 固定", SCHEMA == "VIA.ThreeDayLock.v1", SCHEMA)
    chk("② 門檻四條都寫在 docstring", all(x in __doc__ for x in ("rc == 0", "target_marker_seen")))

    keep_e, keep_l = EVIDENCE, LOCK_DIR
    with tempfile.TemporaryDirectory() as td:
        EVIDENCE = Path(td) / "ev"
        EVIDENCE.mkdir()
        base = {"schema": RECEIPT_SCHEMA, "rc": 0, "target_marker_seen": True,
                "completed_at": "2026-11-08T00:00:00", "log_sha256": "a" * 64}
        (EVIDENCE / "good.json").write_text(json.dumps(base), encoding="utf-8")
        for name, patch in (("bad_rc", {"rc": 1}), ("bad_marker", {"target_marker_seen": False}),
                            ("bad_schema", {"schema": "other"}), ("bad_nosha", {"log_sha256": ""}),
                            ("bad_nodone", {"completed_at": ""})):
            d = dict(base)
            d.update(patch)
            (EVIDENCE / f"{name}.json").write_text(json.dumps(d), encoding="utf-8")
        (EVIDENCE / "broken.json").write_text("{not json", encoding="utf-8")

        g, o = read_receipts()
        chk("③ 只有 good 進綠", [r["case"] for r in g] == ["good"], str([r["case"] for r in g]))
        chk("④ 五種缺項 + 壞 JSON 全進非綠且各帶理由",
            len(o) == 6 and all(r.get("why") for r in o), f"非綠 {len(o)}")
        chk("⑤ 壞 JSON 不炸、記成讀不懂", any("讀不懂" in r.get("why", "") for r in o))

        LOCK_DIR = Path(td) / "lock"
        LOCK_DIR.mkdir()
        rc1, b1, m1 = cmd_lock(True)
        t = lock_tail()
        chk("⑥ 首版寫出", rc1 == 0 and t is not None and t.name.endswith("v0100.json"), m1)
        rc2, b2, m2 = cmd_lock(True)
        chk("⑦ 實質沒變 → 不動(不出 v0101)",
            "不動" in m2 and len(lock_versions()) == 1, m2)

        d = dict(base)
        d["log_sha256"] = "b" * 64
        (EVIDENCE / "good2.json").write_text(json.dumps(d), encoding="utf-8")
        rc3, b3, m3 = cmd_lock(True)
        chk("⑧ 實質變了 → 出 v0101",
            len(lock_versions()) == 2 and lock_versions()[-1].name.endswith("v0101.json"), m3)
        chk("⑨ 新版記 prior",
            json.loads(lock_versions()[-1].read_text(encoding="utf-8")).get("prior", "")
            .endswith("v0100.json"))

        # 重跑仍綠:日誌帶時戳,log_sha256 每跑必變 —— 這**不是**回歸
        (EVIDENCE / "good.json").write_text(json.dumps({**base, "log_sha256": "c" * 64}),
                                            encoding="utf-8")
        rcv, ver = cmd_verify()
        chk("⑩ 重跑仍綠判 REFRESHED、不判 REGRESSED、rc 0",
            rcv == 0 and [r["case"] for r in ver["refreshed"]] == ["good"]
            and not ver["regressed"], f"rc={rcv} refreshed={ver['refreshed']}")
        # 真回歸:收據還在,但已經不綠(rc 1)
        (EVIDENCE / "good.json").write_text(
            json.dumps({**base, "rc": 1, "log_sha256": "c" * 64}), encoding="utf-8")
        rcv_r, ver_r = cmd_verify()
        chk("⑩b 本來綠現在不綠才判 REGRESSED 且 rc 1",
            rcv_r == 1 and [r["case"] for r in ver_r["regressed"]] == ["good"]
            and "rc=1" in ver_r["regressed"][0]["why"], str(ver_r["regressed"]))
        (EVIDENCE / "good.json").write_text(json.dumps({**base, "log_sha256": "c" * 64}),
                                            encoding="utf-8")

        (EVIDENCE / "good.json").unlink()
        rcv2, ver2 = cmd_verify()
        chk("⑪ 案不見了判 GONE 且 rc 1", rcv2 == 1 and "good" in ver2["gone"], str(ver2["gone"]))

        tp = lock_versions()[-1]
        bk = json.loads(tp.read_text(encoding="utf-8"))
        for r in bk["locked"]:
            if r["case"] == "good":
                r["revoked_at"] = "2026-11-08"
        tp.write_text(json.dumps(bk, ensure_ascii=False), encoding="utf-8")
        rcv3, ver3 = cmd_verify()
        chk("⑫ 撤鎖的案不再判 GONE", "good" not in ver3["gone"], str(ver3["gone"]))

        # 版本律防線:目標版號已存在就拒寫。寫在 next_lock_path() 的檔會立刻變成新尾版
        # (lock_versions 照檔名排序),所以這裡把 next_lock_path 暫時指向既有尾版,真的走到那條線。
        (EVIDENCE / "good3.json").write_text(json.dumps({**base, "log_sha256": "d" * 64}),
                                             encoding="utf-8")
        gl = globals()
        real_next = gl["next_lock_path"]
        existing = lock_versions()[-1]
        before = existing.read_text(encoding="utf-8")
        gl["next_lock_path"] = lambda: existing
        try:
            rc4, _, m4 = cmd_lock(True)
        finally:
            gl["next_lock_path"] = real_next
        chk("⑬ 目標版號已存在 → rc 1 拒寫", rc4 == 1 and "拒寫" in m4, m4)
        chk("⑭ 拒寫時已發布檔一字不動", existing.read_text(encoding="utf-8") == before)
        n_before = len(lock_versions())
        rc5, b5, _ = cmd_lock(False)
        chk("⑮ 乾跑不寫檔", len(lock_versions()) == n_before and rc5 == 0)

        rcv4, ver4 = cmd_verify()
        html_green = render_ui(b5, ver4)
        chk("⑯ U/I 用 Atlas --vl-* 視覺鎖定", html_green.count("--vl-") >= 20)
        chk("⑰ U/I 不含骨架標籤(Artifact 契約)",
            not any(x in html_green.lower() for x in ("<!doctype", "<html", "<body")))
        chk("⑱ 沒回歸時總燈 GREEN", ">總燈 GREEN<" in html_green)
        ver_red = {"locked_ok": [], "refreshed": [],
                   "regressed": [{"case": "x", "locked": "aaaaaaaaaaaa",
                                  "why": "rc=1 · 標記沒印"}],
                   "gone": ["y"], "new_green": [], "book": "t.json"}
        html_red = render_ui(b5, ver_red)
        chk("⑲ 有回歸就印總燈 RED,且不同時出現 GREEN 總燈",
            ">總燈 RED<" in html_red and ">總燈 GREEN<" not in html_red)
        chk("⑳ 回歸的案 · 鎖住指紋 · 不綠的理由都印在頁上(可追)",
            "aaaaaaaaaaaa" in html_red and "rc=1" in html_red and "GONE" in html_red)
        chk("㉑ U/I 逸出 HTML 特殊字元(不讓日誌內容破版)",
            "&lt;" in render_ui({**b5, "measured_by": "<img>"}, ver4))

        # 分類器:只認日誌真訊號,不看案名
        (EVIDENCE / "a.txt").write_text(
            "  [OK] 前兩檢\nModuleNotFoundError: No module named 'fitz'\n", encoding="utf-8")
        k, ev = classify_block("a", "rc=1")
        chk("㉒ 缺套件判 ENV_PKG 且帶逐字證據",
            k == "ENV_PKG" and "fitz" in ev, f"{k} · {ev[:60]}")
        (EVIDENCE / "b.txt").write_text("真樹:兩法一致 · PS 讀法 pwsh 不在(文字判讀)\n",
                                        encoding="utf-8")
        chk("㉓ pwsh 不在判 NO_PWSH", classify_block("b", "rc=1")[0] == "NO_PWSH")
        (EVIDENCE / "nlp_fetch_coverage_probe.txt").write_text(
            "ModuleNotFoundError: No module named 'fitz'\n", encoding="utf-8")
        chk("㉔ 案名含 nlp/fetch/coverage/probe 也照日誌判 ENV_PKG",
            classify_block("nlp_fetch_coverage_probe", "rc=1")[0] == "ENV_PKG")
        chk("㉕ 沒日誌判 NO_LOG,不硬歸類", classify_block("nolog_case", "rc=1")[0] == "NO_LOG")
        (EVIDENCE / "c.txt").write_text("一切正常,沒有可認訊號\n", encoding="utf-8")
        chk("㉖ 認不出來判 UNKNOWN,不猜", classify_block("c", "")[0] == "UNKNOWN")
        (EVIDENCE / "d.txt").write_text("同意閘未開,DENY 網路\n", encoding="utf-8")
        chk("㉗ 同意閘字樣判 NET_GATE", classify_block("d", "")[0] == "NET_GATE")
        (EVIDENCE / "e.txt").write_text(
            "[ABSENT] VDF_MDL008_FetchSystem v0102:本直譯器缺核心套件 yfinance —— 不代裝\n",
            encoding="utf-8")
        ke, eve = classify_block("e", "rc=3")
        chk("㉘ 自己印「缺核心套件 X」也判 ENV_PKG 且證據帶套件名",
            ke == "ENV_PKG" and "yfinance" in eve, f"{ke} · {eve[:60]}")

    EVIDENCE, LOCK_DIR = keep_e, keep_l

    chk("㉙ 車道判定", lane_of("functional modules/VRN/x.py") == "VRN-2"
        and lane_of("supportive modules/registry/y.json") == "VCGC"
        and lane_of("docs/z.md") == "docs")

    ws = window_since()
    head_day = git("log", "-1", "--date=short", "--pretty=%ad").strip()
    want = ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", head_day or ""):
        from datetime import date, timedelta
        y, m, dd = (int(x) for x in head_day.split("-"))
        want = (date(y, m, dd) - timedelta(days=WINDOW_DAYS - 1)).isoformat()
    chk("㉚ 視窗起點 = HEAD 日 − 2 天(可重現,不用機器當下時間)",
        bool(ws) and ws == want, f"ws={ws} want={want} head={head_day}")
    chk("㉛ git 壞掉回空字串不炸", git("definitely-not-a-git-verb") == "")

    # 總表行附一個「只有全過才印」且不帶檢數的結語,交接冊的成功標記釘這個 ——
    # 以後加檢也不會讓標記過期(本輪 C 的九個案就是被釘住計數害的)
    print(f"  [計] VIA_ThreeDayLock v0100 自測 OK {ok} · FAIL {fail} · "
          + ("PASS" if fail == 0 else "FAIL"))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
