"""Headless UI smoke tests with validated fictional uploads in session state."""

from streamlit.testing.v1 import AppTest
from result_analysis.core.templates import template
from result_analysis.core.validators import read_marks
from result_analysis.core.subjects_config import STAGES


def navigate(app, page):
    """Use the same menu and Home controls available to teachers."""
    key = "menu_" + page
    app.button(key=key).click().run()


def test_navigation_pages():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    for page in [
        "Individual Subject Analysis",
        "Class Result Analysis",
        "Section Comparison",
        "Help/Instructions",
        "Home",
    ]:
        navigate(app, page)
        assert not app.exception


def test_individual_and_class_results_persist():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    navigate(app, "Individual Subject Analysis")
    app.session_state["individual_data"] = read_marks(
        template(("English",), True), ["English"]
    )
    app.run()
    assert not app.exception
    assert any(m.label == "Pass %" for m in app.metric)
    navigate(app, "Class Result Analysis")
    subjects = STAGES["Key Stage 1"]["core"]
    app.session_state["class_data"] = read_marks(
        template(tuple(subjects), True), subjects
    )
    app.run()
    assert not app.exception
    assert any(m.label == "Passed all %" for m in app.metric)
    navigate(app, "Individual Subject Analysis")
    assert not app.exception
    assert any(m.label == "Pass %" for m in app.metric)


def test_sections_and_benchmarks():
    app = AppTest.from_file("app.py", default_timeout=40).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    navigate(app, "Section Comparison")
    subjects = STAGES["Key Stage 1"]["core"]
    app.session_state["section_records"] = {
        s: read_marks(template(tuple(subjects), True, s), subjects, s)
        for s in ["A", "B"]
    }
    app.session_state["section_finished"] = True
    app.run()
    assert not app.exception
    assert any(m.label == "Passed all %" for m in app.metric)
    assert not any(b.label == "Try fetch from online source" for b in app.button)


def test_remove_reupload_and_national_visibility():
    app = AppTest.from_file("app.py", default_timeout=40).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    navigate(app, "Section Comparison")
    next(s for s in app.selectbox if s.label == "Key Stage").set_value(
        "Key Stage 2"
    ).run()
    next(s for s in app.selectbox if s.label == "Class").set_value("VI").run()
    subjects = STAGES["Key Stage 2"]["core"]
    app.session_state["section_records"] = {
        s: read_marks(template(tuple(subjects), True, s), subjects, s)
        for s in ["A", "B"]
    }
    app.session_state["section_finished"] = True
    app.run()
    assert any(b.label == "Try fetch from online source" for b in app.button)
    next(b for b in app.button if b.label == "Re-upload").click().run()
    assert app.session_state["section_edit"] == "A"
    assert not app.session_state["section_finished"]
    next(b for b in app.button if b.label == "Cancel re-upload").click().run()
    next(b for b in app.button if b.key == "remove_B").click().run()
    assert len(app.session_state["section_records"]) == 1
    assert next(
        b for b in app.button if b.label == "Finish uploading & Analyse"
    ).disabled
    assert not app.exception


def test_subject_settings_survive_navigation():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    navigate(app, "Individual Subject Analysis")
    next(w for w in app.text_input if w.label == "Subject name").set_value(
        "Mathematics"
    ).run()
    next(w for w in app.number_input if w.label == "Maximum marks").set_value(50).run()
    navigate(app, "Home")
    navigate(app, "Individual Subject Analysis")
    assert (
        next(w for w in app.text_input if w.label == "Subject name").value
        == "Mathematics"
    )
    assert next(w for w in app.number_input if w.label == "Maximum marks").value == 50


def test_header_controls_and_language():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    assert len(app.sidebar.text_input) == 0
    app.button(key="language_dz").click().run()
    assert app.session_state["lang"] == "dz"
    assert app.button(key="nav_home").label != "Home"
    app.button(key="menu_Privacy policy").click().run()
    assert app.session_state["result_navigation"] == "Privacy policy"
    app.button(key="language_en").click().run()
    assert app.button(key="nav_home").label == "Home"
    assert not app.exception
