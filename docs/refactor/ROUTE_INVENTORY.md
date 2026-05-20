# Route Inventory

> Day du route runtime cua tbqc. Cot Risk Tier va Domain de input cho Phase 1/2/3.
> Filled: Step 3, 2026-05-20. Total: 113 routes (15 app.py + 28 admin_routes + 6 main + 5 auth +
> 7 activities + 8 family_tree + 12 persons + 8 members_portal + 19 gallery + 1 admin_bp + 4 marriage_api).

## Format

| Cot | Y nghia |
|---|---|
| URL | Route rule |
| Method | GET/POST/PUT/DELETE |
| Endpoint | Flask endpoint name (input cho `url_for`) |
| Handler | Function name (file:line) |
| Pattern | `@app.route` \| `register` \| `blueprint` |
| Domain | Phase 1 domain group |
| Risk | P0 \| P1 \| P2 |
| Auth | `none` \| `login_required` \| `admin_required` \| `permission_required:X` \| `password_in_body` \| `internal_secret` \| `members_session+password` \| `token_optional` |
| Audit | Y \| N |
| HasTest | Y \| N \| partial |

## Risk tier

```
P0 = auth, admin session/token/password, DB write, file write/delete,
     backup create/restore, bulk update/export sensitive data
P1 = read API co contract ro, admin read/write read-back,
     route du lieu quan trong nhung blast radius vua
P2 = health, static-ish, debug/internal, utility low-risk
```

## NOTES tong quat (phat hien o Step 3)

```
[CONFLICT] /api/activities/can-post duoc dang ky 2 lan:
  - admin_routes.py:262  endpoint=api_activities_can_post
  - blueprints/activities.py:165  endpoint=activities.api_activities_can_post
  Blueprint dang ky SAU admin_routes => activities.api_activities_can_post wins cho routing.
  admin_routes endpoint ton tai nhung khong co the reach qua URL.

[MISSING AUTH] blueprints/persons.py: delete_person, create_person,
  delete_persons_batch, update_person_members dung password_in_body (khong Flask-Login).
  update_person, sync_person dung @login_required trong service layer.

[NO AUTH] admin_routes.py:246 /admin/activities — khong co decorator, trang render HTML.
  [RISK] co the truy cap ma khong dang nhap.

[NO AUDIT] admin_routes.py: api_process_request (P0 mutation), api_reset_password (P0 mutation) — 
  khong co log_activity call. Gap can fill o Phase 0b audit tests.

[DUAL BACKUP] Co 2 backup create endpoint:
  app.py:1614 /api/admin/backup (POST) — auth=password_in_body
  admin_routes.py:1560 /admin/api/backup (POST) — auth=permission_required:canViewDashboard
  Ca 2 ton tai dong thoi. Can chon 1 canonical o Phase 1.
```

---

## 1. app.py routes (@app.route) — 15 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/stats | GET | get_stats | get_stats | app.py:1263 | @app.route | infra | P1 | none | N | Y |
| /api/admin/users | GET,POST | api_admin_users | api_admin_users | app.py:1287 | @app.route | admin_users | P0 | login_required | N | partial |
| /api/admin/users/\<int:user_id\> | GET,PUT,DELETE | api_admin_user_detail | api_admin_user_detail | app.py:1338 | @app.route | admin_users | P0 | login_required | N | N |
| /api/admin/verify-password | POST | verify_password_api | verify_password_api | app.py:1413 | @app.route | admin_auth | P0 | login_required | N | N |
| /api/admin/activity-logs | GET | api_admin_activity_logs | api_admin_activity_logs | app.py:1434 | @app.route | admin_logs | P1 | login_required | N | N |
| /api/admin/reset-logs | POST | api_admin_reset_logs | api_admin_reset_logs | app.py:1534 | @app.route | admin_logs | P0 | login_required | Y | N |
| /api/admin/code-graph/rescan | POST | api_admin_code_graph_rescan | api_admin_code_graph_rescan | app.py:1584 | @app.route | admin_dashboard | P1 | login_required | N | N |
| /api/admin/backup | POST | create_backup_api | create_backup_api | app.py:1614 | @app.route | admin_backup | P0 | password_in_body | N | partial |
| /api/admin/backups | GET | list_backups_api | list_backups_api | app.py:1619 | @app.route | admin_backup | P1 | none | N | partial |
| /api/admin/backup/\<filename\> | GET | download_backup | download_backup | app.py:1624 | @app.route | admin_backup | P0 | none | N | Y |
| /api/health | GET | api_health | api_health | app.py:1629 | @app.route | infra | P2 | none | N | Y |
| /api/external-posts | GET | get_external_posts | get_external_posts | app.py:1687 | @app.route | infra | P2 | none | N | Y |
| /api/external-posts/clear-cache | POST | clear_external_posts_cache | clear_external_posts_cache | app.py:1721 | @app.route | infra | P1 | token_optional | N | Y |
| /api/external-posts/refresh | GET,POST | refresh_external_posts | refresh_external_posts | app.py:1731 | @app.route | infra | P1 | token_optional | N | partial |
| /api/stats/members | GET | api_member_stats | api_member_stats | app.py:1759 | @app.route | members_gate | P1 | none | N | Y |

