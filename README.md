# FinGraph Fraud Analytics

A graph database and analytics platform engineered for real-time detection, visualization, and monitoring of financial fraud syndicates using Neo4j, Apache Kafka, FastAPI, and React.

---

## 🚀 Key Architecture & Components

- **Graph Database (Neo4j):** Models transactions, accounts, cards, locations, and merchants as a property graph with indexed constraints and multi-hop pattern matching.
- **Event Streaming (Apache Kafka):** High-throughput producer (producer.py) and consumer (consumer.py) simulating real-time transaction streaming and direct graph ingestion.
- **Backend API (FastAPI):** High-performance analytical REST endpoints providing fraud risk summaries, circular flow diagnostics, and account investigation details.
- **Frontend Dashboard (React + Vite):** Interactive risk monitoring, visual network exploration, and alert triage.

---

## 🛠️ Quick Start Guide

### 1. Start Infrastructure (Docker Compose)
Start Kafka, Zookeeper, and Neo4j:
`ash
docker-compose up -d
`
Neo4j Browser will be accessible at: http://localhost:7474 (Bolt: olt://localhost:7687)

### 2. Configure Environment
Copy .env.example to .env and set your credentials:
`ash
cp .env.example .env
`

### 3. Load Neo4j Graph Dataset
Execute import_script.cypher in the Neo4j Browser to apply schema constraints and import historical transactions from 	ransactions_dataset.csv.

### 4. Real-Time Streaming Ingestion
Run the Kafka consumer to listen and write to Neo4j:
`ash
python consumer.py
`
In a separate terminal, trigger transaction streaming:
`ash
python producer.py
`

### 5. Launch FastAPI Backend
`ash
uvicorn app.main:app --reload --port 8000
`
Interactive Swagger docs: http://localhost:8000/docs

### 6. Launch Frontend Dashboard
`ash
cd fingraph-frontend
npm install
npm run dev
`
Dashboard will run on http://localhost:5173.
