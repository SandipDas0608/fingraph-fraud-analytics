from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import driver
from fastapi.responses import StreamingResponse
import csv
import io

app = FastAPI(title="FinGraph API")
# =========================
# CORS Configuration
# =========================

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Pydantic Response Models
# =========================

class LocationAnalytics(BaseModel):
    city: str
    total_transactions: int
    suspicious_transactions: int


class LocationAnalyticsResponse(BaseModel):
    count: int
    locations: list[LocationAnalytics]


class StatsResponse(BaseModel):
    total_accounts: int
    total_transactions: int
    fraud_transactions: int
    high_risk_transactions: int


class RiskDistributionItem(BaseModel):
    risk_level: str
    transaction_count: int
    percentage: float


class RiskDistributionResponse(BaseModel):
    total_transactions: int
    distribution: list[RiskDistributionItem]


class ApiEndpoint(BaseModel):
    name: str
    endpoint: str
    method: str


class ApiInfoResponse(BaseModel):
    project: str
    version: str
    total_endpoints: int
    endpoints: list[ApiEndpoint]


# Day 8 - Fraud Analytics Models
class FraudTransaction(BaseModel):
    txn_id: str
    account_id: str
    amount: float
    currency: str
    channel: str
    fraud_label: str
    risk_index: float
    txn_datetime: str


class FraudAnalyticsResponse(BaseModel):
    count: int
    transactions: list[FraudTransaction]


# =========================
# Root API
# =========================

@app.get("/")
def root():
    return {"message": "FinGraph Backend Running"}


# =========================
# Health Check
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# Database Test
# =========================

