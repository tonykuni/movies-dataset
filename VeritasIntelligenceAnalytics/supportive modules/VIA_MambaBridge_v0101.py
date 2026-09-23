"""
VIA_MambaBridge_v0101(批710 +真自測六檢)
Micromamba SAT Solver → VIA_EnvManager 衝突報告橋接碼。

配套:Invoke-VIA-MicromambaResolver.ps1(同目錄)
  該腳本以 micromamba create --dry-run 進行極速依賴解析,
  將結果寫入 %TEMP%\\via_mamba_conflict_<env>.json。
本橋接碼負責:
  1. 收集 TEMP 目錄下所有 via_mamba_conflict_*.json 掃描結果。
  2. 正規化為 VIA_EnvManager 的 def_EnvConflictRecord 相容格式
     {env_name, severity, category, detail, related_packages}。
  3. 合併寫入 _via_envmanager_output/VIA_EnvManager_ConflictReport.json
     (只增不減:保留既有衝突,去重後追加),並記錄 History JSONL。

設計原則(承 VIA_EnvManager):
  - 不修改 VIA_EnvManager.py 核心與其 def_scan_all_envs() 邏輯,純外掛式合併。
  - 鬆耦合:不 import EnvManager 模組,只讀寫其公開 JSON 檔。
  - 可離線運作;micromamba 缺席時本橋接碼仍可處理既有報告檔。

CLI:
  python VIA_MambaBridge_v0100.py collect            # 收集並列印(不落地)
  python VIA_MambaBridge_v0100.py merge              # 收集 + 合併寫入衝突報告
  python VIA_MambaBridge_v0100.py merge --dir <路徑>  # 指定掃描目錄
  python VIA_MambaBridge_v0100.py show               # 檢視合併後的衝突報告
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

import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS(與 VIA_EnvManager.py 對齊)
# ══════════════════════════════════════════════════════════════════════════════
def_PARAM_MODULE_ID = "VIS-MAMBA-BRIDGE-000001"
def_PARAM_MODULE_VERSION = "0100"
def_PARAM_OWNER = "VIA_MAMBA_BRIDGE"

def_PARAM_OUTPUT_DIR = Path.cwd() / "_via_envmanager_output"
def_PARAM_CONFLICT_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_ConflictReport.json"
def_PARAM_HISTORY_JSONL = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_History.jsonl"

def_PARAM_REPORT_GLOB = "via_mamba_conflict_*.json"
def_PARAM_CATEGORY_CONFLICT = "MAMBA_SAT_CONFLICT"
def_PARAM_SEVERITY_CONFLICT = "WARN"

# conda/mamba solver 描述中常見的套件名樣式,例如
# "package numpy-1.26.4 requires ..." / "nothing provides pandas >=2.0"
def_PARAM_PKG_TOKEN_RE = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9._-]{1,60}?)(?:-\d[\w.]*|\s*(?:==|>=|<=|>|<|~=)\s*\d)"
)


# ══════════════════════════════════════════════════════════════════════════════
# def LOW LEVEL UTILS
# ══════════════════════════════════════════════════════════════════════════════
def def_now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_read_json_safe(path_value: Path, default_value: Any) -> Any:
    try:
        return json.loads(path_value.read_text(encoding="utf-8-sig"))
    except Exception:
        return default_value


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def def_append_jsonl(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    with path_value.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def def_default_report_dir() -> Path:
    return Path(tempfile.gettempdir())


def def_extract_related_packages(detail_text: str) -> List[str]:
    names = {match.group(1).lower() for match in def_PARAM_PKG_TOKEN_RE.finditer(detail_text or "")}
    return sorted(name for name in names if name not in {"python", "version", "package"})


# ══════════════════════════════════════════════════════════════════════════════
# def COLLECT:讀取 Micromamba Resolver 產出的報告檔
# ══════════════════════════════════════════════════════════════════════════════
def def_collect_mamba_reports(report_dir: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    for report_path in sorted(report_dir.glob(def_PARAM_REPORT_GLOB)):
        payload = def_read_json_safe(report_path, None)
        if not isinstance(payload, dict) or "Environment" not in payload:
            continue
        payload["_source_file"] = str(report_path)
        reports.append(payload)
    return reports


def def_normalize_to_conflict_records(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """轉為 def_EnvConflictRecord 相容 dict;僅收錄實際衝突(乾淨環境不進衝突清單)。"""
    records: List[Dict[str, Any]] = []
    for report in reports:
        env_name = str(report.get("Environment", "unknown"))
        if report.get("IsConflictFree", True):
            continue
        raw_conflicts = report.get("Conflicts") or []
        if isinstance(raw_conflicts, dict):  # ConvertTo-Json 單元素會壓成物件
            raw_conflicts = [raw_conflicts]
        for conflict in raw_conflicts:
            detail_text = str(conflict.get("Description") or conflict.get("Rule") or "unknown solver problem")
            records.append(
                {
                    "env_name": env_name,
                    "severity": def_PARAM_SEVERITY_CONFLICT,
                    "category": def_PARAM_CATEGORY_CONFLICT,
                    "detail": detail_text,
                    "related_packages": def_extract_related_packages(detail_text),
                }
            )
    return records


# ══════════════════════════════════════════════════════════════════════════════
# def MERGE:只增不減合併進 VIA_EnvManager_ConflictReport.json
# ══════════════════════════════════════════════════════════════════════════════
def def_conflict_dedupe_key(record: Dict[str, Any]) -> str:
    return "|".join([
        str(record.get("env_name", "")),
        str(record.get("category", "")),
        str(record.get("detail", "")),
    ])


def def_merge_into_conflict_report(new_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    existing_payload = def_read_json_safe(def_PARAM_CONFLICT_JSON, {"conflicts": []})
    existing_conflicts = existing_payload.get("conflicts") or []
    seen_keys = {def_conflict_dedupe_key(row) for row in existing_conflicts}

    appended: List[Dict[str, Any]] = []
    for record in new_records:
        key = def_conflict_dedupe_key(record)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        appended.append(record)

    merged_conflicts = existing_conflicts + appended
    merged_payload = {
        "conflicts": merged_conflicts,
        "updated_at_utc": def_now_utc_iso(),
        "mamba_bridge": {
            "module_id": def_PARAM_MODULE_ID,
            "version": def_PARAM_MODULE_VERSION,
            "appended_count": len(appended),
        },
    }
    def_write_json(def_PARAM_CONFLICT_JSON, merged_payload)
    def_append_jsonl(
        def_PARAM_HISTORY_JSONL,
        {
            "ts_utc": def_now_utc_iso(),
            "owner": def_PARAM_OWNER,
            "event": "MAMBA_BRIDGE_MERGE",
            "appended": len(appended),
            "skipped_duplicates": len(new_records) - len(appended),
            "total_conflicts": len(merged_conflicts),
        },
    )
    return {
        "ok": True,
        "appended": len(appended),
        "skipped_duplicates": len(new_records) - len(appended),
        "total_conflicts": len(merged_conflicts),
        "path": str(def_PARAM_CONFLICT_JSON),
    }


# ══════════════════════════════════════════════════════════════════════════════
# def CLI
# ══════════════════════════════════════════════════════════════════════════════
def def_print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def def_parse_report_dir(argv: List[str]) -> Path:
    if "--dir" in argv:
        idx = argv.index("--dir")
        if idx + 1 < len(argv):
            return Path(argv[idx + 1])
    return def_default_report_dir()


def def_selftest() -> int:
    """批710(任務 #72):本支有 15 條真 import 邊,卻**一站都沒有**。

    煙測(CGC_MDL147)只能判它 SMOKE ——「載得進來」不等於「算得對」。
    本檢把**算得對**那一段真的跑一次:純函式 + 缺件行為,零網路、零寫入倉內。
    """
    import tempfile
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print("=== Mamba 橋 v0101 · 自測(沙盒 · 零網路 · 零寫入)===")

    # ① 套件名抽取:**正控**=真的抓得到,不是永遠空
    got = def_extract_related_packages("package numpy-1.26.0 requires python >=3.9")
    empty = def_extract_related_packages("")
    none_in = def_extract_related_packages(None)
    excluded = def_extract_related_packages("python-3.9 version-1 package-2")
    chk("① 套件名抽取:帶版號的抓得到並轉小寫;`python`/`version`/`package` 三個泛詞要濾掉。"
        "**正控**=真的抓到 `numpy`(一個永遠回空的抽取器也會通過「泛詞被濾掉」那一半);"
        "空字串與 None 都要安靜回空不炸",
        got == ["numpy"] and empty == [] and none_in == [] and excluded == [],
        "(帶版號 %s · 空 %s · None %s · 三泛詞 %s)" % (got, empty, none_in, excluded))

    # ② 抽取式的**窄**:現況釘住,不假裝它很寬
    spaced = def_extract_related_packages("pandas 2.1 conflicts with numpy 1.24")
    chk("② **現況裁定:抽取式只認 `名-版號` 與 `名>=版號`,不認 `名 空格 版號`。**"
        "mamba/conda 的訊息兩種寫法都有,所以這裡會漏。本檢**釘住現況**不假裝它很寬——"
        "哪天有人把式子放寬,這條會亮,那時才知道行為變了(不是默默變寬也不是默默變窄)",
        spaced == [], "(`pandas 2.1 … numpy 1.24` 抓到 %s —— 現況就是抓不到)" % spaced)

    # ③④ 正規化:乾淨的不進清單 / 單元素被壓成物件也要收
    clean = def_normalize_to_conflict_records([{"Environment": "e", "IsConflictFree": True,
                                                "Conflicts": [{"Description": "x"}]}])
    dirty = def_normalize_to_conflict_records([{"Environment": "e", "IsConflictFree": False,
                                                "Conflicts": [{"Description": "numpy conflict"}]}])
    single = def_normalize_to_conflict_records([{"Environment": "e", "IsConflictFree": False,
                                                 "Conflicts": {"Description": "single"}}])
    chk("③ 乾淨環境**不進衝突清單**(不然每個環境都會有一筆假衝突);有衝突的要進;"
        "PowerShell `ConvertTo-Json` 把單元素陣列壓成物件,那一種也要收得到"
        "(**負控**:乾淨那一筆必須是 0,不是「反正都收」)",
        len(clean) == 0 and len(dirty) == 1 and len(single) == 1,
        "(乾淨 %d · 有衝突 %d · 單元素物件 %d)" % (len(clean), len(dirty), len(single)))

    # ④ fail-open:缺鍵時衝突被靜靜丟掉 —— 釘住並標明風險
    nokey = def_normalize_to_conflict_records([{"Environment": "e",
                                                "Conflicts": [{"Description": "有衝突但沒有 IsConflictFree 鍵"}]}])
    chk("④ **現況裁定:報告缺 `IsConflictFree` 鍵時,預設當成「無衝突」,那一筆衝突會被靜靜丟掉。**"
        "這是 fail-open:上游改欄位名或報告殘缺時,**衝突會消失而不是變紅**。"
        "本檢**不改行為**(改判準會影響環境治理的紅綠,屬操作員裁定),只把它釘住並寫在這裡;"
        "哪天有人改成 fail-closed,這條會亮,那就是有意識的改動不是意外",
        len(nokey) == 0, "(缺鍵 → %d 筆(現況 0,即被丟掉))" % len(nokey))

    # ⑤ 去重鍵只看三欄
    a = {"env_name": "a", "category": "c", "detail": "d"}
    b = dict(a, related_packages=["x"])
    c = dict(a, detail="different")
    chk("⑤ 去重鍵只看 env/category/detail 三欄:同一個衝突被報兩次(套件清單不同)要收斂成一筆;"
        "**負控**:detail 不同就**不可以**被去重掉(去重太狠等於把不同的衝突吃掉)",
        def_conflict_dedupe_key(a) == def_conflict_dedupe_key(b)
        and def_conflict_dedupe_key(a) != def_conflict_dedupe_key(c),
        "(同衝突同鍵 %s · 不同 detail 不同鍵 %s)"
        % (def_conflict_dedupe_key(a) == def_conflict_dedupe_key(b),
           def_conflict_dedupe_key(a) != def_conflict_dedupe_key(c)))

    # ⑥ 壞 JSON 要退回預設,不可以炸
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.json"
        bad.write_text("{ not json", encoding="utf-8")
        good = Path(td) / "good.json"
        good.write_text('{"k": 1}', encoding="utf-8")
        r_bad = def_read_json_safe(bad, {"fallback": True})
        r_missing = def_read_json_safe(Path(td) / "nope.json", {"fallback": True})
        r_good = def_read_json_safe(good, {"fallback": True})
    chk("⑥ 壞掉的 / 不存在的 JSON 要**安靜退回預設**(這支在收集別人產的報告,一份壞檔不可以讓整條鏈停);"
        "**正控**:好的那一份必須真的讀出來——只檢「壞的退預設」的話,一個永遠回預設的讀取器也會過",
        r_bad == {"fallback": True} and r_missing == {"fallback": True} and r_good == {"k": 1},
        "(壞檔 %s · 缺檔 %s · 好檔 %s)" % (r_bad, r_missing, r_good))

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def def_main(argv: List[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv or "--self-test" in argv:
        return def_selftest()
    argv = list(argv if argv is not None else sys.argv[1:])
    command = argv[0] if argv else "collect"
    report_dir = def_parse_report_dir(argv)

    if command == "collect":
        reports = def_collect_mamba_reports(report_dir)
        records = def_normalize_to_conflict_records(reports)
        def_print_json({
            "ok": True,
            "report_dir": str(report_dir),
            "reports_found": len(reports),
            "conflict_records": records,
        })
        return 0

    if command == "merge":
        reports = def_collect_mamba_reports(report_dir)
        records = def_normalize_to_conflict_records(reports)
        result = def_merge_into_conflict_report(records)
        result["report_dir"] = str(report_dir)
        result["reports_found"] = len(reports)
        def_print_json(result)
        return 0 if result.get("appended", 0) == 0 or result.get("ok") else 1

    if command == "show":
        def_print_json(def_read_json_safe(def_PARAM_CONFLICT_JSON, {"conflicts": [], "note": "尚無報告"}))
        return 0

    def_print_json({
        "ok": False,
        "error": "UNKNOWN_COMMAND",
        "supported": ["collect [--dir 路徑]", "merge [--dir 路徑]", "show"],
        "received": command,
    })
    return 1


if __name__ == "__main__":
    sys.exit(def_main())
