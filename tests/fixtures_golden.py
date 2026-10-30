"""
tests/fixtures_golden.py
Deterministic Golden Company Fixtures for End-to-End Regression Testing.
Contains 5 pure-dict fixtures representing distinct corporate archetypes:
1. CLEAN_LARGECAP: Consistent multi-year growth, positive CFO > PAT, low debt, 0% pledge, unqualified auditor.
2. LOSS_MAKER: Negative PAT in latest 2 years, negative operating cash flow, shrinking sales.
3. HIGH_PLEDGE: Encumbered promoter holding (45% pledge), otherwise solvent.
4. CHANNEL_STUFFING: Flat revenue with aggressive 40% YoY receivables expansion and diverging CFO.
5. EMPTY: Completely absent financial statements and live market data.
"""

CLEAN_LARGECAP = {
    "ticker": "CLEANLARGECAP",
    "company_name": "Titanium Bluechip Corp",
    "sector": "Consumer Goods",
    "financials": {
        "years": ["FY21", "FY22", "FY23", "FY24"],
        "pnl": {
            "Sales / Total Revenue": {"values": [10000.0, 11500.0, 13200.0, 15000.0]},
            "Profit Before Tax (PBT)": {"values": [1800.0, 2100.0, 2500.0, 3000.0]},
            "Tax Provision": {"values": [450.0, 525.0, 625.0, 750.0]},
            "Net Profit (PAT)": {"values": [1350.0, 1575.0, 1875.0, 2250.0]},
            "Other Income": {"values": [50.0, 60.0, 70.0, 80.0]}
        },
        "bs": {
            "Fixed Assets (Net PPE)": {"values": [3500.0, 4000.0, 4500.0, 5000.0]},
            "Capital WIP": {"values": [100.0, 120.0, 140.0, 160.0]},
            "Trade Receivables": {"values": [800.0, 900.0, 1020.0, 1150.0]},
            "Current & Other Assets": {"values": [3000.0, 3400.0, 3900.0, 4400.0]},
            "Borrowings / Total Debt": {"values": [300.0, 250.0, 200.0, 150.0]},
            "Total Equity": {"values": [5000.0, 6200.0, 7800.0, 9500.0]}
        },
        "cf": {
            "Cash from Operations (CFO)": {"values": [1500.0, 1800.0, 2200.0, 2600.0]},
            "Free Cash Flow (FCF)": {"values": [1100.0, 1300.0, 1600.0, 1950.0]}
        },
        "cagr": {
            "sales_cagr": 14.5,
            "pat_cagr": 18.6,
            "latest_roe": 23.7
        }
    },
    "market_data": {
        "current_price": 2850.0,
        "market_cap_cr": 145000.0,
        "pe_ratio": 32.0,
        "debt_to_equity": 0.02,
        "screener_metrics": {
            "promoter_pledging": "0.0%",
            "debt_to_equity": "0.02"
        },
        "promoter_pledge_pct": 0.0,
        "auditor_opinion": "Unqualified / Clean Opinion (No CARO modifications)"
    },
    "raw_analysis": {
        "pillars": [
            {"id": 1, "name": "Governance & Capital Allocation", "score": 19.0},
            {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 19.5},
            {"id": 3, "name": "Risk, ESG & Fragility", "score": 11.5},
            {"id": 4, "name": "Valuation & Sanity Layer", "score": 4.5},
            {"id": 5, "name": "Strategic Moat & Pricing Power", "score": 14.0},
            {"id": 6, "name": "Capital Efficiency & Reinvestment", "score": 9.5},
            {"id": 7, "name": "Industry Dynamics & Runway", "score": 9.5},
            {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 5.8}
        ],
        "guardrail_tag": "GOV-CLEAN 🟢",
        "pio_triggered": False,
        "penalties_breakdown": [],
        "bonuses_breakdown": {"cool_pro_bonus": 4.0, "trajectory_bonus": 2.0}
    }
}

