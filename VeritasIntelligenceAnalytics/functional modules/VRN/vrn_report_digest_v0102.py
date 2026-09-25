#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vrn_report_digest_v0102 — 個股報告摘要批跑器(TOOL-070)
====================================================================
操作員令(批41,2026-08-18):「現在又修復文字功能及摘要功能
請寫每個個股報告摘葉(=摘要)」。
v0100→v0101(批42,2026-08-19):
  ① --collect 歸庫搬移 — 原報告搬入正典新報告夾(預設
     functional modules/VRN/input/reports;gitignore 圈內不入版控)。
     零刪除鐵律:搬移+manifest 存證+--undo 可逆;整合去重:同名
     全同 hash=讓位零動作(原地不動記 DUP)、同名異內容=_sha8
     鏡像收容 byte-exact。
  ② --vdf 串跑 — 摘要矩陣列餵 VDF 輸出樞紐(動態解析最新版)
     六格式輸出+讀回驗證,驗證矩陣一併顯示。
  ③ RICH 矩陣 — 每次跑完的驗證結果以 rich 自動調寬高矩陣顯示
     (欄寬隨內容與終端寬自適應、列高 fold 自動換行;rich 缺席
     graceful 降級純文字,誠實零假裝)。
v0101→v0102(批55/58,2026-08-19):
  ④ TW02 抽取道 — 操作員令「評等RATING 目標價都可以在首頁上左右
     資訊區跟修正後的內文找到 目標價TARGET PRICE也是可在同樣位置
     找到」:動態解析最新 VRN_TW02_ReportParser_v*(嚴禁寫死版號),
     首頁區(first_page_chars)先抽評等/目標價/券商/代碼,未中再
     全文(修正後內文)fallback;RATING_SYNONYMS 中英同義+
     TARGET_PRICE_PATTERN(目標價/合理價/TP/PT/Fair Value+NT$ 千分
     位)。新舊整合鐵則(批58):簡單的先用(v1 中央參數 regex 為
     底)、TW02 為升級層、TW02 缺席 graceful 降級 v1 零假綠;逐欄
     記抽取源(TW02:首頁/TW02:內文/v1)誠實可稽。
原則:
  ① 引擎不重造 — 摘要核心=VRN_ENG062 Summarizer(一標題五點+
     ADJ CLOSE 指標);本批跑器動態解析最新版匯入,零改寫正本。
  ② 黃旗補治 — Summarizer 五點缺句時落預設填充語;本器逐點比對
     填充語清單,命中即加「〔自動生成〕」標註(台帳黃旗結案,
     正本零觸碰=version-forward 外包裝)。
  ③ 參數中央化 — 全參數讀 knowledge/VRN_Digest_Params_v0100.json
     (該冊已入 TOOL-069 中央參數樞紐衝突圈);引擎零寫死。
  ④ 誠實三態 — 逐報告 OK/FAIL/SKIP;pdf 無抽取器=SKIP 誠實;
     ticker 年區 2021-2030 依 LOCKED regex 排除。
  ⑤ 存證 — VIA_Reports/digest_runs/DIGEST_<ts>/:逐報告 .md+
     Digest_Matrix.json;理印 U/I VIA_UI_ReportDigest.html。
用法:
  via-digest --dir <報告夾>       → 批跑(txt/md/docx;pdf 視環境)
  via-digest                      → 掃預設候選夾(冊列)
  via-digest --limit N            → 只跑前 N 件
  via-digest --collect --from <舊夾> [--from <舊夾2>] [--to <新夾>]
                                  → 原報告歸庫搬移(manifest+undo)
  via-digest --undo <manifest>    → 反轉一次歸庫搬移
  via-digest --vdf                → 摘要矩陣串跑 VDF 六格式+驗證
  via-digest --selftest           → 十檢(合成 fixture 零網路)
  via-digest --no-open            → 不開 U/I
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

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VRN
VIA = HERE.parent.parent
PARAMS_PATH = HERE / "knowledge" / "VRN_Digest_Params_v0100.json"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"


def load_params() -> dict:
    return json.loads(PARAMS_PATH.read_text(encoding="utf-8-sig"))


def load_summarizer():
    """動態解析最新 Summarizer(鐵律:嚴禁寫死版號)"""
    hits = sorted(HERE.glob("VRN_ENG062_Summarizer*.py")) or sorted(HERE.glob("VRN_Summarizer_v*.py"))
    if not hits:
        return None, "Summarizer 引擎缺(誠實)"
    eng = hits[-1]
    spec = importlib.util.spec_from_file_location("vrn_summarizer_dyn", eng)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        return None, f"Summarizer 匯入敗:{str(exc)[:80]}"
    return mod, eng.name


