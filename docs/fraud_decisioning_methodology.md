# Fraud Decisioning Methodology



## 1. Project Objective



This project develops and evaluates a synthetic bank transaction fraud-decisioning strategy.



The objective is not simply to maximize fraud detection. The decisioning framework is designed to balance:



- fraud interception

- customer friction

- manual review workload

- false declines

- estimated financial loss



Each transaction receives fraud-related signals that are converted into a risk score and mapped to one of three operational decisions:



- APPROVE

- REVIEW

- DECLINE



The project emphasizes strategy evaluation, threshold optimization, business-cost analysis, time-based validation, and stress testing.



---



## 2. Synthetic Data



The project uses a synthetic transaction dataset designed to represent retail banking activity.



The dataset contains:



- 5,000 customers

- approximately 7,500 accounts

- 50,000 transactions

- transaction dates from January through June 2026

- multiple transaction channels

- multiple merchant categories

- customer and account identifiers

- device identifiers

- geographic information



Synthetic fraud scenarios include:



- account takeover (ATO)

- transaction velocity fraud

- geographic anomaly scenarios



The synthetic dataset is intended for methodology development and strategy testing. Results should not be interpreted as estimates of production bank fraud performance.



---



## 3. Fraud Signals



The decisioning framework uses four primary fraud signals.



### 3.1 Transaction Velocity



Velocity measures transaction activity within a short time window.



Current rule:



`transaction\_count\_2min >= 5`



This signal is intended to identify unusually concentrated transaction activity.



---



### 3.2 New Device



A transaction is flagged when it originates from a newly observed device.



Current rule:



`is\_new\_device == 1`



New-device activity is particularly relevant to account-takeover scenarios because a compromised account may be accessed from a device not previously associated with the customer.



---



### 3.3 Amount Anomaly



Transaction amount is compared with the customer's historical transaction behavior.



Current rule:



`amount\_ratio\_to\_customer\_avg >= 3`



This signal identifies transactions that are substantially larger than the customer's observed historical average.



---



### 3.4 New Geographic State



A transaction is flagged when the transaction state has not previously been observed for the customer.



Current rule:



`is\_new\_state == 1`



This signal is intended to represent geographic behavioral change.



The current synthetic implementation is simplified and should not be interpreted as a production impossible-travel model.



---



## 4. Risk Scoring



The baseline strategy assigns weighted points to the fraud signals.



| Signal | Weight |

|---|---:|

| Velocity | 40 |

| New Device | 35 |

| Amount Anomaly | 15 |

| New State | 10 |

| \*\*Total\*\* | \*\*100\*\* |



The resulting score is mapped into three decision bands.



| Risk Score | Decision |

|---:|---|

| 0–24 | APPROVE |

| 25–59 | REVIEW |

| 60–100 | DECLINE |



The design intentionally separates high-confidence automated blocking from transactions requiring additional review.



---



## 5. Strategy Evaluation



Multiple strategy configurations were evaluated by varying:



- signal weights

- review thresholds

- decline thresholds



The evaluation considered both fraud outcomes and operational impact.



Primary metrics included:



- fraud interception rate

- fraud block rate

- missed fraud rate

- review rate

- decline rate

- decline precision

- estimated business cost



---



## 6. Business-Cost Framework



Strategy optimization used illustrative business costs:



- missed fraud: $500

- manual review: $5

- false decline: $25



These values are analytical assumptions rather than observed bank economics.



Estimated strategy cost was used as a comparative optimization measure within the synthetic environment.



---



## 7. Operational Constraints



Before final strategy selection, operational constraints were defined:



- Review rate ≤ 10%

- Decline rate ≤ 1%



A candidate strategy had to satisfy both constraints during the development-period selection process to be eligible for final selection.



This prevents a strategy from achieving high fraud interception simply by routing an impractical proportion of transactions to manual review or automated decline.



---



## 8. Time-Based Validation



The data was divided chronologically:



- Development period: January–April 2026

- Holdout period: May–June 2026



Strategies were evaluated on the development period first.



The final strategy was selected using development-period constraints and cost.



The selected strategy was then evaluated on the unseen May–June holdout without changing its configuration.



This provides a more realistic validation framework than randomly splitting transactions because transaction fraud patterns can change over time.



---



## 9. Final Strategy Selection



Five candidate strategies were evaluated.



Two satisfied the development-period operational constraints.



The selected strategy was the \*\*Baseline\*\* strategy because it had the lowest estimated cost among the qualifying candidates under the stated analytical assumptions.



### Development Performance



| Metric | Baseline |

|---|---:|

| Fraud interception | 81.07% |

| Fraud block rate | 35.73% |

| Missed fraud | 18.93% |

| Review rate | 9.35% |

| Decline rate | 0.80% |

| Decline precision | 100% |

| Estimated cost | $86,600 |



### Unseen Holdout Performance



| Metric | Baseline |

|---|---:|

| Fraud interception | 88.57% |

| Fraud block rate | 44.57% |

| Missed fraud | 11.43% |

| Review rate | 6.27% |

| Decline rate | 0.94% |

| Decline precision | 100% |

| Estimated cost | $25,215 |



The holdout operational constraints were satisfied:



- Review rate: 6.27% ≤ 10%

- Decline rate: 0.94% ≤ 1%



The 100% decline precision observed in this synthetic dataset should not be generalized to production fraud systems.



---



## 10. Stress Testing



The selected strategy was evaluated under seven synthetic scenarios:



1\. Baseline

2\. Low Fraud Prevalence

3\. High Fraud Prevalence

4\. Signal Degradation

5\. Behavioral Drift

6\. Fraud Pattern Shift

7\. Velocity Variation



Stress testing was used to examine how the strategy changes when the fraud environment or signal quality changes.



The results demonstrate that strategy performance is sensitive to changes in fraud prevalence and fraud-pattern assumptions.



In particular, the high-fraud-prevalence scenario produced substantially lower fraud interception than the baseline scenario.



These results should be interpreted as sensitivity analysis rather than evidence of production robustness.



---



## 11. Methodological Workflow



The complete strategy-development workflow is:



```text

Synthetic Transaction Data

&#x20;         ↓

Feature Engineering

&#x20;         ↓

Fraud Rules

&#x20;         ↓

Risk Scoring

&#x20;         ↓

Weight \& Threshold Evaluation

&#x20;         ↓

Business-Cost Optimization

&#x20;         ↓

Development-Period Constraints

&#x20;         ↓

Final Strategy Selection

&#x20;         ↓

Unseen Time-Based Holdout

&#x20;         ↓

Stress Testing

&#x20;         ↓

Final Strategy Documentation


