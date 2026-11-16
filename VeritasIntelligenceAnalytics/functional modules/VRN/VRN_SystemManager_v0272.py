#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VRN-2 SystemManager v0272 — 薄尾:引擎矩陣(本系統每個引擎家族 × 每一版 × 時間,自動登記)。

操作員令(2026-11-14):「VDF / VRN / VCGC 每個子系統 SYSTEM MANAGER」「都有矩陣化自動註冊所有引擎版本號 時間」「做,開 PR 並盯著」。
實測(容器,main @ 850501bb):VRN-2 管理器的資產登記只記到日期、不提交、「引擎」欄在 main 上是 0;VDF 的 engines 只有版號沒有時間;
VCGC 編號冊有版號與時間,但要跑編號那一步才寫。各系統自己沒有一份「引擎 × 版本 × 時間」的矩陣。
本版(前版 v0271 一字不動;平行 extract · 進度 · 全列 · 與上次比照 v0271):
  ① 每次本管理器執行(自測除外)靜默登記自己夾裡每個引擎家族 × 每一版:版號 · 檔案時間(UTC)· 首次登記(UTC)·
     CRLF 無關雜湊 · 大小 · VCGC 號(只讀 VIA_NumberBooks,冊不在就「待號」)。檔沒變不重寫(大小 + 修改時間快取)。
  ② 新動詞 engine-matrix:另查 git 建立時間(每一版檔第一次進 git = 版本建立時間;淺 clone / 沒 git 照實留空),印矩陣,
     出 VIA_Reports/vrn/engine_matrix/VRN_EngineMatrix_latest.{json,csv,html}。
  ③ 同版號內容被改 → 記「變」+ changed_at(版號律:要出新版號);刪掉的版 → 記「消失」+ gone_at;尾版待號 → YELLOW(rc 2)。
只看 VRN 自己的夾(前綴 VRN_ · VRN2_ · VIA_VRN_;跳過 intake · _superseded · tests · contract …)。不 import 他系統、不寫 VCGC 冊、零網路、不碰 TA-Lib、不讀寫同意閘。
號:前版 v0271(main);本版取下一個空號 v0272。
用法:python VRN_SystemManager_v0272.py engine-matrix [--json] [--no-git] [--open] · 自測 python VRN_SystemManager_v0272.py --selftest(本版 + 前版 v0271)。
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
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
TAG = "v0272"
DISPLAY_NAME = "VRN-2 SystemManager"
FAMILY = "VRN_SystemManager"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, "vrn_manager_prior_for_" + TAG)


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(PRIOR, name)


EM_CFG = {"system": "VRN-2", "manager": DISPLAY_NAME + " " + TAG, "dir": "functional modules/VRN", "prefixes": ("VRN_", "VRN2_", "VIA_VRN_"),
          "out": "VIA_Reports/vrn/engine_matrix", "stem": "VRN"}
EM_SKIP = {"__pycache__", "_superseded", "_superseded_redundant", "VIA_RetiredEngines", "references", "intake", "retired", "evidence", "quarantine",
           "archive", "_archive", "restore", "restore_learned", "tests", "contract", "node_modules", ".git", "VIA_Reports"}


def em_files(root) -> list:
    """VRN 自己的夾 · 自己的前綴 · 有版號;跳過 intake / 舊檔 / 測試 / 契約等。"""
    base = Path(root) / EM_CFG["dir"]
    out = []
    for p in base.rglob("*.py") if base.is_dir() else []:
        rel = p.relative_to(base)
        if any(part in EM_SKIP or part.startswith(".") for part in rel.parts[:-1]):
            continue
        if p.name.startswith(EM_CFG["prefixes"]) and EM_VER_RX.match(p.name):
            out.append(p)
    return sorted(out)

