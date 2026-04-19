"""Utilities để che bớt hostname / IP khi log.

Mục tiêu:
- Không in thẳng `DB_HOST` hoặc các hostname nội bộ khác ra stdout trong log
  khởi động. Railway / Render thường forward stdout sang monitoring (Sentry,
  Datadog, các external pipeline), làm thông tin hạ tầng lọt ra ngoài.
- Vẫn đủ để developer đối chiếu: giữ vài ký tự đầu + đuôi (TLD / domain root)
  để dễ nhận diện môi trường đúng.

Không thay đổi bất kỳ logic kết nối DB nào — chỉ phục vụ *log*.
"""

from __future__ import annotations


def mask_host(host: object, *, keep_prefix: int = 3, keep_suffix: int = 4) -> str:
    """Trả về bản đã che của `host` để an toàn khi log.

    >>> mask_host("tramway.proxy.rlwy.net")
    'tra…y.net'
    >>> mask_host("127.0.0.1")
    '127…0.0.1'
    >>> mask_host("")
    '(empty)'
    >>> mask_host(None)
    '(empty)'

    Quy tắc:
    - None / chuỗi rỗng → `(empty)`.
    - `len <= keep_prefix + keep_suffix` → giữ nguyên (quá ngắn để mask có ích,
      trường hợp này thường là `localhost` chỉ trong dev).
    - Còn lại: `prefix` + `…` + `suffix`.
    """

    if host is None:
        return "(empty)"
    s = str(host).strip()
    if not s:
        return "(empty)"

    keep_prefix = max(0, int(keep_prefix))
    keep_suffix = max(0, int(keep_suffix))
    if len(s) <= keep_prefix + keep_suffix:
        return s
    return f"{s[:keep_prefix]}\u2026{s[-keep_suffix:]}"
