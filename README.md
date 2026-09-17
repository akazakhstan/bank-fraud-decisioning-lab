# Bank Fraud Decisioning Lab



A Python-based fraud analytics and decisioning laboratory for evaluating transaction-level fraud strategies under operational and business constraints.



The project focuses on a practical fraud-strategy question:



> How can a bank intercept meaningful amounts of fraud while controlling manual-review workload, automated declines, and estimated financial loss?



Rather than treating fraud detection as a pure classification problem, this project evaluates fraud decisioning as an **operational optimization problem**.



---



## Project Overview



The project develops a synthetic retail-banking transaction environment and evaluates a rule-based fraud decisioning framework.



The analytical workflow includes:



1. Synthetic transaction generation

2. Fraud scenario injection

3. Behavioral and velocity feature engineering

4. Fraud-rule development

5. Weighted risk scoring

6. Decision thresholds

7. Weight sensitivity analysis

8. Strategy grid search

9. Business-cost optimization

10. Cost sensitivity analysis

11. Time-based development/holdout validation

12. Synthetic stress testing

13. Final strategy selection



The final strategy is selected using development-period constraints and estimated business cost, then evaluated on an unseen future-period holdout.



---



## Decisioning Framework



```text

Transaction

&#x20;    |

&#x20;    v

Feature Engineering

&#x20;    |

&#x20;    v

Fraud Signals

&#x20;    |

&#x20;    v

Weighted Risk Score

&#x20;    |

&#x20;    v

+----------+----------+----------+

| APPROVE  |  REVIEW  | DECLINE  |

+----------+----------+----------+


