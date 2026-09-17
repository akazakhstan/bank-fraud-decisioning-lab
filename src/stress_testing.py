"""
Fraud decisioning stress testing.

Tests the frozen Balanced Higher Capture strategy under
different synthetic fraud-environment conditions.

The strategy is NOT re-optimized during stress testing.
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


# Frozen strategy selected during 5C.4
WEIGHTS = {
    "rule_velocity": 20,
    "rule_new_device": 35,
    "rule_amount_anomaly": 30,
    "rule_new_state": 15,
}

REVIEW_THRESHOLD = 20
DECLINE_THRESHOLD = 50


MISSED_FRAUD_COST = 500
MANUAL_REVIEW_COST = 5
FALSE_DECLINE_COST = 25


def score_transactions(
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Apply the frozen Balanced Higher Capture score."""

    df = features.copy()

    df["risk_score"] = (
        df["rule_velocity"] * WEIGHTS["rule_velocity"]
        + df["rule_new_device"] * WEIGHTS["rule_new_device"]
        + df["rule_amount_anomaly"] * WEIGHTS["rule_amount_anomaly"]
        + df["rule_new_state"] * WEIGHTS["rule_new_state"]
    )

    return df


def assign_decisions(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """Apply the frozen decision thresholds."""

    df = scored.copy()

    df["decision"] = "APPROVE"

    df.loc[
        df["risk_score"] >= REVIEW_THRESHOLD,
        "decision",
    ] = "REVIEW"

    df.loc[
        df["risk_score"] >= DECLINE_THRESHOLD,
        "decision",
    ] = "DECLINE"

    return df


def evaluate_strategy(
    scored: pd.DataFrame,
    scenario_name: str,
) -> dict[str, float]:
    """Evaluate the frozen strategy."""

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
        "scenario": scenario_name,
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


def build_base_dataset() -> pd.DataFrame:
    """Generate the deterministic baseline transaction dataset."""

    customers = generate_customers()
    accounts = generate_accounts(customers)

    transactions = generate_transactions(
        customers,
        accounts,
    )

    transactions["timestamp"] = pd.to_datetime(
        transactions["timestamp"]
    )

    return transactions


def run_baseline(
    transactions: pd.DataFrame,
) -> dict[str, float]:
    """Evaluate the frozen strategy on the baseline dataset."""

    features = build_features(
        transactions
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        "Baseline",
    )


def run_fraud_prevalence_scenario(
    transactions: pd.DataFrame,
    multiplier: float,
    scenario_name: str,
) -> dict[str, float]:
    """
    Stress test fraud prevalence.

    Fraud labels are changed only for stress testing.
    Transaction behavior/features remain unchanged.
    """

    stressed = transactions.copy()

    fraud_indices = stressed.index[
        stressed["is_fraud"] == 1
    ]

    non_fraud_indices = stressed.index[
        stressed["is_fraud"] == 0
    ]

    target_fraud_count = int(
        len(fraud_indices) * multiplier
    )

    if target_fraud_count <= len(fraud_indices):

        keep_fraud = fraud_indices[:target_fraud_count]

        stressed["is_fraud"] = 0

        stressed.loc[
            keep_fraud,
            "is_fraud",
        ] = 1

    else:

        additional_needed = (
            target_fraud_count
            - len(fraud_indices)
        )

        additional = non_fraud_indices[
            :additional_needed
        ]

        stressed.loc[
            additional,
            "is_fraud",
        ] = 1

    features = build_features(
        stressed
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        scenario_name,
    )


def run_signal_degradation(
    transactions: pd.DataFrame,
) -> dict[str, float]:
    """
    Remove selected observable fraud signals.

    This scenario makes fraud behavior less distinguishable
    without changing the fraud labels.
    """

    stressed = transactions.copy()

    fraud_mask = stressed["is_fraud"] == 1

    # Make half of fraudulent transactions reuse an existing device.
    # This weakens the observable new-device signal while allowing
    # feature engineering to recalculate is_new_device naturally.

    fraud_indices = stressed.index[
        fraud_mask
    ]

    device_indices = fraud_indices[
        : len(fraud_indices) // 2
    ]

    existing_device_ids = (
        stressed.loc[
            stressed["is_fraud"] == 0,
            "device_id",
        ]
        .dropna()
        .tolist()
    )

    for i, idx in enumerate(device_indices):

        stressed.loc[
            idx,
            "device_id",
        ] = existing_device_ids[
            i % len(existing_device_ids)
        ]

    # Reduce transaction amounts for a subset of fraud.

    amount_indices = fraud_indices[
        len(fraud_indices) // 2:
    ]

    stressed.loc[
        amount_indices,
        "amount",
    ] = (
        stressed.loc[
            amount_indices,
            "amount",
        ]
        * 0.60
    )

    features = build_features(
        stressed
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        "Signal Degradation",
    )


def run_behavioral_drift(
    transactions: pd.DataFrame,
) -> dict[str, float]:
    """
    Increase legitimate customer behavior variation.

    Some legitimate transactions are assigned new states,
    creating additional geographic-change signals.
    """

    stressed = transactions.copy()

    legitimate_indices = stressed.index[
        stressed["is_fraud"] == 0
    ]

    drift_indices = legitimate_indices[
        : int(len(legitimate_indices) * 0.10)
    ]

    states = [
        "NC",
        "SC",
        "VA",
        "GA",
        "FL",
        "TX",
        "NY",
        "CA",
        "IL",
        "AZ",
    ]

    for i, idx in enumerate(drift_indices):
        current_state = stressed.loc[
            idx,
            "state",
        ]

        alternative_states = [
            state
            for state in states
            if state != current_state
        ]

        stressed.loc[
            idx,
            "state",
        ] = alternative_states[
            i % len(alternative_states)
        ]

    features = build_features(
        stressed
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        "Behavioral Drift",
    )


def run_velocity_variation(
    transactions: pd.DataFrame,
) -> dict[str, float]:
    """
    Reduce the concentration of fraudulent transactions
    by spreading selected fraud timestamps apart.
    """

    stressed = transactions.copy()

    fraud_indices = stressed.index[
        stressed["is_fraud"] == 1
    ]

    selected = fraud_indices[
        : len(fraud_indices) // 2
    ]

    for i, idx in enumerate(selected):

        stressed.loc[
            idx,
            "timestamp",
        ] = (
            stressed.loc[
                idx,
                "timestamp",
            ]
            + pd.Timedelta(
                minutes=(i % 10) + 1
            )
        )

    stressed = stressed.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    features = build_features(
        stressed
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        "Velocity Variation",
    )
def run_fraud_pattern_shift(
    transactions: pd.DataFrame,
) -> dict[str, float]:
    """
    Simulate a fraud pattern shift in which fraudulent
    transactions become less distinguishable from normal
    customer behavior.

    The fraud labels remain unchanged.

    Observable fraud signals are weakened through:
        - Device reuse
        - Lower transaction amounts
        - Reduced velocity concentration
        - Less anomalous geographic behavior
    """

    stressed = transactions.copy()

    fraud_indices = stressed.index[
        stressed["is_fraud"] == 1
    ]

    # ---------------------------------------------------------
    # 1. Device reuse
    # ---------------------------------------------------------
    # Half of fraudulent transactions reuse devices observed
    # among legitimate customers.

    device_indices = fraud_indices[
        : len(fraud_indices) // 2
    ]

    existing_device_ids = (
        stressed.loc[
            stressed["is_fraud"] == 0,
            "device_id",
        ]
        .dropna()
        .tolist()
    )

    for i, idx in enumerate(device_indices):

        stressed.loc[
            idx,
            "device_id",
        ] = existing_device_ids[
            i % len(existing_device_ids)
        ]

    # ---------------------------------------------------------
    # 2. Amount anomaly reduction
    # ---------------------------------------------------------
    # Reduce transaction amounts for another subset of fraud
    # so that transactions are closer to normal behavior.

    amount_indices = fraud_indices[
        len(fraud_indices) // 4:
        len(fraud_indices) // 2
    ]

    stressed.loc[
        amount_indices,
        "amount",
    ] = (
        stressed.loc[
            amount_indices,
            "amount",
        ]
        * 0.50
    )

    # ---------------------------------------------------------
    # 3. Velocity weakening
    # ---------------------------------------------------------
    # Spread selected fraudulent transactions apart in time.

    velocity_indices = fraud_indices[
        len(fraud_indices) // 2:
        3 * len(fraud_indices) // 4
    ]

    for i, idx in enumerate(velocity_indices):

        stressed.loc[
            idx,
            "timestamp",
        ] = (
            stressed.loc[
                idx,
                "timestamp",
            ]
            + pd.Timedelta(
                minutes=(i % 15) + 2
            )
        )

    # ---------------------------------------------------------
    # 4. Geographic signal reduction
    # ---------------------------------------------------------
    # Replace the state for a subset of fraudulent transactions
    # with a legitimate customer's state.

    geographic_indices = fraud_indices[
        3 * len(fraud_indices) // 4:
    ]

    legitimate_states = (
        stressed.loc[
            stressed["is_fraud"] == 0,
            "state",
        ]
        .dropna()
        .tolist()
    )

    for i, idx in enumerate(geographic_indices):

        stressed.loc[
            idx,
            "state",
        ] = legitimate_states[
            i % len(legitimate_states)
        ]

    # ---------------------------------------------------------
    # Rebuild the complete feature pipeline
    # ---------------------------------------------------------

    stressed = stressed.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    features = build_features(
        stressed
    )

    features = apply_fraud_rules(
        features
    )

    scored = score_transactions(
        features
    )

    scored = assign_decisions(
        scored
    )

    return evaluate_strategy(
        scored,
        "Fraud Pattern Shift",
    )

def main() -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("5C.5 STRESS TESTING")
    print("=" * 70)

    print()
    print("Generating baseline dataset...")

    transactions = build_base_dataset()

    print(
        f"Transactions: {len(transactions):,}"
    )

    print(
        f"Fraud: "
        f"{transactions['is_fraud'].sum():,}"
    )

    results = []

    print()
    print("Running baseline scenario...")

    results.append(
        run_baseline(
            transactions
        )
    )

    print("Running fraud prevalence scenarios...")

    results.append(
        run_fraud_prevalence_scenario(
            transactions,
            0.50,
            "Low Fraud Prevalence",
        )
    )

    results.append(
        run_fraud_prevalence_scenario(
            transactions,
            1.50,
            "High Fraud Prevalence",
        )
    )

    print("Running signal degradation...")

    results.append(
        run_signal_degradation(
            transactions
        )
    )

    print("Running behavioral drift...")

    results.append(
        run_behavioral_drift(
            transactions
        )
    )
    print("Running fraud pattern shift...")

    results.append(
    run_fraud_pattern_shift(
        transactions
       )
    )

    print("Running velocity variation...")

    results.append(
    run_velocity_variation(
        transactions
       )
    )

    results_df = pd.DataFrame(
    results
    )

    print()
    print("=" * 70)
    print("STRESS TEST RESULTS")
    print("=" * 70)

    print(
        results_df[
            [
                "scenario",
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

    output_file = (
        REPORTS_DIR
        / "stress_test_results.csv"
    )

    results_df.to_csv(
        output_file,
        index=False,
    )

    print()
    print(
        f"Results saved to: {output_file}"
    )


if __name__ == "__main__":
    main()