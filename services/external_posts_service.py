import logging
import os
import secrets
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from flask import jsonify, request

logger = logging.getLogger(__name__)

external_posts_cache = {'data': None, 'timestamp': None, 'cache_duration': timedelta(minutes=30)}

# RSS chính thức của NukeViet cho mục Hoạt động Hội đồng NPT VN (khác /feed/ — trang đó redirect về trang chủ)
NPT_COUNCIL_RSS_URL = 'https://nguyenphuoctoc.info/rss/hoat-dong-hoi-dong-npt-vn/'


def _external_posts_mutation_authorized():
    """
    clear-cache / refresh: nếu EXTERNAL_POSTS_CACHE_SECRET không đặt → giữ hành vi cũ (mở).
    Nếu đặt → bắt buộc header X-External-Posts-Token hoặc X-Cache-Token (hoặc ?token= cho GET).
    """
    secret = (os.environ.get('EXTERNAL_POSTS_CACHE_SECRET') or '').strip()
    if not secret:
        return True
    token = (request.headers.get('X-External-Posts-Token') or request.headers.get('X-Cache-Token') or '').strip()
    if not token:
        token = (request.args.get('token') or '').strip()
    return bool(token) and secrets.compare_digest(token, secret)


def _npt_post_is_new(pub_date_str: str, days: int = 60) -> bool:
    """Đánh dấu tin còn mới (dùng cho badge Thông tin mới)."""
    if not pub_date_str or not pub_date_str.strip():
        return False
    try:
        dt = parsedate_to_datetime(pub_date_str.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() <= days * 86400
    except Exception:
        return False


def _fetch_npt_council_rss(limit: int = 15):
    """
    Lấy danh sách bài từ RSS NukeViet. Phản hồi có thể có cảnh báo PHP trước <?xml — cần cắt bỏ.
    """
    headers = {
        'User-Agent': 'PhongTuyBienQuanCong/1.0 (+https://www.phongtuybienquancong.info)',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        # Một số máy chủ IIS gắn Content-Encoding: gzip không khớp nội dung — tắt nén để tránh lỗi giải mã
        'Accept-Encoding': 'identity',
    }
    r = requests.get(NPT_COUNCIL_RSS_URL, timeout=30, headers=headers)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or 'utf-8'
    text = r.text
    idx = text.find('<?xml')
    if idx > 0:
        text = text[idx:]
    root = ET.fromstring(text)
    channel = root.find('channel')
    if channel is None:
        return []
    out = []
    for item in channel.findall('item')[:limit]:
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        pub = (item.findtext('pubDate') or '').strip()
        desc_html = (item.findtext('description') or '').strip()
        if not title or not link:
            continue
        thumb = None
        plain = ''
        if desc_html:
            soup = BeautifulSoup(desc_html, 'lxml')
            img = soup.find('img')
            if img and img.get('src'):
                thumb = img['src'].strip()
            plain = soup.get_text(separator=' ', strip=True)
            if len(plain) > 500:
                plain = plain[:500].rsplit(' ', 1)[0] + '…'
        out.append({
            'title': title,
            'link': link,
            'date': pub,
            'description': plain,
            'thumbnail': thumb,
            'is_new': _npt_post_is_new(pub),
        })
    return out


def register_external_posts_routes(app):
    @app.route('/api/external-posts', methods=['GET'])
    def get_external_posts():
        """
        Tin Hoạt động Hội đồng NPT VN từ RSS nguyenphuoctoc.info (cache 30 phút).
        """
        now = datetime.now(timezone.utc)
        cache = external_posts_cache
        try:
            limit = min(max(int(request.args.get('limit', 15)), 1), 50)
        except (TypeError, ValueError):
            limit = 15
        if cache['data'] is not None and cache['timestamp'] is not None:
            age = now - cache['timestamp']
            if age < cache['cache_duration']:
                return jsonify({'success': True, 'data': cache['data'], 'cached': True, 'source': NPT_COUNCIL_RSS_URL})
        try:
            data = _fetch_npt_council_rss(limit=limit)
            cache['data'] = data
            cache['timestamp'] = now
            return jsonify({'success': True, 'data': data, 'cached': False, 'source': NPT_COUNCIL_RSS_URL})
        except Exception as e:
            logger.exception('get_external_posts: RSS fetch failed: %s', e)
            if cache['data']:
                return jsonify({
                    'success': True,
                    'data': cache['data'],
                    'cached': True,
                    'stale': True,
                    'warning': 'Không tải được RSS mới; đang dùng dữ liệu cache.',
                    'source': NPT_COUNCIL_RSS_URL,
                })
            return jsonify({'success': False, 'error': 'Không thể tải tin từ Hội đồng NPT VN', 'detail': str(e)}), 502

    @app.route('/api/external-posts/clear-cache', methods=['POST'])
    def clear_external_posts_cache():
        """Xóa cache RSS. Tùy chọn: EXTERNAL_POSTS_CACHE_SECRET + header X-External-Posts-Token."""
        if not _external_posts_mutation_authorized():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        external_posts_cache['data'] = None
        external_posts_cache['timestamp'] = None
        return jsonify({'success': True, 'message': 'Đã xóa cache external-posts'})

    @app.route('/api/external-posts/refresh', methods=['GET', 'POST'])
    def refresh_external_posts():
        """Bỏ qua cache và tải lại RSS. Cùng quy tắc token với clear-cache khi đặt EXTERNAL_POSTS_CACHE_SECRET."""
        if not _external_posts_mutation_authorized():
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        now = datetime.now(timezone.utc)
        try:
            limit = min(max(int(request.args.get('limit', 15)), 1), 50)
        except (TypeError, ValueError):
            limit = 15
        try:
            data = _fetch_npt_council_rss(limit=limit)
            external_posts_cache['data'] = data
            external_posts_cache['timestamp'] = now
            return jsonify({'success': True, 'data': data, 'cached': False, 'source': NPT_COUNCIL_RSS_URL})
        except Exception as e:
            logger.exception('refresh_external_posts failed: %s', e)
            if external_posts_cache['data']:
                return jsonify({
                    'success': True,
                    'data': external_posts_cache['data'],
                    'stale': True,
                    'warning': str(e),
                    'source': NPT_COUNCIL_RSS_URL,
                })
            return jsonify({'success': False, 'error': str(e)}), 502
