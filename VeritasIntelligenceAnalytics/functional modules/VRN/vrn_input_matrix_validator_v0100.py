# -*- coding: utf-8 -*-
"""vrn_input_matrix_validator_v0100.py — VRN 輸入矩陣驗證引擎 v0100(操作員令 2026-08-13:VRN 一起進行)。

流程:輸入=一個資料夾(操作員端由 via-vrn-intake 的 Windows 資料夾選擇器指定;CLI 直接給路徑)
  ① 總輸入矩陣:逐檔規格(名/類型/大小/sha12/列×欄/編碼)
  ② 擷取驗證:可解析性 · 必要欄(date|year + ticker|code)· 整列重複 · 空值率
  ③ 分類:BASICINFO / FINANCIALDATA / ESTIMATE(預估:欄名含 estimate/forecast/consensus/target)/ OTHER
  ④ 正典規則「歷史值蓋過預估值」:同 (ticker, period, metric) 之實際值存在 → 預估值標 SUPERSEDED_BY_ACTUAL;
     僅預估 → ESTIMATE_ONLY;僅實際 → VERIFIED_ACTUAL。零改寫輸入(唯讀;報告 only)。
  ⑤ 輸出:vrn_input_matrix_<ts>.json + 驗證狀態頁 vrn_input_matrix_<ts>.html(視覺鎖 · 零 CDN)
政策:唯讀輸入 · no_fake_fill · NO_CANONICAL_MUTATION · 誠實 OK/WARN/FAIL 不卡斷。
用法:py vrn_input_matrix_validator_v0100.py <輸入資料夾> [--out 輸出資料夾]
"""
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

EST_MARKERS = ("estimate", "forecast", "consensus", "target", "預估", "預測", "目標")
ACT_MARKERS = ("actual", "實際", "歷史")
T = {"bg": "#f2f1ec", "paper": "#ffffff", "ink": "#1b1a17", "ink2": "#33403f",
     "mut": "#6b6860", "line": "#dbd9d3", "line2": "#ebe9e3", "seal": "#9e2b25",
     "teal": "#3c6660", "down": "#3d7a52", "amber": "#8a6420"}


def sniff(path):
    """逐檔規格+可解析性(唯讀)。"""
    info = {"file": path.name, "type": path.suffix.lower().lstrip(".") or "?",
            "bytes": path.stat().st_size, "sha12": "", "rows": None, "cols": None,
            "encoding": "", "headers": [], "gates": [], "verdict": "OK"}
    raw = path.read_bytes()
    info["sha12"] = hashlib.sha256(raw).hexdigest()[:12]
    enc = "utf-8-sig" if raw[:3] == b"\xef\xbb\xbf" else "utf-8"
    try:
        text = raw.decode(enc)
        info["encoding"] = enc
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp950")
            info["encoding"] = "cp950"
        except UnicodeDecodeError:
            info["encoding"] = "binary"
            info["gates"].append(("decode", "FAIL", "非文字或未知編碼"))
            info["verdict"] = "FAIL"
            return info, None
    rows = None
    if info["type"] == "csv":
        rows = list(csv.reader(text.splitlines()))
    elif info["type"] == "json":
        try:
            j = json.loads(text)
            if isinstance(j, list) and j and isinstance(j[0], dict):
                heads = list(j[0].keys())
                rows = [heads] + [[str(r.get(h, "")) for h in heads] for r in j]
            else:
                info["gates"].append(("shape", "WARN", "JSON 非表列型 — 規格記錄 only"))
                info["rows"] = 1
                return info, None
        except Exception as e:
            info["gates"].append(("parse", "FAIL", "JSON 解析失敗:%s" % e))
            info["verdict"] = "FAIL"
            return info, None
    else:
        info["gates"].append(("type", "WARN", "非 csv/json — 規格記錄 only"))
        return info, None
    if not rows or len(rows) < 2:
        info["gates"].append(("rows", "FAIL", "無資料列"))
        info["verdict"] = "FAIL"
        return info, None
    heads = [h.strip().lower() for h in rows[0]]
    info["headers"] = heads
    info["rows"] = len(rows) - 1
    info["cols"] = len(heads)
    # 必要欄
    has_key = any(k in h for h in heads for k in ("ticker", "code", "代號", "股票"))
    has_time = any(k in h for h in heads for k in ("date", "year", "period", "日期", "年度", "期別"))
    info["gates"].append(("key欄", "OK" if has_key else "WARN", "ticker/code" if has_key else "無識別欄"))
    info["gates"].append(("time欄", "OK" if has_time else "WARN", "date/period" if has_time else "無期別欄"))
    # 整列重複
    body = ["\x1f".join(r) for r in rows[1:]]
    ndup = len(body) - len(set(body))
    info["gates"].append(("整列重複", "OK" if ndup == 0 else "WARN", "%d 列" % ndup))
    # 空值率
    cells = sum(len(r) for r in rows[1:]) or 1
    empty = sum(1 for r in rows[1:] for v in r if not str(v).strip())
    er = empty / cells
    info["gates"].append(("空值率", "OK" if er < .2 else "WARN", "%.1f%%" % (er * 100)))
    if any(g[1] == "FAIL" for g in info["gates"]):
        info["verdict"] = "FAIL"
    elif any(g[1] == "WARN" for g in info["gates"]):
        info["verdict"] = "WARN"
    return info, rows


