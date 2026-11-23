"""Reusable Streamlit upload, curriculum, chart and report controls."""

from functools import partial
import hashlib
import pickle
import pandas as pd
import streamlit as st
from result_analysis.core.subjects_config import STAGES, resolve_subjects
from result_analysis.core.templates import template
from result_analysis.core.validators import read_marks, ValidatedData
from result_analysis.core.charts import Chart, interactive
from result_analysis.core.pdf_report import Report, build_pdf
from result_analysis.core.translations import t, language, display_frame, translate, styled_frame

WARNING = (
    "Please follow the exact column names and formats of the template. "
    "Do not rename, reorder or delete columns. Files that do not match will be rejected."
)


@st.cache_data(max_entries=24, show_spinner=False)
def cached_template(
    subjects: tuple, sample: bool, section: str, maximum: float, grade: str = "", lang: str = "en"
) -> bytes:
    """Cache public templates with fully localized template instructions, labels, names, classes, sections and numerals; student uploads stay session-local."""
    return template(
        subjects,
        sample,
        section,
        maximum,
        seed=sum(map(ord, section)) or 19,
        grade=grade,
        lang=lang,
    )


def _selection(prefix: str) -> tuple[list[str], str]:
    """Stage → class → pathway → optional subjects, with enforced counts."""
    a, b = st.columns(2)
    stage = a.selectbox(t("Key Stage"), list(STAGES), key=prefix + "_stage", format_func=partial(translate, lang=language()))
    config = STAGES[stage]
    grade = b.selectbox(t("Class"), config["classes"], key=prefix + "_class", format_func=partial(translate, lang=language()))
    pathway, choices, tvet = "", [], ""
    if "pathways" in config:
        pathway = st.selectbox(
            t("Pathway / Stream"), list(config["pathways"]), format_func=partial(translate, lang=language()), key=prefix + "_path"
        )
        path = config["pathways"][pathway]
        if path.get("options"):
            choices = st.multiselect(
                t(f"Optional subjects (choose {path['min']}–{path['max']})"),
                path["options"],
                format_func=partial(translate, lang=language()), key=prefix + "_choices_" + pathway,
            )
        if "TVET" in choices + path["core"]:
            tvet = st.text_input(
                t("School-specific TVET subject name"), key=prefix + "_tvet"
            )
    try:
        subjects = resolve_subjects(stage, pathway, choices, tvet)
    except ValueError as exc:
        st.warning(t(str(exc)))
        return [], grade
    st.caption(t("Subjects: " + ", ".join(t(s) for s in subjects)))
    return subjects, grade


def _uploader(
    subjects: list[str],
    key: str,
    section: str | None = None,
    maximum: float = 100,
    enforce_max: bool = False,
    grade: str = "",
) -> ValidatedData | None:
    """Persist validated bytes/data across navigation and prevent stale results."""
    signature = (tuple(subjects), section, maximum, enforce_max, grade)
    if st.session_state.get(key + "_schema") != signature:
        st.session_state.pop(key + "_data", None)
        st.session_state.pop(key + "_digest", None)
        st.session_state[key + "_schema"] = signature
    a, b = st.columns(2)
    a.download_button(
        t("Download Template"),
        cached_template(tuple(subjects), False, section or "", maximum, grade, language()),
        f"{key}_template.xlsx",
        key=key + "_template",
        on_click="ignore",
    )
    b.download_button(
        t("Download Sample File"),
        cached_template(tuple(subjects), True, section or "", maximum, grade, language()),
        f"{key}_sample.xlsx",
        key=key + "_sample",
        on_click="ignore",
    )
    st.warning(t(WARNING))
    schema_hash = hashlib.sha256(repr(signature).encode()).hexdigest()[:10]
    upload = st.file_uploader(
        t("Upload Excel (.xlsx)"), type=["xlsx"], key=key + "_file_" + schema_hash
    )
    if upload is not None:
        raw = upload.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        if st.session_state.get(key + "_digest") != digest:
            st.session_state.pop(key + "_data", None)
            with st.spinner(t("Validating workbook…")):
                data = read_marks(
                    raw, subjects, section, maximum if enforce_max else None
                )
            st.session_state[key + "_digest"] = digest
            st.session_state[key + "_errors"] = data.errors
            if not data.errors and grade and data.metadata.get("Class") != grade:
                data.errors.append(f"Report Details, Class: expected {grade}.")
                st.session_state[key + "_errors"] = data.errors
            if not data.errors:
                st.session_state[key + "_data"] = data
        for error in st.session_state.get(key + "_errors", []):
            st.error(t(error))
    data = st.session_state.get(key + "_data")
    if data is not None:
        st.caption(
            t(f"{data.metadata.get('School', '')} · {data.metadata.get('Year', '')} · {' | '.join(t(s.strip()) for s in data.metadata.get('Subjects', '').split(' | '))}")
        )
        st.success(
            t(f"Validated {len(data.frame)} students. Data retained for this session.")
        )
        with st.expander(t("Data preview (first 10 rows)")):
            st.dataframe(styled_frame(data.frame.head(10)), hide_index=True, width="stretch")
        excluded = data.frame[subjects].isna().sum()
        st.caption(
            t("Excluded marks per subject: "
            + ", ".join(
                f"{t(s)}: {excluded[s]} ({t("Absent")}: {data.absent[s].sum()})" for s in subjects
            ))
        )
        small = [s for s in subjects if data.frame[s].notna().sum() < 5]
        if small:
            st.warning(
                t("Fewer than 5 valid marks; interpret cautiously: " + ", ".join(t(s) for s in small))
            )
    return data


