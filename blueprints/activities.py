# -*- coding: utf-8 -*-
"""
Blueprint Tin tuc & Hoat dong.
Routes: /activities, /activities/<id>, /api/activities, /api/activities/post-login,
        /api/activities/<id>, /api/activities/can-post
Chua day du CRUD cho bai dang hoat dong (Activities).
"""
import logging
import json
from flask import Blueprint, render_template, request, jsonify, session, redirect
from flask_login import current_user

from utils.html_sanitize import sanitize_activity_html

logger = logging.getLogger(__name__)
activities_bp = Blueprint('activities', __name__)


# ─────────────────────────────────────────────
# Helper: kiem tra quyen dang bai
# ─────────────────────────────────────────────
def _can_post():
    """Tra ve True neu user co quyen dang bai."""
    if current_user.is_authenticated and getattr(current_user, 'role', '') in ('admin', 'editor'):
        return True
    if session.get('activities_post_ok'):
        return True
    return False


def _activity_to_json(row):
    """Chuyen row DB thanh dict JSON-safe."""
    if not row:
        return None
    images = []
    if row.get('images'):
        try:
            img_val = row['images']
            if isinstance(img_val, str):
                images = json.loads(img_val)
            elif isinstance(img_val, list):
                images = img_val
        except Exception:
            images = []
    return {
        'id': row.get('activity_id'),
        'title': row.get('title'),
        'summary': row.get('summary'),
        'category': row.get('category'),
        'content': row.get('content'),
        'status': row.get('status'),
        'thumbnail': row.get('thumbnail'),
        'images': images,
        'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
        'updated_at': row['updated_at'].isoformat() if row.get('updated_at') else None,
    }


# ─────────────────────────────────────────────
# View routes
# ─────────────────────────────────────────────
@activities_bp.route('/activities', strict_slashes=False)
def activities_page():
    """Trang danh sach hoat dong (public)."""
    return render_template('activities.html')


@activities_bp.route('/activities/<int:activity_id>', strict_slashes=False)
def activity_detail_page(activity_id):
    """Trang chi tiet bai viet."""
    return render_template('activity_detail.html', activity_id=activity_id)


@activities_bp.route('/editor', strict_slashes=False)
def editor_page():
    """Trang soan thao bai dang (yeu cau dang nhap)."""
    return render_template('editor.html')


# ─────────────────────────────────────────────
# API: /api/activities/can-post  (public GET)
# ─────────────────────────────────────────────
@activities_bp.route('/api/activities/can-post', methods=['GET'])
def api_activities_can_post():
    """API kiem tra quyen dang bai."""
    return jsonify({'success': True, 'allowed': bool(_can_post())})


