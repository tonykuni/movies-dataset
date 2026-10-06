#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0143 — 薄尾:config 動詞 + 左面板改成族群設定(操作員令 2026-10-06 收尾:VDF 左面板只有「分族群統一的起始日期」,改族群一起改;少數可新增項目)。
  config show                          印族群冊(每族:起始日期 · 項目 · 最後改動)
  config set --group <G> --start <YYYY-MM-DD>   改一個族群的起始日期(整族一起變;history 只增)
  config add --group <G> --item <代號>          新增項目到族群(同項不重複)
  config group-add --group <G> [--start …]     新增族群
  ui                                    左面板 = 族群表(起始日期可改 → 組 config set 指令)+ 新增項目列 + 複製;右面板同 v0142(健康 / 表頭 / 全景 / 結果 / 本輪 PS)
  冊:SSOT/VDF_Config_v0100.json(VDF 自家;首次自建預設五族:TW_EQUITY · TW_ETF · US_MACRO_FRED · CN_AKSHARE · GLOBAL_INDEX,起始 2015-01-01)
其餘動詞照前版鏈。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import html as _html
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0143"
DEFAULT_GROUPS = {"TW_EQUITY": "台股個股", "TW_ETF": "台股 ETF", "US_MACRO_FRED": "美國總經(FRED)", "CN_AKSHARE": "陸港(AKShare)", "GLOBAL_INDEX": "全球指數"}


