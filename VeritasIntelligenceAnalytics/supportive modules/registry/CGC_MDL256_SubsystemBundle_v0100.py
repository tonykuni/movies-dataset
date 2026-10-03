#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL256_SubsystemBundle v0100 — 子系統下載包:測過的指令 · 帶編號與版本 · 下載到 PC 實測

操作員 2026-10-03:「將更新測試過的指令 編號 版本 下載到 C:\\Users\\tonyk\\OneDrive\\Documents\\VeritasIntelligenceAnalytics\\via_01_vdf」
「vcgc 全部成功收尾 下載到 …\\via_00_vcgc」「下載到 pc 方便實測」。

冊 VIA_SubsystemBundle_SSOT_v0100.json 每一包記:目標資料夾(操作員 PC)· 檔案清單(執行期閉包:實跑自測 / 整合測試時以
sys.addaudithook 記下真被開的檔,pyc 回推原始檔)· 實測指令。本支只做:
  build <包> [--out 夾 | --target] [--no-zip]
                          依冊照 VIA 原佈局複製到 <out>/<包>/VeritasIntelligenceAnalytics/…(鎖冊的 repo 相對路徑在包內照樣解得到),
                          寫 MANIFEST.json(每檔:中央編號 · 版本 · sha256 · 位元組)與 README_實測.txt,再打 zip。
  verify <夾>             逐檔重算 sha256 對 MANIFEST(解壓後在 PC 上也能跑同一支)。
  list                    冊上幾包 · 各幾檔 · 缺檔。
包裡的網路 / 加速器只放鎖版(操作員令「鎖定這兩個 其他刪除」):橋往上找 supportive modules 時先找到包內那一份,不會撞到外層舊副本。
不連網;不改被打包的檔;不碰 TA-Lib;不代設同意閘。只收 VCGC 呼叫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent                 # supportive modules/registry
VIA = HERE.parents[1]                                  # VeritasIntelligenceAnalytics
ENGINE = Path(__file__).stem
BOOK = HERE / "VIA_SubsystemBundle_SSOT_v0100.json"
NUMBOOKS = HERE / "VIA_NumberBooks"
DEFAULT_OUT = VIA / "VIA_Reports" / "bundles"


def load_book(path: Path = BOOK) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def number_index() -> dict:
    """source(VIA 相對路徑)→ 中央編號;同檔多冊(MDL / ENG / TOOL …)全列。"""
    idx: dict = {}
    for book in sorted(NUMBOOKS.glob("VIA_NumberBook_*_v*.jsonl")):
        for line in book.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            src = str(row.get("source") or "")
            if src and row.get("code"):
                idx.setdefault(src, []).append(row["code"])
    return idx


def version_of(rel: str) -> str:
    m = re.search(r"_v(\d{4})\.\w+$", rel) or re.search(r"_v(\d+\.\d+\.\d+)\.\w+$", rel)
    return "v" + m.group(1) if m else "本體(無版號)"


def manifest(name: str, spec: dict, idx: dict | None = None) -> dict:
    idx = number_index() if idx is None else idx
    rows, missing = [], []
    for rel in spec["files"]:
        p = VIA / rel
        if not p.is_file():
            missing.append(rel)
            continue
        rows.append({"path": "VeritasIntelligenceAnalytics/" + rel, "codes": idx.get(rel, []), "version": version_of(rel),
                     "sha256": sha256(p), "bytes": p.stat().st_size})
    return {"schema": "VIA.SubsystemBundle.Manifest.v1", "bundle": name, "target": spec["target"], "built_at":
            datetime.now(timezone.utc).isoformat(timespec="seconds"), "builder": ENGINE, "files": rows, "missing": missing,
            "numbered": sum(1 for r in rows if r["codes"]), "count": len(rows)}


