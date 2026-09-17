"""
Fraud strategy evaluation.

This module evaluates fraud detection rules,
risk scores, decision bands, and threshold strategies.
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
from src.risk_scoring import calculate_risk_score, assign_decision


# --------------------------------------------------
# Rule evaluation
# --------------------------------------------------

def evaluate_rules(scored: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate the combined fraud-rule strategy.

    A transaction is considered flagged when at least
    one fraud rule is triggered.
    """

    df = scored.copy()

    df["predicted_fraud"] = (
        df["rules_triggered"] > 0
    ).astype(int)

    true_positive = (
        (df["predicted_fraud"] == 1)
        & (df["is_fraud"] == 1)
    ).sum()

    false_positive = (
        (df["predicted_fraud"] == 1)
        & (df["is_fraud"] == 0)
    ).sum()

    true_negative = (
        (df["predicted_fraud"] == 0)
        & (df["is_fraud"] == 0)
    ).sum()

    false_negative = (
        (df["predicted_fraud"] == 0)
        & (df["is_fraud"] == 1)
    ).sum()

    total_fraud = df["is_fraud"].sum()
    total_non_fraud = (df["is_fraud"] == 0).sum()

    fraud_capture_rate = (
        true_positive / total_fraud
        if total_fraud > 0
        else 0
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    false_positive_rate = (
        false_positive / total_non_fraud
        if total_non_fraud > 0
        else 0
    )

    return pd.DataFrame(
        [
            {
                "true_positive": true_positive,
                "false_positive": false_positive,
                "true_negative": true_negative,
                "false_negative": false_negative,
                "fraud_capture_rate": fraud_capture_rate,
                "precision": precision,
                "false_positive_rate": false_positive_rate,
            }
        ]
    )


# --------------------------------------------------
# Individual rule evaluation
# --------------------------------------------------

def evaluate_individual_rules(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """
    Evaluate each fraud rule independently.
    """

    rule_columns = [
        "rule_velocity",
        "rule_new_device",
        "rule_amount_anomaly",
        "rule_new_state",
    ]

    results = []

    for rule in rule_columns:

        flagged = scored[rule] == 1

        true_positive = (
            flagged
            & (scored["is_fraud"] == 1)
        ).sum()

        false_positive = (
            flagged
            & (scored["is_fraud"] == 0)
        ).sum()

        total_flagged = flagged.sum()

        precision = (
            true_positive / total_flagged
            if total_flagged > 0
            else 0
        )

        results.append(
            {
                "rule": rule,
                "flagged": total_flagged,
                "true_positive": true_positive,
                "false_positive": false_positive,
                "precision": precision,
            }
        )

    return pd.DataFrame(results)


# --------------------------------------------------
# Generic strategy evaluation
# --------------------------------------------------

def evaluate_strategy(
    scored: pd.DataFrame,
    strategy_name: str,
    prediction: pd.Series,
) -> dict:
    """
    Evaluate an arbitrary fraud detection strategy.
    """

    prediction = prediction.astype(int)

    true_positive = (
        (prediction == 1)
        & (scored["is_fraud"] == 1)
    ).sum()

    false_positive = (
        (prediction == 1)
        & (scored["is_fraud"] == 0)
    ).sum()

    true_negative = (
        (prediction == 0)
        & (scored["is_fraud"] == 0)
    ).sum()

    false_negative = (
        (prediction == 0)
        & (scored["is_fraud"] == 1)
    ).sum()

    total_fraud = scored["is_fraud"].sum()
    total_non_fraud = (
        scored["is_fraud"] == 0
    ).sum()

    fraud_capture_rate = (
        true_positive / total_fraud
        if total_fraud > 0
        else 0
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    false_positive_rate = (
        false_positive / total_non_fraud
        if total_non_fraud > 0
        else 0
    )

    return {
        "strategy": strategy_name,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "true_negative": true_negative,
        "false_negative": false_negative,
        "fraud_capture_rate": fraud_capture_rate,
        "precision": precision,
        "false_positive_rate": false_positive_rate,
    }


# --------------------------------------------------
# Decision band evaluation
# --------------------------------------------------

def evaluate_decision_bands(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """
    Evaluate APPROVE, REVIEW, and DECLINE decision bands.
    """

    results = []

    total_transactions = len(scored)

    for decision in [
        "APPROVE",
        "REVIEW",
        "DECLINE",
    ]:

        subset = scored[
            scored["decision"] == decision
        ]

        transaction_count = len(subset)
        fraud_count = subset["is_fraud"].sum()

        transaction_pct = (
            transaction_count / total_transactions
            if total_transactions > 0
            else 0
        )

        fraud_rate = (
            fraud_count / transaction_count
            if transaction_count > 0
            else 0
        )

        results.append(
            {
                "decision": decision,
                "transaction_count": transaction_count,
                "transaction_pct": transaction_pct,
                "fraud_count": fraud_count,
                "fraud_rate": fraud_rate,
            }
        )

    return pd.DataFrame(results)


# --------------------------------------------------
# Risk score evaluation
# --------------------------------------------------

def evaluate_risk_scores(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """
    Evaluate fraud rate at each observed risk score.
    """

    results = []

    for score in sorted(
        scored["risk_score"].unique()
    ):

        subset = scored[
            scored["risk_score"] == score
        ]

        transaction_count = len(subset)
        fraud_count = subset["is_fraud"].sum()

        fraud_rate = (
            fraud_count / transaction_count
            if transaction_count > 0
            else 0
        )

        results.append(
            {
                "risk_score": score,
                "transaction_count": transaction_count,
                "fraud_count": fraud_count,
                "fraud_rate": fraud_rate,
            }
        )

    return pd.DataFrame(results)


# --------------------------------------------------
# Threshold optimization
# --------------------------------------------------

def evaluate_thresholds(
    scored: pd.DataFrame,
    review_thresholds: list[int],
    decline_thresholds: list[int],
) -> pd.DataFrame:
    """
    Evaluate different review and decline thresholds.

    Decision logic:

        score < review threshold
            APPROVE

        review threshold <= score < decline threshold
            REVIEW

        score >= decline threshold
            DECLINE

    Fraud capture rate measures the percentage of all
    fraud transactions sent to REVIEW or DECLINE.
    """

    results = []

    total_transactions = len(scored)
    total_fraud = scored["is_fraud"].sum()

    for review_threshold in review_thresholds:

        for decline_threshold in decline_thresholds:

            if review_threshold >= decline_threshold:
                continue

            approve = (
                scored["risk_score"]
                < review_threshold
            )

            review = (
                (scored["risk_score"] >= review_threshold)
                & (
                    scored["risk_score"]
                    < decline_threshold
                )
            )

            decline = (
                scored["risk_score"]
                >= decline_threshold
            )

            approve_count = approve.sum()
            review_count = review.sum()
            decline_count = decline.sum()

            approve_fraud = (
                scored.loc[
                    approve,
                    "is_fraud",
                ].sum()
            )

            review_fraud = (
                scored.loc[
                    review,
                    "is_fraud",
                ].sum()
            )

            decline_fraud = (
                scored.loc[
                    decline,
                    "is_fraud",
                ].sum()
            )

            captured_fraud = (
                review_fraud
                + decline_fraud
            )

            approve_pct = (
                approve_count / total_transactions
                if total_transactions > 0
                else 0
            )

            review_pct = (
                review_count / total_transactions
                if total_transactions > 0
                else 0
            )

            decline_pct = (
                decline_count / total_transactions
                if total_transactions > 0
                else 0
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

            results.append(
                {
                    "review_threshold": review_threshold,
                    "decline_threshold": decline_threshold,
                    "approve_pct": approve_pct,
                    "review_pct": review_pct,
                    "decline_pct": decline_pct,
                    "fraud_capture_rate": fraud_capture_rate,
                    "approve_fraud_rate": approve_fraud_rate,
                    "review_fraud_rate": review_fraud_rate,
                    "decline_fraud_rate": decline_fraud_rate,
                }
            )

    return pd.DataFrame(results)


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
    # Build fraud features
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
    # Calculate risk score
    # --------------------------------------------------

    scored = calculate_risk_score(
        scored
    )

    # --------------------------------------------------
    # Assign decision
    # --------------------------------------------------

    scored = assign_decision(
        scored
    )

    # --------------------------------------------------
    # Overall rule evaluation
    # --------------------------------------------------

    overall_results = evaluate_rules(
        scored
    )

    print()
    print(
        "OVERALL RULE EVALUATION"
    )
    print(
        "-----------------------"
    )

    print(
        overall_results.to_string(
            index=False,
            formatters={
                "fraud_capture_rate":
                    "{:.2%}".format,
                "precision":
                    "{:.2%}".format,
                "false_positive_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Individual rule evaluation
    # --------------------------------------------------

    individual_results = (
        evaluate_individual_rules(
            scored
        )
    )

    print()
    print(
        "INDIVIDUAL RULE EVALUATION"
    )
    print(
        "--------------------------"
    )

    print(
        individual_results.to_string(
            index=False,
            formatters={
                "precision":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Fraud type detection
    # --------------------------------------------------

    fraud_types = []

    for fraud_type in sorted(
        scored.loc[
            scored["is_fraud"] == 1,
            "fraud_type",
        ].dropna().unique()
    ):

        subset = scored[
            scored["fraud_type"] == fraud_type
        ]

        detected = (
            subset["rules_triggered"] > 0
        ).sum()

        total = len(subset)

        capture_rate = (
            detected / total
            if total > 0
            else 0
        )

        fraud_types.append(
            {
                "fraud_type": fraud_type,
                "detected": detected,
                "total": total,
                "capture_rate": capture_rate,
            }
        )

    fraud_type_results = pd.DataFrame(
        fraud_types
    )

    print()
    print(
        "FRAUD TYPE DETECTION"
    )
    print(
        "--------------------"
    )

    print(
        fraud_type_results.to_string(
            index=False,
            formatters={
                "capture_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Strategy comparison
    # --------------------------------------------------

    strategy_results = []

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Any rule",
            scored["rules_triggered"] > 0,
        )
    )

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Velocity OR new device",
            (
                (scored["rule_velocity"] == 1)
                | (
                    scored["rule_new_device"] == 1
                )
            ),
        )
    )

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Strong signals OR amount+state",
            (
                (scored["rule_velocity"] == 1)
                | (
                    scored["rule_new_device"] == 1
                )
                | (
                    (
                        scored["rule_amount_anomaly"]
                        == 1
                    )
                    & (
                        scored["rule_new_state"]
                        == 1
                    )
                )
            ),
        )
    )

    strategy_comparison = pd.DataFrame(
        strategy_results
    )

    print()
    print(
        "STRATEGY COMPARISON"
    )
    print(
        "-------------------"
    )

    print(
        strategy_comparison[
            [
                "strategy",
                "true_positive",
                "false_positive",
                "fraud_capture_rate",
                "precision",
                "false_positive_rate",
            ]
        ].to_string(
            index=False,
            formatters={
                "fraud_capture_rate":
                    "{:.2%}".format,
                "precision":
                    "{:.2%}".format,
                "false_positive_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Decision band evaluation
    # --------------------------------------------------

    decision_results = (
        evaluate_decision_bands(
            scored
        )
    )

    print()
    print(
        "DECISION BAND EVALUATION"
    )
    print(
        "------------------------"
    )

    print(
        decision_results.to_string(
            index=False,
            formatters={
                "transaction_pct":
                    "{:.2%}".format,
                "fraud_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Risk score evaluation
    # --------------------------------------------------

    score_results = (
        evaluate_risk_scores(
            scored
        )
    )

    print()
    print(
        "RISK SCORE EVALUATION"
    )
    print(
        "---------------------"
    )

    print(
        score_results.to_string(
            index=False,
            formatters={
                "fraud_rate":
                    "{:.2%}".format,
            },
        )
    )

    # --------------------------------------------------
    # Threshold optimization
    # --------------------------------------------------

    threshold_results = evaluate_thresholds(
        scored,
        review_thresholds=[
            10,
            15,
            20,
            25,
            30,
        ],
        decline_thresholds=[
            35,
            40,
            45,
            50,
            55,
            60,
        ],
    )

    print()
    print(
        "THRESHOLD OPTIMIZATION"
    )
    print(
        "----------------------"
    )

    print(
        threshold_results.to_string(
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
                "approve_fraud_rate":
                    "{:.2%}".format,
                "review_fraud_rate":
                    "{:.2%}".format,
                "decline_fraud_rate":
                    "{:.2%}".format,
            },
        )
    )