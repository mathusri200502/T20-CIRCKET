import csv
import os

ROOT = os.path.dirname(__file__)
IN_CSV = os.path.join(ROOT, 'image_license_metadata.csv')
OUT_MD = os.path.join(ROOT, '..', 'static', 'images', 'ATTRIBUTIONS.md')
OUT_CSV = os.path.join(ROOT, 'usable_images.csv')

os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
rows = []
with open(IN_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r['status'] == 'ok':
            rows.append(r)

# write MD
with open(OUT_MD, 'w', encoding='utf-8') as m:
    m.write('# Image Attributions\n\n')
    m.write('The following images were downloaded from Wikimedia/Wikipedia. Please review individual licenses before reuse (see `scripts/image_license_metadata.csv`).\n\n')
    for r in rows:
        m.write(f"- **{r['name']}** — `{r['local_filename']}`\n")
        m.write(f"  - Source: {r.get('file_url','')}\n")
        m.write(f"  - License: {r.get('license','')} {r.get('license_url','')}\n")
        artist = r.get('artist','') or r.get('credit','')
        if artist:
            m.write(f"  - Artist/Credit: {artist}\n")
        m.write('\n')

# write usable CSV
with open(OUT_CSV, 'w', encoding='utf-8', newline='') as cf:
    w = csv.writer(cf)
    w.writerow(['name','local_filename','file_url','license','license_url','artist'])
    for r in rows:
        w.writerow([r['name'], r['local_filename'], r.get('file_url',''), r.get('license',''), r.get('license_url',''), r.get('artist','')])

print('Wrote', OUT_MD, 'and', OUT_CSV, 'with', len(rows), 'entries')
