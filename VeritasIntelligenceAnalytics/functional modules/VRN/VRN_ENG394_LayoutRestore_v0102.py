"""Candidate v0102: additive pdfplumber font evidence for ENG394.

VCGC entry only. Prior layout is preserved; font evidence is not document acceptance.
Eight local adapters are lazy and opt-in. No automatic installs or DPI escalation.
Native metadata, font-name inference and image estimates remain distinct.
Central registration / Windows and corpus certification are pending.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import re
import statistics
import sys
import tempfile
import time

VERSION = 'v0102'
HERE = Path(__file__).resolve().parent
_STEM = 'VRN_ENG394_LayoutRestore'
def _vnum(q):
    m = re.search(r'_v(\d+)$', q.stem)
    return int(m.group(1)) if m else -1
_PRIOR_PATH = max((q for q in HERE.glob(_STEM + '_v*.py') if 0 <= _vnum(q) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / (_STEM + '_v0100.py'))   # the prior this tail was cut from
TEMP_ROOT = Path(tempfile.gettempdir()) / 'VIA' / 'VRN' / 'font-evidence'
FONT_BOLD_PATTERN = r'(?i)(bold|semibold|demibold|black|heavy)'
MAX_IMAGE_PIXELS = 30_000_000
OCR_TIMEOUT_SECONDS = 60
SUMMARY_SENTENCES = 5
DEPENDENCIES = {
 'summarizer':HERE/'VRN_ENG062_SummarizerV1_v0103.py',
 'valuation':HERE/'VRN_ENG395_ValuationMethodLexicon_v0100.py',
 'rating':HERE.parents[1]/'supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0116.py',
}
REGISTRY = {
 'pdfplumber': {'module':'pdfplumber','distribution':'pdfplumber','license':'MIT','role':'primary native chars/fontname/size','lineage':'pdfminer'},
 'pdfminer': {'module':'pdfminer','distribution':'pdfminer.six','license':'MIT','role':'native char diagnostic','lineage':'pdfminer'},
 'fonttools': {'module':'fontTools','distribution':'fonttools','license':'MIT','role':'font-file weight metadata','lineage':'font-file'},
 'pymupdf': {'module':'fitz','distribution':'PyMuPDF','license':'AGPL-3.0 OR commercial','role':'native span metadata crosscheck','lineage':'mupdf'},
 'pdfium': {'module':'pypdfium2','distribution':'pypdfium2','license':'Apache-2.0 OR BSD-3-Clause; PDFium third-party notices','role':'native font size/weight diagnostic','lineage':'pdfium'},
 'opencv': {'module':'cv2','distribution':'opencv-python','license':'Apache-2.0 (4.5+)','role':'image components; not exact font weight','lineage':'image'},
 'pillow': {'module':'PIL','distribution':'Pillow','license':'MIT-CMU','role':'crop/image geometry; not exact font weight','lineage':'image'},
 'tesseract': {'module':'pytesseract','distribution':'pytesseract','license':'Apache-2.0','role':'OCR word boxes; font attributes unknown','lineage':'tesseract'},
}
# ===== [VIA:ACCEL-BRIDGE:v0100] =====
VIA_ACCEL = None
ACCEL_ERROR = None
try:
    for _root in HERE.parents:
        if (_root / 'supportive modules' / 'VIA_SuperAccel_Module.py').exists():
            sys.path.insert(0, str(_root / 'supportive modules'))
            break
    import VIA_SuperAccel_Module as VIA_ACCEL
except ImportError as _exc:
    ACCEL_ERROR = str(_exc)
# ===== [VIA:ACCEL-BRIDGE:END] =====

def prior():
    name = '_vrn394_font_prior'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, _PRIOR_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def probe():
    result = {}
    for name, spec in REGISTRY.items():
        available = importlib.util.find_spec(spec['module']) is not None
        try:
            version = importlib.metadata.version(spec['distribution'])
        except importlib.metadata.PackageNotFoundError:
            version = None
        result[name] = dict(spec, available=available, installed_version=version,
                            status='AVAILABLE_NOT_CERTIFIED' if available else 'MISSING')
    return result

def font_hint(name):
    return True if re.search(FONT_BOLD_PATTERN, name or '') else None

def extract_plumber(path, page_number):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[page_number - 1]
        rows = [{'text':c.get('text',''), 'bbox':[c['x0'],c['top'],c['x1'],c['bottom']],
                 'size_pt':c.get('size'), 'fontname':c.get('fontname'),
                 'bold':font_hint(c.get('fontname')), 'bold_evidence':'fontname_inference',
                 'rotation_upright':c.get('upright')} for c in page.chars]
        page.close()
        return rows

def extract_miner(path, page_number):
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTChar, LTContainer
    rows = []
    def visit(node, height):
        if isinstance(node, LTChar):
            x0,y0,x1,y1 = node.bbox
            rows.append({'text':node.get_text(),'bbox':[x0,height-y1,x1,height-y0],
                         'size_pt':node.size,'fontname':node.fontname,
                         'bold':font_hint(node.fontname),'bold_evidence':'fontname_inference'})
        elif isinstance(node, LTContainer):
            for child in node:
                visit(child, height)
    for page in extract_pages(path, page_numbers=[page_number-1]):
        visit(page, page.height)
    return rows

def extract_mupdf(path, page_number):
    import fitz
    with fitz.open(path) as doc:
        rows = []
        for block in doc[page_number-1].get_text('dict').get('blocks',[]):
            for line in block.get('lines',[]):
                for span in line['spans']:
                    rows.append({'text':span['text'],'bbox':list(span['bbox']),
                                 'size_pt':span['size'],'fontname':span['font'],
                                 'bold':bool(span['flags'] & 16),
                                 'bold_evidence':'pdf_font_flag_not_visual_guarantee'})
        return rows

def extract_pdfium(path, page_number):
    import pypdfium2 as pdfium
    import pypdfium2.raw as raw
    doc = pdfium.PdfDocument(path)
    page = text = None
    try:
        page = doc[page_number-1]
        text = page.get_textpage()
        height = page.get_height()
        rows = []
        for i in range(text.count_chars()):
            x0,y0,x1,y1 = text.get_charbox(i)
            weight = raw.FPDFText_GetFontWeight(text.raw,i)
            rows.append({'text':text.get_text_range(i,1),'bbox':[x0,height-y1,x1,height-y0],
                         'size_pt':raw.FPDFText_GetFontSize(text.raw,i),'fontname':None,
                         'weight':weight if weight>0 else None,
                         'bold':weight>=700 if weight>0 else None,'bold_evidence':'pdfium_font_weight'})
        return rows
    finally:
        if text is not None: text.close()
        if page is not None: page.close()
        doc.close()

def extract_fonttools(path, page_number):
    from fontTools.ttLib import TTFont
    with TTFont(path, lazy=True) as font:
        weight = font['OS/2'].usWeightClass if 'OS/2' in font else None
        return [{'text':None,'bbox':None,'size_pt':None,'weight':weight,
                 'bold':weight>=700 if weight is not None else None,
                 'bold_evidence':'font_file_OS2','note':'Not mapped to PDF font until identity matched'}]

def image_open(path):
    from PIL import Image
    image = Image.open(path)
    if image.width*image.height > MAX_IMAGE_PIXELS:
        image.close()
        raise ValueError('Image exceeds configured pixel budget')
    return image

def extract_pillow(path, page_number):
    with image_open(path) as image:
        return [{'text':None,'bbox':[0,0,image.width,image.height],'bbox_unit':'pixel',
                 'size_pt':None,'bold':None,'bold_evidence':'unknown_image',
                 'note':'Image geometry only; no exact font inference'}]

def extract_opencv(path, page_number):
    import cv2
    import numpy as np
    with image_open(path) as image:
        gray = np.asarray(image.convert('L'))
    _, binary = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    count,labels,stats,centroids = cv2.connectedComponentsWithStats(binary,8)
    return [{'text':None,'bbox':[int(x),int(y),int(x+w),int(y+h)],'bbox_unit':'pixel',
             'size_pt':None,'bold':None,'bold_evidence':'unknown_image',
             'ink_area_pixels':int(area)} for x,y,w,h,area in stats[1:]]

def extract_tesseract(path, page_number):
    import pytesseract
    with image_open(path) as image:
        d = pytesseract.image_to_data(image,output_type=pytesseract.Output.DICT,timeout=OCR_TIMEOUT_SECONDS)
    rows=[]
    for i,t in enumerate(d['text']):
        if t.strip():
            x,y,w,h=(d[k][i] for k in ['left','top','width','height'])
            rows.append({'text':t,'bbox':[x,y,x+w,y+h],'bbox_unit':'pixel',
                         'size_pt':None,'bold':None,'confidence':float(d['conf'][i]),
                         'bold_evidence':'unknown_ocr','note':'Language defaults to installed Tesseract default; not CJK certified'})
    return rows

def adapter(name,path,page_number=1):
    handlers={'pdfplumber':extract_plumber,'pdfminer':extract_miner,'pymupdf':extract_mupdf,
              'pdfium':extract_pdfium,'fonttools':extract_fonttools,'opencv':extract_opencv,
              'pillow':extract_pillow,'tesseract':extract_tesseract}
    if name not in handlers: raise ValueError('Unknown adapter')
    start=time.monotonic()
    try:
        rows=handlers[name](Path(path),page_number)
        state='EXTRACTED' if rows else 'NODATA'
        error=None
    except Exception as exc:
        rows=[];state='FAILED';error=f'{type(exc).__name__}: {exc}'
    return {'adapter':name,'lineage':REGISTRY[name]['lineage'],'state':state,'error':error,
            'elapsed_seconds':time.monotonic()-start,'items':rows,'page':page_number,
            'accepted':False,'note':'Extraction is not correctness certification'}

def attach_evidence(layout,path,root=None):
    """Add per-page references, never mutate old classifications or discard text."""
    digest=file_hash(path)
    target=Path(root or TEMP_ROOT)/digest/VERSION
    target.mkdir(parents=True,exist_ok=True)
    for page in layout.get('pages',[]):
        result=adapter('pdfplumber',path,page['page'])
        result['source_sha256']=digest
        sizes=[round(c['size_pt'],2) for c in result['items'] if c.get('text','').strip() and c.get('size_pt')]
        result['dominant_body_size_candidate_pt']=statistics.mode(sizes) if sizes else None
        result['body_size_state']='CANDIDATE_NOT_SEMANTICALLY_VERIFIED'
        result['engine_sha256']=file_hash(__file__)
        result['dependencies']=probe()['pdfplumber']
        fd,name=tempfile.mkstemp(prefix=f"p{page['page']}-",suffix='.json',dir=target)
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False)
        final=target/f"page-{page['page']}.json"
        os.replace(name,final)
        page['font_evidence']={'path':str(final),'sha256':file_hash(final),'state':result['state'],
                               'primary':'pdfplumber','source_sha256':digest}
    layout['font_extension']={'version':VERSION,'central_registration':'PENDING',
                             'accel_bridge_loaded':VIA_ACCEL is not None,'accel_error':ACCEL_ERROR,
                             'dpi_escalation':'NEVER_AUTOMATIC;350 only after failed lower stages'}
    return layout

def restore_pdf(path,pages='1'):
    result=attach_evidence(prior().restore_pdf(Path(path),pages),path)
    return attach_language(result)

def load_dependency(key):
    path=DEPENDENCIES[key]
    name='_vrn_font_dep_'+key
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name]

def attach_language(result):
    """Owner dictionaries handle matches; summary never authoritatively rewrites numbers."""
    pages=result.get('pages',[])
    if not pages:return result
    first=next((p for p in pages if p.get('page')==1),None)
    if first is None:return result
    sources=[{'text':x.get('text',''),'anchor':x.get('anchor'),'no':x.get('no')}
             for x in first.get('body',[]) if x.get('text')]
    info_text='\n'.join(json.dumps(t,ensure_ascii=False) for t in first.get('info',[]))
    body_text='\n'.join(x['text'] for x in sources)
    panel={'body_side':'left','information_side':'right','summary_area':'separate',
           'dependencies':{k:{'path':str(p),'sha256':file_hash(p)} for k,p in DEPENDENCIES.items()},
           'dictionary_candidates':[],'summary':{'state':'HOLD_UNVERIFIED_BODY','sentences':[]}}
    try:
        rating=load_dependency('rating')
        valuation=load_dependency('valuation').Matcher()
        for zone,text in [('information',info_text),('body',body_text)]:
            panel['dictionary_candidates'].append({'zone':zone,'rating':rating.rating_of(text),
                                                    'valuation':valuation.match(text),
                                                    'status':'CANDIDATE_REQUIRES_CONTEXT'})
        verified=result.get('verdict')=='GREEN' and result.get('completeness',{}).get('verdict')=='GREEN'
        if verified and body_text.strip():
            mod=load_dependency('summarizer')
            nlp=mod.CategorySentenceExtractor().extract(body_text)
            # Existing local rule mode; do not fetch model or market data.
            selected=mod.ExtractiveSummarizer()._simple_summarize(body_text,SUMMARY_SENTENCES)
            sentences=[]
            for text in selected:
                owners=[s for s in sources if text in s['text']]
                if not owners:raise ValueError('Summary has no exact source anchor')
                sentences.append({'text':text,'anchors':[{'anchor':s['anchor'],'no':s['no']} for s in owners]})
            panel['summary']={'state':'EXTRACTIVE_SOURCE_LINKED' if sentences else 'NODATA',
                              'sentences':sentences,'nlp_categories':nlp,
                              'method':'ENG062 local keyword/category mode; no generative claims'}
    except Exception as exc:
        panel['error']=f'{type(exc).__name__}: {exc}'
        panel['summary']={'state':'BLOCKED','sentences':[]}
    first['first_page_panel']=panel
    return result

def page_html(docs):
    rendered=prior().page_html(docs)
    panels=[]
    for doc in docs:
        first=next((p for p in doc.get('pages',[]) if p.get('page')==1),{})
        panel=first.get('first_page_panel')
        if not panel:continue
        summary=panel['summary']
        lines=''.join('<li>'+html.escape(s['text'])+'<small> '+html.escape(str(s['anchors']))+'</small></li>' for s in summary['sentences'])
        panels.append('<section class="via-note"><h3>獨立摘要區 · '+html.escape(doc.get('name',''))+'</h3><p>'+html.escape(summary['state'])+'</p><ul>'+lines+'</ul><details><summary>RATING / VALUATION 原引擎候選（待語境確認）</summary><pre>'+html.escape(json.dumps(panel['dictionary_candidates'],ensure_ascii=False,indent=2))+'</pre></details></section>')
    extra=''.join(panels)
    return rendered.replace('</body>',extra+'</body>') if '</body>' in rendered else rendered+extra

def selftest():
    """Synthetic contract tests; not real broker PDF acceptance."""
    from reportlab.pdfgen.canvas import Canvas
    checks=[]
    with tempfile.TemporaryDirectory(prefix='via-font-test-') as tmp:
        path=Path(tmp)/'font.pdf'
        canvas=Canvas(str(path),pagesize=(400,500))
        canvas.setFont('Helvetica-Bold',20);canvas.drawString(20,460,'TITLE')
        canvas.setFont('Helvetica',10);canvas.drawString(20,420,'Body source 123.45')
        canvas.save()
        base=adapter('pdfplumber',path)
        checks.append(('pdfplumber_native',base['state']=='EXTRACTED'))
        checks.append(('bold_title',any(c['text']=='T' and c['bold'] is True and abs(c['size_pt']-20)<.1 for c in base['items'])))
        checks.append(('unknown_not_false',font_hint('SubsetX') is None))
        for name in ['pdfminer','pymupdf','pdfium']:
            r=adapter(name,path)
            checks.append((name+'_native',r['state']=='EXTRACTED' and any(c.get('size_pt') and abs(c['size_pt']-20)<.1 for c in r['items'])))
        old={'pages':[{'page':1,'body':[{'text':'unchanged'}]}],'verdict':'YELLOW'}
        new=attach_evidence(old,path,Path(tmp)/'temp')
        checks.append(('additive_layout',new['pages'][0]['body']==[{'text':'unchanged'}] and new['verdict']=='YELLOW'))
        checks.append(('temp_evidence',Path(new['pages'][0]['font_evidence']['path']).is_file()))
        checks.append(('same_lineage',REGISTRY['pdfplumber']['lineage']==REGISTRY['pdfminer']['lineage']))
        checks.append(('no_auto_ocr',new['font_extension']['dpi_escalation'].startswith('NEVER')))
        # Integration with actual predecessor layout, not only a fabricated result.
        integrated=restore_pdf(path,'1')
        checks.append(('prior_engine_integration',bool(integrated['pages'][0].get('font_evidence'))))
        checks.append(('first_page_panel',bool(integrated['pages'][0].get('first_page_panel'))))
        import reportlab
        font=Path(reportlab.__file__).parent/'fonts/VeraBd.ttf'
        checkfont=adapter('fonttools',font)
        checks.append(('fonttools_weight',checkfont['state']=='EXTRACTED' and checkfont['items'][0]['bold'] is True))
        from PIL import Image
        pic=Path(tmp)/'sample.png'
        Image.new('L',(20,30),255).save(pic)
        checks.append(('pillow_geometry',adapter('pillow',pic)['items'][0]['bbox']==[0,0,20,30]))
        checks.append(('corrupt_pdf_fails',adapter('pdfplumber',pic)['state']=='FAILED'))
        language={'name':'synthetic','verdict':'GREEN','completeness':{'verdict':'GREEN'},'pages':[{'page':1,'info':[], 'body':[{'text':'營收成長20%，主要受惠需求增加及產品升級。','anchor':'A1','no':'1'}]}]}
        attach_language(language)
        checks.append(('summary_source_anchor',language['pages'][0]['first_page_panel']['summary']['state']=='EXTRACTIVE_SOURCE_LINKED'))
        checks.append(('predecessor_selftest',prior().selftest()==0))
    print(json.dumps({'version':VERSION,'scope':'SYNTHETIC_ONLY','checks':checks,'failed':sum(not ok for _,ok in checks),'probe':probe()},ensure_ascii=False))
    return int(any(not ok for _,ok in checks))

def __getattr__(name):
    """PEP 562 轉接(尾版律 TAILAPI):本版沒蓋的名稱(含呼叫端在用的單底線私名)一律轉前版鏈;只擋 dunder。"""
    if name.startswith('__') and name.endswith('__'):
        raise AttributeError(name)
    return getattr(prior(), name)


def main():
    if os.environ.get('VIA_FROM_VCGC')!='YES':
        print('Use VCGC entry');return 2
    if '--selftest' in sys.argv[1:]:return selftest()
    if sys.argv[1:]==['--font-probe']:
        print(json.dumps(probe(),ensure_ascii=False));return 0
    # Preserve prior text/--dir/--in/--pages dispatch and output contracts.
    host=prior().PRIOR
    saved=host.restore_pdf
    saved_html=host.page_html
    host.restore_pdf=restore_pdf
    host.page_html=page_html
    try:
        return prior().main()
    finally:
        host.restore_pdf=saved
        host.page_html=saved_html

if __name__=='__main__':
    raise SystemExit(main())
