"use client";

import type { ChatMessage } from "@/types/chat";
import type { Listing } from "@/types/listing";
import { ChatListingCard } from "./ChatListingCard";

interface MessageBubbleProps {
  message: ChatMessage;
  onViewDetails: (listing: Listing) => void;
  onFavoriteToggle: (listingId: string) => void;
}

export function MessageBubble({
  message,
  onViewDetails,
  onFavoriteToggle,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
      }}
    >
      <div style={{ maxWidth: isUser ? "65%" : "75%" }}>
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "var(--radius-md)",
            background: isUser ? "var(--color-primary)" : "var(--color-surface)",
            border: isUser ? "none" : "1px solid var(--color-border)",
            color: isUser ? "#FFFFFF" : "var(--color-text)",
            fontSize: 15,
            fontFamily: "var(--font-body)",
            lineHeight: 1.5,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {message.content}
        </div>
        {!isUser && message.listings && message.listings.length > 0 && (
          <div
            style={{
              marginTop: 8,
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            {message.listings.map((listing) => (
              <ChatListingCard
                key={listing.listing_id}
                listing={listing}
                onViewDetails={() => onViewDetails(listing)}
                onFavoriteToggle={() => onFavoriteToggle(listing.listing_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start" }}>
      <div
        style={{
          padding: "12px 14px",
          borderRadius: "var(--radius-md)",
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          display: "flex",
          gap: 4,
          alignItems: "center",
        }}
      >
        {[
          "var(--color-text-muted)",
          "var(--color-border-strong)",
          "var(--color-border)",
        ].map((color, i) => (
          <div
            key={i}
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: color,
              animation: `pulse 1.5s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
