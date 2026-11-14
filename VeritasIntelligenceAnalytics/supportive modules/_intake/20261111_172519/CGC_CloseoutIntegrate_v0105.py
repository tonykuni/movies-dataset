# [VIA:ACCEL-BRIDGE] CGC_CloseoutIntegrate_v0105 - thin tail: L4 AST similarity capped (files <=200KB, newest 1500 by mtime) -> bounded runtime
# [VIA:ACCEL-BRIDGE] CGC_CloseoutIntegrate_v0104 - thin tail over v0103: accelerator detection recognizes the real VIA bridges (via_superaccel_module / ACCEL-BRIDGE / NET-BRIDGE / VIA_NET_TOOL_PATH / Celeritas)
# [VIA:ACCEL-BRIDGE] CGC_CloseoutIntegrate_v0103 - thin tail over v0102: shield accepts vc.shield() factory shape
# [VIA:ACCEL-BRIDGE] CGC_CloseoutIntegrate_v0102 - thin tail over v0101: manager name patterns aligned to the real tail versions
#   VCGC = CGC_MDL149_VeritasCentralGovernanceConsole_v####, VQG = VQG_AllInOne_v####, VAP = VIA_VAP_* / VAP_*; VQG no longer RESERVED
# [VIA:ACCEL-BRIDGE] CGC_CloseoutIntegrate_v0101 - RC-1 closeout integrator for VCGC
# L1 HARVEST prior run successes (never lose a GREEN)  L2 INTAKE+DEDUP Downloads batch -> VCGC _intake (TEMP ids, no overwrite)
# L3 SIX SystemManagers independence check (compile-only, no execution)  L4 TA-Lib ban + similar-function clusters (AST)
# L5 Token-saving card.  Writes: RUN dir, <root>\supportive modules\_intake\<ts>\ (new files only), one ledger line if ledger exists.
import os, sys, re, json, ast, hashlib, glob, time, threading, shutil
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime, timedelta

try:
    import VeritasCeleritas_v1141 as vc
except Exception:
    vc = None
def shield(fn):
    # VeritasCeleritas_v1141.shield is a decorator FACTORY (@vc.shield()); accept both factory and plain-decorator shapes
    if vc is None or not hasattr(vc, 'shield'):
        return fn
    for attempt in (lambda: vc.shield()(fn), lambda: vc.shield(fn)):
        try:
            w = attempt()
            if callable(w) and w is not fn and getattr(w, '__name__', '') != 'decorator':
                return w
        except Exception:
            pass
    return fn

EXCL = {'.venv', 'venv', 'node_modules', '__pycache__', '.git', '_superseded', 'graphify-out', '.pytest_cache', 'build', 'dist', '_viam_external_vault', '_intake'}
VER_RE = re.compile(r'[_\-]v(\d{3,4})(?:[_\-.]|$)', re.I)
TALIB_RE = re.compile(r'^\s*(import\s+talib|from\s+talib\b|import\s+ta_lib|pip\s+install\s+TA-Lib)', re.I | re.M)
SYSTEMS = {
    'VCGC': [r'CGC_MDL149_VeritasCentralGovernanceConsole', r'CGC_.*SystemManager', r'VIA_CentralGovernanceEngine', r'VCGC.*SystemManager'],
    'VDF':  [r'VDF_SystemManager', r'VDF.*SystemManager', r'VeritasDataForge.*Manager'],
    'VRN':  [r'VRN_SystemManager', r'VRN-?2?.*SystemManager', r'ActivateVRN'],
    'VAP':  [r'VIA_VAP_Chart_SSOT', r'VAP.*SystemManager', r'VAP.*Manager', r'VAP_AllInOne', r'.*autoplot.*manager'],
    'VQG':  [r'VQG_AllInOne', r'VQG.*SystemManager', r'VQG.*Manager'],
    'DB':   [r'.*ParquetLake', r'.*DuckDB.*Manager', r'VIA_DB.*Manager', r'vdf_master_lists.*manager', r'.*LakeManager'],
}
LANES = {}; LOCK = threading.Lock()
def put(i, pct, state, msg):
    with LOCK: LANES[i] = {'pct': pct, 'state': state, 'msg': msg, 't': datetime.now().strftime('%H:%M:%S')}
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 16), b''): h.update(c)
    return h.hexdigest()
