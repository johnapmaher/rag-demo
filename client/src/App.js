import React, { useState } from "react";

function App() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  const handleQuery = async () => {
    const res = await fetch("http://localhost:8000/rag", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    setResponse(data.response);
  };

  return (
    <div>
      <h1>RAG Demo</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question"
      />
      <button onClick={handleQuery}>Submit</button>
      <div>{response && <p>Response: {response}</p>}</div>
    </div>
  );
}

export default App;
