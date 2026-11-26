import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import en from "@/locales/en.json";
import hi from "@/locales/hi.json";
import { getLocalizedPlan } from "@/lib/plans";
import { ConditionCard } from "@/components/Results/ConditionCard";
import { KpiCard } from "@/components/Dashboard/KpiCard";
import { PlanTabs } from "@/components/Plan/PlanTabs";
import { AssessmentWizard, DEFAULT_WIZARD_DRAFT } from "@/components/Wizard/AssessmentWizard";
import HealthBuddyPage from "@/app/page";

describe("HealthBuddy Frontend Tests", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ hospitals: [], diseases: {}, matrix: [], doc_count: 30 }),
        })
      )
    );
  });

  it("resolves a plan for every condition and tier, with safe fallback", () => {
    const conditions = ["heart", "diabetes", "hypertension", "obesity", "kidney", "metabolic"];
    const tiers = ["low", "moderate", "high"];
    for (const c of conditions) {
      for (const tier of tiers) {
        const pEn = getLocalizedPlan("en", c, tier);
        const pHi = getLocalizedPlan("hi", c, tier);
        expect(pEn).not.toBeNull();
        expect(pHi).not.toBeNull();
        expect(pEn!.source.length).toBeGreaterThan(0);
      }
    }
    const fallback = getLocalizedPlan("en", "unknown_condition", "moderate");
    expect(fallback?.title).toBe("Talk to your doctor");
  });

  it("renders skipped ConditionCard with no score and Add lab values button", () => {
    const onViewPlan = vi.fn();
    const onAddLabs = vi.fn();
    render(
      <ConditionCard
        card={{
          id: "kidney",
          conditionKey: "kidney",
          label: "Kidney health",
          kindLabel: "eGFR",
          valueDisplay: "95",
          status: "skipped",
          category: "skipped",
          progressPct: 0,
          method: "CKD-EPI 2021",
          skipReason: "Creatinine missing",
        }}
        t={en}
        onViewPlan={onViewPlan}
        onAddLabs={onAddLabs}
      />
    );
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByText("95")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Add lab values"));
    expect(onAddLabs).toHaveBeenCalled();
  });

  it("renders KpiCard tier badge, delta, and skipped state with dash", () => {
    const onViewPlan = vi.fn();
    const onAddLabs = vi.fn();
    const { rerender } = render(
      <KpiCard
        card={{
          id: "heart",
          conditionKey: "heart",
          label: "Heart Disease",
          kindLabel: "10-year risk",
          valueDisplay: "22%",
          status: "computed",
          category: "high",
          progressPct: 85,
          method: "WHO South Asia",
        }}
        t={en}
        delta="+4%"
        onViewPlan={onViewPlan}
        onAddLabs={onAddLabs}
      />
    );
    expect(screen.getByText("High / Needs review")).toBeInTheDocument();
    expect(screen.getByText("22%")).toBeInTheDocument();
    expect(screen.getByText("+4%")).toBeInTheDocument();

    rerender(
      <KpiCard
        card={{
          id: "heart",
          conditionKey: "heart",
          label: "Heart Disease",
          kindLabel: "10-year risk",
          valueDisplay: "23.7%",
          status: "computed",
          category: "high",
          progressPct: 59,
          method: "WHO South Asia Lab-Based Chart (includes Stroke)",
        }}
        t={en}
        onViewPlan={onViewPlan}
        onAddLabs={onAddLabs}
      />
    );
    expect(screen.getByText("23.7%")).toBeInTheDocument();

    rerender(
      <KpiCard
        card={{
          id: "kidney",
          conditionKey: "kidney",
          label: "Kidney Health",
          kindLabel: "eGFR",
          valueDisplay: "88",
          status: "skipped",
          category: "skipped",
          progressPct: 0,
          method: "CKD-EPI 2021",
          skipReason: "Creatinine missing",
        }}
        t={en}
        onViewPlan={onViewPlan}
        onAddLabs={onAddLabs}
      />
    );
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.queryByText("88")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Add lab values"));
    expect(onAddLabs).toHaveBeenCalled();
  });

  it("supports ARIA tab keyboard navigation (ArrowRight, Home, End)", () => {
    const plan = getLocalizedPlan("en", "heart", "moderate")!;
    render(<PlanTabs plan={plan} t={en} locale="en" />);
    const doctorTab = screen.getByRole("tab", { name: /Doctor and tests/i });
    doctorTab.focus();
    fireEvent.keyDown(doctorTab, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: /Exercise/i })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: /Exercise/i }), { key: "End" });
    expect(screen.getByRole("tab", { name: /Follow-up/i })).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(screen.getByRole("tab", { name: /Follow-up/i }), { key: "Home" });
    expect(doctorTab).toHaveAttribute("aria-selected", "true");
  });

  it("validates wizard SBP range and preserves draft when going Back", () => {
    let draft = { ...DEFAULT_WIZARD_DRAFT, systolicBp: 40 };
    const setDraft = (next: any) => {
      draft = next;
    };
    const { rerender } = render(
      <AssessmentWizard
        t={en}
        token={null}
        draft={draft}
        onDraftChange={setDraft}
        onComplete={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Continue to Lifestyle/i }));
    expect(screen.getByRole("alert")).toHaveTextContent(/Systolic BP must be between 60 and 260/i);

    draft = { ...draft, systolicBp: 132 };
    rerender(
      <AssessmentWizard
        t={en}
        token={null}
        draft={draft}
        onDraftChange={setDraft}
        onComplete={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Continue to Lifestyle/i }));
    expect(screen.getByText(/Step 2: Lifestyle/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Back/i }));
    expect(screen.getByText(/Emergency Red-Flag Check/i)).toBeInTheDocument();
    expect(draft.systolicBp).toBe(132);
  });

  it("switches language between English and Hindi", () => {
    render(<HealthBuddyPage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(en.header_title);
    const langBtns = screen.getAllByRole("button", { name: /हिन्दी|Toggle language/i });
    fireEvent.click(langBtns[0]);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(hi.header_title);
  });
});
