// src/components/OfferModal.tsx
import React, { useState } from 'react'; // Import useState
import { motion } from 'framer-motion';
import {
    FaDollarSign,
    FaGift,
    FaHome,
    FaPaperPlane,
    FaTimes,
    FaHandshake,
    FaMoneyCheckAlt,
    FaCalendarAlt
} from 'react-icons/fa';
import { ModalInputs } from '../types';

type OfferModalProps = {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: () => void;
    modalInputs: ModalInputs;
    setValidatedModalInput: (field: keyof ModalInputs, value: string) => void;
    formatCurrency: (value: number) => string;
};

const OfferModal: React.FC<OfferModalProps> = ({
    isOpen,
    onClose,
    onSubmit,
    modalInputs,
    setValidatedModalInput,
    formatCurrency
}) => {

    // Validation Error State
    const [errors, setErrors] = useState({
        salary: '',
        bonus: '',
        remoteDays: ''
    });

    // New state for tracking which field is being edited
    const [editingField, setEditingField] = useState<keyof ModalInputs | null>(null);

     // Updated Validation Setter
    const setValidatedInput = (field: keyof ModalInputs, value: string) => {
      let numValue = parseInt(value);
      let error = '';

      if (isNaN(numValue) || !Number.isInteger(parseFloat(value))) {
          error = 'Must be a whole number';
      } else {
          switch (field) {
              case 'salary':
                  if (numValue < 0 || numValue > 1000000) {
                      error = 'Salary must be between $0 and $1,000,000';
                  }
                  break;
              case 'bonus':
                  if (numValue < 0 || numValue > 20000) {
                      error = 'Bonus must be between $0 and $20,000';
                  }
                  break;
              case 'remoteDays':
                  if (numValue < 0 || numValue > 5) {
                      error = 'Remote days must be between 0 and 5';
                  }
                  break;
          }
      }
        setErrors(prevErrors => ({ ...prevErrors, [field]: error })); // Update the specific error
        setValidatedModalInput(field, value); //Still update, but with validated value

    };

    // New handler for inline editing
    const handleValueClick = (field: keyof ModalInputs) => {
        setEditingField(field);
    };

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
                    {/* --- Updated Salary Input --- */}
                    <div className="input-container">
                        <FaDollarSign className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalSalary">
                                Base Salary: 
                                {editingField === 'salary' ? (
                                    <input
                                        type="number"
                                        value={modalInputs.salary}
                                        onChange={(e) => setValidatedInput('salary', e.target.value)}
                                        onBlur={() => setEditingField(null)}
                                        autoFocus
                                        className="inline-edit-input"
                                        min="50000"
                                        max="1000000"
                                    />
                                ) : (
                                    <span 
                                        className="editable-value" 
                                        onClick={() => handleValueClick('salary')}
                                    >
                                        {formatCurrency(modalInputs.salary)}
                                    </span>
                                )}
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalSalary"
                                    min="50000"
                                    max="1000000"
                                    step="1000"
                                    value={modalInputs.salary}
                                    onChange={(e) => setValidatedInput('salary', e.target.value)}
                                />
                            </div>
                             {/* Display Salary Error */}
                            <div className="validation-messages">
                                {errors.salary && <span className="error" style={{color: "red"}}>{errors.salary}</span>}
                            </div>
                        </div>
                    </div>

                    {/* --- Updated Bonus Input --- */}
                    <div className="input-container">
                        <FaGift className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalBonus">
                                Sign-On Bonus: 
                                {editingField === 'bonus' ? (
                                    <input
                                        type="number"
                                        value={modalInputs.bonus}
                                        onChange={(e) => setValidatedInput('bonus', e.target.value)}
                                        onBlur={() => setEditingField(null)}
                                        autoFocus
                                        className="inline-edit-input"
                                        min="0"
                                        max="20000"
                                    />
                                ) : (
                                    <span 
                                        className="editable-value" 
                                        onClick={() => handleValueClick('bonus')}
                                    >
                                        {formatCurrency(modalInputs.bonus)}
                                    </span>
                                )}
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalBonus"
                                    min="0"
                                    max="20000"
                                    step="500"
                                    value={modalInputs.bonus}
                                     onChange={(e) => setValidatedInput('bonus', e.target.value)}
                                />
                            </div>
                            {/* Display Bonus Error */}
                            <div className="validation-messages">
                                {errors.bonus && <span className="error" style={{color: "red"}}>{errors.bonus}</span>}
                            </div>
                        </div>
                    </div>

                    {/* --- Updated Remote Days Input --- */}
                    <div className="input-container">
                        <FaHome className="input-icon" />
                        <div className="input-wrapper">
                            <label htmlFor="modalRemoteDays">
                                Remote Days: 
                                {editingField === 'remoteDays' ? (
                                    <input
                                        type="number"
                                        value={modalInputs.remoteDays}
                                        onChange={(e) => setValidatedInput('remoteDays', e.target.value)}
                                        onBlur={() => setEditingField(null)}
                                        autoFocus
                                        className="inline-edit-input"
                                        min="0"
                                        max="5"
                                    />
                                ) : (
                                    <span 
                                        className="editable-value" 
                                        onClick={() => handleValueClick('remoteDays')}
                                    >
                                        {modalInputs.remoteDays}
                                    </span>
                                )} days/week
                            </label>
                            <div className="slider-input-group">
                                <input
                                    type="range"
                                    id="modalRemoteDays"
                                    min="0"
                                    max="5"
                                    step="1"
                                    value={modalInputs.remoteDays}
                                    onChange={(e) => setValidatedInput('remoteDays', e.target.value)}
                                />
                            </div>
                            {/* Display Remote Days Error */}
                            <div className="validation-messages">
                               {errors.remoteDays && <span className="error" style={{color: "red"}}>{errors.remoteDays}</span>}
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
};

export default OfferModal;