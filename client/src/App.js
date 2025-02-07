import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [offerAmount, setOfferAmount] = useState('');
    const socketRef = useRef(null);

    useEffect(() => {
        if (!socketRef.current) {
            socketRef.current = new WebSocket('ws://localhost:8000/ws');

            socketRef.current.onopen = () => {
                console.log('WebSocket connected');
            };

            socketRef.current.onmessage = (event) => {
                console.log('Received:', event.data);
                const parts = event.data.split("|"); // Changed to pipe delimiter
                const messageType = parts[0];
              
                if (messageType === "init") {
                  const playerNumber = parts[1];
                  setMyPlayerNumber(playerNumber);
                } else if (messageType === "ack" || messageType === "msg" || messageType === "offer") {
                  const [_, messageId, playerNumber, messageContent] = parts;
                  setMessages((prev) => [...prev, {
                    player: playerNumber,
                    text: messageContent,
                    sender: messageType === "ack" ? "me" : "other"
                  }]);
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

    const handleAccept = () => {
        console.log("Accept button clicked");
    };

    const handleOffer = () => {
        setIsOfferModalOpen(true);
    };

    const handleObjectives = () => {
        console.log("Objectives button clicked");
    };

    const handleSubmitOffer = () => {
        // --- Send offer to backend ---
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(`offer:${offerAmount}`); // format: "offer:<amount>"
        }

        setIsOfferModalOpen(false);
        setOfferAmount('');
    };

    const handleCancelOffer = () => {
        setIsOfferModalOpen(false);
        setOfferAmount('');
    };


    return (
        <div className="chat-container">
            <h1>NegoWars Chat (MVP)</h1>
             {myPlayerNumber && <h2>You are Player {myPlayerNumber}</h2>} {/* Display player number */}
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
            <div className="action-buttons">
                <button onClick={handleAccept} className="action-button">Accept</button>
                <button onClick={handleOffer} className="action-button">Offer</button>
                <button onClick={handleObjectives} className="action-button">Objectives</button>
            </div>

            {/* --- Offer Modal --- */}
            {isOfferModalOpen && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>Make an Offer</h2>
                        <label htmlFor="offerAmount">Salary Offer:</label>
                        <input
                            type="number"
                            id="offerAmount"
                            value={offerAmount}
                            onChange={(e) => setOfferAmount(e.target.value)}
                            className="modal-input"
                        />
                        <div className="modal-buttons">
                            <button onClick={handleSubmitOffer} className="modal-button modal-submit">Submit</button>
                            <button onClick={handleCancelOffer} className="modal-button modal-cancel">Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;