def load_tw02():
    """動態解析最新 TW02 ReportParser(批55;嚴禁寫死版號;缺席=誠實降級)"""
    import warnings
    hits = sorted(HERE.glob("VRN_TW02_ReportParser_v*.py"))
    if not hits:
        return None, "TW02 缺(降級 v1 抽取)"
    eng = hits[-1]
    name = "vrn_tw02_dyn"
    spec = importlib.util.spec_from_file_location(name, eng)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # 先掛名再 exec(dataclass 解析需要)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec.loader.exec_module(mod)
    except Exception as exc:
        sys.modules.pop(name, None)
        return None, f"TW02 匯入敗:{str(exc)[:60]}"
    return mod, eng.name


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:動態進度條(單行覆寫,不卡斷)"""
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:44]:<44}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


# ── RICH 自動調寬高矩陣(批42:每次跑出來驗證後的結果都用矩陣顯示)──
def rich_matrix(title: str, columns: list[str], rows: list[list[str]],
                state_col: int | None = None) -> bool:
    """rich Table:欄寬隨內容+終端寬自適應、overflow=fold 列高自動換行;
    state_col 指定狀態欄→OK 綠/SKIP·AUTO 黃/FAIL 紅。rich 缺=誠實降級純文字。"""
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", show_lines=False, pad_edge=False)
        for c in columns:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            cells = [str(x) if x is not None else "—" for x in r]
            if state_col is not None and state_col < len(cells):
                s = cells[state_col]
                color = ("green" if s.startswith(("OK", "MOVED", "COMPAT", "PASS"))
                         else "red" if s.startswith("FAIL")
                         else "yellow")
                cells[state_col] = f"[{color}]{s}[/{color}]"
            t.add_row(*cells)
        Console().print(t)
        return True
    except Exception:
        print(f"  ── {title}(rich 缺席,純文字降級)──")
        print("  " + " | ".join(columns))
        for r in rows:
            print("  " + " | ".join(str(x) if x is not None else "—" for x in r))
        return False


# ── 歸庫搬移(批42:原報告搬新報告夾;零刪除=manifest+undo)──
def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_reports(sources: list[Path], dest: Path, prm: dict,
                    manifest_dir: Path) -> int:
    exts = set(prm["extensions"])
    dest.mkdir(parents=True, exist_ok=True)
    files = []
    for src in sources:
        if not src.exists():
            print(f"  [SKIP] 來源夾缺:{src}(誠實)")
            continue
        files += [p for p in sorted(src.rglob("*"))
                  if p.is_file() and p.suffix.lower() in exts and "_sha" not in p.stem
                  and dest not in p.parents]
    if not files:
        print("  [SKIP] 來源夾零報告件(誠實)")
        return 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    entries = []
    n_mv = n_dup = n_mirror = 0
    for i, p in enumerate(files, 1):
        _sweep(p.name, i, len(files))
        sha = sha256_of(p)
        tgt = dest / p.name
        if tgt.exists():
            if sha256_of(tgt) == sha:      # 全同=讓位零動作(原地不動)
                entries.append({"src": str(p), "dst": "", "sha256": sha, "action": "DUP_SKIP"})
                n_dup += 1
                continue
            tgt = dest / f"{p.stem}_sha{sha[:8]}{p.suffix}"  # 異內容=_sha 鏡像收容
            if tgt.exists() and sha256_of(tgt) == sha:
                entries.append({"src": str(p), "dst": "", "sha256": sha, "action": "DUP_SKIP"})
                n_dup += 1
                continue
            n_mirror += 1
        shutil.move(str(p), str(tgt))
        entries.append({"src": str(p), "dst": str(tgt), "sha256": sha, "action": "MOVED"})
        n_mv += 1
    manifest_dir.mkdir(parents=True, exist_ok=True)
    mf = manifest_dir / f"COLLECT_{ts}_manifest.json"
    mf.write_text(json.dumps({"schema": "VIA.DigestCollect.v1", "ts": ts,
                              "dest": str(dest), "sources": [str(s) for s in sources],
                              "moved": n_mv, "dup_skip": n_dup, "sha_mirror": n_mirror,
                              "entries": entries}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    rich_matrix("歸庫搬移結果(零刪除:manifest+undo 可逆)",
                ["件", "動作", "落點"],
                [[Path(e["src"]).name, e["action"],
                  Path(e["dst"]).name if e["dst"] else "(原地讓位)"] for e in entries],
                state_col=1)
    print(f"  [計] 搬 {n_mv}(內 _sha 鏡像 {n_mirror})· 全同讓位 {n_dup} · manifest {mf.name}")
    print(f"  [undo] via-digest --undo \"{mf}\"")
    return 0


def undo_collect(manifest: Path) -> int:
    if not manifest.exists():
        print(f"  [FAIL] manifest 不存在:{manifest}")
        return 1
    d = json.loads(manifest.read_text(encoding="utf-8"))
    n_back = n_skip = 0
    for e in reversed(d["entries"]):
        if e["action"] != "MOVED" or not e["dst"]:
            continue
        src, dst = Path(e["src"]), Path(e["dst"])
        if not dst.exists() or src.exists():
            n_skip += 1
            continue
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dst), str(src))
        n_back += 1
    print(f"  [計] undo 還原 {n_back} · 略過 {n_skip}(落點缺/原位已有,誠實)")
    return 0


# ── VDF 串跑(批42:VDF 可以試跑;摘要矩陣列→六格式輸出+驗證)──
def build_vdf_rows(matrix: dict) -> list[dict]:
    rows = []
    for r in matrix["rows"]:
        if r["state"] != "OK":
            continue
        rows.append({"ReportCode": r.get("report_code", ""), "Ticker": r.get("ticker", ""),
                     "Name": r.get("name", "") or "", "Broker": r.get("broker", "") or "",
                     "Rating": r.get("rating", "") or "",
                     "TargetPrice": r.get("target_price"), "AdjClose": r.get("adj_close"),
                     "UpsidePct": r.get("upside_pct"), "AutoFilled": r.get("auto_filled", 0),
                     "File": r["file"], "Headline": r.get("headline", "")})
    return rows


def run_vdf_chain(matrix: dict, run_dir: Path) -> int:
    rows = build_vdf_rows(matrix)
    if not rows:
        print("  [SKIP] VDF 串跑:零 OK 列可餵(誠實)")
        return 0
    vdf_dir = VIA / "functional modules/VDF"
    hubs = sorted(vdf_dir.glob("VDF_ENG045_OutputHub_v0*.py"))  # 動態解析最新版(鐵律)
    if not hubs:
        print("  [SKIP] VDF 輸出樞紐缺(誠實)")
        return 0
    rows_json = run_dir / "digest_vdf_rows.json"
    rows_json.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, str(hubs[-1]), str(rows_json)],
                       capture_output=True, text=True, timeout=600, cwd=str(vdf_dir))
    evs = sorted((VIA / "VIA_Reports" / "vdfout_runs").glob("VDFOUT_*.json"))
    if r.returncode == 0 and evs:
        m = json.loads(evs[-1].read_text(encoding="utf-8"))["matrix"]
        rich_matrix(f"VDF 六格式輸出+讀回驗證矩陣({len(rows)} 摘要列)",
                    ["表", "格式", "狀態", "列數", "位元組", "檔"],
                    [[x["table"], x["format"], x["status"], x["rows"], x["bytes"], x["file"]]
                     for x in m], state_col=2)
        ok = sum(1 for x in m if str(x["status"]).startswith(("OK", "COMPAT")))
        print(f"  [計] VDF 格式出 {ok}/{len(m)} 綠 · 存證 {evs[-1].name}")
        return 0
    print(f"  [FAIL] VDF 串跑 rc={r.returncode}:{(r.stderr or r.stdout).strip()[-120:]}")
    return 1


# ── 文字抽取(修復後文字功能之最小自足道;docx 零外依)──────
def extract_text(p: Path) -> tuple[str, str]:
    """回 (text, state);state ∈ OK / SKIP:<因>"""
    ext = p.suffix.lower()
    if ext in (".txt", ".md"):
        for enc in ("utf-8-sig", "cp950", "big5", "latin-1"):
            try:
                return p.read_text(encoding=enc), "OK"
            except (UnicodeDecodeError, LookupError):
                continue
        return "", "SKIP:編碼不明"
    if ext == ".docx":
        try:
            with zipfile.ZipFile(p) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            xml = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", "", xml)
            return re.sub(r"\n{3,}", "\n\n", text).strip(), "OK"
        except Exception as exc:
            return "", f"SKIP:docx 讀取敗 {str(exc)[:40]}"
    if ext == ".pdf":
        try:
            import pypdf  # 環境有則用;無=誠實 SKIP
            reader = pypdf.PdfReader(str(p))
            return "\n".join((pg.extract_text() or "") for pg in reader.pages), "OK"
        except ImportError:
            return "", "SKIP:pdf 抽取器缺(pypdf)"
        except Exception as exc:
            return "", f"SKIP:pdf 讀取敗 {str(exc)[:40]}"
    return "", f"SKIP:副檔名不支援 {ext}"


# ── 元資料收割(檔名+內文;LOCKED regex 年區排除)────────────
def harvest_meta(p: Path, text: str, prm: dict, broker_dict: dict,
                 tw02=None) -> dict:
    pats = prm["meta_patterns"]
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])  # LOCKED 第一支放行四碼,年區須疊拒絕閘(字庫 v0101 同法)
    hay = p.stem + "\n" + text[:3000]
    meta = {}
    for cand in re.findall(pats["ticker_candidate"], hay):
        if locked.match(cand) and not year.match(cand):
            meta["ticker"] = cand
            break
    m = re.search(pats["target_price"], text)
    if m:
        meta["target_price"] = float(m.group(1).replace(",", ""))
    m = re.search(pats["rating"], text)
    if m:
        meta["rating"] = m.group(1)
    m = re.search(pats["eps_current"], text)
    if m:
        meta["eps_current"] = float(m.group(1))
    m = re.search(pats["report_date"], hay)
    if m:
        d = re.sub(r"[-/\.]", "", m.group(1))
        meta["report_date"] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    for broker in broker_dict:
        if broker and broker in hay:
            meta["broker"] = broker
            break
    # ── TW02 升級層(批55 令:評等/目標價=首頁上左右資訊區→修正後內文)──
    meta["src"] = {}
    if tw02 is not None:
        fp = text[:prm["first_page_chars"]]
        try:
            page = tw02.PageParser.parse_first_page(fp)
        except Exception:
            page = {}
        if not meta.get("ticker") and page:
            tk = page.get("tickers", {})
            cand = ([c.split(".")[0] for c in tk.get("tw_yfinance", [])]
                    or [c.replace(" TT", "") for c in tk.get("tw_bloomberg", [])]
                    or tk.get("tw_pure", []))
            if cand:
                meta["ticker"] = cand[0]
                meta["src"]["ticker"] = "TW02:首頁"
        m = tw02.RATING_PATTERN.search(fp)
        where = "TW02:首頁"
        if not m:
            m = tw02.RATING_PATTERN.search(text)
            where = "TW02:內文"
        if m:
            raw = m.group(1)
            meta["rating"] = raw  # Summarizer 用原字(誠實原貌)
            low = raw.lower()
            meta["rating_class"] = next(
                (c for c, syns in tw02.RATING_SYNONYMS.items()
                 if raw in syns or low in [x.lower() for x in syns]), None)
            meta["src"]["rating"] = where
        m = tw02.TARGET_PRICE_PATTERN.search(fp)
        where = "TW02:首頁"
        if not m:
            m = tw02.TARGET_PRICE_PATTERN.search(text)
            where = "TW02:內文"
        if m:
            try:
                meta["target_price"] = float(m.group(1).replace(",", ""))
                meta["src"]["target_price"] = where
            except ValueError:
                pass
        if not meta.get("broker") and page.get("broker"):
            meta["broker"] = page["broker"]
            meta["src"]["broker"] = "TW02:首頁"
    return meta


def tag_fillers(summary, prm: dict) -> tuple[int, dict]:
    """五點逐比填充語;命中加〔自動生成〕標註(正本 dataclass 就地
    改欄位值=本器輸出物,Summarizer 引擎零觸碰)"""
    tag = prm["filler_tag"]
    fillers = set(prm["filler_phrases"])
    p1_rx = re.compile(prm["point1_fallback_regex"])
    fields = ["point_1_conclusion", "point_2_growth", "point_3_valuation",
              "point_4_peers", "point_5_risk"]
    n = 0
    flags = {}
    for f in fields:
        v = getattr(summary, f, "") or ""
        auto = v in fillers or (f == "point_1_conclusion" and bool(p1_rx.match(v)))
        flags[f] = "AUTO" if auto else "TEXT"
        if auto and tag not in v:
            setattr(summary, f, f"{v}{tag}")
            n += 1
    return n, flags


# ── 批跑 ─────────────────────────────────────────────────────
def run_batch(report_dir: Path, limit: int | None, no_open: bool,
              out_root: Path | None = None) -> tuple[int, dict | None, Path | None]:
    prm = load_params()
    mod, eng_name = load_summarizer()
    if mod is None:
        print(f"  [FAIL] {eng_name}")
        return 1, None, None
    tw02, tw02_name = load_tw02()
    print(f"  [引擎] {eng_name} · 參數冊 {PARAMS_PATH.name}(中央化)"
          f" · 抽取道 {tw02_name if tw02 else 'v1(' + tw02_name + ')'}")
    exts = set(prm["extensions"])
    files = sorted(p for p in report_dir.rglob("*")
                   if p.is_file() and p.suffix.lower() in exts and "_sha" not in p.stem)
    if limit:
        files = files[:limit]
    if not files:
        print(f"  [SKIP] {report_dir} 內零報告件(誠實;支援 {'/'.join(sorted(exts))})")
        return 0, None, None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or (VIA / prm["output_root"])) / f"DIGEST_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    broker_dict = getattr(mod, "BROKER_ABBR_DICT", {})
    rows = []
    n_ok = n_fail = n_skip = 0
    for i, p in enumerate(files, 1):
        _sweep(p.name, i, len(files))
        text, state = extract_text(p)
        if state != "OK" or not text.strip():
            n_skip += 1
            rows.append({"file": p.name, "state": state if state != "OK" else "SKIP:空文",
                         "ticker": "", "headline": ""})
            continue
        try:
            meta = harvest_meta(p, text, prm, broker_dict, tw02)
            fp = text[:prm["first_page_chars"]]
            rest = text[prm["first_page_chars"]:]
            summary = mod.summarize_report(
                ticker=meta.get("ticker", ""), first_page_text=fp, remaining_text=rest,
                broker=meta.get("broker", ""), report_date=meta.get("report_date", ""),
                filename=p.name, target_price=meta.get("target_price"),
                rating=meta.get("rating", ""), eps_current=meta.get("eps_current"))
            n_auto, flags = tag_fillers(summary, prm)
            stem = (summary.report_code or p.stem).replace("/", "_")
            md_path = run_dir / f"{stem}_digest.md"
            md_path.write_text(summary.to_markdown() + "\n", encoding="utf-8")
            n_ok += 1
            rows.append({"file": p.name, "state": "OK", "ticker": summary.ticker,
                         "name": summary.name, "broker": summary.broker,
                         "rating": summary.rating, "target_price": summary.target_price,
                         "adj_close": summary.adj_close, "upside_pct": summary.upside_pct,
                         "report_code": summary.report_code, "headline": summary.headline,
                         "auto_filled": n_auto, "point_flags": flags,
                         "extract_src": meta.get("src", {}),
                         "rating_class": meta.get("rating_class"),
                         "src_disp": "·".join(sorted({v for v in meta.get("src", {}).values()})) or "v1",
                         "md": md_path.name})
        except Exception as exc:
            n_fail += 1
            rows.append({"file": p.name, "state": f"FAIL:{str(exc)[:60]}",
                         "ticker": "", "headline": ""})
    matrix = {"schema": "VIA.ReportDigest.v2", "ts": ts, "dir": str(report_dir),
              "engine": eng_name, "extractor": tw02_name if tw02 else "v1",
              "total": len(files),
              "ok": n_ok, "fail": n_fail, "skip": n_skip, "rows": rows}
    (run_dir / "Digest_Matrix.json").write_text(
        json.dumps(matrix, ensure_ascii=False, indent=1), encoding="utf-8")
    ui = render_ui(matrix, run_dir, prm)
    rich_matrix(f"摘要批跑驗證矩陣 · {ts}(五點黃=填充語{prm['filler_tag']})",
                ["檔", "態", "代碼", "名", "評等", "目標價", "抽取源", "上漲%", "自動填充", "標題"],
                [[r["file"], r["state"], r.get("ticker", ""), r.get("name", "") or "",
                  r.get("rating", "") or "", r.get("target_price"), r.get("src_disp", ""),
                  r.get("upside_pct"), r.get("auto_filled", ""),
                  (r.get("headline", "") or "")[:44]]
                 for r in rows], state_col=1)
    print(f"  [計] 報告 {len(files)} · OK {n_ok} · FAIL {n_fail} · SKIP {n_skip}(誠實三態)")
    print(f"  [存] {run_dir.relative_to(VIA) if run_dir.is_relative_to(VIA) else run_dir}"
          f" · U/I {ui.name}")
    if not no_open:
        try:
            import webbrowser
            webbrowser.open(ui.as_uri())
        except Exception:
            pass
    return (1 if n_fail else 0), matrix, run_dir


# ── 理印紙墨 U/I ──────────────────────────────────────────────
CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1280px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}.dim{color:#6b6a64}
"""


