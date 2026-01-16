/**
 * PostgreSQL (Supabase) Client Configuration
 * 
 * Initializes and exports a PostgreSQL connection pool
 * for querying real-time fraud detection data.
 */

import { Pool, QueryResult } from 'pg';

// Singleton pool instance
let pool: Pool | null = null;

/**
 * Get or create a PostgreSQL connection pool
 */
export function getDatabasePool(): Pool {
	if (!pool) {
		pool = new Pool({
			host: process.env.POSTGRES_HOST || 'localhost',
			port: parseInt(process.env.POSTGRES_PORT || '5432'),
			database: process.env.POSTGRES_DB || 'postgres',
			user: process.env.POSTGRES_USER || 'postgres',
			password: process.env.POSTGRES_PASSWORD || '',
			ssl: process.env.POSTGRES_SSL_MODE === 'require' ? { rejectUnauthorized: false } : false,
			max: 20, // Maximum pool size
			idleTimeoutMillis: 30000,
			connectionTimeoutMillis: 10000,
		});

		// Log connection errors
		pool.on('error', (err: Error) => {
			console.error('Unexpected PostgreSQL pool error:', err);
		});
	}
	return pool;
}

/**
 * Execute a query and return results
 */
export async function queryDatabase<T>(query: string, params: any[] = []): Promise<T[]> {
	const client = getDatabasePool();
	const result: QueryResult = await client.query(query, params);
	return result.rows as T[];
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
