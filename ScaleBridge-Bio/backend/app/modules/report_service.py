"""PDF Process-Transfer Report generator using ReportLab (docs/04_MVP_SCOPE.md, docs/08_API_SPECIFICATION.md)."""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def render_transfer_report_pdf(
    project: dict[str, Any],
    passport: dict[str, Any] | None,
    scenario: dict[str, Any],
    assessment: dict[str, Any],
    report_version: int,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"ScaleBridge Bio Transfer Report - {project.get('name')}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SBTitle",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0B192C"),
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "SBH2",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0D9488"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "SBBody",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
    )
    warn_style = ParagraphStyle(
        "SBWarn",
        parent=body_style,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#92400E"),
        backColor=colors.HexColor("#FEF3C7"),
        borderPadding=5,
    )

    story: list[Any] = []

    is_syn = bool(assessment.get("is_synthetic") or project.get("is_synthetic_demo"))
    if is_syn:
        story.append(
            Paragraph(
                "<b>SYNTHETIC / DEMONSTRATION DATASET NOTICE:</b> This Process-Transfer Report includes synthetic or demonstration data. It is generated for workflow evaluation only and must not be used for physical pilot execution.",
                warn_style,
            )
        )
        story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("SCALEBRIDGE BIO — PROCESS-TRANSFER READINESS REPORT", title_style))
    story.append(
        Paragraph(
            f"<b>Project:</b> {project.get('name')} &nbsp;|&nbsp; "
            f"<b>Organism:</b> {project.get('organism_name') or 'Unspecified'} &nbsp;|&nbsp; "
            f"<b>Process Type:</b> {project.get('process_type')} &nbsp;|&nbsp; "
            f"<b>Report Version:</b> v{report_version}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>Scenario:</b> {scenario.get('name')} &nbsp;|&nbsp; "
            f"<b>Assessment ID:</b> {assessment.get('id')} &nbsp;|&nbsp; "
            f"<b>Engine Version:</b> {assessment.get('engine_version')} "
            f"(Formulas {assessment.get('formula_registry_version')}, Rules {assessment.get('rule_registry_version')})",
            body_style,
        )
    )
    story.append(Spacer(1, 3 * mm))

    # 1. Executive Readiness Summary
    story.append(Paragraph("1. Executive Readiness Summary", h2_style))
    summary = assessment.get("summary", {})
    sev = summary.get("triggered_by_severity", {})
    summary_data = [
        [
            "Overall Evidence Level",
            "Critical Flags",
            "High Flags",
            "Medium Flags",
            "Insufficient Evidence Items",
            "Validation Tasks",
        ],
        [
            str(summary.get("overall_evidence_level", "unknown")).upper(),
            str(sev.get("critical", 0)),
            str(sev.get("high", 0)),
            str(sev.get("medium", 0)),
            str(summary.get("insufficient_evidence_flag_count", 0)),
            str(summary.get("validation_task_count", 0)),
        ],
    ]
    t_sum = Table(summary_data, colWidths=[32 * mm, 24 * mm, 24 * mm, 26 * mm, 38 * mm, 30 * mm])
    t_sum.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B192C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_sum)

    # 2. Vessel Comparison
    story.append(Paragraph("2. Source vs Target Vessel Profile Snapshot", h2_style))
    snap = assessment.get("inputs_snapshot", {})
    src_v = snap.get("source_vessel", {})
    tgt_v = snap.get("target_vessel", {})
    v_rows = [
        [
            "Vessel Attribute / Parameter",
            f"Source: {src_v.get('name', 'Lab')}",
            f"Target: {tgt_v.get('name', 'Pilot')}",
        ],
        ["Scale Class", str(src_v.get("scale_class", "")), str(tgt_v.get("scale_class", ""))],
        [
            "Impeller Type & Count",
            f"{src_v.get('impeller_type') or 'N/A'} (n={src_v.get('impeller_count') or 1})",
            f"{tgt_v.get('impeller_type') or 'N/A'} (n={tgt_v.get('impeller_count') or 1})",
        ],
    ]
    for pkey in [
        "working_volume_max",
        "vessel_inner_diameter",
        "impeller_diameter",
        "impeller_power_number",
        "agitation_speed_max",
        "motor_power_limit",
        "gas_flow_max",
        "cooling_capacity",
    ]:
        sp = (src_v.get("parameters") or {}).get(pkey)
        tp = (tgt_v.get("parameters") or {}).get(pkey)
        s_str = (
            f"{sp.get('display_value', sp.get('value')):.3g} {sp.get('display_unit', sp.get('unit'))} [{sp.get('provenance')}]"
            if sp
            else "Missing"
        )
        t_str = (
            f"{tp.get('display_value', tp.get('value')):.3g} {tp.get('display_unit', tp.get('unit'))} [{tp.get('provenance')}]"
            if tp
            else "Missing"
        )
        v_rows.append([pkey, s_str, t_str])

    t_v = Table(v_rows, colWidths=[54 * mm, 60 * mm, 60 * mm])
    t_v.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    story.append(t_v)

    # 3. Engineering Calculations
    story.append(Paragraph("3. Scale-Up Engineering Calculations & Provenance", h2_style))
    calc_rows = [["Formula", "Scale / Criterion", "Equation", "Result (Display)", "Status / Evidence"]]
    for c in assessment.get("calculations", []):
        out = c.get("output")
        if out and c.get("status") == "computed":
            res_str = f"{out.get('display_value', out.get('value')):.4g} {out.get('display_unit', out.get('unit'))}"
        else:
            missing_str = ", ".join(c.get("missing_inputs") or [])
            res_str = f"Insufficient ({missing_str})"
        calc_rows.append(
            [
                f"{c.get('formula_id')} ({c.get('formula_name')})",
                f"{c.get('scale')} / {c.get('criterion_id') or 'baseline'}",
                str(c.get("equation", "")),
                Paragraph(res_str, body_style),
                f"{c.get('status')} [{c.get('evidence_level')}]",
            ]
        )

    t_calc = Table(calc_rows, colWidths=[42 * mm, 28 * mm, 36 * mm, 38 * mm, 30 * mm])
    t_calc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B192C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(t_calc)

    # 4. Equipment Compatibility Checks
    story.append(Paragraph("4. Target Vessel Capability Envelope Compatibility", h2_style))
    compat_rows = [["Check ID", "Criterion", "Parameter", "Outcome", "Explanation"]]
    for chk in assessment.get("compatibility_checks", []):
        compat_rows.append(
            [
                str(chk.get("check_id")),
                str(chk.get("criterion_id") or "All"),
                str(chk.get("parameter_key")),
                str(chk.get("outcome")).upper(),
                Paragraph(str(chk.get("explanation", "")), body_style),
            ]
        )
    t_comp = Table(compat_rows, colWidths=[24 * mm, 20 * mm, 30 * mm, 26 * mm, 74 * mm])
    t_comp.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(t_comp)

    # 5. Explainable Risk Register
    story.append(Paragraph("5. Scale-Up Risk Register & Missing Evidence", h2_style))
    risk_rows = [["Rule ID", "Category / Severity", "Outcome", "Explanation & Evidence Gap"]]
    for rf in assessment.get("risk_flags", []):
        if rf.get("outcome") == "not_triggered":
            continue
        gap_txt = f"<br/><b>Evidence Gap:</b> {rf.get('evidence_gap')}" if rf.get("evidence_gap") else ""
        risk_rows.append(
            [
                f"{rf.get('rule_id')} v{rf.get('rule_version')}",
                f"{rf.get('category')} / {str(rf.get('severity')).upper()}",
                str(rf.get("outcome")),
                Paragraph(f"<b>{rf.get('title')}:</b> {rf.get('explanation')}{gap_txt}", body_style),
            ]
        )
    if len(risk_rows) > 1:
        t_risk = Table(risk_rows, colWidths=[26 * mm, 32 * mm, 28 * mm, 88 * mm])
        t_risk.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B192C")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 3.5),
                ]
            )
        )
        story.append(t_risk)

    # 6. Validation Plan
    story.append(Paragraph("6. Prioritized Pre-Pilot Validation Plan", h2_style))
    vt_rows = [["Code", "Priority / Type", "Status", "Action Required"]]
    for vt in assessment.get("validation_tasks", []):
        waiver = f" (Waived: {vt.get('waived_reason')})" if vt.get("status") == "waived" else ""
        vt_rows.append(
            [
                str(vt.get("task_code")),
                f"{vt.get('priority')} / {vt.get('task_type')}",
                f"{vt.get('status')}{waiver}",
                Paragraph(f"<b>{vt.get('title')}:</b> {vt.get('description')}", body_style),
            ]
        )
    if len(vt_rows) > 1:
        t_vt = Table(vt_rows, colWidths=[28 * mm, 28 * mm, 28 * mm, 90 * mm])
        t_vt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D9488")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 3.5),
                ]
            )
        )
        story.append(t_vt)

    # 7. Reviewer Sign-offs & Scientific Disclaimer
    story.append(Paragraph("7. Expert Review Sign-Offs & Scientific Limitations", h2_style))
    reviews = assessment.get("reviews", [])
    if reviews:
        for rev in reviews:
            story.append(
                Paragraph(
                    f"• <b>{rev.get('reviewer_name')}</b> ({rev.get('decision')} at {rev.get('created_at')}): {rev.get('comment')}",
                    body_style,
                )
            )
    else:
        story.append(
            Paragraph(
                "• <b>Review Status:</b> No formal domain-expert sign-off recorded yet for this assessment.",
                body_style,
            )
        )

    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "<b>SCIENTIFIC & REGULATORY DISCLAIMER:</b> ScaleBridge Bio is a process-engineering decision-support workspace, not an autonomous controller, validated digital twin, or engineering design package. Calculations use deterministic relationships (such as OTR = kLa(C* − C_L)) whose validity depends on measured inputs and vessel-specific characterization. Not for GMP production execution or 21 CFR Part 11 compliance.",
            warn_style,
        )
    )

    doc.build(story)
    return buf.getvalue()
