"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { X, Trash2 } from "lucide-react";
import type { Thread } from "@/types/chat";

interface ThreadSidebarProps {
  threads: Thread[];
  activeThreadId: string | null;
  isLoading: boolean;
  isMobileOpen: boolean;
  onSelectThread: (threadId: string) => void;
  onDeleteThread: (threadId: string) => void;
  onNewChat: () => void;
  onCloseMobile: () => void;
}

function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "JUST NOW";
  if (diffMin < 60) return `${diffMin} MIN AGO`;
  if (diffHr < 24) return `${diffHr} HR AGO`;
  if (diffDay === 1) return "YESTERDAY";
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" }).toUpperCase();
}

function SkeletonThread() {
  return (
    <div style={{ padding: "10px 12px" }}>
      <div
        style={{
          height: 14,
          width: "75%",
          background: "var(--color-bg)",
          borderRadius: 4,
          animation: "pulse 1.5s ease-in-out infinite",
          marginBottom: 6,
        }}
      />
      <div
        style={{
          height: 10,
          width: "40%",
          background: "var(--color-bg)",
          borderRadius: 4,
          animation: "pulse 1.5s ease-in-out infinite",
        }}
      />
    </div>
  );
}

/* ── Context menu (right-click on desktop) ── */
interface ContextMenuState {
  threadId: string;
  x: number;
  y: number;
}

function ContextMenu({
  x,
  y,
  onDelete,
  onClose,
}: {
  x: number;
  y: number;
  onDelete: () => void;
  onClose: () => void;
}) {
  return (
    <>
      {/* Invisible backdrop to catch outside clicks */}
      <div
        onClick={onClose}
        onContextMenu={(e) => {
          e.preventDefault();
          onClose();
        }}
        style={{ position: "fixed", inset: 0, zIndex: 200 }}
      />
      <div
        style={{
          position: "fixed",
          left: x,
          top: y,
          zIndex: 201,
          background: "var(--color-surface)",
          border: "1px solid var(--color-border-strong)",
          borderRadius: "var(--radius-sm)",
          boxShadow: "var(--shadow-md)",
          padding: 4,
          minWidth: 140,
        }}
      >
        <button
          onClick={onDelete}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            width: "100%",
            padding: "8px 12px",
            border: "none",
            borderRadius: 4,
            background: "transparent",
            color: "var(--color-error)",
            fontSize: 13,
            fontWeight: 500,
            cursor: "pointer",
            fontFamily: "var(--font-body)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--color-error-bg)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <Trash2 size={14} strokeWidth={1.5} />
          Delete chat
        </button>
      </div>
    </>
  );
}

// Swiping threshold in pixels. Used for mobile devices to delete chats
const SWIPE_THRESHOLD = 72;

function ThreadItem({
  thread,
  isActive,
  onSelect,
  onDelete,
}: {
  thread: Thread;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}) {
  const touchStartX = useRef(0);
  const offsetX = useRef(0);
  const rowRef = useRef<HTMLDivElement>(null);
  const pendingTimers = useRef<ReturnType<typeof setTimeout>[]>([]);

  // Clear any pending timers on unmount
  useEffect(() => {
    const timers = pendingTimers.current;

    return () => {
      timers.forEach(clearTimeout);
    };
  }, []);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    const diff = e.touches[0].clientX - touchStartX.current;
    // Only allow swiping left (negative)
    const clamped = Math.min(0, Math.max(-SWIPE_THRESHOLD - 20, diff));
    offsetX.current = clamped;
    if (rowRef.current) {
      rowRef.current.style.transform = `translateX(${clamped}px)`;
    }
  }, []);

  const onTouchEnd = useCallback(() => {
    if (offsetX.current < -SWIPE_THRESHOLD) {
      // Animate off and delete
      if (rowRef.current) {
        rowRef.current.style.transition = "transform 0.2s ease";
        rowRef.current.style.transform = "translateX(-100%)";
      }
      pendingTimers.current.push(setTimeout(onDelete, 200));
    } else {
      // Snap back
      if (rowRef.current) {
        rowRef.current.style.transition = "transform 0.2s ease";
        rowRef.current.style.transform = "translateX(0)";
      }
    }
    offsetX.current = 0;
    // Clean up transition after snap
    pendingTimers.current.push(
      setTimeout(() => {
        if (rowRef.current) rowRef.current.style.transition = "";
      }, 200),
    );
  }, [onDelete]);

  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        borderRadius: "var(--radius-sm)",
        marginBottom: 2,
      }}
    >
      {/* Delete background revealed on swipe */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "var(--color-error)",
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          paddingRight: 16,
          borderRadius: "var(--radius-sm)",
        }}
      >
        <Trash2 size={16} strokeWidth={1.5} color="#fff" />
      </div>

      {/* Swipeable row */}
      <div
        ref={rowRef}
        onClick={onSelect}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        style={{
          position: "relative",
          padding: "10px 12px",
          borderRadius: "var(--radius-sm)",
          background: isActive ? "var(--color-primary)" : "var(--color-surface)",
          cursor: "pointer",
          zIndex: 1,
        }}
        onMouseEnter={(e) => {
          if (!isActive) e.currentTarget.style.background = "var(--color-bg)";
        }}
        onMouseLeave={(e) => {
          if (!isActive) e.currentTarget.style.background = "var(--color-surface)";
        }}
      >
        <div
          style={{
            fontWeight: 500,
            color: isActive ? "#fff" : "var(--color-text-secondary)",
            fontSize: 13,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {thread.title}
        </div>
        <div
          style={{
            color: isActive ? "rgba(255, 255, 255, 0.6)" : "var(--color-text-muted)",
            fontSize: 11,
            fontWeight: 500,
            letterSpacing: "0.02em",
            marginTop: 4,
          }}
        >
          {formatTimestamp(thread.updated_at)}
        </div>
      </div>
    </div>
  );
}

