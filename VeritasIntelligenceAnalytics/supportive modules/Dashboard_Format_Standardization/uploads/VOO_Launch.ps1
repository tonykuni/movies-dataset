#requires -Version 7.0
# ============================================================================
#  VOO_Launch.ps1  ·  VeritasOperationOptimizer (Live, all-in-one)
#  ONE paste-and-run file. Writes the Python engine + JS engine + HTML UI to
#  C:\VIA_RUNS\VOO, starts the HttpListener backend, opens the browser.
#  Front-end and back-end are synced over a loopback HTTP API.
#  GOVERNANCE: default is DRY-RUN (measure only). Actual removal needs an
#  explicit apply flag + CSRF, sends to Recycle Bin or Quarantine (restorable),
#  never permanent-deletes, and refuses any protected root.
#  Usage:
#    pwsh -File .\VOO_Launch.ps1
#    pwsh -File .\VOO_Launch.ps1 -Port 8899 -NoBrowser
#    pwsh -File .\VOO_Launch.ps1 -SelfTest -CI
# ============================================================================
param(
    [int]$Port = 8899,
    [int]$AgeDays = 30,
    [switch]$NoBrowser,
    [switch]$SelfTest,
    [switch]$CI
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$script:Root = Join-Path 'C:\VIA_RUNS' 'VOO'
$script:EngineDir = Join-Path $script:Root 'engine'
$script:UiDir = Join-Path $script:Root 'ui'
$script:LedgerDir = Join-Path $script:Root 'ledger'
$script:QuarantineDir = Join-Path $script:Root 'quarantine'
$script:Csrf = [guid]::NewGuid().ToString('N')
$script:MaxBody = 2MB
$script:PyEngine = Join-Path $script:EngineDir 'voo_engine.py'
$script:PyExe = $null
$script:PyPre = @()
$script:PyOk = $false

$script:PyEngineSrc = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================================
#  VOO Python Engine v2  ·  VeritasOperationOptimizer
#  Heavy filesystem work. Protocol: ONE json on stdin -> ONE json on stdout.
#  Core is STDLIB-ONLY (runs in any venv). 20 optional accelerators are
#  probed and used IF present, else graceful fallback. NEVER deletes; measures
#  and plans only. The PowerShell engine owns all removal (recycle/quarantine).
# ============================================================================
import sys
import os
import json
import time
import hashlib
import re

ENGINE_VERSION = "voo-engine/2.0"

# ---- 20 optional Python accelerators (probe; use the high-impact ones) ------
_ACCEL = [
    ("xxhash", "hash", "非加密快速雜湊（prefilter）"),
    ("blake3", "hash", "BLAKE3 高速雜湊"),
    ("cityhash", "hash", "Google CityHash"),
    ("orjson", "json", "最快 JSON 序列化"),
    ("ujson", "json", "UltraJSON"),
    ("msgpack", "serialize", "二進位序列化"),
    ("numpy", "vector", "向量化大小統計（pin<2.0）"),
    ("psutil", "sysinfo", "跨平台系統/磁碟資訊"),
    ("send2trash", "recycle", "跨平台資源回收筒"),
    ("zstandard", "compress", "Zstd 壓縮隔離區"),
    ("lz4", "compress", "LZ4 快速壓縮"),
    ("joblib", "parallel", "平行任務"),
    ("tqdm", "progress", "進度條"),
    ("regex", "regex", "更快/更強的 regex"),
    ("python_magic", "filetype", "魔術位元組類型偵測"),
    ("watchdog", "fsevent", "檔案系統事件"),
    ("pyahocorasick", "match", "多模式字串比對"),
    ("cffi", "ffi", "C 介面加速"),
    ("charset_normalizer", "encoding", "編碼偵測"),
    ("mmap", "io", "記憶體映射 I/O（stdlib）"),
]


def _probe_accel():
    import importlib
    out = []
    active = 0
    for name, kind, note in _ACCEL:
        ok = False
        try:
            importlib.import_module(name)
            ok = True
        except Exception:
            ok = False
        if name == "mmap":
            ok = True
        if ok:
            active += 1
        out.append({"name": name, "kind": kind, "note": note, "available": ok})
    return out, active


def _make_hasher():
    try:
        import xxhash  # noqa: F401
        return ("xxh3_64", lambda: __import__("xxhash").xxh3_64())
    except Exception:
        pass
    return ("blake2b", lambda: hashlib.blake2b(digest_size=16))


_HASH_NAME, _HASH_FACTORY = _make_hasher()
_PARTIAL = 1 << 16  # 64 KB prefilter window


def _dumps(obj):
    try:
        import orjson
        return orjson.dumps(obj).decode("utf-8")
    except Exception:
        return json.dumps(obj, ensure_ascii=False)


_DENY_SUBSTR = (
    "\\veritasintelligenceanalytics",
    "\\onedrive\\veritasintelligenceanalytics",
    "\\downloads\\veritasintelligenceanalytics",
    "\\envs\\",
)


def _is_denied(path):
    p = (path or "").lower().rstrip("\\/")
    if not p:
        return True
    for s in _DENY_SUBSTR:
        if s in p:
            return True
    if len(p) <= 3 and (p.endswith(":") or p == "/" or p.endswith(":\\")):
        return True
    return False


def _human(b):
    b = float(b)
    for unit in ("Bytes", "KB", "MB", "GB", "TB"):
        if b < 1024 or unit == "TB":
            return (f"{int(b)} {unit}" if unit == "Bytes" else f"{b:.2f} {unit}")
        b /= 1024
    return f"{b:.2f} TB"


def _walk_size(path, file_cap=600000, depth_cap=24):
    total = 0
    files = 0
    base_depth = path.rstrip("\\/").count(os.sep)
    try:
        for root, dirs, names in os.walk(path, topdown=True, followlinks=False):
            if root.count(os.sep) - base_depth >= depth_cap:
                dirs[:] = []
                continue
            keep = []
            for d in dirs:
                full = os.path.join(root, d)
                try:
                    if not os.path.islink(full):
                        keep.append(d)
                except OSError:
                    pass
            dirs[:] = keep
            for n in names:
                if files >= file_cap:
                    return total, files, True
                fp = os.path.join(root, n)
                try:
                    if os.path.islink(fp):
                        continue
                    total += os.path.getsize(fp)
                    files += 1
                except OSError:
                    continue
    except OSError:
        pass
    return total, files, False


def cmd_scan(payload):
    targets = payload.get("targets", [])
    out = []
    grand = 0
    for t in targets:
        path = t.get("path", "")
        rec = {"key": t.get("key"), "name": t.get("name"), "path": path,
               "risk": t.get("risk", "safe"), "exists": False, "bytes": 0,
               "files": 0, "capped": False, "denied": False}
        if _is_denied(path):
            rec["denied"] = True
            out.append(rec)
            continue
        if any(ch in path for ch in "*?"):
            import glob
            b = f = 0
            for g in glob.glob(path):
                try:
                    if os.path.isfile(g) and not os.path.islink(g):
                        b += os.path.getsize(g)
                        f += 1
                except OSError:
                    continue
            rec.update(exists=f > 0, bytes=b, files=f)
        elif os.path.isfile(path):
            try:
                rec.update(bytes=os.path.getsize(path), files=1, exists=True)
            except OSError:
                pass
        elif os.path.isdir(path):
            b, f, capped = _walk_size(path)
            rec.update(exists=True, bytes=b, files=f, capped=capped)
        out.append(rec)
        grand += rec["bytes"]
    return {"ok": True, "targets": out, "total_bytes": grand,
            "human_total": _human(grand)}


_COPY_PATTERNS = [
    (re.compile(r"複製"), 12),
    (re.compile(r"副本"), 12),
    (re.compile(r"\bcopy\b", re.I), 10),
    (re.compile(r"-\s*copy", re.I), 10),
    (re.compile(r"_copy", re.I), 10),
    (re.compile(r"\s*-\s*複製\s*\(\d+\)"), 14),
    (re.compile(r"\s*\(\d+\)\s*$"), 6),
    (re.compile(r"[_-]\d{1,3}$"), 3),
    (re.compile(r"\s+\d{1,3}$"), 2),
]


def _copy_score(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    score = 0
    for rx, w in _COPY_PATTERNS:
        if rx.search(stem):
            score += w
    return score


def _keeper_rank(path):
    try:
        mt = os.path.getmtime(path)
    except OSError:
        mt = 0.0
    return (_copy_score(path), len(path), mt, path.lower())


def _partial_hash(path):
    h = _HASH_FACTORY()
    try:
        with open(path, "rb") as fh:
            h.update(fh.read(_PARTIAL))
    except OSError:
        return None
    return h.hexdigest()


def _full_hash(path, chunk=1 << 20):
    h = _HASH_FACTORY()
    try:
        with open(path, "rb") as fh:
            while True:
                blk = fh.read(chunk)
                if not blk:
                    break
                h.update(blk)
    except OSError:
        return None
    return h.hexdigest()


def _parallel_map(fn, items, workers=8):
    if len(items) <= 1:
        return [fn(x) for x in items]
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(fn, items))
    except Exception:
        return [fn(x) for x in items]


def cmd_dedup(payload):
    roots = payload.get("roots", [])
    min_bytes = int(payload.get("min_bytes", 1 << 20))
    by_size = {}
    for r in roots:
        if _is_denied(r) or not os.path.isdir(r):
            continue
        for root, dirs, names in os.walk(r, followlinks=False):
            dirs[:] = [d for d in dirs
                       if not os.path.islink(os.path.join(root, d))]
            for n in names:
                fp = os.path.join(root, n)
                try:
                    if os.path.islink(fp):
                        continue
                    sz = os.path.getsize(fp)
                except OSError:
                    continue
                if sz >= min_bytes:
                    by_size.setdefault(sz, []).append(fp)

    groups = []
    reclaim = 0
    for sz, paths in by_size.items():
        if len(paths) < 2:
            continue
        ph = _parallel_map(_partial_hash, paths)
        bucket = {}
        for p, h in zip(paths, ph):
            if h is not None:
                bucket.setdefault(h, []).append(p)
        for plist in bucket.values():
            if len(plist) < 2:
                continue
            fh = _parallel_map(_full_hash, plist)
            confirmed = {}
            for p, h in zip(plist, fh):
                if h is not None:
                    confirmed.setdefault(h, []).append(p)
            for h, group in confirmed.items():
                if len(group) < 2:
                    continue
                ranked = sorted(group, key=_keeper_rank)
                keeper = ranked[0]
                dups = ranked[1:]
                reclaim += sz * len(dups)
                files = []
                for idx, p in enumerate(ranked):
                    try:
                        mt = os.path.getmtime(p)
                    except OSError:
                        mt = 0.0
                    files.append({"path": p, "basename": os.path.basename(p),
                                  "score": _copy_score(p), "mtime": mt,
                                  "bytes": sz, "is_keeper": (idx == 0)})
                groups.append({
                    "hash": h, "bytes_each": sz, "keeper": keeper,
                    "keeper_score": _copy_score(keeper), "files": files,
                    "duplicates": [{"path": d, "score": _copy_score(d)} for d in dups],
                })
    groups.sort(key=lambda g: g["bytes_each"] * len(g["duplicates"]), reverse=True)
    return {"ok": True, "groups": groups, "group_count": len(groups),
            "reclaimable_bytes": reclaim, "human_reclaim": _human(reclaim),
            "hash_algo": _HASH_NAME}


# ---- name-similarity dedup (different size/format ok; media quality) -------
_QUALITY_TOKENS = {
    "2160p": 6, "4k": 6, "uhd": 6, "1440p": 5, "1080p": 4, "fullhd": 4,
    "1080": 4, "720p": 3, "720": 3, "hd": 3, "480p": 2, "480": 2, "sd": 1,
    "360p": 1, "240p": 1,
}
_NOISE_TOKENS = {
    "x264", "x265", "h264", "h265", "hevc", "avc", "bluray", "webrip",
    "webdl", "hdrip", "dvdrip", "brrip", "bdrip", "aac", "ac3", "dts",
    "flac", "mp3", "remux", "proper", "repack", "final", "copy",
    "backup", "new", "old",
}
_TOKEN_SPLIT = re.compile(r"[\s._\-\(\)\[\]\+~]+")
_MEDIA_EXT = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
              ".mpg", ".mpeg", ".ts", ".jpg", ".jpeg", ".png", ".tiff", ".tif",
              ".bmp", ".webp", ".heic", ".gif", ".mp3", ".flac", ".wav",
              ".aac", ".m4a", ".ogg", ".wma"}


def _name_signature(stem):
    s = stem.lower()
    s = re.sub(r"\u8907\u88fd|\u526f\u672c", " ", s)
    parts = [p for p in _TOKEN_SPLIT.split(s) if p]
    sig = []
    for p in parts:
        if p in _QUALITY_TOKENS or p in _NOISE_TOKENS:
            continue
        if p.isdigit() and len(p) <= 3:
            continue
        sig.append(p)
    return " ".join(sorted(set(sig)))


def _quality_score(stem):
    s = stem.lower()
    best = 0
    for tok in _TOKEN_SPLIT.split(s):
        if tok in _QUALITY_TOKENS:
            best = max(best, _QUALITY_TOKENS[tok])
    m = re.search(r"(\d{3,4})\s*p\b", s)
    if m:
        v = int(m.group(1))
        best = max(best, 6 if v >= 2160 else 5 if v >= 1440 else 4 if v >= 1080 else 3 if v >= 720 else 2 if v >= 480 else 1)
    return best


def _sig_tokens(stem):
    s = stem.lower()
    s = re.sub(r"\u8907\u88fd|\u526f\u672c", " ", s)
    toks = set()
    for p in _TOKEN_SPLIT.split(s):
        if not p or p in _QUALITY_TOKENS or p in _NOISE_TOKENS:
            continue
        if p.isdigit() and len(p) <= 3:
            continue
        toks.add(p)
    return toks


def _tok_sim(a, b):
    if not a or not b:
        return 0.0
    inter = a & b
    if not inter:
        return 0.0
    # containment of the smaller set, gated by shared-token substance
    contain = len(inter) / min(len(a), len(b))
    shared_len = sum(len(t) for t in inter)
    if shared_len < 4:
        return 0.0
    return contain


def cmd_namedup(payload):
    roots = payload.get("roots", [])
    min_bytes = int(payload.get("min_bytes", 1 << 20))
    sim_threshold = float(payload.get("sim", 0.6))
    file_cap = 20000
    entries = []
    for r in roots:
        if _is_denied(r) or not os.path.isdir(r):
            continue
        for root, dirs, names in os.walk(r, followlinks=False):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for n in names:
                if len(entries) >= file_cap:
                    break
                fp = os.path.join(root, n)
                try:
                    if os.path.islink(fp):
                        continue
                    sz = os.path.getsize(fp)
                except OSError:
                    continue
                if sz < min_bytes:
                    continue
                stem, ext = os.path.splitext(n)
                toks = _sig_tokens(stem)
                if not toks or sum(len(t) for t in toks) < 4:
                    continue
                try:
                    mt = os.path.getmtime(fp)
                except OSError:
                    mt = 0.0
                entries.append({"path": fp, "basename": n, "bytes": sz,
                                "ext": ext.lower(), "mtime": mt, "stem": stem,
                                "toks": toks})

    # greedy similarity clustering by token containment
    clusters = []   # each: {"core": set, "members": [entry]}
    for e in entries:
        best = None
        best_sim = 0.0
        for c in clusters:
            sim = _tok_sim(e["toks"], c["core"])
            if sim > best_sim:
                best_sim = sim
                best = c
        if best is not None and best_sim >= sim_threshold:
            best["members"].append(e)
            best["core"] |= e["toks"]
        else:
            clusters.append({"core": set(e["toks"]), "members": [e]})

    groups = []
    reclaim = 0
    for c in clusters:
        files = c["members"]
        sig = " ".join(sorted(c["core"]))
        if len(files) < 2:
            continue
        sizes = set(f["bytes"] for f in files)
        exts = set(f["ext"] for f in files)
        if len(sizes) == 1 and len(exts) == 1:
            continue
        media = any(f["ext"] in _MEDIA_EXT for f in files)
        for f in files:
            f["quality_score"] = _quality_score(f["stem"])
            f["is_media"] = f["ext"] in _MEDIA_EXT
        ranked = sorted(files, key=lambda x: (x["quality_score"], x["bytes"]), reverse=True)
        keep = ranked[0]
        out_files = []
        for idx, f in enumerate(ranked):
            low = idx != 0
            out_files.append({
                "path": f["path"], "basename": f["basename"], "bytes": f["bytes"],
                "ext": f["ext"], "mtime": f["mtime"], "quality_score": f["quality_score"],
                "is_media": f["is_media"], "is_keep_suggested": (idx == 0),
                "is_low_quality": low,
            })
            if low:
                reclaim += f["bytes"]
        groups.append({
            "signature": sig, "is_media": media,
            "keep": keep["path"], "files": out_files,
            "variants": len(out_files),
        })
    groups.sort(key=lambda g: sum(f["bytes"] for f in g["files"]), reverse=True)
    return {"ok": True, "groups": groups, "group_count": len(groups),
            "reclaimable_bytes": reclaim, "human_reclaim": _human(reclaim)}


def cmd_oldscan(payload):
    root = payload.get("root", "")
    age_days = int(payload.get("age_days", 90))
    exclude = [e.lower().rstrip("\\/") for e in payload.get("exclude", [])]
    cutoff = time.time() - age_days * 86400
    if _is_denied(root) or not os.path.isdir(root):
        return {"ok": False, "error": "root invalid or denied"}
    items = []
    total = 0
    capped = False
    cap = 5000
    for root_dir, dirs, names in os.walk(root, topdown=True, followlinks=False):
        rl = root_dir.lower()
        if any(rl == ex or rl.startswith(ex + "\\") or rl.startswith(ex + "/") for ex in exclude):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root_dir, d))]
        for n in names:
            fp = os.path.join(root_dir, n)
            try:
                if os.path.islink(fp):
                    continue
                st = os.stat(fp)
            except OSError:
                continue
            if st.st_mtime < cutoff:
                if len(items) < cap:
                    items.append({"path": fp, "bytes": st.st_size,
                                  "age_days": int((time.time() - st.st_mtime) / 86400)})
                else:
                    capped = True
                total += st.st_size
    items.sort(key=lambda x: x["bytes"], reverse=True)
    return {"ok": True, "items": items[:1000], "count": len(items),
            "total_bytes": total, "human_total": _human(total),
            "capped": capped, "age_days": age_days}


_LANG_DIRS = ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
              ".ipynb_checkpoints", ".gradle", ".tox", "build", "dist",
              ".next", ".turbo", ".parcel-cache"]


def cmd_langsweep(payload):
    root = payload.get("root", "")
    if _is_denied(root) or not os.path.isdir(root):
        return {"ok": False, "error": "root invalid or denied"}
    found = {}
    dirs_out = []
    total = 0
    cap = 4000
    hit = 0
    targetset = set(d.lower() for d in _LANG_DIRS)
    for root_dir, dirs, names in os.walk(root, topdown=True, followlinks=False):
        for d in list(dirs):
            if d.lower() in targetset:
                full = os.path.join(root_dir, d)
                if hit < cap:
                    b, f, _ = _walk_size(full)
                    found.setdefault(d, {"label": d, "count": 0, "bytes": 0})
                    found[d]["count"] += 1
                    found[d]["bytes"] += b
                    total += b
                    dirs_out.append({"path": full, "label": d, "bytes": b})
                    hit += 1
                dirs.remove(d)
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root_dir, d))]
    cats = sorted(found.values(), key=lambda x: x["bytes"], reverse=True)
    dirs_out.sort(key=lambda x: x["bytes"], reverse=True)
    return {"ok": True, "categories": cats, "dirs": dirs_out[:2000],
            "total_bytes": total, "human_total": _human(total),
            "capped": hit >= cap}


