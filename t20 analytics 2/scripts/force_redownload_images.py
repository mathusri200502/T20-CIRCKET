import os
import csv
import requests
import shutil
from datetime import datetime

ROOT = os.path.dirname(__file__)
MAP_CSV = os.path.join(ROOT, '..', 'data', 'player_image_map.csv')
REPORT_CSV = os.path.join(ROOT, 'image_download_report.csv')
OUT_DIR = os.path.join(ROOT, '..', 'static', 'images')
BACKUP_DIR = os.path.join(ROOT, 'images_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# load mapping
mapping = []
with open(MAP_CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        mapping.append({'name': row['full_name'].strip(), 'filename': row['filename'].strip()})

# load report into dict by name
report_by_name = {}
with open(REPORT_CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        name = row.get('name','').strip()
        image_url = row.get('image_url','').strip()
        if not name:
            continue
        report_by_name[name] = image_url

print('Backing up existing images to', BACKUP_DIR)
# backup existing files that are in mapping
for m in mapping:
    src = os.path.join(OUT_DIR, m['filename'])
    if os.path.exists(src):
        dst = os.path.join(BACKUP_DIR, m['filename'])
        shutil.copy2(src, dst)

# redownload and overwrite
results = []
for m in mapping:
    name = m['name']
    fname = m['filename']
    image_url = report_by_name.get(name)
    target = os.path.join(OUT_DIR, fname)
    if not image_url:
        results.append((name, fname, 'no_url', ''))
        continue
    try:
        r = requests.get(image_url, timeout=30, headers={'User-Agent':'t20-analytics/1.0'})
        if r.status_code == 200:
            with open(target, 'wb') as out:
                out.write(r.content)
            results.append((name, fname, 'downloaded', image_url))
            print('Downloaded', fname)
        else:
            results.append((name, fname, f'http_{r.status_code}', image_url))
            print('Failed', name, 'http', r.status_code)
    except Exception as e:
        results.append((name, fname, f'error:{e}', image_url))
        print('Error', name, e)

# write report
OUT_REPORT = os.path.join(ROOT, 'force_redownload_report.csv')
with open(OUT_REPORT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['name','filename','result','image_url'])
    for r in results:
        w.writerow(r)

print('Done. Report:', OUT_REPORT)
