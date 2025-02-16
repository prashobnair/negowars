// src/components/ObjectivesModal.tsx

import React from 'react';
import { motion } from 'framer-motion';
import { FaBullseye, FaCheck, FaMoneyCheckAlt, FaHandshake } from 'react-icons/fa';
import { GameRole, BonusObjective } from '../types'; // Import types

type ObjectivesModalProps = {
    isOpen: boolean;
    onClose: () => void;
    playerRole: GameRole | null;
    candidatePrimaryObjectives: string[];
    hrPrimaryObjectives: string[];
    bonusObjective: BonusObjective | null;
};

const ObjectivesModal: React.FC<ObjectivesModalProps> = ({ isOpen, onClose, playerRole, candidatePrimaryObjectives, hrPrimaryObjectives, bonusObjective }) => {
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
                className="modal objectives-content"
                initial={{ y: 50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 50, opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{ backgroundColor: 'white', padding: '20px', borderRadius: '5px' }}
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
                            <p className="bonus-description">{bonusObjective?.description}</p>
                            <p className="bonus-points">{bonusObjective?.bonus}</p>
                        </div>
                    </div>
                </div>

                <div className="modal-buttons">
                    <button onClick={onClose} className="modal-button modal-cancel">Close</button>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default ObjectivesModal;