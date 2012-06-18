try:
    from haystack import indexes, site
except ImportError:
    pass

from askbot.models import Post, Thread, Tag, User

class ThreadIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')

    def index_queryset(self):
        return Thread.objects.all()

    def prepare(self, obj):
        self.prepared_data = super(ThreadIndex, self).prepare(object)

        self.prepared_data['tags'] = [tag.name for tag in objects.tags.all()]

class PostIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    post_text = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='user')

    def index_queryset(self):
        return Post.objects.all()

site.register(Post, PostIndex)
site.register(Thread, ThreadIndex)
