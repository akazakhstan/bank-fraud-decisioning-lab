"""
Synthetic banking transaction data generator.

This module creates realistic-looking synthetic data for the
Bank Fraud Decisioning & Analytics Lab.

No real customer or financial data is used.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RANDOM_SEED = 42

NUM_CUSTOMERS = 5_000
NUM_TRANSACTIONS = 50_000

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Customer generation
# ---------------------------------------------------------------------------

def generate_customers() -> pd.DataFrame:
    """Generate synthetic customer data."""

    rng = np.random.default_rng(RANDOM_SEED)

    customer_ids = [
        f"CUST{number:06d}"
        for number in range(1, NUM_CUSTOMERS + 1)
    ]

    ages = rng.integers(
        low=18,
        high=80,
        size=NUM_CUSTOMERS,
    )

    customer_states = rng.choice(
        [
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
        ],
        size=NUM_CUSTOMERS,
    )

    customer_tenure_months = rng.integers(
        low=1,
        high=181,
        size=NUM_CUSTOMERS,
    )

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "age": ages,
            "state": customer_states,
            "customer_tenure_months": customer_tenure_months,
        }
    )

    return customers


# ---------------------------------------------------------------------------
# Account generation
# ---------------------------------------------------------------------------

def generate_accounts(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate synthetic bank accounts linked to customers."""

    rng = np.random.default_rng(RANDOM_SEED + 1)

    num_accounts = int(len(customers) * 1.5)

    account_ids = [
        f"ACC{number:07d}"
        for number in range(1, num_accounts + 1)
    ]

    customer_ids = rng.choice(
        customers["customer_id"],
        size=num_accounts,
        replace=True,
    )

    account_types = rng.choice(
        [
            "checking",
            "savings",
            "credit_card",
        ],
        size=num_accounts,
        p=[0.55, 0.30, 0.15],
    )

    balances = np.round(
        rng.lognormal(
            mean=8.0,
            sigma=1.0,
            size=num_accounts,
        ),
        2,
    )

    accounts = pd.DataFrame(
        {
            "account_id": account_ids,
            "customer_id": customer_ids,
            "account_type": account_types,
            "balance": balances,
        }
    )

    return accounts


# ---------------------------------------------------------------------------
# Transaction generation
# ---------------------------------------------------------------------------

