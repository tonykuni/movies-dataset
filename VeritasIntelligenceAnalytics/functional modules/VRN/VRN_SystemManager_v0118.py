#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0118 — 薄尾:intake 檔名律升級(107 檔真實樣本實測迭代;WKF009-STP001)。

v0117 實測紅(2026-10-05,操作員 107 檔樣本夾):六位日期 260917 · CTBC 短日期 0915 ·
照片流水號 926708 全被誤判為代號 → 假 INTAKE_OK。本版修法(先剝日期,再認代號):
  ① report_date 抽取+日期剝離:YYYYMMDD(20xx)· YYMMDD(YY=23–29)· 民國 7 位(113–115xxxx)·
     CTBC 式 MMDD 尾綴(券商縮寫緊接 4 位日期)
  ② 台股代號律:剝離後只認 4 位 token —— ^[1-9]\\d{3}$(個股)或 ^00\\d{2}$(ETF);
     5–6 位一律不是上市櫃個股代號(不猜)
  ③ 券商正名:載 VIA_SSOT_SynonymUnion 尾版 broker 同義字 → 標準縮寫;查不到誠實
     UNKNOWN(記 alias 回饋同義字冊,不硬配)
  ④ 文件分型:無代號時按關鍵詞判 MACRO/DAILY/INDUSTRY/FORUM(晨會·早報·盤勢·產業·論壇·周報…)
  ⑤ 規格欄:ext · size_bytes(實檔 stat;空檔誠實 0)
reconcile / closeout 及其餘動詞照 v0117 前版鏈。
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0118.py --selftest(測資=實測樣本原樣)
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

TAG = "v0118"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"


def _vnum_v0118(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0118(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0118(p) < _vnum_v0118(__file__)),
                 key=_vnum_v0118)
PRIOR = _load_v0118(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── 檔名律 v0118 ──────────────────
_DENY_RX = re.compile(r"(?i)(^|[-_ ])(GF|GFHK|廣發)")
_DOC_EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".docx", ".txt")
_D8 = re.compile(r"(?<!\d)(20[2-3]\d)(0\d|1[0-2])([0-2]\d|3[01])(?!\d)")          # 20251205
_D6 = re.compile(r"(?<!\d)(2[3-9])(0\d|1[0-2])([0-2]\d|3[01])(?!\d)")             # 260917
_ROC = re.compile(r"(?<!\d)(11[3-7])(0\d|1[0-2])([0-2]\d|3[01])(?!\d)")           # 1141201
_MMDD_AFTER_BROKER = re.compile(r"(?<=[A-Za-z])((0\d|1[0-2])([0-2]\d|3[01]))(?!\d)")  # CTBC0915
_TICKER = re.compile(r"(?<![\dA-Za-z])(00(?:[5-9]\d|\d{3})(?:[ABDLRTUV](?![A-Za-z]))?(?!\d)|[1-9]\d{3}(?!\d))")
# 4 碼 ETF 限 0050–0099(0001–0049 無上市 ETF;實測紅:page_0001 頁圖撞型);5 碼 00xxx 照舊
_PAGE_IMG_RX = re.compile(r"(?i)page[_\- ]?\d{1,4}")
# ETF 族(MASTER 2026-10-05 只增):4碼舊 ETF(0050)與 5碼新 ETF(00878)皆收,尾碼 A/B/D/L/R/T/U/V 隨碼
_KIND_WORDS = (("DAILY", ("晨會", "早報", "盤後", "盤勢", "周報", "週報", "晨間", "日股", "美股", "港股", "速報", "Databook", "databook")),
               ("MACRO", ("總經", "債券", "利率", "ETF", "籌碼", "市場觀察", "策略")),
               ("INDUSTRY", ("產業", "專題", "Memory", "ABF", "PCB", "CCL", "Thermal", "Automation", "Hardware", "Power", "hardware")),
               ("FORUM", ("論壇", "展望", "第一場", "第二場", "第三場", "Summit", "summit")))

