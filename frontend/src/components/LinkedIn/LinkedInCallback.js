import React, { useEffect, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert, Button } from '@mui/material';
import { linkedinAPI } from '../../services/api';

const LinkedInCallback = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const hasProcessed = useRef(false); // ← Prevent double processing

  useEffect(() => {
    if (hasProcessed.current) return; // ← Exit if already processed

    const handleCallback = async () => {
      hasProcessed.current = true; // ← Mark as processed
      
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const errorParam = urlParams.get('error');

      if (errorParam) {
        setError(`LinkedIn authorization failed: ${errorParam}`);
        setLoading(false);
        return;
      }

      if (!code) {
        setError('No authorization code received');
        setLoading(false);
        return;
      }

      try {
        console.log('Exchanging LinkedIn code...');
        const response = await linkedinAPI.exchangeCodeForToken(code);
        
        if (response.data.success) {
          console.log('LinkedIn connected successfully');
          navigate('/dashboard?linkedin=connected');
        } else {
          setError('Failed to connect LinkedIn account');
          setLoading(false);
        }
      } catch (err) {
        console.error('LinkedIn callback error:', err);
        setError('Failed to process LinkedIn authorization');
        setLoading(false);
      }
    };

    handleCallback();
  }, []); // ← Remove dependencies to prevent re-runs

  if (loading) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Connecting your LinkedIn account...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 8 }}>
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        <Button 
          variant="contained" 
          onClick={() => navigate('/dashboard')}
        >
          Return to Dashboard
        </Button>
      </Box>
    );
  }

  return null;
};

export default LinkedInCallback;


