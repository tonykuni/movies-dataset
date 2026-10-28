#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE]
# [VIA:ACCEL-BRIDGE:v0111]
"""Normalize supported local inputs to PDF; originals and provenance are retained."""
from __future__ import annotations
import base64,html,os,shutil,subprocess,uuid,zipfile,io
from xml.etree import ElementTree as ET
from pathlib import Path
from VRN2_Workbench_v0102 import verb,file_hash
from VRN2_Reconcile_v0100 import decode_text,word_text,XML_NS

WORD_RENDER_TIMEOUT=120
TEXT_PAGE_SIZE=(595,842)
IMAGE_ASSUMED_DPI=200

@verb
def text_pdf(text,target):
    import fitz,io
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
    from reportlab.lib.styles import ParagraphStyle
    font='VRN2InputCJK';pdfmetrics.registerFont(TTFont(font,io.BytesIO(fitz.Font('cjk').buffer)))
    style=ParagraphStyle('source',fontName=font,fontSize=10,leading=15,wordWrap='CJK')
    story=[]
    for line in text.splitlines() or ['']:
        if line.strip():
            for i in range(0,len(line),1000):story.append(Paragraph(html.escape(line[i:i+1000]).replace(' ','&#160;'),style))
        else:story.append(Spacer(1,8))
    SimpleDocTemplate(str(target),pagesize=TEXT_PAGE_SIZE,leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36).build(story)

@verb
def word_pdf(source,target):
    """Use installed Word with macros disabled, otherwise installed LibreOffice. Never installs."""
    if os.name=='nt' and shutil.which('pwsh'):
        @verb
        def quote(s):return "'"+str(s).replace("'","''")+"'"
        code="$ErrorActionPreference='Stop';$w=$null;$d=$null;try{$w=New-Object -ComObject Word.Application;$w.Visible=$false;$w.DisplayAlerts=0;$w.AutomationSecurity=3;$w.Options.UpdateLinksAtOpen=$false;$d=$w.Documents.Open("+quote(source)+",$false,$true);$d.ExportAsFixedFormat("+quote(target)+",17)}finally{if($d){$d.Close(0)};if($w){$w.Quit()}}"
        result=subprocess.run(['pwsh','-NoLogo','-NoProfile','-EncodedCommand',base64.b64encode(code.encode('utf-16-le')).decode()],capture_output=True,timeout=WORD_RENDER_TIMEOUT)
        if result.returncode==0 and target.is_file():return 'MICROSOFT_WORD_PDF'
    exe=shutil.which('soffice') or shutil.which('libreoffice')
    if exe:
        folder=target.parent/('word_'+uuid.uuid4().hex);folder.mkdir()
        try:
            profile=(folder/'profile').resolve().as_uri()
            result=subprocess.run([exe,'-env:UserInstallation='+profile,'--headless','--convert-to','pdf','--outdir',str(folder),str(source)],capture_output=True,timeout=WORD_RENDER_TIMEOUT)
            produced=folder/(source.stem+'.pdf')
            if result.returncode==0 and produced.is_file():shutil.move(produced,target);return 'LIBREOFFICE_PDF'
        finally:shutil.rmtree(folder,ignore_errors=True)
    raise RuntimeError('Word/PDF 轉換器未就緒：需要已安裝的 Microsoft Word 或 LibreOffice；其他檔案可繼續，不自動安裝')

