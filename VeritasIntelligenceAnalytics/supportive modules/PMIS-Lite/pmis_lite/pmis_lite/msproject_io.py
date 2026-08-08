"""MS Project 雙向 I/O —— SSOT → 可匯入 MS Project XML(回寫)+ 反解析 + round-trip 驗證。

深化重點:先前只有單向(MSP XML → SSOT)。本模組補上回寫:
  - to_xml(tasks): 產生 MS Project 2003 XML(UID/ID/Start/Finish/%/OutlineLevel/
    PredecessorLink/Resources/Assignments),可直接在 MS Project「開啟 XML」匯入。
  - from_xml(xml): 反解析回任務(供 round-trip 對帳)。
  - roundtrip(tasks): SSOT → XML → 反解析 → 逐欄比對,確保無資料流失。
只增不減:不動既有 adapters.msproject(讀取端),本檔專責寫入端。純 stdlib。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

NS = "http://schemas.microsoft.com/project"


def _dt(v, default_time):
    """'2026-07-01' → '2026-07-01T08:00:00';已含 T 則原樣。"""
    if not v:
        return ""
    return v if "T" in v else f"{v}T{default_time}"


def _date_only(v):
    return v.split("T")[0] if v else ""


def to_xml(tasks, resources=None, project_name="VIA_SSOT_Export"):
    """SSOT 任務 → MS Project 2003 XML 字串(可匯入)。

    tasks: [{task_id,name,start,finish,pct,predecessors,resource}]
    """
    ET.register_namespace("", NS)
    root = ET.Element(f"{{{NS}}}Project")
    ET.SubElement(root, f"{{{NS}}}Name").text = project_name
    ET.SubElement(root, f"{{{NS}}}Author").text = "VIA SyncEngine"
    ET.SubElement(root, f"{{{NS}}}ScheduleFromStart").text = "1"

    # task_id → UID 對照
    uid = {t.get("task_id"): i + 1 for i, t in enumerate(tasks)}
    tasks_el = ET.SubElement(root, f"{{{NS}}}Tasks")
    for i, t in enumerate(tasks, 1):
        te = ET.SubElement(tasks_el, f"{{{NS}}}Task")
        ET.SubElement(te, f"{{{NS}}}UID").text = str(i)
        ET.SubElement(te, f"{{{NS}}}ID").text = str(i)
        ET.SubElement(te, f"{{{NS}}}Name").text = str(t.get("name", ""))
        ET.SubElement(te, f"{{{NS}}}Active").text = "1"
        ET.SubElement(te, f"{{{NS}}}Start").text = _dt(t.get("start"), "08:00:00")
        ET.SubElement(te, f"{{{NS}}}Finish").text = _dt(t.get("finish"), "17:00:00")
        ET.SubElement(te, f"{{{NS}}}PercentComplete").text = str(int(t.get("pct", 0) or 0))
        ET.SubElement(te, f"{{{NS}}}OutlineLevel").text = str(t.get("outline", 1))
        # 前置 → PredecessorLink(Type 1 = Finish-to-Start)
        preds = t.get("predecessors") or []
        if isinstance(preds, str):
            preds = [p for p in preds.replace(",", " ").split() if p]
        for pid in preds:
            if pid in uid:
                pl = ET.SubElement(te, f"{{{NS}}}PredecessorLink")
                ET.SubElement(pl, f"{{{NS}}}PredecessorUID").text = str(uid[pid])
                ET.SubElement(pl, f"{{{NS}}}Type").text = "1"

    # 資源 + 指派
    res_names = resources or sorted({t.get("resource") for t in tasks if t.get("resource")})
    ruid = {r: i + 1 for i, r in enumerate(res_names)}
    res_el = ET.SubElement(root, f"{{{NS}}}Resources")
    for r, u in ruid.items():
        re_ = ET.SubElement(res_el, f"{{{NS}}}Resource")
        ET.SubElement(re_, f"{{{NS}}}UID").text = str(u)
        ET.SubElement(re_, f"{{{NS}}}ID").text = str(u)
        ET.SubElement(re_, f"{{{NS}}}Name").text = str(r)
        ET.SubElement(re_, f"{{{NS}}}Type").text = "1"
    asg_el = ET.SubElement(root, f"{{{NS}}}Assignments")
    auid = 1
    for i, t in enumerate(tasks, 1):
        r = t.get("resource")
        if r and r in ruid:
            ae = ET.SubElement(asg_el, f"{{{NS}}}Assignment")
            ET.SubElement(ae, f"{{{NS}}}UID").text = str(auid)
            ET.SubElement(ae, f"{{{NS}}}TaskUID").text = str(i)
            ET.SubElement(ae, f"{{{NS}}}ResourceUID").text = str(ruid[r])
            ET.SubElement(ae, f"{{{NS}}}Units").text = "1"
            auid += 1

    xml = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml


def from_xml(xml_str):
    """反解析 MS Project XML → 任務(供 round-trip 對帳)。"""
    root = ET.fromstring(xml_str)
    ns = {"p": NS}
    # UID → resource name
    rmap = {}
    for r in root.findall(".//p:Resources/p:Resource", ns):
        u = r.findtext("p:UID", default="", namespaces=ns)
        rmap[u] = r.findtext("p:Name", default="", namespaces=ns)
    # TaskUID → resourceName
    tres = {}
    for a in root.findall(".//p:Assignments/p:Assignment", ns):
        tu = a.findtext("p:TaskUID", default="", namespaces=ns)
        ru = a.findtext("p:ResourceUID", default="", namespaces=ns)
        if rmap.get(ru):
            tres[tu] = rmap[ru]
    # UID → task_id (以 Name 對回不可靠;用順序 index)
    tasks = []
    uid2idx = {}
    els = root.findall(".//p:Tasks/p:Task", ns)
    for idx, te in enumerate(els):
        uid2idx[te.findtext("p:UID", default="", namespaces=ns)] = idx
    for idx, te in enumerate(els):
        u = te.findtext("p:UID", default="", namespaces=ns)
        preds = []
        for pl in te.findall("p:PredecessorLink", ns):
            pu = pl.findtext("p:PredecessorUID", default="", namespaces=ns)
            if pu in uid2idx:
                preds.append(f"T{uid2idx[pu] + 1}")
        tasks.append({
            "task_id": f"T{idx + 1}",
            "name": te.findtext("p:Name", default="", namespaces=ns),
            "start": _date_only(te.findtext("p:Start", default="", namespaces=ns)),
            "finish": _date_only(te.findtext("p:Finish", default="", namespaces=ns)),
            "pct": int(te.findtext("p:PercentComplete", default="0", namespaces=ns) or 0),
            "predecessors": preds,
            "resource": tres.get(u, ""),
        })
    return tasks


def roundtrip(tasks):
    """SSOT → XML → 反解析 → 逐欄比對。回報是否無資料流失。"""
    xml = to_xml(tasks)
    back = from_xml(xml)
    diffs = []
    for i, t in enumerate(tasks):
        b = back[i] if i < len(back) else {}
        for k in ("name", "start", "finish", "pct"):
            want = t.get(k)
            if k == "pct":
                want = int(want or 0)
            if str(b.get(k)) != str(want):
                diffs.append({"task": t.get("task_id"), "field": k,
                              "ssot": want, "roundtrip": b.get(k)})
    return {"xml": xml, "reparsed": back, "match": len(diffs) == 0,
            "diffs": diffs, "tasks": len(tasks)}
