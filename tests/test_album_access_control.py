"""
test_album_access_control.py — Fix 3.1: Per-album is_public auth (C4)
Chiến lược: mock db_config.get_db_connection để test logic auth mà không cần DB thật.
"""
import pytest
from unittest.mock import MagicMock, patch

def _make_mock_conn(album_row, images=None):
    """Helper tạo mock connection trả về album_row khi SELECT."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.fetchone.return_value = album_row
    cursor.fetchall.return_value = images or []
    conn.is_connected.return_value = True
    return conn

def test_api_get_album_images_private_blocks_anonymous(client):
    """Private album: anonymous user (no session) → 403."""
    private_album = {'album_id': 1, 'is_public': False}
    with patch('services.gallery_service.get_db_connection',
               return_value=_make_mock_conn(private_album)):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 403

def test_api_get_album_images_public_allows_anonymous(client):
    """Public album: anonymous → 200."""
    public_album = {'album_id': 1, 'is_public': True}
    mock_conn = _make_mock_conn(public_album, images=[])
    mock_conn.cursor().fetchall.return_value = []
    with patch('services.gallery_service.get_db_connection', return_value=mock_conn):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 200

def test_api_get_album_images_private_allows_members_gate(client):
    """Private album: user đã qua members gate → 200."""
    private_album = {'album_id': 1, 'is_public': False}
    mock_conn = _make_mock_conn(private_album, images=[])
    with client.session_transaction() as sess:
        sess['members_gate_ok'] = True
    with patch('services.gallery_service.get_db_connection', return_value=mock_conn):
        resp = client.get('/api/albums/1/images')
    assert resp.status_code == 200
