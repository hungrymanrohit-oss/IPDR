import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Chip,
  Button,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

const severityColors = {
  low: 'success',
  medium: 'warning',
  high: 'error',
  critical: 'error',
};

const alertTypeColors = {
  bandwidth_spike: 'primary',
  unusual_protocol: 'secondary',
  port_scan: 'warning',
  ddos_attack: 'error',
  data_exfiltration: 'error',
  custom: 'default',
};

function Alerts() {
  const [filters, setFilters] = useState({
    severity: '',
    acknowledged: '',
  });

  const queryClient = useQueryClient();

  const { data: alerts, isLoading, error } = useQuery(
    ['alerts', filters],
    () => alertsAPI.getAlerts(filters),
    { refetchInterval: 30000 }
  );

  const acknowledgeMutation = useMutation(
    (alertId) => alertsAPI.acknowledgeAlert(alertId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['alerts']);
        toast.success('Alert acknowledged successfully');
      },
      onError: (error) => {
        toast.error(`Error acknowledging alert: ${error.message}`);
      },
    }
  );

  const handleAcknowledge = (alertId) => {
    acknowledgeMutation.mutate(alertId);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Network Alerts
        </Typography>
        <Typography color="error">
          Error loading alerts: {error.message}
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

  const unacknowledgedAlerts = alerts?.results?.filter(alert => !alert.acknowledged) || [];
  const acknowledgedAlerts = alerts?.results?.filter(alert => alert.acknowledged) || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Network Alerts
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={filters.severity}
                  label="Severity"
                  onChange={(e) => handleFilterChange('severity', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filters.acknowledged}
                  label="Status"
                  onChange={(e) => handleFilterChange('acknowledged', e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="false">Unacknowledged</MenuItem>
                  <MenuItem value="true">Acknowledged</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Unacknowledged Alerts */}
      {unacknowledgedAlerts.length > 0 && (
        <Box mb={3}>
          <Typography variant="h6" gutterBottom color="error">
            Unacknowledged Alerts ({unacknowledgedAlerts.length})
          </Typography>
          <Grid container spacing={2}>
            {unacknowledgedAlerts.map((alert) => (
              <Grid item xs={12} key={alert.id}>
                <Alert 
                  severity={severityColors[alert.severity]}
                  action={
                    <Button
                      color="inherit"
                      size="small"
                      onClick={() => handleAcknowledge(alert.id)}
                      disabled={acknowledgeMutation.isLoading}
                    >
                      Acknowledge
                    </Button>
                  }
                >
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {alert.title}
                    </Typography>
                    <Typography variant="body2">
                      {alert.description}
                    </Typography>
                    <Box mt={1}>
                      <Chip 
                        label={alert.alert_type.replace('_', ' ').toUpperCase()} 
                        color={alertTypeColors[alert.alert_type]}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip 
                        label={alert.severity.toUpperCase()} 
                        color={severityColors[alert.severity]}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Typography variant="caption" color="textSecondary">
                        {new Date(alert.timestamp).toLocaleString()}
                      </Typography>
                    </Box>
                  </Box>
                </Alert>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* All Alerts */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            All Alerts
          </Typography>
          <Box sx={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #333' }}>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Type</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Severity</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Title</th>
                  <th style={{ padding: '12px', textAlign: 'left' }}>Description</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Timestamp</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts?.results?.map((alert) => (
                  <tr key={alert.id} style={{ borderBottom: '1px solid #333' }}>
                    <td style={{ padding: '12px' }}>
                      <Chip 
                        label={alert.alert_type.replace('_', ' ').toUpperCase()} 
                        color={alertTypeColors[alert.alert_type]}
                        size="small"
                      />
                    </td>
                    <td style={{ padding: '12px' }}>
                      <Chip 
                        label={alert.severity.toUpperCase()} 
                        color={severityColors[alert.severity]}
                        size="small"
                      />
                    </td>
                    <td style={{ padding: '12px' }}>{alert.title}</td>
                    <td style={{ padding: '12px' }}>{alert.description}</td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      <Chip 
                        label={alert.acknowledged ? 'Acknowledged' : 'Pending'} 
                        color={alert.acknowledged ? 'success' : 'warning'}
                        size="small"
                      />
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {new Date(alert.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px', textAlign: 'center' }}>
                      {!alert.acknowledged && (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => handleAcknowledge(alert.id)}
                          disabled={acknowledgeMutation.isLoading}
                        >
                          Acknowledge
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Alerts;