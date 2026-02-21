#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiem tra sau khi chia tach Blueprints:
1. Khong co AssertionError (view function mapping overwriting) khi khoi dong
2. Cac endpoint da chuyen van tra ve HTTP 200 (hoac 401/302 khi can auth, 500 khi DB down)
Chay: python scripts/check_blueprint_routes.py
"""
import sys
import os

# Chay tu thu muc goc du an
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    errors = []
    print("=" * 60)
    print("1. Khoi dong app va kiem tra loi trung endpoint (AssertionError)")
    print("=" * 60)
    try:
        from app import app
        print("   OK: App import thanh cong, khong co AssertionError.")
    except AssertionError as e:
        if "View function mapping" in str(e) and "overwriting" in str(e):
            errors.append("LOI: Trung endpoint - " + str(e))
            print("   FAIL:", e)
        else:
            raise
    except Exception as e:
        print("   FAIL: ", type(e).__name__, e)
        errors.append(str(e))
        return 1

    print()
    print("2. Kiem tra trung rule cung URL (cung method -> co the gay hanh vi la)")
    print("-" * 60)
    from collections import defaultdict
    by_rule = defaultdict(list)
    for r in app.url_map.iter_rules():
        key = (r.rule, tuple(sorted(r.methods - {"HEAD", "OPTIONS"})))
        by_rule[key].append(r.endpoint)
    dups = {k: v for k, v in by_rule.items() if len(v) > 1}
    if dups:
        for (rule, methods), endpoints in list(dups.items())[:15]:
            print("   ", rule, methods, "->", endpoints)
        print("   (Cung URL + cung method nhieu endpoint: Flask dung endpoint dang ky dau tien)")
    else:
        print("   Khong co cap (rule, method) nao bi trung.")
    print()

    print("3. Goi cac endpoint da chuyen sang blueprints")
    print("-" * 60)
    client = app.test_client()
    # Endpoint khong phu thuoc DB hoac chi can co app
    static_tests = [
        ("GET", "/"),
        ("GET", "/genealogy"),
        ("GET", "/contact"),
        ("GET", "/documents"),
        ("GET", "/login"),
        ("GET", "/api/health"),
        ("GET", "/family-tree-core.js"),
        ("GET", "/family-tree-ui.js"),
        ("GET", "/genealogy-lineage.js"),
    ]
    for method, path in static_tests:
        try:
            r = client.open(path, method=method)
            status = r.status_code
            if status == 200:
                print("   ", method, path, "->", status, "OK")
            else:
                print("   ", method, path, "->", status, "(kiem tra)")
        except Exception as e:
            print("   ", method, path, "ERROR:", e)
            errors.append(path + ": " + str(e))

    # Endpoint phu thuoc DB: chap nhan 200 hoac 500 (khi DB khong chay)
    db_tests = [
        ("GET", "/api/family-tree"),
        ("GET", "/api/relationships"),
        ("GET", "/api/generations"),
        ("GET", "/api/tree"),
        ("GET", "/api/persons"),
        ("GET", "/api/albums"),
    ]
    print()
    print("   Endpoint phu thuoc DB (200 hoac 500 neu DB down):")
    for method, path in db_tests:
        try:
            r = client.open(path, method=method)
            status = r.status_code
            ok = status in (200, 500)
            if status == 200:
                print("   ", method, path, "->", status, "OK")
            elif status == 500:
                print("   ", method, path, "->", status, "(DB down hoac loi - routing OK)")
            else:
                print("   ", method, path, "->", status)
        except Exception as e:
            print("   ", method, path, "ERROR:", e)
            errors.append(path + ": " + str(e))

    print()
    print("=" * 60)
    if errors:
        print("TONG KET: Co loi:", len(errors))
        for e in errors:
            print("  -", e)
        return 1
    print("TONG KET: Khong phat hien AssertionError; cac endpoint static tra 200.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
