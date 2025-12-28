#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genealogy Tree Helper Functions
Updated for new schema: person_id VARCHAR(50), relationships with parent_id/child_id
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


def build_tree(
    root_id: str,
    persons_by_id: Dict[str, Dict],
    children_map: Dict[str, List[str]],
    current_gen: int,
    max_gen: int
) -> Optional[Dict[str, Any]]:
    """
    Build nested descendants tree from root_id up to max_gen.
    
    Args:
        root_id: Person ID (VARCHAR) to start from
        persons_by_id: Dictionary mapping person_id -> person data
        children_map: Dictionary mapping parent_id -> list of child_ids
        current_gen: Current generation level (1 = root)
        max_gen: Maximum generation to include
    
    Returns:
        Tree node dict or None if current_gen > max_gen
    """
    if current_gen > max_gen:
        return None
    
    if root_id not in persons_by_id:
        logger.warning(f"Person {root_id} not found in persons_by_id")
        return None
    
    person = persons_by_id[root_id]
    
    # Build node structure
    node = {
        "person_id": root_id,
        "full_name": person.get("full_name", ""),
        "alias": person.get("alias"),
        "generation_level": person.get("generation_level"),
        "status": person.get("status"),
        "gender": person.get("gender"),
        "home_town": person.get("home_town"),
        "children": []
    }
    
    # Get children
    child_ids = children_map.get(root_id, [])
    
    # Recursively build children
    for child_id in child_ids:
        child_node = build_tree(
            child_id,
            persons_by_id,
            children_map,
            current_gen + 1,
            max_gen
        )
        if child_node:
            node["children"].append(child_node)
    
    return node


def build_ancestors_chain(
    person_id: str,
    persons_by_id: Dict[str, Dict],
    parent_map: Dict[str, Dict]
) -> List[Dict[str, Any]]:
    """
    Return linear chain from farthest ancestor → this person.
    
    Args:
        person_id: Starting person ID (VARCHAR)
        persons_by_id: Dictionary mapping person_id -> person data
        parent_map: Dictionary mapping child_id -> {father_id, mother_id}
    
    Returns:
        List ordered oldest → current person
    """
    chain = []
    current_id = person_id
    visited = set()  # Prevent cycles
    
    while current_id and current_id not in visited:
        visited.add(current_id)
        
        if current_id not in persons_by_id:
            logger.warning(f"Person {current_id} not found in persons_by_id")
            break
        
        person = persons_by_id[current_id]
        chain.append({
            "person_id": current_id,
            "full_name": person.get("full_name", ""),
            "alias": person.get("alias"),
            "generation_level": person.get("generation_level"),
            "status": person.get("status"),
            "gender": person.get("gender")
        })
        
        # Get parent (prefer father, else mother)
        parents = parent_map.get(current_id, {})
        next_id = parents.get("father_id") or parents.get("mother_id")
        
        if not next_id:
            break
        
        current_id = next_id
    
    # Reverse to get oldest → current order
    chain.reverse()
    return chain


