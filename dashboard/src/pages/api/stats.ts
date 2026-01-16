/**
 * API Route: /api/stats
 * 
 * Fetches real-time fraud detection metrics from Supabase PostgreSQL
 * for the dashboard visualization.
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import {
	queryDatabase,
	FraudStats24h,
	TransactionPerMinute,
	RecentAlert,
} from '@/lib/database';

interface StatsResponse {
	fraudStats: FraudStats24h | null;
	transactionsPerMinute: TransactionPerMinute[];
	recentAlerts: RecentAlert[];
	timestamp: string;
	error?: string;
}

export default async function handler(
	req: NextApiRequest,
	res: NextApiResponse<StatsResponse>
) {
	if (req.method !== 'GET') {
		return res.status(405).json({
			fraudStats: null,
			transactionsPerMinute: [],
			recentAlerts: [],
			timestamp: new Date().toISOString(),
			error: 'Method not allowed',
		});
	}

	try {
		// Query 1: Fraud stats for last 24 hours
		const fraudStatsQuery = `
      SELECT
        COUNT(*) AS total_alerts,
        COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_count,
        COALESCE(SUM(total_amount) FILTER (WHERE is_fraud = 1), 0) AS fraud_total_amount,
        COUNT(DISTINCT user_id) AS unique_users_flagged
      FROM fraud_alerts
      WHERE window_end >= NOW() - INTERVAL '24 hours'
    `;

		// Query 2: Transactions per minute (last hour)
		const transactionsPerMinuteQuery = `
      SELECT
        DATE_TRUNC('minute', timestamp) AS minute,
        COUNT(*) AS transaction_count,
        COALESCE(SUM(amount), 0) AS total_volume,
        COALESCE(AVG(amount), 0) AS avg_amount
      FROM transactions
      WHERE timestamp >= NOW() - INTERVAL '1 hour'
      GROUP BY DATE_TRUNC('minute', timestamp)
      ORDER BY minute ASC
    `;

		// Query 3: Recent fraud alerts (last 20)
		const recentAlertsQuery = `
      SELECT
        user_id,
        window_end,
        transaction_count,
        total_amount,
        alert_reason
      FROM fraud_alerts
      WHERE is_fraud = 1
      ORDER BY window_end DESC
      LIMIT 20
    `;

		// Execute queries in parallel
		const [fraudStats, transactionsPerMinute, recentAlerts] = await Promise.all([
			queryDatabase<FraudStats24h>(fraudStatsQuery),
			queryDatabase<TransactionPerMinute>(transactionsPerMinuteQuery),
			queryDatabase<RecentAlert>(recentAlertsQuery),
		]);

		return res.status(200).json({
			fraudStats: fraudStats[0] || null,
			transactionsPerMinute,
			recentAlerts,
			timestamp: new Date().toISOString(),
		});
	} catch (error) {
		console.error('Error fetching stats from PostgreSQL:', error);

		// Return empty data with error message
		return res.status(500).json({
			fraudStats: null,
			transactionsPerMinute: [],
			recentAlerts: [],
			timestamp: new Date().toISOString(),
			error: error instanceof Error ? error.message : 'Failed to fetch statistics',
		});
	}
}