# ────────────────── 引擎矩陣:本系統每個引擎家族 × 每一版 × 時間(自動登記 · 只看自己的夾)──────────────────
# 每次本管理器執行(自測除外)都靜默更新一次登記冊(檔沒變就不重寫;雜湊用大小 + 修改時間快取);`engine-matrix` 動詞印矩陣並出 CSV / HTML。
# 時間四種:file_time(檔案修改時間 UTC)· first_seen(本系統第一次登記到這一版的 UTC 時間)·
#           git_added(這一版檔案第一次進 git 的時間,= 版本建立時間;`engine-matrix` 才查,沒 git / 淺 clone 照實留空)·
#           vcgc_at(VCGC 編號冊給號的時間;只讀,冊不在就「待號」,不代寫冊)。
# 雜湊是 CRLF → LF 後的 SHA-256 前 12 碼(Windows / Linux 同值)。同版號內容變了 = 違反版號律 → 記「變」+ changed_at,燈 YELLOW。
EM_VER_RX = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{4})\.py$")
EM_BOOK_GLOBS = ("VIA_NumberBook_MDL_v*.jsonl", "VIA_NumberBook_ENG_v*.jsonl")
EM_STATE = {"auto": None, "auto_error": None}
EM_COLS = ("system", "family", "version", "tail", "vcgc_code", "vcgc_at", "git_added", "file_time", "first_seen", "changed_at", "gone_at",
           "sha12", "bytes", "state", "path")


def em_utc(ts=None) -> str:
    d = datetime.now(timezone.utc) if ts is None else datetime.fromtimestamp(ts, timezone.utc)
    return d.strftime("%Y-%m-%d %H:%M:%S +00:00")


