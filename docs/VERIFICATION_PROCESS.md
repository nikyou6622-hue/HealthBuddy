# HealthBuddy Hospital & Specialist Verification Process

1. **Official Sources Only:** Entries are sourced exclusively from official hospital websites or national medical registries (`source_url` required on every record).
2. **Three-Stage Review Workflow:** `submitted` → `reviewed` → `verified` (executed by an authenticated `admin` role and recorded in `audit_logs`).
3. **Patient Visibility Rule:** Unverified or stale records (`verified = false`) are strictly excluded from all patient-facing search and care recommendation endpoints.
4. **No Endorsement / No "Best" Claims:** Every care response carries the disclaimer: *"These are matching options, not an endorsement or medical advice."*
5. **Doctors Policy:** Individual doctor listings are deferred until medical registration numbers can be verified against official registries.

