#!/usr/bin/env python3
"""Lossless private Preview transport for the versioned v0105.3 typography preview."""
from pathlib import Path
import base64
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def digest(body):
    return hashlib.sha256(body).hexdigest()


def build():
    source = (ROOT / 'public/governance_v0105_3.html').read_text(encoding='utf-8')
    match = re.search(r'<script id="model" type="application/json">(.*?)</script>', source, re.S)
    assert match
    model = match.group(1).encode('utf-8')
    app = (ROOT / 'scripts/governance_v0105_3.js').read_text(encoding='utf-8')
    assert source.count('<script>' + app + '</script>') == 1
    packed = gzip.compress(model, mtime=0)
    assert gzip.decompress(packed) == model
    data = base64.b64encode(packed).decode('ascii')
    app_literal = json.dumps(app, ensure_ascii=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    bootstrap = """'use strict';
(async () => {
  try {
    if (typeof DecompressionStream !== 'function') throw new Error('Native gzip DecompressionStream required');
    const holder = document.getElementById('model');
    const binary = atob(holder.textContent.trim());
    const bytes = Uint8Array.from(binary, (letter) => letter.charCodeAt(0));
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    const raw = new Uint8Array(await new Response(stream).arrayBuffer());
    if (raw.length !== __MODEL_BYTES__) throw new Error('Uncompressed model byte limit/hash mismatch');
    const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', raw)), (n) => n.toString(16).padStart(2, '0')).join('');
    if (hash !== '__MODEL_SHA__') throw new Error('Lossless model SHA mismatch');
    holder.textContent = new TextDecoder('utf-8', {fatal:true}).decode(raw);
    holder.dataset.transport = 'lossless-gzip';
    const script = document.createElement('script');
    script.textContent = __APP_JS__;
    document.body.append(script);
    window.VIA_PREVIEW_TRANSPORT = {version:'v0105.3', modelSha:hash, sourceContentUnchanged:true, network:false};
  } catch (error) {
    document.getElementById('inventory-warning').textContent = 'STOP: Private Preview native decompression/integrity failed. Use the verified standalone v0105 HTML; no engine or registry activation.';
    console.error(String(error));
  }
})();
""".replace('__MODEL_BYTES__', str(len(model))).replace('__MODEL_SHA__', digest(model)).replace('__APP_JS__', app_literal)
    app_hash = base64.b64encode(hashlib.sha256(app.encode()).digest()).decode()
    boot_hash = base64.b64encode(hashlib.sha256(bootstrap.encode()).digest()).decode()
    csp = "default-src 'none'; script-src 'sha256-" + app_hash + "' 'sha256-" + boot_hash + "'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"
    page = source.replace(match.group(0), '<script id="model" type="application/json" data-transport="gzip">' + data + '</script>')
    page = page.replace('<script>' + app + '</script>', '<script>' + bootstrap + '</script>')
    page = re.sub(r'(<meta http-equiv="Content-Security-Policy" content=")[^"]+(">)', lambda m: m.group(1)+csp+m.group(2), page)
    target = ROOT / 'public/governance-preview-v0105.3.html'
    receipt_path = ROOT / 'data/private_transport_v0105_3.json'
    mirror_names = ['data/governance_inventory_v0105.json', 'public/governance_v0105_3.html']
    versioned_outputs = [target, receipt_path, *(ROOT / (name + '.v0105.3.gz') for name in mirror_names)]
    if any(path.exists() for path in versioned_outputs):
        raise FileExistsError('refuse to overwrite an existing v0105.3 output')
    target.write_text(page, encoding='utf-8')
    mirrors = {}
    for name in mirror_names:
        path = ROOT / name
        original = path.read_bytes()
        packed = gzip.compress(original, mtime=0)
        mirror = ROOT / (name + '.v0105.3.gz')
        mirror.write_bytes(packed)
        mirrors[name] = {'gzip_path': mirror.relative_to(ROOT).as_posix(), 'source_bytes': len(original), 'source_sha256': digest(original), 'gzip_sha256': digest(packed)}
    receipt = {'version':'v0105.3', 'mode':'Lossless private hosting transport, no domain logic or immutable ZIP change',
               'model_sha256':digest(model), 'app_js_sha256':digest(app.encode()), 'source_html_sha256':digest(source.encode()),
               'preview_html_sha256':digest(page.encode()), 'preview_bytes':len(page.encode()), 'gzip_source_mirrors':mirrors,
               'formal_registration':False, 'production_deployment':False, 'existing_engine_modified':False}
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'preview_bytes':receipt['preview_bytes'],'model_sha256':receipt['model_sha256'],'status':'BUILT_NOT_YET_UAT'}))


if __name__ == '__main__':
    build()
