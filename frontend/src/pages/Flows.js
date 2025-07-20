import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  CircularProgress,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { flowsAPI } from '../services/api';

const columns = [
  { field: 'flow_id', headerName: 'Flow ID', width: 130 },
  { field: 'src_ip', headerName: 'Source IP', width: 130 },
  { field: 'dst_ip', headerName: 'Destination IP', width: 130 },
  { field: 'src_port', headerName: 'Src Port', width: 100 },
  { field: 'dst_port', headerName: 'Dst Port', width: 100 },
  { field: 'protocol_name', headerName: 'Protocol', width: 100 },
  { field: 'packets', headerName: 'Packets', width: 100, type: 'number' },
  { field: 'bytes', headerName: 'Bytes', width: 120, type: 'number' },
  { 
    field: 'bandwidth_mbps', 
    headerName: 'Bandwidth (Mbps)', 
    width: 150, 
    type: 'number',
    valueFormatter: (params) => params.value.toFixed(2)
  },
  { 
    field: 'timestamp', 
    headerName: 'Timestamp', 
    width: 180,
    valueFormatter: (params) => new Date(params.value).toLocaleString()
  },
  {
    field: 'src_country',
    headerName: 'Src Country',
    width: 120,
    renderCell: (params) => (
      <Chip 
        label={params.value || 'Unknown'} 
        size="small" 
        variant="outlined"
      />
    )
  },
  {
    field: 'dst_country',
    headerName: 'Dst Country',
    width: 120,
    renderCell: (params) => (
      <Chip 
        label={params.value || 'Unknown'} 
        size="small" 
        variant="outlined"
      />
    )
  },
];

function Flows() {
  const [filters, setFilters] = useState({
    src_ip: '',
    dst_ip: '',
    protocol: '',
  });

  const { data: flows, isLoading, error } = useQuery(
    ['flows', filters],
    () => flowsAPI.getFlows(filters),
    { refetchInterval: 30000 }
  );

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleClearFilters = () => {
    setFilters({
      src_ip: '',
      dst_ip: '',
      protocol: '',
    });
  };

  if (error) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Network Flows
        </Typography>
        <Typography color="error">
          Error loading flows: {error.message}
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Network Flows
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="Source IP"
                value={filters.src_ip}
                onChange={(e) => handleFilterChange('src_ip', e.target.value)}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="Destination IP"
                value={filters.dst_ip}
                onChange={(e) => handleFilterChange('dst_ip', e.target.value)}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                label="Protocol"
                value={filters.protocol}
                onChange={(e) => handleFilterChange('protocol', e.target.value)}
                size="small"
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <Button
                variant="outlined"
                onClick={handleClearFilters}
                fullWidth
              >
                Clear Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Flows Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Flow Data
          </Typography>
          <Box sx={{ height: 600, width: '100%' }}>
            {isLoading ? (
              <Box display="flex" justifyContent="center" alignItems="center" height="100%">
                <CircularProgress />
              </Box>
            ) : (
              <DataGrid
                rows={flows?.results || []}
                columns={columns}
                pageSize={25}
                rowsPerPageOptions={[25, 50, 100]}
                disableSelectionOnClick
                loading={isLoading}
                getRowId={(row) => row.flow_id}
                sx={{
                  '& .MuiDataGrid-cell': {
                    borderBottom: '1px solid #333',
                  },
                  '& .MuiDataGrid-columnHeaders': {
                    backgroundColor: '#1a1a1a',
                    borderBottom: '2px solid #333',
                  },
                }}
              />
            )}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Flows;