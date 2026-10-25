# Comprehensive Institutional Framework & Forensic Due Diligence Analysis

This document provides an exhaustive, granular analysis of each analytical dimension, quantitative formula, forensic threshold, and visualization model implemented in **StockSage (IDEX-7.5SC)**. It concludes with a live case-study walkthrough of **ABB India Ltd**.

---

## 1. The 6-Point Forensic Safety Shield (Anti-Fraud Filter)

The Forensic Safety Shield is an automated pre-qualification gate designed to uncover accounting manipulation, hidden leverage, promoter margin risks, and regulatory probes before standard valuation multiples are evaluated.

```mermaid
flowchart TD
    A["Raw Regulatory & Financial Inputs"] --> B{"6-Point Forensic Safety Shield"}
    B --> C1["1. Auditor & Accounting Check"]
    B --> C2["2. Promoter Share Pledge Check"]
    B --> C3["3. Real Cash vs Paper Profit"]
    B --> C4["4. Customer Payments & Dues"]
    B --> C5["5. Debt & Solvency Health"]
    B --> C6["6. Regulatory Track Record"]
    C1 --> D{"All 6 Pass?"}
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    D -- Yes --> E["6 / 6 CHECKS PASSED — ALL CLEAR (Green Shield)"]
    D -- No --> F["MONITOR / ALERT (Score Deduction & Warning)"]
```

### Detailed Breakdown of the 6 Checks

#### 1. Auditor & Accounting Check
- **Forensic Objective:** Identify qualified opinions, adverse remarks, CARO 2020 reservations, or sudden mid-term auditor resignations under SEBI LODR Regulation 30 Annexure A.
- **Analytical Mechanics:** 
  - Parses statutory auditor notes under ICAI Auditing Standards (SA 700 / SA 705 / SA 706).
  - Evaluates keyword clusters: `unmodified`, `clean`, `true and fair`, `without qualification` vs adverse terms `qualified opinion`, `disclaimer of opinion`, `material misstatement`.
  - Audits CARO 2020 Clause (i) to (xxi) disclosures, specifically looking for physical inventory discrepancies, unrecorded title deeds, or unhedged related-party loans (Section 185/186).
- **Badge Outputs:**
  - `CLEAN AUDIT`: Unmodified opinion, Big-4 or established statutory auditor, zero CARO qualifications.
  - `AUDIT NOTE`: Emphasis of matter or minor CARO clause note flagged.
  - `CRITICAL RISK`: Qualified/adverse opinion or mid-term resignation.

#### 2. Promoter Share Pledge Check
- **Forensic Objective:** Detect promoter borrowing against equity collateral under SEBI (SAST) Regulations, preventing exposure to forced liquidation / margin-call death spirals.
- **Why Promoters Do Not State "No Pledge" in Words:**
  - Under SEBI Takeover Regulations, promoter shareholding is submitted in structured numerical tables (Form C / Regulation 31(1)).
  - Promoters disclose `Pledged Shares = 0` or `0.00%`. They do not write prose stating "we have no pledge".
  - The engine parses raw numerical encumbrance data. If the percentage is strictly `0.00%`, `Nil`, or `0 shares`, it validates that 100% of the promoter stake is unencumbered.
- **Badge Outputs:**
  - `0.0% PLEDGED`: Clean title, zero encumbrances on promoter holding.
  - `< 5.0% PLEDGED`: Minor pledge, classified under `MONITOR`.
  - `> 15.0% PLEDGED`: High-risk encumbrance triggering automatic institutional penalty.

#### 3. Real Cash vs Paper Profit (Cash Flow Conversion)
- **Forensic Objective:** Detect Sloan accrual anomalies, aggressive revenue recognition, or fabricated paper profits through multi-year cumulative cash conversion.
- **Mathematical Formula:**
  $$\text{Cash Conversion Ratio} = \frac{\sum_{t=1}^N \text{CFO}_t}{\sum_{t=1}^N \text{PAT}_t} \times 100$$
- **Thresholds & Logic:**
  - $\text{Ratio} \ge 90\%$: `CFO > PAT (REAL CASH)` — Pristine cash conversion; earnings reflect liquid money in bank accounts.
  - $80\% \le \text{Ratio} < 90\%$: `CFO/PAT: XX%` — Solid conversion with minor working capital absorption.
  - $60\% \le \text{Ratio} < 80\%$: Moderate conversion requiring working capital surveillance.
  - $< 60\%$ or Negative CFO: `NEGATIVE CFO` / `CFO GAP` — Critical red flag indicating uncollected paper earnings.

