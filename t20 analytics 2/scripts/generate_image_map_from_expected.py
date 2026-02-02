import os
base = r'c:\Users\diwaa\OneDrive\Desktop\t20 analytics'
expected = os.path.join(base, 'static', 'images', 'expected_image_filenames.txt')
out = os.path.join(base, 'data', 'player_image_map.csv')
imgdir = os.path.join(base, 'static', 'images')

if not os.path.isfile(expected):
    print('expected file not found:', expected)
    raise SystemExit(1)

files = set(os.listdir(imgdir))
entries = []
with open(expected, 'r', encoding='utf-8') as f:
    for line in f:
        line=line.strip()
        if '->' in line:
            name, fname = [p.strip() for p in line.split('->',1)]
            # clean filename
            fname = fname
            if fname in files:
                entries.append((name, fname))

with open(out, 'w', encoding='utf-8') as f:
    f.write('full_name,filename\n')
    for name,fname in entries:
        f.write(f'{name},{fname}\n')

print('Wrote', len(entries), 'mappings to', out)
