export const validation = {
  email: {
    invalid: "Please enter a valid email address",
  },
  password: {
    required: "Password is required",
    minLength: "Password must be at least 8 characters",
    uppercase: "Password must contain at least one uppercase letter",
    lowercase: "Password must contain at least one lowercase letter",
    number: "Password must contain at least one number",
    mismatch: "Passwords do not match",
  },
  fullName: {
    minLength: "Name must be at least 2 characters",
    maxLength: "Name is too long",
  },
  onboarding: {
    username: {
      minLength: "Username must be at least 2 characters",
      maxLength: "Username must be at most 30 characters",
      pattern: "Username can only contain letters, numbers, and underscores",
    },
    phone: {
      invalid: "Please enter a valid 10-digit phone number",
    },
    price: {
      maxGreaterThanMin: "Max price must be greater than min price",
      min: "Price must be a positive number",
    },
    excerpt: {
      minLength: "Please enter at least 10 characters",
      maxLength: "Must be at most 200 characters",
    },
  },
} as const;
