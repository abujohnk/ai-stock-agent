# ============================================================
# AGENT 1 — LIVE DATA FETCHER
# Project: AI Stock Intelligence Agent System
# Author:  Abu John
# Purpose: Fetch real-time stock data for 29 AI & Tech stocks
#          across India and Global markets
# ============================================================

import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv
import os

# ── SETUP ────────────────────────────────────────────────────────────────────
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── STOCK UNIVERSE ────────────────────────────────────────────────────────────

LARGE_CAP_INDIAN_IT = {
    "TCS.NS":       "TCS",
    "INFY.NS":      "Infosys",
    "HCLTECH.NS":   "HCL Technologies",
    "WIPRO.NS":     "Wipro",
}

MID_CAP_INDIAN_IT = {
    "PERSISTENT.NS": "Persistent Systems",
    "TATAELXSI.NS":  "Tata Elxsi",
    "MPHASIS.NS":    "Mphasis",
    "OFSS.NS":       "Oracle Fin. Services",
}

SMALL_CAP_INDIAN_TECH = {
    "AFFLE.NS":   "Affle India",
    "CYIENT.NS":  "Cyient",
    "INTELLECT.NS": "Intellect Design Arena",
}

INDIAN_AI_PURE_PLAYS = {
    "SAKSOFT.NS":    "Saksoft",
    "NEWGEN.NS":     "Newgen Software",
    "ZENSARTECH.NS": "Zensar Technologies",
}

INDIAN_SEMICONDUCTOR = {
    "DIXON.NS":  "Dixon Technologies",
    "KAYNES.NS": "Kaynes Technology",
}

GLOBAL_AI_LEADERS = {
    "NVDA":  "NVIDIA",
    "MSFT":  "Microsoft",
    "GOOGL": "Alphabet",
    "META":  "Meta Platforms",
    "PLTR":  "Palantir",
}

GLOBAL_AI_MID_TIER = {
    "AMD":  "AMD",
    "CRM":  "Salesforce",
    "NOW":  "ServiceNow",
    "SNOW": "Snowflake",
}

GLOBAL_AI_INFRASTRUCTURE = {
    "AMZN": "Amazon",
    "ORCL": "Oracle",
    "IBM":  "IBM",
}

# ── CATEGORY MAP ─────────────────────────────────────────────────────────────

CATEGORY_MAP = {}
for ticker in LARGE_CAP_INDIAN_IT:
    CATEGORY_MAP[ticker] = "Large Cap Indian IT"
for ticker in MID_CAP_INDIAN_IT:
    CATEGORY_MAP[ticker] = "Mid Cap Indian IT"
for ticker in SMALL_CAP_INDIAN_TECH:
    CATEGORY_MAP[ticker] = "Small Cap Indian Tech"
for ticker in INDIAN_AI_PURE_PLAYS:
    CATEGORY_MAP[ticker] = "Indian AI Pure Play"
for ticker in INDIAN_SEMICONDUCTOR:
    CATEGORY_MAP[ticker] = "Indian Semiconductor"
for ticker in GLOBAL_AI_LEADERS:
    CATEGORY_MAP[ticker] = "Global AI Leader"
for ticker in GLOBAL_AI_MID_TIER:
    CATEGORY_MAP[ticker] = "Global AI Mid Tier"
for ticker in GLOBAL_AI_INFRASTRUCTURE:
    CATEGORY_MAP[ticker] = "Global AI Infrastructure"


# ── FETCH ONE STOCK ───────────────────────────────────────────────────────────

def fetch_stock_data(ticker, company_name, market):

    try:
        stock         = yf.Ticker(ticker)
        info          = stock.info
        history       = stock.history(period="5y")
        financials    = stock.financials
        balance_sheet = stock.balance_sheet

        current_price  = info.get("currentPrice") or info.get("regularMarketPrice")
        market_cap     = info.get("marketCap")
        pe_ratio       = info.get("trailingPE")
        revenue        = info.get("totalRevenue")
        net_income     = info.get("netIncomeToCommon")
        gross_margin   = info.get("grossMargins")
        profit_margin  = info.get("profitMargins")
        roe            = info.get("returnOnEquity")
        debt_to_equity = info.get("debtToEquity")
        free_cashflow  = info.get("freeCashflow")
        week_52_high   = info.get("fiftyTwoWeekHigh")
        week_52_low    = info.get("fiftyTwoWeekLow")
        currency       = info.get("currency", "Unknown")

        # Revenue growth YoY
        revenue_growth  = None
        revenue_history = {}

        if financials is not None and not financials.empty:
            rev_row = None
            for label in ["Total Revenue", "Revenue"]:
                if label in financials.index:
                    rev_row = financials.loc[label]
                    break

            if rev_row is not None:
                rev_sorted = rev_row.sort_index()
                for date, value in rev_sorted.items():
                    if value and not pd.isna(value):
                        revenue_history[str(date.year)] = round(float(value), 0)

                values = [v for v in rev_sorted.values if v and not pd.isna(v)]
                if len(values) >= 2:
                    latest   = values[-1]
                    previous = values[-2]
                    if previous and previous != 0:
                        revenue_growth = round(((latest - previous) / abs(previous)) * 100, 2)

        # 3-year price CAGR (750 trading days ≈ 3 years)
        price_cagr_3yr = None
        if not history.empty and len(history) > 750:
            start_price = float(history["Close"].iloc[0])
            end_price   = float(history["Close"].iloc[-1])
            if start_price > 0:
                price_cagr_3yr = round(((end_price / start_price) ** (1/3) - 1) * 100, 2)

        return {
            "company":            company_name,
            "ticker":             ticker,
            "market":             market,
            "category":           CATEGORY_MAP.get(ticker, "Unknown"),
            "currency":           currency,
            "fetch_date":         datetime.today().strftime("%Y-%m-%d"),
            "current_price":      current_price,
            "week_52_high":       week_52_high,
            "week_52_low":        week_52_low,
            "market_cap":         market_cap,
            "pe_ratio":           pe_ratio,
            "revenue":            revenue,
            "net_income":         net_income,
            "gross_margin_pct":   round(gross_margin * 100, 2) if gross_margin else None,
            "net_margin_pct":     round(profit_margin * 100, 2) if profit_margin else None,
            "roe_pct":            round(roe * 100, 2) if roe else None,
            "debt_to_equity":     debt_to_equity,
            "free_cashflow":      free_cashflow,
            "revenue_growth_pct": revenue_growth,
            "price_cagr_3yr_pct": price_cagr_3yr,
            "revenue_history":    revenue_history,
            "status":             "success"
        }

    except Exception as e:
        print(f"    WARNING: Could not fetch {company_name} ({ticker}): {e}")
        return {
            "company":  company_name,
            "ticker":   ticker,
            "market":   market,
            "category": CATEGORY_MAP.get(ticker, "Unknown"),
            "status":   "error",
            "error":    str(e)
        }