def ver_of(name):
    m = VER_RE.search(os.path.splitext(name)[0]); return int(m.group(1)) if m else None
def fam_of(name):
    s = os.path.splitext(name)[0]; m = VER_RE.search(s); return (s[:m.start()] if m else s).lower()
def walk(root, exts):
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCL and not d.startswith(('RUN_', 'VIA_RUN_'))]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in exts: yield os.path.join(dp, fn)
def read(p, n=400000):
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as f: return f.read(n)
    except Exception: return ''

# ---------- L1 HARVEST ----------
def harvest(temp_dir, dl):
    rows = []; greens = 0; cutoff = datetime.now() - timedelta(days=10)
    dirs = [d for d in glob.glob(os.path.join(temp_dir, 'VIA_RUN_*')) if os.path.isdir(d)]
    dirs += [d for d in glob.glob(os.path.join(dl, 'VIA_Uploads_Workbench', '_runs', '*')) if os.path.isdir(d)]
    dirs = [d for d in dirs if datetime.fromtimestamp(os.path.getmtime(d)) > cutoff]
    put(1, 5, 'RUN', f'{len(dirs)} run dirs')
    for i, d in enumerate(sorted(dirs)):
        put(1, 5 + int(90 * i / max(1, len(dirs))), 'RUN', os.path.basename(d))
        lanes = []
        for lj in glob.glob(os.path.join(d, 'lane_*.json')):
            try:
                o = json.load(open(lj, encoding='utf-8')); lanes.append({'name': o.get('name', ''), 'state': o.get('state', ''), 'msg': str(o.get('msg', ''))[:160]})
            except Exception: pass
        pp = os.path.join(d, 'paste_pack.txt'); pp_lines = read(pp).splitlines() if os.path.exists(pp) else []
        for other in ('panorama2.json', 'coverage.json', 'VIA_ToolRegistry_W4_detect.json', 'inventory.json'):
            if os.path.exists(os.path.join(d, other)): lanes.append({'name': other, 'state': 'ARTIFACT', 'msg': ''})
        for f in glob.glob(os.path.join(d, '*.html')): lanes.append({'name': os.path.basename(f), 'state': 'HTML', 'msg': ''})
        if lanes or pp_lines:
            g = sum(1 for l in lanes if l['state'] == 'GREEN'); greens += g
            rows.append({'run': d, 'when': datetime.fromtimestamp(os.path.getmtime(d)).strftime('%m-%d %H:%M'), 'greens': g,
                         'lanes': lanes, 'paste_head': pp_lines[:8]})
    put(1, 100, 'GREEN' if rows else 'YELLOW', f'runs={len(rows)} greens={greens}')
    return rows

