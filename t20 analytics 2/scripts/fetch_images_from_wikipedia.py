import os, csv, requests, sys

base = r'c:\Users\diwaa\OneDrive\Desktop\t20 analytics'
imgdir = os.path.join(base, 'static', 'images')
csvp = os.path.join(base, 'data', 'player_image_map.csv')

if not os.path.isdir(imgdir):
    print('ERROR: images dir not found:', imgdir)
    sys.exit(1)
if not os.path.isfile(csvp):
    print('ERROR: csv mapping not found:', csvp)
    sys.exit(1)

files = set(os.listdir(imgdir))
rows = []
changed = 0
fetched = 0
failed = []

with open(csvp, 'r', encoding='utf-8') as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        rows.append(r)

session = requests.Session()
session.headers.update({'User-Agent': 'T20AnalyticsImageFetcher/1.0 (contact: you@example.com)'} )

for r in rows:
    name = r.get('full_name','').strip()
    target = r.get('filename','').strip()
    if not name or not target:
        continue
    # If the target already exists, skip
    if target in files:
        continue
    print('Trying:', name)
    wiki_name = name.replace(' ', '_')
    api = f'https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}'
    try:
        resp = session.get(api, timeout=8)
        if resp.status_code != 200:
            print('  No wiki page (status):', resp.status_code)
            failed.append((name, 'no_page'))
            continue
        j = resp.json()
        thumb = j.get('thumbnail') or j.get('originalimage')
        if not thumb or not thumb.get('source'):
            print('  No thumbnail for', name)
            failed.append((name, 'no_thumb'))
            continue
        url = thumb.get('source')
        print('  Found thumbnail:', url)
        # Download
        dresp = session.get(url, stream=True, timeout=15)
        if dresp.status_code != 200:
            print('  Download failed:', dresp.status_code)
            failed.append((name, 'download_failed'))
            continue
        # Determine extension
        url_path = url.split('?')[0]
        ext = os.path.splitext(url_path)[1]
        if not ext:
            ctype = dresp.headers.get('Content-Type','')
            if 'jpeg' in ctype:
                ext = '.jpg'
            elif 'png' in ctype:
                ext = '.png'
            elif 'svg' in ctype:
                ext = '.svg'
            else:
                ext = '.jpg'
        # Prepare filename: prefer the CSV target (replace spaces), but ensure extension
        name_base = target
        if os.path.splitext(name_base)[1] == '':
            name_base = name_base + ext
        else:
            # if target had an extension different from ext, keep target
            pass
        save_path = os.path.join(imgdir, name_base)
        with open(save_path, 'wb') as out:
            for chunk in dresp.iter_content(chunk_size=8192):
                if chunk:
                    out.write(chunk)
        print('  Saved to', name_base)
        # Update tracking
        files.add(name_base)
        if name_base != target:
            r['filename'] = name_base
            changed += 1
        fetched += 1
    except Exception as e:
        print('  Exception for', name, e)
        failed.append((name, str(e)))

# Write back CSV if changed
if changed > 0:
    with open(csvp, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['full_name','filename'])
        writer.writeheader()
        for r in rows:
            writer.writerow({'full_name': r.get('full_name',''), 'filename': r.get('filename','')})

print('\nDone. fetched=', fetched, 'changed=', changed, 'failed=', len(failed))
if failed:
    print('Failures sample:')
    for f in failed[:10]:
        print(' ', f)
