"""
Fraud strategy evaluation.

This module evaluates fraud detection decisions against
known ground-truth fraud labels.
"""

from __future__ import annotations

import pandas as pd


def evaluate_rules(scored: pd.DataFrame) -> dict:
    """
    Evaluate the overall fraud strategy.

    A transaction is considered predicted fraud when at least
    one fraud rule is triggered.
    """

    df = scored.copy()

    df["predicted_fraud"] = (
        df["rules_triggered"] > 0
    ).astype(int)

    actual = df["is_fraud"]
    predicted = df["predicted_fraud"]

    true_positive = (
        (actual == 1) & (predicted == 1)
    ).sum()

    false_positive = (
        (actual == 0) & (predicted == 1)
    ).sum()

    true_negative = (
        (actual == 0) & (predicted == 0)
    ).sum()

    false_negative = (
        (actual == 1) & (predicted == 0)
    ).sum()

    fraud_capture_rate = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    false_positive_rate = (
        false_positive / (false_positive + true_negative)
        if (false_positive + true_negative) > 0
        else 0
    )

    return {
        "true_positive": int(true_positive),
        "false_positive": int(false_positive),
        "true_negative": int(true_negative),
        "false_negative": int(false_negative),
        "fraud_capture_rate": fraud_capture_rate,
        "precision": precision,
        "false_positive_rate": false_positive_rate,
    }


def evaluate_individual_rules(scored: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate each fraud rule independently.

    Measures:
        - number of transactions flagged
        - true positives
        - false positives
        - precision
    """

    rule_columns = [
        "rule_velocity",
        "rule_amount_anomaly",
        "rule_new_device",
        "rule_new_state",
    ]

    results = []

    for rule in rule_columns:

        flagged = scored[rule] == 1
        actual_fraud = scored["is_fraud"] == 1

        true_positive = (
            flagged & actual_fraud
        ).sum()

        false_positive = (
            flagged & ~actual_fraud
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
                "transactions_flagged": int(total_flagged),
                "true_positives": int(true_positive),
                "false_positives": int(false_positive),
                "precision": precision,
            }
        )

    return pd.DataFrame(results)
def evaluate_strategy(
    scored: pd.DataFrame,
    strategy_name: str,
    prediction: pd.Series,
) -> dict:
    """
    Evaluate a specific fraud decisioning strategy.
    """

    actual = scored["is_fraud"]

    predicted = prediction.astype(int)

    true_positive = (
        (actual == 1) & (predicted == 1)
    ).sum()

    false_positive = (
        (actual == 0) & (predicted == 1)
    ).sum()

    true_negative = (
        (actual == 0) & (predicted == 0)
    ).sum()

    false_negative = (
        (actual == 1) & (predicted == 0)
    ).sum()

    fraud_capture_rate = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    false_positive_rate = (
        false_positive / (false_positive + true_negative)
        if (false_positive + true_negative) > 0
        else 0
    )

    return {
        "strategy": strategy_name,
        "true_positive": int(true_positive),
        "false_positive": int(false_positive),
        "true_negative": int(true_negative),
        "false_negative": int(false_negative),
        "fraud_capture_rate": fraud_capture_rate,
        "precision": precision,
        "false_positive_rate": false_positive_rate,
    }

if __name__ == "__main__":

    from src.data_generation import (
        generate_customers,
        generate_accounts,
        generate_transactions,
    )

    from src.feature_engineering import build_features
    from src.rules_engine import apply_fraud_rules

    print("Generating synthetic banking data...")

    customers = generate_customers()

    accounts = generate_accounts(
        customers
    )

    transactions = generate_transactions(
        customers,
        accounts
    )

    print("Building fraud features...")

    features = build_features(
        transactions
    )

    print("Applying fraud rules...")

    scored = apply_fraud_rules(
        features
    )

    # --------------------------------------------------
    # Overall strategy evaluation
    # --------------------------------------------------

    print("Evaluating fraud strategy...")

    metrics = evaluate_rules(
        scored
    )

    print()
    print("FRAUD STRATEGY EVALUATION")
    print("--------------------------")

    print(
        f"True Positives       : "
        f"{metrics['true_positive']}"
    )

    print(
        f"False Positives      : "
        f"{metrics['false_positive']}"
    )

    print(
        f"True Negatives       : "
        f"{metrics['true_negative']}"
    )

    print(
        f"False Negatives      : "
        f"{metrics['false_negative']}"
    )

    print(
        f"Fraud Capture Rate   : "
        f"{metrics['fraud_capture_rate']:.2%}"
    )

    print(
        f"Precision            : "
        f"{metrics['precision']:.2%}"
    )

    print(
        f"False Positive Rate  : "
        f"{metrics['false_positive_rate']:.2%}"
    )

    # --------------------------------------------------
    # Individual rule performance
    # --------------------------------------------------

    rule_results = evaluate_individual_rules(
        scored
    )

    print()
    print("INDIVIDUAL RULE PERFORMANCE")
    print("----------------------------")

    print(
        rule_results.to_string(
            index=False,
            formatters={
                "precision": "{:.2%}".format
            }
        )
    )

    # --------------------------------------------------
    # Fraud type detection
    # --------------------------------------------------

    print()
    print("FRAUD TYPE DETECTION")
    print("--------------------")

    fraud_types = [
        "account_takeover",
        "velocity_fraud",
        "geographic_anomaly",
    ]

    for fraud_type in fraud_types:

        fraud_subset = scored[
            scored["fraud_type"] == fraud_type
        ]

        detected = (
            fraud_subset["rules_triggered"] > 0
        ).sum()

        total = len(fraud_subset)

        capture_rate = (
            detected / total
            if total > 0
            else 0
        )

        print(
            f"{fraud_type:25} "
            f"{detected:4} / {total:4} "
            f"({capture_rate:.2%})"
        )

    # --------------------------------------------------
    # Strategy comparison
    # --------------------------------------------------

    strategy_results = []

    # Strategy A:
    # Any rule triggers fraud.
    prediction_a = (
        scored["rules_triggered"] >= 1
    )

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Any rule",
            prediction_a,
        )
    )

    # Strategy B:
    # Only strong signals trigger fraud.
    prediction_b = (
        (scored["rule_velocity"] == 1)
        | (scored["rule_new_device"] == 1)
    )

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Velocity OR new device",
            prediction_b,
        )
    )

    # Strategy C:
    # Strong signals OR a combination of
    # amount anomaly and geographic change.
    prediction_c = (
        (scored["rule_velocity"] == 1)
        | (scored["rule_new_device"] == 1)
        | (
            (scored["rule_amount_anomaly"] == 1)
            & (scored["rule_new_state"] == 1)
        )
    )

    strategy_results.append(
        evaluate_strategy(
            scored,
            "Strong signals OR amount+state",
            prediction_c,
        )
    )

    strategy_comparison = pd.DataFrame(
        strategy_results
    )

    print()
    print("STRATEGY COMPARISON")
    print("-------------------")

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
                "fraud_capture_rate": "{:.2%}".format,
                "precision": "{:.2%}".format,
                "false_positive_rate": "{:.2%}".format,
            },
        )
    )