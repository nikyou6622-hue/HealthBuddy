# HealthBuddy v3.0 — Detailed Dashboard UI/UX & Architecture Summary

## 1. Design Philosophy & Visual System

HealthBuddy's dashboard is designed around a **safety-first, warm-clinical aesthetic** that replaces sterile hospital-gray interfaces with approachable buttercream and amber tones while preserving strict clinical clarity and high contrast.

### Color Tokens
| Role | Hex / Tailwind | Usage |
|---|---|---|
| **App Canvas** | `#FFFDF6` | Main page background, input backgrounds, exercise step cards |
| **Soft Surface** | `#FFF9E3` / `#FFF3C4` | Secondary cards, filter pills, hospital rows, follow-up cards |
| **Card Surface** | `#FFFFFF` | Primary content cards, chat message bubbles, sticky nav backdrop |
| **Warm Border** | `#EFE4BE` / `#F3EACB` | 1px card & divider borders across all modules |
| **Primary Accent** | `#FFC83D` (hover `#F5B81D`) | Primary CTAs, active nav pills, active section indicator, chat launcher |
| **Soft Accent** | `#FFE89E` / `#FFEBA3` | Numbered step badges, hero gradient start, icon containers |
| **Primary Ink** | `#2B2208` | Headings, primary labels, button text, active icons |
| **Secondary Ink** | `#6B5B2E` / `#5C4B1F` | Subtitles, metadata, guideline attributions, inactive nav text |

### Semantic Clinical Status Palette
| Risk Category | Background | Text | Border |
|---|---|---|---|
| **Low / Normal** | `#DCFCE7` (Emerald 100) | `#14532D` / `#15803D` | `#BBF7D0` |
| **Moderate / Attention** | `#FEF3C7` (Amber 100) | `#92400E` / `#B45309` | `#FDE68A` |
| **High / Urgent / Emergency** | `#FEE2E2` (Rose 100) | `#7F1D1D` / `#DC2626` | `#FECACA` |
| **Skipped / Missing Labs** | `#F1F5F9` (Slate 100) | `#475569` | `#CBD5E1` |

### Typography, Elevation & Layout Geometry
- **Border Radii:** `rounded-[24px]` for hero cards and chat drawer, `rounded-[20px]` for major report sections, `rounded-2xl` for inner cards, `rounded-full` for primary action pills.
- **Numeric Alignment:** `tabular-nums` applied to all scores, probabilities, hospital distances, countdowns, and badge counts so numbers never jitter during updates.
- **Touch Targets:** Interactive buttons and nav items enforce `min-h-[42px]` to `min-h-[44px]` for comfortable mobile and desktop use.

---

## 2. Global App Shell & Navigation (`frontend/app/page.tsx`)

1. **Persistent Safety Banner ([DisclaimerBanner.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/banners/DisclaimerBanner.tsx)):**
   - Full-width `role="status"` top bar (`bg-[#3B2F10]/95`, `#FFF9E3` text, `ShieldAlert` icon in `#FFC83D`).
   - Always visible regardless of scroll position or active view, displaying `t.banner_disclaimer`.

2. **Sidebar & Responsive Navigation:**
   - Desktop left sidebar (`aside`) with HealthBuddy brand lockup, 7 primary views (`dashboard`, `assess`, `plan`, `care`, `history`, `reports`, `settings`), a bilingual **English / हिन्दी** toggle (`lang_toggle`), and a decorative amber SVG wave footer.

3. **Top Utility Bar:**
   - **Live Search Input (`searchQuery`):** Pill-shaped search bar (`Search` icon) that filters risk modules and verified hospitals in real time when on the Dashboard.
   - **Ask HealthBuddy Button:** Warm cream pill (`Bot` icon) that opens the floating `HealthBuddyChat` ML assistant drawer.
   - **Download PDF Button:** Calls `downloadPdf()` (`POST /api/v1/reports/pdf`) and triggers a browser download of `healthbuddy_report.pdf`.
   - **Re-check my health CTA:** Primary amber pill (`RefreshCw` icon) switching to the 3-step `AssessmentWizard`.
   - **Account Avatar:** Circular `#FFC83D` button showing the user's initial (`userEmail[0]`) and linking to Auth & History.

