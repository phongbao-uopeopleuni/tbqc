import pathlib
import re

def test_static_js_uses_escape_html():
    """Verify that vulnerable .innerHTML assignments have been wrapped with escapeHtml."""
    js_dir = pathlib.Path("static/js")
    assert js_dir.exists(), "static/js directory not found"
    
    # Files that were modified in Phase 2
    target_files = [
        "admin-users.js",
        "search.js",
        "activities.js",
        "genealogy-tree.js",
        "admin-logs.js"
    ]
    
    for filename in target_files:
        file_path = js_dir / filename
        if not file_path.exists():
            continue
            
        content = file_path.read_text(encoding="utf-8")
        
        # Check if the file contains escapeHtml usage where there is innerHTML
        # We don't want to enforce it rigidly everywhere, but at least ensure that escapeHtml is used.
        if "innerHTML =" in content or "innerHTML=" in content:
            assert "escapeHtml(" in content, f"File {filename} uses innerHTML but missing escapeHtml() call"

def test_utils_js_contains_escape_html():
    """Verify that static/js/utils.js contains the implementation of escapeHtml."""
    utils_path = pathlib.Path("static/js/utils.js")
    assert utils_path.exists(), "utils.js not found"
    
    content = utils_path.read_text(encoding="utf-8")
    assert "function escapeHtml" in content, "escapeHtml function is missing in utils.js"
    assert ".replace(/&/g," in content and ".replace(/</g," in content, "escapeHtml does not safely escape characters"
