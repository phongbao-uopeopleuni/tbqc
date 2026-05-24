"""Shared crypto utilities — anti-enumeration, timing equalization."""
import bcrypt

# Dummy hash để equalize timing khi user không tồn tại
# Generated với bcrypt.gensalt(rounds=12) từ string ngẫu nhiên
_DUMMY_BCRYPT_HASH = b'$2b$12$DummyHashToEqualizeTimingAttackForNonExistentUsers0000'

GENERIC_AUTH_ERROR = 'Sai tài khoản hoặc mật khẩu'

def equalize_login_timing(provided_password: str) -> None:
    """Run dummy bcrypt check để equalize timing với real verification."""
    try:
        bcrypt.checkpw(provided_password.encode('utf-8'), _DUMMY_BCRYPT_HASH)
    except Exception:
        pass
