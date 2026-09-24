"""PDF Document Generator for DataScope Executive Business Intelligence Reports.

Produces polished, boardroom-ready PDF documents using ReportLab with:
- Exactly 8 full, dense analytical pages for standard business datasets
- Executive business KPI matrix and written narrative briefing
- Operational Performance Indicators with 5-question metric evaluations
- 6-Point Structured Sales & Commercial Analysis Framework
- Comprehensive Profit & Loss Margin & Loss-Making Breakdown
- Customer Segment & Regional Distribution analysis
- Discount & Pricing Governance Rules & Margin Guardrails
- Inventory & Supply Chain Health with honest fallbacks
- Root Cause Analysis & 5-Step Strategic Action Roadmaps
- Business Risk & Anomaly Register with impact analysis
- Market Competition Analysis with required field requirements
- Trends Intelligence & Horizon Forecast Projections
- Priority Corrective Action Plan Table (Boardroom Matrix)
- Final Management Summary & Strategic Decision Boundaries
- Technical Data Validation & Methodology Appendix
- Safe font encoding sanitization (Rupee to Rs.) ensuring zero encoding crashes
- Running header/footers with dynamic page numbering (NumberedCanvas)
"""
from __future__ import annotations

import io
from typing import Any, List, Optional, Tuple

from reportlab.graphics.shapes import Drawing, Group, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.report import ComprehensiveReportResponse


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages in a two-pass approach and draws running header/footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Top Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "DataScope Business Intelligence & Decision Support Dossier")
            self.drawRightString(612 - 54, 750, "Confidential Executive Report")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Running Bottom Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 36, page_str)
        self.drawString(54, 36, "DataScope Universal Decision Intelligence Platform · Boardroom Analytics")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 612 - 54, 48)

        self.restoreState()


def _safe_text(val: Any) -> str:
    """Sanitize text to avoid ReportLab Helvetica encoding crashes."""
    if val is None:
        return ""
    text = str(val)
    text = text.replace("\u20b9", "Rs. ")
    text = text.replace("–", "-").replace("—", "-")
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    return text


