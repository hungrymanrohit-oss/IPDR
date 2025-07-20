import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import { flowsAPI } from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82ca9d', '#ffc658'];

function Geographic() {
  const { data: geographic, isLoading, error } = useQuery(
    'geographic',
    () => flowsAPI.getGeographic({ hours: 24 }),
    { refetchInterval: 300000 } // 5 minutes
  );

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Geographic Distribution
        </Typography>
        <Typography color="error">
          Error loading geographic data: {error.message}
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
        Geographic Distribution
      </Typography>

      <Grid container spacing={3}>
        {/* Source Countries */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Source Countries
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={geographic?.source_countries || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="country" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      value.toLocaleString(), 
                      name
                    ]}
                  />
                  <Bar dataKey="flows_count" fill="#8884d8" name="Flows" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Destination Countries */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Destination Countries
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={geographic?.destination_countries || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="country" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      value.toLocaleString(), 
                      name
                    ]}
                  />
                  <Bar dataKey="flows_count" fill="#82ca9d" name="Flows" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Source Countries Pie Chart */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Source Countries Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={geographic?.source_countries || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ country, percent }) => `${country} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="flows_count"
                  >
                    {(geographic?.source_countries || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Destination Countries Pie Chart */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Destination Countries Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={geographic?.destination_countries || []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ country, percent }) => `${country} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={120}
                    fill="#82ca9d"
                    dataKey="flows_count"
                  >
                    {(geographic?.destination_countries || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Source Countries Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Source Countries - Detailed View
              </Typography>
              <Box sx={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #333' }}>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Country</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Flows</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Packets</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Bytes</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {geographic?.source_countries?.map((country, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #333' }}>
                        <td style={{ padding: '12px' }}>
                          <Chip 
                            label={country.country} 
                            size="small" 
                            variant="outlined"
                          />
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.flows_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.packets_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {(country.bytes_count / (1024 * 1024 * 1024)).toFixed(2)} GB
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Destination Countries Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Destination Countries - Detailed View
              </Typography>
              <Box sx={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #333' }}>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Country</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Flows</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Packets</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Bytes</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {geographic?.destination_countries?.map((country, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #333' }}>
                        <td style={{ padding: '12px' }}>
                          <Chip 
                            label={country.country} 
                            size="small" 
                            variant="outlined"
                          />
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.flows_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.packets_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {(country.bytes_count / (1024 * 1024 * 1024)).toFixed(2)} GB
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {country.percentage.toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Geographic;