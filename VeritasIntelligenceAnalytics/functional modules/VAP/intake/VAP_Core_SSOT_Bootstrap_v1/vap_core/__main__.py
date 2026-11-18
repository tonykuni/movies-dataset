import argparse
import json
from pathlib import Path
from .contracts import VAPContracts

p = argparse.ArgumentParser(description='Validate VAP SSOT / resolve configuration; does NOT render or compute indicators.')
p.add_argument('--root', type=Path)
p.add_argument('--chart', help='Resolve one chart code, e.g. VAP-CH-11')
p.add_argument('--out', type=Path)
a = p.parse_args()
c = VAPContracts(a.root)
result = c.resolve(a.chart) if a.chart else c.report()
text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
if a.out:
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding='utf-8')
    print(a.out)
else:
    print(text, end='')
