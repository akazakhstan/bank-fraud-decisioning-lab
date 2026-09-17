"""
5C.3B - Cost Sensitivity Analysis

Tests fraud decisioning strategies under different business
cost assumptions.

The analysis varies:
    - Risk-score weights
    - Review threshold
    - Decline threshold
    - Missed-fraud cost
    - Manual-review cost
    - False-decline cost

Important:
Cost assumptions are illustrative and are used only for
sensitivity analysis on the synthetic dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from data_generation import (
    generate_accounts,
    generate_customers,
    generate_transactions,
)

from feature_engineering import build_features

from rules_engine import apply_fraud_rules


# ---------------------------------------------------------------------
# Output location
# ---------------------------------------------------------------------

REPORTS_DIR = Path("reports")


# ---------------------------------------------------------------------
# Cost assumptions
# ---------------------------------------------------------------------

MISSED_FRAUD_COSTS = [100, 250, 500, 750, 1000]

REVIEW_COSTS = [2, 5, 10, 20]

FALSE_DECLINE_COSTS = [10, 25, 50, 100]


# ---------------------------------------------------------------------
# Candidate strategies
# ---------------------------------------------------------------------

STRATEGIES = {
    "Baseline": {
        "velocity": 40,
        "new_device": 35,
        "amount_anomaly": 15,
        "new_state": 10,
        "review_threshold": 20,
        "decline_threshold": 60,
    },

    "Amount Emphasis": {
        "velocity": 35,
        "new_device": 35,
        "amount_anomaly": 20,
        "new_state": 10,
        "review_threshold": 20,
        "decline_threshold": 60,
    },

    "Balanced Higher Capture": {
        "velocity": 20,
        "new_device": 35,
        "amount_anomaly": 30,
        "new_state": 15,
        "review_threshold": 20,
        "decline_threshold": 50,
    },

    "Balanced Conservative": {
        "velocity": 30,
        "new_device": 45,
        "amount_anomaly": 15,
        "new_state": 10,
        "review_threshold": 30,
        "decline_threshold": 60,
    },

    "High Capture": {
        "velocity": 20,
        "new_device": 30,
        "amount_anomaly": 30,
        "new_state": 20,
        "review_threshold": 10,
        "decline_threshold": 55,
    },
}


# ---------------------------------------------------------------------
# Strategy outcome
# ---------------------------------------------------------------------

@dataclass
class StrategyOutcome:
    strategy: str
    total_transactions: int
    fraud_transactions: int
    fraud_capture: float
    missed_fraud: int
    manual_reviews: int
    false_declines: int
    precision: float
    review_rate: float
    decline_rate: float


# ---------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------

def prepare_data() -> pd.DataFrame:
    """Generate the synthetic dataset and apply fraud rules."""

    print("Generating synthetic data...")

    customers = generate_customers()

    accounts = generate_accounts(
        customers
    )

    transactions = generate_transactions(
    customers,
    accounts,
    )

    print(f"Customers:     {len(customers):,}")
    print(f"Accounts:      {len(accounts):,}")
    print(f"Transactions:  {len(transactions):,}")

    print("\nBuilding features...")

    features = build_features(
    transactions,
    )
    
    print(
        f"Feature dataset: {features.shape}"
    )

    print("\nApplying fraud rules...")

    ruled = apply_fraud_rules(
        features
    )

    return ruled


# ---------------------------------------------------------------------
# Risk score calculation
# ---------------------------------------------------------------------

def calculate_custom_risk_score(
    df: pd.DataFrame,
    velocity_weight: int,
    new_device_weight: int,
    amount_anomaly_weight: int,
    new_state_weight: int,
) -> pd.DataFrame:
    """
    Calculate risk score using strategy-specific weights.

    The fraud label is NOT used to calculate the score.
    """

    scored = df.copy()

    scored["risk_score"] = (
        scored["rule_velocity"] * velocity_weight
        + scored["rule_new_device"] * new_device_weight
        + scored["rule_amount_anomaly"] * amount_anomaly_weight
        + scored["rule_new_state"] * new_state_weight
    )

    return scored


# ---------------------------------------------------------------------
# Decision assignment
# ---------------------------------------------------------------------

def assign_custom_decision(
    df: pd.DataFrame,
    review_threshold: int,
    decline_threshold: int,
) -> pd.DataFrame:
    """
    Assign APPROVE, REVIEW, or DECLINE using
    strategy-specific thresholds.
    """

    result = df.copy()

    result["decision"] = "APPROVE"

    result.loc[
        result["risk_score"] >= review_threshold,
        "decision",
    ] = "REVIEW"

    result.loc[
        result["risk_score"] >= decline_threshold,
        "decision",
    ] = "DECLINE"

    return result


# ---------------------------------------------------------------------
# Strategy evaluation
# ---------------------------------------------------------------------

def evaluate_strategy(
    df: pd.DataFrame,
    strategy_name: str,
    strategy: dict,
) -> StrategyOutcome:
    """Evaluate one candidate strategy."""

    scored = calculate_custom_risk_score(
        df,
        velocity_weight=strategy["velocity"],
        new_device_weight=strategy["new_device"],
        amount_anomaly_weight=strategy["amount_anomaly"],
        new_state_weight=strategy["new_state"],
    )

    evaluated = assign_custom_decision(
        scored,
        review_threshold=strategy["review_threshold"],
        decline_threshold=strategy["decline_threshold"],
    )

    total_transactions = len(evaluated)

    fraud_mask = (
        evaluated["is_fraud"] == 1
    )

    nonfraud_mask = (
        evaluated["is_fraud"] == 0
    )

    fraud_transactions = int(
        fraud_mask.sum()
    )

    approve_mask = (
        evaluated["decision"] == "APPROVE"
    )

    review_mask = (
        evaluated["decision"] == "REVIEW"
    )

    decline_mask = (
        evaluated["decision"] == "DECLINE"
    )

    # Fraud approved = missed fraud
    missed_fraud = int(
        (
            approve_mask
            & fraud_mask
        ).sum()
    )

    # Manual review volume
    manual_reviews = int(
        review_mask.sum()
    )

    # Legitimate transactions incorrectly declined
    false_declines = int(
        (
            decline_mask
            & nonfraud_mask
        ).sum()
    )

    captured_fraud = (
        fraud_transactions
        - missed_fraud
    )

    fraud_capture = (
        captured_fraud / fraud_transactions
        if fraud_transactions > 0
        else 0.0
    )

    total_declines = int(
        decline_mask.sum()
    )

    true_declines = int(
        (
            decline_mask
            & fraud_mask
        ).sum()
    )

    precision = (
        true_declines / total_declines
        if total_declines > 0
        else 0.0
    )

    review_rate = (
        manual_reviews
        / total_transactions
    )

    decline_rate = (
        total_declines
        / total_transactions
    )

    return StrategyOutcome(
        strategy=strategy_name,
        total_transactions=total_transactions,
        fraud_transactions=fraud_transactions,
        fraud_capture=fraud_capture,
        missed_fraud=missed_fraud,
        manual_reviews=manual_reviews,
        false_declines=false_declines,
        precision=precision,
        review_rate=review_rate,
        decline_rate=decline_rate,
    )


# ---------------------------------------------------------------------
# Cost calculation
# ---------------------------------------------------------------------

def calculate_cost(
    outcome: StrategyOutcome,
    missed_fraud_cost: float,
    review_cost: float,
    false_decline_cost: float,
) -> float:
    """Calculate estimated total business cost."""

    return (
        outcome.missed_fraud
        * missed_fraud_cost
        + outcome.manual_reviews
        * review_cost
        + outcome.false_declines
        * false_decline_cost
    )


# ---------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------

def run_sensitivity(
    outcomes: list[StrategyOutcome],
) -> pd.DataFrame:
    """Evaluate all cost combinations."""

    rows = []

    for missed_cost in MISSED_FRAUD_COSTS:

        for review_cost in REVIEW_COSTS:

            for false_decline_cost in FALSE_DECLINE_COSTS:

                for outcome in outcomes:

                    total_cost = calculate_cost(
                        outcome,
                        missed_cost,
                        review_cost,
                        false_decline_cost,
                    )

                    rows.append(
                        {
                            "missed_fraud_cost": missed_cost,
                            "review_cost": review_cost,
                            "false_decline_cost": false_decline_cost,
                            "strategy": outcome.strategy,
                            "total_cost": total_cost,
                        }
                    )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Winner analysis
# ---------------------------------------------------------------------

def identify_winners(
    sensitivity: pd.DataFrame,
) -> pd.DataFrame:
    """Identify the lowest-cost strategy for every scenario."""

    scenario_columns = [
        "missed_fraud_cost",
        "review_cost",
        "false_decline_cost",
    ]

    winners = (
        sensitivity
        .sort_values("total_cost")
        .groupby(
            scenario_columns,
            as_index=False,
        )
        .first()
    )

    return winners


def summarize_winner_frequency(
    winners: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate how frequently each strategy wins."""

    summary = (
        winners["strategy"]
        .value_counts()
        .rename_axis("strategy")
        .reset_index(
            name="wins"
        )
    )

    summary["win_rate"] = (
        summary["wins"]
        / len(winners)
    )

    return summary


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:

    # Ensure the output directory exists before anything gets written to it.
    # (This is the one line that was missing before - without it, the run
    # would complete the entire analysis and then crash on the final
    # to_csv calls with "Cannot save file into a non-existent directory".)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("5C.3B COST SENSITIVITY ANALYSIS")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Prepare data
    # ---------------------------------------------------------------

    df = prepare_data()

    # ---------------------------------------------------------------
    # Evaluate candidate strategies
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("STRATEGY OUTCOMES")
    print("=" * 70)

    outcomes = []

    for strategy_name, strategy in STRATEGIES.items():

        outcome = evaluate_strategy(
            df,
            strategy_name,
            strategy,
        )

        outcomes.append(
            outcome
        )

        print(
            f"\n{strategy_name}"
        )

        print(
            f"  Fraud capture : "
            f"{outcome.fraud_capture:.2%}"
        )

        print(
            f"  Precision     : "
            f"{outcome.precision:.2%}"
        )

        print(
            f"  Review rate   : "
            f"{outcome.review_rate:.2%}"
        )

        print(
            f"  Decline rate  : "
            f"{outcome.decline_rate:.2%}"
        )

        print(
            f"  Missed fraud  : "
            f"{outcome.missed_fraud:,}"
        )

        print(
            f"  Reviews       : "
            f"{outcome.manual_reviews:,}"
        )

        print(
            f"  False declines: "
            f"{outcome.false_declines:,}"
        )

    # ---------------------------------------------------------------
    # Run sensitivity
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("RUNNING COST SENSITIVITY")
    print("=" * 70)

    sensitivity = run_sensitivity(
        outcomes
    )

    print(
        f"\nCost scenarios evaluated: "
        f"{len(sensitivity):,}"
    )

    # ---------------------------------------------------------------
    # Winners
    # ---------------------------------------------------------------

    winners = identify_winners(
        sensitivity
    )

    print("\n" + "=" * 70)
    print("WINNER FREQUENCY")
    print("=" * 70)

    winner_summary = (
        summarize_winner_frequency(
            winners
        )
    )

    for _, row in winner_summary.iterrows():

        print(
            f"{row['strategy']:<25} "
            f"{int(row['wins']):>3} wins "
            f"({row['win_rate']:.2%})"
        )

    # ---------------------------------------------------------------
    # Cost ranges
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("COST RANGE BY STRATEGY")
    print("=" * 70)

    cost_summary = (
        sensitivity
        .groupby("strategy")[
            "total_cost"
        ]
        .agg(
            [
                "min",
                "max",
                "mean",
            ]
        )
        .sort_values("mean")
    )

    for strategy_name, row in (
        cost_summary.iterrows()
    ):

        print(
            f"{strategy_name:<25} "
            f"Min: ${row['min']:>10,.0f} | "
            f"Mean: ${row['mean']:>10,.0f} | "
            f"Max: ${row['max']:>10,.0f}"
        )

    # ---------------------------------------------------------------
    # Baseline cost scenario
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("BASELINE COST ASSUMPTION COMPARISON")
    print("=" * 70)

    baseline = sensitivity[
        (sensitivity["missed_fraud_cost"] == 500)
        & (sensitivity["review_cost"] == 5)
        & (sensitivity["false_decline_cost"] == 25)
    ].sort_values(
        "total_cost"
    )

    print("\nAssumptions:")
    print("  Missed fraud   = $500")
    print("  Manual review  = $5")
    print("  False decline  = $25")

    print()

    for _, row in baseline.iterrows():

        print(
            f"{row['strategy']:<25} "
            f"${row['total_cost']:>10,.0f}"
        )

    # ---------------------------------------------------------------
    # Final conclusion
    # ---------------------------------------------------------------

    best_strategy = (
        winner_summary.iloc[0]["strategy"]
    )

    print("\n" + "=" * 70)
    print("SENSITIVITY CONCLUSION")
    print("=" * 70)

    print(
        f"\nMost frequent lowest-cost strategy: "
        f"{best_strategy}"
    )

    print(
        "\nThis is a sensitivity analysis on "
        "the synthetic dataset."
    )

    print(
        "The cost assumptions are illustrative "
        "and should not be presented as actual "
        "production fraud-loss estimates."
    )

    # ---------------------------------------------------------------
    # Save results
    # ---------------------------------------------------------------

    sensitivity.to_csv(
        REPORTS_DIR / "cost_sensitivity_results.csv",
        index=False,
    )

    winners.to_csv(
        REPORTS_DIR / "cost_sensitivity_winners.csv",
        index=False,
    )

    winner_summary.to_csv(
        REPORTS_DIR / "cost_sensitivity_winner_summary.csv",
        index=False,
    )

    print("\nResults saved to:")

    print(
        "  reports/cost_sensitivity_results.csv"
    )

    print(
        "  reports/cost_sensitivity_winners.csv"
    )

    print(
        "  reports/cost_sensitivity_winner_summary.csv"
    )


if __name__ == "__main__":
    main()