#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0118 — 薄尾:connect 全景連線檢視(各類文件 × MCP 通道 × 外部工具 × 備份 / 讀取)

操作員 2026-11-22 09:29:「全景式檢視各類文件透過 MCP TO PC GITHUB CHATGPT GEMINI CLAUDE MANUS PERPLEXITY COPILOT GROK
+ GRAPHIFY + OMNIROUTE + PONYTAIL + AGENCY-MEM + 備份/讀取」。
  connect [check]          一張矩陣四段(唯讀,只寫自己的報告夾):
                             A 通道   PC 檔案 · GitHub · Claude(Desktop / Code)· Gemini CLI · Copilot(VS Code)· ChatGPT · Manus · Perplexity · Grok
                                      本機 stdio 用戶端:設定檔在不在 · 有沒有 vcgc 這一項 · VCGC MCP 握手;雲端用戶端:要公開 HTTPS 端點 → 灰「待裁」(資料邊界)
                             B 工具   Graphify · OmniRoute · Ponytail · Agency-mem(agentmemory / claude-mem):裝了沒 · 有沒有收據
                             C 備份 / 讀取   VIA_DailyBackup 尾版 check(只讀對冊)· 最新 MANIFEST 幾小時前
                             D 文件類型   倉內已追蹤檔依類型計數 · 省 Token 讀法(read / slice)· 本機讀取套件 · MCP 能不能讀 · 能不能離開本機
                           寫 VIA_Reports/vcgc/connect/CONNECT_latest.json|txt|html(txt ≤300 行、NEXT: 結尾)
  connect config [--apply] 本機 stdio 用戶端(Claude Desktop · Gemini CLI · VS Code)的設定檔「已存在」才補 vcgc 這一項;
                           沒加 --apply 只列會改哪幾個檔;加了才寫(先留 .bak · 只加不改別的伺服器);不建新的設定檔、不碰雲端用戶端。
其餘動詞照 v0117(toolbox · guard · fuse · omniroute …)。不改 VDF / VRN 的檔;不連外(GitHub 只用本機 git / gh 狀態)。
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

import calendar
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "CGC_SystemManager"
TAG = "CGC_SystemManager v0118"
REG = "supportive modules/registry"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if "cgc_prior_for_v0118" in sys.modules:
    PRIOR = sys.modules["cgc_prior_for_v0118"]
else:
    _spec = importlib.util.spec_from_file_location("cgc_prior_for_v0118", PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules["cgc_prior_for_v0118"] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _v116():
    """往前版鏈找 omniroute 的握手 / MCP 尾版 / 閘道(v0116 那一層)。"""
    m = PRIOR
    while m is not None and not hasattr(m, "handshake"):
        m = getattr(m, "PRIOR", None)
    return m


def _home() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home())


def _appdata() -> Path:
    return Path(os.environ.get("APPDATA") or (_home() / "AppData" / "Roaming"))


