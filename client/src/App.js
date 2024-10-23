import React, { useState } from 'react';
import { Container, TextField, Button, Typography, Box, CircularProgress, Alert } from '@mui/material';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();
      setUploadMessage(data.message);
    } catch (error) {
      setUploadMessage('Error uploading file.');
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/rag', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      setResponse('Error fetching response');
      console.error('Query error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box my={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Document Upload and Query
        </Typography>

        {/* Upload Section */}
        <Box my={4}>
          <Typography variant="h6" component="h2" gutterBottom>
            Upload Document
          </Typography>
          <input
            accept="text/plain"
            style={{ display: 'none' }}
            id="upload-file"
            type="file"
            onChange={handleFileChange}
          />
          <label htmlFor="upload-file">
            <Button variant="contained" color="primary" component="span">
              Choose File
            </Button>
          </label>
          <Button
            variant="contained"
            color="secondary"
            onClick={handleFileUpload}
            disabled={!file || loading}
            style={{ marginLeft: '10px' }}
          >
            Upload
          </Button>
          {loading && <CircularProgress size={24} style={{ marginLeft: '10px' }} />}
          {uploadMessage && (
            <Box mt={2}>
              <Alert severity={uploadMessage.includes('Error') ? 'error' : 'success'}>
                {uploadMessage}
              </Alert>
            </Box>
          )}
        </Box>

        {/* Query Section */}
        <Box my={4}>
          <Typography variant="h6" component="h2" gutterBottom>
            Ask a Question
          </Typography>
          <TextField
            label="Ask a question"
            variant="outlined"
            fullWidth
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ marginBottom: '10px' }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleQuery}
            disabled={loading}
          >
            Submit
          </Button>
          {loading && <CircularProgress size={24} style={{ marginLeft: '10px' }} />}
          {response && (
            <Box mt={2}>
              <Alert severity={response.includes('Error') ? 'error' : 'success'}>
                {response}
              </Alert>
            </Box>
          )}
        </Box>
      </Box>
    </Container>
  );
}

export default App;