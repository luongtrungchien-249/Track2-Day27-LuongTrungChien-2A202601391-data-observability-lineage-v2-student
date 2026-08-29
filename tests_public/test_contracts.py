from pathlib import Path
import pandas as pd

from student_api import validate_orders

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "orders_contract.yaml"


def healthy_df():
    return pd.DataFrame([
        {
            "order_id": 1,
            "customer_id": "C1",
            "amount": 10.0,
            "currency": "USD",
            "status": "completed",
            "created_at": "2026-08-28T10:00:00Z",
            "updated_at": "2026-08-28T10:05:00Z",
        },
        {
            "order_id": 2,
            "customer_id": "C2",
            "amount": 20.0,
            "currency": "USD",
            "status": "pending",
            "created_at": "2026-08-28T10:01:00Z",
            "updated_at": "2026-08-28T10:06:00Z",
        },
    ])


def failed(issues):
    return [i for i in issues if not i["passed"]]


def test_healthy_contract_passes_starter_checks():
    assert not failed(validate_orders(healthy_df(), CONTRACT))


def test_duplicate_order_id_is_detected():
    df = healthy_df()
    df.loc[1, "order_id"] = 1
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "unique" and i["column"] == "order_id" for i in issues)


def test_invalid_currency_is_detected():
    df = healthy_df()
    df.loc[0, "currency"] = "BTC"
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "accepted_values" and i["column"] == "currency" for i in issues)


def test_type_drift_is_detected():
    df = healthy_df()
    df["order_id"] = df["order_id"].astype(object)
    df.loc[0, "order_id"] = "not_an_int"
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "type" and i["column"] == "order_id" for i in issues)


def test_missing_required_column_is_detected():
    df = healthy_df().drop(columns=["amount"])
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "required_column" and i["column"] == "amount" for i in issues)


def test_null_in_required_column_is_detected():
    df = healthy_df()
    df.loc[0, "customer_id"] = None
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "not_null" and i["column"] == "customer_id" for i in issues)


def test_negative_amount_range_violation_is_detected():
    df = healthy_df()
    df.loc[0, "amount"] = -10.0
    issues = failed(validate_orders(df, CONTRACT))
    assert any(i["check"] == "range" and i["column"] == "amount" for i in issues)


def test_empty_dataframe_handling():
    df = pd.DataFrame(columns=["order_id", "customer_id", "amount", "currency", "status", "created_at", "updated_at"])
    issues = validate_orders(df, CONTRACT)
    assert isinstance(issues, list)


def test_kb_contract_min_length_validation():
    from src.contract_validator import load_contract, validate_dataframe
    kb_contract = load_contract(ROOT / "contracts" / "kb_contract.yaml")
    kb_df = pd.DataFrame([
        {
            "doc_id": "D1",
            "version": 1,
            "effective_at": "2026-08-20T10:00:00Z",
            "published_at": "2026-08-28T10:00:00Z",
            "source_uri": "policy.pdf",
            "content": "Too short",  # min_length is 20
        }
    ])
    issues = failed(validate_dataframe(kb_df, kb_contract))
    assert any(i["check"] == "min_length" and i["column"] == "content" for i in issues)