def generate_transactions(
    customers: pd.DataFrame,
    accounts: pd.DataFrame,
) -> pd.DataFrame:
    """Generate synthetic banking transaction data with fraud scenarios."""

    rng = np.random.default_rng(RANDOM_SEED + 2)

    num_transactions = NUM_TRANSACTIONS

    # -----------------------------------------------------------------------
    # Assign transactions to accounts
    # -----------------------------------------------------------------------

    account_ids = rng.choice(
        accounts["account_id"],
        size=num_transactions,
        replace=True,
    )

    # Map accounts to customers
    account_to_customer = (
        accounts.set_index("account_id")["customer_id"]
    )

    customer_ids = account_to_customer.loc[
        account_ids
    ].to_numpy()

    # -----------------------------------------------------------------------
    # Generate transaction timestamps
    # -----------------------------------------------------------------------

    start_date = pd.Timestamp("2026-01-01")
    end_date = pd.Timestamp("2026-06-30")

    timestamps = pd.to_datetime(
    rng.integers(
        start_date.value // 10**9,
        end_date.value // 10**9,
        size=num_transactions,
    ),
    unit="s",
).to_numpy(copy=True)

    # -----------------------------------------------------------------------
    # Transaction amounts
    # -----------------------------------------------------------------------

    amounts = np.round(
        rng.lognormal(
            mean=3.5,
            sigma=1.0,
            size=num_transactions,
        ),
        2,
    )

    # -----------------------------------------------------------------------
    # Merchant categories
    # -----------------------------------------------------------------------

    merchant_categories = rng.choice(
        [
            "grocery",
            "restaurant",
            "gas_station",
            "online_retail",
            "travel",
            "electronics",
            "healthcare",
            "entertainment",
            "utilities",
        ],
        size=num_transactions,
    )

    # -----------------------------------------------------------------------
    # Transaction channels
    # -----------------------------------------------------------------------

    channels = rng.choice(
        [
            "card",
            "online",
            "mobile",
            "wire",
            "ach",
        ],
        size=num_transactions,
        p=[0.35, 0.25, 0.20, 0.10, 0.10],
    )

    # -----------------------------------------------------------------------
    # Transaction states
    # -----------------------------------------------------------------------

    states = rng.choice(
        [
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
        ],
        size=num_transactions,
    )

    # -----------------------------------------------------------------------
    # Device IDs
    # -----------------------------------------------------------------------

    device_ids = [
        f"DEV{number:06d}"
        for number in rng.integers(
            1,
            8001,
            size=num_transactions,
        )
    ]

    # -----------------------------------------------------------------------
    # Fraud indicators
    # -----------------------------------------------------------------------

    is_new_device = np.zeros(
        num_transactions,
        dtype=int,
    )

    is_fraud = np.zeros(
        num_transactions,
        dtype=int,
    )

    fraud_type = np.full(
        num_transactions,
        "none",
        dtype=object,
    )

    # -----------------------------------------------------------------------
    # Account Takeover (ATO)
    # -----------------------------------------------------------------------

    ato_count = 500

    ato_indices = rng.choice(
        num_transactions,
        size=ato_count,
        replace=False,
    )

    is_fraud[ato_indices] = 1
    fraud_type[ato_indices] = "account_takeover"

    is_new_device[ato_indices] = 1

    amounts[ato_indices] = np.round(
        rng.uniform(
            500,
            5000,
            size=ato_count,
        ),
        2,
    )

    channels[ato_indices] = rng.choice(
        [
            "online",
            "mobile",
        ],
        size=ato_count,
    )

    states[ato_indices] = rng.choice(
        [
            "CA",
            "TX",
            "NY",
            "FL",
            "AZ",
        ],
        size=ato_count,
    )

    ato_device_numbers = rng.integers(
        9000,
        9999,
        size=ato_count,
    )

    for position, index in enumerate(ato_indices):
        device_ids[index] = (
            f"DEV{ato_device_numbers[position]:06d}"
        )

    # -----------------------------------------------------------------------
    # Velocity Fraud
    # -----------------------------------------------------------------------
    #
    # Create groups of transactions occurring within a few minutes.
    #
    # Each group represents suspicious transaction velocity from
    # the same account.
    # -----------------------------------------------------------------------

    velocity_count = 300
    velocity_group_size = 5

    velocity_groups = velocity_count // velocity_group_size

    velocity_indices = []

    available_indices = np.setdiff1d(
        np.arange(num_transactions),
        ato_indices,
    )

    selected_indices = rng.choice(
        available_indices,
        size=velocity_count,
        replace=False,
    )

    # Process each velocity group
    for group_number in range(velocity_groups):

        group_start = group_number * velocity_group_size
        group_end = group_start + velocity_group_size

        group_indices = selected_indices[
            group_start:group_end
        ]

        velocity_indices.extend(group_indices)

        # Use the same account for the entire group
        velocity_account = rng.choice(
            accounts["account_id"]
        )

        account_ids[group_indices] = velocity_account

        # Get the corresponding customer
        velocity_customer = account_to_customer.loc[
            velocity_account
        ]

        customer_ids[group_indices] = velocity_customer

        # Create a short transaction window
        base_time = pd.Timestamp(
            "2026-01-01"
        ) + pd.Timedelta(
            minutes=int(
                rng.integers(
                    0,
                    250000,
                )
            )
        )

        group_times = [
            base_time
            + pd.Timedelta(
                seconds=int(
                    rng.integers(
                        5,
                        120,
                    )
                )
            )
            for _ in group_indices
        ]

        timestamps[group_indices] = group_times

        # Mark fraud
        is_fraud[group_indices] = 1
        fraud_type[group_indices] = "velocity_fraud"

        # Suspicious amounts
        amounts[group_indices] = np.round(
            rng.uniform(
                200,
                1500,
                size=velocity_group_size,
            ),
            2,
        )

        # Digital channel
        channels[group_indices] = rng.choice(
            [
                "online",
                "mobile",
            ],
            size=velocity_group_size,
        )

    # -----------------------------------------------------------------------
    # Build transaction DataFrame
    # -----------------------------------------------------------------------

    transactions = pd.DataFrame(
        {
            "transaction_id": [
                f"TXN{number:08d}"
                for number in range(1, num_transactions + 1)
            ],
            "account_id": account_ids,
            "customer_id": customer_ids,
            "timestamp": timestamps,
            "amount": amounts,
            "merchant_category": merchant_categories,
            "channel": channels,
            "state": states,
            "device_id": device_ids,
            "is_new_device": is_new_device,
            "is_fraud": is_fraud,
            "fraud_type": fraud_type,
        }
    )

    return transactions
# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    customers = generate_customers()

    accounts = generate_accounts(
        customers
    )

    transactions = generate_transactions(
        customers,
        accounts,
    )

    # Make sure data directory exists
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Output files
    customer_file = DATA_DIR / "customers.csv"
    account_file = DATA_DIR / "accounts.csv"
    transaction_file = DATA_DIR / "transactions.csv"

    # Save datasets
    customers.to_csv(
        customer_file,
        index=False,
    )

    accounts.to_csv(
        account_file,
        index=False,
    )

    transactions.to_csv(
        transaction_file,
        index=False,
    )

    # -----------------------------------------------------------------------
    # Console output
    # -----------------------------------------------------------------------

    print("Synthetic banking dataset created.")
    print()

    print(f"Number of customers: {len(customers):,}")
    print(f"Number of accounts: {len(accounts):,}")
    print(f"Number of transactions: {len(transactions):,}")
    print()

    print("Fraud distribution:")
    print(transactions["fraud_type"].value_counts())
    print()

    print("Transaction sample:")
    print(transactions.head())