"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { loginSchema, signupSchema, updatePasswordSchema } from "@/lib/validations/auth";
import { headers } from "next/headers";
import { errors } from "@/data/errors";
import { normalizeEmail, sanitizeName, isValidEmail } from "@/lib/utils/sanitization";

export type AuthResult = {
  error?: string;
  success?: boolean;
};

export async function login(formData: FormData): Promise<AuthResult> {
  const supabase = await createClient();

  const rawData = {
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  };

  const parsed = loginSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  // Normalize email to lowercase to prevent case-sensitivity issues
  const normalizedEmail = normalizeEmail(parsed.data.email);

  const { error } = await supabase.auth.signInWithPassword({
    email: normalizedEmail,
    password: parsed.data.password,
  });

  if (error) {
    // Use generic error message to prevent user enumeration
    return { error: errors.login.invalid };
  }

  revalidatePath("/", "layout");
  redirect("/dashboard");
}

export async function signup(formData: FormData): Promise<AuthResult> {
  const supabase = await createClient();

  const rawData = {
    email: formData.get("email") as string,
    password: formData.get("password") as string,
    confirmPassword: formData.get("confirmPassword") as string,
    fullName: formData.get("fullName") as string,
  };

  const parsed = signupSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  // Normalize email to lowercase and trim whitespace
  const normalizedEmail = normalizeEmail(parsed.data.email);
  
  // Sanitize full name - trim and normalize whitespace
  const sanitizedFullName = sanitizeName(parsed.data.fullName);

  const { error } = await supabase.auth.signUp({
    email: normalizedEmail,
    password: parsed.data.password,
    options: {
      data: {
        full_name: sanitizedFullName,
      },
    },
  });

  if (error) {
    // Use generic error message to prevent user enumeration
    return { error: errors.signup.generic };
  }

  revalidatePath("/", "layout");
  redirect("/auth/login?message=Check your email to confirm your account");
}

export async function signInWithOAuth(provider: "google" | "apple" | "facebook") {
  const supabase = await createClient();
  const headersList = await headers();
  const origin = headersList.get("origin");

  // Validate origin is set and matches expected domain
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!appUrl) {
    return { error: "Application configuration error" };
  }

  // Use configured app URL instead of request origin to prevent manipulation
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${appUrl}/auth/callback`,
    },
  });

  if (error) {
    return { error: errors.oauth.providerFailed };
  }

  if (data.url) {
    redirect(data.url);
  }
}

export async function logout() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/auth/login");
}

export async function updatePassword(formData: FormData): Promise<AuthResult> {
  const supabase = await createClient();

  const rawData = {
    password: formData.get("password") as string,
    confirmPassword: formData.get("confirmPassword") as string,
  };

  const parsed = updatePasswordSchema.safeParse(rawData);
  if (!parsed.success) {
    return { error: parsed.error.issues[0].message };
  }

  // Verify user is authenticated before updating password
  const { data: { user }, error: userError } = await supabase.auth.getUser();
  
  if (userError || !user) {
    return { error: "You must be logged in to update your password" };
  }

  const { error } = await supabase.auth.updateUser({
    password: parsed.data.password,
  });

  if (error) {
    return { error: errors.updatePassword.generic };
  }

  revalidatePath("/", "layout");
  redirect("/auth/login?message=Password updated successfully. Please sign in.");
}

export async function resetPassword(formData: FormData): Promise<AuthResult> {
  const supabase = await createClient();
  const rawEmail = formData.get("email") as string;

  if (!rawEmail) {
    return { error: errors.resetPassword.emailRequired };
  }

  // Normalize email
  const email = normalizeEmail(rawEmail);

  // Validate email format
  if (!isValidEmail(email)) {
    return { error: "Please enter a valid email address" };
  }

  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!appUrl) {
    return { error: "Application configuration error" };
  }

  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${appUrl}/auth/callback?type=recovery`,
  });

  if (error) {
    // Use generic error message to prevent user enumeration
    return { error: errors.resetPassword.generic };
  }

  // Always return success even if email doesn't exist to prevent enumeration
  return { success: true };
}
