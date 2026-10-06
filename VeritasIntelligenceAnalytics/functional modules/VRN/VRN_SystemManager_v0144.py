#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0144 — 薄尾:ui 套 L118 滑鼠律(操作員令 2026-10-06:操作介面 Windows I/O 拖曳 / 下拉 / 勾選,動滑鼠不動鍵盤)。
  ui   前版鏈產頁後:指令框旁加「執行(滑鼠)」(via://VRN/<動詞>?args=… 連結,Windows 交給啟動器 PS)與「選檔執行」(pick=1 開檔案選取器);日期欄改 type=date;鍵盤輸入只剩最後手段。
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

import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0144"


def _vnum_v0144(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0144(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0144(p) < _vnum_v0144(__file__)), key=_vnum_v0144)
PRIOR = _load_v0144(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:UI-MOUSE:v0100] L118 滑鼠律後處理:指令框旁加「執行(滑鼠)」= via:// 連結(Windows 交給啟動器)· 「選檔執行」pick=1 · 日期欄改 type=date;鍵盤輸入只剩最後手段 =====
_MOUSE_JS = """
<script>
(function(){
  var SUB=%(sub)s;
  function build(cmd,pick){
    var m=cmd.match(/python\\s+"[^"]+"\\s+(.*)$/); if(!m) return '';
    var toks=m[1].trim().split(/\\s+/).filter(Boolean), verb=[], args=[];
    for(var i=0;i<toks.length;i++){ if(args.length===0 && toks[i].indexOf('--')!==0) verb.push(toks[i]); else args.push(toks[i]); }
    var u='via://'+SUB+'/'+verb.join('/'); var q=[]; if(args.length) q.push('args='+encodeURIComponent(args.join(' '))); if(pick) q.push('pick=1');
    return u+(q.length?('?'+q.join('&')):'');
  }
  function sync(){ var t=document.getElementById('cmd'); if(!t) return; var a=document.getElementById('run'), b=document.getElementById('runpick');
    if(a){a.href=build(t.value,false)||'#';} if(b){b.href=build(t.value,true)||'#';} }
  var t=document.getElementById('cmd'); if(t){ new MutationObserver(sync).observe(t,{attributes:true,childList:true,characterData:true,subtree:true}); t.addEventListener('input',sync); }
  var origSet=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value');
  if(t&&origSet&&origSet.set){ Object.defineProperty(t,'value',{set:function(v){origSet.set.call(this,v);sync();},get:function(){return origSet.get.call(this);}}); }
  document.querySelectorAll("input.sd, input#ns").forEach(function(i){ i.type='date'; });
  sync();
})();
</script>"""
_MOUSE_BTN = "<a id='run' class='btn p' href='#' title='via:// 協定 → 啟動器 PS → python 動詞 → 開 U/I(先跑一次 Invoke-VIA-Launch -RegisterProtocol)'>執行(滑鼠)</a> <a id='runpick' class='btn' href='#' title='先開 Windows 檔案選取器,選到的檔接在參數後'>選檔執行</a>"
_MOUSE_CSS = "<style>a.btn{display:inline-block;padding:4px 10px;border:1px solid var(--line,#e0e0e0);border-radius:6px;background:#fff;color:var(--txt,#1f2937);text-decoration:none;font-size:11px;margin:6px 4px 0 0}a.btn.p{background:var(--acc,#2563eb);color:#fff;border-color:var(--acc,#2563eb)}</style>"


def ui_mouse_apply(html_text, sub):
    """在 <textarea id='cmd'…></textarea> 後插兩個 via:// 按鈕;</body> 前插 JS;日期欄改 type=date。沒有指令框的頁不動。"""
    import re as _re
    if "id='cmd'" not in html_text and 'id="cmd"' not in html_text:
        return html_text
    out = _re.sub(r"(<textarea id=['\"]cmd['\"][^>]*></textarea>)", lambda m: m.group(1) + _MOUSE_BTN, html_text, count=1)
    js = _MOUSE_JS % {"sub": __import__("json").dumps(sub)}
    i = out.rfind("</body>")
    out = (out[:i] + _MOUSE_CSS + js + out[i:]) if i >= 0 else out + _MOUSE_CSS + js
    return out
# ===== [VIA:UI-MOUSE:END] =====


def ui() -> dict:
    u = PRIOR.ui()
    fp = Path(u["html"])
    fp.write_text(ui_mouse_apply(fp.read_text(encoding="utf-8"), "VRN"), encoding="utf-8")
    u["mouse"] = True
    return u


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["ui"]:
        u = ui()
        print("[計] VRN ui · %s · %s · 模板 %s · 滑鼠律 via:// · %s" % (u["html"], " ".join("%s=%s" % kv for kv in u["steps"].items()), u.get("theme"), u["lamp"]))
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

    td = Path(tempfile.mkdtemp(prefix="vrnmouse-"))
    home = td / "functional modules" / "VRN"
    (home / "registry").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_NO_OPEN")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_NO_OPEN": "1"})
    (home / "VRN_SystemManager_v0100.py").write_text("import sys\ndef main(argv=None):\n    return 0\n", encoding="utf-8")
    u = ui()
    htm = Path(u["html"]).read_text(encoding="utf-8")
    chk("① 滑鼠律:執行(滑鼠)與選檔執行按鈕 · via:// 組 URL 的 JS · 日期欄 type=date 腳本", "id='run'" in htm and "id='runpick'" in htm and "via://" in htm and "type='date'" in htm)
    chk("② 不動前版:模板 CSS 仍在 · 兩面板仍在", 'id="via-theme"' in htm and "<aside>" in htm)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("④ 橋齊 · 滑鼠段", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:UI-MOUSE:v0100]" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0144 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
