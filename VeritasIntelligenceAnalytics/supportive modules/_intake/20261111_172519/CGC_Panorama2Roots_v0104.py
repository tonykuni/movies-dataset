# [VIA:ACCEL-BRIDGE] CGC_Panorama2Roots_v0104 - thin tail: git status -uno (untracked skipped) and 60s per git call -> no stall on 28k-file OneDrive trees
# [VIA:ACCEL-BRIDGE] CGC_Panorama2Roots_v0103 - thin tail over v0102: conflicts matched by RELATIVE PATH (not bare name); hash normalizes CRLF/LF and BOM
# [VIA:ACCEL-BRIDGE] CGC_Panorama2Roots_v0102 - thin tail over v0101: shield accepts vc.shield() factory shape
# [VIA:ACCEL-BRIDGE] CGC_Panorama2Roots_v0101 - two-root panoramic scan + GitHub + Graphify + tool enablement
# Token-saving: writes everything to RUN dir; the AI reads only paste_pack.txt (<=300 lines, ends NEXT:)
# Read-only toward VIA roots: never writes inside either root; proposals (TEMP-/CONFLICT-) land in RUN dir only.
import os, sys, re, json, hashlib, subprocess, threading, time, shutil
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime

try:
    import VeritasCeleritas_v1141 as vc  # accelerator (guarded)
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

EXCL_DIRS = {'.venv', 'venv', 'node_modules', '__pycache__', '.git', '_superseded', 'graphify-out',
             '.pytest_cache', '.mypy_cache', '.ruff_cache', 'build', 'dist', '_viam_external_vault'}
EXCL_PREFIX = ('RUN_', 'VIA_RUN_')
PROTECTED = ('dict' + os.sep + 'VDF' + os.sep + '_active', 'functional modules' + os.sep + 'VDF')
EXTS = {'.py', '.ps1', '.json', '.yaml', '.yml'}
VER_RE = re.compile(r'[_\-]v(\d{3,4})(?:[_\-.]|$)', re.I)
MAX_HASH_BYTES = 2 * 1024 * 1024

LANES = {}
LOCK = threading.Lock()

def put(lane, pct, state, msg):
    with LOCK:
        LANES[lane] = {'pct': pct, 'state': state, 'msg': msg, 't': datetime.now().strftime('%H:%M:%S')}

def sha(p):
    # text-normalized digest: CRLF/CR -> LF, strip UTF-8 BOM, so OneDrive (CRLF) vs git-LF copies compare equal
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        data = f.read()
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    h.update(data)
    return h.hexdigest()

def run(cmd, cwd=None, timeout=60):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, encoding='utf-8', errors='replace')
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -999, 'TIMEOUT'
    except Exception as e:
        return -998, str(e)

def which(name):
    for ext in ('', '.exe', '.cmd', '.bat'):
        p = shutil.which(name + ext)
        if p and not p.lower().endswith('.ps1'):
            return p
    return None

# ---------------- lane 1/2: inventory a root ----------------
def inventory(lane, root):
    files = []
    put(lane, 3, 'RUN', 'walking')
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCL_DIRS and not d.startswith(EXCL_PREFIX)]
        rel_dp = os.path.relpath(dp, root)
        for fn in fns:
            ext = os.path.splitext(fn)[1].lower()
            if ext in EXTS:
                files.append(os.path.join(dp, fn))
    n = len(files)
    put(lane, 10, 'RUN', f'{n} files, hashing')
    out = {}
    t0 = time.time()
    for i, p in enumerate(files):
        try:
            st = os.stat(p)
            digest = sha(p) if st.st_size <= MAX_HASH_BYTES else f'BIG:{st.st_size}'
        except Exception as e:
            digest = f'ERR:{e.__class__.__name__}'
            st = None
        rel = os.path.relpath(p, root)
        stem = os.path.splitext(os.path.basename(p))[0]
        m = VER_RE.search(stem)
        fam = (stem[:m.start()] if m else stem).lower()
        ver = int(m.group(1)) if m else None
        out[rel.lower()] = {'rel': rel, 'sha': digest, 'size': (st.st_size if st else 0), 'fam': fam, 'ver': ver,
                            'name': os.path.basename(p).lower(),
                            'protected': any(seg in rel for seg in PROTECTED)}
        if i % 50 == 0:
            put(lane, 10 + int(85 * i / max(1, n)), 'RUN', f'{i}/{n} hashed {int(time.time()-t0)}s')
    put(lane, 100, 'GREEN' if n else 'YELLOW', f'files={n} sec={int(time.time()-t0)}')
    return out

