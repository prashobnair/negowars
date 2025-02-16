// src/contexts/GameContext.tsx
import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { GameRole, Offer, ChatMessage, BonusObjective } from '../types'; // Import your types
import { gameReducer, Action } from '../reducers/gameReducer';  // Import the reducer

// Define the shape of your game state
export type GameState = {
  roomId: string | null;
  playerRole: GameRole | null;
  offer: Offer;
  messages: ChatMessage[];
  isChatDisabled: boolean;
  isOfferDisabled: boolean;
  isLoading: boolean;
  isGameOverModalOpen: boolean;
  gameOverMessage: string | null;
  candidateScore: number | null;
  hrScore: number | null;
  opponentBonusObjective: string | null;
  bonusObjective: BonusObjective | null;
  isTimerRunning: boolean;
  timeLeft: number;
  isPulsing: boolean;
  isPartnerTyping: boolean
  // Add other state fields from App.tsx as needed
};

// Define an initial state for your game
const initialState: GameState = {
  roomId: null,
  playerRole: null,
  offer: {
    salary: null,
    bonus: null,
    remoteDays: null,
    lastSender: null,
  },
  messages: [],
  isChatDisabled: false,
  isOfferDisabled: true, // Good practice to set initial state
  isLoading: false,
  isGameOverModalOpen: false,
  gameOverMessage: null,
  candidateScore: null,
  hrScore: null,
  opponentBonusObjective: null,
  bonusObjective: null,
  isTimerRunning: false,
  timeLeft: 7 * 60,
  isPulsing: false,
  isPartnerTyping: false
};

// Create the context.  The `null!` is a non-null assertion. We'll provide
// a proper value in the Provider.  This is a standard pattern.
const GameContext = createContext<{
  state: GameState;
  dispatch: React.Dispatch<Action>;
} | null>(null); // Use null, and check for null in useContext

// Custom hook to use the context (makes usage cleaner)
export const useGameContext = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error("useGameContext must be used within a GameProvider");
  }
  return context;
};

// Define props for the provider
type GameProviderProps = {
  children: ReactNode;
};

// Create the provider component
export const GameProvider: React.FC<GameProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  return (
    <GameContext.Provider value={{ state, dispatch }}>
      {children}
    </GameContext.Provider>
  );
};