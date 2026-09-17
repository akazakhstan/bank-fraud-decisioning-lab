"""
Time-based train/test validation for fraud decisioning strategies.

Development period:
    January 2026 - April 2026

Holdout period:
    May 2026 - June 2026

The holdout period is evaluated only after the strategy
has been selected using development data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_generation import (
    generate_customers,
    generate_accounts,
    generate_transactions,
)

from feature_engineering import build_features
from rules_engine import apply_fraud_rules


REPORTS_DIR = Path("reports")

SPLIT_DATE = pd.Timestamp("2026-05-01")

MISSED_FRAUD_COST = 500
MANUAL_REVIEW_COST = 5
FALSE_DECLINE_COST = 25


STRATEGIES = {
    "Baseline": {
        "weights": {
            "rule_velocity": 40,
            "rule_new_device": 35,
            "rule_amount_anomaly": 15,
            "rule_new_state": 10,
        },
        "review_threshold": 20,
        "decline_threshold": 60,
    },
    "Amount Emphasis": {
        "weights": {
            "rule_velocity": 35,
            "rule_new_device": 35,
            "rule_amount_anomaly": 20,
            "rule_new_state": 10,
        },
        "review_threshold": 20,
        "decline_threshold": 60,
    },
    "Balanced Higher Capture": {
        "weights": {
            "rule_velocity": 20,
            "rule_new_device": 35,
            "rule_amount_anomaly": 30,
            "rule_new_state": 15,
        },
        "review_threshold": 20,
        "decline_threshold": 50,
    },
    "Balanced Conservative": {
        "weights": {
            "rule_velocity": 30,
            "rule_new_device": 45,
            "rule_amount_anomaly": 15,
            "rule_new_state": 10,
        },
        "review_threshold": 30,
        "decline_threshold": 60,
    },
    "High Capture": {
        "weights": {
            "rule_velocity": 20,
            "rule_new_device": 30,
            "rule_amount_anomaly": 30,
            "rule_new_state": 20,
        },
        "review_threshold": 10,
        "decline_threshold": 55,
    },
}


def score_transactions(
    scored: pd.DataFrame,
    weights: dict[str, int],
) -> pd.DataFrame:
    """Calculate a risk score using supplied strategy weights."""

    df = scored.copy()

    df["risk_score"] = (
        df["rule_velocity"] * weights["rule_velocity"]
        + df["rule_new_device"] * weights["rule_new_device"]
        + df["rule_amount_anomaly"] * weights["rule_amount_anomaly"]
        + df["rule_new_state"] * weights["rule_new_state"]
    )

    return df


def assign_decisions(
    scored: pd.DataFrame,
    review_threshold: int,
    decline_threshold: int,
) -> pd.DataFrame:
    """Assign APPROVE, REVIEW, or DECLINE decisions."""

    df = scored.copy()

    df["decision"] = "APPROVE"

    df.loc[
        df["risk_score"] >= review_threshold,
        "decision",
    ] = "REVIEW"

    df.loc[
        df["risk_score"] >= decline_threshold,
        "decision",
    ] = "DECLINE"

    return df


def evaluate_strategy(
    scored: pd.DataFrame,
) -> dict[str, float]:
    """
    Evaluate fraud decisioning performance.

    Fraud Interception Rate:
        Fraud transactions sent to REVIEW or DECLINE.

    Fraud Block Rate:
        Fraud transactions sent to DECLINE.

    Missed Fraud Rate:
        Fraud transactions incorrectly APPROVED.
    """

    total = len(scored)

    fraud = scored["is_fraud"] == 1
    non_fraud = scored["is_fraud"] == 0

    approve = scored["decision"] == "APPROVE"
    review = scored["decision"] == "REVIEW"
    decline = scored["decision"] == "DECLINE"

    total_fraud = fraud.sum()

    intercepted_fraud = (
        fraud & (review | decline)
    ).sum()

    blocked_fraud = (
        fraud & decline
    ).sum()

    missed_fraud = (
        fraud & approve
    ).sum()

    manual_reviews = review.sum()

    false_declines = (
        non_fraud & decline
    ).sum()

    decline_count = decline.sum()

    fraud_interception_rate = (
        intercepted_fraud / total_fraud * 100
        if total_fraud > 0
        else 0
    )

    fraud_block_rate = (
        blocked_fraud / total_fraud * 100
        if total_fraud > 0
        else 0
    )

    missed_fraud_rate = (
        missed_fraud / total_fraud * 100
        if total_fraud > 0
        else 0
    )

    review_rate = (
        manual_reviews / total * 100
        if total > 0
        else 0
    )

    decline_rate = (
        decline_count / total * 100
        if total > 0
        else 0
    )

    decline_precision = (
        blocked_fraud / decline_count * 100
        if decline_count > 0
        else 0
    )

    estimated_cost = (
        missed_fraud * MISSED_FRAUD_COST
        + manual_reviews * MANUAL_REVIEW_COST
        + false_declines * FALSE_DECLINE_COST
    )

    return {
        "transactions": total,
        "fraud_transactions": int(total_fraud),
        "fraud_interception_rate": fraud_interception_rate,
        "fraud_block_rate": fraud_block_rate,
        "missed_fraud_rate": missed_fraud_rate,
        "review_rate": review_rate,
        "decline_rate": decline_rate,
        "decline_precision": decline_precision,
        "missed_fraud": int(missed_fraud),
        "manual_reviews": int(manual_reviews),
        "false_declines": int(false_declines),
        "estimated_cost": estimated_cost,
    }


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate and chronologically split the raw transaction data."""

    print("Generating synthetic banking dataset...")

    customers = generate_customers()
    accounts = generate_accounts(customers)
    transactions = generate_transactions(
        customers,
        accounts,
    )

    transactions["timestamp"] = pd.to_datetime(
        transactions["timestamp"]
    )

    transactions = transactions.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    development = transactions[
        transactions["timestamp"] < SPLIT_DATE
    ].copy()

    holdout = transactions[
        transactions["timestamp"] >= SPLIT_DATE
    ].copy()

    return development, holdout


