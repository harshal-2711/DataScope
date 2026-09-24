"""DOCX Document Generator for DataScope Executive Business Intelligence Reports.

Produces structured, beautifully formatted Word documents using python-docx with:
- Boardroom-ready executive title and business metadata header
- Executive Business KPI Summary Matrix
- Executive Narrative & 6-Question Structured Business Sections
- Customer Segments, Regional Channels, P&L Loss-Makers, Discount Controls
- Root Cause Analysis & 5-Step Action Roadmaps
- Priority Action Plan Table
- Forecasting, Market Competition, and Decision Boundaries
- Optional secondary Technical Data Validation at the end
"""
from __future__ import annotations

import io
from typing import List, Optional

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from app.schemas.report import ComprehensiveReportResponse


def _set_cell_background(cell, fill_hex: str):
    """Set background color of a table cell using XML shading."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    """Set cell internal padding in twips."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)


def _style_table_header(row, bg_hex="1E293B", text_color="FFFFFF"):
    """Format table header row with bold white text and dark slate background."""
    for cell in row.cells:
        _set_cell_background(cell, bg_hex)
        _set_cell_margins(cell, top=140, bottom=140, left=140, right=140)
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(9.5)
                run.font.name = "Calibri"
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if text_color == "FFFFFF" else RGBColor(0x1E, 0x29, 0x3B)


def _style_table_cells(table, zebra_hex="F8FAFC"):
    """Apply alternating zebra shading and clean padding to table body."""
    for r_idx, row in enumerate(table.rows[1:], start=1):
        bg = zebra_hex if r_idx % 2 == 1 else "FFFFFF"
        for cell in row.cells:
            _set_cell_background(cell, bg)
            _set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Calibri"