export function ThreadSidebar({
  threads,
  activeThreadId,
  isLoading,
  isMobileOpen,
  onSelectThread,
  onDeleteThread,
  onNewChat,
  onCloseMobile,
}: ThreadSidebarProps) {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

  const handleContextMenu = useCallback((e: React.MouseEvent, threadId: string) => {
    e.preventDefault();
    setContextMenu({ threadId, x: e.clientX, y: e.clientY });
  }, []);

  const sidebarContent = (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "var(--color-surface)",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: 16,
          borderBottom: "1px solid var(--color-border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: 700,
            fontSize: 18,
            letterSpacing: "-0.01em",
            color: "var(--color-text)",
          }}
        >
          Conversations
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <button
            onClick={onNewChat}
            style={{
              padding: "6px 12px",
              borderRadius: "var(--radius-sm)",
              background: "var(--color-primary)",
              color: "#fff",
              border: "none",
              fontFamily: "var(--font-display)",
              fontWeight: 600,
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            + New
          </button>
          {/* Mobile close button */}
          <button
            onClick={onCloseMobile}
            className="mobile-only-close"
            style={{
              width: 28,
              height: 28,
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--color-border-strong)",
              background: "transparent",
              cursor: "pointer",
              display: "none",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--color-text-secondary)",
            }}
          >
            <X size={14} strokeWidth={1.5} />
          </button>
        </div>
      </div>

      {/* Thread list */}
      <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
        {isLoading ? (
          <>
            <SkeletonThread />
            <SkeletonThread />
            <SkeletonThread />
          </>
        ) : threads.length === 0 ? (
          <div
            style={{
              padding: "24px 12px",
              textAlign: "center",
              fontSize: 13,
              color: "var(--color-text-muted)",
            }}
          >
            No conversations yet
          </div>
        ) : (
          threads.map((thread) => (
            <div
              key={thread.thread_id}
              onContextMenu={(e) => handleContextMenu(e, thread.thread_id)}
            >
              <ThreadItem
                thread={thread}
                isActive={thread.thread_id === activeThreadId}
                onSelect={() => {
                  onSelectThread(thread.thread_id);
                  onCloseMobile();
                }}
                onDelete={() => onDeleteThread(thread.thread_id)}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <div
        className="thread-sidebar-desktop"
        style={{
          width: 260,
          minWidth: 260,
          borderRight: "1px solid var(--color-border)",
          height: "100%",
        }}
      >
        {sidebarContent}
      </div>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div
          className="thread-sidebar-mobile"
          onClick={(e) => {
            if (e.target === e.currentTarget) onCloseMobile();
          }}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.3)",
            zIndex: 100,
            display: "none",
          }}
        >
          <div
            style={{
              width: 280,
              height: "100%",
              boxShadow: "var(--shadow-lg)",
            }}
          >
            {sidebarContent}
          </div>
        </div>
      )}

      {/* Context menu (desktop right-click) */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onDelete={() => {
            onDeleteThread(contextMenu.threadId);
            setContextMenu(null);
          }}
          onClose={() => setContextMenu(null)}
        />
      )}
    </>
  );
}