def classify(info):
    n = info["file"].lower()
    h = " ".join(info["headers"])
    if any(m in n or m in h for m in EST_MARKERS):
        return "ESTIMATE"
    if "financial" in n or "財務" in n or any(k in h for k in ("revenue", "eps", "資產", "損益", "淨利")):
        return "FINANCIALDATA"
    if "basic" in n or "basicinfo" in n or "基本" in n or any(k in h for k in ("name", "industry", "產業", "名稱")):
        return "BASICINFO"
    return "OTHER"


def key_cells(rows, heads):
    """抽 (ticker, period, metric)→值 供實際/預估對帳(metric=數值欄名)。"""
    def col(*names):
        for i, h in enumerate(heads):
            if any(n in h for n in names):
                return i
        return None
    ck = col("ticker", "code", "代號")
    pk = col("date", "year", "period", "年度", "期別")
    out = {}
    if ck is None or pk is None:
        return out
    for r in rows[1:]:
        if len(r) <= max(ck, pk):
            continue
        for i, h in enumerate(heads):
            if i in (ck, pk) or not str(r[i]).strip():
                continue
            try:
                float(str(r[i]).replace(",", ""))
            except ValueError:
                continue
            out[(r[ck].strip(), r[pk].strip(), h)] = r[i]
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = Path(argv[1])
    if not src.is_dir():
        print("[FAIL] 輸入資料夾不在位:%s" % src)
        return 2
    out_dir = Path(argv[argv.index("--out") + 1]) if "--out" in argv else src / "_vrn_intake_out"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    matrix = []
    actual_keys = {}
    est_files = []
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        info, rows = sniff(p)
        info["class"] = classify(info) if rows else ("OTHER" if info["verdict"] != "FAIL" else "INVALID")
        if rows:
            if info["class"] in ("FINANCIALDATA", "BASICINFO"):
                actual_keys.update({k: info["file"] for k in key_cells(rows, info["headers"])})
            elif info["class"] == "ESTIMATE":
                est_files.append((info, key_cells(rows, info["headers"])))
        matrix.append(info)

    # ④ 歷史值蓋過預估值
    for info, cells in est_files:
        sup = sum(1 for k in cells if k in actual_keys)
        only = len(cells) - sup
        info["actual_override"] = {"superseded_by_actual": sup, "estimate_only": only}
        info["status_label"] = ("SUPERSEDED_BY_ACTUAL %d · ESTIMATE_ONLY %d" % (sup, only)) if cells else "ESTIMATE(無可對帳鍵)"
    for info in matrix:
        if info["class"] in ("FINANCIALDATA", "BASICINFO") and info["verdict"] != "FAIL":
            info["status_label"] = "VERIFIED_ACTUAL(%s)" % info["verdict"]
        elif info["class"] == "ESTIMATE":
            pass
        else:
            info["status_label"] = info["verdict"]

    ok = sum(1 for m in matrix if m["verdict"] == "OK")
    warn = sum(1 for m in matrix if m["verdict"] == "WARN")
    fail = sum(1 for m in matrix if m["verdict"] == "FAIL")
    report = {"version": "v0100", "generated_at": datetime.now().isoformat(timespec="seconds"),
              "input_dir": str(src), "files": len(matrix), "ok": ok, "warn": warn, "fail": fail,
              "policy": ["read-only inputs", "no_fake_fill", "NO_CANONICAL_MUTATION",
                         "historical actuals override estimates (report-only, 零改寫)"],
              "matrix": matrix}
    jp = out_dir / ("vrn_input_matrix_%s.json" % ts)
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    # ⑤ 狀態頁
    rows_html = ""
    for m in matrix:
        gates = " · ".join("%s:%s(%s)" % g for g in m["gates"]) or "—"
        badge = {"OK": "g", "WARN": "a", "FAIL": "r"}[m["verdict"]]
        rows_html += ('<tr><td class="mono">%s</td><td>%s</td><td class="r">%s</td>'
                      '<td class="r">%s</td><td class="r">%s</td><td class="mono">%s</td>'
                      '<td class="small">%s</td><td><span class="tag %s">%s</span></td></tr>'
                      % (m["file"], m["class"], m["type"], "{:,}".format(m["bytes"]),
                         ("%s×%s" % (m["rows"], m["cols"])) if m["rows"] else "—",
                         m["sha12"], gates, badge, m.get("status_label", m["verdict"])))
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN 輸入矩陣驗證 %(ts)s</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",system-ui,sans-serif;font-size:12.5px;padding:16px 20px;max-width:1180px;margin:0 auto}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:20px;font-weight:500;letter-spacing:.055em;color:%(ink)s;border-bottom:1px solid #dcdad3;padding-bottom:10px;margin-bottom:12px}
h1 .seal{display:inline-block;width:30px;height:30px;background:%(seal)s;border-radius:5px;color:%(bg)s;font-family:'Noto Serif CJK TC',serif;font-size:17px;line-height:30px;text-align:center;margin-right:9px;vertical-align:-6px}
table{width:100%%;border-collapse:collapse;font-size:11.5px;background:%(paper)s;border:1px solid %(line)s;border-radius:8px}
th,td{text-align:left;border-bottom:1px solid %(line2)s;padding:6px 8px;vertical-align:top}
th{color:%(mut)s;font-size:10px;text-transform:uppercase;font-family:Consolas,monospace}
.r{text-align:right}.mono{font-family:Consolas,monospace;font-size:11px}.small{font-size:10.5px;color:%(mut)s}
.tag{display:inline-block;padding:1px 8px;border-radius:9px;font-family:Consolas,monospace;font-size:9px;font-weight:700}
.tag.g{background:#e6efec;color:#2c4f4a}.tag.a{background:#f2ecdd;color:#6f5c31}.tag.r{background:#f3e7e6;color:%(seal)s}
.sum{font-family:Consolas,monospace;font-size:11px;color:%(mut)s;margin:8px 0 12px}
.ft{font-family:Consolas,monospace;font-size:9.5px;color:%(mut)s;border-top:1px solid %(line)s;padding-top:8px;margin-top:12px;text-align:center}
</style></head><body>
<h1><span class="seal">驗</span>VRN 輸入矩陣驗證 · Input Matrix Validation</h1>
<div class="sum">輸入:%(src)s · 檔數 %(n)d · OK %(ok)d · WARN %(warn)d · FAIL %(fail)d · 政策:唯讀輸入 · 歷史值蓋過預估值(報告 only 零改寫)· no_fake_fill</div>
<table><tr><th>檔案</th><th>分類</th><th class="r">型</th><th class="r">大小 B</th><th class="r">列×欄</th><th>sha12</th><th>擷取驗證閘</th><th>驗證狀態</th></tr>%(rows)s</table>
<div class="ft">VRN Input Matrix Validator v0100 · append-only · 非投資建議 · 視覺鎖 Veritas Header · 零 CDN</div>
</body></html>""" % dict(T, ts=ts, src=src, n=len(matrix), ok=ok, warn=warn, fail=fail, rows=rows_html)
    hp = out_dir / ("vrn_input_matrix_%s.html" % ts)
    hp.write_bytes(html.encode("utf-8"))
    print("[矩陣] %d 檔 · OK %d · WARN %d · FAIL %d" % (len(matrix), ok, warn, fail))
    for m in matrix:
        print("  %-38s %-13s %s" % (m["file"][:38], m["class"], m.get("status_label", m["verdict"])))
    print("[出] %s\n[出] %s" % (jp, hp))
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
