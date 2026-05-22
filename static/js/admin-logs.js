  // Activity Logs Variables
  let logsOffset = 0;
  let logsLimit = 100;
  let logsTotal = 0;
  let logsFilters = {};

  // Load Activity Logs
  async function loadActivityLogs(limit = logsLimit, offset = logsOffset, filters = logsFilters) {
    const listEl = document.getElementById('activityLogsList');
    const paginationInfo = document.getElementById('logsPaginationInfo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');

    try {
      // Build query string
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
      });

      if (filters.action) params.append('action', filters.action);
      if (filters.target_type) params.append('target_type', filters.target_type);
      if (filters.user_id) params.append('user_id', filters.user_id.toString());

      listEl.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6);"><div class="loading">Đang tải...</div></td></tr>';

      const result = await fetch(`/api/admin/activity-logs?${params.toString()}`, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      // Xử lý các status codes khác nhau
      if (result.status === 401) {
        // Unauthorized - chưa đăng nhập hoặc session hết hạn
        const errorText = await result.text();
        let errorMsg = 'Chưa đăng nhập hoặc session đã hết hạn. Vui lòng đăng nhập lại.';
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Nếu không parse được JSON, dùng message mặc định
        }
        listEl.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6); color: var(--admin-danger);">
          <div style="margin-bottom: 10px;"><strong>Lỗi 401: ${errorMsg}</strong></div>
          <a href="/admin/login" class="btn btn-primary" style="text-decoration: none; display: inline-block; padding: 8px 16px;">Đăng nhập lại</a>
        </td></tr>`;
        paginationInfo.textContent = 'Lỗi xác thực';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      if (result.status === 403) {
        // Forbidden - không có quyền truy cập
        const errorText = await result.text();
        let errorMsg = 'Bạn không có quyền truy cập trang này.';
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Nếu không parse được JSON, dùng message mặc định
        }
        listEl.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6); color: var(--admin-danger);">
          <div><strong>Lỗi 403: ${errorMsg}</strong></div>
        </td></tr>`;
        paginationInfo.textContent = 'Không có quyền truy cập';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      if (result.status === 404) {
        // Not Found - bảng activity_logs không tồn tại
        const errorText = await result.text();
        let errorMsg = 'Bảng activity_logs không tồn tại trong database.';
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Nếu không parse được JSON, dùng message mặc định
        }
        listEl.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6); color: var(--admin-danger);">
          <div><strong>Lỗi 404: ${errorMsg}</strong></div>
          <div style="margin-top: 10px; font-size: 14px; color: var(--admin-text-muted);">Vui lòng kiểm tra database hoặc liên hệ quản trị viên.</div>
        </td></tr>`;
        paginationInfo.textContent = 'Bảng không tồn tại';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      if (!result.ok) {
        // Các lỗi khác
        const errorText = await result.text();
        let errorMsg = `HTTP ${result.status}: ${result.statusText}`;
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.error || errorMsg;
        } catch (e) {
          // Nếu không parse được JSON, dùng status text
        }
        throw new Error(errorMsg);
      }

      // Parse JSON response
      let data;
      try {
        const responseText = await result.text();
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Error parsing JSON response:', parseError);
        throw new Error('Phản hồi từ server không hợp lệ. Vui lòng thử lại.');
      }

      if (!data.success) {
        throw new Error(data.error || 'Không thể tải logs');
      }

      logsTotal = data.total || 0;
      logsLimit = data.limit || 100;
      logsOffset = data.offset || 0;

      const logs = data.logs || [];

      if (logs.length === 0) {
        listEl.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6);">Chưa có log nào</td></tr>';
        paginationInfo.textContent = 'Không có log nào';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
      }

      // Render logs
      listEl.innerHTML = logs.map(log => {
        const createdAt = log.created_at ? formatDateTime(log.created_at) : '-';
        const username = log.username || log.full_name || 'Khách';
        const action = log.action || '-';
        const targetType = log.target_type || '-';
        const targetId = log.target_id || '-';
        const ipAddress = log.ip_address || '-';
        const userAgent = log.user_agent || '-';

        const actionClass = `log-action-${action}`;
        const actionBadge = `<span class="log-action-badge ${actionClass}">${escapeHtml(action)}</span>`;

        // Format before/after data
        const diffHtml = formatLogDiff(log.before_data, log.after_data);

        return `
          <tr class="log-row">
            <td>${createdAt}</td>
            <td>${escapeHtml(username)}</td>
            <td>${actionBadge}</td>
            <td>${escapeHtml(targetType)}</td>
            <td>${escapeHtml(String(targetId))}</td>
            <td class="log-diff">${diffHtml}</td>
            <td>${escapeHtml(ipAddress)}</td>
            <td class="hide-mobile" style="font-size: var(--font-size-xs, 12px); max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(userAgent)}</td>
          </tr>
        `;
      }).join('');

      // Update pagination info
      const start = offset + 1;
      const end = Math.min(offset + limit, logsTotal);
      paginationInfo.textContent = `Hiển thị ${start}-${end} trong tổng ${logsTotal} logs`;

      // Update pagination buttons
      prevBtn.disabled = offset === 0;
      nextBtn.disabled = offset + limit >= logsTotal;

    } catch (err) {
      listEl.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: var(--admin-space-6); color: var(--admin-danger);">Lỗi: ${err.message}</td></tr>`;
      paginationInfo.textContent = 'Lỗi khi tải logs';
      prevBtn.disabled = true;
      nextBtn.disabled = true;
    }
  }

  function formatDateTime(dateStr) {
    try {
      const date = new Date(dateStr);
      // Tự động sử dụng timezone của hệ thống laptop/browser
      // Format: HH:MM:SS DD/MM/YYYY
      const formatter = new Intl.DateTimeFormat('en-US', {
        // Không chỉ định timeZone để tự động dùng timezone của browser
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });

      const parts = formatter.formatToParts(date);
      const hours = parts.find(p => p.type === 'hour').value;
      const minutes = parts.find(p => p.type === 'minute').value;
      const seconds = parts.find(p => p.type === 'second').value;
      const day = parts.find(p => p.type === 'day').value;
      const month = parts.find(p => p.type === 'month').value;
      const year = parts.find(p => p.type === 'year').value;

      return `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
    } catch (e) {
      return dateStr;
    }
  }

  function formatLogDiff(beforeData, afterData) {
    if (!beforeData && !afterData) {
      return '<span style="color: var(--admin-text-muted);">Không có thay đổi</span>';
    }

    if (!beforeData && afterData) {
      return `<details>
        <summary>Tạo mới</summary>
        <pre>${escapeHtml(JSON.stringify(afterData, null, 2))}</pre>
      </details>`;
    }

    if (beforeData && !afterData) {
      return `<details>
        <summary>Xóa</summary>
        <pre>${escapeHtml(JSON.stringify(beforeData, null, 2))}</pre>
      </details>`;
    }

    // Both exist - show diff
    const beforeStr = JSON.stringify(beforeData, null, 2);
    const afterStr = JSON.stringify(afterData, null, 2);

    if (beforeStr === afterStr) {
      return '<span style="color: var(--admin-text-muted);">Không có thay đổi</span>';
    }

    return `<details>
      <summary>Xem thay đổi</summary>
      <div>
        <div style="margin-bottom: var(--space-2);">
          <strong style="color: var(--admin-danger);">Trước:</strong>
          <pre class="diff-removed">${escapeHtml(beforeStr)}</pre>
        </div>
        <div>
          <strong style="color: var(--admin-success);">Sau:</strong>
          <pre class="diff-added">${escapeHtml(afterStr)}</pre>
        </div>
      </div>
    </details>`;
  }

  function escapeHtml(text) {
    if (!text) return '-';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function applyFilters() {
    const action = document.getElementById('filterAction').value.trim();
    const targetType = document.getElementById('filterTargetType').value.trim();
    const userId = document.getElementById('filterUserId').value.trim();

    logsFilters = {};
    if (action) logsFilters.action = action;
    if (targetType) logsFilters.target_type = targetType;
    if (userId) logsFilters.user_id = parseInt(userId);

    logsOffset = 0;
    loadActivityLogs(logsLimit, logsOffset, logsFilters);
  }

  function clearFilters() {
    document.getElementById('filterAction').value = '';
    document.getElementById('filterTargetType').value = '';
    document.getElementById('filterUserId').value = '';
    logsFilters = {};
    logsOffset = 0;
    loadActivityLogs(logsLimit, logsOffset, logsFilters);
  }

  function changeLogsPerPage() {
    const perPage = parseInt(document.getElementById('logsPerPage').value);
    logsLimit = perPage;
    logsOffset = 0;
    loadActivityLogs(logsLimit, logsOffset, logsFilters);
  }

  function previousPage() {
    if (logsOffset > 0) {
      logsOffset = Math.max(0, logsOffset - logsLimit);
      loadActivityLogs(logsLimit, logsOffset, logsFilters);
    }
  }

  function nextPage() {
    if (logsOffset + logsLimit < logsTotal) {
      logsOffset += logsLimit;
      loadActivityLogs(logsLimit, logsOffset, logsFilters);
    }
  }

  function formatBytes(n) {
    if (n == null || n === '') return '—';
    const units = ['B', 'KB', 'MB', 'GB'];
    let i = 0;
    let v = Number(n);
    if (Number.isNaN(v)) return '—';
    while (v >= 1024 && i < units.length - 1) {
      v /= 1024;
      i++;
    }
    return (i === 0 ? v : v.toFixed(2)) + ' ' + units[i];
  }

  async function loadLogStats() {
    try {
      const res = await fetch('/api/admin/log-stats', { credentials: 'include', headers: { Accept: 'application/json' } });
      const data = await res.json();
      if (!data.success) {
        document.getElementById('statPvMonth').textContent = '—';
        document.getElementById('statPvToday').textContent = '—';
        document.getElementById('statLogBytes').textContent = data.error === 'no_db' ? 'Lỗi DB' : '—';
        return;
      }
      document.getElementById('statPvMonth').textContent = data.page_views_month != null ? String(data.page_views_month) : '0';
      document.getElementById('statPvToday').textContent = data.page_views_today != null ? String(data.page_views_today) : '0';
      let bytes = data.total_log_bytes;
      if (bytes == null) {
        let a = data.activity_logs_bytes;
        let p = data.page_views_bytes;
        if (a != null || p != null) bytes = (a || 0) + (p || 0);
      }
      document.getElementById('statLogBytes').textContent = formatBytes(bytes);
    } catch (e) {
      console.error('loadLogStats', e);
    }
  }

  // ============================================================
  // Reset Logs — xoá toàn bộ activity_logs + page_views (có backup)
  // ============================================================
  function openResetLogsModal() {
    const m = document.getElementById('resetLogsModal');
    if (!m) return;
    m.style.display = 'flex';
    const input = document.getElementById('resetLogsConfirmInput');
    if (input) { input.value = ''; input.focus(); }
    const err = document.getElementById('resetLogsError');
    if (err) err.textContent = '';
    const res = document.getElementById('resetLogsResult');
    if (res) res.textContent = '';
    const btn = document.getElementById('btnConfirmResetLogs');
    if (btn) btn.disabled = false;
  }

  function closeResetLogsModal() {
    const m = document.getElementById('resetLogsModal');
    if (m) m.style.display = 'none';
  }

  function _formatBytesShort(n) {
    return formatBytes(n);
  }

  async function confirmResetLogs() {
    const input = document.getElementById('resetLogsConfirmInput');
    const errEl = document.getElementById('resetLogsError');
    const resEl = document.getElementById('resetLogsResult');
    const btn = document.getElementById('btnConfirmResetLogs');
    const token = (input && input.value || '').trim();

    if (token !== 'RESET_ALL_LOGS') {
      if (errEl) errEl.textContent = 'Bạn phải gõ chính xác RESET_ALL_LOGS để xác nhận.';
      return;
    }
    if (errEl) errEl.textContent = '';
    if (resEl) resEl.innerHTML = '<span style="color: var(--admin-text-muted);">Đang xoá log, vui lòng đợi…</span>';
    if (btn) btn.disabled = true;

    try {
      const res = await fetch('/api/admin/reset-logs', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ confirm: 'RESET_ALL_LOGS' }),
      });

      let data = null;
      try { data = await res.json(); } catch (e) { data = null; }

      if (!res.ok || !data || !data.success) {
        const msg = (data && data.error) || `HTTP ${res.status}: ${res.statusText}`;
        if (errEl) errEl.textContent = 'Lỗi: ' + msg;
        if (resEl) resEl.innerHTML = '';
        if (btn) btn.disabled = false;
        return;
      }

      // Thành công — hiển thị tóm tắt + refresh số liệu
      const rd = data.rows_deleted || {};
      const rdLines = Object.keys(rd).map(k => `${k}: ${rd[k]}`).join(', ') || '—';
      const backupTxt = data.backup_file
        ? `<code>${data.backup_file}</code> (${_formatBytesShort(data.backup_size_bytes)})`
        : 'không có';
      if (resEl) {
        resEl.innerHTML = `
          <div style="background: #e8f5e9; border-left: 4px solid #43a047; padding: 10px 14px; border-radius: 4px; color: #1b5e20;">
            <strong>Đã reset log thành công.</strong><br>
            Số dòng đã xoá: ${rdLines}<br>
            Backup: ${backupTxt}
          </div>`;
      }

      // Refresh stats + bảng logs
      try { await loadLogStats(); } catch (e) { /* nuốt lỗi cosmetic */ }
      try {
        logsOffset = 0;
        await loadActivityLogs(logsLimit, logsOffset, logsFilters);
      } catch (e) { /* nuốt lỗi cosmetic */ }

      // Đóng modal sau 1.5s để user kịp đọc thông báo
      setTimeout(closeResetLogsModal, 1500);
    } catch (err) {
      if (errEl) errEl.textContent = 'Lỗi: ' + (err && err.message ? err.message : String(err));
      if (resEl) resEl.innerHTML = '';
      if (btn) btn.disabled = false;
    }
  }

  // Keep inline event handlers working after moving this classic script out of the template.
  window.openResetLogsModal = openResetLogsModal;
  window.closeResetLogsModal = closeResetLogsModal;
  window.confirmResetLogs = confirmResetLogs;
  window.applyFilters = applyFilters;
  window.clearFilters = clearFilters;
  window.changeLogsPerPage = changeLogsPerPage;
  window.previousPage = previousPage;
  window.nextPage = nextPage;
  // ESC để đóng modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const m = document.getElementById('resetLogsModal');
      if (m && m.style.display !== 'none') closeResetLogsModal();
    }
  });

  // Initialize activity logs on page load
  document.addEventListener('DOMContentLoaded', () => {
    loadLogStats();
    loadActivityLogs();
  });
