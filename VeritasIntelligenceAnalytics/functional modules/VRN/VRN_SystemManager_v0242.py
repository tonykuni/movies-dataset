#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN-2 v0242: original-source summaries, compact UI and auditable idempotence.

Financial extraction and the independent financial verifier remain unchanged.
"""
from __future__ import annotations

# ===== 1. Parameters =====
TAG = "v0242"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0239.py"
RUNTIME_METADATA = frozenset(("n", "img", "cache", "cache_hit", "cache_path", "elapsed", "elapsed_s", "secs", "duration_s", "pid", "worker_id", "generated_at"))

import contextlib
import datetime
import hashlib
import html
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types

# [VIA:ACCEL-BRIDGE:v0111] The original manager executes its accelerator bridge.
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0242", Path(__file__).with_name(PRIOR_NAME))
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in list(vars(PRIOR).items()):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def __getattr__(name):
    return getattr(PRIOR, name)


def _rebind(function):
    result = types.FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    result.__kwdefaults__, result.__doc__ = function.__kwdefaults__, function.__doc__
    return result


# ===== 2. Original-source evidence stays next to the unchanged public books =====
SOURCE_PROOFS = []


def acceptance(res, indir, v2, *args, **kwargs):
    result = PRIOR.acceptance(res, indir, v2, *args, **kwargs)
    # The native acceptance card shortens points to 240 characters and omits
    # evidence. Restore the complete, hash-bound source summary for public books.
    _, engine_name = _acc_eng062()
    for entry in result[0]:
        pdf = Path(indir) / entry["file"]
        if not pdf.is_file():
            continue
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        cache = Path(v2) / "summary" / (digest[:12] + "_" + engine_name.replace(".py", "") + ".json")
        if cache.is_file():
            summary = json.loads(cache.read_text(encoding="utf-8"))
            if summary.get("summary_mode") == "SOURCE_VERBATIM" and summary.get("source_pdf_sha256") == digest:
                entry["summary"] = summary
    return result


def _out_books(res, acc, st, v2):
    basic, financial, summaries, gaps, made = PRIOR._out_books(res, acc, st, v2)
    SOURCE_PROOFS.clear()
    by_file = {entry.get("file"): entry for entry in acc}
    title_filled = set()
    for row in basic:
        summary = (by_file.get(row["FILENAME"]) or {}).get("summary") or {}
        if not row.get("TITLE") and summary.get("title_original"):
            row["TITLE"] = summary["title_original"]
            row.setdefault("_STATUS", {})["TITLE"] = "OCR_PENDING" if any((p.get("evidence") or [{}])[0].get("reader") == "OCR" for p in summary.get("points") or []) else "SOURCE_TEXT"
            title_filled.add(row["FILENAME"][:28])
    # Native v0233 folds whitespace for single-line cards. Public quotations
    # must retain the full exact source span, including its original line wraps.
    for row in summaries:
        summary = (by_file.get(row["FILENAME"]) or {}).get("summary") or {}
        points = summary.get("points") or []
        if summary.get("summary_mode") == "SOURCE_VERBATIM":
            row["TITLE"] = summary.get("title_original") or row.get("TITLE") or ""
            row.update({f"POINT_{i+1}": (points[i].get("text") or "") if i < len(points) else "" for i in range(4)})
            row["POINTS_OK"] = sum(bool(row[f"POINT_{i+1}"]) for i in range(4))
        proofs = []
        for index in range(4):
            point = points[index] if index < len(points) else {}
            proof = (point.get("evidence") or [{}])[0]
            text = row.get(f"POINT_{index + 1}") or ""
            exact = bool(text and point.get("verbatim") and text == proof.get("quote") and hashlib.sha256(text.encode("utf-8")).hexdigest() == proof.get("quote_sha256"))
            proofs.append({"point": index + 1, "verbatim": exact, "text": text, **proof})
        SOURCE_PROOFS.append({"file": row["FILENAME"], "mode": summary.get("summary_mode"), "pdf_sha256": summary.get("source_pdf_sha256"), "points": proofs})
        if not all(proof["verbatim"] for proof in proofs):
            gaps.append(row["FILENAME"] + ":四點原文證據未齊")
    target = Path(v2) / "output" / "VRN2_SummarySource_latest.json"
    target.write_text(json.dumps({"schema": "VRN2_SUMMARY_SOURCE/1", "manager": TAG, "documents": SOURCE_PROOFS}, ensure_ascii=False, indent=2), encoding="utf-8")
    repaired_gaps = []
    for gap in gaps:
        filename, separator, missing = gap.partition(":")
        if separator and filename in title_filled:
            remaining = [part for part in missing.split("、") if part != "TITLE"]
            if remaining:
                repaired_gaps.append(filename + ":" + "、".join(remaining))
        else:
            repaired_gaps.append(gap)
    gaps = repaired_gaps
    made = [entry for entry in made if not entry.startswith(("BasicInfo(", "Summary("))]
    made += [_write_book(Path(v2) / "output", "BasicInfo", basic), _write_book(Path(v2) / "output", "Summary", summaries)]
    return basic, financial, summaries, gaps, made


# ===== 3. Compare source content; record every actual data difference =====
def semantic_record(value, key="", path=()):
    if isinstance(value, dict):
        # Only the documented file ordinal/cache metadata and page image paths
        # are operational. A field named n inside table records remains data.
        ignored = RUNTIME_METADATA - {"img"} if not path else ({"img"} if len(path) == 2 and path[0] == "pages" else set())
        return {name: semantic_record(item, name, path + (name,)) for name, item in value.items() if name not in ignored}
    if isinstance(value, list):
        result = [semantic_record(item, key, path + (index,)) for index, item in enumerate(value)]
        # These are classification sets. Table/period/value order remains strict.
        return sorted(result) if key in ("reasons", "na") and all(isinstance(item, str) for item in result) else result
    return value


def record_differences(before, after, path="", limit=80):
    if type(before) is not type(after):
        return [{"path": path, "before": before, "after": after}]
    if isinstance(before, dict):
        out = []
        for name in sorted(set(before) | set(after)):
            if name not in before or name not in after:
                out.append({"path": path + "/" + name, "before": before.get(name), "after": after.get(name)})
            else:
                out.extend(record_differences(before[name], after[name], path + "/" + name, limit - len(out)))
            if len(out) >= limit:
                break
        return out[:limit]
    if isinstance(before, list):
        out = []
        if len(before) != len(after):
            out.append({"path": path + "/length", "before": len(before), "after": len(after)})
        for index, (left, right) in enumerate(zip(before, after)):
            out.extend(record_differences(left, right, path + f"/{index}", limit - len(out)))
            if len(out) >= limit:
                break
        return out[:limit]
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def _idem_check(res, indir, k=3):
    selected = sorted((record for record in res if record.get("lamp") == "GREEN" and len(record.get("pages") or []) >= 2), key=lambda record: record.get("file", ""))[:k]
    if not selected:
        return "GRAY", "沒有可重跑的檔"
    engines = sorted(Path(HERE).glob("VRN_ENG397_P1Segment_v[0-9][0-9][0-9][0-9].py"))
    if not engines:
        return "RED", "找不到 ENG397，冪等檢查未執行"
    spec = importlib.util.spec_from_file_location("vrn_engine_idempotence_v0242", engines[-1])
    engine = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = engine
    spec.loader.exec_module(engine)
    directory = Path(tempfile.mkdtemp(prefix="vrn2_idem_v0242_"))
    (directory / "in").mkdir()
    (directory / ".via_keep").touch()
    for record in selected:
        shutil.copy2(Path(indir) / record["file"], directory / "in" / record["file"])
    saved = {key: os.environ.get(key) for key in ("VIA_VRN2_LANES", "VIA_VRN2_P1_CACHE")}
    receipt = {"manager": TAG, "engine": engines[-1].name, "ignored_runtime_keys": sorted(RUNTIME_METADATA), "files": [], "lamp": "RED"}
    try:
        os.environ["VIA_VRN2_LANES"] = "1"
        os.environ.pop("VIA_VRN2_P1_CACHE", None)
        with (directory / "rerun.log").open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
            engine.run(directory / "in", directory / "rep")
        again = {row["file"]: row for row in json.loads((directory / "rep/p1view/P1VIEW_latest.json").read_text(encoding="utf-8"))}
        for record in selected:
            rerun = again.get(record["file"], {})
            before, after = semantic_record(record), semantic_record(rerun)
            differences = record_differences(before, after)
            receipt["files"].append({"file": record["file"], "input_sha256": hashlib.sha256((Path(indir) / record["file"]).read_bytes()).hexdigest(),
                "semantic_equal": not differences, "differences": differences,
                "runtime_metadata_differences": [row for row in record_differences(record, rerun) if any(part in RUNTIME_METADATA for part in row["path"].split("/"))]})
        failed = [row["file"] for row in receipt["files"] if not row["semantic_equal"]]
        receipt["lamp"] = "RED" if failed else "GREEN"
        message = ("真實內容差異 %d 份：%s" % (len(failed), "、".join(failed))) if failed else "重跑 %d 份，文字／表格／數值／期間／位置一致" % len(selected)
    except Exception as error:
        receipt["error"] = f"{type(error).__name__}: {error}"
        message = "重跑失敗：" + receipt["error"]
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    target = Path(HERE).parents[1] / "VIA_Reports/vrn2/IDEMPOTENCE_latest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    receipt["evidence_directory"] = str(directory)
    target.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    if receipt["lamp"] == "GREEN":
        shutil.rmtree(directory)
    return receipt["lamp"], message + " · 詳細差異 " + str(target)


# ===== 4. Compact, responsive formatting; original system actions retained =====
def _accept_html(out, cnt):
    """Render missing evidence without changing its values or acceptance lamps."""
    names = (("c1", "① 計算驗證"), ("c2", "② 覆蓋"), ("c3", "③ 回原文"), ("c5", "⑤ 一標題四重點"), ("c6", "⑥ AUDIT"), ("c7", "⑦ 基本資料雙讀"))
    escape = lambda value, missing="待核對": html.escape(missing if value is None or value == "" else str(value))
    head = " · ".join("%s 綠%d 黃%d 紅%d 灰%d" % (name, *((cnt.get(key) or {}).get(lamp, 0) for lamp in ("GREEN", "YELLOW", "RED", "GRAY"))) for key, name in names)
    rows = []
    for entry in out:
        cells = []
        for key, _ in names:
            state = entry.get(key) or ("GRAY", "待核對")
            lamp = state[0]
            note = state[1] if len(state) > 1 else None
            cells.append("<td%s><i style='background:%s'></i>%s</td>" % (" class='bl'" if lamp == "RED" else "", _V2C.get(lamp, "#9ca3af"), escape(note)))
        summary = entry.get("summary") or {}
        points = summary.get("points") or []
        quotes = []
        for index in range(4):
            point = (points[index] or {}) if index < len(points) else {}
            quotes.append("<li>[%s · %s] <span style='white-space:pre-line'>%s</span></li>" % (escape(point.get("topic")), escape(point.get("status"), "MISSING"), escape(point.get("text"), "缺少可引用原文，待核對")))
        detail = "<details><summary>%s</summary><ol>%s</ol></details>" % (escape(summary.get("title_original") or summary.get("title"), "缺少原文標題，待核對"), "".join(quotes)) if summary else "待核對"
        rows.append("<tr><td>%s</td>%s<td>%s</td></tr>" % (escape(entry.get("file")), "".join(cells), detail))
    return "<h2 style='margin-top:14px'>完成驗收</h2><div>%s</div><table><tr><th>檔案</th>%s<th>一標題四重點</th></tr>%s</table>" % (escape(head), "".join("<th>%s</th>" % name for _, name in names), "".join(rows))


def _ui_panel_html(v2):
    panel = PRIOR._ui_panel_html(v2)
    config_path = Path(HERE) / "VRN2_UIAction_Config.json"
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        launcher = Path(config.get("launcher") or "")
        if launcher.name == "ActivateVRN-2_v0140.py":
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            template = Path(HERE).parents[1] / "supportive modules/ps7/VeritasCeleritas.PS7.Template.ps1"
            command = "try { . " + quote(template) + "; & " + quote(config["python"]) + " -X utf8 " + quote(launcher) + " } finally { if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { Restore-CeleritasPS7 } }"
            encoded = html.escape(command, quote=True)
            # v0104 exposes c0/c1 for both checkbox states. A callable keeps
            # Windows backslashes literal in the replacement command.
            panel = re.sub(r'(data-c(?:[01])?=")[^"]*"', lambda match: match.group(1) + encoded + '"', panel)
    return panel


COMPACT_STYLE = """<style id="vrn2-professional-v0242">
:root{font-size:13px;color-scheme:light}body{font-family:Inter,"Segoe UI","Noto Sans CJK TC","Microsoft JhengHei",sans-serif!important;font-size:12px!important;line-height:1.55!important;background:#f8f7f2!important;color:#26312f!important;margin:0!important;overflow-x:hidden}
h1{font-size:21px!important;letter-spacing:.01em}h2{font-size:16px!important}h3{font-size:13px!important}small{font-size:10.5px}table{font-size:11.5px!important;line-height:1.5;border-collapse:separate!important;border-spacing:0!important;width:100%}th{font-size:10.5px!important;text-align:left;letter-spacing:.025em;background:#eeeee7!important;position:sticky;top:0;z-index:1}th,td{padding:8px 10px!important;vertical-align:top;border-bottom:1px solid #e1e4dc!important}td{max-width:40rem;overflow-wrap:anywhere}button,input,select{font:inherit!important;font-size:11.5px!important;border-radius:5px!important}button{padding:6px 10px!important}.sum{font-size:11px!important;gap:8px!important;flex-wrap:wrap}.vo-wrap,.vo-sec{min-width:0;max-width:100%;overflow-x:auto}.vo-grid{gap:12px!important}.vo-tb{font-size:11px!important}.vo-tb td{padding:7px 9px!important}#vrn2tabs{display:flex;gap:4px;flex-wrap:wrap;min-width:0}#vrn2panel{font-size:11.5px!important}.source-audit{background:#fffefb;border:1px solid #dedfd5;border-radius:8px;padding:14px;margin:12px 0}.source-audit summary{cursor:pointer;font-weight:600}.source-audit blockquote{white-space:pre-line;margin:8px 0;padding:8px 12px;border-left:2px solid #9b3d2e;background:#f7f7ef;font-size:12px;line-height:1.7}.source-audit ol{padding-left:24px}.source-audit .proof{font-size:10px;color:#64706b}.source-audit details{border-top:1px solid #e6e7df;padding:9px 0}
@media(min-width:1100px){.vo-grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}.source-audit{max-width:1100px}}
@media(min-width:641px){body{padding:12px!important}body:has(#vrn2panel){padding-left:202px!important}#vrn2panel{width:190px!important;padding:14px 10px!important;background:#f1f3ec!important;border-right:1px solid #dce1d5!important}#vrn2panel a{font-size:11.5px!important;line-height:1.45!important}}
@media(max-width:640px){body{font-size:12px!important}h1{font-size:18px!important}.vo-grid{grid-template-columns:minmax(0,1fr)!important}#vrn2panel{position:relative!important;width:auto!important;height:auto!important;max-width:100%!important;inset:auto!important}body{padding:10px!important}#vrn2tabs{margin-left:0!important}table{display:block;overflow-x:auto}.source-audit{padding:10px}.source-audit blockquote{padding:8px;font-size:12px}}
</style>"""


def _out_html(basic, financial, summaries):
    native = PRIOR._out_html(basic, financial, summaries)
    records = []
    for document in SOURCE_PROOFS:
        points = []
        for proof in document["points"]:
            label = "原文" if proof["verbatim"] else "待核對"
            reader = "OCR，需核對原圖" if proof.get("reader") == "OCR" else "PDF 文字層"
            points.append("<li><div class='proof'>%s · p.%s · %s</div><blockquote>%s</blockquote></li>" % (label, html.escape(str(proof.get("page", "—"))), reader, html.escape(proof.get("text") or "缺少可引用原文")))
        records.append("<details><summary>%s</summary><ol>%s</ol></details>" % (html.escape(document["file"]), "".join(points)))
    return native + COMPACT_STYLE + "<h2 id='vrn2-source-h'>四點原文重點</h2><section class='source-audit' id='vrn2-original-quotes'><p>保留原文語言與數字。每點附頁碼、來源區塊與摘錄雜湊；原文不足時保留待核對。</p><a href='output/VRN2_SummarySource_latest.json'>下載來源證據 JSON</a>" + "".join(records) + "</section>"


_native_vrn2 = _rebind(PRIOR.vrn2)


def vrn2(args, rep=None, indir=None, open_ui=True, reg=None):
    # Native scope output lists only the current batch. Keep earlier explicit
    # non-stock decisions so the next run does not re-add excluded reports.
    report = Path(rep or _resolve("_rep")())
    scope = report.parent / "vrn2/VRN2_Scope_latest.json"
    previous = json.loads(scope.read_text(encoding="utf-8")) if scope.is_file() else {}
    result = _native_vrn2(args, rep=rep, indir=indir, open_ui=open_ui, reg=reg)
    if scope.is_file():
        current = json.loads(scope.read_text(encoding="utf-8"))
        excluded = sorted(set(previous.get("non_stock") or []) | set(current.get("non_stock") or []))
        current.update(non_stock=excluded, stock=[name for name in current.get("stock") or [] if name not in excluded])
        scope.write_text(json.dumps(current, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


_success_register = _rebind(PRIOR._success_register)


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    result["manager"] = f"{DISPLAY_NAME} {TAG}"
    return result


def selftest():
    global HERE
    first = {"file": "a.pdf", "n": 1, "cache": "miss", "pages": [{"pno": 1, "img": "old.png", "rows": [["2026", "1.25"]]}]}
    second = {"file": "a.pdf", "n": 7, "cache": "hit", "pages": [{"pno": 1, "img": "new.png", "rows": [["2026", "1.25"]]}]}
    assert semantic_record(first) == semantic_record(second)
    second["pages"][0]["rows"][0][1] = "1.26"
    differences = record_differences(semantic_record(first), semantic_record(second))
    assert differences[0]["path"] == "/pages/0/rows/0/1"
    assert semantic_record(first) != semantic_record(second)
    assert semantic_record({"pages": [{"rows": [{"n": 1}]}]}) != semantic_record({"pages": [{"rows": [{"n": 2}]}]})
    import copy
    missing = [{"file": "missing<&.pdf", "c5": ("YELLOW", "原文不足"), "summary": {"title": None, "points": [{"topic": "growth", "status": "MISSING", "text": None}, {"topic": None, "status": None, "text": "Revenue < 5 & demand\nrecovers."}]}}]
    saved = copy.deepcopy(missing)
    rendered = _accept_html(missing, {})
    assert missing == saved and rendered.count("<li>") == 4
    assert "缺少可引用原文，待核對" in rendered and "Revenue &lt; 5 &amp; demand\nrecovers." in rendered
    assert "missing&lt;&amp;.pdf" in rendered and "原文不足" in rendered
    assert _native_vrn2.__globals__["_accept_html"] is _accept_html
    assert _native_vrn2.__globals__["_idem_check"] is _idem_check
    assert _native_vrn2.__globals__["acceptance"] is acceptance
    saved_here = HERE
    try:
        with tempfile.TemporaryDirectory() as temporary:
            HERE = Path(temporary) / "functional modules/VRN2"
            HERE.mkdir(parents=True)
            (HERE / "VRN2_UIAction_Config.json").write_text(json.dumps({"launcher": str(Path(temporary) / "ActivateVRN-2_v0140.py"), "python": r"C:\Users\test\envs\via_core\Scripts\python.exe"}), encoding="utf-8")
            panel = _ui_panel_html(Path(temporary))
            assert "ActivateVRN-2_v0140.py" in panel and "VeritasCeleritas.PS7.Template.ps1" in panel
            commands = [html.unescape(value) for value in re.findall(r'data-c[01]="([^"]*)"', panel)]
            assert len(commands) == 2 and all("ActivateVRN-2_v0140.py" in value and r"C:\Users\test" in value for value in commands)
    finally:
        HERE = saved_here
    print("[PASS] null-safe original quotes; input/lamps unchanged; actual native dispatch uses current renderer and idempotence; numeric tamper rejected")
    return 0


def main(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--selftest"]:
        return selftest()
    if arguments[:1] == ["vrn2"]:
        code, lines = vrn2(arguments[1:])
        for line in lines:
            print(line, flush=True)
        return code
    return PRIOR.main(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
