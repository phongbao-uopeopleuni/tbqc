-- ============================================
-- PERFORMANCE INDEXES - Giảm RAM gián tiếp
-- Tăng tốc query để giảm thời gian giữ connection → Giảm RAM
-- ============================================
-- Chạy script này trên MySQL/MariaDB
-- Không ảnh hưởng logic, chỉ tăng tốc query
-- Sử dụng IF NOT EXISTS để đảm bảo an toàn

-- Indexes cho bảng persons (thường query nhất)
-- Tăng tốc query theo generation_level, full_name, status
CREATE INDEX IF NOT EXISTS idx_persons_generation_level ON persons(generation_level);
CREATE INDEX IF NOT EXISTS idx_persons_full_name ON persons(full_name);
CREATE INDEX IF NOT EXISTS idx_persons_status ON persons(status);

-- Indexes cho bảng relationships (query nhiều trong /api/members, /api/persons)
-- Tăng tốc query parent-child relationships
CREATE INDEX IF NOT EXISTS idx_relationships_child_id ON relationships(child_id);
CREATE INDEX IF NOT EXISTS idx_relationships_parent_id ON relationships(parent_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relation_type);
CREATE INDEX IF NOT EXISTS idx_relationships_composite ON relationships(parent_id, child_id, relation_type);

-- Indexes cho bảng marriages
-- Tăng tốc query spouse relationships
CREATE INDEX IF NOT EXISTS idx_marriages_person_id ON marriages(person_id);
CREATE INDEX IF NOT EXISTS idx_marriages_spouse_id ON marriages(spouse_person_id);
CREATE INDEX IF NOT EXISTS idx_marriages_status ON marriages(status);

-- Indexes cho bảng activities
-- Tăng tốc query activities theo status và created_at
CREATE INDEX IF NOT EXISTS idx_activities_status ON activities(status);
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON activities(created_at);

-- ============================================
-- VERIFICATION QUERIES (chạy sau khi tạo indexes)
-- ============================================
-- Uncomment các dòng sau để verify indexes đã được tạo:

-- SHOW INDEX FROM persons;
-- SHOW INDEX FROM relationships;
-- SHOW INDEX FROM marriages;
-- SHOW INDEX FROM activities;