@verb
def docx_projection(source,target):
    """Fallback retains text, table cells and embedded images; original layout remains unverified."""
    import fitz
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image as PDFImage
    from reportlab.lib.styles import ParagraphStyle
    font='VRN2DocxCJK';pdfmetrics.registerFont(TTFont(font,io.BytesIO(fitz.Font('cjk').buffer)))
    style=ParagraphStyle('docx_source',fontName=font,fontSize=9,leading=13,wordWrap='CJK');story=[];buffers=[]
    with zipfile.ZipFile(source) as z:
        body=ET.fromstring(z.read('word/document.xml')).find('w:body',XML_NS)
        for element in body:
            if element.tag.endswith('}p'):
                text=''.join(n.text or '' for n in element.findall('.//w:t',XML_NS))
                if text:story.append(Paragraph(html.escape(text),style))
                else:story.append(Spacer(1,6))
            elif element.tag.endswith('}tbl'):
                rows=[]
                for tr in element.findall('w:tr',XML_NS):
                    cells=[]
                    for tc in tr.findall('w:tc',XML_NS):
                        text='\n'.join(''.join(n.text or '' for n in p.findall('.//w:t',XML_NS)) for p in tc.findall('.//w:p',XML_NS))
                        cells.append(Paragraph(html.escape(text).replace('\n','<br/>'),style))
                    if cells:rows.append(cells)
                if rows:
                    width=max(map(len,rows));rows=[row+['']*(width-len(row)) for row in rows]
                    table=Table(rows,colWidths=[523/width]*width,hAlign='LEFT');table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.25,'#aaaaaa'),('VALIGN',(0,0),(-1,-1),'TOP')]))
                    story.extend([table,Spacer(1,8)])
        for name in z.namelist():
            if not name.startswith('word/media/') or name.endswith('/'):continue
            from PIL import Image
            data=z.read(name);buffer=io.BytesIO(data);buffers.append(buffer)
            try:
                with Image.open(io.BytesIO(data)) as image:width,height=image.size
                factor=min(523/width,740/height,1);story.append(Paragraph('SOURCE EMBEDDED IMAGE: '+html.escape(name),style));story.append(PDFImage(buffer,width=width*factor,height=height*factor))
            except Exception as exc:raise ValueError('DOCX 內嵌圖無法無損轉換：'+name) from exc
    SimpleDocTemplate(str(target),pagesize=TEXT_PAGE_SIZE,leftMargin=36,rightMargin=36,topMargin=36,bottomMargin=36).build(story)
@verb
def normalize(source,target):
    source=Path(source);target=Path(target);target.parent.mkdir(parents=True,exist_ok=True);extension=source.suffix.lower();notes=[]
    if extension=='.pdf':shutil.copy2(source,target);method='PDF_ORIGINAL'
    elif extension=='.txt':
        text,encoding=decode_text(source.read_bytes());text_pdf(text,target);method='NATIVE_TEXT_TO_PDF';notes=['文字投影；原文字另保留','SOURCE_ENCODING='+encoding]
    elif extension in ('.doc','.docx'):
        try:method=word_pdf(source,target)
        except RuntimeError:
            if extension!='.docx':raise
            docx_projection(source,target);method='DOCX_NATIVE_TEXT_TABLE_IMAGE_PROJECTION';notes=['原文字、表格格值及內嵌圖片保留；非原版面，必須核對']
    else:
        import fitz,io
        from PIL import Image,ImageOps
        doc=fitz.open()
        try:
            with Image.open(source) as im:
                for i in range(getattr(im,'n_frames',1)):
                    im.seek(i);frame=ImageOps.exif_transpose(im.copy()).convert('RGB');data=io.BytesIO();frame.save(data,format='PNG')
                    width,height=frame.size;page=doc.new_page(width=72*width/IMAGE_ASSUMED_DPI,height=72*height/IMAGE_ASSUMED_DPI);page.insert_image(page.rect,stream=data.getvalue())
            doc.save(target);method='IMAGE_PIXELS_TO_PDF';notes=['未縮小原始像素；DPI 為版面假設，非補回原圖細節','OCR_REQUIRED']
        finally:doc.close()
    return {'source_document':source.name,'source_sha256':file_hash(source),'pdf_name':target.name,'pdf_sha256':file_hash(target),'method':method,'notes':notes,'conversion_verified':extension=='.pdf','status':'SOURCE_ORIGINAL' if extension=='.pdf' else 'CONVERTED_REQUIRES_REVIEW'}
