import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const socketRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    if (!socketRef.current) { // Only connect if not already connected
        socketRef.current = new WebSocket('ws://localhost:8000/ws');

        socketRef.current.onopen = () => {
          console.log('WebSocket connected');
        };

        socketRef.current.onmessage = (event) => {
          console.log('Received:', event.data);
          setMessages((prev) => [...prev, event.data]);
        };

        socketRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          // Consider reconnecting here, if desired.
        };
    }

    // No cleanup function here! We want to keep the connection open.

  }, []); // Keep the empty dependency array to run only on mount


  const sendMessage = () => {
    if (messageInput.trim() && socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(messageInput);
      setMessageInput('');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>NegoWars Chat (MVP)</h1>
      <div>
        {messages.map((msg, index) => (
          <div key={index}>{msg}</div>
        ))}
      </div>
      <input
        type="text"
        value={messageInput}
        onChange={(e) => setMessageInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}

export default App;