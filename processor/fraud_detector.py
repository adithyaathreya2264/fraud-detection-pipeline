#!/usr/bin/env python3
"""
Real-Time Fraud Detection using PyFlink with PostgreSQL (Supabase) Sink

This Flink job performs stateful stream processing on financial transactions:
1. Reads transactions from Redpanda topic 'financial_transactions'
2. Keys the stream by user_id
3. Applies a 1-minute tumbling window
4. Detects fraud based on:
   - Total amount > $3000 in window
   - Transaction count > 5 in window
5. Outputs results directly to Supabase PostgreSQL via JDBC
"""

import json
import os
from datetime import datetime

from pyflink.common import WatermarkStrategy, Types, Row
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaOffsetsInitializer,
)
from pyflink.datastream.connectors.jdbc import JdbcSink, JdbcConnectionOptions, JdbcExecutionOptions
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common.time import Time
from pyflink.common.typeinfo import Types as T
from pyflink.datastream.functions import ProcessWindowFunction

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "financial_transactions")

# PostgreSQL (Supabase) Configuration
JDBC_URL = os.getenv("JDBC_URL", "jdbc:postgresql://localhost:5432/postgres")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# Fraud detection thresholds
AMOUNT_THRESHOLD = 3000.0
COUNT_THRESHOLD = 5
WINDOW_SIZE_MINUTES = 1


class TransactionAggregator(ProcessWindowFunction):
    """
    Aggregates transactions per user in tumbling windows
    and writes both to PostgreSQL tables.
    """

    def process(self, key, context, elements):
        """Process all transactions in the window for a single user."""
        transactions = list(elements)
        
        # Aggregate statistics
        transaction_count = len(transactions)
        total_amount = sum(float(t.get("amount", 0)) for t in transactions)
        
        # Window timing
        window = context.window()
        window_start = window.start
        window_end = window.end
        
        # Apply fraud detection rules
        is_fraud = False
        alert_reasons = []
        
        if total_amount > AMOUNT_THRESHOLD:
            is_fraud = True
            alert_reasons.append(f"High total amount: ${total_amount:.2f}")
        
        if transaction_count > COUNT_THRESHOLD:
            is_fraud = True
            alert_reasons.append(f"High transaction count: {transaction_count}")
        
        alert_reason = "; ".join(alert_reasons) if alert_reasons else "Normal activity"
        
        # Log fraud alerts
        if is_fraud:
            print(f"🚨 FRAUD ALERT: User {key} - {alert_reason}")
        
        # Yield both transaction records and fraud alert
        # Format: (user_id, amount, city, merchant_category, timestamp, window_start, window_end, 
        #          transaction_count, total_amount, is_fraud, alert_reason)
        for txn in transactions:
            yield Row(
                user_id=key,
                amount=float(txn.get("amount", 0)),
                city=txn.get("city", ""),
                merchant_category=txn.get("merchant_category", ""),
                timestamp=txn.get("timestamp", 0),
                window_start=window_start,
                window_end=window_end,
                transaction_count=transaction_count,
                total_amount=total_amount,
                is_fraud=1 if is_fraud else 0,
                alert_reason=alert_reason
            )


def parse_transaction(value: str) -> dict:
    """Parse JSON transaction from Kafka."""
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"Failed to parse transaction: {e}")
        return None