# ── MAIN AGENT FUNCTION ───────────────────────────────────────────────────────

def run_agent1():

    print("\n" + "=" * 60)
    print("AGENT 1 — LIVE DATA FETCHER")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Universe: 29 AI & Tech stocks across 8 categories")
    print("=" * 60)

    all_stock_data = []

    # Indian stocks
    print("\nFetching Indian AI stocks...")
    indian_categories = [
        ("Large Cap Indian IT",   LARGE_CAP_INDIAN_IT),
        ("Mid Cap Indian IT",     MID_CAP_INDIAN_IT),
        ("Small Cap Indian Tech", SMALL_CAP_INDIAN_TECH),
        ("Indian AI Pure Plays",  INDIAN_AI_PURE_PLAYS),
        ("Indian Semiconductor",  INDIAN_SEMICONDUCTOR),
    ]
    for category_name, stocks in indian_categories:
        print(f"\n  [{category_name}]")
        for ticker, name in stocks.items():
            print(f"    Fetching {name} ({ticker})...")
            all_stock_data.append(fetch_stock_data(ticker, name, "India"))

    # Global stocks
    print("\nFetching Global AI stocks...")
    global_categories = [
        ("Global AI Leaders",        GLOBAL_AI_LEADERS),
        ("Global AI Mid Tier",       GLOBAL_AI_MID_TIER),
        ("Global AI Infrastructure", GLOBAL_AI_INFRASTRUCTURE),
    ]
    for category_name, stocks in global_categories:
        print(f"\n  [{category_name}]")
        for ticker, name in stocks.items():
            print(f"    Fetching {name} ({ticker})...")
            all_stock_data.append(fetch_stock_data(ticker, name, "Global"))

    # Count results
    successful = [s for s in all_stock_data if s["status"] == "success"]
    failed     = [s for s in all_stock_data if s["status"] == "error"]

    print(f"\nFetch complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        for f in failed:
            print(f"  FAILED: {f['company']} ({f['ticker']}): {f.get('error')}")

    # Claude validates the data
    print("\nAsking Claude to validate data quality...")

    sample = []
    for stock in successful[:6]:
        sample.append({
            "company":        stock["company"],
            "market":         stock["market"],
            "category":       stock["category"],
            "current_price":  stock["current_price"],
            "market_cap":     stock["market_cap"],
            "net_margin_pct": stock["net_margin_pct"],
            "roe_pct":        stock["roe_pct"],
            "revenue_growth": stock["revenue_growth_pct"],
        })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""You are a financial data quality validator.
I fetched live stock data for {len(successful)} AI and tech companies (India + Global).
Sample of {len(sample)} companies:
{json.dumps(sample, indent=2)}

Please:
1. Confirm data looks reasonable for each stock
2. Flag any suspicious or missing values
3. Give an overall data quality score out of 10
Max 200 words."""
        }]
    )

    claude_validation = response.content[0].text
    print("\nClaude Validation:")
    print("-" * 40)
    print(claude_validation)
    print("-" * 40)

    # Save to JSON for Agent 2
    output = {
        "fetch_date":        datetime.today().strftime("%Y-%m-%d"),
        "fetch_time":        datetime.now().strftime("%H:%M:%S"),
        "total_stocks":      len(all_stock_data),
        "successful":        len(successful),
        "failed":            len(failed),
        "claude_validation": claude_validation,
        "stocks":            all_stock_data
    }

    with open("stock_data.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nSaved to stock_data.json")
    print(f"Successful: {len(successful)} | Failed: {len(failed)}")
    print("\nAgent 1 complete. Passing to Agent 2.")
    print("=" * 60)

    return output


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_agent1()