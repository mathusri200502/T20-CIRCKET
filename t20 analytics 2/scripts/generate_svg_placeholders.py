#!/usr/bin/env python3
"""
Generate SVG placeholders for players that show their name and use team colors.
Updates player_image_map.csv to point to the new SVG files.
"""
import csv
import os
import json
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, 'data', 'player_image_map.csv')
IMAGES_DIR = os.path.join(ROOT, 'static', 'images')
PLAYER_JSON = os.path.join(ROOT, 'data', 't20_wc_player_info.json')

# Team colors (from the CSS gradient)
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
    'Zimbabwe': '#5a00b8'
}

def clean_filename(s):
    """Convert string to safe filename."""
    return re.sub(r'[^a-z0-9-]', '_', s.lower().strip())

def create_player_svg(path, name, team_color='#5a00b8'):
    """Create an SVG placeholder with player name and team color."""
    # Split long names into two lines if needed
    words = name.split()
    if len(words) > 2:
        name_line1 = ' '.join(words[:2])
        name_line2 = ' '.join(words[2:])
    else:
        name_line1 = name
        name_line2 = ''

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

if __name__ == '__main__':
    # Load player info to get teams
    player_teams = {}
    try:
        with open(PLAYER_JSON, encoding='utf-8') as f:
            player_data = json.load(f)
            for p in player_data:
                player_teams[p['name']] = p.get('team', '')
    except Exception as e:
        print(f"Warning: Couldn't load player teams from {PLAYER_JSON}: {e}")

    # Read CSV
    rows = []
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    # Track changes
    changed = False
    generated = []
    
    # Create SVGs for missing images
    for r in rows:
        name = r['full_name'].strip()
        orig_fn = r['filename'].strip()
        if not orig_fn or not name:
            continue

        # Get team color
        team = player_teams.get(name, '')
        team_color = TEAM_COLORS.get(team, '#5a00b8')  # default to purple if team unknown

        # Check if original file exists
        orig_path = os.path.join(IMAGES_DIR, orig_fn)
        if os.path.exists(orig_path):
            continue

        # Generate SVG name and create it
        svg_name = f"{clean_filename(name)}.svg"
        svg_path = os.path.join(IMAGES_DIR, svg_name)
        
        print(f'Generating SVG placeholder for {name} -> {svg_name}')
        try:
            create_player_svg(svg_path, name, team_color)
            r['filename'] = svg_name  # Update mapping to point to new SVG
            generated.append(svg_name)
            changed = True
        except Exception as e:
            print(f'Failed to generate {svg_name}: {e}')

    # Write updated CSV if changes made
    if changed:
        print(f'Writing updated CSV with {len(generated)} new SVG placeholders')
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['full_name', 'filename'])
            writer.writeheader()
            writer.writerows(rows)
        print('Done. Generated SVGs:', ', '.join(generated))
    else:
        print('No changes needed; all mapped files exist')