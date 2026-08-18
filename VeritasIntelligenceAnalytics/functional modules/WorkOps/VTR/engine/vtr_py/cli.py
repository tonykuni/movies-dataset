"""vtr CLI（確定性層）。

    python3 -m vtr_py.cli restore <transcript.txt> --doc-id ID --out DIR
    python3 -m vtr_py.cli replay  <DIR> --to-rev N
    python3 -m vtr_py.cli inspect <DIR>

退出碼（與 01_PYTHON_ENGINE_SPEC.md §7 一致）：
    0 成功 · 2 契約驗證失敗 · 3 sentinel 完整性違反 · 4 改壞率超過門檻
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import json
import sys
from pathlib import Path

from .context import Config, Context
from .document import ContractError, Document
from .pipeline import InvariantViolation, preprocessing_pipeline
from .versioning.patchlog import PATCHLOG_NAME, write_patchlog
from .versioning.replay import ReplayMismatch, replay_to

EXIT_OK = 0
EXIT_CONTRACT = 2
EXIT_SENTINEL = 3
EXIT_HARMFUL = 4

DOC_NAME = "document.json"


def _load_doc(directory: Path) -> Document:
    return Document.from_json((directory / DOC_NAME).read_text(encoding="utf-8"))


def _resolve_doc(directory: Path) -> "Document | None":
    """讀取已修復文件；找不到或讀取失敗時印出中文指引並回傳 None。

    beginner 常照範例打了一個還沒 restore 過的 doc-id —— 要給清楚的下一步，
    而不是把 Python 的 FileNotFoundError 堆疊丟到他們臉上。
    """
    doc_path = directory / DOC_NAME
    if not doc_path.exists():
        print(f"找不到這份文件：{doc_path}", file=sys.stderr)
        print("這個 doc-id 還沒有被修復過，所以沒有東西可以檢視或回滾。",
              file=sys.stderr)
        print("請先用 restore 產生它。想直接看範例跑起來的話：", file=sys.stderr)
        print("  Run-VTR.cmd -Action Restore -Path .\\samples\\", file=sys.stderr)
        print("畫面會顯示產生出來的 doc-id，再用那個 id 執行 inspect / replay。",
              file=sys.stderr)
        return None
    try:
        return _load_doc(directory)
    except (OSError, ContractError, json.JSONDecodeError) as exc:
        print(f"文件讀取失敗：{exc}", file=sys.stderr)
        print("這份 document.json 可能損毀或不是 VTR 產生的。請重新 restore。",
              file=sys.stderr)
        return None


def _save(doc: Document, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / DOC_NAME).write_text(doc.to_json(), encoding="utf-8")
    n = write_patchlog(doc, out / PATCHLOG_NAME)
    print(f"寫入 {out / DOC_NAME}")
    print(f"寫入 {out / PATCHLOG_NAME}（{n} 筆）")


def _summarize(doc: Document) -> None:
    print(f"\ndoc_id      {doc.doc_id}")
    print(f"rev         {doc.rev}")
    print(f"content_hash{'':1}{doc.content_hash[:16]}…")
    print(f"segments    {len(doc.segments)}")
    langs: dict[str, int] = {}
    for s in doc.segments:
        langs[s.lang] = langs.get(s.lang, 0) + 1
    print(f"語言分布    {dict(sorted(langs.items()))}")
    print(f"review 佇列 {len(doc.review_queue)} 筆")
    print("\nrev  stage        applied  metrics")
    for r in doc.revisions:
        keys = {k: v for k, v in r.metrics.items()
                if k in ("patches_applied", "patches_review", "degraded",
                         "protected_total", "unresolved_entities",
                         "stage_rolled_back")}
        print(f"{r.rev:>3}  {r.stage:<12} {len(r.patches_applied):>7}  {keys}")


def cmd_restore(args: argparse.Namespace) -> int:
    raw = Path(args.transcript).read_text(encoding="utf-8")
    meta = json.loads(args.meta) if args.meta else None
    doc = Document.from_raw_text(raw, doc_id=args.doc_id, meta=meta)

    config = Config.load(Path(args.config)) if args.config else Config()
    if args.strict:
        config = Config({**config.data,
                         "pipeline": {**config.data.get("pipeline", {}),
                                      "strict": True}})
    ctx = Context(config=config)

    try:
        result = preprocessing_pipeline().run(doc, ctx)
    except InvariantViolation as exc:
        print(f"不變式違反：\n{exc}", file=sys.stderr)
        return EXIT_SENTINEL
    except ContractError as exc:
        print(f"契約違反：{exc}", file=sys.stderr)
        return EXIT_CONTRACT

    rolled_back = [r for r in result.revisions
                   if r.metrics.get("stage_rolled_back")]
    _save(result, Path(args.out))
    _summarize(result)
    if rolled_back:
        print(f"\n⚠ {len(rolled_back)} 個 Stage 因不變式違反被回退：",
              file=sys.stderr)
        for r in rolled_back:
            for v in r.metrics.get("invariant_violations", []):
                print(f"  - [{r.stage}] {v}", file=sys.stderr)
        return EXIT_SENTINEL
    return EXIT_OK


def cmd_replay(args: argparse.Namespace) -> int:
    doc = _resolve_doc(Path(args.directory))
    if doc is None:
        return EXIT_CONTRACT
    try:
        out_doc = replay_to(doc, args.to_rev)
    except ReplayMismatch as exc:
        print(f"重播失敗：{exc}", file=sys.stderr)
        return EXIT_CONTRACT
    out = Path(args.out) if args.out else Path(args.directory) / f"rev{args.to_rev}"
    _save(out_doc, out)
    _summarize(out_doc)
    return EXIT_OK


def cmd_inspect(args: argparse.Namespace) -> int:
    doc = _resolve_doc(Path(args.directory))
    if doc is None:
        return EXIT_CONTRACT
    _summarize(doc)
    if args.review:
        print("\n待裁決佇列：")
        for p in doc.review_queue:
            print(f"  {p.patch_id} [{p.rule_id}] {p.before!r} → {p.after!r}"
                  f"  conf={p.confidence:.2f}")
            if p.evidence:
                print(f"      {p.evidence}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="vtr", description="VTR 會議紀錄修復引擎（確定性層）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("restore", help="對逐字稿執行 Preprocessing Pipeline")
    r.add_argument("transcript")
    r.add_argument("--doc-id", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--config")
    r.add_argument("--meta", help="JSON 字串，覆寫 document.meta")
    r.add_argument("--strict", action="store_true",
                   help="不變式違反直接失敗，而非回退該 Stage")
    r.set_defaults(func=cmd_restore)

    p = sub.add_parser("replay", help="重播 / 回滾到指定 rev")
    p.add_argument("directory")
    p.add_argument("--to-rev", type=int, required=True)
    p.add_argument("--out")
    p.set_defaults(func=cmd_replay)

    i = sub.add_parser("inspect", help="檢視文件狀態")
    i.add_argument("directory")
    i.add_argument("--review", action="store_true", help="列出待裁決佇列")
    i.set_defaults(func=cmd_inspect)

    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
