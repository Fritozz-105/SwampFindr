"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { StepIndicator, Alert } from "@/components/ui";
import { onboarding, errors as errorMessages } from "@/data";
import {
  profileStepSchema,
  preferencesStepSchema,
  amenitiesStepSchema,
  onboardingSchema,
  type OnboardingData,
} from "@/lib/validations/onboarding";
import { createClient } from "@/lib/supabase/client";
import { ProfileStep } from "./steps/ProfileStep";
import { PreferencesStep } from "./steps/PreferencesStep";
import { AmenitiesStep } from "./steps/AmenitiesStep";

const STORAGE_KEY = "onboarding_form_data";

const STEPS = [
  { title: onboarding.steps.profile.title },
  { title: onboarding.steps.preferences.title },
  { title: onboarding.steps.amenities.title },
];

const defaultData: OnboardingData = {
  username: "",
  phone: "",
  bedrooms: 1,
  bathrooms: 1,
  price_min: 500,
  price_max: 2000,
  distance_from_campus: "any",
  roommates: 0,
  amenities: [],
  excerpt: "",
};

function loadSavedData(): OnboardingData {
  if (typeof window === "undefined") return defaultData;
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) return { ...defaultData, ...JSON.parse(saved) };
  } catch {
    /* ignore */
  }
  return defaultData;
}

export function OnboardingForm() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<OnboardingData>(() => loadSavedData());
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState("");
  const [isPending, setIsPending] = useState(false);

  // Persist to sessionStorage on change
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    } catch {
      /* ignore */
    }
  }, [data]);

  const handleChange = useCallback((field: keyof OnboardingData, value: unknown) => {
    setData((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => {
      if (!prev[field]) return prev;
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  function validateCurrentStep(): boolean {
    const schemas = [profileStepSchema, preferencesStepSchema, amenitiesStepSchema];
    const result = schemas[currentStep].safeParse(data);

    if (result.success) {
      setFieldErrors({});
      return true;
    }

    const errs: Record<string, string> = {};
    for (const issue of result.error.issues) {
      const key = issue.path[0]?.toString();
      if (key && !errs[key]) {
        errs[key] = issue.message;
      }
    }
    setFieldErrors(errs);
    return false;
  }

  function handleNext() {
    if (validateCurrentStep()) {
      setCurrentStep((s) => s + 1);
    }
  }

  function handleBack() {
    setFieldErrors({});
    setCurrentStep((s) => s - 1);
  }

  async function handleSubmit() {
    const result = onboardingSchema.safeParse(data);
    if (!result.success) {
      const errs: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0]?.toString();
        if (key && !errs[key]) {
          errs[key] = issue.message;
        }
      }
      setFieldErrors(errs);
      return;
    }

    setIsPending(true);
    setSubmitError("");

    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        setSubmitError("Session expired. Please log in again.");
        setIsPending(false);
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_FLASK_API_URL ?? "http://localhost:5000";
      const res = await fetch(`${apiUrl}/api/v1/profiles/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(result.data),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setSubmitError(body?.error ?? errorMessages.onboarding.submitFailed);
        setIsPending(false);
        return;
      }

      // Success, clear storage, set cookie, redirect
      sessionStorage.removeItem(STORAGE_KEY);
      document.cookie = "onboarding_completed=true; path=/; max-age=31536000; SameSite=Lax";
      router.push("/dashboard");
    } catch {
      setSubmitError(errorMessages.onboarding.networkError);
      setIsPending(false);
    }
  }

  const isLastStep = currentStep === STEPS.length - 1;

  const isStepValid = (() => {
    const schemas = [profileStepSchema, preferencesStepSchema, amenitiesStepSchema];
    return schemas[currentStep].safeParse(data).success;
  })();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      <StepIndicator steps={STEPS} currentStep={currentStep} />

      {submitError && <Alert variant="error">{submitError}</Alert>}

      {currentStep === 0 && (
        <ProfileStep data={data} onChange={handleChange} errors={fieldErrors} />
      )}
      {currentStep === 1 && (
        <PreferencesStep data={data} onChange={handleChange} errors={fieldErrors} />
      )}
      {currentStep === 2 && (
        <AmenitiesStep data={data} onChange={handleChange} errors={fieldErrors} />
      )}

      <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
        {currentStep > 0 && (
          <button type="button" className="btn-secondary" onClick={handleBack} style={{ flex: 1 }}>
            {onboarding.buttons.back}
          </button>
        )}
        {isLastStep ? (
          <button
            type="button"
            className="btn-primary"
            disabled={isPending || !isStepValid}
            onClick={handleSubmit}
            style={{ flex: 1 }}
          >
            {isPending ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span className="spinner" />
              </span>
            ) : (
              onboarding.buttons.finish
            )}
          </button>
        ) : (
          <button
            type="button"
            className="btn-primary"
            disabled={!isStepValid}
            onClick={handleNext}
            style={{ flex: 1 }}
          >
            {onboarding.buttons.continue}
          </button>
        )}
      </div>
    </div>
  );
}
