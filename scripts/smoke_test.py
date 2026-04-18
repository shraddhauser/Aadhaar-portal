#!/usr/bin/env python3
import urllib.request, urllib.error, urllib.parse

paths = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/dashboard',
    'http://127.0.0.1:8000/api/auth/login',
    'http://127.0.0.1:8000/docs'
]

for p in paths:
    try:
        if p.endswith('/api/auth/login'):
            data = urllib.parse.urlencode({'username':'admin','password':'Admin@1234'}).encode()
            req = urllib.request.Request(p, data=data)
            resp = urllib.request.urlopen(req, timeout=10)
        else:
            resp = urllib.request.urlopen(p, timeout=10)
        print(p, resp.getcode())
        body = resp.read(512)
        try:
            print(body.decode('utf-8'))
        except Exception:
            print(body[:200])
    except urllib.error.HTTPError as e:
        print(p, 'HTTPError', e.code)
        try:
            print(e.read().decode('utf-8'))
        except Exception:
            print(e.read()[:200])
    except Exception as e:
        print(p, 'ERROR', e)
