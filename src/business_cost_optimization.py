"""
Fraud strategy business-cost optimization.

This module evaluates fraud decisioning strategies using
hypothetical business costs.

IMPORTANT:
The cost assumptions are illustrative and are used only
for the synthetic portfolio experiment.
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
# Cost assumptions
# --------------------------------------------------

MISSED_FRAUD_COST = 500.0
MANUAL_REVIEW_COST = 5.0
FALSE_DECLINE_COST = 25.0


# --------------------------------------------------
# Risk score calculation
# --------------------------------------------------

def calculate_score(
    scored: pd.DataFrame,
    velocity_weight: int,
    new_device_weight: int,
    amount_weight: int,
    new_state_weight: int,
) -> pd.Series:
    """
    Calculate risk score using specified weights.
    """

    return (
        scored["rule_velocity"] * velocity_weight
        + scored["rule_new_device"] * new_device_weight
        + scored["rule_amount_anomaly"] * amount_weight
        + scored["rule_new_state"] * new_state_weight
    )


# --------------------------------------------------
# Evaluate business cost
# --------------------------------------------------

def evaluate_business_cost(
    scored: pd.DataFrame,
    strategy_name: str,
    velocity_weight: int,
    new_device_weight: int,
    amount_weight: int,
    new_state_weight: int,
    review_threshold: int,
    decline_threshold: int,
) -> dict:
    """
    Calculate business cost for one fraud strategy.
    """

    df = scored.copy()

    # --------------------------------------------------
    # Calculate risk score
    # --------------------------------------------------

    df["risk_score"] = calculate_score(
        df,
        velocity_weight,
        new_device_weight,
        amount_weight,
        new_state_weight,
    )

    # --------------------------------------------------
    # Assign decisions
    # --------------------------------------------------

    df["decision"] = "APPROVE"

    df.loc[
        df["risk_score"] >= review_threshold,
        "decision",
    ] = "REVIEW"

    df.loc[
        df["risk_score"] >= decline_threshold,
        "decision",
    ] = "DECLINE"

    # --------------------------------------------------
    # Identify outcomes
    # --------------------------------------------------

    approve = df["decision"] == "APPROVE"
    review = df["decision"] == "REVIEW"
    decline = df["decision"] == "DECLINE"

    # Fraud that was approved = missed fraud
    missed_fraud = (
        approve
        & (df["is_fraud"] == 1)
    )

    # Review workload
    manual_reviews = review.sum()

    # Legitimate transactions declined
    false_declines = (
        decline
        & (df["is_fraud"] == 0)
    )

    # Fraud captured by intervention
    captured_fraud = (
        (
            review
            | decline
        )
        & (df["is_fraud"] == 1)
    ).sum()

    total_fraud = df["is_fraud"].sum()

    # --------------------------------------------------
    # Calculate individual costs
    # --------------------------------------------------

    missed_fraud_cost = (
        missed_fraud.sum()
        * MISSED_FRAUD_COST
    )

    review_cost = (
        manual_reviews
        * MANUAL_REVIEW_COST
    )

    false_decline_cost = (
        false_declines.sum()
        * FALSE_DECLINE_COST
    )

    total_cost = (
        missed_fraud_cost
        + review_cost
        + false_decline_cost
    )

    # --------------------------------------------------
    # Performance metrics
    # --------------------------------------------------

    fraud_capture_rate = (
        captured_fraud / total_fraud
        if total_fraud > 0
        else 0
    )

    precision = (
        captured_fraud
        / (
            review.sum()
            + decline.sum()
        )
        if (
            review.sum()
            + decline.sum()
        ) > 0
        else 0
    )

    approve_count = approve.sum()
    review_count = review.sum()
    decline_count = decline.sum()

    total_transactions = len(df)

    approve_pct = (
        approve_count
        / total_transactions
    )

    review_pct = (
        review_count
        / total_transactions
    )

    decline_pct = (
        decline_count
        / total_transactions
    )

    # --------------------------------------------------
    # Return result
    # --------------------------------------------------

    return {
        "strategy": strategy_name,
        "velocity_weight": velocity_weight,
        "new_device_weight": new_device_weight,
        "amount_weight": amount_weight,
        "new_state_weight": new_state_weight,
        "review_threshold": review_threshold,
        "decline_threshold": decline_threshold,
        "approve_pct": approve_pct,
        "review_pct": review_pct,
        "decline_pct": decline_pct,
        "fraud_capture_rate": fraud_capture_rate,
        "precision": precision,
        "missed_fraud": missed_fraud.sum(),
        "manual_reviews": manual_reviews,
        "false_declines": false_declines.sum(),
        "missed_fraud_cost": missed_fraud_cost,
        "review_cost": review_cost,
        "false_decline_cost": false_decline_cost,
        "total_cost": total_cost,
    }


# ==================================================
# Main execution
# ==================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Generate synthetic dataset
    # --------------------------------------------------

    print()
    print(
        "Generating synthetic fraud dataset..."
    )

    customers = generate_customers()

    accounts = generate_accounts(
        customers
    )

    transactions = generate_transactions(
        customers,
        accounts
    )

    # --------------------------------------------------
    # Feature engineering
    # --------------------------------------------------

    print(
        "Building fraud features..."
    )

    features = build_features(
        transactions
    )

    # --------------------------------------------------
    # Apply fraud rules
    # --------------------------------------------------

    print(
        "Applying fraud rules..."
    )

    scored = apply_fraud_rules(
        features
    )

    # --------------------------------------------------
    # Define candidate strategies
    # --------------------------------------------------

    strategies = [
        {
            "name": "Baseline",
            "velocity": 40,
            "new_device": 35,
            "amount": 15,
            "new_state": 10,
            "review": 20,
            "decline": 60,
        },
        {
            "name": "Amount Emphasis",
            "velocity": 35,
            "new_device": 35,
            "amount": 20,
            "new_state": 10,
            "review": 20,
            "decline": 60,
        },
        {
            "name": "Balanced Higher Capture",
            "velocity": 20,
            "new_device": 35,
            "amount": 30,
            "new_state": 15,
            "review": 20,
            "decline": 50,
        },
        {
            "name": "Balanced Conservative",
            "velocity": 30,
            "new_device": 45,
            "amount": 15,
            "new_state": 10,
            "review": 30,
            "decline": 60,
        },
        {
            "name": "High Capture",
            "velocity": 20,
            "new_device": 30,
            "amount": 30,
            "new_state": 20,
            "review": 10,
            "decline": 55,
        },
    ]

    # --------------------------------------------------
    # Evaluate strategies
    # --------------------------------------------------

    results = []

    for strategy in strategies:

        result = evaluate_business_cost(
            scored=scored,
            strategy_name=strategy["name"],
            velocity_weight=strategy["velocity"],
            new_device_weight=strategy["new_device"],
            amount_weight=strategy["amount"],
            new_state_weight=strategy["new_state"],
            review_threshold=strategy["review"],
            decline_threshold=strategy["decline"],
        )

        results.append(result)

    results_df = pd.DataFrame(
        results
    )

    # --------------------------------------------------
    # Rank by total business cost
    # --------------------------------------------------

    ranked = results_df.sort_values(
        "total_cost"
    )

    # --------------------------------------------------
    # Display results
    # --------------------------------------------------

    print()
    print(
        "BUSINESS COST OPTIMIZATION"
    )
    print(
        "=========================="
    )

    print()

    print(
        "Cost assumptions:"
    )

    print(
        f"Missed fraud: "
        f"${MISSED_FRAUD_COST:,.2f}"
    )

    print(
        f"Manual review: "
        f"${MANUAL_REVIEW_COST:,.2f}"
    )

    print(
        f"False decline: "
        f"${FALSE_DECLINE_COST:,.2f}"
    )

    print()

    print(
        ranked[
            [
                "strategy",
                "velocity_weight",
                "new_device_weight",
                "amount_weight",
                "new_state_weight",
                "review_threshold",
                "decline_threshold",
                "approve_pct",
                "review_pct",
                "decline_pct",
                "fraud_capture_rate",
                "precision",
                "missed_fraud",
                "manual_reviews",
                "false_declines",
                "missed_fraud_cost",
                "review_cost",
                "false_decline_cost",
                "total_cost",
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
                "missed_fraud_cost":
                    "${:,.2f}".format,
                "review_cost":
                    "${:,.2f}".format,
                "false_decline_cost":
                    "${:,.2f}".format,
                "total_cost":
                    "${:,.2f}".format,
            },
        )
    )

    # --------------------------------------------------
    # Best strategy
    # --------------------------------------------------

    best = ranked.iloc[0]

    print()
    print(
        "LOWEST-COST STRATEGY"
    )
    print(
        "===================="
    )

    print()

    print(
        f"Strategy: "
        f"{best['strategy']}"
    )

    print(
        f"Fraud capture: "
        f"{best['fraud_capture_rate']:.2%}"
    )

    print(
        f"Precision: "
        f"{best['precision']:.2%}"
    )

    print(
        f"Review rate: "
        f"{best['review_pct']:.2%}"
    )

    print(
        f"Decline rate: "
        f"{best['decline_pct']:.2%}"
    )

    print(
        f"Total estimated cost: "
        f"${best['total_cost']:,.2f}"
    )