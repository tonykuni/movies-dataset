"""Compound figure panels, shared legends and isolated, registered OCR reuse.
OCR is conditional on local language availability; no model download or cloud call.
"""
from __future__ import annotations
import copy
import json
import re
import shutil
import subprocess
from pathlib import Path
from . import VIA_ACCEL
from .SUP_MDL743_LayoutCommon_v0100 import PARAMS, RX, def_id, def_inside, def_number, def_context

# def 01_PARAMETERS — no hidden figure/OCR configuration outside the SSOT.
OCR_CACHE_NAME = "figure_ocr.json"
# [VIA:ACCEL-BRIDGE] Inherited from the owning GenericLayoutHub runtime.


def def_runs(indices):
    runs=[]
    for index in indices:
        if not runs or index>runs[-1][-1]+1:runs.append([index])
        else:runs[-1].append(index)
    return runs


def def_compact_assets(assets):
    """Image fragments/logos are retained as evidence, not counted as complete charts."""
    figures=[];fragments=[]
    for asset in sorted((a for a in assets if a["kind"]=="FIGURE"),key=lambda a:-(a["bbox"][2]-a["bbox"][0])*(a["bbox"][3]-a["bbox"][1])):
        b=asset["bbox"]
        parent=next((f for f in figures if f["page"]==asset["page"] and f["bbox"][0]<=b[0]<=b[2]<=f["bbox"][2] and f["bbox"][1]<=b[1]<=b[3]<=f["bbox"][3]),None)
        if parent or min(b[2]-b[0],b[3]-b[1])<PARAMS["figure_min_size"]:
            item=copy.deepcopy(asset);item["parent_id"]=parent["id"] if parent else None;item["state"]="RETAINED_IMAGE_FRAGMENT";fragments.append(item)
            if parent:parent["source_ids"]+=asset["source_ids"]
        else:figures.append(copy.deepcopy(asset))
    return figures,fragments


def def_split_canvas(image, bbox):
    """Empty gutters must cross the plot; a continuous dual-axis plot blocks a cut."""
    import numpy as np
    pixels=np.asarray(image.convert("RGB"),dtype=float)
    h,w=pixels.shape[:2]
    if min(h,w)<PARAMS["figure_min_size"]:
        return {"panels":[bbox],"shared_legend":[],"decision":"TOO_SMALL"}
    corners=np.vstack([pixels[0,:],pixels[-1,:],pixels[:,0],pixels[:,-1]])
    background=np.median(corners,axis=0)
    mask=np.max(np.abs(pixels-background),axis=2)>PARAMS["figure_background_delta"]
    top,bottom=0,h;legend=[]
    blank_rows=def_runs(np.flatnonzero(mask.mean(axis=1)<=PARAMS["figure_foreground_fraction"]))
    for run in blank_rows:
        if len(run)<max(2,h*PARAMS["figure_gutter_ratio"]):continue
        if run[-1]<h*PARAMS["figure_title_ratio"] and mask[:run[0],int(w*.45):int(w*.55)].any():
            legend.append([0,0,w,run[0]]);top=run[-1]+1
        elif run[-1]>h*PARAMS["axis_bottom_ratio"] and run[0]>h*.5 and mask[run[-1]+1:,int(w*.45):int(w*.55)].any():
            legend.append([0,run[-1]+1,w,h]);bottom=run[0]
    core=mask[top:bottom]
    gaps=def_runs(np.flatnonzero(core.mean(axis=0)<=PARAMS["figure_foreground_fraction"])) if core.size else []
    gaps=[g for g in gaps if g[0]>w*.25 and g[-1]<w*.75 and len(g)>=w*PARAMS["figure_gutter_ratio"]]
    cut=int(sum(max(gaps,key=len))/len(max(gaps,key=len))) if gaps else None
    panels=[[0,top,cut,bottom],[cut,top,w,bottom]] if cut else [[0,top,w,bottom]]
    # A full horizontal gutter can also separate upper/lower panel rows.
    for run in blank_rows:
        if h*.25<run[0]<run[-1]<h*.75 and len(run)>=h*PARAMS["figure_gutter_ratio"]:
            cy=int(sum(run)/len(run));panels=[q for p in panels for q in ([p[0],p[1],p[2],cy],[p[0],cy,p[2],p[3]])];break
    def coordinates(rect):
        return [bbox[0]+rect[0]/w*(bbox[2]-bbox[0]),bbox[1]+rect[1]/h*(bbox[3]-bbox[1]),bbox[0]+rect[2]/w*(bbox[2]-bbox[0]),bbox[1]+rect[3]/h*(bbox[3]-bbox[1])]
    return {"panels":[coordinates(p) for p in panels],"shared_legend":[coordinates(p) for p in legend],"decision":"EMPTY_GUTTER" if len(panels)>1 else "CONTINUOUS_PLOT_KEEP"}


