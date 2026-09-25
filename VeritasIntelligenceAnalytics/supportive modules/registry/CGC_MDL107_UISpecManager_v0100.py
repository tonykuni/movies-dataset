#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL107_UISpecManager v0100 — UI 元件三語轉碼系統管理器(9hh5to 令)
======================================================================
操作員令:「transfer into coding in three languages, coordinated by
system manager in Python」。本件=Python 統籌管理器,五段:
  ① 抽取  目標 HTML(預設 GovDeck/VapDeck 尾版)→元件六類
     (STYLE/SCRIPT/SVG/TABLE/SECTION/ASIDE;regex 道,本艦 token
     冊制頁面為適用域=誠實標)
  ② 對照  元件內 hex 色×VIA_UI_TemplateSSOT palette→token 命中
     +偏差誠實列
  ③ 轉碼  逐元件出三語:component.py(SPEC+render)/component.js
     (SPEC+mount 注入)/component.ps1(base64 fragment+旁建注入函)
  ④ 驗同  真驗非紙面:py=exec 後 render()==原片段;js=SPEC JSON
     解回==原片段;ps1=base64 解回==原片段→parity 三真值入冊
  ⑤ 登冊  VIA_UISpec_Registry_v0100.json(append-only;同 sha 冪等
     跳過)+矩陣印出
移植:--transfer <CMP_ID> --into <頁> = 旁建側本注入(零覆寫零破壞)。
紅線:唯讀來源;產出全落 components/ 新夾+側本;誠實三態。
用法:python3 CGC_MDL107_UISpecManager_v0100.py [--selftest|
     --pages a.html b.html | --transfer UIC_xxxx --into 頁.html]
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
import base64
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UIDIR = VIA / "supportive modules" / "ui_support"
CMPDIR = UIDIR / "components"
REGP = (VIA / "VIA_Reports" / "uispec_runs"
        / "VIA_UISpec_Registry_v0100.json")  # 存證區(同 GRID 慣例;防拉取卡檔)
SSOTP = HERE / "VIA_UI_TemplateSSOT_v0100.json"
KINDS = (("style", r"<style[^>]*>(.*?)</style>", "STYLE_BLOCK"),
         ("script", r"<script[^>]*>(.*?)</script>", "SCRIPT_BLOCK"),
         ("svg", r"<svg[\s>].*?</svg>", "SVG_BLOCK"),
         ("table", r"<table[\s>].*?</table>", "TABLE_BLOCK"),
         ("section", r"<section[\s>].*?</section>", "SECTION_BLOCK"),
         ("aside", r"<aside[\s>].*?</aside>", "ASIDE_BLOCK"))
HEX_RX = re.compile(r"#[0-9a-fA-F]{6}\b")


def banner(t):
    print(f"── {t} ──")


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ── ① 抽取 ──
def extract_components(html: str, page: str) -> list[dict]:
    out = []
    for kind, rx, label in KINDS:
        for i, m in enumerate(re.finditer(rx, html, re.S | re.I), 1):
            frag = m.group(0)
            body = m.group(1) if m.groups() else frag
            out.append({"page": page, "kind": label, "idx": i,
                        "frag": frag, "css_scope": body if kind == "style" else "",
                        "len": len(frag), "sha": _sha(frag)[:16],
                        "id": f"UIC_{_sha(page + label + str(i) + frag)[:8]}"})
    return out


# ── ② token 對照 ──
def token_map(cmp: dict) -> dict:
    try:
        pal = json.loads(SSOTP.read_text(encoding="utf-8")).get("palette", {})
    except Exception:
        pal = {}
    rev = {v.lower(): k for k, v in pal.items() if isinstance(v, str)}
    hexes = {h.lower() for h in HEX_RX.findall(cmp["frag"])}
    hit = sorted(f"{rev[h]}={h}" for h in hexes if h in rev)
    dev = sorted(h for h in hexes if h not in rev)
    return {"tokens": hit, "deviations": dev}