def em_iso_to_utc(s: str) -> str:
    try:
        return datetime.fromisoformat(str(s).strip().replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S +00:00")
    except ValueError:
        return ""


def em_read(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def em_json(s):
    try:
        return json.loads(s) if s else None
    except ValueError:
        return None


def em_sha12(p) -> str:
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def em_numbers(root) -> dict:
    """VCGC 編號冊(MDL + ENG)只讀:檔名(不含 .py)→ 號 · 給號時間。冊不在 → 空(全部「待號」)。"""
    d = Path(root) / "supportive modules" / "registry" / "VIA_NumberBooks"
    out = {}
    for g in EM_BOOK_GLOBS:
        for bp in sorted(d.glob(g)):
            for ln in em_read(bp).splitlines():
                r = em_json(ln)
                if isinstance(r, dict) and r.get("name"):
                    out[r["name"]] = {"code": r.get("code"), "at": r.get("numbered_at") or r.get("updated_at")}
    return out


def em_parse_git(text: str) -> dict:
    """`git log --diff-filter=A --name-only --format=@@%cI` → 檔名 → 第一次加入 git 的 UTC 時間(log 由新到舊,留最舊那次)。"""
    out, cur = {}, ""
    for ln in text.splitlines():
        if ln.startswith("@@"):
            cur = em_iso_to_utc(ln[2:])
        elif ln.strip() and cur:
            out[Path(ln.strip()).name] = cur
    return out


def em_git_added(root) -> dict:
    base = Path(root) / EM_CFG["dir"]
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=off", "log", "--diff-filter=A", "--name-only", "--format=@@%cI", "--", str(base)],
                           cwd=str(root), capture_output=True, timeout=180, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"_error": "%s:%s" % (type(exc).__name__, str(exc)[:120])}
    if r.returncode != 0:
        return {"_error": "git rc %s" % r.returncode}
    return em_parse_git(r.stdout.decode("utf-8", errors="replace"))


def em_out_dir(root, out_dir=None) -> Path:
    return Path(out_dir) if out_dir else Path(root) / EM_CFG["out"]


def em_register(root, out_dir=None, use_git=False, now=None) -> dict:
    """掃自己的夾 → 登記冊(JSON)+ CSV + HTML;回摘要。前一份冊的 first_seen / git_added / changed_at 照留(只增不改)。"""
    root = Path(root)
    od = em_out_dir(root, out_dir)
    reg_p = od / ("%s_EngineMatrix_latest.json" % EM_CFG.get("stem", EM_CFG["system"]))
    prev = em_json(em_read(reg_p)) or {}
    rows_prev = prev.get("rows") or {}
    now = now or em_utc()
    nums = em_numbers(root)
    git = em_git_added(root) if use_git else {}
    files = em_files(root)
    tails = {}
    for p in files:
        m = EM_VER_RX.match(p.name)
        tails[m.group("fam")] = max(tails.get(m.group("fam"), -1), int(m.group("ver")))
    rows, new, changed = {}, [], []
    for p in files:
        m = EM_VER_RX.match(p.name)
        fam, ver, key = m.group("fam"), int(m.group("ver")), p.stem
        st = p.stat()
        old = rows_prev.get(key) or {}
        cached = old.get("bytes") == st.st_size and old.get("mtime_ns") == st.st_mtime_ns and old.get("sha12")
        sha = old["sha12"] if cached else em_sha12(p)
        num = nums.get(key) or {}
        row = {"system": EM_CFG["system"], "family": fam, "version": "v%04d" % ver, "tail": ver == tails[fam],
               "path": p.relative_to(root).as_posix(), "bytes": st.st_size, "mtime_ns": st.st_mtime_ns, "file_time": em_utc(st.st_mtime),
               "sha12": sha, "first_seen": old.get("first_seen") or now, "changed_at": old.get("changed_at"), "gone_at": None,
               "vcgc_code": num.get("code"), "vcgc_at": num.get("at"), "git_added": git.get(p.name) or old.get("git_added"), "state": "在"}
        if old.get("sha_prev"):
            row["sha_prev"] = old["sha_prev"]
        if not old:
            row["state"] = "新" if rows_prev else "在"
            new.append(key)
        elif old.get("sha12") and old["sha12"] != sha:
            row.update(state="變", changed_at=now, sha_prev=old["sha12"])
            changed.append(key)
        elif old.get("state") == "變":
            row["state"] = "變"                                   # 同版號改過內容 = 照實一直標著,不因下一輪沒再變就洗掉
        rows[key] = row
    gone = []
    for key, old in rows_prev.items():
        if key not in rows:
            r = dict(old, tail=False, state="消失", gone_at=old.get("gone_at") or now)
            if not old.get("gone_at"):
                gone.append(key)
            rows[key] = r
    live = [r for r in rows.values() if r["state"] != "消失"]
    tail_rows = [r for r in live if r["tail"]]
    unnum = sorted(r["family"] + "_" + r["version"] for r in tail_rows if not r.get("vcgc_code"))
    bad = sorted(k for k, r in rows.items() if r["state"] == "變")
    summary = {"system": EM_CFG["system"], "manager": EM_CFG["manager"], "updated_at": now, "families": len(tail_rows), "versions": len(live),
               "baseline": not rows_prev, "new": len(new) if rows_prev else 0, "changed_now": len(changed), "changed_total": len(bad),
               "gone_now": len(gone), "gone_total": sum(1 for r in rows.values() if r["state"] == "消失"),
               "tails_numbered": len(tail_rows) - len(unnum), "tails_unnumbered": unnum[:50], "versions_numbered": sum(1 for r in live if r.get("vcgc_code")),
               "git_dated": sum(1 for r in live if r.get("git_added")), "git_error": git.get("_error") if use_git else None,
               "new_list": new[:50] if rows_prev else [], "changed_list": bad[:50], "gone_list": gone[:50]}
    summary["lamp"] = "YELLOW" if (unnum or bad) else ("GREEN" if live else "GRAY")
    body = {"schema": "VIA.EngineMatrix.v1", "system": EM_CFG["system"], "own_dir": EM_CFG["dir"], "summary": summary,
            "rows": dict(sorted(rows.items()))}
    outs = [reg_p, od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"])), od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"]))]
    same = prev.get("rows") == body["rows"] and all(x.is_file() for x in outs)    # 逐版內容沒變且三個檔都在 → 不重寫
    summary["written"] = not same
    if not same:
        od.mkdir(parents=True, exist_ok=True)
        em_write(reg_p, json.dumps(body, ensure_ascii=False, indent=1))
        em_write(od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"])), em_csv(body), bom=True)
        em_write(od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"])), em_html(body))
    summary["files"] = {"json": str(reg_p), "csv": str(od / ("%s_EngineMatrix_latest.csv" % EM_CFG.get("stem", EM_CFG["system"]))),
                        "html": str(od / ("%s_EngineMatrix_latest.html" % EM_CFG.get("stem", EM_CFG["system"])))}
    return summary


def em_write(p: Path, text: str, bom: bool = False) -> None:
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(text, encoding="utf-8-sig" if bom else "utf-8", newline="\n")
    os.replace(tmp, p)


def em_sorted_rows(body: dict) -> list:
    return sorted(body["rows"].values(), key=lambda r: (r["family"], -int(r["version"][1:])))


def em_csv(body: dict) -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(EM_COLS)
    for r in em_sorted_rows(body):
        w.writerow([r.get(c) if r.get(c) is not None else "" for c in EM_COLS])
    return buf.getvalue()


def em_html(body: dict) -> str:
    import html as _h
    s = body["summary"]
    esc = lambda v: _h.escape("" if v is None else str(v))  # noqa: E731
    lamp_c = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "GRAY": "#57606a"}.get(s["lamp"], "#cf222e")
    trs = []
    for r in em_sorted_rows(body):
        cls = " ".join(x for x in ("tail" if r.get("tail") else "", {"新": "new", "變": "chg", "消失": "gone"}.get(r.get("state"), "")) if x)
        trs.append("<tr class='%s'>%s</tr>" % (cls, "".join("<td>%s</td>" % esc(r.get(c) if c != "tail" else ("尾版" if r.get("tail") else ""))
                                                       for c in EM_COLS if c not in ("system", "path"))))
    head = "".join("<th>%s</th>" % esc(c) for c in EM_COLS if c not in ("system", "path"))
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>%s 引擎矩陣</title><style>"
            ":root{--bg:#fff;--fg:#1f2328;--mut:#57606a;--line:#d0d7de;--alt:#f6f8fa}"
            "@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#8d96a0;--line:#30363d;--alt:#161b22}}"
            "body{margin:0;padding:16px;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,'Microsoft JhengHei',sans-serif}"
            "h1{font-size:18px;margin:0 0 6px}.meta{color:var(--mut);margin-bottom:10px}.lamp{font-weight:700;color:%s}"
            ".bar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:8px 0}input{padding:6px 8px;border:1px solid var(--line);"
            "border-radius:6px;background:var(--bg);color:var(--fg);min-width:220px}.wrap{overflow:auto;border:1px solid var(--line);border-radius:6px}"
            "table{border-collapse:collapse;width:100%%;font-size:12.5px}th,td{padding:4px 8px;border-bottom:1px solid var(--line);white-space:nowrap;text-align:left}"
            "th{position:sticky;top:0;background:var(--alt)}tr:nth-child(even) td{background:var(--alt)}tr.tail td:nth-child(2){font-weight:700}"
            "tr.new td:last-child{color:#1a7f37;font-weight:700}tr.chg td:last-child{color:#cf222e;font-weight:700}tr.gone td{opacity:.55}"
            "</style></head><body><h1>%s 引擎矩陣 · %s</h1>"
            "<div class='meta'><span class='lamp'>%s</span> · 家族 %d · 版本 %d · 尾版已給號 %d / %d · git 建立時間 %d 版 · 本輪 新 %d · 同版號內容變 %d · 消失 %d · 更新 %s</div>"
            "<div class='bar'><input id='q' placeholder='篩選(家族 / 版號 / 號)' oninput='f()'><label><input type='checkbox' id='t' onchange='f()'> 只看尾版</label></div>"
            "<div class='wrap'><table><thead><tr>%s</tr></thead><tbody id='b'>%s</tbody></table></div>"
            "<script>function f(){var q=document.getElementById('q').value.toLowerCase(),t=document.getElementById('t').checked;"
            "document.querySelectorAll('#b tr').forEach(function(r){r.style.display=((!t||r.classList.contains('tail'))&&r.textContent.toLowerCase().indexOf(q)>=0)?'':'none'})}</script>"
            "</body></html>") % (esc(s["system"]), lamp_c, esc(s["system"]), esc(s["manager"]), esc(s["lamp"]), s["families"], s["versions"],
                                 s["tails_numbered"], s["families"], s["git_dated"], s["new"], s["changed_total"], s["gone_now"], esc(s["updated_at"]), head, "".join(trs))