4. **Hero Title Banner:**
   - Displays the localized kicker (`t.header_kicker`), `<h1>` headline (*"Your health snapshot"* with `#D99B00` highlight), and an inline decorative heart + ECG pulse SVG illustration on `md+` screens.
   - Shows a subtle banner when `assessData.isIllustrative` is true, prompting the user to run a personalized 3-step assessment.

---

## 3. State Management, Scroll-Spy & Data Flow

In `HealthBuddyPage` ([page.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/app/page.tsx)):
- **`assessData`:** Holds either `ILLUSTRATIVE_ASSESSMENT` (on initial load) or the live response from `POST /api/v1/assess`.
- **`cards` (`ConditionCardData[]`):** Derived via `useMemo` from `assessData.modules` across 7 clinical modules (`heart_who_cvd`, `glucose_classification`, `diabetes_idrs`, `hypertension_bp`, `obesity_anthropometry`, `metabolic_syndrome`, `kidney_ckd_epi`).
- **`activeSection` & Scroll-Spy:** An `IntersectionObserver` (`rootMargin: "-20% 0px -55% 0px"`, `threshold: [0.1, 0.35, 0.6]`) watches `#sec-risk`, `#sec-care`, `#sec-food`, `#sec-exercise`, and `#sec-followup` whenever `nav === "dashboard"`, automatically highlighting the active pill in the sticky menu.
- **`scrollToSection(id)`:** Sets `activeSection(id)` and calls `el.scrollIntoView({ behavior: "smooth", block: "start" })`. Every target `<section>` uses `scroll-mt-24` so headings never land behind the sticky bar.
- **`riskFilter`:** Filters `#sec-risk` cards between `"all"`, `"attention"` (`moderate` or `high`), `"computed"`, and `"skipped"`.
- **`activeCondition`:** Syncs the Food (`#sec-food`), Exercise (`#sec-exercise`), and full `PlanTabs` views across `heart`, `diabetes`, `hypertension`, `obesity`, `metabolic`, and `kidney`.

---

## 4. Detailed Dashboard Section Breakdown (`nav === "dashboard"`)

### A. Sticky Section Menu (`<nav aria-label="Report sections">`)
- `sticky top-2 z-20` glassmorphic white bar (`bg-white/95 backdrop-blur-md`).
- **5 Section Pills with Icons & Live Badges:**
  1. **Risk** (`HeartPulse` icon) — badge shows `computed / total` (e.g., `5/7`).
  2. **Care** (`Building2` icon) — badge shows matched hospital count.
  3. **Food** (`Utensils` icon).
  4. **Exercise** (`Dumbbell` icon).
  5. **Follow-up** (`CalendarClock` icon) — badge shows scheduled follow-up count.
- **Right Quick Action:** Compact **Download PDF** button accessible at any scroll depth.

### B. Live Quick Search Results Strip
- Conditionally rendered when `searchQuery.trim().length > 0`.
- Displays count of matching risk modules (by label, condition key, or method) and verified hospitals (by name, city, or specialties).
- Clicking a matched module sets `activeCondition` and smooth-scrolls to `#sec-risk`; clicking a matched hospital sets `focusedHospital`, opens `HospitalMap`, and smooth-scrolls to `#sec-care`.

### C. Dynamic Hero Summary Row (12-Column Grid)
1. **Overall Summary Card (`lg:col-span-7`, warm yellow gradient):**
   - **[RiskRing.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/charts/RiskRing.tsx):** 120×120 SVG circular progress ring (`stroke="#E59A00"`, animated `stroke-dashoffset` transition `0.6s ease`, `role="img"`, `aria-label`), displaying `{completed}/{total}` and a bottom-center check badge.
   - **Dynamic Headline:** Switches between `t.hero_overall_attention` (if any `moderate` or `high` module exists) and `t.hero_overall_good`.
   - **Risk Distribution Pills:** Live counts for **Low**, **Moderate**, **High** (when > 0), and **Skipped** (when > 0).