# ---------- L2 INTAKE + DEDUP ----------
def intake(dl, root, run_dir, ts, explicit):
    files = [p for p in explicit if os.path.isfile(p)]
    cutoff = time.time() - 7 * 86400
    for p in glob.glob(os.path.join(dl, 'Invoke-VIA-*.ps1')) + glob.glob(os.path.join(dl, 'CGC_*.py')) + glob.glob(os.path.join(dl, 'VIA_*.py')):
        if os.path.getmtime(p) > cutoff and p not in files: files.append(p)
    put(2, 5, 'RUN', f'{len(files)} candidates; indexing root')
    idx_name = defaultdict(list); idx_fam = defaultdict(list)
    sm = os.path.join(root, 'supportive modules') if root else None
    scan_root = sm if (sm and os.path.isdir(sm)) else root
    if scan_root:
        for p in walk(scan_root, {'.py', '.ps1'}):
            n = os.path.basename(p); idx_name[n.lower()].append(p); idx_fam[fam_of(n)].append((ver_of(n), p))
    put(2, 40, 'RUN', f'root index names={len(idx_name)} families={len(idx_fam)}')
    dest = os.path.join(root, 'supportive modules', '_intake', ts) if root else os.path.join(run_dir, '_intake')
    rows = []; tid = 0
    for i, p in enumerate(files):
        put(2, 40 + int(55 * i / max(1, len(files))), 'RUN', os.path.basename(p))
        n = os.path.basename(p); h = sha(p); fam = fam_of(n); v = ver_of(n)
        txt = read(p); talib = bool(TALIB_RE.search(txt))
        joined = bool(re.search(r'via_superaccel_module|ACCEL[-_ ]?BRIDGE|VIA_NET_TOOL_PATH|VeritasCeleritas_v\d+|CELERITAS-TEMPLATE-JOIN|VIA:PS-ACCEL', txt))
        same = idx_name.get(n.lower(), [])
        status, note = 'NEW', ''
        for q in same:
            if sha(q) == h: status, note = 'DUP', q; break
            status, note = 'CONFLICT', q
        if status == 'NEW' and fam in idx_fam:
            vs = sorted([x for x in idx_fam[fam] if x[0] is not None], key=lambda x: -x[0])
            if vs:
                top = vs[0]
                status = 'SIMILAR-NEWER' if (v is not None and v > top[0]) else 'SIMILAR-OLDER'; note = f'root has v{top[0]:04d}: {top[1]}'
        landed = ''
        if status in ('NEW', 'SIMILAR-NEWER') and not talib:
            os.makedirs(dest, exist_ok=True); tgt = os.path.join(dest, n)
            if not os.path.exists(tgt): shutil.copy2(p, tgt); landed = tgt
            else: landed = 'exists'
        tid += 1
        rows.append({'temp_id': f'TEMP-{tid:04d}', 'file': n, 'src': p, 'sha12': h[:12], 'family': fam, 'ver': v, 'status': status,
                     'note': note, 'talib': talib, 'accel_joined': joined, 'landed': landed,
                     'lamp': 'RED' if (talib or status == 'CONFLICT') else ('GREEN' if status in ('NEW', 'SIMILAR-NEWER') else 'YELLOW')})
    worst = 'GREEN'
    for r in rows:
        if r['lamp'] == 'RED': worst = 'RED'
        elif r['lamp'] == 'YELLOW' and worst != 'RED': worst = 'YELLOW'
    put(2, 100, worst if rows else 'YELLOW', f'intake={len(rows)} landed={sum(1 for r in rows if r["landed"] and r["landed"] != "exists")} dest={dest}')
    return rows, dest

