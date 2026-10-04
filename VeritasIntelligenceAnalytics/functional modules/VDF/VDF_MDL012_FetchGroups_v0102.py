#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL012_FetchGroups v0102 — 薄尾:ui 自適應模板(任何 .html 範本套同一份族群快照)+ 對接快照檔

操作員 2026-10-04:「將啟動指令對接 U/I,可以自適應式其他模板範本」。
  ui [--template 名或路徑] [--list-templates] [--home H] [--out F] [--as-of D] [--watch N]
    · 不給 --template = v0101 正典族群頁(左面板功能 + Live log · 右面板多頁)。
    · --template X.html:從範本夾找(本檔同夾 ui_templates\ → <VIA>\VIA_Reports\vdf\ui\templates\ → 直接路徑),
      ① 有 Jinja 語法({% %} / {{ }})且裝了 jinja2 → 沙盒環境渲染,變數 = 快照頂層鍵(groups · engines · as_of · live …)
      ② 沒有 jinja2 → {{ a.b.c }} 逐個代換(找不到的鍵照留原字、列在報告裡,不假填)
      ③ 一律在 </head> 前注入 window.VIA = 快照、鎖定色令牌(SUP_MDL750)、四燈樣式 .lamp-GREEN/YELLOW/RED/NODATA
      輸出 <VIA>\VIA_Reports\vdf\ui\VDF_FetchGroups_<範本名>.html(範本原檔零觸碰)。
    · 每次 ui 都寫對接快照 <VIA>\VIA_Reports\vdf\ui\VDF_FetchGroups_SNAPSHOT_latest.json(工作站 ENG234 等其他 U/I 讀它就能接上,
      頁不直讀庫:引擎 → JSON → 頁)。
    · --list-templates 列範本夾內可用的 .html 與各自用到的變數。
