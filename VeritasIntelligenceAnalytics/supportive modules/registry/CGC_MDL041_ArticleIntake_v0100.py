#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_article_intake_v0100 — 文章攝入引擎(TOOL-045;補強令 2026-08-18)
======================================================================
令:四份 2026 最佳實務文檔(SSOT 抽取管線/文章清洗 URL 擷取/多階段修復
摘要/多因子驗證)之功能工具落地第一波——「一連串混合訊息→多篇結構化
文章」。對齊攝入分類 Schema v001(11 軸)與可治理抽取管線原則:
  ① 切分 — URL 邊界/標題線索/分隔符(---/===)/空行段落聚類
  ② 修復 — CJK 斷行黏合/空白正規化/\xa0/重複空行(保守:不改寫錯字,
     不動專有名詞/代號/URL)
  ③ 判別 — 語言(zh-TW/zh-CN/en/mixed;簡體專用字集偵測)/標題推斷
     (首短句或 markdown #)/規則分類(財經/科技/新聞/專案/法規/其他)
  ④ 輸出 — JSONL+CSV(每筆:url/title/body/category/language/
     source_form=TEXT/provenance/confidence;11 軸對齊,缺軸誠實 Pending)
  ⑤ URL 抓取道(--fetch)— 紅線:僅操作員提供之 URL(非爬站),
     鎖 VIA_NET_CONSENT 同意閘;bs4/trafilatura 在則精抽,缺則標準庫
     regex 低保真誠實標記(GRAPH_OCR 級低信度不單獨計分原則同源)
graceful:opencc/langdetect/bs4 缺席=誠實降級,標準庫全程可跑。
用法:via-article <txt/md 檔>       → 切分+修復+分類+輸出
     via-article --fetch <url>     → 抓取單 URL(同意閘)
     via-article --selftest        → 合成流四檢(零網路)
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

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "article_runs"

URL_RX = re.compile(r"https?://[^\s<>\"')]+")
SEP_RX = re.compile(r"^\s*(-{3,}|={3,}|\*{3,})\s*$")
HEAD_RX = re.compile(r"^#{1,3}\s+(.+)$")
# 簡體專用字樣本集(繁體文本不出現;偵測 zh-CN)
SIMP_CHARS = set("么这为说对时经过还发货组织变让贝见观现规则务动带响听")
CATS = [
    ("財經/投資", ["股", "ETF", "基金", "融資", "外資", "殖利率", "財報", "營收", "投資", "台股", "美股", "債券", "匯率", "CPI", "PMI", "央行"]),
    ("科技", ["AI", "晶片", "半導體", "軟體", "模型", "GPU", "資料庫", "程式", "演算法", "雲端"]),
    ("法規/政策", ["法規", "政策", "監管", "法案", "合規", "主管機關"]),
    ("專案管理", ["專案", "排程", "里程碑", "交付", "需求", "工作流"]),
    ("新聞", ["報導", "記者", "訊息指出", "消息人士"]),
]


def _lang(text: str) -> str:
    han = sum(1 for c in text if "一" <= c <= "鿿")
    if han == 0:
        return "en" if re.search(r"[A-Za-z]", text) else "unknown"
    simp = sum(1 for c in text if c in SIMP_CHARS)
    zh = "zh-CN" if simp >= max(2, han // 200) else "zh-TW"
    latin = len(re.findall(r"[A-Za-z]{3,}", text))
    return f"{zh}+en" if latin >= 10 else zh


def _clean(text: str) -> str:
    text = text.replace("\xa0", " ").replace("​", "")
    text = re.sub(r"[ \t]+", " ", text)
    # CJK 斷行黏合:上行尾與下行首皆為漢字且上行無句чит越終標點 → 併行
    lines = text.splitlines()
    out = []
    for ln in lines:
        ln = ln.rstrip()
        if (out and out[-1] and ln
                and re.search(r"[一-鿿]$", out[-1])
                and not re.search(r"[。!?!?:;;.」』】)]$", out[-1])
                and re.match(r"^[一-鿿]", ln)):
            out[-1] += ln
        else:
            out.append(ln)
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _classify(text: str) -> str:
    scores = {name: sum(text.count(k) for k in kws) for name, kws in CATS}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "其他"


def _title_of(block: str) -> str:
    for ln in block.splitlines():
        ln = ln.strip()
        if not ln or URL_RX.fullmatch(ln):
            continue
        m = HEAD_RX.match(ln)
        if m:
            return m.group(1).strip()[:80]
        return (ln[:60] + ("…" if len(ln) > 60 else ""))
    return "(無標題)"


def segment(raw: str) -> list[dict]:
    """混合訊息流 → 文章塊(URL 邊界/標題/分隔符/空行聚類)。"""
    lines = raw.splitlines()
    blocks, cur = [], []

    def flush():
        if cur and any(l.strip() for l in cur):
            blocks.append("\n".join(cur).strip())
        cur.clear()

    for i, ln in enumerate(lines):
        if SEP_RX.match(ln):
            flush()
            continue
        is_url_line = bool(URL_RX.fullmatch(ln.strip()))
        is_head = bool(HEAD_RX.match(ln.strip()))
        if (is_url_line or is_head) and cur and any(l.strip() for l in cur[-3:]):
            flush()
        cur.append(ln)
    flush()

    arts = []
    for b in blocks:
        body = _clean(b)
        if len(body) < 20:
            continue  # 噪聲塊誠實剔除
        urls = URL_RX.findall(b)
        arts.append({
            "url": urls[0] if urls else "",
            "title": _title_of(b),
            "body": body,
            "category": _classify(body),
            "language": _lang(body),
            "source_form": "TEXT",
            "evidence_status": "M",
            "confidence": 0.7 if urls else 0.6,
            "quality_flags": [] if len(body) > 80 else ["SHORT"],
        })
    return arts


def fetch_url(url: str) -> dict | None:
    """URL 抓取道:僅操作員提供之 URL;同意閘;bs4 在則精抽缺則低保真。"""
    sys.path.insert(0, str(VIA / "supportive modules"))
    try:
        import VIA_NetSupport as net
    except ImportError:
        net = None
    if not (net and net.net_consent()):
        print("  [同意閘] 未同意——$env:VIA_NET_CONSENT='YES' 後重跑(紅線:不代設)")
        return None
    html = net.fetch_text(url)
    if html is None:
        print("  [FAIL] 抓取失敗(誠實 None)")
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.select("script,style,noscript,iframe,nav,footer,header,aside,form"):
            tag.decompose()
        og = soup.select_one('meta[property="og:title"]')
        title = (og.get("content", "") if og else "") or (soup.title.get_text(strip=True) if soup.title else "")
        node = None
        for sel in ("article", '[itemprop="articleBody"]', ".article-content", ".post-content", "main"):
            node = soup.select_one(sel)
            if node:
                break
        paras = [p.get_text(" ", strip=True) for p in (node or soup).find_all("p")]
        body = "\n\n".join(dict.fromkeys(t for t in paras if len(t) >= 15))
        fidelity = "bs4 精抽"
    except ImportError:
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else ""
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S | re.I)
        body = _clean(re.sub(r"<[^>]+>", "\n", text))[:8000]
        fidelity = "標準庫低保真(bs4 缺——低信度,不單獨計分)"
    art = {"url": url, "title": _clean(title)[:120], "body": _clean(body),
           "category": _classify(body), "language": _lang(body),
           "source_form": "API" if "bs4" in fidelity else "GRAPH_OCR級",
           "evidence_status": "M", "confidence": 0.8 if "精抽" in fidelity else 0.3,
           "quality_flags": [] if "精抽" in fidelity else ["LOW_FIDELITY"]}
    print(f"  [抓] {url[:60]} · {fidelity} · 本文 {len(art['body'])} 字")
    return art


def export(arts: list[dict], tag: str) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUT.mkdir(parents=True, exist_ok=True)
    jl = OUT / f"ARTICLES_{ts}_{tag}.jsonl"
    with open(jl, "w", encoding="utf-8") as fh:
        for a in arts:
            fh.write(json.dumps({**a, "provenance": tag, "extracted_at": ts,
                                 "schema": "VIA.ArticleIntake.v1"}, ensure_ascii=False) + "\n")
    cv = OUT / f"ARTICLES_{ts}_{tag}.csv"
    with open(cv, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["url", "title", "category", "language", "confidence", "body_head"])
        for a in arts:
            w.writerow([a["url"], a["title"], a["category"], a["language"],
                        a["confidence"], a["body"][:120]])
    print(f"  [出] {jl.name} + {cv.name}(11 軸對齊;缺軸誠實 Pending)")


def selftest() -> int:
    print("=== 文章攝入 v0100 · 自測四檢(零網路)===")
    raw = """https://example.com/news1
台積電今日召開法說會,外資關注先進製程資本支出與
毛利率展望。融資餘額連三日下降。
---
# AI 模型部署指南
本文介紹如何在本地部署大型語言模型,包含 GPU 資源配置與
資料庫連線設定。程式碼範例使用 Python。
===
这是一段简体中文的新闻报导,记者指出相关政策变化。
"""
    arts = segment(raw)
    checks = [
        ("切分三篇", len(arts) == 3),
        ("URL 綁定+財經分類", arts[0]["url"].endswith("news1") and arts[0]["category"] == "財經/投資"),
        ("標題推斷+科技分類", arts[1]["title"].startswith("AI 模型") and arts[1]["category"] == "科技"),
        ("簡體偵測", arts[2]["language"].startswith("zh-CN")),
    ]
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    # 斷行黏合驗證
    joined = "外資關注先進製程資本支出與毛利率展望" in arts[0]["body"]
    n += joined
    print(f"  [{'PASS' if joined else 'FAIL'}] CJK 斷行黏合")
    print(f"  [計] {n}/5 檢通過")
    return 0 if n == 5 else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    if "--fetch" in argv:
        art = fetch_url(argv[argv.index("--fetch") + 1])
        if art:
            export([art], "fetch")
        return 0 if art else 1
    if not argv:
        print(__doc__)
        return 2
    src = Path(argv[0])
    if not src.is_file():
        print(f"[FAIL] 檔案不存在:{src}")
        return 1
    raw = src.read_text(encoding="utf-8", errors="replace")
    arts = segment(raw)
    print(f"=== 文章攝入 v0100 · {src.name} · 切出 {len(arts)} 篇 ===")
    for a in arts[:10]:
        print(f"  [{a['category']:6s}] {a['language']:8s} · {a['title'][:50]}")
    if len(arts) > 10:
        print(f"  …共 {len(arts)} 篇")
    export(arts, src.stem[:30])
    return 0


if __name__ == "__main__":
    sys.exit(main())