# ---------- L3 SIX MANAGERS ----------
def managers(roots):
    rows = []
    cand = defaultdict(list)
    for r in roots:
        for p in walk(r, {'.py', '.ps1'}):
            n = os.path.basename(p); stem = os.path.splitext(n)[0]
            for sysn, pats in SYSTEMS.items():
                if any(re.match(pat, stem, re.I) for pat in pats): cand[sysn].append(p)
    for i, sysn in enumerate(SYSTEMS):
        put(3, 10 + int(85 * i / 6), 'RUN', sysn)
        ps = cand.get(sysn, [])
        if not ps:
            rows.append({'system': sysn, 'lamp': 'GRAY', 'manager': '', 'ver': '', 'note': 'no manager/tail found in scanned roots (pull main / check branch)'}); continue
        ps.sort(key=lambda p: ((ver_of(os.path.basename(p)) or 0), os.path.getmtime(p)), reverse=True)
        top = ps[0]; txt = read(top); n = os.path.basename(top)
        has_main = ('__main__' in txt) if n.lower().endswith('.py') else True
        has_input = bool(re.search(r'(?m)^\s*[^#]*\binput\(', txt)) if n.lower().endswith('.py') else False
        talib = bool(TALIB_RE.search(txt))
        joined = bool(re.search(r'via_superaccel_module|ACCEL[-_ ]?BRIDGE|NET[-_ ]?BRIDGE|VIA_NET_TOOL_PATH|_via_net\b|VeritasCeleritas_v\d+|CELERITAS-TEMPLATE-JOIN|VIA:PS-ACCEL', txt))
        comp = 'n/a'
        if n.lower().endswith('.py'):
            try: compile(read(top, 5000000), top, 'exec'); comp = 'OK'   # in-memory only, no .pyc written into the root
            except Exception as e: comp = f'ERR {str(e)[:60]}'
        verbs = sorted(set(re.findall(r"['\"](ui|config|inventory|audit|selftest|memory|status)['\"]", txt)))
        indep = comp in ('OK', 'n/a') and has_main and not has_input and not talib
        lamp = 'RED' if (talib or comp.startswith('ERR')) else ('GREEN' if indep and joined else 'YELLOW')
        rows.append({'system': sysn, 'lamp': lamp, 'manager': top, 'ver': ver_of(n), 'candidates': len(ps), 'compile': comp,
                     'main': has_main, 'input': has_input, 'talib': talib, 'accel': joined, 'verbs': verbs,
                     'note': 'independent start OK' if indep else 'blocked: ' + ','.join(k for k, bad in (('compile', comp.startswith('ERR')), ('no __main__', not has_main), ('input()', has_input), ('TA-Lib', talib)) if bad)})
    worst = 'GREEN'
    for r in rows:
        if r['lamp'] == 'RED': worst = 'RED'
        elif r['lamp'] in ('YELLOW', 'GRAY') and worst != 'RED': worst = 'YELLOW'
    put(3, 100, worst, 'six managers: ' + ' '.join(f"{r['system']}={r['lamp']}" for r in rows))
    return rows

