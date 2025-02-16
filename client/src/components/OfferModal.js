// src/components/OfferModal.js
import React from 'react';
import { motion } from 'framer-motion';
import {
    FaDollarSign,
    FaGift,
    FaHome,
    FaPaperPlane,
    FaTimes,
    FaHandshake
} from 'react-icons/fa';

function OfferModal({
    isOpen,
    onClose,
    onSubmit,
    modalInputs, // Use the combined modalInputs object
    setValidatedModalInput, // Use the combined setter
    formatCurrency
}) {

    if (!isOpen) return null;

    return (
        <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
        >
            <motion.div
                className="modal offer-modal-content"
                initial={{ y: 50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 50, opacity: 0 }}
            >
                <div className="offer-header">
                    <FaHandshake className="offer-icon" />
                    <h2>Make an Offer</h2>
                </div>

                <div className="offer-input-group">
                    {/* --- Salary Input --- */}
                    <div className="input-container">
                        <FaDollarSign className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalSalary">
                                Base Salary: {formatCurrency(modalInputs.salary)}
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalSalary"
                                    min="50000"
                                    max="1000000"
                                    step="1000"
                                    value={modalInputs.salary}
                                    onChange={(e) => setValidatedModalInput('salary', e.target.value)}
                                />
                                <div className="direct-input-container">
                                    <input
                                        type="number"
                                        value={modalInputs.salary}
                                        min="50000"
                                        max="1000000"
                                        onChange={(e) => setValidatedModalInput('salary', e.target.value)}
                                        className="direct-input"
                                    />
                                    <span className="currency-symbol">USD</span>
                                </div>
                            </div>
                            <div className="range-labels">
                                <span>{formatCurrency(50000)}</span>
                                <span>{formatCurrency(1000000)}</span>
                            </div>
                        </div>
                    </div>

                    {/* --- Bonus Input --- */}
                    <div className="input-container">
                        <FaGift className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalBonus">
                                Sign-On Bonus: {formatCurrency(modalInputs.bonus)}
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalBonus"
                                    min="0"
                                    max="20000"
                                    step="500"
                                    value={modalInputs.bonus}
                                    onChange={(e) => setValidatedModalInput('bonus', e.target.value)}
                                />
                                <div className="direct-input-container">
                                    <input
                                        type="number"
                                        value={modalInputs.bonus}
                                        min="0"
                                        max="20000"
                                        onChange={(e) => setValidatedModalInput('bonus', e.target.value)}
                                        className="direct-input"
                                    />
                                    <span className="currency-symbol">USD</span>
                                </div>
                            </div>
                            <div className="range-labels">
                                <span>{formatCurrency(0)}</span>
                                <span>{formatCurrency(20000)}</span>
                            </div>
                        </div>
                    </div>

                    {/* --- Remote Days Input --- */}
                    <div className="input-container">
                        <FaHome className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalRemoteDays">
                                Remote Days: {modalInputs.remoteDays} days/week
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalRemoteDays"
                                    min="0"
                                    max="5"
                                    step="1"
                                    value={modalInputs.remoteDays}
                                    onChange={(e) => setValidatedModalInput('remoteDays', e.target.value)}
                                />
                                <div className="direct-input-container">
                                    <input
                                        type="number"
                                        value={modalInputs.remoteDays}
                                        min="0"
                                        max="5"
                                        onChange={(e) => setValidatedModalInput('remoteDays', e.target.value)}
                                        className="direct-input"
                                    />
                                    <span className="days-label">days</span>
                                </div>
                            </div>
                            <div className="range-labels">
                                <span>0</span>
                                <span>5</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="modal-actions">
                    <button onClick={onSubmit} className="modal-button primary-btn">
                        <FaPaperPlane className="btn-icon" />
                        Submit Offer
                    </button>
                    <button onClick={onClose} className="modal-button secondary-btn">
                        <FaTimes className="btn-icon" />
                        Cancel
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
}

export default OfferModal;