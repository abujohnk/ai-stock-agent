# ============================================================
# AGENT 2 — FINANCIAL ANALYST
# Project: AI Stock Intelligence Agent System
# Author:  Abu John
# Purpose: Read stock_data.json from Agent 1, calculate
#          scores, rank stocks, and generate analyst notes
#          using Claude AI.
#
# CONCEPT: Agent 2 is the "brain" of the pipeline.
#          It takes raw data and turns it into insight.
#          This maps to DAX/modelling concepts from your
#          Power BI Course 4.
# ============================================================

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# ── SETUP ─────────────────────────────────────────────────────────────────────
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── SCORING ENGINE ─────────────────────────────────────────────────────────────
# CONCEPT: This is how analysts rank stocks systematically.
#          Each metric gets a score out of 100.
#          We weight them by importance and sum to a final score.
#
# Weights (must add to 100):
#   Revenue Growth  = 25  (are they growing?)
#   Net Margin      = 20  (are they profitable?)
#   ROE             = 20  (are they efficient?)
#   Price CAGR      = 20  (has the stock rewarded investors?)
#   Debt/Equity     = 15  (are they financially safe?)

WEIGHTS = {
    "revenue_growth": 25,
    "net_margin":     20,
    "roe":            20,
    "price_cagr":     20,
    "debt_equity":    15,
}

def score_metric(value, metric, market):
    """
    Converts a raw metric value into a score from 0 to 100.
    Different benchmarks apply for Indian vs Global stocks.
    """

    if value is None:
        return 50  # neutral score if data is missing

    # ── REVENUE GROWTH % ──────────────────────────────────────────────────────
    if metric == "revenue_growth":
        if value >= 25:  return 100
        if value >= 15:  return 80
        if value >= 10:  return 65
        if value >= 5:   return 50
        if value >= 0:   return 35
        return 10  # negative growth

    # ── NET MARGIN % ──────────────────────────────────────────────────────────
    elif metric == "net_margin":
        if market == "India":
            # Indian IT typically 15-25%
            if value >= 20:  return 100
            if value >= 15:  return 80
            if value >= 10:  return 60
            if value >= 5:   return 40
            return 20
        else:
            # Global tech varies widely
            if value >= 25:  return 100
            if value >= 15:  return 80
            if value >= 5:   return 60
            if value >= 0:   return 30
            return 10

    # ── RETURN ON EQUITY % ────────────────────────────────────────────────────
    elif metric == "roe":
        if value >= 30:  return 100
        if value >= 20:  return 80
        if value >= 15:  return 65
        if value >= 10:  return 50
        if value >= 0:   return 30
        return 10  # negative ROE

    # ── 3-YEAR PRICE CAGR % ───────────────────────────────────────────────────
    elif metric == "price_cagr":
        if value >= 30:  return 100
        if value >= 20:  return 85
        if value >= 10:  return 65
        if value >= 0:   return 45
        return 15  # negative CAGR

    # ── DEBT TO EQUITY ────────────────────────────────────────────────────────
    # Lower is better — we invert the scoring
    elif metric == "debt_equity":
        if value <= 0.1:   return 100  # very low debt
        if value <= 0.3:   return 80
        if value <= 0.5:   return 65
        if value <= 1.0:   return 45
        if value <= 2.0:   return 25
        return 10  # high debt

    return 50


def calculate_composite_score(stock):
    """
    Calculates a weighted composite score (0-100) for a stock.
    Returns the score and a breakdown of individual metric scores.
    """

    market = stock.get("market", "Global")

    scores = {
        "revenue_growth": score_metric(stock.get("revenue_growth_pct"), "revenue_growth", market),
        "net_margin":     score_metric(stock.get("net_margin_pct"),     "net_margin",     market),
        "roe":            score_metric(stock.get("roe_pct"),            "roe",            market),
        "price_cagr":     score_metric(stock.get("price_cagr_3yr_pct"), "price_cagr",     market),
        "debt_equity":    score_metric(stock.get("debt_to_equity"),     "debt_equity",    market),
    }

    # Weighted composite
    composite = sum(scores[metric] * (WEIGHTS[metric] / 100) for metric in scores)

    return round(composite, 1), scores


