# Phase 0d Baseline Thresholds

> Gate dung de so sanh baseline truoc/sau moi `[move]` PR runtime trong refactor.

## Thresholds

| Metric | Baseline source | Fail when | Reason |
|---|---|---|---|
| Endpoint p95 latency | `endpoints[*].p95_ms`, `mutation[*].p95_ms` | Tang > 20% | Bat regression network/DB/query sau refactor |
| RSS peak | `rss_peak_mb` | Tang > 15% | Railway RAM headroom nho, can rollback som |
| Startup time | `startup_ms` | Tang > 20% | Gunicorn preload + restart window phai on dinh |
| 5xx error count | `endpoints[*].errors` | Tang bat ky | Error rate gate = 0% increase |
| Audit verify | `mutation[*].audit_verified` | `false` | Mutation P0 khong duoc fail-silent audit |
| DB pool active | `db_pool.max_active` | `> pool_size (3)` | Phase 0d smoke phai giu sequential, khong vuot pool |

## Compare command

```bash
python scripts/perf/compare_baseline.py <old.json> <new.json>
```

## Measurement notes

1. Read endpoints: 5 warm-up + 100 sequential requests.
2. Mutation endpoint: 30 sequential creates, verify `CREATE_USER` audit tang dung 1 moi request.
3. Current runtime deviation: `/api/admin/users` khong emit `CREATE_USER` audit, nen local baseline script do `/admin/api/users` cho mutation gate va ghi ro deviation trong JSON notes.
4. Local perf mode duoc phep tat limiter de tranh mau 100 requests tu tu cham 429 local gate; baseline JSON phai ghi ro dieu nay.
5. Dataset local phai ghi context (`dataset.persons_count`, `dataset.relationships_count`) vi `/api/persons` va `/api/family-tree` phu thuoc row count.
