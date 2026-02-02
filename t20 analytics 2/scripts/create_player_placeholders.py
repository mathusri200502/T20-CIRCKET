#!/usr/bin/env python3
"""
Generate SVG placeholders for players that show their name and use team colors.
Also fixes the CSV mapping file to remove duplicate headers.
"""
import csv
import os
import json
import re
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, 'data', 'player_image_map.csv')
IMAGES_DIR = os.path.join(ROOT, 'static', 'images')
PLAYER_JSON = os.path.join(ROOT, 'data', 't20_wc_player_info.json')

# Team colors (from the site's gradient)
TEAM_COLORS = {
    'Afghanistan': '#5a00b8',
    'Australia': '#e4007a',
    'Bangladesh': '#2b0066',
    'England': '#5a00b8',
    'India': '#2b0066',
    'Ireland': '#5a00b8',
    'Namibia': '#e4007a',
    'Netherlands': '#5a00b8',
    'New Zealand': '#2b0066',
    'Pakistan': '#5a00b8',
    'Scotland': '#e4007a',
    'South Africa': '#2b0066',
    'Sri Lanka': '#5a00b8',
    'U.A.E.': '#e4007a',
    'West Indies': '#2b0066',
    'Zimbabwe': '#5a00b8',
    'DEFAULT': '#5a00b8'
}

def clean_filename(s):
    """Convert string to safe filename."""
    return re.sub(r'[^a-z0-9-]', '_', s.lower().strip())

def create_player_svg(path, name, role='', team_color='#5a00b8'):
    """Create an SVG placeholder showing player name and using team colors."""
    words = name.split()
    if len(words) > 2:
        name_line1 = ' '.join(words[:2])
        name_line2 = ' '.join(words[2:])
    else:
        name_line1 = name
        name_line2 = role if role else ''

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" version="1.1" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
 <defs>
  <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
   <stop offset="0%" style="stop-color:{team_color};stop-opacity:0.9"/>
   <stop offset="100%" style="stop-color:{team_color};stop-opacity:0.7"/>
  </linearGradient>
 </defs>
 <rect width="512" height="512" fill="url(#grad)"/>
 <circle cx="256" cy="180" r="100" fill="#ffffff" fill-opacity="0.2"/>
 <path d="m256 130c-30 0-50 25-50 50 0 30 20 50 50 50s50-20 50-50c0-25-20-50-50-50zm0 120c-60 0-100 40-100 60v20h200v-20c0-20-40-60-100-60z" fill="#ffffff" fill-opacity="0.2"/>
 <g fill="#ffffff" font-family="Arial" text-anchor="middle">
  <text x="256" y="400" font-size="40">{name_line1}</text>
  <text x="256" y="450" font-size="40">{name_line2}</text>
 </g>
</svg>'''
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)

def load_player_info():
    """Load player info to get teams and roles."""
    players = {}
    try:
        with open(PLAYER_JSON, encoding='utf-8') as f:
            data = json.load(f)
            for p in data:
                name = p['name']
                players[name] = {
                    'team': p.get('team', ''),
                    'role': p.get('playingRole', '')
                }
    except Exception as e:
        print(f"Warning: Couldn't load player info: {e}")
    return players

def fix_csv_and_get_rows():
    """Clean the CSV file (remove duplicate headers) and return the valid rows."""
    rows = []
    seen_headers = False
    
    # Read and clean lines
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        lines = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('full_name,filename'):
                if not seen_headers:
                    lines.append(line)
                    seen_headers = True
            else:
                lines.append(line)
    
    # Parse as CSV
    for row in csv.DictReader(lines):
        if row.get('full_name') and row.get('filename'):
            rows.append({
                'full_name': row['full_name'].strip(),
                'filename': row['filename'].strip()
            })
    
    # Backup and write cleaned CSV
    backup_path = f"{CSV_PATH}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(CSV_PATH, backup_path)
    
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['full_name', 'filename'])
        writer.writeheader()
        writer.writerows(rows)
    
    return rows

def main():
    if not os.path.isdir(IMAGES_DIR):
        print('Images directory not found:', IMAGES_DIR)
        return

    print('Loading player info...')
    player_info = load_player_info()
    
    print('Reading and cleaning CSV...')
    rows = fix_csv_and_get_rows()
    
    # Track changes
    changed = False
    generated = []
    missing = []
    
    print('Checking images and generating placeholders...')
    for r in rows:
        name = r['full_name']
        current_file = r['filename']
        
        # Get player info
        info = player_info.get(name, {})
        team = info.get('team', '')
        role = info.get('role', '')
        team_color = TEAM_COLORS.get(team, TEAM_COLORS['DEFAULT'])
        
        # Check if current file exists
        current_path = os.path.join(IMAGES_DIR, current_file)
        if os.path.exists(current_path):
            continue
            
        missing.append(current_file)
        
        # Generate SVG name and create it
        svg_name = f"{clean_filename(name)}.svg"
        svg_path = os.path.join(IMAGES_DIR, svg_name)
        
        print(f'Generating SVG placeholder for {name} -> {svg_name}')
        try:
            create_player_svg(svg_path, name, role, team_color)
            r['filename'] = svg_name  # Update mapping to point to new SVG
            generated.append(svg_name)
            changed = True
        except Exception as e:
            print(f'Failed to generate {svg_name}: {e}')
    
    # Write updated CSV if changes made
    if changed:
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['full_name', 'filename'])
            writer.writeheader()
            writer.writerows(rows)
        print(f'\nUpdated CSV mapping with {len(generated)} new SVG placeholders')
        print('Generated:', ', '.join(generated))
    
    print(f'\nSummary:')
    print(f'Total mappings: {len(rows)}')
    print(f'Missing files: {len(missing)}')
    print(f'Generated SVGs: {len(generated)}')
    
if __name__ == '__main__':
    main()