"use client";

import React, { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, SkipForward } from "lucide-react";
import { apiFetch } from "@/lib/api";

export interface WizardDraft {
  age: number;
  sex: "male" | "female";
  heightCm: number;
  weightKg: number;
  waistCm: number;
  systolicBp: number;
  diastolicBp: number;
  restingHr: string;
  city: string;
  pincode: string;
  redFlags: {
    chest_pain_or_pressure: boolean;
    pain_spreading_arm_or_jaw: boolean;
    severe_breathlessness_at_rest: boolean;
    fainting: boolean;
    face_drooping: boolean;
    arm_weakness: boolean;
    speech_difficulty: boolean;
    sudden_confusion: boolean;
    vomiting_blood: boolean;
    black_stools: boolean;
    persistent_vomiting: boolean;
    fruity_breath: boolean;
  };
  smoker: boolean;
  alcoholDrinksPerWeek: number;
  physicalActivity: "vigorous" | "moderate" | "mild" | "sedentary";
  sittingHours: string;
  sleepHours: string;
  familyDiabetes: "none" | "one_parent" | "both";
  familyHeartDisease: boolean;
  fpg: string;
  hba1c: string;
  ogtt2h: string;
  totalChol: string;
  ldl: string;
  hdl: string;
  triglycerides: string;
  creatinine: string;
  urineAcr: string;
  consentStorage: boolean;
}

export const DEFAULT_WIZARD_DRAFT: WizardDraft = {
  age: 48,
  sex: "male",
  heightCm: 170,
  weightKg: 72,
  waistCm: 92,
  systolicBp: 134,
  diastolicBp: 84,
  restingHr: "74",
  city: "New Delhi",
  pincode: "",
  redFlags: {
    chest_pain_or_pressure: false,
    pain_spreading_arm_or_jaw: false,
    severe_breathlessness_at_rest: false,
    fainting: false,
    face_drooping: false,
    arm_weakness: false,
    speech_difficulty: false,
    sudden_confusion: false,
    vomiting_blood: false,
    black_stools: false,
    persistent_vomiting: false,
    fruity_breath: false,
  },
  smoker: false,
  alcoholDrinksPerWeek: 0,
  physicalActivity: "moderate",
  sittingHours: "6",
  sleepHours: "7",
  familyDiabetes: "none",
  familyHeartDisease: false,
  fpg: "",
  hba1c: "",
  ogtt2h: "",
  totalChol: "",
  ldl: "",
  hdl: "",
  triglycerides: "",
  creatinine: "",
  urineAcr: "",
  consentStorage: false,
};

interface AssessmentWizardProps {
  t: Record<string, string>;
  token: string | null;
  initialStep?: 1 | 2 | 3;
  draft: WizardDraft;
  onDraftChange: (next: WizardDraft) => void;
  onComplete: (result: any) => void;
}

const INPUT_CLS =
  "w-full min-h-[44px] px-3.5 py-2 rounded-xl bg-[#FFF9E3]/60 border border-[#EFE4BE] text-[#2B2208] tabular-nums placeholder-[#6B5B2E]/60 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition text-sm font-medium";

const LABEL_CLS = "block text-xs font-bold uppercase tracking-wider text-[#6B5B2E] mb-1.5";

