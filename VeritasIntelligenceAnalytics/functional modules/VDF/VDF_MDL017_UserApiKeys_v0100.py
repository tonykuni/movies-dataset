#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_MDL017_UserApiKeys v0100 — 每個人輸入自己的 API 鑰(個人設定檔)· 啟動時只帶進子行程 · 環境鑰只當測試鑰

操作員 2026-11-15:「環境鑰用於測試用 · 最後版本要輸入每個人的 API KEY」;存放位置操作員選「個人設定檔」。
現況(盤點):VDF 讀 FRED 鑰的 9 支引擎一律「環境變數 FRED_API_KEY → 輸出夾共用鑰匙檔 .fred_api_key」,
兩者都是整台機器共用,沒有「每個人自己的鑰」。本模組(VDF 自己的;9 支引擎一字不動):
  鑰放哪:每個 Windows 使用者自己的 %APPDATA%\VIA\keys\<名>.key(POSIX:$XDG_CONFIG_HOME 或 ~/.config/via/keys,權限 600)。
          不進倉、不進輸出夾、不印、不寫 log。
  順序:個人鑰 → 環境鑰(只當測試鑰,照實標「測試鑰」)→ 舊共用鑰匙檔(標「舊共用」,建議改個人鑰)→ 沒有(引擎照實 SKIP)。
  怎麼帶進引擎:`run -- <指令>` 起子行程,只在「子行程的環境」放個人鑰(蓋過測試鑰);本視窗環境、檔案一字不動。
               9 支引擎都先讀環境變數,所以整棵子行程樹(ActivateVDF → manager → 引擎)都用這個人的鑰。
指令(在 VDF 夾或倉根都可;每個人用自己的 Windows 帳號跑):
  python VDF_MDL017_UserApiKeys_v0100.py set fred            隱藏輸入(getpass)· 驗格式(FRED = 32 碼小寫英數)· 存個人設定檔
  python VDF_MDL017_UserApiKeys_v0100.py set fred --stdin    從標準輸入讀一行(腳本用;鑰不進指令歷史)
  python VDF_MDL017_UserApiKeys_v0100.py status              每把鑰:個人鑰 / 測試鑰 / 舊共用 有沒有 · 實際會用哪一個 · 指紋(sha256 前 8 碼,不露鑰)
  python VDF_MDL017_UserApiKeys_v0100.py clear fred --yes    刪掉自己的個人鑰
  python VDF_MDL017_UserApiKeys_v0100.py run -- python ActivateVDF.py run …   用個人鑰跑(沒個人鑰 = 照原環境跑,照實說)
  python VDF_MDL017_UserApiKeys_v0100.py --selftest          全在暫存夾,不碰真的個人鑰、不碰本視窗環境、零網路
邊界:AI 不代輸、不代設、不讀值給人看;不碰同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT);不裝套件;不碰 TA-Lib;不匯入他系統程式。
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
    """統包唯一網路工具惰性載入;本模組零網路(只管本機個人鑰)。"""
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

import argparse
import getpass
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # …/functional modules/VDF
_STEM = "VDF_MDL017_UserApiKeys"
TAG = "%s v%s" % (_STEM, Path(__file__).stem.rsplit("_v", 1)[-1])

#: 鑰冊:名字 → 環境變數名(測試鑰)· 舊共用鑰匙檔(相對 VDF 夾)· 格式 · 申請網址。新增 API 只加一列。
KEYS = {
    "fred": {"env": "FRED_API_KEY", "legacy": ("output_hub/mega/.fred_api_key", "output_hub/.fred_api_key"),
             "pattern": r"^[a-z0-9]{32}$", "hint": "32 碼小寫英數", "apply": "https://fredaccount.stlouisfed.org/apikeys"},
}


def key_dir(env=None) -> Path:
    """個人設定檔夾:Windows %APPDATA%\\VIA\\keys;否則 $XDG_CONFIG_HOME/via/keys 或 ~/.config/via/keys。"""
    env = os.environ if env is None else env
    if env.get("APPDATA"):
        return Path(env["APPDATA"]) / "VIA" / "keys"
    base = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "via" / "keys"


