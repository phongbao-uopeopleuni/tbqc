# scripts/branch_report_p5_p8.py
# -*- coding: utf-8 -*-

import os
import re
from collections import deque, defaultdict

import pandas as pd
import mysql.connector

# Optional: dotenv (không bắt buộc)
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


# =======================
# Config
# =======================
KEEP_EXISTING_DB_FOR_TARGET = True  # True: giữ nhánh DB nếu P-5..P-8 đã có
TARGET_MIN_GEN = 5
TARGET_MAX_GEN = 8
ANCHOR_GEN = 4  # dùng các P-4-* đã gán thủ công làm anchor

# mapping theo yêu cầu của bạn
branch_code_to_name = {
    "0": "Tổ tiên",
    "1": "Một",
    "2": "Hai",
    "3": "Ba",
    "4": "Bốn",
    "5": "Năm",
    "6": "Sáu",
    "7": "Bảy",
    "-1": "Khác",
}

ALLOWED_BRANCH_NAME = set(branch_code_to_name.values())

# Ưu tiên tie-break: Tổ tiên(0) lớn nhất => priority nhỏ nhất
branch_priority = {
    "Tổ tiên": 0,
    "Một": 1,
    "Hai": 2,
    "Ba": 3,
    "Bốn": 4,
    "Năm": 5,
    "Sáu": 6,
    "Bảy": 7,
    "Khác": 999,
}

id_gen_re = re.compile(r"^P-(\d+)-(\d+)$")


def get_gen_from_pid(pid: str):
    if not pid:
        return None
    m = id_gen_re.match(str(pid).strip())
    if not m:
        return None
    return int(m.group(1))


def normalize_branch(v):
    """
    Chuẩn hóa về dạng text 'Tổ tiên/Một/.../Khác'
    hỗ trợ cả input dạng '0..7/-1' hoặc text.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if s in branch_code_to_name:
        name = branch_code_to_name[s]
        return name if name in ALLOWED_BRANCH_NAME else None
    if s in ALLOWED_BRANCH_NAME:
        return s
    return None


def detect_branch_source(cursor):
    """
    Detect schema:
    - persons has branch_name?
    - persons has branch_id?
    - branches table exists?
    """
    cursor.execute("""
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'persons'
          AND COLUMN_NAME IN ('branch_name', 'branch_id')
    """)
    cols = {r["COLUMN_NAME"] for r in cursor.fetchall() if r and r.get("COLUMN_NAME")}

    cursor.execute("""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'branches'
        LIMIT 1
    """)
    has_branches_table = cursor.fetchone() is not None

    if "branch_name" in cols:
        return "branch_name"
    if "branch_id" in cols and has_branches_table:
        return "branch_id_join"
    return None


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # D:\tbqc
    scripts_dir = os.path.dirname(os.path.abspath(__file__))              # D:\tbqc\scripts

    # Load env
    env_path = os.path.join(base_dir, "tbqc_db.env")
    if load_dotenv and os.path.exists(env_path):
        load_dotenv(env_path)
    elif load_dotenv:
        load_dotenv()

    db_host = os.getenv("DB_HOST")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME")

    if not all([db_host, db_user, db_name]):
        raise RuntimeError("Thieu DB_HOST/DB_USER/DB_NAME (xem tbqc_db.env).")

    conn = mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
    )

    try:
        cursor = conn.cursor(dictionary=True)

        # 1) Load persons + branch info (normalized)
        branch_source = detect_branch_source(cursor)
        if not branch_source:
            raise RuntimeError("DB khong co branch_name trong persons va cung khong co branch_id+branches table.")

        persons_branch = {}  # pid -> normalized branch name (text)
        if branch_source == "branch_name":
            cursor.execute("SELECT person_id, branch_name FROM persons")
            for r in cursor.fetchall():
                pid = r.get("person_id")
                b = normalize_branch(r.get("branch_name"))
                persons_branch[pid] = b
        else:
            # join branch_id -> branches.branch_name
            cursor.execute("""
                SELECT p.person_id, b.branch_name
                FROM persons p
                LEFT JOIN branches b ON p.branch_id = b.branch_id
            """)
            for r in cursor.fetchall():
                pid = r.get("person_id")
                b = normalize_branch(r.get("branch_name"))
                persons_branch[pid] = b

        # 2) Build children map from relationships (parent -> children)
        cursor.execute("""
            SELECT parent_id, child_id, relation_type
            FROM relationships
            WHERE relation_type IN ('father', 'mother')
        """)
        children_map = defaultdict(list)
        for r in cursor.fetchall():
            parent_id = r.get("parent_id")
            child_id = r.get("child_id")
            if parent_id and child_id:
                children_map[parent_id].append(child_id)

        # 3) Build anchor list: P-4-* with valid branch
        anchors = []
        for pid, bname in persons_branch.items():
            gen = get_gen_from_pid(pid)
            if gen == ANCHOR_GEN and bname in ALLOWED_BRANCH_NAME:
                anchors.append((pid, bname))

        if not anchors:
            print("Khong tim thay anchor P-4-* co Nhánh hop le. Excel se rong.")
            out_path = os.path.join(scripts_dir, "branch_report_P5_P8.xlsx")
            pd.DataFrame(columns=["ID_person", "Nhánh"]).to_excel(out_path, index=False)
            return 0

        # 4) Multi-source propagation with tie-break by branch_priority
        # best_priority[pid] = min priority encountered for that pid
        best_priority = {}
        computed = {}  # pid -> chosen branch name for target range

        q = deque()
        for a_pid, a_branch in anchors:
            q.append((a_pid, a_branch))

        while q:
            pid, branch = q.popleft()
            gen = get_gen_from_pid(pid)
            if gen is None:
                continue
            if gen > TARGET_MAX_GEN:
                continue

            pr = branch_priority.get(branch, 999)
            prev_pr = best_priority.get(pid)

            # If we already have a better (smaller) priority, skip propagation
            if prev_pr is not None and pr >= prev_pr:
                continue

            best_priority[pid] = pr

            # Assign only for targets
            if TARGET_MIN_GEN <= gen <= TARGET_MAX_GEN:
                if not (KEEP_EXISTING_DB_FOR_TARGET and persons_branch.get(pid) in ALLOWED_BRANCH_NAME):
                    computed[pid] = branch

            # propagate to children
            for child_pid in children_map.get(pid, []):
                q.append((child_pid, branch))

        # 5) Output Excel: all persons in P-5..P-8
        out_rows = []
        for pid, db_branch in persons_branch.items():
            gen = get_gen_from_pid(pid)
            if gen is None:
                continue
            if TARGET_MIN_GEN <= gen <= TARGET_MAX_GEN:
                final_branch = None
                if KEEP_EXISTING_DB_FOR_TARGET and db_branch in ALLOWED_BRANCH_NAME:
                    final_branch = db_branch
                else:
                    final_branch = computed.get(pid)

                out_rows.append({
                    "ID_person": pid,
                    "Nhánh": final_branch if final_branch else ""
                })

        df = pd.DataFrame(out_rows)
        df.sort_values(by=["ID_person"], inplace=True)

        out_path = os.path.join(scripts_dir, "branch_report_P5_P8.xlsx")
        df.to_excel(out_path, index=False)

        print(f"Xong. Xuất Excel: {out_path}")
        return 0

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())