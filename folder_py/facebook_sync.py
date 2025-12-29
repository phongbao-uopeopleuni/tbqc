#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Sync Module
Tự động lấy posts từ Facebook page và lưu vào database
"""

import os
import sys
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
import json
import re
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

# Import DB config
try:
    from folder_py.db_config import get_db_connection
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from folder_py.db_config import get_db_connection


class FacebookSync:
    """Class để sync posts từ Facebook page"""
    
    def __init__(self, page_id: str = None, access_token: str = None):
        """
        Initialize Facebook sync
        
        Args:
            page_id: Facebook page ID hoặc username (e.g., "PhongTuyBienQuanCong")
            access_token: Facebook Page Access Token (từ Facebook Graph API)
        """
        self.page_id = page_id or os.environ.get('FB_PAGE_ID', '350336648378946')
        self.access_token = access_token or os.environ.get('FB_ACCESS_TOKEN')
        self.base_url = "https://graph.facebook.com/v24.0"
        self.images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'facebook')
        
        # Tạo thư mục images nếu chưa có
        os.makedirs(self.images_dir, exist_ok=True)
        
        if not self.access_token:
            logger.warning("FB_ACCESS_TOKEN không được set. Sẽ sử dụng public access (hạn chế)")
    
    def get_page_info(self) -> Optional[Dict]:
        """Lấy thông tin page"""
        try:
            url = f"{self.base_url}/{self.page_id}"
            params = {
                'fields': 'id,name,username',
                'access_token': self.access_token
            } if self.access_token else {}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Lỗi khi lấy page info: {e}")
            return None
    
    def fetch_posts(self, limit: int = 25) -> List[Dict]:
        """
        Lấy posts từ Facebook page
        
        Args:
            limit: Số lượng posts tối đa (default: 25)
        
        Returns:
            List of post dictionaries
        """
        posts = []
        
        try:
            # Graph API endpoint
            url = f"{self.base_url}/{self.page_id}/posts"
            params = {
                'fields': 'id,message,created_time,full_picture,permalink_url,attachments{media,subattachments}',
                'limit': min(limit, 100),  # Facebook max limit
                'access_token': self.access_token
            } if self.access_token else {
                'fields': 'id,message,created_time',
                'limit': min(limit, 25)  # Public access limit
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get('data', [])
            
            # Pagination nếu có
            while 'paging' in data and 'next' in data['paging'] and len(posts) < limit:
                try:
                    next_url = data['paging']['next']
                    response = requests.get(next_url, timeout=15)
                    response.raise_for_status()
                    data = response.json()
                    posts.extend(data.get('data', []))
                    if len(posts) >= limit:
                        break
                except Exception as e:
                    logger.warning(f"Lỗi khi paginate: {e}")
                    break
            
            logger.info(f"Đã lấy {len(posts)} posts từ Facebook")
            return posts[:limit]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi fetch posts từ Facebook: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', str(e))
                    error_type = error_data.get('error', {}).get('type', 'Unknown')
                    logger.error(f"Facebook API Error: {error_type} - {error_msg}")
                    logger.error(f"Full Response: {e.response.text}")
                    # Raise với thông báo rõ ràng hơn
                    raise Exception(f"Facebook API Error ({error_type}): {error_msg}")
                except (ValueError, KeyError):
                    logger.error(f"Response: {e.response.text}")
                    raise Exception(f"Lỗi kết nối Facebook API: {str(e)}")
            else:
                raise Exception(f"Lỗi kết nối Facebook API: {str(e)}")
        except Exception as e:
            logger.error(f"Lỗi không xác định: {e}")
            raise
    
    def extract_images_from_post(self, post: Dict) -> List[str]:
        """
        Extract image URLs từ post
        
        Args:
            post: Post dictionary từ Facebook API
        
        Returns:
            List of image URLs
        """
        images = []
        
        # Full picture (main image)
        if 'full_picture' in post:
            images.append(post['full_picture'])
        
        # Attachments
        if 'attachments' in post and 'data' in post['attachments']:
            for attachment in post['attachments']['data']:
                # Main media
                if 'media' in attachment and 'image' in attachment['media']:
                    img_url = attachment['media']['image'].get('src')
                    if img_url:
                        images.append(img_url)
                
                # Subattachments (multiple images)
                if 'subattachments' in attachment and 'data' in attachment['subattachments']:
                    for sub in attachment['subattachments']['data']:
                        if 'media' in sub and 'image' in sub['media']:
                            img_url = sub['media']['image'].get('src')
                            if img_url:
                                images.append(img_url)
        
        return images
    
    def download_image(self, image_url: str) -> Optional[str]:
        """
        Download image và lưu vào static/images/facebook/
        
        Args:
            image_url: URL của image
        
        Returns:
            Relative path to saved image (e.g., "/static/images/facebook/abc123.jpg")
            hoặc None nếu lỗi
        """
        try:
            # Generate filename từ URL hash
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            if not ext.startswith('.'):
                ext = '.jpg'
            
            filename = f"{url_hash}{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            # Skip nếu đã download
            if os.path.exists(filepath):
                logger.debug(f"Image đã tồn tại: {filename}")
                return f"/static/images/facebook/{filename}"
            
            # Download
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Save
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Đã download image: {filename}")
            return f"/static/images/facebook/{filename}"
            
        except Exception as e:
            logger.error(f"Lỗi khi download image {image_url}: {e}")
            return None
    
    def process_post(self, post: Dict) -> Dict:
        """
        Process một post từ Facebook thành format cho database
        
        Args:
            post: Post dictionary từ Facebook API
        
        Returns:
            Dictionary với format: {title, summary, content, thumbnail, created_at, metadata}
        """
        # Extract text
        message = post.get('message', '').strip()
        
        # Tạo title từ message (first line hoặc first 100 chars)
        lines = message.split('\n')
        title = lines[0].strip() if lines else "Bài viết từ Facebook"
        if len(title) > 200:
            title = title[:197] + "..."
        if not title:
            title = f"Post {post.get('id', 'unknown')}"
        
        # Summary = first 300 chars
        summary = message[:300].strip() if message else ""
        if len(message) > 300:
            summary += "..."
        
        # Content = full message
        content = message
        
        # Extract images
        image_urls = self.extract_images_from_post(post)
        
        # Download first image làm thumbnail
        thumbnail = None
        if image_urls:
            thumbnail = self.download_image(image_urls[0])
        
        # Created time
        created_time = post.get('created_time')
        if created_time:
            try:
                # Parse ISO format: "2024-01-01T12:00:00+0000"
                dt = datetime.fromisoformat(created_time.replace('+0000', '+00:00'))
            except:
                dt = datetime.now()
        else:
            dt = datetime.now()
        
        # Metadata
        metadata = {
            'facebook_post_id': post.get('id'),
            'permalink_url': post.get('permalink_url'),
            'image_urls': image_urls,
            'has_images': len(image_urls) > 0
        }
        
        return {
            'title': title,
            'summary': summary,
            'content': content,
            'thumbnail': thumbnail,
            'created_at': dt,
            'metadata': json.dumps(metadata, ensure_ascii=False)
        }
    
    def sync_to_database(self, posts: List[Dict], status: str = 'published') -> Dict:
        """
        Sync posts vào database
        
        Args:
            posts: List of processed post dictionaries
            status: Status cho posts mới ('published' hoặc 'draft')
        
        Returns:
            Dict với stats: {total, new, updated, errors}
        """
        connection = get_db_connection()
        if not connection:
            logger.error("Không thể kết nối database")
            return {'total': 0, 'new': 0, 'updated': 0, 'errors': []}
        
        stats = {'total': len(posts), 'new': 0, 'updated': 0, 'errors': []}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Ensure activities table có metadata column
            # MySQL doesn't support IF NOT EXISTS for ALTER TABLE, so check first
            try:
                cursor.execute("SHOW COLUMNS FROM activities LIKE 'metadata'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE activities ADD COLUMN metadata TEXT")
                
                cursor.execute("SHOW COLUMNS FROM activities LIKE 'facebook_post_id'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE activities ADD COLUMN facebook_post_id VARCHAR(100)")
                
                # Check index
                cursor.execute("SHOW INDEX FROM activities WHERE Key_name = 'idx_facebook_post_id'")
                if not cursor.fetchone():
                    cursor.execute("ALTER TABLE activities ADD INDEX idx_facebook_post_id (facebook_post_id)")
                
                connection.commit()
            except Exception as e:
                # Column có thể đã tồn tại hoặc có lỗi khác
                logger.debug(f"Metadata column check: {e}")
                connection.rollback()
            
            for post_data in posts:
                try:
                    facebook_post_id = json.loads(post_data.get('metadata', '{}')).get('facebook_post_id')
                    if not facebook_post_id:
                        continue
                    
                    # Check nếu post đã tồn tại
                    cursor.execute("""
                        SELECT activity_id, metadata FROM activities 
                        WHERE facebook_post_id = %s
                    """, (facebook_post_id,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing
                        cursor.execute("""
                            UPDATE activities
                            SET title = %s,
                                summary = %s,
                                content = %s,
                                thumbnail = %s,
                                metadata = %s,
                                updated_at = NOW()
                            WHERE activity_id = %s
                        """, (
                            post_data['title'],
                            post_data['summary'],
                            post_data['content'],
                            post_data['thumbnail'],
                            post_data['metadata'],
                            existing['activity_id']
                        ))
                        stats['updated'] += 1
                        logger.info(f"Updated post: {post_data['title'][:50]}")
                    else:
                        # Insert new
                        cursor.execute("""
                            INSERT INTO activities 
                            (title, summary, content, status, thumbnail, created_at, metadata, facebook_post_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            post_data['title'],
                            post_data['summary'],
                            post_data['content'],
                            status,
                            post_data['thumbnail'],
                            post_data['created_at'],
                            post_data['metadata'],
                            facebook_post_id
                        ))
                        stats['new'] += 1
                        logger.info(f"Inserted new post: {post_data['title'][:50]}")
                    
                except Exception as e:
                    error_msg = f"Lỗi khi sync post {post_data.get('title', 'unknown')}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)
            
            connection.commit()
            logger.info(f"Sync completed: {stats['new']} new, {stats['updated']} updated")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"Lỗi database: {e}")
            stats['errors'].append(str(e))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
        
        return stats
    
    def sync(self, limit: int = 25, status: str = 'published') -> Dict:
        """
        Main sync function: fetch posts và sync vào database
        
        Args:
            limit: Số lượng posts tối đa
            status: Status cho posts mới
        
        Returns:
            Dict với sync results
        """
        logger.info(f"Bắt đầu sync Facebook posts (limit: {limit})")
        
        try:
            # Fetch posts
            posts = self.fetch_posts(limit=limit)
            if not posts:
                return {'success': False, 'error': 'Không lấy được posts từ Facebook. Vui lòng kiểm tra lại Page ID và Access Token.'}
            
            # Process posts
            processed_posts = []
            for post in posts:
                try:
                    processed = self.process_post(post)
                    processed_posts.append(processed)
                except Exception as e:
                    logger.error(f"Lỗi khi process post {post.get('id')}: {e}")
            
            if not processed_posts:
                return {'success': False, 'error': 'Không có posts nào được xử lý thành công'}
            
            # Sync to database
            stats = self.sync_to_database(processed_posts, status=status)
            
            return {
                'success': True,
                'stats': stats,
                'message': f"Đã sync {stats['new']} bài mới, {stats['updated']} bài cập nhật"
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Lỗi trong quá trình sync: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Facebook posts to database')
    parser.add_argument('--limit', type=int, default=25, help='Số lượng posts tối đa')
    parser.add_argument('--status', default='published', choices=['published', 'draft'], 
                       help='Status cho posts mới')
    parser.add_argument('--page-id', help='Facebook page ID hoặc username')
    parser.add_argument('--access-token', help='Facebook access token')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Sync
    sync = FacebookSync(page_id=args.page_id, access_token=args.access_token)
    result = sync.sync(limit=args.limit, status=args.status)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