@app.get("/db-test")
def db_test():
    try:
        with driver.session() as session:

            result = session.run(
                "MATCH (a:Account) RETURN count(a) AS total_accounts"
            )

            record = result.single()

            return {
                "database": "connected",
                "total_accounts": record["total_accounts"]
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# API Information
# =========================

@app.get("/api-info", response_model=ApiInfoResponse)
def api_info():

    endpoints = [
        {"name": "Dashboard Stats", "endpoint": "/stats", "method": "GET"},
        {"name": "Transactions", "endpoint": "/transactions", "method": "GET"},
        {"name": "Fraud Summary", "endpoint": "/fraud-summary", "method": "GET"},
        {"name": "Fraud Analytics", "endpoint": "/fraud-analytics", "method": "GET"},
        {"name": "Fraud Breakdown", "endpoint": "/fraud-breakdown", "method": "GET"},
        {"name": "Risk Distribution", "endpoint": "/risk-distribution", "method": "GET"},
        {"name": "Merchant Analytics", "endpoint": "/merchant-analytics", "method": "GET"},
        {"name": "Location Analytics", "endpoint": "/location-analytics", "method": "GET"},
        {"name": "Fraud Trend", "endpoint": "/fraud-trend", "method": "GET"},
        {"name": "Export CSV", "endpoint": "/export-transactions", "method": "GET"},
    ]

    return {
        "project": "FinGraph Fraud Analytics",
        "version": "1.0.0",
        "total_endpoints": len(endpoints),
        "endpoints": endpoints
    }



# =========================
# Dashboard Statistics API
# =========================

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    try:
        with driver.session() as session:

            accounts = session.run(
                "MATCH (a:Account) RETURN count(a) AS count"
            ).single()["count"]

            transactions = session.run(
                "MATCH (t:Transaction) RETURN count(t) AS count"
            ).single()["count"]

            fraud = session.run(
                """
                MATCH (t:Transaction)
                WHERE t.fraud_label <> 'normal'
                RETURN count(t) AS count
                """
            ).single()["count"]

            high_risk = session.run(
                """
                MATCH (t:Transaction)
                WHERE t.risk_index >= 0.8
                RETURN count(t) AS count
                """
            ).single()["count"]

            return {
                "total_accounts": accounts,
                "total_transactions": transactions,
                "fraud_transactions": fraud,
                "high_risk_transactions": high_risk
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================
# Latest Transactions API
# =========================

@app.get("/transactions")
def get_transactions(
    page: int = 1,
    limit: int = 10,
    channel: str | None = None
):
    try:
        skip = (page - 1) * limit

        with driver.session() as session:

            if channel:

                total_query = """
                MATCH (t:Transaction)
                WHERE t.payment_channel = $channel
                RETURN count(t) AS count
                """

                data_query = """
                MATCH (a:Account)-[:MADE]->(t:Transaction)
                WHERE t.payment_channel = $channel
                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime
                ORDER BY t.txn_datetime DESC
                SKIP $skip
                LIMIT $limit
                """

            else:

                total_query = """
                MATCH (t:Transaction)
                RETURN count(t) AS count
                """

                data_query = """
                MATCH (a:Account)-[:MADE]->(t:Transaction)
                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime
                ORDER BY t.txn_datetime DESC
                SKIP $skip
                LIMIT $limit
                """

            total = session.run(
                total_query,
                channel=channel
            ).single()["count"]

            result = session.run(
                data_query,
                skip=skip,
                limit=limit,
                channel=channel
            )

            transactions = [dict(record) for record in result]

            return {
                "page": page,
                "limit": limit,
                "channel": channel,
                "total": total,
                "count": len(transactions),
                "transactions": transactions
            }

    except Exception as e:
        return {"error": str(e)}


# =========================
# Single Transaction API
# Day 14 - Enhanced Investigation Details
# =========================

@app.get("/transaction/{txn_id}")
def get_transaction(txn_id: str):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)
                    WHERE t.txn_id = $txn_id

                    OPTIONAL MATCH (t)-[:AT_MERCHANT]->(m:Merchant)
                    OPTIONAL MATCH (t)-[:OCCURRED_IN]->(l:Location)

                RETURN
                    a.account_id AS account_id,
                    t.txn_id AS txn_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime,
                    t.foreign_txn_flag AS foreign_txn,
                    t.txn_count_past_hour AS transactions_past_hour,
                    m.merchant_type AS merchant_type,
                    l.city AS city,

                    CASE
                        WHEN t.risk_index >= 0.9 THEN 'CRITICAL'
                        WHEN t.risk_index >= 0.7 THEN 'HIGH'
                        WHEN t.risk_index >= 0.4 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS risk_severity

                LIMIT 1
                """,
                txn_id=txn_id
            )

            record = result.single()

            if not record:
                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found"
                )

            transaction = dict(record)

            transaction["foreign_txn"] = bool(
                transaction["foreign_txn"]
            )

            return transaction

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Fraud Summary API
# =========================

@app.get("/fraud-summary")
def get_fraud_summary():
    try:
        with driver.session() as session:

            total = session.run(
                "MATCH (t:Transaction) RETURN count(t) AS count"
            ).single()["count"]

            suspicious = session.run(
                """
                MATCH (t:Transaction)
                WHERE t.fraud_label <> 'normal'
                RETURN count(t) AS count
                """
            ).single()["count"]

            high_risk = session.run(
                """
                MATCH (t:Transaction)
                WHERE t.risk_index >= 0.8
                RETURN count(t) AS count
                """
            ).single()["count"]

            fraud_percentage = (
                round((suspicious / total) * 100, 2)
                if total else 0
            )

            high_risk_percentage = (
                round((high_risk / total) * 100, 2)
                if total else 0
            )

            return {
                "total_transactions": total,
                "suspicious_transactions": suspicious,
                "high_risk_transactions": high_risk,
                "fraud_percentage": fraud_percentage,
                "high_risk_percentage": high_risk_percentage
            }

    except Exception as e:
        return {"error": str(e)}


# =========================
# Day 9 - Fraud Breakdown Models
# =========================

class FraudChannelBreakdown(BaseModel):
    channel: str
    total_transactions: int
    suspicious_transactions: int
    fraud_percentage: float
    average_risk: float
    highest_risk: float


class FraudBreakdownResponse(BaseModel):
    count: int
    channels: list[FraudChannelBreakdown]


# =========================
# Day 8 - Fraud Analytics API
# =========================

@app.get(
    "/fraud-analytics",
    response_model=FraudAnalyticsResponse
)
def get_fraud_analytics(
    limit: int = 20,
    min_risk: float = 0.0
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)
                WHERE t.fraud_label <> 'normal'
                  AND t.risk_index >= $min_risk

                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime

                ORDER BY t.risk_index DESC
                LIMIT $limit
                """,
                min_risk=min_risk,
                limit=limit
            )

            transactions = [dict(record) for record in result]

            return {
                "count": len(transactions),
                "transactions": transactions
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 9 - Fraud Breakdown API
# =========================

@app.get(
    "/fraud-breakdown",
    response_model=FraudBreakdownResponse
)
def get_fraud_breakdown():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                WITH
                    t.payment_channel AS channel,
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label <> 'normal'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions,
                    avg(t.risk_index) AS average_risk,
                    max(t.risk_index) AS highest_risk

                RETURN
                    channel,
                    total_transactions,
                    suspicious_transactions,
                    round(
                        (toFloat(suspicious_transactions) /
                        total_transactions) * 100,
                        2
                    ) AS fraud_percentage,
                    round(average_risk, 3) AS average_risk,
                    round(highest_risk, 3) AS highest_risk

                ORDER BY fraud_percentage DESC
                """
            )

            channels = [dict(record) for record in result]

            return {
                "count": len(channels),
                "channels": channels
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 10 - Risk Distribution API
# =========================

@app.get(
    "/risk-distribution",
    response_model=RiskDistributionResponse
)
def get_risk_distribution():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                WITH
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.risk_index < 0.4
                            THEN 1
                            ELSE 0
                        END
                    ) AS low_risk,
                    sum(
                        CASE
                            WHEN t.risk_index >= 0.4
                            AND t.risk_index < 0.8
                            THEN 1
                            ELSE 0
                        END
                    ) AS medium_risk,
                    sum(
                        CASE
                            WHEN t.risk_index >= 0.8
                            THEN 1
                            ELSE 0
                        END
                    ) AS high_risk

                RETURN
                    total_transactions,
                    low_risk,
                    medium_risk,
                    high_risk
                """
            )

            record = result.single()

            total = record["total_transactions"]
            low = record["low_risk"]
            medium = record["medium_risk"]
            high = record["high_risk"]

            distribution = [
                {
                    "risk_level": "Low Risk",
                    "transaction_count": low,
                    "percentage": round(
                        (low / total) * 100, 2
                    ) if total else 0
                },
                {
                    "risk_level": "Medium Risk",
                    "transaction_count": medium,
                    "percentage": round(
                        (medium / total) * 100, 2
                    ) if total else 0
                },
                {
                    "risk_level": "High Risk",
                    "transaction_count": high,
                    "percentage": round(
                        (high / total) * 100, 2
                    ) if total else 0
                }
            ]

            return {
                "total_transactions": total,
                "distribution": distribution
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
    
# =========================
# Merchant Analytics API
# =========================

@app.get("/merchant-analytics")
def get_merchant_analytics():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)-[:AT_MERCHANT]->(m:Merchant)

                RETURN
                    m.merchant_type AS merchant_type,
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label <> 'normal'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions

                ORDER BY total_transactions DESC
                """
            )

            merchants = [dict(record) for record in result]

            return {
                "count": len(merchants),
                "merchants": merchants
            }

    except Exception as e:
        return {"error": str(e)}


# =========================
# Location Analytics API
# =========================

@app.get(
    "/location-analytics",
    response_model=LocationAnalyticsResponse
)
def get_location_analytics():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)-[:OCCURRED_IN]->(l:Location)

                RETURN
                    l.city AS city,
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label <> 'normal'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions

                ORDER BY total_transactions DESC
                """
            )

            locations = [dict(record) for record in result]

            return {
                "count": len(locations),
                "locations": locations
            }

    except Exception as e:
        return {"error": str(e)}


