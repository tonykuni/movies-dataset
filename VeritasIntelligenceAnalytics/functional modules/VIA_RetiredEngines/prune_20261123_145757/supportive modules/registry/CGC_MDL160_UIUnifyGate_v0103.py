#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL160_UIUnifyGate v0103 — U/I 畫面統一閘(批576 尾版律分母;批577 零CDN/零彈窗收窄)

v0102→v0103(批577 兩條 LAW 的尺在真頁上生了 9 盞假紅,先修尺)
  拿 v0102 的 18 紅逐張看它到底紅在哪一個字,結果:
    · zero_cdn 10 張裡有 **8 張**紅在 `href="http://127.0.0.1:8765/master"`
      ——那是本機指揮台橋(DeckServer),**不是 CDN**。零 CDN 管的是外連第三方。
    · zero_popup 4 張裡有 **1 張**(VIA_UI_TreeAtlas)紅在 `<code>FNC009</code> confirm()`
      ——那是**函數名冊的說明文字**,不是彈窗。彈窗是行為,行為只在腳本裡。
  收窄後 **RED 18 → 9**,九張全是真的。並用合成頁雙向釘住(第⑳㉑檢):
  真的 googleapis / 真的 alert 仍然判紅,本機橋 / 文件裡的函數名不准判紅。
  本機橋外連**另計**(local_bridge_pages),不讓豁免變成消失(L68)。

v0101→v0102(批576 把尺自己先修乾淨,再去修頁)
  批574 我報給操作員的是「106 張 · RED 43」。**那個 106 是灌水的**:
  VIA_UI_ReportDigest.html 有 17 份(每個 digest 跑次夾一份)、VIA_UI_Hub 有 9 個版號、
  VapDeck 6 個、GovDeck 5 個——同一張頁被數了很多遍。套上我們自己的尾版律之後:
  **72 張 · GREEN 39 · YELLOW 15 · RED 18**。這正是我在批575 寫進 L68 的那條律,
  第一個被它抓到的就是我自己的閘。
  另外兩件:① owner 從「提到檔名就算」收窄成 write / title / mention / none 四級證據
  ——舊版會印「該由 A/B/C/D/E/F/G/H 再生」,八個候選等於沒有 owner;
  ② 無再生者的頁要講白「**這張頁自己就是正本**」,不要叫人去找一支不存在的引擎。
  並與批576 新立的正本頁頭件 SUP_MDL750 契約耦合(第⑰檢)。

v0100→v0101(批574 操作員貼進 Veritas Unified Header Design System 規格,要求納入):
  **先量再定級**(這支的老規矩):74 張活頁裡 —— `veritas-header` 結構 **0/74**、
  三行層級 **0/74**、水墨配色令牌 **0/74**、只有品牌行 20/74。
  這是一個**還沒人蓋的新標準**。判 LAW 會當場 74 紅,判 UNIFY 會 74 黃,兩種都是假陽性機器
  ——而且會把真正的紅(43 張破零 CDN)淹掉。
  所以加**第四級 TARGET**:已立契約、尚未施工。**永不判燈,只報覆蓋率**,讓進度看得見。
  施工由頁的 owner 引擎照 `header` 動詞印出的正典規格再生,本閘一如既往**不代改頁**。

操作員令(批570 續):「VIA 作為資料庫與應用介面 HTML U/I 對接;也準備 VIA VRN 的 U/I,
**設計還在進行但畫面統一**」。

【先量再定契約(不發明沒人達得到的標準)】
  本境 65 張 `VIA_UI_*.html` 實測:
    <title> 65/65 · charset 64/65 · viewport 64/65 · lang=zh 64/65 · 零彈窗 62/65
    CSS 變數 :root 61/65 · **零 CDN 56/65** · VIA 頁腳 41/65 · 深色模式 7/65
  所以契約**分三級**,不是一視同仁(一視同仁就是假陽性機器):
    **律級 (LAW)**      已經是既有律(零 CDN / 零彈窗 / charset / viewport / lang)——違反=RED
    **統一級 (UNIFY)**  操作員這一令要的「畫面統一」(主題令牌 :root / VIA 頁腳 / <title>)——缺=YELLOW
    **建議級 (ADVISORY)** 只有 7/65 達標的(深色模式)——**永遠不判紅**,只列出來當路線圖

【不代改頁】
  這些頁都是**引擎產的**。手改頁下一次再生就被蓋掉,而且會讓頁與產它的引擎對不上。
  所以本閘只做兩件:判定 + **指名該由哪一支引擎再生**。沒有 --apply,不寫任何一張頁。

