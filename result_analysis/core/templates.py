"""Dynamic openpyxl templates with protected headers and editable input cells."""

from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from pathlib import Path
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Protection
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from result_analysis.core.subjects_config import IDENTITY
from result_analysis.core.translations import translate
from result_analysis.core.section_names import display_section
from result_analysis.core.numerals import digits


def styled_sheet(
    ws, headers: list[str], rows: list[list], capacity: int = 1000
) -> None:
    """Lock header cells; unlock a bounded teacher-entry area."""
    ws.append(headers)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "F2" if len(headers) > 5 else "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{max(2, len(rows) + 1)}"
    ws.row_dimensions[1].height = 60
    for i, heading in enumerate(headers, 1):
        letter = get_column_letter(i)
        ws.column_dimensions[letter].width = 24 if len(heading) < 30 else 32
        cell = ws.cell(1, i)
        cell.font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill("solid", fgColor="19384A")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.protection = Protection(locked=True)
        for r in range(2, capacity + 2):
            c = ws.cell(r, i)
            c.protection = Protection(locked=False)
            if r <= max(len(rows) + 1, 12):
                c.fill = PatternFill(
                    "solid", fgColor="EFF5FA" if r % 2 == 0 else "FFFFFF"
                )
            if isinstance(c.value, str):
                c.data_type = "s"
    ws.protection.sheet = True
    ws.protection.autoFilter = False
    ws.protection.selectUnlockedCells = False
    ws.print_title_rows = "1:1"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0


