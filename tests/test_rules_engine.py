from app.rules_engine import evaluate_transaction


def test_normal_transaction():
    result = evaluate_transaction({
        "risk_index": 0.20,
        "fraud_label": "normal",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 2
    })

    assert result["status"] == "NORMAL"
    assert result["alert_count"] == 0


def test_medium_risk_transaction():
    result = evaluate_transaction({
        "risk_index": 0.50,
        "fraud_label": "normal",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 3
    })

    assert result["status"] == "ALERT"
    assert "MEDIUM_RISK" in [
        alert["rule"] for alert in result["alerts"]
    ]


def test_high_risk_transaction():
    result = evaluate_transaction({
        "risk_index": 0.75,
        "fraud_label": "normal",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 3
    })

    assert result["status"] == "ALERT"
    assert "HIGH_RISK" in [
        alert["rule"] for alert in result["alerts"]
    ]


def test_critical_risk_transaction():
    result = evaluate_transaction({
        "risk_index": 0.95,
        "fraud_label": "normal",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 3
    })

    assert result["status"] == "ALERT"
    assert "CRITICAL_RISK" in [
        alert["rule"] for alert in result["alerts"]
    ]


def test_suspicious_transaction():
    result = evaluate_transaction({
        "risk_index": 0.30,
        "fraud_label": "suspicious",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 2
    })

    assert result["status"] == "ALERT"
    assert "SUSPICIOUS_TRANSACTION" in [
        alert["rule"] for alert in result["alerts"]
    ]


def test_high_frequency_transaction():
    result = evaluate_transaction({
        "risk_index": 0.30,
        "fraud_label": "normal",
        "foreign_txn_flag": False,
        "txn_count_past_hour": 10
    })

    assert result["status"] == "ALERT"
    assert "HIGH_TRANSACTION_FREQUENCY" in [
        alert["rule"] for alert in result["alerts"]
    ]


def test_foreign_high_risk_transaction():
    result = evaluate_transaction({
        "risk_index": 0.75,
        "fraud_label": "normal",
        "foreign_txn_flag": True,
        "txn_count_past_hour": 3
    })

    assert result["status"] == "ALERT"
    assert "FOREIGN_HIGH_RISK" in [
        alert["rule"] for alert in result["alerts"]
    ]