## 2. admin_routes.py (register pattern) — 28 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /admin/login | GET,POST | admin_login | admin_login | admin_routes.py:47 | register | admin_auth | P0 | none | Y | Y |
| /admin/logout | GET | admin_logout | admin_logout | admin_routes.py:169 | register | admin_auth | P0 | login_required | N | N |
| /admin/dashboard | GET | admin_dashboard | admin_dashboard | admin_routes.py:176 | register | admin_dashboard | P1 | permission_required:canViewDashboard | N | N |
| /admin/activities | GET | admin_activities_page | admin_activities_page | admin_routes.py:246 | register | admin_activities | P1 | none | N | N |
| /api/activities/can-post | GET | api_activities_can_post | api_activities_can_post | admin_routes.py:262 | register | admin_activities | P2 | none | N | partial |
| /admin/requests | GET | admin_requests | admin_requests | admin_routes.py:270 | register | admin_requests | P1 | permission_required:canViewDashboard | N | N |
| /admin/api/requests/\<int:request_id\>/process | POST | api_process_request | api_process_request | admin_routes.py:303 | register | admin_requests | P0 | permission_required:canEditGenealogy | N | N |
| /admin/users | GET | admin_users | admin_users | admin_routes.py:336 | register | admin_users | P1 | admin_required | N | N |
| /admin/api/users | POST | api_create_user | api_create_user | admin_routes.py:364 | register | admin_users | P0 | admin_required | Y | N |
| /admin/api/users/\<int:user_id\> | PUT | api_update_user | api_update_user | admin_routes.py:482 | register | admin_users | P0 | admin_required | Y | N |
| /admin/api/users/\<int:user_id\> | GET | api_get_user | api_get_user | admin_routes.py:577 | register | admin_users | P1 | admin_required | N | N |
| /admin/api/users/\<int:user_id\>/reset-password | POST | api_reset_password | api_reset_password | admin_routes.py:629 | register | admin_users | P0 | admin_required | N | N |
| /admin/api/users/\<int:user_id\> | DELETE | api_delete_user | api_delete_user | admin_routes.py:668 | register | admin_users | P0 | admin_required | Y | N |
| /admin/data-management | GET | admin_data_management | admin_data_management | admin_routes.py:722 | register | admin_data | P1 | permission_required:canViewDashboard | N | N |
| /admin/logs | GET | admin_logs | admin_logs | admin_routes.py:728 | register | admin_logs | P1 | login_required | N | N |
| /admin/api/db-info | GET | admin_api_db_info | admin_api_db_info | admin_routes.py:739 | register | admin_data | P1 | login_required | N | N |
| /admin/api/schema | GET | admin_api_schema | admin_api_schema | admin_routes.py:775 | register | admin_data | P1 | login_required | N | N |
| /admin/api/table-stats | GET | admin_api_table_stats | admin_api_table_stats | admin_routes.py:847 | register | admin_data | P1 | login_required | N | partial |
| /admin/api/csv-data/\<sheet_name\> | GET | get_csv_data | get_csv_data | admin_routes.py:944 | register | admin_data | P1 | permission_required:canViewDashboard | N | N |
| /admin/api/csv-data/\<sheet_name\> | POST | add_csv_row | add_csv_row | admin_routes.py:953 | register | admin_data | P0 | permission_required:canViewDashboard | N | N |
| /admin/api/csv-data/\<sheet_name\>/\<int:row_index\> | PUT | update_csv_row | update_csv_row | admin_routes.py:1003 | register | admin_data | P0 | permission_required:canViewDashboard | N | N |
| /admin/api/csv-data/\<sheet_name\>/\<int:row_index\> | DELETE | delete_csv_row | delete_csv_row | admin_routes.py:1026 | register | admin_data | P0 | permission_required:canViewDashboard | N | N |
| /admin/api/members | GET | get_members_admin | get_members_admin | admin_routes.py:1045 | register | admin_members | P1 | permission_required:canViewDashboard | N | N |
| /admin/api/members | POST | create_member_admin | create_member_admin | admin_routes.py:1188 | register | admin_members | P0 | permission_required:canViewDashboard | Y | N |
| /admin/api/members/\<person_id\> | PUT | update_member_admin | update_member_admin | admin_routes.py:1354 | register | admin_members | P0 | permission_required:canViewDashboard | Y | N |
| /admin/api/members/\<person_id\> | DELETE | delete_member | delete_member | admin_routes.py:1504 | register | admin_members | P0 | permission_required:canViewDashboard | Y | N |
| /admin/api/backup | POST | create_backup | create_backup | admin_routes.py:1560 | register | admin_backup | P0 | permission_required:canViewDashboard | N | partial |
| /admin/api/backup/download/\<filename\> | GET | download_backup_admin | download_backup_admin | admin_routes.py:1621 | register | admin_backup | P0 | permission_required:canViewDashboard | N | partial |

