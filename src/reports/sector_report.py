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
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
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

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
SECTOR_DIR = "reports/sector"


def build_sector_report(broad_sector: str, db_path: str = DB_PATH, out_dir: str = SECTOR_DIR) -> str:
    """Generate a comprehensive sector intelligence report PDF."""
    os.makedirs(out_dir, exist_ok=True)
    clean_sec_name = broad_sector.replace(" ", "_").replace("/", "_")
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    pdf_path = os.path.join(out_dir, f"{clean_sec_name}_report_{date_str}.pdf")

    query = """
    WITH latest_years AS (
        SELECT company_id, MAX(year) AS max_year
        FROM financial_ratios
        GROUP BY company_id
    )
    SELECT 
        c.id AS ticker,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        r.*
    FROM latest_years ly
    JOIN financial_ratios r ON ly.company_id = r.company_id AND ly.max_year = r.year
    JOIN companies c ON r.company_id = c.id
    JOIN sectors s ON r.company_id = s.company_id
    WHERE s.broad_sector = ?
    ORDER BY r.return_on_equity_pct DESC
    """
    with sqlite3.connect(db_path) as conn:
        df_sec = pd.read_sql(query, conn, params=(broad_sector,))

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("SecTitleStyle", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1e3a8a"), spaceAfter=4)
    meta_style = ParagraphStyle("SecMetaStyle", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#4b5563"), spaceAfter=6)
    cell_style = ParagraphStyle("SecCell", parent=styles["Normal"], fontSize=7.5, leading=9)
    bold_cell = ParagraphStyle("SecBoldCell", parent=styles["Normal"], fontSize=7.5, leading=9, fontName="Helvetica-Bold")
    header_cell = ParagraphStyle("SecHeaderCell", parent=styles["Normal"], fontSize=7.5, leading=9, fontName="Helvetica-Bold", textColor=colors.white)

    story = []

    # Title
    story.append(Paragraph(f"<b>Sector Intelligence Report: {broad_sector}</b>", title_style))
    story.append(Paragraph(f"Nifty 100 Financial Intelligence Platform | Total Constituents: <b>{len(df_sec)}</b> | Date: {date_str}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

    # Sector Benchmark Summary
    story.append(Paragraph("<b>Sector Key Performance Indicators (Median Summary)</b>", styles["Heading3"]))
    med_roe = df_sec["return_on_equity_pct"].median()
    med_roce = df_sec["roce_pct"].median()
    med_npm = df_sec["net_profit_margin_pct"].median()
    med_de = df_sec["debt_to_equity"].median()
    med_pe = df_sec["pe_ratio"].median()
    med_score = df_sec["composite_quality_score"].median()

    summary_data = [
        [Paragraph("<b>Metric</b>", bold_cell), Paragraph("<b>Sector Median</b>", bold_cell), Paragraph("<b>Top Performer</b>", bold_cell), Paragraph("<b>Bottom Performer</b>", bold_cell)],
        [Paragraph("Return on Equity (ROE)", cell_style), Paragraph(f"{med_roe:.1f}%" if pd.notna(med_roe) else "N/A", cell_style), Paragraph(f"{df_sec.iloc[0]['ticker']} ({df_sec.iloc[0]['return_on_equity_pct']:.1f}%)", cell_style), Paragraph(f"{df_sec.iloc[-1]['ticker']} ({df_sec.iloc[-1]['return_on_equity_pct']:.1f}%)", cell_style)],
        [Paragraph("ROCE", cell_style), Paragraph(f"{med_roce:.1f}%" if pd.notna(med_roce) else "N/A", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)],
        [Paragraph("Net Profit Margin", cell_style), Paragraph(f"{med_npm:.1f}%" if pd.notna(med_npm) else "N/A", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)],
        [Paragraph("Debt to Equity", cell_style), Paragraph(f"{med_de:.2f}x" if pd.notna(med_de) else "N/A", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)],
        [Paragraph("P/E Ratio (SIMULATED)", cell_style), Paragraph(f"{med_pe:.1f}x" if pd.notna(med_pe) else "N/A", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)],
        [Paragraph("Composite Quality Score", cell_style), Paragraph(f"{med_score:.1f}/100" if pd.notna(med_score) else "N/A", cell_style), Paragraph("-", cell_style), Paragraph("-", cell_style)],
    ]
    t_sum = Table(summary_data, colWidths=[140, 110, 140, 140])
    t_sum.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 10))

    # All Companies Table
    story.append(Paragraph("<b>Constituent Companies Breakdown</b>", styles["Heading3"]))
    table_headers = ["Ticker", "Sub-Sector", "ROE %", "ROCE %", "NPM %", "D/E", "5Y Rev CAGR", "FCF (₹Cr)", "P/E", "Score"]
    table_rows = [
        [Paragraph(f"<b>{h}</b>", header_cell) for h in table_headers]
    ]

    for _, r in df_sec.iterrows():
        table_rows.append([
            Paragraph(f"<b>{r['ticker']}</b>", bold_cell),
            Paragraph(str(r.get("sub_sector", ""))[:18], cell_style),
            Paragraph(f"{r.get('return_on_equity_pct', 0):.1f}%" if pd.notna(r.get("return_on_equity_pct")) else "-", cell_style),
            Paragraph(f"{r.get('roce_pct', 0):.1f}%" if pd.notna(r.get("roce_pct")) else "-", cell_style),
            Paragraph(f"{r.get('net_profit_margin_pct', 0):.1f}%" if pd.notna(r.get("net_profit_margin_pct")) else "-", cell_style),
            Paragraph(f"{r.get('debt_to_equity', 0):.2f}" if pd.notna(r.get("debt_to_equity")) else "-", cell_style),
            Paragraph(f"{r.get('revenue_cagr_5yr', 0):.1f}%" if pd.notna(r.get("revenue_cagr_5yr")) else "-", cell_style),
            Paragraph(f"₹{r.get('free_cash_flow_cr', 0):,.0f}" if pd.notna(r.get("free_cash_flow_cr")) else "-", cell_style),
            Paragraph(f"{r.get('pe_ratio', 0):.1f}" if pd.notna(r.get("pe_ratio")) else "-", cell_style),
            Paragraph(f"<b>{r.get('composite_quality_score', 0):.1f}</b>" if pd.notna(r.get("composite_quality_score")) else "-", bold_cell),
        ])

    t_detail = Table(table_rows, colWidths=[65, 85, 45, 45, 45, 40, 60, 65, 40, 45])
    t_detail.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e3a8a")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_detail)

    doc.build(story)
    logger.info("Generated sector report for '%s' at %s", broad_sector, pdf_path)
    return pdf_path


def generate_all_sector_reports(db_path: str = DB_PATH) -> List[str]:
    """Generate reports for all 11 broad sectors."""
    with sqlite3.connect(db_path) as conn:
        sectors = pd.read_sql("SELECT DISTINCT broad_sector FROM sectors", conn)["broad_sector"].dropna().tolist()
    
    paths = []
    for s in sectors:
        p = build_sector_report(s, db_path)
        paths.append(p)
    logger.info("Generated %d sector reports in %s", len(paths), SECTOR_DIR)
    return paths


if __name__ == "__main__":
    generate_all_sector_reports()
