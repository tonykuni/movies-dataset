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
