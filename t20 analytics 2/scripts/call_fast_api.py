import requests, json
try:
    r = requests.get('http://127.0.0.1:5000/api/category/fast', timeout=10)
    print('status', r.status_code)
    data = r.json()
    print('count', len(data))
    print(json.dumps(data[:10], indent=2))
except Exception as e:
    print('error', repr(e))
