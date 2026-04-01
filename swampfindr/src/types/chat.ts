import type { Listing } from "./listing";

export interface Thread {
  thread_id: string;
  title: string;
  updated_at: string;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  listings?: Listing[];
}

export interface SendMessageResponse {
  success: boolean;
  response: string;
  thread_id: string;
  is_new_thread: boolean;
  listings: Listing[];
  error?: string;
  error_type?: string;
}

export interface ThreadsResponse {
  success: boolean;
  data: {
    thread_id: string;
    created_at: string;
    updated_at: string;
  }[];
}

export interface ChatHistoryResponse {
  success: boolean;
  thread_id: string;
  data: {
    role: string;
    content: string | unknown[];
  }[];
}
