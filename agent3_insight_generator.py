# ============================================================
# AGENT 3 — INSIGHT GENERATOR
# Project: AI Stock Intelligence Agent System
# Author:  Abu John
# Purpose: Read analysis_results.json from Agent 2 and use
#          Claude to write a full narrative investment report
#          covering the AI stock landscape across India and Global.
#
# CONCEPT: This is the "LLM as writer" pattern.
#          Agent 3 takes structured data and turns it into
#          human-quality narrative insight — something no
#          simple script could do on its own.
#          Maps to Course 5 visualisation/insight concepts.
# ============================================================

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# ── SETUP ─────────────────────────────────────────────────────────────────────
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── HELPER: BUILD STOCK SUMMARY TABLE ─────────────────────────────────────────
def build_stock_summary(stocks, market_filter=None, limit=None):
    """
    Builds a clean text summary table of stocks for Claude to read.
    Optionally filter by market (India / Global) and limit rows.
    """
    filtered = stocks
    if market_filter:
        filtered = [s for s in stocks if s["market"] == market_filter]
    if limit:
        filtered = filtered[:limit]

    lines = []
    for s in filtered:
        lines.append(
            f"  {s['company']:<25} | "
            f"Score: {s['composite_score']:>5} | "
            f"Rating: {s['rating']:<11} | "
            f"Rev Growth: {str(s.get('revenue_growth_pct','N/A')):>7}% | "
            f"Net Margin: {str(s.get('net_margin_pct','N/A')):>6}% | "
            f"ROE: {str(s.get('roe_pct','N/A')):>6}%"
        )
    return "\n".join(lines)


# ── SECTION 1: EXECUTIVE SUMMARY ──────────────────────────────────────────────
def generate_executive_summary(data):
    print("  Writing executive summary...")

    stocks      = data["stocks"]
    total       = data["total_stocks"]
    avg_india   = data["avg_score_india"]
    avg_global  = data["avg_score_global"]
    top3        = data["top_3"]
    rating_dist = data["rating_distribution"]

    prompt = f"""You are a senior equity research analyst writing the executive summary 
of a professional AI stock intelligence report dated {data['analysis_date']}.

Universe: {total} AI and technology stocks across India and Global markets.

Key findings:
- Average composite score — Indian stocks:  {avg_india}/100
- Average composite score — Global stocks:  {avg_global}/100
- Top 3 stocks overall: {', '.join(top3)}
- Rating distribution: {json.dumps(rating_dist)}

Top 5 stocks by composite score:
{build_stock_summary(stocks, limit=5)}

Write a compelling 3-paragraph executive summary that:
1. Opens with the big picture — where AI stocks stand right now
2. Highlights the India vs Global comparison and what it means
3. Closes with the key investment takeaway for this universe

Tone: professional, confident, data-driven. No bullet points. Flowing prose only.
Maximum 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── SECTION 2: INDIA DEEP DIVE ─────────────────────────────────────────────────
def generate_india_analysis(data):
    print("  Writing India deep dive...")

    indian_stocks = [s for s in data["stocks"] if s["market"] == "India"]
    indian_stocks.sort(key=lambda x: x["composite_score"], reverse=True)

    prompt = f"""You are a senior equity analyst specialising in Indian technology stocks.

Here are all {len(indian_stocks)} Indian AI and tech stocks ranked by composite score:

{build_stock_summary(indian_stocks)}

Write a 3-paragraph analysis covering:
1. The overall health of the Indian AI/IT sector based on these metrics
2. Which categories (Large Cap IT, Mid Cap IT, Pure Plays, Semiconductor) are 
   performing best and why
3. The standout stock from India and what makes it exceptional

Tone: analytical, specific, reference actual company names and numbers.
No bullet points. Flowing prose. Maximum 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── SECTION 3: GLOBAL DEEP DIVE ───────────────────────────────────────────────
def generate_global_analysis(data):
    print("  Writing Global deep dive...")

    global_stocks = [s for s in data["stocks"] if s["market"] == "Global"]
    global_stocks.sort(key=lambda x: x["composite_score"], reverse=True)

    prompt = f"""You are a senior equity analyst covering global AI technology stocks.

Here are all {len(global_stocks)} Global AI stocks ranked by composite score:

{build_stock_summary(global_stocks)}

Write a 3-paragraph analysis covering:
1. The dominant theme across global AI leaders — what's driving their scores
2. Which global AI segment (Leaders, Mid Tier, Infrastructure) shows the most 
   consistent strength
3. Any surprises — stocks that scored higher or lower than their reputation suggests

Tone: analytical, specific, reference actual company names and numbers.
No bullet points. Flowing prose. Maximum 200 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── SECTION 4: INDIA VS GLOBAL COMPARISON ─────────────────────────────────────
def generate_comparison(data):
    print("  Writing India vs Global comparison...")

    avg_india  = data["avg_score_india"]
    avg_global = data["avg_score_global"]

    indian_stocks = sorted(
        [s for s in data["stocks"] if s["market"] == "India"],
        key=lambda x: x["composite_score"], reverse=True
    )
    global_stocks = sorted(
        [s for s in data["stocks"] if s["market"] == "Global"],
        key=lambda x: x["composite_score"], reverse=True
    )

    # Average key metrics for each market
    def avg_metric(stocks, key):
        vals = [s.get(key) for s in stocks if s.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else "N/A"

    india_margins  = avg_metric(indian_stocks, "net_margin_pct")
    global_margins = avg_metric(global_stocks, "net_margin_pct")
    india_roe      = avg_metric(indian_stocks, "roe_pct")
    global_roe     = avg_metric(global_stocks, "roe_pct")
    india_growth   = avg_metric(indian_stocks, "revenue_growth_pct")
    global_growth  = avg_metric(global_stocks, "revenue_growth_pct")

    prompt = f"""You are writing the India vs Global comparison section of an AI stock report.

