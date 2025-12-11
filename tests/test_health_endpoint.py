#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test /api/health endpoint
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


def test_health_endpoint(client):
    """Test /api/health returns 200 and valid JSON"""
    resp = client.get('/api/health')
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data is not None
    assert 'server' in data
    assert 'database' in data
    assert 'db_config' in data
    assert data['server'] == 'ok'
    
    # Check stats if database is connected
    if data['database'] == 'connected':
        assert 'stats' in data
        assert 'persons_count' in data['stats']
        assert 'relationships_count' in data['stats']

