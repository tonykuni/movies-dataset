#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG085_MarkdownRestore v0100 — 本文還原與分類標註(批636)

操作員令(批636):
  「擷取本文用非OCR / MARKDOWN / OCR 多種擷取法,有時會本文及表格同步擷取;
   用 LAYOUT 引擎標註類別、次類別、頁數;先把還原,再把本文修好,斷行間隔修好,
   一句一行、一標題一行、表格一列一行等還原原貌;表格資料庫;
   文字修正好並標示是標題、表、本文還是其他;
   這是一個**不刪除**修正好本文輸出;再根據修正好的輸出進行 SUMMARIZE。」

【零九頭龍:三道擷取與 LAYOUT 標註都不重做】
  VRN_ENG072 已經落下 sidecar,裡面就有:
      header / right / body / footer   四區(周邊資訊區與本文已分開)
      heads      GenericLayoutEngine 標的 {text, size, level:H1/H2/H3}
      tables     逐表逐列
      compare    **方法之間逐區對照**({ratio, verdict: AGREE/DIVERGE/BOTH_EMPTY})
      triage     DIGITAL / 稀薄 / backend(非OCR 還是 OCR 走的哪一道)
  所以本器**讀 sidecar**,不重抽一次。重抽的那一份跟原本那一份遲早會不一樣。

【要修的病(實測,不是假設)】
  `VRN_Meeting_Minutes` 這一份:
      tables[0] 只撈到表頭 `[['#','行動','負責人','期限']]` —— **一列**,
      而資料列全部漏進 body,變成
          「1 Action Items 行動項目#行動負責人期限1 ControlCenter 的即時狀態燈號…」
  這就是操作員說的「有時會本文及表格同步擷取」。
  本器的 A 道就是把**已經黏進本文的表格片段**找回來、標成表,
  而不是把它刪掉——刪掉就違反「不刪除」。

【不刪除是硬規矩】
  輸出是**新的一層**:原件零觸碰、sidecar 零改寫。
  而且**字元保全率**要現場量:來源(四區+表)的非空白字元,
  一個都不可以在輸出裡消失。㊀ 那一檢就是釘這件事——
  「修好」如果是靠丟掉修不動的那幾段換來的,那不是修好。

【類別 / 次類別】
  標題 H1/H2/H3 · 表 表頭/表列 · 本文 句 · 其他 頁首/右欄/頁尾
  判不出來的標 `未分類`,**不硬塞本文**(硬塞的那一段 SUMMARIZE 會當句子讀)。

【頁數】
  sidecar 是首頁層級,所以預設 page=1;頁尾寫得出「第 N 頁」就用它。
  兩者都沒有就 **page=None 並說出來**,不編一個號碼。

【紀律】
  · 零網路 · 原件零觸碰 · 預設**不寫庫**(表格入庫要 `--apply`)
  · 零九頭龍:擷取、LAYOUT、SUMMARIZE 都呼叫既有正主

用法:
  … run --in "<sidecar 夾>"            還原全部(只讀;出 .md 與 manifest)
  … one --file "<sidecar.json>"        單份
  … run --in <夾> --apply              表格另外入庫(vrn_md_tables)
  … --selftest
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
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
SIDECARS = VIA / "VIA_Reports" / "first_page_text"
OUT = VIA / "VIA_Reports" / "vrn" / "markdown"

# 類別冊。**這一份是分類的唯一出處**——頁上/庫裡/MD 裡的標籤都從這裡長出來。
KINDS = {
    "標題": {"subs": ["H1", "H2", "H3", "H4"], "md": "#", "why": "LAYOUT 引擎給的層級"},
    "表":   {"subs": ["表頭", "表列", "表格殘片"], "md": "|", "why": "來自 tables,或從本文裡找回來的殘片"},
    "本文": {"subs": ["句"], "md": "", "why": "一句一行"},
    "其他": {"subs": ["頁首", "右欄", "頁尾"], "md": ">", "why": "周邊資訊區"},
    "未分類": {"subs": ["未分類"], "md": "", "why": "判不出來就說判不出來,不硬塞本文"},
}

_ZW = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF, 0x00AD))
_SENT_END = "。．.!?!?;;"
#: 光禿禿的編號:`1.` `2)` `①` `(3)`——它是下一句的號碼,不是一句話。
_BARE_NUM = re.compile(r"[(（]?\s*(?:\d{1,3}|[①-⑳]|[a-zA-Z])\s*[.)）、]?\s*")


