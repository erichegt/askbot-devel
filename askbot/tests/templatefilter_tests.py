from unittest import TestCase
from askbot.templatetags import extra_filters_jinja as filters
from askbot.conf import settings as askbot_settings

class AbsolutizeImageUrlsTests(TestCase):
    def setUp(self):
        askbot_settings.update('APP_URL', 'http://example.com')
    def test_absolutize_image_urls(self):
        text = """<img class="junk" src="/some.gif"> <IMG SRC='/some.png'>"""
        output = filters.absolutize_image_urls_func(text)
        self.assertEqual(
            output,
            '<img class="junk" src="http://example.com/some.gif"> <IMG SRC="http://example.com/some.png">'
        )
