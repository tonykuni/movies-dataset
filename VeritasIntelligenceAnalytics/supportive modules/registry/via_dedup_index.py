# -*- coding: utf-8 -*-
r"""VIA 整合去重引擎 v0100(ENG-049)— 操作員「整合優化」令

把整合去重鐵律產品化:本機一鍵對照庫內正本出判定,免逐檔上傳。
  build          全庫 sha256 索引 → VIA_Reports/dedup/VIA_Content_Hash_Index.json(可再生側車,不入 git)
  check <路徑>   檔案或資料夾逐檔判定:IDENTICAL(已在籍)/ VERSION_DIFFERS(同名異雜湊)/
                 NOT_IN_REPO(候歸戶)→ 報告 JSON + 誠實摘要;隔離件命中額外標示
  report         去重戰役總表 HTML(讀 audit_tools/VIA_ModuleDedup_Homing_Record_v0100.json)
全唯讀不動正本;只寫 VIA_Reports/dedup/ 下產物。zero 外部依賴(stdlib)。
"""
import hashlib, json, os, re, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent          # supportive modules/registry
ROOT = HERE.parent.parent                        # VeritasIntelligenceAnalytics
OUT = ROOT / "VIA_Reports" / "dedup"
INDEX_P = OUT / "VIA_Content_Hash_Index.json"
AUDIT_P = HERE.parent / "audit_tools" / "VIA_ModuleDedup_Homing_Record_v0100.json"
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".venv_pm", "dedup"}
UPLOAD_PREFIX = re.compile(r"^[0-9a-f]{8}-")
UPLOAD_SUFFIX = re.compile(r"(_\d+| \(\d+\))$")


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_name(name):
    """上傳檔名正規化:去 8hex- 前綴與 _n / (n) 尾綴,供同名異版比對。"""
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    stem = UPLOAD_PREFIX.sub("", stem)
    stem = UPLOAD_SUFFIX.sub("", stem)
    return (stem + ("." + ext if ext else "")).lower()


def cmd_build():
    by_sha, by_name, n = {}, {}, 0
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in EXCLUDE_DIRS]
        for fn in fns:
            p = Path(dp) / fn
            try:
                sha = sha256_of(p)
            except Exception:
                continue
            rel = str(p.relative_to(ROOT))
            by_sha.setdefault(sha, []).append(rel)
            by_name.setdefault(norm_name(fn), []).append({"path": rel, "sha": sha})
            n += 1
    OUT.mkdir(parents=True, exist_ok=True)
    INDEX_P.write_text(json.dumps({
        "generated": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT), "files": n,
        "by_sha": by_sha, "by_name": by_name}, ensure_ascii=False), encoding="utf-8")
    print("[索引] %d 檔入索引 → %s" % (n, INDEX_P))
    print("[治理] 索引=可再生側車(不入 git);正本有增減後重跑 build 即新")
    return 0


def _load_index():
    if not INDEX_P.exists():
        print("[FAIL] 索引不在位 — 先跑:via-dedup build")
        return None
    idx = json.loads(INDEX_P.read_text(encoding="utf-8"))
    print("[索引] %s 產生 · %d 檔" % (idx.get("generated", "?"), idx.get("files", 0)))
    return idx


