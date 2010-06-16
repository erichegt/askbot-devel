from django.contrib.sitemaps import Sitemap
from askbot.models import Question

class QuestionsSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.5
    def items(self):
        return Question.objects.exclude(deleted=True)

    def lastmod(self, obj):
        return obj.last_activity_at

    def location(self, obj):
        return obj.get_absolute_url()
