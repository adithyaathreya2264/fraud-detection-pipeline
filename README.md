# 🏦 Real-Time Financial Fraud Detection Pipeline

A complete **Kappa Architecture** implementation for real-time fraud detection using modern streaming technologies.

## 🏗️ Architecture

```
┌─────────────┐     ┌───────────┐     ┌─────────────┐     ┌────────────┐     ┌───────────┐
│   Generator │────▶│  Redpanda │────▶│   PyFlink   │────▶│ ClickHouse │────▶│ Dashboard │
│  (Python)   │     │  (Kafka)  │     │ (Processor) │     │   (OLAP)   │     │ (Next.js) │
└─────────────┘     └───────────┘     └─────────────┘     └────────────┘     └───────────┘
                         │                   │
                         │                   │
                         └───────────────────┘
                           fraud_alerts topic
```

## 📁 Project Structure

```
fraud-detection-pipeline/
├── infra/                    # Docker Compose infrastructure
│   └── docker-compose.yml
├── generator/                # Synthetic data generator
│   ├── Dockerfile
│   ├── requirements.txt
│   └── producer.py
├── processor/                # PyFlink stream processor
│   ├── Dockerfile
│   ├── requirements.txt
│   └── fraud_detector.py
├── database/                 # ClickHouse initialization
│   └── init.sql
└── dashboard/                # Next.js + Tremor frontend
    ├── package.json
    ├── .env.local
    └── src/
        ├── lib/clickhouse.ts
        ├── pages/
        │   ├── index.tsx
        │   └── api/stats.ts
        └── styles/
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for dashboard development)
- Python 3.11+ (optional, for local testing)

### 1. Start the Infrastructure

```bash
cd infra
docker-compose up -d
```

This starts:
- **Redpanda** (Kafka-compatible) - Port 19092 (external), 9092 (internal)
- **Flink JobManager** - Web UI at http://localhost:8081
- **Flink TaskManager** - Linked to JobManager
- **ClickHouse** - HTTP port 8123, Native port 9000
- **Generator** - Produces synthetic transactions

### 2. Verify Services

```bash
# Check all containers are running
docker-compose ps

# View Redpanda topics
docker exec -it redpanda rpk topic list

# Check ClickHouse
docker exec -it clickhouse clickhouse-client --query "SELECT count() FROM fraud_detection.transactions"
```

### 3. Start the Dashboard

```bash
cd dashboard
npm install
npm run dev -- -p 3050
```

Open http://localhost:3050 to view the live dashboard.

## 🔍 Fraud Detection Logic

The PyFlink processor implements these fraud detection rules within a **1-minute tumbling window**:

| Rule | Condition | Description |
|------|-----------|-------------|
| 🚨 High Amount | `total_amount > $3,000` | Unusual spending within window |
| 🚨 Rapid Fire | `transaction_count > 5` | Too many transactions in short time |

## 📊 Data Flow

1. **Generator** produces transactions with:
   - Normal behavior: $10-$100 amounts
   - Fraud patterns: High-value (>$1000) or rapid bursts (6 txns in 10s)

2. **Redpanda** receives transactions on `financial_transactions` topic

3. **PyFlink** processes the stream:
   - Keys by `user_id`
   - Applies 1-minute tumbling windows
   - Aggregates `total_amount` and `transaction_count`
   - Flags fraud based on rules
   - Outputs to `fraud_alerts` topic

4. **ClickHouse** ingests from both topics via Kafka Engine tables

5. **Dashboard** queries ClickHouse and displays:
   - Fraud count (24h)
   - Total fraud amount
   - Transactions per minute chart
   - Recent fraud alerts

## 🛠️ Configuration

### Environment Variables

**Generator:**
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `redpanda:9092`)
- `KAFKA_TOPIC`: Output topic (default: `financial_transactions`)

**Dashboard (.env.local):**
- `CLICKHOUSE_HOST`: ClickHouse host (default: `localhost`)
- `CLICKHOUSE_PORT`: HTTP port (default: `8123`)
- `CLICKHOUSE_DATABASE`: Database name (default: `fraud_detection`)
- `CLICKHOUSE_USER`: Username (default: `default`)
- `CLICKHOUSE_PASSWORD`: Password (default: empty)

## 📈 Monitoring

- **Flink Web UI**: http://localhost:8081
- **Redpanda Admin**: http://localhost:9644
- **Dashboard**: http://localhost:3050

## 🧹 Cleanup

```bash
cd infra
docker-compose down -v
```

## 📚 Tech Stack

| Component | Technology |
|-----------|------------|
| Message Broker | Redpanda (Kafka-compatible) |
| Stream Processing | Apache Flink (PyFlink) |
| OLAP Database | ClickHouse |
| Data Generation | Python (Faker) |
| Frontend | Next.js + TypeScript |
| Visualization | Tremor React |
| Infrastructure | Docker Compose |

## 📝 License

MIT
