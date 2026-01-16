/**
 * ClickHouse Client Configuration
 * 
 * Initializes and exports a ClickHouse client instance
 * for querying real-time fraud detection data.
 */

import { createClient, ClickHouseClient } from '@clickhouse/client';

// Singleton client instance
let client: ClickHouseClient | null = null;

/**
 * Get or create a ClickHouse client instance
 */
export function getClickHouseClient(): ClickHouseClient {
	if (!client) {
		client = createClient({
			url: `http://${process.env.CLICKHOUSE_HOST || 'localhost'}:${process.env.CLICKHOUSE_PORT || '8123'}`,
			database: process.env.CLICKHOUSE_DATABASE || 'fraud_detection',
			username: process.env.CLICKHOUSE_USER || 'default',
			password: process.env.CLICKHOUSE_PASSWORD || '',
		});
	}
	return client;
}

/**
 * Execute a query and return results as JSON
 */
export async function queryClickHouse<T>(query: string): Promise<T[]> {
	const clickhouse = getClickHouseClient();
	const result = await clickhouse.query({
		query,
		format: 'JSONEachRow',
	});
	return result.json<T>();
}

/**
 * Fraud statistics for the last 24 hours
 */
export interface FraudStats24h {
	total_alerts: number;
	fraud_count: number;
	fraud_total_amount: number;
	unique_users_flagged: number;
}

/**
 * Transaction per minute data for charts
 */
export interface TransactionPerMinute {
	minute: string;
	transaction_count: number;
	total_volume: number;
	avg_amount: number;
}

/**
 * Recent fraud alert
 */
export interface RecentAlert {
	user_id: number;
	window_end: string;
	transaction_count: number;
	total_amount: number;
	alert_reason: string;
}

/**
 * Fraud by city statistics
 */
export interface FraudByCity {
	city: string;
	fraud_count: number;
	total_fraud_amount: number;
}