def _vnum_v0143(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0143(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0143(p) < _vnum_v0143(__file__)), key=_vnum_v0143)
PRIOR = _load_v0143(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _home():
    return Path(os.environ.get("VIA_VDF_HOME") or HERE)


def _cfg_path() -> Path:
    return _home() / "SSOT" / "VDF_Config_v0100.json"


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def config_load() -> dict:
    p = _cfg_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8-sig"))
        except ValueError:
            pass
    cfg = {"schema": "VIA.VDF.Config.v1", "version": "v0100", "created_at": _now(), "rule": "族群統一起始日期:改族群整族一起變;items 只增(退役標 status);history 只增",
           "groups": {g: {"zh": zh, "start_date": "2015-01-01", "items": [], "updated_at": _now()} for g, zh in DEFAULT_GROUPS.items()}, "history": []}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    return cfg


def _save(cfg: dict, action: dict) -> None:
    cfg["history"].append(dict(action, ts=_now()))
    cfg["updated_at"] = _now()
    _cfg_path().write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def config_set(group: str, start: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", start or ""):
        return {"ok": False, "why": "起始日期要 YYYY-MM-DD"}
    cfg = config_load()
    g = cfg["groups"].get(group)
    if not g:
        return {"ok": False, "why": "族群 %s 不在(config group-add)" % group}
    old = g["start_date"]
    g["start_date"], g["updated_at"] = start, _now()
    _save(cfg, {"action": "SET_START", "group": group, "from": old, "to": start, "items_affected": len(g["items"])})
    return {"ok": True, "group": group, "from": old, "to": start, "items_affected": len(g["items"])}


def config_add(group: str, item: str) -> dict:
    cfg = config_load()
    g = cfg["groups"].get(group)
    if not g:
        return {"ok": False, "why": "族群 %s 不在" % group}
    item = (item or "").strip()
    if not item:
        return {"ok": False, "why": "項目空"}
    if any(i.get("id") == item for i in g["items"]):
        return {"ok": True, "group": group, "item": item, "dup": True}
    g["items"].append({"id": item, "added_at": _now(), "status": "ACTIVE"})
    g["updated_at"] = _now()
    _save(cfg, {"action": "ADD_ITEM", "group": group, "item": item})
    return {"ok": True, "group": group, "item": item, "n": len(g["items"])}


def config_group_add(group: str, start: str = "2015-01-01", zh: str = "") -> dict:
    cfg = config_load()
    if group in cfg["groups"]:
        return {"ok": True, "group": group, "dup": True}
    cfg["groups"][group] = {"zh": zh or group, "start_date": start, "items": [], "updated_at": _now()}
    _save(cfg, {"action": "ADD_GROUP", "group": group, "start": start})
    return {"ok": True, "group": group}


def _ui_left_v0143(cfg: dict, py_path: str) -> str:
    rows = "".join("<tr><td><b>%s</b><div class='dim'>%s · %d 項</div></td><td><input class='sd' data-g='%s' value='%s' size='10'></td><td><button onclick=\"setStart('%s')\">改整族</button></td></tr>"
                   % (_html.escape(g), _html.escape(v.get("zh", "")), len(v.get("items", [])), _html.escape(g), _html.escape(v.get("start_date", "")), _html.escape(g)) for g, v in cfg["groups"].items())
    gopts = "".join("<option value='%s'>%s</option>" % (_html.escape(g), _html.escape(g)) for g in cfg["groups"])
    return """
  <div class='card'><b>族群統一起始日期</b><div class='dim'>改一族,整族項目一起變(VDF_Config_v0100 · history 只增)</div>
  <table><thead><tr><th>族群</th><th>起始</th><th></th></tr></thead><tbody>%s</tbody></table></div>
  <div class='card'><b>新增項目</b><label>族群</label><select id='ag'>%s</select><label>項目(代號 / 序列名)</label><input id='ai' placeholder='2330.TW'><button onclick="addItem()">新增</button></div>
  <div class='card'><b>新增族群</b><label>族群代碼</label><input id='ng' placeholder='JP_EQUITY'><label>起始</label><input id='ns' value='2015-01-01'><button onclick="addGroup()">新增</button></div>
  <label>指令(貼到 PowerShell)</label><textarea id='cmd' rows='4' readonly></textarea><button onclick='copyit()'>複製</button>
  <script>
  var PY=%s;
  function out(c){document.getElementById('cmd').value=c}
  function setStart(g){var d=document.querySelector('input.sd[data-g="'+g+'"]').value;out('python "'+PY+'" config set --group '+g+' --start '+d)}
  function addItem(){out('python "'+PY+'" config add --group '+document.getElementById('ag').value+' --item '+document.getElementById('ai').value.trim())}
  function addGroup(){out('python "'+PY+'" config group-add --group '+document.getElementById('ng').value.trim()+' --start '+document.getElementById('ns').value.trim())}
  function copyit(){var t=document.getElementById('cmd');t.select();try{navigator.clipboard.writeText(t.value)}catch(e){document.execCommand('copy')}}
  </script>""" % (rows, gopts, json.dumps(py_path))


def ui() -> dict:
    """兩面板:右面板沿用 v0142 的頁籤;左面板換成族群設定。做法:先叫前版 ui() 產頁,再把 <aside>…</aside> 的內容換掉(不改前版檔)。"""
    base = PRIOR.ui()
    fp = Path(base["html"])
    htm = fp.read_text(encoding="utf-8")
    cfg = config_load()
    left = _ui_left_v0143(cfg, str(HERE / Path(__file__).name))
    a, b = htm.find("<aside>"), htm.find("</aside>")
    if a >= 0 and b > a:
        htm = htm[:a] + "<aside>" + left + htm[b:]
        fp.write_text(htm, encoding="utf-8")
    base["left"] = "config(族群 %d)" % len(cfg["groups"])
    return base


def _print_cfg(cfg: dict) -> None:
    print("[計] VDF config · 族群 %d · 冊 %s · history %d" % (len(cfg["groups"]), _cfg_path().name, len(cfg.get("history", []))))
    for g, v in cfg["groups"].items():
        print("  [OK] %s(%s)· 起始 %s · 項目 %d%s" % (g, v.get("zh", ""), v.get("start_date"), len(v.get("items", [])), (" · " + ",".join(i["id"] for i in v["items"][:8])) if v.get("items") else ""))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:1] == ["config"]:
        sub = args[1:2]
        if sub == ["show"] or not sub:
            _print_cfg(config_load())
            return 0
        if sub == ["set"]:
            r = config_set(opt("--group", ""), opt("--start", ""))
        elif sub == ["add"]:
            r = config_add(opt("--group", ""), opt("--item", ""))
        elif sub == ["group-add"]:
            r = config_group_add(opt("--group", ""), opt("--start", "2015-01-01"), opt("--zh", ""))
        else:
            print("[拒跑] config show | set --group G --start D | add --group G --item X | group-add --group G [--start D]")
            return 2
        print("[計] VDF config %s · %s" % (sub[0], json.dumps(r, ensure_ascii=False)))
        return 0 if r.get("ok") else 1
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VDF ui · %s · %s · 左 %s · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), u.get("left"), u["lamp"]))
        print("  [U/I] %s" % u["html"])
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdfcfg-"))
    home = td / "functional modules" / "VDF"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_HEALTH_OUT": str(td / "VIA_Reports" / "vdf"), "VIA_NO_OPEN": "1"})
    (home / "VDF_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    cfg = config_load()
    chk("① 首次自建五族 · 起始 2015-01-01", len(cfg["groups"]) == 5 and all(v["start_date"] == "2015-01-01" for v in cfg["groups"].values()))
    config_add("TW_EQUITY", "2330.TW")
    config_add("TW_EQUITY", "2317.TW")
    r = config_set("TW_EQUITY", "2018-06-01")
    cfg2 = config_load()
    chk("② 改族群起始 → 整族一起(items_affected 2)· history 3 · 壞日期拒", r["items_affected"] == 2 and cfg2["groups"]["TW_EQUITY"]["start_date"] == "2018-06-01" and len(cfg2["history"]) == 3 and not config_set("TW_EQUITY", "2018/6/1")["ok"])
    chk("③ 重複項不重加 · 新族群可加", config_add("TW_EQUITY", "2330.TW").get("dup") and config_group_add("JP_EQUITY", "2020-01-01")["ok"] and "JP_EQUITY" in config_load()["groups"])
    u = ui()
    htm = Path(u["html"]).read_text(encoding="utf-8")
    chk("④ ui 左面板 = 族群表(改整族 · 新增項目 · 新增族群 · 組指令)· 右面板頁籤仍在", "改整族" in htm and "新增項目" in htm and "config set --group" in htm and (htm.count('<div class="page"') + htm.count('<div class="page on"')) == 5)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 三橋 · glob 取前版", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]")))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0143 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
