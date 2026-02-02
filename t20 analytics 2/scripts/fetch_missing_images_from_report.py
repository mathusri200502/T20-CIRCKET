import os
import csv
import requests

ROOT = os.path.dirname(__file__)
MAP_CSV = os.path.join(ROOT, '..', 'data', 'player_image_map.csv')
REPORT_CSV = os.path.join(ROOT, 'image_download_report.csv')
OUT_DIR = os.path.join(ROOT, '..', 'static', 'images')
OUT_REPORT = os.path.join(ROOT, 'missing_image_downloads.csv')

os.makedirs(OUT_DIR, exist_ok=True)

# load mapping
mapping = []
with open(MAP_CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        mapping.append({'name': row['full_name'].strip(), 'filename': row['filename'].strip()})

# load report into dict by name (prefer first match with image_url)
report_by_name = {}
with open(REPORT_CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        name = row.get('name','').strip()
        image_url = row.get('image_url','').strip()
        status = row.get('status','').strip()
        if not name:
            continue
        if name not in report_by_name and image_url:
            report_by_name[name] = {'image_url': image_url, 'status': status}

results = []
downloaded = 0
skipped = 0
not_found = 0
errors = 0

for m in mapping:
    name = m['name']
    fname = m['filename']
    target_path = os.path.join(OUT_DIR, fname)
    if os.path.exists(target_path):
        skipped += 1
        results.append((name, fname, 'exists', ''))
        continue
    info = report_by_name.get(name)
    if not info:
        not_found += 1
        results.append((name, fname, 'no_image_url', ''))
        continue
    image_url = info['image_url']
    try:
        r = requests.get(image_url, timeout=20, headers={'User-Agent': 't20-analytics-fetcher/1.0'})
        if r.status_code == 200:
            with open(target_path, 'wb') as out:
                out.write(r.content)
            downloaded += 1
            results.append((name, fname, 'downloaded', image_url))
            print(f'Downloaded {fname} for {name}')
        else:
            errors += 1
            results.append((name, fname, f'http_{r.status_code}', image_url))
            print(f'Failed HTTP {r.status_code} for {name} -> {image_url}')
    except Exception as e:
        errors += 1
        results.append((name, fname, f'error:{e}', image_url))
        print(f'Error downloading for {name}: {e}')

# write out report
with open(OUT_REPORT, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['name','filename','result','image_url'])
    for r in results:
        w.writerow(r)

print(f'Downloaded: {downloaded}, Skipped(existing): {skipped}, No URL: {not_found}, Errors: {errors}')
print('Report:', OUT_REPORT)
