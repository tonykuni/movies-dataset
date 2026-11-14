# [VIA:ACCEL-BRIDGE] CGC_AccelInject_v0101 - every engine of every system onto the LATEST accelerator, by AST injection into joined copies
# Scope: <root>\functional modules\{VDF,VRN,VQG,VAP}\**  +  <root>\supportive modules\registry (VCGC)  +  DB (ParquetLake / *Lake*)
# Rules: originals never edited (append-only law); joined copies land in <root>\supportive modules\_vcjoin\<ts>\<relpath>;
#        SUCCESS LOCK book appended (sha + mtime + version) for files that already comply; policy matrix per system.
import os, sys, re, ast, json, hashlib, time
from datetime import datetime
from collections import defaultdict
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

EXCL = {'.venv', 'venv', 'node_modules', '__pycache__', '.git', '_superseded', 'graphify-out', '_intake', '_vcjoin', '_superseded_redundant', 'references'}
ACCEL_RE = re.compile(r'via_superaccel_module|ACCEL[-_ ]?BRIDGE|VeritasCeleritas_v\d+|CELERITAS-TEMPLATE-JOIN|VIA:PS-ACCEL|Invoke-VCPython|AutoImport\.ps1')
NET_RE   = re.compile(r'NET[-_ ]?BRIDGE|VIA_NET_TOOL_PATH|_via_net\b|VeritasAegisNexus|NetUnified')
OUTBOUND_RE = re.compile(r'(?m)^\s*(import|from)\s+(requests|urllib|httpx|aiohttp|yfinance|akshare|playwright|selenium|websocket)\b|Invoke-WebRequest|Invoke-RestMethod|HttpClient')
FORBID = {'py': [(r'(?m)^\s*(import\s+talib|from\s+talib\b)', 'TA-Lib'), (r'(?m)^\s*[^#]*\binput\(', 'input()'), (r'consent[_ ]?(write|approve)\s*=\s*True', 'consent-write')],
          'ps': [(r'Invoke-Expression|\biex\b', 'Invoke-Expression'), (r'Net\.WebClient', 'WebClient'), (r'HKLM:', 'HKLM'), (r'Stop-Process\s+-Id\s+(?!\$PID)', 'Stop-Process other PID'), (r'talib', 'TA-Lib')]}
VER_RE = re.compile(r'_v(\d{3,4})(?:[_\-.]|$)', re.I)
SYSTEMS = {'VDF': ['functional modules/VDF'], 'VRN': ['functional modules/VRN'], 'VQG': ['functional modules/VQG'], 'VAP': ['functional modules/VAP'],
           'VCGC': ['supportive modules/registry'], 'DB': ['functional modules/DB', 'supportive modules/lake']}

def read(p, n=2000000):
    try:
        with open(p, 'r', encoding='utf-8', errors='replace') as f: return f.read(n)
    except Exception: return ''
def sha_norm(p):
    d = open(p, 'rb').read()
    if d.startswith(b'\xef\xbb\xbf'): d = d[3:]
    return hashlib.sha256(d.replace(b'\r\n', b'\n').replace(b'\r', b'\n')).hexdigest()
def walk(d, exts):
    for dp, dns, fns in os.walk(d):
        dns[:] = [x for x in dns if x not in EXCL and not x.startswith(('RUN_', 'VIA_RUN_'))]
        for fn in fns:
            if os.path.splitext(fn)[1].lower() in exts: yield os.path.join(dp, fn)

def latest_accel(root):
    """pick the newest python accelerator and PS accelerator available under supportive modules"""
    sm = os.path.join(root, 'supportive modules'); py_mod, ps_mod = None, None
    if os.path.isdir(sm):
        cands = []
        for p in walk(sm, {'.py'}):
            n = os.path.basename(p)
            if n == 'via_superaccel_module.py': cands.append((9999, os.path.getmtime(p), 'via_superaccel_module', p))
            m = re.match(r'(VeritasCeleritas_v(\d+))\.py$', n)
            if m: cands.append((int(m.group(2)), os.path.getmtime(p), m.group(1), p))
        if cands: cands.sort(); py_mod = cands[-1]
        pcs = []
        for p in walk(sm, {'.ps1', '.psm1'}):
            n = os.path.basename(p)
            if n == 'VeritasCeleritas.PS7.AutoImport.ps1': pcs.append((2, os.path.getmtime(p), p))
            elif re.search(r'PS-?ACCEL|PSAccel|Celeritas\.PS7\.Template', n, re.I): pcs.append((1, os.path.getmtime(p), p))
        if pcs: pcs.sort(); ps_mod = pcs[-1][2]
    return py_mod, ps_mod

def py_insert_index(src):
    """AST: line index after module docstring and __future__ imports"""
    try:
        t = ast.parse(src)
    except Exception:
        return None
    idx = 0
    body = t.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) and isinstance(body[0].value.value, str):
        idx = body[0].end_lineno
    for n in body:
        if isinstance(n, ast.ImportFrom) and n.module == '__future__': idx = max(idx, n.end_lineno)
    return idx

