"""ML-trained HealthBuddy knowledgebase chatbot using TF-IDF + Cosine Similarity and safety overrides."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import ARTIFACTS_DIR, BACKEND_DIR, CARE_DATA_DIR, REPO_ROOT
from app.services.kb.records import build_knowledge_base_record
from app.services.safety.disclaimers import PERSISTENT_BANNER_DISCLAIMER

CONTENT_DIR = BACKEND_DIR / "app" / "services" / "recommend" / "content"
FRONTEND_PLANS_EN = REPO_ROOT / "frontend" / "data" / "plans.en.json"
CHATBOT_ARTIFACT_PATH = ARTIFACTS_DIR / "chatbot_kb.joblib"

EMERGENCY_PATTERNS = [
    (r"\b(chest pain|chest tightness|chest pressure|pain radiating|left arm pain|jaw pain)\b", "Possible cardiac emergency symptoms"),
    (r"\b(face droop|arm weakness|slurred speech|sudden numbness|stroke)\b", "Possible stroke warning signs"),
    (r"\b(can't breathe|cannot breathe|severe shortness of breath|difficulty breathing|gasping)\b", "Severe breathing difficulty"),
    (r"\b(vomiting blood|black stool|tarry stool|severe bleeding|coughing blood)\b", "Severe gastrointestinal or internal bleeding"),
    (r"\b(unconscious|fainted|seizure|unresponsive)\b", "Loss of consciousness or seizure"),
    (r"\b(confusion|fruity breath|hyperglycemic crisis|ketoacidosis)\b", "Possible hyperglycemic crisis"),
]


@dataclass
class KBDocument:
    doc_id: str
    category: str
    condition: str
    tier: str
    title: str
    text: str
    answer: str
    source: str
    reviewer: str
    tags: List[str]


def _load_frontend_plans() -> Dict[str, Any]:
    if FRONTEND_PLANS_EN.exists():
        try:
            with open(FRONTEND_PLANS_EN, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def build_knowledge_documents() -> List[KBDocument]:
    """Assemble structured clinical, ML model, hospital, and safety documents for TF-IDF training."""
    docs: List[KBDocument] = []
    frontend_plans = _load_frontend_plans()

    # 1. Condition recommendation JSONs (food, exercise, doctor/tests, follow-up)
    if CONTENT_DIR.exists():
        for path in sorted(CONTENT_DIR.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cond = data.get("condition", path.stem)
            title = data.get("title", cond.title())
            source = data.get("source", "Clinical Guidelines")
            reviewer = data.get("reviewed_by", "Clinical Review Board")
            tiers = data.get("tiers", {})
            fe_cond = frontend_plans.get(cond, {})

            for tier_name, tier_data in tiers.items():
                fe_tier = fe_cond.get(tier_name, {})
                eat_more = fe_tier.get("eat_more", [])
                avoid = fe_tier.get("avoid", [])
                food_items = tier_data.get("food", [])
                exercise_items = tier_data.get("exercise", [])
                doctor_tests = tier_data.get("doctor_tests", [])
                hosp_guidance = tier_data.get("hospital_guidance", "")
                followup_days = tier_data.get("followup_days", 30)

                # Food & Diet document
                food_lines = []
                if eat_more:
                    food_lines.append("Eat more: " + "; ".join(eat_more))
                if avoid:
                    food_lines.append("Avoid: " + "; ".join(avoid))
                if food_items:
                    food_lines.append("Guidance: " + "; ".join(food_items))
                docs.append(
                    KBDocument(
                        doc_id=f"{cond}_{tier_name}_food",
                        category="nutrition",
                        condition=cond,
                        tier=tier_name,
                        title=f"{title} — Diet & Nutrition ({tier_name.title()} risk)",
                        text=f"{cond} {title} {tier_name} risk food diet nutrition eat avoid indian meal plan " + " ".join(food_lines),
                        answer="\n".join(food_lines),
                        source=source,
                        reviewer=reviewer,
                        tags=[cond, tier_name, "food", "diet", "nutrition"],
                    )
                )

                # Exercise document
                ex_target = fe_tier.get("exercise_target", "")
                ex_text = ("Target: " + ex_target + "\n" if ex_target else "") + " ".join(exercise_items)
                docs.append(
                    KBDocument(
                        doc_id=f"{cond}_{tier_name}_exercise",
                        category="exercise",
                        condition=cond,
                        tier=tier_name,
                        title=f"{title} — Exercise & Activity ({tier_name.title()} risk)",
                        text=f"{cond} {title} {tier_name} risk exercise physical activity workout walking fitness " + ex_text,
                        answer=(f"Target: {ex_target}\n" if ex_target else "") + "Key steps: " + "; ".join(exercise_items),
                        source=source,
                        reviewer=reviewer,
                        tags=[cond, tier_name, "exercise", "activity"],
                    )
                )

                # Doctor, Tests & Follow-up document
                doc_answer = (
                    "Recommended clinical steps & tests: "
                    + "; ".join(doctor_tests)
                    + (f"\nCare setting: {hosp_guidance}" if hosp_guidance else "")
                    + f"\nSuggested follow-up: within {followup_days} days."
                )
                docs.append(
                    KBDocument(
                        doc_id=f"{cond}_{tier_name}_care",
                        category="clinical_care",
                        condition=cond,
                        tier=tier_name,
                        title=f"{title} — Tests, Specialist & Follow-up ({tier_name.title()} risk)",
                        text=f"{cond} {title} {tier_name} risk doctor specialist tests lab follow-up hospital " + doc_answer,
                        answer=doc_answer,
                        source=source,
                        reviewer=reviewer,
                        tags=[cond, tier_name, "doctor", "tests", "followup"],
                    )
                )

    # 2. ML Model Evaluation & Feature Metadata
    if ARTIFACTS_DIR.exists():
        for disease_dir in sorted(ARTIFACTS_DIR.iterdir()):
            if not disease_dir.is_dir():
                continue
            eval_path = disease_dir / "evaluation_results.json"
            meta_path = disease_dir / "training_metadata.json"
            if not eval_path.exists():
                continue
            try:
                with open(eval_path, "r", encoding="utf-8") as f:
                    eval_data = json.load(f)
                meta_data = {}
                if meta_path.exists():
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                disease_name = disease_dir.name.replace("_", " ").title()
                best_model = eval_data.get("best_model", "logistic_regression")
                models = eval_data.get("models", {})
                best_metrics = models.get(best_model, {})
                features = meta_data.get("feature_columns", [])
                roc_auc = best_metrics.get("roc_auc")
                acc = best_metrics.get("accuracy")
                f1 = best_metrics.get("f1_weighted")
                summary = (
                    f"For {disease_name}, HealthBuddy uses {best_model.replace('_', ' ').title()} "
                    f"(ROC-AUC: {roc_auc:.3f}, Accuracy: {acc:.3f}, Weighted F1: {f1:.3f}) "
                    if isinstance(roc_auc, (int, float)) and isinstance(acc, (int, float)) and isinstance(f1, (int, float))
                    else f"For {disease_name}, HealthBuddy uses calibrated ML screening ({best_model}). "
                )
                if features:
                    summary += f"Input biomarkers ({len(features)}): {', '.join(features[:10])}{'...' if len(features) > 10 else ''}."
                docs.append(
                    KBDocument(
                        doc_id=f"ml_{disease_dir.name}",
                        category="ml_models",
                        condition=disease_dir.name,
                        tier="info",
                        title=f"ML Model Performance — {disease_name}",
                        text=f"machine learning model accuracy roc auc sensitivity specificity benchmarks biomarkers {disease_name} {best_model} {' '.join(features)}",
                        answer=summary,
                        source="HealthBuddy ML Evaluation Artifacts",
                        reviewer="Automated Cross-Validation Pipeline",
                        tags=["ml", "accuracy", "model", disease_dir.name],
                    )
                )
            except Exception:
                continue

    # 3. Verified Hospitals Directory
    hosp_csv = CARE_DATA_DIR / "hospitals.csv"
    if hosp_csv.exists():
        try:
            with open(hosp_csv, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if str(row.get("verified", "")).lower() != "true":
                        continue
                    name = row.get("name", "Hospital")
                    city = row.get("city", "")
                    specs = row.get("specialties") or row.get("specialties_text", "")
                    facs = row.get("services") or row.get("facilities_text", "")
                    ins = row.get("insurance_notes", "")
                    phone = row.get("phone", "")
                    emerg = "24x7 Emergency-capable" if str(row.get("emergency_24x7", "")).lower() == "true" else "Scheduled OPD"
                    answer = (
                        f"{name} ({city}) — {emerg}. Specialties: {specs}. "
                        f"Facilities: {facs}. Insurance/Scheme: {ins}. Phone: {phone}."
                    )
                    docs.append(
                        KBDocument(
                            doc_id=f"hospital_{row.get('id', name)}",
                            category="hospitals",
                            condition="care",
                            tier="verified",
                            title=f"Verified Hospital: {name} ({city})",
                            text=f"hospital clinic doctor care {name} {city} {specs} {facs} {ins} {emerg}",
                            answer=answer,
                            source="HealthBuddy Verified Care Directory",
                            reviewer="Admin Verification Board",
                            tags=["hospital", "care", city.lower()],
                        )
                    )
        except Exception:
            pass

    # 3b. Doctors / Specialists & Care Services from unified KB record
    try:
        kb_record = build_knowledge_base_record(save=True)
        for doc_spec in kb_record.get("doctors", []):
            sname = doc_spec.get("name", "")
            sub = doc_spec.get("subspecialty", "")
            conds = ", ".join(doc_spec.get("conditions_covered", []))
            hosps = ", ".join(doc_spec.get("available_at_hospitals", [])[:4])
            docs.append(
                KBDocument(
                    doc_id=f"doctor_{doc_spec.get('id', sname)}",
                    category="doctors",
                    condition="care",
                    tier="verified",
                    title=f"Specialist: {sname} ({sub})",
                    text=f"doctor specialist {sname} {sub} {conds} {hosps}",
                    answer=f"{sname} ({sub}) covers {conds}. Available at verified hospitals: {hosps or 'See Care Directory'}.",
                    source="HealthBuddy Specialist & Care Knowledge Base",
                    reviewer="Clinical Review Board",
                    tags=["doctor", "specialist", sname.lower()],
                )
            )
        for care_item in kb_record.get("care", []):
            cname = care_item.get("name", "")
            desc = care_item.get("description", "")
            hosps = ", ".join(care_item.get("available_at_hospitals", [])[:4])
            docs.append(
                KBDocument(
                    doc_id=f"kb_{care_item.get('id', cname)}",
                    category="care",
                    condition="care",
                    tier="verified",
                    title=f"Care & Service: {cname}",
                    text=f"care service facility routing {cname} {desc} {hosps}",
                    answer=f"{desc}" + (f" Available at: {hosps}." if hosps else ""),
                    source="HealthBuddy Care & Routing Knowledge Base",
                    reviewer="Clinical Review Board",
                    tags=["care", "service", cname.lower()],
                )
            )
        for rm in kb_record.get("risk_modules", []):
            rm_title = rm.get("title", "")
            rm_cond = rm.get("condition_key", "general")
            drivers = ", ".join(rm.get("modifiable_drivers", []))
            tests = ", ".join(rm.get("recommended_tests", []))
            docs.append(
                KBDocument(
                    doc_id=f"risk_mod_{rm.get('id', rm_cond)}",
                    category="risk_knowledge",
                    condition=rm_cond,
                    tier="all",
                    title=rm_title,
                    text=f"risk calculator {rm_title} {rm.get('methodology', '')} {rm.get('why_it_matters', '')} {drivers} {tests}",
                    answer=(
                        f"{rm.get('methodology', '')}\n"
                        f"Why it matters: {rm.get('why_it_matters', '')}\n"
                        f"Key drivers: {drivers}.\n"
                        f"Recommended tests: {tests}."
                    ),
                    source="HealthBuddy Clinical Risk Knowledge Base",
                    reviewer="Clinical Review Board",
                    tags=["risk", rm_cond, "calculator"],
                )
            )
        for faq in kb_record.get("faqs", []):
            ftitle = faq.get("title", "")
            fcat = faq.get("category", "guidance")
            docs.append(
                KBDocument(
                    doc_id=f"faq_{faq.get('id', ftitle)}",
                    category=fcat,
                    condition=fcat,
                    tier="general",
                    title=ftitle,
                    text=f"{ftitle} {faq.get('summary', '')} {faq.get('answer', '')} {' '.join(faq.get('tags', []))}",
                    answer=faq.get("answer", ""),
                    source="HealthBuddy Clinical FAQ Knowledge Base",
                    reviewer="Clinical Review Board",
                    tags=faq.get("tags", []),
                )
            )
        for food in kb_record.get("foods", []):
            fname = food.get("name", "")
            fhindi = food.get("hindi", "")
            fgroup = food.get("group", "")
            fadvice = food.get("advice", "")
            fnote = food.get("note", "")
            codes = food.get("codes", {})
            cond_summary = ", ".join(
                f"{k}: {v.replace('_', ' ')}" for k, v in codes.items()
            )
            docs.append(
                KBDocument(
                    doc_id=f"kb_{food.get('id', fname)}",
                    category="nutrition",
                    condition="food",
                    tier=fadvice,
                    title=f"Food Guide: {fname} ({fhindi})",
                    text=f"food eat diet nutrition {fname} {fhindi} {fgroup} {fadvice} {fnote} diabetes hypertension heart obesity kidney",
                    answer=(
                        f"{fname} ({fhindi}) — Group: {fgroup}, General advice: {fadvice.replace('_', ' ')}.\n"
                        f"Condition guidance: {cond_summary}.\n"
                        f"Note: {fnote}."
                    ),
                    source="HealthBuddy Indian Food Knowledge Base (ICMR-NIN aligned)",
                    reviewer="Clinical Review Board",
                    tags=["food", "diet", fgroup, fadvice],
                )
            )
        for ex in kb_record.get("exercises", []):
            ename = ex.get("name", "")
            ehindi = ex.get("hindi", "")
            ecat = ex.get("category", "")
            eint = ex.get("intensity", "")
            conds = ", ".join(ex.get("conditions_safe", []))
            clearance = "Medical clearance advised for high-risk profiles." if ex.get("medical_clearance_required") else "Generally safe to start gently."
            docs.append(
                KBDocument(
                    doc_id=f"kb_{ex.get('id', ename)}",
                    category="exercise",
                    condition="exercise",
                    tier=eint,
                    title=f"Exercise Guide: {ename} ({ehindi})",
                    text=f"exercise workout yoga pranayama {ename} {ehindi} {ecat} {eint} {conds} {ex.get('benefits', '')} {ex.get('cautions', '')}",
                    answer=(
                        f"{ename} ({ehindi}) — {ecat.title()} ({eint} intensity), Duration: {ex.get('duration_or_reps', '')}.\n"
                        f"Benefits: {ex.get('benefits', '')}.\n"
                        f"Cautions: {ex.get('cautions', '')} ({clearance})"
                    ),
                    source="HealthBuddy Exercise & Yoga Knowledge Base",
                    reviewer="Clinical Review Board",
                    tags=["exercise", ecat, eint],
                )
            )
    except Exception:
        pass

    # 4. Clinical Calculators, Privacy & Safety FAQs
    faqs = [
        KBDocument(
            doc_id="calc_indian_bmi",
            category="calculators",
            condition="obesity",
            tier="info",
            title="Indian BMI & Waist Cutoffs",
            text="bmi body mass index overweight obesity waist circumference asian indian cutoff 23 25",
            answer=(
                "HealthBuddy uses Asian/Indian BMI cutoffs: Normal 18.5–22.9 kg/m², Overweight 23.0–24.9 kg/m², "
                "and Obesity ≥ 25.0 kg/m². Abdominal obesity cutoffs are waist ≥ 90 cm for men and ≥ 80 cm for women."
            ),
            source="ICMR / Consensus Guidelines for Asian Indians",
            reviewer="HealthBuddy Clinical Team",
            tags=["bmi", "waist", "obesity"],
        ),
        KBDocument(
            doc_id="calc_idrs",
            category="calculators",
            condition="diabetes",
            tier="info",
            title="Indian Diabetes Risk Score (IDRS) & HbA1c",
            text="idrs indian diabetes risk score hba1c fasting glucose fpg prediabetes",
            answer=(
                "IDRS scores age, waist circumference, physical activity, and family history (0–100; ≥ 60 indicates high risk). "
                "When lab values are provided, HbA1c ≥ 6.5% or FPG ≥ 126 mg/dL flags diabetes range, while HbA1c 5.7–6.4% or FPG 100–125 mg/dL flags prediabetes."
            ),
            source="MDRF IDRS & ADA/ICMR Diabetes Guidelines",
            reviewer="HealthBuddy Clinical Team",
            tags=["idrs", "diabetes", "hba1c"],
        ),
        KBDocument(
            doc_id="calc_kidney_egfr",
            category="calculators",
            condition="kidney",
            tier="info",
            title="Kidney Health (CKD-EPI 2021 eGFR)",
            text="kidney egfr creatinine urine acr ckd-epi skipped missing labs",
            answer=(
                "Kidney screening uses the race-free CKD-EPI 2021 equation from serum creatinine, age, and sex (plus urine ACR if entered). "
                "If creatinine is not entered, the kidney module is safely marked 'Skipped' rather than guessing."
            ),
            source="NKF / ASN CKD-EPI 2021 Guidelines",
            reviewer="HealthBuddy Clinical Team",
            tags=["kidney", "egfr", "creatinine"],
        ),
        KBDocument(
            doc_id="faq_safety_privacy",
            category="safety",
            condition="general",
            tier="info",
            title="Safety, Disclaimers & Data Privacy",
            text="privacy consent delete data safety medical device diagnosis disclaimer emergency red flag",
            answer=(
                "HealthBuddy is an educational screening tool, not a certified medical device, and does not replace a doctor. "
                "Emergency red-flag symptoms always override ML scores. Biomarker storage is opt-in, and you can delete your stored data anytime via 'Delete my data'."
            ),
            source="HealthBuddy Safety & Privacy Policy",
            reviewer="HealthBuddy Governance",
            tags=["privacy", "safety", "disclaimer"],
        ),
    ]
    docs.extend(faqs)
    return docs


def train_chatbot_kb(save: bool = True) -> Dict[str, Any]:
    """Train the TF-IDF ML retrieval model on the HealthBuddy clinical knowledgebase."""
    documents = build_knowledge_documents()
    corpus = [f"{d.title} {' '.join(d.tags)} {d.text}" for d in documents]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    payload = {
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "documents": [asdict(d) for d in documents],
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "doc_count": len(documents),
    }
    if save:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        joblib.dump(payload, CHATBOT_ARTIFACT_PATH)
    return payload


class HealthBuddyChatbot:
    """Context-aware, safety-first ML knowledgebase chatbot."""

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Any = None
        self.documents: List[KBDocument] = []
        self.trained_at: str = ""
        self._load_or_train()

    def _load_or_train(self) -> None:
        if CHATBOT_ARTIFACT_PATH.exists():
            try:
                data = joblib.load(CHATBOT_ARTIFACT_PATH)
                self._apply_payload(data)
                return
            except Exception:
                pass
        self.retrain()

    def _apply_payload(self, data: Dict[str, Any]) -> None:
        self.vectorizer = data["vectorizer"]
        self.tfidf_matrix = data["tfidf_matrix"]
        self.documents = [KBDocument(**d) for d in data["documents"]]
        self.trained_at = data.get("trained_at", "")

    def retrain(self) -> Dict[str, Any]:
        payload = train_chatbot_kb(save=True)
        self._apply_payload(payload)
        return {"doc_count": len(self.documents), "trained_at": self.trained_at}

    def _check_emergency(self, message: str) -> Optional[str]:
        low = message.lower()
        for pattern, reason in EMERGENCY_PATTERNS:
            if re.search(pattern, low):
                return reason
        return None

    def _default_suggestions(self, lang: str) -> List[str]:
        if lang == "hi":
            return [
                "मेरे जोखिम परिणाम समझाएं",
                "मुझे क्या खाना चाहिए और क्या टालना चाहिए?",
                "मेरे लिए सुरक्षित व्यायाम क्या हैं?",
                "मुझे किस डॉक्टर से मिलना चाहिए?",
            ]
        return [
            "Explain my risk results",
            "What foods should I eat and avoid?",
            "What exercises are safe for me?",
            "Which verified hospitals or specialists fit my plan?",
            "How accurate are HealthBuddy's ML models?",
        ]

    def ask(
        self,
        message: str,
        lang: str = "en",
        assessment_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean_msg = (message or "").strip()
        if not clean_msg:
            return {
                "reply": "Please type a health question so I can search the HealthBuddy clinical knowledgebase.",
                "emergency": False,
                "confidence": 0.0,
                "matched_topics": [],
                "sources": [],
                "suggestions": self._default_suggestions(lang),
                "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
            }

        # 1. Hard-coded emergency red-flag check first
        emergency_reason = self._check_emergency(clean_msg)
        if emergency_reason:
            reply = (
                f"URGENT SAFETY ALERT ({emergency_reason}): Do not wait for screening scores or chat guidance. "
                "Call local emergency services immediately (India: 112 / 108, US: 911) or go to the nearest 24x7 emergency hospital."
            )
            return {
                "reply": reply,
                "emergency": True,
                "confidence": 1.0,
                "matched_topics": ["Emergency Red-Flag Override"],
                "sources": ["HealthBuddy Hard-Coded Safety Layer"],
                "suggestions": ["Show nearest 24x7 emergency hospitals"],
                "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
            }

        if self.vectorizer is None or self.tfidf_matrix is None:
            self._load_or_train()

        # 2. Expand query with user's active assessment tiers if asking about "my" plan/risk
        ctx_tiers: Dict[str, str] = {}
        if isinstance(assessment_context, dict):
            for k, v in assessment_context.items():
                if isinstance(v, str) and v.lower() in {"low", "moderate", "high"}:
                    ctx_tiers[k.lower()] = v.lower()

        expanded_query = clean_msg
        personal_words = ("my ", "me ", "mine", "plan", "risk", "result", "should i")
        if ctx_tiers and any(w in clean_msg.lower() for w in personal_words):
            priority_conds = [c for c, t in ctx_tiers.items() if t in {"high", "moderate"}]
            if priority_conds:
                expanded_query += " " + " ".join(f"{c} {ctx_tiers[c]}" for c in priority_conds)

        query_vec = self.vectorizer.transform([expanded_query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Boost documents that match the user's exact risk tier for a condition
        if ctx_tiers:
            for idx, doc in enumerate(self.documents):
                if doc.condition in ctx_tiers and doc.tier == ctx_tiers[doc.condition]:
                    sims[idx] *= 1.25

        ranked_indices = sims.argsort()[::-1]
        top_docs: List[KBDocument] = []
        top_score = float(sims[ranked_indices[0]]) if len(ranked_indices) > 0 else 0.0

        for idx in ranked_indices[:4]:
            score = float(sims[idx])
            if score >= 0.08:
                top_docs.append(self.documents[idx])

        if not top_docs:
            # Friendly fallback grounded in user's context
            ctx_note = ""
            if ctx_tiers:
                summary_parts = [f"{c.title()}: {t.upper()}" for c, t in ctx_tiers.items()]
                ctx_note = f" Based on your current snapshot ({', '.join(summary_parts)}), you can ask about diet, exercise, tests, or verified hospitals for any of these."
            return {
                "reply": (
                    "I couldn't find an exact match in the clinical knowledgebase for that phrasing."
                    + ctx_note
                    + " Try asking about heart health, diabetes/IDRS, blood pressure, kidney eGFR, Indian diet guidance, exercise, or verified hospitals."
                ),
                "emergency": False,
                "confidence": round(top_score, 3),
                "matched_topics": [],
                "sources": [],
                "suggestions": self._default_suggestions(lang),
                "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
            }

        # 3. Synthesize structured response from top retrieved documents
        primary = top_docs[0]
        parts = [f"**{primary.title}**\n{primary.answer}"]
        for extra in top_docs[1:3]:
            if extra.doc_id != primary.doc_id and extra.category == primary.category:
                parts.append(f"**{extra.title}**\n{extra.answer}")
            elif extra.doc_id != primary.doc_id and extra.condition == primary.condition:
                parts.append(f"**{extra.title}**\n{extra.answer}")

        if ctx_tiers and primary.condition in ctx_tiers:
            parts.append(
                f"_Personalized note: Your current assessment shows **{ctx_tiers[primary.condition].upper()}** tier for {primary.condition}._"
            )

        sources = list(dict.fromkeys(d.source for d in top_docs[:3] if d.source))
        topics = list(dict.fromkeys(d.title for d in top_docs[:3]))

        return {
            "reply": "\n\n".join(parts),
            "emergency": False,
            "confidence": round(min(top_score, 1.0), 3),
            "matched_topics": topics,
            "sources": sources,
            "suggestions": self._default_suggestions(lang),
            "disclaimer": PERSISTENT_BANNER_DISCLAIMER,
        }


_chatbot_instance: Optional[HealthBuddyChatbot] = None


def get_chatbot() -> HealthBuddyChatbot:
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = HealthBuddyChatbot()
    return _chatbot_instance