# ---------- L4 TA-LIB + SIMILAR ----------
def py_funcs(p):
    try:
        t = ast.parse(read(p, 2000000))
        return {n.name for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    except Exception: return set()
def ps_funcs(p):
    return set(m.lower() for m in re.findall(r'(?im)^\s*function\s+([\w\-]+)', read(p, 2000000)))
def talib_similar(roots):
    talib_hits = []; sigs = {}
    files = []
    for r in roots:
        sm = os.path.join(r, 'supportive modules')
        files += list(walk(sm if os.path.isdir(sm) else r, {'.py', '.ps1'}))
    files = [f for f in files if os.path.getsize(f) <= 200 * 1024]
    files = sorted(files, key=os.path.getmtime, reverse=True)[:1500]
    put(4, 5, 'RUN', f'{len(files)} files (capped: <=200KB, newest 1500)')
    for i, p in enumerate(files):
        if i % 40 == 0: put(4, 5 + int(70 * i / max(1, len(files))), 'RUN', f'{i}/{len(files)}')
        txt = read(p)
        if TALIB_RE.search(txt): talib_hits.append(p)
        fs = py_funcs(p) if p.lower().endswith('.py') else ps_funcs(p)
        if len(fs) >= 4: sigs[p] = fs
    put(4, 80, 'RUN', 'clustering')
    clusters = []; seen = set(); items = list(sigs.items())
    byfam = defaultdict(list)
    for p, fs in items: byfam[fam_of(os.path.basename(p))].append(p)
    for a in range(len(items)):
        pa, fa = items[a]
        if pa in seen: continue
        grp = [pa]
        for b in range(a + 1, len(items)):
            pb, fb = items[b]
            if pb in seen or fam_of(os.path.basename(pa)) == fam_of(os.path.basename(pb)): continue
            j = len(fa & fb) / max(1, len(fa | fb))
            if j >= 0.6: grp.append(pb); seen.add(pb)
        if len(grp) > 1: seen.add(pa); clusters.append({'jaccard>=0.6': True, 'files': grp, 'shared': sorted(fa & sigs[grp[1]])[:8]})
    multi = {f: sorted({ver_of(os.path.basename(p)) for p in ps if ver_of(os.path.basename(p))}) for f, ps in byfam.items() if len(ps) > 3}
    put(4, 100, 'RED' if talib_hits else ('YELLOW' if clusters else 'GREEN'), f'talib={len(talib_hits)} similar-clusters={len(clusters)} thin-tail-families(>3 versions)={len(multi)}')
    return talib_hits, clusters, multi

# ---------- L5 TOKEN CARD ----------
def token_card(root):
    rows = []
    def add(k, ok, note): rows.append({'item': k, 'lamp': 'GREEN' if ok else 'YELLOW', 'note': note})
    cl = os.path.join(root, 'CLAUDE.md'); add('CLAUDE.md TOKEN BLOCK', os.path.exists(cl) and 'VIA TOKEN BLOCK' in read(cl), cl)
    ci = os.path.join(root, '.claudeignore'); add('.claudeignore', os.path.exists(ci), f'{len(read(ci).splitlines())} lines' if os.path.exists(ci) else 'missing')
    ctx = os.path.join(root, '.claude', 'ctx'); add('ctx split', os.path.isdir(ctx) and len(os.listdir(ctx)) >= 4, ctx)
    gj = glob.glob(os.path.join(root, '**', 'graphify-out', 'graph.json'), recursive=True)
    add('Graphify graph', bool(gj), gj[0] if gj else 'no graph.json (extract may be running)')
    add('graphify skill (project)', os.path.isdir(os.path.join(root, '.claude', 'skills', 'graphify')), '.claude/skills/graphify')
    home = os.path.expanduser('~'); add('claude-mem', os.path.isdir(os.path.join(home, '.claude-mem')), '~/.claude-mem')
    wf = os.path.join(root, 'workflows', 'VIA_Workflow_VCGC_TokenTools.json'); add('TokenTools manifest', os.path.exists(wf), wf)
    led = os.path.join(root, 'VIA_WorkflowLedger.jsonl'); add('WorkflowLedger', os.path.exists(led), led)
    put(5, 100, 'GREEN' if all(r['lamp'] == 'GREEN' for r in rows) else 'YELLOW', f"{sum(1 for r in rows if r['lamp']=='GREEN')}/{len(rows)} token items on")
    return rows

@shield
def main():
    run_dir = sys.argv[1]; roots = [a for a in sys.argv[2:] if os.path.isdir(a) and not a.lower().endswith(('.py', '.ps1'))]
    explicit = [a for a in sys.argv[2:] if a.lower().endswith(('.py', '.ps1'))]
    os.makedirs(run_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    root = roots[0] if roots else run_dir
    dl = os.path.join(os.path.expanduser('~'), 'Downloads'); temp_dir = os.environ.get('TEMP') or os.environ.get('TMPDIR') or '/tmp'
    order = ['L1 Harvest prior successes', 'L2 Intake+dedup -> VCGC _intake', 'L3 Six SystemManagers independent?', 'L4 TA-Lib ban + similar clusters', 'L5 Token-saving card']
    stop = threading.Event()
    def ticker():
        while not stop.is_set():
            with LOCK:
                parts = []; tot = 0
                for i, nm in enumerate(order, 1):
                    l = LANES.get(i, {'pct': 0, 'state': 'WAIT'}); tot += l['pct']; parts.append(f"L{i} {l['pct']:3d}% {l['state'][:1]}")
            sys.stdout.write('\r' + ' | '.join(parts) + f' | TOTAL {tot//5:3d}%  '); sys.stdout.flush(); time.sleep(0.5)
    th = threading.Thread(target=ticker, daemon=True); th.start()
    with ThreadPoolExecutor(max_workers=5) as ex:
        f1 = ex.submit(harvest, temp_dir, dl); f2 = ex.submit(intake, dl, root, run_dir, ts, explicit)
        f3 = ex.submit(managers, roots); f4 = ex.submit(talib_similar, roots); f5 = ex.submit(token_card, root)
        H = f1.result(); I, dest = f2.result(); M = f3.result(); T, C, MULTI = f4.result(); K = f5.result()
    stop.set(); th.join(1); print()
    out = {'ts': ts, 'roots': roots, 'harvest': H, 'intake': I, 'intake_dest': dest, 'managers': M, 'talib': T, 'similar': C, 'multi_version_families': MULTI, 'token': K, 'lanes': LANES}
    json.dump(out, open(os.path.join(run_dir, 'closeout.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # ledger line (append-only, only if ledger exists)
    led = os.path.join(root, 'VIA_WorkflowLedger.jsonl')
    digest = hashlib.sha256(json.dumps({'managers': M, 'intake': I}, sort_keys=True, default=str).encode()).hexdigest()
    line = {'ts': ts, 'engine': 'CGC_CloseoutIntegrate_v0105', 'mode': 'RC-1 CLOSEOUT', 'sha256': digest, 'run': run_dir,
            'managers': {m['system']: m['lamp'] for m in M}, 'intake': len(I), 'talib': len(T), 'similar_clusters': len(C)}
    if os.path.exists(led):
        with open(led, 'a', encoding='utf-8') as f: f.write(json.dumps(line, ensure_ascii=False) + '\n')
    open(os.path.join(run_dir, 'ledger_line.json'), 'w', encoding='utf-8').write(json.dumps(line, ensure_ascii=False))
    # HTML
    css = ('.l{display:inline-block;width:12px;height:12px;border-radius:50%}.GREEN{background:#2EB872}.YELLOW{background:#F5C518}.GRAY{background:#9AA3AD}'
           '.RED{background:#E0342B;animation:bl 1.6s infinite}@keyframes bl{50%{opacity:.25}}body{font:12px/1.4 "Segoe UI",system-ui;background:#F7F8FA;color:#1F2937;margin:16px}'
           'table{border-collapse:collapse;background:#fff;width:100%;max-width:1250px}th,td{border:1px solid #E5E7EB;padding:3px 7px;text-align:left;vertical-align:top}th{background:#EEF1F5}h1{font-size:15px;margin:12px 0 6px}small{color:#6B7280}')
    def tr(cells, lamp=None): return '<tr>' + (f"<td><span class='l {lamp}'></span></td>" if lamp else '') + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>VIA Closeout</title><style>{css}</style></head><body><h1>VIA RC-1 Closeout Integrate &middot; {ts}</h1><small>root={root}</small>"]
    h.append('<h1>Lanes</h1><table><tr><th></th><th>Lane</th><th>%</th><th>Result</th></tr>')
    for i, nm in enumerate(order, 1):
        l = LANES.get(i, {'pct': 0, 'state': 'GRAY', 'msg': ''}); h.append(tr([nm, l['pct'], l['msg']], l['state']))
    h.append('</table><h1>Six SystemManagers (compile-only, nothing executed)</h1><table><tr><th></th><th>System</th><th>Manager</th><th>v</th><th>compile</th><th>__main__</th><th>input()</th><th>TA-Lib</th><th>accel</th><th>verbs</th><th>Note</th></tr>')
    for m in M: h.append(tr([m['system'], m.get('manager', ''), m.get('ver', ''), m.get('compile', ''), m.get('main', ''), m.get('input', ''), m.get('talib', ''), m.get('accel', ''), ' '.join(m.get('verbs', [])), m['note']], m['lamp']))
    h.append('</table><h1>Intake (TEMP zone; formal numbers only from CGE after no-conflict)</h1><table><tr><th></th><th>TEMP</th><th>File</th><th>Status</th><th>Note</th><th>TA-Lib</th><th>Accel</th><th>Landed</th></tr>')
    for r in I: h.append(tr([r['temp_id'], r['file'], r['status'], r['note'], r['talib'], r['accel_joined'], r['landed']], r['lamp']))
    h.append('</table><h1>TA-Lib hits (constitution ban)</h1><table>' + ''.join(tr([p], 'RED') for p in T) + '</table>')
    h.append('<h1>Similar-function clusters (dedupe candidates; nothing deleted)</h1><table><tr><th>Files</th><th>Shared</th></tr>')
    for c in C[:60]: h.append(tr(['<br>'.join(c['files']), ', '.join(c['shared'])]))
    h.append('</table><h1>Token card</h1><table>' + ''.join(tr([k['item'], k['note']], k['lamp']) for k in K) + '</table>')
    h.append('<h1>Harvested prior runs (nothing lost)</h1><table><tr><th>When</th><th>Run</th><th>GREEN</th><th>Lanes</th></tr>')
    for r in H: h.append(tr([r['when'], r['run'], r['greens'], '; '.join(f"{l['state']} {l['name']}" for l in r['lanes'][:8])]))
    h.append('</table></body></html>')
    html = os.path.join(run_dir, 'VIA_Closeout.html'); open(html, 'w', encoding='utf-8').write('\n'.join(h))
    # paste pack
    pp = [f'CLOSEOUT {ts} root={root}']
    for i, nm in enumerate(order, 1):
        l = LANES.get(i, {'state': 'GRAY', 'msg': ''}); pp.append(f"{l['state']} {nm} {l['msg']}")
    pp.append('--- SIX MANAGERS ---')
    for m in M: pp.append(f"{m['lamp']} {m['system']} {os.path.basename(m.get('manager','')) or '-'} v={m.get('ver','')} compile={m.get('compile','')} main={m.get('main','')} input={m.get('input','')} talib={m.get('talib','')} accel={m.get('accel','')} | {m['note']}")
    pp.append('--- INTAKE (TEMP) ---')
    for r in I[:40]: pp.append(f"{r['lamp']} {r['temp_id']} {r['file']} {r['status']} {('TALIB ' if r['talib'] else '')}{r['note'][:70]}")
    pp.append(f'--- TA-LIB HITS {len(T)} ---'); pp += [f'RED TALIB {p}' for p in T[:30]]
    pp.append(f'--- SIMILAR CLUSTERS {len(C)} ---')
    for c in C[:25]: pp.append('YELLOW SIM ' + ' <> '.join(os.path.basename(f) for f in c['files'][:3]) + ' shared=' + ','.join(c['shared'][:4]))
    pp.append(f'--- THIN-TAIL FAMILIES >3 versions: {len(MULTI)} (retire-to-top candidates) ---')
    for f, vs in sorted(MULTI.items(), key=lambda kv: -len(kv[1]))[:25]: pp.append(f'YELLOW FAM {f} versions={len(vs)} top=v{vs[-1] if vs else "-"}')
    pp.append('--- TOKEN ---'); pp += [f"{k['lamp']} {k['item']} {k['note'][:80]}" for k in K]
    pp.append(f'--- HARVEST runs={len(H)} greens={sum(r["greens"] for r in H)} ---')
    for r in H[-12:]: pp.append(f"{r['when']} {os.path.basename(r['run'])} greens={r['greens']}")
    pp.append(f'HTML={html}'); pp.append(f'JSON={os.path.join(run_dir, "closeout.json")}'); pp.append(f'LEDGER={"appended" if os.path.exists(led) else "no ledger file; line saved in run dir"}')
    pp = pp[:299]; pp.append('NEXT: paste back; GREEN managers = seal candidates, YELLOW = fix list (six classes only), RED = constitution violations first')
    open(os.path.join(run_dir, 'paste_pack.txt'), 'w', encoding='utf-8').write('\n'.join(pp)); print('\n'.join(pp))
    return 0

if __name__ == '__main__':
    sys.exit(main() or 0)
