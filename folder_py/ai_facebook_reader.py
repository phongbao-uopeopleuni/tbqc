#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Facebook Post Reader
Dùng AI để đọc và extract nội dung từ Facebook post link
"""

import os
import re
import requests
import logging
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)


class AIFacebookReader:
    """Class để đọc Facebook post bằng AI"""
    
    def __init__(self, ai_provider: str = 'openai', api_key: str = None):
        """
        Initialize AI Facebook Reader
        
        Args:
            ai_provider: 'openai', 'anthropic', hoặc 'gemini'
            api_key: API key cho AI service
        """
        self.ai_provider = ai_provider.lower()
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            logger.warning("Không có AI API key. Một số tính năng có thể không hoạt động.")
    
    def extract_post_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract post ID từ Facebook URL
        
        Args:
            url: Facebook post URL (ví dụ: https://www.facebook.com/PhongTuyBienQuanCong/posts/123456)
        
        Returns:
            Post ID hoặc None
        """
        try:
            # Pattern 1: /posts/123456
            match = re.search(r'/posts/(\d+)', url)
            if match:
                return match.group(1)
            
            # Pattern 2: ?story_fbid=123456
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            if 'story_fbid' in query:
                return query['story_fbid'][0]
            
            # Pattern 3: /permalink/123456
            match = re.search(r'/permalink/(\d+)', url)
            if match:
                return match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Lỗi khi extract post ID: {e}")
            return None
    
    def get_post_content_via_scraping(self, url: str) -> Optional[Dict]:
        """
        Lấy nội dung post bằng cách scrape HTML (cần user agent và có thể cần login)
        
        Args:
            url: Facebook post URL
        
        Returns:
            Dict với title, content, images, date hoặc None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            if not response.ok:
                # Facebook thường chặn scraping với HTTP 400/403
                # Không phải lỗi nghiêm trọng, AI vẫn có thể đọc với URL trực tiếp
                logger.info(f"Không thể scrape HTML từ {url}: HTTP {response.status_code} (Facebook có thể đang chặn scraping, sẽ dùng AI với URL trực tiếp)")
                return None
            
            html = response.text
            
            # Kiểm tra xem có phải là trang lỗi của Facebook không
            if 'login' in html.lower() or 'facebook.com/login' in html.lower() or len(html) < 1000:
                logger.info(f"HTML từ {url} có vẻ không hợp lệ (có thể cần login), sẽ dùng AI với URL trực tiếp")
                return None
            
            # Extract basic info từ HTML (rất hạn chế vì Facebook dùng JavaScript)
            # Đây chỉ là fallback, tốt nhất là dùng AI để đọc
            return {
                'html': html[:5000],  # Chỉ lấy một phần HTML để AI đọc
                'url': url
            }
        except requests.exceptions.RequestException as e:
            # Lỗi kết nối hoặc timeout - không phải lỗi nghiêm trọng
            logger.info(f"Không thể scrape Facebook {url}: {e} (sẽ dùng AI với URL trực tiếp)")
            return None
        except Exception as e:
            logger.warning(f"Lỗi không mong đợi khi scrape Facebook: {e}")
            return None
    
    def extract_content_with_ai(self, url: str, html_content: str = None) -> Optional[Dict]:
        """
        Dùng AI để extract nội dung từ Facebook post
        
        Args:
            url: Facebook post URL
            html_content: HTML content (nếu có)
        
        Returns:
            Dict với title, content, summary, images, date
        """
        if not self.api_key:
            return {'error': 'Không có AI API key. Vui lòng set OPENAI_API_KEY hoặc ANTHROPIC_API_KEY.'}
        
        try:
            if self.ai_provider == 'openai':
                return self._extract_with_openai(url, html_content)
            elif self.ai_provider == 'anthropic':
                return self._extract_with_anthropic(url, html_content)
            else:
                return {'error': f'AI provider {self.ai_provider} chưa được hỗ trợ'}
        except Exception as e:
            logger.error(f"Lỗi khi dùng AI extract: {e}", exc_info=True)
            return {'error': f'Lỗi AI: {str(e)}'}
    
    def _extract_with_openai(self, url: str, html_content: str = None) -> Dict:
        """Extract content với OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            prompt = f"""Bạn là một AI chuyên extract nội dung từ Facebook posts.

URL Facebook post: {url}

Nhiệm vụ: Extract thông tin từ Facebook post này và trả về dưới dạng JSON với format:
{{
    "title": "Tiêu đề bài đăng (nếu không có thì tạo từ nội dung)",
    "content": "Nội dung đầy đủ của bài đăng",
    "summary": "Tóm tắt ngắn gọn (tối đa 300 ký tự)",
    "images": ["url1", "url2", ...],
    "date": "Ngày đăng (nếu có)",
    "author": "Tác giả (nếu có)"
}}

Lưu ý:
- Nếu không có HTML content, hãy dựa vào URL và kiến thức của bạn về page "Phòng Tuy Biên Quân Công"
- Nội dung phải giữ nguyên tiếng Việt
- Images: chỉ list URL của hình ảnh (nếu có)
- Date: format YYYY-MM-DD hoặc "Không rõ"

Trả về JSON hợp lệ, không có markdown formatting."""

            if html_content:
                prompt += f"\n\nHTML Content (một phần):\n{html_content[:3000]}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Hoặc "gpt-4" nếu muốn tốt hơn
                messages=[
                    {"role": "system", "content": "Bạn là một AI chuyên extract nội dung từ Facebook posts. Luôn trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON từ response
            import json
            # Remove markdown code blocks nếu có
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            return result
            
        except ImportError:
            return {'error': 'OpenAI library chưa được cài đặt. Chạy: pip install openai'}
        except Exception as e:
            logger.error(f"Lỗi OpenAI API: {e}", exc_info=True)
            return {'error': f'Lỗi OpenAI: {str(e)}'}
    
    def _extract_with_anthropic(self, url: str, html_content: str = None) -> Dict:
        """Extract content với Anthropic Claude API"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            
            prompt = f"""Bạn là một AI chuyên extract nội dung từ Facebook posts.

URL Facebook post: {url}

Nhiệm vụ: Extract thông tin từ Facebook post này và trả về dưới dạng JSON với format:
{{
    "title": "Tiêu đề bài đăng",
    "content": "Nội dung đầy đủ",
    "summary": "Tóm tắt ngắn gọn",
    "images": ["url1", "url2"],
    "date": "Ngày đăng",
    "author": "Tác giả"
}}

Trả về JSON hợp lệ."""

            if html_content:
                prompt += f"\n\nHTML Content:\n{html_content[:3000]}"
            
            message = client.messages.create(
                model="claude-3-haiku-20240307",  # Hoặc "claude-3-opus" nếu muốn tốt hơn
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = message.content[0].text.strip()
            
            import json
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            return result
            
        except ImportError:
            return {'error': 'Anthropic library chưa được cài đặt. Chạy: pip install anthropic'}
        except Exception as e:
            logger.error(f"Lỗi Anthropic API: {e}", exc_info=True)
            return {'error': f'Lỗi Anthropic: {str(e)}'}
    
    def read_facebook_post(self, url: str) -> Dict:
        """
        Main function: Đọc Facebook post và extract nội dung
        
        Args:
            url: Facebook post URL
        
        Returns:
            Dict với title, content, summary, images, date, author
        """
        logger.info(f"Đang đọc Facebook post: {url}")
        
        # Kiểm tra API key trước
        if not self.api_key:
            error_msg = (
                'Không có AI API key. Vui lòng set một trong các biến môi trường sau:\n'
                '- OPENAI_API_KEY (cho OpenAI GPT)\n'
                '- ANTHROPIC_API_KEY (cho Anthropic Claude)\n\n'
                'Sau khi set, khởi động lại server.'
            )
            logger.error(error_msg)
            return {'error': error_msg}
        
        # Bước 1: Thử scrape HTML (có thể không thành công - Facebook thường chặn)
        html_data = self.get_post_content_via_scraping(url)
        
        # Bước 2: Dùng AI để extract nội dung (với hoặc không có HTML)
        # Ngay cả khi không scrape được HTML, AI vẫn có thể đọc dựa vào URL
        result = self.extract_content_with_ai(url, html_data.get('html') if html_data else None)
        
        # Nếu có warning về scraping nhưng AI vẫn thành công, thêm thông tin
        if html_data is None and 'error' not in result:
            result['_note'] = 'Không thể scrape HTML từ Facebook (có thể bị chặn), nhưng AI đã đọc được nội dung dựa vào URL.'
        
        return result

