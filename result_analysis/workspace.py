"""Bhutan Result Analysis Tool: Streamlit entry point and sidebar navigation."""

from base64 import b64encode
from functools import lru_cache
from pathlib import Path
import streamlit as st
from result_analysis.core.subjects_config import METHODS
from result_analysis.core.translations import t, LANGUAGES, set_language
from result_analysis.views import individual, class_result, sections
from components.navigation import go


def render():
    ROOT = Path(__file__).resolve().parent


    @lru_cache(maxsize=1)
    def tibetan_style() -> str:
        """Embed the reference app's licensed Tibetan font for browser display."""
        encoded = b64encode((ROOT / "assets/tibetan.woff2").read_bytes()).decode("ascii")
        return (
            "<style>@font-face{font-family:'Result Tibetan';font-display:swap;"
            "unicode-range:U+0F00-0FFF;src:url(data:font/woff2;base64,"
            + encoded
            + ") format('woff2')}"
            ".stApp{font-family:'Source Sans 3','Result Tibetan',sans-serif}</style>"
        )


    st.html(ROOT / "assets/theme.css")
    st.html(tibetan_style())
    if st.session_state.get('lang') == 'dz':
        st.html("<style>.stApp, .stApp button, .stApp input, .stApp label, .stApp p, .stApp h1, .stApp h2, .stApp h3{font-family:'Source Sans 3','Result Tibetan',sans-serif;line-height:1.9}</style>")


    def navigate(page_name: str) -> None:
        """Home cards use the same navigation state as the sidebar."""
        st.session_state["result_navigation"] = page_name


    page = st.session_state.get("result_navigation", "Home")

    if page != "Home":
        st.html('<span class="workspace-compact"></span>')
    with st.container(key="valley_art"):
        st.image(str(ROOT / "static/valley.jpg"), width="stretch")
    with st.container(key="school_header"):
        with st.container(key="classroom_art"):
            st.image(str(ROOT / "static/classroom.jpg"), width="stretch")
        with st.container(
            key="header_tools",
            horizontal=True,
            gap="xsmall",
            horizontal_alignment="right",
            vertical_alignment="center",
        ):
            if st.button(t("Home"), icon=":material/home:", key="nav_home"):
                go("portal")
            with st.popover(t("Language"), icon=":material/language:"):
                for code, label in LANGUAGES.items():
                    st.button(
                        t(label),
                        key="language_" + code,
                        width="stretch",
                        icon=":material/check:"
                        if st.session_state.get("lang", "en") == code
                        else None,
                        on_click=set_language,
                        args=(code,),
                    )
            with st.popover(t("Menu"), icon=":material/menu:"):
                from components.workspace import workspace_links
                workspace_links()
                st.divider()
                for target, label in [
                    ("Home", "Bhutan Result Analysis Tool"),
                    ("Individual Subject Analysis", "Individual subject"),
                    ("Class Result Analysis", "Class results"),
                    ("Section Comparison", "Section comparison"),
                    ("Help/Instructions", "Help / Instructions"),
                    ("Methodology", "Methodology"),
                    ("Session", "Session"),
                    ("Privacy policy", "Privacy policy"),
                ]:
                    st.button(
                        t(label),
                        key="menu_" + target,
                        width="stretch",
                        on_click=navigate,
                        args=(target,),
                    )
        st.markdown(
            t(f'<p class="ia-eyebrow">{t("Assessment workspace")}</p>'
            f'<p class="ia-title">{t("Bhutan Result Analysis Tool")}</p>'
            f'<p class="ia-sub">{t("A clearer picture of learning.")}<br>{t("From your mark sheet to the next lesson.")}</p>'),
            unsafe_allow_html=True,
        )
    metadata = {}
    if page == "Home":
        st.header(t("What would you like to understand?"))
        st.caption(
            t("Choose an analysis to get started. Each workspace includes a matching Excel template and a fictional sample.")
        )
        modules = [
            (
                "subject",
                "01",
                "Individual subject",
                "Look closely at one subject.",
                "Score distribution · Outliers · Group comparisons",
                "Analyse a subject",
                "Individual Subject Analysis",
            ),
            (
                "class",
                "02",
                "Class results",
                "See the whole class, subject by subject.",
                "Pass rates · Subject diagnosis · Student support",
                "Analyse a class",
                "Class Result Analysis",
            ),
            (
                "sections",
                "03",
                "Section comparison",
                "Bring the grade’s results together.",
                "Section rankings · Grade overview · Benchmarks",
                "Compare sections",
                "Section Comparison",
            ),
        ]
        for column, (key, number, title, description, detail, action, target) in zip(
            st.columns(3), modules
        ):
            with column:
                with st.container(border=True, key="module_" + key):
                    st.markdown(
                        t(f'<span class="module-symbol">{number}</span>'),
                        unsafe_allow_html=True,
                    )
                    st.subheader(t(title))
                    st.write(t(description))
                    st.markdown(
                        t(f'<p class="module-detail">{detail}</p>'), unsafe_allow_html=True
                    )
                    st.button(
                        t(action),
                        key="open_" + key,
                        type="primary",
                        width="stretch",
                        on_click=navigate,
                        args=(target,),
                    )
        st.markdown(
            t('<div class="workflow-note"><span><strong>1</strong> Get your template</span>'
            "<span><strong>2</strong> Upload your marks</span><span><strong>3</strong> Review and export</span></div>"),
            unsafe_allow_html=True,
        )
        st.info(
            t("Pass mark: 40% of each subject’s maximum. Blank and Absent marks are excluded per subject and counted separately.")
        )
    elif page == "Individual Subject Analysis":
        individual.render(metadata)
    elif page == "Class Result Analysis":
        class_result.render(metadata)
    elif page == "Section Comparison":
        sections.render(metadata)
    elif page == "Session":
        st.header(t("Session"))
        st.write(
            t("Uploaded workbooks and generated reports remain available during this session.")
        )
        records = st.session_state.get("section_records", {})
        st.write(t(f"Saved sections: {len(records)}"))
        if st.button(t("Clear session data"), type="primary"):
            language = st.session_state.get("lang", "en")
            from components.workspace import clear_result_session
            clear_result_session()
            st.session_state["lang"] = language
            st.session_state["result_navigation"] = "Home"
            st.rerun()
    elif page == "Privacy policy":
        st.header(t("Privacy policy"))
        st.write(
            t("Uploaded files are processed in server memory for your current session. Hosted use sends the workbook to the server; local use processes it on your computer. The app does not intentionally save student records to disk, a database, or an external analytics service.")
        )
        st.write(
            t("Only blank templates and fictional sample files are shared-cache items. Student data and PDF bytes stay in session state. Downloads contain student records. Clear session data removes the app’s session records; closing the browser or restarting the server may require a new upload.")
        )
        st.write(
            t("Name hiding does not anonymize student IDs. Follow your school’s policy when sharing downloaded reports.")
        )
    elif page == "Methodology":
        st.header(t("Methodology"))
        st.write(t(METHODS))
        st.subheader(t("Diagnosis and interpretation"))
        st.write(
            t("Urgent: pass<60% OR mean<45%. Improvement: pass<75% OR mean<55%, after urgent. Doing Well: pass≥90% AND mean≥65%. Remaining assessed combinations are Satisfactory. SD>20 points suggests differentiated teaching; group gaps≥10 points merit investigation. These are descriptive rules, not causal conclusions.")
        )
        st.write(
            t("Score bands represent continuous intervals: 0≤x<40, 40≤x<50, …, 80≤x≤100. PDF charts use the same data as the on-screen analysis. Compact reports prioritize distributions, means, pass rates and comparisons; optional student lists can be included before downloading.")
        )
    else:
        st.header(t("Help / Instructions"))
        st.write(
            t("Choose your analysis and subjects, then download the matching Excel template. Complete School Name and Academic Year in Report Details. Class, Teacher Name and Subjects also belong in the workbook. Keep all Marks and Settings columns in their original order.")
        )
        st.write(
            t("Upload the completed workbook. Section files must have the same school, year, class, subjects and maximum marks. Use the exact section name shown in the upload slot. Select Prepare PDF Report to create a visual report, then Download PDF Report.")
        )
        st.write(
            t("Use Male/Female (M/F accepted), Boarder/Day Scholar (Hostel/Day-scholar accepted), numeric marks, Absent or blank. Student IDs must be unique across sections. No formulas or totals rows. Maximum: 10 MB and 10,000 students per file.")
        )
        st.write(
            t("Dzongkha translation is available throughout the app, templates and reports. Dzongkha mode uses Dzongkha numerals; calculations and student names are preserved.")
        )
        st.write(
            t("Benchmark figures are supplied manually. National inputs appear only for VI, VIII, X and XII. The optional online hook falls back to manual entry; it never invents figures.")
        )
    st.markdown(
        t('<div class="result-footer"><span>Bhutan Result Analysis Tool</span><span>Made for educators in Bhutan</span></div>'),
        unsafe_allow_html=True,
    )


    # Localize labels owned by the framework without changing user-entered data.
    import json
    st.html(
        "<script>" + (ROOT / "assets/native_locale.js").read_text().replace(
            "__LANGUAGE__", json.dumps(st.session_state.get("lang", "en"))
        ) + "</script>",
        unsafe_allow_javascript=True,
    )
