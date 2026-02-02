import json
import os
from pathlib import Path

data_dir = Path('data')
out_dir = Path('static/teams')
out_dir.mkdir(parents=True, exist_ok=True)

# Load players aggregated from app logic is simpler: reuse the three JSONs
player_info = json.load(open(data_dir / 't20_wc_player_info.json', encoding='utf-8'))
batting = json.load(open(data_dir / 't20_wc_batting_summary.json', encoding='utf-8'))
bowling = json.load(open(data_dir / 't20_wc_bowling_summary.json', encoding='utf-8'))

# Build quick aggregates like app.py
from collections import defaultdict

def aggregate_batting(batting_json):
    agg = defaultdict(lambda: {'runs':0, 'balls':0, '4s':0, '6s':0, 'innings':0, 'positions':[], 'name':None, 'team':None})
    for block in batting_json:
        for r in block.get('battingSummary', []):
            name = r.get('batsmanName','').strip()
            if not name: continue
            try:
                runs = int(r.get('runs','0'))
            except:
                runs = 0
            try:
                balls = int(r.get('balls','0'))
            except:
                balls = 0
            _4s = int(r.get('4s','0')) if str(r.get('4s','0')).isdigit() else 0
            _6s = int(r.get('6s','0')) if str(r.get('6s','0')).isdigit() else 0
            pos = r.get('battingPos', None)
            teamInnings = r.get('teamInnings','')
            agg[name]['name'] = name
            agg[name]['team'] = teamInnings or agg[name].get('team')
            agg[name]['runs'] += runs
            agg[name]['balls'] += balls
            agg[name]['4s'] += _4s
            agg[name]['6s'] += _6s
            if balls > 0 or runs>0:
                agg[name]['innings'] += 1
            if pos is not None:
                try:
                    agg[name]['positions'].append(int(pos))
                except:
                    pass
    for p,d in agg.items():
        d['strike_rate'] = round((d['runs']/d['balls']*100) if d['balls']>0 else 0,2)
        d['bat_avg'] = round((d['runs']/d['innings']) if d['innings']>0 else 0,2)
    return agg


def overs_to_balls(overs_str):
    try:
        if '.' in overs_str:
            o,s = overs_str.split('.')
            return int(o)*6 + int(s)
        return int(float(overs_str))*6
    except:
        return 0


def aggregate_bowling(bowling_json):
    agg = defaultdict(lambda: {'runs_conceded':0, 'wickets':0, 'balls':0, 'maiden':0, 'overs':0.0, 'dot_balls':0, 'name':None, 'team':None, 'innings':0})
    for block in bowling_json:
        for r in block.get('bowlingSummary', []):
            name = r.get('bowlerName','').strip()
            if not name: continue
            runs = int(r.get('runs','0')) if str(r.get('runs','0')).isdigit() else 0
            wickets = int(r.get('wickets','0')) if str(r.get('wickets','0')).isdigit() else 0
            overs_str = r.get('overs','0')
            balls = overs_to_balls(overs_str)
            maiden = int(r.get('maiden','0')) if str(r.get('maiden','0')).isdigit() else 0
            zeros = int(r.get('0s','0')) if str(r.get('0s','0')).isdigit() else 0
            team = r.get('bowlingTeam','')
            agg[name]['name'] = name
            agg[name]['team'] = team or agg[name].get('team')
            agg[name]['runs_conceded'] += runs
            agg[name]['wickets'] += wickets
            agg[name]['balls'] += balls
            agg[name]['maiden'] += maiden
            agg[name]['dot_balls'] += zeros
            if balls > 0:
                agg[name]['innings'] = agg[name].get('innings', 0) + 1
    for p,d in agg.items():
        d['overs'] = round(d['balls']/6,2) if d['balls']>0 else 0
        d['economy'] = round((d['runs_conceded']/d['overs']) if d['overs']>0 else 0,2)
        d['bowling_sr'] = round((d['balls']/d['wickets']) if d['wickets']>0 else 999.0,2)
        d['bowling_avg'] = round((d['runs_conceded']/d['wickets']) if d['wickets']>0 else 999.0,2)
        d['dot_pct'] = round((d['dot_balls']/d['balls']*100) if d['balls']>0 else 0,2)
    return agg

