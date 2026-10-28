#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111]
"""One focused run, preserving existing caches and avoiding full activation checks."""
from __future__ import annotations
import contextlib,hashlib,importlib.machinery,importlib.util,json,os,sys
from pathlib import Path
from VRN2_Workbench_v0102 import verb

# Exact compatibility path semantics from the supplied manager v0153.
@verb
def compatible_vdf_home(module_path):
    home=Path(os.environ.get('VIA_VRN_SSOT_HOME') or Path(module_path).parent)
    return Path(os.environ.get('VIA_VDF_HOME') or home.parent/'VDF')

@contextlib.contextmanager
@verb
def manager_compatibility(folder):
    original=importlib.machinery.SourceFileLoader.exec_module;applied=[];folder=Path(folder).resolve()
    @verb
    def execute(loader,module):
        path=Path(loader.path)
        if path.parent.resolve()==folder and path.name.startswith('VRN_SystemManager_v'):
            # A later version can replace this with its real definition. No __getattr__ traversal.
            if '_vdf_home' not in vars(module):
                @verb
                def vdf_home(p=str(path)):return compatible_vdf_home(p)
                module._vdf_home=vdf_home;applied.append(path.name)
        return original(loader,module)
    importlib.machinery.SourceFileLoader.exec_module=execute
    try:yield applied
    finally:importlib.machinery.SourceFileLoader.exec_module=original

@verb
def run(root,manager_name='VRN_SystemManager_v0253.py'):
    root=Path(root);folder=root/'functional modules'/'VRN';source=Path(os.environ['VIA_VRN_INPUT']);output=Path(os.environ['VIA_VRN2_JOB_OUTPUT'])
    if not source.is_dir():raise FileNotFoundError(str(source))
    os.environ.update(VIA_NO_OPEN='1',VIA_VRN2_NO_PUSH='1',VIA_VRN_HEALTH_OUT=str(output),VIA_VRN_SSOT_HOME=str(folder),VIA_VRN2_P1_CACHE=str(root/'VIA_Reports'/'vrn2'/'p1_cache'),VIA_VRN2_OCR_CACHE=str(root/'VIA_Reports'/'vrn2'/'ocr_cache'))
    for name in ('p1_cache','ocr_cache'):(root/'VIA_Reports'/'vrn2'/name).mkdir(parents=True,exist_ok=True)
    if str(folder) not in sys.path:sys.path.insert(0,str(folder))
    # Existing isolated OCR bridge is reused. No model download or package install at job startup.
    from VRN2_ContentRepair_v0100 import ocr_environment
    ocr_environment(folder)
    path=folder/manager_name
    with manager_compatibility(folder) as applied:
        spec=importlib.util.spec_from_file_location('vrn2_focused_manager',path);manager=importlib.util.module_from_spec(spec);sys.modules[spec.name]=manager;spec.loader.exec_module(manager)
    print('[計] 聚焦快路徑：沿用擷取／OCR 快取；不重做 envcheck、accelfix、register、Git；_vdf_home 記憶體相容層 '+str(len(applied))+' 個模組',flush=True)
    result=manager.vrn2(['--run'],rep=output,indir=source,open_ui=False)
    return result if isinstance(result,int) else 0