def def_ocr_roles(items, bbox):
    """Assign geometric roles; pairing is an auditable candidate, not a digitized series."""
    roles={k:[] for k in ("title_units","x_axis","left_y_axis","right_y_axis","legend","data_labels")}
    for word in sorted(items,key=lambda w:(w["bbox"][1],w["bbox"][0])):
        x=((word["bbox"][0]+word["bbox"][2])/2-bbox[0])/max(bbox[2]-bbox[0],1)
        y=((word["bbox"][1]+word["bbox"][3])/2-bbox[1])/max(bbox[3]-bbox[1],1)
        numeric=def_number(word["text"]) is not None
        role="title_units" if y<PARAMS["figure_title_ratio"] else "x_axis" if y>=PARAMS["axis_bottom_ratio"] else "left_y_axis" if x<PARAMS["axis_left_ratio"] and numeric else "right_y_axis" if x>PARAMS["axis_right_ratio"] and numeric else "data_labels" if numeric else "legend"
        roles[role].append(copy.deepcopy(word))
    pairs=[]
    for value in roles["data_labels"]:
        candidates=sorted(roles["x_axis"],key=lambda label:abs(sum(label["bbox"][::2])/2-sum(value["bbox"][::2])/2))
        if candidates:
            label=candidates[0];distance=abs(sum(label["bbox"][::2])/2-sum(value["bbox"][::2])/2)
            if distance<=(bbox[2]-bbox[0])*PARAMS["label_pair_tolerance"]:
                pairs.append({"label_id":label["id"],"value_id":value["id"],"state":"CANDIDATE_SERIES_UNASSIGNED"})
    return {"roles":roles,"pair_candidates":pairs}


def def_figure_metadata(asset, context, panels):
    captions=[x for x in context["above"]+context["below"] if RX["caption"].match(x["text"])]
    sources=[x for x in context["below"] if RX["source"].match(x["text"])]
    parent=" ".join(x["text"] for x in captions)
    labels=re.findall(r'([^：:]+?)\s*[（(](?:左|右|上|下)(?:圖)?[）)]',parent)
    out=[]
    for i,panel in enumerate(panels):
        local=[c for c in captions if def_inside(c["bbox"],[panel[0],0,panel[2],panel[3]])]
        out.append({"id":def_id("FIG",asset["id"],i),"parent_id":asset["id"],"bbox":panel,
                    "caption":local[0]["text"] if len(captions)>1 and local else labels[i] if len(labels)==len(panels) else parent,
                    "caption_relation":"INDEPENDENT" if len(captions)>1 and local else "SHARED_PARENT",
                    "sources":copy.deepcopy(sources)})
    return out


def def_ocr_status():
    executable=shutil.which("tesseract")
    if not executable:return {"state":"UNAVAILABLE","reason":"tesseract absent","languages":[]}
    completed=subprocess.run([executable,"--list-langs"],capture_output=True,text=True,timeout=PARAMS["ocr_probe_timeout"])
    languages=[s.strip() for s in completed.stdout.splitlines()[1:] if s.strip()]
    missing=sorted(set(PARAMS["ocr_languages"].split("+"))-set(languages))
    return {"state":"UNAVAILABLE" if missing or completed.returncode else "AVAILABLE","reason":"missing languages: "+",".join(missing) if missing else completed.stderr.strip(),"languages":languages}