def render_ui(matrix: dict, run_dir: Path, prm: dict) -> Path:
    rows = []
    for r in matrix["rows"]:
        st = r["state"]
        cls = "ok" if st == "OK" else ("bad" if st.startswith("FAIL") else "warn")
        flags = r.get("point_flags", {})
        dots = "".join(
            f"<span class='{'warn' if flags.get(f) == 'AUTO' else 'ok'}'>●</span>"
            for f in ["point_1_conclusion", "point_2_growth", "point_3_valuation",
                      "point_4_peers", "point_5_risk"]) if flags else "—"
        rows.append(
            f"<tr><td class='mono dim'>{r['file']}</td><td class='{cls}'>{st}</td>"
            f"<td class='mono'>{r.get('ticker', '')}</td><td>{r.get('name', '') or ''}</td>"
            f"<td>{r.get('broker', '') or ''}</td><td>{r.get('rating', '') or ''}</td>"
            f"<td>{r.get('target_price', '') or ''}</td>"
            f"<td class='mono dim'>{r.get('src_disp', '') or ''}</td>"
            f"<td>{r.get('upside_pct', '') or ''}</td>"
            f"<td>{dots}</td><td class='dim'>{(r.get('headline', '') or '')[:60]}</td></tr>")
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VRN 個股報告摘要矩陣</title><style>{CSS}</style></head><body>
<div class="card"><h1>個股報告摘要矩陣 · Report Digest</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">批次 {matrix['ts']} · 來源 {matrix['dir']} · 引擎 {matrix['engine']}
 · 報告 {matrix['total']}(OK {matrix['ok']} / FAIL {matrix['fail']} / SKIP {matrix['skip']})
 · 五點燈:綠=原文抽句 / 黃=填充語{prm['filler_tag']}標註</div>
