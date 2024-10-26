// See models.py

export enum BackendChatMessageRole {
  Assistant = "assistant",
  System = "system",
  User = "user",
}

interface BackendChatMessage {
  body: string;
  created_at: string;
  role: BackendChatMessageRole;
}

export interface InitialChatState {
  id: number;
  title: string;
  chat_messages?: BackendChatMessage[];
}

export enum ChatMessageAuthor {
  User = "You",
  System = "🤖 MattGPT",
}

export interface ChatMessage {
  body: string;
  author: string;
  date: number | null;
  isUserMessage: boolean;
}

export enum ToastState {
  Danger = "danger",
  Info = "info",
  Success = "Success",
}

export interface ToastMessage {
  title: string;
  body: string;
  state: ToastState;
}

export interface Source {
  source: string;
  page_content: string;
}

export interface InputCommand {
  label: string;
  description: string;
  endpoint: string;
}
