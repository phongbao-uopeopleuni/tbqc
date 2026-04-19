"""Bug #13 — Dependencies có CVE đã công bố.

Mục tiêu: chặn việc downgrade vô tình về các bản dính CVE. Test chỉ so sánh
phiên bản đang cài (không thay đổi môi trường), để vừa bảo vệ CI vừa không làm
ảnh hưởng logic/vận hành website.

Các CVE tham chiếu:
- requests < 2.32.4: CVE-2024-35195, CVE-2024-47081
- flask-cors < 5.0.0: CVE-2024-6839, CVE-2024-6221, CVE-2024-1681
- Werkzeug < 3.0.3: CVE-2024-34069, CVE-2024-49766, CVE-2024-49767
- flask < 3.0.3: kéo theo Werkzeug cũ
- mysql-connector-python < 8.4.0: CVE-2024-21272, CVE-2024-21275
- Pillow < 10.3.0: CVE-2024-28219
"""

from __future__ import annotations

from importlib.metadata import version as pkg_version, PackageNotFoundError

import pytest


def _parse(v: str) -> tuple[int, ...]:
    """Parse PEP 440-ish versions into comparable tuples.

    Bỏ qua suffix rc/post/dev để so sánh theo số chính (đủ cho CVE floor).
    """

    out: list[int] = []
    for part in v.split("+", 1)[0].split("."):
        # Tách ký tự không phải số (vd '3rc1' -> '3')
        num = ""
        for ch in part:
            if ch.isdigit():
                num += ch
            else:
                break
        if num == "":
            break
        out.append(int(num))
    return tuple(out)


# (package name, minimum safe version)
_FLOORS = [
    ("requests", "2.32.4"),
    ("Flask-Cors", "5.0.0"),
    ("Werkzeug", "3.0.3"),
    ("flask", "3.0.3"),
    ("mysql-connector-python", "8.4.0"),
    ("Pillow", "10.3.0"),
]


@pytest.mark.parametrize("pkg,floor", _FLOORS)
def test_dependency_is_at_or_above_cve_floor(pkg: str, floor: str) -> None:
    try:
        installed = pkg_version(pkg)
    except PackageNotFoundError:
        pytest.skip(f"{pkg} chưa được cài trong môi trường test")
        return

    assert _parse(installed) >= _parse(floor), (
        f"{pkg}=={installed} thấp hơn mức an toàn {floor}. "
        "Bump requirements.txt hoặc reinstall (xem Bug #13 trong security audit)."
    )


def test_requirements_txt_still_pins_cve_fixed_versions() -> None:
    """Bảo vệ file requirements.txt trước commit vô tình.

    Không so sánh bản cài đặt — chỉ kiểm tra text file để phát hiện ngay việc
    rollback. Giữ kiểm tra ở mức substring để chịu được khoảng trắng / xuống
    dòng / comment đi kèm.
    """

    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    content = (root / "requirements.txt").read_text(encoding="utf-8")

    # Các dòng pin bắt buộc cho Batch C của security audit.
    must_contain = [
        "flask==3.0.3",
        "flask-cors==5.0.1",
        "requests==2.32.4",
        "mysql-connector-python==8.4.0",
    ]
    missing = [p for p in must_contain if p not in content]
    assert not missing, (
        "requirements.txt thiếu các pin bảo mật đã bump ở Bug #13: "
        f"{missing}. KHÔNG downgrade nếu không có phân tích CVE thay thế."
    )

    # Không cho phép pin lại các bản dính CVE.
    forbidden = [
        "flask==3.0.0",
        "flask-cors==4.0.0",
        "requests==2.31.0",
        "mysql-connector-python==8.2.0",
    ]
    present = [p for p in forbidden if p in content]
    assert not present, (
        f"requirements.txt đang pin lại bản có CVE: {present}. "
        "Xem docs/security-audit-bugs canvas #13."
    )