其餘動詞全照 v0101 / v0100。產生器不開瀏覽器(PS 啟動器 Invoke-VDF-FetchGroupsUI-v0100.ps1 才開)。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入;本檔零網路,橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import html
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VDF_MDL012_FetchGroups_v0101.py"
_spec = importlib.util.spec_from_file_location("VDF_MDL012_FetchGroups_v0101_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PRIOR.TAG = TAG
PRIOR.PRIOR.TAG = TAG
VIA = PRIOR.VIA
OUT_DIR = VIA / "VIA_Reports" / "vdf" / "ui"
SNAP_LATEST = OUT_DIR / "VDF_FetchGroups_SNAPSHOT_latest.json"
TEMPLATE_DIRS = [HERE / "ui_templates", OUT_DIR / "templates"]
_VAR = re.compile(r"\{\{\s*([A-Za-z_][\w]*(?:\.[\w]+)*)\s*(?:\|[^}]*)?\}\}")
_JINJA_BLOCK = re.compile(r"\{%")
LAMP_CSS = (".lamp-GREEN{background:rgba(63,185,132,.18);color:#3FB984}.lamp-YELLOW{background:rgba(224,179,65,.18);color:#E0B341}"
            ".lamp-RED{background:rgba(224,108,96,.18);color:#E06C60}.lamp-NODATA,.lamp-NODATE,.lamp-LOCKED{background:rgba(140,153,166,.16);color:#8C99A6}")

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_LIVE_V0101 = PRIOR.live_log


def live_log_v0102(home: Path, n: int = 160) -> dict:
    """同 v0101,但日誌行先清:ANSI 色碼 / 控制字元拿掉、tqdm 的 \\r 覆寫只留最後一段、空行與純進度條行不顯示。"""
    d = _LIVE_V0101(home, n)
    out = []
    for ln in d.get("lines", []):
        src, _, body = ln.partition("] ")
        body = _ANSI.sub("", body.split("\r")[-1]).rstrip()
        if not body or re.fullmatch(r"\s*\d+%\|.*\|\s*\d+/\d+.*", body):
            continue
        out.append(f"{src}] {body}")
    d["lines"] = out
    return d


PRIOR.live_log = live_log_v0102


def find_template(name: str) -> Path | None:
    p = Path(name)
    if p.is_file():
        return p
    for d in TEMPLATE_DIRS:
        for cand in (d / name, d / (name + ".html")):
            if cand.is_file():
                return cand
    return None


def list_templates() -> list:
    out = []
    for d in TEMPLATE_DIRS:
        for p in sorted(d.glob("*.html")) if d.is_dir() else []:
            t = p.read_text(encoding="utf-8", errors="replace")
            out.append({"name": p.name, "dir": str(d), "kb": round(p.stat().st_size / 1024, 1),
                        "vars": sorted(set(_VAR.findall(t)))[:40], "jinja_blocks": bool(_JINJA_BLOCK.search(t))})
    return out


def _lookup(snap: dict, dotted: str):
    cur = snap
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return KeyError
    return cur


def _tokens_css() -> str:
    hits = sorted((PRIOR.UI_DIR).glob("SUP_MDL750_VeritasUIHead_v*.py"), key=PRIOR.PRIOR._vnum)
    if hits:
        try:
            sp = importlib.util.spec_from_file_location("veritas_ui_head_for_mdl012_v0102", hits[-1])
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
            return m.tokens_css()
        except Exception:
            pass
    return ":root{--via-ok:#3FB984;--via-warn:#E0B341;--via-bad:#E06C60;--via-muted:#8C99A6}"


def render_template(tpl: str, snap: dict) -> tuple:
    """回 (頁, 報告)。Jinja 有裝且範本用了區塊語法 → 沙盒渲染;否則逐變數代換,找不到的照留。"""
    report = {"engine": "", "vars": [], "missing": []}
    used = sorted(set(_VAR.findall(tpl)))
    report["vars"] = used
    out = None
    if _JINJA_BLOCK.search(tpl) or used:
        try:
            from jinja2.sandbox import SandboxedEnvironment
            from jinja2 import Undefined
            env = SandboxedEnvironment(autoescape=True, undefined=Undefined)
            out = env.from_string(tpl).render(**snap, snapshot=snap, VIA=snap)
            report["engine"] = "jinja2(沙盒)"
            bound = set(re.findall(r"\{%-?\s*(?:for|set)\s+([A-Za-z_]\w*)", tpl)) | {"snapshot", "VIA", "loop"}   # 迴圈 / set 綁定的名不算缺
            report["missing"] = [v for v in used if _lookup(snap, v) is KeyError and v.split(".")[0] not in bound]
        except ImportError:
            out = None
        except Exception as exc:
            report["engine"] = f"jinja2 失敗 → 逐變數代換({type(exc).__name__}: {str(exc)[:80]})"
            out = None
    if out is None:
        if not report["engine"]:
            report["engine"] = "逐變數代換"

        def sub(m):
            v = _lookup(snap, m.group(1))
            if v is KeyError:
                report["missing"].append(m.group(1))
                return m.group(0)
            return html.escape(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str))
        out = _VAR.sub(sub, tpl)
    inject = ("<!-- [VIA:TEMPLATE-INJECT:v0100] VDF_MDL012 v0102 -->"
              f"<style>{_tokens_css()}\n{LAMP_CSS}</style>"
              '<script>window.VIA = ' + json.dumps(snap, ensure_ascii=False, default=str).replace("</", "<\\/") + ";</script>")
    if re.search(r"</head>", out, re.I):
        out = re.sub(r"</head>", lambda m: inject + m.group(0), out, count=1, flags=re.I)   # 函式代換:快照裡的 \\ 路徑不當跳脫
    else:
        out = inject + out
    report["missing"] = sorted(set(report["missing"]))
    if not report["engine"].startswith("jinja2(") and _JINJA_BLOCK.search(tpl):
        report["note"] = "本境缺 jinja2:{% %} 區塊原樣留在頁上沒渲染(裝 jinja2 或改用純 {{ 變數 }} 範本)"
    return out, report


def write_snapshot(snap: dict, path: Path | None = None) -> Path:
    path = path or SNAP_LATEST
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(snap, ensure_ascii=False, default=str, indent=1), encoding="utf-8")
    os.replace(tmp, path)
    return path


