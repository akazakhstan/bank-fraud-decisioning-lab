# Fraud Strategy Selection



## 1. Purpose



The purpose of the strategy-selection process is to identify a fraud-decisioning configuration that balances fraud interception with operational constraints and estimated business cost.



The strategy-selection process evaluates combinations of:



- fraud-signal weights

- review thresholds

- decline thresholds



The final strategy is selected using development-period results and then evaluated on an unseen time-based holdout.



---



## 2. Candidate Strategies



Five candidate strategies were evaluated during the final selection process.



| Strategy | Velocity | New Device | Amount | New State | Review Threshold | Decline Threshold |

|---|---:|---:|---:|---:|---:|---:|

| Baseline | 40 | 35 | 15 | 10 | 20 | 60 |

| Amount Emphasis | 35 | 35 | 20 | 10 | 20 | 60 |

| Balanced Higher Capture | 20 | 35 | 30 | 15 | 20 | 50 |

| Balanced Conservative | 30 | 45 | 15 | 10 | 30 | 60 |

| High Capture | 20 | 30 | 30 | 20 | 10 | 55 |



Weights sum to 100 for every strategy.



---



## 3. Selection Constraints



Operational constraints were established before final strategy selection.



### Review constraint



The proportion of transactions routed to manual review must not exceed:



`10%`



### Decline constraint



The proportion of transactions automatically declined must not exceed:



`1%`



A strategy must satisfy both constraints to be considered eligible for final selection.



These constraints are intended to prevent excessive analyst workload and excessive automated customer declines.



---



## 4. Development-Period Evaluation



The development period covers January through April 2026.



| Strategy | Fraud Interception | Review Rate | Decline Rate | Estimated Cost | Qualifies |

|---|---:|---:|---:|---:|---|

| Baseline | 81.07% | 9.35% | 0.80% | $86,600 | Yes |

| Amount Emphasis | 84.67% | 10.25% | 0.80% | $74,595 | No |

| Balanced Higher Capture | 84.67% | 10.14% | 0.91% | $74,420 | No |

| Balanced Conservative | 49.73% | 0.25% | 0.87% | $188,910 | Yes |

| High Capture | 94.80% | 79.89% | 0.89% | $152,750 | No |



The Amount Emphasis and Balanced Higher Capture strategies produced higher fraud interception than the Baseline during development, but both exceeded the 10% review-rate constraint.



The High Capture strategy produced substantially higher fraud interception but generated an operationally impractical review rate.



Two strategies therefore qualified:



- Baseline

- Balanced Conservative



---



## 5. Final Selection



Among the qualifying strategies, the Baseline strategy had the lower estimated cost under the stated analytical cost assumptions.



The Baseline strategy was therefore selected.



### Selected Configuration



| Signal | Weight |

|---|---:|

| Velocity | 40 |

| New Device | 35 |

| Amount Anomaly | 15 |

| New State | 10 |



Decision thresholds:



| Risk Score | Decision |

|---:|---|

| 0–24 | APPROVE |

| 25–59 | REVIEW |

| 60–100 | DECLINE |



---



## 6. Development Performance of Selected Strategy



The selected Baseline strategy produced:



- Fraud interception: 81.07%

- Fraud block rate: 35.73%

- Missed fraud rate: 18.93%

- Review rate: 9.35%

- Decline rate: 0.80%

- Decline precision: 100%

- Estimated cost: $86,600



Both operational constraints were satisfied during development.



---



## 7. Time-Based Holdout Evaluation



After selection, the Baseline configuration was evaluated on an unseen May–June 2026 holdout.



The strategy configuration was not changed for the holdout evaluation.



### Holdout Results



- Fraud interception: 88.57%

- Fraud block rate: 44.57%

- Missed fraud rate: 11.43%

- Review rate: 6.27%

- Decline rate: 0.94%

- Decline precision: 100%

- Estimated cost: $25,215



### Holdout Constraints



| Constraint | Result | Status |

|---|---:|---|

| Review rate ≤ 10% | 6.27% | PASS |

| Decline rate ≤ 1% | 0.94% | PASS |



The selected strategy therefore satisfied both operational constraints on the unseen holdout.



The difference between development and holdout performance should not be interpreted as evidence of improvement over time. The synthetic fraud composition and transaction characteristics differ between periods.



---



## 8. Why the Selection Process Matters



The strategy was not selected solely on maximum fraud detection.



Instead, the process incorporated three dimensions:



1\. \*\*Fraud effectiveness\*\*

2\. \*\*Operational feasibility\*\*

3\. \*\*Estimated business cost\*\*



This reflects the practical nature of fraud decisioning, where maximizing detection can create excessive customer friction or analyst workload.



The selection process therefore treats fraud strategy as a decision-optimization problem rather than a pure classification problem.



---



## 9. Cost Assumptions



The estimated cost framework uses the following illustrative assumptions:



| Cost Component | Assumption |

|---|---:|

| Missed fraud | $500 |

| Manual review | $5 |

| False decline | $25 |



These values are analytical assumptions used to compare strategies within the synthetic environment.



They do not represent observed costs from an actual financial institution.



Consequently, the estimated dollar amounts should not be interpreted as forecasts of real-world financial losses.



---



## 10. Interpretation



The Baseline strategy represents the selected operating point within the tested candidate set.



It provides a balance between fraud interception and operational constraints under the assumptions used in this project.



The unseen holdout evaluation provides evidence that the selected configuration continued to satisfy the predefined review and decline constraints during a later time period.



However, because the data and fraud scenarios are synthetic, the results demonstrate the methodology rather than production-level fraud performance.



---



## 11. Decisioning Framework



The complete selection framework can be summarized as:



```text

Candidate Strategies

&#x20;       ↓

Development Evaluation

&#x20;       ↓

Apply Operational Constraints

&#x20;       ↓

Remove Ineligible Strategies

&#x20;       ↓

Compare Estimated Cost

&#x20;       ↓

Select Baseline Strategy

&#x20;       ↓

Freeze Configuration

&#x20;       ↓

Evaluate Unseen Holdout

&#x20;       ↓

Stress Test


