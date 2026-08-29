"""Modern Enterprise Data Reliability & Observability Control Room."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "latest_metrics.json"
HISTORY = ROOT / "data" / "history" / "metrics_history.csv"
LINEAGE_FILE = ROOT / "data" / "baseline" / "lineage_graph.json"

st.set_page_config(
    page_title="Data Reliability Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich styling
st.markdown(
    """
    <style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.0rem; color: #64748B; margin-bottom: 1.5rem; }
    .status-card { padding: 1.2rem; border-radius: 10px; background-color: #F8FAFC; border: 1px solid #E2E8F0; margin-bottom: 1rem; }
    .badge-pass { background-color: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 12px; font-weight: 600; }
    .badge-fail { background-color: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 12px; font-weight: 600; }
    .badge-warn { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 12px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🛡️ Data Reliability Command Center</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-Time Data Observability, Contracts, Lineage & SLO Monitoring</div>', unsafe_allow_html=True)

if not REPORT.exists():
    st.warning("⚠️ No metrics report found. Please run `.venv\\Scripts\\python scripts\\run_baseline.py` to generate report.")
    st.stop()

report = json.loads(REPORT.read_text(encoding="utf-8"))
contract_slo = report.get("contract_slo", {})
row_anomaly = report.get("row_count_anomaly", {})
kb_anomaly = report.get("kb_text_length_signal", {})

# Top Global Health Banner
is_critical = (report.get("critical_contract_failures", 0) > 0) or contract_slo.get("breached", False)
is_anomaly = row_anomaly.get("is_anomaly", False) or kb_anomaly.get("is_anomaly", False)

if is_critical:
    st.error("🚨 **SYSTEM ALERT: CRITICAL RELIABILITY VIOLATION DETECTED** — Contract Breach / SLO Exhaustion. Pipeline should be quarantined!")
elif is_anomaly:
    st.warning("⚠️ **SYSTEM WARNING: STATISTICAL ANOMALIES DETECTED** — Data drift or volume shift observed.")
else:
    st.success("✅ **SYSTEM HEALTHY: ALL PIPELINE CONTRACTS & METRICS OPERATIONAL**")

# Top KPI Metric Cards
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Orders Ingested", f"{report.get('orders_rows', 0):,} rows")
with c2:
    st.metric("Freshness Lag", f"{report.get('freshness_minutes', 0):.1f} min", delta="-15 min SLA", delta_color="inverse")
with c3:
    st.metric("Contract Violations", f"{report.get('failed_contract_checks', 0)} failed", delta=f"{report.get('critical_contract_failures', 0)} critical", delta_color="inverse")
with c4:
    burn_rate = contract_slo.get("burn_rate", 0.0)
    st.metric("SLO Burn Rate", f"{burn_rate:.2f}x", delta="Target: 99.9%", delta_color="off")
with c5:
    rem_budget = contract_slo.get("remaining_error_budget_fraction", 1.0) * 100
    st.metric("Remaining Budget", f"{rem_budget:.1f}%")

st.markdown("---")

# Main Content Tabs
tab_metrics, tab_contracts, tab_lineage, tab_slo, tab_incident = st.tabs([
    "📈 Metric Observability",
    "📜 Data Contracts & Quality",
    "🕸️ Lineage & Blast Radius",
    "🎯 SLO & Error Budget",
    "🚨 Incident Response & Runbook",
])

with tab_metrics:
    st.subheader("Statistical Anomaly & Drift Analysis")
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("**Order Volume Anomaly Detector (MAD / Z-Score)**")
        st.write(f"- Status: {'🚨 ANOMALY' if row_anomaly.get('is_anomaly') else '✅ Normal'}")
        st.write(f"- Method: `{row_anomaly.get('method')}`")
        st.write(f"- Anomaly Score: `{row_anomaly.get('score', 0):.2f}`")
        st.caption(f"Reason: {row_anomaly.get('reason')}")

    with col_m2:
        st.markdown("**Knowledge Base RAG Text Length Signal**")
        st.write(f"- Status: {'🚨 SHIFT DETECTED' if kb_anomaly.get('is_anomaly') else '✅ Normal'}")
        st.write(f"- Mean Token Length: `{kb_anomaly.get('current_mean', 0):.1f}` tokens")
        st.caption(f"Reason: {kb_anomaly.get('reason')}")

    if HISTORY.exists():
        st.markdown("### Historical Metric Trends (42 Days)")
        history_df = pd.read_csv(HISTORY)
        history_df["date"] = pd.to_datetime(history_df["date"])
        
        hist_col1, hist_col2 = st.columns(2)
        with hist_col1:
            st.markdown("**Daily Order Volume (Weekend Seasonality vs Weekday)**")
            st.line_chart(history_df.set_index("date")[["row_count"]])
        with hist_col2:
            st.markdown("**Average Order Amount ($USD)**")
            st.line_chart(history_df.set_index("date")[["avg_amount"]])

with tab_contracts:
    st.subheader("Data Contract Compliance Details")
    st.write("Validation results for incoming `orders` and `kb_documents` datasets:")
    
    issues_list = []
    if "kb_contract_issues" in report:
        issues_list.extend(report["kb_contract_issues"])
    
    if not issues_list and report.get("failed_contract_checks", 0) == 0:
        st.success("All schema, type, uniqueness, range, and freshness rules passed successfully.")
    else:
        st.dataframe(pd.DataFrame(issues_list) if issues_list else pd.DataFrame([{"info": "See latest_metrics.json for complete check list"}]))

with tab_lineage:
    st.subheader("Transitive Lineage Graph & Blast Radius")
    st.markdown("Trace propagation from corrupted sources to downstream business marts and dashboards:")
    
    if LINEAGE_FILE.exists():
        with open(LINEAGE_FILE, "r", encoding="utf-8") as f:
            lineage_data = json.load(f)
        
        st.markdown("#### Dataset-Level Dependencies")
        st.json(lineage_data.get("dataset_lineage", {}))

        blast_radius = report.get("sample_blast_radius_from_stg_orders", [])
        st.info(f"**Impacted downstream assets if `stg_orders` is compromised:**\n\n`stg_orders` ➔ " + " ➔ ".join([f"`{node}`" for node in blast_radius]))

with tab_slo:
    st.subheader("Service Level Objectives & Error Budget Health")
    st.write(f"- **SLO Target:** `{contract_slo.get('target', 0.999) * 100:.2f}%`")
    st.write(f"- **Allowed Bad Rate:** `{contract_slo.get('allowed_bad_rate', 0.001) * 100:.3f}%`")
    st.write(f"- **Actual Bad Rate:** `{contract_slo.get('actual_bad_rate', 0.0) * 100:.3f}%`")
    st.write(f"- **Burn Rate Factor:** `{contract_slo.get('burn_rate', 0.0):.2f}x`")
    st.progress(max(0.0, min(1.0, contract_slo.get("remaining_error_budget_fraction", 1.0))))

with tab_incident:
    st.subheader("Active Incident Response Plan")
    st.markdown("""
    | Step | Action | Status | Owner |
    |---|---|---|---|
    | 1. Detect | Automated Anomaly & Contract Alerts | COMPLETED | Observability System |
    | 2. Triage | Determine Failure Severity (P1/P2/P3) | COMPLETED | On-Call Engineer |
    | 3. Root Cause | Ingestion Truncation & Stale KB | IDENTIFIED | Data Platform |
    | 4. Blast Radius | Upstream orders ➔ Daily Revenue Mart | TRACED | Lineage BFS |
    | 5. Mitigate | Quarantine Corrupted Batch & Trigger Backfill | READY | Data Operations |
    | 6. Verify | Great Expectations & dbt Unit Tests Validation | VERIFIED | Analytics Eng |
    """)

