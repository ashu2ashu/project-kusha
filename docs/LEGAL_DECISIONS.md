# Legal & Regulatory Decisions Record

| Decision | Options considered | Chosen | Date | Owner | Consequence |
|---|---|---|---|---|---|
| 1. SEBI Regulatory Posture | A: De-advisory reframing<br>B: Keep as-is with disclaimers<br>C: Register as RA/IA | **Option A (PROVISIONAL)** | 2026-10-31 | Product Owner | BUY/HOLD/AVOID stances and % allocation bands removed; replaced with qualitative risk tiers. |
| 2. Distribution Model | Personal/local workstation only<br>Publicly hosted SaaS | **Personal/local only (PROVISIONAL)** | 2026-10-31 | Product Owner | No multi-tenant hosting; single-user local execution; documented in README. |
| 3. Repository Licensing | Proprietary / all rights reserved<br>Permissive (MIT / Apache-2.0) | **Proprietary / all rights reserved (PROVISIONAL)** | 2026-10-31 | Product Owner | All rights reserved; no license granted to public; all unbacked IP secrecy claims removed. |
| 4. Third-Party Data Redistribution | On-demand transient fetching<br>Redistributed raw datasets | **On-demand transient fetching** | 2026-10-31 | Product Owner | Raw Yahoo Finance / BSE filings queried on demand; no dataset redistribution. |
| 5. Repository Visibility | Public repository / Private repository | **OPEN — not decided** | — | Product Owner | Source is currently PUBLIC with no licence granted. One of: make private, keep public under all-rights-reserved, or adopt an OSS licence. |

## Reasoning and Context

### 1. SEBI Regulatory Posture
Under SEBI (Research Analysts) Regulations, 2014 and SEBI (Investment Advisers) Regulations, 2013, actionable buy/sell/hold calls and numeric portfolio allocation percentages constitute regulated financial advice that cannot be neutralized by disclaimer banners. Option A removes directional advice across UI, exports, and code while preserving analytical quality scoring.

### 2. Distribution Model
Project KUSHA lacks multi-user authentication, tenant isolation, and session cryptographic boundaries. Running locally preserves single-user control over session state and API keys.

### 3. Repository Licensing
No public license is granted. Unfounded marketing assertions of compiled proprietary secrecy have been stripped; Python source code remains proprietary to the owner.

### 4. Third-Party Data Redistribution
Yahoo Finance and BSE public filing endpoints are queried directly from the user workstation on an as-needed basis for local ephemeral analysis without bulk resale or secondary redistribution.

---

> This document records product decisions, not legal advice. If the tool is distributed publicly, obtain a qualified opinion on SEBI (Research Analysts) Regulations, 2014 and SEBI (Investment Advisers) Regulations, 2013.
