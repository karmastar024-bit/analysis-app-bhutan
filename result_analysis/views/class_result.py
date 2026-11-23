"""Class and whole-grade analysis components."""

from result_analysis.core.translations import t, display_frame, styled_frame

import pandas as pd
import streamlit as st
from result_analysis.core.stats import (
    percentages,
    subject_stats,
    student_results,
    class_overview,
    comparisons,
    comparison_text,
    diagnosis,
)
from result_analysis.core.charts import Chart
from result_analysis.core.pdf_report import Report
from result_analysis.views.common import (
    selection,
    uploader,
    metrics,
    table,
    chart,
    text,
    report_download,
)


def group_results(
    frame: pd.DataFrame, pct: pd.DataFrame, report: Report, overall: bool = False
) -> None:
    """Group means and pass rates, with per-subject exclusions and denominators."""
    for group in ["Gender", "Residence"]:
        data = pct.copy()
        if overall:
            data["Overall average"] = pct.mean(axis=1)
        comp = comparisons(frame, data, group)
        table(report, group + " statistics", comp)
        for metric in ["Mean", "Pass %"]:
            chart(
                report,
                Chart(
                    f"{group}: {metric} by subject",
                    "bar",
                    comp,
                    "Subject",
                    metric,
                    group,
                ),
            )
        for subject in data:
            text(report, comparison_text(comp, group, subject))
        if (comp["n"] < 5).any():
            st.warning(
                t(f"Some {group.lower()} comparison groups have fewer than 5 valid marks.")
            )
        if overall:
            text(
                report,
                "Overall group pass % measures available student averages ≥40%; it is distinct from passing all subjects.",
            )


def class_content(
    frame: pd.DataFrame,
    maxima: dict,
    report: Report,
    key: str,
    whole_grade: bool = False,
) -> None:
    """Collect all class outputs for either the class or combined-grade report."""
    pct = percentages(frame, maxima)
    results = student_results(frame, maxima)
    overview = class_overview(results)
    overview_values = {
        k: overview[k]
        for k in [
            "Students",
            "Assessed n",
            "Complete n",
            "Mean",
            "Passed all %",
            "Passed any %",
            "Average total marks",
            "Failing 1",
            "Failing 2",
            "Failing 3+",
        ]
    }
    metrics(overview_values)
    text(
        report,
        f"Passed all denominator: {overview['Complete n']} complete records. "
        f"Passed any denominator: {overview['Assessed n']} students with at least one valid mark. "
        "Available subject averages contribute to class mean; totals and rankings require complete records. "
        "Failure counts count observed failures, including students with other missing marks.",
    )
    table(report, "Class overview", pd.DataFrame([overview_values]))
    stats = subject_stats(pct)
    tabs = st.tabs(
        [t(label) for label in [
            "Subject statistics",
            "Charts",
            "Group comparisons",
            "Diagnosis",
            "Student support",
        ]]
    )
    with tabs[0]:
        table(report, "Per-subject statistics (%)", stats, heat=True)
        small = stats.loc[stats["n"] < 5, "Subject"].tolist()
        if small:
            st.warning(t("Small samples (fewer than 5 students): " + ", ".join(small)))
    with tabs[1]:
        chart(
            report,
            Chart(
                "Mean percentage by subject",
                "bar",
                stats,
                "Subject",
                "Mean",
                pass_line=True,
            ),
        )
        chart(
            report,
            Chart("Pass percentage by subject", "bar", stats, "Subject", "Pass %"),
        )
        long = pct.melt(var_name="Subject", value_name="Score %")
        chart(
            report, Chart("Score spread by subject", "box", long, "Subject", "Score %")
        )
    with tabs[2]:
        group_results(frame, pct, report, whole_grade)
    with tabs[3]:
        diagnosed = diagnosis(frame, pct)
        st.caption(
            t("Subject strength = 50% mean + 50% pass rate. Thresholds are configurable in core/subjects_config.py.")
        )
        colors = {
            "Needs Urgent Attention": "#8c2532",
            "Needs Improvement": "#86531e",
            "Satisfactory": "#236789",
            "Doing Well": "#247454",
            "No data": "#555555",
        }
        st.dataframe(
            styled_frame(diagnosed).map(
                lambda v: "background-color: " + {t(k): c for k, c in colors.items()}[v] + "; color: white",
                subset=[t("Diagnosis")],
            ),
            hide_index=True,
            width="stretch",
        )
        report.tables.append(("Subject diagnosis and strength ranking", diagnosed))
        for _, row in diagnosed.iterrows():
            text(
                report,
                f"{row.Subject}: {row['Diagnosis']}. {row['Reasons and recommendations']}",
            )
    with tabs[4]:
        hide = st.toggle(t("Hide student names"), value=True, key=key + "_hide")
        display = results.drop(columns=["Student Name"]) if hide else results
        top = display[display.Rank.le(10)].sort_values(["Rank", "Student ID"])
        table(report, "Top 10 rank positions (ties included)", top)
        if st.toggle(t("Show students needing support"), key=key + "_support"):
            mask = results["Failed subjects"].ge(2) | results["Borderline subjects"].gt(
                0
            )
            table(report, "Students needing support", display[mask])
        table(
            report,
            "Incomplete records for follow-up",
            display[display["Excluded subjects"].gt(0)],
        )


def render(metadata: dict) -> None:
    """Single class upload and complete report."""
    st.header(t("Class Result Analysis"))
    subjects, grade = selection("class")
    if not subjects:
        return
    data = uploader(subjects, "class", grade=grade)
    if data is None:
        return
    metadata = data.metadata
    report = Report(f"Class {grade}: result analysis")
    class_content(data.frame, data.maxima, report, "class")
    report_download(
        report, {**metadata, "Class": grade, "Section": "All uploaded"}, "class"
    )
