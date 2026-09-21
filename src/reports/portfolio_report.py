import datetime
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.reports.sector_report import generate_all_sector_reports
from src.reports.tearsheet import generate_all_tearsheets

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
PORTFOLIO_DIR = "reports/portfolio"


def build_portfolio_summary_pdf(db_path: str = DB_PATH, out_dir: str = PORTFOLIO_DIR) -> str:
    """Generate a single portfolio summary PDF with 1-page profile for all 92 companies."""
    os.makedirs(out_dir, exist_ok=True)
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    pdf_path = os.path.join(out_dir, f"portfolio_summary_{date_str}.pdf")

    query = """
    WITH latest_years AS (
        SELECT company_id, MAX(year) AS max_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        c.id AS ticker,
        c.company_name,
        c.about_company,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        r.*
    FROM latest_years ly
    JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
    JOIN companies c ON r.company_id = c.id
    LEFT JOIN sectors s ON r.company_id = s.company_id
    ORDER BY s.broad_sector, c.company_name
    """
    with sqlite3.connect(db_path) as conn:
        df_all = pd.read_sql(query, conn)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    cover_title = ParagraphStyle("CoverTitle", parent=styles["Heading1"], fontSize=22, leading=26, textColor=colors.HexColor("#1e3a8a"), alignment=TA_CENTER)
    cover_sub = ParagraphStyle("CoverSub", parent=styles["Normal"], fontSize=12, leading=16, textColor=colors.HexColor("#4b5563"), alignment=TA_CENTER)
    
    co_title = ParagraphStyle("CoTitle", parent=styles["Heading2"], fontSize=14, leading=16, textColor=colors.HexColor("#1e3a8a"), spaceAfter=2)
    meta_style = ParagraphStyle("CoMeta", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#4b5563"))
    body_style = ParagraphStyle("CoBody", parent=styles["Normal"], fontSize=7.5, leading=10)
    bold_cell = ParagraphStyle("BoldCell", parent=styles["Normal"], fontSize=7.5, leading=9, fontName="Helvetica-Bold")
    header_cell = ParagraphStyle("HCell", parent=styles["Normal"], fontSize=7.5, leading=9, fontName="Helvetica-Bold", textColor=colors.white)

    story = []

    # ================= COVER / EXECUTIVE SUMMARY PAGE =================
    story.append(Spacer(1, 100))
    story.append(Paragraph("<b>NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM</b>", cover_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Portfolio Summary & Executive Almanac</b><br/>All {len(df_all)} Constituents Profiled", cover_sub))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Publication Date: {datetime.datetime.now().strftime('%B %d, %Y')} | Version 1.0", cover_sub))
    story.append(Spacer(1, 40))
    story.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#1e3a8a"), spaceAfter=30))

    # High-level universe stats table
    med_roe = df_all["return_on_equity_pct"].median()
    med_roce = df_all["roce_pct"].median()
    med_npm = df_all["net_profit_margin_pct"].median()
    med_de = df_all["debt_to_equity"].median()
    med_pe = df_all["pe_ratio"].median()
    tot_fcf = df_all["free_cash_flow_cr"].sum()

    u_summary = [
        [Paragraph("<b>Universe Key Metric</b>", header_cell), Paragraph("<b>Nifty 100 Value</b>", header_cell)],
        [Paragraph("Total Tracked Companies", bold_cell), Paragraph(f"{len(df_all)} Constituents", body_style)],
        [Paragraph("Median Return on Equity (ROE)", bold_cell), Paragraph(f"{med_roe:.1f}%", body_style)],
        [Paragraph("Median ROCE", bold_cell), Paragraph(f"{med_roce:.1f}%", body_style)],
        [Paragraph("Median Net Profit Margin (NPM)", bold_cell), Paragraph(f"{med_npm:.1f}%", body_style)],
        [Paragraph("Median Debt to Equity", bold_cell), Paragraph(f"{med_de:.2f}x", body_style)],
        [Paragraph("Median P/E Ratio (SIMULATED)", bold_cell), Paragraph(f"{med_pe:.1f}x", body_style)],
        [Paragraph("Total Aggregate Free Cash Flow (Latest)", bold_cell), Paragraph(f"₹{tot_fcf:,.0f} Crore", body_style)],
    ]
    t_u = Table(u_summary, colWidths=[240, 240])
    t_u.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t_u)

    # ================= 1-PAGE PER COMPANY =================
    for idx, row in df_all.iterrows():
        story.append(PageBreak())
        cid = row["ticker"]
        cname = row.get("company_name", cid)
        sec = row.get("broad_sector", "General")
        subsec = row.get("sub_sector", "General")
        
        story.append(Paragraph(f"<b>{cname}</b> ({cid})", co_title))
        story.append(Paragraph(f"Sector: <b>{sec}</b> | Sub-Sector: <b>{subsec}</b> | Cap Category: <b>{row.get('market_cap_category', 'Large Cap')}</b>", meta_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a8a"), spaceAfter=8, spaceBefore=4))

        about_txt = str(row.get("about_company", "Description unavailable."))
        if len(about_txt) > 300:
            about_txt = about_txt[:300] + "..."
        story.append(Paragraph(f"<b>Business Overview:</b> {about_txt}", body_style))
        story.append(Spacer(1, 8))

        # KPI Summary Table
        def f(v, suf=""):
            return f"{v:.1f}{suf}" if (v is not None and pd.notna(v)) else "N/A"

        co_kpis = [
            [Paragraph("<b>Financial Metric</b>", bold_cell), Paragraph("<b>Value</b>", bold_cell), Paragraph("<b>Financial Metric</b>", bold_cell), Paragraph("<b>Value</b>", bold_cell)],
            [Paragraph("Return on Equity (ROE)", body_style), Paragraph(f(row.get("return_on_equity_pct"), "%"), bold_cell), Paragraph("Return on Capital (ROCE)", body_style), Paragraph(f(row.get("roce_pct"), "%"), bold_cell)],
            [Paragraph("Net Profit Margin", body_style), Paragraph(f(row.get("net_profit_margin_pct"), "%"), body_style), Paragraph("Operating Margin (OPM)", body_style), Paragraph(f(row.get("operating_profit_margin_pct"), "%"), body_style)],
            [Paragraph("Debt to Equity", body_style), Paragraph(f(row.get("debt_to_equity"), "x"), body_style), Paragraph("Interest Coverage", body_style), Paragraph(f(row.get("interest_coverage"), "x"), body_style)],
            [Paragraph("Free Cash Flow (FCF)", body_style), Paragraph(f"₹{row.get('free_cash_flow_cr', 0):,.0f} Cr" if pd.notna(row.get("free_cash_flow_cr")) else "N/A", body_style), Paragraph("CapEx Intensity", body_style), Paragraph(f(row.get("capex_intensity_pct"), "%"), body_style)],
            [Paragraph("5-Yr Revenue CAGR", body_style), Paragraph(f(row.get("revenue_cagr_5yr"), "%"), bold_cell), Paragraph("5-Yr PAT CAGR", body_style), Paragraph(f(row.get("pat_cagr_5yr"), "%"), bold_cell)],
            [Paragraph("P/E Ratio (SIMULATED)", body_style), Paragraph(f(row.get("pe_ratio"), "x"), body_style), Paragraph("P/B Ratio", body_style), Paragraph(f(row.get("pb_ratio"), "x"), body_style)],
            [Paragraph("Dividend Yield (SIMULATED)", body_style), Paragraph(f(row.get("dividend_yield_pct"), "%"), body_style), Paragraph("Dividend Payout", body_style), Paragraph(f(row.get("dividend_payout_ratio_pct"), "%"), body_style)],
            [Paragraph("Capital Allocation Class", bold_cell), Paragraph(str(row.get("capital_allocation_pattern", "N/A")), bold_cell), Paragraph("Composite Health Score", bold_cell), Paragraph(f"<b>{row.get('composite_quality_score', 0):.1f}/100</b>", bold_cell)],
        ]
        t_co = Table(co_kpis, colWidths=[140, 120, 140, 120])
        t_co.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e2e8f0")),
            ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0,0), (-1,-1), 3.5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3.5),
        ]))
        story.append(t_co)
        story.append(Spacer(1, 8))

        # Embed Radar Chart
        radar_path = os.path.join("reports/radar_charts", f"{cid}_radar.png")
        if os.path.exists(radar_path):
            story.append(Image(radar_path, width=4.0*inch, height=4.0*inch))

    doc.build(story)
    logger.info("Generated master portfolio summary PDF at %s (%d pages)", pdf_path, len(df_all) + 1)
    return pdf_path


def generate_all_reports(db_path: str = DB_PATH) -> None:
    """Master report generation runner for `make report`."""
    logger.info("Starting master PDF report generation...")
    # 1. Tearsheets (92)
    generate_all_tearsheets(db_path)
    # 2. Sector reports (11)
    generate_all_sector_reports(db_path)
    # 3. Portfolio summary
    build_portfolio_summary_pdf(db_path)
    logger.info("Completed all PDF reports generation successfully.")


if __name__ == "__main__":
    generate_all_reports()
