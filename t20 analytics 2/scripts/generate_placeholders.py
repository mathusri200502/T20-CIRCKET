#!/usr/bin/env python3
"""
Generate simple solid-color PNG placeholders for missing images listed in
`data/player_image_map.csv`. Uses only Python stdlib (zlib, struct, binascii).
Updates the CSV to point to the new .png filenames and writes a backup.
"""
import csv
import os
import sys
import zlib
import struct
import binascii

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, 'data', 'player_image_map.csv')
BACKUP_PATH = CSV_PATH + '.bak'
IMAGES_DIR = os.path.join(ROOT, 'static', 'images')

# PNG writer (RGB)

def write_solid_png(path, width, height, color=(180, 180, 180)):
    """Write a simple RGB PNG with given solid color to path."""
    # Raw image data: each scanline starts with filter byte 0
    row = b"\x00" + bytes(color) * width
    raw = row * height
    compressor = zlib.compressobj()
    compressed = compressor.compress(raw) + compressor.flush()

    def png_chunk(chunk_type, data):
        chunk = struct.pack('>I', len(data)) + chunk_type + data
        crc = struct.pack('>I', binascii.crc32(chunk_type + data) & 0xffffffff)
        return chunk + crc

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        # IHDR
        ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        f.write(png_chunk(b'IHDR', ihdr))
        # IDAT
        f.write(png_chunk(b'IDAT', compressed))
        # IEND
        f.write(png_chunk(b'IEND', b''))


if __name__ == '__main__':
    if not os.path.isdir(IMAGES_DIR):
        print('Images directory not found:', IMAGES_DIR)
        sys.exit(1)

    # Read CSV
    rows = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # If file has bad header, fallback
        if 'full_name' not in reader.fieldnames or 'filename' not in reader.fieldnames:
            # attempt to parse manually
            f.seek(0)
            lines = [l.rstrip('\n') for l in f]
            for line in lines:
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2 and parts[0] != 'full_name':
                    rows.append({'full_name': parts[0], 'filename': parts[1]})
        else:
            for r in reader:
                rows.append({'full_name': r.get('full_name','').strip(), 'filename': r.get('filename','').strip()})

    existing_files = set(os.listdir(IMAGES_DIR))
    changed = False
    generated = []

    for r in rows:
        orig_fn = r['filename']
        if not orig_fn:
            continue
        # normalize
        if orig_fn in existing_files:
            continue
        base, ext = os.path.splitext(orig_fn)
        new_fn = base + '.png'
        new_path = os.path.join(IMAGES_DIR, new_fn)
        if new_fn in existing_files:
            # update mapping to png
            r['filename'] = new_fn
            changed = True
            continue
        # create placeholder
        print('Generating placeholder for', orig_fn, '->', new_fn)
        try:
            write_solid_png(new_path, 512, 512, color=(200,200,200))
            existing_files.add(new_fn)
            r['filename'] = new_fn
            generated.append(new_fn)
            changed = True
        except Exception as e:
            print('Failed to generate', new_fn, ':', e)

    # Backup and write CSV if changes
    if changed:
        print('Backing up', CSV_PATH, '->', BACKUP_PATH)
        with open(BACKUP_PATH, 'w', encoding='utf-8', newline='') as bf:
            writer = csv.writer(bf)
            writer.writerow(['full_name','filename'])
            for r in rows:
                writer.writerow([r['full_name'], r['filename']])
        # overwrite original
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as of:
            writer = csv.writer(of)
            writer.writerow(['full_name','filename'])
            for r in rows:
                writer.writerow([r['full_name'], r['filename']])
        print('Wrote updated CSV with', len(generated), 'placeholders generated.')
    else:
        print('No changes needed; all mapped files present.')

    print('Done.')
