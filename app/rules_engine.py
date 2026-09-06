# ==========================================
# FinGraph - Fraud Rules Engine
# Week 4 - Day 1
# ==========================================


# Risk thresholds
CRITICAL_RISK = 0.90
HIGH_RISK = 0.70
MEDIUM_RISK = 0.40

# Transaction-frequency threshold
HIGH_FREQUENCY_THRESHOLD = 10


def evaluate_transaction(transaction: dict) -> dict:
    """
    Evaluate a transaction against FinGraph fraud rules.

    This function does not connect to Neo4j.
    It evaluates transaction data supplied as a dictionary.
    """

    risk_index = float(transaction.get("risk_index", 0))
    fraud_label = str(
        transaction.get("fraud_label", "normal")
    ).lower()

    foreign_txn = bool(
        transaction.get("foreign_txn_flag", False)
    )

    transactions_past_hour = int(
        transaction.get("txn_count_past_hour", 0)
    )

    alerts = []

    # ------------------------------------------
    # Rule 1 - Critical Risk
    # ------------------------------------------

    if risk_index >= CRITICAL_RISK:
        alerts.append({
            "rule": "CRITICAL_RISK",
            "severity": "CRITICAL",
            "message": "Transaction risk index is critically high."
        })

    # ------------------------------------------
    # Rule 2 - High Risk
    # ------------------------------------------

    elif risk_index >= HIGH_RISK:
        alerts.append({
            "rule": "HIGH_RISK",
            "severity": "HIGH",
            "message": "Transaction risk index is high."
        })

    # ------------------------------------------
    # Rule 3 - Medium Risk
    # ------------------------------------------

    elif risk_index >= MEDIUM_RISK:
        alerts.append({
            "rule": "MEDIUM_RISK",
            "severity": "MEDIUM",
            "message": "Transaction requires additional review."
        })

    # ------------------------------------------
    # Rule 4 - Suspicious Transaction
    # ------------------------------------------

    if fraud_label != "normal":
        alerts.append({
            "rule": "SUSPICIOUS_TRANSACTION",
            "severity": "HIGH",
            "message": "Transaction has a suspicious fraud label."
        })

    # ------------------------------------------
    # Rule 5 - High Transaction Frequency
    # ------------------------------------------

    if transactions_past_hour >= HIGH_FREQUENCY_THRESHOLD:
        alerts.append({
            "rule": "HIGH_TRANSACTION_FREQUENCY",
            "severity": "HIGH",
            "message": "High number of transactions detected within one hour."
        })

    # ------------------------------------------
    # Rule 6 - Foreign High-Risk Transaction
    # ------------------------------------------

    if foreign_txn and risk_index >= HIGH_RISK:
        alerts.append({
            "rule": "FOREIGN_HIGH_RISK",
            "severity": "HIGH",
            "message": "Foreign transaction has a high risk index."
        })

    # ------------------------------------------
    # Determine overall status
    # ------------------------------------------

    if not alerts:
        status = "NORMAL"
    else:
        status = "ALERT"

    return {
        "status": status,
        "risk_index": risk_index,
        "alerts": alerts,
        "alert_count": len(alerts)
    }