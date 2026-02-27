import { z } from "zod";
import { validation } from "@/data/validation";

const v = validation.onboarding;

export const profileStepSchema = z.object({
  username: z
    .string()
    .min(2, v.username.minLength)
    .max(30, v.username.maxLength)
    .regex(/^[a-zA-Z0-9_]+$/, v.username.pattern),
  phone: z
    .string()
    .regex(/^(\d{10}|)$/, v.phone.invalid),
});

export const preferencesStepSchema = z
  .object({
    bedrooms: z.coerce.number().int().min(0).max(6),
    bathrooms: z.coerce.number().int().min(1).max(6),
    price_min: z.coerce.number().int().min(0, v.price.min),
    price_max: z.coerce.number().int().min(0, v.price.min),
    distance_from_campus: z.string(),
    roommates: z.coerce.number().int().min(0).max(10),
  })
  .refine((data) => data.price_max > data.price_min, {
    message: v.price.maxGreaterThanMin,
    path: ["price_max"],
  });

export const amenitiesStepSchema = z.object({
  amenities: z.array(z.string()),
  excerpt: z.string().min(10, v.excerpt.minLength).max(200, v.excerpt.maxLength),
});

export const onboardingSchema = z
  .object({
    username: z
      .string()
      .min(2, v.username.minLength)
      .max(30, v.username.maxLength)
      .regex(/^[a-zA-Z0-9_]+$/, v.username.pattern),
    phone: z
      .string()
      .regex(/^(\d{10}|)$/, v.phone.invalid),
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

export type ProfileStepData = z.infer<typeof profileStepSchema>;
export type PreferencesStepData = z.infer<typeof preferencesStepSchema>;
export type AmenitiesStepData = z.infer<typeof amenitiesStepSchema>;
export type OnboardingData = z.infer<typeof onboardingSchema>;