<table><tr><th>檔</th><th>態</th><th>代碼</th><th>名</th><th>券商</th><th>評等</th>
<th>目標價</th><th>抽取源</th><th>上漲%</th><th>五點</th><th>標題</th></tr>{''.join(rows)}</table></div>
</body></html>"""
    out = run_dir / prm["ui_name"]
    out.write_text(html, encoding="utf-8")
    return out


# ── 七檢自測(合成 fixture 零網路)───────────────────────────
FIXTURE_FULL = """數位測試工業 投資報告
評等:買進 (維持)
目標價:250 元
2026-01-15
AI 應用需求強勁,先進封裝訂單能見度達兩季。
預估 EPS 12.5 元,年增 18%。
成長動能:高速運算產品線放量,市佔持續提升。
財務預估:毛利率站穩 42%,ROE 20% 以上。
同業比較:相較同業 A 公司與 B 公司,產品組合較優。
風險因子:留意庫存去化不如預期與匯率波動。
"""

FIXTURE_SPARSE = """測試精機
簡評:產業復甦初期。
"""

# 批55 令 fixture:首頁上左右資訊區(英式評等+NT$ 千分位目標價)
FIXTURE_TW02_HEAD = """統一測試科技 (2377.TW) 投資報告
Rating: Overweight    Target Price: NT$1,200
分析師觀點:伺服器散熱需求強勁,訂單能見度高。
"""

# 批55 令 fixture:首頁無評等目標價,修正後內文才有(合理價變體)
FIXTURE_TW02_BODY = """測試應材 6180
本季表現平穩,首頁資訊區無評等揭示。
""" + "填充行。\n" * 600 + """
經修正後之內文評價:我們認為合理價 850 元具吸引力,評等調整為 買進。
"""


def selftest() -> int:
    import shutil
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    prm = load_params()
    # ① 參數冊中央化在位:必備鍵齊
    need = {"first_page_chars", "filler_phrases", "filler_tag", "meta_patterns",
            "tw_ticker_locked", "output_root"}
    chk("參數冊必備鍵", need <= set(prm.keys()), f"({PARAMS_PATH.name})")

    # ② Summarizer 動態解析可匯入
    mod, eng_name = load_summarizer()
    chk("Summarizer 動態匯入", mod is not None, f"({eng_name})")
    if mod is None:
        print("  [計] 七檢中止(引擎缺)")
        return 1

    # ③ ticker 年區閘=LOCKED 收+YEAR_SUSPECT 拒疊閘:2330 收、2025 拒
    locked = re.compile(prm["tw_ticker_locked"])
    year = re.compile(prm["year_suspect"])
    gate = lambda s: bool(locked.match(s)) and not year.match(s)
    chk("ticker 年區閘", gate("2330") and not gate("2025"))

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        rpt = sand / "reports"
        rpt.mkdir()
        (rpt / "2330_數位測試工業_20260115.txt").write_text(FIXTURE_FULL, encoding="utf-8")
        (rpt / "1560_測試精機.txt").write_text(FIXTURE_SPARSE, encoding="utf-8")
        # 合成 docx(zip+document.xml;零外依)
        dx = rpt / "3661_合成docx報告.docx"
        with zipfile.ZipFile(dx, "w") as z:
            z.writestr("word/document.xml",
                       "<w:document><w:p><w:t>合成docx 目標價:300 元 評等:持有</w:t></w:p>"
                       "<w:p><w:t>風險因子:留意需求波動。</w:t></w:p></w:document>")
        (rpt / "空文報告.txt").write_text("", encoding="utf-8")  # SKIP 態觸發件(空文;兩端環境穩定)

        # ④ docx 抽取道通
        text, state = extract_text(dx)
        chk("docx 抽取(零外依)", state == "OK" and "目標價" in text)

        # ⑤ 元資料收割:ticker/目標價/評等/日期
        meta = harvest_meta(rpt / "2330_數位測試工業_20260115.txt", FIXTURE_FULL, prm,
                            getattr(mod, "BROKER_ABBR_DICT", {}))
        chk("元資料收割", meta.get("ticker") == "2330" and meta.get("target_price") == 250.0
            and meta.get("rating") == "買進" and meta.get("report_date") == "2026-01-15")

        # ⑥ 批跑三態+黃旗標註:sparse 件五點必有 AUTO 標
        rc, mx_out, _rd = run_batch(rpt, limit=None, no_open=True, out_root=sand / "out")
        runs = sorted((sand / "out").glob("DIGEST_*"))
        ok6 = bool(runs) and rc == 0
        if ok6:
            mx = json.loads((runs[-1] / "Digest_Matrix.json").read_text(encoding="utf-8"))
            sparse = next((r for r in mx["rows"] if r["file"].startswith("1560")), {})
            ok6 = (mx["ok"] >= 3 and mx["fail"] == 0 and mx["skip"] == 1
                   and sparse.get("auto_filled", 0) >= 3)
        chk("批跑三態+填充語標註", ok6)

        # ⑦ 產物齊:逐報告 md 含標註、U/I 含銘言
        ok7 = False
        if runs:
            mds = list(runs[-1].glob("*_digest.md"))
            ui = runs[-1] / prm["ui_name"]
            ok7 = (len(mds) >= 3 and ui.exists()
                   and MOTTO in ui.read_text(encoding="utf-8")
                   and any(prm["filler_tag"] in m.read_text(encoding="utf-8") for m in mds))
        chk("md+U/I 產物齊", ok7)

        # ⑧ 歸庫搬移:MOVED+全同讓位 DUP_SKIP+異內容 _sha 鏡像+manifest
        old1, old2 = sand / "old1", sand / "old2"
        newlib = sand / "newlib"
        old1.mkdir(); old2.mkdir()
        (old1 / "甲報告.txt").write_text(FIXTURE_FULL, encoding="utf-8")
        (old2 / "甲報告.txt").write_text(FIXTURE_FULL, encoding="utf-8")      # 全同=讓位
        (old2 / "乙報告.txt").write_text(FIXTURE_SPARSE, encoding="utf-8")
        (newlib / "").parent.mkdir(exist_ok=True)
        (newlib).mkdir(exist_ok=True)
        (newlib / "乙報告.txt").write_text("既存異內容", encoding="utf-8")     # 異內容=_sha 鏡像
        collect_reports([old1, old2], newlib, prm, sand / "mf")
        mfs = sorted((sand / "mf").glob("COLLECT_*_manifest.json"))
        ok8 = False
        if mfs:
            md_ = json.loads(mfs[-1].read_text(encoding="utf-8"))
            ok8 = (md_["moved"] == 2 and md_["dup_skip"] == 1 and md_["sha_mirror"] == 1
                   and (newlib / "甲報告.txt").exists()
                   and (old2 / "甲報告.txt").exists()          # 讓位=原地不動
                   and len(list(newlib.glob("乙報告_sha*.txt"))) == 1)
        chk("歸庫搬移(MOVED/讓位/_sha鏡像/manifest)", ok8)

        # ⑨ undo 可逆:MOVED 件全數回原位
        rc9 = undo_collect(mfs[-1]) if mfs else 1
        chk("undo 還原可逆", rc9 == 0 and (old1 / "甲報告.txt").exists()
            and (old2 / "乙報告.txt").exists()
            and not list(newlib.glob("乙報告_sha*.txt")))

        # ⑩ VDF 列建構+RICH 渲染道通(rich 缺=graceful 降級亦過)
        vrows = build_vdf_rows(mx_out) if mx_out else []
        ok10 = (len(vrows) == 3 and all("Ticker" in r for r in vrows)
                and json.dumps(vrows, ensure_ascii=False))
        rich_matrix("渲染道通測試", ["a", "b"], [["x", "OK"]], state_col=1)
        chk("VDF 列建構+RICH 渲染", bool(ok10))
        # ⑪ TW02 抽取道:首頁區英式評等+NT$ 千分位目標價(批55 令)
        tw02, tw02_name = load_tw02()
        ok11 = tw02 is not None
        if ok11:
            m11 = harvest_meta(rpt / "2330_數位測試工業_20260115.txt",
                               FIXTURE_TW02_HEAD, prm, {}, tw02)
            ok11 = (m11.get("rating") == "Overweight"
                    and m11.get("rating_class") == "BUY"
                    and m11.get("target_price") == 1200.0
                    and m11.get("src", {}).get("rating") == "TW02:首頁"
                    and m11.get("src", {}).get("target_price") == "TW02:首頁")
        chk("TW02 首頁區抽取(Overweight→BUY+NT$1,200)", ok11, f"({tw02_name})")

        # ⑫ TW02 內文 fallback(合理價變體)+TW02 缺席降級 v1 不假綠
        ok12 = tw02 is not None
        if ok12:
            m12 = harvest_meta(rpt / "1560_測試精機.txt",
                               FIXTURE_TW02_BODY, prm, {}, tw02)
            m_no = harvest_meta(rpt / "2330_數位測試工業_20260115.txt",
                                FIXTURE_FULL, prm, {}, None)  # 降級道
            ok12 = (m12.get("target_price") == 850.0
                    and m12.get("src", {}).get("target_price") == "TW02:內文"
                    and m12.get("rating") == "買進"
                    and m_no.get("target_price") == 250.0
                    and m_no.get("rating") == "買進"
                    and m_no.get("src") == {})
        chk("TW02 內文fallback(合理價850)+缺席降級v1", ok12)
    n = 12 - len(fails)
    print(f"  [計] 十二檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 個股報告摘要批跑器 v0102 · 十二檢自測(合成 fixture 零網路)===")
        return selftest()
    if "--undo" in args:
        i = args.index("--undo")
        if i + 1 >= len(args):
            print("[用法] via-digest --undo <manifest路徑>")
            return 2
        print("=== 歸庫搬移 undo(零刪除鐵律)===")
        return undo_collect(Path(args[i + 1]))
    if "--collect" in args:
        prm = load_params()
        sources = [Path(args[i + 1]) for i, a in enumerate(args)
                   if a == "--from" and i + 1 < len(args)]
        if not sources:
            print("[用法] via-digest --collect --from <舊報告夾> [--from <舊夾2>] [--to <新夾>]")
            return 2
        dest = (Path(args[args.index("--to") + 1]) if "--to" in args
                else VIA / "functional modules/VRN/input/reports")
        print(f"=== 原報告歸庫搬移 → {dest}(manifest+undo;全同讓位/_sha 鏡像)===")
        return collect_reports(sources, dest, prm, VIA / prm["output_root"])
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1]) if i + 1 < len(args) else None
    no_open = "--no-open" in args
    prm = load_params()
    if "--dir" in args:
        i = args.index("--dir")
        report_dir = Path(args[i + 1]) if i + 1 < len(args) else None
        if not report_dir or not report_dir.exists():
            print(f"  [FAIL] 報告夾不存在:{report_dir}")
            return 1
    else:
        report_dir = next((VIA / d for d in prm["default_scan_dirs"]
                           if (VIA / d).exists()), None)
        if report_dir is None:
            print("  [SKIP] 未指定 --dir 且預設候選夾皆缺(誠實):")
            for d in prm["default_scan_dirs"]:
                print(f"         · {d}")
            return 0
        print(f"  [夾] 未指定 --dir,用預設候選:{report_dir.relative_to(VIA)}")
    print(f"=== 個股報告摘要批跑器 v0102 · 一標題五點+TW02 抽取道(TOOL-070)===")
    rc, matrix, run_dir = run_batch(report_dir, limit, no_open)
    if "--vdf" in args and matrix and run_dir:
        rc = max(rc, run_vdf_chain(matrix, run_dir))
    return rc


if __name__ == "__main__":
    sys.exit(main())
