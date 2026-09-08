"""
Fraud risk scoring.

This module converts fraud detection signals into
an interpretable transaction risk score.
"""

from __future__ import annotations

import pandas as pd


def calculate_risk_score(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate an interpretable fraud risk score.

    Risk weights:

        Velocity       +40
        New device     +35
        Amount anomaly +15
        New state      +10

    Maximum possible score = 100.
    """

    df = scored.copy()

    df["risk_score"] = (
        df["rule_velocity"] * 40
        + df["rule_new_device"] * 35
        + df["rule_amount_anomaly"] * 15
        + df["rule_new_state"] * 10
    )

    return df


def assign_decision(
    scored: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign a fraud decision based on risk score.

    Decision bands:

        0–24   → APPROVE
        25–59  → REVIEW
        60–100 → DECLINE
    """

    df = scored.copy()

    df["decision"] = "APPROVE"

    df.loc[
        df["risk_score"] >= 25,
        "decision",
    ] = "REVIEW"

    df.loc[
        df["risk_score"] >= 60,
        "decision",
    ] = "DECLINE"

    return df