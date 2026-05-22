(function () {
    async function fetchJson(url, options = {}) {
      const response = await fetch(url, {
        ...options,
        credentials: 'include'
      });
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          window.location.href = '/admin/login';
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    }

    function showMessage(text, type = 'success', timeout = 5000) {
      const msgEl = document.getElementById('message');
      msgEl.innerHTML = text; // Use innerHTML to support HTML content
      msgEl.className = `alert alert-${type}`;
      msgEl.style.display = 'block';
      setTimeout(() => {
        msgEl.style.display = 'none';
      }, timeout);
    }

    async function loadUsers() {
      const listEl = document.getElementById('usersList');
      try {
        const users = await fetchJson('/api/admin/users');
        if (!Array.isArray(users) || users.length === 0) {
          listEl.innerHTML = '<tr><td colspan="8" class="loading-cell"><div class="loading">Chưa có người dùng nào</div></td></tr>';
          return;
        }

        listEl.innerHTML = users.map(u => {
          const createdDate = u.created_at ? new Date(u.created_at).toLocaleDateString('vi-VN') : '';
          const roleClass = `role-${u.role || 'user'}`;
          const statusClass = u.is_active ? 'status-active' : 'status-inactive';
          const statusText = u.is_active ? 'Hoạt động' : 'Vô hiệu';

          return `
            <tr>
              <td>${u.user_id}</td>
              <td><strong>${escapeHtml(u.username || '')}</strong></td>
              <td>${escapeHtml(u.full_name || '-')}</td>
              <td>${escapeHtml(u.email || '-')}</td>
              <td><span class="role-badge ${roleClass}">${u.role || 'user'}</span></td>
              <td><span class="${statusClass}">${statusText}</span></td>
              <td>${createdDate}</td>
              <td>
                <button class="btn btn-sm btn-secondary" onclick="editUser(${u.user_id})">Sửa</button>
                ${u.user_id !== currentUserId ? `<button class="btn btn-sm btn-danger" onclick="deleteUser(${u.user_id}, '${escapeHtml(u.username || '')}')">Xóa</button>` : ''}
              </td>
            </tr>
          `;
        }).join('');
      } catch (err) {
        listEl.innerHTML = `<tr><td colspan="8" class="loading-cell text-muted" style="color: var(--admin-danger);"><div class="loading">Lỗi: ${err.message}</div></td></tr>`;
        showMessage('Lỗi khi tải danh sách người dùng: ' + err.message, 'error');
      }
    }

    let currentUserId = null;

    async function getCurrentUser() {
      try {
        const result = await fetchJson('/api/current-user');
        if (result && result.success && result.user) {
          currentUserId = result.user.user_id;
        }
      } catch (e) {
        console.error('Failed to get current user:', e);
      }
    }

    function openAddUserModal() {
      document.getElementById('modalTitle').textContent = 'Thêm người dùng';
      document.getElementById('userForm').reset();
      document.getElementById('userId').value = '';
      document.getElementById('passwordGroup').style.display = 'block';
      document.getElementById('password').required = true;
      document.getElementById('userModal').classList.add('active');
    }

    function closeUserModal() {
      document.getElementById('userModal').classList.remove('active');
    }

    async function editUser(userId) {
      try {
        const user = await fetchJson(`/api/admin/users/${userId}`);
        document.getElementById('modalTitle').textContent = 'Sửa người dùng';
        document.getElementById('userId').value = user.user_id;
        document.getElementById('username').value = user.username || '';
        document.getElementById('password').value = '';
        document.getElementById('passwordGroup').style.display = 'block';
        document.getElementById('password').required = false;
        document.getElementById('full_name').value = user.full_name || '';
        document.getElementById('email').value = user.email || '';
        document.getElementById('role').value = user.role || 'user';
        document.getElementById('is_active').checked = user.is_active !== false;
        document.getElementById('userModal').classList.add('active');
      } catch (err) {
        showMessage('Lỗi: ' + err.message, 'error');
      }
    }

    async function deleteUser(userId, username) {
      if (!confirm(`Bạn có chắc muốn xóa người dùng "${username}"?`)) return;
      try {
        await fetchJson(`/api/admin/users/${userId}`, { method: 'DELETE' });
        showMessage('Đã xóa thành công');
        loadUsers();
      } catch (err) {
        showMessage('Lỗi: ' + err.message, 'error');
      }
    }

    document.getElementById('userForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const userId = formData.get('user_id');
      const data = Object.fromEntries(formData);

      // Nếu là sửa và không có password mới, không gửi password
      if (userId && !data.password) {
        delete data.password;
      }

      try {
        if (userId) {
          await fetchJson(`/api/admin/users/${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          showMessage('Đã cập nhật thành công');
        } else {
          await fetchJson('/api/admin/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          showMessage('Đã thêm thành công');
        }
        closeUserModal();
        loadUsers();
      } catch (err) {
        showMessage('Lỗi: ' + err.message, 'error');
      }
    });

    // Close modal when clicking outside
    document.getElementById('userModal').addEventListener('click', (e) => {
      if (e.target.id === 'userModal') {
        closeUserModal();
      }
    });

    // Initialize
    getCurrentUser();
    loadUsers();

    // Activity Logs Variables
    let logsOffset = 0;
    let logsLimit = 100;
    let logsTotal = 0;
    let logsFilters = {};
    let autoRefreshInterval = null;

    // Load Activity Logs
    async function loadActivityLogs(limit = logsLimit, offset = logsOffset, filters = logsFilters) {
      const logViewer = document.getElementById('plainLogViewer');
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

        logViewer.textContent = 'Đang tải logs...';

        const result = await fetchJson(`/api/admin/activity-logs?${params.toString()}`);

        if (!result.success) {
          throw new Error(result.error || 'Không thể tải logs');
        }

        logsTotal = result.total || 0;
        logsLimit = result.limit || 100;
        logsOffset = result.offset || 0;

        const logs = result.logs || [];

        if (logs.length === 0) {
          logViewer.textContent = 'Chưa có log nào';
          paginationInfo.textContent = 'Không có log nào';
          prevBtn.disabled = true;
          nextBtn.disabled = true;
          return;
        }

        // Format logs as plain text (similar to system log viewer)
        const logLines = logs.map(log => {
          const timestamp = log.created_at ? formatLogTimestamp(log.created_at) : 'N/A';
          const username = log.username || log.full_name || 'Khách';
          const action = log.action || 'UNKNOWN';
          const targetType = log.target_type || '';
          const targetId = log.target_id || '';
          const ipAddress = log.ip_address || '';

          // Build log line similar to system logs
          let logLine = `${timestamp} [${action}] ${username}`;

          if (targetType && targetId) {
            logLine += `: ${action} ${targetType} ID=${targetId}`;
          } else if (targetType) {
            logLine += `: ${action} ${targetType}`;
          } else {
            logLine += `: ${action}`;
          }

          if (ipAddress) {
            logLine += ` (IP: ${ipAddress})`;
          }

          // Add additional info if available
          if (log.before_data || log.after_data) {
            const changes = [];
            if (log.before_data && log.after_data) {
              changes.push('updated');
            } else if (log.after_data) {
              changes.push('created');
            } else if (log.before_data) {
              changes.push('deleted');
            }
            if (changes.length > 0) {
              logLine += ` [${changes.join(', ')}]`;
            }
          }

          return logLine;
        });

        // Render as plain text
        logViewer.textContent = logLines.join('\n');

        // Auto-scroll to top (newest logs at top)
        logViewer.scrollTop = 0;

        // Update pagination info
        const start = offset + 1;
        const end = Math.min(offset + limit, logsTotal);
        paginationInfo.textContent = `Hiển thị ${start}-${end} trong tổng ${logsTotal} logs`;

        // Update pagination buttons
        prevBtn.disabled = offset === 0;
        nextBtn.disabled = offset + limit >= logsTotal;

      } catch (err) {
        logViewer.textContent = `Lỗi: ${err.message}`;
        logViewer.style.color = '#ef4444';
        paginationInfo.textContent = 'Lỗi khi tải logs';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        showMessage('Lỗi khi tải logs: ' + err.message, 'error');
      }
    }

    function formatLogTimestamp(dateStr) {
      try {
        const date = new Date(dateStr);
        const month = date.toLocaleString('en-US', { month: 'short' });
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${month} ${day} ${hours}:${minutes}:${seconds}`;
      } catch (e) {
        return dateStr;
      }
    }

    function formatDateTime(dateStr) {
      try {
        const date = new Date(dateStr);
        return date.toLocaleString('vi-VN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      } catch (e) {
        return dateStr;
      }
    }

    function formatLogDiff(beforeData, afterData) {
      if (!beforeData && !afterData) {
        return '<span style="color: var(--color-text-muted);">Không có thay đổi</span>';
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
        return '<span style="color: var(--color-text-muted);">Không có thay đổi</span>';
      }

      return `<details>
        <summary>Xem thay đổi</summary>
        <div>
          <div style="margin-bottom: var(--admin-space-2);">
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

    function applyFilters() {
      const action = document.getElementById('filterAction').value.trim();
      const userId = document.getElementById('filterUserId').value.trim();

      logsFilters = {};
      if (action) logsFilters.action = action;
      if (userId) logsFilters.user_id = parseInt(userId);

      logsOffset = 0;
      loadActivityLogs(logsLimit, logsOffset, logsFilters);
    }

    function clearFilters() {
      document.getElementById('filterAction').value = '';
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

    function toggleAutoRefresh() {
      const checkbox = document.getElementById('autoRefreshCheckbox');
      if (checkbox.checked) {
        autoRefreshInterval = setInterval(() => {
          loadActivityLogs(logsLimit, logsOffset, logsFilters);
        }, 30000); // 30 seconds
      } else {
        if (autoRefreshInterval) {
          clearInterval(autoRefreshInterval);
          autoRefreshInterval = null;
        }
      }
    }

    // Initialize activity logs on page load
    loadActivityLogs();

    // Sync TBQC Accounts function
    async function syncTbqcAccounts() {
      const syncBtn = document.getElementById('syncBtn');
      const originalText = syncBtn.innerHTML;

      // Disable button and show loading
      syncBtn.disabled = true;
      syncBtn.innerHTML = 'Đang đồng bộ...';

      try {
        const response = await fetch('/api/admin/sync-tbqc-accounts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
          // Show success message
          showMessage(`${data.message}`, 'success');

          // Show detailed results
          if (data.results && data.results.length > 0) {
            const resultsHtml = data.results.map(r => {
              if (r.success) {
                return `${r.username} (${r.full_name}): ${r.action} thành công (ID: ${r.user_id})`;
              } else {
                return `${r.username}: ${r.error || 'Lỗi không xác định'}`;
              }
            }).join('<br>');

            showMessage(`<strong>Chi tiết:</strong><br>${resultsHtml}`, 'info', 10000);
          }

          // Reload users list
          loadUsers();
        } else {
          showMessage(`Lỗi: ${data.error || 'Không thể đồng bộ'}`, 'error');
        }
      } catch (error) {
        console.error('Error syncing TBQC accounts:', error);
        showMessage(`Lỗi kết nối: ${error.message}`, 'error');
      } finally {
        // Re-enable button
        syncBtn.disabled = false;
        syncBtn.innerHTML = originalText;
      }
    }
    // Preserve globals used by inline handlers and generated onclick attributes.
    window.fetchJson = fetchJson;
    window.showMessage = showMessage;
    window.loadUsers = loadUsers;
    window.getCurrentUser = getCurrentUser;
    window.openAddUserModal = openAddUserModal;
    window.closeUserModal = closeUserModal;
    window.editUser = editUser;
    window.deleteUser = deleteUser;
    window.loadActivityLogs = loadActivityLogs;
    window.formatLogTimestamp = formatLogTimestamp;
    window.formatDateTime = formatDateTime;
    window.formatLogDiff = formatLogDiff;
    window.applyFilters = applyFilters;
    window.clearFilters = clearFilters;
    window.changeLogsPerPage = changeLogsPerPage;
    window.previousPage = previousPage;
    window.nextPage = nextPage;
    window.toggleAutoRefresh = toggleAutoRefresh;
    window.syncTbqcAccounts = syncTbqcAccounts;
})();
