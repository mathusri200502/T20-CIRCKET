#!/usr/bin/env python3
"""
Generate SVG placeholders for all players mentioned in data files that don't have images.
Reads player info from JSON files and creates informative SVG placeholders.
"""
import csv
import os
import json
import re
import shutil
from datetime import datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, 'data', 'player_image_map.csv')
IMAGES_DIR = os.path.join(ROOT, 'static', 'images')
PLAYER_JSON = os.path.join(ROOT, 'data', 't20_wc_player_info.json')
FULL_PLAYERS_JSON = os.path.join(ROOT, 'data', 'full_players_json.json')

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
    s = re.sub(r'[^a-z0-9-]', '_', s.lower().strip())
    s = re.sub(r'_+', '_', s)  # collapse multiple underscores
    return s.strip('_')

def create_player_svg(path, name, info):
    """Create an SVG placeholder showing player name and using team colors."""
    team = info.get('team', '')
    role = info.get('role', '')
    team_color = TEAM_COLORS.get(team, TEAM_COLORS['DEFAULT'])
    
    # Format name lines
    words = name.split()
    if len(words) > 2:
        name_line1 = ' '.join(words[:2])
        name_line2 = ' '.join(words[2:])
    else:
        name_line1 = name
        name_line2 = ''
    
    # Add team/role info if available
    info_line = []
    if team:
        info_line.append(team)
    if role:
        info_line.append(role)
    info_text = ' | '.join(info_line)

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
  <text x="256" y="380" font-size="40">{name_line1}</text>
  <text x="256" y="430" font-size="40">{name_line2}</text>
  <text x="256" y="470" font-size="24">{info_text}</text>
 </g>
</svg>'''
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(svg)

def load_player_info():
    """Load player info from both JSONs to get full player details."""
    players = {}
    
    try:
        # Load t20_wc_player_info.json
        with open(PLAYER_JSON, encoding='utf-8') as f:
            data = json.load(f)
            for p in data:
                name = p['name']
                players[name] = {
                    'team': p.get('team', ''),
                    'role': p.get('playingRole', ''),
                    'batting': p.get('battingStyle', ''),
                    'bowling': p.get('bowlingStyle', '')
                }
    except Exception as e:
        print(f"Warning: Couldn't load T20 WC player info: {e}")
    
    try:
        # Load full_players_json.json
        with open(FULL_PLAYERS_JSON, encoding='utf-8') as f:
            data = json.load(f)
            for p in data:
                name = p['full_name']
                if name not in players:
                    players[name] = {
                        'team': p.get('country', ''),
                        'role': p.get('role', ''),
                        'batting': p.get('batting_style', ''),
                        'bowling': p.get('bowling_style', '')
                    }
    except Exception as e:
        print(f"Warning: Couldn't load full players JSON: {e}")
    
    return players

def get_current_mappings():
    """Read current CSV mappings, clean any duplicate headers."""
    rows = []
    seen_headers = False
    
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
    
    for row in csv.DictReader(lines):
        if row.get('full_name') and row.get('filename'):
            rows.append({
                'full_name': row['full_name'].strip(),
                'filename': row['filename'].strip()
            })
    return rows

def backup_csv():
    """Create timestamped backup of CSV."""
    backup_path = f"{CSV_PATH}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
    shutil.copy2(CSV_PATH, backup_path)
    return backup_path

def main():
    if not os.path.isdir(IMAGES_DIR):
        print('Images directory not found:', IMAGES_DIR)
        return

    print('Loading player info...')
    player_info = load_player_info()
    print(f'Found {len(player_info)} players in data files')
    
    print('Reading current CSV mappings...')
    current_rows = get_current_mappings()
    print(f'Found {len(current_rows)} mappings in CSV')
    
    # Track all existing image files
    print('Listing existing images...')
    existing_files = set(f for f in os.listdir(IMAGES_DIR) if os.path.isfile(os.path.join(IMAGES_DIR, f)))
    print(f'Found {len(existing_files)} files in images directory')
    
    # Build mapping of who already has images
    mapped_players = {}
    for r in current_rows:
        name = r['full_name']
        filename = r['filename']
        mapped_players[name] = filename
    
    # Generate SVGs for unmapped players and players with missing files
    generated = []
    updated_rows = []
    
    print('\nChecking players and generating placeholders...')
    for name, info in player_info.items():
        current_file = mapped_players.get(name, '')
        
        # If player has a mapping and file exists, keep it
        if current_file and os.path.exists(os.path.join(IMAGES_DIR, current_file)):
            updated_rows.append({'full_name': name, 'filename': current_file})
            continue
            
        # Generate SVG for this player
        svg_name = f"{clean_filename(name)}.svg"
        svg_path = os.path.join(IMAGES_DIR, svg_name)
        
        print(f'Generating SVG placeholder for {name} -> {svg_name}')
        try:
            create_player_svg(svg_path, name, info)
            updated_rows.append({'full_name': name, 'filename': svg_name})
            generated.append(name)
        except Exception as e:
            print(f'Failed to generate {svg_name}: {e}')
            # Keep old mapping if it existed
            if name in mapped_players:
                updated_rows.append({'full_name': name, 'filename': mapped_players[name]})
    
    # Write updated CSV with all mappings
    if generated:
        backup_path = backup_csv()
        print(f'\nBacked up original CSV to: {backup_path}')
        
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['full_name', 'filename'])
            writer.writeheader()
            writer.writerows(updated_rows)
        
        print(f'\nUpdated CSV mapping with {len(generated)} new SVG placeholders')
        print('Generated placeholders for:', ', '.join(generated))
    else:
        print('\nNo new placeholders needed')
    
    print(f'\nFinal Summary:')
    print(f'Total players in data: {len(player_info)}')
    print(f'Players with images: {len(updated_rows)}')
    print(f'New SVGs generated: {len(generated)}')
    
if __name__ == '__main__':
    main()