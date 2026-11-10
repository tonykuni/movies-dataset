#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DownloadsSync v0101 — 薄尾:頁面視覺跟鎖走(Manus 線上站)· 更強的自適應(上傳前綴 · 內容判讀 · 多來源 · 上次以來)

操作員令(2026-11-11):「自建平台 HTML U/I 視覺 … 百分百鎖定 MANUS · 各類元件不違反其風格 · synchronizer 要更強大完整自適應式 ·
鎖定視覺怎樣去自動隨系統更動去調整 · 節省後續修改反覆耗費 token · 不要浪費做過的東西」。
v0100 實測缺口:① 頁面寫死自己的色票 + 暗色模式 → VisualSpecLock v0101 audit 判 RED(鎖外色 8 · 鎖外字體 1);
② 上傳檔名帶 8 碼前綴(例 0d43c6a1-visual-responsive.spec.ts)→ 名字比不到,真正的 VIA 元件被當「無關」;
③ 只看檔名:名字不像 VIA、內容卻是 VIA 的文件 / 測試 / CI 漏掉;④ 只能一個來源夾;⑤ 重跑看不出哪些是新來的。
本版(v0100 一字不動):
  · 主題 = VisualSpecLock 最新一版鎖冊的解析 token(theme_vars);頁面只用 var(--…),不寫任何色碼 / 字體 → 鎖換版,重跑 plan 即跟著換。
    找不到鎖冊 → 照 v0100 外觀並在頁首標「未接鎖」(不假裝)。
  · 檔名比對先去掉上傳前綴「8 碼十六進位 + -」。
  · 名字不像 VIA 的文字檔(≤ 1 MB · .md .ts .js .yml .yaml .json .py .ps1 .txt .html .css)看內容:含 VIA 系統字樣 → NEW_FAMILY(標「內容判讀」)。
  · --src 可給多次(Downloads · 桌面 · 其他收件夾)。
  · 「上次以來新出現」:與上一份清單比 sha256,新出現的列加標記 + 計數。