def _create_bar_chart_flowable(items: List[Tuple[str, float, str]], title: str = "Top Segments by Revenue Contribution") -> Drawing:
    """Create a standalone clean vector horizontal bar chart for top performers."""
    d = Drawing(504, 110)
    d.add(Rect(0, 0, 504, 110, fillColor=colors.HexColor("#F8FAFC"), strokeColor=colors.HexColor("#E2E8F0"), strokeWidth=0.5, rx=4, ry=4))
    d.add(String(12, 94, title, fontName="Helvetica-Bold", fontSize=9, fillColor=colors.HexColor("#0F172A")))
    
    if not items:
        d.add(String(12, 50, "No visual comparison data available.", fontName="Helvetica-Oblique", fontSize=8, fillColor=colors.HexColor("#64748B")))
        return d

    max_val = max((val for _, val, _ in items), default=1.0) or 1.0
    bar_y = 70
    bar_height = 12
    max_bar_width = 280

    for idx, (label, val, formatted) in enumerate(items[:4]):
        # Label
        short_label = label[:24] + ("..." if len(label) > 24 else "")
        d.add(String(12, bar_y + 2, short_label, fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#334155")))
        
        # Background bar
        d.add(Rect(140, bar_y, max_bar_width, bar_height, fillColor=colors.HexColor("#E2E8F0"), strokeColor=None, rx=2, ry=2))
        
        # Value bar
        w = max(4, int((val / max_val) * max_bar_width))
        bar_color = colors.HexColor("#2563EB") if idx == 0 else (colors.HexColor("#3B82F6") if idx == 1 else colors.HexColor("#60A5FA"))
        d.add(Rect(140, bar_y, w, bar_height, fillColor=bar_color, strokeColor=None, rx=2, ry=2))
        
        # Value string
        d.add(String(145 + max_bar_width, bar_y + 2, formatted, fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor("#0F172A")))
        bar_y -= 18

    return d


def generate_pdf_report(
    report: ComprehensiveReportResponse,
    selected_sections: Optional[List[str]] = None,
) -> io.BytesIO:
    """Generate and return a binary stream of the PDF report (8 full pages)."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    style_super_title = ParagraphStyle(
        "ReportSuperTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=2,
    )

    style_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    style_sub_meta = ParagraphStyle(
        "ReportSubMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
        spaceAfter=8,
    )

    style_h1 = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=4,
    )

    style_h2 = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=6,
        spaceAfter=3,
    )

    style_body = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4,
    )

    style_body_bold = ParagraphStyle(
        "ReportBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )

    style_bullet = ParagraphStyle(
        "ReportBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
        leftIndent=10,
        spaceAfter=2,
    )

    style_th = ParagraphStyle(
        "ReportTH",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
    )

    style_td = ParagraphStyle(
        "ReportTD",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
    )

    story: List[Any] = []
    meta = report.metadata
    exec_sum = report.executive_summary

    # ====================================================
    # PAGE 1: EXECUTIVE BRIEFING & CORE HEALTH MATRIX
    # ====================================================
    story.append(Paragraph("DATASCOPE BUSINESS INTELLIGENCE & DECISION SUPPORT", style_super_title))
    story.append(Paragraph(_safe_text(f"Executive Business Performance Dossier: {meta.dataset_name}"), style_title))
    story.append(
        Paragraph(
            _safe_text(
                f"Domain: {meta.domain_name}   |   Reporting Period: {meta.reporting_period}   |   Business Condition: {exec_sum.overall_business_condition}   |   Generated: {meta.generated_at}"
            ),
            style_sub_meta,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

    story.append(Paragraph("1. Executive Business Summary & Performance Matrix", style_h1))

    # 2x4 KPI Matrix
    kpi_cards = [
        ("Total Revenue", _safe_text(exec_sum.total_sales_revenue or "N/A")),
        ("Net Profit", _safe_text(exec_sum.total_profit_loss or "N/A")),
        ("Profit Margin", _safe_text(exec_sum.profit_margin_pct or "N/A")),
        ("Total Orders", _safe_text(exec_sum.total_orders_count or "N/A")),
        ("Avg Order Value", _safe_text(exec_sum.average_order_value or "N/A")),
        ("Units Sold", _safe_text(exec_sum.total_units_sold or "N/A")),
        ("Avg Discount", _safe_text(exec_sum.average_discount_pct or "N/A")),
        ("Business Health", _safe_text(exec_sum.overall_business_health)),
    ]

    kpi_data = []
    for r_idx in range(2):
        row_cells = []
        for c_idx in range(4):
            idx = r_idx * 4 + c_idx
            lbl, val = kpi_cards[idx]
            cell_p = Paragraph(
                f"<font size=6.5 color='#64748B'><b>{lbl}</b></font><br/><font size=10 color='#0F172A'><b>{val}</b></font>",
                ParagraphStyle("KPICell", parent=styles["Normal"], alignment=1, leading=11),
            )
            row_cells.append(cell_p)
        kpi_data.append(row_cells)

    kpi_tbl = Table(kpi_data, colWidths=[126, 126, 126, 126])
    kpi_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(kpi_tbl)
    story.append(Spacer(1, 6))

    # Executive Briefing Callout Box
    summary_box_data = [
        [
            Paragraph(
                f"<font color='#1E40AF'><b>Executive Business Briefing & Commercial Context:</b></font><br/>"
                f"{_safe_text(exec_sum.overall_performance_summary)}",
                style_body,
            )
        ]
    ]
    sum_box_tbl = Table(summary_box_data, colWidths=[504])
    sum_box_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(sum_box_tbl)
    story.append(Spacer(1, 6))

    # Major Observations
    if exec_sum.major_positive_findings or exec_sum.major_negative_findings:
        story.append(Paragraph("<b>Core Commercial Observations:</b>", style_h2))
        for pos in exec_sum.major_positive_findings:
            story.append(Paragraph(f"<font color='#059669'>• [POSITIVE MOMENTUM]</font> {_safe_text(pos)}", style_bullet))
        for neg in exec_sum.major_negative_findings:
            story.append(Paragraph(f"<font color='#DC2626'>• [ATTENTION REQUIRED]</font> {_safe_text(neg)}", style_bullet))

    # Top Risks & Management Priorities
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Top Priority Business Risks:</b>", style_h2))
    for rsk in exec_sum.most_important_risks[:3]:
        story.append(Paragraph(f"<font color='#991B1B'>• [CRITICAL RISK]</font> {_safe_text(rsk)}", style_bullet))

    story.append(Paragraph("<b>Top Executive Management Actions:</b>", style_h2))
    for act in exec_sum.priority_corrective_actions[:5]:
        story.append(Paragraph(f"• <b>Action:</b> {_safe_text(act)}", style_bullet))

    # END OF PAGE 1
    story.append(PageBreak())

    # ====================================================
    # PAGE 2: BUSINESS PERFORMANCE OVERVIEW & COMMERCIAL DIMENSIONS
    # ====================================================
    story.append(Paragraph("2. Business Performance Overview & Operational Metrics", style_h1))
    bp_rep = report.business_performance

    if not bp_rep.is_available:
        story.append(Paragraph(f"<i>{_safe_text(bp_rep.unavailable_reason or 'Business performance metrics unavailable.')}</i>", style_body))
    else:
        story.append(Paragraph(_safe_text(bp_rep.summary_text), style_body))

        # Operational Performance Indicators Table (5 Questions)
        if bp_rep.metric_highlights:
            story.append(Paragraph("Key Operational Performance Indicators", style_h2))
            kpi_th_data = [[
                Paragraph("Metric Name", style_th),
                Paragraph("Observed Value", style_th),
                Paragraph("Business Meaning & Interpretation", style_th),
                Paragraph("Status / Signal", style_th),
            ]]
            for m in bp_rep.metric_highlights[:6]:
                status_str = "<font color='#DC2626'><b>Action Needed</b></font>" if m.requires_attention else "<font color='#059669'>Healthy</font>"
                kpi_th_data.append([
                    Paragraph(_safe_text(m.name), style_td),
                    Paragraph(_safe_text(m.formatted_value), style_td),
                    Paragraph(_safe_text(m.business_meaning), style_td),
                    Paragraph(status_str, style_td),
                ])
            k_tbl = Table(kpi_th_data, colWidths=[100, 75, 239, 90])
            k_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(k_tbl)
            story.append(Spacer(1, 6))

        # Top Performers Table
        if bp_rep.top_performers:
            story.append(Paragraph("Top Commercial Performers (Revenue Contribution)", style_h2))
            perf_th_data = [[
                Paragraph("Segment Name", style_th),
                Paragraph("Dimension", style_th),
                Paragraph("Revenue", style_th),
                Paragraph("Share %", style_th),
                Paragraph("Commercial Note", style_th),
            ]]
            chart_items = []
            for p in bp_rep.top_performers[:5]:
                share_txt = f"{p.percentage_share:.1f}%" if p.percentage_share else "N/A"
                perf_th_data.append([
                    Paragraph(_safe_text(p.name), style_td),
                    Paragraph(_safe_text(p.entity_type), style_td),
                    Paragraph(_safe_text(p.formatted_value), style_td),
                    Paragraph(share_txt, style_td),
                    Paragraph(_safe_text(p.note or "Primary commercial driver."), style_td),
                ])
                chart_items.append((p.name, p.raw_value or 0.0, p.formatted_value))

            p_tbl = Table(perf_th_data, colWidths=[110, 75, 75, 54, 190])
            p_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(p_tbl)
            story.append(Spacer(1, 6))

            # Visual Bar Chart Drawing
            chart_flowable = _create_bar_chart_flowable(chart_items, title="Revenue Contribution by Key Segments")
            story.append(chart_flowable)

    # END OF PAGE 2
    story.append(PageBreak())

    # ====================================================
    # PAGE 3: 6-POINT IN-DEPTH REVENUE & SALES ANALYSIS
    # ====================================================
    story.append(Paragraph("3. Revenue & Sales In-Depth Analysis", style_h1))
    story.append(
        Paragraph(
            "This section evaluates commercial volume, revenue concentration, and sales velocity using DataScope's 6-Point Analytical Framework. Each finding connects observed evidence to strategic leadership actions.",
            style_body,
        )
    )

    if bp_rep.six_point_findings:
        for f_idx, f in enumerate(bp_rep.six_point_findings[:3]):
            story.append(Paragraph(f"<b>Observation {f_idx + 1}: {_safe_text(f.observation_title)}</b>", style_h2))
            
            box_content = [
                [Paragraph(f"<b>1. What was observed:</b> {_safe_text(f.what_happened)}", style_body)],
                [Paragraph(f"<b>2. Business meaning:</b> {_safe_text(f.business_meaning)}", style_body)],
                [Paragraph(f"<b>3. Why it matters:</b> {_safe_text(f.why_it_matters)}", style_body)],
                [Paragraph(f"<b>4. Recommended action:</b> {_safe_text(f.recommended_action)}", style_body)],
                [Paragraph(f"<b>5. Verified data evidence:</b> {_safe_text(f.evidence)}", style_body)],
                [Paragraph(f"<b>6. Limitations & assumptions:</b> {_safe_text(f.limitations)}", style_body)],
            ]
            f_tbl = Table(box_content, colWidths=[504])
            f_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(f_tbl)
            story.append(Spacer(1, 6))

    # END OF PAGE 3
    story.append(PageBreak())

    # ====================================================
    # PAGE 4: PROFIT & LOSS ANALYSIS & MARGIN EROSION
    # ====================================================
    story.append(Paragraph("4. Profit & Loss Analysis & Margin Trajectory", style_h1))
    pl_rep = report.profit_loss

    if not pl_rep.is_available:
        story.append(Paragraph(f"<i>{_safe_text(pl_rep.unavailable_reason or 'Profit & Loss analysis is unavailable.')}</i>", style_body))
    else:
        # P&L Overview Callout
        pl_callout = [
            [
                Paragraph(
                    f"<b>Commercial P&L Summary:</b><br/>"
                    f"• <b>Revenue Trajectory:</b> {_safe_text(pl_rep.revenue_trend_summary)}<br/>"
                    f"• <b>Net Profit Status:</b> {_safe_text(pl_rep.profit_trend_summary)}<br/>"
                    f"• <b>Profit Margin Evaluation:</b> {_safe_text(pl_rep.profit_margin_summary)}",
                    style_body,
                )
            ]
        ]
        pl_tbl = Table(pl_callout, colWidths=[504])
        pl_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBF7D0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(pl_tbl)
        story.append(Spacer(1, 6))

        # Loss-Making Segments Table
        if pl_rep.loss_making_segments:
            story.append(Paragraph("Loss-Making Segments (Direct Margin Leakage)", style_h2))
            l_data = [[
                Paragraph("Segment Name", style_th),
                Paragraph("Revenue", style_th),
                Paragraph("Loss Amount", style_th),
                Paragraph("Margin %", style_th),
                Paragraph("Actionable Response", style_th),
            ]]
            for ls in pl_rep.loss_making_segments[:5]:
                l_data.append([
                    Paragraph(_safe_text(ls.name), style_td),
                    Paragraph(_safe_text(ls.revenue_formatted), style_td),
                    Paragraph(_safe_text(ls.profit_loss_formatted), style_td),
                    Paragraph(f"{ls.profit_margin_pct:.1f}%", style_td),
                    Paragraph(_safe_text(ls.actionable_response or "Review pricing and vendor cost structure."), style_td),
                ])
            l_tbl = Table(l_data, colWidths=[110, 75, 75, 54, 190])
            l_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#991B1B")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FEE2E2")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(l_tbl)
            story.append(Spacer(1, 6))

        # High Sales Low Profit Segments Table
        if pl_rep.high_sales_low_profit_segments:
            story.append(Paragraph("High-Volume Low-Margin Products (<10% Margin)", style_h2))
            t_data = [[
                Paragraph("Segment Name", style_th),
                Paragraph("Revenue", style_th),
                Paragraph("Profit", style_th),
                Paragraph("Margin %", style_th),
                Paragraph("Operational Observation", style_th),
            ]]
            for ts in pl_rep.high_sales_low_profit_segments[:4]:
                t_data.append([
                    Paragraph(_safe_text(ts.name), style_td),
                    Paragraph(_safe_text(ts.revenue_formatted), style_td),
                    Paragraph(_safe_text(ts.profit_loss_formatted), style_td),
                    Paragraph(f"{ts.profit_margin_pct:.1f}%", style_td),
                    Paragraph(_safe_text(ts.explanation), style_td),
                ])
            t_tbl = Table(t_data, colWidths=[110, 75, 75, 54, 190])
            t_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D97706")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFFBEB")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FDE68A")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FEF3C7")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(t_tbl)
            story.append(Spacer(1, 6))

        # Discount Margin Observations
        if pl_rep.discount_margin_observations:
            story.append(Paragraph("Discount-Related Margin Erosion Analysis", style_h2))
            for obs in pl_rep.discount_margin_observations:
                story.append(Paragraph(f"• {_safe_text(obs)}", style_bullet))

    # END OF PAGE 4
    story.append(PageBreak())

    # ====================================================
    # PAGE 5: CUSTOMER BEHAVIOR & REGIONAL / CHANNEL DISTRIBUTION
    # ====================================================
    story.append(Paragraph("5. Customer Segment & Sales Behavior", style_h1))
    cust_rep = report.customer_segment_analysis

    if not cust_rep or not cust_rep.is_available:
        story.append(Paragraph(f"<i>{_safe_text(cust_rep.unavailable_reason if cust_rep else 'Customer segment analysis unavailable.')}</i>", style_body))
    else:
        story.append(Paragraph(_safe_text(cust_rep.strategic_summary), style_body))

        if cust_rep.segments:
            c_data = [[
                Paragraph("Customer Segment", style_th),
                Paragraph("Revenue", style_th),
                Paragraph("Share %", style_th),
                Paragraph("AOV", style_th),
                Paragraph("Marketing / Retention Strategy", style_th),
            ]]
            for s in cust_rep.segments:
                c_data.append([
                    Paragraph(_safe_text(s.segment_name), style_td),
                    Paragraph(_safe_text(s.revenue_formatted), style_td),
                    Paragraph(f"{s.revenue_share_pct:.1f}%", style_td),
                    Paragraph(_safe_text(s.aov_formatted), style_td),
                    Paragraph(_safe_text(s.marketing_strategy), style_td),
                ])
            c_tbl = Table(c_data, colWidths=[100, 75, 54, 75, 200])
            c_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(c_tbl)
            story.append(Spacer(1, 6))

    # Regional & Channel Distribution
    story.append(Paragraph("6. Regional & Distribution Channel Analysis", style_h1))
    rc_rep = report.regional_channel_analysis

    if not rc_rep or not rc_rep.is_available:
        story.append(Paragraph(f"<i>{_safe_text(rc_rep.unavailable_reason if rc_rep else 'Regional distribution analysis unavailable.')}</i>", style_body))
    else:
        story.append(Paragraph(_safe_text(rc_rep.operational_takeaway), style_body))

        if rc_rep.items:
            rc_data = [[
                Paragraph(f"{rc_rep.dimension_name or 'Distribution Hub'}", style_th),
                Paragraph("Revenue", style_th),
                Paragraph("Share %", style_th),
                Paragraph("Order Volume", style_th),
                Paragraph("Operational Logistics Observation", style_th),
            ]]
            for r in rc_rep.items:
                rc_data.append([
                    Paragraph(_safe_text(r.name), style_td),
                    Paragraph(_safe_text(r.revenue_formatted), style_td),
                    Paragraph(f"{r.revenue_share_pct:.1f}%", style_td),
                    Paragraph(f"{r.order_volume:,}", style_td),
                    Paragraph(_safe_text(r.operational_observation), style_td),
                ])
            rc_tbl = Table(rc_data, colWidths=[100, 75, 54, 75, 200])
            rc_tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(rc_tbl)

    # END OF PAGE 5
    story.append(PageBreak())

    # ====================================================
    # PAGE 6: DISCOUNT & PRICING CONTROLS, INVENTORY & ROOT CAUSE ANALYSIS
    # ====================================================
    story.append(Paragraph("7. Discount & Pricing Dynamics", style_h1))
    dp_rep = report.discount_pricing

    if not dp_rep or not dp_rep.is_available:
        story.append(Paragraph(f"<i>{_safe_text(dp_rep.unavailable_reason if dp_rep else 'Discount analysis unavailable.')}</i>", style_body))
    else:
        if dp_rep.margin_erosion_estimate:
            story.append(Paragraph(f"<b>Margin Erosion Exposure:</b> {_safe_text(dp_rep.margin_erosion_estimate)}", style_body_bold))
        for obs in dp_rep.discount_tier_observations:
            story.append(Paragraph(f"• {_safe_text(obs)}", style_bullet))
        if dp_rep.suggested_controls:
            story.append(Paragraph("<b>Suggested Discount Governance Rules:</b>", style_h2))
            for ctrl in dp_rep.suggested_controls:
                story.append(Paragraph(f"• {_safe_text(ctrl)}", style_bullet))

    story.append(Spacer(1, 4))
    story.append(Paragraph("8. Inventory & Supply Chain Health", style_h1))
    inv_rep = report.inventory_analysis

    if not inv_rep or not inv_rep.is_available:
        story.append(
            Paragraph(
                "<i>Inventory levels were not available in the uploaded data. Therefore, stock-out risk, excess inventory, and reorder recommendations cannot be reliably calculated.</i>",
                style_body,
            )
        )
    else:
        story.append(Paragraph(_safe_text(inv_rep.inventory_turnover_observation), style_body))
        for alert in inv_rep.reorder_alerts:
            story.append(Paragraph(f"• {_safe_text(alert)}", style_bullet))

    story.append(Spacer(1, 4))
    story.append(Paragraph("9. Root Cause Analysis & Problem Diagnostics", style_h1))
    rca_rep = report.root_cause_analysis

    if rca_rep and rca_rep.root_causes:
        story.append(Paragraph(_safe_text(rca_rep.summary_statement), style_body))
        for rc in rca_rep.root_causes:
            story.append(Paragraph(f"<b>Diagnostic: {_safe_text(rc.issue_title)}</b>", style_h2))
            story.append(Paragraph(f"• <b>Confirmed Observation:</b> {_safe_text(rc.confirmed_observation)}", style_bullet))
            story.append(Paragraph(f"• <b>Contributing Factors:</b> {_safe_text(', '.join(rc.possible_contributing_factors))}", style_bullet))
            story.append(Paragraph(f"• <b>Validation Data Needed:</b> {_safe_text(', '.join(rc.data_needed_for_validation))}", style_bullet))
            story.append(Paragraph(f"• <b>Recommended Investigation:</b> {_safe_text(rc.recommended_investigation)}", style_bullet))

    # END OF PAGE 6
    story.append(PageBreak())

    # ====================================================
    # PAGE 7: BUSINESS RISK REGISTER & MARKET COMPETITION
    # ====================================================
    story.append(Paragraph("10. Business Risk & Anomaly Register", style_h1))
    r_rep = report.risks_anomalies

    if r_rep.verified_risks:
        story.append(Paragraph(_safe_text(r_rep.summary_statement), style_body))
        r_data = [[
            Paragraph("Risk Title", style_th),
            Paragraph("Category", style_th),
            Paragraph("Severity", style_th),
            Paragraph("Business Impact & Immediate Action", style_th),
        ]]
        for r in r_rep.verified_risks[:4]:
            r_data.append([
                Paragraph(_safe_text(r.title), style_td),
                Paragraph(_safe_text(r.category), style_td),
                Paragraph(_safe_text(r.severity.upper()), style_td),
                Paragraph(_safe_text(f"{r.business_impact} Action: {r.recommended_action}"), style_td),
            ])
        r_tbl = Table(r_data, colWidths=[120, 84, 60, 240])
        r_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7F1D1D")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FEF2F2")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#FCA5A5")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FEE2E2")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(r_tbl)
        story.append(Spacer(1, 6))

    story.append(Paragraph("11. Market Competition Analysis", style_h1))
    comp_rep = report.market_competition

    if not comp_rep.is_available:
        comp_box = [
            [
                Paragraph(
                    f"<b>Market Competition Status:</b><br/>"
                    f"{_safe_text(comp_rep.summary_statement)}<br/><br/>"
                    f"<font color='#64748B'><b>Required External Benchmark Fields:</b> Competitor Name, Industry Sector, Reporting Period, Competitor Revenue, Operating Margin %, Annual Growth Rate, and Relative Pricing Index.<br/>"
                    f"<i>Note: DataScope strictly distinguishes internal customer segments and sales channels from external market competitors to maintain analytical integrity.</i></font>",
                    style_body,
                )
            ]
        ]
        c_box_tbl = Table(comp_box, colWidths=[504])
        c_box_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(c_box_tbl)

    # END OF PAGE 7
    story.append(PageBreak())

    # ====================================================
    # PAGE 8: FORECASTING, STRATEGIC RECOMMENDATIONS, ACTION PLAN, CONCLUSION & APPENDIX
    # ====================================================
    story.append(Paragraph("12. Trends & Horizon Forecasting Projections", style_h1))
    fc_rep = report.forecasting

    if fc_rep.is_available and fc_rep.forecast_points:
        story.append(Paragraph(_safe_text(fc_rep.plain_language_interpretation), style_body))
        fc_data = [[
            Paragraph("Horizon Period", style_th),
            Paragraph("Projected Value", style_th),
            Paragraph("80% Confidence Band", style_th),
            Paragraph("95% Confidence Band", style_th),
        ]]
        for pt in fc_rep.forecast_points[:5]:
            fc_data.append([
                Paragraph(_safe_text(pt.period), style_td),
                Paragraph(_safe_text(pt.forecast_formatted), style_td),
                Paragraph(_safe_text(f"{pt.lower_bound_80_formatted} to {pt.upper_bound_80_formatted}"), style_td),
                Paragraph(_safe_text(f"{pt.lower_bound_95_formatted} to {pt.upper_bound_95_formatted}"), style_td),
            ])
        fc_tbl = Table(fc_data, colWidths=[100, 114, 145, 145])
        fc_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EFF6FF")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DBEAFE")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(fc_tbl)
        story.append(Spacer(1, 4))

    # Priority Action Plan Table
    story.append(Paragraph("13. Priority Corrective Action Plan (Boardroom Matrix)", style_h1))
    cap_rep = report.corrective_action_plan

    if cap_rep and cap_rep.action_items:
        act_data = [[
            Paragraph("Priority", style_th),
            Paragraph("Business Issue", style_th),
            Paragraph("Recommended Action", style_th),
            Paragraph("Owner", style_th),
            Paragraph("Target KPI", style_th),
            Paragraph("Timeframe", style_th),
        ]]
        for a in cap_rep.action_items[:5]:
            act_data.append([
                Paragraph(_safe_text(a.priority), style_td),
                Paragraph(_safe_text(a.problem), style_td),
                Paragraph(_safe_text(a.recommended_action), style_td),
                Paragraph(_safe_text(a.owner_team), style_td),
                Paragraph(_safe_text(a.metric_to_track), style_td),
                Paragraph(_safe_text(a.review_period), style_td),
            ])
        act_tbl = Table(act_data, colWidths=[45, 105, 154, 65, 75, 60])
        act_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(act_tbl)
        story.append(Spacer(1, 4))

    # Final Management Summary & Technical Validation Appendix
    story.append(Paragraph("14. Final Management Summary & Decision Boundaries", style_h1))
    if report.data_driven_conclusion.main_findings:
        for conc in report.data_driven_conclusion.main_findings[:2]:
            story.append(Paragraph(f"• <b>Executive Takeaway:</b> {_safe_text(conc)}", style_bullet))

    story.append(Spacer(1, 4))
    story.append(Paragraph("15. Data Reliability & Methodology (Appendix)", style_h1))
    d_over = report.dataset_overview
    story.append(
        Paragraph(
            _safe_text(
                f"Dataset Dimensions: {d_over.dimensions_text}   |   Quality Score: {d_over.data_quality_score}/100 ({d_over.data_quality_status})   |   Duplicate Records: {d_over.duplicate_rows_count:,} ({d_over.duplicate_rows_pct}%)<br/>"
                f"Calculation Baseline: Complete record audit with strict dimension hygiene and domain-aware revenue inference."
            ),
            ParagraphStyle("TechFoot", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=7, leading=9.5, textColor=colors.HexColor("#64748B")),
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    buf.seek(0)
    return buf
