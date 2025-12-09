#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script import dữ liệu từ TBQC_FINAL.csv vào database
UPDATED FOR TBQC_FINAL.csv

Yêu cầu:
- Giữ nguyên tiền tố trong tên (TBQC, Ưng, Bửu, CTTN, CHTN, v.v.)
- Phân biệt người trùng tên bằng Đời
- Sử dụng Check tên bố/mẹ để xác nhận quan hệ
- Xử lý quan hệ cha-mẹ-con, hôn phối, anh chị em, con cái
"""

import csv
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import re
import logging
from typing import Dict, List, Optional, Tuple

# =====================================================
# CẤU HÌNH
# =====================================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'tbqc2025',
    'user': 'tbqc_admin',  # User đã tạo trong database
    'password': 'tbqc2025',  # Password đã tạo
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

CSV_FILE = 'TBQC_FINAL.csv'

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('genealogy_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# File log cho các trường hợp mơ hồ
ambiguous_log = open('genealogy_ambiguous_parents.log', 'w', encoding='utf-8')

# File log cho suy diễn con dâu/con rể (sẽ được tạo trong infer_in_law_relationships)

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def normalize(str_value):
    """Chuẩn hóa chuỗi (chỉ trim, KHÔNG thay đổi tiền tố hay viết hoa)"""
    if not str_value:
        return None
    result = str(str_value).strip()
    return result if result else None

def normalize_name_for_search(name):
    """Chuẩn hóa tên để tìm kiếm (xử lý gạch nối)
    
    Chuyển đổi tất cả các loại gạch nối về khoảng trắng và chuẩn hóa khoảng trắng.
    Ví dụ: "Ưng-Lương" -> "Ưng Lương", "Ưng Lương" -> "Ưng Lương"
    """
    if not name or not isinstance(name, str):
        return ''
    normalized = name.strip()
    # Thay thế tất cả các loại gạch nối Unicode và ASCII về khoảng trắng
    # \u2010-\u2015: các loại gạch nối Unicode (‑, ‒, –, —, ―)
    # \-: dấu gạch nối ASCII thông thường
    normalized = re.sub(r'[\u2010-\u2015\-]', ' ', normalized)
    # Gom nhiều khoảng trắng liên tiếp về 1 khoảng trắng
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

def parse_date(date_str):
    """Parse ngày từ format DD/MM/YYYY hoặc DD/MM/--"""
    if not date_str or date_str.strip() == '' or '--' in date_str:
        return None
    try:
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            day, month, year = parts
            if year == '--' or not year.isdigit():
                return None
            # Xử lý năm 2 chữ số
            if len(year) == 2:
                year = '19' + year if int(year) > 50 else '20' + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception as e:
        logger.warning(f"Lỗi parse ngày '{date_str}': {e}")
    return None

def parse_lunar_date(date_str):
    """Parse ngày âm lịch (giữ nguyên format gốc)"""
    if not date_str or date_str.strip() == '' or '--' in date_str:
        return None
    return normalize(date_str)

def parse_names_list(text):
    """Parse danh sách tên từ chuỗi (tách bằng ; hoặc ,)"""
    if not text or text.strip() == '':
        return []
    # Tách theo ; hoặc ,
    names = re.split(r'[;,]', text)
    return [normalize(name) for name in names if normalize(name)]

# =====================================================
# DATABASE HELPER FUNCTIONS
# =====================================================

def get_or_create_location(cursor, location_name, location_type):
    """Lấy hoặc tạo location"""
    if not location_name:
        return None
    
    cursor.execute(
        "SELECT location_id FROM locations WHERE location_name = %s AND location_type = %s",
        (location_name, location_type)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO locations (location_name, location_type, full_address) VALUES (%s, %s, %s)",
        (location_name, location_type, location_name)
    )
    return cursor.lastrowid

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    
    try:
        gen_num = int(generation_number)
    except:
        return None
    
    cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (gen_num,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO generations (generation_number) VALUES (%s)",
        (gen_num,)
    )
    return cursor.lastrowid

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name:
        return None
    
    cursor.execute("SELECT branch_id FROM branches WHERE branch_name = %s", (branch_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO branches (branch_name) VALUES (%s)",
        (branch_name,)
    )
    return cursor.lastrowid

# =====================================================
# TÌM CHA/MẸ VỚI LOGIC ĐÚNG
# =====================================================

def find_parent_by_name_and_generation(
    cursor, 
    parent_name: str, 
    child_generation: int,
    check_flag: Optional[str] = None,
    child_fm_id: Optional[str] = None
) -> Optional[int]:
    """
    Tìm cha/mẹ theo tên và đời, sử dụng FM_ID để tránh mapping nhầm
    
    Logic:
    1. Tìm tất cả người có tên trùng khớp (full_name = parent_name)
    2. Nếu >1 kết quả:
       - Ưu tiên người có Đời = child_generation - 1
       - Nếu có child_fm_id, tìm các anh chị em của child (cùng FM_ID) 
         và xác định cha mẹ chung từ relationships của họ
       - Nếu có check_flag = 'ok' hoặc 'OK', ưu tiên hơn
    3. Nếu vẫn nhiều hoặc không tìm thấy → log và return None
    
    QUAN TRỌNG: Giữ nguyên tiền tố trong tên, không chuẩn hóa
    """
    if not parent_name or parent_name.strip() == '' or parent_name == '??':
        return None
    
    parent_name = parent_name.strip()
    
    # Tính expected generation của parent
    expected_parent_generation = child_generation - 1
    
    # Tìm generation_id tương ứng với expected_parent_generation
    cursor.execute(
        "SELECT generation_id FROM generations WHERE generation_number = %s",
        (expected_parent_generation,)
    )
    gen_result = cursor.fetchone()
    expected_gen_id = gen_result[0] if gen_result else None
    
    # Nếu có FM_ID, sử dụng để xác định chính xác hơn
    if child_fm_id and child_fm_id.strip() and child_fm_id != '':
        # Tìm tất cả anh chị em có cùng FM_ID
        cursor.execute("""
            SELECT DISTINCT r.father_id, r.mother_id
            FROM relationships r
            INNER JOIN persons p ON r.child_id = p.person_id
            WHERE p.fm_id = %s
              AND (r.father_id IS NOT NULL OR r.mother_id IS NOT NULL)
        """, (child_fm_id,))
        
        fm_parents = cursor.fetchall()
        
        if len(fm_parents) == 1:
            # Có 1 cặp cha mẹ duy nhất cho nhóm FM_ID này
            father_id, mother_id = fm_parents[0]
            
            # Xác định đây là cha hay mẹ
            normalized_parent_name = normalize_name_for_search(parent_name)
            
            if father_id:
                cursor.execute("SELECT full_name FROM persons WHERE person_id = %s", (father_id,))
                father_result = cursor.fetchone()
                if father_result and normalize_name_for_search(father_result[0]) == normalized_parent_name:
                    logger.info(f"Tìm thấy cha '{parent_name}' qua FM_ID {child_fm_id} (person_id={father_id})")
                    return father_id
            
            if mother_id:
                cursor.execute("SELECT full_name FROM persons WHERE person_id = %s", (mother_id,))
                mother_result = cursor.fetchone()
                if mother_result and normalize_name_for_search(mother_result[0]) == normalized_parent_name:
                    logger.info(f"Tìm thấy mẹ '{parent_name}' qua FM_ID {child_fm_id} (person_id={mother_id})")
                    return mother_id
    
    # Normalize tên để tìm kiếm (xử lý gạch nối)
    normalized_parent_name = normalize_name_for_search(parent_name)
    
    # Tìm tất cả người có tên trùng khớp (sau khi normalize)
    # Ưu tiên người có Đời đúng
    if expected_gen_id:
        # Tìm chính xác trước
        cursor.execute(
            """SELECT person_id, generation_id, csv_id, full_name
               FROM persons 
               WHERE full_name = %s AND generation_id = %s""",
            (parent_name, expected_gen_id)
        )
        matching_generation = cursor.fetchall()
        
        # Nếu không tìm thấy, thử normalize (LUÔN thử, không chỉ khi normalized != original)
        if len(matching_generation) == 0:
            # Tìm tất cả người có đời đúng, rồi normalize để so sánh
            cursor.execute(
                """SELECT person_id, generation_id, csv_id, full_name
                   FROM persons 
                   WHERE generation_id = %s""",
                (expected_gen_id,)
            )
            all_gen_persons = cursor.fetchall()
            matching_generation = [
                p for p in all_gen_persons 
                if normalize_name_for_search(p[3]) == normalized_parent_name
            ]
        
        if len(matching_generation) == 1:
            # Chỉ có 1 người có Đời đúng → dùng
            logger.info(f"Chọn cha/mẹ '{parent_name}' với Đời {expected_parent_generation} (person_id={matching_generation[0][0]})")
            return matching_generation[0][0]
        
        if len(matching_generation) > 1:
            # Vẫn nhiều người cùng Đời → log mơ hồ
            ambiguous_log.write(
                f"TRÙNG TÊN VÀ ĐỜI: '{parent_name}' - Đời {expected_parent_generation} - "
                f"Có {len(matching_generation)} người: {[p[0] for p in matching_generation]}"
            )
            if child_fm_id:
                ambiguous_log.write(f" - FM_ID: {child_fm_id}")
            ambiguous_log.write("\n")
            # Nếu có check_flag = ok, có thể ưu tiên nhưng vẫn log
            if check_flag and check_flag.lower() == 'ok':
                logger.warning(f"Check flag = OK nhưng vẫn có {len(matching_generation)} người trùng")
            return None
    
    # Tìm tất cả người có tên trùng (không phân biệt Đời)
    # Thử chính xác trước
    cursor.execute(
        "SELECT person_id, generation_id, csv_id, full_name FROM persons WHERE full_name = %s",
        (parent_name,)
    )
    all_candidates = cursor.fetchall()
    
    # Nếu không tìm thấy, thử normalize (LUÔN thử, không chỉ khi normalized != original)
    if len(all_candidates) == 0:
        cursor.execute(
            "SELECT person_id, generation_id, csv_id, full_name FROM persons"
        )
        all_persons = cursor.fetchall()
        # So sánh sau khi normalize cả hai bên
        all_candidates = []
        for p in all_persons:
            normalized_db_name = normalize_name_for_search(p[3])
            if normalized_db_name == normalized_parent_name:
                all_candidates.append(p)
    
    if not all_candidates:
        logger.warning(f"Không tìm thấy cha/mẹ: '{parent_name}'")
        return None
    
    if len(all_candidates) == 1:
        # Chỉ có 1 kết quả → dùng luôn (nhưng log cảnh báo nếu Đời không đúng)
        person_id, gen_id, csv_id = all_candidates[0]
        if gen_id != expected_gen_id:
            ambiguous_log.write(
                f"ĐỜI KHÔNG KHỚP: '{parent_name}' - Mong đợi Đời {expected_parent_generation} - "
                f"Tìm thấy Đời khác (person_id={person_id}, csv_id={csv_id})"
            )
            if child_fm_id:
                ambiguous_log.write(f" - FM_ID: {child_fm_id}")
            ambiguous_log.write("\n")
        return person_id
    
    # Nhiều kết quả nhưng không có ai có Đời đúng → log
    ambiguous_log.write(
        f"KHÔNG TÌM THẤY ĐỜI ĐÚNG: '{parent_name}' - Mong đợi Đời {expected_parent_generation} - "
        f"Có {len(all_candidates)} người nhưng không ai có Đời đúng: {[p[0] for p in all_candidates]}"
    )
    if child_fm_id:
        ambiguous_log.write(f" - FM_ID: {child_fm_id}")
    ambiguous_log.write("\n")
    return None

# =====================================================
# IMPORT FUNCTIONS
# =====================================================

def import_persons(cursor, csv_data: List[Dict]) -> Dict[str, int]:
    """
    Bước 1: Import tất cả persons (chưa gán cha/mẹ)
    Returns: mapping csv_id -> person_id
    """
    logger.info("=== BƯỚC 1: Import persons ===")
    
    csv_id_to_person_id = {}
    stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'duplicates_skipped': 0}
    
    for row in csv_data:
        csv_id = normalize(row.get('ID', ''))
        if not csv_id:
            continue
        
        full_name = normalize(row.get('Họ và tên', ''))
        if not full_name:
            logger.warning(f"Bỏ qua dòng {csv_id}: không có tên")
            stats['errors'] += 1
            continue
        
        # Kiểm tra đã tồn tại chưa (đảm bảo mỗi csv_id chỉ map với 1 person_id)
        cursor.execute("SELECT person_id FROM persons WHERE csv_id = %s", (csv_id,))
        existing = cursor.fetchone()
        
        # VALIDATION: Đảm bảo không có duplicate csv_id
        # (existing là tuple hoặc None, không phải list)
        # Kiểm tra nếu csv_id đã được map với person_id khác trong lần import này
        if csv_id in csv_id_to_person_id:
            logger.warning(f"csv_id '{csv_id}' đã được xử lý trong lần import này, bỏ qua")
            stats['duplicates_skipped'] += 1
            continue
        
        # Lấy thông tin
        common_name = normalize(row.get('Tên thường gọi', ''))
        gender = normalize(row.get('Giới tính', ''))
        status = normalize(row.get('Trạng thái', ''))
        generation_num = normalize(row.get('Đời', ''))
        origin = normalize(row.get('Nguyên quán', ''))
        nationality = normalize(row.get('Quốc Tịch', '')) or 'Việt Nam'
        religion = normalize(row.get('Tôn giáo', ''))
        blood_type = normalize(row.get('Nhóm máu', ''))
        genetic_disease = normalize(row.get('Bệnh di truyền', ''))
        fm_id = normalize(row.get('Father_Mother_ID', ''))  # Lấy FM_ID từ CSV
        
        # Lấy tên bố/mẹ từ CSV (lấy cột cuối cùng nếu có nhiều cột trùng tên)
        row_keys = list(row.keys())
        father_name_col_idx = -1
        mother_name_col_idx = -1
        for i, key in enumerate(row_keys):
            if key == 'Tên bố':
                father_name_col_idx = i
            if key == 'Tên mẹ':
                mother_name_col_idx = i
        
        father_name_csv = None
        mother_name_csv = None
        if father_name_col_idx >= 0:
            father_name_csv = normalize(row[row_keys[father_name_col_idx]])
        if mother_name_col_idx >= 0:
            mother_name_csv = normalize(row[row_keys[mother_name_col_idx]])
        
        # Lấy hoặc tạo generation, location
        generation_id = get_or_create_generation(cursor, generation_num)
        origin_location_id = get_or_create_location(cursor, origin, 'Nguyên quán')
        
        if existing:
            # Update (đảm bảo csv_id đã tồn tại chỉ update, không tạo mới)
            person_id = existing[0]
            cursor.execute("""
                UPDATE persons 
                SET full_name = %s, common_name = %s, gender = %s, generation_id = %s,
                    origin_location_id = %s, nationality = %s, religion = %s, 
                    status = %s, blood_type = %s, genetic_disease = %s, fm_id = %s,
                    father_name = %s, mother_name = %s
                WHERE person_id = %s
            """, (full_name, common_name, gender, generation_id, origin_location_id,
                  nationality, religion, status, blood_type, genetic_disease, fm_id,
                  father_name_csv, mother_name_csv, person_id))
            stats['updated'] += 1
        else:
            # Insert
            cursor.execute("""
                INSERT INTO persons 
                (csv_id, fm_id, full_name, common_name, gender, generation_id, 
                 origin_location_id, nationality, religion, status, blood_type, genetic_disease,
                 father_name, mother_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (csv_id, fm_id, full_name, common_name, gender, generation_id,
                  origin_location_id, nationality, religion, status, blood_type, genetic_disease,
                  father_name_csv, mother_name_csv))
            person_id = cursor.lastrowid
            stats['inserted'] += 1
        
        csv_id_to_person_id[csv_id] = person_id
        
        # Import birth records
        birth_date_solar = parse_date(row.get('Ngày sinh (dương lịch)', ''))
        birth_date_lunar = parse_lunar_date(row.get('Ngày sinh (âm lịch)', ''))
        birth_location = normalize(row.get('Nơi sinh', ''))
        birth_location_id = get_or_create_location(cursor, birth_location, 'Nơi sinh') if birth_location else None
        
        if existing:
            cursor.execute("""
                UPDATE birth_records 
                SET birth_date_solar = %s, birth_date_lunar = %s, birth_location_id = %s
                WHERE person_id = %s
            """, (birth_date_solar, birth_date_lunar, birth_location_id, person_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO birth_records (person_id, birth_date_solar, birth_date_lunar, birth_location_id)
                    VALUES (%s, %s, %s, %s)
                """, (person_id, birth_date_solar, birth_date_lunar, birth_location_id))
        else:
            cursor.execute("""
                INSERT INTO birth_records (person_id, birth_date_solar, birth_date_lunar, birth_location_id)
                VALUES (%s, %s, %s, %s)
            """, (person_id, birth_date_solar, birth_date_lunar, birth_location_id))
        
        # Import death records
        death_date_solar = parse_date(row.get('Ngày mất(dương lịch', ''))
        death_date_lunar = parse_lunar_date(row.get('Ngày mất(âm lịch)', ''))
        death_location = normalize(row.get('Nơi mất', ''))
        grave_location = normalize(row.get('Mộ phần', ''))
        death_location_id = get_or_create_location(cursor, death_location, 'Nơi mất') if death_location else None
        
        if existing:
            cursor.execute("""
                UPDATE death_records 
                SET death_date_solar = %s, death_date_lunar = %s, death_location_id = %s, grave_location = %s
                WHERE person_id = %s
            """, (death_date_solar, death_date_lunar, death_location_id, grave_location, person_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO death_records (person_id, death_date_solar, death_date_lunar, death_location_id, grave_location)
                    VALUES (%s, %s, %s, %s, %s)
                """, (person_id, death_date_solar, death_date_lunar, death_location_id, grave_location))
        else:
            cursor.execute("""
                INSERT INTO death_records (person_id, death_date_solar, death_date_lunar, death_location_id, grave_location)
                VALUES (%s, %s, %s, %s, %s)
            """, (person_id, death_date_solar, death_date_lunar, death_location_id, grave_location))
        
        # Import personal details
        contact_info = normalize(row.get('Thông tin liên lạc', ''))
        social_media = normalize(row.get('Mạng xã hội', ''))
        occupation = normalize(row.get('Nghề nghiệp', ''))
        education = normalize(row.get('Giáo dục', ''))
        events = normalize(row.get('Sự kiện', ''))
        titles = normalize(row.get('Danh hiệu', ''))
        notes = normalize(row.get('Ghi chú', ''))
        
        if existing:
            cursor.execute("""
                UPDATE personal_details 
                SET contact_info = %s, social_media = %s, occupation = %s, 
                    education = %s, events = %s, titles = %s, notes = %s
                WHERE person_id = %s
            """, (contact_info, social_media, occupation, education, events, titles, notes, person_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO personal_details 
                    (person_id, contact_info, social_media, occupation, education, events, titles, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (person_id, contact_info, social_media, occupation, education, events, titles, notes))
        else:
            cursor.execute("""
                INSERT INTO personal_details 
                (person_id, contact_info, social_media, occupation, education, events, titles, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (person_id, contact_info, social_media, occupation, education, events, titles, notes))
    
    logger.info(f"Hoàn thành import persons: {stats['inserted']} mới, {stats['updated']} cập nhật, "
                f"{stats['duplicates_skipped']} bỏ qua (duplicate), {stats['errors']} lỗi")
    
    # VALIDATION: Kiểm tra mỗi csv_id chỉ map với 1 person_id
    duplicate_mappings = {}
    for csv_id, person_id in csv_id_to_person_id.items():
        if csv_id in duplicate_mappings:
            duplicate_mappings[csv_id].append(person_id)
        else:
            duplicate_mappings[csv_id] = [person_id]
    
    duplicates = {k: v for k, v in duplicate_mappings.items() if len(v) > 1}
    if duplicates:
        logger.error(f"LỖI: Tìm thấy {len(duplicates)} csv_id map với nhiều person_id:")
        for csv_id, person_ids in duplicates.items():
            logger.error(f"  - csv_id '{csv_id}' -> person_ids: {person_ids}")
    else:
        logger.info(f"✅ Validation: Mỗi csv_id chỉ map với 1 person_id ({len(csv_id_to_person_id)} mappings)")
    return csv_id_to_person_id

def import_relationships(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    Bước 2: Import quan hệ cha-mẹ-con
    Sử dụng logic tìm cha/mẹ theo tên + Đời
    """
    logger.info("=== BƯỚC 2: Import relationships ===")
    
    stats = {'created': 0, 'updated': 0, 'ambiguous': 0, 'errors': 0}
    
    for row in csv_data:
        csv_id = normalize(row.get('ID', ''))
        if not csv_id or csv_id not in csv_id_to_person_id:
            continue
        
        child_id = csv_id_to_person_id[csv_id]
        
        # Lấy Đời của child
        cursor.execute("""
            SELECT g.generation_number 
            FROM persons p 
            JOIN generations g ON p.generation_id = g.generation_id 
            WHERE p.person_id = %s
        """, (child_id,))
        gen_result = cursor.fetchone()
        if not gen_result:
            continue
        child_generation = gen_result[0]
        
        # Tìm cha
        # CSV có 2 cột "Tên bố" và 2 cột "Tên mẹ"
        # Cột cuối cùng (cột 31 và 32) là chính xác, có kèm "Check tên bố/mẹ"
        # Lấy tất cả keys và tìm cột "Tên bố" cuối cùng (có index cao nhất)
        row_keys = list(row.keys())
        father_name_col_idx = -1
        mother_name_col_idx = -1
        
        for i, key in enumerate(row_keys):
            if key == 'Tên bố':
                father_name_col_idx = i
            if key == 'Tên mẹ':
                mother_name_col_idx = i
        
        # Lấy giá trị từ cột cuối cùng (nếu có nhiều cột trùng tên)
        father_name = None
        mother_name = None
        
        if father_name_col_idx >= 0:
            father_name = normalize(row[row_keys[father_name_col_idx]])
        if mother_name_col_idx >= 0:
            mother_name = normalize(row[row_keys[mother_name_col_idx]])
        
        check_father = normalize(row.get('Check tên bố', ''))
        check_mother = normalize(row.get('Check tên mẹ', ''))
        
        # Lấy FM_ID của child để sử dụng trong tìm kiếm cha mẹ
        cursor.execute("SELECT fm_id FROM persons WHERE person_id = %s", (child_id,))
        fm_result = cursor.fetchone()
        child_fm_id = fm_result[0] if fm_result else None
        
        father_id = None
        if father_name and father_name != '??':
            father_id = find_parent_by_name_and_generation(
                cursor, father_name, child_generation, check_father, child_fm_id
            )
            if not father_id:
                stats['ambiguous'] += 1
        
        mother_id = None
        if mother_name and mother_name != '??':
            mother_id = find_parent_by_name_and_generation(
                cursor, mother_name, child_generation, check_mother, child_fm_id
            )
            if not mother_id:
                stats['ambiguous'] += 1
        
        # Tạo hoặc cập nhật relationship
        if father_id or mother_id:
            cursor.execute("""
                SELECT relationship_id FROM relationships WHERE child_id = %s
            """, (child_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE relationships 
                    SET father_id = %s, mother_id = %s, 
                        check_father_name = %s, check_mother_name = %s, fm_id = %s
                    WHERE relationship_id = %s
                """, (father_id, mother_id, check_father, check_mother, child_fm_id, existing[0]))
                stats['updated'] += 1
            else:
                cursor.execute("""
                    INSERT INTO relationships 
                    (child_id, father_id, mother_id, check_father_name, check_mother_name, fm_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (child_id, father_id, mother_id, check_father, check_mother, child_fm_id))
                stats['created'] += 1
        else:
            stats['errors'] += 1
    
    logger.info(f"Hoàn thành import relationships: {stats['created']} mới, {stats['updated']} cập nhật, "
                f"{stats['ambiguous']} mơ hồ, {stats['errors']} lỗi")

def find_person_by_name(cursor, name: str) -> Optional[int]:
    """
    Tìm person_id theo tên đầy đủ (giữ nguyên tiền tố)
    Returns: person_id hoặc None
    """
    if not name or name.strip() == '' or name == '??':
        return None
    
    name = name.strip()
    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (name,))
    result = cursor.fetchone()
    return result[0] if result else None

def import_marriages(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    Bước 3: Import hôn phối (vào bảng marriages_spouses)
    UPDATED FOR TBQC_FINAL.csv: Tạo quan hệ 2 chiều
    """
    logger.info("=== BƯỚC 3: Import marriages (2 chiều) ===")
    
    stats = {'created': 0, 'reverse_created': 0, 'errors': 0}
    
    for row in csv_data:
        csv_id = normalize(row.get('ID', ''))
        if not csv_id or csv_id not in csv_id_to_person_id:
            continue
        
        person_id = csv_id_to_person_id[csv_id]
        spouses_text = normalize(row.get('Thông tin hôn phối', ''))
        
        if not spouses_text:
            continue
        
        spouse_names = parse_names_list(spouses_text)
        
        for spouse_name in spouse_names:
            if not spouse_name or spouse_name == '??':
                continue
            
            # Tìm spouse trong DB
            spouse_person_id = find_person_by_name(cursor, spouse_name)
            
            # Kiểm tra đã tồn tại chưa (chiều person -> spouse)
            cursor.execute("""
                SELECT marriage_id FROM marriages_spouses 
                WHERE person_id = %s AND spouse_name = %s
            """, (person_id, spouse_name))
            
            existing = cursor.fetchone()
            marriage_id = None
            
            if not existing:
                # Tạo quan hệ person -> spouse
                cursor.execute("""
                    INSERT INTO marriages_spouses 
                    (person_id, spouse_name, spouse_person_id, is_active)
                    VALUES (%s, %s, %s, TRUE)
                """, (person_id, spouse_name, spouse_person_id))
                marriage_id = cursor.lastrowid
                stats['created'] += 1
            else:
                marriage_id = existing[0]
                # Cập nhật spouse_person_id nếu tìm thấy
                if spouse_person_id:
                    cursor.execute("""
                        UPDATE marriages_spouses 
                        SET spouse_person_id = %s 
                        WHERE marriage_id = %s
                    """, (spouse_person_id, marriage_id))
            
            # Tạo quan hệ ngược lại (spouse -> person) nếu spouse có trong DB
            if spouse_person_id:
                # Kiểm tra đã có quan hệ ngược chưa
                cursor.execute("""
                    SELECT marriage_id FROM marriages_spouses 
                    WHERE person_id = %s AND spouse_name = %s
                """, (spouse_person_id, row.get('Họ và tên', '').strip()))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO marriages_spouses 
                        (person_id, spouse_name, spouse_person_id, reverse_marriage_id, is_active)
                        VALUES (%s, %s, %s, %s, TRUE)
                    """, (spouse_person_id, row.get('Họ và tên', '').strip(), person_id, marriage_id))
                    
                    # Cập nhật reverse_marriage_id cho quan hệ gốc
                    cursor.execute("""
                        UPDATE marriages_spouses 
                        SET reverse_marriage_id = %s 
                        WHERE marriage_id = %s
                    """, (cursor.lastrowid, marriage_id))
                    
                    stats['reverse_created'] += 1
    
    logger.info(f"Hoàn thành import marriages: {stats['created']} mới, "
                f"{stats['reverse_created']} quan hệ ngược, {stats['errors']} lỗi")

def infer_in_law_relationships(cursor, csv_id_to_person_id: Dict[str, int]):
    """
    Bước 4: Suy diễn quan hệ con dâu / con rể
    ADDED IN-LAW RELATIONSHIPS
    
    Logic:
    - Với mỗi người con (có father_id và/hoặc mother_id):
      + Tìm danh sách hôn phối của người con
      + Với mỗi người hôn phối:
        * Nếu người con là con trai (Nam) → vợ là con dâu của cha/mẹ
        * Nếu người con là con gái (Nữ) → chồng là con rể của cha/mẹ
    """
    logger.info("=== BƯỚC 4: Suy diễn quan hệ con dâu / con rể ===")
    
    stats = {'con_dau': 0, 'con_re': 0, 'skipped_no_gender': 0, 'skipped_no_parent': 0, 'errors': 0}
    in_law_log = open('in_law_inference_issues.log', 'w', encoding='utf-8')
    
    # Lấy tất cả người có cha/mẹ
    cursor.execute("""
        SELECT 
            r.child_id,
            r.father_id,
            r.mother_id,
            p.gender,
            p.full_name AS child_name
        FROM relationships r
        JOIN persons p ON r.child_id = p.person_id
        WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL
    """)
    
    children_with_parents = cursor.fetchall()
    
    for child_row in children_with_parents:
        child_id = child_row[0]
        father_id = child_row[1]
        mother_id = child_row[2]
        child_gender = child_row[3]
        child_name = child_row[4]
        
        # Kiểm tra giới tính
        if not child_gender or child_gender not in ['Nam', 'Nữ']:
            in_law_log.write(
                f"BỎ QUA - Không xác định được giới tính: {child_name} (person_id={child_id})\n"
            )
            stats['skipped_no_gender'] += 1
            continue
        
        # Lấy danh sách hôn phối của người con
        cursor.execute("""
            SELECT spouse_name, spouse_person_id 
            FROM marriages_spouses 
            WHERE person_id = %s AND is_active = TRUE
        """, (child_id,))
        
        spouses = cursor.fetchall()
        
        if not spouses:
            continue
        
        # Xác định cha/mẹ cần tạo quan hệ
        parents = []
        if father_id:
            parents.append(('father', father_id))
        if mother_id:
            parents.append(('mother', mother_id))
        
        if not parents:
            stats['skipped_no_parent'] += 1
            continue
        
        for spouse_name, spouse_person_id in spouses:
            if not spouse_name or spouse_name == '??':
                continue
            
            # Xác định loại quan hệ
            if child_gender == 'Nam':
                # Con trai → vợ là con dâu
                relation_type = 'con_dau'
                stats['con_dau'] += 1
            else:  # child_gender == 'Nữ'
                # Con gái → chồng là con rể
                relation_type = 'con_re'
                stats['con_re'] += 1
            
            # Tạo quan hệ cho từng cha/mẹ
            for parent_role, parent_id in parents:
                # Kiểm tra đã tồn tại chưa (theo unique constraint: parent_id, child_id, relation_type)
                cursor.execute("""
                    SELECT in_law_id FROM in_law_relationships 
                    WHERE parent_id = %s AND child_id = %s AND relation_type = %s
                """, (parent_id, child_id, relation_type))
                
                existing = cursor.fetchone()
                if existing:
                    # Đã tồn tại, có thể update in_law_person_id nếu chưa có
                    if spouse_person_id:
                        cursor.execute("""
                            UPDATE in_law_relationships 
                            SET in_law_person_id = %s, in_law_name = %s
                            WHERE parent_id = %s AND child_id = %s AND relation_type = %s
                            AND in_law_person_id IS NULL
                        """, (spouse_person_id, spouse_name, parent_id, child_id, relation_type))
                    # Nếu đã có in_law_person_id, bỏ qua (tránh ghi đè)
                else:
                    # Chưa tồn tại, insert mới
                    try:
                        cursor.execute("""
                            INSERT INTO in_law_relationships 
                            (parent_id, in_law_person_id, in_law_name, child_id, relation_type)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (parent_id, spouse_person_id, spouse_name, child_id, relation_type))
                    except Error as e:
                        if e.errno == 1062:  # Duplicate entry
                            logger.warning(f"Duplicate in-law relationship: parent_id={parent_id}, child_id={child_id}, relation_type={relation_type}")
                            stats['errors'] += 1
                        else:
                            raise
    
    in_law_log.close()
    logger.info(f"Hoàn thành suy diễn in-law: {stats['con_dau']} con dâu, {stats['con_re']} con rể, "
                f"{stats['skipped_no_gender']} bỏ qua (không có giới tính), "
                f"{stats['skipped_no_parent']} bỏ qua (không có cha/mẹ), {stats['errors']} lỗi")

def import_siblings_and_children(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    Bước 5: Import quan hệ anh chị em và con cái
    UPDATED FOR TBQC_FINAL.csv
    """
    logger.info("=== BƯỚC 5: Import siblings and children ===")
    
    stats = {'siblings': 0, 'children': 0, 'errors': 0}
    
    for row in csv_data:
        csv_id = normalize(row.get('ID', ''))
        if not csv_id or csv_id not in csv_id_to_person_id:
            continue
        
        person_id = csv_id_to_person_id[csv_id]
        
        # Import anh chị em
        siblings_text = normalize(row.get('Thông tin anh chị em', ''))
        if siblings_text:
            sibling_names = parse_names_list(siblings_text)
            for sibling_name in sibling_names:
                if not sibling_name or sibling_name == '??':
                    continue
                
                sibling_person_id = find_person_by_name(cursor, sibling_name)
                
                # Kiểm tra đã tồn tại chưa (quan hệ 1 chiều, sẽ tự động tạo ngược lại nếu cần)
                cursor.execute("""
                    SELECT sibling_id FROM sibling_relationships 
                    WHERE person_id = %s AND (sibling_person_id = %s OR sibling_name = %s)
                """, (person_id, sibling_person_id, sibling_name))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO sibling_relationships 
                        (person_id, sibling_person_id, sibling_name, relation_type)
                        VALUES (%s, %s, %s, 'khac')
                    """, (person_id, sibling_person_id, sibling_name))
                    stats['siblings'] += 1
        
        # Import con cái (đã được xử lý ở Bước 2 qua relationships, nhưng có thể bổ sung từ cột "Thông tin con cái")
        children_text = normalize(row.get('Thông tin con cái', ''))
        if children_text:
            # Ghi chú: Quan hệ con cái chính đã được tạo ở Bước 2 (relationships)
            # Cột này có thể dùng để validate hoặc bổ sung thông tin
            children_names = parse_names_list(children_text)
            stats['children'] += len(children_names)
    
        logger.info(f"Hoàn thành import siblings/children: {stats['siblings']} anh/chị/em, "
                f"{stats['children']} con (đã được xử lý ở Bước 2), {stats['errors']} lỗi")

def populate_parent_fields_in_persons(cursor):
    """
    Bước 6: Populate father_id, mother_id, father_name, mother_name vào bảng persons
    từ dữ liệu trong relationships
    """
    logger.info("=== BƯỚC 6: Populate parent fields vào persons ===")
    
    stats = {'updated_ids': 0, 'updated_names': 0}
    
    # Bước 6.1: Cập nhật father_id và mother_id từ relationships
    cursor.execute("""
        UPDATE persons p
        INNER JOIN relationships r ON p.person_id = r.child_id
        SET 
            p.father_id = r.father_id,
            p.mother_id = r.mother_id
        WHERE r.father_id IS NOT NULL OR r.mother_id IS NOT NULL
    """)
    stats['updated_ids'] = cursor.rowcount
    logger.info(f"Đã cập nhật {stats['updated_ids']} persons với father_id/mother_id từ relationships")
    
    # Bước 6.2: Cập nhật father_name và mother_name từ persons (dựa trên father_id/mother_id)
    cursor.execute("""
        UPDATE persons p
        LEFT JOIN persons father ON p.father_id = father.person_id
        LEFT JOIN persons mother ON p.mother_id = mother.person_id
        SET 
            p.father_name = father.full_name,
            p.mother_name = mother.full_name
        WHERE p.father_id IS NOT NULL OR p.mother_id IS NOT NULL
    """)
    stats['updated_names'] = cursor.rowcount
    logger.info(f"Đã cập nhật {stats['updated_names']} persons với father_name/mother_name từ persons")
    
    return stats

# =====================================================
# MAIN
# =====================================================

def main():
    """Hàm chính"""
    logger.info("Bắt đầu import TBQC_FINAL.csv")
    
    # Đọc CSV
    csv_data = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        logger.info(f"Đọc được {len(csv_data)} dòng từ {CSV_FILE}")
    except Exception as e:
        logger.error(f"Lỗi đọc CSV: {e}")
        return
    
    # Kết nối database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("Kết nối database thành công")
    except Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
        return
    
    try:
        # Bước 1: Import persons
        csv_id_to_person_id = import_persons(cursor, csv_data)
        conn.commit()
        
        # Bước 2: Import relationships
        import_relationships(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        
        # Bước 3: Import marriages (2 chiều)
        import_marriages(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        
        # Bước 4: Suy diễn quan hệ con dâu / con rể
        infer_in_law_relationships(cursor, csv_id_to_person_id)
        conn.commit()
        
        # Bước 5: Import siblings and children
        import_siblings_and_children(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        
        # Bước 6: Populate parent fields vào persons table
        populate_parent_fields_in_persons(cursor)
        conn.commit()
        
        logger.info("Hoàn thành import!")
        
        # Tổng kết
        logger.info("\n" + "="*80)
        logger.info("TỔNG KẾT IMPORT:")
        logger.info(f"  - Persons: {len(csv_id_to_person_id)} người")
        cursor.execute("SELECT COUNT(*) FROM relationships")
        logger.info(f"  - Relationships: {cursor.fetchone()[0]} quan hệ cha/mẹ-con")
        cursor.execute("SELECT COUNT(*) FROM marriages_spouses WHERE is_active = TRUE")
        logger.info(f"  - Marriages: {cursor.fetchone()[0]} quan hệ hôn phối")
        cursor.execute("SELECT COUNT(*) FROM in_law_relationships")
        logger.info(f"  - In-laws: {cursor.fetchone()[0]} quan hệ con dâu/con rể")
        cursor.execute("SELECT COUNT(*) FROM sibling_relationships")
        logger.info(f"  - Siblings: {cursor.fetchone()[0]} quan hệ anh/chị/em")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình import: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        ambiguous_log.close()
        logger.info("Đóng kết nối database")

if __name__ == '__main__':
    main()