# =========================
# Account Transactions API
# =========================

@app.get("/account/{account_id}")
def get_account_transactions(
    account_id: str,
    limit: int = 20
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account {account_id: $account_id})-[:MADE]->(t:Transaction)

                RETURN
                    a.account_id AS account_id,
                    t.txn_id AS txn_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime

                ORDER BY t.txn_datetime DESC
                LIMIT $limit
                """,
                account_id=account_id,
                limit=limit
            )

            transactions = [dict(record) for record in result]

            return {
                "account_id": account_id,
                "count": len(transactions),
                "transactions": transactions
            }

    except Exception as e:
        return {"error": str(e)}



# =========================
# Fraud Trend API
# =========================

@app.get("/fraud-trend")
def get_fraud_trend():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                WHERE t.fraud_label <> 'normal'

                RETURN
                    substring(t.txn_datetime, 0, 10) AS date,
                    count(t) AS suspicious_transactions

                ORDER BY date
                """
            )

            trend = [dict(record) for record in result]

            return {
                "count": len(trend),
                "trend": trend
            }

    except Exception as e:
        return {"error": str(e)}


# =========================
# CSV Export API
# =========================

@app.get("/export-transactions")
def export_transactions(limit: int = 100):

    with driver.session() as session:

        result = session.run(
            """
            MATCH (a:Account)-[:MADE]->(t:Transaction)

            RETURN
                a.account_id AS account_id,
                t.txn_id AS txn_id,
                t.txn_amount AS amount,
                t.payment_channel AS channel,
                t.fraud_label AS fraud_label,
                t.risk_index AS risk_index,
                t.txn_datetime AS txn_datetime

            ORDER BY t.txn_datetime DESC

            LIMIT $limit
            """,
            limit=limit
        )

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "account_id",
            "txn_id",
            "amount",
            "channel",
            "fraud_label",
            "risk_index",
            "txn_datetime"
        ])

        for record in result:
            writer.writerow(record.values())

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=transactions.csv"
            }
        )


