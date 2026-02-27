"use client";

import { useState } from "react";
import { ChevronIcon } from "./icons";

type SettingsCardProps = {
  title: string;
  description: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
};

export function SettingsCard({
  title,
  description,
  defaultOpen = false,
  children,
}: SettingsCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="settings-card">
      <button
        type="button"
        className="settings-card-header"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
      >
        <div>
          <h3
            style={{
              fontFamily: "var(--font-display)",
              fontSize: 16,
              fontWeight: 600,
              color: "var(--color-text)",
              letterSpacing: "-0.01em",
            }}
          >
            {title}
          </h3>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", marginTop: 2 }}>
            {description}
          </p>
        </div>
        <ChevronIcon className={`settings-card-chevron${isOpen ? " open" : ""}`} />
      </button>
      {isOpen && <div className="settings-card-body">{children}</div>}
    </div>
  );
}
