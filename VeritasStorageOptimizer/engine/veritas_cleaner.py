#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Veritas Engine - Local Storage Cleaner & Optimizer (2026 Production Edition)
Architecture: Standard Library Only / UTF-8 No BOM / Stream-Safe
"""
import os
import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# 預設保護名單與暫存檔檔名標籤
TEMP_EXTENSIONS = {".tmp", ".log", ".cache", ".bak", ".old", ".temp", ".swp", ".dmp"}
PROTECTED_DIRS = {".git", ".svn", ".venv", "node_modules", "site-packages", "$RECYCLE.BIN", "System Volume Information"}
DUP_MIN_BYTES = 1024  # 重複比對的最小檔案容量門檻


def is_skipped_dir(parent: str, name: str) -> bool:
    """保護名單、symlink,以及任何含 pyvenv.cfg 的 Python 虛擬環境一律跳過:
    各 venv 內含成千上萬相同的套件檔案,跨 venv 去重會毀掉第一個以外的環境。"""
    if name in PROTECTED_DIRS:
        return True
    dir_path = Path(parent) / name
    if dir_path.is_symlink():
        return True
    return (dir_path / "pyvenv.cfg").is_file()


def calculate_hash_stream(file_path: Path, chunk_size: int = 65536) -> str:
    """採用串流讀取計算 MD5,避免記憶體溢位"""
    hasher = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return ""


def format_size(size_bytes: float) -> str:
    """轉換容量格式為可讀字串"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def clean_empty_directories(target_path: Path, dry_run: bool = True) -> list:
    """由下而上遞迴清理空資料夾"""
    removed_dirs = []
    for root, dirs, _ in os.walk(target_path, topdown=False):
        for d in dirs:
            dir_path = Path(root) / d
            if is_skipped_dir(root, d):
                continue
            try:
                if not any(dir_path.iterdir()):
                    removed_dirs.append(dir_path)
                    if not dry_run:
                        dir_path.rmdir()
            except (PermissionError, OSError):
                continue
    return removed_dirs


def execute_cleanup(target_dir: str, size_threshold_mb: float, dry_run: bool = True,
                    log_file: str = "cleanup_audit.log"):
    target_path = Path(target_dir).resolve()
    if not target_path.exists() or not target_path.is_dir():
        print(f"[Error] Target directory '{target_dir}' does not exist.")
        sys.exit(1)

    print(f"=== Starting Scan: {target_path} (Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}) ===", flush=True)
    size_limit_bytes = int(size_threshold_mb * 1024 * 1024)
    size_groups = {}
    files_to_remove = []
    freed_bytes = 0

    # Pass 1: 遍歷檔案與處理暫存檔 / 超大檔案
    for root, dirs, files in os.walk(target_path):
        # 排除保護目錄 / symlink / Python 虛擬環境
        dirs[:] = [d for d in dirs if not is_skipped_dir(root, d)]

        for file in files:
            file_path = Path(root) / file

            try:
                file_size = file_path.stat().st_size
            except (PermissionError, OSError):
                continue

            # 策略 1: 刪除副檔名為暫存檔的檔案
            if file_path.suffix.lower() in TEMP_EXTENSIONS:
                files_to_remove.append((file_path, file_size, "Temp File"))
                freed_bytes += file_size
                continue

            # 策略 2: 標記超過閾值的大檔案 (非暫存檔)
            if file_size > size_limit_bytes:
                files_to_remove.append((file_path, file_size, f"Over Limit (>{size_threshold_mb}MB)"))
                freed_bytes += file_size
                continue

            # 策略 3: 為重複檔案比對收集「檔案大小相同的群組」
            # 小於 DUP_MIN_BYTES 的檔案不列入:刪除近乎零容量的「重複檔」
            # 釋放不了空間,卻常是 __init__.py / .gitkeep 等結構性檔案
            if file_size >= DUP_MIN_BYTES:
                size_groups.setdefault(file_size, []).append(file_path)

    # Pass 2: 針對容量相同的候選群組進行 Hash 比對
    for file_size, candidate_paths in size_groups.items():
        if len(candidate_paths) < 2:
            continue

        hashes = {}
        for path in candidate_paths:
            h = calculate_hash_stream(path)
            if not h:
                continue
            if h in hashes:
                files_to_remove.append((path, file_size, f"Duplicate of {hashes[h].name}"))
                freed_bytes += file_size
            else:
                hashes[h] = path

    # Pass 3: 執行刪除作業與日誌紀錄
    audit_logs = [
        "=== VERITAS CLEANUP AUDIT LOG ===",
        f"Timestamp: {datetime.now().isoformat()}",
        f"Target Directory: {target_path}",
        f"Execution Mode: {'DRY-RUN' if dry_run else 'LIVE_DELETE'}\n",
        "--- Target File Items ---"
    ]

    for path, size, reason in files_to_remove:
        line = f"[{reason}] {format_size(size)} -> {path}"
        audit_logs.append(line)
        print(line, flush=True)
        if not dry_run:
            try:
                path.unlink()
            except Exception as e:
                audit_logs.append(f"  └─ Failed to remove: {e}")

    removed_empty_dirs = clean_empty_directories(target_path, dry_run=dry_run)
    audit_logs.append("\n--- Removed Empty Directories ---")
    for d in removed_empty_dirs:
        audit_logs.append(f"[Empty Directory] -> {d}")
        print(f"[Empty Directory] -> {d}", flush=True)

    audit_logs.append("\nSummary:")
    audit_logs.append(f"Total Files Marked: {len(files_to_remove)}")
    audit_logs.append(f"Total Empty Dirs Marked: {len(removed_empty_dirs)}")
    audit_logs.append(f"Estimated Space Freed: {format_size(freed_bytes)}")

    # 寫入稽核日誌
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(audit_logs))

    print("Scan complete.")
    print(f"Items to purge: {len(files_to_remove)} files, {len(removed_empty_dirs)} empty folders.")
    print(f"Total Space to Free: {format_size(freed_bytes)}")
    print(f"Audit log saved to: {Path(log_file).resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Veritas Standard Storage Optimizer 2026")
    parser.add_argument("--dir", type=str, required=True, help="Target folder path to clean")
    parser.add_argument("--max-mb", type=float, default=200.0, help="File size limit threshold in MB")
    parser.add_argument("--log", type=str, default="cleanup_audit.log", help="Audit log output path")
    parser.add_argument("--execute", action="store_true",
                        help="Perform live deletion (Defaults to Dry-Run if omitted)")

    args = parser.parse_args()
    if not args.max_mb > 0:
        parser.error("--max-mb must be a positive number")
    execute_cleanup(target_dir=args.dir, size_threshold_mb=args.max_mb,
                    dry_run=not args.execute, log_file=args.log)
