# -*- coding: utf-8 -*-
import auth
from auth import User

from services import site_announcements


def _set_logged_in_admin(client):
    with client.session_transaction() as session:
        session["_user_id"] = "1"
        session["_fresh"] = True
        session["_id"] = "announcements-admin-session"


def test_homepage_renders_custom_announcements(client, monkeypatch, tmp_path):
    storage = tmp_path / "site_announcements.json"
    monkeypatch.setattr(site_announcements, "ANNOUNCEMENTS_FILE", storage)
    site_announcements.save_announcement_settings(
        ["Họp mặt hậu duệ tháng 9", "", "Cập nhật gia phả mới"],
        {
            "xuan": {
                "title": "GIỖ XUÂN 2027",
                "lunar_label": "09/2 ÂL",
                "date": "2027-04-01",
            },
            "thu": {
                "title": "GIỖ THU 2027",
                "lunar_label": "04/7 ÂL",
                "date": "2027-08-20",
            },
        },
    )

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Họp mặt hậu duệ tháng 9" in html
    assert "Cập nhật gia phả mới" in html
    assert "GIỖ XUÂN 2027" in html
    assert "01/04/2027" in html
    assert 'data-target-date="2027-08-20"' in html


def test_admin_announcements_page_and_save(flask_app, monkeypatch, tmp_path):
    storage = tmp_path / "site_announcements.json"
    monkeypatch.setattr(site_announcements, "ANNOUNCEMENTS_FILE", storage)
    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(1, "admin.seed", "admin", full_name="Admin Seed"),
    )

    client = flask_app.test_client()
    _set_logged_in_admin(client)

    page_response = client.get("/admin/announcements")
    assert page_response.status_code == 200
    assert "Quản lý Thông báo" in page_response.get_data(as_text=True)

    payload = {
        "lines": [
            "Dòng 1",
            "Dòng 2",
            "",
            "Dòng 4",
            "Dòng 5",
            "Dòng 6",
            "Dòng 7",
            "Dòng 8",
            "Dòng 9",
            "Dòng 10",
            "Dòng 11 sẽ bị bỏ qua",
        ],
        "memorials": {
            "xuan": {
                "title": "GIỖ XUÂN 2028",
                "lunar_label": "10/2 ÂL",
                "date": "2028-03-30",
            },
            "thu": {
                "title": "GIỖ THU 2028",
                "lunar_label": "06/7 ÂL",
                "date": "2028-08-11",
            },
        },
    }
    save_response = client.post("/admin/api/announcements", json=payload)

    assert save_response.status_code == 200
    data = save_response.get_json()
    assert data["success"] is True
    assert len(data["lines"]) == site_announcements.MAX_ANNOUNCEMENTS
    assert data["lines"][0] == "Dòng 1"
    assert data["lines"][-1] == "Dòng 10"
    assert "Dòng 11 sẽ bị bỏ qua" not in data["lines"]
    assert data["memorials"]["xuan"]["title"] == "GIỖ XUÂN 2028"
    assert data["memorials"]["thu"]["date"] == "2028-08-11"
    assert data["memorials"]["thu"]["display_date"] == "11/08/2028"

    stored = site_announcements.load_announcement_settings()
    assert stored["lines"][1] == "Dòng 2"
    assert stored["lines"][-1] == "Dòng 10"
    assert stored["memorials"]["xuan"]["date"] == "2028-03-30"


def test_admin_announcements_reject_invalid_payload(flask_app, monkeypatch, tmp_path):
    storage = tmp_path / "site_announcements.json"
    monkeypatch.setattr(site_announcements, "ANNOUNCEMENTS_FILE", storage)
    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(1, "admin.seed", "admin", full_name="Admin Seed"),
    )

    client = flask_app.test_client()
    _set_logged_in_admin(client)

    response = client.post(
        "/admin/api/announcements",
        json={"lines": "not-a-list", "memorials": {}},
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False


def test_admin_announcements_reject_invalid_memorial_payload(flask_app, monkeypatch, tmp_path):
    storage = tmp_path / "site_announcements.json"
    monkeypatch.setattr(site_announcements, "ANNOUNCEMENTS_FILE", storage)
    monkeypatch.setattr(
        auth,
        "get_user_by_id",
        lambda user_id: User(1, "admin.seed", "admin", full_name="Admin Seed"),
    )

    client = flask_app.test_client()
    _set_logged_in_admin(client)

    response = client.post(
        "/admin/api/announcements",
        json={"lines": [], "memorials": "not-a-dict"},
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
