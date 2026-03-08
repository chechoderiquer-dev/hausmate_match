import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type FormEvent,
} from "react";
import { MadridDistrictMap } from "./components/madrid-district-map";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";
import { Checkbox } from "./components/ui/checkbox";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Select } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import {
  POLICY_VERSION,
  copy,
  districtGroups,
  type Language,
  type Option,
} from "./lib/content";
import { persistSubmission } from "./lib/supabase";
import { cn } from "./lib/utils";
import "./app.css";

type StatusTone = "error" | "success" | "warning";
type StepIndex = 0 | 1 | 2;

interface FormState {
  fullName: string;
  whatsapp: string;
  age: string;
  gender: string;
  budget: string;
  rooms: string;
  lookingFor: string;
  homeRoutinePreference: string;
  livingPreference: string;
  country: string;
  primaryLanguage: string;
  urgency: string;
  lifestyleTags: string[];
  districts: string[];
  otherArea: string;
  moveIn: string;
  moveOut: string;
  notes: string;
  consentPrivacy: boolean;
  consentShare: boolean;
  consentWhatsapp: boolean;
}

interface Notice {
  tone: StatusTone;
  message: string;
}

async function hashValue(value: string) {
  const bytes = new TextEncoder().encode(value);
  const buffer = await window.crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(buffer))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function getDefaultForm(language: Language): FormState {
  const set = copy[language];
  const today = new Date();
  const moveOut = new Date(today);
  moveOut.setDate(today.getDate() + 180);

  return {
    fullName: "",
    whatsapp: "",
    age: "25",
    gender: set.genderOptions[0],
    budget: "",
    rooms: "",
    lookingFor: "",
    homeRoutinePreference: set.homeRoutineOptions[0],
    livingPreference: set.livingOptions[0],
    country: set.countryDefault,
    primaryLanguage: set.languageOptions[0].value,
    urgency: set.urgencyOptions[1].value,
    lifestyleTags: [],
    districts: [],
    otherArea: "",
    moveIn: today.toISOString().slice(0, 10),
    moveOut: moveOut.toISOString().slice(0, 10),
    notes: "",
    consentPrivacy: false,
    consentShare: false,
    consentWhatsapp: false,
  };
}

function getOptionLabel(options: Option[], value: string) {
  return options.find((option) => option.value === value)?.label ?? value;
}

function sanitizeWhatsappInput(rawValue: string) {
  const allowed = rawValue.replace(/[^\d+\s()-]/g, "");
  let plusSeen = false;

  return allowed
    .split("")
    .filter((character, index) => {
      if (character !== "+") return true;
      if (index !== 0 || plusSeen) return false;
      plusSeen = true;
      return true;
    })
    .join("");
}

function isValidWhatsapp(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (!/^\+?[\d\s()-]+$/.test(trimmed)) return false;

  const digits = trimmed.replace(/\D/g, "");
  return digits.length >= 7 && digits.length <= 15;
}

function normalizeAgeInput(rawValue: string) {
  const digits = rawValue.replace(/\D/g, "");
  if (!digits) {
    return "";
  }

  const withoutLeadingZeros = digits.replace(/^0+(?=\d)/, "");
  const numeric = Number(withoutLeadingZeros);
  const clamped = Math.min(99, numeric);

  return String(clamped);
}

function getReadableError(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  if (error && typeof error === "object") {
    const maybeError = error as {
      message?: unknown;
      details?: unknown;
      hint?: unknown;
      code?: unknown;
    };

    const parts = [
      typeof maybeError.message === "string" ? maybeError.message : null,
      typeof maybeError.details === "string" ? maybeError.details : null,
      typeof maybeError.hint === "string" ? maybeError.hint : null,
    ].filter(Boolean) as string[];

    if (parts.length > 0) {
      return parts.join(" ");
    }

    if (typeof maybeError.code === "string") {
      return `Supabase error: ${maybeError.code}`;
    }
  }

  return String(error);
}

