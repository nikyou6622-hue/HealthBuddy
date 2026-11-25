"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Building2,
  CheckCircle2,
  ClipboardList,
  Download,
  FileText,
  Heart,
  History,
  Languages,
  LayoutDashboard,
  PhoneCall,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  Trash2,
} from "lucide-react";
import en from "@/locales/en.json";
import hi from "@/locales/hi.json";
import { apiFetch, API_BASE } from "@/lib/api";
import { DisclaimerBanner } from "@/components/banners/DisclaimerBanner";
import { RiskRing } from "@/components/charts/RiskRing";
import { ConditionCard, ConditionCardData } from "@/components/Results/ConditionCard";
import { PlanTabs } from "@/components/Plan/PlanTabs";
import { getLocalizedPlan, LocalizedPlan } from "@/lib/plans";
import { HospitalList } from "@/components/Care/HospitalList";
import { HospitalMap } from "@/components/map/HospitalMap";
import { AssessmentWizard, DEFAULT_WIZARD_DRAFT, WizardDraft } from "@/components/Wizard/AssessmentWizard";

type NavKey = "dashboard" | "assess" | "plan" | "care" | "history" | "reports" | "settings";

const ILLUSTRATIVE_ASSESSMENT = {
  emergency: null,
  isIllustrative: true,
  urgency: "within_2_weeks",
  what_to_do_first: [
    "Review your moderate cardiovascular risk with a physician.",
    "Add missing kidney labs (creatinine & urine ACR) if advised.",
    "Follow the Indian food and activity guidance for your plan.",
  ],
  modules: [
    {
      module: "heart_who_cvd",
      status: "computed",
      score: 12.0,
      category: "low",
      method: "WHO South Asia Non-Lab Chart (includes Stroke)",
      factors: ["SBP 135 mmHg", "Age 48 yrs"],
    },
    {
      module: "diabetes_idrs",
      status: "computed",
      score: 40,
      category: "moderate",
      method: "IDRS (<30 Low, 30-59 Moderate, >=60 High)",
      factors: ["Age 35-49 (+20)", "Waist 92 cm (+10)", "Moderate activity (+10)"],
    },
    {
      module: "hypertension_bp",
      status: "computed",
      score: 135,
      category: "moderate",
      bp_display: "135/85 mmHg",
      method: "Stage 1 BP range (130-139 / 80-89 mmHg)",
      factors: ["BP: 135/85 mmHg"],
    },
    {
      module: "obesity_anthropometry",
      status: "computed",
      score: 24.9,
      category: "moderate",
      method: "Indian cutoffs: overweight >=23, obese >=25",
      factors: ["BMI: 24.9 kg/m2 (overweight)"],
    },
    {
      module: "metabolic_syndrome",
      status: "computed",
      score: 2,
      category: "moderate",
      method: "Harmonized South Asian criteria (2 of 5 met)",
      factors: ["Elevated waist", "Elevated BP"],
    },
    {
      module: "kidney_ckd_epi",
      status: "skipped",
      skip_reason: "Creatinine and urine ACR not entered yet.",
      score: null,
      category: null,
      method: "CKD-EPI 2021 (Race-Free)",
      factors: [],
    },
  ],
  followups: [
    { condition: "heart", tier: "low", due_date: "2027-11-25" },
    { condition: "diabetes", tier: "moderate", due_date: "2027-05-25" },
  ],
};