Summary statistics:
                    India       Global
Avg Composite Score {avg_india}        {avg_global}
Avg Net Margin %    {india_margins}%       {global_margins}%
Avg ROE %           {india_roe}%       {global_roe}%
Avg Revenue Growth  {india_growth}%       {global_growth}%

Top Indian stock:  {indian_stocks[0]['company']} — {indian_stocks[0]['composite_score']}/100
Top Global stock:  {global_stocks[0]['company']} — {global_stocks[0]['composite_score']}/100

Write 2 paragraphs:
1. A direct head-to-head comparison — where India wins, where Global wins
2. What this means for an investor deciding between Indian and Global AI exposure

Be specific with numbers. Flowing prose. Maximum 150 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── SECTION 5: TOP PICKS ──────────────────────────────────────────────────────
def generate_top_picks(data):
    print("  Writing top picks...")

    top5 = data["stocks"][:5]

    picks_text = ""
    for s in top5:
        note = s.get("analyst_note", "")
        picks_text += f"""
{s['company']} ({s['ticker']}) — {s['rating']} — Score: {s['composite_score']}/100
Revenue Growth: {s.get('revenue_growth_pct','N/A')}% | Net Margin: {s.get('net_margin_pct','N/A')}% | ROE: {s.get('roe_pct','N/A')}%
Analyst note: {note}
"""

    prompt = f"""You are writing the Top Stock Picks section of an AI investment report.

Here are the top 5 stocks from our universe:
{picks_text}

Write a short paragraph (2-3 sentences) for EACH stock that:
- States why it earned its ranking
- Highlights its single most impressive metric
- Gives a clear one-line investment case

Format each pick as:
[Company Name]
[Your 2-3 sentence paragraph]

Maximum 250 words total."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── SECTION 6: RISKS ──────────────────────────────────────────────────────────
def generate_risks(data):
    print("  Writing risk section...")

    avoid_watch = [
        s for s in data["stocks"]
        if s["rating"] in ["Avoid", "Watch"]
    ]

    low_scorers_text = "\n".join([
        f"  {s['company']} ({s['ticker']}) — Score: {s['composite_score']}/100 — {s['rating']}"
        for s in avoid_watch
    ])

    prompt = f"""You are writing the Risk Factors section of an AI stock report.

Stocks rated Watch or Avoid in our universe:
{low_scorers_text if low_scorers_text else "None — all stocks rated Hold or above"}

Write 2 paragraphs covering:
1. The specific risks shown by the weaker stocks in our universe
2. Broader sector risks facing AI stocks in both India and Global markets 
   (valuation, regulation, AI commoditisation, macro)

Be direct and honest. Flowing prose. Maximum 150 words."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


# ── MAIN AGENT FUNCTION ────────────────────────────────────────────────────────
def run_agent3():

    print("\n" + "=" * 60)
    print("AGENT 3 — INSIGHT GENERATOR")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load data from Agent 2
    print("\nLoading analysis_results.json from Agent 2...")

    if not os.path.exists("analysis_results.json"):
        print("ERROR: analysis_results.json not found. Run Agent 2 first.")
        return

    with open("analysis_results.json", "r") as f:
        data = json.load(f)

    print(f"Loaded analysis for {data['total_stocks']} stocks.")
    print("\nGenerating report sections (6 Claude calls — takes ~60 seconds)...\n")

    # Generate all sections
    report = {
        "report_date":          data["analysis_date"],
        "generated_at":         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "universe_size":        data["total_stocks"],
        "avg_score_india":      data["avg_score_india"],
        "avg_score_global":     data["avg_score_global"],
        "top_3":                data["top_3"],
        "rating_distribution":  data["rating_distribution"],
        "sections": {}
    }

    report["sections"]["executive_summary"] = generate_executive_summary(data)
    report["sections"]["india_analysis"]    = generate_india_analysis(data)
    report["sections"]["global_analysis"]   = generate_global_analysis(data)
    report["sections"]["india_vs_global"]   = generate_comparison(data)
    report["sections"]["top_picks"]         = generate_top_picks(data)
    report["sections"]["risk_factors"]      = generate_risks(data)

    # Save for Agent 4
    with open("report_insights.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print preview
    print("\n" + "=" * 60)
    print("REPORT PREVIEW")
    print("=" * 60)

    print("\n── EXECUTIVE SUMMARY ──")
    print(report["sections"]["executive_summary"])

    print("\n── TOP PICKS ──")
    print(report["sections"]["top_picks"])

    print("\n── RISK FACTORS ──")
    print(report["sections"]["risk_factors"])

    print(f"\nFull report saved to report_insights.json")
    print("\nAgent 3 complete. Passing to Agent 4.")
    print("=" * 60)

    return report


# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_agent3()