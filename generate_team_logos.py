import json
from pathlib import Path
import os

# Load team data to get list of teams
with open('data/t20_wc_player_info.json', 'r', encoding='utf-8') as f:
    players = json.load(f)

# Get unique teams
teams = sorted(set(p['team'] for p in players if p.get('team')))

# Team colors mapping
team_colors = {
    'India': {'primary': '#0033A0', 'secondary': '#FF9933'},
    'Australia': {'primary': '#00843D', 'secondary': '#FFCD00'},
    'England': {'primary': '#1A1A4B', 'secondary': '#C8102E'},
    'Pakistan': {'primary': '#00B300', 'secondary': '#FFFFFF'},
    'New Zealand': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'South Africa': {'primary': '#007749', 'secondary': '#FDB913'},
    'West Indies': {'primary': '#7B0041', 'secondary': '#FFD700'},
    'Sri Lanka': {'primary': '#003399', 'secondary': '#FFD700'},
    'Bangladesh': {'primary': '#006A4E', 'secondary': '#F42A41'},
    'Afghanistan': {'primary': '#0066CC', 'secondary': '#FF0000'},
    'Netherlands': {'primary': '#FF6F00', 'secondary': '#FFFFFF'},
    'Ireland': {'primary': '#169B62', 'secondary': '#FF883E'},
    'Zimbabwe': {'primary': '#FF0000', 'secondary': '#FFFF00'},
    'Namibia': {'primary': '#003580', 'secondary': '#FFFFFF'},
}

# Default colors for teams not in the mapping
default_colors = {'primary': '#4B5563', 'secondary': '#9CA3AF'}

def create_team_logo(team_name, output_path):
    """Create an SVG logo for the team with team colors"""
    colors = team_colors.get(team_name, default_colors)
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="400" height="140" viewBox="0 0 400 140">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{colors['primary']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{colors['secondary']};stop-opacity:1" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="4" stdDeviation="4" flood-opacity="0.3"/>
    </filter>
    <linearGradient id="textGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:white;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f0f0f0;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#grad)" rx="12" filter="url(#shadow)"/>
  <g transform="translate(200, 70)">
    <!-- White glow background -->
    <rect x="-180" y="-30" width="360" height="60" rx="30" 
          fill="white" opacity="0.1"/>
    <!-- Team name -->
    <text x="0" y="8" font-family="Arial, sans-serif" font-size="36" 
          font-weight="bold" fill="url(#textGrad)" text-anchor="middle"
          style="filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.3))">
      {team_name.upper()}
    </text>
  </g>
</svg>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)

def main():
    # Create output directory if it doesn't exist
    output_dir = Path('static/images/team-logos')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logo for each team
    for team in teams:
        output_path = output_dir / f"{team.lower().replace(' ', '_')}.svg"
        create_team_logo(team, output_path)
        print(f"Created logo for {team}")

if __name__ == '__main__':
    main()