# -*- coding: utf-8 -*-
"""
VIA_VRN_FirstPageEngine  v0102
ALL-IN-ONE engine consolidating the VRN first-page extraction & cross-validation logic.

Modules (single file, one entry point `FirstPageEngine.run`):
  1 SSOT loader          - load _RAW_REGEX/_RAW_SYNONYMS from SSOT .py, else locked fallback
  2 TickerFilename       - tokenize, 4-digit ticker / 6-8 digit date, disambiguation ladder,
                           year-band reclaim, tri-code cross-check, email->analyst/broker
  3 Layout               - font-hierarchy (MAIN_TITLE..FOOTER), element_type, boilerplate,
                           company-name (largest+bold), sentence linking (break at period)
  4 TableGeometry        - reconstruct hidden-gridline tables via x/y clustering, period headers
  5 NLPRepair            - real via_nlp bridge (v1.8.0 TextProcessor) + heuristic fallback
  6 FinancialValidation  - Add/Sub tolerance layering, Division two-stage, Historical YoY
  7 PriceAdjustment      - adjusted-price consistency + TP sanity gate
  8 CrossValidation      - filename <-> text <-> table <-> financials
Governance: append-only; raw + repaired coexist; TABLE/FIGURE never enter NLP.

====================================================================
v0101 → v0102(批426):九項升級,每一項都由本會期的實跑證據帶出來
====================================================================
【崩潰修】
 A. FinancialValidation.multiply / add_sub 遇 None 會 TypeError 當場崩——
    而 None 正是抽取器找不到數字時的**常態回傳**。實測:
      multiply(None,10,5)  → TypeError: unsupported operand type(s) for -: 'NoneType' and 'int'
      add_sub(None,[1,2])  → TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
    → 全面 None-safe,無值一律 N/A(不猜、不當 0)。

【死掛鉤修】
 B. NLPRepair 的外接掛鉤呼叫 self.ext.repaired(raw),但 via_nlp 的 TextProcessor
    **沒有 repaired() 這個方法**(它叫 repair(),且回 dict 不回 str)。
    後果:掛鉤永遠 AttributeError → 靜默退回啟發式後備,外接引擎等於沒接。
    這是「捕捉到卻不顯示」的變體:失敗被 except 吃掉,對外看不出來。
    → 改用真實 API(repair/normalize/split_sentences),並新增 route() 讓呼叫端
      看得見這一次走的是 HUB / DIRECT / HEURISTIC 哪一條。
 C. 新增 SUP_MDL744_NLPApplicationHub 自動掛載(尾版律,現為 v1.8.0/39 模組),
    不必由呼叫端自己 import。橋缺席=誠實退後備並留因由。

【檔名拆解】(操作員批420 規格)
 D. 民國年七碼日期:1141202 → 2025-12-02(v0101 回 None;操作員真檔名正在用)。
 E. 名字-KY 也是公司名稱:慧洋-KY 不再被切成「慧洋」+「KY」。

【抽取覆蓋】
 F. 目標價 regex 加寬到 Target price / Price Target / PT / 目標價(v0101 只認
    NT$ 與 目標價,GS/MS 的 "Price Target 650"、"PT 78" 全部漏抽)。

【判定誠實】
 G. report_kind 分類(個股/產業/大盤晨報/海外/研討會)+ kind_expects_ticker():
    非個股報告本來就沒有代號與目標價,不得因此被判失敗(批418 的 DONE_NS 律)。
 H. TP 合理性閘(TP/價 落在 0.2–5.0 之外=TP_SUSPECT),且 upside 只接受
    **已復權**價:拿原始 close 算復權升幅一律拒算(批425:引擎誠實拒絕頂替是對的)。
 I. 總判 aggregate_verdict() 必須讀到**所有**子閘(含 TP 合理性)——
    批422 的假綠就是上游閘抓到了、下游判定不讀它。

【其他】
 J. CLI 真的接線(--file/--dir/--ssot/--json/--selftest),且自測用攔真實呼叫證明
    旗標有傳到;批425 一連四例都是「參數在、線沒接」。
 K. TableGeometry 最近群聚查找由 O(n·m) min() 改 bisect(大頁面明顯有感)。
 L. 移除死碼(v0101 line 168 的 core lambda 定義後從未使用)。
 M. --selftest 零觸碰任何正本(批424:自測寫正本冊,十餘跑就把 66 筆灌成 78 筆)。

用法:
  python3 VIA_VRN_FirstPageEngine_v0102.py --selftest
  python3 VIA_VRN_FirstPageEngine_v0102.py --file <報告.pdf> [--ssot <SSOT.py>] [--json]
  python3 VIA_VRN_FirstPageEngine_v0102.py --dir <報告夾> [--json]
"""
import bisect
import json
import os
import re
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ENGINE_NAME = "VIA_VRN_FirstPageEngine"
ENGINE_VERSION = "v0102"

# =====================================================================
# 1 · SSOT LOADER
# =====================================================================
_LOCK = {
    "TW_STOCK_CODE_4DIGIT": r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
    "TW_YFINANCE_TICKER":   r"([1-9]\d{3})\.(TW|TWO)",
    "TW_BLOOMBERG_TICKER":  r"([1-9]\d{3})\s+TT",
}


def load_ssot_blocks(ssot_path):
    blocks = {}
    if not (ssot_path and os.path.exists(ssot_path)):
        return blocks
    txt = open(ssot_path, encoding="utf-8", errors="replace").read()
    for var in ("_RAW_REGEX", "_RAW_LISTS", "_RAW_SYNONYMS"):
        m = re.search(var + r"\s*[:=][^=]*=?\s*json\.loads\(r'''(.*?)'''\)", txt, re.S)
        if m:
            try:
                blocks[var] = json.loads(m.group(1))
            except Exception:
                blocks[var] = []
    return blocks


# =====================================================================
# 1b · via_nlp 橋(批426-C):自動掛 SUP_MDL744_NLPApplicationHub 尾版
# ---------------------------------------------------------------------
# v0101 要呼叫端自己把 engine 傳進來,實務上沒人傳=外接引擎形同虛設。
# 這裡自己找橋:supportive modules/70_VRN_Rules/SUP_MDL744_*.py(尾版律 glob)。
# 橋缺席不是錯誤,是**誠實降級**——留因由,由 route() 對外交代。
# =====================================================================
def _find_via_root(start: Path) -> Path | None:
    p = start.resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return None


