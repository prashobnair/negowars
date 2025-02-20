// src/components/WelcomeScreen.tsx
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Login from './Login';
import Register from './Register';

type WelcomeScreenProps = {
  onLogin: (token: string) => void;
  onGuestLogin: () => void;
  onRegister: (token: string) => void; // ADD THIS LINE
};

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onLogin, onGuestLogin, onRegister }) => { // onRegister is now correctly part of the props
  const [isLoginModalOpen, setIsLoginModalOpen] = React.useState(false);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = React.useState(false);

  return (
    <div className="welcome-screen">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        Welcome to NegoWars!
      </motion.h1>

      <motion.div
        className="welcome-buttons"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <button className="login-button" onClick={() => setIsLoginModalOpen(true)}>
          Login
        </button>
        <button className="register-button" onClick={() => setIsRegisterModalOpen(true)}>
          Register
        </button>
        <button className="guest-button" onClick={onGuestLogin}>
          Play as Guest
        </button>
      </motion.div>

      <AnimatePresence>
        {isLoginModalOpen && (
          <Login onLogin={onLogin} onClose={() => setIsLoginModalOpen(false)} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isRegisterModalOpen && (
          <Register onRegister={onRegister} onClose={() => setIsRegisterModalOpen(false)} />
        )}
      </AnimatePresence>
    </div>
  );
};

export default WelcomeScreen;