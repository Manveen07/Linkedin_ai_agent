import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './hooks/useAuth';
import LoginForm from './components/Auth/LoginForm';
import ContentGenerator from './components/ContentGeneration/ContentGenerator';
import AnalyticsDashboard from './components/Analytics/AnalyticsDashboard';
import LinkedInCallback from './components/LinkedIn/LinkedInCallback';

import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box, 
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0077B5', // LinkedIn blue
    },
  },
});

const MainDashboard = () => {
  const [activeTab, setActiveTab] = React.useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} centered>
          <Tab label="Content Generator" />
          <Tab label="Analytics" />
        </Tabs>
      </Box>
      
      {activeTab === 0 && <ContentGenerator />}
      {activeTab === 1 && <AnalyticsDashboard />}
    </Box>
  );
};

const AppLayout = ({ children }) => {
  const { user, logout, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            LinkedIn AI Agent
          </Typography>
          {user && (
            <>
              <Typography variant="body2" sx={{ mr: 2 }}>
                Welcome, {user.name}
              </Typography>
              <Button color="inherit" onClick={logout}>
                Logout
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>

      
      <Box sx={{ mt: 2 }}>
        {children}
      </Box>
    </Box>
  );
};

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <AppLayout>
            <Routes>
              <Route 
                path="/login" 
                element={<LoginForm />} 
              />
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <MainDashboard />
                  </ProtectedRoute>
                } 
              />
              {/* Add LinkedIn callback route */}
              <Route 
                path="/linkedin/callback" 
                element={
                  <ProtectedRoute>
                    <LinkedInCallback />
                  </ProtectedRoute>
                } 
              />
              <Route 
                path="/" 
                element={<Navigate to="/dashboard" />} 
              />
            </Routes>
          </AppLayout>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
