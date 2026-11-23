"""Bhutan-local report dates with Dzongkha ordinal month names."""
from result_analysis.core.numerals import digits

MONTH_ORDINALS = ('དང་པ', 'གཉིས་པ', 'གསུམ་པ', 'བཞི་པ', 'ལྔ་པ', 'དྲུག་པ',
                  'བདུན་པ', 'བརྒྱད་པ', 'དགུ་པ', 'བཅུ་པ', 'བཅུ་གཅིག་པ', 'བཅུ་གཉིས་པ')

def report_date(value, lang='en'):
    if lang == 'dz':
        return digits(f'{value.day} སྤྱི་ཟླ་{MONTH_ORDINALS[value.month - 1]} {value.year}')
    return value.strftime('%d %b %Y')
