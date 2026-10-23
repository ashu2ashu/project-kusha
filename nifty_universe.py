"""
nifty_universe.py
Directory of listed Indian Nifty companies with NSE tickers and sector mappings.
Includes live market data ingestion via Yahoo Finance.
"""

from typing import Dict, Any, Optional

NIFTY_COMPANIES = [
    {"name": "Reliance Industries Ltd", "ticker": "RELIANCE", "sector": "Chemicals / Oil & Gas"},
    {"name": "Tata Consultancy Services Ltd", "ticker": "TCS", "sector": "IT Services / Consulting"},
    {"name": "HDFC Bank Ltd", "ticker": "HDFCBANK", "sector": "Banks / NBFC"},
    {"name": "ICICI Bank Ltd", "ticker": "ICICIBANK", "sector": "Banks / NBFC"},
    {"name": "Infosys Ltd", "ticker": "INFY", "sector": "IT Services / Consulting"},
    {"name": "Hindustan Unilever Ltd", "ticker": "HINDUNILVR", "sector": "FMCG / Retail"},
    {"name": "ITC Ltd", "ticker": "ITC", "sector": "FMCG / Retail"},
    {"name": "State Bank of India", "ticker": "SBIN", "sector": "Banks / NBFC"},
    {"name": "Bharti Airtel Ltd", "ticker": "BHARTIARTL", "sector": "Logistics / Transport"},
    {"name": "Larsen & Toubro Ltd", "ticker": "LT", "sector": "Construction / Infra (milestone billing)"},
    {"name": "Tata Motors Ltd", "ticker": "TATAMOTORS", "sector": "Manufacturing / B2B"},
    {"name": "Tata Consumer Products Ltd", "ticker": "TATACONSUM", "sector": "FMCG / Retail"},
    {"name": "Titan Company Ltd", "ticker": "TITAN", "sector": "Consumer Durables / Retailer credit"},
    {"name": "Sun Pharmaceutical Industries Ltd", "ticker": "SUNPHARMA", "sector": "Pharma / Formulations (trade)"},
    {"name": "Bajaj Finance Ltd", "ticker": "BAJFINANCE", "sector": "Banks / NBFC"},
    {"name": "Maruti Suzuki India Ltd", "ticker": "MARUTI", "sector": "Manufacturing / B2B"},
    {"name": "Mahindra & Mahindra Ltd", "ticker": "M&M", "sector": "Manufacturing / B2B"},
    {"name": "Asian Paints Ltd", "ticker": "ASIANPAINT", "sector": "Consumer Durables / Retailer credit"},
    {"name": "UltraTech Cement Ltd", "ticker": "ULTRACEMCO", "sector": "Manufacturing / B2B"},
    {"name": "NTPC Ltd", "ticker": "NTPC", "sector": "Capital Goods / Industrial"},
    {"name": "Power Grid Corporation of India Ltd", "ticker": "POWERGRID", "sector": "Capital Goods / Industrial"},
    {"name": "Adani Enterprises Ltd", "ticker": "ADANIENT", "sector": "Construction / Infra (milestone billing)"},
    {"name": "Adani Ports and SEZ Ltd", "ticker": "ADANIPORTS", "sector": "Logistics / Transport"},
    {"name": "Coal India Ltd", "ticker": "COALINDIA", "sector": "Chemicals / Oil & Gas"},
    {"name": "Wipro Ltd", "ticker": "WIPRO", "sector": "IT Services / Consulting"},
    {"name": "HCL Technologies Ltd", "ticker": "HCLTECH", "sector": "IT Services / Consulting"},
    {"name": "Bajaj Finserv Ltd", "ticker": "BAJAJFINSV", "sector": "Banks / NBFC"},
    {"name": "Oil & Natural Gas Corporation Ltd", "ticker": "ONGC", "sector": "Chemicals / Oil & Gas"},
    {"name": "Bharat Petroleum Corporation Ltd", "ticker": "BPCL", "sector": "Chemicals / Oil & Gas"},
    {"name": "Grasim Industries Ltd", "ticker": "GRASIM", "sector": "Manufacturing / B2B"},
    {"name": "Hindalco Industries Ltd", "ticker": "HINDALCO", "sector": "Manufacturing / B2B"},
    {"name": "JSW Steel Ltd", "ticker": "JSWSTEEL", "sector": "Manufacturing / B2B"},
    {"name": "Tata Steel Ltd", "ticker": "TATASTEEL", "sector": "Manufacturing / B2B"},
    {"name": "Cipla Ltd", "ticker": "CIPLA", "sector": "Pharma / Formulations (trade)"},
    {"name": "Dr. Reddy's Laboratories Ltd", "ticker": "DRREDDY", "sector": "Pharma / Formulations (trade)"},
    {"name": "Apollo Hospitals Enterprise Ltd", "ticker": "APOLLOHOSP", "sector": "Hospitals / Healthcare (insurer payments)"},
    {"name": "Divi's Laboratories Ltd", "ticker": "DIVISLAB", "sector": "Pharma / Formulations (trade)"},
    {"name": "Eicher Motors Ltd", "ticker": "EICHERMOT", "sector": "Manufacturing / B2B"},
    {"name": "Hero MotoCorp Ltd", "ticker": "HEROMOTOCO", "sector": "Manufacturing / B2B"},
    {"name": "Bajaj Auto Ltd", "ticker": "BAJAJ-AUTO", "sector": "Manufacturing / B2B"},
    {"name": "Britannia Industries Ltd", "ticker": "BRITANNIA", "sector": "FMCG / Retail"},
    {"name": "Nestle India Ltd", "ticker": "NESTLEIND", "sector": "FMCG / Retail"},
    {"name": "Varun Beverages Ltd", "ticker": "VBL", "sector": "FMCG / Retail"},
    {"name": "Zomato Ltd", "ticker": "ZOMATO", "sector": "SaaS / Subscription (B2B)"},
    {"name": "Trent Ltd", "ticker": "TRENT", "sector": "FMCG / Retail"},
    {"name": "Bharat Electronics Ltd", "ticker": "BEL", "sector": "Capital Goods / Industrial"},
    {"name": "Hindustan Aeronautics Ltd", "ticker": "HAL", "sector": "Capital Goods / Industrial"},
    {"name": "Dixon Technologies (India) Ltd", "ticker": "DIXON", "sector": "Consumer Durables / Retailer credit"},
    {"name": "Polycab India Ltd", "ticker": "POLYCAB", "sector": "Capital Goods / Industrial"},
    {"name": "Persistent Systems Ltd", "ticker": "PERSISTENT", "sector": "IT Services / Consulting"},
    {"name": "Coforge Ltd", "ticker": "COFORGE", "sector": "IT Services / Consulting"},
    {"name": "Central Depository Services (India) Ltd", "ticker": "CDSL", "sector": "Banks / NBFC"},
    {"name": "BSE Ltd", "ticker": "BSE", "sector": "Banks / NBFC"},
    {"name": "DLF Ltd", "ticker": "DLF", "sector": "Construction / Infra (milestone billing)"},
    {"name": "Godrej Consumer Products Ltd", "ticker": "GODREJCP", "sector": "FMCG / Retail"},
    {"name": "Havells India Ltd", "ticker": "HAVELLS", "sector": "Consumer Durables / Retailer credit"},
    {"name": "Pidilite Industries Ltd", "ticker": "PIDILITIND", "sector": "Chemicals / Oil & Gas"},
    {"name": "Siemens Ltd", "ticker": "SIEMENS", "sector": "Capital Goods / Industrial"},
    {"name": "ABB India Ltd", "ticker": "ABB", "sector": "Capital Goods / Industrial"},
    {"name": "Custom / Unlisted / Manual Entry", "ticker": "CUSTOM", "sector": "Other / Diversified"}
]

def get_company_list():
    """Returns sorted display names for UI selection."""
    return [f"{c['name']} ({c['ticker']})" for c in NIFTY_COMPANIES]

def find_company_info(display_str: str) -> Dict[str, str]:
    """Finds company dict given display string."""
    for c in NIFTY_COMPANIES:
        if f"{c['name']} ({c['ticker']})" == display_str:
            return c
    return {"name": display_str, "ticker": "CUSTOM", "sector": "FMCG / Retail"}

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
            # Fallback to BSE ticker if NSE missing
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