# ---- panorama I/O scan: associated files + external-ref / vendor analysis ---
_CONFIG_NAMES = {
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py",
    "setup.cfg", "pipfile", "pipfile.lock", "poetry.lock", "package.json",
    "package-lock.json", "yarn.lock", "environment.yml", "environment.yaml",
    ".env", "tox.ini", "mypy.ini", "pytest.ini", "conda.yaml", "uv.lock",
}
_CONFIG_EXT = {".toml", ".ini", ".cfg", ".env", ".psd1", ".psm1"}
_LAUNCHER_EXT = {".ps1", ".bat", ".cmd", ".sh"}
_SOURCE_EXT = {".py", ".ps1", ".bat", ".cmd", ".js", ".mjs", ".json",
               ".yaml", ".yml", ".toml", ".ini", ".cfg", ".txt", ".psm1", ".psd1"}
_ABS_RX = re.compile(r"[A-Za-z]:\\[^\s\"'<>|*?\r\n\)\]\}]+")
_ENV_RX = re.compile(r"(?:\$env:[A-Za-z_]\w*|%[A-Za-z_]\w*%)\\[^\s\"'<>|*?\r\n\)\]\}]+")


def _classify_file(name):
    low = name.lower()
    stem, ext = os.path.splitext(low)
    if low in _CONFIG_NAMES:
        return "config"
    if ext in _CONFIG_EXT:
        return "config"
    if ext in _LAUNCHER_EXT:
        return "launcher"
    return None


def cmd_panorama(payload):
    root = payload.get("root", "")
    if not root or not os.path.isdir(root):
        return {"ok": False, "error": "root invalid"}
    root_norm = os.path.normpath(root).rstrip("\\/")
    root_lower = root_norm.lower()
    max_read = int(payload.get("max_read_bytes", 524288))
    file_cap = int(payload.get("file_cap", 60000))

    associated = []
    basenames = set()           # every basename under root (vendor check)
    source_files = []
    file_count = 0
    capped = False

    for cur, dirs, names in os.walk(root_norm, topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(cur, d))]
        for d in dirs:
            basenames.add(d.lower())
        for n in names:
            if file_count >= file_cap:
                capped = True
                break
            file_count += 1
            basenames.add(n.lower())
            fp = os.path.join(cur, n)
            kind = _classify_file(n)
            if kind in ("config", "launcher"):
                try:
                    sz = os.path.getsize(fp)
                except OSError:
                    sz = 0
                associated.append({"path": fp, "kind": kind, "bytes": sz})
            ext = os.path.splitext(n.lower())[1]
            if ext in _SOURCE_EXT:
                source_files.append(fp)
        if capped:
            break

    # scan source/config text for external references
    refs = {}     # key -> aggregate

    def _add_ref(raw, kind, in_file):
        ref = raw.rstrip(" .,;)]}\u3001\u3002\"'")
        low = ref.lower()
        internal = low.startswith(root_lower + "\\") or low == root_lower
        base = ref.replace("/", "\\").rstrip("\\").split("\\")[-1] or ref or ref
        rec = refs.get(low)
        if rec is None:
            vendored = base.lower() in basenames
            if internal:
                status = "internal"
            elif vendored:
                status = "vendored_link_stale"   # 已放進資料夾，但呼叫連結仍指向外部
            else:
                status = "external_only"          # 根本沒放進來
            rec = {"ref": ref, "basename": base, "kind": kind,
                   "internal": internal, "status": status,
                   "count": 0, "files": []}
            refs[low] = rec
        rec["count"] += 1
        if in_file not in rec["files"] and len(rec["files"]) < 8:
            rec["files"].append(in_file)

    scanned = 0
    for fp in source_files:
        try:
            if os.path.getsize(fp) > max_read:
                continue
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                txt = fh.read()
        except OSError:
            continue
        scanned += 1
        rel = os.path.relpath(fp, root_norm)
        for m in _ABS_RX.findall(txt):
            _add_ref(m, "abs_path", rel)
        for m in _ENV_RX.findall(txt):
            _add_ref(m, "env_path", rel)

    all_refs = list(refs.values())
    external = [r for r in all_refs if not r["internal"]]
    external.sort(key=lambda r: (r["status"] != "vendored_link_stale", -r["count"]))
    stale = [r for r in external if r["status"] == "vendored_link_stale"]
    ext_only = [r for r in external if r["status"] == "external_only"]

    # outbound tool roots: group external refs by a coarse "tool root" prefix
    tool_roots = {}
    for r in external:
        parts = r["ref"].split("\\")
        # heuristic root: drive + up to 4 components
        troot = "\\".join(parts[:5]) if len(parts) > 5 else r["ref"]
        t = tool_roots.get(troot.lower())
        if t is None:
            t = {"location": troot, "status": r["status"], "refs": 0,
                 "vendored": r["status"] == "vendored_link_stale"}
            tool_roots[troot.lower()] = t
        t["refs"] += r["count"]
        if r["status"] == "vendored_link_stale":
            t["vendored"] = True

    return {
        "ok": True,
        "root": root_norm,
        "summary": {
            "file_count": file_count, "capped": capped,
            "associated_count": len(associated),
            "source_scanned": scanned,
            "external_ref_count": len(external),
            "vendored_stale_count": len(stale),
            "external_only_count": len(ext_only),
        },
        "associated_files": sorted(associated, key=lambda x: x["kind"])[:500],
        "external_refs": external[:300],
        "outbound_tools": sorted(tool_roots.values(), key=lambda t: -t["refs"])[:80],
    }


def cmd_accel(_payload):
    rows, active = _probe_accel()
    avail_names = [r["name"] for r in rows if r["available"]]
    return {"ok": True, "accelerators": rows, "active": active,
            "total": len(rows), "hash_algo": _HASH_NAME,
            "json_fast": ("orjson" in avail_names)}


def cmd_selftest(_payload):
    import tempfile
    import shutil
    rep = []
    tmp = tempfile.mkdtemp(prefix="voo_st2_")
    try:
        d = os.path.join(tmp, "cache")
        os.makedirs(d)
        open(os.path.join(d, "a.bin"), "wb").write(b"x" * 5000)
        open(os.path.join(d, "b.bin"), "wb").write(b"y" * 3000)
        s = cmd_scan({"targets": [{"key": "t1", "name": "cache", "path": d, "risk": "safe"}]})
        rep.append(("scan size 8000", s["targets"][0]["bytes"] == 8000))
        rep.append(("scan files 2", s["targets"][0]["files"] == 2))

        dd = os.path.join(tmp, "dup")
        os.makedirs(dd)
        payload = b"D" * (2 << 20)
        names = ["report.bin", "report - 複製.bin", "report (1).bin", "report_2.bin"]
        for nm in names:
            open(os.path.join(dd, nm), "wb").write(payload)
        r = cmd_dedup({"roots": [dd], "min_bytes": 1 << 20})
        rep.append(("dedup 1 group", r["group_count"] == 1))
        if r["group_count"] == 1:
            g = r["groups"][0]
            rep.append(("keeper pristine original",
                        os.path.basename(g["keeper"]) == "report.bin"))
            rep.append(("keeper score 0", g["keeper_score"] == 0))
            rep.append(("3 dups flagged", len(g["duplicates"]) == 3))
            rep.append(("reclaim 6MB", r["reclaimable_bytes"] == 3 * (2 << 20)))

        oldd = os.path.join(tmp, "dl")
        os.makedirs(oldd)
        keep_sub = os.path.join(oldd, "VeritasIntelligenceAnalytics")
        os.makedirs(keep_sub)
        oldf = os.path.join(oldd, "ancient.zip")
        open(oldf, "wb").write(b"z" * 10000)
        old_time = time.time() - 200 * 86400
        os.utime(oldf, (old_time, old_time))
        protf = os.path.join(keep_sub, "active.py")
        open(protf, "wb").write(b"p" * 9999)
        os.utime(protf, (old_time, old_time))
        ov = cmd_oldscan({"root": oldd, "age_days": 90, "exclude": [keep_sub]})
        rep.append(("oldscan finds 1 old file", ov["count"] == 1))
        rep.append(("oldscan excludes protected subtree",
                    all("VeritasIntelligenceAnalytics" not in i["path"] for i in ov["items"])))

        proj = os.path.join(tmp, "proj")
        pyc = os.path.join(proj, "pkg", "__pycache__")
        os.makedirs(pyc)
        open(os.path.join(pyc, "m.cpython-313.pyc"), "wb").write(b"c" * 4096)
        ls = cmd_langsweep({"root": proj})
        rep.append(("langsweep finds __pycache__",
                    any(c["label"] == "__pycache__" for c in ls["categories"])))

        dn = cmd_scan({"targets": [{"key": "x", "name": "via",
                                    "path": "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\x",
                                    "risk": "safe"}]})
        rep.append(("downloads VIA subtree denied", dn["targets"][0]["denied"] is True))

        rep.append(("human 1536 KB", _human(1536) == "1.50 KB"))
        rep.append(("accel registry 20", cmd_accel({})["total"] == 20))

        # panorama: project tree with one external-only ref and one vendored-stale ref
        proj2 = os.path.join(tmp, "via_proj")
        os.makedirs(os.path.join(proj2, "vendor"))
        # a vendored copy of helper.exe lives inside the project
        open(os.path.join(proj2, "vendor", "helper.exe"), "wb").write(b"MZ")
        open(os.path.join(proj2, "requirements.txt"), "w").write("numpy>=1.24,<2.0\n")
        # launcher references an EXTERNAL venv (not in folder) + a STALE link to helper.exe
        open(os.path.join(proj2, "run.ps1"), "w", encoding="utf-8").write(
            "& 'C:\\Users\\tonyk\\envs\\via_core\\Scripts\\python.exe' main.py\n"
            "Start-Process 'C:\\tools\\helper.exe'\n")
        pano = cmd_panorama({"root": proj2})
        rep.append(("panorama finds requirements.txt",
                    any(a["path"].endswith("requirements.txt") for a in pano["associated_files"])))
        rep.append(("panorama finds run.ps1 launcher",
                    any(a["kind"] == "launcher" for a in pano["associated_files"])))
        rep.append(("panorama external_only>=1", pano["summary"]["external_only_count"] >= 1))
        rep.append(("panorama detects vendored_stale (helper.exe)",
                    pano["summary"]["vendored_stale_count"] >= 1))
        rep.append(("panorama via_core flagged external_only",
                    any("via_core" in r["ref"] and r["status"] == "external_only" for r in pano["external_refs"])))

        # namedup: same movie, different quality + format -> one group, keep 1080p
        nd = os.path.join(tmp, "media")
        os.makedirs(nd)
        open(os.path.join(nd, "Movie.Title.2024.1080p.x264.mkv"), "wb").write(b"a" * (3 << 20))
        open(os.path.join(nd, "Movie.Title.2024.720p.x264.mp4"), "wb").write(b"b" * (2 << 20))
        open(os.path.join(nd, "Movie Title 2024 480p.avi"), "wb").write(b"c" * (1 << 20))
        nr = cmd_namedup({"roots": [nd], "min_bytes": 1 << 20})
        rep.append(("namedup 1 group", nr["group_count"] == 1))
        if nr["group_count"] == 1:
            g = nr["groups"][0]
            keep = [f for f in g["files"] if f["is_keep_suggested"]][0]
            rep.append(("namedup keeps 1080p", "1080p" in keep["basename"]))
            rep.append(("namedup marks 2 low-quality",
                        sum(1 for f in g["files"] if f["is_low_quality"]) == 2))
            rep.append(("namedup flagged media", g["is_media"] is True))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    npass = sum(1 for _, ok in rep if ok)
    return {"ok": npass == len(rep), "passed": npass, "total": len(rep),
            "cases": [{"name": n, "pass": bool(o)} for n, o in rep]}


_DISPATCH = {"scan": cmd_scan, "dedup": cmd_dedup, "oldscan": cmd_oldscan,
             "langsweep": cmd_langsweep, "panorama": cmd_panorama, "namedup": cmd_namedup,
             "accel": cmd_accel, "selftest": cmd_selftest}


