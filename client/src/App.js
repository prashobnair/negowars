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
                const parts = event.data.split("|");
                const messageType = parts[0];
                let playerNumber = null;
                let messageContent = null;


                if (messageType.startsWith("init")) {
                    playerNumber = parts[1];
                    setMyPlayerNumber(playerNumber);
                    setMessages((prev) => [...prev, { player: playerNumber, text: `You are Player ${playerNumber}`, sender: "system" }]);
                } else if (messageType === "ack") {
                    playerNumber = parts[2];
                    messageContent = parts[3];
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
                } else if (messageType === "msg") {
                    playerNumber = parts[2];
                    messageContent = parts[3];
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "other" }]);
                }  else if (messageType === "offer") {
                    playerNumber = parts[2];
                    messageContent = parts[3];
                    const sender = playerNumber === myPlayerNumber ? "me" : "other";
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: sender }]);
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
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(`offer:${offerAmount}`);
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
            <div className="message-list">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender === 'me' ? 'my-message' : msg.sender === 'system' ? 'system-message' : 'other-message'}`}>
                        {msg.sender !== "system" && (
                            <span className="message-player">Player {msg.player}: </span>
                        )}
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