def main():
    print("=" * 60)
    print("🔍 Real-Time Fraud Detection Pipeline (Supabase)")
    print("=" * 60)
    print(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Input Topic: {INPUT_TOPIC}")
    print(f"PostgreSQL: {JDBC_URL}")
    print(f"Window Size: {WINDOW_SIZE_MINUTES} minute(s)")
    print(f"Amount Threshold: ${AMOUNT_THRESHOLD}")
    print(f"Count Threshold: {COUNT_THRESHOLD}")
    print("=" * 60)

    # Create execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)
    
    # Enable checkpointing
    env.enable_checkpointing(60000)

    # Configure Kafka source
    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_topics(INPUT_TOPIC)
        .set_group_id("flink-fraud-detector-supabase")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    # JDBC Sink for transactions table
    jdbc_transactions_sink = JdbcSink.sink(
        """
        INSERT INTO transactions (transaction_id, user_id, timestamp, amount, currency, city, merchant_category)
        VALUES (gen_random_uuid(), ?, to_timestamp(? / 1000.0), ?, 'USD', ?, ?)
        ON CONFLICT (transaction_id) DO NOTHING
        """,
        T.ROW([
            T.INT(),      # user_id
            T.LONG(),     # timestamp (epoch ms)
            T.DOUBLE(),   # amount
            T.STRING(),   # city
            T.STRING(),   # merchant_category
        ]),
        JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .with_url(JDBC_URL)
        .with_driver_name("org.postgresql.Driver")
        .with_user_name(POSTGRES_USER)
        .with_password(POSTGRES_PASSWORD)
        .build(),
        JdbcExecutionOptions.builder()
        .with_batch_size(100)
        .with_batch_interval_ms(1000)
        .with_max_retries(3)
        .build()
    )

    # JDBC Sink for fraud alerts table
    jdbc_alerts_sink = JdbcSink.sink(
        """
        INSERT INTO fraud_alerts (user_id, window_start, window_end, transaction_count, total_amount, is_fraud, alert_reason)
        VALUES (?, to_timestamp(? / 1000.0), to_timestamp(? / 1000.0), ?, ?, ?, ?)
        ON CONFLICT (user_id, window_end) DO UPDATE SET
            transaction_count = EXCLUDED.transaction_count,
            total_amount = EXCLUDED.total_amount,
            is_fraud = EXCLUDED.is_fraud,
            alert_reason = EXCLUDED.alert_reason
        """,
        T.ROW([
            T.INT(),      # user_id
            T.LONG(),     # window_start
            T.LONG(),     # window_end
            T.INT(),      # transaction_count
            T.DOUBLE(),   # total_amount
            T.INT(),      # is_fraud
            T.STRING(),   # alert_reason
        ]),
        JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .with_url(JDBC_URL)
        .with_driver_name("org.postgresql.Driver")
        .with_user_name(POSTGRES_USER)
        .with_password(POSTGRES_PASSWORD)
        .build(),
        JdbcExecutionOptions.builder()
        .with_batch_size(50)
        .with_batch_interval_ms(2000)
        .with_max_retries(3)
        .build()
    )

    # Build the processing pipeline
    stream = (
        env.from_source(
            kafka_source,
            WatermarkStrategy.no_watermarks(),
            "Kafka Source"
        )
        .map(parse_transaction, output_type=Types.PICKLED_BYTE_ARRAY())
        .filter(lambda x: x is not None)
        .key_by(lambda x: x["user_id"])
        .window(TumblingProcessingTimeWindows.of(Time.minutes(WINDOW_SIZE_MINUTES)))
        .process(TransactionAggregator())
    )

    # Write transactions
    stream.map(
        lambda row: Row(
            user_id=row.user_id,
            timestamp=row.timestamp,
            amount=row.amount,
            city=row.city,
            merchant_category=row.merchant_category
        ),
        output_type=T.ROW([T.INT(), T.LONG(), T.DOUBLE(), T.STRING(), T.STRING()])
    ).add_sink(jdbc_transactions_sink).name("PostgreSQL Transactions Sink")

    # Write fraud alerts (only one per window)
    stream.key_by(lambda row: (row.user_id, row.window_end)).map(
        lambda row: Row(
            user_id=row.user_id,
            window_start=row.window_start,
            window_end=row.window_end,
            transaction_count=row.transaction_count,
            total_amount=row.total_amount,
            is_fraud=row.is_fraud,
            alert_reason=row.alert_reason
        ),
        output_type=T.ROW([T.INT(), T.LONG(), T.LONG(), T.INT(), T.DOUBLE(), T.INT(), T.STRING()])
    ).add_sink(jdbc_alerts_sink).name("PostgreSQL Alerts Sink")

    # Execute
    print("🚀 Starting Flink job with Supabase PostgreSQL sink...")
    env.execute("Fraud Detection Pipeline (Supabase)")


if __name__ == "__main__":
    main()
