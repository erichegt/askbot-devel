from django.test import TestCase
from askbot.tests.utils import with_settings
from askbot.utils.url_utils import urls_equal
from askbot.utils.html import absolutize_urls
from askbot.conf import settings as askbot_settings

class UrlUtilsTests(TestCase):
    
    def tests_urls_equal(self):
        e = urls_equal
        self.assertTrue(e('', ''))
        self.assertTrue(e('', '/', True))
        self.assertTrue(e('http://cnn.com', 'http://cnn.com/', True))

        self.assertFalse(e('https://cnn.com', 'http://cnn.com'))
        self.assertFalse(e('http://cnn.com:80', 'http://cnn.com:8000'))

        self.assertTrue(e('http://cnn.com/path', 'http://cnn.com/path/', True))
        self.assertFalse(e('http://cnn.com/path', 'http://cnn.com/path/'))
        

class HTMLUtilsTests(TestCase):
    """tests for :mod:`askbot.utils.html` module"""
    
    @with_settings(APP_URL='http://example.com')
    def test_absolutize_image_urls(self):
        text = """<img class="junk" src="/some.gif"> <img class="junk" src="/cat.gif"> <IMG SRC='/some.png'>"""
        #jinja register.filter decorator works in a weird way
        self.assertEqual(
            absolutize_urls(text),
            '<img class="junk" src="http://example.com/some.gif" style="max-width:500px;"> <img class="junk" src="http://example.com/cat.gif" style="max-width:500px;"> <IMG SRC="http://example.com/some.png" style="max-width:500px;">'
        )

    @with_settings(APP_URL='http://example.com')
    def test_absolutize_anchor_urls(self):
        text = """<a class="junk" href="/something">link</a> <A HREF='/something'>link</A>"""
        #jinja register.filter decorator works in a weird way
        self.assertEqual(
            absolutize_urls(text),
            '<a class="junk" href="http://example.com/something">link</a> <A HREF="http://example.com/something">link</A>'
        )