LOSS_MAKER = {
    "ticker": "LOSSMAKER",
    "company_name": "Bleeding Tech Holdings",
    "sector": "Information Technology",
    "financials": {
        "years": ["FY21", "FY22", "FY23", "FY24"],
        "pnl": {
            "Sales / Total Revenue": {"values": [1200.0, 1050.0, 900.0, 750.0]},
            "Profit Before Tax (PBT)": {"values": [40.0, 10.0, -180.0, -320.0]},
            "Tax Provision": {"values": [10.0, 2.0, 0.0, 0.0]},
            "Net Profit (PAT)": {"values": [30.0, 8.0, -180.0, -320.0]},
            "Other Income": {"values": [5.0, 4.0, 3.0, 2.0]}
        },
        "bs": {
            "Fixed Assets (Net PPE)": {"values": [400.0, 380.0, 350.0, 310.0]},
            "Capital WIP": {"values": [20.0, 15.0, 10.0, 5.0]},
            "Trade Receivables": {"values": [250.0, 260.0, 280.0, 310.0]},
            "Current & Other Assets": {"values": [500.0, 450.0, 400.0, 350.0]},
            "Borrowings / Total Debt": {"values": [300.0, 450.0, 600.0, 850.0]},
            "Total Equity": {"values": [400.0, 350.0, 150.0, -120.0]}
        },
        "cf": {
            "Cash from Operations (CFO)": {"values": [15.0, -20.0, -150.0, -280.0]},
            "Free Cash Flow (FCF)": {"values": [-30.0, -60.0, -190.0, -310.0]}
        },
        "cagr": {
            "sales_cagr": -14.5,
            "pat_cagr": -45.0,
            "latest_roe": -65.0
        }
    },
    "market_data": {
        "current_price": 42.0,
        "market_cap_cr": 850.0,
        "pe_ratio": -3.5,
        "debt_to_equity": 4.5,
        "screener_metrics": {
            "promoter_pledging": "12.5%",
            "debt_to_equity": "4.5"
        },
        "promoter_pledge_pct": 12.5,
        "auditor_opinion": "Qualified Opinion (Going Concern Emphasis of Matter)"
    },
    "raw_analysis": {
        "pillars": [
            {"id": 1, "name": "Governance & Capital Allocation", "score": 6.0},
            {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 4.0},
            {"id": 3, "name": "Risk, ESG & Fragility", "score": 2.0},
            {"id": 4, "name": "Valuation & Sanity Layer", "score": 1.0},
            {"id": 5, "name": "Strategic Moat & Pricing Power", "score": 3.0},
            {"id": 6, "name": "Capital Efficiency & Reinvestment", "score": 2.0},
            {"id": 7, "name": "Industry Dynamics & Runway", "score": 3.0},
            {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 2.0}
        ],
        "guardrail_tag": "GOV-ALERT 🟡",
        "pio_triggered": False,
        "penalties_breakdown": [
            {"penalty_name": "Severe Cash Burn", "points": -5.0, "reason": "Persistent negative CFO and PAT destruction"},
            {"penalty_name": "Over-leverage", "points": -2.5, "reason": "High D/E > 4.0 with negative net worth"}
        ],
        "bonuses_breakdown": {}
    }
}

HIGH_PLEDGE = {
    "ticker": "HIGHPLEDGE",
    "company_name": "Promoter Encumbered Infra Ltd",
    "sector": "Infrastructure",
    "financials": {
        "years": ["FY21", "FY22", "FY23", "FY24"],
        "pnl": {
            "Sales / Total Revenue": {"values": [4000.0, 4600.0, 5200.0, 6000.0]},
            "Profit Before Tax (PBT)": {"values": [600.0, 720.0, 850.0, 980.0]},
            "Tax Provision": {"values": [150.0, 180.0, 210.0, 245.0]},
            "Net Profit (PAT)": {"values": [450.0, 540.0, 640.0, 735.0]},
            "Other Income": {"values": [20.0, 25.0, 30.0, 35.0]}
        },
        "bs": {
            "Fixed Assets (Net PPE)": {"values": [2000.0, 2300.0, 2600.0, 2900.0]},
            "Capital WIP": {"values": [250.0, 300.0, 350.0, 400.0]},
            "Trade Receivables": {"values": [500.0, 560.0, 620.0, 700.0]},
            "Current & Other Assets": {"values": [1500.0, 1700.0, 1900.0, 2200.0]},
            "Borrowings / Total Debt": {"values": [1200.0, 1300.0, 1400.0, 1500.0]},
            "Total Equity": {"values": [2200.0, 2600.0, 3100.0, 3700.0]}
        },
        "cf": {
            "Cash from Operations (CFO)": {"values": [480.0, 580.0, 690.0, 790.0]},
            "Free Cash Flow (FCF)": {"values": [200.0, 250.0, 300.0, 360.0]}
        },
        "cagr": {
            "sales_cagr": 14.5,
            "pat_cagr": 17.8,
            "latest_roe": 19.8
        }
    },
    "market_data": {
        "current_price": 310.0,
        "market_cap_cr": 12500.0,
        "pe_ratio": 17.0,
        "debt_to_equity": 0.41,
        "screener_metrics": {
            "promoter_pledging": "45.00%",
            "debt_to_equity": "0.41"
        },
        "promoter_pledge_pct": 45.0,
        "auditor_opinion": "Unqualified Opinion"
    },
    "raw_analysis": {
        "pillars": [
            {"id": 1, "name": "Governance & Capital Allocation", "score": 11.0},
            {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 15.0},
            {"id": 3, "name": "Risk, ESG & Fragility", "score": 5.0},
            {"id": 4, "name": "Valuation & Sanity Layer", "score": 3.0},
            {"id": 5, "name": "Strategic Moat & Pricing Power", "score": 9.0},
            {"id": 6, "name": "Capital Efficiency & Reinvestment", "score": 6.5},
            {"id": 7, "name": "Industry Dynamics & Runway", "score": 7.0},
            {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 2.0}
        ],
        "guardrail_tag": "PROM-ALERT 🟡",
        "pio_triggered": False,
        "penalties_breakdown": [
            {"penalty_name": "Promoter Encumbrance Risk", "points": -4.0, "reason": "45% promoter stake encumbered"}
        ],
        "bonuses_breakdown": {}
    }
}