def mount_nlp_hub(explicit_dir=None):
    """回 (hub_module | None, why)。零網路;失敗只降級不拋。"""
    root = Path(explicit_dir) if explicit_dir else _find_via_root(Path(__file__).parent)
    if root is None:
        return None, "找不到 VIA 根(需同時有 supportive modules/ 與 functional modules/)"
    d = root / "supportive modules" / "70_VRN_Rules"
    hits = sorted(d.glob("SUP_MDL744_NLPApplicationHub_v*.py")) if d.is_dir() else []
    if not hits:
        return None, f"SUP_MDL744 缺檔({d})"
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("via_nlp_hub_fpe", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod          # 延後註解要靠這行
        spec.loader.exec_module(mod)
        st = mod.mount()
        if st.get("state") in ("ABSENT", "FAILED"):
            return None, f"橋在位但掛載 {st.get('state')}:{st.get('why', '')}"
        return mod, ""
    except Exception as exc:
        return None, f"橋載入失敗 {type(exc).__name__}:{str(exc)[:90]}"


# =====================================================================
# 2 · TICKER / FILENAME
# =====================================================================
class TickerFilename:
    _PUN = ("　 \t\r\n．。,、;:()()【】〔〕「」『』《》〈〉[]{}<>"
            "·•‧//\\|—–-_~＿＝=＋+＊*＆&%%#＃@＠!!??＂\"＇'｀`^$＄.,;:!?\"'()[]{}<>")
    _SEP = re.compile("[" + re.escape(_PUN) + "]+")
    _SECTOR_KW = ("產業", "類股", "族群", "策略", "展望", "sector", "industry")
    # 批426-G(承 批418):報告型別冊。非個股本來就沒有代號與目標價,
    # 不得因此被判失敗——這是操作員 63 份真報告裡 19 份的常態。
    _KIND_KW = (
        ("大盤晨報", ("晨報", "晨會", "盤勢", "盤前", "盤後", "每日觀察",
                      "morning", "daily wrap", "market wrap")),
        ("研討會",   ("研討會", "法說", "論壇", "conference", "summit", "expert call")),
        ("海外",     ("海外", "美股", "陸股", "港股", "全球", "global", "offshore")),
        ("產業",     _SECTOR_KW),
    )
    # 批426-E:名字-KY 也是公司名稱(慧洋-KY / 貿聯-KY / AMAX-KY)
    _KY = re.compile(r"([一-鿿A-Za-z0-9]+)\s*-\s*KY\b", re.I)

    def __init__(self, ssot_path=None, official_set=None):
        b = load_ssot_blocks(ssot_path)
        rules = {r.get("rule_name") or r.get("name"): r for r in b.get("_RAW_REGEX", [])}

        def pat(name):
            r = rules.get(name)
            return r["pattern"] if (r and r.get("pattern")) else _LOCK[name]

        self.rx_bare_strict = re.compile(r"(?<!\d)" + pat("TW_STOCK_CODE_4DIGIT") + r"(?!\d)")
        self.rx_bare_any = re.compile(r"(?<!\d)([1-9]\d{3})(?!\d)")
        self.rx_yf = re.compile(r"(?<!\d)" + pat("TW_YFINANCE_TICKER") + r"\b", re.I)
        self.rx_bb = re.compile(r"(?<!\d)" + pat("TW_BLOOMBERG_TICKER") + r"\b", re.I)
        self.alias2tk, self.tk2name = {}, {}
        for s in b.get("_RAW_SYNONYMS", []):
            canon = s.get("canonical", "")
            mt = re.match(r"(\d{4})", canon)
            if not mt:
                continue
            tk = mt.group(1)
            names = [a for a in s.get("aliases", [])
                     if not re.match(r"^\d{4}(\s+TT|\.TW[O]?)?$", a)]
            cn = next((a for a in names if re.search(r"[一-鿿]", a)),
                      (names[0] if names else ""))
            self.tk2name[tk] = cn
            for a in s.get("aliases", []) + [canon]:
                self.alias2tk[a] = tk
        self.official_set = set(official_set) if official_set else None

    @staticmethod
    def is_valid_bare(t):
        return bool(re.fullmatch(r"[1-9]\d{3}", t or ""))

    @staticmethod
    def numtoken_to_date(tok):
        """8 碼西元 / 7 碼民國 / 6 碼西元兩位年 → ISO 日期。
        批426-D:v0101 缺 7 碼民國(1141202),而操作員真檔名正在用
        (華南投顧-2637-慧洋-KY-1141202)。民國年上限 200 以免把 4 碼代號誤讀。"""
        if not (tok and tok.isdigit()):
            return None
        if len(tok) == 8:
            y, mo, d = tok[:4], tok[4:6], tok[6:8]
        elif len(tok) == 7:                       # 民國:114 1202 → 2025-12-02
            roc = int(tok[:3])
            if not (1 <= roc <= 200):
                return None
            y, mo, d = str(roc + 1911), tok[3:5], tok[5:7]
        elif len(tok) == 6:
            y, mo, d = "20" + tok[:2], tok[2:4], tok[4:6]
        else:
            return None
        try:
            iy, im, idd = int(y), int(mo), int(d)
        except ValueError:
            return None
        if 1990 <= iy <= 2099 and 1 <= im <= 12 and 1 <= idd <= 31:
            return "%04d-%02d-%02d" % (iy, im, idd)
        return None

    @staticmethod
    def _cls(ch):
        if ch.isdigit():
            return "DIGIT"
        o = ord(ch)
        if (0x4E00 <= o <= 0x9FFF) or (0x3400 <= o <= 0x4DBF) or (0xF900 <= o <= 0xFAFF):
            return "CJK"
        if "A" <= ch.upper() <= "Z":
            return "LATIN"
        return "OTHER"

    def tokenize(self, name):
        stem = re.sub(r"\.(pdf|docx?|pptx?|png|jpe?g|tiff?|webp|heic)$", "",
                      name or "", flags=re.I)
        stem = unicodedata.normalize("NFKC", stem)
        stem = self._SEP.sub(" ", stem)
        out = []
        for chunk in stem.split():
            cur, ck = "", None
            for ch in chunk:
                k = self._cls(ch)
                if k == "OTHER":
                    if cur:
                        out.append((cur, ck))
                    cur, ck = "", None
                    continue
                if ck is None or k == ck:
                    cur += ch
                    ck = k
                else:
                    out.append((cur, ck))
                    cur, ck = ch, k
            if cur:
                out.append((cur, ck))
        return out

    def classify_kind(self, name, has_ticker):
        """批426-G:報告型別。回 (kind, reason)。個股=有代號且不含非個股關鍵詞。"""
        low = unicodedata.normalize("NFKC", name or "").lower()
        for kind, kws in self._KIND_KW:
            hit = next((k for k in kws if k.lower() in low), None)
            if hit:
                return kind, f"檔名含「{hit}」"
        return ("個股", "有四碼代號") if has_ticker else ("未分類", "無代號且無型別關鍵詞")

    @staticmethod
    def kind_expects_ticker(kind):
        """非個股不該被要求要有代號/目標價(批418 DONE_NS 律)。"""
        return kind == "個股"

    def parse_filename(self, name):
        res = {"tickers": [], "dates": [], "cjk": [], "latin": [],
               "names": [], "kind": "", "kind_reason": ""}
        # 批426-E:先把 X-KY 整體收成公司名,避免被分隔符切斷
        for m in self._KY.finditer(unicodedata.normalize("NFKC", name or "")):
            res["names"].append(m.group(0).replace(" ", ""))
        for tok, kind in self.tokenize(name):
            if kind == "DIGIT":
                if len(tok) == 4 and self.is_valid_bare(tok):
                    res["tickers"].append(tok)
                else:
                    d = self.numtoken_to_date(tok)
                    if d:
                        res["dates"].append(d)
            elif kind == "CJK":
                res["cjk"].append(tok)
            elif kind == "LATIN":
                res["latin"].append(tok)
        res["kind"], res["kind_reason"] = self.classify_kind(name, bool(res["tickers"]))
        return res

    @staticmethod
    def parse_email(text):
        return [{"analyst_id": m.group(1), "broker_domain": m.group(2)}
                for m in re.finditer(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)", text or "")]

    def resolve(self, filename, title="", body=""):
        fn, title, body = filename or "", title or "", body or ""

        def suf(src):
            m = self.rx_yf.search(src) or self.rx_bb.search(src)
            return m.group(1) if m else None

        tk = suf(fn)
        if tk:
            return self._ok(tk, "FILE_SUFFIX")
        m = self.rx_bare_strict.search(fn)
        if m:
            return self._ok(m.group(1), "FILE_BARE")
        if any(k in fn for k in self._SECTOR_KW):
            return self._sec("SECTOR_FILE")
        tk = suf(title)
        if tk:
            return self._ok(tk, "TITLE_SUFFIX")
        for a, t in self.alias2tk.items():
            if a and len(a) >= 2 and re.search(r"[一-鿿A-Za-z]", a) and a in title:
                return self._ok(t, "TITLE_SYNONYM")
        tk = suf(body)
        if tk:
            return self._ok(tk, "BODY_SUFFIX")
        if any(k in title for k in self._SECTOR_KW):
            return self._sec("SECTOR_TITLE")
        for src, why in ((fn, "FILE"), (title, "TITLE")):
            m = self.rx_bare_any.search(src)
            if m:
                cand = m.group(1)
                if 2021 <= int(cand) <= 2030:
                    if ((self.official_set and cand in self.official_set)
                            or (cand == suf(fn + " " + title + " " + body))):
                        return self._ok(cand, "RECLAIM_" + why)
                else:
                    return self._ok(cand, why + "_BARE_ANY")
        m = self.rx_bare_strict.search(body[:600])
        if m:
            return self._ok(m.group(1), "BODY_BARE")
        return self._sec("NONE")

    def _ok(self, tk, method):
        return {"ticker": tk, "name": self.tk2name.get(tk, ""),
                "method": method, "is_sector": False}

    def _sec(self, method):
        return {"ticker": "", "name": "", "method": method, "is_sector": True}

    def cross_check(self, filename_ticker, raw=None, yf=None, bbg=None):
        # 批426-L:v0101 這裡有個 core lambda 定義後從未使用(死碼),已移除。
        res = {"filename_ticker": filename_ticker, "checks": [], "verdict": "PASS"}

        def core4(c):
            m = re.match(r"([1-9]\d{3})", c or "")
            return m.group(1) if m else None

        def add(label, v, ok, msg):
            res["checks"].append({"code": label, "value": v, "ok": ok, "msg": msg})
            if not ok:
                res["verdict"] = "FAIL"

        if raw is not None:
            add("TW_TICKER", raw,
                self.is_valid_bare(raw) and core4(raw) == filename_ticker, "raw core4")
        if yf is not None:
            add("TW_YFINANCE", yf,
                bool(re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", yf, re.I))
                and core4(yf) == filename_ticker, "yf")
        if bbg is not None:
            add("TW_BLOOMBERG", bbg,
                bool(re.fullmatch(r"[1-9]\d{3}\s+TT", bbg, re.I))
                and core4(bbg) == filename_ticker, "bbg")
        return res


# =====================================================================
# 3 · LAYOUT  (font hierarchy + element_type + sentence linking)
# =====================================================================
class Layout:
    _BOILER = ("投顧", "研究部", "免責", "disclosure", "bloomberg", "reuters",
               "not investment advice", "for information only")

    def __init__(self, page_height=842.0):
        self.H = page_height

    @staticmethod
    def _lines_from_chars(chars):
        """group chars into text lines by rounded 'top', ordered top->bottom, left->right."""
        rows = defaultdict(list)
        for c in chars:
            rows[round(c["top"] / 3.0)].append(c)
        lines = []
        for key in sorted(rows):
            cs = sorted(rows[key], key=lambda c: c["x0"])
            text = "".join(c["text"] for c in cs)
            size = statistics.median([c["size"] for c in cs]) if cs else 0
            bold = sum(1 for c in cs if "bold" in (c.get("fontname") or "").lower()) > len(cs) / 2
            top = min(c["top"] for c in cs)
            x0 = min(c["x0"] for c in cs)
            lines.append({"text": text, "size": round(size, 2), "bold": bold,
                          "top": top, "x0": x0, "chars": cs})
        return lines

    def classify(self, chars):
        lines = self._lines_from_chars(chars)
        if not lines:
            return {"lines": [], "body_size": 0, "company_name": "",
                    "main_text": "", "footer": ""}
        sizes = [l["size"] for l in lines]
        body_size = statistics.median(sizes)
        for l in lines:
            r = l["size"] / body_size if body_size else 1
            low = l["text"].lower()
            if l["top"] >= self.H * 0.88 or any(b in low for b in self._BOILER):
                l["level"] = "FOOTER"
            elif r >= 1.8:
                l["level"] = "MAIN_TITLE"
            elif r >= 1.4:
                l["level"] = "HEADLINE"
            elif r >= 1.15:
                l["level"] = "H2"
            elif r <= 0.8:
                l["level"] = "FOOTER"
            else:
                l["level"] = "BODY"
        cands = [l for l in lines if l["level"] in ("MAIN_TITLE", "HEADLINE")]
        company = ""
        if cands:
            cands.sort(key=lambda l: (-l["size"], not l["bold"], l["top"]))
            company = cands[0]["text"].strip()
        body_lines = [l["text"] for l in lines if l["level"] == "BODY"]
        main_text = self._link_sentences(body_lines)
        footer = " ".join(l["text"] for l in lines if l["level"] == "FOOTER")
        return {"lines": lines, "body_size": body_size, "company_name": company,
                "main_text": main_text, "footer": footer}

    @staticmethod
    def _link_sentences(body_lines):
        """rightward+downward link; break only at sentence-final punctuation."""
        buf, out = "", []
        for ln in body_lines:
            ln = ln.strip()
            if not ln:
                continue
            buf = (buf + " " + ln).strip() if buf else ln
            while True:
                m = re.search(r"[。.!?!?]", buf)
                if not m:
                    break
                cut = m.end()
                out.append(buf[:cut].strip())
                buf = buf[cut:].strip()
        if buf:
            out.append(buf)
        return " ".join(out)


# =====================================================================
# 4 · TABLE GEOMETRY (hidden gridline reconstruction)
# =====================================================================
class TableGeometry:
    @staticmethod
    def _cluster(vals, gap):
        vals = sorted(vals)
        if not vals:
            return []
        groups = [[vals[0]]]
        for v in vals[1:]:
            if v - groups[-1][-1] <= gap:
                groups[-1].append(v)
            else:
                groups.append([v])
        return [statistics.mean(g) for g in groups]

    @staticmethod
    def _nearest(centers, v):
        """批426-K:v0101 用 min(range(n), key=...) 逐格線性掃,
        每個字元 O(欄數+列數);一頁上萬字元時明顯拖慢。
        centers 本來就是排序好的 → 改二分,O(log n)。答案完全相同。"""
        if not centers:
            return 0
        i = bisect.bisect_left(centers, v)
        if i == 0:
            return 0
        if i >= len(centers):
            return len(centers) - 1
        return i if (centers[i] - v) < (v - centers[i - 1]) else i - 1

    def reconstruct(self, chars, col_gap=18.0, row_gap=6.0):
        """cluster chars by x (columns) and y (rows) -> 2D grid of cell text."""
        if not chars:
            return {"rows": [], "n_cols": 0}
        row_centers = self._cluster([c["top"] for c in chars], row_gap)
        col_centers = self._cluster([c["x0"] for c in chars], col_gap)
        grid = [["" for _ in col_centers] for _ in row_centers]
        by_row = defaultdict(list)
        for c in chars:
            by_row[self._nearest(row_centers, c["top"])].append(c)
        for ri, cs in by_row.items():
            cs.sort(key=lambda c: c["x0"])
            for c in cs:
                grid[ri][self._nearest(col_centers, c["x0"])] += c["text"]
        rows = [[cell.strip() for cell in r] for r in grid]
        return {"rows": rows, "n_cols": len(col_centers),
                "col_centers": col_centers, "row_centers": row_centers}

    @staticmethod
    def restore_period_header(cells):
        """期間表頭正規化。批426b:改吃 parse_period()——v0101 只認 12/24A 與 2023
        兩型,操作員規格要的 FY-23 / F23 / 20230102 / 230102 / 民國 全部漏。
        回鍵沿用 raw/period/kind 以維持相容,另加 basis(A實際/E預估/F預測)與 roc。"""
        out = []
        for c in cells:
            r = parse_period(c)
            out.append({"raw": r["raw"], "period": r["period"], "kind": r["kind"],
                        "basis": r["basis"], "roc": r["roc"]})
        return out


# =====================================================================
# 5 · NLP REPAIR  (批426-B/C:真 API + 自動掛橋 + 走哪條看得見)
# =====================================================================
class NLPRepair:
    """v0101 的掛鉤呼叫 self.ext.repaired(raw),但 via_nlp 的 TextProcessor
    **沒有 repaired()**(它是 repair(),而且回 dict 不回 str)。
    後果:每次都 AttributeError → 被 except 吃掉 → 靜默退啟發式,
    外接引擎等於沒接,而且對外看不出來(「捕捉到卻不顯示」)。
    v0102:用真 API,而且把這一次走的路徑對外交代。"""

    def __init__(self, external_engine=None, auto_hub=True, via_root=None):
        self.ext = external_engine
        self._route = "HEURISTIC"
        self._why = ""
        self.hub = None
        if self.ext is not None:
            self._route = "DIRECT"
        elif auto_hub:
            hub, why = mount_nlp_hub(via_root)
            self.hub = hub
            self._why = why
            if hub is not None:
                tp = hub.text_processor()
                if tp is not None:
                    self.ext = tp
                    self._route = "HUB"
                else:
                    self._why = self._why or "橋在位但 text_processor() 回 None"

    def route(self) -> dict:
        """走哪一條、為何沒走到更好的那條——都要說得出來。"""
        st = self.hub.mount() if self.hub is not None else {}
        return {"route": self._route, "why": self._why,
                "hub_dir": st.get("dir_name", ""), "hub_state": st.get("state", "")}

    def repair_text(self, raw):
        if self.ext is not None:
            try:
                r = self.ext.repair(raw)              # 真 API:回 dict
                if isinstance(r, dict):
                    for k in ("repaired", "text", "output", "result"):
                        if isinstance(r.get(k), str) and r[k].strip():
                            return r[k]
                elif isinstance(r, str) and r.strip():
                    return r
            except Exception as exc:
                self._why = f"repair() 例外 {type(exc).__name__}(已退後備)"
            try:
                n = self.ext.normalize(raw)           # 次選:正規化也算修復
                if isinstance(n, str) and n.strip():
                    return n
            except Exception:
                pass
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", raw or "")
        return re.sub(r"\s+", " ", t).strip()

    def split_sentences(self, text):
        if self.ext is not None:
            try:
                s = self.ext.split_sentences(text)
                if isinstance(s, list) and s:
                    return s
            except Exception as exc:
                self._why = f"split_sentences() 例外 {type(exc).__name__}(已退後備)"
        parts = re.split(r"(?<=[。.!?!?])\s+", text or "")
        return [p.strip() for p in parts if p.strip()]


# =====================================================================
# 5b · 正典驗證橋(批426 新增;操作員令「整合如果關聯 驗證法」)
# ---------------------------------------------------------------------
# 操作員另附兩支同族正典,關聯明確:
#   VRN_MDL008_CrossValidator  → 單位正規化 to_million/std_val、
#                                 容差分層 tolerance(依量級,非相對誤差)、
#                                 compare_one/classify_mismatch/fallback_resolve
#   VRN_TW02_ReportParser      → CrossValidator.validate 三源交叉核對
#                                 (Filename ↔ 第一頁 ↔ 財報頁)、is_valid_ticker
# 本檔 v0101 的 _band() 其實是 MDL008 tolerance() 的**粗糙複製品**,而且模型不同:
#   MDL008 = 依金額量級給絕對容差(百萬元;>=1000 大、>=100 中、其餘小)
#   v0101  = 一律相對誤差 1%/5%/10%
# 零九頭龍:不再寫第三份,改**綁正典**;正典缺席才退本地 band,並且說得出退了。
# =====================================================================
class XValBridge:
    """掛載 MDL008 / TW02 正典。缺席=誠實降級,絕不假裝有。"""

    def __init__(self, via_root=None, mdl008_path=None, tw02_path=None):
        self.mdl008, self.tw02 = None, None
        self.why = {"mdl008": "", "tw02": ""}
        root = Path(via_root) if via_root else _find_via_root(Path(__file__).parent)
        for key, explicit, globs in (
                ("mdl008", mdl008_path, ("VRN_MDL008_CrossValidator*.py",)),
                ("tw02", tw02_path, ("VRN_TW02_ReportParser*.py",))):
            hit = Path(explicit) if explicit else None
            if hit is None and root is not None:
                for g in globs:
                    found = sorted((root / "functional modules" / "VRN").glob(g))
                    if found:
                        hit = found[-1]
                        break
            if hit is None or not Path(hit).exists():
                self.why[key] = f"{globs[0]} 未尋獲(functional modules/VRN/)"
                continue
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"via_{key}_fpe", hit)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)
                setattr(self, key, mod)
            except Exception as exc:
                self.why[key] = f"載入失敗 {type(exc).__name__}:{str(exc)[:80]}"

    def status(self):
        return {"mdl008": self.mdl008 is not None, "tw02": self.tw02 is not None,
                "why": {k: v for k, v in self.why.items() if v}}

    # ---- MDL008:單位正規化 + 量級容差 ----
    def std_val(self, value, unit="million"):
        if self.mdl008 is not None:
            try:
                return self.mdl008.std_val(value, unit)
            except Exception:
                pass
        try:
            return float(str(value).replace(",", "").replace(",", "").strip())
        except Exception:
            return None

    def tolerance(self, v):
        """回 (絕對容差, 來源)。正典缺席=None 表示「用相對誤差 band」。"""
        if self.mdl008 is not None:
            try:
                return self.mdl008.tolerance(v), "MDL008"
            except Exception:
                pass
        return None, "LOCAL_BAND"

    # ---- TW02:三源交叉核對 ----
    def three_way(self, filename_data, first_page_data, financial_page_data):
        if self.tw02 is None:
            return None
        try:
            return self.tw02.CrossValidator.validate(
                filename_data, first_page_data, financial_page_data)
        except Exception as exc:
            self.why["tw02"] = f"validate 例外 {type(exc).__name__}:{str(exc)[:80]}"
            return None

    def is_valid_ticker(self, code):
        if self.tw02 is not None:
            try:
                return bool(self.tw02.is_valid_ticker(code))
            except Exception:
                pass
        return bool(re.fullmatch(r"[1-9]\d{3}", code or "")) and not (2000 <= int(code or 0) <= 2030)


# =====================================================================
# 6 · FINANCIAL VALIDATION  (批426-A None-safe;綁 MDL008 容差)
# =====================================================================
class FinancialValidation:
    def __init__(self, xval: "XValBridge | None" = None):
        self.xv = xval

    @staticmethod
    def _num(x):
        """批426-A:None / 空字串 / 帶逗號字串 一律安全轉數;不可轉=None。
        v0101 直接拿 None 去算術,multiply(None,10,5) 當場 TypeError——
        而 None 正是抽取器找不到數字時的常態回傳。"""
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return None if isinstance(x, float) and x != x else float(x)
        try:
            return float(str(x).replace(",", "").replace(",", "").strip())
        except Exception:
            return None

    def _band(self, err, expected=None):
        """容差判定。有 MDL008=用它的量級絕對容差;缺席=退相對誤差 band 並註明。"""
        a = abs(err)
        if self.xv is not None and expected is not None:
            tol, src = self.xv.tolerance(expected)
            if tol is not None:
                diff = abs(err * expected)
                if diff <= tol:
                    return "PASS", 1.0, src
                if diff <= tol * 5:
                    return "WARN", 0.65, src
                return "FAIL", 0.45, src
        if a <= 0.01:
            return "PASS", 1.0, "LOCAL_BAND"
        if a <= 0.05:
            return "PASS-SOFT", 0.85, "LOCAL_BAND"
        if a <= 0.10:
            return "WARN", 0.65, "LOCAL_BAND"
        return "FAIL", 0.45, "LOCAL_BAND"

    def add_sub(self, total, parts):
        """total ?= sum(parts)。無值一律 N/A(不猜、不當 0)。"""
        t = self._num(total)
        ps = [self._num(p) for p in (parts or [])]
        if t is None or not ps or any(p is None for p in ps):
            return {"verdict": "N/A", "conf": 0.0, "rel_err": None,
                    "why": "無值(total 或 parts 有 None)"}
        if t == 0:
            return {"verdict": "N/A", "conf": 0.0, "rel_err": None, "why": "total=0"}
        s = sum(ps)
        err = (s - t) / t
        v, c, src = self._band(err, t)
        return {"verdict": v, "conf": c, "rel_err": round(err, 4),
                "computed": s, "reported": t, "tol_src": src}

    def multiply(self, actual, a, b, scale_percent=False):
        """actual ?= a * b(TargetPrice = PER × EPS;NetIncome = EPS × Shares)。"""
        av, x, y = self._num(actual), self._num(a), self._num(b)
        if av is None or x is None or y is None:
            return {"verdict": "N/A", "conf": 0.0, "why": "無值"}
        expected = x * y
        if scale_percent:
            expected /= 100.0
        if expected == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "expected=0"}
        err = (av - expected) / expected
        v, c, src = self._band(err, expected)
        return {"verdict": v, "conf": c, "expected": round(expected, 4),
                "actual": av, "rel_err": round(err, 4), "tol_src": src}

    def division(self, actual, numer, denom, scale_percent=False):
        """兩段:A 量級 0.5x–3.0x、B 容差。處理 ROE %/小數。"""
        av, n, d = self._num(actual), self._num(numer), self._num(denom)
        if av is None or n is None or d is None or d == 0 or av == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "無值或分母/實際為 0"}
        expected = n / d
        if scale_percent:
            expected *= 100.0
        if expected == 0:
            return {"verdict": "N/A", "conf": 0.0, "why": "expected=0"}
        ratio = av / expected
        stage_a = 0.5 <= ratio <= 3.0
        err = (av - expected) / expected
        v, c, src = self._band(err, expected)
        if v == "FAIL" and stage_a:
            v, c = "PASS-RANGE", 0.6      # 量級對(平均 vs 期末權益之類),不判死
        return {"verdict": v, "conf": c, "expected": round(expected, 4),
                "actual": av, "ratio": round(ratio, 3),
                "stageA_magnitude_ok": stage_a, "tol_src": src}

    def historical_yoy(self, series):
        """series: list[(year, value)] ascending。無值那一年回 None,不外插。"""
        out = []
        s = sorted(series or [])
        for i in range(1, len(s)):
            (_, v0), (y1, v1) = s[i - 1], s[i]
            a, b = self._num(v0), self._num(v1)
            if a in (None, 0) or b is None:
                out.append({"year": y1, "yoy": None})
                continue
            out.append({"year": y1, "yoy": round((b - a) / abs(a), 4)})
        return out


