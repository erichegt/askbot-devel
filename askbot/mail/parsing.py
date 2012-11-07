"""a module for parsing email response text
this file is a candidate for publishing as an independent module
"""
import re

#Regexes for quote separators
#add more via variables ending with _QUOTE_RE
#These regexes do not contain any trailing:
#* newline chars,
#* lines starting with | or >
#* lines consisting entirely of empty space
#expressions are stripped of month and day names
#to keep them simpler and make the additions of language variants
#easier.
GMAIL_QUOTE_RE = r'\n\nOn [^\n]* wrote:\Z'
YAHOO_QUOTE_RE = r'\n\n\n\n_+\n From: [^\n]+\nTo: [^\n]+\nSent: [^\n]+\nSubject: [^\n]+\Z'
KMAIL_QUOTE_RE = r'\AOn [^\n]+ you wrote:\s*\n\n'
OUTLOOK_RTF_QUOTE_RE = r'\n\nSubject: [^\n]+\nFrom: [^\n]+\nTo: [^\n]+\nDate: [^\n]+\Z'
OUTLOOK_TEXT_QUOTE_RE = r'\n_+\Z'

def compile_quote_regexes():
    regex_names = filter(
        lambda v: v.endswith('_QUOTE_RE'),
        globals().keys()
    )
    compiled_regexes = list()
    for regex_name in regex_names:
        regex = globals()[regex_name]
        compiled_regexes.append(
            re.compile(
                regex,
                re.MULTILINE | re.IGNORECASE
            )
        )
    return compiled_regexes

CLIENT_SPECIFIC_QUOTE_REGEXES = compile_quote_regexes()

def strip_trailing_empties_and_quotes(text):
    #strip empty lines and quote lines starting with | and >
    return re.sub(r'(([\n\s\xa0])|(\n[\|>][^\n]*))*\Z', '', text)

def strip_leading_empties(text):
    return re.sub(r'\A[\n\s\xa0]*', '', text)

def strip_email_client_formatting(text):
    """strips email client formatting from the responses,
    such as empty lines and quote separators (on ... wrote)

    if one client-specific separator matches, then result
    is immediately returned
    """
    text = strip_trailing_empties_and_quotes(text)
    for regex in CLIENT_SPECIFIC_QUOTE_REGEXES:
        if regex.search(text):
            text = regex.sub('', text)
            break
    text = strip_trailing_empties_and_quotes(text)
    return strip_leading_empties(text)

def extract_reply_contents(text, reply_separator=None):
    """If reply_separator is given,
    take the part above the separator.
    After, strip the email-client-specific text

    ``text`` is the input text
    ``reply_separator`` is either a string or a regex object
    """
    if reply_separator:
        if isinstance(reply_separator, basestring):
            text = text.split(reply_separator)[0]
        else:
            testre = re.compile('test')
            if type(testre) == type(reply_separator):
                text = reply_separator.split(text)[0]
            else:
                raise ValueError('reply_separator must be a string or a compiled regex')
    return strip_email_client_formatting(text)
