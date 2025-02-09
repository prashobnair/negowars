import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [myPlayerNumber, setMyPlayerNumber] = useState(null);
    const [roomId, setRoomId] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [offerAmount, setOfferAmount] = useState('');
    const [isObjectivesModalOpen, setIsObjectivesModalOpen] = useState(false);
    const socketRef = useRef(null);
    const myPlayerNumberRef = useRef(null);
    const [playerRole, setPlayerRole] = useState(null);
    const [isGameOverModalOpen, setIsGameOverModalOpen] = useState(false);
    const [gameOverMessage, setGameOverMessage] = useState(null);

    // --- State for Current Offer ---
    const [currentSalaryOffer, setCurrentSalaryOffer] = useState(null);
    const [currentBonusOffer, setCurrentBonusOffer] = useState(null);
    const [currentRemoteDaysOffer, setCurrentRemoteDaysOffer] = useState(null);

    // --- State for Offer Modal Input ---
    const [modalSalary, setModalSalary] = useState('');
    const [modalBonus, setModalBonus] = useState('');
    const [modalRemoteDays, setModalRemoteDays] = useState('');

    // --- State for Timer ---
    const [timeLeft, setTimeLeft] = useState(7 * 60); // 7 minutes in seconds

    // --- Game Over State ---
    const [candidateScore, setCandidateScore] = useState(null);
    const [hrScore, setHrScore] = useState(null);
    const [opponentBonusObjective, setOpponentBonusObjective] = useState(null); // e.g., "debt", "quick"


    // --- Define Objectives (Hardcoded for MVP) ---
    const candidatePrimaryObjectives = [
        "Achieve a base salary of at least $65,000.",
        "Secure a sign-on bonus of at least $5,000.",
        "Obtain at least 2 remote work days per week.",
    ];
    const candidateBonusObjectives = [
      {
        id: "debt",
        description: "Personal Debt: Secure a sign-on bonus of at least $7,000.",
        bonus: "+30 points if achieved",
      },
    ];

    const hrPrimaryObjectives = [
        "Keep the base salary at or below $70,000.",
        "Limit the sign-on bonus to a maximum of $8,000.",
        "Limit remote work days to a maximum of 1 per week",
    ];
    const hrBonusObjectives = [
        {
          id: "budget",
          description: "Budget Hero: Keep the total compensation (salary + bonus) below $76000",
          bonus: "+30 points if achieved",
        },
      ];

    // --- State for storing the selected bonus objective ---
    const [bonusObjective, setBonusObjective] = useState(null);


    // --- useEffect for WebSocket Connection ---
    useEffect(() => {
        // Prevent multiple connections
        if (socketRef.current) {
            return;
        }

        socketRef.current = new WebSocket('ws://localhost:8000/ws');
        
        socketRef.current.onopen = () => {
            console.log('WebSocket connected');
        };

        socketRef.current.onmessage = (event) => {
            const parts = event.data.split("|");
            const messageType = parts[0];

            if (messageType === "init") {
                const playerNumber = parts[1];
                const roomId = parts[2];
                setMyPlayerNumber(playerNumber);
                setRoomId(roomId);
                myPlayerNumberRef.current = playerNumber;
                
            } else if (messageType === "role") {
                const role = parts[1];
                setPlayerRole(role);

                const bonusObjectives = role === "candidate" ? candidateBonusObjectives : hrBonusObjectives;
                const randomIndex = Math.floor(Math.random() * bonusObjectives.length);
                setBonusObjective(bonusObjectives[randomIndex]);

                setMessages((prev) => [...prev, { player: myPlayerNumberRef.current, text: `You are ${role.charAt(0).toUpperCase() + role.slice(1)}`, sender: "system" }]);

            } else if (messageType === "ack") {
                const [_, messageId, playerNumber, messageContent] = parts;
                setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
            } else if (messageType === "msg") {
                const sender = parts[2];
                const text = parts.slice(3).join("|");
                console.log("Received chat message from:", sender, "text:", text);
                setMessages((prev) => [
                    ...prev,
                    {
                        player: sender,
                        text: text,
                        sender: sender === myPlayerNumberRef.current ? 'me' : 'other',
                        role: Number(sender) % 2 !== 0 ? 'Candidate' : 'Hr',
                    }
                ]);
            }  else if (messageType === "offer") {
                const [_, messageId, playerNumber, messageContent] = parts;
                const sender = playerNumber === myPlayerNumberRef.current ? "me" : "other";
                
                // --- Parse Offer Details ---
                const offerParts = messageContent.split(",");
                const salaryPart = offerParts.find(part => part.trim().startsWith("Offer:"));
                const bonusPart = offerParts.find(part => part.trim().startsWith("Bonus:"));
                const remoteDaysPart = offerParts.find(part => part.trim().startsWith("Remote Days:"));

                if (salaryPart) {
                    const salaryString = salaryPart.split(":")[1].replace(/[^0-9]/g, '');
                    const salary = parseInt(salaryString, 10);
                    if (!isNaN(salary)) {
                        setCurrentSalaryOffer(salary);
                    }
                }

                if (bonusPart) {
                    const bonusString = bonusPart.split(":")[1].replace(/[^0-9]/g, '');
                    const bonus = parseInt(bonusString, 10);
                    if (!isNaN(bonus)) {
                        setCurrentBonusOffer(bonus);
                    }
                }

                if (remoteDaysPart) {
                    const remoteDaysString = remoteDaysPart.split(":")[1].replace(/[^0-9]/g, '');
                    const remoteDays = parseInt(remoteDaysString, 10);
                    if (!isNaN(remoteDays)) {
                        setCurrentRemoteDaysOffer(remoteDays);
                    }
                }
            } else if (messageType === "gameover") {
                const [_, messageId, outcome, candidateScore, hrScore, candidateBonus, hrBonus] = parts;
                console.log("Game Over Message Parts:", {
                    outcome,
                    candidateScore,
                    hrScore,
                    candidateBonus,
                    hrBonus,
                    playerRole
                });
                
                // Make sure we're using the correct playerRole
                const currentRole = playerRole || (Number(myPlayerNumberRef.current) % 2 !== 0 ? "candidate" : "hr");
                
                setGameOverMessage(outcome);
                setCandidateScore(candidateScore);
                setHrScore(hrScore);
                setOpponentBonusObjective(currentRole === "candidate" ? hrBonus : candidateBonus);
                setIsGameOverModalOpen(true);
                
                // Only reset the modal input states
                setModalSalary('');
                setModalBonus('');
                setModalRemoteDays('');
            } else if (messageType === "error") {
                const errorMessage = parts.slice(1).join("|");
                alert(errorMessage);  // Or handle the error in a more user-friendly way
            }
        };

        socketRef.current.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            socketRef.current = null;
        };

        socketRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }, []); // Empty dependency array

    // --- useEffect for Timer ---
    useEffect(() => {
        let timerInterval;
        if (timeLeft > 0) {
            timerInterval = setInterval(() => {
                setTimeLeft((prevTime) => prevTime - 1);
            }, 1000); // Decrement every 1000ms (1 second)
        } else {
            // When timer reaches 0, send "gameover" message
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send("gameover|timeout|Game Over! Negotiation timed out."); // Use consistent format
            }
        }

        // Cleanup function: clear the interval when the component unmounts or timeLeft changes
        return () => clearInterval(timerInterval);
    }, [timeLeft, socketRef]);

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
        // Initialize modal input fields with current offer values (or defaults)
        setModalSalary(currentSalaryOffer !== null ? currentSalaryOffer : '');
        setModalBonus(currentBonusOffer !== null ? currentBonusOffer : '');
        setModalRemoteDays(currentRemoteDaysOffer !== null ? currentRemoteDaysOffer : '');

    };

    const handleObjectives = () => {
        setIsObjectivesModalOpen(true);
    };

    const handleSubmitOffer = () => {
        // Input validation
        const salary = parseInt(modalSalary);
        const bonus = parseInt(modalBonus);
        const remoteDays = parseInt(modalRemoteDays);

        // Validate salary
        if (isNaN(salary) || salary < 0 || salary > 1000000 || !Number.isInteger(salary)) {
            alert("Base salary must be a whole number between $0 and $1,000,000");
            return;
        }

        // Validate bonus
        if (isNaN(bonus) || bonus < 0 || bonus > 10000 || !Number.isInteger(bonus)) {
            alert("Sign-on bonus must be a whole number between $0 and $10,000");
            return;
        }

        // Validate remote days
        if (isNaN(remoteDays) || remoteDays < 0 || remoteDays > 5 || !Number.isInteger(remoteDays)) {
            alert("Remote work days must be a whole number between 0 and 5");
            return;
        }

        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            const offerMessage = `offer:${salary},${bonus},${remoteDays}`;
            socketRef.current.send(offerMessage);
        }

        setIsOfferModalOpen(false);
    };

    const handleCancelOffer = () => {
        setIsOfferModalOpen(false);
        // No need to reset individual offer states here; they're managed by the modal
    };

    const handleCloseObjectives = () => {
        setIsObjectivesModalOpen(false);
    }
    const handleCloseGameOver = () => {
        setIsGameOverModalOpen(false);
        resetGameState(); // Reset all states when modal is closed
    };

    // --- Helper function to format time ---
    const formatTime = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
    };

    // Add these helper functions at the top level of the App component
    const getBonusObjectiveDescription = (objectiveId, role) => {
        console.log("Getting bonus objective description:", { objectiveId, role });
        
        if (!objectiveId) {
            console.log("No objectiveId provided");
            return "N/A";
        }
        
        // Determine role if not provided
        const currentRole = role || (Number(myPlayerNumberRef.current) % 2 !== 0 ? "candidate" : "hr");
        
        if (currentRole === "candidate") {
            const hrObjective = hrBonusObjectives.find(obj => obj.id === objectiveId);
            console.log("Found HR objective:", hrObjective);
            return hrObjective ? hrObjective.description : "N/A";
        } else if (currentRole === "hr") {
            const candidateObjective = candidateBonusObjectives.find(obj => obj.id === objectiveId);
            console.log("Found candidate objective:", candidateObjective);
            return candidateObjective ? candidateObjective.description : "N/A";
        }
        return "N/A";
    };

    // Add this new function to reset game-related states
    const resetGameState = () => {
        // Reset current offer states
        setCurrentSalaryOffer(null);
        setCurrentBonusOffer(null);
        setCurrentRemoteDaysOffer(null);
        
        // Reset offer modal states
        setModalSalary('');
        setModalBonus('');
        setModalRemoteDays('');
        
        // Reset game over states
        setGameOverMessage(null);
        setCandidateScore(null);
        setHrScore(null);
        setOpponentBonusObjective(null);
        
        // Reset modals
        setIsOfferModalOpen(false);
        setIsObjectivesModalOpen(false);
        setIsGameOverModalOpen(false);
        
        // Reset messages
        setMessages([]);
    };

    return (
        <div className="chat-container">
            <h1>NegoWars (MVP)</h1>
            <div className="room-info">
                <p>Room #{roomId || "..."}</p>
            </div>

            {/* --- Display Timer --- */}
            <div className="round-info">
                <p>Time Left: {formatTime(timeLeft)}</p>
            </div>

            {/* --- Current Offer Display --- */}
            <div className="current-offer">
                <h2>Current Offer</h2>
                <p>Base Salary: ${currentSalaryOffer !== null ? currentSalaryOffer.toLocaleString() : "N/A"}</p>
                <p>Sign-On Bonus: ${currentBonusOffer !== null ? currentBonusOffer.toLocaleString() : "N/A"}</p>
                <p>Remote Work Days Per Week: {currentRemoteDaysOffer !== null ? currentRemoteDaysOffer : "N/A"}</p>
            </div>

            <div className="message-list">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender === 'me' ? 'my-message' : msg.sender === 'system' ? 'system-message' : 'other-message'}`}>
                        {msg.sender !== "system" && (
                            <span className="message-player">
                            {msg.sender === 'me' ? 
                                playerRole.charAt(0).toUpperCase() + playerRole.slice(1) : 
                                msg.role}: 
                        </span>
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
                    onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          sendMessage();
                        }
                      }}
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
                        <label htmlFor="modalSalary">Base Salary:</label>
                        <input
                            type="number"
                            id="modalSalary"
                            value={modalSalary}
                            onChange={(e) => setModalSalary(e.target.value)}
                            className="modal-input"
                        />
                        <label htmlFor="modalBonus">Sign-On Bonus:</label>
                        <input
                            type="number"
                            id="modalBonus"
                            value={modalBonus}
                            onChange={(e) => setModalBonus(e.target.value)}
                            className="modal-input"
                        />
                        <label htmlFor="modalRemoteDays">Remote Work Days Per Week:</label>
                        <input
                            type="number"
                            id="modalRemoteDays"
                            value={modalRemoteDays}
                            onChange={(e) => setModalRemoteDays(e.target.value)}
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
                        
                        {playerRole === "candidate" && (
                            <div>
                                <h3>Primary Objectives:</h3>
                                <ul>
                                    {candidatePrimaryObjectives.map((objective, index) => (
                                        <li key={index}>{objective}</li>
                                    ))}
                                </ul>
                                <h3>Bonus Objective:</h3>
                                <p>{bonusObjective.description}</p>
                                <p>Bonus: {bonusObjective.bonus}</p>
                            </div>
                        )}
                        {playerRole === "hr" && (
                            <div>
                                <h3>Primary Objectives:</h3>
                                <ul>
                                    {hrPrimaryObjectives.map((objective, index) => (
                                        <li key={index}>{objective}</li>
                                    ))}
                                </ul>
                                <h3>Bonus Objective:</h3>
                                <p>{bonusObjective.description}</p>
                                <p>Bonus: {bonusObjective.bonus}</p>
                            </div>
                        )}
                        <div className="modal-buttons">
                            <button onClick={handleCloseObjectives} className="modal-button modal-cancel">Close</button>
                        </div>
                    </div>
                </div>
            )}
            {/* --- Game Over Modal --- */}
            {isGameOverModalOpen && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h2>Game Over</h2>
                        <p>{gameOverMessage}</p>
                        {/* Display Scores */}
                        <p>Candidate Score: {candidateScore !== null ? candidateScore : "N/A"}</p>
                        <p>HR Score: {hrScore !== null ? hrScore : "N/A"}</p>

                        {/* Display Opponent's Bonus Objective (if game ended successfully)*/}
                        {gameOverMessage && !gameOverMessage.includes("timed out") && (
                            <>
                                <h3>Final Terms:</h3>
                                <p>Base Salary: ${currentSalaryOffer !== null ? currentSalaryOffer.toLocaleString() : "N/A"}</p>
                                <p>Sign-On Bonus: ${currentBonusOffer !== null ? currentBonusOffer.toLocaleString() : "N/A"}</p>
                                <p>Remote Work Days: {currentRemoteDaysOffer !== null ? currentRemoteDaysOffer : "N/A"}</p>
                                <h3>Opponent's Bonus Objective:</h3>
                                <p>{getBonusObjectiveDescription(opponentBonusObjective, playerRole)}</p>
                            </>
                        )}
                        <div className="modal-buttons">
                            <button onClick={handleCloseGameOver} className="modal-button modal-cancel">Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;