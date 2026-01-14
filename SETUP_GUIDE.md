# 🚀 Complete Setup Guide - Fraud Detection Pipeline

## Prerequisites Checklist

Before running the pipeline, ensure you have:

- [ ] **Docker Desktop** installed and running
- [ ] **Node.js 18+** installed
- [ ] **Supabase account** created
- [ ] **Database tables** created in Supabase
- [ ] **`.env` file** filled with your credentials

---

## Step-by-Step Setup

### 1️⃣ Install Docker Desktop

**Download & Install:**
- Windows: https://www.docker.com/products/docker-desktop/
- Install and restart your computer
- Launch Docker Desktop and wait until it shows "Engine running"

**Verify installation:**
```powershell
docker --version
# Should show: Docker version XX.XX.XX
```

---

### 2️⃣ Set Up Supabase Database

**Create Project:**
1. Go to https://app.supabase.com/
2. Click "New Project"
3. Choose a name, set a password (SAVE THIS!)
4. Wait for project to initialize (~2 minutes)

**Get Credentials:**
1. Go to **Settings → Database**
2. Scroll to "Connection string"
3. Copy the values shown

**Initialize Database:**
1. Go to **SQL Editor**: https://app.supabase.com/project/_/sql/new
2. Open `database/init.sql` from your project
3. Copy ALL contents
4. Paste in SQL Editor
5. Click "Run" or press Ctrl+Enter
6. Verify: Should see "Success. No rows returned"
7. Go to **Table Editor** - you should see `transactions` and `fraud_alerts` tables

---

### 3️⃣ Configure Environment Variables

**Edit `.env` file in project root:**

Replace these values with your Supabase credentials:

```env
POSTGRES_HOST=db.xxxxxxxxxxxxxx.supabase.co      ← Replace with YOUR host
POSTGRES_PORT=5432                                ← Keep as-is
POSTGRES_DB=postgres                              ← Keep as-is
POSTGRES_USER=postgres                            ← Keep as-is
POSTGRES_PASSWORD=your_supabase_password          ← YOUR password
POSTGRES_SSL_MODE=require                         ← Keep as-is

JDBC_URL=jdbc:postgresql://db.xxxxxxxxxxxxxx.supabase.co:5432/postgres?sslmode=require
                         ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                         Update this host to match POSTGRES_HOST
```

**Save the file!**

---

### 4️⃣ Start Infrastructure Services

**Navigate to infra folder:**
```powershell
cd e:\Personal_Projects\fraud-detection-pipeline\infra
```

**Start all services:**
```powershell
docker compose up -d
```

**What this starts:**
- Redpanda (Kafka message broker)
- Flink JobManager (stream processing master)
- Flink TaskManager (stream processing worker)
- Generator (creates fake transactions)

**Verify services:**
```powershell
docker compose ps
```

You should see 4 containers running:
- ✅ redpanda
- ✅ flink-jobmanager
- ✅ flink-taskmanager
- ✅ generator

**Check logs:**
```powershell
# See transaction generation
docker logs generator --follow

# Press Ctrl+C to stop watching
```

---

### 5️⃣ Build and Run Flink Processor

This component reads from Kafka and writes to Supabase.

**Navigate to processor folder:**
```powershell
cd e:\Personal_Projects\fraud-detection-pipeline\processor
```

**Build Docker image:**
```powershell
docker build -t fraud-processor .
```

This takes ~2-3 minutes to download dependencies.

**Run the processor:**
```powershell
docker run -d `
  --name processor `
  --env-file ..\.env `
  --network infra_fraud-net `
  fraud-processor
```

**Check it's running:**
```powershell
docker logs processor --follow
```

You should see:
```
🔍 Real-Time Fraud Detection Pipeline (Supabase)
====================================
Kafka: redpanda:9092
PostgreSQL: jdbc:postgresql://...
🚀 Starting Flink job...
```

Look for fraud alerts:
```
🚨 FRAUD ALERT: User 42 - High total amount: $3500.00
```

---

### 6️⃣ Start the Dashboard

