"""
data_integrity_agent.py
Data Consistency & Reconciliation Engine (formerly Sentinel)
Performs deterministic arithmetic consistency and sanity checks on financial statements
and market data. Does NOT claim independent statutory audit, tamper-proof certification,
or external authenticity verification.
"""

import hashlib
import time
from typing import Dict, Any, List, Optional


class DataIntegritySentinel:
    """
    Automated Data Consistency & Reconciliation Engine.
    Executes standard arithmetic reconciliation checks (balance sheet identities,
    cash flow conversions, and market boundary sanity).
    Unavailable inputs result in 'INSUFFICIENT_DATA' rather than passing marks.
    """
    AGENT_NAME = "Data Consistency & Reconciliation Engine"
    AGENT_VERSION = "3.0-TRUTHFUL"
    FRAMEWORK = "Internal Arithmetic Consistency & Data Sanity Protocols"

    @classmethod
    def audit_and_certify(
        cls,
        ticker_symbol: str,
        company_name: str,
        financial_statements: Optional[Dict[str, Any]] = None,
        live_market_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Conducts 6-point arithmetic consistency and sanity checks on ingested data.
        Returns check results, evaluated count, skipped count, and deterministic status.
        """
        start_time = time.time()
        checks: List[Dict[str, Any]] = []
        penalties = 0.0
        audit_flags: List[str] = []

        fin = financial_statements or {}
        live = live_market_data or {}
        pnl = fin.get("pnl", {})
        bs = fin.get("bs", {})
        cf = fin.get("cf", {})
        years = fin.get("years", [])

        # -------------------------------------------------------------
        # CHECK 1: Balance Sheet Accounting Equation Consistency
        # Assets should be >= Net Worth (Assets = Equity + Liabilities)
        # -------------------------------------------------------------
        nw_vals = [v for v in bs.get("Total Net Worth / Equity", {}).get("values", []) if v is not None]
        asset_vals = [v for v in bs.get("Total Liabilities & Assets", {}).get("values", []) if v is not None]

        if nw_vals and asset_vals:
            latest_nw = nw_vals[-1]
            latest_assets = asset_vals[-1]
            if latest_assets > 0 and latest_nw > 0:
                if latest_nw > latest_assets * 1.05:
                    bs_status = "FAILED"
                    bs_passed = False
                    bs_detail = f"Anomalous equation: Reported Net Worth (₹{latest_nw:,.1f} Cr) exceeds Total Assets (₹{latest_assets:,.1f} Cr)."
                    penalties += 2.0
                    audit_flags.append("Balance Sheet Equation Discrepancy")
                else:
                    bs_status = "PASSED"
                    bs_passed = True
                    bs_detail = f"Consistent: Total Assets (₹{latest_assets:,.1f} Cr) covers Net Worth (₹{latest_nw:,.1f} Cr) and Liabilities."
            else:
                bs_status = "INSUFFICIENT_DATA"
                bs_passed = None
                bs_detail = "Reported asset or equity values are zero or negative; equation check inconclusive."
        else:
            bs_status = "INSUFFICIENT_DATA"
            bs_passed = None
            bs_detail = "Balance sheet data missing or incomplete; equation consistency not evaluated."

        checks.append({
            "id": "CHK_01_BS_EQUATION",
            "name": "Balance Sheet Arithmetic Consistency",
            "category": "Accounting Consistency",
            "status": bs_status,
            "passed": bs_passed,
            "severity": "CRITICAL" if bs_status == "FAILED" else ("INFO" if bs_status == "PASSED" else "WARNING"),
            "detail": bs_detail
        })

        # -------------------------------------------------------------
        # CHECK 2: Cash Flow Math Consistency (CFO - Capex vs FCF)
        # -------------------------------------------------------------
        cfo_vals = [v for v in cf.get("Cash from Operations (CFO)", {}).get("values", []) if v is not None]
        capex_vals = [v for v in cf.get("Capital Expenditure (Capex)", {}).get("values", []) if v is not None]
        fcf_vals = [v for v in cf.get("Free Cash Flow (FCF)", {}).get("values", []) if v is not None]

        if cfo_vals and capex_vals and fcf_vals:
            latest_cfo = cfo_vals[-1]
            latest_capex = abs(capex_vals[-1])
            latest_fcf = fcf_vals[-1]
            expected_fcf = latest_cfo - latest_capex
            diff = abs(latest_fcf - expected_fcf)
            if diff > 15.0 and abs(diff / (abs(latest_fcf) or 1.0)) > 0.08:
                cf_status = "FAILED"
                cf_passed = False
                cf_detail = f"Variance detected: Reported FCF is ₹{latest_fcf:,.1f} Cr vs Expected CFO - Capex of ₹{expected_fcf:,.1f} Cr."
                penalties += 1.5
                audit_flags.append("Free Cash Flow Reconciliation Variance")
            else:
                cf_status = "PASSED"
                cf_passed = True
                cf_detail = f"Reconciled: CFO (₹{latest_cfo:,.1f} Cr) - Capex (₹{latest_capex:,.1f} Cr) ≈ FCF (₹{latest_fcf:,.1f} Cr)."
        else:
            cf_status = "INSUFFICIENT_DATA"
            cf_passed = None
            cf_detail = "Cash flow statement lines (CFO, Capex, or FCF) missing; reconciliation not evaluated."

        checks.append({
            "id": "CHK_02_CF_RECONCILE",
            "name": "Cash Flow Arithmetic Consistency",
            "category": "Cash Flow Sanity",
            "status": cf_status,
            "passed": cf_passed,
            "severity": "HIGH" if cf_status == "FAILED" else ("INFO" if cf_status == "PASSED" else "WARNING"),
            "detail": cf_detail
        })

        # -------------------------------------------------------------
        # CHECK 3: Earnings Quality & Accrual Check (CFO vs PAT)
        # -------------------------------------------------------------
        pat_vals = [v for v in pnl.get("Net Profit (PAT)", {}).get("values", []) if v is not None]

        if pat_vals and cfo_vals:
            latest_pat = pat_vals[-1]
            latest_cfo = cfo_vals[-1]
            if latest_pat > 0:
                conv_ratio = (latest_cfo / latest_pat) * 100
                if latest_cfo < 0:
                    accrual_status = "FAILED"
                    accrual_passed = False
                    accrual_detail = f"Negative CFO Divergence: PAT is positive (₹{latest_pat:,.1f} Cr) but CFO is negative (₹{latest_cfo:,.1f} Cr)."
                    penalties += 2.5
                    audit_flags.append("Negative Operating Cash Flow Divergence")
                elif conv_ratio < 40:
                    accrual_status = "FAILED"
                    accrual_passed = False
                    accrual_detail = f"Low Cash Conversion: CFO / PAT is {conv_ratio:.1f}%, indicating heavy working capital absorption."
                    penalties += 1.5
                    audit_flags.append("Sub-40% Cash Flow Yield")
                else:
                    accrual_status = "PASSED"
                    accrual_passed = True
                    accrual_detail = f"Sound Cash Conversion: CFO covers {conv_ratio:.1f}% of reported Net Profit."
            else:
                accrual_status = "PASSED"
                accrual_passed = True
                accrual_detail = "Base period PAT is negative or zero; cash conversion ratio not stressed."
        else:
            accrual_status = "INSUFFICIENT_DATA"
            accrual_passed = None
            accrual_detail = "PAT or CFO history missing from provider; accrual conversion not evaluated."

        checks.append({
            "id": "CHK_03_ACCRUAL_STRESS",
            "name": "Operating Cash vs Net Profit Conversion",
            "category": "Earnings Quality",
            "status": accrual_status,
            "passed": accrual_passed,
            "severity": "HIGH" if accrual_status == "FAILED" else ("INFO" if accrual_status == "PASSED" else "WARNING"),
            "detail": accrual_detail
        })

        # -------------------------------------------------------------
        # CHECK 4: Topline to Bottomline Structural Hierarchy
        # Sales >= PAT under standard operations
        # -------------------------------------------------------------
        rev_vals = [v for v in pnl.get("Sales / Total Revenue", {}).get("values", []) if v is not None]

        if rev_vals and pat_vals:
            latest_rev = rev_vals[-1]
            latest_pat = pat_vals[-1]
            if latest_rev > 0 and latest_pat > latest_rev * 1.05:
                hier_status = "FAILED"
                hier_passed = False
                hier_detail = f"Hierarchy anomaly: Reported PAT (₹{latest_pat:,.1f} Cr) exceeds Total Revenue (₹{latest_rev:,.1f} Cr) (one-offs or reporting error)."
                penalties += 2.0
                audit_flags.append("Net Profit Exceeds Revenue")
            elif latest_rev > 0:
                hier_status = "PASSED"
                hier_passed = True
                hier_detail = f"Structural hierarchy consistent: Revenue ₹{latest_rev:,.1f} Cr → Net Profit ₹{latest_pat:,.1f} Cr."
            else:
                hier_status = "INSUFFICIENT_DATA"
                hier_passed = None
                hier_detail = "Reported revenue is zero or missing."
        else:
            hier_status = "INSUFFICIENT_DATA"
            hier_passed = None
            hier_detail = "Revenue or PAT time series missing; hierarchy not evaluated."

        checks.append({
            "id": "CHK_04_PNL_HIERARCHY",
            "name": "P&L Structural Hierarchy",
            "category": "Accounting Consistency",
            "status": hier_status,
            "passed": hier_passed,
            "severity": "MEDIUM" if hier_status == "FAILED" else ("INFO" if hier_status == "PASSED" else "WARNING"),
            "detail": hier_detail
        })

        # -------------------------------------------------------------
        # CHECK 5: Market Pricing & 52-Week Range Boundary Sanity
        # -------------------------------------------------------------
        cmp_price = live.get("current_price")
        hi_52 = live.get("high_52w")
        lo_52 = live.get("low_52w")

        if isinstance(cmp_price, (int, float)) and isinstance(hi_52, (int, float)) and isinstance(lo_52, (int, float)):
            if lo_52 > 0 and hi_52 >= lo_52:
                if cmp_price < lo_52 * 0.93 or cmp_price > hi_52 * 1.07:
                    market_status = "FAILED"
                    market_passed = False
                    market_detail = f"Price outlier: CMP ₹{cmp_price} falls outside 52W range [₹{lo_52} - ₹{hi_52}]."
                    penalties += 1.0
                    audit_flags.append("52W Price Boundary Outlier")
                else:
                    market_status = "PASSED"
                    market_passed = True
                    market_detail = f"Price action consistent: CMP ₹{cmp_price:,.2f} within 52W channel [₹{lo_52:,.2f} — ₹{hi_52:,.2f}]."
            else:
                market_status = "INSUFFICIENT_DATA"
                market_passed = None
                market_detail = "52-week high/low data invalid or zero."
        else:
            market_status = "INSUFFICIENT_DATA"
            market_passed = None
            market_detail = "Current market price or 52-week trading boundaries missing from provider."

        checks.append({
            "id": "CHK_05_MARKET_BOUNDS",
            "name": "Market Pricing & 52-Week Boundaries",
            "category": "Market Data Sanity",
            "status": market_status,
            "passed": market_passed,
            "severity": "MEDIUM" if market_status == "FAILED" else ("INFO" if market_status == "PASSED" else "WARNING"),
            "detail": market_detail
        })

        # -------------------------------------------------------------
        # CHECK 6: Reporting History Depth
        # -------------------------------------------------------------
        if years and len(years) >= 3:
            fresh_status = "PASSED"
            fresh_passed = True
            fresh_detail = f"Sufficient history present across {len(years)} fiscal periods ({', '.join(years)})."
        elif years and len(years) == 2:
            fresh_status = "PASSED"
            fresh_passed = True
            fresh_detail = f"Minimum history present: {len(years)} fiscal periods ({', '.join(years)})."
        elif years and len(years) < 2:
            fresh_status = "FAILED"
            fresh_passed = False
            fresh_detail = f"Insufficient history: only {len(years)} fiscal period(s) available; minimum 2 required."
            penalties += 2.0
            audit_flags.append("Limited Historical Continuity")
        else:
            fresh_status = "INSUFFICIENT_DATA"
            fresh_passed = None
            fresh_detail = "No historical fiscal periods provided in statement dataset."

        checks.append({
            "id": "CHK_06_REPORTING_DEPTH",
            "name": "Historical Reporting Depth",
            "category": "Data Freshness",
            "status": fresh_status,
            "passed": fresh_passed,
            "severity": "HIGH" if fresh_status == "FAILED" else ("INFO" if fresh_status == "PASSED" else "WARNING"),
            "detail": fresh_detail
        })

        # -------------------------------------------------------------
        # SYNTHESIS & REPORT IDENTIFIER (Not a cryptographic proof of authenticity)
        # -------------------------------------------------------------
        passed_count = sum(1 for c in checks if c["status"] == "PASSED")
        failed_count = sum(1 for c in checks if c["status"] == "FAILED")
        skipped_count = sum(1 for c in checks if c["status"] == "INSUFFICIENT_DATA")
        total_count = len(checks)
        evaluated_count = passed_count + failed_count

        # Compute consistency score based ONLY on evaluated checks
        if evaluated_count == 0:
            integrity_score = None
            status = "INSUFFICIENT DATA / NOT EVALUATED ⚪"
            badge_color = "#64748B"
            badge_bg = "#F8FAFC"
            badge_border = "#CBD5E1"
            summary_headline = "Required Source Data Absent — Consistency Checks Skipped"
            verdict_desc = "None of the 6 consistency checks could be evaluated because financial statements were empty or missing. Scoring cannot proceed on unverified data."
            can_score = False
        else:
            # Score proportional to evaluated checks
            base_score = 100.0
            integrity_score = max(0.0, min(100.0, base_score - penalties))

            if failed_count == 0 and skipped_count == 0:
                status = "CONSISTENCY CHECKS PASSED 🟢"
                badge_color = "#059669"
                badge_bg = "#ECFDF5"
                badge_border = "#A7F3D0"
                summary_headline = "All 6 Evaluated Mathematical Consistency Checks Reconciled"
                verdict_desc = "Statement inputs satisfy basic arithmetic identities and pricing bounds. Note: These are automated consistency tests, not independent statutory audits."
                can_score = True
            elif failed_count == 0 and skipped_count > 0:
                status = "PARTIALLY EVALUATED 🟡"
                badge_color = "#D97706"
                badge_bg = "#FFFBEB"
                badge_border = "#FDE68A"
                summary_headline = f"{passed_count} Checks Passed, {skipped_count} Skipped Due to Missing Data"
                verdict_desc = f"{passed_count} checks passed with no detected variances. {skipped_count} checks were skipped due to absent provider data."
                can_score = (evaluated_count >= 2)
            else:
                status = "CONSISTENCY VARIANCES FLAGGED 🔴"
                badge_color = "#DC2626"
                badge_bg = "#FEF2F2"
                badge_border = "#FECACA"
                summary_headline = f"{failed_count} Accounting / Pricing Inconsistencies Detected"
                verdict_desc = f"Engine detected variances: {', '.join(audit_flags)}. Mandatory risk deductions applied."
                can_score = True

        # Generate unique report run identifier (explicitly NOT proof of authenticity)
        hash_seed = f"{ticker_symbol}:{company_name}:{years}:{penalties}:{time.strftime('%Y%m%d%H%M')}"
        run_id = "CONSISTENCY-RUN-" + hashlib.sha256(hash_seed.encode()).hexdigest()[:10].upper()

        return {
            "agent_name": cls.AGENT_NAME,
            "agent_version": cls.AGENT_VERSION,
            "framework": cls.FRAMEWORK,
            "audit_hash": run_id,
            "run_id": run_id,
            "run_id_notice": "Run identifier is a local calculation hash for reference tracking. It does not certify third-party authenticity or tamper-proofing.",
            "ticker": ticker_symbol,
            "company_name": company_name,
            "timestamp": time.strftime("%d %b %Y, %H:%M:%S UTC", time.gmtime()),
            "status": status,
            "integrity_score": integrity_score,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "evaluated_count": evaluated_count,
            "total_count": total_count,
            "all_passed": (failed_count == 0 and skipped_count == 0),
            "can_score": can_score,
            "badge_color": badge_color,
            "badge_bg": badge_bg,
            "badge_border": badge_border,
            "summary_headline": summary_headline,
            "verdict_desc": verdict_desc,
            "checks": checks,
            "audit_flags": audit_flags,
            "integrity_penalty_applied": penalties,
            "elapsed_ms": round((time.time() - start_time) * 1000, 1)
        }


def render_sentinel_audit_certificate_html(report: Dict[str, Any]) -> str:
    """
    Renders the Data Consistency & Reconciliation Card for display in the UI.
    Clearly shows which checks ran, which passed, which failed, and which had insufficient data.
    """
    status = report.get("status", "NOT EVALUATED")
    score = report.get("integrity_score")
    score_display = f"{score:.1f}" if score is not None else "N/A"
    passed_cnt = report.get("passed_count", 0)
    failed_cnt = report.get("failed_count", 0)
    skipped_cnt = report.get("skipped_count", 0)
    total_cnt = report.get("total_count", 6)
    run_id = report.get("run_id") or report.get("audit_hash", "N/A")
    badge_color = report.get("badge_color", "#059669")
    badge_bg = report.get("badge_bg", "#ECFDF5")
    badge_border = report.get("badge_border", "#A7F3D0")
    headline = report.get("summary_headline", "")
    verdict = report.get("verdict_desc", "")
    checks = report.get("checks", [])

    check_cards = []
    for c in checks:
        chk_status = c.get("status", "UNKNOWN")
        if chk_status == "PASSED":
            c_icon = "✔"
            c_color = "#059669"
            c_bg = "#F0FDF4"
            c_border = "#BBF7D0"
            tag_label = "PASSED"
        elif chk_status == "FAILED":
            c_icon = "✖"
            c_color = "#DC2626"
            c_bg = "#FEF2F2"
            c_border = "#FECACA"
            tag_label = "VARIANCE"
        else:
            c_icon = "⚪"
            c_color = "#64748B"
            c_bg = "#F8FAFC"
            c_border = "#E2E8F0"
            tag_label = "INSUFFICIENT DATA"

        check_cards.append(
            f'<div style="background: {c_bg}; border: 1.5px solid {c_border}; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;">'
            f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
            f'<div style="font-size: 14.5px; font-weight: 800; color: #0F172A; display: flex; align-items: center; gap: 8px;">'
            f'<span style="color: {c_color}; font-weight: 900; font-size: 15px;">{c_icon}</span> {c.get("name")}'
            f'</div>'
            f'<span style="font-size: 11.5px; font-weight: 700; color: {c_color}; background: #FFFFFF; border: 1px solid {c_border}; padding: 2px 8px; border-radius: 9999px;">{tag_label}</span>'
            f'</div>'
            f'<div style="font-size: 13.5px; line-height: 1.5; color: #334155; margin-left: 23px;">{c.get("detail")}</div>'
            f'</div>'
        )

    return f"""
    <div style="background: #FFFFFF; border: 2px solid {badge_border}; border-radius: 12px; padding: 22px 24px; margin-top: 18px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
      
      <!-- Top Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 14px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px;">🔍</span>
            <span style="font-size: 18.5px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px;">Data Consistency & Reconciliation Trail</span>
            <span style="background: {badge_bg}; color: {badge_color}; border: 1.5px solid {badge_border}; font-size: 12.5px; font-weight: 800; padding: 3px 10px; border-radius: 9999px;">{status}</span>
          </div>
          <div style="font-size: 13.5px; color: #64748B; margin-top: 5px;">
            Deterministic Arithmetic & Boundary Sanity Checks • Internal Data Quality Engine
          </div>
        </div>
        
        <div style="text-align: right;">
          <div style="font-size: 12px; font-weight: 700; color: #64748B; text-transform: uppercase;">Consistency Index</div>
          <div style="font-size: 28px; font-weight: 900; color: {badge_color}; font-family: 'JetBrains Mono', monospace; line-height: 1.2;">
            {score_display}<span style="font-size: 16px; font-weight: 700; color: #64748B;">/100</span>
          </div>
          <div style="font-size: 11px; font-weight: 600; color: #94A3B8; font-family: 'JetBrains Mono', monospace;">ID: {run_id}</div>
        </div>
      </div>

      <!-- Verdict Banner -->
      <div style="background: {badge_bg}; border-left: 4.5px solid {badge_color}; border-radius: 0 8px 8px 0; padding: 14px 18px; margin-top: 14px; margin-bottom: 16px;">
        <div style="font-size: 15px; font-weight: 800; color: {badge_color};">{headline}</div>
        <div style="font-size: 13.5px; line-height: 1.55; color: #1E293B; margin-top: 4px;">{verdict}</div>
      </div>

      <!-- Scope Notice -->
      <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13.5px; line-height: 1.5; color: #475569;">
        ℹ️ <strong>Scope Disclosure:</strong> These automated checks evaluate basic mathematical identities (e.g. Assets ≥ Equity, CFO - Capex ≈ FCF) and pricing sanity within available third-party data feeds. They do NOT constitute an independent statutory audit, certification of filing authenticity, or guarantee against accounting fraud.
      </div>

      <!-- Checklist Summary -->
      <div style="font-size: 14px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
        <span>6-Point Consistency Evaluation</span>
        <span style="font-size: 12.5px; font-weight: 700; color: {badge_color};">
          {passed_cnt} Passed • {failed_cnt} Flagged • {skipped_cnt} Insufficient Data
        </span>
      </div>
      
      <div style="display: grid; grid-template-columns: 1fr; gap: 2px;">
        {"".join(check_cards)}
      </div>

    </div>
    """
