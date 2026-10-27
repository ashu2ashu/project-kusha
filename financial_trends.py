"""
financial_trends.py
Multi-Year Historical Financial Statements, CAGR Growth Engine & Visualizer
Provides institutional Screener.in-grade financial analysis for Indian listed companies.
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_financial_statements(ticker_symbol: str) -> Dict[str, Any]:
    """
    Fetches annual and quarterly financial statements from yfinance for an Indian ticker,
    converts figures to ₹ Crores, and computes CAGR and forensic conversion ratios.
    """
    sym = ticker_symbol if ticker_symbol.endswith((".NS", ".BO")) or ticker_symbol.startswith("^") else f"{ticker_symbol}.NS"
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t = yf.Ticker(sym)
            fin = t.financials
            bs = t.balance_sheet
            cf = t.cashflow
            q_fin = t.quarterly_financials

            # Graceful BSE (.BO) fallback if NSE (.NS) yields empty statements
            if (fin is None or fin.empty) and sym.endswith(".NS"):
                alt_sym = sym.replace(".NS", ".BO")
                alt_t = yf.Ticker(alt_sym)
                alt_fin = alt_t.financials
                if alt_fin is not None and not alt_fin.empty:
                    sym = alt_sym
                    t = alt_t
                    fin = alt_fin
                    bs = alt_t.balance_sheet
                    cf = alt_t.cashflow
                    q_fin = alt_t.quarterly_financials
    except Exception as e:
        return {"error": f"Failed to fetch statements for {sym}: {str(e)}"}

    if fin is None or fin.empty:
        return {"error": f"No annual financial statements found for {sym}."}

    # Identify valid annual periods with recorded revenue
    valid_cols = [
        c for c in sorted(fin.columns)
        if 'Total Revenue' in fin.index and pd.notna(fin.loc['Total Revenue', c]) and fin.loc['Total Revenue', c] > 0
    ]
    if len(valid_cols) < 2:
        valid_cols = sorted(fin.columns)

    year_labels = [c.strftime("Mar %Y") if c.month in [3, 4] else c.strftime("%b %Y") for c in valid_cols]

    def get_val(df, candidates, col, scale=1e7):
        if df is None or df.empty:
            return None
        for cand in candidates:
            if cand in df.index and col in df.columns:
                val = df.loc[cand, col]
                if pd.notna(val):
                    return float(val) / scale
        return None

    # 1. P&L Statement (Annual)
    pnl_keys = [
        ("Sales / Total Revenue", ["Total Revenue", "Operating Revenue"], True),
        ("Raw Materials & Direct Costs", ["Cost Of Revenue"], False),
        ("Operating & Staff Expenses", ["Operating Expense", "Other Operating Expenses"], False),
        ("Operating Profit / Net Interest Income", ["Normalized EBITDA", "EBITDA", "Operating Income", "Net Interest Income", "Pretax Income"], True),
        ("Other Income", ["Other Non Operating Income Expenses", "Other Income Expense"], False),
        ("Depreciation & Amort.", ["Reconciled Depreciation", "Depreciation And Amortization", "Depreciation Amortization Depletion"], False),
        ("Interest & Finance Costs", ["Interest Expense", "Interest Expense Non Operating"], False),
        ("Profit Before Tax (PBT)", ["Pretax Income"], True),
        ("Tax Provision", ["Tax Provision"], False),
        ("Net Profit (PAT)", ["Net Income", "Net Income Common Stockholders"], True),
        ("Basic EPS (₹)", ["Basic EPS", "Diluted EPS"], False, 1.0)
    ]

    extracted_pnl = {}
    for item in pnl_keys:
        label = item[0]
        cands = item[1]
        is_highlight = item[2]
        scale = item[3] if len(item) > 3 else 1e7
        row_vals = [round(v, 1) if v is not None else None for v in [get_val(fin, cands, c, scale) for c in valid_cols]]
        extracted_pnl[label] = {
            "values": row_vals,
            "highlight": is_highlight,
            "is_eps": (scale == 1.0)
        }

    rev_vals = extracted_pnl["Sales / Total Revenue"]["values"]
    op_key = "Operating Profit / Net Interest Income" if "Operating Profit / Net Interest Income" in extracted_pnl else "Operating Profit (EBITDA)"
    ebitda_vals = extracted_pnl[op_key]["values"]
    pat_vals = extracted_pnl["Net Profit (PAT)"]["values"]

    opm_vals = [round((e / r * 100), 1) if (e is not None and r is not None and r > 0) else None for e, r in zip(ebitda_vals, rev_vals)]
    npm_vals = [round((p / r * 100), 1) if (p is not None and r is not None and r > 0) else None for p, r in zip(pat_vals, rev_vals)]
    extracted_pnl["OPM %"] = {"values": opm_vals, "highlight": False, "is_pct": True}
    extracted_pnl["NPM %"] = {"values": npm_vals, "highlight": False, "is_pct": True}

    # 2. Balance Sheet (Annual)
    bs_cols = [c for c in sorted(bs.columns) if c in valid_cols or c in fin.columns] if bs is not None and not bs.empty else []
    if not bs_cols and bs is not None and not bs.empty:
        bs_cols = sorted(bs.columns)[-len(valid_cols):]
    bs_years = [c.strftime("Mar %Y") if c.month in [3, 4] else c.strftime("%b %Y") for c in bs_cols]

    bs_keys = [
        ("Equity Share Capital", ["Common Stock", "Capital Stock"], False),
        ("Reserves & Surplus", ["Retained Earnings", "Other Equity Gross"], False),
        ("Total Net Worth / Equity", ["Stockholders Equity", "Common Stock Equity"], True),
        ("Total Borrowings / Debt", ["Total Debt", "Long Term Debt And Capital Lease Obligation"], True),
        ("Other Liabilities", ["Other Non Current Liabilities", "Other Current Liabilities"], False),
        ("Total Liabilities & Assets", ["Total Assets"], True),
        ("Fixed Assets (Net PPE)", ["Net PPE", "Gross PPE"], False),
        ("Capital WIP", ["Construction In Progress"], False),
        ("Investments", ["Investments And Advances", "Other Investments"], False),
        ("Trade Receivables", ["Accounts Receivable", "Gross Accounts Receivable", "Receivables"], False),
        ("Current & Other Assets", ["Current Assets", "Other Current Assets"], False),
        ("Current Liabilities", ["Current Liabilities", "Other Current Liabilities"], False),
        ("Cash & Equivalents", ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"], True)
    ]

    extracted_bs = {}
    for label, cands, is_highlight in bs_keys:
        row_vals = [round(v, 1) if v is not None else None for v in [get_val(bs, cands, c, 1e7) for c in bs_cols]]
        extracted_bs[label] = {
            "values": row_vals,
            "highlight": is_highlight
        }

    # 3. Cash Flow Statement (Annual)
    cf_cols = [c for c in sorted(cf.columns) if c in valid_cols] if cf is not None and not cf.empty else []
    if not cf_cols and cf is not None and not cf.empty:
        cf_cols = sorted(cf.columns)[-len(valid_cols):]
    cf_years = [c.strftime("Mar %Y") if c.month in [3, 4] else c.strftime("%b %Y") for c in cf_cols]

    cf_keys = [
        ("Cash from Operations (CFO)", ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"], True),
        ("Capital Expenditure (Capex)", ["Capital Expenditure", "Net PPE Purchase And Sale"], True),
        ("Free Cash Flow (FCF)", ["Free Cash Flow"], True),
        ("Cash from Investing (CFI)", ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"], False),
        ("Cash from Financing (CFF)", ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"], False),
        ("Net Cash Inflow / Outflow", ["Changes In Cash", "End Cash Position"], True)
    ]

    extracted_cf = {}
    for label, cands, is_highlight in cf_keys:
        row_vals = [round(v, 1) if v is not None else None for v in [get_val(cf, cands, c, 1e7) for c in cf_cols]]
        if label == "Capital Expenditure (Capex)":
            row_vals = [-abs(x) if x is not None else None for x in row_vals]
        extracted_cf[label] = {
            "values": row_vals,
            "highlight": is_highlight
        }

    # Free Cash Flow reconciliation without fabricating missing values
    cfo_vals = extracted_cf["Cash from Operations (CFO)"]["values"]
    capex_vals = extracted_cf["Capital Expenditure (Capex)"]["values"]
    fcf_vals = extracted_cf["Free Cash Flow (FCF)"]["values"]
    reconciled_fcf = []
    for fcf, cfo, capex in zip(fcf_vals, cfo_vals, capex_vals):
        if fcf is not None:
            reconciled_fcf.append(fcf)
        elif cfo is not None and capex is not None:
            reconciled_fcf.append(round(cfo + capex, 1))
        else:
            reconciled_fcf.append(None)
    extracted_cf["Free Cash Flow (FCF)"]["values"] = reconciled_fcf

    # Reconcile CFO to PAT by exact matching fiscal dates to prevent period drift
    pat_by_date = {c: p for c, p in zip(valid_cols, pat_vals)}
    cfo_to_pat = []
    for c, cfo in zip(cf_cols, cfo_vals):
        pat_matched = pat_by_date.get(c)
        if cfo is not None and pat_matched is not None and pat_matched > 0:
            cfo_to_pat.append(round((cfo / pat_matched) * 100, 1))
        else:
            cfo_to_pat.append(None)
    extracted_cf["CFO / PAT Conversion %"] = {"values": cfo_to_pat, "highlight": False, "is_pct": True}

    # 4. Quarterly Trends (Last 5 Quarters)
    extracted_quarterly = {}
    q_years = []
    if q_fin is not None and not q_fin.empty:
        valid_q_cols = [c for c in sorted(q_fin.columns) if 'Total Revenue' in q_fin.index and pd.notna(q_fin.loc['Total Revenue', c])][-5:]
        q_years = [c.strftime("%b %Y") for c in valid_q_cols]
        q_keys = [
            ("Sales / Revenue", ["Total Revenue", "Operating Revenue"], True),
            ("Operating Profit", ["Normalized EBITDA", "EBITDA", "Operating Income"], True),
            ("Net Profit (PAT)", ["Net Income", "Net Income Common Stockholders"], True)
        ]
        for label, cands, is_hl in q_keys:
            row_vals = [round(v, 1) if v is not None else None for v in [get_val(q_fin, cands, c, 1e7) for c in valid_q_cols]]
            extracted_quarterly[label] = {"values": row_vals, "highlight": is_hl}

        q_rev = extracted_quarterly.get("Sales / Revenue", {}).get("values", [])
        q_op = extracted_quarterly.get("Operating Profit", {}).get("values", [])
        q_opm = [round((op / rv * 100), 1) if (op is not None and rv is not None and rv > 0) else None for op, rv in zip(q_op, q_rev)]
        extracted_quarterly["OPM %"] = {"values": q_opm, "highlight": False, "is_pct": True}

    # 5. Compound Growth Rates (CAGR) and Key Institutional Metas
    def calc_cagr(start_v, end_v, periods):
        if start_v is not None and end_v is not None and start_v > 0 and end_v > 0 and periods > 0:
            return round(((end_v / start_v) ** (1.0 / periods) - 1.0) * 100, 1)
        return None

    n_years = len(valid_cols) - 1
    sales_cagr = calc_cagr(rev_vals[0], rev_vals[-1], n_years) if n_years >= 2 and rev_vals else None
    pat_cagr = calc_cagr(pat_vals[0], pat_vals[-1], n_years) if n_years >= 2 and pat_vals else None
    ebitda_cagr = calc_cagr(ebitda_vals[0], ebitda_vals[-1], n_years) if n_years >= 2 and ebitda_vals else None

    # Latest YoY Growth
    sales_yoy = round(((rev_vals[-1] - rev_vals[-2]) / abs(rev_vals[-2])) * 100, 1) if len(rev_vals) >= 2 and rev_vals[-1] is not None and rev_vals[-2] is not None and rev_vals[-2] > 0 else None
    pat_yoy = round(((pat_vals[-1] - pat_vals[-2]) / abs(pat_vals[-2])) * 100, 1) if len(pat_vals) >= 2 and pat_vals[-1] is not None and pat_vals[-2] is not None and pat_vals[-2] > 0 else None
    ebitda_yoy = round(((ebitda_vals[-1] - ebitda_vals[-2]) / abs(ebitda_vals[-2])) * 100, 1) if len(ebitda_vals) >= 2 and ebitda_vals[-1] is not None and ebitda_vals[-2] is not None and ebitda_vals[-2] > 0 else None

    valid_conversions = [x for x in cfo_to_pat if x is not None and x > 0]
    avg_cfo_pat = round(float(np.mean(valid_conversions)), 1) if valid_conversions else None

    nw_vals = extracted_bs.get("Total Net Worth / Equity", {}).get("values", [])
    latest_roe = round((pat_vals[-1] / nw_vals[-1] * 100), 1) if nw_vals and pat_vals and nw_vals[-1] is not None and pat_vals[-1] is not None and nw_vals[-1] > 0 else None

    debt_vals = extracted_bs.get("Total Borrowings / Debt", {}).get("values", [])
    latest_de = round((debt_vals[-1] / nw_vals[-1]), 2) if nw_vals and debt_vals and nw_vals[-1] is not None and debt_vals[-1] is not None and nw_vals[-1] > 0 else None

    # Calculate ROCE (Return on Capital Employed) = EBIT / Capital Employed * 100
    ebit_last = ebitda_vals[-1] if (ebitda_vals and ebitda_vals[-1] is not None) else None
    nw_last = nw_vals[-1] if (nw_vals and nw_vals[-1] is not None) else None
    debt_last = debt_vals[-1] if (debt_vals and debt_vals[-1] is not None) else 0.0
    cap_emp = (nw_last + debt_last) if (nw_last is not None and nw_last > 0) else None
    latest_roce = round((ebit_last / cap_emp * 100), 2) if (ebit_last is not None and cap_emp is not None and cap_emp > 0) else None

    # Calculate ROIC (Return on Invested Capital) = NOPAT / Invested Capital * 100
    cash_vals = extracted_bs.get("Cash & Equivalents", {}).get("values", [])
    cash_last = cash_vals[-1] if (cash_vals and cash_vals[-1] is not None) else 0.0
    inv_cap = max(1.0, cap_emp - cash_last) if cap_emp is not None else None
    pbt_vals = extracted_pnl.get("Profit Before Tax (PBT)", {}).get("values", [])
    tax_vals = extracted_pnl.get("Tax Provision", {}).get("values", [])
    pbt_last = pbt_vals[-1] if (pbt_vals and pbt_vals[-1] is not None) else None
    tax_last = tax_vals[-1] if (tax_vals and tax_vals[-1] is not None) else None
    eff_tax_rate = (tax_last / pbt_last) if (pbt_last and tax_last and pbt_last > 0 and 0 <= tax_last <= pbt_last) else 0.25
    nopat = (ebit_last * (1.0 - eff_tax_rate)) if ebit_last is not None else None
    latest_roic = round((nopat / inv_cap * 100), 2) if (nopat is not None and inv_cap is not None and inv_cap > 0) else None

    # Interest Coverage = EBIT / Interest Expense
    int_vals = extracted_pnl.get("Interest & Finance Costs", {}).get("values", [])
    int_last = int_vals[-1] if (int_vals and int_vals[-1] is not None) else None
    if ebit_last is not None and int_last is not None and int_last > 0:
        latest_int_coverage = round(ebit_last / int_last, 2)
    elif ebit_last is not None and ebit_last > 0 and (debt_last is None or debt_last < 50.0):
        latest_int_coverage = 99.0
    else:
        latest_int_coverage = None

    # Asset Turnover = Total Revenue / Total Assets
    assets_vals = extracted_bs.get("Total Liabilities & Assets", {}).get("values", [])
    asset_last = assets_vals[-1] if (assets_vals and assets_vals[-1] is not None) else None
    rev_last = rev_vals[-1] if (rev_vals and rev_vals[-1] is not None) else None
    latest_asset_turnover = round(rev_last / asset_last, 2) if (rev_last and asset_last and asset_last > 0) else None

    # Current Ratio = Current Assets / Current Liabilities
    ca_vals = extracted_bs.get("Current & Other Assets", {}).get("values", [])
    cl_vals = extracted_bs.get("Current Liabilities", {}).get("values", [])
    ca_last = ca_vals[-1] if (ca_vals and ca_vals[-1] is not None) else None
    cl_last = cl_vals[-1] if (cl_vals and cl_vals[-1] is not None) else None
    latest_current_ratio = round(ca_last / cl_last, 2) if (ca_last and cl_last and cl_last > 0) else None

    # CROIC = Free Cash Flow / Invested Capital * 100
    fcf_vals = extracted_cf.get("Free Cash Flow (FCF)", {}).get("values", [])
    fcf_last = fcf_vals[-1] if (fcf_vals and fcf_vals[-1] is not None) else None
    latest_croic = round((fcf_last / inv_cap * 100), 2) if (fcf_last is not None and inv_cap is not None and inv_cap > 0) else None

    # Receivables & DSO = Trade Receivables / Revenue * 365
    rec_vals = extracted_bs.get("Trade Receivables", {}).get("values", [])
    rec_last = rec_vals[-1] if (rec_vals and rec_vals[-1] is not None) else None
    if rec_last is not None and rev_last is not None and rev_last > 0:
        latest_dso = round((rec_last / rev_last) * 365, 0)
        latest_rec_to_sales = round((rec_last / rev_last) * 100, 1)
    else:
        latest_dso = None
        latest_rec_to_sales = None

    fetch_time = datetime.now(timezone.utc)
    return {
        "symbol": sym,
        "years": year_labels,
        "bs_years": bs_years,
        "cf_years": cf_years,
        "q_years": q_years,
        "pnl": extracted_pnl,
        "bs": extracted_bs,
        "cf": extracted_cf,
        "quarterly": extracted_quarterly,
        "cagr": {
            "sales_cagr": sales_cagr,
            "sales_yoy": sales_yoy,
            "pat_cagr": pat_cagr,
            "pat_yoy": pat_yoy,
            "ebitda_cagr": ebitda_cagr,
            "ebitda_yoy": ebitda_yoy,
            "avg_cfo_pat": avg_cfo_pat,
            "latest_roe": latest_roe,
            "latest_de": latest_de,
            "latest_roce": latest_roce,
            "latest_roic": latest_roic,
            "latest_croic": latest_croic,
            "latest_dso": latest_dso,
            "latest_rec_to_sales": latest_rec_to_sales,
            "latest_int_coverage": latest_int_coverage,
            "latest_asset_turnover": latest_asset_turnover,
            "latest_current_ratio": latest_current_ratio,
            "n_years": n_years,
            "latest_opm": opm_vals[-1] if (opm_vals and opm_vals[-1] is not None) else None,
            "opm_expansion": round(opm_vals[-1] - opm_vals[0], 1) if len(opm_vals) >= 2 and opm_vals[-1] is not None and opm_vals[0] is not None else None
        },
        "data_provider": "Yahoo Finance (unverified third-party dataset / delayed)",
        "source_disclaimer": "Historical statements retrieved from Yahoo Finance. Not official statutory filings or SEBI disclosures.",
        "fetched_at": fetch_time.isoformat()
    }


def build_revenue_profit_chart(fin_data: Dict[str, Any], company_name: str) -> go.Figure:
    """Creates a dual-axis revenue, profit, and margin expansion chart."""
    years = fin_data.get("years", [])
    pnl = fin_data.get("pnl", {})
    rev = pnl.get("Sales / Total Revenue", {}).get("values", [])
    pat = pnl.get("Net Profit (PAT)", {}).get("values", [])
    opm = pnl.get("OPM %", {}).get("values", [])
    npm = pnl.get("NPM %", {}).get("values", [])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar traces: Sales & PAT
    fig.add_trace(
        go.Bar(
            x=years,
            y=rev,
            name="Sales (₹ Cr)",
            marker_color="#059669",
            opacity=0.90,
            hovertemplate="Sales: ₹%{y:,.0f} Cr<extra></extra>"
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=years,
            y=pat,
            name="Net Profit (₹ Cr)",
            marker_color="#2563EB",
            opacity=0.92,
            hovertemplate="PAT: ₹%{y:,.0f} Cr<extra></extra>"
        ),
        secondary_y=False
    )

    # Line traces: Margins on secondary axis
    if any(x != 0 for x in opm):
        fig.add_trace(
            go.Scatter(
                x=years,
                y=opm,
                name="OPM %",
                mode="lines+markers",
                line=dict(color="#D97706", width=2.8),
                marker=dict(size=7, color="#D97706"),
                hovertemplate="OPM: %{y:.1f}%<extra></extra>"
            ),
            secondary_y=True
        )
    if any(x != 0 for x in npm):
        fig.add_trace(
            go.Scatter(
                x=years,
                y=npm,
                name="NPM %",
                mode="lines+markers",
                line=dict(color="#7C3AED", width=2.2, dash="dot"),
                marker=dict(size=6, color="#7C3AED"),
                hovertemplate="NPM: %{y:.1f}%<extra></extra>"
            ),
            secondary_y=True
        )

    fig.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#0F172A", family="Inter, sans-serif")
        ),
        barmode="group",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_yaxes(
        title_text="Amount (₹ Crores)",
        secondary_y=False,
        gridcolor="#F1F5F9",
        tickfont=dict(size=11, color="#64748B", family="JetBrains Mono, monospace")
    )
    fig.update_yaxes(
        title_text="Margin (%)",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(size=11, color="#64748B", family="JetBrains Mono, monospace")
    )
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11, color="#64748B"))
    return fig


def build_cashflow_health_chart(fin_data: Dict[str, Any], company_name: str) -> go.Figure:
    """Creates a forensic cash flow chart: CFO vs Capex vs FCF with PAT benchmark."""
    cf_years = fin_data.get("cf_years", [])
    cf = fin_data.get("cf", {})
    pnl = fin_data.get("pnl", {})

    cfo = cf.get("Cash from Operations (CFO)", {}).get("values", [])
    capex = cf.get("Capital Expenditure (Capex)", {}).get("values", [])
    fcf = cf.get("Free Cash Flow (FCF)", {}).get("values", [])
    pat = pnl.get("Net Profit (PAT)", {}).get("values", [])[-len(cf_years):]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=cf_years,
            y=cfo,
            name="Operating Cash Flow (CFO)",
            marker_color="#059669",
            hovertemplate="CFO: ₹%{y:,.0f} Cr<extra></extra>"
        )
    )
    fig.add_trace(
        go.Bar(
            x=cf_years,
            y=capex,
            name="Capex",
            marker_color="#DC2626",
            hovertemplate="Capex: ₹%{y:,.0f} Cr<extra></extra>"
        )
    )
    fig.add_trace(
        go.Bar(
            x=cf_years,
            y=fcf,
            name="Free Cash Flow (FCF)",
            marker_color="#2563EB",
            hovertemplate="FCF: ₹%{y:,.0f} Cr<extra></extra>"
        )
    )

    if pat:
        fig.add_trace(
            go.Scatter(
                x=cf_years,
                y=pat,
                name="Net Profit (PAT Benchmark)",
                mode="lines+markers",
                line=dict(color="#64748B", width=2.2, dash="dash"),
                marker=dict(size=6, symbol="diamond"),
                hovertemplate="PAT Benchmark: ₹%{y:,.0f} Cr<extra></extra>"
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#0F172A", family="Inter, sans-serif")
        ),
        barmode="group",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_yaxes(
        title_text="Cash Flow (₹ Crores)",
        gridcolor="#F1F5F9",
        tickfont=dict(size=11, color="#64748B", family="JetBrains Mono, monospace")
    )
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11, color="#64748B"))
    return fig


def build_balance_sheet_chart(fin_data: Dict[str, Any], company_name: str) -> go.Figure:
    """Creates a balance sheet structure chart: Net Worth vs Total Debt."""
    bs_years = fin_data.get("bs_years", [])
    bs = fin_data.get("bs", {})

    nw = bs.get("Total Net Worth / Equity", {}).get("values", [])
    debt = bs.get("Total Borrowings / Debt", {}).get("values", [])
    assets = bs.get("Total Liabilities & Assets", {}).get("values", [])

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=bs_years,
            y=nw,
            name="Net Worth (Equity)",
            marker_color="#059669",
            hovertemplate="Net Worth: ₹%{y:,.0f} Cr<extra></extra>"
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Bar(
            x=bs_years,
            y=debt,
            name="Total Borrowings (Debt)",
            marker_color="#DC2626",
            hovertemplate="Debt: ₹%{y:,.0f} Cr<extra></extra>"
        ),
        secondary_y=False
    )

    de_ratio = [round(d / n, 2) if n > 0 else 0.0 for d, n in zip(debt, nw)]
    fig.add_trace(
        go.Scatter(
            x=bs_years,
            y=de_ratio,
            name="Debt-to-Equity",
            mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(size=6),
            hovertemplate="D/E: %{y:.2f}x<extra></extra>"
        ),
        secondary_y=True
    )

    fig.update_layout(
        template="plotly_white",
        height=360,
        margin=dict(l=10, r=10, t=25, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#0F172A", family="Inter, sans-serif")
        ),
        barmode="group",
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_yaxes(
        title_text="Amount (₹ Crores)",
        secondary_y=False,
        gridcolor="#F1F5F9",
        tickfont=dict(size=11, color="#64748B", family="JetBrains Mono, monospace")
    )
    fig.update_yaxes(
        title_text="Debt / Equity (x)",
        secondary_y=True,
        showgrid=False,
        tickfont=dict(size=11, color="#64748B", family="JetBrains Mono, monospace")
    )
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11, color="#64748B"))
    return fig


def render_growth_cagr_scorecard_html(cagr: Dict[str, Any]) -> str:
    """Renders the 4-card Screener-style Compounded Growth & Quality KPI Matrix."""
    sales_cagr = cagr.get("sales_cagr")
    sales_yoy = cagr.get("sales_yoy")
    pat_cagr = cagr.get("pat_cagr")
    pat_yoy = cagr.get("pat_yoy")
    avg_cfo_pat = cagr.get("avg_cfo_pat")
    latest_roe = cagr.get("latest_roe")
    latest_de = cagr.get("latest_de")
    n_years = cagr.get("n_years", 3)
    latest_opm = cagr.get("latest_opm")
    opm_exp = cagr.get("opm_expansion")

    # Cash conversion forensic tag
    if avg_cfo_pat is not None:
        if avg_cfo_pat >= 100:
            cfo_badge = '<span style="background: #ECFDF5; color: #059669; border: 1.5px solid #A7F3D0; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">🟢 Institutional Grade</span>'
        elif avg_cfo_pat >= 75:
            cfo_badge = '<span style="background: #EFF6FF; color: #2563EB; border: 1.5px solid #BFDBFE; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">🔵 Sound Accruals</span>'
        elif avg_cfo_pat >= 50:
            cfo_badge = '<span style="background: #FFFBEB; color: #D97706; border: 1.5px solid #FDE68A; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">🟡 Working Capital Drag</span>'
        else:
            cfo_badge = '<span style="background: #FEF2F2; color: #DC2626; border: 1.5px solid #FECACA; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">🔴 Accrual Divergence</span>'
    else:
        cfo_badge = '<span style="background: #F1F5F9; color: #64748B; border: 1.5px solid #E2E8F0; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">⚪ Data Unavailable</span>'

    # Debt tag
    if latest_de is not None:
        if latest_de <= 0.1:
            de_badge = '<span style="background: #ECFDF5; color: #059669; border: 1.5px solid #A7F3D0; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">Practically Debt Free</span>'
        elif latest_de <= 0.5:
            de_badge = '<span style="background: #EFF6FF; color: #2563EB; border: 1.5px solid #BFDBFE; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">Conservative Leverage</span>'
        elif latest_de <= 1.0:
            de_badge = '<span style="background: #FFFBEB; color: #D97706; border: 1.5px solid #FDE68A; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">Moderate Debt</span>'
        else:
            de_badge = '<span style="background: #FEF2F2; color: #DC2626; border: 1.5px solid #FECACA; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">High Leverage</span>'
    else:
        de_badge = '<span style="background: #F1F5F9; color: #64748B; border: 1.5px solid #E2E8F0; font-size: 11.5px; font-weight: 800; padding: 3px 9px; border-radius: 9999px;">⚪ Data Unavailable</span>'

    sales_cagr_str = f"{sales_cagr:.1f}%" if sales_cagr is not None else "N/A"
    pat_cagr_str = f"{pat_cagr:.1f}%" if pat_cagr is not None else "N/A"
    sales_yoy_str = f"{sales_yoy:+.1f}%" if sales_yoy is not None else "N/A"
    sales_yoy_color = ("#059669" if sales_yoy >= 0 else "#DC2626") if sales_yoy is not None else "#64748B"
    pat_yoy_str = f"{pat_yoy:+.1f}%" if pat_yoy is not None else "N/A"
    pat_yoy_color = ("#059669" if pat_yoy >= 0 else "#DC2626") if pat_yoy is not None else "#64748B"
    opm_exp_str = (f"+{opm_exp:.1f}%" if opm_exp >= 0 else f"{opm_exp:.1f}%") if opm_exp is not None else "N/A"
    opm_color = ("#059669" if opm_exp >= 0 else "#DC2626") if opm_exp is not None else "#64748B"
    avg_cfo_pat_str = f"{avg_cfo_pat:.1f}%" if avg_cfo_pat is not None else "N/A"
    latest_roe_str = f"{latest_roe:.1f}%" if latest_roe is not None else "N/A"
    latest_de_str = f"{latest_de:.2f}x" if latest_de is not None else "N/A"

    html = f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 12px; margin-bottom: 22px;">
      
      <!-- Card 1: Sales Growth -->
      <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #059669; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size: 12.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Compounded Sales Growth</div>
        <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 8px;">
          <span style="font-size: 28px; font-weight: 900; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{sales_cagr_str}</span>
          <span style="font-size: 13px; font-weight: 700; color: #059669;">{n_years}Y CAGR</span>
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #64748B; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E2E8F0; padding-top: 8px;">
          <span>Latest Fiscal YoY:</span>
          <span style="font-weight: 800; font-size: 14px; color: {sales_yoy_color}; font-family: 'JetBrains Mono', monospace;">{sales_yoy_str}</span>
        </div>
      </div>

      <!-- Card 2: Profit Growth -->
      <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #2563EB; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size: 12.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Compounded Profit Growth</div>
        <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 8px;">
          <span style="font-size: 28px; font-weight: 900; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{pat_cagr_str}</span>
          <span style="font-size: 13px; font-weight: 700; color: #2563EB;">{n_years}Y PAT CAGR</span>
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #64748B; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E2E8F0; padding-top: 8px;">
          <span>Latest Fiscal YoY:</span>
          <span style="font-weight: 800; font-size: 14px; color: {pat_yoy_color}; font-family: 'JetBrains Mono', monospace;">{pat_yoy_str}</span>
        </div>
      </div>

      <!-- Card 3: Forensic Cash Conversion -->
      <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #D97706; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 12.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">CFO / PAT Conversion</span>
          {cfo_badge}
        </div>
        <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 8px;">
          <span style="font-size: 28px; font-weight: 900; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{avg_cfo_pat_str}</span>
          <span style="font-size: 13px; font-weight: 700; color: #D97706;">Avg Cash Yield</span>
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #64748B; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E2E8F0; padding-top: 8px;">
          <span>OPM Expansion ({n_years}Y):</span>
          <span style="font-weight: 800; font-size: 14px; color: {opm_color}; font-family: 'JetBrains Mono', monospace;">{opm_exp_str}</span>
        </div>
      </div>

      <!-- Card 4: Capital Return & Leverage -->
      <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 4.5px solid #7C3AED; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 12.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">Return on Equity & D/E</span>
          {de_badge}
        </div>
        <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 8px;">
          <span style="font-size: 28px; font-weight: 900; color: #0F172A; font-family: 'JetBrains Mono', monospace;">{latest_roe_str}</span>
          <span style="font-size: 13px; font-weight: 700; color: #7C3AED;">ROE</span>
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #64748B; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E2E8F0; padding-top: 8px;">
          <span>Debt / Equity:</span>
          <span style="font-weight: 800; font-size: 14px; color: #2563EB; font-family: 'JetBrains Mono', monospace;">{latest_de_str}</span>
        </div>
      </div>

    </div>
    """
    return html


