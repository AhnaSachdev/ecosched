import { useState } from "react";
import axios from "axios";

function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");

  const sendPrompt = async () => {
    const res = await axios.post("http://127.0.0.1:8000/ask", {
      text: input,
    });
    setResponse(res.data.response);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>EcoSched AI</h1>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask something..."
        style={{ width: "300px", padding: "10px" }}
      />

      <button onClick={sendPrompt}>Send</button>

      <p>{response}</p>
    </div>
  );
}

export default App;