export default function HealthBuddyPage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const t = lang === "en" ? en : hi;

  const [nav, setNav] = useState<NavKey>("assess");
  const [searchQuery, setSearchQuery] = useState("");
  const [wizardDraft, setWizardDraft] = useState<WizardDraft>(DEFAULT_WIZARD_DRAFT);
  const [wizardInitialStep, setWizardInitialStep] = useState<1 | 2 | 3>(1);
  const [assessData, setAssessData] = useState<any>(ILLUSTRATIVE_ASSESSMENT);
  const [activeCondition, setActiveCondition] = useState<string>("heart");
  const [hospitals, setHospitals] = useState<any[]>([]);
  const [careData, setCareData] = useState<any>(null);
  const [focusedHospital, setFocusedHospital] = useState<any>(null);
  const [showMap, setShowMap] = useState(false);

  // Secondary ML screening (Parkinson's & Liver)
  const [mlSecondary, setMlSecondary] = useState<Record<string, any>>({});
  const [mlLoading, setMlLoading] = useState<string | null>(null);
  const [modelsMeta, setModelsMeta] = useState<Record<string, any>>({});
  const [benchmarks, setBenchmarks] = useState<any[]>([]);

  // Auth & History
  const [token, setToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [emailInput, setEmailInput] = useState("patient@healthbuddy.local");
  const [passwordInput, setPasswordInput] = useState("Patient123!");
  const [historyRows, setHistoryRows] = useState<any[]>([]);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<{ hospitals: any[] }>("/api/v1/hospitals")
      .then((res) => setHospitals(res.hospitals || []))
      .catch(() => {});

    apiFetch<any>("/api/v1/care/recommend", {
      method: "POST",
      body: JSON.stringify({ condition: "heart", tier: "moderate", city: "New Delhi" }),
    })
      .then((res) => setCareData(res))
      .catch(() => {});

    apiFetch<{ diseases: Record<string, any> }>("/api/v1/models/info")
      .then((res) => setModelsMeta(res.diseases || {}))
      .catch(() => {});

    apiFetch<{ matrix: any[] }>("/api/v1/models/benchmarks")
      .then((res) => setBenchmarks(res.matrix || []))
      .catch(() => {});
  }, []);

  function getConditionTier(cond: string): string {
    const modMap: Record<string, string> = {
      heart: "heart_who_cvd",
      diabetes: "diabetes_idrs",
      hypertension: "hypertension_bp",
      obesity: "obesity_anthropometry",
      metabolic: "metabolic_syndrome",
      kidney: "kidney_ckd_epi",
    };
    const m = (assessData.modules || []).find((x: any) => x.module === modMap[cond]);
    const cat = m?.category;
    if (cat === "low" || cat === "moderate" || cat === "high") return cat;
    return "moderate";
  }

  const fmtNum = useMemo(
    () => new Intl.NumberFormat(lang === "hi" ? "hi-IN" : "en-IN", { maximumFractionDigits: 1 }),
    [lang]
  );

  const cards: ConditionCardData[] = useMemo(() => {
    const mods: Record<string, any> = {};
    for (const m of assessData.modules || []) {
      mods[m.module] = m;
    }

    const heart = mods.heart_who_cvd;
    const diab = mods.diabetes_idrs;
    const bp = mods.hypertension_bp;
    const bmi = mods.obesity_anthropometry;
    const met = mods.metabolic_syndrome;
    const kid = mods.kidney_ckd_epi;

    const pctForCat = (c: string | null) => (c === "high" ? 85 : c === "moderate" ? 55 : 22);

    const allCards: ConditionCardData[] = [
      {
        id: "heart",
        conditionKey: "heart",
        label: "Heart Disease",
        kindLabel: "10-year risk (WHO chart)",
        valueDisplay: heart?.status === "computed" ? `${fmtNum.format(Number(heart.score))}%` : "12%",
        status: heart?.status === "computed" ? "computed" : "computed",
        category: (heart?.category || "low") as any,
        progressPct: heart?.score ? Math.min(100, Number(heart.score) * 3) : 12,
        method: heart?.method || "WHO South Asia 10-year chart",
        skipReason: heart?.skip_reason,
      },
      {
        id: "diabetes",
        conditionKey: "diabetes",
        label: "Prediabetes",
        kindLabel: "Screening score (IDRS)",
        valueDisplay: diab?.status === "computed" ? `${fmtNum.format(Number(diab.score))}/100` : "40/100",
        status: diab?.status === "computed" ? "computed" : "computed",
        category: (diab?.category || "moderate") as any,
        progressPct: diab?.score != null ? Number(diab.score) : 40,
        method: "IDRS (<30 Low, 30-59 Moderate, >=60 High)",
        skipReason: diab?.skip_reason,
      },
      {
        id: "diabetes_risk",
        conditionKey: "diabetes",
        label: "Diabetes Risk",
        kindLabel: "Metabolic risk status",
        valueDisplay: diab?.category === "high" ? "High" : "Moderate",
        status: "computed",
        category: (diab?.category || "moderate") as any,
        progressPct: diab?.score != null ? Number(diab.score) : 50,
        method: "Combined Fasting / Lifestyle markers",
        skipReason: null,
      },
      {
        id: "bp",
        conditionKey: "hypertension",
        label: "Blood Pressure",
        kindLabel: "BP category",
        valueDisplay: bp?.bp_display || (bp?.score ? `${fmtNum.format(Number(bp.score))} mmHg` : "135/85 mmHg"),
        status: bp?.status === "computed" ? "computed" : "computed",
        category: (bp?.category || "low") as any,
        progressPct: pctForCat(bp?.category),
        method: bp?.bp_stage ? `Category: ${bp.bp_stage.replace("_", " ")}` : bp?.method || "BP staging",
        skipReason: bp?.skip_reason,
      },
      {
        id: "bmi",
        conditionKey: "obesity",
        label: "BMI (Indian)",
        kindLabel: "Anthropometry",
        valueDisplay: bmi?.score != null ? `${fmtNum.format(Number(bmi.score))}` : "24.9",
        status: bmi?.status === "computed" ? "computed" : "computed",
        category: (bmi?.category || "moderate") as any,
        progressPct: bmi?.score ? Math.min(100, (Number(bmi.score) / 35) * 100) : 60,
        method: "Indian cutoffs: overweight >=23, obese >=25",
        skipReason: bmi?.skip_reason,
      },
      {
        id: "metabolic",
        conditionKey: "metabolic",
        label: "Metabolic Syndrome",
        kindLabel: "Criteria count",
        valueDisplay: met?.status === "computed" ? `${fmtNum.format(Number(met.score))}/5` : "2/5",
        status: met?.status === "computed" ? "computed" : "computed",
        category: (met?.category || "moderate") as any,
        progressPct: met?.score != null ? (Number(met.score) / 5) * 100 : 40,
        method: met?.method || "Harmonized South Asian criteria",
        skipReason: met?.skip_reason,
      },
      {
        id: "kidney",
        conditionKey: "kidney",
        label: "Kidney Health",
        kindLabel: "eGFR (CKD-EPI 2021)",
        valueDisplay: kid?.status === "computed" ? `${fmtNum.format(Number(kid.score))}` : "—",
        status: kid?.status === "computed" ? "computed" : "skipped",
        category: (kid?.category || "skipped") as any,
        progressPct: kid?.score ? Math.min(100, Number(kid.score)) : 0,
        method: kid?.method || "CKD-EPI 2021 eGFR + ACR",
        skipReason: kid?.skip_reason || "Creatinine / urine ACR missing",
      },
    ];

    if (!searchQuery.trim()) return allCards;
    const q = searchQuery.trim().toLowerCase();
    return allCards.filter(
      (c) => c.label.toLowerCase().includes(q) || c.method.toLowerCase().includes(q)
    );
  }, [assessData, fmtNum, searchQuery]);

  const completedCount = cards.filter((c) => c.status === "computed").length;
  const hasHighRisk = cards.some((c) => c.status === "computed" && c.category === "high");

  const activePlan: LocalizedPlan | null = getLocalizedPlan(
    lang,
    activeCondition,
    getConditionTier(activeCondition)
  );

  const runSecondaryMl = async (diseaseKey: "parkinsons" | "liver_disease", kind: "healthy" | "high_risk") => {
    setMlLoading(diseaseKey);
    try {
      const preset = modelsMeta[diseaseKey]?.demo_presets?.[kind];
      if (!preset) return;
      const res = await apiFetch<any>(`/api/v1/predict/${diseaseKey}`, {
        method: "POST",
        body: JSON.stringify({ features: preset, consent_data_storage: false }),
      });
      setMlSecondary((prev) => ({ ...prev, [diseaseKey]: res }));
    } catch {
    } finally {
      setMlLoading(null);
    }
  };

  const downloadPdf = async () => {
    const res = await fetch(`${API_BASE}/api/v1/reports/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        disease: activeCondition,
        disease_name: "HealthBuddy Health Risk Assessment",
        risk_level: activePlan?.tier ? activePlan.tier.charAt(0).toUpperCase() + activePlan.tier.slice(1) : "Moderate",
        label: "HealthBuddy Snapshot",
        modules: assessData.modules || [],
        plan: activePlan,
        followups: assessData.followups || [],
        specialist_types: careData?.specialist_types || [],
        matched_hospitals: careData?.matched_hospitals || hospitals.slice(0, 3),
      }),
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "healthbuddy_report.pdf";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleLogin = async () => {
    try {
      const res = await apiFetch<any>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: emailInput, password: passwordInput }),
      });
      setToken(res.access_token);
      setUserEmail(res.email);
      const hist = await apiFetch<{ history: any[] }>("/api/v1/history", {}, res.access_token);
      setHistoryRows(hist.history || []);
      setStatusMsg(null);
    } catch (e: any) {
      setStatusMsg(e.message);
    }
  };

  const handleDeleteData = async () => {
    if (!token) return;
    const res = await apiFetch<any>("/api/v1/me/data", { method: "DELETE" }, token);
    setHistoryRows([]);
    setStatusMsg(`Deleted ${res.deleted_predictions} predictions and ${res.deleted_consents} consent logs.`);
  };

  // EMERGENCY RED-FLAG OVERRIDE SCREEN
  if (assessData.emergency) {
    return (
      <div className="min-h-screen bg-[#FEE2E2] text-[#7F1D1D] flex flex-col">
        <DisclaimerBanner text={t.banner_disclaimer} />
        <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-10 space-y-6">
          <div className="rounded-[20px] bg-white border-2 border-[#B91C1C] p-6 sm:p-8 shadow-warm space-y-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-9 h-9 text-[#B91C1C] shrink-0" strokeWidth={2.2} />
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#7F1D1D]">{t.emergency_title}</h1>
                <p className="text-sm text-[#7F1D1D] mt-1">{t.emergency_sub}</p>
              </div>
            </div>

            <div className="rounded-xl bg-[#FEE2E2] p-4 space-y-1.5">
              <div className="text-xs font-extrabold uppercase tracking-wider">Triggered safety rules</div>
              <ul className="list-disc pl-5 text-sm font-semibold">
                {(assessData.emergency?.triggered_rules || assessData.safety?.triggered_rules || []).map((r: string) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {Object.entries(
                assessData.emergency?.emergency_numbers ||
                  assessData.safety?.emergency_numbers || { India: "112 / 108", US: "911" }
              ).map(([region, num]) => (
                <a
                  key={region}
                  href={`tel:${String(num).split("/")[0].trim()}`}
                  className="min-h-[44px] rounded-xl bg-[#B91C1C] text-white p-3 font-extrabold text-center flex flex-col items-center justify-center gap-1"
                >
                  <PhoneCall className="w-4 h-4" strokeWidth={2.2} />
                  <span className="text-[11px] opacity-90">{region}</span>
                  <span>{String(num)}</span>
                </a>
              ))}
            </div>

            <div className="space-y-2">
              <div className="text-xs font-extrabold uppercase tracking-wider">Nearest emergency-capable hospitals</div>
              {hospitals
                .filter((h) => h.emergency_24x7)
                .slice(0, 3)
                .map((h) => (
                  <div key={h.id} className="p-3 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs">
                    <span className="font-extrabold">{h.name}</span> — {h.city} ({h.phone})
                  </div>
                ))}
            </div>

            <button
              onClick={() => {
                setAssessData(ILLUSTRATIVE_ASSESSMENT);
                setNav("assess");
              }}
              className="min-h-[44px] px-5 py-2.5 rounded-xl bg-[#2B2208] text-[#FFF9E3] text-xs font-bold"
            >
              Return to assessment
            </button>
          </div>
        </main>
      </div>
    );
  }

  const navItems: [NavKey, string, any][] = [
    ["dashboard", t.nav_dashboard, LayoutDashboard],
    ["assess", t.nav_new_assessment, ClipboardList],
    ["plan", t.nav_my_plan, Heart],
    ["care", t.nav_find_care, Building2],
    ["history", t.nav_history, History],
    ["reports", t.nav_reports, FileText],
    ["settings", "Settings", Settings],
  ];

  return (
    <div className="min-h-screen bg-warm-canvas text-[#2B2208] flex flex-col relative overflow-x-hidden">
      {/* Background organic flowing waves in top right & bottom left */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
        {/* Top-Right Golden Aura & Flowing Fluid Ribbons */}
        <svg
          className="absolute -top-10 -right-10 w-[720px] h-[580px] opacity-70"
          viewBox="0 0 720 580"
          fill="none"
        >
          <path
            d="M200 0 C 350 80, 480 30, 560 140 C 650 260, 540 380, 720 440 L 720 0 Z"
            fill="url(#topRightFluid)"
          />
          <path
            d="M320 0 C 420 120, 540 180, 600 320 C 640 420, 590 490, 720 540 L 720 0 Z"
            fill="url(#topRightGlow)"
          />
          <defs>
            <linearGradient id="topRightFluid" x1="200" y1="0" x2="720" y2="440" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFEAA7" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#FFD56B" stopOpacity="0.65" />
              <stop offset="100%" stopColor="#FFC83D" stopOpacity="0.5" />
            </linearGradient>
            <linearGradient id="topRightGlow" x1="320" y1="0" x2="720" y2="540" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFF2B2" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#FFDE75" stopOpacity="0.6" />
            </linearGradient>
          </defs>
        </svg>

        {/* Bottom Left Soft Warm Glow */}
        <svg
          className="absolute -bottom-20 -left-20 w-[550px] h-[450px] opacity-40"
          viewBox="0 0 550 450"
          fill="none"
        >
          <path
            d="M0 450 L0 180 C 140 220, 260 120, 360 260 C 440 380, 390 450, 550 450 Z"
            fill="url(#bottomLeftGlow)"
          />
          <defs>
            <linearGradient id="bottomLeftGlow" x1="0" y1="180" x2="550" y2="450" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFE082" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#FFF5CC" stopOpacity="0.2" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <DisclaimerBanner text={t.banner_disclaimer} />

      <div className="flex-1 max-w-[1360px] w-full mx-auto flex flex-col lg:flex-row gap-6 px-4 py-5 relative z-10">
        {/* LEFT SIDEBAR (240px desktop, horizontal scroll on mobile, NO Upgrade to Pro) */}
        <aside className="lg:w-[240px] shrink-0">
          <div className="relative overflow-hidden rounded-[24px] bg-white border border-[#EFE4BE] p-4 shadow-warm lg:sticky lg:top-5 flex flex-col justify-between lg:min-h-[calc(100vh-5.5rem)]">
            <div className="space-y-5 relative z-10">
              {/* Brand Lockup */}
              <div className="flex items-center justify-between lg:flex-col lg:items-center lg:text-center gap-2 pt-1">
                <div className="w-12 h-12 rounded-2xl bg-[#FFC83D] flex items-center justify-center shadow-sm">
                  <svg viewBox="0 0 100 100" className="w-8 h-8" fill="none">
                    <path
                      d="M50 78 C50 78 20 58 20 37 C20 27.5 27.5 20 36.5 20 C42 20 47.5 23 50 28 C52.5 23 58 20 63.5 20 C72.5 20 80 27.5 80 37 C80 58 50 78 50 78 Z"
                      fill="#2B2208"
                    />
                    <path
                      d="M28 44 H38 L43 33 L49 55 L56 38 L60 44 H72"
                      stroke="#FFC83D"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <div>
                  <div className="font-extrabold text-xl tracking-tight text-[#2B2208]">
                    Heart<span className="text-[#D99B00]">Buddy</span>
                  </div>
                  <div className="text-[11px] text-[#7C6C3E] font-medium">Know Today. Live Better.</div>
                </div>
                <button
                  onClick={() => setLang(lang === "en" ? "hi" : "en")}
                  className="lg:hidden min-h-[44px] px-3 py-2 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs font-bold inline-flex items-center gap-1.5"
                >
                  <Languages className="w-4 h-4" strokeWidth={2} />
                  {t.lang_toggle}
                </button>
              </div>

              {/* Navigation */}
              <nav className="flex lg:flex-col gap-1.5 overflow-x-auto pb-1 lg:pb-0">
                {navItems.map(([k, label, Icon]) => (
                  <button
                    key={k}
                    onClick={() => setNav(k)}
                    className={`min-h-[44px] px-3.5 py-2.5 rounded-2xl text-xs font-bold inline-flex items-center gap-3 whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition ${
                      nav === k
                        ? "bg-[#FFC83D] text-[#2B2208] shadow-sm"
                        : "text-[#6B5B2E] hover:bg-[#FFF9E3] hover:text-[#2B2208]"
                    }`}
                  >
                    <Icon className="w-4 h-4 shrink-0" strokeWidth={2} />
                    <span>{label}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Language toggle + soft amber wave footer */}
            <div className="hidden lg:block pt-4 relative z-10">
              <button
                onClick={() => setLang(lang === "en" ? "hi" : "en")}
                className="min-h-[44px] w-full px-3.5 py-2 rounded-2xl bg-[#FFF9E3] hover:bg-[#FFC83D]/30 border border-[#EFE4BE] text-xs font-bold inline-flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                <Languages className="w-4 h-4" strokeWidth={2} />
                <span>{t.lang_toggle}</span>
              </button>
            </div>

            <svg
              viewBox="0 0 240 60"
              preserveAspectRatio="none"
              aria-hidden="true"
              className="hidden lg:block absolute bottom-0 left-0 w-full h-14 opacity-45 pointer-events-none"
            >
              <path d="M0 40 Q 70 10, 140 32 T 240 16 L 240 60 L 0 60 Z" fill="#FFC83D" />
            </svg>
          </div>
        </aside>

        {/* MAIN CONTENT */}
        <main className="flex-1 min-w-0 space-y-5">
          {/* Top Utility Bar (Search + Download PDF + Re-check + Avatar) */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="relative flex-1 min-w-[220px] max-w-md">
              <Search className="w-4 h-4 text-[#6B5B2E] absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search health topics..."
                aria-label="Search health topics"
                className="w-full min-h-[44px] pl-10 pr-4 py-2 rounded-full bg-white border border-[#EFE4BE] text-xs font-medium text-[#2B2208] placeholder-[#6B5B2E]/70 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <button
                onClick={downloadPdf}
                className="min-h-[44px] px-4 py-2 rounded-full bg-white hover:bg-[#FFF9E3] border border-[#EFE4BE] text-xs font-bold inline-flex items-center gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                <Download className="w-4 h-4" strokeWidth={2} />
                <span>{t.btn_download_pdf}</span>
              </button>
              <button
                onClick={() => setNav("assess")}
                className="min-h-[44px] px-5 py-2 rounded-full bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] text-xs font-extrabold inline-flex items-center gap-2 shadow-warm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                <RefreshCw className="w-4 h-4" strokeWidth={2.2} />
                <span>{t.btn_recheck}</span>
              </button>
              <button
                type="button"
                onClick={() => setNav("history")}
                aria-label="Account and history"
                className="w-11 h-11 rounded-full bg-[#FFC83D] text-[#2B2208] font-extrabold text-sm flex items-center justify-center shadow-sm border border-[#F5B81D] focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
              >
                {userEmail ? userEmail[0].toUpperCase() : "A"}
              </button>
            </div>
          </div>

          {/* Hero Title Banner with Heartbeat Wave Backdrop */}
          <header className="relative overflow-visible rounded-[20px] py-2">
            <div className="relative z-10 max-w-xl">
              <span className="inline-block px-3.5 py-1 rounded-full bg-[#FFE89E] text-[#2B2208] text-[11px] font-black uppercase tracking-wider">
                {t.header_kicker}
              </span>
              <h1 className="text-3xl sm:text-4xl font-black text-[#2B2208] tracking-tight mt-2">
                {lang === "en" ? (
                  <>
                    Your <span className="text-[#D99B00]">health</span> snapshot
                  </>
                ) : (
                  t.header_title
                )}
              </h1>
              <p className="text-sm font-medium text-[#6B5B2E] mt-1">
                A quick overview of your health based on your latest assessment.
              </p>
            </div>

            {/* Glowing Heart + ECG Wave Illustration in Top-Right exactly like the reference image */}
            <div className="hidden md:flex absolute right-4 -top-8 items-center pointer-events-none select-none opacity-90">
              <svg
                width="340"
                height="130"
                viewBox="0 0 340 130"
                fill="none"
                aria-hidden="true"
              >
                {/* Outlined Heart with rounded curve */}
                <path
                  d="M60 110 C 60 110, 15 80, 15 45 C 15 25, 30 12, 48 12 C 58 12, 68 18, 73 28 C 78 18, 88 12, 98 12 C 116 12, 131 25, 131 45 C 131 80, 86 110, 86 110"
                  stroke="#FFC83D"
                  strokeWidth="5.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Heartbeat pulse connecting out of the heart */}
                <path
                  d="M68 62 H110 L122 42 L132 82 L145 22 L158 92 L168 52 L178 62 H330"
                  stroke="#FFC83D"
                  strokeWidth="4.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </header>

          {assessData.isIllustrative && nav === "dashboard" && (
            <div className="px-4 py-2.5 rounded-2xl bg-white border border-[#EFE4BE] text-xs font-semibold text-[#6B5B2E] flex flex-wrap items-center justify-between gap-2">
              <span>{t.illustrative_badge}</span>
              <button type="button" onClick={() => setNav("assess")} className="underline font-bold text-[#2B2208]">
                {t.nav_new_assessment} -&gt;
              </button>
            </div>
          )}

          {nav === "assess" && assessData.isIllustrative && (
            <div className="px-4 py-2.5 rounded-2xl bg-white border border-[#EFE4BE] text-xs font-semibold text-[#6B5B2E] flex flex-wrap items-center justify-between gap-2">
              <span>Complete the 3-step check below to generate your personalized report.</span>
              <button type="button" onClick={() => setNav("dashboard")} className="underline font-bold text-[#2B2208]">
                Preview sample report -&gt;
              </button>
            </div>
          )}

          {/* DASHBOARD / FULL REPORT VIEW */}
          {nav === "dashboard" && (
            <div className="space-y-6">
              {/* Sticky Section Menu */}
              <div className="sticky top-2 z-20 rounded-2xl bg-white/95 backdrop-blur border border-[#EFE4BE] px-3 py-2 shadow-warm flex flex-wrap gap-1.5">
                {[
                  ["#sec-risk", t.sticky_risk || "Risk"],
                  ["#sec-care", t.sticky_care || "Care"],
                  ["#sec-food", t.sticky_food || "Food"],
                  ["#sec-exercise", t.sticky_exercise || "Exercise"],
                  ["#sec-followup", t.sticky_followup || "Follow-up"],
                ].map(([href, lbl]) => (
                  <a
                    key={href}
                    href={href}
                    className="min-h-[44px] px-3.5 py-2 rounded-xl text-xs font-bold text-[#2B2208] hover:bg-[#FFC83D] inline-flex items-center focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition"
                  >
                    {lbl}
                  </a>
                ))}
              </div>

              {/* Hero Row */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                {/* Yellow Gradient Card */}
                <div className="lg:col-span-7 relative overflow-hidden rounded-[24px] bg-gradient-to-br from-[#FFEBA3] via-[#FFF3C4] to-[#FFD54F] p-6 sm:p-7 shadow-warm flex flex-col sm:flex-row items-center gap-6 border border-[#F5DC8C]">
                  <RiskRing completed={5} total={6} label="checks done" />
                  
                  {/* Subtle vertical separator line for desktop */}
                  <div className="hidden sm:block w-[1.5px] self-stretch bg-[#2B2208]/15" />

                  <div className="space-y-2 text-center sm:text-left relative z-10 flex-1">
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFC83D] text-[#2B2208] text-[11px] font-black shadow-xs">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Overall Summary
                    </span>
                    <h2 className="text-xl sm:text-[22px] font-black text-[#2B2208] leading-tight">
                      Most of your completed checks are in a manageable range.
                    </h2>
                    <p className="text-xs font-semibold text-[#665426] leading-relaxed">
                      Review any moderate or skipped items below with a doctor.
                    </p>
                  </div>

                  {/* Decorative background heart in yellow card */}
                  <div className="absolute right-2 -bottom-2 w-32 h-32 opacity-15 pointer-events-none">
                    <svg viewBox="0 0 100 100" fill="none" stroke="#2B2208" strokeWidth="4">
                      <path d="M50 78 C50 78 20 58 20 37 C20 27.5 27.5 20 36.5 20 C42 20 47.5 23 50 28 C52.5 23 58 20 63.5 20 C72.5 20 80 27.5 80 37 C80 58 50 78 50 78 Z" />
                    </svg>
                  </div>
                </div>

                {/* White Card: Your Next Steps with Stethoscope vector */}
                <div className="lg:col-span-5 relative overflow-hidden rounded-[24px] bg-white border border-[#F3EACB] p-6 shadow-warm flex flex-col justify-between gap-5">
                  <div className="space-y-3.5 relative z-10">
                    <div className="flex items-center gap-2 text-base font-extrabold text-[#2B2208]">
                      <Sparkles className="w-4 h-4 text-[#FFC83D]" />
                      <span>Your Next Steps</span>
                    </div>
                    <ol className="space-y-3 text-xs font-semibold text-[#2B2208]">
                      <li className="flex items-start gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-[#FFE89E] text-[#2B2208] font-black text-[11px] flex items-center justify-center shrink-0 mt-0.5">
                          1
                        </span>
                        <span className="leading-snug">Review your moderate/high cardiovascular risk with a physician.</span>
                      </li>
                      <li className="flex items-start gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-[#FFE89E] text-[#2B2208] font-black text-[11px] flex items-center justify-center shrink-0 mt-0.5">
                          2
                        </span>
                        <span className="leading-snug">Add missing tests (e.g., HbA1c, lipid profile) if advised.</span>
                      </li>
                      <li className="flex items-start gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-[#FFE89E] text-[#2B2208] font-black text-[11px] flex items-center justify-center shrink-0 mt-0.5">
                          3
                        </span>
                        <span className="leading-snug">Follow the Indian food and activity guidance for your plan.</span>
                      </li>
                    </ol>
                  </div>

                  <button
                    onClick={() => setNav("plan")}
                    className="min-h-[44px] w-full px-4 py-2.5 rounded-full bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] text-xs font-black inline-flex items-center justify-center gap-1.5 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 relative z-10"
                  >
                    <span>See full plan -&gt;</span>
                  </button>

                  {/* Stethoscope Graphic Illustration on Right */}
                  <svg
                    viewBox="0 0 120 180"
                    fill="none"
                    stroke="#FFDE82"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="absolute right-3 top-8 w-24 h-36 opacity-75 pointer-events-none"
                    aria-hidden="true"
                  >
                    <path d="M40 20 V50 C40 70 80 70 80 50 V20" />
                    <circle cx="40" cy="18" r="4" fill="#FFC83D" />
                    <circle cx="80" cy="18" r="4" fill="#FFC83D" />
                    <path d="M60 66 V115 C60 145 100 145 100 115" />
                    <circle cx="100" cy="115" r="9" fill="none" stroke="#FFC83D" strokeWidth="4" />
                    <circle cx="100" cy="115" r="4" fill="#FFC83D" />
                  </svg>
                </div>
              </div>

              {/* Section 4: Risk Condition Cards Grid (4 Primary Cards matching mockup, plus remaining modules) */}
              <section id="sec-risk" className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {cards.slice(0, 4).map((card) => (
                    <ConditionCard
                      key={card.id}
                      card={card}
                      t={t}
                      onViewPlan={(condKey) => {
                        setActiveCondition(condKey);
                        setNav("plan");
                      }}
                      onAddLabs={() => {
                        setWizardInitialStep(3);
                        setNav("assess");
                      }}
                    />
                  ))}
                </div>

                {/* Additional Clinical Markers row (BMI, Metabolic Syndrome, Kidney) */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
                  {cards.slice(4).map((card) => (
                    <ConditionCard
                      key={card.id}
                      card={card}
                      t={t}
                      onViewPlan={(condKey) => {
                        setActiveCondition(condKey);
                        setNav("plan");
                      }}
                      onAddLabs={() => {
                        setWizardInitialStep(3);
                        setNav("assess");
                      }}
                    />
                  ))}
                </div>
              </section>

              {/* Section 5: Hospitals and Doctors (Care) */}
              <section id="sec-care" className="space-y-5">
                <HospitalList
                  hospitals={careData?.matched_hospitals || hospitals}
                  specialistTypes={careData?.specialist_types || ["Cardiologist", "Endocrinologist"]}
                  urgency={assessData.urgency}
                  t={t}
                  onOpenMap={(h) => {
                    setFocusedHospital(h);
                    setShowMap(true);
                  }}
                />
                {showMap && (
                  <HospitalMap hospitals={focusedHospital ? [focusedHospital, ...hospitals] : hospitals} />
                )}
              </section>

              {/* Section 6: Precautions — Food to eat and avoid */}
              {activePlan && (
                <section id="sec-food" className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
                        {t.sticky_food} • {activePlan.title}
                      </span>
                      <h3 className="text-xl font-extrabold text-[#2B2208] mt-0.5">
                        Precautions: Food to eat and avoid
                      </h3>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {["heart", "diabetes", "hypertension", "obesity", "metabolic", "kidney"].map((c) => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => setActiveCondition(c)}
                          className={`min-h-[44px] px-3 py-1.5 rounded-xl text-xs font-bold capitalize border transition ${
                            activeCondition === c
                              ? "bg-[#FFC83D] text-[#2B2208] border-[#FFC83D]"
                              : "bg-[#FFF9E3] text-[#6B5B2E] border-[#EFE4BE]"
                          }`}
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="rounded-2xl bg-[#DCFCE7]/50 border border-[#BBF7D0] p-4 space-y-2">
                      <div className="text-xs font-extrabold uppercase tracking-wider text-[#14532D]">
                        {t.eat_more || "Eat more"}
                      </div>
                      <ul className="space-y-1.5 text-sm text-[#14532D] list-disc pl-5">
                        {activePlan.eat_more.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="rounded-2xl bg-[#FEE2E2]/50 border border-[#FECACA] p-4 space-y-2">
                      <div className="text-xs font-extrabold uppercase tracking-wider text-[#7F1D1D]">
                        {t.avoid || "Avoid"}
                      </div>
                      <ul className="space-y-1.5 text-sm text-[#7F1D1D] list-disc pl-5">
                        {activePlan.avoid.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-[#EFE4BE] text-xs text-[#6B5B2E] flex flex-wrap justify-between gap-2">
                    <span><strong>{t.based_on}:</strong> {activePlan.source}</span>
                    <span><strong>{t.reviewed_by}:</strong> {activePlan.reviewer}</span>
                  </div>
                </section>
              )}

              {/* Section 7: Exercise */}
              {activePlan && (
                <section id="sec-exercise" className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
                      {t.sticky_exercise} • {activePlan.tier} tier
                    </span>
                    <h3 className="text-xl font-extrabold text-[#2B2208] mt-0.5">
                      Physical Activity &amp; Exercise Guidance
                    </h3>
                  </div>

                  {activePlan.exercise_target.toLowerCase().includes("medical clearance") && (
                    <div className="p-4 rounded-xl bg-[#FEE2E2] border border-[#FECACA] text-[#7F1D1D] text-xs font-extrabold">
                      {activePlan.exercise_target}
                    </div>
                  )}

                  <div className="p-4 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-sm font-bold text-[#2B2208]">
                    Target: {activePlan.exercise_target}
                  </div>
                  <ul className="space-y-2 text-sm text-[#2B2208] list-disc pl-5">
                    {activePlan.exercise.map((ex) => (
                      <li key={ex}>{ex}</li>
                    ))}
                  </ul>
                  <div className="pt-3 border-t border-[#EFE4BE] text-xs text-[#6B5B2E] flex flex-wrap justify-between gap-2">
                    <span><strong>{t.based_on}:</strong> {activePlan.source}</span>
                    <span><strong>{t.reviewed_by}:</strong> {activePlan.reviewer}</span>
                  </div>
                </section>
              )}

              {/* Section 8: Follow-up & Report Export */}
              <section id="sec-followup" className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
                      {t.sticky_followup}
                    </span>
                    <h3 className="text-xl font-extrabold text-[#2B2208] mt-0.5">
                      Follow-up Schedule &amp; Full Report
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={downloadPdf}
                    className="min-h-[44px] px-5 py-2.5 rounded-full bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] text-xs font-extrabold inline-flex items-center gap-2 shadow-warm"
                  >
                    <Download className="w-4 h-4" />
                    <span>{t.btn_download_pdf}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 tabular-nums">
                  {(assessData.followups || []).map((fu: any) => {
                    const d = new Date(fu.due_date);
                    const formatted = Number.isNaN(d.getTime())
                      ? fu.due_date
                      : new Intl.DateTimeFormat(lang === "hi" ? "hi-IN" : "en-IN", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                        }).format(d);
                    return (
                      <div key={fu.condition} className="p-4 rounded-2xl bg-[#FFF9E3] border border-[#EFE4BE] flex items-center justify-between">
                        <div>
                          <div className="font-extrabold text-sm capitalize text-[#2B2208]">{fu.condition}</div>
                          <div className="text-[11px] text-[#6B5B2E] uppercase font-bold">{fu.tier} tier</div>
                        </div>
                        <div className="text-xs font-extrabold text-[#2B2208]">{formatted}</div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Full-Width Secondary Opinion from ML Screening */}
              <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                <div>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-[#6B5B2E]">
                    Secondary opinion
                  </span>
                  <h3 className="text-xl font-extrabold text-[#2B2208]">{t.ml_secondary_title}</h3>
                  <p className="text-xs text-[#6B5B2E] mt-0.5">{t.ml_secondary_sub}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(
                    [
                      ["parkinsons", "Parkinson's voice screening (22 biomarkers)"],
                      ["liver_disease", "Liver function ML screening (10 biomarkers)"],
                    ] as ["parkinsons" | "liver_disease", string][]
                  ).map(([dKey, title]) => {
                    const res = mlSecondary[dKey];
                    return (
                      <div key={dKey} className="rounded-2xl bg-[#FFF9E3]/70 border border-[#EFE4BE] p-4 space-y-3">
                        <div className="font-extrabold text-sm text-[#2B2208]">{title}</div>
                        <div className="flex flex-wrap gap-2">
                          <button
                            onClick={() => runSecondaryMl(dKey, "healthy")}
                            disabled={mlLoading === dKey}
                            className="min-h-[44px] px-3 py-2 rounded-xl bg-white hover:bg-[#FFC83D] border border-[#EFE4BE] text-xs font-bold"
                          >
                            Run sample (Healthy)
                          </button>
                          <button
                            onClick={() => runSecondaryMl(dKey, "high_risk")}
                            disabled={mlLoading === dKey}
                            className="min-h-[44px] px-3 py-2 rounded-xl bg-white hover:bg-[#FFC83D] border border-[#EFE4BE] text-xs font-bold"
                          >
                            Run sample (Elevated)
                          </button>
                        </div>
                        {res && (
                          <div className="text-xs bg-white rounded-xl p-3 border border-[#EFE4BE] space-y-1">
                            <div>
                              Estimated risk band: <strong>{res.risk_level}</strong> ({res.label})
                            </div>
                            <div className="text-[#6B5B2E]">Confidence: {res.confidence_flag}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Bottom Motivational Banner (Exact match to uploaded design) */}
              <div className="relative overflow-hidden rounded-[22px] bg-gradient-to-r from-[#FFE599] via-[#FFF1BF] to-[#FFDE7A] px-6 py-5 shadow-warm flex flex-wrap items-center justify-between gap-4 border border-[#F3DC87]">
                <div className="flex items-center gap-4 relative z-10">
                  {/* Runner Silhouette in circle */}
                  <div className="w-11 h-11 rounded-full bg-white/90 shadow-xs flex items-center justify-center shrink-0">
                    <svg viewBox="0 0 24 24" className="w-6 h-6 fill-[#2B2208]" aria-hidden="true">
                      <path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7z"/>
                    </svg>
                  </div>
                  <div>
                    <div className="font-black text-base sm:text-lg text-[#2B2208] leading-tight">
                      A healthier you, a happier tomorrow.
                    </div>
                    <div className="text-xs font-bold text-[#6D5A28] mt-0.5">
                      Stay consistent, stay healthy!
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setNav("assess")}
                  className="min-h-[44px] px-5 py-2.5 rounded-full bg-[#FFC83D] hover:bg-[#F5B81D] border border-[#E09D00]/40 text-[#2B2208] text-xs font-black inline-flex items-center gap-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 relative z-10"
                >
                  <Heart className="w-4 h-4 fill-[#2B2208] text-[#2B2208]" />
                  <span>HealthBuddy</span>
                </button>

                {/* Subtle Background Pine Trees and Sun Landscape Graphic */}
                <svg
                  viewBox="0 0 400 60"
                  preserveAspectRatio="none"
                  className="absolute right-0 bottom-0 h-16 w-96 opacity-25 pointer-events-none"
                  aria-hidden="true"
                >
                  <polygon points="260,60 270,35 280,60" fill="#2B2208" />
                  <polygon points="275,60 285,30 295,60" fill="#2B2208" />
                  <polygon points="290,60 300,40 310,60" fill="#2B2208" />
                  <polygon points="320,60 330,32 340,60" fill="#2B2208" />
                  <polygon points="335,60 345,25 355,60" fill="#2B2208" />
                  <polygon points="350,60 360,38 370,60" fill="#2B2208" />
                  <polygon points="375,60 385,30 395,60" fill="#2B2208" />
                </svg>
              </div>
            </div>
          )}

          {/* NEW ASSESSMENT WIZARD */}
          {nav === "assess" && (
            <AssessmentWizard
              t={t}
              token={token}
              initialStep={wizardInitialStep}
              draft={wizardDraft}
              onDraftChange={setWizardDraft}
              onComplete={(result) => {
                setAssessData({ ...result, isIllustrative: false });
                if (!result.emergency) {
                  setCareData(result.care);
                  setNav("dashboard");
                }
              }}
            />
          )}

          {/* MY PLAN VIEW */}
          {nav === "plan" && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {["heart", "diabetes", "hypertension", "obesity", "metabolic", "kidney"].map((c) => (
                  <button
                    key={c}
                    onClick={() => setActiveCondition(c)}
                    className={`min-h-[44px] px-4 py-2 rounded-xl text-xs font-bold capitalize ${
                      activeCondition === c
                        ? "bg-[#FFC83D] text-[#2B2208]"
                        : "bg-white border border-[#EFE4BE] text-[#6B5B2E]"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
              {activePlan && <PlanTabs plan={activePlan} t={t} locale={lang} />}
            </div>
          )}

          {/* FIND CARE VIEW */}
          {nav === "care" && (
            <div className="space-y-5">
              <HospitalList
                hospitals={hospitals}
                specialistTypes={["Cardiologist", "Endocrinologist", "Neurologist", "Hepatologist"]}
                t={t}
                onOpenMap={(h) => setFocusedHospital(h)}
              />
              <HospitalMap hospitals={focusedHospital ? [focusedHospital, ...hospitals] : hospitals} />
            </div>
          )}

          {/* HISTORY VIEW */}
          {nav === "history" && (
            <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
              {statusMsg && <div className="p-3 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs font-bold">{statusMsg}</div>}
              {!token ? (
                <div className="space-y-3 max-w-md">
                  <h2 className="text-lg font-extrabold">Sign in to view history &amp; manage data</h2>
                  <input type="email" value={emailInput} onChange={(e) => setEmailInput(e.target.value)} className="w-full min-h-[44px] px-3 py-2 rounded-xl border border-[#EFE4BE] text-sm" />
                  <input type="password" value={passwordInput} onChange={(e) => setPasswordInput(e.target.value)} className="w-full min-h-[44px] px-3 py-2 rounded-xl border border-[#EFE4BE] text-sm" />
                  <button onClick={handleLogin} className="min-h-[44px] px-5 py-2.5 rounded-xl bg-[#FFC83D] text-[#2B2208] text-xs font-extrabold">
                    Sign In
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex flex-wrap justify-between items-center gap-2">
                    <span className="text-sm font-bold">Signed in as {userEmail}</span>
                    <button onClick={handleDeleteData} className="min-h-[44px] px-4 py-2 rounded-xl bg-[#FEE2E2] text-[#7F1D1D] text-xs font-bold inline-flex items-center gap-1.5">
                      <Trash2 className="w-4 h-4" /> Delete my data
                    </button>
                  </div>
                  <div className="space-y-2">
                    {historyRows.map((r) => (
                      <div key={r.id} className="p-3 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs flex justify-between">
                        <span><strong>#{r.id} {r.disease}</strong> — {r.risk_level}</span>
                        <span>{new Date(r.created_at).toLocaleString()}</span>
                      </div>
                    ))}
                    {historyRows.length === 0 && <p className="text-xs text-[#6B5B2E]">No stored assessments.</p>}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* REPORTS VIEW */}
          {nav === "reports" && (
            <div className="space-y-6">
              <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                <div className="flex flex-wrap justify-between items-center gap-3">
                  <div>
                    <h2 className="text-xl font-extrabold text-[#2B2208]">Full Health Assessment Report</h2>
                    <p className="text-xs text-[#6B5B2E]">
                      {assessData.isIllustrative ? t.illustrative_badge : "Personalized clinical screening summary"}
                    </p>
                  </div>
                  <button
                    onClick={downloadPdf}
                    className="min-h-[44px] px-4 py-2 rounded-full bg-[#FFC83D] hover:bg-[#F5B81D] text-[#2B2208] text-xs font-extrabold inline-flex items-center gap-1.5"
                  >
                    <Download className="w-4 h-4" /> {t.btn_download_pdf}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {cards.map((c) => (
                    <div key={c.id} className="p-3.5 rounded-xl bg-[#FFF9E3] border border-[#EFE4BE] text-xs space-y-1">
                      <div className="font-extrabold text-[#2B2208]">{c.label}</div>
                      <div className="text-lg font-extrabold tabular-nums">
                        {c.status === "skipped" ? "Skipped" : c.valueDisplay}
                      </div>
                      <div className="text-[#6B5B2E]">{c.method}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4">
                <h2 className="text-lg font-extrabold">16-Model Clinical Benchmarks</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-[#FFF9E3] font-bold">
                      <tr>
                        <th className="p-2.5">Disease</th>
                        <th className="p-2.5">Algorithm</th>
                        <th className="p-2.5">Accuracy</th>
                        <th className="p-2.5">F1-Weighted</th>
                        <th className="p-2.5">ROC-AUC</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarks.map((b, i) => (
                        <tr key={i} className="border-t border-[#EFE4BE]">
                          <td className="p-2.5 font-bold">{b.disease_name}</td>
                          <td className="p-2.5">{b.algorithm}</td>
                          <td className="p-2.5">{(b.accuracy * 100).toFixed(2)}%</td>
                          <td className="p-2.5">{b.f1_weighted.toFixed(4)}</td>
                          <td className="p-2.5">{b.roc_auc.toFixed(4)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* SETTINGS VIEW */}
          {nav === "settings" && (
            <div className="rounded-[20px] bg-white border border-[#EFE4BE] p-6 shadow-warm space-y-4 max-w-xl">
              <h2 className="text-lg font-extrabold text-[#2B2208]">Preferences &amp; Language</h2>
              <div className="flex items-center justify-between p-4 rounded-2xl bg-[#FFF9E3] border border-[#EFE4BE]">
                <div>
                  <div className="font-bold text-sm">Display Language</div>
                  <div className="text-xs text-[#6B5B2E]">Switch between English and Hindi</div>
                </div>
                <button
                  onClick={() => setLang(lang === "en" ? "hi" : "en")}
                  className="min-h-[44px] px-4 py-2 rounded-xl bg-[#FFC83D] text-[#2B2208] text-xs font-extrabold"
                >
                  {t.lang_toggle}
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