def render_financial_table_html(statement_dict: Dict[str, Any], years: List[str], statement_name: str) -> str:
    """Renders an institutional Screener.in multi-year tabular financial statement with generous legible typography."""
    if not statement_dict or not years:
        return "<div style='color: #64748B; padding: 18px; font-size: 15px;'>No statement data available.</div>"

    header_cols = "".join([
        f'<th style="text-align: right; padding: 12px 18px; font-size: 13.5px; font-weight: 800; color: #0F172A; border-bottom: 2px solid #E2E8F0; background: #F8FAFC; white-space: nowrap; font-family: \'JetBrains Mono\', monospace;">{yr}</th>'
        for yr in years
    ])

    rows_html = []
    for label, meta in statement_dict.items():
        vals = meta.get("values", [])
        is_highlight = meta.get("highlight", False)
        is_pct = meta.get("is_pct", False)
        is_eps = meta.get("is_eps", False)

        row_bg = "#F8FAFC" if is_highlight else "#FFFFFF"
        font_weight = "800" if is_highlight else "500"
        label_color = "#0F172A" if is_highlight else "#334155"

        val_cells = []
        for v in vals:
            if v is None or pd.isna(v):
                formatted_val = "N/A"
                val_color = "#64748B"
            elif is_pct:
                formatted_val = f"{v:.1f}%"
                val_color = "#059669" if v >= 0 else "#DC2626"
            elif is_eps:
                formatted_val = f"₹{v:.2f}"
                val_color = "#2563EB" if is_highlight else "#0F172A"
            else:
                if v == 0:
                    formatted_val = "-"
                    val_color = "#64748B"
                elif v > 0:
                    formatted_val = f"₹{v:,.1f}"
                    val_color = "#059669" if is_highlight else "#0F172A"
                else:
                    formatted_val = f"-₹{abs(v):,.1f}"
                    val_color = "#DC2626"

            val_cells.append(
                f'<td style="text-align: right; padding: 12px 18px; font-family: \'JetBrains Mono\', monospace; font-size: 14px; font-weight: {font_weight}; color: {val_color}; white-space: nowrap;">{formatted_val}</td>'
            )

        rows_html.append(
            f'<tr style="background: {row_bg}; border-bottom: 1px solid #F1F5F9;">'
            f'<td style="padding: 12px 20px; font-size: 14px; font-weight: {font_weight}; color: {label_color}; white-space: nowrap;">{label}</td>'
            f'{"".join(val_cells)}'
            f'</tr>'
        )

    return f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; overflow-x: auto; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-top: 12px; margin-bottom: 20px;">
      <table style="width: 100%; border-collapse: collapse; font-family: 'Inter', -apple-system, sans-serif;">
        <thead>
          <tr style="background: #F8FAFC;">
            <th style="text-align: left; padding: 12px 20px; font-size: 13.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #E2E8F0; white-space: nowrap;">
              {statement_name} <span style="font-size: 12px; font-weight: 600; color: #64748B;">(₹ Crores)</span>
            </th>
            {header_cols}
          </tr>
        </thead>
        <tbody>
          {"".join(rows_html)}
        </tbody>
      </table>
    </div>
    """


def generate_forensic_cagr_insights(fin_data: Dict[str, Any], company_name: str) -> List[Dict[str, str]]:
    """Generates concise institutional takeaways based on multi-year trends."""
    cagr = fin_data.get("cagr", {}) if isinstance(fin_data, dict) else {}

    def _safe_float(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    sales_cagr = _safe_float(cagr.get("sales_cagr"))
    pat_cagr = _safe_float(cagr.get("pat_cagr"))
    sales_yoy = _safe_float(cagr.get("sales_yoy"))
    pat_yoy = _safe_float(cagr.get("pat_yoy"))
    avg_cfo_pat = _safe_float(cagr.get("avg_cfo_pat"))
    latest_de = _safe_float(cagr.get("latest_de"))
    latest_roe = _safe_float(cagr.get("latest_roe"))
    opm_exp = _safe_float(cagr.get("opm_expansion"))
    n_years = cagr.get("n_years", 3) or 3

    insights = []

    # 1. Sales & Growth Momentum
    if sales_cagr is not None:
        yoy_str = f"with latest fiscal YoY growth of {sales_yoy:+.1f}%" if sales_yoy is not None else "over recent reporting periods"
        if sales_cagr >= 15:
            insights.append({
                "type": "positive",
                "title": f"Aggressive Topline Compounder ({sales_cagr:.1f}% {n_years}Y CAGR)",
                "body": f"{company_name} demonstrates strong revenue compounding over {n_years} years {yoy_str}, indicating sustained market share expansion."
            })
        elif sales_cagr >= 8:
            insights.append({
                "type": "positive",
                "title": f"Steady Topline Expansion ({sales_cagr:.1f}% {n_years}Y CAGR)",
                "body": f"Solid revenue growth trajectory matching or outpacing Indian GDP nominal growth. Latest fiscal expansion recorded {yoy_str}."
            })
        else:
            insights.append({
                "type": "neutral",
                "title": f"Moderate Growth / Mature Scale ({sales_cagr:.1f}% {n_years}Y CAGR)",
                "body": f"Topline expansion reflects mature market saturation or cyclical plateau. Latest fiscal growth clocked {yoy_str}."
            })

    # 2. Forensic Earnings Quality & Cash Flow
    if avg_cfo_pat is not None:
        if avg_cfo_pat >= 95:
            insights.append({
                "type": "positive",
                "title": f"High Earnings Quality (Avg CFO/PAT: {avg_cfo_pat:.1f}%)",
                "body": "Exceptional cash flow conversion. Accounting net profit is backed 1-to-1 or better by audited operating cash flow, ruling out aggressive revenue accruals."
            })
        elif avg_cfo_pat >= 70:
            insights.append({
                "type": "neutral",
                "title": f"Acceptable Cash Flow Backing (Avg CFO/PAT: {avg_cfo_pat:.1f}%)",
                "body": "Operating cash flow broadly tracks net profit, though working capital requirements or inventory cycles absorb a portion of annual earnings."
            })
        else:
            insights.append({
                "type": "caution",
                "title": f"Forensic Accrual Divergence (Avg CFO/PAT: {avg_cfo_pat:.1f}%)",
                "body": "Reported net profits exceed audited cash generated from operations, indicating working capital buildup, extended debtor days, or aggressive revenue recognition."
            })
    else:
        insights.append({
            "type": "neutral",
            "title": "CFO / PAT Conversion: Uncalculated / Negative Base",
            "body": "Cash conversion percentage is not applicable due to negative net profit or non-positive baseline cash flows across reporting periods."
        })

    # 3. Solvency & Balance Sheet Endurance
    if latest_de is not None:
        if latest_de <= 0.2:
            insights.append({
                "type": "positive",
                "title": f"Fortress Balance Sheet (D/E: {latest_de:.2f}x)",
                "body": "Virtually zero debt distress risk. Robust net worth foundation provides high resilience against interest rate hikes and economic downcycles."
            })
        elif latest_de <= 0.8:
            insights.append({
                "type": "neutral",
                "title": f"Prudent Capital Leverage (D/E: {latest_de:.2f}x)",
                "body": "Manageable debt levels well within standard institutional solvency guardrails for Indian corporate balance sheets."
            })
        else:
            insights.append({
                "type": "caution",
                "title": f"Elevated Balance Sheet Leverage (D/E: {latest_de:.2f}x)",
                "body": "Higher debt burden requires sustained operating cash flows to comfortably service interest costs and refinancing maturities."
            })
    else:
        insights.append({
            "type": "neutral",
            "title": "Solvency & Leverage: Data Unavailable",
            "body": "Debt-to-equity ratio could not be determined from the available historical balance sheet statements."
        })

    # 4. Operating Margin & Return on Equity
    if opm_exp is not None:
        if opm_exp > 1.0:
            insights.append({
                "type": "positive",
                "title": f"Operating Margin Expansion (+{opm_exp:.1f}% over {n_years}Y)",
                "body": f"Operating efficiency has expanded over {n_years} fiscal periods, proving operating leverage and pricing power against raw material cost pressures."
            })
        elif opm_exp < -2.0:
            insights.append({
                "type": "caution",
                "title": f"Operating Margin Compression ({opm_exp:.1f}% over {n_years}Y)",
                "body": f"Operating margins have faced compression over {n_years} fiscal periods, reflecting competitive discounting, higher input costs, or elevated marketing spend."
            })

    return insights
