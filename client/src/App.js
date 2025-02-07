import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false); // Add modal state
    const [offerAmount, setOfferAmount] = useState(''); // Add offer amount state
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
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
                } else if (messageType === "msg") {
                    const messageId = parts[1];
                    const playerNumber = parts[2];
                    const messageContent = parts[3];
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "other" }]);
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
        setIsOfferModalOpen(true); // Open the modal
    };

    const handleObjectives = () => {
        console.log("Objectives button clicked");
    };

    // --- Modal Handlers ---
    const handleSubmitOffer = () => {
        console.log("Offer submitted:", offerAmount);
        setIsOfferModalOpen(false); // Close the modal
        setOfferAmount(''); // Reset the offer amount
    };

    const handleCancelOffer = () => {
        setIsOfferModalOpen(false); // Close the modal
        setOfferAmount(''); // Reset the offer amount
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