export const LAB_TEST_PRESETS: {
  id: string;
  label: string;
  badge: string;
  patch: Partial<WizardDraft>;
}[] = [
  {
    id: "healthy_baseline",
    label: "1. Healthy Baseline (42F, Bengaluru)",
    badge: "Low Risk",
    patch: {
      age: 42,
      sex: "female",
      heightCm: 162,
      weightKg: 56,
      waistCm: 74,
      systolicBp: 116,
      diastolicBp: 74,
      city: "Bengaluru",
      smoker: false,
      physicalActivity: "vigorous",
      familyDiabetes: "none",
      fpg: "88",
      hba1c: "5.2",
      ogtt2h: "112",
      totalChol: "168",
      ldl: "92",
      hdl: "56",
      triglycerides: "95",
      creatinine: "0.78",
      urineAcr: "10",
    },
  },
  {
    id: "prediabetes_metabolic",
    label: "2. Prediabetes + Metabolic (46M, New Delhi)",
    badge: "Moderate / High",
    patch: {
      age: 46,
      sex: "male",
      heightCm: 171,
      weightKg: 74,
      waistCm: 94,
      systolicBp: 134,
      diastolicBp: 84,
      city: "New Delhi",
      smoker: false,
      physicalActivity: "mild",
      familyDiabetes: "one_parent",
      fpg: "114",
      hba1c: "6.1",
      ogtt2h: "162",
      totalChol: "212",
      ldl: "136",
      hdl: "37",
      triglycerides: "185",
      creatinine: "0.95",
      urineAcr: "22",
    },
  },
  {
    id: "heart_hypertension",
    label: "3. Heart + Stage 2 BP (58M Smoker, Mumbai)",
    badge: "High CVD",
    patch: {
      age: 58,
      sex: "male",
      heightCm: 172,
      weightKg: 80,
      waistCm: 99,
      systolicBp: 154,
      diastolicBp: 96,
      city: "Mumbai",
      smoker: true,
      physicalActivity: "sedentary",
      familyDiabetes: "none",
      familyHeartDisease: true,
      fpg: "102",
      hba1c: "5.8",
      ogtt2h: "",
      totalChol: "248",
      ldl: "162",
      hdl: "35",
      triglycerides: "210",
      creatinine: "1.15",
      urineAcr: "38",
    },
  },
  {
    id: "diabetes_kidney",
    label: "4. Diabetes + Kidney Strain (62F, Jaipur)",
    badge: "CKD + DM",
    patch: {
      age: 62,
      sex: "female",
      heightCm: 156,
      weightKg: 65,
      waistCm: 90,
      systolicBp: 146,
      diastolicBp: 90,
      city: "Jaipur",
      smoker: false,
      physicalActivity: "mild",
      familyDiabetes: "both",
      fpg: "164",
      hba1c: "7.9",
      ogtt2h: "228",
      totalChol: "228",
      ldl: "142",
      hdl: "42",
      triglycerides: "195",
      creatinine: "1.75",
      urineAcr: "165",
    },
  },
  {
    id: "high_risk_multi",
    label: "5. Multi-Risk Senior (66M, Chennai)",
    badge: "Urgent Review",
    patch: {
      age: 66,
      sex: "male",
      heightCm: 168,
      weightKg: 84,
      waistCm: 105,
      systolicBp: 166,
      diastolicBp: 98,
      city: "Chennai",
      smoker: true,
      physicalActivity: "sedentary",
      familyDiabetes: "both",
      familyHeartDisease: true,
      fpg: "188",
      hba1c: "8.4",
      ogtt2h: "256",
      totalChol: "262",
      ldl: "174",
      hdl: "32",
      triglycerides: "265",
      creatinine: "2.15",
      urineAcr: "340",
    },
  },
];

