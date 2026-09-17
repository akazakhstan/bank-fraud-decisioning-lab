"""
Final fraud strategy selection.

Consolidates:
    - Time-based development/holdout validation
    - Stress testing
    - Business-cost analysis

The final strategy is selected using predefined business
and operational criteria rather than maximizing a single metric.

Selection methodology:
    1. Apply operational constraints to development results.
    2. Select the lowest-cost qualifying strategy.
    3. Freeze the selected strategy.
    4. Evaluate the frozen strategy on the unseen holdout period.
    5. Summarize stress-test performance.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REPORTS_DIR = Path("reports")

# Predefined operational constraints.
MAX_REVIEW_RATE = 10.0
MAX_DECLINE_RATE = 1.0


def load_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load development, holdout, and stress-test results."""

    development_file = (
        REPORTS_DIR / "train_test_development_results.csv"
    )

    holdout_file = (
        REPORTS_DIR / "train_test_holdout_results.csv"
    )

    stress_file = (
        REPORTS_DIR / "stress_test_results.csv"
    )

    development = pd.read_csv(development_file)
    holdout = pd.read_csv(holdout_file)
    stress = pd.read_csv(stress_file)

    return development, holdout, stress


def select_strategy(
    development: pd.DataFrame,
) -> tuple[str, pd.DataFrame]:
    """
    Select the lowest-cost strategy that satisfies
    the predefined development-period constraints.
    """

    qualifying = development[
        (development["review_rate"] <= MAX_REVIEW_RATE)
        & (development["decline_rate"] <= MAX_DECLINE_RATE)
    ].copy()

    qualifying = qualifying.sort_values(
        "estimated_cost"
    )

    if qualifying.empty:
        raise ValueError(
            "No development strategy satisfies the "
            "predefined operational constraints."
        )

    selected_strategy = qualifying.iloc[0]["strategy"]

    return selected_strategy, qualifying


def evaluate_operational_constraints(
    selected: pd.Series,
) -> dict[str, float]:
    """Evaluate constraints for the selected strategy."""

    review_pass = (
        selected["review_rate"]
        <= MAX_REVIEW_RATE
    )

    decline_pass = (
        selected["decline_rate"]
        <= MAX_DECLINE_RATE
    )

    return {
        "strategy": selected["strategy"],
        "review_rate": selected["review_rate"],
        "max_review_rate": MAX_REVIEW_RATE,
        "review_constraint_pass": review_pass,
        "decline_rate": selected["decline_rate"],
        "max_decline_rate": MAX_DECLINE_RATE,
        "decline_constraint_pass": decline_pass,
        "all_operational_constraints_pass": (
            review_pass and decline_pass
        ),
    }


