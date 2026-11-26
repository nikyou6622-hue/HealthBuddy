import plansEn from "@/data/plans.en.json";
import plansHi from "@/data/plans.hi.json";

export interface LocalizedPlan {
  condition: string;
  title: string;
  tier: string;
  source: string;
  reviewer: string;
  version: string;
  doctor_tests: string[];
  eat_more: string[];
  avoid: string[];
  exercise_target: string;
  exercise: string[];
  followup_months: number;
  is_pending_review: boolean;
}

const FALLBACK_PLAN: LocalizedPlan = {
  condition: "general",
  title: "Talk to your doctor",
  tier: "moderate",
  source: "General Clinical Guidance",
  reviewer: "pending",
  version: "1.0.0",
  doctor_tests: ["Talk to your doctor for a personalized evaluation."],
  eat_more: ["Balanced home-cooked meals with vegetables and whole grains."],
  avoid: ["Ultra-processed snacks, excess salt, and sugary drinks."],
  exercise_target: "Consult a physician before starting a new exercise routine.",
  exercise: ["Gentle walking if comfortable, pending doctor review."],
  followup_months: 6,
  is_pending_review: true,
};

export function getLocalizedPlan(
  locale: "en" | "hi",
  condition: string,
  tier: string
): LocalizedPlan | null {
  const dict: any = locale === "hi" ? plansHi : plansEn;
  const condBlock = dict[condition];
  const normTier = tier === "low" || tier === "moderate" || tier === "high" ? tier : "moderate";

  if (!condBlock || !condBlock[normTier]) {
    return FALLBACK_PLAN;
  }

  const reviewer = condBlock.reviewer || "pending";
  const isPending = reviewer.toLowerCase() === "pending";
  if (isPending && process.env.NEXT_PUBLIC_ENV === "production") {
    return null;
  }

  const tData = condBlock[normTier];
  return {
    condition,
    title: condBlock.title,
    tier: normTier,
    source: condBlock.source,
    reviewer,
    version: condBlock.version,
    doctor_tests: tData.doctor_tests || [],
    eat_more: tData.eat_more || [],
    avoid: tData.avoid || [],
    exercise_target: tData.exercise_target || "",
    exercise: tData.exercise || [],
    followup_months: tData.followup_months || 6,
    is_pending_review: isPending,
  };
}

