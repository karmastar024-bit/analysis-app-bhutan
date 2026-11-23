"""Language changes preserve calculations, student identities and workbook safety."""
from io import BytesIO
import pandas as pd
import pytest
from openpyxl import load_workbook
from result_analysis.core.templates import template
from result_analysis.core.validators import read_marks
from result_analysis.core.translations import translate, display_frame
from result_analysis.core.subjects_config import STAGES

@pytest.mark.parametrize('subjects', [('English',),tuple(STAGES['Key Stage 1']['core'])])
def test_translated_workbook_round_trip(subjects):
    en=read_marks(template(subjects,True,'A',grade='PP'),list(subjects),'A')
    dz=read_marks(template(subjects,True,'A',grade='PP',lang='dz'),list(subjects),'A')
    assert not en.errors and not dz.errors
    pd.testing.assert_frame_equal(en.frame.drop(columns=['Student Name']),dz.frame.drop(columns=['Student Name']))
    assert all(any('\u0f00' <= c <= '\u0fff' for c in name) and 'Sample' not in name for name in dz.frame['Student Name'])
    assert en.maxima == dz.maxima
    pd.testing.assert_frame_equal(en.absent,dz.absent)
    book=load_workbook(BytesIO(template(subjects,True,'A',lang='dz')))
    assert translate('Marks','dz') in book.sheetnames
    ws=book[translate('Marks','dz')]
    assert ws['A1'].value == translate('Student ID','dz')
    assert ws['A2'].value == 'A-༠༠༡'
    assert ws['F4'].value == translate('Absent','dz')
    assert ws['C2'].value == translate('Female','dz')
    assert translate('Female','dz') in next(iter(ws.data_validations.dataValidation)).formula1
    assert all(c.value != 'AB' for sheet in book for row in sheet for c in row)
    assert ws.protection.sheet and not ws['F2'].protection.locked


def test_display_preserves_student_text_and_numerals():
    frame=pd.DataFrame({'Student Name':['English','Male'],'Student ID':['001','002'],'Gender':['Male','Female'],'Mean':[40.25,0]})
    result=display_frame(frame,'dz')
    assert result[translate('Student Name','dz')].tolist() == ['English','Male']
    assert result[translate('Student ID','dz')].tolist() == ['001','002']
    assert result[translate('Mean','dz')].tolist() == [40.25,0]
    assert translate('Validated 32 students. Data retained for this session.','dz') != 'Validated 32 students. Data retained for this session.'
    assert translate('n') == 'Number of students'
    assert translate('n', 'dz') == 'སློབ་ཕྲུག་གྱངས་ཁ།'
    assert 'Class' not in translate('Class PP: section comparison', 'dz')
    assert 'section' not in translate('Class PP: section comparison', 'dz')
    assert '༣༢' in translate('Validated 32 students. Data retained for this session.','dz')


def test_language_switch_keeps_results():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file('app.py',default_timeout=40).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    app.button(key='menu_Class Result Analysis').click().run()
    subjects=STAGES['Key Stage 1']['core']
    app.session_state['class_data']=read_marks(template(tuple(subjects),True,grade='PP',lang='dz'),subjects)
    app.run()
    english=[m.value for m in app.metric]
    app.button(key='language_dz').click().run()
    assert not app.exception
    from result_analysis.core.numerals import digits
    assert [m.value for m in app.metric] == [digits(v) for v in english]
    assert all(m.label != 'Mean' for m in app.metric)
    app.button(key='language_en').click().run()
    assert not app.exception and [m.value for m in app.metric] == english


def test_dzongkha_section_sequence_and_upload():
    from result_analysis.core.section_names import section_label, display_section, canonical_section
    assert [section_label(i, 'dz') for i in range(5)] == ['ཀ', 'ཁ', 'ག', 'ང', 'ཅ']
    assert section_label(29, 'dz') == 'ཨ'
    assert section_label(30, 'dz') == 'ཀཀ'
    assert display_section('A', 'dz') == 'ཀ'
    assert display_section('B', 'dz') == 'ཁ'
    assert canonical_section('ཀ་') == 'A'
    assert display_section('Blue', 'dz') == 'Blue'
    raw = template(('English',), True, 'B', lang='dz')
    book = load_workbook(BytesIO(raw))
    assert book[translate('Marks', 'dz')]['E2'].value == 'ཁ'
    data = read_marks(raw, ['English'], 'B')
    assert not data.errors
    assert data.frame.Section.eq('B').all()


