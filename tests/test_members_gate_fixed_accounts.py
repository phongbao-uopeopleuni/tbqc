# -*- coding: utf-8 -*-
"""
Verify hardened members-gate fixed-account password checking.

- Plaintext vẫn hoạt động (tương thích ngược).
- Bcrypt hash trong env được phát hiện và verify đúng.
- Mật khẩu sai/rỗng luôn trả False.
- So sánh dùng secrets.compare_digest / bcrypt.checkpw (không phải `==`).
"""
import bcrypt
import pytest


def test_is_bcrypt_hash_detects_prefixes():
    from app import _is_bcrypt_hash

    assert _is_bcrypt_hash("$2a$12$" + "x" * 53)
    assert _is_bcrypt_hash("$2b$12$" + "x" * 53)
    assert _is_bcrypt_hash("$2y$12$" + "x" * 53)
    assert not _is_bcrypt_hash("plaintext_password")
    assert not _is_bcrypt_hash("")
    assert not _is_bcrypt_hash(None)


def test_verify_fixed_member_password_plaintext_backward_compat():
    from app import _verify_fixed_member_password

    assert _verify_fixed_member_password("secret123", "secret123") is True
    assert _verify_fixed_member_password("secret123", "wrong") is False
    assert _verify_fixed_member_password("secret123", "") is False
    assert _verify_fixed_member_password("", "secret123") is False


def test_verify_fixed_member_password_bcrypt_hash():
    from app import _verify_fixed_member_password

    plaintext = "super-strong-passw0rd"
    hashed = bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode()

    assert _verify_fixed_member_password(hashed, plaintext) is True
    assert _verify_fixed_member_password(hashed, "wrong") is False
    assert _verify_fixed_member_password(hashed, "") is False


def test_validate_tbqc_gate_uses_constant_time_check(monkeypatch):
    """
    validate_tbqc_gate phải từ chối `==`-style timing leaks:
    khi stored là plaintext, verify đi qua secrets.compare_digest.
    """
    import app as app_module

    monkeypatch.setitem(app_module.FIXED_MEMBERS_PASSWORDS, "fixed_user_test", "plain_pw")
    try:
        assert app_module.validate_tbqc_gate("fixed_user_test", "plain_pw") is True
        assert app_module.validate_tbqc_gate("fixed_user_test", "plain_pw_wrong") is False
        assert app_module.validate_tbqc_gate("fixed_user_test", "") is False
    finally:
        app_module.FIXED_MEMBERS_PASSWORDS.pop("fixed_user_test", None)


def test_validate_tbqc_gate_accepts_bcrypt_env_entry(monkeypatch):
    import app as app_module

    plaintext = "env-stored-bcrypt-pw"
    hashed = bcrypt.hashpw(plaintext.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode()
    monkeypatch.setitem(app_module.FIXED_MEMBERS_PASSWORDS, "fixed_user_bcrypt", hashed)
    try:
        assert app_module.validate_tbqc_gate("fixed_user_bcrypt", plaintext) is True
        assert app_module.validate_tbqc_gate("fixed_user_bcrypt", "wrong") is False
    finally:
        app_module.FIXED_MEMBERS_PASSWORDS.pop("fixed_user_bcrypt", None)
