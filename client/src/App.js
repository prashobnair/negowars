import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [offerAmount, setOfferAmount] = useState('');
    const [isObjectivesModalOpen, setIsObjectivesModalOpen] = useState(false); // NEW: State for Objectives modal
    const socketRef = useRef(null);
    const myPlayerNumberRef = useRef(null);

    useEffect(() => {
        if (!socketRef.current) {
            socketRef.current = new WebSocket('ws://localhost:8000/ws');

            socketRef.current.onopen = () => {
                console.log('WebSocket connected');
            };

            socketRef.current.onmessage = (event) => {
                const parts = event.data.split("|");
                const messageType = parts[0];

                if (messageType.startsWith("init")) {
                    const playerNumber = messageType.split(":")[1];
                    setMyPlayerNumber(playerNumber);
                    myPlayerNumberRef.current = playerNumber;
                    setMessages((prev) => [...prev, { player: playerNumber, text: `You are Player ${playerNumber}`, sender: "system" }]);
                } else if (messageType === "ack") {
                    const [_, messageId, playerNumber, messageContent] = parts;
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
                } else if (messageType === "msg") {
                    const [_, messageId, playerNumber, messageContent] = parts;
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "other" }]);
                } else if (messageType === "offer") {
                    const [_, messageId, playerNumber, messageContent] = parts;
                    const sender = playerNumber === myPlayerNumberRef.current ? "me" : "other";
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: sender }]);
                } else if (messageType === "gameover") {
                    const [_, messageId, messageContent] = parts;
                    setMessages((prev) => [...prev, { player: null, text: messageContent, sender: "system" }]);
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
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send("accept");
        }
    };

    const handleOffer = () => {
        setIsOfferModalOpen(true);
    };

    const handleObjectives = () => {
        // --- Open the Objectives modal ---
        setIsObjectivesModalOpen(true);
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

    // --- Handler for closing the Objectives modal ---
    const handleCloseObjectives = () => {
        setIsObjectivesModalOpen(false);
    }

    return (
        <div className="chat-container">
            <h1>NegoWars (MVP)</h1>
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

            {/* --- Offer Modal (Existing) --- */}
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

            {/* --- Objectives Modal (NEW) --- */}
            {isObjectivesModalOpen && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>Objectives</h2>
                        <p>Placeholder for objectives...</p> {/* Placeholder content */}
                        <div className="modal-buttons">
                            <button onClick={handleCloseObjectives} className="modal-button modal-cancel">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;