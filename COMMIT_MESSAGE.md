# Git Commit Message Template

## Commit Message Đề Xuất:

```
Fix API /api/tree 404 and /api/ancestors 500 errors

- Fix /api/tree route to handle max_gen and max_generation parameters
- Fix /api/ancestors collation mismatch error in stored procedures
- Update stored procedures (sp_get_ancestors, sp_get_descendants, sp_get_children) with collation fix
- Add update_stored_procedures.py script for easy procedure updates
- Improve error handling and logging in API routes
- Fix indentation issues in app.py
- Add test scripts for API verification
```

## Files Changed:

### Core Files:
- `app.py` - Fixed routes and error handling
- `folder_sql/update_views_procedures_tbqc.sql` - Updated stored procedures with collation fix
- `folder_sql/reset_schema_tbqc.sql` - Schema definition
- `folder_sql/drop_old_tables.sql` - Cleanup script

### New Files:
- `update_stored_procedures.py` - Script to update stored procedures
- `test_ancestors_api.py` - Test script for ancestors API
- `test_api_tree_direct.py` - Test script for tree API
- `fix_collation_procedures.sql` - SQL file for collation fix
- `FIX_ANCESTORS_COMPLETE.md` - Documentation
- `FIX_API_TREE_404.md` - Documentation
- `NEXT_STEPS_CHECKLIST.md` - Next steps guide

### Documentation:
- Various markdown files for troubleshooting and guides

