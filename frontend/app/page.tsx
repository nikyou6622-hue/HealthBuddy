"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  ClipboardList,
  Download,
  FileText,
  Heart,
  HeartPulse,
  History,
  LayoutDashboard,
  PhoneCall,
  Printer,
  RefreshCw,
  Settings,
  Sparkles,
  Trash2,
  Utensils,
} from "lucide-react";
import en from "@/locales/en.json";
import hi from "@/locales/hi.json";
import { apiFetch, getApiBase, RecoModelInfo, RecoResponse } from "@/lib/api";
import { DisclaimerBanner } from "@/components/banners/DisclaimerBanner";
import { AppShell } from "@/components/layout/AppShell";
import { NavItemDef } from "@/components/layout/Sidebar";
import { SummaryHeader } from "@/components/Dashboard/SummaryHeader";
import { RiskGrid } from "@/components/Dashboard/RiskGrid";
import { NextSteps } from "@/components/Dashboard/NextSteps";
import { TrendsChart, TrendPoint } from "@/components/Dashboard/TrendsChart";
import { CareSection } from "@/components/Dashboard/CareSection";
import { GuidanceTabs } from "@/components/Dashboard/GuidanceTabs";
import { PersonalizedPlanCard } from "@/components/Dashboard/PersonalizedPlanCard";
import { MlScreeningCard } from "@/components/Dashboard/MlScreeningCard";
import { ConditionCardData } from "@/components/Results/ConditionCard";
import { PlanTabs } from "@/components/Plan/PlanTabs";
import { getLocalizedPlan, LocalizedPlan } from "@/lib/plans";
import { HospitalList } from "@/components/Care/HospitalList";
import { HospitalMap } from "@/components/map/HospitalMap";
import { AssessmentWizard, DEFAULT_WIZARD_DRAFT, WizardDraft } from "@/components/Wizard/AssessmentWizard";
import { HealthBuddyChat } from "@/components/Chat/HealthBuddyChat";
import { KnowledgeBaseView } from "@/components/KnowledgeBase/KnowledgeBaseView";

type NavKey = "dashboard" | "assess" | "plan" | "care" | "kb" | "history" | "reports" | "settings";

const ILLUSTRATIVE_ASSESSMENT = {
  emergency: null,
  isIllustrative: true,
  assessed_at: null as string | null,
  urgency: "within_2_weeks",
  what_to_do_first: [
    "Review your moderate cardiovascular risk with a physician.",
    "Add missing kidney labs (creatinine & urine ACR) if advised.",
    "Follow the Indian food and activity guidance for your plan.",
  ],
  modules: [
    { module: "heart_who_cvd", status: "computed", score: 12, category: "low", method: "WHO South Asia 10-year chart" },
    { module: "diabetes_idrs", status: "computed", score: 40, category: "moderate", method: "MDRF IDRS" },
    { module: "hypertension_bp", status: "computed", score: 135, bp_display: "135/85 mmHg", bp_stage: "stage_1", category: "moderate", method: "ICMR/ACC BP staging" },
    { module: "obesity_anthropometry", status: "computed", score: 24.9, category: "moderate", method: "Indian BMI cutoffs" },
    { module: "metabolic_syndrome", status: "computed", score: 2, category: "moderate", method: "Harmonized South Asian criteria" },
    { module: "kidney_ckd_epi", status: "skipped", score: null, category: "skipped", skip_reason: "Creatinine missing", method: "CKD-EPI 2021 eGFR" },
  ],
  followups: [
    { condition: "heart", tier: "low", due_date: "2027-05-24" },
    { condition: "diabetes", tier: "moderate", due_date: "2026-12-26" },
    { condition: "hypertension", tier: "moderate", due_date: "2026-12-10" },
  ],
};

