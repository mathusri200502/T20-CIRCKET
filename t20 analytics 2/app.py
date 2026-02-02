from flask import Flask, jsonify, render_template, send_from_directory, request, redirect, url_for
import re
import json
import os
import requests
from requests.exceptions import RequestException
from collections import defaultdict

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
DATA_DIR = 'data'

def load_json(fname):
    with open(os.path.join(DATA_DIR, fname), 'r', encoding='utf-8') as f:
        return json.load(f)

def search_data(query):
    results = {
        'players': [],
        'teams': set(),
        'categories': []
    }
    
    import difflib
    query_norm = re.sub(r'[^a-z0-9]', '', query.lower())
    # Prepare lists for fuzzy matching
    player_names = [p.get('name', '') for p in player_info_json]
    player_names_norm = [re.sub(r'[^a-z0-9]', '', n.lower()) for n in player_names]
    team_names = list(set([p.get('team', '') for p in player_info_json]))
    team_names_norm = [re.sub(r'[^a-z0-9]', '', t.lower()) for t in team_names]
    # Fuzzy match players
    close_players = difflib.get_close_matches(query_norm, player_names_norm, n=5, cutoff=0.6)
    for idx, norm_name in enumerate(player_names_norm):
        if norm_name in close_players:
            results['players'].append(player_info_json[idx])
            results['teams'].add(player_info_json[idx].get('team', ''))
    # Fuzzy match teams
    close_teams = difflib.get_close_matches(query_norm, team_names_norm, n=3, cutoff=0.6)
    for idx, norm_team in enumerate(team_names_norm):
        if norm_team in close_teams:
            results['teams'].add(team_names[idx])
    # Fuzzy match categories
    categories = ['power', 'anchor', 'finisher', 'allrounder', 'fast']
    close_categories = difflib.get_close_matches(query_norm, categories, n=3, cutoff=0.6)
    for cat in close_categories:
        results['categories'].append(cat)
    return results

def aggregate_batting(batting_json):
    # batting_json structure: list of { "battingSummary": [ ... ] }
    agg = defaultdict(lambda: {'runs':0, 'balls':0, '4s':0, '6s':0, 'innings':0, 'positions':[], 'name':None, 'team':None})
    for block in batting_json:
        for r in block.get('battingSummary', []):
            name = r.get('batsmanName','').strip()
            if not name: 
                continue
            # convert values; handle '-' for SR etc
            runs = int(r.get('runs','0')) if r.get('runs','0').isdigit() else 0
            balls = int(r.get('balls','0')) if str(r.get('balls','0')).isdigit() else 0
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
    # compute derived
    for p,d in agg.items():
        d['strike_rate'] = round((d['runs']/d['balls']*100) if d['balls']>0 else 0,2)
        d['bat_avg'] = round((d['runs']/d['innings']) if d['innings']>0 else 0,2)
        # boundary %
        total_boundaries = d['4s'] + d['6s']
        d['boundary_pct'] = round((total_boundaries* (4) / d['runs'] * 100) if d['runs']>0 else 0,2) if d['runs']>0 else 0.0
        d['avg_ball_faced'] = round((d['balls']/d['innings']) if d['innings']>0 else 0,2)
        d['batting_position'] = min(d['positions']) if d['positions'] else None
    return agg

def aggregate_bowling(bowling_json):
    agg = defaultdict(lambda: {'runs_conceded':0, 'wickets':0, 'balls':0, 'maiden':0, 'overs':0.0, 'dot_balls':0, 'name':None, 'team':None})
    def overs_to_balls(overs_str):
        try:
            if '.' in overs_str:
                o,s = overs_str.split('.')
                return int(o)*6 + int(s)
            return int(float(overs_str))*6
        except:
            return 0
    for block in bowling_json:
        for r in block.get('bowlingSummary', []):
            name = r.get('bowlerName','').strip()
            if not name:
                continue
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

