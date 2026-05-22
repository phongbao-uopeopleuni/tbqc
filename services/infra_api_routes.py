import logging
import os
import secrets
import traceback

import mysql.connector
from flask import jsonify, request

from config import is_production_env
from db import DB_CONFIG, get_db_config, get_db_connection

logger = logging.getLogger(__name__)


def _health_detail_authorized():
    """Day du chi tiet /api/health khi dat HEALTH_DETAIL_SECRET va gui dung header."""
    secret = (os.environ.get('HEALTH_DETAIL_SECRET') or '').strip()
    if not secret:
        return False
    key = (request.headers.get('X-Health-Detail-Key') or '').strip()
    return bool(key) and secrets.compare_digest(key, secret)


def _public_health_payload(full: dict) -> dict:
    """Ban health cong khai: khong lo host DB, user, port, loi noi bo chi tiet."""
    out = {
        'server': full.get('server', 'ok'),
        'database': full.get('database', 'unknown'),
        'blueprints_registered': full.get('blueprints_registered', True),
        'stats': full.get('stats', {'persons_count': 0, 'relationships_count': 0}),
    }
    if full.get('database', '').startswith('error:'):
        out['database'] = 'error'
    return out


def _resolve_blueprints_error(blueprints_error):
    if callable(blueprints_error):
        return blueprints_error()
    return blueprints_error


def register_health_route(app, blueprints_error=None):
    @app.route('/api/health', methods=['GET'])
    def api_health():
        """API kiem tra health cua server va database. Hien thi loi ket noi chi tiet neu that bai."""
        try:
            # Uu tien DB_CONFIG da load luc khoi dong (tranh request thay localhost)
            cfg = DB_CONFIG if (DB_CONFIG.get('host') and DB_CONFIG.get('host') != 'localhost') else get_db_config()
            current_blueprints_error = _resolve_blueprints_error(blueprints_error)
            health_status = {
                'server': 'ok',
                'blueprints_registered': current_blueprints_error is None,
                'database': 'unknown',
                'db_config': {
                    'host': cfg.get('host', 'N/A'),
                    'database': cfg.get('database', 'N/A'),
                    'user': cfg.get('user', 'N/A'),
                    'port': cfg.get('port', 'N/A'),
                    'password_set': 'Yes' if cfg.get('password') else 'No'
                },
                'stats': {'persons_count': 0, 'relationships_count': 0},
            }
            connection = get_db_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute('SELECT 1')
                    cursor.fetchone()
                    health_status['database'] = 'connected'
                    try:
                        cursor.execute('SELECT COUNT(*) as count FROM persons')
                        result = cursor.fetchone()
                        health_status['stats']['persons_count'] = result['count'] if result else 0
                        cursor.execute('SELECT COUNT(*) as count FROM relationships')
                        result = cursor.fetchone()
                        health_status['stats']['relationships_count'] = result['count'] if result else 0
                    except Exception as e:
                        logger.warning(f'Error getting stats: {e}')
                    cursor.close()
                    connection.close()
                except Exception as e:
                    health_status['database'] = f'error: {str(e)}'
                    logger.error(f'Database health check error: {e}')
            else:
                health_status['database'] = 'connection_failed'
                try:
                    mysql.connector.connect(**cfg)
                except Exception as e:
                    health_status['connection_error'] = str(e)
            if current_blueprints_error:
                health_status['blueprints_error'] = current_blueprints_error
            if is_production_env() and not _health_detail_authorized():
                return jsonify(_public_health_payload(health_status))
            return jsonify(health_status)
        except Exception as e:
            logger.error(f'api_health error: {e}', exc_info=True)
            if is_production_env() and not _health_detail_authorized():
                return jsonify({'server': 'ok', 'database': 'error'}), 500
            return jsonify({'server': 'ok', 'database': 'error', 'error': str(e)}), 500


