// src/components/GameOverModal.js
import React from 'react';
import { motion } from 'framer-motion';
import { GameRole, Offer } from '../types'; // Import types

type GameOverModalProps = {
    isOpen: boolean;
    onClose: () => void;
    gameOverMessage: string | null;
    candidateScore: number | null;
    hrScore: number | null;
    offer: Offer;
    getBonusObjectiveDescription: (objectiveId: string | null, role?: GameRole) => string;
    opponentBonusObjective: string | null;
    playerRole: GameRole | null;
};

const GameOverModal: React.FC<GameOverModalProps> = ({ isOpen, onClose, gameOverMessage, candidateScore, hrScore, offer, getBonusObjectiveDescription, opponentBonusObjective, playerRole }) => {
    if (!isOpen) return null;

    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ position: 'fixed', top: '0', left: '0', width: '100%', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}
        >
            <motion.div
                className="modal"
                initial={{ y: 50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 50, opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{ backgroundColor: 'white', padding: '20px', borderRadius: '5px' }}
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
                        {/* Use offer.salary, offer.bonus, offer.remoteDays */}
                        <p>Base Salary: ${offer.salary !== null ? offer.salary.toLocaleString() : "N/A"}</p>
                        <p>Sign-On Bonus: ${offer.bonus !== null ? offer.bonus.toLocaleString() : "N/A"}</p>
                        <p>Remote Work Days: {offer.remoteDays !== null ? offer.remoteDays : "N/A"}</p>
                        <h3>Opponent's Bonus Objective:</h3>
                        <p>{getBonusObjectiveDescription(opponentBonusObjective, playerRole as GameRole)}</p>
                    </>
                )}
                <div className="modal-buttons">
                    <button onClick={onClose} className="modal-button modal-cancel">Close</button>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default GameOverModal;