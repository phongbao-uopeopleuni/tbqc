"""test_log_retention.py — Fix 5.1: Activity logs cleanup"""
import pytest
from unittest.mock import MagicMock
import scripts.cleanup_activity_logs as cleanup_module

def test_cleanup_executes_correct_sql(monkeypatch):
    """cleanup() gửi đúng DELETE query với parameterized RETENTION_DAYS."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.return_value = ("activity_logs",)
    mock_cursor.rowcount = 5
    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()

    assert result == 5
    calls = [str(c) for c in mock_cursor.execute.call_args_list]
    assert any("DELETE FROM activity_logs" in c for c in calls)
    assert any("INTERVAL" in c for c in calls)

def test_cleanup_skips_when_table_missing(monkeypatch):
    """cleanup() trả về 0 nếu bảng không tồn tại — không crash."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.is_connected.return_value = True
    mock_cursor.fetchone.return_value = None
    monkeypatch.setattr(cleanup_module, "get_db_connection", lambda: mock_conn)

    result = cleanup_module.cleanup()
    assert result == 0
