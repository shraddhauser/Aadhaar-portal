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
    try:
        auth = login()
        token = auth['access_token']
        print('Logged in, token len:', len(token))

        endpoints = ['/live/summary','/live/gender-split','/live/age-split','/live/status-breakdown','/live/update-types','/history/monthly-trend?year=2024']
        for ep in endpoints:
            try:
                data = get(ep, token)
                print('\n', ep, '->')
                print(json.dumps(data, indent=2)[:1000])
            except Exception as e:
                print(ep, 'ERROR', e)
    except Exception as e:
        print('Login failed:', e)
