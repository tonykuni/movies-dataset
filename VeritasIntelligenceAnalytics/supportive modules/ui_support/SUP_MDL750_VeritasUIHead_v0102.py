#!/usr/bin/env python3
# 批631:本檔 v0101 的 docstring 裡有 `\d` / `\*` 這種**在字串裡不是合法跳脫**的序列,
#   而那個 docstring 不是 raw string。py3.11 只給 DeprecationWarning(預設不印),
#   **py3.12 給 SyntaxWarning 並印到終端**——工作站的矩陣輸出被它插進來,
#   連帶把 docstring 那一行也印出來,表格當場被切斷。
#   修法:那個 docstring 改成 r"""…"""(一個字元),語意零變。
# -*- coding: utf-8 -*-
"""SUP_MDL750:Veritas 正典頁頭件(畫面統一的唯一出處)。

批576。操作員批574 給了 Veritas 統一表頭的完整規格,批575 之後 U/I 閘量到的實情是:
**72 張尾版頁裡 18 張紅**,而紅的原因高度集中——零 CDN 9、零彈窗 4、viewport 5、lang 2。
這些全是**頁頭**的事。每一支產頁引擎各自抄一份 `<head>`,就會各自漏掉不同的一項,
而且一漏就是十幾張頁一起漏(L61 規則收斂律)。

所以不再一張一張補頁,而是立**一個頁頭正本**:

    from SUP_MDL750_VeritasUIHead_v0100 import page, veritas_header, SUBSYSTEMS
    html = page("VIA · 資料鍛造 VDF 現況台", body_html,
                subsystem="VeritasDataForge")

這一件同時滿足 CGC_MDL160 畫面統一閘的**全部 13 條**契約:
  LAW      零 CDN · 零彈窗 · UTF-8 · viewport · lang="zh-Hant"
  UNIFY    <title> · :root 主題令牌 · 頁腳 VIA 標記
  ADVISORY prefers-color-scheme 深色模式
  TARGET   veritas-header 結構 · 母品牌行 · 三行小/大/小 · 水墨配色 #121417 / #090A0B

自測的做法是**把閘的尺搬過來對自己跑**(契約耦合):本件產出的樣頁必須通過
CGC_MDL160 的 CONTRACT 每一條;閘改了尺,這裡當場紅——兩邊永遠不會各說各話。

紀律:零網路 · 零 CDN(只用系統字體堆疊)· 零彈窗 · 零第三方 · 純函式無副作用。
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

import html as _html
import sys
from datetime import datetime
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]

# ── 操作員批574 原文規格(一個字都不改;要改是操作員的手)──────────────────
FONT_STACK = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
              'Helvetica, Arial, "Noto Sans TC", "Microsoft JhengHei", sans-serif')
INK = {
    "header_bg": "#121417",
    "page_bg": "#090A0B",
    "row1": "#8C99A6",
    "row2": "#F0F4F8",
    "row3": "#737D87",
    "rule": "rgba(255,255,255,0.08)",
    "pad": "32px 40px",
    "gap": "8px",
}
ROW_SPEC = {
    "row1": {"size": "13px", "weight": "400", "ls": "1.2px"},
    "row2": {"size": "26px", "weight": "600", "ls": "0.3px"},
    "row3": {"size": "13px", "weight": "400", "ls": "0.5px"},
}
BRAND = "VERITAS INTELLIGENCE ANALYTICS"
SUBSYSTEMS = {
    "VIA Central Governance Console": "專注於中央治理、規則控管與跨系統版本化的統一指揮平台",
    "VeritasReportNova": "專注於知識資料庫化、結構化與報表級資料整備的平台",
    "VeritasDataForge": "AI 驅動的市場資料擷取、驗證與資料庫工程平台",
    "VIA Active Taiwan Stock ETF Analysis": "專注於台股主動式 ETF 的資料解析、規則治理與跨週期動態整合的平台",
    "VIA Taiwan Stock Revenue Analysis": "專注於台股上市櫃公司營收資料的解析、治理與跨系統整合的平台",
    "VIA Market Dynamics and Rotation": "專注於市場結構、資金輪動與跨週期動態解析的平台",
}


def tagline_for(subsystem: str | None) -> str:
    """六個子系統的定位句;不在名冊上就誠實留空,**不自己編一句**。"""
    if not subsystem:
        return ""
    return SUBSYSTEMS.get(subsystem, "")


def tokens_css() -> str:
    """:root 主題令牌 + 深色模式。畫面統一的根——顏色只有這裡一個出處。"""
    return f""":root{{
  --via-ink-header:{INK['header_bg']};
  --via-ink-page:{INK['page_bg']};
  --via-ink-row1:{INK['row1']};
  --via-ink-row2:{INK['row2']};
  --via-ink-row3:{INK['row3']};
  --via-rule:{INK['rule']};
  --via-fg:#E6EBF2;
  --via-muted:#8C99A6;
  --via-card:#14181C;
  --via-ok:#3FB984;
  --via-warn:#E0B341;
  --via-bad:#E06C60;
  --via-font:{FONT_STACK};
}}
@media (prefers-color-scheme: light){{
  :root:not([data-theme="dark"]){{
    --via-ink-page:#F6F8FA; --via-fg:#172033; --via-card:#FFFFFF; --via-rule:rgba(0,0,0,0.10);
  }}
}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
body{{background:var(--via-ink-page);color:var(--via-fg);font:14px/1.6 var(--via-font)}}
a{{color:#7FB2FF}}
.via-wrap{{padding:24px 40px}}
@media (max-width:640px){{.via-wrap{{padding:16px}}}}"""


def header_css() -> str:
    r = ROW_SPEC
    return f""".veritas-header{{
  background:var(--via-ink-header);
  padding:{INK['pad']};
  border-bottom:1px solid var(--via-rule);
  display:flex;align-items:center;justify-content:space-between;gap:24px;
}}
.veritas-header .vh-lines{{display:flex;flex-direction:column;gap:{INK['gap']}}}
.veritas-header .header-line-small{{
  font-size:{r['row1']['size']};font-weight:{r['row1']['weight']};
  letter-spacing:{r['row1']['ls']};color:var(--via-ink-row1);text-transform:uppercase;
}}
.veritas-header .header-line-large{{
  font-size:{r['row2']['size']};font-weight:{r['row2']['weight']};
  letter-spacing:{r['row2']['ls']};color:var(--via-ink-row2);
}}
.veritas-header .header-line-tag{{
  font-size:{r['row3']['size']};font-weight:{r['row3']['weight']};
  letter-spacing:{r['row3']['ls']};color:var(--via-ink-row3);
}}
.veritas-header .vh-lamp{{display:flex;gap:8px;align-items:center;font-size:12px;color:var(--via-muted)}}
.veritas-header .vh-dot{{width:8px;height:8px;border-radius:50%;background:var(--via-muted);display:inline-block}}
.vh-dot.ok{{background:var(--via-ok)}} .vh-dot.warn{{background:var(--via-warn)}} .vh-dot.bad{{background:var(--via-bad)}}
@media (max-width:640px){{
  .veritas-header{{padding:20px 16px;flex-direction:column;align-items:flex-start;gap:12px}}
  .veritas-header .header-line-large{{font-size:21px}}
}}"""


def veritas_header(system_title: str, tagline: str = "", lamp: str = "") -> str:
    """三行:小字母品牌 → 大字子系統 → 小字定位。右側預留狀態燈號位(操作員原文)。

    第三行缺定位句時**整行不出**(誠實留白,不塞佔位字)。
    """
    t = _html.escape(system_title)
    g = _html.escape(tagline) if tagline else ""
    row3 = f'\n      <div class="header-line-tag">{g}</div>' if g else ""
    lamp_html = lamp if lamp else '<span class="vh-dot"></span><span>—</span>'
    return f"""<header class="veritas-header">
    <div class="vh-lines">
      <div class="header-line-small">{BRAND}</div>
      <div class="header-line-large">{t}</div>{row3}
    </div>
    <div class="vh-lamp">{lamp_html}</div>
  </header>"""


def footer(note: str = "") -> str:
    """頁腳 VIA 標記:看得出這張頁跟其他張是同一個系統。"""
    n = f" · {_html.escape(note)}" if note else ""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (f'<footer class="via-foot" style="padding:18px 40px;border-top:1px solid var(--via-rule);'
            f'color:var(--via-muted);font-size:12px">'
            f'VIA · Veritas Intelligence Analytics · 頁頭件 SUP_MDL750 v{VERSION} · {ts}{n}</footer>')


def head(title: str, extra_css: str = "") -> str:
    """零 CDN 的 <head>:字體用系統堆疊,樣式全內嵌。"""
    css = tokens_css() + "\n" + header_css() + ("\n" + extra_css if extra_css else "")
    return f"""<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(title)}</title>
<style>
{css}
</style>
</head>"""


def page(title: str, body: str, *, subsystem: str | None = None,
         tagline: str | None = None, lamp: str = "", extra_css: str = "",
         foot_note: str = "", lang: str = "zh-Hant") -> str:
    """整頁組裝。body 由呼叫端給(本件不碰內容,只管頭尾與令牌)。"""
    tg = tagline if tagline is not None else tagline_for(subsystem)
    return f"""<!doctype html>
<html lang="{lang}">
{head(title, extra_css)}
<body>
  {veritas_header(subsystem or title, tg, lamp)}
  <main class="via-wrap">
{body}
  </main>
  {footer(foot_note)}
</body>
</html>
"""



# ── 批578:讓**既有的頁**接上表頭,而不是要求它們整頁重寫 ────────────────────
def header_tokens_css() -> str:
    r"""只給表頭用的令牌。**刻意不碰 body/html/\*** —— 既有頁有自己的版面,
    接表頭不該順便換掉它的底色與字體(那不是統一,那是覆蓋)。"""
    return (f":root{{--via-ink-header:{INK['header_bg']};--via-ink-page:{INK['page_bg']};"
            f"--via-ink-row1:{INK['row1']};--via-ink-row2:{INK['row2']};--via-ink-row3:{INK['row3']};"
            f"--via-rule:{INK['rule']};--via-muted:#8C99A6;--via-ok:#3FB984;"
            f"--via-warn:#E0B341;--via-bad:#E06C60;--via-font:{FONT_STACK};}}\n"
            "@media (prefers-color-scheme: light){:root:not([data-theme=\"dark\"]){--via-rule:rgba(0,0,0,0.10);}}\n")


_ADOPT_MARK = "<!-- [VIA:VERITAS-HEADER:v0100] SUP_MDL750 -->"


def adopt(page_html: str, system_title: str, tagline: str | None = None,
          *, lamp: str = "") -> str:
    """把 Veritas 正典表頭接到一張**既有的頁**上,並補齊 LAW 五條。

    設計上三件事一定要守住:
      ① **冪等**:已經接過(帶標記)就原樣回傳,再生一百次也只有一個表頭。
      ② **不覆蓋既有版面**:只注入表頭自己的 CSS 與令牌,不碰 body/html/*。
      ③ **只補不刪**:缺 lang / viewport / charset 才補,既有的一律不動。
    這樣一支產頁引擎只要在寫檔前多一行 `html = adopt(html, "…")` 就接上了。
    """
    import re as _re
    if _ADOPT_MARK in page_html or 'class="veritas-header"' in page_html:
        return page_html                                    # ① 冪等
    t = page_html
    m = _re.search(r"<html\b[^>]*>", t, _re.I)              # ③ lang
    if m and "lang=" not in m.group(0).lower():
        t = t[:m.start()] + '<html lang="zh-Hant">' + t[m.end():]
    low = t.lower()
    if 'name="viewport"' not in low and "name='viewport'" not in low:
        mm = _re.search(r"<meta[^>]*charset[^>]*>", t, _re.I)
        vp = '<meta name="viewport" content="width=device-width, initial-scale=1">'
        if mm:
            t = t[:mm.end()] + vp + t[mm.end():]
        else:
            t = _re.sub(r"<head[^>]*>", lambda x: x.group(0) + '<meta charset="utf-8">' + vp,
                        t, count=1, flags=_re.I)
    css = "<style>\n" + header_tokens_css() + header_css() + "\n</style>"   # ②
    if _re.search(r"</head>", t, _re.I):
        t = _re.sub(r"</head>", css + "</head>", t, count=1, flags=_re.I)
    else:
        t = css + t
    tg = tagline if tagline is not None else tagline_for(system_title)
    blk = _ADOPT_MARK + "\n" + veritas_header(system_title, tg, lamp) + "\n"
    if _re.search(r"<body[^>]*>", t, _re.I):
        t = _re.sub(r"(<body[^>]*>)", lambda x: x.group(1) + "\n" + blk, t, count=1, flags=_re.I)
    else:
        t = t + blk
    return t


# ── 自測:把畫面統一閘的尺搬過來對自己跑(契約耦合,兩邊不會各說各話)────────
def _gate_contract():
    """載 CGC_MDL160 尾版的 CONTRACT;缺席=誠實回 None(不假裝通過)。"""
    import importlib.util as ilu
    here = Path(__file__).resolve()
    via = here.parents[2]
    hits = sorted((via / "supportive modules" / "registry").glob("CGC_MDL160_UIUnifyGate_v*.py"))
    if not hits:
        return None, "ABSENT"
    sp = ilu.spec_from_file_location("_gate750", hits[-1])
    mod = ilu.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod.CONTRACT, hits[-1].name


def selftest() -> int:
    fails, n = [], [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    sample = page("VIA · 資料鍛造 VDF 現況台", "<p>樣頁</p>",
                  subsystem="VeritasDataForge", foot_note="selftest")

    contract, who = _gate_contract()
    chk("① 畫面統一閘的尺載得到(契約耦合;閘缺席=誠實 ABSENT,不自己發明一套尺)",
        contract is not None, f"({who})")
    if contract:
        bad = [f"{k}({lv})" for k, lv, _zh, fn in contract if not fn(sample)]
        chk("② 本件產出的樣頁通過閘的**全部 13 條**契約(LAW+UNIFY+ADVISORY+TARGET)",
            not bad, f"({len(contract)} 條 · 不過 {bad or '無'})")
        laws = [k for k, lv, _z, fn in contract if lv == "LAW" and not fn(sample)]
        chk("③ LAW 五條逐條:零 CDN · 零彈窗 · UTF-8 · viewport · lang", not laws, f"({laws or '全過'})")
        tgt = [k for k, lv, _z, fn in contract if lv == "TARGET" and not fn(sample)]
        chk("④ TARGET 四條(Veritas Header)也真的達成——不是只立契約不施工", not tgt, f"({tgt or '全過'})")

    chk("⑤ 零 CDN 是**結構性**的:本件一個 http(s) 外連字串都不產生(字體走系統堆疊)",
        "http://" not in sample and "https://" not in sample)
    chk("⑥ 六個子系統定位句與操作員原文一字不差,且**不在名冊上就留空不編**",
        len(SUBSYSTEMS) == 6 and tagline_for("VeritasDataForge").startswith("AI 驅動")
        and tagline_for("不存在的子系統") == "",
        f"({len(SUBSYSTEMS)} 條)")
    chk("⑦ 三行順序小→大→小,且第三行缺定位句時整行不出(誠實留白,不塞佔位字)",
        sample.index("header-line-small") < sample.index("header-line-large")
        and "header-line-tag" not in veritas_header("X", ""))
    esc = page("<b>x</b>&y", "<p>b</p>", subsystem=None, tagline="<i>t</i>")
    chk("⑧ 標題與定位句逐字跳脫(呼叫端給什麼都不會破版或注入)",
        "&lt;b&gt;" in esc and "&lt;i&gt;" in esc and "<b>x</b>" not in esc)
    chk("⑨ 顏色與尺寸只有一個出處(INK / ROW_SPEC),樣頁裡找得到水墨兩色與三個級距",
        all(v in sample for v in (INK["header_bg"], INK["page_bg"]))
        and all(ROW_SPEC[k]["size"] in sample for k in ROW_SPEC))
    chk("⑩ 純函式無副作用:本件不寫任何檔、不讀庫、不觸網(只在自測時 import 閘讀尺)",
        "write_text(" not in Path(__file__).read_text(encoding="utf-8").split("def selftest")[0])
    chk("⑪ 行動裝置:640px 斷點在(手機上不橫向捲)", "@media (max-width:640px)" in sample)
    # ── 批578:adopt() 三檢 ────────────────────────────────────────────────
    legacy = ('<!doctype html><html><head><meta charset="utf-8"><title>舊頁</title>'
              '<style>body{background:#fff;color:#111;font-family:Georgia,serif}</style>'
              '</head><body><h1>既有內容</h1></body></html>')
    got = adopt(legacy, "VeritasDataForge")
    chk("⑬ adopt 把表頭接到既有頁上,並補齊 lang / viewport(缺才補)",
        'lang="zh-Hant"' in got and 'name="viewport"' in got
        and "veritas-header" in got and "既有內容" in got)
    chk("⑭ adopt **冪等**:接過的頁再接一百次還是只有一個表頭",
        adopt(got, "VeritasDataForge") == got and got.count("veritas-header") == got.count("veritas-header"))
    chk("⑮ adopt **不覆蓋既有版面**:不注入 body/html/* 的規則(接表頭不等於換掉人家的底色)",
        "body{background:#fff" in got
        and "body{{" not in header_tokens_css() and "body{" not in header_tokens_css()
        and "html,body" not in header_tokens_css())
    if contract:
        _bad2 = [k for k, lv, _z, fn in contract if lv in ("LAW", "TARGET") and not fn(got)]
        chk("⑯ 接過表頭的舊頁,LAW 五條與 TARGET 四條都過(表頭一接上,四個 TARGET 一起達成)",
            not _bad2, f"(不過 {_bad2 or '無'})")

    chk("⑫ 帶加速器橋(MDL156 覆蓋閘)",
        "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0]-len(fails)} · FAIL {len(fails)}")
    return 0 if not fails else 1


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] in ("demo", "--demo"):
        print(page("VIA · 中央治理 CGC 現況台", "<p>demo</p>",
                   subsystem="VIA Central Governance Console"))
        return 0
    print(f"[SUP_MDL750 v{VERSION}] Veritas 正典頁頭件 · 用法:selftest | demo")
    print("  程式內用:from SUP_MDL750_VeritasUIHead_v0100 import page, veritas_header, SUBSYSTEMS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
