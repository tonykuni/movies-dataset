#!/usr/bin/env python3
"""VTR SSOT Lexicon validator / indexer.

驗證 lexicon/*.json 是否符合 SSOT 規則，並產生 lexicon.index.json（含 SHA-256）。

用法:
    python3 validate_lexicon.py                 # 驗證
    python3 validate_lexicon.py --write-index   # 驗證並更新 lexicon.index.json

退出碼:
    0  通過（可能有 warning）
    2  結構/schema 錯誤
    3  SSOT 一致性錯誤（id 重複、alias 衝突、危險詞條…）

若安裝了 jsonschema，會額外做完整 JSON Schema 驗證；未安裝時只跑本檔內建的結構檢查
（內建檢查涵蓋所有會造成引擎誤修的情況，schema 驗證是額外保險）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = LEXICON_DIR / "schema" / "vtr-lexicon.schema.json"
INDEX_PATH = LEXICON_DIR / "lexicon.index.json"

FILES = {
    "project": "projects.json",
    "product": "products.json",
    "person": "people.json",
    "part_number": "partnumbers.json",
    "domain_term": "domain.json",
}

KIND_PREFIX = {
    "project": "PRJ",
    "product": "PRD",
    "person": "PER",
    "part_number": "PN",
    "domain_term": "DOM",
}

ID_RE = re.compile(r"^LEX-(PRJ|PRD|PER|PN|DOM)-\d{4}$")
SCOPE_RE = re.compile(r"^(global|project:[A-Za-z0-9_-]+|customer:[A-Za-z0-9_-]+|dept:[A-Za-z0-9_-]+)$")
TEMPLATE_RE = re.compile(r"^<.*>$")
ALIAS_TYPES = {"abbrev", "spoken", "asr_error", "legacy", "translation", "typo"}
STATUSES = {"draft", "active", "deprecated"}
LANGS = {"zh", "en", "mixed", "code"}
SOURCES = {"operator", "meeting_intake", "erp_import", "migration"}

# 短別名若未設 exact_only，模糊比對極易誤命中一般詞。
SHORT_ALIAS_LEN = 3


class Report:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        self.schema_errors: list[tuple[str, str]] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append((where, msg))

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append((where, msg))

    def schema_error(self, where: str, msg: str) -> None:
        self.schema_errors.append((where, msg))


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_files(rep: Report) -> dict[str, dict]:
    docs: dict[str, dict] = {}
    for kind, name in FILES.items():
        path = LEXICON_DIR / name
        if not path.exists():
            rep.schema_error(name, "檔案不存在")
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rep.schema_error(name, f"JSON 解析失敗: {exc}")
            continue
        if doc.get("schema_version") != "vtr-lexicon/1.0":
            rep.schema_error(name, f"schema_version 應為 vtr-lexicon/1.0，實得 {doc.get('schema_version')!r}")
        if doc.get("kind") != kind:
            rep.schema_error(name, f"kind 應為 {kind!r}，實得 {doc.get('kind')!r}")
        if not isinstance(doc.get("entries"), list):
            rep.schema_error(name, "entries 必須為陣列")
            continue
        docs[name] = doc
    return docs


def check_structure(name: str, doc: dict, rep: Report) -> None:
    kind = doc.get("kind", "")
    want_prefix = KIND_PREFIX.get(kind)
    for i, e in enumerate(doc.get("entries", [])):
        where = f"{name}[{i}]"
        eid = e.get("id")
        if not isinstance(eid, str) or not ID_RE.match(eid):
            rep.schema_error(where, f"id 格式不合法: {eid!r}")
            continue
        where = f"{name}:{eid}"

        if want_prefix and not eid.startswith(f"LEX-{want_prefix}-"):
            rep.error(where, f"id 前綴與 kind 不符，應為 LEX-{want_prefix}-")

        for field in ("canonical", "lang", "status", "enabled", "scope", "provenance"):
            if field not in e:
                rep.schema_error(where, f"缺少必要欄位 {field}")

        if not isinstance(e.get("canonical"), str) or not e.get("canonical"):
            rep.schema_error(where, "canonical 必須為非空字串")
        if e.get("lang") not in LANGS:
            rep.schema_error(where, f"lang 不合法: {e.get('lang')!r}")
        if e.get("status") not in STATUSES:
            rep.schema_error(where, f"status 不合法: {e.get('status')!r}")
        if not isinstance(e.get("enabled"), bool):
            rep.schema_error(where, "enabled 必須為布林值")

        scope = e.get("scope")
        if not isinstance(scope, list) or not scope:
            rep.schema_error(where, "scope 必須為非空陣列")
        else:
            for s in scope:
                if not isinstance(s, str) or not SCOPE_RE.match(s):
                    rep.schema_error(where, f"scope 值不合法: {s!r}")

        prov = e.get("provenance")
        if not isinstance(prov, dict):
            rep.schema_error(where, "provenance 必須為物件")
        else:
            for field in ("created_at", "created_by", "source"):
                if field not in prov:
                    rep.schema_error(where, f"provenance 缺少 {field}")
            if prov.get("source") not in SOURCES:
                rep.schema_error(where, f"provenance.source 不合法: {prov.get('source')!r}")

        for j, a in enumerate(e.get("aliases", []) or []):
            aw = f"{where}.aliases[{j}]"
            if not isinstance(a, dict):
                rep.schema_error(aw, "alias 必須為物件")
                continue
            if not isinstance(a.get("surface"), str) or not a.get("surface"):
                rep.schema_error(aw, "alias.surface 必須為非空字串")
            if a.get("type") not in ALIAS_TYPES:
                rep.schema_error(aw, f"alias.type 不合法: {a.get('type')!r}")


def check_ssot(docs: dict[str, dict], rep: Report) -> None:
    """SSOT 一致性 —— 這些錯誤會直接造成引擎誤修，優先級高於 schema。"""
    ids: dict[str, str] = {}
    canon_owner: dict[str, str] = {}          # canonical(casefold) -> entry id
    alias_owner: dict[str, list[str]] = defaultdict(list)  # surface(casefold) -> [entry id]
    # surface(casefold) -> [(entry id, auto_correct)]，用於反向護欄檢查
    alias_detail: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    guard_canon: set[str] = set()             # negative_guard 詞條的 canonical(casefold)
    all_entries: dict[str, dict] = {}

    for name, doc in docs.items():
        for e in doc.get("entries", []):
            eid = e.get("id")
            if not isinstance(eid, str) or not ID_RE.match(eid):
                continue
            where = f"{name}:{eid}"
            if eid in ids:
                rep.error(where, f"id 重複，已出現於 {ids[eid]}")
                continue
            ids[eid] = where
            all_entries[eid] = e

            canon = (e.get("canonical") or "")
            key = canon.casefold()
            if key in canon_owner:
                rep.error(where, f"canonical {canon!r} 與 {canon_owner[key]} 重複 —— canonical 必須全域唯一")
            else:
                canon_owner[key] = eid

            policy = e.get("match_policy") or {}
            is_template = bool(TEMPLATE_RE.match(canon))
            if policy.get("negative_guard"):
                guard_canon.add(key)

            for a in e.get("aliases", []) or []:
                surface = a.get("surface") or ""
                auto = a.get("auto_correct", True)
                alias_owner[surface.casefold()].append(eid)
                alias_detail[surface.casefold()].append((eid, bool(auto)))
                if (not is_template
                        and not TEMPLATE_RE.match(surface)
                        and len(surface) < SHORT_ALIAS_LEN
                        and auto
                        and not policy.get("exact_only")):
                    rep.warn(
                        f"{where}.aliases[{surface!r}]",
                        f"別名長度 < {SHORT_ALIAS_LEN} 且未設 match_policy.exact_only —— "
                        "模糊比對可能誤命中一般詞",
                    )

    # alias 指向多個 canonical → 無法決定收斂目標
    for surface, owners in alias_owner.items():
        if TEMPLATE_RE.match(surface):
            continue
        distinct = sorted(set(owners))
        if len(distinct) > 1:
            rep.error(
                f"alias:{surface!r}",
                f"同一別名被 {len(distinct)} 個詞條宣告（{', '.join(distinct)}）—— 收斂目標不明確",
            )

    # alias 與別的詞條的 canonical 相同 → 會互相收斂成環。
    # 唯一合法例外：該 canonical 屬於 negative_guard 詞條，且所有引用它的別名皆 auto_correct=false
    # （代表「辨識得到、但一律送仲裁」，而非自動收斂）。
    for surface, owners in alias_owner.items():
        if TEMPLATE_RE.match(surface):
            continue
        owner_of_canon = canon_owner.get(surface)
        if not owner_of_canon or owner_of_canon in owners:
            continue
        if surface in guard_canon:
            offenders = [eid for eid, auto in alias_detail[surface] if auto]
            if offenders:
                rep.error(
                    f"alias:{surface!r}",
                    f"{owner_of_canon} 為 negative_guard 詞條，"
                    f"但 {', '.join(sorted(set(offenders)))} 以它為別名且 auto_correct=true —— "
                    "護欄詞必須設 auto_correct=false，改由仲裁決定",
                )
            continue
        rep.error(
            f"alias:{surface!r}",
            f"此字串同時是 {owner_of_canon} 的 canonical 與 {owners[0]} 的別名 —— 會造成收斂環。"
            "若這是刻意的一般詞衝突，請在 canonical 端設 match_policy.negative_guard=true"
            "並將別名設 auto_correct=false",
        )

    # 狀態一致性
    for eid, e in all_entries.items():
        where = ids[eid]
        status, enabled = e.get("status"), e.get("enabled")
        if status == "draft" and enabled:
            rep.error(where, "status=draft 的詞條必須 enabled=false（VIA intake policy）")
        if status == "deprecated" and e.get("deprecated_by") is None:
            rep.warn(where, "status=deprecated 但未指定 deprecated_by")
        dep = e.get("deprecated_by")
        if dep and dep not in all_entries:
            rep.error(where, f"deprecated_by 指向不存在的詞條 {dep}")

        prov = e.get("provenance") or {}
        if enabled and prov.get("approved_by") in (None, ""):
            rep.error(where, "enabled=true 但 provenance.approved_by 為空 —— 未經覆核不得啟用")
        if prov.get("source") == "meeting_intake" and enabled:
            rep.error(where, "source=meeting_intake 的詞條不得直接 enabled=true")

        # 料號安全護欄
        if eid.startswith("LEX-PN-"):
            policy = e.get("match_policy") or {}
            canon = e.get("canonical") or ""
            if not policy.get("exact_only") and not policy.get("case_sensitive"):
                rep.warn(
                    where,
                    "料號詞條未設 exact_only 或 case_sensitive —— 料號模糊比對是高風險行為",
                )
            if TEMPLATE_RE.match(canon) and not policy.get("exact_only"):
                rep.error(where, "料號範本詞條必須設 exact_only=true")


def check_with_jsonschema(docs: dict[str, dict], rep: Report) -> bool:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return False
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    for name, doc in docs.items():
        for err in validator.iter_errors(doc):
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            rep.schema_error(f"{name}:{loc}", err.message)
    return True


def build_index(docs: dict[str, dict]) -> dict:
    files = []
    for kind, name in FILES.items():
        path = LEXICON_DIR / name
        if not path.exists():
            continue
        entries = docs.get(name, {}).get("entries", [])
        files.append({
            "filename": name,
            "kind": kind,
            "entries": len(entries),
            "enabled": sum(1 for e in entries if e.get("enabled")),
            "draft": sum(1 for e in entries if e.get("status") == "draft"),
            "aliases": sum(len(e.get("aliases") or []) for e in entries),
            "bytes": path.stat().st_size,
            "sha256": sha256_of(path),
        })
    scopes = sorted({
        s
        for doc in docs.values()
        for e in doc.get("entries", [])
        for s in (e.get("scope") or [])
    })
    return {
        "schema_version": "vtr-lexicon-index/1.0",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": "validate_lexicon.py",
        "schema": {
            "filename": "schema/vtr-lexicon.schema.json",
            "sha256": sha256_of(SCHEMA_PATH) if SCHEMA_PATH.exists() else None,
        },
        "files": files,
        "totals": {
            "entries": sum(f["entries"] for f in files),
            "enabled": sum(f["enabled"] for f in files),
            "draft": sum(f["draft"] for f in files),
            "aliases": sum(f["aliases"] for f in files),
        },
        "scopes": scopes,
        "governance": {
            "intake_policy": "新詞一律 enabled=false 草稿；啟用需 provenance.approved_by",
            "promotion_gate": "OPERATOR_REVIEW_AND_SEPARATE_HASH_LOCKED_TRANSACTION_REQUIRED",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="VTR SSOT Lexicon validator")
    ap.add_argument("--write-index", action="store_true", help="驗證通過後更新 lexicon.index.json")
    ap.add_argument("--quiet", action="store_true", help="只輸出錯誤")
    args = ap.parse_args()

    rep = Report()
    docs = load_files(rep)
    for name, doc in docs.items():
        check_structure(name, doc, rep)
    check_ssot(docs, rep)
    used_schema = check_with_jsonschema(docs, rep)

    for where, msg in rep.schema_errors:
        print(f"SCHEMA  {where}: {msg}")
    for where, msg in rep.errors:
        print(f"ERROR   {where}: {msg}")
    if not args.quiet:
        for where, msg in rep.warnings:
            print(f"WARN    {where}: {msg}")

    index = build_index(docs)
    if not args.quiet:
        t = index["totals"]
        print(
            f"\n詞條 {t['entries']}（啟用 {t['enabled']} / 草稿 {t['draft']}）"
            f"・別名 {t['aliases']}・scope {len(index['scopes'])}"
            f"・jsonschema {'已套用' if used_schema else '未安裝（僅內建檢查）'}"
        )

    if rep.schema_errors:
        return 2
    if rep.errors:
        return 3

    if args.write_index:
        INDEX_PATH.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if not args.quiet:
            print(f"已寫入 {INDEX_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