def def_figures(document, words, lines, assets, output, core, ocr_status):
    from PIL import Image
    figures=[];page_by={p["physical_page"]:p for p in document["layout"]["pages"]}
    statuses=core.backend_map(core.probe_backends())
    for asset in assets:
        if asset["kind"]!="FIGURE":continue
        page=page_by[asset["page"]];image_path=Path(page.get("image_path") or "")
        result=copy.deepcopy(asset);result["state"]="REVIEW";result["panels"]=[]
        if not image_path.is_file():
            result["issue"]="source image absent";figures.append(result);continue
        with Image.open(image_path) as original:
            scale_x=original.width/page["width"];scale_y=original.height/page["height"]
            box=asset["bbox"];crop=original.crop((int(box[0]*scale_x),int(box[1]*scale_y),int(box[2]*scale_x),int(box[3]*scale_y)))
            if not crop.width or not crop.height:
                result["issue"]="empty image crop";figures.append(result);continue
            split=def_split_canvas(crop,box)
            result["split"]=split;context=def_context(asset,lines,assets);result["context"]=context
            panels=def_figure_metadata(asset,context,split["panels"])
            panels += [{"id":def_id("LEGEND",asset["id"],i),"parent_id":asset["id"],"bbox":b,"caption":"shared legend","sources":[],"shared_legend":True} for i,b in enumerate(split["shared_legend"])]
            for panel in panels:
                b=panel["bbox"];panel_words=[copy.deepcopy(w) for w in words if w["page"]==asset["page"] and def_inside(w["bbox"],b)]
                directory=Path(output)/"figures"/panel["id"];directory.mkdir(parents=True,exist_ok=True)
                picture=directory/"source.png"
                im=original.crop((int(b[0]*scale_x),int(b[1]*scale_y),int(b[2]*scale_x),int(b[3]*scale_y)))
                im.resize((max(1,im.width*PARAMS["figure_upscale"]),max(1,im.height*PARAMS["figure_upscale"]))).save(picture)
                panel["image_path"]=str(picture.resolve())
                panel["ocr_state"]="NATIVE_GEOMETRY" if len(panel_words)>=PARAMS["ocr_min_native_tokens"] else "NOT_RUN"
                if len(panel_words)<PARAMS["ocr_min_native_tokens"]:
                    if ocr_status["state"]!="AVAILABLE":panel["ocr_state"]="UNAVAILABLE";panel["ocr_reason"]=ocr_status["reason"]
                    else:
                        cache=directory/OCR_CACHE_NAME
                        if cache.is_file():
                            ocr=json.loads(cache.read_text());panel["ocr_cache_hit"]=True
                        else:
                            p=core.PageLayout(physical_page=asset["page"],width=b[2]-b[0],height=b[3]-b[1])
                            found=core.run_tesseract_tsv(picture,p,core.EngineConfig(ocr_languages=PARAMS["ocr_languages"]),statuses)
                            ocr={"words":[{"id":def_id("OCR",panel["id"],i),"page":asset["page"],"text":e.raw_text,"bbox":[e.bbox.x0+b[0],e.bbox.y0+b[1],e.bbox.x1+b[0],e.bbox.y1+b[1]],"source":"registered_tesseract","geometry_level":"line"} for i,e in enumerate(found)],"warnings":p.warnings}
                            cache.write_text(json.dumps(ocr,ensure_ascii=False))
                        panel_words+=ocr["words"];panel["ocr_state"]="REVIEW" if ocr["words"] else "NODATA";panel["ocr_warnings"]=ocr["warnings"]
                panel["information"]=def_ocr_roles(panel_words,b);panel["words"]=panel_words
            shared=[p for p in panels if p.get("shared_legend")]
            result["shared_legend_ids"]=[p["id"] for p in shared]
            for panel in panels:
                if not panel.get("shared_legend"):panel["shared_legend_ids"]=result["shared_legend_ids"]
            result["panels"]=panels
        figures.append(result)
    return figures
