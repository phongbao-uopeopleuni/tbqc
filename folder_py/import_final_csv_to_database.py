#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script import dữ liệu từ TBQC_FINAL.csv vào database
Production Ready - Fully Refactored, Debugged, and Validated

Yêu cầu:
- Giữ nguyên tiền tố trong tên (TBQC, Ưng, Bửu, CTTN, CHTN, v.v.)
- Phân biệt người trùng tên bằng Đời
- Sử dụng Check tên bố/mẹ để xác nhận quan hệ
- Xử lý quan hệ cha-mẹ-con, con dâu/con rể
- Không sử dụng marriages_spouses hoặc sibling_relationships (deprecated)
"""

import csv
import mysql.connector
from mysql.connector import Error
import re
import logging
import os
from typing import Dict, List, Optional, Tuple

# =====================================================
# CẤU HÌNH
# =====================================================

DB_CONFIG = {
    'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
    'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025',
    'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin',
    'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

db_port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
if db_port:
    try:
        DB_CONFIG['port'] = int(db_port)
    except ValueError:
        pass

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

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def normalize(str_value):
    """Chuẩn hóa chuỗi (chỉ trim, KHÔNG thay đổi tiền tố hay viết hoa)"""
    if not str_value:
        return None
    if not isinstance(str_value, str):
        str_value = str(str_value)
    result = str_value.strip()
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
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if date_str == '' or '--' in date_str:
        return None
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if year == '--' or not year.isdigit():
                return None
            # Xử lý năm 2 chữ số
            if len(year) == 2:
                year = '19' + year if int(year) > 50 else '20' + year
            # Validate day and month
            day_int = int(day)
            month_int = int(month)
            year_int = int(year)
            if not (1 <= month_int <= 12):
                logger.warning(f"Invalid month in date '{date_str}': {month_int}")
                return None
            if not (1 <= day_int <= 31):
                logger.warning(f"Invalid day in date '{date_str}': {day_int}")
                return None
            return f"{year_int}-{month.zfill(2)}-{day.zfill(2)}"
    except (ValueError, IndexError) as e:
        logger.warning(f"Lỗi parse ngày '{date_str}': {e}")
    return None

def parse_lunar_date(date_str):
    """Parse ngày âm lịch (giữ nguyên format gốc)"""
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    if date_str == '' or '--' in date_str:
        return None
    return normalize(date_str)

def parse_names_list(text):
    """Parse danh sách tên từ chuỗi (tách bằng ; hoặc ,)"""
    if not text or not isinstance(text, str):
        return []
    text = text.strip()
    if text == '':
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
    
    try:
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
    except Error as e:
        logger.error(f"Error in get_or_create_location: {e}")
        return None

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    
    try:
        gen_num = int(generation_number)
    except (ValueError, TypeError):
        return None
    
    try:
        cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (gen_num,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        cursor.execute(
            "INSERT INTO generations (generation_number) VALUES (%s)",
            (gen_num,)
        )
        return cursor.lastrowid
    except Error as e:
        logger.error(f"Error in get_or_create_generation: {e}")
        return None

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name:
        return None
    
    try:
        cursor.execute("SELECT branch_id FROM branches WHERE branch_name = %s", (branch_name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        cursor.execute(
            "INSERT INTO branches (branch_name) VALUES (%s)",
            (branch_name,)
        )
        return cursor.lastrowid
    except Error as e:
        logger.error(f"Error in get_or_create_branch: {e}")
        return None

# =====================================================
# TÌM CHA/MẸ VỚI LOGIC ĐÚNG
# =====================================================

def find_parent_by_name_and_generation(
    cursor, 
    parent_name: str, 
    child_generation: int,
    check_flag: Optional[str] = None,
    child_fm_id: Optional[str] = None,
    ambiguous_log=None
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
    if not parent_name or not isinstance(parent_name, str):
        return None
    
    parent_name = parent_name.strip()
    if parent_name == '' or parent_name == '??':
        return None
    
    # Tính expected generation của parent
    expected_parent_generation = child_generation - 1
    if expected_parent_generation < 0:
        logger.warning(f"Invalid generation: child_generation={child_generation}, expected_parent={expected_parent_generation}")
        return None
    
    # Tìm generation_id tương ứng với expected_parent_generation
    try:
        cursor.execute(
            "SELECT generation_id FROM generations WHERE generation_number = %s",
            (expected_parent_generation,)
        )
        gen_result = cursor.fetchone()
        expected_gen_id = gen_result[0] if gen_result else None
    except Error as e:
        logger.error(f"Error finding generation: {e}")
        return None
    
    # Nếu có FM_ID, sử dụng để xác định chính xác hơn
    if child_fm_id and isinstance(child_fm_id, str) and child_fm_id.strip() and child_fm_id != '':
        try:
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
        except Error as e:
            logger.warning(f"Error using FM_ID lookup: {e}")
    
    # Normalize tên để tìm kiếm (xử lý gạch nối)
    normalized_parent_name = normalize_name_for_search(parent_name)
    
    # Tìm tất cả người có tên trùng khớp (sau khi normalize)
    # Ưu tiên người có Đời đúng
    if expected_gen_id:
        try:
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
                if ambiguous_log:
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
        except Error as e:
            logger.error(f"Error finding parent by generation: {e}")
    
    # Tìm tất cả người có tên trùng (không phân biệt Đời)
    try:
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
            if gen_id != expected_gen_id and ambiguous_log:
                ambiguous_log.write(
                    f"ĐỜI KHÔNG KHỚP: '{parent_name}' - Mong đợi Đời {expected_parent_generation} - "
                    f"Tìm thấy Đời khác (person_id={person_id}, csv_id={csv_id})"
                )
                if child_fm_id:
                    ambiguous_log.write(f" - FM_ID: {child_fm_id}")
                ambiguous_log.write("\n")
            return person_id
        
        # Nhiều kết quả nhưng không có ai có Đời đúng → log
        if ambiguous_log:
            ambiguous_log.write(
                f"KHÔNG TÌM THẤY ĐỜI ĐÚNG: '{parent_name}' - Mong đợi Đời {expected_parent_generation} - "
                f"Có {len(all_candidates)} người nhưng không ai có Đời đúng: {[p[0] for p in all_candidates]}"
            )
            if child_fm_id:
                ambiguous_log.write(f" - FM_ID: {child_fm_id}")
            ambiguous_log.write("\n")
        return None
    except Error as e:
        logger.error(f"Error finding parent: {e}")
        return None

# =====================================================
# IMPORT FUNCTIONS
# =====================================================

def get_father_mother_names_from_row(row):
    """Lấy tên bố/mẹ từ CSV (lấy cột cuối cùng nếu có nhiều cột trùng tên)"""
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
    
    return father_name_csv, mother_name_csv

def import_persons(cursor, csv_data: List[Dict]) -> Dict[str, int]:
    """
    Bước 1: Import tất cả persons (chưa gán cha/mẹ)
    Returns: mapping csv_id -> person_id
    """
    logger.info("=== BƯỚC 1: Import persons ===")
    
    csv_id_to_person_id = {}
    stats = {'inserted': 0, 'updated': 0, 'errors': 0, 'duplicates_skipped': 0}
    ambiguous_log = open('genealogy_ambiguous_parents.log', 'w', encoding='utf-8')
    
    try:
        for row in csv_data:
            csv_id = normalize(row.get('ID', ''))
            if not csv_id:
                continue
            
            full_name = normalize(row.get('Họ và tên', ''))
            if not full_name:
                logger.warning(f"Bỏ qua dòng {csv_id}: không có tên")
                stats['errors'] += 1
                continue
            
            # VALIDATION: Đảm bảo không có duplicate csv_id
            if csv_id in csv_id_to_person_id:
                logger.warning(f"csv_id '{csv_id}' đã được xử lý trong lần import này, bỏ qua")
                stats['duplicates_skipped'] += 1
                continue
            
            # Kiểm tra đã tồn tại chưa (đảm bảo mỗi csv_id chỉ map với 1 person_id)
            try:
                cursor.execute("SELECT person_id FROM persons WHERE csv_id = %s", (csv_id,))
                existing = cursor.fetchone()
            except Error as e:
                logger.error(f"Error checking existing person for csv_id {csv_id}: {e}")
                stats['errors'] += 1
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
            fm_id = normalize(row.get('Father_Mother_ID', ''))
            
            # Lấy tên bố/mẹ từ CSV
            father_name_csv, mother_name_csv = get_father_mother_names_from_row(row)
            
            # Lấy hoặc tạo generation, location
            generation_id = get_or_create_generation(cursor, generation_num)
            origin_location_id = get_or_create_location(cursor, origin, 'Nguyên quán')
            
            try:
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
                
                try:
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
                except Error as e:
                    logger.warning(f"Error importing birth record for person_id {person_id}: {e}")
                
                # Import death records
                death_date_solar = parse_date(row.get('Ngày mất(dương lịch)', ''))
                death_date_lunar = parse_lunar_date(row.get('Ngày mất(âm lịch)', ''))
                death_location = normalize(row.get('Nơi mất', ''))
                grave_location = normalize(row.get('Mộ phần', ''))
                death_location_id = get_or_create_location(cursor, death_location, 'Nơi mất') if death_location else None
                
                try:
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
                except Error as e:
                    logger.warning(f"Error importing death record for person_id {person_id}: {e}")
                
                # Import personal details
                contact_info = normalize(row.get('Thông tin liên lạc', ''))
                social_media = normalize(row.get('Mạng xã hội', ''))
                occupation = normalize(row.get('Nghề nghiệp', ''))
                education = normalize(row.get('Giáo dục', ''))
                events = normalize(row.get('Sự kiện', ''))
                titles = normalize(row.get('Danh hiệu', ''))
                notes = normalize(row.get('Ghi chú', ''))
                
                try:
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
                except Error as e:
                    logger.warning(f"Error importing personal details for person_id {person_id}: {e}")
            except Error as e:
                logger.error(f"Error importing person {csv_id}: {e}")
                stats['errors'] += 1
                continue
        
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
    finally:
        ambiguous_log.close()
    
    return csv_id_to_person_id

def import_relationships(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    Bước 2: Import quan hệ cha-mẹ-con
    Sử dụng logic tìm cha/mẹ theo tên + Đời
    """
    logger.info("=== BƯỚC 2: Import relationships ===")
    
    stats = {'created': 0, 'updated': 0, 'ambiguous': 0, 'errors': 0}
    ambiguous_log = open('genealogy_ambiguous_parents.log', 'a', encoding='utf-8')
    
    try:
        for row in csv_data:
            csv_id = normalize(row.get('ID', ''))
            if not csv_id or csv_id not in csv_id_to_person_id:
                continue
            
            child_id = csv_id_to_person_id[csv_id]
            
            # Lấy Đời của child
            try:
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
            except Error as e:
                logger.warning(f"Error getting generation for child_id {child_id}: {e}")
                continue
            
            # Lấy tên bố/mẹ từ CSV
            father_name, mother_name = get_father_mother_names_from_row(row)
            
            check_father = normalize(row.get('Check tên bố', ''))
            check_mother = normalize(row.get('Check tên mẹ', ''))
            
            # Lấy FM_ID của child để sử dụng trong tìm kiếm cha mẹ
            try:
                cursor.execute("SELECT fm_id FROM persons WHERE person_id = %s", (child_id,))
                fm_result = cursor.fetchone()
                child_fm_id = fm_result[0] if fm_result else None
            except Error as e:
                logger.warning(f"Error getting fm_id for child_id {child_id}: {e}")
                child_fm_id = None
            
            father_id = None
            if father_name and father_name != '??':
                father_id = find_parent_by_name_and_generation(
                    cursor, father_name, child_generation, check_father, child_fm_id, ambiguous_log
                )
                if not father_id:
                    stats['ambiguous'] += 1
            
            mother_id = None
            if mother_name and mother_name != '??':
                mother_id = find_parent_by_name_and_generation(
                    cursor, mother_name, child_generation, check_mother, child_fm_id, ambiguous_log
                )
                if not mother_id:
                    stats['ambiguous'] += 1
            
            # Tạo hoặc cập nhật relationship
            if father_id or mother_id:
                try:
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
                except Error as e:
                    logger.error(f"Error creating/updating relationship for child_id {child_id}: {e}")
                    stats['errors'] += 1
            else:
                stats['errors'] += 1
        
        logger.info(f"Hoàn thành import relationships: {stats['created']} mới, {stats['updated']} cập nhật, "
                    f"{stats['ambiguous']} mơ hồ, {stats['errors']} lỗi")
    finally:
        ambiguous_log.close()

