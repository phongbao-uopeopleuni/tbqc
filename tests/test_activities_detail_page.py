import db
from services import activities_service


class _FakeCursor:
    def __init__(self, main_row):
        self._main_row = main_row
        self._current = None

    def execute(self, query, params=None):
        if 'SELECT * FROM activities WHERE activity_id = %s' in query:
            self._current = self._main_row
        elif 'FROM activities' in query and "status = 'published'" in query:
            self._current = []
        else:
            self._current = None

    def fetchone(self):
        if isinstance(self._current, dict):
            return self._current
        return None

    def fetchall(self):
        if isinstance(self._current, list):
            return self._current
        return []

    def close(self):
        return None


class _FakeConnection:
    def __init__(self, main_row):
        self._main_row = main_row

    def cursor(self, dictionary=True):
        return _FakeCursor(self._main_row)

    def commit(self):
        return None

    def close(self):
        return None

    def is_connected(self):
        return True


def test_activity_detail_page_renders_published_post(client, monkeypatch):
    main_row = {
        'activity_id': 101,
        'title': 'Bai test published',
        'summary': 'Tom tat',
        'category': None,
        'content': '<p>Noi dung</p>',
        'status': 'published',
        'thumbnail': None,
        'images': '[]',
        'created_at': None,
        'updated_at': None,
    }
    monkeypatch.setattr(db, 'get_db_connection', lambda: _FakeConnection(main_row))
    monkeypatch.setattr(activities_service, 'ensure_activities_table', lambda cursor: None)

    resp = client.get('/activities/101')

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Bai test published' in body
    assert 'Không tìm thấy bài viết' not in body


def test_activity_detail_page_hides_draft_for_public(client, monkeypatch):
    main_row = {
        'activity_id': 102,
        'title': 'Bai nhap',
        'summary': 'Tom tat nhap',
        'category': None,
        'content': '<p>Ban nhap</p>',
        'status': 'draft',
        'thumbnail': None,
        'images': '[]',
        'created_at': None,
        'updated_at': None,
    }
    monkeypatch.setattr(db, 'get_db_connection', lambda: _FakeConnection(main_row))
    monkeypatch.setattr(activities_service, 'ensure_activities_table', lambda cursor: None)

    resp = client.get('/activities/102')

    assert resp.status_code == 404
    body = resp.get_data(as_text=True)
    assert 'Không tìm thấy bài viết' in body