@shield
def main():
    run_dir = sys.argv[1]; roots = [a for a in sys.argv[2:] if os.path.isdir(a)]
    os.makedirs(run_dir, exist_ok=True); ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    root = roots[0] if roots else run_dir
    py_mod, ps_mod = latest_accel(root)
    py_name = py_mod[2] if py_mod else 'VeritasCeleritas_v1141'
    pp = [f'ACCEL-INJECT {ts} root={root}', f"latest PY accel = {py_name} ({os.path.basename(py_mod[3]) if py_mod else 'not found under supportive modules; using name only'})",
          f"latest PS accel = {os.path.basename(ps_mod) if ps_mod else 'NOT FOUND (AutoImport / PS-ACCEL)'}"]
    join_root = os.path.join(root, 'supportive modules', '_vcjoin', ts)
    lock_path = os.path.join(root, 'supportive modules', 'ssot', 'VIA_SuccessLock_v0101.jsonl')
    rows = []; per_sys = defaultdict(lambda: defaultdict(int)); locks = []
    for sysn, rels in SYSTEMS.items():
        for rel in rels:
            d = os.path.join(root, *rel.split('/'))
            if not os.path.isdir(d): continue
            for p in walk(d, {'.py', '.ps1'}):
                kind = 'py' if p.lower().endswith('.py') else 'ps'
                txt = read(p); relp = os.path.relpath(p, root)
                accel = bool(ACCEL_RE.search(txt)); net = bool(NET_RE.search(txt)); outbound = bool(OUTBOUND_RE.search(txt))
                forb = [lab for rx, lab in FORBID[kind] if re.search(rx, txt)]
                comp = 'n/a'
                if kind == 'py':
                    try: compile(txt, p, 'exec'); comp = 'OK'
                    except Exception as e: comp = f'ERR {str(e)[:50]}'
                else:
                    comp = 'OK' if (txt.count('{') == txt.count('}') and txt.count('(') == txt.count(')')) else 'ERR bracket-unbalanced'
                m = VER_RE.search(os.path.splitext(os.path.basename(p))[0]); ver = int(m.group(1)) if m else None
                need_net = outbound and not net
                compliant = comp == 'OK' and accel and not forb and not need_net
                per_sys[sysn]['files'] += 1; per_sys[sysn]['accel'] += int(accel); per_sys[sysn]['compliant'] += int(compliant)
                per_sys[sysn]['forbid'] += int(bool(forb)); per_sys[sysn]['need_net'] += int(need_net); per_sys[sysn]['compile_err'] += int(comp != 'OK')
                landed = ''
                if not accel and comp == 'OK' and not forb:
                    dst = os.path.join(join_root, relp); os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if kind == 'py':
                        i = py_insert_index(txt)
                        if i is not None:
                            lines = txt.splitlines(True)
                            block = (f'# [VIA:ACCEL-BRIDGE] auto-joined {ts[:8]} via AST (original untouched) · latest={py_name}\n'
                                     f'try:\n    import {py_name} as _via_accel\nexcept Exception:\n    _via_accel = None\n')
                            out = ''.join(lines[:i]) + block + ''.join(lines[i:])
                            try: compile(out, dst, 'exec'); open(dst, 'w', encoding='utf-8').write(out); landed = dst
                            except Exception as e: landed = f'INJECT-FAIL {str(e)[:40]}'
                    else:
                        guard = (f'# CELERITAS-TEMPLATE-JOIN  [VIA:PS-ACCEL] auto-joined {ts[:8]} (original untouched)\n#Requires -Version 7.0\n'
                                 + (f'if (Test-Path "{ps_mod}") {{ . "{ps_mod}" }}\n' if ps_mod else 'if ($env:VIA_CELERITAS_ROOT -and (Test-Path (Join-Path $env:VIA_CELERITAS_ROOT "VeritasCeleritas.PS7.AutoImport.ps1"))) { . (Join-Path $env:VIA_CELERITAS_ROOT "VeritasCeleritas.PS7.AutoImport.ps1") }\n'))
                        body = re.sub(r'(?m)^\s*#Requires -Version [\d\.]+\s*\n', '', txt)
                        open(dst, 'w', encoding='utf-8').write(guard + body); landed = dst
                    per_sys[sysn]['joined_copies'] += int(bool(landed) and not landed.startswith('INJECT-FAIL'))
                if compliant:
                    locks.append({'ts': ts, 'system': sysn, 'file': relp, 'ver': ver, 'sha256_norm': sha_norm(p), 'mtime': datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec='seconds'), 'lock': 'SUCCESS'})
                rows.append({'system': sysn, 'file': relp, 'kind': kind, 'ver': ver, 'compile': comp, 'accel': accel, 'net': net, 'outbound': outbound, 'forbid': forb, 'compliant': compliant, 'joined_copy': landed})
    # success-lock book: append-only, skip entries already locked with same sha
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    have = set()
    if os.path.exists(lock_path):
        for l in read(lock_path).splitlines():
            try: o = json.loads(l); have.add((o['file'], o['sha256_norm']))
            except Exception: pass
    new_locks = [x for x in locks if (x['file'], x['sha256_norm']) not in have]
    with open(lock_path, 'a', encoding='utf-8') as f:
        for x in new_locks: f.write(json.dumps(x, ensure_ascii=False) + '\n')
    json.dump({'ts': ts, 'py_accel': py_name, 'ps_accel': ps_mod, 'per_system': per_sys, 'rows': rows, 'locks_new': len(new_locks), 'lock_book': lock_path, 'join_root': join_root},
              open(os.path.join(run_dir, 'accelinject.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    pp.append('--- COVERAGE per system (compliant = compile OK + accel + no forbidden + net bridge if outbound) ---')
    for sysn in SYSTEMS:
        c = per_sys.get(sysn)
        if not c: pp.append(f'GRAY {sysn} no files under {SYSTEMS[sysn]}'); continue
        cov = int(100 * c['accel'] / max(1, c['files'])); comp = int(100 * c['compliant'] / max(1, c['files']))
        lamp = 'GREEN' if comp == 100 else ('RED' if c['forbid'] or c['compile_err'] else 'YELLOW')
        pp.append(f"{lamp} {sysn} files={c['files']} accel={cov}% compliant={comp}% forbid={c['forbid']} compile_err={c['compile_err']} need_net_bridge={c['need_net']} joined_copies={c['joined_copies']}")
    pp.append(f'LOCK book {lock_path} +{len(new_locks)} (total compliant now {len(locks)})')
    pp.append(f'JOINED copies -> {join_root}')
    pp.append('--- POLICY VIOLATIONS (first 40) ---')
    for r in [x for x in rows if x['forbid'] or x['compile'] != 'OK'][:40]: pp.append(f"RED {r['system']} {r['file'][:80]} {','.join(r['forbid'])} {r['compile'] if r['compile'] != 'OK' else ''}")
    pp.append('--- OUTBOUND WITHOUT NET BRIDGE (first 30) ---')
    for r in [x for x in rows if x['outbound'] and not x['net']][:30]: pp.append(f"YELLOW {r['system']} {r['file'][:90]}")
    css = '.l{display:inline-block;width:12px;height:12px;border-radius:50%}.GREEN{background:#2EB872}.YELLOW{background:#F5C518}.GRAY{background:#9AA3AD}.RED{background:#E0342B;animation:bl 1.6s infinite}@keyframes bl{50%{opacity:.25}}body{font:12px/1.4 "Segoe UI",system-ui;background:#F7F8FA;color:#1F2937;margin:16px}table{border-collapse:collapse;background:#fff;width:100%;max-width:1200px}th,td{border:1px solid #E5E7EB;padding:3px 7px;text-align:left}th{background:#EEF1F5}h1{font-size:15px;margin:12px 0 6px}'
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>VIA AccelInject</title><style>{css}</style></head><body><h1>Accelerator injection &middot; {ts}</h1><table><tr><th></th><th>Line</th></tr>"]
    for l in pp: h.append(f"<tr><td><span class='l {l.split()[0] if l.split()[0] in ('GREEN','YELLOW','RED','GRAY') else ''}'></span></td><td>{l}</td></tr>")
    h.append('</table><h1>Files</h1><table><tr><th></th><th>Sys</th><th>File</th><th>v</th><th>compile</th><th>accel</th><th>net</th><th>forbid</th><th>joined copy</th></tr>')
    for r in rows[:1500]: h.append(f"<tr><td><span class='l {'GREEN' if r['compliant'] else ('RED' if r['forbid'] or r['compile']!='OK' else 'YELLOW')}'></span></td><td>{r['system']}</td><td>{r['file']}</td><td>{r['ver'] or ''}</td><td>{r['compile']}</td><td>{r['accel']}</td><td>{r['net']}</td><td>{','.join(r['forbid'])}</td><td>{r['joined_copy']}</td></tr>")
    h.append('</table></body></html>'); html = os.path.join(run_dir, 'VIA_AccelInject.html'); open(html, 'w', encoding='utf-8').write('\n'.join(h))
    pp.append(f'HTML={html}'); pp = pp[:299]; pp.append('NEXT: paste coverage lines back; joined copies are proposals (TEMP), promote via thin-tail versions only after VCGC number issue')
    open(os.path.join(run_dir, 'paste_pack.txt'), 'w', encoding='utf-8').write('\n'.join(pp)); print('\n'.join(pp)); return 0

if __name__ == '__main__':
    sys.exit(main() or 0)
