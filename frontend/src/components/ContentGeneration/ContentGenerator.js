
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Paper,
  Snackbar,
} from '@mui/material';
import { contentAPI, linkedinAPI } from '../../services/api';
import { useAuth } from '../../hooks/useAuth';

const TONE_OPTIONS = [
  "professional", "casual", "inspirational"
];
const AUDIENCE_OPTIONS = [
  "entry", "manager", "executive", "all"
];

const ContentGenerator = () => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    topic: '',
    post_type: 'professional',
    length: 'medium',
    tone: 'professional',
    audience: '',
  });
  const [generatedContent, setGeneratedContent] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [topicSuggestions, setTopicSuggestions] = useState([]);
  const [linkedinStatus, setLinkedinStatus] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editableContent, setEditableContent] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [scheduleDateTime, setScheduleDateTime] = useState('');

  // AI Content Improvement state
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestionType, setSuggestionType] = useState('improve');
  const [customRequest, setCustomRequest] = useState('');

  useEffect(() => {
    checkLinkedInStatus();
  }, [user]);

  useEffect(() => {
    const cached = localStorage.getItem(`topicSuggestions:${user?.industry}`);
    if (user?.industry && cached) {
      setTopicSuggestions(JSON.parse(cached));
    } else if (user?.industry) {
      fetchTopicSuggestions();
    }
  }, [user?.industry]); 

  const fetchContentSuggestions = async (type = 'improve', customReq = '') => {
    if (!editableContent.trim()) {
      setSnackbar({ open: true, message: 'Please enter some content to improve', severity: 'warning' });
      return;
    }
    
    setLoadingSuggestions(true);
    try {
      const response = await contentAPI.suggestImprovements({
        current_content: editableContent,
        suggestion_type: type,
        target_tone: formData.tone,
        specific_request: customReq
      });
      
      // Directly apply the improved content
      const improvedContent = response.data.content;
      setEditableContent(improvedContent);
      
      // Update the main content state
      setGeneratedContent(prev => ({
        ...prev,
        content: improvedContent,
        hashtags: response.data.hashtags || prev.hashtags,
        character_count: response.data.character_count || improvedContent.length,
        estimated_engagement: response.data.estimated_engagement || prev.estimated_engagement
      }));
      
      setSnackbar({ open: true, message: 'Content improved successfully!', severity: 'success' });
    } catch (error) {
      console.error('Failed to improve content:', error);
      
      const errorMessage = error.response?.data?.detail || 
                          error.response?.statusText || 
                          'Failed to improve content';
      
      setSnackbar({ open: true, message: errorMessage, severity: 'error' });
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const fetchTopicSuggestions = async () => {
    try {
      const response = await contentAPI.getTopicSuggestions(user.industry);
      setTopicSuggestions(response.data.suggestions);
      localStorage.setItem(
        `topicSuggestions:${user.industry}`,
        JSON.stringify(response.data.suggestions)
      );
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    }
  };

  const handleSchedulePost = async () => {
    if (!scheduleDateTime) {
      setSnackbar({ open: true, message: 'Please select date and time', severity: 'warning' });
      return;
    }

    const isoString = new Date(scheduleDateTime).toISOString();
    console.log('Scheduling post:', generatedContent.post_id, scheduleDateTime);

    try {
      await contentAPI.schedulePost({
        post_id: generatedContent.post_id,
        scheduled_time: isoString
      });

      setSnackbar({ open: true, message: 'Post scheduled successfully!', severity: 'success' });
    } catch (error) {
      console.error('Failed to schedule post:', error);
      setSnackbar({ open: true, message: 'Failed to schedule post', severity: 'error' });
    }
  };

  const checkLinkedInStatus = async () => {
    try {
      const response = await linkedinAPI.getConnectionStatus();
      setLinkedinStatus(response.data.connected);
    } catch (error) {
      console.error('Failed to check LinkedIn status:', error);
    }
  };

  const handleGenerate = async () => {
    if (!formData.topic.trim()) {
      setError('Please enter a topic');
      return;
    }
    setLoading(true);
    setError('');
    setEditMode(false);

    try {
      const response = await contentAPI.generateContent(formData);
      setGeneratedContent(response.data);
      console.log('Generated content:', response.data);
      setSnackbar({ open: true, message: 'Content generated successfully!', severity: 'success' });
    } catch (error) {
      setError('Failed to generate content. Please try again.');
      setSnackbar({ open: true, message: 'Content generation failed.', severity: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!generatedContent) return;
    try {
      await contentAPI.saveDraft({
        content: editMode ? editableContent : generatedContent.content,
        hashtags: generatedContent.hashtags,
        topic: generatedContent.topic,
      });
      setSnackbar({ open: true, message: 'Draft saved successfully!', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to save draft', severity: 'error' });
    }
  };

  const handlePublishToLinkedIn = async () => {
    if (!generatedContent) return;
    if (!linkedinStatus) {
      setSnackbar({ open: true, message: 'Please connect your LinkedIn account first', severity: 'warning' });
      return;
    }
    try {
      const response = await linkedinAPI.publishPost({
        post_id: generatedContent.post_id, 
        content: editMode ? editableContent : generatedContent.content
      });
      if (response.data.success) {
        setSnackbar({ open: true, message: 'Published to LinkedIn successfully!', severity: 'success' });
      } else {
        setSnackbar({ open: true, message: 'Failed to publish to LinkedIn: ' + response.data.error, severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to publish to LinkedIn', severity: 'error' });
    }
  };

  const handleConnectLinkedIn = async () => {
    try {
      const response = await linkedinAPI.connectLinkedIn();
      window.open(response.data.authorization_url, '_blank');
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to connect LinkedIn', severity: 'error' });
    }
  };

  const handleDisconnectLinkedIn = async () => {
    try {
      await linkedinAPI.disconnectLinkedIn();
      setLinkedinStatus(false);
      setSnackbar({ open: true, message: 'LinkedIn disconnected successfully!', severity: 'success' });
    } catch (error) {
      setSnackbar({ open: true, message: 'Failed to disconnect LinkedIn', severity: 'error' });
    }
  };

  const handleEditToggle = () => {
    setEditMode(!editMode);
    if (!editMode) {
      setEditableContent(generatedContent.content);
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        AI Content Generator
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate LinkedIn Post
              </Typography>

              <TextField
                fullWidth
                label="Topic"
                value={formData.topic}
                onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                margin="normal"
                placeholder="e.g., The future of AI in software development"
              />

              <TextField
                fullWidth
                select
                label="Post Type"
                value={formData.post_type}
                onChange={(e) => setFormData({ ...formData, post_type: e.target.value })}
                margin="normal"
              >
                <MenuItem value="professional">Professional</MenuItem>
                <MenuItem value="casual">Casual</MenuItem>
                <MenuItem value="thought_leadership">Thought Leadership</MenuItem>
              </TextField>

              <TextField
                fullWidth
                select
                label="Length"
                value={formData.length}
                onChange={(e) => setFormData({ ...formData, length: e.target.value })}
                margin="normal"
              >
                <MenuItem value="short">Short (&lt; 100 words)</MenuItem>
                <MenuItem value="medium">Medium (100-200 words)</MenuItem>
                <MenuItem value="long">Long (200-300 words)</MenuItem>
              </TextField>

              <TextField
                fullWidth
                select
                label="Tone"
                value={formData.tone}
                onChange={(e) => setFormData({ ...formData, tone: e.target.value })}
                margin="normal"
              >
                {TONE_OPTIONS.map((tone) => (
                  <MenuItem key={tone} value={tone}>
                    {tone.charAt(0).toUpperCase() + tone.slice(1)}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                fullWidth
                select
                label="Target Audience"
                value={formData.audience}
                onChange={(e) => setFormData({ ...formData, audience: e.target.value })}
                margin="normal"
              >
                {AUDIENCE_OPTIONS.map((aud) => (
                  <MenuItem key={aud} value={aud}>
                    {aud === 'all' ? 'General LinkedIn Audience' : aud.charAt(0).toUpperCase() + aud.slice(1)}
                  </MenuItem>
                ))}
              </TextField>

              {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

              <Button
                variant="contained"
                onClick={handleGenerate}
                disabled={loading}
                fullWidth
                sx={{ mt: 3 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate Content'}
              </Button>
            </CardContent>
          </Card>

          {/* LinkedIn Connection Status */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>LinkedIn Connection</Typography>
              {linkedinStatus ? (
                <>
                  <Alert severity="success">LinkedIn Connected ✓</Alert>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={handleDisconnectLinkedIn}
                    sx={{ mt: 2 }}
                  >
                    Disconnect LinkedIn
                  </Button>
                </>
              ) : (
                <Box>
                  <Alert severity="warning">LinkedIn Not Connected</Alert>
                  <Button
                    variant="outlined"
                    onClick={handleConnectLinkedIn}
                    sx={{ mt: 2 }}
                  >
                    Connect LinkedIn
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>

          {topicSuggestions.length > 0 && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Topic Suggestions for {user?.industry}
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {topicSuggestions.map((suggestion, index) => (
                    <Chip
                      key={index}
                      label={suggestion}
                      onClick={() => setFormData({ ...formData, topic: suggestion })}
                      variant="outlined"
                      clickable
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {generatedContent && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Generated Content
                </Typography>
                <Box sx={{ mt: 1, textAlign: 'right' }}>
                  <Typography variant="caption">
                    Character count: {(editMode ? editableContent.length : generatedContent.content.length)}/3000
                  </Typography>
                </Box>
                <Paper sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  {editMode ? (
                    <Box>
                      <TextField
                        multiline
                        fullWidth
                        value={editableContent}
                        onChange={e => setEditableContent(e.target.value)}
                        rows={6}
                        label="Edit Content"
                        sx={{ mb: 2 }}
                      />
                      
                      {/* AI Content Improvement Panel */}
                      <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          AI Content Improvements
                        </Typography>
                        
                        <Grid container spacing={2} sx={{ mb: 2 }}>
                          <Grid item xs={12} sm={6}>
                            <TextField
                              select
                              fullWidth
                              size="small"
                              label="Improvement Type"
                              value={suggestionType}
                              onChange={(e) => setSuggestionType(e.target.value)}
                            >
                              <MenuItem value="improve">Improve Engagement</MenuItem>
                              <MenuItem value="shorten">Make Shorter</MenuItem>
                              <MenuItem value="expand">Add More Detail</MenuItem>
                              <MenuItem value="tone_change">Change Tone</MenuItem>
                              <MenuItem value="custom">Custom Request</MenuItem>
                            </TextField>
                          </Grid>
                          
                          {suggestionType === 'custom' && (
                            <Grid item xs={12}>
                              <TextField
                                fullWidth
                                size="small"
                                label="Describe what you want to change"
                                value={customRequest}
                                onChange={(e) => setCustomRequest(e.target.value)}
                                placeholder="e.g., make it more technical, add statistics, focus on benefits..."
                              />
                            </Grid>
                          )}
                          
                          <Grid item xs={12} sm={6}>
                            <Button
                              variant="contained"
                              onClick={() => fetchContentSuggestions(suggestionType, customRequest)}
                              disabled={loadingSuggestions || !editableContent.trim()}
                              fullWidth
                              size="small"
                            >
                              {loadingSuggestions ? <CircularProgress size={20} /> : 'Apply AI Improvement'}
                            </Button>
                          </Grid>
                        </Grid>
                        
                        <Typography variant="caption" color="text.secondary">
                          This will directly improve your content based on the selected type.
                        </Typography>
                      </Box>
                    </Box>
                  ) : (
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                      {generatedContent.content}
                    </Typography>
                  )}
                </Paper>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Hashtags:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {generatedContent.hashtags.map((hashtag, index) => (
                      <Chip key={index} label={hashtag} size="small" />
                    ))}
                  </Box>
                </Box>
                
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Predicted Engagement:
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Typography variant="body2">
                        👍 {generatedContent.estimated_engagement.predicted_likes}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2">
                        💬 {generatedContent.estimated_engagement.predicted_comments}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2">
                        🔄 {generatedContent.estimated_engagement.predicted_shares}
                      </Typography>
                    </Grid>
                    <Grid item xs={3}>
                      <Typography variant="body2">
                        📊 {generatedContent.estimated_engagement.engagement_score}%
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
                
                <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                  <Button
                    variant={editMode ? "contained" : "outlined"}
                    onClick={handleEditToggle}
                    sx={{ flex: 1 }}
                  >
                    {editMode ? 'Preview' : 'Edit'}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleSaveDraft}
                    sx={{ flex: 1 }}
                  >
                    Save as Draft
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handlePublishToLinkedIn}
                    disabled={!linkedinStatus}
                    sx={{ flex: 1 }}
                  >
                    Publish to LinkedIn
                  </Button>
                </Box>
                
                <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Schedule for Later
                  </Typography>
                  
                  <TextField
                    label="Schedule Date & Time"
                    type="datetime-local"
                    value={scheduleDateTime}
                    onChange={(e) => setScheduleDateTime(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    fullWidth
                    sx={{ mb: 2 }}
                    inputProps={{
                      min: new Date().toISOString().slice(0, 16)
                    }}
                  />
                  
                  <Button
                    variant="outlined"
                    onClick={handleSchedulePost}
                    disabled={!scheduleDateTime}
                    fullWidth
                  >
                    Schedule Post
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3500}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ContentProps={{ 
          'aria-describedby': 'message-id', 
          style: { 
            backgroundColor: snackbar.severity === 'success' ? '#43a047' : 
                           snackbar.severity === 'warning' ? '#ff9800' : '#d32f2f' 
          } 
        }}
      />
    </Box>
  );
};

export default ContentGenerator;