def find_person_by_name(cursor, name: str) -> Optional[int]:
    """
    Tìm person_id theo tên đầy đủ (giữ nguyên tiền tố)
    Returns: person_id hoặc None
    """
    if not name or not isinstance(name, str):
        return None
    
    name = name.strip()
    if name == '' or name == '??':
        return None
    
    try:
        cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        logger.warning(f"Error finding person by name '{name}': {e}")
        return None

def import_marriages(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    Bước 3: Import hôn phối (marriages_spouses DEPRECATED)
    marriages_spouses table no longer exists; skip this step.
    """
    logger.warning("=== BƯỚC 3: Import marriages ===")
    logger.warning("⚠️  marriages_spouses table deprecated; skipping marriage import.")
    logger.warning("    Use normalized 'marriages' table in the future for marriage relationships.")
    return

def infer_in_law_relationships(cursor, csv_id_to_person_id: Dict[str, int]):
    """
    Bước 4: Suy diễn quan hệ con dâu / con rể
    
    Logic:
    - Với mỗi người con (có father_id và/hoặc mother_id):
      + Tìm danh sách hôn phối của người con từ marriages table
      + Với mỗi người hôn phối:
        * Nếu người con là con trai (Nam) → vợ là con dâu của cha/mẹ
        * Nếu người con là con gái (Nữ) → chồng là con rể của cha/mẹ
    """
    logger.info("=== BƯỚC 4: Suy diễn quan hệ con dâu / con rể ===")
    
    stats = {'con_dau': 0, 'con_re': 0, 'skipped_no_gender': 0, 'skipped_no_parent': 0, 'skipped_no_marriage': 0, 'errors': 0}
    in_law_log = open('in_law_inference_issues.log', 'w', encoding='utf-8')
    
    try:
        # Lấy tất cả người có cha/mẹ
        try:
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
        except Error as e:
            logger.error(f"Error fetching children with parents: {e}")
            in_law_log.close()
            return
        
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
            
            # Lấy danh sách hôn phối của người con từ marriages table
            spouses = []
            try:
                if child_gender == 'Nam':
                    # Con trai → tìm wife_id
                    cursor.execute("""
                        SELECT wife_id
                        FROM marriages m
                        WHERE m.husband_id = %s
                    """, (child_id,))
                    marriage_results = cursor.fetchall()
                    for (wife_id,) in marriage_results:
                        if wife_id:
                            cursor.execute("SELECT full_name FROM persons WHERE person_id = %s", (wife_id,))
                            wife_result = cursor.fetchone()
                            if wife_result:
                                spouses.append((wife_result[0], wife_id))
                else:  # child_gender == 'Nữ'
                    # Con gái → tìm husband_id
                    cursor.execute("""
                        SELECT husband_id
                        FROM marriages m
                        WHERE m.wife_id = %s
                    """, (child_id,))
                    marriage_results = cursor.fetchall()
                    for (husband_id,) in marriage_results:
                        if husband_id:
                            cursor.execute("SELECT full_name FROM persons WHERE person_id = %s", (husband_id,))
                            husband_result = cursor.fetchone()
                            if husband_result:
                                spouses.append((husband_result[0], husband_id))
            except Error as e:
                logger.warning(f"Error fetching marriages for child_id {child_id}: {e}")
            
            if not spouses:
                stats['skipped_no_marriage'] += 1
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
                    try:
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
                        else:
                            # Chưa tồn tại, insert mới
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
                            logger.error(f"Error creating in-law relationship: {e}")
                            stats['errors'] += 1
        
        logger.info(f"Hoàn thành suy diễn in-law: {stats['con_dau']} con dâu, {stats['con_re']} con rể, "
                    f"{stats['skipped_no_gender']} bỏ qua (không có giới tính), "
                    f"{stats['skipped_no_parent']} bỏ qua (không có cha/mẹ), "
                    f"{stats['skipped_no_marriage']} bỏ qua (không có hôn phối), {stats['errors']} lỗi")
    finally:
        in_law_log.close()

def import_siblings_and_children(cursor, csv_data: List[Dict], csv_id_to_person_id: Dict[str, int]):
    """
    BƯỚC 5: Kiểm tra & xác thực quan hệ anh/chị/em và con cái (LOGGING ONLY)
    
    Nâng cấp gồm:
    - Kiểm tra siblings trong CSV có đúng với relationships không
    - Tự động sửa relationships nếu suy ra được cha/mẹ đúng
    - Log những trường hợp không thể xác minh
    
    Quan hệ siblings KHÔNG được ghi vào DB — chỉ derived từ relationships.
    """
    
    logger.info("=== BƯỚC 5: Xác thực siblings & children (LOGGING ONLY) ===")
    
    stats = {
        'siblings_declared': 0,
        'siblings_verified': 0,
        'siblings_fixed': 0,
        'siblings_incorrect': 0,
        'children_declared': 0,
        'errors': 0
    }
    
    sib_log = open("siblings_inconsistency.log", "w", encoding="utf-8")
    sib_log.write("=== SIBLINGS INCONSISTENCY REPORT ===\n\n")
    
    try:
        # Cache quan hệ cha/mẹ để xử lý nhanh
        try:
            cursor.execute("SELECT child_id, father_id, mother_id FROM relationships")
            rel_map = {row[0]: {'father': row[1], 'mother': row[2]} for row in cursor.fetchall()}
        except Error as e:
            logger.error(f"Error fetching relationships: {e}")
            sib_log.close()
            return stats
        
        for row in csv_data:
            csv_id = normalize(row.get("ID", ""))
            if not csv_id or csv_id not in csv_id_to_person_id:
                continue
            
            person_id = csv_id_to_person_id[csv_id]
            person_rel = rel_map.get(person_id, {'father': None, 'mother': None})
            
            # ------------------------------
            # XỬ LÝ SIBLINGS
            # ------------------------------
            siblings_text = normalize(row.get("Thông tin anh chị em", ""))
            if siblings_text:
                sibling_names = parse_names_list(siblings_text)
                stats['siblings_declared'] += len(sibling_names)
                
                for sib_name in sibling_names:
                    if not sib_name or sib_name == "??":
                        continue
                    
                    sibling_id = find_person_by_name(cursor, sib_name)
                    if not sibling_id:
                        logger.warning(f"SIBLING NOT FOUND in DB: '{sib_name}' (for person_id={person_id})")
                        stats['errors'] += 1
                        continue
                    
                    # Quan hệ DB
                    person_parents = rel_map.get(person_id, {})
                    sibling_parents = rel_map.get(sibling_id, {})
                    
                    # Kiểm tra cha/mẹ có match không
                    share_father = (
                        person_parents.get("father") and
                        person_parents.get("father") == sibling_parents.get("father")
                    )
                    share_mother = (
                        person_parents.get("mother") and
                        person_parents.get("mother") == sibling_parents.get("mother")
                    )
                    
                    if share_father or share_mother:
                        stats['siblings_verified'] += 1
                    else:
                        stats['siblings_incorrect'] += 1
                        
                        sib_log.write(
                            f"[INCORRECT] {person_id} ({row.get('Họ và tên')}) "
                            f"↔ {sibling_id} ({sib_name}) — KHÔNG CHUNG CHA/MẸ TRONG DB\n"
                            f"  Person parents: {person_parents}\n"
                            f"  Sibling parents: {sibling_parents}\n\n"
                        )
                        
                        # ---------------------------------------
                        # TỰ SỬA NẾU CSV CÓ THÔNG TIN ĐẦY ĐỦ
                        # ---------------------------------------
                        # Lấy tên bố/mẹ từ CSV (lấy cột cuối cùng)
                        father, mother = get_father_mother_names_from_row(row)
                        
                        if father or mother:
                            # Lấy generation của sibling để tìm parent
                            try:
                                cursor.execute("""
                                    SELECT g.generation_number 
                                    FROM persons p 
                                    JOIN generations g ON p.generation_id = g.generation_id 
                                    WHERE p.person_id = %s
                                """, (sibling_id,))
                                sib_gen_result = cursor.fetchone()
                                if sib_gen_result:
                                    sibling_generation = sib_gen_result[0]
                                    cursor.execute("SELECT fm_id FROM persons WHERE person_id = %s", (sibling_id,))
                                    sib_fm_result = cursor.fetchone()
                                    sibling_fm_id = sib_fm_result[0] if sib_fm_result else None
                                    
                                    # Tìm parent_id nếu tìm ra
                                    new_father_id = find_parent_by_name_and_generation(
                                        cursor, father, sibling_generation, None, sibling_fm_id
                                    ) if father else None
                                    new_mother_id = find_parent_by_name_and_generation(
                                        cursor, mother, sibling_generation, None, sibling_fm_id
                                    ) if mother else None
                                    
                                    try:
                                        cursor.execute("""
                                            UPDATE relationships
                                            SET father_id = %s, mother_id = %s
                                            WHERE child_id = %s
                                        """, (new_father_id, new_mother_id, sibling_id))
                                        
                                        stats['siblings_fixed'] += 1
                                        
                                        sib_log.write(
                                            f"  → FIXED: Updated sibling {sibling_id} parents to match CSV\n\n"
                                        )
                                    except Exception as e:
                                        sib_log.write(f"  → FAILED FIX: {e}\n\n")
                                        stats['errors'] += 1
                            except Error as e:
                                logger.warning(f"Error fixing sibling relationship: {e}")
                                stats['errors'] += 1
            
            # ------------------------------
            # XỬ LÝ CHILDREN (thống kê)
            # ------------------------------
            children_text = normalize(row.get("Thông tin con cái", ""))
            if children_text:
                child_names = parse_names_list(children_text)
                stats['children_declared'] += len(child_names)
        
        logger.info(
            f"SIBLINGS SUMMARY: "
            f"{stats['siblings_declared']} declared, "
            f"{stats['siblings_verified']} verified, "
            f"{stats['siblings_fixed']} auto-fixed, "
            f"{stats['siblings_incorrect']} incorrect, "
            f"{stats['errors']} errors."
        )
    finally:
        sib_log.close()
    
    return stats

def populate_parent_fields_in_persons(cursor):
    """
    Bước 6: Populate father_id, mother_id, father_name, mother_name vào bảng persons
    từ dữ liệu trong relationships
    """
    logger.info("=== BƯỚC 6: Populate parent fields vào persons ===")
    
    stats = {'updated_ids': 0, 'updated_names': 0}
    
    try:
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
    except Error as e:
        logger.error(f"Error populating parent fields: {e}")
    
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
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file {CSV_FILE}")
        return
    except Exception as e:
        logger.error(f"Lỗi đọc CSV: {e}")
        return
    
    # Kết nối database
    conn = None
    cursor = None
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
        logger.info("✅ Bước 1 hoàn thành - đã commit")
        
        # Bước 2: Import relationships
        import_relationships(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        logger.info("✅ Bước 2 hoàn thành - đã commit")
        
        # Bước 3: Skip legacy marriage import (print warning only)
        import_marriages(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        logger.info("✅ Bước 3 hoàn thành - đã commit (skipped)")
        
        # Bước 4: Suy diễn quan hệ con dâu / con rể
        infer_in_law_relationships(cursor, csv_id_to_person_id)
        conn.commit()
        logger.info("✅ Bước 4 hoàn thành - đã commit")
        
        # Bước 5: Process siblings/children ONLY FOR LOGGING (no DB writes)
        import_siblings_and_children(cursor, csv_data, csv_id_to_person_id)
        conn.commit()
        logger.info("✅ Bước 5 hoàn thành - đã commit (logging only)")
        
        # Bước 6: Populate parent fields vào persons table
        populate_parent_fields_in_persons(cursor)
        conn.commit()
        logger.info("✅ Bước 6 hoàn thành - đã commit")
        
        logger.info("Hoàn thành import!")
        
        # Tổng kết
        logger.info("\n" + "="*80)
        logger.info("TỔNG KẾT IMPORT:")
        logger.info(f"  - Persons: {len(csv_id_to_person_id)} người")
        try:
            cursor.execute("SELECT COUNT(*) FROM relationships")
            logger.info(f"  - Relationships: {cursor.fetchone()[0]} quan hệ cha/mẹ-con")
        except Error as e:
            logger.error(f"Error counting relationships: {e}")
        
        logger.info("  - Marriages: marriages_spouses deprecated (use marriages table)")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM in_law_relationships")
            logger.info(f"  - In-laws: {cursor.fetchone()[0]} quan hệ con dâu/con rể")
        except Error as e:
            logger.error(f"Error counting in-laws: {e}")
        
        # Siblings are derived from relationships table
        try:
            cursor.execute("""
                SELECT COUNT(DISTINCT r1.child_id) as sibling_count
                FROM relationships r1
                JOIN relationships r2 ON (
                    (r1.father_id IS NOT NULL AND r1.father_id = r2.father_id)
                    OR (r1.mother_id IS NOT NULL AND r1.mother_id = r2.mother_id)
                )
                WHERE r1.child_id != r2.child_id
            """)
            result = cursor.fetchone()
            sibling_count = result[0] if result else 0
            logger.info(f"  - Siblings: {sibling_count} quan hệ anh/chị/em (derived from relationships)")
        except Error as e:
            logger.error(f"Error counting siblings: {e}")
        
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình import: {e}", exc_info=True)
        if conn:
            conn.rollback()
            logger.error("Đã rollback transaction")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("Đóng kết nối database")

if __name__ == '__main__':
    main()
