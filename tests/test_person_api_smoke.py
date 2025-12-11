#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for /api/person/<id> endpoint
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


def test_persons_endpoint(client):
    """Test /api/persons returns 200 and list"""
    resp = client.get('/api/persons')
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert isinstance(data, list)


def test_person_detail_endpoint(client):
    """Test /api/person/<id> if at least one person exists"""
    # First get persons list
    resp = client.get('/api/persons')
    assert resp.status_code == 200
    
    persons = resp.get_json()
    if not persons or len(persons) == 0:
        pytest.skip("No persons in database")
    
    # Get first person's ID
    first_person = persons[0]
    person_id = first_person.get('person_id')
    
    if not person_id:
        pytest.skip("No person_id in response")
    
    # Test detail endpoint
    resp = client.get(f'/api/person/{person_id}')
    assert resp.status_code == 200
    
    data = resp.get_json()
    assert data is not None
    assert 'person_id' in data or 'full_name' in data


def test_person_not_found(client):
    """Test /api/person/<invalid_id> returns 404"""
    resp = client.get('/api/person/999999')
    assert resp.status_code == 404