**Navigate to dashboard folder:**
```powershell
cd e:\Personal_Projects\fraud-detection-pipeline\dashboard
```

**Install dependencies (first time only):**
```powershell
npm install
```

**Start development server:**
```powershell
npm run dev -- -p 3050
```

**Open in browser:**
http://localhost:3050

You should see:
- 📊 KPI cards showing fraud statistics
- 📈 Transaction chart (may be empty initially)
- 🚨 Recent fraud alerts list

**Wait 1-2 minutes** for data to flow through the pipeline and appear in the dashboard.

---

## 🔍 Verification & Troubleshooting

### Check Docker Containers
```powershell
docker ps
```
Should show 5 containers:
- redpanda
- flink-jobmanager
- flink-taskmanager
- generator
- processor

### Check Kafka Topics
```powershell
docker exec -it redpanda rpk topic list
```
Should show: `financial_transactions`

### Check Data in Supabase

Go to Supabase **SQL Editor** and run:

```sql
-- Check transactions
SELECT COUNT(*) FROM transactions;

-- Check fraud alerts
SELECT * FROM fraud_alerts WHERE is_fraud = 1 ORDER BY window_end DESC LIMIT 10;

-- View analytics
SELECT * FROM fraud_stats_24h;
```

### Check Flink Web UI

Open: http://localhost:8081

- Go to "Running Jobs"
- Should see "Fraud Detection Pipeline (Supabase)"
- Check metrics: records sent, checkpoints

### Common Issues

**"Cannot connect to Docker daemon"**
- Solution: Start Docker Desktop and wait for it to fully initialize

**"Port already in use"**
- Solution: Stop conflicting services or change ports in docker-compose.yml

**"Database connection failed"**
- Solution: Verify `.env` credentials match Supabase dashboard
- Check Supabase project is active (not paused)

**"No fraud alerts appearing"**
- Solution: Wait 1-2 minutes for data to accumulate
- Check generator logs: `docker logs generator`
- Verify fraud patterns are being generated

---

## 🛑 Stopping Everything

**Stop all Docker services:**
```powershell
cd e:\Personal_Projects\fraud-detection-pipeline\infra
docker compose down
```

**Stop processor:**
```powershell
docker stop processor
docker rm processor
```

**Stop dashboard:**
- Press `Ctrl+C` in the terminal running npm

---

## 📊 Expected Results

After 1-2 minutes, you should see:

**In Dashboard:**
- Fraud Detected (24h): 5-15 alerts
- Total fraud amount: $5,000 - $20,000
- Transactions per minute: Growing chart
- Recent alerts: List of flagged users

**In Supabase (SQL Editor):**
```sql
SELECT COUNT(*) FROM transactions;
-- Should show: 100+ transactions

SELECT COUNT(*) FROM fraud_alerts WHERE is_fraud = 1;
-- Should show: 5+ fraud alerts
```

**In Generator Logs:**
```
💰 HIGH VALUE: User 42 - $1250.00 in New York
🚨 Generating fraud burst for user 137...
📊 Stats: 500 total, 12 high-value, 3 bursts
```

**In Processor Logs:**
```
🚨 FRAUD ALERT: User 42 - High total amount: $3200.00
🚨 FRAUD ALERT: User 137 - High transaction count: 6
```

---

## ✅ Success Checklist

- [ ] Docker Desktop installed and running
- [ ] All 5 containers running (`docker ps`)
- [ ] Supabase tables created and contain data
- [ ] Dashboard accessible at http://localhost:3050
- [ ] KPI cards showing non-zero values
- [ ] Transaction chart displaying data
- [ ] Fraud alerts appearing in the list

---

## 🎉 You're Done!

The pipeline is now running end-to-end:

```
Generator → Redpanda → Flink → Supabase → Dashboard
   ↓           ↓          ↓         ↓          ↓
 Fake      Streaming   Fraud    Cloud DB    Live
 Txns      Messages   Detect    Storage     Viz
```

Enjoy monitoring real-time fraud detection! 🚀
