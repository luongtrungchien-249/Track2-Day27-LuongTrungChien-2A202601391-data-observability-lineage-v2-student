#!/usr/bin/env python3
"""Great Expectations Core 1.21 validation workflow.

Packages expectations into a Suite, Validation Definition, and evaluates
results with severity-aware actions (Block/Quarantine/Warn).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import great_expectations as gx
except ImportError as exc:
    raise SystemExit("great_expectations is not installed. Run: pip install -r requirements.txt") from exc


def main() -> None:
    orders_path = ROOT / "data" / "incoming" / "orders.csv"
    if not orders_path.exists():
        print(f"Data file not found: {orders_path}")
        return

    df = pd.read_csv(orders_path)
    context = gx.get_context(mode="ephemeral")

    # Data Source & Batch Definition
    data_source = context.data_sources.add_pandas("orders_pandas")
    asset = data_source.add_dataframe_asset(name="orders_dataframe")
    batch_definition = asset.add_batch_definition_whole_dataframe("whole_orders")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    # Expectation Suite
    suite_name = "orders_contract_suite"
    suite = gx.ExpectationSuite(name=suite_name)
    
    expectations = [
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="order_id",
            notes="order_id must never be null",
        ),
        gx.expectations.ExpectColumnValuesToBeUnique(
            column="order_id",
            notes="order_id must be unique across all rows",
        ),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="amount",
            min_value=0,
            notes="Order amount cannot be negative",
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="currency",
            value_set=["USD", "VND"],
            notes="Supported currencies are USD and VND",
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="status",
            value_set=["pending", "completed", "refunded", "cancelled"],
            notes="Allowed order lifecycle statuses",
        ),
    ]

    for exp in expectations:
        suite.add_expectation(exp)

    context.suites.add(suite)

    # Validation Definition
    validation_definition = gx.ValidationDefinition(
        data=batch_definition,
        suite=suite,
        name="orders_validation_definition",
    )
    context.validation_definitions.add(validation_definition)

    # Run validation
    validation_results = batch.validate(suite)
    
    print("=== GREAT EXPECTATIONS VALIDATION REPORT ===")
    all_passed = True
    critical_failures = 0

    for res in validation_results.results:
        exp_type = res.expectation_config.type
        success = res.success
        col = res.expectation_config.kwargs.get("column", "all")
        status_str = "PASS" if success else "FAIL"
        print(f"[{status_str}] {exp_type:<35} (col: {col})")
        if not success:
            all_passed = False
            critical_failures += 1

    print("\n--- Summary & Recommended Action ---")
    if all_passed:
        print("Status: ALL EXPECTATIONS PASSED")
        print("Action: PROCEED (Pipeline unblocked)")
    else:
        print(f"Status: {critical_failures} EXPECTATION(S) FAILED")
        print("Action: BLOCK PIPELINE & QUARANTINE DATA (Critical data quality violation)")


if __name__ == "__main__":
    main()

