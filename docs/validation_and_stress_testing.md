# Validation and Stress Testing



## 1. Purpose



The fraud decisioning strategy was evaluated using two complementary validation approaches:



1. Time-based out-of-sample validation

2. Synthetic stress testing



Time-based validation evaluates whether the selected strategy continues to operate within predefined constraints on a later, unseen period.



Stress testing evaluates how strategy performance changes when fraud prevalence, signal quality, transaction behavior, or fraud patterns are altered.



---



## 2. Time-Based Validation



### 2.1 Data Split



The transaction dataset covers January through June 2026.



The data was divided chronologically:



| Period | Role | Transactions | Fraud |

|---|---|---:|---:|

| January–April 2026 | Development | 33,357 | 750 |

| May–June 2026 | Holdout | 16,643 | 350 |



The chronological split was selected to better reflect how a fraud strategy would be developed using historical data and subsequently evaluated on future transactions.



---



## 3. Development-Period Selection



Candidate strategies were evaluated on the January–April development period.



The predefined operational constraints were:



- Review rate ≤ 10%

- Decline rate ≤ 1%



Only strategies satisfying both constraints were eligible for final selection.



The Baseline strategy and Balanced Conservative strategy qualified.



The Baseline strategy was selected because it had the lower estimated cost among the qualifying candidates.



---



## 4. Selected Strategy on Development Data



The selected Baseline strategy produced the following development-period results:



| Metric | Result |

|---|---:|

| Fraud interception rate | 81.07% |

| Fraud block rate | 35.73% |

| Missed fraud rate | 18.93% |

| Review rate | 9.35% |

| Decline rate | 0.80% |

| Decline precision | 100% |

| Estimated cost | $86,600 |



Both operational constraints were satisfied during development.



---



## 5. Out-of-Time Holdout



After the Baseline strategy was selected, its configuration was kept unchanged and evaluated on the May–June 2026 holdout period.



The holdout period was not used for strategy selection.



### Holdout Results



| Metric | Result |

|---|---:|

| Fraud interception rate | 88.57% |

| Fraud block rate | 44.57% |

| Missed fraud rate | 11.43% |

| Review rate | 6.27% |

| Decline rate | 0.94% |

| Decline precision | 100% |

| Estimated cost | $25,215 |



### Operational Constraints



| Constraint | Holdout Result | Status |

|---|---:|---|

| Review rate ≤ 10% | 6.27% | PASS |

| Decline rate ≤ 1% | 0.94% | PASS |



The selected strategy therefore satisfied both predefined operational constraints on the unseen holdout.



---



## 6. Interpretation of Holdout Results



The holdout fraud interception rate was higher than the development-period rate:



- Development: 81.07%

- Holdout: 88.57%



This difference should not be interpreted as evidence that the strategy becomes more effective over time.



The synthetic transaction and fraud characteristics differ between the two periods. Changes in fraud composition, signal distribution, and transaction behavior can affect measured performance.



The purpose of the holdout is therefore to evaluate the frozen strategy on unseen temporal data rather than to demonstrate improvement over time.



---



# 7. Synthetic Stress Testing



## 7.1 Purpose



Stress testing was performed to examine the sensitivity of the selected strategy to changes in the synthetic fraud environment.



Seven scenarios were evaluated:



1. Baseline

2. Low Fraud Prevalence

3. High Fraud Prevalence

4. Signal Degradation

5. Behavioral Drift

6. Fraud Pattern Shift

7. Velocity Variation



Stress testing does not establish production robustness. It provides sensitivity analysis within the assumptions of the synthetic dataset.



---



## 8. Stress-Test Results



| Scenario | Fraud Interception | Missed Fraud | Review Rate | Decline Rate | Estimated Cost | Change vs. Baseline |

|---|---:|---:|---:|---:|---:|---:|

| Baseline | 87.09% | 12.91% | 9.01% | 0.96% | $93,525 | 0.00 pp |

| Low Fraud Prevalence | 89.09% | 10.91% | 9.01% | 0.96% | $58,425 | +2.00 pp |

| High Fraud Prevalence | 60.85% | 39.15% | 9.01% | 0.96% | $345,525 | -26.24 pp |

| Signal Degradation | 86.55% | 13.45% | 9.01% | 0.96% | $96,535 | -0.55 pp |

| Behavioral Drift | 87.09% | 12.91% | 9.01% | 0.96% | $93,525 | 0.00 pp |

