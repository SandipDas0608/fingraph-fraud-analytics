// FinGraph Data Engineering - Bulk CSV Cypher Ingestion Script
// Engineered by shubhamgawari9226
// Aligned with production schema: Account, Card, Location, Merchant, Transaction

// Step 1: Enforce Unique Constraints and Indexes
CREATE CONSTRAINT account_id_unique IF NOT EXISTS
FOR (a:Account) REQUIRE a.account_id IS UNIQUE;

CREATE CONSTRAINT card_no_unique IF NOT EXISTS
FOR (c:Card) REQUIRE c.card_no IS UNIQUE;

CREATE CONSTRAINT txn_id_unique IF NOT EXISTS
FOR (t:Transaction) REQUIRE t.txn_id IS UNIQUE;

CREATE CONSTRAINT location_city_unique IF NOT EXISTS
FOR (l:Location) REQUIRE l.city IS UNIQUE;

CREATE CONSTRAINT merchant_type_unique IF NOT EXISTS
FOR (m:Merchant) REQUIRE m.merchant_type IS UNIQUE;

// Step 2: Ingest Transaction Data with Full Property Graph Modeling
LOAD CSV WITH HEADERS FROM 'file:///transactions_dataset.csv' AS row
MERGE (a:Account {account_id: row.customer_account})
MERGE (c:Card {card_no: row.card_no})
MERGE (l:Location {city: row.city})
  ON CREATE SET l.country_code = row.country_code
MERGE (m:Merchant {merchant_type: row.merchant_type})

CREATE (t:Transaction {
  txn_id: row.txn_id,
  txn_datetime: row.txn_datetime,
  txn_amount: toFloat(row.txn_amount),
  txn_currency: row.txn_currency,
  payment_channel: row.payment_channel,
  km_from_home: toFloat(row.km_from_home),
  foreign_txn_flag: toInteger(row.foreign_txn_flag),
  txn_count_past_hour: toInteger(row.txn_count_past_hour),
  fraud_label: row.fraud_label,
  risk_index: toFloat(row.risk_index)
})

MERGE (a)-[:USES_CARD]->(c)
CREATE (a)-[:MADE]->(t)
CREATE (t)-[:OCCURRED_IN]->(l)
CREATE (t)-[:AT_MERCHANT]->(m);

