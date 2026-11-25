# HealthBuddy v3.0 Privacy & Data Minimization Policy

1. **Data Minimization:** Raw clinical biomarker inputs are **not** stored in the database unless the user explicitly checks the data-storage consent option (`consent_data_storage=true`).
2. **Location Consent:** Browser geolocation is requested only on explicit user click (`Use My Location`), with typed city/pincode as the default fallback.
3. **Authentication & Security:** Passwords are hashed using PBKDF2-HMAC-SHA256 with per-user salts; API sessions use signed JWT tokens with role-based access control (`patient`, `clinician`, `admin`).
4. **Right to Deletion (`DELETE /api/v1/me/data`):** Authenticated users can permanently delete their stored prediction records and consent logs at any time.
5. **No Paid Listings:** Hospital matching is strictly deterministic based on clinical capabilities, verified status, and distance/location—never paid placement.

