"""
recaptcha-django

ReCAPTCHA (Completely Automated Public Turing test to tell Computers and
Humans Apart - while helping digitize books, newspapers, and old time radio
shows) module for django
"""

from django.forms import Widget, Field, ValidationError
from django.conf import settings
from django.utils.translation import get_language, ugettext_lazy as _
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from recaptcha.client import captcha
from askbot.conf import settings as askbot_settings


HUMAN_ERRORS = {
    'unknown':                  _(u'Unknown error.'),
    'invalid-site-public-key':  _(u'ReCAPTCHA is wrongly configured.'),
    'invalid-site-private-key': _(u'ReCAPTCHA is wrongly configured.'),
    'invalid-request-cookie':   _(u'Bad reCAPTCHA challenge parameter.'),
    'incorrect-captcha-sol':    _(u'The CAPTCHA solution was incorrect.'),
    'verify-params-incorrect':  _(u'Bad reCAPTCHA verification parameters.'),
    'invalid-referrer':         _(u'Provided reCAPTCHA API keys are not valid for this domain.'),
    'recaptcha-not-reachable':  _(u'ReCAPTCHA could not be reached.')
}


class ReCaptchaWidget(Widget):
    """
    A Widget that renders a ReCAPTCHA form
    """
    options = ['theme', 'lang', 'custom_theme_widget', 'tabindex']

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        error = final_attrs.get('error', None)
        html = captcha.displayhtml(
                            askbot_settings.RECAPTCHA_KEY, 
                            error=error
                        )
        options = u',\n'.join([u'%s: "%s"' % (k, conditional_escape(v)) \
                   for k, v in final_attrs.items() if k in self.options])
        return mark_safe(u"""<script type="text/javascript">
        var RecaptchaOptions = {
            %s
        };
        </script>
        %s
        """ % (options, html))


    def value_from_datadict(self, data, files, name):
        """
        Generates Widget value from data dictionary.
        """
        try:
            return {'challenge': data['recaptcha_challenge_field'],
                    'response': data['recaptcha_response_field'],
                    'ip': data['recaptcha_ip_field']}
        except KeyError:
            return None
        
class ReCaptchaField(Field):
    """
    Field definition for a ReCAPTCHA
    """
    widget = ReCaptchaWidget

    def clean(self, value):
        if value is None:
            raise ValidationError(_('Invalid request'))
        resp = captcha.submit(value.get('challenge', None),
                              value.get('response', None),
                              askbot_settings.RECAPTCHA_SECRET,
                              value.get('ip', None))
        if not resp.is_valid:
            self.widget.attrs['error'] = resp.error_code 
            raise ValidationError(HUMAN_ERRORS.get(resp.error_code, _(u'Unknown error.')))