## 3. blueprints/main.py — 6 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| / | GET | main.index | index | blueprints/main.py:13 | blueprint | public | P1 | none | N | Y |
| /api/genealogy/verify-passphrase | POST | main.verify_genealogy_passphrase | verify_genealogy_passphrase | blueprints/main.py:22 | blueprint | members_gate | P0 | none | N | Y |
| /genealogy | GET | main.genealogy_page | genealogy_page | blueprints/main.py:38 | blueprint | public | P1 | none | N | Y |
| /contact | GET | main.contact_page | contact_page | blueprints/main.py:49 | blueprint | public | P2 | none | N | N |
| /documents | GET | main.documents_page | documents_page | blueprints/main.py:58 | blueprint | public | P2 | none | N | N |
| /privacy | GET | main.privacy_page | privacy_page | blueprints/main.py:67 | blueprint | public | P2 | none | N | Y |

## 4. blueprints/auth.py — 5 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /login | GET | auth.login_page | login_page | blueprints/auth.py:21 | blueprint | admin_auth | P2 | none | N | N |
| /admin/login-page | GET | auth.admin_login_page | admin_login_page | blueprints/auth.py:28 | blueprint | admin_auth | P2 | none | N | N |
| /api/login | POST | auth.api_login | api_login | blueprints/auth.py:38 | blueprint | admin_auth | P0 | none | Y | Y |
| /api/logout | POST | auth.api_logout | api_logout | blueprints/auth.py:111 | blueprint | admin_auth | P0 | none | N | N |
| /api/current-user | GET | auth.get_current_user | get_current_user | blueprints/auth.py:117 | blueprint | admin_auth | P1 | none | N | N |

## 5. blueprints/activities.py — 7 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /activities | GET | activities.activities_page | activities_page | blueprints/activities.py:62 | blueprint | activities | P2 | none | N | Y |
| /activities/\<int:activity_id\> | GET | activities.activity_detail_page | activity_detail_page | blueprints/activities.py:68 | blueprint | activities | P2 | none | N | Y |
| /editor | GET | activities.editor_page | editor_page | blueprints/activities.py:156 | blueprint | activities | P1 | none | N | N |
| /api/activities/can-post | GET | activities.api_activities_can_post | api_activities_can_post | blueprints/activities.py:165 | blueprint | activities | P2 | none | N | partial |
| /api/activities/post-login | POST | activities.api_activities_post_login | api_activities_post_login | blueprints/activities.py:174 | blueprint | activities | P0 | none | N | N |
| /api/activities | GET,POST | activities.api_activities | api_activities | blueprints/activities.py:200 | blueprint | activities | P1 | none | N | N |
| /api/activities/\<int:activity_id\> | GET,PUT,DELETE | activities.api_activity_detail | api_activity_detail | blueprints/activities.py:293 | blueprint | activities | P1 | none | N | N |