def build_templated(home: Path, template: str, out: Path | None, as_of: str | None) -> tuple:
    tp = find_template(template)
    if not tp:
        raise FileNotFoundError(f"找不到範本 {template}(找過:{' · '.join(str(d) for d in TEMPLATE_DIRS)})")
    snap = PRIOR.gather(home, as_of)
    write_snapshot(snap)
    page, rep = render_template(tp.read_text(encoding="utf-8", errors="replace"), snap)
    out = out or OUT_DIR / (tp.stem + ".html" if tp.stem.startswith("VDF_FetchGroups_") else f"VDF_FetchGroups_{tp.stem}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out)
    return snap, out, tp, rep


def cmd_ui(argv: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG} ui")
    ap.add_argument("--home"); ap.add_argument("--out"); ap.add_argument("--as-of"); ap.add_argument("--template")
    ap.add_argument("--list-templates", action="store_true")
    ap.add_argument("--watch", type=int, default=0); ap.add_argument("--watch-max", type=int, default=0)
    a = ap.parse_args(argv)
    if a.list_templates:
        rows = list_templates()
        print(f"[範本] {len(rows)} 份 · 夾:{' · '.join(str(d) for d in TEMPLATE_DIRS)}")
        for r in rows:
            print(f"  {r['name']:<44} {r['kb']:>7} KB · Jinja 區塊 {'有' if r['jinja_blocks'] else '無'} · 變數 {', '.join(r['vars'][:8])}")
        return 0
    if not a.template:
        rc = PRIOR.cmd_ui(a)
        try:
            write_snapshot(PRIOR.gather(PRIOR.PRIOR._ctx(a)[-1], a.as_of))
            print(f"[對接] 快照 → {SNAP_LATEST}")
        except Exception as exc:
            print(f"[對接] 快照沒寫成:{type(exc).__name__}: {exc}")
        return rc
    home = PRIOR.PRIOR._ctx(a)[-1]
    t_end = time.time() + (a.watch_max or 4 * 3600)
    idle = None
    while True:
        snap, out, tp, rep = build_templated(home, a.template, Path(a.out) if a.out else None, a.as_of)
        print(f"[ui · 範本] {tp.name} → {out} · {round(out.stat().st_size / 1024, 1)} KB · 引擎 {rep['engine']} · 變數 {len(rep['vars'])}"
              + (f" · 找不到 {len(rep['missing'])}:{', '.join(rep['missing'][:6])}(照留原字)" if rep["missing"] else "")
              + (f" · ⚠ {rep['note']}" if rep.get("note") else "")
              + f" · as-of {snap['as_of']} · 對接快照 {SNAP_LATEST.name}")
        if not a.watch:
            return 0
        idle = None if snap["live"]["running"] else (idle or time.time())
        if time.time() > t_end or (idle and time.time() - idle > 1800):
            return 0
        time.sleep(max(5, a.watch))


# ---------- 自測 ----------
def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = PRIOR.selftest()
    PRIOR.TAG = TAG
    chk("① v0101 自測照過(本版 8 + v0100 14)", prior_rc == 0, buf.getvalue()[-300:])
    snap = {"as_of": "2026-10-02", "tool": TAG, "groups": [{"id": "TW_DAILY", "zh": "台股每日行情", "summary": {"worst": "GREEN"}},
                                                            {"id": "SHIPPING", "zh": "航運指數", "summary": {"worst": "YELLOW"}}],
            "live": {"running": False}, "home": "C:\\Users\\x\\via_database\\vdf_fetch"}
    tpl1 = "<html><head><title>{{ tool }}</title></head><body><b>{{ as_of }}</b> {{ groups.1.zh }} {{ nope.x }}</body></html>"
    out1, rep1 = render_template(tpl1, snap)
    chk("② 純 HTML 範本:{{ }} 代換(含點路徑 groups.1.zh)· 注入 window.VIA + 鎖定色 + 四燈(快照含 Windows 反斜線路徑也注入得進)· 找不到的變數照留不假填",
        "<b>2026-10-02</b> 航運指數" in out1 and "window.VIA = " in out1 and "--via-ok" in out1 and ".lamp-YELLOW" in out1
        and out1.index("window.VIA") < out1.index("</head>") and "nope.x" in rep1["missing"], rep1)
    tpl2 = ("<html><head></head><body>{% for g in groups %}<i class='lamp-{{ g.summary.worst }}'>{{ g.zh }}</i>{% endfor %}"
            "{{ '<script>' }}</body></html>")
    out2, rep2 = render_template(tpl2, snap)
    try:
        import jinja2  # noqa: F401
        has_j2 = True
    except ImportError:
        has_j2 = False
    if has_j2:
        chk("③ Jinja 範本:沙盒渲染迴圈 · 自動跳脫(<script> 字串不成標籤)",
            "<i class='lamp-GREEN'>台股每日行情</i><i class='lamp-YELLOW'>航運指數</i>" in out2 and "&lt;script&gt;" in out2
            and rep2["engine"].startswith("jinja2"), (rep2, out2[-200:]))
    else:
        chk("③ 本境缺 jinja2:不崩、退逐變數代換、照實註明 Jinja 區塊沒渲染(不假裝渲染過)",
            rep2["engine"] == "逐變數代換" and "{% for g in groups %}" in out2 and "jinja2" in rep2.get("note", "")
            and "window.VIA = " in out2, rep2)
    tpl3 = "<div>{{ __class__.__mro__ }}{% set x = ''.__class__ %}{{ x.__subclasses__() }}</div>"
    out3, rep3 = render_template(tpl3, snap)
    chk("④ 沙盒擋得住:範本碰不到 Python 內部(__subclasses__ 不展開)", "subprocess" not in out3 and "Popen" not in out3, (rep3, out3[:200]))
    tmp = Path(tempfile.mkdtemp(prefix="mdl012tpl_"))
    try:
        global SNAP_LATEST, TEMPLATE_DIRS, OUT_DIR
        keep = (SNAP_LATEST, list(TEMPLATE_DIRS), OUT_DIR)
        OUT_DIR = tmp / "out"
        SNAP_LATEST = OUT_DIR / "VDF_FetchGroups_SNAPSHOT_latest.json"
        TEMPLATE_DIRS = [tmp / "tpl"]
        (tmp / "tpl").mkdir()
        (tmp / "tpl" / "Mini.html").write_text("<html><head></head><body>as-of {{ as_of }} · {{ groups.0.zh }}</body></html>", encoding="utf-8")
        home = tmp / "home"
        (home / "output_hub").mkdir(parents=True)
        lst = list_templates()
        snap2, out, tp, rep = build_templated(home, "Mini", None, "2026-10-02")
        body = out.read_text(encoding="utf-8")
        js = json.loads(SNAP_LATEST.read_text(encoding="utf-8"))
        chk("⑤ 範本夾:列得出(含用到的變數)· 名字不帶 .html 也找得到 · 輸出 VDF_FetchGroups_<範本>.html · 範本原檔零觸碰",
            [r["name"] for r in lst] == ["Mini.html"] and "as_of" in lst[0]["vars"] and out.name == "VDF_FetchGroups_Mini.html"
            and "as-of 2026-10-02 · 台股每日行情" in body
            and (tmp / "tpl" / "Mini.html").read_text(encoding="utf-8").count("{{") == 2)
        chk("⑥ 對接快照:每次產頁都寫 SNAPSHOT_latest.json(13 族群 · as-of 同一天),其他 U/I 讀它就接上",
            js["as_of"] == "2026-10-02" and len(js["groups"]) == len(snap2["groups"]) >= 13)
        try:
            build_templated(home, "NoSuch", None, "2026-10-02")
            ok = False
        except FileNotFoundError as exc:
            ok = "找不到範本" in str(exc)
        chk("⑦ 範本不在 = 誠實報找不到(列出找過的夾),不退回別頁假裝成功", ok)
        SNAP_LATEST, TEMPLATE_DIRS, OUT_DIR = keep
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    shipped = list((HERE / "ui_templates").glob("*.html"))
    chk("⑧ 隨附範例範本至少一份(ui_templates\\)", len(shipped) >= 1, shipped)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0101 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "ui":
        return cmd_ui(argv[1:])
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
