#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 精簡面板：選檔與核對；其他既有動作轉交 v0105。"""
from __future__ import annotations
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

HERE=Path(__file__).resolve().parent
CONFIG=HERE/"VRN2_UIAction_Config.json"
SELECTION=HERE/"VRN2_SelectedInput.json"
PRIOR=HERE/"VRN2_UIAction_v0105.py"


def pick_reports(config):
    import tkinter as tk
    from tkinter import filedialog,messagebox
    app=tk.Tk();app.withdraw()
    try:
        paths=filedialog.askopenfilenames(title="選擇 VRN-2 個股 PDF 報告",filetypes=[("PDF reports","*.pdf")])
        if not paths:return 0
        destination=Path(config["v2"])/"selected_reports"/dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        destination.mkdir(parents=True,exist_ok=False)
        for p in paths:
            source=Path(p).resolve()
            if not source.is_file() or source.suffix.lower()!=".pdf":raise ValueError("非 PDF 報告")
            target=destination/source.name
            if target.exists():raise ValueError("選取了不同資料夾的同名 PDF；請分批選取")
            shutil.copy2(source,target)
        SELECTION.write_text(json.dumps({"input":str(destination),"count":len(paths)},ensure_ascii=False,indent=2),encoding="utf-8")
        messagebox.showinfo("VRN-2",f"已選擇 {len(paths)} 份報告。按「核對報告」開始。")
    finally:app.destroy()
    return 0


def audit_reports(config):
    selected=json.loads(SELECTION.read_text(encoding="utf-8")) if SELECTION.is_file() else {}
    env=dict(os.environ)
    if selected.get("input"):env["VIA_VRN_INPUT"]=selected["input"]
    launcher=Path(config["launcher"]).resolve()
    if not launcher.is_file():raise FileNotFoundError(launcher)
    py=config.get("python") or sys.executable
    ps=shutil.which("pwsh")
    if os.name=="nt" and ps:
        def quote(s):return "'"+str(s).replace("'","''")+"'"
        subprocess.Popen([ps,"-NoExit","-Command","& "+quote(py)+" "+quote(launcher)],env=env,cwd=str(HERE))
    else:
        subprocess.Popen([py,str(launcher)],env=env,cwd=str(HERE))
    return 0


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    uri=next((s for s in args if s.startswith("vrn2://")),"")
    action=urllib.parse.urlsplit(uri).netloc
    if action in ("pick","audit"):
        config=json.loads(CONFIG.read_text(encoding="utf-8"))
        return pick_reports(config) if action=="pick" else audit_reports(config)
    if not PRIOR.is_file():raise FileNotFoundError(PRIOR)
    return subprocess.run([sys.executable,str(PRIOR)]+args,cwd=str(HERE)).returncode

if __name__=="__main__":
    raise SystemExit(main())
