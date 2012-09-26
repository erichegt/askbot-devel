from unittest import TestCase
from askbot.templatetags import extra_filters_jinja as filters
from askbot.conf import settings as askbot_settings

class AbsolutizeUrlsTests(TestCase):
    def setUp(self):
        askbot_settings.update('APP_URL', 'http://example.com')
    def test_absolutize_image_urls(self):
        text = """<img class="junk" src="/some.gif"> <img class="junk" src="../../cat.gif"> <IMG SRC='/some.png'>"""
        #jinja register.filter decorator works in a weird way
        output = filters.absolutize_urls[0](text)
        self.assertEqual(
            output,
            '<img class="junk" src="http://example.com/some.gif" style="max-width:500px;"> <img class="junk" src="http://example.com/../../cat.gif" style="max-width:500px;"> <IMG SRC="http://example.com/some.png" style="max-width:500px;">'
        )
    def test_absolutize_anchor_urls(self):
        text = """<a class="junk" href="/something">link</a> <A HREF='/something'>link</A>"""
        #jinja register.filter decorator works in a weird way
        output = filters.absolutize_urls[0](text)
        self.assertEqual(
            output,
            '<a class="junk" href="http://example.com/something">link</a> <A HREF="http://example.com/something">link</A>'
        )
