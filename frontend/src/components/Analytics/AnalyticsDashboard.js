import React, { useEffect, useState } from 'react';
import { analyticsAPI } from '../../services/api';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  CircularProgress, 
  Card, 
  CardContent,
  Chip
} from '@mui/material';

const AnalyticsDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await analyticsAPI.getDashboard();
        setDashboardData(response.data);
      } catch (err) {
        setError('Failed to load analytics data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Analytics Dashboard
      </Typography>
      
      {/* User Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'primary.main', color: 'white' }}>
            <Typography variant="h4">{dashboardData?.user_stats?.total_posts || 0}</Typography>
            <Typography variant="h6">Total Posts</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'warning.main', color: 'white' }}>
            <Typography variant="h4">{dashboardData?.user_stats?.drafts || 0}</Typography>
            <Typography variant="h6">Drafts</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'info.main', color: 'white' }}>
            <Typography variant="h4">{dashboardData?.user_stats?.scheduled || 0}</Typography>
            <Typography variant="h6">Scheduled</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'success.main', color: 'white' }}>
            <Typography variant="h4">{dashboardData?.user_stats?.published || 0}</Typography>
            <Typography variant="h6">Published</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* Engagement Summary */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Engagement Summary
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Typography variant="h5">👍 {dashboardData?.engagement_summary?.total_likes || 0}</Typography>
              <Typography color="text.secondary">Total Likes</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="h5">💬 {dashboardData?.engagement_summary?.total_comments || 0}</Typography>
              <Typography color="text.secondary">Total Comments</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="h5">🔄 {dashboardData?.engagement_summary?.total_shares || 0}</Typography>
              <Typography color="text.secondary">Total Shares</Typography>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="h5">📊 {dashboardData?.engagement_summary?.avg_engagement_rate || '0%'}</Typography>
              <Typography color="text.secondary">Engagement Rate</Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Content Performance */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Content Performance Insights
          </Typography>
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Best Performing Topics:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {(dashboardData?.content_performance?.best_performing_topics || ['AI', 'Technology', 'Innovation']).map((topic, index) => (
                <Chip key={index} label={topic} variant="outlined" />
              ))}
            </Box>
          </Box>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2">
                <strong>Optimal Post Length:</strong> {dashboardData?.content_performance?.optimal_post_length || 'Medium'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2">
                <strong>Best Posting Days:</strong> {(dashboardData?.content_performance?.best_posting_days || ['Tuesday', 'Wednesday', 'Thursday']).join(', ')}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default AnalyticsDashboard;