其餘(判定 · apply 只增 ≤1 MB · 原件不動 · 不做 git)照 v0100。不碰 TA-Lib;不讀寫同意閘;零網路。
"""
from __future__ import annotations

import argparse
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0101"
TAG = "VIA_DownloadsSync " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VIA_DownloadsSync"
UPLOAD_PREFIX = re.compile(r"^[0-9a-f]{8}-")
TEXT_EXT = {".md", ".ts", ".js", ".yml", ".yaml", ".json", ".py", ".ps1", ".txt", ".html", ".css"}
VIA_WORDS = re.compile(r"\b(VIA[_-][A-Za-z]|VCGC|VRN-?[12]|VDF[_ ]|VQG|VAP[_ ]|Veritas|CGC_MDL)")


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
VIA = PRIOR.VIA
_CLASSIFY_V0100 = PRIOR.classify


def __getattr__(name):
    return getattr(PRIOR, name)


# ---------- 主題(跟鎖走)----------
def visual_lock():
    d = VIA / "docs" / "handoff" / "ai"
    tails = sorted(d.glob("VIA_VisualSpecLock_v*.py"), key=_vnum)
    if not tails:
        return None
    try:
        return _load(tails[-1], "VIA_VisualSpecLock_for_" + _STEM)
    except Exception:
        return None


def page_theme(lock_mod=None) -> tuple[str, str]:
    """回 (CSS 變數區塊, 來源說明)。頁面只引用下列語意名,值全來自鎖冊。"""
    m = lock_mod if lock_mod is not None else visual_lock()
    t = m.theme_vars() if m else {}
    if not t:
        return "", "未接鎖(找不到 VisualSpecLock 鎖冊)"
    pick = lambda *ks: next((t[k] for k in ks if t.get(k) and "var(" not in t[k]), None)
    sem = {"--s-bg": pick("--bg"), "--s-panel": pick("--white", "--paper"), "--s-ink": pick("--ink"), "--s-title": pick("--title", "--ink"),
           "--s-mute": pick("--muted"), "--s-line": pick("--line"), "--s-row": pick("--row", "--graybg"),
           "--s-accent": pick("--green", "--g-ink"), "--s-ok": pick("--g-ink", "--green"), "--s-ok-bg": pick("--g-bg"),
           "--s-warn": pick("--y-ink"), "--s-warn-bg": pick("--y-bg"), "--s-bad": pick("--red", "--r-ink"), "--s-bad-bg": pick("--r-bg"),
           "--s-sans": pick("--sans"), "--s-serif": pick("--serif"), "--s-mono": pick("--mono")}
    css = ":root{" + ";".join(f"{k}:{v}" for k, v in sem.items() if v) + "}"
    lp = m.latest_lock()
    return css, f"視覺鎖 {lp.name if lp else '?'}"


# ---------- 自適應 ----------
def clean_name(name: str) -> str:
    return UPLOAD_PREFIX.sub("", name)


def classify(name: str, data: bytes, idx: dict) -> dict:
    st = _CLASSIFY_V0100(clean_name(name), data, idx)
    if st["state"] == "IGNORE" and Path(name).suffix.lower() in TEXT_EXT and len(data) <= 1024 * 1024:
        try:
            txt = data[:200_000].decode("utf-8", errors="ignore")
        except Exception:
            txt = ""
        if len(VIA_WORDS.findall(txt)) >= 2:
            return {"state": "NEW_FAMILY", "why": "內容判讀:含 VIA 系統字樣"}
    return st


def scan_many(srcs: list, idx: dict, prev: dict | None = None) -> dict:
    PRIOR.classify = classify                                   # v0100 scan 以模組全域叫 classify
    try:
        mans = [(s, PRIOR.scan(s, idx)) for s in srcs]
    finally:
        PRIOR.classify = _CLASSIFY_V0100
    rows, counts = [], {}
    for s, m in mans:
        for r in m["rows"]:
            r["src"] = str(s)
            rows.append(r)
        for k, v in m["counts"].items():
            counts[k] = counts.get(k, 0) + v
    seen_before = {r.get("sha256") for r in (prev or {}).get("rows", []) if r.get("sha256")}
    for r in rows:
        r["since_last"] = bool(prev) and r.get("sha256") not in seen_before
    man = dict(mans[0][1]) if mans else {"schema": "via.downloads.sync/1"}
    man.update(engine=TAG, src=" · ".join(str(s) for s, _ in mans), rows=rows, counts=counts,
               take=sum(1 for r in rows if r["state"] in PRIOR.TAKE), since_last=sum(1 for r in rows if r.get("since_last")),
               lamp="YELLOW" if counts.get("CONFLICT") else "GREEN")
    return man


TONE = {"IN_REPO": "ok", "CONFLICT": "bad", "CHANGED": "warn", "NEW_VERSION": "accent", "OLD_VERSION": "warn", "NEW_FAMILY": "accent",
        "ZIP": "accent", "DUP": "mute", "BIG": "mute"}


def render_html(man: dict, lock_mod=None) -> str:
    theme, theme_src = page_theme(lock_mod)
    L = PRIOR.STATE_LABEL
    chips = "".join(f'<button class="chip t-{TONE.get(k, "mute")}" data-s="{k}">{html.escape(L.get(k, k))} <b>{v}</b></button>'
                    for k, v in man["counts"].items() if k != "IGNORE")
    if man.get("since_last"):
        chips += f'<button class="chip t-accent" data-s="__new">上次以來新出現 <b>{man["since_last"]}</b></button>'
    note = lambda r: r.get("repo_path") or r.get("repo_max") or r.get("dup_of") or (PRIOR._zip_note(r["zip"]) if r.get("zip") else r.get("why", ""))
    trs = "".join(
        f'<tr data-s="{r["state"]}" data-n="{1 if r.get("since_last") else 0}"><td><span class="tag t-{TONE.get(r["state"], "mute")}">'
        f'{html.escape(L.get(r["state"], r["state"]))}</span>{" <span class=new>新</span>" if r.get("since_last") else ""}</td>'
        f'<td class="mono">{html.escape(clean_name(r["rel"]))}</td><td class="num">{r["bytes"]:,}</td><td class="mono">{r["mtime"]}</td>'
        f'<td class="mono">{html.escape(note(r))}</td></tr>' for r in man["rows"])
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Downloads 同步器</title><style>
{theme}
body{{margin:0;background:var(--s-bg);color:var(--s-ink);font:14px/1.5 var(--s-sans);padding:16px max(16px,env(safe-area-inset-left))}}
h1{{font:600 22px/1.2 var(--s-serif);color:var(--s-title);margin:0 0 4px;border-left:4px solid var(--s-accent);padding-left:8px}}
.sub{{color:var(--s-mute);font-size:12px;margin-bottom:12px}} .panel{{background:var(--s-panel);border:1px solid var(--s-line);padding:12px;margin-bottom:12px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px}} .chip{{border:1px solid var(--s-line);background:var(--s-panel);color:var(--s-ink);padding:4px 10px;cursor:pointer;font:inherit}}
.chip.on{{outline:2px solid var(--s-accent)}} .tag{{font-size:12px;padding:1px 6px;white-space:nowrap}} .new{{font-size:11px;color:var(--s-panel);background:var(--s-accent);padding:0 4px}}
.t-ok{{color:var(--s-ok)}} .t-warn{{color:var(--s-warn)}} .t-bad{{color:var(--s-bad)}} .t-accent{{color:var(--s-accent)}} .t-mute{{color:var(--s-mute)}}
.wrap{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;min-width:720px}} th,td{{border-bottom:1px solid var(--s-line);padding:6px 8px;text-align:left;vertical-align:top}}
tbody tr:nth-child(even){{background:var(--s-row)}} th{{font-size:12px;color:var(--s-mute);font-weight:600}}
.mono{{font-family:var(--s-mono);font-size:12px;word-break:break-all}} .num{{text-align:right;font-variant-numeric:tabular-nums}}
</style></head><body>
<h1>VIA Downloads 同步器</h1>
<div class="sub">{html.escape(TAG)} · {html.escape(theme_src)} · 掃描 {html.escape(man['at'])} · 來源 {html.escape(man['src'])} · 燈 {man['lamp']} · 該收 {man['take']} · 與 VIA 無關 {man['counts'].get('IGNORE', 0)} 件(只計數不列名)</div>
<div class="panel chips">{chips}<button class="chip" data-s="">全部</button></div>
<div class="panel wrap"><table><thead><tr><th>狀態</th><th>檔案</th><th>位元組</th><th>修改時間(UTC)</th><th>倉內對照 / 說明</th></tr></thead><tbody>{trs}</tbody></table></div>
<div class="sub">更新:重跑 <span class="mono">python VIA_DownloadsSync_v0101.py plan</span> 即重生本頁(視覺跟著最新視覺鎖)· 收件:<span class="mono">apply</span>(只增 · ≤1 MB · 原件不動)。</div>
<script id="manifest" type="application/json">{html.escape(json.dumps(man, ensure_ascii=False))}</script>
<script>document.querySelectorAll('.chip').forEach(function(b){{b.addEventListener('click',function(){{var s=b.dataset.s;
document.querySelectorAll('.chip').forEach(function(x){{x.classList.toggle('on',x===b&&s!=='')}});
document.querySelectorAll('tbody tr').forEach(function(tr){{tr.hidden=!!s&&(s==='__new'?tr.dataset.n!=='1':tr.dataset.s!==s)}});}})}});</script>
</body></html>"""


