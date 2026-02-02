import csv
import os
import requests
import urllib.parse

ROOT = os.path.dirname(__file__)
REPORT_CSV = os.path.join(ROOT, 'image_download_report.csv')
OUT_CSV = os.path.join(ROOT, 'image_license_metadata.csv')
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
HEADERS = {'User-Agent': 't20-analytics-image-metadata/1.0 (email@example.com)'}


def extract_filename_from_url(url):
    if not url:
        return None
    # decode and take last path component
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    # if path contains '/File:' use the part after /wiki/
    if '/wiki/File:' in path:
        return path.split('/wiki/')[1].replace('File:', 'File:')
    # else take last component
    parts = path.split('/')
    if not parts:
        return None
    last = parts[-1]
    # sometimes thumbnail urls have extra segments, try to detect 'thumb' pattern
    if 'thumb' in parts:
        # the file name may be after 'thumb/.../filename.ext'
        # find last component that looks like a filename containing a dot
        for p in reversed(parts):
            if '.' in p:
                return 'File:' + p
    # fallback
    if '.' in last:
        return 'File:' + last
    return None


def query_commons_for_file(file_title):
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'imageinfo',
        'titles': file_title,
        'iiprop': 'extmetadata|url'
    }
    try:
        r = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {'error': str(e)}


rows = []
with open(REPORT_CSV, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    # expected: name,filename,status,page_url,image_url
    for row in reader:
        name, local_fname, status, page_url, image_url = row
        if status != 'downloaded':
            continue
        file_title = extract_filename_from_url(image_url)
        if not file_title:
            rows.append([name, local_fname, image_url, 'no_file_detected', '', '', '', '', ''])
            continue
        data = query_commons_for_file(file_title)
        if 'error' in data:
            rows.append([name, local_fname, image_url, 'api_error', data['error'], '', '', '', file_title])
            continue
        pages = data.get('query', {}).get('pages', {})
        # there should be one page
        found = False
        for pid, page in pages.items():
            if 'missing' in page:
                rows.append([name, local_fname, image_url, 'missing_on_commons', '', '', '', '', file_title])
                found = True
                break
            iinfo = page.get('imageinfo')
            if not iinfo:
                rows.append([name, local_fname, image_url, 'no_imageinfo', '', '', '', '', file_title])
                found = True
                break
            i = iinfo[0]
            url = i.get('url','')
            ext = i.get('extmetadata', {})
            license = ext.get('LicenseShortName', {}).get('value','')
            license_url = ext.get('LicenseUrl', {}).get('value','')
            artist = ext.get('Artist', {}).get('value','')
            credit = ext.get('Credit', {}).get('value','')
            usage = ext.get('UsageTerms', {}).get('value','')
            rows.append([name, local_fname, image_url, 'ok', url, license, license_url, artist, credit, usage, file_title])
            found = True
            break
        if not found:
            rows.append([name, local_fname, image_url, 'unknown_response', '', '', '', '', '', '', file_title])

# write output CSV
out_headers = ['name','local_filename','image_url','status','file_url','license','license_url','artist','credit','usage_terms','commons_file_title']
with open(OUT_CSV, 'w', encoding='utf-8', newline='') as outf:
    w = csv.writer(outf)
    w.writerow(out_headers)
    for r in rows:
        w.writerow(r)

# summary
ok = sum(1 for r in rows if r[3]=='ok')
missing = sum(1 for r in rows if r[3]=='missing_on_commons')
errors = sum(1 for r in rows if r[3] in ('api_error','no_imageinfo','no_file_detected','unknown_response'))
print(f'OK: {ok}, missing_on_commons: {missing}, other_errors: {errors}')
print('Wrote', OUT_CSV)