def cmd_check(target):
    idx = _load_index()
    if idx is None:
        return 1
    tp = Path(target)
    if not tp.exists():
        print("[FAIL] 路徑不存在:%s" % target)
        return 1
    cands = [tp] if tp.is_file() else sorted(
        p for p in tp.rglob("*") if p.is_file()
        and not any(d in p.parts for d in EXCLUDE_DIRS))
    rows = []
    n_id = n_ver = n_new = 0
    for p in cands:
        try:
            sha = sha256_of(p)
        except Exception as e:
            rows.append({"file": str(p), "verdict": "READ_ERROR", "detail": str(e)[:80]})
            continue
        hit = idx["by_sha"].get(sha)
        if hit:
            n_id += 1
            quar = [h for h in hit if "quarantine" in h.lower()]
            v = {"file": str(p), "sha256_16": sha[:16], "verdict": "IDENTICAL", "canon": hit}
            if quar:
                v["redline"] = "命中隔離件 — 維持隔離不回歸:%s" % quar[0]
            rows.append(v)
            continue
        nm = idx["by_name"].get(norm_name(p.name))
        if nm:
            n_ver += 1
            rows.append({"file": str(p), "sha256_16": sha[:16], "verdict": "VERSION_DIFFERS",
                         "canon_variants": nm[:5],
                         "hint": "同名異雜湊 — 人工裁定新舊(正本 changelog/版號優先);劣本不入籍"})
        else:
            n_new += 1
            rows.append({"file": str(p), "sha256_16": sha[:16], "verdict": "NOT_IN_REPO",
                         "hint": "候歸戶 — 上傳交 AI 依位階裁定落籍"})
    OUT.mkdir(parents=True, exist_ok=True)
    rep_p = OUT / ("dedup_check_%s.json" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    rep_p.write_text(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                 "target": str(tp), "n": len(cands),
                                 "identical": n_id, "version_differs": n_ver, "not_in_repo": n_new,
                                 "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("========== 整合去重判定(%d 檔)==========" % len(cands))
    print("  已在籍 IDENTICAL       %d(免上傳)" % n_id)
    print("  同名異版 VERSION_DIFFERS %d(需人工裁定)" % n_ver)
    print("  候歸戶 NOT_IN_REPO     %d(上傳交裁定)" % n_new)
    for r in rows:
        if r["verdict"] != "IDENTICAL":
            print("  [%s] %s" % (r["verdict"], r["file"]))
        if r.get("redline"):
            print("  [紅線] %s" % r["redline"])
    print("[報告] %s" % rep_p)
    return 0


def cmd_report():
    aud = {}
    try:
        aud = json.loads(AUDIT_P.read_text(encoding="utf-8"))
    except Exception:
        print("[WARN] 戰役稽核紀錄不在位:%s — 出空表" % AUDIT_P)
    # 併入早期兩份去重紀錄(FIS 家族 / 含隔離件批)— 同鍵位 schema,直接串接
    for extra in ("VIA_FIS_Family_Dedup_Record_v0100.json", "VIA_Upload_Dedup_Record_v0101.json"):
        try:
            e = json.loads((AUDIT_P.parent / extra).read_text(encoding="utf-8"))
            aud.setdefault("dedup_already_homed", [])
            aud["dedup_already_homed"] = e.get("dedup", []) + aud["dedup_already_homed"]
        except Exception:
            pass
    sec = []

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def table(title, rows, cols):
        h = "<div class='card'><h2>%s(%d)</h2><table><thead><tr>" % (esc(title), len(rows))
        h += "".join("<th>%s</th>" % esc(c[0]) for c in cols) + "</tr></thead><tbody>"
        for r in rows:
            h += "<tr>" + "".join("<td>%s</td>" % esc(r.get(c[1], "")) for c in cols) + "</tr>"
        return h + "</tbody></table></div>"

    ah = aud.get("dedup_already_homed", [])
    hn = aud.get("homed_new", [])
    sp = aud.get("superseded_not_homed", [])
    sec.append(table("已在籍(byte-identical,零落籍)", ah,
                     [("上傳檔", "upload"), ("sha16", "sha256_16"), ("判定", "verdict"), ("庫內正本", "canon")]))
    sec.append(table("新歸戶", hn,
                     [("上傳檔", "upload"), ("sha16", "sha256_16"), ("落籍位置", "homed_to"), ("裁定", "adjudication")]))
    sec.append(table("劣本不入籍(帳上留痕)", sp,
                     [("上傳檔", "upload"), ("sha16", "sha256_16"), ("判定", "verdict"), ("原因", "reason")]))
    idx_line = ""
    if INDEX_P.exists():
        idx = json.loads(INDEX_P.read_text(encoding="utf-8"))
        idx_line = "本機索引:%s 產生 · %d 檔" % (idx.get("generated", "?"), idx.get("files", 0))
    html = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VIA 整合去重戰役總表</title><style>"
            "body{background:#f5f4f0;color:#1e1d1a;font-family:'DM Sans','Noto Sans TC',sans-serif;"
            "font-size:13px;margin:0;padding:24px}h1{font-size:20px;margin:0 0 4px}"
            ".sub{color:#6b6860;font-size:12px;margin-bottom:14px}"
            ".strip{height:6px;border-radius:2px;margin:12px 0;"
            "background:linear-gradient(90deg,#4c78a8,#439a9a,#5a9e6f,#c9b05a,#c96b5a)}"
            ".kpis{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}"
            ".kpi{background:#fff;border:1px solid #dbd9d3;border-radius:6px;padding:10px 14px}"
            ".kpi b{font-size:22px;display:block}"
            ".card{background:#fff;border:1px solid #dbd9d3;border-radius:8px;padding:12px;margin:12px 0;overflow-x:auto}"
            "h2{font-size:14px;margin:0 0 6px}table{width:100%;border-collapse:collapse;font-size:11.5px}"
            "th,td{padding:5px 8px;border-bottom:1px solid #eceae2;text-align:left;vertical-align:top}"
            "th{font-size:9.5px;color:#6b6860;text-transform:uppercase}"
            ".foot{color:#9c9890;font-size:11px;border-top:1px solid #dbd9d3;padding-top:10px;margin-top:14px}"
            "</style></head><body><h1>整合去重戰役總表</h1>"
            "<div class='sub'>操作員「全部模組整合去重」+「整合優化」令 · append-only · 正本零觸碰 · "
            + esc(idx_line) + "</div><div class='strip'></div><div class='kpis'>"
            "<div class='kpi'><b>%d</b>已在籍</div><div class='kpi'><b>%d</b>新歸戶</div>"
            "<div class='kpi'><b>%d</b>劣本留痕</div><div class='kpi'><b>%d</b>總判定</div></div>"
            % (len(ah), len(hn), len(sp), len(ah) + len(hn) + len(sp))
            + "".join(sec)
            + "<div class='foot'>ENG-049 via-dedup · build=建索引 · check 路徑=本機判定 · "
              "劣本不入籍帳上留痕 · 隔離件永不回歸 · 產生 "
            + datetime.now().strftime("%Y-%m-%d %H:%M") + "</div></body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    rp = OUT / "VIA_Dedup_Campaign_Matrix.html"
    rp.write_text(html, encoding="utf-8")
    print("[總表] 已在籍 %d · 新歸戶 %d · 劣本留痕 %d → %s" % (len(ah), len(hn), len(sp), rp))
    return 0


def main(argv):
    if len(argv) < 2 or argv[1] == "build":
        return cmd_build()
    if argv[1] == "check":
        if len(argv) < 3:
            print("用法:via-dedup check <檔案或資料夾>")
            return 2
        return cmd_check(argv[2])
    if argv[1] == "report":
        return cmd_report()
    print("動詞:build(預設)/ check <路徑> / report")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
