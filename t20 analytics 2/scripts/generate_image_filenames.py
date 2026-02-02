import json
import re
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 't20_wc_player_info.json')
OUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'expected_image_filenames.txt')

def make_filename(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s + '.jpg'

def main():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        players = json.load(f)
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as out:
        for p in players:
            name = p.get('name','').strip()
            if not name:
                continue
            fn = make_filename(name)
            line = f"{name} -> {fn}\n"
            out.write(line)
    # also print first 30 lines to stdout
    with open(OUT_FILE, 'r', encoding='utf-8') as out:
        for i, l in enumerate(out):
            if i < 200:
                print(l.strip())
            else:
                break

if __name__ == '__main__':
    main()
