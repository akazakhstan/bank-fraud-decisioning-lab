"""
Fraud strategy grid search.

Systematically evaluates combinations of:
    - Risk weights
    - Review thresholds
    - Decline thresholds

The objective is to identify strategies that balance
fraud capture, precision, and operational workload.
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
# Strategy evaluation
# --------------------------------------------------

def evaluate_strategy(
    scored: pd.DataFrame,
    velocity_weight: int,
    new_device_weight: int,
    amount_weight: int,
    new_state_weight: int,
    review_threshold: int,
    decline_threshold: int,
) -> dict:
    """
    Evaluate one complete fraud decisioning strategy.
    """

    df = scored.copy()

    # Calculate risk score
    df["risk_score"] = calculate_score(
        df,
        velocity_weight,
        new_device_weight,
        amount_weight,
        new_state_weight,
    )

    # Apply decision bands
    df["decision"] = "APPROVE"

    df.loc[
        df["risk_score"] >= review_threshold,
        "decision",
    ] = "REVIEW"

    df.loc[
        df["risk_score"] >= decline_threshold,
        "decision",
    ] = "DECLINE"

    total_transactions = len(df)
    total_fraud = df["is_fraud"].sum()

    # Decision masks
    approve = df["decision"] == "APPROVE"
    review = df["decision"] == "REVIEW"
    decline = df["decision"] == "DECLINE"

    # Transaction volumes
    approve_count = approve.sum()
    review_count = review.sum()
    decline_count = decline.sum()

    # Fraud volumes
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

    # Fraud captured by intervention
    captured_fraud = (
        review_fraud
        + decline_fraud
    )

    # Rates
    fraud_capture_rate = (
        captured_fraud / total_fraud
        if total_fraud > 0
        else 0
    )

    precision = (
        captured_fraud
        / (review_count + decline_count)
        if (review_count + decline_count) > 0
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

    approve_pct = (
        approve_count / total_transactions
    )

    review_pct = (
        review_count / total_transactions
    )

    decline_pct = (
        decline_count / total_transactions
    )

    return {
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
        "approve_fraud_rate": approve_fraud_rate,
        "review_fraud_rate": review_fraud_rate,
        "decline_fraud_rate": decline_fraud_rate,
    }


# --------------------------------------------------
# Generate weight combinations
# --------------------------------------------------

def generate_weight_combinations() -> list[dict]:
    """
    Generate valid weight combinations.

    All weights must sum to exactly 100.
    """

    combinations = []

    for velocity in range(20, 51, 5):

        for new_device in range(20, 51, 5):

            for amount in range(10, 31, 5):

                for new_state in range(0, 21, 5):

                    total = (
                        velocity
                        + new_device
                        + amount
                        + new_state
                    )

                    if total == 100:

                        combinations.append(
                            {
                                "velocity": velocity,
                                "new_device": new_device,
                                "amount": amount,
                                "new_state": new_state,
                            }
                        )

    return combinations


# ==================================================
# Main execution
# ==================================================

if __name__ == "__main__":

    # --------------------------------------------------
    # Generate synthetic data
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
    # Generate weight combinations
    # --------------------------------------------------

    weight_combinations = (
        generate_weight_combinations()
    )

    print()
    print(
        f"Weight combinations: "
        f"{len(weight_combinations)}"
    )

    # --------------------------------------------------
    # Define thresholds
    # --------------------------------------------------

    review_thresholds = [
        10,
        15,
        20,
        25,
        30,
    ]

    decline_thresholds = [
        35,
        40,
        45,
        50,
        55,
        60,
    ]

    # --------------------------------------------------
    # Run grid search
    # --------------------------------------------------

    print(
        "Running strategy grid search..."
    )

    results = []

    total_combinations = (
        len(weight_combinations)
        * len(review_thresholds)
        * len(decline_thresholds)
    )

    completed = 0

    for weights in weight_combinations:

        for review_threshold in review_thresholds:

            for decline_threshold in decline_thresholds:

                if (
                    review_threshold
                    >= decline_threshold
                ):
                    continue

                result = evaluate_strategy(
                    scored=scored,
                    velocity_weight=weights[
                        "velocity"
                    ],
                    new_device_weight=weights[
                        "new_device"
                    ],
                    amount_weight=weights[
                        "amount"
                    ],
                    new_state_weight=weights[
                        "new_state"
                    ],
                    review_threshold=review_threshold,
                    decline_threshold=decline_threshold,
                )

                results.append(result)

                completed += 1

    results_df = pd.DataFrame(
        results
    )

    print(
        f"Completed strategies: "
        f"{len(results_df)}"
    )

    # --------------------------------------------------
    # Apply operational constraints
    # --------------------------------------------------

    qualified = results_df[
        (results_df["fraud_capture_rate"] >= 0.85)
        & (results_df["review_pct"] <= 0.10)
        & (results_df["decline_pct"] <= 0.01)
    ].copy()

    # --------------------------------------------------
    # Rank qualified strategies
    # --------------------------------------------------

    qualified = qualified.sort_values(
        [
            "fraud_capture_rate",
            "precision",
            "approve_pct",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    # --------------------------------------------------
    # Display results
    # --------------------------------------------------

    print()
    print(
        "QUALIFIED STRATEGIES"
    )
    print(
        "===================="
    )

    print()

    print(
        f"Strategies meeting constraints: "
        f"{len(qualified)}"
    )

    if len(qualified) > 0:

        print()

        print(
            qualified.head(20).to_string(
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

    else:

        print()
        print(
            "No strategies met all constraints."
        )

    # --------------------------------------------------
    # Highest fraud capture
    # --------------------------------------------------

    highest_capture = results_df.sort_values(
        [
            "fraud_capture_rate",
            "precision",
        ],
        ascending=False,
    )

    print()
    print(
        "TOP STRATEGIES BY FRAUD CAPTURE"
    )
    print(
        "==============================="
    )

    print()

    print(
        highest_capture.head(10).to_string(
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
    # Highest precision
    # --------------------------------------------------

    highest_precision = results_df[
        results_df["review_pct"] <= 0.10
    ].sort_values(
        [
            "precision",
            "fraud_capture_rate",
        ],
        ascending=False,
    )

    print()
    print(
        "TOP STRATEGIES BY PRECISION "
        "(REVIEW <= 10%)"
    )
    print(
        "========================================"
    )

    print()

    print(
        highest_precision.head(10).to_string(
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