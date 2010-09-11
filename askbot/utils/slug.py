from unidecode import unidecode
from django.template.defaultfilters import slugify as slgfy


def slugify(s, max_length=50):
    if s == '':
        return s
    slug = slgfy(unidecode(s))
    while len(slug) > max_length:
        # try to shorten word by word until len(slug) <= max_length
        temp = slug[:slug.rfind('-')]
        if len(temp) > 0:
            slug = temp
        else:
            # we have nothing left, do not apply the last crop, apply the cut-off directly
            slug = slug[:max_length]
            break
    return slug
