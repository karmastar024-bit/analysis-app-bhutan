"""End-to-end report capture from each real UI, including the full chart set."""

from io import BytesIO
from unittest.mock import patch
from pathlib import Path
import pandas as pd
import pytest
from pypdf import PdfReader
from streamlit.testing.v1 import AppTest
from result_analysis.core.templates import template
from result_analysis.core.validators import read_marks
from result_analysis.core.subjects_config import STAGES
from result_analysis.core.pdf_report import build_pdf, selected_charts
from result_analysis.core.translations import translate


def navigate(app, page):
    """Use the same menu and Home controls available to teachers."""
    key = "nav_home" if page == "Home" else "menu_" + page
    app.button(key=key).click().run()


@pytest.mark.parametrize("lang", ["en", "dz"])
@pytest.mark.parametrize("module", ["individual", "class", "sections"])
def test_complete_module_pdf(module, tmp_path, lang):
    """Render precisely what the module passes to its PDF button."""
    names = {
        "individual": "Individual Subject Analysis",
        "class": "Class Result Analysis",
        "sections": "Section Comparison",
    }
    app = AppTest.from_file("app.py", default_timeout=60).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    navigate(app, names[module])
    subjects = ["English"] if module == "individual" else STAGES["Key Stage 1"]["core"]
    if module == "sections":
        app.session_state["section_records"] = {
            s: read_marks(template(tuple(subjects), True, s), subjects, s)
            for s in ["A", "B"]
        }
        app.session_state["section_finished"] = True
    else:
        app.session_state[module + "_data"] = read_marks(
            template(tuple(subjects), True), subjects
        )
    if lang == "dz":
        app.button(key="language_dz").click()
    app.run()
    captured = []

    def capture(report, metadata):
        captured.append((report, metadata))
        return b"%PDF-test"

    with patch("result_analysis.views.common.build_pdf", capture):
        next(b for b in app.button if b.label == translate("Prepare PDF Report", lang)).click().run()
    assert not app.exception
    assert captured
    report, metadata = captured[0]
    assert all(c.y in ('Mean', 'Pass %') for c in report.charts if c.group in ('Gender', 'Residence'))
    output = build_pdf(report, metadata)
    reader = PdfReader(BytesIO(output))
    assert sum(len(page.images) for page in reader.pages) == len(
        selected_charts(report)
    )
    assert len(report.charts) >= (
        7 if module == "individual" else 7 if module == "class" else 15
    )
    # QA outputs are fictional only and ignored by source control.
    folder = tmp_path / "pdfs"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{module}_{lang}.pdf").write_bytes(output)
    for i, page in enumerate(reader.pages):
        if lang == "en":
            assert f"Page {i + 1}" in page.extract_text()
        else:
            assert metadata['Language'] == 'dz'
            assert '༢༠༢༦' in ''.join(page.extract_text().split())