def build_development_features(
    development: pd.DataFrame,
) -> pd.DataFrame:
    """Build features using development transactions only."""

    print("Building development features...")

    features = build_features(
        development
    )

    return apply_fraud_rules(features)


def build_holdout_features(
    development: pd.DataFrame,
    holdout: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build holdout features while preserving historical context.

    The feature engine receives the complete chronological history,
    but only May-June transactions are returned for evaluation.

    Because feature calculations are causal, each transaction can
    use information available before or at that transaction's time.
    """

    print("Building holdout features with historical context...")

    combined = pd.concat(
        [development, holdout],
        ignore_index=True,
    )

    features = build_features(
        combined
    )

    features = apply_fraud_rules(
        features
    )

    holdout_ids = set(
        holdout["transaction_id"]
    )

    features = features[
        features["transaction_id"].isin(
            holdout_ids
        )
    ].copy()

    return features


def evaluate_candidates(
    features: pd.DataFrame,
    period_name: str,
) -> pd.DataFrame:
    """Evaluate every candidate strategy for a given period."""

    results = []

    for strategy_name, strategy in STRATEGIES.items():

        scored = score_transactions(
            features,
            strategy["weights"],
        )

        scored = assign_decisions(
            scored,
            strategy["review_threshold"],
            strategy["decline_threshold"],
        )

        metrics = evaluate_strategy(
            scored
        )

        metrics["period"] = period_name
        metrics["strategy"] = strategy_name

        results.append(metrics)

    return pd.DataFrame(results)


def main() -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    development, holdout = prepare_data()

    print()
    print("=" * 70)
    print("TIME-BASED TRAIN/TEST VALIDATION")
    print("=" * 70)

    print(
        f"Development transactions: {len(development):,}"
    )

    print(
        f"Development fraud: "
        f"{development['is_fraud'].sum():,}"
    )

    print(
        f"Holdout transactions: {len(holdout):,}"
    )

    print(
        f"Holdout fraud: "
        f"{holdout['is_fraud'].sum():,}"
    )

    print()
    print("Building features...")

    development_features = build_development_features(
        development
    )

    holdout_features = build_holdout_features(
        development,
        holdout,
    )

    print(
        f"Development feature rows: "
        f"{len(development_features):,}"
    )

    print(
        f"Holdout feature rows: "
        f"{len(holdout_features):,}"
    )

    print()
    print("Evaluating candidate strategies on development data...")

    development_results = evaluate_candidates(
        development_features,
        "Development",
    )

    print(
    development_results[
        [
            "strategy",
            "fraud_interception_rate",
            "fraud_block_rate",
            "missed_fraud_rate",
            "review_rate",
            "decline_rate",
            "decline_precision",
            "estimated_cost",
        ]
    ].sort_values(
        "estimated_cost"
    ).to_string(
        index=False,
        formatters={
            "fraud_interception_rate": "{:.2f}".format,
            "fraud_block_rate": "{:.2f}".format,
            "missed_fraud_rate": "{:.2f}".format,
            "review_rate": "{:.2f}".format,
            "decline_rate": "{:.2f}".format,
            "decline_precision": "{:.2f}".format,
            "estimated_cost": "{:.0f}".format,
        },
    )
)
    # ---------------------------------------------------------
    # Select strategy ONLY from development data.
    #
    # Operational constraints:
    #   - Review rate <= 10%
    #   - Decline rate <= 1%
    #
    # Only strategies satisfying both constraints are eligible.
    # The lowest-cost eligible strategy is selected.
    # ---------------------------------------------------------

    MAX_REVIEW_RATE = 10.0
    MAX_DECLINE_RATE = 1.0

    qualifying_strategies = development_results[
        (development_results["review_rate"] <= MAX_REVIEW_RATE)
        & (development_results["decline_rate"] <= MAX_DECLINE_RATE)
    ].copy()

    if qualifying_strategies.empty:
        raise ValueError(
            "No development strategy satisfies the predefined "
            "operational constraints."
        )

    qualifying_strategies = qualifying_strategies.sort_values(
        "estimated_cost"
    )

    selected_strategy = qualifying_strategies.iloc[0]["strategy"]

    print()
    print("Development strategy eligibility:")
    print()

    development_eligibility = development_results[
        [
            "strategy",
            "review_rate",
            "decline_rate",
            "estimated_cost",
        ]
    ].copy()

    development_eligibility["qualifies"] = (
        (development_eligibility["review_rate"] <= MAX_REVIEW_RATE)
        & (development_eligibility["decline_rate"] <= MAX_DECLINE_RATE)
    )

    print(
        development_eligibility.to_string(
            index=False
        )
    )

    print()
    print(
        f"Operational constraints: "
        f"review <= {MAX_REVIEW_RATE:.2f}%, "
        f"decline <= {MAX_DECLINE_RATE:.2f}%"
    )

    print(
        f"Qualifying strategies: "
        f"{len(qualifying_strategies)}"
    )

    print(
        f"Selected strategy: "
        f"{selected_strategy}"
    )

    # ---------------------------------------------------------
    # Freeze the selected strategy.
    # ---------------------------------------------------------

    strategy = STRATEGIES[
        selected_strategy
    ]

    # ---------------------------------------------------------
    # Evaluate the frozen strategy on the unseen holdout.
    # ---------------------------------------------------------

    holdout_scored = score_transactions(
        holdout_features,
        strategy["weights"],
    )

    holdout_scored = assign_decisions(
        holdout_scored,
        strategy["review_threshold"],
        strategy["decline_threshold"],
    )

    holdout_metrics = evaluate_strategy(
        holdout_scored
    )

    holdout_metrics["period"] = "Holdout"
    holdout_metrics["strategy"] = selected_strategy

    holdout_results = pd.DataFrame(
        [holdout_metrics]
    )

    print()
    print("=" * 70)
    print("SELECTED DEVELOPMENT STRATEGY")
    print("=" * 70)

    print(
        f"Strategy: {selected_strategy}"
    )

    print()
    print("HOLDOUT RESULTS")
    print("=" * 70)

    print(
        holdout_results[
            [
                "strategy",
                "fraud_interception_rate",
                "fraud_block_rate",
                "missed_fraud_rate",
                "review_rate",
                "decline_rate",
                "decline_precision",
                "estimated_cost",
            ]
        ].to_string(
            index=False
        )
    )

    # ---------------------------------------------------------
    # Development + holdout comparison
    # ---------------------------------------------------------

    selected_development = development_results[
        development_results["strategy"]
        == selected_strategy
    ].copy()

    comparison = pd.concat(
        [
            selected_development,
            holdout_results,
        ],
        ignore_index=True,
    )

    # ---------------------------------------------------------
    # Save reports
    # ---------------------------------------------------------

    development_results.to_csv(
        REPORTS_DIR
        / "train_test_development_results.csv",
        index=False,
    )

    holdout_results.to_csv(
        REPORTS_DIR
        / "train_test_holdout_results.csv",
        index=False,
    )

    comparison.to_csv(
        REPORTS_DIR
        / "train_test_strategy_comparison.csv",
        index=False,
    )

    print()
    print("Reports saved:")

    print(
        REPORTS_DIR
        / "train_test_development_results.csv"
    )

    print(
        REPORTS_DIR
        / "train_test_holdout_results.csv"
    )

    print(
        REPORTS_DIR
        / "train_test_strategy_comparison.csv"
    )


if __name__ == "__main__":
    main()
    