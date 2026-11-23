"""Presentation-only translations; canonical calculation fields never change."""
import re
from functools import lru_cache
import streamlit as st
from result_analysis.core.locale_dz import MESSAGES, PATTERNS
from result_analysis.core.section_names import section_list
from result_analysis.core.numerals import text_digits, digits, display_number

LANGUAGES = {"en": "English", "dz": "རྫོང་ཁ"}

def language():
    return st.session_state.get("lang", "en")

@lru_cache(maxsize=1)
def _patterns():
    result = []
    for source, target in PATTERNS.items():
        pieces = re.split(r'(\{\d+\})', source)
        expression = ''.join('(.+?)' if re.fullmatch(r'\{\d+\}', p) else re.escape(p) for p in pieces)
        result.append((re.compile(expression, re.DOTALL), target, source))
    result.sort(key=lambda item: len(re.sub(r'\{\d+\}', '', item[2])), reverse=True)
    return result

def _translate_text(value, lang="en"):
    if isinstance(value, str):
        value = {"n": "Number of students", "Assessed n": "Number of assessed students",
                 "Complete n": "Number of students with complete results"}.get(value, value)
    if lang != "dz" or not isinstance(value, str):
        return value
    if value in MESSAGES:
        return MESSAGES[value]
    for pattern, target, source in _patterns():
        match = pattern.fullmatch(value)
        if match:
            # A placeholder must not swallow unrelated sentences in composed prose.
            if any(re.search(r'[.!?]\s+\S|།\s', part) for part in match.groups()) and not source.startswith('Prepared by '):
                continue
            # Names and section labels are literal, even if they match a UI word.
            literal = source.startswith(('Prepared by ', 'Best performing section', 'Benchmark differences', 'Section ', 'Re-upload section', 'Add next section', 'Report Details'))
            values = list(match.groups())
            if source.startswith(('Section ', 'Re-upload section', 'Add next section', 'Best performing section')):
                values[0] = section_list(values[0], lang)
            if source.startswith('Academic year '):
                values[2] = section_list(values[2], lang)
            return target.format(*(v if literal else translate(v, lang) for v in values))
    # HTML markup is owned by the app; translate only its text nodes.
    if '<' in value and '>' in value and re.search(r'</?\w+[ >]', value):
        return re.sub(r'(?<=>)([^<>]+)(?=<)', lambda m: translate(m[0], lang), value)
    stripped = value.strip()
    if stripped != value and stripped in MESSAGES:
        return value.replace(stripped, MESSAGES[stripped])
    # Interpretations are composed of independently translated sentences.
    sentences = re.split(r'(?<=[.!?])\s+', value)
    if len(sentences) > 1:
        return ' '.join(translate(part, lang) for part in sentences)
    if ': ' in value and value.endswith('.'):
        prefix, suffix = value.split(': ', 1)
        if suffix[:-1] in MESSAGES:
            return translate(prefix, lang) + ': ' + MESSAGES[suffix[:-1]]
    return value

def translate(value, lang="en"):
    result = _translate_text(value, lang)
    return text_digits(result, lang) if lang == 'dz' and isinstance(result, str) else result


def styled_frame(frame, lang=None):
    lang = lang or language()
    return display_frame(frame, lang).style.format(lambda v: display_number(v, lang))


def t(value):
    return translate(value, language())

def display_frame(frame, lang=None):
    """Localize labels and enumerations, preserving names, IDs and free text."""
    lang = lang or language()
    result = frame.copy()
    enums = {'Gender','Residence','Diagnosis','Type','Result','Source','Status','Remark','Subject','Reasons and recommendations'}
    for column in result.columns:
        if column in {'Section', 'Best section', 'Weakest section'}:
            result[column] = result[column].map(lambda v: section_list(v, lang))
        elif column in enums:
            result[column] = result[column].map(lambda v: translate(v, lang))
    result.columns = [translate(c, lang) for c in result.columns]
    result.index.name = translate(result.index.name, lang)
    result.columns.name = translate(result.columns.name, lang)
    return result

def set_language(code):
    st.session_state['lang'] = code