用法:
  via-uiunify scan              逐頁三級判定
  via-uiunify plan              只列不合的,並指名 owner 引擎與該補什麼
  via-uiunify contract          印出契約本身(三級逐條)
  via-uiunify --selftest
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
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "uiunify"
UI_DIRS = ["supportive modules/ui_support", "VIA_Reports"]
OWNER_SCAN = ["supportive modules/registry", "supportive modules/VIA_Governance_Runtime",
              "supportive modules/ui_support", "functional modules/VDF/engine",
              "functional modules/VRN", "functional modules/VAP/engine"]   # 批577:+治理執行期與 ui_support
                                                                          #   (Hub 系列的 owner 住在那裡,舊版掃不到)

_CDN = re.compile(r'(?:src|href)\s*=\s*["\']\s*https?://[^"\']*', re.I)
_POP = re.compile(r'\b(?:alert|confirm|prompt)\s*\(')

# ── 批577:兩條 LAW 的尺收窄(舊尺在真頁上生了 9 盞假紅)──────────────────────
#: 回送位址=本機指揮台橋(DeckServer 8765),不是第三方 CDN。零 CDN 管的是**外連第三方**。
#: 具名豁免,而且**另計**(local_bridge),不讓它消失在報告裡(L68)。
_LOOPBACK = re.compile(r'https?://(?:127\.0\.0\.1|localhost|\[::1\]|0\.0\.0\.0)(?::\d+)?', re.I)
_SCRIPTS = re.compile(r'<script[^>]*>([\s\S]*?)</script>', re.I)
_HANDLERS = re.compile(r'\son[a-z]+\s*=\s*"([^"]*)"|\son[a-z]+\s*=\s*\'([^\']*)\'', re.I)


def external_links(t: str) -> list:
    """頁上的**第三方**外連(扣掉回送位址)。"""
    return [m.group(0) for m in _CDN.finditer(t) if not _LOOPBACK.search(m.group(0))]


def local_links(t: str) -> list:
    """回送位址外連:本機橋,具名豁免但要看得見。"""
    return [m.group(0) for m in _CDN.finditer(t) if _LOOPBACK.search(m.group(0))]


def script_text(t: str) -> str:
    """只取**腳本脈絡**:<script> 內文 + on* 行內處理器。

    舊尺是對整頁做字串比對,結果 `<code>confirm()</code>` 這種**文件說明文字**
    被判成彈窗(VIA_UI_TreeAtlas 就是這樣紅的,它列的是函數名冊)。
    彈窗是行為,行為只可能發生在腳本裡。
    """
    parts = [m.group(1) for m in _SCRIPTS.finditer(t)]
    for m in _HANDLERS.finditer(t):
        parts.append(m.group(1) or m.group(2) or "")
    return "\n".join(parts)
_re3 = re.compile(r'header-line-small[\s\S]{0,400}header-line-large')

# (鍵, 級別, 中文, 判定)
CONTRACT = [
    ("zero_cdn",  "LAW",      "零 CDN(不得外連**第三方**;回送位址=本機橋,具名豁免另計)",
     lambda t: not external_links(t)),
    ("zero_popup", "LAW",     "零彈窗(**腳本脈絡**裡不得 alert/confirm/prompt;文件裡寫函數名不算)",
     lambda t: not _POP.search(script_text(t))),
    ("charset",   "LAW",      "宣告 UTF-8",                                lambda t: "charset=utf-8" in t.lower().replace('"', "").replace("'", "")),
    ("viewport",  "LAW",      "行動裝置 viewport",                          lambda t: 'name="viewport"' in t.lower() or "name='viewport'" in t.lower()),
    ("lang",      "LAW",      "lang=\"zh…\"",                              lambda t: 'lang="zh' in t.lower() or "lang='zh" in t.lower()),
    ("title",     "UNIFY",    "有 <title>(分頁看得出是哪一張)",            lambda t: "<title>" in t.lower()),
    ("theme_root", "UNIFY",   "CSS 變數 :root 主題令牌(畫面統一的根)",      lambda t: ":root{" in t.replace(" ", "") or ":root {" in t),
    ("via_mark",  "UNIFY",    "頁腳帶 VIA 標記(看得出是同一個系統)",        lambda t: "VIA" in t[-4000:]),
    ("dark",      "ADVISORY", "深色模式(prefers-color-scheme)——路線圖,不判紅", lambda t: "prefers-color-scheme" in t),
    # ── 批574 Veritas Unified Header Design System(第四級 TARGET:已立契約、尚未施工)──
    #   本境實測 0/74,所以**永不判燈**,只計覆蓋率。判紅或判黃都會把真正的紅淹掉。
    ("vh_struct", "TARGET", "Veritas Header 結構(class=veritas-header)",
     lambda t: "veritas-header" in t),
    ("vh_brand",  "TARGET", "Row1 母品牌行 VERITAS INTELLIGENCE ANALYTICS",
     lambda t: "VERITAS INTELLIGENCE ANALYTICS" in t.upper()),
    ("vh_three",  "TARGET", "三行層級 小/大/小(header-line-small → large → small)",
     lambda t: bool(_re3.search(t))),
    ("vh_ink",    "TARGET", "水墨配色令牌(#121417 頭 / #090A0B 底)",
     lambda t: "#121417" in t or "#090A0B" in t.upper()),
]
LEVEL_FAIL = {"LAW": "RED", "UNIFY": "YELLOW", "ADVISORY": "ADVISORY", "TARGET": "TARGET"}

