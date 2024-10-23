import React, { useState } from 'react';
import { Container, TextField, Button, Typography, Box, CircularProgress, Alert } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { styled } from '@mui/system';

const theme = createTheme({
  palette: {
    primary: {
      main: '#00ffcc',
    },
    secondary: {
      main: '#ff00ff',
    },
    background: {
      default: '#0d0d0d',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#00ffcc',
      secondary: '#ff00ff',
    },
  },
  typography: {
    fontFamily: 'Orbitron, Arial, sans-serif',
    h4: {
      color: '#ff00ff',
      textShadow: '0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 20px #ff00ff',
    },
    h6: {
      color: '#ff00ff',
      textShadow: '0 0 5px #ff00ff, 0 0 10px #ff00ff, 0 0 20px #ff00ff',
    },
  },
});

const NeonButton = styled(Button)({
  backgroundColor: '#0d0d0d',
  color: '#00ffcc',
  border: '2px solid #00ffcc',
  padding: '10px 20px',
  fontFamily: 'Orbitron, sans-serif',
  cursor: 'pointer',
  transition: 'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease',
  '&:hover': {
    backgroundColor: '#00ffcc',
    color: '#0d0d0d',
    borderColor: '#ff00ff',
  },
});

const NeonTextField = styled(TextField)({
  '& .MuiOutlinedInput-root': {
    '& fieldset': {
      borderColor: '#00ffcc',
    },
    '&:hover fieldset': {
      borderColor: '#ff00ff',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#ff00ff',
    },
  },
  '& .MuiInputBase-input': {
    color: '#00ffcc',
  },
  '& .MuiInputLabel-root': {
    color: '#00ffcc',
  },
  '& .MuiInputLabel-root.Mui-focused': {
    color: '#ff00ff',
  },
});

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
    <ThemeProvider theme={theme}>
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
              <NeonButton variant="contained" color="primary" component="span">
                Choose File
              </NeonButton>
            </label>
            <NeonButton
              variant="contained"
              color="secondary"
              onClick={handleFileUpload}
              disabled={!file || loading}
              style={{ marginLeft: '10px' }}
            >
              Upload
            </NeonButton>
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
            <NeonTextField
              label="Ask a question"
              variant="outlined"
              fullWidth
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{ marginBottom: '10px' }}
            />
            <NeonButton
              variant="contained"
              color="primary"
              onClick={handleQuery}
              disabled={loading}
            >
              Submit
            </NeonButton>
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
    </ThemeProvider>
  );
}

export default App;