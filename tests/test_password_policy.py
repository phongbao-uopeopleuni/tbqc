"""test_password_policy.py — Fix 4.3: Password min 10 chars + digit + letter (L3)"""
import pytest
from admin.users_routes import _validate_password_strength

def test_short_password_rejected():
    assert _validate_password_strength("Ab1") is not None
    assert _validate_password_strength("Ab123456") is not None  # 8 chars — còn thiếu

def test_no_digit_rejected():
    assert _validate_password_strength("abcdefghij") is not None

def test_no_letter_rejected():
    assert _validate_password_strength("1234567890") is not None

def test_strong_password_accepted():
    assert _validate_password_strength("StrongPass1") is None
    assert _validate_password_strength("MyPassword123") is None

def test_exactly_10_chars_with_digit_and_letter():
    assert _validate_password_strength("Password1!") is None  # 10 chars
