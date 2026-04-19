"""Smoke test qua Flask test client: GET /genealogy → 200, đếm <script src=...>."""
import os, re, sys
os.environ.setdefault('FLASK_ENV', 'testing')

# Chỉ import sau khi env đã set
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app  # noqa: E402

app.config['TESTING'] = True
client = app.test_client()
resp = client.get('/genealogy')
print('GET /genealogy ->', resp.status_code)
html = resp.get_data(as_text=True)
print('html length:', len(html))
srcs = re.findall(r'<script[^>]*src="([^"]+)"', html)
print(f'Script srcs found: {len(srcs)}')
for s in srcs:
    print(' -', s)

# Kiểm tra chính xác 4 file mới có mặt
expected = [
    '/static/js/genealogy-tree-controls.js',
    '/static/js/genealogy-lineage-ui.js',
    '/static/js/genealogy-member-stats.js',
    '/static/js/genealogy-grave-family-view.js',
]
missing = [s for s in expected if s not in srcs]
print('Missing expected:', missing)
assert resp.status_code == 200, 'Trang /genealogy không trả 200'
assert not missing, f'Thiếu script: {missing}'
print('\nOK — /genealogy render 200 & đủ 4 script mới.')
