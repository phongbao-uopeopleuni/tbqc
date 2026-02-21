# -*- coding: utf-8 -*-
"""
Blueprint Gia phả & Thành viên rễ.
Routes: /api/family-tree, /api/tree, /api/ancestors/<person_id>, /api/descendants/<person_id>,
        /api/relationships, /api/children/<parent_id>, /api/generations, /api/genealogy/sync
"""
from flask import Blueprint

family_tree_bp = Blueprint('family_tree', __name__)


def _call_app(handler_name, *args, **kwargs):
    """Gọi handler từ app (late import tránh circular import)."""
    from app import (
        get_family_tree,
        get_relationships,
        get_children,
        sync_genealogy_from_members,
        get_tree,
        get_ancestors,
        get_descendants,
        get_generations_api,
    )
    handlers = {
        'get_family_tree': get_family_tree,
        'get_relationships': get_relationships,
        'get_children': get_children,
        'sync_genealogy_from_members': sync_genealogy_from_members,
        'get_tree': get_tree,
        'get_ancestors': get_ancestors,
        'get_descendants': get_descendants,
        'get_generations_api': get_generations_api,
    }
    fn = handlers[handler_name]
    return fn(*args, **kwargs)


@family_tree_bp.route('/api/family-tree')
def get_family_tree():
    return _call_app('get_family_tree')


@family_tree_bp.route('/api/relationships')
def get_relationships():
    return _call_app('get_relationships')


@family_tree_bp.route('/api/children/<parent_id>')
def get_children(parent_id):
    return _call_app('get_children', parent_id)


@family_tree_bp.route('/api/genealogy/sync', methods=['POST'])
def sync_genealogy_from_members():
    return _call_app('sync_genealogy_from_members')


@family_tree_bp.route('/api/tree', methods=['GET'])
def get_tree():
    return _call_app('get_tree')


@family_tree_bp.route('/api/ancestors/<person_id>', methods=['GET'])
def get_ancestors(person_id):
    return _call_app('get_ancestors', person_id)


@family_tree_bp.route('/api/descendants/<person_id>', methods=['GET'])
def get_descendants(person_id):
    return _call_app('get_descendants', person_id)


@family_tree_bp.route('/api/generations', methods=['GET'])
def get_generations_api():
    return _call_app('get_generations_api')
