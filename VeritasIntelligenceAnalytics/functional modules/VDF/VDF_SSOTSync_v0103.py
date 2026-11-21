#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_SSOTSync v0103 — 薄尾(v0100–v0102 一字不動):VDF 自己發號、自己定案,不再等 VCGC 核號

操作員 2026-11-21 裁定:「同意 VDF 也自己發號 你決定」(前一則:VRN 自己發號;「他們全都是獨立的系統,他們當然可以擁有自己的一套資料」)。
v0100 的設計是「VDF-<類>-#### 只是內部追蹤號,ssot_id 由 VCGC 中央編號核發,核到才轉已確認」;本版改成:
  · VDF-<類>-#### 就是 VDF 自己的定案號。待核狀態(暫編 / 內容更新 · 待 VCGC 重檢 / 衝突 · 待人判)一律轉「已確認(VDF 自發)」,號不變。
  · 已由 VCGC 核發的條目(「已確認(VCGC)」+ ssot_id)原樣保留 —— 那是歷史,不改寫;之後內容有變照樣升 semver,但直接由 VDF 自己定案。
  · contract/VDF_NUMBER_REQUEST_latest.json 照寫(ActivateVDF 查它在不在),但請號清單空、規則改寫成 VDF 自己定案;不再讀 VCGC 核發冊。
  · 狀態檔 contract/VDF_NUMBER_STATE_latest.json 不寫本機絕對路徑。
  · VDF 自發條目(沒有 ssot_id)內容有變也升 semver(v0100 只對有中央號的升;PR #705 Codex P2)。
register 的收割(v0101 / v0102 的 harvest)、登記鍵、號碼規則(鍵不變號不變 · 只增不減 · 內容有變才出新版冊)全部照舊。
ActivateVDF 每輪呼叫尾版的 sync → 走本版。v0100 本體函式不動,前版自測照舊。
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

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SSOTSync"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
SELF_STATUS = "已確認(VDF 自發)"
PENDING_PREFIX = ("暫編", "內容更新", "衝突")
RULING = "操作員 2026-11-21 裁定:VDF 自己發號、自己定案,不再向 VCGC 請號"


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
P2 = importlib.util.module_from_spec(_spec)                # v0102(薄尾;它把 harvest 接到 v0100 本體)
sys.modules[_spec.name] = P2
_spec.loader.exec_module(P2)
BASE = P2.BASE                                             # v0100 本體


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(先 v0102 再 v0100)。"""
    for mod in (P2, BASE):
        if hasattr(mod, name):
            return getattr(mod, name)
    raise AttributeError(f"{TAG}:前版鏈沒有 {name}")


def self_confirm(vdf: Path = HERE, inplace: bool = False) -> dict:
    """登記冊尾版裡的待核條目一律轉「已確認(VDF 自發)」(號不變);已由 VCGC 核發的照留;退役不動。
    inplace=True:同一輪 register 剛寫的新版冊直接改,不多出一版。有改才寫。"""
    reg = BASE.latest_register(vdf)
    if not reg:
        return {"verb": "apply", "lamp": "GRAY", "why": "沒有登記冊(先 register)"}
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    changed, ts = 0, BASE.now()
    for e in entries.values():
        st = str(e.get("status", ""))
        if st.startswith(PENDING_PREFIX):
            e["status"] = SELF_STATUS
            e["self_confirmed_at"] = ts
            changed += 1
    out = reg
    if changed:
        out = reg if inplace else reg.with_name("VDF_SSOT_Register_v%04d.json" % (BASE._vnum(reg) + 1))
        book.update(at=ts, prior=reg.name if out != reg else book.get("prior"), writer="%s(自發定案)" % TAG, entries=entries,
                    rule="VDF 的 SSOT / 正則 / 同義字 / 參數 / 政策帳(唯一寫入者 = VDF_SSOTSync):VDF-<類>-#### 是 VDF 自己的定案號(" + RULING + ")· "
                         "已由 VCGC 核發的 ssot_id 照留 · 鍵不變號不變 · 只增不減 · 內容有變才出新版冊")
        out.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    live = [e for e in entries.values() if not str(e.get("status", "")).startswith("退役")]
    self_n = sum(1 for e in live if str(e.get("status", "")) == SELF_STATUS)
    vcgc_n = sum(1 for e in live if str(e.get("status", "")).startswith("已確認(VCGC)"))
    left = [k for k, e in entries.items() if str(e.get("status", "")).startswith(PENDING_PREFIX)]
    state = {"engine": TAG, "verb": "apply", "mode": "VDF 自發號", "at": ts, "lamp": "GREEN" if not left else "YELLOW",
             "register": out.name, "prior_register": reg.name if out != reg else None, "confirmed": len(live) - len(left), "self_confirmed": self_n,
             "vcgc_confirmed_kept": vcgc_n, "pending": len(left), "conflicts": 0, "changed": changed, "pending_keys": left[:50], "rule": RULING}
    (vdf / "contract").mkdir(parents=True, exist_ok=True)
    (vdf / "contract" / BASE.STATE_NAME).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    return state


def _snapshot(vdf: Path) -> dict:
    reg = BASE.latest_register(vdf)
    if not reg:
        return {}
    ents = json.loads(reg.read_text(encoding="utf-8")).get("entries") or {}
    return {k: (e.get("fp"), json.dumps(e.get("content"), sort_keys=True, ensure_ascii=False), e.get("semver") or "1.0.0", str(e.get("status", "")), e.get("ssot_id") or "")
            for k, e in ents.items()}


def bump_self_issued(vdf: Path, before: dict) -> int:
    """v0100 只在有中央號(ssot_id)時才升 semver;VDF 自發的條目沒有 ssot_id → 內容改了版本卻停在原地(PR #705 Codex P2)。
    這裡補上:本輪內容(指紋 / 內容)有變、前一份是已確認、沒有 ssot_id 的條目 → 升 minor、supersedes = 舊版;直接改 register 剛寫的那一版冊。"""
    reg = BASE.latest_register(vdf)
    if not reg or not before:
        return 0
    book = json.loads(reg.read_text(encoding="utf-8"))
    entries = book.get("entries") or {}
    n = 0
    for k, e in entries.items():
        b = before.get(k)
        if not b or e.get("ssot_id") or not b[3].startswith("已確認"):
            continue
        now_sig = (e.get("fp"), json.dumps(e.get("content"), sort_keys=True, ensure_ascii=False))
        if now_sig != (b[0], b[1]) and (e.get("semver") or "1.0.0") == b[2]:
            e["supersedes"] = b[2]
            e["semver"] = BASE._bump(b[2])
            e["sha256"] = BASE.asset_sha(e)
            n += 1
    if n:
        reg.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return n


def register(vdf: Path = HERE, items: dict | None = None) -> dict:
    before = _snapshot(vdf)
    r = BASE.register(vdf, items)                          # 收割(v0102 harvest)· 號碼 · 版冊規則照 v0100
    r["self_bumped"] = bump_self_issued(vdf, before) if r.get("written") else 0
    r["self_confirm"] = self_confirm(vdf, inplace=bool(r.get("written")))
    return r


def apply(vdf: Path = HERE, inplace: bool = False) -> dict:
    return self_confirm(vdf, inplace)


def request(vdf: Path = HERE) -> dict:
    """照 v0100 寫申請檔(全部已確認 → 請號清單空;VDF 內部自撞檢查照跑),再把規則改寫成 VDF 自己定案。"""
    q = BASE.request(vdf)
    f = vdf / "contract" / BASE.REQUEST_NAME
    if f.is_file():
        req = json.loads(f.read_text(encoding="utf-8"))
        req.update(engine=TAG, mode="VDF 自發號", rule=RULING + " · 請號清單永遠空;本檔只留給讀它的工具確認 VDF 編號同步有跑")
        f.write_text(json.dumps(req, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    q["mode"] = "VDF 自發號"
    return q


def sync(vdf: Path = HERE) -> dict:
    r = register(vdf)
    a = apply(vdf, inplace=bool(r.get("written")))
    q = request(vdf)
    lamp = "YELLOW" if "YELLOW" in (a.get("lamp"), q.get("lamp")) else a.get("lamp", "GREEN")
    line = "[VDF 編號同步] %s · VDF 自發號 · 登記 %d 條(%s)· 已確認 %d(VDF 自發 %d · 先前 VCGC 核發 %d)· 待核 %d · 自撞 %d · 冊 %s%s%s" % (
        lamp, r["entries"], " · ".join("%s %d" % kv for kv in sorted(r["by_kind"].items())), a.get("confirmed", 0), a.get("self_confirmed", 0),
        a.get("vcgc_confirmed_kept", 0), a.get("pending", 0), q.get("self_conflicts", 0), a.get("register") or r["register"],
        "(新版)" if (r.get("prior") or a.get("prior_register")) else "",
        (" · 略過 %d(%s)" % (len(r["skipped"]), " ; ".join(r["skipped"][:3]))) if r.get("skipped") else "")
    return {"verb": "sync", "lamp": lamp, "register": r, "apply": a, "request": q, "line": line}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a else "sync"
    fn = {"register": register, "request": request, "apply": apply, "sync": sync}.get(verb)
    if fn is None:
        return BASE.main(a)
    r = fn()
    print(r["line"] if "line" in r else json.dumps(r, ensure_ascii=False, indent=1, default=str))
    return 0 if r.get("lamp") in ("GREEN", "YELLOW", None) else 1


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 薄尾自測(VDF 自己發號定案 · 不等 VCGC 核號)===" % TAG, flush=True)
    with tempfile.TemporaryDirectory(prefix="vdf_ssotsync_v0103_") as td:
        vdf = Path(td) / "VDF"
        (vdf / "registry").mkdir(parents=True)
        ent = {"VDF:SSOT:A": {"no": "VDF-SSOT-0001", "kind": "SSOT", "key": "VDF:SSOT:A", "fp": "a1", "content": {"x": 1}, "semver": "1.0.0", "status": "暫編 · 待 VCGC 核號", "ssot_id": ""},
               "VDF:SSOT:B": {"no": "VDF-SSOT-0002", "kind": "SSOT", "key": "VDF:SSOT:B", "fp": "b1", "content": {"x": 2}, "semver": "1.0.0", "status": "已確認(VCGC)", "ssot_id": "VIA-VDF-SSOT007"},
               "VDF:SSOT:C": {"no": "VDF-SSOT-0003", "kind": "SSOT", "key": "VDF:SSOT:C", "fp": "c2", "content": {"x": 3}, "semver": "1.1.0", "status": "內容更新 · 待 VCGC 重檢", "ssot_id": "VIA-VDF-SSOT008"},
               "VDF:SSOT:D": {"no": "VDF-SSOT-0004", "kind": "SSOT", "key": "VDF:SSOT:D", "fp": "d1", "content": {"x": 4}, "semver": "1.0.0", "status": "衝突 · 待人判(VCGC)· x", "ssot_id": ""},
               "VDF:SSOT:E": {"no": "VDF-SSOT-0005", "kind": "SSOT", "key": "VDF:SSOT:E", "fp": "e1", "content": {"x": 5}, "semver": "1.0.0", "status": "退役(保留)", "ssot_id": ""}}
        (vdf / "registry" / "VDF_SSOT_Register_v0100.json").write_text(json.dumps({"schema": "VIA.VDF.SSOTRegister.v2", "entries": ent}, ensure_ascii=False), encoding="utf-8")
        s1 = apply(vdf)
        b = json.loads((vdf / "registry" / "VDF_SSOT_Register_v0101.json").read_text(encoding="utf-8"))["entries"]
        chk("① 待核三種(暫編 · 內容更新 · 衝突)→ 已確認(VDF 自發)· 號不變 · 已由 VCGC 核發的照留(狀態 + ssot_id)· 退役不動 · 出一版",
            [b[k]["status"] for k in "ABCDE" for k in ["VDF:SSOT:" + k]] == [SELF_STATUS, "已確認(VCGC)", SELF_STATUS, SELF_STATUS, "退役(保留)"]
            and [b["VDF:SSOT:" + k]["no"] for k in "ABCDE"] == ["VDF-SSOT-%04d" % i for i in range(1, 6)] and b["VDF:SSOT:C"]["ssot_id"] == "VIA-VDF-SSOT008"
            and s1["pending"] == 0 and s1["lamp"] == "GREEN" and s1["self_confirmed"] == 3 and s1["vcgc_confirmed_kept"] == 1, s1)
        st = json.loads((vdf / "contract" / "VDF_NUMBER_STATE_latest.json").read_text(encoding="utf-8"))
        chk("② 狀態檔:模式 VDF 自發號 · 待核 0 · 不寫本機絕對路徑(沒有 grant_sources)", st.get("mode") == "VDF 自發號" and st["pending"] == 0 and "grant_sources" not in st, st)
        s2 = apply(vdf)
        chk("③ 再跑一次:無變更 · 不出新版", s2["changed"] == 0 and not (vdf / "registry" / "VDF_SSOT_Register_v0102.json").exists(), s2)
        keep = BASE.harvest
        items = {k: {"kind": "SSOT", "fp": e["fp"], "version": "v0100", "src": ["x.json"], "content": e["content"]} for k, e in ent.items() if k != "VDF:SSOT:E"}
        items["VDF:SSOT:F"] = {"kind": "SSOT", "fp": "f1", "version": "v0100", "src": ["f.json"], "content": {"x": 6}}
        items["VDF:SSOT:A"] = dict(items["VDF:SSOT:A"], fp="a2", content={"x": 11})
        BASE.harvest = lambda vdf=None: items
        try:
            sy = sync(vdf)
            sy2 = sync(vdf)
        finally:
            BASE.harvest = keep
        last = json.loads(BASE.latest_register(vdf).read_text(encoding="utf-8"))["entries"]
        req = json.loads((vdf / "contract" / "VDF_NUMBER_REQUEST_latest.json").read_text(encoding="utf-8"))
        chk("④ sync:新條目 F 拿 VDF-SSOT-0006 直接已確認(VDF 自發)· A 內容變 → 升版仍已確認(不回待核)· 號全不變 · 請號清單空 · 規則寫 VDF 自己定案",
            last["VDF:SSOT:F"]["no"] == "VDF-SSOT-0006" and last["VDF:SSOT:F"]["status"] == SELF_STATUS and last["VDF:SSOT:A"]["status"] == SELF_STATUS
            and last["VDF:SSOT:A"]["no"] == "VDF-SSOT-0001" and req.get("pending") == [] and req.get("ssot_items") == [] and "VDF 自己發號" in req.get("rule", "")
            and "VDF 自發號" in sy["line"] and "待核 0" in sy["line"], (sy["line"], req.get("pending"), last.get("VDF:SSOT:F")))
        chk("⑤ 第二次 sync:登記冊不再出新版(不會每輪換版)", not sy2["register"].get("written") and sy2["apply"]["changed"] == 0, (sy2["register"].get("register"), sy2["apply"].get("changed")))
        items["VDF:SSOT:F"] = dict(items["VDF:SSOT:F"], fp="f2", content={"x": 66})
        BASE.harvest = lambda vdf=None: items
        try:
            sy3 = sync(vdf)
            sy4 = sync(vdf)
        finally:
            BASE.harvest = keep
        l3 = json.loads(BASE.latest_register(vdf).read_text(encoding="utf-8"))["entries"]
        chk("⑤b VDF 自發條目(沒有 ssot_id)內容再改 → semver 1.0.0 → 1.1.0 · supersedes 1.0.0 · 號不變 · 仍已確認 · 不編假中央號;再跑一次不再升(PR #705 Codex P2)",
            l3["VDF:SSOT:F"]["semver"] == "1.1.0" and l3["VDF:SSOT:F"]["supersedes"] == "1.0.0" and l3["VDF:SSOT:F"]["no"] == "VDF-SSOT-0006"
            and l3["VDF:SSOT:F"]["status"] == SELF_STATUS and not l3["VDF:SSOT:F"].get("ssot_id") and sy3["register"]["self_bumped"] == 1
            and not sy4["register"].get("written"), (l3["VDF:SSOT:F"].get("semver"), sy3["register"].get("self_bumped"), sy4["register"].get("written")))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 + 網路橋在 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑 · v0100 本體函式沒被換掉",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "[VIA:NET-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src
        and BASE.register.__module__ == BASE.__name__ and BASE.apply.__module__ == BASE.__name__)
    rc = P2.main(["--selftest"])
    chk("⑦ 前版 %s 自測照過" % PRIOR_PATH.stem, rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (TAG, sum(ok), len(ok), "PASS" if good else "FAIL"), flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