2. **Your Next Steps Card (`lg:col-span-5`, white card with stethoscope SVG):**
   - Renders up to 3 prioritized steps from `assessData.what_to_do_first` with numbered `#FFE89E` circular badges.
   - **See full plan** pill button (`ArrowRight` icon) navigating to `nav === "plan"`.

### D. Section 1 — Clinical Risk Breakdown (`#sec-risk`)
- **Section Header & Filter Bar:** `HeartPulse` icon badge, computed/review summary subtitle, and 4 filter pills (**All**, **Needs review**, **Computed**, **Missing labs**) with count badges.
- **2-Tier Grid (when `riskFilter === "all"`):**
  - **Row 1 (4 columns on `lg`):** Primary modules — Heart Disease, Prediabetes/Glycemic Status, Diabetes Risk (IDRS), Blood Pressure.
  - **Row 2 (3 columns on `sm+`):** Supporting markers — Indian BMI, Metabolic Syndrome, Kidney Health (eGFR).
- **[ConditionCard.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/Results/ConditionCard.tsx):**
  - Condition-specific icon & color themes (`pink` heart, `purple`/`red` droplet, `blue` activity, `amber` scale, `orange` shield, `teal` kidney) with subtle bottom wave SVG.
  - **Safety Guard for Missing Labs:** When `status === "skipped"` or `"needs_more_info"`, the numeric score is replaced with `"—"` (never guessed) and the CTA switches to **Add lab values** (jumping to Step 3 of the wizard).

### E. Section 2 — Care & Verified Hospitals (`#sec-care`)
- **[HospitalList.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/Care/HospitalList.tsx):**
  - Shows recommended specialist types (e.g., `Cardiologist / Endocrinologist`) and `urgency` pill.
  - Sector filter pills: **All**, **Government / Public**, **Private / Non-Profit**.
  - Displays up to 3 verified hospitals with **Verified** (`CheckCircle2`), **Emergency-capable** (`AlertCircle`), city/pincode, distance in km, primary match reason, and **Open map** button.
- **[HospitalMap.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/map/HospitalMap.tsx):**
  - Conditionally expanded when **Open map** is clicked, paired with a **Hide map** toggle button.

### F. Section 3 — Precautions: Food to Eat and Avoid (`#sec-food`)
- **Header:** `Utensils` icon badge + 6 condition selector pills (`heart`, `diabetes`, `hypertension`, `obesity`, `metabolic`, `kidney`), each displaying a live risk-colored status dot (`rose-500`, `amber-500`, `emerald-500`).
- **2-Column Comparison Grid:**
  - **Eat more** (emerald tint, item count pill, `CheckCircle2` icon cards).
  - **Avoid** (rose tint, item count pill, `Ban` icon cards).
- **Attribution Footer:** Displays clinical guideline `source`, `reviewed_by`, and a **See full plan** link.

### G. Section 4 — Physical Activity & Exercise Guidance (`#sec-exercise`)
- **Header:** `Dumbbell` icon badge + color-coded risk-tier pill (`low`, `moderate`, `high`).
- **Safety Clearance Banner:** Automatically highlights medical clearance warnings in rose-red (`AlertTriangle` icon) when `exercise_target` requires physician clearance.
- **Recommended Target Callout:** Gradient cream-to-amber banner highlighting the weekly activity target.
- **Actionable Step Cards:** 2-column grid of numbered exercise guidance cards (`1`, `2`, ...) with guideline attribution footer.

### H. Section 5 — Follow-up Schedule & Full Report (`#sec-followup`)
- **Header:** `CalendarClock` icon badge + **Download PDF** button.
- **Schedule Grid:** 3-column grid of tier-colored follow-up cards showing condition name, risk tier badge, localized due date (`en-IN` / `hi-IN` via `Intl.DateTimeFormat`), and relative countdown (`In X days`).
- **Visit Preparation Strip:** Quick checklist (*Download PDF summary*, *Recent lab reports (HbA1c, lipids, creatinine)*, *Current medication list*).