bat_agg = aggregate_batting(batting)
bowl_agg = aggregate_bowling(bowling)

# merge player info
players = {}
for p in player_info:
    name = p.get('name','').strip()
    players[name] = {
        'name': name,
        'team': p.get('team',''),
        'battingStyle': p.get('battingStyle',''),
        'bowlingStyle': p.get('bowlingStyle',''),
        'playingRole': p.get('playingRole',''),
        'description': p.get('description',''),
        'runs': 0, 'balls':0, '4s':0, '6s':0, 'innings':0,
        'strike_rate':0, 'bat_avg':0, 'boundary_pct':0, 'avg_ball_faced':0, 'batting_position': None,
        'runs_conceded':0, 'wickets':0, 'economy':None, 'bowling_sr':None, 'bowling_avg':None, 'dot_pct':None
    }

for name, d in bat_agg.items():
    if name not in players:
        players[name] = {'name':name, 'team':d.get('team','')}
    players[name].update({
        'runs': d.get('runs',0),
        'balls': d.get('balls',0),
        '4s': d.get('4s',0),
        '6s': d.get('6s',0),
        'innings': d.get('innings',0),
        'strike_rate': d.get('strike_rate',0),
        'bat_avg': d.get('bat_avg',0),
    })

for name, d in bowl_agg.items():
    if name not in players:
        players[name] = {'name':name, 'team':d.get('team','')}
    players[name].update({
        'runs_conceded': d.get('runs_conceded',0),
        'wickets': d.get('wickets',0),
        'economy': d.get('economy', None),
        'bowling_sr': d.get('bowling_sr', None),
        'bowling_avg': d.get('bowling_avg', None),
        'dot_pct': d.get('dot_pct', None),
        'balls_bowled': d.get('balls',0),
        'innings_bowled': d.get('innings',0),
        'overs': d.get('overs',0),
        'maiden': d.get('maiden',0)
    })

# group by team
teams = defaultdict(list)
for p in players.values():
    t = p.get('team') or 'Unknown'
    teams[t].append(p)

# create static HTML pages
for team, plist in teams.items():
    safe_name = team.lower().replace(' ', '_')
    html_path = out_dir / f"{safe_name}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(f"<html><head><meta charset=\"utf-8\"><title>{team}</title><link rel=\"stylesheet\" href=\"/static/css/styles.css\"></head><body>\n")
        f.write(f"<div class=\"team-logo\"><img src=\"/static/images/team-logos/{safe_name}.svg\" onerror=\"this.src='/static/images/team-logos/default.svg'\"/></div>\n")
        f.write("<div class=\"player-grid\">\n")
        for p in plist:
            img_name = p['name'].lower().replace(' ', '_').replace('.', '').replace("'", "")
            f.write(f"<div class=\"player-card\">\n")
            f.write(f"<img src=\"/static/images/{img_name}.jpg\" alt=\"{p['name']}\" onerror=\"this.src='/static/images/placeholder.svg'\"/>\n")
            f.write(f"<div class=\"info\">\n<h3>{p['name']}</h3>\n<div class=\"role\">{p.get('playingRole','')} | {p.get('battingStyle','')}</div>\n")
            f.write("<div class=\"stats\">\n")
            f.write(f"<div class=\"stat\"><div class=\"value\">{p.get('runs',0)}</div><div class=\"label\">Runs</div></div>\n")
            f.write(f"<div class=\"stat\"><div class=\"value\">{p.get('wickets',0)}</div><div class=\"label\">Wkts</div></div>\n")
            f.write(f"<div class=\"stat\"><div class=\"value\">{p.get('bat_avg',0)}</div><div class=\"label\">Avg</div></div>\n")
            f.write(f"<div class=\"stat\"><div class=\"value\">{p.get('economy',0)}</div><div class=\"label\">Econ</div></div>\n")
            f.write("</div>\n</div>\n</div>\n")
        f.write("</div>\n</body></html>")
    print(f"Wrote {html_path}")

print('Done')