# ── ③ 三語轉碼 ──
def emit_py(cmp: dict, d: Path) -> Path:
    spec = {k: cmp[k] for k in ("id", "page", "kind", "idx", "sha")}
    p = d / "component.py"
    p.write_text(
        "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"
        f'"""UI 元件(三語轉碼之 Python 語):{cmp["id"]} · {cmp["kind"]}'
        f' · 源 {cmp["page"]}(MDL107 管理器產;SPEC 內嵌零外依)"""\n'
        f"SPEC = {json.dumps(spec, ensure_ascii=False)}\n"
        f"FRAGMENT = {json.dumps(cmp['frag'], ensure_ascii=False)}\n\n\n"
        "def render() -> str:\n    return FRAGMENT\n\n\n"
        "def preview_page() -> str:\n"
        "    return ('<!DOCTYPE html><html lang=\"zh-Hant\"><head>"
        "<meta charset=\"utf-8\"></head><body>' + FRAGMENT + '</body></html>')\n\n\n"
        "if __name__ == '__main__':\n    print(render())\n",
        encoding="utf-8")
    return p


def emit_js(cmp: dict, d: Path) -> Path:
    spec = {"id": cmp["id"], "kind": cmp["kind"], "sha": cmp["sha"],
            "html": cmp["frag"]}
    p = d / "component.js"
    p.write_text(
        f"// UI 元件(三語轉碼之 JS 語):{cmp['id']} · {cmp['kind']}(MDL107 產)\n"
        f"var VIA_CMP_SPEC = {json.dumps(spec, ensure_ascii=False)};\n"
        "function mount(sel){var el=document.querySelector(sel);\n"
        " if(el){el.insertAdjacentHTML('beforeend', VIA_CMP_SPEC.html);}return !!el;}\n",
        encoding="utf-8")
    return p


def emit_ps1(cmp: dict, d: Path) -> Path:
    b64 = base64.b64encode(cmp["frag"].encode("utf-8")).decode("ascii")
    p = d / "component.ps1"
    p.write_text(
        f"# UI 元件(三語轉碼之 PowerShell 語):{cmp['id']} · {cmp['kind']}(MDL107 產)\n"
        "# base64 fragment=零跳脫風險;Write-Component=旁建側本注入(零覆寫)\n"
        f"$CmpId = '{cmp['id']}'\n"
        f"$FragmentB64 = '{b64}'\n"
        "$Fragment = [System.Text.Encoding]::UTF8.GetString("
        "[System.Convert]::FromBase64String($FragmentB64))\n"
        "function Write-Component([string]$TargetHtml) {\n"
        "  $html = Get-Content -Raw -Encoding UTF8 $TargetHtml\n"
        "  $out = $html -replace '</body>', ($Fragment + \"`n</body>\")\n"
        "  $dir = Join-Path (Split-Path -Parent $TargetHtml) '_transfers'\n"
        "  New-Item -ItemType Directory -Force -Path $dir | Out-Null\n"
        "  $leaf = (Split-Path -Leaf $TargetHtml) -replace '\\.html$', "
        "('__with_' + $CmpId + '.html')\n"
        "  $side = Join-Path $dir $leaf\n"
        "  Set-Content -Encoding UTF8 -Path $side -Value $out\n"
        "  Write-Host ('[旁建隔離夾] ' + $side)\n}\n"
        "if ($args.Count -ge 1) { Write-Component $args[0] } else { $Fragment }\n",
        encoding="utf-8")
    return p


# ── ④ 驗同(真驗非紙面)──
def verify_parity(cmp: dict, d: Path) -> dict:
    par = {"py": False, "js": False, "ps1": False}
    try:
        ns: dict = {}
        exec((d / "component.py").read_text(encoding="utf-8"), ns)
        par["py"] = ns["render"]() == cmp["frag"]
    except Exception:
        pass
    try:
        line = next(ln for ln in (d / "component.js").read_text(
            encoding="utf-8").splitlines() if ln.startswith("var VIA_CMP_SPEC = "))
        par["js"] = json.loads(line[len("var VIA_CMP_SPEC = "):-1])["html"] == cmp["frag"]
    except Exception:
        pass
    try:
        m = re.search(r"\$FragmentB64 = '([A-Za-z0-9+/=]+)'",
                      (d / "component.ps1").read_text(encoding="utf-8"))
        par["ps1"] = base64.b64decode(m.group(1)).decode("utf-8") == cmp["frag"]
    except Exception:
        pass
    return par


