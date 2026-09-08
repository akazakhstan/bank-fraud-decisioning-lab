"""
Fraud decisioning rules engine.

This module applies observable transaction and behavioral
signals to identify potentially fraudulent transactions.
"""

from __future__ import annotations

import pandas as pd


def apply_fraud_rules(features: pd.DataFrame) -> pd.DataFrame:
    """
    Apply fraud detection rules to engineered transaction features.

    Rules are based only on observable transaction behavior.
    Ground-truth fraud labels are intentionally excluded.
    """

    df = features.copy()

    # Rule 1: High transaction velocity
    df["rule_velocity"] = (
        df["transaction_count_2min"] >= 5
    ).astype(int)

    # Rule 2: Large transaction relative to customer history
    df["rule_amount_anomaly"] = (
        df["amount_ratio_to_customer_avg"] >= 3
    ).astype(int)

    # Rule 3: New device
    df["rule_new_device"] = (
        df["is_new_device"] == 1
    ).astype(int)

    # Rule 4: New geographic state
    df["rule_new_state"] = (
        df["is_new_state"] == 1
    ).astype(int)

    # Count how many rules triggered
    rule_columns = [
        "rule_velocity",
        "rule_amount_anomaly",
        "rule_new_device",
        "rule_new_state",
    ]

    df["rules_triggered"] = df[rule_columns].sum(axis=1)

    return df