#!/usr/bin/env python3
import urllib.request, urllib.parse, json
from _credentials import get_admin_credentials
API_BASE = 'http://127.0.0.1:8000/api'

def login(user=None, pwd=None):
    if user is None or pwd is None:
        creds = get_admin_credentials()
        if creds is None:
            raise SystemExit('Set ADMIN_USERNAME and ADMIN_PASSWORD, or run in a terminal.')
        user, pwd = creds
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
