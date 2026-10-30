"""
forensic_risk_engine.py
Institutional Forensic Due Diligence & Concealed Risk Audit Engine for StockSage.
Performs 8 multi-year forensic accounting stress tests designed to uncover concealed
accounting anomalies, channel stuffing, expense capitalization, tax discrepancies,
credit rating alerts, and governance red flags beyond standard annual report narratives.
"""

import time
import math
import re
import html as _html
from typing import Dict, Any, List, Optional


def _esc(value: Any) -> str:
    """Escape any value before interpolation into rendered HTML."""
    return _html.escape(str(value if value is not None else ""), quote=True)


# Canonical Database of Credit Ratings for Indian Listed Equities
# (Sourced from public CRISIL, ICRA, CARE, India Ratings disclosures)
KNOWN_CREDIT_RATINGS: Dict[str, Dict[str, Any]] = {
    "ABB": {
        "agency": "CRISIL",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Virtually zero debt; strong cash reserves and robust working capital lines.",
        "rationale_date": "Oct 2025"
    },
    "ABBOTINDIA": {
        "agency": "CRISIL",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Zero debt; negative working capital cycle and high liquid cash buffers.",
        "rationale_date": "Aug 2025"
    },
    "RELIANCE": {
        "agency": "CRISIL / CARE",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Massive operating cash flows with global access to capital markets.",
        "rationale_date": "Sep 2025"
    },
    "TCS": {
        "agency": "ICRA",
        "rating": "ICRA AAA / Stable",
        "short_term": "ICRA A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Debt-free with pristine operating cash flows and strong treasury yields.",
        "rationale_date": "Jul 2025"
    },
    "HDFCBANK": {
        "agency": "CRISIL / CARE",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Robust",
        "headroom": "Pristine capital adequacy (CAR > 18%) well above RBI regulatory floor.",
        "rationale_date": "Oct 2025"
    },
    "INFY": {
        "agency": "CRISIL",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Virtually debt-free with substantial liquid investment book.",
        "rationale_date": "Aug 2025"
    },
    "LT": {
        "agency": "CRISIL / ICRA",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Strong",
        "headroom": "Deep banking relationships and well-diversified sovereign/private order book.",
        "rationale_date": "Sep 2025"
    },
    "ITC": {
        "agency": "CRISIL",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Zero net debt, generating enormous steady operating cash flow.",
        "rationale_date": "Jun 2025"
    },
    "BHARTIARTL": {
        "agency": "CRISIL / ICRA",
        "rating": "CRISIL AA+ / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Strong",
        "headroom": "Robust ARPU expansion and de-leveraging trajectory.",
        "rationale_date": "Jul 2025"
    },
    "HINDUNILVR": {
        "agency": "CRISIL",
        "rating": "CRISIL AAA / Stable",
        "short_term": "CRISIL A1+",
        "outlook": "STABLE",
        "liquidity": "Superior",
        "headroom": "Debt-free FMCG powerhouse with zero external credit dependence.",
        "rationale_date": "Sep 2025"
    }
}


