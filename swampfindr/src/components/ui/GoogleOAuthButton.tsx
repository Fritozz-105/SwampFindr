"use client";

import type { ReactNode } from "react";
import { GoogleIcon } from "./icons";

type GoogleOAuthButtonProps = {
  onClick: () => void;
  children?: ReactNode;
};

export function GoogleOAuthButton({
  onClick,
  children = "Continue with Google",
}: GoogleOAuthButtonProps) {
  return (
    <button type="button" className="btn-google" onClick={onClick}>
      <GoogleIcon />
      {children}
    </button>
  );
}