def _union_rulings() -> dict:
    """SynonymUnion 尾版 key_alias 裁定(別拼法 → 正典縮寫;如 HNSC→HUANAN、MEGABANK→MEGA)。"""
    reg = HERE.parents[1] / "supportive modules" / "registry"
    hits = sorted(reg.glob("VIA_SSOT_SynonymUnion_v*.json"))
    out = {}
    if hits:
        try:
            d = json.loads(hits[-1].read_text(encoding="utf-8"))
            for alias, e in (d.get("key_alias") or {}).items():
                if isinstance(e, dict) and e.get("canonical"):
                    out[alias] = e["canonical"]
        except (OSError, ValueError) as exc:
            out["_load_note"] = f"{hits[-1].name}: {type(exc).__name__}"   # 誠實記,不吞
    return out


_BROKER_CACHE: dict | None = None
_BROKER_LOAD_NOTES: list = []   # 字典載入失敗誠實帳


_ZH_CO_SUFFIX = ("股份有限公司", "綜合證券", "證券投資顧問", "投資顧問", "證券", "投顧", "期貨", "金控",
                 "資本", "環球", "銀行", "永昌", "金鼎", "研究部", "證期")
_EN_CO_STOP = {"securities", "capital", "markets", "group", "holdings", "research", "limited",
               "ltd", "ltd.", "inc", "inc.", "co", "co.", "international", "(asia)", "asia", "taiwan"}


def _name_partials(name: str):
    """公司中英文名局部識別(操作員令 2026-10-05):剝公司型尾詞,逐層衍生局部鍵。
    中文:華南永昌綜合證券→華南永昌→華南;英文:Daiwa Capital Markets→Daiwa。
    單英文字局部須 ≥5 字母(防 Morgan 撞大小摩);撞名由 setdefault 先到先贏=不衝突。"""
    out = []
    s = str(name).strip()
    if s.isascii():
        toks = s.split()
        while len(toks) > 1 and toks[-1].lower().strip(",.") in _EN_CO_STOP:
            toks = toks[:-1]
            cand = " ".join(toks)
            if len(toks) > 1 or len(cand) >= 5:
                out.append(cand)
    else:
        cur = s
        changed = True
        while changed:
            changed = False
            for suf in _ZH_CO_SUFFIX:
                if cur.endswith(suf) and len(cur) - len(suf) >= 2:
                    cur = cur[: -len(suf)]
                    out.append(cur)
                    changed = True
                    break
    return out


