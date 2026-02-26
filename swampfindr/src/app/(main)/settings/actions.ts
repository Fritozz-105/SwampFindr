"use server";

import { createClient } from "@/lib/supabase/server";
import { changePasswordSchema, changeEmailSchema } from "@/lib/validations/settings";
import { errors } from "@/data/errors";

export type SettingsActionResult = {
  success?: boolean;
  error?: string;
  message?: string;
};

export async function changePassword(formData: FormData): Promise<SettingsActionResult> {
  const rawData = {
    currentPassword: formData.get("currentPassword") as string,
    password: formData.get("password") as string,
    confirmPassword: formData.get("confirmPassword") as string,
  };

  const parsed = changePasswordSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  const supabase = await createClient();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();
  if (userError || !user?.email) {
    return { error: errors.settings.passwordUpdateFailed };
  }

  const { error: signInError } = await supabase.auth.signInWithPassword({
    email: user.email,
    password: parsed.data.currentPassword,
  });
  if (signInError) {
    return { error: errors.settings.wrongCurrentPassword };
  }

  const { error } = await supabase.auth.updateUser({ password: parsed.data.password });

  if (error) {
    return { error: errors.settings.passwordUpdateFailed };
  }

  return { success: true, message: "Password updated successfully" };
}

export async function changeEmail(formData: FormData): Promise<SettingsActionResult> {
  const rawData = {
    email: formData.get("email") as string,
  };

  const parsed = changeEmailSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.updateUser({ email: parsed.data.email });

  if (error) {
    return { error: errors.settings.emailUpdateFailed };
  }

  return { success: true, message: "Confirmation email sent to your new address" };
}
