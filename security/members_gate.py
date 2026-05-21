import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _load_fixed_members_passwords():
    raw = os.environ.get('MEMBERS_FIXED_ACCOUNTS', '').strip()
    result = {}
    for part in raw.split(','):
        part = part.strip()
        if ':' in part:
            u, p = part.split(':', 1)
            result[u.strip()] = p.strip()
    return result


_BCRYPT_HASH_PREFIXES = ('$2a$', '$2b$', '$2y$')


def _is_bcrypt_hash(value) -> bool:
    """Phát hiện bcrypt hash qua prefix chuẩn (không phụ thuộc độ dài)."""
    return isinstance(value, str) and value.startswith(_BCRYPT_HASH_PREFIXES)


def _verify_fixed_member_password(stored: str, provided: str) -> bool:
    """
    Verify mật khẩu tài khoản cố định (cổng Members) một cách constant-time.

    - `stored` là bcrypt hash ($2a/$2b/$2y) → dùng bcrypt.checkpw.
    - `stored` là plaintext (tương thích ngược) → secrets.compare_digest.
    - Đầu vào rỗng / lỗi bất kỳ → trả False (fail-closed, không raise ra ngoài).
    """
    if not stored or not provided:
        return False
    try:
        if _is_bcrypt_hash(stored):
            import bcrypt
            return bcrypt.checkpw(
                provided.encode('utf-8'),
                stored.encode('utf-8'),
            )
        return secrets.compare_digest(
            stored.encode('utf-8'),
            provided.encode('utf-8'),
        )
    except Exception:
        logger.exception('Members gate: error while verifying fixed account password')
        return False


FIXED_MEMBERS_PASSWORDS = _load_fixed_members_passwords()
MEMBERS_GATE_ACCOUNTS = [{'username': k, 'password': v} for k, v in FIXED_MEMBERS_PASSWORDS.items()]
if FIXED_MEMBERS_PASSWORDS:
    _fixed_hashed = sum(1 for v in FIXED_MEMBERS_PASSWORDS.values() if _is_bcrypt_hash(v))
    _fixed_plain = len(FIXED_MEMBERS_PASSWORDS) - _fixed_hashed
    logger.info(
        'Members gate: %d fixed account(s) from MEMBERS_FIXED_ACCOUNTS '
        '(bcrypt=%d, plaintext=%d). Khuyến nghị chuyển sang bcrypt hash '
        'để tránh lộ plaintext qua env/log/backup.',
        len(FIXED_MEMBERS_PASSWORDS), _fixed_hashed, _fixed_plain,
    )


def sync_members_gate_accounts_from_db():
    """
    Đồng bộ MEMBERS_GATE_ACCOUNTS từ database
    Lấy password từ database cho 4 accounts tbqcnhanh1-4
    Chỉ dùng khi cần đồng bộ động (có thể gọi khi app khởi động hoặc định kỳ)
    """
    global MEMBERS_GATE_ACCOUNTS
    from db import get_db_connection
    connection = get_db_connection()
    if not connection:
        logger.warning('Cannot sync MEMBERS_GATE_ACCOUNTS: database connection failed')
        return
    try:
        cursor = connection.cursor(dictionary=True)
        logger.debug('MEMBERS_GATE_ACCOUNTS sync: skipped (update accounts via env when needed)')
    except Exception as e:
        logger.error(f'Error syncing MEMBERS_GATE_ACCOUNTS: {e}')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def validate_tbqc_gate(username: str, password: str) -> bool:
    """
    Kiểm tra username/password cho cổng Members.
    - Ưu tiên 4 tài khoản cố định (dict FIXED_MEMBERS_PASSWORDS).
    - Các user khác: auth.get_user_by_username + verify_password.
    """
    username = (username or '').strip()
    password = (password or '').strip()
    if not username or not password:
        return False
    # 1) So khớp 4 tài khoản cố định bằng dict — verify constant-time
    #    (bcrypt.checkpw nếu env đã hash, secrets.compare_digest nếu plaintext).
    expected = FIXED_MEMBERS_PASSWORDS.get(username)
    if expected is not None and _verify_fixed_member_password(expected, password):
        logger.info(f'Members gate OK (fixed): {username}')
        return True
    # 2) Các user khác: DB
    try:
        from auth import get_user_by_username, verify_password
        user_data = get_user_by_username(username)
        if user_data and user_data.get('password_hash'):
            if verify_password(password, user_data['password_hash']):
                logger.info(f'Members gate OK (database): {username}')
                return True
            return False
        if user_data:
            return False
    except Exception as e:
        logger.warning(f'Members gate DB/auth error: {e}')
    return False