def merge_player_info(player_info_json, batting_agg, bowling_agg):
    players = {}
    for p in player_info_json:
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
    for name, d in batting_agg.items():
        if name not in players:
            players[name] = {'name':name, 'team':d.get('team',''), 'battingStyle':'', 'bowlingStyle':'', 'playingRole':'', 'description':'',
                             'runs':0,'balls':0,'4s':0,'6s':0,'innings':0,'strike_rate':0,'bat_avg':0,'boundary_pct':0,'avg_ball_faced':0,'batting_position':None,
                             'runs_conceded':0,'wickets':0,'economy':None,'bowling_sr':None,'bowling_avg':None,'dot_pct':None}
        players[name].update({
            'runs': d.get('runs',0),
            'balls': d.get('balls',0),
            '4s': d.get('4s',0),
            '6s': d.get('6s',0),
            'innings': d.get('innings',0),
            'strike_rate': d.get('strike_rate',0),
            'bat_avg': d.get('bat_avg',0),
            'boundary_pct': d.get('boundary_pct',0),
            'avg_ball_faced': d.get('avg_ball_faced',0),
            'batting_position': d.get('batting_position', None)
        })
    for name, d in bowling_agg.items():
        if name not in players:
            players[name] = {'name':name, 'team':d.get('team',''), 'battingStyle':'', 'bowlingStyle':'', 'playingRole':'', 'description':'',
                             'runs':0,'balls':0,'4s':0,'6s':0,'innings':0,'strike_rate':0,'bat_avg':0,'boundary_pct':0,'avg_ball_faced':0,'batting_position':None,
                             'runs_conceded':0,'wickets':0,'economy':None,'bowling_sr':None,'bowling_avg':None,'dot_pct':None}
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
    return players

def is_power_hitter(p):
    return (p.get('bat_avg',0) > 30 and p.get('strike_rate',0) > 140 and p.get('innings',0) > 3 and p.get('boundary_pct',0) > 50.0 and (p.get('batting_position') is not None and p.get('batting_position') <= 3))

def is_anchor(p):
    return (p.get('bat_avg',0) > 40 and p.get('strike_rate',0) > 125 and p.get('innings',0) > 3 and p.get('avg_ball_faced',0) > 20 and (p.get('batting_position') is not None and p.get('batting_position') > 2))

def is_finisher(p):
    return (p.get('bat_avg',0) > 25 and p.get('strike_rate',0) > 130 and p.get('innings',0) > 3 and p.get('avg_ball_faced',0) > 12 and (p.get('batting_position') is not None and p.get('batting_position') > 4) and p.get('innings',0) > 1)

def is_allrounder(p):
    econ = p.get('economy')
    return (p.get('bat_avg',0) > 15 and p.get('strike_rate',0) > 140 and p.get('innings',0) > 2 and (p.get('batting_position') is not None and p.get('batting_position') > 4) and p.get('innings',0) > 2 and (econ is not None and econ < 7) and (p.get('bowling_sr') is not None and p.get('bowling_sr') < 20.0))

def is_specialist_fast(p):
    econ = p.get('economy')
    bs = (p.get('bowlingStyle') or '').lower()
    return (
        (p.get('innings_bowled', 0) > 4)
        and (econ is not None and econ != '' and float(econ) < 7.0)
        and (p.get('bowling_sr') is not None and p.get('bowling_sr') < 16.0)
        and ('fast' in bs)
        and (p.get('bowling_avg') is not None and p.get('bowling_avg') < 20)
        and (p.get('dot_pct', 0) > 40.0)
    )

CATEGORY_FUNCS = {
    'power': is_power_hitter,
    'anchor': is_anchor,
    'finisher': is_finisher,
    'allrounder': is_allrounder,
    'fast': is_specialist_fast
}

# Load and aggregate data once
print("Loading data...")
batting_json = load_json('t20_wc_batting_summary.json')
bowling_json = load_json('t20_wc_bowling_summary.json')
player_info_json = load_json('t20_wc_player_info.json')

print("Aggregating data...")
bat_agg = aggregate_batting(batting_json)
bowl_agg = aggregate_bowling(bowling_json)
players = merge_player_info(player_info_json, bat_agg, bowl_agg)

# Load player image mapping from CSV (optional file) and resolve missing extensions
IMAGE_MAP_PATH = os.path.join(DATA_DIR, 'player_image_map.csv')
IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')
player_image_map = {}
if os.path.exists(IMAGE_MAP_PATH):
    try:
        with open(IMAGE_MAP_PATH, 'r', encoding='utf-8') as f:
            # Skip header
            next(f)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',', 1)
                if len(parts) != 2:
                    continue
                name, fname = parts[0].strip(), parts[1].strip()
                if not name:
                    continue
                # If the filename exists as given, keep it. Otherwise try common extensions.
                candidate = None
                given_path = os.path.join(IMAGE_DIR, fname)
                if os.path.exists(given_path):
                    candidate = fname
                else:
                    for ext in ('.jpg', '.jpeg', '.png', '.svg', '.webp'):
                        alt = fname + ext
                        if os.path.exists(os.path.join(IMAGE_DIR, alt)):
                            candidate = alt
                            break
                # If not found yet, also try stripping any trailing dots/spaces and check
                if not candidate:
                    short = fname.rstrip('. ')
                    if short and os.path.exists(os.path.join(IMAGE_DIR, short)):
                        candidate = short

                # Save candidate (may be None) so we can do normalized lookup later
                player_image_map[name] = candidate if candidate else fname
    except Exception as e:
        print(f"Error loading image map: {e}")

