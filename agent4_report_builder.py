# ============================================================
# AGENT 4 — REPORT BUILDER
# Project: AI Stock Intelligence Agent System
# Author:  Abu John
# Purpose: Read report_insights.json from Agent 3 and build
#          a polished, self-contained HTML report that can be
#          opened in any browser — no server needed.
#
# CONCEPT: The "renderer" agent. Takes structured narrative
#          text and data, and assembles a professional HTML
#          dashboard. This is what you present in your portfolio.
# ============================================================

import json
import os
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# ── SETUP ─────────────────────────────────────────────────────────────────────
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ── RATING COLOUR MAP ─────────────────────────────────────────────────────────
RATING_COLOURS = {
    "Strong Buy": "#00c853",
    "Buy":        "#69f0ae",
    "Hold":       "#ffd740",
    "Watch":      "#ff9100",
    "Avoid":      "#ff1744",
}

RATING_BG = {
    "Strong Buy": "#00c85322",
    "Buy":        "#69f0ae22",
    "Hold":       "#ffd74022",
    "Watch":      "#ff910022",
    "Avoid":      "#ff174422",
}


# ── HELPER: SCORE BAR ─────────────────────────────────────────────────────────
def score_bar(score, rating):
    colour = RATING_COLOURS.get(rating, "#888")
    return f"""
    <div class="score-bar-wrap">
      <div class="score-bar" style="width:{score}%;background:{colour};"></div>
      <span class="score-label">{score}</span>
    </div>"""


# ── HELPER: METRIC PILL ───────────────────────────────────────────────────────
def metric_pill(label, value, suffix=""):
    if value is None:
        display = "N/A"
    else:
        display = f"{value}{suffix}"
    return f'<span class="pill"><span class="pill-label">{label}</span><span class="pill-value">{display}</span></span>'