def em_auto(root) -> dict | None:
    """每次本管理器執行時的靜默登記(不印任何東西 · 不擋主動詞);失敗只記在 EM_STATE。"""
    try:
        EM_STATE["auto"] = em_register(root)
    except Exception as exc:  # noqa: BLE001 — 自動登記壞了不擋主流程,照實記下,engine-matrix 動詞會顯示
        EM_STATE["auto_error"] = "%s:%s" % (type(exc).__name__, str(exc)[:160])
    return EM_STATE["auto"]


def em_cmd(args: list, root) -> int:
    """`engine-matrix [--json] [--no-git] [--open]`:登記並印矩陣(每家族一列:尾版 · 版數 · 號 · 時間);燈照 L16(0 綠 · 2 黃)。"""
    s = em_register(root, use_git="--no-git" not in args)
    if "--json" in args:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        body = em_json(em_read(s["files"]["json"])) or {"rows": {}}
        print("  %-48s %-6s %4s  %-18s %-25s %-25s %s" % ("家族", "尾版", "版數", "VCGC 號", "版本建立(git)", "首次登記", "狀態"))
        fams = {}
        for r in body["rows"].values():
            if r.get("state") != "消失":
                fams.setdefault(r["family"], []).append(r)
        for fam in sorted(fams):
            rs = fams[fam]
            t = next(x for x in rs if x.get("tail"))
            flag = "變" if any(x.get("state") == "變" for x in rs) else ("新" if t.get("state") == "新" else "")
            print("  %-48s %-6s %4d  %-18s %-25s %-25s %s" % (fam[:48], t["version"], len(rs), t.get("vcgc_code") or "待號",
                                                             t.get("git_added") or "—", t.get("first_seen") or "—", flag))
        print("[%s] 引擎矩陣 %s · 家族 %d · 版本 %d · 尾版已給號 %d / %d · git 建立時間 %d 版%s · 本輪 新 %d · 同版號內容變 %d · 消失 %d"
              % (EM_CFG["manager"], s["lamp"], s["families"], s["versions"], s["tails_numbered"], s["families"], s["git_dated"],
                 ("(git:%s)" % s["git_error"]) if s.get("git_error") else "", s["new"], s["changed_total"], s["gone_now"]))
        if s["tails_unnumbered"]:
            print("  [待號] 尾版還沒有 VCGC 號:" + " · ".join(s["tails_unnumbered"][:8]) + (" …" if len(s["tails_unnumbered"]) > 8 else ""))
        if s["changed_list"]:
            print("  [變] 同版號內容被改過(版號律:要出新版號):" + " · ".join(s["changed_list"][:8]))
        print("  [檔] %s · %s · %s" % (s["files"]["json"], s["files"]["csv"], s["files"]["html"]))
    if "--open" in args:
        import webbrowser
        webbrowser.open(Path(s["files"]["html"]).as_uri())
    return 0 if s["lamp"] == "GREEN" else 2


