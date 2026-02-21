# -*- coding: utf-8 -*-
"""
Blueprint Hình ảnh & Album, Mộ phần.
Routes: /api/geoapify-key, /api/grave/*, /api/upload-image, /api/gallery/anh1,
        /api/albums, /api/albums/<id>, /images/<path>, /static/images/<path>,
        /family-tree-core.js, /family-tree-ui.js, /genealogy-lineage.js
"""
from flask import Blueprint

gallery_bp = Blueprint('gallery', __name__)


def _call_app(handler_name, *args, **kwargs):
    """Gọi handler từ app (late import tránh circular import)."""
    from app import (
        get_geoapify_api_key,
        update_grave_location,
        upload_grave_image,
        delete_grave_image,
        search_grave,
        upload_image,
        serve_core_js,
        serve_ui_js,
        serve_genealogy_js,
        serve_image_static,
        api_gallery_anh1,
        api_get_albums,
        api_create_album,
        api_update_album,
        api_delete_album,
        api_get_album_images,
        serve_image,
    )
    handlers = {
        'get_geoapify_api_key': get_geoapify_api_key,
        'update_grave_location': update_grave_location,
        'upload_grave_image': upload_grave_image,
        'delete_grave_image': delete_grave_image,
        'search_grave': search_grave,
        'upload_image': upload_image,
        'serve_core_js': serve_core_js,
        'serve_ui_js': serve_ui_js,
        'serve_genealogy_js': serve_genealogy_js,
        'serve_image_static': serve_image_static,
        'api_gallery_anh1': api_gallery_anh1,
        'api_get_albums': api_get_albums,
        'api_create_album': api_create_album,
        'api_update_album': api_update_album,
        'api_delete_album': api_delete_album,
        'api_get_album_images': api_get_album_images,
        'serve_image': serve_image,
    }
    fn = handlers[handler_name]
    return fn(*args, **kwargs)


@gallery_bp.route('/api/geoapify-key')
def get_geoapify_api_key():
    return _call_app('get_geoapify_api_key')


@gallery_bp.route('/api/grave/update-location', methods=['POST'])
def update_grave_location():
    return _call_app('update_grave_location')


@gallery_bp.route('/api/grave/upload-image', methods=['POST'])
def upload_grave_image():
    return _call_app('upload_grave_image')


@gallery_bp.route('/api/grave/delete-image', methods=['POST'])
def delete_grave_image():
    return _call_app('delete_grave_image')


@gallery_bp.route('/api/grave-search', methods=['GET', 'POST'])
def search_grave():
    return _call_app('search_grave')


@gallery_bp.route('/api/upload-image', methods=['POST'])
def upload_image():
    return _call_app('upload_image')


@gallery_bp.route('/family-tree-core.js')
def serve_core_js():
    return _call_app('serve_core_js')


@gallery_bp.route('/family-tree-ui.js')
def serve_ui_js():
    return _call_app('serve_ui_js')


@gallery_bp.route('/genealogy-lineage.js')
def serve_genealogy_js():
    return _call_app('serve_genealogy_js')


@gallery_bp.route('/static/images/<path:filename>')
def serve_image_static(filename):
    return _call_app('serve_image_static', filename)


@gallery_bp.route('/api/gallery/anh1', methods=['GET'])
def api_gallery_anh1():
    return _call_app('api_gallery_anh1')


@gallery_bp.route('/api/albums', methods=['GET'])
def api_get_albums():
    return _call_app('api_get_albums')


@gallery_bp.route('/api/albums', methods=['POST'])
def api_create_album():
    return _call_app('api_create_album')


@gallery_bp.route('/api/albums/<int:album_id>', methods=['PUT'])
def api_update_album(album_id):
    return _call_app('api_update_album', album_id)


@gallery_bp.route('/api/albums/<int:album_id>', methods=['DELETE'])
def api_delete_album(album_id):
    return _call_app('api_delete_album', album_id)


@gallery_bp.route('/api/albums/<int:album_id>/images', methods=['GET'])
def api_get_album_images(album_id):
    return _call_app('api_get_album_images', album_id)


@gallery_bp.route('/images/<path:filename>')
def serve_image(filename):
    return _call_app('serve_image', filename)
