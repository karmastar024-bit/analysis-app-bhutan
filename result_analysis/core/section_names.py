"""Language-specific automatic section labels with stable workbook identities."""
import re

DZ_ALPHABET = tuple('ཀཁགངཅཆཇཉཏཐདནཔཕབམཙཚཛཝཞཟའཡརལཤསཧཨ')

def _encode(index, alphabet):
    result = ''
    index += 1
    while index:
        index, digit = divmod(index - 1, len(alphabet))
        result = alphabet[digit] + result
    return result

def _index(label, alphabet):
    result = 0
    for char in label:
        result = result * len(alphabet) + alphabet.index(char) + 1
    return result - 1

def section_label(index, lang='en'):
    if index < 0:
        raise ValueError('Section index must be nonnegative.')
    return _encode(index, DZ_ALPHABET if lang == 'dz' else tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))

def canonical_section(name):
    """Map automatic Tibetan labels to English keys, preserving custom names."""
    name = str(name).strip()
    compact = name.replace('་', '').replace('།', '')
    if 1 <= len(compact) <= 2 and all(c in DZ_ALPHABET for c in compact):
        return section_label(_index(compact, DZ_ALPHABET))
    return name

def display_section(name, lang='en'):
    name = canonical_section(name)
    if lang == 'dz' and re.fullmatch('[A-Z]{1,2}', name):
        return section_label(_index(name, tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ')), 'dz')
    return name

def section_list(value, lang='en'):
    return ', '.join(display_section(v.strip(), lang) for v in str(value).split(','))
