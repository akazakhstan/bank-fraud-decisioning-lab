"""
Fraud feature engineering.

This module transforms raw banking transactions into
behavioral features used by fraud detection strategies.
"""

from __future__ import annotations

import pandas as pd


def calculate_velocity_features(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate transaction velocity features.

    Features:
        transaction_count_2min:
            Number of transactions for the same account
            within the previous 2 minutes.

        amount_sum_2min:
            Total transaction amount for the same account
            within the previous 2 minutes.
    """

    df = transactions.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        ["account_id", "timestamp"]
    ).reset_index(drop=True)

    velocity_results = []

    for account_id, group in df.groupby(
        "account_id",
        sort=False,
    ):
        group = group.sort_values(
            "timestamp"
        ).copy()

        rolling_group = group.set_index(
            "timestamp"
        )

        rolling_group["transaction_count_2min"] = (
            rolling_group["transaction_id"]
            .rolling("2min")
            .count()
        )

        rolling_group["amount_sum_2min"] = (
            rolling_group["amount"]
            .rolling("2min")
            .sum()
        )

        velocity_results.append(
            rolling_group.reset_index()
        )

    result = pd.concat(
        velocity_results,
        ignore_index=True,
    )

    result = result.sort_values(
        ["account_id", "timestamp"]
    ).reset_index(drop=True)

    return result


def calculate_behavioral_features(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate customer behavioral features.

    Features:
        time_since_previous_transaction:
            Seconds since the customer's previous transaction.

        is_new_state:
            Indicates whether the transaction state differs
            from the customer's previous transaction state.

        customer_avg_amount:
            Historical average transaction amount for the customer.

        amount_ratio_to_customer_avg:
            Current amount divided by the customer's historical
            average transaction amount.
    """

    df = transactions.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    # Sort by customer and time
    df = df.sort_values(
        ["customer_id", "timestamp"]
    ).reset_index(drop=True)

    # -----------------------------------------------------------------------
    # Time since previous transaction
    # -----------------------------------------------------------------------

    df["previous_timestamp"] = (
        df.groupby("customer_id")["timestamp"]
        .shift(1)
    )

    df["time_since_previous_transaction"] = (
        df["timestamp"]
        - df["previous_timestamp"]
    ).dt.total_seconds()

    # -----------------------------------------------------------------------
    # Previous transaction state
    # -----------------------------------------------------------------------

    df["previous_state"] = (
        df.groupby("customer_id")["state"]
        .shift(1)
    )

    df["is_new_state"] = (
        (
            df["state"]
            != df["previous_state"]
        )
        & df["previous_state"].notna()
    ).astype(int)

        # -----------------------------------------------------------------------
    # Historical customer average transaction amount
    # -----------------------------------------------------------------------
    #
    # IMPORTANT:
    # Only transactions BEFORE the current transaction are used.
    #
    # This prevents look-ahead bias / data leakage.
    # -----------------------------------------------------------------------

    cumulative_amount = (
        df.groupby("customer_id")["amount"]
        .cumsum()
    )

    transaction_number = (
        df.groupby("customer_id")
        .cumcount()
    )

    previous_amount_sum = (
        cumulative_amount - df["amount"]
    )

    df["customer_avg_amount"] = (
        previous_amount_sum
        / transaction_number
    )

    # -----------------------------------------------------------------------
    # Handle first transaction for each customer
    # -----------------------------------------------------------------------

    df["customer_avg_amount"] = (
        df["customer_avg_amount"]
        .fillna(df["amount"])
    )

    # -----------------------------------------------------------------------
    # Transaction amount relative to historical customer average
    # -----------------------------------------------------------------------

    df["amount_ratio_to_customer_avg"] = (
        df["amount"]
        / df["customer_avg_amount"]
    )

    return df

def build_features(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Build the complete fraud feature set.

    Combines:
        - Transaction velocity
        - Customer behavioral features
    """

    velocity_features = calculate_velocity_features(transactions)

    behavioral_features = calculate_behavioral_features(transactions)

    feature_columns = [
        "transaction_id",
        "transaction_count_2min",
        "amount_sum_2min",
    ]

    velocity_features = velocity_features[feature_columns]

    result = behavioral_features.merge(
        velocity_features,
        on="transaction_id",
        how="left",
    )

    return result