# ── ⑤ 登冊 ──
def register(rows: list[dict]) -> tuple[int, int]:
    REGP.parent.mkdir(parents=True, exist_ok=True)
    if REGP.exists():
        reg = json.loads(REGP.read_text(encoding="utf-8"))
    else:
        reg = {"registry_id": "VIA_UISpec_Registry", "append_only": True,
               "policy": "元件三語轉碼冊:同 sha 冪等跳過;來源唯讀;產出旁建",
               "components": [], "runs": []}
    known = {c["sha"] for c in reg["components"]}
    new = 0
    for r in rows:
        if r["sha"] in known:
            continue
        reg["components"].append(r)
        known.add(r["sha"])
        new += 1
    reg["runs"].append({"ts": datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "scanned": len(rows), "new": new})
    REGP.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    return new, len(reg["components"])


def run(pages: list[Path]) -> int:
    banner("① 抽取(六類元件;token 冊制頁面適用域)")
    comps = []
    for pg in pages:
        try:
            html = pg.read_text(encoding="utf-8")
        except Exception:
            print(f"  [SKIP] {pg.name} 讀取缺(誠實)")
            continue
        cs = extract_components(html, pg.name)
        print(f"  {pg.name}:{len(cs)} 件")
        comps += cs
    if not comps:
        print("  零元件=誠實停")
        return 1
    banner("② token 對照(TemplateSSOT palette)")
    for c in comps:
        c.update(token_map(c))
    ndev = sum(1 for c in comps if c["deviations"])
    print(f"  命中 token 元件 {sum(1 for c in comps if c['tokens'])} · 有偏差色 {ndev}(誠實列)")
    banner("③ 三語轉碼(py/js/ps1)")
    rows = []
    for c in comps:
        d = CMPDIR / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        emit_py(c, d)
        emit_js(c, d)
        emit_ps1(c, d)
        banner4 = c  # noqa
        rows.append(c)
    print(f"  出碼 {len(rows)} 件 × 3 語 → {CMPDIR}")
    banner("④ 驗同(exec/JSON/base64 三道真解回對原)")
    ok3 = 0
    for c in rows:
        c["parity"] = verify_parity(c, CMPDIR / c["id"])
        if all(c["parity"].values()):
            ok3 += 1
    print(f"  三語全同 {ok3}/{len(rows)}(不同=誠實列冊)")
    banner("⑤ 登冊(append-only;同 sha 冪等)")
    slim = [{k: c[k] for k in ("id", "page", "kind", "idx", "len", "sha",
                               "tokens", "deviations", "parity")} for c in rows]
    new, total = register(slim)
    print(f"  新登 {new} · 冊總 {total} · {REGP.name}")
    print(f"  [計] 元件 {len(rows)} · 三語全同 {ok3} · 偏差色 {ndev} · 冊 {total}")
    return 0 if ok3 == len(rows) else 1


def transfer(cmp_id: str, into: Path) -> int:
    reg = json.loads(REGP.read_text(encoding="utf-8")) if REGP.exists() else {}
    hit = next((c for c in reg.get("components", []) if c["id"] == cmp_id), None)
    if not hit:
        print(f"  ✗ {cmp_id} 不在冊(先跑抽取)")
        return 1
    frag = None
    pyp = CMPDIR / cmp_id / "component.py"
    if pyp.exists():
        ns: dict = {}
        exec(pyp.read_text(encoding="utf-8"), ns)
        frag = ns["render"]()
    if frag is None:
        print("  ✗ 元件碼缺(誠實)")
        return 1
    html = into.read_text(encoding="utf-8")
    td = CMPDIR / "_transfers"  # 隔離夾:側本永不落 ui_support 根
    td.mkdir(parents=True, exist_ok=True)  # (防尾版 glob 誤食=鐵律護欄)
    side = td / f"{into.stem}__with_{cmp_id}.html"
    side.write_text(html.replace("</body>", frag + "\n</body>"),
                    encoding="utf-8")
    print(f"  [旁建] {side}(原頁零觸碰;隔離夾防 glob 誤食)")
    return 0


