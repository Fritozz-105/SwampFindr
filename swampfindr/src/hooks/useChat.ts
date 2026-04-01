"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import {
  sendChatMessage,
  getThreads,
  getChatHistory,
  toggleFavorite,
  deleteThread as deleteThreadApi,
} from "@/lib/api/flask";
import type { Thread, ChatMessage } from "@/types/chat";
import type { Listing } from "@/types/listing";

function parseHistoryContent(content: string | unknown[]): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((item) => {
        if (typeof item === "string") return item;
        if (typeof item === "object" && item !== null && "text" in item) {
          return String((item as { text: unknown }).text);
        }
        return "";
      })
      .join("")
      .trim();
  }
  return String(content ?? "");
}

async function getToken(): Promise<string | null> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function useChat() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoadingThreads, setIsLoadingThreads] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const lastUserMessage = useRef<string>("");

  // Fetch threads on mount
  useEffect(() => {
    const fetchThreads = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await getThreads(token);
        if (res.success) {
          setThreads(
            res.data.map((t) => ({
              ...t,
              title: "Conversation",
            })),
          );
        }
      } catch {
        // Non-critical, sidebar will be empty
      } finally {
        setIsLoadingThreads(false);
      }
    };
    fetchThreads();
  }, []);

  // Fetch favorites from profile on mount
  useEffect(() => {
    const fetchFavorites = async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080"}/api/v1/profiles/me`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (res.ok) {
          const body = await res.json();
          setFavorites(new Set(body.data?.favorites ?? []));
        }
      } catch {
        // Non-critical
      }
    };
    fetchFavorites();
  }, []);

  const selectThread = useCallback(async (threadId: string) => {
    setActiveThreadId(threadId);
    setMessages([]);
    setError(null);
    setIsLoadingHistory(true);
    try {
      const token = await getToken();
      if (!token) return;
      const res = await getChatHistory(token, threadId);
      if (res.success) {
        const parsed: ChatMessage[] = res.data
          .filter(
            (m) =>
              m.role === "user" || m.role === "assistant" || m.role === "human" || m.role === "ai",
          )
          .map((m) => ({
            role: m.role === "human" || m.role === "user" ? "user" : "assistant",
            content: parseHistoryContent(m.content),
          }));
        setMessages(parsed);

        // Derive thread title from first user message
        const firstUserMsg = parsed.find((m) => m.role === "user");
        if (firstUserMsg) {
          const title =
            firstUserMsg.content.length > 40
              ? firstUserMsg.content.slice(0, 40) + "..."
              : firstUserMsg.content;
          setThreads((prev) => prev.map((t) => (t.thread_id === threadId ? { ...t, title } : t)));
        }
      }
    } catch {
      setError("Failed to load conversation history.");
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  const startNewChat = useCallback(() => {
    setActiveThreadId(null);
    setMessages([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isSending) return;
      setError(null);
      lastUserMessage.current = content;

      // Optimistic user message
      setMessages((prev) => [...prev, { role: "user", content }]);
      setIsSending(true);

      try {
        const token = await getToken();
        if (!token) {
          setError("Not authenticated.");
          setIsSending(false);
          return;
        }

        const res = await sendChatMessage(token, content, activeThreadId ?? undefined);

        if (!res.success) {
          setError(res.error ?? "Something went wrong. Try again.");
          setIsSending(false);
          return;
        }

        // Mark is_favorited on returned listings
        const listingsWithFavs: Listing[] = (res.listings ?? []).map((l) => ({
          ...l,
          is_favorited: favorites.has(l.listing_id),
        }));

        // Append assistant message
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: res.response,
            listings: listingsWithFavs.length > 0 ? listingsWithFavs : undefined,
          },
        ]);

        // Handle new thread
        if (res.is_new_thread) {
          const title = content.length > 40 ? content.slice(0, 40) + "..." : content;
          setActiveThreadId(res.thread_id);
          setThreads((prev) => [
            {
              thread_id: res.thread_id,
              title,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            ...prev,
          ]);
        } else {
          // Move thread to top
          setThreads((prev) => {
            const updated = prev.map((t) =>
              t.thread_id === res.thread_id ? { ...t, updated_at: new Date().toISOString() } : t,
            );
            updated.sort(
              (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
            );
            return updated;
          });
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Could not connect to server. Check your connection.",
        );
      } finally {
        setIsSending(false);
      }
    },
    [activeThreadId, isSending, favorites],
  );

  const retryLastMessage = useCallback(async () => {
    if (!lastUserMessage.current) return;
    // Remove the last user message (will be re-added by sendMessage)
    setMessages((prev) => {
      const idx = prev.findLastIndex((m) => m.role === "user");
      if (idx === -1) return prev;
      return prev.slice(0, idx);
    });
    setError(null);
    await sendMessage(lastUserMessage.current);
  }, [sendMessage]);

  const handleDeleteThread = useCallback(
    async (threadId: string) => {
      const token = await getToken();
      if (!token) {
        setError("Session expired. Please refresh.");
        return;
      }

      // Capture state for rollback
      const previousThreads = threads;
      const previousActiveThreadId = activeThreadId;
      const previousMessages = messages;

      // Optimistic removal
      setThreads((prev) => prev.filter((t) => t.thread_id !== threadId));
      if (activeThreadId === threadId) {
        setActiveThreadId(null);
        setMessages([]);
        setError(null);
      }

      try {
        await deleteThreadApi(token, threadId);
      } catch {
        // Revert full state on failure
        setThreads(previousThreads);
        if (previousActiveThreadId === threadId) {
          setActiveThreadId(previousActiveThreadId);
          setMessages(previousMessages);
        }
      }
    },
    [threads, activeThreadId, messages],
  );

  const handleToggleFavorite = useCallback(async (listingId: string) => {
    // Optimistic update in messages
    setMessages((prev) =>
      prev.map((m) => {
        if (!m.listings) return m;
        return {
          ...m,
          listings: m.listings.map((l) =>
            l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l,
          ),
        };
      }),
    );
    setFavorites((prev) => {
      const next = new Set(prev);
      if (next.has(listingId)) next.delete(listingId);
      else next.add(listingId);
      return next;
    });

    try {
      const token = await getToken();
      if (!token) return;
      await toggleFavorite(token, listingId);
    } catch {
      // Revert
      setMessages((prev) =>
        prev.map((m) => {
          if (!m.listings) return m;
          return {
            ...m,
            listings: m.listings.map((l) =>
              l.listing_id === listingId ? { ...l, is_favorited: !l.is_favorited } : l,
            ),
          };
        }),
      );
      setFavorites((prev) => {
        const next = new Set(prev);
        if (next.has(listingId)) next.delete(listingId);
        else next.add(listingId);
        return next;
      });
    }
  }, []);

  return {
    threads,
    activeThreadId,
    messages,
    isLoadingThreads,
    isLoadingHistory,
    isSending,
    error,
    selectThread,
    startNewChat,
    sendMessage,
    retryLastMessage,
    deleteThread: handleDeleteThread,
    toggleFavorite: handleToggleFavorite,
  };
}
