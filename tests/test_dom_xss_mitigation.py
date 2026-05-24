"""
test_dom_xss_mitigation.py — Kiểm tra DOM XSS fixes (Phase 2, Fix 2.1 và 2.2)

Chiến lược: Static analysis trên từng file JS.
- Mỗi dangerous innerHTML pattern cụ thể phải có escapeHtml() trong context ±3 dòng.
- Tất cả files trong VULNERABLE_FILES phải tồn tại (guard chống silent-skip).
- utils.js phải có implementation đầy đủ của escapeHtml với 5 replacements.

Files đã được kiểm tra:
- Fix 2.1 (C3): genealogy-tree-controls.js — search box XSS
- Fix 2.2 (H1): admin-users.js, admin-logs.js, admin-activities.js,
                genealogy-grave-family-view.js (bao gồm TD-4)
"""
import pathlib

JS_DIR = pathlib.Path("static/js")

# Format: (filename, [danh sách exact substring của dangerous innerHTML assignments])
# Mỗi entry phải là 1 pattern đủ để identify dòng cụ thể trong file.
VULNERABLE_FILES = [
    # Fix 2.1 (C3) — genealogy search box
    ("genealogy-tree-controls.js", [
        "searchResults.innerHTML = `<div",
    ]),
    # Fix 2.2 (H1) — admin JS error messages
    ("admin-users.js",       ["Lỗi: ${"]),
    ("admin-logs.js",        ["Lỗi: ${"]),
    ("admin-activities.js",  ["Lỗi: ${"]),
    # Fix 2.2 (H1) + TD-4 — grave family view
    ("genealogy-grave-family-view.js", [
        "graveInfoText",
    ]),
]


def test_escape_html_utility_exists_and_is_complete():
    """utils.js phải có escapeHtml với đầy đủ 5 character replacements và window export."""
    utils_path = JS_DIR / "utils.js"
    assert utils_path.exists(), "static/js/utils.js không tồn tại"

    content = utils_path.read_text(encoding="utf-8")
    assert "function escapeHtml" in content, "escapeHtml function không có trong utils.js"

    # Verify đủ 5 replacements cần thiết để chống XSS
    required_replacements = ["/&/g", "/<", "/>/", '/"/g', "/'/g"]
    for rep in required_replacements:
        assert rep in content, (
            f"escapeHtml trong utils.js thiếu replacement: {rep}"
        )
    assert "window.escapeHtml" in content, (
        "escapeHtml phải được expose qua window.escapeHtml để các file JS khác dùng được"
    )


def test_all_vulnerable_files_must_exist():
    """Guard: TẤT CẢ files trong VULNERABLE_FILES phải tồn tại.
    
    Nếu file không tồn tại, test_dangerous_innerhtml_uses_escape_html sẽ silently skip
    mà không phát hiện. Test này ngăn chặn false-pass khi file bị rename/xóa.
    """
    for filename, _ in VULNERABLE_FILES:
        path = JS_DIR / filename
        assert path.exists(), (
            f"static/js/{filename} không tồn tại.\n"
            f"Nếu file đã đổi tên → cập nhật VULNERABLE_FILES trong test này.\n"
            f"Nếu file bị xóa → xem xét lại scope của Fix 2.1/2.2."
        )


def test_dangerous_innerhtml_uses_escape_html():
    """Mỗi dangerous innerHTML pattern phải có escapeHtml() trong context ±3 dòng.
    
    Strict hơn test cũ: không chỉ check "file có escapeHtml ở đâu đó" mà check
    từng pattern cụ thể có escapeHtml gần đó. Bắt được trường hợp file có
    một số innerHTML đã escaped và một số chưa.
    """
    for filename, dangerous_patterns in VULNERABLE_FILES:
        path = JS_DIR / filename
        if not path.exists():
            # test_all_vulnerable_files_must_exist sẽ fail trước
            continue

        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()

        for pattern in dangerous_patterns:
            matching_lines = [
                (i, line) for i, line in enumerate(lines)
                if pattern in line and "innerHTML" in line
            ]

            if not matching_lines:
                # Pattern không tồn tại trong file → fix đã dùng cách khác
                # Không fail, nhưng log để biết
                continue

            for line_idx, line_content in matching_lines:
                # Kiểm tra window context: 1 dòng trước đến 3 dòng sau
                ctx_start = max(0, line_idx - 1)
                ctx_end = min(len(lines), line_idx + 4)
                context = "\n".join(lines[ctx_start:ctx_end])

                assert "escapeHtml(" in context, (
                    f"\n{'='*60}\n"
                    f"FILE: {filename}:{line_idx + 1}\n"
                    f"PATTERN: '{pattern}' dùng innerHTML NHƯNG không có escapeHtml() trong ±3 dòng\n"
                    f"CONTEXT:\n{context}\n"
                    f"{'='*60}\n"
                    f"Fix: thay 'innerHTML = graveInfoText' bằng 'innerHTML = escapeHtml(graveInfoText)'"
                )
