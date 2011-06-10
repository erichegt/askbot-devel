from unittest import TestCase
from askbot.templatetags import extra_filters_jinja as filters
from askbot.conf import settings as askbot_settings

class AbsolutizeUrlsTests(TestCase):
    def setUp(self):
        askbot_settings.update('APP_URL', 'http://example.com')
    def test_absolutize_image_urls(self):
        text = """<img class="junk" src="/some.gif"> <IMG SRC='/some.png'>"""
        output = filters.absolutize_urls_func(text)
        self.assertEqual(
            output,
            '<img class="junk" src="http://example.com/some.gif"> <IMG SRC="http://example.com/some.png">'
        )
    def test_absolutize_anchor_urls(self):
        text = """<a class="junk" href="/something">link</a> <A HREF='/something'>link</A>"""
        output = filters.absolutize_urls_func(text)
        self.assertEqual(
            output,
            '<a class="junk" href="http://example.com/something">link</a> <A HREF="http://example.com/something">link</A>'
        )