# ---------------- lane 3: git ----------------
def git_lane(repos):
    rows = []
    git = which('git')
    if not git:
        put(3, 100, 'YELLOW', 'git not on PATH'); return rows
    for i, r in enumerate(repos):
        put(3, 10 + int(80 * i / max(1, len(repos))), 'RUN', os.path.basename(r))
        if not os.path.isdir(os.path.join(r, '.git')):
            rows.append({'repo': r, 'lamp': 'GRAY', 'note': 'not a git repo'}); continue
        rc, br = run([git, 'rev-parse', '--abbrev-ref', 'HEAD'], r)
        rc, dirty = run([git, 'status', '--porcelain', '-uno'], r, 60)
        dirty_n = len([l for l in dirty.splitlines() if l.strip()]) if rc == 0 else -1
        rc2, ab = run([git, 'rev-list', '--left-right', '--count', 'HEAD...@{u}'], r)
        ahead, behind = (-1, -1)
        if rc2 == 0 and ab:
            parts = ab.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
        rc3, l7 = run([git, 'log', '--since=7.days', '--oneline'], r)
        c7 = len(l7.splitlines()) if rc3 == 0 else -1
        rc4, lsf = run([git, 'ls-files'], r, 60)
        tracked = len(lsf.splitlines()) if rc4 == 0 else -1
        lamp = 'GREEN'
        if behind > 100 or dirty_n > 100: lamp = 'RED'
        elif behind > 0 or dirty_n > 0 or ahead > 0: lamp = 'YELLOW'
        rows.append({'repo': r, 'branch': br, 'dirty': dirty_n, 'ahead': ahead, 'behind': behind,
                     'commits_7d': c7, 'tracked': tracked, 'lamp': lamp})
    worst = 'GREEN'
    for x in rows:
        if x['lamp'] == 'RED': worst = 'RED'
        elif x['lamp'] == 'YELLOW' and worst != 'RED': worst = 'YELLOW'
    put(3, 100, worst, f'repos={len(rows)}')
    return rows