def write_outputs(man: dict, out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    j, h = out / "VIA_DownloadsSync_latest.json", out / "VIA_DownloadsSync_latest.html"
    j.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    h.write_text(render_html(man), encoding="utf-8")
    return j, h


def selftest() -> int:
    import subprocess
    import tempfile
    checks = []

    def ck(name, cond, note=""):
        checks.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    rc0 = PRIOR.selftest()
    ck("v0100 自測照過(16 項)", rc0 == 0, f"rc {rc0}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        repo = td / "repo"
        repo.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=str(repo), capture_output=True)
        run("init", "-q")
        (repo / "VDF_ENG001_Demo_v0101.py").write_bytes(b"print(1)\n")
        run("add", "-A")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x")
        idx = PRIOR.repo_index(repo)
        s1, s2 = td / "Downloads", td / "Desktop"
        s1.mkdir()
        s2.mkdir()
        (s1 / "0d43c6a1-VDF_ENG001_Demo_v0101.py").write_bytes(b"print(1)\n")                 # 上傳前綴 + 已在倉
        (s1 / "0d43c6a1-visual-responsive.spec.ts").write_bytes(b"// VIA_HTML_UI audit for VCGC and VAP_ pages\n")  # 名不像 · 內容像
        (s1 / "notes.txt").write_bytes(b"grocery list\n")                                      # 無關
        (s2 / "VQG_Tool_v0100.py").write_bytes(b"x=1\n")                                       # 第二來源
        man = scan_many([s1, s2], idx)
        st = {clean_name(r["name"]): r["state"] for r in man["rows"]}
        ck("上傳前綴去掉後比對(已在倉)", st.get("VDF_ENG001_Demo_v0101.py") == "IN_REPO", st)
        ck("名字不像、內容像 VIA → NEW_FAMILY(內容判讀)", st.get("visual-responsive.spec.ts") == "NEW_FAMILY")
        ck("多來源合併 · 無關檔只計數", st.get("VQG_Tool_v0100.py") == "NEW_FAMILY" and man["counts"].get("IGNORE") == 1
           and "notes.txt" not in st, man["src"])
        (s2 / "VAP_New_v0100.py").write_bytes(b"y=2\n")
        man2 = scan_many([s1, s2], idx, prev=man)
        newn = [clean_name(r["name"]) for r in man2["rows"] if r["since_last"]]
        ck("上次以來新出現:只標新的那件", newn == ["VAP_New_v0100.py"] and man2["since_last"] == 1, newn)
        lock_dir = td / "lock"
        lock_dir.mkdir()

        class FakeLock:
            def theme_vars(self):
                return {"--bg": "#f2f1ec", "--white": "#fff", "--ink": "#33403f", "--muted": "#6b6860", "--line": "#dbd9d3",
                        "--green": "#2c4f4a", "--red": "#9e2b25", "--sans": "'Microsoft JhengHei',sans-serif"}

            def latest_lock(self):
                return lock_dir / "VIA_VisualSpecLock_v0199.json"
        page = render_html(man2, FakeLock())
        body_css = page.split("</style>")[0].split("}", 1)[1]
        ck("頁面樣式只用 var(--…)::root 之外沒有任何色碼", not re.search(r"#[0-9a-fA-F]{3,8}\b", body_css), re.findall(r"#[0-9a-fA-F]{3,8}\b", body_css)[:3])
        ck("主題值來自鎖(--s-accent = 鎖的 --green)· 頁首標鎖冊名", "--s-accent:#2c4f4a" in page and "VIA_VisualSpecLock_v0199.json" in page)

        class NoLock:
            def theme_vars(self):
                return {}

            def latest_lock(self):
                return None
        ck("找不到鎖 → 頁首照實標「未接鎖」", "未接鎖" in render_html(man2, NoLock()))
    vl = visual_lock()
    if vl is not None and vl.latest_lock():
        real = render_html(scan_many([HERE], PRIOR.repo_index()), vl)
        r = vl.audit_text(real, json.loads(vl.latest_lock().read_text(encoding="utf-8")))
        ck("真鎖 audit:本頁 GREEN(不違反鎖定風格)", r["lamp"] == "GREEN", r)
    src = Path(__file__).read_text(encoding="utf-8")
    ck("不碰 TA-Lib · 不寫同意閘 · 不做 git 寫入", not re.search(r"^\s*(import|from)\s+talib", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"\"git\", \"(add|commit|push)\"", src))
    print(f"[計] {TAG} 本版 {sum(checks)}/{len(checks)} " + ("PASS" if all(checks) else "FAIL"))
    return 0 if all(checks) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog=TAG, description="自適應 Downloads 同步器(視覺跟鎖 · 多來源 · 內容判讀 · 上次以來)")
    ap.add_argument("verb", nargs="?", choices=("plan", "apply"), default="plan")
    ap.add_argument("--src", action="append")
    ap.add_argument("--out")
    ap.add_argument("--max-mb", type=float, default=1.0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    srcs = [Path(s) for s in (a.src or [str(PRIOR.default_src())])]
    missing = [s for s in srcs if not s.is_dir()]
    if missing:
        print(f"[{TAG}] RED · 來源夾不在:{' · '.join(map(str, missing))}")
        return 2
    out = Path(a.out) if a.out else VIA / "VIA_Reports" / "sync"
    prev_p = out / "VIA_DownloadsSync_latest.json"
    prev = json.loads(prev_p.read_text(encoding="utf-8")) if prev_p.is_file() else None
    man = scan_many(srcs, PRIOR.repo_index(), prev)
    j, h = write_outputs(man, out)
    L = PRIOR.STATE_LABEL
    print(f"[{TAG}] {man['lamp']} · " + " · ".join(f"{L.get(k, k) if k != 'IGNORE' else '無關'} {v}" for k, v in man["counts"].items())
          + f" · 該收 {man['take']} · 上次以來新出現 {man['since_last']}")
    print(f"  清單 {j}\n  頁面 {h}")
    for r in man["rows"]:
        if r["state"] == "CONFLICT":
            print(f"  [要人判] {r['rel']} 與倉內 {r['repo_path']} 同名不同內容(版號律:另出新版號,不覆寫)")
    if a.verb == "apply":
        for s in srcs:
            sub = dict(man, rows=[r for r in man["rows"] if r.get("src") == str(s)])
            res = PRIOR.apply(sub, s, max_bytes=int(a.max_mb * 1024 * 1024))
            print(f"[{TAG}] 收件 {s} · 複製 {res['copied']} · 已收過 {res['already']} · 只記錄 {res['record_only']} · 到 {res['dest']}")
    return 0 if man["lamp"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
