# -*- coding: utf-8 -*-
"""
Blueprint Tin tức & Hoạt động.
Routes: /activities, /activities/<id>, /api/activities, /api/activities/post-login, /api/activities/can-post, ...
TODO: Thêm routes khi có trong app hoặc admin_routes (Bước 2.4).
"""
from flask import Blueprint

activities_bp = Blueprint('activities', __name__)

# Các route sẽ được thêm khi migrate (nếu có trong app)
