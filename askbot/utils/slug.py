"""defines the method for building slugs
slugification may be disabled with a live setting "USE_ASCII_ONLY_SLUGS"

the setting was added just in case - if people actually
want to see unicode characters in the slug. If this is the choice
slug will be simply equal to the input text
"""
from unidecode import unidecode
from django.template import defaultfilters
from django.conf import settings


def slugify(input_text, max_length=50):
    """custom slugify function that
    removes diacritic modifiers from the characters
    """
    if getattr(settings, 'ALLOW_UNICODE_SLUGS', False) == False:
        if input_text == '':
            return input_text
        slug = defaultfilters.slugify(unidecode(input_text))
        while len(slug) > max_length:
            # try to shorten word by word until len(slug) <= max_length
            temp = slug[:slug.rfind('-')]
            if len(temp) > 0:
                slug = temp
            else:
                #we have nothing left, do not apply the last crop,
                #apply the cut-off directly
                slug = slug[:max_length]
                break
        return slug
    else:
        return input_text
