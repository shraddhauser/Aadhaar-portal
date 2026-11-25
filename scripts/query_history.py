#!/usr/bin/env python3
import urllib.request, urllib.parse, json
API_BASE = 'http://127.0.0.1:8000/api'

def login(user='admin', pwd='Admin@1234'):
    url = f'{API_BASE}/auth/login'
    data = urllib.parse.urlencode({'username': user, 'password': pwd}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def get(path, token):
    req = urllib.request.Request(f'{API_BASE}{path}')
    req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

if __name__ == '__main__':
    auth = login()
    token = auth['access_token']
    print('Logged in as admin')
    years = get('/history/yearly-growth', token)
    print('years:', years)
    if years:
        latest = years[-1]['year']
        print('Latest year:', latest)
        mt = get(f'/history/monthly-trend?year={latest}', token)
        print('monthly-trend for', latest, '->', mt)
    else:
        print('No yearly data')