# =========================
# Day 12 - Analytics Summary KPI API
# =========================

@app.get("/analytics-summary")
def get_analytics_summary():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)
                RETURN
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label = 'suspicious'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label = 'suspicious'
                            AND t.foreign_txn_flag = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_foreign_transactions
                """
            )

            record = result.single()

            total = record["total_transactions"]
            suspicious = record["suspicious_transactions"]

            suspicious_rate = (
                round((suspicious / total) * 100, 2)
                if total else 0
            )

            return {
                "total_transactions": total,
                "suspicious_transactions": suspicious,
                "suspicious_rate": suspicious_rate,
                "suspicious_foreign_transactions":
                    record["suspicious_foreign_transactions"]
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 12 - Account Risk Distribution API
# =========================

@app.get("/account-risk-distribution")
def get_account_risk_distribution():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(:Transaction)
                WHERE a.account_id IS NOT NULL
                  AND a.risk_score IS NOT NULL

                WITH DISTINCT a

                RETURN
                    CASE
                        WHEN a.risk_score >= 80 THEN 'CRITICAL'
                        WHEN a.risk_score >= 60 THEN 'HIGH'
                        WHEN a.risk_score >= 30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS risk_tier,
                    count(a) AS account_count
                """
            )

            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }

            for record in result:
                tier = record["risk_tier"].lower()
                distribution[tier] = record["account_count"]

            return {
                "risk_distribution": distribution
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 12 - Top Risk Accounts API
# =========================

@app.get("/top-risk-accounts")
def get_top_risk_accounts(limit: int = 10):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(:Transaction)
                WHERE a.account_id IS NOT NULL
                  AND a.risk_score IS NOT NULL

                WITH DISTINCT a

                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS risk_score,
                    CASE
                        WHEN a.risk_score >= 80 THEN 'CRITICAL'
                        WHEN a.risk_score >= 60 THEN 'HIGH'
                        WHEN a.risk_score >= 30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS risk_tier

                ORDER BY a.risk_score DESC
                LIMIT $limit
                """,
                limit=limit
            )

            accounts = [dict(record) for record in result]

            return {
                "count": len(accounts),
                "accounts": accounts
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 12 - Suspicious Merchant Analysis API
# =========================

@app.get("/suspicious-merchants")
def get_suspicious_merchants():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)-[:AT_MERCHANT]->(m:Merchant)
                WHERE t.fraud_label = 'suspicious'

                RETURN
                    m.merchant_type AS merchant_type,
                    count(t) AS suspicious_transactions

                ORDER BY suspicious_transactions DESC
                """
            )

            merchants = [dict(record) for record in result]

            return {
                "count": len(merchants),
                "merchants": merchants
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 12 - Transaction Frequency Analysis API
# =========================

@app.get("/transaction-frequency")
def get_transaction_frequency():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                RETURN
                    t.txn_count_past_hour AS transactions_past_hour,
                    t.fraud_label AS fraud_label,
                    count(t) AS transaction_count

                ORDER BY transactions_past_hour DESC, fraud_label
                """
            )

            frequency = [dict(record) for record in result]

            return {
                "count": len(frequency),
                "frequency": frequency
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 12 - Foreign Transaction Analysis API
# =========================

@app.get("/foreign-transactions")
def get_foreign_transactions():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                RETURN
                    t.foreign_txn_flag AS foreign_txn,
                    t.fraud_label AS fraud_label,
                    count(t) AS transaction_count

                ORDER BY foreign_txn, fraud_label
                """
            )

            foreign_transactions = []

            for record in result:
                foreign_transactions.append({
                    "foreign_txn": bool(record["foreign_txn"]),
                    "fraud_label": record["fraud_label"],
                    "transaction_count": record["transaction_count"]
                })

            return {
                "count": len(foreign_transactions),
                "foreign_transactions": foreign_transactions
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 12 - Circular Flow Test API
# Synthetic/Test Data Only
# =========================

@app.get("/circular-flow-test")
def get_circular_flow_test():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH p = (a:Account)-[:TRANSFERRED_TO*3..3]->(a)
                WHERE a.account_id STARTS WITH 'TEST'

                RETURN
                    a.account_id AS start_account,
                    [n IN nodes(p) | n.account_id] AS flow,
                    length(p) AS path_length
                """
            )

            cycles = [dict(record) for record in result]

            return {
                "test_data": True,
                "production_data": False,
                "note": (
                    "Circular-flow detection is currently validated "
                    "only on synthetic test data."
                ),
                "count": len(cycles),
                "cycles": cycles
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================
# Day 13 - Account Investigation API
# =========================

@app.get("/account-investigation/{account_id}")
def get_account_investigation(
    account_id: str,
    limit: int = 20
):
    try:
        with driver.session() as session:

            # Account-level summary
            summary_result = session.run(
                """
                MATCH (a:Account {account_id: $account_id})-[:MADE]->(t:Transaction)

                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS risk_score,

                    CASE
                        WHEN a.risk_score >= 80 THEN 'CRITICAL'
                        WHEN a.risk_score >= 60 THEN 'HIGH'
                        WHEN a.risk_score >= 30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS risk_tier,

                    count(t) AS total_transactions,

                    sum(
                        CASE
                            WHEN t.fraud_label = 'suspicious'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions,

                    max(t.risk_index) AS highest_transaction_risk,

                    sum(
                        CASE
                            WHEN t.foreign_txn_flag = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS foreign_transactions
                """,
                account_id=account_id
            )

            summary = summary_result.single()

            if not summary:
                raise HTTPException(
                    status_code=404,
                    detail="Account not found"
                )

            # Recent transactions
            transaction_result = session.run(
                """
                MATCH (a:Account {account_id: $account_id})-[:MADE]->(t:Transaction)

                RETURN
                    t.txn_id AS txn_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.fraud_label AS fraud_label,
                    t.risk_index AS risk_index,
                    t.foreign_txn_flag AS foreign_txn,
                    t.txn_datetime AS txn_datetime

                ORDER BY t.txn_datetime DESC
                LIMIT $limit
                """,
                account_id=account_id,
                limit=limit
            )

            transactions = [
                dict(record)
                for record in transaction_result
            ]

            return {
                "account": dict(summary),
                "recent_transactions": transactions
            }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 13 - Investigation Alerts API
# =========================

@app.get("/investigation-alerts")
def get_investigation_alerts(
    limit: int = 20,
    min_risk: float = 0.0
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)

                WHERE t.fraud_label = 'suspicious'
                  AND t.risk_index >= $min_risk

                OPTIONAL MATCH (t)-[:AT_MERCHANT]->(m:Merchant)
                OPTIONAL MATCH (t)-[:OCCURRED_IN]->(l:Location)

                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.payment_channel AS channel,
                    t.risk_index AS risk_index,
                    t.foreign_txn_flag AS foreign_txn,
                    t.txn_count_past_hour AS transactions_past_hour,
                    t.txn_datetime AS txn_datetime,
                    m.merchant_type AS merchant_type,
                    l.city AS city,

                    CASE
                        WHEN t.risk_index >= 0.80 THEN 'CRITICAL'
                        WHEN t.risk_index >= 0.60 THEN 'HIGH'
                        WHEN t.risk_index >= 0.30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS alert_severity

                ORDER BY t.risk_index DESC
                LIMIT $limit
                """,
                limit=limit,
                min_risk=min_risk
            )

            alerts = []

            for record in result:
                alert = dict(record)

                alert["foreign_txn"] = bool(
                    alert["foreign_txn"]
                )

                alerts.append(alert)

            return {
                "count": len(alerts),
                "min_risk": min_risk,
                "alerts": alerts
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 14 - Investigation Accounts API
# =========================

@app.get("/investigation-accounts")
def get_investigation_accounts(
    limit: int = 20,
    min_risk_score: int = 0
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)

                WHERE a.account_id IS NOT NULL
                  AND a.risk_score IS NOT NULL
                  AND a.risk_score >= $min_risk_score

                WITH
                    a,
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label = 'suspicious'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions,
                    sum(t.txn_amount) AS total_amount,
                    max(t.risk_index) AS highest_transaction_risk

                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS risk_score,

                    CASE
                        WHEN a.risk_score >= 80 THEN 'CRITICAL'
                        WHEN a.risk_score >= 60 THEN 'HIGH'
                        WHEN a.risk_score >= 30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS risk_tier,

                    total_transactions,
                    suspicious_transactions,
                    round(total_amount, 2) AS total_amount,
                    highest_transaction_risk

                ORDER BY
                    a.risk_score DESC,
                    suspicious_transactions DESC,
                    highest_transaction_risk DESC

                LIMIT $limit
                """,
                limit=limit,
                min_risk_score=min_risk_score
            )

            accounts = [
                dict(record)
                for record in result
            ]

            return {
                "count": len(accounts),
                "min_risk_score": min_risk_score,
                "accounts": accounts
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 15 - Dashboard Overview API
# =========================

@app.get("/dashboard-overview")
def get_dashboard_overview():
    try:
        with driver.session() as session:

            # Main dashboard statistics
            stats_record = session.run(
                """
                MATCH (t:Transaction)

                WITH
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label <> 'normal'
                            THEN 1
                            ELSE 0
                        END
                    ) AS fraud_transactions,
                    sum(
                        CASE
                            WHEN t.risk_index >= 0.8
                            THEN 1
                            ELSE 0
                        END
                    ) AS high_risk_transactions

                MATCH (a:Account)

                RETURN
                    count(a) AS total_accounts,
                    total_transactions,
                    fraud_transactions,
                    high_risk_transactions
                """
            )

            stats = dict(stats_record.single())

            # Latest high-risk alerts
            alerts_result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)

                WHERE t.risk_index >= 0.8

                OPTIONAL MATCH (t)-[:AT_MERCHANT]->(m:Merchant)
                OPTIONAL MATCH (t)-[:OCCURRED_IN]->(l:Location)

                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime,
                    m.merchant_type AS merchant_type,
                    l.city AS city

                ORDER BY t.risk_index DESC
                LIMIT 5
                """
            )

            recent_alerts = [
                dict(record)
                for record in alerts_result
            ]

            # Highest-risk accounts
            accounts_result = session.run(
                """
                MATCH (a:Account)

                WHERE a.risk_score IS NOT NULL
                AND a.account_id IS NOT NULL
                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS risk_score,
                    a.risk_tier AS risk_tier

                ORDER BY a.risk_score DESC
                LIMIT 5
                """
            )

            top_risk_accounts = [
                dict(record)
                for record in accounts_result
            ]

            return {
                "stats": stats,
                "recent_alerts": recent_alerts,
                "top_risk_accounts": top_risk_accounts
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# Day 16 - Dashboard Analytics API
# =========================

@app.get("/dashboard-analytics")
def get_dashboard_analytics():
    try:
        with driver.session() as session:

            # Risk distribution
            risk_result = session.run(
                """
                MATCH (t:Transaction)

                RETURN
                    sum(CASE
                        WHEN t.risk_index < 0.4
                        THEN 1 ELSE 0
                    END) AS low,

                    sum(CASE
                        WHEN t.risk_index >= 0.4
                        AND t.risk_index < 0.8
                        THEN 1 ELSE 0
                    END) AS medium,

                    sum(CASE
                        WHEN t.risk_index >= 0.8
                        THEN 1 ELSE 0
                    END) AS high
                """
            )

            risk_record = risk_result.single()

            risk_distribution = {
                "low": risk_record["low"],
                "medium": risk_record["medium"],
                "high": risk_record["high"]
            }

            # Fraud by payment channel
            channel_result = session.run(
                """
                MATCH (t:Transaction)

                RETURN
                    t.payment_channel AS channel,
                    count(t) AS total_transactions,
                    sum(
                        CASE
                            WHEN t.fraud_label <> 'normal'
                            THEN 1
                            ELSE 0
                        END
                    ) AS suspicious_transactions

                ORDER BY suspicious_transactions DESC
                """
            )

            fraud_by_channel = [
                dict(record)
                for record in channel_result
            ]

            # Suspicious merchants
            merchant_result = session.run(
                """
                MATCH (t:Transaction)-[:AT_MERCHANT]->(m:Merchant)

                WHERE t.fraud_label <> 'normal'

                RETURN
                    m.merchant_type AS merchant_type,
                    count(t) AS suspicious_transactions

                ORDER BY suspicious_transactions DESC
                LIMIT 10
                """
            )

            suspicious_merchants = [
                dict(record)
                for record in merchant_result
            ]

            # Fraud trend
            trend_result = session.run(
                """
                MATCH (t:Transaction)

                WHERE t.fraud_label <> 'normal'

                RETURN
                    substring(t.txn_datetime, 0, 10) AS date,
                    count(t) AS suspicious_transactions

                ORDER BY date
                """
            )

            fraud_trend = [
                dict(record)
                for record in trend_result
            ]

            return {
                "risk_distribution": risk_distribution,
                "fraud_by_channel": fraud_by_channel,
                "suspicious_merchants": suspicious_merchants,
                "fraud_trend": fraud_trend
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Alert & Notification System API
# =========================

@app.get("/alert-notifications")
def get_alert_notifications(
    limit: int = 20,
    min_risk: float = 0.6
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)

                WHERE t.fraud_label = 'suspicious'
                  AND t.risk_index >= $min_risk

                OPTIONAL MATCH (t)-[:AT_MERCHANT]->(m:Merchant)
                OPTIONAL MATCH (t)-[:OCCURRED_IN]->(l:Location)

                RETURN
                    t.txn_id AS txn_id,
                    a.account_id AS account_id,
                    t.txn_amount AS amount,
                    t.txn_currency AS currency,
                    t.risk_index AS risk_index,
                    t.txn_datetime AS txn_datetime,
                    t.notification_status AS notification_status,
                    m.merchant_type AS merchant_type,
                    l.city AS city,

                    CASE
                        WHEN t.risk_index >= 0.80 THEN 'CRITICAL'
                        WHEN t.risk_index >= 0.60 THEN 'HIGH'
                        WHEN t.risk_index >= 0.30 THEN 'MEDIUM'
                        ELSE 'LOW'
                    END AS severity

                ORDER BY t.risk_index DESC
                LIMIT $limit
                """,
                limit=limit,
                min_risk=min_risk
            )

            notifications = []

            for record in result:
                item = dict(record)

                severity = item["severity"]
                account_id = item["account_id"]
                amount = item["amount"]
                currency = item["currency"]
                risk_index = item["risk_index"]

                if severity == "CRITICAL":
                    title = "Critical Fraud Alert"
                elif severity == "HIGH":
                    title = "High Risk Transaction Alert"
                else:
                    title = "Suspicious Transaction Alert"

                message = (
                    f"{severity} risk transaction detected "
                    f"for account {account_id}. "
                    f"Amount: {amount} {currency}. "
                    f"Risk score: {risk_index}."
                )

                notifications.append({
                    "txn_id": item["txn_id"],
                    "account_id": account_id,
                    "title": title,
                    "message": message,
                    "severity": severity,
                    "risk_index": risk_index,
                    "amount": amount,
                    "currency": currency,
                    "merchant_type": item["merchant_type"],
                    "city": item["city"],
                    "txn_datetime": item["txn_datetime"],
                    "status": item["notification_status"] or "unread"
                })

            return {
                "count": len(notifications),
                "min_risk": min_risk,
                "notifications": notifications
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# =========================
# Day 17 + Day 20 - Alert Notification Summary API
# =========================

@app.get("/alert-notification-summary")
def get_alert_notification_summary():
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction)

                WHERE t.fraud_label = 'suspicious'
                  AND t.risk_index >= 0.30

                RETURN
                    count(t) AS total_notifications,

                    sum(
                        CASE
                            WHEN t.risk_index >= 0.80
                            THEN 1
                            ELSE 0
                        END
                    ) AS critical,

                    sum(
                        CASE
                            WHEN t.risk_index >= 0.60
                            AND t.risk_index < 0.80
                            THEN 1
                            ELSE 0
                        END
                    ) AS high,

                    sum(
                        CASE
                            WHEN t.risk_index >= 0.30
                            AND t.risk_index < 0.60
                            THEN 1
                            ELSE 0
                        END
                    ) AS medium,

                    sum(
                        CASE
                            WHEN t.notification_status = 'acknowledged'
                            THEN 1
                            ELSE 0
                        END
                    ) AS acknowledged,

                    sum(
                        CASE
                            WHEN t.notification_status IS NULL
                              OR t.notification_status = 'unread'
                            THEN 1
                            ELSE 0
                        END
                    ) AS unread
                """
            )

            record = result.single()

            return {
                "total_notifications": record["total_notifications"],
                "critical": record["critical"],
                "high": record["high"],
                "medium": record["medium"],
                "unread": record["unread"],
                "acknowledged": record["acknowledged"]
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
# =========================
# Day 18 - Account Risk Scores API
# =========================

@app.get("/account-risk-scores")
def get_account_risk_scores(
    limit: int = 20,
    min_score: int = 0
):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)
                WHERE a.account_id IS NOT NULL
                  AND a.risk_score IS NOT NULL
                  AND a.risk_score >= $min_score

                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS risk_score,
                    a.risk_tier AS risk_tier,
                    a.last_risk_calculated AS last_risk_calculated

                ORDER BY a.risk_score DESC, a.account_id
                LIMIT $limit
                """,
                limit=limit,
                min_score=min_score
            )

            accounts = []

            for record in result:
                account = dict(record)

                if account["last_risk_calculated"] is not None:
                    account["last_risk_calculated"] = str(
                        account["last_risk_calculated"]
                    )

                accounts.append(account)

            return {
                "count": len(accounts),
                "min_score": min_score,
                "accounts": accounts
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Day 19 - Alert Acknowledgement API
# =========================

@app.patch("/alert-notifications/{txn_id}/acknowledge")
def acknowledge_alert(txn_id: str):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (t:Transaction {txn_id: $txn_id})
                WHERE t.fraud_label <> 'normal'

                SET t.notification_status = 'acknowledged',
                    t.acknowledged_at = datetime()

                RETURN
                    t.txn_id AS txn_id,
                    t.notification_status AS status,
                    t.acknowledged_at AS acknowledged_at
                """,
                txn_id=txn_id
            ).single()

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail="Fraud alert not found"
                )

            return {
                "message": "Alert acknowledged successfully",
                "txn_id": result["txn_id"],
                "status": result["status"],
                "acknowledged_at": str(result["acknowledged_at"])
            }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# =========================
