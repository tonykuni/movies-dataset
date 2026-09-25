#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Snapshot Integration v1.0
==============================
L: 註冊到 via 主路由 (via via-snapshot / via via-verify / via via-rollback)
N: 自動快照 + 保留策略 (retention policy)
O: 跨機同步 (filesystem mirror / S3 / OneDrive / Git LFS)

此檔放在產品根目錄的 tools/ 下；由 snapshot_install.ps1 安裝註冊。

依賴：via_inventory.py 必須已存在於 tools/ 下 (前面 K 章節的成果)。

子命令:
  install         把所有 snapshot 指令註冊到 commands.json (主路由可呼叫)
  auto            自動快照模式 (適合掛 hook 或定時任務)
  retention       套用保留策略 (清理舊快照)
  sync            把 snapshots/ 推到遠端
  pull            從遠端拉回缺失的快照
  hook            列出/設定自動觸發點 (post-activate, post-forge, pre-commit, daily)
  status          顯示同步與保留狀態
"""

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


import os, sys, json, hashlib, hmac, shutil, argparse, datetime, subprocess, fnmatch, re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# ============================================================
# 環境檢測 — 找到 VIA 產品根目錄
# ============================================================
def find_via_root(start: Path = None) -> Path:
    """從當前位置往上找，直到看到 via.ps1 + config/via.config.json"""
    p = Path(start or Path.cwd()).resolve()
    for _ in range(8):
        if (p / "via.ps1").exists() and (p / "config" / "via.config.json").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return Path.cwd()

VIA_ROOT = find_via_root()
SNAP_ROOT = VIA_ROOT / "snapshots"
SYNC_CONFIG = VIA_ROOT / "config" / "snapshot_sync.json"
HOOK_CONFIG = VIA_ROOT / "config" / "snapshot_hooks.json"
COMMANDS_JSON = VIA_ROOT / "config" / "commands.json"
AUDIT_LOG = VIA_ROOT / "logs" / "audit.log"

def now_iso() -> str:
    try:
        d = datetime.datetime.now(datetime.UTC).replace(microsecond=0, tzinfo=None)
    except AttributeError:
        d = datetime.datetime.utcnow().replace(microsecond=0)
    return d.isoformat() + "Z"

def banner(s: str):
    print("\n" + "=" * 66)
    print(f"  {s}")
    print("=" * 66)

def log_audit(action: str, detail: Any):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"ts": now_iso(), "action": action, "detail": detail},
                       ensure_ascii=False)
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def call_inventory(args: List[str], capture: bool = False) -> subprocess.CompletedProcess:
    """呼叫 via_inventory.py 子命令"""
    inv_path = VIA_ROOT / "tools" / "via_inventory.py"
    if not inv_path.exists():
        raise FileNotFoundError(f"找不到 {inv_path}；請先安裝 via_inventory.py")
    cmd = [sys.executable, str(inv_path), "--base", str(VIA_ROOT), *args]
    return subprocess.run(cmd, capture_output=capture, text=True)


# ============================================================
# L) CLI 整合 — 把指令註冊到 commands.json
# ============================================================
#
# CMD-ID 規範 (VIA.SNAP 是新領域編號，永不重用):
#   VIA.SNAP.CREATE.001     via-snapshot      手動拍快照
#   VIA.SNAP.LIST.001       via-snap-list     列出所有快照
#   VIA.SNAP.DIFF.001       via-snap-diff     比對兩版
#   VIA.SNAP.VERIFY.001     via-verify        驗證完整性
#   VIA.SNAP.ROLLBACK.001   via-rollback      回滾
#   VIA.SNAP.BUMP.001       via-bump          升版號
#   VIA.SNAP.AUTO.001       via-snap-auto     自動快照模式
#   VIA.SNAP.RETAIN.001     via-snap-retain   套用保留策略
#   VIA.SNAP.SYNC.001       via-snap-sync     推到遠端
#   VIA.SNAP.PULL.001       via-snap-pull     從遠端拉回
#   VIA.SNAP.STATUS.001     via-snap-status   同步狀態
#   VIA.SNAP.HOOK.001       via-snap-hook     設定自動觸發
#   VIA.SNAP.CONSOLE.001    via-snap-console  開啟儀表板 HTML

SNAPSHOT_COMMANDS = [
    {"id":"VIA.SNAP.CREATE.001",   "alias":"via-snapshot",     "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"手動拍系統快照"},
    {"id":"VIA.SNAP.LIST.001",     "alias":"via-snap-list",    "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"列出所有快照"},
    {"id":"VIA.SNAP.DIFF.001",     "alias":"via-snap-diff",    "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"比對兩個快照差異"},
    {"id":"VIA.SNAP.VERIFY.001",   "alias":"via-verify",       "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"驗證快照完整性 (HMAC + SHA256)"},
    {"id":"VIA.SNAP.ROLLBACK.001", "alias":"via-rollback",     "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"回滾到指定快照"},
    {"id":"VIA.SNAP.BUMP.001",     "alias":"via-bump",         "subsystem":"VIA",
     "script":"tools/via_inventory.py", "description":"升版號 (patch/minor/major)"},
    {"id":"VIA.SNAP.AUTO.001",     "alias":"via-snap-auto",    "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"自動快照 (給 hook 用)"},
    {"id":"VIA.SNAP.RETAIN.001",   "alias":"via-snap-retain",  "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"套用保留策略清理"},
    {"id":"VIA.SNAP.SYNC.001",     "alias":"via-snap-sync",    "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"推快照到遠端"},
    {"id":"VIA.SNAP.PULL.001",     "alias":"via-snap-pull",    "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"從遠端拉回快照"},
    {"id":"VIA.SNAP.STATUS.001",   "alias":"via-snap-status",  "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"顯示快照與同步狀態"},
    {"id":"VIA.SNAP.HOOK.001",     "alias":"via-snap-hook",    "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"設定自動觸發點"},
    {"id":"VIA.SNAP.CONSOLE.001",  "alias":"via-snap-console", "subsystem":"VIA",
     "script":"tools/via_snapshot_integration.py", "description":"開啟快照儀表板 HTML"},
]

def cmd_install(args):
    """L: 註冊到 commands.json"""
    banner("INSTALL — 註冊 snapshot 指令到主路由")
    if not COMMANDS_JSON.exists():
        print(f"  ✗ 找不到 {COMMANDS_JSON}")
        print(f"    請先用 Forge 生成基本產品骨架")
        sys.exit(1)

    data = json.loads(COMMANDS_JSON.read_text(encoding="utf-8"))
    existing = {c["id"] for c in data.get("commands", [])}

    added = 0; skipped = 0
    for c in SNAPSHOT_COMMANDS:
        if c["id"] in existing:
            skipped += 1
            continue
        c = {**c, "status": "Active"}
        data["commands"].append(c)
        added += 1
        print(f"  ✓ {c['id']:28s}  {c['alias']:22s}  {c['description']}")

    data["last_modified"] = now_iso()
    COMMANDS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    print(f"\n  Added: {added}  Skipped: {skipped}")
    print(f"  ✓ commands.json 已更新")
    log_audit("snapshot_install", {"added": added, "skipped": skipped})

    print(f"\n  測試: via via-snap-status")


# ============================================================
# N) 自動快照 + 保留策略
# ============================================================
DEFAULT_RETENTION = {
    "keep_all_major":    True,    # 1.0.0, 2.0.0, ... 永遠保留
    "keep_all_minor":    True,    # 1.1.0, 1.2.0, ... 永遠保留
    "keep_recent_patch": 10,      # PATCH 版只保留最近 N 個
    "keep_all_archived": True,    # 有 files.tar.gz 的永遠保留
    "min_age_days":      1,       # 1 天內的快照永遠保留
    "max_total":         100,     # 總數上限 (硬上限)
}

HOOK_TRIGGERS = {
    "post-activate":  "via via-activate 成功後自動拍",
    "post-forge":     "Forge 重新生成產品包後自動拍",
    "pre-rollback":   "回滾前先拍安全快照",
    "daily":          "每天一次 (由排程器觸發)",
    "on-config-change": "config/ 內任何檔案異動時觸發",
}

def parse_snap_id(snap_id: str) -> Tuple[int, int, int, str]:
    """v1.2.3_20260523-153045_a3f8b2c1 → (1,2,3, timestamp)"""
    m = re.match(r"^v(\d+)\.(\d+)\.(\d+)_(\d{8}-\d{6})_", snap_id)
    if not m:
        return (0, 0, 0, "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4))

def is_archived(snap_dir: Path) -> bool:
    return (snap_dir / "files.tar.gz").exists()

def cmd_auto(args):
    """N: 自動快照模式 — 由 hook 觸發"""
    trigger = args.trigger or "manual"
    banner(f"AUTO SNAPSHOT — trigger: {trigger}")

    # 決定要不要拍
    hooks = load_hooks()
    if trigger != "manual" and trigger not in hooks.get("enabled", []):
        print(f"  ⊘ hook '{trigger}' 未啟用，跳過")
        return

    note = args.note or f"auto: {trigger}"
    extra = []
    if args.archive: extra.append("--archive")
    if args.include_auth: extra.append("--include-auth")
    extra.extend(["--note", note])

    r = call_inventory(["snapshot", *extra])
    log_audit("auto_snapshot", {"trigger": trigger, "exit": r.returncode})

    # 拍完套用保留策略
    if hooks.get("auto_retention", True):
        print("\n  套用保留策略 ...")
        apply_retention(load_retention(), dry_run=False)

    # 拍完自動 sync (若有設定)
    cfg = load_sync_config()
    if cfg and cfg.get("auto_push", False):
        print("\n  自動推送到遠端 ...")
        push_to_remote(cfg, dry_run=False)


def load_retention() -> Dict[str, Any]:
    p = VIA_ROOT / "config" / "snapshot_retention.json"
    if p.exists():
        return {**DEFAULT_RETENTION, **json.loads(p.read_text(encoding="utf-8"))}
    return dict(DEFAULT_RETENTION)


def save_retention(d: Dict[str, Any]):
    p = VIA_ROOT / "config" / "snapshot_retention.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def list_snapshots_local() -> List[Dict[str, Any]]:
    if not SNAP_ROOT.exists(): return []
    items = []
    for d in sorted(SNAP_ROOT.iterdir()):
        if not d.is_dir(): continue
        inv_path = d / "INVENTORY.json"
        if not inv_path.exists(): continue
        try:
            inv = json.loads(inv_path.read_text(encoding="utf-8"))
            major, minor, patch, ts = parse_snap_id(d.name)
            items.append({
                "snap_id": d.name, "path": d,
                "major": major, "minor": minor, "patch": patch,
                "ts": ts, "version": inv.get("version"),
                "scanned_at": inv.get("scanned_at"),
                "archived": is_archived(d),
                "note": inv.get("note") or "",
            })
        except Exception as e:
            print(f"  ⚠ {d.name}: {e}")
    return items


def apply_retention(policy: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    items = list_snapshots_local()
    if not items:
        return {"deleted": 0, "kept": 0, "items": []}

    try:
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    except AttributeError:
        now = datetime.datetime.utcnow()
    min_age_cutoff = now - datetime.timedelta(days=policy["min_age_days"])

    # 分類
    keep: List[Dict] = []
    delete: List[Dict] = []

    # 按 (major, minor, patch, ts) 排序
    items_sorted = sorted(items, key=lambda x: (x["major"], x["minor"], x["patch"], x["ts"]))

    # 先標記必保留
    by_major = {}
    by_minor = {}
    patch_groups: Dict[Tuple[int,int], List[Dict]] = {}

    for it in items_sorted:
        key_major = it["major"]
        key_minor = (it["major"], it["minor"])
        # patch=0 表示是 .0 release → 視為 minor
        is_minor_release = it["patch"] == 0 and it["minor"] > 0
        is_major_release = it["patch"] == 0 and it["minor"] == 0

        # 收集 patch 群組 (同 major.minor 下的 patch 版)
        patch_groups.setdefault(key_minor, []).append(it)

    # 對每個 (major,minor) 群組保留最近 N 個 patch
    for key, group in patch_groups.items():
        # 排序：時間新到舊
        group_sorted = sorted(group, key=lambda x: x["ts"], reverse=True)
        kept_in_group = set()
        for idx, it in enumerate(group_sorted):
            reasons = []
            # 1. min age
            try:
                ts_dt = datetime.datetime.strptime(it["ts"], "%Y%m%d-%H%M%S")
                if ts_dt > min_age_cutoff:
                    reasons.append(f"<{policy['min_age_days']}d")
            except: pass

            # 2. major release
            if policy["keep_all_major"] and it["patch"] == 0 and it["minor"] == 0:
                reasons.append("major")

            # 3. minor release
            if policy["keep_all_minor"] and it["patch"] == 0 and it["minor"] > 0:
                reasons.append("minor")

            # 4. archived
            if policy["keep_all_archived"] and it["archived"]:
                reasons.append("archived")

            # 5. recent patch (前 N 個)
            if it["patch"] > 0 and idx < policy["keep_recent_patch"]:
                reasons.append(f"recent[{idx+1}/{policy['keep_recent_patch']}]")

            if reasons:
                it["_keep_reasons"] = reasons
                keep.append(it)
                kept_in_group.add(it["snap_id"])
            else:
                it["_delete_reason"] = "old patch beyond keep_recent_patch"
                delete.append(it)

    # max_total 硬上限：若 keep 超過上限，從最舊的 non-major/minor 開始刪
    if len(keep) > policy["max_total"]:
        excess = len(keep) - policy["max_total"]
        # 排除必保（major/minor/archived/recent）
        deletable = [k for k in keep if not any(r in ["major","minor","archived"]
                                                 for r in k["_keep_reasons"])]
        deletable.sort(key=lambda x: x["ts"])
        to_remove = deletable[:excess]
        for r in to_remove:
            r["_delete_reason"] = "max_total exceeded"
            delete.append(r)
            keep.remove(r)

    # 執行
    print(f"\n  Policy: keep_all_major={policy['keep_all_major']}, "
          f"keep_all_minor={policy['keep_all_minor']}, "
          f"keep_recent_patch={policy['keep_recent_patch']}")
    print(f"  Total: {len(items)}  Keep: {len(keep)}  Delete: {len(delete)}")
    if dry_run:
        print(f"\n  [DRY-RUN] 不會真的刪除")

    for it in delete:
        action = "[DRY] would delete" if dry_run else "delete"
        print(f"  - {action}: {it['snap_id']}  ({it.get('_delete_reason','')})")
        if not dry_run:
            shutil.rmtree(it["path"])
            log_audit("retention_delete", it["snap_id"])

    for it in keep:
        print(f"  ✓ keep: {it['snap_id']}  [{', '.join(it['_keep_reasons'])}]")

    return {"deleted": len(delete), "kept": len(keep),
            "items": [{"snap_id": x["snap_id"],
                       "action": "delete" if x in delete else "keep",
                       "reason": x.get("_delete_reason") or ", ".join(x.get("_keep_reasons", []))}
                       for x in items]}


def cmd_retention(args):
    """N: 套用保留策略"""
    banner("RETENTION POLICY")
    policy = load_retention()
    print("  Current policy:")
    for k, v in policy.items():
        print(f"    {k:22s} = {v}")
    apply_retention(policy, dry_run=not args.execute)
    if not args.execute:
        print(f"\n  ⚠ 這是 DRY-RUN。要真的刪除請加 --execute")


# ============================================================
# O) 跨機同步
# ============================================================
SYNC_BACKENDS = {
    "filesystem": "本機/網路磁碟 (UNC path / mapped drive)",
    "onedrive":   "OneDrive 同步資料夾 (本機路徑即可)",
    "s3":         "AWS S3 (需 aws-cli 已設定)",
    "git":        "Git LFS repo",
    "rsync":      "rsync (Linux/macOS or WSL)",
    "robocopy":   "robocopy (Windows)",
}

def load_sync_config() -> Optional[Dict[str, Any]]:
    if SYNC_CONFIG.exists():
        return json.loads(SYNC_CONFIG.read_text(encoding="utf-8"))
    return None

def save_sync_config(cfg: Dict[str, Any]):
    SYNC_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    SYNC_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                            encoding="utf-8")


def push_to_remote(cfg: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    backend = cfg["backend"]
    remote  = cfg["remote"]
    print(f"\n  Backend: {backend}")
    print(f"  Remote : {remote}")
    if dry_run:
        print(f"  [DRY-RUN]")

    local_items = list_snapshots_local()
    if not local_items:
        return {"pushed": 0, "skipped": 0, "error": "no local snapshots"}

    pushed = 0; skipped = 0; errors = []

    if backend in ("filesystem", "onedrive"):
        remote_path = Path(remote)
        if not dry_run:
            remote_path.mkdir(parents=True, exist_ok=True)
        for it in local_items:
            dst = remote_path / it["snap_id"]
            if dst.exists():
                print(f"  ⊘ skip (exists): {it['snap_id']}")
                skipped += 1; continue
            print(f"  → push: {it['snap_id']}")
            if not dry_run:
                shutil.copytree(it["path"], dst)
            pushed += 1

    elif backend == "robocopy":
        # Windows robocopy
        cmd_base = ["robocopy", str(SNAP_ROOT), str(remote), "/E", "/COPY:DAT",
                    "/R:2", "/W:5", "/NP", "/NDL"]
        print(f"  cmd: {' '.join(cmd_base)}")
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            # robocopy 退出碼 0-7 都算正常
            if r.returncode > 7:
                errors.append(r.stderr or r.stdout)
            else:
                pushed = len(local_items)

    elif backend == "rsync":
        cmd_base = ["rsync", "-a", "--progress", f"{SNAP_ROOT}/", remote]
        print(f"  cmd: {' '.join(cmd_base)}")
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(r.stderr)
            else:
                pushed = len(local_items)

    elif backend == "s3":
        cmd_base = ["aws", "s3", "sync", str(SNAP_ROOT), remote]
        if cfg.get("storage_class"):
            cmd_base.extend(["--storage-class", cfg["storage_class"]])
        print(f"  cmd: {' '.join(cmd_base)}")
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(r.stderr)
            else:
                pushed = len(local_items)

    elif backend == "git":
        # Git LFS
        repo_dir = Path(remote)
        if not dry_run:
            if not (repo_dir / ".git").exists():
                errors.append(f"{repo_dir} 不是 Git repo；請先 git init + git lfs install")
            else:
                # 複製 snapshots 過去
                dst = repo_dir / "snapshots"
                if dst.exists(): shutil.rmtree(dst)
                shutil.copytree(SNAP_ROOT, dst)
                # commit + push
                msg = f"snapshot sync {now_iso()}"
                subprocess.run(["git", "-C", str(repo_dir), "add", "snapshots/"])
                subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", msg])
                r = subprocess.run(["git", "-C", str(repo_dir), "push"],
                                    capture_output=True, text=True)
                if r.returncode != 0:
                    errors.append(r.stderr)
                else:
                    pushed = len(local_items)

    else:
        errors.append(f"未知 backend: {backend}")

    result = {"backend": backend, "remote": remote,
              "pushed": pushed, "skipped": skipped, "errors": errors}
    log_audit("snapshot_sync_push", result)
    return result


def pull_from_remote(cfg: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    backend = cfg["backend"]
    remote  = cfg["remote"]
    SNAP_ROOT.mkdir(parents=True, exist_ok=True)
    local_ids = {d.name for d in SNAP_ROOT.iterdir() if d.is_dir()}
    pulled = 0; skipped = 0; errors = []

    if backend in ("filesystem", "onedrive"):
        remote_path = Path(remote)
        if not remote_path.exists():
            return {"pulled": 0, "error": f"遠端不存在: {remote}"}
        for d in remote_path.iterdir():
            if not d.is_dir(): continue
            if not (d / "INVENTORY.json").exists(): continue
            if d.name in local_ids:
                skipped += 1; continue
            print(f"  ← pull: {d.name}")
            if not dry_run:
                shutil.copytree(d, SNAP_ROOT / d.name)
            pulled += 1

    elif backend == "robocopy":
        cmd_base = ["robocopy", str(remote), str(SNAP_ROOT), "/E", "/XO",
                    "/R:2", "/W:5"]
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            if r.returncode > 7: errors.append(r.stderr or r.stdout)

    elif backend == "rsync":
        cmd_base = ["rsync", "-a", "--ignore-existing", f"{remote}/", str(SNAP_ROOT) + "/"]
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            if r.returncode != 0: errors.append(r.stderr)

    elif backend == "s3":
        cmd_base = ["aws", "s3", "sync", remote, str(SNAP_ROOT)]
        if not dry_run:
            r = subprocess.run(cmd_base, capture_output=True, text=True)
            if r.returncode != 0: errors.append(r.stderr)

    elif backend == "git":
        repo_dir = Path(remote)
        if not dry_run:
            subprocess.run(["git", "-C", str(repo_dir), "pull"])
            src = repo_dir / "snapshots"
            if src.exists():
                for d in src.iterdir():
                    if d.is_dir() and d.name not in local_ids:
                        shutil.copytree(d, SNAP_ROOT / d.name)
                        pulled += 1

    result = {"backend": backend, "remote": remote,
              "pulled": pulled, "skipped": skipped, "errors": errors}
    log_audit("snapshot_sync_pull", result)
    return result


def cmd_sync(args):
    """O: 推到遠端"""
    banner("SYNC PUSH")
    cfg = load_sync_config()
    if not cfg:
        # 互動式設定
        print("  尚未設定同步目標。")
        print("\n  可用後端:")
        for k, desc in SYNC_BACKENDS.items():
            print(f"    {k:12s} — {desc}")
        backend = input("\n  選擇 backend: ").strip().lower()
        if backend not in SYNC_BACKENDS:
            print("  ✗ 未知 backend"); sys.exit(1)
        remote = input(f"  遠端位置 (路徑/URL/repo): ").strip()
        if not remote: sys.exit(1)
        auto_push = input("  Auto-push after every snapshot? [y/N]: ").strip().lower() == "y"
        cfg = {"backend": backend, "remote": remote, "auto_push": auto_push,
               "created_at": now_iso()}
        save_sync_config(cfg)
        print(f"  ✓ 已保存到 {SYNC_CONFIG.name}")

    r = push_to_remote(cfg, dry_run=not args.execute)
    print(f"\n  Pushed: {r['pushed']}  Skipped: {r['skipped']}")
    if r["errors"]:
        print(f"  Errors:")
        for e in r["errors"]: print(f"    - {e}")
    if not args.execute and cfg["backend"] in ("filesystem", "onedrive"):
        print(f"\n  ⚠ DRY-RUN. 加 --execute 真的推送")


def cmd_pull(args):
    """O: 從遠端拉回"""
    banner("SYNC PULL")
    cfg = load_sync_config()
    if not cfg:
        print("  ✗ 尚未設定同步目標。請先 via via-snap-sync"); sys.exit(1)
    r = pull_from_remote(cfg, dry_run=not args.execute)
    print(f"\n  Pulled: {r['pulled']}  Skipped: {r.get('skipped',0)}")
    if r.get("errors"):
        for e in r["errors"]: print(f"  Error: {e}")


# ============================================================
# Hook 設定
# ============================================================
def load_hooks() -> Dict[str, Any]:
    if HOOK_CONFIG.exists():
        return json.loads(HOOK_CONFIG.read_text(encoding="utf-8"))
    return {"enabled": [], "auto_retention": True}

def save_hooks(d: Dict[str, Any]):
    HOOK_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    HOOK_CONFIG.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                            encoding="utf-8")

def cmd_hook(args):
    """設定自動觸發點"""
    banner("HOOK CONFIGURATION")
    hooks = load_hooks()

    if args.list or (not args.enable and not args.disable):
        print("  Available hooks:")
        for k, desc in HOOK_TRIGGERS.items():
            mark = "✓" if k in hooks["enabled"] else " "
            print(f"    [{mark}] {k:22s} — {desc}")
        print(f"\n  Auto retention: {hooks.get('auto_retention', True)}")
        print(f"\n  用法:")
        print(f"    --enable post-activate,daily")
        print(f"    --disable post-activate")
        return

    if args.enable:
        for h in args.enable.split(","):
            h = h.strip()
            if h not in HOOK_TRIGGERS:
                print(f"  ✗ 未知 hook: {h}"); continue
            if h not in hooks["enabled"]:
                hooks["enabled"].append(h)
                print(f"  ✓ enabled: {h}")
    if args.disable:
        for h in args.disable.split(","):
            h = h.strip()
            if h in hooks["enabled"]:
                hooks["enabled"].remove(h)
                print(f"  ⊘ disabled: {h}")
    save_hooks(hooks)
    print(f"\n  ✓ 已保存到 {HOOK_CONFIG.name}")


# ============================================================
# Status
# ============================================================
def cmd_status(args):
    banner("VIA SNAPSHOT STATUS")
    items = list_snapshots_local()
    print(f"  Base    : {VIA_ROOT}")
    print(f"  Snapshots: {len(items)}")
    if items:
        total_size = sum(sum(f.stat().st_size for f in i["path"].rglob("*") if f.is_file())
                          for i in items)
        archived = sum(1 for i in items if i["archived"])
        print(f"    Total size : {total_size/1024/1024:.1f} MB")
        print(f"    Archived   : {archived}/{len(items)}")
        print(f"    Latest     : {items[-1]['snap_id']}")

    print(f"\n  Retention policy:")
    policy = load_retention()
    for k, v in policy.items():
        print(f"    {k:22s} = {v}")

    print(f"\n  Hooks enabled:")
    hooks = load_hooks()
    if hooks["enabled"]:
        for h in hooks["enabled"]: print(f"    ✓ {h}")
    else:
        print(f"    (none)")

    print(f"\n  Sync target:")
    cfg = load_sync_config()
    if cfg:
        print(f"    backend  : {cfg['backend']}")
        print(f"    remote   : {cfg['remote']}")
        print(f"    auto_push: {cfg.get('auto_push', False)}")
    else:
        print(f"    (not configured; run: via via-snap-sync to set up)")

    print(f"\n  CMD-IDs registered: {len([c for c in SNAPSHOT_COMMANDS])}")


# ============================================================
# Console (開啟 HTML 儀表板)
# ============================================================
def cmd_console(args):
    html = VIA_ROOT / "tools" / "VIA_Snapshot_Console.html"
    if not html.exists():
        print(f"  ✗ 找不到 {html}")
        print(f"    請先安裝 VIA_Snapshot_Console.html")
        sys.exit(1)
    # 先 dump 一份 inventory JSON 給 HTML 讀
    data_file = VIA_ROOT / "tools" / "snapshot_console_data.json"
    items = list_snapshots_local()
    payload = {"generated_at": now_iso(),
               "base": str(VIA_ROOT),
               "snapshots": []}
    for it in items:
        try:
            inv = json.loads((it["path"] / "INVENTORY.json").read_text(encoding="utf-8"))
            payload["snapshots"].append({
                "snap_id": it["snap_id"],
                "version": it["version"],
                "ts": it["ts"],
                "scanned_at": it["scanned_at"],
                "archived": it["archived"],
                "note": it["note"],
                "file_count": inv["L1_physical"]["file_count"],
                "total_bytes": inv["L1_physical"]["total_bytes"],
                "merkle_root": inv["L1_physical"]["merkle_root"],
                "subsystem_count": inv["L2_logical"]["subsystem_count"],
                "subsystems": [s["code"] for s in inv["L2_logical"]["subsystems"]],
                "command_count": inv["L2_logical"]["command_count_registered"],
                "license_count": inv["L4_runtime"]["license_count"],
                "feature_mask_hex": inv["L2_logical"].get("feature_mask_hex"),
            })
        except Exception as e:
            print(f"  ⚠ {it['snap_id']}: {e}")

    data_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"  ✓ 資料已輸出到 {data_file.name}")
    print(f"  ✓ 開啟: {html}")

    # 跨平台開檔
    if sys.platform == "win32":
        os.startfile(str(html))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(html)])
    else:
        subprocess.run(["xdg-open", str(html)])


# ============================================================
# CLI
# ============================================================
def main():
    ap = argparse.ArgumentParser(prog="via_snapshot_integration",
        description="VIA Snapshot Integration — L+N+O")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("install", help="L: 註冊 snapshot 指令到 via 主路由")

    s = sub.add_parser("auto", help="N: 自動快照 (給 hook 用)")
    s.add_argument("--trigger", help="觸發來源 (post-activate/daily/...)")
    s.add_argument("--archive", action="store_true")
    s.add_argument("--include-auth", action="store_true")
    s.add_argument("--note")

    s = sub.add_parser("retention", help="N: 套用保留策略")
    s.add_argument("--execute", action="store_true")

    s = sub.add_parser("sync", help="O: 推快照到遠端")
    s.add_argument("--execute", action="store_true")

    s = sub.add_parser("pull", help="O: 從遠端拉回快照")
    s.add_argument("--execute", action="store_true")

    s = sub.add_parser("hook", help="設定自動觸發點")
    s.add_argument("--list", action="store_true")
    s.add_argument("--enable", help="逗號分隔")
    s.add_argument("--disable", help="逗號分隔")

    sub.add_parser("status", help="顯示快照與同步狀態")
    sub.add_parser("console", help="開啟 HTML 儀表板")

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help(); return

    fn = {"install": cmd_install, "auto": cmd_auto, "retention": cmd_retention,
          "sync": cmd_sync, "pull": cmd_pull, "hook": cmd_hook,
          "status": cmd_status, "console": cmd_console}[args.cmd]
    fn(args)


if __name__ == "__main__":
    main()