def metrics(values: dict) -> None:
    """Responsive rows of four metric cards with consistent precision."""
    entries = list(values.items())
    for start in range(0, len(entries), 4):
        for column, (label, value) in zip(st.columns(4), entries[start : start + 4]):
            display = (
                "N/A"
                if pd.isna(value)
                else f"{value:.2f}"
                if isinstance(value, float)
                else str(value)
            )
            column.metric(t(label), t(display))


def table(report: Report, title: str, frame: pd.DataFrame, heat: bool = False) -> None:
    """Display and collect exactly the same table for export."""
    st.subheader(t(title))
    if frame.empty:
        st.info(t("No matching records."))
    else:
        styled = styled_frame(frame)
        if heat:
            columns = [
                c for c in frame.select_dtypes("number") if frame[c].notna().any()
            ]
            if columns:
                styled = styled.background_gradient(cmap="Blues", subset=[t(c) for c in columns])
        st.dataframe(styled, hide_index=True, width="stretch")
    report.tables.append((title, frame))


def chart(report: Report, spec: Chart) -> None:
    """Render a chart and retain its data for the PDF counterpart."""
    st.plotly_chart(interactive(spec), width="stretch", theme=None)
    report.charts.append(spec)


def text(report: Report, message: str) -> None:
    """Show an interpretation and include it in the report."""
    st.write(t(message))
    report.texts.append(message)


def _report_download(report: Report, metadata: dict, key: str) -> None:
    """Cache generated PDFs within this user's session, invalidated by content."""
    report.include_student_lists = st.toggle(
        t("Include selected student lists in PDF"), value=False, key=key + "_pdf_lists"
    )
    metadata = {**metadata, "Language": language()}
    digest = hashlib.sha256(pickle.dumps((report, metadata))).hexdigest()
    state_key = key + "_pdf"
    cached = st.session_state.get(state_key)
    if cached and cached[0] != digest:
        st.session_state.pop(state_key)
        cached = None
    if st.button(t("Prepare PDF Report"), key=key + "_prepare", type="primary"):
        try:
            with st.spinner(t("Rendering report tables and charts…")):
                content = build_pdf(report, metadata)
            st.session_state[state_key] = (digest, content)
            cached = (digest, content)
        except Exception as exc:
            st.error(
                t(f"The PDF could not be generated ({type(exc).__name__}). Check installed dependencies and configured font. Your results remain available.")
            )
    if cached:
        st.download_button(
            t("Download PDF Report"),
            cached[1],
            key + ".pdf",
            "application/pdf",
            key=key + "_download",
            on_click="ignore",
        )
    else:
        st.download_button(
            t("Download PDF Report"),
            b"",
            key + ".pdf",
            disabled=True,
            key=key + "_disabled",
        )


def selection(prefix: str) -> tuple[list[str], str]:
    """Keep curriculum choices together on a readable setup panel."""
    with st.container(border=True, key="setup_panel"):
        st.subheader(t("Set up your class"))
        st.caption(t("Your selections determine the subjects in the template."))
        return _selection(prefix)


def uploader(
    subjects: list[str],
    key: str,
    section: str | None = None,
    maximum: float = 100,
    enforce_max: bool = False,
    grade: str = "",
) -> ValidatedData | None:
    """Present template downloads, file checks and upload status as one task."""
    with st.container(border=True, key="upload_panel"):
        st.subheader(t("Upload your mark sheet"))
        st.caption(
            t("Start with the matching template, or download the fictional sample to explore the analysis.")
        )
        return _uploader(subjects, key, section, maximum, enforce_max, grade)


def report_download(report: Report, metadata: dict, key: str) -> None:
    """Give report preparation a clear destination after the results."""
    with st.container(border=True, key="report_panel"):
        st.subheader(t("Take your analysis to the staff meeting"))
        st.caption(
            t("Prepare a PDF with the visual summary, charts and optional student lists. School, year and subject details come from your uploaded workbook.")
        )
        _report_download(report, metadata, key)
