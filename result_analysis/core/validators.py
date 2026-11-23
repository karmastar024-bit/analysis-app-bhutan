"""Strict workbook validation with original Excel row numbers."""

from dataclasses import dataclass, field
from io import BytesIO
import math
from zipfile import BadZipFile, ZipFile
import pandas as pd
from openpyxl import load_workbook
from result_analysis.core.subjects_config import IDENTITY
from result_analysis.core.locale_dz import MESSAGES
from result_analysis.core.section_names import canonical_section
from result_analysis.core.numerals import ascii_digits


@dataclass
class ValidatedData:
    """Validated records and separate absence flags, retained only in session memory."""

    frame: pd.DataFrame
    maxima: dict[str, float]
    absent: pd.DataFrame
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


def canonical(value):
    """Accept translated structural labels without touching student-entered text."""
    if not isinstance(value, str):
        return value
    return next((en for en, dz in MESSAGES.items() if dz == value.strip()), value)


def normalized(value: object) -> str:
    """Normalize headers and categorical values without changing student names."""
    return str(ascii_digits(canonical(value)) or "").strip().casefold()


def read_marks(
    raw: bytes,
    subjects: list[str],
    required_section: str | None = None,
    expected_max: float | None = None,
) -> ValidatedData:
    """Reject reordered/extra columns, formulas, invalid identities and invalid marks."""
    errors: list[str] = []
    empty = ValidatedData(pd.DataFrame(), {}, pd.DataFrame(), errors)
    try:
        if len(raw) > 10 * 1024 * 1024:
            raise ValueError("File exceeds 10 MB.")
        with ZipFile(BytesIO(raw)) as archive:
            if sum(f.file_size for f in archive.infolist()) > 80 * 1024 * 1024:
                raise ValueError("Workbook expands beyond the 80 MB safety limit.")
        book = load_workbook(BytesIO(raw), read_only=True, data_only=False)
        # Rename sheet structures only. Names, IDs and other free text stay literal.
        for sheet in book:
            sheet.title = canonical(sheet.title)
        if not {"Marks", "Settings", "Report Details"}.issubset(book.sheetnames):
            raise ValueError(
                "Required worksheets: Marks, Settings and Report Details. Download a new template."
            )
        detail_rows = list(book["Report Details"].iter_rows(values_only=True))
        fields = ["School Name", "Academic Year", "Class", "Teacher Name", "Subjects"]
        if (
            not detail_rows
            or len(detail_rows[0]) != 2
            or [normalized(v) for v in detail_rows[0]] != ["field", "value"]
            or [
                normalized(r[0])
                for r in detail_rows[1:]
                if any(v is not None for v in r)
            ]
            != [normalized(f) for f in fields]
        ):
            raise ValueError(
                "Report Details: keep the Field/Value columns and all five original fields in order."
            )
        details = dict(zip(fields, [r[1] for r in detail_rows[1:6]]))
        school = details["School Name"]
        if not isinstance(school, str) or not school.strip() or school.startswith("="):
            errors.append(
                "Report Details row 2, School Name: enter the school name as text."
            )
        try:
            year = float(details["Academic Year"])
            if (
                isinstance(details["Academic Year"], bool)
                or not 2000 <= year <= 2100
                or not year.is_integer()
            ):
                raise ValueError
        except (TypeError, ValueError):
            errors.append(
                "Report Details row 3, Academic Year: enter a whole year from 2000 to 2100."
            )
            year = 0
        for label in ["Class", "Teacher Name", "Subjects"]:
            if isinstance(details[label], str) and details[label].startswith("="):
                errors.append(f"Report Details, {label}: formulas are not accepted.")
        if normalized(" | ".join(str(canonical(v.strip())) for v in str(details["Subjects"]).split(" | "))) != normalized(" | ".join(subjects)):
            errors.append(
                "Report Details row 6, Subjects: must match Settings and Marks subjects."
            )
        if errors:
            return empty
        metadata = {
            "School": school.strip(),
            "Year": str(int(year)),
            "Class": str(canonical(details["Class"]) or "").strip(),
            "Teacher": str(details["Teacher Name"] or "").strip(),
            "Subjects": " | ".join(subjects),
        }
        ws = book["Marks"]
        if ws.max_row > 10001 or ws.max_column > 50:
            raise ValueError("Maximum supported size: 10,000 students and 50 columns.")
        rows = list(ws.iter_rows(values_only=True))
        expected = IDENTITY + subjects
        if not rows or [normalized(v) for v in rows[0]] != [
            normalized(v) for v in expected
        ]:
            raise ValueError(
                "Marks row 1: columns must match this exact order: "
                + ", ".join(expected)
            )
        setting_rows = list(book["Settings"].iter_rows(values_only=True))
        if not setting_rows or [normalized(x) for x in setting_rows[0]] != [
            "subject",
            "max marks",
        ]:
            raise ValueError("Settings row 1 must contain Subject, Max Marks.")
        supplied = [r for r in setting_rows[1:] if any(x is not None for x in r)]
        if [normalized(r[0]) for r in supplied] != [normalized(s) for s in subjects]:
            raise ValueError(
                "Settings subjects must match the selected subjects in order."
            )
        maxima = {}
        for row_no, (subject, row) in enumerate(zip(subjects, supplied), 2):
            value = row[1]
            if isinstance(value, str) and any(c in '༠༡༢༣༤༥༦༧༨༩' for c in value):
                try:
                    value = float(ascii_digits(value))
                except ValueError:
                    pass
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                errors.append(
                    f"Settings row {row_no}, column Max Marks: enter a positive number."
                )
            else:
                maxima[subject] = float(value)
        if (
            expected_max is not None
            and maxima
            and any(v != expected_max for v in maxima.values())
        ):
            errors.append(
                f"Settings: maximum must match the selected maximum {expected_max:g}."
            )
        if errors:
            return empty
        data, row_numbers = [], []
        for row_no, row in enumerate(rows[1:], 2):
            if all(v is None or str(v).strip() == "" for v in row):
                continue
            data.append(list(row))
            row_numbers.append(row_no)
        if not data:
            raise ValueError("Marks contains no student records.")
        frame = pd.DataFrame(data, columns=expected).astype({s: object for s in subjects})
        absent = pd.DataFrame(False, index=frame.index, columns=subjects)
        seen: set[str] = set()
        gender = {"male": "Male", "m": "Male", "female": "Female", "f": "Female"}
        residence = {
            "boarder": "Boarder",
            "hostel": "Boarder",
            "day scholar": "Day Scholar",
            "day-scholar": "Day Scholar",
            "dayscholar": "Day Scholar",
        }
        for i, row_no in enumerate(row_numbers):
            name_value = frame.at[i, "Student Name"]
            if pd.notna(name_value) and not isinstance(name_value, str):
                errors.append(f"Row {row_no}, column Student Name: expected text.")
            for column in expected:
                value = frame.at[i, column]
                if isinstance(value, str) and value.startswith("="):
                    errors.append(
                        f"Row {row_no}, column {column}: formulas are not accepted; paste values."
                    )
            for column in IDENTITY:
                v = frame.at[i, column]
                frame.at[i, column] = "" if pd.isna(v) else str(v).strip()
            for column in ["Student ID", "Student Name"]:
                if not frame.at[i, column]:
                    errors.append(f"Row {row_no}, column {column}: value is required.")
            frame.at[i, "Student ID"] = ascii_digits(frame.at[i, "Student ID"])
            sid = frame.at[i, "Student ID"].casefold()
            if sid in seen:
                errors.append(
                    f"Row {row_no}, column Student ID: duplicate ID {frame.at[i, 'Student ID']}."
                )
            seen.add(sid)
            for column, mapping in [("Gender", gender), ("Residence", residence)]:
                key = normalized(frame.at[i, column])
                if key not in mapping:
                    errors.append(
                        f"Row {row_no}, column {column}: allowed values are {', '.join(dict.fromkeys(mapping.values()))}."
                    )
                else:
                    frame.at[i, column] = mapping[key]
            if required_section is not None:
                if normalized(canonical_section(frame.at[i, "Section"])) != normalized(canonical_section(required_section)):
                    errors.append(
                        f"Row {row_no}, column Section: expected {required_section}."
                    )
                else:
                    frame.at[i, "Section"] = canonical_section(required_section)
            for subject in subjects:
                value = frame.at[i, subject]
                if pd.isna(value) or str(value).strip() == "":
                    frame.at[i, subject] = float("nan")
                elif normalized(value) in {"ab", "absent", "ཆད་མི", "ཆད་མི།"}:
                    absent.at[i, subject] = True
                    frame.at[i, subject] = float("nan")
                else:
                    try:
                        number = float(ascii_digits(value))
                        if isinstance(value, bool) or not math.isfinite(number):
                            raise ValueError
                        if number < 0:
                            errors.append(
                                f"Row {row_no}, column {subject}: value {number:g} is below 0."
                            )
                        elif number > maxima[subject]:
                            errors.append(
                                f"Row {row_no}, column {subject}: value {number:g} exceeds maximum {maxima[subject]:g}."
                            )
                        frame.at[i, subject] = number
                    except (TypeError, ValueError):
                        errors.append(
                            f"Row {row_no}, column {subject}: expected a numeric mark, blank, or Absent; found {value!r}."
                        )
        book.close()
        if errors:
            return empty
        frame[subjects] = frame[subjects].astype(float)
        return ValidatedData(frame, maxima, absent, metadata=metadata)
    except (ValueError, BadZipFile, KeyError, OSError, TypeError) as exc:
        errors.append(str(exc))
        return empty
    except Exception:
        errors.append(
            "Cannot read this workbook. Use an unencrypted .xlsx file created from the template."
        )
        return empty


def check_section_compatibility(
    candidate: ValidatedData, others: dict[str, ValidatedData]
) -> list[str]:
    """Reject conflicting scales or duplicate IDs across the grade."""
    errors = []
    for name, other in others.items():
        for field in ["School", "Year", "Class"]:
            if normalized(candidate.metadata.get(field)) != normalized(
                other.metadata.get(field)
            ):
                errors.append(f"Report Details {field} differs from section {name}.")
        if candidate.maxima != other.maxima:
            errors.append(f"Subjects or maximum marks differ from section {name}.")
        duplicate = set(candidate.frame["Student ID"].str.casefold()) & set(
            other.frame["Student ID"].str.casefold()
        )
        if duplicate:
            errors.append(
                f"Student IDs already present in section {name}: {', '.join(sorted(duplicate))}."
            )
    return errors
