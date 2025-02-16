export type GameRole = "candidate" | "hr";
export type ChatMessageSender = "me" | "other" | "system";

export interface ChatMessage {
  player: string;
  text: string;
  sender: ChatMessageSender;
  role?: string;
}

export interface BonusObjective {
  id: string;
  description: string;
  bonus: string;
}

export interface Offer {
  salary: number | null;
  bonus: number | null;
  remoteDays: number | null;
  lastSender: string | null;
}

export interface ModalInputs {
  salary: number;
  bonus: number;
  remoteDays: number;
}
