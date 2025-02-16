// App.tsx
import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { motion, AnimatePresence } from 'framer-motion';
import { FaBullseye, FaCheck, FaMoneyCheckAlt, FaHandshake } from 'react-icons/fa';

// Component Imports
import OfferModal from './components/OfferModal';
import ObjectivesModal from './components/ObjectivesModal';
import GameOverModal from './components/GameOverModal';
import Timer from './components/Timer';
import ErrorBoundary from './components/ErrorBoundary'; // Import ErrorBoundary

// NEW: Import types
import { GameRole, BonusObjective, ChatMessage, Offer, ModalInputs } from './types';


function App() {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [messageInput, setMessageInput] = useState<string>('');
    const [roomId, setRoomId] = useState<string | null>(null);
    const [isOfferModalOpen, setIsOfferModalOpen] = useState<boolean>(false);
    const [isObjectivesModalOpen, setIsObjectivesModalOpen] = useState<boolean>(false);
    const socketRef = useRef<WebSocket | null>(null);
    const myPlayerNumberRef = useRef<string | null>(null);
    const [playerRole, setPlayerRole] = useState<GameRole | null>(null);
    const [isGameOverModalOpen, setIsGameOverModalOpen] = useState<boolean>(false);
    const [gameOverMessage, setGameOverMessage] = useState<string | null>(null);

    // --- Combined Offer State ---
    const [offer, setOffer] = useState<Offer>({
        salary: null,
        bonus: null,
        remoteDays: null,
        lastSender: null
    });

    // --- Combined Modal Input State ---
    const [modalInputs, setModalInputs] = useState<ModalInputs>({
        salary: 0,
        bonus: 0,
        remoteDays: 0
    });

  // --- Combined Validation Setter ---
  const setValidatedModalInput = (field: keyof ModalInputs, value: string) => {
    let numValue = parseInt(value);
    let maxVal: number; // Explicit type
    switch (field) {
      case 'salary':
        maxVal = 1000000;
        break;
      case 'bonus':
        maxVal = 20000;
        break;
      case 'remoteDays':
        maxVal = 5;
        break;
      default:
        return; // Should not happen
    }
    numValue = Math.max(0, Math.min(numValue, maxVal));
    setModalInputs(prevInputs => ({
      ...prevInputs,
      [field]: numValue
    }));
  };

    // --- State for Timer ---
    const [timeLeft, setTimeLeft] = useState<number>(7 * 60);
    const [isTimerRunning, setIsTimerRunning] = useState<boolean>(false);

    // --- Game Over State ---
    const [candidateScore, setCandidateScore] = useState<number | null>(null);
    const [hrScore, setHrScore] = useState<number | null>(null);
    const [opponentBonusObjective, setOpponentBonusObjective] = useState<string | null>(null);

    // --- State for Chat Disabled ---
    const [isChatDisabled, setIsChatDisabled] = useState<boolean>(false);

    // --- State for Offer Button Disabled ---
    const [isOfferDisabled, setIsOfferDisabled] = useState<boolean>(true);

    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isPulsing, setIsPulsing] = useState<boolean>(false);

    // --- Define Objectives (Hardcoded for MVP) ---
    const candidatePrimaryObjectives: string[] = [
        "Achieve a base salary of at least $65,000.",
        "Secure a sign-on bonus of at least $5,000.",
        "Obtain at least 2 remote work days per week.",
    ];
    const candidateBonusObjectives: BonusObjective[] = [
        {
            id: "debt",
            description: "Personal Debt: Secure a sign-on bonus of at least $7,000.",
            bonus: "+30 points if achieved",
        },
    ];

    const hrPrimaryObjectives: string[] = [
        "Keep the base salary at or below $70,000.",
        "Limit the sign-on bonus to a maximum of $8,000.",
        "Limit remote work days to a maximum of 1 per week",
    ];
    const hrBonusObjectives: BonusObjective[] = [
        {
            id: "budget",
            description: "Budget Hero: Keep the total compensation (salary + bonus) below $76000",
            bonus: "+30 points if achieved",
        },
    ];

      // --- State for selected bonus objective ---
  const [bonusObjective, setBonusObjective] = useState<BonusObjective | null>(null);  // Use BonusObjective

  const messageListRef = useRef<HTMLDivElement>(null); // Type the ref

  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isPartnerTyping, setIsPartnerTyping] = useState<boolean>(false);
  const typingTimeout = useRef<NodeJS.Timeout | null>(null); // Type the ref - NodeJS.Timeout in Node.js environment

    const formatCurrency = (value: number) => { // Type the argument
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

    useEffect(() => {
        if (messageListRef.current) {
            messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
        }
    }, [messages, candidateBonusObjectives, hrBonusObjectives, playerRole]);

    useEffect(() => {
    if (socketRef.current) {
      return;
    }

    socketRef.current = new WebSocket('ws://localhost:8000/ws');
    setIsLoading(true);

    socketRef.current.onopen = () => {
      setIsLoading(false);
      console.log('WebSocket connected');
    };

    socketRef.current.onmessage = (event: MessageEvent) => {
      const parts = event.data.split("|");
      const messageType = parts[0];

      console.log("Received message:", { messageType, parts });

      if (messageType === "init") {
        const playerNumber = parts[1];
        const roomId = parts[2];
        myPlayerNumberRef.current = playerNumber;
        setRoomId(roomId);

      } else if (messageType === "role") {
        const role = parts[1] as GameRole; // Type assertion
        setPlayerRole(role);
        const bonusObjectives = role === "candidate" ? candidateBonusObjectives : hrBonusObjectives;
        const randomIndex = Math.floor(Math.random() * bonusObjectives.length);
        setBonusObjective(bonusObjectives[randomIndex]);
        setMessages((prev) => [...prev, { player: myPlayerNumberRef.current as string, text: `You are ${role.charAt(0).toUpperCase() + role.slice(1)}`, sender: "system" }]);

      } else if (messageType === "waiting") {
        const message = parts[1];
        setMessages((prev: ChatMessage[]) => [...prev, { player: "system", text: message, sender: "system" }]);
      } else if (messageType === "chat_disabled") {
          const message = parts[1]; //Get the message
        setIsChatDisabled(true);
        setIsOfferDisabled(true);
        setMessages((prev: ChatMessage[]) => [...prev, { player: "system", text: message, sender: "system" }]); // Add to message
      } else if (messageType === "player_connected") {
        const message = parts[1];
        setMessages((prev: ChatMessage[]) => [...prev, { player: "system", text: message, sender: "system" }]);
        setIsChatDisabled(false);
        setIsOfferDisabled(false);
      } else if (messageType === "start_timer") {
          const message = parts[1];
        setIsTimerRunning(true);
        setTimeLeft(7 * 60);
        setMessages((prev: ChatMessage[]) => [...prev, { player: "system", text: message, sender: "system" }]);
      } else if (messageType === "ack") {
        const [_, messageId, playerNumber, messageContent] = parts;
        setMessages((prev: ChatMessage[]) => [...prev, { player: playerNumber, text: messageContent, sender: "me" }]);
      } else if (messageType === "msg") {
        const sender = parts[2];
        const text = parts.slice(3).join("|");

        setIsPartnerTyping(false);
        setMessages((prev: ChatMessage[]) => [
          ...prev,
          {
            player: sender,
            text: text,
            sender: sender === myPlayerNumberRef.current ? 'me' : 'other',
            role: Number(sender) % 2 !== 0 ? 'Candidate' : 'Hr',
          }
        ]);
      } else if (messageType === "offer") {
        const [_, messageId, playerNumber, messageContent] = parts;
        console.log("Offer received:", { messageId, playerNumber, messageContent });

        setOffer(prevOffer => ({
          ...prevOffer,
          lastSender: playerNumber
        }));

        const offerParts = messageContent.split(",").map((part: string) => part.split(":"));
        const offerDetails = Object.fromEntries(offerParts);

        const salary = offerDetails.salary;
        const bonus = offerDetails.bonus;
        const remote_days = offerDetails.remote_days;

        const parsedSalary = parseInt(salary, 10);
        const parsedBonus = parseInt(bonus, 10);
        const parsedRemoteDays = parseInt(remote_days, 10);

        setOffer(prevOffer => ({
          ...prevOffer,
          salary: !isNaN(parsedSalary) ? parsedSalary : prevOffer.salary,
          bonus: !isNaN(parsedBonus) ? parsedBonus : prevOffer.bonus,
          remoteDays: !isNaN(parsedRemoteDays) ? parsedRemoteDays : prevOffer.remoteDays,
        }));

        setMessages((prev: ChatMessage[]) => [
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
        const currentRole = playerRole || (Number(myPlayerNumberRef.current) % 2 !== 0 ? "candidate" : "hr");

        setGameOverMessage(outcome);
        setCandidateScore(candidateScore !== null ? parseInt(candidateScore) : null);
        setHrScore(hrScore !== null ? parseInt(hrScore) : null);

        setOpponentBonusObjective(currentRole === "candidate" ? hrBonus : candidateBonus);
        setIsGameOverModalOpen(true);

        setModalInputs({
          salary: 0,
          bonus: 0,
          remoteDays: 0
        });

      }else if (messageType === "typing") {
        const isTypingStatus = parts[1].toLowerCase() === 'true';
        setIsPartnerTyping(isTypingStatus);
        return; // Important: Return here to avoid further processing
      } else if (messageType === "error") {
        const errorMessage = parts.slice(1).join("|");
        alert(errorMessage);
      }
    };

    socketRef.current.onclose = (event: CloseEvent) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      socketRef.current = null;
      if (event.code !== 1000 && event.code !== 1001) {
        setIsLoading(false);
        alert('Connection lost. Please refresh the page.');
      }
    };

    socketRef.current.onerror = (error: Event) => {
      console.error('WebSocket error:', error);
      setIsLoading(false);
      alert('Connection error. Please refresh the page.');
    };
  }, []);

    useEffect(() => {
    let timerInterval: NodeJS.Timeout; // Explicit type
    if (isTimerRunning && timeLeft > 0) {
      timerInterval = setInterval(() => {
        setTimeLeft((prevTime) => prevTime - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send("gameover|timeout|Game Over! Negotiation timed out.");
      }
    }
    return () => clearInterval(timerInterval);
  }, [isTimerRunning, timeLeft]);

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
      setMessageInput('');
      setIsTyping(false);
      socketRef.current.send("typing:false");
      clearTimeout(typingTimeout.current!); // Use non-null assertion if you're sure it's defined
    }
  };

  const handleAccept = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send("accept");
    }
  };

    const handleOffer = () => {
    setIsOfferModalOpen(true);
    setModalInputs({
      salary: offer.salary !== null ? offer.salary : 0,
      bonus: offer.bonus !== null ? offer.bonus : 0,
      remoteDays: offer.remoteDays !== null ? offer.remoteDays : 0,
    });
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMessageInput(e.target.value);
    if (e.target.value.trim()) {
        if (!isTyping) {
            socketRef.current!.send("typing:true");
            setIsTyping(true);
        }
        clearTimeout(typingTimeout.current!);
        typingTimeout.current = setTimeout(() => {
            setIsTyping(false);
            socketRef.current!.send("typing:false");
        }, 1000);
    } else {
        setIsTyping(false);
        socketRef.current!.send("typing:false");
        clearTimeout(typingTimeout.current!);
    }
  };

    const handleObjectives = () => {
    setIsObjectivesModalOpen(true);
  };

    const handleSubmitOffer = () => {
    console.log("Submit offer clicked");
    console.log("Current values:", modalInputs);
    const salary = modalInputs.salary;
    const bonus = modalInputs.bonus;
    const remote_days = modalInputs.remoteDays;

    if (isNaN(salary) || salary < 0 || salary > 1000000 || !Number.isInteger(salary)) {
      console.log("Salary validation failed");
      alert("Base salary must be a whole number between $0 and $1,000,000");
      return;
    }
    if (isNaN(bonus) || bonus < 0 || bonus > 10000 || !Number.isInteger(bonus)) {
      console.log("Bonus validation failed");
      alert("Sign-on bonus must be a whole number between $0 and $10,000");
      return;
    }
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

      setOffer({
        salary: salary,
        bonus: bonus,
        remoteDays: remote_days,
        lastSender: myPlayerNumberRef.current as string // Assuming myPlayerNumberRef.current is a string
      });
    } else {
      console.log("WebSocket not ready");
    }

    setIsOfferModalOpen(false);
    console.log("Offer modal closed");
  };

    const handleCancelOffer = () => {
    setIsOfferModalOpen(false);
  };

    const handleCloseObjectives = () => {
    setIsObjectivesModalOpen(false);
  };

    const handleCloseGameOver = () => {
    setIsGameOverModalOpen(false);
    resetGameState();
  };

    const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };

   const getBonusObjectiveDescription = (objectiveId: string | null, role?: GameRole) => { // Type the arguments
    if (!objectiveId) {
      return "N/A";
    }

    const currentRole = role || (Number(myPlayerNumberRef.current) % 2 !== 0 ? "candidate" : "hr");

    if (currentRole === "candidate") {
      const hrObjective = hrBonusObjectives.find(obj => obj.id === objectiveId);
      return hrObjective ? hrObjective.description : "N/A";
    } else if (currentRole === "hr") {
      const candidateObjective = candidateBonusObjectives.find(obj => obj.id === objectiveId);
      return candidateObjective ? candidateObjective.description : "N/A";
    }
    return "N/A";
  };

    const resetGameState = () => {
        setOffer({
            salary: null,
            bonus: null,
            remoteDays: null,
            lastSender: null
        });

        setModalInputs({
            salary: 0,
            bonus: 0,
            remoteDays: 0
        });

        setGameOverMessage(null);
        setCandidateScore(null);
        setHrScore(null);
        setOpponentBonusObjective(null);

        setIsOfferModalOpen(false);
        setIsObjectivesModalOpen(false);
        setIsGameOverModalOpen(false);

        setMessages([]);
    };

    return (
        <ErrorBoundary>
            <div className="chat-container">
                <div className="header">
                    <div className="status-badge">
                        <span className="room-id">Room #{roomId}</span>
                    </div>
                    <Timer timeLeft={timeLeft} isPulsing={isPulsing} formatTime={formatTime} />
                </div>

                <div className="current-offer">
                    <h2><strong>Current Offer:</strong></h2>
                    <p>Base Salary: ${offer.salary !== null ? offer.salary.toLocaleString() : "N/A"}</p>
                    <p>Sign-On Bonus: ${offer.bonus !== null ? offer.bonus.toLocaleString() : "N/A"}</p>
                    <p>Remote Work Days Per Week: {offer.remoteDays !== null ? offer.remoteDays : "N/A"}</p>
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
                            disabled={!offer.salary || !offer.lastSender || offer.lastSender === myPlayerNumberRef.current}
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

                <OfferModal
                    isOpen={isOfferModalOpen}
                    onClose={handleCancelOffer}
                    onSubmit={handleSubmitOffer}
                    modalInputs={modalInputs}
                    setValidatedModalInput={setValidatedModalInput}
                    formatCurrency={formatCurrency}
                />

                <ObjectivesModal
                    isOpen={isObjectivesModalOpen}
                    onClose={handleCloseObjectives}
                    playerRole={playerRole}
                    candidatePrimaryObjectives={candidatePrimaryObjectives}
                    hrPrimaryObjectives={hrPrimaryObjectives}
                    bonusObjective={bonusObjective}
                />

                <GameOverModal
                    isOpen={isGameOverModalOpen}
                    onClose={handleCloseGameOver}
                    gameOverMessage={gameOverMessage}
                    candidateScore={candidateScore}
                    hrScore={hrScore}
                    offer={offer}
                    getBonusObjectiveDescription={getBonusObjectiveDescription}
                    opponentBonusObjective={opponentBonusObjective}
                    playerRole={playerRole}
                />

                {isLoading && (
                    <div className="loading-overlay">
                        <div className="loading-spinner"></div>
                    </div>
                )}
            </div>
        </ErrorBoundary>
    );
}

export default App;