import datetime
import logging
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Tuple
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

load_dotenv()
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
REPORTS_DIR = "reports/tearsheets"
TEMP_CHART_DIR = "reports/temp_charts"


def generate_company_charts(
    company_id: str,
    df_pl: pd.DataFrame,
    df_r: pd.DataFrame,
    temp_dir: str = TEMP_CHART_DIR
) -> Tuple[Optional[str], Optional[str]]:
    """Generate static financial trend charts for PDF embedding."""
    os.makedirs(temp_dir, exist_ok=True)
    if df_pl.empty or df_r.empty:
        return None, None

    # Chart 1: 10-yr Sales & Net Profit Bar/Line
    plt.figure(figsize=(6.5, 2.2))
    years = [y.split("-")[0] for y in df_pl["year"]]
    sales = df_pl["sales"] / 1000.0  # In ₹ '000 Cr
    net_profit = df_pl["net_profit"] / 1000.0

    ax1 = plt.gca()
    bars = ax1.bar(years, sales, color="#2b5c8f", alpha=0.85, width=0.55, label="Sales (₹'000 Cr)")
    ax1.set_ylabel("Sales (₹'000 Cr)", color="#2b5c8f", fontsize=8)
    ax1.tick_params(axis="y", labelcolor="#2b5c8f", labelsize=7)
    ax1.tick_params(axis="x", labelsize=7, rotation=35)

    ax2 = ax1.twinx()
    ax2.plot(years, net_profit, color="#d9534f", marker="o", linewidth=1.5, markersize=3, label="Net Profit (₹'000 Cr)")
    ax2.set_ylabel("PAT (₹'000 Cr)", color="#d9534f", fontsize=8)
    ax2.tick_params(axis="y", labelcolor="#d9534f", labelsize=7)

    plt.title("Historical Revenue & Net Profit Trend (10-Yr)", fontsize=9, fontweight="bold", pad=6)
    plt.tight_layout()
    chart1_path = os.path.join(temp_dir, f"{company_id}_pl_trend.png")
    plt.savefig(chart1_path, dpi=130)
    plt.close()

    # Chart 2: ROE & ROCE Return Trends
    plt.figure(figsize=(6.5, 2.0))
    r_years = [y.split("-")[0] for y in df_r["year"]]
    roe = df_r["return_on_equity_pct"]
    roce = df_r["roce_pct"]

    plt.plot(r_years, roe, color="#1b9e77", marker="s", linewidth=1.8, markersize=3.5, label="ROE %")
    plt.plot(r_years, roce, color="#7570b3", marker="^", linewidth=1.8, markersize=3.5, label="ROCE %")
    plt.axhline(15.0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7, label="15% Benchmark")
    plt.ylabel("Return %", fontsize=8)
    plt.yticks(fontsize=7)
    plt.xticks(fontsize=7, rotation=35)
    plt.title("Return on Equity (ROE) & Return on Capital (ROCE) Trend", fontsize=9, fontweight="bold", pad=6)
    plt.legend(loc="upper left", fontsize=7)
    plt.tight_layout()
    chart2_path = os.path.join(temp_dir, f"{company_id}_return_trend.png")
    plt.savefig(chart2_path, dpi=130)
    plt.close()

    return chart1_path, chart2_path


