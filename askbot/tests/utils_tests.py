from django.test import TestCase
from askbot.utils.url_utils import urls_equal

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
        
