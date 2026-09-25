"""MS Project adapter。

.mpp 是專屬二進位格式，純 Python 解析困難；最穩的兩條路：
  A) 在 MS Project 內『另存為 XML』(原生功能) → 本 adapter 直接讀（預設，無需 Java）
  B) 安裝 mpxj + JPype 直接讀 .mpp（跨格式最強，但需 Java 執行環境）

本檔實作 A（XML），並把每個 Task 當成一個事件 Record：
  名稱/負責人(資源)/開始/完成/百分比/前置任務 → SSOT。
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

import os
import xml.etree.ElementTree as ET
from typing import Iterable

from ..schema import Record

_NS = {"p": "http://schemas.microsoft.com/project"}


class MSProjectAdapter:
    source_type = "msproject"

    def __init__(self, path: str, audit=None):
        self.path = path
        self.audit = audit

    def _iter_files(self):
        if os.path.isdir(self.path):
            for n in sorted(os.listdir(self.path)):
                if n.lower().endswith(".xml"):
                    yield os.path.join(self.path, n)
        elif self.path.lower().endswith(".xml"):
            yield self.path

    def read(self) -> Iterable[Record]:
        a = self.audit.audit("msproject") if self.audit else None
        for fpath in self._iter_files():
            try:
                tree = ET.parse(fpath)
            except Exception as e:
                if a:

                    a.failures.append((os.path.basename(fpath), f"xml_parse:{e.__class__.__name__}"))
                continue
            root = tree.getroot()

            # 資源對照 (UID → 名稱)
            res = {}
            for r in root.findall(".//p:Resources/p:Resource", _NS):
                uid = (r.findtext("p:UID", default="", namespaces=_NS))
                name = (r.findtext("p:Name", default="", namespaces=_NS))
                if uid:
                    res[uid] = name
            # 任務指派 (TaskUID → ResourceName)
            assign = {}
            for asg in root.findall(".//p:Assignments/p:Assignment", _NS):
                tuid = asg.findtext("p:TaskUID", default="", namespaces=_NS)
                ruid = asg.findtext("p:ResourceUID", default="", namespaces=_NS)
                if tuid and ruid in res:
                    assign.setdefault(tuid, []).append(res[ruid])

            for task in root.findall(".//p:Tasks/p:Task", _NS):
                if a:
                    a.seen += 1
                name = task.findtext("p:Name", default="", namespaces=_NS)
                if not name:
                    if a:

                        a.failures.append(("task", "no_name(摘要列或空任務)"))
                    continue
                tuid = task.findtext("p:UID", default="", namespaces=_NS)
                pct = task.findtext("p:PercentComplete", default="", namespaces=_NS)
                start = task.findtext("p:Start", default="", namespaces=_NS)
                finish = task.findtext("p:Finish", default="", namespaces=_NS)

                rec = Record(source_type=self.source_type)
                rec.title = name
                rec.actor = ";".join(assign.get(tuid, []))
                rec.event_time = (finish or start or "")[:10]
                rec.status = "已結" if pct == "100" else ("進行中" if pct and pct != "0" else "待辦")
                rec.body = f"完成度 {pct}% · 起 {start[:10]} 迄 {finish[:10]}"
                rec.source_ref = f"{os.path.basename(fpath)}::task{tuid}"
                rec.raw_keys = f"pct={pct} | start={start[:10]} | finish={finish[:10]}"
                if a:
                    a.extracted += 1
                yield rec