# ─────────────────────────────────────────────
# API: /api/activities/post-login  (POST)
# ─────────────────────────────────────────────
@activities_bp.route('/api/activities/post-login', methods=['POST'])
def api_activities_post_login():
    """Dang nhap cong Activities bang password rieng."""
    try:
        data = request.get_json(silent=True) or {}
        password = (data.get('password') or request.form.get('password') or '').strip()
        if not password:
            return jsonify({'success': False, 'error': 'Thieu mat khau'}), 400
        import os
        correct = os.environ.get('ADMIN_PASSWORD') or os.environ.get('MEMBERS_PASSWORD', '')
        if correct and password == correct:
            session['activities_post_ok'] = True
            session.permanent = True
            session.modified = True
            gate_user = session.get('members_gate_user', 'editor')
            return jsonify({'success': True, 'gate_username': gate_user})
        return jsonify({'success': False, 'error': 'Mat khau khong dung'}), 401
    except Exception as e:
        logger.error(f'api_activities_post_login error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────
# API: GET /api/activities  –  lay danh sach
#      POST /api/activities – tao bai moi
# ─────────────────────────────────────────────
@activities_bp.route('/api/activities', methods=['GET', 'POST'])
def api_activities():
    """GET: lay danh sach bai viet.  POST: tao bai moi (yeu cau quyen)."""
    try:
        from db import get_db_connection
        from services.activities_service import ensure_activities_table
    except ImportError:
        return jsonify({'success': False, 'error': 'Server config error'}), 500

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Khong the ket noi database'}), 500

    cursor = connection.cursor(dictionary=True)
    try:
        ensure_activities_table(cursor)
        connection.commit()

        # ── GET ──────────────────────────────────────────────
        if request.method == 'GET':
            status_filter = request.args.get('status')      # published / draft / None
            limit  = min(int(request.args.get('limit',  50)), 50)
            offset = max(int(request.args.get('offset', 0)),  0)

            where_clauses = []
            params = []
            if status_filter:
                where_clauses.append('status = %s')
                params.append(status_filter)

            where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
            cursor.execute(
                f'SELECT * FROM activities {where_sql} ORDER BY created_at DESC LIMIT %s OFFSET %s',
                params + [limit, offset]
            )
            rows = cursor.fetchall()
            return jsonify([_activity_to_json(r) for r in rows])

        # ── POST ─────────────────────────────────────────────
        if not _can_post():
            return jsonify({'success': False, 'error': 'Ban chua dang nhap hoac khong co quyen dang bai'}), 403

        data = request.get_json(silent=True) or {}
        title   = (data.get('title') or '').strip()
        content = sanitize_activity_html((data.get('content') or '').strip())
        if not title:
            return jsonify({'success': False, 'error': 'Thieu tieu de'}), 400
        if not content:
            return jsonify({'success': False, 'error': 'Thieu noi dung'}), 400

        summary_raw = (data.get('summary') or '').strip() or None
        summary = sanitize_activity_html(summary_raw) if summary_raw else None
        category  = (data.get('category') or '').strip() or None
        status    = data.get('status', 'draft')
        thumbnail = data.get('thumbnail') or None
        images    = data.get('images', [])
        images_json = json.dumps(images, ensure_ascii=False) if images else None

        cursor.execute(
            '''INSERT INTO activities (title, summary, category, content, status, thumbnail, images)
               VALUES (%s, %s, %s, %s, %s, %s, %s)''',
            (title, summary, category, content, status, thumbnail, images_json)
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.execute('SELECT * FROM activities WHERE activity_id = %s', (new_id,))
        new_row = cursor.fetchone()
        return jsonify({'success': True, 'data': _activity_to_json(new_row)}), 201

    except Exception as e:
        logger.error(f'api_activities error: {e}', exc_info=True)
        try:
            connection.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            if getattr(connection, 'is_connected', lambda: False)():
                connection.close()
        except Exception:
            pass


# ─────────────────────────────────────────────
# API: GET  /api/activities/<id>  – chi tiet
#      PUT  /api/activities/<id>  – cap nhat
#      DELETE /api/activities/<id> – xoa
# ─────────────────────────────────────────────
@activities_bp.route('/api/activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
def api_activity_detail(activity_id):
    """Chi tiet / cap nhat / xoa mot bai viet."""
    try:
        from db import get_db_connection
        from services.activities_service import ensure_activities_table
    except ImportError:
        return jsonify({'success': False, 'error': 'Server config error'}), 500

    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Khong the ket noi database'}), 500

    cursor = connection.cursor(dictionary=True)
    try:
        ensure_activities_table(cursor)
        connection.commit()

        # ── GET ──────────────────────────────────────────────
        if request.method == 'GET':
            cursor.execute('SELECT * FROM activities WHERE activity_id = %s', (activity_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Khong tim thay bai viet'}), 404
            return jsonify(_activity_to_json(row))

        # Cac method con lai yeu cau quyen
        if not _can_post():
            return jsonify({'success': False, 'error': 'Khong co quyen'}), 403

        cursor.execute('SELECT activity_id FROM activities WHERE activity_id = %s', (activity_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Khong tim thay bai viet'}), 404

        # ── DELETE ───────────────────────────────────────────
        if request.method == 'DELETE':
            cursor.execute('DELETE FROM activities WHERE activity_id = %s', (activity_id,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Da xoa bai viet'})

        # ── PUT ──────────────────────────────────────────────
        data = request.get_json(silent=True) or {}
        updates, params = [], []

        for field in ('title', 'summary', 'category', 'content', 'status', 'thumbnail'):
            if field in data:
                updates.append(f'{field} = %s')
                raw = data[field]
                if field in ('content', 'summary') and isinstance(raw, str):
                    params.append(sanitize_activity_html(raw.strip()))
                else:
                    params.append((raw or '').strip() if isinstance(raw, str) else raw)

        if 'images' in data:
            images = data['images']
            updates.append('images = %s')
            params.append(json.dumps(images, ensure_ascii=False) if images else None)

        if not updates:
            return jsonify({'success': False, 'error': 'Khong co du lieu cap nhat'}), 400

        params.append(activity_id)
        cursor.execute(
            f'UPDATE activities SET {", ".join(updates)} WHERE activity_id = %s',
            params
        )
        connection.commit()
        cursor.execute('SELECT * FROM activities WHERE activity_id = %s', (activity_id,))
        updated = cursor.fetchone()
        return jsonify({'success': True, 'data': _activity_to_json(updated)})

    except Exception as e:
        logger.error(f'api_activity_detail error: {e}', exc_info=True)
        try:
            connection.rollback()
        except Exception:
            pass
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            if getattr(connection, 'is_connected', lambda: False)():
                connection.close()
        except Exception:
            pass
