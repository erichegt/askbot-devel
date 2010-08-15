from django import forms
from django.utils import safestring

class ImageInput(forms.FileInput):

    def render(self, name, value, attrs = None):
        output = '<img '
        if attrs and 'image_class' in attrs:
            output += 'class="%s" ' % attrs['image_class']
        output += 'src="%s"/><br/>' % value
        output += super(ImageInput, self).render(name, value, attrs)
        return safestring.mark_safe(output)
