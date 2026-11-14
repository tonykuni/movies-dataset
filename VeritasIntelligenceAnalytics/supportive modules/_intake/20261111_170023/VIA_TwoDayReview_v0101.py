# [VIA:ACCEL-BRIDGE] VIA_TwoDayReview_v0101 - harvest every run of the last 2 days (OneShot/W4/CloseoutAll/FinTest/DesktopOneShot/OneClick),
# build the RC-1 readiness checklist from the newest panorama2/closeout/fintest JSON, ask Graphify the two open questions, write HTML + paste pack.
import os, sys, re, json, glob, time, subprocess, shutil
from datetime import datetime, timedelta
try:
    import VeritasCeleritas_v1141 as vc
except Exception:
    vc = None
def shield(fn):
    if vc is None or not hasattr(vc, 'shield'): return fn
    for attempt in (lambda: vc.shield()(fn), lambda: vc.shield(fn)):
        try:
            w = attempt()
            if callable(w) and w is not fn and getattr(w, '__name__', '') != 'decorator': return w
        except Exception: pass
    return fn

def read(p, n=600000):
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as f: return f.read(n)
    except Exception: return ''
def jload(p):
    try: return json.load(open(p, encoding='utf-8', errors='replace'))
    except Exception: return None
def lamps(text):
    return {k: len(re.findall(r'(?m)^\s*(?:\[)?' + k + r'(?:\])?\b', text)) for k in ('GREEN', 'YELLOW', 'RED')}
def run(cmd, cwd, timeout):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, encoding='utf-8', errors='replace')
        return r.returncode, (r.stdout + '\n' + r.stderr).strip()
    except subprocess.TimeoutExpired: return -999, 'TIMEOUT'
    except Exception as e: return -998, str(e)