## 6. blueprints/family_tree.py — 8 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/family-tree | GET | family_tree.get_family_tree | get_family_tree | blueprints/family_tree.py:42 | blueprint | family_tree | P1 | none | N | partial |
| /api/relationships | GET | family_tree.get_relationships | get_relationships | blueprints/family_tree.py:48 | blueprint | family_tree | P1 | none | N | partial |
| /api/children/\<parent_id\> | GET | family_tree.get_children | get_children | blueprints/family_tree.py:54 | blueprint | family_tree | P1 | none | N | Y |
| /api/genealogy/sync | POST | family_tree.sync_genealogy_from_members | sync_genealogy_from_members | blueprints/family_tree.py:60 | blueprint | family_tree | P0 | none | N | Y |
| /api/tree | GET | family_tree.get_tree | get_tree | blueprints/family_tree.py:66 | blueprint | family_tree | P1 | none | N | N |
| /api/ancestors/\<person_id\> | GET | family_tree.get_ancestors | get_ancestors | blueprints/family_tree.py:72 | blueprint | family_tree | P1 | none | N | Y |
| /api/descendants/\<person_id\> | GET | family_tree.get_descendants | get_descendants | blueprints/family_tree.py:78 | blueprint | family_tree | P1 | none | N | Y |
| /api/generations | GET | family_tree.get_generations_api | get_generations_api | blueprints/family_tree.py:84 | blueprint | family_tree | P1 | none | N | N |

## 7. blueprints/persons.py — 12 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/persons | GET | persons.get_persons | get_persons | blueprints/persons.py:54 | blueprint | persons | P1 | none | N | Y |
| /api/person/\<person_id\> | GET | persons.get_person | get_person | blueprints/persons.py:60 | blueprint | persons | P1 | none | N | Y |
| /api/search | GET | persons.search_persons | search_persons | blueprints/persons.py:66 | blueprint | persons | P1 | none | N | N |
| /api/edit-requests | POST | persons.create_edit_request | create_edit_request | blueprints/persons.py:72 | blueprint | persons | P1 | none | N | partial |
| /api/person/\<int:person_id\> | DELETE | persons.delete_person | delete_person | blueprints/persons.py:77 | blueprint | persons | P0 | password_in_body | N | N |
| /api/person/\<int:person_id\> | PUT | persons.update_person | update_person | blueprints/persons.py:82 | blueprint | persons | P0 | login_required | N | N |
| /api/person/\<int:person_id\>/sync | POST | persons.sync_person | sync_person | blueprints/persons.py:87 | blueprint | persons | P0 | login_required | N | N |
| /api/persons | POST | persons.create_person | create_person | blueprints/persons.py:92 | blueprint | persons | P0 | password_in_body | N | N |
| /api/persons/\<person_id\> | PUT | persons.update_person_members | update_person_members | blueprints/persons.py:97 | blueprint | persons | P0 | password_in_body | N | N |
| /api/fix/p-1-1-parents | GET,POST | persons.fix_p1_1_parents | fix_p1_1_parents | blueprints/persons.py:102 | blueprint | persons | P1 | internal_secret | N | N |
| /api/genealogy/update-info | POST | persons.update_genealogy_info | update_genealogy_info | blueprints/persons.py:110 | blueprint | persons | P1 | internal_secret | N | partial |
| /api/persons/batch | DELETE | persons.delete_persons_batch | delete_persons_batch | blueprints/persons.py:118 | blueprint | persons | P0 | password_in_body | N | N |