# =====================================================================
# 5c · 期間/日期正規化(批426b;操作員規格)
# ---------------------------------------------------------------------
# 操作員規格三條:
#   ① 整合到「百萬」,小數點後**兩位**
#   ② 補不足能力
#   ③ 數字 / 英文+數字 / 民國,且**有前綴**:FY-23、F23、2023、20230102、230102
# v0101 的 restore_period_header 只認 12/24A 與 2023 兩型,其餘全回 None。
# 這裡把研報實務上會出現的寫法一次收齊,並且**分開回報「期間」與「基準」**
# (A=實際 / E=預估 / F=預測),因為把預估當實際比對就是製造假訊息。
# =====================================================================
MILLION_DECIMALS = 2                     # 規格①:百萬 + 小數點後兩位

_BASIS = {"A": "actual", "E": "estimate", "F": "forecast"}


def _yy_to_year(yy: int) -> int:
    """兩位年展開:00–79 → 20xx,80–99 → 19xx(研報實務不會出現 1980 前預估)。"""
    return 2000 + yy if yy <= 79 else 1900 + yy


def parse_period(tok):
    """任一期間/日期記號 → 結構化。認不出回 kind=None(誠實,不硬猜)。
    回 {"raw","kind","period","basis","roc"};kind ∈ date|year|quarter|month|None"""
    s = unicodedata.normalize("NFKC", str(tok or "")).strip()
    if not s:
        return {"raw": tok, "kind": None, "period": None, "basis": None, "roc": False}

    def out(kind, period, basis=None, roc=False):
        return {"raw": tok, "kind": kind, "period": period, "basis": basis, "roc": roc}

    # 民國:114年 / 民國114 / ROC114
    m = re.fullmatch(r"(?:民國|ROC)?\s*(\d{2,3})\s*年", s, re.I)
    if m and 1 <= int(m.group(1)) <= 200:
        return out("year", str(int(m.group(1)) + 1911), None, True)

    # 純數字:8 碼西元日 / 7 碼民國日 / 6 碼西元日 / 4 碼年
    if s.isdigit():
        if len(s) in (6, 7, 8):
            d = TickerFilename.numtoken_to_date(s)
            if d:
                return out("date", d, None, len(s) == 7)
        if len(s) == 4 and 1990 <= int(s) <= 2099:
            return out("year", s)
        return out(None, None)

    # 帶分隔的日期:2023-01-02 / 2023/1/2 / 114-12-02(民國)
    m = re.fullmatch(r"(\d{2,4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if m:
        y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        roc = False
        if y <= 200:                                  # 民國年
            y, roc = y + 1911, True
        elif y < 1000:
            y = _yy_to_year(y)
        if 1990 <= y <= 2099 and 1 <= mo <= 12 and 1 <= dd <= 31:
            return out("date", "%04d-%02d-%02d" % (y, mo, dd), None, roc)

    # 季:1Q25 / 25Q1 / Q1 2025 / 1Q2025
    m = (re.fullmatch(r"([1-4])Q\s*(\d{2,4})", s, re.I)
         or re.fullmatch(r"Q([1-4])\s*(\d{2,4})", s, re.I))
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        y = y if y >= 1000 else _yy_to_year(y)
        return out("quarter", "%04d-Q%d" % (y, q))
    m = re.fullmatch(r"(\d{2,4})\s*Q([1-4])", s, re.I)
    if m:
        y, q = int(m.group(1)), int(m.group(2))
        y = y if y >= 1000 else _yy_to_year(y)
        return out("quarter", "%04d-Q%d" % (y, q))

    # 月:12/24A → 2024-12(actual);12/25E → 2025-12(estimate)
    m = re.fullmatch(r"(\d{1,2})/(\d{2})([AEF])?", s, re.I)
    if m:
        mo, yy = int(m.group(1)), int(m.group(2))
        if 1 <= mo <= 12:
            return out("month", "%04d-%02d" % (_yy_to_year(yy), mo),
                       _BASIS.get((m.group(3) or "").upper()))

    # 會計年度前綴:FY-23 / FY23 / FY 2023 / F23 / E23 / A23 / 23F / 2023F
    m = re.fullmatch(r"FY[\s\-_]?(\d{2,4})([AEF])?", s, re.I)
    if m:
        y = int(m.group(1))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS.get((m.group(2) or "").upper()))
    m = re.fullmatch(r"([AEF])[\s\-_]?(\d{2,4})", s, re.I)       # F23 / E-23
    if m:
        y = int(m.group(2))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS[m.group(1).upper()])
    m = re.fullmatch(r"(\d{2,4})[\s\-_]?([AEF])", s, re.I)       # 23F / 2023E
    if m:
        y = int(m.group(1))
        return out("year", str(y if y >= 1000 else _yy_to_year(y)),
                   _BASIS[m.group(2).upper()])

    return out(None, None)