def assign_rating(score):
    """
    Converts a composite score into a simple analyst rating.
    """
    if score >= 75:  return "Strong Buy"
    if score >= 60:  return "Buy"
    if score >= 45:  return "Hold"
    if score >= 30:  return "Watch"
    return "Avoid"


def assign_rating_emoji(rating):
    emojis = {
        "Strong Buy": "🟢",
        "Buy":        "🔵",
        "Hold":       "🟡",
        "Watch":      "🟠",
        "Avoid":      "🔴",
    }
    return emojis.get(rating, "⚪")


# ── CURRENCY FORMATTING ────────────────────────────────────────────────────────
def format_market_cap(value, currency):
    """
    Formats market cap with correct currency label and unit.
    Fixes the currency ambiguity flagged by Claude in Agent 1.
    """
    if value is None:
        return "N/A"

    if currency == "INR":
        crore = value / 10_000_000
        if crore >= 100_000:
            return f"₹{crore/100_000:.1f}L Cr"
        return f"₹{crore:,.0f} Cr"
    else:
        billion = value / 1_000_000_000
        if billion >= 1000:
            return f"${billion/1000:.1f}T"
        return f"${billion:.1f}B"


# ── CLAUDE ANALYST NOTE ────────────────────────────────────────────────────────
def generate_analyst_note(stock, composite_score, rating, score_breakdown):
    """
    Asks Claude to write a short professional analyst note
    for this stock based on its metrics and score.

    CONCEPT: This is "LLM as analyst" — instead of hardcoding
    rules for every possible scenario, we let Claude reason
    about the numbers and write human-quality commentary.
    """

    prompt = f"""You are a professional equity analyst writing a brief stock note.

Company: {stock['company']} ({stock['ticker']})
Market: {stock['market']} | Category: {stock['category']}
Rating: {rating} | Composite Score: {composite_score}/100

Key Metrics:
- Revenue Growth (YoY): {stock.get('revenue_growth_pct', 'N/A')}%
- Net Margin: {stock.get('net_margin_pct', 'N/A')}%
- ROE: {stock.get('roe_pct', 'N/A')}%
- 3-Year Price CAGR: {stock.get('price_cagr_3yr_pct', 'N/A')}%
- Debt/Equity: {stock.get('debt_to_equity', 'N/A')}
- P/E Ratio: {stock.get('pe_ratio', 'N/A')}

Score Breakdown:
- Revenue Growth score: {score_breakdown['revenue_growth']}/100
- Net Margin score:     {score_breakdown['net_margin']}/100
- ROE score:           {score_breakdown['roe']}/100
- Price CAGR score:    {score_breakdown['price_cagr']}/100
- Debt/Equity score:   {score_breakdown['debt_equity']}/100

Write a 3-sentence analyst note covering:
1. What this company does well (its strongest metric)
2. What the key risk or weakness is
3. One-line investment conclusion matching the {rating} rating

Be concise, factual, and professional. No fluff."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


# ── MAIN AGENT FUNCTION ────────────────────────────────────────────────────────
def run_agent2():

    print("\n" + "=" * 60)
    print("AGENT 2 — FINANCIAL ANALYST")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── LOAD DATA FROM AGENT 1 ─────────────────────────────────────────────────
    print("\nLoading stock_data.json from Agent 1...")

    if not os.path.exists("stock_data.json"):
        print("ERROR: stock_data.json not found. Run Agent 1 first.")
        return

    with open("stock_data.json", "r") as f:
        agent1_data = json.load(f)

    stocks = [s for s in agent1_data["stocks"] if s["status"] == "success"]
    print(f"Loaded {len(stocks)} stocks for analysis.")

    # ── SCORE AND RANK ALL STOCKS ──────────────────────────────────────────────
    print("\nCalculating composite scores...")

    analysed_stocks = []

    for stock in stocks:
        composite_score, score_breakdown = calculate_composite_score(stock)
        rating = assign_rating(composite_score)
        emoji  = assign_rating_emoji(rating)

        analysed_stocks.append({
            **stock,
            "composite_score":  composite_score,
            "score_breakdown":  score_breakdown,
            "rating":           rating,
            "rating_emoji":     emoji,
            "market_cap_fmt":   format_market_cap(
                                    stock.get("market_cap"),
                                    stock.get("currency", "USD")
                                ),
        })

    # Sort by composite score descending
    analysed_stocks.sort(key=lambda x: x["composite_score"], reverse=True)

    # Print ranking table
    print(f"\n{'Rank':<5} {'Company':<25} {'Market':<8} {'Score':<8} {'Rating':<12}")
    print("-" * 65)
    for i, stock in enumerate(analysed_stocks, 1):
        print(
            f"{i:<5} "
            f"{stock['company']:<25} "
            f"{stock['market']:<8} "
            f"{stock['composite_score']:<8} "
            f"{stock['rating_emoji']} {stock['rating']}"
        )

    # ── GENERATE CLAUDE ANALYST NOTES ─────────────────────────────────────────
    # We generate notes for the top 10 stocks only to save API cost.
    # Agent 3 will use these notes in the final report.

    print(f"\nGenerating Claude analyst notes for top 10 stocks...")
    print("(This may take 30-60 seconds)\n")

    top_10 = analysed_stocks[:10]

    for i, stock in enumerate(top_10, 1):
        print(f"  Analysing {stock['company']} ({i}/10)...")
        note = generate_analyst_note(
            stock,
            stock["composite_score"],
            stock["rating"],
            stock["score_breakdown"]
        )
        stock["analyst_note"] = note

    # Add placeholder for remaining stocks
    for stock in analysed_stocks[10:]:
        stock["analyst_note"] = None

    # ── SUMMARY STATISTICS ────────────────────────────────────────────────────
    indian_stocks = [s for s in analysed_stocks if s["market"] == "India"]
    global_stocks = [s for s in analysed_stocks if s["market"] == "Global"]

    avg_score_india  = round(sum(s["composite_score"] for s in indian_stocks)  / len(indian_stocks), 1)  if indian_stocks  else 0
    avg_score_global = round(sum(s["composite_score"] for s in global_stocks) / len(global_stocks), 1) if global_stocks else 0

    rating_counts = {}
    for stock in analysed_stocks:
        r = stock["rating"]
        rating_counts[r] = rating_counts.get(r, 0) + 1

    print(f"\n{'='*60}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Average Score — Indian stocks:  {avg_score_india}/100")
    print(f"Average Score — Global stocks:  {avg_score_global}/100")
    print(f"\nRating Distribution:")
    for rating, count in sorted(rating_counts.items()):
        print(f"  {rating}: {count} stocks")

    top3 = analysed_stocks[:3]
    print(f"\nTop 3 Stocks Overall:")
    for i, s in enumerate(top3, 1):
        print(f"  {i}. {s['company']} ({s['ticker']}) — {s['composite_score']}/100 — {s['rating']}")

    # ── SAVE TO JSON FOR AGENT 3 ───────────────────────────────────────────────
    output = {
        "analysis_date":      datetime.today().strftime("%Y-%m-%d"),
        "analysis_time":      datetime.now().strftime("%H:%M:%S"),
        "total_stocks":       len(analysed_stocks),
        "avg_score_india":    avg_score_india,
        "avg_score_global":   avg_score_global,
        "rating_distribution": rating_counts,
        "top_3":              [s["company"] for s in top3],
        "stocks":             analysed_stocks
    }

    with open("analysis_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to analysis_results.json")
    print("\nAgent 2 complete. Passing to Agent 3.")
    print("=" * 60)

    return output


# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_agent2()