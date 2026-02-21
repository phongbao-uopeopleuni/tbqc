# -*- coding: utf-8 -*-
"""
Blueprint Quản lý hồ sơ cá nhân (Person CRUD).
Routes: /api/person/<id>, /api/persons, /api/persons/batch, /api/search, /api/person/<id>/sync,
        /api/edit-requests, /api/fix/p-1-1-parents, /api/genealogy/update-info, ...
"""
from flask import Blueprint

persons_bp = Blueprint('persons', __name__)


def _call_app(handler_name, *args, **kwargs):
    """Gọi handler từ app (late import tránh circular import)."""
    from app import (
        get_persons,
        get_person,
        search_persons,
        create_edit_request,
        delete_person,
        update_person,
        sync_person,
        create_person,
        update_person_members,
        fix_p1_1_parents,
        update_genealogy_info,
        delete_persons_batch,
    )
    handlers = {
        'get_persons': get_persons,
        'get_person': get_person,
        'search_persons': search_persons,
        'create_edit_request': create_edit_request,
        'delete_person': delete_person,
        'update_person': update_person,
        'sync_person': sync_person,
        'create_person': create_person,
        'update_person_members': update_person_members,
        'fix_p1_1_parents': fix_p1_1_parents,
        'update_genealogy_info': update_genealogy_info,
        'delete_persons_batch': delete_persons_batch,
    }
    fn = handlers[handler_name]
    return fn(*args, **kwargs)


@persons_bp.route('/api/persons')
def get_persons():
    return _call_app('get_persons')


@persons_bp.route('/api/person/<person_id>')
def get_person(person_id):
    return _call_app('get_person', person_id)


@persons_bp.route('/api/search', methods=['GET'])
def search_persons():
    return _call_app('search_persons')


@persons_bp.route('/api/edit-requests', methods=['POST'])
def create_edit_request():
    return _call_app('create_edit_request')


@persons_bp.route('/api/person/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    return _call_app('delete_person', person_id)


@persons_bp.route('/api/person/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    return _call_app('update_person', person_id)


@persons_bp.route('/api/person/<int:person_id>/sync', methods=['POST'])
def sync_person(person_id):
    return _call_app('sync_person', person_id)


@persons_bp.route('/api/persons', methods=['POST'])
def create_person():
    return _call_app('create_person')


@persons_bp.route('/api/persons/<person_id>', methods=['PUT'])
def update_person_members(person_id):
    return _call_app('update_person_members', person_id)


@persons_bp.route('/api/fix/p-1-1-parents', methods=['GET', 'POST'])
def fix_p1_1_parents():
    return _call_app('fix_p1_1_parents')


@persons_bp.route('/api/genealogy/update-info', methods=['POST'])
def update_genealogy_info():
    return _call_app('update_genealogy_info')


@persons_bp.route('/api/persons/batch', methods=['DELETE'])
def delete_persons_batch():
    return _call_app('delete_persons_batch')
