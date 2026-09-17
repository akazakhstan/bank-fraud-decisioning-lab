# Limitations and Next Steps



## 1. Purpose



This project is designed to demonstrate fraud analytics, decisioning strategy development, validation, and stress testing using synthetic banking transaction data.



The results demonstrate an analytical methodology rather than production fraud performance.



---



## 2. Data Limitations



The project uses synthetic transaction data.



Consequently:



- transaction behavior is simulated

- fraud labels are synthetically generated

- customer behavior does not represent actual bank customers

- transaction distributions may not reflect real financial institutions

- fraud prevalence is controlled by the data-generation process



The observed performance metrics should therefore not be interpreted as expected production performance.



---



## 3. Fraud Scenario Limitations



The synthetic dataset includes account takeover, velocity fraud, and geographic anomaly scenarios.



These scenarios are intentionally simplified.



Real-world fraud can involve:



- coordinated fraud rings

- mule accounts

- social engineering

- credential compromise

- device compromise

- synthetic identities

- merchant abuse

- payment-account takeover

- first-party fraud

- organized fraud campaigns



The current project does not attempt to model the full fraud ecosystem.



---



## 4. Feature Limitations



The current strategy uses four principal signals:



- transaction velocity

- new device

- amount anomaly

- new geographic state



These provide a useful foundation but do not represent the complete feature set available to a production fraud system.



Potential future features include:



### Customer Behavior



- historical transaction frequency

- merchant-category behavior

- typical transaction amount

- time-of-day behavior

- day-of-week behavior

- account balance behavior



### Device Intelligence



- device reputation

- device age

- device-sharing patterns

- device-to-account relationships

- emulator or automation indicators



### Geographic Intelligence



- distance from previous transaction

- travel-time feasibility

- IP geolocation

- device location

- known customer locations



### Network Features



- shared devices

- shared payment instruments

- shared addresses

- shared identifiers

- account-to-account relationships



---



## 5. Geographic Modeling Limitation



The current new-state signal identifies whether a state has previously been observed for the customer.



This is not equivalent to a production impossible-travel model.



A production implementation would consider:



- previous transaction location

- current transaction location

- elapsed time

- geographic distance

- plausible travel speed

- IP/device location

- customer travel patterns



Future iterations should replace the simplified state-based signal with a more realistic geographic anomaly framework.



---



## 6. Business-Cost Limitations



The strategy-selection framework uses illustrative cost assumptions:



| Cost | Assumption |

|---|---:|

| Missed fraud | $500 |

| Manual review | $5 |

| False decline | $25 |



These assumptions are used to compare strategies within the synthetic environment.



They are not based on actual bank loss data or actual analyst operating costs.



A production implementation should estimate costs using observed:



- fraud losses

- recovery rates

- analyst labor costs

- customer-service costs

- chargebacks

- reimbursement costs

- customer attrition or friction

- operational capacity



---



## 7. Model and Strategy Limitations



The current system is primarily a rule-based weighted scoring framework.



It does not currently include:



- supervised machine-learning probability models

- probability calibration

- model explainability frameworks

- online learning

- real-time model retraining

- automated champion/challenger deployment

- production model monitoring

- automated threshold optimization

- causal experimentation



The framework can nevertheless serve as a foundation for comparing rule-based strategies with statistical and machine-learning approaches.



---



## 8. Validation Limitations



The project uses a six-month synthetic time horizon.



The current validation includes:



- January–April development data

- May–June unseen holdout data

- synthetic stress scenarios



Additional validation would be useful before drawing stronger conclusions.



Potential extensions include:



- rolling-window validation

- multiple time-based holdouts

- seasonal validation

- fraud-type-specific validation

- channel-specific validation

- customer-segment validation

- threshold stability analysis



---



## 9. Stress-Test Limitations



The stress tests modify synthetic fraud conditions according to predefined scenarios.



They should therefore be interpreted as sensitivity analysis.



They do not reproduce the full complexity of real-world fraud evolution.



In particular, the high-fraud-prevalence scenario demonstrates that the selected strategy can experience materially lower interception when the underlying fraud environment changes.



This reinforces the importance of monitoring strategy performance rather than assuming that a fixed strategy will remain optimal indefinitely.



---



## 10. Production Architecture — Future State



A future production-oriented architecture could extend the current framework:



```text

Transaction

&#x20;    ↓

Real-Time Feature Generation

&#x20;    ↓

Customer / Device / Geographic Intelligence

&#x20;    ↓

Fraud Rules

&#x20;    ↓

Risk Model

&#x20;    ↓

Decision Engine

&#x20;    ↓

&#x20;┌─────────┬─────────┬─────────┐

&#x20;│ APPROVE │ REVIEW  │ DECLINE │

&#x20;└─────────┴─────────┴─────────┘

&#x20;    ↓

Case Management

&#x20;    ↓

Analyst Feedback

&#x20;    ↓

Strategy Monitoring

&#x20;    ↓

Threshold / Rule Optimization


