"use client";

import { useState, useRef, useEffect } from "react";
import { Menu } from "lucide-react";
import { useChat } from "@/hooks/useChat";
import { ThreadSidebar } from "./ThreadSidebar";
import { MessageBubble, TypingIndicator } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { ListingDetailPopup } from "./ListingDetailPopup";

function MessageSkeleton() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* User skeleton */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            width: "45%",
            height: 40,
            borderRadius: "var(--radius-md)",
            background: "var(--color-bg)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
      {/* Assistant skeleton */}
      <div style={{ display: "flex", justifyContent: "flex-start" }}>
        <div
          style={{
            width: "60%",
            height: 64,
            borderRadius: "var(--radius-md)",
            background: "var(--color-bg)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
      {/* User skeleton */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <div
          style={{
            width: "35%",
            height: 40,
            borderRadius: "var(--radius-md)",
            background: "var(--color-bg)",
            animation: "pulse 1.5s ease-in-out infinite",
          }}
        />
      </div>
    </div>
  );
}

export function ChatView() {
  const {
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
    deleteThread,
    toggleFavorite,
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [popupListingId, setPopupListingId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitiallyLoaded = useRef(false);

  // Derive popup listing from messages so it stays in sync with favorite toggles
  const popupListing = popupListingId
    ? messages
        .flatMap((m) => m.listings ?? [])
        .find((l) => l.listing_id === popupListingId) ?? null
    : null;

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  // Auto-select most recent thread on initial load only
  useEffect(() => {
    if (!isLoadingThreads && threads.length > 0 && !hasInitiallyLoaded.current) {
      hasInitiallyLoaded.current = true;
      selectThread(threads[0].thread_id);
    }
  }, [isLoadingThreads, threads, selectThread]);

  const hasMessages = messages.length > 0;
  const showEmptyState = !activeThreadId && !isLoadingHistory && !hasMessages;
  const showWelcome = activeThreadId && !isLoadingHistory && !hasMessages;

  return (
    <div
      className="chat-container"
      style={{
        display: "flex",
        height: "calc(100vh - 64px)",
        background: "var(--color-bg)",
      }}
    >
      <ThreadSidebar
        threads={threads}
        activeThreadId={activeThreadId}
        isLoading={isLoadingThreads}
        isMobileOpen={sidebarOpen}
        onSelectThread={selectThread}
        onDeleteThread={deleteThread}
        onNewChat={() => {
          startNewChat();
          setSidebarOpen(false);
        }}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      {/* Chat area */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          minWidth: 0,
        }}
      >
        {/* Mobile top bar */}
        <div
          className="chat-mobile-topbar"
          style={{
            padding: "12px 16px",
            background: "var(--color-surface)",
            borderBottom: "1px solid var(--color-border)",
            display: "none",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <button
            onClick={() => setSidebarOpen(true)}
            style={{
              padding: 6,
              border: "1px solid var(--color-border-strong)",
              borderRadius: "var(--radius-sm)",
              background: "transparent",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Menu size={18} strokeWidth={1.5} color="var(--color-text-secondary)" />
          </button>
          <span
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: 15,
              color: "var(--color-text)",
            }}
          >
            Chat
          </span>
          <button
            onClick={() => {
              startNewChat();
            }}
            style={{
              padding: "4px 10px",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-primary)",
              color: "#fff",
              border: "none",
              fontFamily: "var(--font-display)",
              fontWeight: 600,
              fontSize: 11,
              cursor: "pointer",
            }}
          >
            + New
          </button>
        </div>

        {/* Messages area */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px 32px",
            display: "flex",
            flexDirection: "column",
            gap: 16,
          }}
        >
          {isLoadingHistory && <MessageSkeleton />}

          {showEmptyState && (
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
              }}
            >
              <div>
                <h2
                  style={{
                    fontFamily: "var(--font-display)",
                    fontWeight: 700,
                    fontSize: 24,
                    letterSpacing: "-0.015em",
                    color: "var(--color-text)",
                    marginBottom: 8,
                  }}
                >
                  Start a conversation
                </h2>
                <p
                  style={{
                    fontSize: 15,
                    color: "var(--color-text-secondary)",
                    lineHeight: 1.5,
                  }}
                >
                  Ask about apartments, bus routes, or anything housing-related
                  near UF.
                </p>
              </div>
            </div>
          )}

          {showWelcome && (
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                textAlign: "center",
              }}
            >
              <p
                style={{
                  fontSize: 15,
                  color: "var(--color-text-muted)",
                }}
              >
                Ask me about apartments, bus routes, or anything
                housing-related.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <MessageBubble
              key={i}
              message={msg}
              onViewDetails={(listing) => setPopupListingId(listing.listing_id)}
              onFavoriteToggle={toggleFavorite}
            />
          ))}

          {isSending && <TypingIndicator />}

          {error && (
            <div
              style={{
                padding: "12px 14px",
                background: "var(--color-error-bg)",
                border: "1px solid rgba(220, 38, 38, 0.2)",
                borderRadius: "var(--radius-md)",
                color: "var(--color-error)",
                fontSize: 13,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span>{error}</span>
              <button
                onClick={retryLastMessage}
                style={{
                  padding: "4px 10px",
                  borderRadius: "var(--radius-sm)",
                  background: "var(--color-error)",
                  color: "#fff",
                  border: "none",
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Retry
              </button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput onSend={sendMessage} disabled={isSending} />
      </div>

      {/* Listing detail popup */}
      {popupListing && (
        <ListingDetailPopup
          listing={popupListing}
          onClose={() => setPopupListingId(null)}
          onFavoriteToggle={toggleFavorite}
        />
      )}
    </div>
  );
}
