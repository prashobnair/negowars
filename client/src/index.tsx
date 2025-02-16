// src/index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App'; // Remove .tsx extension
import { GameProvider } from './contexts/GameContext'; // Import the provider

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <GameProvider> {/* Wrap the App component */}
      <App />
    </GameProvider>
  </React.StrictMode>
);