#!/usr/bin/env python3
"""重算 VTR_Subsystem_Manifest.json。

manifest 登錄每個 canonical artifact 的 SHA-256，是 VIA hash-locked 晉升流程的
輸入。它必須能被**重現**，不能只存在於某次臨時執行的腳本裡 —— 否則下次有人改了
一份規格件，就沒有可信的方式重建 manifest。

用法:
    python3 tools/build_manifest.py            # 檢查 manifest 是否與檔案一致
    python3 tools/build_manifest.py --write    # 重算並寫回

退出碼:
    0  一致（或已寫入）
    5  manifest 與實際檔案不一致（--write 可修）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "VTR_Subsystem_Manifest.json"

#: 固定登錄的規格件。順序即 manifest 中的順序，刻意穩定以便 diff 可讀。
SPEC_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("contracts/vtr-document.schema.json",
     "Document 資料契約 · Python 版與 JavaScript 版共用的唯一 SSOT 結構"),
    ("config/vtr.json", "引擎設定 · 兩版引擎共用的門檻與權重"),
    ("docs/00_ARCHITECTURE.md",
     "完整修復引擎架構圖 · 三層架構 / 八步管線 / P0 遮罩 / 信心度閘門 / 四大 Pipeline"),
    ("docs/01_PYTHON_ENGINE_SPEC.md",
     "Python 版修復引擎規格書 · 權威實作（含實作狀態標記）"),
    ("docs/02_JAVASCRIPT_ENGINE_SPEC.md",
     "JavaScript 版修復引擎規格書 · 即時預覽 / 編輯器層 / 人工裁決 UI"),
    ("docs/03_SSOT_LEXICON_SPEC.md",
     "SSOT Lexicon 結構規格書 · 詞條結構 / 比對演算法 / 治理"),
    ("lexicon/schema/vtr-lexicon.schema.json", "Lexicon JSON Schema · 詞庫檔契約"),
    ("lexicon/lexicon.index.json", "Lexicon 索引 · 各詞庫檔 SHA-256 與統計"),
    ("lexicon/tools/validate_lexicon.py", "Lexicon 驗證器 / 索引產生器 · CI 掛載點"),
    ("tools/build_manifest.py", "Manifest 重算工具（本檔）"),
    ("Invoke-VTR.ps1", "PowerShell 單一進入點 · operator workstation 用"),
    ("README.md", "VTR 子系統導覽"),
)


def _canonical_bytes(raw: bytes) -> bytes:
    """把檔案內容正規化成跨平台一致的位元組。

    hash-lock 的意義是「內容身分」，而 Windows(CRLF) 與 Linux/Git(LF) 對同一份
    文字檔會產生不同的位元組 —— 若直接雜湊原始位元組，同一份規格件在兩個平台上
    的 SHA-256 就不同，manifest 在 Windows checkout 上會全體誤報「內容已變更」。

    因此文字檔一律先把 CRLF 正規化為 LF 再雜湊；含 null byte 的二進位檔原樣雜湊
    （不會被行尾正規化破壞）。git 自己也是這樣看待文字內容的。
    UTF-8 BOM 不含 CR/LF，不受此正規化影響，維持逐位元組不變。
    """
    if b"\x00" in raw:
        return raw
    return raw.replace(b"\r\n", b"\n")


def content_hash(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path.read_bytes())).hexdigest()


def content_size(path: Path) -> int:
    return len(_canonical_bytes(path.read_bytes()))


def sha256_of(path: Path) -> str:
    """保留供既有呼叫端使用；等同 content_hash（正規化後雜湊）。"""
    return content_hash(path)


def collect_artifacts() -> list[dict]:
    arts: list[dict] = []
    for rel, role in SPEC_ARTIFACTS:
        p = ROOT / rel
        if not p.exists():
            print(f"WARN  登錄的檔案不存在，已跳過: {rel}", file=sys.stderr)
            continue
        arts.append({"filename": rel, "role": role,
                     "bytes": content_size(p), "sha256": content_hash(p)})

    # 引擎程式碼以萬用字元收集：新增 Stage 時不需要手動維護清單。
    for p in sorted((ROOT / "engine").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT).as_posix()
        arts.append({"filename": rel, "role": "引擎程式碼（確定性層）",
                     "bytes": content_size(p), "sha256": content_hash(p)})
    return arts


def build() -> dict:
    idx = json.loads((ROOT / "lexicon/lexicon.index.json").read_text(encoding="utf-8"))
    return {
        "subsystem": "VTR",
        "role": ("DG-IN Meeting Transcript Restoration Engine · 中英文會議紀錄修復引擎"
                 "（雙語混合修復架構 / 八步修復法 / SSOT Lexicon / 四大 Pipeline）"),
        "integration_state": "SPEC_REGISTERED_DETERMINISTIC_LAYER_IMPLEMENTED",
        "canonical_tree": (
            "本 anchor 攜帶 VTR canonical 規格件（contracts/, config/, docs/, lexicon/）"
            "與確定性層引擎（engine/vtr_py：步驟 1–2 + P0 遮罩 + 版本重播）。"
            "步驟 3–8 需模型層，尚未實作 —— 見 README.md。"),
        "discovery_root": "functional modules/VTR",
        "entry_point": "Invoke-VTR.ps1",
        "artifacts": collect_artifacts(),
        "implementation_status": {
            "implemented": [
                "資料契約與 Python 綁定", "Pipeline 四條不變式", "信心度閘門",
                "步驟 1 LANG_DETECT", "步驟 2 NORMALIZE",
                "P0 PROTECT / UNPROTECT（pattern 規則）",
                "Diff & Versioning（patch log / replay / 回滾）",
                "CLI restore / inspect / replay",
                "PowerShell 單一進入點 Invoke-VTR.ps1",
            ],
            "not_implemented": [
                "P0 詞庫精確命中（待接 SSOT Lexicon）",
                "步驟 3 PUNCTUATE", "步驟 4 SEGMENT", "步驟 5 SPELL",
                "步驟 6 GRAMMAR", "步驟 7 LEXICON", "步驟 8 STRUCTURE",
                "LLM 仲裁層", "@dg-in/vtr-js",
            ],
            "third_party_dependencies":
                "無。確定性層僅使用 Python 標準函式庫，可在未安裝任何套件的環境執行。",
        },
        "verification": {
            "one_shot": "pwsh -File Invoke-VTR.ps1",
            "lexicon": "python3 lexicon/tools/validate_lexicon.py（exit 0/2/3）",
            "engine": "cd engine && python3 -m unittest discover -s tests -t .",
            "manifest": "python3 tools/build_manifest.py（exit 0/5）",
            "test_categories": ["單元", "屬性/不變式", "對抗", "回歸", "突變驗證"],
        },
        "lexicon": {
            "totals": idx["totals"],
            "scopes": idx["scopes"],
            "index_file": "lexicon/lexicon.index.json",
            "validator": "lexicon/tools/validate_lexicon.py",
        },
        "engine_contract": {
            "document_schema": "contracts/vtr-document.schema.json",
            "stages": ["LANG_DETECT", "NORMALIZE", "PROTECT", "PUNCTUATE", "SEGMENT",
                       "SPELL", "GRAMMAR", "LEXICON", "UNPROTECT", "STRUCTURE"],
            "confidence_gate": {"auto": ">=0.85", "review": "0.60-0.85",
                                "reject": "<0.60", "llm_only_ceiling": 0.80},
            "rule_id_namespace": "VTR.<STAGE>.<rule>",
            "invariants": [
                "只有 SEGMENT 可改變 segment 數量",
                "PROTECT 與 UNPROTECT 之間 sentinel 原封不動",
                "Patch.span 必須落在 Stage 執行前的合法範圍",
                "rule_id 必須已註冊於 RULE_REGISTRY",
            ],
            "rollback_semantics":
                "不變式違反時該 Stage 的所有 patch 一律不套用，但仍寫入 revision 記錄違反原因。",
            "cross_engine_rule":
                "Python 版與 JavaScript 版對同一規則必須使用同一 rule_id；"
                "Lexicon 比對分數差異須 < 0.01。",
        },
        "governance": {
            "intake_policy": (
                "新詞條一律 enabled=false 草稿（source=meeting_intake 強制 false）；"
                "啟用需 provenance.approved_by。由 validate_lexicon.py 強制。"),
            "restoration_policy": (
                "引擎僅產生 candidate + patch log，不得直接改寫 canonical 逐字稿。"
                "單獨 LLM 判斷信心度上限 0.80，永遠進人工複核（由 ConfidenceGate 建構時強制）。"),
            "audit_chain":
                "append-only patch log；每筆改動可回答 source / rule_id / evidence / confidence。",
            "promotion_gate": "OPERATOR_REVIEW_AND_SEPARATE_HASH_LOCKED_TRANSACTION_REQUIRED",
            "canonical_mutation_by_system_manager": False,
            "sandbox_repair_only": True,
        },
        "system_manager": {
            "version": "v0162B",
            "analyzed_sections": ["MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS"],
            "round_limit": 3,
        },
    }


def serialize(manifest: dict) -> str:
    return json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="重算 VTR 子系統 manifest")
    ap.add_argument("--write", action="store_true", help="寫回 manifest")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    fresh = serialize(build())

    if args.write:
        MANIFEST.write_text(fresh, encoding="utf-8")
        n = len(json.loads(fresh)["artifacts"])
        if not args.quiet:
            print(f"已寫入 {MANIFEST.name}（{n} 個 artifact）")
        return 0

    if not MANIFEST.exists():
        print("manifest 不存在；用 --write 建立", file=sys.stderr)
        return 5

    current = MANIFEST.read_text(encoding="utf-8")
    if current == fresh:
        if not args.quiet:
            n = len(json.loads(fresh)["artifacts"])
            print(f"manifest 與檔案一致（{n} 個 artifact）")
        return 0

    # 指出到底哪裡不一致，而不是只說「不一致」
    cur_arts = {a["filename"]: a["sha256"]
                for a in json.loads(current).get("artifacts", [])}
    new_arts = {a["filename"]: a["sha256"]
                for a in json.loads(fresh)["artifacts"]}
    for fn in sorted(set(cur_arts) | set(new_arts)):
        if fn not in cur_arts:
            print(f"NEW      {fn}", file=sys.stderr)
        elif fn not in new_arts:
            print(f"REMOVED  {fn}", file=sys.stderr)
        elif cur_arts[fn] != new_arts[fn]:
            print(f"CHANGED  {fn}", file=sys.stderr)
    print("manifest 與實際檔案不一致；執行 --write 更新", file=sys.stderr)
    return 5


if __name__ == "__main__":
    sys.exit(main())