export default function HealthBuddyPage() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const t: Record<string, string> = lang === "en" ? en : hi;

  const [darkMode, setDarkMode] = useState(false);
  const [nav, setNav] = useState<NavKey>("assess");
  const [searchQuery, setSearchQuery] = useState("");
  const [wizardDraft, setWizardDraft] = useState<WizardDraft>(DEFAULT_WIZARD_DRAFT);
  const [wizardInitialStep, setWizardInitialStep] = useState<1 | 2 | 3>(1);
  const [assessData, setAssessData] = useState<any>(ILLUSTRATIVE_ASSESSMENT);
  const [activeCondition, setActiveCondition] = useState<string>("heart");

  const [hospitals, setHospitals] = useState<any[]>([]);
  const [careData, setCareData] = useState<any>(null);
  const [kbData, setKbData] = useState<any>(null);
  const [focusedHospital, setFocusedHospital] = useState<any>(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);

  const [mlSecondary, setMlSecondary] = useState<Record<string, any>>({});
  const [mlLoading, setMlLoading] = useState<string | null>(null);
  const [mlError, setMlError] = useState<string | null>(null);
  const [modelsMeta, setModelsMeta] = useState<Record<string, any>>({});
  const [benchmarks, setBenchmarks] = useState<any[]>([]);

  const [recoData, setRecoData] = useState<RecoResponse | null>(null);
  const [recoModelInfo, setRecoModelInfo] = useState<RecoModelInfo | null>(null);
  const [recoLoading, setRecoLoading] = useState<boolean>(false);
  const [recoError, setRecoError] = useState<string | null>(null);

  const [token, setToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [emailInput, setEmailInput] = useState("patient@healthbuddy.local");
  const [passwordInput, setPasswordInput] = useState("Patient123!");
  const [historyRows, setHistoryRows] = useState<any[]>([]);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const [activeSection, setActiveSection] = useState<string>("sec-risk");
  const [chatOpen, setChatOpen] = useState(false);

  // Sync dark mode attribute on <html>
  useEffect(() => {
    if (typeof window !== "undefined") {
      const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
      if (prefersDark) setDarkMode(true);
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const fetchReco = async (draft: WizardDraft, currentLang: "en" | "hi" = lang) => {
    setRecoLoading(true);
    setRecoError(null);
    const num = (v: string | number | undefined) =>
      v !== undefined && v !== "" && !Number.isNaN(Number(v)) ? Number(v) : undefined;
    try {
      const res = await apiFetch<RecoResponse>("/api/v1/reco/personalized", {
        method: "POST",
        body: JSON.stringify({
          age: draft.age ?? 48,
          sex: draft.sex || "male",
          height_cm: draft.heightCm ?? 168,
          weight_kg: draft.weightKg ?? 72,
          waist_cm: draft.waistCm ?? 92,
          systolic_bp: draft.systolicBp ?? 135,
          diastolic_bp: draft.diastolicBp ?? 85,
          physical_activity: draft.physicalActivity || "mild",
          smoker: Boolean(draft.smoker),
          alcohol_drinks_per_week: draft.alcoholDrinksPerWeek ?? 0,
          family_diabetes: draft.familyDiabetes || "none",
          family_heart_disease: Boolean(draft.familyHeartDisease),
          fpg: num(draft.fpg),
          hba1c: num(draft.hba1c),
          total_cholesterol: num(draft.totalChol),
          ldl: num(draft.ldl),
          hdl: num(draft.hdl),
          triglycerides: num(draft.triglycerides),
          serum_creatinine: num(draft.creatinine),
          urine_acr: num(draft.urineAcr),
          city: draft.city || "New Delhi",
          red_flags: draft.redFlags || {},
          lang: currentLang,
          top_k: 8,
        }),
      });
      setRecoData(res);
    } catch {
      setRecoError("Could not load personalized recommendations.");
    } finally {
      setRecoLoading(false);
    }
  };

  const loadInitialData = async () => {
    setDataLoading(true);
    setDataError(null);
    try {
      const [hospRes, careRes, modelsRes, benchRes, kbRes, recoInfoRes] = await Promise.all([
        apiFetch<{ hospitals: any[] }>("/api/v1/hospitals"),
        apiFetch<any>("/api/v1/care/recommend", {
          method: "POST",
          body: JSON.stringify({ condition: "heart", tier: "moderate", city: "New Delhi" }),
        }),
        apiFetch<{ diseases: Record<string, any> }>("/api/v1/models/info"),
        apiFetch<{ matrix: any[] }>("/api/v1/models/benchmarks"),
        apiFetch<any>("/api/v1/kb").catch(() => null),
        apiFetch<RecoModelInfo>("/api/v1/reco/model-info").catch(() => null),
      ]);
      setHospitals(hospRes.hospitals || []);
      setCareData(careRes);
      setModelsMeta(modelsRes.diseases || {});
      setBenchmarks(benchRes.matrix || []);
      if (kbRes) setKbData(kbRes);
      if (recoInfoRes) setRecoModelInfo(recoInfoRes);
      fetchReco(DEFAULT_WIZARD_DRAFT, "en");
    } catch {
      setDataError("Some backend services are currently unavailable.");
    } finally {
      setDataLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (nav !== "dashboard" || typeof IntersectionObserver === "undefined") return;
    const sectionIds = ["sec-risk", "sec-guidance", "sec-care", "sec-ml"];
    const elements = sectionIds
      .map((id) => document.getElementById(id))
      .filter((el): el is HTMLElement => Boolean(el));
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]?.target?.id) {
          setActiveSection(visible[0].target.id);
        }
      },
      { rootMargin: "-20% 0px -55% 0px", threshold: [0.1, 0.35, 0.6] }
    );
    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, [nav, assessData, activeCondition]);

  function scrollToSection(id: string) {
    setActiveSection(id);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

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
        kindLabel: heart?.status === "computed" ? "10-year risk" : "",
        valueDisplay:
          heart?.status === "computed" && heart?.score != null
            ? `${fmtNum.format(Number(heart.score))}%`
            : "—",
        status: heart?.status === "computed" ? "computed" : "skipped",
        category:
          heart?.status === "computed"
            ? ((heart?.category || "low") as any)
            : "skipped",
        progressPct: heart?.status === "computed" && heart?.score ? Math.min(100, Number(heart.score) * 2.5) : 0,
        method: heart?.method || "WHO South Asia 10-year chart",
        skipReason: heart?.skip_reason || "WHO chart valid for ages 40–74",
      },
      {
        id: "diabetes",
        conditionKey: "diabetes",
        label: "Diabetes Risk (IDRS)",
        kindLabel: "score",
        valueDisplay: diab?.status === "computed" && diab?.score != null ? `${fmtNum.format(Number(diab.score))}/100` : "—",
        status: diab?.status === "computed" ? "computed" : "skipped",
        category: diab?.status === "computed" ? ((diab?.category || "moderate") as any) : "skipped",
        progressPct: diab?.score != null ? Number(diab.score) : 0,
        method: "IDRS (<30 Low, 30–59 Mod, ≥60 High)",
        skipReason: diab?.skip_reason,
      },
      {
        id: "bp",
        conditionKey: "hypertension",
        label: "Blood Pressure",
        kindLabel: "",
        valueDisplay:
          bp?.status === "computed"
            ? bp?.bp_display || (bp?.score != null ? `${fmtNum.format(Number(bp.score))} mmHg` : "—")
            : "—",
        status: bp?.status === "computed" ? "computed" : "skipped",
        category: bp?.status === "computed" ? ((bp?.category || "low") as any) : "skipped",
        progressPct: bp?.status === "computed" ? pctForCat(bp?.category) : 0,
        method: bp?.bp_stage ? `Category: ${bp.bp_stage.replace("_", " ")}` : bp?.method || "BP staging",
        skipReason: bp?.skip_reason,
      },
      {
        id: "bmi",
        conditionKey: "obesity",
        label: "BMI (Indian)",
        kindLabel: "kg/m²",
        valueDisplay: bmi?.status === "computed" && bmi?.score != null ? `${fmtNum.format(Number(bmi.score))}` : "—",
        status: bmi?.status === "computed" ? "computed" : "skipped",
        category: bmi?.status === "computed" ? ((bmi?.category || "moderate") as any) : "skipped",
        progressPct: bmi?.score ? Math.min(100, (Number(bmi.score) / 35) * 100) : 0,
        method: "Indian cutoffs: ≥23 overweight, ≥25 obese",
        skipReason: bmi?.skip_reason,
      },
      {
        id: "metabolic",
        conditionKey: "metabolic",
        label: "Metabolic Syndrome",
        kindLabel: met?.status === "computed" ? "criteria" : "",
        valueDisplay: met?.status === "computed" && met?.score != null ? `${fmtNum.format(Number(met.score))}/5` : "—",
        status: met?.status === "computed" ? "computed" : "skipped",
        category: met?.status === "computed" ? ((met?.category || "moderate") as any) : "skipped",
        progressPct: met?.status === "computed" && met?.score != null ? (Number(met.score) / 5) * 100 : 0,
        method: met?.method || "Harmonized South Asian criteria",
        skipReason: met?.skip_reason || "Needs fasting glucose, triglycerides, or HDL",
      },
      {
        id: "kidney",
        conditionKey: "kidney",
        label: "Kidney Health",
        kindLabel: kid?.status === "computed" ? "eGFR" : "",
        valueDisplay: kid?.status === "computed" && kid?.score != null ? `${fmtNum.format(Number(kid.score))}` : "—",
        status: kid?.status === "computed" ? "computed" : "skipped",
        category: kid?.status === "computed" ? ((kid?.category || "skipped") as any) : "skipped",
        progressPct: kid?.status === "computed" && kid?.score ? Math.min(100, Number(kid.score)) : 0,
        method: kid?.g_stage ? `${kid.method || "CKD-EPI 2021"} (${kid.g_stage})` : kid?.method || "CKD-EPI 2021 eGFR + ACR",
        skipReason: kid?.skip_reason || "Creatinine / urine ACR missing",
      },
    ];

    if (!searchQuery.trim()) return allCards;
    const q = searchQuery.trim().toLowerCase();
    return allCards.filter(
      (c) => c.label.toLowerCase().includes(q) || c.method.toLowerCase().includes(q)
    );
  }, [assessData, fmtNum, searchQuery]);

  const trendPoints: TrendPoint[] = useMemo(() => {
    if (historyRows.length < 2) return [];
    return historyRows.slice(-6).map((r) => ({
      dateLabel: new Intl.DateTimeFormat(lang === "hi" ? "hi-IN" : "en-IN", {
        month: "short",
        day: "numeric",
      }).format(new Date(r.created_at)),
      systolicBp: r.systolic_bp ?? null,
      bmi: r.bmi ?? null,
    }));
  }, [historyRows, lang]);

  const completedCount = cards.filter((c) => c.status === "computed").length;
  const lowCount = cards.filter((c) => c.status === "computed" && c.category === "low").length;
  const moderateCount = cards.filter((c) => c.status === "computed" && c.category === "moderate").length;
  const highCount = cards.filter((c) => c.status === "computed" && c.category === "high").length;
  const skippedCount = cards.filter((c) => c.status !== "computed").length;

  const activePlan: LocalizedPlan | null = getLocalizedPlan(
    lang,
    activeCondition,
    getConditionTier(activeCondition)
  );

  const runSecondaryMl = async (diseaseKey: "parkinsons" | "liver_disease", kind: "healthy" | "high_risk") => {
    setMlLoading(diseaseKey);
    setMlError(null);
    try {
      const preset = modelsMeta[diseaseKey]?.demo_presets?.[kind];
      if (!preset) {
        setMlError("Demo preset not available.");
        return;
      }
      const res = await apiFetch<any>(`/api/v1/predict/${diseaseKey}`, {
        method: "POST",
        body: JSON.stringify({ features: preset, consent_data_storage: false }),
      });
      setMlSecondary((prev) => ({ ...prev, [diseaseKey]: res }));
    } catch {
      setMlError("Could not run secondary ML screening. Please retry.");
    } finally {
      setMlLoading(null);
    }
  };

  const downloadPdf = async () => {
    const base = getApiBase();
    const endpointUrl = base ? new URL("/api/v1/reports/pdf", base).toString() : "/api/v1/reports/pdf";
    const res = await fetch(endpointUrl, {
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
        personalized_plan: recoData || null,
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
      <div className="min-h-screen bg-hb-highBg text-hb-highInk flex flex-col">
        <DisclaimerBanner text={t.banner_disclaimer} collapsedLabel={t.banner_collapsed_label} />
        <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-10 space-y-6">
          <div className="rounded-lg bg-hb-surface border-2 border-hb-highInk p-6 sm:p-8 shadow-md space-y-5">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-9 h-9 text-hb-highInk shrink-0" strokeWidth={2.2} aria-hidden="true" />
              <div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-hb-highInk">{t.emergency_title}</h1>
                <p className="text-sm text-hb-highInk mt-1">{t.emergency_sub}</p>
              </div>
            </div>

            <div className="rounded-md bg-hb-highBg p-4 space-y-1.5">
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
                  className="min-h-[44px] rounded-md bg-hb-highInk text-white p-3 font-extrabold text-center flex flex-col items-center justify-center gap-1"
                >
                  <PhoneCall className="w-4 h-4" strokeWidth={2.2} aria-hidden="true" />
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
                  <div key={h.id} className="p-3 rounded-md bg-hb-subtle border border-hb-border text-xs text-hb-ink">
                    <span className="font-extrabold">{h.name}</span> — {h.city} ({h.phone})
                  </div>
                ))}
            </div>

            <button
              type="button"
              onClick={() => {
                setAssessData(ILLUSTRATIVE_ASSESSMENT);
                setNav("assess");
              }}
              className="min-h-[44px] px-5 py-2.5 rounded-md bg-hb-ink text-hb-surface text-xs font-bold"
            >
              Return to assessment
            </button>
          </div>
        </main>
      </div>
    );
  }

  const navItems: NavItemDef[] = [
    { key: "dashboard", label: t.nav_dashboard, Icon: LayoutDashboard },
    { key: "assess", label: t.nav_new_assessment, Icon: ClipboardList },
    { key: "plan", label: t.nav_my_plan, Icon: Heart },
    { key: "care", label: t.nav_find_care, Icon: Building2 },
    { key: "kb", label: t.nav_kb || "Knowledge Base", Icon: BookOpen },
    { key: "history", label: t.nav_history, Icon: History },
    { key: "reports", label: t.nav_reports, Icon: FileText },
    { key: "settings", label: t.nav_settings || "Settings", Icon: Settings },
  ];

  const nextSteps: string[] =
    Array.isArray(assessData.what_to_do_first) && assessData.what_to_do_first.length > 0
      ? assessData.what_to_do_first.slice(0, 3)
      : ILLUSTRATIVE_ASSESSMENT.what_to_do_first;

  return (
    <AppShell
      disclaimerText={t.banner_disclaimer}
      disclaimerCollapsedLabel={t.banner_collapsed_label}
      navItems={navItems}
      activeNav={nav}
      onSelectNav={(k) => setNav(k as NavKey)}
      lang={lang}
      onToggleLang={() => setLang(lang === "en" ? "hi" : "en")}
      langLabel={t.lang_toggle}
      darkMode={darkMode}
      onToggleDarkMode={() => setDarkMode((d) => !d)}
      moreLabel={t.nav_more || "More"}
      tagline={t.tagline}
      searchQuery={searchQuery}
      onSearchChange={setSearchQuery}
      searchPlaceholder={t.search_placeholder || "Search topics, modules, or hospitals..."}
      onOpenChat={() => setChatOpen(true)}
      askLabel={t.ask_healthbuddy || "Ask HealthBuddy"}
      onDownloadPdf={downloadPdf}
      downloadLabel={t.btn_download_pdf}
      userEmail={userEmail}
      onOpenAccount={() => setNav("history")}
    >
      {/* Inline Backend Error State with Retry */}
      {dataError && (
        <div
          role="alert"
          className="rounded-md bg-hb-modBg border border-hb-modBorder px-4 py-3 text-xs font-semibold text-hb-modInk flex flex-wrap items-center justify-between gap-2"
        >
          <span>{dataError}</span>
          <button
            type="button"
            onClick={loadInitialData}
            className="px-3 py-1 rounded-md bg-hb-surface border border-hb-border text-hb-ink font-bold inline-flex items-center gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{t.retry || "Retry"}</span>
          </button>
        </div>
      )}

      {/* Page Heading for Non-Dashboard Views (ensures single semantic <h1> per view) */}
      {nav !== "dashboard" && (
        <header className="space-y-1">
          <span className="inline-block px-2.5 py-0.5 rounded-full bg-hb-accentSoft text-hb-accentInk text-[11px] font-bold uppercase tracking-wider">
            {t.header_kicker}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-hb-ink tracking-tight">
            {t.header_title}
          </h1>
          {nav === "assess" && assessData.isIllustrative && (
            <div className="pt-1 flex flex-wrap items-center justify-between gap-2 text-xs text-hb-muted">
              <span>Complete the 3-step check below to generate your personalized report.</span>
              <button
                type="button"
                onClick={() => setNav("dashboard")}
                className="font-bold text-hb-accentInk underline"
              >
                Preview sample dashboard
              </button>
            </div>
          )}
        </header>
      )}

      {/* DASHBOARD VIEW */}
      {nav === "dashboard" && (
        <div className="space-y-5">
          {assessData.isIllustrative && (
            <div className="rounded-md bg-hb-surface border border-hb-border px-4 py-2.5 text-xs font-medium text-hb-muted flex flex-wrap items-center justify-between gap-2">
              <span>{t.illustrative_badge}</span>
              <button
                type="button"
                onClick={() => setNav("assess")}
                className="font-bold text-hb-accentInk underline"
              >
                {t.nav_new_assessment}
              </button>
            </div>
          )}

          {/* Compact Health Summary Header */}
          <SummaryHeader
            completedCount={completedCount}
            totalCount={cards.length || 6}
            lowCount={lowCount}
            moderateCount={moderateCount}
            highCount={highCount}
            skippedCount={skippedCount}
            lastAssessedIso={assessData.assessed_at}
            lang={lang}
            t={t}
            onRecheck={() => setNav("assess")}
          />

          {/* Sticky Section Navigation Bar */}
          <nav
            aria-label="Report sections"
            className="sticky top-2 z-20 rounded-lg bg-hb-surface/95 backdrop-blur-md border border-hb-border shadow-sm px-3 py-2 flex flex-wrap items-center justify-between gap-2"
          >
            <div className="flex items-center gap-1.5 overflow-x-auto">
              {[
                {
                  id: "sec-risk",
                  label: t.sticky_risk || "Risk",
                  Icon: HeartPulse,
                  badge: `${completedCount}/${cards.length || 6}`,
                },
                {
                  id: "sec-guidance",
                  label: t.sticky_guidance || "Guidance",
                  Icon: Utensils,
                  badge: activeCondition,
                },
                {
                  id: "sec-reco",
                  label: t.sticky_reco || "Personalized",
                  Icon: Sparkles,
                  badge: "ML #3",
                },
                {
                  id: "sec-care",
                  label: t.sticky_care || "Care",
                  Icon: Building2,
                  badge: String((careData?.matched_hospitals || hospitals).length || 0),
                },
                {
                  id: "sec-ml",
                  label: t.sticky_ml || "ML Screening",
                  Icon: Sparkles,
                  badge: "2",
                },
              ].map(({ id, label, Icon, badge }) => {
                const isActive = activeSection === id;
                return (
                  <a
                    key={id}
                    href={`#${id}`}
                    onClick={(e) => {
                      e.preventDefault();
                      scrollToSection(id);
                    }}
                    aria-current={isActive ? "location" : undefined}
                    className={`min-h-[40px] px-3 py-1.5 rounded-md text-xs font-bold whitespace-nowrap inline-flex items-center gap-2 transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-hb-accent ${
                      isActive
                        ? "bg-hb-cta text-hb-ctaInk shadow-sm"
                        : "text-hb-muted hover:text-hb-ink hover:bg-hb-subtle"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                    <span>{label}</span>
                    <span
                      className={`px-1.5 py-0.5 rounded-full text-[10px] font-extrabold capitalize tabular-nums ${
                        isActive
                          ? "bg-hb-surface/70 text-hb-ink"
                          : "bg-hb-subtle text-hb-muted border border-hb-border"
                      }`}
                    >
                      {badge}
                    </span>
                  </a>
                );
              })}
            </div>

            <div className="hidden sm:flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setChatOpen(true)}
                className="min-h-[38px] px-2.5 py-1.5 rounded-md bg-hb-subtle hover:bg-hb-accentSoft border border-hb-border text-xs font-bold text-hb-ink inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
              >
                <img src="/healthbuddy-logo.svg" alt="" className="w-3.5 h-3.5" aria-hidden="true" />
                <span>{t.ask_healthbuddy || "Ask HealthBuddy"}</span>
              </button>
              <button
                type="button"
                onClick={downloadPdf}
                aria-label={t.btn_download_pdf || "Download PDF"}
                className="min-h-[38px] px-2.5 py-1.5 rounded-md bg-hb-subtle hover:bg-hb-border/40 border border-hb-border text-xs font-bold text-hb-ink inline-flex items-center gap-1.5 focus:outline-none focus:ring-2 focus:ring-hb-accent transition-colors"
              >
                <Download className="w-3.5 h-3.5" aria-hidden="true" />
                <span>PDF</span>
              </button>
            </div>
          </nav>

          {/* Sorted KPI Risk Grid (Urgent / High -> Moderate -> Low -> Skipped) */}
          <RiskGrid
            cards={cards}
            t={t}
            loading={dataLoading && cards.length === 0}
            riskKnowledge={kbData?.risk_modules || []}
            onViewPlan={(condKey) => {
              setActiveCondition(condKey);
              setNav("plan");
            }}
            onAddLabs={() => {
              setWizardInitialStep(3);
              setNav("assess");
            }}
          />

          {/* Split Row: Next Steps (Max 3) + Longitudinal Health Trends */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <NextSteps
              steps={nextSteps}
              t={t}
              onSeeFullPlan={() => setNav("plan")}
              onRecheck={() => {
                setWizardInitialStep(3);
                setNav("assess");
              }}
            />
            <TrendsChart
              points={trendPoints}
              t={t}
              onStartAssess={() => setNav("assess")}
            />
          </div>

          {/* Tabbed Guidance (Food / Exercise / Doctor & Lab Tests / Follow-up) */}
          <GuidanceTabs
            activeCondition={activeCondition}
            onSelectCondition={setActiveCondition}
            getConditionTier={getConditionTier}
            activePlan={activePlan}
            followups={assessData.followups || []}
            kbGuidance={kbData?.guidance || []}
            kbFaqs={kbData?.faqs || []}
            kbFoods={kbData?.foods || []}
            kbExercises={kbData?.exercises || []}
            lang={lang}
            t={t}
            onSeeFullPlan={() => setNav("plan")}
            onDownloadPdf={downloadPdf}
          />

          {/* Personalized Plan (ML #3) */}
          <PersonalizedPlanCard
            data={recoData}
            modelInfo={recoModelInfo}
            loading={recoLoading}
            error={recoError}
            lang={lang}
            t={t}
            onRetry={() => fetchReco(wizardDraft)}
            onAddLabs={() => {
              setWizardInitialStep(3);
              setNav("assess");
            }}
          />

          {/* Side-by-Side Verified Care & Interactive Map */}
          <CareSection
            hospitals={hospitals}
            matchedHospitals={careData?.matched_hospitals || []}
            specialistTypes={careData?.specialist_types || ["Cardiologist", "Endocrinologist"]}
            urgency={assessData.urgency}
            focusedHospital={focusedHospital}
            onSelectHospital={(h) => setFocusedHospital(h)}
            kbDoctors={kbData?.doctors || []}
            kbServices={kbData?.care || []}
            kbCareFaqs={(kbData?.faqs || []).filter((f: any) => f.category === "care")}
            t={t}
          />

          {/* Secondary, Non-Diagnostic ML Screening */}
          <MlScreeningCard
            mlSecondary={mlSecondary}
            mlLoading={mlLoading}
            mlError={mlError}
            onRunMl={runSecondaryMl}
            t={t}
          />

          {/* Warm Golden Motivational Footer */}
          <div className="relative overflow-hidden rounded-2xl border border-[#F3DC87] dark:border-hb-border shadow-sm flex flex-wrap items-center justify-between gap-4 px-6 py-5"
            style={{ background: "linear-gradient(135deg, #FFF5CC 0%, #FFE566 60%, #FFC83D 100%)" }}>
            <div className="flex items-center gap-4 relative z-10">
              {/* Running person icon */}
              <div className="w-12 h-12 rounded-2xl bg-white/60 flex items-center justify-center shrink-0 shadow-sm">
                <svg viewBox="0 0 24 24" className="w-6 h-6 fill-[#2B2208] dark:fill-hb-ink" aria-hidden="true">
                  <path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7z"/>
                </svg>
              </div>
              <div>
                <div className="font-extrabold text-base text-hb-ink leading-tight">
                  A healthier you, a happier tomorrow.
                </div>
                <div className="text-xs font-semibold text-[#78600A] mt-0.5">
                  Stay consistent, stay healthy!
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setChatOpen(true)}
              className="min-h-[44px] px-5 py-2.5 rounded-full bg-hb-cta hover:bg-[#F5B81D] text-hb-ctaInk text-sm font-extrabold inline-flex items-center gap-2 shadow-md focus:outline-none focus:ring-2 focus:ring-hb-accent relative z-10 border-2 border-white/40 transition-colors"
            >
              <Heart className="w-4 h-4 fill-current" aria-hidden="true" />
              <span>HealthBuddy</span>
            </button>

            {/* Hills silhouette decoration */}
            <svg
              viewBox="0 0 500 60"
              preserveAspectRatio="none"
              aria-hidden="true"
              className="absolute right-0 bottom-0 h-14 w-72 opacity-30 pointer-events-none"
            >
              <path d="M0 60 L0 42 Q 80 20, 160 38 T 320 25 T 500 35 L 500 60 Z" fill="#C07A00" />
              {/* Trees */}
              <polygon points="380,35 390,10 400,35" fill="#8B6914" opacity="0.5" />
              <polygon points="400,35 412,14 424,35" fill="#8B6914" opacity="0.4" />
              <polygon points="425,35 434,18 443,35" fill="#8B6914" opacity="0.3" />
            </svg>
          </div>
        </div>
      )}

      {/* NEW ASSESSMENT WIZARD VIEW */}
      {nav === "assess" && (
        <AssessmentWizard
          t={t}
          token={token}
          draft={wizardDraft}
          initialStep={wizardInitialStep}
          onDraftChange={setWizardDraft}
          onComplete={(result: any) => {
            setAssessData({ ...result, isIllustrative: false, assessed_at: new Date().toISOString() });
            if (result?.care) setCareData(result.care);
            // Auto-focus Guidance on the highest-risk computed condition from the lab report
            const modToCond: Record<string, string> = {
              heart_who_cvd: "heart",
              diabetes_idrs: "diabetes",
              glucose_classification: "diabetes",
              hypertension_bp: "hypertension",
              kidney_ckd_epi: "kidney",
              metabolic_syndrome: "metabolic",
              obesity_anthropometry: "obesity",
            };
            const rank: Record<string, number> = { high: 0, moderate: 1, low: 2 };
            const bestMod = (result?.modules || [])
              .filter((m: any) => m.status === "computed" && modToCond[m.module] && rank[m.category] !== undefined)
              .sort((a: any, b: any) => rank[a.category] - rank[b.category])[0];
            if (bestMod && modToCond[bestMod.module]) {
              setActiveCondition(modToCond[bestMod.module]);
            }
            fetchReco(wizardDraft);
            setNav("dashboard");
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
                type="button"
                onClick={() => setActiveCondition(c)}
                className={`min-h-[42px] px-4 py-2 rounded-full text-xs font-bold capitalize border transition-colors ${
                  activeCondition === c
                    ? "bg-hb-cta text-hb-ctaInk border-hb-cta"
                    : "bg-hb-surface border-hb-border text-hb-muted hover:text-hb-ink"
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
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
          <div className="lg:col-span-7">
            <HospitalList
              hospitals={hospitals}
              allHospitals={hospitals}
              defaultShowAll
              specialistTypes={["Cardiologist", "Endocrinologist", "Neurologist", "Hepatologist"]}
              t={t}
              onOpenMap={(h) => setFocusedHospital(h)}
            />
          </div>
          <div className="lg:col-span-5">
            <HospitalMap hospitals={focusedHospital ? [focusedHospital, ...hospitals] : hospitals} />
          </div>
        </div>
      )}

      {/* KNOWLEDGE BASE VIEW */}
      {nav === "kb" && (
        <KnowledgeBaseView t={t} onAskHealthBuddy={() => setChatOpen(true)} />
      )}

      {/* HISTORY VIEW */}
      {nav === "history" && (
        <div className="rounded-lg bg-hb-surface border border-hb-border p-6 shadow-sm space-y-4">
          {statusMsg && (
            <div className="p-3 rounded-md bg-hb-subtle border border-hb-border text-xs font-bold text-hb-ink">
              {statusMsg}
            </div>
          )}
          {!token ? (
            <div className="space-y-3 max-w-md">
              <h2 className="text-lg font-extrabold text-hb-ink">Sign in to view history &amp; manage data</h2>
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                aria-label="Email"
                className="w-full min-h-[44px] px-3 py-2 rounded-md bg-hb-canvas border border-hb-border text-sm text-hb-ink"
              />
              <input
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                aria-label="Password"
                className="w-full min-h-[44px] px-3 py-2 rounded-md bg-hb-canvas border border-hb-border text-sm text-hb-ink"
              />
              <button
                type="button"
                onClick={handleLogin}
                className="min-h-[44px] px-5 py-2.5 rounded-md bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold"
              >
                Sign In
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap justify-between items-center gap-2">
                <span className="text-sm font-bold text-hb-ink">Signed in as {userEmail}</span>
                <button
                  type="button"
                  onClick={handleDeleteData}
                  className="min-h-[44px] px-4 py-2 rounded-md bg-hb-highBg text-hb-highInk border border-hb-highBorder text-xs font-bold inline-flex items-center gap-1.5"
                >
                  <Trash2 className="w-4 h-4" /> Delete my data
                </button>
              </div>
              <div className="space-y-2">
                {historyRows.map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-md bg-hb-subtle border border-hb-border text-xs flex justify-between tabular-nums"
                  >
                    <span>
                      <strong>#{r.id} {r.disease}</strong> — {r.risk_level}
                    </span>
                    <span className="text-hb-muted">{new Date(r.created_at).toLocaleString()}</span>
                  </div>
                ))}
                {historyRows.length === 0 && (
                  <p className="text-xs text-hb-muted">No stored assessments.</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* REPORTS VIEW (Printable Layout + Benchmarks) */}
      {nav === "reports" && (
        <div className="space-y-5">
          <div className="rounded-lg bg-hb-surface border border-hb-border p-6 shadow-sm space-y-4">
            <div className="flex flex-wrap justify-between items-center gap-3">
              <div>
                <h2 className="text-xl font-extrabold text-hb-ink">Full Health Assessment Report</h2>
                <p className="text-xs text-hb-muted">
                  {assessData.isIllustrative ? t.illustrative_badge : "Personalized clinical screening summary"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2" data-no-print="true">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="min-h-[42px] px-4 py-2 rounded-full bg-hb-subtle hover:bg-hb-border/50 border border-hb-border text-hb-ink text-xs font-bold inline-flex items-center gap-1.5"
                >
                  <Printer className="w-4 h-4" aria-hidden="true" />
                  <span>{t.btn_print_report || "Print report"}</span>
                </button>
                <button
                  type="button"
                  onClick={downloadPdf}
                  className="min-h-[42px] px-4 py-2 rounded-full bg-hb-cta hover:bg-hb-accent text-hb-ctaInk text-xs font-extrabold inline-flex items-center gap-1.5"
                >
                  <Download className="w-4 h-4" aria-hidden="true" />
                  <span>{t.btn_download_pdf}</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {cards.map((c) => (
                <div key={c.id} className="p-3.5 rounded-md bg-hb-subtle border border-hb-border text-xs space-y-1">
                  <div className="font-bold text-hb-ink">{c.label}</div>
                  <div className="text-lg font-extrabold tabular-nums text-hb-ink">
                    {c.status === "skipped" ? "—" : c.valueDisplay}
                  </div>
                  <div className="text-hb-muted">{c.method}</div>
                </div>
              ))}
            </div>
          </div>

          <TrendsChart points={trendPoints} t={t} onStartAssess={() => setNav("assess")} />

          <div className="rounded-lg bg-hb-surface border border-hb-border p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-extrabold text-hb-ink">16-Model Clinical Benchmarks</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left tabular-nums">
                <thead className="bg-hb-subtle font-bold text-hb-ink">
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
                    <tr key={i} className="border-t border-hb-border">
                      <td className="p-2.5 font-bold text-hb-ink">{b.disease_name}</td>
                      <td className="p-2.5 text-hb-muted">{b.algorithm}</td>
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
        <div className="rounded-lg bg-hb-surface border border-hb-border p-6 shadow-sm space-y-4 max-w-xl">
          <h2 className="text-lg font-extrabold text-hb-ink">Preferences &amp; Appearance</h2>

          <div className="flex items-center justify-between p-4 rounded-md bg-hb-subtle border border-hb-border">
            <div>
              <div className="font-bold text-sm text-hb-ink">Display Language</div>
              <div className="text-xs text-hb-muted">Switch between English and Hindi</div>
            </div>
            <button
              type="button"
              onClick={() => setLang(lang === "en" ? "hi" : "en")}
              className="min-h-[42px] px-4 py-2 rounded-md bg-hb-cta text-hb-ctaInk text-xs font-extrabold"
            >
              {t.lang_toggle}
            </button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-md bg-hb-subtle border border-hb-border">
            <div>
              <div className="font-bold text-sm text-hb-ink">{t.theme_label || "Appearance"}</div>
              <div className="text-xs text-hb-muted">Toggle Light or Dark clinical theme</div>
            </div>
            <button
              type="button"
              onClick={() => setDarkMode((d) => !d)}
              className="min-h-[42px] px-4 py-2 rounded-md bg-hb-surface border border-hb-border text-hb-ink text-xs font-extrabold"
            >
              {darkMode ? t.theme_light || "Light" : t.theme_dark || "Dark"}
            </button>
          </div>
        </div>
      )}

      <HealthBuddyChat
        lang={lang}
        assessmentContext={{
          heart: getConditionTier("heart"),
          diabetes: getConditionTier("diabetes"),
          hypertension: getConditionTier("hypertension"),
          obesity: getConditionTier("obesity"),
          metabolic: getConditionTier("metabolic"),
          kidney: getConditionTier("kidney"),
        }}
        open={chatOpen}
        onOpenChange={setChatOpen}
      />
    </AppShell>
  );
}
