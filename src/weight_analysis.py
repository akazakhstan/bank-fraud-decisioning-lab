"""
Fraud risk-weight sensitivity analysis.

Tests how different risk-weight configurations affect
fraud detection performance and decision outcomes.
"""

from __future__ import annotations

import pandas as pd

from src.data_generation import (
    generate_customers,
    generate_accounts,
    generate_transactions,
)

from src.feature_engineering import build_features
from src.rules_engine import apply_fraud_rules


# --------------------------------------------------
# Risk scoring
# --------------------------------------------------

def calculate_custom_score(
    scored: pd.DataFrame,
    velocity_weight: int,
    new_device_weight: int,
    amount_weight: int,
    new_state_weight: int,
) -> pd.Series:
    """
    Calculate a risk score using custom signal weights.
    """

    return (
        scored["rule_velocity"] * velocity_weight
        + scored["rule_new_device"] * new_device_weight
        + scored["rule_amount_anomaly"] * amount_weight
        + scored["rule_new_state"] * new_state_weight
    )


# --------------------------------------------------
# Strategy evaluation
# --------------------------------------------------

def evaluate_weight_strategy(
    scored: pd.DataFrame,
    strategy_name: str,
    velocity_weight: int,
    new_device_weight: int,
    amount_weight: int,
    new_state_weight: int,
    review_threshold: int = 20,
    decline_threshold: int = 60,
) -> dict:
    """
    Evaluate one risk-weight configuration.
    """

    df = scored.copy()

    df["risk_score_test"] = calculate_custom_score(
        df,
        velocity_weight,
        new_device_weight,
        amount_weight,
        new_state_weight,
    )

    df["decision_test"] = "APPROVE"

    df.loc[
        df["risk_score_test"] >= review_threshold,
        "decision_test",
    ] = "REVIEW"

    df.loc[
        df["risk_score_test"] >= decline_threshold,
        "decision_test",
    ] = "DECLINE"

    total_transactions = len(df)
    total_fraud = df["is_fraud"].sum()

    approve = df["decision_test"] == "APPROVE"
    review = df["decision_test"] == "REVIEW"
    decline = df["decision_test"] == "DECLINE"

    approve_count = approve.sum()
    review_count = review.sum()
    decline_count = decline.sum()

    approve_fraud = df.loc[
        approve,
        "is_fraud",
    ].sum()

    review_fraud = df.loc[
        review,
        "is_fraud",
    ].sum()

    decline_fraud = df.loc[
        decline,
        "is_fraud",
    ].sum()

    captured_fraud = (
        review_fraud
        + decline_fraud
    )

    fraud_capture_rate = (
        captured_fraud / total_fraud
        if total_fraud > 0
        else 0
    )

    approve_fraud_rate = (
        approve_fraud / approve_count
        if approve_count > 0
        else 0
    )

    review_fraud_rate = (
        review_fraud / review_count
        if review_count > 0
        else 0
    )

    decline_fraud_rate = (
        decline_fraud / decline_count
        if decline_count > 0
        else 0
    )

    # Fraud precision for transactions sent
    # to REVIEW or DECLINE.
    flagged_count = (
        review_count + decline_count
    )

    precision = (
        captured_fraud / flagged_count
        if flagged_count > 0
        else 0
    )

    return {
        "strategy": strategy_name,
        "velocity_weight": velocity_weight,
        "new_device_weight": new_device_weight,
        "amount_weight": amount_weight,
        "new_state_weight": new_state_weight,
        "approve_pct": (
            approve_count / total_transactions
        ),
        "review_pct": (
            review_count / total_transactions
        ),
        "decline_pct": (
            decline_count / total_transactions
        ),
        "fraud_capture_rate": fraud_capture_rate,
        "precision": precision,
        "approve_fraud_rate": approve_fraud_rate,
        "review_fraud_rate": review_fraud_rate,
        "decline_fraud_rate": decline_fraud_rate,
    }


# ==================================================
# Main execution
# ==================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Generate synthetic dataset
    # --------------------------------------------------

    customers = generate_customers()

    accounts = generate_accounts(
        customers
    )

    transactions = generate_transactions(
        customers,
        accounts
    )

    # --------------------------------------------------
    # Build features
    # --------------------------------------------------

    features = build_features(
        transactions
    )

    # --------------------------------------------------
    # Apply fraud rules
    # --------------------------------------------------

    scored = apply_fraud_rules(
        features
    )

    # --------------------------------------------------
    # Define strategies
    # --------------------------------------------------

    strategies = [
        {
            "name": "Baseline",
            "velocity": 40,
            "new_device": 35,
            "amount": 15,
            "new_state": 10,
        },
        {
            "name": "Velocity Emphasis",
            "velocity": 50,
            "new_device": 30,
            "amount": 10,
            "new_state": 10,
        },
        {
            "name": "New Device Emphasis",
            "velocity": 30,
            "new_device": 45,
            "amount": 15,
            "new_state": 10,
        },
        {
            "name": "Reduced New State",
            "velocity": 40,
            "new_device": 40,
            "amount": 15,
            "new_state": 5,
        },
        {
            "name": "Strong Velocity",
            "velocity": 45,
            "new_device": 35,
            "amount": 15,
            "new_state": 5,
        },
        {
            "name": "Amount Emphasis",
            "velocity": 35,
            "new_device": 35,
            "amount": 20,
            "new_state": 10,
        },
    ]

    # --------------------------------------------------
    # Evaluate strategies
    # --------------------------------------------------

    results = []

    for strategy in strategies:

        result = evaluate_weight_strategy(
            scored=scored,
            strategy_name=strategy["name"],
            velocity_weight=strategy["velocity"],
            new_device_weight=strategy["new_device"],
            amount_weight=strategy["amount"],
            new_state_weight=strategy["new_state"],
        )

        results.append(result)

    results_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------
    # Display results
    # --------------------------------------------------

    print()
    print(
        "RISK WEIGHT SENSITIVITY ANALYSIS"
    )
    print(
        "================================"
    )

    print()

    print(
        results_df[
            [
                "strategy",
                "velocity_weight",
                "new_device_weight",
                "amount_weight",
                "new_state_weight",
                "approve_pct",
                "review_pct",
                "decline_pct",
                "fraud_capture_rate",
                "precision",
                "approve_fraud_rate",
                "review_fraud_rate",
                "decline_fraud_rate",
            ]
        ].to_string(
            index=False,
            formatters={
                "approve_pct":
                    "{:.2%}".format,
                "review_pct":
                    "{:.2%}".format,
                "decline_pct":
                    "{:.2%}".format,
                "fraud_capture_rate":
                    "{:.2%}".format,
                "precision":
                    "{:.2%}".format,
                "approve_fraud_rate":
                    "{:.2%}".format,
                "review_fraud_rate":
                    "{:.2%}".format,
                "decline_fraud_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Rank strategies
    # --------------------------------------------------

    ranked = results_df.sort_values(
        [
            "fraud_capture_rate",
            "precision",
        ],
        ascending=False,
    )

    print()
    print(
        "STRATEGY RANKING"
    )
    print(
        "================"
    )

    print()

    print(
        ranked[
            [
                "strategy",
                "fraud_capture_rate",
                "precision",
                "approve_pct",
                "review_pct",
                "decline_pct",
            ]
        ].to_string(
            index=False,
            formatters={
                "fraud_capture_rate":
                    "{:.2%}".format,
                "precision":
                    "{:.2%}".format,
                "approve_pct":
                    "{:.2%}".format,
                "review_pct":
                    "{:.2%}".format,
                "decline_pct":
                    "{:.2%}".format,
            },
        )
    )