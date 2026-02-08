# Real-Time Financial Fraud Detection Pipeline

A complete **Kappa Architecture** implementation for real-time fraud detection using modern streaming technologies with cloud database (Supabase PostgreSQL).

##  Architecture

```
┌─────────────┐     ┌───────────┐     ┌─────────────┐     ┌──────────────────┐     ┌───────────┐
│   Generator │────▶│  Redpanda │────▶│   PyFlink   │────▶│    Supabase      │────▶│ Dashboard │
│  (Python)   │     │  (Kafka)  │     │ (Processor) │     │  (PostgreSQL)    │     │ (Next.js) │
└─────────────┘     └───────────┘     └─────────────┘     └──────────────────┘     └───────────┘
                                              │
                                              │ JDBC writes to cloud
                                              ▼
                                      fraud_alerts + transactions
```

##  Project Structure

```
fraud-detection-pipeline/
├── .env                      # Supabase credentials (create from .env.example)
├── infra/                    # Docker Compose infrastructure
│   └── docker-compose.yml
├── generator/                # Synthetic data generator
│   ├── Dockerfile
│   ├── requirements.txt
│   └── producer.py
├── processor/                # PyFlink stream processor
│   ├── Dockerfile
│   ├── requirements.txt
│   └── fraud_detector.py    # JDBC sink to Supabase
├── database/                 # PostgreSQL initialization
│   └── init.sql
└── dashboard/                # Next.js + Tremor frontend
    ├── package.json
    └── src/
        ├── lib/database.ts   # PostgreSQL client
        ├── pages/
        │   ├── index.tsx
        │   └── api/stats.ts
        └── styles/
```

##  Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for dashboard)
- **Supabase account** (free tier works)

### 1. Set Up Supabase

1. **Create a Supabase project**: https://app.supabase.com/
2. **Get your connection details**:
   - Go to Settings → Database
   - Copy the connection string details
3. **Run the database initialization**:
   - Open SQL Editor in Supabase dashboard
   - Copy contents of `database/init.sql`
   - Execute the SQL to create tables and views

### 2. Configure Environment

**Copy the example file:**
```bash
cp .env.example .env
```

**Edit `.env` with your Supabase credentials:**
```env
POSTGRES_HOST=db.xxxxxxxxxxxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_supabase_password
POSTGRES_SSL_MODE=require
JDBC_URL=jdbc:postgresql://db.xxxxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require
```

### 3. Start the Infrastructure

```bash
cd infra
docker compose up -d
```

This starts:
- **Redpanda** (Kafka-compatible) - Port 19092 (external), 9092 (internal)
- **Flink JobManager** - Web UI at http://localhost:8081
- **Flink TaskManager** - Linked to JobManager
- **Generator** - Produces synthetic transactions

> **Note**: The Flink processor (fraud detector) needs to be submitted manually with your Supabase credentials or you can uncomment the `processor` service in `docker-compose.yml` after filling `.env`.

### 4. Submit Flink Job (Manual Option)

If you want to run the processor manually:

```bash
cd processor

# Build the Docker image
docker build -t fraud-processor .

# Run with environment variables from .env
docker run --env-file ../.env --network fraud-net fraud-processor
```

### 5. Start the Dashboard

```bash
cd dashboard
npm install
npm run dev -- -p 3050
```

Open **http://localhost:3050** to view the live dashboard.

##  Fraud Detection Logic

The PyFlink processor implements these fraud detection rules within a **1-minute tumbling window**:

| Rule | Condition | Description |
|------|-----------|-------------|
| High Amount | `total_amount > $3,000` | Unusual spending within window |
| Rapid Fire | `transaction_count > 5` | Too many transactions in short time |

## Data Flow

1. **Generator** produces transactions with:
   - Normal behavior: $10-$100 amounts
   - Fraud patterns: High-value (>$1000) or rapid bursts (6 txns in 10s)

2. **Redpanda** receives transactions on `financial_transactions` topic

3. **PyFlink** processes the stream:
   - Keys by `user_id`
   - Applies 1-minute tumbling windows
   - Aggregates `total_amount` and `transaction_count`
   - Flags fraud based on rules
   - **Writes directly to Supabase via JDBC**

4. **Supabase PostgreSQL** stores:
   - All transactions in `transactions` table
   - Fraud alerts in `fraud_alerts` table

5. **Dashboard** queries Supabase and displays:
   - Fraud count (24h)
   - Total fraud amount
   - Transactions per minute chart
   - Recent fraud alerts

## Configuration

### Environment Variables

**Root `.env` (Supabase credentials):**
- `POSTGRES_HOST`: Supabase host (e.g., `db.xxxxx.supabase.co`)
- `POSTGRES_PORT`: Port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `postgres`)
- `POSTGRES_USER`: Username (default: `postgres`)
- `POSTGRES_PASSWORD`: Your Supabase password
- `JDBC_URL`: Full JDBC connection string

**Generator:**
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `redpanda:9092`)
- `KAFKA_TOPIC`: Output topic (default: `financial_transactions`)

## Monitoring

- **Flink Web UI**: http://localhost:8081
- **Redpanda Admin**: http://localhost:9644
- **Dashboard**: http://localhost:3050
- **Supabase Dashboard**: https://app.supabase.com/project/_/editor

## Verify Data Flow

```bash
# Check Redpanda topics
docker exec -it redpanda rpk topic list

# Query Supabase (use SQL Editor or client)
# SELECT COUNT(*) FROM transactions;
# SELECT * FROM fraud_alerts WHERE is_fraud = 1 LIMIT 10;
```

## Cleanup

```bash
cd infra
docker compose down -v
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Message Broker | Redpanda (Kafka-compatible) |
| Stream Processing | Apache Flink (PyFlink) with JDBC sink |
| Cloud Database | Supabase (PostgreSQL) |
| Data Generation | Python (Faker) |
| Frontend | Next.js + TypeScript |
| Visualization | Tremor React |
| Infrastructure | Docker Compose |

## Why Supabase?

- **Free tier**: Great for development and demos
- **Real-time subscriptions**: Potential for live dashboard updates
- **Managed**: No database ops required
- **Global CDN**: Fast queries worldwide
- **PostgreSQL**: Standard SQL, great tooling


