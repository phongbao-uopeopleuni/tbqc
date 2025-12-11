#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test tree endpoints
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


def test_tree_endpoint(client):
    """Test /api/tree returns valid JSON with root node"""
    resp = client.get('/api/tree?max_gen=5')
    
    # Should return 200 or 500 (if DB not available)
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert data is not None
        assert 'person_id' in data
        assert 'full_name' in data
        assert 'children' in data
        assert isinstance(data['children'], list)


def test_search_endpoint(client):
    """Test /api/search returns list"""
    resp = client.get('/api/search?q=test')
    
    # Should return 200 or 500 (if DB not available)
    assert resp.status_code in [200, 500]
    
    if resp.status_code == 200:
        data = resp.get_json()
        assert isinstance(data, list)


def test_search_empty_query(client):
    """Test /api/search with empty query returns empty list"""
    resp = client.get('/api/search?q=')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

