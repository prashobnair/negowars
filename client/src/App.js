import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [myPlayerNumber, setMyPlayerNumber] = useState(null); // Store our player number
  const socketRef = useRef(null);

  useEffect(() => {
    if (!socketRef.current) {
        socketRef.current = new WebSocket('ws://localhost:8000/ws');

        socketRef.current.onopen = () => {
          console.log('WebSocket connected');
        };

        socketRef.current.onmessage = (event) => {
          console.log('Received:', event.data);
          const parts = event.data.split(":");
          const messageType = parts[0];

            if (messageType === "init") {
                const playerNumber = parts[1];
                setMyPlayerNumber("You are Player " + playerNumber);
            } else if(messageType === "ack") {
                const messageId = parts[1];
                const playerNumber = parts[2];
                const messageContent = parts[3];
                setMessages((prev) => [...prev, `Player ${playerNumber}: ${messageContent}`]);
            } else if (messageType === "msg") {
                const messageId = parts[1];
                const playerNumber = parts[2];
                const messageContent = parts[3];
                setMessages((prev) => [...prev, `Player ${playerNumber}: ${messageContent}`]);
            }
        };

        socketRef.current.onclose = () => {
          console.log('WebSocket disconnected');
        };
    }
  }, []);

  const sendMessage = () => {
    if (messageInput.trim() && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(messageInput);
      setMessageInput('');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>NegoWars Chat (MVP)</h1>
      <h2>{myPlayerNumber}</h2> {/* Display the player number */}
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