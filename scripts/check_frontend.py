#!/usr/bin/env python3
import urllib.request, urllib.error

url = 'http://127.0.0.1:3000/pages/login.html'
try:
    resp = urllib.request.urlopen(url, timeout=5)
    print('OK', resp.getcode())
    body = resp.read(1024).decode('utf-8', errors='ignore')
    # print only the <title> or first 300 chars
    print(body[:300])
except Exception as e:
    print('ERROR', e)
