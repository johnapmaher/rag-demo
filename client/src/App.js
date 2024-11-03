import React, { useState } from 'react';
import { Container, TextField, Button, Typography, Box, CircularProgress, Alert, Switch, FormControlLabel } from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { styled } from '@mui/system';

const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2', // Professional blue color
    },
    secondary: {
      main: '#dc004e', // Professional red color
    },
    background: {
      default: '#f5f5f5', // Light grey background
      paper: '#ffffff', // White paper background
    },
    text: {
      primary: '#333333', // Dark grey text
      secondary: '#666666', // Light grey text
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h4: {
      fontWeight: 500,
      color: '#1976d2',
    },
    h6: {
      fontWeight: 500,
      color: '#1976d2',
    },
  },
});

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9', // Light blue color
    },
    secondary: {
      main: '#f48fb1', // Light pink color
    },
    background: {
      default: '#121212', // Dark background
      paper: '#1e1e1e', // Dark paper background
    },
    text: {
      primary: '#ffffff', // White text
      secondary: '#bbbbbb', // Light grey text
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h4: {
      fontWeight: 500,
      color: '#90caf9',
    },
    h6: {
      fontWeight: 500,
      color: '#90caf9',
    },
  },
});

const CustomButton = styled(Button)({
  margin: '10px',
});

const CustomTextField = styled(TextField)({
  marginBottom: '10px',
});

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await fetch(process.env.REACT_APP_UPLOAD_URL, {
        method: 'POST',
        headers: { 
          'Content-Type': 'multipart/form-data',
          'file-name': file.name,},
        body: formData,
      });

      const data = await res.json();
      setUploadMessage(data.message);
      setSessionId(data.sessionId);
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
      const res = await fetch(process.env.REACT_APP_QUERY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, sessionId }),
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

  const handleThemeChange = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <Box sx={{ backgroundColor: 'background.default', minHeight: '100vh', padding: 2 }}>
        <Container maxWidth="md">
          <Box my={4}>
            <FormControlLabel
              control={<Switch checked={darkMode} onChange={handleThemeChange} />}
              label="Dark Mode"
            />
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
                <CustomButton variant="contained" color="primary" component="span">
                  Choose File
                </CustomButton>
              </label>
              <CustomButton
                variant="contained"
                color="secondary"
                onClick={handleFileUpload}
                disabled={!file || loading}
              >
                Upload
              </CustomButton>
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
              <CustomTextField
                label="Ask a question"
                variant="outlined"
                fullWidth
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <CustomButton
                variant="contained"
                color="primary"
                onClick={handleQuery}
                disabled={loading}
              >
                Submit
              </CustomButton>
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
      </Box>
    </ThemeProvider>
  );
}

export default App;