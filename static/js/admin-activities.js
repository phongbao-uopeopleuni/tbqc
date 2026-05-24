(function () {
    // Khởi tạo Quill Editor
    let quillEditor = null;
    let currentPostId = null;

    document.addEventListener('DOMContentLoaded', function() {
      const editorElement = document.getElementById('contentEditor');
      if (!editorElement) {
        console.error('Quill Editor: Element #contentEditor not found');
        return;
      }

      try {
        quillEditor = new Quill('#contentEditor', {
          theme: 'snow',
          modules: {
            toolbar: [
              [{ 'header': [1, 2, 3, false] }],
              ['bold', 'italic', 'underline', 'strike'],
              [{ 'color': [] }, { 'background': [] }],
              [{ 'list': 'ordered'}, { 'list': 'bullet' }],
              [{ 'align': [] }],
              ['link', 'image'],
              ['clean']
            ]
          },
          placeholder: 'Nhập nội dung bài viết...'
        });
        console.log('Quill Editor initialized successfully');
      } catch (error) {
        console.error('Quill Editor initialization error:', error);
        showMessage('Lỗi khởi tạo editor. Vui lòng tải lại trang.', 'error');
      }
    });

    /**
     * Clean text - Loại bỏ TẤT CẢ các ký tự không hợp lệ
     */
    function cleanText(text) {
      if (!text || typeof text !== 'string') {
        return '';
      }

      return text.replace(/[^\x20-\x7E\u00A0-\uFFFF\n\r\t]/g, '')
        .replace(/[\u200B-\u200D\uFEFF]/g, '')
        .replace(/[\u25A0-\u25FF]/g, '')
        /* eslint-disable-next-line no-control-regex */
        .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]/g, '');
    }

    /**
     * Sanitize HTML content để load vào Quill Editor
     */
    function sanitizeHtmlForQuill(html) {
      if (!html || typeof html !== 'string') {
        return '';
      }

      try {
        let cleaned = cleanText(html);
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = cleaned;

        const scripts = tempDiv.querySelectorAll('script, style, iframe, object, embed, form, input, button');
        scripts.forEach(el => el.remove());

        const allElements = tempDiv.querySelectorAll('*');
        allElements.forEach(el => {
          Array.from(el.attributes).forEach(attr => {
            if (attr.name.toLowerCase().startsWith('on')) {
              el.removeAttribute(attr.name);
            }
          });
        });

        const walker = document.createTreeWalker(
          tempDiv,
          NodeFilter.SHOW_TEXT,
          null,
          false
        );

        let node;
        while ((node = walker.nextNode())) {
          node.textContent = cleanText(node.textContent);
        }

        allElements.forEach(el => {
          Array.from(el.attributes).forEach(attr => {
            const cleanedValue = cleanText(attr.value);
            if (cleanedValue !== attr.value) {
              el.setAttribute(attr.name, cleanedValue);
            }
          });
        });

        let sanitized = tempDiv.innerHTML;
        sanitized = cleanText(sanitized);

        sanitized = sanitized
          .replace(/&nbsp;/g, ' ')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'");

        sanitized = cleanText(sanitized);

        return sanitized;
      } catch (error) {
        console.error('Error sanitizing HTML for Quill:', error);
        return cleanText(html);
      }
    }

    // Generic JSON fetch helper
    async function fetchJson(url, options) {
      const res = await fetch(url, options);
      const contentType = res.headers.get('Content-Type') || '';
      const text = await res.text();

      if (!res.ok) {
        console.error('HTTP error for', url, res.status, text);
        throw new Error(`HTTP ${res.status} khi gọi ${url}`);
      }

      if (!contentType.includes('application/json')) {
        console.error('Non‑JSON response for', url, 'contentType =', contentType, 'body =', text.slice(0, 200));
        throw new Error(`Phản hồi không phải JSON. Server trả về HTML hoặc nội dung khác.`);
      }

      try {
        return JSON.parse(text);
      } catch (e) {
        console.error('JSON parse error for', url, 'body =', text.slice(0, 200));
        throw e;
      }
    }

    function escapeHtml(text) {
      if (text === null || text === undefined) return '';
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    function showMessage(msg, type = 'success') {
      const msgEl = document.getElementById('message');
      msgEl.className = `message ${type}`;
      msgEl.textContent = msg;
      msgEl.style.display = 'block';
      setTimeout(() => { msgEl.style.display = 'none'; }, 5000);
    }

    async function checkAuth() {
      try {
        const result = await fetchJson('/api/activities/can-post');
        return !!(result && result.allowed);
      } catch (e) {
        console.warn('checkAuth failed (API unavailable or error):', e.message);
        return true;
      }
    }

    async function loadPosts() {
      const listEl = document.getElementById('postsList');
      try {
        const posts = await fetchJson('/api/activities');
        if (!Array.isArray(posts) || posts.length === 0) {
          listEl.innerHTML = '<div class="loading">Chưa có bài viết nào</div>';
          return;
        }
        listEl.innerHTML = posts.map(p => {
          const date = p.created_at ? new Date(p.created_at).toLocaleDateString('vi-VN') : '';
          const statusClass = p.status === 'published' ? 'status-published' : 'status-draft';
          const statusText = p.status === 'published' ? 'Đã đăng' : 'Nháp';
          const thumbnail = p.thumbnail ? `<img src="${escapeHtml(p.thumbnail)}" alt="Thumbnail">` : '';
          const isActive = currentPostId == p.id ? 'active' : '';
          return `
            <div class="post-item ${isActive}" onclick="editPost(${p.id})">
              <div class="post-title">
                ${thumbnail}
                <span>${escapeHtml(p.title || 'Không có tiêu đề')}</span>
              </div>
              <div class="post-meta">
                <span class="post-status ${statusClass}">${statusText}</span>
                ${date ? date : ''}
              </div>
              <div class="post-actions">
                <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); editPost(${p.id})">Sửa</button>
                <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deletePost(${p.id}, '${escapeHtml(p.title || '')}')">Xóa</button>
                <a href="/activities/${p.id || p.activity_id}" target="_blank" class="btn btn-sm btn-primary" style="text-decoration:none;display:inline-block;" onclick="event.stopPropagation();">Xem</a>
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        listEl.innerHTML = `<div class="message error">Lỗi: ${escapeHtml(err.message)}</div>`;
      }
    }

    async function editPost(id) {
      try {
        currentPostId = id;
        const post = await fetchJson(`/api/activities/${id}`);
        document.getElementById('activityId').value = post.id;
        document.getElementById('title').value = post.title || '';
        document.getElementById('summary').value = post.summary || '';
        document.getElementById('category').value = post.category || '';

        const content = post.content || '';
        console.log('Loading content into Quill Editor, length:', content.length);

        if (quillEditor) {
          try {
            if (!quillEditor.root) {
              console.error('Quill Editor root not available');
              document.getElementById('content').value = content;
            } else {
              if (!content || content.trim() === '') {
                quillEditor.setContents([]);
                console.log('Quill Editor: Set empty content');
              } else {
                const sanitizedContent = sanitizeHtmlForQuill(content);
                console.log('Quill Editor: Sanitized content length:', sanitizedContent.length);

                try {
                  quillEditor.setContents([]);
                  const finalCleanHtml = sanitizeHtmlForQuill(sanitizedContent);
                  let delta = quillEditor.clipboard.convert({ html: finalCleanHtml });

                  if (delta && delta.ops) {
                    delta.ops = delta.ops.map(op => {
                      if (op.insert && typeof op.insert === 'string') {
                        op.insert = cleanText(op.insert);
                      }
                      if (op.attributes) {
                        Object.keys(op.attributes).forEach(key => {
                          if (typeof op.attributes[key] === 'string') {
                            op.attributes[key] = cleanText(op.attributes[key]);
                          }
                        });
                      }
                      return op;
                    }).filter(op => {
                      if (op.insert && typeof op.insert === 'string') {
                        const cleaned = cleanText(op.insert);
                        return cleaned.length > 0;
                      }
                      return true;
                    });
                  }

                  quillEditor.setContents(delta);
                  console.log('Quill Editor: Content loaded successfully');
                } catch (deltaError) {
                  console.error('Quill Editor: Error loading content:', deltaError);
                  const cleanTextOnly = cleanText(sanitizedContent);
                  quillEditor.setText(cleanTextOnly);
                  console.log('Quill Editor: Fallback to text-only mode');
                }
              }
            }
          } catch (error) {
            console.error('Quill Editor: Error setting content:', error);
            document.getElementById('content').value = content;
            showMessage('Lỗi khi load nội dung vào editor. Đã fallback về textarea.', 'error');
          }
        } else {
          console.warn('Quill Editor not initialized, using textarea');
          document.getElementById('content').value = content;
        }

        document.getElementById('thumbnail').value = post.thumbnail || '';
        document.getElementById('status').value = post.status || 'draft';
        document.getElementById('formTitle').textContent = 'Chỉnh sửa bài đăng';
        document.getElementById('submitBtn').textContent = 'Cập nhật';
        // Nút Đăng bài luôn hiển thị

        uploadedImages = post.images || [];
        updateImagesPreview();
        updateImagesCount();

        if (post.thumbnail) {
          const previewDiv = document.getElementById('thumbnailPreview');
          const previewImg = document.getElementById('previewImg');
          previewImg.src = post.thumbnail;
          previewDiv.style.display = 'block';
        }

        document.getElementById('activityForm').scrollIntoView({ behavior: 'smooth' });
        loadPosts(); // Reload để highlight active post
      } catch (err) {
        console.error('Error in editPost:', err);
        showMessage('Lỗi: ' + err.message, 'error');
      }
    }

    async function deletePost(id, title) {
      if (!confirm(`Bạn có chắc muốn xóa bài "${title}"?`)) return;
      try {
        await fetchJson(`/api/activities/${id}`, { method: 'DELETE' });
        showMessage('Đã xóa thành công');
        loadPosts();
        if (document.getElementById('activityId').value == id) {
          resetForm();
        }
      } catch (err) {
        showMessage('Lỗi: ' + err.message, 'error');
      }
    }

    function resetForm() {
      document.getElementById('activityForm').reset();
      document.getElementById('activityId').value = '';
      currentPostId = null;
      document.getElementById('formTitle').textContent = 'Tạo bài đăng mới';
      document.getElementById('submitBtn').textContent = 'Lưu nháp';
      // Nút Đăng bài luôn hiển thị
      document.getElementById('thumbnailPreview').style.display = 'none';
      document.getElementById('thumbnailFile').value = '';
      uploadedImages = [];
      updateImagesPreview();
      updateImagesCount();

      if (quillEditor) {
        try {
          quillEditor.setContents([]);
          console.log('Quill Editor: Reset to empty state');
        } catch (error) {
          console.error('Quill Editor: Error resetting editor:', error);
          try {
            if (quillEditor.root) {
              quillEditor.root.innerHTML = '';
            }
          } catch (fallbackError) {
            console.error('Quill Editor: Fallback reset failed:', fallbackError);
          }
        }
      }

      document.getElementById('content').value = '';
      loadPosts(); // Reload để remove active highlight
    }

    async function publishNow() {
      const form = document.getElementById('activityForm');
      const title = document.getElementById('title').value.trim();
      const contentText = quillEditor ? quillEditor.getText().trim() : document.getElementById('content').value.trim();

      // Validate trước khi đăng
      if (!title) {
        showMessage('Vui lòng nhập tiêu đề', 'error');
        document.getElementById('title').focus();
        return;
      }

      if (!contentText) {
        showMessage('Vui lòng nhập nội dung', 'error');
        if (quillEditor) {
          quillEditor.focus();
        }
        return;
      }

      // Set status thành published và submit form
      document.getElementById('status').value = 'published';
      form.dispatchEvent(new Event('submit'));
    }

    // Danh sách ảnh đã upload
    let uploadedImages = [];

    async function handleThumbnailUpload(event) {
      const file = event.target.files[0];
      if (!file) {
        console.log('No file selected');
        return;
      }

      console.log('Thumbnail upload started:', file.name, file.size, file.type);

      if (!file.type.startsWith('image/')) {
        showMessage('Vui lòng chọn file ảnh', 'error');
        event.target.value = '';
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        showMessage('File ảnh quá lớn (tối đa 5MB)', 'error');
        event.target.value = '';
        return;
      }

      // Show preview immediately
      const reader = new FileReader();
      reader.onload = function(e) {
        const previewDiv = document.getElementById('thumbnailPreview');
        const previewImg = document.getElementById('previewImg');
        previewImg.src = e.target.result;
        previewDiv.style.display = 'block';
      };
      reader.readAsDataURL(file);

      const formData = new FormData();
      formData.append('image', file);

      try {
        showMessage('Đang upload ảnh...', 'success');
        console.log('Sending upload request to /api/upload-image');

        const response = await fetch('/api/upload-image', {
          method: 'POST',
          body: formData,
          credentials: 'include'
        });

        console.log('Upload response status:', response.status);
        console.log('Upload response headers:', response.headers);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Upload failed:', response.status, errorText);
          throw new Error(`HTTP ${response.status}: ${response.statusText || errorText}`);
        }

        const contentType = response.headers.get('Content-Type') || '';
        console.log('Response Content-Type:', contentType);

        let result;
        if (contentType.includes('application/json')) {
          result = await response.json();
        } else {
          const text = await response.text();
          console.error('Non-JSON response:', text);
          throw new Error('Server trả về response không phải JSON');
        }

        console.log('Upload result:', result);

        if (result.success && result.url) {
          document.getElementById('thumbnail').value = result.url;
          showMessage('Upload ảnh thành công!', 'success');
          console.log('Thumbnail URL set to:', result.url);
        } else {
          const errorMsg = result.error || result.message || 'Lỗi khi upload ảnh';
          console.error('Upload failed:', errorMsg);
          showMessage(errorMsg, 'error');
          // Reset preview on error
          document.getElementById('thumbnailPreview').style.display = 'none';
        }
      } catch (err) {
        console.error('Upload error:', err);
        showMessage('Lỗi: ' + err.message, 'error');
        // Reset preview on error
        document.getElementById('thumbnailPreview').style.display = 'none';
      } finally {
        // Reset input để có thể chọn lại file cùng tên
        event.target.value = '';
      }
    }

    async function handleImagesUpload(event) {
      const files = Array.from(event.target.files);
      if (files.length === 0) {
        console.log('No files selected');
        return;
      }

      console.log('Images upload started:', files.length, 'files');

      const currentCount = uploadedImages.length;
      const remainingSlots = 10 - currentCount;

      if (files.length > remainingSlots) {
        showMessage(`Chỉ có thể upload tối đa 10 ảnh. Bạn đã có ${currentCount} ảnh, chỉ có thể thêm ${remainingSlots} ảnh nữa.`, 'error');
        event.target.value = '';
        return;
      }

      const validFiles = files.filter(file => {
        if (!file.type.startsWith('image/')) {
          showMessage(`File "${file.name}" không phải là ảnh`, 'error');
          return false;
        }

        if (file.size > 5 * 1024 * 1024) {
          showMessage(`File "${file.name}" quá lớn (tối đa 5MB)`, 'error');
          return false;
        }
        return true;
      });

      if (validFiles.length === 0) {
        event.target.value = '';
        return;
      }

      showMessage(`Đang upload ${validFiles.length} ảnh...`, 'success');

      let successCount = 0;
      let failCount = 0;

      for (let i = 0; i < validFiles.length; i++) {
        const file = validFiles[i];
        const formData = new FormData();
        formData.append('image', file);

        console.log(`Uploading file ${i + 1}/${validFiles.length}:`, file.name, file.size, file.type);

        try {
          const response = await fetch('/api/upload-image', {
            method: 'POST',
            body: formData,
            credentials: 'include'
          });

          console.log(`Upload response for ${file.name}:`, response.status);

          if (!response.ok) {
            const errorText = await response.text();
            console.error(`Upload failed for ${file.name}:`, response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText || errorText}`);
          }

          const contentType = response.headers.get('Content-Type') || '';
          let result;

          if (contentType.includes('application/json')) {
            result = await response.json();
          } else {
            const text = await response.text();
            console.error('Non-JSON response for', file.name, ':', text);
            throw new Error('Server trả về response không phải JSON');
          }

          console.log('Upload result for', file.name, ':', result);

          if (result.success && result.url) {
            uploadedImages.push(result.url);
            updateImagesPreview();
            updateImagesCount();
            successCount++;
            console.log('Successfully uploaded:', file.name, 'URL:', result.url);
          } else {
            const errorMsg = result.error || result.message || 'Lỗi không xác định';
            console.error(`Upload failed for ${file.name}:`, errorMsg);
            showMessage(`Lỗi upload "${file.name}": ${errorMsg}`, 'error');
            failCount++;
          }
        } catch (err) {
          console.error(`Upload error for ${file.name}:`, err);
          showMessage(`Lỗi upload "${file.name}": ${err.message}`, 'error');
          failCount++;
        }
      }

      event.target.value = '';

      if (successCount > 0) {
        showMessage(`Đã upload thành công ${successCount}/${validFiles.length} ảnh`, 'success');
      }

      if (failCount > 0 && successCount === 0) {
        showMessage(`Không thể upload ảnh. Vui lòng kiểm tra console để xem chi tiết lỗi.`, 'error');
      }
    }

    function updateImagesPreview() {
      const previewDiv = document.getElementById('imagesPreview');
      if (!previewDiv) {
        console.error('imagesPreview element not found');
        return;
      }

      previewDiv.innerHTML = '';

      if (!uploadedImages || uploadedImages.length === 0) {
        previewDiv.style.display = 'none';
        return;
      }

      uploadedImages.forEach((url, index) => {
        if (!url) return;

        const imgContainer = document.createElement('div');
        imgContainer.className = 'image-preview-item';

        const img = document.createElement('img');
        let imageUrl = url;
        if (!imageUrl.startsWith('http') && !imageUrl.startsWith('/')) {
          imageUrl = '/' + imageUrl;
        }
        img.src = imageUrl;
        img.loading = 'lazy';

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '×';
        removeBtn.onclick = (e) => {
          e.preventDefault();
          e.stopPropagation();
          if (confirm('Bạn có chắc muốn xóa ảnh này?')) {
            uploadedImages.splice(index, 1);
            updateImagesPreview();
            updateImagesCount();
          }
        };

        img.onerror = function() {
          console.error('Failed to load image:', imageUrl);
          imgContainer.style.border = '2px solid #c62828';
          img.style.display = 'none';
        };

        imgContainer.appendChild(img);
        imgContainer.appendChild(removeBtn);
        previewDiv.appendChild(imgContainer);
      });

      previewDiv.style.display = 'grid';
    }

    function updateImagesCount() {
      document.getElementById('imagesCount').textContent = `Đã chọn: ${uploadedImages.length}/10`;
    }

    document.getElementById('activityForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('activityId').value;

      let contentHtml = '';
      if (quillEditor) {
        contentHtml = quillEditor.root.innerHTML;
        const textContent = quillEditor.getText().trim();
        if (!textContent) {
          showMessage('Vui lòng nhập nội dung', 'error');
          return;
        }

        contentHtml = sanitizeHtmlForQuill(contentHtml);
        console.log('Form submit: Cleaned content length:', contentHtml.length);
      } else {
        contentHtml = document.getElementById('content').value.trim();
        contentHtml = sanitizeHtmlForQuill(contentHtml);
      }

      document.getElementById('content').value = contentHtml;

      const data = {
        title: document.getElementById('title').value.trim(),
        summary: document.getElementById('summary').value.trim(),
        category: document.getElementById('category').value.trim() || null,
        content: contentHtml,
        status: document.getElementById('status').value,
        thumbnail: document.getElementById('thumbnail').value.trim(),
        images: uploadedImages
      };

      if (!data.title) {
        showMessage('Vui lòng nhập tiêu đề', 'error');
        return;
      }

      try {
        if (id) {
          await fetchJson(`/api/activities/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          showMessage('Đã cập nhật thành công');
        } else {
          await fetchJson('/api/activities', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          showMessage('Đã tạo bài viết thành công');
        }
        resetForm();
        loadPosts();
      } catch (err) {
        showMessage('Lỗi: ' + err.message, 'error');
      }
    });

    // Preserve globals used by inline handlers and generated onclick attributes.
    window.cleanText = cleanText;
    window.sanitizeHtmlForQuill = sanitizeHtmlForQuill;
    window.fetchJson = fetchJson;
    window.escapeHtml = escapeHtml;
    window.showMessage = showMessage;
    window.checkAuth = checkAuth;
    window.loadPosts = loadPosts;
    window.editPost = editPost;
    window.deletePost = deletePost;
    window.resetForm = resetForm;
    window.publishNow = publishNow;
    window.handleThumbnailUpload = handleThumbnailUpload;
    window.handleImagesUpload = handleImagesUpload;
    window.updateImagesPreview = updateImagesPreview;
    window.updateImagesCount = updateImagesCount;
    // Initialize: load danh sách bài ngay (trang đã được gate phía server).
    // Không redirect khi checkAuth lỗi để tránh vòng lặp request -> 429.
    (async () => {
      loadPosts();
    })();
})();
