from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


def format_datetime(dt_value):
    """
    Format:
    13th May 2026, 12:37 PM (IST)
    """

    if not dt_value:
        return "N/A"

    if isinstance(dt_value, str):
        try:
            dt_value = datetime.fromisoformat(dt_value)
        except Exception:
            return dt_value

    ist = dt_value.astimezone(ZoneInfo("Asia/Kolkata"))

    day = ist.day

    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd"
        }.get(day % 10, "th")

    return ist.strftime(
        f"{day}{suffix} %B %Y, %I:%M %p (IST)"
    )


def paragraph_cell(text, style):
    return Paragraph(str(text), style)


def generate_email_report(summary, emails):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title_style",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0D47A1"),
        fontSize=22,
        leading=28,
    )

    section_style = ParagraphStyle(
        "section_style",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1565C0"),
        fontSize=14,
        leading=18,
    )

    body_style = ParagraphStyle(
        "body_style",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
    )

    small_style = ParagraphStyle(
        "small_style",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    )

    elements = []

    # Title
    elements.append(
        Paragraph("Email Intelligence Report", title_style)
    )
    elements.append(Spacer(1, 25))

    # Executive Overview
    elements.append(
        Paragraph("Executive Overview", section_style)
    )
    elements.append(Spacer(1, 8))

    elements.append(
        Paragraph(
            summary.get("recommendation", "No overview available."),
            body_style,
        )
    )

    elements.append(Spacer(1, 20))

    # Thread details
    elements.append(
        Paragraph("Thread Details", section_style)
    )
    elements.append(Spacer(1, 8))

    thread_table = Table(
        [
            [
                paragraph_cell("Thread Start", body_style),
                paragraph_cell(
                    format_datetime(summary.get("thread_start")),
                    body_style
                ),
            ],
            [
                paragraph_cell("Thread End", body_style),
                paragraph_cell(
                    format_datetime(summary.get("thread_end")),
                    body_style
                ),
            ],
        ],
        colWidths=[140, 360],
    )

    thread_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#B0BEC5")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    elements.append(thread_table)
    elements.append(Spacer(1, 20))

    # People involved
    elements.append(
        Paragraph("People Involved", section_style)
    )
    elements.append(Spacer(1, 8))

    participant_rows = [
        [
            paragraph_cell("<b>Name</b>", body_style),
            paragraph_cell("<b>Email</b>", body_style),
        ]
    ]

    for p in summary.get("participants", []):
        participant_rows.append([
            paragraph_cell(p.get("name", "Unknown"), body_style),
            paragraph_cell(p.get("email", "Unknown"), body_style),
        ])

    participant_table = Table(
        participant_rows,
        colWidths=[180, 320],
    )

    participant_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565C0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#B0BEC5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    elements.append(participant_table)
    elements.append(Spacer(1, 20))

    # Subjects
    elements.append(
        Paragraph("Important Subjects", section_style)
    )
    elements.append(Spacer(1, 8))

    seen = set()

    for mail in emails:
        if mail.subject not in seen:
            seen.add(mail.subject)
            elements.append(
                Paragraph(f"• {mail.subject}", body_style)
            )

    elements.append(Spacer(1, 20))

    # Discussion summary
    elements.append(
        Paragraph("Conversation Summary", section_style)
    )
    elements.append(Spacer(1, 8))

    for item in summary.get("discussion_summary", []):
        elements.append(
            Paragraph(f"• {item}", body_style)
        )

    elements.append(Spacer(1, 20))

    # Further actions
    elements.append(
        Paragraph("Further Actions", section_style)
    )
    elements.append(Spacer(1, 8))

    for item in summary.get("further_actions", []):
        elements.append(
            Paragraph(f"• {item}", body_style)
        )

    elements.append(Spacer(1, 20))

    # Timeline
    elements.append(
        Paragraph("Timeline", section_style)
    )
    elements.append(Spacer(1, 10))

    timeline_rows = [
        [
            paragraph_cell("<b>Date & Time (IST)</b>", body_style),
            paragraph_cell("<b>Sender</b>", body_style),
            paragraph_cell("<b>Subject</b>", body_style),
        ]
    ]

    for mail in emails:
        timeline_rows.append([
            paragraph_cell(
                format_datetime(mail.email_date),
                small_style
            ),
            paragraph_cell(
                mail.sender,
                small_style
            ),
            paragraph_cell(
                mail.subject,
                small_style
            ),
        ])

    timeline_table = Table(
        timeline_rows,
        colWidths=[150, 170, 190],
        repeatRows=1,
    )

    timeline_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#B0BEC5")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    elements.append(timeline_table)

    doc.build(elements)

    buffer.seek(0)

    return buffer