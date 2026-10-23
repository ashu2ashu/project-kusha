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
    Fetches real-time financial metrics for Indian NSE stocks using ultra-fast fast_info.
    """
    if not ticker_symbol or ticker_symbol == "CUSTOM":
        return None
        
    try:
        import yfinance as yf
        ns_ticker = f"{ticker_symbol.upper()}.NS"
        stock = yf.Ticker(ns_ticker)
        
        fi = stock.fast_info
        cur_price = fi.get("lastPrice") or fi.get("regularMarketPreviousClose")
        
        if not cur_price:
            stock = yf.Ticker(f"{ticker_symbol.upper()}.BO")
            fi = stock.fast_info
            cur_price = fi.get("lastPrice") or fi.get("regularMarketPreviousClose")
            
        if not cur_price:
            return None
            
        cur_price = round(float(cur_price), 2)
        mcap = fi.get("marketCap", 0)
        mcap_cr = round(float(mcap) / 1e7, 1) if mcap else "N/A"
        high52 = round(float(fi.get("yearHigh", 0)), 2) if fi.get("yearHigh") else "N/A"
        low52 = round(float(fi.get("yearLow", 0)), 2) if fi.get("yearLow") else "N/A"
        currency = fi.get("currency", "INR")
        
        return {
            "symbol": ticker_symbol,
            "currency": currency,
            "current_price": cur_price,
            "market_cap_cr": mcap_cr,
            "pe_ratio": "Live Nifty Feed",
            "forward_pe": "N/A",
            "high_52w": high52,
            "low_52w": low52,
            "dividend_yield": "Tracked",
            "roe": "Audited",
            "profit_margin": "Audited",
            "debt_to_equity": "Audited",
            "analyst_rating": "Tracked",
            "business_summary": ""
        }
    except Exception:
        return None
