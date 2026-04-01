# -*- coding: utf-8 -*-
"""Family tree API handlers (no circular imports from app)."""
import logging

from flask import jsonify, request
from mysql.connector import Error

from db import get_db_connection

logger = logging.getLogger(__name__)


def get_generations_api():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "\n            SELECT\n                generation_id,\n                generation_number,\n                description AS generation_name\n            FROM generations\n            ORDER BY generation_number\n        "
        )
        rows = cursor.fetchall()
        return (jsonify(rows), 200)
    except Exception as e:
        print("Error in /api/generations:", e)
        return (jsonify({"error": str(e)}), 500)
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_family_tree():
    """Lấy cây gia phả"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({"error": "Không thể kết nối database"}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM v_family_tree ORDER BY generation_number, full_name")
        tree = cursor.fetchall()
        return jsonify(tree)
    except Error as e:
        return (jsonify({"error": str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_relationships():
    """Lấy quan hệ gia đình với ID (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({"error": "Không thể kết nối database"}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "\n            SELECT \n                r.id AS relationship_id,\n                r.child_id,\n                r.parent_id,\n                r.relation_type,\n                child.full_name AS child_name,\n                child.gender AS child_gender,\n                parent.full_name AS parent_name,\n                parent.gender AS parent_gender\n            FROM relationships r\n            INNER JOIN persons child ON r.child_id = child.person_id\n            INNER JOIN persons parent ON r.parent_id = parent.person_id\n            ORDER BY r.id\n        "
        )
        relationships = cursor.fetchall()
        return jsonify(relationships)
    except Error as e:
        return (jsonify({"error": str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_children(parent_id):
    """Lấy con của một người (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({"error": "Không thể kết nối database"}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "\n            SELECT \n                p.person_id,\n                p.full_name,\n                p.gender,\n                p.generation_level,\n                r.relation_type\n            FROM relationships r\n            INNER JOIN persons p ON r.child_id = p.person_id\n            WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')\n            ORDER BY p.full_name\n        ",
            (parent_id,),
        )
        children = cursor.fetchall()
        return jsonify(children)
    except Error as e:
        return (jsonify({"error": str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
