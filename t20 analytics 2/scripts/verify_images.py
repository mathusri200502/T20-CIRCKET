import os, csv
base = r'c:\Users\diwaa\OneDrive\Desktop\t20 analytics'
imgdir = os.path.join(base, 'static', 'images')
csvp = os.path.join(base, 'data', 'player_image_map.csv')

if not os.path.isdir(imgdir):
    print('ERROR: images dir not found:', imgdir)
    raise SystemExit(1)
if not os.path.isfile(csvp):
    print('ERROR: csv mapping not found:', csvp)
    raise SystemExit(1)

files = set(os.listdir(imgdir))
missing = []
present = []
with open(csvp, 'r', encoding='utf-8') as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        fn = r.get('filename','').strip()
        if not fn:
            continue
        if fn in files:
            present.append(fn)
        else:
            missing.append(fn)

print('IMAGES_DIR:', imgdir)
print('TOTAL_MAPPINGS:', len(present) + len(missing))
print('FOUND:', len(present))
print('MISSING:', len(missing))
if missing:
    print('\nMissing files:')
    for m in missing:
        print(m)
else:
    print('\nAll mapped images are present.')
