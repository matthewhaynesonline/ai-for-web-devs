// See models.py

export enum GeneratedMediaType {
  GeneratedMedia = "generated_media",
  GeneratedImage = "generated_image",
}

export interface GeneratedMedia {
  id: number;
  type: GeneratedMediaType;
  filename?: string;
  prompt?: string;
  created_at: string;
  updated_at: string;
}

export enum BackendChatMessageRole {
  Assistant = "assistant",
  System = "system",
  User = "user",
}

export enum BackendChatMessageState {
  Pending = "pending",
  Ready = "ready",
}

export interface BackendChatMessage {
  id: number;
  content: string;
  created_at: string;
  updated_at: string;
  role: BackendChatMessageRole;
  state?: BackendChatMessageState;
  generated_media?: GeneratedMedia | null;
}

export interface BackendChatState {
  id: number;
  title: string;
  chat_messages?: BackendChatMessage[];
  created_at?: string;
  updated_at?: string;
}

export enum ChatMessageAuthor {
  User = "You",
  System = "🤖 MattGPT",
}

export interface ChatMessage {
  id?: number;
  title?: string;
  content: string;
  author: string;
  date: Date | number | null;
  isUserMessage: boolean;
  state?: BackendChatMessageState;
  generatedMedia?: GeneratedMedia | null;
}

export enum ToastState {
  Danger = "danger",
  Info = "info",
  Success = "Success",
}

export interface ToastMessage {
  title: string;
  content: string;
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
