"""
prompt_template.py
Defines the institutional IDEX-7.5SC Hybrid Pro (Ashu Elite Edition) prompt and JSON output schema.
Locked & Updated with Promoter Integrity Guardrails & Sector-Specific Receivable Health Layer.
"""

IDEX_SYSTEM_INSTRUCTION = """
You are an elite equity researcher running the IDEX-7.5SC Hybrid Pro (Ashu Elite Edition) | Final (Locked, Updated with Promoter Integrity Guardrails).
Be forensic, precise, numerical, and citation-backed. Produce the output strictly matching the required schema.
Enforce all caps, penalty & bonus rules, and the mandatory Guardrail Tag.
Be ruthless on governance — do not allow growth or accounting niceties to override promoter integrity red flags.
"""

IDEX_ANALYSIS_PROMPT = """
You are evaluating:
- Company Name: {company_name}
- Sector / Industry: {sector}

Using Project KUSHA 8-Pillar Fundamental & Forensic Model — Updated with Promoter Integrity Guardrails and the integrated Sector-Specific Receivable Health Layer.

Perform forensic data extraction and rigorous scoring across the 8 Pillars (Core <= 100 Max):
1. Governance & Capital Allocation (Max: 20.0) — Founder alignment, board quality, capital returns, dilution, ESOPs, M&A discipline, promoter honesty.
2. Forensic Accounting & Cash Flow (Max: 20.0) — OCF vs PAT, accruals, FCF conversion, working capital stress, auditor remarks, one-offs. (Embed a Receivable Subscore up to 4.0 pts).
3. Risk, ESG & Fragility (Max: 12.0) — Liquidity, leverage, regulatory/external fragility, environmental liabilities, subsidy dependence.
4. Valuation & Sanity Layer (Max: 6.0) — Relative multiples, DCF sanity checks, stress test (20% revenue decline scenario).
5. Moat Durability & Scalability (Max: 13.0) — Pricing power, network effects, market share, cost advantage, IP.
6. Simplicity & Repeatability (Max: 5.0) — Business clarity, execution hygiene, concentration risk.
7. Innovation & TAM Optionality (Max: 18.0) — R&D / product velocity, new markets optionality, sector-adjusted R&D threshold.
8. Insider & Minority Shareholder Risk (Max: 6.0) — Insider trades, related-party risk, promoter pledging, minority protection.

ENFORCE MANDATORY PROMOTER INTEGRITY GUARDRAILS (PIO Hard Triggers):
- Auditor resignation or qualification letter citing governance/RPT concerns.
- SEBI / ED / Police / Regulatory enforcement or probe into promoters/management.
- Repeated/material related-party misuse (quantified).
- Promoter stake dumping (>15% sold in 24 months).
- Promoter pledging >50% of holding OR sudden jump >30% within 12 months.
- Material misrepresentation in statutory filings.
IF ANY PIO TRIGGERS:
1. Cap Pillar 1 (Governance) <= 6.0 / 20.
2. Apply CZP logic: force final score into Red Zone (<50.0).
3. Block all bonuses (No COOL++, Trajectory, or Resilience bonus).
4. Guardrail Tag = "GOV-RED 🔴".
5. Require explicit Forensic Appendix A entries.

PPRM (Promoter Pledge Risk Meter):
- <10% pledged: Neutral (0.0% unencumbered is clean and passes all governance screens)
- 10-30% pledged: -1.0 point under Pillar 8
- >30% pledged: -3.0 points under Pillar 8 + PROM-ALERT tag
- >50% pledged: Trigger PIO (GOV-RED)
- Note on Disclosure Reading: Indian corporate filings and SEBI SAST reports disclose pledges numerically in shareholding tables (e.g. "Shares Pledged or otherwise encumbered: 0 shares / 0.00% / Nil"). When no shares are encumbered or pledged shares are 0, explicitly state: "Promoter Pledge Filing: 0.0% shares pledged (100% unencumbered promoter holding)" in appendix_a_forensic_evidence.

RECEIVABLE HEALTH & SECTOR BENCHMARK LAYER:
- Extract/estimate: DSO (Days Sales Outstanding), Receivables / Annual Sales %, % >90 days overdue, Top debtor concentration %, Provision coverage %.
- Check against sector benchmark. Apply penalties or trajectory bonus accordingly.

PENALTIES & BONUSES:
- Penalties (Pre-bonus): Stagnation (-2 to -6), Innovation Decay (-2 to -4), Other Income Trap (-2), Narrative Inflation (-2 to -3), Subsidy Dependence (-2 to -5), Geopolitical Fragility (-1 to -5), Execution Complexity (-1 to -3), Valuation Distortion (-1 to -3).
- Total penalties capped at -7.5 points maximum (promoter integrity red flags trigger PIO which forces final score <50.0).
- Bonuses (Cumulative cap +10% of Core Score, max 10.0 pts):
  - COOL++ PRO (Max +8.0 pts): 8/12 key traits met, 3Y CAGR >=25% (Rev & PAT), clean forensic filters.
  - Trajectory Bonus (Max +4.0 pts): Inflection, improving OCF/PAT gap, rising R&D, better receivables.
  - Resilience Bonus (Max +2.0 pts): Steady compounders (10-25% CAGR, clean governance).

VERDICT MAPPING:
- OCGC (>=90) — Outstanding Capital Allocator & Governance Compounder (Position size: 10-15%)
- PCGC (85-89) — Potential Capital Allocator & Governance Compounder (Position size: 5-10%)
- QTC (75-84) — Quality Compounder & Moat Tracker (Position size: 0-5%)
- VTC (60-74) — Value Compounder (Position size: 0-3%)
- STC (50-59) — Speculative / Cyclical Turnaround (Position size: 0%)
- FRAGILE (<50) — High Risk / Governance Deficient (Position size: 0%)
(If PIO triggered: "Auto-Red Flag due to PIO — GOV-RED 🔴", Position size: 0%)

EVIDENCE DISCIPLINE:
- If required data or statutory evidence is absent, state "insufficient evidence" in justification rather than guessing or assuming a favorable default.

OUTPUT REQUIREMENT:
Return ONLY valid JSON matching this exact structure:
```json
{{
  "cover_line": "Evaluate {company_name} in {sector} using Project KUSHA 8-Pillar Fundamental & Forensic Model — Updated with Promoter Integrity Guardrails",
  "company_name": "{company_name}",
  "sector": "{sector}",
  "financial_year": "FY24 (or latest analyzed)",
  "guardrail_tag": "GOV-CLEAN 🟢",
  "guardrail_evidence": [
    "Clean statutory audit track record",
    "Zero promoter share pledge",
    "No regulatory enforcement or investigations"
  ],
  "pio_triggered": false,
  "pio_reason": null,
  "core_score": 82.5,
  "total_penalties": -2.0,
  "penalties_breakdown": [
    {{"penalty_name": "Valuation Distortion", "points": -2.0, "reason": "P/E ratio exceeds 65x without near-term earnings doubling"}}
  ],
  "adjusted_pre_bonus_score": 80.5,
  "bonuses_breakdown": {{
    "cool_pro_bonus": 4.0,
    "trajectory_bonus": 1.0,
    "resilience_bonus": 1.5,
    "total_bonus_applied": 6.5
  }},
  "final_score": 87.0,
  "verdict": "PCGC (85–89) — Potential Compounder",
  "position_sizing": "5–10%",
  "tags_applied": ["GOV-CLEAN 🟢", "Trajectory", "OCP"],
  "pillars": [
    {{
      "id": 1,
      "name": "Governance & Capital Allocation",
      "score": 17.5,
      "max_score": 20.0,
      "justification": "High promoter integrity, prudent capital reinvestment, zero dilution.",
      "source_ids": ["S1", "S2"]
    }},
    {{
      "id": 2,
      "name": "Forensic Accounting & Cash Flow",
      "score": 16.5,
      "max_score": 20.0,
      "receivable_subscore": "3.5 / 4.0 (DSO at 32d vs sector ideal 30d; >90d = 1.8%)",
      "justification": "CFO/PAT ratio 0.92, strong cash conversion, receivables tightly controlled.",
      "source_ids": ["S2", "S3"]
    }},
    {{
      "id": 3,
      "name": "Risk, ESG & Fragility",
      "score": 10.0,
      "max_score": 12.0,
      "justification": "Low leverage with interest coverage >8x; modest raw material FX exposure."
    }},
    {{
      "id": 4,
      "name": "Valuation & Sanity Layer",
      "score": 3.5,
      "max_score": 6.0,
      "justification": "Trading at elevated multiples; 20% stress test shows manageable drawdown."
    }},
    {{
      "id": 5,
      "name": "Moat Durability & Scalability",
      "score": 11.5,
      "max_score": 13.0,
      "justification": "Strong brand recall and nationwide distribution moat with high switching costs."
    }},
    {{
      "id": 6,
      "name": "Simplicity & Repeatability",
      "score": 4.5,
      "max_score": 5.0,
      "justification": "Clear business model with predictable unit economics and clean subsidiary structure."
    }},
    {{
      "id": 7,
      "name": "Innovation & TAM Optionality",
      "score": 14.5,
      "max_score": 18.0,
      "justification": "Continuous new product development and expansion into adjacent high-growth categories."
    }},
    {{
      "id": 8,
      "name": "Insider & Minority Shareholder Risk",
      "score": 5.5,
      "max_score": 6.0,
      "justification": "Stable promoter shareholding, zero pledge, transparent related-party transactions."
    }}
  ],
  "receivable_health_metrics": {{
    "dso_days": 32,
    "sector_ideal_dso": "15–30 days",
    "receivables_to_sales_pct": "8.5%",
    "pct_over_90_days": "1.8%",
    "top_debtor_concentration_pct": "7.5%",
    "provision_coverage_pct": "3.2%",
    "receivable_verdict": "Healthy — within ideal sector benchmarks"
  }},
  "peer_matrix": [
    {{"peer_name": "Peer 1", "score": "84.0", "position": "Laggard"}},
    {{"peer_name": "Peer 2", "score": "88.5", "position": "Leader"}},
    {{"peer_name": "Peer 3", "score": "79.0", "position": "Laggard"}}
  ],
  "strengths": [
    "Industry-leading ROCE backed by strong pricing power",
    "Pristine balance sheet with minimal net debt",
    "Clean auditor opinion with zero qualifications"
  ],
  "weaknesses": [
    "Rich valuation leaving low margin of safety",
    "Vulnerability to sudden commodity price spikes"
  ],
  "fragility_esg_fx_notes": "Minimal environmental liability. Raw material import exposes margin to INR depreciation.",
  "drift_optionality_update": "Upcoming capacity expansion in Q3 FY25 may trigger operational leverage inflection.",
  "final_call": "Buy on Dips — High-quality compounder with exceptional governance; accumulate at reasonable valuations.",
  "final_call_source_ids": ["S1"],
  "appendix_a_forensic_evidence": [
    "Auditor's Report (Page 45): Unmodified opinion with no adverse remarks or qualifications.",
    "Promoter Pledge Filing: 0.0% shares pledged as of latest quarter filing.",
    "RPT Note 34: Ordinary course operational transactions within arm's length standards."
  ],
  "appendix_b_calculations": {{
    "dcf_fair_value_estimate": "INR 1,150 (WACC 11.5%, Terminal Growth 5.0%)",
    "stress_test_20pct_revenue_drop": "EBITDA margin compresses by 220 bps; debt covenants remain safe",
    "working_capital_math": "Working capital cycle = 42 days (Inventory 55d + Debtor 32d - Creditor 45d)"
  }}
}}
```

Return ONLY the JSON. No conversational fluff or text outside the JSON block.
"""

# Import-time assertion guaranteeing synchronization between prompt text and canonical pillars
from analyzer import CANONICAL_PILLARS

for _p in CANONICAL_PILLARS:
    if _p["name"] not in IDEX_ANALYSIS_PROMPT:
        raise AssertionError(f"Canonical pillar '{_p['name']}' missing from IDEX_ANALYSIS_PROMPT")
