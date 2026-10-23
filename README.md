# 🇮🇳 FinScan India — AI Financial & Forensic Pillar Analyzer

A complete web platform built for analyzing Indian BSE/NSE listed companies by uploading their Annual Reports, Financial Statements, or Investor Presentations (PDF).

The app evaluates companies across **5 Fundamental Pillars** using forensic Indian accounting guidelines (Ind AS):
1. **📈 Profitability & Operating Growth** (Revenue CAGR, EBITDA margin expansion, pricing power)
2. **🔄 Capital Allocation & Return Efficiency** (ROCE, ROE, asset turnover)
3. **🛡️ Solvency, Leverage & Balance Sheet Strength** (Net Debt/EBITDA, Interest Coverage, working capital cycle)
4. **💵 Cash Flow Reality Check** (CFO to PAT conversion, Free Cash Flow)
5. **🔍 Corporate Governance & Forensic Red Flags** (Auditor qualifications, Related Party Transactions, Contingent liabilities, Promoter pledging)

---

## 🚀 How to Run the Website (Super Simple for Non-Coders)

### Option A: The 1-Click Launch (Mac Terminal)
Open your terminal inside this folder and run:
```bash
./run.sh
```
Your browser will open automatically at `http://localhost:8501`.

---

## 🔑 Getting Your Free Gemini API Key (Takes 60 seconds)
This application uses **Google Gemini 2.0 / 1.5 Flash**, which has a generous **100% Free Tier** (no credit card needed):
1. Go to [Google AI Studio](https://aistudio.google.com).
2. Sign in with your Google account.
3. Click **"Get API key"** -> **"Create API key"**.
4. Paste your key either:
   - In the left sidebar of the website when it opens, **OR**
   - In a file named `.env` in this directory:
     ```env
     GEMINI_API_KEY=your_actual_key_here
     ```

*(Don't have a key right now? No problem! Just check **"Run in Demo / Preview Mode"** in the sidebar to test all charts, scores, and features instantly!)*

---

## 📝 Customizing Your Prompt Model
You can plug in your custom prompt model in two easy ways:
1. **Directly from the website**: Open the **"🛠️ Custom Analysis Prompt"** section in the left sidebar and paste your prompt.
2. **In code**: Open [prompt_template.py](file:///Users/ashutoshraj/Downloads/Project%20KUSHA/prompt_template.py) and update `DEFAULT_ANALYSIS_PROMPT`.

---

## 🌐 How to Host it Free on the Internet (Streamlit Cloud)
To let anyone in India visit your website on a public URL (`https://your-project.streamlit.app`):
1. Create a free account at [GitHub.com](https://github.com) and push this folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
3. Select your repository, pick `app.py`, and click **Deploy**!
4. Under "Advanced settings", paste your `GEMINI_API_KEY`.
5. Your website is live and hosted for ₹0!
