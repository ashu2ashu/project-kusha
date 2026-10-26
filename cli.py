"""
cli.py
StockSage Institutional Financial Terminal — Command-Line Interface (CLI)
Enables running full 8-pillar IDEX-7.5SC evaluations, multi-year financial statements,
and forensic stress tests directly inside your terminal shell.
"""

import argparse
import logging
import os
import sys
import warnings

# Suppress library deprecation and non-critical runtime notices in CLI mode
warnings.filterwarnings('ignore')
logging.getLogger("streamlit").setLevel(logging.ERROR)

from dotenv import load_dotenv

load_dotenv(override=True)

import analyzer
import nifty_universe
import financial_trends
import data_integrity_agent
import forensic_risk_engine


# ANSI Terminal Colors
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def print_banner():
    print(f"{BOLD}{GREEN}╔══════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{GREEN}║               STOCKSAGE INSTITUTIONAL TERMINAL • ASHU ELITE EDITION             ║{RESET}")
    print(f"{BOLD}{GREEN}║        IDEX-7.5SC Hybrid Pro Framework • Terminal Command-Line Interface         ║{RESET}")
    print(f"{BOLD}{GREEN}╚══════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")


def run_cli_analysis(ticker: str, is_demo: bool = False, model: str = "gemini-3.5-flash"):
    sym = ticker.upper().strip()
    company_info = nifty_universe.find_company_info(sym)
    company_name = company_info.get("name") or sym
    sector = company_info.get("sector") or "Diversified"

    print(f"{CYAN}▶ Fetching market quotes and audited statements for {BOLD}{sym}{RESET}{CYAN} ({company_name})...{RESET}")

    # 1. Fetch live quotes & financial statements
    live_data = nifty_universe.fetch_live_market_data(sym) or {}
    fin_statements = financial_trends.fetch_financial_statements(sym)
    if "error" in fin_statements:
        print(f"{YELLOW}⚠ Financial statement notice: {fin_statements['error']}{RESET}")
        fin_statements = {}

    cagr = fin_statements.get("cagr", {})

    # Display Market Header
    cmp_price = live_data.get("current_price") or 0.0
    h52 = live_data.get("high_52w") or 0.0
    l52 = live_data.get("low_52w") or 0.0
    pe = live_data.get("pe_ratio") or "N/A"
    mc_cr = live_data.get("market_cap_cr") or 0.0
    roce = cagr.get("latest_roce") or "N/A"
    roic = cagr.get("latest_roic") or "N/A"
    de = cagr.get("latest_de") or "N/A"

    print(f"\n{BOLD}┌─ MARKET SNAPSHOT ──────────────────────────────────────────────────────────────┐{RESET}")
    print(f"│ {BOLD}{company_name:<40}{RESET} │ Ticker: {BOLD}{sym:<10}{RESET} Sector: {sector:<15} │")
    print(f"│ CMP: {BOLD}₹{cmp_price:>10,.2f}{RESET}  │ 52W Range: ₹{l52:,.0f} - ₹{h52:,.0f}   │ MCap: ₹{mc_cr:>10,.0f} Cr       │")
    print(f"│ P/E: {str(pe):>8}      │ ROCE: {str(roce):>6}%       ROIC: {str(roic):>6}%     D/E: {str(de):>5}x          │")
    print(f"{BOLD}└────────────────────────────────────────────────────────────────────────────────┘{RESET}")

    # 2. Run Forensic Risk Engine Audit
    print(f"\n{CYAN}▶ Running 8-Pillar Forensic Stress Test Radar...{RESET}")
    forensic_rep = forensic_risk_engine.ForensicRiskEngine.audit_company_forensics(
        ticker_symbol=sym,
        company_name=company_name,
        sector=sector,
        financial_statements=fin_statements,
        live_market_data=live_data
    )

    fqi = forensic_rep.get("fqi_score", 100.0)
    v_badge = forensic_rep.get("verdict_badge", "PRISTINE")
    v_color = GREEN if v_badge == "PRISTINE" else (YELLOW if v_badge == "MONITOR" else RED)

    print(f"{BOLD}┌─ FORENSIC DUE DILIGENCE AUDIT ─────────────────────────────────────────────────┐{RESET}")
    print(f"│ Forensic Quality Index (FQI): {v_color}{BOLD}{fqi:>5.1f} / 100{RESET} │ Verdict: {v_color}{BOLD}{v_badge:<25}{RESET} │")
    print(f"├────────────────────────────────────────────────────────────────────────────────┤")
    for chk in forensic_rep.get("checks", []):
        st = chk.get("status", "N/A")
        st_color = GREEN if st == "PASS" else (YELLOW if st == "MONITOR" else RED)
        title = chk.get("title", "")[:35]
        metric = str(chk.get("metric", "N/A"))[:15]
        bench = str(chk.get("benchmark", ""))[:18]
        print(f"│ {title:<36} │ {metric:<16} │ {bench:<18} │ {st_color}{st:<8}{RESET} │")
    print(f"{BOLD}└────────────────────────────────────────────────────────────────────────────────┘{RESET}")

    # 3. Run Data Integrity Sentinel
    sentinel_rep = data_integrity_agent.DataIntegritySentinel.audit_and_certify(
        ticker_symbol=sym,
        company_name=company_name,
        financial_statements=fin_statements,
        live_market_data=live_data
    )

    # 4. Run IDEX-7.5SC Model Analysis
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if is_demo or not api_key:
        print(f"\n{YELLOW}▶ Running IDEX-7.5SC Framework in Deterministic Demo Mode (Synthetic Sample)...{RESET}")
        idex_res = analyzer.get_demo_analysis(
            company_name=company_name,
            sector=sector,
            live_data=live_data,
            sentinel_report=sentinel_rep,
            forensic_report=forensic_rep
        )
    else:
        print(f"\n{CYAN}▶ Running Gemini AI Grounded Institutional Assessment ({model})...{RESET}")
        try:
            idex_res = analyzer.analyze_document_with_gemini(
                company_name=company_name,
                sector=sector,
                api_key=api_key,
                live_data=live_data,
                selected_model=model,
                sentinel_report=sentinel_rep,
                forensic_report=forensic_rep
            )
        except Exception as e:
            print(f"{YELLOW}⚠ Gemini API live query error: {e}. Falling back to deterministic demo scorecard.{RESET}")
            idex_res = analyzer.get_demo_analysis(
                company_name=company_name,
                sector=sector,
                live_data=live_data,
                sentinel_report=sentinel_rep,
                forensic_report=forensic_rep
            )

    # Display 8 Canonical Pillars
    print(f"\n{BOLD}┌─ 8 CANONICAL PILLARS SCORECARD (IDEX-7.5SC) ──────────────────────────────────┐{RESET}")
    print(f"│ ID  Pillar Name                                Score / Max     Weight   Status │")
    print(f"├────────────────────────────────────────────────────────────────────────────────┤")
    for p in idex_res.get("pillars", []):
        p_id = p.get("id", 1)
        p_name = p.get("name", "")[:38]
        p_score = p.get("score", 0.0)
        p_max = p.get("max_score", 20.0)
        pct = (p_score / p_max) * 100.0 if p_max > 0 else 0
        p_col = GREEN if pct >= 80 else (YELLOW if pct >= 50 else RED)
        status = "Pristine" if pct >= 80 else ("Moderate" if pct >= 50 else "Fragile")
        print(f"│ P{p_id:<2} {p_name:<39} │ {p_col}{BOLD}{p_score:>5.1f}{RESET} / {p_max:<5.1f} │ {pct:>5.1f}%  │ {p_col}{status:<8}{RESET} │")
    print(f"{BOLD}└────────────────────────────────────────────────────────────────────────────────┘{RESET}")

    # Display Score Bridge & Institutional Verdict
    core_score = idex_res.get("core_score", 0.0)
    total_pen = idex_res.get("total_penalties", 0.0)
    total_bon = idex_res.get("bonuses_breakdown", {}).get("total_bonus_applied", 0.0)
    final_score = idex_res.get("final_score", 0.0)
    verdict = idex_res.get("verdict", "N/A")
    pos_sizing = idex_res.get("position_sizing", "0%")
    guardrail = idex_res.get("guardrail_tag", "GOV-CLEAN 🟢")
    pio_trig = idex_res.get("pio_triggered", False)

    print(f"\n{BOLD}┌─ INSTITUTIONAL SCORE BRIDGE & VERDICT ─────────────────────────────────────────┐{RESET}")
    print(f"│ Core Quality: {BOLD}{core_score:>5.1f}{RESET} │ Penalties: {RED}{total_pen:>5.1f} pts{RESET} │ Bonuses: {MAGENTA}+{total_bon:>4.1f} pts{RESET} (Max 10.0 pts)  │")
    if pio_trig:
        print(f"│ {RED}{BOLD}🚨 MANDATORY PROMOTER INTEGRITY OVERRIDE (PIO) TRIGGERED: Cap ≤ 49.0 pts{RESET}       │")
    print(f"├────────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ {BOLD}FINAL IDEX SCORE : {GREEN if final_score >= 75 else (YELLOW if final_score >= 50 else RED)}{BOLD}{final_score:>5.1f} / 100.0{RESET}                                                │")
    print(f"│ Guardrail Tag    : {guardrail:<58} │")
    print(f"│ Verdict Band     : {BOLD}{verdict[:58]:<58}{RESET} │")
    print(f"│ Allocation Sizing: {BOLD}{pos_sizing:<58}{RESET} │")
    print(f"{BOLD}└────────────────────────────────────────────────────────────────────────────────┘{RESET}")
    print(f"\n{DIM}Run complete. For the interactive visual dashboard, run: streamlit run app.py{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="StockSage Institutional Financial Terminal CLI")
    parser.add_argument("ticker", nargs="?", default="ABB", help="NSE/BSE ticker symbol (e.g. ABB, RELIANCE, TCS, INFY)")
    parser.add_argument("--demo", action="store_true", help="Run in synthetic demonstration mode")
    parser.add_argument("--model", default="gemini-3.5-flash", help="Gemini model name")
    args = parser.parse_args()

    print_banner()
    run_cli_analysis(args.ticker, is_demo=args.demo, model=args.model)


if __name__ == "__main__":
    main()