## 8. blueprints/members_portal.py — 8 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /members | GET | members_portal.members | members | blueprints/members_portal.py:24 | blueprint | members_gate | P1 | none | N | partial |
| /members/verify | POST | members_portal.members_verify | members_verify | blueprints/members_portal.py:35 | blueprint | members_gate | P0 | none | N | Y |
| /members/logout | GET,POST | members_portal.members_logout | members_logout | blueprints/members_portal.py:91 | blueprint | members_gate | P2 | none | N | N |
| /api/members | GET | members_portal.get_members | get_members | blueprints/members_portal.py:101 | blueprint | members_gate | P1 | members_session | N | Y |
| /members/export/excel | GET | members_portal.export_members_excel | export_members_excel | blueprints/members_portal.py:418 | blueprint | members_gate | P1 | none | N | N |
| /api/members/bulk-update-branch | POST | members_portal.bulk_update_members_branch | bulk_update_members_branch | blueprints/members_portal.py:463 | blueprint | members_gate | P0 | members_session+password | N | N |
| /members/template/Template_updatetbqc.xlsx | GET | members_portal.download_template_update_sll | download_template_update_sll | blueprints/members_portal.py:932 | blueprint | members_gate | P2 | none | N | N |
| /api/members/bulk-update-sll | POST | members_portal.bulk_update_members_sll | bulk_update_members_sll | blueprints/members_portal.py:944 | blueprint | members_gate | P0 | members_session+password | N | N |

## 9. blueprints/gallery.py — 19 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/geoapify-key | GET | gallery.get_geoapify_api_key | get_geoapify_api_key | blueprints/gallery.py:78 | blueprint | gallery | P1 | none | N | N |
| /api/grave/update-location | POST | gallery.update_grave_location | update_grave_location | blueprints/gallery.py:84 | blueprint | gallery | P0 | internal_secret | N | Y |
| /api/grave/upload-image | POST | gallery.upload_grave_image | upload_grave_image | blueprints/gallery.py:92 | blueprint | gallery | P0 | internal_secret | N | Y |
| /api/grave/delete-image | POST | gallery.delete_grave_image | delete_grave_image | blueprints/gallery.py:100 | blueprint | gallery | P0 | password_in_body | N | Y |
| /api/grave-search | GET,POST | gallery.search_grave | search_grave | blueprints/gallery.py:105 | blueprint | gallery | P2 | none | N | partial |
| /api/upload-image | POST | gallery.upload_image | upload_image | blueprints/gallery.py:110 | blueprint | gallery | P0 | none | N | partial |
| /family-tree-core.js | GET | gallery.serve_core_js | serve_core_js | blueprints/gallery.py:115 | blueprint | static_serve | P2 | none | N | N |
| /family-tree-ui.js | GET | gallery.serve_ui_js | serve_ui_js | blueprints/gallery.py:120 | blueprint | static_serve | P2 | none | N | N |
| /genealogy-lineage.js | GET | gallery.serve_genealogy_js | serve_genealogy_js | blueprints/gallery.py:125 | blueprint | static_serve | P2 | none | N | N |
| /static/images/\<path:filename\> | GET | gallery.serve_image_static | serve_image_static | blueprints/gallery.py:130 | blueprint | static_serve | P2 | none | N | N |
| /api/gallery/anh1 | GET | gallery.api_gallery_anh1 | api_gallery_anh1 | blueprints/gallery.py:136 | blueprint | gallery | P2 | none | N | N |
| /api/albums/verify-password | POST | gallery.api_verify_album_password | api_verify_album_password | blueprints/gallery.py:141 | blueprint | gallery | P0 | none | N | Y |
| /api/albums | GET | gallery.api_get_albums | api_get_albums | blueprints/gallery.py:146 | blueprint | gallery | P1 | none | N | Y |
| /api/albums | POST | gallery.api_create_album | api_create_album | blueprints/gallery.py:152 | blueprint | gallery | P0 | none | N | N |
| /api/albums/\<int:album_id\> | PUT | gallery.api_update_album | api_update_album | blueprints/gallery.py:157 | blueprint | gallery | P0 | none | N | N |
| /api/albums/\<int:album_id\> | DELETE | gallery.api_delete_album | api_delete_album | blueprints/gallery.py:162 | blueprint | gallery | P0 | none | N | N |
| /api/albums/\<int:album_id\>/images | GET | gallery.api_get_album_images | api_get_album_images | blueprints/gallery.py:167 | blueprint | gallery | P1 | none | N | N |
| /api/albums/\<int:album_id\>/images | DELETE | gallery.api_delete_album_images | api_delete_album_images | blueprints/gallery.py:172 | blueprint | gallery | P0 | none | N | N |
| /images/\<path:filename\> | GET | gallery.serve_image | serve_image | blueprints/gallery.py:177 | blueprint | static_serve | P2 | none | N | N |

