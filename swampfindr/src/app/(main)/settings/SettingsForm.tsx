"use client";

import { SettingsCard } from "@/components/ui";
import { settings } from "@/data/settings";
import { useProfile } from "@/hooks/useProfile";
import type { ProfileData } from "@/types/profile";
import { AvatarSection } from "./sections/AvatarSection";
import { EditProfileSection } from "./sections/EditProfileSection";
import { EditPreferencesSection } from "./sections/EditPreferencesSection";
import { ChangePasswordSection } from "./sections/ChangePasswordSection";
import { ChangeEmailSection } from "./sections/ChangeEmailSection";
import { MfaSection } from "./sections/MfaSection";

type SettingsFormProps = {
  user: { id: string; email: string; provider: string } | null;
  initialProfile: ProfileData | null;
};

export function SettingsForm({ user, initialProfile }: SettingsFormProps) {
  const { profile: liveProfile, refetch } = useProfile();
  const profile = liveProfile ?? initialProfile;

  if (!user) return null;

  const s = settings.sections;

  return (
    <div
      className="animate-fade-up"
      style={{
        borderRadius: "var(--radius-lg)",
        padding: "8px 24px",
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
      }}
    >
      <SettingsCard title={s.avatar.title} description={s.avatar.description} defaultOpen>
        <AvatarSection
          username={profile?.username ?? ""}
          avatarUrl={profile?.avatar_url ?? null}
          onUpdate={refetch}
        />
      </SettingsCard>

      <SettingsCard title={s.profile.title} description={s.profile.description} defaultOpen>
        <EditProfileSection
          username={profile?.username ?? ""}
          phone={profile?.phone ?? ""}
          onUpdate={refetch}
        />
      </SettingsCard>

      <SettingsCard title={s.preferences.title} description={s.preferences.description}>
        <EditPreferencesSection preferences={profile?.preferences ?? null} onUpdate={refetch} />
      </SettingsCard>

      <SettingsCard title={s.password.title} description={s.password.description}>
        <ChangePasswordSection provider={user.provider} />
      </SettingsCard>

      <SettingsCard title={s.email.title} description={s.email.description}>
        <ChangeEmailSection currentEmail={user.email} />
      </SettingsCard>

      <SettingsCard title={s.mfa.title} description={s.mfa.description}>
        <MfaSection />
      </SettingsCard>
    </div>
  );
}
