import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import { api } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function Dashboard() {
  const [realTimeData, setRealTimeData] = useState(null);
  const { data: summary, isLoading: summaryLoading } = useQuery(
    'summary',
    () => api.get('/api/flows/summary/'),
    { refetchInterval: 30000 }
  );

  const { data: topTalkers, isLoading: talkersLoading } = useQuery(
    'top-talkers',
    () => api.get('/api/flows/top-talkers/'),
    { refetchInterval: 60000 }
  );

  const { data: protocols, isLoading: protocolsLoading } = useQuery(
    'protocols',
    () => api.get('/api/flows/protocols/'),
    { refetchInterval: 60000 }
  );

  const { data: bandwidth, isLoading: bandwidthLoading } = useQuery(
    'bandwidth',
    () => api.get('/api/flows/bandwidth/?hours=1&interval=5m'),
    { refetchInterval: 30000 }
  );

  // WebSocket connection for real-time updates
  const { data: wsData } = useWebSocket('ws://localhost:8000/ws/flows/');

  useEffect(() => {
    if (wsData) {
      setRealTimeData(wsData);
    }
  }, [wsData]);

  if (summaryLoading || talkersLoading || protocolsLoading || bandwidthLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Network Flow Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Flows (24h)
              </Typography>
              <Typography variant="h4">
                {summary?.total_flows?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Packets (24h)
              </Typography>
              <Typography variant="h4">
                {summary?.total_packets?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Bytes (24h)
              </Typography>
              <Typography variant="h4">
                {summary?.total_bytes ? 
                  `${(summary.total_bytes / (1024 * 1024 * 1024)).toFixed(2)} GB` : 
                  '0 GB'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Bandwidth
              </Typography>
              <Typography variant="h4">
                {summary?.avg_bandwidth ? 
                  `${summary.avg_bandwidth.toFixed(2)} Mbps` : 
                  '0 Mbps'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Bandwidth Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bandwidth Usage (Last Hour)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={bandwidth || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                    formatter={(value) => [`${value.toFixed(2)} Mbps`, 'Bandwidth']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="bandwidth_mbps" 
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Protocol Distribution */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Protocol Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={protocols || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="flows_count"
                  >
                    {(protocols || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Talkers */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Source IPs
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={topTalkers?.top_sources || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ip_address" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="bandwidth_mbps" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Real-time Flows */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Flows
              </Typography>
              <Box maxHeight={300} overflow="auto">
                {realTimeData?.recent_flows?.map((flow, index) => (
                  <Box key={index} mb={1} p={1} border="1px solid #333" borderRadius={1}>
                    <Typography variant="body2">
                      {flow.src_ip} → {flow.dst_ip} ({flow.protocol})
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {flow.bandwidth_mbps.toFixed(2)} Mbps • {new Date(flow.timestamp).toLocaleTimeString()}
                    </Typography>
                  </Box>
                )) || (
                  <Typography color="textSecondary">
                    No recent flows available
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Real-time Status */}
      {realTimeData && (
        <Alert severity="success" sx={{ mt: 2 }}>
          Real-time data connection active - Last update: {new Date().toLocaleTimeString()}
        </Alert>
      )}
    </Box>
  );
}

export default Dashboard;