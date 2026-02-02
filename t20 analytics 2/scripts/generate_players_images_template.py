import csv
import json
import os

ROOT = os.path.dirname(__file__)
REPORT = os.path.join(ROOT, 'force_redownload_report.csv')
OUT = os.path.join(ROOT, '..', 'players_images.json.template')

rows = {}
with open(REPORT, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        name = row.get('name','').strip()
        result = row.get('result','').strip()
        if not name:
            continue
        if result != 'downloaded':
            rows[name] = ""

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)

print('Wrote', OUT)