def to_million_2dp(value, unit="million", unit_mult=None):
    """規格①:任何單位 → 百萬,固定小數點後兩位。
    unit_mult 可傳 MDL008 的 UNIT_MULT 以共用同一份單位冊(零九頭龍)。
    無值 / 不可轉 → None(不當 0)。"""
    mult = (unit_mult or {}).get(unit)
    if mult is None:
        mult = {"million": 1.0, "billion": 1000.0, "hundred_million": 100.0,
                "million_ntd": 1.0, "thousand_ntd": 0.001, "thousand": 0.001,
                "ntd": 1e-6, "yuan": 1e-6, "元": 1e-6, "千元": 0.001,
                "百萬": 1.0, "億": 100.0, "十億": 1000.0}.get(unit, 1.0)
    try:
        v = float(str(value).replace(",", "").replace(",", "").strip()) * mult
    except Exception:
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return round(v, MILLION_DECIMALS)


# =====================================================================
# 7 · PRICE ADJUSTMENT (批426-H:復權誠實 + TP 合理性閘)
# =====================================================================
class PriceAdjustment:
    # 批419 工作站實錄:37 份真報告裡三份的 TP/價 比是 0.020 / 0.019 / 0.005
    # ——目標價只有股價的 1/50 到 1/200,那是抽錯的數。把它印成
    # 「潛在上漲空間 -98%」比不印更糟,讀的人會以為那是預測。
    TP_SANITY_LO, TP_SANITY_HI = 0.2, 5.0

    @staticmethod
    def to_adjusted(raw_price, cum_adjust_factor):
        """passed ex-div/ex-rights → 乘累積因子使序列可比。"""
        if raw_price is None or cum_adjust_factor in (None, 0):
            return raw_price
        return round(raw_price * cum_adjust_factor, 4)

    def normalize_series(self, prices, factors):
        return [self.to_adjusted(p, f) for p, f in zip(prices, factors)]

    def tp_sanity(self, target_price, price):
        """回 (態, 比值)。OK / TP_SUSPECT(帶外=疑抽錯)/ NA(算不了)。
        只 flag 不丟棄:我們不知道哪個數字才對,丟棄等於替操作員決定。"""
        try:
            if target_price is None or not price:
                return "NA", None
            r = float(target_price) / float(price)
        except Exception:
            return "NA", None
        return ("OK" if self.TP_SANITY_LO <= r <= self.TP_SANITY_HI else "TP_SUSPECT"), r

    def upside(self, target_price, current_price_adj, is_adjusted=True):
        """批426-H:current_price_adj 必須是**已復權**價。
        批425 實證:ENG080 在價表缺 adj_close 時誠實拒絕拿 close 頂替
        (「Adjusted 與原始不混用」)=正確行為。這裡照同一條律:
        is_adjusted=False 一律拒算,回 None 並由呼叫端交代,不悄悄用原始價。"""
        if not is_adjusted:
            return None
        if target_price is None or not current_price_adj:
            return None
        return round((float(target_price) - float(current_price_adj))
                     / float(current_price_adj), 4)


