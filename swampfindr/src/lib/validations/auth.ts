import { z } from "zod";
import { validation } from "@/data/validation";

export const passwordSchema = z
  .string()
  .min(8, validation.password.minLength)
  .regex(/[A-Z]/, validation.password.uppercase)
  .regex(/[a-z]/, validation.password.lowercase)
  .regex(/[0-9]/, validation.password.number)
  .regex(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/, validation.password.specialChar);

export const loginSchema = z.object({
  email: z.string().email(validation.email.invalid),
  password: z.string().min(1, validation.password.required),
});

export const signupSchema = z
  .object({
    email: z.string().email(validation.email.invalid),
    password: passwordSchema,
    confirmPassword: z.string(),
    fullName: z.string().min(2, validation.fullName.minLength).max(100, validation.fullName.maxLength),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: validation.password.mismatch,
    path: ["confirmPassword"],
  });

export const updatePasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: validation.password.mismatch,
    path: ["confirmPassword"],
  });

export type LoginFormData = z.infer<typeof loginSchema>;
export type SignupFormData = z.infer<typeof signupSchema>;
export type UpdatePasswordFormData = z.infer<typeof updatePasswordSchema>;
