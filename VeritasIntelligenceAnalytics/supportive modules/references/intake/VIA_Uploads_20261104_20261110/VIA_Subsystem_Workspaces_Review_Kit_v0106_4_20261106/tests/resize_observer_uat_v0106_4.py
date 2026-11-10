#!/usr/bin/env python3
"""Native ResizeObserver stress and no-write-in-delivery checks. No error suppression."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PROBE = r"""(() => {
 const metrics = {depth:0, callbacks:0, deliveryWrites:[], errorEvents:[]};
 window.__RO_PROBE = metrics;
 const Original = window.ResizeObserver;
 window.ResizeObserver = class extends Original {
   constructor(callback) { super((entries,observer) => { metrics.depth++; metrics.callbacks++; try { callback(entries,observer); } finally {metrics.depth--;} }); }
 };
 const set = CSSStyleDeclaration.prototype.setProperty;
 CSSStyleDeclaration.prototype.setProperty = function(name,value,priority) {
   if (metrics.depth && ['--head','--center-head','--tabs-height','--brand-logo-height'].includes(name)) metrics.deliveryWrites.push({name,value});
   return set.call(this,name,value,priority);
 };
 window.addEventListener('error', event => {metrics.errorEvents.push(event.message);});
})();"""


def run(root: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=False)
    checks=[];pages=[];old=[]
    cases=[('global',root/'public/governance-preview-v0105.3.html')]+[(s,root/f'public/system-v0106.4-{s}.html') for s in ['vcgc','vdf','vrn','vqg','vap','database']]
    chromium=shutil.which('chromium') or shutil.which('google-chrome')
    if not chromium:raise RuntimeError('Installed Chromium required')
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=chromium,headless=True,args=['--no-sandbox'])
        legacy=root/'public/governance-preview-v0105.2.html'
        compared=[('legacy-global',legacy)] if legacy.exists() else []
        for label,file in [*compared,*cases]:
            context=browser.new_context(viewport={'width':1440,'height':900})
            context.add_init_script(PROBE);page=context.new_page();errors=[];console=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('console',lambda msg:console.append(msg.text) if msg.type=='error' else None)
            page.goto(file.resolve().as_uri())
            page.wait_for_function('Boolean(window.VIA_GOVERNANCE || window.VIA_SUBSYSTEM)',timeout=30000)
            for width in [768,390,1101,719,1440,391,900,390,1440]:
                page.set_viewport_size({'width':width,'height':900})
                page.wait_for_timeout(55)
                page.evaluate("(() => {const copy=document.querySelector('.brand-copy');copy.style.fontSize='13px';copy.style.letterSpacing='0.1px';})()")
                page.wait_for_timeout(55)
                page.evaluate("(() => {const copy=document.querySelector('.brand-copy');copy.style.fontSize='';copy.style.letterSpacing='';})()")
                page.wait_for_timeout(55)
            for which in ['#toggle-input','#toggle-evidence']:
                for _ in range(2):page.locator(which).click();page.wait_for_timeout(60)
            page.wait_for_timeout(250)
            metric=page.evaluate('window.__RO_PROBE')
            geometry=page.evaluate("(() => {const h=document.getElementById('masthead').getBoundingClientRect();return {height:h.height,cssHead:parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--head')),overflow:document.documentElement.scrollWidth>innerWidth};})()")
            row={'page':label,'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'metrics':metric,'page_errors':errors,'console_errors':console,'geometry':geometry}
            if label=='legacy-global':old.append(row)
            else:
                pages.append(row)
                for name,good in [('native observer exercised',metric['callbacks']>0),('no layout property writes in RO delivery',len(metric['deliveryWrites'])==0),('no ResizeObserver error events',not metric['errorEvents']),('no page/console errors',not errors and not console),('header offset matches live measured size',abs(geometry['height']-geometry['cssHead'])<=2),('no viewport overflow',not geometry['overflow'])]:checks.append({'page':label,'name':name,'passed':bool(good)})
            context.close()
        browser.close()
    result={'version':'v0106.4','status':'PASS' if all(c['passed']for c in checks)else'FAIL','generated_at_utc':datetime.now(timezone.utc).isoformat(),'checks_total':len(checks),'checks_passed':sum(c['passed']for c in checks),'checks':checks,'pages':pages,'legacy_comparison':old,'scope':'Native RO viewport/font/panel stress; original errors captured without preventDefault or ignoring; no engine/network/registration changes'}
    (out/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    r=run(a.root,a.out);print(json.dumps({k:r[k]for k in ['status','checks_total','checks_passed']}));return 0 if r['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
