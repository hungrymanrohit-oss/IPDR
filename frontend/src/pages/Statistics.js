import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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
import { statisticsAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

function Statistics() {
  const { data: statistics, isLoading, error } = useQuery(
    'statistics',
    () => statisticsAPI.getStatistics(),
    { refetchInterval: 60000 }
  );

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Flow Statistics
        </Typography>
        <Typography color="error">
          Error loading statistics: {error.message}
        </Typography>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Flow Statistics
      </Typography>

      <Grid container spacing={3}>
        {/* Time Series Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Flow Volume Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={statistics?.time_series || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(value) => new Date(value).toLocaleString()}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="total_flows" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    name="Total Flows"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="total_packets" 
                    stroke="#82ca9d" 
                    strokeWidth={2}
                    name="Total Packets"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Protocol Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Protocol Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statistics?.protocol_distribution || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="flows_count"
                  >
                    {(statistics?.protocol_distribution || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Ports */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Destination Ports
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statistics?.top_ports || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="dst_port" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="flows_count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Country Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Geographic Distribution (Source)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statistics?.country_distribution?.source || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="country" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="flows_count" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* ASN Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                ASN Distribution (Source)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={statistics?.asn_distribution?.source || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="asn" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="flows_count" fill="#ffc658" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Summary Statistics */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary Statistics
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="textSecondary">
                    Average Flow Duration
                  </Typography>
                  <Typography variant="h6">
                    {statistics?.avg_flow_duration ? 
                      `${statistics.avg_flow_duration.toFixed(2)}s` : 
                      'N/A'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="textSecondary">
                    Maximum Bandwidth
                  </Typography>
                  <Typography variant="h6">
                    {statistics?.max_bandwidth ? 
                      `${statistics.max_bandwidth.toFixed(2)} Mbps` : 
                      'N/A'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="textSecondary">
                    Average Bandwidth
                  </Typography>
                  <Typography variant="h6">
                    {statistics?.avg_bandwidth ? 
                      `${statistics.avg_bandwidth.toFixed(2)} Mbps` : 
                      'N/A'
                    }
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="body2" color="textSecondary">
                    Total Unique IPs
                  </Typography>
                  <Typography variant="h6">
                    {statistics?.unique_ips || 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Statistics;