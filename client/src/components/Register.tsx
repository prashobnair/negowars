// src/components/Register.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface RegisterProps {
    onRegister: (token: string) => void;
    onClose: () => void;
}
const Register: React.FC<RegisterProps> = ({ onRegister, onClose }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError('');

        try {
            const response = await fetch('http://localhost:8000/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // MUST BE THIS
                },
                body: new URLSearchParams({ // Correctly format as form data
                    username,
                    password,
                    email, // Include email in the request
                }),
            });

            if (response.ok) {
                const data = await response.json();
                onRegister(data.access_token);
                onClose();
            } else {
                const errorData = await response.json();
                console.log('Error response:', errorData);
                setError(errorData.detail || 'Registration failed');
            }
        } catch (error) {
            setError('An unexpected error occurred.');
            console.error("Registration error:", error);
        }
    };

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
                  <h2>Register</h2>
                </div>

            {error && <p style={{color: "red"}}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="username">Username:</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="email">Email:</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="password">Password:</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                <button type="submit">Register</button>
                <button type='button' onClick={onClose}>Cancel</button>
            </form>
            </motion.div>
        </motion.div>
    );
};

export default Register;