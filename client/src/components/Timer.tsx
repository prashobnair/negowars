// src/components/Timer.tsx
import React from 'react';

type TimerProps = {
  timeLeft: number;
  isPulsing: boolean;
  formatTime: (seconds: number) => string;
};

const Timer: React.FC<TimerProps> = ({ timeLeft, isPulsing, formatTime }) => {
  return (
    <div className="timer">
      <div className={`timer-progress ${isPulsing ? 'pulse' : ''}`}>
        <svg width="48" height="48">
          <circle
            cx="24"
            cy="24"
            r="20"
            className="timer-base"
            strokeWidth="4"
          />
          <circle
            cx="24"
            cy="24"
            r="20"
            className={`timer-fill ${
              timeLeft > 240 ? 'green' :
              timeLeft > 60 ? 'orange' :
              'red'
            }`}
            strokeWidth="4"
            strokeDasharray={`${(timeLeft / 420) * 126} 126`}
            transform="rotate(-90 24 24)"
          />
        </svg>
      </div>
      <span className="timer-text">{formatTime(timeLeft)}</span>
    </div>
  );
};

export default Timer;