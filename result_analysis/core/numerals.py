"""Dzongkha digit presentation and input normalization, without changing values."""
import math
import numbers
import re

DZ_DIGITS = str.maketrans('0123456789', '༠༡༢༣༤༥༦༧༨༩')
LATIN_DIGITS = str.maketrans('༠༡༢༣༤༥༦༧༨༩', '0123456789')

def digits(value, lang='dz'):
    return str(value).translate(DZ_DIGITS) if lang == 'dz' else str(value)

def ascii_digits(value):
    return value.translate(LATIN_DIGITS) if isinstance(value, str) else value

def text_digits(value, lang='dz'):
    """Keep HTML attributes and Plotly expressions executable."""
    return ''.join(part if re.fullmatch(r'%\{[^}]*\}|</?[A-Za-z][^>]*>', part) else digits(part,lang)
                   for part in re.split(r'(%\{[^}]*\}|</?[A-Za-z][^>]*>)', value))

def display_number(value, lang='en', precision=2):
    if value is None:
        return ''
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, numbers.Number):
        if not math.isfinite(float(value)):
            return 'མི་འཇུག' if lang == 'dz' else 'N/A'
        return digits(f'{value:.{precision}f}',lang)
    return digits(value,lang)
