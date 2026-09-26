from pathlib import Path
import base64
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'deliverables' / 'VIA_NLP_OneEngine_v1_9_0.py'

def def_build():
    memory = io.BytesIO()
    inventory = []
    with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as output:
        with zipfile.ZipFile(ROOT/'prior_nlp/VIA_NLP_Application_System_v1.8.0.zip') as source:
            for entry in source.namelist():
                if entry.endswith('/'):
                    continue
                relative = 'legacy/'+entry.split('/',1)[1]
                raw = source.read(entry)
                output.writestr(relative,raw)
                inventory.append({'path':relative,'sha256':hashlib.sha256(raw).hexdigest()})
        with zipfile.ZipFile(ROOT/'prior_nlp/MarkdownEditingEngine_v1.4.0_FINAL.zip') as source:
            for entry in ('engine/semantic_reconstruction.py','engine/appearance_reconstruction.py','config/reconstruction_rules.json','RECONSTRUCTION_GUIDE.md','LICENSE'):
                relative = 'markdown/'+Path(entry).name
                raw = source.read(entry)
                output.writestr(relative,raw)
                inventory.append({'path':relative,'sha256':hashlib.sha256(raw).hexdigest()})
    raw = memory.getvalue()
    encoded = base64.b85encode(raw).decode('ascii')
    wrapped = '\n'.join(encoded[i:i+110] for i in range(0,len(encoded),110))
    template = (ROOT/'nlp_build/one_engine.py').read_text(encoding='utf-8')
    final = template.replace('__PAYLOAD_SHA256__',hashlib.sha256(raw).hexdigest()).replace('__PAYLOAD_B85__',wrapped)
    OUTPUT.write_text(final,encoding='utf-8')
    (ROOT/'nlp_build/payload_inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'file':str(OUTPUT),'bytes':OUTPUT.stat().st_size,'payload_files':len(inventory)}))

if __name__=='__main__':
    def_build()
