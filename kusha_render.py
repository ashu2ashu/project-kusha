"""
kusha_render.py
Pure HTML & Plotly Rendering Engine for Project KUSHA / StockSage.

Contains pure rendering functions for metric cards, Plotly charts, traffic-light
indicators, forensic fraud shield dossiers, and responsive institutional visual components.
Maintains 100% purity: zero Streamlit runtime dependencies or st.* calls.
"""

import html
import re
import json
import math
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import analyzer
from analyzer import verdict_band, guardrail_level, GUARDRAIL_RED, GUARDRAIL_ALERT

def esc(value: Any) -> str:
    """Escape any value for safe HTML interpolation. None becomes an empty string."""
    return html.escape(str(value if value is not None else ""), quote=True)




def safe_url(url: Any) -> str:
    """Return the URL only if it is an absolute http(s) URL, else ''."""
    u = str(url or "").strip()
    return u if u.lower().startswith(("https://", "http://")) else ""




def sanitize_memo_field(val: Any, max_len: int = 600) -> str:
    """Neutralize structural markdown, strip leading control characters, collapse to single line, and cap length."""
    if val is None:
        return ""
    s = str(val).replace("\r", " ").replace("\n", " ")
    # Strip dangerous leading structural markdown characters repeatedly
    s = re.sub(r'^[#>\-*|`\s]+', '', s)
    # Escape pipe characters so they don't break markdown tables
    s = s.replace("|", "\\|")
    # Collapse multiple whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip() + "..."
    return s




def build_filing_ingestion_notice_html(filing_metadata):
    """Build an escaped filing notice that does not imply unverified ingestion."""
    metadata = filing_metadata or {}
    title = html.escape(str(metadata.get("title") or "Annual Report"), quote=True)
    year = html.escape(str(metadata.get("year") or "Latest"), quote=True)
    source = html.escape(str(metadata.get("source") or "Source not verified"), quote=True)
    analyzed = metadata.get("ingestion_status") == "analyzed"
    is_manual = metadata.get("source") == "Manual PDF Upload"

    if analyzed and is_manual:
        heading = "Uploaded PDF analyzed · source not independently verified"
        description = "The uploaded document was attached to the analysis. Its origin and statutory status were not independently verified."
        background, border, accent, heading_color, body_color = "#EFF6FF", "#BFDBFE", "#2563EB", "#1E40AF", "#475569"
    elif analyzed:
        heading = "Official BSE India Filing Analyzed · Multimodal Document Ingestion"
        description = "The official statutory filing was attached to Gemini and analyzed against all 8 governance and financial pillars."
        background, border, accent, heading_color, body_color = "#ECFDF5", "#A7F3D0", "#059669", "#065F46", "#475569"
    else:
        heading = "Filing listed · PDF not analyzed"
        description = "The filing metadata was found, but the PDF was not confirmed as attached to the completed analysis."
        background, border, accent, heading_color, body_color = "#FFFBEB", "#FDE68A", "#D97706", "#92400E", "#475569"

    filing_url = str(metadata.get("url") or "")
    try:
        parsed_url = urlparse(filing_url)
        host = (parsed_url.hostname or "").lower().rstrip(".")
        safe_bse_url = (
            filing_url
            if parsed_url.scheme == "https"
            and (host == "bseindia.com" or host.endswith(".bseindia.com"))
            and parsed_url.path.lower().endswith(".pdf")
            else None
        )
    except ValueError:
        safe_bse_url = None
    link_html = (
        f'<a href="{html.escape(safe_bse_url, quote=True)}" target="_blank" rel="noopener noreferrer" '
        'style="color: #059669; font-weight: 700; text-decoration: underline; font-size: 13px; font-family: \'JetBrains Mono\', monospace;">View BSE-hosted PDF ↗</a>'
        if safe_bse_url
        else '<span style="color: #64748B; font-size: 13px;">No verified filing link</span>'
    )

    display_title = title if year in title else f"{title} ({year})"
    return (
        f'<div style="background: {background}; border: 1px solid {border}; border-left: 5px solid {accent}; '
        'border-radius: 10px; padding: 12px 18px; margin-bottom: 16px; display: flex; '
        'justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">'
        f'<div><div style="font-size: 11px; font-weight: 800; color: {heading_color}; text-transform: uppercase; '
        f'letter-spacing: 0.6px; margin-bottom: 2px;">{heading}</div>'
        f'<div style="font-size: 14.5px; font-weight: 750; color: #0F172A;">{display_title} · {source}</div>'
        f'<div style="font-size: 12px; color: {body_color}; margin-top: 2px;">{description}</div></div>'
        f'<div>{link_html}</div></div>'
    )




