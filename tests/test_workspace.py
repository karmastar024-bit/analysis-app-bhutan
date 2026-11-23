"""Integration checks for the shared entry point and session boundaries."""
from streamlit.testing.v1 import AppTest
from result_analysis.core.templates import template
from result_analysis.core.validators import read_marks


def test_workspace_switch_and_shared_language():
    app = AppTest.from_file('app.py', default_timeout=45).run()
    assert not app.exception
    app.button(key='open_workspace_results').click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES['results']._script_hash
    app.button(key='open_subject').click().run()
    app.session_state['individual_data'] = read_marks(template(('English',), True), ['English'])
    app.run()
    assert any(m.label == 'Pass %' for m in app.metric)
    # Resolve the registered pages to exercise the same links as the menus.
    from components.navigation import PAGES
    app._page_hash = PAGES['home']._script_hash
    app.run()
    assert not app.exception
    assert any('Choose a test item' in h.value for h in app.header)
    app.button(key='language_dz').click().run()
    app._page_hash = PAGES['results']._script_hash
    app.run()
    assert app.session_state['lang'] == 'dz'
    assert not app.exception
    assert app.session_state['individual_data'] is not None
    app._page_hash = PAGES['portal']._script_hash
    app.run()
    assert not app.exception
    assert app.button(key='open_workspace_results').label != 'Open result analysis'


def test_clear_result_session_preserves_item_results():
    app = AppTest.from_file('app.py', default_timeout=45).run()
    app.button(key='open_workspace_results').click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES['results']._script_hash
    app.session_state['tf_results'] = {'retained': True}
    app.session_state['individual_data'] = 'test record'
    app.session_state['section_records'] = {'A': 'test record'}
    app.button(key='menu_Session').click().run()
    next(b for b in app.button if b.label == 'Clear session data').click().run()
    assert not app.exception
    assert app.session_state['tf_results'] == {'retained': True}
    assert 'individual_data' not in app.session_state
    assert 'section_records' not in app.session_state
