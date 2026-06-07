# DB Operation Map

## Purpose

This document summarizes how the tbqc database is currently operated after the June 3
refactor scope closeout.

Use this file to answer four questions quickly:

1. Which tables are the current source of truth?
2. Which fields/tables are compatibility or legacy only?
3. Which runtime paths still depend on legacy compatibility behavior?
4. Which DB changes are safe now, and which must stay deferred?

Primary references:

1. [Refactor plan June 3rd.md](../../Refactor%20plan%20June%203rd.md)
2. [VERIFICATION_REPORT.md](../VERIFICATION_REPORT.md)
3. [phase-6-closeout-2026-06-05.md](../phase-6/phase-6-closeout-2026-06-05.md)

## Core Tables

### `persons`

Role:

- canonical person record
- carries profile fields, generation, and the legacy compatibility field `father_mother_id`

Important current rule:

- `persons.father_mother_id` is **not** the main parent/spouse source of truth anymore
- it still exists as a compatibility field and must not be removed casually

Runtime dependencies still using it:

- `sp_get_ancestors` fallback
- parts of `/api/ancestors`
- some search/disambiguation and backward-compatible projections exposing `fm_id`

### `relationships`

Role:

- canonical bloodline/parent-child source of truth

Canonical shape:

- `parent_id`
- `child_id`
- `relation_type`

Current rule:

- parent links must be read and written through `relationships`
- old assumptions about `father_id`, `mother_id`, or `relationship_id` are legacy and should stay dead

### `marriages`

Role:

- canonical spouse source of truth

Current rule:

- spouse reads are marriages-first
- legacy spouse sources must not override normalized `marriages`

Phase 1 result:

- the legacy spouse migration was executed
- post-migration count reached `353`
- runtime now treats `marriages` as the practical source of truth

## Compatibility And Legacy Data

### `persons.father_mother_id`

Status:

- compatibility field
- still active in fallback paths

Do:

- keep it while stored procedure/runtime fallback still exists
- allow read/expose for backward compatibility where needed

Do not:

- treat it as the primary grouping or relationship source
- remove it before an explicit Phase 7 or post-plan decision

### `spouse_sibling_children`

Status:

- legacy transition table
- no longer runtime priority for spouse reads

Do:

- keep read-only during the transition window
- use it only for audit/history/manual reconciliation if needed

Do not:

- let it override `marriages`
- drop it without a separate approved cleanup scope

### `in_law_relationships`

Status:

- legacy table
- verified empty during refactor verification
- dead delete path removed from runtime
- dropped from the current database on 2026-06-07

Current action state:

- cleanup SQL remains as an execution artifact in `folder_sql/drop_legacy_tables_phase4.sql`
- runtime must not reintroduce any dependency on this table

### `personal_details`

Status:

- legacy table
- verified empty during refactor verification
- dead delete path removed from runtime
- dropped from the current database on 2026-06-07

Current action state:

- cleanup SQL remains as an execution artifact in `folder_sql/drop_legacy_tables_phase4.sql`
- runtime must not reintroduce any dependency on this table

## Runtime Read Paths

### Parent/ancestor reads

Primary source:

- `relationships`

Fallbacks still alive:

- `persons.father_mother_id` in `sp_get_ancestors`
- direct-query ancestor fallback paths also still include `father_mother_id`

Key files:

- `services/genealogy_read_service.py`
- `services/person_service.py`
- `docs/refactor/verification_results.json`

### Spouse reads

Primary source:

- `marriages`

Resolver:

- `services/person_helpers.py:get_preferred_spouse_names()`

Main consumers:

- `services/genealogy_read_service.py`
- `services/members_helpers.py`
- `services/members_service.py`
- `services/person_service.py`

### Tree grouping reads

Primary grouping key for current scope:

- derived `family_group_key`

Current rule:

- `family_group_key` is derived from `father_id|mother_id`
- `father_mother_id` is fallback only, not the preferred grouping source

Key files:

- `folder_py/genealogy_tree.py`
- `static/js/family-tree-core.js`
- `static/js/family-tree-graph-builder.js`

## Runtime Write Paths

### Person update/create/delete

Current rule:

- mutation paths must preserve the canonical model:
  - person row in `persons`
  - parent links in `relationships`
  - spouse links in `marriages`

Important mutation behavior already locked in:

- `update_person()` and the shared write core use `relationships`
- parent mutation rules are now explicit:
  - omitted = keep
  - blank = delete
  - unmappable = reject

Key files:

- `services/person_service.py`
- `blueprints/persons.py`

### Spouse migration and spouse writes

Current rule:

- `marriages` owns spouse normalization
- migration script is idempotent and already executed once successfully

Key artifacts:

- `scripts/migrate_spouse_sibling_children_to_marriages.py`
- `backups/tbqc_backup_20260605_011423.sql`
- `backups/rollback_spouse_to_marriages.sql`

## Stored Procedures

### `sp_get_ancestors`

Status:

- still active
- still has fallback via `persons.father_mother_id`

Implication:

- any cleanup touching `father_mother_id` is unsafe until this dependency is removed by explicit scope

### `sp_get_descendants`

Status:

- still active
- already aligned with `relationships`

## Safe Changes Now

- documentation updates
- test coverage updates that reflect current behavior
- merge/closeout of the already-approved refactor scope
- manual execution of `drop_legacy_tables_phase4.sql` only after fresh backup and explicit approval

## Unsafe Or Deferred Changes

- introducing `family_units` automatically because the old draft mentioned it
- removing `father_mother_id`
- dropping `spouse_sibling_children`
- removing defensive `SHOW COLUMNS` guards just to make code look cleaner
- broad DB cleanup outside the narrow verified artifacts already prepared

## Practical Summary

If you need one short mental model, use this:

- `persons` = person record
- `relationships` = parent/child truth
- `marriages` = spouse truth
- `father_mother_id` = compatibility only
- `spouse_sibling_children` = read-only transition legacy
- `family_group_key` = current tree grouping key
- `family_units` = deferred, not part of the approved runtime model
