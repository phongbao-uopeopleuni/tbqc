#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để reset database và import lại dữ liệu từ 3 CSV chính thức:
- person.csv
- father_mother.csv
- spouse_sibling_children.csv
"""

import mysql.connector
from mysql.connector import Error
import csv
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reset_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import DB config
try:
    from folder_py.db_config import get_db_config, get_db_connection
except ImportError:
    # Fallback nếu không import được
    def get_db_config():
        return {
            'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
            'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'railway',
            'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'root',
            'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or '',
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
    def get_db_connection():
        import mysql.connector
        config = get_db_config()
        if 'port' not in config:
            port = os.environ.get('DB_PORT') or os.environ.get('MYSQLPORT')
            if port:
                try:
                    config['port'] = int(port)
                except ValueError:
                    pass
        return mysql.connector.connect(**config)


def execute_sql_file(connection, file_path: str) -> bool:
    """Chạy file SQL"""
    logger.info(f"📄 Đang chạy: {file_path}")
    try:
        if not os.path.exists(file_path):
            logger.error(f"❌ File không tồn tại: {file_path}")
            return False
        
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        cursor = connection.cursor()
        
        # Tách các câu lệnh (hỗ trợ DELIMITER)
        statements = []
        current_statement = ""
        delimiter = ";"
        
        for line in sql_content.split('\n'):
            stripped_line = line.strip()
            if stripped_line.startswith('DELIMITER'):
                delimiter = stripped_line.split()[1]
                continue
            if stripped_line and not stripped_line.startswith('--'):
                current_statement += line + "\n"
                if stripped_line.endswith(delimiter):
                    stmt = current_statement[:-len(delimiter)-1].strip()
                    if stmt:
                        statements.append(stmt)
                    current_statement = ""
        
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Chạy từng statement
        for statement in statements:
            if statement.strip() and not statement.strip().startswith('--'):
                try:
                    cursor.execute(statement)
                except Error as e:
                    error_msg = str(e)
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        logger.warning(f"  ⚠️  Bỏ qua (đã tồn tại): {error_msg[:100]}")
                    else:
                        logger.error(f"  ❌ Lỗi: {error_msg[:100]}")
                        raise
        
        connection.commit()
        logger.info(f"  ✅ Hoàn thành: {os.path.basename(file_path)}")
        return True
    except Exception as e:
        logger.error(f"  ❌ Lỗi khi chạy {file_path}: {e}")
        connection.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()


def parse_date(date_str: str) -> Optional[str]:
    """Parse date từ CSV format (dd/mm/yyyy) sang MySQL DATE format"""
    if not date_str or date_str.strip() == '':
        return None
    
    date_str = date_str.strip()
    try:
        # Format: dd/mm/yyyy hoặc dd/mm/--
        if '--' in date_str:
            return None
        
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if year == '--' or month == '--' or day == '--':
                return None
            # MySQL format: YYYY-MM-DD
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    except Exception as e:
        logger.debug(f"Không parse được date '{date_str}': {e}")
    
    return None


def import_persons(connection, csv_file: str) -> Tuple[int, Dict[str, List[str]], Dict[str, Dict]]:
    """
    Import persons từ person.csv
    Returns: (count, name_to_id_map, id_to_person_map)
    - name_to_id_map: full_name -> [person_id, ...]
    - id_to_person_map: person_id -> {full_name, father_mother_id, ...}
    """
    # Đảm bảo đường dẫn tuyệt đối
    if not os.path.isabs(csv_file):
        csv_file = os.path.abspath(csv_file)
    
    logger.info(f"\n📥 Bước 1: Import persons từ {csv_file}")
    logger.info(f"   Đường dẫn tuyệt đối: {os.path.abspath(csv_file)}")
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ File không tồn tại: {csv_file}")
        return 0, {}, {}
    
    cursor = connection.cursor()
    name_to_id_map: Dict[str, List[str]] = {}  # full_name -> [person_id, ...]
    id_to_person_map: Dict[str, Dict] = {}  # person_id -> {full_name, father_mother_id, ...}
    success_count = 0
    error_count = 0
    skipped_count = 0
    total_rows = 0
    
    try:
        # Đọc CSV với encoding utf-8-sig để xử lý BOM
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Log thông tin về CSV
            if reader.fieldnames:
                logger.info(f"   📋 Các cột trong CSV ({len(reader.fieldnames)} cột):")
                for i, col in enumerate(reader.fieldnames, 1):
                    logger.info(f"      {i}. {col}")
            else:
                logger.warning("   ⚠️  Không đọc được tên cột từ CSV")
            
            # Process từng dòng
            for idx, row in enumerate(reader, start=2):  # start=2 vì dòng 1 là header
                total_rows += 1
                try:
                    person_id = row.get('person_id', '').strip()
                    if not person_id:
                        skipped_count += 1
                        logger.debug(f"   Dòng {idx}: Bỏ qua vì không có person_id")
                        continue
                    
                    full_name = row.get('full_name', '').strip()
                    if not full_name:
                        skipped_count += 1
                        logger.warning(f"   ⚠️  Dòng {idx}: Person {person_id} không có full_name, bỏ qua")
                        continue
                    
                    # Map từ CSV columns sang database columns với validation
                    # Đảm bảo không có giá trị rỗng string, chỉ None nếu thực sự không có
                    def clean_value(val):
                        """Clean value: strip và convert empty string to None"""
                        if val is None:
                            return None
                        val_str = str(val).strip()
                        return val_str if val_str else None
                    
                    # Parse generation_level với xử lý lỗi (phải parse trước khi dùng)
                    generation_level = None
                    gen_level_str = row.get('generation_level', '').strip()
                    if gen_level_str:
                        try:
                            generation_level = int(gen_level_str)
                        except ValueError:
                            logger.warning(f"   ⚠️  Dòng {idx}: generation_level '{gen_level_str}' không phải số, set None")
                    
                    # Parse dates
                    birth_solar = parse_date(row.get('birth_solar', ''))
                    death_solar = parse_date(row.get('death_solar', ''))
                    
                    # Map từ CSV columns sang database columns
                    # CSV có: "status (sống/mất)" -> DB: "status"
                    status_value = row.get('status (sống/mất)', '').strip() or None
                    
                    # Clean các giá trị
                    alias_value = clean_value(row.get('alias', ''))
                    gender_value = clean_value(row.get('gender', ''))
                    hometown_value = clean_value(row.get('hometown', ''))
                    nationality_value = clean_value(row.get('nationality', ''))
                    religion_value = clean_value(row.get('religion', ''))
                    place_of_death_value = clean_value(row.get('place_of_death', ''))
                    grave_info_value = clean_value(row.get('grave_info', ''))
                    contact_value = clean_value(row.get('contact', ''))
                    social_value = clean_value(row.get('social', ''))
                    career_value = clean_value(row.get('career', ''))
                    education_value = clean_value(row.get('education', ''))
                    events_value = clean_value(row.get('events', ''))
                    titles_value = clean_value(row.get('titles', ''))
                    blood_type_value = clean_value(row.get('blood_type', ''))
                    genetic_disease_value = clean_value(row.get('genetic_disease', ''))
                    note_value = clean_value(row.get('note', ''))
                    father_mother_id_value = clean_value(row.get('father_mother_id', ''))
                    birth_lunar_value = clean_value(row.get('birth_lunar', ''))
                    death_lunar_value = clean_value(row.get('death_lunar', ''))
                    
                    # Build name map (có thể có nhiều người cùng tên)
                    if full_name not in name_to_id_map:
                        name_to_id_map[full_name] = []
                    name_to_id_map[full_name].append(person_id)
                    
                    # Build id_to_person_map để resolve ambiguous bằng nhiều tiêu chí
                    id_to_person_map[person_id] = {
                        'full_name': full_name,
                        'father_mother_id': father_mother_id_value,
                        'gender': gender_value,
                        'generation_level': generation_level,
                        'birth_solar': birth_solar,  # Để match khi không có father_mother_id
                        'father_name': None,  # Sẽ được cập nhật từ father_mother.csv
                        'mother_name': None   # Sẽ được cập nhật từ father_mother.csv
                    }
                    
                    # Insert person với named parameters để dễ debug
                    insert_sql = """
                        INSERT INTO persons (
                            person_id, full_name, alias, gender, status, generation_level,
                            birth_date_solar, birth_date_lunar, death_date_solar, death_date_lunar,
                            home_town, nationality, religion, place_of_death, grave_info,
                            contact, social, occupation, education, events, titles,
                            blood_type, genetic_disease, note, father_mother_id
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    
                    values = (
                        person_id,
                        full_name,
                        alias_value,
                        gender_value,
                        status_value,
                        generation_level,
                        birth_solar,
                        birth_lunar_value,
                        death_solar,
                        death_lunar_value,
                        hometown_value,  # CSV: "hometown" -> DB: "home_town"
                        nationality_value,
                        religion_value,
                        place_of_death_value,
                        grave_info_value,
                        contact_value,
                        social_value,
                        career_value,  # CSV: "career" -> DB: "occupation"
                        education_value,
                        events_value,
                        titles_value,
                        blood_type_value,
                        genetic_disease_value,
                        note_value,
                        father_mother_id_value
                    )
                    
                    # Debug log cho dòng đầu tiên
                    if success_count == 0 and idx == 2:
                        logger.info(f"   [DEBUG] Dòng đầu tiên - Sample values:")
                        logger.info(f"      person_id: {person_id}")
                        logger.info(f"      full_name: {full_name}")
                        logger.info(f"      alias: {alias_value}")
                        logger.info(f"      gender: {gender_value}")
                        logger.info(f"      status: {status_value}")
                        logger.info(f"      generation_level: {generation_level}")
                        logger.info(f"      hometown: {hometown_value}")
                    
                    # Thử insert từng dòng
                    cursor.execute(insert_sql, values)
                    success_count += 1
                    
                    # Log progress mỗi 100 dòng
                    if success_count % 100 == 0:
                        logger.info(f"   ✅ Đã import {success_count} persons...")
                    
                except Error as e:
                    error_count += 1
                    error_msg = str(e)
                    logger.error(f"   ❌ Dòng {idx}: Lỗi insert person {person_id} ({full_name})")
                    logger.error(f"      Chi tiết: {error_msg}")
                    # Không rollback, tiếp tục với dòng tiếp theo
                    continue
                except Exception as e:
                    error_count += 1
                    logger.error(f"   ❌ Dòng {idx}: Lỗi không mong đợi khi xử lý person {person_id}")
                    logger.error(f"      Chi tiết: {str(e)}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
        
        # Commit tất cả các dòng thành công
        connection.commit()
        logger.info(f"\n✅ Hoàn thành import persons:")
        logger.info(f"   ✅ Thành công: {success_count} persons")
        logger.info(f"   ❌ Lỗi: {error_count} dòng")
        logger.info(f"   ⏭️  Bỏ qua: {skipped_count} dòng")
        logger.info(f"   📊 Tổng số dòng đã xử lý: {total_rows}")
        
        if success_count == 0:
            logger.error("   ❌ KHÔNG IMPORT ĐƯỢC PERSON NÀO!")
            logger.error("   Vui lòng kiểm tra:")
            logger.error("   1. Schema bảng persons đã được tạo chưa?")
            logger.error("   2. Cấu trúc CSV có đúng không?")
            logger.error("   3. Xem log chi tiết ở trên để biết lỗi cụ thể")
            return 0, {}, {}
        
        logger.info(f"   📊 Đã build id_to_person_map với {len(id_to_person_map)} entries")
        return success_count, name_to_id_map, id_to_person_map
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi đọc CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Chỉ rollback nếu chưa commit gì cả
        if success_count == 0:
            connection.rollback()
        return 0, {}, {}
    finally:
        cursor.close()


def resolve_name_to_id(name: str, name_to_id_map: Dict[str, List[str]], 
                       person_id: str = None, context: str = "",
                       id_to_person_map: Dict[str, Dict] = None,
                       child_father_mother_id: str = None,
                       child_info: Dict = None) -> Optional[str]:
    """
    Resolve tên thành person_id với nhiều tiêu chí để xác định chính xác
    
    Khi ambiguous, resolve theo thứ tự ưu tiên:
    1. father_mother_id match
    2. father_name match (nếu đang resolve parent)
    3. birth_solar match
    4. generation_level match
    
    Args:
        name: Tên cần resolve
        name_to_id_map: Map full_name -> [person_id, ...]
        person_id: ID của person hiện tại (context)
        context: Context string (father, mother, spouse)
        id_to_person_map: Map person_id -> {full_name, father_mother_id, birth_solar, generation_level, ...}
        child_father_mother_id: father_mother_id của child (để match với parent)
        child_info: Thông tin của child {father_mother_id, birth_solar, generation_level, father_name, ...}
    
    Returns: person_id nếu tìm thấy duy nhất hoặc match được, None nếu không tìm thấy
    """
    if not name or not name.strip():
        return None
    
    name = name.strip()
    
    # Exact match
    if name in name_to_id_map:
        ids = name_to_id_map[name]
        if len(ids) == 1:
            return ids[0]
        else:
            # Ambiguous - nhiều người cùng tên
            # Resolve bằng nhiều tiêu chí theo thứ tự ưu tiên
            matched_ids = ids.copy()
            
            # Ưu tiên 1: father_mother_id match
            if id_to_person_map and child_father_mother_id:
                logger.info(f"   🔍 AMBIGUOUS: '{name}' có {len(ids)} kết quả, đang resolve...")
                logger.info(f"      Child father_mother_id: {child_father_mother_id}")
                logger.info(f"      Candidate IDs: {ids}")
                
                # Tìm person nào có cùng father_mother_id với child
                fm_matched = []
                for candidate_id in matched_ids:
                    candidate_info = id_to_person_map.get(candidate_id, {})
                    candidate_fm_id = candidate_info.get('father_mother_id', '')
                    if candidate_fm_id and candidate_fm_id == child_father_mother_id:
                        fm_matched.append(candidate_id)
                        logger.info(f"      ✅ Match (father_mother_id): {candidate_id} có fm_id = {candidate_fm_id}")
                
                if len(fm_matched) == 1:
                    logger.info(f"   ✅ Resolved: '{name}' -> {fm_matched[0]} (match bằng father_mother_id)")
                    return fm_matched[0]
                elif len(fm_matched) > 0:
                    matched_ids = fm_matched  # Tiếp tục với các match này
                    logger.info(f"      → Còn {len(matched_ids)} candidates sau khi match father_mother_id")
            
            # Ưu tiên 2: birth_solar match (parent phải lớn hơn child)
            if len(matched_ids) > 1 and child_info:
                child_birth_solar = child_info.get('birth_solar')
                if child_birth_solar:
                    birth_matched = []
                    for candidate_id in matched_ids:
                        candidate_info = id_to_person_map.get(candidate_id, {})
                        candidate_birth = candidate_info.get('birth_solar')
                        # Match nếu birth_solar hợp lý cho parent-child relationship
                        # Logic: Parent thường lớn hơn child khoảng 15-50 năm
                        if candidate_birth:
                            try:
                                from datetime import datetime
                                child_date = datetime.strptime(child_birth_solar, '%Y-%m-%d')
                                candidate_date = datetime.strptime(candidate_birth, '%Y-%m-%d')
                                age_diff = (child_date - candidate_date).days / 365.25
                                # Parent phải lớn hơn child ít nhất 15 tuổi và không quá 50 tuổi
                                if 15 <= age_diff <= 50:
                                    birth_matched.append(candidate_id)
                                    logger.info(f"      ✅ Match (birth_solar): {candidate_id} có age_diff = {age_diff:.1f} năm")
                            except Exception as e:
                                logger.debug(f"      Lỗi parse date: {e}")
                    
                    if len(birth_matched) == 1:
                        logger.info(f"   ✅ Resolved: '{name}' -> {birth_matched[0]} (match bằng birth_solar)")
                        return birth_matched[0]
                    elif len(birth_matched) > 0:
                        matched_ids = birth_matched
                        logger.info(f"      → Còn {len(matched_ids)} candidates sau khi match birth_solar")
            
            # Ưu tiên 3: generation_level match
            if len(matched_ids) > 1 and child_info:
                child_gen_level = child_info.get('generation_level')
                if child_gen_level is not None:
                    gen_matched = []
                    for candidate_id in matched_ids:
                        candidate_info = id_to_person_map.get(candidate_id, {})
                        candidate_gen = candidate_info.get('generation_level')
                        # Parent phải có generation_level nhỏ hơn child 1 level
                        if candidate_gen is not None and candidate_gen == child_gen_level - 1:
                            gen_matched.append(candidate_id)
                            logger.info(f"      ✅ Match (generation_level): {candidate_id} có gen = {candidate_gen}")
                    
                    if len(gen_matched) == 1:
                        logger.info(f"   ✅ Resolved: '{name}' -> {gen_matched[0]} (match bằng generation_level)")
                        return gen_matched[0]
                    elif len(gen_matched) > 0:
                        matched_ids = gen_matched
                        logger.info(f"      → Còn {len(matched_ids)} candidates sau khi match generation_level")
            
            # Nếu vẫn không resolve được
            logger.warning(f"⚠️  AMBIGUOUS: '{name}' có {len(ids)} kết quả, không resolve được (context: {context}, person: {person_id})")
            logger.warning(f"    Final candidate IDs: {matched_ids}")
            if child_father_mother_id:
                logger.warning(f"    Child father_mother_id: {child_father_mother_id}")
            return None
    
    # Try partial match (tên có thể có thêm prefix/suffix)
    matches = []
    for full_name, ids in name_to_id_map.items():
        if name in full_name or full_name in name:
            matches.extend(ids)
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        # Áp dụng cùng logic resolve như exact match
        # Recursive call với matches thay vì ids
        temp_name_map = {name: matches}
        return resolve_name_to_id(
            name, temp_name_map, person_id, context,
            id_to_person_map, child_father_mother_id, child_info
        )
    
    # Not found
    logger.warning(f"⚠️  NOT FOUND: '{name}' (context: {context}, person: {person_id})")
    return None


def import_parent_relationships(connection, csv_file: str, name_to_id_map: Dict[str, List[str]], 
                                id_to_person_map: Dict[str, Dict]) -> Tuple[int, int, int]:
    """
    Import parent relationships từ father_mother.csv
    Sử dụng father_mother_id để resolve ambiguous cases
    
    Returns: (father_links, mother_links, ambiguous_count)
    """
    logger.info(f"\n📥 Bước 2: Import parent relationships từ {csv_file}")
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ File không tồn tại: {csv_file}")
        return 0, 0, 0
    
    cursor = connection.cursor()
    father_links = 0
    mother_links = 0
    ambiguous_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                child_id = row.get('person_id', '').strip()
                if not child_id:
                    continue
                
                # Lấy thông tin của child để resolve ambiguous
                child_info = id_to_person_map.get(child_id, {}).copy()
                child_father_mother_id = child_info.get('father_mother_id', '')
                
                father_name = row.get('father_name', '').strip()
                mother_name = row.get('mother_name', '').strip()
                
                # Cập nhật child_info với father_name và mother_name từ CSV
                child_info['father_name'] = father_name
                child_info['mother_name'] = mother_name
                
                # Resolve father
                if father_name:
                    father_id = resolve_name_to_id(
                        father_name, 
                        name_to_id_map, 
                        child_id, 
                        "father",
                        id_to_person_map=id_to_person_map,
                        child_father_mother_id=child_father_mother_id,
                        child_info=child_info
                    )
                    if father_id:
                        try:
                            insert_sql = """
                                INSERT INTO relationships (parent_id, child_id, relation_type)
                                VALUES (%s, %s, 'father')
                                ON DUPLICATE KEY UPDATE relation_type = 'father'
                            """
                            cursor.execute(insert_sql, (father_id, child_id))
                            father_links += 1
                        except Error as e:
                            logger.error(f"❌ Lỗi insert father relationship: {e}")
                    else:
                        ambiguous_count += 1
                
                # Resolve mother
                if mother_name:
                    mother_id = resolve_name_to_id(
                        mother_name, 
                        name_to_id_map, 
                        child_id, 
                        "mother",
                        id_to_person_map=id_to_person_map,
                        child_father_mother_id=child_father_mother_id,
                        child_info=child_info
                    )
                    if mother_id:
                        try:
                            insert_sql = """
                                INSERT INTO relationships (parent_id, child_id, relation_type)
                                VALUES (%s, %s, 'mother')
                                ON DUPLICATE KEY UPDATE relation_type = 'mother'
                            """
                            cursor.execute(insert_sql, (mother_id, child_id))
                            mother_links += 1
                        except Error as e:
                            logger.error(f"❌ Lỗi insert mother relationship: {e}")
                    else:
                        ambiguous_count += 1
        
        connection.commit()
        logger.info(f"✅ Đã link {father_links} fathers và {mother_links} mothers")
        logger.info(f"⚠️  Có {ambiguous_count} trường hợp ambiguous/not found")
        
        return father_links, mother_links, ambiguous_count
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi import parent relationships: {e}")
        connection.rollback()
        return 0, 0, 0
    finally:
        cursor.close()


def parse_spouse_names(spouse_str: str) -> List[str]:
    """Parse spouse names từ CSV (có thể phân tách bằng ; hoặc ,)"""
    if not spouse_str or not spouse_str.strip():
        return []
    
    # Split by ; or ,
    names = []
    for delimiter in [';', ',']:
        if delimiter in spouse_str:
            names = [n.strip() for n in spouse_str.split(delimiter)]
            break
    
    if not names:
        names = [spouse_str.strip()]
    
    # Filter empty
    return [n for n in names if n]


def import_marriages(connection, csv_file: str, name_to_id_map: Dict[str, List[str]], 
                     id_to_person_map: Dict[str, Dict]) -> Tuple[int, int]:
    """
    Import marriages từ spouse_sibling_children.csv
    Sử dụng father_mother_id để resolve ambiguous cases nếu có
    
    Returns: (marriages_count, ambiguous_count)
    """
    logger.info(f"\n📥 Bước 3: Import marriages từ {csv_file}")
    
    if not os.path.exists(csv_file):
        logger.error(f"❌ File không tồn tại: {csv_file}")
        return 0, 0
    
    cursor = connection.cursor()
    marriages_count = 0
    ambiguous_count = 0
    processed_pairs = set()  # Để tránh duplicate
    
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                person_id = row.get('person_id', '').strip()
                if not person_id:
                    continue
                
                # Lấy father_mother_id của person để resolve ambiguous (nếu cần)
                person_info = id_to_person_map.get(person_id, {})
                person_father_mother_id = person_info.get('father_mother_id', '')
                
                spouse_names_str = row.get('spouse_name', '').strip()
                if not spouse_names_str:
                    continue
                
                # Parse spouse names
                spouse_names = parse_spouse_names(spouse_names_str)
                
                for spouse_name in spouse_names:
                    # Với marriages, không có father_mother_id để match trực tiếp
                    # Nhưng vẫn truyền id_to_person_map để có thể dùng trong tương lai
                    spouse_id = resolve_name_to_id(
                        spouse_name, 
                        name_to_id_map, 
                        person_id, 
                        "spouse",
                        id_to_person_map=id_to_person_map,
                        child_father_mother_id=None  # Không áp dụng cho marriages
                    )
                    
                    if spouse_id:
                        # Tạo pair key để tránh duplicate (theo cả 2 chiều)
                        pair_key1 = (person_id, spouse_id)
                        pair_key2 = (spouse_id, person_id)
                        
                        if pair_key1 in processed_pairs or pair_key2 in processed_pairs:
                            continue
                        
                        try:
                            insert_sql = """
                                INSERT INTO marriages (person_id, spouse_person_id, status)
                                VALUES (%s, %s, 'Đang kết hôn')
                                ON DUPLICATE KEY UPDATE status = 'Đang kết hôn'
                            """
                            cursor.execute(insert_sql, (person_id, spouse_id))
                            processed_pairs.add(pair_key1)
                            marriages_count += 1
                        except Error as e:
                            logger.error(f"❌ Lỗi insert marriage: {e}")
                    else:
                        ambiguous_count += 1
        
        connection.commit()
        logger.info(f"✅ Đã import {marriages_count} marriages")
        logger.info(f"⚠️  Có {ambiguous_count} trường hợp ambiguous/not found")
        
        return marriages_count, ambiguous_count
        
    except Exception as e:
        logger.error(f"❌ Lỗi khi import marriages: {e}")
        connection.rollback()
        return 0, 0
    finally:
        cursor.close()


def main():
    """Hàm chính"""
    print("="*80)
    print("🔄 RESET DATABASE VÀ IMPORT TỪ 3 CSV CHÍNH THỨC")
    print("="*80)
    
    # Get DB config
    db_config = get_db_config()
    logger.info(f"📊 Database: {db_config.get('database')} @ {db_config.get('host')}")
    
    # Kết nối database
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("❌ Không thể kết nối database")
            return
        logger.info("✅ Kết nối database thành công")
    except Error as e:
        logger.error(f"❌ Lỗi kết nối database: {e}")
        return
    
    try:
        # Bước 0: Drop các bảng cũ (nếu có)
        logger.info("\n" + "="*80)
        logger.info("🗑️  Bước 0: Drop các bảng cũ (nếu có)")
        logger.info("="*80)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        drop_file = os.path.join(base_dir, 'folder_sql', 'drop_old_tables.sql')
        if os.path.exists(drop_file):
            logger.info(f"   📄 Chạy: {drop_file}")
            if not execute_sql_file(conn, drop_file):
                logger.warning("⚠️  Có lỗi khi drop bảng cũ, tiếp tục...")
            else:
                logger.info("   ✅ Đã drop các bảng cũ thành công")
        else:
            logger.warning("   ⚠️  Không tìm thấy drop_old_tables.sql, bỏ qua")
        
        # Bước 0.5: Kiểm tra và thêm cột alias nếu thiếu (fallback)
        logger.info("\n" + "="*80)
        logger.info("🔍 Bước 0.5: Kiểm tra schema và thêm cột alias nếu thiếu")
        logger.info("="*80)
        
        try:
            cursor = conn.cursor()
            # Check if alias column exists
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                  AND TABLE_NAME = 'persons' 
                  AND COLUMN_NAME = 'alias'
            """)
            result = cursor.fetchone()
            has_alias = result[0] > 0 if result else False
            
            if not has_alias:
                logger.warning("   ⚠️  Cột alias không tồn tại, đang thêm...")
                try:
                    cursor.execute("ALTER TABLE persons ADD COLUMN alias TEXT AFTER full_name")
                    conn.commit()
                    logger.info("   ✅ Đã thêm cột alias thành công")
                except Error as e:
                    error_msg = str(e)
                    if 'Duplicate column name' in error_msg:
                        logger.info("   ℹ️  Cột alias đã tồn tại")
                    else:
                        logger.warning(f"   ⚠️  Không thể thêm cột alias: {e}")
            else:
                logger.info("   ✅ Cột alias đã tồn tại")
            cursor.close()
        except Exception as e:
            logger.warning(f"   ⚠️  Lỗi khi kiểm tra schema: {e}")
        
        # Bước 1: Chạy reset schema
        logger.info("\n" + "="*80)
        logger.info("📋 Bước 1: Reset schema")
        logger.info("="*80)
        
        schema_file = os.path.join(base_dir, 'folder_sql', 'reset_schema_tbqc.sql')
        logger.info(f"   📄 Chạy: {schema_file}")
        if not execute_sql_file(conn, schema_file):
            logger.error("❌ Dừng lại do lỗi ở reset_schema_tbqc.sql")
            return
        logger.info("   ✅ Schema đã được tạo/cập nhật")
        
        # Bước 2: Reset data (truncate tables)
        logger.info("\n" + "="*80)
        logger.info("🗑️  Bước 2: Reset data (truncate tables)")
        logger.info("="*80)
        
        reset_file = os.path.join(base_dir, 'folder_sql', 'reset_tbqc_tables.sql')
        if not execute_sql_file(conn, reset_file):
            logger.error("❌ Dừng lại do lỗi ở reset_tbqc_tables.sql")
            return
        
        # Bước 3: Import persons
        logger.info("\n" + "="*80)
        logger.info("📥 Bước 3: Import persons")
        logger.info("="*80)
        
        # Đảm bảo đường dẫn CSV là tuyệt đối
        person_csv = os.path.abspath(os.path.join(base_dir, 'person.csv'))
        logger.info(f"📄 Đường dẫn person.csv: {person_csv}")
        persons_count, name_to_id_map, id_to_person_map = import_persons(conn, person_csv)
        
        if persons_count == 0:
            logger.error("❌ Không import được persons, dừng lại")
            logger.error("   Vui lòng kiểm tra:")
            logger.error(f"   1. File CSV có tồn tại tại: {person_csv}")
            logger.error("   2. Schema đã được tạo chưa?")
            logger.error("   3. Xem log chi tiết ở trên để biết lỗi cụ thể")
            return
        
        # Bước 4: Import parent relationships
        logger.info("\n" + "="*80)
        logger.info("📥 Bước 4: Import parent relationships")
        logger.info("="*80)
        
        father_mother_csv = os.path.abspath(os.path.join(base_dir, 'father_mother.csv'))
        logger.info(f"📄 Đường dẫn father_mother.csv: {father_mother_csv}")
        father_links, mother_links, ambiguous_parents = import_parent_relationships(
            conn, father_mother_csv, name_to_id_map, id_to_person_map
        )
        
        # Bước 5: Import marriages
        logger.info("\n" + "="*80)
        logger.info("📥 Bước 5: Import marriages")
        logger.info("="*80)
        
        spouse_csv = os.path.abspath(os.path.join(base_dir, 'spouse_sibling_children.csv'))
        logger.info(f"📄 Đường dẫn spouse_sibling_children.csv: {spouse_csv}")
        marriages_count, ambiguous_spouses = import_marriages(conn, spouse_csv, name_to_id_map, id_to_person_map)
        
        # Bước 6: Update views and procedures
        logger.info("\n" + "="*80)
        logger.info("📋 Bước 6: Update views và stored procedures")
        logger.info("="*80)
        
        views_file = os.path.join(base_dir, 'folder_sql', 'update_views_procedures_tbqc.sql')
        execute_sql_file(conn, views_file)  # Không dừng nếu lỗi ở đây
        
        # Summary
        print("\n" + "="*80)
        print("✅ HOÀN THÀNH IMPORT!")
        print("="*80)
        print(f"\n📊 THỐNG KÊ:")
        print(f"   Persons imported: {persons_count}")
        print(f"   Father links: {father_links}")
        print(f"   Mother links: {mother_links}")
        print(f"   Marriages imported: {marriages_count}")
        print(f"   Ambiguous parent cases: {ambiguous_parents}")
        print(f"   Ambiguous spouse cases: {ambiguous_spouses}")
        print("\n📝 Log chi tiết được ghi vào: reset_import.log")
        print("="*80)
        
    except Exception as e:
        logger.error(f"❌ Lỗi: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
    finally:
        if conn.is_connected():
            conn.close()
            logger.info("✅ Đã đóng kết nối database")


if __name__ == '__main__':
    main()