# Veritas Unified Header 正典規格(操作員批574 原文;頁的 owner 引擎照這個再生)
VERITAS_HEADER_SPEC = {
    "rows": [
        {"row": 1, "kind": "小字 · 母品牌", "text": "VERITAS INTELLIGENCE ANALYTICS",
         "size": "13px", "weight": 400, "color": "#8C99A6", "letter_spacing": "1.2px",
         "transform": "uppercase"},
        {"row": 2, "kind": "大字 · 子系統名稱", "text": "{{ SYSTEM_TITLE }}",
         "size": "26px", "weight": 600, "color": "#F0F4F8", "letter_spacing": "0.3px"},
        {"row": 3, "kind": "小字 · 子系統定位", "text": "{{ SYSTEM_TAGLINE }}",
         "size": "13px", "weight": 400, "color": "#737D87", "letter_spacing": "0.5px"},
    ],
    "box": {"header_bg": "#121417", "page_bg": "#090A0B", "padding": "32px 40px",
            "row_gap": "8px", "border_bottom": "1px solid rgba(255,255,255,0.08)"},
    "font": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    "subsystems": {
        "VIA Central Governance Console": "專注於中央治理、規則控管與跨系統版本化的統一指揮平台",
        "VeritasReportNova": "專注於知識資料庫化、結構化與報表級資料整備的平台",
        "VeritasDataForge": "AI 驅動的市場資料擷取、驗證與資料庫工程平台",
        "VIA Active Taiwan Stock ETF Analysis": "專注於台股主動式 ETF 的資料解析、規則治理與跨週期動態整合的平台",
        "VIA Taiwan Stock Revenue Analysis": "專注於台股上市櫃公司營收資料的解析、治理與跨系統整合的平台",
        "VIA Market Dynamics and Rotation": "專注於市場結構、資金輪動與跨週期動態解析的平台",
    },
    "policy": "零 CDN · 零彈窗 · 右側預留狀態燈號位;本閘不代改頁,施工由頁的 owner 引擎再生",
}


def pages_all() -> list:
    """全掃(不套尾版律)。留著是為了讓分母的變動看得見(L68)。"""
    out = []
    for rel in UI_DIRS:
        d = VIA / rel
        if not d.exists():
            continue
        for p in sorted(d.rglob("VIA_UI_*.html")):
            s = str(p).replace("\\", "/")
            if any(k in s for k in ("references/intake", "VIA_RetiredEngines", "SCOPE_COPY")):
                continue
            out.append(p)
    return out


def _family(p: Path) -> str:
    """去版號分家族:VIA_UI_Hub_v0108.html → VIA_UI_Hub.html"""
    return re.sub(r"_v\d{4}\.html$", ".html", p.name)


def folded() -> dict:
    """批576:被尾版律折疊掉的份數,逐家族攤開(L68 分母要看得見)。"""
    fam: dict[str, list] = {}
    for p in pages_all():
        fam.setdefault(_family(p), []).append(p)
    return {k: len(v) for k, v in fam.items() if len(v) > 1}


