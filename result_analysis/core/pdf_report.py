"""Visual ReportLab reports with summary cards and optional student lists."""

from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
import os
from threading import RLock
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape
from zoneinfo import ZoneInfo
import pandas as pd
from result_analysis.core.translations import translate
from result_analysis.core.numerals import digits
from result_analysis.core.dates import report_date


def escape(value: str) -> str:
    """Use portable mathematical text while preserving Unicode student names."""
    replacements = {
        "−": "-",
        "–": "-",
        "—": "-",
        "×": " x ",
        "≥": ">=",
        "≤": "<=",
        "↑": "",
        "↓": "",
        "→": "",
        "’": "'",
        "…": "...",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return xml_escape(value)


@dataclass
class Report:
    """The same tables, interpretations and chart definitions shown in the UI."""

    title: str
    tables: list[tuple[str, pd.DataFrame]] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)
    charts: list = field(default_factory=list)
    include_student_lists: bool = False


def font_path() -> Path | None:
    """Optional TrueType font supporting Tibetan and Latin characters."""
    configured = os.environ.get("DZONGKHA_FONT_PATH", "")
    if configured and Path(configured).is_file():
        return Path(configured)
    for name in ["ResultTibetan.ttf", "Jomolhari.ttf", "NotoSerifTibetan-Regular.ttf"]:
        candidate = Path(__file__).resolve().parent.parent / "assets" / name
        if candidate.is_file():
            return candidate
    return None


_PDF_LOCK = RLock()


def build_pdf(report: Report, metadata: dict[str, str]) -> bytes:
    """Serialize font registration and matplotlib rendering within this process."""
    with _PDF_LOCK:
        return _build_pdf(report, metadata)


def selected_charts(report: Report) -> list:
    """Choose complementary visuals instead of repeating every descriptive metric."""
    from result_analysis.core.charts import Chart

    charts = []
    for chart in report.charts:
        if chart.group in ("Gender", "Residence") and chart.y not in ("Mean", "Pass %"):
            continue
        if chart.kind == "heatmap" and chart.y not in ("Mean", "Pass %"):
            continue
        if chart.group == "Section" and chart.y not in ("Mean", "Pass %"):
            continue
        charts.append(chart)
    for title, frame in report.tables:
        if frame.empty:
            continue
        if title == "Class overview":
            counts = frame.iloc[0]
            if all(key in counts for key in ["Failing 1", "Failing 2", "Failing 3+"]):
                chart_data = pd.DataFrame(
                    {
                        "Failed subjects": ["1", "2", "3 or more"],
                        "Students": [
                            counts["Failing 1"],
                            counts["Failing 2"],
                            counts["Failing 3+"],
                        ],
                    }
                )
                charts.append(
                    Chart(
                        "Students needing subject support",
                        "bar",
                        chart_data,
                        "Failed subjects",
                        "Students",
                    )
                )
        if title == "Subject diagnosis and strength ranking":
            charts.append(
                Chart(
                    "Subject priorities",
                    "bar",
                    frame,
                    "Subject",
                    "Strength",
                    "Diagnosis",
                )
            )
        if title == "Section comparison and overall ranks":
            charts.insert(
                0,
                Chart(
                    "Overall section performance", "bar", frame, "Section", "Composite"
                ),
            )
        if title == "Per-subject statistics (%)" and frame["Excluded"].sum() > 0:
            charts.append(
                Chart(
                    "Unassessed marks by subject", "bar", frame, "Subject", "Excluded"
                )
            )
    return charts


