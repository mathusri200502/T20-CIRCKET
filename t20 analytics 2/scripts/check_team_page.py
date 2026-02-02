import requests
r = requests.get('http://127.0.0.1:5000/team/India')
html = r.text
start = html.find('<div class="player-grid">')
end = html.find('</div>', start)
print('status', r.status_code)
print(html[start:end+6])
