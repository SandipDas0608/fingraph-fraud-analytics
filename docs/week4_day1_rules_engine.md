# Week 4 - Day 1: Fraud Rules Engine

## Objective

Designed and implemented the foundation of an automated fraud-alert rules engine for the FinGraph project.

The rules engine evaluates transaction attributes and generates investigation alerts based on predefined risk conditions.

The implementation is independent of the current Neo4j connection issue.

---

## 1. Risk Thresholds

| Risk Index | Severity |
|------------|----------|
| < 0.40 | LOW |
| 0.40 - < 0.70 | MEDIUM |
| 0.70 - < 0.90 | HIGH |
| >= 0.90 | CRITICAL |

---

## 2. Fraud Alert Rules

### Rule 1 - Critical Risk

If:

risk_index >= 0.90

Generate:

CRITICAL_RISK

---

### Rule 2 - High Risk

If:

risk_index >= 0.70

Generate:

HIGH_RISK

---

### Rule 3 - Medium Risk

If:

risk_index >= 0.40

Generate:

MEDIUM_RISK

---

### Rule 4 - Suspicious Transaction

If:

fraud_label != "normal"

Generate:

SUSPICIOUS_TRANSACTION

---

### Rule 5 - High Transaction Frequency

If:

txn_count_past_hour >= 10

Generate:

HIGH_TRANSACTION_FREQUENCY

---

### Rule 6 - Foreign High-Risk Transaction

If:

foreign_txn_flag = True

and:

risk_index >= 0.70

Generate:

FOREIGN_HIGH_RISK

---

## 3. Rules Engine Architecture

Transaction Data
        |
        v
Rules Engine
        |
        v
Risk Evaluation
        |
        v
Fraud Rules
        |
        v
Alert Detection
        |
        v
ALERT / NORMAL

---

## 4. Implementation

Created:

app/rules_engine.py

The module provides:

evaluate_transaction()

The function accepts transaction information as a dictionary and returns:

- Overall status
- Risk index
- Triggered alerts
- Alert count

---

## 5. Automated Testing

Created:

tests/test_rules_engine.py

Seven test scenarios were implemented:

1. Normal transaction
2. Medium-risk transaction
3. High-risk transaction
4. Critical-risk transaction
5. Suspicious transaction
6. High-frequency transaction
7. Foreign high-risk transaction

---

## 6. Test Result

Automated tests were executed using pytest.

Result:

7 passed in 0.04s

All implemented rules passed their validation tests.

---

## 7. Neo4j Dependency

The current shared Neo4j connection is unavailable because of the existing routing issue.

Therefore, the rules engine was intentionally designed and tested independently of Neo4j.

Once the shared Neo4j connection is restored, the rules engine can be integrated with the FastAPI backend and live transaction data.

---

## 8. Day 1 Completion

Week 4 Day 1 successfully completed.

Completed work:

- Risk thresholds defined
- Fraud alert rules defined
- Rules engine implemented
- Automated test suite created
- Seven test cases validated
- Documentation completed

Status:

COMPLETED