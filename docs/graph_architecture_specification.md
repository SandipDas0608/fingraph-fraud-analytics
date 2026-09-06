# FinGraph Graph Architecture & Data Engineering Specifications

**Author:** shubhamgawari9226  
**Component:** Graph Schema, Streaming Ingestion & Real-Time Analytics  

---

## 1. Architectural Overview

The FinGraph architecture is structured into three operational tiers:

`
[ Financial Transactions Stream ]
               │
               ▼
       [ Apache Kafka ]
         (Topic: financial-transactions)
               │
       ┌───────┴───────┐
       ▼               ▼
[ Python Ingestion ]  [ Risk Flagging Engine ]
 (consumer.py)          (Real-time Thresholds)
       │
       ▼
 [ Neo4j Graph Cluster ]
   - Account Nodes
   - Card Nodes
   - Transaction Nodes
   - Location & Merchant Nodes
   - Multi-hop Pattern Matching (Cycles, Mules, Shared Cards)
       │
       ▼
  [ FastAPI Backend ]
   - Graph Analytics Endpoints
   - Risk Distribution
   - Account Investigation
`

---

## 2. Graph Node & Relationship Schema

### Node Labels and Constraints

| Label | Primary Key / Constraint | Indexed Properties | Key Properties |
|---|---|---|---|
| :Account | ccount_id IS UNIQUE | isk_score, isk_tier | ccount_id, isk_score, isk_tier |
| :Card | card_no IS UNIQUE | - | card_no |
| :Transaction | 	xn_id IS UNIQUE | isk_index, 	xn_datetime, raud_label | 	xn_id, 	xn_amount, 	xn_currency, payment_channel, isk_index, raud_label |
| :Location | city IS UNIQUE | country_code | city, country_code |
| :Merchant | merchant_type IS UNIQUE | - | merchant_type |

### Relationships

- (:Account)-[:USES_CARD]->(:Card)
- (:Account)-[:MADE]->(:Transaction)
- (:Transaction)-[:OCCURRED_IN]->(:Location)
- (:Transaction)-[:AT_MERCHANT]->(:Merchant)
- (:Account)-[:TRANSFERRED_TO]->(:Account) (Direct funds routing / circular flow)

---

## 3. Real-Time Streaming Ingestion Pipeline

The real-time streaming pipeline comprises:
1. **Producer (producer.py):** Replays transactions to Kafka topic inancial-transactions.
2. **Consumer (consumer.py):** Consumes JSON transaction payloads, validates schema headers, and executes atomic Cypher transactions using parameter maps to construct graph topology without Cypher injection vulnerabilities.

---

## 4. Graph Algorithms & Fraud Patterns

- **Circular Flow Detection:** Path traversals of length  \in [3, 5]$ detecting money laundering layering loops.
- **Card Reuse / Mule Detection:** Identifies multiple account nodes linked to the same card node or geographic anomalies.
- **Risk Score Aggregation:** Aggregates transaction-level isk_index into account-level composite risk scores.