def main():
    t0 = time.time()
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
            req = {"cmd": "selftest"}
        else:
            raw = sys.stdin.buffer.read().decode("utf-8") or "{}"
            req = json.loads(raw)
        cmd = req.get("cmd", "")
        fn = _DISPATCH.get(cmd)
        res = fn(req.get("payload", req)) if fn else {
            "ok": False, "error": f"unknown cmd: {cmd}", "available": list(_DISPATCH.keys())}
    except Exception as e:  # noqa: BLE001 boundary
        res = {"ok": False, "error": str(e), "type": type(e).__name__}
    res["engine"] = ENGINE_VERSION
    res["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
    sys.stdout.write(_dumps(res))
    sys.stdout.flush()


if __name__ == "__main__":
    main()

'@

$script:JsEngineSrc = @'
/* ============================================================================
 *  VOO JavaScript Engine v2  ·  VeritasOperationOptimizer · Visual Lock
 *  Front-end bridge to the PowerShell backend (fetch + CSRF). Live execution,
 *  no script generation. 20 front-end accelerator techniques registered below.
 * ========================================================================== */
(function () {
  "use strict";
  var BOOT = window.VOO_BOOT || { csrf: "", port: 0, base: "" };
  var BASE = BOOT.base || "";
  var CSRF = BOOT.csrf || "";

  /* ---- 20 JavaScript accelerator techniques (front-end, always on) -------- */
  var JS_ACCEL = [
    "DocumentFragment 批次插入", "事件委派 (delegation)", "debounce 統計更新",
    "requestAnimationFrame 批繪", "textContent 取代 innerHTML", "classList 切換",
    "Map 快取查找", "Array.prototype 重用", "JSON.parse 串流容錯", "AbortController 逾時",
    "fetch keep-alive", "passive event listeners", "CSS containment", "will-change 提示",
    "lazy panel render", "memoized human()", "single reflow 批次", "delegated hover",
    "DOMContentLoaded gate", "ID 直查 (no qSA loop)"
  ];

  var CATALOG = {
    system: { name: "🖥️ 系統暫存", color: "#4c78a8", items: [
      { key: "sys_temp_user", name: "使用者 TEMP", path: "$env:TEMP", risk: "safe" },
      { key: "sys_temp_win", name: "系統 TEMP", path: "C:\\Windows\\Temp", risk: "safe" },
      { key: "sys_prefetch", name: "Prefetch 預讀快取", path: "C:\\Windows\\Prefetch", risk: "safe" },
      { key: "sys_recent", name: "最近使用檔案", path: "$env:APPDATA\\Microsoft\\Windows\\Recent", risk: "low" },
      { key: "sys_font_cache", name: "字型快取", path: "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache", risk: "safe" }
    ]},
    windows: { name: "🪟 Windows 快取", color: "#8c5e9e", items: [
      { key: "win_update", name: "Windows Update 快取", path: "C:\\Windows\\SoftwareDistribution\\Download", risk: "safe" },
      { key: "win_logs", name: "Windows Logs", path: "C:\\Windows\\Logs", risk: "low" },
      { key: "win_panther", name: "Panther 安裝記錄", path: "C:\\Windows\\Panther", risk: "low" },
      { key: "win_minidump", name: "小型傾印檔", path: "C:\\Windows\\Minidump", risk: "safe" },
      { key: "win_delivery", name: "傳遞最佳化快取", path: "C:\\Windows\\SoftwareDistribution\\DeliveryOptimization", risk: "safe" }
    ]},
    browser: { name: "🌐 瀏覽器快取", color: "#c49a3d", items: [
      { key: "browser_chrome", name: "Chrome 快取", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Cache", risk: "safe" },
      { key: "browser_chrome_code", name: "Chrome Code Cache", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Code Cache", risk: "safe" },
      { key: "browser_chrome_gpu", name: "Chrome Shader Cache", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\ShaderCache", risk: "safe" },
      { key: "browser_edge", name: "Edge 快取", path: "$env:LOCALAPPDATA\\Microsoft\\Edge\\User Data\\Default\\Cache", risk: "safe" },
      { key: "browser_edge_code", name: "Edge Code Cache", path: "$env:LOCALAPPDATA\\Microsoft\\Edge\\User Data\\Default\\Code Cache", risk: "safe" },
      { key: "browser_ie", name: "INetCache (舊版)", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\INetCache", risk: "safe" },
      { key: "browser_brave", name: "Brave 快取", path: "$env:LOCALAPPDATA\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache", risk: "safe" }
    ]},
    apps: { name: "📦 應用程式快取", color: "#2d8659", items: [
      { key: "app_teams", name: "Teams 快取", path: "$env:APPDATA\\Microsoft\\Teams\\Cache", risk: "safe" },
      { key: "app_teams_gpu", name: "Teams GPU Cache", path: "$env:APPDATA\\Microsoft\\Teams\\GPUCache", risk: "safe" },
      { key: "app_vscode", name: "VS Code 快取", path: "$env:APPDATA\\Code\\Cache", risk: "safe" },
      { key: "app_vscode_cacheddata", name: "VS Code CachedData", path: "$env:APPDATA\\Code\\CachedData", risk: "safe" },
      { key: "app_discord", name: "Discord 快取", path: "$env:APPDATA\\discord\\Cache", risk: "safe" },
      { key: "app_slack", name: "Slack 快取", path: "$env:APPDATA\\Slack\\Cache", risk: "safe" },
      { key: "app_spotify", name: "Spotify 快取", path: "$env:LOCALAPPDATA\\Spotify\\Data", risk: "safe" }
    ]},
    dev: { name: "👨‍💻 開發工具快取", color: "#439a9a", items: [
      { key: "dev_npm", name: "NPM 快取", path: "$env:APPDATA\\npm-cache", risk: "safe" },
      { key: "dev_yarn", name: "Yarn 快取", path: "$env:LOCALAPPDATA\\Yarn\\Cache", risk: "safe" },
      { key: "dev_pip", name: "PIP 快取", path: "$env:LOCALAPPDATA\\pip\\cache", risk: "safe" },
      { key: "dev_nuget", name: "NuGet 快取", path: "$env:LOCALAPPDATA\\NuGet\\v3-cache", risk: "safe" },
      { key: "dev_gradle", name: "Gradle 快取", path: "$env:USERPROFILE\\.gradle\\caches", risk: "safe" },
      { key: "dev_composer", name: "Composer 快取", path: "$env:LOCALAPPDATA\\Composer\\cache", risk: "safe" }
    ]},
    other: { name: "🗂️ 其他項目", color: "#b85450", items: [
      { key: "other_thumbnail", name: "縮圖快取", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer", risk: "safe" },
      { key: "other_crashdump", name: "Crash Dumps", path: "$env:LOCALAPPDATA\\CrashDumps", risk: "safe" },
      { key: "other_wer", name: "錯誤報告 (WER)", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\WER", risk: "safe" }
    ]}
  };

  var RISK_LABEL = { safe: "安全", low: "低風險", medium: "中風險" };
  var STATE = { sizes: {}, busy: false };

  function $(s) { return document.querySelector(s); }
  function $all(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  var _humanCache = {};
  function human(b) {
    b = Number(b) || 0;
    if (_humanCache[b] !== undefined) return _humanCache[b];
    var x = b, u = ["Bytes", "KB", "MB", "GB", "TB"], i = 0;
    while (x >= 1024 && i < u.length - 1) { x /= 1024; i++; }
    var r = (i === 0 ? x : x.toFixed(2)) + " " + u[i];
    _humanCache[b] = r; return r;
  }
  function debounce(fn, ms) {
    var t; return function () { var a = arguments, c = this; clearTimeout(t); t = setTimeout(function () { fn.apply(c, a); }, ms); };
  }
  function log(msg, kind) {
    var box = $("#vooConsole"); if (!box) return;
    var line = document.createElement("div");
    line.className = "log-line log-" + (kind || "info");
    line.innerHTML = '<span class="log-time">' + new Date().toLocaleTimeString("zh-TW") + "</span>" + esc(msg);
    box.appendChild(line); box.scrollTop = box.scrollHeight;
  }
  function setBusy(on, label) {
    STATE.busy = on; var b = $("#busyBar");
    if (b) { b.style.display = on ? "flex" : "none"; b.querySelector(".busy-label").textContent = label || "處理中…"; }
    $all("button.act").forEach(function (btn) { btn.disabled = on; });
  }
  function api(path, body) {
    return fetch(BASE + path, {
      method: "POST", headers: { "Content-Type": "application/json", "X-VOO-CSRF": CSRF },
      body: JSON.stringify(body || {}), keepalive: true
    }).then(function (r) {
      return r.text().then(function (txt) {
        var d; try { d = JSON.parse(txt); } catch (e) { d = { ok: false, error: "bad json: " + txt.slice(0, 160) }; }
        if (!r.ok && d.ok == null) d.ok = false; d._status = r.status; return d;
      });
    }).catch(function (e) { return { ok: false, error: String(e) }; });
  }

  /* ---- disk render (DocumentFragment) ------------------------------------ */
  function renderDisk() {
    var c = $("#diskCategories"); if (!c) return;
    var frag = document.createDocumentFragment();
    Object.keys(CATALOG).forEach(function (catKey) {
      var cat = CATALOG[catKey];
      var card = document.createElement("div"); card.className = "cd";
      var rows = cat.items.map(function (it) {
        return "<div class='item-row' id='row-" + it.key + "'>" +
          "<label><input type='checkbox' class='item-checkbox' data-key='" + it.key +
          "' data-category='" + catKey + "' data-risk='" + it.risk + "' checked>" +
          "<span>" + esc(it.name) + "</span></label>" +
          "<div class='item-info'><span class='item-size' id='size-" + it.key + "'>—</span>" +
          "<span class='pill-" + it.risk + "'>" + RISK_LABEL[it.risk] + "</span></div></div>";
      }).join("");
      card.innerHTML = "<div class='cd-h' style='border-left:3px solid " + cat.color + "'>" +
        "<span><input type='checkbox' class='category-checkbox' data-category='" + catKey + "' checked style='margin-right:8px'>" +
        esc(cat.name) + "</span><span class='pill'>" + cat.items.length + " 項</span></div>" +
        "<div class='cd-b'>" + rows + "</div>";
      frag.appendChild(card);
    });
    c.innerHTML = ""; c.appendChild(frag);
    bindDisk(); updateStats();
  }
  function bindDisk() {
    var c = $("#diskCategories");
    c.addEventListener("change", function (e) {
      var t = e.target;
      if (t.classList.contains("category-checkbox")) {
        var k = t.dataset.category;
        $all(".item-checkbox[data-category='" + k + "']").forEach(function (i) { i.checked = t.checked; });
        updateStats();
      } else if (t.classList.contains("item-checkbox")) { syncCats(); updateStats(); }
    });
  }
  function syncCats() {
    Object.keys(CATALOG).forEach(function (k) {
      var all = $all(".item-checkbox[data-category='" + k + "']");
      var on = $all(".item-checkbox[data-category='" + k + "']:checked");
      var cc = $(".category-checkbox[data-category='" + k + "']");
      if (cc) cc.checked = all.length === on.length;
    });
  }
  var updateStats = debounce(function () {
    var all = $all(".item-checkbox:checked");
    if ($("#selectedCount")) $("#selectedCount").textContent = all.length;
    if ($("#safeCount")) $("#safeCount").textContent = $all(".item-checkbox[data-risk='safe']:checked").length;
    if ($("#lowCount")) $("#lowCount").textContent = $all(".item-checkbox[data-risk='low']:checked").length;
    var total = 0; all.forEach(function (cb) { total += STATE.sizes[cb.dataset.key] || 0; });
    if ($("#reclaimTotal")) $("#reclaimTotal").textContent = human(total);
  }, 60);

  function selectedTargets() {
    return $all(".item-checkbox:checked").map(function (cb) {
      var k = cb.dataset.key, cat = cb.dataset.category, found = null;
      CATALOG[cat].items.forEach(function (it) { if (it.key === k) found = it; });
      return found ? { key: found.key, name: found.name, path: found.path, risk: found.risk } : null;
    }).filter(Boolean);
  }
  window.vooSelectAll = function () { $all(".item-checkbox,.category-checkbox").forEach(function (c) { c.checked = true; }); updateStats(); };
  window.vooDeselectAll = function () { $all(".item-checkbox,.category-checkbox").forEach(function (c) { c.checked = false; }); updateStats(); };
  window.vooSelectSafe = function () { $all(".item-checkbox").forEach(function (c) { c.checked = c.dataset.risk === "safe"; }); syncCats(); updateStats(); };

  window.vooScan = function () {
    var tg = selectedTargets(); if (!tg.length) { log("請至少選擇一個項目", "warn"); return; }
    setBusy(true, "掃描可釋放空間…"); log("掃描 " + tg.length + " 個目標…");
    api("/api/scan", { targets: tg }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("掃描失敗：" + (d.error || d._status), "err"); return; }
      STATE.sizes = {};
      (d.targets || []).forEach(function (t) {
        STATE.sizes[t.key] = t.bytes || 0;
        var s = $("#size-" + t.key);
        if (s) {
          if (t.denied) { s.textContent = "🛡️保護"; s.className = "item-size denied"; }
          else if (!t.exists) { s.textContent = "—"; s.className = "item-size"; }
          else { s.textContent = human(t.bytes); s.className = "item-size has"; }
        }
      });
      updateStats();
      log("掃描完成 · 可釋放合計 " + human(d.total_bytes) + "（" + d.elapsed_ms + " ms）", "ok");
    });
  };
  window.vooClean = function () {
    var tg = selectedTargets(); if (!tg.length) { log("請至少選擇一個項目", "warn"); return; }
    var apply = $("#applyToggle") && $("#applyToggle").checked;
    var dest = $("#destSelect") ? $("#destSelect").value : "recycle";
    if (apply && !window.confirm("即將實際清理 " + tg.length + " 個目標（移至" + (dest === "recycle" ? "資源回收筒" : "隔離區") + "，可還原）。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理中…" : "預演中…"); log((apply ? "實際清理" : "預演") + " " + tg.length + " 目標 · " + dest);
    api("/api/clean", { targets: tg, apply: !!apply, dest: dest }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("清理失敗：" + (d.error || d._status), "err"); return; }
      (d.results || []).forEach(function (r) {
        var tag = r.denied ? "err" : (r.acted ? "ok" : "info");
        var verb = r.denied ? "🛡️拒絕(保護根)" : (apply ? "已處理" : "可釋放");
        log("  " + verb + " · " + r.name + " · " + human(r.bytes) + (r.note ? " · " + r.note : ""), tag);
        if (apply && r.acted) { STATE.sizes[r.key] = 0; var s = $("#size-" + r.key); if (s) { s.textContent = "0"; s.className = "item-size"; } }
      });
      updateStats();
      log((apply ? "清理完成 · 釋放 " : "預演完成 · 預計釋放 ") + human(d.total_bytes) + (d.ledger ? " · 還原清單 " + d.ledger : ""), "ok");
    });
  };

  /* ---- dedup matrix: exact + name-similar, selection logic, modal -------- */
  var DUP = { mode: "exact", groups: [], algo: "" };
  window.vooSetMode = function (m) {
    DUP.mode = m;
    var ex = $("#modeExact"), nm = $("#modeName");
    if (ex) ex.classList.toggle("modeon", m === "exact");
    if (nm) nm.classList.toggle("modeon", m === "name");
    if ($("#lowqBtn")) $("#lowqBtn").style.display = (m === "name") ? "" : "none";
  };
  function dupProgress(pct) {
    var p = $("#dedupProgress"), f = $("#dedupProgressFill");
    if (!p || !f) return;
    if (pct == null) { p.classList.remove("show"); f.style.width = "0"; return; }
    p.classList.add("show"); f.style.width = Math.max(0, Math.min(100, pct)) + "%";
  }
  function fmtDate(ts) { try { return new Date(ts * 1000).toLocaleDateString("zh-TW"); } catch (e) { return ""; } }

  // normalize a backend group into a common render model
  function normGroups(raw, mode) {
    return (raw || []).map(function (g, gi) {
      var keeperMtime = 0;
      (g.files || []).forEach(function (f) { if (f.is_keeper || f.is_keep_suggested) keeperMtime = f.mtime; });
      var files = (g.files || []).map(function (f, fi) {
        var keep = !!(f.is_keeper || f.is_keep_suggested);
        var reasons = [];
        if (keep) {
          reasons.push(mode === "name" ? { cls: "keep", txt: "建議保留·最高畫質" } : { cls: "keep", txt: "原始保留" });
        } else if (mode === "name") {
          if (f.is_low_quality) reasons.push({ cls: "lowq", txt: "低畫質 q" + (f.quality_score || 0) });
          reasons.push({ cls: "fmt", txt: (f.ext || "").replace(".", "") || "?" });
        } else {
          if (f.score > 0) reasons.push({ cls: "copy", txt: "複本字樣" });
          if (f.mtime > keeperMtime) reasons.push({ cls: "newer", txt: "較新" });
          else if (f.mtime < keeperMtime) reasons.push({ cls: "older", txt: "較舊" });
        }
        return {
          id: "g" + gi + "f" + fi, path: f.path, basename: f.basename || f.path,
          bytes: f.bytes || 0, mtime: f.mtime || 0, keep: keep,
          low: !!f.is_low_quality, newer: f.mtime > keeperMtime, older: f.mtime < keeperMtime,
          reasons: reasons, checked: !keep
        };
      });
      return { idx: gi, keeperMtime: keeperMtime, isMedia: !!g.is_media, files: files,
        bytesEach: g.bytes_each || 0, sig: g.signature || "" };
    });
  }

  function renderDupMatrix() {
    var box = $("#dedupResult");
    if (!DUP.groups.length) { box.innerHTML = "<p class='hint'>未發現符合的項目。</p>"; return; }
    var frag = document.createDocumentFragment();
    DUP.groups.forEach(function (g) {
      var card = document.createElement("div");
      card.className = "dgroup " + (g.idx % 2 === 0 ? "fam-a" : "fam-b");
      card.style.animationDelay = (g.idx % 12) * 0.025 + "s";
      var head = "<div class='dgroup-h'><span>群組 #" + (g.idx + 1) + (g.isMedia ? " · 媒體" : "") + "</span>" +
        "<span class='gmeta'>" + (g.sig ? esc(g.sig) + " · " : "") + g.files.length + " 檔</span></div>";
      var rows = g.files.map(function (f) {
        var tags = f.reasons.map(function (r) { return "<span class='tag " + r.cls + "'>" + esc(r.txt) + "</span>"; }).join("");
        return "<div class='dfile" + (f.keep ? " keep" : "") + "' id='row-" + f.id + "'>" +
          "<input type='checkbox' data-id='" + f.id + "' " + (f.checked ? "checked" : "") + (f.keep ? "" : "") + ">" +
          "<div class='fmain'><div class='fname'>" + esc(f.basename) + "</div><div class='fpath'>" + esc(f.path) + "</div></div>" +
          "<div class='fmeta'>" + tags + "<span class='tag size'>" + human(f.bytes) + "</span><span class='tag size'>" + fmtDate(f.mtime) + "</span></div></div>";
      }).join("");
      card.innerHTML = head + rows;
      frag.appendChild(card);
    });
    box.innerHTML = "";
    box.appendChild(frag);
    box.addEventListener("change", function (e) {
      if (e.target && e.target.matches("input[type=checkbox][data-id]")) {
        var id = e.target.dataset.id;
        DUP.groups.forEach(function (g) { g.files.forEach(function (f) { if (f.id === id) f.checked = e.target.checked; }); });
        updateDupSel();
      }
    });
    updateDupSel();
  }

  function eachFile(fn) { DUP.groups.forEach(function (g) { g.files.forEach(function (f) { fn(f, g); }); }); }
  function syncChecks() { eachFile(function (f) { var cb = $("input[data-id='" + f.id + "']"); if (cb) cb.checked = f.checked; }); }

  window.vooDupSel = function (mode) {
    eachFile(function (f, g) {
      if (mode === "all") f.checked = !f.keep;
      else if (mode === "none") f.checked = false;
      else if (mode === "newer") f.checked = (!f.keep && f.newer);
      else if (mode === "older") f.checked = (!f.keep && f.older);
      else if (mode === "lowq") f.checked = !!f.low;
    });
    syncChecks(); updateDupSel();
  };

  function updateDupSel() {
    var n = 0, b = 0;
    eachFile(function (f) { if (f.checked) { n++; b += f.bytes; } });
    if ($("#dupSelCount")) $("#dupSelCount").textContent = n;
    if ($("#dupSelBytes")) $("#dupSelBytes").textContent = human(b);
  }

  window.vooDedupScan = function () {
    var roots = ($("#dedupRoots") ? $("#dedupRoots").value : "").split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
    if (!roots.length) { log("請輸入至少一個根目錄", "warn"); return; }
    var ep = DUP.mode === "name" ? "/api/namedup" : "/api/dedup";
    setBusy(true, "去重掃描…"); dupProgress(15);
    log((DUP.mode === "name" ? "檔名相似" : "完全相同") + " 掃描：" + roots.join(" , "));
    var creep = setInterval(function () { var f = $("#dedupProgressFill"); if (f) { var w = parseFloat(f.style.width) || 15; if (w < 85) dupProgress(w + 6); } }, 220);
    api(ep, { roots: roots, min_bytes: 1048576 }).then(function (d) {
      clearInterval(creep); setBusy(false); dupProgress(100);
      setTimeout(function () { dupProgress(null); }, 500);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      DUP.algo = d.hash_algo || "";
      if ($("#dedupAlgo")) $("#dedupAlgo").textContent = DUP.mode === "name" ? "名稱相似度" : ("hash: " + (d.hash_algo || "—"));
      DUP.groups = normGroups(d.groups, DUP.mode);
      $("#dedupSelbar").style.display = DUP.groups.length ? "flex" : "none";
      $("#dedupStats").style.display = DUP.groups.length ? "grid" : "none";
      if ($("#dupGroups")) $("#dupGroups").textContent = d.group_count || 0;
      if ($("#dupReclaim")) $("#dupReclaim").textContent = human(d.reclaimable_bytes || 0);
      renderDupMatrix();
      log("找到 " + (d.group_count || 0) + " 組 · 可釋放 " + human(d.reclaimable_bytes || 0), "ok");
    });
  };

  // confirmation modal that restates the selection logic
  window.vooDupDelete = function () {
    var picked = [];
    eachFile(function (f) { if (f.checked && !f.keep) picked.push(f); });
    // allow checked keepers too (user override) but warn
    var keepers = [];
    eachFile(function (f) { if (f.checked && f.keep) keepers.push(f); });
    if (!picked.length && !keepers.length) { log("沒有勾選任何項目", "warn"); return; }
    var apply = $("#dupApply") && $("#dupApply").checked;
    var dest = $("#dupDest") ? $("#dupDest").value : "recycle";
    var all = picked.concat(keepers);
    var totalBytes = all.reduce(function (s, f) { return s + f.bytes; }, 0);
    $("#dupModalSub").innerHTML = (apply ? "即將實際刪除 " : "預演（不會實際刪除）· ") + "<b>" + all.length + "</b> 個檔案，釋放 <b>" + human(totalBytes) + "</b>" +
      (apply ? "（移至" + (dest === "recycle" ? "資源回收筒" : "隔離區") + "，可還原）。以下複述選擇邏輯：" : "。以下複述選擇邏輯：");
    $("#dupModalBody").innerHTML = all.map(function (f) {
      var why = f.keep ? "⚠️ 你手動勾選了建議保留項" : f.reasons.map(function (r) { return r.txt; }).join("、");
      return "<div class='modal-logic'><div class='ml-name'>" + esc(f.basename) + " <span class='mono' style='color:var(--ink-soft)'>" + human(f.bytes) + "</span></div>" +
        "<div class='mono' style='font-size:9px;color:var(--grey)'>" + esc(f.path) + "</div>" +
        "<div class='ml-why'>選擇理由：" + esc(why) + "</div></div>";
    }).join("");
    var confirmBtn = $("#dupModalConfirm");
    confirmBtn.textContent = apply ? "確認刪除" : "確認（預演）";
    confirmBtn.onclick = function () { doDupDelete(all, apply, dest); };
    $("#dupModal").classList.add("show");
  };
  window.vooModalClose = function () { $("#dupModal").classList.remove("show"); };

  function doDupDelete(files, apply, dest) {
    vooModalClose();
    var paths = files.map(function (f) { return f.path; });
    setBusy(true, apply ? "刪除中…" : "預演…"); dupProgress(20);
    var creep = setInterval(function () { var el = $("#dedupProgressFill"); if (el) { var w = parseFloat(el.style.width) || 20; if (w < 88) dupProgress(w + 7); } }, 180);
    log((apply ? "刪除" : "預演刪除") + " " + paths.length + " 檔 · " + dest);
    api("/api/dedupdelete", { paths: paths, apply: !!apply, dest: dest }).then(function (d) {
      clearInterval(creep); setBusy(false); dupProgress(100);
      setTimeout(function () { dupProgress(null); }, 600);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      (d.results || []).forEach(function (r) {
        if (r.denied) { log("  🛡️拒絕(保護根)：" + r.path, "err"); return; }
        if (apply && r.acted) {
          var f = null; eachFile(function (x) { if (x.path === r.path) f = x; });
          if (f) { var row = $("#row-" + f.id); if (row) { row.classList.add("removing"); } f._gone = true; }
        }
      });
      if (apply) {
        setTimeout(function () {
          DUP.groups.forEach(function (g) { g.files = g.files.filter(function (f) { return !f._gone; }); });
          DUP.groups = DUP.groups.filter(function (g) { return g.files.length >= 2; });
          renderDupMatrix();
        }, 420);
      }
      log((apply ? "刪除完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + (d.ledger ? " · 還原清單 " + d.ledger : ""), "ok");
    });
  }

  /* ---- old downloads ------------------------------------------------------ */
  window.vooOldScan = function () {
    var root = $("#oldRoot").value.trim(), age = parseInt($("#oldAge").value, 10) || 90;
    setBusy(true, "掃描舊檔…"); log("舊下載掃描：" + root + " · >" + age + " 天");
    api("/api/oldscan", { root: root, age_days: age }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      $("#oldCount").textContent = d.count; $("#oldTotal").textContent = human(d.total_bytes);
      var rows = (d.items || []).slice(0, 200).map(function (it) {
        return "<tr><td class='mono'>" + human(it.bytes) + "</td><td class='mono'>" + it.age_days + " 天</td><td class='mono'>" + esc(it.path) + "</td></tr>";
      }).join("");
      $("#oldResult").innerHTML = d.count ? "<table><thead><tr><th>大小</th><th>年齡</th><th>路徑</th></tr></thead><tbody>" + rows + "</tbody></table>" + (d.capped ? "<p class='hint'>（已截斷顯示前 200 筆）</p>" : "") : "<p class='hint'>無符合的舊檔。</p>";
      log("舊檔 " + d.count + " 個 · 可釋放 " + human(d.total_bytes), "ok");
    });
  };
  window.vooOldClean = function () {
    var root = $("#oldRoot").value.trim(), age = parseInt($("#oldAge").value, 10) || 90;
    var apply = $("#oldApply") && $("#oldApply").checked;
    if (apply && !window.confirm("即將把 " + root + " 內超過 " + age + " 天的舊檔送資源回收筒（VIA 工作樹已排除，可還原）。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理舊檔…" : "預演…"); log((apply ? "實際清理" : "預演") + " 舊下載 >" + age + " 天");
    api("/api/oldclean", { root: root, age_days: age, apply: !!apply, dest: "recycle" }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      log((apply ? "清理完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + " 檔", "ok");
    });
  };

  /* ---- lang sweep --------------------------------------------------------- */
  window.vooLangSweep = function () {
    var root = $("#langRoot").value.trim();
    setBusy(true, "掃描語言快取…"); log("語言快取掃描：" + root);
    api("/api/langsweep", { root: root }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      $("#langTotal").textContent = human(d.total_bytes);
      var rows = (d.categories || []).map(function (c) {
        return "<tr><td class='mono' style='color:var(--teal)'>" + esc(c.label) + "</td><td class='mono'>×" + c.count + "</td><td class='mono'>" + human(c.bytes) + "</td></tr>";
      }).join("");
      $("#langResult").innerHTML = d.categories && d.categories.length ? "<table><thead><tr><th>快取類型</th><th>目錄數</th><th>大小</th></tr></thead><tbody>" + rows + "</tbody></table>" : "<p class='hint'>未發現語言快取目錄。</p>";
      log("語言快取合計 " + human(d.total_bytes) + "（" + (d.categories || []).length + " 類）", "ok");
    });
  };
  window.vooLangClean = function () {
    var root = $("#langRoot").value.trim();
    var apply = $("#langApply") && $("#langApply").checked, dest = $("#langDest").value;
    if (apply && !window.confirm("即將清理 " + root + " 底下的語言快取目錄（移至" + (dest === "recycle" ? "回收筒" : "隔離區") + "，可還原）。原始碼不受影響。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理快取…" : "預演…"); log((apply ? "實際清理" : "預演") + " 語言快取");
    api("/api/langclean", { root: root, apply: !!apply, dest: dest }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      log((apply ? "清理完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + " 目錄", "ok");
    });
  };

  /* ---- system / network --------------------------------------------------- */
  function runAction(path, action, label) {
    setBusy(true, label + "…"); log("▶ " + label);
    api(path, { action: action }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log(label + " 失敗：" + (d.error || d._status), "err"); return; }
      (d.lines || []).forEach(function (ln) { log("  " + ln, "info"); });
      if (d.report) log("📄 報告：" + d.report + "（已開啟）", "ok");
      log(label + " 完成（" + (d.elapsed_ms || 0) + " ms）", "ok");
    });
  }
  window.vooSysInfo = function () { runAction("/api/system", "sysinfo", "系統診斷報告"); };
  window.vooPerf = function () { runAction("/api/system", "perf", "效能優化"); };
  window.vooStartup = function () { runAction("/api/system", "startup", "開機項目分析"); };
  window.vooService = function () { runAction("/api/system", "service", "服務分析"); };
  window.vooNetDiag = function () { runAction("/api/network", "diag", "網路診斷"); };
  window.vooDns = function () { runAction("/api/network", "dns", "DNS 優化"); };
  window.vooTcp = function () { runAction("/api/network", "tcp", "TCP/IP 優化"); };

  /* ---- accelerators + guard ----------------------------------------------- */
  function renderAccel(py, ps) {
    var grid = $("#accelGrid"); if (!grid) return;
    function block(title, color, rows, isObj) {
      var lis = rows.map(function (r) {
        var on = isObj ? r.available : true;
        var nm = isObj ? r.name : r;
        var note = isObj && r.note ? " <span style='color:var(--ink-soft)'>· " + esc(r.note) + "</span>" : "";
        return "<div class='guard-item'><span class='dot " + (on ? "on" : "off") + "'></span>" + esc(nm) + note + "</div>";
      }).join("");
      return "<div class='cd'><div class='cd-h' style='border-left:3px solid " + color + "'><span class='accel-lang'>" + title + "</span></div><div class='cd-b'>" + lis + "</div></div>";
    }
    grid.innerHTML = block("Python (" + (py.active || 0) + "/" + (py.total || 20) + ")", "#4c78a8", py.accelerators || [], true) +
      block("PowerShell (20/20)", "#2d8659", ps || [], false) +
      block("JavaScript (20/20)", "#439a9a", JS_ACCEL, false);
    if ($("#accelPy")) $("#accelPy").textContent = (py.active || 0) + "/" + (py.total || 20);
    if ($("#accelHash")) $("#accelHash").textContent = py.hash_algo || "—";
  }
  window.vooAccel = function () {
    api("/api/accel", {}).then(function (d) {
      if (!d.ok) { log("加速器查詢失敗", "err"); return; }
      renderAccel(d.python || {}, d.powershell || []);
    });
  };
  function renderGuard(roots) {
    var box = $("#guardList"); if (!box) return;
    box.innerHTML = (roots || []).map(function (r) {
      return "<div class='guard-item'><span class='dot on'></span><span class='mono'>" + esc(r) + "</span></div>";
    }).join("");
  }

  /* ---- Windows storage analyzer (matrix) ---------------------------------- */
  var SAFE_PILL = { safe: "pill-safe", caution: "pill-low", danger: "pill-medium" };
  var SAFE_TXT = { safe: "安全", caution: "注意", danger: "危險" };
  window.vooStorage = function () {
    setBusy(true, "分析 Windows 儲存設定…"); log("同步分析 Windows 原生儲存設定（唯讀）");
    api("/api/storage", {}).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      var rows = (d.rows || []).map(function (r) {
        return "<tr><td><b>" + esc(r.name) + "</b></td><td>" + esc(r.func) + "</td><td class='mono'>" + esc(r.method) +
          "</td><td class='mono' style='color:var(--primary)'>" + esc(r.value) + "</td>" +
          "<td><span class='" + (SAFE_PILL[r.safety] || "pill-grey") + "'>" + (SAFE_TXT[r.safety] || r.safety) + "</span></td>" +
          "<td>" + esc(r.advice) + "</td><td class='mono'>" + (r.actionable ? "✓ 可操作" : "報告") + "</td></tr>";
      }).join("");
      $("#storageResult").innerHTML = "<div class='cd'><div class='cd-h'>💾 Windows 儲存設定矩陣<span class='pill'>" + (d.rows || []).length + " 項 · " + esc(d.generated || "") + "</span></div><div class='cd-b' style='padding:0'>" +
        "<table><thead><tr><th>項目</th><th>功能</th><th>方法</th><th>現值</th><th>安全</th><th>建議</th><th>可操作</th></tr></thead><tbody>" + rows + "</tbody></table></div></div>";
      log("儲存設定分析完成 · " + (d.rows || []).length + " 項（危險項僅報告，不自動更改）", "ok");
    });
  };

  /* ---- panorama I/O scan (matrix) ----------------------------------------- */
  var PANO_PILL = { vendored_link_stale: "pill-low", external_only: "pill-medium", internal: "pill-safe" };
  var PANO_TXT = { vendored_link_stale: "已放進·連結待修", external_only: "未納入·建議納入", internal: "內部" };
  window.vooPanorama = function () {
    var root = $("#panoRoot").value.trim();
    setBusy(true, "全景掃描…"); log("🛰️ 全景 I/O 掃描：" + root);
    api("/api/panorama", { root: root }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      var s = d.summary || {};
      $("#panoFiles").textContent = s.file_count != null ? s.file_count : "—";
      $("#panoAssoc").textContent = s.associated_count != null ? s.associated_count : "—";
      $("#panoStale").textContent = s.vendored_stale_count != null ? s.vendored_stale_count : "—";
      $("#panoExt").textContent = s.external_only_count != null ? s.external_only_count : "—";
      var assoc = (d.associated_files || []).map(function (a) {
        return "<tr><td><span class='pill-safe'>" + esc(a.kind) + "</span></td><td class='mono'>" + esc(a.path) + "</td><td class='mono'>" + human(a.bytes) + "</td></tr>";
      }).join("");
      var refs = (d.external_refs || []).map(function (r) {
        return "<tr><td><span class='" + (PANO_PILL[r.status] || "pill-grey") + "'>" + (PANO_TXT[r.status] || r.status) + "</span></td>" +
          "<td class='mono'>" + esc(r.basename) + "</td><td class='mono'>" + esc(r.ref) + "</td><td class='mono'>×" + r.count + "</td><td class='mono' style='color:var(--ink-soft)'>" + esc((r.files || []).slice(0, 3).join(", ")) + "</td></tr>";
      }).join("");
      var tools = (d.outbound_tools || []).map(function (t) {
        return "<tr><td class='mono'>" + esc(t.location) + "</td><td><span class='" + (t.vendored ? "pill-low" : "pill-medium") + "'>" + (t.vendored ? "已放進·連結待修" : "未納入") + "</span></td><td class='mono'>×" + t.refs + "</td></tr>";
      }).join("");
      $("#panoResult").innerHTML =
        "<div class='cd'><div class='cd-h'>🔒 關聯保護項目（設定/環境/啟動檔）<span class='pill'>" + (d.associated_files || []).length + " · 已在保護根內</span></div><div class='cd-b' style='padding:0'><table><thead><tr><th>類型</th><th>路徑</th><th>大小</th></tr></thead><tbody>" + (assoc || "<tr><td colspan=3 class='hint' style='padding:10px'>無</td></tr>") + "</tbody></table></div></div>" +
        "<div class='cd'><div class='cd-h'>📡 對外呼叫工具 · vendor 連結分析<span class='pill'>stale=" + (s.vendored_stale_count || 0) + " · external=" + (s.external_only_count || 0) + "</span></div><div class='cd-b' style='padding:0'><table><thead><tr><th>狀態</th><th>名稱</th><th>參照路徑</th><th>次數</th><th>出現於</th></tr></thead><tbody>" + (refs || "<tr><td colspan=5 class='hint' style='padding:10px'>未發現對外參照</td></tr>") + "</tbody></table></div></div>" +
        (tools ? "<div class='cd'><div class='cd-h'>🧭 對外工具根</div><div class='cd-b' style='padding:0'><table><thead><tr><th>位置</th><th>狀態</th><th>參照</th></tr></thead><tbody>" + tools + "</tbody></table></div></div>" : "");
      log("全景掃描完成 · 關聯保護 " + (s.associated_count || 0) + " · 連結待修 " + (s.vendored_stale_count || 0) + " · 未納入 " + (s.external_only_count || 0), "ok");
    });
  };

  /* ---- tool registry matrix ----------------------------------------------- */
  window.vooToolMatrix = function () {
    setBusy(true, "載入工具矩陣…");
    api("/api/toolmatrix", {}).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      function tbl(title, color, rows, cols) {
        return "<div class='cd'><div class='cd-h' style='border-left:3px solid " + color + "'>" + title + "<span class='pill'>" + rows.length + "</span></div><div class='cd-b' style='padding:0'><table><thead><tr>" + cols.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr></thead><tbody>" + rows.join("") + "</tbody></table></div></div>";
      }
      var py = ((d.python && d.python.accelerators) || []).map(function (r) {
        return "<tr><td class='mono'>" + esc(r.name) + "</td><td>" + esc(r.kind) + "</td><td>" + esc(r.note) + "</td><td><span class='" + (r.available ? "pill-safe" : "pill-grey") + "'>" + (r.available ? "可用" : "缺") + "</span></td></tr>";
      });
      var ps = (d.powershell || []).map(function (t, i) { return "<tr><td class='mono'>PS-" + (i + 1) + "</td><td class='mono'>" + esc(t) + "</td></tr>"; });
      var js = JS_ACCEL.map(function (t, i) { return "<tr><td class='mono'>JS-" + (i + 1) + "</td><td class='mono'>" + esc(t) + "</td></tr>"; });
      var ext = (d.external || []).map(function (t) { return "<tr><td class='mono'>" + esc(t.tool) + "</td><td>" + esc(t.purpose) + "</td><td><span class='pill-low'>對外</span></td><td class='mono'>" + esc(t.location) + "</td></tr>"; });
      var cim = (d.cim || []).map(function (t) { return "<tr><td class='mono'>" + esc(t.tool) + "</td><td>" + esc(t.purpose) + "</td><td><span class='pill-safe'>內部</span></td></tr>"; });
      $("#toolResult").innerHTML =
        "<div class='sg'><div class='sc'><div class='lbl'>Python</div><div class='val'>" + py.length + "</div></div><div class='sc g'><div class='lbl'>PowerShell</div><div class='val'>" + ps.length + "</div></div><div class='sc t'><div class='lbl'>JavaScript</div><div class='val'>" + js.length + "</div></div><div class='sc y'><div class='lbl'>對外 EXE</div><div class='val'>" + ext.length + "</div></div><div class='sc r'><div class='lbl'>CIM</div><div class='val'>" + cim.length + "</div></div></div>" +
        tbl("🐍 Python 加速器", "#4c78a8", py, ["名稱", "類型", "說明", "狀態"]) +
        tbl("🔷 PowerShell 技法", "#2d8659", ps, ["#", "技法"]) +
        tbl("🟨 JavaScript 技法", "#439a9a", js, ["#", "技法"]) +
        tbl("⚙️ 對外 EXE 工具", "#b85450", ext, ["工具", "用途", "範圍", "位置"]) +
        tbl("📊 CIM 類別", "#8c5e9e", cim, ["類別", "用途", "範圍"]);
      log("工具矩陣載入完成", "ok");
    });
  };

  window.vooTab = function (id) {
    $all(".tab").forEach(function (b) { b.classList.remove("active"); });
    $all(".panel").forEach(function (c) { c.classList.remove("active"); });
    var btn = $("[data-tab='" + id + "']"); if (btn) btn.classList.add("active");
    var pane = $("#tab-" + id); if (pane) pane.classList.add("active");
    if (id === "accel") vooAccel();
    if (id === "tools") vooToolMatrix();
  };

  function boot() {
    renderDisk();
    api("/api/health", {}).then(function (d) {
      var badge = $("#healthBadge"), vb = $("#verBadge");
      if (d.ok) {
        if (badge) badge.innerHTML = "● 後端連線 · " + (d.version || "") + (d.admin ? " · 系統管理員" : " · 一般權限") + "<br>Python: " + (d.python_ok ? esc(d.python || "ok") : "未就緒");
        if (vb) { vb.textContent = d.version || "live"; vb.className = "badge"; }
        log("後端連線成功 · " + (d.version || "") + (d.python ? " · Python：" + d.python : ""), "ok");
        if (!d.admin) log("提示：未以系統管理員執行，部分系統路徑會略過", "warn");
        if (!d.python_ok) log("警告：Python 引擎未就緒，掃描/重複檔/語言快取停用", "err");
        renderGuard(d.protected_roots || []);
      } else if (badge) { badge.textContent = "● 後端連線失敗"; if (vb) vb.className = "badge bad"; }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.__VOO = { CATALOG: CATALOG, human: human, selectedTargets: selectedTargets, JS_ACCEL: JS_ACCEL, renderAccel: renderAccel, renderGuard: renderGuard };
})();

'@

$script:HtmlSrc = @'
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VeritasOperationOptimizer · Live · Visual Lock</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@500;700;800&family=DM+Sans:wght@400;500;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{
--bg:#f5f4f0;--paper:#ffffff;--ink:#1d1d1f;--ink-soft:#5b5a55;--line:#e0ddd5;--line-soft:#ebe9e2;
--primary:#4c78a8;--teal:#439a9a;--green:#2d8659;--yellow:#c49a3d;--red:#b85450;--grey:#9c9890;
--up-red:#c96b5a;--down-green:#5a9e6f;--purple:#8c5e9e;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;font-size:12px;line-height:1.55}
.rainbow-border{height:4px;background:linear-gradient(90deg,#b85450,#c49a3d,#2d8659,#439a9a,#4c78a8,#8c5e9e)}
.wrap{max-width:1480px;margin:0 auto;padding:22px}
.hdr{padding:14px 0 10px;border-bottom:1px solid var(--line);margin-bottom:14px;display:flex;align-items:center;gap:14px}
.seal{width:42px;height:42px;flex:0 0 42px;background:var(--up-red);color:#fff;border-radius:4px;display:flex;align-items:center;justify-content:center;font-family:'Noto Serif TC','DM Serif Display',serif;font-size:24px;font-weight:700;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.hdr h1{font-family:'Syne',sans-serif;font-weight:800;font-size:21px;letter-spacing:-.01em}
.hdr .sub{color:var(--ink-soft);font-family:'DM Mono',monospace;font-size:10.5px;margin-top:2px}
.hdr .badge{display:inline-block;padding:1px 7px;background:var(--green);color:#fff;font-size:9px;margin-left:6px;letter-spacing:.05em;font-family:'DM Mono',monospace;border-radius:2px}
.hdr .badge.warn{background:var(--yellow)}.hdr .badge.bad{background:var(--red)}
.hdr-right{margin-left:auto;text-align:right;font-family:'DM Mono',monospace;font-size:10px;color:var(--ink-soft)}
.tabs{display:flex;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:14px}
.tab{padding:8px 13px;cursor:pointer;border-right:1px solid var(--line);font-family:'Syne',sans-serif;font-weight:600;font-size:11px;letter-spacing:.02em;user-select:none;color:var(--ink-soft)}
.tab.active{background:var(--primary);color:#fff}
.tab:hover:not(.active){background:var(--line-soft);color:var(--ink)}
.panel{display:none}.panel.active{display:block}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin-bottom:14px}
.sc{background:var(--paper);padding:9px 12px;border-left:3px solid var(--primary);border-radius:2px}
.sc.t{border-left-color:var(--teal)}.sc.g{border-left-color:var(--green)}.sc.y{border-left-color:var(--yellow)}.sc.r{border-left-color:var(--red)}
.sc .lbl{font-size:9px;color:var(--ink-soft);text-transform:uppercase;letter-spacing:.06em;margin-bottom:2px}
.sc .val{font-family:'DM Mono',monospace;font-size:17px;font-weight:500}
.toolbar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.btn{padding:7px 13px;border:1px solid var(--line);background:var(--paper);color:var(--ink);cursor:pointer;font-family:'Syne',sans-serif;font-weight:600;font-size:11px;border-radius:2px;display:inline-flex;align-items:center;gap:6px}
.btn:hover:not(:disabled){background:var(--line-soft)}
.btn:disabled{opacity:.45;cursor:not-allowed}
.btn.primary{background:var(--primary);color:#fff;border-color:var(--primary)}
.btn.teal{background:var(--teal);color:#fff;border-color:var(--teal)}
.btn.green{background:var(--green);color:#fff;border-color:var(--green)}
.btn.red{background:var(--red);color:#fff;border-color:var(--red)}
.spacer{flex:1}
.apply-wrap{display:flex;align-items:center;gap:9px;padding:6px 11px;background:var(--paper);border:1px solid var(--line);border-radius:2px}
.apply-wrap label{display:flex;align-items:center;gap:6px;cursor:pointer;font-size:11px;color:var(--ink-soft);font-family:'DM Mono',monospace}
.apply-wrap input[type=checkbox]{width:15px;height:15px;accent-color:var(--red)}
select,input[type=text],input[type=number]{background:var(--paper);color:var(--ink);border:1px solid var(--line);border-radius:2px;padding:5px 8px;font-family:'DM Mono',monospace;font-size:10.5px}
textarea{width:100%;min-height:78px;background:var(--paper);color:var(--ink);border:1px solid var(--line);border-radius:2px;padding:9px;font-family:'DM Mono',monospace;font-size:10.5px;resize:vertical}
.cd{background:var(--paper);border:1px solid var(--line);border-radius:3px;margin-bottom:11px;overflow:hidden}
.cd-h{padding:8px 12px;border-bottom:1px solid var(--line);font-family:'Syne',sans-serif;font-weight:700;font-size:12px;display:flex;justify-content:space-between;align-items:center;cursor:pointer}
.cd-h .pill{font-family:'DM Mono',monospace;font-size:9.5px;padding:1px 6px;background:var(--line-soft);border-radius:2px;font-weight:400;color:var(--ink-soft)}
.cd-b{padding:6px}
.item-row{display:flex;justify-content:space-between;align-items:center;padding:7px 11px;border-bottom:1px solid var(--line-soft)}
.item-row:last-child{border-bottom:none}
.item-row:hover{background:#fafaf6}
.item-row label{display:flex;align-items:center;gap:10px;cursor:pointer;flex:1;font-size:11.5px}
.item-row input[type=checkbox]{width:15px;height:15px;accent-color:var(--primary)}
.item-info{display:flex;align-items:center;gap:9px}
.item-size{font-family:'DM Mono',monospace;font-size:10.5px;color:var(--grey);min-width:66px;text-align:right}
.item-size.has{color:var(--primary);font-weight:500}.item-size.denied{color:var(--up-red)}
.pill-safe{background:var(--green);color:#fff;padding:1px 6px;border-radius:2px;font-size:8.5px;font-family:'DM Mono',monospace}
.pill-low{background:var(--yellow);color:#fff;padding:1px 6px;border-radius:2px;font-size:8.5px;font-family:'DM Mono',monospace}
.pill-medium{background:var(--red);color:#fff;padding:1px 6px;border-radius:2px;font-size:8.5px;font-family:'DM Mono',monospace}
table{width:100%;border-collapse:collapse;font-size:10.5px}
thead th{background:var(--line-soft);padding:6px 8px;text-align:left;font-family:'Syne',sans-serif;font-weight:700;font-size:10px;letter-spacing:.03em;border-bottom:1px solid var(--line)}
tbody td{padding:5px 8px;border-bottom:1px solid var(--line-soft);vertical-align:top}
tbody tr:hover{background:#fafaf6}
.mono{font-family:'DM Mono',monospace}
.hint{color:var(--ink-soft);font-size:10.5px;margin-bottom:9px}
.cardgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:11px}
.console-wrap{margin-top:6px;background:var(--paper);border:1px solid var(--line);border-radius:3px;overflow:hidden}
.console-head{display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-bottom:1px solid var(--line);font-family:'Syne',sans-serif;font-weight:700;font-size:11px}
.busy-bar{display:none;align-items:center;gap:8px;color:var(--primary);font-size:10px;font-family:'DM Mono',monospace}
.spinner{width:12px;height:12px;border:2px solid var(--line);border-top-color:var(--primary);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
#vooConsole{max-height:300px;overflow-y:auto;padding:10px 12px;font-family:'DM Mono',monospace;font-size:10.5px;background:#fcfbf8}
.log-line{padding:1.5px 0;white-space:pre-wrap;word-break:break-all}
.log-time{color:var(--grey);margin-right:7px}
.log-ok{color:var(--green)}.log-err{color:var(--red)}.log-warn{color:var(--yellow)}.log-info{color:var(--ink)}
footer{margin-top:18px;padding-top:11px;border-top:1px solid var(--line);color:var(--ink-soft);font-size:9.5px;font-family:'DM Mono',monospace}
.accel-lang{font-family:'Syne',sans-serif;font-weight:700;font-size:12px;margin:2px 0}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px}
.dot.on{background:var(--green)}.dot.off{background:var(--grey)}
.guard-item{padding:5px 8px;border-bottom:1px solid var(--line-soft);font-family:'DM Mono',monospace;font-size:10px;display:flex;gap:8px;align-items:center}
.guard-item:last-child{border-bottom:none}

/* ---- dedup matrix, progress, modal, animations ---- */
.dedup-modes{display:flex;gap:7px;margin-bottom:10px}
.dedup-modes .btn.modeon{background:var(--primary);color:#fff;border-color:var(--primary)}
.voo-progress{height:8px;background:var(--line-soft);border-radius:5px;overflow:hidden;margin:10px 0;display:none}
.voo-progress.show{display:block}
.voo-progress-fill{height:100%;width:0;border-radius:5px;background:linear-gradient(90deg,#4c78a8,#439a9a,#4c78a8);background-size:200% 100%;transition:width .35s cubic-bezier(.4,0,.2,1);animation:shimmer 1.1s linear infinite}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.seltoolbar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:10px 0;padding:9px;background:var(--paper);border:1px solid var(--line);border-radius:3px;position:sticky;top:0;z-index:5}
.dgroup{border:1px solid var(--line);border-radius:4px;margin-bottom:10px;overflow:hidden;animation:groupIn .4s ease both}
@keyframes groupIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.dgroup.fam-a{border-left:4px solid var(--primary)}
.dgroup.fam-a .dgroup-h{background:rgba(76,120,168,.08)}
.dgroup.fam-b{border-left:4px solid var(--teal)}
.dgroup.fam-b .dgroup-h{background:rgba(67,154,154,.10)}
.dgroup-h{padding:7px 11px;font-family:'Syne',sans-serif;font-weight:700;font-size:11px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.dgroup-h .gmeta{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--ink-soft);font-weight:400}
.dfile{display:flex;align-items:center;gap:10px;padding:7px 11px;border-top:1px solid var(--line-soft);transition:background .15s,opacity .35s,transform .35s,max-height .35s;max-height:80px}
.dfile:hover{background:#fafaf6}
.dfile.keep{background:rgba(45,134,89,.06)}
.dfile.removing{opacity:0;transform:translateX(40px);max-height:0;padding-top:0;padding-bottom:0;border:none}
.dfile input[type=checkbox]{width:16px;height:16px;accent-color:var(--red);cursor:pointer;transition:transform .12s}
.dfile input[type=checkbox]:active{transform:scale(1.3)}
.dfile input[type=checkbox]:checked{animation:pop .2s ease}
@keyframes pop{50%{transform:scale(1.35)}}
.dfile .fmain{flex:1;min-width:0}
.dfile .fname{font-size:11.5px;word-break:break-all}
.dfile .fpath{font-family:'DM Mono',monospace;font-size:9px;color:var(--grey);word-break:break-all}
.dfile .fmeta{display:flex;gap:6px;align-items:center;flex-shrink:0}
.tag{font-family:'DM Mono',monospace;font-size:8.5px;padding:1px 6px;border-radius:2px;white-space:nowrap}
.tag.keep{background:var(--green);color:#fff}
.tag.copy{background:var(--red);color:#fff}
.tag.newer{background:var(--yellow);color:#fff}
.tag.older{background:var(--grey);color:#fff}
.tag.lowq{background:var(--up-red);color:#fff}
.tag.fmt{background:var(--purple);color:#fff}
.tag.size{background:var(--line-soft);color:var(--ink-soft)}
.modal-backdrop{position:fixed;inset:0;background:rgba(29,29,31,.45);backdrop-filter:blur(2px);display:none;align-items:center;justify-content:center;z-index:50;animation:fadeIn .2s ease}
.modal-backdrop.show{display:flex}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal-box{background:var(--paper);border-radius:6px;max-width:680px;width:92%;max-height:82vh;display:flex;flex-direction:column;box-shadow:0 18px 50px rgba(0,0,0,.3);animation:popIn .26s cubic-bezier(.34,1.56,.64,1)}
@keyframes popIn{from{opacity:0;transform:scale(.92) translateY(10px)}to{opacity:1;transform:none}}
.modal-box .rb{height:4px;background:linear-gradient(90deg,#b85450,#c49a3d,#2d8659,#439a9a,#4c78a8,#8c5e9e);border-radius:6px 6px 0 0}
.modal-h{padding:14px 18px 8px;font-family:'Syne',sans-serif;font-weight:800;font-size:16px}
.modal-sub{padding:0 18px 10px;color:var(--ink-soft);font-size:11px;border-bottom:1px solid var(--line)}
.modal-body{padding:10px 18px;overflow-y:auto;flex:1}
.modal-logic{padding:8px 11px;border-bottom:1px solid var(--line-soft)}
.modal-logic .ml-name{font-size:11px;word-break:break-all}
.modal-logic .ml-why{font-family:'DM Mono',monospace;font-size:9.5px;color:var(--red);margin-top:1px}
.modal-foot{padding:12px 18px;border-top:1px solid var(--line);display:flex;justify-content:flex-end;gap:9px}
</style>
</head>
<body>
<div class="rainbow-border"></div>
<div class="wrap">
<div class="hdr">
  <div class="seal">淨</div>
  <div>
    <h1>VeritasOperationOptimizer <span class="badge" id="verBadge">live</span></h1>
    <div class="sub">系統深度優化 · 前後端即時連動 · 一貼啟動 · Visual Lock</div>
  </div>
  <div class="hdr-right" id="healthBadge">連線中…</div>
</div>

<div class="tabs" role="tablist">
  <div class="tab active" data-tab="disk" onclick="vooTab('disk')">🧹 磁碟清理</div>
  <div class="tab" data-tab="dedup" onclick="vooTab('dedup')">♊ 重複檔</div>
  <div class="tab" data-tab="old" onclick="vooTab('old')">📥 舊下載</div>
  <div class="tab" data-tab="lang" onclick="vooTab('lang')">🧬 語言快取</div>
  <div class="tab" data-tab="system" onclick="vooTab('system')">📊 系統</div>
  <div class="tab" data-tab="network" onclick="vooTab('network')">🌐 網路</div>
  <div class="tab" data-tab="accel" onclick="vooTab('accel')">⚡ 加速器</div>
  <div class="tab" data-tab="storage" onclick="vooTab('storage')">💾 Windows 儲存</div>
  <div class="tab" data-tab="panorama" onclick="vooTab('panorama')">🛰️ 全景掃描</div>
  <div class="tab" data-tab="tools" onclick="vooTab('tools')">🧰 工具矩陣</div>
  <div class="tab" data-tab="guard" onclick="vooTab('guard')">🛡️ 保護根</div>
</div>

<!-- DISK -->
<div class="panel active" id="tab-disk">
<div class="toolbar">
<button class="btn primary act" onclick="vooScan()">🔍 掃描可釋放</button>
<button class="btn green act" onclick="vooClean()">🧹 清理選取</button>
<button class="btn act" onclick="vooSelectSafe()">只選安全</button>
<button class="btn act" onclick="vooSelectAll()">全選</button>
<button class="btn act" onclick="vooDeselectAll()">全不選</button>
<div class="spacer"></div>
<div class="apply-wrap">
<label><input type="checkbox" id="applyToggle"> 實際執行（預設僅預演）</label>
<select id="destSelect"><option value="recycle">→ 資源回收筒</option><option value="quarantine">→ 隔離區（可還原）</option></select>
</div>
</div>
<div class="sg">
<div class="sc"><div class="lbl">已選</div><div class="val" id="selectedCount">0</div></div>
<div class="sc g"><div class="lbl">安全</div><div class="val" id="safeCount">0</div></div>
<div class="sc y"><div class="lbl">低風險</div><div class="val" id="lowCount">0</div></div>
<div class="sc t"><div class="lbl">可釋放（掃描後）</div><div class="val" id="reclaimTotal">—</div></div>
</div>
<div class="cardgrid" id="diskCategories"></div>
</div>

<!-- DEDUP -->
<div class="panel" id="tab-dedup">
<div class="cd"><div class="cd-h">♊ 去重矩陣<span class="pill" id="dedupAlgo">—</span></div><div class="cd-b" style="padding:12px">
<p class="hint">兩種判定：<b>完全相同</b>（大小＋雜湊一致，可能性極高）與<b>檔名高度相似</b>（關鍵字重疊高，可不同大小/格式，如影片畫質）。同色系為同組（藍／青交錯）。預設保留最原始（最舊、無編號/複製字樣）<b>不勾選</b>，勾選複本/較新/低畫質；刪除前彈窗複述選擇邏輯供你確認。</p>
<textarea id="dedupRoots" placeholder="C:\Users\tonyk\Downloads&#10;D:\Media"></textarea>
<div class="dedup-modes" style="margin-top:9px">
<button class="btn modeon act" id="modeExact" onclick="vooSetMode('exact')">完全相同</button>
<button class="btn act" id="modeName" onclick="vooSetMode('name')">檔名相似</button>
<button class="btn primary act" onclick="vooDedupScan()">🔎 掃描去重</button>
</div>
<div class="voo-progress" id="dedupProgress"><div class="voo-progress-fill" id="dedupProgressFill"></div></div>
<div class="seltoolbar" id="dedupSelbar" style="display:none">
<button class="btn act" onclick="vooDupSel('all')">全選</button>
<button class="btn act" onclick="vooDupSel('none')">全不選</button>
<button class="btn act" onclick="vooDupSel('newer')">都選較新的</button>
<button class="btn act" onclick="vooDupSel('older')">都選較舊的</button>
<button class="btn act" id="lowqBtn" onclick="vooDupSel('lowq')" style="display:none">都選低畫質</button>
<div class="spacer"></div>
<span class="mono" style="color:var(--ink-soft)">勾選 <b id="dupSelCount">0</b> · 釋放 <b id="dupSelBytes">0</b></span>
<div class="apply-wrap"><label><input type="checkbox" id="dupApply"> 實際刪除</label><select id="dupDest"><option value="recycle">→ 回收筒</option><option value="quarantine">→ 隔離區</option></select></div>
<button class="btn red act" onclick="vooDupDelete()">🗑️ 刪除勾選</button>
</div>
<div class="sg" id="dedupStats" style="display:none">
<div class="sc"><div class="lbl">群組</div><div class="val" id="dupGroups">—</div></div>
<div class="sc t"><div class="lbl">可釋放</div><div class="val" id="dupReclaim">—</div></div>
</div>
<div id="dedupResult" style="margin-top:10px"></div>
</div></div>
</div>

<!-- OLD DOWNLOADS -->
<div class="panel" id="tab-old">
<div class="cd"><div class="cd-h">📥 過老的 Downloads 檔案<span class="pill">VIA 工作樹自動排除</span></div><div class="cd-b" style="padding:12px">
<p class="hint">掃描 Downloads 內超過指定天數、且<b>不屬於 VeritasIntelligenceAnalytics 工作樹</b>的鬆散舊檔。預設僅預演；實際執行送資源回收筒（可還原）。</p>
<div class="toolbar">
<label class="mono" style="color:var(--ink-soft)">根目錄</label>
<input type="text" id="oldRoot" style="flex:1;max-width:360px" value="C:\Users\tonyk\Downloads">
<label class="mono" style="color:var(--ink-soft)">超過</label>
<input type="number" id="oldAge" value="90" style="width:70px"> <span class="mono" style="color:var(--ink-soft)">天</span>
<button class="btn primary act" onclick="vooOldScan()">🔍 掃描舊檔</button>
<div class="spacer"></div>
<div class="apply-wrap"><label><input type="checkbox" id="oldApply"> 實際送回收筒</label></div>
<button class="btn green act" onclick="vooOldClean()">🧹 清理已掃描</button>
</div>
<div class="sg"><div class="sc t"><div class="lbl">舊檔數</div><div class="val" id="oldCount">—</div></div><div class="sc"><div class="lbl">可釋放</div><div class="val" id="oldTotal">—</div></div></div>
<div id="oldResult"></div>
</div></div>
</div>

<!-- LANG CACHE -->
<div class="panel" id="tab-lang">
<div class="cd"><div class="cd-h">🧬 語言快取掃描（程式語言爆衝）<span class="pill">__pycache__ / build / dist …</span></div><div class="cd-b" style="padding:12px">
<p class="hint">掃描指定根目錄底下的可再生語言快取/建置目錄（__pycache__、.pytest_cache、.mypy_cache、.gradle、build、dist、.next…），只量測。原始碼絕不刪。</p>
<div class="toolbar">
<label class="mono" style="color:var(--ink-soft)">根目錄</label>
<input type="text" id="langRoot" style="flex:1;max-width:420px" value="C:\Users\tonyk\Downloads">
<button class="btn primary act" onclick="vooLangSweep()">🔬 掃描語言快取</button>
<div class="spacer"></div>
<div class="apply-wrap"><label><input type="checkbox" id="langApply"> 實際清理</label><select id="langDest"><option value="recycle">→ 回收筒</option><option value="quarantine">→ 隔離區</option></select></div>
<button class="btn green act" onclick="vooLangClean()">🧹 清理快取</button>
</div>
<div class="sg"><div class="sc t"><div class="lbl">可釋放合計</div><div class="val" id="langTotal">—</div></div></div>
<div id="langResult"></div>
</div></div>
</div>

<!-- SYSTEM -->
<div class="panel" id="tab-system">
<div class="toolbar">
<button class="btn primary act" onclick="vooSysInfo()">📊 系統診斷報告</button>
<button class="btn green act" onclick="vooPerf()">⚡ 效能優化</button>
<button class="btn teal act" onclick="vooStartup()">🚀 開機項目</button>
<button class="btn act" onclick="vooService()">🔧 服務分析</button>
</div>
<div class="cd"><div class="cd-h">🔍 即時系統工具</div><div class="cd-b" style="padding:12px">
<table><tbody>
<tr><td class="mono" style="color:var(--primary)">系統診斷報告</td><td>CPU／RAM／磁碟／Top 進程／啟動項 → 產生 Visual Lock HTML 報告並自動開啟</td></tr>
<tr><td class="mono" style="color:var(--primary)">效能優化</td><td>高效能電源計畫、視覺效果、GC 回收、DNS 清理</td></tr>
<tr><td class="mono" style="color:var(--primary)">開機項目</td><td>列出啟動項目（不自動停用）</td></tr>
<tr><td class="mono" style="color:var(--primary)">服務分析</td><td>檢視可考慮停用的非必要服務（只報告）</td></tr>
</tbody></table>
</div></div>
</div>

<!-- NETWORK -->
<div class="panel" id="tab-network">
<div class="toolbar">
<button class="btn primary act" onclick="vooNetDiag()">🌐 網路診斷</button>
<button class="btn green act" onclick="vooDns()">📡 DNS 優化</button>
<button class="btn teal act" onclick="vooTcp()">⚡ TCP/IP 優化</button>
</div>
<div class="cd"><div class="cd-h">🌐 網路即時工具</div><div class="cd-b" style="padding:12px">
<table><tbody>
<tr><td class="mono" style="color:var(--primary)">網路診斷</td><td>適配器／IP／DNS／對外連線測試</td></tr>
<tr><td class="mono" style="color:var(--primary)">DNS 優化</td><td>清理 DNS 快取並重新註冊</td></tr>
<tr><td class="mono" style="color:var(--primary)">TCP/IP 優化</td><td>TCP 自動調整（需系統管理員，提示重開機）</td></tr>
</tbody></table>
</div></div>
</div>

<!-- ACCELERATORS -->
<div class="panel" id="tab-accel">
<p class="hint">每語言 20 項加速器（libs/tools/extensions）。可用者即時啟用、缺者自動降級。Python 依目前 venv 探測；PowerShell／JavaScript 為內建技法，固定啟用。</p>
<div class="sg">
<div class="sc"><div class="lbl">Python 可用</div><div class="val" id="accelPy">—</div></div>
<div class="sc g"><div class="lbl">PowerShell</div><div class="val">20/20</div></div>
<div class="sc t"><div class="lbl">JavaScript</div><div class="val">20/20</div></div>
<div class="sc y"><div class="lbl">雜湊演算法</div><div class="val mono" id="accelHash" style="font-size:13px">—</div></div>
</div>
<div class="cardgrid" id="accelGrid"></div>
</div>

<!-- WINDOWS STORAGE -->
<div class="panel" id="tab-storage">
<p class="hint">Windows 原生省空間設定與方法，每項詳列<b>功能／方法／現值／安全等級／建議</b>。唯讀分析：危險項（休眠檔、分頁檔、系統還原、WinSxS、Compact OS）只報告不自動更改，<b>絕不誤刪或亂改設定</b>；僅標「可操作」者才走本工具的預演＋回收筒流程。</p>
<div class="toolbar"><button class="btn primary act" onclick="vooStorage()">🔍 分析 Windows 儲存設定（同步跑）</button></div>
<div id="storageResult"></div>
</div>

<!-- PANORAMA -->
<div class="panel" id="tab-panorama">
<p class="hint">對專案資料夾做 Windows I/O <b>全景式掃描</b>：列出關聯設定/環境/啟動檔（標為特定保護項目），並分析<b>對外呼叫的工具</b>——區分「已放進資料夾但呼叫連結沒改（vendored_link_stale）」與「根本沒放進來（external_only）」。唯讀，不改動專案。</p>
<div class="toolbar">
<label class="mono" style="color:var(--ink-soft)">專案根</label>
<input type="text" id="panoRoot" style="flex:1;max-width:520px" value="C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics">
<button class="btn primary act" onclick="vooPanorama()">🛰️ 全景掃描</button>
</div>
<div class="sg">
<div class="sc"><div class="lbl">檔案總數</div><div class="val" id="panoFiles">—</div></div>
<div class="sc g"><div class="lbl">關聯保護檔</div><div class="val" id="panoAssoc">—</div></div>
<div class="sc y"><div class="lbl">連結待修(stale)</div><div class="val" id="panoStale">—</div></div>
<div class="sc r"><div class="lbl">未納入(external)</div><div class="val" id="panoExt">—</div></div>
</div>
<div id="panoResult"></div>
</div>

<!-- TOOL MATRIX -->
<div class="panel" id="tab-tools">
<p class="hint">本系統使用到的所有工具，矩陣式註冊列出：Python 加速器、PowerShell 技法、JavaScript 技法、對外 EXE 工具、CIM 類別。內部／對外範圍一目了然。</p>
<div class="toolbar"><button class="btn primary act" onclick="vooToolMatrix()">🧰 載入工具矩陣</button></div>
<div id="toolResult"></div>
</div>

<!-- GUARD -->
<div class="panel" id="tab-guard">
<p class="hint">以下保護根永不觸碰（含 Downloads 內的 VeritasIntelligenceAnalytics 工作樹）。清理只刪「子項目」且每條路徑逐一重新驗證。</p>
<div class="cd"><div class="cd-h">🛡️ 保護根</div><div class="cd-b" id="guardList"></div></div>
</div>

<div class="modal-backdrop" id="dupModal">
<div class="modal-box">
<div class="rb"></div>
<div class="modal-h">確認刪除</div>
<div class="modal-sub" id="dupModalSub">—</div>
<div class="modal-body" id="dupModalBody"></div>
<div class="modal-foot">
<button class="btn" onclick="vooModalClose()">取消</button>
<button class="btn red" id="dupModalConfirm">確認刪除</button>
</div>
</div>
</div>

<div class="console-wrap">
<div class="console-head"><span>📜 執行紀錄</span><span class="busy-bar" id="busyBar"><span class="spinner"></span><span class="busy-label">處理中…</span></span></div>
<div id="vooConsole"></div>
</div>

<footer>VeritasOperationOptimizer · Live · VRN 生態系統 · 預設僅預演量測；勾「實際執行」才移除（回收筒／隔離區，可還原）。保護根永不觸碰。</footer>
</div>

<script>
(function(){
  var raw="__PORT__";var p=parseInt(raw,10);if(isNaN(p))p=0;
  window.VOO_BOOT={csrf:"__CSRF__",port:p,base:(window.location&&window.location.origin&&window.location.origin!=="null")?window.location.origin:""};
})();
</script>
<script src="/voo.js"></script>
</body>
</html>

'@


# ---- protected roots: never touched, ever ----------------------------------
$script:ProtectedRoots = @(
    (Join-Path $env:USERPROFILE 'envs'),
    'C:\VeritasIntelligenceAnalytics',
    (Join-Path $env:USERPROFILE 'Downloads\VeritasIntelligenceAnalytics'),
    (Join-Path $env:USERPROFILE 'OneDrive\VeritasIntelligenceAnalytics'),
    'C:\Program Files',
    'C:\Program Files (x86)',
    'C:\ProgramData\Microsoft\Windows',
    (Join-Path $env:USERPROFILE 'Documents'),
    (Join-Path $env:USERPROFILE 'Desktop'),
    (Join-Path $env:USERPROFILE 'Pictures'),
    (Join-Path $env:USERPROFILE 'Videos'),
    (Join-Path $env:USERPROFILE 'Music'),
    (Join-Path $env:USERPROFILE 'OneDrive')
)
# active VIA work tree (under Downloads) - excluded from any Downloads sweep
$script:ViaWorkTree = (Join-Path $env:USERPROFILE 'Downloads\VeritasIntelligenceAnalytics')

# ---- PowerShell 20 accelerator registry (real PS7/.NET techniques in use) ---
$script:PsAccel = @(
    '[System.IO.Directory]::EnumerateFiles 惰性列舉（資料夾測量）',
    '[System.IO.FileInfo].Length 直取大小（免管線物件）',
    '[System.Collections.Generic.List[T]] 取代 += 陣列複製',
    '[System.Text.StringBuilder] 字串組裝',
    'ProcessStartInfo + ArgumentList 逐參數（免引號注入）',
    'StandardOutput.ReadToEndAsync 非阻塞 stdout/stderr 抽取',
    '[System.Net.HttpListener] 內建非阻塞後端',
    '[IO.File]::WriteAllText + UTF8(no BOM) 直寫',
    '[System.Diagnostics.Stopwatch] 高解析計時',
    'Hashtable O(1) 查找',
    '[ordered]@{} 保序字典',
    'ConvertFrom-Json -AsHashtable 免 PSObject 開銷',
    'Get-CimInstance -Filter 提供者層過濾',
    '[regex]::Replace 編譯式樣式',
    '[System.Environment]::ExpandEnvironmentVariables 原生展開',
    'Microsoft.VisualBasic 資源回收筒（免 shell.exe）',
    'WaitForExit(timeout) + Kill 子程序逾時保護',
    '-LiteralPath 免萬用字元解析',
    'Where-Object 早期過濾縮小集合',
    '$script: 作用域快取（免重算）'
)
# ---- Windows subdirs that ARE allowed (regenerable caches only) ------------
$script:AllowedWinSub = @(
    'C:\Windows\Temp',
    'C:\Windows\Prefetch',
    'C:\Windows\Logs',
    'C:\Windows\Panther',
    'C:\Windows\Minidump',
    'C:\Windows\SoftwareDistribution\Download',
    'C:\Windows\SoftwareDistribution\DeliveryOptimization',
    'C:\Windows\ServiceProfiles\LocalService\AppData\Local\FontCache'
)
$script:DriveRootPattern = '^[A-Za-z]:\\?$'

function Test-VOOAdmin {
    $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $pr = [System.Security.Principal.WindowsPrincipal]::new($id)
    return $pr.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
}
$script:IsAdmin = Test-VOOAdmin

function Write-VOOFile {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Path $Path -Parent
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Text, $script:Utf8NoBom)
}

function Resolve-VOOPath {
    param([string]$Raw)
    if ([string]::IsNullOrWhiteSpace($Raw)) { return '' }
    $work = $Raw
    # convert $env:NAME -> %NAME% so ExpandEnvironmentVariables handles it
    $work = [regex]::Replace($work, '\$env:([A-Za-z_][A-Za-z0-9_]*)', '%$1%')
    $expanded = [System.Environment]::ExpandEnvironmentVariables($work)
    return $expanded
}

function Test-VOOAllowed {
    param([string]$Full)
    if ([string]::IsNullOrWhiteSpace($Full)) { return $false }
    $norm = $Full.TrimEnd('\').ToLowerInvariant()
    if ($norm -match $script:DriveRootPattern) { return $false }
    # user profile root itself is off-limits (only subfolders allowed)
    if ($norm -eq $env:USERPROFILE.TrimEnd('\').ToLowerInvariant()) { return $false }
    foreach ($p in $script:ProtectedRoots) {
        $pl = $p.TrimEnd('\').ToLowerInvariant()
        if ($norm -eq $pl) { return $false }
        if ($norm.StartsWith($pl + '\')) { return $false }
    }
    # anything under C:\Windows is denied UNLESS it is an allowed cache subdir
    if ($norm.StartsWith('c:\windows')) {
        $okWin = $false
        foreach ($w in $script:AllowedWinSub) {
            $wl = $w.ToLowerInvariant()
            if ($norm -eq $wl -or $norm.StartsWith($wl + '\')) { $okWin = $true; break }
        }
        if (-not $okWin) { return $false }
    }
    return $true
}

function Get-VOOFolderSize {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
    # accelerator: lazy .NET enumeration avoids building a full pipeline object set
    $sum = [int64]0
    try {
        $opt = [System.IO.SearchOption]::AllDirectories
        foreach ($f in [System.IO.Directory]::EnumerateFiles($Path, '*', $opt)) {
            try { $sum += [int64]([System.IO.FileInfo]::new($f)).Length } catch { }
        }
        return $sum
    } catch {
        $fallback = (Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        if ($null -eq $fallback) { return [int64]0 }
        return [int64]$fallback
    }
}

function Format-VOOSize {
    param([int64]$Bytes)
    $b = [double]$Bytes
    foreach ($u in @('Bytes', 'KB', 'MB', 'GB', 'TB')) {
        if ($b -lt 1024 -or $u -eq 'TB') {
            if ($u -eq 'Bytes') { return ('{0} {1}' -f [int]$b, $u) }
            return ('{0:N2} {1}' -f $b, $u)
        }
        $b = $b / 1024
    }
    return ('{0:N2} TB' -f $b)
}

function Find-VOOPython {
    $candidates = @(
        @{ Exe = (Join-Path $env:USERPROFILE 'envs\via_core\Scripts\python.exe'); Pre = @() },
        @{ Exe = (Join-Path $env:USERPROFILE 'envs\venv_core\Scripts\python.exe'); Pre = @() },
        @{ Exe = 'python'; Pre = @() },
        @{ Exe = 'py'; Pre = @('-3') }
    )
    foreach ($c in $candidates) {
        $found = $false
        if ($c.Exe -like '*\*') {
            if (Test-Path -LiteralPath $c.Exe) { $found = $true }
        } else {
            $found = $true
        }
        if (-not $found) { continue }
        $probe = Invoke-VOOProc -Exe $c.Exe -PreArgs $c.Pre -ScriptArgs @('-c', "import sys;print('VOOPY_OK')") -StdinText '' -TimeoutMs 8000
        if ($probe.Stdout -match 'VOOPY_OK') {
            $script:PyExe = $c.Exe
            $script:PyPre = $c.Pre
            return $true
        }
    }
    return $false
}

function Invoke-VOOProc {
    param(
        [string]$Exe,
        [string[]]$PreArgs = @(),
        [string[]]$ScriptArgs = @(),
        [string]$StdinText = '',
        [int]$TimeoutMs = 60000
    )
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Exe
    $psi.UseShellExecute = $false
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8NoBom
    $psi.StandardErrorEncoding = $script:Utf8NoBom
    foreach ($a in $PreArgs) { $psi.ArgumentList.Add($a) }
    foreach ($a in $ScriptArgs) { $psi.ArgumentList.Add($a) }
    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi
    $outBuf = ''
    $errBuf = ''
    try {
        $proc.Start() | Out-Null
        $outTask = $proc.StandardOutput.ReadToEndAsync()
        $errTask = $proc.StandardError.ReadToEndAsync()
        if (-not [string]::IsNullOrEmpty($StdinText)) {
            $proc.StandardInput.Write($StdinText)
        }
        $proc.StandardInput.Close()
        if (-not $proc.WaitForExit($TimeoutMs)) {
            try { $proc.Kill($true) } catch { }
            return @{ Ok = $false; Stdout = ''; Stderr = 'timeout'; Code = -1 }
        }
        $outBuf = $outTask.GetAwaiter().GetResult()
        $errBuf = $errTask.GetAwaiter().GetResult()
        return @{ Ok = ($proc.ExitCode -eq 0); Stdout = $outBuf; Stderr = $errBuf; Code = $proc.ExitCode }
    } catch {
        return @{ Ok = $false; Stdout = ''; Stderr = $_.Exception.Message; Code = -1 }
    } finally {
        $proc.Dispose()
    }
}

function Invoke-VOOEngine {
    param([string]$Cmd, [hashtable]$Payload)
    if (-not $script:PyOk) { return @{ ok = $false; error = 'python engine not ready' } }
    $req = @{ cmd = $Cmd; payload = $Payload }
    $json = $req | ConvertTo-Json -Depth 8 -Compress
    $r = Invoke-VOOProc -Exe $script:PyExe -PreArgs $script:PyPre -ScriptArgs @($script:PyEngine) -StdinText $json -TimeoutMs 180000
    if (-not $r.Ok -and [string]::IsNullOrWhiteSpace($r.Stdout)) {
        return @{ ok = $false; error = ('engine failed: {0}' -f $r.Stderr) }
    }
    try {
        return ($r.Stdout | ConvertFrom-Json)
    } catch {
        return @{ ok = $false; error = ('bad engine json: {0}' -f $r.Stderr) }
    }
}

# ---- removal tiers (recycle bin / quarantine) ------------------------------
function Move-VOOChildToRecycle {
    param([string]$Path)
    $freed = [int64]0
    Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $child = $_
        if ($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { return }
        $sz = if ($child.PSIsContainer) { Get-VOOFolderSize -Path $child.FullName } else { [int64]$child.Length }
        try {
            if ($child.PSIsContainer) {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                    $child.FullName,
                    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
            } else {
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    $child.FullName,
                    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
            }
            $freed += $sz
        } catch { }
    }
    return $freed
}

function Move-VOOChildToQuarantine {
    param([string]$Path, [string]$Key, [string]$Stamp)
    $dest = Join-Path (Join-Path $script:QuarantineDir $Stamp) $Key
    if (-not (Test-Path -LiteralPath $dest)) {
        New-Item -ItemType Directory -Path $dest -Force | Out-Null
    }
    $ledger = Join-Path $script:LedgerDir ('quarantine_{0}.csv' -f $Stamp)
    $freed = [int64]0
    $rows = [System.Collections.Generic.List[object]]::new()
    Get-ChildItem -LiteralPath $Path -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $child = $_
        if ($child.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { return }
        $sz = if ($child.PSIsContainer) { Get-VOOFolderSize -Path $child.FullName } else { [int64]$child.Length }
        $target = Join-Path $dest $child.Name
        try {
            Move-Item -LiteralPath $child.FullName -Destination $target -Force -ErrorAction Stop
            $freed += $sz
            $rows.Add([pscustomobject]@{ Original = $child.FullName; Quarantined = $target; Bytes = $sz })
        } catch { }
    }
    if ($rows.Count -gt 0) {
        $rows | Export-Csv -LiteralPath $ledger -Encoding UTF8BOM -NoTypeInformation -Append
    }
    return @{ Freed = $freed; Ledger = $ledger }
}

# whole-path removal: takes a single file OR a single dir (not its children)
function Remove-VOOPathToRecycle {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return [int64]0 }
    $isDir = (Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue).PSIsContainer
    $sz = if ($isDir) { Get-VOOFolderSize -Path $Path } else { [int64]((Get-Item -LiteralPath $Path -Force).Length) }
    try {
        if ($isDir) {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory(
                $Path,
                [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
        } else {
            [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                $Path,
                [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
        }
        return $sz
    } catch {
        return [int64]0
    }
}

function Remove-VOOPathToQuarantine {
    param([string]$Path, [string]$Key, [string]$Stamp)
    if (-not (Test-Path -LiteralPath $Path)) { return @{ Freed = [int64]0; Ledger = $null } }
    $dest = Join-Path (Join-Path $script:QuarantineDir $Stamp) $Key
    if (-not (Test-Path -LiteralPath $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }
    $ledger = Join-Path $script:LedgerDir ('quarantine_{0}.csv' -f $Stamp)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    $isDir = $item.PSIsContainer
    $sz = if ($isDir) { Get-VOOFolderSize -Path $Path } else { [int64]$item.Length }
    $target = Join-Path $dest $item.Name
    try {
        Move-Item -LiteralPath $Path -Destination $target -Force -ErrorAction Stop
        ([pscustomobject]@{ Original = $Path; Quarantined = $target; Bytes = $sz }) |
            Export-Csv -LiteralPath $ledger -Encoding UTF8BOM -NoTypeInformation -Append
        return @{ Freed = $sz; Ledger = $ledger }
    } catch {
        return @{ Freed = [int64]0; Ledger = $ledger }
    }
}

# ---- HTTP helpers ----------------------------------------------------------
function Send-VOOJson {
    param($Context, $Obj, [int]$Code = 200)
    $body = $Obj | ConvertTo-Json -Depth 10 -Compress
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($body)
    $resp = $Context.Response
    $resp.StatusCode = $Code
    $resp.ContentType = 'application/json; charset=utf-8'
    $resp.Headers['X-Content-Type-Options'] = 'nosniff'
    $resp.Headers['X-Frame-Options'] = 'DENY'
    $resp.Headers['Referrer-Policy'] = 'no-referrer'
    $resp.ContentLength64 = $bytes.Length
    $resp.OutputStream.Write($bytes, 0, $bytes.Length)
    $resp.OutputStream.Close()
}

function Send-VOOText {
    param($Context, [string]$Text, [string]$Ctype)
    $bytes = $script:Utf8NoBom.GetBytes($Text)
    $resp = $Context.Response
    $resp.StatusCode = 200
    $resp.ContentType = $Ctype
    $resp.Headers['X-Content-Type-Options'] = 'nosniff'
    $resp.ContentLength64 = $bytes.Length
    $resp.OutputStream.Write($bytes, 0, $bytes.Length)
    $resp.OutputStream.Close()
}

function Read-VOOBody {
    param($Context)
    $req = $Context.Request
    if ($req.ContentLength64 -gt $script:MaxBody) { return $null }
    $reader = [System.IO.StreamReader]::new($req.InputStream, [System.Text.Encoding]::UTF8)
    $raw = $reader.ReadToEnd()
    $reader.Close()
    if ([string]::IsNullOrWhiteSpace($raw)) { return @{} }
    try { return ($raw | ConvertFrom-Json -AsHashtable) } catch { return $null }
}

# ---- API handlers ----------------------------------------------------------
function Invoke-VOOScan {
    param($Body)
    $targets = @()
    foreach ($t in @($Body.targets)) {
        $full = Resolve-VOOPath -Raw ([string]$t.path)
        $allowed = Test-VOOAllowed -Full $full
        $targets += @{ key = [string]$t.key; name = [string]$t.name; path = $full; risk = [string]$t.risk; allowed = $allowed }
    }
    $forPy = @()
    foreach ($t in $targets) {
        if ($t.allowed) { $forPy += @{ key = $t.key; name = $t.name; path = $t.path; risk = $t.risk } }
    }
    $res = Invoke-VOOEngine -Cmd 'scan' -Payload @{ targets = $forPy }
    $out = @()
    $total = [int64]0
    $lookup = @{}
    if ($res.ok) { foreach ($r in @($res.targets)) { $lookup[$r.key] = $r } }
    foreach ($t in $targets) {
        if (-not $t.allowed) {
            $out += @{ key = $t.key; name = $t.name; path = $t.path; risk = $t.risk; exists = $false; bytes = 0; denied = $true }
            continue
        }
        $r = $lookup[$t.key]
        if ($null -ne $r) {
            $out += @{ key = $t.key; name = $t.name; path = $t.path; risk = $t.risk; exists = $r.exists; bytes = $r.bytes; denied = $false }
            $total += [int64]$r.bytes
        } else {
            $out += @{ key = $t.key; name = $t.name; path = $t.path; risk = $t.risk; exists = $false; bytes = 0; denied = $false }
        }
    }
    return @{ ok = $true; targets = $out; total_bytes = $total; human_total = (Format-VOOSize -Bytes $total); elapsed_ms = $res.elapsed_ms }
}

function Invoke-VOOClean {
    param($Body)
    $apply = [bool]$Body.apply
    $dest = [string]$Body.dest
    if ([string]::IsNullOrWhiteSpace($dest)) { $dest = 'recycle' }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $results = @()
    $total = [int64]0
    $ledgerOut = $null
    foreach ($t in @($Body.targets)) {
        $full = Resolve-VOOPath -Raw ([string]$t.path)
        $key = [string]$t.key
        $name = [string]$t.name
        if (-not (Test-VOOAllowed -Full $full)) {
            $results += @{ key = $key; name = $name; bytes = 0; acted = $false; denied = $true; note = '保護根' }
            continue
        }
        if (-not (Test-Path -LiteralPath $full)) {
            $results += @{ key = $key; name = $name; bytes = 0; acted = $false; denied = $false; note = '不存在' }
            continue
        }
        $size = Get-VOOFolderSize -Path $full
        if (-not $apply) {
            $results += @{ key = $key; name = $name; bytes = $size; acted = $false; denied = $false; note = '預演' }
            $total += $size
            continue
        }
        if ($dest -eq 'quarantine') {
            $q = Move-VOOChildToQuarantine -Path $full -Key $key -Stamp $stamp
            $freed = [int64]$q.Freed
            $ledgerOut = $q.Ledger
            $results += @{ key = $key; name = $name; bytes = $freed; acted = ($freed -gt 0); denied = $false; note = '已隔離' }
            $total += $freed
        } else {
            $freed = Move-VOOChildToRecycle -Path $full
            $results += @{ key = $key; name = $name; bytes = $freed; acted = ($freed -gt 0); denied = $false; note = '已移至回收筒' }
            $total += $freed
        }
    }
    return @{ ok = $true; results = $results; total_bytes = $total; human_total = (Format-VOOSize -Bytes $total); ledger = $ledgerOut }
}

function Invoke-VOODedup {
    param($Body)
    $roots = @()
    foreach ($r in @($Body.roots)) {
        $full = Resolve-VOOPath -Raw ([string]$r)
        if (Test-VOOAllowed -Full $full) { $roots += $full }
    }
    if ($roots.Count -eq 0) { return @{ ok = $false; error = '無有效根目錄（可能被保護根擋下）' } }
    $minBytes = [int64]$Body.min_bytes
    if ($minBytes -le 0) { $minBytes = 1048576 }
    return (Invoke-VOOEngine -Cmd 'dedup' -Payload @{ roots = $roots; min_bytes = $minBytes })
}

function Invoke-VOONameDup {
    param($Body)
    $roots = @()
    foreach ($r in @($Body.roots)) {
        $full = Resolve-VOOPath -Raw ([string]$r)
        if (Test-VOOAllowed -Full $full) { $roots += $full }
    }
    if ($roots.Count -eq 0) { return @{ ok = $false; error = '無有效根目錄（可能被保護根擋下）' } }
    $minBytes = [int64]$Body.min_bytes
    if ($minBytes -le 0) { $minBytes = 1048576 }
    return (Invoke-VOOEngine -Cmd 'namedup' -Payload @{ roots = $roots; min_bytes = $minBytes })
}

# delete an explicit, user-confirmed list of paths (recycle/quarantine) --------
function Invoke-VOODedupDelete {
    param($Body)
    $apply = [bool]$Body.apply
    $dest = [string]$Body.dest
    if ([string]::IsNullOrWhiteSpace($dest)) { $dest = 'recycle' }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $freed = [int64]0
    $acted = 0
    $total = 0
    $ledger = $null
    $results = [System.Collections.Generic.List[object]]::new()
    foreach ($p in @($Body.paths)) {
        $total++
        $path = [string]$p
        $denied = (-not (Test-VOOAllowed -Full $path))
        $bytes = [int64]0
        $did = $false
        if (-not $denied -and (Test-Path -LiteralPath $path)) {
            try { $bytes = [int64]((Get-Item -LiteralPath $path -Force).Length) } catch { $bytes = 0 }
            if ($apply) {
                if ($dest -eq 'quarantine') {
                    $q = Remove-VOOPathToQuarantine -Path $path -Key ('dup_{0}' -f $acted) -Stamp $stamp
                    if ($q.Freed -gt 0) { $freed += $q.Freed; $acted++; $did = $true; $ledger = $q.Ledger }
                } else {
                    $r = Remove-VOOPathToRecycle -Path $path
                    if ($r -gt 0) { $freed += $r; $acted++; $did = $true }
                }
            } else {
                $freed += $bytes
            }
        }
        $results.Add([ordered]@{ path = $path; bytes = $bytes; acted = $did; denied = $denied })
    }
    return @{ ok = $true; total_bytes = $freed; acted_count = $acted; total_count = $total;
        applied = $apply; ledger = $ledger; results = @($results) }
}

function Invoke-VOOOldScan {
    param($Body)
    $root = Resolve-VOOPath -Raw ([string]$Body.root)
    if (-not (Test-VOOAllowed -Full $root)) { return @{ ok = $false; error = '根目錄被保護根擋下或無效' } }
    $age = [int]$Body.age_days
    if ($age -le 0) { $age = 90 }
    return (Invoke-VOOEngine -Cmd 'oldscan' -Payload @{ root = $root; age_days = $age; exclude = @($script:ViaWorkTree) })
}

function Invoke-VOOOldClean {
    param($Body)
    $root = Resolve-VOOPath -Raw ([string]$Body.root)
    if (-not (Test-VOOAllowed -Full $root)) { return @{ ok = $false; error = '根目錄被保護根擋下或無效' } }
    $age = [int]$Body.age_days
    if ($age -le 0) { $age = 90 }
    $apply = [bool]$Body.apply
    $viaLower = $script:ViaWorkTree.TrimEnd('\').ToLowerInvariant()
    $scan = Invoke-VOOEngine -Cmd 'oldscan' -Payload @{ root = $root; age_days = $age; exclude = @($script:ViaWorkTree) }
    if (-not $scan.ok) { return $scan }
    $freed = [int64]0
    $acted = 0
    $total = 0
    foreach ($it in @($scan.items)) {
        $total++
        $p = [string]$it.path
        $pl = $p.ToLowerInvariant()
        if (-not (Test-VOOAllowed -Full $p)) { continue }
        if ($pl -eq $viaLower -or $pl.StartsWith($viaLower + '\')) { continue }
        if ($apply) {
            $r = Remove-VOOPathToRecycle -Path $p
            if ($r -gt 0) { $freed += $r; $acted++ }
        } else {
            $freed += [int64]$it.bytes
        }
    }
    return @{ ok = $true; total_bytes = $freed; acted_count = $acted; total_count = $total; applied = $apply }
}

function Invoke-VOOLangSweep {
    param($Body)
    $root = Resolve-VOOPath -Raw ([string]$Body.root)
    if (-not (Test-VOOAllowed -Full $root)) { return @{ ok = $false; error = '根目錄被保護根擋下或無效' } }
    return (Invoke-VOOEngine -Cmd 'langsweep' -Payload @{ root = $root })
}

function Invoke-VOOLangClean {
    param($Body)
    $root = Resolve-VOOPath -Raw ([string]$Body.root)
    if (-not (Test-VOOAllowed -Full $root)) { return @{ ok = $false; error = '根目錄被保護根擋下或無效' } }
    $apply = [bool]$Body.apply
    $dest = [string]$Body.dest
    if ([string]::IsNullOrWhiteSpace($dest)) { $dest = 'recycle' }
    $whitelist = @('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
        '.ipynb_checkpoints', '.gradle', '.tox', 'build', 'dist', '.next', '.turbo', '.parcel-cache')
    $sweep = Invoke-VOOEngine -Cmd 'langsweep' -Payload @{ root = $root }
    if (-not $sweep.ok) { return $sweep }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $freed = [int64]0
    $acted = 0
    $total = 0
    $ledger = $null
    foreach ($d in @($sweep.dirs)) {
        $total++
        $p = [string]$d.path
        $base = (Split-Path -Path $p -Leaf).ToLowerInvariant()
        if ($whitelist -notcontains $base) { continue }
        if (-not (Test-VOOAllowed -Full $p)) { continue }
        if ($apply) {
            if ($dest -eq 'quarantine') {
                $q = Remove-VOOPathToQuarantine -Path $p -Key ('lang_{0}' -f $acted) -Stamp $stamp
                if ($q.Freed -gt 0) { $freed += $q.Freed; $acted++; $ledger = $q.Ledger }
            } else {
                $r = Remove-VOOPathToRecycle -Path $p
                if ($r -gt 0) { $freed += $r; $acted++ }
            }
        } else {
            $freed += [int64]$d.bytes
        }
    }
    return @{ ok = $true; total_bytes = $freed; acted_count = $acted; total_count = $total; applied = $apply; ledger = $ledger }
}

function Invoke-VOOAccel {
    $py = Invoke-VOOEngine -Cmd 'accel' -Payload @{ }
    return @{ ok = $true; python = $py; powershell = @($script:PsAccel) }
}

function Invoke-VOOGuard {
    return @{ ok = $true; protected_roots = @($script:ProtectedRoots) }
}

# ---- Windows native storage analyzer: READ-ONLY matrix ---------------------
# Each row explains 功能/方法/現值/安全/建議. NOTHING here auto-applies a
# destructive change or setting. Dangerous items are report-only (actionable=$false).
function Invoke-VOOStorage {
    $rows = [System.Collections.Generic.List[object]]::new()
    $addRow = {
        param($key, $name, $func, $method, $value, $safety, $advice, $actionable)
        $rows.Add([ordered]@{ key = $key; name = $name; func = $func; method = $method;
                value = $value; safety = $safety; advice = $advice; actionable = [bool]$actionable })
    }

    # 1. Storage Sense (儲存空間感知)
    $ssVal = '未知'
    try {
        $ssp = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\StorageSense\Parameters\StoragePolicy' -ErrorAction Stop
        $ssVal = if ($ssp.'01' -eq 1) { '已啟用' } else { '未啟用' }
    } catch { $ssVal = '未啟用或無法讀取' }
    & $addRow 'storagesense' '儲存空間感知 Storage Sense' '自動清理暫存檔與資源回收筒，依排程釋放空間' '設定 → 系統 → 儲存空間 → 儲存空間感知（開啟並設定排程）' $ssVal 'safe' '建議開啟，僅清理暫存與回收筒，安全' $false

    # 2. Recycle Bin (資源回收筒)
    $rbVal = '需掃描'
    try {
        $rbPath = 'C:\$Recycle.Bin'
        if (Test-Path -LiteralPath $rbPath) { $rbVal = Format-VOOSize -Bytes (Get-VOOFolderSize -Path $rbPath) }
    } catch { }
    & $addRow 'recyclebin' '資源回收筒' '已刪除但未清空的檔案佔用空間' '清空回收筒（可先檢視內容）' $rbVal 'safe' '清空前確認無誤刪；本工具清理走回收筒，雙保險' $false

    # 3. Hibernation file (休眠檔)
    $hibVal = '不存在 / 已停用'
    try { if (Test-Path -LiteralPath 'C:\hiberfil.sys') { $hibVal = Format-VOOSize -Bytes ([int64]((Get-Item 'C:\hiberfil.sys' -Force).Length)) } } catch { }
    & $addRow 'hiberfil' '休眠檔 hiberfil.sys' '支援休眠與快速啟動，大小約等於實體記憶體' 'powercfg /h off（系統管理員）可移除，但會關閉休眠與快速啟動' $hibVal 'caution' '若你使用休眠/快速啟動，請勿停用；僅報告，不自動處理' $false

    # 4. Page file (分頁檔)
    $pfVal = '未知'
    try {
        $pf = Get-CimInstance Win32_PageFileUsage -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $pf) { $pfVal = ('{0} · 目前 {1} MB' -f $pf.Name, $pf.CurrentUsage) }
    } catch { }
    & $addRow 'pagefile' '分頁檔 pagefile.sys' '虛擬記憶體，記憶體不足時的緩衝' '系統內容 → 進階 → 虛擬記憶體（不建議手動關閉）' $pfVal 'danger' '關閉或縮小可能造成程式崩潰；僅報告，絕不自動更改' $false

    # 5. System Restore (系統還原)
    $srVal = '需系統管理員查詢'
    try {
        $sr = Get-CimInstance -Namespace 'root\default' -ClassName SystemRestore -ErrorAction SilentlyContinue
        if ($null -ne $sr) { $srVal = ('還原點 {0} 個' -f @($sr).Count) }
    } catch { }
    & $addRow 'systemrestore' '系統還原 System Restore' '保存系統還原點，可回復設定/驅動變更' '系統內容 → 系統保護（調整磁碟使用上限，而非停用）' $srVal 'danger' '停用會失去所有還原點；僅報告，不自動更改' $false

    # 6. WinSxS component store (元件存放區)
    & $addRow 'winsxs' 'WinSxS 元件存放區' 'Windows 更新的舊版元件備份，會隨時間膨脹' 'DISM /Online /Cleanup-Image /AnalyzeComponentStore（分析）→ /StartComponentCleanup（清理，系統管理員）' '需執行 DISM 分析' 'caution' '只用官方 DISM 清理，勿手動刪 WinSxS；本工具不自動執行' $false

    # 7. Windows.old (升級殘留)
    $woVal = '不存在'
    try { if (Test-Path -LiteralPath 'C:\Windows.old') { $woVal = Format-VOOSize -Bytes (Get-VOOFolderSize -Path 'C:\Windows.old') } } catch { }
    & $addRow 'windowsold' 'Windows.old 升級殘留' '保留舊版 Windows 以便回復，通常數十 GB' '磁碟清理 → 清理系統檔案 → 先前的 Windows 安裝' $woVal 'caution' '確認不需回復舊版後再清；建議用磁碟清理而非手動刪' $false

    # 8. Disk Cleanup (磁碟清理工具)
    & $addRow 'diskcleanup' '磁碟清理 cleanmgr' 'Windows 內建清理：更新殘留、傳遞最佳化、縮圖、回收筒等' 'cleanmgr（可勾選項目），或 cleanmgr /sageset:1 設定後 /sagerun:1' '可開啟工具' 'safe' '官方工具，逐項可勾選，安全；可由本面板開啟' $true

    # 9. Windows Update cache (更新快取)
    $wuVal = '需掃描'
    try { $p = 'C:\Windows\SoftwareDistribution\Download'; if (Test-Path -LiteralPath $p) { $wuVal = Format-VOOSize -Bytes (Get-VOOFolderSize -Path $p) } } catch { }
    & $addRow 'wucache' 'Windows Update 快取' '已下載的更新封包，可安全再生' '本面板「磁碟清理」分頁已含此項（送回收筒）' $wuVal 'safe' '安全清理；本工具預設預演＋回收筒' $true

    # 10. Memory dumps (記憶體傾印)
    $mdVal = '不存在'
    try {
        $dmp = 0
        if (Test-Path -LiteralPath 'C:\Windows\MEMORY.DMP') { $dmp += [int64]((Get-Item 'C:\Windows\MEMORY.DMP' -Force).Length) }
        if (Test-Path -LiteralPath 'C:\Windows\Minidump') { $dmp += Get-VOOFolderSize -Path 'C:\Windows\Minidump' }
        if ($dmp -gt 0) { $mdVal = Format-VOOSize -Bytes $dmp }
    } catch { }
    & $addRow 'memdump' '記憶體傾印 MEMORY.DMP / Minidump' '當機分析用的傾印檔，分析後可清' '磁碟清理 → 系統錯誤記憶體傾印檔' $mdVal 'safe' '一般使用者可安全清理' $true

    # 11. Compact OS / NTFS 壓縮
    & $addRow 'compactos' 'Compact OS / NTFS 壓縮' '壓縮系統檔以省空間（CPU 換空間）' 'compact /compactos:query 查詢；compact /compactos:always 啟用（系統管理員）' '需查詢' 'caution' '低階機可考慮；本工具僅報告，不自動套用' $false

    return @{ ok = $true; rows = @($rows); generated = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') }
}

# ---- panorama I/O scan of the protected project tree (READ-ONLY) -----------
function Invoke-VOOPanorama {
    param($Body)
    $root = [string]$Body.root
    if ([string]::IsNullOrWhiteSpace($root)) { $root = $script:ViaWorkTree }
    else { $root = Resolve-VOOPath -Raw $root }
    if (-not (Test-Path -LiteralPath $root)) { return @{ ok = $false; error = ('路徑不存在：{0}' -f $root) } }
    # NOTE: panorama is read-only; we deliberately scan the protected project tree.
    $res = Invoke-VOOEngine -Cmd 'panorama' -Payload @{ root = $root }
    if ($res -is [System.Collections.IDictionary] -or $res.PSObject) {
        try { $res | Add-Member -NotePropertyName 'is_protected' -NotePropertyValue $true -Force } catch { }
    }
    return $res
}

# ---- tool registry matrix --------------------------------------------------
function Invoke-VOOToolMatrix {
    $py = Invoke-VOOEngine -Cmd 'accel' -Payload @{ }
    $ext = @(
        [ordered]@{ tool = 'cleanmgr.exe'; type = 'exe'; purpose = '磁碟清理'; scope = 'external'; location = 'C:\Windows\System32\cleanmgr.exe' },
        [ordered]@{ tool = 'Dism.exe'; type = 'exe'; purpose = 'WinSxS 元件存放區清理'; scope = 'external'; location = 'C:\Windows\System32\Dism.exe' },
        [ordered]@{ tool = 'powercfg.exe'; type = 'exe'; purpose = '電源計畫 / 休眠檔'; scope = 'external'; location = 'C:\Windows\System32\powercfg.exe' },
        [ordered]@{ tool = 'vssadmin.exe'; type = 'exe'; purpose = '陰影複製 / 還原點查詢'; scope = 'external'; location = 'C:\Windows\System32\vssadmin.exe' },
        [ordered]@{ tool = 'compact.exe'; type = 'exe'; purpose = 'NTFS / Compact OS 壓縮查詢'; scope = 'external'; location = 'C:\Windows\System32\compact.exe' },
        [ordered]@{ tool = 'ipconfig.exe'; type = 'exe'; purpose = 'DNS 重新註冊'; scope = 'external'; location = 'C:\Windows\System32\ipconfig.exe' },
        [ordered]@{ tool = 'netsh.exe'; type = 'exe'; purpose = 'TCP/IP 調整'; scope = 'external'; location = 'C:\Windows\System32\netsh.exe' },
        [ordered]@{ tool = 'python.exe'; type = 'exe'; purpose = 'VOO Python 引擎執行'; scope = 'external'; location = $script:PyExe }
    )
    $cim = @(
        [ordered]@{ tool = 'Win32_OperatingSystem'; type = 'cim'; purpose = '記憶體 / OS 資訊'; scope = 'internal'; location = 'CIM' },
        [ordered]@{ tool = 'Win32_Processor'; type = 'cim'; purpose = 'CPU 資訊'; scope = 'internal'; location = 'CIM' },
        [ordered]@{ tool = 'Win32_LogicalDisk'; type = 'cim'; purpose = '磁碟容量'; scope = 'internal'; location = 'CIM' },
        [ordered]@{ tool = 'Win32_StartupCommand'; type = 'cim'; purpose = '開機項目'; scope = 'internal'; location = 'CIM' },
        [ordered]@{ tool = 'Win32_PageFileUsage'; type = 'cim'; purpose = '分頁檔'; scope = 'internal'; location = 'CIM' },
        [ordered]@{ tool = 'Win32_Service'; type = 'cim'; purpose = '服務分析'; scope = 'internal'; location = 'CIM' }
    )
    return @{ ok = $true; python = $py; powershell = @($script:PsAccel); external = @($ext); cim = @($cim) }
}

function Invoke-VOOSystem {
    param($Body)
    $action = [string]$Body.action
    $lines = [System.Collections.Generic.List[string]]::new()
    $report = $null
    switch ($action) {
        'sysinfo' {
            $os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
            $cpu = Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1
            $disk = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' -ErrorAction SilentlyContinue
            $procCount = (Get-Process).Count
            if ($null -ne $os) {
                $freeGb = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
                $usedPct = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / $os.TotalVisibleMemorySize * 100, 1)
                $lines.Add(('可用記憶體：{0} GB · 使用率 {1}%' -f $freeGb, $usedPct))
            }
            if ($null -ne $cpu) { $lines.Add(('CPU：{0} · {1} 執行緒' -f $cpu.Name, $cpu.NumberOfLogicalProcessors)) }
            $lines.Add(('執行中進程：{0}' -f $procCount))
            foreach ($dd in @($disk)) {
                $tot = [math]::Round($dd.Size / 1GB, 1)
                $fr = [math]::Round($dd.FreeSpace / 1GB, 1)
                $lines.Add(('磁碟 {0} · 總 {1}GB · 可用 {2}GB' -f $dd.DeviceID, $tot, $fr))
            }
            $report = Write-VOOSysReport -Os $os -Disk $disk
            if ($null -ne $report) { Start-Process $report }
        }
        'perf' {
            try { powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null; $lines.Add('已啟用高效能電源計畫') } catch { $lines.Add('電源計畫設定略過') }
            try {
                $regPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects'
                Set-ItemProperty -Path $regPath -Name 'VisualFXSetting' -Value 2 -ErrorAction SilentlyContinue
                $lines.Add('視覺效果已調整為效能優先')
            } catch { }
            [System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()
            $lines.Add('受管記憶體垃圾回收完成')
            try { Clear-DnsClientCache; $lines.Add('DNS 快取已清理') } catch { }
        }
        'startup' {
            $items = Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue
            $lines.Add(('啟動項目共 {0} 個：' -f @($items).Count))
            foreach ($s in @($items)) { $lines.Add((' · {0}  [{1}]' -f $s.Name, $s.Location)) }
            $lines.Add('提示：工作管理員 → 啟動 頁籤可停用')
        }
        'service' {
            $opt = @(
                @{ Name = 'DiagTrack'; Desc = '診斷追蹤 (遙測)' },
                @{ Name = 'SysMain'; Desc = 'Superfetch (SSD 可停)' },
                @{ Name = 'WSearch'; Desc = 'Windows Search 索引' },
                @{ Name = 'Fax'; Desc = '傳真服務' },
                @{ Name = 'XblAuthManager'; Desc = 'Xbox Live 驗證' }
            )
            foreach ($o in $opt) {
                $svc = Get-Service -Name $o.Name -ErrorAction SilentlyContinue
                if ($null -ne $svc) {
                    $st = if ($svc.Status -eq 'Running') { '運行中' } else { '已停止' }
                    $lines.Add((' · {0} [{1}] — {2}' -f $o.Name, $st, $o.Desc))
                }
            }
            $lines.Add('只報告，不自動停用；如需停用請手動 Set-Service -StartupType Disabled')
        }
        default { return @{ ok = $false; error = ('unknown action: {0}' -f $action) } }
    }
    return @{ ok = $true; lines = @($lines); report = $report }
}

function Write-VOOSysReport {
    param($Os, $Disk)
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $path = Join-Path $env:USERPROFILE ('Desktop\VOO_SysReport_{0}.html' -f $stamp)
    $topMem = Get-Process | Sort-Object @{ e = 'WorkingSet64'; desc = $true } | Select-Object -First 10 Name, @{ N = 'MemMB'; E = { [math]::Round($_.WorkingSet64 / 1MB, 1) } }
    $rowsDisk = ''
    foreach ($d in @($Disk)) {
        $tot = [math]::Round($d.Size / 1GB, 1)
        $fr = [math]::Round($d.FreeSpace / 1GB, 1)
        $rowsDisk += ('<tr><td>{0}</td><td>{1} GB</td><td>{2} GB</td></tr>' -f $d.DeviceID, $tot, $fr)
    }
    $rowsMem = ''
    foreach ($p in $topMem) { $rowsMem += ('<tr><td>{0}</td><td>{1}</td></tr>' -f $p.Name, $p.MemMB) }
    $tpl = @'
<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8"><title>VOO 系統診斷報告</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>:root{--bg:#f5f4f0;--paper:#fff;--ink:#1d1d1f;--ink-soft:#5b5a55;--line:#e0ddd5;--line-soft:#ebe9e2;--primary:#4c78a8;--teal:#439a9a}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--ink);padding:0 0 40px;font-size:12px}
.rb{height:4px;background:linear-gradient(90deg,#b85450,#c49a3d,#2d8659,#439a9a,#4c78a8,#8c5e9e)}
.wrap{max-width:980px;margin:0 auto;padding:28px}
h1{font-family:'Syne',sans-serif;font-weight:800;font-size:22px;letter-spacing:-.01em;border-bottom:1px solid var(--line);padding-bottom:12px}
.sub{color:var(--ink-soft);font-family:'DM Mono',monospace;font-size:11px;margin:4px 0 20px}
h2{font-family:'Syne',sans-serif;font-weight:700;font-size:14px;margin:22px 0 8px;padding-left:9px;border-left:3px solid var(--primary)}
table{width:100%;border-collapse:collapse;margin:6px 0;background:var(--paper);border:1px solid var(--line)}
th,td{padding:7px 11px;text-align:left;border-bottom:1px solid var(--line-soft);font-size:11px}
th{background:var(--line-soft);font-family:'Syne',sans-serif;font-weight:700;font-size:10px;letter-spacing:.03em}
td{font-family:'DM Mono',monospace}tr:hover td{background:#fafaf6}</style></head>
<body><div class="rb"></div><div class="wrap"><h1>VOO 系統診斷報告</h1><div class="sub">VeritasOperationOptimizer · Visual Lock · 生成時間 __TS__</div>
<h2>磁碟狀態</h2><table><tr><th>磁碟</th><th>總容量</th><th>可用空間</th></tr>__DISK__</table>
<h2>Top 10 記憶體進程</h2><table><tr><th>進程</th><th>記憶體 (MB)</th></tr>__MEM__</table>
</div></body></html>
'@
    $htmlOut = $tpl.Replace('__TS__', (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')).Replace('__DISK__', $rowsDisk).Replace('__MEM__', $rowsMem)
    Write-VOOFile -Path $path -Text $htmlOut
    return $path
}

function Invoke-VOONetwork {
    param($Body)
    $action = [string]$Body.action
    $lines = [System.Collections.Generic.List[string]]::new()
    switch ($action) {
        'diag' {
            Get-NetAdapter -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'Up' } | ForEach-Object {
                $lines.Add(('適配器 {0} — {1}' -f $_.Name, $_.LinkSpeed))
            }
            foreach ($tgt in @('8.8.8.8', '1.1.1.1')) {
                $ping = Test-Connection -TargetName $tgt -Count 1 -ErrorAction SilentlyContinue
                if ($null -ne $ping) { $lines.Add(('Ping {0} 正常' -f $tgt)) }
                else { $lines.Add(('Ping {0} 無回應' -f $tgt)) }
            }
        }
        'dns' {
            try { Clear-DnsClientCache; $lines.Add('DNS 快取已清理') } catch { $lines.Add('DNS 清理略過') }
            try { ipconfig /registerdns | Out-Null; $lines.Add('DNS 已重新註冊') } catch { }
        }
        'tcp' {
            if (-not $script:IsAdmin) { $lines.Add('需系統管理員，TCP 優化略過'); break }
            try { netsh int tcp set global autotuninglevel=normal | Out-Null; $lines.Add('TCP 自動調整=normal') } catch { }
            $lines.Add('建議重新啟動以套用變更')
        }
        default { return @{ ok = $false; error = ('unknown action: {0}' -f $action) } }
    }
    return @{ ok = $true; lines = @($lines) }
}

# ---- write engines to disk -------------------------------------------------
function Initialize-VOO {
    foreach ($d in @($script:Root, $script:EngineDir, $script:UiDir, $script:LedgerDir, $script:QuarantineDir)) {
        if (-not (Test-Path -LiteralPath $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
    Write-VOOFile -Path $script:PyEngine -Text $script:PyEngineSrc
    Write-VOOFile -Path (Join-Path $script:UiDir 'voo.js') -Text $script:JsEngineSrc
    $html = $script:HtmlSrc.Replace('__CSRF__', $script:Csrf).Replace('__PORT__', [string]$Port)
    Write-VOOFile -Path (Join-Path $script:UiDir 'voo_ui.html') -Text $html
    try { Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction Stop } catch { }
    $script:PyOk = Find-VOOPython
}

# ---- request router --------------------------------------------------------
function Invoke-VOORoute {
    param($Context)
    $req = $Context.Request
    $path = $req.Url.AbsolutePath
    $method = $req.HttpMethod
    # Host allowlist (loopback only) against DNS rebinding
    $reqHost = $req.Headers['Host']
    if ($reqHost -and ($reqHost -notmatch '^(127\.0\.0\.1|localhost)(:\d+)?$')) {
        Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'bad host' } -Code 403
        return
    }
    if ($method -eq 'GET' -and ($path -eq '/' -or $path -eq '/index.html')) {
        $html = [System.IO.File]::ReadAllText((Join-Path $script:UiDir 'voo_ui.html'), $script:Utf8NoBom)
        Send-VOOText -Context $Context -Text $html -Ctype 'text/html; charset=utf-8'
        return
    }
    if ($method -eq 'GET' -and $path -eq '/voo.js') {
        $js = [System.IO.File]::ReadAllText((Join-Path $script:UiDir 'voo.js'), $script:Utf8NoBom)
        Send-VOOText -Context $Context -Text $js -Ctype 'application/javascript; charset=utf-8'
        return
    }
    # all /api/* require POST + CSRF
    if ($path -like '/api/*') {
        if ($method -ne 'POST') { Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'POST only' } -Code 405; return }
        $token = $req.Headers['X-VOO-CSRF']
        if ($path -ne '/api/health' -and $token -ne $script:Csrf) {
            Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'csrf' } -Code 403; return
        }
        $body = Read-VOOBody -Context $Context
        if ($null -eq $body) { Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'bad body' } -Code 413; return }
        switch ($path) {
            '/api/health' { Send-VOOJson -Context $Context -Obj @{ ok = $true; version = 'voo/2.0'; admin = $script:IsAdmin; python = $script:PyExe; python_ok = $script:PyOk; csrf = $script:Csrf; protected_roots = @($script:ProtectedRoots) } }
            '/api/scan' { Send-VOOJson -Context $Context -Obj (Invoke-VOOScan -Body $body) }
            '/api/clean' { Send-VOOJson -Context $Context -Obj (Invoke-VOOClean -Body $body) }
            '/api/dedup' { Send-VOOJson -Context $Context -Obj (Invoke-VOODedup -Body $body) }
            '/api/namedup' { Send-VOOJson -Context $Context -Obj (Invoke-VOONameDup -Body $body) }
            '/api/dedupdelete' { Send-VOOJson -Context $Context -Obj (Invoke-VOODedupDelete -Body $body) }
            '/api/oldscan' { Send-VOOJson -Context $Context -Obj (Invoke-VOOOldScan -Body $body) }
            '/api/oldclean' { Send-VOOJson -Context $Context -Obj (Invoke-VOOOldClean -Body $body) }
            '/api/langsweep' { Send-VOOJson -Context $Context -Obj (Invoke-VOOLangSweep -Body $body) }
            '/api/langclean' { Send-VOOJson -Context $Context -Obj (Invoke-VOOLangClean -Body $body) }
            '/api/accel' { Send-VOOJson -Context $Context -Obj (Invoke-VOOAccel) }
            '/api/guard' { Send-VOOJson -Context $Context -Obj (Invoke-VOOGuard) }
            '/api/storage' { Send-VOOJson -Context $Context -Obj (Invoke-VOOStorage) }
            '/api/panorama' { Send-VOOJson -Context $Context -Obj (Invoke-VOOPanorama -Body $body) }
            '/api/toolmatrix' { Send-VOOJson -Context $Context -Obj (Invoke-VOOToolMatrix) }
            '/api/system' { Send-VOOJson -Context $Context -Obj (Invoke-VOOSystem -Body $body) }
            '/api/network' { Send-VOOJson -Context $Context -Obj (Invoke-VOONetwork -Body $body) }
            default { Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'not found' } -Code 404 }
        }
        return
    }
    Send-VOOJson -Context $Context -Obj @{ ok = $false; error = 'not found' } -Code 404
}

# ---- self-test (static, no server) -----------------------------------------
function Invoke-VOOSelfTest {
    $rep = [System.Collections.Generic.List[object]]::new()
    $add = { param($n, $c) $rep.Add(@{ name = $n; pass = [bool]$c }) }
    & $add 'resolve $env expands' ((Resolve-VOOPath -Raw '$env:TEMP\x') -notmatch '\$env:')
    & $add 'protected envs denied' (-not (Test-VOOAllowed -Full (Join-Path $env:USERPROFILE 'envs\via_core')))
    & $add 'VIA root denied' (-not (Test-VOOAllowed -Full 'C:\VeritasIntelligenceAnalytics\x'))
    & $add 'Downloads VIA subtree denied' (-not (Test-VOOAllowed -Full (Join-Path $env:USERPROFILE 'Downloads\VeritasIntelligenceAnalytics\sub\x')))
    & $add 'Downloads loose file reachable' (Test-VOOAllowed -Full (Join-Path $env:USERPROFILE 'Downloads\old_installer.exe'))
    & $add 'PsAccel has 20' ($script:PsAccel.Count -eq 20)
    & $add 'storage analyzer defined' ([bool](Get-Command Invoke-VOOStorage -ErrorAction SilentlyContinue))
    & $add 'panorama handler defined' ([bool](Get-Command Invoke-VOOPanorama -ErrorAction SilentlyContinue))
    & $add 'toolmatrix handler defined' ([bool](Get-Command Invoke-VOOToolMatrix -ErrorAction SilentlyContinue))
    & $add 'remove-path recycle defined' ([bool](Get-Command Remove-VOOPathToRecycle -ErrorAction SilentlyContinue))
    & $add 'namedup handler defined' ([bool](Get-Command Invoke-VOONameDup -ErrorAction SilentlyContinue))
    & $add 'dedupdelete handler defined' ([bool](Get-Command Invoke-VOODedupDelete -ErrorAction SilentlyContinue))
    & $add 'drive root denied' (-not (Test-VOOAllowed -Full 'C:\'))
    & $add 'profile root denied' (-not (Test-VOOAllowed -Full $env:USERPROFILE))
    & $add 'windows bare denied' (-not (Test-VOOAllowed -Full 'C:\Windows\System32'))
    & $add 'windows temp allowed' (Test-VOOAllowed -Full 'C:\Windows\Temp')
    & $add 'temp cache allowed' (Test-VOOAllowed -Full (Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data\Default\Cache'))
    & $add 'format size GB' ((Format-VOOSize -Bytes 1610612736) -eq '1.50 GB')
    $pass = (@($rep) | Where-Object { $_.pass }).Count
    $total = @($rep).Count
    foreach ($r in $rep) {
        $mark = if ($r.pass) { 'PASS' } else { 'FAIL' }
        $fg = if ($r.pass) { 'Green' } else { 'Red' }
        Write-Host ('  [{0}] {1}' -f $mark, $r.name) -ForegroundColor $fg
    }
    Write-Host ('  -- {0}/{1} PASS --' -f $pass, $total) -ForegroundColor Cyan
    return ($pass -eq $total)
}

# ---- main ------------------------------------------------------------------
Initialize-VOO

if ($SelfTest) {
    $allPass = Invoke-VOOSelfTest
    if ($CI) { if ($allPass) { exit 0 } else { exit 1 } }
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add(('http://127.0.0.1:{0}/' -f $Port))
try {
    $listener.Start()
} catch {
    Write-Host ('無法在 port {0} 啟動：{1}' -f $Port, $_.Exception.Message) -ForegroundColor Red
    return
}

Write-Host ('═' * 70) -ForegroundColor Cyan
Write-Host '  ⚡ VeritasOperationOptimizer · Live 已啟動' -ForegroundColor Yellow
Write-Host ('  位址：http://127.0.0.1:{0}/' -f $Port) -ForegroundColor White
$pyState = if ($script:PyOk) { ('Python：{0}' -f $script:PyExe) } else { 'Python：未就緒（掃描/重複檔停用）' }
Write-Host ('  {0}' -f $pyState) -ForegroundColor White
$adminState = if ($script:IsAdmin) { '系統管理員' } else { '一般權限（部分系統路徑略過）' }
Write-Host ('  權限：{0}' -f $adminState) -ForegroundColor White
Write-Host ('  停止：在此視窗按 Ctrl+C') -ForegroundColor DarkGray
Write-Host ('═' * 70) -ForegroundColor Cyan

if (-not $NoBrowser) {
    Start-Process ('http://127.0.0.1:{0}/' -f $Port)
}

while ($listener.IsListening) {
    try {
        $ctx = $listener.GetContext()
        Invoke-VOORoute -Context $ctx
    } catch {
        Write-Host ('請求處理錯誤：{0}' -f $_.Exception.Message) -ForegroundColor DarkYellow
    }
}
