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
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from 'react-query';
import { flowsAPI } from '../services/api';

function TopTalkers() {
  const { data: topTalkers, isLoading, error } = useQuery(
    'top-talkers',
    () => flowsAPI.getTopTalkers({ limit: 20 }),
    { refetchInterval: 60000 }
  );

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Top Talkers
        </Typography>
        <Typography color="error">
          Error loading top talkers: {error.message}
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
        Top Talkers
      </Typography>

      <Grid container spacing={3}>
        {/* Top Source IPs */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Source IPs (by Traffic Volume)
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={topTalkers?.top_sources || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ip_address" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${(value / (1024 * 1024)).toFixed(2)} MB`, 
                      name
                    ]}
                  />
                  <Bar dataKey="bytes_count" fill="#8884d8" name="Bytes" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Destination IPs */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Destination IPs (by Traffic Volume)
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={topTalkers?.top_destinations || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ip_address" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${(value / (1024 * 1024)).toFixed(2)} MB`, 
                      name
                    ]}
                  />
                  <Bar dataKey="bytes_count" fill="#82ca9d" name="Bytes" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Source IPs by Bandwidth */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Source IPs (by Bandwidth)
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={topTalkers?.top_sources || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ip_address" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value.toFixed(2)} Mbps`, 
                      name
                    ]}
                  />
                  <Bar dataKey="bandwidth_mbps" fill="#ffc658" name="Bandwidth (Mbps)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Destination IPs by Bandwidth */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Destination IPs (by Bandwidth)
              </Typography>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={topTalkers?.top_destinations || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ip_address" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value.toFixed(2)} Mbps`, 
                      name
                    ]}
                  />
                  <Bar dataKey="bandwidth_mbps" fill="#ff7300" name="Bandwidth (Mbps)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Detailed Source IPs Table */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Source IPs - Detailed View
              </Typography>
              <Box sx={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #333' }}>
                      <th style={{ padding: '12px', textAlign: 'left' }}>IP Address</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>Country</th>
                      <th style={{ padding: '12px', textAlign: 'left' }}>City</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Flows</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Packets</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Bytes</th>
                      <th style={{ padding: '12px', textAlign: 'right' }}>Bandwidth (Mbps)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {topTalkers?.top_sources?.map((ip, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #333' }}>
                        <td style={{ padding: '12px' }}>{ip.ip_address}</td>
                        <td style={{ padding: '12px' }}>
                          <Chip 
                            label={ip.country || 'Unknown'} 
                            size="small" 
                            variant="outlined"
                          />
                        </td>
                        <td style={{ padding: '12px' }}>{ip.city || 'Unknown'}</td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {ip.flows_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {ip.packets_count.toLocaleString()}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {(ip.bytes_count / (1024 * 1024)).toFixed(2)} MB
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          {ip.bandwidth_mbps.toFixed(2)}
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

export default TopTalkers;