# A 段:通道。kind=local → stdio 設定檔;cloud → 只能走公開 HTTPS(資料邊界待裁)
def client_paths(home: Path = None, appdata: Path = None) -> dict:
    home = home or _home()
    appdata = appdata or _appdata()
    return {
        "claude-desktop": [appdata / "Claude" / "claude_desktop_config.json",
                           home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"],
        "gemini-cli": [home / ".gemini" / "settings.json"],
        "copilot-vscode": [appdata / "Code" / "User" / "mcp.json"],
    }


CHANNELS = [
    {"key": "pc-files", "name": "PC 檔案(本機倉 · VCGC MCP stdio)", "kind": "local"},
    {"key": "github", "name": "GitHub(origin · gh 登入)", "kind": "local"},
    {"key": "claude-code", "name": "Claude Code(倉根 .mcp.json)", "kind": "local"},
    {"key": "claude-desktop", "name": "Claude Desktop", "kind": "local"},
    {"key": "gemini-cli", "name": "Gemini(Gemini CLI)", "kind": "local"},
    {"key": "copilot-vscode", "name": "Copilot(VS Code)", "kind": "local"},
    {"key": "chatgpt", "name": "ChatGPT", "kind": "cloud"},
    {"key": "manus", "name": "Manus", "kind": "cloud"},
    {"key": "perplexity", "name": "Perplexity", "kind": "cloud"},
    {"key": "grok", "name": "Grok", "kind": "cloud"},
]
CLOUD_NOTE = "網頁 / 雲端用戶端吃不到本機 stdio,要公開 HTTPS 端點 → 與「能離開本機的只有程式碼結構與 schema」衝突,待裁(11-19 起);不開端點"

# D 段:文件類型
DOC_CLASSES = [
    ("程式", (".py", ".ps1", ".psm1", ".js", ".ts"), "read 骨架卡 · slice 一個定義", None, "結構可離機"),
    ("冊 / 設定", (".json", ".jsonl", ".yaml", ".yml", ".toml"), "read 兩層卡 · slice JSON 路徑", None, "結構可離機"),
    ("文件", (".md", ".txt", ".html"), "read · NLP --brief 摘要", None, "倉內文件可;研報不離機"),
    ("辦公", (".pdf", ".docx", ".xlsx", ".pptx", ".csv"), "本機套件讀", ("pypdf", "docx", "openpyxl", "pptx"), "內容不離機(研報 / 數據)"),
    ("資料庫", (".parquet", ".duckdb", ".db", ".sqlite"), "DuckDB / pyarrow 本機查", ("duckdb", "pyarrow"), "不離機"),
    ("圖", (".png", ".jpg", ".jpeg", ".svg", ".gif"), "—", None, "不離機"),
]


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _has_vcgc(cfg) -> bool:
    if not isinstance(cfg, dict):
        return False
    for key in ("mcpServers", "servers"):
        s = cfg.get(key)
        if isinstance(s, dict) and "vcgc" in s:
            return True
    mcp = cfg.get("mcp")
    return isinstance(mcp, dict) and isinstance(mcp.get("servers"), dict) and "vcgc" in mcp["servers"]


def _run(cmd: list, cwd: Path, timeout: int = 20):
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def check_channels(via: Path, handshake_ok: bool, tools: int, paths: dict = None) -> list:
    rows, paths = [], paths or client_paths()
    repo = via.parent
    for c in CHANNELS:
        k, row = c["key"], {"key": c["key"], "name": c["name"], "kind": c["kind"]}
        if c["kind"] == "cloud":
            row.update(lamp="GRAY", how="遠端 MCP(HTTPS)", evidence="—", note=CLOUD_NOTE)
        elif k == "pc-files":
            row.update(lamp="GREEN" if handshake_ok else "RED", how="stdio · CGC_MDL279 尾版",
                       evidence="握手 %s · 工具 %d 個" % ("成功" if handshake_ok else "失敗", tools),
                       note="工具全是治理類;沒有「讀一份文件」的工具 → 見 D 段")
        elif k == "github":
            rc, out = _run(["git", "remote", "get-url", "origin"], repo)
            gh = shutil.which("gh")
            grc, _ = _run([gh, "auth", "status"], repo) if gh else (None, "")
            ok = rc == 0 and "github.com" in out
            row.update(lamp="GREEN" if ok and grc == 0 else "YELLOW" if ok else "RED", how="git origin · gh",
                       evidence="origin %s · gh %s" % ("在" if ok else "沒有", "已登入" if grc == 0 else "沒裝" if not gh else "沒登入"),
                       note="唯讀;不 fetch")
        elif k == "claude-code":
            cfg = _json(repo / ".mcp.json")
            row.update(lamp="GREEN" if _has_vcgc(cfg) and handshake_ok else "YELLOW" if cfg else "RED", how="倉根 .mcp.json",
                       evidence="有 vcgc" if _has_vcgc(cfg) else ("檔在、沒有 vcgc" if cfg else "沒有 .mcp.json"), note="")
        else:
            hit = next((p for p in paths.get(k, []) if p.is_file()), None)
            if hit is None:
                base = next((p.parent for p in paths.get(k, []) if p.parent.is_dir()), None)
                row.update(lamp="GRAY" if base is None else "YELLOW", how="本機 stdio 設定檔",
                           evidence="沒裝(找不到設定夾)" if base is None else "裝了、沒有設定檔",
                           note="" if base is None else "connect config --apply 只補已存在的檔;這個要先在該 app 開一次 MCP 設定")
            else:
                has = _has_vcgc(_json(hit))
                row.update(lamp="GREEN" if has and handshake_ok else "YELLOW", how="本機 stdio 設定檔",
                           evidence=("有 vcgc · " if has else "沒有 vcgc · ") + hit.name, path=str(hit),
                           note="" if has else "connect config --apply 補上(先留 .bak)")
        rows.append(row)
    return rows


def check_tools(via: Path, home: Path = None) -> list:
    home = home or _home()
    rows = []
    rec = via / "VIA_Reports" / "graphify" / "VIA_Graphify_latest.json"
    mod = importlib.util.find_spec("graphify") is not None
    rows.append({"key": "graphify", "name": "Graphify(知識圖 · 只准本機 AST 模式)", "lamp": "GREEN" if rec.is_file() and mod else "YELLOW" if (rec.is_file() or mod) else "GRAY",
                 "evidence": "套件 %s · 收據 %s" % ("在" if mod else "沒裝", "在" if rec.is_file() else "沒有"), "note": "via-vcgc graphify status"})
    v = _v116()
    g = v.gateway() if v and hasattr(v, "gateway") else {"listening_20128": False, "installed": []}
    rows.append({"key": "omniroute", "name": "OmniRoute(AI 閘道 · 只送程式碼與 schema)", "lamp": "GREEN" if g.get("listening_20128") else "YELLOW" if g.get("installed") else "GRAY",
                 "evidence": "在聽 20128" if g.get("listening_20128") else ("已裝沒在跑" if g.get("installed") else "沒裝"), "note": "裝與啟動在 ApplyRun 的 G 道"})
    pony = [p for p in (home / ".claude" / "plugins").glob("**/*ponytail*")][:1] if (home / ".claude" / "plugins").is_dir() else []
    rows.append({"key": "ponytail", "name": "Ponytail(讓代理少寫程式碼的規則集 · Claude Code 外掛)", "lamp": "GREEN" if pony else "GRAY",
                 "evidence": "外掛在 " + pony[0].name if pony else "沒裝(~/.claude/plugins 找不到)", "note": "不是日誌監控;倉內無檔"})
    mem = [n for n in (".agentmemory", ".claude-mem", ".agency-mem") if (home / n).is_dir()]
    rows.append({"key": "agency-mem", "name": "Agency-mem(agentmemory / claude-mem 代理記憶)", "lamp": "YELLOW" if mem else "GRAY",
                 "evidence": "找到 " + " · ".join(mem) if mem else "沒裝",
                 "note": "11-06 裁定收尾期不引入;裝了也只列不接(記憶內容可能含資料,離機前要過資料邊界)"})
    return rows


def check_backup(via: Path) -> dict:
    ai = via / "docs" / "handoff" / "ai"
    hits = sorted(ai.glob("VIA_DailyBackup_v*.py"), key=_vnum)
    man = via / "docs" / "handoff" / "backup" / "BACKUP_MANIFEST_latest.json"
    m = _json(man) or {}
    stamp = str(m.get("created_at") or m.get("at") or m.get("ts") or "")
    age = None
    try:
        age = round((time.time() - calendar.timegm(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S"))) / 3600, 1)
    except (ValueError, OverflowError):
        age = None
    out = {"key": "backup", "name": "備份 / 讀取(VIA_DailyBackup)", "tail": hits[-1].name if hits else None, "manifest": man.is_file(),
           "age_h": age, "check": None}
    if hits:
        rc, txt = _run([sys.executable, "-B", str(hits[-1]), "check"], via.parent, 600)
        lamp = re.search(r"\b(GREEN|YELLOW|RED)\b", txt or "")
        out["check"] = {"rc": rc, "lamp": lamp.group(1) if lamp else None, "tail": (txt or "").strip().splitlines()[-1:] }
    c = (out["check"] or {}).get("lamp")
    out["lamp"] = "RED" if not hits or not man.is_file() else (c or "YELLOW")
    out["evidence"] = "尾版 %s · MANIFEST %s%s · check %s" % (out["tail"] or "—", "在" if man.is_file() else "缺",
                                                         (" · %.1f 小時前" % age) if age is not None else "", c or "讀不到燈")
    out["note"] = "讀取 = check 逐檔 sha 對冊;zip 不在本機 → 黃(照實)"
    return out


def check_doctypes(via: Path) -> list:
    rc, out = _run(["git", "ls-files", "-z"], via.parent, 120)
    files = [f for f in (out or "").split("\0") if f] if rc == 0 else []
    counts = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        counts[ext] = counts.get(ext, 0) + 1
    rows = []
    for name, exts, how, libs, boundary in DOC_CLASSES:
        n = sum(counts.get(e, 0) for e in exts)
        miss = [m for m in (libs or ()) if importlib.util.find_spec(m) is None]
        if name in ("程式", "冊 / 設定", "文件"):
            lamp, mcp = ("YELLOW", "否(MCP 沒有讀檔工具;本機 token read 可)")
        elif name == "圖":
            lamp, mcp = "GRAY", "否"
        else:
            lamp, mcp = ("YELLOW" if miss else "GREEN"), "否(不離機,照邊界)"
        rows.append({"key": name, "exts": " ".join(exts), "count": n, "how": how, "libs_missing": miss, "mcp": mcp, "boundary": boundary,
                     "lamp": lamp if n else "GRAY"})
    return rows


def connect(via: Path = VIA_ROOT, out_dir: Path = None, paths: dict = None, home: Path = None) -> dict:
    v = _v116()
    tail = v.mcp_tail(via) if v else None
    tools, why = (v.handshake(tail, via) if (v and tail) else ([], "找不到 MCP 尾版"))
    res = {"tag": TAG, "at": utc(), "mcp_server": tail.name if tail else None, "mcp_tools": len(tools), "mcp_why": why,
           "channels": check_channels(via, bool(tools), len(tools), paths), "tools": check_tools(via, home),
           "backup": check_backup(via), "doctypes": check_doctypes(via)}
    lamps = [r["lamp"] for r in res["channels"] + res["tools"] + res["doctypes"]] + [res["backup"]["lamp"]]
    res["lamp"] = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    res["counts"] = {k: lamps.count(k) for k in ("GREEN", "YELLOW", "RED", "GRAY")}
    write(via, res, out_dir)
    return res


def _lines(res: dict) -> list:
    L = ["# VCGC connect 全景連線 · %s · %s · 總燈 %s · 綠 %d 黃 %d 紅 %d 灰 %d" % (TAG, res["at"], res["lamp"], *[res["counts"][k] for k in ("GREEN", "YELLOW", "RED", "GRAY")]),
         "## A 通道(VCGC MCP %s · %s · 工具 %d)" % (res["mcp_server"] or "—", res["mcp_why"], res["mcp_tools"])]
    L += ["[%s] %s · %s · %s%s" % (r["lamp"], r["name"], r["how"], r["evidence"], (" · " + r["note"]) if r.get("note") else "") for r in res["channels"]]
    L.append("## B 工具")
    L += ["[%s] %s · %s · %s" % (r["lamp"], r["name"], r["evidence"], r["note"]) for r in res["tools"]]
    b = res["backup"]
    L += ["## C 備份 / 讀取", "[%s] %s · %s · %s" % (b["lamp"], b["name"], b["evidence"], b["note"])]
    L.append("## D 文件類型(倉內已追蹤檔)")
    L += ["[%s] %s %d 檔(%s)· 讀法 %s%s · MCP %s · %s" % (r["lamp"], r["key"], r["count"], r["exts"], r["how"],
                                                       (" · 缺套件 " + " ".join(r["libs_missing"])) if r["libs_missing"] else "", r["mcp"], r["boundary"]) for r in res["doctypes"]]
    fix = [r["key"] for r in res["channels"] if r["lamp"] == "YELLOW" and r.get("path")]
    if any(r["lamp"] == "RED" for r in res["channels"]):
        nxt = "NEXT: 先修 A 段紅(MCP 握手 / GitHub / .mcp.json)"
    elif fix:
        nxt = "NEXT: connect config --apply 補 vcgc 到 " + "、".join(fix) + "(先留 .bak)"
    elif b["lamp"] != "GREEN":
        nxt = "NEXT: 備份 check 不綠 → 跑 VIA_DailyBackup backup 再 check"
    else:
        nxt = "NEXT: 裁定兩件:雲端 AI 要不要開 HTTPS 端點 · MCP 要不要加「只回結構」的讀檔工具"
    return L[:299] + [nxt]


def write(via: Path, res: dict, out_dir: Path = None) -> Path:
    out = out_dir or (via / "VIA_Reports" / "vcgc" / "connect")
    out.mkdir(parents=True, exist_ok=True)
    (out / "CONNECT_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    lines = _lines(res)
    (out / "CONNECT_latest.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    css = ""
    try:
        css = PRIOR._lamp_css(via)
    except Exception:
        css = ""

    def table(title, head, rows):
        return ("<h2>%s</h2><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
            html.escape(title), "".join("<th>%s</th>" % html.escape(h) for h in head),
            "".join("<tr><td><span class='lamp %s'></span>%s</td>%s</tr>" % (r[0], r[0], "".join("<td>%s</td>" % html.escape(str(x)) for x in r[1:])) for r in rows)))

    b = res["backup"]
    page = ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>VCGC connect</title><style>" + css +
            "body{font:11px/1.35 system-ui,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a;margin:12px}h1{font-size:14px;margin:0 0 6px}h2{font-size:12px;margin:12px 0 4px}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{padding:3px 6px;border-bottom:1px solid #e2e8f0;text-align:left;overflow-wrap:anywhere;white-space:normal}"
            "th{background:#f1f5f9}td:first-child,th:first-child{width:7em}</style><h1>VCGC 全景連線 · " + html.escape(res["lamp"]) + " · " + html.escape(lines[-1]) + "</h1>" +
            table("A 通道", ["燈", "通道", "連法", "證據", "說明"], [(r["lamp"], r["name"], r["how"], r["evidence"], r.get("note", "")) for r in res["channels"]]) +
            table("B 工具", ["燈", "工具", "證據", "說明"], [(r["lamp"], r["name"], r["evidence"], r["note"]) for r in res["tools"]]) +
            table("C 備份 / 讀取", ["燈", "項目", "證據", "說明"], [(b["lamp"], b["name"], b["evidence"], b["note"])]) +
            table("D 文件類型", ["燈", "類型", "檔數", "副檔名", "讀法", "MCP", "能否離機"],
                  [(r["lamp"], r["key"], r["count"], r["exts"], r["how"] + ((" · 缺 " + " ".join(r["libs_missing"])) if r["libs_missing"] else ""), r["mcp"], r["boundary"]) for r in res["doctypes"]]) +
            "</html>")
    (out / "CONNECT_latest.html").write_text(page, encoding="utf-8")
    return out


def config(apply: bool, via: Path = VIA_ROOT, paths: dict = None) -> list:
    """只補已存在的本機 stdio 設定檔;先 .bak;只加 vcgc 一項。"""
    v = _v116()
    tail = v.mcp_tail(via) if v else None
    if tail is None:
        return [("—", "找不到 MCP 尾版,不動")]
    entry = {"command": sys.executable, "args": [str(tail), "--serve", "--root", str(via)], "env": {"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES"}}
    done = []
    for k, cands in (paths or client_paths()).items():
        hit = next((p for p in cands if p.is_file()), None)
        if hit is None:
            continue
        cfg = _json(hit)
        if not isinstance(cfg, dict):
            done.append((str(hit), "讀不懂(不是 JSON 物件),不動"))
            continue
        if _has_vcgc(cfg):
            done.append((str(hit), "已有 vcgc"))
            continue
        key = "servers" if k == "copilot-vscode" else "mcpServers"
        if not apply:
            done.append((str(hit), "會加 %s.vcgc(加 --apply 才寫)" % key))
            continue
        shutil.copy2(hit, hit.with_name(hit.name + ".bak_" + time.strftime("%Y%m%d%H%M%S")))
        cfg.setdefault(key, {})["vcgc"] = entry
        tmp = hit.with_name(hit.name + ".tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, hit)
        done.append((str(hit), "已加 %s.vcgc(備份 .bak)" % key))
    return done or [("—", "本機沒有任何已存在的 Claude Desktop / Gemini CLI / VS Code 設定檔")]


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["connect"]:
        sub = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "check"
        if sub == "config":
            for p, msg in config("--apply" in argv):
                print("[connect config] %s · %s" % (msg, p), flush=True)
            return 0
        res = connect()
        print("\n".join(_lines(res)), flush=True)
        print("[報告] %s" % (VIA_ROOT / "VIA_Reports" / "vcgc" / "connect" / "CONNECT_latest.html"), flush=True)
        return 0 if res["lamp"] == "GREEN" else 1 if res["lamp"] == "RED" else 2
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 9 項 · 前版 %s)" % (TAG, PRIOR_PATH.name), flush=True)
    with tempfile.TemporaryDirectory(prefix="csm118_") as td:
        home, app = Path(td) / "home", Path(td) / "app"
        (app / "Claude").mkdir(parents=True)
        (home / ".gemini").mkdir(parents=True)
        (app / "Claude" / "claude_desktop_config.json").write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
        (home / ".gemini" / "settings.json").write_text(json.dumps({"mcpServers": {"vcgc": {"command": "py"}}}), encoding="utf-8")
        paths = client_paths(home, app)
        rows = {r["key"]: r for r in check_channels(VIA_ROOT, True, 17, paths)}
        chk("T1 雲端四家一律灰 + 待裁說明(不冒充可連)", all(rows[k]["lamp"] == "GRAY" and "待裁" in rows[k]["note"] for k in ("chatgpt", "manus", "perplexity", "grok")))
        chk("T2 本機:有 vcgc → 綠 · 檔在沒 vcgc → 黃 · 沒裝 → 灰", rows["gemini-cli"]["lamp"] == "GREEN" and rows["claude-desktop"]["lamp"] == "YELLOW"
            and rows["copilot-vscode"]["lamp"] == "GRAY", {k: rows[k]["lamp"] for k in ("gemini-cli", "claude-desktop", "copilot-vscode")})
        chk("T3 MCP 握手失敗 → PC 檔案紅", {r["key"]: r for r in check_channels(VIA_ROOT, False, 0, paths)}["pc-files"]["lamp"] == "RED")
        dry = config(False, VIA_ROOT, paths)
        raw = (app / "Claude" / "claude_desktop_config.json").read_text(encoding="utf-8")
        chk("T4 config 沒 --apply:只列不寫", any("會加" in m for _, m in dry) and "vcgc" not in raw, dry)
        done = config(True, VIA_ROOT, paths)
        cfg = json.loads((app / "Claude" / "claude_desktop_config.json").read_text(encoding="utf-8"))
        chk("T5 config --apply:只加 vcgc、別的伺服器原樣、留 .bak、不建新檔", "vcgc" in cfg["mcpServers"] and "other" in cfg["mcpServers"]
            and list((app / "Claude").glob("*.bak_*")) and not (app / "Code").exists(), done)
        t = {r["key"]: r for r in check_tools(VIA_ROOT, home)}
        chk("T6 工具段:Ponytail / Agency-mem 沒裝 → 灰,Agency-mem 帶 11-06 裁定", t["ponytail"]["lamp"] == "GRAY" and t["agency-mem"]["lamp"] == "GRAY" and "11-06" in t["agency-mem"]["note"])
        res = {"tag": TAG, "at": utc(), "mcp_server": "x", "mcp_tools": 17, "mcp_why": "握手成功", "channels": list(rows.values()), "tools": list(t.values()),
               "backup": {"lamp": "YELLOW", "name": "備份", "evidence": "e", "note": "n"},
               "doctypes": [{"key": "程式", "exts": ".py", "count": 3, "how": "read", "libs_missing": [], "mcp": "否", "boundary": "結構可離機", "lamp": "YELLOW"}],
               "lamp": "YELLOW", "counts": {"GREEN": 1, "YELLOW": 2, "RED": 0, "GRAY": 3}}
        out = write(VIA_ROOT, res, Path(td) / "out")
        txt = (out / "CONNECT_latest.txt").read_text(encoding="utf-8").splitlines()
        chk("T7 報告:txt NEXT: 結尾 · html 四段、燈在第一欄", txt[-1].startswith("NEXT:") and len(txt) <= 300
            and (out / "CONNECT_latest.html").read_text(encoding="utf-8").count("<h2>") == 4 and "<td><span class='lamp" in (out / "CONNECT_latest.html").read_text(encoding="utf-8"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T8 檔面:第 3 行加速器標記 · 零 TA-Lib · 不設同意閘 · 不連外(無連網呼叫 · 無 git 拉推)",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("url" + "open") not in src and not re.search(r"\[\s*['\"]git['\"]\s*,\s*['\"](fetch|pull|clone|push)", src))
    prior_rc = PRIOR.selftest()
    chk("T9 前版 %s 自測照過" % PRIOR_PATH.name, prior_rc == 0, prior_rc)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