# =====================================================================
# 8 · CROSS VALIDATION
# =====================================================================
class BrokerRatingDict:
    BROKER = {
        "KGI": ["凱基", "kgi", "kgieworld"], "YUANTA": ["元大", "yuanta"],
        "FUBON": ["富邦", "fubon"], "CAPITAL": ["群益", "capital"],
        "PRESIDENT": ["統一", "pscnet"], "CTBC": ["中信", "中國信託", "ctbc"],
        "JPMORGAN": ["摩根", "jp morgan", "j.p. morgan", "jpm", "jpmorgan"],
        "GOLDMAN": ["高盛", "goldman", "gs"], "BOFA": ["美銀", "美林", "bofa", "merrill"],
        "MACQUARIE": ["麥格理", "macquarie", "mq"], "CITI": ["花旗", "citi"],
        "UBS": ["瑞銀", "ubs"], "DAIWA": ["大和", "daiwa"], "NOMURA": ["野村", "nomura"],
        "MORGANSTANLEY": ["摩根士丹利", "morgan stanley", "ms"], "CLSA": ["里昂", "clsa"],
        "MEGA": ["兆豐"], "HUANAN": ["華南", "華南永昌"], "TAISHIN": ["台新"],
        "SINOPAC": ["永豐"], "FIRST": ["第一金"], "MASTERLINK": ["元富"],
    }
    RATING = {
        "BUY": ["買進", "強力買進", "加碼", "逢低加碼", "buy", "outperform",
                "overweight", "strong buy"],
        "HOLD": ["中立", "持有", "區間", "區間操作", "neutral", "hold",
                 "market perform", "equal-weight", "equalweight"],
        "SELL": ["賣出", "減碼", "sell", "underperform", "underweight", "reduce"],
        "ADD": ["逢低", "accumulate", "add"],
        "NOT_RATED": ["未評等", "無評等", "not rated", "nr", "n/r"],
    }

    def __init__(self, extra_broker=None, extra_rating=None):
        self.b = {k: set(x.lower() for x in v) for k, v in self.BROKER.items()}
        self.r = {k: set(x.lower() for x in v) for k, v in self.RATING.items()}
        for k, v in (extra_broker or {}).items():
            self.b.setdefault(k, set()).update(x.lower() for x in v)
        for k, v in (extra_rating or {}).items():
            self.r.setdefault(k, set()).update(x.lower() for x in v)

    def broker_normalize(self, s):
        if not s:
            return None
        low = s.lower()
        for canon, al in self.b.items():
            if any(a in low for a in al):
                return canon
        return None

    def rating_normalize(self, s):
        if not s:
            return None
        low = s.lower()
        for canon, al in self.r.items():
            if any(re.search(r"\b" + re.escape(a) + r"\b", low) or a in low for a in al):
                return canon
        return None

    def validate_rating(self, s):
        c = self.rating_normalize(s)
        return {"raw": s, "canonical": c, "in_dict": c is not None}