# Attach resolved image filenames to players where available
for pname, pobj in players.items():
    assigned = None
    # exact match
    if pname in player_image_map and player_image_map[pname]:
        assigned = player_image_map[pname]
    else:
        # try normalized match by stripping non-alphanum
        norm = re.sub(r"[^a-z0-9]", "", pname.lower())
        for k, v in player_image_map.items():
            if not v:
                continue
            if re.sub(r"[^a-z0-9]", "", k.lower()) == norm:
                assigned = v
                break
    if assigned:
        pobj['img_name'] = assigned
print("Data loaded and processed.")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/player/<player>')
def player(player):
    # Input validation
    if not player or len(player.strip()) == 0:
        return "Invalid player name", 400
        
    # Find player info with case-insensitive match
    player_obj = None
    for p in players.values():
        if p['name'].lower() == player.lower():
            player_obj = p
            break
            
    if not player_obj:
        return render_template('search.html', 
                             query=player,
                             players=[],
                             teams=[],
                             categories=[],
                             error=f"Player '{player}' not found")

    # Load full_players_json.json for biography/history
    try:
        with open(os.path.join(DATA_DIR, 'full_players_json.json'), 'r', encoding='utf-8') as f:
            full_players = json.load(f)
    except Exception as e:
        print(f"Error loading full_players_json.json: {e}")
        full_players = []

    # Find matching player in full_players_json.json (case-insensitive)
    player_bio = None
    for fp in full_players:
        if fp.get('full_name', '').lower() == player_obj['name'].lower():
            player_bio = fp
            break

    # Add biography/history fields to player_obj for template
    if player_bio:
        player_obj['biography'] = player_bio.get('biography', '')
        player_obj['date_of_birth'] = player_bio.get('date_of_birth', '')
        player_obj['batting_style'] = player_bio.get('batting_style', '')
        player_obj['bowling_style'] = player_bio.get('bowling_style', '')
        player_obj['role'] = player_bio.get('role', '')
        player_obj['country'] = player_bio.get('country', '')
                             
    # Get Wikipedia summary with proper error handling
    wiki_summary = None
    try:
        # Clean the player name for Wikipedia API
        wiki_name = player_obj['name'].replace(' ', '_')
        wiki_api = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_name}"
        
        # Add timeout and user-agent
        headers = {'User-Agent': 'T20Analytics/1.0'}
        resp = requests.get(wiki_api, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            wiki_data = resp.json()
            wiki_summary = wiki_data.get('extract')
        else:
            print(f"Wikipedia API error: {resp.status_code}")
    except RequestException as e:
        print(f"Wikipedia request failed: {str(e)}")
    except Exception as e:
        print(f"Error fetching Wikipedia data: {str(e)}")

    # Get match records from batting and bowling data
    match_records = []
    try:
        # Get batting records
        for match in batting_json:
            for innings in match.get('battingSummary', []):
                if innings.get('batsmanName', '').lower() == player_obj['name'].lower():
                    record = {
                        'type': 'batting',
                        'runs': innings.get('runs', '0'),
                        'balls': innings.get('balls', '0'),
                        '4s': innings.get('4s', '0'),
                        '6s': innings.get('6s', '0'),
                        'sr': innings.get('strikeRate', '0'),
                        'team': innings.get('teamInnings', '')
                    }
                    match_records.append(record)
                    
        # Get bowling records
        for match in bowling_json:
            for spell in match.get('bowlingSummary', []):
                if spell.get('bowlerName', '').lower() == player_obj['name'].lower():
                    record = {
                        'type': 'bowling',
                        'overs': spell.get('overs', '0'),
                        'wickets': spell.get('wickets', '0'),
                        'runs': spell.get('runs', '0'),
                        'economy': spell.get('economy', '0'),
                        'team': spell.get('bowlingTeam', '')
                    }
                    match_records.append(record)
    except Exception as e:
        print(f"Error processing match records: {str(e)}")
        
    # Add image filename
    player_obj['img_name'] = re.sub(r'[^a-z0-9]+', '_', player_obj['name'].lower()).strip('_')
    
    # Render template with all data
    return render_template('player.html', 
                         player=player_obj, 
                         wiki_summary=wiki_summary, 
                         match_records=match_records)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect('/')
    
    try:
        results = search_data(query)
        print(f"Search results for '{query}': {results}")  # Debug log
        # If only one team matched and no players/categories, redirect to team page
        if len(results['teams']) == 1 and not results['players'] and not results['categories']:
            team_name = list(results['teams'])[0]
            return redirect(url_for('team', team=team_name))
        # If only one player matched and no teams/categories, redirect to player page
        if len(results['players']) == 1 and not results['teams'] and not results['categories']:
            player_name = results['players'][0]['name']
            return redirect(url_for('player', player=player_name))
        return render_template('search.html', 
                             query=query,
                             players=results['players'],
                             teams=list(results['teams']),
                             categories=results['categories'])
    except Exception as e:
        print(f"Error during search: {str(e)}")  # Debug log
        return f"An error occurred: {str(e)}", 500

@app.route('/category/<cat>')
def category(cat):
    return render_template('category.html', category=cat)

@app.route('/best11')
def best11():
    return render_template('best11.html')

@app.route('/team/<team>')
def team(team):
    team_players = [p for p in players.values() if p.get('team','').lower() == team.lower()]
    role_order = {'Batter': 1, 'Opening Batter': 1, 'Top Order Batter': 1,
                  'Allrounder': 2, 'Bowling Allrounder': 2,
                  'Bowler': 3, 'Opening Bowler': 3}
    team_players.sort(key=lambda p: (role_order.get(p.get('playingRole', ''), 4), p.get('name', '')))
    for p in team_players:
        name = (p.get('name') or '')
        img_name = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        p['img_name'] = img_name
    return render_template('team.html', team=team, team_players=team_players)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# API Routes
@app.route('/api/teams')
def api_teams():
    teams = set(p.get('team', '') for p in players.values())
    return jsonify(sorted(list(teams)))

@app.route('/api/team/<team>')
def api_team(team):
    team_players = [p for p in players.values() if p.get('team', '').lower() == team.lower()]
    role_order = {'Batter': 1, 'Opening Batter': 1, 'Top Order Batter': 1,
                  'Allrounder': 2, 'Bowling Allrounder': 2,
                  'Bowler': 3, 'Opening Bowler': 3}
    team_players.sort(key=lambda p: (role_order.get(p.get('playingRole', ''), 4), p.get('name', '')))
    return jsonify(team_players)

@app.route('/api/players')
def api_players():
    return jsonify(list(players.values()))

@app.route('/api/category/<cat>')
def api_category(cat):
    func = CATEGORY_FUNCS.get(cat)
    if not func:
        return jsonify({'error':'unknown category'}), 400
    matched = [p for p in players.values() if func(p)]
    
    if cat == 'fast' and not matched:
        matched = [p for p in players.values() if ('fast' in (p.get('bowlingStyle') or '').lower() or 'pace' in (p.get('bowlingStyle') or '').lower()) and (p.get('wickets',0) > 2 or (p.get('economy') is not None and p.get('economy') < 9))]
    
    if cat == 'power':
        matched.sort(key=lambda x: x.get('runs',0), reverse=True)
    elif cat == 'anchor':
        matched.sort(key=lambda x: x.get('bat_avg',0), reverse=True)
    elif cat == 'finisher':
        matched.sort(key=lambda x: x.get('strike_rate',0), reverse=True)
    elif cat == 'allrounder':
        matched.sort(key=lambda x: (x.get('wickets',0)+x.get('runs',0)/10), reverse=True)
    elif cat == 'fast':
        matched.sort(key=lambda x: x.get('wickets',0), reverse=True)
    return jsonify(matched)

@app.route('/api/best11')
def api_best11():
    picks = []
    def pick(cat, n):
        resp = api_category(cat).get_json()
        if isinstance(resp, dict) and resp.get('error'):
            return []
        return resp[:n]
    picks += pick('power',3)
    picks += pick('anchor',2)
    picks += pick('finisher',2)
    picks += pick('allrounder',2)
    picks += pick('fast',2)
    
    seen = set()
    uniq = []
    for p in picks:
        if p['name'] not in seen:
            seen.add(p['name'])
            uniq.append(p)
        if len(uniq) >= 11:
            break
    return jsonify(uniq)

@app.route('/api/log', methods=['POST'])
def api_log():
    try:
        data = json.loads(request.data.decode('utf-8')) if request.data else {}
    except Exception:
        data = {}
    os.makedirs('logs', exist_ok=True)
    with open(os.path.join('logs','client_errors.log'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
    return ('', 204)

if __name__ == "__main__":
    print("Starting Flask server...")
    try:
        app.run(host='127.0.0.1', port=5050, debug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")