def build_descendants(
    root_id: str,
    persons_by_id: Dict[str, Dict],
    children_map: Dict[str, List[str]],
    max_depth: int,
    current_depth: int = 0,
    parent_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Return descendants of root_id up to max_depth levels below.
    
    Args:
        root_id: Person ID (VARCHAR) to start from
        persons_by_id: Dictionary mapping person_id -> person data
        children_map: Dictionary mapping parent_id -> list of child_ids
        max_depth: Maximum depth to traverse (1 = children only)
        current_depth: Current depth (0 = root)
        parent_id: Parent person_id for this node
    
    Returns:
        Flat list of descendant nodes with depth and parent_id
    """
    if current_depth >= max_depth:
        return []
    
    if root_id not in persons_by_id:
        logger.warning(f"Person {root_id} not found in persons_by_id")
        return []
    
    descendants = []
    person = persons_by_id[root_id]
    
    # Add current person as descendant (if not root)
    if current_depth > 0:
        descendants.append({
            "person_id": root_id,
            "full_name": person.get("full_name", ""),
            "alias": person.get("alias"),
            "generation_level": person.get("generation_level"),
            "status": person.get("status"),
            "gender": person.get("gender"),
            "home_town": person.get("home_town"),
            "depth": current_depth,
            "parent_id": parent_id
        })
    
    # Get children and recurse
    child_ids = children_map.get(root_id, [])
    for child_id in child_ids:
        child_descendants = build_descendants(
            child_id,
            persons_by_id,
            children_map,
            max_depth,
            current_depth + 1,
            root_id
        )
        descendants.extend(child_descendants)
    
    return descendants


def build_children_map(cursor) -> Dict[str, List[str]]:
    """
    Build children_map from relationships table (new schema).
    
    Returns:
        Dictionary mapping parent_id -> list of child_ids
    """
    children_map = {}
    
    cursor.execute("""
        SELECT parent_id, child_id
        FROM relationships
        WHERE relation_type IN ('father', 'mother')
    """)
    
    for row in cursor.fetchall():
        # Handle both dict and tuple results
        if isinstance(row, dict):
            parent_id = row['parent_id']
            child_id = row['child_id']
        else:
            parent_id = row[0]
            child_id = row[1]
        
        if parent_id and child_id:
            if parent_id not in children_map:
                children_map[parent_id] = []
            if child_id not in children_map[parent_id]:
                children_map[parent_id].append(child_id)
    
    return children_map


def build_parent_map(cursor) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Build parent_map from relationships table (new schema).
    
    Returns:
        Dictionary mapping child_id -> {father_id, mother_id}
    """
    parent_map = {}
    
    cursor.execute("""
        SELECT child_id, parent_id, relation_type
        FROM relationships
        WHERE relation_type IN ('father', 'mother')
    """)
    
    for row in cursor.fetchall():
        # Handle both dict and tuple results
        if isinstance(row, dict):
            child_id = row['child_id']
            parent_id = row['parent_id']
            relation_type = row['relation_type']
        else:
            child_id = row[0]
            parent_id = row[1]
            relation_type = row[2]
        
        if child_id not in parent_map:
            parent_map[child_id] = {
                "father_id": None,
                "mother_id": None
            }
        
        if relation_type == 'father':
            parent_map[child_id]["father_id"] = parent_id
        elif relation_type == 'mother':
            parent_map[child_id]["mother_id"] = parent_id
    
    return parent_map


def load_persons_data(cursor) -> Dict[str, Dict]:
    """
    Load all persons data from new schema.
    
    Returns:
        Dictionary mapping person_id -> person data
    """
    cursor.execute("""
        SELECT 
            p.person_id,
            p.full_name,
            p.alias,
            p.gender,
            p.status,
            p.generation_level,
            p.home_town,
            p.nationality,
            p.religion,
            p.birth_date_solar,
            p.birth_date_lunar,
            p.death_date_solar,
            p.death_date_lunar,
            p.place_of_death,
            p.grave_info,
            p.contact,
            p.social,
            p.occupation,
            p.education,
            p.events,
            p.titles,
            p.blood_type,
            p.genetic_disease,
            p.note,
            p.father_mother_id,
            -- Cha từ relationships
            father.full_name AS father_name,
            -- Mẹ từ relationships
            mother.full_name AS mother_name
        FROM persons p
        -- Cha từ relationships (relation_type = 'father')
        LEFT JOIN relationships rel_father
            ON rel_father.child_id = p.person_id 
            AND rel_father.relation_type = 'father'
        LEFT JOIN persons father
            ON rel_father.parent_id = father.person_id
        -- Mẹ từ relationships (relation_type = 'mother')
        LEFT JOIN relationships rel_mother
            ON rel_mother.child_id = p.person_id 
            AND rel_mother.relation_type = 'mother'
        LEFT JOIN persons mother
            ON rel_mother.parent_id = mother.person_id
    """)
    
    persons_by_id = {}
    for row in cursor.fetchall():
        # Handle both dict and tuple results
        if isinstance(row, dict):
            persons_by_id[row['person_id']] = dict(row)
        else:
            # Tuple format
            persons_by_id[row[0]] = {
                'person_id': row[0],
                'full_name': row[1],
                'alias': row[2],
                'gender': row[3],
                'status': row[4],
                'generation_level': row[5],
                'home_town': row[6],
                'nationality': row[7],
                'religion': row[8],
                'birth_date_solar': row[9],
                'birth_date_lunar': row[10],
                'death_date_solar': row[11],
                'death_date_lunar': row[12],
                'place_of_death': row[13],
                'grave_info': row[14],
                'contact': row[15],
                'social': row[16],
                'occupation': row[17],
                'education': row[18],
                'events': row[19],
                'titles': row[20],
                'blood_type': row[21],
                'genetic_disease': row[22],
                'note': row[23],
                'father_mother_id': row[24],
                'father_name': row[25] if len(row) > 25 else None,
                'mother_name': row[26] if len(row) > 26 else None
            }
    
    logger.info(f"Loaded {len(persons_by_id)} persons")
    return persons_by_id
