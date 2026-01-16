/**
 * Real-Time Financial Fraud Detection Dashboard
 * 
 * Displays live fraud detection metrics using Tremor visualization components.
 * Auto-refreshes every 5 seconds for real-time updates.
 */

import { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import {
  Card,
  Title,
  Text,
  Metric,
  Flex,
  Grid,
  LineChart,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Badge,
  ProgressBar,
} from '@tremor/react';
import styles from '@/styles/Home.module.css';

// Types matching API response
interface FraudStats {
  total_alerts: number;
  fraud_count: number;
  fraud_total_amount: number;
  unique_users_flagged: number;
}

interface TransactionPerMinute {
  minute: string;
  transaction_count: number;
  total_volume: number;
  avg_amount: number;
}

interface RecentAlert {
  user_id: number;
  window_end: string;
  transaction_count: number;
  total_amount: number;
  alert_reason: string;
}

interface StatsResponse {
  fraudStats: FraudStats | null;
  transactionsPerMinute: TransactionPerMinute[];
  recentAlerts: RecentAlert[];
  timestamp: string;
  error?: string;
}

// Refresh interval in milliseconds
const REFRESH_INTERVAL = 5000;

export default function Dashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: StatsResponse = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setError(null);
        setStats(data);
        setLastUpdate(new Date());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchStats]);

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  // Format timestamp
  const formatTime = (timestamp: string): string => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Transform chart data
  const chartData = stats?.transactionsPerMinute.map((item) => ({
    time: formatTime(item.minute),
    'Transactions': item.transaction_count,
    'Volume ($)': Math.round(Number(item.total_volume)),
  })) || [];

  return (
    <>
      <Head>
        <title>Fraud Detection Dashboard</title>
        <meta name="description" content="Real-time financial fraud detection monitoring" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <div className={styles.container}>
          {/* Header */}
          <Flex justifyContent="between" alignItems="center" className={styles.header}>
            <div>
              <Title className={styles.title}>🔒 Fraud Detection Dashboard</Title>
              <Text className={styles.subtitle}>Real-time financial transaction monitoring</Text>
            </div>
            <div className={styles.statusContainer}>
              {loading && <Badge color="yellow">Loading...</Badge>}
              {error && <Badge color="red">Error: {error}</Badge>}
              {!loading && !error && (
                <Badge color="green">
                  Live • Updated {lastUpdate?.toLocaleTimeString()}
                </Badge>
              )}
            </div>
          </Flex>

          {/* KPI Cards */}
          <Grid numItemsSm={2} numItemsLg={4} className={styles.kpiGrid}>
            <Card decoration="top" decorationColor="red" className={styles.kpiCard}>
              <Flex alignItems="start">
                <div>
                  <Text>Fraud Detected (24h)</Text>
                  <Metric className={styles.fraudMetric}>
                    {stats?.fraudStats?.fraud_count ?? 0}
                  </Metric>
                </div>
                <Badge color="red" size="lg">🚨</Badge>
              </Flex>
              <ProgressBar
                value={Math.min(((stats?.fraudStats?.fraud_count ?? 0) / 100) * 100, 100)}
                color="red"
                className={styles.progressBar}
              />
            </Card>

            <Card decoration="top" decorationColor="amber" className={styles.kpiCard}>
              <Flex alignItems="start">
                <div>
                  <Text>Fraud Amount (24h)</Text>
                  <Metric className={styles.amountMetric}>
                    {formatCurrency(stats?.fraudStats?.fraud_total_amount ?? 0)}
                  </Metric>
                </div>
                <Badge color="amber" size="lg">💰</Badge>
              </Flex>
            </Card>

            <Card decoration="top" decorationColor="blue" className={styles.kpiCard}>
              <Flex alignItems="start">
                <div>
                  <Text>Total Alerts (24h)</Text>
                  <Metric>{stats?.fraudStats?.total_alerts ?? 0}</Metric>
                </div>
                <Badge color="blue" size="lg">📊</Badge>
              </Flex>
            </Card>

            <Card decoration="top" decorationColor="violet" className={styles.kpiCard}>
              <Flex alignItems="start">
                <div>
                  <Text>Users Flagged</Text>
                  <Metric>{stats?.fraudStats?.unique_users_flagged ?? 0}</Metric>
                </div>
                <Badge color="violet" size="lg">👤</Badge>
              </Flex>
            </Card>
          </Grid>

          {/* Charts and Alerts Grid */}
          <Grid numItemsLg={2} className={styles.mainGrid}>
            {/* Transactions Chart */}
            <Card className={styles.chartCard}>
              <Title>📈 Transactions per Minute</Title>
              <Text>Last hour activity</Text>
              {chartData.length > 0 ? (
                <LineChart
                  className={styles.chart}
                  data={chartData}
                  index="time"
                  categories={['Transactions', 'Volume ($)']}
                  colors={['blue', 'emerald']}
                  yAxisWidth={60}
                  showAnimation={true}
                  curveType="monotone"
                />
              ) : (
                <div className={styles.noData}>
                  <Text>No transaction data available</Text>
                  <Text>Waiting for data from the pipeline...</Text>
                </div>
              )}
            </Card>

            {/* Recent Alerts */}
            <Card className={styles.alertsCard}>
              <Title>🚨 Recent Fraud Alerts</Title>
              <Text>Latest detected suspicious activities</Text>
              <div className={styles.alertsTableContainer}>
                {stats?.recentAlerts && stats.recentAlerts.length > 0 ? (
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableHeaderCell>User ID</TableHeaderCell>
                        <TableHeaderCell>Amount</TableHeaderCell>
                        <TableHeaderCell>Txns</TableHeaderCell>
                        <TableHeaderCell>Time</TableHeaderCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.recentAlerts.map((alert, index) => (
                        <TableRow key={`${alert.user_id}-${alert.window_end}-${index}`}>
                          <TableCell>
                            <Badge color="red">#{alert.user_id}</Badge>
                          </TableCell>
                          <TableCell>
                            <Text className={styles.alertAmount}>
                              {formatCurrency(Number(alert.total_amount))}
                            </Text>
                          </TableCell>
                          <TableCell>
                            <Badge color="amber">{alert.transaction_count}</Badge>
                          </TableCell>
                          <TableCell>
                            <Text>{formatTime(alert.window_end)}</Text>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className={styles.noData}>
                    <Text>No fraud alerts detected</Text>
                    <Text>System is monitoring transactions...</Text>
                  </div>
                )}
              </div>
            </Card>
          </Grid>

          {/* Footer */}
          <div className={styles.footer}>
            <Text>
              🏦 Real-Time Fraud Detection Pipeline | Powered by Redpanda, Apache Flink & ClickHouse
            </Text>
          </div>
        </div>
      </main>
    </>
  );
}