def em_selftest(chk) -> None:
    """引擎矩陣自測(暫存夾,不碰真倉的登記冊)。chk(name, cond, note)。"""
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        own = root / EM_CFG["dir"]
        (own / "intake").mkdir(parents=True)
        pre = EM_CFG["prefixes"][0]
        a0, a1, b0 = own / (pre + "ENG901_Alpha_v0100.py"), own / (pre + "ENG901_Alpha_v0101.py"), own / (pre + "ENG902_Beta_v0100.py")
        a0.write_text("x = 1\n", encoding="utf-8")
        a1.write_bytes(b"x = 2\r\n")
        b0.write_text("y = 1\n", encoding="utf-8")
        (own / "intake" / (pre + "ENG903_Skip_v0100.py")).write_text("z\n", encoding="utf-8")
        (own / "notmine_v0100.py").write_text("n\n", encoding="utf-8")
        nb = root / "supportive modules" / "registry" / "VIA_NumberBooks"
        nb.mkdir(parents=True)
        (nb / "VIA_NumberBook_ENG_v0100.jsonl").write_text(json.dumps({"code": "VIA-X-ENG001", "name": pre + "ENG901_Alpha_v0101",
                                                                      "numbered_at": "2026-11-14 10:00:00 +0000"}) + "\n", encoding="utf-8")
        s1 = em_register(root, now="2026-11-14 00:00:00 +00:00")
        body1 = em_json(em_read(s1["files"]["json"]))
        r_a1 = body1["rows"][pre + "ENG901_Alpha_v0101"]
        chk("E1 首次登記:只收自己的夾 · 自己前綴 · 有版號(intake / 別人的檔不收)· 家族 2 · 版本 3 · 尾版 Alpha v0101 有號 · Beta 待號 → YELLOW · "
            "CSV / HTML 都寫出 · 雜湊 CRLF 與 LF 同值",
            s1["baseline"] and s1["families"] == 2 and s1["versions"] == 3 and r_a1["tail"] and r_a1["vcgc_code"] == "VIA-X-ENG001"
            and s1["tails_unnumbered"] == [pre + "ENG902_Beta_v0100"] and s1["lamp"] == "YELLOW"
            and Path(s1["files"]["csv"]).is_file() and "ENG901_Alpha" in em_read(s1["files"]["html"])
            and r_a1["sha12"] == hashlib.sha256(b"x = 2\n").hexdigest()[:12] and r_a1["first_seen"] == "2026-11-14 00:00:00 +00:00", s1)
        s1b = em_register(root, now="2026-11-14 00:30:00 +00:00")
        b0.write_text("y = 2  # 同版號改內容\n", encoding="utf-8")
        a2 = own / (pre + "ENG901_Alpha_v0102.py")
        a2.write_text("x = 3\n", encoding="utf-8")
        a0.unlink()
        s2 = em_register(root, now="2026-11-15 00:00:00 +00:00")
        body2 = em_json(em_read(s2["files"]["json"]))
        rows2 = body2["rows"]
        chk("E2 第二輪:沒變就不重寫 · 新版 Alpha v0102 記「新」並成尾版(待號)· 同版號改內容 Beta v0100 記「變」+ changed_at · 刪掉的 v0100 記「消失」+ gone_at · "
            "首次登記時間照留",
            s1b["written"] is False and s2["new"] == 1 and rows2[pre + "ENG901_Alpha_v0102"]["state"] == "新" and rows2[pre + "ENG901_Alpha_v0102"]["tail"]
            and rows2[pre + "ENG902_Beta_v0100"]["state"] == "變" and rows2[pre + "ENG902_Beta_v0100"]["changed_at"] == "2026-11-15 00:00:00 +00:00"
            and rows2[pre + "ENG901_Alpha_v0100"]["state"] == "消失" and rows2[pre + "ENG901_Alpha_v0100"]["gone_at"] == "2026-11-15 00:00:00 +00:00"
            and rows2[pre + "ENG902_Beta_v0100"]["first_seen"] == "2026-11-14 00:00:00 +00:00" and s2["changed_list"] == [pre + "ENG902_Beta_v0100"], s2)
        s3 = em_register(root, now="2026-11-16 00:00:00 +00:00")
        rows3 = em_json(em_read(s3["files"]["json"]))["rows"]
        chk("E3 第三輪:「變」照實一直標著(不因下一輪沒再改就洗掉)· 消失的不重複算",
            rows3[pre + "ENG902_Beta_v0100"]["state"] == "變" and s3["gone_now"] == 0 and s3["gone_total"] == 1, s3)
        g = em_parse_git("@@2026-11-14T23:05:00+08:00\nVeritasIntelligenceAnalytics/x/%sENG901_Alpha_v0102.py\n\n"
                         "@@2026-11-01T01:00:00+00:00\nVeritasIntelligenceAnalytics/x/%sENG901_Alpha_v0102.py\nVeritasIntelligenceAnalytics/x/%sENG902_Beta_v0100.py\n"
                         % (pre, pre, pre))
        chk("E4 git 建立時間:+08:00 換成 UTC · 同一檔多次加入取最早那次", g.get(pre + "ENG902_Beta_v0100.py") == "2026-11-01 01:00:00 +00:00"
            and g.get(pre + "ENG901_Alpha_v0102.py") == "2026-11-01 01:00:00 +00:00" and em_iso_to_utc("2026-11-14T23:05:00+08:00") == "2026-11-14 15:05:00 +00:00", g)
        buf = io.StringIO()
        keep = dict(EM_STATE)
        with contextlib.redirect_stdout(buf):
            em_auto(root)
        auto_ok = buf.getvalue() == "" and EM_STATE.get("auto_error") is None and isinstance(EM_STATE.get("auto"), dict)
        EM_STATE.update(keep)
        chk("E5 自動登記:一個字都不印(不弄亂 --json 等輸出)· 不擋主流程", auto_ok, buf.getvalue()[:200])