class ForensicRiskEngine:
    """
    Forensic Due Diligence & Concealed Risk Audit Engine.
    Executes 8 institutional checks beyond the statutory annual report to identify
    potential accounting maneuvers, hidden leverage, channel stuffing, or tax divergence.
    """
    ENGINE_NAME = "Forensic Due Diligence & Concealed Risk Engine"
    VERSION = "2026.1"

    @classmethod
    def audit_company_forensics(
        cls,
        ticker_symbol: str,
        company_name: str,
        sector: str,
        financial_statements: Optional[Dict[str, Any]] = None,
        live_market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes the 8-pillar forensic audit on multi-year statements and external signals.
        Returns detailed check results, Forensic Quality Index (FQI 0-100), and institutional verdict.
        """
        start_time = time.time()
        sym = (ticker_symbol or "").upper().strip()
        fin = financial_statements if isinstance(financial_statements, dict) else {}
        live = live_market_data if isinstance(live_market_data, dict) else {}

        pnl = fin.get("pnl", {})
        bs = fin.get("bs", {})
        cf = fin.get("cf", {})
        cagr = fin.get("cagr", {})
        years = fin.get("years", [])

        checks: List[Dict[str, Any]] = []
        forensic_penalties = 0.0
        critical_red_flags: List[str] = []

        # =========================================================================
        # 1. CASH CONVERSION STRESS: 3-5 Year Cumulative CFO vs PAT
        # =========================================================================
        cfo_raw = cf.get("Cash from Operations (CFO)", {}).get("values", [])
        pat_raw = pnl.get("Net Profit (PAT)", {}).get("values", [])
        aligned_pairs = [(c, p) for c, p in zip(cfo_raw, pat_raw) if c is not None and p is not None]

        if len(aligned_pairs) >= 2:
            n_eval = len(aligned_pairs)
            cum_cfo = sum(c for c, p in aligned_pairs)
            cum_pat = sum(p for c, p in aligned_pairs)

            if cum_pat > 0:
                conv_ratio = (cum_cfo / cum_pat) * 100.0
                if cum_cfo < 0:
                    status = "CRITICAL"
                    forensic_penalties += 25.0
                    critical_red_flags.append("Negative Cumulative Cash Flow Divergence")
                    detail = (
                        f"Severe Divergence: {n_eval}-Year Cumulative Net Profit is ₹{cum_pat:,.1f} Cr, "
                        f"but Operating Cash Flow is NEGATIVE (-₹{abs(cum_cfo):,.1f} Cr). High probability of phantom profits."
                    )
                elif conv_ratio < 60.0:
                    status = "CRITICAL"
                    forensic_penalties += 18.0
                    critical_red_flags.append("Severe Working Capital Cash Trapping (<60% CFO/PAT)")
                    detail = (
                        f"Weak Cash Conversion: {n_eval}-Year Cumulative CFO (₹{cum_cfo:,.1f} Cr) converted only "
                        f"{conv_ratio:.1f}% of reported PAT (₹{cum_pat:,.1f} Cr). Significant profits remain uncollected."
                    )
                elif conv_ratio < 80.0:
                    status = "MONITOR"
                    forensic_penalties += 6.0
                    detail = (
                        f"Moderate Cash Conversion: {n_eval}-Year Cumulative CFO/PAT is {conv_ratio:.1f}%. "
                        f"Some earnings absorbed by working capital expansion."
                    )
                else:
                    status = "PASS"
                    detail = (
                        f"Pristine Cash Conversion: {n_eval}-Year Cumulative CFO (₹{cum_cfo:,.1f} Cr) represents "
                        f"{conv_ratio:.1f}% of PAT (₹{cum_pat:,.1f} Cr). Reported profits represent real cash in the bank."
                    )
            else:
                if cum_cfo < 0:
                    status = "CRITICAL"
                    forensic_penalties += 20.0
                    critical_red_flags.append("Dual Net Loss & Operating Cash Deficit")
                    conv_ratio = None
                    detail = (
                        f"Severe Stress: {n_eval}-Year Cumulative PAT is negative (-₹{abs(cum_pat):,.1f} Cr) and "
                        f"Operating Cash Flow is also negative (-₹{abs(cum_cfo):,.1f} Cr). High operational cash burn."
                    )
                else:
                    status = "MONITOR"
                    forensic_penalties += 5.0
                    conv_ratio = None
                    detail = (
                        f"Loss-Making with Positive Cash: {n_eval}-Year Cumulative PAT is negative (-₹{abs(cum_pat):,.1f} Cr), "
                        f"though Operating Cash Flow is positive (+₹{cum_cfo:,.1f} Cr) due to non-cash charges."
                    )
        else:
            status = "INSUFFICIENT_DATA"
            conv_ratio = None
            detail = "Multi-year cash flow or net profit series insufficient to evaluate cumulative conversion."

        checks.append({
            "id": "FOR_01_CASH_CONVERSION",
            "title": "Cash Conversion Quality (Multi-Year CFO vs PAT)",
            "category": "Earnings Quality",
            "metric": f"{conv_ratio:.1f}%" if conv_ratio is not None else "N/A",
            "benchmark": "≥ 80.0%",
            "status": status,
            "detail": detail
        })

        # =========================================================================
        # 2. REVENUE VS RECEIVABLES VELOCITY (Channel Stuffing Radar)
        # =========================================================================
        rev_raw = pnl.get("Sales / Total Revenue", {}).get("values", [])
        rec_raw = bs.get("Trade Receivables", {}).get("values", []) or bs.get("Current & Other Assets", {}).get("values", [])
        sales_cagr = cagr.get("sales_cagr")
        aligned_rec = [(r, c) for r, c in zip(rev_raw, rec_raw) if r is not None and c is not None]

        if len(aligned_rec) >= 2 and aligned_rec[-2][0] > 0 and aligned_rec[-2][1] > 0:
            rev_yoy = ((aligned_rec[-1][0] - aligned_rec[-2][0]) / abs(aligned_rec[-2][0])) * 100.0
            rec_yoy = ((aligned_rec[-1][1] - aligned_rec[-2][1]) / abs(aligned_rec[-2][1])) * 100.0
            velocity_spread = rec_yoy - rev_yoy

            if velocity_spread > 18.0 and rec_yoy > 20.0:
                rec_status = "CRITICAL"
                forensic_penalties += 16.0
                critical_red_flags.append("Receivables Expansion Outpacing Revenue (>18% Spread)")
                rec_detail = (
                    f"Channel Stuffing Alert: Current assets/receivables grew {rec_yoy:.1f}% YoY while revenue grew only "
                    f"{rev_yoy:.1f}% (Spread: +{velocity_spread:.1f}%). Suggests aggressive dealer credit or uncollected inventory."
                )
            elif velocity_spread > 8.0:
                rec_status = "MONITOR"
                forensic_penalties += 5.0
                rec_detail = (
                    f"Receivables Mild Drag: Current assets grew faster than sales by +{velocity_spread:.1f}% "
                    f"({rec_yoy:.1f}% vs {rev_yoy:.1f}%). Monitor payment cycles."
                )
            else:
                rec_status = "PASS"
                rec_detail = (
                    f"Harmonious Collections: Revenue growth ({rev_yoy:.1f}%) aligns cleanly with asset velocity "
                    f"({rec_yoy:.1f}%). Zero indication of channel stuffing."
                )
        else:
            # No receivable/revenue series means the check was never performed.
            # It must not be reported as a pass.
            rec_status = "INSUFFICIENT_DATA"
            velocity_spread = None
            rec_detail = "Receivables and revenue series unavailable or too short; channel-stuffing radar not evaluated."

        checks.append({
            "id": "FOR_02_RECEIVABLE_VELOCITY",
            "title": "Revenue vs Receivables Velocity (Channel Stuffing Radar)",
            "category": "Sales Authenticity",
            "metric": f"{velocity_spread:+.1f}% spread" if velocity_spread is not None else "N/A",
            "benchmark": "Spread ≤ +8.0%",
            "status": rec_status,
            "detail": rec_detail
        })

        # =========================================================================
        # 3. CAPITAL WORK-IN-PROGRESS (CWIP) AGING (Expense Capitalization)
        # =========================================================================
        cwip_raw = bs.get("Capital WIP", {}).get("values", [])
        ppe_raw = bs.get("Fixed Assets (Net PPE)", {}).get("values", [])
        aligned_cwip = [(c, p) for c, p in zip(cwip_raw, ppe_raw) if c is not None and p is not None]

        if aligned_cwip and aligned_cwip[-1][1] > 0:
            latest_cwip = aligned_cwip[-1][0]
            latest_ppe = aligned_cwip[-1][1]
            cwip_ratio = (latest_cwip / latest_ppe) * 100.0

            if cwip_ratio > 35.0 and len(aligned_cwip) >= 2 and aligned_cwip[-2][0] > 0 and (latest_cwip / aligned_cwip[-2][0]) > 1.25:
                cwip_status = "CRITICAL"
                forensic_penalties += 14.0
                critical_red_flags.append("Bloated CWIP / Uncommercialized Capex Hoarding")
                cwip_detail = (
                    f"Capex Bloat: CWIP is ₹{latest_cwip:,.1f} Cr ({cwip_ratio:.1f}% of Net PPE ₹{latest_ppe:,.1f} Cr). "
                    f"Delayed capitalization risks unrecorded operating cost hoarding."
                )
            elif cwip_ratio > 20.0:
                cwip_status = "MONITOR"
                forensic_penalties += 4.0
                cwip_detail = f"Active Capex: CWIP represents {cwip_ratio:.1f}% of PPE (₹{latest_cwip:,.1f} Cr). Verify timely commissioning."
            else:
                cwip_status = "PASS"
                cwip_detail = f"Prudent Asset Formation: CWIP is modest at ₹{latest_cwip:,.1f} Cr ({cwip_ratio:.1f}% of PPE). Regular capitalization."
        else:
            cwip_status = "INSUFFICIENT_DATA"
            cwip_ratio = None
            cwip_detail = "Capital WIP or net PPE series unavailable; expense-capitalization check not evaluated."

        checks.append({
            "id": "FOR_03_CWIP_AGING",
            "title": "Capital WIP Aging & Expense Capitalization Check",
            "category": "Balance Sheet Integrity",
            "metric": f"{cwip_ratio:.1f}% of PPE" if cwip_ratio is not None else "N/A",
            "benchmark": "< 20.0%",
            "status": cwip_status,
            "detail": cwip_detail
        })

        # =========================================================================
        # 4. CASH TAX PAID VS P&L TAX (Phantom Profit & Tax Leakage)
        # =========================================================================
        pbt_raw = pnl.get("Profit Before Tax (PBT)", {}).get("values", [])
        tax_raw = pnl.get("Tax Provision", {}).get("values", [])
        aligned_tax = [(p, t) for p, t in zip(pbt_raw, tax_raw) if p is not None and t is not None]

        if aligned_tax and aligned_tax[-1][0] > 0:
            latest_pbt = aligned_tax[-1][0]
            latest_tax = abs(aligned_tax[-1][1])
            effective_tax_rate = (latest_tax / latest_pbt) * 100.0

            if effective_tax_rate < 12.0:
                tax_status = "CRITICAL"
                forensic_penalties += 15.0
                critical_red_flags.append("Abnormally Low Effective Tax Rate (<12%)")
                tax_detail = (
                    f"Tax Divergence Alert: Effective tax rate is only {effective_tax_rate:.1f}% "
                    f"(Tax: ₹{latest_tax:,.1f} Cr on PBT: ₹{latest_pbt:,.1f} Cr) vs Indian corporate rate ~25%. "
                    f"Profits may be paper-only, non-taxable one-offs, or artificial transfer pricing."
                )
            elif effective_tax_rate < 18.0:
                tax_status = "MONITOR"
                forensic_penalties += 4.0
                tax_detail = f"Moderate Tax Concession: Effective tax rate is {effective_tax_rate:.1f}%. Verify tax credits or SEZ incentives."
            elif effective_tax_rate > 35.0:
                tax_status = "MONITOR"
                tax_detail = f"High Tax Outflow: Effective tax rate is {effective_tax_rate:.1f}% due to deferred tax or non-deductible items."
            else:
                tax_status = "PASS"
                tax_detail = f"Healthy Tax Realization: Effective tax rate is {effective_tax_rate:.1f}%, consistent with Indian statutory corporate rates."
        else:
            tax_status = "INSUFFICIENT_DATA"
            effective_tax_rate = None
            tax_detail = "PBT or tax provision series unavailable; effective tax rate not evaluated."

        checks.append({
            "id": "FOR_04_TAX_DIVERGENCE",
            "title": "Cash Tax Alignment vs P&L Provision",
            "category": "Tax & Earnings Authenticity",
            "metric": f"{effective_tax_rate:.1f}%" if effective_tax_rate is not None else "N/A",
            "benchmark": "18.0% – 32.0%",
            "status": tax_status,
            "detail": tax_detail
        })

        # =========================================================================
        # 5. OTHER INCOME DEPENDENCY (Core Operating Strength)
        # =========================================================================
        oth_raw = pnl.get("Other Income", {}).get("values", [])
        aligned_oth = [(p, o) for p, o in zip(pbt_raw, oth_raw) if p is not None and o is not None]

        if aligned_oth and aligned_oth[-1][0] > 0:
            latest_pbt = aligned_oth[-1][0]
            latest_oth = aligned_oth[-1][1]
            other_inc_pct = (latest_oth / latest_pbt) * 100.0

            if other_inc_pct > 30.0:
                oth_status = "CRITICAL"
                forensic_penalties += 14.0
                critical_red_flags.append("High Other Income Dependency (>30% of PBT)")
                oth_detail = (
                    f"Core Deterioration Warning: Other Income (₹{latest_oth:,.1f} Cr) drives {other_inc_pct:.1f}% of PBT "
                    f"(₹{latest_pbt:,.1f} Cr). Operating engine is weak and masked by non-core treasury/asset gains."
                )
            elif other_inc_pct > 18.0:
                oth_status = "MONITOR"
                forensic_penalties += 4.0
                oth_detail = f"Noticeable Treasury Share: Other income accounts for {other_inc_pct:.1f}% of PBT. Core profitability must be watched."
            else:
                oth_status = "PASS"
                oth_detail = f"Core-Driven Quality: Other income accounts for only {other_inc_pct:.1f}% of PBT. Profits are authentically operational."
        else:
            oth_status = "INSUFFICIENT_DATA"
            other_inc_pct = None
            oth_detail = "Other income or PBT series unavailable; non-core dependency not evaluated."

        checks.append({
            "id": "FOR_05_OTHER_INCOME_DEPENDENCY",
            "title": "Other Income Dependency & Core Business Decoupling",
            "category": "Core Earnings Purity",
            "metric": f"{other_inc_pct:.1f}% of PBT" if other_inc_pct is not None else "N/A",
            "benchmark": "< 18.0%",
            "status": oth_status,
            "detail": oth_detail
        })

        # =========================================================================
        # 6. EXTERNAL CREDIT RATING & SOLVENCY PROFILE
        # =========================================================================
        cra_info = KNOWN_CREDIT_RATINGS.get(sym)
        de_val = live.get("debt_to_equity")

        if cra_info:
            cra_rating = cra_info.get("rating", "Not rated")
            cra_outlook = cra_info.get("outlook", "STABLE")
            cra_agency = cra_info.get("agency", "Unknown agency")
            cra_headroom = cra_info.get("headroom", "")
            rationale_date = cra_info.get("rationale_date", "date not recorded")
            junior_grade = any(x in cra_rating for x in ("AA-", " A+", " A ", "BBB"))
            cra_status = (
                "PASS" if ("AAA" in cra_rating or "AA+" in cra_rating)
                else ("MONITOR" if junior_grade else "CRITICAL")
            )
            cra_detail = (
                f"External credit rating on record: {cra_agency} '{cra_rating}' "
                f"({cra_outlook} outlook, disclosure dated {rationale_date}). {cra_headroom}"
            )
        elif de_val is not None:
            if float(de_val) <= 0.3:
                cra_status = "PASS"
                cra_rating = "SOLVENT (Low-Debt Model)"
                cra_detail = f"Solvency Proxy: Low leverage balance sheet (D/E: {float(de_val):.2f}x). Ratio proxy, not rating agency certification."
            elif float(de_val) <= 0.8:
                cra_status = "MONITOR"
                cra_rating = "MODERATE LEVERAGE"
                cra_detail = f"Solvency Proxy: Manageable leverage (D/E: {float(de_val):.2f}x). Fully serviceable from operating cash."
            else:
                cra_status = "CRITICAL"
                cra_rating = "HIGH LEVERAGE"
                forensic_penalties += 12.0
                critical_red_flags.append(f"Excessive Leverage (D/E {float(de_val):.2f}x)")
                cra_detail = f"Solvency Proxy: Elevated leverage (D/E: {float(de_val):.2f}x); vulnerable to debt refinancing stress."
        else:
            cra_status = "INSUFFICIENT_DATA"
            cra_rating = "NOT EVALUATED"
            cra_detail = "No credit rating on record and no debt-to-equity input supplied; solvency not evaluated."

        checks.append({
            "id": "FOR_06_CREDIT_RATING_SOLVENCY",
            "title": "Credit Rating & Independent Bank Line Solvency",
            "category": "External Solvency",
            "metric": cra_rating,
            "benchmark": "Tier-1 AAA / AA+ or D/E ≤ 0.5x",
            "status": cra_status,
            "detail": cra_detail
        })

        # =========================================================================
        # 7. PROMOTER PLEDGE & ENCUMBRANCE RADAR (SAST Checks)
        # =========================================================================
        prom_pledge_raw = (live.get("screener_metrics", {}) or {}).get("promoter_pledging")
        pledge_pct = None
        if prom_pledge_raw is not None:
            match = re.search(r"-?\d+(?:\.\d+)?", str(prom_pledge_raw))
            if match:
                pledge_pct = float(match.group(0))

        if pledge_pct is None:
            # Absence of a pledge disclosure is not evidence of zero pledging.
            pledge_status = "INSUFFICIENT_DATA"
            pledge_metric = "N/A"
            pledge_detail = "Promoter pledge disclosure unavailable from the supplied source; encumbrance not evaluated."
        elif pledge_pct > 0.0:
            pledge_status = "CRITICAL"
            forensic_penalties += 20.0
            pledge_metric = f"{pledge_pct:.2f}% pledged"
            critical_red_flags.append(f"Active Promoter Share Pledge ({pledge_metric})")
            pledge_detail = f"Encumbrance Warning: promoter shares are pledged ({pledge_metric}) as loan collateral. High margin-call vulnerability."
        else:
            pledge_status = "PASS"
            pledge_metric = "0.0% pledged"
            pledge_detail = "Clean title: disclosure reports 0.0% of promoter shareholding pledged."

        checks.append({
            "id": "FOR_07_PROMOTER_PLEDGE",
            "title": "Promoter Pledging & Indirect Encumbrances (SAST)",
            "category": "Ownership Integrity",
            "metric": pledge_metric,
            "benchmark": "Strictly 0.0%",
            "status": pledge_status,
            "detail": pledge_detail
        })

        # =========================================================================
        # 8. AUDITOR TENURE, CARO & SECRETARIAL GOVERNANCE
        # =========================================================================
        # No auditor opinion is supplied by the market-data feed. Only evaluate when
        # an explicit disclosure was passed in; otherwise report that it was not checked.
        auditor_opinion = str(live.get("auditor_opinion") or "").strip()
        op_lower = auditor_opinion.lower()
        is_unqualified = "unqualified" in op_lower and "not unqualified" not in op_lower
        is_adverse = (
            any(marker in op_lower for marker in ("adverse", "disclaimer of opinion", "resign"))
            or (bool(re.search(r'\bqualified\b', op_lower)) and not is_unqualified)
        )

        if not auditor_opinion:
            auditor_status = "INSUFFICIENT_DATA"
            auditor_metric = "N/A"
            auditor_detail = (
                "Auditor opinion, CARO qualifications and resignation history were not supplied "
                "by the available data source; governance check not evaluated."
            )
        elif is_adverse:
            auditor_status = "CRITICAL"
            auditor_metric = "QUALIFIED / ADVERSE"
            forensic_penalties += 18.0
            critical_red_flags.append("Adverse or qualified auditor opinion")
            auditor_detail = f"Auditor disclosure supplied: {auditor_opinion}"
        else:
            auditor_status = "PASS"
            auditor_metric = "UNQUALIFIED"
            auditor_detail = f"Auditor disclosure supplied reports an unqualified opinion: {auditor_opinion}"

        checks.append({
            "id": "FOR_08_AUDITOR_GOVERNANCE",
            "title": "Statutory Auditor Independence & CARO Qualifications",
            "category": "Regulatory Governance",
            "metric": auditor_metric,
            "benchmark": "Zero Qualifications & Resignations",
            "status": auditor_status,
            "detail": auditor_detail
        })

        # =========================================================================
        # SCORING & FORENSIC QUALITY INDEX (FQI 0-100)
        # A score is only issued when enough checks were actually evaluated.
        # Missing inputs must never contribute to a clean verdict.
        # =========================================================================
        evaluated = [c for c in checks if c["status"] in ("PASS", "MONITOR", "CRITICAL")]
        insufficient = [c for c in checks if c["status"] == "INSUFFICIENT_DATA"]
        coverage = round(len(evaluated) / len(checks), 2) if checks else 0.0
        min_coverage = 0.75
        scored = len(evaluated) > 0 and coverage >= min_coverage

        candidate_score = max(round(100.0 - forensic_penalties, 1), 10.0)
        coverage_note = (
            f"Evidence coverage {len(evaluated)}/{len(checks)} checks evaluated; "
            f"{len(insufficient)} not evaluated due to missing data."
        )

        if critical_red_flags:
            verdict = "CRITICAL / HIGH FORENSIC ANOMALY RISK"
            verdict_badge = "HIGH RISK"
            verdict_color = "#DC2626"
            verdict_bg = "#FEF2F2"
            verdict_border = "#FECACA"
            verdict_desc = (
                f"Serious red flags identified ({'; '.join(critical_red_flags)}). "
                f"High risk of uncollectible revenue or disguised liabilities. {coverage_note}"
            )
            fqi_score = candidate_score if scored else None
        elif not scored:
            fqi_score = None
            verdict = "INSUFFICIENT DATA — FORENSIC SCORE WITHHELD"
            verdict_badge = "INSUFFICIENT DATA"
            verdict_color = "#64748B"
            verdict_bg = "#F8FAFC"
            verdict_border = "#CBD5E1"
            verdict_desc = (
                "Not enough forensic checks could be evaluated to issue a score. "
                f"{coverage_note} Absence of evidence is not evidence of cleanliness."
            )
        elif candidate_score >= 82.0:
            fqi_score = candidate_score
            verdict = "LOW FORENSIC RISK (BASED ON EVALUATED CHECKS)"
            verdict_badge = "PRISTINE"
            verdict_color = "#059669"
            verdict_bg = "#ECFDF5"
            verdict_border = "#A7F3D0"
            verdict_desc = (
                "Evaluated statements show healthy cash conversion and no detected red flags. "
                f"{coverage_note}"
            )
        elif candidate_score >= 60.0:
            fqi_score = candidate_score
            verdict = "MODERATE / MONITOR ACCRUAL DRIFT"
            verdict_badge = "MONITOR"
            verdict_color = "#D97706"
            verdict_bg = "#FFFBEB"
            verdict_border = "#FDE68A"
            verdict_desc = f"Mild forensic divergence detected. Monitor working-capital absorption. {coverage_note}"
        else:
            fqi_score = candidate_score
            verdict = "CRITICAL / HIGH FORENSIC ANOMALY RISK"
            verdict_badge = "HIGH RISK"
            verdict_color = "#DC2626"
            verdict_bg = "#FEF2F2"
            verdict_border = "#FECACA"
            verdict_desc = f"Multiple forensic warnings detected without a hard red flag. {coverage_note}"

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            "ticker": sym,
            "company_name": company_name,
            "sector": sector,
            "fqi_score": fqi_score,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "verdict_color": verdict_color,
            "verdict_bg": verdict_bg,
            "verdict_border": verdict_border,
            "verdict_desc": verdict_desc,
            "critical_red_flags": critical_red_flags,
            "checks": checks,
            "passed_count": sum(1 for c in checks if c["status"] == "PASS"),
            "monitor_count": sum(1 for c in checks if c["status"] == "MONITOR"),
            "critical_count": sum(1 for c in checks if c["status"] == "CRITICAL"),
            "insufficient_count": len(insufficient),
            "evaluated_count": len(evaluated),
            "coverage": coverage,
            "score_issued": scored,
            "total_checks": len(checks),
            "credit_rating": cra_info or {
                "agency": "Not verified",
                "rating": cra_rating,
                "outlook": "Not verified",
                "headroom": "No rating disclosure supplied.",
            },
            "elapsed_ms": elapsed_ms
        }


def render_forensic_dossier_html(report: Dict[str, Any]) -> str:
    """
    Renders a responsive, institutional HTML dashboard card for the 8-Pillar Forensic Risk Audit.
    """
    if not report:
        return ""

    fqi = report.get("fqi_score")
    fqi_display = f"{float(fqi):.1f}" if isinstance(fqi, (int, float)) else "N/A"
    v_badge = report.get("verdict_badge", "NOT EVALUATED")

    if v_badge == "PRISTINE":
        v_color = "#059669"
        v_bg = "#ECFDF5"
        v_border = "#A7F3D0"
    elif v_badge == "MONITOR":
        v_color = "#D97706"
        v_bg = "#FFFBEB"
        v_border = "#FDE68A"
    elif v_badge in ("NOT EVALUATED", "INSUFFICIENT DATA"):
        v_color = "#64748B"
        v_bg = "#F8FAFC"
        v_border = "#CBD5E1"
    else:
        v_color = "#DC2626"
        v_bg = "#FEF2F2"
        v_border = "#FECACA"

    v_desc = report.get("verdict_desc", "")
    checks = report.get("checks", [])
    cra = report.get("credit_rating", {})

    check_rows = []
    for c in checks:
        st = c["status"]
        if st == "PASS":
            icon = "🟢"
            bg = "#F8FAFC"
            border = "#E2E8F0"
            color = "#059669"
            badge = "PASSED"
        elif st == "MONITOR":
            icon = "🟡"
            bg = "#FFFBEB"
            border = "#FDE68A"
            color = "#D97706"
            badge = "MONITOR"
        elif st == "CRITICAL":
            icon = "🔴"
            bg = "#FEF2F2"
            border = "#FECACA"
            color = "#DC2626"
            badge = "RED FLAG"
        else:
            icon = "⚪"
            bg = "#F8FAFC"
            border = "#E2E8F0"
            color = "#64748B"
            badge = "N/A"

        check_rows.append(
            f'<div style="background:{bg}; border:1px solid {border}; border-radius:10px; padding:12px 16px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">'
            f'<div style="flex:1;">'
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
            f'<span style="font-size:16px;">{icon}</span>'
            f'<span style="font-size:13.5px; font-weight:800; color:#0F172A;">{_esc(c.get("title"))}</span>'
            f'<span style="background:#FFFFFF; color:{color}; border:1px solid {border}; font-size:10.5px; font-weight:800; padding:2px 8px; border-radius:9999px;">{_esc(c.get("category"))}</span>'
            f'</div>'
            f'<div style="font-size:12.5px; line-height:1.5; color:#475569; margin-top:4px;">{_esc(c.get("detail"))}</div>'
            f'</div>'
            f'<div style="text-align:right; min-width:110px;">'
            f'<div style="font-size:13.5px; font-weight:900; color:{color}; font-family:\'JetBrains Mono\', monospace;">{_esc(c.get("metric"))}</div>'
            f'<div style="font-size:10.5px; color:#64748B; margin-top:2px;">Benchmark: {_esc(c.get("benchmark"))}</div>'
            f'</div>'
            f'</div>'
        )

    cra_agency = cra.get("agency") or "Not verified"
    cra_rating = cra.get("rating") or "Not verified"
    cra_outlook = cra.get("outlook") or "Not verified"
    cra_headroom = cra.get("headroom") or "No rating disclosure supplied."

    # Governance card must reflect the actual check results, never a fixed "Clean Audit".
    pledge_check = next((c for c in checks if c.get("id") == "FOR_07_PROMOTER_PLEDGE"), {})
    auditor_check = next((c for c in checks if c.get("id") == "FOR_08_AUDITOR_GOVERNANCE"), {})
    pledge_metric = pledge_check.get("metric", "N/A")
    auditor_metric = auditor_check.get("metric", "N/A")
    governance_ok = (
        pledge_check.get("status") == "PASS" and auditor_check.get("status") == "PASS"
    )
    gov_color = "#059669" if governance_ok else "#64748B"
    gov_headline = f"Pledge: {pledge_metric} • Auditor: {auditor_metric}"
    gov_sub = (
        "Both encumbrance and auditor disclosures were evaluated and passed."
        if governance_ok
        else "One or more governance disclosures were unavailable or flagged — see checks below."
    )

    html = (
        f'<div style="background:#FFFFFF; border:1.5px solid {v_border}; border-radius:16px; padding:24px 26px; margin-bottom:24px; box-shadow:0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:12px; border-bottom:1px solid #E2E8F0; padding-bottom:14px;">'
        f'<div>'
        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
        f'<span style="font-size:20px;">🕵️</span>'
        f'<span style="font-size:15px; font-weight:900; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">Institutional Forensic Due Diligence & Concealed Risk Audit</span>'
        f'</div>'
        f'<div style="font-size:12px; color:#64748B;">Multi-year accrual stress, channel stuffing radar, CWIP bloat, tax discrepancy & credit rating surveillance</div>'
        f'</div>'
        f'<div style="display:flex; align-items:center; gap:10px;">'
        f'<div style="background:{v_bg}; border:1px solid {v_border}; border-radius:10px; padding:6px 14px; text-align:right;">'
        f'<div style="font-size:9.5px; font-weight:800; color:{v_color}; text-transform:uppercase;">Forensic Quality Index</div>'
        f'<div style="font-size:18px; font-weight:900; color:{v_color}; font-family:\'JetBrains Mono\', monospace;">{fqi_display} / 100</div>'
        f'</div>'
        f'<span style="background:{v_color}; color:#FFFFFF; font-size:12px; font-weight:900; padding:8px 14px; border-radius:9999px; letter-spacing:0.5px; font-family:\'JetBrains Mono\', monospace;">{_esc(v_badge)}</span>'
        f'</div>'
        f'</div>'
        f'<div style="background:{v_bg}; border:1px solid {v_border}; border-radius:10px; padding:12px 18px; margin-bottom:16px; font-size:13px; color:{v_color}; font-weight:600; line-height:1.5;">'
        f'<strong>Audit Verdict:</strong> {_esc(v_desc)}'
        f'</div>'
        f'<div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">'
        f'<div style="background:#F8FAFC; border:1.5px solid #E2E8F0; border-radius:8px; padding:12px 16px;">'
        f'<div style="font-size:10.5px; font-weight:800; color:#2563EB; text-transform:uppercase; margin-bottom:4px;">🏛️ External Credit Rating Disclosure</div>'
        f'<div style="font-size:14px; font-weight:800; color:#0F172A;">{_esc(cra_rating)} ({_esc(cra_agency)})</div>'
        f'<div style="font-size:11.5px; color:#64748B; margin-top:2px;">Outlook: {_esc(cra_outlook)} • {_esc(cra_headroom)}</div>'
        f'</div>'
        f'<div style="background:#F8FAFC; border:1.5px solid #E2E8F0; border-radius:8px; padding:12px 16px;">'
        f'<div style="font-size:10.5px; font-weight:800; color:{gov_color}; text-transform:uppercase; margin-bottom:4px;">🛡️ Governance Disclosures</div>'
        f'<div style="font-size:14px; font-weight:800; color:{gov_color};">{_esc(gov_headline)}</div>'
        f'<div style="font-size:11.5px; color:#64748B; margin-top:2px;">{_esc(gov_sub)}</div>'
        f'</div>'
        f'</div>'
        f'<div style="margin-top:14px;">'
        f'<div style="font-size:11.5px; font-weight:800; color:#64748B; text-transform:uppercase; margin-bottom:8px; letter-spacing:0.4px;">8-Pillar Forensic Stress Test Matrix</div>'
        f'{"".join(check_rows)}'
        f'</div>'
        f'</div>'
    )
    return html