def build_tearsheet_pdf(company_id: str, db_path: str = DB_PATH, out_dir: str = REPORTS_DIR) -> str:
    """Generate a high-density 2-page executive tearsheet PDF for a specific company."""
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, f"{company_id}_tearsheet.pdf")

    with sqlite3.connect(db_path) as conn:
        co_row = pd.read_sql("SELECT * FROM companies WHERE id = ?", conn, params=(company_id,)).iloc[0].to_dict()
        sec_df = pd.read_sql("SELECT * FROM sectors WHERE company_id = ?", conn, params=(company_id,))
        sec_row = sec_df.iloc[0].to_dict() if not sec_df.empty else {}
        df_pl = pd.read_sql("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=(company_id,))
        df_bs = pd.read_sql("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=(company_id,))
        df_cf = pd.read_sql("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=(company_id,))
        df_r = pd.read_sql("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", conn, params=(company_id,))

    # Load pros and cons
    pros_cons_file = "output/pros_cons_generated.csv"
    pros_list, cons_list = [], []
    if os.path.exists(pros_cons_file):
        df_pc = pd.read_csv(pros_cons_file)
        df_pc_co = df_pc[df_pc["company_id"] == company_id]
        pros_list = df_pc_co[df_pc_co["type"] == "pro"]["text"].tolist()[:3]
        cons_list = df_pc_co[df_pc_co["type"] == "con"]["text"].tolist()[:3]

    latest_r = df_r.iloc[-1].to_dict() if not df_r.empty else {}
    latest_pl = df_pl.iloc[-1].to_dict() if not df_pl.empty else {}
    latest_bs = df_bs.iloc[-1].to_dict() if not df_bs.empty else {}
    latest_cf = df_cf.iloc[-1].to_dict() if not df_cf.empty else {}

    # Generate charts
    chart1_path, chart2_path = generate_company_charts(company_id, df_pl, df_r)
    radar_path = os.path.join("reports/radar_charts", f"{company_id}_radar.png")

    # Document setup: 2 pages
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=16, leading=18, textColor=colors.HexColor("#1e3a8a"), spaceAfter=2)
    meta_style = ParagraphStyle("MetaStyle", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#4b5563"))
    section_title = ParagraphStyle("SecTitle", parent=styles["Heading2"], fontSize=10, leading=12, textColor=colors.HexColor("#1e3a8a"), spaceBefore=6, spaceAfter=4)
    cell_style = ParagraphStyle("CellText", parent=styles["Normal"], fontSize=7.5, leading=9)
    bold_cell = ParagraphStyle("BoldCell", parent=styles["Normal"], fontSize=7.5, leading=9, fontName="Helvetica-Bold")
    kpi_val_style = ParagraphStyle("KPIVal", parent=styles["Normal"], fontSize=12, leading=14, fontName="Helvetica-Bold", alignment=TA_CENTER, textColor=colors.HexColor("#1e3a8a"))
    kpi_lbl_style = ParagraphStyle("KPILbl", parent=styles["Normal"], fontSize=6.5, leading=8, alignment=TA_CENTER, textColor=colors.HexColor("#4b5563"))

    story = []

    # ================= PAGE 1 =================
    # Header
    co_name = co_row.get("company_name", company_id)
    sector_info = f"Sector: <b>{sec_row.get('broad_sector', 'N/A')}</b> | Sub-Sector: <b>{sec_row.get('sub_sector', 'N/A')}</b> | Cap: <b>{sec_row.get('market_cap_category', 'Large Cap')}</b>"
    story.append(Paragraph(f"<b>{co_name}</b> ({company_id})", title_style))
    story.append(Paragraph(sector_info, meta_style))
    story.append(Paragraph(f"Nifty 100 Financial Intelligence Tearsheet | Reporting Date: {latest_r.get('year', '2024-03')}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=6, spaceBefore=4))

    # KPI 6-Tile Header Block
    def fmt(v, suffix=""):
        return f"{v:.1f}{suffix}" if (v is not None and pd.notna(v)) else "N/A"

    kpi_tiles_data = [
        [
            Paragraph(fmt(latest_r.get("return_on_equity_pct"), "%"), kpi_val_style),
            Paragraph(fmt(latest_r.get("roce_pct"), "%"), kpi_val_style),
            Paragraph(fmt(latest_r.get("net_profit_margin_pct"), "%"), kpi_val_style),
            Paragraph(fmt(latest_r.get("debt_to_equity"), "x"), kpi_val_style),
            Paragraph(f"₹{latest_r.get('free_cash_flow_cr', 0):,.0f} Cr" if pd.notna(latest_r.get("free_cash_flow_cr")) else "N/A", kpi_val_style),
            Paragraph(fmt(latest_r.get("revenue_cagr_5yr"), "%"), kpi_val_style),
        ],
        [
            Paragraph("ROE (Latest)", kpi_lbl_style),
            Paragraph("ROCE (Latest)", kpi_lbl_style),
            Paragraph("Net Margin (NPM)", kpi_lbl_style),
            Paragraph("Debt / Equity", kpi_lbl_style),
            Paragraph("Free Cash Flow", kpi_lbl_style),
            Paragraph("5-Yr Rev CAGR", kpi_lbl_style),
        ]
    ]
    t_kpis = Table(kpi_tiles_data, colWidths=[90]*6)
    t_kpis.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_kpis)
    story.append(Spacer(1, 6))

    # Financial Performance History (Table)
    story.append(Paragraph("<b>Key Financial History (₹ Crore)</b>", section_title))
    hist_cols = ["Metric"] + [y.split("-")[0] for y in df_pl["year"].tail(6)]
    table_hist_data = [
        [Paragraph(f"<b>{c}</b>", bold_cell) for c in hist_cols]
    ]

    metrics_map = [
        ("Sales", "sales", df_pl),
        ("Operating Profit", "operating_profit", df_pl),
        ("OPM %", "opm_percentage", df_pl),
        ("Net Profit (PAT)", "net_profit", df_pl),
        ("EPS (₹)", "eps", df_pl),
    ]

    for label, col_name, src_df in metrics_map:
        row_vals = [Paragraph(f"<b>{label}</b>", bold_cell)]
        sub_df = src_df.tail(6)
        for _, r in sub_df.iterrows():
            v = r.get(col_name)
            val_str = f"{v:,.0f}" if (v is not None and pd.notna(v) and col_name != "opm_percentage" and col_name != "eps") else f"{v:.1f}" if pd.notna(v) else "-"
            row_vals.append(Paragraph(val_str, cell_style))
        table_hist_data.append(row_vals)

    col_w = [120] + [70] * (len(hist_cols) - 1)
    t_hist = Table(table_hist_data, colWidths=col_w)
    t_hist.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0,0), (-1,-1), 2.5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_hist)
    story.append(Spacer(1, 6))

    # Embed Charts
    if chart1_path and os.path.exists(chart1_path):
        story.append(Image(chart1_path, width=7.2*inch, height=2.2*inch))
    if chart2_path and os.path.exists(chart2_path):
        story.append(Image(chart2_path, width=7.2*inch, height=1.9*inch))

    # ================= PAGE 2 =================
    story.append(PageBreak())
    story.append(Paragraph(f"<b>{co_name}</b> — Balance Sheet, Cash Flow & Qualitative Intelligence", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=6, spaceBefore=4))

    def safe_money(v: Any) -> str:
        if v is None or pd.isna(v):
            return "-"
        try:
            return f"₹{float(v):,.0f}"
        except (ValueError, TypeError):
            return "-"

    # Balance Sheet & Cash Flow Summary Split Table
    story.append(Paragraph("<b>Balance Sheet & Cash Flow Structure (Latest ₹ Cr)</b>", section_title))
    fa_cwip = (float(latest_bs.get('fixed_assets') or 0)) + (float(latest_bs.get('cwip') or 0))
    bs_cf_data = [
        [Paragraph("<b>Balance Sheet Metric</b>", bold_cell), Paragraph("<b>Value (₹ Cr)</b>", bold_cell), Paragraph("<b>Cash Flow Metric</b>", bold_cell), Paragraph("<b>Value (₹ Cr)</b>", bold_cell)],
        [Paragraph("Equity Capital", cell_style), Paragraph(safe_money(latest_bs.get('equity_capital')), cell_style), Paragraph("Cash from Operations (CFO)", cell_style), Paragraph(safe_money(latest_cf.get('operating_activity')), cell_style)],
        [Paragraph("Reserves & Surplus", cell_style), Paragraph(safe_money(latest_bs.get('reserves')), cell_style), Paragraph("Investing Cash Flow (CFI / CapEx)", cell_style), Paragraph(safe_money(latest_cf.get('investing_activity')), cell_style)],
        [Paragraph("Total Borrowings (Debt)", cell_style), Paragraph(safe_money(latest_bs.get('borrowings')), cell_style), Paragraph("Financing Cash Flow (CFF)", cell_style), Paragraph(safe_money(latest_cf.get('financing_activity')), cell_style)],
        [Paragraph("Fixed Assets & CWIP", cell_style), Paragraph(safe_money(fa_cwip), cell_style), Paragraph("Net Free Cash Flow (FCF)", cell_style), Paragraph(safe_money(latest_r.get('free_cash_flow_cr')), cell_style)],
        [Paragraph("Total Assets", cell_style), Paragraph(safe_money(latest_bs.get('total_assets')), cell_style), Paragraph("Capital Allocation Pattern", cell_style), Paragraph(f"<b>{latest_r.get('capital_allocation_pattern', 'N/A')}</b>", bold_cell)],
    ]

    t_bscf = Table(bs_cf_data, colWidths=[150, 120, 150, 120])
    t_bscf.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_bscf)
    story.append(Spacer(1, 8))

    # Radar Chart & Qualitative Pros/Cons Split
    radar_col = []
    if os.path.exists(radar_path):
        radar_col.append(Image(radar_path, width=3.3*inch, height=3.3*inch))
    else:
        radar_col.append(Paragraph("Radar chart not available", cell_style))

    qual_col = [
        Paragraph("<b>Investment Strengths (Pros)</b>", ParagraphStyle("ProTitle", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#166534"), fontName="Helvetica-Bold")),
    ]
    for p in pros_list:
        qual_col.append(Paragraph(f"• {p}", ParagraphStyle("ProTxt", parent=cell_style, textColor=colors.HexColor("#15803d"))))
    qual_col.append(Spacer(1, 6))

    qual_col.append(Paragraph("<b>Risks & Considerations (Cons)</b>", ParagraphStyle("ConTitle", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#991b1b"), fontName="Helvetica-Bold")))
    for c in cons_list:
        qual_col.append(Paragraph(f"• {c}", ParagraphStyle("ConTxt", parent=cell_style, textColor=colors.HexColor("#b91c1c"))))
    
    qual_col.append(Spacer(1, 6))
    score_val = latest_r.get('composite_quality_score', 'N/A')
    qual_col.append(Paragraph(f"<b>Composite Quality Score: {score_val} / 100</b>", ParagraphStyle("ScoreBadge", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e3a8a"))))
    qual_col.append(Paragraph("<i>Note: Stock prices and valuation multiples are SIMULATED datasets for analytical framework.</i>", ParagraphStyle("SimNote", parent=styles["Normal"], fontSize=6.5, textColor=colors.HexColor("#6b7280"))))

    split_table = Table([[radar_col, qual_col]], colWidths=[240, 300])
    split_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(split_table)

    # Build PDF
    doc.build(story)
    return pdf_path


def generate_all_tearsheets(db_path: str = DB_PATH) -> int:
    """Generate all 92 company tearsheet PDFs."""
    with sqlite3.connect(db_path) as conn:
        companies = pd.read_sql("SELECT id FROM companies", conn)["id"].tolist()
    
    count = 0
    for cid in companies:
        build_tearsheet_pdf(cid, db_path)
        count += 1
    logger.info("Generated %d company tearsheets in %s", count, REPORTS_DIR)
    return count


if __name__ == "__main__":
    generate_all_tearsheets()
