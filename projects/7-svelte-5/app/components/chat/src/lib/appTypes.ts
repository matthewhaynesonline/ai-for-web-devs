// See models.py

export enum GeneratedMediaType {
  GeneratedMedia = "generated_media",
  GeneratedImage = "generated_image",
  GeneratedAudio = "generated_audio",
}

export interface GeneratedMedia {
  id: number;
  filename: string;
  prompt: string;
  type: GeneratedMediaType;
  created_at: string;
  updated_at: string;
}

export enum ChatMessageRole {
  Assistant = "assistant",
  System = "system",
  User = "user",
}

export enum ChatMessageState {
  Pending = "pending",
  Ready = "ready",
}

export interface ChatMessage {
  id: number;
  content: string;
  role: ChatMessageRole;
  state: ChatMessageState;
  created_at: string | null;
  updated_at: string | null;
  title?: string | null;
  generated_media?: GeneratedMedia | null;
}

export const defaultChatMessage: ChatMessage = {
  id: 0,
  content: "",
  role: ChatMessageRole.User,
  state: ChatMessageState.Ready,
  created_at: new Date(Date.now()).toISOString(),
  updated_at: new Date(Date.now()).toISOString(),
};

export interface Chat {
  id: number;
  title: string | null;
  created_at: string | null;
  updated_at: string | null;
  chat_messages: ChatMessage[];
}

export const defaultChat: Chat = {
  id: 0,
  title: "",
  created_at: null,
  updated_at: null,
  chat_messages: [],
};

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

export const defaultToastMessage: ToastMessage = {
  title: "",
  content: "",
  state: ToastState.Danger,
};

export interface Source {
  source: string;
  page_content: string;
}

export const defaultSource: Source = {
  source: "",
  page_content: "",
};

export interface InputCommand {
  label: string;
  description: string;
  endpoint: string;
}
