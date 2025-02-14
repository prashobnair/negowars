import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { motion, AnimatePresence } from 'framer-motion';
import { FaBullseye, FaCheck, FaClock, FaMoneyCheckAlt, FaHandshake } from 'react-icons/fa';

function App() {
    const [messages, setMessages] = useState([]);
    const [messageInput, setMessageInput] = useState('');
    const [roomId, setRoomId] = useState(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
    const [isObjectivesModalOpen, setIsObjectivesModalOpen] = useState(false);
    const socketRef = useRef(null);
    const myPlayerNumberRef = useRef(null);
    const [playerRole, setPlayerRole] = useState(null);
    const [isGameOverModalOpen, setIsGameOverModalOpen] = useState(false);
    const [gameOverMessage, setGameOverMessage] = useState(null);
    const [lastOfferSender, setLastOfferSender] = useState(null);

    // --- State for Current Offer ---
    const [currentSalaryOffer, setCurrentSalaryOffer] = useState(null);
    const [currentBonusOffer, setCurrentBonusOffer] = useState(null);
    const [currentRemoteDaysOffer, setCurrentRemoteDaysOffer] = useState(null);

    // --- State for Offer Modal Input ---
    const [modalSalary, setModalSalary] = useState('');
    const [modalBonus, setModalBonus] = useState('');
    const [modalRemoteDays, setModalRemoteDays] = useState('');

    // --- State for Timer ---
    const [timeLeft, setTimeLeft] = useState(7 * 60); // Set your desired timer duration
    const [isTimerRunning, setIsTimerRunning] = useState(false); // State to manage timer

    // --- Game Over State ---
    const [candidateScore, setCandidateScore] = useState(null);
    const [hrScore, setHrScore] = useState(null);
    const [opponentBonusObjective, setOpponentBonusObjective] = useState(null); // e.g., "debt", "quick"

    // --- State for Chat Disabled ---
    const [isChatDisabled, setIsChatDisabled] = useState(false);

    // --- State for Offer Button Disabled ---
    const [isOfferDisabled, setIsOfferDisabled] = useState(true); // Initially disable the offer button

    const [isLoading, setIsLoading] = useState(false);

    const [isPulsing, setIsPulsing] = useState(false);


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

    const messageListRef = useRef(null); // Create a ref for the message list

    const [isTyping, setIsTyping] = useState(false);
    const [isPartnerTyping, setIsPartnerTyping] = useState(false);
    const typingTimeout = useRef();

    // useEffect to scroll to the bottom whenever messages change
    useEffect(() => {
        if (messageListRef.current) {
            messageListRef.current.scrollTop = messageListRef.current.scrollHeight; // Scroll to the bottom
        }
    }, [messages]); // Dependency on messages

    // --- useEffect for WebSocket Connection ---
    useEffect(() => {
        // Prevent multiple connections
        if (socketRef.current) {
            return;
        }

        socketRef.current = new WebSocket('ws://localhost:8000/ws');
        setIsLoading(true);

        socketRef.current.onopen = () => {
            setIsLoading(false); // Set loading to false when connected
            console.log('WebSocket connected');
        };

        socketRef.current.onmessage = (event) => {
            const parts = event.data.split("|");
            const messageType = parts[0];

            console.log("Received message:", { messageType, parts });

            if (messageType === "init") {
                const playerNumber = parts[1];
                const roomId = parts[2];
                myPlayerNumberRef.current = playerNumber;
                setRoomId(roomId);
                
            } else if (messageType === "role") {
                const role = parts[1];
                setPlayerRole(role);
                console.log(`Player role set to: ${role}`); // Log role assignment

                const bonusObjectives = role === "candidate" ? candidateBonusObjectives : hrBonusObjectives;
                const randomIndex = Math.floor(Math.random() * bonusObjectives.length);
                setBonusObjective(bonusObjectives[randomIndex]);

                setMessages((prev) => [...prev, { player: myPlayerNumberRef.current, text: `You are ${role.charAt(0).toUpperCase() + role.slice(1)}`, sender: "system" }]);

            } else if (messageType === "waiting") {
                const message = parts[1];
                console.log(`Waiting message received: ${message}`); // Log waiting message
                setMessages((prev) => [...prev, { player: "system", text: message, sender: "system" }]);
            } else if (messageType === "chat_disabled") {
                console.log("Chat disabled message received."); // Log chat disabled message
                setIsChatDisabled(true); // Disable chat input
                setIsOfferDisabled(true); // Disable offer button
            } else if (messageType === "player_connected") {
                const message = "A second player has connected. You can start the negotiation now.";
                console.log(message); // Log player connected message
                setMessages((prev) => [...prev, { player: "system", text: message, sender: "system" }]);
                setIsChatDisabled(false); // Enable chat input
                setIsOfferDisabled(false); // Enable offer button
            } else if (messageType === "start_timer") {
                console.log("Timer start message received."); // Log timer start message
                setIsTimerRunning(true); // Start the timer
                setTimeLeft(7 * 60); // Reset timer duration if needed
            } else if (messageType === "ack") {
                const [_, messageId, playerNumber, messageContent] = parts;
                setMessages((prev) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
            } else if (messageType === "msg") {
                const sender = parts[2];
                const text = parts.slice(3).join("|");

                setIsPartnerTyping(false); // Clear typing indicator when message received
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
                console.log("Offer received:", { messageId, playerNumber, messageContent });

                setLastOfferSender(() => playerNumber); // Use functional update
                
                // --- Parse Offer Details ---
                const offerParts = messageContent.split(",").map(part => part.split(":"));
                const offerDetails = Object.fromEntries(offerParts);
                
                const salary = offerDetails.salary;
                const bonus = offerDetails.bonus;
                const remote_days = offerDetails.remote_days;

                console.log("Parsed offer details:", { salary, bonus, remote_days });
                
                // Convert to numbers and update state
                const parsedSalary = parseInt(salary, 10);
                const parsedBonus = parseInt(bonus, 10);
                const parsedRemoteDays = parseInt(remote_days, 10);
                
                console.log("Parsed offer values:", { parsedSalary, parsedBonus, parsedRemoteDays });
                
                if (!isNaN(parsedSalary)) {
                    setCurrentSalaryOffer(parsedSalary);
                }
                if (!isNaN(parsedBonus)) {
                    setCurrentBonusOffer(parsedBonus);
                }
                if (!isNaN(parsedRemoteDays)) {
                    setCurrentRemoteDaysOffer(parsedRemoteDays);
                }
                
                // Add a message to the chat
                setMessages((prev) => [
                    ...prev,
                    {
                        player: playerNumber,
                        text: `New offer: $${parsedSalary.toLocaleString()} salary, $${parsedBonus.toLocaleString()} bonus, ${parsedRemoteDays} remote days`,
                        sender: playerNumber === myPlayerNumberRef.current ? 'me' : 'other',
                        role: Number(playerNumber) % 2 !== 0 ? 'Candidate' : 'Hr',
                    }
                ]);
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
            } else if (messageType === "typing") {
                    const isTypingStatus = parts[1].toLowerCase(); 
                    setIsPartnerTyping(isTypingStatus === 'true'); 
                    return; 
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
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // --- useEffect for Timer ---
    useEffect(() => {
        let timerInterval;
        if (isTimerRunning && timeLeft > 0) {
            timerInterval = setInterval(() => {
                setTimeLeft((prevTime) => prevTime - 1);
            }, 1000); // Decrement every 1000ms (1 second)
        } else if (timeLeft === 0) {
            // When timer reaches 0, send "gameover" message
            if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send("gameover|timeout|Game Over! Negotiation timed out."); // Use consistent format
            }
        }

        // Cleanup function: clear the interval when the component unmounts or timeLeft changes
        return () => clearInterval(timerInterval);
    }, [isTimerRunning, timeLeft]); // Add isTimerRunning and timeLeft to dependencies

    // Add this effect to handle red phase pulsing
    useEffect(() => {
        if (timeLeft <= 60 && !isPulsing) {
        setIsPulsing(true);
        } else if (timeLeft > 60 && isPulsing) {
        setIsPulsing(false);
        }
    }, [timeLeft, isPulsing]);
  

    const sendMessage = () => {
        if (messageInput.trim() && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(messageInput);
            setMessageInput(''); // Clear input after sending
            setIsTyping(false); // Reset typing status
            socketRef.current.send("typing:false"); // Inform server typing stopped
            clearTimeout(typingTimeout.current); // Clear any pending typing timeout
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

    const handleInputChange = (e) => {
        setMessageInput(e.target.value);
        
        // Only send typing status if we weren't already typing
        if (!isTyping && e.target.value.trim()) {
            socketRef.current.send("typing:true");
            setIsTyping(true);
        }
        
        // Clear previous timeout
        clearTimeout(typingTimeout.current);
        
        // Set new timeout
        typingTimeout.current = setTimeout(() => {
            if (isTyping) {
                setIsTyping(false);
                socketRef.current.send("typing:false");
            }
        }, 1000);
        
        // If input is empty, stop typing immediately
        if (!e.target.value.trim() && isTyping) {
            setIsTyping(false);
            socketRef.current.send("typing:false");
            clearTimeout(typingTimeout.current);
        }
    };

    const handleObjectives = () => {
        setIsObjectivesModalOpen(true);
    };
    

    const handleSubmitOffer = () => {
        console.log("Submit offer clicked");
        console.log("Current values:", { modalSalary, modalBonus, modalRemoteDays });

        // Input validation
        const salary = parseInt(modalSalary);
        const bonus = parseInt(modalBonus);
        const remote_days = parseInt(modalRemoteDays);

        console.log("Parsed values:", { salary, bonus, remote_days });

        // Validate salary
        if (isNaN(salary) || salary < 0 || salary > 1000000 || !Number.isInteger(salary)) {
            console.log("Salary validation failed");
            alert("Base salary must be a whole number between $0 and $1,000,000");
            return;
        }

        // Validate bonus
        if (isNaN(bonus) || bonus < 0 || bonus > 10000 || !Number.isInteger(bonus)) {
            console.log("Bonus validation failed");
            alert("Sign-on bonus must be a whole number between $0 and $10,000");
            return;
        }

        // Validate remote days
        if (isNaN(remote_days) || remote_days < 0 || remote_days > 5 || !Number.isInteger(remote_days)) {
            console.log("Remote days validation failed");
            alert("Remote work days must be a whole number between 0 and 5");
            return;
        }

        console.log("All validations passed");
        console.log("WebSocket state:", {
            exists: !!socketRef.current,
            readyState: socketRef.current?.readyState,
            OPEN: WebSocket.OPEN
        });

        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            const offerMessage = `offer:${salary},${bonus},${remote_days}`;
            console.log("Sending offer message:", offerMessage);
            socketRef.current.send(offerMessage);
            console.log("Offer message sent");

            // Update local state when sending offer
            setCurrentSalaryOffer(salary);
            setCurrentBonusOffer(bonus);
            setCurrentRemoteDaysOffer(remote_days);
            setLastOfferSender(myPlayerNumberRef.current);
        } else {
            console.log("WebSocket not ready");
        }

        setIsOfferModalOpen(false);
        console.log("Offer modal closed");
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
            <div className="header">
                <div className="status-badge">
                    <span className="room-id">Room #{roomId}</span>
                </div>
                <div className="timer">
                    <div className={`timer-progress ${isPulsing ? 'pulse' : ''}`}>
                        <svg width="48" height="48">
                        <circle
                            cx="24"
                            cy="24"
                            r="20"
                            className="timer-base"
                            strokeWidth="4"
                        />
                        <circle
                            cx="24"
                            cy="24"
                            r="20"
                            className={`timer-fill ${
                            timeLeft > 240 ? 'green' : 
                            timeLeft > 60 ? 'orange' : 
                            'red'
                            }`}
                            strokeWidth="4"
                            strokeDasharray={`${(timeLeft / 420) * 126} 126`}
                            transform="rotate(-90 24 24)"
                        />
                        </svg>
                    </div>
                    <span className="timer-text">{formatTime(timeLeft)}</span>
                </div>


            </div>

            {/* --- Current Offer Display --- */}
            <div className="current-offer">
                <h2><strong>Current Offer:</strong></h2>
                <p>Base Salary: ${currentSalaryOffer !== null ? currentSalaryOffer.toLocaleString() : "N/A"}</p>
                <p>Sign-On Bonus: ${currentBonusOffer !== null ? currentBonusOffer.toLocaleString() : "N/A"}</p>
                <p>Remote Work Days Per Week: {currentRemoteDaysOffer !== null ? currentRemoteDaysOffer : "N/A"}</p>
            </div>
            
            <div className="message-list" ref={messageListRef}>
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.sender === 'me' ? 'my-message' : msg.sender === 'system' ? 'system-message' : 'other-message'}`}>
                        
                        <span className="message-text">{msg.text}</span>
                    </div>
                ))}
                {isPartnerTyping && (
                    <div className="typing-bubble">
                        <div className="dot"></div>
                        <div className="dot"></div>
                        <div className="dot"></div>
                    </div>
                )}
            </div>
            <div className="input-action-group">
                <div className="input-area">
                    <input
                        type="text"
                        value={messageInput}
                        onChange={handleInputChange}
                        onKeyPress={(e) => {
                        if (e.key === 'Enter' && !isChatDisabled) {
                            sendMessage();
                        }
                        }}
                        className="message-input"
                        disabled={isChatDisabled}
                        placeholder="Type your message..."
                    />
                    <button 
                        onClick={sendMessage} 
                        className="send-button" 
                        disabled={isChatDisabled}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
                <div className="action-buttons">
                    <button 
                        onClick={handleAccept} 
                        className="action-button accept"
                        disabled={!currentSalaryOffer || !lastOfferSender || lastOfferSender === myPlayerNumberRef.current}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                        Accept
                    </button>
                    <button 
                        onClick={handleOffer} 
                        className="action-button offer"
                        disabled={isOfferDisabled}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                        </svg>
                        Offer
                    </button>
                    <button 
                        onClick={handleObjectives} 
                        className="action-button objectives"
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                        </svg>
                        Objectives
                    </button>
                </div>
            </div>
            <AnimatePresence>
                {isOfferModalOpen && (
                
                    <motion.div
                    className="modal-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }} // Optional: Add a transition duration
                    style={{position: 'fixed', top: '0', left:'0', width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'}}
                    >
                    <motion.div
                        className="modal"
                        initial={{ y: 50, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: 50, opacity: 0 }}
                        transition={{ duration: 0.2 }} // Optional: Add a transition duration
                        style={{backgroundColor: 'white', padding: '20px', borderRadius: '5px'}}
                    >
                        <h2>Make an Offer</h2>
                        <div className="input-group">
                            <label htmlFor="modalSalary">Base Salary ($)</label>
                            <input
                                type="number"
                                id="modalSalary"
                                value={modalSalary}
                                onChange={(e) => setModalSalary(e.target.value)}
                                className="modal-input"
                                placeholder="65000"
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="modalBonus">Sign-On Bonus ($)</label>
                            <input
                                type="number"
                                id="modalBonus"
                                value={modalBonus}
                                onChange={(e) => setModalBonus(e.target.value)}
                                className="modal-input"
                                placeholder="65000"
                            />
                        </div>
                        <div className="input-group">
                            <label htmlFor="modalRemoteDays">Remote Work Days Per Week</label>
                            <input
                                type="number"
                                id="modalRemoteDays"
                                value={modalRemoteDays}
                                onChange={(e) => setModalRemoteDays(e.target.value)}
                                className="modal-input"
                                placeholder="65000"
                            />
                        </div>
                        
                        <div className="modal-buttons">
                            <button 
                                onClick={handleSubmitOffer} 
                                className="modal-button modal-submit"
                            >
                                Submit Offer
                            </button>
                            <button 
                                onClick={handleCancelOffer} 
                                className="modal-button modal-cancel"
                            >
                                Cancel
                            </button>
                        </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
            <AnimatePresence>
            {isObjectivesModalOpen && (
                <motion.div
                    className="modal-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{position: 'fixed', top: '0', left:'0', width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'}}
                >
                    <motion.div
                    className="modal objectives-content"
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 50, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{backgroundColor: 'white', padding: '20px', borderRadius: '5px'}}
                    >
                    <div className="objectives-header">
                        <FaBullseye className="objectives-icon" size={32} color="#2b6cb0" />
                        <h2 className="objectives-title">{playerRole === "candidate" ? "Candidate Objectives" : "HR Objectives"}</h2>
                    </div>

                    <div className="objectives-section">
                        <h3 className="section-title">
                        <FaCheck className="section-icon" /> Primary Goals
                        </h3>
                        <ul className="key-points">
                        {(playerRole === "candidate" ? candidatePrimaryObjectives : hrPrimaryObjectives).map((objective, index) => (
                            <li className="key-point" key={index}>
                            <FaCheck className="key-point-icon" />
                            <span>{objective}</span>
                            </li>
                        ))}
                        </ul>
                    </div>

                    <div className="objectives-section">
                        <h3 className="section-title">
                        <FaMoneyCheckAlt className="section-icon" /> Bonus Objective
                        </h3>
                        <div className="bonus-card">
                        <FaHandshake className="bonus-icon" />
                        <div>
                            <p className="bonus-description">{bonusObjective.description}</p>
                            <p className="bonus-points">{bonusObjective.bonus}</p>
                        </div>
                        </div>
                    </div>

                    <div className="modal-buttons">
                        <button onClick={handleCloseObjectives} className="modal-button modal-cancel">Close</button>
                    </div>
                    </motion.div>
                </motion.div>
            )}

            </AnimatePresence>
            {/* --- Game Over Modal --- */}
            <AnimatePresence>
                {isGameOverModalOpen && (
                    <motion.div
                    className="modal-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{position: 'fixed', top: '0', left:'0', width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center'}}
                >
                    <motion.div
                    className="modal"
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 50, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{backgroundColor: 'white', padding: '20px', borderRadius: '5px'}}
                    >
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
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
            {isLoading && (
                <div className="loading-overlay">
                    <div className="loading-spinner"></div>
                </div>
            )}
        </div>
    );
}

export default App;