def pages() -> list:
    """**尾版律**分母(批576):同一個頁家族只問最後一支;同名多份(歷史跑次夾)只問最新那一份。

    批575 以前這裡是全掃,量出「106 張 · RED 43」——但那 106 裡面
    VIA_UI_ReportDigest.html 有 17 份(每個 digest 跑次夾一份)、VIA_UI_Hub 有 9 個版號、
    VapDeck 6 個、GovDeck 5 個。**同一張頁被數了很多次,真正該修的張數被灌水**。
    這正是我自己在批575 寫進 L68 的那條律:尺不得比律窄,也不得比律寬到把同一件事數很多遍。
    """
    fam: dict[str, list] = {}
    for p in pages_all():
        fam.setdefault(_family(p), []).append(p)
    # 版號大的優先;同名時路徑字典序最後(跑次夾帶時戳,最後=最新)
    return [sorted(v, key=lambda x: (x.name, str(x)))[-1] for v in fam.values()]


_WRITE = re.compile(r'(write_text|\.write\(|open\([^)]*["\']w)')


def _owner_sources() -> list:
    out = []
    for rel in OWNER_SCAN:
        d = VIA / rel
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            s = str(p).replace("\\", "/")
            if any(k in s for k in ("references/intake", "VIA_RetiredEngines", "__pycache__")):
                continue
            try:
                out.append((p, p.read_text(encoding="utf-8", errors="ignore")))
            except Exception:
                continue
    return out


def owners(ps: list | None = None) -> dict:
    """頁名 → {engines, kind}。批576:**分辨證據強度**,不再把「提到檔名」當 owner。

      write   引擎裡出現這個檔名,而且鄰近 400 字內有寫檔動作 → 它真的產這張頁
      title   引擎裡出現這張頁的 <title> 原文 → 它幾乎一定是模板出處(檔名常是動態組的)
      mention 只提到檔名(可能只是連結它)→ 弱證據,列出來但講明是弱的
      none    **無再生者:這張頁自己就是正本**,要改就是直接改它

    舊版把三種混成一團,結果 plan 會印出「該由 A/B/C/D/E/F/G/H 再生」——
    八個候選等於沒有 owner(L30 一功能一主:要指得出**那一支**)。
    """
    srcs = _owner_sources()
    ps = ps if ps is not None else pages()
    out = {}
    for p in ps:
        fn = p.name
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            txt = ""
        ti = re.search(r"<title>(.*?)</title>", txt, re.S)
        title = ti.group(1).strip() if ti else ""
        w, ttl, mention = [], [], []
        for q, s in srcs:
            stem = q.stem.rsplit("_v", 1)[0]
            if stem.startswith("CGC_MDL160_UIUnifyGate"):
                continue                      # 批577:閘自己的說明文字提到頁名 ≠ 它產那張頁
            if fn in s:
                near = any(_WRITE.search(s[max(0, m.start() - 400):m.end() + 400])
                           for m in re.finditer(re.escape(fn), s))
                (w if near else mention).append(stem)
            if title and len(title) >= 6 and title in s:
                ttl.append(stem)
        if w:
            out[fn] = {"engines": sorted(set(w)), "kind": "write"}
        elif ttl:
            out[fn] = {"engines": sorted(set(ttl)), "kind": "title"}
        elif mention:
            out[fn] = {"engines": sorted(set(mention)), "kind": "mention"}
        else:
            out[fn] = {"engines": [], "kind": "none"}
    return out