## 10. blueprints/admin.py — 1 route

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/admin/sync-tbqc-accounts | POST | admin.api_sync_tbqc_accounts | api_sync_tbqc_accounts | blueprints/admin.py:16 | blueprint | admin_users | P0 | login_required | N | N |

## 11. marriage_api.py (register pattern) — 4 routes

| URL | Method | Endpoint | Handler | File:Line | Pattern | Domain | Risk | Auth | Audit | HasTest |
|---|---|---|---|---|---|---|---|---|---|---|
| /api/person/\<person_id\>/spouses | GET | get_person_spouses | get_person_spouses | marriage_api.py:26 | register | marriage | P1 | login_required | N | N |
| /api/person/\<person_id\>/spouses | POST | create_spouse | create_spouse | marriage_api.py:66 | register | marriage | P0 | permission_required:canEditGenealogy | Y | N |
| /api/marriages/\<int:marriage_id\> | PUT | update_spouse | update_spouse | marriage_api.py:109 | register | marriage | P0 | permission_required:canEditGenealogy | Y | N |
| /api/marriages/\<int:marriage_id\> | DELETE | delete_spouse | delete_spouse | marriage_api.py:160 | register | marriage | P0 | permission_required:canEditGenealogy | Y | N |

---

## Summary

| Source | Routes | P0 | P1 | P2 |
|---|---|---|---|---|
| app.py | 15 | 5 | 8 | 2 |
| admin_routes.py | 28 | 14 | 13 | 1 |
| blueprints/main.py | 6 | 1 | 2 | 3 |
| blueprints/auth.py | 5 | 2 | 1 | 2 |
| blueprints/activities.py | 7 | 1 | 2 | 4 |
| blueprints/family_tree.py | 8 | 1 | 7 | 0 |
| blueprints/persons.py | 12 | 7 | 4 | 1 |
| blueprints/members_portal.py | 8 | 3 | 3 | 2 |
| blueprints/gallery.py | 19 | 8 | 4 | 7 |
| blueprints/admin.py | 1 | 1 | 0 | 0 |
| marriage_api.py | 4 | 3 | 1 | 0 |
| **TOTAL** | **113** | **46** | **45** | **22** |

## Domain groups (cho Phase 1/2 split)

```
admin_auth        : /admin/login, /admin/logout, /login, /admin/login-page, /api/login, /api/logout, /api/current-user, /api/admin/verify-password
admin_dashboard   : /admin/dashboard, /api/admin/code-graph/rescan
admin_users       : /admin/users, /admin/api/users/*, /api/admin/users/*, /api/admin/sync-tbqc-accounts
admin_requests    : /admin/requests, /admin/api/requests/*/process
admin_members     : /admin/api/members/*
admin_data        : /admin/data-management, /admin/api/db-info, /admin/api/schema, /admin/api/table-stats, /admin/api/csv-data/*
admin_logs        : /admin/logs, /api/admin/activity-logs, /api/admin/reset-logs
admin_backup      : /api/admin/backup, /api/admin/backups, /api/admin/backup/<f>, /admin/api/backup, /admin/api/backup/download/<f>
admin_activities  : /admin/activities, /api/activities/can-post (admin_routes instance)
public            : /, /genealogy, /contact, /documents, /privacy
members_gate      : /members/*, /api/members, /api/members/bulk-update-*, /api/stats/members, /api/genealogy/verify-passphrase
persons           : /api/persons, /api/person/*, /api/search, /api/edit-requests, /api/persons/batch, /api/fix/p-1-1-parents, /api/genealogy/update-info
family_tree       : /api/family-tree, /api/relationships, /api/children/*, /api/genealogy/sync, /api/tree, /api/ancestors/*, /api/descendants/*, /api/generations
activities        : /activities, /activities/*, /editor, /api/activities/*
gallery           : /api/grave/*, /api/grave-search, /api/upload-image, /api/geoapify-key, /api/albums/*, /api/gallery/anh1
marriage          : /api/person/*/spouses, /api/marriages/*
static_serve      : /family-tree-core.js, /family-tree-ui.js, /genealogy-lineage.js, /static/images/*, /images/*
infra             : /api/health, /api/stats, /api/external-posts/*, /api/stats/members
```