def selftest() -> int:
    import tempfile
    fails = []
    n = [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    fx = ('<!DOCTYPE html><html><head><style>.a{color:#f6f7f9;'
          'background:#123456}</style></head><body>'
          '<section id="s1"><table><tr><td>x</td></tr></table></section>'
          '<aside class="g"><b>閘</b></aside>'
          '<svg viewBox="0 0 1 1"><rect/></svg>'
          "<script>var q=1;</script></body></html>")
    cs = extract_components(fx, "fx.html")
    kinds = sorted(c["kind"] for c in cs)
    chk("① 六類抽取(style/script/svg/table/section/aside 各一)",
        kinds == ["ASIDE_BLOCK", "SCRIPT_BLOCK", "SECTION_BLOCK",
                  "STYLE_BLOCK", "SVG_BLOCK", "TABLE_BLOCK"])
    st = next(c for c in cs if c["kind"] == "STYLE_BLOCK")
    tm = token_map(st)
    chk("② token 對照(#f6f7f9=bg 命中;#123456=偏差誠實列)",
        any("bg=#f6f7f9" in t for t in tm["tokens"])
        and "#123456" in tm["deviations"])
    with tempfile.TemporaryDirectory() as td:
        global CMPDIR, REGP
        oc, orp = CMPDIR, REGP
        CMPDIR, REGP = Path(td) / "cmp", Path(td) / "reg.json"
        try:
            c = next(x for x in cs if x["kind"] == "ASIDE_BLOCK")
            c.update(token_map(c))
            d = CMPDIR / c["id"]
            d.mkdir(parents=True)
            emit_py(c, d)
            emit_js(c, d)
            emit_ps1(c, d)
            chk("③ 三語出碼(component.py/js/ps1 三檔齊)",
                all((d / f"component.{e}").exists() for e in ("py", "js", "ps1")))
            par = verify_parity(c, d)
            chk("④ 驗同三真(exec 回原/JSON 回原/base64 回原)",
                par == {"py": True, "js": True, "ps1": True})
            bad = dict(c)
            bad["frag"] = c["frag"] + "<i>改</i>"
            chk("④b 竄改=驗同誠實 False(非紙面)",
                verify_parity(bad, d)["py"] is False)
            row = {k: c[k] for k in ("id", "page", "kind", "idx", "len", "sha",
                                     "tokens", "deviations")}
            row["parity"] = par
            n1, t1 = register([row])
            n2, t2 = register([row])
            chk("⑤ 登冊 append-only+同 sha 冪等(再登=0 新)",
                n1 == 1 and t1 == 1 and n2 == 0 and t2 == 1)
            tgt = Path(td) / "page.html"
            tgt.write_text("<html><body><p>頁</p></body></html>", encoding="utf-8")
            rc = transfer(c["id"], tgt)
            side = CMPDIR / "_transfers" / f"page__with_{c['id']}.html"
            chk("⑥ 移植=旁建側本(原頁零觸碰+片段入側本)",
                rc == 0 and side.exists() and c["frag"] in side.read_text(encoding="utf-8")
                and "閘" not in tgt.read_text(encoding="utf-8").replace("頁", ""))
            chk("⑥b 冊外移植誠實拒", transfer("UIC_nope", tgt) == 1)
        finally:
            CMPDIR, REGP = oc, orp
    chk("⑦ 真頁抽取(GovDeck 尾版≥3 件;唯讀)",
        len(extract_components(
            sorted(UIDIR.glob("VIA_UI_GovDeck_v0*.html"))[-1].read_text(
                encoding="utf-8"), "govdeck")) >= 3)
    print(f"  [計] 自測 {n[0]} 項 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== UI 元件三語轉碼管理器(CGC_MDL107)· 自測 ===")
        return selftest()
    if "--transfer" in a:
        cid = a[a.index("--transfer") + 1]
        into = Path(a[a.index("--into") + 1])
        return transfer(cid, into)
    print("=== UI 元件三語轉碼(Python 系統管理器)· 五段 · 唯讀來源+旁建產出 ===")
    if "--pages" in a:
        pages = [Path(x) for x in a[a.index("--pages") + 1:]]
    else:
        pages = [sorted(UIDIR.glob(g))[-1] for g in
                 ("VIA_UI_GovDeck_v0*.html", "VIA_UI_VapDeck_v0*.html")
                 if sorted(UIDIR.glob(g))]
    return run(pages)


if __name__ == "__main__":
    sys.exit(main())