def scan() -> dict:
    ps = pages()
    if not ps:
        return {"state": "ABSENT", "why": f"找不到 VIA_UI_*.html(掃了 {UI_DIRS})"}
    own = owners(ps)
    n_all = len(pages_all())
    rows, tally = [], {"GREEN": 0, "RED": 0, "YELLOW": 0, "ADVISORY": 0}
    for p in ps:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            rows.append({"page": p.name, "state": "RED", "why": f"{type(exc).__name__}: {exc}"})
            tally["RED"] += 1
            continue
        bad = []
        for key, lvl, zh, test in CONTRACT:
            if not test(t):
                bad.append({"item": key, "level": lvl, "zh": zh})
        red = [b for b in bad if b["level"] == "LAW"]
        yel = [b for b in bad if b["level"] == "UNIFY"]
        tgt = [b for b in bad if b["level"] == "TARGET"]     # 批574:**永不判燈**,只計覆蓋
        st = "RED" if red else ("YELLOW" if yel else "GREEN")
        tally[st] += 1
        if any(b["level"] == "ADVISORY" for b in bad):
            tally["ADVISORY"] += 1
        o = own.get(p.name, {"engines": [], "kind": "none"})
        rows.append({"page": p.name, "rel": str(p.relative_to(VIA)), "state": st,
                     "miss": bad, "owner": o["engines"], "owner_kind": o["kind"]})
    n_local = sum(1 for p in ps for _l in [local_links(p.read_text(encoding="utf-8", errors="ignore"))] if _l)
    return {"state": "OK", "n": len(rows), "n_all": n_all, "folded": folded(),
            "local_bridge_pages": n_local, "tally": tally, "rows": rows,
            "contract_levels": {k: sum(1 for c in CONTRACT if c[1] == k)
                                for k in ("LAW", "UNIFY", "ADVISORY", "TARGET")},
            "target_coverage": {key: sum(1 for r in rows
                                         if not any(m["item"] == key for m in r.get("miss", [])))
                                for key, lvl, _z, _t in CONTRACT if lvl == "TARGET"},
            "note": (f"分母(L68):全掃 {n_all} 張 → **尾版律後 {len(rows)} 張**"
                     f"(折疊 {len(folded())} 個家族;同一張頁不再被數很多遍)。"
                     f"本機橋外連 {n_local} 張(回送位址,具名豁免不判紅但另計;批577)。"
                     "ADVISORY 與 TARGET **永遠不判燈**;TARGET=已立契約,施工進度看 target_coverage")}


def _owner_clean(row: dict) -> bool:
    """批577:這張頁紅的那一條,在 owner 的**尾版原始碼**裡還在不在。

    不在=頁只是比引擎舊(下次再生就綠),在=引擎本身還沒修。
    這兩件事對操作員是完全不同的下一步,不該混在同一個「RED」裡。
    """
    laws = {m["item"] for m in row.get("miss", []) if m["level"] == "LAW"}
    if not laws or not row.get("owner"):
        return False
    tails = {}
    for q, s in _owner_sources():
        stem = q.stem.rsplit("_v", 1)[0]
        if stem in row["owner"]:
            prev = tails.get(stem)
            if prev is None or q.name > prev[0]:
                tails[stem] = (q.name, s)
    if not tails:
        return False
    for _stem, (_n, s) in tails.items():
        if "zero_cdn" in laws and external_links(s):
            return False
        if "zero_popup" in laws and _POP.search(script_text(s)):
            return False
        if "viewport" in laws and 'name="viewport"' not in s and "name='viewport'" not in s:
            return False
        if "lang" in laws and 'lang="zh' not in s and "lang='zh" not in s:
            return False
    return True