def _build_pdf(report: Report, metadata: dict[str, str]) -> bytes:
    """Visual-first portrait A4: headline figures, charts and optional student lists."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        PageBreak,
        LongTable,
        Table,
        TableStyle,
        Image,
        KeepTogether,
    )
    from result_analysis.core.charts import image_bytes

    lang = metadata.get('Language', 'en')
    tr = lambda value: translate(value, lang)
    # Translate presentation text only; report data stays canonical for selection.
    original_paragraph = Paragraph
    def Paragraph(value, style):
        return original_paragraph(tr(value), style)
    output = BytesIO()
    font = "Helvetica"
    path = font_path()
    if path:
        font = "Dzongkha"
        if font not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font, str(path)))
    ink = colors.HexColor("#19384A")
    muted = colors.HexColor("#526A78")
    body = ParagraphStyle("Body", fontName=font, fontSize=10, leading=19, shaping=True, textColor=ink)
    small = ParagraphStyle(
        "Small", parent=body, fontSize=8, leading=16, textColor=muted
    )
    heading = ParagraphStyle(
        "Heading",
        parent=body,
        fontSize=16,
        leading=29,
        spaceAfter=10,
        keepWithNext=True,
    )
    title_style = ParagraphStyle(
        "Title", parent=body, fontSize=21, leading=36, spaceAfter=10
    )
    number_style = ParagraphStyle("Number", parent=body, fontSize=23, leading=28)
    header_style = ParagraphStyle("TableHead", parent=small, textColor=colors.white)
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=23 * mm,
        bottomMargin=19 * mm,
        title=report.title,
        author=metadata.get("Teacher", ""),
    )
    date = report_date(datetime.now(ZoneInfo("Asia/Thimphu")), lang)
    school = metadata.get("School") or "School not supplied"
    story = [
        original_paragraph(escape(digits(school, lang)), heading),
        Paragraph(escape(tr(report.title)), title_style),
    ]
    context = f"Academic year {metadata.get('Year', 'Not supplied')} · Class {metadata.get('Class', 'Not supplied')} · Section {metadata.get('Section', 'As uploaded')}"
    story += [Paragraph(escape(tr(context)), body)]
    if metadata.get("Teacher"):
        story.append(Paragraph(escape("Prepared by " + metadata["Teacher"]), small))
    story += [Spacer(1, 7 * mm)]
    summary_frame = next(
        (
            f
            for name, f in report.tables
            if name in ("Summary (%)", "Class overview") and not f.empty
        ),
        None,
    )
    if summary_frame is not None:
        row = summary_frame.iloc[0]
        keys = (
            ["n", "Mean", "Median", "Pass %", "Std dev", "Excluded"]
            if "n" in row.index
            else [
                "Students",
                "Mean",
                "Passed all %",
                "Passed any %",
                "Complete n",
                "Assessed n",
            ]
        )
        labels = {
            "n": "Assessed students",
            "Mean": "Mean (%)",
            "Median": "Median (%)",
            "Std dev": "Sample SD",
            "Complete n": "Complete results",
            "Assessed n": "Assessed students",
            "Excluded": "Excluded marks",
        }
        cards = []
        for key in keys:
            value = row.get(key)
            value_text = (
                "N/A"
                if pd.isna(value)
                else f"{value:.2f}"
                if isinstance(value, float)
                else str(value)
            )
            cards.append(
                [
                    Paragraph(escape(tr(labels.get(key, key))), small),
                    Paragraph(escape(value_text), number_style),
                ]
            )
        card_rows = [cards[i : i + 3] for i in range(0, len(cards), 3)]
        table = Table(card_rows, colWidths=[doc.width / 3] * 3)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF5F5")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D3E2E5")),
                    ("INNERGRID", (0, 0), (-1, -1), 3, colors.white),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story += [table, Spacer(1, 4 * mm)]
        note = (
            "Pass rate uses valid marks only. Blank/Absent marks are excluded."
            if "n" in row.index
            else "Passed all uses complete results; passed any uses assessed students. Mean uses available subject averages."
        )
        story.append(Paragraph(note, small))
    best = next(
        (
            text
            for text in report.texts
            if text.startswith("Best performing section overall:")
        ),
        None,
    )
    if best:
        story += [Spacer(1, 3 * mm), Paragraph(escape(best), body)]
    charts = selected_charts(report)
    for index, chart in enumerate(charts):
        if index == 1 or (index > 1 and index % 2 == 1):
            story.append(PageBreak())
        story.append(Spacer(1, 5 * mm))
        image = Image(
            BytesIO(image_bytes(chart, lang=lang)), width=doc.width, height=doc.width * 0.48
        )
        story.append(KeepTogether([image, Spacer(1, 4 * mm)]))
    if not charts:
        story.append(Paragraph("No chart data available for this report.", body))
    if report.include_student_lists:
        for title, frame in report.tables:
            if frame.empty or "Student ID" not in frame.columns:
                continue
            preferred = [
                "Student ID",
                "Student Name",
                "Rank",
                "Average %",
                "Score %",
                "Failed subjects",
                "Borderline subjects",
                "Excluded subjects",
            ]
            columns = [c for c in preferred if c in frame.columns][:6]
            if len(columns) <= 2:
                columns += [c for c in frame.columns if c not in columns][:3]
            story += [PageBreak(), Paragraph(escape(tr(title)), heading)]
            cells = [[Paragraph(escape(tr(c)), header_style) for c in columns]]
            for values in frame[columns].itertuples(index=False, name=None):
                cells.append(
                    [
                        original_paragraph(
                            escape(digits(
                                tr("N/A")
                                if pd.isna(v)
                                else f"{v:.2f}"
                                if isinstance(v, float)
                                else str(v), lang
                            )),
                            small,
                        )
                        for v in values
                    ]
                )
            listing = LongTable(
                cells, colWidths=[doc.width / len(columns)] * len(columns), repeatRows=1
            )
            listing.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), ink),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#EFF5F5")],
                        ),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.append(listing)

    def page(canvas, document):
        canvas.saveState()
        canvas.setFillColor(ink)
        canvas.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, fill=1, stroke=0)
        header = Paragraph(
            escape(f"{school} · {metadata.get('Year', '')} · {date}"), small
        )
        _, height = header.wrap(doc.width, 12 * mm)
        header.drawOn(canvas, 16 * mm, A4[1] - 10 * mm - height)
        canvas.setStrokeColor(colors.HexColor("#CDDDE2"))
        canvas.line(16 * mm, 15 * mm, A4[0] - 16 * mm, 15 * mm)
        canvas.setFont(font, 8)
        canvas.setFillColor(muted)
        footer = Paragraph(tr("Bhutan Result Analysis Tool") + " · " + tr("Pass threshold 40%"), small)
        footer.wrap(doc.width - 25*mm, 12*mm)
        footer.drawOn(canvas, 16*mm, 8*mm)
        page_number = Paragraph(tr(f"Page {document.page}"), small)
        page_number.wrap(25*mm, 12*mm)
        page_number.drawOn(canvas, A4[0]-40*mm, 8*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=page, onLaterPages=page)
    return output.getvalue()