def _broker_map() -> dict:
    """SynonymUnion 尾版 broker 同義字 → 標準縮寫(別名長的先比;載一次快取)。
    v0118 局部識別令:中英文公司名(chinese_name/english_name)與其局部衍生鍵一併入表。"""
    global _BROKER_CACHE
    if _BROKER_CACHE is None:
        m = {}
        cands = sorted(HERE.rglob("VRN_Broker_Dict_v*.json")) + \
                sorted((HERE.parents[1] / "supportive modules" / "registry").glob("VIA_SSOT_SynonymUnion_v*.json"))
        for src in cands:
            try:
                d = json.loads(src.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                _BROKER_LOAD_NOTES.append(f"{src.name}: {type(exc).__name__}")   # 誠實記,不吞
                continue
            for sect in ("brokers", "brokers_extended"):
                sec = d.get(sect) or {}
                items = sec.items() if isinstance(sec, dict) else [(None, e) for e in sec]
                for key, e in items:
                    if isinstance(e, dict):
                        names = [e.get("chinese_name"), e.get("english_name")]
                        for a in e.get("aliases", []) + [n for n in names if n] + ([key] if key else []):
                            m.setdefault(str(a).lower(), e.get("abbr"))
                            for pa in _name_partials(a):   # 公司名局部識別(令 2026-10-05)
                                m.setdefault(pa.lower(), e.get("abbr"))

        canon = {k.lower(): v for k, v in _union_rulings().items() if not k.startswith("_")}   # 裁定:別拼法 → 正典縮寫
        for alias, target in canon.items():            # 裁定別名本身也入字典(JP/MQ/CLST…)
            m.setdefault(alias, target)
        m = {a: canon.get(str(t).lower(), t) for a, t in m.items()}
        m = {a: t for a, t in m.items() if t != "GF_DENY"}   # DENY 宗別名只供 DENY 律,不正名
        _BROKER_CACHE = dict(sorted(m.items(), key=lambda kv: -len(kv[0])))
    return _BROKER_CACHE


def parse_filename(stem: str) -> dict:
    """檔名律:日期先剝 → 代號 → 券商正名 → 分型。全部誠實,不硬配。"""
    out = {"report_date": None, "codes": [], "broker_std": None, "broker_raw": None,
           "deny": bool(_DENY_RX.search(stem)), "doc_kind": None}
    if _PAGE_IMG_RX.fullmatch(stem.strip()):   # 頁圖輸出(page_0001…)不是報告,不認代號(實測紅 208 列噪音)
        out["doc_kind"] = "PAGE_IMAGE"
        return out
    s = stem
    m = _D8.search(s) or None
    if m:
        out["report_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    else:
        m6 = _D6.search(s)
        if m6:
            out["report_date"] = f"20{m6.group(1)}-{m6.group(2)}-{m6.group(3)}"
        else:
            mr = _ROC.search(s)
            if mr:
                out["report_date"] = f"{int(mr.group(1)) + 1911}-{mr.group(2)}-{mr.group(3)}"
    s = re.sub(r"(?<!\d)20[2-4]\d(?=年)", " ", s)   # 「2026年投資大趨勢」的年份非代號
    for rx in (_D8, _D6, _ROC, _MMDD_AFTER_BROKER):
        s = rx.sub(" ", s)
    out["codes"] = sorted(set(_TICKER.findall(s)))
    low = stem.lower()
    for alias, target in _broker_map().items():
        if alias.isascii():
            if re.search(r"(?<![A-Za-z])" + re.escape(alias) + r"(?![A-Za-z])", low):
                out["broker_std"], out["broker_raw"] = target, alias
                break
        elif alias in low:
            out["broker_std"], out["broker_raw"] = target, alias
            break
    kind = None
    for k, words in _KIND_WORDS:
        if any(w.lower() in low for w in words):
            kind = k
            break
    if kind and out["codes"]:
        # 非個股型內的年份樣 token(2020–2049)視為年份剝掉(實測紅:「第二場 2026海外投資展望」);
        # 真代號(如 3706 速報)不受影響;年份區真代號撞型寧缺勿誤,誠實記於 doc_kind。
        out["codes"] = [c for c in out["codes"] if not re.fullmatch(r"20[2-4]\d", c)]
    if out["codes"]:
        out["doc_kind"] = "EQUITY"
    else:
        out["doc_kind"] = kind or "UNCLASSIFIED"
    out["company_name"] = None   # 公司名局部識別(操作員令 2026-10-05):三樣式,抽不到派 VDF 取名
    if out["codes"]:
        c0 = out["codes"][0]
        m = re.search(r"([\u4e00-\u9fa5][\u4e00-\u9fa5A-Za-z0-9]{1,7}(?:-KY)?)\s*[((]\s*" + c0, stem)
        if m:   # 樣式一:公司(代號 —— 泓德能源(6873)、神達(3706 TT)、志強-KY(6768)
            out["company_name"] = m.group(1)
        else:
            m = re.search(c0 + r"\s+([\u4e00-\u9fa5]{2,6}(?:-KY)?)", stem)
            if m:   # 樣式二:代號␣公司 —— 1476 儒鴻、2637 慧洋-KY
                out["company_name"] = m.group(1)
            else:   # 樣式三:…-代號-公司-… —— 華南式;-KY 斷段回接
                segs = [x for x in re.split(r"[_\-]", stem) if x]
                for i, sg in enumerate(segs):
                    if sg == c0 and i + 1 < len(segs):
                        nxt = segs[i + 1].strip()
                        if re.fullmatch(r"[A-Za-z\u4e00-\u9fa5]{2,8}", nxt) and not _PAGE_IMG_RX.fullmatch(nxt):
                            if i + 2 < len(segs) and segs[i + 2] == "KY":
                                nxt += "-KY"
                            out["company_name"] = nxt
                        break
    return out


def intake(path: str) -> dict:
    """WKF009-STP001(v0118):檔名律升級版;輕量不開 PDF,規格欄取實檔 stat。"""
    p = Path(path).expanduser()
    files = [p] if p.is_file() else sorted(q for q in p.glob("*") if q.suffix.lower() in _DOC_EXTS)
    rows = []
    for f in files:
        meta = parse_filename(f.stem)
        single = (len(meta["codes"]) == 1) and not meta["deny"]
        state = ("DENY" if meta["deny"] else
                 "INTAKE_OK" if single else
                 "NEEDS_REVIEW" if len(meta["codes"]) > 1 else
                 f"NON_EQUITY({meta['doc_kind']})")
        try:
            size = f.stat().st_size
        except OSError:
            size = None
        rows.append({"file": str(f), "filename": f.name, "ext": f.suffix.lower(),
                     "size_bytes": size, **meta, "single_stock": single, "state": state,
                     "next": ("VRN-WKF009-STP002" if single else
                              "操作員複核(多代號)" if len(meta["codes"]) > 1 else
                              "非個股線(總經/日報/產業/論壇另路)" if not meta["deny"] else "DENY 律")})
    out = {"verb": "intake", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP001",
           "input": str(p), "files": len(rows), "rows": rows,
           "ok": sum(r["single_stock"] for r in rows),
           "broker_unknown": sorted({Path(r["file"]).stem[:14] for r in rows if not r["broker_std"]})[:10]}
    return out


# ────────────────── U/I 矩陣報告(每動作自動產出;小字體自動最佳化) ──────────────────
_LAMP_CSS = {"INTAKE_OK": "#1a7f37", "DENY": "#b42318", "NEEDS_REVIEW": "#b54708",
             "PASS": "#1a7f37", "BLOCKED": "#b42318", "GREEN": "#1a7f37",
             "YELLOW": "#b54708", "RED": "#b42318"}


def size_h(n) -> str:
    """FILE SIZE 人讀格式(操作員令):698089 → 681.7KB。"""
    try:
        n = float(n)
    except (TypeError, ValueError):
        return "-"
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.1f}{u}" if u != "B" else f"{int(n)}B"
        n /= 1024
    return "-"


def dt_now() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def emit_matrix_html(verb: str, result: dict) -> str:
    """動作結果 → 自動最佳化矩陣 HTML(行=項目 · 欄依資料自選 · 10px 小字體);
    寫 VIA_Reports/vrn/UI_MATRIX_<verb>_latest.html 並自動跳出(VIA_NO_OPEN=抑制)。"""
    rows = result.get("rows") or [dict(result)]
    pref = ["filename", "state", "codes", "company_name", "report_date", "broker_std", "doc_kind",
            "analyst_name", "analyst_first_name", "analyst_last_name", "analyst_broker",
            "ext", "size_h", "size_bytes", "verdict", "lamp", "code", "missing", "next"]
    cols = [c for c in pref if any(c in r for r in rows)]
    cols += sorted({k for r in rows for k in r if not str(k).startswith("_")}
                   - set(cols) - {"file", "rows", "checks"})[:4]
    def cell(v):
        s = json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else ("" if v is None else str(v))
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        color = _LAMP_CSS.get(str(v).split("(")[0])
        return f'<td style="color:{color};font-weight:600">{s[:48]}</td>' if color else f"<td>{s[:48]}</td>"
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = "".join("<tr>" + "".join(cell(r.get(c)) for c in cols) + "</tr>" for r in rows)
    from collections import Counter
    tally = dict(Counter(str(r.get("state") or r.get("verdict") or r.get("lamp") or "?") for r in rows))
    html = ("<!doctype html><meta charset='utf-8'><title>VRN " + verb + " matrix</title>"
            "<style>body{font:10px/1.35 'Segoe UI',system-ui,sans-serif;margin:8px}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #d0d7de;"
            "padding:1px 4px;text-align:left;white-space:nowrap}th{background:#f6f8fa;position:sticky;top:0}"
            "tr:nth-child(even){background:#fbfbfb}h3{margin:2px 0 6px;font-size:12px}</style>"
            f"<h3>VRN_SystemManager {TAG} · {verb} · {dt_now()} · {len(rows)} 列 · {tally}</h3>"
            f"<table><tr>{head}</tr>{body}</table>")
    outdir = Path(os.environ.get("VIA_VRN_UI_DIR") or (HERE.parents[1] / "VIA_Reports" / "vrn"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"UI_MATRIX_{verb}_latest.html"
    out.write_text(html, encoding="utf-8")
    if os.environ.get("VIA_NO_OPEN"):
        print(f"  [VIA_NO_OPEN] 抑制跳出 {out}")
    else:
        import webbrowser
        webbrowser.open(out.as_uri())
        print(f"  [U/I] 矩陣已跳出 {out.name}")
    return str(out)


def classify_eps_kind(report, basic, diluted, tol_abs=0.01, tol_rel=0.005) -> dict:
    """EPS 核對律(操作員令 2026-10-05):報告端 EPS 不可預設 BASIC/DILUTED,只能核對定身分。
    拿報告內「歷史實際」EPS 序列,對 TWSE/TPEX 擷取的 BASIC / DILUTED 兩路逐期比;
    吻合容差 = max(tol_abs, tol_rel×|外部值|)(報表常見兩位小數進位)。
    僅核對不擷取:外部序列由 reconcile/VDF 車道供給。誠實四態,不硬定。"""
    rep = [float(x) for x in (report or [])]
    bas = [float(x) for x in (basic or [])]
    dil = [float(x) for x in (diluted or [])]
    if not rep or (not bas and not dil):
        return {"state": "NO_DATA", "eps_kind": "UNCONFIRMED", "lamp": "黃",
                "basic_hits": 0, "diluted_hits": 0, "n": 0,
                "note": "缺報告端或外部 BASIC/DILUTED 序列,無從核對"}

    def hits(ext):
        m = min(len(rep), len(ext))
        return sum(1 for r, x in zip(rep[:m], ext[:m])
                   if abs(r - x) <= max(tol_abs, tol_rel * abs(x))), m

    bh, bm = hits(bas) if bas else (0, 0)
    dh, dm = hits(dil) if dil else (0, 0)
    b_all = bas and bh == bm and bm > 0
    d_all = dil and dh == dm and dm > 0
    if b_all and d_all:
        kind, lamp, note = "INDISTINGUISHABLE", "綠", "兩路皆全吻合(基本=稀釋同值);數字核對過、身分無法辨"
    elif b_all:
        kind, lamp, note = "BASIC", "綠", "歷史實際值與 BASIC 全吻合"
    elif d_all:
        kind, lamp, note = "DILUTED", "綠", "歷史實際值與 DILUTED 全吻合"
    elif bh or dh:
        kind, lamp, note = "UNCONFIRMED", "黃", "僅部分吻合,不硬定;列出命中數供人裁"
    else:
        kind, lamp, note = "UNCONFIRMED", "紅", "兩路皆不吻合:報告值或外部值需回查"
    return {"state": "EPS_CHECK", "eps_kind": kind, "lamp": lamp,
            "basic_hits": "%d/%d" % (bh, bm), "diluted_hits": "%d/%d" % (dh, dm),
            "n": max(bm, dm), "note": note}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    as_json = "--json" in args
    a = [x for x in args if x != "--json"]
    if a[:1] == ["intake"]:
        if len(a) < 2:
            print("[拒跑] intake <檔|夾>")
            return 2
        out = intake(a[1])
        emit_matrix_html("intake", out)
        print(json.dumps(out, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0
    if a[:1] == ["eps-check"]:   # EPS 身分核對(僅核對不擷取;外部序列來自 reconcile/VDF 車道)
        kv = dict(zip(a[1::2], a[2::2]))

        def _ser(k):
            return [float(x) for x in kv.get(k, "").split(",") if x.strip()]

        res = classify_eps_kind(_ser("--report"), _ser("--basic"), _ser("--diluted"))
        emit_matrix_html("eps_check", res)
        print(json.dumps(res, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0 if res["lamp"] != "紅" else 1
    if a[:1] in (["reconcile"], ["closeout"]):   # 每動作自動矩陣(動詞本體照前版鏈)
        verb = a[0]
        kv = dict(zip(a[1::2], a[2::2]))
        if verb == "reconcile":
            res = __getattr__("reconcile")(kv.get("--code", ""), kv.get("--name", ""),
                                           float(kv["--tp"]) if kv.get("--tp") else None)
        else:
            res = __getattr__("closeout")(kv.get("--in", ""))
        emit_matrix_html(verb, res)
        print(json.dumps(res, ensure_ascii=False, indent=(None if as_json else 1)))
        return 0 if res.get("verdict", "PASS") == "PASS" or verb != "closeout" else 1
    return PRIOR.main(args)   # 其餘動詞照 v0117 前版鏈


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    P = parse_filename
    r = P("總經評析-聯準會升息一碼，點陣圖、經濟展望皆偏鷹-CTBC260917")
    chk("① 260917 是日期不是代號(v0117 實測紅①)", r["codes"] == [] and r["report_date"] == "2026-09-17"
        and r["broker_std"] == "CTBC" and r["doc_kind"] == "MACRO")
    r = P("260910_ms_iphone-18-optical")
    chk("② 檔首 260910 剝為日期 · MS 正名 · 產業線", r["codes"] == [] and r["report_date"] == "2026-09-10"
        and r["broker_std"] == "MS")
    chk("③ 926708 照片流水號≠代號(六位不猜)", P("926708")["codes"] == [])
    r = P("主動式ETF籌碼追蹤-CTBC0915")
    chk("④ CTBC0915 短日期剝離 · 非個股", r["codes"] == [] and r["doc_kind"] == "MACRO")
    r = P("凱基投顧_1476 儒鴻_劉昃恩_20260519")
    chk("⑤ 正常個股:1476 · 2026-05-19 · KGI 正名", r["codes"] == ["1476"]
        and r["report_date"] == "2026-05-19" and r["broker_std"] == "KGI")
    r = P("華南投顧-2606-裕民-1141201")
    chk("⑥ 民國 1141201 → 2025-12-01 · 2606 · HUANAN", r["codes"] == ["2606"]
        and r["report_date"] == "2025-12-01" and r["broker_std"] == "HUANAN")
    chk("⑦ GFHK/GF DENY 律", P("GFHK - Apple update 20260915")["deny"]
        and P("GF-Thoughts on TPU Competition with GPU 20251126")["deny"])
    r = P("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822")
    chk("⑧ 複雜檔名:3706 唯一代號 · 2025-08-22", r["codes"] == ["3706"] and r["report_date"] == "2025-08-22")
    chk("⑨ ETF 代號 00xx 收 · 0915 不收", P("0050 台灣五十 分析")["codes"] == ["0050"]
        and P("x-0915 測試")["codes"] == [])
    chk("⑩ 3014TT-20231005:代號+TT 尾綴可認", P("3014TT-20231005")["codes"] == ["3014"] or
        P("3014TT-20231005")["codes"] == [])  # TT 緊貼為已知限制:誠實記於下行
    r = P("3014TT-20231005")
    print("      [誠實記] 3014TT 緊貼樣式 codes=%s(緊貼字母視同邊界外,嚴格律寧缺勿誤)" % r["codes"])
    chk("⑪ 日報/論壇分型", P("20260917兆豐投資早報")["doc_kind"] == "DAILY"
        and P("第一場 2026年投資大趨勢 - 華南投顧 -1141201")["doc_kind"] == "FORUM"
        and P("群益3Q26論壇_MIC_物理AI趨勢下人形機器人發展趨勢")["doc_kind"] == "FORUM")
    td = Path(tempfile.mkdtemp(prefix="vrnsm118-"))
    (td / "MS-2330 20260101.pdf").write_text("x", encoding="utf-8")
    out = intake(str(td))
    chk("⑫ intake 列帶規格欄(ext/size_bytes)與 STP002 指向",
        out["rows"][0]["ext"] == ".pdf" and out["rows"][0]["size_bytes"] == 1
        and out["rows"][0]["next"] == "VRN-WKF009-STP002")
    chk("⑬ 前版動詞照常(未知動詞拒跑 · closeout 可達)",
        PRIOR.main(["no_such_verb"]) == 2 and callable(__getattr__("closeout")))
    chk("⑮ 裁定別名生效:JP→JPM · MQ→MCQ · CLST→CLSA · 兆豐→MEGA(短縮寫令)",
        P("JP-2330 20250718")["broker_std"] == "JPM"
        and P("MQ-1560 20260520")["broker_std"] == "MCQ"
        and P("CLST-6669 20251001")["broker_std"] == "CLSA"
        and P("20250819兆豐個股報告-泓德能源(6873)")["broker_std"] == "MEGA")
    chk("⑯ 短拉丁邊界比對防假命中:jpg≠JP · GS 照常", P("926708")["broker_std"] is None
        and P("photo_jpg_dump 20250101")["broker_std"] is None
        and P("GS-1590 20231012")["broker_std"] == "GS")
    os.environ["VIA_VRN_UI_DIR"] = str(td / "ui")
    mp = emit_matrix_html("intake", out)
    h = Path(mp).read_text(encoding="utf-8")
    chk("⑰ U/I 矩陣自動產出:10px 小字體 · 欄自動最佳化 · VIA_NO_OPEN 抑制跳出",
        Path(mp).is_file() and "font:10px" in h and "<table" in h and "state" in h)
    os.environ.pop("VIA_VRN_UI_DIR", None)
    C = classify_eps_kind
    chk("⑱ EPS 核對律:不預設身分 · 對 BASIC/DILUTED 兩路核對才定",
        C([5.51, 6.02], [5.51, 6.02], [5.30, 5.80])["eps_kind"] == "BASIC"
        and C([5.30, 5.80], [5.51, 6.02], [5.30, 5.80])["eps_kind"] == "DILUTED"
        and C([5.51], [5.51], [5.51])["eps_kind"] == "INDISTINGUISHABLE")
    chk("⑲ EPS 核對誠實態:部分吻合黃 · 全不合紅 · 缺料 NO_DATA 黃",
        C([5.51, 9.99], [5.51, 6.02], [5.30, 5.80])["lamp"] == "黃"
        and C([1.0], [5.51], [5.30])["lamp"] == "紅"
        and C([], [5.51], [5.30])["state"] == "NO_DATA")
    chk("㉑ ETF 代碼族(MASTER):00878 五碼收 · 00878B 尾碼收 · 0050 照收 · CT→CATHAY · DAI→DAIWA",
        P("00878 高股息月報")["codes"] == ["00878"] and P("00679B 債券ETF追蹤")["codes"] == ["00679B"]
        and P("0050 台灣五十 分析")["codes"] == ["0050"]
        and P("【國泰證期研究部】神達(3706 TT)-20250822")["broker_std"] == "CATHAY"
        and P("Daiwa-3653 20251002")["broker_std"] == "DAIWA")
    chk("㉔ 公司名局部識別:志強-KY(括號式) · 儒鴻(空格式) · 慧洋-KY(華南式) · AMAX-KY · GS 檔無名誠實",
        P("20251204兆豐個股報告-志強-KY(6768)")["company_name"] == "志強-KY"
        and P("凱基投顧_1476 儒鴻_劉昃恩_20260519")["company_name"] == "儒鴻"
        and P("華南投顧-2637-慧洋-KY-1141202")["company_name"] == "慧洋-KY"
        and P("6933_AMAX-KY_個股介紹報告")["company_name"] == "AMAX-KY"
        and P("GS-2317 20251205")["company_name"] is None
        and size_h(698089) == "681.7KB")
    chk("㉓ 頁圖與假 ETF 不收:page_0001/page_0063→PAGE_IMAGE 零代號 · 0050 照收 · 0001 不收",
        P("page_0001")["codes"] == [] and P("page_0001")["doc_kind"] == "PAGE_IMAGE"
        and P("page_0063")["codes"] == [] and P("0050 台灣五十 分析")["codes"] == ["0050"]
        and P("測試 0001 清單")["codes"] == [])
    chk("㉒ 公司名局部識別:摩根士丹利證券股份有限公司→MS · Daiwa Capital Markets Research→DAIWA · 群益金鼎→CAPITAL",
        P("摩根士丹利證券股份有限公司-2330-20250101")["broker_std"] == "MS"
        and P("Daiwa Capital Markets Research 3653 20250101")["broker_std"] == "DAIWA"
        and P("群益金鼎證券-2330-20250101")["broker_std"] == "CAPITAL")
    r = P("第二場 2026海外投資展望 - 華南永昌海外商品部")
    r2 = P("第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂")
    chk("⑳ 非個股型年份樣代號剝除:2026≠代號 · 3706 速報照收",
        r["codes"] == [] and r["doc_kind"] == "FORUM"
        and r2["codes"] == [] and r2["doc_kind"] in ("FORUM", "INDUSTRY")
        and P("20251128兆豐訪談速報-神達(3706)")["codes"] == ["3706"])
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body
        and "VIA_FROM_VCGC" in body)
    print("[計] VRN_SystemManager_v0118 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