def plan() -> dict:
    sc = scan()
    if sc["state"] != "OK":
        return sc
    todo = [r for r in sc["rows"] if r["state"] in ("RED", "YELLOW")]
    KIND_ZH = {"write": "該由(真的寫這張頁的)", "title": "該由(模板出處,依 <title> 認的)",
               "mention": "只找到「提到檔名」的弱證據,可能不是它:"}
    for r in todo:
        k = r.get("owner_kind", "none")
        if k == "none" or not r["owner"]:
            r["fix"] = "**無再生者:這張頁自己就是正本**,要改就是直接改它(不是叫引擎再生)"
        else:
            r["fix"] = KIND_ZH[k] + " " + " / ".join(r["owner"][:4]) + \
                (f" 等 {len(r['owner'])} 支" if len(r["owner"]) > 4 else "") + " 再生"
            # 批577:owner 的**尾版原始碼**已經不含這條違規 → 頁只是比引擎舊
            if r["state"] == "RED" and _owner_clean(r):
                r["fix_ready"] = True
                r["fix"] += "  ★ **owner 尾版已修好(批577):跑一次再生這張就會綠**"
    return {"state": "OK" if not any(r["state"] == "RED" for r in todo) else "FAIL",
            "n_total": sc["n"], "n_todo": len(todo),
            "n_red": sum(1 for r in todo if r["state"] == "RED"),
            "n_yellow": sum(1 for r in todo if r["state"] == "YELLOW"),
            "todo": todo,
            "note": "本閘不改頁:頁是引擎產的,手改下一次再生就被蓋掉,而且會讓頁與引擎對不上"}


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL160 U/I 畫面統一閘 v{VERSION} · 自測(零網路;不改任何一張頁) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路、零寫頁(不 import requests/httpx/urllib;無 write_text 寫 .html)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib"))
        and ".html\").write_text" not in code and "p.write_text(h" not in code)
    chk("② 沒有 --apply(頁是引擎產的,不代改)", '"--apply"' not in code and "'--apply'" not in code)
    # 批574:契約從三級變四級(+TARGET)。這一檢是**自己的尺**,加級就要跟著改——
    #   我第一版沒改它,自測當場紅。這正是它該有的行為:尺釘死級別,加級必須被看見。
    chk("③ 契約分四級(LAW/UNIFY/ADVISORY/TARGET),且 ADVISORY 與 TARGET 永不判燈",
        {c[1] for c in CONTRACT} == {"LAW", "UNIFY", "ADVISORY", "TARGET"}
        and LEVEL_FAIL["ADVISORY"] == "ADVISORY" and LEVEL_FAIL["TARGET"] == "TARGET")

    # 合成三張頁:全合 / 破律 / 只缺統一級
    with tempfile.TemporaryDirectory() as td:
        g = globals()
        d = Path(td) / "supportive modules" / "ui_support"
        d.mkdir(parents=True)
        good = ('<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width"><title>好頁</title>'
                '<style>:root{--fg:#111}@media (prefers-color-scheme:dark){:root{--fg:#eee}}</style>'
                '<body>內容</body><footer>VIA</footer></html>')
        (d / "VIA_UI_Good_v0100.html").write_text(good, encoding="utf-8")
        (d / "VIA_UI_Cdn_v0100.html").write_text(
            good.replace("<body>", '<script src="https://cdn.example.com/x.js"></script><body>'), encoding="utf-8")
        (d / "VIA_UI_Plain_v0100.html").write_text(
            '<!doctype html><html lang="zh-Hant"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width"><body>只有內容</body></html>', encoding="utf-8")
        old_via, old_dirs, old_own = g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"]
        g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"] = Path(td), ["supportive modules/ui_support"], []
        try:
            sc = scan()
            by = {r["page"]: r for r in sc["rows"]}
            chk("④ 全合的頁=GREEN", by["VIA_UI_Good_v0100.html"]["state"] == "GREEN")
            chk("⑤ 外連 CDN=**RED**(律級;零 CDN 是既有律)",
                by["VIA_UI_Cdn_v0100.html"]["state"] == "RED"
                and any(m["item"] == "zero_cdn" for m in by["VIA_UI_Cdn_v0100.html"]["miss"]))
            chk("⑥ 只缺主題令牌/頁腳/標題=**YELLOW**,不冒充 RED(畫面統一是新令,不是舊律)",
                by["VIA_UI_Plain_v0100.html"]["state"] == "YELLOW"
                and not any(m["level"] == "LAW" for m in by["VIA_UI_Plain_v0100.html"]["miss"]),
                str([m["item"] for m in by["VIA_UI_Plain_v0100.html"]["miss"]]))
            chk("⑦ 缺深色模式不影響燈號(ADVISORY 只列不判)",
                any(m["item"] == "dark" for m in by["VIA_UI_Plain_v0100.html"]["miss"])
                and by["VIA_UI_Plain_v0100.html"]["state"] != "RED")
            pl = plan()
            chk("⑧ plan 只列不合的,並對每一張講得出下一步",
                pl["n_total"] == 3 and pl["n_todo"] == 2 and all("fix" in r for r in pl["todo"]))
            # 批576:尺跟著行為一起改——舊版判「找不到就寫『不猜』請操作員指認」,
            # 新版分得出四級證據,無再生者要講白「**這張頁自己就是正本**」(那才是下一步)。
            chk("⑨ 找不到再生者的頁,fix 要講白「這張頁自己就是正本」——那是可執行的下一步,"
                "不是把球丟回給操作員",
                all("這張頁自己就是正本" in r["fix"] for r in pl["todo"])
                and all(r.get("owner_kind") == "none" for r in pl["todo"]))
        finally:
            g["VIA"], g["UI_DIRS"], g["OWNER_SCAN"] = old_via, old_dirs, old_own

    real = scan()
    chk("⑩ 掃得到本庫的真實頁(≥40 張)", real["state"] == "OK" and real["n"] >= 40,
        f"{real.get('n')} 張 · GREEN {real['tally']['GREEN']} · YELLOW {real['tally']['YELLOW']} · RED {real['tally']['RED']}")
    chk("⑪ owner 對照查得到(頁要再生時找得到人)",
        sum(1 for r in real["rows"] if r["owner"]) >= 20,
        f"查得到 owner {sum(1 for r in real['rows'] if r['owner'])} 張")
    chk("⑫ TARGET 級**永不判燈**(Veritas Header 本境 0/74;判紅或判黃都會把真正的紅淹掉)",
        LEVEL_FAIL["TARGET"] == "TARGET"
        and all(x["state"] != "RED" for x in real["rows"]
                if all(m["level"] == "TARGET" for m in x.get("miss", []))),
        f"TARGET 項 {sum(1 for c in CONTRACT if c[1] == 'TARGET')} 個")
    chk("⑬ Veritas Header 正典規格三行齊、六個子系統定位齊(操作員批574 原文)",
        len(VERITAS_HEADER_SPEC["rows"]) == 3 and len(VERITAS_HEADER_SPEC["subsystems"]) == 6
        and VERITAS_HEADER_SPEC["rows"][0]["text"] == "VERITAS INTELLIGENCE ANALYTICS")
    chk("⑭ plan 不把 TARGET 列成待修(它不是債,是路線圖)",
        all(all(m["level"] not in ("ADVISORY", "TARGET") for m in x["miss"]) or x["state"] != "GREEN"
            for x in plan()["todo"]))
    # ── 批576 ────────────────────────────────────────────────────────────────
    sc2 = scan()
    fold = sc2.get("folded", {})
    chk("⑯ 分母看得見(L68):全掃 → 尾版律後的張數,而且被折疊的家族逐個講得出來",
        sc2["n"] <= sc2.get("n_all", sc2["n"]) and isinstance(fold, dict)
        and all(v > 1 for v in fold.values()),
        f"(全掃 {sc2.get('n_all')} → 尾版 {sc2['n']} · 折疊 {len(fold)} 家族:"
        + ", ".join(f"{k}×{v}" for k, v in sorted(fold.items(), key=lambda x: -x[1])[:4]) + ")")

    _head_mod, _head_why = None, "ABSENT"
    try:
        import importlib.util as _ilu576
        _hits = sorted((VIA / "supportive modules" / "ui_support")
                       .glob("SUP_MDL750_VeritasUIHead_v*.py"))
        if _hits:
            _sp = _ilu576.spec_from_file_location("_head576", _hits[-1])
            _head_mod = _ilu576.module_from_spec(_sp)
            _sp.loader.exec_module(_head_mod)
            _head_why = _hits[-1].name
    except Exception as exc:                                  # pragma: no cover
        _head_why = f"{type(exc).__name__}: {exc}"
    _bad_head = ([k for k, _lv, _z, fn in CONTRACT
                  if not fn(_head_mod.page("樣頁", "<p>x</p>", subsystem="VeritasDataForge"))]
                 if _head_mod else ["ABSENT"])
    chk("⑰ 正本頁頭件在位,而且它的產出通過本閘**全部 13 條**契約(契約耦合:"
        "頁頭件與閘互相釘住,誰漂移誰當場紅)",
        _head_mod is not None and not _bad_head,
        f"({_head_why} · 不過 {_bad_head or '無'})")

    chk("⑱ owner 分得出證據強度(write / title / mention / none),"
        "**不再把「提到檔名」當成 owner**(L30 一功能一主)",
        all(r.get("owner_kind") in ("write", "title", "mention", "none") for r in sc2["rows"])
        and any(r.get("owner_kind") == "none" for r in sc2["rows"]),
        "(kind: " + ", ".join(f"{k}={sum(1 for r in sc2['rows'] if r.get('owner_kind') == k)}"
                              for k in ("write", "title", "mention", "none")) + ")")

    chk("⑲ 無再生者的頁,plan 要講白「這張頁自己就是正本」——不叫人去找一支不存在的引擎",
        all("這張頁自己就是正本" in r["fix"]
            for r in plan().get("todo", []) if r.get("owner_kind") == "none"))

    # ── 批577:兩條 LAW 的尺收窄,雙向釘住(真違規要紅、假違規不准紅)──────────
    _cdn_law = next(fn for k, _l, _z, fn in CONTRACT if k == "zero_cdn")
    _pop_law = next(fn for k, _l, _z, fn in CONTRACT if k == "zero_popup")
    _bridge = '<a href="http://127.0.0.1:8765/master">橋</a>'
    _third = '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet">'
    chk("⑳ 零 CDN 管的是**第三方**:回送位址(127.0.0.1/localhost/::1)是本機指揮台橋,"
        "具名豁免不判紅但另計;真的外連第三方仍然判紅",
        _cdn_law(_bridge) and not _cdn_law(_third)
        and len(local_links(_bridge)) == 1 and len(external_links(_bridge)) == 0,
        f"(本機橋頁 {scan().get('local_bridge_pages')} 張;舊尺會把它們全判紅)")
    _doc = "<p>函數名冊:<code>FNC009</code> confirm()</p>"
    _real = '<script>function f(){ alert("x"); }</script>'
    _inline = '<button onclick="confirm(\'x\')">b</button>'
    chk("㉑ 零彈窗只在**腳本脈絡**判(<script> 與 on* 屬性):文件裡寫 <code>confirm()</code> "
        "不是彈窗;真的在腳本裡叫 alert/confirm 仍然判紅",
        _pop_law(_doc) and not _pop_law(_real) and not _pop_law(_inline))

    _pl = plan()
    _reds = [r for r in _pl.get("todo", []) if r["state"] == "RED"]
    chk("㉒ 紅頁要分得出「**引擎還沒修**」和「**頁比引擎舊**」:owner 尾版原始碼已不含該違規時,"
        "plan 標 fix_ready 並講「跑一次再生就會綠」——兩者的下一步完全不同",
        all(("fix_ready" in r) == ("★" in r["fix"]) for r in _reds),
        f"(RED {len(_reds)} · 其中頁比引擎舊 {sum(1 for r in _reds if r.get('fix_ready'))})")

    chk("⑮ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL160_UIUnifyGate", description="U/I 畫面統一閘(零網路;不改頁)")
    ap.add_argument("verb", nargs="?", default="scan", choices=["scan", "plan", "contract", "header"])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "header":
        print(f"[CGC_MDL160 v{VERSION}] Veritas Unified Header 正典規格(操作員批574 原文)")
        for r in VERITAS_HEADER_SPEC["rows"]:
            print(f"  Row{r['row']} {r['kind']:<16} {r['size']:<6} w{r['weight']} {r['color']:<9}"
                  f" ls {r['letter_spacing']:<6} {r['text']}")
        b = VERITAS_HEADER_SPEC["box"]
        print(f"  盒  頭底 {b['header_bg']} · 頁底 {b['page_bg']} · padding {b['padding']} · 行距 {b['row_gap']}")
        print(f"  子系統定位({len(VERITAS_HEADER_SPEC['subsystems'])} 個):")
        for k, v in VERITAS_HEADER_SPEC["subsystems"].items():
            print(f"    {k:<42} {v}")
        print(f"  註:{VERITAS_HEADER_SPEC['policy']}")
        return 0
    if a.verb == "contract":
        print(f"[CGC_MDL160 v{VERSION}] 畫面統一契約(三級)")
        for key, lvl, zh, _t in CONTRACT:
            print(f"  [{lvl:<8}] {key:<12} {zh}")
        print("  註:LAW 違反=RED · UNIFY 缺=YELLOW · ADVISORY/TARGET **永遠不判燈**")
        print("      TARGET=已立契約尚未施工(Veritas Header 本境 0/74);規格看 `via-uiunify header`")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    r = scan() if a.verb == "scan" else plan()
    write_out(f"UIUNIFY_{a.verb.upper()}_{ts}.json", r)
    write_out(f"UIUNIFY_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    elif a.verb == "scan":
        t = r["tally"]
        print(f"[CGC_MDL160 v{VERSION}] scan · {r['state']} · {r['n']} 張頁")
        print(f"  GREEN {t['GREEN']} · YELLOW {t['YELLOW']} · **RED {t['RED']}** "
              f"(另有 {t['ADVISORY']} 張缺 ADVISORY 項目,不判紅)")
        tc = r.get("target_coverage", {})
        if tc:
            print(f"  [TARGET · 已立契約尚未施工;不判燈] Veritas Header 覆蓋:"
                  + " · ".join(f"{k} {v}/{r['n']}" for k, v in tc.items()))
    else:
        print(f"[CGC_MDL160 v{VERSION}] plan · {r['state']} · 共 {r['n_total']} 張 · "
              f"待修 {r['n_todo']}(RED {r['n_red']} · YELLOW {r['n_yellow']})")
        for x in r["todo"][:40]:
            miss = " · ".join(f"{m['item']}({m['level']})" for m in x["miss"]
                          if m["level"] not in ("ADVISORY", "TARGET"))
            print(f"  [{x['state']:<6}] {x['page']:<44} 缺 {miss}")
            print(f"           → {x['fix']}")
        print(f"  註:{r['note']}")
    return {"OK": 0, "NODATA": 2, "ABSENT": 3}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