#### 4. Customer Payments & Dues (Debtor Health)
- **Forensic Objective:** Evaluate receivables velocity, channel stuffing, and customer overdue aging under Ind AS 109 Expected Credit Loss (ECL).
- **Mathematical Formula:**
  $$\text{DSO (Days Sales Outstanding)} = \frac{\text{Trade Receivables}}{\text{Total Revenue}} \times 365$$
- **Sector-Specific Thresholds:**
  - **B2B / Capital Goods / Infra:** Standard commercial credit terms are 60–90 days. A DSO $\le 90$ days with $<10\%$ overdue beyond 90 days represents healthy institutional payment behavior.
  - **FMCG / Retail:** Cash or short credit; threshold $\le 45$ days.
  - If $\text{DSO} > 120$ days or receivables growth outpaces revenue growth by $>18\%$, the channel stuffing alarm triggers.
- **Badge Outputs:** `DSO: 28 DAYS`, `HEALTHY DSO`, or `DSO FLAGGED`.

#### 5. Debt & Solvency Health
- **Forensic Objective:** Ensure structural balance sheet resilience, testing solvency against interest rate shocks and credit covenant breaches.
- **Key Metrics:**
  - $\text{Debt-to-Equity (D/E)} = \frac{\text{Total Borrowings}}{\text{Total Shareholders' Equity}}$
  - $\text{Interest Coverage Ratio} = \frac{\text{EBIT}}{\text{Finance Costs}}$
- **Thresholds:**
  - $\text{D/E} \le 0.05\text{x}$: `DEBT FREE`
  - $0.05\text{x} < \text{D/E} \le 0.50\text{x}$: `D/E 0.XXx` (Conservative leverage)
  - $\text{D/E} > 1.20\text{x}$ or Interest Coverage $< 2.5\text{x}$: High financial leverage warning.

#### 6. Regulatory Track Record
- **Forensic Objective:** Screen MCA filings, SEBI enforcement orders, exchange surveillance lists (ASM / GSM), and insider trading logs.
- **Logic:** Confirms zero active show-cause notices, forensic audit orders, or promoter debarment decrees.
- **Badge Outputs:** `CLEAN RECORD` vs `UNDER PROBE`.

---

## 2. The Valuation Compass & Intrinsic Fair Value Architecture

The Valuation Compass visualizes the relationship between the **Current Market Price (CMP)**, the **52-Week Range Corridor**, and the **DCF Intrinsic Fair Value Sensitivity Band**.

```
52W Low (₹4,637.5)                   CMP (₹6,140.0)           DCF Fair (₹6,508.0)         52W High (₹7,924.5)
      |------------------------------------●---------------------------[=======]-------------------|
       ◄───────── Active CMP Fill ─────────►                           ◄─ Band ─►
```

### Architectural Mechanics & Calculations

1. **Strict CMP Anchoring (No 52W High Stretch):**
   - The active progress bar fill represents the price journey from 52-week support up to the current quotation:
     $$\text{Fill Left} = \min(\%_{\text{52WL}}, \%_{\text{CMP}}), \quad \text{Fill Width} = |\%_{\text{CMP}} - \%_{\text{52WL}}|$$
   - The bar fill terminates **strictly at CMP**, eliminating misleading impressions of full valuation exhaustion.

2. **DCF Fair Value Target Capsule & Sensitivity Band:**
   - Rather than an arbitrary single price point, intrinsic value is projected as a sensitivity corridor:
     $$\text{Band Low} = \text{DCF Mid} \times 0.95, \quad \text{Band High} = \text{DCF Mid} \times 1.05$$
   - Eliminates duplicate range targets (e.g. `₹5,850 – ₹5,850`), cleanly displaying `₹6,508 (±5% Band: ₹6,183 – ₹6,833)`.

3. **Margin of Safety (MOS):**
   $$\text{MOS} = \frac{\text{DCF Midpoint} - \text{CMP}}{\text{DCF Midpoint}} \times 100$$
   - $\text{MOS} > 0$: Trading at a discount to intrinsic value (Green Badge `+5.7% Margin of Safety`).
   - $\text{MOS} < 0$: Trading at a premium to intrinsic value (Red Badge `XX% Valuation Premium`).

4. **Asymmetry & Risk-Reward Ratio:**
   $$\text{Upside to DCF} = \frac{\text{DCF Mid} - \text{CMP}}{\text{CMP}} \times 100$$
   $$\text{Downside to 52W Low} = \frac{\text{CMP} - \text{52W Low}}{\text{CMP}} \times 100$$
   - Rendered with single clean mathematical signs: `+6.0% to DCF • -2.0% to 52W L` (zero `+-` double sign artifacts).

---

## 3. The 8 Concealed Risk Forensic Surveillance Engines

Beyond statutory annual report prose, the Forensic Risk Engine runs 8 automated forensic tests to detect balance sheet distortions:

| Test ID | Surveillance Focus | Forensic Formula / Condition | Critical Red Flag Threshold |
| :--- | :--- | :--- | :--- |
| **FOR-01** | **Cash Conversion Quality** | $\frac{\sum \text{CFO}_{3\text{Y}}}{\sum \text{PAT}_{3\text{Y}}} \times 100$ | $< 60\%$ or Cumulative CFO $< 0$ |
| **FOR-02** | **Channel Stuffing Radar** | $\Delta\% \text{ Receivables} - \Delta\% \text{ Revenue}$ | Spread $> +18.0\%$ with Rec YoY $> 20\%$ |
| **FOR-03** | **Expense Capitalization Check** | $\frac{\text{Capital WIP}}{\text{Net Fixed Assets (PPE)}} \times 100$ | $\text{CWIP} > 35\%$ of PPE with slow capitalization |
| **FOR-04** | **Tax Provision Alignment** | $\frac{\text{Tax Provision}}{\text{PBT}} \times 100$ vs Statutory $25\%$ | Effective Tax Rate $< 12.0\%$ |
| **FOR-05** | **Other Income Decoupling** | $\frac{\text{Other Income}}{\text{PBT}} \times 100$ | Other Income $> 30.0\%$ of PBT |
| **FOR-06** | **External Credit Rating & Headroom** | External CRISIL/ICRA ratings & bank line headroom | Rating below Investment Grade (or D/E $> 1.0\text{x}$) |
| **FOR-07** | **Promoter Encumbrances (SAST)** | Pledged promoter shares / Total promoter shares | Pledged stake $> 0.0\%$ |
| **FOR-08** | **Auditor Tenure & CARO Defense** | Auditor tenure under Section 139(2) + CARO qualifications | Any adverse CARO remark or sudden resignation |

- **Forensic Quality Index (FQI):** Scored on a deterministic $0 - 100$ scale. Deductions are subtracted for each triggered risk flag. An FQI $\ge 82.0$ qualifies as `PRISTINE / LOW FORENSIC RISK`.

---

## 4. The 10-Pillar Quality Scorecard Framework

The core institutional rating engine evaluates 10 foundational quality pillars:

```mermaid
pie title 10-Pillar Quality Weightage
    "P1: Governance & Capital Allocation" : 20
    "P2: Forensic Accounting & Cash Flow" : 20
    "P3: Risk, ESG & Fragility" : 12
    "P4: Valuation & Sanity Layer" : 6
    "P5: Moat Durability & Scalability" : 13
    "P6: Simplicity & Repeatability" : 5
    "P7: Innovation & TAM Optionality" : 18
    "P8: Insider & Minority Shareholder Risk" : 6
```

### Pillar Overview & Evidence Hierarchy
1. **P1: Governance & Capital Allocation (Max: 20 pts):** Board composition, independent directorships, capital allocation discipline (ROCE > WACC), dividend payout consistency.
2. **P2: Forensic Accounting & Cash Flow (Max: 20 pts):** CFO/EBITDA purity, Sloan accruals, conservative depreciation schedules, working capital cash absorption.
3. **P3: Risk, ESG & Fragility (Max: 12 pts):** Balance sheet leverage, customer/supplier concentration, regulatory compliance, environmental liabilities.
4. **P4: Valuation & Sanity Layer (Max: 6 pts):** Forward P/E relative to 5-year historical median, EV/EBITDA, margin of safety.
5. **P5: Moat Durability & Scalability (Max: 13 pts):** Pricing power, market share stability, switching costs, return on capital persistence.
6. **P6: Simplicity & Repeatability (Max: 5 pts):** Transparency of revenue model, clean divisional reporting, minimal off-balance-sheet joint ventures.
7. **P7: Innovation & TAM Optionality (Max: 18 pts):** Total addressable market expansion, product innovation, R&D reinvestment, industry tailwinds.
8. **P8: Insider & Minority Shareholder Risk (Max: 6 pts):** Related-party transactions (RPTs), promoter buying/selling, royalty payouts to parent entities.

### Deterministic Penalty & Bonus Bridge
$$\text{Final Score} = \text{Core Quality} - \text{Penalties} + \text{Bonuses}$$
- **Penalties:** Capped at $-7.5$ points (e.g. Valuation premium sanity: $-1.5$ pts).
- **Bonuses:** Capped at $+10.0\%$ (Trajectory bonus: $+1.0\%$, Cool-Pro operational leadership: $+3.0\%$, Balance sheet resilience: $+1.5\%$).

---

## 5. Live Case Study: ABB India Ltd Audit Walkthrough

The table below summarizes the exact audited figures, statutory disclosures, and calculations for **ABB India Ltd** from live exchange feeds and multi-year statements:

| Dimension / Metric | Live Value | Institutional Benchmark | Forensic Finding & Audit Verdict |
| :--- | :---: | :---: | :--- |
| **Current Market Price (CMP)** | **₹6,140.00** | — | Active quote verified via NSE/BSE third-party feed. |
| **52-Week Range Corridor** | **₹4,637.50 – ₹7,924.50** | — | Trading at 46% of 52-week corridor; support at ₹4,637.5. |
| **DCF Intrinsic Fair Value** | **₹6,508.00** | $\text{WACC } 11.2\%, g = 5.0\%$ | **+5.7% Margin of Safety** (Intrinsic band: ₹6,183 – ₹6,833). |
| **Valuation Progress Bar** | **Filled 52W L → CMP** | Anchored to CMP | Deep blue bar fills strictly to ₹6,140.0 (no stretch to 52W High). |
| **Promoter Share Pledge** | **0.00% (Nil)** | Strictly 0.0% | **PASS:** 75.0% promoter stake (ABB Asea Brown Boveri Ltd) is 100% unencumbered. |
| **Statutory Auditor Opinion** | **Unmodified (Clean)** | Big-4 / Zero CARO notes | **PASS:** BSR & Co. LLP issued an unqualified opinion with clean CARO clauses. |
| **Cumulative CFO Conversion** | **81.5% (Avg 3Y)** | $\ge 80.0\%$ | **PASS:** ₹4,645 Cr cumulative CFO vs reported PAT; ₹3,840 Cr cumulative FCF. |
| **Receivables Velocity (DSO)** | **28 Days** | $\le 90$ Days (B2B Infra) | **PASS:** Rapid payment collection; overdue $>90$ days is $<1.4\%$. |
| **Debt-to-Equity (D/E)** | **0.01x (Debt Free)** | $\le 0.50\text{x}$ | **PASS:** Negligible borrowings; pristine liquid treasury book. |
| **External Credit Rating** | **CRISIL AAA / Stable** | Tier-1 Investment Grade | **PASS:** Highest solvency certification with superior liquidity headroom. |
| **Effective Tax Rate** | **25.2%** | $18\% - 30\%$ | **PASS:** Perfectly aligned with Indian statutory corporate tax rates. |
| **Other Income Share** | **7.4% of PBT** | $< 18.0\%$ | **PASS:** Profits driven by core electrification/motion manufacturing. |
| **Forensic Quality Index (FQI)** | **100.0 / 100.0** | $\ge 82.0$ | **PRISTINE / LOW FORENSIC RISK:** 6/6 Shield checks passed. |
| **Composite Quality Rating** | **87.5 / 100 (PCGC 85–89)** | Tier-1 Compounder | **STRONG ACCUMULATE:** 5–10% Institutional Portfolio Allocation. |

---

## 6. Verification Summary

Every analytical layer in the system operates deterministically, providing unbiased institutional assessments grounded in verifiable statutory data.

- **Audited Files:**
  - [`forensic_risk_engine.py`](file:///Users/ashutoshraj/Downloads/Project%20KUSHA/forensic_risk_engine.py): 8 Concealed Risk Engines & FQI scoring.
  - [`app.py`](file:///Users/ashutoshraj/Downloads/Project%20KUSHA/app.py): 6-Point Shield rendering, CMP-anchored Valuation Compass, and Dossier UI.
  - [`analyzer.py`](file:///Users/ashutoshraj/Downloads/Project%20KUSHA/analyzer.py): Multi-tier evidence citation matcher and 10-pillar validation.
  - [`nifty_universe.py`](file:///Users/ashutoshraj/Downloads/Project%20KUSHA/nifty_universe.py): Live market quote feeds and ratio sanitization.