def summarize_stress(
    stress: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize stress-test behavior relative to baseline."""

    result = stress.copy()

    baseline = result[
        result["scenario"] == "Baseline"
    ].iloc[0]

    result["interception_change_pp"] = (
        result["fraud_interception_rate"]
        - baseline["fraud_interception_rate"]
    )

    result["missed_fraud_change_pp"] = (
        result["missed_fraud_rate"]
        - baseline["missed_fraud_rate"]
    )

    result["cost_change"] = (
        result["estimated_cost"]
        - baseline["estimated_cost"]
    )

    return result


def create_final_summary(
    selected_strategy: str,
    holdout: pd.DataFrame,
    stress: pd.DataFrame,
) -> pd.DataFrame:
    """Create the final portfolio summary."""

    selected_rows = holdout[
        holdout["strategy"] == selected_strategy
    ]

    if selected_rows.empty:
        raise ValueError(
            f"No holdout result found for selected strategy: "
            f"{selected_strategy}"
        )

    selected = selected_rows.iloc[0]

    baseline = stress[
        stress["scenario"] == "Baseline"
    ].iloc[0]

    pattern_shift = stress[
        stress["scenario"] == "Fraud Pattern Shift"
    ].iloc[0]

    velocity_shift = stress[
        stress["scenario"] == "Velocity Variation"
    ].iloc[0]

    high_prevalence = stress[
        stress["scenario"] == "High Fraud Prevalence"
    ].iloc[0]

    summary = {
        "strategy": selected_strategy,

        "holdout_interception_rate":
            selected["fraud_interception_rate"],

        "holdout_block_rate":
            selected["fraud_block_rate"],

        "holdout_missed_fraud_rate":
            selected["missed_fraud_rate"],

        "holdout_review_rate":
            selected["review_rate"],

        "holdout_decline_rate":
            selected["decline_rate"],

        "holdout_decline_precision":
            selected["decline_precision"],

        "holdout_estimated_cost":
            selected["estimated_cost"],

        "baseline_interception_rate":
            baseline["fraud_interception_rate"],

        "fraud_pattern_shift_interception":
            pattern_shift["fraud_interception_rate"],

        "velocity_variation_interception":
            velocity_shift["fraud_interception_rate"],

        "high_prevalence_interception":
            high_prevalence["fraud_interception_rate"],

        "high_prevalence_missed_fraud_rate":
            high_prevalence["missed_fraud_rate"],
    }

    return pd.DataFrame([summary])


def main() -> None:

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("5C.6 FINAL STRATEGY SELECTION")
    print("=" * 70)

    development, holdout, stress = load_results()

    print()
    print(
        f"Development strategies evaluated: "
        f"{len(development)}"
    )

    print(
        f"Holdout strategies evaluated: "
        f"{len(holdout)}"
    )

    print(
        f"Stress scenarios evaluated: "
        f"{len(stress)}"
    )

    # ---------------------------------------------------------
    # Development-period strategy selection
    # ---------------------------------------------------------

    selected_strategy, qualifying = select_strategy(
        development
    )

    print()
    print("Development strategy selection:")
    print()

    development_display = development[
        [
            "strategy",
            "fraud_interception_rate",
            "review_rate",
            "decline_rate",
            "estimated_cost",
        ]
    ].copy()

    development_display["qualifies"] = (
        (development_display["review_rate"] <= MAX_REVIEW_RATE)
        & (development_display["decline_rate"] <= MAX_DECLINE_RATE)
    )

    print(
        development_display.to_string(
            index=False
        )
    )

    print()
    print(
        f"Qualifying strategies: "
        f"{len(qualifying)}"
    )

    print(
        f"Selected strategy: "
        f"{selected_strategy}"
    )

    # ---------------------------------------------------------
    # Development constraints for selected strategy
    # ---------------------------------------------------------

    selected_development = development[
        development["strategy"] == selected_strategy
    ].iloc[0]

    development_constraints = (
        evaluate_operational_constraints(
            selected_development
        )
    )

    print()
    print("Selected strategy — development performance:")
    print()

    print(
        development[
            development["strategy"] == selected_strategy
        ][
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
    # Out-of-time holdout validation
    # ---------------------------------------------------------

    selected_holdout = holdout[
        holdout["strategy"] == selected_strategy
    ]

    print()
    print("Selected strategy — out-of-time holdout performance:")
    print()

    print(
        selected_holdout[
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
    # Holdout constraints
    # ---------------------------------------------------------

    if selected_holdout.empty:
        raise ValueError(
            "Selected strategy does not have a holdout result."
        )

    holdout_constraints = (
        evaluate_operational_constraints(
            selected_holdout.iloc[0]
        )
    )

    print()
    print("Holdout operational constraints:")
    print(
        f"Review rate: "
        f"{holdout_constraints['review_rate']:.2f}% "
        f"(limit {MAX_REVIEW_RATE:.2f}%)"
    )

    print(
        f"Decline rate: "
        f"{holdout_constraints['decline_rate']:.2f}% "
        f"(limit {MAX_DECLINE_RATE:.2f}%)"
    )

    print(
        f"Constraints satisfied: "
        f"{holdout_constraints['all_operational_constraints_pass']}"
    )

    # ---------------------------------------------------------
    # Stress testing
    # ---------------------------------------------------------

    stress_summary = summarize_stress(stress)

    print()
    print("Synthetic stress-test performance:")
    print()

    print(
        stress_summary[
            [
                "scenario",
                "fraud_interception_rate",
                "missed_fraud_rate",
                "review_rate",
                "decline_rate",
                "estimated_cost",
                "interception_change_pp",
            ]
        ].to_string(
            index=False,
            formatters={
                "fraud_interception_rate": "{:.2f}".format,
                "missed_fraud_rate": "{:.2f}".format,
                "review_rate": "{:.2f}".format,
                "decline_rate": "{:.2f}".format,
                "estimated_cost": "{:.0f}".format,
                "interception_change_pp": "{:.2f}".format,
            },
        )
    )
    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    final_summary = create_final_summary(
        selected_strategy,
        holdout,
        stress,
    )

    print()
    print("=" * 70)
    print("FINAL STRATEGY")
    print("=" * 70)

    print(
        f"Strategy: {selected_strategy}"
    )

    print(
        "Status: Selected using development-period "
        "constraints and cost"
    )

    print()
    print("Selection basis:")

    print(
        "1. Operational constraints were defined before "
        "final strategy selection."
    )

    print(
        "2. Strategies were evaluated using development-period "
        "performance."
    )

    print(
        "3. Only strategies meeting both review and decline "
        "constraints were eligible."
    )

    print(
        "4. The lowest estimated-cost qualifying strategy "
        "was selected."
    )

    print(
        "5. The selected strategy was evaluated on an unseen "
        "May-June holdout."
    )

    print(
        "6. The selected strategy was tested under multiple "
"synthetic fraud-environment stress scenarios."
    )

    # ---------------------------------------------------------
    # Save outputs
    # ---------------------------------------------------------

    final_summary_file = (
        REPORTS_DIR
        / "final_strategy_summary.csv"
    )

    stress_summary_file = (
        REPORTS_DIR
        / "final_strategy_stress_summary.csv"
    )

    constraints_file = (
        REPORTS_DIR
        / "final_strategy_constraints.csv"
    )

    final_summary.to_csv(
        final_summary_file,
        index=False,
    )

    stress_summary.to_csv(
        stress_summary_file,
        index=False,
    )

    pd.DataFrame(
        [
            {
                "selection_period": "Development",
                "selected_strategy": selected_strategy,
                "review_rate": selected_development["review_rate"],
                "max_review_rate": MAX_REVIEW_RATE,
                "review_constraint_pass":
                    development_constraints[
                        "review_constraint_pass"
                    ],
                "decline_rate":
                    selected_development["decline_rate"],
                "max_decline_rate": MAX_DECLINE_RATE,
                "decline_constraint_pass":
                    development_constraints[
                        "decline_constraint_pass"
                    ],
                "all_development_constraints_pass":
                    development_constraints[
                        "all_operational_constraints_pass"
                    ],
                "holdout_review_rate":
                    holdout_constraints["review_rate"],
                "holdout_decline_rate":
                    holdout_constraints["decline_rate"],
                "all_holdout_constraints_pass":
                    holdout_constraints[
                        "all_operational_constraints_pass"
                    ],
            }
        ]
    ).to_csv(
        constraints_file,
        index=False,
    )

    print()
    print("Reports saved:")
    print(final_summary_file)
    print(stress_summary_file)
    print(constraints_file)


if __name__ == "__main__":
    main()