# ---------------- lane 4: graphify ----------------
def graph_lane(roots, run_dir):
    gexe = which('graphify')
    cands = []
    for r in roots:
        for dp, dns, fns in os.walk(r):
            dns[:] = [d for d in dns if d not in EXCL_DIRS - {'graphify-out'} and not d.startswith(EXCL_PREFIX)]
            if 'graph.json' in fns and os.path.basename(dp) == 'graphify-out':
                cands.append(os.path.join(dp, 'graph.json'))
            if dp.count(os.sep) - r.count(os.sep) > 3:
                dns[:] = []
    info = {'graphify': gexe or 'MISSING', 'graphs': []}
    put(4, 30, 'RUN', f'graphs found={len(cands)}')
    for g in cands:
        try:
            j = json.load(open(g, encoding='utf-8', errors='replace'))
            nodes = j.get('nodes') or []
            edges = j.get('edges') or j.get('links') or []
            deg = defaultdict(int)
            for e in edges:
                s = e.get('source') if isinstance(e, dict) else None
                t = e.get('target') if isinstance(e, dict) else None
                if s is not None: deg[str(s)] += 1
                if t is not None: deg[str(t)] += 1
            ids = [str(n.get('id', n.get('name', i))) if isinstance(n, dict) else str(n) for i, n in enumerate(nodes)]
            orphans = sum(1 for i in ids if deg.get(i, 0) == 0)
            hubs = sorted(deg.items(), key=lambda kv: -kv[1])[:5]
            info['graphs'].append({'path': g, 'nodes': len(nodes), 'edges': len(edges), 'orphans': orphans,
                                   'hubs': [f'{k}({v})' for k, v in hubs]})
        except Exception as e:
            info['graphs'].append({'path': g, 'error': str(e)})
    if not cands:
        tgt = None
        for r in roots:
            sm = os.path.join(r, 'supportive modules')
            if os.path.isdir(sm): tgt = sm; break
        if gexe and tgt:
            log = os.path.join(run_dir, 'graphify_extract.log')
            flag = os.path.join(tgt, 'graphify-out', '.via_extract_running')
            os.makedirs(os.path.dirname(flag), exist_ok=True)
            open(flag, 'w').write(datetime.now().isoformat())
            subprocess.Popen([gexe, 'extract', tgt, '--code-only', '--no-viz'], cwd=tgt,
                             stdout=open(log, 'w'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            info['detached'] = {'target': tgt, 'log': log}
            put(4, 100, 'YELLOW', f'no graph yet; extract DETACHED on {os.path.basename(tgt)}')
        else:
            put(4, 100, 'YELLOW' if gexe else 'RED', 'graphify missing' if not gexe else 'no target')
        return info
    tot_n = sum(g.get('nodes', 0) for g in info['graphs'])
    put(4, 100, 'GREEN' if tot_n else 'YELLOW', f'graphs={len(cands)} nodes={tot_n}')
    return info

# ---------------- lane 5: tools ----------------
def tools_lane(roots):
    rows = []
    def add(tid, name, lamp, note): rows.append({'id': tid, 'name': name, 'lamp': lamp, 'note': note})
    put(5, 10, 'RUN', 'graphify')
    g = which('graphify'); add('TOOL-0001', 'Graphify', 'GREEN' if g else 'RED', g or 'missing')
    put(5, 25, 'RUN', 'omniroute')
    o = which('omniroute') or which('omni-route')
    try:
        import importlib.util as u
        spec = u.find_spec('omniroute')
    except Exception:
        spec = None
    add('TOOL-0003', 'OmniRoute', 'GREEN' if (o or spec) else 'GRAY', (o or ('pip:omniroute' if spec else 'unverified; not installed')))
    put(5, 45, 'RUN', 'playwright')
    try:
        import importlib.util as u
        pw = u.find_spec('playwright')
    except Exception:
        pw = None
    add('TOOL-0004', 'Playwright', 'GREEN' if (pw and which('npx')) else 'YELLOW', f"py={'OK' if pw else 'MISSING'} npx={'OK' if which('npx') else 'MISSING'}")
    put(5, 65, 'RUN', 'vcgc mcp')
    mcp = None
    for r in roots:
        reg = os.path.join(r, 'supportive modules', 'registry')
        if os.path.isdir(reg):
            vs = sorted([f for f in os.listdir(reg) if re.match(r'CGC_MDL279_MCPServer_v\d+\.py$', f)])
            if vs: mcp = os.path.join(reg, vs[-1]); break
    if mcp:
        rc, out = run([sys.executable, '-B', mcp, '--selftest'], os.path.dirname(mcp), 120)
        add('TOOL-0011', 'VCGC MCP', 'GREEN' if rc == 0 else 'RED', f'{os.path.basename(mcp)} rc={rc} ' + (out.splitlines()[-1][:80] if out else ''))
    else:
        add('TOOL-0011', 'VCGC MCP', 'YELLOW', 'CGC_MDL279_MCPServer not found under supportive modules/registry')
    put(5, 85, 'RUN', 'claude-mem / ponytail')
    home = os.path.expanduser('~')
    add('TOOL-0012', 'claude-mem', 'GREEN' if os.path.isdir(os.path.join(home, '.claude-mem')) else 'GRAY', '~/.claude-mem')
    add('TOOL-0002', 'Ponytail', 'GREEN' if which('node') else 'GRAY', 'node present' if which('node') else 'node missing')
    worst = 'GREEN'
    for x in rows:
        if x['lamp'] == 'RED': worst = 'RED'
        elif x['lamp'] in ('YELLOW',) and worst != 'RED': worst = 'YELLOW'
    put(5, 100, worst, f'tools={len(rows)}')
    return rows

# ---------------- cross-root analysis ----------------
def cross(invA, invB):
    conflicts, dups, diverge = [], [], []
    # exact relative-path match first (same place in both roots); versioned script names also matched by name
    for k in sorted(set(invA) & set(invB)):
        a, b = invA[k], invB[k]
        if a['sha'] == b['sha']:
            dups.append((a['rel'], b['rel']))
        elif not a['sha'].startswith(('BIG', 'ERR')):
            conflicts.append({'name': a['name'], 'A': a['rel'], 'B': b['rel'], 'sizeA': a['size'], 'sizeB': b['size'], 'match': 'relpath'})
    seen = {(c['A'].lower(), c['B'].lower()) for c in conflicts}
    byname_A = defaultdict(list); byname_B = defaultdict(list)
    for k, v in invA.items():
        if v['ver'] is not None: byname_A[v['name']].append(v)
    for k, v in invB.items():
        if v['ver'] is not None: byname_B[v['name']].append(v)
    for name in sorted(set(byname_A) & set(byname_B)):
        for a in byname_A[name]:
            for b in byname_B[name]:
                if (a['rel'].lower(), b['rel'].lower()) in seen or a['rel'].lower() == b['rel'].lower():
                    continue
                if a['sha'] == b['sha']:
                    dups.append((a['rel'], b['rel']))
                elif not a['sha'].startswith(('BIG', 'ERR')):
                    conflicts.append({'name': name, 'A': a['rel'], 'B': b['rel'], 'sizeA': a['size'], 'sizeB': b['size'], 'match': 'versioned-name'})
    famA = defaultdict(int); famB = defaultdict(int)
    for v in invA.values():
        if v['ver'] is not None: famA[v['fam']] = max(famA[v['fam']], v['ver'])
    for v in invB.values():
        if v['ver'] is not None: famB[v['fam']] = max(famB[v['fam']], v['ver'])
    for fam in sorted(set(famA) & set(famB)):
        if famA[fam] != famB[fam]:
            diverge.append({'family': fam, 'maxA': famA[fam], 'maxB': famB[fam]})
    return conflicts, dups, diverge

@shield
def main():
    run_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    roots = [a for a in sys.argv[2:] if os.path.isdir(a)]
    os.makedirs(run_dir, exist_ok=True)
    # repos: roots' git tops + known siblings
    repos = []
    for r in roots:
        cur = r
        for _ in range(4):
            if os.path.isdir(os.path.join(cur, '.git')): repos.append(cur); break
            nxt = os.path.dirname(cur)
            if nxt == cur: break
            cur = nxt
    home = os.path.expanduser('~')
    for extra in (os.path.join(home, 'VIA-VDF-VRN'), os.path.join(home, 'VIA-VERB-ENGINE'), os.path.join(home, 'movies-dataset')):
        if os.path.isdir(os.path.join(extra, '.git')) and extra not in repos: repos.append(extra)
    res = {}
    stop = threading.Event()
    def ticker():
        order = ['L1 root A inventory', 'L2 root B inventory', 'L3 GitHub (local git)', 'L4 Graphify graph', 'L5 Tools enable/check']
        while not stop.is_set():
            with LOCK:
                parts = []
                tot = 0
                for i, nm in enumerate(order, 1):
                    l = LANES.get(i, {'pct': 0, 'state': 'WAIT', 'msg': ''})
                    tot += l['pct']; parts.append(f"{nm[:4]} {l['pct']:3d}% {l['state'][:1]}")
            sys.stdout.write('\r' + ' | '.join(parts) + f' | TOTAL {tot//5:3d}%   ')
            sys.stdout.flush(); time.sleep(0.5)
    th = threading.Thread(target=ticker, daemon=True); th.start()
    with ThreadPoolExecutor(max_workers=5) as ex:
        fA = ex.submit(inventory, 1, roots[0]) if roots else None
        fB = ex.submit(inventory, 2, roots[1]) if len(roots) > 1 else None
        fG = ex.submit(git_lane, repos)
        fR = ex.submit(graph_lane, roots, run_dir)
        fT = ex.submit(tools_lane, roots)
        invA = fA.result() if fA else {}
        invB = fB.result() if fB else {}
        if not fB: put(2, 100, 'GRAY', 'single root')
        res['git'] = fG.result(); res['graph'] = fR.result(); res['tools'] = fT.result()
    stop.set(); th.join(1); print()
    conflicts, dups, diverge = cross(invA, invB)
    # TEMP zone proposals (no constitution rights): deterministic ids over sorted keys; VCGC/CGE issues formal numbers
    temp = []
    for i, c in enumerate(sorted(conflicts, key=lambda c: c['name']), 1):
        temp.append({'temp_id': f'TEMP-{i:04d}', 'kind': 'CONFLICT', 'conflict_id': f'CONFLICT-{i:05d}', **c})
    off = len(temp)
    for i, d in enumerate(sorted(diverge, key=lambda d: d['family']), 1):
        temp.append({'temp_id': f'TEMP-{off+i:04d}', 'kind': 'DIVERGENCE', **d})
    json.dump({'roots': roots, 'repos': repos, 'countA': len(invA), 'countB': len(invB), 'dups': len(dups),
               'conflicts': conflicts, 'diverge': diverge, 'temp_zone': temp, 'git': res['git'],
               'graph': res['graph'], 'tools': res['tools'], 'lanes': LANES},
              open(os.path.join(run_dir, 'panorama2.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(os.path.join(run_dir, 'VIA_ConflictRegistry_proposed.jsonl'), 'w', encoding='utf-8') as f:
        for t in temp: f.write(json.dumps(t, ensure_ascii=False) + '\n')
    # HTML
    lamp_css = ('.l{display:inline-block;width:12px;height:12px;border-radius:50%}.GREEN{background:#2EB872}.YELLOW{background:#F5C518}'
                '.GRAY{background:#9AA3AD}.RED{background:#E0342B;animation:bl 1.6s infinite}@keyframes bl{50%{opacity:.25}}'
                'body{font:12px/1.4 "Segoe UI",system-ui;background:#F7F8FA;color:#1F2937;margin:16px}table{border-collapse:collapse;background:#fff;max-width:1200px;width:100%}'
                'th,td{border:1px solid #E5E7EB;padding:3px 7px;text-align:left}th{background:#EEF1F5}h1{font-size:15px;margin:12px 0 6px}')
    def tr(cells, lamp=None):
        return '<tr>' + (f"<td><span class='l {lamp}'></span></td>" if lamp else '') + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
    order = ['L1 root A inventory', 'L2 root B inventory', 'L3 GitHub (local git)', 'L4 Graphify graph', 'L5 Tools enable/check']
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>VIA Panorama2</title><style>{lamp_css}</style></head><body>",
         f"<h1>VIA Panorama2 &middot; {datetime.now():%Y-%m-%d %H:%M}</h1><small>A={roots[0] if roots else ''}<br>B={roots[1] if len(roots)>1 else '-'}</small>",
         '<h1>Lanes</h1><table><tr><th></th><th>Lane</th><th>%</th><th>Result</th></tr>']
    for i, nm in enumerate(order, 1):
        l = LANES.get(i, {'pct': 0, 'state': 'GRAY', 'msg': ''}); h.append(tr([nm, l['pct'], l['msg']], l['state']))
    h.append(f"</table><h1>Cross-root</h1><table><tr><th>A files</th><th>B files</th><th>Identical dups</th><th>Same-name conflicts</th><th>Version divergences</th></tr>{tr([len(invA), len(invB), len(dups), len(conflicts), len(diverge)])}</table>")
    h.append('<h1>TEMP zone (no constitution rights until VCGC issues a formal number)</h1><table><tr><th></th><th>TEMP</th><th>Kind</th><th>Detail</th></tr>')
    for t in temp[:300]:
        d = f"{t['name']} | A:{t['A']} ({t['sizeA']}B) | B:{t['B']} ({t['sizeB']}B)" if t['kind'] == 'CONFLICT' else f"{t['family']} | A max v{t['maxA']} | B max v{t['maxB']}"
        h.append(tr([t['temp_id'], t['kind'], d], 'RED' if t['kind'] == 'CONFLICT' else 'YELLOW'))
    h.append('</table><h1>Git</h1><table><tr><th></th><th>Repo</th><th>Branch</th><th>Dirty</th><th>Ahead</th><th>Behind</th><th>7d</th><th>Tracked</th></tr>')
    for g in res['git']:
        h.append(tr([g['repo'], g.get('branch', ''), g.get('dirty', ''), g.get('ahead', ''), g.get('behind', ''), g.get('commits_7d', ''), g.get('tracked', g.get('note', ''))], g['lamp']))
    h.append('</table><h1>Graphify</h1><table><tr><th>Graph</th><th>Nodes</th><th>Edges</th><th>Orphans</th><th>Hubs</th></tr>')
    for g in res['graph'].get('graphs', []):
        h.append(tr([g['path'], g.get('nodes', g.get('error', '')), g.get('edges', ''), g.get('orphans', ''), ', '.join(g.get('hubs', []))]))
    h.append('</table><h1>Tools</h1><table><tr><th></th><th>ID</th><th>Tool</th><th>Note</th></tr>')
    for t in res['tools']:
        h.append(tr([t['id'], t['name'], t['note']], t['lamp']))
    h.append('</table></body></html>')
    html = os.path.join(run_dir, 'VIA_Panorama2.html')
    open(html, 'w', encoding='utf-8').write('\n'.join(h))
    # paste pack <= 300 lines
    pp = [f'PANORAMA2 {datetime.now():%Y-%m-%d %H:%M} A={roots[0] if roots else "-"} B={roots[1] if len(roots)>1 else "-"}']
    for i, nm in enumerate(order, 1):
        l = LANES.get(i, {'pct': 0, 'state': 'GRAY', 'msg': ''}); pp.append(f"{l['state']} {nm} {l['msg']}")
    pp.append(f'CROSS A={len(invA)} B={len(invB)} dups={len(dups)} conflicts={len(conflicts)} divergences={len(diverge)} temp_zone={len(temp)}')
    for g in res['git']:
        pp.append(f"{g['lamp']} GIT {os.path.basename(g['repo'])} br={g.get('branch','')} dirty={g.get('dirty','')} ahead={g.get('ahead','')} behind={g.get('behind','')} 7d={g.get('commits_7d','')}")
    for g in res['graph'].get('graphs', []):
        pp.append(f"GRAPH {g['path']} nodes={g.get('nodes','')} edges={g.get('edges','')} orphans={g.get('orphans','')} hubs={' '.join(g.get('hubs', []))[:120]}")
    if res['graph'].get('detached'): pp.append(f"YELLOW GRAPH extract detached target={res['graph']['detached']['target']}")
    for t in res['tools']:
        pp.append(f"{t['lamp']} {t['id']} {t['name']} {t['note'][:90]}")
    pp.append('--- TOP CONFLICTS (same name, different content) ---')
    for t in [x for x in temp if x['kind'] == 'CONFLICT'][:60]:
        pp.append(f"{t['conflict_id']} {t['name']} A={t['sizeA']}B B={t['sizeB']}B {t['A']}")
    pp.append('--- TOP DIVERGENCES (version families) ---')
    for t in [x for x in temp if x['kind'] == 'DIVERGENCE'][:40]:
        pp.append(f"{t['temp_id']} {t['family']} A=v{t['maxA']} B=v{t['maxB']}")
    pp.append(f'HTML={html}')
    pp.append(f'JSON={os.path.join(run_dir, "panorama2.json")}')
    pp = pp[:299]
    pp.append('NEXT: paste this pack back; VCGC/CGE issues formal numbers only for TEMP entries you and the AI resolve')
    open(os.path.join(run_dir, 'paste_pack.txt'), 'w', encoding='utf-8').write('\n'.join(pp))
    print('\n'.join(pp))
    return 0

if __name__ == '__main__':
    sys.exit(main() or 0)