class FieldValidation:
    _TEL = re.compile(r"(?:\+?886[-\s]?|\(0\d\)\s?|0)\d(?:[-\s]?\d){7,9}")
    # 批426-F:v0101 只認 NT$ 與 目標價,GS/MS 的 "Price Target 650"、"PT 78"
    # 全部漏抽(實測皆回 None)。加寬到與 VRN_ENG073 TP_RX 同一組觸發詞。
    _TP = re.compile(
        r"(?:Target\s*price|Price\s*Target|\bPT\b|目標價)"
        r"[^\d\-]{0,20}(?:NT\$|NT\s?\$|新台幣)?\s*([0-9][0-9,]*\.?\d*)", re.I)
    _TP_BARE = re.compile(r"(?:NT\$|NT\s?\$)\s*([0-9][0-9,]*\.?\d*)", re.I)

    def __init__(self, brd=None, price=None):
        self.brd = brd or BrokerRatingDict()
        self.price = price or PriceAdjustment()

    def extract_tel(self, text):
        out = []
        for m in self._TEL.finditer(text or ""):
            t = m.group(0).strip()
            if 8 <= len(re.sub(r"\D", "", t)) <= 12:
                out.append(t)
        return out

    def validate_email(self, email, broker_canon=None):
        m = re.match(r"([A-Za-z][A-Za-z.\-_]*)@([A-Za-z0-9.\-]+)$", email or "")
        if not m:
            return {"email": email, "valid": False, "broker_match": None}
        domain = m.group(2)
        dom_broker = self.brd.broker_normalize(domain)
        return {"email": email, "valid": True, "domain": domain,
                "domain_broker": dom_broker,
                "broker_match": (broker_canon is None) or (dom_broker == broker_canon)}

    def extract_target_price(self, text):
        m = self._TP.search(text or "") or self._TP_BARE.search(text or "")
        if not m:
            return None
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return None

    def validate_target_price(self, tp, per=None, eps=None, current=None,
                              fin=None, current_is_adjusted=True):
        res = {"target_price": tp, "checks": []}
        if tp is None or tp <= 0:
            res["checks"].append({"name": "positive", "ok": False})
            res["verdict"] = "FAIL"
            res["tp_state"] = "NA"
            return res
        res["checks"].append({"name": "positive", "ok": True})
        if per and eps and fin:
            mul = fin.multiply(tp, per, eps)
            res["checks"].append({"name": "TP=PER*EPS",
                                  "ok": mul["verdict"] in ("PASS", "PASS-SOFT", "N/A"),
                                  "detail": mul})
        # 批426-H:合理性閘進 checks(不是只擺著)——批422 的假綠就是閘抓到了下游不讀
        st, ratio = self.price.tp_sanity(tp, current)
        res["tp_state"], res["tp_ratio"] = st, (round(ratio, 4) if ratio else None)
        if st != "NA":
            res["checks"].append({"name": "tp_sanity", "ok": st == "OK",
                                  "state": st, "ratio": res["tp_ratio"],
                                  "band": [self.price.TP_SANITY_LO, self.price.TP_SANITY_HI]})
        if current:
            up = self.price.upside(tp, current, is_adjusted=current_is_adjusted)
            res["checks"].append({"name": "upside_sane",
                                  "ok": (up is not None and abs(up) <= 2.0),
                                  "upside": up,
                                  "why": "" if current_is_adjusted
                                         else "現價非復權=拒算(Adjusted 與原始不混用)"})
        res["verdict"] = "PASS" if all(c["ok"] for c in res["checks"]) else "WARN"
        return res


class CrossValidation:
    @staticmethod
    def four_way(filename_ticker, title_ticker, table_ticker=None, financials_ticker=None):
        vals = [("filename", filename_ticker), ("title", title_ticker),
                ("table", table_ticker), ("financials", financials_ticker)]
        present = [(k, v) for k, v in vals if v]
        agree = len({v for _, v in present}) <= 1
        return {"verdict": "PASS" if agree and present else ("FAIL" if present else "N/A"),
                "sources": dict(present)}

    @staticmethod
    def filename_vs_page(fn, page):
        out = {"fields": {}, "verdict": "PASS"}
        for key in ("ticker", "broker", "date"):
            a, b = fn.get(key), page.get(key)
            if a and b:
                ok = (a == b)
                out["fields"][key] = {"filename": a, "page": b, "match": ok}
                if not ok:
                    out["verdict"] = "FAIL"
            else:
                out["fields"][key] = {"filename": a, "page": b, "match": None}
        return out

    @staticmethod
    def zone_presence(info_zone_fields, body_zone_fields):
        return {"info_zone": {"has_data": bool(info_zone_fields),
                              "n": len(info_zone_fields or [])},
                "body_zone": {"has_data": bool(body_zone_fields),
                              "n": len(body_zone_fields or [])},
                "verdict": "PASS" if (info_zone_fields and body_zone_fields) else "WARN"}

    @staticmethod
    def historical_vs_source(report_vals, source_vals, tol=0.05):
        out = {"years": {}, "verdict": "PASS"}
        for y in sorted(set(report_vals) & set(source_vals)):
            rv, sv = report_vals[y], source_vals[y]
            if sv in (None, 0) or rv is None:
                out["years"][y] = {"report": rv, "source": sv, "match": None}
                continue
            err = abs((rv - sv) / sv)
            ok = err <= tol
            out["years"][y] = {"report": rv, "source": sv,
                               "rel_err": round(err, 4), "match": ok}
            if not ok:
                out["verdict"] = "FAIL"
        return out


# =====================================================================
# ORCHESTRATOR
# =====================================================================
class FirstPageEngine:
    def __init__(self, ssot_path=None, official_set=None, nlp_engine=None,
                 via_root=None, auto_hub=True):
        self.tf = TickerFilename(ssot_path, official_set)
        self.layout = Layout()
        self.tg = TableGeometry()
        self.nlp = NLPRepair(nlp_engine, auto_hub=auto_hub, via_root=via_root)
        self.xval = XValBridge(via_root)
        self.fin = FinancialValidation(self.xval)
        self.price = PriceAdjustment()
        self.brd = BrokerRatingDict()
        self.fv = FieldValidation(self.brd, self.price)
        self.xv = CrossValidation()

    # ---- 規格①:單位冊與 MDL008 共用(零九頭龍) ----
    def to_million(self, value, unit="million"):
        um = getattr(self.xval.mdl008, "UNIT_MULT", None) if self.xval.mdl008 else None
        return to_million_2dp(value, unit, um)

    def _filename_fields(self, filename):
        p = self.tf.parse_filename(filename)
        ticker = p["tickers"][0] if p["tickers"] else None
        date = p["dates"][0] if p["dates"] else None
        broker = None
        for tok in p["cjk"] + p["latin"]:
            b = self.brd.broker_normalize(tok)
            if b:
                broker = b
                break
        return {"ticker": ticker, "broker": broker, "date": date, "parse": p}

    @staticmethod
    def aggregate_verdict(out):
        """批426-I:總判必須讀到**所有**子閘。
        批422 的假綠就是上游閘抓到了(ENG080 TP_SUSPECT)、下游判定不讀它,
        於是一份目標價只有股價 1/200 的報告被印成 DONE。
        這裡把每個子判定逐一列出來,任何一個 FAIL 就 FAIL,任何 WARN 就 WARN,
        並回 gates 讓呼叫端看得見是誰把燈拉下來的——不做沉默彙總。"""
        gates = {}
        for key, path in (("ticker_cross", ("cross_check", "verdict")),
                          ("filename_vs_page", ("xv_filename_vs_page", "verdict")),
                          ("zone_presence", ("xv_zone_presence", "verdict")),
                          ("target_price", ("target_price", "verdict")),
                          ("historical", ("xv_historical", "verdict"))):
            node = out.get(path[0])
            if isinstance(node, dict) and node.get(path[1]):
                gates[key] = node[path[1]]
        tp_state = (out.get("target_price") or {}).get("tp_state")
        if tp_state == "TP_SUSPECT":
            gates["tp_sanity"] = "FAIL"          # 不得被無聲吞掉
        kind = ((out.get("filename_parse") or {}).get("kind")) or ""
        if not TickerFilename.kind_expects_ticker(kind):
            # 批418/426-G:非個股沒有代號與目標價是**正常**,不因此判紅
            for k in ("ticker_cross", "target_price", "tp_sanity"):
                if gates.get(k) in ("FAIL", "WARN"):
                    gates[k] = "N/A_NON_STOCK"
        vals = [v for v in gates.values() if v not in ("N/A", "N/A_NON_STOCK")]
        verdict = ("FAIL" if any(v == "FAIL" for v in vals)
                   else "WARN" if any(v in ("WARN", "PASS-SOFT", "PASS-RANGE") for v in vals)
                   else "PASS" if vals else "N/A")
        return {"verdict": verdict, "gates": gates, "kind": kind,
                "non_stock": not TickerFilename.kind_expects_ticker(kind)}

    def run(self, filename, chars=None, title_codes=None, table_chars=None,
            per=None, eps=None, current_price=None, current_is_adjusted=True,
            source_historical=None, report_historical=None,
            first_page_data=None, financial_page_data=None):
        out = {"engine": ENGINE_NAME, "version": ENGINE_VERSION,
               "filename": filename,
               "governance": "append-only; raw+repaired coexist"}
        fnf = self._filename_fields(filename)
        out["filename_parse"] = fnf["parse"]
        out["filename_fields"] = {k: fnf[k] for k in ("ticker", "broker", "date")}
        lay = (self.layout.classify(chars) if chars
               else {"company_name": "", "main_text": "", "footer": "", "lines": []})
        out["layout"] = {"company_name": lay["company_name"],
                         "footer_excluded": bool(lay["footer"])}
        title, body = lay["company_name"], lay["main_text"]
        full_text = (" ".join(l["text"] for l in lay.get("lines", []))
                     or (lay["footer"] + " " + body))
        out["ticker"] = self.tf.resolve(filename, title, body)
        out["main_text_raw"] = body
        out["main_text_repaired"] = self.nlp.repair_text(body)
        out["nlp_route"] = self.nlp.route()          # 批426-B:走哪條看得見
        out["xval_bridge"] = self.xval.status()      # 正典在不在也看得見

        emails = self.tf.parse_email(full_text)
        out["emails"] = emails
        out["tel"] = self.fv.extract_tel(full_text)
        page_broker = self.brd.broker_normalize(full_text)
        out["broker"] = page_broker
        out["rating"] = self.brd.validate_rating(full_text)
        tp = self.fv.extract_target_price(full_text)
        out["target_price"] = self.fv.validate_target_price(
            tp, per=per, eps=eps, current=current_price, fin=self.fin,
            current_is_adjusted=current_is_adjusted)
        if emails:
            e0 = emails[0]["analyst_id"] + "@" + emails[0]["broker_domain"]
            out["email_validation"] = self.fv.validate_email(e0, page_broker)

        page_date = fnf["date"]
        out["xv_filename_vs_page"] = self.xv.filename_vs_page(
            fnf, {"ticker": out["ticker"]["ticker"] or None,
                  "broker": page_broker, "date": page_date})
        info_zone = [x for x in [tp, out["rating"]["canonical"], page_broker] if x]
        out["xv_zone_presence"] = self.xv.zone_presence(
            info_zone, self.nlp.split_sentences(body))
        if title_codes:
            out["cross_check"] = self.tf.cross_check(out["ticker"]["ticker"], **title_codes)
        if table_chars:
            tbl = self.tg.reconstruct(table_chars)
            if tbl["rows"]:
                tbl["period_header"] = self.tg.restore_period_header(tbl["rows"][0])
            out["table"] = tbl
        if source_historical and report_historical:
            out["xv_historical"] = self.xv.historical_vs_source(
                report_historical, source_historical)
        # 批426:TW02 三源交叉核對(正典在位才跑;缺席誠實 None)
        if first_page_data is not None and financial_page_data is not None:
            tw = self.xval.three_way(
                {"potential_tickers": fnf["parse"]["tickers"],
                 "dates": fnf["parse"]["dates"]},
                first_page_data, financial_page_data)
            out["xv_three_source"] = tw if tw is not None else {
                "skipped": True, "why": self.xval.status()["why"].get("tw02", "TW02 缺席")}
        out["summary"] = self.aggregate_verdict(out)
        return out


