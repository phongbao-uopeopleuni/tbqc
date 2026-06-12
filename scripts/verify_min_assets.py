# -*- coding: utf-8 -*-
"""Verify homepage serves minified assets (index.min.css/js, common.min.js)."""
import sys

sys.path.insert(0, '.')
import app as app_module

app = app_module.app
app.config['TESTING'] = True
c = app.test_client()

r = c.get('/')
html = r.get_data(as_text=True)
assert r.status_code == 200, f'homepage status {r.status_code}'
assert '/static/css/index.min.css?v=' in html, 'index.min.css reference missing'
assert '/static/js/index.min.js?v=' in html, 'index.min.js reference missing'
assert '/static/js/common.min.js?v=' in html, 'common.min.js reference missing'
assert '/static/css/index.css"' not in html, 'old index.css still referenced'

for path in ['/static/css/index.min.css', '/static/js/index.min.js', '/static/js/common.min.js']:
    rs = c.get(path)
    assert rs.status_code == 200, f'{path} -> {rs.status_code}'
    print(f'OK {path} {rs.status_code} {len(rs.data)} bytes')

print('HOMEPAGE VERIFY: ALL OK')