def test_section_field_switches_alphabets():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file('app.py', default_timeout=40).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    app.button(key='menu_Section Comparison').click().run()
    assert next(w for w in app.text_input if w.label == 'Section name').value == 'A'
    app.button(key='language_dz').click().run()
    assert not app.exception
    assert next(w for w in app.text_input if w.label == translate('Section name', 'dz')).value == 'ཀ'
    assert any('ཀ' in h.value for h in app.subheader)
    app.button(key='language_en').click().run()
    assert not app.exception
    assert next(w for w in app.text_input if w.label == 'Section name').value == 'A'


def test_dzongkha_numerals_preserve_numeric_values():
    from result_analysis.core.numerals import digits, ascii_digits
    from result_analysis.core.translations import styled_frame
    assert digits('0123456789') == '༠༡༢༣༤༥༦༧༨༩'
    assert ascii_digits('༤༠.༢༥') == '40.25'
    frame = pd.DataFrame({'Mean': [40.25, 0.0]})
    styled = styled_frame(frame, 'dz')
    assert '༤༠.༢༥' in styled.to_html()
    assert styled.data.iloc[0, 0] == 40.25
    source = template(('English 2',), True, 'A', maximum=50, grade='VI', lang='dz')
    data = read_marks(source, ['English 2'], 'A', 50)
    assert not data.errors
    assert data.maxima == {'English 2': 50.0}
    assert data.metadata['Class'] == 'VI'
    book = load_workbook(BytesIO(source))
    assert book[translate('Report Details','dz')]['B3'].value == '༢༠༢༦'
    assert book[translate('Settings','dz')]['B2'].value == '༥༠'
    assert all(len(rule.formula1 or '') <= 255 for ws in book for rule in ws.data_validations.dataValidation)


def test_dzongkha_maximum_input():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file('app.py', default_timeout=40).run()
    app.button(key="open_workspace_results").click().run()
    from components.navigation import PAGES
    app._page_hash = PAGES["results"]._script_hash  # AppTest does not retain switch_page routing.
    app.button(key='menu_Individual Subject Analysis').click().run()
    app.button(key='language_dz').click().run()
    assert not app.exception
    app.text_input(key='individual_maximum_dz').set_value('༥༠').run()
    assert not app.exception
    assert app.session_state['individual_maximum'] == 50.0
    app.button(key='language_en').click().run()
    assert not app.exception
    assert app.number_input(key='individual_maximum').value == 50.0


def test_all_month_names_and_catalogue_use_dzongkha():
    from result_analysis.core.dates import report_date, MONTH_ORDINALS
    from result_analysis.core.locale_dz import MESSAGES, PATTERNS
    from datetime import datetime
    import re
    for month, ordinal in enumerate(MONTH_ORDINALS, 1):
        text = report_date(datetime(2026, month, 23), 'dz')
        assert 'སྤྱི་ཟླ་' + ordinal in text
        assert not re.search('[A-Za-z0-9]', text)
    assert report_date(datetime(2026, 11, 23), 'en') == '23 Nov 2026'
    for text in [*MESSAGES.values(), *PATTERNS.values()]:
        visible = re.sub(r'%\{[^}]*\}|</?[A-Za-z][^>]*>', '', text)
        assert not re.search('[A-Za-z]', visible), text


def test_composed_diagnoses_are_fully_translated():
    from result_analysis.core.stats import diagnosis, percentages
    import re
    subjects = list(STAGES['Key Stage 1']['core'])
    data = read_marks(template(tuple(subjects), True, lang='dz'), subjects)
    for _, row in diagnosis(data.frame, percentages(data.frame, data.maxima)).iterrows():
        text = f"{row.Subject}: {row['Diagnosis']}. {row['Reasons and recommendations']}"
        assert not re.search('[A-Za-z]', translate(text, 'dz')), translate(text, 'dz')