# =====================================================================
# CLI(批426-J:真的接線;批425 一連四例都是「參數在、線沒接」)
# =====================================================================
def _argval(args, flag):
    if flag not in args:
        return None
    i = args.index(flag) + 1
    if i >= len(args) or args[i].startswith("--"):
        print(f"[旗標] {flag} 後面沒有值=忽略(誠實提示,不當作預設)")
        return None
    return args[i]


def _pdf_chars(path):
    """PyMuPDF 抽字元幾何;缺庫=誠實 None(不假裝抽到)。"""
    try:
        import fitz
    except Exception:
        return None, "PyMuPDF(fitz)未安裝=無法取字元幾何"
    try:
        with fitz.open(str(path)) as doc:
            if not doc.page_count:
                return [], "空 PDF"
            pg = doc[0]
            chars = []
            for b in pg.get_text("dict")["blocks"]:
                for ln in b.get("lines", []):
                    for sp in ln.get("spans", []):
                        for ch in sp.get("text", ""):
                            chars.append({"text": ch, "top": sp["bbox"][1],
                                          "x0": sp["bbox"][0], "size": sp.get("size", 10),
                                          "fontname": sp.get("font", "")})
            return chars, ""
    except Exception as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:90]}"


def run_cli(args):
    ssot = _argval(args, "--ssot")
    as_json = "--json" in args
    one, many = _argval(args, "--file"), _argval(args, "--dir")
    if not one and not many:
        print(__doc__)
        return 0
    eng = FirstPageEngine(ssot_path=ssot, via_root=_argval(args, "--via-root"))
    targets = ([Path(one)] if one
               else sorted(Path(many).glob("*.pdf")) if Path(many).is_dir() else [])
    if not targets:
        print(f"[絕] 無可處理檔({one or many})")
        return 2
    reports, bad = [], 0
    for p in targets:
        chars, why = _pdf_chars(p)
        r = eng.run(p.name, chars=chars or None)
        r["chars_why"] = why
        reports.append(r)
        s = r["summary"]
        if s["verdict"] == "FAIL":
            bad += 1
        if not as_json:
            fp = r["filename_parse"]
            tp = r["target_price"]
            print(f"  [{s['verdict']:<4}] {p.name[:44]:<46} 型別={fp['kind']:<6} "
                  f"代號={r['ticker']['ticker'] or '-':<5} 券商={r['broker'] or '-':<8} "
                  f"TP={tp.get('target_price') or '-'} ({tp.get('tp_state', '-')})"
                  + (f" · 閘 {s['gates']}" if s["verdict"] != "PASS" else ""))
    if as_json:
        print(json.dumps(reports, ensure_ascii=False, indent=1, default=str))
    else:
        nlp = reports[0]["nlp_route"]
        xb = reports[0]["xval_bridge"]
        print(f"[計] {len(reports)} 件 · FAIL {bad} · NLP 路徑={nlp['route']}"
              + (f"({nlp['hub_dir']})" if nlp.get("hub_dir") else "")
              + (f" · **為何**:{nlp['why']}" if nlp.get("why") else "")
              + f" · 正典 MDL008={'在' if xb['mdl008'] else '缺'}"
                f"/TW02={'在' if xb['tw02'] else '缺'}")
    return 1 if bad else 0