def _spec(name: str) -> dict:
    if name not in KEYS:
        raise KeyError("不認得的鑰名 %r(認得:%s)" % (name, ", ".join(sorted(KEYS))))
    return KEYS[name]


def valid(name: str, value: str) -> bool:
    return bool(value) and re.match(_spec(name)["pattern"], value) is not None


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8] if value else ""


def user_key_path(name: str, kdir: Path | None = None) -> Path:
    _spec(name)
    return (kdir or key_dir()) / (name + ".key")


def save(name: str, value: str, kdir: Path | None = None) -> Path:
    """存個人鑰(原子寫 · POSIX 權限 600)。格式不對 → ValueError(不存)。"""
    value = (value or "").strip()
    if not valid(name, value):
        raise ValueError("格式不對(%s 要 %s);沒存" % (name, _spec(name)["hint"]))
    p = user_key_path(name, kdir)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + name + "_", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(value)
        if os.name != "nt":
            os.chmod(tmp, 0o600)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return p


def clear(name: str, kdir: Path | None = None) -> bool:
    p = user_key_path(name, kdir)
    if p.is_file():
        p.unlink()
        return True
    return False


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    except OSError:
        return ""


def resolve(name: str, kdir: Path | None = None, env=None, vdf_dir: Path | None = None) -> tuple:
    """(值, 來源):個人鑰 → 測試鑰(環境)→ 舊共用鑰匙檔 → ('', 'none')。值只回給呼叫端,不印。"""
    sp, env = _spec(name), (os.environ if env is None else env)
    v = _read(user_key_path(name, kdir))
    if v:
        return v, "user"
    v = (env.get(sp["env"]) or "").strip()
    if v:
        return v, "env-test"
    for rel in sp["legacy"]:
        v = _read((vdf_dir or HERE) / rel)
        if v:
            return v, "legacy-shared"
    return "", "none"


_SRC_LABEL = {"user": "個人鑰", "env-test": "環境鑰(測試鑰)", "legacy-shared": "舊共用鑰匙檔", "none": "沒有鑰"}


def status(kdir: Path | None = None, env=None, vdf_dir: Path | None = None) -> list:
    """每把鑰的狀態(只有有沒有 · 來源 · 指紋;永不含值)。"""
    env = os.environ if env is None else env
    rows = []
    for name, sp in sorted(KEYS.items()):
        u = _read(user_key_path(name, kdir))
        t = (env.get(sp["env"]) or "").strip()
        legacy = [rel for rel in sp["legacy"] if _read((vdf_dir or HERE) / rel)]
        v, src = resolve(name, kdir, env, vdf_dir)
        rows.append({"name": name, "user": bool(u), "user_ok": valid(name, u) if u else None, "env_test": bool(t),
                     "legacy": legacy, "use": src, "fp": fingerprint(v), "path": str(user_key_path(name, kdir))})
    return rows


def child_env(base, kdir: Path | None = None, vdf_dir: Path | None = None) -> tuple:
    """子行程環境:照抄 base;有個人鑰的那幾把 → 換成個人鑰(蓋過測試鑰)。回 (env, {名: 來源})。不碰 base 本身。"""
    out, used = dict(base), {}
    for name, sp in KEYS.items():
        v, src = resolve(name, kdir, out, vdf_dir)
        if src == "user":
            out[sp["env"]] = v
        used[name] = src
    return out, used


def run_with_keys(cmd: list, kdir: Path | None = None) -> int:
    env, used = child_env(os.environ, kdir)
    for name, src in sorted(used.items()):
        sp = KEYS[name]
        extra = "" if src in ("user",) else (" · 正式版請先 set %s 輸入自己的鑰" % name)
        print("[鑰] %s:%s%s" % (name, _SRC_LABEL[src], extra), flush=True)
    if not cmd:
        print("[鑰] run 後面要接指令:run -- python ActivateVDF.py run …", flush=True)
        return 2
    return subprocess.run(cmd, env=env).returncode