### I. Secondary Opinion ML Screening & Motivational Footer
- **Secondary ML Screening:** Interactive sample runners (*Healthy* vs. *Elevated*) for **Parkinson's voice screening (22 biomarkers)** and **Liver function ML screening (10 biomarkers)** via `POST /api/v1/predict/{disease}`, displaying risk band badge, calibrated probability %, confidence flag, and top contributing factors.
- **Motivational Banner:** Warm amber gradient footer (*"A healthier you, a happier tomorrow."*) with runner silhouette SVG, landscape backdrop, and quick re-assessment button.

---

## 5. HealthBuddy ML Knowledgebase Chatbot

### Frontend Drawer ([HealthBuddyChat.tsx](file:///media/nik/B/Healthcore/heartbuddy/frontend/components/Chat/HealthBuddyChat.tsx))
- **Launcher:** Floating bottom-right `#FFC83D` pill (`Ask HealthBuddy` + `ML` badge) plus a top utility bar shortcut.
- **Chat Window (`410px` × `560px`):**
  - Header showing `HealthBuddy`, `ML KB` badge, indexed document count from `GET /api/v1/chat/status`, **Clear chat** (`Trash2`), and **Close** (`X`) controls.
  - Message stream supporting inline bold formatting (`**...**`), **Emergency Red-Flag Override** alert cards, **Source** citations, **ML match %** confidence badges, and clickable follow-up suggestion pills.
  - Context-aware: automatically sends the user's current 6-condition `assessmentContext` and `lang` (`en` / `hi`) with every `POST /api/v1/chat` request.

### Backend ML Engine ([knowledge_bot.py](file:///media/nik/B/Healthcore/heartbuddy/backend/app/services/chatbot/knowledge_bot.py))
- **Model:** scikit-learn `TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)` + cosine similarity, persisted to `backend/artifacts/chatbot_kb.joblib`.
- **Indexed Corpus:**
  1. All 6 clinical condition recommendation JSONs + Indian meal plans (`plans.en.json`)
  2. ML evaluation & biomarker metadata (`heart_disease`, `diabetes`, `parkinsons`, `liver_disease`)
  3. Verified hospitals directory ([hospitals.csv](file:///media/nik/B/Healthcore/heartbuddy/data/care/hospitals.csv))
  4. Clinical calculator & privacy/safety FAQs (Indian BMI, IDRS, CKD-EPI 2021 eGFR, safety rules)
- **Safety-First Pipeline:**
  1. Hard-coded regex red-flag check runs *before* ML retrieval; emergency symptoms immediately return `emergency: true` with `112 / 108 / 911` guidance.
  2. Context-aware query expansion & `1.25×` score boosting for documents matching the user's active risk tiers.
  3. Minimum similarity threshold (`0.08`) with safe fallback guidance if no document matches.

---

## 6. Accessibility, Localization & Verification

- **Bilingual Support:** Full English ([en.json](file:///media/nik/B/Healthcore/heartbuddy/frontend/locales/en.json)) and Hindi ([hi.json](file:///media/nik/B/Healthcore/heartbuddy/frontend/locales/hi.json)) translations across labels, status pills, hero summaries, and chatbot prompts.
- **Accessibility:** Semantic landmarks (`<nav>`, `<main>`, `<section>`, `<header>`), `aria-label` / `aria-current="location"` on sticky nav, `role="status"` on safety banner, focus rings (`focus:ring-2 focus:ring-amber-500`), and `aria-hidden="true"` on decorative SVGs.
- **Verified Tests:**
  - Backend: `pytest -v` — `17 passed` (unit calculators, safety & care rules, API integration, and `test_healthbuddy_ml_chatbot`).
  - Frontend: `npx tsc --noEmit` & `npm test` (Vitest) — `5 passed`.
