import React, { useState, useEffect, useRef } from 'react';
import './App.css'; // Import the CSS file

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
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
                } else if (messageType === "ack") {
                    const messageId = parts[1];
                    const playerNumber = parts[2];
                    const messageContent = parts[3];
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]); // Store player and sender info
                } else if (messageType === "msg") {
                    const messageId = parts[1];
                    const playerNumber = parts[2];
                    const messageContent = parts[3];
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "other" }]); // Store player and sender info
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
        <div className="chat-container">
            <h1>NegoWars Chat (MVP)</h1>
            <h2>{myPlayerNumber}</h2>
            <div className="message-list">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender === 'me' ? 'my-message' : 'other-message'}`}>
                        <span className="message-player">Player {msg.player}: </span>
                        <span className="message-text">{msg.text}</span>
                    </div>
                ))}
            </div>
            <div className="input-area">
                <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    className="message-input"
                />
                <button onClick={sendMessage} className="send-button">Send</button>
            </div>
        </div>
    );
}

export default App;