from __future__ import annotations
import json
from html.parser import HTMLParser
from pathlib import Path

root = Path('/home/ubuntu/work/movies-dataset/VeritasIntelligenceAnalytics')
out = root / 'VIA_Reports/vrn/nlp_pipeline'
html_path = out / 'NLP_VRN_VDF_latest.html'
json_path = out / 'NLP_VRN_VDF_latest.json'
md_path = out / 'NLP_VRN_VDF_latest.md'
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = set(); self.text = ''
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == 'id': self.ids.add(v)
    def handle_data(self, data): self.text += data
p = P(); p.feed(html_path.read_text(encoding='utf-8'))
payload = json.loads(json_path.read_text(encoding='utf-8'))
assert {'p1','p2','p3'} <= p.ids
assert all(x in p.text for x in ('第 1 頁', '第 2 頁', '第 3 頁'))
assert payload['report_artifacts']['html'].endswith('NLP_VRN_VDF_MATRIX.html')
assert payload['nlp']['processed'] == 2 and payload['nlp']['summary_ok'] == 2
assert payload['database']['state'] == 'GREEN'
assert 'VDF 阻擋原因' in md_path.read_text(encoding='utf-8')
print('html_pages=3 json=valid markdown=valid nlp=2/2 db=GREEN')
