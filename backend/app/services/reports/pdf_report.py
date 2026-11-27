"""PDF report generator for HealthBuddy v3.0 using ReportLab."""

from io import BytesIO
from datetime import datetime, timezone
from typing import Any, Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.safety.disclaimers import FULL_MEDICAL_DISCLAIMER


def generate_assessment_pdf(payload: Dict[str, Any]) -> bytes:
    """Generate a clean PDF assessment summary for patient or clinician download."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "HealthBuddy v3.0 — Clinical Screening Summary")
    y -= 22

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    y -= 26

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Assessment Result")
    y -= 18

    c.setFont("Helvetica", 10)
    lines = [
        f"Disease Module: {payload.get('disease_name', payload.get('disease', 'N/A'))}",
        f"Risk Level: {payload.get('risk_level', 'N/A')} ({payload.get('label', 'N/A')})",
        f"Calibrated Probability: {payload.get('probability', 'N/A')}",
        f"Confidence Flag: {payload.get('confidence_flag', 'N/A')}",
        f"Model Version: {payload.get('model_version', 'N/A')}",
    ]
    for line in lines:
        c.drawString(60, y, line)
        y -= 15

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Top Contributing Factors")
    y -= 18
    c.setFont("Helvetica", 10)
    for factor in payload.get("top_factors", [])[:5]:
        text = factor.get("plain_explanation", str(factor))[:95]
        c.drawString(60, y, f"- {text}")
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Matched Care Options")
    y -= 18
    c.setFont("Helvetica", 10)
    specialists: List[str] = payload.get("specialist_types", [])
    if specialists:
        c.drawString(60, y, f"Suggested Specialists: {', '.join(specialists)}")
        y -= 15
    for hosp in payload.get("matched_hospitals", [])[:3]:
        c.drawString(60, y, f"- {hosp.get('name')} ({hosp.get('city')}) | Verified: {hosp.get('verified')}")
        y -= 14

    if payload.get("modules"):
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Clinical Calculator Scores")
        y -= 16
        c.setFont("Helvetica", 9)
        for mod in payload["modules"][:7]:
            line = f"- {mod.get('module')}: {mod.get('status')} | score={mod.get('score')} | tier={mod.get('category')}"
            c.drawString(60, y, line[:95])
            y -= 13

    if payload.get("plan"):
        plan = payload["plan"]
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Care Plan ({plan.get('condition')} - {plan.get('tier')})")
        y -= 16
        c.setFont("Helvetica", 9)
        for item in (plan.get("doctor_tests") or [])[:3]:
            c.drawString(60, y, f"- Test/Doctor: {item[:85]}")
            y -= 13
        for item in (plan.get("exercise") or [])[:2]:
            c.drawString(60, y, f"- Exercise: {item[:85]}")
            y -= 13

    if payload.get("personalized_plan"):
        pplan = payload["personalized_plan"]
        cats = pplan.get("categories") or {}
        if y < 180:
            c.showPage()
            y = height - 50
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"Personalized Plan (ML #3 — {pplan.get('model_version', 'v1')})")
        y -= 16
        c.setFont("Helvetica", 9)
        for cat_key, cat_lbl in [("foods", "Top Foods"), ("exercises", "Top Exercises"), ("hospitals", "Top Hospitals"), ("specialties", "Specialists"), ("care", "Care & Follow-up")]:
            items = cats.get(cat_key) or []
            if items:
                names = ", ".join(str(x.get("name", "")) for x in items[:5])
                c.drawString(60, y, f"- {cat_lbl}: {names[:88]}")
                y -= 13

    if payload.get("followups"):
        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Follow-up Schedule")
        y -= 16
        c.setFont("Helvetica", 9)
        for fu in payload["followups"][:5]:
            c.drawString(60, y, f"- {fu.get('condition')} ({fu.get('tier')}): Due {fu.get('due_date')}")
            y -= 13

    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Disclaimer:")
    y -= 14
    c.setFont("Helvetica", 8)
    for chunk_start in range(0, len(FULL_MEDICAL_DISCLAIMER), 95):
        c.drawString(50, y, FULL_MEDICAL_DISCLAIMER[chunk_start:chunk_start + 95])
        y -= 12

    c.showPage()
    c.save()
    return buffer.getvalue()