function renderRequiredLabel(text: string) {
  const trimmed = text.trimEnd();
  if (!trimmed.endsWith("*")) {
    return text;
  }

  const labelWithoutAsterisk = trimmed.slice(0, -1).trimEnd();
  return (
    <>
      {labelWithoutAsterisk} <span className="required-asterisk">*</span>
    </>
  );
}

export default function App() {
  const [language, setLanguage] = useState<Language>("Español");
  const [form, setForm] = useState<FormState>(() => getDefaultForm("Español"));
  const [step, setStep] = useState<StepIndex>(0);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [districtQuery, setDistrictQuery] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const [continueAttempted, setContinueAttempted] = useState(false);
  const [stickyDockProgress, setStickyDockProgress] = useState(0);
  const formRef = useRef<HTMLElement | null>(null);
  const stickyCtaRef = useRef<HTMLDivElement | null>(null);
  const transientNoticeTimerRef = useRef<number | null>(null);

  const content = useMemo(() => copy[language], [language]);
  const stepProgress = ((step + 1) / content.stepNames.length) * 100;

  const groupedDistricts = useMemo(() => {
    const query = districtQuery.trim().toLowerCase();
    return districtGroups
      .map((group) => ({
        key: group.key,
        districts: group.districts.filter((district) =>
          district.toLowerCase().includes(query),
        ),
      }))
      .filter((group) => group.districts.length > 0);
  }, [districtQuery]);

  const stepCompletion = useMemo(
    () => [
      Boolean(form.fullName.trim() && isValidWhatsapp(form.whatsapp)),
      Boolean(
        form.budget &&
          Number(form.budget) > 0 &&
          true,
      ),
      Boolean(
        form.consentPrivacy && form.consentShare && form.consentWhatsapp,
      ),
    ] as const,
    [form],
  );

  const canSubmit =
    stepCompletion[0] &&
    stepCompletion[1] &&
    stepCompletion[2] &&
    !submitting;

  const canContinue =
    (step === 0 && stepCompletion[0]) ||
    (step === 1 && stepCompletion[1]);

  const updateField = <Key extends keyof FormState>(
    key: Key,
    value: FormState[Key],
  ) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const toggleDistrict = (district: string) => {
    setForm((current) => {
      const exists = current.districts.includes(district);
      return {
        ...current,
        districts: exists
          ? current.districts.filter((item) => item !== district)
          : [...current.districts, district],
      };
    });
  };

  const toggleLifestyle = (tag: string) => {
    setForm((current) => {
      const exists = current.lifestyleTags.includes(tag);
      return {
        ...current,
        lifestyleTags: exists
          ? current.lifestyleTags.filter((item) => item !== tag)
          : [...current.lifestyleTags, tag],
      };
    });
  };

  const scrollToForm = () => {
    formRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const clearTransientNoticeTimer = () => {
    if (transientNoticeTimerRef.current !== null) {
      window.clearTimeout(transientNoticeTimerRef.current);
      transientNoticeTimerRef.current = null;
    }
  };

  const showTransientContinueNotice = (message: string) => {
    clearTransientNoticeTimer();
    setNotice({ tone: "error", message });
    const wordCount = message.trim().split(/\s+/).filter(Boolean).length;
    const durationMs = Math.max(1000, wordCount * 1000);
    transientNoticeTimerRef.current = window.setTimeout(() => {
      setNotice((current) =>
        current?.tone === "error" && current.message === message ? null : current,
      );
      transientNoticeTimerRef.current = null;
    }, durationMs);
  };

  const resetFlow = (nextLanguage: Language = language) => {
    clearTransientNoticeTimer();
    setForm(getDefaultForm(nextLanguage));
    setStep(0);
    setNotice(null);
    setDistrictQuery("");
    setIsComplete(false);
    setContinueAttempted(false);
  };

  const switchLanguage = (nextLanguage: Language) => {
    setLanguage(nextLanguage);
    setForm((current) => ({
      ...getDefaultForm(nextLanguage),
      fullName: current.fullName,
      whatsapp: current.whatsapp,
      age: current.age,
      budget: current.budget,
      rooms: current.rooms,
      lookingFor: current.lookingFor,
      homeRoutinePreference: current.homeRoutinePreference,
      gender: current.gender,
      livingPreference: current.livingPreference,
      country: current.country,
      primaryLanguage: current.primaryLanguage,
      urgency: current.urgency,
      lifestyleTags: current.lifestyleTags,
      districts: current.districts,
      otherArea: current.otherArea,
      moveIn: current.moveIn,
      moveOut: current.moveOut,
      notes: current.notes,
      consentPrivacy: current.consentPrivacy,
      consentShare: current.consentShare,
      consentWhatsapp: current.consentWhatsapp,
    }));
    clearTransientNoticeTimer();
    setNotice(null);
    setContinueAttempted(false);
  };

  const canAccessStep = (targetStep: StepIndex) => {
    if (targetStep === 0) return true;
    if (targetStep === 1) return stepCompletion[0];
    return stepCompletion[0] && stepCompletion[1];
  };

  const formatMissingMessage = (items: string[]) => {
    if (language === "Español") {
      return `Falta completar: ${items.join(", ")}.`;
    }

    return `Missing: ${items.join(", ")}.`;
  };

  const getContinueErrorMessage = (currentStep: StepIndex) => {
    if (currentStep === 0) {
      const missing = [
        !form.fullName.trim() ? content.name.replace(" *", "") : null,
        !form.whatsapp.trim()
          ? content.wa.replace(" *", "")
          : !isValidWhatsapp(form.whatsapp)
            ? content.waInvalid
            : null,
      ].filter(Boolean) as string[];

      return formatMissingMessage(missing);
    }

    if (currentStep === 1) {
      const missing = [
        !form.budget || Number(form.budget) <= 0 ? content.budget : null,
      ].filter(Boolean) as string[];

      return formatMissingMessage(missing);
    }

    const missing = [
      !form.consentPrivacy ? content.legalOpt1.replace(" *", "") : null,
      !form.consentShare ? content.legalOpt2.replace(" *", "") : null,
      !form.consentWhatsapp ? content.legalOpt3.replace(" *", "") : null,
    ].filter(Boolean) as string[];

    return formatMissingMessage(missing);
  };

  const navigateToStep = (targetStep: StepIndex) => {
    if (targetStep === step) return;
    if (targetStep < step || canAccessStep(targetStep)) {
      setStep(targetStep);
      clearTransientNoticeTimer();
      setNotice(null);
      setContinueAttempted(false);
      scrollToForm();
    }
  };

  const goToNextStep = () => {
    setContinueAttempted(true);

    if (step === 0 && !stepCompletion[0]) {
      showTransientContinueNotice(getContinueErrorMessage(0));
      return;
    }

    if (step === 1 && !stepCompletion[1]) {
      showTransientContinueNotice(getContinueErrorMessage(1));
      return;
    }

    clearTransientNoticeTimer();
    setNotice(null);
    setContinueAttempted(false);
    setStep((current) => (current < 2 ? ((current + 1) as StepIndex) : current));
    scrollToForm();
  };

  const goToPreviousStep = () => {
    clearTransientNoticeTimer();
    setNotice(null);
    setContinueAttempted(false);
    setStep((current) => (current > 0 ? ((current - 1) as StepIndex) : current));
    scrollToForm();
  };

  const handleContinueAction = () => {
    if (!canContinue) {
      setContinueAttempted(true);
      showTransientContinueNotice(getContinueErrorMessage(step));
      return;
    }

    goToNextStep();
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!stepCompletion[0] || !stepCompletion[1] || !stepCompletion[2]) {
      const missing = [
        !form.fullName.trim() ? content.name.replace(" *", "") : null,
        !form.whatsapp.trim()
          ? content.wa.replace(" *", "")
          : !isValidWhatsapp(form.whatsapp)
            ? content.waInvalid
            : null,
        !form.budget || Number(form.budget) <= 0 ? content.budget : null,
        !form.consentPrivacy ? content.legalOpt1.replace(" *", "") : null,
        !form.consentShare ? content.legalOpt2.replace(" *", "") : null,
        !form.consentWhatsapp ? content.legalOpt3.replace(" *", "") : null,
      ].filter(Boolean) as string[];

      clearTransientNoticeTimer();
      setNotice({ tone: "error", message: formatMissingMessage(missing) });
      return;
    }

    setSubmitting(true);
    clearTransientNoticeTimer();
    setNotice(null);

    const now = new Date();
    const cleanWhatsapp = form.whatsapp.replace(/\D/g, "");
    const dedupeKey = await hashValue(
      `${cleanWhatsapp}_${now.toISOString().slice(0, 10)}`,
    );
    const consentTimestamp = now.toISOString();
    const otherArea = form.otherArea.trim();
    const allAreas = [
      ...form.districts,
      ...(otherArea ? [otherArea] : []),
    ];
    const profileSummary = [
      form.notes.trim(),
      form.lifestyleTags.length > 0
        ? `${content.lifestyle}: ${form.lifestyleTags.join(", ")}`
        : "",
      `${content.urgency}: ${getOptionLabel(content.urgencyOptions, form.urgency)}`,
      form.lookingFor
        ? `${content.lookingFor}: ${getOptionLabel(content.lookingForOptions, form.lookingFor)}`
        : "",
      form.rooms ? `${content.rooms}: ${form.rooms}` : "",
      form.homeRoutinePreference
        ? `${content.homeRoutine}: ${form.homeRoutinePreference}`
        : "",
      otherArea ? `${content.otherArea}: ${otherArea}` : "",
    ]
      .filter(Boolean)
      .join("\n");

    const payload = {
      nombre: form.fullName.trim(),
      telefono: form.whatsapp.trim(),
      telefono_raw: form.whatsapp.trim(),
      dedupe_key: dedupeKey,
      budget: Number(form.budget),
      habitaciones: form.rooms,
      pref_genero: form.livingPreference,
      edad: form.age ? Number(form.age) : null,
      genero: form.gender,
      zona: allAreas.length > 0 ? allAreas.join(", ") : content.districtFallback,
      inicio: form.moveIn,
      fin: form.moveOut,
      idioma: getOptionLabel(content.languageOptions, form.primaryLanguage),
      Perfil: profileSummary,
      notas: `LOG LEGAL ${POLICY_VERSION} | ${consentTimestamp} | Pais: ${getOptionLabel(content.countryOptions, form.country)} | Consentimiento: OK`,
      created_at: consentTimestamp,
      policy_version: POLICY_VERSION,
      consent_timestamp: consentTimestamp,
      consent_language: language,
      consent_privacy: form.consentPrivacy,
      consent_share: form.consentShare,
      consent_whatsapp: form.consentWhatsapp,
    };

    try {
      await persistSubmission(payload);
      setIsComplete(true);
      clearTransientNoticeTimer();
      setNotice(null);
    } catch (error) {
      const readableError = getReadableError(error);
      const message = readableError.toLowerCase();

      if (message.includes("duplicate key")) {
        clearTransientNoticeTimer();
        setNotice({ tone: "warning", message: content.duplicate });
      } else {
        if (import.meta.env.DEV) {
          console.error("Submission failed:", error);
        }
        clearTransientNoticeTimer();
        setNotice({
          tone: "error",
          message: content.internalError,
        });
      }
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    return () => {
      clearTransientNoticeTimer();
    };
  }, []);

  useEffect(() => {
    let frame = 0;
    const preDockDistance = 140;

    const updateStickyState = () => {
      frame = 0;
      const stickyElement = stickyCtaRef.current;
      if (!stickyElement) return;

      const remainingScroll =
        document.documentElement.scrollHeight - (window.scrollY + window.innerHeight);
      const clampedRemaining = Math.max(0, remainingScroll);
      const progress = Math.max(
        0,
        Math.min(1, 1 - clampedRemaining / preDockDistance),
      );

      setStickyDockProgress((current) =>
        Math.abs(current - progress) < 0.01 ? current : progress,
      );
    };

    const scheduleUpdate = () => {
      if (frame !== 0) return;
      frame = window.requestAnimationFrame(updateStickyState);
    };

    scheduleUpdate();
    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);

    return () => {
      if (frame !== 0) {
        window.cancelAnimationFrame(frame);
      }
      window.removeEventListener("scroll", scheduleUpdate);
      window.removeEventListener("resize", scheduleUpdate);
    };
  }, []);

  if (isComplete) {
    return (
      <main className="app-shell">
        <div className="app-container">
          <div className="app-glow" />
          <Card className="completion-card">
            <div className="completion-smile">:)</div>
            <p className="kicker">{content.completionEyebrow}</p>
            <h1 className="hero-title completion-title">{content.completionTitle}</h1>
            <p className="completion-copy">{content.completionBody}</p>
            <Button onClick={() => resetFlow()}>{content.completionButton}</Button>
          </Card>
        </div>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <div className="app-container">
        <div className="app-glow" />

        <header className="hero-grid">
          <div className="hero-copy-block">
            <p className="eyebrow">{content.eyebrow}</p>
            <h1 className="hero-title">{content.headline}</h1>
            <p className="hero-copy">{content.intro}</p>
          </div>

          <div className="language-panel">
            <div className="logo-frame">
              <img
                alt="HausMate logo"
                className="logo"
                decoding="async"
                loading="eager"
                src="/logo_hausmate.png"
              />
            </div>
            <div className="language-toggle">
              {(["Español", "English"] as const).map((option) => (
                <Button
                  className={cn(
                    "language-option min-h-10 px-4 text-[length:var(--text-body)] font-semibold whitespace-nowrap",
                    language === option && "is-active",
                  )}
                  key={option}
                  onClick={() => switchLanguage(option)}
                  variant="ghost"
                >
                  {option}
                </Button>
              ))}
            </div>
          </div>
        </header>

        <section className="content-grid">
          <Card className="form-card">
            <section className="form-stack" ref={formRef}>
              <div className="section-header">
                <div className="progress-header">
                  <div>
                    <p className="progress-kicker">
                      {content.progressLabel} · {content.stepOf} {step + 1} /{" "}
                      {content.stepNames.length}
                    </p>
                    <h2 className="section-title">{content.stepNames[step]}</h2>
                  </div>
                  <div className="progress-track" aria-hidden="true">
                    <div
                      className="progress-bar"
                      style={{ width: `${stepProgress}%` }}
                    />
                  </div>
                </div>
                <div className="step-tabs" aria-label="Form steps">
                  {content.stepNames.map((name, index) => {
                    const targetStep = index as StepIndex;
                    return (
                      <button
                        className={cn(
                          "step-tab",
                          index === step && "is-active",
                          index < step && "is-complete",
                          !canAccessStep(targetStep) && targetStep > step && "is-locked",
                        )}
                        key={name}
                        onClick={() => navigateToStep(targetStep)}
                        type="button"
                      >
                        <span className="step-number">{index + 1}</span>
                        <span>{name}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="trust-note">{content.trustMessage}</p>
              </div>

              <form className="form-stack" id="match-form-form" onSubmit={handleSubmit}>
                {step === 0 ? (
                  <>
                    <div className="form-grid">
                      <div className="form-field">
                        <Label htmlFor="fullName">
                          {renderRequiredLabel(content.name)}
                        </Label>
                        <Input
                          id="fullName"
                          onChange={(event) =>
                            updateField("fullName", event.target.value)
                          }
                          placeholder={content.namePlaceholder}
                          value={form.fullName}
                        />
                        {continueAttempted && !form.fullName.trim() ? (
                          <p className="field-hint">{content.name.replace(" *", "")}</p>
                        ) : null}
                      </div>
                      <div className="form-field">
                        <Label htmlFor="whatsapp">
                          {renderRequiredLabel(content.wa)}
                        </Label>
                        <Input
                          id="whatsapp"
                          autoComplete="tel"
                          inputMode="tel"
                          onChange={(event) =>
                            updateField(
                              "whatsapp",
                              sanitizeWhatsappInput(event.target.value),
                            )
                          }
                          placeholder={content.waPlaceholder}
                          value={form.whatsapp}
                        />
                        {continueAttempted && !form.whatsapp.trim() ? (
                          <p className="field-hint">{content.wa.replace(" *", "")}</p>
                        ) : continueAttempted && !isValidWhatsapp(form.whatsapp) ? (
                          <p className="field-hint">{content.waInvalid}</p>
                        ) : null}
                      </div>
                      <div className="form-field">
                        <Label htmlFor="age">{content.age}</Label>
                        <Input
                          id="age"
                          autoComplete="off"
                          inputMode="numeric"
                          onChange={(event) =>
                            updateField("age", normalizeAgeInput(event.target.value))
                          }
                          type="text"
                          value={form.age}
                        />
                      </div>
                      <div className="form-field">
                        <Label htmlFor="gender">{content.gender}</Label>
                        <Select
                          id="gender"
                          onChange={(event) => updateField("gender", event.target.value)}
                          value={form.gender}
                        >
                          {content.genderOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="country">{content.country}</Label>
                        <Select
                          id="country"
                          onChange={(event) => updateField("country", event.target.value)}
                          value={form.country}
                        >
                          {content.countryOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="primaryLanguage">{content.language}</Label>
                        <Select
                          id="primaryLanguage"
                          onChange={(event) =>
                            updateField("primaryLanguage", event.target.value)
                          }
                          value={form.primaryLanguage}
                        >
                          {content.languageOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                    </div>
                  </>
                ) : null}

                {step === 1 ? (
                  <>
                    <div className="form-grid">
                      <div className="form-field">
                        <Label htmlFor="budget">
                          {renderRequiredLabel(content.budget)}
                        </Label>
                        <Input
                          id="budget"
                          min={0}
                          onChange={(event) =>
                            updateField("budget", event.target.value)
                          }
                          placeholder={content.budgetPlaceholder}
                          step={50}
                          type="number"
                          value={form.budget}
                        />
                        {continueAttempted && (!form.budget || Number(form.budget) <= 0) ? (
                          <p className="field-hint">{content.budget.replace(" *", "")}</p>
                        ) : null}
                      </div>
                      <div className="form-field">
                        <Label htmlFor="rooms">{content.rooms}</Label>
                        <Select
                          id="rooms"
                          onChange={(event) => updateField("rooms", event.target.value)}
                          value={form.rooms}
                        >
                          <option value="" disabled>
                            -
                          </option>
                          {content.roomOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="lookingFor">{content.lookingFor}</Label>
                        <Select
                          id="lookingFor"
                          onChange={(event) =>
                            updateField("lookingFor", event.target.value)
                          }
                          value={form.lookingFor}
                        >
                          <option value="">-</option>
                          {content.lookingForOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="livingPreference">
                          {content.livingPreference}
                        </Label>
                        <Select
                          id="livingPreference"
                          onChange={(event) =>
                            updateField("livingPreference", event.target.value)
                          }
                          value={form.livingPreference}
                        >
                          {content.livingOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="homeRoutinePreference">
                          {content.homeRoutine}
                        </Label>
                        <Select
                          id="homeRoutinePreference"
                          onChange={(event) =>
                            updateField("homeRoutinePreference", event.target.value)
                          }
                          value={form.homeRoutinePreference}
                        >
                          {content.homeRoutineOptions.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </Select>
                      </div>
                      <div className="form-field">
                        <Label htmlFor="urgency">{content.urgency}</Label>
                        <Select
                          id="urgency"
                          onChange={(event) => updateField("urgency", event.target.value)}
                          value={form.urgency}
                        >
                          {content.urgencyOptions.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                      </div>
                    </div>

                    <div className="district-section">
                      <div>
                        <h3 className="section-title">{content.lifestyle}</h3>
                      </div>
                      <div className="district-grid">
                        {content.lifestyleOptions.map((tag) => {
                          const selected = form.lifestyleTags.includes(tag);
                          return (
                            <button
                              className={cn("district-chip", selected && "is-selected")}
                              key={tag}
                              onClick={() => toggleLifestyle(tag)}
                              type="button"
                            >
                              {selected ? "✓ " : ""}
                              {tag}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="district-section">
                      <div>
                        <h3 className="section-title">{content.areas}</h3>
                        <p className="section-copy subcopy-spacing">{content.areasHelp}</p>
                      </div>

                      <div className="area-layout">
                        <div className="area-controls">
                          <div className="form-field">
                            <Label htmlFor="districtSearch">{content.zoneSearch}</Label>
                            <Input
                              id="districtSearch"
                              onChange={(event) => setDistrictQuery(event.target.value)}
                              placeholder={content.zoneSearchPlaceholder}
                              value={districtQuery}
                            />
                          </div>
                          <div className="form-field">
                            <Label htmlFor="otherArea">{content.otherArea}</Label>
                            <Input
                              id="otherArea"
                              onChange={(event) =>
                                updateField("otherArea", event.target.value)
                              }
                              placeholder={content.otherAreaPlaceholder}
                              value={form.otherArea}
                            />
                          </div>

                          {groupedDistricts.length > 0 ? (
                            <div className="district-groups">
                              {groupedDistricts.map((group) => (
                                <div className="district-group" key={group.key}>
                                  <p className="district-group-title">
                                    {content.zoneGroupLabels[group.key]}
                                  </p>
                                  <div className="district-grid">
                                    {group.districts.map((district) => {
                                      const selected = form.districts.includes(district);
                                      return (
                                        <button
                                          className={cn(
                                            "district-chip",
                                            selected && "is-selected",
                                          )}
                                          key={district}
                                          onClick={() => toggleDistrict(district)}
                                          type="button"
                                        >
                                          {selected ? "✓ " : ""}
                                          {district}
                                        </button>
                                      );
                                    })}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="empty-state">{content.noZoneResults}</p>
                          )}
                        </div>

                        <MadridDistrictMap
                          body={content.areaMapBody}
                          onToggleDistrict={toggleDistrict}
                          selectedDistricts={form.districts}
                          title={content.areaMapTitle}
                        />
                      </div>
                    </div>
                  </>
                ) : null}

                {step === 2 ? (
                  <>
                    <div className="form-grid">
                      <div className="form-field">
                        <Label htmlFor="moveIn">{content.moveIn}</Label>
                        <Input
                          id="moveIn"
                          onChange={(event) => updateField("moveIn", event.target.value)}
                          type="date"
                          value={form.moveIn}
                        />
                      </div>
                      <div className="form-field">
                        <Label htmlFor="moveOut">{content.moveOut}</Label>
                        <Input
                          id="moveOut"
                          onChange={(event) => updateField("moveOut", event.target.value)}
                          type="date"
                          value={form.moveOut}
                        />
                      </div>
                    </div>

                    <div className="form-field">
                      <Label htmlFor="notes">{content.notes}</Label>
                      <Textarea
                        id="notes"
                        onChange={(event) => updateField("notes", event.target.value)}
                        placeholder={content.notesPlaceholder}
                        value={form.notes}
                      />
                    </div>

                    <div className="legal-panel">
                      <h3 className="section-title">{content.legalHeader}</h3>

                      <label className="checkbox-row">
                        <Checkbox
                          checked={form.consentPrivacy}
                          onChange={(event) =>
                            updateField("consentPrivacy", event.target.checked)
                          }
                        />
                        <span>{renderRequiredLabel(content.legalOpt1)}</span>
                      </label>

                      <label className="checkbox-row">
                        <Checkbox
                          checked={form.consentShare}
                          onChange={(event) =>
                            updateField("consentShare", event.target.checked)
                          }
                        />
                        <span>{renderRequiredLabel(content.legalOpt2)}</span>
                      </label>

                      <label className="checkbox-row">
                        <Checkbox
                          checked={form.consentWhatsapp}
                          onChange={(event) =>
                            updateField("consentWhatsapp", event.target.checked)
                          }
                        />
                        <span>{renderRequiredLabel(content.legalOpt3)}</span>
                      </label>

                      <details className="policy-details">
                        <summary className="policy-summary">{content.viewPolicy}</summary>
                        <div className="policy-body">{content.policyContent}</div>
                      </details>
                    </div>
                  </>
                ) : null}

                <div className="form-actions desktop-actions">
                  <div className="form-actions-left">
                    {step > 0 ? (
                      <Button
                        className="back-step-button"
                        onClick={goToPreviousStep}
                        type="button"
                        variant="ghost"
                      >
                        {content.previousStep}
                      </Button>
                    ) : (
                      <div />
                    )}

                    {notice ? (
                      <div
                        className={cn(
                          "notice action-notice",
                          notice.tone === "success" && "notice-success",
                          notice.tone === "warning" && "notice-warning",
                          notice.tone === "error" && "notice-error",
                        )}
                      >
                        {notice.message}
                      </div>
                    ) : null}
                  </div>

                  {step < 2 ? (
                    <Button
                      aria-disabled={!canContinue}
                      className={cn(
                        "cta-button",
                        !canContinue && "is-disabled-action",
                      )}
                      onClick={handleContinueAction}
                      type="button"
                    >
                      {content.nextStep}
                    </Button>
                  ) : (
                    <Button className="cta-button" disabled={!canSubmit} type="submit">
                      {submitting ? content.loading : content.submit}
                    </Button>
                  )}
                </div>
              </form>
            </section>
          </Card>
        </section>

        <div
          className="sticky-cta"
          ref={stickyCtaRef}
          style={
            {
              "--sticky-dock-progress": String(stickyDockProgress),
            } as CSSProperties
          }
        >
          <div className="sticky-cta-inner">
            <div className="sticky-copy">
              <span className="sticky-step">
                {content.stepOf} {step + 1} / {content.stepNames.length}
              </span>
              <span className="sticky-title">{content.stepNames[step]}</span>
            </div>
            {step < 2 ? (
              <Button
                aria-disabled={!canContinue}
                className={cn(
                  "cta-button sticky-cta-button",
                  !canContinue && "is-disabled-action",
                )}
                onClick={handleContinueAction}
                type="button"
              >
                {content.stickyCta}
              </Button>
            ) : (
              <Button
                className="cta-button sticky-cta-button"
                disabled={!canSubmit}
                form="match-form-form"
                type="submit"
              >
                {submitting ? content.loading : content.submit}
              </Button>
            )}
          </div>
          {notice ? (
            <div
              className={cn(
                "notice mobile-action-feedback",
                notice.tone === "success" && "notice-success",
                notice.tone === "warning" && "notice-warning",
                notice.tone === "error" && "notice-error",
              )}
            >
              {notice.message}
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
