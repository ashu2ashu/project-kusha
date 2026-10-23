"""
nifty_universe.py
Comprehensive directory of all 501 Nifty 500 listed Indian companies.
Includes automatic industry-to-sector mapping and live market data ingestion.
"""

import os
import pandas as pd
from typing import Dict, Any, Optional, List

CSV_PATH = os.path.join(os.path.dirname(__file__), "nifty500.csv")

INDUSTRY_MAPPING = {
    "Automobile and Auto Components": "Manufacturing / B2B",
    "Capital Goods": "Capital Goods / Industrial",
    "Chemicals": "Chemicals / Oil & Gas",
    "Construction": "Construction / Infra (milestone billing)",
    "Construction Materials": "Manufacturing / B2B",
    "Consumer Durables": "Consumer Durables / Retailer credit",
    "Consumer Services": "FMCG / Retail",
    "Diversified": "Manufacturing / B2B",
    "Fast Moving Consumer Goods": "FMCG / Retail",
    "Financial Services": "Banks / NBFC",
    "Healthcare": "Pharma / Formulations (trade)",
    "Information Technology": "IT Services / Consulting",
    "Media Entertainment & Publication": "SaaS / Subscription (B2B)",
    "Metals & Mining": "Manufacturing / B2B",
    "Oil Gas & Consumable Fuels": "Chemicals / Oil & Gas",
    "Power": "Capital Goods / Industrial",
    "Realty": "Construction / Infra (milestone billing)",
    "Services": "Logistics / Transport",
    "Telecommunication": "Logistics / Transport",
    "Textiles": "Manufacturing / B2B"
}

_cached_nifty_list = None
_cached_lookup = {}

def load_nifty500() -> List[Dict[str, str]]:
    """Loads and caches the complete Nifty 500 universe."""
    global _cached_nifty_list, _cached_lookup
    if _cached_nifty_list is not None:
        return _cached_nifty_list

    companies = []
    _cached_lookup = {}

    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            for _, row in df.iterrows():
                name = str(row.get("Company Name", "")).strip()
                symbol = str(row.get("Symbol", "")).strip()
                industry = str(row.get("Industry", "")).strip()
                sector = INDUSTRY_MAPPING.get(industry, "Manufacturing / B2B")
                
                item = {
                    "name": name,
                    "ticker": symbol,
                    "industry": industry,
                    "sector": sector,
                    "display": f"{name} ({symbol})"
                }
                companies.append(item)
                _cached_lookup[item["display"]] = item
                _cached_lookup[symbol] = item
        except Exception:
            pass

    # Sort alphabetically by company name
    companies.sort(key=lambda x: x["name"])

    # Append Custom / Manual entry option at the end
    custom_item = {
        "name": "Custom / Unlisted / Manual Entry",
        "ticker": "CUSTOM",
        "industry": "Other",
        "sector": "Other / Diversified",
        "display": "Custom / Unlisted / Manual Entry (CUSTOM)"
    }
    companies.append(custom_item)
    _cached_lookup[custom_item["display"]] = custom_item
    _cached_lookup["CUSTOM"] = custom_item

    _cached_nifty_list = companies
    return _cached_nifty_list

def get_company_list() -> List[str]:
    """Returns sorted display strings for UI selection."""
    comp_list = load_nifty500()
    return [c["display"] for c in comp_list]

def find_company_info(display_str: str) -> Dict[str, str]:
    """Finds company metadata from display string or ticker."""
    load_nifty500()
    if display_str in _cached_lookup:
        return _cached_lookup[display_str]
    return {
        "name": display_str,
        "ticker": "CUSTOM",
        "industry": "Other",
        "sector": "FMCG / Retail",
        "display": display_str
    }

def fetch_live_market_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time financial metrics from Yahoo Finance for Indian NSE stocks.
    """
    if not ticker_symbol or ticker_symbol == "CUSTOM":
        return None
        
    try:
        import yfinance as yf
        ns_ticker = f"{ticker_symbol.upper()}.NS"
        stock = yf.Ticker(ns_ticker)
        info = stock.info
        
        if not info or "currentPrice" not in info:
            stock = yf.Ticker(f"{ticker_symbol.upper()}.BO")
            info = stock.info
            
        if not info or "currentPrice" not in info:
            return None
            
        mcap_cr = round(info.get("marketCap", 0) / 1e7, 1) if info.get("marketCap") else "N/A"
        pe_val = round(info.get("trailingPE", 0), 1) if info.get("trailingPE") else "N/A"
        fwd_pe = round(info.get("forwardPE", 0), 1) if info.get("forwardPE") else "N/A"
        high52 = info.get("fiftyTwoWeekHigh", "N/A")
        low52 = info.get("fiftyTwoWeekLow", "N/A")
        cur_price = info.get("currentPrice", "N/A")
        div_yield = round(info.get("dividendYield", 0) * 100, 2) if info.get("dividendYield") else "0.0%"
        roe_pct = round(info.get("returnOnEquity", 0) * 100, 1) if info.get("returnOnEquity") else "N/A"
        profit_margin = round(info.get("profitMargins", 0) * 100, 1) if info.get("profitMargins") else "N/A"
        debt_to_equity = round(info.get("debtToEquity", 0) / 100, 2) if info.get("debtToEquity") else "N/A"
        
        return {
            "symbol": ticker_symbol,
            "currency": info.get("currency", "INR"),
            "current_price": cur_price,
            "market_cap_cr": mcap_cr,
            "pe_ratio": pe_val,
            "forward_pe": fwd_pe,
            "high_52w": high52,
            "low_52w": low52,
            "dividend_yield": f"{div_yield}%" if isinstance(div_yield, (int, float)) else div_yield,
            "roe": f"{roe_pct}%" if isinstance(roe_pct, (int, float)) else roe_pct,
            "profit_margin": f"{profit_margin}%" if isinstance(profit_margin, (int, float)) else profit_margin,
            "debt_to_equity": debt_to_equity,
            "analyst_rating": info.get("recommendationKey", "N/A").replace("_", " ").title(),
            "business_summary": info.get("longBusinessSummary", "")
        }
    except Exception:
        return None
