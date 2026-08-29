from student_api import column_downstream, downstream_assets


def test_transitive_downstream_assets():
    graph = {
        "raw_orders": ["stg_orders"],
        "stg_orders": ["revenue"],
        "revenue": ["dashboard"],
    }
    assert downstream_assets(graph, "raw_orders") == ["stg_orders", "revenue", "dashboard"]


def test_transitive_column_downstream():
    col_graph = {
        "raw_orders.amount": ["stg_orders.amount_usd"],
        "stg_orders.amount_usd": ["fct_daily_revenue.daily_revenue"],
        "fct_daily_revenue.daily_revenue": ["ceo_dashboard.revenue"],
    }
    result = column_downstream(col_graph, "raw_orders.amount")
    assert result == ["stg_orders.amount_usd", "fct_daily_revenue.daily_revenue", "ceo_dashboard.revenue"]


def test_lineage_handles_cycles_without_infinite_loop():
    cyclic_graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A", "D"],
    }
    result = downstream_assets(cyclic_graph, "A")
    assert result == ["B", "C", "D"]


def test_lineage_handles_diamond_dependencies():
    diamond_graph = {
        "root": ["left", "right"],
        "left": ["sink"],
        "right": ["sink"],
    }
    result = downstream_assets(diamond_graph, "root")
    assert result == ["left", "right", "sink"]


def test_lineage_missing_start_node_returns_empty():
    assert downstream_assets({}, "non_existent") == []
    assert column_downstream({}, "non_existent") == []