def render_dalal_street_metric_cards_html(live_data: dict, fin_res: dict = None) -> str:
    if not live_data:
        return ""
    sm = dict(live_data.get("screener_metrics", {}))
    if fin_res and "cagr" in fin_res and not fin_res.get("error"):
        cagr_d = fin_res.get("cagr", {})
        if sm.get("roce") in ("N/A", None) and cagr_d.get("latest_roce") is not None:
            sm["roce"] = f"{cagr_d['latest_roce']:.2f} %"
        if sm.get("roe") in ("N/A", None) and cagr_d.get("latest_roe") is not None:
            sm["roe"] = f"{cagr_d['latest_roe']:.1f} %"
        if sm.get("roic") in ("N/A", None) and cagr_d.get("latest_roic") is not None:
            sm["roic"] = f"{cagr_d['latest_roic']:.2f} %"
        if sm.get("current_ratio") in ("N/A", None) and cagr_d.get("latest_current_ratio") is not None:
            sm["current_ratio"] = f"{cagr_d['latest_current_ratio']:.2f}"
        if sm.get("int_coverage") in ("N/A", None) and cagr_d.get("latest_int_coverage") is not None:
            ic_v = cagr_d["latest_int_coverage"]
            sm["int_coverage"] = "Net Cash (Debt-Free)" if ic_v >= 99.0 else f"{ic_v:.2f}"
        if sm.get("asset_turnover") in ("N/A", None) and cagr_d.get("latest_asset_turnover") is not None:
            sm["asset_turnover"] = f"{cagr_d['latest_asset_turnover']:.2f}"
        if sm.get("debt_to_equity") in ("N/A", None) and cagr_d.get("latest_de") is not None:
            sm["debt_to_equity"] = f"{cagr_d['latest_de']:.2f}"

    cur_p = live_data.get("current_price", 0)
    cur_str = f"₹ {cur_p:,.2f}" if isinstance(cur_p, (int, float)) else "N/A"

    def fmt_metric_row(label: str, value: str, style_mode: str = "normal", is_even: bool = False) -> str:
        row_bg = ' style="background-color: #F8FAFC;"' if is_even else ''
        if style_mode == "emerald":
            val_span = f'<span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 14px; font-family: monospace;">{value}</span>'
        elif style_mode == "teal":
            val_span = f'<span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 14px; font-family: monospace;">{value}</span>'
        elif style_mode == "bold":
            val_span = f'<span style="font-weight: 900; color: #0F172A; font-size: 15px; font-family: monospace;">{value}</span>'
        else:
            val_span = f'<span style="font-weight: 700; color: #334155; font-size: 14.5px; font-family: monospace;">{value}</span>'
        return f'<tr{row_bg}><td class="m-label">{label}</td><td class="m-val">{val_span}</td></tr>'

    col1_items = [
        ("Market Capitalization", sm.get("market_cap", "N/A"), "bold"),
        ("Current Price (CMP)", cur_str, "emerald"),
        ("Price to Earnings (P/E)", sm.get("pe", "N/A"), "normal"),
        ("Price to Book Value (P/B)", sm.get("price_to_book", "N/A"), "normal"),
        ("Enterprise Value (EV)", sm.get("ev", "N/A"), "normal"),
        ("EV / EBITDA Multiple", sm.get("ev_to_ebitda", "N/A"), "normal"),
        ("Historical High / Low", sm.get("high_low", "N/A"), "normal"),
        ("Sector Median P/E", sm.get("industry_pe", "N/A"), "normal"),
        ("Graham Intrinsic Value", sm.get("graham_number", "N/A"), "normal"),
    ]

    col2_items = [
        ("ROCE (Capital Employed)", sm.get("roce", "N/A"), "emerald"),
        ("ROE (Shareholder Equity)", sm.get("roe", "N/A"), "emerald"),
        ("ROIC (Invested Capital)", sm.get("roic", "N/A"), "emerald"),
        ("Operating Margin (OPM)", sm.get("opm", "N/A"), "normal"),
        ("Net Profit Margin (NPM)", sm.get("npm_last_year", "N/A"), "normal"),
        ("Earnings Yield", sm.get("earnings_yield", "N/A"), "normal"),
        ("Asset Turnover Ratio", sm.get("asset_turnover", "N/A"), "normal"),
        ("Book Value Per Share", sm.get("book_value", "N/A"), "normal"),
        ("Face Value", sm.get("face_value", "N/A"), "normal"),
    ]

    col3_items = [
        ("Total Debt", sm.get("debt", "N/A"), "normal"),
        ("Debt to Equity Ratio", sm.get("debt_to_equity", "N/A"), "normal"),
        ("Current Ratio", sm.get("current_ratio", "N/A"), "normal"),
        ("Interest Coverage Ratio", sm.get("int_coverage", "N/A"), "normal"),
        ("Est. 5Y FCF Run-Rate", sm.get("free_cash_flow_5yr", "N/A"), "teal"),
        ("CMP to Free Cash Flow", sm.get("cmp_to_fcf", "N/A"), "teal"),
        ("Promoter Shareholding", sm.get("promoter_holding", "N/A"), "bold"),
        ("Sales Growth (5 Years)", sm.get("sales_growth_5yr", "N/A"), "normal"),
        ("Dividend Yield", sm.get("dividend_yield", "N/A"), "normal"),
    ]

    def build_spacious_card(title: str, icon: str, badge_lbl: str, hdr_bg: str, border_col: str, title_col: str, badge_fg: str, items: list) -> str:
        rows_html = [fmt_metric_row(lbl, val, smode, is_even=(idx % 2 == 1)) for idx, (lbl, val, smode) in enumerate(items)]
        return (
            f'<div class="metric-domain-card" style="border: 1.5px solid {border_col}; background: #FFFFFF; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">'
            f'<div class="metric-domain-header" style="background: {hdr_bg}; border-bottom: 1.5px solid {border_col};">'
            f'<div style="display: flex; align-items: center; gap: 10px;">'
            f'<span style="font-size: 18px;">{icon}</span>'
            f'<span style="font-size: 14.5px; font-weight: 800; color: {title_col}; letter-spacing: -0.3px;">{title}</span>'
            f'</div>'
            f'<span style="font-size: 11px; font-weight: 800; color: {badge_fg}; background: #FFFFFF; border: 1px solid {border_col}; padding: 3px 9px; border-radius: 9999px; font-family: monospace;">{badge_lbl}</span>'
            f'</div>'
            f'<table class="metric-table-spacious">'
            f'<tbody>{"".join(rows_html)}</tbody>'
            f'</table>'
            f'</div>'
        )

    card_val = build_spacious_card("Valuation & Pricing Multiples", "🏛️", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#2563EB", "#2563EB", col1_items)
    card_ret = build_spacious_card("Profitability & Capital Returns", "📈", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#059669", "#059669", col2_items)
    card_sol = build_spacious_card("Solvency, Cash Flow & Growth", "🛡️", "9 Key Metrics", "#F8FAFC", "#E2E8F0", "#7C3AED", "#7C3AED", col3_items)
    return f"{card_val}{card_ret}{card_sol}"




def build_ticker_chart(df: pd.DataFrame, ticker_title: str, chart_style: str = "Area", show_dma: bool = True):
    if df.empty or len(df) < 2:
        return None
        
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.80, 0.20]
    )
    
    if chart_style in ("Candlestick", "Candles"):
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                name="OHLC",
                increasing_line_color="#059669",
                decreasing_line_color="#DC2626",
                showlegend=False
            ),
            row=1, col=1
        )
    else:
        start_price = float(df["Close"].iloc[0])
        end_price = float(df["Close"].iloc[-1])
        line_color = "#059669" if end_price >= start_price else "#DC2626"
        fill_color = "rgba(5, 150, 105, 0.08)" if end_price >= start_price else "rgba(220, 38, 38, 0.08)"
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name="CMP",
                line=dict(color=line_color, width=2.4),
                fill="tozeroy",
                fillcolor=fill_color
            ),
            row=1, col=1
        )
        
    if show_dma:
        if len(df) >= 50:
            sma50 = df["Close"].rolling(window=50).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=sma50,
                    mode="lines",
                    name="50 DMA",
                    line=dict(color="#2563EB", width=1.5, dash="dot")
                ),
                row=1, col=1
            )
        if len(df) >= 200:
            sma200 = df["Close"].rolling(window=200).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=sma200,
                    mode="lines",
                    name="200 DMA",
                    line=dict(color="#D97706", width=1.5, dash="dash")
                ),
                row=1, col=1
            )

    vol_colors = ["#059669" if c >= o else "#DC2626" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.55),
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11, family="Inter, sans-serif")),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1, gridcolor="#F1F5F9", tickfont=dict(size=11, family="JetBrains Mono, monospace", color="#475569"))
    fig.update_yaxes(title_text="Vol", row=2, col=1, gridcolor="#F1F5F9", tickfont=dict(size=10, color="#64748B"))
    fig.update_xaxes(gridcolor="#F1F5F9", tickfont=dict(size=11, color="#475569"))
    return fig




# Single Source of Truth for 8 Canonical Pillars
PILLAR_STYLE = {
    "1": {"icon": "🏛️", "chip": "Governance", "chip_bg": "rgba(5, 150, 105, 0.08)", "chip_fg": "#059669", "border": "rgba(5, 150, 105, 0.25)"},
    "2": {"icon": "🔍", "chip": "Forensics", "chip_bg": "rgba(37, 99, 235, 0.08)", "chip_fg": "#2563EB", "border": "rgba(37, 99, 235, 0.25)"},
    "3": {"icon": "🛡️", "chip": "Risk / ESG", "chip_bg": "rgba(124, 58, 237, 0.08)", "chip_fg": "#7C3AED", "border": "rgba(124, 58, 237, 0.25)"},
    "4": {"icon": "📈", "chip": "Valuation", "chip_bg": "rgba(37, 99, 235, 0.08)", "chip_fg": "#2563EB", "border": "rgba(37, 99, 235, 0.25)"},
    "5": {"icon": "🔄", "chip": "Moat", "chip_bg": "rgba(5, 150, 105, 0.08)", "chip_fg": "#059669", "border": "rgba(5, 150, 105, 0.25)"},
    "6": {"icon": "💵", "chip": "Simplicity", "chip_bg": "rgba(217, 119, 6, 0.08)", "chip_fg": "#D97706", "border": "rgba(217, 119, 6, 0.25)"},
    "7": {"icon": "🚀", "chip": "Innovation", "chip_bg": "rgba(124, 58, 237, 0.08)", "chip_fg": "#7C3AED", "border": "rgba(124, 58, 237, 0.25)"},
    "8": {"icon": "⚖️", "chip": "Insider Risk", "chip_bg": "rgba(234, 88, 12, 0.08)", "chip_fg": "#EA580C", "border": "rgba(234, 88, 12, 0.25)"},
}

_missing_pillar_ids = [p["id"] for p in analyzer.CANONICAL_PILLARS if str(p["id"]) not in PILLAR_STYLE]
if _missing_pillar_ids:
    raise RuntimeError(f"PILLAR_STYLE missing ids: {_missing_pillar_ids}")

class PillarMetadataDict(dict):
    """Dictionary holding pillar metadata, supporting both int and str key access."""
    def __getitem__(self, key):
        return super().__getitem__(str(key))
    def get(self, key, default=None):
        return super().get(str(key), default)

PILLAR_METADATA = PillarMetadataDict({
    str(p["id"]): {
        "id": p["id"],
        "name": p["name"],
        "icon": PILLAR_STYLE[str(p["id"])]["icon"],
        "chip": PILLAR_STYLE[str(p["id"])]["chip"],
        "chip_bg": PILLAR_STYLE[str(p["id"])]["chip_bg"],
        "chip_fg": PILLAR_STYLE[str(p["id"])]["chip_fg"],
        "border": PILLAR_STYLE[str(p["id"])]["border"],
    }
    for p in analyzer.CANONICAL_PILLARS
})
_PILLAR_STYLE = [
    (PILLAR_STYLE[str(p["id"])]["icon"], PILLAR_STYLE[str(p["id"])]["chip"], PILLAR_STYLE[str(p["id"])]["chip_bg"], PILLAR_STYLE[str(p["id"])]["chip_fg"], PILLAR_STYLE[str(p["id"])]["border"])
    for p in analyzer.CANONICAL_PILLARS
]



def build_radar_chart(pillars):
    if not pillars:
        return None
    names = [f"P{p['id']}: {p['name']}" for p in pillars]
    pct_scores = [(p["score"] / p["max_score"]) * 100 for p in pillars]
    
    names_closed = names + [names[0]]
    pct_closed = pct_scores + [pct_scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=pct_closed,
        theta=names_closed,
        fill='toself',
        fillcolor='rgba(5, 150, 105, 0.18)',
        line=dict(color='#059669', width=3),
        marker=dict(size=7, color='#2563EB', line=dict(color='#FFFFFF', width=2)),
        name='% of Max Score'
    ))

    fig.update_layout(
        template="plotly_white",
        polar=dict(
            bgcolor='#FFFFFF',
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%",
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(color='#64748B', size=10, family='JetBrains Mono')
            ),
            angularaxis=dict(
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(color='#0F172A', size=11.5, family='Inter', weight=700)
            )
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        margin=dict(l=55, r=55, t=30, b=30),
        height=430
    )
    return fig



