"""Shared entry point and navigation between the two assessment tools."""
import streamlit as st
from utils.translations import t


def workspace_links():
    from components.navigation import PAGES
    for key, label in (("portal", "Choose an analysis"), ("home", "Item analysis"),
                       ("results", "Result analysis")):
        st.page_link(PAGES[key], label=t(label))


def preserve_result_choices():
    # Keep setup choices when the user visits the other workspace. Uploaded
    # workbooks and completed results already live in non-widget state keys.
    prefixes = ("class_stage", "class_class", "class_path", "class_choices", "class_tvet",
                "sections_stage", "sections_class", "sections_path", "sections_choices",
                "sections_tvet", "individual_subject", "individual_maximum")
    for key in list(st.session_state):
        if key.startswith(prefixes):
            st.session_state[key] = st.session_state[key]


def clear_result_session():
    """Clear result-analysis records without removing item-analysis results."""
    prefixes = ("individual_", "class_", "sections_", "section_", "benchmark_", "benchmarks_", "edit_", "remove_")
    for key in list(st.session_state):
        if key.startswith(prefixes) or key == "result_navigation":
            del st.session_state[key]


def render():
    from components.navigation import go
    st.header(t("Choose an analysis"))
    st.caption(t("Start with questions or look at results across subjects and classes."))
    choices = [
        ("home", "Item analysis", "Review questions and responses.",
         "Multiple choice, true or false, fill in the blanks, matching, written responses and score distributions."),
        ("results", "Result analysis", "Understand performance across your school.",
         "Explore a subject, review class results or compare sections using your mark sheets."),
    ]
    for column, (target, title, subtitle, detail) in zip(st.columns(2), choices):
        with column, st.container(border=True, key="workspace_" + target):
            st.subheader(t(title))
            st.write(t(subtitle))
            st.caption(t(detail))
            if st.button(t("Open " + title.lower()), key="open_workspace_" + target,
                         width="stretch", type="primary"):
                go(target)
    st.caption(t("Both tools include Excel templates and PDF reports, in English and Dzongkha."))
