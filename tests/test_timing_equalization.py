import pytest
import bcrypt
from unittest.mock import patch

def test_timing_equalization_calls_bcrypt_once():
    """Verify that verify_password and equalize_login_timing both call bcrypt.checkpw exactly once."""
    from utils.crypto import equalize_login_timing
    from auth import verify_password
    
    with patch('bcrypt.checkpw') as mock_checkpw:
        mock_checkpw.return_value = False
        
        # 1. Simulate non-existent user login (uses equalize_login_timing)
        equalize_login_timing("wrongpassword")
        assert mock_checkpw.call_count == 1, "equalize_login_timing must call bcrypt.checkpw exactly once to equal timing"
        mock_checkpw.reset_mock()
        
        # 2. Simulate existing user with wrong password (uses verify_password)
        hashed_pw = bcrypt.hashpw(b"realpassword", bcrypt.gensalt())
        # In python 3, bcrypt returns bytes, our auth checks assume string sometimes or bytes.
        # auth.verify_password takes (plain, hashed)
        verify_password("wrongpassword", hashed_pw)
        assert mock_checkpw.call_count == 1, "verify_password must call bcrypt.checkpw exactly once"

def test_members_gate_timing_equalization(monkeypatch):
    """Verify members gate calls checkpw once for unknown user."""
    from security.members_gate import validate_tbqc_gate
    
    with patch('bcrypt.checkpw') as mock_checkpw:
        mock_checkpw.return_value = False
        
        # Ensure user is not found in DB
        monkeypatch.setattr("security.members_gate.FIXED_MEMBERS_PASSWORDS", {})
        monkeypatch.setattr("auth.get_user_by_username", lambda u: None)
        
        validate_tbqc_gate("unknown", "any")
        assert mock_checkpw.call_count == 1

def test_admin_login_timing_equalization(client, monkeypatch):
    """Verify admin login calls checkpw once for unknown user."""
    with patch('bcrypt.checkpw') as mock_checkpw:
        mock_checkpw.return_value = False
        
        # We also need to mock get_user_by_username to return None (unknown user)
        monkeypatch.setattr("admin.login_routes.get_user_by_username", lambda u: None)
        monkeypatch.setattr("admin.login_routes.log_login", lambda **kw: None)
        
        client.post("/admin/login", data={"username": "unknown", "password": "any"})
        
        # Since user doesn't exist, it should fallback to equalize_login_timing and call checkpw
        assert mock_checkpw.call_count == 1

def test_equalize_login_timing_actually_runs_bcrypt():
    """Test behavioral: equalize_login_timing phải thực sự chạy bcrypt (~100ms).
    
    Test này KHÔNG dùng mock. Nếu _DUMMY_BCRYPT_HASH không hợp lệ → bcrypt raise exception
    → bị except pass nuốt → hàm return trong microseconds → test FAIL với elapsed < 0.05s.
    """
    import time
    from utils.crypto import equalize_login_timing

    # Import lại module để lấy giá trị _DUMMY_BCRYPT_HASH hiện tại (không cache)
    import importlib
    import utils.crypto as crypto_module
    importlib.reload(crypto_module)

    start = time.monotonic()
    crypto_module.equalize_login_timing("any-test-password")
    elapsed = time.monotonic() - start

    assert elapsed >= 0.05, (
        f"equalize_login_timing chỉ mất {elapsed:.4f}s — bcrypt không chạy thực sự. "
        f"Kiểm tra _DUMMY_BCRYPT_HASH: phải đúng 60 bytes và hợp lệ. "
        f"Gợi ý: chạy `python -c \"import bcrypt; print(len(bcrypt.hashpw(b'x', bcrypt.gensalt(12))))\"` "
        f"để verify độ dài hash chuẩn."
    )


def test_members_gate_timing_equalization_behavioral(monkeypatch):
    """Test behavioral: members gate phải tốn thời gian bcrypt cho unknown user.
    
    Monkeypatch path: security.members_gate import 'from auth import get_user_by_username'
    bên trong function body (lazy import) → patch target là auth.get_user_by_username.
    """
    import time
    from security.members_gate import validate_tbqc_gate

    monkeypatch.setattr("security.members_gate.FIXED_MEMBERS_PASSWORDS", {})
    monkeypatch.setattr("auth.get_user_by_username", lambda u: None)

    start = time.monotonic()
    result = validate_tbqc_gate("unknown_user_xyz", "any_password_123")
    elapsed = time.monotonic() - start

    assert result is False
    assert elapsed >= 0.05, (
        f"Members gate chỉ mất {elapsed:.4f}s cho unknown user — "
        f"timing equalization không hoạt động (phụ thuộc TD-1 fix)."
    )
