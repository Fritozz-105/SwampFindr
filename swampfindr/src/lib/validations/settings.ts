import { z } from "zod";
import { validation } from "@/data/validation";

const v = validation.onboarding;

export const profileUpdateSchema = z.object({
  username: z
    .string()
    .min(2, v.username.minLength)
    .max(30, v.username.maxLength)
    .regex(/^[a-zA-Z0-9_]+$/, v.username.pattern),
  phone: z.string().regex(/^(\d{10}|)$/, v.phone.invalid),
});

export const preferencesUpdateSchema = z
  .object({
    bedrooms: z.coerce.number().int().min(0).max(6),
    bathrooms: z.coerce.number().int().min(1).max(6),
    price_min: z.coerce.number().int().min(0, v.price.min),
    price_max: z.coerce.number().int().min(0, v.price.min),
    distance_from_campus: z.string(),
    roommates: z.coerce.number().int().min(0).max(10),
    amenities: z.array(z.string()),
    excerpt: z.string().min(10, v.excerpt.minLength).max(200, v.excerpt.maxLength),
  })
  .refine((data) => data.price_max > data.price_min, {
    message: v.price.maxGreaterThanMin,
    path: ["price_max"],
  });

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, validation.password.currentRequired),
    password: z
      .string()
      .min(8, validation.password.minLength)
      .regex(/[A-Z]/, validation.password.uppercase)
      .regex(/[a-z]/, validation.password.lowercase)
      .regex(/[0-9]/, validation.password.number),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: validation.password.mismatch,
    path: ["confirmPassword"],
  });

export const changeEmailSchema = z.object({
  email: z.string().email(validation.email.invalid),
});

export type ProfileUpdateData = z.infer<typeof profileUpdateSchema>;
export type PreferencesUpdateData = z.infer<typeof preferencesUpdateSchema>;
export type ChangePasswordData = z.infer<typeof changePasswordSchema>;
export type ChangeEmailData = z.infer<typeof changeEmailSchema>;