def generate_docx_report(
    report: ComprehensiveReportResponse,
    selected_sections: Optional[List[str]] = None,
) -> io.BytesIO:
    """Generate and return a binary stream of the DOCX report."""
    doc = Document()

    # Set page margins
    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        
        # Configure Header & Footer
        header = s.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(f"DataScope Business Intelligence Report | {report.metadata.dataset_name}")
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

        footer = s.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run(f"Generated on {report.metadata.generated_at} · Executive Decision Intelligence")
        frun.font.size = Pt(8)
        frun.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    meta = report.metadata
    exec_sum = report.executive_summary

    # ----------------------------------------------------
    # TITLE & HEADER BLOCK
    # ----------------------------------------------------
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(10)
    title_p.paragraph_format.space_after = Pt(2)
    run_badge = title_p.add_run("DATASCOPE BUSINESS INTELLIGENCE & DECISION SUPPORT\n")
    run_badge.font.size = Pt(10)
    run_badge.font.bold = True
    run_badge.font.color.rgb = RGBColor(0x25, 0x63, 0xEB)

    run_title = title_p.add_run(f"Business Performance Report: {meta.dataset_name}")
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    sub_run = sub_p.add_run(
        f"Domain: {meta.domain_name}   |   Reporting Period: {meta.reporting_period}   |   Business Condition: {exec_sum.overall_business_condition}"
    )
    sub_run.font.size = Pt(9.5)
    sub_run.font.italic = True
    sub_run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    # ----------------------------------------------------
    # SECTION 1: EXECUTIVE BUSINESS SUMMARY
    # ----------------------------------------------------
    h1 = doc.add_heading("1. Executive Business Summary", level=1)
    h1.paragraph_format.space_before = Pt(12)
    h1.paragraph_format.space_after = Pt(6)

    # KPI Table
    kpi_cards = [
        ("Total Revenue", exec_sum.total_sales_revenue or "N/A"),
        ("Net Profit", exec_sum.total_profit_loss or "N/A"),
        ("Profit Margin", exec_sum.profit_margin_pct or "N/A"),
        ("Total Orders", exec_sum.total_orders_count or "N/A"),
        ("Avg Order Value", exec_sum.average_order_value or "N/A"),
        ("Units Sold", exec_sum.total_units_sold or "N/A"),
        ("Avg Discount", exec_sum.average_discount_pct or "N/A"),
        ("Business Health", exec_sum.overall_business_health),
    ]

    kpi_table = doc.add_table(rows=2, cols=4)
    kpi_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, (label, val) in enumerate(kpi_cards):
        r_idx = idx // 4
        c_idx = idx % 4
        cell = kpi_table.rows[r_idx].cells[c_idx]
        _set_cell_background(cell, "F1F5F9")
        _set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        r1 = p.add_run(f"{label}\n")
        r1.font.size = Pt(8)
        r1.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
        
        r2 = p.add_run(val)
        r2.font.size = Pt(12)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    # Narrative Summary Callout Box
    summary_box = doc.add_table(rows=1, cols=1)
    summary_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    c_box = summary_box.rows[0].cells[0]
    _set_cell_background(c_box, "EFF6FF")
    _set_cell_margins(c_box, top=120, bottom=120, left=140, right=140)
    sp = c_box.paragraphs[0]
    s_title = sp.add_run("Executive Business Briefing:\n")
    s_title.font.bold = True
    s_title.font.size = Pt(10)
    s_title.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)
    s_body = sp.add_run(exec_sum.overall_performance_summary)
    s_body.font.size = Pt(9.5)
    s_body.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    # Major Positives & Negatives
    if exec_sum.major_positive_findings or exec_sum.major_negative_findings:
        p_pn = doc.add_paragraph()
        p_pn.paragraph_format.space_before = Pt(8)
        p_pn.paragraph_format.space_after = Pt(2)
        r_pn = p_pn.add_run("Core Performance Observations:")
        r_pn.font.bold = True
        r_pn.font.size = Pt(10)

        for pos in exec_sum.major_positive_findings:
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.space_after = Pt(2)
            br = bp.add_run(f"[POSITIVE] {pos}")
            br.font.size = Pt(9)
            br.font.color.rgb = RGBColor(0x05, 0x96, 0x69)

        for neg in exec_sum.major_negative_findings:
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.space_after = Pt(2)
            br = bp.add_run(f"[ATTENTION] {neg}")
            br.font.size = Pt(9)
            br.font.color.rgb = RGBColor(0xDC, 0x26, 0x26)

    # Top 3 Recommended Actions
    if exec_sum.top_3_recommended_actions:
        p_act = doc.add_paragraph()
        p_act.paragraph_format.space_before = Pt(6)
        p_act.paragraph_format.space_after = Pt(2)
        r_act = p_act.add_run("Top Priority Management Actions:")
        r_act.font.bold = True
        r_act.font.size = Pt(10)
        for act in exec_sum.top_3_recommended_actions:
            bp = doc.add_paragraph(style="List Bullet")
            bp.paragraph_format.space_after = Pt(2)
            br = bp.add_run(act)
            br.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 2: BUSINESS PERFORMANCE & OPERATIONAL KPIS
    # ----------------------------------------------------
    h2 = doc.add_heading("2. Business Performance Overview", level=1)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(4)

    bp_rep = report.business_performance
    if not bp_rep.is_available:
        p_un = doc.add_paragraph(bp_rep.unavailable_reason or "Business performance breakdown is unavailable.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        p_pdesc = doc.add_paragraph(bp_rep.summary_text)
        p_pdesc.runs[0].font.size = Pt(9.5)

        if bp_rep.metric_highlights:
            doc.add_heading("Key Operational Performance Indicators", level=2)
            kpi_tbl = doc.add_table(rows=1, cols=4)
            kpi_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = kpi_tbl.rows[0]
            hdr.cells[0].text = "Metric Name"
            hdr.cells[1].text = "Observed Value"
            hdr.cells[2].text = "Business Meaning"
            hdr.cells[3].text = "Attention Required"
            _style_table_header(hdr)

            for m in bp_rep.metric_highlights:
                row = kpi_tbl.add_row()
                row.cells[0].text = m.name
                row.cells[1].text = m.formatted_value
                row.cells[2].text = m.business_meaning
                row.cells[3].text = "YES (Review)" if m.requires_attention else "Normal"
            _style_table_cells(kpi_tbl)

        if bp_rep.top_performers:
            doc.add_heading("Top Commercial Performers", level=2)
            perf_tbl = doc.add_table(rows=1, cols=4)
            perf_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = perf_tbl.rows[0]
            hdr.cells[0].text = "Segment / Entity"
            hdr.cells[1].text = "Dimension"
            hdr.cells[2].text = "Revenue"
            hdr.cells[3].text = "Share %"
            _style_table_header(hdr)

            for item in bp_rep.top_performers:
                row = perf_tbl.add_row()
                row.cells[0].text = item.name
                row.cells[1].text = item.entity_type
                row.cells[2].text = item.formatted_value
                row.cells[3].text = f"{item.percentage_share:.1f}%" if item.percentage_share else "N/A"
            _style_table_cells(perf_tbl)

    # ----------------------------------------------------
    # SECTION 3: 6-POINT REVENUE & SALES ANALYSIS
    # ----------------------------------------------------
    if bp_rep.six_point_findings:
        doc.add_heading("3. Revenue & Sales In-Depth Analysis", level=1)
        for f in bp_rep.six_point_findings:
            p_fhead = doc.add_paragraph()
            p_fhead.paragraph_format.space_before = Pt(8)
            p_fhead.paragraph_format.space_after = Pt(2)
            r_fh = p_fhead.add_run(f"Observation: {f.observation_title}")
            r_fh.font.bold = True
            r_fh.font.size = Pt(10.5)

            six_points = [
                ("1. WHAT WAS OBSERVED", f.what_happened),
                ("2. BUSINESS MEANING", f.business_meaning),
                ("3. WHY IT MATTERS", f.why_it_matters),
                ("4. RECOMMENDED ACTION", f.recommended_action),
                ("5. EVIDENCE FROM DATA", f.evidence),
                ("6. LIMITATIONS TO NOTE", f.limitations),
            ]
            for q_label, q_val in six_points:
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.space_after = Pt(2)
                r_ql = bp.add_run(f"{q_label}: ")
                r_ql.font.bold = True
                r_ql.font.size = Pt(8.5)
                r_qv = bp.add_run(q_val)
                r_qv.font.size = Pt(8.5)

    # ----------------------------------------------------
    # SECTION 4: PROFIT & LOSS ANALYSIS
    # ----------------------------------------------------
    h4 = doc.add_heading("4. Profit & Loss Analysis", level=1)
    h4.paragraph_format.space_before = Pt(14)
    h4.paragraph_format.space_after = Pt(4)

    pl_rep = report.profit_loss
    if not pl_rep.is_available:
        p_un = doc.add_paragraph(pl_rep.unavailable_reason or "Reliable profit and loss analysis is unavailable.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        p_pl_meta = doc.add_paragraph(
            f"Revenue: {pl_rep.revenue_trend_summary}   |   Net Profit: {pl_rep.profit_trend_summary}   |   Margin: {pl_rep.profit_margin_summary}"
        )
        p_pl_meta.runs[0].font.bold = True
        p_pl_meta.runs[0].font.size = Pt(9.5)

        if pl_rep.loss_making_segments:
            doc.add_heading("Loss-Making Segments (Direct Margin Leakage)", level=2)
            loss_tbl = doc.add_table(rows=1, cols=4)
            loss_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = loss_tbl.rows[0]
            hdr.cells[0].text = "Segment Name"
            hdr.cells[1].text = "Revenue"
            hdr.cells[2].text = "Loss Amount"
            hdr.cells[3].text = "Margin %"
            _style_table_header(hdr, bg_hex="991B1B")

            for item in pl_rep.loss_making_segments:
                row = loss_tbl.add_row()
                row.cells[0].text = item.name
                row.cells[1].text = item.revenue_formatted
                row.cells[2].text = item.profit_loss_formatted
                row.cells[3].text = f"{item.profit_margin_pct:.1f}%"
            _style_table_cells(loss_tbl, zebra_hex="FEF2F2")

        if pl_rep.high_sales_low_profit_segments:
            doc.add_heading("High-Volume Low-Margin Products (<10% Margin)", level=2)
            thin_tbl = doc.add_table(rows=1, cols=4)
            thin_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            hdr = thin_tbl.rows[0]
            hdr.cells[0].text = "Segment Name"
            hdr.cells[1].text = "Revenue"
            hdr.cells[2].text = "Profit"
            hdr.cells[3].text = "Margin %"
            _style_table_header(hdr, bg_hex="D97706")

            for item in pl_rep.high_sales_low_profit_segments:
                row = thin_tbl.add_row()
                row.cells[0].text = item.name
                row.cells[1].text = item.revenue_formatted
                row.cells[2].text = item.profit_loss_formatted
                row.cells[3].text = f"{item.profit_margin_pct:.1f}%"
            _style_table_cells(thin_tbl, zebra_hex="FFFBEB")

        if pl_rep.discount_margin_observations:
            doc.add_heading("Discount vs Profit Margin Dynamics", level=2)
            for obs in pl_rep.discount_margin_observations:
                bp = doc.add_paragraph(style="List Bullet")
                br = bp.add_run(obs)
                br.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 5: CUSTOMER & SEGMENT ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("5. Customer & Segment Analysis", level=1)
    cust_rep = report.customer_segment_analysis
    if not cust_rep or not cust_rep.is_available:
        p_un = doc.add_paragraph(cust_rep.unavailable_reason if cust_rep else "Customer segment analysis is unavailable because customer classification fields were not detected.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        doc.add_paragraph(cust_rep.strategic_summary)
        c_tbl = doc.add_table(rows=1, cols=5)
        c_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = c_tbl.rows[0]
        hdr.cells[0].text = "Customer Segment"
        hdr.cells[1].text = "Revenue"
        hdr.cells[2].text = "Share %"
        hdr.cells[3].text = "Average Order Value"
        hdr.cells[4].text = "Marketing Strategy"
        _style_table_header(hdr)

        for s in cust_rep.segments:
            row = c_tbl.add_row()
            row.cells[0].text = s.segment_name
            row.cells[1].text = s.revenue_formatted
            row.cells[2].text = f"{s.revenue_share_pct:.1f}%"
            row.cells[3].text = s.aov_formatted
            row.cells[4].text = s.marketing_strategy
        _style_table_cells(c_tbl)

    # ----------------------------------------------------
    # SECTION 6: REGIONAL / CHANNEL ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("6. Regional & Channel Distribution", level=1)
    rc_rep = report.regional_channel_analysis
    if not rc_rep or not rc_rep.is_available:
        p_un = doc.add_paragraph(rc_rep.unavailable_reason if rc_rep else "Regional/channel analysis is unavailable because distribution dimensions were not detected.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        doc.add_paragraph(rc_rep.operational_takeaway)
        rc_tbl = doc.add_table(rows=1, cols=4)
        rc_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = rc_tbl.rows[0]
        hdr.cells[0].text = f"{rc_rep.dimension_name or 'Distribution Hub'}"
        hdr.cells[1].text = "Revenue"
        hdr.cells[2].text = "Share %"
        hdr.cells[3].text = "Operational Observation"
        _style_table_header(hdr)

        for r in rc_rep.items:
            row = rc_tbl.add_row()
            row.cells[0].text = r.name
            row.cells[1].text = r.revenue_formatted
            row.cells[2].text = f"{r.revenue_share_pct:.1f}%"
            row.cells[3].text = r.operational_observation
        _style_table_cells(rc_tbl)

    # ----------------------------------------------------
    # SECTION 7: DISCOUNT & PRICING ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("7. Discount & Pricing Controls", level=1)
    dp_rep = report.discount_pricing
    if not dp_rep or not dp_rep.is_available:
        p_un = doc.add_paragraph(dp_rep.unavailable_reason if dp_rep else "Discount analysis unavailable.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        if dp_rep.margin_erosion_estimate:
            p_er = doc.add_paragraph(f"Margin Erosion Risk: {dp_rep.margin_erosion_estimate}")
            p_er.runs[0].font.bold = True

        for obs in dp_rep.discount_tier_observations:
            bp = doc.add_paragraph(style="List Bullet")
            br = bp.add_run(obs)
            br.font.size = Pt(9)

        if dp_rep.suggested_controls:
            doc.add_heading("Suggested Discount Governance Rules", level=2)
            for ctrl in dp_rep.suggested_controls:
                bp = doc.add_paragraph(style="List Bullet")
                br = bp.add_run(ctrl)
                br.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 8: INVENTORY / STOCK ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("8. Inventory & Stock Analysis", level=1)
    inv_rep = report.inventory_analysis
    if not inv_rep or not inv_rep.is_available:
        p_un = doc.add_paragraph(inv_rep.unavailable_reason if inv_rep else "Inventory analysis is unavailable.")
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)
    else:
        doc.add_paragraph(inv_rep.inventory_turnover_observation)
        for alert in inv_rep.reorder_alerts:
            bp = doc.add_paragraph(style="List Bullet")
            br = bp.add_run(alert)
            br.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 9: ROOT CAUSE ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("9. Root Cause Analysis", level=1)
    rca_rep = report.root_cause_analysis
    if rca_rep and rca_rep.root_causes:
        doc.add_paragraph(rca_rep.summary_statement)
        for rc in rca_rep.root_causes:
            p_rc = doc.add_paragraph()
            p_rc.paragraph_format.space_before = Pt(6)
            r_rc = p_rc.add_run(f"Root Cause Investigation: {rc.issue_title}")
            r_rc.font.bold = True
            r_rc.font.size = Pt(10)

            doc.add_paragraph(f"• Confirmed Observation: {rc.confirmed_observation}")
            doc.add_paragraph(f"• Contributing Factors: {', '.join(rc.possible_contributing_factors)}")
            doc.add_paragraph(f"• Data Needed for Validation: {', '.join(rc.data_needed_for_validation)}")
            doc.add_paragraph(f"• Recommended Investigation: {rc.recommended_investigation}")

    # ----------------------------------------------------
    # SECTION 10: BUSINESS RISK ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("10. Business Risk & Anomaly Register", level=1)
    r_rep = report.risks_anomalies
    if r_rep.verified_risks:
        risk_tbl = doc.add_table(rows=1, cols=4)
        risk_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = risk_tbl.rows[0]
        hdr.cells[0].text = "Risk Title"
        hdr.cells[1].text = "Category"
        hdr.cells[2].text = "Severity"
        hdr.cells[3].text = "Business Impact & Action"
        _style_table_header(hdr, bg_hex="7F1D1D")

        for r in r_rep.verified_risks:
            row = risk_tbl.add_row()
            row.cells[0].text = r.title
            row.cells[1].text = r.category
            row.cells[2].text = r.severity.upper()
            row.cells[3].text = f"{r.business_impact} Action: {r.recommended_action}"
        _style_table_cells(risk_tbl, zebra_hex="FEF2F2")

    # ----------------------------------------------------
    # SECTION 11: MARKET COMPETITION ANALYSIS
    # ----------------------------------------------------
    doc.add_heading("11. Market Competition Analysis", level=1)
    comp_rep = report.market_competition
    if not comp_rep.is_available:
        p_un = doc.add_paragraph(comp_rep.summary_statement)
        p_un.runs[0].font.italic = True
        p_un.runs[0].font.size = Pt(9.5)

        p_req = doc.add_paragraph()
        p_req.paragraph_format.space_before = Pt(4)
        p_req.add_run("Required external data fields for competitor benchmarking: Competitor Name, Sector, Period, Competitor Revenue, Margin %, Growth Rate, and Pricing Index.")
        p_req.runs[0].font.size = Pt(8.5)
        p_req.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # ----------------------------------------------------
    # SECTION 12: TRENDS & FORECASTING
    # ----------------------------------------------------
    doc.add_heading("12. Trends & Forecasting Projections", level=1)
    tr_rep = report.trends_intelligence
    fc_rep = report.forecasting

    if tr_rep.is_available:
        doc.add_paragraph(tr_rep.plain_language_interpretation)
    if fc_rep.is_available and fc_rep.forecast_points:
        doc.add_heading(f"Forecast Projections ({fc_rep.forecasted_metric})", level=2)
        fc_tbl = doc.add_table(rows=1, cols=4)
        fc_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = fc_tbl.rows[0]
        hdr.cells[0].text = "Horizon Period"
        hdr.cells[1].text = "Projected Value"
        hdr.cells[2].text = "80% Confidence Band"
        hdr.cells[3].text = "95% Confidence Band"
        _style_table_header(hdr, bg_hex="1E3A8A")

        for pt in fc_rep.forecast_points:
            row = fc_tbl.add_row()
            row.cells[0].text = pt.period
            row.cells[1].text = pt.forecast_formatted
            row.cells[2].text = f"{pt.lower_bound_80_formatted} to {pt.upper_bound_80_formatted}"
            row.cells[3].text = f"{pt.lower_bound_95_formatted} to {pt.upper_bound_95_formatted}"
        _style_table_cells(fc_tbl, zebra_hex="EFF6FF")

    # ----------------------------------------------------
    # SECTION 13: STRATEGIC RECOMMENDATIONS
    # ----------------------------------------------------
    doc.add_heading("13. Evidence-Based Strategic Recommendations", level=1)
    recs_rep = report.recommendations
    for rec in recs_rep.recommendations_list:
        p_rh = doc.add_paragraph()
        p_rh.paragraph_format.space_before = Pt(6)
        r_rh = p_rh.add_run(f"[{rec.priority.upper()}] {rec.title} (Owner: {rec.suggested_owner_team})")
        r_rh.font.bold = True
        r_rh.font.size = Pt(10)

        doc.add_paragraph(f"• Problem: {rec.problem}")
        doc.add_paragraph(f"• Evidence: {rec.evidence}")
        doc.add_paragraph(f"• Recommended Action: {rec.exact_recommended_action}")
        doc.add_paragraph(f"• Target KPI & Timeframe: {rec.metric_to_track} ({rec.suggested_review_period})")

    # ----------------------------------------------------
    # SECTION 14: PRIORITY ACTION PLAN TABLE
    # ----------------------------------------------------
    doc.add_heading("14. Priority Action Plan Table", level=1)
    cap_rep = report.corrective_action_plan
    if cap_rep and cap_rep.action_items:
        act_tbl = doc.add_table(rows=1, cols=6)
        act_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = act_tbl.rows[0]
        hdr.cells[0].text = "Priority"
        hdr.cells[1].text = "Business Issue"
        hdr.cells[2].text = "Recommended Action"
        hdr.cells[3].text = "Owner"
        hdr.cells[4].text = "Target KPI"
        hdr.cells[5].text = "Timeframe"
        _style_table_header(hdr)

        for a in cap_rep.action_items:
            row = act_tbl.add_row()
            row.cells[0].text = a.priority
            row.cells[1].text = a.problem
            row.cells[2].text = a.recommended_action
            row.cells[3].text = a.owner_team
            row.cells[4].text = a.metric_to_track
            row.cells[5].text = a.review_period
        _style_table_cells(act_tbl)

    # ----------------------------------------------------
    # SECTION 15: BUSINESS LIMITATIONS & DECISION BOUNDARIES
    # ----------------------------------------------------
    doc.add_heading("15. Business Limitations & Missing Data", level=1)
    for lim in report.data_driven_conclusion.important_limitations:
        bp = doc.add_paragraph(style="List Bullet")
        br = bp.add_run(lim)
        br.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 16: TECHNICAL DATA VALIDATION (SECONDARY AT BOTTOM)
    # ----------------------------------------------------
    doc.add_heading("16. Technical Data Validation (Appendix)", level=1)
    d_over = report.dataset_overview
    p_tech = doc.add_paragraph(
        f"Dataset Dimensions: {d_over.dimensions_text}   |   Quality Score: {d_over.data_quality_score}/100 ({d_over.data_quality_status})   |   Duplicate Rows: {d_over.duplicate_rows_count:,} ({d_over.duplicate_rows_pct}%)"
    )
    p_tech.runs[0].font.size = Pt(8.5)
    p_tech.runs[0].font.italic = True
    p_tech.runs[0].font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out