# ────────────────── 動詞 ──────────────────
def collect() -> dict:
    """VCGC 子系統對接口(照前版 · 只讀)· served_by 記本版。"""
    out = PRIOR.collect()
    if isinstance(out, dict):
        out = dict(out)
        sb = dict(out.get("served_by") or {})
        sb["tail"] = FAMILY + "_" + TAG
        out["served_by"] = sb
    return out


def provenance(args: list) -> int:
    """同 v0262 / v0270 / v0271:直送 ENG114 尾版;`--selftest` 之後再跑本版自測,回傳碼取大。"""
    h = PRIOR.host()
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    rc = int(h._load_engine(h.provenance_engine_path()).main(list(args)) or 0)
    if "--selftest" in args:
        print("  ── 來源回歸之後:本版管理器自測 ──", flush=True)
        rc = max(rc, int(selftest() or 0))
    return rc


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["provenance"]:
        return provenance(args[1:])
    if args == ["--selftest"] or "--selftest" in args[:1]:
        return selftest()
    if args[:1] == ["engine-matrix"]:
        return em_cmd(args[1:], VIA_ROOT)
    if args[:1] != ["_extract_worker"]:
        em_auto(VIA_ROOT)                                        # 每次執行靜默登記引擎版本與時間(不印 · 不擋)
    return PRIOR.main(args)


