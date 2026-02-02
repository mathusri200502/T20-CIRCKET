
import os
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'images')
import json
import re
import csv
import time
import requests
"""
Process `data/players_images.json`.
For each entry, try downloading from Bing using the provided image id (OIP/ODL/OIF etc.).
If that fails, fall back to Wikipedia lookup by player name.
Writes a CSV report at the end.
"""

PLAYERS_IMAGES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'players_images.json')

def download_from_bing_id(image_id, target_filename=None):
    """Try to download an image given a Bing id like 'OIP.<hash>' or 'ODL.<hash>'.
    Returns saved filename or None on failure."""
    if not image_id:
        return None
    # ensure no extension on id
    id_part = image_id
    # if given a filename with ext, remove ext for ID
    id_part = os.path.splitext(id_part)[0]
    # common mm.bing.net hosts to try
    hosts = ["tse1.mm.bing.net", "tse2.mm.bing.net", "tse3.mm.bing.net", "tse4.mm.bing.net", "cc.bingj.com"]
    for host in hosts:
        url = f"https://{host}/th?id={id_part}&pid=Api"
        try:
            r = requests.get(url, timeout=12)
            if r.status_code == 200 and r.content:
                # determine extension
                ct = r.headers.get('content-type','').lower()
                if 'png' in ct:
                    ext = '.png'
                else:
                    ext = '.jpg'
                if not target_filename:
                    target_filename = id_part + ext
                target_path = os.path.join(OUT_DIR, target_filename)
                with open(target_path, 'wb') as f:
                    f.write(r.content)
                return target_filename
        except Exception:
            continue
    return None

def download_players_images():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(PLAYERS_IMAGES_FILE, 'r', encoding='utf-8') as f:
        plist = json.load(f)
    report = []
    for item in plist:
        name = item.get('name')
        image_id = item.get('image')
        saved = None
        # check if file already exists locally
        candidates = []
        if os.path.splitext(image_id)[1]:
            candidates.append(image_id)
        else:
            candidates.append(image_id + '.jpg')
            candidates.append(image_id + '.png')
        for c in candidates:
            if os.path.exists(os.path.join(OUT_DIR, c)):
                saved = c
                break
        if not saved:
            # try Bing id download
            saved = download_from_bing_id(image_id)
        if not saved:
            # fallback to Wikipedia lookup for the player name
            # reuse existing wiki logic from later in file: perform a query for pageimages
            params = {
                'action':'query',
                'format':'json',
                'titles': name,
                'prop':'pageimages|info',
                'piprop':'original|thumbnail',
                'pithumbsize':400,
                'redirects':1
            }
            try:
                r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
                data = r.json()
                pages = data.get('query',{}).get('pages',{})
                for pid, page in pages.items():
                    if 'missing' in page:
                        continue
                    thumb = page.get('thumbnail') or page.get('original')
                    fullurl = thumb.get('source') if thumb else ''
                    if fullurl:
                        resp = requests.get(fullurl, headers=HEADERS, timeout=15)
                        if resp.status_code == 200:
                            # choose filename
                            fname = make_filename(name)
                            out_path = os.path.join(OUT_DIR, fname)
                            with open(out_path, 'wb') as out:
                                out.write(resp.content)
                            saved = fname
                            break
            except Exception as e:
                report.append((name, image_id, 'error', str(e), ''))
                continue
        if saved:
            report.append((name, image_id, 'downloaded', '', saved))
        else:
            report.append((name, image_id, 'not_found', '', ''))
        time.sleep(0.2)
    # write report
    with open(REPORT_CSV, 'w', newline='', encoding='utf-8') as csvf:
        w = csv.writer(csvf)
        w.writerow(['name','image_id','status','note','saved_filename'])
        for row in report:
            w.writerow(row)
    succ = sum(1 for r in report if r[2]=='downloaded')
    notf = sum(1 for r in report if r[2]=='not_found')
    err = sum(1 for r in report if r[2]=='error')
    print(f'Downloaded: {succ}, Not found: {notf}, Errors: {err}')
    print('Report written to', REPORT_CSV)

if __name__ == '__main__':
    download_players_images()


ROOT = os.path.dirname(__file__)
OUT_DIR = os.path.join(ROOT, '..', 'static', 'images')
DATA_FILE = os.path.join(ROOT, '..', 'data', 't20_wc_player_info.json')
FILENAME_SCRIPT = os.path.join(ROOT, 'generate_image_filenames.py')
REPORT_CSV = os.path.join(ROOT, 'image_download_report.csv')
PLACEHOLDER = os.path.join(OUT_DIR, 'placeholder.png')

# reuse filename logic
import importlib.util
spec = importlib.util.spec_from_file_location('gen', FILENAME_SCRIPT)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
make_filename = gen.make_filename

WIKI_API = 'https://en.wikipedia.org/w/api.php'
HEADERS = {'User-Agent': 't20-analytics-image-downloader/1.0 (email@example.com)'}

os.makedirs(OUT_DIR, exist_ok=True)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    players = json.load(f)

results = []

for p in players:
    name = p.get('name','').strip()
    if not name:
        continue
    fname = make_filename(name)
    out_path = os.path.join(OUT_DIR, fname)
    # Query Wiki for a page with this exact name
    params = {
        'action':'query',
        'format':'json',
        'titles': name,
        'prop':'pageimages|info',
        'piprop':'original|thumbnail',
        'pithumbsize':400,
        'redirects':1
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        data = r.json()
    except Exception as e:
        results.append((name, fname, 'error', str(e), ''))
        time.sleep(0.5)
        continue
    pages = data.get('query',{}).get('pages',{})
    found = False
    for pid, page in pages.items():
        if 'missing' in page:
            continue
        thumb = page.get('thumbnail') or page.get('original')
        fullurl = ''
        if thumb:
            fullurl = thumb.get('source')
        # also capture page URL
        pageurl = 'https://en.wikipedia.org/?curid=' + str(page.get('pageid')) if page.get('pageid') else ''
        if fullurl:
            try:
                resp = requests.get(fullurl, headers=HEADERS, timeout=15)
                if resp.status_code == 200:
                    with open(out_path, 'wb') as out:
                        out.write(resp.content)
                    # attempt to get license info via Wikimedia Commons (skip deep license lookup)
                    results.append((name, fname, 'downloaded', pageurl, fullurl))
                    found = True
                    break
            except Exception as e:
                results.append((name, fname, 'error', str(e), fullurl))
                found = True
                break
    if not found:
        results.append((name, fname, 'not_found', '', ''))
    time.sleep(0.3)

# write report CSV
with open(REPORT_CSV, 'w', newline='', encoding='utf-8') as csvf:
    w = csv.writer(csvf)
    w.writerow(['name','filename','status','page_url','image_url'])
    for row in results:
        w.writerow(row)

# print summary
succ = sum(1 for r in results if r[2]=='downloaded')
notf = sum(1 for r in results if r[2]=='not_found')
err = sum(1 for r in results if r[2]=='error')
print(f'Downloaded: {succ}, Not found: {notf}, Errors: {err}')
print('Report written to', REPORT_CSV)
