# -*- coding: utf-8 -*-
"""Verify /genealogy render: 2 details.mobile-advanced-controls co `open` + script dong tren mobile."""
import re
import sys

sys.path.insert(0, '.')
import app as app_module

app = app_module.app
app.config['TESTING'] = True
c = app.test_client()

r = c.get('/genealogy')
html = r.get_data(as_text=True)
assert r.status_code == 200, f'/genealogy status {r.status_code}'

details_open = re.findall(r'<details[^>]*mobile-advanced-controls[^>]*\bopen\b[^>]*>', html)
assert len(details_open) == 2, f'expected 2 <details ... open>, got {len(details_open)}'

assert "matchMedia && window.matchMedia('(max-width: 768px)')" in html, 'mobile-close script missing'
assert "removeAttribute('open')" in html, 'removeAttribute call missing'

for el_id in ['zoomInBtn', 'zoomOutBtn', 'resetZoomBtn', 'fitToViewBtn', 'fullscreenBtn', 'genFilter', 'syncBtn', 'exportPdfBtn']:
    assert f'id="{el_id}"' in html, f'{el_id} missing from page'

print('GENEALOGY CONTROLS VERIFY: ALL OK (2 details open + mobile script + 8 control ids)')