export function AssessmentWizard({
  t,
  token,
  initialStep = 1,
  draft,
  onDraftChange,
  onComplete,
}: AssessmentWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3>(initialStep);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const update = (patch: Partial<WizardDraft>) => {
    onDraftChange({ ...draft, ...patch });
  };

  const autoBmi = useMemo(() => {
    if (draft.heightCm <= 0 || draft.weightKg <= 0) return null;
    const bmi = draft.weightKg / ((draft.heightCm / 100) ** 2);
    const cat =
      bmi < 18.5
        ? "Underweight"
        : bmi < 23
        ? "Normal"
        : bmi < 25
        ? "Overweight (Indian >=23)"
        : "Obese (Indian >=25)";
    return { value: bmi.toFixed(1), cat };
  }, [draft.heightCm, draft.weightKg]);

  const autoEgfr = useMemo(() => {
    const scr = Number(draft.creatinine);
    if (!draft.creatinine || Number.isNaN(scr) || scr <= 0 || draft.age <= 0) return null;
    const isFemale = draft.sex === "female";
    const kappa = isFemale ? 0.7 : 0.9;
    const alpha = isFemale ? -0.241 : -0.302;
    const sf = isFemale ? 1.012 : 1.0;
    const ratio = scr / kappa;
    const egfr =
      142 *
      (Math.min(ratio, 1) ** alpha) *
      (Math.max(ratio, 1) ** -1.2) *
      (0.9938 ** draft.age) *
      sf;
    return egfr.toFixed(1);
  }, [draft.creatinine, draft.age, draft.sex]);

  const validateStep1 = (): string | null => {
    if (draft.age < 1 || draft.age > 120) return "Age must be between 1 and 120 years.";
    if (draft.heightCm < 50 || draft.heightCm > 250) return "Height must be between 50 and 250 cm.";
    if (draft.weightKg < 15 || draft.weightKg > 300) return "Weight must be between 15 and 300 kg.";
    if (draft.waistCm < 30 || draft.waistCm > 220) return "Waist circumference must be between 30 and 220 cm.";
    if (draft.systolicBp < 60 || draft.systolicBp > 260) return "Systolic BP must be between 60 and 260 mmHg.";
    if (draft.diastolicBp < 30 || draft.diastolicBp > 180) return "Diastolic BP must be between 30 and 180 mmHg.";
    if (draft.restingHr.trim() !== "") {
      const hr = Number(draft.restingHr);
      if (Number.isNaN(hr) || hr < 30 || hr > 220) return "Resting heart rate must be between 30 and 220 bpm.";
    }
    return null;
  };

  const validateStep2 = (): string | null => {
    if (draft.alcoholDrinksPerWeek < 0 || draft.alcoholDrinksPerWeek > 100) {
      return "Alcohol drinks per week must be between 0 and 100.";
    }
    if (draft.sittingHours.trim() !== "") {
      const sh = Number(draft.sittingHours);
      if (Number.isNaN(sh) || sh < 0 || sh > 24) return "Sitting hours must be between 0 and 24.";
    }
    if (draft.sleepHours.trim() !== "") {
      const sl = Number(draft.sleepHours);
      if (Number.isNaN(sl) || sl < 0 || sl > 24) return "Sleep hours must be between 0 and 24.";
    }
    return null;
  };

  const validateLabs = (): string | null => {
    const checks: [string, string, number, number][] = [
      ["Fasting Glucose", draft.fpg, 20, 1000],
      ["HbA1c", draft.hba1c, 2, 200],
      ["2h Glucose", draft.ogtt2h, 20, 1000],
      ["Total Cholesterol", draft.totalChol, 50, 800],
      ["LDL Cholesterol", draft.ldl, 10, 500],
      ["HDL Cholesterol", draft.hdl, 10, 150],
      ["Triglycerides", draft.triglycerides, 20, 2000],
      ["Serum Creatinine", draft.creatinine, 0.1, 20],
      ["Urine ACR", draft.urineAcr, 0, 5000],
    ];
    for (const [name, raw, minV, maxV] of checks) {
      if (raw.trim() !== "") {
        const val = Number(raw);
        if (Number.isNaN(val) || val < minV || val > maxV) {
          return `${name} must be between ${minV} and ${maxV} (entered: ${raw}).`;
        }
      }
    }
    return null;
  };

  const submitAssessment = async (skipLabs: boolean) => {
    const err1 = validateStep1();
    if (err1) {
      setStep(1);
      setErrorMsg(err1);
      return;
    }
    const err2 = validateStep2();
    if (err2) {
      setStep(2);
      setErrorMsg(err2);
      return;
    }
    if (!skipLabs) {
      const err3 = validateLabs();
      if (err3) {
        setErrorMsg(err3);
        return;
      }
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const payload = {
        age: Number(draft.age),
        sex: draft.sex,
        height_cm: Number(draft.heightCm),
        weight_kg: Number(draft.weightKg),
        waist_cm: Number(draft.waistCm),
        systolic_bp: Number(draft.systolicBp),
        diastolic_bp: Number(draft.diastolicBp),
        resting_hr: draft.restingHr.trim() ? Number(draft.restingHr) : null,
        city: draft.city || null,
        pincode: draft.pincode || null,
        smoker: draft.smoker,
        alcohol_drinks_per_week: Number(draft.alcoholDrinksPerWeek),
        physical_activity: draft.physicalActivity,
        sitting_hours: draft.sittingHours.trim() ? Number(draft.sittingHours) : null,
        sleep_hours: draft.sleepHours.trim() ? Number(draft.sleepHours) : null,
        family_diabetes: draft.familyDiabetes,
        family_heart_disease: draft.familyHeartDisease,
        region: "IN",
        fpg: !skipLabs && draft.fpg.trim() ? Number(draft.fpg) : null,
        hba1c: !skipLabs && draft.hba1c.trim() ? Number(draft.hba1c) : null,
        ogtt_2h: !skipLabs && draft.ogtt2h.trim() ? Number(draft.ogtt2h) : null,
        total_cholesterol: !skipLabs && draft.totalChol.trim() ? Number(draft.totalChol) : null,
        ldl: !skipLabs && draft.ldl.trim() ? Number(draft.ldl) : null,
        hdl: !skipLabs && draft.hdl.trim() ? Number(draft.hdl) : null,
        triglycerides: !skipLabs && draft.triglycerides.trim() ? Number(draft.triglycerides) : null,
        serum_creatinine: !skipLabs && draft.creatinine.trim() ? Number(draft.creatinine) : null,
        urine_acr: !skipLabs && draft.urineAcr.trim() ? Number(draft.urineAcr) : null,
        red_flags: draft.redFlags,
        consent_data_storage: draft.consentStorage,
      };
      const res = await apiFetch<any>("/api/v1/assess", {
        method: "POST",
        body: JSON.stringify(payload),
      }, token);
      onComplete(res);
    } catch (e: any) {
      setErrorMsg(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {errorMsg && (
        <div role="alert" className="p-4 rounded-2xl bg-[#FEE2E2] border border-[#FECACA] text-[#7F1D1D] text-xs font-bold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 3-Step Progress Bar */}
      <div className="grid grid-cols-3 gap-2.5 text-xs font-bold">
        {[
          [1, t.step_safety || "1. Basics and Safety"],
          [2, t.step_biomarkers || "2. Lifestyle"],
          [3, t.step_results || "3. Optional Labs"],
        ].map(([n, label]) => (
          <button
            key={n}
            type="button"
            onClick={() => {
              setErrorMsg(null);
              setStep(n as 1 | 2 | 3);
            }}
            className={`min-h-[44px] flex items-center justify-center p-3 rounded-2xl border text-center focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
              step === n
                ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D] shadow-warm"
                : step > (n as number)
                ? "bg-[#DCFCE7] text-[#14532D] border-[#BBF7D0]"
                : "bg-white text-[#6B5B2E] border-[#EFE4BE]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* STEP 1: BASICS AND SAFETY (Red-flag checklist FIRST) */}
      {step === 1 && (
        <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-6">
          {/* Red Flags First */}
          <div className="space-y-2.5">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#B91C1C]">
              Emergency Red-Flag Check (Answer First)
            </div>
            <p className="text-xs text-[#6B5B2E]">
              If any of these apply right now, do not wait for scores. Check the box and submit to see emergency guidance.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              {(
                [
                  ["chest_pain_or_pressure", "Chest pain or pressure"],
                  ["pain_spreading_arm_or_jaw", "Pain spreading to arm or jaw"],
                  ["severe_breathlessness_at_rest", "Severe breathlessness at rest"],
                  ["fainting", "Fainting / sudden loss of consciousness"],
                  ["face_drooping", "Face drooping (stroke sign)"],
                  ["arm_weakness", "Arm weakness (stroke sign)"],
                  ["speech_difficulty", "Speech trouble (stroke sign)"],
                  ["sudden_confusion", "Sudden confusion"],
                  ["vomiting_blood", "Severe bleeding / vomiting blood"],
                  ["black_stools", "Black tarry stools"],
                  ["persistent_vomiting", "Very high sugar with persistent vomiting"],
                  ["fruity_breath", "Very high sugar with fruity breath"],
                ] as [keyof WizardDraft["redFlags"], string][]
              ).map(([k, lbl]) => (
                <label
                  key={k}
                  className="min-h-[44px] flex items-center gap-2.5 p-3 rounded-xl bg-[#FFF9E3]/50 border border-[#EFE4BE] cursor-pointer hover:bg-[#FFF9E3]"
                >
                  <input
                    type="checkbox"
                    checked={draft.redFlags[k]}
                    onChange={(e) =>
                      update({ redFlags: { ...draft.redFlags, [k]: e.target.checked } })
                    }
                    className="w-4 h-4 accent-[#B91C1C]"
                  />
                  <span className="font-medium text-[#2B2208]">{lbl}</span>
                </label>
              ))}
            </div>
            {Object.values(draft.redFlags).some(Boolean) && (
              <button
                type="button"
                onClick={() => submitAssessment(true)}
                disabled={loading}
                className="min-h-[44px] px-5 py-2.5 rounded-xl bg-[#B91C1C] text-white text-xs font-extrabold"
              >
                {loading ? "Checking..." : "Get Immediate Emergency Guidance ->"}
              </button>
            )}
          </div>

          <hr className="border-[#EFE4BE]" />

          {/* Basics */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className={LABEL_CLS}>Age (years, 1-120)</label>
              <input type="number" inputMode="numeric" min={1} max={120} value={draft.age} onChange={(e) => update({ age: Number(e.target.value) })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Sex</label>
              <div className="grid grid-cols-2 gap-2">
                {(["male", "female"] as const).map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => update({ sex: opt })}
                    className={`min-h-[44px] rounded-xl text-xs font-bold capitalize border focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                      draft.sex === opt
                        ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D]"
                        : "bg-[#FFF9E3]/60 text-[#6B5B2E] border-[#EFE4BE]"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className={LABEL_CLS}>Height (cm, 50-250)</label>
              <input type="number" inputMode="decimal" min={50} max={250} value={draft.heightCm} onChange={(e) => update({ heightCm: Number(e.target.value) })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Weight (kg, 15-300)</label>
              <input type="number" inputMode="decimal" min={15} max={300} value={draft.weightKg} onChange={(e) => update({ weightKg: Number(e.target.value) })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Waist (cm, 30-220)</label>
              <input type="number" inputMode="decimal" min={30} max={220} value={draft.waistCm} onChange={(e) => update({ waistCm: Number(e.target.value) })} className={INPUT_CLS} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={LABEL_CLS}>SBP (mmHg, 60-260)</label>
                <input type="number" inputMode="numeric" min={60} max={260} value={draft.systolicBp} onChange={(e) => update({ systolicBp: Number(e.target.value) })} className={INPUT_CLS} />
              </div>
              <div>
                <label className={LABEL_CLS}>DBP (mmHg, 30-180)</label>
                <input type="number" inputMode="numeric" min={30} max={180} value={draft.diastolicBp} onChange={(e) => update({ diastolicBp: Number(e.target.value) })} className={INPUT_CLS} />
              </div>
            </div>
            <div>
              <label className={LABEL_CLS}>Resting Heart Rate (bpm, optional)</label>
              <input type="number" inputMode="numeric" min={30} max={220} placeholder="e.g. 72" value={draft.restingHr} onChange={(e) => update({ restingHr: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>City (optional, for hospitals)</label>
              <input type="text" placeholder="e.g. New Delhi" value={draft.city} onChange={(e) => update({ city: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Pin code (optional)</label>
              <input type="text" inputMode="numeric" placeholder="e.g. 110029" value={draft.pincode} onChange={(e) => update({ pincode: e.target.value })} className={INPUT_CLS} />
            </div>
          </div>

          {autoBmi && (
            <div className="p-3.5 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs font-semibold text-[#2B2208] tabular-nums">
              Auto-Calculated BMI: <strong>{autoBmi.value} kg/m2</strong> — {autoBmi.cat}
            </div>
          )}

          <button
            type="button"
            onClick={() => {
              const err = validateStep1();
              if (err) {
                setErrorMsg(err);
                return;
              }
              setErrorMsg(null);
              setStep(2);
            }}
            className="min-h-[44px] px-6 py-2.5 rounded-xl bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] font-extrabold text-sm shadow-warm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            Continue to Lifestyle -&gt;
          </button>
        </div>
      )}

      {/* STEP 2: LIFESTYLE */}
      {step === 2 && (
        <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-5">
          <h3 className="text-lg font-extrabold text-[#2B2208]">Step 2: Lifestyle &amp; Family History</h3>

          <div className="space-y-2">
            <label className={LABEL_CLS}>Physical Activity</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {(["vigorous", "moderate", "mild", "sedentary"] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => update({ physicalActivity: val })}
                  className={`min-h-[44px] px-3 py-2 rounded-xl text-xs font-bold capitalize border focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                    draft.physicalActivity === val
                      ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D]"
                      : "bg-[#FFF9E3]/60 text-[#6B5B2E] border-[#EFE4BE]"
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className={LABEL_CLS}>Family History of Diabetes</label>
            <div className="grid grid-cols-3 gap-2.5">
              {(
                [
                  ["none", "None"],
                  ["one_parent", "One parent"],
                  ["both", "Both parents"],
                ] as const
              ).map(([val, lbl]) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => update({ familyDiabetes: val })}
                  className={`min-h-[44px] px-3 py-2 rounded-xl text-xs font-bold border focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                    draft.familyDiabetes === val
                      ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D]"
                      : "bg-[#FFF9E3]/60 text-[#6B5B2E] border-[#EFE4BE]"
                  }`}
                >
                  {lbl}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className={LABEL_CLS}>Alcohol (drinks/week, 0-100)</label>
              <input type="number" inputMode="decimal" min={0} max={100} value={draft.alcoholDrinksPerWeek} onChange={(e) => update({ alcoholDrinksPerWeek: Number(e.target.value) })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Sitting hours / day (0-24)</label>
              <input type="number" inputMode="decimal" min={0} max={24} placeholder="e.g. 6" value={draft.sittingHours} onChange={(e) => update({ sittingHours: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Sleep hours / night (0-24)</label>
              <input type="number" inputMode="decimal" min={0} max={24} placeholder="e.g. 7" value={draft.sleepHours} onChange={(e) => update({ sleepHours: e.target.value })} className={INPUT_CLS} />
            </div>
          </div>

          <div className="flex flex-wrap gap-6">
            <label className="min-h-[44px] inline-flex items-center gap-2.5 text-sm font-medium text-[#2B2208] cursor-pointer">
              <input type="checkbox" checked={draft.smoker} onChange={(e) => update({ smoker: e.target.checked })} className="w-4 h-4 accent-[#2B2208]" />
              <span>Current tobacco smoker</span>
            </label>
            <label className="min-h-[44px] inline-flex items-center gap-2.5 text-sm font-medium text-[#2B2208] cursor-pointer">
              <input type="checkbox" checked={draft.familyHeartDisease} onChange={(e) => update({ familyHeartDisease: e.target.checked })} className="w-4 h-4 accent-[#2B2208]" />
              <span>Family history of heart disease</span>
            </label>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setErrorMsg(null);
                setStep(1);
              }}
              className="min-h-[44px] px-5 py-2.5 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-sm font-bold focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              &lt;- Back
            </button>
            <button
              type="button"
              onClick={() => {
                const err = validateStep2();
                if (err) {
                  setErrorMsg(err);
                  return;
                }
                setErrorMsg(null);
                setStep(3);
              }}
              className="min-h-[44px] px-6 py-2.5 rounded-xl bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] font-extrabold text-sm shadow-warm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              Continue to Optional Labs -&gt;
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: OPTIONAL LABS */}
      {step === 3 && (
        <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-extrabold text-[#2B2208]">Step 3: Optional Lab Values</h3>
              <p className="text-xs text-[#6B5B2E] mt-0.5">
                Every lab field is optional. Missing labs are safely marked as skipped.
              </p>
            </div>
            <button
              type="button"
              onClick={() => submitAssessment(true)}
              disabled={loading}
              className="min-h-[44px] px-4 py-2 rounded-xl bg-[#FFF9E3] hover:bg-[#FFC83D]/40 border border-[#EFE4BE] text-[#2B2208] text-xs font-extrabold inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              <SkipForward className="w-4 h-4" />
              <span>Skip, I don&apos;t have lab reports</span>
            </button>
          </div>

          {/* 5 Quick Test Lab Report Inputs */}
          <div className="rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] p-3.5 space-y-2">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#6B5B2E]">
              Quick Test Lab Report Inputs (5 Sample Profiles)
            </div>
            <div className="flex flex-wrap gap-1.5">
              {LAB_TEST_PRESETS.map((preset) => (
                <button
                  key={preset.id}
                  type="button"
                  onClick={() => {
                    setErrorMsg(null);
                    onDraftChange({ ...draft, ...preset.patch });
                  }}
                  className="min-h-[36px] px-3 py-1.5 rounded-full bg-white hover:bg-[#FFC83D]/30 border border-[#EFE4BE] text-xs font-bold text-[#2B2208] inline-flex items-center gap-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <span>{preset.label}</span>
                  <span className="px-1.5 py-0.5 rounded-full bg-[#FFF3C4] text-[10px] font-extrabold text-[#78350F]">
                    {preset.badge}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className={LABEL_CLS}>Fasting Glucose (mg/dL, 20-1000)</label>
              <input type="number" inputMode="decimal" min={20} max={1000} placeholder="e.g. 105" value={draft.fpg} onChange={(e) => update({ fpg: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>HbA1c (% or mmol/mol, 2-200)</label>
              <input type="number" inputMode="decimal" step="0.1" min={2} max={200} placeholder="e.g. 5.8" value={draft.hba1c} onChange={(e) => update({ hba1c: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>2-hour Glucose (mg/dL, 20-1000)</label>
              <input type="number" inputMode="decimal" min={20} max={1000} placeholder="e.g. 145" value={draft.ogtt2h} onChange={(e) => update({ ogtt2h: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Total Cholesterol (mg/dL, 50-800)</label>
              <input type="number" inputMode="decimal" min={50} max={800} placeholder="e.g. 210" value={draft.totalChol} onChange={(e) => update({ totalChol: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>LDL Cholesterol (mg/dL, 10-500)</label>
              <input type="number" inputMode="decimal" min={10} max={500} placeholder="e.g. 130" value={draft.ldl} onChange={(e) => update({ ldl: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>HDL Cholesterol (mg/dL, 10-150)</label>
              <input type="number" inputMode="decimal" min={10} max={150} placeholder="e.g. 42" value={draft.hdl} onChange={(e) => update({ hdl: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Triglycerides (mg/dL, 20-2000)</label>
              <input type="number" inputMode="decimal" min={20} max={2000} placeholder="e.g. 160" value={draft.triglycerides} onChange={(e) => update({ triglycerides: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Serum Creatinine (mg/dL, 0.1-20)</label>
              <input type="number" inputMode="decimal" step="0.01" min={0.1} max={20} placeholder="e.g. 0.9" value={draft.creatinine} onChange={(e) => update({ creatinine: e.target.value })} className={INPUT_CLS} />
            </div>
            <div>
              <label className={LABEL_CLS}>Urine ACR (mg/g, 0-5000)</label>
              <input type="number" inputMode="decimal" min={0} max={5000} placeholder="e.g. 20" value={draft.urineAcr} onChange={(e) => update({ urineAcr: e.target.value })} className={INPUT_CLS} />
            </div>
          </div>

          {autoEgfr && (
            <div className="p-3.5 rounded-xl bg-[#DCFCE7] border border-[#BBF7D0] text-xs font-semibold text-[#14532D] tabular-nums flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Auto-Calculated CKD-EPI 2021 eGFR: <strong>{autoEgfr} mL/min/1.73m2</strong></span>
            </div>
          )}

          <label className="min-h-[44px] inline-flex items-center gap-2.5 text-xs font-semibold text-[#2B2208] cursor-pointer">
            <input
              type="checkbox"
              checked={draft.consentStorage}
              onChange={(e) => update({ consentStorage: e.target.checked })}
              className="w-4 h-4 accent-[#2B2208]"
            />
            <span>Save my results to History</span>
          </label>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => {
                setErrorMsg(null);
                setStep(2);
              }}
              className="min-h-[44px] px-5 py-2.5 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-sm font-bold focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              &lt;- Back
            </button>
            <button
              type="button"
              onClick={() => submitAssessment(false)}
              disabled={loading}
              className="min-h-[44px] flex-1 py-2.5 rounded-xl bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] font-extrabold text-sm shadow-warm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              {loading ? "Running Assessment..." : "Run Health Risk Assessment ->"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
