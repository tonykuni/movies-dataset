"""VIS Workbench · 郵箱自動擷取（單檔貼上即跑）。

在你自己的機器上執行，自動讀取 Outlook 或 Gmail 近 N 月郵件 → 統一 Record →
寫入本機 SSOT（mail_fetched.jsonl）+ 產生 HTML 摘要。全本機、不外傳。

用法（擇一）：
  Outlook（Windows，已登入 Outlook，免密碼）：
      pip install pywin32
      python fetch_mailbox.py outlook --months 6

  Gmail（任何系統，需一次性 App Password）：
      pip install imap-tools
      python fetch_mailbox.py gmail --user you@gmail.com --token "xxxx xxxx xxxx xxxx" --days 180

  自我測試（無信箱也能看流程）：
      python fetch_mailbox.py selftest

合規：只讀你本人有權限的信箱、用你本人的認證；本機解析、不上傳；只記工作事實。
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

AUP = "本工具僅讀取您本人有權限的信箱、使用您本人的認證，於本機處理、不外傳，僅記錄工作事實。"
OUT_DIR = os.path.join(os.getcwd(), "VIA_RUNS", "mailbox")
PROFILE = os.path.join(OUT_DIR, "profile.json")          # 非機密：provider/user/期間
_SERVICE = "VIS-Workbench-mail"


# ---------- 憑證持久化（第一次存，之後這台電腦自動讀）----------
def save_token(user: str, token: str) -> str:
    """優先存進作業系統憑證保險庫(keyring)；無 keyring 才退而存受限本機檔。"""
    try:
        import keyring                       # pip install keyring（Windows 認證管理員）
        keyring.set_password(_SERVICE, user, token)
        return "keyring（作業系統憑證保險庫）"
    except Exception:
        os.makedirs(OUT_DIR, exist_ok=True)
        fp = os.path.join(OUT_DIR, ".mail_token")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(json.dumps({user: token}))
        try:
            os.chmod(fp, 0o600)              # 僅本人可讀
        except Exception:
            pass
        return f"本機受限檔 {fp}（建議改 pip install keyring 用系統保險庫）"


def load_token(user: str) -> str:
    try:
        import keyring
        t = keyring.get_password(_SERVICE, user)
        if t:
            return t
    except Exception:
        pass
    fp = os.path.join(OUT_DIR, ".mail_token")
    if os.path.exists(fp):
        try:
            return json.load(open(fp, encoding="utf-8")).get(user, "")
        except Exception:
            return ""
    return ""


def save_profile(d: dict) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(d, open(PROFILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def load_profile() -> dict:
    if os.path.exists(PROFILE):
        try:
            return json.load(open(PROFILE, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _rec_to_dict(r) -> dict:
    return {k: getattr(r, k, "") for k in
            ("title", "body", "actor", "counterparts", "event_time",
             "source_type", "source_ref", "thread_id", "raw_keys")}


# ---------- Outlook（COM，免密碼，用已登入 session）----------
def fetch_outlook(months: int = 6, include_sent: bool = True) -> list[dict]:
    import win32com.client  # pip install pywin32
    out = []
    cutoff = datetime.now() - timedelta(days=months * 31)
    app = win32com.client.Dispatch("Outlook.Application")
    ns = app.GetNamespace("MAPI")
    try:
        ns.SendAndReceive(False)   # 先逼 Outlook 與伺服器同步，避免讀到舊快取
    except Exception:
        pass
    folders = [6]                  # 6 = Inbox
    if include_sent:
        folders.append(5)          # 5 = Sent
    for fid in folders:
        try:
            items = ns.GetDefaultFolder(fid).Items
        except Exception:
            continue
        items.Sort("[ReceivedTime]", True)
        for it in items:
            try:
                rt = getattr(it, "ReceivedTime", None) or getattr(it, "SentOn", None)
                when = datetime(rt.year, rt.month, rt.day, rt.hour, rt.minute) if rt else None
                if when and when < cutoff:
                    break
                out.append({
                    "title": str(getattr(it, "Subject", "") or ""),
                    "body": str(getattr(it, "Body", "") or "")[:20000],
                    "actor": str(getattr(it, "SenderName", "") or ""),
                    "counterparts": str(getattr(it, "To", "") or "") + ";" + str(getattr(it, "CC", "") or ""),
                    "event_time": when.isoformat(timespec="seconds") if when else "",
                    "source_type": "outlook_com",
                    "source_ref": "outlook:" + str(getattr(it, "EntryID", ""))[:24],
                    "thread_id": str(getattr(it, "ConversationTopic", "") or ""),
                    "raw_keys": str(getattr(it, "Subject", "") or ""),
                })
            except Exception:
                continue
    return out


# ---------- Gmail / IMAP（App Password）----------
def fetch_imap(provider: str, user: str, token: str, days: int = 180, folder: str = "INBOX") -> list[dict]:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pmis_lite.adapters.mail_imap import MailIMAPAdapter
    ad = MailIMAPAdapter(provider=provider, user=user, token=token,
                         lookback_days=days, folder=folder)
    if not ad.available():
        raise RuntimeError("imap-tools 未安裝或認證不全：pip install imap-tools，並提供 --user/--token")
    return [_rec_to_dict(r) for r in ad.fetch()]


# ---------- 自我測試（mock，無信箱也能驗證流程）----------
def fetch_selftest() -> list[dict]:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pmis_lite.adapters.mail_imap import message_to_record

    class M:
        uid = "1"; subject = "Re: PSU 新案 LLC 效率"; from_ = "lin.pm@client.com"
        to = ("tony.h@company.com",); cc = ("rd@company.com",)
        date = datetime(2026, 6, 28, 14, 30)
        text = "如電話討論，效率目標 92%。\n\n> 上一封引文..."; html = ""
        headers = {"message-id": ["<demo@client.com>"]}
    return [_rec_to_dict(message_to_record(M()))]


# ---------- 寫入 SSOT + HTML 摘要 ----------
def write_outputs(records: list[dict], provider: str) -> tuple[str, str]:
    os.makedirs(OUT_DIR, exist_ok=True)
    jl = os.path.join(OUT_DIR, "mail_fetched.jsonl")
    with open(jl, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 摘要統計（本機規則，無 AI）
    from collections import Counter
    senders = Counter(r["actor"] for r in records if r["actor"])
    times = sorted([r["event_time"] for r in records if r["event_time"]])
    span = (times[0][:10] + " → " + times[-1][:10]) if times else "—"
    rows = "".join(
        f"<tr><td>{(r['event_time'] or '')[:16]}</td><td>{_esc(r['actor'])}</td>"
        f"<td>{_esc(r['title'][:60])}</td></tr>"
        for r in records[:50])
    top = "".join(f"<li>{_esc(s)} · {c} 封</li>" for s, c in senders.most_common(8))
    html = f"""<!doctype html><html lang="zh-TW"><meta charset="utf-8">