def _print_status(rows: list) -> None:
    for r in rows:
        sp = KEYS[r["name"]]
        print("[鑰] %s · 個人鑰 %s%s · 測試鑰(環境 %s)%s · 舊共用 %s · 實際會用:%s%s" % (
            r["name"], "有" if r["user"] else "沒有", "" if r["user_ok"] in (None, True) else "(格式不對)", sp["env"],
            "有" if r["env_test"] else "沒有", ("有:" + ", ".join(r["legacy"])) if r["legacy"] else "沒有",
            _SRC_LABEL[r["use"]], (" · 指紋 " + r["fp"]) if r["fp"] else ""), flush=True)
        print("      個人鑰位置 %s · 申請 %s" % (r["path"], sp["apply"]), flush=True)


def _own_src_ok() -> tuple:
    src = Path(__file__).read_text(encoding="utf-8")
    bad = []
    if "[VIA:ACCEL-BRIDGE:v0100]" not in src or "[VIA:NET-BRIDGE:v0100]" not in src:
        bad.append("缺橋")
    if re.search(r"VIA_(NET|SCRAPE)_" + "CON" + r"SENT['\"]\]\s*=(?!=)", src):
        bad.append("寫同意閘")
    if re.search(r"os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.(pop|update|setdefault|clear)\(|\bput" + r"env\b", src):
        bad.append("寫本行程環境")
    if re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VRN2_|VCGC|ta" + r"lib\b|requests|urllib|httpx)", src, re.M):
        bad.append("匯入他系統 / 網路 / TA-Lib")
    return (not bad), bad


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
        else:
            f += 1
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("=== %s · 自測(暫存夾 · 不碰真的個人鑰 · 不碰本視窗環境 · 零網路)===" % TAG, flush=True)
    env_before = dict(os.environ)
    sim = "0123456789abcdef0123456789abcdef"                # 格式樣本(不是任何人的真鑰)
    sim2 = "fedcba9876543210fedcba9876543210"
    with tempfile.TemporaryDirectory(prefix="vdf_keys_") as td:
        td = Path(td)
        kd, vdf = td / "keys", td / "VDF"
        (vdf / "output_hub" / "mega").mkdir(parents=True)
        pth = save("fred", sim, kd)
        chk("① 存個人鑰:檔在個人鑰夾 · 內容只有鑰 · POSIX 權限 600(Windows 由 %APPDATA% 使用者權限保護)",
            pth == kd / "fred.key" and pth.read_text(encoding="utf-8") == sim
            and (os.name == "nt" or (pth.stat().st_mode & 0o777) == 0o600) and not list(kd.glob(".fred_*")))
        bad, refused = [], []
        for v in ("", "short", sim.upper(), sim + "0", "0123456789abcdef0123456789abcde!"):
            try:
                save("fred", v, kd)
                bad.append(v)
            except ValueError as exc:
                refused.append(str(exc))
        chk("② 格式不對一律不存(空 · 太短 · 大寫 · 太長 · 符號)· 原本的個人鑰不被蓋掉", not bad and len(refused) == 5
            and all("沒存" in x for x in refused) and _read(kd / "fred.key") == sim, bad)
        envm = {"FRED_API_KEY": sim2, "PATH": "/x"}
        (vdf / "output_hub" / "mega" / ".fred_api_key").write_text(sim2, encoding="utf-8")
        r1 = resolve("fred", kd, envm, vdf)
        clear("fred", kd)
        r2 = resolve("fred", kd, envm, vdf)
        r3 = resolve("fred", kd, {"PATH": "/x"}, vdf)
        (vdf / "output_hub" / "mega" / ".fred_api_key").unlink()
        r4 = resolve("fred", kd, {"PATH": "/x"}, vdf)
        chk("③ 順序:個人鑰 → 環境測試鑰 → 舊共用鑰匙檔 → 沒有", [x[1] for x in (r1, r2, r3, r4)] == ["user", "env-test", "legacy-shared", "none"]
            and r1[0] == sim and r2[0] == sim2 and r4[0] == "", [x[1] for x in (r1, r2, r3, r4)])
        save("fred", sim, kd)
        ce, used = child_env(envm, kd, vdf)
        ce2, used2 = child_env({"PATH": "/x"}, td / "nokeys", vdf)
        chk("④ 子行程環境:有個人鑰 → 只換那一個變數(蓋過測試鑰)· 其他照抄 · 傳進來的 dict 不被改;沒個人鑰 → 原樣",
            ce.get("FRED_API_KEY") == sim and ce.get("PATH") == "/x" and envm["FRED_API_KEY"] == sim2 and used == {"fred": "user"}
            and ce2 == {"PATH": "/x"} and used2 == {"fred": "none"}, (used, used2))
        rows = status(kd, envm, vdf)
        blob = repr(rows)
        chk("⑤ status 不露鑰:只有 有沒有 · 來源 · 指紋(sha256 前 8 碼)", sim not in blob and sim2 not in blob and rows[0]["use"] == "user"
            and rows[0]["fp"] == fingerprint(sim) and len(rows[0]["fp"]) == 8 and rows[0]["user"] and rows[0]["env_test"], rows)
        chk("⑥ 個人鑰夾:Windows = %APPDATA%\\VIA\\keys · 其他 = XDG 或 ~/.config/via/keys",
            key_dir({"APPDATA": r"C:\Users\u\AppData\Roaming"}) == Path(r"C:\Users\u\AppData\Roaming") / "VIA" / "keys"
            and key_dir({"XDG_CONFIG_HOME": "/cfg"}) == Path("/cfg") / "via" / "keys")
        try:
            resolve("nope", kd, {}, vdf)
            unknown_ok = False
        except KeyError:
            unknown_ok = True
        chk("⑦ 不認得的鑰名 → 明說(不猜)", unknown_ok)
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_run = run_with_keys([sys.executable, "-c", "print(7)"], td / "nokeys")
        chk("⑩ run 端到端:沒個人鑰 → 照原環境起子行程 · rc 0 · 照實印來源(不是「個人鑰」)", rc_run == 0
            and "[鑰] fred:" in buf.getvalue() and "個人鑰" not in buf.getvalue().split("fred:", 1)[1].split("·")[0], buf.getvalue()[-160:])
    ok, bad = _own_src_ok()
    chk("⑧ 兩座橋 · 不寫本行程環境 · 不寫同意閘 · 不匯入他系統 / 網路套件 / TA-Lib", ok, bad)
    chk("⑨ 本行程環境前後一樣 · 真的個人鑰夾沒被碰(自測全在暫存夾)", dict(os.environ) == env_before)
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    if argv[:1] == ["run"]:
        rest = argv[1:]
        return run_with_keys(rest[1:] if rest[:1] == ["--"] else rest)
    ap = argparse.ArgumentParser(prog=Path(__file__).name, description="每個人自己的 API 鑰(個人設定檔)")
    sub = ap.add_subparsers(dest="verb")
    s = sub.add_parser("set")
    s.add_argument("name")
    s.add_argument("--stdin", action="store_true")
    sub.add_parser("status")
    c = sub.add_parser("clear")
    c.add_argument("name")
    c.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv)
    if a.verb == "set":
        sp = _spec(a.name)
        value = sys.stdin.readline().strip() if a.stdin else getpass.getpass("  %s 鑰(輸入不顯示;%s;申請 %s):" % (a.name, sp["hint"], sp["apply"]))
        try:
            p = save(a.name, value)
        except ValueError as exc:
            print("[鑰] %s" % exc, flush=True)
            return 2
        print("[鑰] %s 個人鑰已存 · 指紋 %s · %s" % (a.name, fingerprint(value.strip()), p), flush=True)
        return 0
    if a.verb == "clear":
        if not a.yes:
            print("[鑰] 要刪自己的 %s 個人鑰請加 --yes" % a.name, flush=True)
            return 2
        print("[鑰] %s 個人鑰%s" % (a.name, "已刪" if clear(a.name) else "本來就沒有"), flush=True)
        return 0
    _print_status(status())
    return 0


if __name__ == "__main__":
    sys.exit(main())