def register_member_stats_route(app):
    @app.route('/api/stats/members', methods=['GET'])
    def api_member_stats():
        """Tra ve thong ke thanh vien: tong, nam, nu, khong ro, theo doi va theo nhanh."""
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_members,
                    SUM(CASE WHEN gender = 'Nam' THEN 1 ELSE 0 END) AS male_count,
                    SUM(CASE WHEN gender = 'Nữ' THEN 1 ELSE 0 END) AS female_count,
                    SUM(CASE
                            WHEN gender IS NULL OR gender = '' OR gender NOT IN ('Nam', 'Nữ')
                            THEN 1 ELSE 0 END) AS unknown_gender_count
                FROM persons
            """)
            row = cursor.fetchone() or {}
            cursor.execute('''
                SELECT
                    COALESCE(generation_level, 0) AS generation_level,
                    COUNT(*) AS count
                FROM persons
                WHERE generation_level IS NOT NULL
                    AND generation_level >= 1
                    AND generation_level <= 8
                GROUP BY generation_level
                ORDER BY generation_level ASC
            ''')
            generation_stats = cursor.fetchall()
            generation_dict = {}
            for gen_stat in generation_stats:
                gen_level = gen_stat.get('generation_level', 0)
                count = gen_stat.get('count', 0)
                generation_dict[int(gen_level)] = int(count)
            generation_counts = []
            for i in range(1, 9):
                generation_counts.append({'generation_level': i, 'count': generation_dict.get(i, 0)})

            cursor.execute(
                """
                SELECT COUNT(*) AS ancestor_count
                FROM persons
                WHERE generation_level = 1
                """
            )
            ancestor_row = cursor.fetchone() or {}
            ancestor_count = int(ancestor_row.get('ancestor_count') or 0)

            branch_counts = []
            try:
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'persons'
                      AND COLUMN_NAME IN ('branch_name', 'branch_id')
                    """
                )
                branch_cols = {str((r or {}).get('COLUMN_NAME') or '').strip() for r in (cursor.fetchall() or [])}
                has_branch_name = 'branch_name' in branch_cols
                has_branch_id = 'branch_id' in branch_cols

                has_branches_table = False
                if has_branch_id:
                    cursor.execute(
                        """
                        SELECT TABLE_NAME
                        FROM information_schema.TABLES
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME = 'branches'
                        LIMIT 1
                        """
                    )
                    has_branches_table = bool(cursor.fetchone())

                if has_branch_name:
                    cursor.execute(
                        """
                        SELECT
                            COALESCE(NULLIF(TRIM(branch_name), ''), 'Không rõ / khác') AS branch_name,
                            COUNT(*) AS count
                        FROM persons
                        GROUP BY COALESCE(NULLIF(TRIM(branch_name), ''), 'Không rõ / khác')
                        ORDER BY count DESC, branch_name ASC
                        """
                    )
                    branch_counts = cursor.fetchall() or []
                elif has_branch_id and has_branches_table:
                    cursor.execute(
                        """
                        SELECT
                            COALESCE(NULLIF(TRIM(b.branch_name), ''), 'Không rõ / khác') AS branch_name,
                            COUNT(*) AS count
                        FROM persons p
                        LEFT JOIN branches b ON p.branch_id = b.branch_id
                        GROUP BY COALESCE(NULLIF(TRIM(b.branch_name), ''), 'Không rõ / khác')
                        ORDER BY count DESC, branch_name ASC
                        """
                    )
                    branch_counts = cursor.fetchall() or []
                else:
                    branch_counts = []
            except Exception as branch_err:
                logger.warning('Could not build branch_counts in /api/stats/members: %s', branch_err)
                branch_counts = []

            cursor.execute("""
                SELECT
                    academic_rank,
                    COUNT(*) AS count
                FROM persons
                WHERE academic_rank IS NOT NULL
                    AND academic_rank != ''
                    AND TRIM(academic_rank) != ''
                GROUP BY academic_rank
                ORDER BY count DESC, academic_rank ASC
            """)
            academic_rank_stats = cursor.fetchall()
            cursor.execute("""
                SELECT
                    academic_degree,
                    COUNT(*) AS count
                FROM persons
                WHERE academic_degree IS NOT NULL
                    AND academic_degree != ''
                    AND TRIM(academic_degree) != ''
                GROUP BY academic_degree
                ORDER BY count DESC, academic_degree ASC
            """)
            academic_degree_stats = cursor.fetchall()
            cursor.execute("""
                SELECT COUNT(*) AS total_with_rank
                FROM persons
                WHERE academic_rank IS NOT NULL
                    AND academic_rank != ''
                    AND TRIM(academic_rank) != ''
            """)
            total_with_rank_result = cursor.fetchone()
            total_with_rank = total_with_rank_result.get('total_with_rank', 0) if total_with_rank_result else 0
            cursor.execute("""
                SELECT COUNT(*) AS total_with_degree
                FROM persons
                WHERE academic_degree IS NOT NULL
                    AND academic_degree != ''
                    AND TRIM(academic_degree) != ''
            """)
            total_with_degree_result = cursor.fetchone()
            total_with_degree = total_with_degree_result.get('total_with_degree', 0) if total_with_degree_result else 0
            degree_categories = {'Cử nhân': 0, 'Thạc sĩ': 0, 'Tiến sĩ': 0, 'Giáo sư': 0, 'Phó Giáo sư': 0}
            for stat in academic_degree_stats:
                degree = stat.get('academic_degree', '').strip() if stat.get('academic_degree') else ''
                count = stat.get('count', 0)
                if not degree:
                    continue
                degree_lower = degree.lower()
                if any((kw in degree_lower for kw in ['tiến sĩ', 'tiến sỹ', 'doctor', 'phd', 'doctorate', 'ts.', 'ts '])):
                    degree_categories['Tiến sĩ'] += count
                elif any((kw in degree_lower for kw in ['thạc sĩ', 'thạc sỹ', 'master', 'masters', 'th.s', 'th.s.', 'thạc sĩ'])):
                    degree_categories['Thạc sĩ'] += count
                elif any((kw in degree_lower for kw in ['cử nhân', 'bachelor', 'cử nhân', 'cn.', 'cn '])):
                    degree_categories['Cử nhân'] += count
            for stat in academic_rank_stats:
                rank = stat.get('academic_rank', '').strip() if stat.get('academic_rank') else ''
                count = stat.get('count', 0)
                if not rank:
                    continue
                rank_lower = rank.lower()
                if any((kw in rank_lower for kw in ['phó giáo sư', 'phó giáo sư', 'associate professor', 'pgs.', 'pgs ', 'phó giáo sư'])):
                    degree_categories['Phó Giáo sư'] += count
                elif any((kw in rank_lower for kw in ['giáo sư', 'professor', 'gs.', 'gs ', 'giáo sư'])):
                    degree_categories['Giáo sư'] += count
            return jsonify({'total_members': row.get('total_members', 0), 'male_count': row.get('male_count', 0), 'female_count': row.get('female_count', 0), 'unknown_gender_count': row.get('unknown_gender_count', 0), 'ancestor_count': ancestor_count, 'branch_counts': branch_counts, 'generation_counts': generation_counts, 'academic_rank_stats': academic_rank_stats, 'academic_degree_stats': academic_degree_stats, 'total_with_rank': total_with_rank, 'total_with_degree': total_with_degree, 'degree_categories': degree_categories})
        except Exception as e:
            print(f'ERROR: Loi khi lay thong ke thanh vien: {e}')
            print(traceback.format_exc())
            return (jsonify({'success': False, 'error': 'Không thể lấy thống kê'}), 500)
        finally:
            try:
                if connection.is_connected():
                    cursor.close()
                    connection.close()
            except Exception:
                pass
