import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [offerAmount, setOfferAmount] = useState('');
    const [isObjectivesModalOpen, setIsObjectivesModalOpen] = useState(false);
    const socketRef = useRef(null);
    const myPlayerNumberRef = useRef(null);
    const [playerRole, setPlayerRole] = useState(null); // NEW: Store player's role

    // --- Define Objectives (Hardcoded for MVP) ---
    const candidatePublicObjectives = [
        "Achieve a base salary of at least $65,000 (ideal: $75,000+).",
        "Secure a sign-on bonus of at least $5,000 (ideal: $8,000+).",
        "Obtain at least 2 remote work days per week.",
    ];
    const candidateHiddenObjectives = [
      {
        id: "debt",
        description: "Secret Debt: You have a pressing personal debt.  Secure a sign-on bonus of at least $7,000 for a bonus.",
        bonus: "+30 points if achieved",
      },
      {
        id: "growth",
        description: "Career Growth: You are prioritizing long-term career growth. (Placeholder)",
        bonus: "+20 points (Placeholder)",
      },
    ];

    const hrPublicObjectives = [
        "Keep the base salary at or below $70,000.",
        "Limit the sign-on bonus to a maximum of $8,000.",
        "Minimize remote work days (ideally 0-1).",
        "Keep total compensation (salary + bonus) at or below $80,000."
    ];
    const hrHiddenObjectives = [
        {
          id: "quick",
          description: "Quick Close: Finalize the deal within 3 rounds",
          bonus: "+30 points if achieved",
        },
        {
          id: "budget",
          description: "Budget Hero: Keep the total compensation below $76000",
          bonus: "+30 points if achieved",
        },
      ];

    // --- State for storing the selected hidden objective ---
    const [hiddenObjective, setHiddenObjective] = useState(null);

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
                    const playerNumber = parts[1];
                    setMyPlayerNumber(playerNumber);
                    myPlayerNumberRef.current = playerNumber;
                    // Don't add "You are Player X" message here yet
                } else if (messageType === "role") { // NEW: Handle "role" message
                    const role = parts[1];
                    setPlayerRole(role); // Store the role ("candidate" or "hr")

                    // Randomly select a hidden objective based on the role
                    const hiddenObjectives = role === "candidate" ? candidateHiddenObjectives : hrHiddenObjectives;
                    const randomIndex = Math.floor(Math.random() * hiddenObjectives.length);
                    setHiddenObjective(hiddenObjectives[randomIndex]);

                    // Add "You are Candidate/HR" message *after* receiving role:
                    setMessages((prev) => [...prev, { player: myPlayerNumberRef.current, text: `You are ${role.charAt(0).toUpperCase() + role.slice(1)}`, sender: "system" }]);

                } else if (messageType === "ack") {
                    const [_, messageId, playerNumber, messageContent] = parts;
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
                } else if (messageType === "msg") {
                    const [_, messageId, playerNumber, messageContent] = parts;
                    setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "other" }]);
                }  else if (messageType === "offer") {
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

            {isObjectivesModalOpen && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>Objectives</h2>
                        {playerRole === "candidate" && (
                            <div>
                                <h3>Public Objectives:</h3>
                                <ul>
                                    {candidatePublicObjectives.map((objective, index) => (
                                        <li key={index}>{objective}</li>
                                    ))}
                                </ul>
                                <h3>Hidden Objective:</h3>
                                <p>{hiddenObjective.description}</p>
                                <p>Bonus: {hiddenObjective.bonus}</p>
                            </div>
                        )}
                        {playerRole === "hr" && (
                            <div>
                                <h3>Public Objectives:</h3>
                                <ul>
                                    {hrPublicObjectives.map((objective, index) => (
                                        <li key={index}>{objective}</li>
                                    ))}
                                </ul>
                                <h3>Hidden Objective:</h3>
                                <p>{hiddenObjective.description}</p>
                                <p>Bonus: {hiddenObjective.bonus}</p>
                            </div>
                        )}
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