| Fraud Pattern Shift | 83.18% | 16.82% | 8.98% | 0.93% | $114,940 | -3.91 pp |

| Velocity Variation | 84.18% | 15.82% | 8.98% | 0.93% | $109,440 | -2.91 pp |



---



## 9. Stress-Test Interpretation



### 9.1 Low Fraud Prevalence



Under the low-fraud-prevalence scenario, fraud interception increased by 2.00 percentage points relative to the stress-test baseline.



Estimated cost decreased because the synthetic environment contained less fraud-related financial exposure.



---



### 9.2 High Fraud Prevalence



The high-fraud-prevalence scenario produced the largest deterioration in fraud interception.



Fraud interception decreased from 87.09% to 60.85%, a change of:



`-26.24 percentage points`



Estimated cost increased substantially under the assumed $500 missed-fraud cost.



This illustrates that a fixed fraud-decisioning strategy can behave differently when the underlying fraud environment changes significantly.



---



### 9.3 Signal Degradation



When fraud signals were degraded, fraud interception changed only modestly:



- Baseline: 87.09%

- Signal Degradation: 86.55%

- Change: -0.55 percentage points



This suggests relatively limited sensitivity under the specific synthetic degradation assumptions used in the test.



---



### 9.4 Behavioral Drift



The behavioral-drift scenario produced the same aggregate performance as the stress-test baseline.



This result is specific to the synthetic drift implementation and should not be interpreted as evidence that the strategy is immune to real-world behavioral drift.



---



### 9.5 Fraud Pattern Shift



Fraud pattern shift reduced interception to 83.18%.



The change relative to the stress-test baseline was:



`-3.91 percentage points`



This demonstrates that changes in the relationship between fraud events and available signals can reduce strategy effectiveness.



---



### 9.6 Velocity Variation



Velocity variation reduced interception to 84.18%.



The change relative to the stress-test baseline was:



`-2.91 percentage points`



This illustrates the importance of monitoring velocity-based signals because changes in transaction timing can affect rule performance.



---



## 10. Key Validation Findings



The validation process provides several findings:



1. The Baseline strategy satisfied the predefined review and decline constraints during development.

2. The same frozen strategy satisfied both constraints on the unseen May–June holdout.

3. Holdout fraud interception was 88.57%.

4. The synthetic stress tests demonstrated that performance can change materially under different fraud-environment assumptions.

5. High fraud prevalence produced the largest reduction in interception among the tested scenarios.

6. Fraud-pattern and velocity changes also reduced interception.

7. The stress-test results reinforce the need for ongoing strategy monitoring in a production environment.



---



## 11. Production Monitoring Implications



A production fraud strategy would require continuous monitoring of both fraud performance and operational outcomes.



Potential monitoring metrics include:



- fraud interception rate

- confirmed fraud rate

- false-positive rate

- false-decline rate

- review rate

- analyst workload

- approval rate

- customer friction

- fraud loss

- fraud prevalence

- signal coverage

- feature distribution drift

- rule hit rates

- strategy performance by channel

- strategy performance by fraud type



Monitoring should be used to identify deterioration in strategy performance and determine when thresholds, rules, features, or models require reassessment.



---



## 12. Limitations



The validation and stress-testing results are subject to several limitations.



### Synthetic Data



The transaction data and fraud labels are synthetic and do not represent observed bank transactions.



### Simplified Fraud Patterns



The injected fraud scenarios represent simplified versions of account takeover, velocity fraud, and geographic anomalies.



### Simplified Geographic Modeling



The geographic anomaly implementation does not represent a full production impossible-travel or geolocation-risk system.



### Illustrative Costs



The business-cost assumptions are analytical assumptions and are not based on actual bank loss or operational-cost data.



### Limited Time Horizon



The dataset covers six months, which is insufficient to represent long-term seasonal and strategic fraud changes.



### No Real-Time Environment



The project evaluates transactions in a batch analytical environment rather than a production real-time decisioning system.



---



## 13. Recommended Future Validation



Future iterations could extend the validation framework with:



- rolling time-window validation

- multiple historical holdout periods

- cross-channel validation

- fraud-type-specific performance monitoring

- threshold stability analysis

- feature drift detection

- probability calibration

- champion/challenger testing

- analyst feedback loops

- real-world cost calibration

- real-time decisioning simulation



These extensions would allow the strategy framework to better approximate a production fraud-management environment.


