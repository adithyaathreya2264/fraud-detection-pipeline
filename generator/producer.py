#!/usr/bin/env python3
"""
Real-Time Financial Transaction Generator

Generates synthetic credit card transactions and publishes them to Redpanda/Kafka.
Includes both normal transactions and fraud patterns for testing.
"""

import json
import os
import random
import time
import uuid
from datetime import datetime, timezone

from faker import Faker
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:19092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "financial_transactions")

# Initialize Faker
fake = Faker()

# User profiles for consistent fraud patterns
# Some users are "normal", some are "potential fraudsters"
FRAUD_USER_IDS = [42, 137, 256, 500, 777]  # Users that will exhibit fraud patterns
NORMAL_USER_RANGE = (1, 1000)

# Transaction timing
BASE_DELAY_MS = 100  # Base delay between transactions (100ms = 10 TPS average)
FRAUD_BURST_COUNT = 6  # Number of rapid transactions in a fraud burst
FRAUD_BURST_DELAY_MS = 1500  # Delay between burst transactions (1.5 seconds)


def create_producer() -> KafkaProducer:
    """Create Kafka producer with retry logic."""
    max_retries = 30
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
            )
            print(f"✅ Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return producer
        except NoBrokersAvailable:
            print(
                f"⏳ Waiting for Kafka brokers... (attempt {attempt + 1}/{max_retries})"
            )
            time.sleep(retry_delay)

    raise Exception(f"Failed to connect to Kafka after {max_retries} attempts")


def generate_normal_transaction(user_id: int) -> dict:
    """Generate a normal transaction (amount < $100)."""
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),  # Epoch ms
        "amount": round(random.uniform(10.00, 99.99), 2),
        "currency": "USD",
        "city": fake.city(),
        "merchant_category": random.choice(
            ["grocery", "restaurant", "gas_station", "retail", "online"]
        ),
    }


def generate_high_value_transaction(user_id: int) -> dict:
    """Generate a high-value transaction (amount > $1000) - potential fraud."""
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
        "amount": round(random.uniform(1000.00, 5000.00), 2),
        "currency": "USD",
        "city": fake.city(),
        "merchant_category": random.choice(["luxury", "electronics", "jewelry"]),
    }


def generate_fraud_burst(producer: KafkaProducer, user_id: int):
    """
    Generate a burst of rapid-fire transactions for a user.
    This simulates a stolen card being used multiple times quickly.
    """
    print(f"🚨 Generating fraud burst for user {user_id}...")

    for i in range(FRAUD_BURST_COUNT):
        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
            "amount": round(random.uniform(200.00, 800.00), 2),
            "currency": "USD",
            "city": fake.city(),
            "merchant_category": random.choice(["atm", "online", "electronics"]),
        }

        producer.send(
            KAFKA_TOPIC, key=str(user_id), value=transaction
        )

        print(
            f"  📤 Burst {i + 1}/{FRAUD_BURST_COUNT}: "
            f"User {user_id} - ${transaction['amount']:.2f}"
        )

        time.sleep(FRAUD_BURST_DELAY_MS / 1000)

    producer.flush()


def main():
    """Main loop for generating transactions."""
    print("=" * 60)
    print("🏦 Financial Transaction Generator")
    print("=" * 60)
    print(f"Kafka Brokers: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"Topic: {KAFKA_TOPIC}")
    print(f"Fraud User IDs: {FRAUD_USER_IDS}")
    print("=" * 60)

    producer = create_producer()

    transaction_count = 0
    fraud_high_value_count = 0
    fraud_burst_count = 0

    try:
        while True:
            # Decide transaction type (weighted random)
            transaction_type = random.choices(
                ["normal", "high_value_fraud", "burst_fraud"],
                weights=[0.92, 0.05, 0.03],  # 92% normal, 5% high value, 3% burst
                k=1,
            )[0]

            if transaction_type == "normal":
                # Normal transaction for random user
                user_id = random.randint(*NORMAL_USER_RANGE)
                transaction = generate_normal_transaction(user_id)

                producer.send(
                    KAFKA_TOPIC, key=str(user_id), value=transaction
                )

                transaction_count += 1

                if transaction_count % 100 == 0:
                    print(
                        f"📊 Stats: {transaction_count} total, "
                        f"{fraud_high_value_count} high-value, "
                        f"{fraud_burst_count} bursts"
                    )

                # Random delay for natural traffic pattern
                delay = random.uniform(
                    BASE_DELAY_MS * 0.5, BASE_DELAY_MS * 2.0
                ) / 1000
                time.sleep(delay)

            elif transaction_type == "high_value_fraud":
                # High-value transaction from a known fraud user
                user_id = random.choice(FRAUD_USER_IDS)
                transaction = generate_high_value_transaction(user_id)

                producer.send(
                    KAFKA_TOPIC, key=str(user_id), value=transaction
                )

                fraud_high_value_count += 1
                transaction_count += 1

                print(
                    f"💰 HIGH VALUE: User {user_id} - ${transaction['amount']:.2f} "
                    f"in {transaction['city']}"
                )

                time.sleep(BASE_DELAY_MS / 1000)

            elif transaction_type == "burst_fraud":
                # Rapid-fire burst from a fraud user
                user_id = random.choice(FRAUD_USER_IDS)
                generate_fraud_burst(producer, user_id)

                fraud_burst_count += 1
                transaction_count += FRAUD_BURST_COUNT

            # Flush periodically
            if transaction_count % 50 == 0:
                producer.flush()

    except KeyboardInterrupt:
        print("\n⚠️ Shutting down generator...")
    finally:
        producer.flush()
        producer.close()
        print(f"✅ Generator stopped. Total transactions: {transaction_count}")


if __name__ == "__main__":
    main()