# ── BUILD HTML ────────────────────────────────────────────────────────────────
def build_html(insights, stock_data):
    """
    Assembles the full HTML report from insights and raw stock data.
    """

    report_date  = insights.get("report_date", datetime.today().strftime("%Y-%m-%d"))
    generated_at = insights.get("generated_at", "")
    universe     = insights.get("universe_size", 0)
    avg_india    = insights.get("avg_score_india", "N/A")
    avg_global   = insights.get("avg_score_global", "N/A")
    top3         = insights.get("top_3", [])
    rating_dist  = insights.get("rating_distribution", {})
    sections     = insights.get("sections", {})

    stocks       = stock_data.get("stocks", [])
    ranked       = sorted(
        [s for s in stocks if s.get("status") == "success"],
        key=lambda x: x.get("composite_score", 0),
        reverse=True
    )

    # ── RATING DISTRIBUTION BARS ───────────────────────────────────────────────
    rating_bars_html = ""
    for rating, count in rating_dist.items():
        colour = RATING_COLOURS.get(rating, "#888")
        pct    = round((count / universe) * 100)
        rating_bars_html += f"""
        <div class="dist-row">
          <span class="dist-label">{rating}</span>
          <div class="dist-bar-wrap">
            <div class="dist-bar" style="width:{pct}%;background:{colour}"></div>
          </div>
          <span class="dist-count">{count}</span>
        </div>"""

    # ── TOP 3 CARDS ────────────────────────────────────────────────────────────
    top3_cards_html = ""
    medals = ["🥇", "🥈", "🥉"]
    for i, stock in enumerate(ranked[:3]):
        colour = RATING_COLOURS.get(stock.get("rating", "Hold"), "#888")
        bg     = RATING_BG.get(stock.get("rating", "Hold"), "#88888822")
        top3_cards_html += f"""
        <div class="top-card" style="border-top:4px solid {colour};background:{bg}">
          <div class="top-medal">{medals[i]}</div>
          <div class="top-name">{stock['company']}</div>
          <div class="top-ticker">{stock['ticker']}</div>
          <div class="top-score">{stock.get('composite_score','N/A')}<span>/100</span></div>
          <div class="top-rating" style="color:{colour}">{stock.get('rating','N/A')}</div>
          <div class="top-pills">
            {metric_pill("Rev Gr", stock.get('revenue_growth_pct'), "%")}
            {metric_pill("Margin", stock.get('net_margin_pct'), "%")}
            {metric_pill("ROE", stock.get('roe_pct'), "%")}
          </div>
        </div>"""

    # ── FULL STOCK TABLE ───────────────────────────────────────────────────────
    table_rows_html = ""
    for i, s in enumerate(ranked):
        colour  = RATING_COLOURS.get(s.get("rating", "Hold"), "#888")
        bg      = RATING_BG.get(s.get("rating", "Hold"), "#88888811")
        market_badge = (
            '<span class="badge india">India</span>'
            if s.get("market") == "India"
            else '<span class="badge global">Global</span>'
        )

        def fmt(val, suffix=""):
            return f"{val}{suffix}" if val is not None else "—"

        table_rows_html += f"""
        <tr style="background:{bg}" class="stock-row">
          <td class="rank">{i+1}</td>
          <td>
            <div class="stock-name">{s['company']}</div>
            <div class="stock-ticker">{s['ticker']}</div>
          </td>
          <td>{market_badge}</td>
          <td class="category-cell">{s.get('category','—')}</td>
          <td>
            {score_bar(s.get('composite_score', 0), s.get('rating','Hold'))}
          </td>
          <td style="color:{colour};font-weight:700">{s.get('rating','—')}</td>
          <td class="num">{fmt(s.get('revenue_growth_pct'),"%")}</td>
          <td class="num">{fmt(s.get('net_margin_pct'),"%")}</td>
          <td class="num">{fmt(s.get('roe_pct'),"%")}</td>
          <td class="num">{fmt(s.get('debt_to_equity'))}</td>
          <td class="num">{fmt(s.get('price_cagr_3yr_pct'),"%")}</td>
        </tr>"""

    # ── SECTION PROSE ─────────────────────────────────────────────────────────
    def prose_section(title, key, icon=""):
        text = sections.get(key, "")
        paragraphs = "".join(f"<p>{p.strip()}</p>" for p in text.split("\n") if p.strip())
        return f"""
        <section class="prose-section">
          <h2>{icon} {title}</h2>
          <div class="prose">{paragraphs}</div>
        </section>"""

    # Top picks section (preserve formatting)
    top_picks_raw = sections.get("top_picks", "")
    top_picks_html = ""
    blocks = top_picks_raw.strip().split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue
        header = lines[0].replace("**", "").strip()
        body   = " ".join(lines[1:]).strip()
        if header:
            top_picks_html += f"""
            <div class="pick-card">
              <div class="pick-header">{header}</div>
              <p>{body}</p>
            </div>"""

    # ── FULL HTML ──────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Stock Intelligence Report — {report_date}</title>
  <style>
    /* ── RESET & BASE ──────────────────────────────────────── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0d0f14;
      color: #e0e4ef;
      min-height: 100vh;
    }}

    /* ── HEADER ────────────────────────────────────────────── */
    header {{
      background: linear-gradient(135deg, #0f1923 0%, #1a2744 50%, #0f1923 100%);
      border-bottom: 1px solid #2a3a5c;
      padding: 40px 60px 32px;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
    }}
    .report-label {{
      font-size: 11px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: #5b9cf6;
      margin-bottom: 8px;
    }}
    h1 {{
      font-size: 28px;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.2;
    }}
    .header-meta {{
      text-align: right;
      font-size: 12px;
      color: #8899bb;
      line-height: 1.8;
    }}
    .header-stats {{
      display: flex;
      gap: 40px;
      margin-top: 28px;
      padding-top: 24px;
      border-top: 1px solid #2a3a5c;
      flex-wrap: wrap;
    }}
    .hstat {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .hstat-value {{
      font-size: 32px;
      font-weight: 700;
      color: #5b9cf6;
    }}
    .hstat-label {{
      font-size: 11px;
      color: #8899bb;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}

    /* ── MAIN LAYOUT ────────────────────────────────────────── */
    main {{ max-width: 1400px; margin: 0 auto; padding: 40px 40px 80px; }}

    /* ── SECTION TITLES ─────────────────────────────────────── */
    .section-title {{
      font-size: 13px;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: #5b9cf6;
      margin: 48px 0 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid #1e2d4a;
    }}

    /* ── DASHBOARD ROW ───────────────────────────────────────── */
    .dashboard-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .dashboard-card {{
      background: #131824;
      border: 1px solid #1e2d4a;
      border-radius: 10px;
      padding: 24px;
    }}
    .dashboard-card h3 {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #8899bb;
      margin-bottom: 16px;
    }}

    /* ── SCORE COMPARISON ─────────────────────────────────────── */
    .score-compare {{ display: flex; flex-direction: column; gap: 14px; }}
    .sc-row {{ display: flex; align-items: center; gap: 12px; }}
    .sc-market {{
      width: 70px;
      font-size: 13px;
      color: #c0ccdd;
      font-weight: 600;
    }}
    .sc-bar-wrap {{
      flex: 1;
      background: #0d1520;
      border-radius: 4px;
      height: 20px;
      overflow: hidden;
    }}
    .sc-bar {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.6s ease;
    }}
    .sc-val {{
      width: 50px;
      text-align: right;
      font-size: 18px;
      font-weight: 700;
      color: #fff;
    }}

    /* ── RATING DISTRIBUTION ─────────────────────────────────── */
    .dist-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .dist-label {{
      width: 95px;
      font-size: 12px;
      color: #c0ccdd;
    }}
    .dist-bar-wrap {{
      flex: 1;
      background: #0d1520;
      border-radius: 4px;
      height: 16px;
      overflow: hidden;
    }}
    .dist-bar {{
      height: 100%;
      border-radius: 4px;
      min-width: 4px;
    }}
    .dist-count {{
      width: 20px;
      text-align: right;
      font-size: 13px;
      font-weight: 700;
      color: #fff;
    }}

    /* ── TOP 3 PODIUM ─────────────────────────────────────────── */
    .top3-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 8px;
    }}
    .top-card {{
      background: #131824;
      border: 1px solid #1e2d4a;
      border-radius: 10px;
      padding: 24px;
      text-align: center;
    }}
    .top-medal  {{ font-size: 28px; margin-bottom: 8px; }}
    .top-name   {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
    .top-ticker {{ font-size: 12px; color: #8899bb; margin-bottom: 12px; }}
    .top-score  {{ font-size: 36px; font-weight: 800; color: #fff; line-height: 1; margin-bottom: 6px; }}
    .top-score span {{ font-size: 14px; color: #8899bb; font-weight: 400; }}
    .top-rating {{ font-size: 13px; font-weight: 700; margin-bottom: 12px; }}
    .top-pills  {{ display: flex; justify-content: center; flex-wrap: wrap; gap: 6px; }}

    /* ── PILLS ──────────────────────────────────────────────── */
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #0d1520;
      border: 1px solid #2a3a5c;
      border-radius: 20px;
      padding: 3px 10px;
      font-size: 11px;
    }}
    .pill-label {{ color: #8899bb; }}
    .pill-value {{ color: #e0e4ef; font-weight: 600; }}

    /* ── STOCK TABLE ─────────────────────────────────────────── */
    .table-wrap {{
      overflow-x: auto;
      border-radius: 10px;
      border: 1px solid #1e2d4a;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    thead th {{
      background: #0d1520;
      color: #8899bb;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      padding: 12px 14px;
      text-align: left;
      white-space: nowrap;
      position: sticky;
      top: 0;
    }}
    .stock-row td {{ padding: 11px 14px; border-bottom: 1px solid #1a2030; }}
    .stock-row:hover {{ filter: brightness(1.1); }}
    .stock-row:last-child td {{ border-bottom: none; }}
    .rank {{ color: #5b9cf6; font-weight: 700; font-size: 14px; }}
    .stock-name  {{ font-weight: 600; color: #fff; }}
    .stock-ticker{{ font-size: 11px; color: #8899bb; }}
    .num {{ text-align: right; color: #c0ccdd; font-variant-numeric: tabular-nums; }}
    .category-cell {{ font-size: 11px; color: #8899bb; }}

    .badge {{
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 20px;
      letter-spacing: 0.5px;
    }}
    .badge.india  {{ background: #ff670022; color: #ff9100; border: 1px solid #ff910055; }}
    .badge.global {{ background: #5b9cf622; color: #5b9cf6; border: 1px solid #5b9cf655; }}

    /* ── SCORE BAR ────────────────────────────────────────────── */
    .score-bar-wrap {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 120px;
    }}
    .score-bar {{
      height: 6px;
      border-radius: 3px;
      flex: 1;
      max-width: 100px;
    }}
    .score-label {{ font-size: 13px; font-weight: 700; color: #fff; }}

    /* ── PROSE SECTIONS ──────────────────────────────────────── */
    .prose-section {{
      background: #131824;
      border: 1px solid #1e2d4a;
      border-radius: 10px;
      padding: 32px 36px;
      margin-bottom: 20px;
    }}
    .prose-section h2 {{
      font-size: 18px;
      color: #fff;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid #1e2d4a;
    }}
    .prose p {{
      color: #bbc8dd;
      line-height: 1.75;
      margin-bottom: 16px;
      font-size: 14px;
    }}
    .prose p:last-child {{ margin-bottom: 0; }}

    /* ── TOP PICKS ────────────────────────────────────────────── */
    .picks-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    .pick-card {{
      background: #0d1520;
      border: 1px solid #1e2d4a;
      border-radius: 8px;
      padding: 20px;
    }}
    .pick-header {{
      font-size: 14px;
      font-weight: 700;
      color: #5b9cf6;
      margin-bottom: 10px;
    }}
    .pick-card p {{
      font-size: 13px;
      color: #bbc8dd;
      line-height: 1.65;
    }}

    /* ── FOOTER ───────────────────────────────────────────────── */
    footer {{
      text-align: center;
      padding: 40px;
      border-top: 1px solid #1e2d4a;
      color: #4a5a7a;
      font-size: 12px;
      line-height: 1.8;
    }}

    @media (max-width: 800px) {{
      header {{ padding: 24px; }}
      main   {{ padding: 20px; }}
      .dashboard-row {{ grid-template-columns: 1fr; }}
      .top3-grid     {{ grid-template-columns: 1fr; }}
      .picks-grid    {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>

<!-- ── HEADER ─────────────────────────────────────────────────────────── -->
<header>
  <div class="header-top">
    <div>
      <div class="report-label">AI Stock Intelligence Report</div>
      <h1>India &amp; Global AI Stocks<br>Investment Analysis</h1>
    </div>
    <div class="header-meta">
      <div>Report Date: <strong style="color:#e0e4ef">{report_date}</strong></div>
      <div>Generated:   <strong style="color:#e0e4ef">{generated_at}</strong></div>
      <div>Author: <strong style="color:#e0e4ef">Abu John</strong></div>
      <div>Powered by: <strong style="color:#5b9cf6">Claude Sonnet (Anthropic)</strong></div>
    </div>
  </div>
  <div class="header-stats">
    <div class="hstat">
      <span class="hstat-value">{universe}</span>
      <span class="hstat-label">Stocks Analysed</span>
    </div>
    <div class="hstat">
      <span class="hstat-value">{avg_india}</span>
      <span class="hstat-label">India Avg Score</span>
    </div>
    <div class="hstat">
      <span class="hstat-value">{avg_global}</span>
      <span class="hstat-label">Global Avg Score</span>
    </div>
    <div class="hstat">
      <span class="hstat-value" style="color:#00c853">{top3[0] if top3 else '—'}</span>
      <span class="hstat-label">Top Ranked Stock</span>
    </div>
  </div>
</header>

<main>

  <!-- ── DASHBOARD ─────────────────────────────────────────────────── -->
  <div class="section-title">Dashboard Overview</div>
  <div class="dashboard-row">

    <div class="dashboard-card">
      <h3>Average Composite Score — India vs Global</h3>
      <div class="score-compare">
        <div class="sc-row">
          <span class="sc-market">🇮🇳 India</span>
          <div class="sc-bar-wrap">
            <div class="sc-bar" style="width:{avg_india}%;background:#ff9100;"></div>
          </div>
          <span class="sc-val">{avg_india}</span>
        </div>
        <div class="sc-row">
          <span class="sc-market">🌐 Global</span>
          <div class="sc-bar-wrap">
            <div class="sc-bar" style="width:{avg_global}%;background:#5b9cf6;"></div>
          </div>
          <span class="sc-val">{avg_global}</span>
        </div>
      </div>
    </div>

    <div class="dashboard-card">
      <h3>Rating Distribution — All {universe} Stocks</h3>
      {rating_bars_html}
    </div>

  </div>

  <!-- ── TOP 3 ──────────────────────────────────────────────────────── -->
  <div class="section-title">Top 3 Stocks</div>
  <div class="top3-grid">
    {top3_cards_html}
  </div>

  <!-- ── EXEC SUMMARY ───────────────────────────────────────────────── -->
  <div class="section-title">Report</div>
  {prose_section("Executive Summary", "executive_summary", "📋")}

  <!-- ── INDIA ──────────────────────────────────────────────────────── -->
  {prose_section("India Deep Dive", "india_analysis", "🇮🇳")}

  <!-- ── GLOBAL ─────────────────────────────────────────────────────── -->
  {prose_section("Global AI Leaders", "global_analysis", "🌐")}

  <!-- ── COMPARISON ─────────────────────────────────────────────────── -->
  {prose_section("India vs Global Comparison", "india_vs_global", "⚖️")}

  <!-- ── TOP PICKS ──────────────────────────────────────────────────── -->
  <section class="prose-section">
    <h2>🏆 Top Stock Picks</h2>
    <div class="picks-grid">
      {top_picks_html}
    </div>
  </section>

  <!-- ── RISKS ──────────────────────────────────────────────────────── -->
  {prose_section("Risk Factors", "risk_factors", "⚠️")}

  <!-- ── FULL STOCK TABLE ───────────────────────────────────────────── -->
  <div class="section-title">Full Universe — All {universe} Stocks Ranked</div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Company</th>
          <th>Market</th>
          <th>Category</th>
          <th>Score</th>
          <th>Rating</th>
          <th>Rev Gr %</th>
          <th>Net Margin %</th>
          <th>ROE %</th>
          <th>D/E</th>
          <th>3Y CAGR %</th>
        </tr>
      </thead>
      <tbody>
        {table_rows_html}
      </tbody>
    </table>
  </div>

</main>

<!-- ── FOOTER ─────────────────────────────────────────────────────────── -->
<footer>
  <p>AI Stock Intelligence Report &nbsp;·&nbsp; Author: Abu John &nbsp;·&nbsp; {report_date}</p>
  <p>Powered by Claude Sonnet (Anthropic) &nbsp;·&nbsp; Data sourced from Yahoo Finance via yfinance</p>
  <p style="margin-top:8px;color:#2a3a5c">
    This report is for educational and portfolio purposes only.<br>
    Not financial advice. Always do your own research before investing.
  </p>
</footer>

</body>
</html>"""

    return html


# ── MAIN AGENT FUNCTION ────────────────────────────────────────────────────────
def run_agent4():

    print("\n" + "=" * 60)
    print("AGENT 4 — REPORT BUILDER")
    print(f"Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load data from Agent 3
    print("\nLoading report_insights.json from Agent 3...")
    if not os.path.exists("report_insights.json"):
        print("ERROR: report_insights.json not found. Run Agent 3 first.")
        return

    with open("report_insights.json", "r") as f:
        insights = json.load(f)

    # Also load raw stock data for the full table
    print("Loading analysis_results.json for stock table...")
    if not os.path.exists("analysis_results.json"):
        print("ERROR: analysis_results.json not found. Run Agent 2 first.")
        return

    with open("analysis_results.json", "r") as f:
        stock_data = json.load(f)

    print("\nBuilding HTML report...")
    html = build_html(insights, stock_data)

    # Save the report
    output_file = "ai_stock_report.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nReport saved: {output_file}")
    print(f"File size:    {round(os.path.getsize(output_file) / 1024, 1)} KB")
    print(f"\nOpen in browser:")
    print(f"  start {output_file}")
    print("\nAgent 4 complete. Pipeline finished.")
    print("=" * 60)


# ── RUN ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_agent4()