import urllib.request, urllib.parse, json

def login_and_get_token(user='admin', pwd='Admin@1234'):
    data = urllib.parse.urlencode({'username': user, 'password': pwd}).encode()
    req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=data, headers={'Content-Type':'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode()
    return json.loads(body)['access_token']


def get_json(url, token):
    hdr = {'Authorization': f'Bearer {token}'}
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.getcode(), r.read().decode()


token = login_and_get_token()
print('Got token (len)=', len(token))

endpoints = [
    'http://127.0.0.1:8000/api/live/summary',
    'http://127.0.0.1:8000/api/live/gender-split',
    'http://127.0.0.1:8000/api/live/age-split',
    'http://127.0.0.1:8000/api/live/status-breakdown',
    'http://127.0.0.1:8000/api/history/monthly-trend?year=2026',
    'http://127.0.0.1:8000/api/history/regional-comparison?start_date=2026-01-01&end_date=2026-04-18'
]

for e in endpoints:
    try:
        code, body = get_json(e, token)
        print('\n', e, code)
        print(body[:1000])
    except Exception as ex:
        print('\nERROR', e, ex)