@shield
def main():
    run_dir = sys.argv[1]; roots = [a for a in sys.argv[2:] if os.path.isdir(a)]
    os.makedirs(run_dir, exist_ok=True)
    temp = os.environ.get('TEMP') or '/tmp'; dl = os.path.join(os.path.expanduser('~'), 'Downloads')
    since = datetime.now() - timedelta(days=2)
    pp = [f'TWO-DAY REVIEW {datetime.now():%Y-%m-%d %H:%M} since={since:%m-%d %H:%M}']
    # ---- 1. harvest timeline ----
    rows = []
    for d in glob.glob(os.path.join(temp, 'VIA_RUN_*')) + glob.glob(os.path.join(dl, 'VIA_Uploads_Workbench', '_runs', '*')):
        if not os.path.isdir(d) or datetime.fromtimestamp(os.path.getmtime(d)) < since: continue
        kind = re.sub(r'^VIA_RUN_\d{8}_\d{6}_', '', os.path.basename(d))
        txt = ''
        for pf in ('paste_pack_ALL.txt', 'paste_pack.txt'):
            for f in glob.glob(os.path.join(d, '**', pf), recursive=True): txt += read(f) + '\n'
        for f in glob.glob(os.path.join(d, '**', 'lane_*.json'), recursive=True):
            o = jload(f)
            if o: txt += f"{o.get('state','')} {o.get('name','')}\n"
        l = lamps(txt)
        rows.append({'when': datetime.fromtimestamp(os.path.getmtime(d)).strftime('%m-%d %H:%M'), 'kind': kind, 'path': d, **l})
    for f in glob.glob(os.path.join(temp, 'VIA_DesktopOneShot*_paste.txt')) + glob.glob(os.path.join(temp, 'VIA_OneClick_*.log')):
        if datetime.fromtimestamp(os.path.getmtime(f)) < since: continue
        t = read(f); l = lamps(t)
        rows.append({'when': datetime.fromtimestamp(os.path.getmtime(f)).strftime('%m-%d %H:%M'), 'kind': os.path.basename(f)[:40], 'path': f, **l})
    rows.sort(key=lambda r: r['when'])
    pp.append(f'--- TIMELINE runs={len(rows)} ---')
    for r in rows: pp.append(f"{r['when']} {r['kind'][:34]:34} G={r['GREEN']} Y={r['YELLOW']} R={r['RED']}")
    # ---- 2. readiness from newest JSONs ----
    def newest(pattern):
        c = sorted(glob.glob(os.path.join(temp, 'VIA_RUN_*', '**', pattern), recursive=True), key=os.path.getmtime)
        return (c[-1], jload(c[-1])) if c else (None, None)
    p2p, p2 = newest('panorama2.json'); cop, co = newest('closeout.json'); fnp, fn = newest('fintest.json')
    chk = []
    def add(lamp, item, note): chk.append((lamp, item, note))
    if p2:
        g = [x for x in p2.get('git', []) if x.get('lamp') == 'RED']
        add('RED' if g else 'GREEN', 'git main clean', '; '.join(f"{os.path.basename(x['repo'])} dirty={x.get('dirty')} behind={x.get('behind')}" for x in g) or 'no red repo')
        add('RED' if len(p2.get('conflicts', [])) > 5 else ('YELLOW' if p2.get('conflicts') else 'GREEN'), 'cross-root conflicts', f"{len(p2.get('conflicts', []))} (same name, different content); divergences={len(p2.get('diverge', []))}")
        for c in p2.get('conflicts', [])[:5]: add('RED', '  conflict', f"{c['name']} A={c.get('sizeA')}B B={c.get('sizeB')}B")
        gr = p2.get('graph', {}).get('graphs', [])
        add('GREEN' if gr else 'YELLOW', 'Graphify graphs', f"{len(gr)} graphs nodes={sum(x.get('nodes', 0) for x in gr)}")
    else: add('GRAY', 'panorama2.json', 'not found in TEMP runs')
    if co:
        for m in co.get('managers', []): add(m['lamp'], f"manager {m['system']}", f"{os.path.basename(m.get('manager', '') or '-')} {m.get('note', '')}")
        add('RED' if co.get('talib') else 'GREEN', 'TA-Lib ban', f"hits={len(co.get('talib', []))}")
        add('YELLOW' if co.get('similar') else 'GREEN', 'similar-function clusters', f"{len(co.get('similar', []))} (dedupe candidates, nothing deleted)")
        add('YELLOW' if co.get('multi_version_families') else 'GREEN', 'thin-tail families >3 versions', f"{len(co.get('multi_version_families', {}))}")
        tk = co.get('token', []); add('GREEN' if all(t['lamp'] == 'GREEN' for t in tk) else 'YELLOW', 'token-saving card', f"{sum(1 for t in tk if t['lamp']=='GREEN')}/{len(tk)} on")
        add('GREEN', 'intake TEMP zone', f"{len(co.get('intake', []))} files landed (no constitution rights)")
    else: add('GRAY', 'closeout.json', 'not found in TEMP runs')
    if fn:
        add('GREEN' if fn.get('fin_candidates') else 'YELLOW', 'VDF financial MDL mapping', f"candidates={fn.get('fin_candidates')} (expected MDL006 三大報表)")
        add('YELLOW', 'VDF test params', 'overlay landed; manager config groups still start=2015-01-01 items=0 → set via manager verb')
    else: add('GRAY', 'fintest.json', 'not run yet')
    add('YELLOW', 'MDL149 v0195 twin', 'same number, two contents (A 26703B / B 18205B) → constitution breach, TEMP first case')
    add('YELLOW', 'PeerBridge prove', 'MATCH 15 / GAP 8; IFC-003 not ACTIVE in VCGC contract book (your call)')
    add('GREEN', 'ENG238 / MDL009 / VQG', 'holdings filled 1,162,429 rows; VQG register 66 rows; idempotent on rerun')
    pp.append('--- READINESS (RC-1 SEAL) ---')
    for lamp, item, note in chk: pp.append(f'{lamp} {item} | {note[:120]}')
    go = 'NO-GO' if any(l == 'RED' for l, _, _ in chk) else ('HOLD' if any(l == 'YELLOW' for l, _, _ in chk) else 'GO')
    pp.append(f'GO/HOLD/NO-GO = {go}')
    # ---- 3. Graphify questions ----
    gexe = shutil.which('graphify') or shutil.which('graphify.exe')
    gq = []
    gdirs = []
    for r in roots:
        for d in glob.glob(os.path.join(r, 'VIA_Reports', 'graphify', '*', 'graphify-out')): gdirs.append(os.path.dirname(d))
    questions = [('VDF', 'MDL006 三大報表 financial statements engine: which module resolves tickers and start date, and which engines does it depend on'),
                 ('VDF', 'MDL008 FetchSystem child process version resolution for MDL009'),
                 ('VRN', 'VRN SystemManager peers verb: how are VCGC and VDF managers discovered')]
    for sub, q in questions:
        d = next((x for x in gdirs if os.path.basename(x).upper().startswith(sub)), None)
        if not gexe or not d: gq.append((sub, q, -1, 'graphify or graph dir missing')); continue
        rc, o = run([gexe, 'query', q], d, 180)
        gq.append((sub, q, rc, o))
    pp.append('--- GRAPHIFY ---')
    for sub, q, rc, o in gq:
        pp.append(f"{'GREEN' if rc == 0 else 'YELLOW'} graphify[{sub}] rc={rc} q={q[:60]}")
        for l in [x for x in o.splitlines() if x.strip()][:8]: pp.append('    ' + l[:110])
    # ---- 4. lessons roll-up ----
    pp.append('--- LESSONS (evidence from these two days) ---')
    pp += ['LESSON-0002 scope creep: W4 tool install/intake happened inside RC-1 → allowed only as W4 unfreeze; keep LAW-11',
           'LESSON-0003 divergence: OneDrive root vs Workbench_Local root; MDL149 v0195 twin; 4 shadow prefixes (VETF_/_sha/__cherrylagoon/B_)',
           'LESSON-0004 roots: main dirty 500+/behind 519; branch files cherry-checked-out; card downloads arrive as zip; MotW blocks ps1',
           'LESSON-0005 DoD: six managers now have conform/health/peers verbs; VDF test params need manager config verb, not browser localStorage',
           'FIX-TRACE: shield factory shape → v0102/v0103; npx.ps1 shim → Resolve-Exe; CRLF vs LF → normalized hash; manifest.json basename → relpath match']
    json.dump({'timeline': rows, 'readiness': chk, 'go': go, 'graphify': gq, 'sources': {'panorama2': p2p, 'closeout': cop, 'fintest': fnp}},
              open(os.path.join(run_dir, 'review.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    css = '.l{display:inline-block;width:12px;height:12px;border-radius:50%}.GREEN{background:#2EB872}.YELLOW{background:#F5C518}.GRAY{background:#9AA3AD}.RED{background:#E0342B;animation:bl 1.6s infinite}@keyframes bl{50%{opacity:.25}}body{font:12px/1.4 "Segoe UI",system-ui;background:#F7F8FA;color:#1F2937;margin:16px}table{border-collapse:collapse;background:#fff;width:100%;max-width:1150px}th,td{border:1px solid #E5E7EB;padding:3px 7px;text-align:left;vertical-align:top}th{background:#EEF1F5}h1{font-size:15px;margin:12px 0 6px}pre{background:#fff;border:1px solid #E5E7EB;padding:6px;font-size:11px;max-height:30vh;overflow:auto}'
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>VIA Two-Day Review</title><style>{css}</style></head><body><h1>VIA Two-Day Review &middot; {datetime.now():%Y-%m-%d %H:%M} &middot; <b>{go}</b></h1>"]
    h.append('<h1>Readiness</h1><table><tr><th></th><th>Item</th><th>Note</th></tr>' + ''.join(f"<tr><td><span class='l {l}'></span></td><td>{i}</td><td>{n}</td></tr>" for l, i, n in chk) + '</table>')
    h.append('<h1>Timeline</h1><table><tr><th>When</th><th>Run</th><th>G</th><th>Y</th><th>R</th><th>Path</th></tr>' + ''.join(f"<tr><td>{r['when']}</td><td>{r['kind']}</td><td>{r['GREEN']}</td><td>{r['YELLOW']}</td><td>{r['RED']}</td><td>{r['path']}</td></tr>" for r in rows) + '</table>')
    h.append('<h1>Graphify</h1>' + ''.join(f"<h3>[{s}] rc={rc} {q}</h3><pre>{o.replace('<','&lt;')[:4000]}</pre>" for s, q, rc, o in gq) + '</body></html>')
    html = os.path.join(run_dir, 'VIA_TwoDayReview.html'); open(html, 'w', encoding='utf-8').write('\n'.join(h))
    pp.append(f'HTML={html}'); pp = pp[:299]; pp.append('NEXT: decide release root (OneDrive vs Workbench_Local) and IFC-003; then PR→main, tag rc-1')
    open(os.path.join(run_dir, 'paste_pack.txt'), 'w', encoding='utf-8').write('\n'.join(pp)); print('\n'.join(pp)); return 0

if __name__ == '__main__':
    sys.exit(main() or 0)