def template(
    subjects: tuple[str, ...],
    sample: bool = False,
    section: str = "",
    maximum: float = 100,
    seed: int = 19,
    grade: str = "",
    lang: str = "en",
) -> bytes:
    """Build a Marks/Settings/Instructions workbook entirely in memory."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Marks"
    rng = np.random.default_rng(seed)
    names = ["Sonam", "Pema", "Karma", "Tshering", "Deki", "Tashi", "Kezang", "Choden"]
    dz_names = ["བསོད་ནམས།", "པདྨ།", "ཀརྨ།", "ཚེ་རིང་།", "བདེ་སྐྱིད།", "བཀྲ་ཤིས།", "སྐལ་བཟང་།", "ཆོས་ལྡན།"]
    rows = []
    if sample:
        for i in range(32):
            marks = np.clip(rng.normal(62, 20, len(subjects)), 0, 100) * maximum / 100
            row = [
                f"{section or 'S'}-{i + 1:03}",
                f"{dz_names[i % len(dz_names)]} དཔེ་ཚད་ {i + 1}" if lang == "dz" else f"{names[i % len(names)]} Sample {i + 1}",
                "Male" if i % 2 else "Female",
                "Boarder" if i % 3 else "Day Scholar",
                section,
            ]
            row += [round(float(v), 2) for v in marks]
            if i == 2:
                row[5] = "Absent"
            if i == 5:
                row[-1] = None
            rows.append(row)
    styled_sheet(ws, IDENTITY + list(subjects), rows)
    for column, options in [("C", "Male,Female"), ("D", "Boarder,Day Scholar")]:
        rule = DataValidation(type="list", formula1=f'"{options}"', allow_blank=False)
        rule.showErrorMessage = True
        rule.errorTitle = "Choose a listed value"
        rule.error = f"Allowed: {options}"
        rule.errorStyle = "stop"
        ws.add_data_validation(rule)
        rule.add(f"{column}2:{column}1001")
    settings = wb.create_sheet("Settings")
    styled_sheet(
        settings,
        ["Subject", "Max Marks"],
        [[s, maximum] for s in subjects],
        len(subjects),
    )
    for row in range(2, len(subjects) + 2):
        settings.cell(row, 1).protection = Protection(locked=True)
    rule = DataValidation(type="decimal", operator="greaterThan", formula1=0)
    rule.showErrorMessage = True
    settings.add_data_validation(rule)
    rule.add(f"B2:B{len(subjects) + 1}")
    details = wb.create_sheet("Report Details", 0)
    fields = [
        ["School Name", "Fictional Bhutan School" if sample else ""],
        ["Academic Year", datetime.now(ZoneInfo("Asia/Thimphu")).year],
        ["Class", grade],
        ["Teacher Name", "Sample Teacher" if sample else ""],
        ["Subjects", " | ".join(subjects)],
    ]
    styled_sheet(details, ["Field", "Value"], fields, len(fields))
    details.column_dimensions["A"].width = 25
    details.column_dimensions["B"].width = 75
    for row in range(2, 7):
        details.cell(row, 1).protection = Protection(locked=True)
        details.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="center")
        details.row_dimensions[row].height = (
            30 if row != 6 else max(45, 18 * len(subjects))
        )
    details["B6"].protection = Protection(locked=True)
    year_rule = DataValidation(
        type="whole", operator="between", formula1=2000, formula2=2100
    )
    year_rule.showErrorMessage = True
    year_rule.error = "Enter an academic year from 2000 to 2100."
    details.add_data_validation(year_rule)
    year_rule.add("B3")
    wb.active = 0
    instructions = wb.create_sheet("Instructions")
    lines = [
        "Bhutan Result Analysis Tool - "
        + ("FICTIONAL SAMPLE DATA" if sample else "EMPTY TEMPLATE"),
        "Complete School Name and Academic Year on Report Details. Check Class and Teacher Name; Subjects is generated automatically.",
        "Keep every column name and its order. Fill one student per row on Marks.",
        "Student ID must be unique across the grade. Student Name, Gender and Residence are required.",
        "Gender: Male/Female (M/F accepted). Residence: Boarder/Day Scholar (Hostel/Day-scholar accepted).",
        "Section is required for section comparison and must match the upload slot name.",
        "Enter numeric marks, Absent for an absent student, or leave a mark blank. Absent/blank are excluded per subject.",
        "Edit Max Marks on Settings before entering marks. Default maximum is 100.",
        "Pass means at least 40% of maximum marks. No formulas or totals rows are accepted.",
        "Headers and subject labels are protected. Input rows 2–1001 are unlocked.",
        "For more than 1000 students, unprotect the worksheet in Excel; the app accepts up to 10000.",
        "Sheet protection prevents accidental edits; it is not encryption or access control.",
        "All dummy sample names and marks are fictional. Remove them before entering real data.",
    ]
    instructions.column_dimensions["A"].width = 110
    for line in lines:
        instructions.append([line])
        cell = instructions.cell(instructions.max_row, 1)
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        instructions.row_dimensions[instructions.max_row].height = 32
    instructions["A1"].font = Font(bold=True, color="19384A", size=14)
    if lang == "dz":
        localize_workbook(wb)
    output = BytesIO()
    wb.save(output)
    return output.getvalue()




def localize_workbook(wb):
    """Translate a generated workbook, leaving numeric cells and IDs intact."""
    for ws in wb:
        original = ws.title
        for row in ws:
            for cell in row:
                if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                    cell.value = digits(cell.value)
                    cell.data_type = 's'
                if isinstance(cell.value, str):
                    value = cell.value
                    if original == 'Marks' and cell.column == 5 and cell.row > 1:
                        value = display_section(value, 'dz')
                    elif original == 'Report Details' and cell.coordinate == 'B6':
                        value = ' | '.join(translate(v, 'dz') for v in value.split(' | '))
                    elif original == 'Instructions' and cell.row == 1:
                        value = ' - '.join(translate(v, 'dz') for v in value.split(' - '))
                    else:
                        value = translate(value, 'dz')
                    cell.value = digits(value)
                    cell.data_type = 's'
                cell.font = Font(name='Noto Serif Tibetan', size=12,
                                 bold=cell.font.bold, color='FFFFFF' if cell.row == 1 and original != 'Instructions' else '19384A')
                cell.alignment = Alignment(wrap_text=True, vertical='center')
            if any(c.value is not None for c in row):
                ws.row_dimensions[row[0].row].height = 70 if original == 'Instructions' else 65 if row[0].row == 1 else 42
        for rule in ws.data_validations.dataValidation:
            if rule.type in ('decimal', 'whole'):
                ref = 'B3' if original == 'Report Details' else 'B2'
                converted = ref
                for latin, dz in zip('0123456789', '༠༡༢༣༤༥༦༧༨༩'):
                    converted = f'SUBSTITUTE({converted},"{dz}","{latin}")'
                number = f'VALUE({converted})'
                condition = f'ABS({number}-2050)<=50' if rule.type == 'whole' else f'{number}>0'
                rule.type = 'custom'
                rule.operator = None
                rule.formula1 = f'IFERROR({condition},FALSE)'
                rule.formula2 = None
            if rule.type == 'list':
                options = rule.formula1.strip('"').split(',')
                rule.formula1 = '"' + ','.join(translate(v, 'dz') for v in options) + '"'
                rule.error = translate("Allowed: " + ", ".join(translate(v, "dz") for v in options), "dz")
            rule.errorTitle = translate(rule.errorTitle, 'dz')
            rule.error = translate(rule.error, 'dz')
        ws.title = translate(original, 'dz')


if __name__ == "__main__":
    folder = Path("sample_data")
    folder.mkdir(exist_ok=True)
    from result_analysis.core.subjects_config import STAGES

    selected = tuple(STAGES["Key Stage 1"]["core"])
    for sec in ["A", "B"]:
        (folder / f"section_{sec}_sample.xlsx").write_bytes(
            template(selected, True, sec, seed=ord(sec), grade="PP")
        )
    (folder / "subject_sample.xlsx").write_bytes(template(("English",), True))
