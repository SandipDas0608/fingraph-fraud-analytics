"""
Kafka Event Consumer for Ingesting Transactions into Neo4j.
Engineered by shubhamgawari9226 - Ingests real-time events into Neo4j graph nodes.
"""
import os
import json
from dotenv import load_dotenv
from kafka import KafkaConsumer
from neo4j import GraphDatabase

load_dotenv()

# 1. Initialize Kafka Consumer Configuration
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'financial-transactions')
KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')
NEO4J_URI = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'neo4j')

print(f"Initializing Kafka Consumer engine for topic: '{KAFKA_TOPIC}'...")

try:
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=[KAFKA_SERVER],
        auto_offset_reset='latest',  # Read fresh live data packets arriving now
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    print(f"Connected to Kafka broker. Waiting for real-time live data blocks...\n")
except Exception as e:
    print(f"Error: Could not connect to Kafka server. Details: {e}")
    consumer = None

try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    neo4j_driver.verify_connectivity()
    print(f"Connected to Neo4j graph database at {NEO4J_URI}\n")
except Exception as e:
    print(f"Warning: Neo4j connection inactive ({e}). Ingestion will run in dry-run mode.\n")
    neo4j_driver = None


def ingest_transaction_to_graph(driver_instance, data: dict):
    """Ingest a streamed transaction record into Neo4j graph nodes and relationships."""
    if not driver_instance:
        return False
    query = """
    MERGE (a:Account {account_id: $account_id})
    MERGE (c:Card {card_no: $card_no})
    MERGE (l:Location {city: $city})
    MERGE (m:Merchant {merchant_type: $merchant_type})
    CREATE (t:Transaction {
        txn_id: $txn_id,
        txn_datetime: $txn_datetime,
        txn_amount: toFloat($txn_amount),
        txn_currency: $txn_currency,
        payment_channel: $payment_channel,
        km_from_home: toFloat($km_from_home),
        foreign_txn_flag: toInteger($foreign_txn_flag),
        txn_count_past_hour: toInteger($txn_count_past_hour),
        fraud_label: $fraud_label,
        risk_index: toFloat($risk_index)
    })
    MERGE (a)-[:USES_CARD]->(c)
    CREATE (a)-[:MADE]->(t)
    CREATE (t)-[:OCCURRED_IN]->(l)
    CREATE (t)-[:AT_MERCHANT]->(m)
    """
    params = {
        "account_id": str(data.get("customer_account", data.get("account_id", "ACC_UNKNOWN"))),
        "card_no": str(data.get("card_no", "CARD_UNKNOWN")),
        "city": str(data.get("city", "UNKNOWN")),
        "merchant_type": str(data.get("merchant_type", "General")),
        "txn_id": str(data.get("txn_id", "TXN_N/A")),
        "txn_datetime": str(data.get("txn_datetime", "")),
        "txn_amount": float(data.get("txn_amount", 0.0)),
        "txn_currency": str(data.get("txn_currency", "INR")),
        "payment_channel": str(data.get("payment_channel", "UPI")),
        "km_from_home": float(data.get("km_from_home", 0.0)),
        "foreign_txn_flag": int(data.get("foreign_txn_flag", 0)),
        "txn_count_past_hour": int(data.get("txn_count_past_hour", 1)),
        "fraud_label": str(data.get("fraud_label", "normal")),
        "risk_index": float(data.get("risk_index", 0.0))
    }
    with driver_instance.session() as session:
        session.run(query, **params)
    return True


# 2. Read and Parse the Incoming Live Stream Fields
if consumer is not None:
    try:
        for message in consumer:
            transaction_data = message.value
            
            # Dynamically extract fields matching your exact column headers
            tx_id = transaction_data.get('txn_id', 'N/A')
            timestamp = transaction_data.get('txn_datetime', 'N/A')
            amount = transaction_data.get('txn_amount', 'N/A')
            currency = transaction_data.get('txn_currency', 'N/A')
            city = transaction_data.get('city', 'N/A')
            label = str(transaction_data.get('fraud_label', 'N/A')).lower()
            
            # Print parsed records cleanly in tracking panel
            print("-" * 60)
            print(f"🚀 [LIVE TRANSACTION RECORD CAPTURED]")
            print(f"   🔹 ID        : {tx_id}")
            print(f"   🔹 Timestamp : {timestamp}")
            print(f"   🔹 Amount    : {amount} {currency}")
            print(f"   🔹 Location  : {city}")
            print(f"   🔹 Label     : {label}")
            
            # Automated flagging engine based on your new labels
            if 'suspicious' in label or '1' in label:
                print("   ⚠️  ALERT: Critical Suspicious Activity Flagged on this Account!")

            # Ingest to Neo4j
            if neo4j_driver:
                try:
                    ingest_transaction_to_graph(neo4j_driver, transaction_data)
                    print(f"   Graph Ingestion: Node & relationships synced to Neo4j")
                except Exception as ingest_err:
                    print(f"   Graph Ingestion Error: {ingest_err}")
                
    except KeyboardInterrupt:
        print("\nShutting down stream consumer node gracefully...")
    finally:
        if neo4j_driver:
            neo4j_driver.close()
