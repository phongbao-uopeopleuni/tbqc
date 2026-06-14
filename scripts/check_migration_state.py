"""
Read-only pre-migration check — chạy trước scripts/migrate.py để biết columns nào
đang thiếu trên DB đích. Không thay đổi dữ liệu.

Yêu cầu: DB_HOST, DB_PORT, DB_NAME, DB_USER (hoặc DB_MIGRATOR_USER) được set trong env.

Usage:
    python scripts/check_migration_state.py
    python scripts/check_migration_state.py --strict  # exit 1 nếu có cột còn thiếu
"""
import os
import sys
import argparse

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("ERROR: mysql-connector-python chưa cài. Chạy: pip install mysql-connector-python")
    sys.exit(2)


# Các cột bắt buộc phải có sau khi migrate hoàn tất.
# Format: (table, column, description)
REQUIRED_COLUMNS = [
    ("users", "password_changed_at", "session invalidation on password change (Fix 4.1)"),
    ("users", "consent_at", "NĐ13 consent timestamp (Fix 7.2)"),
    ("users", "consent_version", "NĐ13 consent version (Fix 7.2)"),
    ("users", "permissions", "per-user permission overrides (B2)"),
    ("albums", "is_public", "album visibility flag (Fix 3.1)"),
    ("persons", "version", "optimistic lock counter (Fix 4.2)"),
]

# Kiểm tra riêng: enum phải có giá trị 'editor'
ROLE_ENUM_CHECK = ("users", "role", "editor")


def _connect():
    user = os.environ.get("DB_MIGRATOR_USER") or os.environ.get("DB_USER")
    password = os.environ.get("DB_MIGRATOR_PASSWORD") or os.environ.get("DB_PASSWORD")
    if not user or not password:
        print("ERROR: Cần DB_MIGRATOR_USER (hoặc DB_USER) và mật khẩu tương ứng.")
        sys.exit(2)
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=user,
        password=password,
        database=os.environ.get("DB_NAME"),
    )


def check_columns(cursor):
    missing = []
    present = []
    for table, col, desc in REQUIRED_COLUMNS:
        cursor.execute(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
            (table, col),
        )
        row = cursor.fetchone()
        if row:
            present.append((table, col, desc))
        else:
            missing.append((table, col, desc))
    return present, missing


def check_role_enum(cursor):
    table, col, required_value = ROLE_ENUM_CHECK
    cursor.execute(
        "SELECT COLUMN_TYPE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table, col),
    )
    row = cursor.fetchone()
    if not row:
        return False, None
    col_type = row[0] if isinstance(row, (list, tuple)) else row.get("COLUMN_TYPE", "")
    return required_value in col_type, col_type


def main():
    parser = argparse.ArgumentParser(description="Read-only migration pre-check")
    parser.add_argument("--strict", action="store_true", help="Exit 1 nếu có cột còn thiếu")
    args = parser.parse_args()

    try:
        conn = _connect()
    except Error as e:
        print(f"ERROR: Không thể kết nối DB: {e}")
        sys.exit(2)

    cursor = conn.cursor()
    try:
        present, missing = check_columns(cursor)
        enum_ok, enum_type = check_role_enum(cursor)
    finally:
        cursor.close()
        conn.close()

    # --- Report ---
    print("\n=== Migration State Check ===\n")

    print("Columns already present (ALTER sẽ là no-op):")
    if present:
        for table, col, desc in present:
            print(f"  ✓  {table}.{col}  ({desc})")
    else:
        print("  (none)")

    print("\nColumns MISSING (ALTER sẽ thêm mới):")
    if missing:
        for table, col, desc in missing:
            print(f"  ✗  {table}.{col}  ({desc})")
    else:
        print("  (none — all present)")

    print(f"\nusers.role enum:")
    if enum_ok:
        print(f"  ✓  'editor' đã có trong enum: {enum_type}")
    else:
        print(f"  ✗  'editor' THIẾU — MODIFY COLUMN sẽ widening: {enum_type}")

    has_issues = bool(missing) or not enum_ok
    print()
    if has_issues:
        print("RESULT: Cần chạy migrate.py để áp dụng các thay đổi còn thiếu.")
    else:
        print("RESULT: DB đã ở trạng thái đầy đủ — migrate.py sẽ là no-op.")

    if args.strict and has_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
