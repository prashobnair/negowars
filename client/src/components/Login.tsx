// src/components/Login.tsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';

interface LoginProps {
  onLogin: (token: string) => void;
  onClose: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin, onClose }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(''); // Clear any previous errors

    try {
      const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username,
          password,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        onLogin(data.access_token); // Call the callback with the token
        onClose(); // Close the modal on success
      } else {
        // Handle errors (e.g., 401 Unauthorized, etc.)
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed'); // Use the error detail, or a generic message
      }
    } catch (error) {
      setError('An unexpected error occurred.');
      console.error("Login error:", error);
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
                    <h2>Login</h2>
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
                        <label htmlFor="password">Password:</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit">Login</button>
                    <button type="button" onClick={onClose}>Cancel</button>
                </form>
            </motion.div>
      </motion.div>
  );
};

export default Login;