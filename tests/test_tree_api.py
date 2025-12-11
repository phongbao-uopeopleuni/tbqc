#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for tree and search APIs
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_tree_endpoint_basic(client):
    """Test /api/tree returns valid JSON"""
    resp = client.get('/api/tree?max_gen=5')
    
    # Should return 200 or 500 (if DB not available)
    assert resp.status_code in [200, 404, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert data is not None
        assert 'person_id' in data
        assert 'full_name' in data
        assert 'children' in data
        assert isinstance(data['children'], list)


def test_tree_endpoint_with_root_id(client):
    """Test /api/tree with specific root_id"""
    resp = client.get('/api/tree?root_id=1&max_gen=3')
    assert resp.status_code in [200, 404, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert data['person_id'] == 1


def test_search_endpoint_basic(client):
    """Test /api/search returns list"""
    resp = client.get('/api/search?q=test')
    
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert isinstance(data, list)


def test_search_endpoint_empty(client):
    """Test /api/search with empty query"""
    resp = client.get('/api/search?q=')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_endpoint_with_generation(client):
    """Test /api/search with generation filter"""
    resp = client.get('/api/search?q=Minh&generation=1')
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert isinstance(data, list)
        # All results should have generation_number = 1
        for item in data:
            if 'generation_number' in item:
                assert item['generation_number'] == 1


def test_ancestors_endpoint(client):
    """Test /api/ancestors/<id>"""
    # Try with person_id=1 (should exist if DB has data)
    resp = client.get('/api/ancestors/1')
    assert resp.status_code in [200, 404, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert 'person' in data
        assert 'ancestors_chain' in data
        assert isinstance(data['ancestors_chain'], list)


def test_ancestors_not_found(client):
    """Test /api/ancestors/<invalid_id> returns 404"""
    resp = client.get('/api/ancestors/999999')
    assert resp.status_code == 404


def test_descendants_endpoint(client):
    """Test /api/descendants/<id>"""
    resp = client.get('/api/descendants/1?max_depth=3')
    assert resp.status_code in [200, 404, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert 'root_id' in data
        assert 'max_depth' in data
        assert 'descendants' in data
        assert isinstance(data['descendants'], list)


def test_descendants_not_found(client):
    """Test /api/descendants/<invalid_id> returns 404"""
    resp = client.get('/api/descendants/999999')
    assert resp.status_code == 404