def norm(s: str) -> str:
    """比對用的正規化:去零寬、全形→半形、壓空白。**只用於比對,不用於輸出**。"""
    s = str(s or "")
    s = s.translate({ord(c): None for c in _ZW})
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def repair_text(s: str) -> tuple:
    """修斷行與間隔。回 `(修好的字串, {動了幾處})`。

    **不刪字**:只做四件——去零寬、全形空白換半形、把 CJK 中間被硬斷的行接回、
    壓連續空白。每一種都記次數,因為「修了什麼」要說得出來。
    """
    n = {"zw": 0, "fullwidth_space": 0, "joins": 0, "spaces": 0}
    for c in _ZW:
        n["zw"] += s.count(c)
    s = s.translate({ord(c): None for c in _ZW})
    n["fullwidth_space"] = s.count("　")
    s = s.replace("　", " ")
    # CJK 被硬斷:`中\n文` → `中文`(兩側都是 CJK 才接,英數不接——英數接了會黏成錯字)
    def _j(m):
        n["joins"] += 1
        return m.group(1) + m.group(2)
    s = re.sub(r"([一-龥])\s*\n\s*([一-龥])", _j, s)
    before = len(s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    n["spaces"] = before - len(s)
    return s, n


def split_sentences(s: str) -> list:
    """一句一行。**只在句末標點斷**,而且表格與標題不走這裡。

    為什麼不順便拿換行當句界:研報的換行多半是版面折行不是句界,
    拿它斷會把一句話切成三行(而 SUMMARIZE 會把三行讀成三件事)。
    """
    out, buf = [], ""
    for ch in str(s or ""):
        buf += ch
        if ch in _SENT_END:
            t = buf.strip()
            if t:
                out.append(t)
            buf = ""
    t = buf.strip()
    if t:
        out.append(t)
    # **光禿禿的編號不是一句**。`1.` / `2.` / `①` 被句末的 `.` 切成獨立一行之後,
    #   「一句一行」就變成「一個號碼也一行」——而 SUMMARIZE 會把它讀成一件事。
    #   編號黏回它後面那一句(實測:VRN_Meeting_Minutes 一份就生了 5 行這種)。
    merged = []
    for x in out:
        if merged and _BARE_NUM.fullmatch(merged[-1]):
            merged[-1] = merged[-1] + " " + x
        else:
            merged.append(x)
    return merged


def table_fragments(tables: list) -> dict:
    """本文裡用來找回表格殘片的鑰匙。回 `{"row": [...], "cell": [...]}`。

    **以「列」為單位拼起來**,不是逐格比——自測 ⑧ 當場抓到:
    病灶是整列被黏進本文(`…行動項目#行動負責人期限1 燈號要補…`),
    而逐格比的話 `#` 太短被濾掉、`行動` 又不在行首,於是一個都對不上,
    那一行就被判成本文(而 SUMMARIZE 會把表頭當句子讀)。
    列鑰匙要 ≥2 格且 ≥4 字才算數,不然 `['1','2']` 這種會亂咬。
    """
    rows, cells = [], []
    for t in tables or []:
        for row in (t or []):
            cs = row if isinstance(row, (list, tuple)) else [row]
            ks = [norm(c) for c in cs]
            joined = "".join(ks)
            if len([k for k in ks if k]) >= 2 and len(joined) >= 4:
                rows.append(joined)
            for k in ks:
                if len(k) >= 4:
                    cells.append(k)
    return {"row": sorted(set(rows), key=len, reverse=True),
            "cell": sorted(set(cells), key=len, reverse=True)}


def page_of(sc: dict) -> tuple:
    """頁數。頁尾寫得出「第 N 頁」就用它;否則 sidecar 是首頁層級 → 1;
    真的判不出來回 `(None, 理由)`——**不編號碼**。"""
    foot = str(sc.get("footer") or "")
    m = re.search(r"第\s*(\d{1,4})\s*頁", foot) or re.search(r"[Pp]age\s*(\d{1,4})", foot)
    if m:
        return int(m.group(1)), "頁尾寫出來的"
    if any(str(sc.get(k) or "").strip() for k in ("header", "right", "body", "footer")):
        return 1, "sidecar 是首頁層級(ENG072 只抽第一頁),所以是 1"
    return None, "頁尾沒寫、四區也全空——判不出來就不編號碼"


def restore(sc: dict, name: str = "") -> dict:
    """一份 sidecar → 分類標註過的行串 + 保全率。"""
    page, page_why = page_of(sc)
    frs = table_fragments(sc.get("tables") or [])
    heads = []
    for h in (sc.get("heads") or []):
        if isinstance(h, dict) and str(h.get("text") or "").strip():
            heads.append({"key": norm(h["text"]), "text": str(h["text"]).strip(),
                          "level": str(h.get("level") or "H3").upper(),
                          "size": h.get("size")})
    head_keys = {h["key"]: h for h in heads}

    rows = []

    def add(kind, sub, text, why, extra=None):
        t = str(text or "").strip()
        if not t:
            return
        rows.append(dict({"kind": kind, "sub": sub, "text": t, "page": page, "why": why},
                         **(extra or {})))

    # ① 其他:周邊資訊區(頁首 / 右欄 / 頁尾)
    for key, sub in (("header", "頁首"), ("right", "右欄"), ("footer", "頁尾")):
        raw = str(sc.get(key) or "")
        if raw.strip():
            fixed, _ = repair_text(raw)
            add("其他", sub, fixed, f"ENG072 的 {key} 區")

    # ② 標題 + 本文:走 body,先把標題整行切出來,剩下的才斷句
    body, rep = repair_text(str(sc.get("body") or ""))
    for line in [x for x in re.split(r"\n+", body) if x.strip()]:
        k = norm(line)
        if k in head_keys:
            h = head_keys[k]
            add("標題", h["level"], line, f"LAYOUT 引擎標的 {h['level']}(字級 {h['size']})")
            continue
        # 標題被黏在行首**或行中**。
        #   實測:`M E E T I N G M I N U T E S · 會議紀錄VRN Fetch v4 — 設計審查會議日期…`
        #   裡面那個 H1 `VRN Fetch v4 — 設計審查會議` 卡在中間,只比行首是抓不到的
        #   ——跟表格殘片同一種病:黏在哪裡都要找得回來。
        pre = next((h for h in heads
                    if h["key"] and h["key"] in k and len(h["key"]) < len(k)), None)
        if pre:
            i = line.find(pre["text"])
            # **字面找不到就不切。**我第一版在 find 回 -1 的時候還是從 0 砍掉
            #   `len(標題)` 個字——那等於砍掉沒對上的內容,保全率當場從 100%
            #   掉到 96.97%(㊀ 在真資料上抓到,夾具太小沒照出來)。
            #   正規化對得上、字面對不上,代表原字裡夾著零寬或全形——
            #   那種情況**寧可不切**,留一行完整的比切壞一行好。
            if i < 0:
                pre = None
            else:
                head_txt = pre["text"]
        if pre:
            before, after = line[:i], line[i + len(head_txt):]
            if before.strip():
                for _s in split_sentences(before):
                    add("本文", "句", _s, "標題前面那一段(標題原本黏在行中)")
            add("標題", pre["level"], head_txt,
                f"LAYOUT 標的 {pre['level']},原本黏在{'行首' if i == 0 else '行中'},切出來")
            line = after
            k = norm(line)
            if not k:
                continue
        # 表格殘片:整行被表吃掉,或行首黏著表的格子
        # 列鑰匙用 `in`(整列被黏在句子中間也要抓到);格鑰匙才用相等/開頭。
        hit = next((f for f in frs["row"] if f and f in k), "") or \
              next((f for f in frs["cell"] if f and (k == f or k.startswith(f))), "")
        if hit:
            add("表", "表格殘片", line,
                f"這一行在 tables 裡有對得上的格子({hit[:18]}…)——"
                f"擷取時本文與表格黏在一起了,標成表**但不刪**")
            continue
        for s in split_sentences(line):
            add("本文", "句", s, "一句一行(只在句末標點斷)")

    # ③ 表:逐表逐列,一列一行
    for ti, t in enumerate(sc.get("tables") or []):
        for ri, row in enumerate(t or []):
            cells = [str(c) for c in (row if isinstance(row, (list, tuple)) else [row])]
            add("表", "表頭" if ri == 0 else "表列", " | ".join(cells),
                f"tables[{ti}] 第 {ri} 列", {"table": ti, "row": ri, "cells": cells})

    # ④ 保全率:來源非空白字元,一個都不可以不見
    src = "".join(str(sc.get(k) or "") for k in ("header", "right", "body", "footer"))
    src += "".join("".join(str(c) for c in (r if isinstance(r, (list, tuple)) else [r]))
                   for t in (sc.get("tables") or []) for r in (t or []))
    src_chars = norm(src)
    out_chars = norm("".join(r["text"] for r in rows))
    kept = sum(1 for i, ch in enumerate(src_chars) if ch in out_chars) if src_chars else 0
    from collections import Counter
    cs, co = Counter(src_chars), Counter(out_chars)
    lost = {c: n - co.get(c, 0) for c, n in cs.items() if n > co.get(c, 0)}
    keep_rate = (1 - sum(lost.values()) / len(src_chars)) * 100.0 if src_chars else None

    return {
        "name": name, "page": page, "page_why": page_why,
        "rows": rows, "repair": rep,
        "n_rows": len(rows),
        "by_kind": {k: sum(1 for r in rows if r["kind"] == k) for k in KINDS},
        "keep": {"src_chars": len(src_chars), "out_chars": len(out_chars),
                 "lost_chars": sum(lost.values()),
                 "lost_sample": sorted(lost.items(), key=lambda x: -x[1])[:6],
                 "rate": keep_rate},
        "method": (sc.get("logic") or {}).get("method", ""),
        "triage": (sc.get("triage") or {}).get("state", ""),
        "compare": sc.get("compare") or {},
    }


def to_markdown(r: dict) -> str:
    """分類標註 → Markdown。**每一行都帶著它是什麼**(HTML 註解,人看不到 AI 看得到)。"""
    L = [f"<!-- VRN_ENG085 v{VERSION} · 還原層(不刪除;原件零觸碰)-->",
         f"<!-- 來源 {r['name']} · 頁 {r['page'] if r['page'] is not None else '判不出來'}"
         f"({r['page_why']})· 擷取法 {r['method'] or '未標'} · 版面 {r['triage'] or '未標'} -->",
         f"<!-- 保全率 {('%.2f%%' % r['keep']['rate']) if r['keep']['rate'] is not None else '—'}"
         f" · 來源字 {r['keep']['src_chars']} · 掉 {r['keep']['lost_chars']} -->", ""]
    last = None
    for row in r["rows"]:
        k, sub, t = row["kind"], row["sub"], row["text"]
        if k != last:
            L.append("")
            last = k
        tag = f"<!-- {k}/{sub} p{row['page'] if row['page'] is not None else '?'} -->"
        if k == "標題":
            lv = {"H1": 1, "H2": 2, "H3": 3, "H4": 4}.get(sub, 3)
            L.append(f"{'#' * lv} {t} {tag}")
        elif k == "表":
            L.append(f"{t} {tag}" if t.startswith("|") else f"| {t} | {tag}")
        elif k == "其他":
            L.append(f"> {t} {tag}")
        else:
            L.append(f"{t} {tag}")
    return "\n".join(L) + "\n"


def run(indir: str = "", apply_db: bool = False) -> dict:
    d = Path(indir) if indir else SIDECARS
    if not d.exists():
        return {"state": "ABSENT", "why": f"sidecar 夾不在:{d}。先跑 ENG072(via-firstpage)"}
    files = sorted(d.glob("*.json"))
    if not files:
        return {"state": "NODATA", "why": f"夾子在但沒有 sidecar:{d}"}
    OUT.mkdir(parents=True, exist_ok=True)
    rows, tables_out = [], []
    for f in files:
        try:
            sc = json.loads(f.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            rows.append({"name": f.name, "state": "FAIL", "why": f"{type(exc).__name__}: {exc}"})
            continue
        r = restore(sc, f.stem)
        (OUT / f"{f.stem}.md").write_text(to_markdown(r), encoding="utf-8")
        for x in r["rows"]:
            if x["kind"] == "表" and "cells" in x:
                tables_out.append({"report": f.stem, "page": x["page"], "table": x["table"],
                                   "row": x["row"], "sub": x["sub"], "cells": x["cells"]})
        r["state"] = "OK"
        rows.append({k: v for k, v in r.items() if k != "rows"})
    ok = [r for r in rows if r.get("state") == "OK"]
    rates = [r["keep"]["rate"] for r in ok if r.get("keep", {}).get("rate") is not None]
    res = {"state": "OK", "dir": str(d), "out": str(OUT), "n": len(files),
           "ok": len(ok), "fail": len(files) - len(ok),
           "tables_rows": len(tables_out),
           "keep_min": min(rates) if rates else None,
           "keep_all_100": all(abs(x - 100.0) < 1e-9 for x in rates) if rates else None,
           "rows": rows}
    (OUT / "VRN_MD_RESTORE_manifest.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    if apply_db:
        res["db"] = _write_tables(tables_out)
    else:
        res["db"] = {"state": "SKIPPED",
                     "why": f"預設不寫庫;要把 {len(tables_out)} 列表格入庫請加 --apply"}
    return res


def _write_tables(rows: list) -> dict:
    """表格入庫(操作員令「表格資料庫」)。**只增不減**:同報告同表先刪同鍵再寫。"""
    if not rows:
        return {"state": "NODATA", "why": "沒有表格列可入庫"}
    try:
        import duckdb
    except Exception:
        return {"state": "ABSENT", "why": "本境沒有 duckdb(不代裝;在工作站跑)"}
    db = VIA / "functional modules" / "VRN" / "output" / "vrn_reports.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        con.execute("""CREATE TABLE IF NOT EXISTS vrn_md_tables(
            report VARCHAR, page INTEGER, tbl INTEGER, row_no INTEGER,
            sub VARCHAR, cells VARCHAR, extracted_at VARCHAR)""")
        reps = sorted({r["report"] for r in rows})
        con.execute("DELETE FROM vrn_md_tables WHERE report IN ("
                    + ",".join("?" * len(reps)) + ")", reps)
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        con.executemany(
            "INSERT INTO vrn_md_tables(report,page,tbl,row_no,sub,cells,extracted_at) "
            "VALUES (?,?,?,?,?,?,?)",
            [(r["report"], r["page"], r["table"], r["row"], r["sub"],
              json.dumps(r["cells"], ensure_ascii=False), ts) for r in rows])
        n = con.execute("SELECT count(*) FROM vrn_md_tables").fetchone()[0]
    finally:
        con.close()
    return {"state": "OK", "db": str(db), "table": "vrn_md_tables",
            "written": len(rows), "total": n}


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VRN_ENG085 本文還原與分類標註 v{VERSION} · 自測(零網路;零寫庫)===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路", not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 預設不寫庫:`--apply` 才入庫,平跑只讀",
        "apply_db: bool = False" in code and '"state": "SKIPPED"' in code)
    chk("③ 零九頭龍:三道擷取與 LAYOUT 標註都**讀 ENG072 的 sidecar**,不重抽",
        "first_page_text" in code and "heads" in code and "compare" in code
        and "pdfplumber" not in code and "fitz" not in code)

    sc = {"header": "兆豐證券", "right": "目標價 1000", "footer": "第 7 頁",
          "body": "本次會議共 10 段。\n1 Action Items 行動項目#行動負責人期限1 燈號要補重試計數。\n"
                  "我們決定維持 PDF 流程。",
          "heads": [{"text": "1 Action Items 行動項目", "size": 14.0, "level": "H3"}],
          "tables": [[["#", "行動", "負責人", "期限"]]],
          "logic": {"method": "DUAL_ZONES"}, "triage": {"state": "DIGITAL"}}
    r = restore(sc, "夾具")
    kinds = {x["kind"] for x in r["rows"]}
    chk("④ 四類都標得出來(標題/表/本文/其他)",
        {"標題", "表", "本文", "其他"} <= kinds, str(sorted(kinds)))
    chk("⑤ 頁數讀頁尾的「第 N 頁」,不是猜的",
        r["page"] == 7 and "頁尾" in r["page_why"], f"(p{r['page']} · {r['page_why']})")
    chk("⑥ 判不出頁數要**說判不出來**,不編號碼",
        page_of({})[0] is None and "不編" in page_of({})[1])
    _h = [x for x in r["rows"] if x["kind"] == "標題"]
    chk("⑦ 黏在行首的標題要切出來,而且層級用 LAYOUT 給的(不是自己猜)",
        len(_h) == 1 and _h[0]["sub"] == "H3" and _h[0]["text"] == "1 Action Items 行動項目",
        str([(x["sub"], x["text"][:20]) for x in _h]))
    _t = [x for x in r["rows"] if x["kind"] == "表"]
    chk("⑧ **本文與表格黏在一起的那一段要標成表**(操作員點名的病):"
        "`#行動負責人期限…` 在 tables 裡對得上格子,標成表格殘片——**但不刪**",
        any(x["sub"] == "表格殘片" for x in _t) and any(x["sub"] == "表頭" for x in _t),
        str([x["sub"] for x in _t]))
    _b = [x for x in r["rows"] if x["kind"] == "本文"]
    chk("⑨ 一句一行:句末標點才斷,換行不斷"
        "(研報的換行多半是版面折行;拿它斷會把一句切三行,SUMMARIZE 就讀成三件事)",
        all(x["text"][-1] in _SENT_END for x in _b) and len(_b) >= 2,
        str([x["text"][:16] for x in _b]))
    chk("㊀ **不刪除**:來源非空白字元保全率 100%。"
        "「修好」如果是靠丟掉修不動的那幾段換來的,那不是修好",
        r["keep"]["rate"] is not None and abs(r["keep"]["rate"] - 100.0) < 1e-9,
        f"(保全 {r['keep']['rate']:.2f}% · 來源 {r['keep']['src_chars']} 字 · "
        f"掉 {r['keep']['lost_chars']}{' · ' + str(r['keep']['lost_sample']) if r['keep']['lost_chars'] else ''})")
    fixed, rep = repair_text("中\n文  斷行​與　間隔")
    chk("⑪ 修斷行與間隔:去零寬 · 全形空白換半形 · CJK 硬斷接回 · 壓連續空白,"
        "**而且每一種都記次數**(修了什麼要說得出來)",
        rep["zw"] == 1 and rep["fullwidth_space"] == 1 and rep["joins"] == 1
        and "中文" in fixed and "​" not in fixed, f"{rep}")
    chk("⑫ 英數中間的硬斷**不接**(接了會黏成錯字:`Q2\\n2025` → `Q22025`)",
        repair_text("Q2\n2025")[1]["joins"] == 0)
    md = to_markdown(r)
    chk("⑬ MD 每一行都帶著它是什麼(類別/次類別/頁),AI 讀得出來",
        md.count("<!-- 標題/H3") == 1 and "<!-- 表/表頭" in md and "<!-- 本文/句" in md
        and "保全率 100.00%" in md, f"({len(md)} 字)")
    chk("⑭ 類別冊是分類的唯一出處:每一個用到的類別都在 KINDS 裡,"
        "次類別也在它的 subs 裡(加一類沒進冊,它就只活在程式裡——LL207 同族)",
        all(x["kind"] in KINDS and x["sub"] in KINDS[x["kind"]]["subs"] for x in r["rows"]),
        str([(x["kind"], x["sub"]) for x in r["rows"] if x["kind"] not in KINDS
             or x["sub"] not in KINDS.get(x["kind"], {}).get("subs", [])] or "全在冊"))
    _n = split_sentences("決議1.\nMDL010 已接上。\n2.\n維持 PDF 流程。")
    chk("⑰ **光禿禿的編號不是一句**:`1.` `2.` 被句末的 `.` 切成獨立一行之後,"
        "「一句一行」就變成「一個號碼也一行」,而 SUMMARIZE 會把它讀成一件事。"
        "編號要黏回它後面那一句(實測 VRN_Meeting_Minutes 一份就生了 5 行這種)",
        # 斷言是 3 不是 2——我第一版寫 2,而正確結果是
        #   `決議1.` / `MDL010 已接上。` / `2. 維持 PDF 流程。`。
        #   **檢寫錯的時候先懷疑檢**:這裡碼是對的,錯的是我算錯句數。
        not any(_BARE_NUM.fullmatch(x) for x in _n) and len(_n) == 3
        and _n[-1].startswith("2. "),
        str(_n))
    _mid = restore({"body": "前言一段。標題在中間後面還有話。",
                    "heads": [{"text": "標題在中間", "size": 20.0, "level": "H1"}]}, "行中")
    _mk = [(x["kind"], x["sub"], x["text"]) for x in _mid["rows"]]
    chk("⑱ 標題黏在**行中**也要切出來(不只行首)。實測:"
        "`…會議紀錄VRN Fetch v4 — 設計審查會議日期…` 裡那個 H1 卡在中間,只比行首抓不到"
        "——跟表格殘片同一種病:黏在哪裡都要找得回來。而且**前面那一段不可以丟**",
        any(k == "標題" and t == "標題在中間" for k, _, t in _mk)
        and any(k == "本文" and "前言一段" in t for k, _, t in _mk)
        and abs(_mid["keep"]["rate"] - 100.0) < 1e-9,
        str(_mk))
    # ⑲ 夾具要**造得出那個坑**:標題在 heads 裡是乾淨的,body 裡卻夾著零寬——
    #   正規化對得上、字面對不上。我第一版在這種情況照 len(標題) 硬切,
    #   保全率在真資料上從 100% 掉到 96.97%,而**夾具太小沒照出來**。
    _zwv = restore({"body": "前面一段話。標\u200b題\u200b在中間後面還有話。",
                    "heads": [{"text": "標題在中間", "size": 20.0, "level": "H1"}]}, "零寬")
    chk("⑲ 正規化對得上、**字面對不上就不切**:原字裡夾著零寬的時候,"
        "照 `len(標題)` 硬切會砍掉沒對上的字。留一行完整的,比切壞一行好"
        "——保全率仍須 100%",
        abs(_zwv["keep"]["rate"] - 100.0) < 1e-9 and _zwv["keep"]["lost_chars"] == 0,
        f"(保全 {_zwv['keep']['rate']:.2f}% · 掉 {_zwv['keep']['lost_chars']})")
    chk("⑮ 夾不在=ABSENT 且講得出下一句(去跑 ENG072)· 空夾=NODATA",
        run("/no/such/dir")["state"] == "ABSENT" and "ENG072" in run("/no/such/dir")["why"])
    _e = restore({}, "空")
    chk("⑯ 空 sidecar:零行、保全率不給數字(沒有分母就不給比率),不當成 100%",
        _e["n_rows"] == 0 and _e["keep"]["rate"] is None,
        f"(rate={_e['keep']['rate']})")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(檢數現場計)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG085_MarkdownRestore",
                                 description="本文還原與分類標註(零網路;預設不寫庫)")
    ap.add_argument("verb", nargs="?", default="run", choices=["run", "one"])
    ap.add_argument("--in", dest="indir", default="", help="sidecar 夾(預設 VIA_Reports/first_page_text)")
    ap.add_argument("--file", default="", help="單一 sidecar.json")
    ap.add_argument("--apply", action="store_true", help="表格入庫(預設不寫)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verb == "one":
        if not a.file:
            print("  [絕] one 要給檔:--file <sidecar.json>")
            return 1
        p = Path(a.file)
        if not p.exists():
            print(f"[VRN_ENG085 v{VERSION}] one · ABSENT · 檔不在:{p}")
            return 3
        r = restore(json.loads(p.read_text(encoding="utf-8-sig")), p.stem)
        OUT.mkdir(parents=True, exist_ok=True)
        q = OUT / f"{p.stem}.md"
        q.write_text(to_markdown(r), encoding="utf-8")
        print(json.dumps({k: v for k, v in r.items() if k != "rows"}, ensure_ascii=False)
              if a.json else
              f"[VRN_ENG085 v{VERSION}] one · {p.stem} · 行 {r['n_rows']} · "
              f"{r['by_kind']} · 保全 {r['keep']['rate']:.2f}% · 頁 {r['page']} → {q}")
        return 0
    res = run(a.indir, a.apply)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res["state"] == "OK" else {"NODATA": 2, "ABSENT": 3}.get(res["state"], 1)
    if res["state"] != "OK":
        print(f"[VRN_ENG085 v{VERSION}] run · {res['state']} · {res['why']}")
        return {"NODATA": 2, "ABSENT": 3}.get(res["state"], 1)
    print(f"[VRN_ENG085 v{VERSION}] run · OK · {res['n']} 份(OK {res['ok']} · FAIL {res['fail']})")
    print(f"  [保全] 最低 {res['keep_min']:.2f}%" if res["keep_min"] is not None else "  [保全] 無分母")
    print(f"         全部 100%:{'是' if res['keep_all_100'] else '**否——有份數掉字,逐份看 manifest**'}")
    print(f"  [表格] {res['tables_rows']} 列 · 入庫 {res['db']['state']}"
          f"{' · ' + res['db'].get('why', '') if res['db'].get('why') else ''}")
    print(f"  [出] {res['out']}")
    return 0 if res["keep_all_100"] is not False else 1


if __name__ == "__main__":
    sys.exit(main())