def readme(name: str, spec: dict, man: dict) -> str:
    lines = [f"{name} 下載包 · {man['built_at']} · {man['count']} 檔(有中央編號 {man['numbered']})· 建包 {ENGINE}",
             "", f"1. 解壓到:{spec['target']}", "   (資料夾裡會有 VeritasIntelligenceAnalytics\\…,保持這個層次,不要攤平)",
             "", "2. 開 PowerShell,進到包內的 VeritasIntelligenceAnalytics:",
             f"   cd \"{spec['target']}\\VeritasIntelligenceAnalytics\"", "",
             "3. 先驗包(逐檔 sha256 對 MANIFEST;不合就停):",
             f"   py -3 \"supportive modules\\registry\\{ENGINE}.py\" verify .. ", "", "4. 實測指令(照順序):"]
    lines += ["   " + c for c in spec.get("commands") or []]
    lines += ["", "py 不行就把 py -3 換成 python。", "連網實測要你自己在本視窗開雙閘(AI 永不代設):",
              "   $env:VIA_NET_CONSENT='YES'", "   $env:VIA_SCRAPE_CONSENT='<你的同意值>'"]
    return "\n".join(lines) + "\n"


class BundleRefused(Exception):
    pass


def build(name: str, out: Path | None = None, make_zip: bool = True) -> dict:
    """照冊複製到 <out>/<包>/…。目標夾已在:有 MANIFEST(前一版包)= 只覆蓋清單檔、刪舊清單有新清單沒有的檔;
    沒有 MANIFEST(不是包)= 拒跑(不砍操作員的資料)。"""
    book = load_book()
    spec = book["bundles"][name]
    out = Path(out or DEFAULT_OUT)
    root = out / name
    old_files: list = []
    if root.exists() and any(root.iterdir()):
        if not (root / "MANIFEST.json").is_file():
            raise BundleRefused(f"{root} 已存在且不是下載包(沒有 MANIFEST.json)—— 不覆蓋、不刪;換 --out 或先自己清空")
        old_files = [r["path"] for r in json.loads((root / "MANIFEST.json").read_text(encoding="utf-8")).get("files") or []]
    man = manifest(name, spec)
    keep = {r["path"] for r in man["files"]}
    removed = []
    for rel in old_files:
        if rel not in keep and (root / rel).is_file():
            (root / rel).unlink()
            removed.append(rel)
    for r in man["files"]:
        dst = root / r["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(VIA.parent / r["path"], dst)
    (root / "MANIFEST.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (root / "README_實測.txt").write_text(readme(name, spec, man), encoding="utf-8")
    man["removed_old"] = removed
    man["dir"] = str(root)
    if make_zip:
        zp = out / f"{name}.zip"
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(root.rglob("*")):
                if f.is_file():
                    z.write(f, Path(name) / f.relative_to(root))
        man["zip"], man["zip_bytes"] = str(zp), zp.stat().st_size
    return man


def verify(folder: Path) -> dict:
    folder = Path(folder)
    if not (folder / "MANIFEST.json").is_file() and (folder.parent / "MANIFEST.json").is_file():
        folder = folder.parent
    man = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = [r["path"] for r in man["files"] if not (folder / r["path"]).is_file() or sha256(folder / r["path"]) != r["sha256"]]
    return {"bundle": man["bundle"], "count": len(man["files"]), "bad": bad, "ok": not bad}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    verb = args[0] if args else "list"
    if verb == "verify":                                    # PC 上解壓後直接跑:不需要 VCGC(只讀、只算雜湊)
        target = Path(args[1]) if len(args) > 1 else Path.cwd()
        r = verify(target)
        print(f"[{ENGINE} verify] {r['bundle']} · {r['count'] - len(r['bad'])}/{r['count']} 檔 sha256 相符" +
              ("" if r["ok"] else " · 不合:" + " · ".join(r["bad"][:5])))
        return 0 if r["ok"] else 1
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(f"[{ENGINE}] 拒絕。只能經 via-vcgc(verify 除外)。")
        return 2
    book = load_book()
    if verb == "list":
        for n, s in book["bundles"].items():
            miss = [f for f in s["files"] if not (VIA / f).is_file()]
            print(f"  {n:12} {len(s['files']):4} 檔 · 缺 {len(miss)} · → {s['target']}")
        return 0
    if verb == "build":
        if len(args) < 2 or args[1] not in book["bundles"]:
            print(f"[拒跑] {ENGINE}:build 要給包名(冊上:{' · '.join(book['bundles'])})")
            return 2
        out = Path(args[args.index("--out") + 1]) if "--out" in args else None
        if "--target" in args:                              # 冊上登記的操作員 PC 目標夾(在 PC 上跑)
            out = Path(book["bundles"][args[1]]["target"]).parent
        try:
            m = build(args[1], out, make_zip="--no-zip" not in args)
        except BundleRefused as e:
            print(f"[拒跑] {ENGINE}:{e}")
            return 2
        z = f" · zip {m['zip_bytes']:,} B → {m['zip']}" if m.get("zip") else ""
        print(f"[{ENGINE} build] {m['bundle']} · {m['count']} 檔(有編號 {m['numbered']})· 缺 {len(m['missing'])} · 舊檔清 {len(m['removed_old'])} → {m['dir']}{z}")
        for x in m["missing"]:
            print(f"   [缺] {x}")
        return 0 if not m["missing"] else 1
    print(f"[拒跑] {ENGINE}:未知動詞 '{verb}'(已知:list · build · verify · --selftest)")
    return 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 自測(子系統下載包:冊 · 清單 · 編號 · sha256 · zip)===")
    book = load_book()
    chk("① 冊:每包有目標資料夾 · 檔案清單 · 實測指令", all(s.get("target") and s.get("files") and s.get("commands") for s in book["bundles"].values()),
        list(book["bundles"]))
    with tempfile.TemporaryDirectory() as tmp:
        name = next(iter(book["bundles"]))
        m = build(name, Path(tmp))
        chk("② build:清單檔全在 · 照 VIA 佈局落 <包>/VeritasIntelligenceAnalytics/… · zip 有", not m["missing"] and Path(m["zip"]).is_file()
            and (Path(tmp) / name / "VeritasIntelligenceAnalytics").is_dir(), (m["count"], len(m["missing"])))
        chk("③ 每檔有版本 · sha256;中央編號有登的帶上", all(r["version"] and len(r["sha256"]) == 64 for r in m["files"]) and m["numbered"] > 0,
            f"有編號 {m['numbered']}/{m['count']}")
        v = verify(Path(tmp) / name)
        tgt = Path(tmp) / name / m["files"][0]["path"]
        tgt.write_bytes(tgt.read_bytes() + b"\n#x")
        v2 = verify(Path(tmp) / name)
        chk("④ verify:原包全相符;改一個位元組 → 點名不合(負控)", v["ok"] and not v2["ok"] and v2["bad"] == [m["files"][0]["path"]])
        with zipfile.ZipFile(m["zip"]) as z:
            names = z.namelist()
        (Path(tmp) / "userdata" / name).mkdir(parents=True)
        (Path(tmp) / "userdata" / name / "my.parquet").write_bytes(b"x")
        try:
            build(name, Path(tmp) / "userdata", make_zip=False)
            refused = False
        except BundleRefused:
            refused = True
        m2 = build(name, Path(tmp), make_zip=False)
        chk("⑤b 目標夾不是包 → 拒跑不刪(操作員資料在);前一版包 → 原地更新不打 zip", refused and (Path(tmp) / "userdata" / name / "my.parquet").is_file()
            and m2["count"] == m["count"] and "zip" not in m2)
        chk("⑤ zip 內含 MANIFEST.json · README_實測.txt · 全部檔", f"{name}/MANIFEST.json" in names and f"{name}/README_實測.txt" in names
            and len(names) == m["count"] + 2, len(names))
    vdf = book["bundles"].get("via_01_vdf", {}).get("files", [])
    locked = json.loads((HERE / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
    net = locked["network"]["path"].split("VeritasIntelligenceAnalytics/", 1)[-1]
    acc = locked["accelerator"]["path"].split("VeritasIntelligenceAnalytics/", 1)[-1]
    others = [f for f in vdf if re.search(r"VeritasAegisNexus_v|VeritasCeleritas_v", f) and f not in (net, acc)
              and not f.endswith("VeritasAegisNexus_v1651.py")]
    chk("⑥ via_01_vdf 包內網路 / 加速器只有鎖版(v1652 + 其本體 v1651 · v1141)", net in vdf and acc in vdf and not others, others)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"  [計] {ENGINE} {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
