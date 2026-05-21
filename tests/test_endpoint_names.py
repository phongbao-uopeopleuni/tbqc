"""Endpoint names are a public contract for template url_for usage."""


EXPECTED_ADMIN_ENDPOINTS = {
    "admin_login",
    "admin_logout",
    "admin_dashboard",
    "admin_logs",
    "admin_requests",
    "admin_users",
    "admin_data_management",
    "admin_api_db_info",
    "admin_api_schema",
    "admin_api_table_stats",
    "api_admin_activity_logs",
    "api_admin_reset_logs",
    "api_create_user",
    "api_update_user",
    "api_get_user",
    "api_reset_password",
    "api_delete_user",
    "api_process_request",
    "create_backup",
    "create_backup_api",
    "list_backups_api",
    "download_backup",
    "download_backup_admin",
    "get_csv_data",
    "add_csv_row",
    "update_csv_row",
    "delete_csv_row",
    "get_members_admin",
    "create_member_admin",
    "update_member_admin",
    "delete_member",
}


def test_expected_admin_endpoints_present(flask_app):
    actual = set(flask_app.view_functions)
    missing = EXPECTED_ADMIN_ENDPOINTS - actual
    assert not missing, f"Missing admin endpoints: {sorted(missing)}"


def test_admin_login_logout_endpoint_paths(flask_app):
    rules_by_endpoint = flask_app.url_map._rules_by_endpoint

    login_rules = {
        (tuple(sorted(rule.methods - {"HEAD", "OPTIONS"})), rule.rule)
        for rule in rules_by_endpoint["admin_login"]
    }
    logout_rules = {
        (tuple(sorted(rule.methods - {"HEAD", "OPTIONS"})), rule.rule)
        for rule in rules_by_endpoint["admin_logout"]
    }

    assert login_rules == {(("GET", "POST"), "/admin/login")}
    assert logout_rules == {(("GET",), "/admin/logout")}
