-- =====================================================
-- ROLLBACK SCRIPT FOR IMPORTED GENEALOGY DATA
-- =====================================================
--
-- WARNING: This script will delete imported genealogy data.
-- Use ONLY for rollback / re-import scenarios.
-- Does NOT drop tables, only deletes data.
--
-- This script deletes data in the correct dependency order
-- to avoid foreign key constraint violations.
--
-- Tables affected:
--   - in_law_relationships
--   - relationships
--   - birth_records
--   - death_records
--   - personal_details
--   - persons
--
-- Tables NOT affected (preserved):
--   - generations (reference/master data)
--   - branches (reference/master data)
--   - locations (reference/master data)
--   - marriages (normalized table, may contain data)
--   - users (authentication data)
--
-- =====================================================

USE tbqc2025;

-- Disable foreign key checks temporarily
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- STEP 1: Delete in-law relationships
-- =====================================================
DELETE FROM in_law_relationships;
SELECT CONCAT('Deleted from in_law_relationships: ', ROW_COUNT(), ' rows') AS status;

-- =====================================================
-- STEP 2: Delete relationships (parent-child)
-- =====================================================
DELETE FROM relationships;
SELECT CONCAT('Deleted from relationships: ', ROW_COUNT(), ' rows') AS status;

-- =====================================================
-- STEP 3: Delete birth records
-- =====================================================
DELETE FROM birth_records;
SELECT CONCAT('Deleted from birth_records: ', ROW_COUNT(), ' rows') AS status;

-- =====================================================
-- STEP 4: Delete death records
-- =====================================================
DELETE FROM death_records;
SELECT CONCAT('Deleted from death_records: ', ROW_COUNT(), ' rows') AS status;

-- =====================================================
-- STEP 5: Delete personal details
-- =====================================================
DELETE FROM personal_details;
SELECT CONCAT('Deleted from personal_details: ', ROW_COUNT(), ' rows') AS status;

-- =====================================================
-- STEP 6: Delete persons
-- =====================================================
DELETE FROM persons;
SELECT CONCAT('Deleted from persons: ', ROW_COUNT(), ' rows') AS status;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================
-- VERIFICATION
-- =====================================================
SELECT 'Rollback completed. Verification:' AS status;

SELECT 
    'persons' AS table_name,
    COUNT(*) AS remaining_rows
FROM persons
UNION ALL
SELECT 
    'relationships' AS table_name,
    COUNT(*) AS remaining_rows
FROM relationships
UNION ALL
SELECT 
    'birth_records' AS table_name,
    COUNT(*) AS remaining_rows
FROM birth_records
UNION ALL
SELECT 
    'death_records' AS table_name,
    COUNT(*) AS remaining_rows
FROM death_records
UNION ALL
SELECT 
    'personal_details' AS table_name,
    COUNT(*) AS remaining_rows
FROM personal_details
UNION ALL
SELECT 
    'in_law_relationships' AS table_name,
    COUNT(*) AS remaining_rows
FROM in_law_relationships;

SELECT 'Rollback script completed successfully.' AS status;

