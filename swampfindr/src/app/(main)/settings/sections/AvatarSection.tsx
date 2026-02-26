"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import { createClient } from "@/lib/supabase/client";
import { settings } from "@/data/settings";
import { errors } from "@/data/errors";
import { Alert } from "@/components/ui";

const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:5000";
const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MIME_TO_EXT: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
};

type AvatarSectionProps = {
  username: string;
  avatarUrl: string | null;
  onUpdate: () => void;
};

export function AvatarSection({ username, avatarUrl, onUpdate }: AvatarSectionProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Please upload a JPG, PNG, or WebP image.");
      return;
    }
    if (file.size > MAX_SIZE) {
      setError("File must be under 5 MB.");
      return;
    }

    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const supabase = createClient();
      const {
        data: { user },
        error: authErr,
      } = await supabase.auth.getUser();

      if (authErr || !user) {
        setError("Not authenticated. Please refresh and try again.");
        setUploading(false);
        return;
      }

      const ext = MIME_TO_EXT[file.type] ?? "jpg";
      const path = `${user.id}/${Date.now()}.${ext}`;

      const { error: uploadErr } = await supabase.storage
        .from("avatars")
        .upload(path, file, { upsert: true });

      if (uploadErr) {
        setError(errors.settings.avatarUploadFailed);
        setUploading(false);
        return;
      }

      const { data: urlData } = supabase.storage.from("avatars").getPublicUrl(path);

      const {
        data: { session },
      } = await supabase.auth.getSession();

      const res = await fetch(`${API_URL}/api/v1/profiles/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({ avatar_url: urlData.publicUrl }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.error ?? errors.settings.avatarUploadFailed);
        setUploading(false);
        return;
      }

      setSuccess(settings.messages.avatarUpdated);
      onUpdate();
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleRemove() {
    setUploading(true);
    setError("");
    setSuccess("");

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        setError("Not authenticated. Please refresh and try again.");
        setUploading(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profiles/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ avatar_url: null }),
      });

      if (!res.ok) {
        setError(errors.settings.avatarUploadFailed);
        setUploading(false);
        return;
      }

      setSuccess(settings.messages.avatarRemoved);
      onUpdate();
    } catch {
      setError(errors.settings.networkError);
    } finally {
      setUploading(false);
    }
  }

  const initial = username?.charAt(0)?.toUpperCase() || "?";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        {avatarUrl ? (
          <Image src={avatarUrl} alt="Avatar" width={80} height={80} className="avatar-circle" />
        ) : (
          <div className="avatar-placeholder">{initial}</div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="btn-primary"
              style={{ padding: "8px 16px", fontSize: 14, width: "auto" }}
              disabled={uploading}
              onClick={() => fileRef.current?.click()}
            >
              {uploading
                ? settings.sections.avatar.uploading
                : settings.sections.avatar.uploadButton}
            </button>
            {avatarUrl && (
              <button
                type="button"
                className="btn-secondary"
                style={{ padding: "8px 16px", fontSize: 14 }}
                disabled={uploading}
                onClick={handleRemove}
              >
                {settings.sections.avatar.removeButton}
              </button>
            )}
          </div>
          <p style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
            {settings.sections.avatar.maxSize}
          </p>
        </div>

        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          style={{ display: "none" }}
          onChange={handleUpload}
        />
      </div>

      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}
    </div>
  );
}