# Fraud Network API
# =========================

@app.get("/fraud-network")
def get_fraud_network(limit: int = 50):
    try:
        with driver.session() as session:

            result = session.run(
                """
                MATCH (a:Account)-[:MADE]->(t:Transaction)
                OPTIONAL MATCH (t)-[:AT_MERCHANT]->(m:Merchant)
                OPTIONAL MATCH (t)-[:OCCURRED_IN]->(l:Location)

                WHERE t.fraud_label <> 'normal'

                RETURN
                    a.account_id AS account_id,
                    a.risk_score AS account_risk_score,
                    a.risk_tier AS account_risk_tier,
                    t.txn_id AS txn_id,
                    t.risk_index AS risk_index,
                    t.fraud_label AS fraud_label,
                    t.txn_amount AS amount,
                    m.merchant_type AS merchant_type,
                    l.city AS city

                ORDER BY t.risk_index DESC
                LIMIT $limit
                """,
                limit=limit
            )

            nodes = []
            edges = []
            seen_nodes = set()

            for record in result:

                account_id = record["account_id"]
                txn_id = record["txn_id"]
                merchant_type = record["merchant_type"]
                city = record["city"]

                # Account node
                account_node_id = f"account:{account_id}"

                if account_node_id not in seen_nodes:
                    nodes.append({
                        "id": account_node_id,
                        "type": "account",
                        "label": account_id,
                        "risk_score": record["account_risk_score"],
                        "risk_tier": record["account_risk_tier"]
                    })
                    seen_nodes.add(account_node_id)

                # Transaction node
                txn_node_id = f"transaction:{txn_id}"

                if txn_node_id not in seen_nodes:
                    nodes.append({
                        "id": txn_node_id,
                        "type": "transaction",
                        "label": txn_id,
                        "risk_index": record["risk_index"],
                        "fraud_label": record["fraud_label"],
                        "amount": record["amount"]
                    })
                    seen_nodes.add(txn_node_id)

                edges.append({
                    "source": account_node_id,
                    "target": txn_node_id,
                    "relationship": "MADE"
                })

                # Merchant node
                if merchant_type:
                    merchant_node_id = f"merchant:{merchant_type}"

                    if merchant_node_id not in seen_nodes:
                        nodes.append({
                            "id": merchant_node_id,
                            "type": "merchant",
                            "label": merchant_type
                        })
                        seen_nodes.add(merchant_node_id)

                    edges.append({
                        "source": txn_node_id,
                        "target": merchant_node_id,
                        "relationship": "AT_MERCHANT"
                    })

                # Location node
                if city:
                    location_node_id = f"location:{city}"

                    if location_node_id not in seen_nodes:
                        nodes.append({
                            "id": location_node_id,
                            "type": "location",
                            "label": city
                        })
                        seen_nodes.add(location_node_id)

                    edges.append({
                        "source": txn_node_id,
                        "target": location_node_id,
                        "relationship": "OCCURRED_IN"
                    })

            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_nodes": len(nodes),
                    "total_edges": len(edges)
                }
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )