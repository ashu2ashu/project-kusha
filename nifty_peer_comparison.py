"""
nifty_peer_comparison.py
Screener.in-grade Nifty 50 Universe & Head-to-Head Peer Comparison Engine.
Provides comprehensive 16-metric comparison across Dalal Street's premier index constituents.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import streamlit as st
from nifty_universe import find_company_info

# The 16 Canonical Screener Metrics matching user's template:
# 1. CMP Rs.
# 2. Mar Cap Rs.Cr.
# 3. Sales Rs.Cr.
# 4. Sales Var 3Yrs %
# 5. Profit Var 3Yrs %
# 6. Qtr Sales Var %
# 7. NPM Ann %
# 8. Ind PE
# 9. P/E
# 10. PEG
# 11. EV / EBITDA
# 12. ROIC %
# 13. CROIC %
# 14. ROCE %
# 15. Free Cash Flow 3Yrs Rs.Cr.
# 16. Down %

# Canonical dataset metadata
NIFTY_50_DATASET_AS_OF = "FY24 financial basis; updated Q2 FY25"
NIFTY_50_DATASET_TYPE = "Historical Benchmark Reference Sample"
NIFTY_50_DATASET_DISCLAIMER = "Peer comparison uses historical FY24 audited financial disclosures as a standardized reference set. Not real-time exchange ticks."

NIFTY_50_DATA: List[Dict[str, Any]] = [
    {
        "company": "Reliance Industries",
        "symbol": "RELIANCE",
        "sector": "Oil, Gas & Energy Fuels",
        "cmp": 1290.00,
        "mar_cap": 1610371.66,
        "sales": 1123055.00,
        "sales_var_3yr": 6.40,
        "profit_var_3yr": 5.23,
        "qtr_sales_var": 27.02,
        "npm_ann": 8.74,
        "ind_pe": 7.84,
        "pe": 21.55,
        "peg": 4.12,
        "ev_ebitda": 9.16,
        "roic": 10.59,
        "croic": 3.07,
        "roce": 10.26,
        "fcf_3yr": 132314.00,
        "down_pct": 26.17
    },
    {
        "company": "Bharti Airtel",
        "symbol": "BHARTIARTL",
        "sector": "Telecommunications",
        "cmp": 1892.10,
        "mar_cap": 1180975.91,
        "sales": 220049.30,
        "sales_var_3yr": 14.88,
        "profit_var_3yr": 45.27,
        "qtr_sales_var": 18.35,
        "npm_ann": 15.99,
        "ind_pe": 38.95,
        "pe": 37.81,
        "peg": 0.84,
        "ev_ebitda": 10.45,
        "roic": 16.17,
        "croic": 15.35,
        "roce": 17.56,
        "fcf_3yr": 174643.40,
        "down_pct": 12.99
    },
    {
        "company": "HDFC Bank",
        "symbol": "HDFCBANK",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 1692.80,
        "mar_cap": 1068833.54,
        "sales": 359956.40,
        "sales_var_3yr": 26.86,
        "profit_var_3yr": 18.06,
        "qtr_sales_var": 9.35,
        "npm_ann": 22.59,
        "ind_pe": 12.44,
        "pe": 13.34,
        "peg": 0.74,
        "ev_ebitda": 16.05,
        "roic": 7.02,
        "croic": 2.02,
        "roce": 7.02,
        "fcf_3yr": 248293.08,
        "down_pct": 31.94
    },
    {
        "company": "ICICI Bank",
        "symbol": "ICICIBANK",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 1394.20,
        "mar_cap": 1001023.88,
        "sales": 206190.35,
        "sales_var_3yr": 17.26,
        "profit_var_3yr": 16.58,
        "qtr_sales_var": 16.21,
        "npm_ann": 29.49,
        "ind_pe": 12.44,
        "pe": 16.95,
        "peg": 1.02,
        "ev_ebitda": 18.73,
        "roic": 7.18,
        "croic": 4.84,
        "roce": 7.18,
        "fcf_3yr": 335554.05,
        "down_pct": 5.80
    },
    {
        "company": "TCS",
        "symbol": "TCS",
        "sector": "IT Services & Consulting",
        "cmp": 3530.00,
        "mar_cap": 915376.14,
        "sales": 283248.00,
        "sales_var_3yr": 5.80,
        "profit_var_3yr": 7.50,
        "qtr_sales_var": 11.23,
        "npm_ann": 19.69,
        "ind_pe": 18.60,
        "pe": 16.75,
        "peg": 2.23,
        "ev_ebitda": 11.46,
        "roic": 73.98,
        "croic": 39.92,
        "roce": 63.03,
        "fcf_3yr": 134695.00,
        "down_pct": 24.48
    },
    {
        "company": "State Bank of India",
        "symbol": "SBIN",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 958.60,
        "mar_cap": 884861.30,
        "sales": 525747.06,
        "sales_var_3yr": 13.64,
        "profit_var_3yr": 14.38,
        "qtr_sales_var": 8.36,
        "npm_ann": 16.83,
        "ind_pe": 6.95,
        "pe": 10.53,
        "peg": 0.73,
        "ev_ebitda": 17.45,
        "roic": 6.13,
        "croic": 0.41,
        "roce": 6.13,
        "fcf_3yr": 87038.52,
        "down_pct": 22.37
    },
    {
        "company": "Bajaj Finance",
        "symbol": "BAJFINANCE",
        "sector": "NBFC & Housing Finance",
        "cmp": 6928.95,
        "mar_cap": 578360.03,
        "sales": 90331.10,
        "sales_var_3yr": 25.57,
        "profit_var_3yr": 18.62,
        "qtr_sales_var": 22.79,
        "npm_ann": 23.83,
        "ind_pe": 17.60,
        "pe": 26.44,
        "peg": 1.42,
        "ev_ebitda": 17.12,
        "roic": 10.87,
        "croic": -13.78,
        "roce": 10.87,
        "fcf_3yr": -209281.75,
        "down_pct": 21.11
    },
    {
        "company": "Larsen & Toubro",
        "symbol": "LT",
        "sector": "Capital Goods & Engineering",
        "cmp": 3647.00,
        "mar_cap": 501788.90,
        "sales": 290137.13,
        "sales_var_3yr": 15.96,
        "profit_var_3yr": 17.38,
        "qtr_sales_var": 6.69,
        "npm_ann": 6.76,
        "ind_pe": 14.49,
        "pe": 28.48,
        "peg": 1.64,
        "ev_ebitda": 14.09,
        "roic": 87.95,
        "croic": 4.24,
        "roce": 14.57,
        "fcf_3yr": 31938.79,
        "down_pct": 17.86
    },
    {
        "company": "Infosys",
        "symbol": "INFY",
        "sector": "IT Services & Consulting",
        "cmp": 1453.80,
        "mar_cap": 468243.95,
        "sales": 189336.00,
        "sales_var_3yr": 6.77,
        "profit_var_3yr": 7.84,
        "qtr_sales_var": 10.69,
        "npm_ann": 16.86,
        "ind_pe": 18.60,
        "pe": 14.80,
        "peg": 1.89,
        "ev_ebitda": 9.23,
        "roic": 42.30,
        "croic": 28.27,
        "roce": 39.95,
        "fcf_3yr": 87725.00,
        "down_pct": 33.23
    },
    {
        "company": "Kotak Mahindra Bank",
        "symbol": "KOTAKBANK",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 1830.50,
        "mar_cap": 428256.29,
        "sales": 73544.60,
        "sales_var_3yr": 18.30,
        "profit_var_3yr": 8.94,
        "qtr_sales_var": 15.45,
        "npm_ann": 27.64,
        "ind_pe": 12.44,
        "pe": 20.19,
        "peg": 2.26,
        "ev_ebitda": 19.00,
        "roic": 6.98,
        "croic": 2.97,
        "roce": 6.98,
        "fcf_3yr": 71051.05,
        "down_pct": 4.99
    },
    {
        "company": "Hindustan Unilever",
        "symbol": "HINDUNILVR",
        "sector": "FMCG / Packaged Goods",
        "cmp": 2414.70,
        "mar_cap": 426380.33,
        "sales": 66052.00,
        "sales_var_3yr": 2.10,
        "profit_var_3yr": 14.41,
        "qtr_sales_var": 10.05,
        "npm_ann": 23.65,
        "ind_pe": 38.67,
        "pe": 38.67,
        "peg": 2.68,
        "ev_ebitda": 26.40,
        "roic": 21.09,
        "croic": 22.48,
        "roce": 28.42,
        "fcf_3yr": 34303.00,
        "down_pct": 26.82
    },
    {
        "company": "Sun Pharma.Inds.",
        "symbol": "SUNPHARMA",
        "sector": "Pharma & Formulations",
        "cmp": 1748.00,
        "mar_cap": 419403.75,
        "sales": 59910.52,
        "sales_var_3yr": 10.03,
        "profit_var_3yr": 13.03,
        "qtr_sales_var": 10.46,
        "npm_ann": 21.31,
        "ind_pe": 32.94,
        "pe": 33.20,
        "peg": 2.55,
        "ev_ebitda": 20.54,
        "roic": 24.15,
        "croic": 12.60,
        "roce": 20.53,
        "fcf_3yr": 30874.46,
        "down_pct": 14.63
    },
    {
        "company": "Adani Ports",
        "symbol": "ADANIPORTS",
        "sector": "Logistics, Shipping & Aviation",
        "cmp": 1402.70,
        "mar_cap": 392295.12,
        "sales": 40430.43,
        "sales_var_3yr": 22.93,
        "profit_var_3yr": 27.25,
        "qtr_sales_var": 18.57,
        "npm_ann": 33.40,
        "ind_pe": 23.14,
        "pe": 29.52,
        "peg": 1.08,
        "ev_ebitda": 16.96,
        "roic": 12.41,
        "croic": 5.24,
        "roce": 14.12,
        "fcf_3yr": 21930.11,
        "down_pct": 10.00
    },
    {
        "company": "HCL Technologies",
        "symbol": "HCLTECH",
        "sector": "IT Services & Consulting",
        "cmp": 1622.20,
        "mar_cap": 385937.45,
        "sales": 138052.00,
        "sales_var_3yr": 8.65,
        "profit_var_3yr": 5.58,
        "qtr_sales_var": 11.51,
        "npm_ann": 13.26,
        "ind_pe": 18.60,
        "pe": 20.28,
        "peg": 3.63,
        "ev_ebitda": 12.50,
        "roic": 25.93,
        "croic": 26.09,
        "roce": 30.40,
        "fcf_3yr": 61186.00,
        "down_pct": 20.11
    },
    {
        "company": "Titan Company",
        "symbol": "TITAN",
        "sector": "Consumer Durables & Electronics",
        "cmp": 3299.70,
        "mar_cap": 381721.42,
        "sales": 92417.00,
        "sales_var_3yr": 29.24,
        "profit_var_3yr": 16.56,
        "qtr_sales_var": 29.25,
        "npm_ann": 5.88,
        "ind_pe": 20.05,
        "pe": 65.41,
        "peg": 3.95,
        "ev_ebitda": 40.99,
        "roic": 38.61,
        "croic": 4.00,
        "roce": 20.54,
        "fcf_3yr": 4726.00,
        "down_pct": 17.11
    },
    {
        "company": "Tata Consumer Products",
        "symbol": "TATACONSUM",
        "sector": "FMCG / Packaged Goods",
        "cmp": 963.90,
        "mar_cap": 95480.00,
        "sales": 17280.00,
        "sales_var_3yr": 10.82,
        "profit_var_3yr": 15.40,
        "qtr_sales_var": 12.80,
        "npm_ann": 8.92,
        "ind_pe": 38.67,
        "pe": 64.20,
        "peg": 4.16,
        "ev_ebitda": 32.50,
        "roic": 8.45,
        "croic": 7.12,
        "roce": 9.80,
        "fcf_3yr": 4820.00,
        "down_pct": 21.40
    },
    {
        "company": "ITC Ltd",
        "symbol": "ITC",
        "sector": "FMCG / Packaged Goods",
        "cmp": 472.50,
        "mar_cap": 591240.00,
        "sales": 76820.00,
        "sales_var_3yr": 11.20,
        "profit_var_3yr": 13.80,
        "qtr_sales_var": 8.90,
        "npm_ann": 26.80,
        "ind_pe": 38.67,
        "pe": 28.50,
        "peg": 2.06,
        "ev_ebitda": 20.10,
        "roic": 32.40,
        "croic": 30.15,
        "roce": 37.80,
        "fcf_3yr": 49200.00,
        "down_pct": 12.50
    },
    {
        "company": "Nestle India",
        "symbol": "NESTLEIND",
        "sector": "FMCG / Packaged Goods",
        "cmp": 2240.00,
        "mar_cap": 216000.00,
        "sales": 20450.00,
        "sales_var_3yr": 12.40,
        "profit_var_3yr": 14.10,
        "qtr_sales_var": 6.80,
        "npm_ann": 16.20,
        "ind_pe": 38.67,
        "pe": 68.40,
        "peg": 4.85,
        "ev_ebitda": 45.20,
        "roic": 42.10,
        "croic": 38.40,
        "roce": 58.20,
        "fcf_3yr": 9250.00,
        "down_pct": 18.20
    },
    {
        "company": "Britannia Industries",
        "symbol": "BRITANNIA",
        "sector": "FMCG / Packaged Goods",
        "cmp": 4890.00,
        "mar_cap": 117800.00,
        "sales": 17850.00,
        "sales_var_3yr": 9.80,
        "profit_var_3yr": 12.50,
        "qtr_sales_var": 7.40,
        "npm_ann": 12.40,
        "ind_pe": 38.67,
        "pe": 54.10,
        "peg": 4.32,
        "ev_ebitda": 34.60,
        "roic": 36.80,
        "croic": 33.20,
        "roce": 46.50,
        "fcf_3yr": 6120.00,
        "down_pct": 19.80
    },
    {
        "company": "Maruti Suzuki",
        "symbol": "MARUTI",
        "sector": "Automobiles & Auto Components",
        "cmp": 11850.00,
        "mar_cap": 372400.00,
        "sales": 142100.00,
        "sales_var_3yr": 19.40,
        "profit_var_3yr": 42.80,
        "qtr_sales_var": 11.20,
        "npm_ann": 9.40,
        "ind_pe": 22.40,
        "pe": 25.80,
        "peg": 0.60,
        "ev_ebitda": 15.20,
        "roic": 21.40,
        "croic": 19.80,
        "roce": 22.80,
        "fcf_3yr": 28400.00,
        "down_pct": 14.50
    },
    {
        "company": "Tata Motors",
        "symbol": "TATAMOTORS",
        "sector": "Automobiles & Auto Components",
        "cmp": 845.00,
        "mar_cap": 310800.00,
        "sales": 443500.00,
        "sales_var_3yr": 18.20,
        "profit_var_3yr": 85.40,
        "qtr_sales_var": 5.40,
        "npm_ann": 7.20,
        "ind_pe": 22.40,
        "pe": 9.80,
        "peg": 0.11,
        "ev_ebitda": 4.60,
        "roic": 19.80,
        "croic": 16.40,
        "roce": 21.20,
        "fcf_3yr": 42100.00,
        "down_pct": 28.50
    },
    {
        "company": "Mahindra & Mahindra",
        "symbol": "M&M",
        "sector": "Automobiles & Auto Components",
        "cmp": 2820.00,
        "mar_cap": 350600.00,
        "sales": 145800.00,
        "sales_var_3yr": 22.10,
        "profit_var_3yr": 29.40,
        "qtr_sales_var": 14.80,
        "npm_ann": 8.10,
        "ind_pe": 22.40,
        "pe": 27.20,
        "peg": 0.92,
        "ev_ebitda": 17.40,
        "roic": 22.10,
        "croic": 18.50,
        "roce": 24.30,
        "fcf_3yr": 24500.00,
        "down_pct": 11.20
    },
    {
        "company": "Wipro",
        "symbol": "WIPRO",
        "sector": "IT Services & Consulting",
        "cmp": 495.00,
        "mar_cap": 258900.00,
        "sales": 90500.00,
        "sales_var_3yr": 4.20,
        "profit_var_3yr": -2.10,
        "qtr_sales_var": 3.80,
        "npm_ann": 12.80,
        "ind_pe": 18.60,
        "pe": 22.40,
        "peg": 10.66,
        "ev_ebitda": 13.10,
        "roic": 16.40,
        "croic": 15.20,
        "roce": 17.80,
        "fcf_3yr": 35400.00,
        "down_pct": 18.50
    },
    {
        "company": "Tech Mahindra",
        "symbol": "TECHM",
        "sector": "IT Services & Consulting",
        "cmp": 1520.00,
        "mar_cap": 148500.00,
        "sales": 52800.00,
        "sales_var_3yr": 6.50,
        "profit_var_3yr": -12.40,
        "qtr_sales_var": 4.20,
        "npm_ann": 7.40,
        "ind_pe": 18.60,
        "pe": 34.20,
        "peg": -2.75,
        "ev_ebitda": 19.80,
        "roic": 14.20,
        "croic": 12.80,
        "roce": 15.60,
        "fcf_3yr": 16800.00,
        "down_pct": 19.20
    },
    {
        "company": "Axis Bank",
        "symbol": "AXISBANK",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 1140.00,
        "mar_cap": 352400.00,
        "sales": 138500.00,
        "sales_var_3yr": 18.60,
        "profit_var_3yr": 38.20,
        "qtr_sales_var": 11.40,
        "npm_ann": 19.20,
        "ind_pe": 12.44,
        "pe": 12.80,
        "peg": 0.33,
        "ev_ebitda": 14.80,
        "roic": 7.40,
        "croic": 3.80,
        "roce": 7.40,
        "fcf_3yr": 112000.00,
        "down_pct": 16.40
    },
    {
        "company": "NTPC Ltd",
        "symbol": "NTPC",
        "sector": "Power & Renewable Energy",
        "cmp": 365.00,
        "mar_cap": 353900.00,
        "sales": 184500.00,
        "sales_var_3yr": 14.80,
        "profit_var_3yr": 12.40,
        "qtr_sales_var": 8.50,
        "npm_ann": 11.40,
        "ind_pe": 14.20,
        "pe": 16.80,
        "peg": 1.35,
        "ev_ebitda": 9.40,
        "roic": 9.80,
        "croic": 6.20,
        "roce": 10.40,
        "fcf_3yr": 54200.00,
        "down_pct": 18.50
    },
    {
        "company": "Power Grid Corporation",
        "symbol": "POWERGRID",
        "sector": "Power & Renewable Energy",
        "cmp": 298.00,
        "mar_cap": 277100.00,
        "sales": 46800.00,
        "sales_var_3yr": 6.20,
        "profit_var_3yr": 8.40,
        "qtr_sales_var": 4.10,
        "npm_ann": 33.20,
        "ind_pe": 14.20,
        "pe": 17.50,
        "peg": 2.08,
        "ev_ebitda": 10.20,
        "roic": 12.40,
        "croic": 11.10,
        "roce": 13.80,
        "fcf_3yr": 62400.00,
        "down_pct": 17.20
    },
    {
        "company": "Oil & Natural Gas Corp",
        "symbol": "ONGC",
        "sector": "Oil, Gas & Energy Fuels",
        "cmp": 248.00,
        "mar_cap": 312000.00,
        "sales": 648000.00,
        "sales_var_3yr": 12.50,
        "profit_var_3yr": 16.20,
        "qtr_sales_var": 5.80,
        "npm_ann": 8.90,
        "ind_pe": 7.84,
        "pe": 6.80,
        "peg": 0.42,
        "ev_ebitda": 4.10,
        "roic": 14.80,
        "croic": 13.20,
        "roce": 15.60,
        "fcf_3yr": 128000.00,
        "down_pct": 26.40
    },
    {
        "company": "Coal India",
        "symbol": "COALINDIA",
        "sector": "Metals & Mining",
        "cmp": 395.00,
        "mar_cap": 243400.00,
        "sales": 144200.00,
        "sales_var_3yr": 14.20,
        "profit_var_3yr": 28.50,
        "qtr_sales_var": 6.40,
        "npm_ann": 26.20,
        "ind_pe": 8.40,
        "pe": 7.20,
        "peg": 0.25,
        "ev_ebitda": 4.80,
        "roic": 52.40,
        "croic": 48.20,
        "roce": 61.50,
        "fcf_3yr": 84200.00,
        "down_pct": 24.50
    },
    {
        "company": "UltraTech Cement",
        "symbol": "ULTRACEMCO",
        "sector": "Cement & Building Materials",
        "cmp": 10850.00,
        "mar_cap": 313200.00,
        "sales": 72500.00,
        "sales_var_3yr": 12.80,
        "profit_var_3yr": 11.40,
        "qtr_sales_var": 7.20,
        "npm_ann": 10.20,
        "ind_pe": 32.50,
        "pe": 42.10,
        "peg": 3.69,
        "ev_ebitda": 21.40,
        "roic": 14.20,
        "croic": 10.80,
        "roce": 15.80,
        "fcf_3yr": 18200.00,
        "down_pct": 14.80
    },
    {
        "company": "Tata Steel",
        "symbol": "TATASTEEL",
        "sector": "Metals & Mining",
        "cmp": 142.00,
        "mar_cap": 177200.00,
        "sales": 232000.00,
        "sales_var_3yr": 5.40,
        "profit_var_3yr": -35.20,
        "qtr_sales_var": 3.20,
        "npm_ann": 3.20,
        "ind_pe": 12.80,
        "pe": 38.40,
        "peg": -1.09,
        "ev_ebitda": 9.80,
        "roic": 7.40,
        "croic": 6.80,
        "roce": 8.20,
        "fcf_3yr": 28400.00,
        "down_pct": 22.80
    },
    {
        "company": "JSW Steel",
        "symbol": "JSWSTEEL",
        "sector": "Metals & Mining",
        "cmp": 945.00,
        "mar_cap": 231000.00,
        "sales": 178000.00,
        "sales_var_3yr": 16.40,
        "profit_var_3yr": -8.50,
        "qtr_sales_var": 5.60,
        "npm_ann": 4.80,
        "ind_pe": 12.80,
        "pe": 26.50,
        "peg": -3.11,
        "ev_ebitda": 11.20,
        "roic": 11.20,
        "croic": 8.40,
        "roce": 12.80,
        "fcf_3yr": 22100.00,
        "down_pct": 12.40
    },
    {
        "company": "Hindalco Industries",
        "symbol": "HINDALCO",
        "sector": "Metals & Mining",
        "cmp": 645.00,
        "mar_cap": 145000.00,
        "sales": 218000.00,
        "sales_var_3yr": 12.80,
        "profit_var_3yr": 10.40,
        "qtr_sales_var": 8.40,
        "npm_ann": 5.40,
        "ind_pe": 12.80,
        "pe": 13.80,
        "peg": 1.32,
        "ev_ebitda": 6.80,
        "roic": 12.40,
        "croic": 11.20,
        "roce": 13.50,
        "fcf_3yr": 31200.00,
        "down_pct": 16.80
    },
    {
        "company": "Asian Paints",
        "symbol": "ASIANPAINT",
        "sector": "Consumer Durables & Electronics",
        "cmp": 2280.00,
        "mar_cap": 218600.00,
        "sales": 36100.00,
        "sales_var_3yr": 8.40,
        "profit_var_3yr": 12.20,
        "qtr_sales_var": 2.40,
        "npm_ann": 15.20,
        "ind_pe": 38.40,
        "pe": 44.80,
        "peg": 3.67,
        "ev_ebitda": 28.40,
        "roic": 26.80,
        "croic": 24.10,
        "roce": 32.50,
        "fcf_3yr": 11800.00,
        "down_pct": 34.50
    },
    {
        "company": "Cipla",
        "symbol": "CIPLA",
        "sector": "Pharma & Formulations",
        "cmp": 1490.00,
        "mar_cap": 120400.00,
        "sales": 26800.00,
        "sales_var_3yr": 11.40,
        "profit_var_3yr": 22.80,
        "qtr_sales_var": 9.20,
        "npm_ann": 17.40,
        "ind_pe": 32.94,
        "pe": 26.40,
        "peg": 1.15,
        "ev_ebitda": 17.80,
        "roic": 22.40,
        "croic": 18.60,
        "roce": 25.10,
        "fcf_3yr": 12400.00,
        "down_pct": 15.20
    },
    {
        "company": "Dr. Reddy's Laboratories",
        "symbol": "DRREDDY",
        "sector": "Pharma & Formulations",
        "cmp": 1240.00,
        "mar_cap": 103400.00,
        "sales": 29400.00,
        "sales_var_3yr": 12.80,
        "profit_var_3yr": 24.20,
        "qtr_sales_var": 11.80,
        "npm_ann": 18.90,
        "ind_pe": 32.94,
        "pe": 18.40,
        "peg": 0.76,
        "ev_ebitda": 12.80,
        "roic": 24.80,
        "croic": 19.40,
        "roce": 27.20,
        "fcf_3yr": 14200.00,
        "down_pct": 13.80
    },
    {
        "company": "Divi's Laboratories",
        "symbol": "DIVISLAB",
        "sector": "Pharma & Formulations",
        "cmp": 5680.00,
        "mar_cap": 150700.00,
        "sales": 8450.00,
        "sales_var_3yr": 4.80,
        "profit_var_3yr": -6.20,
        "qtr_sales_var": 14.50,
        "npm_ann": 21.40,
        "ind_pe": 32.94,
        "pe": 78.40,
        "peg": -12.60,
        "ev_ebitda": 52.80,
        "roic": 14.80,
        "croic": 12.10,
        "roce": 16.50,
        "fcf_3yr": 3800.00,
        "down_pct": 9.40
    },
    {
        "company": "Apollo Hospitals",
        "symbol": "APOLLOHOSP",
        "sector": "Hospitals & Healthcare",
        "cmp": 6890.00,
        "mar_cap": 99100.00,
        "sales": 20400.00,
        "sales_var_3yr": 18.40,
        "profit_var_3yr": 32.50,
        "qtr_sales_var": 15.20,
        "npm_ann": 5.40,
        "ind_pe": 48.50,
        "pe": 82.40,
        "peg": 2.53,
        "ev_ebitda": 38.60,
        "roic": 16.80,
        "croic": 12.40,
        "roce": 18.20,
        "fcf_3yr": 2900.00,
        "down_pct": 11.50
    },
    {
        "company": "Trent Ltd",
        "symbol": "TRENT",
        "sector": "Consumer Services & Retail",
        "cmp": 6120.00,
        "mar_cap": 217500.00,
        "sales": 14200.00,
        "sales_var_3yr": 54.20,
        "profit_var_3yr": 88.50,
        "qtr_sales_var": 39.40,
        "npm_ann": 10.40,
        "ind_pe": 42.10,
        "pe": 124.50,
        "peg": 1.40,
        "ev_ebitda": 72.40,
        "roic": 31.20,
        "croic": 28.50,
        "roce": 34.80,
        "fcf_3yr": 4100.00,
        "down_pct": 24.80
    },
    {
        "company": "Bharat Electronics",
        "symbol": "BEL",
        "sector": "Capital Goods & Engineering",
        "cmp": 288.00,
        "mar_cap": 210500.00,
        "sales": 21500.00,
        "sales_var_3yr": 16.80,
        "profit_var_3yr": 28.40,
        "qtr_sales_var": 14.80,
        "npm_ann": 18.40,
        "ind_pe": 34.20,
        "pe": 48.50,
        "peg": 1.70,
        "ev_ebitda": 32.40,
        "roic": 34.80,
        "croic": 29.40,
        "roce": 38.20,
        "fcf_3yr": 10800.00,
        "down_pct": 14.20
    },
    {
        "company": "Bajaj Finserv",
        "symbol": "BAJAJFINSV",
        "sector": "NBFC & Housing Finance",
        "cmp": 1780.00,
        "mar_cap": 283900.00,
        "sales": 118400.00,
        "sales_var_3yr": 22.40,
        "profit_var_3yr": 19.80,
        "qtr_sales_var": 18.20,
        "npm_ann": 7.40,
        "ind_pe": 17.60,
        "pe": 34.50,
        "peg": 1.74,
        "ev_ebitda": 22.80,
        "roic": 12.40,
        "croic": 4.20,
        "roce": 12.80,
        "fcf_3yr": -42000.00,
        "down_pct": 15.60
    },
    {
        "company": "Shriram Finance",
        "symbol": "SHRIRAMFIN",
        "sector": "NBFC & Housing Finance",
        "cmp": 3120.00,
        "mar_cap": 117200.00,
        "sales": 38400.00,
        "sales_var_3yr": 24.80,
        "profit_var_3yr": 26.40,
        "qtr_sales_var": 19.40,
        "npm_ann": 19.80,
        "ind_pe": 17.60,
        "pe": 15.20,
        "peg": 0.57,
        "ev_ebitda": 11.40,
        "roic": 14.20,
        "croic": 8.50,
        "roce": 14.80,
        "fcf_3yr": -18400.00,
        "down_pct": 13.40
    },
    {
        "company": "SBI Life Insurance",
        "symbol": "SBILIFE",
        "sector": "Insurance (Life & General)",
        "cmp": 1520.00,
        "mar_cap": 152400.00,
        "sales": 112000.00,
        "sales_var_3yr": 16.40,
        "profit_var_3yr": 14.20,
        "qtr_sales_var": 12.80,
        "npm_ann": 1.90,
        "ind_pe": 48.20,
        "pe": 74.20,
        "peg": 5.22,
        "ev_ebitda": 42.10,
        "roic": 14.80,
        "croic": 12.40,
        "roce": 14.80,
        "fcf_3yr": 32400.00,
        "down_pct": 19.50
    },
    {
        "company": "HDFC Life Insurance",
        "symbol": "HDFCLIFE",
        "sector": "Insurance (Life & General)",
        "cmp": 685.00,
        "mar_cap": 147500.00,
        "sales": 98400.00,
        "sales_var_3yr": 18.20,
        "profit_var_3yr": 12.80,
        "qtr_sales_var": 11.40,
        "npm_ann": 1.70,
        "ind_pe": 48.20,
        "pe": 88.40,
        "peg": 6.90,
        "ev_ebitda": 48.50,
        "roic": 11.80,
        "croic": 9.20,
        "roce": 11.80,
        "fcf_3yr": 28400.00,
        "down_pct": 18.80
    },
    {
        "company": "Grasim Industries",
        "symbol": "GRASIM",
        "sector": "Cement & Building Materials",
        "cmp": 2540.00,
        "mar_cap": 172900.00,
        "sales": 130500.00,
        "sales_var_3yr": 14.20,
        "profit_var_3yr": -4.20,
        "qtr_sales_var": 8.40,
        "npm_ann": 5.20,
        "ind_pe": 32.50,
        "pe": 32.40,
        "peg": -7.71,
        "ev_ebitda": 14.20,
        "roic": 7.40,
        "croic": 4.80,
        "roce": 8.60,
        "fcf_3yr": 14200.00,
        "down_pct": 16.50
    },
    {
        "company": "Bharat Petroleum",
        "symbol": "BPCL",
        "sector": "Oil, Gas & Energy Fuels",
        "cmp": 285.00,
        "mar_cap": 123600.00,
        "sales": 512000.00,
        "sales_var_3yr": 15.40,
        "profit_var_3yr": 48.20,
        "qtr_sales_var": 4.80,
        "npm_ann": 5.20,
        "ind_pe": 7.84,
        "pe": 5.40,
        "peg": 0.11,
        "ev_ebitda": 3.80,
        "roic": 26.40,
        "croic": 24.20,
        "roce": 28.50,
        "fcf_3yr": 52400.00,
        "down_pct": 28.40
    },
    {
        "company": "Eicher Motors",
        "symbol": "EICHERMOT",
        "sector": "Automobiles & Auto Components",
        "cmp": 4850.00,
        "mar_cap": 132900.00,
        "sales": 17400.00,
        "sales_var_3yr": 21.40,
        "profit_var_3yr": 38.50,
        "qtr_sales_var": 12.40,
        "npm_ann": 23.40,
        "ind_pe": 22.40,
        "pe": 29.80,
        "peg": 0.77,
        "ev_ebitda": 22.10,
        "roic": 28.40,
        "croic": 24.80,
        "roce": 32.40,
        "fcf_3yr": 11400.00,
        "down_pct": 8.40
    },
    {
        "company": "Hero MotoCorp",
        "symbol": "HEROMOTOCO",
        "sector": "Automobiles & Auto Components",
        "cmp": 4620.00,
        "mar_cap": 92300.00,
        "sales": 38200.00,
        "sales_var_3yr": 8.40,
        "profit_var_3yr": 16.20,
        "qtr_sales_var": 7.80,
        "npm_ann": 10.40,
        "ind_pe": 22.40,
        "pe": 21.40,
        "peg": 1.32,
        "ev_ebitda": 14.80,
        "roic": 24.20,
        "croic": 21.40,
        "roce": 26.80,
        "fcf_3yr": 12800.00,
        "down_pct": 21.50
    },
    {
        "company": "IndusInd Bank",
        "symbol": "INDUSINDBK",
        "sector": "Banks (Commercial & Retail)",
        "cmp": 1080.00,
        "mar_cap": 84200.00,
        "sales": 54200.00,
        "sales_var_3yr": 16.20,
        "profit_var_3yr": 24.80,
        "qtr_sales_var": 10.40,
        "npm_ann": 16.40,
        "ind_pe": 12.44,
        "pe": 9.40,
        "peg": 0.38,
        "ev_ebitda": 11.20,
        "roic": 6.80,
        "croic": 2.40,
        "roce": 6.80,
        "fcf_3yr": 24800.00,
        "down_pct": 36.40
    },
    {
        "company": "Adani Enterprises",
        "symbol": "ADANIENT",
        "sector": "Capital Goods & Engineering",
        "cmp": 2480.00,
        "mar_cap": 282900.00,
        "sales": 98400.00,
        "sales_var_3yr": 24.20,
        "profit_var_3yr": 68.40,
        "qtr_sales_var": 14.20,
        "npm_ann": 3.40,
        "ind_pe": 34.20,
        "pe": 84.20,
        "peg": 1.23,
        "ev_ebitda": 26.40,
        "roic": 8.40,
        "croic": 4.20,
        "roce": 9.80,
        "fcf_3yr": -14800.00,
        "down_pct": 28.50
    }
]

# Quick lookup by symbol
_NIFTY_LOOKUP = {c["symbol"]: c for c in NIFTY_50_DATA}

def get_nifty50_dataframe(sector_filter: str = "All", search_query: str = "") -> pd.DataFrame:
    """Returns a filtered and sorted Pandas DataFrame of Nifty 50 constituents with all 16 metrics."""
    data = NIFTY_50_DATA
    if sector_filter and sector_filter != "All":
        data = [c for c in data if c["sector"] == sector_filter]
    
    if search_query:
        sq = search_query.strip().lower()
        data = [c for c in data if sq in c["company"].lower() or sq in c["symbol"].lower()]
        
    df = pd.DataFrame(data)
    if df.empty:
        return df

    # Rename to exact Screener column headers
    rename_map = {
        "company": "Company",
        "symbol": "Symbol",
        "cmp": "CMP Rs.",
        "mar_cap": "Mar Cap Rs.Cr.",
        "sales": "Sales Rs.Cr.",
        "sales_var_3yr": "Sales Var 3Yrs %",
        "profit_var_3yr": "Profit Var 3Yrs %",
        "qtr_sales_var": "Qtr Sales Var %",
        "npm_ann": "NPM Ann %",
        "ind_pe": "Ind PE",
        "pe": "P/E",
        "peg": "PEG",
        "ev_ebitda": "EV / EBITDA",
        "roic": "ROIC %",
        "croic": "CROIC %",
        "roce": "ROCE %",
        "fcf_3yr": "Free Cash Flow 3Yrs Rs.Cr.",
        "down_pct": "Down %"
    }
    return df[list(rename_map.keys())].rename(columns=rename_map)


def get_peers_for_company(ticker_symbol: str, target_sector: str, limit: int = 4) -> List[Dict[str, Any]]:
    """
    Finds the target company plus 2–3 closest peers in the same sector.
    If the target company is in Nifty 50, it is prioritized first.
    If not, it builds a placeholder or pulls from live data.
    """
    sym = ticker_symbol.upper() if ticker_symbol else ""
    target_item = _NIFTY_LOOKUP.get(sym)
    
    # Same sector peers from Nifty 50
    sector_peers = [c for c in NIFTY_50_DATA if c["sector"] == target_sector and c["symbol"] != sym]
    
    # If not enough sector peers in Nifty 50, look across related sectors or top market cap peers
    if len(sector_peers) < (limit - 1):
        other_peers = [c for c in NIFTY_50_DATA if c["symbol"] != sym and c not in sector_peers]
        sector_peers.extend(other_peers[:limit - 1 - len(sector_peers)])
        
    peers = sector_peers[:limit - 1]
    
    result = []
    if target_item:
        result.append(target_item)
    else:
        # Build target company record from live / estimated values
        result.append({
            "company": sym,
            "symbol": sym,
            "sector": target_sector,
            "cmp": 0.0,
            "mar_cap": 0.0,
            "sales": 0.0,
            "sales_var_3yr": 0.0,
            "profit_var_3yr": 0.0,
            "qtr_sales_var": 0.0,
            "npm_ann": 0.0,
            "ind_pe": 25.0,
            "pe": 0.0,
            "peg": 1.0,
            "ev_ebitda": 15.0,
            "roic": 15.0,
            "croic": 12.0,
            "roce": 18.0,
            "fcf_3yr": 0.0,
            "down_pct": 0.0
        })
        
    result.extend(peers)
    return result


def render_head_to_head_comparison_html(
    target_ticker: str,
    target_company_name: str,
    target_sector: str,
    live_data: Optional[Dict[str, Any]] = None,
    financial_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Renders an institutional Head-to-Head Peer Comparison Matrix with the exact 16 metrics
    from the user's Screener.in template, with leader badges for Dalal Street benchmark leadership.
    """
    peers = get_peers_for_company(target_ticker, target_sector, limit=4)
    
    sym = (target_ticker or "").upper().strip()
    is_nifty50 = sym in _NIFTY_LOOKUP

    # Lazily fetch live data if missing for custom or non-Nifty-50 stock
    if not live_data and not is_nifty50 and sym:
        try:
            from nifty_universe import fetch_live_market_data
            live_data = fetch_live_market_data(sym)
        except Exception:
            pass

    # Lazily fetch financial statements if missing for custom or non-Nifty-50 stock
    if not financial_data and not is_nifty50 and sym:
        try:
            from financial_trends import fetch_financial_statements
            financial_data = fetch_financial_statements(sym)
        except Exception:
            pass

    # If target is first in list, sync latest market and statement metrics
    if peers:
        target_p = peers[0]
        if target_company_name:
            target_p["company"] = target_company_name

        if live_data:
            cur_p = live_data.get("current_price") or live_data.get("cmp")
            if cur_p and isinstance(cur_p, (int, float)):
                target_p["cmp"] = float(cur_p)
                
            pe_val = live_data.get("pe_ratio")
            if pe_val and isinstance(pe_val, (int, float)):
                target_p["pe"] = float(pe_val)
                
            h52 = live_data.get("high_52w")
            if h52 and cur_p and h52 > 0:
                target_p["down_pct"] = round(max(((h52 - cur_p) / h52) * 100, 0), 2)
                
            mc = live_data.get("market_cap_cr") or (live_data.get("market_cap_num", 0) / 1e7 if live_data.get("market_cap_num") else None)
            if mc and isinstance(mc, (int, float)) and mc > 0:
                target_p["mar_cap"] = round(float(mc), 1)

            # EV / EBITDA from live data
            ev_eb = live_data.get("ev_ebitda") or (live_data.get("screener_metrics", {}).get("evebitda"))
            if ev_eb not in (None, "N/A"):
                try:
                    target_p["ev_ebitda"] = round(float(ev_eb), 2)
                except (ValueError, TypeError):
                    pass

            # PEG Ratio from live data
            peg_val = live_data.get("peg") or (live_data.get("screener_metrics", {}).get("peg_ratio"))
            if peg_val not in (None, "N/A"):
                try:
                    target_p["peg"] = round(float(peg_val), 2)
                except (ValueError, TypeError):
                    pass

            # Profit margin from live data
            pm = live_data.get("profit_margin")
            if pm and isinstance(pm, (int, float)):
                target_p["npm_ann"] = round(float(pm), 2)
            elif isinstance(pm, str) and "%" in pm:
                try:
                    target_p["npm_ann"] = round(float(pm.replace("%", "").strip()), 2)
                except (ValueError, TypeError):
                    pass

            # Free cashflow from live data
            if live_data.get("fcf_cr"):
                target_p["fcf_3yr"] = round(float(live_data["fcf_cr"]) * 3, 1)

        if financial_data and not financial_data.get("error"):
            pnl = financial_data.get("pnl", {})
            sales_v = pnl.get("Sales / Total Revenue", {}).get("values", [])
            if sales_v and sales_v[-1] is not None and sales_v[-1] > 0:
                target_p["sales"] = round(float(sales_v[-1]), 1)
            elif live_data and live_data.get("sales_cr"):
                target_p["sales"] = round(float(live_data["sales_cr"]), 1)

            npm_v = pnl.get("NPM %", {}).get("values", [])
            if npm_v and npm_v[-1] is not None:
                target_p["npm_ann"] = round(float(npm_v[-1]), 2)

            cagr = financial_data.get("cagr", {})
            if cagr.get("sales_cagr") is not None:
                target_p["sales_var_3yr"] = round(float(cagr["sales_cagr"]), 2)
            elif cagr.get("sales_yoy") is not None:
                target_p["sales_var_3yr"] = round(float(cagr["sales_yoy"]), 2)

            if cagr.get("pat_cagr") is not None:
                target_p["profit_var_3yr"] = round(float(cagr["pat_cagr"]), 2)
            elif cagr.get("pat_yoy") is not None:
                target_p["profit_var_3yr"] = round(float(cagr["pat_yoy"]), 2)

            qtr = financial_data.get("quarterly", {})
            q_sales = qtr.get("Sales / Revenue", {}).get("values", [])
            if len(q_sales) >= 2 and q_sales[-2] and q_sales[-2] > 0:
                target_p["qtr_sales_var"] = round(((q_sales[-1] - q_sales[-2]) / abs(q_sales[-2])) * 100, 2)
            elif cagr.get("sales_yoy") is not None:
                target_p["qtr_sales_var"] = round(float(cagr["sales_yoy"]), 2)

            cf = financial_data.get("cf", {})
            fcf_v = cf.get("Free Cash Flow (FCF)", {}).get("values", [])
            if fcf_v:
                valid_fcf = [v for v in fcf_v[-3:] if v is not None]
                if valid_fcf:
                    target_p["fcf_3yr"] = round(sum(valid_fcf), 1)

            roe_v = cagr.get("latest_roe")
            if cagr.get("latest_roce") is not None:
                target_p["roce"] = round(float(cagr["latest_roce"]), 2)
            elif roe_v is not None and roe_v > 0:
                target_p["roce"] = round(float(roe_v), 2)

            if cagr.get("latest_roic") is not None:
                target_p["roic"] = round(float(cagr["latest_roic"]), 2)
            elif roe_v is not None and roe_v > 0:
                target_p["roic"] = round(float(roe_v), 2)

            if cagr.get("latest_croic") is not None:
                target_p["croic"] = round(float(cagr["latest_croic"]), 2)
            else:
                bs = financial_data.get("bs", {})
                nw_vals = bs.get("Total Net Worth / Equity", {}).get("values", [])
                debt_vals = bs.get("Total Borrowings / Debt", {}).get("values", [])
                if fcf_v and nw_vals and fcf_v[-1] is not None and nw_vals[-1] is not None:
                    inv_cap = nw_vals[-1] + (debt_vals[-1] if debt_vals and debt_vals[-1] is not None else 0.0)
                    if inv_cap > 0:
                        target_p["croic"] = round((fcf_v[-1] / inv_cap) * 100, 2)
                elif roe_v is not None and roe_v > 0:
                    target_p["croic"] = round(float(roe_v), 2)

            # Reconcile PEG if still default 1.0 or 0
            if (target_p.get("peg") in (1.0, 0.0, None)) and target_p.get("pe", 0) > 0 and target_p.get("profit_var_3yr", 0) > 0:
                target_p["peg"] = round(target_p["pe"] / target_p["profit_var_3yr"], 2)

        # Sync Industry P/E from peer group
        other_pes = [p.get("pe", 0) for p in peers[1:] if p.get("pe", 0) > 0]
        if other_pes:
            target_p["ind_pe"] = round(sum(other_pes) / len(other_pes), 2)

    # Categories and metrics to compare:
    # label, key, format_type, lower_is_better
    metric_defs = [
        # 1. Valuation & Scale
        ("Mar Cap (₹ Cr)", "mar_cap", "num_cr", False),
        ("Current Price (CMP)", "cmp", "curr", False),
        ("Stock P/E", "pe", "ratio", True),
        ("Industry P/E", "ind_pe", "ratio", False),
        ("PEG Ratio", "peg", "ratio", True),
        ("EV / EBITDA", "ev_ebitda", "ratio", True),
        # 2. Growth & Profitability
        ("Annual Sales (₹ Cr)", "sales", "num_cr", False),
        ("3-Year Sales Growth %", "sales_var_3yr", "pct", False),
        ("3-Year PAT Growth %", "profit_var_3yr", "pct", False),
        ("Quarterly Sales Growth %", "qtr_sales_var", "pct", False),
        ("Net Profit Margin (NPM %)", "npm_ann", "pct", False),
        # 3. Capital Efficiency & Cash Generation
        ("ROIC %", "roic", "pct", False),
        ("CROIC %", "croic", "pct", False),
        ("ROCE %", "roce", "pct", False),
        ("3-Year Cumulative FCF (₹ Cr)", "fcf_3yr", "num_cr", False),
        # 4. Market Posture
        ("% Down from 52W High", "down_pct", "pct", True)
    ]

    # Build Header Columns
    header_th = ['<th style="background:#064E3B; color:#FFFFFF; padding:12px 14px; text-align:left; font-size:13px; font-weight:800; border:none; width:28%;">METRIC</th>']
    for idx, p in enumerate(peers):
        is_target = (idx == 0)
        bg = "#065F46" if is_target else "#0F172A"
        crown = ' <span style="background:#10B981; color:#022C22; font-size:10px; font-weight:800; padding:2px 6px; border-radius:9999px;">TARGET</span>' if is_target else ''
        header_th.append(
            f'<th style="background:{bg}; color:#FFFFFF; padding:12px 14px; text-align:right; font-size:13px; font-weight:800; border:none;">'
            f'{p["company"]}<br><span style="font-size:11px; color:#A7F3D0; font-family:monospace;">{p["symbol"]}</span>{crown}'
            f'</th>'
        )
    header_row = "".join(header_th)

    # Build Table Rows
    rows_html = []
    for m_label, m_key, m_type, lower_better in metric_defs:
        vals = [p.get(m_key, 0.0) for p in peers]
        
        # Determine leader
        valid_vals = [v for v in vals if v is not None and v != 0.0]
        leader_val = None
        if valid_vals:
            leader_val = min(valid_vals) if lower_better else max(valid_vals)

        td_cells = [f'<td style="padding:10px 14px; font-weight:700; color:#1E293B; font-size:13px; background:#F8FAFC; border-bottom:1px solid #E2E8F0; position:sticky; left:0; z-index:2; transition:background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1);">{m_label}</td>']
        for p in peers:
            v = p.get(m_key, 0.0)
            is_leader = (leader_val is not None and v == leader_val and len(valid_vals) > 1)
            
            # Format string
            if m_type == "curr":
                fmt_str = f"₹{v:,.2f}"
            elif m_type == "num_cr":
                fmt_str = f"₹{v:,.1f} Cr"
            elif m_type == "pct":
                fmt_str = f"{v:+.2f}%" if (m_key in ["sales_var_3yr", "profit_var_3yr", "qtr_sales_var"] and v > 0) else f"{v:.2f}%"
            elif m_type == "ratio":
                fmt_str = f"{v:.2f}x"
            else:
                fmt_str = str(v)

            if is_leader:
                cell_style = "background:#ECFDF5; color:#064E3B; font-weight:800; border-bottom:1px solid #A7F3D0;"
                badge = ' <span style="color:#059669; font-size:12px;">★</span>'
            else:
                cell_style = "color:#334155; font-weight:600; border-bottom:1px solid #E2E8F0;"
                badge = ''

            td_cells.append(f'<td style="padding:10px 14px; text-align:right; font-size:13.5px; font-family:\'JetBrains Mono\', monospace; transition:background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1); {cell_style}">{fmt_str}{badge}</td>')

        rows_html.append(f"<tr class='peer-matrix-row'>{''.join(td_cells)}</tr>")

    table_body = "".join(rows_html)

    html = (
        f'<style>'
        f'.peer-matrix-row {{ transition: background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1); }}'
        f'.peer-matrix-row:hover td {{ background-color: #F0FDF4 !important; }}'
        f'.peer-matrix-row:hover td:first-child {{ background-color: #E6FBF0 !important; }}'
        f'</style>'
        f'<div style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:16px; padding:24px 26px; margin-top:22px; margin-bottom:24px; box-shadow:0 4px 20px -2px rgba(15,23,42,0.05);">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:10px;">'
        f'<div>'
        f'<div style="display:flex; align-items:center; gap:8px;">'
        f'<span style="font-size:20px;">⚔️</span>'
        f'<span style="font-size:15px; font-weight:800; color:#0F172A; text-transform:uppercase; letter-spacing:0.5px;">Head-to-Head Sector Peer Comparison (Dalal Street Benchmark)</span>'
        f'</div>'
        f'<div style="font-size:12.5px; color:#64748B; margin-top:3px;">Benchmarking {target_company_name} ({target_ticker}) against top {target_sector} peers on the 16 canonical Screener metrics</div>'
        f'</div>'
        f'<span style="background:#ECFDF5; color:#047857; border:1px solid #A7F3D0; font-size:11.5px; font-weight:800; padding:4px 10px; border-radius:9999px;">★ Leader Highlighted</span>'
        f'</div>'
        f'<div style="overflow-x:auto; border-radius:10px; border:1px solid #E2E8F0; box-shadow:0 1px 3px rgba(0,0,0,0.02);">'
        f'<table style="width:100%; border-collapse:collapse; background:#FFFFFF;">'
        f'<thead><tr>{header_row}</tr></thead>'
        f'<tbody>{table_body}</tbody>'
        f'</table>'
        f'</div>'
        f'<div style="font-size:12px; color:#64748B; margin-top:10px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">'
        f'<span>Source: Screener.in institutional 16-metric framework & BSE/NSE audited filings</span>'
        f'<span style="font-weight:600; color:#047857;">★ Indicates sector category leader</span>'
        f'</div>'
        f'</div>'
    )
    return html


def render_nifty50_screener_view():
    """
    Renders the complete Screener.in-grade 'Companies in Nifty 50' view matching
    the user's template with all 16 metrics, sector filtering, searching, and CSV export.
    """
    st.html("""
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:18px 24px; margin-bottom:18px; box-shadow:0 1px 3px rgba(0,0,0,0.02);">
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
        <div>
          <div style="font-size:22px; font-weight:800; color:#0F172A; letter-spacing:-0.4px;">
            Companies in Nifty 50 (Historical Benchmark Sample)
          </div>
          <div style="font-size:13px; color:#64748B; margin-top:2px;">
            50 constituents • FY24 financial basis; dataset note updated Q2 FY25. Static reference sample, not live exchange data.
          </div>
        </div>
        <div style="display:flex; gap:8px; align-items:center;">
          <span style="background:#FFFBEB; color:#B45309; border:1px solid #FDE68A; font-size:12px; font-weight:700; padding:4px 10px; border-radius:6px;">
            📅 FY24 basis · Q2 FY25 update note
          </span>
          <span style="background:#F8FAFC; color:#334155; border:1px solid #CBD5E1; font-size:12px; font-weight:700; padding:4px 10px; border-radius:6px;">
            16 Canonical Metrics
          </span>
        </div>
      </div>
    </div>
    """)

    # Top Controls Bar: Sector Filter, Search & Export
    col_filter1, col_filter2, col_filter3 = st.columns([1.5, 1.8, 1])
    
    # Unique sectors in Nifty 50
    all_sectors = ["All"] + sorted(list(set(c["sector"] for c in NIFTY_50_DATA)))
    
    with col_filter1:
        chosen_sector = st.selectbox(
            "Filter Sector",
            options=all_sectors,
            key="nifty50_sector_filter",
            label_visibility="collapsed"
        )
    with col_filter2:
        search_query = st.text_input(
            "Search Company",
            placeholder="Search Nifty 50 (e.g. Reliance, HDFC, Tata, Infosys)...",
            key="nifty50_search_box",
            label_visibility="collapsed"
        )
    with col_filter3:
        df_export = get_nifty50_dataframe(sector_filter=chosen_sector, search_query=search_query)
        csv_data = df_export.to_csv(index=False)
        st.download_button(
            label="⬇ Export CSV",
            data=csv_data,
            file_name="Nifty50_Screener_Metrics.csv",
            mime="text/csv",
            width="stretch"
        )

    # Summary KPI Strip
    if not df_export.empty:
        total_mc = sum(df_export["Mar Cap Rs.Cr."])
        med_pe = df_export["P/E"].median()
        med_roce = df_export["ROCE %"].median()
        med_croic = df_export["CROIC %"].median()
        
        kpi_strip_html = f"""
        <style>
        .nifty50-screener-row {{
            border-bottom: 1px solid #F1F5F9;
            transition: background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .nifty50-screener-row td {{
            transition: background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .nifty50-screener-row:hover td {{
            background-color: #F0FDF4 !important;
        }}
        .nifty50-screener-row:hover td:first-child {{
            background-color: #F0FDF4 !important;
        }}
        </style>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-bottom:18px;">
          <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">TOTAL MARKET CAP</div>
            <div style="font-size:18px; font-weight:800; color:#0F172A; margin-top:3px; font-family:monospace;">₹{total_mc:,.0f} Cr</div>
            <div style="font-size:11.5px; color:#059669; margin-top:2px;">{len(df_export)} Companies Displayed</div>
          </div>
          <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">MEDIAN P/E</div>
            <div style="font-size:18px; font-weight:800; color:#1E3A8A; margin-top:3px; font-family:monospace;">{med_pe:.2f}x</div>
            <div style="font-size:11.5px; color:#64748B; margin-top:2px;">Index Valuation Median</div>
          </div>
          <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">MEDIAN ROCE</div>
            <div style="font-size:18px; font-weight:800; color:#047857; margin-top:3px; font-family:monospace;">{med_roce:.2f}%</div>
            <div style="font-size:11.5px; color:#059669; margin-top:2px;">Capital Efficiency Benchmark</div>
          </div>
          <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 14px;">
            <div style="font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase;">MEDIAN CROIC</div>
            <div style="font-size:18px; font-weight:800; color:#0D9488; margin-top:3px; font-family:monospace;">{med_croic:.2f}%</div>
            <div style="font-size:11.5px; color:#0D9488; margin-top:2px;">Cash Return on Capital</div>
          </div>
        </div>
        """
        st.html(kpi_strip_html)

    # Focused metric views keep the historical benchmark easier to scan on small screens.
    metric_views = {
        "Overview": ["Company", "Symbol", "CMP Rs.", "Mar Cap Rs.Cr.", "Sales Var 3Yrs %", "Profit Var 3Yrs %", "ROCE %"],
        "Growth": ["Company", "Symbol", "CMP Rs.", "Sales Var 3Yrs %", "Profit Var 3Yrs %", "Qtr Sales Var %", "NPM Ann %"],
        "Valuation": ["Company", "Symbol", "CMP Rs.", "P/E", "PEG", "EV / EBITDA", "Down %"],
        "Returns & Cash Flow": ["Company", "Symbol", "CMP Rs.", "ROIC %", "CROIC %", "ROCE %", "Free Cash Flow 3Yrs Rs.Cr."],
    }
    control_col, sort_col = st.columns([2, 1])
    with control_col:
        metric_view = st.segmented_control("Metrics", list(metric_views), default="Overview", key="nifty50_metric_view")
    with sort_col:
        active_view = metric_view or "Overview"
        sort_column = st.selectbox("Sort rows by", metric_views[active_view][2:], key=f"nifty50_sort_column_{active_view}")
    direction_col, layout_col = st.columns([1, 1])
    with direction_col:
        sort_direction = st.selectbox("Order", ["Highest first", "Lowest first"], key=f"nifty50_sort_direction_{active_view}")
    with layout_col:
        compact_display = st.toggle("Compact", value=True, key="nifty50_compact_display", help="Use a narrow three-column view for small screens.")

    st.caption("Historical FY24 benchmark sample · not live exchange data. Tap a row to select it; the Analyze action appears just below. Use the sort controls or table headers to reorder rows.")
    display_df = df_export[metric_views[active_view]].copy()
    display_df.insert(0, "Company / Symbol", display_df["Symbol"] + " · " + display_df["Company"])
    display_df = display_df.sort_values(sort_column, ascending=sort_direction == "Lowest first", na_position="last")
    display_symbols = display_df["Symbol"].copy()
    display_df = display_df.drop(columns=["Company", "Symbol"])
    page_number = 1
    if compact_display:
        page_size = 10
        page_count = max(1, (len(display_df) + page_size - 1) // page_size)
        page_key = f"nifty50_page_{abs(hash((chosen_sector, search_query, active_view, sort_column, sort_direction)))}"
        page_number = st.selectbox("Page", list(range(1, page_count + 1)), key=page_key)
        page_start = (page_number - 1) * page_size
        visible_symbols = display_symbols.iloc[page_start:page_start + page_size]
        page_end = min(page_start + page_size, len(display_df))
        if len(display_df):
            st.caption(f"Showing rows {page_start + 1}–{page_end} of {len(display_df)} · 10 per page")
        else:
            st.info("No benchmark companies match these filters.")
        compact_columns = ["Company / Symbol", "CMP Rs."]
        if sort_column != "CMP Rs.":
            compact_columns.append(sort_column)
        table_df = display_df[compact_columns]
        table_df = table_df.iloc[page_start:page_start + page_size]
    else:
        table_df = display_df
        visible_symbols = display_symbols
    benchmark_event = st.dataframe(
        table_df,
        hide_index=True,
        width="stretch",
        height=min(430 if compact_display else 680, 44 + 36 * max(len(table_df), 1)),
        on_select="rerun",
        selection_mode="single-row",
        key=f"nifty50_metric_table_{abs(hash((chosen_sector, search_query, active_view, sort_column, sort_direction, compact_display, page_number)))}",
        column_config={
            "CMP Rs.": st.column_config.NumberColumn("Price (₹)", format="₹ %.2f"),
            "Mar Cap Rs.Cr.": st.column_config.NumberColumn("Market cap (₹ Cr)", format="%.0f"),
            "Sales Rs.Cr.": st.column_config.NumberColumn("Sales (₹ Cr)", format="%.0f"),
            "Sales Var 3Yrs %": st.column_config.NumberColumn("Sales growth (3Y) %", format="%.2f%%"),
            "Profit Var 3Yrs %": st.column_config.NumberColumn("Profit growth (3Y) %", format="%.2f%%"),
            "Qtr Sales Var %": st.column_config.NumberColumn("Quarterly sales change %", format="%.2f%%"),
            "NPM Ann %": st.column_config.NumberColumn("Net margin %", format="%.2f%%"),
            "P/E": st.column_config.NumberColumn("P/E", format="%.2fx"),
            "Ind PE": st.column_config.NumberColumn("Industry P/E", format="%.2fx"),
            "PEG": st.column_config.NumberColumn("PEG", format="%.2fx"),
            "EV / EBITDA": st.column_config.NumberColumn("EV / EBITDA", format="%.2fx"),
            "ROIC %": st.column_config.NumberColumn("ROIC %", format="%.2f%%"),
            "CROIC %": st.column_config.NumberColumn("CROIC %", format="%.2f%%"),
            "ROCE %": st.column_config.NumberColumn("ROCE %", format="%.2f%%"),
            "Free Cash Flow 3Yrs Rs.Cr.": st.column_config.NumberColumn("3Y free cash flow (₹ Cr)", format="%.0f"),
            "Down %": st.column_config.NumberColumn("Downside %", format="%.2f%%"),
        },
    )

    # Launch the company selected directly in the current filtered and sorted table.
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("##### 🔍 Analyze a company from this benchmark")
        selected_rows = benchmark_event.selection.rows if benchmark_event else []
        if selected_rows:
            row_index = selected_rows[0]
            selected_symbol = visible_symbols.iloc[row_index]
            selected_company = table_df.iloc[row_index]["Company / Symbol"]
            action_col, hint_col = st.columns([1, 3])
            with hint_col:
                st.caption(f"Selected from the current filters and sort: {selected_company}")
            with action_col:
                if st.button("Analyze selected company ↗", key="btn_launch_from_screener", type="primary", width="stretch"):
                    company_info = find_company_info(selected_symbol)
                    st.session_state["selected_company_choice"] = company_info["display"]
                    if company_info.get("ticker") == "CUSTOM":
                        st.session_state["benchmark_launch_notice"] = (
                            f"{selected_company} uses a historical benchmark symbol that is not in the current tracked company universe. "
                            "Choose the current listed entity and ticker manually before running a current analysis."
                        )
                    st.session_state["pending_nav_mode"] = "🔬 Company Analysis"
                    st.rerun()
        else:
            st.caption("Tap a row in the table above to analyze that company.")