def selftest() -> int:
    print("[計] %s %s 自測開始(本版 8 項 · 再前版 %s)" % (DISPLAY_NAME, TAG, PRIOR_PATH.name), flush=True)
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    em_selftest(chk)
    fams = {EM_VER_RX.match(p.name).group("fam") for p in em_files(VIA_ROOT)}
    tails = sorted(p.name for p in em_files(VIA_ROOT) if p.name.startswith(FAMILY + "_v"))
    chk("E6 真倉:VRN 自己的引擎家族 %d 個都收到(管理器尾版 %s 在內)· intake / 測試 / 契約夾不收"
        % (len(fams), tails[-1] if tails else "—"),
        len(fams) > 10 and FAMILY in fams and (tails[-1] if tails else "") == Path(__file__).name
        and not any("/intake/" in p.as_posix() or "/tests/" in p.as_posix() for p in em_files(VIA_ROOT)), sorted(fams)[:5])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("E7 檔面:def main / def selftest / def collect · 第 3 行加速器標記 · __main__ provenance 守門在 --selftest 之前 · 子行程不經 shell · 零 TA-Lib · 不寫同意閘",
        "\ndef main(" in text and "\ndef selftest(" in text and "\ndef collect(" in text and text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]"
        and text.index('sys.argv[1:2] == ["provenance"]') < text.index('"--selftest" in sys.argv:') and "shell=" + "True" not in text
        and "import " + "talib" not in text and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text)
    print("  ── 前版 %s 自測(本版只加引擎矩陣,平行 extract 等照前版)──" % PRIOR_PATH.name, flush=True)
    prior_rc = int(PRIOR.selftest() or 0)
    chk("E8 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s %s(%s_%s.py)自測 %d/%d · %s" % (DISPLAY_NAME, TAG, FAMILY, TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["provenance"]:     # 同 v0262 / v0270 / v0271:provenance 先於任何 --selftest 攔截
        sys.exit(provenance(sys.argv[2:]))
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