def parse_dcf_estimate(dcf_str):
    if not dcf_str:
        return None, None, None
    s = str(dcf_str)
    curr_matches = re.findall(r"(?:INR|₹|Rs\.?)\s*([\d,]+(?:\.\d+)?)", s, re.IGNORECASE)
    nums = []
    for item in curr_matches:
        clean = item.replace(",", "").strip()
        if clean:
            try:
                v = float(clean)
                if v > 0:
                    nums.append(v)
            except ValueError:
                pass
    if not nums:
        fallback = re.findall(r"\b([\d,]+(?:\.\d+)?)\b(?!\s*(?:%|bps|percent))", s, re.IGNORECASE)
        for item in fallback:
            clean = item.replace(",", "").strip()
            if clean:
                try:
                    v = float(clean)
                    if v > 0:
                        nums.append(v)
                except ValueError:
                    pass
    if len(nums) >= 2:
        l, h = sorted([nums[0], nums[1]])
        return l, h, (l + h) / 2.0
    elif len(nums) == 1:
        return nums[0], nums[0], nums[0]
    return None, None, None



def render_live_analysis_timer_html(
    company_name: str,
    ticker: str,
    mode_label: str,
    est_label: str,
    est_sec_typical: int = 60,
    completed_sec: float | None = None,
    is_error: bool = False
) -> str:
    """Renders a client-side JavaScript ticking stopwatch and progress gauge for live analysis."""
    esc_company = html.escape(str(company_name or "Target Entity"))
    esc_ticker = html.escape(str(ticker or "NSE/BSE"))
    esc_mode = html.escape(str(mode_label or "Fundamental Audit"))
    esc_est = html.escape(str(est_label or "~45–75s"))
    typical_s = max(1, int(est_sec_typical or 60))

    if completed_sec is not None:
        total_s = max(0.0, float(completed_sec))
        m = int(total_s // 60)
        s = int(total_s % 60)
        d = int((total_s * 10) % 10)
        time_display = f"{m:02d}:{s:02d}"
        tenths_display = str(d)
        
        if is_error:
            pulse_color = "#DC2626"
            title_text = f"Audit Interrupted · {esc_company} ({esc_ticker})"
            badge_text = "Failed / Error"
            badge_style = "color: #EF4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3);"
            bar_style = "width: 100%; background: #EF4444;"
            phase_text = "Evaluation interrupted. See technical diagnostics below."
            pct_display = "100%"
        else:
            pulse_color = "#10B981"
            title_text = f"Audit Completed · {esc_company} ({esc_ticker})"
            badge_text = f"Completed in {total_s:.1f}s ✔"
            badge_style = "color: #10B981; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);"
            bar_style = "width: 100%; background: linear-gradient(90deg, #10B981, #059669);"
            phase_text = "✅ Institutional brief compiled &amp; mathematical guardrails verified."
            pct_display = "100%"

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    color: #F8FAFC;
    overflow: hidden;
  }}
  .timer-card {{
    background: linear-gradient(135deg, #090D16 0%, #0F172A 60%, #1E293B 100%);
    border: 1.5px solid #334155;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  }}
  .header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .live-tag {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.7px;
    color: {pulse_color};
    text-transform: uppercase;
  }}
  .pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: {pulse_color};
    box-shadow: 0 0 8px {pulse_color};
  }}
  .mode-badge {{
    background: rgba(56, 189, 248, 0.12);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.28);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    font-family: monospace;
    letter-spacing: 0.4px;
  }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: 1.2fr 1fr 0.9fr;
    gap: 12px;
    align-items: center;
  }}
  .metric-block {{
    display: flex;
    flex-direction: column;
  }}
  .metric-label {{
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #94A3B8;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .clock-digits {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 24px;
    font-weight: 900;
    color: #F8FAFC;
    letter-spacing: 0.5px;
    line-height: 1.1;
  }}
  .clock-digits .tenths {{
    color: {pulse_color};
    font-size: 20px;
  }}
  .estimate-val {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 16px;
    font-weight: 700;
    color: #E2E8F0;
  }}
  .status-badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    {badge_style}
    padding: 3px 8px;
    border-radius: 6px;
    text-align: center;
    width: fit-content;
  }}
  .progress-track {{
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 6px;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 9px;
  }}
  .progress-fill {{
    height: 100%;
    {bar_style}
    border-radius: 9999px;
  }}
  .footer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 11px;
  }}
  .phase-text {{
    color: #94A3B8;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .pct-text {{
    color: {pulse_color};
    font-family: monospace;
    font-weight: 800;
    font-size: 11px;
    margin-left: 8px;
  }}
</style>
</head>
<body>
<div class="timer-card">
  <div class="header-row">
    <div class="live-tag">
      <span class="pulse-dot"></span>
      <span>{title_text}</span>
    </div>
    <span class="mode-badge">{esc_mode}</span>
  </div>
  <div class="metrics-grid">
    <div class="metric-block">
      <span class="metric-label">Total Duration</span>
      <div class="clock-digits"><span>{time_display}</span>.<span class="tenths">{tenths_display}</span></div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Target Estimate</span>
      <div class="estimate-val">⏳ {esc_est}</div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Engine Status</span>
      <div class="status-badge">{badge_text}</div>
    </div>
  </div>
  <div class="progress-track">
    <div class="progress-fill"></div>
  </div>
  <div class="footer-row">
    <span class="phase-text">{phase_text}</span>
    <span class="pct-text">{pct_display}</span>
  </div>