# =====================================================================
# SELFTEST(批426-M:零觸碰任何正本;批424 的教訓——自測寫正本冊,
#          十餘跑就把 escalation_log 從 66 筆灌成 78 筆)
# =====================================================================
def _ast_calls(src, skip_funcs=()):
    """回 (被呼叫的屬性名集合, 屬性名→所在函式名)。
    批426 自審:v0102 初版的檢②⑪ 用「原始碼裡有沒有這串字」來判,結果掃到
    **斷言自己寫的那串字**=自指偽陽(批423 SUP_MDL743 踩過同一個坑)。
    掃 AST 看的是真實呼叫節點,字串常數不會被算進來。"""
    import ast as _ast
    tree = _ast.parse(src)
    where, names = {}, set()
    for fn in _ast.walk(tree):
        if not isinstance(fn, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            continue
        if fn.name in skip_funcs:
            continue
        for n in _ast.walk(fn):
            if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Attribute):
                names.add(n.func.attr)
                where.setdefault(n.func.attr, fn.name)
    return names, where


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    fin = FinancialValidation()
    # ① 崩潰修(v0101 實測 TypeError)
    r1, r2 = fin.multiply(None, 10, 5), fin.add_sub(None, [1, 2])
    r3 = fin.division(None, 1, 2)
    chk("① None 不再當場崩(批426-A:v0101 multiply(None,10,5) 與 add_sub(None,[1,2]) "
        "皆 TypeError,而 None 正是抽取器找不到數字時的常態回傳)",
        r1["verdict"] == "N/A" and r2["verdict"] == "N/A" and r3["verdict"] == "N/A"
        and fin.multiply(1275, 25, 51)["verdict"] in ("PASS", "PASS-SOFT", "WARN", "FAIL"),
        f"(multiply={r1['verdict']} add_sub={r2['verdict']} division={r3['verdict']})")

    # ② NLP 真 API(v0101 呼叫不存在的 repaired())
    src = Path(__file__).read_text(encoding="utf-8")
    nlp = NLPRepair(auto_hub=False)
    _calls, _ = _ast_calls(src)
    _dehy = nlp.repair_text("a-\n b   c")      # f-string 運算式不得含反斜線 → 先取值
    chk("② NLP 掛鉤用真 API(批426-B:v0101 呼叫 self.ext.repaired(),而 TextProcessor "
        "只有 repair()——每次 AttributeError 被 except 吃掉→靜默退後備,外接引擎等於沒接。"
        "本檢用 AST 看真實呼叫節點,不掃字串——掃字串會掃到斷言自己寫的那串字)",
        "repaired" not in _calls and "repair" in _calls
        and "split_sentences" in _calls and "normalize" in _calls
        and nlp.route()["route"] == "HEURISTIC"
        # 後備行為兩件事各驗一次:換行連字號要**接回**(a- \n b → ab,這是
        # 研報 PDF 換行斷字的常態),連續空白要壓成一個。
        and _dehy == "ab c"
        and nlp.repair_text("x   y\n\n z") == "x y z",
        f"(呼叫到 repair={'repair' in _calls} repaired={'repaired' in _calls};"
        f"去連字號={_dehy!r};無外接時 route={nlp.route()['route']})")

    # ③ 民國七碼(v0101 回 None)
    chk("③ 民國七碼日期(批426-D:操作員真檔名 華南投顧-2637-慧洋-KY-1141202 正在用;"
        "v0101 只認 8/6 碼,1141202 回 None)",
        TickerFilename.numtoken_to_date("1141202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("20251202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("251202") == "2025-12-02"
        and TickerFilename.numtoken_to_date("3014") is None,
        "(四碼代號不得被當日期)")

    # ④ -KY 公司名 + 型別分類
    tf = TickerFilename()
    p = tf.parse_filename("華南投顧-2637-慧洋-KY-1141202.pdf")
    p2 = tf.parse_filename("20251205兆豐晨會報告-當日新聞與重要訊息評論.pdf")
    chk("④ 名字-KY 整體收為公司名 + 報告型別分類(批426-E/G;v0101 把 慧洋-KY 切成"
        "「慧洋」+「KY」,且無型別概念=非個股會被當失敗)",
        "慧洋-KY" in p["names"] and p["tickers"] == ["2637"]
        and p["dates"] == ["2025-12-02"] and p["kind"] == "個股"
        and p2["kind"] == "大盤晨報"
        and TickerFilename.kind_expects_ticker("個股")
        and not TickerFilename.kind_expects_ticker("大盤晨報"),
        f"(names={p['names']} kind={p['kind']} / {p2['kind']})")

    # ⑤ 目標價 regex 加寬(v0101 兩型皆回 None)
    fv = FieldValidation()
    got = {s: fv.extract_target_price(s) for s in
           ("目標價:145 元", "NT$1,275", "12-month target price: NT$1,275",
            "Price Target 650", "PT 78")}
    chk("⑤ 目標價觸發詞加寬(批426-F:v0101 只認 NT$ 與 目標價,GS/MS 的 "
        "Price Target / PT 全部漏抽——實測皆回 None)",
        got["Price Target 650"] == 650.0 and got["PT 78"] == 78.0
        and got["12-month target price: NT$1,275"] == 1275.0
        and got["目標價:145 元"] == 145.0,
        f"({got})")

    # ⑥ 期間前綴(操作員規格③)
    pp = {t: parse_period(t) for t in
          ("FY-23", "F23", "2023", "20230102", "230102", "1141202",
           "12/25E", "1Q25", "114年", "2023F")}
    chk("⑥ 期間前綴全收(操作員規格③:FY-23 / F23 / 2023 / 20230102 / 230102 / 民國;"
        "並分開回報基準 A實際/E預估/F預測——把預估當實際比對就是製造假訊息)",
        pp["FY-23"]["period"] == "2023" and pp["F23"]["period"] == "2023"
        and pp["F23"]["basis"] == "forecast" and pp["2023"]["kind"] == "year"
        and pp["20230102"]["period"] == "2023-01-02"
        and pp["230102"]["period"] == "2023-01-02"
        and pp["1141202"]["period"] == "2025-12-02" and pp["1141202"]["roc"]
        and pp["12/25E"]["period"] == "2025-12" and pp["12/25E"]["basis"] == "estimate"
        and pp["1Q25"]["period"] == "2025-Q1" and pp["114年"]["period"] == "2025"
        and pp["2023F"]["basis"] == "forecast",
        f"(FY-23→{pp['FY-23']['period']} · F23→{pp['F23']['basis']} · "
        f"1141202→{pp['1141202']['period']} · 1Q25→{pp['1Q25']['period']})")

    # ⑦ 百萬兩位小數(操作員規格①)
    chk("⑦ 統一到百萬、小數點後兩位(操作員規格①;不可轉=None 不當 0)",
        to_million_2dp("22,500.049") == 22500.05
        and to_million_2dp(1, "billion") == 1000.0
        and to_million_2dp("1,234", "thousand_ntd") == 1.23
        and to_million_2dp(None) is None and to_million_2dp("n/a") is None
        and MILLION_DECIMALS == 2,
        f"(22,500.049→{to_million_2dp('22,500.049')} · "
        f"1 billion→{to_million_2dp(1, 'billion')})")

    # ⑧ TP 合理性閘 + 復權誠實
    pa = PriceAdjustment()
    chk("⑧ TP 合理性閘 + 復權誠實(批419 工作站:三份真報告 TP/價 比 0.020/0.019/0.005"
        "=抽錯的數,印成「上漲 -98%」比不印更糟;批425:現價非復權一律拒算,"
        "不拿原始 close 頂替)",
        pa.tp_sanity(38.0, 942.0)[0] == "TP_SUSPECT"
        and pa.tp_sanity(1275.0, 1130.0)[0] == "OK"
        and pa.tp_sanity(None, 100)[0] == "NA"
        and pa.upside(1275, 1130) == 0.1283
        and pa.upside(1275, 1130, is_adjusted=False) is None,
        f"(0.040→{pa.tp_sanity(38.0, 942.0)[0]} · "
        f"非復權→{pa.upside(1275, 1130, is_adjusted=False)})")

    # ⑨ 總判必須讀到所有子閘(批422 假綠)
    eng = FirstPageEngine(auto_hub=False)
    bad = {"filename_parse": {"kind": "個股"},
           "target_price": {"verdict": "PASS", "tp_state": "TP_SUSPECT"}}
    ns = {"filename_parse": {"kind": "大盤晨報"},
          "target_price": {"verdict": "FAIL", "tp_state": "NA"}}
    a, b = eng.aggregate_verdict(bad), eng.aggregate_verdict(ns)
    chk("⑨ 總判讀得到 TP 合理性閘,且非個股不被判紅(批422 假綠:上游閘抓到 TP_SUSPECT、"
        "下游判定不讀它,於是目標價只有股價 1/200 的報告被印成 DONE;批418:"
        "非個股沒有代號與目標價是正常)",
        a["verdict"] == "FAIL" and a["gates"].get("tp_sanity") == "FAIL"
        and b["verdict"] != "FAIL" and b["non_stock"] is True
        and b["gates"].get("target_price") == "N/A_NON_STOCK",
        f"(個股+TP_SUSPECT→{a['verdict']} · 非個股+FAIL→{b['verdict']})")

    # ⑩ CLI 真的接線(批425 一連四例)
    seen = {}
    real_run, real_argv = FirstPageEngine.run, sys.argv
    try:
        FirstPageEngine.run = lambda self, filename, **kw: (
            seen.update({"filename": filename, "kw": sorted(kw)}) or {
                "summary": {"verdict": "PASS", "gates": {}},
                "filename_parse": {"kind": "個股"}, "ticker": {"ticker": "2330"},
                "broker": "GS", "target_price": {"target_price": 1, "tp_state": "OK"},
                "nlp_route": {"route": "HEURISTIC", "why": ""},
                "xval_bridge": {"mdl008": False, "tw02": False, "why": {}}})
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "GS-2330 20251205.pdf"
            f.write_bytes(b"%PDF-1.4\n%%EOF\n")
            sys.argv = ["x", "--file", str(f)]
            rc = run_cli(sys.argv[1:])
            sys.argv = ["x", "--file"]                 # 缺值對照組:不得 IndexError
            rc2 = run_cli(sys.argv[1:])
    finally:
        FirstPageEngine.run, sys.argv = real_run, real_argv
    chk("⑩ CLI 旗標真的接到 run()(批425:ENG073 main() 光禿禿 return run()、"
        "ENG074 寫死 run(d,None,..)、MDL141 不解析 --db、AllGreen $StageTimeoutSec "
        "宣告沒用過——四天內同一模式四次。缺值時誠實忽略不得 IndexError)",
        rc == 0 and seen.get("filename") == "GS-2330 20251205.pdf" and rc2 == 0,
        f"(收到 filename={seen.get('filename')})")

    # ⑪ 正典橋誠實三態 + 零觸碰正本
    xb = XValBridge(via_root="/__no_such_via_root__")
    _prod_calls, _ = _ast_calls(src, skip_funcs=("selftest",))   # 正式碼路徑
    chk("⑪ 正典橋缺席=誠實說缺(不假裝有),且本檔自測零觸碰任何正本"
        "(批424:自測寫正本冊,十餘跑把 66 筆灌成 78 筆)",
        xb.status()["mdl008"] is False and xb.status()["tw02"] is False
        and xb.status()["why"] and xb.tolerance(500)[1] == "LOCAL_BAND"
        and xb.is_valid_ticker("2330") and not xb.is_valid_ticker("2025")
        and not (_prod_calls & {"write_text", "write_bytes", "escalate", "mkdir"}),
        f"(why={list(xb.status()['why'])};selftest 以外的落檔呼叫="
        f"{sorted(_prod_calls & {'write_text', 'write_bytes', 'escalate', 'mkdir'}) or '無'})")

    # ⑫ 表格幾何:bisect 與線性掃答案必須完全相同(批426-K 只換速度不換答案)
    import random
    random.seed(7)
    centers = sorted(random.uniform(0, 800) for _ in range(60))
    probes = [random.uniform(-50, 850) for _ in range(400)]
    same = all(TableGeometry._nearest(centers, v)
               == min(range(len(centers)), key=lambda i: abs(centers[i] - v))
               for v in probes)
    chk("⑫ bisect 最近群聚與原線性掃**答案完全相同**(批426-K 是效能改寫,"
        "不是行為改寫;400 組亂數探針對照)",
        same and TableGeometry._nearest([], 1) == 0)

    n = 12
    print(f"  [計] 十二檢 OK {n - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print(f"=== {ENGINE_NAME} {ENGINE_VERSION} · 十二檢自測"
              "(零網路;零觸碰正本;含 v0101 實測缺陷對照)===")
        return selftest()
    return run_cli(args)


if __name__ == "__main__":
    sys.exit(main())