CHANNEL_STUFFING = {
    "ticker": "CHANNELSTUFF",
    "company_name": "Aggressive Distributor Ltd",
    "sector": "Consumer Discretionary",
    "financials": {
        "years": ["FY21", "FY22", "FY23", "FY24"],
        "pnl": {
            "Sales / Total Revenue": {"values": [3000.0, 3050.0, 3020.0, 3010.0]},  # Flat revenue
            "Profit Before Tax (PBT)": {"values": [350.0, 360.0, 370.0, 380.0]},
            "Tax Provision": {"values": [90.0, 92.0, 95.0, 98.0]},
            "Net Profit (PAT)": {"values": [260.0, 268.0, 275.0, 282.0]},
            "Other Income": {"values": [10.0, 12.0, 15.0, 18.0]}
        },
        "bs": {
            "Fixed Assets (Net PPE)": {"values": [800.0, 820.0, 840.0, 860.0]},
            "Capital WIP": {"values": [20.0, 20.0, 20.0, 20.0]},
            "Trade Receivables": {"values": [400.0, 500.0, 700.0, 980.0]},  # Receivables growing 40% YoY
            "Current & Other Assets": {"values": [900.0, 1100.0, 1400.0, 1960.0]},
            "Borrowings / Total Debt": {"values": [200.0, 350.0, 600.0, 950.0]},
            "Total Equity": {"values": [1200.0, 1350.0, 1480.0, 1600.0]}
        },
        "cf": {
            "Cash from Operations (CFO)": {"values": [240.0, 120.0, -50.0, -180.0]},  # Diverging CFO
            "Free Cash Flow (FCF)": {"values": [180.0, 60.0, -110.0, -240.0]}
        },
        "cagr": {
            "sales_cagr": 0.1,
            "pat_cagr": 2.7,
            "latest_roe": 17.6
        }
    },
    "market_data": {
        "current_price": 180.0,
        "market_cap_cr": 4500.0,
        "pe_ratio": 16.0,
        "debt_to_equity": 0.59,
        "screener_metrics": {
            "promoter_pledging": "0.0%",
            "debt_to_equity": "0.59"
        },
        "promoter_pledge_pct": 0.0,
        "auditor_opinion": "Unqualified Opinion"
    },
    "raw_analysis": {
        "pillars": [
            {"id": 1, "name": "Governance & Capital Allocation", "score": 10.0},
            {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 5.0},
            {"id": 3, "name": "Risk, ESG & Fragility", "score": 5.0},
            {"id": 4, "name": "Valuation & Sanity Layer", "score": 2.5},
            {"id": 5, "name": "Strategic Moat & Pricing Power", "score": 6.0},
            {"id": 6, "name": "Capital Efficiency & Reinvestment", "score": 4.0},
            {"id": 7, "name": "Industry Dynamics & Runway", "score": 5.0},
            {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 3.0}
        ],
        "guardrail_tag": "PROM-ALERT 🟡",
        "pio_triggered": False,
        "penalties_breakdown": [
            {"penalty_name": "Channel Stuffing / Uncollected Sales", "points": -5.0, "reason": "Receivables surge +40% with negative CFO"}
        ],
        "bonuses_breakdown": {}
    }
}

EMPTY = {
    "ticker": "EMPTYCORP",
    "company_name": "Unverified Shell Corp",
    "sector": "Other",
    "financials": None,
    "market_data": None,
    "raw_analysis": {
        "pillars": [
            {"id": 1, "name": "Governance & Capital Allocation", "score": 0.0},
            {"id": 2, "name": "Forensic Accounting & Cash Flow", "score": 0.0},
            {"id": 3, "name": "Risk, ESG & Fragility", "score": 0.0},
            {"id": 4, "name": "Valuation & Sanity Layer", "score": 0.0},
            {"id": 5, "name": "Strategic Moat & Pricing Power", "score": 0.0},
            {"id": 6, "name": "Capital Efficiency & Reinvestment", "score": 0.0},
            {"id": 7, "name": "Industry Dynamics & Runway", "score": 0.0},
            {"id": 8, "name": "Insider & Minority Shareholder Risk", "score": 0.0}
        ],
        "guardrail_tag": "GOV-ALERT 🟡",
        "pio_triggered": False,
        "penalties_breakdown": [],
        "bonuses_breakdown": {}
    }
}