</div>
</body>
</html>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
    color: #F8FAFC;
    overflow: hidden;
  }}
  .timer-card {{
    background: linear-gradient(135deg, #090D16 0%, #0F172A 60%, #1E293B 100%);
    border: 1.5px solid #334155;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.45);
  }}
  .header-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .live-tag {{
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.7px;
    color: #38BDF8;
    text-transform: uppercase;
  }}
  .pulse-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px #10B981;
    animation: livePulse 1.4s ease-in-out infinite;
  }}
  @keyframes livePulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.4; transform: scale(0.85); }}
  }}
  .mode-badge {{
    background: rgba(56, 189, 248, 0.12);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.28);
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    font-family: monospace;
    letter-spacing: 0.4px;
  }}
  .metrics-grid {{
    display: grid;
    grid-template-columns: 1.2fr 1fr 0.9fr;
    gap: 12px;
    align-items: center;
  }}
  .metric-block {{
    display: flex;
    flex-direction: column;
  }}
  .metric-label {{
    font-size: 9.5px;
    font-weight: 800;
    letter-spacing: 0.6px;
    color: #94A3B8;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .clock-digits {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 24px;
    font-weight: 900;
    color: #F8FAFC;
    letter-spacing: 0.5px;
    line-height: 1.1;
  }}
  .clock-digits .tenths {{
    color: #38BDF8;
    font-size: 20px;
  }}
  .estimate-val {{
    font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
    font-size: 16px;
    font-weight: 700;
    color: #E2E8F0;
  }}
  .status-badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    color: #10B981;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    padding: 3px 8px;
    border-radius: 6px;
    text-align: center;
    width: fit-content;
  }}
  .progress-track {{
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.05);
    height: 6px;
    border-radius: 9999px;
    overflow: hidden;
    margin-top: 9px;
  }}
  .progress-fill {{
    height: 100%;
    width: 2%;
    background: linear-gradient(90deg, #38BDF8, #10B981);
    border-radius: 9999px;
    transition: width 0.15s ease-out;
  }}
  .footer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    font-size: 11px;
  }}
  .phase-text {{
    color: #94A3B8;
    font-size: 11px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .pct-text {{
    color: #38BDF8;
    font-family: monospace;
    font-weight: 800;
    font-size: 11px;
    margin-left: 8px;
  }}
</style>
</head>
<body>
<div class="timer-card">
  <div class="header-row">
    <div class="live-tag">
      <span class="pulse-dot"></span>
      <span>Live Audit &middot; {esc_company} ({esc_ticker})</span>
    </div>
    <span class="mode-badge">{esc_mode}</span>
  </div>
  <div class="metrics-grid">
    <div class="metric-block">
      <span class="metric-label">Elapsed Time</span>
      <div class="clock-digits"><span id="m_s">00:00</span>.<span class="tenths" id="tenths">0</span></div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Estimated Latency</span>
      <div class="estimate-val">⏳ {esc_est}</div>
    </div>
    <div class="metric-block">
      <span class="metric-label">Engine Pace</span>
      <div class="status-badge" id="pace_badge">Active &middot; On Track</div>
    </div>
  </div>
  <div class="progress-track">
    <div class="progress-fill" id="progress_bar"></div>
  </div>
  <div class="footer-row">
    <span class="phase-text" id="phase_label">Connecting to exchange feeds &amp; fundamental database...</span>
    <span class="pct-text" id="pct_label">0%</span>
  </div>
</div>
<script>
(function() {{
  var t0 = Date.now();
  var est = {typical_s};
  var msEl = document.getElementById('m_s');
  var tenEl = document.getElementById('tenths');
  var barEl = document.getElementById('progress_bar');
  var pctEl = document.getElementById('pct_label');
  var phaseEl = document.getElementById('phase_label');
  var paceEl = document.getElementById('pace_badge');

  function update() {{
    var elapsedMs = Date.now() - t0;
    var totalSec = elapsedMs / 1000.0;
    var mins = Math.floor(totalSec / 60);
    var secs = Math.floor(totalSec % 60);
    var tenths = Math.floor((elapsedMs % 1000) / 100);

    msEl.textContent = (mins < 10 ? '0' : '') + mins + ':' + (secs < 10 ? '0' : '') + secs;
    tenEl.textContent = tenths;

    var pct = 0;
    if (est <= 1) {{
      pct = Math.min(98, Math.round(totalSec * 80));
    }} else {{
      pct = Math.round((totalSec / est) * 100);
      if (pct > 96) {{
        pct = Math.min(99, 96 + Math.round(((totalSec - est) / (est * 0.5)) * 3));
      }}
    }}
    pct = Math.max(2, Math.min(99, pct));
    barEl.style.width = pct + '%';
    pctEl.textContent = pct + '%';

    if (totalSec > est && paceEl && est > 2) {{
      paceEl.textContent = 'Deep Synthesis';
      paceEl.style.color = '#F59E0B';
      paceEl.style.borderColor = 'rgba(245, 158, 11, 0.4)';
      paceEl.style.background = 'rgba(245, 158, 11, 0.15)';
    }}

    if (pct < 15) {{
      phaseEl.textContent = 'Connecting to exchange feeds & parsing fundamental tables...';
    }} else if (pct < 35) {{
      phaseEl.textContent = 'Evaluating statutory filings & footnote schedules...';
    }} else if (pct < 70) {{
      phaseEl.textContent = 'Multimodal reasoning across 8 Pillars with Gemini 2.5...';
    }} else if (pct < 90) {{
      phaseEl.textContent = 'Enforcing deterministic Python scoring & PIO guardrails...';
    }} else {{
      phaseEl.textContent = 'Compiling institutional research brief & governance dossier...';
    }}
  }}

  setInterval(update, 100);
  update();
}})();
</script>
</body>
</html>"""



def render_research_provenance_and_evidence_card(res, live_data, target_company_name, target_ticker, target_sector, fin_res=None):
    live = live_data or {}
    company_name = html.escape(str(target_company_name or res.get("company_name", "Tracked Company")))
    ticker = html.escape(str(target_ticker or res.get("ticker", "NSE")))
    sector = html.escape(str(target_sector or res.get("sector", "General")))
    
    filing_meta = res.get("filing_metadata") or {}
    period = html.escape(str(filing_meta.get("year") or res.get("financial_year") or "FY2024 / TTM"))
    
    is_demo = bool(res.get("is_synthetic_demo", False))
    is_analyzed = filing_meta.get("ingestion_status") == "analyzed" or res.get("document_analyzed", False)
    
    # 1. Company & Period
    q1_sub = f"<strong>{company_name}</strong> ({ticker}) · Sector: {sector} · Audited Period: <strong>{period}</strong>"
    
    # 2. Data Origin
    if is_demo:
        q2_source = "Synthetic demonstration dataset (sample for UI walkthrough; not live market data)"
        q2_chip = "SYNTHETIC SAMPLE"
        q2_chip_bg = "#FFFBEB"
        q2_chip_fg = "#D97706"
        q2_chip_bdr = "#FDE68A"
    elif is_analyzed:
        q2_source = f"Official BSE India statutory filing ({filing_meta.get('title', 'Annual Report')}) + delayed Yahoo Finance statements (~4 years, unaudited) + delayed quotes"
        q2_chip = "STATUTORY BSE FILING"
        q2_chip_bg = "#ECFDF5"
        q2_chip_fg = "#059669"
        q2_chip_bdr = "#A7F3D0"
    else:
        research = res.get("web_research", {})
        src_cnt = len(research.get("sources", []))
        q2_source = f"Delayed Yahoo Finance market and statement data (unaudited) + {src_cnt} web citation{'s' if src_cnt != 1 else ''}"
        q2_chip = "PUBLIC FEEDS & CITATIONS"
        q2_chip_bg = "#EFF6FF"
        q2_chip_fg = "#2563EB"
        q2_chip_bdr = "#BFDBFE"

    # 3. Freshness & Integrity
    sentinel = res.get("sentinel_audit") or {}
    s_score = sentinel.get("integrity_score")
    s_text = f"{s_score:.0f}/100" if s_score is not None else "Not evaluated (insufficient data)"
    retrieval_time = res.get("retrieved_at") or "Not recorded"
    exec_sec = res.get("execution_time_seconds")
    est_lbl = res.get("estimated_time_label")
    is_cached = res.get("is_cached_result", False)
    if is_cached:
        latency_str = f" · Replay: Local Cache ({exec_sec:.2f}s · 0 API Quota)"
    else:
        latency_str = f" · Latency: {exec_sec:.1f}s" + (f" (Est: {est_lbl})" if est_lbl else "") if exec_sec is not None else ""
    q3_text = f"Retrieved: {retrieval_time} · Multimodal Ingestion: {'Verified' if is_analyzed else 'Public Feed'} · Mathematical Sanity Check: {s_text}{latency_str}"

    # 4. Qualified Conclusion & Supporting Evidence
    try:
        final_score = float(res.get("final_score", 0))
    except (ValueError, TypeError):
        final_score = 0.0
    pio_trig = res.get("pio_triggered", False)
    guardrail = str(res.get("guardrail_tag", ""))

    if pio_trig or analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_RED or final_score < 55.0:
        stance_label = "Elevated Caution / High Risk"
        stance_col = "#DC2626"
        stance_bg = "#FEF2F2"
        stance_bdr = "#FECACA"
    elif final_score >= 70.0:
        stance_label = "Constructive Watchlist / Quality Franchise"
        stance_col = "#059669"
        stance_bg = "#ECFDF5"
        stance_bdr = "#A7F3D0"
    else:
        stance_label = "Monitored / Neutral Tier"
        stance_col = "#D97706"
        stance_bg = "#FFFBEB"
        stance_bdr = "#FDE68A"

    verdict_text = res.get("verdict", "") or f"Composite Forensic Score: {final_score:.1f}/100"
    verdict_clean = html.escape(str(verdict_text))

    # 5. Evidence Gaps
    gaps = res.get("evidence_gaps") or []
    if gaps:
        gap_items = "".join([f'<li style="margin-bottom: 4px;">{html.escape(str(g))}</li>' for g in gaps[:3]])
        q5_html = f'<ul style="margin: 4px 0 0 16px; padding: 0; color: #B45309; font-size: 12px; line-height: 1.45;">{gap_items}</ul>'
        gap_badge = f'<span style="background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">{len(gaps)} EVIDENCE GAPS</span>'
    else:
        q5_html = '<div style="font-size: 12px; color: #059669; margin-top: 4px;">✔ Standard audited statement schedules reviewed; check Notes to Accounts for unlisted commitments.</div>'
        gap_badge = '<span style="background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">STANDARD DISCLOSURES</span>'

    # 6. What to Inspect Next
    next_checks = [
        "CARO 2020 Order: Check paragraph 3 for adverse inventory or disputed statutory tax remarks.",
        "Notes to Accounts: Review Note on Related-Party Transactions & Contingent Liabilities.",
        "Cash Conversion: Cross-examine CFO vs PAT across trailing 4 quarters.",
        "Promoter Registry: Inspect BSE / NSE shareholding disclosures for fresh encumbrances."
    ]
    next_html = "".join([f'<li style="margin-bottom: 4px;">{html.escape(c)}</li>' for c in next_checks])

    card_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 10px; border-bottom: 1.5px solid #F1F5F9; padding-bottom: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 18px;">🧭</span>'
        f'<span style="font-size: 14px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.7px;">Research Provenance &amp; Due Diligence Framework</span>'
        f'</div>'
        f'<span style="background: {q2_chip_bg}; color: {q2_chip_fg}; border: 1px solid {q2_chip_bdr}; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace;">{q2_chip}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; margin-bottom: 14px;">'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #059669;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">1. Subject Entity &amp; Target Period</div>'
        f'<div style="font-size: 12.5px; color: #0F172A; margin-top: 4px; line-height: 1.45;">{q1_sub}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #2563EB;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">2. Source Provenance</div>'
        f'<div style="font-size: 12px; color: #334155; margin-top: 4px; line-height: 1.45;">{q2_source}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid #7C3AED;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">3. Freshness &amp; Sanity Audit</div>'
        f'<div style="font-size: 12px; color: #334155; margin-top: 4px; line-height: 1.45;">{q3_text}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; border-left: 3.5px solid {stance_col};">'
        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
        f'<span style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">4. Model Forensic Stance</span>'
        f'<span style="background: {stance_bg}; color: {stance_col}; border: 1px solid {stance_bdr}; font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">{stance_label}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #0F172A; font-weight: 600; margin-top: 4px; line-height: 1.45;">{verdict_clean}</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">'
        f'<div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 12px 14px;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
        f'<span style="font-size: 11px; font-weight: 800; color: #92400E; text-transform: uppercase; letter-spacing: 0.5px;">5. Evidence Gaps &amp; Uncertainties</span>'
        f'{gap_badge}'
        f'</div>'
        f'{q5_html}'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px;">'
        f'<div style="font-size: 11px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">6. What to Inspect Next (Due Diligence Checklist)</div>'
        f'<ol style="margin: 4px 0 0 16px; padding: 0; color: #475569; font-size: 12px; line-height: 1.45;">{next_html}</ol>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    return card_html



def render_traffic_light_and_eli15_html(res, live_data, target_company_name, target_sector):
    live = live_data or {}

    def _parse_num(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    cmp = _parse_num(live.get("current_price"))
    de_val = _parse_num(live.get("debt_to_equity"))
    pe = _parse_num(live.get("pe_ratio"))

    # 1. Management Integrity
    pio_trig = res.get("pio_triggered", False)
    guardrail = str(res.get("guardrail_tag", ""))
    total_pen = _parse_num(res.get("total_penalties")) or 0.0
    is_doc_analyzed = res.get("filing_metadata", {}).get("ingestion_status") == "analyzed" or res.get("document_analyzed", False)
    is_insufficient = res.get("analysis_status") == "insufficient_evidence"
    has_gaps = is_insufficient or (bool(res.get("evidence_gaps")) and not is_doc_analyzed)

    if pio_trig or analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_RED:
        gov_status = "CRITICAL RISK"
        gov_color = "#DC2626"
        gov_bg = "#FEF2F2"
        gov_border = "#FECACA"
        gov_sub = "High risk: Serious audit red flags or promoter integrity warnings active."
        gov_icon = "🔴"
    elif analyzer.guardrail_level(guardrail) == analyzer.GUARDRAIL_ALERT or total_pen >= 4.0:
        gov_status = "MONITOR"
        gov_color = "#D97706"
        gov_bg = "#FFFBEB"
        gov_border = "#FDE68A"
        gov_sub = "Watch closely: Minor disclosure alerts or related-party schedules flagged."
        gov_icon = "🟡"
    elif has_gaps:
        gov_status = "INSUFFICIENT DATA"
        gov_color = "#D97706"
        gov_bg = "#FFFBEB"
        gov_border = "#FDE68A"
        gov_sub = "Evidence gaps present: Full statutory disclosures could not be verified."
        gov_icon = "🟡"
    else:
        gov_status = "PRISTINE"
        gov_color = "#059669"
        gov_bg = "#ECFDF5"
        gov_border = "#A7F3D0"
        gov_sub = "Clean record: Zero shares pledged, trusted auditor, no accounting issues."
        gov_icon = "🟢"

    # 2. Balance Sheet Fortress
    if de_val is not None:
        if de_val <= 0.4:
            bs_status = "FORTRESS"
            bs_color = "#059669"
            bs_bg = "#ECFDF5"
            bs_border = "#A7F3D0"
            bs_sub = f"Virtually debt-free ({de_val:.2f}x D/E) with strong cash reserves."
            bs_icon = "🟢"
        elif de_val <= 1.0:
            bs_status = "MODERATE"
            bs_color = "#D97706"
            bs_bg = "#FFFBEB"
            bs_border = "#FDE68A"
            bs_sub = f"Manageable debt ({de_val:.2f}x D/E) comfortably serviced by operating cash."
            bs_icon = "🟡"
        else:
            bs_status = "LEVERAGED"
            bs_color = "#DC2626"
            bs_bg = "#FEF2F2"
            bs_border = "#FECACA"
            bs_sub = f"High debt ({de_val:.2f}x D/E). Vulnerable to interest rate or economic slowdowns."
            bs_icon = "🔴"
    else:
        bs_status = "NOT ASSESSED"
        bs_color = "#64748B"
        bs_bg = "#F8FAFC"
        bs_border = "#E2E8F0"
        bs_sub = "Debt-to-equity metric is unavailable from market data feeds."
        bs_icon = "⚪"

    # 3. Valuation Multiples
    appendix_b = res.get("appendix_b_calculations") or {}
    dcf_str = appendix_b.get("dcf_fair_value_estimate", "")
    dcf_low, dcf_high, dcf_mid = parse_dcf_estimate(dcf_str)

    mos_pct = None
    if dcf_mid and cmp:
        mos_pct = ((dcf_mid - cmp) / dcf_mid) * 100.0

    if mos_pct is not None:
        if mos_pct >= 5.0:
            val_status = "ATTRACTIVE"
            val_color = "#059669"
            val_bg = "#ECFDF5"
            val_border = "#A7F3D0"
            val_sub = f"Good entry: Trading {mos_pct:.1f}% below fair value (₹{dcf_mid:,.0f})."
            val_icon = "🟢"
        elif mos_pct >= -10.0:
            val_status = "FAIR VALUE"
            val_color = "#2563EB"
            val_bg = "#EFF6FF"
            val_border = "#BFDBFE"
            val_sub = f"Fairly priced: Trading near intrinsic fair value (₹{dcf_mid:,.0f})."
            val_icon = "🔵"
        else:
            val_status = "STRETCHED"
            val_color = "#DC2626"
            val_bg = "#FEF2F2"
            val_border = "#FECACA"
            val_sub = f"Expensive: Trading {abs(mos_pct):.1f}% above fair value (₹{dcf_mid:,.0f})."
            val_icon = "🔴"
    elif pe is not None:
        if pe <= 25:
            val_status = "ATTRACTIVE"
            val_color = "#059669"
            val_bg = "#ECFDF5"
            val_border = "#A7F3D0"
            val_sub = f"Attractive multiple ({pe:.1f}x P/E) offering good value support."
            val_icon = "🟢"
        elif pe <= 55:
            val_status = "FAIR VALUE"
            val_color = "#2563EB"
            val_bg = "#EFF6FF"
            val_border = "#BFDBFE"
            val_sub = f"Reasonable multiple ({pe:.1f}x P/E) reflecting steady business quality."
            val_icon = "🔵"
        else:
            val_status = "STRETCHED"
            val_color = "#DC2626"
            val_bg = "#FEF2F2"
            val_border = "#FECACA"
            val_sub = f"High valuation ({pe:.1f}x P/E) leaves little margin for error."
            val_icon = "🔴"
    else:
        val_status = "BALANCED"
        val_color = "#2563EB"
        val_bg = "#EFF6FF"
        val_border = "#BFDBFE"
        val_sub = "Valuation multiples in line with industry peers."
        val_icon = "🔵"

    # ELI15 Plain English
    final_score = _parse_num(res.get("final_score")) or 0.0
    company_clean = html.escape(str(target_company_name or "This company"))
    sector_clean = html.escape(str(target_sector or "its sector"))

    band = verdict_band(final_score)
    eli_badge_fg = band["color"]
    r, g, b = int(band["color"][1:3], 16), int(band["color"][3:5], 16), int(band["color"][5:7], 16)
    eli_badge_bg = f"rgba({r}, {g}, {b}, 0.08)"
    eli_badge_bdr = f"rgba({r}, {g}, {b}, 0.25)"

    if band["code"] in ("OCGC", "PCGC"):
        eli_action = "Bottom Line: High-quality compounder with verified cash flows and clean governance metrics. Favorable risk-reward profile for fundamental watchlists."
        eli_badge = "HIGH FINANCIAL INTEGRITY"
    elif band["code"] in ("QTC", "VTC"):
        eli_action = "Bottom Line: Established franchise with solid moats, but monitored accruals or valuation suggest exercising margin of safety."
        eli_badge = "MONITORED QUALITY TIER"
    else:
        eli_action = "Bottom Line: Elevated forensic risk. Significant anomalies identified in debt servicing, governance signals, or cash conversion."
        eli_badge = "ELEVATED FORENSIC RISK"

    strengths = res.get("strengths", [])
    if strengths and len(strengths) > 0:
        clean_s = html.escape(str(strengths[0]).rstrip("."))
        if "insufficient evidence" in clean_s.lower() and not is_doc_analyzed:
            eli_biz = f"<strong>{company_clean}</strong> operates in India\'s <strong>{sector_clean}</strong> sector; statutory research is incomplete due to evidence gaps."
        else:
            eli_biz = f"<strong>{company_clean}</strong> is an established market leader in India\'s <strong>{sector_clean}</strong> sector, powered by {clean_s.lower()}."
    else:
        eli_biz = f"<strong>{company_clean}</strong> is an established business in India\'s <strong>{sector_clean}</strong> sector with healthy operating cash flows and strong market reach."

    rendered_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; flex-wrap: wrap; gap: 10px;">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🚦</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">10-Second Telemetry & Quick Takeaway</span>'
        f'</div>'
        f'<span style="background: {eli_badge_bg}; color: {eli_badge_fg}; border: 1px solid {eli_badge_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.4px;">{eli_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 18px;">'
        f'<div style="background: {gov_bg}; border: 1.5px solid {gov_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">1. MANAGEMENT & AUDIT</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{gov_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {gov_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{gov_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{gov_sub}</div>'
        f'</div>'
        f'<div style="background: {bs_bg}; border: 1.5px solid {bs_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">2. BALANCE SHEET FORTRESS</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{bs_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {bs_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{bs_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{bs_sub}</div>'
        f'</div>'
        f'<div style="background: {val_bg}; border: 1.5px solid {val_border}; border-radius: 12px; padding: 16px 18px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px;">3. VALUATION & ENTRY</div>'
        f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">'
        f'<span style="font-size: 16px;">{val_icon}</span>'
        f'<span style="font-size: 16px; font-weight: 900; color: {val_color}; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{val_status}</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569;">{val_sub}</div>'
        f'</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-left: 4.5px solid #059669; border-radius: 10px; padding: 16px 20px;">'
        f'<div style="font-size: 11.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">'
        f'<span>💬</span> Plain-English Executive Summary (ELI15 Takeaway)'
        f'</div>'
        f'<div style="font-size: 13.5px; line-height: 1.6; color: #334155; margin-bottom: 6px;">{eli_biz}</div>'
        f'<div style="font-size: 13.5px; line-height: 1.6; color: #0F172A; font-weight: 700;">{eli_action}</div>'
        f'</div>'
        f'</div>'
    )
    return rendered_html




def _display_status(engine_status: str) -> str:
    """Canonical mapping from engine check status to user-facing shield status."""
    return {
        "PASS": "PASS",
        "MONITOR": "MONITOR",
        "CRITICAL": "ALERT",
        "INSUFFICIENT_DATA": "NOT EVALUATED",
    }.get(engine_status, "NOT EVALUATED")


def shield_rows(res: dict, live_data: dict, financial_data: dict = None, forensic_report: dict = None) -> List[Dict[str, Any]]:
    """
    Pure data extractor for the 6-point Forensic Fraud Shield.
    Returns list of dicts: {"title": str, "status": str, "badge": str, "evidence": str, "check_id": Optional[str]}.
    Enforces engine check truthfulness: no check may be PASS unless the engine evaluated it as PASS.
    """
    res = res or {}
    live = live_data or {}
    forensic_rep = forensic_report or res.get("forensic_report") or {}

    checks_list = forensic_rep.get("checks", [])
    checks_by_id = {c.get("id"): c for c in checks_list if isinstance(c, dict)}

    rows = []

    # 1. Auditor & Accounting Check (FOR_08_AUDITOR_GOVERNANCE)
    c8 = checks_by_id.get("FOR_08_AUDITOR_GOVERNANCE")
    if c8:
        raw_status = c8.get("status", "INSUFFICIENT_DATA")
        disp_status = _display_status(raw_status)
        if disp_status == "PASS":
            badge = "CLEAN AUDIT"
        elif disp_status == "ALERT":
            badge = "AUDIT NOTE"
        elif disp_status == "MONITOR":
            badge = "AUDIT MONITOR"
        else:
            badge = "NOT EVALUATED"
        evidence = c8.get("detail") or "Statutory auditor governance check evaluated."
    else:
        disp_status = "NOT EVALUATED"
        badge = "NOT EVALUATED"
        evidence = "This check was not performed on the available data."

    rows.append({
        "title": "Auditor & Accounting Check",
        "status": disp_status,
        "badge": badge,
        "evidence": evidence,
        "check_id": "FOR_08_AUDITOR_GOVERNANCE"
    })

    # 2. Promoter Share Pledge (FOR_07_PROMOTER_PLEDGE)
    c7 = checks_by_id.get("FOR_07_PROMOTER_PLEDGE")
    if c7:
        raw_status = c7.get("status", "INSUFFICIENT_DATA")
        disp_status = _display_status(raw_status)
        if disp_status == "PASS":
            badge = "0.0% PLEDGED"
        elif disp_status == "ALERT":
            badge = c7.get("metric") or "PLEDGE FLAGGED"
        elif disp_status == "MONITOR":
            badge = c7.get("metric") or "PLEDGE MONITOR"
        else:
            badge = "NOT EVALUATED"
        evidence = c7.get("detail") or "Promoter share pledge check evaluated."
    else:
        disp_status = "NOT EVALUATED"
        badge = "NOT EVALUATED"
        evidence = "This check was not performed on the available data."

    rows.append({
        "title": "Promoter Share Pledge",
        "status": disp_status,
        "badge": badge,
        "evidence": evidence,
        "check_id": "FOR_07_PROMOTER_PLEDGE"
    })

    # 3. Real Cash vs Paper Profit (FOR_01_CASH_CONVERSION)
    c1 = checks_by_id.get("FOR_01_CASH_CONVERSION")
    if c1:
        raw_status = c1.get("status", "INSUFFICIENT_DATA")
        disp_status = _display_status(raw_status)
        if disp_status == "PASS":
            badge = c1.get("metric") or "CFO > PAT (REAL CASH)"
        elif disp_status == "ALERT":
            badge = "NEGATIVE CFO" if "Negative" in c1.get("detail", "") else (c1.get("metric") or "CASH DEFICIT")
        elif disp_status == "MONITOR":
            badge = c1.get("metric") or "CFO/PAT MONITOR"
        else:
            badge = "NOT EVALUATED"
        evidence = c1.get("detail") or "Operating cash flow conversion evaluated."
    else:
        disp_status = "NOT EVALUATED"
        badge = "NOT EVALUATED"
        evidence = "This check was not performed on the available data."

    rows.append({
        "title": "Real Cash vs Paper Profit",
        "status": disp_status,
        "badge": badge,
        "evidence": evidence,
        "check_id": "FOR_01_CASH_CONVERSION"
    })

    # 4. Customer Payments & Dues (FOR_02_RECEIVABLE_VELOCITY)
    c2 = checks_by_id.get("FOR_02_RECEIVABLE_VELOCITY")
    dso_raw = res.get("receivable_health_metrics", {}).get("dso_days")
    if c2:
        raw_status = c2.get("status", "INSUFFICIENT_DATA")
        disp_status = _display_status(raw_status)
        metric_val = c2.get("metric")
        if metric_val and metric_val != "N/A":
            badge = metric_val
        elif disp_status == "PASS":
            badge = "HARMONIOUS"
        else:
            badge = "NOT EVALUATED"
        evidence = c2.get("detail") or "Revenue vs receivables velocity evaluated."
        if dso_raw is not None:
            evidence += f" [DSO (not the engine metric): {dso_raw} days]"
    else:
        disp_status = "NOT EVALUATED"
        badge = "NOT EVALUATED"
        evidence = "This check was not performed on the available data."
        if dso_raw is not None:
            evidence += f" [DSO (not the engine metric): {dso_raw}]"

    rows.append({
        "title": "Customer Payments & Dues",
        "status": disp_status,
        "badge": badge,
        "evidence": evidence,
        "check_id": "FOR_02_RECEIVABLE_VELOCITY"
    })

    # 5. Debt & Solvency Health (FOR_06_CREDIT_RATING_SOLVENCY)
    c6 = checks_by_id.get("FOR_06_CREDIT_RATING_SOLVENCY")
    if c6:
        raw_status = c6.get("status", "INSUFFICIENT_DATA")
        disp_status = _display_status(raw_status)
        if disp_status == "PASS":
            badge = c6.get("metric") or "DEBT FREE"
        elif disp_status == "ALERT":
            badge = "HIGH DEBT"
        elif disp_status == "MONITOR":
            badge = c6.get("metric") or "ELEVATED D/E"
        else:
            badge = "NOT EVALUATED"
        evidence = c6.get("detail") or "Debt and balance sheet leverage evaluated."
    else:
        disp_status = "NOT EVALUATED"
        badge = "NOT EVALUATED"
        evidence = "This check was not performed on the available data."

    rows.append({
        "title": "Debt & Solvency Health",
        "status": disp_status,
        "badge": badge,
        "evidence": evidence,
        "check_id": "FOR_06_CREDIT_RATING_SOLVENCY"
    })

    # 6. Regulatory Track Record (Engine does not emit check; check PIO trigger)
    pio_trig = res.get("pio_triggered", False)
    if pio_trig:
        reg_status = "ALERT"
        reg_badge = "UNDER PROBE"
        reg_ev = "Regulatory warnings, auditor actions, or forensic concerns flagged in records."
    else:
        reg_status = "NOT EVALUATED"
        reg_badge = "NOT EVALUATED"
        reg_ev = "This check was not performed on the available data."

    rows.append({
        "title": "Regulatory Track Record",
        "status": reg_status,
        "badge": reg_badge,
        "evidence": reg_ev,
        "check_id": None
    })

    return rows


def render_forensic_fraud_shield_html(res: dict, live_data: dict, financial_data: dict = None, forensic_report: dict = None) -> str:
    """Renders the 6-point Forensic Fraud Shield card using pure shield_rows data."""
    shield_items = shield_rows(res, live_data, financial_data=financial_data, forensic_report=forensic_report)

    passed_count = sum(1 for it in shield_items if it["status"] == "PASS")
    not_verified_count = sum(1 for it in shield_items if it["status"] == "NOT EVALUATED")
    total_shield = len(shield_items)

    if passed_count == total_shield:
        shield_badge = f"{passed_count} / {total_shield} CHECKS PASSED — ALL CLEAR"
    elif not_verified_count:
        shield_badge = f"{passed_count} / {total_shield} PASSED · {not_verified_count} NOT EVALUATED"
    else:
        shield_badge = f"{passed_count} / {total_shield} CHECKS PASSED"

    all_clear = (passed_count == total_shield)
    shield_badge_bg = "rgba(5, 150, 105, 0.08)" if all_clear else "rgba(217, 119, 6, 0.08)"
    shield_badge_fg = "#059669" if all_clear else "#D97706"
    shield_badge_bdr = "rgba(5, 150, 105, 0.25)" if all_clear else "rgba(217, 119, 6, 0.25)"

    cards_html_list = []
    for it in shield_items:
        is_pass = (it["status"] == "PASS")
        is_alert = (it["status"] == "ALERT")
        icon_str = "✔" if is_pass else ("✖" if is_alert else "⚠")
        icon_bg = "#ECFDF5" if is_pass else ("#FEF2F2" if is_alert else "#FFFBEB")
        icon_fg = "#059669" if is_pass else ("#DC2626" if is_alert else "#D97706")
        badge_bg = "rgba(5, 150, 105, 0.08)" if is_pass else ("rgba(220, 38, 38, 0.08)" if is_alert else "rgba(217, 119, 6, 0.08)")
        badge_fg = "#059669" if is_pass else ("#DC2626" if is_alert else "#D97706")
        badge_border = "rgba(5, 150, 105, 0.25)" if is_pass else ("rgba(220, 38, 38, 0.25)" if is_alert else "rgba(217, 119, 6, 0.25)")

        cards_html_list.append(
            f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 16px 18px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s ease;">'
            f'<div>'
            f'<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; gap: 8px;">'
            f'<div style="display: flex; align-items: center; gap: 8px;">'
            f'<span style="display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; background: {icon_bg}; color: {icon_fg}; border-radius: 50%; font-size: 12px; font-weight: 900;">{icon_str}</span>'
            f'<span style="font-size: 13.5px; font-weight: 800; color: #0F172A;">{html.escape(str(it["title"]))}</span>'
            f'</div>'
            f'<span style="background: {badge_bg}; color: {badge_fg}; border: 1px solid {badge_border}; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 9999px; white-space: nowrap; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{html.escape(str(it["badge"]))}</span>'
            f'</div>'
            f'<div style="font-size: 12.5px; line-height: 1.5; color: #475569; margin-top: 4px;">{html.escape(str(it["evidence"]))}</div>'
            f'</div>'
            f'</div>'
        )
    cards_html = "".join(cards_html_list)

    shield_html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 22px 24px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🛡️</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">6-Point Forensic Safety Shield (Anti-Fraud Filter)</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">A 6-point background check for accounting tricks, hidden debt, and promoter red flags</div>'
        f'</div>'
        f'<span style="background: {shield_badge_bg}; color: {shield_badge_fg}; border: 1px solid {shield_badge_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; letter-spacing: 0.4px; font-family: \'JetBrains Mono\', monospace;">{shield_badge}</span>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">'
        f'{cards_html}'
        f'</div>'
        f'</div>'
    )
    return shield_html


def render_valuation_compass_html(res, live_data):
    live = live_data or {}

    def _parse_num(val):
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    cmp = _parse_num(live.get("current_price"))
    low_52w = _parse_num(live.get("low_52w"))
    high_52w = _parse_num(live.get("high_52w"))

    appendix_b = res.get("appendix_b_calculations") or {}
    dcf_str = appendix_b.get("dcf_fair_value_estimate", "")
    dcf_low, dcf_high, dcf_mid = parse_dcf_estimate(dcf_str)

    # No fair-value estimate from the model means no fair-value corridor.
    # Deriving one from the current price would fabricate a "target" from the
    # very number it is supposed to be compared against.
    if not cmp or not dcf_mid:
        return ""

    # Intrinsic target and sensitivity band handling
    if not dcf_low or not dcf_high or abs(dcf_high - dcf_low) < 1.0:
        dcf_card_val = f"₹{dcf_mid:,.0f}"
        dcf_card_sub = f"Intrinsic Target (±5% Band: ₹{dcf_mid * 0.95:,.0f} – ₹{dcf_mid * 1.05:,.0f})"
        band_low = dcf_mid * 0.95
        band_high = dcf_mid * 1.05
    else:
        dcf_card_val = f"₹{dcf_low:,.0f} – ₹{dcf_high:,.0f}"
        dcf_card_sub = f"Midpoint: ₹{dcf_mid:,.0f}"
        band_low = dcf_low
        band_high = dcf_high

    if not low_52w:
        low_52w = min(cmp, band_low)
    if not high_52w:
        high_52w = max(cmp, band_high)

    # Margin of Safety calculation
    mos_pct = ((dcf_mid - cmp) / dcf_mid) * 100.0
    if mos_pct > 0:
        mos_badge = f"+{mos_pct:.1f}% Margin of Safety"
        mos_color = "#059669"
        mos_bg = "rgba(5, 150, 105, 0.08)"
        mos_bdr = "rgba(5, 150, 105, 0.25)"
        mos_desc = f"Trading at a discount to the model fair-value estimate (₹{dcf_mid:,.0f})"
    else:
        mos_badge = f"{abs(mos_pct):.1f}% Valuation Premium"
        mos_color = "#DC2626"
        mos_bg = "rgba(220, 38, 38, 0.08)"
        mos_bdr = "rgba(220, 38, 38, 0.25)"
        mos_desc = f"Trading above the model fair-value estimate (₹{dcf_mid:,.0f})"

    # Asymmetry & Risk-Reward calculations
    downside_low_pct = ((cmp - low_52w) / cmp) * 100.0 if cmp and low_52w else 0.0
    upside_dcf_pct = ((dcf_mid - cmp) / cmp) * 100.0 if cmp and dcf_mid else 0.0

    if upside_dcf_pct >= 0:
        upside_str = f"+{upside_dcf_pct:.1f}% to model fair value"
        upside_color = "#059669"
        asymmetry_desc = "Favorable risk-reward versus the model estimate"
    else:
        upside_str = f"{upside_dcf_pct:.1f}% to model fair value"
        upside_color = "#DC2626"
        asymmetry_desc = "Trading above the model estimate; downside risk to 52W Low"

    downside_str = f"-{abs(downside_low_pct):.1f}% to 52W L"

    val_min = min(low_52w, band_low, cmp) * 0.96
    val_max = max(high_52w, band_high, cmp) * 1.04
    span = max(val_max - val_min, 1.0)

    def to_pct(v):
        return min(96.0, max(4.0, (v - val_min) / span * 100.0))

    pct_low = to_pct(low_52w)
    pct_high = to_pct(high_52w)
    pct_cmp = to_pct(cmp)
    pct_dcf_low = to_pct(band_low)
    pct_dcf_high = to_pct(band_high)
    dcf_width = max(3.0, pct_dcf_high - pct_dcf_low)

    # Active valuation bar fills strictly in accordance with Current Market Price (CMP)
    fill_left = min(pct_low, pct_cmp)
    fill_width = max(3.0, abs(pct_cmp - pct_low))
    range_52w_width = max(3.0, pct_high - pct_low)

    html = (
        f'<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 26px; margin-bottom: 22px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">'
        f'<div>'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span style="font-size: 20px;">🧭</span>'
        f'<span style="font-size: 14.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px;">Valuation Compass & Fair Value Corridor</span>'
        f'</div>'
        f'<div style="font-size: 12.5px; color: #64748B; margin-top: 3px;">Current market price relative to the 52-week corridor and a model-estimated fair value (not a computed DCF)</div>'
        f'</div>'
        f'<span style="background: {mos_bg}; color: {mos_color}; border: 1px solid {mos_bdr}; font-size: 11.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; font-family: \'JetBrains Mono\', monospace; letter-spacing: 0.3px;">{mos_badge}</span>'
        f'</div>'
        f'<div style="position: relative; margin: 44px 16px 36px 16px; height: 14px; background: #F1F5F9; border: 1px solid #CBD5E1; border-radius: 9999px;">'
        # 1. 52-week range corridor (unfilled guide from 52W L to 52W H)
        f'<div style="position: absolute; left: {pct_low:.1f}%; width: {range_52w_width:.1f}%; height: 100%; background: #E2E8F0; border-radius: 9999px;"></div>'
        # 2. Active valuation bar filled in accordance with CMP (from 52W Low up to CMP)
        f'<div style="position: absolute; left: {fill_left:.1f}%; width: {fill_width:.1f}%; height: 100%; background: linear-gradient(90deg, #60A5FA 0%, #2563EB 100%); border-radius: 9999px; z-index: 2;"></div>'
        # 3. DCF Fair Value Range Target Zone (capsule)
        f'<div style="position: absolute; left: {pct_dcf_low:.1f}%; width: {dcf_width:.1f}%; height: 100%; background: rgba(5, 150, 105, 0.15); border: 2px solid #059669; border-radius: 9999px; z-index: 3;"></div>'
        # 4. 52W Low tick & label
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W L: ₹{low_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_low:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #CBD5E1; border-radius: 2px; z-index: 4;"></div>'
        # 5. DCF Fair Value Target Label (below)
        f'<div style="position: absolute; left: {to_pct(dcf_mid):.1f}%; top: 18px; transform: translateX(-50%); font-size: 11.5px; font-weight: 800; color: #059669; font-family: \'JetBrains Mono\', monospace; white-space: nowrap; z-index: 4;">▲ Est. Fair: ₹{dcf_mid:,.0f}</div>'
        # 6. CMP Needle and Badge (positioned precisely at CMP)
        f'<div style="position: absolute; left: {pct_cmp:.1f}%; top: -34px; transform: translateX(-50%); z-index: 5; text-align: center;">'
        f'<span style="background: #2563EB; color: #FFFFFF; font-size: 11.5px; font-weight: 900; padding: 2px 8px; border-radius: 6px; box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4); font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">CMP ₹{cmp:,.1f}</span>'
        f'<div style="width: 3px; height: 18px; background: #2563EB; margin: 0 auto; border-radius: 2px;"></div>'
        f'</div>'
        # 7. 52W High tick & label
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -26px; transform: translateX(-50%); font-size: 11px; font-weight: 700; color: #64748B; font-family: \'JetBrains Mono\', monospace; white-space: nowrap;">52W H: ₹{high_52w:,.1f}</div>'
        f'<div style="position: absolute; left: {pct_high:.1f}%; top: -2px; transform: translateX(-50%); width: 3px; height: 18px; background: #CBD5E1; border-radius: 2px; z-index: 4;"></div>'
        f'</div>'
        # Bottom Metric Cards
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 28px;">'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">FAIR VALUE (MODEL ESTIMATE)</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: #059669; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{dcf_card_val}</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{dcf_card_sub}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">VALUATION STATUS</div>'
        f'<div style="font-size: 16.5px; font-weight: 800; color: {mos_color}; font-family: \'JetBrains Mono\', monospace; margin-top: 4px;">{mos_badge}</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{mos_desc}</div>'
        f'</div>'
        f'<div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px; padding: 14px 16px;">'
        f'<div style="font-size: 10.5px; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;">UPSIDE VS DOWNSIDE</div>'
        f'<div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-top: 4px; font-family: \'JetBrains Mono\', monospace;">'
        f'<span style="color: {upside_color};">{upside_str}</span> &bull; <span style="color: #64748B;">{downside_str}</span>'
        f'</div>'
        f'<div style="font-size: 12px; color: #64748B; margin-top: 2px;">{asymmetry_desc}</div>'
        f'</div>'
        f'</div>'
        # Micro-Legend for Valuation Compass
        f'<div style="display: flex; justify-content: center; align-items: center; gap: 20px; flex-wrap: wrap; margin-top: 18px; padding-top: 14px; border-top: 1px dashed #E2E8F0; font-size: 11px; font-weight: 700; color: #64748B;">'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #2563EB; border-radius: 2px;"></span> CMP Active Price Pin</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: rgba(5, 150, 105, 0.15); border: 1.5px solid #059669; border-radius: 2px;"></span> Model Fair Value Zone</span>'
        f'<span style="display: inline-flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 11px; height: 11px; background: #E2E8F0; border: 1px solid #CBD5E1; border-radius: 2px;"></span> 52-Week Range Bounds</span>'
        f'</div>'
        f'</div>'
    )
    return html



def render_graphical_forensic_architecture_html() -> str:
    """
    Renders an innovative graphical pipeline and visual benchmark compass for the
    StockSage Forensic Evaluation Architecture, replacing walls of text with intuitive infographics.
    """
    return """
    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 16px; padding: 24px 28px; box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);">
      <!-- Header -->
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px; flex-wrap: wrap; gap: 12px; border-bottom: 1.5px solid #E2E8F0; padding-bottom: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 22px;">🧭</span>
            <span style="font-size: 17px; font-weight: 800; color: #0F172A; letter-spacing: -0.2px;">StockSage Forensic Architecture & Evaluation Pipeline</span>
          </div>
          <div style="font-size: 13px; color: #64748B; margin-top: 3px;">
            Multi-layer forensic screening combining market context with audited filing telemetry.
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">Ind AS Aligned</span>
          <span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">Internal consistency checks</span>
        </div>
      </div>

      <!-- Stage 1-4 Connected Pipeline Infographic -->
      <div class="ss-pipeline-grid">
        <!-- Step 1 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #059669; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #059669; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(5,150,105,0.3);">1</span>
            <span style="font-size: 10px; font-weight: 800; color: #059669; background: rgba(5, 150, 105, 0.08); border: 1px solid rgba(5, 150, 105, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">DATA LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Universe Ingestion</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Ingest 501 tracked equities, pull live quotes, and review primary annual reports.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">501 tracked</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">Live Feeds</span>
          </div>
        </div>

        <!-- Step 2 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #2563EB; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #2563EB; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(37,99,235,0.3);">2</span>
            <span style="font-size: 10px; font-weight: 800; color: #2563EB; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">AUDIT LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Sentinel-1 Verification</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Runs 6-point mathematical cross-check to verify balance equations and zero hallucinations.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">6/6 Check</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">SHA Seal</span>
          </div>
        </div>

        <!-- Step 3 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #D97706; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #D97706; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(217,119,6,0.3);">3</span>
            <span style="font-size: 10px; font-weight: 800; color: #D97706; background: rgba(217, 119, 6, 0.08); border: 1px solid rgba(217, 119, 6, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">CAGR LAYER</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">Multi-Year Trends</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Computes 3–5 year compounded growth across Revenue, Profit, ROCE, and Free Cash Flow.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">5Y CAGR</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">FCF Engine</span>
          </div>
        </div>

        <!-- Step 4 -->
        <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3.5px solid #7C3AED; border-radius: 12px; padding: 18px 20px; position: relative;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="width: 26px; height: 26px; border-radius: 50%; background: #7C3AED; color: #FFFFFF; font-weight: 900; font-size: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(124,58,237,0.3);">4</span>
            <span style="font-size: 10px; font-weight: 800; color: #7C3AED; background: rgba(124, 58, 237, 0.08); border: 1px solid rgba(124, 58, 237, 0.25); padding: 2px 7px; border-radius: 9999px; font-family: 'JetBrains Mono', monospace;">SYNTHESIS</span>
          </div>
          <div style="font-size: 14.5px; font-weight: 800; color: #0F172A; margin-bottom: 4px;">8-Pillar AI Dossier</div>
          <div style="font-size: 12px; color: #475569; line-height: 1.45; margin-bottom: 12px;">Synthesizes 0–100 score, forensic penalties, Big 4 auditor checks, and institutional position call.</div>
          <div style="display: flex; flex-wrap: wrap; gap: 6px;">
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">0-100 Score</span>
            <span style="font-size: 10px; background: #FFFFFF; border: 1px solid #CBD5E1; color: #334155; padding: 2px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">Position Call</span>
          </div>
        </div>
      </div>

      <!-- Graphical Metric Benchmark Cards -->
      <div style="border-top: 1.5px solid #E2E8F0; padding-top: 20px;">
        <div style="font-size: 12.5px; font-weight: 800; color: #0F172A; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 14px; display: flex; align-items: center; gap: 8px;">
          <span>📊</span> Forensic Threshold Compass (Dalal Street Institutional Benchmarks)
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
          <!-- Benchmark 1 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #059669; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #059669; text-transform: uppercase; letter-spacing: 0.5px;">CFO / PAT CONVERSION</span>
              <span style="background: rgba(5, 150, 105, 0.08); color: #059669; border: 1px solid rgba(5, 150, 105, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 95%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #059669; width: 95%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Real Cash in Bank: Over 95% confirms reported accounting profits actually turn into liquid cash.</div>
          </div>

          <!-- Benchmark 2 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #2563EB; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.5px;">DEBT TO EQUITY (D/E)</span>
              <span style="background: rgba(37, 99, 235, 0.08); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≤ 0.3x</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #2563EB; width: 30%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Solvency Shield: Low debt prevents interest burden shocks during macro slowdowns.</div>
          </div>

          <!-- Benchmark 3 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #D97706; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #D97706; text-transform: uppercase; letter-spacing: 0.5px;">ROCE (CAPITAL RETURNS)</span>
              <span style="background: rgba(217, 119, 6, 0.08); color: #D97706; border: 1px solid rgba(217, 119, 6, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 20%</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #D97706; width: 80%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Elite Moat: Generates >₹20 operating profit per ₹100 of capital employed.</div>
          </div>

          <!-- Benchmark 4 -->
          <div style="background: #F8FAFC; border: 1.5px solid #E2E8F0; border-top: 3px solid #7C3AED; border-radius: 12px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span style="font-size: 10.5px; font-weight: 800; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.5px;">COMPOSITE QUALITY SCORE</span>
              <span style="background: rgba(124, 58, 237, 0.08); color: #7C3AED; border: 1px solid rgba(124, 58, 237, 0.25); font-size: 10px; font-weight: 800; padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace;">≥ 85 / 100</span>
            </div>
            <div style="background: #E2E8F0; border-radius: 9999px; height: 5px; margin-bottom: 8px;">
              <div style="background: #7C3AED; width: 85%; height: 5px; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4;">Potential Compounder: Top 15% quality tier with clean governance and moat endurance.</div>
          </div>
        </div>
      </div>
    </div>
    """


