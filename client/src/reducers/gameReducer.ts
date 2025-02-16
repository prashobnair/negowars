// src/reducers/gameReducer.ts
import { GameState } from '../contexts/GameContext'; // Import GameState
import { Offer, ChatMessage } from '../types';

// Define action types.  This is where you define all the possible
// actions that can modify your game state.  This is *crucial* for
// TypeScript to understand what's going on.
export type Action =
  | { type: 'SET_ROOM_ID'; payload: string }
  | { type: 'SET_PLAYER_ROLE'; payload: 'candidate' | 'hr' }
  | { type: 'UPDATE_OFFER'; payload: Offer }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'SET_IS_CHAT_DISABLED', payload: boolean}
  | { type: 'SET_IS_OFFER_DISABLED', payload: boolean}
  | { type: 'SET_IS_LOADING', payload: boolean}
  | { type: 'SET_IS_GAME_OVER_MODAL_OPEN', payload: boolean}
  | { type: 'SET_GAME_OVER_MESSAGE', payload: string | null}
  | { type: 'SET_CANDIDATE_SCORE', payload: number | null}
  | { type: 'SET_HR_SCORE', payload: number | null}
  | { type: 'SET_OPPONENT_BONUS_OBJECTIVE', payload: string | null}
  | { type: 'SET_BONUS_OBJECTIVE', payload: any | null}
  | { type: 'SET_IS_TIMER_RUNNING', payload: boolean}
  | { type: 'SET_TIME_LEFT', payload: number}
  | { type: 'SET_IS_PULSING', payload: boolean}
  | { type: 'SET_IS_PARTNER_TYPING', payload: boolean}
  | { type: 'SET_OFFER'; payload: Offer }
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'RESET_GAME'}; // Add a RESET_GAME action

// The reducer function
export const gameReducer = (state: GameState, action: Action): GameState => {
  switch (action.type) {
    case 'SET_ROOM_ID':
      return { ...state, roomId: action.payload };
    case 'SET_PLAYER_ROLE':
      return { ...state, playerRole: action.payload };
    case 'UPDATE_OFFER':
      return { ...state, offer: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_IS_CHAT_DISABLED':
        return { ...state, isChatDisabled: action.payload };
    case 'SET_IS_OFFER_DISABLED':
        return { ...state, isOfferDisabled: action.payload };
    case 'SET_IS_LOADING':
        return { ...state, isLoading: action.payload };
    case 'SET_IS_GAME_OVER_MODAL_OPEN':
        return { ...state, isGameOverModalOpen: action.payload };
    case 'SET_GAME_OVER_MESSAGE':
        return { ...state, gameOverMessage: action.payload };
    case 'SET_CANDIDATE_SCORE':
        return { ...state, candidateScore: action.payload };
    case 'SET_HR_SCORE':
        return { ...state, hrScore: action.payload };
    case 'SET_OPPONENT_BONUS_OBJECTIVE':
        return { ...state, opponentBonusObjective: action.payload };
    case 'SET_BONUS_OBJECTIVE':
        return { ...state, bonusObjective: action.payload };
    case 'SET_IS_TIMER_RUNNING':
        return { ...state, isTimerRunning: action.payload };
    case 'SET_TIME_LEFT':
        return { ...state, timeLeft: action.payload };
    case 'SET_IS_PULSING':
      return { ...state, isPulsing: action.payload };
    case 'SET_IS_PARTNER_TYPING':
      return { ...state, isPartnerTyping: action.payload};

    case 'RESET_GAME': //Add all parameters to reset all states
        return {
            ...state,
            offer: { salary: null, bonus: null, remoteDays: null, lastSender: null },
            messages: [],
            gameOverMessage: null,
            candidateScore: null,
            hrScore: null,
            opponentBonusObjective: null,
            isGameOverModalOpen: false,
        };

    default:
      return state; // Always return state in the default case
  }
};