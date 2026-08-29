# Incident Report: E-Commerce Pipeline Silent Degradation & Stale Support Policy

## Severity
**P1 (Critical Business Impact)** — Revenue reporting anomaly on CEO Dashboard and Customer Support AI Agent serving outdated refund terms to end users.

## Summary
On 2026-08-29, while pipeline execution status reported `SUCCESS`, data reliability signals detected multiple silent data anomalies:
1. Significant revenue discrepancy caused by upstream ingestion volume drop and multi-version SCD customer join inflation.
2. AI Support Agent RAG index serving deprecated 14-day refund policy instead of the updated 7-day policy due to stale knowledge-base document ingestion lag (> 3 hours).

## Detection
- **Signal 1:** Metric Volume Anomaly Detector flagged partial ingestion drop (`len(orders) = 150` vs 600 baseline, MAD score = 5.53).
- **Signal 2:** Knowledge Base Contract validator flagged Freshness SLA violation (`published_at` delay = 185 min vs 60 min SLA).
- **Signal 3:** dbt Unit Tests flagged revenue multiplication from duplicate active customer records.
- **First observed time:** 2026-08-29T05:25:00Z UTC.

## Root Cause
1. **Upstream Ingestion Truncation:** Upstream batch job experienced partial packet loss/timeout, persisting only 25% of orders without throwing an ETL process exit error.
2. **Knowledge Base Sync Failure:** The automated sync job for policy documentation stalled, leaving `kb_documents.jsonl` unrefreshed for > 3 hours while RAG embedding pipelines continued processing old cache.
3. **Slowly Changing Dimension (SCD) Key Multiplicity:** Customer dimension ETL created overlapping `is_active = true` records for modified customer profiles, leading to Cartesian joins in `fct_daily_revenue`.

## Evidence
1. `orders_contract.yaml` & `kb_contract.yaml` validation logs confirmed freshness breach (`delay_minutes=185.0`, `max_delay_minutes=60`).
2. `observability/anomaly.py` robust MAD detector flagged statistical anomaly on order volume with confidence score > 5.0.
3. dbt unit tests exposed that 1 order for a duplicate active customer record doubled the row count and inflated revenue.
4. Lineage graph traversal proved the transitive propagation from `stg_orders` to `fct_daily_revenue` and `ceo_revenue_dashboard`.

## Blast Radius

```text
raw_orders
└── stg_orders (amount_usd, status)
    └── fct_daily_revenue (daily_revenue)
        └── ceo_revenue_dashboard

kb_documents
└── kb_active_docs
    └── rag_index (embeddings)
        └── support_agent (refund policy answers)
```

## Mitigation
1. **Quarantine & Re-ingest:** Quarantined corrupted partial orders batch; triggered backfill re-ingestion from raw event stream for 2026-08-29.
2. **Active Customer Deduplication:** Added deduplication filter on `valid_to IS NULL AND is_active = true` ordered by `valid_from DESC` in customer staging model.
3. **KB Sync Trigger & Cache Invalidation:** Manually triggered document synchronization worker and flushed stale vector embeddings from RAG vector database.

## Recovery
- Re-ran `sync_dbt_seeds.py` and `dbt build --project-dir dbt_project --profiles-dir dbt_project` (all 17 models, data tests, and unit tests passed).
- Re-evaluated Great Expectations Checkpoint: 100% PASS.
- Verified CEO Dashboard daily revenue metric matches transactional ledger.

## Verification
- [x] Contract healthy (Schema, Types, Not Null, Unique, Accepted Values, Freshness)
- [x] dbt tests healthy (11 generic/singular tests + 1 unit test passed)
- [x] Anomaly returned to expected statistical baseline
- [x] SLO healthy / Error budget burn-rate normal (burn rate < 1.0)
- [x] Downstream output verified on Streamlit Dashboard

## Prevention / Action Items
| Action | Owner | Deadline | Why |
|---|---|---|---|
| Enforce Great Expectations / Contract Validator in CI/CD pipeline blocking step | Data Platform Team | 2026-09-02 | Prevent silent schema & volume corruption from entering marts |
| Deploy Multi-window Multi-burn-rate SRE alerting on critical dataset SLOs | SRE / Observability Team | 2026-09-05 | Alert on sustained data loss within 1 hour while filtering noise |
| Implement Unique surrogate key constraints on SCD Type 2 active customer records | Analytics Engineering | 2026-09-03 | Prevent fan-out joins in financial marts |
| Add RAG embedding drift & document freshness monitors before serving agent queries | AI / Support Team | 2026-09-04 | Ensure customer agents never serve outdated policy documents |

