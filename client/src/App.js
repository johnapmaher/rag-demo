import React, { useState } from 'react';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [file, setFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleFileUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setUploadMessage(data.message);
    } catch (error) {
      setUploadMessage('Error uploading document');
    }
  };

  const handleQuery = async () => {
    try {
      const res = await fetch('http://localhost:8000/rag', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      setResponse('Error fetching response');
    }
  };

  return (
    <div>
      {/* Upload Section */}
      <div>
        <h2>Upload Document</h2>
        <input type="file" onChange={handleFileChange} aria-label="Upload Document" />
        <button onClick={handleFileUpload}>Upload</button>
        {uploadMessage && <p>{uploadMessage}</p>}
      </div>

      {/* Query Section */}
      <div>
        <h2>Ask a Question</h2>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question"
        />
        <button onClick={handleQuery}>Submit</button>
        {response && <p>Response: {response}</p>}
      </div>
    </div>
  );
}

export default App;