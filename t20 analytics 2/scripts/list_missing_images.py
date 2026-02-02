import json
import re
from pathlib import Path

DATA = Path('data/t20_wc_player_info.json')
IMAGEDIR = Path('static/images')
OUTCSV = Path('scripts/missing_images.csv')

with open(DATA, 'r', encoding='utf-8') as f:
    players = json.load(f)

missing = []

for p in players:
    name = p.get('name','').strip()
    if not name:
        continue
    img_name = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    found = False
    for ext in ('.jpg', '.jpeg', '.png', '.svg'):
        if (IMAGEDIR / (img_name + ext)).exists():
            found = True
            break
    if not found:
        missing.append({'name': name, 'expected': img_name + '.jpg'})

# write CSV
OUTCSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUTCSV, 'w', encoding='utf-8') as f:
    f.write('name,expected_filename\n')
    for m in missing:
        f.write('"{}",{}\n'.format(m['name'].replace('"','""'), m['expected']))

print(f'Total players checked: {len(players)}')
print(f'Missing images: {len(missing)}')
for m in missing:
    print(m['name'], '->', m['expected'])
print('\nWrote', OUTCSV)
