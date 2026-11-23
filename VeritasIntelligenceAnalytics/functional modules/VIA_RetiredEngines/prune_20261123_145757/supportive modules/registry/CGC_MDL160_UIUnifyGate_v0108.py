#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL160_UIUnifyGate v0106 — U/I 畫面統一閘(批648 +「面」的分類與退路檢)

v0105→v0106(批648 **我上一批的題目問錯了,先更正**)
  批647 我在收尾寫「ui_support 那 30 份靠 hub 的頁,要不要收成資料內嵌、file:// 直開」。
  這一批真的去量,**沒有一份在抓自己的 `.json`**。它們抓的是
  `/run?task=` · `/intake` · `/auto` · `/upload` · `/ping` · `/status` · `/stock_fetch`
  ——全是 `127.0.0.1:8765` 的 hub 端點。

      致動器(會打 /run·/intake·/auto·/upload)   **14 份**  ← 天生需要 server
      唯讀狀態(只打 /ping·/status·/probe)         10 份
      有 hub 字樣但無端點                          10 份
      真外部 CDN(非 127.0.0.1)                   **1 筆**  ← VIA_UI_Hub_v0108 的 Google Fonts

  **一個會打 `/run?task=` 的頁是致動器,不是視圖。**把它「收成靜態檔」這件事沒有意義:
  靜態檔跑不了任務。我上一批把控制面錯當成報表面,所以問了一個不成立的問題。

  真正缺的是**分類本身**:沒有它,以後有人會拿 file:// 去要求一個致動器,
  或反過來出貨一個「報表」而它其實需要 hub。v0106 把它寫進契約,並加兩道檢:
    ① **視圖面不得打 hub 端點**(L100 的邊界:入口/視圖面必須 file:// 直開)
    ② **有 fetch 的頁,每一個 fetch 都要有退路**——hub 不在時要說得出「hub 不在」,不是白屏。
       量到 28 份有 fetch,**27 份每個 fetch 都護著,1 份不足**:
       `VIA_UI_CommandDeck_v0100.html` 7 個 fetch 裡 5 個沒有 `.catch`,
       **包含它的第一個 `fetch("/ping")`**(hub 探活)——hub 不在時它靜靜地不渲染。
  **本閘不改頁**(v0102 起的紀律):只點名、只指 owner。零 CDN 那一筆既有的 LAW 已經在報紅,
  不需要新尺;本批不重複造第二把。

CGC_MDL160_UIUnifyGate v0105 — U/I 畫面統一閘(批647 +正典 TEMPLATE 車道)

v0104→v0105(批647 操作員裁定「VIA_HTML_UI 進 VIA,為可調整統一銜接系統的 TEMPLATE」)
  量到的起點:`VIA_HTML_UI` 226 件**只在 main**,本分支 0 件;Register 冊上**零引用**
  ——沒有短令、沒有梭、沒有格子站。它是一整包做好的東西,**站在系統外面**。
  而它三支正典入口頁 `ui/VIA-Complete-System.html`、`ui/VIA-UI-Standalone-NoServer.html`、
  `ui/VIA-SYNCHRONIZER-Standalone.html` 量下去:**零 `fetch(`、零 XHR、零外部 src**,
  狀態走 `localStorage` —— **file:// 直開就會動**,它自己的 STANDARD.md 也明寫
  「The package must remain usable from `file://` without network access」。

  對照樹內另一套:`supportive modules/ui_support/VIA_UI_*.html` 68 份裡 **30 份要靠 hub**
  (`fetch(` / 外部 src)。**兩套 U/I 並存**,而只有其中一套能離線開。

  v0105 做的事:把那份 STANDARD 的 Offline contract **從散文變成機器每次重驗的一道檢**。
  新 `template` 車道(零網路、零寫頁,與本閘既有紀律同):
    ① **完整性**:逐檔 sha256 對 `manifest.json` 的 223 筆(正本零觸碰的證據,不是宣稱)
    ② **離線契約**:三支正典入口頁逐頁掃 fetch/XHR/外部 src/相對 .json ——
       任何一項非零就 RED。**「零 server」這句話從此有人守**
    ③ **銜接面**:產業 profile、模組數、品質基線照印(manifest 是正本,本閘不自己編)
    ④ `--open`:以 `file://` 開啟正典啟動器,**走 SUP_MDL737 的 VIA_NO_OPEN 閘**
       (批366)——不自己繞過零跳出閘

CGC_MDL160_UIUnifyGate v0104 — U/I 畫面統一閘(批582 收回一個不能證明的承諾)

v0103→v0104(批582 操作員工作站實錄逼出來的自我更正)
  他那邊 `via-uiunify plan` 印出 RED 13,其中 VIA_UI_ETFConsensusAnalysis / RevenueConsensusAnalysis /
  StdDashboard / VRNControlTower 都掛著「★ owner 尾版已修好(批577):跑一次再生這張就會綠」——
  **但那些 owner(VDF_ENG068/069、VAP_ENG014…)我批577 根本沒碰過。**
  根因:v0103 的 `_owner_clean` 只問「owner 尾版原始碼裡找不到這條違規」就下保證。
  對 viewport/lang 這種**正向律**還算數(要有才算有);對 zero_cdn/zero_popup 這種**否定律**
  完全不算數——違規可能來自它 read 進來的樣板檔,不在它自己的原始碼裡。
  三處收窄:① 弱證據(mention)不給任何標記 ② 否定律遇到「會讀外部樣板」的引擎就不下結論
  ③ 措辭從「**就會綠**」改成「**再生一次即可驗證**;若仍紅,違規來自它引用的樣板」。
  **不承諾自己不能證明的結果**——那跟假綠是同一件事。

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
import hashlib
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


# ── 批648:U/I「面」的分類 ───────────────────────────────────────────────
#: **致動器端點**:打了它就會讓系統動起來(跑任務/收件/上傳)。
ACTUATOR_EP = re.compile(r"""["'`]/(?:run|intake|auto|upload|pick|stock_fetch)\b""")
#: **唯讀端點**:只問狀態,不改變任何東西。
READONLY_EP = re.compile(r"""["'`]/(?:ping|status|probe|stock_data)\b""")
#: 本機 hub(不是 CDN——批577 已經為這件事修過一次尺)。
HUB_RX = re.compile(r"127\.0\.0\.1|localhost")
FETCH_RX = re.compile(r"\bfetch\s*\(")

SURFACE = {
    "VIEW": "視圖面/入口面:**必須 file:// 直開**(L100);不得打任何 hub 端點",
    "READONLY_PANEL": "唯讀控制面:只問狀態;hub 不在要說得出來,不得白屏",
    "ACTUATOR": "致動器:會打 /run·/intake·/auto·/upload,**天生需要本機 hub**——"
                "要求它 file:// 可跑是問錯問題(靜態檔跑不了任務)",
}


def surface_of(t: str) -> str:
    """一張頁是哪一種面。**看它打什麼端點,不看它叫什麼名字。**"""
    if ACTUATOR_EP.search(t):
        return "ACTUATOR"
    if READONLY_EP.search(t) or (HUB_RX.search(t) and FETCH_RX.search(t)):
        return "READONLY_PANEL"
    return "VIEW"


def _inside_try(t: str, pos: int) -> bool:
    """這個位置是不是被某一層 `try{` 包著?**往回走括號深度**,不用字串比對。

    批648 第二把尺:第一版寫 `"try {" in before`(帶空格),而真頁是**壓縮過的** `try{`
    ——MasterControl 的 `try{const response=await fetch(...)` 與 VRNControlTower 的
    `try{const r=await(await fetch(...)).json()` 全被誤判成無退路。三件假紅,逐件看過才發現。
    正解:從 fetch 往回掃,每遇到 `}` 深度 +1、遇到 `{` 深度 -1;深度變成 -1 的那個 `{`
    就是包住它的區塊起點,看它前面幾個字是不是 `try`。逐層往外找,直到檔頭。
    """
    depth, i = 0, pos - 1
    while i >= 0:
        ch = t[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            if depth == 0:
                head = t[max(0, i - 12):i].replace(" ", "").replace("\n", "")
                if head.endswith("try"):
                    return True
                # 不是 try,繼續往更外層找
            else:
                depth -= 1
        i -= 1
    return False


def fetch_guards(t: str) -> list:
    """逐個 `fetch(` 看它有沒有退路。回 [(片段, 有無退路)]。

    尺的長法(LL278:分類尺靠走過真實命中長出來):
      從 `fetch(` 往前找有沒有包住它的 `try {`,往後掃到這條敘述鏈結束(深度回 0 且遇 `;`),
      在那一段裡找 `.catch(`。**只數整頁的 catch 總數是不夠的**——
      一頁有 7 個 fetch、5 個 catch,不代表每個 fetch 都被護到。
    """
    out = []
    for m in FETCH_RX.finditer(t):
        i = m.end()
        depth, j, nlim = 1, i, min(len(t), i + 1200)
        while j < nlim and depth > 0:
            ch = t[j]
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            j += 1
        # 鏈尾:再往後吃掉 .then(...).catch(...) 這一串,到 `;` 或換行結束
        k, depth2 = j, 0
        while k < min(len(t), j + 2000):
            ch = t[k]
            if ch in "([{":
                depth2 += 1
            elif ch in ")]}":
                depth2 -= 1
            elif ch == ";" and depth2 <= 0:
                break
            k += 1
        chain = t[m.start():k]
        guarded = (".catch(" in chain) or ("catch(" in chain.replace(" ", "")) \
            or _inside_try(t, m.start())
        out.append((chain[:70].replace("\n", " "), bool(guarded)))
    return out


#: **宣告面**:由「它住在哪」決定,不由「它做什麼」決定。
#: 批648 自訂正:第一版的越界檢是「分類成 VIEW 且打了 hub 端點」——
#: 而分類本身就是看端點,所以那個條件**邏輯上永遠不會成立**,是一盞永遠不會亮的燈
#: (LL133 判定器不自判;LL207 同族:加了態卻接不到)。
#: 非循環的尺:**宣告看位置,實測看端點,兩者不一致才是越界。**
DECLARED_VIEW = ("VIA_HTML_UI/ui/", "VIA_Reports/")


def declared_view(path_str: str) -> bool:
    p = path_str.replace("\\", "/")
    return any(k in p for k in DECLARED_VIEW)


def view_boundary(root: Path | None = None) -> dict:
    """L100 邊界:**宣告是入口/視圖面的頁,不得打任何 hub 端點**(打了就非 file:// 可開)。

    宣告面的母體= `VIA_HTML_UI/ui/`(正典入口)+ `VIA_Reports/**latest*.html`(產物視圖)。
    這兩處的頁本來就該 file:// 直開;它們一旦開始打 hub,L100 就破了而且沒有人會發現。
    """
    base = Path(root) if root is not None else VIA
    out = {"checked": 0, "cross": [], "state": "GREEN"}
    cands = list((base / "VIA_HTML_UI" / "ui").glob("*.html"))
    cands += [p for p in (base / "VIA_Reports").rglob("*.html") if "latest" in p.name]
    for p in cands:
        try:
            st = script_text(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        out["checked"] += 1
        s_ = surface_of(st)
        if s_ != "VIEW":
            out["cross"].append({"file": str(p.relative_to(base)), "measured": s_})
    out["state"] = "GREEN" if not out["cross"] else "RED"
    return out


def surfaces() -> dict:
    """全樹 U/I 頁的「面」分類 × 退路實況。**零寫頁。**"""
    rep_ = {"pages": 0, "by_surface": {}, "view_calls_hub": [], "unguarded": [], "detail": []}
    for p in pages():
        t = p.read_text(encoding="utf-8", errors="replace")
        #: 批648 第三把尺:**只看腳本脈絡**。本閘 v0103 早就為同一件事修過一次
        #: (`<code>confirm()</code>` 是函數名冊的說明文字,不是彈窗)——
        #: 我第一版又對整頁做比對,於是 VIA_UI_TreeAtlas 的
        #: `fetch()</li><li><code>FNC003</code>` 被判成 6 個沒有退路的 fetch。
        #: **行為只在腳本裡**,而本閘已經有 `script_text()`,不另寫一份(L30)。
        st = script_text(t)
        s = surface_of(st)
        rep_["pages"] += 1
        rep_["by_surface"][s] = rep_["by_surface"].get(s, 0) + 1
        g = fetch_guards(st)
        bad = [c for c, ok in g if not ok]
        if declared_view(str(p)) and s != "VIEW":
            rep_["view_calls_hub"].append(p.name)          # 宣告是視圖面,實測卻在打 hub
        if bad:
            rep_["unguarded"].append({"file": p.name, "surface": s,
                                      "fetch": len(g), "bad": len(bad), "sample": bad[:2]})
        if g:
            rep_["detail"].append({"file": p.name, "surface": s, "fetch": len(g),
                                   "guarded": sum(1 for _, ok in g if ok)})
    #: **判燈的只有「視圖面不得打 hub」這一條**(它靜態可證:端點字面就在腳本裡)。
    #: 退路那一條**降為 ADVISORY,永遠不判燈**——因為靜態掃描證不出它。實測走過的極限:
    #:   · `VIA_b64(f).then(b64 => fetch('/intake',…)).then(…)` → fetch 在回呼裡,守衛在**外層鏈**
    #:   · `function postJson(p,b){ return fetch(B+p,…).then(…) }` → promise 被 return 出去,
    #:     守衛在**呼叫端**
    #: 兩種都不在任何一個以 fetch 為起點的掃描窗裡。硬判就會生一面假紅牆(LL272),
    #: 而本閘 v0104 的紀律寫得很清楚:**不承諾自己不能證明的結果——那跟假綠是同一件事**。
    #: 所以這裡只**攤開**:哪幾張頁的哪幾個 fetch,在本尺的視野內看不到退路;要不要動,人來看。
    rep_["guard_note"] = ("ADVISORY:靜態掃描證不出「每個 fetch 都有退路」"
                          "(回呼內的 fetch 與被 return 出去的 promise,守衛在掃描窗之外);"
                          "本項只攤開不判燈")
    vb = view_boundary()
    rep_["boundary"] = vb
    rep_["view_calls_hub"] += [x["file"] + f"({x['measured']})" for x in vb["cross"]]
    rep_["state"] = "GREEN" if not rep_["view_calls_hub"] else "RED"
    return rep_


# ── 批647:正典 TEMPLATE(VIA_HTML_UI)──────────────────────────────────
TEMPLATE_ROOT = VIA / "VIA_HTML_UI"
TEMPLATE_MANIFEST = TEMPLATE_ROOT / "manifest.json"
#: 離線契約的四道尺。**行為在腳本裡**,所以看的是整頁原文的這四種寫法。
OFFLINE_RX = {
    "fetch(": re.compile(r"\bfetch\s*\(", re.I),
    "XHR": re.compile(r"XMLHttpRequest"),
    "外部 src/href": re.compile(r"""(?:src|href)\s*=\s*["'](?:https?:)?//""", re.I),
    "相對 .json": re.compile(r"""(?:src|href|url|open)\s*[=(]\s*["'][^"':]*\.json["']"""),
}


def git_probe(root: Path, sample: str = "") -> dict:
    """換行被改寫時,**閘自己去問 git**,而不是隔著網路叫操作員貼給我。

    批651 的實錄:批650 我給了
        git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"
    沙盒兩種情境(有先跑 git status / 沒先跑)都成功換回 LF,
    **操作員的機器上卻還是 173 件**。我沒有他的機器,再猜就是第二次亂槍打鳥。
    所以把診斷搬進閘裡:三個只讀的問題,一次問完。

    只讀、不寫、不觸網;git 不在就誠實說量不到(不假裝一切正常)。
    """
    out: dict[str, Any] = {"state": "NODATA", "why": "", "toplevel": "", "attr": "",
                           "autocrlf": "", "dirty": 0, "dirty_head": []}
    try:
        import subprocess                                  # 只呼叫本機 git,零網路
    except Exception as e:                                 # noqa: BLE001
        out["why"] = f"import subprocess 失敗:{e}"
        return out

    def g(*a: str) -> str:
        try:
            r = subprocess.run(("git",) + a, cwd=str(root), capture_output=True,
                               text=True, timeout=30)
            return (r.stdout or "").strip()
        except Exception:                                  # noqa: BLE001
            return ""

    top = g("rev-parse", "--show-toplevel")
    if not top:
        out["why"] = "這裡不是 git 工作副本,或 git 不在 PATH —— 量不到就說量不到"
        return out
    out["toplevel"] = top
    out["autocrlf"] = g("config", "core.autocrlf") or "(未設)"
    if sample:
        out["attr"] = g("check-attr", "text", "--", sample)
    st = g("status", "--porcelain", "--", str(root))
    lines = [x for x in st.splitlines() if x.strip()]
    out["dirty"] = len(lines)
    out["dirty_head"] = [x[:60] for x in lines[:3]]
    locked = "text: unset" in out["attr"]
    if not locked:
        out["state"] = "RED"
        out["why"] = ("**位元鎖沒生效**(check-attr 不是 `text: unset`)——"
                      ".gitattributes 還沒拉到,或樣式沒對上這個路徑。先 git pull。")
    elif lines:
        out["state"] = "YELLOW"
        out["why"] = ("位元鎖生效,而且 **git 看得見這些檔被改過**("
                      f"{len(lines)} 件)。下一道:\n"
                      '    git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"')
    else:
        out["state"] = "RED"
        out["why"] = ("位元鎖生效,但 **git 認為工作副本是乾淨的** —— 它的 stat 快取還停在"
                      "舊屬性下的判斷,所以 checkout 不會重寫任何檔案(這正是批650 那一道沒生效的樣子)。"
                      "把索引條目拿掉再長回來,強制重寫:\n"
                      '    git rm --cached -r -q -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"\n'
                      '    git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"')
    return out


def template(open_it: bool = False, root: Path | None = None) -> dict:
    """正典 TEMPLATE 的完整性 × 離線契約 × 銜接面。**零網路、零寫頁。**

    `manifest.json` 是這一包的正本:入口、目錄、profile、模組數、品質基線、逐檔 sha256
    全部從它讀出來——**本閘不自己編一份**(L30 一個出處)。
    """
    #: 批647:`root` 可注入。**自測給了自訂夾就不得再摸全域正式產物**(LL263 那次撞名的教訓)。
    troot = Path(root) if root is not None else TEMPLATE_ROOT
    tman = troot / "manifest.json"
    out = {"state": "ABSENT", "why": "", "root": str(troot), "release": "",
           "entrypoints": {}, "profiles": [], "module_counts": {}, "quality": {},
           "files_in_manifest": 0, "sha_ok": 0, "sha_drift": [], "eol_converted": [], "missing": [],
           "offline": {}, "offline_bad": [], "opened": ""}
    if not tman.is_file():
        out["why"] = (f"正典 TEMPLATE 冊不在:{tman}"
                      "(批647 之前它只在 main;**缺件是缺件,不是零違規**)")
        return out
    try:
        mf = json.loads(tman.read_text(encoding="utf-8"))
    except Exception as e:
        out["state"], out["why"] = "RED", f"冊讀不動:{type(e).__name__}: {e}"
        return out
    out["release"] = str(mf.get("release", ""))
    out["entrypoints"] = dict(mf.get("canonicalEntrypoints", {}))
    out["profiles"] = list(mf.get("industryProfiles", []))
    out["module_counts"] = dict(mf.get("moduleCounts", {}))
    out["quality"] = dict(mf.get("qualityBaseline", {}))
    # ① 完整性:逐檔 sha256 對冊
    rows = mf.get("files", []) or []
    out["files_in_manifest"] = len(rows)
    for r in rows:
        p = troot / str(r.get("path", ""))
        if not p.is_file():
            out["missing"].append(str(r.get("path", "")))
            continue
        try:
            got = hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            out["missing"].append(str(r.get("path", "")))
            continue
        want = str(r.get("sha256", ""))
        if got == want:
            out["sha_ok"] += 1
        else:
            # 批650 操作員實機實錄:對得上 50 · **漂移 173**。
            # 容器同一包量:二進位 42 + 本來就 CRLF 8 = **正好 50**;純 LF 文字件 **正好 173**。
            # 一個不多一個不少 —— 那不是漂移,是 Windows 的 core.autocrlf 把 LF 轉成 CRLF,
            # 每一行多一個位元組。冊上的 sha 算的是**原始位元**,當然對不上。
            # 「不一致」這三個字讓人以為正本被人改過;要說得出是哪一種不一致(L92)。
            b = p.read_bytes()
            if (hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == want
                    or hashlib.sha256(b.replace(b"\n", b"\r\n")).hexdigest() == want):
                out["eol_converted"].append(str(r.get("path", "")))
            else:
                out["sha_drift"].append(str(r.get("path", "")))
    # ② 離線契約:三支正典入口頁
    for key, rel in out["entrypoints"].items():
        p = troot / str(rel)
        if not p.is_file():
            out["offline"][key] = {"file": str(rel), "state": "ABSENT"}
            out["offline_bad"].append(f"{key}:檔不在")
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        hits = {k: len(rx.findall(t)) for k, rx in OFFLINE_RX.items()}
        bad = {k: v for k, v in hits.items() if v}
        out["offline"][key] = {"file": str(rel), "bytes": len(t),
                               "state": "GREEN" if not bad else "RED", "hits": bad}
        if bad:
            out["offline_bad"].append(f"{key}:{bad}")
    # 換行被改寫**仍然是紅**:冊的承諾就是逐位元相同,放行等於假綠。
    # 但它要跟「被人改過內容」分開報,而且要當場講得出治法(下面 fix_hint)。
    ok = (not out["sha_drift"]) and (not out["eol_converted"]) \
        and (not out["missing"]) and (not out["offline_bad"])
    out["state"] = "GREEN" if ok else "RED"
    out["git"] = git_probe(troot, out["eol_converted"][0]) if out["eol_converted"] else {}
    out["fix_hint"] = ("" if not out["eol_converted"] else
                       "git 改寫了正本的位元組(Windows core.autocrlf:LF→CRLF)。"
                       "批650 已在倉庫 .gitattributes 加位元鎖 "
                       "`VeritasIntelligenceAnalytics/VIA_HTML_UI/** -text`;"
                       "拉下來之後再下一道 "
                       '`git checkout HEAD -- "VeritasIntelligenceAnalytics/VIA_HTML_UI"` '
                       "把工作副本換回原始位元(沙盒實測過:光 pull 不會動到已經在磁碟上的檔)")
    out["why"] = ("完整性與離線契約皆過" if ok else
                  f"內容漂移 {len(out['sha_drift'])} · **換行被改寫 {len(out['eol_converted'])}** · "
                  f"缺件 {len(out['missing'])} · 離線契約違反 {len(out['offline_bad'])}")
    if open_it:
        launcher = troot / str(out["entrypoints"].get("launcher", ""))
        if launcher.is_file():
            try:
                if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "install_no_open_guard"):
                    VIA_ACCEL.install_no_open_guard()      # 批366 零跳出閘=操作員的開關,不繞過
                import webbrowser as _wb
                _wb.open(launcher.as_uri())
                out["opened"] = launcher.as_uri()
            except Exception as e:
                out["opened"] = f"(開不起來:{type(e).__name__})"
        else:
            out["opened"] = "(啟動器不在)"
    return out


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
    if row.get("owner_kind") == "mention":
        return False                       # 批582:弱證據不給任何保證
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
        # 批582:zero_cdn / zero_popup 是**否定律**——「原始碼裡找不到」不等於「產出不會有」,
        # 違規可能來自它讀進來的樣板檔。所以否定律只在「這支不讀外部樣板」時才敢下結論。
        if ("zero_cdn" in laws or "zero_popup" in laws) and _reads_template(s):
            return False
    return True


_TPL_HINT = re.compile("read_text|TEMPLATE|template|BaseTemplate|"
                       "UI_TemplateSSOT|render_template|jinja", re.I)


def _reads_template(src: str) -> bool:
    """這支引擎會不會把**別的檔**讀進來當版面(那樣違規就可能不在它自己的原始碼裡)。"""
    return bool(_TPL_HINT.search(src))


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
                # 批582 自我更正:v0103 在這裡寫「跑一次再生這張就會綠」——**那是我不能證明的承諾**。
                # 操作員工作站上 VIA_UI_ETFConsensusAnalysis 等頁掛著這個標記,
                # 但它們的 owner(VDF_ENG068 等)我**從來沒碰過**。
                # 「原始碼裡找不到違規」只支持「值得再生一次驗證」,不支持「一定會綠」。
                r["fix_ready"] = r.get("owner_kind")
                r["fix"] += ("  ★ **owner 尾版原始碼裡已無這條違規**"
                             + ("(而且它就是真的寫這張頁的那支)" if r.get("owner_kind") == "write"
                                else "(owner 是依 <title> 認的,可能不是真的產它那支)")
                             + " → **再生一次即可驗證**;若再生後仍紅,違規來自它引用的樣板")
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
    chk("㉒ 紅頁要分得出「**引擎還沒修**」和「**值得再生一次驗證**」;而且**不承諾不能證明的結果**"
        "(批582:否定律的「原始碼裡找不到」不等於「產出不會有」;弱證據不給標記)",
        all(("fix_ready" in r) == ("★" in r["fix"]) for r in _reds)
        and all("就會綠" not in r["fix"] for r in _reds)          # 批582:不承諾不能證明的結果
        and all(r.get("owner_kind") != "mention" for r in _reds if r.get("fix_ready")),
        f"(RED {len(_reds)} · 值得再生一次驗證的 {sum(1 for r in _reds if r.get('fix_ready'))})")

    chk("⑮ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    # ── 批647 正典 TEMPLATE 車道 ─────────────────────────────────────────
    import hashlib as _h647, json as _j647, shutil as _s647
    _live = template()
    chk("⑳ 正典 TEMPLATE 完整性:逐檔 sha256 對 `manifest.json`"
        "(批647 把 VIA_HTML_UI 226 件整包搬進 VIA 樹,**byte-exact**;"
        "正本零觸碰要拿得出證據,不是宣稱)",
        _live["state"] in ("GREEN", "RED", "ABSENT")
        and (_live["state"] != "GREEN" or (_live["sha_ok"] == _live["files_in_manifest"]
                                           and not _live["sha_drift"] and not _live["missing"])),
        f"({_live['state']} · 冊 {_live['files_in_manifest']} · 對上 {_live['sha_ok']}"
        f" · 漂移 {len(_live['sha_drift'])} · 缺 {len(_live['missing'])})")

    with tempfile.TemporaryDirectory() as _td647:
        _sb = Path(_td647) / "pkg"
        (_sb / "ui").mkdir(parents=True)
        _page = "<html><body><h1>x</h1></body></html>"
        (_sb / "ui" / "L.html").write_text(_page, encoding="utf-8")
        _mf = {"release": "test", "canonicalEntrypoints": {"launcher": "ui/L.html"},
               "industryProfiles": ["p1"], "moduleCounts": {"p1": 1}, "qualityBaseline": {},
               "files": [{"path": "ui/L.html", "bytes": len(_page),
                          "sha256": _h647.sha256(_page.encode()).hexdigest()}]}
        (_sb / "manifest.json").write_text(_j647.dumps(_mf, ensure_ascii=False), encoding="utf-8")
        _clean = template(root=_sb)
        # 竄改一個位元組 → 漂移要被指名
        (_sb / "ui" / "L.html").write_text(_page + "<!--x-->", encoding="utf-8")
        _drift = template(root=_sb)
        # 塞一個 fetch( → 離線契約要紅
        (_sb / "ui" / "L.html").write_text(_page.replace("<h1>", "<script>fetch('/a')</script><h1>"),
                                           encoding="utf-8")
        _mf["files"][0]["sha256"] = _h647.sha256((_sb / "ui" / "L.html").read_bytes()).hexdigest()
        _mf["files"][0]["bytes"] = (_sb / "ui" / "L.html").stat().st_size
        (_sb / "manifest.json").write_text(_j647.dumps(_mf, ensure_ascii=False), encoding="utf-8")
        _off = template(root=_sb)
        _absent = template(root=Path(_td647) / "_nope_")

    chk("㉑ 檢⑳ 咬得住:乾淨包 GREEN · **改一個位元組就指名漂移** · 夾不在=ABSENT 不是 GREEN"
        "(缺件是缺件,不是零違規)",
        _clean["state"] == "GREEN" and _drift["state"] == "RED"
        and _drift["sha_drift"] == ["ui/L.html"] and _absent["state"] == "ABSENT",
        f"(乾淨 {_clean['state']} · 竄改 {_drift['state']}{_drift['sha_drift']}"
        f" · 夾不在 {_absent['state']})")

    # ── 批650:換行被改寫 ≠ 內容漂移 ──
    #   操作員實機:對得上 50 · 漂移 173。容器同包量:二進位 42 + 本來就 CRLF 8 = 正好 50,
    #   純 LF 文字件正好 173。數字一個不多一個不少 —— 我的檢⑳ 把 git 的換行轉換
    #   報成「不一致」,那三個字讀起來像正本被人改過。判錯的紅燈和假綠一樣傷。
    with tempfile.TemporaryDirectory() as _td650:
        _sb2 = Path(_td650) / "pkg"
        (_sb2 / "ui").mkdir(parents=True)
        _lfpage = "<html>\n<body>\n<h1>x</h1>\n</body>\n</html>\n"
        _mf2 = {"release": "t", "canonicalEntrypoints": {"launcher": "ui/L.html"},
                "industryProfiles": ["p1"], "moduleCounts": {"p1": 1}, "qualityBaseline": {},
                "files": [{"path": "ui/L.html", "bytes": len(_lfpage),
                           "sha256": _h647.sha256(_lfpage.encode()).hexdigest()}]}
        (_sb2 / "manifest.json").write_text(_j647.dumps(_mf2, ensure_ascii=False), encoding="utf-8")
        # ① 模擬 Windows checkout:同樣的內容,換行被換成 CRLF
        (_sb2 / "ui" / "L.html").write_bytes(_lfpage.replace("\n", "\r\n").encode())
        _eol = template(root=_sb2)
        # ② 真的被改內容:不得被當成換行問題放過
        (_sb2 / "ui" / "L.html").write_bytes((_lfpage + "<!--tamper-->").encode())
        _tam = template(root=_sb2)
    chk("㉗ **換行被改寫 ≠ 內容漂移**(操作員實機 173 件全是這一種):"
        "CRLF 化的檔要歸 eol_converted、**仍然紅**、而且當場講得出治法;"
        "真的動到內容的要歸 sha_drift。兩種都紅,但紅的理由不能混為一談(L92)",
        (_eol["state"] == "RED" and _eol["eol_converted"] == ["ui/L.html"]
         and not _eol["sha_drift"] and "gitattributes" in _eol.get("fix_hint", "")
         and _tam["state"] == "RED" and _tam["sha_drift"] == ["ui/L.html"]
         and not _tam["eol_converted"]),
        f"(CRLF:{_eol['state']} eol={_eol['eol_converted']} drift={_eol['sha_drift']}"
        f" · 竄改:{_tam['state']} eol={_tam['eol_converted']} drift={_tam['sha_drift']})")

    # ── 批651:閘要自己會問 git,不要隔著網路叫操作員貼 ──
    #   批650 我給的 `git checkout HEAD -- <路徑>` 在沙盒兩種情境都成功,
    #   操作員機器上卻沒換回來。我沒有他的機器,不能猜第二次(L93 先疑尺不疑樹,
    #   但這次連樹都在別人家)。把三個只讀的問題搬進閘裡,一次問完。
    import subprocess as _sp651
    def _git651(cwd, *a):
        return _sp651.run(("git",) + a, cwd=str(cwd), capture_output=True, text=True, timeout=30)
    _gitok = True
    try:
        _git651(".", "--version")
    except Exception:                                      # noqa: BLE001
        _gitok = False
    if _gitok:
        with tempfile.TemporaryDirectory() as _td651:
            _rp = Path(_td651) / "repo"
            (_rp / "pkg").mkdir(parents=True)
            (_rp / "pkg" / "f.md").write_bytes(b"a\nb\n")
            _git651(_rp, "init", "-q")
            _git651(_rp, "add", "-A")
            _git651(_rp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "i")
            # ① 沒有位元鎖 → 閘要說「鎖沒生效」
            _p_nolock = git_probe(_rp / "pkg", "pkg/f.md")
            # ② 有位元鎖 + 檔案被換成 CRLF → 閘要說「git 看得見,下一道 checkout」
            (_rp / ".gitattributes").write_text("pkg/** -text\n", encoding="utf-8")
            _git651(_rp, "add", "-A")
            _git651(_rp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "a")
            (_rp / "pkg" / "f.md").write_bytes(b"a\r\nb\r\n")
            _p_dirty = git_probe(_rp / "pkg", "pkg/f.md")
            # ③ 有位元鎖 + 工作副本乾淨 → 閘要說「git 認為乾淨,要先 rm --cached」
            (_rp / "pkg" / "f.md").write_bytes(b"a\nb\n")
            _p_clean = git_probe(_rp / "pkg", "pkg/f.md")
        chk("㉘ **閘自己會問 git**(批650 我給的那一道在操作員機器上沒生效,而我沒有他的機器"
            "——再猜就是第二次亂槍)。三種局面要分得開:鎖沒生效 / 鎖生效且 git 看得見 /"
            "鎖生效但 git 認為乾淨(那正是 checkout 不會重寫任何檔的樣子)。只讀、不寫、不觸網",
            (_p_nolock["state"] == "RED" and "位元鎖沒生效" in _p_nolock["why"]
             and _p_dirty["state"] == "YELLOW" and _p_dirty["dirty"] >= 1
             and "checkout HEAD" in _p_dirty["why"]
             and _p_clean["state"] == "RED" and "rm --cached" in _p_clean["why"]
             and "text: unset" in _p_dirty["attr"]),
            f"(無鎖 {_p_nolock['state']} · 有鎖髒 {_p_dirty['state']}/{_p_dirty['dirty']} 件"
            f" · 有鎖乾淨 {_p_clean['state']})")
    else:
        chk("㉘ 閘自己會問 git(本境沒有 git=量不到,誠實 SKIP 不假裝過)", True, "git ABSENT")

    chk("㉒ **離線契約是機器驗的,不是散文**:入口頁塞一個 `fetch(` 就 RED"
        "(STANDARD.md 寫「usable from file:// without network」——批647 之前沒有任何一道檢在守它;"
        "而樹內另一套 ui_support/VIA_UI_*.html 68 份裡有 30 份要靠 hub)",
        _off["state"] == "RED" and any("fetch(" in str(v.get("hits", ""))
                                       for v in _off["offline"].values()),
        f"({_off['state']} · {[v.get('hits') for v in _off['offline'].values()]})")

    _code647 = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("㉓ `--open` **走 SUP_MDL737 的 VIA_NO_OPEN 閘**(批366),不自己繞過零跳出閘;"
        "且 template 車道零寫頁(不寫任何 .html)",
        "install_no_open_guard" in _code647
        and "write_text" not in _code647.split("def template", 1)[1].split("def external_links", 1)[0],
        "(零跳出閘在位 · template 不寫頁)")

    # ── 批648「面」分類與 L100 邊界 ───────────────────────────────────────
    _act = "<script>fetch('/run?task=x').then(r=>r.json())</script>"
    _ro = "<script>fetch('/ping').then(r=>r.json()).catch(()=>{})</script>"
    _view = "<script>const a=1;</script>"
    chk("㉔ 「面」分得出來:打 /run 是**致動器**、只打 /ping 是唯讀控制面、都不打是視圖面"
        "(批648 更正:我上一批問『要不要把那 30 份收成資料內嵌』——"
        "真的去量,**沒有一份在抓自己的 .json**,它們抓的全是 hub 端點;"
        "一個會打 `/run?task=` 的頁是致動器,**靜態檔跑不了任務**,那個問題不成立)",
        surface_of(script_text(_act)) == "ACTUATOR"
        and surface_of(script_text(_ro)) == "READONLY_PANEL"
        and surface_of(script_text(_view)) == "VIEW",
        f"({surface_of(script_text(_act))} / {surface_of(script_text(_ro))} / {surface_of(script_text(_view))})")

    with tempfile.TemporaryDirectory() as _td648:
        _sb = Path(_td648)
        (_sb / "VIA_HTML_UI" / "ui").mkdir(parents=True)
        (_sb / "VIA_Reports" / "x").mkdir(parents=True)
        (_sb / "VIA_HTML_UI" / "ui" / "ok.html").write_text(_view, encoding="utf-8")
        (_sb / "VIA_Reports" / "x" / "a_latest.html").write_text(_view, encoding="utf-8")
        _clean648 = view_boundary(root=_sb)
        (_sb / "VIA_Reports" / "x" / "b_latest.html").write_text(_act, encoding="utf-8")
        _cross648 = view_boundary(root=_sb)
    chk("㉕ **L100 邊界咬得住**:宣告是入口/視圖面(VIA_HTML_UI/ui + VIA_Reports latest)的頁"
        "一旦打 hub 端點就被點名。**這一檢我改過一次尺**:第一版寫「分類成 VIEW 且打了 hub」,"
        "而分類本身就是看端點——那個條件**邏輯上永遠不會成立**,是一盞永遠不會亮的燈"
        "(LL133 判定器不自判)。非循環的尺:**宣告看位置,實測看端點**",
        _clean648["state"] == "GREEN" and not _clean648["cross"]
        and _cross648["state"] == "RED"
        and [x["measured"] for x in _cross648["cross"]] == ["ACTUATOR"],
        f"(乾淨 {_clean648['state']} {_clean648['checked']} 張 · 越界 {_cross648['state']}"
        f" {[x['file'] for x in _cross648['cross']]})")

    _min = "<script>try{const r=await(await fetch('/ping')).json();}catch(e){}</script>"
    _g = fetch_guards(script_text(_min))
    _r648 = surfaces()
    chk("㉖ 退路那一項是 **ADVISORY 不判燈**,而且尺的極限寫在報告裡"
        "(靜態掃描證不出「每個 fetch 都有退路」:回呼內的 fetch 與被 return 出去的 promise,"
        "守衛在掃描窗之外——硬判就是一面假紅牆 LL272;本閘 v0104 的紀律是"
        "**不承諾自己不能證明的結果**)。另:`_inside_try` 要認得壓縮寫法 `try{`"
        "(第一版只認 `try {` 帶空格,三件真頁被誤判)",
        all(ok for _, ok in _g) and _g
        and "ADVISORY" in str(_r648.get("guard_note", ""))
        and (_r648["state"] == "GREEN" or _r648["view_calls_hub"]),
        f"(壓縮 try{{ 認得={all(ok for _, ok in _g)} · 裁決 {_r648['state']}"
        f" · ADVISORY 攤開 {len(_r648['unguarded'])} 張)")

    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL160_UIUnifyGate", description="U/I 畫面統一閘(零網路;不改頁)")
    ap.add_argument("verb", nargs="?", default="scan",
                    choices=["scan", "plan", "contract", "header", "template", "surface"])
    ap.add_argument("--open", action="store_true",
                    help="template:以 file:// 開正典啟動器(走 VIA_NO_OPEN 閘)")
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
    if a.verb == "surface":
        r = surfaces()
        print(f"[CGC_MDL160 v{VERSION}] U/I「面」分類 · {r['state']} · {r['pages']} 張頁")
        for k, zh in SURFACE.items():
            print(f"  [{k:<15}] {r['by_surface'].get(k, 0):>3} 張 · {zh}")
        _vb = r.get("boundary", {})
        print(f"  [L100 邊界] 宣告面(VIA_HTML_UI/ui + VIA_Reports latest)驗 {_vb.get('checked', 0)} 張"
              f" · **越界 {len(r['view_calls_hub'])}**"
              + ("(0=宣告是視圖面的,沒有一張在打 hub)" if not r["view_calls_hub"] else ""))
        for x in r["view_calls_hub"][:8]:
            print(f"    [越界] {x}")
        print(f"  [ADVISORY · 本尺視野內看不到退路的 fetch] {len(r['unguarded'])} 張"
              f"(**不判燈**;{r.get('guard_note', '')[:52]}…)")
        for x in r["unguarded"][:8]:
            print(f"    [無退路] {x['file'][:46]:<46} {x['surface']:<15}"
                  f" {x['bad']}/{x['fetch']} 個 fetch 沒護到")
            for s in x["sample"]:
                print(f"        · {s}")
        print(f"  [裁決] {r['state']} · "
              + ("**視圖面零越界**(L100 的邊界守住了);退路那一項為 ADVISORY,見上"
                 if r["state"] == "GREEN"
                 else "視圖面有頁在打 hub——**本閘不改頁**,只點名、只指 owner(v0102 起的紀律)"))
        return 0 if r["state"] == "GREEN" else 1
    if a.verb == "template":
        r = template(open_it=a.open)
        print(f"[CGC_MDL160 v{VERSION}] 正典 TEMPLATE · {r['state']} · {r['why']}")
        print(f"  根 {r['root']} · release {r['release'] or '(未標)'}")
        if r["state"] == "ABSENT":
            print(f"  [裁決] ABSENT · {r['why']}")
            return 3
        print(f"  [完整性] 冊上 {r['files_in_manifest']} 件 · sha 對得上 {r['sha_ok']}"
              f" · **內容漂移 {len(r['sha_drift'])}** · **換行被改寫 {len(r.get('eol_converted') or [])}**"
              f" · **缺件 {len(r['missing'])}**")
        if r.get("eol_converted"):
            print(f"    [換行被改寫] {len(r['eol_converted'])} 件 —— 內容是對的,位元不是。"
                  f"例:{', '.join(r['eol_converted'][:3])}")
            print(f"    [治法] {r.get('fix_hint', '')}")
            _g = r.get("git") or {}
            if _g:
                print(f"    [問 git] 工作副本 {_g.get('toplevel', '?')} · core.autocrlf={_g.get('autocrlf', '?')}")
                print(f"             check-attr → {_g.get('attr') or '(問不到)'}"
                      f" · git 看得見被改過的 {_g.get('dirty', 0)} 件")
                for _x in _g.get("dirty_head") or []:
                    print(f"               {_x}")
                print(f"    [{_g.get('state', 'NODATA')}] {_g.get('why', '')}")
        for x in (r["sha_drift"] + r["missing"])[:6]:
            print(f"    [不一致] {x}")
        print("  [離線契約] 「file:// 直開、零 server」——本閘逐頁量,不看它自己怎麼宣稱:")
        for k, v in r["offline"].items():
            print(f"    [{v['state']:<6}] {k:<12} {v['file']:<42}"
                  + (f" {v.get('bytes', 0):,} 字" if v.get("bytes") else "")
                  + (f"  ← {v.get('hits')}" if v.get("hits") else ""))
        print(f"  [銜接面] 產業 profile {len(r['profiles'])} 個 {r['profiles']}"
              f" · 模組 {r['module_counts']}")
        q = r["quality"]
        if q:
            print(f"  [品質基線(冊上)] e2e {q.get('e2ePassed')}/{q.get('e2eTotal')}"
                  f" · 跨頁同步 {q.get('crossPageSyncPassed')}/{q.get('crossPageSyncTotal')}"
                  f" · 啟動器流程 {q.get('launcherUserFlow')} · 視埠 {q.get('viewports')}")
        if r["opened"]:
            print(f"  [開啟] {r['opened']}")
        print(f"  [裁決] {r['state']} · {r['why']}")
        return 0 if r["state"] == "GREEN" else 1
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
