"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import type { ProfileData } from "@/types/profile";

const API_URL = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:8080";

export function useProfile() {
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profiles/me`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!res.ok) {
        setError("Failed to load profile");
        setLoading(false);
        return;
      }

      const body = await res.json();
      setProfile(body.data);
    } catch {
      setError("Could not connect to server");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return { profile, loading, error, refetch: fetchProfile };
}
