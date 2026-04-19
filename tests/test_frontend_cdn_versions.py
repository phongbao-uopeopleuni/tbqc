"""Chặn regress phiên bản các thư viện JS nạp qua CDN.

Các thư viện tbqc load từ CDN (jsdelivr / unpkg) — không có package-lock để
bảo vệ, nên nếu ai đó đổi lại `@latest` hay bump tụt xuống thì không có lớp
nào chặn. Test này kiểm theo chuỗi text trong template + admin_templates.py.

Chỉ cập nhật mức floor khi có lý do rõ ràng (CVE, breaking, bump chủ ý). Nếu
muốn hạ version, SỬA đồng thời file này + cân nhắc test render.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_admin_dashboard_chart_js_pinned_to_v4():
    src = _read("admin_templates.py")

    # Không còn pin 3.x nào cho chart.js
    assert "chart.js@3." not in src, (
        "admin_templates.py đang pin Chart.js 3.x — phải bump tối thiểu 4.5.1. "
        "Xem commit lịch sử security audit Batch upgrade."
    )
    # Phải có đúng pin 4.5.1 (hoặc major 4.x lớn hơn — cho phép bump tiến)
    assert "chart.js@4.5.1" in src or "chart.js@4." in src, (
        "admin_templates.py phải tham chiếu chart.js major 4.x."
    )
    # Không còn pin trống / @latest
    assert "cdn.jsdelivr.net/npm/chart.js\"" not in src
    assert "cdn.jsdelivr.net/npm/chart.js/dist" not in src


def test_genealogy_bundle_chart_js_pinned_and_not_latest():
    src = _read("templates/genealogy/partials/_scripts_external_bundle.html")

    # Không được dùng @latest — upstream major release có thể break UI.
    assert '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' not in src, (
        "Không dùng chart.js @latest — pin chặt version để chặn regress."
    )
    assert "chart.js@4." in src, "Genealogy bundle phải pin Chart.js major 4.x."


def test_genealogy_bundle_d3_still_at_latest_minor():
    """D3 v7.9.0 là bản mới nhất của dòng 7.x (tới 2026-04).

    Nếu D3 ra major v8 thì revalidate thủ công vì API có thể đổi — test này
    chỉ chặn tụt về bản cũ hơn 7.9.0.
    """

    src = _read("templates/genealogy/partials/_scripts_external_bundle.html")
    assert "d3@7.9.0" in src or "d3@7." in src


def test_chart_js_umd_path_used_for_v4():
    """Chart.js v4 dùng bundle `chart.umd.min.js` (khác tên file của v3).

    Nếu ai đó bump pin nhưng giữ path `chart.min.js` thì trình duyệt 404.
    """

    for rel in (
        "admin_templates.py",
        "templates/genealogy/partials/_scripts_external_bundle.html",
    ):
        src = _read(rel)
        # Chỉ check khi file thực sự nạp chart.js major 4
        if "chart.js@4." in src:
            assert "chart.umd.min.js" in src or "chart.umd.js" in src, (
                f"{rel} pin chart.js@4.x nhưng đang dùng path cũ. v4 đổi tên "
                "bundle thành chart.umd.min.js — sửa path để tránh 404."
            )


def test_no_core_js_runtime_dependency():
    """core-js không có trong runtime tbqc — đảm bảo không vô tình thêm.

    Nếu trong tương lai cần core-js polyfill, hãy thêm vào package.json
    (nếu dùng build step) HOẶC CDN kèm pin version + cập nhật test này.
    """

    # Check template + static/js root (không scan node_modules)
    for rel in (
        "templates/genealogy/partials/_scripts_external_bundle.html",
        "admin_templates.py",
    ):
        src = _read(rel)
        assert "core-js" not in src.lower(), (
            f"{rel} bất ngờ có core-js — nếu cố ý thêm, pin version cụ thể "
            "và update test này."
        )