<title>VIS Workbench · 郵箱擷取摘要</title>
<style>body{{font-family:'DM Sans','Noto Sans TC',sans-serif;background:#f5f4f0;color:#2b2a28;padding:24px;max-width:900px;margin:auto}}
h1{{color:#4c78a8;border-bottom:2px solid #4c78a8;padding-bottom:8px;font-size:1.2rem}}
.k{{display:flex;gap:24px;margin:16px 0}} .k div{{background:#fff;border:1px solid #e3e0d8;border-radius:6px;padding:12px 18px}}
.k b{{font-size:1.4rem;color:#439a9a}} table{{width:100%;border-collapse:collapse;background:#fff;font-size:.85rem}}
td,th{{border-bottom:1px solid #eee;padding:7px 10px;text-align:left}} ul{{font-size:.9rem}}
.aup{{font-size:.78rem;color:#9c9890;margin-top:20px}}</style>
<h1>VIS Workbench · 郵箱自動擷取摘要（{_esc(provider)}）</h1>
<div class="k"><div>擷取郵件<br><b>{len(records)}</b> 封</div>
<div>時間範圍<br><b style="font-size:1rem">{span}</b></div>
<div>往來對象<br><b>{len(senders)}</b> 人</div></div>
<h3>主要往來對象</h3><ul>{top or '<li>—</li>'}</ul>
<h3>最新 50 封</h3><table><tr><th>時間</th><th>寄件</th><th>主旨</th></tr>{rows}</table>
<p class="aup">{AUP}<br>產生於 {datetime.now():%Y-%m-%d %H:%M} · 本機處理 · 寫入 {jl}</p>
</html>"""
    hp = os.path.join(OUT_DIR, "mail_summary.html")
    with open(hp, "w", encoding="utf-8") as f:
        f.write(html)
    return jl, hp


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def main(argv):
    print("=" * 64); print("REMINDER:", AUP); print("=" * 64)

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    has = lambda name: name in argv

    mode = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else ""

    # 無參數 → 用這台電腦記住的設定自動讀（第一次設定後即可裸跑/雙擊）
    if not mode:
        prof = load_profile()
        if prof.get("provider"):
            mode = prof["provider"]
            print(f"  [記憶] 沿用這台電腦上次設定：{mode} · {prof.get('user','')}")
        else:
            mode = "auto"
            print("  [自動] 沒有既有設定，嘗試偵測桌機版 Outlook（免登入直接讀）…")

    # auto：門外漢零輸入。優先桌機 Outlook（COM，免登入，宛如本機使用者本人）
    if mode == "auto":
        try:
            import win32com.client  # noqa: F401
            print("  [OK] 偵測到桌機版 Outlook，直接以你本機已登入身分讀取（不需登入/密碼）。")
            mode = "outlook"
        except Exception:
            print("  [提示] 未偵測到桌機版 Outlook（或未安裝 pywin32）。")
            print("        · Outlook 桌機版：安裝並登入後雙擊本程式即可，全程免再登入。")
            print("        · 只有網頁版 Outlook / Gmail：首次授權一次（見說明檔），之後自動。")
            print("        先以離線自檢示範流程：")
            mode = "selftest"

    # 增量：只抓上次同步之後（背景靜默同步用）
    inc_days = None
    if has("--since-last"):
        last = load_profile().get("last_sync", "")
        if last:
            try:
                gap = (datetime.now() - datetime.fromisoformat(last)).days + 1
                inc_days = max(1, gap)
                print(f"  [增量] 上次同步 {last[:10]}，本次只抓近 {inc_days} 天")
            except Exception:
                pass

    def _days_default(key):
        return inc_days if inc_days is not None else load_profile().get(key, 180)

    try:
        if mode == "outlook":
            months = int(opt("--months", (max(1, inc_days // 31 + 1) if inc_days else load_profile().get("months", 6))))
            recs = fetch_outlook(months=months)
            save_profile({**load_profile(), "provider": "outlook", "months": months,
                          "last_sync": datetime.now().isoformat(timespec="seconds")})
        elif mode == "gmail_oauth":
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from pmis_lite.adapters.mail_oauth import fetch_gmail_oauth
            cs = opt("--client_secret", load_profile().get("client_secret", ""))
            days = int(opt("--days", load_profile().get("days", 180)))
            tok = os.path.join(OUT_DIR, "gmail_oauth_token.json")
            os.makedirs(OUT_DIR, exist_ok=True)
            recs = [_rec_to_dict(r) for r in fetch_gmail_oauth(cs, tok, lookback_days=days)]
            save_profile({"provider": "gmail_oauth", "client_secret": cs, "days": days})
        elif mode == "m365_oauth":
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from pmis_lite.adapters.mail_oauth import fetch_m365_oauth
            cid = opt("--client_id", load_profile().get("client_id", ""))
            tenant = opt("--tenant", load_profile().get("tenant", "common"))
            days = int(opt("--days", load_profile().get("days", 180)))
            cache = os.path.join(OUT_DIR, "m365_oauth_cache.bin")
            os.makedirs(OUT_DIR, exist_ok=True)
            recs = [_rec_to_dict(r) for r in fetch_m365_oauth(cid, tenant, cache, lookback_days=days)]
            save_profile({"provider": "m365_oauth", "client_id": cid, "tenant": tenant, "days": days})
        elif mode in ("gmail", "outlook365", "imap", "yahoo"):
            user = opt("--user", load_profile().get("user", ""))
            token = opt("--token", "") or load_token(user)            # 沒給就從保險庫載
            if has("--save") and opt("--token", ""):
                where = save_token(user, opt("--token", ""))
                print(f"  [記住] App Password 已存入 {where}；以後這台電腦自動讀，免再貼。")
            if not token:
                print("  [需要授權] 首次請加 --token \"...\" --save 存一次；之後裸跑即可自動讀。")
                return 1
            days = int(opt("--days", load_profile().get("days", 180)))
            recs = fetch_imap(provider=("gmail" if mode == "imap" else mode),
                              user=user, token=token, days=days)
            save_profile({"provider": mode, "user": user, "days": days})  # 記住（不含密碼）
        else:
            mode = "selftest"; recs = fetch_selftest()
    except Exception as e:
        print(f"  [錯誤] {e.__class__.__name__}: {e}")
        print("  → 不崩潰。請確認套件已裝、認證正確；或先跑 `python fetch_mailbox.py selftest`")
        return 1

    # 記錄本次同步時間（供下次 --since-last 增量）
    try:
        _p = load_profile(); _p["last_sync"] = datetime.now().isoformat(timespec="seconds"); save_profile(_p)
    except Exception:
        pass

    jl, hp = write_outputs(recs, mode)
    print(f"  擷取 {len(recs)} 封 → {jl}")
    print(f"  HTML 摘要 → {hp}")

    # 一條龍：擷取完直接進 SSOT pipeline（分類 + 全景 + 週報）
    if has("--pipeline"):
        run_pipeline_oneshot(jl)

    try:
        if os.name == "nt":
            os.startfile(hp)
    except Exception:
        pass
    print("  下一步：把 mail_fetched.jsonl 接進 SSOT pipeline 分類/全景分析。")
    return 0


def run_pipeline_oneshot(jsonl_path: str):
    """把擷取的郵件 jsonl 直接餵進 pipeline，一條龍出分類+全景+週報。"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import json as _json
    cfg = {
        "_AUP_REMINDER": AUP, "owner": "me", "locale": "zh-TW", "auto_detect": False,
        "numbering": {"prefix": "VWB", "domain": "MAIL", "hash_len": 6},
        "classification": {"product": {}, "topic": {},
                           "status": {"已結": ["done", "完成", "結案"], "逾期": ["overdue", "逾期"]}},
        "terms": {"seed": {}}, "mining": {"min_frequency": 2, "min_confidence": 0.55, "auto_merge": False},
        "sources": [{"type": "mail_jsonl", "enabled": True, "path": jsonl_path}],
        "supplement": {"enabled": False},
        "attachments": {"enabled": False},
        "output": {"store_dir": os.path.join(OUT_DIR, "ssot"), "markdown": True, "pptx_template": None},
    }
    cfg_path = os.path.join(OUT_DIR, "pipeline_config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        _json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        from pmis_lite.pipeline import run
        r = run(cfg_path)
        print(f"  [一條龍] SSOT 完成：{len(r['records'])} 筆 → {cfg['output']['store_dir']}")
    except Exception as e:
        print(f"  [一條龍] pipeline 失敗（擷取仍成功）：{e.__class__.__name__}: {e}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
