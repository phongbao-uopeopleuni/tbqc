-- =====================================================
-- DROP CÁC BẢNG CŨ TRƯỚC KHI TẠO SCHEMA MỚI
-- Chạy script này trước khi chạy reset_schema_tbqc.sql
-- =====================================================

USE railway;

SET FOREIGN_KEY_CHECKS = 0;

-- Drop các bảng có foreign key trước
DROP TABLE IF EXISTS relationships;
DROP TABLE IF EXISTS marriages;
DROP TABLE IF EXISTS in_law_relationships;

-- Drop bảng chính
DROP TABLE IF EXISTS persons;

-- Drop các bảng phụ (nếu có)
DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS birth_records;
DROP TABLE IF EXISTS death_records;
DROP TABLE IF EXISTS personal_details;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS generations;
DROP TABLE IF EXISTS locations;

-- Drop views (nếu có)
DROP VIEW IF EXISTS v_family_tree;
DROP VIEW IF EXISTS v_family_relationships;
DROP VIEW IF EXISTS v_person_full_info;

-- Drop stored procedures (nếu có)
DROP PROCEDURE IF EXISTS sp_get_ancestors;
DROP PROCEDURE IF EXISTS sp_get_descendants;
DROP PROCEDURE IF EXISTS sp_get_children;

SET FOREIGN_KEY_CHECKS = 1;

-- Note: Bảng users không drop để giữ tài khoản admin

